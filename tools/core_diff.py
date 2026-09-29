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


def _pinned_texts(commit, rels):
    """{rel: bytes at the pin, or None if absent}, from one `git cat-file
    --batch` rather than a `git show` process per file."""
    want = "".join(f"{commit}:biblecore/{rel}\n" for rel in rels).encode()
    r = subprocess.run(["git", "cat-file", "--batch"], cwd=CORE, input=want,
                       capture_output=True)
    data, pos, out = r.stdout, 0, {}
    for rel in rels:
        end = data.index(b"\n", pos)
        header = data[pos:end].split()
        pos = end + 1
        if header[-1] == b"missing":
            out[rel] = None
            continue
        size = int(header[2])
        out[rel] = data[pos:pos + size]
        pos += size + 1
    return out


# vendored file types: code, plus the components' css/json/md and web/ assets
EXTS = (".py", ".css", ".json", ".md", ".js", ".svg")


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
    pinned = {p[len("biblecore/"):] for p in listed.stdout.split() if p.endswith(EXTS)}
    have = set()
    for d, dirs, files in os.walk(dst):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(EXTS):
                have.add(os.path.relpath(os.path.join(d, f), dst).replace(os.sep, "/"))
    out = []
    shared = sorted(have & pinned)
    texts = _pinned_texts(commit, shared)
    for rel in shared:
        with open(os.path.join(dst, rel), "rb") as fh:
            mine = fh.read().replace(b"\r\n", b"\n")
        theirs = (texts[rel] or b"").replace(b"\r\n", b"\n")
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
