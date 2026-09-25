"""Check this book against the core it vendors (review D9).

    python -m biblecore test            # everything
    python -m biblecore test --quick    # skip the build-idempotence run

The core's own unit tests live in bible-core (tests/run.py), since they
need Joshua's data as a fixture. This is the book-side half, the
acceptance checks a book can run on itself:

  pin          book.json "core", CORE_VERSION and the package agree
  corpus       the word table and reading text load
  data         roots.json validates; every data/*.json parses
  units        every built unit validates (validate step)
  contracts    every built unit carries a contract stamp no newer than core
  example      the style reference's worked example (section 8) validates, if it has one
  audit        tracked-thread coverage (reported, not a failure)
  idempotent   re-running the build's hard steps changes no file; anything
               it would change is reported and put back

Exit 1 if any check fails.
"""
import contextlib
import glob
import io
import json
import os
import re

from biblecore import __version__, contract
from biblecore.book import book

FENCE_RE = re.compile(r"```html\n(.*?)```", re.S)


def _quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def check_pin():
    b = book()
    errs = []
    pinned = b.cfg.get("core")
    if pinned != __version__:
        errs.append(f"book.json pins core {pinned!r}, vendored package is {__version__}")
    vf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CORE_VERSION")
    if os.path.exists(vf):
        first = open(vf, encoding="utf-8").read().split()[:1]
        if first != [__version__]:
            errs.append(f"CORE_VERSION says {first}, package says {__version__}")
        if "+dirty" in open(vf, encoding="utf-8").read():
            errs.append("CORE_VERSION is marked +dirty (vendored from uncommitted core)")
    else:
        errs.append("biblecore/CORE_VERSION missing (vendor with tools/core_sync.py)")
    return errs, []


def check_corpus():
    from biblecore import corpus
    ad = corpus.adapter()
    words = ad.load_words(book())
    reading = ad.load_reading(book())
    if not words or not reading:
        return ["word table or reading text is empty"], []
    return [], [f"{len(reading)} verses, {len(words)} words"]


def check_data():
    errs = []
    for p in sorted(glob.glob(os.path.join(book().path("data"), "*.json"))):
        try:
            json.load(open(p, encoding="utf-8"))
        except Exception as exc:
            errs.append(f"{os.path.basename(p)} doesn't parse: {exc}")
    from biblecore import roots
    rc, out = _quiet(roots.main, [])
    if rc:
        errs.append("roots.json fails validation:\n" + out.strip())
    return errs, []


def check_units():
    from biblecore import validate_units
    rc, out = _quiet(validate_units.main, [])
    if rc:
        return [ln.strip() for ln in out.splitlines() if "ERROR" in ln or "FAIL" in ln], []
    last = out.strip().splitlines()[-1] if out.strip() else ""
    return [], [last]


def check_contracts():
    from biblecore import meta as um
    errs, notes = [], []
    for row in um._load("units.json")["units"]:
        if not row.get("built"):
            continue
        c = row.get("contract")
        if c is None:
            notes.append(f"unit-{row['n']:02d} unstamped (counts as {contract.UNSTAMPED}; "
                         f"`python -m biblecore migrate` stamps it)")
        else:
            errs += [f"unit-{row['n']:02d}: {e}" for e in contract.check_stamp(c)]
    return errs, notes


def check_example():
    from biblecore import meta as um
    path = book().path("style_reference")
    if not os.path.exists(path):
        return [], ["no style reference"]
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^## 8\..*?(?=^## \d)", text, re.S | re.M)
    fence = FENCE_RE.search(m.group(0)) if m else None
    if not fence:
        return [], ["section 8 has no ```html worked example yet"]
    meta = um.parse(fence.group(1))
    if meta is None:
        return ["worked example has no unit-meta block"], []
    # threads/roots in an example needn't exist in this book's registries,
    # so only the self-contained checks apply
    errs = [e for e in um.validate(meta) if "data/threads.json" not in e]
    errs += um.check_endnote_integrity(fence.group(1))
    errs += um.check_no_native_script(fence.group(1))
    errs += um.check_no_inline_style(fence.group(1))
    return [f"example: {e}" for e in errs], []


def check_audit():
    from biblecore import audit
    rc_out = io.StringIO()
    with contextlib.redirect_stdout(rc_out):
        problems = audit.audit()
    n = len(problems) if problems else 0
    return [], [f"{n} coverage issue(s)" + (" (run `python -m biblecore audit`)" if n else "")]


def _snapshot():
    b = book()
    paths = glob.glob(os.path.join(b.path("data"), "*.json"))
    paths += glob.glob(os.path.join(b.path("units"), "unit-*.html"))
    paths += [b.path("digest")]
    snap = {}
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as fh:
                snap[p] = fh.read()
    return snap


def check_idempotent():
    from biblecore import build
    before = _snapshot()
    failed_at = None
    try:
        for name, fn in build.STEPS:
            rc, _ = _quiet(fn, [])
            if rc:
                failed_at = name
                break
        after = _snapshot()
    finally:
        now = _snapshot()
        for p, data in before.items():
            if now.get(p) != data:
                with open(p, "wb") as fh:
                    fh.write(data)
        for p in set(now) - set(before):
            os.remove(p)
    if failed_at:
        return [f"build failed at {failed_at} (run `python -m biblecore build`)"], []
    changed = sorted(os.path.relpath(p, book().root) for p in set(before) | set(after)
                     if before.get(p) != after.get(p))
    if changed:
        return [f"the build would change {len(changed)} file(s): {', '.join(changed)} -- "
                f"run `python -m biblecore build` and commit (restored for now)"], []
    return [], []


CHECKS = [
    ("pin", check_pin),
    ("corpus", check_corpus),
    ("data", check_data),
    ("units", check_units),
    ("contracts", check_contracts),
    ("example", check_example),
    ("audit", check_audit),
    ("idempotent", check_idempotent),
]


def main(argv=None):
    args = list(argv or [])
    failed = 0
    for name, fn in CHECKS:
        if name == "idempotent" and "--quick" in args:
            continue
        try:
            errs, notes = fn()
        except Exception as exc:
            errs, notes = [f"{type(exc).__name__}: {exc}"], []
        mark = "FAIL" if errs else "ok"
        print(f"{mark:4}  {name}" + (f"  ({'; '.join(notes)})" if notes and not errs else ""))
        for e in errs:
            print(f"      {e}")
        failed += bool(errs)
    print(f"\n{book().name}: {len(CHECKS) - failed} ok, {failed} failed")
    return 1 if failed else 0
