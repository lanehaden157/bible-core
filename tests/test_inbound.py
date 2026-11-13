"""Inbound leads (the unit pack's "Already cited from"): rows pointing into a
unit are listed, others not, grouped by book and unit; mirror-file pairs, law
and bible-core canon/ rows included. Built from a synthetic folder of books."""
import json
import os
import tempfile

import support  # noqa: F401  (puts the core on sys.path)
from biblecore import inbound
from biblecore.book import Book


def _w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)


def _book(root, name, osis, slug, rows, units, mirrors=None, pairs=None):
    folder = os.path.join(root, name)
    cfg = {"book": name, "osis": osis, "abbrev": osis, "slug": slug, "language": "hebrew",
           "corpus": {"kind": "oshb", "pin": "morphhb@2.0.2", "word_ids": True}}
    if mirrors:
        cfg["mirrors"] = mirrors
    _w(os.path.join(folder, "book.json"), cfg)
    _w(os.path.join(folder, "data", "units.json"),
       {"units": [{"n": n, "title": t, "passage": "1:1-2:2"} for n, t in units]})
    _w(os.path.join(folder, "data", "canon.json"), {"intertext": rows, "typescenes": []})
    if pairs:
        _w(os.path.join(folder, "data", mirrors[0]["file"]), {"version": 1, "pairs": pairs})
    return Book.from_file(os.path.join(folder, "book.json"))


def _world():
    root = tempfile.mkdtemp(prefix="inbound-")
    lev = _book(root, "Leviticus", "Lev", "leviticus",
                [{"from": "Lev 10:1", "to": "Lev 8:36", "kind": "echo", "unit": 3, "note": "own", "source": "echo"},
                 {"from": "Lev 8:5", "to": "Exod 29:1", "kind": "echo", "unit": 2, "note": "", "source": "echo"}],
                [(2, "Ordination"), (3, "Nadab")])
    _book(root, "Numbers", "Num", "numbers",
          [{"from": "Num 3:4", "to": "Lev 10:1–2", "kind": "story", "unit": 2, "note": "fire", "source": "story"},
           {"from": "Num 6:1", "to": "Lev 8:12", "kind": "echo", "unit": 4, "note": "oil", "source": "echo"},
           {"from": "Num 6:2", "to": "Lev 9:24", "kind": "law", "unit": 4, "note": "law x", "source": "law"},
           {"from": "Num 7:1", "to": "Lev 12:1", "kind": "echo", "unit": 5, "note": "out", "source": "echo"},
           {"from": "Num 1:1", "to": "Lev 8:12", "kind": "echo", "unit": 1, "note": "first", "source": "echo"}],
          [(1, "Census"), (2, "Priests"), (4, "Nazirite"), (5, "Gifts")],
          mirrors=[{"with": "Exod", "file": "mirror-exodus.json"}],
          pairs=[{"id": "Q", "here": "Num 5:1", "other": "Exod 40:1", "title": "no"}])
    _book(root, "Exodus", "Exod", "exodus", [], [(1, "x")],
          mirrors=[{"with": "Lev", "file": "mirror-leviticus.json"}],
          pairs=[{"id": "M", "here": "Exod 40:1–33", "other": "Lev 8:1–9:24", "title": "Setting up"}])
    _w(os.path.join(root, "bible-core", "canon", "intertext.json"),
       {"edges": [{"from": "Josh 1:1", "to": "Lev 8:20", "kind": "allusion", "unit": 1, "note": "hand",
                   "source": "hand", "book": "joshua"},
                  {"from": "Num 6:1", "to": "Lev 8:12", "kind": "echo", "unit": 4, "note": "oil",
                   "source": "echo", "book": "numbers"}]})
    _w(os.path.join(root, "bible-core", "canon", "books.json"),
       {"books": [{"osis": "Josh", "slug": "joshua"}, {"osis": "Num", "slug": "numbers"},
                  {"osis": "Exod", "slug": "exodus"}, {"osis": "Lev", "slug": "leviticus"}]})
    return lev


def test_targets_in_range_are_listed_and_others_not():
    b = _world()
    rows = inbound.inbound(b, (8, 1), (9, 24), 1)
    tos = {(r["from"], r["to"]) for r in rows}
    assert ("Num 6:1", "Lev 8:12") in tos and ("Num 6:2", "Lev 9:24") in tos
    assert ("Josh 1:1", "Lev 8:20") in tos and ("Lev 10:1", "Lev 8:36") in tos
    assert ("Num 3:4", "Lev 10:1–2") not in tos and ("Num 7:1", "Lev 12:1") not in tos
    assert ("Lev 8:5", "Exod 29:1") not in tos          # target is another book


def test_boundaries_and_ranges_overlap():
    b = _world()
    assert any(r["to"] == "Lev 10:1–2" for r in inbound.inbound(b, (9, 24), (10, 1), 1))
    assert not any(r["to"] == "Lev 10:1–2" for r in inbound.inbound(b, (8, 1), (9, 24), 1))


def test_dedup_across_stores_and_own_unit_skipped():
    b = _world()
    rows = inbound.inbound(b, (8, 1), (9, 24), 1)
    assert sum(1 for r in rows if r["from"] == "Num 6:1") == 1       # canon.json + canon/ once
    # unit 3 made the Lev 10:1 -> 8:36 row; asking as unit 3 hides it
    assert not any(r["from"] == "Lev 10:1" for r in inbound.inbound(b, (8, 1), (9, 24), 3))


def test_mirror_pairs_and_law_rows_included():
    b = _world()
    rows = inbound.inbound(b, (8, 1), (9, 24), 1)
    assert any(r["kind"] == "mirror" and r["from"] == "Exod 40:1–33" and "Setting up" in r["note"] for r in rows)
    assert any(r["kind"] == "law" and r["from"] == "Num 6:2" for r in rows)
    # a pair only counts for the side that points into the unit
    assert not any(r["from"] == "Num 5:1" for r in rows)


def test_pack_section_groups_by_book_and_unit():
    b = _world()
    md = "\n".join(inbound.pack_section(b, 1, (8, 1), (9, 24)))
    assert md.startswith("## Already cited from")
    assert "**Numbers unit 4: Nazirite**" in md and "**Leviticus unit 3: Nadab**" in md
    assert "**Exodus (mirror file)**" in md
    assert md.index("Josh") < md.index("**Numbers unit 4") < md.index("**Exodus")
    assert md.count("Lev 8:12 ← Num 6:1") == 1 and "Lev 9:24 ← Num 6:2 · law" in md


def test_empty_section_says_none():
    b = _world()
    md = "\n".join(inbound.pack_section(b, 1, (20, 1), (20, 9)))
    assert "_None" in md and "←" not in md


def test_book_with_no_siblings_still_works():
    root = tempfile.mkdtemp(prefix="inbound-solo-")
    b = _book(root, "Leviticus", "Lev", "leviticus", [], [(1, "a")])
    assert inbound.inbound(b, (1, 1), (2, 2), 1) == []
