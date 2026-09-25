"""The per-fragment metadata block: parse, validate, generate, plus the
fragment-level checks (ARCHITECTURE.md §2).

Seeded from Joshua's pipeline/unit_meta.py. Book-specific parts now come
from book.json: grouping keys (Joshua's `movement`), extra meta keys, and
whether opens/payoffs must carry a `note`.

Every fragment carries, right after <article class="unit" …>, a block:

    <script type="application/json" id="unit-meta">
    { …the JSON below… }
    </script>

Shape (style reference §3):
  unit       int      unit number
  slug       str      "unit-09"            (derived if absent)
  passage    str      "Numbers 9:1-23"
  title      str
  <grouping> int                           (optional, one per book.json grouping
                                           kind, e.g. movement; from units.json)
  roots      [ {root, translit, gloss, example?, echo?} ]
             LOCAL roots only (a tracked thread's entry lives in
             threads.json). No colour -- the site assigns it. No
             kind/members (a taxonomy that was tried and reverted).
             `example`: one quoted clause from the unit's own English.
             `echo`: one line naming where the word appeared before or
             reappears later, shown in the root popover.
  threads    { opens:[{id,ref,note}], payoffs:[{id,ref,note}],
               candidates:[{root,why,ids?,refs?}],
               retro:[{unit,verse,text,root,why,nth?,op?,w?}] }
             All four sub-keys required, each a list, empty lists fine.
             opens/payoffs `note` is required unless book.json turns
             checks.opens_note_required off. candidates PROPOSE threads
             (`ids` are lemma ids observed, as evidence). retro fixes
             EARLIER units; `w` is optional in the artifact because the
             porter fills data-w. candidates/retro are consumed by the
             porter and never regenerated.
  contract   str      core version the unit was ported under ("0.3.0");
                        stamped by the porter, moved only by migrations
                        (contract.py). Absent on units ported before 0.3.0.
  questions  [ {topic, note, options?} ]
             Wording/data calls only Lane can make, surfaced at port time in
             Claude Code rather than asked on the project side. Consumed and
             dropped like candidates/retro.

Unknown top-level keys are a hard validate() failure (learned: Matthew's
`descriptor`/`discourse` were authored for eleven units and silently
dropped). Being allowed by validate() is not the same as surviving a regen:
generate() must round-trip every allowed key, which is why the book-declared
groupings and meta_keys are both copied through from units.json.
"""

import json
import os
import re

from biblecore.book import book
from biblecore.lang import ALL_SCRIPTS_RE

BLOCK_RE = re.compile(
    r'[ \t]*<script type="application/json" id="unit-meta">\s*'
    r'(\{.*?\})\s*</script>\n?',
    re.S,
)
ARTICLE_RE = re.compile(r'(<article class="unit"[^>]*>\n?)')


# ---------------------------------------------------------------- load helpers

def _load(name):
    with open(book().data(name), encoding="utf-8") as f:
        return json.load(f)


def _unit_row(units_json, n):
    for u in units_json["units"]:
        if u["n"] == n:
            return u
    return None


# ---------------------------------------------------------------- parse

def parse(html):
    """Return the metadata dict from a fragment string, or None if absent."""
    m = BLOCK_RE.search(html)
    if not m:
        return None
    return json.loads(m.group(1))


def strip(html):
    """Remove an existing metadata block (used before re-injecting)."""
    return BLOCK_RE.sub("", html, count=1)


def inject(html, meta):
    """Insert / replace the metadata block immediately after the <article> tag."""
    html = strip(html)
    m = ARTICLE_RE.search(html)
    if not m:
        raise ValueError("fragment has no <article class=\"unit\"> open tag")
    body = json.dumps(meta, indent=2, ensure_ascii=False)
    block = f'<script type="application/json" id="unit-meta">\n{body}\n</script>\n'
    return html[:m.end()] + block + html[m.end():]


# ---------------------------------------------------------------- validate

REQUIRED = ("unit", "passage", "title", "roots", "threads")

# The complete, closed set of top-level keys a fragment's meta block may
# carry. Anything else is a hard validate() failure -- see module
# docstring. Extending this set is a deliberate schema change, not
# something a fragment author should be able to do just by typing a new
# key and having it silently pass.
CORE_TOP_LEVEL_KEYS = {
    "unit", "slug", "passage", "title", "roots", "threads", "questions",
    # canon rows (G9), consumed at port like questions -- see canon.py
    "intertext", "typescenes",
    # core version the unit was written against (D7) -- see contract.py
    "contract",
}


