"""Laws: biblecore/laws.json and its validator, the `lawparallel` box check,
canon kind `law`, lawbriefs[] and the "Law behind this" chip (shell gating,
the hub's law-briefs.json, the chip's own logic under node), and the hub's
law index page. Samples are fixtures (tests/laws_sample.py), not book data."""
import contextlib
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import support
from template_book import make_book
import laws_sample as ls
from biblecore import assets, canon, components, laws
from biblecore import book as bookmod

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import hub_build  # noqa: E402

_tmp = None
_saved = laws.PATH
META = {"passage": "Deuteronomy 15:12–18"}


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-laws-")
    make_book(_tmp, "Deuteronomy", "Deut", "deuteronomy")
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["components"] = ["echo", "lawparallel"]
    cfg["law_chips"] = True
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))
    laws.PATH = os.path.join(_tmp, "laws-sample.json")
    json.dump(ls.data(), open(laws.PATH, "w", encoding="utf-8"))


def teardown():
    laws.PATH = _saved
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def test_shipped_file_is_valid():
    return laws.validate(json.load(open(_saved, encoding="utf-8")))


def test_sample_is_valid():
    return laws.validate(ls.data())


def test_validator_rejects_bad_files():
    def mut(fn):
        d = ls.data()
        fn(d)
        return laws.validate(d)

    bad = {
        "duplicate id": lambda d: d["laws"][1].update(id="release-of-slaves"),
        "bad id": lambda d: d["laws"][0].update(id="Release_Of"),
        "one passage": lambda d: d["laws"][0].update(passages=d["laws"][0]["passages"][:1]),
        "bad ref": lambda d: d["laws"][0]["passages"][0].update(ref="Exodus twenty"),
        "out of order": lambda d: d["laws"][0]["passages"].reverse(),
        "overlap": lambda d: d["laws"][0]["passages"][1].update(ref="Exod 21:5–9"),
        "no difference": lambda d: d["laws"][0]["passages"][0].update(differences=[]),
        "blank difference": lambda d: d["laws"][0]["passages"][0].update(differences=["  "]),
        "no summary": lambda d: d["laws"][0]["passages"][0].pop("summary"),
        "reason outside": lambda d: d["laws"][0]["passages"][0]["reasons"][0].update(at="Exod 22:1"),
        "reason no why": lambda d: d["laws"][0]["passages"][0]["reasons"][0].pop("why"),
        "unknown key": lambda d: d["laws"][0]["passages"][0].update(date="early"),
        "dating in difference": lambda d: d["laws"][0]["passages"][2].update(
            differences=["A later redaction by the Deuteronomic school."]),
        "dating in reason": lambda d: d["laws"][0]["passages"][1]["reasons"][0].update(
            why="Reflects pre-exilic practice."),
        "top key": lambda d: d.update(extra=1),
        "version": lambda d: d.update(version=2),
    }
    fails = [f"'{n}' passed validation" for n, fn in bad.items() if not mut(fn)]
    # dating goes in the footnote, and that is allowed
    d = ls.data()
    d["laws"][0]["passages"][2]["footnote"] = "Many date this passage later than Exodus 21."
    if laws.validate(d):
        fails.append(f"a dating footnote was refused: {laws.validate(d)}")
    return fails


def test_lawparallel_registered_and_checked():
    reg = components.registry()
    if "lawparallel" not in reg:
        return ["lawparallel is not in the registry"]
    chk = reg["lawparallel"].check
    fails = []
    errs = chk(ls.unit(), META)
    if errs:
        fails.append(f"good box failed: {errs}")
    # components.check runs it for an enabled component
    if components.check(ls.unit(), META, "0.32.0"):
        fails.append("components.check refused a good unit")
    base = ls.box()
    bad = {
        "unknown law": base.replace('data-law="release-of-slaves"', 'data-law="no-such-law"'),
        "no law": base.replace(' data-law="release-of-slaves"', ""),
        "no data-at": base.replace(' data-at="Deut 15:12–18"', ""),
        "at not a passage": base.replace('data-at="Deut 15:12–18"', 'data-at="Deut 15:1–11"'),
        "at in another book": base.replace('data-at="Deut 15:12–18"', 'data-at="Exod 21:2–6"'),
        "anchor outside at": base.replace('data-anchor="15:12"', 'data-anchor="15:20"'),
        "row not a passage": base.replace('<span class="src">Lev 25:39–43', '<span class="src">Lev 25:1–5'),
        "row is own passage": base.replace('<span class="src">Lev 25:39–43', '<span class="src">Deut 15:12–18'),
        "no difference": re.sub(r'<span class="diff">Speaks.*?</span>', "", base),
        "made-up difference": base.replace("Speaks of a man only", "Speaks of a man or a woman"),
        "made-up reason": base.replace("I love my master", "I fear my master"),
        "no take": re.sub(r'<p class="take">.*?</p>', "", base),
        "no rows": re.sub(r'<div class="row">.*?</div>', "", base, flags=re.S),
        "no title": base.replace(' class="par-title"', ""),
        "script": base.replace("Six years", "שש years"),
        "dating": base.replace("Each place", "The later redaction"),
        "data-root": base.replace('<span class="txt">', '<span class="txt" data-root="x">', 1),
        "duplicate row": base.replace("</p></aside>", "</p></aside>").replace(
            '<div class="row"><span class="src">Lev', '<div class="row"><span class="src">Exod 21:2–6</span><span class="txt">x</span>'
            '<span class="diff">' + ls.SLAVE["passages"][0]["differences"][0] + '</span></div><div class="row"><span class="src">Lev'),
    }
    for name, box in bad.items():
        if not chk(ls.unit(box), META):
            fails.append(f"'{name}' passed the check")
    return fails


