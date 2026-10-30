"""Lint for a research chat's handoff file (canon/handoff-template.md).

    python -m biblecore handoff-check <book>_NN_handoff.md

Warns when "Calls for Lane" is missing, says "none" or has no numbered call
while the rest of the handoff still mentions a provisional or "to flag"
rendering, when the heading's count differs from the numbered calls, or when
a line outside the section marks something provisional. Warnings only: exit
status is 0, the check is advice for Lane, not a gate on the build.
"""
import re
import sys

_HEAD = re.compile(r"^##\s+(?:Calls for Lane|Questions for Lane)\b(.*)$", re.I | re.M)
_NEXT = re.compile(r"^##\s", re.M)
_CALL = re.compile(r"^\s*(?:\*\*)?(?:Call\s+)?(\d+)[.)]", re.I | re.M)
_FLAG = re.compile(r"provisional|to flag", re.I)


def check(text):
    """List of warning strings for a handoff's text."""
    m = _HEAD.search(text)
    if not m:
        return ['no "Calls for Lane" section (leave it in with "none" if empty)']
    rest = text[m.end():]
    nxt = _NEXT.search(rest)
    body = rest[:nxt.start()] if nxt else rest
    outside = text[:m.start()] + (rest[nxt.start():] if nxt else "")
    calls = {int(n) for n in _CALL.findall(body)}
    says_none = re.match(r"\s*none\b", body, re.I) is not None
    warns = []
    hits = [ln.strip() for ln in outside.splitlines() if _FLAG.search(ln)]
    if (says_none or not calls) and (hits or _FLAG.search(body)):
        warns.append('"Calls for Lane" is none/empty but the text mentions a '
                     'provisional rendering: ' + (hits[0] if hits else body.strip())[:80])
    elif hits:
        warns.append(f"{len(hits)} line(s) outside the section mention a provisional "
                     f"rendering; each needs a numbered call (first: {hits[0][:80]})")
    count = re.search(r"\((\d+)\)", m.group(1))
    if count and int(count.group(1)) != len(calls):
        warns.append(f'heading says ({count.group(1)}) but {len(calls)} numbered call(s) found')
    return warns


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        warns = check(fh.read())
    for w in warns:
        print("warning: " + w)
    if not warns:
        print("handoff-check: ok")
    return 0
