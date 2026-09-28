"""A tiny Greek book for tests that shouldn't need the Matthew checkout:
three MorphGNT files (Matthew, Mark, John), a four-feature Text-Fabric LXX
and a two-entry morphological lexicon, all written into a temp folder.

    root = greek_book.make()      # the current Book is now "Matthew"
    ...
    greek_book.remove(root)       # and support.joshua_book() again

The words are chosen for what the tests check:
  * a homograph: 'τίς' (who?) first, then 'τις' (someone) -- lemma ids
    'tis' and 'tis2'; the LXX has 'τις' at Gen 1:1
  * a phrase shared with the LXX: βίβλος γενέσεως (Matt 1:1, Gen 2:4)
  * a rare word in Mark (a Synoptic, excluded from leads) and John
"""
import json
import os
import shutil
import tempfile

import support
from biblecore import book as bookmod

# (bbccvv, pos, parse, text, word, lemma)
NT = {
    "61-Mt": [
        ("010101", "N-", "----NSF-", "Βίβλος", "Βίβλος", "βίβλος"),
        ("010101", "N-", "----GSF-", "γενέσεως.", "γενέσεως", "γένεσις"),
        ("010102", "RI", "----NSM-", "τίς", "τίς", "τίς"),
        ("010102", "V-", "3PAI-S--", "λέγει;", "λέγει", "λέγω"),
        ("010103", "RI", "----NSM-", "τις", "τις", "τις"),
        ("010103", "N-", "----NSM-", "ζηλωτής", "ζηλωτής", "ζηλωτής"),
    ],
    "62-Mk": [
        ("020101", "N-", "----NSM-", "ζηλωτής", "ζηλωτής", "ζηλωτής"),
    ],
    "64-Jn": [
        ("040101", "N-", "----NSM-", "ζηλωτής", "ζηλωτής", "ζηλωτής"),
        ("040101", "V-", "3PAI-S--", "λέγει.", "λέγει", "λέγω"),
    ],
}
# (book, chapter, verse, lemma), one per LXX word node
LXX = [
    ("Gen", 1, 1, "τις"),
    ("Gen", 1, 1, "λέγω"),
    ("Gen", 2, 4, "βίβλος"),
    ("Gen", 2, 4, "γένεσις"),
    ("Exod", 1, 1, "ζηλωτής"),
]
LEXICON = """\
βίβλος:
    pos: N
    gloss: book
γένεσις:
    pos: N
    gloss: "origin, birth"
"""


def tf(path, values, header="@node\n@valueType=str\n@writtenBy=test\n"):
    """A Text-Fabric feature file: one bare value per node, runs of equal
    values folded into a 'start-end<TAB>value' line (the shape book.tf
    and chapter.tf use for higher node types)."""
    lines, i = [], 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[j + 1] == values[i]:
            j += 1
        if j > i:
            lines.append(f"{i + 1}-{j + 1}\t{values[i]}")
        else:
            lines.append(str(values[i]))
        i = j + 1
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n" + "\n".join(lines) + "\n")


def write_lxx(folder, rows=LXX):
    os.makedirs(folder, exist_ok=True)
    tf(os.path.join(folder, "book.tf"), [r[0] for r in rows])
    tf(os.path.join(folder, "chapter.tf"), [r[1] for r in rows])
    tf(os.path.join(folder, "verse.tf"), [r[2] for r in rows])
    # the lemma file keeps one line per node, as the real one does
    with open(os.path.join(folder, "lex_utf8.tf"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("@node\n@valueType=str\n\n" + "\n".join(r[3] for r in rows) + "\n")


def make(units=({"n": 1, "slug": "unit-01", "passage": "Matthew 1:1–3", "title": "One"},)):
    root = tempfile.mkdtemp(prefix="bc-greek-")
    mgnt = os.path.join(root, "corpus", "morphgnt")
    os.makedirs(mgnt)
    for stem, rows in NT.items():
        with open(os.path.join(mgnt, f"{stem}-morphgnt.txt"), "w", encoding="utf-8",
                  newline="\n") as fh:
            for bcv, pos, parse, text, word, lemma in rows:
                fh.write(f"{bcv} {pos} {parse} {text} {word} {word.lower()} {lemma}\n")
    write_lxx(os.path.join(root, "corpus", "lxx"))
    lex = os.path.join(root, "corpus", "lexicon", "lexemes.yaml")
    os.makedirs(os.path.dirname(lex))
    with open(lex, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(LEXICON)
    os.makedirs(os.path.join(root, "data"))
    with open(os.path.join(root, "data", "units.json"), "w", encoding="utf-8") as fh:
        json.dump({"book": "Matthew", "unit_count": len(units), "units": list(units)}, fh)
    cfg = {"book": "Matthew", "osis": "Matt", "slug": "matthew", "language": "greek",
           "corpus": {"kind": "morphgnt", "pin": "morphgnt/sblgnt", "word_ids": True},
           "versification": "source", "groupings": [], "components": []}
    bookmod.use(bookmod.Book(cfg, root))
    return root


def remove(root):
    shutil.rmtree(root, ignore_errors=True)
    support.joshua_book()
