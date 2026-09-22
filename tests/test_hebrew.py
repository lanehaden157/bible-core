"""Regression test for hebrew.py -- and its scheme's authoritative
definition. If this file and hebrew.py's docstring disagree about what a
given input should produce, THIS FILE WINS; the docstring is a summary
that can drift.

All word-level cases are real OSHB word ids pulled from Joshua-words.tsv
(surface/lemma/morph looked up here by id at test time, never hand-typed).
Each expected value was worked out independently from the word's actual
Unicode codepoints (dumped and read directly, not recalled/typed from
memory) and the rules documented in hebrew.py's module docstring -- not
copied from transliterate_word()'s own output. Two of these hand
derivations (06VdU, 06bjL) initially missed a codepoint on a first pass
and were corrected after re-reading the dumped codepoints, which is the
point of doing it this way: the mistake was caught by re-deriving, not by
trusting the generator.

Covers every row of phase-0.6-plan.md's measured-output table (06b5Q is
covered by the closely analogous 06XR4/06K9n kol cases; melek itself
doesn't recur as a bare form early enough in Joshua to pull a cleaner id,
so the no-spirantization rule is instead exercised directly by 06XSi/
06j8W/065Pr/06bjL, each of which has a bare bet/kaf/pe in the old scheme's
spirantizing position), plus: kol/YHWH/Jerusalem overrides (bare and
prefixed), a Ketiv/Qere pair, word-initial shuruq, sin/shin-dot and
begadkefat minimal pairs, heavy niqqud/cantillation stacking, dagesh-forte
doubling (including a double-forte word and the "preposition assimilation"
gemination pattern shared with the article), silent vs. vocal sheva in
every position the rules distinguish, furtive patach, and tsere-yod
alongside hiriq-yod matres.
"""
import csv
import os
import sys

import support  # noqa: E402
support.joshua_book()
from biblecore.lang.hebrew import transliterate, transliterate_word, transliterate_ref  # noqa: E402

WORDS_TSV = os.path.join(support.JOSHUA, "Joshua-words.tsv")
READING_TXT = os.path.join(support.JOSHUA, "Joshua-reading.txt")


