"""OSHB (morphhb) corpus: the Hebrew Bible, one OSIS XML file per book.

    python -m biblecore corpus        # write <Book>-reading.txt, <Book>-words.tsv,
                                      # candidate-boundaries.md for this book

Generalised from Joshua's pipeline/build_reading.py; its output for Joshua is
byte-identical (tests/test_corpus_oshb.py).

Ketiv/Qere: the running OSIS text carries the Ketiv word unpointed when a
Qere override exists (<note type="variant"><rdg type="x-qere">...). The
reading text substitutes the pointed Qere (what is read aloud). The word
table keeps a row for every <w>, Ketiv and Qere alike, each with its own
OSHB id, Ketiv first. load_words() drops the Ketiv rows again by that
adjacency (same ref, unpointed row immediately followed by a pointed one).

Aramaic (review E16): OSHB marks each word's language in the first letter
of its morph code, H for Hebrew and A for Aramaic (Dan 2:4b-7:28, Ezra
4:8-6:18 and 7:12-26, Jer 10:11, Gen 31:47). Lemma ids share Strong's one
number space, so roots and the audit need nothing new. load_words() gives
every row a `lang` from language_of(), and the word table stays as it is.
"""
import csv
import os
import re
import unicodedata
import xml.etree.ElementTree as ET

from biblecore import versify

NS = {"o": "http://www.bibletechnologies.net/2003/OSIS/namespace"}


