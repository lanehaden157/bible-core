"""Tiers: the unit map's Tier/Peak/stretches/Digests, the checks, the digest
component, the corpus count of untranslated verses (`untr`), World English
Bible text (USFM parse, pinned fetch), and a tiered scratch book built end to
end from a copy of Numbers. A book without tiers is tests/test_tiers_noop.py."""
import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile

import support
from template_book import make_book
from biblecore import assets, components, emit, fetch, manifest, scan, tiers, units_map as um
from biblecore import validate_units, verify_occurrences, webtext
from biblecore import book as bookmod

EMPTY = {"book": "Test", "unit_count": 0, "groupings": [], "units": []}

WIDE = """# Test map

## Overview

| # | Passage | Working title | Tier | Peak |
|---|---|---|---|---|
| | **PART ONE — A (1:1–3:9)** | | | |
| 01 | 1:1–54 | First | full | ★ |
| 02 | 2:1–20 | Second | condensed; 2:5–9 digest; 2:10 - 12 condensed | |
| 03 | 3:1–9 | Third | digest | |
| 04 | 4:1–9 | Fourth | | no |

## Digests

- 01: First unit, in a sentence or two.
- 02: Second unit summed up.
- 03: Third.
"""

PLAIN = """| # | Passage | Working title |
|---|---|---|
| 01 | 1:1–54 | First |
| 02 | 2:1–20 | Second |
"""


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


# ------------------------------------------------------------- unit map

def test_old_three_column_map_reads_the_same_with_or_without_tiers():
    a, _ = um.plan(PLAIN, [], "Test", EMPTY)
    b, _ = um.plan(PLAIN, [], "Test", EMPTY, tiers=True)
    fails = []
    if a != b:
        fails.append(f"tiers=True changed a plain map: {a} vs {b}")
    if any(k in r for r in a["units"] for k in ("tier", "peak", "stretches", "digest")):
        fails.append(f"a plain map grew tier keys: {a['units']}")
    return fails


def test_wide_map_is_ignored_for_a_tierless_book():
    uj, report = um.plan(WIDE, ["part"], "Test", EMPTY)
    fails = []
    if any(k in r for r in uj["units"] for k in ("tier", "peak", "stretches", "digest")):
        fails.append("a tierless book took tier keys from the map")
    if [r["n"] for r in uj["units"]] != [1, 2, 3, 4]:
        fails.append(f"wide rows not read: {uj['units']}")
    if not any("not true" in r for r in report):
        fails.append(f"no note that the columns were ignored: {report}")
    return fails


def test_tier_peak_stretches_and_digests_parse():
    uj, report = um.plan(WIDE, ["part"], "Test", EMPTY, tiers=True)
    rows = {r["n"]: r for r in uj["units"]}
    fails = []
    want = {1: dict(tier="full", peak=True, digest="First unit, in a sentence or two."),
            2: dict(tier="condensed",
                    stretches=[{"tier": "digest", "verses": "2:5–9"},
                               {"tier": "condensed", "verses": "2:10–12"}],
                    digest="Second unit summed up."),
            3: dict(tier="digest", digest="Third."),
            4: dict(tier="full")}
    for n, w in want.items():
        got = {k: rows[n][k] for k in ("tier", "peak", "stretches", "digest") if k in rows[n]}
        if got != w:
            fails.append(f"unit {n}: {got} != {w}")
    if rows[4].get("peak"):
        fails.append("'no' in the Peak column made a peak")
    if rows[1]["part"] != 1:
        fails.append("the heading row with extra columns lost its grouping")
    return fails


def test_bad_tier_cells_are_reported_not_guessed():
    md = WIDE.replace("| 03 | 3:1–9 | Third | digest |", "| 03 | 3:1–9 | Third | gist; nonsense |")
    uj, report = um.plan(md, ["part"], "Test", EMPTY, tiers=True)
    fails = []
    if not any("unit 3: tier 'gist'" in r for r in report):
        fails.append(f"bad tier not reported: {report}")
    if not any("unit 3: stretch 'nonsense'" in r for r in report):
        fails.append(f"bad stretch not reported: {report}")
    return fails


