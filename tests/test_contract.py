"""D7 contract versions, migrations, the data manifest (F17), the book-side
self-test (D9) and sync-check's paste tracking (D6), on a scratch copy of
Joshua."""
import contextlib
import io
import json
import os
import shutil

import support
from biblecore import contract, manifest, migrate, selftest
from biblecore import meta as um
from biblecore.book import book

_tmp = None


def setup():
    global _tmp
    _tmp = support.scratch_book()


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def _unit(n):
    return support.read(os.path.join(_tmp, "units", f"unit-{n:02d}.html"))


def test_stamp_validation():
    fails = []
    base = {"unit": 1, "passage": "x", "title": "x", "roots": [],
            "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []}}
    if um.validate(dict(base, contract=contract.current())):
        fails.append(f"current stamp rejected: {um.validate(dict(base, contract=contract.current()))}")
    if not um.validate(dict(base, contract="99.0.0")):
        fails.append("a stamp newer than core was accepted")
    if not um.validate(dict(base, contract="soon")):
        fails.append("a malformed stamp was accepted")
    return fails


def test_new_check_skips_unstamped_units():
    html = _unit(1)
    if um.parse(html).get("contract"):
        return ["Joshua unit 1 unexpectedly carries a stamp"]
    probe = (contract.current(), "probe", lambda h, m, t, c: ["probe fired"])
    um.FRAGMENT_CHECKS.append(probe)
    try:
        old = um.validate_fragment(html, meta=um.parse(html))
        stamped = um.validate_fragment(html, meta=dict(um.parse(html), contract=contract.current()))
    finally:
        um.FRAGMENT_CHECKS.remove(probe)
    fails = []
    if "probe fired" in old:
        fails.append("a check newer than the unit's contract ran on it")
    if "probe fired" not in stamped:
        fails.append("a check at the unit's contract didn't run")
    return fails


def test_migrate_stamps_and_is_idempotent():
    before = {n: _unit(n) for n in (1, 2, 3, 4)}
    _quiet(migrate.main, [])
    fails = []
    rows = {u["n"]: u for u in um._load("units.json")["units"]}
    for n in (1, 2, 3, 4):
        if rows[n].get("contract") != contract.current():
            fails.append(f"unit {n} row not stamped")
        meta = um.parse(_unit(n))
        if meta.get("contract") != contract.current():
            fails.append(f"unit {n} meta not stamped")
        stripped = _unit(n).replace(f'\n  "contract": "{contract.current()}",', "")
        if stripped != before[n]:
            fails.append(f"unit {n} changed beyond the stamp")
    again = io.StringIO()
    with contextlib.redirect_stdout(again):
        migrate.main([])
    if "0 unit(s) moved" not in again.getvalue():
        fails.append("second migrate wasn't a no-op")
    return fails


def test_manifest():
    _quiet(manifest.main, [])
    path = book().data("manifest.json")
    first = support.read(path)
    _quiet(manifest.main, [])
    m = json.loads(first)
    fails = []
    if support.read(path) != first:
        fails.append("manifest isn't deterministic")
    if m["units_built"] != 4 or m["core"] != contract.current():
        fails.append(f"manifest counts/core wrong: {m['units_built']}, {m['core']}")
    if "units.json" not in m["files"]:
        fails.append("manifest lists no units.json")
    return fails


def test_selftest_checks():
    fails = []
    errs, notes = selftest.check_contracts()
    if errs or not any("unstamped" in n for n in notes):
        fails.append(f"contracts: {errs} {notes}")
    errs, _ = selftest.check_units()
    if errs:
        fails.append(f"units: {errs}")
    # a consistent book (built once) changes nothing on a second build
    from biblecore import build
    for _name, fn in build.STEPS:
        _quiet(fn, [])
    errs, _ = selftest.check_idempotent()
    if errs:
        fails.append(f"idempotent: {errs}")
    # a hand edit the build would undo is reported, and put back
    p = book().data("occurrences.json")
    edited = support.read(p).replace("{", "{ ", 1)
    open(p, "w", encoding="utf-8").write(edited)
    errs, _ = selftest.check_idempotent()
    if not errs or "occurrences.json" not in errs[0]:
        fails.append(f"a stale occurrences.json wasn't reported: {errs}")
    if support.read(p) != edited:
        fails.append("check_idempotent didn't restore the file it rebuilt")
    return fails


def test_sync_check_paste_tracking():
    from biblecore import sync
    chat = os.path.join(_tmp, "CHAT_SIDE_INSTRUCTIONS.md")
    open(chat, "w", encoding="utf-8").write("field v1\n")
    os.makedirs(os.path.join(_tmp, "project-side"), exist_ok=True)
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=_tmp, check=True)

    def out():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sync.check_main([])
        return buf.getvalue()
    fails = []
    if "PASTE BY HAND" not in out():
        fails.append("never-pasted field not flagged")
    _quiet(sync.check_main, ["--mark-pasted"])
    if "PASTE BY HAND" in out():
        fails.append("flagged right after --mark-pasted")
    open(chat, "w", encoding="utf-8").write("field v2\n")
    if "PASTE BY HAND" not in out():
        fails.append("changed field not flagged")
    return fails
