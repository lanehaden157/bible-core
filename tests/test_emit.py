"""emit.py (the interlinear/search data layer) and the OSHB morphology
decoder, on a scratch copy of Joshua."""
import contextlib
import csv
import io
import json
import os
import re
import shutil

import support
from biblecore import emit
from biblecore.book import book
from biblecore.lang.hebrew_morph import _morpheme, describe

_tmp = None
HEB = re.compile("[֐-׿]")


def setup():
    global _tmp
    _tmp = support.scratch_book()


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def test_describe_reads_slots_by_position():
    cases = {
        "HR/Ncmsc": "preposition + noun, masc. sing. construct",
        "HC/Vqw3ms": "and + verb, qal wayyiqtol, 3rd masc. sing.",
        "HVqrmpa": "verb, qal participle, masc. pl. absolute",
        "HTo/Sp3ms": "object marker + pronoun suffix, 3rd masc. sing.",
        "ANcmsd/Td": "Aramaic: noun, masc. sing. determined + the",
    }
    return [f"{c}: {describe(c)!r} != {want!r}" for c, want in cases.items()
            if describe(c) != want]


def test_every_joshua_morpheme_decodes():
    rows = csv.DictReader(open(os.path.join(support.JOSHUA, "Joshua-words.tsv"),
                               encoding="utf-8"), delimiter="\t")
    raw = {m for r in rows for m in r["morph"][1:].split("/") if _morpheme(m, False) == m}
    if raw:
        return [f"{len(raw)} morpheme(s) left undecoded: {sorted(raw)[:10]}"]


def test_emit_outputs():
    with contextlib.redirect_stdout(io.StringIO()):
        emit.main([])
    d = book().path("data")
    fails = []
    words = json.load(open(os.path.join(d, "words", "1.json"), encoding="utf-8"))
    w1 = words["verses"]["1"][0]
    if set(w1) - {"w", "t", "l", "m", "a"} or not w1["t"] or not w1["l"]:
        fails.append(f"word row shape: {w1}")
    lem = json.load(open(os.path.join(d, "lemmas.json"), encoding="utf-8"))["lemmas"]
    if "5414" not in lem or lem["5414"]["n"] < 50 or not lem["5414"]["g"]:
        fails.append(f"natan (5414) lemma entry: {lem.get('5414', {}).get('n')}")
    text = json.load(open(os.path.join(d, "text.json"), encoding="utf-8"))["verses"]
    if not text or text[0]["r"] != "1:1" or "<" in text[0]["t"] or not text[0]["t"]:
        fails.append(f"text.json first verse: {text[:1]}")
    blob = "".join(open(os.path.join(root, f), encoding="utf-8").read()
                   for root, _d, fs in os.walk(d) for f in fs
                   if f.endswith(".json") and ("words" in root or f in ("lemmas.json", "text.json")))
    if HEB.search(blob):
        fails.append("native script in the emitted data")
    before = open(os.path.join(d, "lemmas.json"), encoding="utf-8").read()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        emit.main([])
    if "(0 file(s) changed)" not in out.getvalue() or \
            open(os.path.join(d, "lemmas.json"), encoding="utf-8").read() != before:
        fails.append("emit isn't idempotent")
    return fails


def test_main_lemma():
    cases = {"c/1696": "1696", "l/6485 a": "6485a", "b/1007+": "1007", "d": "", "": ""}
    return [f"{k!r} -> {emit.main_lemma(k)!r}" for k, v in cases.items()
            if emit.main_lemma(k) != v]