def allowed_top_level_keys():
    """The core keys, plus one per grouping kind and any extra meta keys the
    book declares in book.json. Extending this is a book.json edit, and
    generate() must be taught to round-trip any new key."""
    b = book()
    return CORE_TOP_LEVEL_KEYS | set(b.groupings) | set(b.meta_keys)

# threads must carry all four of these, each a list (style reference §3).
THREADS_SUBKEYS = ("opens", "payoffs", "candidates", "retro")

_ID_RE = re.compile(r"^\d+[a-z]?$")
_REF_RE = re.compile(r"^\d+:\d+$")
# Word ids are alphanumeric; not pinned to OSHB's 5-character shape.
_WORD_ID_RE = re.compile(r"^[0-9A-Za-z]+$")


_SPACED_ID_RE = re.compile(r"^\s*(\d+)\s+([a-z])\s*$")


def normalize_candidates(meta):
    """Rewrite the word table's own id spelling ('6485 a') to the canonical
    form ('6485a') in threads.candidates[].ids, in place. The chat side
    copies ids straight out of the TSV, so this is accepted rather than
    failed. Returns one note per rewritten id."""
    notes = []
    th = meta.get("threads") if isinstance(meta, dict) else None
    for i, c in enumerate((th or {}).get("candidates") or []):
        ids = c.get("ids") if isinstance(c, dict) else None
        if not isinstance(ids, list):
            continue
        for j, x in enumerate(ids):
            m = _SPACED_ID_RE.match(x) if isinstance(x, str) else None
            if m:
                ids[j] = m.group(1) + m.group(2)
                notes.append(f"threads.candidates[{i}] ({c.get('root', '?')}): "
                             f"id '{x}' read as '{ids[j]}'")
    return notes


