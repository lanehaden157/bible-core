"""Cut a bible-core release (structural audit F3/F4).

    python tools/release.py 0.11.1 --note "what changed, in a sentence or two"
    python tools/release.py 0.11.1 --note "..." --skip-tests
    python tools/release.py 0.11.1 --note "..." --dry-run    # say what it would do

Commit the change itself first; this makes the release commit on top. In
order:

  1. refuse on a dirty tree, an existing tag, or a version that isn't above
     the current one
  2. run the suite (`python tests/run.py`); stop if it fails
  3. set `__version__` in biblecore/__init__.py, the one place the version
     is written (book.json "core" is set by core_sync.py, the template's by
     new_book.py)
  4. add `- X.Y.Z: <note>` to the end of ARCHITECTURE.md's version list
  5. commit those two files ("Core X.Y.Z: <note>") and tag vX.Y.Z

It never pushes. It prints the push commands and the second half of the
release, `python tools/core_sync.py --all` (vendor, build, test and commit
in every core book).
"""
import argparse
import os
import re
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INIT = "biblecore/__init__.py"  # forward slashes: also a git pathspec
ARCH = "ARCHITECTURE.md"
_VER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_LIST_LINE = re.compile(r"^- \d+\.\d+\.\d+")


def parse(v):
    m = _VER.match(v)
    if not m:
        raise ValueError(f"not a version: {v!r} (want X.Y.Z)")
    return tuple(int(x) for x in m.groups())


def git(args, root=CORE):
    return subprocess.run(["git"] + args, cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def current_version(root=CORE):
    text = open(os.path.join(root, INIT), encoding="utf-8").read()
    m = re.search(r'^__version__ = "([^"]+)"', text, re.M)
    if not m:
        raise RuntimeError(f"no __version__ line in {INIT}")
    return m.group(1)


def bump_version(version, root=CORE):
    p = os.path.join(root, INIT)
    text = open(p, encoding="utf-8").read()
    new, n = re.subn(r'^__version__ = "[^"]+"', f'__version__ = "{version}"', text,
                     count=1, flags=re.M)
    if not n:
        raise RuntimeError(f"no __version__ line in {INIT}")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)


def add_version_line(version, note, root=CORE):
    """Append `- X.Y.Z: note` after the last line of ARCHITECTURE.md's
    version list (the first list of `- N.N.N` lines; a list item may wrap
    onto indented lines)."""
    p = os.path.join(root, ARCH)
    lines = open(p, encoding="utf-8").read().split("\n")
    first = next((i for i, ln in enumerate(lines) if _LIST_LINE.match(ln)), None)
    if first is None:
        raise RuntimeError(f"no version list (lines starting '- N.N.N') in {ARCH}")
    end = first
    while end + 1 < len(lines) and (_LIST_LINE.match(lines[end + 1])
                                    or lines[end + 1].startswith("  ")):
        end += 1
    if any(ln.startswith(f"- {version}:") or ln.startswith(f"- {version} ")
           for ln in lines[first:end + 1]):
        raise RuntimeError(f"{ARCH} already lists {version}")
    lines.insert(end + 1, f"- {version}: {note.strip()}")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))


def dirty(root=CORE):
    r = git(["status", "--porcelain", "--untracked-files=all"], root)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="release.py")
    ap.add_argument("version", help="the new version, X.Y.Z")
    ap.add_argument("--note", required=True,
                    help="the ARCHITECTURE.md version-list line (what changed)")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="check and report; change nothing")
    ap.add_argument("--trailer", action="append", default=[],
                    help="a trailer line for the release commit (repeatable)")
    a = ap.parse_args(argv)

    try:
        new = parse(a.version)
        old = current_version()
        if new <= parse(old):
            print(f"{a.version} isn't above the current version {old}")
            return 1
    except (ValueError, RuntimeError) as exc:
        print(exc)
        return 1
    tag = f"v{a.version}"
    if git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"]).returncode == 0:
        print(f"tag {tag} already exists")
        return 1
    d = dirty()
    if d:
        print("the tree is dirty; commit the change first (or it's another session's work):")
        for ln in d:
            print("  ", ln)
        return 1
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    behind = git(["rev-list", "--count", "HEAD..@{u}"])
    if branch != "main":
        print(f"note: on branch {branch}, not main")
    if behind.returncode == 0 and behind.stdout.strip() not in ("", "0"):
        print(f"note: {behind.stdout.strip()} commit(s) behind the upstream you last fetched; "
              f"pull first if that's newer work")

    print(f"release {old} -> {a.version}: {a.note.strip()}")
    if a.dry_run:
        steps = ([] if a.skip_tests else ["run the tests"]) + [
            f"set {INIT}", f"add the {ARCH} line", "commit", f"tag {tag}"]
        print("dry run; would " + ", ".join(steps))
        return 0

    if a.skip_tests:
        print("tests skipped (--skip-tests)")
    else:
        print("running python tests/run.py ...")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join("tests", "run.py")], cwd=CORE,
                           env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        tail = (r.stdout + r.stderr).strip().splitlines()[-12:]
        for ln in tail:
            print("   ", ln)
        if r.returncode:
            print("tests failed; nothing changed")
            return 1

    try:
        bump_version(a.version)
        add_version_line(a.version, a.note)
    except RuntimeError as exc:
        git(["checkout", "--", INIT, ARCH])
        print(f"{exc}; nothing committed")
        return 1
    r = git(["add", "--", INIT, ARCH])
    msg = f"Core {a.version}: {a.note.strip()}"
    cmd = ["commit", "-q", "-m", msg] + [x for t in a.trailer for x in ("--trailer", t)]
    r = r if r.returncode else git(cmd)
    if r.returncode:
        print(f"commit failed: {(r.stderr or r.stdout).strip()}")
        return 1
    r = git(["tag", tag])
    if r.returncode:
        print(f"tag failed: {r.stderr.strip()}")
        return 1
    sha = git(["rev-parse", "--short", "HEAD"]).stdout.strip()
    print(f"committed {sha} and tagged {tag}. Nothing pushed. Next:")
    print(f"  git push origin {branch} {tag}")
    print("  python tools/core_sync.py --all      # vendor, build, test, commit in each core book")
    return 0


if __name__ == "__main__":
    sys.exit(main())
