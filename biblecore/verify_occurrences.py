"""Independently re-derive occurrence counts against data/occurrences.json.

    python -m biblecore verify-occurrences

A line-oriented tokeniser, deliberately different from scan.py's regex, so
a bug in one approach can't hide in both. Also checks each thread's
`tagged` flag against the fragments. (Colour resolution is meta.py's job,
colour distance is validate_units.py's.)

Exit non-zero on any failure.
"""

import glob
import json
import os

from biblecore.book import book


def load(name):
    with open(book().data(name), encoding="utf-8") as fh:
        return json.load(fh)


def recount(html):
    """Token-by-token count, independent of scan_occurrences' regex structure."""
    counts = {}
    for tok in html.replace(">", "> ").split():
        if tok.startswith('data-root="'):
            r = tok.split('"')[1]
            counts[r] = counts.get(r, 0) + 1
    return counts


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def check():
    """Every failure found, as messages ([] == clean)."""
    fail = []
    units_dir = book().path("units")
    occ = load("occurrences.json")
    threads_json = load("threads.json")

    for path in sorted(glob.glob(os.path.join(units_dir, "unit-*.html"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        mine = recount(_read(path))
        theirs = {r: v["total"] for r, v in occ.get(slug, {}).items()}
        if mine != theirs:
            fail.append(f"{slug}: count mismatch\n   verify={mine}\n   json  ={theirs}")

    # thread tagged-flag sanity
    all_roots = set()
    for path in glob.glob(os.path.join(units_dir, "unit-*.html")):
        all_roots |= set(recount(_read(path)))
    for t in threads_json.get("threads", []):
        present = t["root"] in all_roots
        if t.get("tagged") and not present:
            fail.append(f"thread '{t['id']}' tagged:true but root '{t['root']}' "
                       f"not in any fragment")
        if not t.get("tagged") and present:
            fail.append(f"thread '{t['id']}' tagged:false but root '{t['root']}' "
                       f"IS in a fragment -- flip the flag")
    return fail


def main(argv=None):
    fail = check()
    if fail:
        print("FAIL")
        for f in fail:
            print(" -", f)
        return 1
    print("occurrences verified -- counts match, tagged flags consistent")
    return 0

