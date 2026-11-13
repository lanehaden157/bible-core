"""unit-pack, checks, promote.complete and the audit opener warning, on a
temp copy of Numbers (skipped when it isn't checked out beside bible-core)."""
import json

import support
from biblecore import audit, checks, promote, unit_pack
from biblecore.book import book


def setup():
    if support.have_numbers():
        support.numbers_book()


def teardown():
    support.joshua_book()


def test_pack_has_the_sections_and_no_script():
    if not support.have_numbers():
        return
    md, st = unit_pack.build_pack(book(), 1)
    for h in ("## Map entry", "## Versification", "## Rulings that apply",
              "## Tracked threads in this unit", "## Lemma table", "## Leads",
              "## Already cited from", "## Known source gaps"):
        assert h in md, h
    assert not any("֐" <= c <= "׿" for c in md), "native Hebrew in the pack"
    assert st["lemmas"] > 10 and st["threads"] > 3 and st["bytes"] < 40 * 1024


def test_pack_computes_first_occurrence():
    if not support.have_numbers():
        return
    md, _ = unit_pack.build_pack(book(), 1)
    row = next(l for l in md.splitlines() if l.startswith("| `account`"))
    assert "1:3 (unit 1)" in row and "yes" in row


def test_skeleton_ties_chat_transliteration_to_forms():
    assert unit_pack._skeleton("kofer") == unit_pack._skeleton("kopher")
    assert unit_pack._skeleton("ḥamishshah") == unit_pack._skeleton("chamisha")


def test_checks_resolve_transliteration_and_flag_the_rest():
    if not support.have_numbers():
        return
    from biblecore import leads
    bible = leads.load_bible()
    ok = checks.run_check(bible, {"ref": "Exod 16:16 / Exod 38:26", "claim": "c",
                                  "expect": ["gulgolet", "!kofer"]})
    assert ok["status"] == "confirmed" and ok["held"][0][2] == ["1538"], ok
    wrong = checks.run_check(bible, {"ref": "Exod 30:12", "claim": "c", "expect": ["gulgolet"]})
    assert wrong["status"] == "not found"
    assert checks.run_check(bible, {"ref": "Foo 1:1", "claim": "c", "expect": "x"})["status"] == "unresolved"
    assert checks.run_check(bible, {"ref": "Exod 99:1", "claim": "c", "expect": "x"})["status"] == "unresolved"


def test_promote_complete_fills_opens_refs_and_reach():
    if not support.have_numbers():
        return
    item = {"entry": {"id": "skull", "ids": ["1538"], "gloss": "skull, a head counted",
                      "opens": {"note": "per skull"}, "payoffs": [{"unit": 3, "note": "again"}]}}
    out, notes = promote.complete(item, this_unit=1)
    e = out["entry"]
    assert e["opens"]["unit"] == 1 and e["opens"]["ref"] == "1:2" and e["opens"]["note"] == "per skull"
    assert e["payoffs"][0]["unit"] == 3 and e["payoffs"][0]["ref"].startswith("3:")
    assert out["reach"].startswith("12 occurrences") or "occurrences" in out["reach"]
    assert 1 not in out["retrofit"]
    # a wrong opener is corrected and reported
    bad = {"entry": {**item["entry"], "opens": {"unit": 3, "ref": "3:47", "note": "n"}}}
    out2, notes2 = promote.complete(bad, this_unit=1)
    assert out2["entry"]["opens"]["unit"] == 1 and notes2


def test_audit_warns_on_a_late_opener():
    if not support.have_numbers():
        return
    b = book()
    threads = json.load(open(b.data("threads.json"), encoding="utf-8"))
    roots = json.load(open(b.data("roots.json"), encoding="utf-8"))
    units = json.load(open(b.data("units.json"), encoding="utf-8"))
    t = threads["threads"][0]
    t["opens"] = {"unit": 99, "ref": "99:1", "note": "late"}
    ws = audit.opener_warnings(threads, roots, units, audit.load_words())
    assert any(w.startswith(t["id"] + ":") for w in ws), ws
