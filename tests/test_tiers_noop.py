"""A book without tiers builds exactly as it did before tiers existed.

The gate for the tiers release: for Joshua, Numbers and Matthew, build a copy
of the book with the core at a BASE commit and again with this checkout's
core, same inputs, and compare the two whole trees byte for byte (the vendored
biblecore/ itself aside). Nothing may differ: not data/, units/, css/, the
app shell, index.html, the synced mirror.

Runs only when BIBLECORE_NOOP_BASE names the commit (the last one before the
change under test), e.g.

    BIBLECORE_NOOP_BASE=217333d python tests/run.py tiers_noop

A later release that changes a tierless book's output on purpose moves the
base, or simply isn't compared. The second test is the always-on cheap
version: the shell for a tierless book has none of the tier code.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import support
from template_book import make_book
from biblecore import assets
from biblecore import book as bookmod

BASE = os.environ.get("BIBLECORE_NOOP_BASE")
SKIP = {"biblecore", "__pycache__", "out", ".git", "node_modules"}


def _git_archive(commit, dest):
    """This repo's biblecore/ at `commit`, unpacked into dest/biblecore."""
    os.makedirs(dest, exist_ok=True)
    arc = subprocess.run(["git", "archive", commit, "biblecore"], cwd=support.CORE,
                         capture_output=True)
    if arc.returncode:
        raise RuntimeError(arc.stderr.decode(errors="replace"))
    subprocess.run(["tar", "-x", "-C", dest], input=arc.stdout, check=True)


def _prepare(name, core, tmp):
    """A private, buildable copy of sibling `name` with `core` as its
    biblecore/ ("work" = this checkout's)."""
    src = support.copy_of(name)
    dest = os.path.join(tmp, name)
    shutil.copytree(src, dest)
    if core == "work":
        shutil.copytree(os.path.join(support.CORE, "biblecore"), os.path.join(dest, "biblecore"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        _git_archive(core, dest)
    # the big read-only inputs stay in the real checkout
    p = os.path.join(dest, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    real = support.SOURCES[name]
    paths = cfg.setdefault("paths", {})
    if cfg["language"] == "greek":
        paths.setdefault("morphgnt", os.path.join(real, "corpus", "morphgnt"))
        paths.setdefault("lxx", os.path.join(real, "corpus", "lxx"))
        paths.setdefault("greek_lexicon", os.path.join(real, "corpus", "lexicon", "lexemes.yaml"))
        for k in ("morphgnt", "lxx", "greek_lexicon"):
            if not os.path.isabs(paths[k]):
                paths[k] = os.path.join(real, paths[k])
    else:
        paths.setdefault("wlc", os.path.join(real, "node_modules", "morphhb", "wlc"))
        paths.setdefault("lexicon", os.path.join(real, "corpus", "lexicon", "HebrewStrong.xml"))
    json.dump(cfg, open(p, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    return dest


def _build(root):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "biblecore", "build"], cwd=root, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr)[-1500:]


def _tree(root):
    out = {}
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = open(p, "rb").read()
    return out


def test_tierless_books_build_identically():
    if not BASE:
        return []
    fails = []
    for name in ("Joshua", "Numbers", "Matthew"):
        if not os.path.isdir(support.SOURCES[name]):
            continue
        tmp = tempfile.mkdtemp(prefix="bc-noop-")
        try:
            a = _prepare(name, BASE, tmp + "/a")
            b = _prepare(name, "work", tmp + "/b")
            for label, root in (("base", a), ("work", b)):
                rc, tail = _build(root)
                if rc:
                    fails.append(f"{name}: build with the {label} core failed:\n{tail}")
            ta, tb = _tree(a), _tree(b)
            for rel in sorted(set(ta) | set(tb)):
                if ta.get(rel) != tb.get(rel):
                    how = "only in base" if rel not in tb else "only in work" if rel not in ta else "differs"
                    fails.append(f"{name}: {rel} {how}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return fails


def test_tierless_shell_has_no_tier_code():
    tmp = tempfile.mkdtemp(prefix="bc-noop-shell-")
    try:
        make_book(tmp, "Leviticus", "Lev", "leviticus")
        b = bookmod.Book.from_file(os.path.join(tmp, "book.json"))
        shell = assets.shell(b)
        fails = []
        if "app/tiers.js" in shell:
            fails.append("a tierless book was given app/tiers.js")
        for rel, text in shell.items():
            if re.search(r"tiers", text, re.I) and rel != "index.html":
                fails.append(f"{rel} mentions tiers in a tierless build")
            if "//tiers:" in text:
                fails.append(f"{rel} kept a tier marker line")
        tiered = bookmod.Book({**b.cfg, "tiers": True}, tmp)
        shell_t = assets.shell(tiered)
        if "app/tiers.js" not in shell_t or "tiers.init(" not in shell_t["app/main.js"]:
            fails.append("a tiered book's shell lacks tiers.js or its hooks in main.js")
        if "//tiers:" in shell_t["app/main.js"]:
            fails.append("the tiered main.js kept marker lines")
        if "not translated here" not in shell_t["app/threads.js"]:
            fails.append("the tiered threads.js lacks the untranslated timeline text")
        return fails
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        support.joshua_book()
