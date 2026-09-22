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
        if not os.path.exists(os.path.join(d, "canon-conventions.md")):
            fails.append("canon-conventions.md not copied")
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