def validate(meta, threads_json=None):
    """Return a list of human-readable problems ([] == clean). Every
    problem in this list is a hard build failure for whatever calls this
    (no separate warning tier) -- see check 1 below in particular."""
    errs = []
    if not isinstance(meta, dict):
        return ["metadata is not a JSON object"]

    # check 1: unknown top-level keys are a hard failure, not a warning.
    # This is the check that didn't exist for Matthew until after
    # "descriptor" and "discourse" had already shipped, undetected,
    # across eleven units -- both documented in that project's own
    # unit_meta.py docstring, neither ever wired into generate()'s
    # rebuild, so every regen silently dropped them.
    unknown = set(meta.keys()) - allowed_top_level_keys()
    for k in sorted(unknown):
        errs.append(f"unknown top-level key '{k}' -- not a core key, a grouping, "
                    f"or a book.json meta_keys entry. If it's a real new field, "
                    f"declare it there (and make sure generate() round-trips it) "
                    f"rather than letting it silently vanish on regen.")

    for k in REQUIRED:
        if k not in meta:
            errs.append(f"missing required key: {k}")
    if "unit" in meta and not isinstance(meta["unit"], int):
        errs.append("unit must be an integer")
    for g in book().groupings:
        if g in meta and not isinstance(meta[g], int):
            errs.append(f"{g} must be an integer")

    for i, r in enumerate(meta.get("roots", []) or []):
        where = f"roots[{i}]"
        for k in ("root", "translit", "gloss"):
            if not r.get(k):
                errs.append(f"{where}: missing {k}")
        if "color" in r or "colour" in r:
            errs.append(f"{where}: carries a colour — the site assigns colours, "
                        "declare translit + gloss only")
        if "kind" in r or "members" in r:
            errs.append(f"{where}: carries 'kind'/'members' — that taxonomy "
                        "was tried and reverted (style reference §1); a root "
                        "is {root, translit, gloss}, nothing more")
        if not re.fullmatch(r"[a-z0-9-]+", r.get("root", "x")):
            errs.append(f"{where}: root '{r.get('root')}' must be [a-z0-9-]")
        if "example" in r and not isinstance(r["example"], str):
            errs.append(f"{where}: 'example' must be a string")
        if "echo" in r and not (isinstance(r["echo"], str) and r["echo"].strip()):
            errs.append(f"{where}: 'echo' must be a non-empty string")
        for k in set(r) - {"root", "translit", "gloss", "example", "echo",
                           "color", "colour", "kind", "members"}:
            errs.append(f"{where}: unknown key '{k}' -- a root is "
                        "{root, translit, gloss, example?, echo?}")

    th = meta.get("threads", {}) or {}
    for key in THREADS_SUBKEYS:
        if key not in th:
            errs.append(f"threads.{key} is required (all four of "
                        f"{THREADS_SUBKEYS} must be present, empty lists fine)")
        elif not isinstance(th[key], list):
            errs.append(f"threads.{key} must be a list")

    note_required = book().check("opens_note_required")
    for key in ("opens", "payoffs"):
        for i, e in enumerate(th.get(key, []) or []):
            if not e.get("note"):
                if not note_required:
                    continue
                errs.append(f"threads.{key}[{i}]: missing required 'note' "
                            "(the popover line for this beat, checklist 4)")
            elif not isinstance(e["note"], str):
                errs.append(f"threads.{key}[{i}]: 'note' must be a string")

    for i, c in enumerate(th.get("candidates", []) or []):
        where = f"threads.candidates[{i}]"
        if not c.get("root"):
            errs.append(f"{where}: missing 'root'")
        elif not re.fullmatch(r"[a-z0-9-]+", c["root"]):
            errs.append(f"{where}: root '{c['root']}' must be [a-z0-9-]")
        if not c.get("why"):
            errs.append(f"{where}: missing 'why'")
        for k in ("stems", "exclude"):
            if k in c:
                errs.append(f"{where}: '{k}' is not part of the schema — "
                            "candidates are {root, why, ids?, refs?} now "
                            "(id-based, style reference §2/§3), not Hebrew "
                            "consonant-skeleton stems")
        if "ids" in c:
            if not isinstance(c["ids"], list) or not all(
                    isinstance(x, str) and _ID_RE.match(x) for x in c["ids"]):
                errs.append(f"{where}: 'ids' must be a list of strings matching "
                            f"^\\d+[a-z]?$ (e.g. '2763', '2763a')")
        if "refs" in c:
            if not isinstance(c["refs"], list) or not all(
                    isinstance(x, str) and _REF_RE.match(x) for x in c["refs"]):
                errs.append(f"{where}: 'refs' must be a list of 'C:V' strings "
                            f"(e.g. '6:5')")

    for i, q in enumerate(meta.get("questions", []) or []):
        where = f"questions[{i}]"
        if not q.get("topic"):
            errs.append(f"{where}: missing 'topic'")
        elif not isinstance(q["topic"], str):
            errs.append(f"{where}: 'topic' must be a string")
        if not q.get("note"):
            errs.append(f"{where}: missing 'note'")
        elif not isinstance(q["note"], str):
            errs.append(f"{where}: 'note' must be a string")
        if "options" in q:
            if not isinstance(q["options"], list) or not all(
                    isinstance(x, str) for x in q["options"]):
                errs.append(f"{where}: 'options' must be a list of strings")

    from biblecore import canon, contract
    errs += canon.validate_meta(meta)
    errs += contract.check_stamp(meta.get("contract"))

    if threads_json is not None:
        ids = {t["id"] for t in threads_json["threads"]}
        roots = {t["root"] for t in threads_json["threads"]}
        for key in ("opens", "payoffs"):
            for e in th.get(key, []) or []:
                if e.get("id") not in ids:
                    errs.append(f"threads.{key}: '{e.get('id')}' is not a "
                                "thread id in data/threads.json "
                                "(use threads.candidates to propose a new one)")

        this_slug = meta.get("slug") or f"unit-{meta.get('unit', 0):02d}"
        try:
            units_json = _load("units.json")
        except Exception:
            units_json = {"units": []}
        unit_roots = {u["slug"]: set((u.get("roots") or {}).keys())
                      for u in units_json["units"]}
        VALID_OPS = {"add", "retag", "retag_word", "untag_word", "unwrap",
                     "strip_span", "text"}
        for i, e in enumerate(th.get("retro", []) or []):
            where = f"threads.retro[{i}]"
            slug = e.get("unit", "")
            op = e.get("op", "add")
            if not re.fullmatch(r"unit-\d{2}", slug):
                errs.append(f"{where}: 'unit' must be a slug like 'unit-06'")
            elif slug == this_slug:
                errs.append(f"{where}: retro is for EARLIER units, not this one "
                            f"({slug}) — tag this unit's own occurrences in the "
                            "fragment or in retrofit-tags.json directly")
            if not e.get("why"):
                errs.append(f"{where}: missing 'why'")
            if op not in VALID_OPS:
                errs.append(f"{where}: op '{op}' not one of {sorted(VALID_OPS)}")
            targets = ([e.get("to")] if op in ("retag", "retag_word", "text")
                       else [e.get("root")] if op in ("add", "unwrap", "untag_word")
                       else [])
            for r in filter(None, targets):
                known = slug in unit_roots and r in unit_roots[slug]
                if r not in roots and not known:
                    errs.append(f"{where}: '{r}' is neither a tracked thread nor "
                                f"a declared root of {slug} — a tag that resolves "
                                "to no colour is a hard verify failure")
                # A retro fix that creates or repoints a span onto a TRACKED
                # thread produces a span that must carry data-w -- but `w` is
                # OPTIONAL here (style reference §7 item 6, review A6): the
                # chat side is told not to hand-chase word ids, and
                # assign_data_w.py fills them during the port. A malformed
                # `w` is still an error; a missing one is not. The guarantee
                # is kept where it belongs, on the built fragment, by
                # check_tracked_spans_have_data_w().
                if op in ("add", "retag", "retag_word") and r in roots:
                    wid = e.get("w")
                    if wid and not _WORD_ID_RE.match(wid):
                        errs.append(f"{where}: op '{op}' targets tracked "
                                    f"thread '{r}' with 'w'={wid!r}, which is "
                                    "not a valid word id")
    return errs


