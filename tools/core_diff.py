"""Report edits made directly to a book's vendored copy of bible-core, or
the template changes a book hasn't taken.

    python tools/core_diff.py ../Numbers
    python tools/core_diff.py ../Numbers --template            # template drift, with diffs
    python tools/core_diff.py ../Numbers --template --stat     # one line per file
    python tools/core_diff.py ../Numbers --template --set-base [COMMIT]   # after adopting

Compares `<book>/biblecore/` against the bible-core commit recorded in its
CORE_VERSION (via `git show <commit>:biblecore/<file>`), so a book pinned to
an older core isn't reported as "edited" just because core moved on.

This is a report, never a gate (ARCHITECTURE.md §5): it exists so a quick
local fix doesn't silently become a fork. A real divergence belongs in a
book-local module that wraps the core function, or in bible-core itself.

`--template` (structural audit D3) covers the files the template seeds into
a new book (CLAUDE.md, the style reference, CHAT_SIDE_INSTRUCTIONS.md, ...).
Those become the book's own, so template fixes never reach an existing book
by themselves. The book records the bible-core commit whose template it last
took in book.json "template" (new_book.py fills it). The report lists every
template-seeded file whose template copy changed since then, with the
placeholders filled with the book's values, and shows the template's diff.
Adopting stays optional (forward-only core); `--set-base` moves the base once
you've taken what you want (default: bible-core HEAD). Starter data and logs
(data/, units/, session_index.md, ...) and the generated app shell are left
out.
"""
import os
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # new_book


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
EXTS = (".py", ".css", ".json", ".md", ".js", ".html", ".svg")


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


# ---- --template: what the template changed since the book last took it --

# Seeded once, then the book's own data or record: template changes to
# these starters don't apply to a book that has filled them.
BOOK_OWNED = ("data/", "units/", "canon-leads/", "source-artifacts/", "retrofit/",
              "session_index.md", "improvements_log.md")
# Once in the template, now written by `assets` from biblecore/web/ (0.11.0):
# the plain core_diff above covers them as vendored code.
GENERATED = ("index.html", "app/", "css/core.css", "css/components.css",
             "css/division.css", "css/styles.css")


def _git(args):
    return subprocess.run(["git"] + args, cwd=CORE, capture_output=True)


def _template_files(rev):
    r = _git(["ls-tree", "-r", "--name-only", rev, "--", "template"])
    if r.returncode:
        raise RuntimeError(f"bible-core has no commit {rev}")
    return [p[len("template/"):] for p in r.stdout.decode().split("\n")
            if p.startswith("template/")]


def _show(rev, rel):
    r = _git(["show", f"{rev}:template/{rel}"])
    return r.stdout.decode("utf-8").replace("\r\n", "\n") if r.returncode == 0 else None


