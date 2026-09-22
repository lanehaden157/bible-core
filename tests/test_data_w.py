"""Tests for assign_data_w.py.

The headline test is the round-trip: strip every data-w from the one
hand-tagged unit on disk and prove the assigner puts all of them back
byte-identically. That is the whole claim of the script -- it reproduces
hand work -- so it is checked against real data, not a fixture.

The rest are the refusal cases. The script must decline to guess whenever
a verse's span count and source-hit count disagree, because a wrong
data-w points a reader's popover at the wrong Hebrew word, which is worse
than the missing-data-w hard error the audit already catches.
"""
import io
import os
import re
import sys

import support  # noqa: E402
support.joshua_book()
from biblecore import audit as atc          # noqa: E402
from biblecore.data_w import plan, apply_edits, verse_blocks  # noqa: E402

ROOT = support.JOSHUA
UNIT1 = os.path.join(ROOT, "units", "unit-01.html")

_fails = []


def _check(label, cond, detail=""):
    if cond:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}")
        _fails.append((label, detail))


def test_round_trip_reproduces_hand_tagging():
    orig = io.open(UNIT1, encoding="utf-8").read()
    stripped = re.sub(r'\s*data-w="[^"]*"', "", orig)
    _check("stripping leaves no data-w", "data-w" not in stripped)

    edits, report = plan(stripped, "Joshua 1:1-18")
    _check("unit 1 needs no human intervention", not report, report)

    rebuilt = apply_edits(stripped, edits)
    _check("rebuilt file is byte-identical to the hand-tagged original",
           rebuilt == orig)

    before = atc.parse_tagged_spans(orig)
    after = atc.parse_tagged_spans(rebuilt)
    _check("every span's (root, word_id) matches the original",
           before == after)
    expected = orig.count('data-w="')
    _check("every tracked span was assigned",
           len([w for _, w in after if w]) == expected,
           len([w for _, w in after if w]))


def test_idempotent_on_tagged_file():
    """Re-running on a fully tagged unit must be a no-op, not a rewrite."""
    orig = io.open(UNIT1, encoding="utf-8").read()
    edits, report = plan(orig, "Joshua 1:1-18")
    _check("no edits proposed for an already-tagged unit", not edits, edits)
    _check("no complaints about an already-tagged unit", not report, report)


def test_count_mismatch_is_refused():
    """Two spans, one source hit -> assign nothing, explain why."""
    html = ('<div class="v"><span class="n">1</span> '
            '<span class="r" data-root="give">gave</span> and '
            '<span class="r" data-root="give">gave</span></div>')
    edits, report = plan(html, "Joshua 1:1-1")
    _check("a span/hit count mismatch assigns nothing", not edits, edits)
    _check("a span/hit count mismatch is reported",
           any("span(s) but" in r for r in report), report)


def test_existing_conflicting_data_w_is_left_alone():
    """A span that already claims a different word id is never overwritten."""
    orig = io.open(UNIT1, encoding="utf-8").read()
    bogus = orig.replace('data-w="06TSc"', 'data-w="06ZZZ"', 1)
    _check("fixture actually changed a data-w", bogus != orig)
    edits, report = plan(bogus, "Joshua 1:1-18")
    _check("a conflicting data-w is not silently rewritten", not edits, edits)
    _check("a conflicting data-w is reported",
           any("resolve by hand" in r for r in report), report)


def test_verse_blocks_default_and_rollover():
    """Bare verse numbers inherit the passage chapter and roll forward."""
    html = ('<div class="v"><span class="n">17</span> a</div>'
            '<div class="v"><span class="n">18</span> b</div>'
            '<div class="v"><span class="n">1</span> c</div>'
            '<div class="v"><span class="n">2:5</span> d</div>')
    got = [(ch, v) for _, _, ch, v in verse_blocks(html, 1)]
    _check("bare numbers take the passage chapter and roll over",
           got == [(1, 17), (1, 18), (2, 1), (2, 5)], got)


def main():
    for fn in (test_round_trip_reproduces_hand_tagging,
               test_idempotent_on_tagged_file,
               test_count_mismatch_is_refused,
               test_existing_conflicting_data_w_is_left_alone,
               test_verse_blocks_default_and_rollover):
        print(f"\n{fn.__name__}:")
        fn()
    print()
    if _fails:
        print(f"FAIL: {len(_fails)} problem(s)")
        for label, detail in _fails:
            print(f" - {label}: {detail}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
