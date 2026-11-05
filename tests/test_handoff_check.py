"""handoff-check: template shape, boxes, quotes against the notes, and the
original rule that a handoff can't say "none" while it has provisional renderings."""
from biblecore import handoff_check

GOOD = """# Handoff

## Scope
Unit 1, 1:1-54, The First Accounting. Notes: 4 rows.

## Verse by verse
- 3: see Call 1

## Approved boxes

### The census at the mountain
- **Kind:** story
- **Anchor:** 1:46
- **Ref:** Exod 38:26
- **Story:** The same total, paid per skull.
- **Same:** the number 603,550
- **Different:** payment, not counting
- **Does:** ties the muster to the sanctuary.

2 rows considered, 1 ship, 1 dropped.

## Decisions
none

## Threads
none

## Calls for Lane (1)

1. v3 'x' or 'y'.

## Checks for code
none

## Source status
Read: Exod 38.
"""
NOTES = ("| 1:46 | Exod 38:26 | story | gulgolet | per head, \"the same total is paid\" | VERIFIED | strong | ship |\n"
         "| 1:2 | Exod 30:12 | echo | gulgolet | not read | RECALLED | weak | drop |\n"
         "Unit 1: 4 rows\n")


def _fix(old, new, text=GOOD):
    assert old in text, old
    return text.replace(old, new, 1)


def test_ok():
    assert handoff_check.check(GOOD) == []


def test_none_with_provisional():
    bad = _fix("see Call 1", "'x' (provisional)")
    bad = _fix("1. v3 'x' or 'y'.", "none", bad)
    assert any("none/empty" in w for w in handoff_check.check(bad))


def test_count_mismatch():
    assert any("heading says" in w for w in handoff_check.check(_fix("(1)", "(3)")))


def test_missing_section():
    assert handoff_check.check("## Scope\nx\n")


def test_out_of_order_and_missing():
    ws = handoff_check.check(_fix("## Decisions\nnone\n", "") + "\n## Decisions\nnone\n")
    assert any("out of template order" in w for w in ws)
    assert any('missing section "Source status"' in w
               for w in handoff_check.check(_fix("## Source status\nRead: Exod 38.\n", "")))


def test_native_script():
    assert any("native" in w for w in handoff_check.check(_fix("Read: Exod 38.", "Read: גלגלת")))


def test_box_fields_and_anchor():
    ws = handoff_check.check(_fix("- **Does:** ties the muster to the sanctuary.\n", ""))
    assert any("missing Does" in w for w in ws)
    assert any("outside the unit" in w for w in handoff_check.check(_fix("1:46", "2:3")))
    assert any("Ref names no verses" in w for w in handoff_check.check(_fix("Exod 38:26", "Exodus")))


def test_count_line():
    assert any("considered" in w and "ship" in w for w in handoff_check.check(_fix("2 rows considered", "9 rows considered")))
    assert any("no count line" in w for w in handoff_check.check(_fix("2 rows considered, 1 ship, 1 dropped.", "")))


def test_notes_row_count_and_quotes():
    assert handoff_check.check(GOOD, NOTES) == []
    assert any("4 rows" in w or "ends with" in w for w in handoff_check.check(_fix("4 rows", "5 rows"), NOTES))
    quoted = _fix("The same total, paid per skull.", 'Says "the same total is paid" outright.')
    assert handoff_check.check(quoted, NOTES) == []
    assert any("not in the notes" in w for w in handoff_check.check(_fix("The same total, paid per skull.", 'Says "a quote the notes never had".'), NOTES))
    recalled = NOTES.replace("VERIFIED", "RECALLED")
    assert any("not marked VERIFIED" in w for w in handoff_check.check(quoted, recalled))
