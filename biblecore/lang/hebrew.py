"""Deterministic Hebrew -> Latin transliteration. Hebrew sibling to
pipeline/greek.py (Projects/Matthew) -- same role: one small pure function,
unit-testable via its own __main__ block.

Scheme (a summary -- tests/test_hebrew.py's expected values are the
authoritative definition; if this docstring and that file disagree, the
test file wins). Locked by joshua_study_style_reference.md §5 and the
phase-0.6-plan.md §A decisions:

- Alphabet: ʾ b g d h w z ḥ ṭ y k l m n s ʿ p ts q r sh ś t.
  No vowel length. No spirantization -- bet/kaf/pe are ALWAYS b/k/p, never
  v/kh/f; gimel/dalet/tav are always g/d/t (unchanged from before). Tsadi
  is the digraph "ts", not a diacritic (§A1: matches how shin was already
  handled as a digraph rather than as š). Shin (no sin dot) is the
  digraph "sh"; sin (sin dot) is "ś", distinct from samekh's plain "s".
  Ayin always carries a trailing combining low line (ʿ̲) so it survives
  copy-paste distinguishably from alef (§A3) -- baked into the output
  string itself, not a wrapping <span>.
- Sheva (na/nach): ported from the Hebrew parser project's rules
  (Projects/Hebrew/pipeline/transliterate.py), which follow standard
  introductory-grammar rules (e.g. Pratico & Van Pelt):
    1. Word/morpheme-final sheva is silent.
    2. Word/morpheme-initial sheva is vocal ("e").
    3. Of two consecutive shevas, the first is silent, the second vocal.
    4. Otherwise (default -- closing a syllable after a short vowel) it's
       silent.
  Plus one the parser project deliberately skipped (§5: hammelakim, not
  hamlakim): sheva under a dagesh-forte (doubled) consonant is vocal. Where
  more than one of these could apply, this module checks them in the order
  final, initial, doubled, consecutive-pair, default -- word-final and
  word-initial are checked first because they're structural (there either
  is or isn't a following/preceding cluster in this morpheme), and in
  every case actually observed in Joshua's text the doubled-vs-initial
  question doesn't arise (a doubled consonant's own dagesh can't be
  word-initial in the sense that matters, since dagesh forte requires a
  preceding vowel -- except for non-begadkefat letters, whose dagesh is
  forte regardless of position; when a non-begadkefat morpheme-initial
  letter is both "initial" and "doubled" under this module's rules, both
  paths already agree on "vocal", so the ordering is moot there too).
- Dagesh forte doubles the consonant (rendered by repeating its Latin
  text). Distinguishing forte from lene:
    - A NON-begadkefat letter's dagesh is always forte (doubled), with two
      exemptions: a dagesh on vav that has no vowel of its own is shuruq
      (a mater, not gemination -- see below), and a dagesh on a
      word/morpheme-final he is mappiq (marks it as consonantal, not
      doubling).
    - A begadkefat letter's (bet/gimel/dalet/kaf/pe/tav) dagesh is forte
      only when it immediately follows an audible vowel (a real vowel, a
      mater-absorbed vowel, or a resolved vocal sheva) within the same
      morpheme; at morpheme-initial position or right after a silent
      sheva, it's dagesh lene (the ordinary word-initial "hardening"
      dagesh) and the consonant is not doubled. Since this module already
      never spirantizes begadkefat letters, lene vs. forte only ever
      affects whether the letter doubles, not which letter it renders as.
    - The article's (and inseparable-preposition's) gemination therefore
      falls out for free: OSHB already marks the article as its own
      "/"-delimited morpheme (e.g. "הַ/מְּלָכִים"), so the following
      morpheme's initial consonant already carries its own dagesh in the
      source text -- this module doesn't need to propagate doubling
      across the hyphen itself.
- Matres lectionis (vowel-only letters, absorbed rather than also emitted
  as a consonant): shuruq (bare vav+dagesh, no vowel of its own) -> u;
  holam male (bare vav+holam, no dagesh) -> o; hiriq-yod (a vowelless bare
  yod immediately after a hiriq) -> i (drop the yod); tsere-yod (a
  vowelless bare yod immediately after a tsere) -> e (drop the yod, new
  in this rework -- the parser project didn't need it, hiriq-yod's
  analogue). Final he after a vowel is always "h", pointed or not --
  matches convention ("torah" not "tora"); a mappiq'd final he is "h" for
  the same reason, mappiq or not doesn't change the letter.
- Furtive patach: a patach whose OWN mark sits on a word/morpheme-final
  ḥet, ayin, or mappiq'd he glides in before the guttural rather than
  after it, so the output order is vowel+consonant instead of
  consonant+vowel (yehoshuaʿ̲, not yehošuʿ̲a). Guarded, per the standard
  rule, against a preceding a-class vowel (patach/qamats), which would
  make this a genuine (non-furtive) patach instead.
- Niqqud and cantillation are both identified via unicodedata.combining()
  != 0 rather than a hand-rolled codepoint-range check (which would also
  catch maqqef/sof-pasuq/paseq, which are *not* combining marks).
  Cantillation marks and meteg are simply dropped; they carry no vowel
  quality here.
- OSHB marks morpheme boundaries inside a single <w> with a literal "/"
  (e.g. vav-conjunction + kol). Each "/"-delimited morpheme is
  transliterated independently (its own sheva na/nach, dagesh forte, and
  matres resolution -- none of it crosses a "/" boundary) and morphemes
  are rejoined with "-" (§A2: hyphenate, not join solid). Word-initial
  shuruq therefore renders "u-", not "w-".
- Maqqef (the real word-joining hyphen at the segment level, not inside a
  <w>) also renders as "-". Everything else that isn't a Hebrew letter, a
  combining mark, or "/" passes through unchanged -- spaces included, so
  a phrase keeps its word boundaries.
- Overrides are keyed on LEMMA ID now, not on consonant skeleton (§5,
  §A7) -- 3068/3069 -> bare "YHWH" (not "Yahweh"; that's a
  translation-choices.md rendering decision, not a transliteration
  output), 3389 -> "Yerushalayim" (the deterministic pass loses the word's
  second vowel: "yerushalam"), 3605 -> "kol" (the deterministic pass
  renders "kal" in most of its Joshua occurrences). Because overrides now
  need a lemma, not just a Hebrew string, they only apply through
  transliterate_word()/transliterate_ref() -- bare transliterate(text)
  has no lemma to consult and is a deterministic-only fallback, same as
  before.
"""