# ---------------------------------------------------------- validate_fragment

# Component classes every unit fragment must contain. The legend is
# section.block.legend (style reference §4), so both class tokens are
# required, not just "legend" -- a fragment with roots/threads but no
# rendered legend is exactly as broken as one referencing a CSS class that
# doesn't exist, just in the opposite direction.
REQUIRED_COMPONENT_CLASSES = {"block", "legend"}

CLASS_ATTR_RE = re.compile(r'class="([^"]*)"')
# Grep-level CSS class-selector scan, not a real CSS parser: any ".name"
# where name starts with a letter, so "12px"/".5em" don't get pulled in
# as fake classes. Good enough for a whitelist diff; a hand-rolled parser
# would be more precision than a fragment/stylesheet pair this small needs.
CSS_CLASS_RE = re.compile(r'\.([a-zA-Z][a-zA-Z0-9_-]*)')

ID_ATTR_RE = re.compile(r'id="([\w-]*n\d+[a-z]?)"')
HREF_ATTR_RE = re.compile(r'href="#([\w-]*n\d+[a-z]?)"')

def _css_classes(css_path=None):
    css_path = css_path or book().path("css")
    if not os.path.exists(css_path):
        return None  # caller turns this into a hard failure, not a silent pass
    css = open(css_path, encoding="utf-8").read()
    return set(CSS_CLASS_RE.findall(css))


def check_component_whitelist(html, css_path=None):
    """1) every class used in the fragment must be defined in
    css/styles.css (grep-diff, not a CSS parser -- see CSS_CLASS_RE).
    2) every class in REQUIRED_COMPONENT_CLASSES must actually appear."""
    errs = []
    css_classes = _css_classes(css_path)
    if css_classes is None:
        errs.append(f"{css_path or book().path('css')} not found -- can't check the fragment's "
                    "classes against it. Create the stylesheet (or point "
                    "css_path at the right one) before validating fragments.")
        css_classes = set()

    fragment_classes = set()
    for m in CLASS_ATTR_RE.finditer(html):
        fragment_classes.update(m.group(1).split())

    unstyled = sorted(fragment_classes - css_classes)
    for cls in unstyled:
        errs.append(f"fragment uses class '{cls}' which css/styles.css does "
                    f"not define -- typo, or a class that needs adding there")

    missing_required = sorted(REQUIRED_COMPONENT_CLASSES - fragment_classes)
    for cls in missing_required:
        errs.append(f"required component missing: no element with class "
                    f"'{cls}' in this fragment")
    return errs


def check_endnote_integrity(html):
    """Every id="…n<N>" must have a matching href="#…n<N>" and vice versa
    -- an endnote nobody links to, or a link to an endnote that doesn't
    exist, are both silent breakage (a dead citation marker, or a click
    that goes nowhere)."""
    ids = {m.group(1) for m in ID_ATTR_RE.finditer(html)}
    hrefs = {m.group(1) for m in HREF_ATTR_RE.finditer(html)}
    errs = []
    orphan_ids = sorted(ids - hrefs)
    orphan_hrefs = sorted(hrefs - ids)
    for i in orphan_ids:
        errs.append(f"endnote id=\"{i}\" has no href=\"#{i}\" pointing to it "
                    f"-- unreferenced endnote")
    for h in orphan_hrefs:
        errs.append(f"href=\"#{h}\" has no matching id=\"{h}\" -- link to a "
                    f"nonexistent endnote")
    return errs


