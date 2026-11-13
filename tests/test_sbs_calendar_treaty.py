"""Wave 2 group 4: Side by side (component_labels), the calendar file and
box, and the overlay with verse ranges (overlay_note, overlay.py, the
//overlayx shell blocks). Samples are fixtures, not book data."""
import json
import os
import re
import shutil
import subprocess
import tempfile

import support
from template_book import make_book
import calendar_sample as cs
from biblecore import assets, components, overlay
from biblecore import book as bookmod
from biblecore import calendar as cal

_tmp = None
_saved = cal.PATH
META = {"passage": "Leviticus 23:1–44"}
NOTE = "The treaty model fits the loyalty provisions, not the social laws."
BASE = {"book": "X", "osis": "X", "slug": "x", "language": "hebrew", "corpus": {"kind": "oshb"}}


def _cfg(**kw):
    """Reset book.json to the scratch book's defaults plus kw; make it current."""
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    for k in ("overlay", "overlay_note", "component_labels"):
        cfg.pop(k, None)
    cfg.update(kw)
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-g4-")
    make_book(_tmp, "Deuteronomy", "Deut", "deuteronomy")
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg.update(components=["echo", "synoptic", "calendar"], groupings=["movement", "treaty"])
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    _cfg()
    cal.PATH = os.path.join(_tmp, "calendar-sample.json")
    json.dump(cs.data(), open(cal.PATH, "w", encoding="utf-8"))


def teardown():
    cal.PATH = _saved
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


# ------------------------------------------------------------ side by side

def test_component_labels_validated():
    fails = []
    if bookmod.validate_config(dict(BASE, component_labels={"synoptic": "Side by side"})):
        fails.append("a valid component_labels was refused")
    for name, cl in {"unknown component": {"nope": "X"}, "not a toggle": {"list": "X"},
                     "blank": {"synoptic": " "}, "not a dict": ["synoptic"]}.items():
        if not bookmod.validate_config(dict(BASE, component_labels=cl)):
            fails.append(f"'{name}' passed")
    return fails


def test_side_by_side_label_is_opt_in():
    _cfg()
    plain = components.app_manifest(components.enabled())["components"]
    fails = []
    syn = next(c for c in plain if c["name"] == "synoptic")
    if "labels" in syn["toggle"]:
        fails.append("synoptic gained a chip label with no component_labels")
    _cfg(component_labels={"synoptic": "Side by side"})
    lab = components.app_manifest(components.enabled())["components"]
    syn = next(c for c in lab if c["name"] == "synoptic")
    if syn["toggle"].get("labels", {}).get("default") != "Side by side":
        fails.append(f"label did not reach components.json: {syn['toggle']}")
    cal_toggle = lambda cs_: next(c for c in cs_ if c["name"] == "calendar")["toggle"]
    if cal_toggle(lab) != cal_toggle(plain):
        fails.append("another component's toggle changed")
    _cfg()
    return fails


def test_synoptic_takes_an_old_testament_pair():
    html = ('<article class="unit"><p class="v"><span class="n">9</span> At that time I said to you.</p>'
            '<aside class="synoptic" data-anchor="1:9"><h4>Exod 18:13–26 <span>— Jethro\'s counsel</span></h4>'
            '<div class="row"><span class="src">Exod 18:21</span><span class="txt">Able men.</span></div>'
            '<p class="take">Moses tells it as his own proposal.</p></aside></article>')
    return components.registry()["synoptic"].check(html, {"passage": "Deuteronomy 1:9–18"})


# ---------------------------------------------------------------- calendar

def test_shipped_calendar_is_valid():
    return cal.validate(json.load(open(_saved, encoding="utf-8")))


def test_sample_calendar_is_valid():
    return cal.validate(cs.data())


def test_calendar_validator_rejects_bad_files():
    def mut(fn):
        d = cs.data()
        fn(d)
        return cal.validate(d)

    bad = {
        "duplicate id": lambda d: d["feasts"][1].update(id="passover-unleavened-bread"),
        "bad id": lambda d: d["feasts"][0].update(id="Passover_1"),
        "no passages": lambda d: d["feasts"][0].update(passages=[]),
        "bad ref": lambda d: d["feasts"][0]["passages"][0].update(ref="Leviticus twenty"),
        "out of order": lambda d: d["feasts"][0]["passages"].reverse(),
        "overlap": lambda d: d["feasts"][0]["passages"][1].update(ref="Lev 23:5–8"),
        "no requires": lambda d: d["feasts"][0]["passages"][0].update(requires=[]),
        "blank date": lambda d: d["feasts"][0]["passages"][0].update(date=" "),
        "unknown key": lambda d: d["feasts"][0]["passages"][0].update(summary="x"),
        "dating": lambda d: d["feasts"][0]["passages"][2].update(requires=["A later redaction adds this."]),
        "top key": lambda d: d.update(extra=1),
        "version": lambda d: d.update(version=2),
    }
    return [f"'{n}' passed validation" for n, fn in bad.items() if not mut(fn)]