import csv
import os
import re
import unicodedata

_ALEF = "א"
_BET = "ב"
_GIMEL = "ג"
_DALET = "ד"
_HE = "ה"
_VAV = "ו"
_ZAYIN = "ז"
_HET = "ח"
_TET = "ט"
_YOD = "י"
_KAF = "כ"
_KAF_FINAL = "ך"
_LAMED = "ל"
_MEM = "מ"
_MEM_FINAL = "ם"
_NUN = "נ"
_NUN_FINAL = "ן"
_SAMEKH = "ס"
_AYIN_LETTER = "ע"
_PE = "פ"
_PE_FINAL = "ף"
_TSADI = "צ"
_TSADI_FINAL = "ץ"
_QOF = "ק"
_RESH = "ר"
_SHIN = "ש"
_TAV = "ת"

_AYIN_OUT = "ʿ̲"  # ayin (ʿ) + combining low line, see docstring

# Position/mark-dependent letters (shin's sin-dot; everything else is a
# flat consonant now that spirantization is gone) plus vav, which needs
# its own mater/consonant branching.
_CONSONANTS = {
    _ALEF: "ʾ",
    _BET: "b",
    _GIMEL: "g",
    _DALET: "d",
    _HE: "h",
    _VAV: "w",
    _ZAYIN: "z",
    _HET: "ḥ",
    _TET: "ṭ",
    _YOD: "y",
    _KAF: "k", _KAF_FINAL: "k",
    _LAMED: "l",
    _MEM: "m", _MEM_FINAL: "m",
    _NUN: "n", _NUN_FINAL: "n",
    _SAMEKH: "s",
    _AYIN_LETTER: _AYIN_OUT,
    _PE: "p", _PE_FINAL: "p",
    _TSADI: "ts", _TSADI_FINAL: "ts",
    _QOF: "q",
    _RESH: "r",
    _TAV: "t",
}

_HEB_LETTERS = set(_CONSONANTS) | {_SHIN, _VAV}

