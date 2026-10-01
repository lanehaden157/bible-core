"""Shared test fixtures.

The core is tested against real book data: Joshua (the reference
implementation) and Numbers (the template-shaped book). The sibling
checkouts are sources only. Tests work on temporary copies of them
(copy_of(); JOSHUA below is one), made once per process, so a book command
that writes lands in the copy.

Structural audit B1: tests have written into ../Joshua twice, once through a
harness that didn't go through run.py. So importing this module also
installs a guard (a Python audit hook) that refuses, for the rest of the
process, any write, rename, delete or mkdir under ../Joshua, ../Numbers or
../Matthew, however the test functions are called. run.py's snapshot check
stays as the backstop, and covers child processes too (the guard can't see
into those; the tests run their CLI subprocesses in temp folders).

Big read-only inputs (morphhb's wlc/, the lexicons, Matthew's corpora) are
read from the real checkouts in place rather than copied.
"""
import json
import re
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
if CORE not in sys.path:
    sys.path.insert(0, CORE)
# Matthew's parity tests import its own pipeline modules; importing would
# write __pycache__/ beside them.
sys.dont_write_bytecode = True

from biblecore import book as bookmod  # noqa: E402

BIBLE = os.path.dirname(CORE)
SOURCES = {name: os.path.join(BIBLE, name) for name in ("Joshua", "Numbers", "Matthew")}


# -- the guard --------------------------------------------------------------

class SiblingWriteError(PermissionError):
    pass


_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_PATH_EVENTS = {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.truncate",
                "os.chmod", "os.utime", "os.symlink", "os.link", "shutil.rmtree",
                "shutil.move", "shutil.copyfile", "shutil.copytree"}
_ROOTS = tuple(os.path.normcase(os.path.abspath(p)) + os.sep for p in SOURCES.values())


def _under_sibling(path):
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    p = os.path.normcase(os.path.abspath(os.fsdecode(path)))
    return (p + os.sep).startswith(_ROOTS)


def _guard(event, args):
    if event == "open":
        path, _mode, flags = args
        if isinstance(flags, int) and flags & _WRITE_FLAGS and _under_sibling(path):
            raise SiblingWriteError(f"tests must not write into a sibling book repo: {path} "
                                    f"(work on support.copy_of(...) instead)")
    elif event in _PATH_EVENTS:
        # for the two-path events (rename, copy, move, link) the target is
        # what matters; a source under a sibling is a read (copy) or also
        # caught (rename/move remove it)
        targets = args[:2] if event in ("os.rename", "shutil.move") else \
            args[1:2] if event in ("shutil.copyfile", "shutil.copytree", "os.symlink",
                                   "os.link") else args[:1]
        for t in targets:
            if _under_sibling(t):
                raise SiblingWriteError(f"tests must not change a sibling book repo "
                                        f"({event}): {t}")


def install_guard():
    """Once per process: sibling repos become write-protected for it."""
    if not getattr(sys, "_biblecore_sibling_guard", False):
        sys.addaudithook(_guard)
        sys._biblecore_sibling_guard = True


install_guard()


# -- copies of the sibling checkouts ----------------------------------------

# not copied: history, installed packages, the vendored core (tests use this
# checkout's), build output, and big inputs that are read in place
SKIP_DIRS = {".git", "node_modules", "biblecore", "corpus", "out", "archive",
             "__pycache__", "pipeline"}
SKIP_EXT = (".pdf",)
_copies = {}
_tmp_root = None


def _cleanup():
    if _tmp_root:
        shutil.rmtree(_tmp_root, ignore_errors=True)


def copy_of(name):
    """A temporary copy of the sibling checkout `name` ("Joshua", "Numbers",
    "Matthew"), made on first use and shared by the process's tests: every
    text and data file, not .git, node_modules, the vendored biblecore/, the
    corpora or PDFs. Returns the real (missing) path if the sibling isn't
    checked out, so have_*() checks still say no."""
    global _tmp_root
    src = SOURCES[name]
    if not os.path.isdir(src):
        return src
    if name not in _copies:
        if _tmp_root is None:
            import atexit
            _tmp_root = tempfile.mkdtemp(prefix="biblecore-siblings-")
            atexit.register(_cleanup)
        dst = os.path.join(_tmp_root, name)
        shutil.copytree(src, dst, ignore=lambda d, names: [
            n for n in names if n in SKIP_DIRS or n.endswith(SKIP_EXT)])
        _copies[name] = dst
    return _copies[name]


