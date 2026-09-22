"""Regression test for roots.py, against synthetic roots.json fixtures
built from real lemma ids pulled from Joshua-words.tsv (3068 YHWH, 3389
Jerusalem, 3605 kol -- all confirmed present via hebrew.py's own OVERRIDES
table and its corpus sweep). No real thread/root content exists yet
(data/roots.json is still empty scaffolding), so every fixture here is
synthetic and self-contained.
"""
import os
import sys

import support  # noqa: E402
support.joshua_book()
from biblecore.roots import bare_id, known_lemma_ids, lemma_key, validate  # noqa: E402

# Ids confirmed to occur in Joshua-words.tsv (see hebrew.py's OVERRIDES /
# test_hebrew.py's corpus sweep).
REAL_ID_YHWH = "3068"
REAL_ID_JERUSALEM = "3389"
REAL_ID_KOL = "3605"


def test_known_lemma_ids_contains_real_ids():
    known = known_lemma_ids()
    failures = []
    for id_ in (REAL_ID_YHWH, REAL_ID_JERUSALEM, REAL_ID_KOL):
        if id_ not in known:
            failures.append(f"{id_}: expected in known_lemma_ids(), not found")
    return failures


def test_valid_document_passes():
    data = {
        "version": 1,
        "roots": {
            "divine-name": {"ids": [REAL_ID_YHWH], "note": "the tetragrammaton"},
            "kol": {"ids": [REAL_ID_KOL], "note": "totality"},
        },
    }
    errors = validate(data)
    if errors:
        return [f"expected a clean document to pass, got: {errors}"]
    return []


def test_unknown_id_fails():
    data = {
        "version": 1,
        "roots": {"bogus": {"ids": ["999999"], "note": "does not exist in the corpus"}},
    }
    errors = validate(data)
    if not any("999999" in e and "not a lemma" in e for e in errors):
        return [f"expected an unknown-id failure, got: {errors}"]
    return []


def test_bad_slug_fails():
    data = {
        "version": 1,
        "roots": {"Bad Slug!": {"ids": [REAL_ID_KOL], "note": "n"}},
    }
    errors = validate(data)
    if not any("slug must match" in e for e in errors):
        return [f"expected a bad-slug failure, got: {errors}"]
    return []


def test_lettered_id_normalizes():
    """bare_id() still strips; lemma_key() keeps the letter (review A7)."""
    failures = []
    if bare_id(f"{REAL_ID_KOL}a") != REAL_ID_KOL:
        failures.append(f"bare_id({REAL_ID_KOL}a) did not strip the trailing letter")
    if lemma_key(f"{REAL_ID_KOL}a") != f"{REAL_ID_KOL}a":
        failures.append("lemma_key() dropped the disambiguating letter")
    if lemma_key("1007+") != "1007":
        failures.append("lemma_key() kept the '+' compound marker, which is "
                        "the same lexeme and must be stripped")
    if lemma_key("310 a") != "310a":
        failures.append("lemma_key() did not normalize the TSV's spaced spelling")
    return failures


def test_lettered_id_that_does_not_exist_fails():
    """A suffixed id matches only its own lexeme, so one the corpus never
    carries would match nothing at all -- a silent zero. Loud instead.

    This reverses the old rule, which accepted any lettered spelling as
    long as the bare number occurred; that was safe only while the letter
    was being stripped before matching.
    """
    data = {
        "version": 1,
        "roots": {"kol": {"ids": [f"{REAL_ID_KOL}a"], "note": "no such lexeme"}},
    }
    errors = validate(data)
    if not any("would match nothing" in e for e in errors):
        return [f"expected a nonexistent lettered id to be rejected, got: {errors}"]
    return []


