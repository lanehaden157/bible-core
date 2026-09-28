"""corpus/lxx.py: the Text-Fabric LXX reader, on small feature files written
into a temp folder (greek_book.write_lxx), so it runs without Matthew's
copy of the LXX."""
import os
import shutil
import tempfile

import greek_book
from biblecore.corpus import lxx

_tmp = None


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-lxx-")


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)


def test_words_by_book_in_text_order():
    greek_book.write_lxx(_tmp)
    out = lxx.load_lxx(_tmp, lambda w: w.upper())
    assert out.pop(lxx.BOOKS_KEY) == ["Gen", "Exod"], out
    assert out["Gen"] == [(1, 1, "ΤΙΣ"), (1, 1, "ΛΈΓΩ"), (2, 4, "ΒΊΒΛΟΣ"), (2, 4, "ΓΈΝΕΣΙΣ")], out
    assert out["Exod"] == [(1, 1, "ΖΗΛΩΤΉΣ")], out


def test_higher_nodes_after_the_words_are_ignored():
    # book/chapter/verse files go on past the last word, one line per
    # higher-level node ('6<TAB>1' is the first chapter node); only word
    # nodes are read
    greek_book.write_lxx(_tmp)
    for name in ("chapter.tf", "verse.tf"):
        with open(os.path.join(_tmp, name), "a", encoding="utf-8") as fh:
            fh.write("6\t1\n2\n")
    out = lxx.load_lxx(_tmp, lambda w: w)
    assert sum(len(v) for k, v in out.items() if k != lxx.BOOKS_KEY) == 5, out


def test_missing_feature_file_exits_with_a_pointer():
    greek_book.write_lxx(_tmp)
    os.remove(os.path.join(_tmp, "verse.tf"))
    try:
        lxx.load_lxx(_tmp, lambda w: w)
    except SystemExit as exc:
        assert "verse.tf" in str(exc) and "corpus/README.md" in str(exc), exc
    else:
        raise AssertionError("expected SystemExit for a missing feature file")


def test_a_word_with_no_lemma_keeps_the_rest_aligned():
    # Text-Fabric leaves out a node with no value and gives the next one an
    # explicit number: node 2 has no lemma, so node 3's line is '3<TAB>c'
    greek_book.write_lxx(_tmp, [("Gen", 1, 1, "a"), ("Gen", 1, 2, "-"),
                                ("Gen", 1, 3, "c"), ("Exod", 2, 1, "d")])
    with open(os.path.join(_tmp, "lex_utf8.tf"), "w", encoding="utf-8") as fh:
        fh.write("@node\n@valueType=str\n\na\n3\tc\nd\n")
    out = lxx.load_lxx(_tmp, lambda w: w)
    assert out["Gen"] == [(1, 1, "a"), (1, 3, "c")], out
    assert out["Exod"] == [(2, 1, "d")], out
