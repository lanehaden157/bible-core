"""The OSHB corpus builder reproduces Joshua's committed word table, reading
text and boundary list byte for byte, and the documented BHS counts."""
import os
import shutil
import tempfile

import support
from biblecore import book as bookmod
from biblecore.corpus import oshb


def test_joshua_rebuild_is_byte_identical():
    if not support.have_joshua():
        return ["Joshua checkout not found next to bible-core"]
    real = support.joshua_book()
    tmp = tempfile.mkdtemp(prefix="biblecore-corpus-")
    try:
        cfg = dict(real.cfg, paths=dict(real.cfg["paths"], wlc=real.path("wlc")))
        counts = oshb.build(bookmod.Book(cfg, tmp))
        fails = []
        for name in ("Joshua-words.tsv", "Joshua-reading.txt", "candidate-boundaries.md"):
            if support.read(os.path.join(tmp, name)) != support.read(os.path.join(support.JOSHUA, name)):
                fails.append(f"{name} differs from Joshua's committed copy")
        expected = {"verses": 658, "words": 10083, "pe": 52, "samekh": 42}
        if counts != expected:
            fails.append(f"counts {counts} != BHS-verified {expected}")
        return fails
    finally:
        shutil.rmtree(tmp)


def test_load_words_drops_exactly_the_32_ketiv():
    b = support.joshua_book()
    words = oshb.load_words(b)
    if len(words) != 10083 - 32:
        return [f"expected 10051 running-text words, got {len(words)}"]


def test_load_reading():
    verses = oshb.load_reading(support.joshua_book())
    if len(verses) != 658 or verses[0][:2] != (1, 1):
        return [f"unexpected reading parse: {len(verses)} verses, first {verses[0][:2]}"]