def test_lawparallel_check_ignores_boxless_units():
    return components.registry()["lawparallel"].check("<article></article>", META)


def test_canon_law_kind_and_harvest():
    fails = []
    if "law" not in canon.KINDS or "law" not in canon.HARVESTED:
        fails.append("canon lacks the law kind")
    rows = canon.harvest_laws(ls.unit(), 1, "Deut")
    got = sorted((r["from"], r["to"], r["kind"], r["source"]) for r in rows)
    want = [("Deut 15:12", "Exod 21:2–6", "law", "law"), ("Deut 15:12", "Lev 25:39–43", "law", "law")]
    if got != want:
        fails.append(f"harvested {got}")
    if any(r.get("note") != "law release-of-slaves" for r in rows):
        fails.append("rows lack the law id in the note")
    meta = {"intertext": [{"ref": "15:12", "to": "Exod 21:2", "kind": "law"}]}
    if canon.validate_meta(meta):
        fails.append(f"meta intertext kind law refused: {canon.validate_meta(meta)}")
    return fails


def test_lawbriefs_meta_validation_and_merge():
    ok = {"lawbriefs": [{"law": "release-of-slaves", "ref": "Deut 15:12–18",
                         "brief": "A bound Hebrew goes free in the seventh year. He leaves with a gift."}]}
    fails = []
    if canon.validate_meta(ok):
        fails.append(f"good brief refused: {canon.validate_meta(ok)}")
    sub_ = lambda **kw: {"lawbriefs": [{**ok["lawbriefs"][0], **kw}]}
    bad = {
        "unknown law": sub_(law="nope"),
        "ref outside": sub_(ref="Deut 16:1"),
        "ref not full": sub_(ref="15:12"),
        "three sentences": sub_(brief="One. Two. Three."),
        "long": sub_(brief="x" * 500),
        "empty": sub_(brief=""),
        "dating": sub_(brief="A later redaction of the older law."),
        "key": sub_(extra=1),
        "not a list": {"lawbriefs": {}},
    }
    for name, m in bad.items():
        if not canon.validate_meta(m):
            fails.append(f"brief '{name}' passed")
    # a sub-range of a passage is fine
    if canon.validate_meta(sub_(ref="Deut 15:15")):
        fails.append("a verse inside a passage was refused")
    # merge: written when present, replaced per unit, absent otherwise
    _quiet(canon.merge_meta, ok, 1)
    d = canon.load()
    if [r["unit"] for r in d.get("lawbriefs", [])] != [1] or d["lawbriefs"][0]["source"] != "meta":
        fails.append(f"merge wrote {d.get('lawbriefs')}")
    _quiet(canon.merge_meta, {}, 1)
    if "lawbriefs" in canon.load() or "lawbriefs" in open(bookmod.book().data("canon.json"), encoding="utf-8").read():
        fails.append("a unit with no briefs left lawbriefs behind")
    return fails


def test_meta_key_is_allowed():
    from biblecore import meta as um
    return [] if "lawbriefs" in um.allowed_top_level_keys() else ["lawbriefs is not an allowed meta key"]


