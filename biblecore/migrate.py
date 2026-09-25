"""Move built units forward to a newer contract (review D7).

    python -m biblecore migrate [--to X.Y.Z] [--dry] [--unit N]

A unit validates against the checks of the core version it was ported
under (contract.py). To hold it to newer rules, run the migrations between
its stamp and the target. Each one is idempotent and says what it changed.
The runner then moves the unit's stamp in units.json, and the build's
refresh step carries it into the meta block.

A migration is (version, name, fn). fn(html, row) returns (new_html,
notes). It gets the fragment and the unit's units.json row, and can edit
the row in place. Add new ones to MIGRATIONS in version order, alongside
any check they prepare units for (meta.FRAGMENT_CHECKS).

Nothing here runs on its own. Shipped units are never regenerated into a
new shape without this explicit step (ARCHITECTURE.md §5).
"""
import argparse
import json

from biblecore import contract
from biblecore import meta as um
from biblecore.book import book


def _stamp_only(html, row):
    """0.3.0: stamps the contract and changes no content. Units ported before
    0.3.0 already meet every 0.3.0 check."""
    return html, []


MIGRATIONS = [
    ("0.3.0", "stamp contract", _stamp_only),
]


def pending(from_v, to_v):
    return [m for m in MIGRATIONS
            if contract.parse(from_v) < contract.parse(m[0]) <= contract.parse(to_v)]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m biblecore migrate")
    ap.add_argument("--to", default=contract.current())
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--unit", type=int)
    a = ap.parse_args(argv or [])
    target = a.to
    if contract.check_stamp(target):
        print(contract.check_stamp(target)[0])
        return 2

    uj = um._load("units.json")
    moved = 0
    for row in uj["units"]:
        if not row.get("built") or (a.unit and row["n"] != a.unit):
            continue
        have = contract.of(row)
        steps = pending(have, target)
        if contract.parse(have) >= contract.parse(target):
            print(f"unit-{row['n']:02d}: at {have}, nothing to do")
            continue
        path = book().unit_path(row["n"])
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        new = html
        print(f"unit-{row['n']:02d}: {have} -> {target}")
        for ver, name, fn in steps:
            new, notes = fn(new, row)
            print(f"  {ver} {name}: " + ("; ".join(notes) if notes else "no content change"))
        row["contract"] = target
        moved += 1
        if not a.dry and new != html:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)

    if moved and not a.dry:
        with open(book().data("units.json"), "w", encoding="utf-8") as fh:
            json.dump(uj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        from biblecore import refresh
        refresh.main([])
    print(f"migrate: {moved} unit(s) {'would move' if a.dry else 'moved'} to {target}")
    if moved and not a.dry:
        print("run `python -m biblecore build` and commit")
    return 0
