"""book.json: closed keys, defaults, and per-book groupings reaching the
meta block (the things a new book is allowed to change)."""
import json
import os

import support
from biblecore import book as bookmod
from biblecore import meta

MIN = {"book": "Numbers", "osis": "Num", "slug": "numbers", "language": "hebrew",
       "corpus": {"kind": "oshb", "pin": "morphhb@2.0.2", "word_ids": True}}


def test_minimal_config_is_valid():
    return bookmod.validate_config(MIN)


def test_unknown_top_level_key_fails():
    errs = bookmod.validate_config(dict(MIN, discourse=True))
    if not any("unknown key 'discourse'" in e for e in errs):
        return [f"expected an unknown-key error, got {errs}"]


def test_unknown_nested_keys_fail():
    cfg = dict(MIN, paths={"wordz": "x"}, checks={"nope": True},
               corpus=dict(MIN["corpus"], extra=1))
    errs = bookmod.validate_config(cfg)
    want = ["paths: unknown path 'wordz'", "checks: unknown check 'nope'",
            "corpus: unknown key 'extra'"]
    return [f"missing error: {w}" for w in want if not any(w in e for e in errs)]


def test_default_paths_derive_from_the_book():
    b = bookmod.Book(MIN, "/tmp/numbers")
    got = {k: os.path.relpath(b.path(k), b.root).replace(os.sep, "/")
           for k in ("words", "reading", "style_reference", "retrofit", "out")}
    want = {"words": "Numbers-words.tsv", "reading": "Numbers-reading.txt",
            "style_reference": "numbers_study_style_reference.md",
            "retrofit": "retrofit/retrofit-tags.json", "out": "out"}
    if got != want:
        return [f"{got} != {want}"]
    if not b.source_glob(3).replace(os.sep, "/").endswith("source-artifacts/numbers_03_*.html"):
        return [f"source glob: {b.source_glob(3)}"]


def _meta(**extra):
    m = {"unit": 1, "passage": "Numbers 1:1-54", "title": "t", "roots": [],
         "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []}}
    m.update(extra)
    return m


def test_groupings_are_the_books_own():
    """A book declaring a 'generation' grouping may use it in meta; Joshua's
    'movement' is then an unknown key, not a core one."""
    prev = bookmod._current
    try:
        bookmod.use(bookmod.Book(dict(MIN, groupings=["generation"]), "/tmp/numbers"))
        fails = []
        if meta.validate(_meta(generation=1)):
            fails.append(f"generation rejected: {meta.validate(_meta(generation=1))}")
        if not any("unknown top-level key 'movement'" in e
                   for e in meta.validate(_meta(movement=1))):
            fails.append("movement should be unknown for this book")
        if not any("generation must be an integer" in e
                   for e in meta.validate(_meta(generation="one"))):
            fails.append("non-integer grouping should fail")
        return fails
    finally:
        bookmod.use(prev)


def test_meta_keys_extend_the_schema_and_round_trip():
    prev = bookmod._current
    try:
        bookmod.use(bookmod.Book(dict(MIN, meta_keys=["census"]), "/tmp/numbers"))
        fails = meta.validate(_meta(census="first"))
        uj = {"units": [{"n": 1, "slug": "unit-01", "passage": "Numbers 1:1-54",
                         "title": "t", "census": "first", "built": True}]}
        g = meta.generate(1, uj, {"threads": []})
        if g.get("census") != "first":
            fails.append(f"generate() dropped a declared meta key: {g}")
        return fails
    finally:
        bookmod.use(prev)


def test_opens_note_requirement_is_a_setting():
    m = _meta(threads={"opens": [{"id": "x", "ref": "1:1"}], "payoffs": [],
                       "candidates": [], "retro": []})
    prev = bookmod._current
    try:
        bookmod.use(bookmod.Book(MIN, "/tmp/numbers"))
        strict = meta.validate(m)
        bookmod.use(bookmod.Book(dict(MIN, checks={"opens_note_required": False}),
                                 "/tmp/numbers"))
        loose = meta.validate(m)
    finally:
        bookmod.use(prev)
    fails = []
    if not any("note" in e for e in strict):
        fails.append("default should require opens.note")
    if loose:
        fails.append(f"opens_note_required=false should allow it: {loose}")
    return fails


def test_joshua_fixture_is_a_valid_book():
    return bookmod.validate_config(json.load(open(support.FIXTURE, encoding="utf-8")))