def test_a_built_row_takes_only_the_tier_keys():
    have = {"book": "Test", "unit_count": 2, "groupings": [],
            "units": [{"n": 1, "slug": "unit-01", "passage": "Test 1:1–54", "title": "Old",
                       "built": True, "roots": {"x": {}}, "contract": "0.30.1",
                       "digest": "the unit's own words"},
                      {"n": 2, "slug": "unit-02", "passage": "Test 2:1–20", "title": "Two",
                       "built": True}]}
    uj, report = um.plan(WIDE, ["part"], "Test", have, tiers=True)
    r1, r2 = uj["units"][0], uj["units"][1]
    fails = []
    if r1["title"] != "Old" or r1["roots"] != {"x": {}} or r1["contract"] != "0.30.1":
        fails.append(f"a built row's own keys changed: {r1}")
    if not r1.get("peak") or r1["tier"] != "full":
        fails.append(f"map-only peak not applied to a built row: {r1}")
    if r1["digest"] != "the unit's own words":
        fails.append("the map's digest overwrote the unit's own")
    if r2.get("digest") != "Second unit summed up." or r2["tier"] != "condensed":
        fails.append(f"map-only digest/tier not applied to a built row: {r2}")
    again, _ = um.plan(WIDE, ["part"], "Test", uj, tiers=True)
    if again != uj:
        fails.append("applying the map twice changed units.json")
    return fails


# ------------------------------------------------------------- checks

def _with_book(tiered=True, components_=("echo", "list", "digest")):
    tmp = tempfile.mkdtemp(prefix="bc-tiers-")
    make_book(tmp, "Leviticus", "Lev", "leviticus")
    p = os.path.join(tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["components"] = list(components_)
    if tiered:
        cfg["tiers"] = True
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))
    return tmp


DIGEST = ('<section class="block digest" data-verses="3:1–9"><h2>T</h2>'
          '<p>It sums up the verses.</p></section>')


def test_row_errors():
    ok = {"n": 1, "passage": "Leviticus 3:1–20", "tier": "condensed", "peak": None}
    ok.pop("peak")
    fails = []
    if tiers.row_errors(ok):
        fails.append(f"a clean row failed: {tiers.row_errors(ok)}")
    bad = [({"n": 1, "tier": "tiny"}, "tier 'tiny'"),
           ({"n": 1, "tier": "digest", "peak": True}, "must be tier full"),
           ({"n": 1, "peak": False}, "peak must be true"),
           ({"n": 1, "passage": "Leviticus 3:1–10", "stretches": [{"tier": "digest", "verses": "4:1–2"}]},
            "outside the unit's passage"),
           ({"n": 1, "passage": "Leviticus 3:1–10",
             "stretches": [{"tier": "digest", "verses": "3:1–5"}, {"tier": "condensed", "verses": "3:5–8"}]},
            "overlaps"),
           ({"n": 1, "passage": "Leviticus 3:1–10", "stretches": [{"tier": "full", "verses": "3:1–5"}]},
            "not condensed or digest")]
    for row, want in bad:
        errs = tiers.row_errors(row)
        if not any(want in e for e in errs):
            fails.append(f"{row} should fail with {want!r}: {errs}")
    return fails


def test_digest_is_required_short_and_covers_its_stretches():
    row = {"n": 3, "passage": "Leviticus 3:1–9", "tier": "digest", "digest": "Short one.", "built": True}
    fails = []
    if tiers.built_errors(row, DIGEST):
        fails.append(f"a covered digest unit failed: {tiers.built_errors(row, DIGEST)}")
    if not any("no digest" in e for e in tiers.built_errors({**row, "digest": ""}, DIGEST)):
        fails.append("a missing digest passed")
    if not any("no digest" in e for e in tiers.built_errors({k: v for k, v in row.items() if k != "digest"}, DIGEST)):
        fails.append("an absent digest passed")
    long = " ".join(["word"] * 81)
    if not any("81 words" in e for e in tiers.built_errors({**row, "digest": long}, DIGEST)):
        fails.append("an 81-word digest passed")
    if tiers.built_errors({**row, "digest": " ".join(["word"] * 80)}, DIGEST):
        fails.append("an 80-word digest failed")
    if not any("not covered" in e for e in tiers.built_errors(row, "<p>nothing</p>")):
        fails.append("a digest unit with no digest block passed")
    stretch = {"n": 3, "passage": "Leviticus 3:1–20", "tier": "full", "digest": "ok.",
               "stretches": [{"tier": "digest", "verses": "3:5–9"}]}
    if tiers.built_errors(stretch, DIGEST):
        fails.append("a digest stretch inside a covering block failed")
    if not any("not covered" in e for e in tiers.built_errors(stretch, DIGEST.replace("3:1–9", "3:1–4"))):
        fails.append("an uncovered digest stretch passed")
    two = (DIGEST.replace("3:1–9", "3:1–4") + DIGEST.replace("3:1–9", "3:5–9"))
    if tiers.built_errors(stretch, two):
        fails.append("two adjacent digest blocks should cover a stretch together")
    return fails


