"""World English Bible text for a tiered book: USFM -> data/web/<ch>.json.

    (run by `python -m biblecore emit`; the USFM comes from `fetch`)

The site shows this text only when a reader expands a `data-verses` block,
labelled as not the study's translation. WEB is public domain. The book's
USFM sits in `paths.web` (default corpus/web/), tracked in the book's repo and
pinned by sha1 in fetch.py, so a build never needs the network.

Output, one file per chapter of the whole book:

    data/web/<ch>.json   {"c": 1, "verses": {"1": "text", "3-4": "text", ...}}

Numbered the way the book displays: WEB is English-numbered, so a book with
versification "kjv" gets it as is, and a Hebrew book with "source" gets each
English verse moved to the corpus verse it translates (versify.py: Lev
5:20-26 is English 6:1-7). A verse bridge ("\\v 3-4") is one entry under
"3-4". The build fails when a chapter's verses differ from the corpus's, so a
numbering mismatch is never shown as the wrong text.
"""
import json
import os
import re
import sys
from collections import OrderedDict

from biblecore import fetch, versify
from biblecore.book import book

NOTE_RE = re.compile(r"\\(f|fe|x|ef|ex)\s.*?\\\1\*", re.S)
ATTR_RE = re.compile(r"\|[^\\|]*(?=\\)")
CLOSE_RE = re.compile(r"\\\+?[a-z]+\d*\*")
MARK_RE = re.compile(r"^\\([a-z]+\d*)\*?(?:[ \t]+(.*))?$")
TOKEN_RE = re.compile(r"\\(c|v)[ \t]+(\d+)(?:[-\u2013](\d+))?[a-z]?")
OPEN_RE = re.compile(r"\\\+?[a-z]+\d*(?=[ \t]|$)[ \t]?")
# lines that carry no verse text: ids, headings, running heads, references,
# psalm titles
SKIP_MARKERS = {"id", "ide", "h", "toc1", "toc2", "toc3", "mt", "mt1", "mt2", "mt3",
                "mt4", "ms", "ms1", "ms2", "mr", "s", "s1", "s2", "s3", "s4", "r",
                "sr", "d", "sp", "rem", "cl", "cd", "iex", "imt"}


def clean(text):
    text = ATTR_RE.sub("", text)
    text = CLOSE_RE.sub("", text)
    text = OPEN_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(usfm):
    """{chapter: [(lo, hi, text)]} in text order; lo == hi unless a bridge."""
    usfm = NOTE_RE.sub("", usfm.replace("\r\n", "\n"))
    lines = []
    for line in usfm.split("\n"):
        line = line.strip()
        m = MARK_RE.match(line)
        if m and m.group(1) in SKIP_MARKERS:
            continue
        if m and m.group(1) not in ("c", "v"):
            line = m.group(2) or ""      # a paragraph or poetry marker: keep its text
        lines.append(line)
    text = " ".join(lines)
    out, ch, cur = OrderedDict(), None, None
    pos = 0
    for m in TOKEN_RE.finditer(text):
        if cur is not None:
            cur[2].append(text[pos:m.start()])
        pos = m.end()
        if m.group(1) == "c":
            ch, cur = int(m.group(2)), None
            out.setdefault(ch, [])
        elif ch is not None:
            lo = int(m.group(2))
            cur = (lo, int(m.group(3) or lo), [])
            out[ch].append(cur)
    if cur is not None:
        cur[2].append(text[pos:])
    return OrderedDict(
        (c, [(lo, hi, clean(" ".join(parts))) for lo, hi, parts in vs
             if clean(" ".join(parts))])
        for c, vs in out.items())


def verse_sets(chapters):
    """{chapter: {verse numbers}}, a bridge counted verse by verse."""
    return {c: {v for lo, hi, _ in vs for v in range(lo, hi + 1)}
            for c, vs in chapters.items()}


