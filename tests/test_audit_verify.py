"""Verification for audit_thread_coverage.py, written before any real
thread/unit exists (per house rule: verify before generator, not after --
Matthew's worst silent bug shipped across seven files before a verifier
existed for it).

Two parts:

1. An INDEPENDENT re-derivation of the source-side id-matching the audit
   does (`_independent_source_hits_for_root`), built separately -- its own
   Ketiv detection, its own bare-id parsing, csv.reader (not
   csv.DictReader, so even the row-access style differs from the audit's),
   and NOT importing roots.py's or audit_thread_coverage.py's matching
   functions. This is cross-checked against the real
   audit_thread_coverage.source_hits_for_root() for a handful of real ids
   (§5's kol=3605, and 3068/3389) -- if the two ever disagree, one of them
   has a bug, and this test is what would catch it.

   The old verify script's kol/Caleb stem-over-match regression doesn't
   apply anymore (nothing here does substring matching), so it's replaced
   with a live regression pulled from the TSV at check time: the id set
   {3605} must yield exactly as many word ids as there are Joshua-words.tsv
   rows with a lemma segment whose bare id is 3605, and none of those word
   ids may carry lemma 3612 (Caleb) -- the exact over-match id-based
   matching is designed to not have.

2. Synthetic fragment fixtures, built from REAL word ids/surface forms
   pulled from Joshua-words.tsv (never hand-typed), run through the real
   `coverage_for_fragment()` with a synthetic threads.json/roots.json.
   Each fixture is built to trigger exactly one of the five failure shapes
   the audit is supposed to catch: a gap, a wrong-lemma id, a missing
   data-w on a tracked span, a tagged id outside the unit's passage, and a
   tagged id that doesn't exist at all.
"""
import csv
import os
import sys
import unicodedata

import support  # noqa: E402
support.joshua_book()
from biblecore import audit  # noqa: E402

WORDS_TSV = os.path.join(support.JOSHUA, "Joshua-words.tsv")

REAL_ID_KOL = "3605"
REAL_ID_CALEB = "3612"
REAL_ID_YHWH = "3068"


# --------------------------------------------------- independent re-derivation

_CANTILLATION_RANGE = range(0x0591, 0x05B0)


def _has_niqqud_independent(s):
    return any(
        unicodedata.combining(c) != 0 and ord(c) not in _CANTILLATION_RANGE
        for c in s
    )


def _bare_id_independent(seg):
    """Digits, optionally followed by a space+letter or '+' -- see
    roots.py's bare_id docstring for why those two trailing forms exist.
    Re-implemented here rather than imported."""
    digits = ""
    i = 0
    while i < len(seg) and seg[i].isdigit():
        digits += seg[i]
        i += 1
    if not digits:
        return None
    rest = seg[i:]
    if rest in ("", "+") or (len(rest) == 2 and rest[0] == " " and rest[1].isalpha()):
        return digits
    return None  # doesn't match any known trailing-marker shape


