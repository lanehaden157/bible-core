"""World English Bible text for a tiered book: USFM -> data/web/<ch>.json.

    (run by `python -m biblecore emit`; the USFM comes from `fetch`)

The site shows this text only when a reader expands a `data-verses` block,
labelled as not the study's translation. WEB is public domain. The book's
USFM sits in `paths.web` (default corpus/web/), tracked in the book's repo and
pinned by sha1 in fetch.py, so a build never needs the network.

Output, one file per chapter of the whole book:

    data/web/<ch>.json   {"c": 1, "verses": {"1": "text", ...}}

English numbering, which is what a "kjv"-versification book displays.
Footnotes, cross-references, Strong's tags and character markup are dropped;
a verse bridge ("\\v 3-4") is stored under its first number.
"""
import json
import os
import re
import sys
from collections import OrderedDict

from biblecore import fetch
from biblecore.book import book

NOTE_RE = re.compile(r"\\(f|fe|x|ef|ex)\s.*?\\\1\*", re.S)
ATTR_RE = re.compile(r"\|[^\\|]*(?=\\)")
CLOSE_RE = re.compile(r"\\\+?[a-z]+\d*\*")
OPEN_RE = re.compile(r"\\\+?[a-z]+\d*(?:\s|$)")
# paragraph and poetry markers whose lines carry verse text
TEXT_MARKERS = {"p", "m", "pi", "pi1", "pi2", "mi", "nb", "q", "q1", "q2", "q3", "q4",
                "qr", "qc", "qm", "li", "li1", "li2", "li3", "li4", "pc", "pr", "cls", "b"}
LINE_RE = re.compile(r"^\\([a-z]+\d*)\*?(?:\s+(.*))?$")


def clean(text):
    text = NOTE_RE.sub("", text)
    text = ATTR_RE.sub("", text)
    text = CLOSE_RE.sub("", text)
    text = OPEN_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(usfm):
    """{chapter: {verse: text}} from one book's USFM."""
    usfm = NOTE_RE.sub("", usfm.replace("\r\n", "\n"))
    out, ch, v = OrderedDict(), None, None
    for line in usfm.split("\n"):
        line = line.rstrip()
        m = LINE_RE.match(line)
        if not m:
            if v is not None and line.strip():
                out[ch][v] += " " + line
            continue
        marker, rest = m.group(1), m.group(2) or ""
        if marker == "c":
            ch, v = int(rest.split()[0]), None
            out.setdefault(ch, OrderedDict())
        elif marker == "v":
            mv = re.match(r"(\d+)\S*\s*(.*)$", rest)
            if ch is None or not mv:
                continue
            v = int(mv.group(1))
            out[ch][v] = mv.group(2)
        elif marker in TEXT_MARKERS and v is not None and rest:
            out[ch][v] += " " + rest
    return OrderedDict(
        (c, OrderedDict((k, clean(t)) for k, t in vs.items() if clean(t)))
        for c, vs in out.items())


def usfm_path(b):
    name = fetch.WEB_FILES.get(b.osis)
    return os.path.join(b.path("web"), name[0]) if name else None


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
    wrote = 0
    folder = b.data("web")
    for ch, vs in chapters.items():
        text = json.dumps({"c": ch, "verses": {str(k): t for k, t in vs.items()}},
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
