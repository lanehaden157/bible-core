"""Vendor bible-core into a book (ARCHITECTURE.md §5).

    python tools/core_sync.py ../Numbers          # copy biblecore/ + the canon files in
    python tools/core_sync.py ../Numbers --check  # say what would change, write nothing
    python tools/core_sync.py --all               # every core book: vendor, build, test, commit
    python tools/core_sync.py --all --check       # what --all would do, write nothing

Copies this checkout's `biblecore/` package into `<book>/biblecore/` and
the shared chat-side files in CANON_FILES into the book root, writes
`<book>/biblecore/CORE_VERSION` (the package version plus the bible-core
commit it came from, so core_diff.py can compare against exactly that), and
sets book.json "core" to the package version.

Refuses when the book's copy has local edits (core_diff.py lists them):
move the change into bible-core, or into a book-local override, first.
Also refuses when this checkout has uncommitted changes to biblecore/ or
canon/, since the recorded commit wouldn't describe what was copied.

`--all` is the second half of a release (after tools/release.py). For every
`kind: core` book in canon/books.json whose `repo` folder sits next to
bible-core, it vendors, sets book.json "core", runs the book's `build` and
`biblecore test`, then stages the files that changed (explicit paths, never
`git add -A`) and commits them. A book whose working tree is dirty is
skipped and named, since that is usually another session's work. It never
pushes; it prints the push commands.

Not a submodule, on purpose (review H2): a plain copy with a version file
survives OneDrive and Windows tooling.
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
BOOKS_JSON = os.path.join(CORE, "canon", "books.json")

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
            if f.endswith((".py", ".css", ".json", ".md", ".js", ".svg", ".html")):
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


def set_book_core(book_root, version=None):
    """Write the package version into book.json "core" (structural audit F4:
    biblecore/__init__.py is the one source). Only that line changes, so a
    book's own formatting survives; a book.json without the key gets it
    added. Returns True when the file changed."""
    if version is None:
        from biblecore import __version__ as version
    p = os.path.join(book_root, "book.json")
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    new, n = re.subn(r'^(\s*"core"\s*:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{version}"',
                     text, count=1, flags=re.M)
    if not n:
        cfg = json.loads(text)
        cfg["core"] = version
        new = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
    if new == text:
        return False
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    return True


def vendor(book_root, check=False, allow_dirty=False):
    """Vendor into one book. 0 on success (or nothing to do), 1 refused."""
    from core_diff import local_edits  # noqa: E402  (same folder)
    edits = local_edits(book_root)
    if edits:
        print("the book's biblecore/ has local edits -- move them into bible-core "
              "or a book-local override first:")
        for e in edits:
            print("  ", e)
        return 1
    dirty = core_dirty()
    if dirty and not allow_dirty:
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
    if check:
        return 0
    if acts:
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
    if set_book_core(book_root):
        print("book.json \"core\" updated")
    return 0


# ---- --all -----------------------------------------------------------------

def core_books(path=BOOKS_JSON):
    """(name, folder) for every `kind: core` book with a repo folder."""
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)["books"]
    return [(r["name"], os.path.join(os.path.dirname(CORE), r["repo"]))
            for r in rows if r.get("kind") == "core" and r.get("repo")]


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def changed_paths(root):
    """Every path `git status` reports (untracked files one by one); for a
    rename, the new path."""
    r = git(["status", "--porcelain", "-z", "--untracked-files=all"], root)
    if r.returncode:
        raise RuntimeError(f"git status failed in {root}: {r.stderr.strip()}")
    parts, out, i = r.stdout.split("\0"), [], 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.append(entry[3:])
        if entry[0] in "RC":  # -z puts the rename's source path next
            i += 1
    return out


def run_biblecore(root, args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("BIBLECORE_BOOK", None)
    return subprocess.run([sys.executable, "-m", "biblecore"] + args, cwd=root, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _tail(r, n=8):
    return [ln for ln in (r.stdout + r.stderr).strip().splitlines()[-n:]]


def sync_book(name, root, check=False, trailers=()):
    """Vendor, build, test and commit one book. Returns (status, detail)."""
    from core_diff import local_edits
    from biblecore import __version__
    if not os.path.exists(os.path.join(root, "book.json")):
        return "skipped", f"no book.json at {root}"
    dirty = changed_paths(root)
    if dirty:
        more = f" (+{len(dirty) - 3} more)" if len(dirty) > 3 else ""
        return "skipped", f"working tree dirty, likely another session: {', '.join(dirty[:3])}{more}"
    if local_edits(root):
        return "skipped", "its biblecore/ has local edits (tools/core_diff.py lists them)"

    if check:
        acts = plan(root)
        pinned = json.load(open(os.path.join(root, "book.json"), encoding="utf-8")).get("core")
        if not acts and pinned == __version__:
            return "current", f"already on {__version__}"
        return "would sync", (f"{len(acts)} vendored file(s) differ; book.json core "
                              f"{pinned} -> {__version__}; then build, test, commit")

    if vendor(root):
        return "failed", "vendor refused (see above)"
    r = run_biblecore(root, ["build"])
    if r.returncode:
        for ln in _tail(r):
            print("    ", ln)
        return "failed", "build failed; the vendored files are left uncommitted to inspect"
    r = run_biblecore(root, ["test"])
    if r.returncode:
        for ln in _tail(r, 15):
            print("    ", ln)
        return "failed", "biblecore test failed; the changes are left uncommitted to inspect"

    paths = changed_paths(root)
    if not paths:
        return "current", f"already on {__version__}; nothing changed"
    print("   staging:")
    for p in paths:
        print(f"     {p}")
    for i in range(0, len(paths), 100):
        r = git(["add", "--"] + paths[i:i + 100], root)
        if r.returncode:
            return "failed", f"git add: {r.stderr.strip()}"
    commit = (core_commit() or "unknown")[:7]
    msg = (f"Core {__version__}: vendor bible-core {commit}, rebuild\n\n"
           f"By tools/core_sync.py --all: vendored biblecore/ and the canon files, set\n"
           f"book.json core, ran build and biblecore test (both passed).\n")
    cmd = ["commit", "-q", "-m", msg] + [x for t in trailers for x in ("--trailer", t)]
    r = git(cmd, root)
    if r.returncode:
        return "failed", f"git commit: {(r.stderr or r.stdout).strip()}"
    sha = git(["rev-parse", "--short", "HEAD"], root).stdout.strip()
    detail = f"{sha}, {len(paths)} file(s)"
    sc = run_biblecore(root, ["sync-check"])
    if "NEEDS RE-SYNCING" in sc.stdout or "NO LONGER SYNCED" in sc.stdout:
        detail += "; chat-side files changed -> `python -m biblecore sync` after pushing"
    return "committed", detail


def sync_all(check=False, trailers=()):
    from biblecore import __version__
    dirty = core_dirty()
    if dirty:
        print("bible-core has uncommitted changes under biblecore/ or canon/; "
              "commit (or release) first:")
        for ln in dirty:
            print("  ", ln)
        return 1
    commit = (core_commit() or "unknown")[:7]
    print(f"bible-core {__version__} ({commit})" + ("  [check only]" if check else ""))
    results = []
    for name, root in core_books():
        print(f"\n== {name} ({root})")
        if not os.path.isdir(root):
            status, detail = "skipped", "not found next to bible-core"
        else:
            status, detail = sync_book(name, root, check, trailers)
        print(f"   {status}: {detail}")
        results.append((name, root, status, detail))

    print("\nsummary")
    for name, _root, status, detail in results:
        print(f"  {name:12} {status:10} {detail}")
    pushed = [(n, r) for n, r, s, _ in results if s == "committed"]
    if pushed:
        print("\nnothing was pushed. When ready:")
        for _n, r in pushed:
            print(f"  git -C {os.path.relpath(r)} push")
    return 1 if any(s == "failed" for *_x, s, _d in results) else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?")
    ap.add_argument("--all", action="store_true",
                    help="every kind:core book in canon/books.json: vendor, build, test, commit")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="vendor even with uncommitted core changes (testing only; not with --all)")
    ap.add_argument("--trailer", action="append", default=[],
                    help="with --all: a trailer line for each book's commit (repeatable)")
    a = ap.parse_args(argv)
    if a.all:
        if a.book or a.allow_dirty:
            ap.error("--all takes no book folder and no --allow-dirty")
        return sync_all(a.check, a.trailer)
    if not a.book:
        ap.error("name a book folder, or pass --all")
    book_root = os.path.abspath(a.book)
    if not os.path.exists(os.path.join(book_root, "book.json")):
        print(f"{book_root} has no book.json")
        return 2
    rc = vendor(book_root, a.check, a.allow_dirty)
    if rc == 0 and not a.check:
        print("next: the book's build, `python -m biblecore test`, commit explicit paths.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
