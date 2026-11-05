"""Lint for a verse chat's handoff file (canon/handoff-template.md).

    python -m biblecore handoff-check <book>_NN_handoff.md [<book>_NN_notes.md]

Warns about: a missing or out-of-order template section; native Hebrew or Greek
script; a story or parallel box missing a field, an anchor outside the unit, or
a ref without verses; an "Approved boxes" count line that doesn't add up; and,
when the notes file is given, a quoted passage in a box that the notes don't
mark VERIFIED, or a row count that differs from the notes'. It also keeps the
original "Calls for Lane" checks: missing, "none" or empty while the text still
mentions a provisional or "to flag" rendering, a heading count that differs
from the numbered calls, or a provisional line outside the section.

Warnings only: exit status is 0, the check is advice for Lane, not a gate on
the build.
"""
import re
import sys

_HEAD = re.compile(r"^##\s+(?:Calls for Lane|Questions for Lane)\b(.*)$", re.I | re.M)
_NEXT = re.compile(r"^##\s", re.M)
_CALL = re.compile(r"^\s*(?:\*\*)?(?:Call\s+)?(\d+)[.)]", re.I | re.M)
_FLAG = re.compile(r"provisional|to flag", re.I)

SECTIONS = ["Scope", "Verse by verse", "Approved boxes", "Decisions", "Threads",
            "Calls for Lane", "Checks for code", "Source status"]
_SECTION_RE = re.compile(r"^##\s+(.*?)\s*$", re.M)
_SCRIPT = re.compile(r"[֐-׿Ͱ-Ͽἀ-῿]")
_CV = re.compile(r"\d+:\d+")
BOX_FIELDS = ("Kind", "Anchor", "Ref", "Story", "Same", "Different", "Does")
_FULL_KINDS = ("story", "parallel", "synoptic")
_COUNT = re.compile(r"(\d+)\s+rows?\s+considered\D+(\d+)\s+ship\D+(\d+)\s+dropped", re.I)
_QUOTE = re.compile(r"[\"“]([^\"”“]{12,}?)[\"”]")


def _sections(text):
    """[(canonical name or raw heading, body)] in order."""
    ms = list(_SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        name = m.group(1)
        for s in SECTIONS:
            if name.lower().startswith(s.lower()) or (
                    s == "Calls for Lane" and name.lower().startswith("questions for lane")):
                name = s
                break
        out.append((name, text[m.end():end]))
    return out


def _unit_range(scope):
    m = re.search(r"(\d+):(\d+)\s*[-–—]\s*(?:(\d+):)?(\d+)", scope)
    if not m:
        return None
    c1, v1 = int(m.group(1)), int(m.group(2))
    return (c1, v1), (int(m.group(3)) if m.group(3) else c1, int(m.group(4)))


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def _boxes(body):
    """[(title, {field: text})] for each ### block in Approved boxes."""
    parts = re.split(r"^###\s+", body, flags=re.M)[1:]
    out = []
    for p in parts:
        title, _nl, rest = p.partition("\n")
        fields = {}
        for f in BOX_FIELDS:
            m = re.search(rf"\*\*{f}[:.]?\*\*[:.]?\s*(.*?)(?=\n\s*[-*]?\s*\*\*(?:{'|'.join(BOX_FIELDS)})|\Z)",
                          rest, re.S | re.I)
            if m and m.group(1).strip():
                fields[f] = m.group(1).strip()
        out.append((title.strip(), fields))
    return out


def _calls_warnings(text):
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


def _notes_rows(notes):
    """(row count the notes state, [(normalised line, verified?)])."""
    stated = None
    for m in re.finditer(r"(\d+)\s+rows?\b", notes, re.I):
        stated = int(m.group(1))        # the last one: the closing count line
    lines = [(_norm(ln), "VERIFIED" in ln.upper()) for ln in notes.splitlines() if ln.strip()]
    return stated, lines


def check(text, notes=None):
    """List of warning strings for a handoff's text (and, optionally, the
    notes file's text)."""
    warns = []
    secs = _sections(text)
    names = [n for n, _b in secs]
    last = -1
    for want in SECTIONS:
        if want == "Calls for Lane":
            continue                    # reported with its own, richer messages
        if want not in names:
            warns.append(f'missing section "{want}" (leave it in with "none" if empty)')
        else:
            i = names.index(want)
            if i < last:
                warns.append(f'section "{want}" is out of template order')
            last = max(last, i)
    body = dict(secs)

    if _SCRIPT.search(text):
        ln = next(l for l in text.splitlines() if _SCRIPT.search(l))
        warns.append("native Hebrew or Greek script in the handoff (transliterate): " + ln.strip()[:60])

    scope = body.get("Scope", "")
    span = _unit_range(scope)
    boxes = _boxes(body.get("Approved boxes", ""))
    for title, f in boxes:
        label = f'box "{title[:40] or "(untitled)"}"'
        if not title:
            warns.append(f"{label}: no title")
        kind = (f.get("Kind") or "").lower()
        need = BOX_FIELDS if any(k in kind for k in _FULL_KINDS) else ("Kind", "Anchor", "Ref", "Does")
        miss = [x for x in need if x not in f]
        if miss:
            warns.append(f"{label}: missing {', '.join(miss)}")
        if "Ref" in f and not _CV.search(f["Ref"]):
            warns.append(f"{label}: Ref names no verses")
        if "Anchor" in f:
            m = _CV.search(f["Anchor"])
            if not m:
                warns.append(f"{label}: Anchor is not a C:V")
            elif span:
                c, v = (int(x) for x in m.group(0).split(":"))
                if not span[0] <= (c, v) <= span[1]:
                    warns.append(f"{label}: Anchor {m.group(0)} is outside the unit")

    cm = _COUNT.search(body.get("Approved boxes", ""))
    if not cm:
        if "Approved boxes" in body:
            warns.append('"Approved boxes" has no count line ("N rows considered, M ship, K dropped")')
    else:
        n, ship, drop = (int(x) for x in cm.groups())
        if n != ship + drop:
            warns.append(f"count line says {n} considered but {ship} ship + {drop} dropped = {ship + drop}")
        if len(boxes) > ship:
            warns.append(f"{len(boxes)} boxes but only {ship} ship in the count line")

    if notes is not None:
        stated, nlines = _notes_rows(notes)
        hm = re.search(r"Notes:\s*(\d+)\s+rows?", scope, re.I)
        if stated is not None and hm and int(hm.group(1)) != stated:
            warns.append(f"Scope says the notes have {hm.group(1)} rows but the notes file ends with {stated}")
        elif stated is not None and not hm:
            warns.append('Scope has no "Notes: N rows" line to check against the notes file')
        for title, f in boxes:
            for fld, val in f.items():
                for q in _QUOTE.findall(val):
                    nq = _norm(q)
                    hit = [ver for ln, ver in nlines if nq and nq in ln]
                    if not hit:
                        warns.append(f'box "{title[:40]}": quoted text not in the notes: "{q[:50]}"')
                    elif not any(hit):
                        warns.append(f'box "{title[:40]}": quote is in the notes but not marked VERIFIED: "{q[:50]}"')

    return warns + _calls_warnings(text)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) not in (1, 2):
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        text = fh.read()
    notes = None
    if len(argv) == 2:
        with open(argv[1], encoding="utf-8") as fh:
            notes = fh.read()
    warns = check(text, notes)
    for w in warns:
        print("warning: " + w)
    if not warns:
        print("handoff-check: ok")
    return 0