def check_no_native_script(html):
    """Zero Hebrew or Greek script anywhere in a fragment, attribute values
    included, no exceptions. A fragment is English plus transliteration;
    original-language strings are generated from the corpus by word id,
    never typed into a fragment (ARCHITECTURE.md §2)."""
    hits = ALL_SCRIPTS_RE.findall(html)
    if not hits:
        return []
    sample = "".join(sorted(set(hits))[:10])
    return [f"{len(hits)} native-script character(s) found in the fragment "
            f"(fragments carry English + transliteration only). "
            f"Sample: {sample!r}"]


# ------------------------------------------------------- newer fragment checks
# (checklist items 6, 7, 9, 13; §4's rl-outside-verse-blocks convention)

DATA_ROOT_RE = re.compile(r'data-root="([a-z0-9-]+)"')
SPAN_R_RE = re.compile(r'<span\s+class="r"([^>]*)>')
DATA_W_ATTR_RE = re.compile(r'data-w="')
PERICOPE_RE = re.compile(r'<h3\s+class="pericope">(.*?)</h3>', re.S)
PERICOPE_RANGE_RE = re.compile(r'·\s*\d+:\d+')
STYLE_ATTR_RE = re.compile(r'\bstyle\s*=\s*"')
CSS_VAR_RE = re.compile(r'--c-[a-zA-Z0-9_-]+')
VBLOCK_RE = re.compile(r'<(?:div|p)\s+class="v"[^>]*>(.*?)</(?:div|p)>', re.S)
RL_RE = re.compile(r'class="rl"')
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _detag(s):
    return _WS_RE.sub(" ", _TAG_RE.sub("", s)).strip()


def check_data_root_resolves(html, meta=None, threads_json=None):
    """Every data-root slug must resolve to a colour: a threads.json
    thread's `root`, or this fragment's own meta.roots[] (checklist 6). A
    data-root that resolves to nothing is a hard build failure (style
    reference §1)."""
    if meta is None:
        meta = parse(html) or {}
    if threads_json is None:
        try:
            threads_json = _load("threads.json")
        except Exception:
            threads_json = {"threads": []}

    known = {t["root"] for t in threads_json.get("threads", [])}
    known |= {r["root"] for r in (meta.get("roots") or []) if r.get("root")}

    errs = []
    for slug in sorted(set(DATA_ROOT_RE.findall(html))):
        if slug not in known:
            errs.append(f"data-root=\"{slug}\" resolves to no colour -- not a "
                        f"thread in data/threads.json and not in this "
                        f"fragment's own roots[] (checklist 6)")
    return errs


def check_tracked_spans_have_data_w(html, threads_json=None):
    """Every span tagging a TRACKED thread (data-root matching a
    threads.json thread's root) must carry data-w (checklist 7, style
    reference §2). Local roots (declared only in this fragment's own
    roots[]) don't need one."""
    if threads_json is None:
        try:
            threads_json = _load("threads.json")
        except Exception:
            threads_json = {"threads": []}
    tracked = {t["root"] for t in threads_json.get("threads", [])}

    errs = []
    for m in SPAN_R_RE.finditer(html):
        attrs = m.group(1)
        rm = DATA_ROOT_RE.search(attrs)
        if not rm or rm.group(1) not in tracked:
            continue
        if not DATA_W_ATTR_RE.search(attrs):
            errs.append(f"span tags tracked thread '{rm.group(1)}' with no "
                        f"data-w attribute (checklist 7)")
    return errs


def check_pericope_headings(html):
    """Every h3.pericope must carry its '· C:V' (or C:V-C:V) range
    (checklist 9)."""
    errs = []
    for m in PERICOPE_RE.finditer(html):
        if not PERICOPE_RANGE_RE.search(m.group(1)):
            errs.append(f"pericope heading missing its '· C:V' range: "
                        f"{_detag(m.group(1))!r}")
    return errs


ECHO_OPEN_RE = re.compile(r'<aside\s+class="echo"([^>]*)>')
ECHO_CLOSE_RE = re.compile(r'</aside>')
ECHO_ANCHOR_RE = re.compile(r'data-anchor="([^"]*)"')
GLOSS_OPEN_RE = re.compile(r'<span\s+class="gloss">')
SPAN_CLOSE_RE = re.compile(r'</span>')
NUM_RE = re.compile(r'<span class="n">\s*(?:(\d+):)?(\d+)\s*</span>')
PASSAGE_FIRST_CH_RE = re.compile(r"(\d+):")