# Begadkefat letters -- the six whose dagesh can be lene (word-initial /
# after silent sheva, not doubled) or forte (after an audible vowel,
# doubled). No spirantization means lene vs. forte only ever changes
# whether the consonant doubles, never which letter it renders as.
_BEGADKEFAT = {_BET, _GIMEL, _DALET, _KAF, _KAF_FINAL, _PE, _PE_FINAL, _TAV}

_VOWELS = {
    "ֱ": "e",  # hataf segol
    "ֲ": "a",  # hataf patah
    "ֳ": "o",  # hataf qamats
    "ִ": "i",  # hiriq
    "ֵ": "e",  # tsere
    "ֶ": "e",  # segol
    "ַ": "a",  # patah
    "ָ": "a",  # qamats
    "ֹ": "o",  # holam
    "ֺ": "o",  # holam haser for vav
    "ֻ": "u",  # qubuts
    "ׇ": "o",  # qamats qatan
}

_SHVA = "ְ"
_DAGESH = "ּ"  # also mappiq, on he -- same codepoint, disambiguated by base letter
_SIN_DOT = "ׂ"
_SHIN_DOT = "ׁ"
_HOLAM = "ֹ"
_HOLAM_HASER = "ֺ"
_PATACH = "ַ"
_QAMATS = "ָ"
_TSERE = "ֵ"
_HIRIQ = "ִ"
_MAQQEF = "־"

# Word/morpheme-final het, ayin, or mappiq'd he take a furtive patach.
_FURTIVE_BASES = {_HET, _AYIN_LETTER, _HE}

# Overrides keyed on bare lemma id (the OSHB disambiguation letter
# stripped -- see _bare_lemma_id). Only apply via transliterate_word()/
# transliterate_ref(); bare transliterate(text) has no lemma and never
# consults this table.
OVERRIDES = {
    "3068": "YHWH",
    "3069": "YHWH",
    "3389": "Yerushalayim",
    "3605": "kol",
}

_LEMMA_ID_RE = re.compile(r"^(\d+)")

# Native script a fragment must never contain (the whole Hebrew block:
# letters, niqqud, cantillation, maqqef, sof-pasuq).
SCRIPT_RE = re.compile("[֐-׿]")


def _bare_lemma_id(lemma_segment):
    """'3389' -> '3389'; '1004 b' -> '1004'; '' / None -> None. The
    trailing letter is an OSHB disambiguator, not part of the id (see
    joshua_study_style_reference.md §2) -- opaque here, just stripped."""
    if not lemma_segment:
        return None
    m = _LEMMA_ID_RE.match(lemma_segment.strip())
    return m.group(1) if m else None


def _clusters(morpheme):
    """Group each base consonant with the combining marks that follow it."""
    clusters = []
    for ch in morpheme:
        if ch in _HEB_LETTERS:
            clusters.append([ch, []])
        elif clusters and (unicodedata.combining(ch) != 0):
            clusters[-1][1].append(ch)
    return clusters


def _own_vowel_mark(marks):
    for m in marks:
        if m in _VOWELS or m == _SHVA:
            return m
    return None


def _consonant_text(base, marks):
    if base == _SHIN:
        return "ś" if _SIN_DOT in marks else "sh"
    return _CONSONANTS[base]


def _is_forte(base, marks, prev_audible):
    """Whether this cluster's dagesh is forte (doubling), not lene or a
    mater marker (shuruq / mappiq). See module docstring."""
    if _DAGESH not in marks:
        return False
    if base == _VAV:
        return False  # shuruq is a mater, not gemination (handled in the mater pass)
    if base == _HE:
        return False  # mappiq marks a consonantal final he, not doubling
    if base in _BEGADKEFAT:
        return prev_audible
    return True


