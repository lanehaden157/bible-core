"""Apply a thread delta's ready entries to data/threads.json.

    python -m biblecore apply-delta 17 [--dry]

Reads out/thread-delta-NN.md (written by `port`) and applies the two kinds of
line the porter prints as ready JSON:

    add to `X`.payoffs: `{"unit": N, "ref": "...", "note": "..."}`
    set `X`.opens: `{"unit": N, "ref": "...", "note": "..."}`

A payoff is skipped when the thread already has one for that unit, and an
opens when the thread already has a noted one, so re-running is harmless.
Everything else in the delta (status changes, candidates, promotions) is
judgment and stays by hand. threads.json keeps its formatting: indent 2,
no trailing newline.
"""
import argparse
import json
import os
import re
import sys

from biblecore.book import book

LINE = re.compile(r"^\s*-\s+(add to|set)\s+`([^`]+)`\.(payoffs|opens):\s+`(\{.*\})`\s*$")


def parse_delta(text):
    """[(verb, thread id, 'payoffs'|'opens', entry dict)] in file order."""
    out = []
    for line in text.splitlines():
        m = LINE.match(line)
        if m:
            out.append((m.group(1), m.group(2), m.group(3), json.loads(m.group(4))))
    return out


def apply(threads, items):
    """Mutate `threads` (the loaded threads.json); return (applied, skipped)."""
    by_id = {t["id"]: t for t in threads["threads"]}
    applied, skipped = [], []
    for verb, tid, kind, entry in items:
        t = by_id.get(tid)
        label = f"{tid}.{kind} unit {entry.get('unit')} {entry.get('ref', '')}"
        if t is None:
            skipped.append(f"{label}: no thread `{tid}`")
        elif kind == "payoffs":
            pays = t.setdefault("payoffs", [])
            if any(p.get("unit") == entry.get("unit") for p in pays):
                skipped.append(f"{label}: already has a payoff for that unit")
            else:
                pays.append(entry)
                pays.sort(key=lambda p: p.get("unit", 0))
                applied.append(label)
        else:
            if (t.get("opens") or {}).get("note"):
                skipped.append(f"{label}: opens already has a note")
            else:
                t["opens"] = entry
                applied.append(label)
    return applied, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore apply-delta")
    ap.add_argument("unit", type=int)
    ap.add_argument("--dry", action="store_true", help="report, write nothing")
    a = ap.parse_args(argv)
    b = book()
    src = os.path.join(b.path("out"), f"thread-delta-{a.unit:02d}.md")
    if not os.path.exists(src):
        sys.exit(f"no {os.path.relpath(src, b.root)} -- run `port {a.unit}` first")
    with open(src, encoding="utf-8") as fh:
        items = parse_delta(fh.read())
    path = b.data("threads.json")
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    threads = json.loads(raw)
    applied, skipped = apply(threads, items)
    for s in applied:
        print("  applied", s)
    for s in skipped:
        print("  skipped", s)
    print(f"{len(applied)} applied, {len(skipped)} skipped of {len(items)} ready entries"
          + (" [dry]" if a.dry else ""))
    if applied and not a.dry:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(threads, indent=2, ensure_ascii=False))
        print("wrote", os.path.relpath(path, b.root), "-- then `build` (it audits)")
    return 0