def test_calendar_box_checked():
    chk = components.registry()["calendar"].check
    fails = []
    errs = chk(cs.unit(), META)
    if errs:
        fails.append(f"good box failed: {errs}")
    base = cs.box()
    bad = {
        "unknown feast": base.replace('data-feast="passover-unleavened-bread"', 'data-feast="nope"'),
        "no feast": base.replace(' data-feast="passover-unleavened-bread"', ""),
        "row not a passage": base.replace("Lev 23:5–8", "Lev 23:9–14"),
        "made-up date": base.replace("fourteenth day, at twilight", "tenth day"),
        "made-up requirement": base.replace("Passover to the Lord.", "Passover to the Lord and a lamb."),
        "no requirement": re.sub(r'<span class="req">.*?</span>', "", base),
        "no take": re.sub(r'<p class="take">.*?</p>', "", base),
        "no title": base.replace(' class="cal-title"', ""),
        "script": base.replace("Passover to", "שלום Passover to"),
        "data-root": base.replace('<span class="req">', '<span class="req" data-root="x">', 1),
        "no rows": re.sub(r'<div class="row">.*?</div>', "", base, flags=re.S),
    }
    for name, box in bad.items():
        if not chk(cs.unit(box), META):
            fails.append(f"'{name}' passed the check")
    # a passage the file gives no date takes no span.date
    weeks = ('<aside class="calendar" data-anchor="23:5" data-feast="weeks"><h4><span class="cal-title">Weeks</span></h4>'
             '<div class="row"><span class="src">Deut 16:9–12</span><span class="date">x</span>'
             '<span class="req">Count seven weeks and keep the feast with a freewill offering.</span></div>'
             '<p class="take">t</p></aside>')
    if not chk(cs.unit(weeks), META):
        fails.append("a date the file doesn't give passed")
    return fails


def test_calendar_whole_table_must_list_everything():
    chk = components.registry()["calendar"].check
    rows = []
    for f in cs.data()["feasts"]:
        for p in f["passages"]:
            rows.append(f'<div class="row" data-feast="{f["id"]}"><span class="src">{p["ref"]}</span>'
                        + (f'<span class="date">{p["date"]}</span>' if p.get("date") else "")
                        + f'<span class="req">{p["requires"][0]}</span></div>')
    whole = ('<aside class="calendar" data-anchor="23:5" data-feast="all"><h4><span class="cal-title">The appointed times</span></h4>'
             + "".join(rows) + '<p class="take">t</p></aside>')
    fails = []
    errs = chk(cs.unit(whole), META)
    if errs:
        fails.append(f"whole table failed: {errs}")
    if not chk(cs.unit(whole.replace(rows[-1], "")), META):
        fails.append("a whole-table box missing a passage passed")
    if not chk(cs.unit(whole.replace(' data-feast="weeks"', "", 1)), META):
        fails.append("a whole-table row without data-feast passed")
    return fails


def test_calendar_follows_the_contract_gate():
    """A unit ported before the component's `since` is not held to it."""
    bad = cs.unit(cs.box(feast="nope"))
    fails = []
    if components.check(bad, META, "0.34.0"):
        fails.append("calendar was checked on a unit older than its since")
    if not components.check(bad, META, "0.35.0"):
        fails.append("calendar was not checked on a unit at its since")
    return fails


# ----------------------------------------------------------------- overlay

def _units(passages):
    return [{"n": i, "slug": f"unit-{i:02d}", "passage": p, "title": "t", "built": False}
            for i, p in enumerate(passages, 1)]


def _uj(verses=None, extra=None):
    d = {"groupings": [
        {"kind": "treaty", "n": 1, "name": "witnesses", "label": "Witnesses", "units": [1, 3],
         "verses": verses if verses is not None else {"1": "4:26", "3": "30:19"}}],
        "units": _units(["Deuteronomy 4:1–40", "Deuteronomy 5:1–33", "Deuteronomy 30:11–20"])}
    d["groupings"] += extra or []
    return d


def _book(**kw):
    return bookmod.Book(dict(BASE, groupings=["movement", "treaty"], overlay="treaty", **kw), _tmp)