def test_digest_component_checks():
    chk = components.registry()["digest"].check
    fails = []
    if chk(DIGEST, {}):
        fails.append(f"a clean block failed: {chk(DIGEST, {})}")
    for html, want in [(DIGEST.replace(' data-verses="3:1–9"', ""), "needs data-verses"),
                       (DIGEST.replace('class="block digest"', 'class="digest block"'), "block digest"),
                       (DIGEST.replace("<p>It sums up the verses.</p>", "<p> </p>"), "no <p> text")]:
        errs = chk(html, {})
        if not any(want in e for e in errs):
            fails.append(f"{want!r} not caught: {errs}")
    return fails


def test_a_tiered_book_must_enable_the_digest_component():
    tmp = _with_book(components_=("echo", "list"))
    try:
        errs = tiers.validate({"units": []})
        return [] if any("components must include 'digest'" in e for e in errs) else [f"{errs}"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()


def test_tiers_key_must_be_boolean_and_digest_meta_needs_it():
    fails = []
    errs = bookmod.validate_config({**json.load(open(support.FIXTURE, encoding="utf-8")), "tiers": "yes"})
    if not any("'tiers' must be true or false" in e for e in errs):
        fails.append(f"tiers: 'yes' accepted: {errs}")
    return fails


# ------------------------------------------------------------- untranslated counts

def _row(wid, lemma, ch, v):
    return {"word_id": wid, "lemma": lemma, "ch": ch, "v": v}


def test_untranslated_counts_come_from_the_corpus():
    words = [_row("a", "111", 3, 1), _row("b", "111", 3, 2), _row("c", "111", 3, 5),
             _row("d", "111", 3, 6), _row("e", "222", 3, 5), _row("f", "111", 4, 1)]
    roots = {"roots": {"x": {"ids": ["111"]}, "y": {"ids": ["222"]}, "z": {"ids": ["333"]}}}
    row = {"n": 3, "passage": "Leviticus 3:1–6"}
    got = tiers.untranslated(row, "", words, roots, {(3, 1), (3, 2)})
    want = {"x": {"count": 2, "verses": ["3:5", "3:6"]}, "y": {"count": 1, "verses": ["3:5"]}}
    return [] if got == want else [f"{got} != {want}"]


# ------------------------------------------------------------- WEB

USFM = r"""\id LEV World English Bible (WEB)
\h Leviticus
\c 1
\s1 Heading
\p
\v 1 \w Yahweh|strong="H3068"\w*\f + \fr 1:1 \ft note text\f* called \w to|strong="H1696"\w* \nd Moses\nd*.
\v 2 Speak to the children of Israel.
\q1 A line of poetry
\q2 and its answer.
\c 2
\p
\v 1 \add When\add* anyone offers an offering.
\v 3-4 A bridged pair.
"""


def test_usfm_parse():
    got = webtext.parse(USFM)
    want = {1: {1: "Yahweh called to Moses.",
                2: "Speak to the children of Israel. A line of poetry and its answer."},
            2: {1: "When anyone offers an offering.", 3: "A bridged pair."}}
    return [] if {c: dict(v) for c, v in got.items()} == want else [f"{dict(got)}"]


def _zip_with(tmp, name, data):
    path = os.path.join(tmp, "eng-web_usfm.zip")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, data)
    return path


def test_web_fetch_is_pinned_and_emit_writes_chapters():
    tmp = _with_book()
    saved = dict(fetch.WEB_FILES)
    try:
        data = USFM.encode("utf-8")
        name = "04-LEVeng-web.usfm"
        _zip_with(tmp, name, data)
        base = "file:///" + tmp.replace(os.sep, "/")
        b = bookmod.book()
        fails = []
        fetch.WEB_FILES["Lev"] = (name, "0" * 40)
        probs = fetch.fetch_web(b, base=base, log=lambda *_: None)
        if not (probs and "discarded" in probs[0]) or os.path.exists(os.path.join(b.root, "corpus", "web", name)):
            fails.append(f"a download off the pin was kept: {probs}")
        fetch.WEB_FILES["Lev"] = (name, hashlib.sha1(data).hexdigest())
        probs = fetch.fetch_web(b, base=base, log=lambda *_: None)
        dest = os.path.join(b.root, "corpus", "web", name)
        if probs or not os.path.exists(dest):
            fails.append(f"a pinned download wasn't written: {probs}")
        if fetch.fetch_web(b, check_only=True, log=lambda *_: None):
            fails.append("--check failed on a good file")
        with open(dest, "ab") as fh:
            fh.write(b"edit")
        if not any("sha1" in p for p in fetch.fetch_web(b, log=lambda *_: None)):
            fails.append("an edited file wasn't reported")
        with open(dest, "wb") as fh:
            fh.write(data)
        n, problem = webtext.emit(b, log=lambda *_: None)
        c1 = json.load(open(b.data("web/1.json"), encoding="utf-8"))
        if problem or n != 2 or c1["verses"]["1"] != "Yahweh called to Moses.":
            fails.append(f"emit: {n} {problem} {c1}")
        if webtext.emit(b, log=lambda *_: None)[0] != 0:
            fails.append("emit isn't idempotent")
        del fetch.WEB_FILES["Lev"]
        if not fetch.fetch_web(b, log=lambda *_: None):
            fails.append("a book with no pin wasn't reported")
        return fails
    finally:
        fetch.WEB_FILES.clear()
        fetch.WEB_FILES.update(saved)
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()


