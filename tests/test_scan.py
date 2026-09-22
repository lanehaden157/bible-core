"""Regression tests for scan_occurrences.py. Operates purely on English
gloss HTML (mirrors what a built fragment's visible text looks like), so
nothing here needs Hebrew.
"""
import os
import sys

from biblecore import scan as so  # noqa: E402

fail = []


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


def test_scan_counts_in_verse_occurrences():
    html = (
        '<p class="v"><span class="n">1</span> and <span class="r" '
        'data-root="kol" data-w="06a">all</span> Israel</p>'
        '<p class="v"><span class="n">2</span> <span class="r" '
        'data-root="kol" data-w="06b">All</span> of them</p>'
    )
    roots = so.scan_unit(html)
    _check("kol should count 2 in-verse occurrences", roots["kol"]["count"] == 2, roots)
    _check("kol verses should be [1, 2]", roots["kol"]["verses"] == [1, 2], roots)


def test_scan_hits_have_context_snippets():
    html = ('<p class="v"><span class="n">3</span> before the '
            '<span class="r" data-root="devote">devoted</span> city fell</p>')
    roots = so.scan_unit(html)
    hit = roots["devote"]["hits"][0]
    _check("hit text should be the tagged word", hit["hit"] == "devoted", hit)
    _check("pre-context should contain the text right before the hit",
           "before the" in hit["pre"], hit)
    _check("post-context should contain the text right after the hit",
           "city fell" in hit["post"], hit)


def test_scan_total_counts_legend_and_gloss_occurrences_too():
    """`total` counts every data-root in the fragment, not just in-verse
    ones -- e.g. a legend entry or an .rl gloss span outside a .v block."""
    html = (
        '<section class="block legend"><ul><li class="r" data-root="kol">'
        'kol</li></ul></section>'
        '<p class="v"><span class="n">1</span> <span class="r" '
        'data-root="kol" data-w="06a">all</span></p>'
    )
    roots = so.scan_unit(html)
    _check("count (in-verse only) should be 1", roots["kol"]["count"] == 1, roots)
    _check("total (legend + in-verse) should be 2", roots["kol"]["total"] == 2, roots)


def test_scan_empty_fragment_yields_no_roots():
    html = '<p class="v"><span class="n">1</span> nothing tagged here</p>'
    roots = so.scan_unit(html)
    _check("an untagged fragment should yield no roots", roots == {}, roots)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        before = len(fail)
        t()
        print(("  ok  " if len(fail) == before else "FAIL  ") + t.__name__)

    if fail:
        print(f"\nFAIL: {len(fail)} problem(s)")
        for f in fail:
            print(" -", f)
        sys.exit(1)
    print(f"\nPASS: {len(tests)} checks")


if __name__ == "__main__":
    main()
