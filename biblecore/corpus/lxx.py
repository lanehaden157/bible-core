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
Each feature file's data lines follow the word-slot nodes (1..N); a line
is either a bare value (the next node) or "start[-end]<TAB>value" (a run of
nodes sharing one value, expanded here). A node with no value has no line:
the next line names its node explicitly, and the nodes skipped read as "".
Higher node types (book/chapter/verse nodes themselves) follow after node N
in the same file and are never read -- verified against fetch_corpus.py's
pinned commit. N is the last node lex_utf8.tf gives a value.
"""
import os
import sys


def _tf_lines(path):
    """The data lines of a feature file (after the header's blank line)."""
    lines = open(path, encoding="utf-8").read().split("\n")
    i = lines.index("") + 1
    if lines[-1] == "":
        lines.pop()
    return lines[i:]


def _tf_nodes(lines):
    """(first_node, last_node, value) per data line."""
    node = 1
    for line in lines:
        if "\t" in line:
            rng, value = line.split("\t", 1)
            if "-" in rng:
                start, end = (int(x) for x in rng.split("-"))
            else:
                start = end = int(rng)
        else:
            start = end = node
            value = line
        yield start, end, value
        node = end + 1


def _tf_values(lines, limit):
    """The value of every node 1..limit, "" for a node the file skips."""
    node = 1
    for start, end, value in _tf_nodes(lines):
        if node > limit:
            return
        for _ in range(node, min(start, limit + 1)):
            yield ""
        for _ in range(max(start, node), min(end, limit) + 1):
            yield value
        node = end + 1
    for _ in range(node, limit + 1):
        yield ""


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
    lex = _tf_lines(os.path.join(path, "lex_utf8.tf"))
    n_words = max((end for _s, end, _v in _tf_nodes(lex)), default=0)

    lemmas = list(_tf_values(lex, n_words))
    books, chapters, verses = (list(_tf_values(_tf_lines(os.path.join(path, f)), n_words))
                               for f in ("book.tf", "chapter.tf", "verse.tf"))

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
