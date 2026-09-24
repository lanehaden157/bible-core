"""units_map: unit rows + groupings from the literary unit map's Overview
table (the layout Numbers' map uses), and tools/new_book.py's lexicon pin."""
import os
import sys

import support
from biblecore import units_map as um

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import new_book  # noqa: E402

MAP = """# Test — Literary Unit Map

Ground rules prose, with a | stray pipe | that isn't a unit row.

## Overview

| # | Passage | Working title |
|---|---|---|
| | **PART ONE — The generation of the exodus (1:1–2:10)** | |
| | *I. At Sinai: ordering the camp (1:1–1:54)* | |
| 01 | 1:1–54 | The first accounting |
| | *II. Kadesh: the refusal (2:1–2:10)* | |
| 02 | 2:1–5 [Heb 2:1–6] | Second |
| | **PART TWO — The generation of the land (3:1–3:9)** | |
| | *III. On the plains of Moab (3:1–3:9)* | |
| 03 | 3:1–9 | Third |

## Unit entries

| 04 | 9:9 | not part of the overview |
"""

EMPTY = {"book": "Test", "unit_count": 0, "groupings": [], "units": []}


def test_rows_and_groupings_from_overview():
    uj, report = um.plan(MAP, ["part", "movement"], "Test", EMPTY)
    assert uj is not None, report
    rows = {u["n"]: u for u in uj["units"]}
    assert sorted(rows) == [1, 2, 3], sorted(rows)   # table ends before unit 4
    assert rows[2] == {"n": 2, "slug": "unit-02", "passage": "Test 2:1–5",
                       "title": "Second", "movement": 2, "part": 1,
                       "built": False}, rows[2]
    assert rows[3]["part"] == 2 and rows[3]["movement"] == 3, rows[3]
    assert uj["unit_count"] == 3
    got = [(g["kind"], g["n"], g["name"], g["label"], g["span"], g["units"])
           for g in uj["groupings"]]
    assert got == [
        ("movement", 1, "at-sinai", "At Sinai: ordering the camp", "1:1–1:54", [1]),
        ("movement", 2, "kadesh", "Kadesh: the refusal", "2:1–2:10", [2]),
        ("movement", 3, "plains-of-moab", "On the plains of Moab", "3:1–3:9", [3]),
        ("part", 1, "generation-of-the-exodus", "The generation of the exodus",
         "1:1–2:10", [1, 2]),
        ("part", 2, "generation-of-the-land", "The generation of the land",
         "3:1–3:9", [3]),
    ], got
    assert any("unit 2" in r and "Hebrew 2:1–6" in r for r in report), report


def test_existing_rows_and_groupings_are_kept():
    have = {"book": "Test", "unit_count": 3,
            "groupings": [{"kind": "movement", "n": 1, "name": "hand-named",
                           "span": "1:1–1:54", "units": [1, 2]}],
            "units": [{"n": 1, "slug": "unit-01", "passage": "Test 1:1–54",
                       "title": "The First Accounting", "built": True,
                       "roots": {"x": {}}}]}
    uj, report = um.plan(MAP, ["part", "movement"], "Test", have)
    assert uj["units"][0] == have["units"][0], uj["units"][0]
    assert uj["groupings"] == have["groupings"], uj["groupings"]
    assert any("members differ" in r for r in report), report
    assert any("kept 1 existing row" in r for r in report), report


def test_too_few_kinds_is_refused():
    uj, report = um.plan(MAP, ["movement"], "Test", EMPTY)
    assert uj is None and any("--kinds" in r for r in report), report


def test_map_without_headings_gives_units_only():
    md = "| # | Passage | Title |\n|---|---|---|\n| 1 | 1:1–5 | One |\n| 2 | 1:6–9 | Two |\n"
    uj, report = um.plan(md, [], "Test", EMPTY)
    assert [u["n"] for u in uj["units"]] == [1, 2] and uj["groupings"] == [], uj


def test_no_rows_is_reported():
    uj, report = um.plan("# nothing here\n", ["part"], "Test", EMPTY)
    assert uj is None and any("no unit rows" in r for r in report), report


def test_lexicon_pin_matches_shipped_file():
    assert new_book.sha1(new_book.LEXICON) == new_book.LEXICON_SHA1
