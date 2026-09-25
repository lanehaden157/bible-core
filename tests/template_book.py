"""Instantiate the starter template as a scratch book (test helper).

make_book(dest, name, osis, slug) copies template/ to dest, fills the
{{BOOK}}/{{OSIS}}/{{ABBREV}}/{{SLUG}} placeholders (file names included),
and vendors this checkout's biblecore/ + canon files, the same way
tools/core_sync.py does minus the git bookkeeping.
"""
import os
import shutil
import sys

import support

sys.path.insert(0, os.path.join(support.CORE, "tools"))
from new_book import instantiate  # noqa: E402


def make_book(dest, name, osis, slug, abbrev=None):
    instantiate(dest, name, osis, slug, abbrev)
    shutil.copytree(os.path.join(support.CORE, "biblecore"), os.path.join(dest, "biblecore"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    from core_sync import copy_canon_files
    copy_canon_files(dest)
    from biblecore import __version__
    with open(os.path.join(dest, "biblecore", "CORE_VERSION"), "w") as fh:
        fh.write(f"{__version__} test\n")
    return dest