# ------------------------------------------------------------- a tiered book end to end

def _tiered_numbers(tmp, tiered=True):
    """A private, buildable copy of Numbers (the real corpus read in place),
    tiered, with a small World English Bible file standing in for the pin."""
    dest = os.path.join(tmp, "Numbers")
    shutil.copytree(support.copy_of("Numbers"), dest)
    p = os.path.join(dest, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["paths"] = dict(cfg.get("paths", {}), **support.read_only_paths(support.NUMBERS_SRC))
    if tiered:
        cfg["tiers"] = True
        cfg["components"] = list(cfg["components"]) + ["digest"]
    json.dump(cfg, open(p, "w", encoding="utf-8", newline="\n"), indent=2)
    up = os.path.join(dest, "data", "units.json")
    uj = json.load(open(up, encoding="utf-8"))
    if tiered:
        for r in uj["units"]:
            if r.get("built"):
                r["digest"] = f"Unit {r['n']} in a sentence."
        uj["units"][0].update(tier="condensed", stretches=[{"tier": "condensed", "verses": "1:20–43"}])
        uj["units"][1]["peak"] = True
    json.dump(uj, open(up, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    os.makedirs(os.path.join(dest, "corpus", "web"), exist_ok=True)
    with open(os.path.join(dest, "corpus", "web", "05-NUMeng-web.usfm"), "w", encoding="utf-8") as fh:
        fh.write("\\id NUM\n\\c 1\n\\p\n\\v 22 Of the children of Simeon.\n\\v 23 Those counted.\n")
    bookmod.use(bookmod.Book(cfg, dest))
    return dest


def test_a_tiered_book_builds_end_to_end():
    if not support.have_numbers():
        return []
    tmp = tempfile.mkdtemp(prefix="bc-tiered-")
    saved = dict(fetch.WEB_FILES)
    fails = []
    try:
        dest = _tiered_numbers(tmp)
        b = bookmod.book()
        fetch.WEB_FILES["Num"] = ("05-NUMeng-web.usfm", "0" * 40)
        _quiet(assets.main, [])
        for rel in ("app/tiers.js", "css/components.css"):
            if not os.path.exists(os.path.join(dest, rel)):
                fails.append(f"{rel} not written")
        if "tier-condensed" not in open(os.path.join(dest, "css", "components.css"), encoding="utf-8").read():
            fails.append("the digest component's css (tier shading) isn't in components.css")
        _quiet(scan.main, [])
        occ = json.load(open(b.data("occurrences.json"), encoding="utf-8"))
        untr = {r: e["untr"] for r, e in occ["unit-01"].items() if "untr" in e}
        if not untr:
            fails.append("unit 1's table verses (1:20-43) gave no `untr` counts")
        for r, u in untr.items():
            if not all(20 <= int(v.split(":")[1]) <= 43 and v.startswith("1:") for v in u["verses"]):
                fails.append(f"untr {r} names verses outside the table: {u['verses']}")
            if u["count"] < len(u["verses"]):
                fails.append(f"untr {r}: count {u['count']} < {len(u['verses'])} verses")
        if verify_occurrences.check():
            fails.append(f"verify-occurrences fails on untr-only roots: {verify_occurrences.check()}")
        rc = _quiet(emit.main, [])
        # the fixture USFM's sha1 isn't the real pin, but emit reads the file as it is
        if rc != 0 or not os.path.exists(b.data("web/1.json")):
            fails.append(f"emit didn't write data/web/1.json (rc {rc})")
        _quiet(manifest.main, [])
        m = json.load(open(b.data("manifest.json"), encoding="utf-8"))
        if m.get("tiers") is not True or "web/" not in m["files"]:
            fails.append(f"manifest lacks tiers/web: {m.get('tiers')} {list(m['files'])}")
        if _quiet(validate_units.main, []):
            fails.append("a tiered Numbers with digests failed validation")
        # a built unit without its digest, and one over 80 words, fail the build
        up = b.data("units.json")
        uj = json.load(open(up, encoding="utf-8"))
        del uj["units"][2]["digest"]
        uj["units"][3]["digest"] = " ".join(["w"] * 81)
        json.dump(uj, open(up, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = validate_units.main([])
        if rc != 1 or "no digest" not in buf.getvalue() or "81 words" not in buf.getvalue():
            fails.append(f"missing / long digests didn't fail validation (rc {rc}):\n{buf.getvalue()[-400:]}")
    finally:
        fetch.WEB_FILES.clear()
        fetch.WEB_FILES.update(saved)
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()
    return fails


def test_the_same_book_without_tiers_gets_no_tier_output():
    if not support.have_numbers():
        return []
    tmp = tempfile.mkdtemp(prefix="bc-untiered-")
    fails = []
    try:
        dest = _tiered_numbers(tmp, tiered=False)
        b = bookmod.book()
        _quiet(assets.main, [])
        _quiet(scan.main, [])
        occ = open(b.data("occurrences.json"), encoding="utf-8").read()
        if "untr" in occ:
            fails.append("a tierless scan wrote `untr`")
        if os.path.exists(os.path.join(dest, "app", "tiers.js")):
            fails.append("a tierless book was given app/tiers.js")
        _quiet(manifest.main, [])
        m = json.load(open(b.data("manifest.json"), encoding="utf-8"))
        if "tiers" in m or "web/" in m["files"]:
            fails.append("a tierless manifest mentions tiers or web/")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()
    return fails


# ------------------------------------------------------------- the rest of the opt-in

def test_meta_digest_is_for_tiered_books_only():
    from biblecore import meta as um
    meta = {"unit": 1, "slug": "unit-01", "passage": "Joshua 1:1-18", "title": "T",
            "roots": [], "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
            "digest": "A sentence."}
    support.joshua_book()
    fails = []
    if not any("only a tiered book" in e for e in um.validate(meta, {"threads": []})):
        fails.append("a tierless book accepted a meta digest")
    tmp = _with_book()
    try:
        errs = um.validate({**meta, "passage": "Leviticus 1:1-9"}, {"threads": []})
        if any("digest" in e for e in errs):
            fails.append(f"a tiered book rejected a meta digest: {errs}")
        if not any("non-empty" in e for e in um.validate({**meta, "digest": " "}, {"threads": []})):
            fails.append("a blank meta digest passed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()
    return fails


def test_new_book_routing_and_cards_follow_tiers():
    import sys
    sys.path.insert(0, os.path.join(support.CORE, "tools"))
    import core_sync
    import new_book
    field = open(os.path.join(support.CORE, "template", "CHAT_SIDE_INSTRUCTIONS.md"), encoding="utf-8").read()
    fails = []
    if "card-condensed.md" in new_book.keep_tiers(field, False):
        fails.append("a tierless field routes to the tier card")
    t = new_book.keep_tiers(field, True)
    if "card-condensed.md" not in t or "<!-- tiers" in t or "<!-- /tiers" in t:
        fails.append("a tiered field lost the route or kept a marker")
    tmp = tempfile.mkdtemp(prefix="bc-newtier-")
    try:
        new_book.instantiate(tmp, "Leviticus", "Lev", "leviticus", tiers=True)
        cfg = json.load(open(os.path.join(tmp, "book.json"), encoding="utf-8"))
        if cfg.get("tiers") is not True or "digest" not in cfg["components"]:
            fails.append(f"--tiers didn't write book.json: {cfg}")
        bookmod.Book(cfg, tmp)
        if not os.path.exists(os.path.join(tmp, "lens.md")):
            fails.append("a new book has no lens.md")
        if "card-condensed.md" not in core_sync.canon_files(tmp):
            fails.append("a tiered book isn't given the tier card")
        plain = tempfile.mkdtemp(prefix="bc-newplain-")
        try:
            new_book.instantiate(plain, "Leviticus", "Lev", "leviticus")
            if "card-condensed.md" in core_sync.canon_files(plain):
                fails.append("a tierless book is given the tier card")
        finally:
            shutil.rmtree(plain, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return fails