def test_chip_code_only_in_law_chip_books():
    fails = []
    b = bookmod.book()
    shell = assets.shell(b)
    main = shell["app/main.js"]
    if "app/lawchip.js" not in shell or "lawchip.load(bookInfo.hub)" not in main or "lawchip.mount(content)" not in main:
        fails.append("a law_chips book lacks lawchip.js or its hooks")
    if "//law:" in main:
        fails.append("main.js kept a marker line")
    other = tempfile.mkdtemp(prefix="bc-laws-off-")
    try:
        make_book(other, "Numbers", "Num", "numbers")
        bo = bookmod.Book.from_file(os.path.join(other, "book.json"))
        sh = assets.shell(bo)
        if "app/lawchip.js" in sh:
            fails.append("a book without law_chips got lawchip.js")
        for rel, text in sh.items():
            if re.search(r"lawchip|law-brief|//law:", text):
                fails.append(f"{rel} mentions the law chip in a book without law_chips")
    finally:
        shutil.rmtree(other, ignore_errors=True)
    src = open(os.path.join(support.CORE, "biblecore", "web", "app", "main.js"), encoding="utf-8").read()
    gone, kept = assets.law_text(src, False), assets.law_text(src, True)
    if "lawchip" in gone or "lawchip.mount" not in kept or "//law" in kept:
        fails.append("law_text on/off wrong")
    if bookmod.validate_config({**b.cfg, "law_chips": "yes"}) == bookmod.validate_config(b.cfg):
        fails.append("law_chips must be true or false")
    return fails


# ---- the hub: law-briefs.json and the index page

def _hub_fixture():
    """A root holding a Deuteronomy repo with one lawbrief on a built unit."""
    root = tempfile.mkdtemp(prefix="bc-laws-hub-")
    repo = os.path.join(root, "Deuteronomy")
    os.makedirs(os.path.join(repo, "data"))
    json.dump({"units": [{"n": 1, "slug": "release", "title": "t", "passage": "Deuteronomy 15:12–18", "built": True},
                         {"n": 2, "slug": "later", "title": "t", "passage": "Deuteronomy 16:1–8", "built": False}]},
              open(os.path.join(repo, "data", "units.json"), "w"))
    json.dump({"intertext": [], "typescenes": [], "lawbriefs": [
        {"law": "release-of-slaves", "ref": "Deut 15:12–18", "brief": "A bound Hebrew goes free. He leaves with a gift.", "unit": 1, "source": "meta"},
        {"law": "release-of-slaves", "ref": "Deut 15:12–18", "brief": "Not built.", "unit": 2, "source": "meta"},
        {"law": "gone-law", "ref": "Deut 15:12–18", "brief": "x", "unit": 1, "source": "meta"}]},
              open(os.path.join(repo, "data", "canon.json"), "w"))
    return root


def test_hub_law_briefs_data():
    root = _hub_fixture()
    try:
        started = [{"osis": "Deut", "repo": "Deuteronomy", "site": "https://x.test/deuteronomy/", "kind": "core"}]
        out = hub_build.law_briefs(started, root=root, laws_path=laws.PATH)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    rows = out["briefs"]
    if len(rows) != 1:
        return [f"expected 1 brief (unbuilt unit and unknown law dropped), got {rows}"]
    r = rows[0]
    want = {"law": "release-of-slaves", "refbook": "Deut", "span": [15, 12, 15, 18], "slug": "release",
            "site": "https://x.test/deuteronomy/", "book": "Deut", "link": "cv"}
    return [f"{k}: {r.get(k)!r} != {v!r}" for k, v in want.items() if r.get(k) != v]


def test_hub_build_includes_laws_files():
    out = hub_build.build(laws.PATH)
    fails = []
    if len(out["laws.json"]["laws"]) != 2:
        fails.append("hub laws.json lacks the sample laws")
    if "briefs" not in out["law-briefs.json"]:
        fails.append("hub law-briefs.json lacks briefs")
    return fails


def test_hub_page_has_the_law_index():
    hub = os.path.join(support.CORE, "hub")
    js = open(os.path.join(hub, "app", "hub.js"), encoding="utf-8").read()
    html = open(os.path.join(hub, "index.html"), encoding="utf-8").read()
    fails = []
    if "function laws(" not in js or "laws.json" not in js or "laws," not in js:
        fails.append("hub.js lacks the laws view")
    if 'href="#/laws"' not in html:
        fails.append("index.html lacks the Laws link")
    # the view reads the file's own fields only
    for field in ("p.summary", "p.differences", "p.reasons", "p.footnote", "r.why"):
        if field not in js:
            fails.append(f"the laws view ignores {field}")
    return fails


