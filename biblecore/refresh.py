"""Regenerate the unit-meta block in every built fragment from
data/units.json + data/threads.json, so built units track data changes.
Idempotent; part of the build. New units get their block from the porter.

    python -m biblecore refresh
"""
import glob
import os
import re

from biblecore import meta as um
from biblecore.book import book


def main(argv=None):
    uj = um._load("units.json")
    tj = um._load("threads.json")
    built = {u["n"] for u in uj["units"] if u.get("built")}
    changed = 0
    for path in sorted(glob.glob(os.path.join(book().path("units"), "unit-*.html"))):
        n = int(re.search(r"unit-(\d+)", os.path.basename(path)).group(1))
        if n not in built:
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        new = um.inject(html, um.generate(n, uj, tj))
        if new != html:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1
            print(f"refreshed unit-{n:02d} meta")
    print(f"refresh: {changed} fragment(s) updated")
    return 0