def _verse_at(html, pos, default_ch):
    """The (ch, v) of the .v block a position in html falls inside, or the
    nearest preceding one if it's a following sibling (a .gloss/.echo,
    which live just after the </p> of the verse they comment on).

    Bare verse numbers (`<span class="n">3</span>`) inherit the chapter
    from the nearest preceding explicit `C:V` and roll forward on a
    number that goes backwards -- same convention as
    data_w.verse_blocks(), reimplemented locally rather than imported, so
    this module stays a leaf with no dependency on the word table."""
    ch, v, prev_v = default_ch, None, None
    for m in NUM_RE.finditer(html, 0, pos):
        this_v = int(m.group(2))
        if m.group(1):
            ch, prev_v = int(m.group(1)), None
        elif prev_v is not None and this_v < prev_v:
            ch += 1
        prev_v = this_v
        v = this_v
    return ch, v


def check_echo(html, meta=None):
    """`aside.echo` — style reference §4: optional, a verse sibling like
    `.gloss`, "ship it only with its nesting-depth check."

    Three things, all part of that check:
    1. `data-anchor="C:V"` is present and well-formed.
    2. The anchor matches the verse the echo actually follows in the
       fragment -- an anchor that drifts from its position is exactly the
       kind of silent mismatch a reader would never notice and a diff
       would never catch.
    3. No `<aside class="echo">` starts inside an unclosed (or
       too-early-closed) `<span class="gloss">` (`67b2712`: an aside
       spliced into gloss content collapsed silently). Modelled the way a
       naive renderer actually behaves -- the *nearest* `</span>` at or
       after a gloss's opening tag is treated as closing it, whether or
       not it was meant to -- because that mismatch is the failure mode,
       not a hypothetical one.
    """
    errs = []
    default_ch = None
    if meta and meta.get("passage"):
        m = PASSAGE_FIRST_CH_RE.search(meta["passage"])
        if m:
            default_ch = int(m.group(1))

    span_closes = [m.start() for m in SPAN_CLOSE_RE.finditer(html)]
    gloss_ranges = []
    for m in GLOSS_OPEN_RE.finditer(html):
        end = next((p for p in span_closes if p >= m.end()), len(html))
        gloss_ranges.append((m.start(), end))

    for m in ECHO_OPEN_RE.finditer(html):
        attrs = m.group(1)
        am = ECHO_ANCHOR_RE.search(attrs)
        if not am:
            errs.append("aside.echo has no data-anchor=\"C:V\" attribute")
            continue
        anchor = am.group(1)
        if not _REF_RE.match(anchor):
            errs.append(f"aside.echo data-anchor={anchor!r} is not 'C:V' "
                        f"(e.g. '3:2')")
            continue

        if default_ch is not None:
            ch, v = _verse_at(html, m.start(), default_ch)
            if v is not None and anchor != f"{ch}:{v}":
                errs.append(f"aside.echo data-anchor={anchor!r} doesn't match "
                            f"the verse it follows ({ch}:{v}) -- an echo "
                            f"anchors the verse it's a sibling of")

        if any(gs < m.start() < ge for gs, ge in gloss_ranges):
            errs.append(f"aside.echo at data-anchor={anchor!r} starts inside "
                        f"an unclosed .gloss span -- the exact 67b2712 "
                        f"failure mode (style reference §4): close the "
                        f".gloss's </span> before the aside, don't nest it")

    if len(ECHO_CLOSE_RE.findall(html)) != len(ECHO_OPEN_RE.findall(html)):
        errs.append("aside.echo open/close count mismatch -- an unclosed "
                    "or stray </aside>")

    return errs


DECLARED_RE = re.compile(r'\bdata-verses="([^"]*)"')
_DECLARED_RANGE_RE = re.compile(r"^\s*(\d+):(\d+)\s*(?:[-–]\s*(?:(\d+):)?(\d+))?\s*$")
_PASSAGE_RANGE_RE = re.compile(r"(\d+):(\d+)\s*[-–]\s*(?:(\d+):)?(\d+)")


def _parse_declared(value):
    """'1:22–43' -> ((1, 22), (1, 43)); '1:22–2:3' and '1:22' too. None if
    malformed or backwards."""
    m = _DECLARED_RANGE_RE.match(value)
    if not m:
        return None
    lo = (int(m.group(1)), int(m.group(2)))
    hi = (int(m.group(3) or m.group(1)), int(m.group(4) or m.group(2)))
    return (lo, hi) if lo <= hi else None


def declared_ranges(html):
    """[(lo, hi)] for every element carrying data-verses: verses a component
    (a table.list, say) presents in place of verse-by-verse text. The audit
    reports tracked-thread occurrences there as covered, not as gaps."""
    out = []
    for m in DECLARED_RE.finditer(html):
        r = _parse_declared(m.group(1))
        if r:
            out.append(r)
    return out


