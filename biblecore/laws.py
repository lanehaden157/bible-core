"""Laws: one law restated in several places (Exodus, Leviticus, Numbers,
Deuteronomy), as data, a check, a box (`lawparallel`) and a hub page.

    python -m biblecore.laws [FILE]      # check the laws file (default: biblecore/laws.json)

The file is POLICY, like threads.json: a human adds a law, the validator
checks it. It lives in the package (biblecore/laws.json, source of truth in
bible-core) so every book that is vendored checks a box against the same
file the hub draws its law index from.

    {"version": 1,
     "laws": [{"id": "release-of-slaves",              # [a-z0-9-], unique
               "title": "...", "note"?: "...",
               "passages": [                           # Bible order, no overlap, 2 or more
                 {"ref": "Exod 21:2–6",                # one span of one book
                  "summary": "what this passage says",
                  "differences": ["how it differs from the others"],   # required, 1+
                  "reasons": [{"at": "Exod 21:5", "why": "the text's own 'because'"}],
                  "footnote"?: "a dating or source debate goes only here"}]}]}

A box makes no claim this file doesn't hold. Differences and reasons are the
text's own: a dating or source argument in any other field fails the check.
"""
import json
import os
import re

from biblecore import mirror as mr
from biblecore.corpus import oshb

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laws.json")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOP_KEYS = {"_note", "version", "laws"}
LAW_KEYS = {"id", "title", "note", "passages"}
PASSAGE_KEYS = {"ref", "summary", "differences", "reasons", "footnote"}
REASON_KEYS = {"at", "why"}
MAX_SUMMARY = 280
# Source-critical dating arguments belong in `footnote` only.
DATING_RE = re.compile(
    r"\b(pre-?exilic|post-?exilic|redact\w*|Priestly (?:source|writer|school|stratum)|"
    r"Deuteronomic (?:school|redact\w*|author)|Holiness Code|Covenant Code|"
    r"documentary hypothesis|JEDP|\bP source|\bD source|\bH source|"
    r"(?:earlier|later|older|younger) (?:than|law)|dated to|composed (?:in|after|before))", re.I)


def load(path=None):
    with open(path or PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _order(sp):
    return (oshb.BOOK_IDS.index(sp[0]), sp[1], sp[2])


def validate(data):
    """Problems with a laws file (a list of strings, empty when sound)."""
    errs = []
    if not isinstance(data, dict):
        return ["laws file must be an object {version, laws}"]
    for k in sorted(set(data) - TOP_KEYS):
        errs.append(f"unknown top-level key '{k}'")
    if data.get("version") != 1:
        errs.append("'version' must be 1")
    laws = data.get("laws")
    if not isinstance(laws, list):
        return errs + ["'laws' must be a list"]
    seen = set()
    for i, law in enumerate(laws):
        where = f"laws[{i}]"
        if not isinstance(law, dict):
            errs.append(f"{where}: must be an object")
            continue
        lid = law.get("id")
        where = f"law {lid!r}" if isinstance(lid, str) else where
        if not isinstance(lid, str) or not ID_RE.match(lid):
            errs.append(f"{where}: 'id' must match [a-z0-9-] (e.g. 'release-of-slaves')")
        elif lid in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(lid)
        for k in sorted(set(law) - LAW_KEYS):
            errs.append(f"{where}: unknown key '{k}'")
        if not str(law.get("title", "")).strip():
            errs.append(f"{where}: needs a 'title'")
        ps = law.get("passages")
        if not isinstance(ps, list) or len(ps) < 2:
            errs.append(f"{where}: needs 2 or more passages (a law that stands in one place has no parallel)")
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
        errs.append(f"{where}: ref {p.get('ref')!r} is not one span of one book, like 'Exod 21:2–6'")
    else:
        if prev is not None and _order(sp) <= _order(prev):
            errs.append(f"{where}: {p['ref']} is not after the one before it (Bible order, no overlap)")
    summ = p.get("summary")
    if not isinstance(summ, str) or not summ.strip():
        errs.append(f"{where}: needs a 'summary'")
    elif len(summ) > MAX_SUMMARY:
        errs.append(f"{where}: summary is {len(summ)} characters, keep it under {MAX_SUMMARY}")
    diffs = p.get("differences")
    if (not isinstance(diffs, list) or not diffs
            or not all(isinstance(d, str) and d.strip() for d in diffs)):
        errs.append(f"{where}: 'differences' must be a list of 1 or more statements "
                    f"(how this passage differs from the others)")
    reasons = p.get("reasons", [])
    if not isinstance(reasons, list):
        errs.append(f"{where}: 'reasons' must be a list of {{at, why}}")
        reasons = []
    for k, r in enumerate(reasons, 1):
        rw = f"{where} reason {k}"
        if not isinstance(r, dict):
            errs.append(f"{rw}: must be {{at, why}}")
            continue
        for key in sorted(set(r) - REASON_KEYS):
            errs.append(f"{rw}: unknown key '{key}'")
        at = mr.parse_span(r.get("at"))
        if at is None:
            errs.append(f"{rw}: 'at' {r.get('at')!r} is not a verse reference")
        elif sp and not mr.contains(sp, at):
            errs.append(f"{rw}: 'at' {r['at']} is outside {p['ref']}")
        if not isinstance(r.get("why"), str) or not r["why"].strip():
            errs.append(f"{rw}: needs 'why' (the text's own reason)")
    if "footnote" in p and not (isinstance(p["footnote"], str) and p["footnote"].strip()):
        errs.append(f"{where}: 'footnote' must be a non-empty string")
    texts = [summ] + (diffs if isinstance(diffs, list) else []) + [
        r.get("why") for r in reasons if isinstance(r, dict)]
    for t in texts:
        if isinstance(t, str) and DATING_RE.search(t):
            errs.append(f"{where}: dating or source argument ({DATING_RE.search(t).group(0)!r}) "
                        f"belongs in 'footnote' only")
    return errs


def table(data=None):
    """{law id: law} for the laws file."""
    data = data if data is not None else load()
    return {law["id"]: law for law in data.get("laws", [])}


def passage_of(law, ref):
    """The passage of `law` whose ref text equals `ref` (en dash or hyphen)."""
    want = mr.parse_span(ref)
    for p in law["passages"]:
        if want and mr.parse_span(p["ref"]) == want:
            return p
    return None


def containing(law, span):
    """The passage of `law` that contains span (a mirror.parse_span tuple)."""
    for p in law["passages"]:
        sp = mr.parse_span(p["ref"])
        if sp and mr.contains(sp, span):
            return p
    return None


def main(argv=None):
    import sys
    path = (argv if argv is not None else sys.argv[1:] or [None])[0]
    data = load(path)
    errs = validate(data)
    for e in errs:
        print("  " + e)
    n = len(data.get("laws", []))
    print(f"laws: {n} law(s), {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