NODE_CHIP = r"""
const src = process.argv[2];
const log = [];
class El {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.attrs = {}; this.hidden = false;
    this.cls = new Set(); this.listeners = {}; this.id = ""; this._text = ""; this.classList = {
      toggle: (c, on) => { on ? this.cls.add(c) : this.cls.delete(c); }, add: (c) => this.cls.add(c) }; }
  set className(v) { this.cls = new Set(v.split(" ")); } get className() { return [...this.cls].join(" "); }
  setAttribute(k, v) { this.attrs[k] = v; }
  set textContent(v) { this._text = v; this.children = []; }
  get textContent() { return this._text + this.children.map((c) => (typeof c === "string" ? c : c.textContent)).join(""); }
  append(...xs) { this.children.push(...xs); }
  addEventListener(k, f) { this.listeners[k] = f; }
  querySelectorAll() { return this.echoes; }
}
const head = new El("head");
global.document = { createElement: (t) => new El(t), getElementById: (id) => head.children.find((c) => c.id === id) || null, head };
const echo = (text) => { const e = new El("aside"); e._text = text; return e; };
const root = new El("div");
root.echoes = [echo("cf. Deut 15:12–18"), echo("cf. Gen 1:1"), echo("cf. Deut 14:1"), echo("cf. Exod 21:2; 21:5")];
const BRIEFS = { briefs: [
  { law: "release-of-slaves", ref: "Deut 15:12–18", refbook: "Deut", span: [15, 12, 15, 18], brief: "Brief A.", site: "https://x.test/deuteronomy/", slug: "release", unit: 1, book: "Deut", link: "cv" },
  { law: "release-of-slaves", ref: "Exod 21:2–6", refbook: "Exod", span: [21, 2, 21, 6], brief: "Brief B.", site: "https://x.test/deuteronomy/", slug: "release", unit: 1, book: "Deut", link: "cv" } ] };
let mode = process.argv[3];
global.fetch = (u) => mode === "down" ? Promise.reject(new Error("offline")) :
  mode === "404" ? Promise.resolve({ ok: false }) : Promise.resolve({ ok: true, json: () => Promise.resolve(mode === "bad" ? { briefs: 5 } : BRIEFS) });
const m = await import(src);
m.mount(root);                       // before the briefs arrive: nothing, no error
m.load("https://hub.test/bible");
await new Promise((r) => setTimeout(r, 20));
const chipped = root.echoes.map((e) => !!e.dataset.lawChip);
const first = root.echoes[0];
const panel = first.children.find((c) => c instanceof El && c.cls.has("law-brief"));
const btn = first.children.find((c) => c instanceof El && c.cls.has("law-chip"));
let opened = null;
if (btn) { btn.listeners.click({ stopPropagation() {} }); opened = !panel.hidden; }
const links = panel ? panel.children.flatMap((p) => p.children).filter((c) => c instanceof El && c.tag === "a").map((a) => a.href) : [];
console.log(JSON.stringify({ chipped, opened, links, panel: panel ? panel.textContent : null }));
"""


def test_chip_logic_under_node():
    node = shutil.which("node")
    if not node:
        return []       # node is a convenience here, not a requirement
    js = os.path.join(support.CORE, "biblecore", "web", "app", "lawchip.js")
    runner = os.path.join(_tmp, "chip-run.mjs")
    open(runner, "w", encoding="utf-8").write(NODE_CHIP)
    fails = []

    def run(mode):
        r = subprocess.run([node, runner, "file:///" + js.replace("\\", "/"), mode], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        if r.returncode:
            return None, (r.stderr or r.stdout)[-600:]
        return json.loads(r.stdout.strip().splitlines()[-1]), ""

    out, err = run("ok")
    if out is None:
        return [f"node run failed: {err}"]
    if out["chipped"] != [True, False, False, True]:
        fails.append(f"chips on echoes: {out['chipped']} (want the Deut 15 echo and the Exod 21 echo only)")
    if out["opened"] is not True:
        fails.append("clicking the chip did not open the brief")
    if "Brief A." not in (out["panel"] or ""):
        fails.append(f"brief text missing: {out['panel']}")
    if out["links"] != ["https://x.test/deuteronomy/#/release/15:12"]:
        fails.append(f"unit link: {out['links']}")
    for mode in ("down", "404", "bad"):
        out, err = run(mode)
        if out is None:
            fails.append(f"hub '{mode}': error, {err}")
        elif any(out["chipped"]):
            fails.append(f"hub '{mode}': chips shown without briefs")
    return fails
