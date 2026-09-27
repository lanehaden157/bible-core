"""The core, run read-only against Joshua's real data, agrees with what
Joshua has committed. Joshua was the reference implementation and has run on
the core itself since 2026-09-26, so the comparison against Joshua's own
audit script is gone; these still catch a core change that would alter a
shipped book's output."""
import glob
import json
import os
import re

import support
from biblecore import meta, roots, scan

UNITS = os.path.join(support.JOSHUA, "units")


def setup():
    support.joshua_book()


def _units():
    return sorted(glob.glob(os.path.join(UNITS, "unit-*.html")))


def test_every_built_unit_validates_clean():
    tj = meta._load("threads.json")
    fails = []
    for path in _units():
        html = support.read(path)
        m = meta.parse(html)
        errs = meta.validate(m, tj) + meta.validate_fragment(html, meta=m, threads_json=tj)
        fails += [f"{os.path.basename(path)}: {e}" for e in errs]
    return fails


def test_generate_reproduces_every_committed_meta_block():
    """refresh is idempotent on Joshua: the core's generate() rebuilds each
    unit's meta block exactly as Joshua's committed fragment carries it."""
    uj, tj = meta._load("units.json"), meta._load("threads.json")
    fails = []
    for path in _units():
        html = support.read(path)
        n = int(re.search(r"unit-(\d+)", path).group(1))
        if meta.inject(html, meta.generate(n, uj, tj)) != html:
            fails.append(f"unit {n}: regenerated meta block differs from committed")
    return fails


def test_scan_matches_committed_occurrences_json():
    committed = json.load(open(os.path.join(support.JOSHUA, "data", "occurrences.json"),
                               encoding="utf-8"))
    ours = {os.path.splitext(os.path.basename(p))[0]: scan.scan_unit(support.read(p))
            for p in _units()}
    return [] if ours == committed else ["scan output differs from data/occurrences.json"]


def test_roots_json_validates():
    tj = meta._load("threads.json")
    return roots.validate(roots.load_roots(), threads_data=tj)


