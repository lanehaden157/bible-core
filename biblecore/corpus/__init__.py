"""Corpus adapters: where a book's words and verses come from.

Each adapter exposes build(book) (generate the book's word table and reading
text from the pinned source) and load_words(book) (word rows in text order,
with integer ch/v, variant readings already resolved).
"""
import importlib


def adapter(kind=None):
    if kind is None:
        from biblecore.book import book
        kind = book().cfg["corpus"]["kind"]
    try:
        return importlib.import_module(f"biblecore.corpus.{kind}")
    except ModuleNotFoundError:
        raise ValueError(f"no corpus adapter 'biblecore/corpus/{kind}.py'")