def test_real_lettered_ids_split_distinct_lexemes():
    """3885a 'lodge' and 3885b 'murmur' are different words sharing a
    Strong's number, and may therefore live in different roots."""
    failures = []
    data = {
        "version": 1,
        "roots": {
            "lodge": {"ids": ["3885a"], "note": "lun, lodge"},
            "murmur": {"ids": ["3885b"], "note": "lun, murmur"},
        },
    }
    errors = validate(data)
    if errors:
        failures.append(f"3885a and 3885b in separate roots should be legal, "
                        f"got: {errors}")

    # but a bare 3885 claims the whole number, so it collides with either
    data2 = {
        "version": 1,
        "roots": {
            "lodge": {"ids": ["3885"], "note": "all of 3885"},
            "murmur": {"ids": ["3885b"], "note": "just the murmur sense"},
        },
    }
    if not any("claimed by both" in e for e in validate(data2)):
        failures.append("a bare id must collide with a suffixed id under the "
                        "same number")
    return failures


def test_id_in_two_roots_fails():
    data = {
        "version": 1,
        "roots": {
            "root-a": {"ids": [REAL_ID_KOL], "note": "first claim"},
            "root-b": {"ids": [REAL_ID_KOL], "note": "second claim"},
        },
    }
    errors = validate(data)
    if not any("hard failure" in e for e in errors):
        return [f"expected an id-in-two-roots failure, got: {errors}"]
    return []


def test_missing_note_fails():
    data = {"version": 1, "roots": {"kol": {"ids": [REAL_ID_KOL]}}}
    errors = validate(data)
    if not any("missing required 'note'" in e for e in errors):
        return [f"expected a missing-note failure, got: {errors}"]
    return []


def test_kind_members_rejected():
    data = {
        "version": 1,
        "roots": {"kol": {"ids": [REAL_ID_KOL], "note": "n", "kind": "verb"}},
    }
    errors = validate(data)
    if not any("kind" in e and "members" in e for e in errors):
        return [f"expected a kind/members rejection, got: {errors}"]
    return []


def test_translit_gloss_rejected():
    data = {
        "version": 1,
        "roots": {"kol": {"ids": [REAL_ID_KOL], "note": "n", "translit": "kol"}},
    }
    errors = validate(data)
    if not any("id-sets only" in e for e in errors):
        return [f"expected a translit-field rejection, got: {errors}"]
    return []


def test_thread_with_missing_root_fails():
    data = {
        "version": 1,
        "roots": {"kol": {"ids": [REAL_ID_KOL], "note": "n"}},
    }
    threads_data = {
        "version": 1,
        "threads": [{"id": "give", "root": "give", "status": "open"}],
    }
    errors = validate(data, threads_data=threads_data)
    if not any("give" in e and "no matching" in e for e in errors):
        return [f"expected a missing-thread-root failure, got: {errors}"]
    return []


def test_thread_with_present_root_passes():
    data = {
        "version": 1,
        "roots": {"kol": {"ids": [REAL_ID_KOL], "note": "n"}},
    }
    threads_data = {
        "version": 1,
        "threads": [{"id": "kol", "root": "kol", "status": "open"}],
    }
    errors = validate(data, threads_data=threads_data)
    if errors:
        return [f"expected a matching thread root to pass, got: {errors}"]
    return []


_TESTS = [
    test_known_lemma_ids_contains_real_ids,
    test_valid_document_passes,
    test_unknown_id_fails,
    test_bad_slug_fails,
    test_lettered_id_normalizes,
    test_lettered_id_that_does_not_exist_fails,
    test_real_lettered_ids_split_distinct_lexemes,
    test_id_in_two_roots_fails,
    test_missing_note_fails,
    test_kind_members_rejected,
    test_translit_gloss_rejected,
    test_thread_with_missing_root_fails,
    test_thread_with_present_root_passes,
]


if __name__ == "__main__":
    all_failures = []
    for t in _TESTS:
        all_failures += [f"{t.__name__}: {f}" for f in t()]

    if all_failures:
        print(f"FAIL: {len(all_failures)} of {len(_TESTS)} checks failed\n")
        for f in all_failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print(f"PASS: {len(_TESTS)} checks")
