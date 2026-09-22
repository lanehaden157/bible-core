"""Shared test fixtures.

Joshua is the reference implementation, so the core is tested against its
real data, read-only: its word table, units, threads and roots. Nothing here
writes into the Joshua repo; a test that needs to write copies what it needs
into a temporary book first (scratch_book()).
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
if CORE not in sys.path:
    sys.path.insert(0, CORE)

from biblecore import book as bookmod  # noqa: E402

JOSHUA = os.path.normpath(os.path.join(CORE, "..", "Joshua"))
FIXTURE = os.path.join(HERE, "joshua-book.json")


def have_joshua():
    return os.path.exists(os.path.join(JOSHUA, "Joshua-words.tsv"))


def joshua_book():
    """The real Joshua repo as a Book (read-only use only)."""
    return bookmod.use(bookmod.Book.from_file(FIXTURE, root=JOSHUA))


def scratch_book(copy=("data", "units", "css", "Joshua-words.tsv",
                       "Joshua-reading.txt", "pipeline/retrofit-tags.json")):
    """A temporary writable copy of the parts of Joshua a test needs, as the
    current Book. Big read-only inputs (morphhb, the lexicon) stay pointed at
    the real repo. Returns the temp root; the caller removes it."""
    tmp = tempfile.mkdtemp(prefix="biblecore-")
    for rel in copy:
        src = os.path.join(JOSHUA, rel)
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        elif os.path.exists(src):
            shutil.copyfile(src, dst)
    cfg = json.load(open(FIXTURE, encoding="utf-8"))
    cfg["palette"] = os.path.join(HERE, "joshua_well.json")
    cfg["paths"] = dict(cfg["paths"],
                        wlc=os.path.join(JOSHUA, "node_modules", "morphhb", "wlc"),
                        lexicon=os.path.join(JOSHUA, "pipeline", "corpus", "lexicon",
                                             "HebrewStrong.xml"))
    bookmod.use(bookmod.Book(cfg, tmp))
    return tmp


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
