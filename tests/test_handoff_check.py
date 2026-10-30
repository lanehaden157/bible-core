"""handoff-check: a handoff can't say "none" while it still has provisional renderings."""
from biblecore import handoff_check

OK = "## Verse by verse\n- 3: see Call 1\n\n## Calls for Lane (1)\n\n1. v3 'x' or 'y'.\n\n## Checks for code\nnone\n"
NONE = "## Verse by verse\n- 3: 'x' (provisional)\n\n## Calls for Lane\n\nnone\n"


def test_ok():
    assert handoff_check.check(OK) == []


def test_none_with_provisional():
    assert any("none/empty" in w for w in handoff_check.check(NONE))


def test_count_mismatch():
    assert any("heading says" in w for w in handoff_check.check(OK.replace("(1)", "(3)")))


def test_missing_section():
    assert handoff_check.check("## Scope\nx\n")
