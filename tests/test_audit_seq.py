"""audit.source_hits_for_seq / source_hits_for_entry: phrase threads (plan
D2, "teach multi word" -- a fixed title with no single lemma, e.g. "son of
man" = huios ... [article] ... anthropos). Synthetic word rows, Hebrew-style
numeric ids (the matching itself is language-agnostic; roots.py's Hebrew
default needs no book context beyond what support.joshua_book() sets)."""
import support
support.joshua_book()
from biblecore.audit import source_hits_for_entry, source_hits_for_seq
from biblecore.roots import validate


def row(wid, lemma, ch, v):
    return {"word_id": wid, "lemma": lemma, "ch": ch, "v": v}


def test_matches_across_a_small_gap_in_order():
    # "111 ... [113, an article] ... 222" -- 111 then 222, one word between
    words = [row("w1", "111", 1, 1), row("w2", "113", 1, 1), row("w3", "222", 1, 1)]
    hits = source_hits_for_seq(words, ["111", "222"])
    if hits != {"w3": (1, 1)}:
        return [f"expected a hit at w3, got {hits}"]
    return []


def test_no_match_beyond_the_gap():
    filler = [row(f"w{i}", "999", 1, 1) for i in range(2, 8)]  # 6 words between
    words = [row("w1", "111", 1, 1), *filler, row("w9", "222", 1, 1)]
    hits = source_hits_for_seq(words, ["111", "222"], max_gap=4)
    if hits:
        return [f"expected no hit past max_gap, got {hits}"]
    return []


def test_order_matters():
    # 222 before 111 -- not the phrase "111 then 222"
    words = [row("w1", "222", 1, 1), row("w2", "111", 1, 1)]
    hits = source_hits_for_seq(words, ["111", "222"])
    if hits:
        return [f"expected no hit -- wrong order, got {hits}"]
    return []


def test_never_crosses_a_verse():
    words = [row("w1", "111", 1, 1), row("w2", "222", 1, 2)]
    hits = source_hits_for_seq(words, ["111", "222"], max_gap=4)
    if hits:
        return [f"expected no hit across a verse boundary, got {hits}"]
    return []


def test_two_occurrences_in_one_verse():
    words = [row("w1", "111", 1, 1), row("w2", "222", 1, 1),
             row("w3", "111", 1, 1), row("w4", "222", 1, 1)]
    hits = source_hits_for_seq(words, ["111", "222"])
    if set(hits) != {"w2", "w4"}:
        return [f"expected hits at w2 and w4, got {hits}"]
    return []


def test_bare_id_matches_any_letter_variant():
    words = [row("w1", "111", 1, 1), row("w2", "222a", 1, 1)]
    hits = source_hits_for_seq(words, ["111", "222"])  # bare 222 in the seq
    if hits != {"w2": (1, 1)}:
        return [f"expected a bare-id match, got {hits}"]
    return []


def test_source_hits_for_entry_dispatches_on_seq():
    words = [row("w1", "111", 1, 1), row("w2", "222", 1, 1)]
    seq_entry = {"seq": ["111", "222"], "note": "x"}
    id_entry = {"ids": ["111"], "note": "x"}
    if source_hits_for_entry(words, seq_entry) != {"w2": (1, 1)}:
        return ["seq entry didn't dispatch to source_hits_for_seq"]
    if source_hits_for_entry(words, id_entry) != {"w1": (1, 1)}:
        return ["ids entry didn't dispatch to source_hits_for_root"]
    return []


def test_alt_order_matches_the_same_title_reversed():
    # "the Law and the Prophets" (5:17) but "the prophets and the law"
    # (11:13): seq covers one order, alt the other; hits merge.
    words = [row("w1", "111", 1, 1), row("w2", "222", 1, 1),
             row("w3", "222", 1, 2), row("w4", "111", 1, 2)]
    entry = {"seq": ["111", "222"], "alt": [["222", "111"]], "note": "x"}
    hits = source_hits_for_entry(words, entry)
    if hits != {"w2": (1, 1), "w4": (1, 2)}:
        return [f"expected both orders to hit, got {hits}"]
    if source_hits_for_entry(words, {"seq": ["111", "222"], "note": "x"}) != {"w2": (1, 1)}:
        return ["without alt, only the primary order should hit"]
    return []


# ---- roots.json validation --------------------------------------------

REAL_ID_YHWH = "3068"
REAL_ID_KOL = "3605"


def test_valid_seq_root_passes():
    data = {"version": 1, "roots": {
        "son-of-man": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "note": "a fixed title"},
    }}
    errors = validate(data)
    if errors:
        return [f"expected a clean seq root to pass, got: {errors}"]
    return []


def test_seq_of_one_fails():
    data = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH], "note": "x"},
    }}
    if not validate(data):
        return ["a one-entry seq should fail -- that's just an ordinary root"]
    return []


def test_seq_and_ids_together_fails():
    data = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "ids": [REAL_ID_YHWH], "note": "x"},
    }}
    if not validate(data):
        return ["a root with both seq and ids should fail"]
    return []


def test_seq_lemmas_dont_clash_with_an_ordinary_root():
    # REAL_ID_YHWH is claimed twice: once by an ordinary root, once inside
    # a seq. That's fine -- seq is a positional constraint, not a claim.
    data = {"version": 1, "roots": {
        "divine-name": {"ids": [REAL_ID_YHWH], "note": "the tetragrammaton"},
        "some-title": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "note": "a fixed title"},
    }}
    errors = validate(data)
    if errors:
        return [f"a seq lemma shouldn't clash with an ordinary root's id: {errors}"]
    return []


def test_seq_unknown_id_fails():
    data = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, "999999"], "note": "x"},
    }}
    if not validate(data):
        return ["an unknown lemma id inside seq should fail"]
    return []


def test_seq_bad_gap_fails():
    data = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "note": "x", "gap": 0},
    }}
    if not validate(data):
        return ["gap: 0 should fail (must be a positive integer)"]
    return []


def test_valid_alt_passes():
    data = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "alt": [[REAL_ID_KOL, REAL_ID_YHWH]],
              "note": "both orders"},
    }}
    errors = validate(data)
    if errors:
        return [f"expected seq + alt to pass, got: {errors}"]
    return []


def test_alt_without_seq_fails():
    data = {"version": 1, "roots": {
        "x": {"ids": [REAL_ID_YHWH], "alt": [[REAL_ID_KOL, REAL_ID_YHWH]], "note": "x"},
    }}
    if not validate(data):
        return ["alt on an ids root should fail"]
    return []


def test_alt_of_one_or_unknown_id_fails():
    one = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "alt": [[REAL_ID_YHWH]], "note": "x"}}}
    unknown = {"version": 1, "roots": {
        "x": {"seq": [REAL_ID_YHWH, REAL_ID_KOL], "alt": [[REAL_ID_KOL, "999999"]], "note": "x"}}}
    fails = []
    if not validate(one):
        fails.append("a one-entry alt should fail")
    if not validate(unknown):
        fails.append("an unknown lemma id inside alt should fail")
    return fails
