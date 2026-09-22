"""Report edits made directly to a book's vendored copy of bible-core.

    python tools/core_diff.py ../Numbers

Compares `<book>/biblecore/` against the bible-core commit recorded in its
CORE_VERSION (via `git show <commit>:biblecore/<file>`), so a book pinned to
an older core isn't reported as "edited" just because core moved on.

This is a report, never a gate (ARCHITECTURE.md §5): it exists so a quick
local fix doesn't silently become a fork. A real divergence belongs in a
book-local module that wraps the core function, or in bible-core itself.
"""
import os
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pinned_commit(book_root):
    path = os.path.join(book_root, "biblecore", "CORE_VERSION")
    if not os.path.exists(path):
        return None
    parts = open(path, encoding="utf-8").read().split()
    return parts[1] if len(parts) > 1 and parts[1] != "unknown" else None


def _pinned_text(commit, rel):
    r = subprocess.run(["git", "show", f"{commit}:biblecore/{rel}"], cwd=CORE,
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def local_edits(book_root):
    """['modified x.py', 'added y.py', 'removed z.py'] against the pin."""
    dst = os.path.join(book_root, "biblecore")
    if not os.path.isdir(dst):
        return []
    commit = _pinned_commit(book_root)
    if commit is None:
        return ["no CORE_VERSION commit recorded -- can't tell edits from core changes"]
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "biblecore"],
                            cwd=CORE, capture_output=True, text=True)
    if listed.returncode:
        return [f"pinned commit {commit[:10]} not found in this bible-core checkout"]
    pinned = {p[len("biblecore/"):] for p in listed.stdout.split() if p.endswith(".py")}
    have = set()
    for d, dirs, files in os.walk(dst):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                have.add(os.path.relpath(os.path.join(d, f), dst).replace(os.sep, "/"))
    out = []
    for rel in sorted(have & pinned):
        with open(os.path.join(dst, rel), "rb") as fh:
            mine = fh.read().replace(b"\r\n", b"\n")
        theirs = (_pinned_text(commit, rel) or b"").replace(b"\r\n", b"\n")
        if mine != theirs:
            out.append(f"modified {rel}")
    out += [f"added {rel}" for rel in sorted(have - pinned)]
    out += [f"removed {rel}" for rel in sorted(pinned - have)]
    return out


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__)
        return 2
    book_root = os.path.abspath(args[0])
    edits = local_edits(book_root)
    if not edits:
        print("biblecore/ matches its pinned bible-core commit")
        return 0
    print("biblecore/ differs from its pinned bible-core commit:")
    for e in edits:
        print("  ", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
