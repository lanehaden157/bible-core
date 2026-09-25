"""Vendor bible-core into a book (ARCHITECTURE.md §5).

    python tools/core_sync.py ../Numbers          # copy biblecore/ + the canon files in
    python tools/core_sync.py ../Numbers --check  # say what would change, write nothing

Copies this checkout's `biblecore/` package into `<book>/biblecore/` and
the shared chat-side files in CANON_FILES into the book root, then writes
`<book>/biblecore/CORE_VERSION`: the package version plus the bible-core
commit it came from, so core_diff.py can compare against exactly that.

Refuses when the book's copy has local edits (core_diff.py lists them):
move the change into bible-core, or into a book-local override, first.
Also refuses when this checkout has uncommitted changes to biblecore/ or
canon/, since the recorded commit wouldn't describe what was copied.

Not a submodule, on purpose (review H2): a plain copy with a version file
survives OneDrive and Windows tooling.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)

# bible-core canon/ file -> its name in the book root (all synced to the
# project side; the book never edits them)
CANON_FILES = {
    "conventions.md": "canon-conventions.md",
    "decisions.md": "canon-decisions.md",
    "workflow.md": "core-workflow.md",
}


def copy_canon_files(book_root):
    for src, dst in CANON_FILES.items():
        shutil.copyfile(os.path.join(CORE, "canon", src), os.path.join(book_root, dst))


def core_commit():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=CORE, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def core_dirty():
    r = subprocess.run(["git", "status", "--porcelain", "--", "biblecore", "canon"],
                       cwd=CORE, capture_output=True, text=True)
    return [ln for ln in r.stdout.splitlines() if "__pycache__" not in ln]


def package_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith((".py", ".css", ".json", ".md", ".js")):
                out.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    return sorted(out)


def plan(book_root):
    """[(action, rel_path)] to bring the book's copy to this checkout."""
    src, dst = os.path.join(CORE, "biblecore"), os.path.join(book_root, "biblecore")
    have = set(package_files(dst)) if os.path.isdir(dst) else set()
    want = set(package_files(src))
    acts = []
    for rel in sorted(want):
        if rel not in have:
            acts.append(("add", rel))
        elif not filecmp.cmp(os.path.join(src, rel), os.path.join(dst, rel), shallow=False):
            acts.append(("update", rel))
    for rel in sorted(have - want):
        acts.append(("remove", rel))
    for src, dst in CANON_FILES.items():
        s, d = os.path.join(CORE, "canon", src), os.path.join(book_root, dst)
        if not os.path.exists(d) or not filecmp.cmp(s, d, shallow=False):
            acts.append(("update" if os.path.exists(d) else "add", f"../{dst}"))
    return acts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="vendor even with uncommitted core changes (testing only)")
    a = ap.parse_args(argv)
    book_root = os.path.abspath(a.book)
    if not os.path.exists(os.path.join(book_root, "book.json")):
        print(f"{book_root} has no book.json")
        return 2

    from core_diff import local_edits  # noqa: E402  (same folder)
    edits = local_edits(book_root)
    if edits:
        print("the book's biblecore/ has local edits -- move them into bible-core "
              "or a book-local override first:")
        for e in edits:
            print("  ", e)
        return 1
    dirty = core_dirty()
    if dirty and not a.allow_dirty:
        print("bible-core has uncommitted changes under biblecore/ or canon/; "
              "commit first so CORE_VERSION names what was copied:")
        for ln in dirty:
            print("  ", ln)
        return 1

    acts = plan(book_root)
    for act, rel in acts:
        print(f"  {act:6} {rel}")
    if not acts:
        print("already current")
    if a.check or not acts:
        return 0

    dst = os.path.join(book_root, "biblecore")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(CORE, "biblecore"), dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    copy_canon_files(book_root)
    from biblecore import __version__
    commit = core_commit() or "unknown"
    with open(os.path.join(dst, "CORE_VERSION"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{__version__} {commit}{' +dirty' if dirty else ''}\n")
    print(f"vendored bible-core {__version__} ({commit[:10]}) into {dst}")
    print("update book.json \"core\" if the version changed, run the book's build, commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
