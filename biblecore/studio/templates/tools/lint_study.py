"""Mechanical checks on a unit's study files, so the fact-checker doesn't spend turns on them.

    python tools/lint_study.py N

Vendored from bible-core (studio); the book's copy is overwritten on sync.

work/NN/briefing.md and verse-by-verse.md (read aloud): no native Hebrew or Greek
script, digits, bullets, bold, tables or headings with "#"; briefing length by tier
(full 600-900 words, condensed/digest 300-500; no verse-by-verse then).
work/NN/notes.md: no native script; every link-table row has 8 cells with a known
status, strength and verdict. Exit 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
NATIVE = re.compile("[Ͱ-Ͽἀ-῿֐-׿]")
STATUS = {"VERIFIED", "ENGLISH", "SHEET", "SECONDHAND", "RECALLED"}
STRENGTH = {"strong", "possible", "weak"}


def tier(n):
    for u in json.loads((ROOT / "data" / "units.json").read_text("utf-8"))["units"]:
        if u["n"] == n:
            return u.get("tier", "full")
    return "full"


def spoken(path):
    fails = []
    for i, ln in enumerate(path.read_text("utf-8").splitlines(), 1):
        for pat, what in ((NATIVE, "native script"), (r"\d", "a digit"), (r"^\s*([-*•]|\d+\.)\s", "a bullet"),
                          (r"\*\*|__", "bold"), (r"^\s*\|", "a table"), (r"^\s*#", "a # heading")):
            if re.search(pat, ln):
                fails.append(f"{path.name}:{i}: {what}")
                break
    return fails


def notes(path):
    fails = []
    text = path.read_text("utf-8")
    if NATIVE.search(text):
        fails.append(f"{path.name}: native script")
    for i, ln in enumerate(text.splitlines(), 1):
        if not ln.startswith("|") or ln.startswith("|---") or ln.startswith("| verse"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != 8:
            if len(cells) > 3 and cells[-1][:4] in ("ship", "tent", "drop"):
                fails.append(f"{path.name}:{i}: {len(cells)} cells, want 8")
            continue
        if cells[5].split()[0].upper() not in STATUS and not any(s in cells[5].upper() for s in STATUS):
            fails.append(f"{path.name}:{i}: status {cells[5]!r}")
        if cells[6].lower() not in STRENGTH:
            fails.append(f"{path.name}:{i}: strength {cells[6]!r}")
        if not re.match(r"(ship|tentative|drop)", cells[7].lower()):
            fails.append(f"{path.name}:{i}: verdict {cells[7]!r}")
    return fails


def main(a):
    n = int(a[0])
    d = ROOT / "work" / f"{n:02d}"
    t = tier(n)
    fails = []
    for name in ("briefing.md", "verse-by-verse.md"):
        f = d / name
        if f.exists():
            fails += spoken(f)
    b = d / "briefing.md"
    if b.exists():
        words = len(b.read_text("utf-8").split())
        lo, hi = (600, 900) if t == "full" else (300, 500)
        if not lo <= words <= hi:
            fails.append(f"briefing.md: {words} words, {t} tier wants {lo}-{hi}")
    if t != "full" and (d / "verse-by-verse.md").exists():
        fails.append("verse-by-verse.md: only full-tier units have one")
    if (d / "notes.md").exists():
        fails += notes(d / "notes.md")
    print("\n".join(fails) if fails else "study files: ok")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
