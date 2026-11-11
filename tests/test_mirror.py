"""The mirror: a book that reads another book backwards (biblecore/mirror.py),
on a private copy of Numbers mirroring Exodus. The pairs here are fixtures that
exercise the machinery with claims checked against morphhb (F, H, I are the
plan's verified rows); they are not the book's seed data."""
import copy
import io
import json
import os
import shutil
import tempfile
import contextlib

import support
from biblecore import book as bookmod
from biblecore import canon, components, meta as um, mirror, unit_pack
from biblecore.corpus import oshb

_tmp = None
_book = None
FILE = "mirror-exodus.json"

GOOD = {
    "version": 1,
    "centre": {"span": "Exod 19:1 – Num 10:10", "label": "fixture", "note": "n"},
    "sources": [{"id": "s1", "cite": "a source"}],
    "pairs": [
        {"id": "A", "tier": "chiasm", "pos": 1, "here": "Num 22:2–24:25",
         "other": "Exod 5:1–15:21", "title": "The outer pair", "strength": 2,
         "status": "seed", "source": "s1"},
        {"id": "B", "tier": "chiasm", "pos": 2, "here": "Num 22:21–35",
         "other": "Exod 14:5–31", "title": "Nested", "strength": 1,
         "status": "seed", "source": "s1"},
        {"id": "F", "tier": "chiasm", "pos": 6, "here": "Num 13:16–14:38",
         "other": "Exod 17:8–16", "title": "Joshua", "strength": 3,
         "shared": [{"label": "Joshua", "ids": ["3091"],
                     "where": {"here": "Num 13:16", "other": "Exod 17:9"}}],
         "status": "seed", "source": "s1"},
        {"id": "H", "tier": "chiasm", "pos": 7, "here": "Num 11:10–17",
         "other": "Exod 18:13–18", "title": "The burden", "strength": 3,
         "shared": [{"label": "heavy", "ids": ["3515"],
                     "where": {"here": "Num 11:14", "other": "Exod 18:18"}},
                    {"label": "alone", "ids": ["905"],
                     "where": {"here": "Num 11:14", "other": "Exod 18:18"}}],
         "status": "seed", "source": "s1", "note": "a note"},
        {"id": "I", "tier": "chiasm", "pos": 8, "here": "Num 10:29–36",
         "other": "Exod 18:19–27", "title": "Hobab", "strength": 2,
         "status": "seed", "source": "s1"},
        {"id": "P", "tier": "chiasm", "pos": 9, "here": "Num 15:32–36",
         "other": "Exod 15:22–17:7", "title": "A poetry-twin fixture", "strength": 2,
         "poetry": "other", "status": "seed", "source": "s1"},
        {"id": "E1", "tier": "echo", "here": "Num 25:1–5", "other": "Exod 32:6",
         "title": "The calf", "strength": 1, "status": "kept", "source": "s1"},
    ],
}


