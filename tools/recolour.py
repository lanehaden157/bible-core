"""Re-assign every colour in a shipped book from its colour well.

    python tools/recolour.py ../Matthew          # write
    python tools/recolour.py ../Matthew --dry    # report only

For a book that moves onto a larger well (tools/make_well.py) after units have
shipped. Only colours change: no fragment, tag or word is touched.

  1. Tracked threads (data/threads.json), in the order they open, take the
     well's colours in order (colour.assign_hues, no two within de_min()).
  2. Each built unit's local roots (data/units.json) take the first well
     colour at least de_min() from every colour the unit tags (its tracked
     threads, read from the fragment's data-root spans) and its other locals.
  3. A tracked root's entry in a unit's `roots` map is only the fallback if the
     thread is ever demoted (units.json's _note); it is set to the thread's
     new colour so no stale colour is left behind.

Prints the closest pair per unit before and after. Writes through json.dump
(indent 2, LF) like the porter does, and refuses if a plain round trip of the
files wouldn't reproduce them byte for byte (so a diff is only colours).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
sys.path.insert(0, CORE)

from biblecore import book as bookmod  # noqa: E402
from biblecore.colour import assign_hues, closest_pairs, de_min  # noqa: E402
from biblecore.validate_units import unit_colours  # noqa: E402


def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def tagged_roots(html):
    html = re.sub(r'<script type="application/json" id="unit-meta">.*?</script>', "", html or "", flags=re.S)
    return set(re.findall(r'data-root="([a-z0-9-]+)"', html))


def recolour(threads_json, units_json, fragments, well):
    """New (threads_json, units_json); inputs are not modified. `fragments` is
    {unit n: html}."""
    import copy
    threads_json, units_json = copy.deepcopy(threads_json), copy.deepcopy(units_json)
    order = sorted(range(len(threads_json["threads"])),
                   key=lambda i: ((threads_json["threads"][i].get("opens") or {}).get("unit") or 999, i))
    names = [threads_json["threads"][i]["root"] for i in order]
    hues = assign_hues(names, [], well)
    for i in order:
        threads_json["threads"][i]["color"] = hues[threads_json["threads"][i]["root"]]
    tracked = {t["root"]: t["color"] for t in threads_json["threads"]}

    for row in units_json["units"]:
        roots = row.get("roots")
        if not row.get("built") or not roots:
            continue
        tagged = tagged_roots(fragments.get(row["n"])) | set(roots)
        taken = [tracked[r] for r in sorted(tagged) if r in tracked]
        local = [r for r in roots if r not in tracked]
        new = assign_hues(local, taken, well)
        for name, entry in roots.items():
            entry["color"] = tracked[name] if name in tracked else new[name]
    return threads_json, units_json


def unit_closest(threads_json, units_json, fragments):
    """{unit n: closest pair's dE2000 among every root the unit tags}."""
    threads = {t["root"]: t for t in threads_json["threads"]}
    out = {}
    for row in units_json["units"]:
        if not row.get("built") or not row.get("roots"):
            continue
        tagged = tagged_roots(fragments.get(row["n"])) | set(row["roots"])
        cols = unit_colours(row["slug"], tagged, threads, units_json)
        pairs = closest_pairs(cols, limit=1)
        if pairs:
            out[row["n"]] = pairs[0][0]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("book", help="the book's folder")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    b = bookmod.use(bookmod.Book.from_file(os.path.join(os.path.abspath(a.book), "book.json")))
    tp, up = b.data("threads.json"), b.data("units.json")
    with open(tp, encoding="utf-8") as fh:
        t_text = fh.read()
    with open(up, encoding="utf-8") as fh:
        u_text = fh.read()
    threads_json, units_json = json.loads(t_text), json.loads(u_text)
    if dump(threads_json) != t_text or dump(units_json) != u_text:
        print("data/threads.json or units.json isn't in json.dump form; a recolour would reformat "
              "it. Normalise it in its own commit first.")
        return 2
    fragments = {}
    for row in units_json["units"]:
        if row.get("built"):
            with open(b.unit_path(row["n"]), encoding="utf-8") as fh:
                fragments[row["n"]] = fh.read()

    well = b.palette()
    new_t, new_u = recolour(threads_json, units_json, fragments, well)
    before = unit_closest(threads_json, units_json, fragments)
    after = unit_closest(new_t, new_u, fragments)
    print(f"well {len(well)} colours, de_min {de_min():g}; {len(new_t['threads'])} threads")
    print("closest pair per unit (dE2000), before -> after:")
    for n in sorted(before):
        print(f"  unit {n:>2}: {before[n]:5.1f} -> {after.get(n, float('nan')):5.1f}")
    hexes = [t["color"] for t in new_t["threads"]]
    assert len(set(hexes)) == len(hexes), "two threads share a colour"
    low = [n for n, d in after.items() if d < de_min()]
    print(f"{len(low)} unit(s) under {de_min():g} after" + (f": {low}" if low else ""))
    if a.dry:
        return 0
    with open(tp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dump(new_t))
    with open(up, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dump(new_u))
    print("wrote data/threads.json and data/units.json; run `python -m biblecore build`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
