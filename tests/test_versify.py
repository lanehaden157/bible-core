"""versify: morphhb's VerseMap.xml (WLC -> KJV) and the loaders that use it.
The Numbers checks are the hand-built map Numbers needed before this existed
(numbers-versification-map.md), now read from the corpus instead."""
import os

import support
from biblecore import audit, book as bookmod, versify

WLC = os.path.join(support.JOSHUA, "node_modules", "morphhb", "wlc")


def test_numbers_map_matches_the_hand_built_one():
    num = versify.load(WLC)["Num"]
    assert len(num) == 46, len(num)
    assert num[(17, 1)] == (16, 36) and num[(17, 15)] == (16, 50)
    assert num[(17, 16)] == (17, 1) and num[(17, 28)] == (17, 13)
    assert num[(30, 1)] == (29, 40) and num[(30, 17)] == (30, 16)
    assert num[(25, 19)] == (26, 1)


def test_to_source_handles_merges_and_moves():
    num = versify.load(WLC)["Num"]
    heb16 = {(16, v) for v in range(1, 36)} | {(17, 1)}
    assert versify.to_source(26, 1, num) == [(25, 19), (26, 1)]   # merge
    assert versify.to_source(16, 36, num, heb16) == [(17, 1)]     # moved
    assert versify.to_source(16, 36, num) == [(16, 36), (17, 1)]  # no `present`
    assert versify.to_source(17, 1, num) == [(17, 16)]            # its own moved away
    assert versify.to_source(3, 4, num) == [(3, 4)]               # untouched


def test_joshua_has_no_differences():
    # which is why the Joshua parity tests are unaffected by versify
    assert "Josh" not in versify.load(WLC)


def test_source_setting_turns_it_off():
    b = support.joshua_book()
    cfg = dict(b.cfg, osis="Num", versification="source")
    assert versify.book_map(bookmod.Book(cfg, b.root), osis="Num") == {}
    cfg["versification"] = "kjv"
    assert len(versify.book_map(bookmod.Book(cfg, b.root), osis="Num")) == 46
    try:
        bookmod.Book(dict(cfg, versification="nrsv"), b.root)
    except bookmod.BookError:
        pass
    else:
        raise AssertionError("an unknown versification must be refused")


def test_parse_range_reads_half_verses_as_whole():
    assert audit.parse_range("Numbers 26:1b–65") == ((26, 1), (26, 65))
    assert audit.parse_range("Numbers 25:1–26:1a") == ((25, 1), (26, 1))
