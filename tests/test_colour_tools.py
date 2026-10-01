"""The per-book colour spacing (checks.colour_de_min), tools/make_well.py and
tools/recolour.py: a book that outgrows the default well can lower the
spacing, generate a bigger well, and recolour what it shipped."""
import json
import os
import sys

import support
from biblecore import book as bookmod
from biblecore import colour

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import make_well  # noqa: E402
import recolour  # noqa: E402

MIN = {"book": "Matthew", "osis": "Matt", "slug": "matthew", "language": "greek",
       "corpus": {"kind": "morphgnt", "pin": "morphgnt/sblgnt@aaed91e", "word_ids": True}}


def test_colour_de_min_is_a_checked_book_setting():
    fails = []
    ok = bookmod.validate_config(dict(MIN, checks={"colour_de_min": 7}))
    if ok:
        fails.append(f"7 rejected: {ok}")
    for bad in ("tight", 25, 1, True):
        if not bookmod.validate_config(dict(MIN, checks={"colour_de_min": bad})):
            fails.append(f"{bad!r} accepted")
    b = bookmod.Book(dict(MIN, checks={"colour_de_min": 7}), "/tmp/x")
    if b.check("colour_de_min") != 7 or bookmod.Book(MIN, "/tmp/x").check("colour_de_min") != 10:
        fails.append("setting or default not read")
    bookmod.use(b)
    try:
        if colour.de_min() != 7:
            fails.append(f"colour.de_min() = {colour.de_min()}")
    finally:
        support.joshua_book()
    return fails


def test_make_well_spaces_every_pair_and_is_deterministic():
    kw = dict(de=14, bg="#f1ead9", min_contrast=3.0, step=48)
    a, b = make_well.build_well(**kw), make_well.build_well(**kw)
    fails = []
    if a != b:
        fails.append("two runs differ")
    if len(a) < 10:
        fails.append(f"only {len(a)} colours")
    if make_well.min_pairwise(a) < 14:
        fails.append(f"closest pair {make_well.min_pairwise(a):.1f} under 14")
    bad = [c for c in a if not make_well.usable(c, "#f1ead9", 3.0)]
    if bad:
        fails.append(f"unusable colours in the well: {bad[:3]}")
    starter = [c for c in make_well.starter() if make_well.usable(c, "#f1ead9", 3.0)]
    if a[0] != starter[0]:
        fails.append("the starter well's first colour should lead")
    lower = make_well.build_well(de=10, bg="#f1ead9", min_contrast=3.0, step=48)
    if len(lower) > len(make_well.build_well(de=7, bg="#f1ead9", min_contrast=3.0, step=48)):
        fails.append("a tighter floor gave a smaller well")
    return fails


def test_recolour_keeps_threads_distinct_and_locals_clear_of_the_unit():
    well = make_well.build_well(de=14, bg="#f1ead9", min_contrast=3.0, step=48)
    threads = {"threads": [
        {"id": "a", "root": "a", "color": "#000001", "opens": {"unit": 2, "ref": "2:1"}},
        {"id": "b", "root": "b", "color": "#000001", "opens": {"unit": 1, "ref": "1:1"}},
        {"id": "c", "root": "c", "color": "#000002", "opens": {"unit": 1, "ref": "1:2"}}]}
    units = {"units": [
        {"n": 1, "slug": "unit-01", "built": True,
         "roots": {"b": {"color": "#111111"}, "loc": {"color": "#222222"}}},
        {"n": 2, "slug": "unit-02", "built": True, "roots": {"a": {"color": "#333333"}}},
        {"n": 3, "slug": "unit-03", "built": False}]}
    frags = {1: '<span data-root="b">x</span><span data-root="c">y</span><span data-root="loc">z</span>',
             2: '<span data-root="a">q</span>'}
    before = json.dumps([threads, units], sort_keys=True)
    t2, u2 = recolour.recolour(threads, units, frags, well)
    fails = []
    if json.dumps([threads, units], sort_keys=True) != before:
        fails.append("inputs were modified")
    cols = {t["root"]: t["color"] for t in t2["threads"]}
    if len(set(cols.values())) != 3:
        fails.append(f"threads share a colour: {cols}")
    if cols["b"] != well[0]:
        fails.append("the first thread to open didn't take the well's first colour")
    r1 = u2["units"][0]["roots"]
    if r1["b"]["color"] != cols["b"]:
        fails.append("a tracked root's fallback copy wasn't set to the thread's colour")
    unit1 = [cols["b"], cols["c"], r1["loc"]["color"]]
    if min(colour.ciede2000(x, y) for i, x in enumerate(unit1) for y in unit1[i + 1:]) < 14:
        fails.append(f"unit 1's colours are closer than the floor: {unit1}")
    if "roots" in u2["units"][2]:
        fails.append("an unbuilt unit gained roots")
    return fails
