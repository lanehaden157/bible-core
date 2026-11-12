"""Tiers: a unit is full, condensed or digest, and some are peaks.

A book opts in with book.json `"tiers": true`. Nothing in this module (or any
tier code elsewhere) runs for a book without it, so a tierless book builds
exactly as it did before tiers existed.

Where the pieces live:

  units.json row   tier (full | condensed | digest, default full), peak: true,
                   stretches [{tier: condensed|digest, verses: "C:V–V"}],
                   digest "two to four sentences". `units-from-map` writes
                   tier/peak/stretches/digest from the unit map (units_map.py);
                   a unit's own meta `digest` fills the row at port.
  fragment         `<section class="block digest" data-verses="C:V–V">` holds
                   the summary of a digest stretch (components/digest).
  data/web/<ch>    World English Bible text for the expand button (web.py).
  occurrences.json `untr` per root: occurrences in verses the unit does not
                   translate, counted from the corpus (untranslated()).

    python -m biblecore tiers      # the check below, on its own
"""
import json
import os
import re
import sys

from biblecore import meta as um
from biblecore.book import book

TIERS = ("full", "condensed", "digest")
STRETCH_TIERS = ("condensed", "digest")
DIGEST_MAX_WORDS = 80

DIGEST_BLOCK_RE = re.compile(r'<section\b[^>]*\bclass="[^"]*\bdigest\b[^"]*"[^>]*>', re.I)


def words(text):
    return len(re.findall(r"\S+", text or ""))


def _passage_range(passage):
    m = um._PASSAGE_RANGE_RE.search(passage or "")
    if m:
        return ((int(m.group(1)), int(m.group(2))),
                (int(m.group(3) or m.group(1)), int(m.group(4))))
    m = re.search(r"(\d+):(\d+)", passage or "")
    return ((int(m.group(1)), int(m.group(2))),) * 2 if m else None


def _next(cv):
    return (cv[0], cv[1] + 1)


def _merge(ranges):
    """Digest blocks that run on from one another count as one stretch."""
    out = []
    for lo, hi in sorted(ranges):
        if out and (lo <= _next(out[-1][1]) or lo == (out[-1][1][0] + 1, 1)):
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def digest_ranges(html):
    """[(lo, hi)] declared by the fragment's digest blocks."""
    out = []
    for m in DIGEST_BLOCK_RE.finditer(html):
        d = um.DECLARED_RE.search(m.group(0))
        r = um._parse_declared(d.group(1)) if d else None
        if r:
            out.append(r)
    return out


def row_errors(row):
    """Problems with a unit row's own tier keys (built or not)."""
    n = row.get("n")
    where = f"unit {n}"
    errs = []
    tier = row.get("tier", "full")
    if tier not in TIERS:
        errs.append(f"{where}: tier {tier!r} is not one of {list(TIERS)}")
    if "peak" in row and row["peak"] is not True:
        errs.append(f"{where}: peak must be true or absent")
    if row.get("peak") and tier != "full":
        errs.append(f"{where}: a peak must be tier full (it is {tier!r})")
    if "digest" in row and not isinstance(row["digest"], str):
        errs.append(f"{where}: digest must be a string")
    span = _passage_range(row.get("passage"))
    seen = []
    for i, s in enumerate(row.get("stretches") or []):
        w = f"{where}: stretches[{i}]"
        if not isinstance(s, dict) or set(s) - {"tier", "verses"}:
            errs.append(f"{w}: must be {{tier, verses}}")
            continue
        if s.get("tier") not in STRETCH_TIERS:
            errs.append(f"{w}: tier {s.get('tier')!r} is not condensed or digest")
        r = um._parse_declared(s.get("verses") or "")
        if r is None:
            errs.append(f"{w}: verses {s.get('verses')!r} is not 'C:V–V'")
            continue
        if span and not (span[0] <= r[0] and r[1] <= span[1]):
            errs.append(f"{w}: {s['verses']} is outside the unit's passage")
        for o in seen:
            if not (r[1] < o[0] or o[1] < r[0]):
                errs.append(f"{w}: overlaps another stretch")
        seen.append(r)
    return errs


def built_errors(row, html):
    """Problems with a built unit: digest present and short, digest blocks
    covering the stretches (and the whole unit when its tier is digest)."""
    n = row.get("n")
    where = f"unit {n}"
    errs = []
    d = (row.get("digest") or "").strip() if isinstance(row.get("digest"), str) else ""
    if not d:
        errs.append(f"{where}: no digest -- every built unit of a tiered book carries "
                    f"two to four sentences (the unit map's Digests section, or the "
                    f"meta block's `digest` at port)")
    elif words(d) > DIGEST_MAX_WORDS:
        errs.append(f"{where}: digest is {words(d)} words, over {DIGEST_MAX_WORDS}")
    have = _merge(digest_ranges(html))
    need = [um._parse_declared(s["verses"]) for s in row.get("stretches") or []
            if s.get("tier") == "digest"]
    if row.get("tier") == "digest":
        need.append(_passage_range(row.get("passage")))
    for r in need:
        if r and not any(a <= r[0] and r[1] <= b for a, b in have):
            errs.append(f"{where}: digest stretch {_fmt(r)} is not covered by "
                        f"`section.block.digest` blocks (data-verses)")
    for m in DIGEST_BLOCK_RE.finditer(html):
        if not um.DECLARED_RE.search(m.group(0)):
            errs.append(f"{where}: a digest block has no data-verses")
    return errs


def _fmt(r):
    (c1, v1), (c2, v2) = r
    return f"{c1}:{v1}" + (f"–{v2}" if c1 == c2 and v2 != v1 else
                            f"–{c2}:{v2}" if (c1, v1) != (c2, v2) else "")


def validate(units_json, read=None):
    """Every tier problem in units.json and the built fragments ([] == clean).
    `read(row)` returns a built unit's html (default: units/<slug>.html)."""
    if read is None:
        def read(row):
            p = os.path.join(book().path("units"), row["slug"] + ".html")
            with open(p, encoding="utf-8") as fh:
                return fh.read()
    errs = []
    if "digest" not in book().components:
        errs.append("book.json components must include 'digest' for a tiered book")
    for row in units_json.get("units", []):
        errs += row_errors(row)
        if row.get("built") and row.get("contract") != "legacy":
            errs += built_errors(row, read(row))
    return errs


# ---------------------------------------------------------------- untranslated

def untranslated(row, html, words_rows, roots_json, written):
    """{root: {count, verses}} -- occurrences of each tracked root in the
    unit's passage in verses the fragment does not write out. Counted from the
    corpus word table with audit's matcher, so the thread timelines stay true
    where a unit condenses or digests. `written` = {(ch, v)} of the fragment's
    verse blocks."""
    from biblecore import audit
    span = _passage_range(row.get("passage"))
    if not span:
        return {}
    out = {}
    for slug, entry in sorted((roots_json.get("roots") or {}).items()):
        hits = audit.source_hits_for_entry(words_rows, entry)
        vs = sorted({cv for cv in hits.values()
                     if span[0] <= cv <= span[1] and cv not in written})
        n = sum(1 for cv in hits.values()
                if span[0] <= cv <= span[1] and cv not in written)
        if n:
            out[slug] = {"count": n, "verses": [f"{c}:{v}" for c, v in vs]}
    return out


def main(argv=None):
    b = book()
    if not b.tiers:
        print("not a tiered book (book.json \"tiers\" is not true)")
        return 0
    with open(b.data("units.json"), encoding="utf-8") as fh:
        errs = validate(json.load(fh))
    for e in errs:
        print("  ERROR", e)
    print(f"tiers: {len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