def _write(data):
    with open(os.path.join(_book.root, "data", FILE), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def setup():
    global _tmp, _book
    if not support.have_numbers():
        return
    _tmp = tempfile.mkdtemp(prefix="bc-mirror-")
    root = os.path.join(_tmp, "Numbers")
    shutil.copytree(support.copy_of("Numbers"), root)
    cfg = json.load(open(os.path.join(root, "book.json"), encoding="utf-8"))
    cfg["paths"] = dict(cfg.get("paths", {}), **support.read_only_paths(support.NUMBERS_SRC))
    cfg["components"] = cfg["components"] + ["mirror"]
    cfg["mirrors"] = [{"with": "Exod", "file": FILE}]
    _book = bookmod.use(bookmod.Book(cfg, root))
    _write(GOOD)


def teardown():
    if _tmp:
        shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _have():
    return _book is not None


def _errs_for(mutate):
    data = copy.deepcopy(GOOD)
    mutate(data)
    errs, _notes = mirror.validate_data(_book, "Exod", data, FILE)
    return errs


# ------------------------------------------------------------ book.json key

def test_mirrors_key_is_closed_and_checked():
    base = {"book": "X", "osis": "Num", "slug": "x", "language": "hebrew",
            "corpus": {"kind": "oshb"}}
    ok = bookmod.validate_config({**base, "mirrors": [{"with": "Exod", "file": "m.json"}]})
    assert ok == [], ok
    bad = {
        "not a list": {"with": "Exod", "file": "m.json"},
        "unknown book": [{"with": "Exodus", "file": "m.json"}],
        "itself": [{"with": "Num", "file": "m.json"}],
        "path in file": [{"with": "Exod", "file": "../m.json"}],
        "extra key": [{"with": "Exod", "file": "m.json", "x": 1}],
        "twice": [{"with": "Exod", "file": "a.json"}, {"with": "Exod", "file": "b.json"}],
    }
    fails = [k for k, v in bad.items() if not bookmod.validate_config({**base, "mirrors": v})]
    greek = bookmod.validate_config({**base, "language": "greek",
                                     "mirrors": [{"with": "Exod", "file": "m.json"}]})
    if not greek:
        fails.append("a Greek book may not mirror yet")
    return [f"accepted: {k}" for k in fails]


# ------------------------------------------------------- second-book reading

def test_second_book_reads_in_english_numbering():
    if not _have():
        return
    rows = oshb.load_other_words("Exod", _book)
    cvs = {(w["ch"], w["v"]) for w in rows}
    fails = []
    if (8, 32) not in cvs:
        fails.append("Exod 8:32 (English) missing: VerseMap not applied")
    if (7, 29) in cvs:
        fails.append("Exod 7:29 present: still Hebrew numbering")
    if (22, 31) not in cvs:
        fails.append("Exod 22:31 (English) missing")
    w = rows[0]
    if not (w["lemma"] and w["surface"] and w["word_id"] and w["lang"] == "hebrew"):
        fails.append(f"row shape {w}")
    # Ketiv rows are dropped the way load_words drops them: no row pair shares a ref with an unpointed first
    if oshb.load_other_words("Exod", _book) is not rows:
        fails.append("not cached")
    try:
        oshb.load_other_words("Exodus", _book)
        fails.append("a bad book id was accepted")
    except ValueError:
        pass
    return fails


def test_this_books_words_unchanged_by_the_refactor():
    if not _have():
        return
    words = oshb.load_words(_book)
    return [] if words and words[0]["ref"].startswith("Num.1.1") else ["Numbers words changed"]


# ------------------------------------------------------------------- check

def test_clean_data_passes_and_reports_structure():
    if not _have():
        return
    errs, notes = mirror.check(_book)
    assert errs == [], errs
    text = "; ".join(notes)
    assert notes[0] == "7 pair(s)", notes
    assert "nesting: A contains B" in text, text           # reported, not failed
    assert "wide:" not in text or "units" in text
    return []


def test_check_catches_the_failures_the_plan_names():
    if not _have():
        return
    fails = []

    def expect(label, mutate, needle):
        errs = _errs_for(mutate)
        if not any(needle in e for e in errs):
            fails.append(f"{label}: wanted {needle!r}, got {errs}")

    def bad_ref(d):
        d["pairs"][4]["other"] = "Exod 99:1"
    expect("a ref that doesn't resolve", bad_ref, "does not resolve")

    def missing_lemma(d):   # Midian (H4084) is not in Exod 18:19-27 (the plan's pair I)
        d["pairs"][4]["shared"] = [{"label": "Midian", "ids": ["4084"],
                                    "where": {"here": "Num 10:29", "other": "Exod 18:19"}}]
    expect("a shared lemma missing from a passage", missing_lemma, "H4084 is not in Exod 18:19")

    def strength3_no_evidence(d):
        d["pairs"][4]["strength"] = 3
    expect("strength 3 with no shared entry", strength3_no_evidence, "strength 3 needs a passing")

    def strength3_failed_claim(d):   # a failed claim must not leave the third dot
        d["pairs"][4]["strength"] = 3
        d["pairs"][4]["shared"] = [{"label": "Midian", "ids": ["4084"],
                                    "where": {"here": "Num 10:29", "other": "Exod 18:19"}}]
    expect("a failed claim keeps no third dot", strength3_failed_claim, "strength 3 needs a passing")

    def outside(d):
        d["pairs"][3]["shared"][0]["where"]["other"] = "Exod 17:9"
    expect("shared ref outside the pair", outside, "lies outside the pair")

    def dup_pos(d):
        d["pairs"][1]["pos"] = 1
    expect("duplicate pos", dup_pos, "also pair A")

    def unknown(d):
        d["pairs"][0]["colour"] = "red"
    expect("unknown key", unknown, "unknown key 'colour'")

    def echo_pos(d):
        d["pairs"][6]["pos"] = 3
    expect("echo with a position", echo_pos, "echo pair has no 'pos'")

    def wrong_book(d):
        d["pairs"][0]["other"] = "Lev 1:1"
    expect("twin in the wrong book", wrong_book, "expected Exod")
    return fails


def test_passing_claim_is_really_in_both_passages():
    """Pair F's Joshua and pair H's kaved/levad, the plan's verified rows."""
    if not _have():
        return
    errs, _n = mirror.validate_data(_book, "Exod", copy.deepcopy(GOOD), FILE)
    return errs


def test_order_that_does_not_reverse_is_a_note_not_an_error():
    if not _have():
        return
    data = copy.deepcopy(GOOD)
    data["pairs"][3]["pos"], data["pairs"][4]["pos"] = 8, 7      # H and I swap
    errs, notes = mirror.validate_data(_book, "Exod", data, FILE)
    assert not errs, errs
    assert any(n.startswith("order:") for n in notes), notes


# ----------------------------------------------------------- the check wiring

def test_selftest_has_a_mirror_check():
    from biblecore import selftest
    assert "mirror" in [n for n, _f in selftest.CHECKS]
    if not _have():
        return
    errs, notes = selftest.check_mirror()
    assert errs == [] and notes, (errs, notes)


def test_missing_file_is_an_error():
    if not _have():
        return
    p = os.path.join(_book.root, "data", FILE)
    os.rename(p, p + ".off")
    try:
        errs, _n = mirror.check(_book)
    finally:
        os.rename(p + ".off", p)
    assert errs and "not found" in errs[0], errs


# --------------------------------------------------------------- the component

META = {"passage": "Numbers 11:1-35", "contract": "0.29.0"}
BOX = ('<p class="v"><span class="n">14</span> I alone.</p>'
       '<aside class="mirror" data-anchor="11:14" data-pair="H" data-span="11:10–17">'
       '<h4><span class="par-title">The burden</span> <span class="par-ref">Exod 18:13–18</span>'
       ' <span class="strength"></span></h4>'
       '<div class="row"><span class="src">Exod 18:18</span><span class="txt">too '
       '<span class="sh" data-ids="3515">heavy</span> for you, you cannot do it '
       '<span class="sh" data-ids="905">alone</span></span></div>'
       '<p class="take">The same weight.</p></aside>')


def test_component_is_registered_whole():
    reg = components.registry()
    c = reg["mirror"]
    fails = []
    for f in ("style.css", "snippet.md", "__init__.py"):
        if not os.path.exists(os.path.join(c.folder, f)):
            fails.append(f"lacks {f}")
    for cls in c.spec["classes"]:
        if f".{cls}" not in c.read("style.css"):
            fails.append(f"class {cls} has no rule")
    return fails


def test_component_accepts_a_good_box_and_rejects_the_bad():
    if not _have():
        return
    chk = components.registry()["mirror"].check
    fails = []
    good = chk(BOX, META)
    if good:
        fails.append(f"good box rejected: {good}")
    cases = {
        "unknown pair": BOX.replace('data-pair="H"', 'data-pair="Z"'),
        "no pair": BOX.replace(' data-pair="H"', ''),
        "anchor outside the pair": BOX.replace('data-anchor="11:14"', 'data-anchor="11:30"'),
        "ref outside the twin": BOX.replace("Exod 18:13–18", "Exod 17:8–16"),
        "ref in the wrong book": BOX.replace("Exod 18:13–18", "Lev 18:13–18"),
        "word not in shared": BOX.replace('data-ids="905"', 'data-ids="1234"'),
        "sh without ids": BOX.replace(' data-ids="905"', ""),
        "wrong dots": BOX.replace('<span class="strength"></span>',
                                  '<span class="strength" data-n="1">●○○</span>'),
        "no take": BOX.replace('<p class="take">The same weight.</p>', ""),
        "no rows": BOX.replace('<div class="row">', '<div class="x">'),
        "script": BOX.replace("heavy", "heavy " + "כבד"),
        "data-root": BOX.replace('<span class="sh" data-ids="3515">', '<span data-root="x" class="sh" data-ids="3515">'),
        "span outside unit": BOX.replace('data-span="11:10–17"', 'data-span="12:1–3"'),
        "pair not kept": BOX,
    }
    for label, html in cases.items():
        if label == "pair not kept":
            data = copy.deepcopy(GOOD)
            data["pairs"][3]["status"] = "draft"
            _write(data)
            try:
                errs = chk(html, META)
            finally:
                _write(GOOD)
        else:
            errs = chk(html, META)
        if not errs:
            fails.append(f"accepted: {label}")
    return fails


def test_poetry_twin_takes_no_rows_and_echo_no_dots():
    if not _have():
        return
    chk = components.registry()["mirror"].check
    poetry = ('<p class="v"><span class="n">32</span> x.</p>'
              '<aside class="mirror" data-anchor="15:32" data-pair="P">'
              '<h4><span class="par-title">t</span> <span class="par-ref">Exod 15:22–27</span></h4>'
              '<p class="take">Ref and title only.</p></aside>')
    meta = {"passage": "Numbers 15:32-41", "contract": "0.29.0"}
    fails = []
    if chk(poetry, meta):
        fails.append(f"a poetry twin with no rows rejected: {chk(poetry, meta)}")
    with_row = poetry.replace('<p class="take">', '<div class="row"><span class="src">a</span>'
                              '<span class="txt">b</span></div><p class="take">')
    if not chk(with_row, meta):
        fails.append("a poetry twin with rows accepted")
    echo = poetry.replace('data-pair="P"', 'data-pair="E1"').replace("Exod 15:22–27", "Exod 32:6").replace(
        'data-anchor="15:32"', 'data-anchor="25:2"').replace(
        '</h4>', ' <span class="strength"></span></h4>').replace(
        '<p class="take">', '<div class="row"><span class="src">a</span><span class="txt">b</span></div>'
        '<p class="take">')
    emeta = {"passage": "Numbers 25:1-9", "contract": "0.29.0"}
    echo = echo.replace('<span class="n">32</span>', '<span class="n">2</span>')
    if not any("echo-tier" in e for e in chk(echo, emeta)):
        fails.append(f"an echo box with dots accepted: {chk(echo, emeta)}")
    return fails


def test_component_without_a_configured_mirror_is_an_error():
    if not _have():
        return
    saved = _book.cfg.pop("mirrors")
    try:
        errs = components.registry()["mirror"].check(BOX, META)
    finally:
        _book.cfg["mirrors"] = saved
    assert any("declares no mirrors" in e for e in errs), errs


# ------------------------------------------------------------- strength dots

def test_build_fills_dots_and_is_idempotent():
    if not _have():
        return
    table = mirror.pair_table(_book)
    once = mirror.fill_html(BOX, table)
    twice = mirror.fill_html(once, table)
    fails = []
    if 'data-n="3"' not in once or "●●●" not in once:
        fails.append(f"dots not written: {once}")
    if once != twice:
        fails.append("fill is not idempotent")
    wrong = mirror.fill_html(BOX.replace('<span class="strength"></span>',
                                         '<span class="strength" data-n="1">●○○</span>'), table)
    if wrong != once:
        fails.append("a wrong span is not corrected")
    nospan = mirror.fill_html(BOX.replace(' <span class="strength"></span>', ""), table)
    if nospan != once.replace(' <span class="strength"', ' <span class="strength"'):
        if "●●●" not in nospan:
            fails.append("a missing span is not inserted")
    echo = BOX.replace('data-pair="H"', 'data-pair="E1"')
    if mirror.fill_html(echo, table) != echo:
        fails.append("an echo box was given dots")
    if components.registry()["mirror"].check(once, META):
        fails.append(f"a filled box fails its own check: {components.registry()['mirror'].check(once, META)}")
    return fails


def test_fill_units_writes_lf_and_only_changed_units():
    if not _have():
        return
    path = _book.unit_path(1)
    saved = open(path, encoding="utf-8", newline="").read()
    uj_path = os.path.join(_book.root, "data", "units.json")
    try:
        # put a mirror box into unit 1's html for the test (the pair's anchor
        # check is the component's job, not fill's)
        html = saved.replace("</article>", BOX + "</article>")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        changed = mirror.fill_units(_book)
        after = open(path, "rb").read()
        again = mirror.fill_units(_book)
    finally:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(saved)
    assert changed == [1] and again == [], (changed, again)
    assert b"\r\n" not in after and "●●●".encode() in after


# ----------------------------------------------------------------- canon kind

def test_canon_kind_mirror_and_harvest():
    assert "mirror" in canon.KINDS and "mirror" in canon.HARVESTED
    rows = canon.harvest_mirrors(BOX, 11, abbrev="Num")
    assert rows == [{"from": "Num 11:14", "to": "Exod 18:13–18", "kind": "mirror", "unit": 11,
                     "note": "pair H: The burden", "source": "mirror"}], rows
    assert canon.harvest_mirrors('<aside class="mirror" data-anchor="bad"><h4>'
                                 '<span class="par-ref">Exod 1:1</span></h4></aside>', 1) == []
    # a mirror kind is allowed in a meta block's intertext[] too
    assert canon.validate_meta({"intertext": [{"ref": "1:1", "to": "Exod 1:1", "kind": "mirror"}]}) == []


# ------------------------------------------------------------ the pack section

def test_pack_has_an_exodus_mirror_section_for_a_pair_unit():
    if not _have():
        return
    units = json.load(open(_book.data("units.json"), encoding="utf-8"))["units"]
    n = next(u["n"] for u in units if u["passage"].startswith("Numbers 11:") or u["passage"].startswith("11:"))
    md, st = unit_pack.build_pack(_book, n)
    fails = []
    for needle in ("## Exodus mirror", "### Pair H: The burden", "strength 3 of 3",
                   "Exod 18:13–18", "Shared words", "heavy (H3515)", "twin text",
                   "| lemma | form | gloss"):
        if needle not in md:
            fails.append(f"missing {needle!r}")
    if any("֐" <= c <= "׿" for c in md):
        fails.append("native Hebrew in the pack")
    if "A reading, not a fact" not in md:
        fails.append("the reading caveat is missing")
    return fails


def test_pack_trims_a_wide_twin_and_stays_in_budget():
    if not _have():
        return
    lines, note = mirror._twin_lines(mirror.verse_index(_book, "Exod"), "Exod",
                                     mirror.parse_span("Exod 5:1–15:21"), {"3091"}, cap=12)
    assert len(lines) == 12 and "Trimmed to 12 of" in note, (len(lines), note)
    full, none = mirror._twin_lines(mirror.verse_index(_book, "Exod"), "Exod",
                                    mirror.parse_span("Exod 18:13–18"), set())
    assert len(full) == 6 and none == ""


def test_pack_for_a_unit_with_no_pair_lists_exodus_leads():
    if not _have():
        return
    md, _st = unit_pack.build_pack(_book, 1)
    assert "## Exodus mirror" in md and "No pair of the Exodus mirror overlaps this unit" in md
    assert "Rare words" in md and "Two-word phrases" in md
    assert not any("֐" <= c <= "׿" for c in md)


def test_pack_is_unchanged_for_a_book_that_mirrors_nothing():
    if not _have():
        return
    saved = _book.cfg.pop("mirrors")
    try:
        md, _st = unit_pack.build_pack(_book, 1)
    finally:
        _book.cfg["mirrors"] = saved
    assert "mirror" not in md.lower().replace("unit pack", "")


# ---------------------------------------------------------- proposals (mirror[])

PROPOSAL = {"ref": "11:14", "to": "Exod 18:18", "tier": "echo", "title": "Too heavy alone",
            "strength": 3, "note": "Moses carries the people alone.",
            "shared": [{"label": "heavy", "ids": ["3515"],
                        "where": {"here": "Num 11:14", "other": "Exod 18:18"}}]}


def test_mirror_key_shape_is_validated_in_meta():
    assert mirror.validate_meta({"mirror": [PROPOSAL]}) == []
    bad = mirror.validate_meta({"mirror": [{"ref": "Num 11:14", "to": "somewhere", "tier": "x",
                                            "strength": 4, "z": 1}]})
    text = "; ".join(bad)
    for needle in ("'ref' must be", "'to' must name", "'tier' must be", "'strength'",
                   "unknown key 'z'", "missing 'title'", "missing 'note'"):
        assert needle in text, (needle, text)
    # the closed meta key set takes it, so a unit carrying it validates
    assert "mirror" in um.CORE_TOP_LEVEL_KEYS


def test_proposals_resolve_write_a_delta_and_keep_only_by_decision():
    if not _have():
        return
    delta = mirror.delta_path(_book)
    os.makedirs(os.path.dirname(delta), exist_ok=True)
    if os.path.exists(delta):
        os.remove(delta)
    before = open(os.path.join(_book.root, "data", FILE), "rb").read()
    props, errs = mirror.port_proposals({"mirror": [PROPOSAL]}, 11)
    assert not errs and len(props) == 1, (props, errs)
    p = props[0]
    assert p["id"] == "u11-1" and p["shared_passed"] == 1 and p["strength_supported"] and p["status"] == "proposed"
    assert json.load(open(delta, encoding="utf-8"))["proposals"][0]["ref"] == "Num 11:14"
    # the porter never writes the data file
    assert open(os.path.join(_book.root, "data", FILE), "rb").read() == before
    # a re-port of the same unit replaces its proposals
    mirror.port_proposals({"mirror": [PROPOSAL, {**PROPOSAL, "ref": "11:15"}]}, 11)
    assert len(json.load(open(delta, encoding="utf-8"))["proposals"]) == 2
    # a ref that doesn't resolve is an error; a failed shared claim is recorded, not hidden
    _p, errs = mirror.port_proposals({"mirror": [{**PROPOSAL, "to": "Exod 99:1"}]}, 12, write=False)
    assert errs and "does not resolve" in errs[0], errs
    weak = {**PROPOSAL, "shared": [{"label": "Midian", "ids": ["4084"],
                                    "where": {"here": "Num 10:29", "other": "Exod 18:19"}}], "ref": "10:29",
            "to": "Exod 18:19"}
    wp, werrs = mirror.port_proposals({"mirror": [weak]}, 10, write=False)
    assert not werrs and wp[0]["shared_failures"] and not wp[0]["strength_supported"], wp
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mirror.print_proposals(wp)
    assert "FAILS" in buf.getvalue() and "cannot be kept at 3" in buf.getvalue()
    # and no mirror configured is an error, not silence
    saved = _book.cfg.pop("mirrors")
    try:
        _p, errs = mirror.port_proposals({"mirror": [PROPOSAL]}, 11, write=False)
    finally:
        _book.cfg["mirrors"] = saved
    assert errs and "declares no mirrors" in errs[0]


def test_keep_writes_the_pair_and_rolls_back_a_bad_one():
    if not _have():
        return
    data_path = os.path.join(_book.root, "data", FILE)
    original = open(data_path, "rb").read()
    delta = mirror.delta_path(_book)
    try:
        if os.path.exists(delta):
            os.remove(delta)
        mirror.port_proposals({"mirror": [{**PROPOSAL, "tier": "chiasm"}, PROPOSAL]}, 11)
        # a chiasm proposal needs a position
        try:
            mirror.keep("u11-1")
            raise AssertionError("kept a chiasm pair with no --pos")
        except mirror.MirrorError as exc:
            assert "--pos" in str(exc)
        pair = mirror.keep("u11-2")
        assert pair["id"] == "K1" and pair["status"] == "kept" and pair["tier"] == "echo", pair
        assert "pos" not in pair and pair["here"] == "Num 11:14" and pair["other"] == "Exod 18:18"
        saved = json.load(open(data_path, encoding="utf-8"))
        assert saved["pairs"][-1]["id"] == "K1"
        assert b"\r\n" not in open(data_path, "rb").read()
        # keeping again is refused
        try:
            mirror.keep("u11-2")
            raise AssertionError("kept twice")
        except mirror.MirrorError:
            pass
        # a pair that would fail the check is rolled back, the file untouched
        before = open(data_path, "rb").read()
        mirror.port_proposals({"mirror": [{**PROPOSAL, "strength": 3, "ref": "10:29", "to": "Exod 18:19",
                                           "shared": [{"label": "Midian", "ids": ["4084"],
                                                       "where": {"here": "Num 10:29",
                                                                 "other": "Exod 18:19"}}]}]}, 10)
        try:
            mirror.keep("u10-1")
            raise AssertionError("kept an unsupported strength 3")
        except mirror.MirrorError as exc:
            assert "would fail its check" in str(exc), exc
        assert open(data_path, "rb").read() == before
        d = mirror.decline("u10-1")
        assert d["status"] == "declined"
    finally:
        with open(data_path, "wb") as fh:
            fh.write(original)
        if os.path.exists(delta):
            os.remove(delta)


def test_cli_checks_and_reports_a_problem():
    if not _have():
        return
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = mirror.main([])
    assert rc == 0 and "mirror: 7 pair(s) ok" in out.getvalue(), out.getvalue()
    bad = copy.deepcopy(GOOD)
    bad["pairs"][4]["other"] = "Exod 99:1"
    _write(bad)
    try:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = mirror.main([])
    finally:
        _write(GOOD)
    assert rc == 1 and "ERROR" in out.getvalue()


def test_half_verse_letter_and_nested_pairs():
    assert mirror.parse_span("Num 21:16–18a") == ("Num", (21, 16), (21, 18))
    assert mirror.parse_span("Num 21:18b") == ("Num", (21, 18), (21, 18))
    if not _have():
        return
    data = copy.deepcopy(GOOD)
    errs, notes = mirror.validate_data(_book, "Exod", data, FILE)
    assert not any(n.startswith("order: A then B") for n in notes), notes
    # null pos/poetry and the research file's extra keys are fine
    data["pairs"][6]["pos"], data["pairs"][6]["poetry"] = None, None
    data["pairs"][2]["strength_why"], data["pairs"][2]["unverified"] = "why", True
    errs, _n = mirror.validate_data(_book, "Exod", data, FILE)
    assert errs == [], errs


def test_mirror_is_a_cli_command():
    from biblecore import __main__ as cli
    assert cli.COMMANDS["mirror"] == ("biblecore.mirror", "main") and "mirror" in cli.ARGPARSED
    assert "mirror" in cli.__doc__
