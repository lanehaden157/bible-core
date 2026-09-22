"""Tests for canon_leads.py against the real Hebrew Bible (morphhb).

Known positives are links the intertext work on units 1-2 actually uses,
so a regression here means the leads sheet stopped surfacing something a
reader already relied on.
"""
import os
import re
import sys
import tempfile

import support  # noqa: E402
support.joshua_book()
from biblecore import leads as cl  # noqa: E402

fail = []


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


BIBLE = cl.load_bible()
FREQ = cl.verse_freq(BIBLE)


def _unit(passage):
    uv = cl.passage_verses(BIBLE, passage)
    return cl.rare_leads(BIBLE, FREQ, uv), cl.phrase_leads(BIBLE, FREQ, uv)


def _rare_refs(rare, lid):
    lead = next((r for r in rare if r["id"] == lid), None)
    return {ref for ref, _ in lead["hits"]} if lead else set()


def _phrase_refs(phrases, ids):
    """Torah refs of the phrase lead containing every id in `ids`."""
    for p in phrases:
        if set(ids) <= {w[0] for w in p["words"]}:
            return {ref for ref, _ in p["hits"]}
    return set()


def test_bare_ids():
    _check("prefix and letter suffix dropped", cl.bare_ids("c/3722 b") == ["3722"], cl.bare_ids("c/3722 b"))
    _check("'+' dropped", cl.bare_ids("1007+") == ["1007"], cl.bare_ids("1007+"))
    _check("pure prefix yields nothing", cl.bare_ids("d") == [], cl.bare_ids("d"))


def test_passage_scope():
    uv = cl.passage_verses(BIBLE, "Joshua 2:1–24")
    _check("Joshua 2 has 24 verses", len(uv) == 24, len(uv))
    uv = cl.passage_verses(BIBLE, "Joshua 3:1–4:24")
    _check("a two-chapter passage spans both chapters", len(uv) == 17 + 24, len(uv))


def test_unit1_sole_of_the_foot():
    _, phrases = _unit("Joshua 1:1–18")
    refs = _phrase_refs(phrases, ["3709", "7272"])
    for want in ("Gen.8.9", "Deut.11.24", "Deut.28.65"):
        _check(f"kap regel lead reaches {want}", want in refs, sorted(refs))


def test_unit1_merges_overlapping_pairs():
    _, phrases = _unit("Joshua 1:1–18")
    tribal = [p for p in phrases if "1425" in {w[0] for w in p["words"]}]
    _check("Reubenite/Gadite/half-tribe is one lead, not several", len(tribal) == 1,
           [[w[0] for w in p["words"]] for p in tribal])


def test_unit2_rare_words():
    rare, _ = _unit("Joshua 2:1–24")
    for lid, want in (("367", "Exod.15.16"), ("367", "Exod.23.27"), ("4127", "Exod.15.15"),
                      ("4549", "Deut.1.28"), ("7851", "Num.25.1")):
        _check(f"rare H{lid} reaches {want}", want in _rare_refs(rare, lid), sorted(_rare_refs(rare, lid)))


def test_unit2_sodom_phrase():
    _, phrases = _unit("Joshua 2:1–24")
    _check("'before they lay down' reaches Gen 19:4",
           "Gen.19.4" in _phrase_refs(phrases, ["2962", "7901"]), None)


def test_common_words_excluded():
    rare, _ = _unit("Joshua 2:1–24")
    ids = {r["id"] for r in rare}
    for lid in ("5414", "935", "7971"):   # give, enter, send
        _check(f"common H{lid} is not a rare lead", lid not in ids, None)
    _check("every rare lead is at or under the cutoff",
           all(r["freq"] <= cl.RARE_DEFAULT for r in rare), [(r["id"], r["freq"]) for r in rare])


def test_output_has_no_native_hebrew_and_stays_short():
    with tempfile.TemporaryDirectory() as d:
        path = cl.build(2, bible=BIBLE, freq=FREQ, out_dir=d)
        md = open(path, encoding="utf-8").read()
    _check("no Hebrew script in the leads sheet", not re.search(r"[֐-׿]", md),
           re.findall(r"[֐-׿]+", md)[:5])
    leads = md.count("\n- **")
    _check("unit 2 stays a short reading list (<= 30 leads)", leads <= 30, leads)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        before = len(fail)
        t()
        print(("  ok  " if len(fail) == before else "FAIL  ") + t.__name__)
    if fail:
        print(f"\nFAIL: {len(fail)} problem(s)")
        for f in fail:
            print(" -", f)
        sys.exit(1)
    print(f"\nPASS: {len(tests)} checks")


if __name__ == "__main__":
    main()