def to_source(b, chapters, corpus):
    """WEB's English numbering moved onto the corpus's own (a Hebrew book with
    versification "source"). `corpus` = {chapter: {verses}} in that numbering.
    Several English verses landing on one corpus verse are joined; one English
    verse spanning two corpus verses is given to both."""
    vmap = versify.load(b.path("wlc")).get(b.osis, {})
    present = {(c, v) for c, vs in corpus.items() for v in vs}
    out = OrderedDict()
    for c, vs in chapters.items():
        for lo, hi, text in vs:
            # an English verse made of two corpus verses is shown under both
            for sc, sv in versify.to_source(c, lo, vmap, present) or [(c, lo)]:
                ent = out.setdefault(sc, OrderedDict())
                ent[(sv, sv)] = (ent[(sv, sv)] + " " + text) if (sv, sv) in ent else text
    return OrderedDict((c, [(lo, hi, t) for (lo, hi), t in sorted(ent.items())])
                       for c, ent in sorted(out.items()))


def corpus_verses(b):
    """{chapter: {verses}} of the book's corpus, in its displayed numbering."""
    from biblecore import corpus
    out = {}
    for row in corpus.adapter().load_words():
        out.setdefault(row["ch"], set()).add(row["v"])
    return out


def mismatches(chapters, corpus):
    """([problem], [note]): a chapter that exists on one side only, or a
    corpus verse WEB lacks, is a problem (a numbering shift shows up so). A
    verse only WEB has is a note: a different Greek text reads more verses
    (Matt 17:21 is in WEB, not in SBLGNT), and showing it is harmless."""
    have = verse_sets(chapters)
    bad, notes = [], []
    for c in sorted(set(have) | set(corpus)):
        a, k = have.get(c, set()), corpus.get(c, set())
        if k - a or (a and not k):
            bad.append(f"chapter {c}: WEB has {len(a)} verses, the corpus {len(k)}"
                       + (f" (only WEB: {sorted(a - k)})" if a - k else "")
                       + (f" (only corpus: {sorted(k - a)})" if k - a else ""))
        elif a - k:
            notes.append(f"chapter {c}: WEB also has {sorted(a - k)}")
    return bad, notes


def usfm_path(b):
    name = fetch.WEB_FILES.get(b.osis)
    return os.path.join(b.path("web"), name[0]) if name else None


def key(lo, hi):
    return str(lo) if lo == hi else f"{lo}-{hi}"


def emit(b, log=print):
    """Write data/web/<ch>.json. Returns (files changed, problem or None)."""
    path = usfm_path(b)
    if path is None:
        return 0, (f"no World English Bible pin for {b.osis} in fetch.WEB_FILES -- "
                   f"add its file name and sha1 there")
    if not os.path.exists(path):
        return 0, (f"{os.path.relpath(path, b.root)} is missing -- "
                   f"run `python -m biblecore fetch`")
    with open(path, encoding="utf-8") as fh:
        chapters = parse(fh.read())
    corpus = corpus_verses(b)
    if b.language == "hebrew" and b.versification == "source":
        chapters = to_source(b, chapters, corpus)
    bad, notes = mismatches(chapters, corpus)
    for n in notes:
        log(f"web: {n} (not in the corpus)")
    if bad:
        return 0, (f"the World English Bible's verses don't match the corpus's "
                   f"({len(bad)} chapter(s)): " + "; ".join(bad[:5]))
    wrote = 0
    folder = b.data("web")
    for ch, vs in chapters.items():
        text = json.dumps({"c": ch, "verses": {key(lo, hi): t for lo, hi, t in vs}},
                          ensure_ascii=False, separators=(",", ":")) + "\n"
        dest = os.path.join(folder, f"{ch}.json")
        old = open(dest, encoding="utf-8").read() if os.path.exists(dest) else None
        if old != text:
            os.makedirs(folder, exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            wrote += 1
    log(f"web: {len(chapters)} chapter file(s) from {os.path.basename(path)} "
        f"({wrote} changed)")
    return wrote, None


def main(argv=None):
    b = book()
    if not b.tiers:
        print("not a tiered book (book.json \"tiers\" is not true)")
        return 0
    _, problem = emit(b)
    if problem:
        print("FAIL", problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
