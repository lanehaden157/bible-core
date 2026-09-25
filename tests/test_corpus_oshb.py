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


def test_aramaic_words_carry_lang():
    """E16: Daniel switches to Aramaic mid-verse at 2:4."""
    real = support.joshua_book()
    tmp = tempfile.mkdtemp(prefix="biblecore-dan-")
    try:
        cfg = dict(real.cfg, book="Daniel", osis="Dan", slug="daniel",
                   paths=dict(real.cfg["paths"], wlc=real.path("wlc"),
                              words="Daniel-words.tsv", reading="Daniel-reading.txt",
                              verse_map="daniel-versification.md"))
        b = bookmod.Book(cfg, tmp)
        oshb.build(b)
        v = [w for w in oshb.load_words(b) if (w["ch"], w["v"]) == (2, 4)]
        langs = [w["lang"] for w in v]
        fails = []
        if not langs or langs[0] != "hebrew" or langs[-1] != "aramaic":
            fails.append(f"Dan 2:4 langs {langs}")
        if "hebrew" in {w["lang"] for w in oshb.load_words(b) if w["ch"] == 5}:
            fails.append("Dan 5 should be all Aramaic")
        return fails
    finally:
        shutil.rmtree(tmp)
