"""MorphGNT (SBLGNT) corpus: the Greek New Testament, one file per book.

    python -m biblecore corpus        # write <Book>-reading.txt and <Book>-words.tsv

The second corpus adapter (review G7), with the same interface as
corpus/oshb.py: build(b), load_words(b), load_reading(b). Everything
downstream (data-w, the audit, roots, emit) does id arithmetic, so a Greek
book gets Joshua's audit quality once its word table exists.

Source lines (https://github.com/morphgnt/sblgnt):
    010101 N- ----NSF- Βίβλος Βίβλος βίβλος βίβλος
    bbccvv pos parse    text   word   normalized lemma

Word table columns match OSHB's:
  word_id  bbccvv + two-digit position in the verse ("01010101"): stable,
           alphanumeric, unique in the book
  ref      "Matt.1.1"
  surface  the word without punctuation (column 5)
  lemma    the lemma id: lang/greek.lemma_key(lemma), plus a digit when two
           distinct NT lemmas share a transliteration (ordered by first
           appearance in canonical order, so ids are stable across books)
  morph    "<pos>:<parse>" (lang/greek_morph.describe reads it)

The reading text joins column 4 (the text with its punctuation), one verse
per line: "Matt 1:1<TAB>Βίβλος γενέσεως …". SBLGNT's verse numbering is the
English one, so book.json should say `"versification": "source"`.

book.json: "corpus": {"kind": "morphgnt", "pin": "morphgnt/sblgnt@<commit>",
"word_ids": true}. `paths.morphgnt` is the folder of *-morphgnt.txt files
(default corpus/morphgnt).
"""
import csv
import os
import re

from biblecore.lang import greek

# OSIS id -> MorphGNT file stem, in canonical order
FILES = [
    ("Matt", "61-Mt"), ("Mark", "62-Mk"), ("Luke", "63-Lk"), ("John", "64-Jn"),
    ("Acts", "65-Ac"), ("Rom", "66-Ro"), ("1Cor", "67-1Co"), ("2Cor", "68-2Co"),
    ("Gal", "69-Ga"), ("Eph", "70-Eph"), ("Phil", "71-Php"), ("Col", "72-Col"),
    ("1Thess", "73-1Th"), ("2Thess", "74-2Th"), ("1Tim", "75-1Ti"), ("2Tim", "76-2Ti"),
    ("Titus", "77-Tit"), ("Phlm", "78-Phm"), ("Heb", "79-Heb"), ("Jas", "80-Jas"),
    ("1Pet", "81-1Pe"), ("2Pet", "82-2Pe"), ("1John", "83-1Jn"), ("2John", "84-2Jn"),
    ("3John", "85-3Jn"), ("Jude", "86-Jud"), ("Rev", "87-Re"),
]
LINE_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


def _dir(b):
    return b.path("morphgnt")


def _file(b, stem):
    return os.path.join(_dir(b), f"{stem}-morphgnt.txt")


def _rows(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = LINE_RE.match(line)
            if m:
                yield m.groups()


def lemma_ids(b):
    """Greek lemma -> id, over every NT book on disk, so the same lemma gets
    the same id in every book. A transliteration two lemmas share gets a
    digit on the second and later (by first appearance)."""
    seen, ids, taken = {}, {}, {}
    for _osis, stem in FILES:
        p = _file(b, stem)
        if not os.path.exists(p):
            continue
        for g in _rows(p):
            lemma = g[8]
            if lemma in ids:
                continue
            key = greek.lemma_key(lemma)
            n = taken.get(key, 0) + 1
            taken[key] = n
            ids[lemma] = key if n == 1 else f"{key}{n}"
    return ids


def _book_stem(b):
    for osis, stem in FILES:
        if osis == b.osis:
            return stem
    raise ValueError(f"{b.osis} isn't a MorphGNT book (NT osis ids: "
                     f"{', '.join(o for o, _ in FILES)})")


def parse(b):
    path = _file(b, _book_stem(b))
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found -- set paths.morphgnt in book.json "
                                f"to the folder of *-morphgnt.txt files")
    ids = lemma_ids(b)
    reading, words = [], []
    cur, text, pos_in_verse = None, [], 0
    for bk, c, v, pos, parse_, t, word, _norm, lemma in _rows(path):
        ref = (int(c), int(v))
        if ref != cur:
            if cur:
                reading.append(f"{b.osis} {cur[0]}:{cur[1]}\t{' '.join(text)}")
            cur, text, pos_in_verse = ref, [], 0
        pos_in_verse += 1
        text.append(t)
        words.append((f"{bk}{c}{v}{pos_in_verse:02d}", f"{b.osis}.{int(c)}.{int(v)}",
                      word, ids[lemma], f"{pos}:{parse_}"))
    if cur:
        reading.append(f"{b.osis} {cur[0]}:{cur[1]}\t{' '.join(text)}")
    return reading, words


def build(b):
    reading, words = parse(b)
    with open(b.path("reading"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(reading) + "\n")
    with open(b.path("words"), "w", encoding="utf-8", newline="\n") as f:
        f.write("word_id\tref\tsurface\tlemma\tmorph\n")
        for row in words:
            f.write("\t".join(row) + "\n")
    return {"verses": len(reading), "words": len(words)}


_words_cache = {}


def load_words(b=None):
    if b is None:
        from biblecore.book import book
        b = book()
    path = b.path("words")
    if path not in _words_cache:
        with open(path, encoding="utf-8") as f:
            out = []
            for row in csv.DictReader(f, delimiter="\t"):
                _bk, ch, v = row["ref"].split(".")
                out.append({**row, "ch": int(ch), "v": int(v), "lang": "greek"})
        _words_cache[path] = out
    return _words_cache[path]


def load_reading(b=None):
    if b is None:
        from biblecore.book import book
        b = book()
    line_re = re.compile(re.escape(b.osis) + r" (\d+):(\d+)\t(.*)")
    out = []
    with open(b.path("reading"), encoding="utf-8") as f:
        for line in f:
            m = line_re.match(line.rstrip("\n"))
            if m:
                out.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    if not out:
        raise ValueError(f"{b.path('reading')} parsed to zero '{b.osis} C:V' lines")
    return out


def _clear():
    _words_cache.clear()


from biblecore.book import on_reset  # noqa: E402
on_reset(_clear)