TABLE_LIST_RE = re.compile(r'<table\s+class="list"[^>]*>(.*?)</table>', re.S)
SECTION_BLOCK_OPEN_RE = re.compile(r'<section\s+class="block"[^>]*>')
TR_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<t([hd])[^>]*>')


def check_table_list(html):
    """`table.list` -- style reference §4: a count/list table (Numbers'
    censuses first). What the site relies on:
    1. it sits inside a `<section class="block">` (the app keeps such a
       block in line with the text; a bare table gets no block styling);
    2. its first row is a header row of `<th>`;
    3. every row has the same number of cells, since the last column is
       the right-aligned count."""
    errs = []
    for i, m in enumerate(TABLE_LIST_RE.finditer(html), 1):
        where = f"table.list #{i}"
        before = html[:m.start()]
        opens = [s.end() for s in SECTION_BLOCK_OPEN_RE.finditer(before)]
        if not opens or "</section>" in before[opens[-1]:]:
            errs.append(f"{where}: not inside <section class=\"block\"> -- wrap it "
                        f"(style reference §4)")
        rows = [CELL_RE.findall(r.group(1)) for r in TR_RE.finditer(m.group(1))]
        if not rows:
            errs.append(f"{where}: has no rows")
            continue
        if not rows[0] or any(c != "h" for c in rows[0]):
            errs.append(f"{where}: first row must be a header row of <th> cells")
        widths = sorted({len(r) for r in rows})
        if len(widths) > 1:
            errs.append(f"{where}: rows have {widths} cells -- every row needs "
                        f"the same count (the last column is the number)")
    return errs


def check_declared_verses(html, meta=None):
    """data-verses: well-formed C:V[–[C:]V], inside the unit's passage, and
    no declared verse also appears as a verse block. That last rule is what
    keeps the declaration honest: a verse shown in full must be tagged in
    full, so it can't also be excused from the audit."""
    errs = []
    passage = None
    default_ch = None
    if meta and meta.get("passage"):
        pm = _PASSAGE_RANGE_RE.search(meta["passage"])
        if pm:
            passage = ((int(pm.group(1)), int(pm.group(2))),
                       (int(pm.group(3) or pm.group(1)), int(pm.group(4))))
        fm = PASSAGE_FIRST_CH_RE.search(meta["passage"])
        if fm:
            default_ch = int(fm.group(1))

    ranges = []
    for m in DECLARED_RE.finditer(html):
        r = _parse_declared(m.group(1))
        if r is None:
            errs.append(f"data-verses={m.group(1)!r} is not 'C:V', 'C:V–V' or "
                        f"'C:V–C:V' (in order)")
            continue
        if passage and not (passage[0] <= r[0] and r[1] <= passage[1]):
            errs.append(f"data-verses={m.group(1)!r} reaches outside this unit's "
                        f"passage {meta['passage']!r}")
        ranges.append((m.group(1), r))

    if ranges and default_ch is not None:
        ch, prev_v = default_ch, None
        for m in NUM_RE.finditer(html):
            this_v = int(m.group(2))
            if m.group(1):
                ch, prev_v = int(m.group(1)), None
            elif prev_v is not None and this_v < prev_v:
                ch += 1
            prev_v = this_v
            for raw, (lo, hi) in ranges:
                if lo <= (ch, this_v) <= hi:
                    errs.append(f"verse {ch}:{this_v} is written out as a verse "
                                f"AND declared covered by data-verses={raw!r} -- "
                                f"narrow the declaration to the verses the "
                                f"component actually replaces")
    return errs


def check_no_inline_style(html):
    """No inline style=, no --c-* colour vars (checklist 13)."""
    errs = []
    if STYLE_ATTR_RE.search(html):
        errs.append("fragment has an inline style=\"...\" attribute -- not allowed")
    css_vars = sorted(set(CSS_VAR_RE.findall(html)))
    for v in css_vars:
        errs.append(f"fragment uses colour variable '{v}' -- the site assigns "
                    f"colours, no --c-* vars in a fragment")
    return errs


def warnings_for_fragment(html):
    """Non-fatal warnings -- distinct from validate_fragment()'s hard
    failures. Currently just class=\"rl\" inside a .v block (style
    reference §4: valid outside verse blocks, but inside one it's counted
    anyway, so rl there only mislabels intent, doesn't break anything)."""
    warnings = []
    for m in VBLOCK_RE.finditer(html):
        if RL_RE.search(m.group(1)):
            warnings.append("class=\"rl\" found inside a .v verse block -- "
                            "valid only outside verse blocks; inside one it's "
                            "counted anyway, so this only mislabels intent")
    return warnings