JOSHUA_SRC = SOURCES["Joshua"]
NUMBERS_SRC = SOURCES["Numbers"]
MATTHEW_SRC = SOURCES["Matthew"]
# Matthew's fetched corpora (`python -m biblecore fetch` there) and its retired
# pipeline, kept in archive/ as the reference the parity tests compare against
MATTHEW_CORPUS = os.path.join(MATTHEW_SRC, "corpus")
MATTHEW_PIPE = os.path.join(MATTHEW_SRC, "archive", "pipeline")
JOSHUA = copy_of("Joshua")
WLC = os.path.join(JOSHUA_SRC, "node_modules", "morphhb", "wlc")
LEXICON = os.path.join(JOSHUA_SRC, "corpus", "lexicon", "HebrewStrong.xml")

# Joshua's real book.json, less its core pin (the tests run this checkout).
# test_book checks it still matches ../Joshua/book.json; refresh it when
# Joshua's settings change.
FIXTURE = os.path.join(HERE, "joshua-book.json")


def read_only_paths(src):
    """The big read-only inputs of a Hebrew book, pointed at the real
    checkout: the only path overrides the fixtures need."""
    return {"wlc": os.path.join(src, "node_modules", "morphhb", "wlc"),
            "lexicon": os.path.join(src, "corpus", "lexicon", "HebrewStrong.xml")}


def have_joshua():
    return os.path.exists(os.path.join(JOSHUA_SRC, "Joshua-words.tsv"))


def have_numbers():
    return os.path.exists(os.path.join(NUMBERS_SRC, "book.json"))


def joshua_config():
    cfg = json.load(open(FIXTURE, encoding="utf-8"))
    cfg["paths"] = dict(cfg.get("paths", {}), **read_only_paths(JOSHUA_SRC))
    return cfg


def joshua_book():
    """Joshua (a temp copy, shared by the process's tests) as the current
    Book. Tests that write to it should use scratch_book() instead, so they
    don't change what the next test reads."""
    return bookmod.use(bookmod.Book(joshua_config(), JOSHUA))


def numbers_book():
    """Numbers (a temp copy) as the current Book, from its own book.json:
    the template-shaped book on the forward path (two groupings, five
    components, default paths). Call have_numbers() first."""
    root = copy_of("Numbers")
    cfg = json.load(open(os.path.join(root, "book.json"), encoding="utf-8"))
    cfg["paths"] = dict(cfg.get("paths", {}), **read_only_paths(NUMBERS_SRC))
    return bookmod.use(bookmod.Book(cfg, root))


def scratch_book(copy=("data", "units", "css", "Joshua-words.tsv",
                       "Joshua-reading.txt", "retrofit/retrofit-tags.json")):
    """A private writable copy of the parts of Joshua a test needs, as the
    current Book. Returns the temp root; the caller removes it."""
    tmp = tempfile.mkdtemp(prefix="biblecore-")
    for rel in copy:
        src = os.path.join(JOSHUA, rel)
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        elif os.path.exists(src):
            shutil.copyfile(src, dst)
    bookmod.use(bookmod.Book(joshua_config(), tmp))
    return tmp


def unstamp(root):
    """Drop the `contract` stamps from a scratch copy's units and units.json,
    so it looks like a book from before contract versions (Joshua's units are
    stamped since it moved onto the core, 2026-09-26)."""
    for f in os.listdir(os.path.join(root, "units")):
        path = os.path.join(root, "units", f)
        text = read(path)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(re.sub(r'\n  "contract": "[^"]*",', "", text))
    path = os.path.join(root, "data", "units.json")
    uj = json.load(open(path, encoding="utf-8"))
    for u in uj["units"]:
        u.pop("contract", None)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(uj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
