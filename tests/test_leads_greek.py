"""Greek canon leads (plan D4): corpus/lxx.py + leads.py's Greek path,
proved against Matthew's own pipeline/canon_leads.py over a real unit,
read-only. Structured comparison (lead keys and hit counts), not a text
diff -- core's rendering deliberately differs in small ways (full osis book
names instead of Matthew's "Mt"/"Mk"/"Lk" short codes)."""
import importlib.util
import json
import os
import sys

import support
from biblecore import book as bookmod
from biblecore import leads

MATTHEW = os.path.normpath(os.path.join(support.CORE, "..", "Matthew"))
LXX_DIR = os.path.join(MATTHEW, "pipeline", "corpus", "lxx")
MGNT_DIR = os.path.join(MATTHEW, "pipeline", "corpus", "morphgnt")
UNIT_N = 13


def _have():
    return (os.path.exists(os.path.join(LXX_DIR, "lex_utf8.tf"))
            and os.path.exists(os.path.join(MGNT_DIR, "61-Mt-morphgnt.txt")))


def _matthew_module(name):
    path = os.path.join(MATTHEW, "pipeline", f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"matthew_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    old = sys.path[:]
    sys.path.insert(0, os.path.join(MATTHEW, "pipeline"))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = old
    return mod


def setup():
    cfg = {"book": "Matthew", "osis": "Matt", "slug": "matthew", "language": "greek",
           "corpus": {"kind": "morphgnt", "pin": "morphgnt/sblgnt", "word_ids": True},
           "versification": "source", "groupings": [], "components": [],
           "paths": {"morphgnt": MGNT_DIR, "lxx": LXX_DIR}}
    bookmod.use(bookmod.Book(cfg, MATTHEW))


def teardown():
    support.joshua_book()


def test_parity_with_matthews_own_canon_leads():
    if not _have():
        return ["Matthew's LXX/MorphGNT corpus not found next to bible-core"]
    row = next(u for u in json.load(open(os.path.join(MATTHEW, "data", "units.json"),
                                         encoding="utf-8"))["units"] if u["n"] == UNIT_N)
    passage = row["passage"]

    gc = _matthew_module("greek_corpus")
    cl = _matthew_module("canon_leads")
    their_nt, their_lxx, _order = cl.load_corpus()
    their_freq = cl.verse_freq(their_nt, their_lxx)
    their_uw = cl.passage_words(their_nt, passage)
    their_rare = cl.rare_leads(their_nt, their_lxx, their_freq, their_uw)
    their_phrase = cl.phrase_leads(their_lxx, their_freq, their_uw)

    our_nt, our_lxx, _order = leads.load_greek_corpus()
    our_freq = leads.verse_freq_greek(our_nt, our_lxx)
    our_uw = leads.passage_words_greek(our_nt, passage)
    our_rare = leads.rare_leads_greek(our_nt, our_lxx, our_freq, our_uw)
    our_phrase = leads.phrase_leads_greek(our_lxx, our_freq, our_uw)

    fails = []
    # KNOWN, correct differences from Matthew's simpler key scheme:
    #  * "ou2" -- Matthew's own script keys purely by transliteration
    #    ("ou"), collapsing ou (not) and ou (a distinct homograph lexeme)
    #    into one bucket. Core's lemma_ids() (morphgnt.py) disambiguates
    #    homographs with a digit, same as roots.py/audit.py do everywhere
    #    else -- so core correctly reports "ou2" as its own, separate rare
    #    lead, which Matthew's script silently folds into "ou".
    #  * "mechri(s)" -- Matthew's key keeps MorphGNT's parenthesized movable
    #    letter literally (its greek_corpus.py never strips it); core's
    #    lang/greek.lemma_key() strips it (a lemma-id can't contain '(' --
    #    roots.LEMMA_ID_RE), so "mechri(s)" and any other spelling of the
    #    same lemma correctly land on one "mechri" id, changing its
    #    frequency and dropping it out of core's rare-lead threshold. Not a
    #    lead core is missing -- the word just isn't rare once its
    #    occurrences are counted correctly under one id.
    KNOWN_KEY_DIFFERENCES = {"ou2", "mechri(s)"}
    their_rare_keys = {r["key"]: (len(r["lxx"]), len(r["nt"])) for r in their_rare
                       if r["key"] not in KNOWN_KEY_DIFFERENCES}
    our_rare_keys = {r["key"]: (len(r["lxx"]), len(r["nt"])) for r in our_rare
                     if r["key"] not in KNOWN_KEY_DIFFERENCES}
    if their_rare_keys != our_rare_keys:
        only_theirs = set(their_rare_keys) - set(our_rare_keys)
        only_ours = set(our_rare_keys) - set(their_rare_keys)
        diffs = {k: (their_rare_keys.get(k), our_rare_keys.get(k))
                for k in set(their_rare_keys) | set(our_rare_keys)
                if their_rare_keys.get(k) != our_rare_keys.get(k)}
        fails.append(f"rare leads differ: only in Matthew's {only_theirs}, "
                     f"only in core's {only_ours}, count mismatches {diffs}")

    their_phrase_keys = {tuple(w[0] for w in p["words"]): len(p["hits"]) for p in their_phrase}
    our_phrase_keys = {tuple(w[0] for w in p["words"]): len(p["hits"]) for p in our_phrase}
    if their_phrase_keys != our_phrase_keys:
        fails.append(f"phrase leads differ: Matthew's {len(their_phrase_keys)} vs "
                     f"core's {len(our_phrase_keys)}; symmetric diff "
                     f"{set(their_phrase_keys) ^ set(our_phrase_keys)}")

    if len(our_rare) < 3:
        fails.append(f"suspiciously few rare leads found: {len(our_rare)}")
    return fails