# Every fragment check with the core version it arrived in (D7). A unit is
# held to the checks at or below its `contract`; a check added in a later
# core applies to it only after a migration moves its stamp forward. Add
# new checks at the bottom with the version they ship in.
FRAGMENT_CHECKS = [
    ("0.1.0", "whitelist", lambda h, m, t, c: check_component_whitelist(h, c)),
    ("0.1.0", "endnotes", lambda h, m, t, c: check_endnote_integrity(h)),
    ("0.1.0", "native-script", lambda h, m, t, c: check_no_native_script(h)),
    ("0.1.0", "data-root", lambda h, m, t, c: check_data_root_resolves(h, m, t)),
    ("0.1.0", "data-w", lambda h, m, t, c: check_tracked_spans_have_data_w(h, t)),
    ("0.1.0", "pericope", lambda h, m, t, c: check_pericope_headings(h)),
    ("0.1.0", "echo", lambda h, m, t, c: check_echo(h, m)),
    ("0.2.0", "data-verses", lambda h, m, t, c: check_declared_verses(h, m)),
    ("0.2.0", "table.list", lambda h, m, t, c: check_table_list(h)),
    ("0.1.0", "inline-style", lambda h, m, t, c: check_no_inline_style(h)),
]


def validate_fragment(html, css_path=None, meta=None, threads_json=None):
    """All fragment-level HARD checks in one call: component whitelist,
    endnote integrity, zero native script, data-root resolution, tracked-
    span data-w, pericope headings, aside.echo anchors/nesting, no inline
    style/--c-* vars, plus whatever FRAGMENT_CHECKS gains later -- each
    only if the unit's `contract` is at or past the version it arrived in.
    Does not include validate()'s meta-dict checks, and does not include
    warnings_for_fragment()'s non-fatal warnings -- run all three when
    checking a real fragment."""
    from biblecore import contract
    unit_contract = contract.of(meta if meta is not None else parse(html))
    errs = []
    for since, _name, fn in FRAGMENT_CHECKS:
        if contract.at_least(unit_contract, since):
            errs += fn(html, meta, threads_json, css_path)
    return errs


# ---------------------------------------------------------------- generate
# (derive a metadata block for an already-built unit from the data files —
#  used to keep blocks fresh once a build step exists)

def _threads_touching(threads_json, n):
    """opens/payoffs entries for unit n, carrying `note` through.

    `note` is required by validate() on both, so generate() must round-trip
    it or every regenerated meta block fails the project's own validator.
    The note lives on the threads.json entry: `opens.note` for an opening
    beat, `payoffs[].note` for a payoff.
    """
    opens, payoffs = [], []
    for t in threads_json["threads"]:
        o = t.get("opens") or {}
        if o.get("unit") == n:
            opens.append({"id": t["id"], "ref": o.get("ref", ""),
                          "note": o.get("note", "")})
        for p in t.get("payoffs", []):
            if p.get("unit") == n:
                payoffs.append({"id": t["id"], "ref": p.get("ref", ""),
                                "note": p.get("note", "")})
    return opens, payoffs


def generate(n, units_json=None, threads_json=None):
    """Build the metadata dict for unit n from the committed data files."""
    units_json = units_json or _load("units.json")
    threads_json = threads_json or _load("threads.json")
    row = _unit_row(units_json, n)
    if row is None:
        raise KeyError(f"unit {n} not in units.json")

    thread_roots = {t["root"] for t in threads_json["threads"]}
    roots = []
    for name, e in (row.get("roots") or {}).items():
        if isinstance(e, str):
            e = {"translit": "", "gloss": ""}
        if name not in thread_roots and not (e.get("translit") or e.get("gloss")):
            continue
        entry = {"root": name,
                 "translit": e.get("translit", ""),
                 "gloss": e.get("gloss", "")}
        if e.get("example"):
            entry["example"] = e["example"]
        if e.get("echo"):
            entry["echo"] = e["echo"]
        roots.append(entry)
    roots.sort(key=lambda r: r["root"])

    opens, payoffs = _threads_touching(threads_json, n)
    meta = {"unit": n, "slug": row["slug"], "passage": row["passage"],
            "title": row["title"]}
    for g in book().groupings:
        if row.get(g) is not None:
            meta[g] = row[g]
    for k in book().meta_keys:
        if row.get(k) is not None:
            meta[k] = row[k]
    if row.get("contract"):
        meta["contract"] = row["contract"]
    meta["roots"] = roots
    meta["threads"] = {"opens": opens, "payoffs": payoffs, "candidates": [], "retro": []}
    return meta
