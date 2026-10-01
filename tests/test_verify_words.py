"""verify_words: the independent check of data/words/ and lemmas.json
(Matthew's interlinear pilot, note 9), on Joshua's real data (Hebrew, read
from a temp copy and OSHB in place) and on greek_book.py's tiny Greek book.
Each passes clean, and each kind of corruption is caught."""
import contextlib
import io
import json
import os
import shutil
import tempfile

import greek_book
import support
from biblecore import emit, verify_words
from biblecore import book as bookmod
from biblecore.corpus import morphgnt


def _words_copy(root):
    """A private copy of root's data/ (the checks write into it)."""
    tmp = tempfile.mkdtemp(prefix="bc-vw-")
    shutil.copytree(os.path.join(root, "data"), os.path.join(tmp, "data"))
    return tmp


def _edit(path, fn):
    d = json.load(open(path, encoding="utf-8"))
    fn(d)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, ensure_ascii=False)


def _corruptions(first_ch_file, lemmas_file, native):
    """(name, path, edit) -- each should make the check fail."""
    def first_row(d):
        return d["verses"][sorted(d["verses"], key=int)[0]][0]
    return [
        ("dropped word", first_ch_file, lambda d: d["verses"][sorted(d["verses"], key=int)[0]].pop()),
        ("native script", first_ch_file, lambda d: first_row(d).update(t=native)),
        ("raw parsing", first_ch_file, lambda d: first_row(d).update(m="V-:3PAI-S--")),
        ("extra key", first_ch_file, lambda d: first_row(d).update(x=1)),
        ("lemma count", lemmas_file, lambda d: next(iter(d["lemmas"].values())).update(n=999)),
    ]


def _run_corruptions(root, ch, native):
    fails = []
    words = os.path.join(root, "data", "words", f"{ch}.json")
    lemmas = os.path.join(root, "data", "lemmas.json")
    for name, path, edit in _corruptions(words, lemmas, native):
        keep = open(path, encoding="utf-8").read()
        _edit(path, edit)
        try:
            errs, _ = verify_words.check()
            if not errs:
                fails.append(f"missed: {name}")
        finally:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(keep)
    return fails


def test_hebrew_clean_and_corrupted():
    if not support.have_joshua():
        return ["skipped: no ../Joshua"]
    tmp = _words_copy(support.JOSHUA)
    try:
        cfg = support.joshua_config()
        cfg["paths"] = dict(cfg["paths"], data=os.path.join(tmp, "data"))
        bookmod.use(bookmod.Book(cfg, support.JOSHUA))
        errs, notes = verify_words.check()
        fails = [f"clean Joshua failed: {errs[:5]}"] if errs else []
        if not notes or "verses" not in notes[0]:
            fails.append(f"no summary note: {notes}")
        fails += _run_corruptions(tmp, 1, "בְּ")
        return fails
    finally:
        support.joshua_book()
        shutil.rmtree(tmp, ignore_errors=True)


def test_greek_clean_and_corrupted():
    root = greek_book.make()
    try:
        # a gloss for every lemma, as the real lexicon gives the NT
        with open(os.path.join(root, "corpus", "lexicon", "lexemes.yaml"), "a",
                  encoding="utf-8", newline="\n") as fh:
            for lemma, gloss in (("λέγω", "say"), ("τίς", "who?"), ("τις", "someone"),
                                 ("ζηλωτής", "zealot")):
                fh.write(f"{lemma}:\n    pos: X\n    gloss: {gloss}\n")
        morphgnt._clear()
        with contextlib.redirect_stdout(io.StringIO()):
            morphgnt.build(bookmod.book())
            emit.main([])
        errs, _ = verify_words.check()
        fails = [f"clean Greek book failed: {errs[:5]}"] if errs else []
        fails += _run_corruptions(root, 1, "βίβλος")
        # a second Greek lemma given an existing id
        path = os.path.join(root, "data", "words", "1.json")
        keep = open(path, encoding="utf-8").read()
        _edit(path, lambda d: d["verses"]["2"][0].update(l="biblos"))
        if not verify_words.check()[0]:
            fails.append("missed: one id for two Greek lemmas")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep)
        return fails
    finally:
        morphgnt._clear()
        greek_book.remove(root)