def _book_cfg(book_root):
    import json
    with open(os.path.join(book_root, "book.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _subs(cfg):
    from new_book import placeholders
    return placeholders(cfg.get("book", ""), cfg.get("osis", ""), cfg.get("slug", ""),
                        cfg.get("abbrev"), cfg.get("core", ""), cfg.get("template", ""))


def _book_rel(rel, cfg):
    """Where the book keeps the file the template seeds at `rel`."""
    paths = cfg.get("paths") or {}
    if rel == "CHAT_SIDE_INSTRUCTIONS.md" and paths.get("chat_side"):
        return paths["chat_side"]
    if rel.startswith("css/") and paths.get("css") and not paths["css"].endswith(".css"):
        return paths["css"].rstrip("/") + "/" + rel[len("css/"):]
    return rel


def template_drift(book_root, base=None, head="HEAD"):
    """[(state, template_rel, book_rel, base_text, head_text)] for every
    template-seeded file whose template copy changed between the book's
    base and `head`, placeholders filled with the book's values. States:

      take     the book's file still matches the old template: the new
               one can replace it whole
      review   the book has its own edits: apply the template's change by hand
      current  the book already has the new template text
      new      the template added it; the book doesn't have it
      removed  the template dropped it; the book still has it
    """
    from new_book import fill
    cfg = _book_cfg(book_root)
    base = base or cfg.get("template")
    if not base:
        raise RuntimeError("book.json has no \"template\" base; record one with "
                           "--set-base <bible-core commit>")
    subs = _subs(cfg)
    before, after = set(_template_files(base)), set(_template_files(head))
    out = []
    for rel in sorted(before | after):
        if rel.endswith(".gitkeep") or rel.startswith(BOOK_OWNED + GENERATED):
            continue
        old = _show(base, rel) if rel in before else None
        new = _show(head, rel) if rel in after else None
        if old == new:
            continue
        old = fill(old, subs) if old is not None else None
        new = fill(new, subs) if new is not None else None
        brel = _book_rel(fill(rel, subs), cfg)
        p = os.path.join(book_root, brel)
        mine = (open(p, encoding="utf-8").read().replace("\r\n", "\n")
                if os.path.exists(p) else None)
        if new is None:
            state = "removed" if mine is not None else None
        elif mine is None:
            state = "new"
        elif mine == new:
            state = "current"
        elif mine == old:
            state = "take"
        else:
            state = "review"
        if state:
            out.append((state, fill(rel, subs), brel, old, new))
    return out


def set_base(book_root, rev="HEAD"):
    """Record `rev` (default: bible-core HEAD) as the book's template base in
    book.json "template", touching only that line. Returns the short hash."""
    import re
    r = _git(["rev-parse", "--short=7", f"{rev}^{{commit}}"])
    if r.returncode:
        raise RuntimeError(f"bible-core has no commit {rev}")
    short = r.stdout.decode().strip()
    vendored = os.path.join(book_root, "biblecore", "book.py")
    if not (os.path.exists(vendored) and '"template",' in open(vendored, encoding="utf-8").read()):
        raise RuntimeError("the book's vendored core doesn't know book.json \"template\" "
                           "yet (0.11.1+); run core_sync.py on it first")
    p = os.path.join(book_root, "book.json")
    text = open(p, encoding="utf-8").read()
    new, n = re.subn(r'^(\s*"template"\s*:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{short}"',
                     text, count=1, flags=re.M)
    if not n:  # add it after "core" (or before the closing brace)
        new, n = re.subn(r'^(\s*)("core"\s*:\s*"[^"]*")(,?)\n',
                         lambda m: f'{m.group(1)}{m.group(2)},\n{m.group(1)}"template": '
                                   f'"{short}"{m.group(3)}\n', text, count=1, flags=re.M)
    if not n:
        new, n = re.subn(r'\n}\s*$', f',\n  "template": "{short}"\n}}\n', text, count=1)
    if not n:
        raise RuntimeError("couldn't place \"template\" in book.json; add it by hand")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    return short


def template_main(book_root, args):
    import difflib
    if "--set-base" in args:
        i = args.index("--set-base")
        rev = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("-") else "HEAD"
        short = set_base(book_root, rev)
        print(f"book.json \"template\" = {short}: the template as of that commit is "
              f"taken; later template changes will show here. Commit book.json.")
        return 0
    base = None
    if "--base" in args:
        base = args[args.index("--base") + 1]
    stat = "--stat" in args
    rows = template_drift(book_root, base)
    cfg = _book_cfg(book_root)
    head = _git(["rev-parse", "--short=7", "HEAD"]).stdout.decode().strip()
    print(f"template changes since {base or cfg.get('template')} (bible-core {head}), "
          f"for {cfg.get('book', book_root)}")
    if _git(["status", "--porcelain", "--", "template"]).stdout.strip():
        print("  (bible-core has uncommitted template/ edits; they're not included)")
    if not rows:
        print("  nothing: the book has taken every template change")
        return 0
    order = ("take", "review", "new", "removed", "current")
    for state in order:
        for st, rel, brel, old, new in rows:
            if st == state:
                print(f"  {st:8} {brel}")
    if not stat:
        for st, rel, brel, old, new in rows:
            if st in ("take", "review", "new"):
                print(f"\n--- template/{rel}: {st}")
                diff = difflib.unified_diff((old or "").splitlines(), (new or "").splitlines(),
                                            "base", "now", lineterm="", n=2)
                for ln in list(diff)[2:]:
                    print(ln)
    print("\nAdopting is optional. After taking what you want, record it with\n"
          f"  python tools/core_diff.py {os.path.relpath(book_root)} --template --set-base")
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    book_root = os.path.abspath(args[0])
    if "--template" in args:
        try:
            return template_main(book_root, args[1:])
        except RuntimeError as exc:
            print(exc)
            return 1
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
