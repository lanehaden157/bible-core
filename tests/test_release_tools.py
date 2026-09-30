"""The release tooling (structural audit F3/F4/D3): tools/release.py,
tools/core_sync.py --all and tools/core_diff.py --template, on scratch
copies. Nothing here touches bible-core's own files or the sibling books.

The scratch-book tests need a committed bible-core (vendoring refuses a
dirty core, and the template report reads committed template/ files), so
they're skipped rather than failed while core has uncommitted changes.
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

import support
from template_book import make_book

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import core_diff  # noqa: E402
import core_sync  # noqa: E402
import new_book  # noqa: E402
import release  # noqa: E402

from biblecore import __version__  # noqa: E402
from biblecore import book as bookmod  # noqa: E402


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = fn(*a)
    return rc, out.getvalue()


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          encoding="utf-8")


def _git_init(root):
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "start")


def _rmtree(d):
    """rmtree that also removes git's read-only object files (Windows)."""
    import stat

    def unlock(fn, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    shutil.rmtree(d, onexc=unlock)


def _core_template_dirty():
    r = subprocess.run(["git", "status", "--porcelain", "--", "template", "biblecore", "canon"],
                       cwd=support.CORE, capture_output=True, text=True)
    return [ln for ln in r.stdout.splitlines() if "__pycache__" not in ln]


# ---- F4: one version source ------------------------------------------------

def test_template_book_json_holds_no_version():
    """template/book.json's "core" and "template" are placeholders that
    new_book.py fills, so a release bumps biblecore/__init__.py only."""
    cfg = json.load(open(os.path.join(support.CORE, "template", "book.json"), encoding="utf-8"))
    fails = []
    if cfg.get("core") != "{{CORE}}":
        fails.append(f"template/book.json core is {cfg.get('core')!r}, want '{{{{CORE}}}}'")
    if cfg.get("template") != "{{TEMPLATE}}":
        fails.append(f"template/book.json template is {cfg.get('template')!r}")
    return fails


def test_new_book_fills_core_and_template():
    d = tempfile.mkdtemp(prefix="bc-f4-")
    try:
        make_book(d, "Leviticus", "Lev", "leviticus")
        cfg = json.load(open(os.path.join(d, "book.json"), encoding="utf-8"))
        fails = bookmod.validate_config(cfg)
        if cfg.get("core") != __version__:
            fails.append(f"core {cfg.get('core')!r}, package {__version__}")
        want = new_book.template_commit()
        if want and cfg.get("template") != want:
            fails.append(f"template {cfg.get('template')!r}, bible-core HEAD {want}")
        return fails
    finally:
        _rmtree(d)


def test_book_json_template_key_is_checked():
    base = {"book": "X", "osis": "X", "slug": "x", "language": "hebrew",
            "corpus": {"kind": "oshb"}}
    fails = []
    if bookmod.validate_config({**base, "template": "591dba6"}):
        fails.append("a short commit hash was refused")
    if not bookmod.validate_config({**base, "template": "HEAD"}):
        fails.append("'HEAD' was accepted as a template base")
    return fails


def test_set_book_core_touches_only_that_line():
    d = tempfile.mkdtemp(prefix="bc-core-")
    try:
        p = os.path.join(d, "book.json")
        text = '{\n  "book": "X",\n  "groupings": ["a",  "b"],\n  "core": "0.1.0",\n  "hub": "h"\n}\n'
        open(p, "w", encoding="utf-8", newline="\n").write(text)
        fails = []
        if not core_sync.set_book_core(d, "9.9.9"):
            fails.append("reported no change")
        got = open(p, encoding="utf-8").read()
        if got != text.replace('"0.1.0"', '"9.9.9"'):
            fails.append(f"more than the core line changed: {got!r}")
        if core_sync.set_book_core(d, "9.9.9"):
            fails.append("second write reported a change")
        open(p, "w").write('{"book": "X"}')
        core_sync.set_book_core(d, "9.9.9")
        if json.load(open(p)).get("core") != "9.9.9":
            fails.append("core not added to a book.json without it")
        return fails
    finally:
        _rmtree(d)


# ---- F3: release.py --------------------------------------------------------

def test_release_bumps_and_adds_the_version_line():
    d = tempfile.mkdtemp(prefix="bc-rel-")
    try:
        os.makedirs(os.path.join(d, "biblecore"))
        open(os.path.join(d, "biblecore", "__init__.py"), "w").write(
            '"""doc"""\n\n__version__ = "0.4.2"\n')
        arch = ("# A\n\n**Status:** x\n\n- 0.4.0: one\n  wrapped.\n- 0.4.2: two\n\n"
                "## Next\n\n- 1.0.0: not the list\n")
        open(os.path.join(d, "ARCHITECTURE.md"), "w").write(arch)
        fails = []
        if release.current_version(d) != "0.4.2":
            fails.append("current_version")
        release.bump_version("0.4.3", d)
        if release.current_version(d) != "0.4.3":
            fails.append("bump_version")
        release.add_version_line("0.4.3", "three ", d)
        got = open(os.path.join(d, "ARCHITECTURE.md")).read()
        if got != arch.replace("- 0.4.2: two\n", "- 0.4.2: two\n- 0.4.3: three\n"):
            fails.append(f"version line misplaced: {got!r}")
        try:
            release.add_version_line("0.4.3", "again", d)
            fails.append("a repeated version was accepted")
        except RuntimeError:
            pass
        msg = release.commit_message("0.4.3", "short fix.")
        if msg != "Core 0.4.3: short fix":
            fails.append(f"one-sentence message: {msg!r}")
        msg = release.commit_message("0.4.3", "tooling (F3). `x.py` does 0.4.3 things")
        if not msg.startswith("Core 0.4.3: tooling (F3)\n\ntooling (F3). `x.py`"):
            fails.append(f"long message: {msg!r}")
        if release.parse("0.10.0") <= release.parse("0.9.10"):
            fails.append("versions compare as strings")
        return fails
    finally:
        _rmtree(d)


def test_release_refuses_a_dirty_tree():
    d = tempfile.mkdtemp(prefix="bc-rel-")
    try:
        open(os.path.join(d, "a.txt"), "w").write("a\n")
        _git_init(d)
        fails = []
        if release.dirty(d):
            fails.append(f"clean repo reported dirty: {release.dirty(d)}")
        open(os.path.join(d, "b.txt"), "w").write("b\n")
        if not release.dirty(d):
            fails.append("an untracked file wasn't reported")
        return fails
    finally:
        _rmtree(d)


# ---- F3: core_sync --all ---------------------------------------------------

def test_changed_paths_lists_each_file():
    d = tempfile.mkdtemp(prefix="bc-cp-")
    try:
        open(os.path.join(d, "a.txt"), "w").write("a\n")
        open(os.path.join(d, "gone.txt"), "w").write("g\n")
        _git_init(d)
        open(os.path.join(d, "a.txt"), "w").write("changed\n")
        os.remove(os.path.join(d, "gone.txt"))
        os.makedirs(os.path.join(d, "new dir"))
        open(os.path.join(d, "new dir", "x.txt"), "w").write("x\n")
        got = sorted(core_sync.changed_paths(d))
        want = ["a.txt", "gone.txt", "new dir/x.txt"]
        return [] if got == want else [f"changed_paths {got}, want {want}"]
    finally:
        _rmtree(d)


def test_core_books_come_from_books_json():
    names = [n for n, _root in core_sync.core_books()]
    fails = [f"{n} missing from core_books" for n in ("Numbers", "Joshua") if n not in names]
    if "Matthew" in names:
        fails.append("Matthew (kind legacy) listed as a core book")
    return fails


def _scratch_repo_book(d):
    """A template book on an older core pin, built and committed."""
    make_book(d, "Leviticus", "Lev", "leviticus")
    p = os.path.join(d, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["paths"] = {"wlc": support.WLC}
    cfg["core"] = "0.0.1"
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(d, "biblecore", "CORE_VERSION"), "w", newline="\n") as fh:
        fh.write(f"{__version__} {core_sync.core_commit()}\n")
    for cmd in (["corpus"], ["build"]):
        r = core_sync.run_biblecore(d, cmd)
        if r.returncode:
            raise RuntimeError(f"{cmd[0]} failed: {r.stdout[-400:]}{r.stderr[-400:]}")
    _git_init(d)


def test_sync_book_commits_a_clean_book_and_skips_a_dirty_one():
    if _core_template_dirty() or not os.path.isdir(support.WLC):
        print("    (skipped: bible-core has uncommitted changes, or no WLC)")
        return
    d = tempfile.mkdtemp(prefix="bc-all-")
    try:
        _scratch_repo_book(d)
        fails = []
        open(os.path.join(d, "stray.md"), "w").write("another session's edit\n")
        (status, detail), _out = _quiet(lambda: core_sync.sync_book("Lev", d))
        if status != "skipped" or "stray.md" not in detail:
            fails.append(f"dirty book not skipped: {status} {detail}")
        if json.load(open(os.path.join(d, "book.json")))["core"] != "0.0.1":
            fails.append("a skipped book was changed")
        os.remove(os.path.join(d, "stray.md"))

        head = _git(d, "rev-parse", "HEAD").stdout.strip()
        rc_out = _quiet(lambda: core_sync.sync_book("Lev", d, trailers=["X-Test: yes"]))
        status, detail = rc_out[0]
        if status != "committed":
            return fails + [f"sync_book: {status} {detail}\n{rc_out[1][-1500:]}"]
        files = _git(d, "diff", "--name-only", head, "HEAD").stdout.split()
        if files != ["book.json"]:
            fails.append(f"expected only book.json committed (vendor already current), got {files}")
        msg = _git(d, "log", "-1", "--format=%B").stdout
        if not msg.startswith(f"Core {__version__}:") or "X-Test: yes" not in msg:
            fails.append(f"commit message: {msg!r}")
        if _git(d, "status", "--porcelain").stdout.strip():
            fails.append("tree not clean after the commit")
        status, detail = _quiet(lambda: core_sync.sync_book("Lev", d))[0]
        if status != "current":
            fails.append(f"second run not a no-op: {status} {detail}")
        return fails
    finally:
        _rmtree(d)


# ---- D3: core_diff --template ----------------------------------------------

def test_template_drift_states_and_set_base():
    if _core_template_dirty():
        print("    (skipped: bible-core has uncommitted template/ changes)")
        return
    d = tempfile.mkdtemp(prefix="bc-drift-")
    try:
        make_book(d, "Leviticus", "Lev", "leviticus")
        fails = []
        rows = core_diff.template_drift(d)
        if rows:
            fails.append(f"a fresh book shows drift: {[(s, r) for s, r, *_ in rows]}")
        # 591dba6 (0.8.5) predates later template edits to CLAUDE.md and the
        # instruction file: a fresh book already has the new text
        old = "591dba6"
        rows = {r: s for s, r, *_ in core_diff.template_drift(d, old)}
        if rows.get("CLAUDE.md") != "current":
            fails.append(f"CLAUDE.md from the current template: {rows.get('CLAUDE.md')}")
        # back to the old template text -> "take"; a book edit on top -> "review"
        old_text = dict((r, o) for _s, r, _b, o, _n in core_diff.template_drift(d, old))
        with open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(old_text["CLAUDE.md"])
        rows = {r: s for s, r, *_ in core_diff.template_drift(d, old)}
        if rows.get("CLAUDE.md") != "take":
            fails.append(f"CLAUDE.md at the old template text: {rows.get('CLAUDE.md')}")
        with open(os.path.join(d, "CLAUDE.md"), "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\nA book's own note.\n")
        rows = {r: s for s, r, *_ in core_diff.template_drift(d, old)}
        if rows.get("CLAUDE.md") != "review":
            fails.append(f"CLAUDE.md with a book edit: {rows.get('CLAUDE.md')}")
        if any(r.startswith(("app/", "data/", "units/")) or r == "index.html" for r in rows):
            fails.append(f"generated or book-owned files reported: {sorted(rows)}")

        before = open(os.path.join(d, "book.json"), encoding="utf-8").read()
        short = core_diff.set_base(d, old)
        after = open(os.path.join(d, "book.json"), encoding="utf-8").read()
        if json.loads(after).get("template") != short or not short.startswith(old):
            fails.append(f"set_base wrote {json.loads(after).get('template')}")
        changed = [x for x, y in zip(before.split("\n"), after.split("\n")) if x != y]
        if len(changed) != 1:
            fails.append(f"set_base changed {len(changed)} lines")
        fails += bookmod.validate_config(json.loads(after))
        rc, out = _quiet(core_diff.main, [d, "--template", "--stat"])
        if rc or "review   CLAUDE.md" not in out:
            fails.append(f"--template --stat output: {out}")
        try:
            core_diff.set_base(d, "0000000")
            fails.append("an unknown commit was accepted")
        except RuntimeError:
            pass
        return fails
    finally:
        _rmtree(d)
