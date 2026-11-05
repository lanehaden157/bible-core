"""Run a unit's checks[] against the corpus, as one list for Lane.

    python -m biblecore checks UNIT|FILE

A check is {ref, claim, expect}. A research chat can only write transliteration
for passages outside its own book, so `expect` is a transliterated word
(`gulgolet`; macrons, apostrophes and doubled letters ignored), `!word` for a
word that should be absent, or a lemma id (`H1538`, `1538`). Nothing here is
dropped silently: every check comes back confirmed, partial, not found or
unresolved (the ref names no verse), and each transliteration shows the lemma
ids it resolved to, so Lane can see what was actually matched.

Hebrew books read the Hebrew Bible (morphhb, as `leads` does). A Greek book's
checks run against the LXX by `python -m biblecore lxx --checks`, which this
command hands over to; an NT passage cited from a Greek book is reported as
skipped there. A ref may name several passages ("Isa 38:10 / Wis 16:13"); their
words are pooled.
"""
import argparse
import glob
import json
import os
import re
import sys

from biblecore import leads, lxx_lookup, meta as um
from biblecore.book import book
from biblecore.unit_pack import _skeleton


def checks_from(arg):
    """Reuses lxx --checks' reader: a unit number/slug (its source artifact), an
    artifact .html or a .json list."""
    return lxx_lookup.checks_from(arg)


def _parts(trl):
    """The hyphen-separated pieces of a transliterated form (prefixes split off)."""
    return [p for p in re.split(r"[-\s]", trl) if p]


def _matches(expected, form):
    sk = _skeleton(expected)
    if not sk:
        return False
    for p in _parts(form) + [form]:
        ps = _skeleton(p)
        if ps == sk or (len(sk) >= 3 and sk in ps):
            return True
    return False


def passage_words(bible, ref):
    """[(word tuple, 'C:V')] for every passage in a ref string. ValueError if a
    book can't be placed; an empty result for a verse not in the corpus."""
    out, missing = [], []
    for code, lo, hi in lxx_lookup.parse_refs(ref, leads.BOOKS):
        got = 0
        for r, words in bible.get(code, ()):
            _b, c, v = r.split(".")
            if lo <= (int(c), int(v)) <= hi:
                got += 1
                out += [(w, f"{code} {c}:{v}") for w in words]
        if not got:
            missing.append(f"{code} {lo[0]}:{lo[1]}")
    return out, missing


def run_check(bible, check):
    """-> {status, held: [(entry, ok, resolved ids)], missing: [...], error}"""
    try:
        words, missing = passage_words(bible, check["ref"])
    except ValueError as exc:
        return {"status": "unresolved", "held": [], "missing": [], "error": str(exc)}
    forms = [(leads.translit(w), w[0]) for w, _r in words]
    expect = check["expect"]
    entries = [expect] if isinstance(expect, str) else list(expect)
    held = []
    for e in entries:
        e = e.strip()
        neg = e.startswith("!")
        word = e[1:].strip() if neg else e
        idm = re.fullmatch(r"H?(\d+)[a-z]?", word, re.I)
        if idm:
            found = sorted({lid for _f, lid in forms if lid == idm.group(1)})
        else:
            found = sorted({lid for f, lid in forms if _matches(word, f)})
        held.append((e, (not found) if neg else bool(found), found))
    n = sum(1 for _e, ok, _f in held if ok)
    status = "confirmed" if n == len(held) else "partial" if n else "not found"
    if missing and not words:
        status = "unresolved"
    return {"status": status, "held": held, "missing": missing, "error": None}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore checks", description=__doc__.split("\n\n")[0])
    ap.add_argument("source", metavar="UNIT|FILE")
    a = ap.parse_args(argv)
    b = book()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if b.language == "greek":
        return lxx_lookup.main(["--checks", a.source])
    checks = checks_from(a.source)
    if not checks:
        print("no checks[] in that source")
        return 0
    bible = leads.load_bible()
    counts, lane = {}, []
    for c in checks:
        r = run_check(bible, c)
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        print(f"{r['status'].upper():10} {c.get('ref', '?')} — {c.get('claim', '').strip()}")
        for e, ok, found in r["held"]:
            tail = (" -> ids " + ", ".join(found)) if found else ""
            print(f"{'':12}{'ok ' if ok else 'NO '} {e}{tail}")
        for m in r["missing"]:
            print(f"{'':12}no such verse in this corpus: {m}")
        if r["error"]:
            print(f"{'':12}{r['error']}")
        if r["status"] != "confirmed":
            lane.append(f"{c.get('ref', '?')} — {c.get('claim', '').strip()} ({r['status']})")
    print("\n" + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    if lane:
        print("\nFor Lane (checks that did not confirm; nothing is dropped):")
        for x in lane:
            print(f"  - {x}")
    return 0
