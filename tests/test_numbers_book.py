"""Numbers as a fixture (structural audit B4): the book on the forward path,
shaped like the current template (default paths, two groupings, five
components, kjv versification). tests/template_book.py covers an empty
template book; this covers a populated one. It runs `biblecore test` on a
temp copy of ../Numbers, read from its own book.json. Skipped when Numbers
isn't checked out beside bible-core."""
import contextlib
import io

import support
from biblecore import selftest


def setup():
    if support.have_numbers():
        support.numbers_book()


def teardown():
    support.joshua_book()


def test_numbers_passes_biblecore_test():
    """Every book-side check but the core pin (Numbers pins the release it
    last took, which trails this checkout between releases). For the same
    reason the copy's manifest, which records the core version, is
    refreshed first."""
    if not support.have_numbers():
        return []
    from biblecore import manifest
    with contextlib.redirect_stdout(io.StringIO()):
        manifest.main([])
    fails = []
    for name, fn in selftest.CHECKS:
        if name == "pin":
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            errs, _notes = fn()
        fails += [f"{name}: {e}" for e in errs]
    return fails


def test_numbers_resolved_sync_list():
    """Core's defaults give Numbers everything it synced before P4 (0.10.0),
    with no extras: the style reference, the unit map, the canon leads and
    the versification list included."""
    if not support.have_numbers():
        return []
    from biblecore import sync
    got = sync.resolve()
    want = ["numbers_study_style_reference.md", "resources.md", "core-workflow.md",
            "data/roots.json", "Numbers-words.tsv", "numbers-literary-unit-map.md",
            "canon-leads/canon-leads-unit-01.md", "numbers-versification.md"]
    return [f"{w} not synced" for w in want if w not in got]
