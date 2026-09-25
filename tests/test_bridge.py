"""canon/bridge.json (F2): every row's cited words are really in the cited
verses. The Hebrew side is checked against the word tables on disk (Numbers,
Joshua), the LXX side against Matthew's CenterBLC LXX, and the NT side
against MorphGNT, all read-only. Rows whose corpus isn't on disk are
skipped, not failed."""
import importlib.util
import json
import os
import re

import support
from biblecore.lang import greek

BIBLE = os.path.dirname(support.CORE)
PIPE = os.path.join(BIBLE, "Matthew", "pipeline")
MGNT = os.path.join(PIPE, "corpus", "morphgnt")
BRIDGE = json.load(open(os.path.join(support.CORE, "canon", "bridge.json"), encoding="utf-8"))
REF_RE = re.compile(r"^((?:\d )?[A-Za-z]+) (\d+):(\d+)")
NT_STEMS = {"Matt": "61-Mt", "1 Cor": "67-1Co"}
NT_BOOKNO = {"61-Mt": "01", "67-1Co": "07"}
LXX_NAMES = {"Num": "Num", "Hos": "Hos", "Josh": "Josh", "Deut": "Deut"}


def _ref(r):
    m = REF_RE.match(r)
    return m.group(1), int(m.group(2)), int(m.group(3))


def test_rows_shape():
    fails = []
    threads = {t["id"] for t in json.load(open(os.path.join(support.CORE, "canon", "threads.json"),
                                               encoding="utf-8"))["threads"]}
    for row in BRIDGE["rows"]:
        if row["thread"] is not None and row["thread"] not in threads:
            fails.append(f"bridge row names unknown canon thread {row['thread']!r}")
        for k in row["nt"] + row["lxx"]:
            if not greek.LEMMA_ID_RE.match(k):
                fails.append(f"{k!r} isn't a Greek lemma key")
        if not all(re.match(r"^\d+[a-z]?$", h) for h in row["heb"]):
            fails.append(f"heb ids {row['heb']}")
    return fails


def test_nt_words_in_their_verses():
    if not os.path.isdir(MGNT):
        return []
    fails = []
    for row in BRIDGE["rows"]:
        book, c, v = _ref(row["nt_ref"])
        stem = NT_STEMS.get(book)
        if not stem:
            fails.append(f"no MorphGNT file mapped for {book}")
            continue
        prefix = f"{NT_BOOKNO[stem]}{c:02d}{v:02d}"
        lemmas = {greek.lemma_key(l.split()[6])
                  for l in open(os.path.join(MGNT, f"{stem}-morphgnt.txt"), encoding="utf-8")
                  if l.startswith(prefix)}
        for k in row["nt"]:
            if k not in lemmas:
                fails.append(f"{k} not in {row['nt_ref']} ({sorted(lemmas)[:8]}…)")
    return fails


def test_lxx_words_in_their_verses():
    src = os.path.join(PIPE, "greek_corpus.py")
    if not os.path.exists(os.path.join(PIPE, "corpus", "lxx", "lex_utf8.tf")):
        return []
    spec = importlib.util.spec_from_file_location("matthew_greek_corpus", src)
    import sys
    sys.path.insert(0, PIPE)
    try:
        gc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gc)
        lxx = gc.load_lxx()
    finally:
        sys.path.remove(PIPE)
    fails = []
    for row in BRIDGE["rows"]:
        book, c, v = _ref(row["lxx_ref"])
        got = {r[2] for r in lxx.get(LXX_NAMES.get(book, book), []) if r[0] == c and r[1] == v}
        for k in row["lxx"]:
            if k not in got:
                fails.append(f"{k} not in LXX {row['lxx_ref']}")
    return fails


def test_hebrew_ids_occur():
    """Each Hebrew id occurs in Numbers' or Joshua's word table."""
    import csv
    ids = set()
    for tsv in (os.path.join(BIBLE, "Numbers", "Numbers-words.tsv"),
                os.path.join(BIBLE, "Joshua", "Joshua-words.tsv")):
        if os.path.exists(tsv):
            for r in csv.DictReader(open(tsv, encoding="utf-8"), delimiter="\t"):
                for seg in r["lemma"].split("/"):
                    m = re.match(r"^(\d+)", seg.strip())
                    if m:
                        ids.add(m.group(1))
    if not ids:
        return []
    return [f"Strong's {h} occurs in neither Numbers nor Joshua"
            for row in BRIDGE["rows"] for h in row["heb"] if h not in ids]
