"""tools/core_sync.py and tools/core_diff.py on a scratch book.

Needs a committed bible-core (CORE_VERSION pins a commit). With uncommitted
changes under biblecore/ or canon/, sync refuses by design, so the round
trip here is skipped rather than failed.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile

import support

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import core_diff  # noqa: E402
import core_sync  # noqa: E402


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = fn(*a)
    return rc, out.getvalue()


def test_vendor_diff_and_refusal_round_trip():
    if core_sync.core_dirty():
        print("    (skipped: bible-core has uncommitted changes)")
        return
    d = tempfile.mkdtemp(prefix="bc-sync-")
    try:
        open(os.path.join(d, "book.json"), "w").write("{}")
        fails = []
        rc, out = _quiet(core_sync.main, [d])
        if rc or not os.path.exists(os.path.join(d, "biblecore", "CORE_VERSION")):
            return [f"vendoring failed: {out}"]
        for f in core_sync.CANON_FILES.values():
            if not os.path.exists(os.path.join(d, f)):
                fails.append(f"{f} not copied")
        pinned = open(os.path.join(d, "biblecore", "CORE_VERSION")).read().split()
        if pinned[1] != core_sync.core_commit():
            fails.append(f"CORE_VERSION pins {pinned[1]}, HEAD is {core_sync.core_commit()}")
        if core_diff.local_edits(d):
            fails.append(f"fresh copy reported as edited: {core_diff.local_edits(d)}")
        _rc, out = _quiet(core_sync.main, [d, "--check"])
        if "already current" not in out:
            fails.append(f"second sync not a no-op: {out}")

        with open(os.path.join(d, "biblecore", "scan.py"), "a", encoding="utf-8") as f:
            f.write("\n# local fix\n")
        open(os.path.join(d, "biblecore", "mine.py"), "w").write("x = 1\n")
        edits = core_diff.local_edits(d)
        if edits != ["modified scan.py", "added mine.py"]:
            fails.append(f"unexpected edit report: {edits}")
        rc, out = _quiet(core_sync.main, [d])
        if rc != 1 or "local edits" not in out:
            fails.append("sync should refuse to overwrite local edits")
        return fails
    finally:
        shutil.rmtree(d)


def test_new_book_registers_the_hub_row():
    """new_book.py fills the book's canon/books.json row (structural audit
    P1), touching only that line; the hub workflow clones from `site`."""
    import json
    import new_book
    d = tempfile.mkdtemp(prefix="bc-books-")
    try:
        path = os.path.join(d, "books.json")
        shutil.copyfile(new_book.BOOKS_JSON, path)
        before = open(path, encoding="utf-8").read().split("\n")
        fails = []
        owner = new_book.pages_owner(path)
        if owner != "lanehaden157":
            fails.append(f"pages_owner: {owner}")
        row = new_book.register_book("Lev", "leviticus", "Leviticus", "LaneHaden157", path)
        want = {"osis": "Lev", "name": "Leviticus", "t": "ot", "slug": "leviticus",
                "site": "https://lanehaden157.github.io/leviticus/",
                "repo": "Leviticus", "kind": "core"}
        if row != want:
            fails.append(f"row: {row}")
        raw = open(path, "rb").read()
        if b"\r\n" in raw:
            fails.append("CRLF written")
        after = raw.decode("utf-8").split("\n")
        changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
        if len(after) != len(before) or len(changed) != 1 or '"Lev"' not in after[changed[0]]:
            fails.append(f"expected only Leviticus's line to change: {changed}")
        if json.loads(raw)["books"][2] != want:
            fails.append("the file doesn't parse to the new row")
        try:
            new_book.register_book("Nope", "x", "X", "o", path)
            fails.append("an unknown osis was accepted")
        except RuntimeError:
            pass
        return fails
    finally:
        shutil.rmtree(d)
