"""CenterBLC's Text-Fabric build of Rahlfs' 1935 LXX (the Old Testament in
Greek) -- a reference corpus for canon leads (plan D4), not a book's own
corpus (no book reads it as `corpus.adapter()`; the NT-in-Greek is
corpus/morphgnt.py). Ported from Matthew's pipeline/greek_corpus.py, which
reads it read-only for pipeline/canon_leads.py.

Format (four plain-text Text-Fabric feature files, one value per word-slot
node, in `paths.lxx`):
    lex_utf8.tf   the lemma (Greek, with accents)
    book.tf       the LXX's own book abbreviation
    chapter.tf    chapter number
    verse.tf      verse number
Each feature file's data lines run 1:1 with word-slot nodes (1..N); a line
is either a bare value (the next node) or "start[-end]<TAB>value" (a run of
nodes sharing one value, expanded here). Higher node types (book/chapter/
verse nodes themselves) follow after node N in the same file and are never
read -- verified against fetch_corpus.py's pinned commit.
"""
import os
import sys


def _tf_values(path, limit):
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    while lines[i] != "":
        i += 1
    i += 1  # skip the blank line ending the header
    node = 1
    while node <= limit and i < len(lines):
        line = lines[i]
        i += 1
        if "\t" in line:
            rng, value = line.split("\t", 1)
            if "-" in rng:
                start, end = (int(x) for x in rng.split("-"))
            else:
                start = end = int(rng)
            for _ in range(start, min(end, limit) + 1):
                yield value
            node = end + 1
        else:
            yield line
            node += 1


BOOKS_KEY = "__order__"


def load_lxx(path, key_fn):
    """-> {book: [(chapter, verse, key)]} in text order, plus BOOKS_KEY:
    the LXX's own book order. `key_fn(lemma_greek)` turns a lemma into the
    same key the NT-in-Greek corpus uses (lang/greek.lemma_key, so the two
    corpora -- which don't share a numbering scheme -- match by
    transliteration, exactly as data-root slugs already collapse inflected
    forms onto one stem). No display surface form is kept (this dataset
    gives only the lemma per word); leads print the lemma key itself."""
    for name in ("lex_utf8.tf", "book.tf", "chapter.tf", "verse.tf"):
        if not os.path.exists(os.path.join(path, name)):
            sys.exit(f"LXX Text-Fabric data not found ({name}) at {path} -- "
                     f"see corpus/README.md")
    lex_path = os.path.join(path, "lex_utf8.tf")
    with open(lex_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    i = 0
    while lines[i] != "":
        i += 1
    n_words = len(lines) - (i + 1)
    if lines and lines[-1] == "":
        n_words -= 1

    lemmas = list(_tf_values(lex_path, n_words))
    books = list(_tf_values(os.path.join(path, "book.tf"), n_words))
    chapters = list(_tf_values(os.path.join(path, "chapter.tf"), n_words))
    verses = list(_tf_values(os.path.join(path, "verse.tf"), n_words))

    out = {}
    order = []
    for book, ch, v, lemma in zip(books, chapters, verses, lemmas):
        if book not in out:
            out[book] = []
            order.append(book)
        if not lemma:
            continue
        out[book].append((int(ch), int(v), key_fn(lemma)))
    out[BOOKS_KEY] = order
    return out