def _local(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def _walk_verse(verse_el, ref, word_rows, boundaries):
    tokens = []
    glue_next = False

    def push(text):
        nonlocal glue_next
        if glue_next and tokens:
            tokens[-1] = tokens[-1] + text
            glue_next = False
        else:
            tokens.append(text)

    children = list(verse_el)
    i, n = 0, len(children)
    while i < n:
        el = children[i]
        tag = _local(el.tag)
        if tag == "w":
            wid, lemma, morph = el.get("id"), el.get("lemma", ""), el.get("morph", "")
            surface = "".join(el.itertext())
            qere = None
            if i + 1 < n and _local(children[i + 1].tag) == "note":
                qere = children[i + 1].find("o:rdg[@type='x-qere']/o:w", NS)
                if qere is not None:
                    i += 1
            if qere is not None:
                q_surface = "".join(qere.itertext())
                push(q_surface)
                word_rows.append((wid, ref, surface, lemma, morph))
                word_rows.append((qere.get("id"), ref, q_surface,
                                  qere.get("lemma", ""), qere.get("morph", "")))
            else:
                push(surface)
                word_rows.append((wid, ref, surface, lemma, morph))
        elif tag == "seg":
            seg_type = el.get("type", "")
            seg_text = el.text or ""
            if seg_type == "x-maqqef":
                if tokens:
                    tokens[-1] = tokens[-1] + seg_text
                else:
                    tokens.append(seg_text)
                glue_next = True
            elif seg_type == "x-sof-pasuq":
                if tokens:
                    tokens[-1] = tokens[-1] + seg_text
                else:
                    tokens.append(seg_text)
            elif seg_type in ("x-pe", "x-samekh"):
                boundaries.append((ref, seg_type))
            elif seg_text.strip():
                tokens.append(seg_text)
        i += 1

    line = " ".join(t for t in tokens if t != "")
    return re.sub(r" +", " ", line).strip()


def source_xml(b):
    return os.path.join(b.path("wlc"), f"{b.osis}.xml")


def parse(b):
    """(reading_lines, word_rows, boundaries) for book b."""
    src = source_xml(b)
    if not os.path.exists(src):
        raise FileNotFoundError(f"{src} not found -- is morphhb installed "
                                f"(npm ci) and paths.wlc right in book.json?")
    root = ET.parse(src).getroot()
    book_div = root.find(f".//o:div[@osisID='{b.osis}']", NS)
    if book_div is None:
        raise ValueError(f"{src} has no <div osisID='{b.osis}'>")
    reading, words, boundaries = [], [], []
    for chapter_el in book_div.findall("o:chapter", NS):
        chap = chapter_el.get("osisID").split(".")[1]
        for verse_el in chapter_el.findall("o:verse", NS):
            v = verse_el.get("osisID").split(".")[2]
            line = _walk_verse(verse_el, f"{b.osis}.{chap}.{v}", words, boundaries)
            reading.append(f"{b.osis} {chap}:{v}\t{line}")
    return reading, words, boundaries


def build(b):
    """Write the book's reading text, word table and boundary list. Returns
    counts for the caller to check against a printed edition."""
    reading, words, boundaries = parse(b)
    with open(b.path("reading"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(reading) + "\n")
    with open(b.path("words"), "w", encoding="utf-8", newline="\n") as f:
        f.write("word_id\tref\tsurface\tlemma\tmorph\n")
        for row in words:
            f.write("\t".join(row) + "\n")
    with open(b.path("boundaries"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Candidate paragraph-break boundaries (petuhah / setumah)\n\n")
        f.write("Raw list of every `x-pe` (petuhah, פ) and `x-samekh` (setumah, ס) "
                f"marker in {b.name}, from OSHB ({_pin(b)}), in document order. "
                "Not interpreted or grouped.\n\n")
        f.write("| # | Ref | Type |\n|---|---|---|\n")
        for idx, (ref, seg_type) in enumerate(boundaries, 1):
            label = "petuhah (פ)" if seg_type == "x-pe" else "setumah (ס)"
            _bk, c, v = ref.split(".")
            f.write(f"| {idx} | {b.osis} {c}:{v} | {label} |\n")
    counts = {"verses": len(reading), "words": len(words),
              "pe": sum(1 for _, t in boundaries if t == "x-pe"),
              "samekh": sum(1 for _, t in boundaries if t == "x-samekh")}
    moved = write_verse_map(b, reading)
    if moved:
        counts["renumbered"] = moved
    return counts


def write_verse_map(b, reading):
    """<slug>-versification.md: every verse whose displayed number differs
    from the corpus's, from morphhb's VerseMap.xml. Written only when the
    book has differences; returns how many verses moved."""
    vmap = versify.book_map(b)
    if not vmap:
        return 0
    present = set()
    for line in reading:
        c, v = line.split("\t", 1)[0].split(" ")[-1].split(":")
        present.add((int(c), int(v)))
    lines = [
        f"# {b.name} — verse numbering\n",
        f"Generated by `python -m biblecore corpus` from morphhb's "
        f"`wlc/VerseMap.xml` ({_pin(b)}); don't hand-edit. The study cites "
        f"English (KJV) numbering; the word table, reading text and "
        f"candidate boundaries keep the Hebrew (Leningrad) numbering. Every "
        f"verse not listed here has the same number in both.\n",
        "| English | Hebrew |", "|---|---|",
    ]
    for dc, dv in sorted(set(vmap.values())):
        srcs = versify.to_source(dc, dv, vmap, present)
        lines.append(f"| {dc}:{dv} | {' + '.join(f'{c}:{v}' for c, v in srcs)} |")
    with open(b.path("verse_map"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return len(vmap)


def _pin(b):
    pin = b.cfg["corpus"].get("pin", "morphhb")
    return pin.replace("@", " ")


# ------------------------------------------------------------------ loading

_CANTILLATION_RANGE = range(0x0591, 0x05B0)


def language_of(morph):
    """'aramaic' for an OSHB morph code starting with A, else 'hebrew'."""
    return "aramaic" if (morph or "").startswith("A") else "hebrew"


def has_niqqud(s):
    return any(unicodedata.combining(c) != 0 and ord(c) not in _CANTILLATION_RANGE
               for c in s)


_words_cache = {}


def load_words(b=None):
    """Every word-table row, Ketiv rows dropped, as dicts with integer ch/v.
    Order preserved (it is text order)."""
    if b is None:
        from biblecore.book import book
        b = book()
    path = b.path("words")
    if path in _words_cache:
        return _words_cache[path]
    with open(path, encoding="utf-8") as f:
        raw = list(csv.DictReader(f, delimiter="\t"))
    is_ketiv = [False] * len(raw)
    for i in range(len(raw) - 1):
        a, c = raw[i], raw[i + 1]
        if a["ref"] == c["ref"] and not has_niqqud(a["surface"]) and has_niqqud(c["surface"]):
            is_ketiv[i] = True
    # ch/v are in the book's displayed numbering; `ref` stays the corpus's
    # own (see biblecore/versify.py)
    vmap = versify.book_map(b)
    out = []
    for i, row in enumerate(raw):
        if is_ketiv[i]:
            continue
        _bk, ch, v = row["ref"].split(".")
        ch, v = versify.to_display(int(ch), int(v), vmap)
        out.append({**row, "ch": ch, "v": v, "lang": language_of(row["morph"])})
    _words_cache[path] = out
    return out


def load_reading(b=None):
    """[(ch, v, text)] from the reading text."""
    if b is None:
        from biblecore.book import book
        b = book()
    line_re = re.compile(re.escape(b.osis) + r" (\d+):(\d+)\t(.*)")
    vmap = versify.book_map(b)
    out = []
    with open(b.path("reading"), encoding="utf-8") as f:
        for line in f:
            m = line_re.match(line.rstrip("\n"))
            if m:
                ch, v = versify.to_display(int(m.group(1)), int(m.group(2)), vmap)
                if out and out[-1][:2] == (ch, v):   # two source verses, one shown
                    out[-1] = (ch, v, out[-1][2] + " " + m.group(3))
                else:
                    out.append((ch, v, m.group(3)))
    if not out:
        raise ValueError(f"{b.path('reading')} parsed to zero '{b.osis} C:V' lines")
    return out


def _clear():
    _words_cache.clear()


from biblecore.book import on_reset  # noqa: E402
on_reset(_clear)
