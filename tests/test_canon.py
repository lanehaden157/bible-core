"""canon.py (a book's intertext/type-scene rows) and tools/canon_collect.py
(the roll-up into bible-core/canon/). Joshua's echoes are harvested
read-only; the collector test runs against a scratch books folder."""
import json
import os
import shutil
import sys
import tempfile

import support
from biblecore import canon
from biblecore import meta as um

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import canon_collect  # noqa: E402


def test_parse_refs_continuations_and_prose():
    p = canon.parse_refs
    assert p("Isa 40:26; Ps 147:4 — the promise (Gen 15:5; 22:17)") == \
        ["Isa 40:26", "Ps 147:4", "Gen 15:5", "Gen 22:17"]
    assert p("Deut 31:6, 8 — and Heb 13:5") == ["Deut 31:6", "Deut 31:8", "Heb 13:5"]
    assert p("over Saul (2 Sam 1:1) and 1 Chr 6:22") == ["2 Sam 1:1", "1 Chr 6:22"]
    assert p("Deut 11:24–25 — nearly") == ["Deut 11:24–25"]
    assert p("verses 22-43 repeat; Rise 1:2") == []


def test_harvest_joshua_unit_1_echoes():
    path = os.path.join(support.JOSHUA, "units", "unit-01.html")
    html = support.read(path)
    rows = canon.harvest(html, 1, abbrev="Josh", meta=um.parse(html))
    pairs = {(r["from"], r["to"]) for r in rows}
    for want in [("Josh 1:5", "Exod 3:12"), ("Josh 1:13", "Deut 3:18–20"),
                 ("Josh 1:2", "Gen 13:17"), ("Josh 1:8", "Ps 1:2–3")]:
        assert want in pairs, (want, sorted(pairs)[:10])
    assert all(r["source"] == "echo" and r["kind"] == "echo" for r in rows)


def test_meta_entries_validate():
    good = {"intertext": [{"ref": "6:24", "to": "Ps 67:1", "kind": "echo", "note": "x"}],
            "typescenes": [{"id": "blessing", "ref": "6:23", "label": "Priestly blessing"}]}
    assert canon.validate_meta(good) == []
    bad = {"intertext": [{"ref": "Num 6:24", "to": "somewhere", "kind": "hint", "x": 1}],
           "typescenes": [{"id": "Bad Id", "ref": "6"}]}
    errs = canon.validate_meta(bad)
    for frag in ("'ref'", "'to'", "'kind'", "unknown key 'x'", "'id'"):
        assert any(frag in e for e in errs), (frag, errs)


def test_meta_keys_are_allowed_top_level():
    m = {"unit": 1, "passage": "Joshua 1:1-18", "title": "t", "roots": [],
         "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
         "intertext": [{"ref": "1:5", "to": "Exod 3:12", "kind": "echo"}],
         "typescenes": [{"id": "commissioning", "ref": "1:6"}]}
    support.joshua_book()
    assert um.validate(m) == [], um.validate(m)


def test_collect_merges_books_keeps_hand_rows():
    root = tempfile.mkdtemp(prefix="biblecore-canon-")
    try:
        cdir = os.path.join(root, "bible-core", "canon")
        shutil.copytree(os.path.join(support.CORE, "canon"), cdir)
        book = os.path.join(root, "Testbook", "data")
        os.makedirs(book)
        json.dump({"slug": "testbook"}, open(os.path.join(root, "Testbook", "book.json"), "w"))
        json.dump({"threads": [{"id": "charge"}]}, open(os.path.join(book, "threads.json"), "w"))
        json.dump({"intertext": [{"from": "Tb 1:1", "to": "Gen 1:1", "kind": "echo",
                                  "unit": 1, "note": "", "source": "echo"}],
                   "typescenes": [{"id": "new-scene", "ref": "Tb 1:2", "unit": 1,
                                   "note": "", "source": "meta", "label": "New"},
                                  {"id": "census", "ref": "Tb 2:1", "unit": 2,
                                   "note": "", "source": "meta"}]},
                  open(os.path.join(book, "canon.json"), "w"))
        it, ts, warns = canon_collect.collect(root=root, canon_dir=cdir)
        srcs = {e["source"] for e in it["edges"]}
        assert "hand" in srcs and "echo" in srcs, srcs
        assert any(e["from"] == "Tb 1:1" and e["book"] == "testbook" for e in it["edges"])
        ids = {s["id"]: s for s in ts["typescenes"]}
        assert "new-scene" in ids and ids["new-scene"]["label"] == "New"
        assert any("new-scene" in w for w in warns), warns
        census = [i for i in ids["census"]["instances"] if i["book"] == "testbook"]
        assert len(census) == 1 and len(ids["census"]["instances"]) == 4
        # running twice doesn't duplicate book rows
        it2, ts2, _ = canon_collect.collect(root=root, canon_dir=cdir)
        assert len(it2["edges"]) == len(it["edges"])
    finally:
        shutil.rmtree(root, ignore_errors=True)
