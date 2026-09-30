"""The MorphGNT corpus adapter (G7), proved on Matthew's data read-only:
the word table and reading text build, the reading text matches Matthew's
own SBLGNT file verse for verse, Greek lemma ids flow through roots and
the audit, and emit writes an interlinear layer with no native script."""
import contextlib
import io
import json
import os
import re
import shutil
import tempfile

import support
from biblecore import book as bookmod
from biblecore import emit, roots
from biblecore.corpus import morphgnt
from biblecore.lang.greek_morph import describe

MATTHEW = support.MATTHEW_SRC  # read-only inputs (corpora, its own pipeline)
MGNT = os.path.join(MATTHEW, "pipeline", "corpus", "morphgnt")
LEXICON = os.path.join(support.CORE, "corpus", "lexicon", "lexemes.yaml")
GREEK = re.compile("[Ͱ-Ͽἀ-῿]")
_tmp = None


def _have():
    return os.path.exists(os.path.join(MGNT, "61-Mt-morphgnt.txt"))


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-mgnt-")
    cfg = {"book": "Matthew", "osis": "Matt", "slug": "matthew", "language": "greek",
           "corpus": {"kind": "morphgnt", "pin": "morphgnt/sblgnt", "word_ids": True},
           "versification": "source", "groupings": [], "components": [],
           "paths": {"morphgnt": MGNT, "greek_lexicon": LEXICON}}
    os.makedirs(os.path.join(_tmp, "data"))
    json.dump({"book": "Matthew", "unit_count": 0, "units": []},
              open(os.path.join(_tmp, "data", "units.json"), "w"))
    bookmod.use(bookmod.Book(cfg, _tmp))


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def test_build_and_reading_parity():
    if not _have():
        return ["Matthew's MorphGNT not found next to bible-core"]
    b = bookmod.book()
    counts = morphgnt.build(b)
    fails = []
    lines = sum(1 for _ in open(os.path.join(MGNT, "61-Mt-morphgnt.txt"), encoding="utf-8"))
    if counts["words"] != lines:
        fails.append(f"{counts['words']} words vs {lines} source lines")
    ours = {(c, v): t for c, v, t in morphgnt.load_reading(b)}
    theirs = {}
    for line in open(os.path.join(MATTHEW, "MatthewSBLGNT.txt"), encoding="utf-8"):
        m = re.match(r"Matt (\d+):(\d+)\t(.*)", line.rstrip("\n"))
        if m:
            theirs[(int(m.group(1)), int(m.group(2)))] = " ".join(m.group(3).split())
    if set(ours) != set(theirs):
        fails.append(f"verse sets differ: {sorted(set(ours) ^ set(theirs))[:5]}")
    # The words must match exactly. Punctuation may not: the two SBLGNT copies
    # write elision as U+2019 vs U+02BC and the question mark as ';' vs
    # U+037E, a couple of verses differ by a comma (21:15), and one by a
    # paragraph-initial capital (27:24). So compare the lower-cased
    # words with punctuation removed, and cap the punctuation-only differences.
    import unicodedata
    words_of = lambda t: re.sub(r"[^\w\s]", "", unicodedata.normalize("NFC", t.replace("ʼ", "")).lower()).split()
    punct = lambda t: " ".join(unicodedata.normalize("NFC", t.replace("’", "ʼ")).split())
    diff = [k for k in ours if k in theirs and words_of(ours[k]) != words_of(theirs[k])]
    if diff:
        fails.append(f"{len(diff)} verse(s) differ in their words, e.g. {diff[:3]}")
    loose = [k for k in ours if k in theirs and punct(ours[k]) != punct(theirs[k])]
    if len(loose) > 3:
        fails.append(f"{len(loose)} verses differ in punctuation (expected a couple): {loose[:5]}")
    return fails


