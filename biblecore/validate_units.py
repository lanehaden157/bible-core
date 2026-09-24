"""Hard-gate every built fragment in units/ against the contract.

    python -m biblecore validate

Re-validates what is actually on disk, as a build step that fails:
anything that touches a fragment after the port (retrofit edits, a
regenerated meta block, a hand edit) could otherwise push a shipped unit
out of contract unnoticed. (learned: Joshua A1, a regenerated meta block
failed the project's own validator on every build, silently.)

Colour distance is checked too, as a warning: two roots in one unit closer
than DE_MIN read as one colour.
"""
import glob
import os
import re
import sys

from biblecore import meta as um
from biblecore.book import book
from biblecore.colour import DE_MIN, closest_pairs

def unit_colours(slug, roots, threads, units_json):
    """root -> hex for every root tagged in this unit, tracked or local.

    Mirrors app/threads.js resolveUnit(): a tracked thread's colour comes
    from threads.json and wins; a local root's from units.json.
    """
    row = next((u for u in units_json["units"] if u.get("slug") == slug), None)
    local = (row or {}).get("roots") or {}
    out = {}
    for r in sorted(roots):
        if r in threads:
            c = threads[r].get("color")
        else:
            e = local.get(r)
            c = e.get("color") if isinstance(e, dict) else e
        if c:
            out[r] = c
    return out


def check_colours(slug, colours):
    """Warn on same-unit pairs under DE_MIN, and show the ranked ceiling."""
    out = []
    pairs = closest_pairs(colours, limit=3)
    for d, ra, ca, rb, cb in pairs:
        if d < DE_MIN:
            out.append(f"colours close: '{ra}' ({ca}) / '{rb}' ({cb}) "
                       f"dE2000={d:.1f}, under {DE_MIN}")
    if pairs:
        ranked = ", ".join(f"{ra}/{rb} {d:.1f}" for d, ra, _, rb, _ in pairs)
        out.append(f"closest pairs in this unit (dE2000): {ranked}")
    return out


def check_thread_hexes_unique(threads):
    """No two tracked threads may share a hex, book-wide.

    Matthew has three sets of threads sharing a colour (review B2); a
    shared hex means two different threads look like one wherever they
    meet, in any unit. Cheap to assert, so assert it.
    """
    out, by_hex = [], {}
    for root, t in sorted(threads.items()):
        c = (t.get("color") or "").lower()
        if c:
            by_hex.setdefault(c, []).append(t.get("id", root))
    for c, ids in sorted(by_hex.items()):
        if len(ids) > 1:
            out.append(f"threads {', '.join(repr(i) for i in ids)} all use "
                       f"{c} -- two threads that look like one")
    return out


def roots_in_fragment(html):
    """Every distinct data-root slug tagged in the fragment."""
    import re
    return set(re.findall(r'data-root="([a-z0-9-]+)"', html or ""))


def main(argv=None):
    threads_json = um._load("threads.json")
    units_json = um._load("units.json")
    threads = {t["root"]: t for t in threads_json["threads"]}

    book_warns = check_thread_hexes_unique(threads)
    for w in book_warns:
        print("  warn  (book-wide)", w)

    paths = sorted(glob.glob(os.path.join(book().path("units"), "unit-*.html")))
    if not paths:
        print("no built units to validate")
        return 0

    total_err, total_warn = 0, len(book_warns)
    for path in paths:
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        meta = um.parse(html)

        errs = []
        if meta is None:
            errs.append("no meta block (unit_meta.parse returned None)")
        else:
            errs += [f"meta: {e}" for e in um.validate(meta, threads_json)]
            errs += um.validate_fragment(html, meta=meta,
                                         threads_json=threads_json)
        warns = um.warnings_for_fragment(html)
        if meta is not None:
            # Colour distance is a tunable aesthetic judgement, not a
            # contract breach, so it warns rather than failing the build.
            # It still gets said out loud on every build, which is the
            # backstop that was missing (review A4).
            slug = meta.get("slug") or name[:-5]
            warns += check_colours(
                slug, unit_colours(slug, roots_in_fragment(html),
                                   threads, units_json))
        total_err += len(errs)
        total_warn += len(warns)

        status = "FAIL" if errs else ("warn" if warns else "ok")
        print(f"{name}: {status}")
        for e in errs:
            print("  ERROR", e)
        for w in warns:
            print("  warn ", w)
        # The usual cause is a thread promoted after the port: its spans
        # predate tracking. Fill them in place; a --force re-port also
        # works but replaces the whole fragment with the source artifact.
        if any("with no data-w attribute" in e for e in errs):
            m = re.search(r"unit-(\d+)", name)
            if m:
                print(f"  -> fill in place: python -m biblecore data-w "
                      f"{int(m.group(1))}   (no re-port needed)")

    print(f"\n{len(paths)} unit(s): {total_err} error(s), "
          f"{total_warn} warning(s)")
    return 1 if total_err else 0

