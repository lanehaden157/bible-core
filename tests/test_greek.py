"""The Greek transliteration scheme's authoritative definition (review E12).
If this file and greek.py's docstring disagree, THIS FILE WINS.

Each expected value was worked out from the rules (letters, diphthongs,
nasal gamma, rough breathing -> h, initial rho -> rh, accents / smooth
breathing / iota subscript / diaeresis dropped, leading capital kept), not
copied from transliterate()'s output. The parity test then holds the core
module to Matthew's own pipeline/greek.py over every word of Matthew, since
the scheme is frozen per language (H10) and Matthew's study already uses it.
"""
import importlib.util
import os

import support
from biblecore.lang import greek

MATTHEW = os.path.normpath(os.path.join(support.CORE, "..", "Matthew"))
MORPHGNT = os.path.join(MATTHEW, "pipeline", "corpus", "morphgnt", "61-Mt-morphgnt.txt")

CASES = {
    # letters, eta/omega macrons
    "βίβλος": "biblos",
    "γενέσεως": "geneseōs",
    "ἐγέννησεν": "egennēsen",
    "διδάσκαλος": "didaskalos",
    "ἐλέησον": "eleēson",
    # digraph consonants and upsilon -> y
    "Χριστός": "Christos",
    "ψυχή": "psychē",
    "φῶς": "phōs",
    "θεός": "theos",
    # diphthongs
    "οὐρανός": "ouranos",
    "πνεῦμα": "pneuma",
    "Ἐμμανουήλ": "Emmanouēl",
    "Ἰησοῦς": "Iēsous",
    # nasal gamma
    "ἄγγελος": "angelos",
    "εὐαγγέλιον": "euangelion",
    # rough breathing, including on the second letter of a diphthong
    "ἅγιος": "hagios",
    "ἁμαρτία": "hamartia",
    "υἱός": "huios",
    "αἷμα": "haima",
    "εὑρίσκω": "heuriskō",
    "ὑπό": "hypo",
    # rho
    "ῥαββί": "rhabbi",
    "Ῥώμη": "Rhōmē",
    # iota subscript dropped
    "ᾠδή": "ōdē",
    # diaeresis: letters unchanged
    "Μωϋσῆς": "Mōysēs",
}


def test_cases():
    return [f"{g}: got {greek.transliterate(g)!r}, want {want!r}"
            for g, want in CASES.items() if greek.transliterate(g) != want]


def test_phrase_keeps_separators():
    got = greek.transliterate("βίβλος γενέσεως, Ἰησοῦ")
    if got != "biblos geneseōs, Iēsou":
        return [got]


def test_lemma_key():
    fails = []
    for lemma, key in {"κληρονομέω": "klēronomeō", "ἔλεος": "eleos", "Ἰησοῦς": "iēsous"}.items():
        if greek.lemma_key(lemma) != key:
            fails.append(f"{lemma}: {greek.lemma_key(lemma)!r} != {key!r}")
        if not greek.LEMMA_ID_RE.match(greek.lemma_key(lemma)):
            fails.append(f"{key} doesn't match LEMMA_ID_RE")
    return fails


def test_parity_with_matthew_over_every_word():
    src = os.path.join(MATTHEW, "pipeline", "greek.py")
    if not (os.path.exists(src) and os.path.exists(MORPHGNT)):
        return ["Matthew checkout (pipeline/greek.py + MorphGNT) not found next to bible-core"]
    spec = importlib.util.spec_from_file_location("matthew_greek", src)
    theirs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theirs)
    diffs, n = [], 0
    for line in open(MORPHGNT, encoding="utf-8"):
        parts = line.split()
        for w in (parts[3], parts[6]):
            n += 1
            a, b = greek.transliterate(w), theirs.transliterate(w)
            if a != b:
                diffs.append(f"{w}: core {a!r}, Matthew {b!r}")
    return diffs[:10] if diffs else ([] if n > 30000 else [f"only {n} words read"])
