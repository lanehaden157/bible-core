"""An independent check of the reading data layer (data/words/<ch>.json and
data/lemmas.json) against the source corpus (Matthew's interlinear pilot,
note 9).

    python -m biblecore verify-words

It uses nothing that builds those files: no corpus parsing, no language
adapter, no transliterator. It re-reads the source its own way (MorphGNT by
a plain whitespace split; OSHB's OSIS XML with ElementTree, its own
Ketiv/Qere rule and its own read of morphhb's VerseMap.xml), so a bug in
the generator can't hide in both. `biblecore test` runs it as `words`.

Checks (any failure exits 1):
  1. the chapter files hold exactly the source's verses (displayed
     numbering), and each verse the source's words, by word id, in order
  2. every row is {w, t, l, m} (plus "a": 1 on an Aramaic word, and only there)
  3. transliterations use only the scheme's Latin letters, never the
     original script (Greek: a-z with ē/ō and a final ’ for elision;
     Hebrew: a-z, ʾ ʿ ḥ ṭ ś š, the combining low line and hyphens)
  4. every parsing was put into words (no raw morphology code left)
  5. lemma ids follow the source's lemmas: the same source lemma always
     gets the same id, and two source lemmas never share one (Greek); the
     id is the word's last Strong's segment (Hebrew)
  6. lemmas.json has exactly the words' lemma ids, each {t, g, n, refs}
     with n and refs matching the words; a Greek t is its id without the
     homograph digit. A Greek lemma without a gloss fails (the MorphGNT
     lexicon covers the NT); Hebrew ones are listed, since Strong's has gaps.
"""
import glob
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from biblecore.book import book

WORD_KEYS = {"w", "t", "l", "m"}
LEMMA_KEYS = {"t", "g", "n", "refs"}
TRANSLIT = {
    "greek": re.compile(r"^[A-Za-zēōĒŌ]+’?$"),
    "hebrew": re.compile(r"^[A-Za-zʾʿḥṭśš̲-]+$"),
}
NATIVE = re.compile(r"[Ͱ-Ͽἀ-῿֐-׿]")
# a source code left undecoded: MorphGNT "V-" / "3PAI-S--", OSHB "HC/Vpw3ms"
RAW_MORPH = re.compile(r"^(?:[A-Z][A-Za-z0-9-]*:|[HA][A-Z][a-z0-9]*(?:/[A-Z][a-z0-9]*)*$)")
OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"


# ------------------------------------------------------------------ sources

def greek_source(b):
    """{(ch, v): [(word id, lemma)]} from the book's MorphGNT file, by split.
    The file name is the one thing taken from the corpus adapter (its FILES
    list); none of its parsing is used."""
    from biblecore.corpus.morphgnt import FILES
    stem = dict(FILES).get(b.osis)
    path = os.path.join(b.path("morphgnt"), f"{stem}-morphgnt.txt")
    if stem is None or not os.path.exists(path):
        raise FileNotFoundError(f"no MorphGNT file for {b.osis} in {b.path('morphgnt')}")
    out = defaultdict(list)
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            cols = line.split()
            if len(cols) != 7:
                continue
            ref = cols[0]
            key = (int(ref[2:4]), int(ref[4:6]))
            out[key].append((f"{ref}{len(out[key]) + 1:02d}", cols[6]))
    return out


def hebrew_source(b):
    """{(ch, v): [(word id, main lemma key, aramaic?)]} from OSHB, Ketiv
    dropped (a <w> followed by a <note> whose x-qere reading has a <w>), in
    the book's displayed numbering (VerseMap.xml read here, not by versify)."""
    src = os.path.join(b.path("wlc"), f"{b.osis}.xml")
    vmap = {}
    if b.versification != "source":
        vm = os.path.join(b.path("wlc"), "VerseMap.xml")
        if os.path.exists(vm):
            text = open(vm, encoding="utf-8").read()
            for s, d in re.findall(r'<verse wlc="([^"]+)" kjv="([^"]+)"', text):
                sb, sc, sv = s.split("!")[0].split(".")
                _db, dc, dv = d.split("!")[0].split(".")
                if sb == b.osis:
                    vmap.setdefault((int(sc), int(sv)), (int(dc), int(dv)))
    out = defaultdict(list)
    root = ET.parse(src).getroot()
    for verse in root.iter(OSIS + "verse"):
        _bk, c, v = verse.get("osisID").split(".")
        key = vmap.get((int(c), int(v)), (int(c), int(v)))
        kids = list(verse)
        for i, el in enumerate(kids):
            if el.tag == OSIS + "w":
                nxt = kids[i + 1] if i + 1 < len(kids) else None
                qere = (nxt.find(f"{OSIS}rdg[@type='x-qere']/{OSIS}w")
                        if nxt is not None and nxt.tag == OSIS + "note" else None)
                w = qere if qere is not None else el
                out[key].append((w.get("id"), _strongs_key(w.get("lemma", "")),
                                 w.get("morph", "").startswith("A")))
    return out


def _strongs_key(lemma):
    """'c/1696' -> '1696', 'b/4057 b' -> '4057b', 'c/d' -> ''. A trailing
    '+' (OSHB: the name runs on into the next word, Beth-el) isn't part of
    the lexeme."""
    keys = [s.replace(" ", "").rstrip("+") for s in lemma.split("/")
            if re.fullmatch(r"\d+(?: ?[a-z])?\+?", s.strip())]
    return keys[-1] if keys else ""