def _translit_morpheme(morpheme):
    cl = _clusters(morpheme)
    n = len(cl)
    own_vowel = [_own_vowel_mark(marks) for _, marks in cl]

    # Pass 1: matres lectionis. A vowelless consonant followed by a bare
    # vav carrying holam/holam-haser (no dagesh) or a dagesh with no vowel
    # of its own (shuruq) absorbs that vav's vowel instead of also
    # emitting a consonant "w". A hiriq or tsere immediately followed by a
    # bare, unmarked yod absorbs that yod the same way (drop it, i not
    # iy / e not ey).
    absorbed = [False] * n
    absorbed_vowel = [None] * n
    for i in range(n):
        base, marks = cl[i]
        if own_vowel[i] is None and i + 1 < n:
            nbase, nmarks = cl[i + 1]
            n_vowel_marks = [m for m in nmarks if m in _VOWELS]
            if nbase == _VAV and n_vowel_marks == [_HOLAM]:
                absorbed_vowel[i], absorbed[i + 1] = "o", True
            elif nbase == _VAV and n_vowel_marks == [_HOLAM_HASER]:
                absorbed_vowel[i], absorbed[i + 1] = "o", True
            elif nbase == _VAV and _DAGESH in nmarks and not n_vowel_marks:
                absorbed_vowel[i], absorbed[i + 1] = "u", True
        if own_vowel[i] in (_HIRIQ, _TSERE) and i + 1 < n:
            nbase, nmarks = cl[i + 1]
            if nbase == _YOD and not nmarks:
                absorbed[i + 1] = True

    real_indices = [i for i in range(n) if not absorbed[i]]

    def prev_real(pos):
        return real_indices[pos - 1] if pos > 0 else None

    def next_real(pos):
        return real_indices[pos + 1] if pos + 1 < len(real_indices) else None

    out = []
    prev_audible = False
    for pos, i in enumerate(real_indices):
        base, marks = cl[i]
        is_last_real = pos == len(real_indices) - 1
        is_word_initial = pos == 0

        is_word_initial_shuruq = (
            pos == 0 and base == _VAV and own_vowel[i] is None and _DAGESH in marks
        )

        if is_word_initial_shuruq:
            cons, vowel = "", "u"
        else:
            forte = _is_forte(base, marks, prev_audible)
            cons = _consonant_text(base, marks)
            if forte:
                cons = cons + cons

            if own_vowel[i] == _SHVA:
                if is_word_initial:
                    # A lone consonant+shva (bound prefixes -- article,
                    # ל/ב/כ shown alone) can only be a syllable onset,
                    # never a closed syllable, so word-initial wins even
                    # when it coincides with word-final.
                    vowel = "e"
                elif is_last_real:
                    vowel = ""
                elif forte:
                    vowel = "e"
                else:
                    pj, nj = prev_real(pos), next_real(pos)
                    prev_is_shva = pj is not None and own_vowel[pj] == _SHVA
                    next_is_shva = nj is not None and own_vowel[nj] == _SHVA
                    if prev_is_shva:
                        vowel = "e"   # second of a consecutive pair: vocal
                    elif next_is_shva:
                        vowel = ""    # first of a consecutive pair: silent
                    else:
                        vowel = ""    # default: silent
            elif own_vowel[i] is not None:
                vowel = _VOWELS[own_vowel[i]]
            elif absorbed_vowel[i] is not None:
                vowel = absorbed_vowel[i]
            else:
                vowel = ""

        # Furtive patach: a patach on a word/morpheme-final het/ayin/
        # mappiq'd he glides in before the guttural, not after.
        is_furtive = (
            is_last_real
            and own_vowel[i] == _PATACH
            and (base in (_HET, _AYIN_LETTER) or (base == _HE and _DAGESH in marks))
        )
        if is_furtive:
            pj = prev_real(pos)
            prev_vowel = own_vowel[pj] if pj is not None else None
            if prev_vowel in (_PATACH, _QAMATS):
                is_furtive = False

        out.append(vowel + cons if is_furtive else cons + vowel)
        prev_audible = vowel != ""

    return "".join(out)


