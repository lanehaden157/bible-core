"""Language adapters. Each exposes:

    transliterate(text) -> str                       deterministic, no lemma
    transliterate_word(surface, lemma, morph) -> str with lemma-keyed overrides
    SCRIPT_RE                                        the language's native script

Schemes are frozen per language and never harmonised across languages
(review H10); the adapter's own test file is its authoritative definition.
"""
import importlib
import re

# Every original-language script a fragment must never contain, whatever
# the book's own language: Hebrew (U+0590-05FF) and Greek (U+0370-03FF,
# U+1F00-1FFF extended). A Hebrew book quoting the LXX still transliterates.
ALL_SCRIPTS_RE = re.compile("[֐-׿Ͱ-Ͽἀ-῿]")


def adapter(language=None):
    if language is None:
        from biblecore.book import book
        language = book().language
    try:
        return importlib.import_module(f"biblecore.lang.{language}")
    except ModuleNotFoundError:
        raise ValueError(f"no language adapter 'biblecore/lang/{language}.py' "
                         f"-- add one (see biblecore/lang/__init__.py)")