# ------------------------------------------------------------------ check

def check(b=None):
    """(errors, notes)."""
    b = b or book()
    lang = b.language
    errs, notes = [], []
    if lang == "greek":
        src = greek_source(b)
    elif lang == "hebrew":
        src = hebrew_source(b)
    else:
        return [], [f"no independent check for {lang}"]
    translit = TRANSLIT[lang]

    words_dir = os.path.join(b.path("data"), "words")
    chapters = sorted({c for c, _ in src})
    on_disk = sorted(int(os.path.basename(p)[:-5])
                     for p in glob.glob(os.path.join(words_dir, "*.json")))
    if on_disk != chapters:
        errs.append(f"chapter files {on_disk} != the source's chapters {chapters}")

    src_to_id, id_to_src = {}, {}
    counts, refs = defaultdict(int), defaultdict(list)
    n_rows = 0
    for c in chapters:
        p = os.path.join(words_dir, f"{c}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        if d.get("c") != c:
            errs.append(f"words/{c}.json: c is {d.get('c')!r}")
        got = d.get("verses", {})
        want = sorted(v for cc, v in src if cc == c)
        if sorted(int(v) for v in got) != want:
            errs.append(f"words/{c}.json: verses differ from the source "
                        f"(only in the data: {sorted(set(map(int, got)) - set(want))[:8]}, "
                        f"only in the source: {sorted(set(want) - set(map(int, got)))[:8]})")
        for v in want:
            rows, source = got.get(str(v), []), src[(c, v)]
            if [r.get("w") for r in rows] != [s[0] for s in source]:
                errs.append(f"{c}:{v}: word ids differ from the source "
                            f"({len(rows)} in the data, {len(source)} in the source)")
                continue
            n_rows += len(rows)
            for i, (row, s) in enumerate(zip(rows, source), 1):
                where = f"{c}:{v} word {i} ({row['w']})"
                keys = set(row) - {"a"}
                if keys != WORD_KEYS:
                    errs.append(f"{where}: keys {sorted(row)}")
                    continue
                if NATIVE.search(row["t"]) or not translit.match(row["t"]):
                    errs.append(f"{where}: transliteration {row['t']!r}")
                if not row["m"] or RAW_MORPH.match(row["m"]):
                    errs.append(f"{where}: parsing not put into words: {row['m']!r}")
                lid = row["l"]
                if lang == "greek":
                    if src_to_id.setdefault(s[1], lid) != lid:
                        errs.append(f"{where}: lemma id {lid}, but {src_to_id[s[1]]} elsewhere "
                                    f"for the same source lemma")
                    if id_to_src.setdefault(lid, s[1]) != s[1]:
                        errs.append(f"{where}: id {lid} names two source lemmas")
                else:
                    if lid != s[1]:
                        errs.append(f"{where}: lemma id {lid!r}, the source says {s[1]!r}")
                    if bool(row.get("a")) != s[2] or row.get("a") not in (None, 1):
                        errs.append(f"{where}: Aramaic flag {row.get('a')!r} disagrees "
                                    f"with the source")
                if lid:
                    counts[lid] += 1
                    ref = f"{c}:{v}"
                    if not refs[lid] or refs[lid][-1] != ref:
                        refs[lid].append(ref)

    lem = json.load(open(os.path.join(b.path("data"), "lemmas.json"),
                         encoding="utf-8")).get("lemmas", {})
    if set(lem) != set(counts):
        errs.append(f"lemmas.json ids differ from the words: only in lemmas.json "
                    f"{sorted(set(lem) - set(counts))[:8]}, only in the words "
                    f"{sorted(set(counts) - set(lem))[:8]}")
    unglossed = []
    for lid, e in lem.items():
        if set(e) != LEMMA_KEYS:
            errs.append(f"lemma {lid}: keys {sorted(e)}")
            continue
        if e["n"] != counts.get(lid):
            errs.append(f"lemma {lid}: n={e['n']}, the words count {counts.get(lid)}")
        if e["refs"] != refs.get(lid):
            errs.append(f"lemma {lid}: refs differ from the words")
        if NATIVE.search(e["t"]) or (lang == "greek" and e["t"] != lid.rstrip("0123456789")):
            errs.append(f"lemma {lid}: t={e['t']!r}")
        if not e["g"]:
            unglossed.append(lid)
    if unglossed:
        msg = f"{len(unglossed)} lemma(s) without a gloss: {', '.join(sorted(unglossed)[:10])}"
        (errs if lang == "greek" else notes).append(msg)
    notes.insert(0, f"{len(chapters)} chapters, {len(src)} verses, {n_rows} words, "
                    f"{len(lem)} lemmas")
    return errs, notes


def main(argv=None):
    errs, notes = check()
    for e in errs[:60]:
        print("FAIL", e)
    if len(errs) > 60:
        print(f"... and {len(errs) - 60} more")
    for n in notes:
        print("note", n)
    print(f"verify-words: {'ok' if not errs else f'{len(errs)} failure(s)'}")
    return 1 if errs else 0
