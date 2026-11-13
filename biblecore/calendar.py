"""Calendar: the appointed times as Lev 23, Num 28-29 and Deut 16 each give
them, side by side. Data, a check, a box (`calendar`).

    python -m biblecore.calendar [FILE]   # check the calendar (default: biblecore/calendar.json)

The file is POLICY, like laws.json: a human adds a feast, the validator
checks it. It lives in the package (source of truth in bible-core), so every
vendored book checks a box against the same file.

    {"version": 1,
     "feasts": [{"id": "passover",                 # [a-z0-9-], unique
                 "title": "Passover",
                 "note"?: "...",
                 "passages": [                      # Bible order, no overlap, 1 or more
                   {"ref": "Lev 23:5",              # one span of one book
                    "date": "first month, fourteenth day, at twilight",   # as the passage gives it
                    "requires": ["what the passage requires"]}]}]}   # 1+ statements

Rows come from the verses: `date` and `requires` are the passage's own
statements, in the book's terms; a feast the passage does not date has no
`date` (leave it out, never guess). A box makes no claim the file doesn't hold.
"""
import json
import os
import re

from biblecore import laws, mirror as mr

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar.json")
ID_RE = laws.ID_RE
TOP_KEYS = {"_note", "version", "feasts"}
FEAST_KEYS = {"id", "title", "note", "passages"}
PASSAGE_KEYS = {"ref", "date", "requires"}
MAX_STATEMENT = 280


def load(path=None):
    with open(path or PATH, encoding="utf-8") as fh:
        return json.load(fh)


def validate(data):
    """Problems with a calendar file (a list of strings, empty when sound)."""
    errs = []
    if not isinstance(data, dict):
        return ["calendar file must be an object {version, feasts}"]
    for k in sorted(set(data) - TOP_KEYS):
        errs.append(f"unknown top-level key '{k}'")
    if data.get("version") != 1:
        errs.append("'version' must be 1")
    feasts = data.get("feasts")
    if not isinstance(feasts, list):
        return errs + ["'feasts' must be a list"]
    seen = set()
    for i, f in enumerate(feasts):
        where = f"feasts[{i}]"
        if not isinstance(f, dict):
            errs.append(f"{where}: must be an object")
            continue
        fid = f.get("id")
        where = f"feast {fid!r}" if isinstance(fid, str) else where
        if not isinstance(fid, str) or not ID_RE.match(fid):
            errs.append(f"{where}: 'id' must match [a-z0-9-] (e.g. 'day-of-coverings')")
        elif fid in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(fid)
        for k in sorted(set(f) - FEAST_KEYS):
            errs.append(f"{where}: unknown key '{k}'")
        if not str(f.get("title", "")).strip():
            errs.append(f"{where}: needs a 'title'")
        if "note" in f and not (isinstance(f["note"], str) and f["note"].strip()):
            errs.append(f"{where}: 'note' must be a non-empty string")
        ps = f.get("passages")
        if not isinstance(ps, list) or not ps:
            errs.append(f"{where}: needs 1 or more passages")
            continue
        prev = None
        for j, p in enumerate(ps):
            errs += _passage(f"{where} passage {j + 1}", p, prev)
            sp = mr.parse_span(p.get("ref")) if isinstance(p, dict) else None
            prev = sp if sp else prev
    return errs


def _passage(where, p, prev):
    errs = []
    if not isinstance(p, dict):
        return [f"{where}: must be an object"]
    for k in sorted(set(p) - PASSAGE_KEYS):
        errs.append(f"{where}: unknown key '{k}'")
    sp = mr.parse_span(p.get("ref"))
    if sp is None:
        errs.append(f"{where}: ref {p.get('ref')!r} is not one span of one book, like 'Lev 23:5–8'")
    elif prev is not None and laws._order(sp) <= laws._order(prev):
        errs.append(f"{where}: {p['ref']} is not after the one before it (Bible order, no overlap)")
    if "date" in p and not (isinstance(p["date"], str) and p["date"].strip()):
        errs.append(f"{where}: 'date' must be a non-empty string (or left out when the passage gives none)")
    req = p.get("requires")
    if (not isinstance(req, list) or not req
            or not all(isinstance(r, str) and r.strip() for r in req)):
        errs.append(f"{where}: 'requires' must be a list of 1 or more statements")
        req = []
    for t in ([p.get("date")] if isinstance(p.get("date"), str) else []) + req:
        if len(t) > MAX_STATEMENT:
            errs.append(f"{where}: a statement is {len(t)} characters, keep it under {MAX_STATEMENT}")
        m = laws.DATING_RE.search(t)
        if m:
            errs.append(f"{where}: dating or source argument ({m.group(0)!r}) has no place here")
    return errs


def table(data=None):
    """{feast id: feast} for the calendar file."""
    data = data if data is not None else load()
    return {f["id"]: f for f in data.get("feasts", [])}


def passage_of(feast, ref):
    """The passage of `feast` whose ref equals `ref` (en dash or hyphen)."""
    want = mr.parse_span(ref)
    for p in feast["passages"]:
        if want and mr.parse_span(p["ref"]) == want:
            return p
    return None


def main(argv=None):
    import sys
    path = (argv if argv is not None else sys.argv[1:] or [None])[0]
    data = load(path)
    errs = validate(data)
    for e in errs:
        print("  " + e)
    print(f"calendar: {len(data.get('feasts', []))} feast(s), {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