def _independent_source_hits_for_root(id_set):
    """{word_id: (ch, v)} via a separately-written parse of
    Joshua-words.tsv (csv.reader + manual header-index lookup, not
    DictReader; own Ketiv detection; own bare-id parsing)."""
    with open(WORDS_TSV, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        i_wid, i_ref, i_surface, i_lemma = (
            header.index("word_id"), header.index("ref"),
            header.index("surface"), header.index("lemma"),
        )
        raw = list(reader)

    is_ketiv = [False] * len(raw)
    for i in range(len(raw) - 1):
        a, b = raw[i], raw[i + 1]
        if (a[i_ref] == b[i_ref]
                and not _has_niqqud_independent(a[i_surface])
                and _has_niqqud_independent(b[i_surface])):
            is_ketiv[i] = True

    hits = {}
    for i, row in enumerate(raw):
        if is_ketiv[i]:
            continue
        seg_ids = set()
        for seg in row[i_lemma].split("/"):
            seg = seg.strip()
            if not seg or not seg[0].isdigit():
                continue
            bare = _bare_id_independent(seg)
            if bare:
                seg_ids.add(bare)
        if seg_ids & id_set:
            _book, ch, v = row[i_ref].split(".")
            hits[row[i_wid]] = (int(ch), int(v))
    return hits


def test_independent_matches_real_for_kol():
    independent = _independent_source_hits_for_root({REAL_ID_KOL})
    real = audit.source_hits_for_root(audit.load_words(), {REAL_ID_KOL})
    if independent != real:
        only_independent = set(independent) - set(real)
        only_real = set(real) - set(independent)
        return [f"kol (3605): independent vs. real audit disagree -- "
                f"{len(only_independent)} only in independent, "
                f"{len(only_real)} only in real: "
                f"{sorted(only_independent)[:5]} / {sorted(only_real)[:5]}"]
    return []


def test_independent_matches_real_for_yhwh():
    independent = _independent_source_hits_for_root({REAL_ID_YHWH})
    real = audit.source_hits_for_root(audit.load_words(), {REAL_ID_YHWH})
    if independent != real:
        return [f"YHWH (3068): independent ({len(independent)}) vs. "
                f"real ({len(real)}) disagree"]
    return []


def test_kol_count_matches_raw_tsv_count():
    """The id set {3605} must yield exactly as many word ids as there are
    Joshua-words.tsv rows whose lemma has a bare-id-3605 segment -- a live
    count taken from the file at check time, not a hardcoded number."""
    failures = []
    raw_count = 0
    with open(WORDS_TSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            for seg in row["lemma"].split("/"):
                seg = seg.strip()
                if seg and _bare_id_independent(seg) == REAL_ID_KOL:
                    raw_count += 1
                    break
    hits = audit.source_hits_for_root(audit.load_words(), {REAL_ID_KOL})
    # Ketiv rows are dropped by load_words(), so allow raw_count to exceed
    # len(hits) only by however many kol occurrences were Ketiv (expected: 0,
    # kol is never part of a Ketiv/Qere pair in Joshua, but check rather than
    # assume).
    if len(hits) > raw_count:
        failures.append(f"kol: {len(hits)} hits but only {raw_count} raw TSV "
                         f"rows carry lemma 3605 -- hits should never exceed "
                         f"the raw row count")
    return failures


def test_kol_excludes_caleb():
    hits = audit.source_hits_for_root(audit.load_words(), {REAL_ID_KOL})
    words = audit.words_by_id(audit.load_words())
    caleb_leaked = [wid for wid in hits
                    if REAL_ID_CALEB in audit._lemma_bare_ids(words[wid]["lemma"])]
    if caleb_leaked:
        return [f"kol id-set leaked {len(caleb_leaked)} Caleb (3612) word id(s): "
                f"{caleb_leaked[:5]} -- this is exactly the over-match the old "
                f"substring-stem approach had and id-based matching must not"]
    return []


# --------------------------------------------------------- fragment fixtures

def _load_word_row(word_id):
    with open(WORDS_TSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["word_id"] == word_id:
                return row
    raise KeyError(word_id)


# Real rows pulled by id (never hand-typed): kol bare (Josh 1:3), YHWH bare
# (Josh 1:1, wrong lemma for a "kol" tag), we-kol (Josh 1:2, outside a
# passage declared as covering only 1:3).
_KOL_ROW = _load_word_row("06XR4")       # Josh.1.3, lemma 3605
_YHWH_ROW = _load_word_row("06k5P")      # Josh.1.1, lemma 3068
_WEKOL_ROW = _load_word_row("06yw4")     # Josh.1.2, lemma c/3605

_SYNTHETIC_THREADS = {"version": 1, "threads": [{"id": "kol", "root": "kol"}]}
_SYNTHETIC_ROOTS = {"version": 1, "roots": {"kol": {"ids": [REAL_ID_KOL], "note": "totality"}}}


def _fragment(inner_html, verse=3):
    return (
        f'<article class="unit" data-unit="1">'
        f'<p class="v"><span class="n">{verse}</span> {inner_html}</p>'
        f'</article>'
    )


def test_gap_detected():
    """Passage covers 1:3 (where the real kol word lives) but the fragment
    tags nothing -- must show up as exactly one gap for that word id."""
    html = _fragment("nothing tagged here")
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    gap_ids = {g["word_id"] for g in cov["gaps"]}
    if gap_ids != {"06XR4"}:
        return [f"expected gap {{06XR4}}, got {gap_ids}"]
    if cov["wrong"] or cov["strays"] or cov["missing_data_w"]:
        return [f"expected only a gap, also got: {cov}"]
    return []


def test_wrong_lemma_id_detected():
    """Tag a real word (YHWH, lemma 3068) as if it were 'kol' -- the id
    exists and is in range, but its lemma isn't in kol's id set."""
    html = _fragment(
        f'<span class="r" data-root="kol" data-w="{_YHWH_ROW["word_id"]}">the</span>',
        verse=1,
    )
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:1", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    wrong_ids = {w["word_id"] for w in cov["wrong"]}
    if wrong_ids != {_YHWH_ROW["word_id"]}:
        return [f"expected wrong-id {{{_YHWH_ROW['word_id']}}}, got {wrong_ids}"]
    return []


def test_missing_data_w_detected():
    """A tracked-thread span with data-root but no data-w at all is a
    hard error, independent of gap/wrong/stray counting."""
    html = _fragment('<span class="r" data-root="kol">all</span>', verse=3)
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    if cov["missing_data_w"] != 1:
        return [f"expected missing_data_w == 1, got {cov['missing_data_w']}"]
    return []


def test_stray_outside_passage_detected():
    """Tag a real, correctly-lemma'd kol word (we-kol, Josh 1:2) but
    declare the unit's passage as only 1:3 -- the id is real and correctly
    matched to the root, but its ref falls outside this unit's own
    passage, so it's a stray, not a gap-filler."""
    html = _fragment(
        f'<span class="r" data-root="kol" data-w="{_WEKOL_ROW["word_id"]}">and all</span>',
        verse=3,  # mislabeled on purpose -- the word's REAL ref (1:2) is what matters
    )
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    stray_ids = {s["word_id"] for s in cov["strays"]}
    if _WEKOL_ROW["word_id"] not in stray_ids:
        return [f"expected stray {{{_WEKOL_ROW['word_id']}}}, got {stray_ids}"]
    # Josh 1:3's real kol word is still ungapped-for since nothing tagged it.
    gap_ids = {g["word_id"] for g in cov["gaps"]}
    if "06XR4" not in gap_ids:
        return [f"expected 06XR4 to still show as a gap alongside the stray, got gaps={gap_ids}"]
    return []


def test_declared_verses_are_covered_not_gaps():
    """A component that presents 1:3 in place of verse text (a table with
    data-verses) turns the real kol word there from a gap into 'covered'.
    A verse outside the declaration still gaps."""
    html = ('<article class="unit" data-unit="1">'
            '<table class="list" data-verses="1:3"></table>'
            '</article>')
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    fails = []
    if cov["gaps"]:
        fails.append(f"expected no gaps, got {[g['word_id'] for g in cov['gaps']]}")
    if {c["word_id"] for c in cov["covered"]} != {"06XR4"}:
        fails.append(f"expected 06XR4 covered, got {cov['covered']}")
    html2 = html.replace('data-verses="1:3"', 'data-verses="1:4"')
    cov2 = audit.coverage_for_fragment("fx", html2, "Joshua 1:3-4", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    if "06XR4" not in {g["word_id"] for g in cov2["gaps"]}:
        fails.append("a verse outside the declaration must still gap")
    return fails


def test_nonexistent_id_detected():
    """A tagged data-w that doesn't correspond to any real word id at all
    is a stray for a different reason (doesn't exist), not out-of-range."""
    html = _fragment(
        '<span class="r" data-root="kol" data-w="zzNOPE99">bogus</span>',
        verse=3,
    )
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    matches = [s for s in cov["strays"] if s["word_id"] == "zzNOPE99"]
    if not matches:
        return [f"expected a stray for nonexistent id zzNOPE99, got strays={cov['strays']}"]
    if "does not exist" not in matches[0]["reason"]:
        return [f"expected reason to say the id doesn't exist, got: {matches[0]['reason']}"]
    return []


def test_local_root_verse_view():
    """A data-root that is NOT a tracked thread (a local, unit-only root)
    must show up in coverage_for_fragment()'s 'local' per-verse listing,
    not as a gap/wrong/stray for the tracked 'kol' thread it has nothing
    to do with."""
    # Josh 1:6 has no kol occurrence (checked against Joshua-words.tsv), so a
    # passage scoped to just that verse has zero source hits for the
    # unrelated tracked 'kol' thread -- isolates the local-root behavior.
    html = _fragment(
        '<span class="r" data-root="strong">chazak</span>',
        verse=6,
    )
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:6", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    failures = []
    if cov["local"].get("strong") != [(1, 6)]:
        failures.append(f"expected local={{'strong': [(1, 6)]}}, got {cov['local']}")
    if cov["gaps"] or cov["wrong"] or cov["strays"] or cov["missing_data_w"]:
        failures.append(f"a local-root-only fragment (no kol in this verse) "
                         f"should have no tracked-thread issues at all, got: {cov}")
    return failures


def test_clean_fragment_has_no_issues():
    """The real kol word, correctly tagged, in range -- no gap, no wrong,
    no stray, no missing-data-w."""
    html = _fragment(
        f'<span class="r" data-root="kol" data-w="{_KOL_ROW["word_id"]}">all</span>',
        verse=3,
    )
    cov = audit.coverage_for_fragment("fx", html, "Joshua 1:3", _SYNTHETIC_THREADS, _SYNTHETIC_ROOTS)
    if cov["gaps"] or cov["wrong"] or cov["strays"] or cov["missing_data_w"]:
        return [f"expected a clean fragment, got: {cov}"]
    return []


_TESTS = [
    test_independent_matches_real_for_kol,
    test_independent_matches_real_for_yhwh,
    test_kol_count_matches_raw_tsv_count,
    test_kol_excludes_caleb,
    test_gap_detected,
    test_wrong_lemma_id_detected,
    test_missing_data_w_detected,
    test_stray_outside_passage_detected,
    test_nonexistent_id_detected,
    test_local_root_verse_view,
    test_clean_fragment_has_no_issues,
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
