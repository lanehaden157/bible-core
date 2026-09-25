"""Which version of the core a unit was written against (review D7).

The porter stamps `contract` (the core version doing the port) into a new
unit's meta block and its units.json row. Validation then runs only the
checks that existed at that version, so a check added later never fails a
unit that shipped before it. To hold an older unit to newer rules, run its
migrations (`python -m biblecore migrate`), which move the stamp forward.

Units ported before 0.3.0 carry no stamp and count as UNSTAMPED.
"""
import re

from biblecore import __version__

UNSTAMPED = "0.2.0"
_VER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse(v):
    m = _VER_RE.match(v or "")
    if not m:
        raise ValueError(f"not a core version: {v!r} (want 'X.Y.Z')")
    return tuple(int(x) for x in m.groups())


def is_version(v):
    return isinstance(v, str) and bool(_VER_RE.match(v))


def of(meta_or_row):
    """The unit's contract version, or UNSTAMPED."""
    v = (meta_or_row or {}).get("contract")
    return v if is_version(v) else UNSTAMPED


def at_least(contract, since):
    return parse(contract) >= parse(since)


def current():
    return __version__


def check_stamp(contract):
    """Problems with a stamp itself: malformed, or newer than this core
    (a unit ported by a newer core than the one validating it)."""
    if contract is None:
        return []
    if not is_version(contract):
        return [f"contract {contract!r} is not a core version 'X.Y.Z'"]
    if parse(contract) > parse(__version__):
        return [f"contract {contract} is newer than this core ({__version__}); "
                f"re-vendor bible-core before validating this unit"]
    return []