def test_ids_flow_through_roots_and_audit():
    if not _have():
        return ["Matthew's MorphGNT not found"]
    b = bookmod.book()
    morphgnt.build(b)
    words = morphgnt.load_words(b)
    fails = []
    if len({w["word_id"] for w in words}) != len(words):
        fails.append("word ids aren't unique")
    known = roots.known_lemma_ids(b.path("words"))
    if "klēronomeō" not in known:
        fails.append("klēronomeō not among Matthew's lemma ids")
    doc = {"roots": {"inherit": {"ids": ["klēronomeō"], "note": "x"},
                     "mercy": {"ids": ["eleos"], "note": "x"}}}
    errs = roots.validate(doc, b.path("words"))
    if errs:
        fails.append(f"roots.validate: {errs}")
    from biblecore import audit
    hits = audit.source_hits_for_root(words, ["klēronomeō"])
    if (5, 5) not in hits.values():
        fails.append(f"klēronomeō hits miss Matt 5:5: {sorted(set(hits.values()))}")
    mercy = audit.source_hits_for_root(words, ["eleos"])
    if (9, 13) not in mercy.values():
        fails.append("eleos hits miss Matt 9:13")
    return fails


def test_emit_greek():
    if not _have():
        return ["Matthew's MorphGNT not found"]
    b = bookmod.book()
    morphgnt.build(b)
    with contextlib.redirect_stdout(io.StringIO()):
        emit.main([])
    w = json.load(open(os.path.join(_tmp, "data", "words", "5.json"), encoding="utf-8"))
    v5 = w["verses"]["5"]
    fails = []
    if not any(x["l"] == "klēronomeō" for x in v5):
        fails.append(f"Matt 5:5 words: {[x['l'] for x in v5]}")
    blob = "".join(open(os.path.join(r, f), encoding="utf-8").read()
                   for r, _d, fs in os.walk(os.path.join(_tmp, "data")) for f in fs)
    if GREEK.search(blob):
        fails.append("native Greek script in emitted data")
    lemmas = json.load(open(os.path.join(_tmp, "data", "lemmas.json"), encoding="utf-8"))["lemmas"]
    if lemmas.get("klēronomeō", {}).get("g") != "I inherit, obtain":
        fails.append(f"klēronomeō gloss: {lemmas.get('klēronomeō')}")
    return fails


def test_greek_lexicon_covers_matthew():
    """Every lemma actually in Matthew's own text resolves to a gloss in the
    morphological lexicon. (Matthew's corpus/morphgnt/ folder holds every NT
    book, for future books' canon leads; lemma_forms() ids the whole set,
    so this checks against Matthew's own word table, not that wider set --
    a gap elsewhere is a future book's problem, worth re-checking then,
    since MorphGNT sub-projects have occasionally drifted on accentuation.)"""
    if not _have() or not os.path.exists(LEXICON):
        return ["Matthew's MorphGNT or the vendored lexicon not found"]
    from biblecore.lang import greek_lexicon
    b = bookmod.book()
    morphgnt.build(b)
    forms = morphgnt.lemma_forms(b)
    glosses = greek_lexicon.load_glosses(LEXICON)
    used = {row["lemma"] for row in morphgnt.load_words(b)}
    missing = sorted({forms[key] for key in used if forms.get(key) not in glosses})
    if missing:
        return [f"{len(missing)} Matthew lemma(s) with no lexicon gloss, e.g. {missing[:5]}"]
    return []


def test_describe():
    cases = {
        "V-:3AAI-S--": "verb, aorist active indicative, 3rd sing.",
        "N-:----NSF-": "noun, nom. fem. sing.",
        "RA:----GSM-": "the, gen. masc. sing.",
        "V-:-PAPNSM-": "verb, present active participle, nom. masc. sing.",
        "A-:----NPM-": "adjective, nom. masc. pl.",
        "C-:--------": "conjunction",
    }
    return [f"{c}: {describe(c)!r} != {want!r}" for c, want in cases.items() if describe(c) != want]
