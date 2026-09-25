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


def test_every_template_sync_file_has_a_role():
    """synced-index.md is the one list of synced files; each file the template
    syncs needs a role there (biblecore/sync.py ROLES), or the index says
    'book file' and the chat side learns nothing. Also: every template sync
    file exists in a fresh book, apart from those the build generates."""
    import json
    import tempfile
    from template_book import make_book
    from biblecore import book as bookmod
    from biblecore import sync
    d = tempfile.mkdtemp(prefix="bc-roles-")
    try:
        make_book(d, "Leviticus", "Lev", "leviticus")
        b = bookmod.Book.from_file(os.path.join(d, "book.json"))
        cfg = json.load(open(os.path.join(d, "book.json"), encoding="utf-8"))
        fails = []
        names = list(cfg["sync"]["files"]) + [
            "canon-leads/canon-leads-unit-01.md", "leviticus-versification.md"]
        for rel in names:
            if not sync.role_for(os.path.basename(rel), b):
                fails.append(f"{rel}: no role in sync.ROLES")
        generated = {"threads-digest.md", "Leviticus-words.tsv", "components-reference.md"}
        for rel in cfg["sync"]["files"]:
            if rel not in generated and not os.path.exists(os.path.join(d, rel)):
                fails.append(f"{rel}: missing from a fresh book")
        text = sync.index_text(b)
        if "resources.md" not in text or "core-workflow.md" not in text:
            fails.append("index misses resources.md or core-workflow.md")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)
        support.joshua_book()
