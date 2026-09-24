"""The core, run read-only against Joshua's real data, agrees with what
Joshua's own pipeline produced. Joshua is the reference implementation;
any disagreement here is a porting bug in the core (or a real Joshua bug
worth knowing about)."""
import glob
import json
import os
import re
import subprocess
import sys

import support
from biblecore import audit, meta, roots, scan

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


_JOSHUA_DUMP = r'''
import json, sys
sys.path.insert(0, ".")
import audit_thread_coverage as a
uj = json.load(open("../data/units.json", encoding="utf-8"))
out = {u["slug"]: a.coverage_for_unit(u["slug"]) for u in uj["units"] if u.get("built")}
for c in out.values():
    c["local"] = {k: [list(x) for x in v] for k, v in c["local"].items()}
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, sort_keys=True))
'''


def test_audit_matches_joshuas_own_audit():
    """Run Joshua's audit (read-only) and the core's on every built unit;
    the structured coverage must be identical."""
    r = subprocess.run([sys.executable, "-c", _JOSHUA_DUMP],
                       cwd=os.path.join(support.JOSHUA, "pipeline"),
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        return [f"Joshua's audit failed to run: {r.stderr[-400:]}"]
    theirs = json.loads(r.stdout)
    uj = meta._load("units.json")
    ours = {}
    for u in uj["units"]:
        if u.get("built"):
            c = audit.coverage_for_unit(u["slug"])
            c["local"] = {k: [list(x) for x in v] for k, v in c["local"].items()}
            ours[u["slug"]] = c
    for slug, c in ours.items():
        if c.pop("covered"):  # a core-only key; Joshua declares no verses
            return [f"{slug}: unexpected covered verses"]
    ours = json.loads(json.dumps(ours, ensure_ascii=False, sort_keys=True))
    if ours != theirs:
        diffs = [s for s in theirs if ours.get(s) != theirs[s]]
        return [f"coverage differs for {diffs}"]