def _load_words():
    rows = {}
    with open(WORDS_TSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows[row["word_id"]] = row
    return rows


# (word_id, expected) -- surface/lemma/morph are looked up from
# Joshua-words.tsv, not retyped here.
WORD_CASES = [
    # phase-0.6-plan.md's measured-output table, corrected:
    ("062oS", "ha-mmelakim"),   # dagesh-forte doubling (article gemination, already its own OSHB morpheme) + sheva-under-doubling vocal
    ("06K9n", "ka-mmishpaṭ"),   # same gemination pattern via an inseparable preposition, not just the article; sheva now silent under shin, shin -> sh
    ("06aPd", "yehoshuaʿ̲"),    # furtive patach on final ayin, shin -> sh
    ("06LeN", "netatti-w"),     # hiriq-yod -> i (no more "iy"); the 2nd tav is genuinely dagesh-forte (doubled), preceded by a vowel
    ("06k5P", "YHWH"),          # lemma-keyed override, bare "YHWH" not "Yahweh"
    # kol override: bare, vav-prefixed, kaf-prefixed
    ("06XR4", "kol"),
    ("06yw4", "we-kol"),
    ("06zQ2", "ke-kol"),
    # YHWH override, two different cantillation patterns on the same lemma
    ("06LN3", "YHWH"),
    # Jerusalem override: bare and bet-prefixed
    ("06YgF", "Yerushalayim"),
    ("06sZv", "bi-Yerushalayim"),
    # word-initial shuruq ("and", u- not w-) + sin-dot (ś, not s -- distinct from samekh)
    ("06cpb", "u-śemoʾwl"),
    # heavy niqqud/cantillation stacking; also a real consecutive-shva pair
    # (shin's sheva silent, pe's vocal) and a lene (non-doubling) dagesh on pe
    ("06HYt", "le-mishpeḥote-hem"),
    # dagesh-forte doubling on the 2nd tav of a Hitpael (preceded by a vowel)
    ("06mrF", "we-hitḥattantem"),
    # shin-dot (default, no dot needed -> sh) proper nouns
    ("06vuQ", "mosheh"),
    ("06EVS", "mosheh"),
    # no spirantization: bet with no dagesh stays "b" (not "v"); tsere-yod -> e
    ("06XSi", "beta-h"),
    ("06j8W", "bete-ke"),
    # no spirantization: pe with no dagesh stays "p" (not "f")
    ("065Pr", "le-paney-ka"),
    # sin-dot mid-word (ś), lene dagesh at word start, vocal sheva word-initial
    ("06Qsh", "taśkil"),
    # tsere-yod mater, silent default-case sheva
    ("06zpy", "shoṭre"),
    # dagesh-forte doubling on pe, immediately followed by word-final silent sheva
    ("063k3", "ṭapp-kem"),
    # two dagesh-forte letters in one morpheme (article gemination on shin,
    # plus the root's own geminate tet) -- an intentionally unusual case
    ("062tS", "ha-shshiṭṭim"),
    # consecutive-shva pair (tet silent, mem vocal), no spirantization
    ("06Hki", "wa-tiṭmene-m"),
    # lene dagesh word-initial (bet not doubled), tsere-yod x2
    ("06VdU", "be-ʿ̲ene-kem"),
    # article/preposition gemination pattern again, doubling a non-begadkefat
    # letter (shin) that isn't the article's own morpheme
    ("06bjL", "ba-shshoparot"),
    # no spirantization on bet x2, silent default-case shevas
    ("06VY5", "lebabe-nu"),
    # plain object marker, unaffected by any of the rework
    ("06thY", "ʾet"),
    # bare consonant with no vowel at word end, no furtive (patach belongs
    # to the preceding letter, not this one) -- unaffected by the rework
    ("06Dzw", "raʿ̲"),
    # Ketiv/Qere pair, Josh 2:13 -- Ketiv is fully unpointed (no niqqud at
    # all), so nothing in this rework touches it; Qere exercises a
    # holam-vav mater absorbed into a *yod*, not just a plain consonant
    ("06x72", "ʾḥwt-y"),
    ("06FYV", "ʾaḥyota-y"),
    # definite article + tsadi (digraph "ts", per §A1, not "ṣ")
    ("065SS", "ha-ʾarets"),
    # tet, unaffected by the rework
    ("06Nvk", "ʾaḥare"),  # also: tsere-yod mater on a non-construct word
]


def test_word_cases():
    rows = _load_words()
    failures = []
    for wid, expected in WORD_CASES:
        if wid not in rows:
            failures.append(f"{wid}: not found in Joshua-words.tsv")
            continue
        row = rows[wid]
        got = transliterate_word(row["surface"], row["lemma"], row["morph"])
        if got != expected:
            failures.append(
                f"{wid} ({row['ref']}, {row['surface']!r}): "
                f"expected {expected!r}, got {got!r}"
            )
    return failures


def test_ref_matches_word_cases():
    """transliterate_ref() must agree with transliterate_word() called on
    each of that verse's rows individually, space-joined -- proves the
    verse-level API doesn't diverge from the word-level one it's built on."""
    rows = _load_words()
    by_ref = {}
    for row in rows.values():
        by_ref.setdefault(row["ref"], []).append(row)

    failures = []
    for tsv_ref in ("Josh.1.1", "Josh.6.20", "Josh.24.15"):
        matching = [r for r in by_ref.get(tsv_ref, [])]
        if not matching:
            failures.append(f"{tsv_ref}: no rows found")
            continue
        book, chap, verse = tsv_ref.split(".")
        spoken_ref = f"{book} {chap}:{verse}"
        expected = " ".join(
            transliterate_word(r["surface"], r["lemma"], r["morph"]) for r in matching
        )
        got = transliterate_ref(spoken_ref)
        if got != expected:
            failures.append(f"{spoken_ref}: expected {expected!r}, got {got!r}")
    return failures


def test_phrase_keeps_spaces():
    """A full verse must not lose its spaces going through bare
    transliterate() -- deterministic, no overrides (that needs a lemma).
    Josh 1:1, pulled verbatim from Joshua-reading.txt -- 13 space-separated
    words, including two maqqef-joined pairs and two YHWH occurrences
    (rendered deterministically here, "yehwah", since bare transliterate()
    has no lemma to key an override on)."""
    failures = []
    with open(READING_TXT, encoding="utf-8") as f:
        line = f.readline().rstrip("\n")
    ref, verse = line.split("\t", 1)
    if ref != "Josh 1:1":
        failures.append(f"expected Joshua-reading.txt line 1 to be Josh 1:1, got {ref}")
        return failures

    expected_word_count = verse.count(" ") + 1
    got = transliterate(verse)
    got_word_count = got.count(" ") + 1
    if got_word_count != expected_word_count:
        failures.append(
            f"phrase lost/gained spaces: {expected_word_count} words in, "
            f"{got_word_count} words out ({got!r})"
        )

    expected = (
        "wa-yehi ʾaḥare mot mosheh ʿ̲ebed yehwah wa-yyoʾmer yehwah "
        "ʾel-yehoshuaʿ̲ bin-nun mesharet mosheh le-ʾmor׃"
    )
    if got != expected:
        failures.append(f"Josh 1:1 mismatch:\n  expected {expected!r}\n  got      {got!r}")
    return failures


def test_maqqef_pair():
    """A maqqef-joined pair, pulled from the same Josh 1:1 line, in
    isolation -- 'unto Joshua'. Also exercises furtive patach on the
    maqqef-joined word's own final ayin."""
    failures = []
    substring = "אֶל־יְהוֹשֻׁ֣עַ"
    expected = "ʾel-yehoshuaʿ̲"
    got = transliterate(substring)
    if got != expected:
        failures.append(f"maqqef pair: expected {expected!r}, got {got!r}")
    return failures


def test_full_corpus_sweep():
    """Every one of Joshua's 10,083 words must transliterate through
    transliterate_word() without raising, produce non-empty output, and
    use only the locked scheme's alphabet. This also validates
    _align_lemma_to_surface()'s morph/lemma-segment alignment over every
    row, not just the ~30 hand-picked cases above -- a misalignment
    anywhere raises ValueError, which this test would catch."""
    import re

    allowed = re.compile(r"^[A-Za-zʾʿ̲ḥṭś\-]*$")
    rows = _load_words()
    failures = []
    for wid, row in rows.items():
        try:
            got = transliterate_word(row["surface"], row["lemma"], row["morph"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{wid} ({row['ref']}): raised {exc!r}")
            continue
        if not got:
            failures.append(f"{wid} ({row['ref']}): empty output")
        elif not allowed.match(got):
            failures.append(f"{wid} ({row['ref']}): {got!r} has unexpected characters")
    return failures


if __name__ == "__main__":
    all_failures = []
    all_failures += test_word_cases()
    all_failures += test_ref_matches_word_cases()
    all_failures += test_phrase_keeps_spaces()
    all_failures += test_maqqef_pair()
    sweep_failures = test_full_corpus_sweep()
    all_failures += sweep_failures

    total = len(WORD_CASES) + 3 + 1 + 10083
    if all_failures:
        print(f"FAIL: {len(all_failures)} of {total} checks failed\n")
        for f in all_failures[:100]:
            print(f"  - {f}")
        if len(all_failures) > 100:
            print(f"  ... and {len(all_failures) - 100} more")
        raise SystemExit(1)
    print(
        f"PASS: {total} checks ({len(WORD_CASES)} word cases, "
        f"3 ref-vs-word cases, 1 phrase case, 1 maqqef case, "
        f"10083 full-corpus sweep)"
    )