def transliterate(text: str) -> str:
    """Transliterate a Hebrew word or phrase, deterministically -- no
    lemma-keyed overrides applied (see transliterate_word/
    transliterate_ref for that). Non-Hebrew characters (spaces, Latin
    text, sof-pasuq, etc.) pass through unchanged, so a multi-word phrase
    keeps its spacing. Maqqef renders as a hyphen."""
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _HEB_LETTERS:
            j = i
            while j < n and (
                text[j] in _HEB_LETTERS
                or unicodedata.combining(text[j]) != 0
                or text[j] == "/"
            ):
                j += 1
            word = text[i:j]
            morphemes = [m for m in word.split("/") if m]
            out.append("-".join(_translit_morpheme(m) for m in morphemes))
            i = j
        elif ch == _MAQQEF:
            out.append("-")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _align_lemma_to_surface(surface_morphemes, lemma, morph):
    """Return a list, one entry per surface morpheme, of that morpheme's
    bare lemma id (or None). A pronoun-suffix morph segment ("Sp3ms" etc)
    has no corresponding lemma segment -- OSHB's lemma field only carries
    one entry per *content* morpheme, not per surface morpheme -- so this
    walks morph's segments, skipping "S..." ones, consuming lemma's
    segments in order for the rest."""
    if not morph:
        lemma_segs = lemma.split("/") if lemma else []
        return [_bare_lemma_id(s) for s in lemma_segs] + [None] * (
            len(surface_morphemes) - len(lemma_segs)
        )

    morph_segs = morph.split("/")
    if morph_segs and morph_segs[0].startswith("H"):
        morph_segs[0] = morph_segs[0][1:]
    lemma_segs = lemma.split("/") if lemma else []

    per_morpheme = []
    li = 0
    for seg in morph_segs:
        if seg.startswith("S"):
            per_morpheme.append(None)
        else:
            per_morpheme.append(lemma_segs[li] if li < len(lemma_segs) else None)
            li += 1

    if len(per_morpheme) != len(surface_morphemes):
        raise ValueError(
            f"morph segment count ({len(per_morpheme)}) != surface morpheme "
            f"count ({len(surface_morphemes)}) for surface={surface_morphemes!r} "
            f"lemma={lemma!r} morph={morph!r}"
        )
    return [_bare_lemma_id(s) for s in per_morpheme]


def transliterate_word(surface: str, lemma: str, morph: str = None) -> str:
    """Transliterate one <w>'s surface form, applying OVERRIDES per
    morpheme via its lemma id. `lemma` and `morph` are the raw
    Joshua-words.tsv field values for this word (morph is needed to align
    lemma segments to surface morphemes correctly when a pronoun suffix is
    present -- see _align_lemma_to_surface); morph may be omitted only when
    the word has no suffix segment (lemma and surface morpheme counts
    already match 1:1)."""
    surface_morphemes = [m for m in surface.split("/") if m]
    lemma_ids = _align_lemma_to_surface(surface_morphemes, lemma, morph)
    parts = []
    for morpheme, lemma_id in zip(surface_morphemes, lemma_ids):
        if lemma_id in OVERRIDES:
            parts.append(OVERRIDES[lemma_id])
        else:
            parts.append(_translit_morpheme(morpheme))
    return "-".join(parts)


_ref_rows_cache = {}


def _load_rows_by_ref(words_tsv):
    if words_tsv not in _ref_rows_cache:
        rows = {}
        with open(words_tsv, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="	")
            for row in reader:
                rows.setdefault(row["ref"], []).append(row)
        _ref_rows_cache[words_tsv] = rows
    return _ref_rows_cache[words_tsv]


def _to_tsv_ref(ref: str) -> str:
    """'Josh 1:1' -> 'Josh.1.1' (the word table's ref spelling)."""
    book, rest = ref.split(" ", 1)
    chap, verse = rest.split(":")
    return f"{book}.{chap}.{verse}"


def transliterate_ref(ref: str, words_tsv: str = None) -> str:
    """Transliterate every word of a verse, in word-table order,
    space-joined, applying lemma-keyed overrides. `ref` is the spoken form
    ("Josh 1:1"), matching the reading text. Word-based, not raw-text-
    based: it does not reproduce maqqef or sof-pasuq, since those aren't
    part of any <w> row (see transliterate() for raw-text phrase
    handling, which does). `words_tsv` defaults to the current book's."""
    if words_tsv is None:
        from biblecore.book import book
        words_tsv = book().path("words")
    tsv_ref = _to_tsv_ref(ref)
    rows = _load_rows_by_ref(words_tsv).get(tsv_ref)
    if not rows:
        raise ValueError(f"no {os.path.basename(words_tsv)} rows for ref "
                         f"{ref!r} ({tsv_ref!r})")
    return " ".join(
        transliterate_word(row["surface"], row["lemma"], row["morph"])
        for row in rows
    )
