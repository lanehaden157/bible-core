"""Which version of the core a unit was written against (review D7).

The porter stamps `contract` (the core version doing the port) into a new
unit's meta block and its units.json row. Validation then runs only the
checks that existed at that version, so a check added later never fails a
unit that shipped before it. To hold an older unit to newer rules, run its
migrations (`python -m biblecore migrate`), which move the stamp forward.

Units ported before 0.3.0 carry no stamp and count as UNSTAMPED.

A unit may instead be stamped `legacy`: it was built before the book moved
onto core and is boxed as it shipped. It is held to no versioned fragment
check (every check arrived at some version, and a legacy unit is older than
all of them), and `migrate` leaves it alone. Only a book's older units get
this stamp; it is set by hand in the unit's `units.json` row and meta block,
never by the porter, so a new unit can't slip into it and a book-wide
`skip_fragment_checks` isn't needed to excuse the old ones.
"""
import re

from biblecore import __version__

UNSTAMPED = "0.2.0"
LEGACY = "legacy"
_VER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse(v):
    m = _VER_RE.match(v or "")
    if not m:
        raise ValueError(f"not a core version: {v!r} (want 'X.Y.Z')")
    return tuple(int(x) for x in m.groups())


def is_version(v):
    return isinstance(v, str) and bool(_VER_RE.match(v))


def of(meta_or_row):
    """The unit's contract version, LEGACY, or UNSTAMPED."""
    v = (meta_or_row or {}).get("contract")
    return v if v == LEGACY or is_version(v) else UNSTAMPED


def is_legacy(contract):
    return contract == LEGACY


def at_least(contract, since):
    if is_legacy(contract):
        return False
    return parse(contract) >= parse(since)


def current():
    return __version__


def check_stamp(contract):
    """Problems with a stamp itself: malformed, or newer than this core
    (a unit ported by a newer core than the one validating it)."""
    if contract is None or is_legacy(contract):
        return []
    if not is_version(contract):
        return [f"contract {contract!r} is not a core version 'X.Y.Z' (or 'legacy')"]
    if parse(contract) > parse(__version__):
        return [f"contract {contract} is newer than this core ({__version__}); "
                f"re-vendor bible-core before validating this unit"]
    return []