def test_overlay_validates_verse_ranges_and_multi_membership():
    b = _book(overlay_note=NOTE)
    fails = []
    if overlay.validate(_uj(), b):
        fails.append(f"good overlay failed: {overlay.validate(_uj(), b)}")
    second = {"kind": "treaty", "n": 2, "name": "blessings", "units": [1, 2], "verses": {"1": "4:40"}}
    if overlay.validate(_uj(extra=[second]), b):
        fails.append("a unit in two elements was refused")
    if overlay.validate(_uj({"1": "4:26–31; 4:35"}), b):
        fails.append("a range and a list were refused")
    bad = {
        "verse outside the unit": _uj({"1": "5:26"}),
        "bad verses": _uj({"1": "twenty-six"}),
        "non-member": _uj({"2": "5:1"}),
        "unit not in units.json": _uj(extra=[{"kind": "treaty", "n": 2, "name": "x", "units": [9]}]),
        "duplicate n": _uj(extra=[{"kind": "treaty", "n": 1, "name": "x", "units": [2]}]),
        "listed twice": _uj(extra=[{"kind": "treaty", "n": 2, "name": "x", "units": [2, 2]}]),
    }
    for name, uj in bad.items():
        if not overlay.validate(uj, b):
            fails.append(f"'{name}' passed")
    return fails


def test_note_and_verses_are_tied_together():
    fails = []
    if bookmod.validate_config(dict(BASE, groupings=["movement", "treaty"], overlay="treaty", overlay_note="N.")):
        fails.append("a valid overlay_note was refused")
    if not bookmod.validate_config(dict(BASE, groupings=["movement", "treaty"], overlay_note="N.")):
        fails.append("overlay_note without overlay passed")
    if not bookmod.validate_config(dict(BASE, groupings=["movement", "treaty"], overlay="treaty", overlay_note="")):
        fails.append("a blank overlay_note passed")
    if not overlay.validate(_uj(), _book()):
        fails.append("'verses' without overlay_note passed")
    return fails


def test_plain_overlay_is_unchanged():
    """Members without verses (Matthew's discourses) validate as before."""
    b = bookmod.Book(dict(BASE, groupings=["movement", "discourse"], overlay="discourse"), _tmp)
    uj = {"groupings": [{"kind": "discourse", "n": 1, "name": "d", "units": [1, 2]}],
          "units": _units(["Matthew 5:1–48", "Matthew 6:1–34"])}
    return overlay.validate(uj, b)


def _main_js(**kw):
    _cfg(overlay="treaty", **kw)
    out = assets.generated(bookmod.book())
    _cfg()
    return (next(v for k, v in out.items() if k.endswith("app/main.js")),
            next(v for k, v in out.items() if k.endswith("css/core.css")))


def test_shell_gates_the_overlay_extension():
    js_off, css_off = _main_js()
    js_on, css_on = _main_js(overlay_note="Note.")
    fails = []
    for tok in ("overlaysOf", "overlayVerses", "bm-key-note"):
        if tok in js_off:
            fails.append(f"'{tok}' is in a book without overlay_note")
        if tok not in js_on:
            fails.append(f"'{tok}' is missing from a book with overlay_note")
    if "overlayx" in js_off or "overlayx" in js_on:
        fails.append("an //overlayx marker survived into the shell")
    if "bm-key-note" in css_off or "bm-key-note" not in css_on:
        fails.append("overlay.css is not gated by overlay_note")
    return fails


def test_off_branch_is_the_old_overlay_code():
    """Stripped of the extension, main.js is what shipped in 0.34.0."""
    git = subprocess.run(["git", "show", "fec7f9c:biblecore/web/app/main.js"], cwd=support.CORE,
                         capture_output=True)
    if git.returncode:
        return []
    new = open(os.path.join(support.CORE, "biblecore", "web", "app", "main.js"), encoding="utf-8").read()
    old = git.stdout.decode("utf-8")
    if assets.overlayx_text(new, False).replace("\r\n", "\n") != old.replace("\r\n", "\n"):
        return ["main.js without the overlay extension differs from the 0.34.0 file"]
    return []


def test_extended_shell_parses():
    node = shutil.which("node")
    if not node:
        return []
    js, _ = _main_js(overlay_note="Note.")
    p = os.path.join(_tmp, "main-check.mjs")
    open(p, "w", encoding="utf-8").write(js)
    r = subprocess.run([node, "--check", p], capture_output=True, text=True)
    return [r.stderr[-400:]] if r.returncode else []


def test_manifest_carries_the_note_only_when_set():
    from biblecore import manifest
    fails = []
    _cfg(overlay="treaty")
    if "overlay_note" in manifest.build():
        fails.append("manifest has an overlay_note nobody set")
    _cfg(overlay="treaty", overlay_note="Note.")
    if manifest.build().get("overlay_note") != "Note.":
        fails.append("manifest lost the overlay_note")
    _cfg()
    return fails
