"""Assign `data-w` to tracked-thread spans by per-verse alignment.

    python -m biblecore data-w 6            # write units/unit-06.html
    python -m biblecore data-w 6 --dry      # report, write nothing
    python -m biblecore data-w --src X.html --passage "Numbers 6:1-27"

The chat side marks roots with data-root only; this fills the word ids.
Deliberately conservative: where a verse's span count and source-hit count
agree, the zip is unambiguous and it assigns; where they disagree it
assigns nothing in that verse and says why. A wrong data-w is worse than a
missing one (a missing one is a hard error the audit catches; a wrong one
silently points a popover at the wrong word).
"""
import argparse
import os
import re
import sys

from biblecore import audit as atc
from biblecore import meta as um
from biblecore.book import book
from biblecore.roots import load_roots


def verse_blocks(html, default_ch):
    """[(start, end, ch, v)] for each class="v" block carrying a number.

    Fragments usually write the bare verse number (`<span class="n">3</span>`)
    and state the chapter only when it changes -- unit 1 never states it at
    all -- so `default_ch` (the passage's opening chapter) seeds it, an
    explicit `C:V` resets it, and a verse number that goes *backwards*
    rolls it forward for a unit that spans a chapter boundary.
    """
    out, ch, prev_v = [], default_ch, None
    for m in atc.VBLOCK.finditer(html):
        seg = m.group(1)
        nm = atc.NUM_CV.search(seg)
        if not nm:
            continue
        v = int(nm.group(2))
        if nm.group(1):
            ch, prev_v = int(nm.group(1)), None
        elif prev_v is not None and v < prev_v:
            ch += 1
        prev_v = v
        out.append((m.start(1), m.end(1), ch, v))
    return out


def spans_in(html, start, end, root):
    """[(attr_start, attr_end, existing_w)] for this root's spans in a slice."""
    out = []
    for m in atc.SPAN_ATTRS.finditer(html, start, end):
        attrs = m.group(1)
        rm = atc.DATA_ROOT.search(attrs)
        if not rm or rm.group(1) != root:
            continue
        wm = atc.DATA_W.search(attrs)
        out.append((m.start(1), m.end(1), wm.group(1) if wm else None))
    return out


def plan(html, passage, threads_json=None, roots_json=None):
    """Work out every assignment without touching the html.

    Returns (edits, report) where edits is
    [(attr_start, attr_end, word_id)] in document order and report is a
    list of human-readable lines about what could not be decided.
    """
    threads_json = threads_json or um._load("threads.json")
    roots_json = roots_json or load_roots()
    tracked = atc._tracked_roots(threads_json)
    roots = roots_json.get("roots", {})

    lo, hi = atc.parse_range(passage)
    words = atc.load_words()
    blocks = verse_blocks(html, lo[0])

    edits, report = [], []
    for tid, root_slug in sorted(tracked.items(), key=lambda kv: kv[1]):
        entry = roots.get(root_slug)
        if entry is None:
            continue
        hits = {w: cv for w, cv in
                atc.source_hits_for_root(words, entry["ids"]).items()
                if atc.in_range(cv, lo, hi)}

        by_verse = {}
        for wid, cv in hits.items():
            by_verse.setdefault(cv, []).append(wid)
        # word-table order is text order; keep it.
        order = {row["word_id"]: i for i, row in enumerate(words)}
        for cv in by_verse:
            by_verse[cv].sort(key=lambda w: order.get(w, 0))

        for s, e, ch, v in blocks:
            spans = spans_in(html, s, e, root_slug)
            if not spans:
                continue
            want = by_verse.get((ch, v), [])
            have_w = [w for _, _, w in spans]

            if len(spans) != len(want):
                report.append(
                    f"{root_slug} {ch}:{v}: {len(spans)} span(s) but "
                    f"{len(want)} source hit(s) -- left alone. One span over "
                    f"two Hebrew words, one word as two spans, or a real "
                    f"mismatch; see CLAUDE.md retrofit recipe step 4.")
                continue

            for (a_s, a_e, existing), wid in zip(spans, want):
                if existing == wid:
                    continue
                if existing is not None:
                    report.append(
                        f"{root_slug} {ch}:{v}: span already has "
                        f"data-w=\"{existing}\" but alignment says "
                        f"\"{wid}\" -- left alone, resolve by hand.")
                    continue
                edits.append((a_s, a_e, wid))

    edits.sort(key=lambda t: t[0])
    return edits, report


def apply_edits(html, edits):
    """Inject data-w into each span's attribute run, back to front."""
    for a_s, a_e, wid in sorted(edits, reverse=True):
        attrs = html[a_s:a_e]
        if atc.DATA_W.search(attrs):
            attrs = atc.DATA_W.sub(f'data-w="{wid}"', attrs, count=1)
        else:
            attrs = re.sub(r'(data-root="[a-z0-9-]+")',
                           rf'\1 data-w="{wid}"', attrs, count=1)
        html = html[:a_s] + attrs + html[a_e:]
    return html


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore data-w")
    ap.add_argument("unit", nargs="?", type=int)
    ap.add_argument("--src", help="operate on this file instead of units/")
    ap.add_argument("--passage", help="required with --src")
    ap.add_argument("--dry", action="store_true", help="report, write nothing")
    a = ap.parse_args(argv)

    if a.src:
        if not a.passage:
            ap.error("--src requires --passage")
        path, passage = a.src, a.passage
    else:
        if a.unit is None:
            ap.error("give a unit number or --src")
        path = book().unit_path(a.unit)
        row = um._unit_row(um._load("units.json"), a.unit)
        if row is None:
            print(f"unit {a.unit} not in units.json")
            return 1
        passage = row["passage"]

    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    edits, report = plan(html, passage)

    for line in report:
        print("  needs eyes:", line)
    print(f"\n{len(edits)} span(s) can be assigned unambiguously; "
          f"{len(report)} need(s) a human.")

    if not edits:
        return 1 if report else 0
    if a.dry:
        print("(--dry: nothing written)")
        return 0

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(apply_edits(html, edits))
    print(f"wrote {os.path.relpath(path, book().root)}")
    return 0

