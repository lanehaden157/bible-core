"""The test fixtures themselves (structural audit B1): tests read sibling
data through temp copies, and a write into a sibling repo is refused even
when a test function is called directly, not through run.py."""
import os
import pathlib
import shutil

import support


def _probe(name):
    # a folder that doesn't exist: without the guard the write fails anyway
    # (FileNotFoundError), so this test can never create a file there
    return os.path.join(support.SOURCES[name], "__guard_probe__", "x.txt")


def test_writes_into_siblings_are_refused():
    fails = []
    for name in support.SOURCES:
        p = _probe(name)
        attempts = {
            "open(w)": lambda: open(p, "w"),
            "open(a)": lambda: open(p, "a"),
            "write_text": lambda: pathlib.Path(p).write_text("x"),
            "os.open": lambda: os.open(p, os.O_WRONLY | os.O_CREAT),
            "mkdir": lambda: os.mkdir(os.path.dirname(p)),
            "remove": lambda: os.remove(p),
            "replace": lambda: os.replace(p, p + ".2"),
            "copyfile": lambda: shutil.copyfile(support.FIXTURE, p),
            "rmtree": lambda: shutil.rmtree(os.path.dirname(p)),
        }
        for label, attempt in attempts.items():
            try:
                attempt()
            except support.SiblingWriteError:
                continue
            except OSError as exc:
                fails.append(f"{name} {label}: got {type(exc).__name__}, not refused")
                continue
            fails.append(f"{name} {label}: not refused")
    return fails


def test_reads_of_siblings_still_work():
    if not support.have_joshua():
        return []
    with open(os.path.join(support.JOSHUA_SRC, "book.json"), encoding="utf-8") as fh:
        return [] if '"Joshua"' in fh.read() else ["couldn't read ../Joshua/book.json"]


def test_the_default_book_is_a_temp_copy():
    b = support.joshua_book()
    real = os.path.normcase(os.path.abspath(support.JOSHUA_SRC))
    root = os.path.normcase(os.path.abspath(b.root))
    fails = []
    if support.have_joshua() and (root == real or root.startswith(real + os.sep)):
        fails.append(f"joshua_book() is rooted in the real checkout: {b.root}")
    if support.have_joshua() and not os.path.exists(os.path.join(b.root, "units", "unit-01.html")):
        fails.append("the copy has no units")
    return fails
