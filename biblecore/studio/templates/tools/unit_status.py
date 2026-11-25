"""Where each unit stands, read from the files (no state is stored).

    python tools/unit_status.py          # every unit
    python tools/unit_status.py 20       # one unit

Vendored from bible-core (studio); the book's copy is overwritten on sync.
Looks in this checkout and every .claude/worktrees/* checkout and reports the
furthest stage found for each unit, with where it was found. Shipped = the
unit's study files are on origin/main (a unit built under an older flow
counts as "built (old flow)" until its study ships).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT
if ROOT.parent.name == "worktrees" and ROOT.parent.parent.name == ".claude":
    MAIN = ROOT.parent.parent.parent

STAGES = ["not started", "researched", "briefed", "verse by verse", "fact-checked",
          "awaiting calls", "calls answered", "built", "shipped"]


def on_main(path):
    r = subprocess.run(["git", "-C", str(MAIN), "cat-file", "-e", f"origin/main:{path}"],
                       capture_output=True)
    return r.returncode == 0


def units():
    data = json.loads((MAIN / "data" / "units.json").read_text("utf-8"))["units"]
    return {u["n"]: u.get("tier", "full") for u in data}


def stage(root, n, tier):
    w = root / "work" / f"{n:02d}"
    h = w / "calls.md"
    if (w / "built").exists():
        return 7
    if h.exists():
        text = h.read_text("utf-8")
        answers = re.search(r"^## Answers\s*\n(.+)", text, re.M | re.S)
        return 6 if answers and answers.group(1).strip() else 5
    steps = [(4, "factcheck.md"), (2, "briefing.md"), (1, "notes.md")]
    if tier == "full":
        steps.insert(1, (3, "verse-by-verse.md"))
    for i, f in steps:
        if (w / f).exists():
            return i
    return 0


def calls(root, n):
    h = root / "work" / f"{n:02d}" / "calls.md"
    m = h.exists() and re.search(r"^## Calls for Lane \((\d+)\)", h.read_text("utf-8"), re.M)
    return m.group(1) if m else ""


def main(only):
    roots = [MAIN] + sorted((MAIN / ".claude" / "worktrees").glob("*/"))
    for n, tier in units().items():
        if only and n not in only:
            continue
        t = "" if tier == "full" else f" ({tier})"
        if on_main(f"work/{n:02d}/built"):
            print(f"{n:2d}{t}  shipped")
            continue
        best, where = 0, ""
        for r in roots:
            s = stage(r, n, tier)
            if s > best:
                best, where = s, ("main" if r == MAIN else r.name)
        root = MAIN if where == "main" else MAIN / ".claude" / "worktrees" / where
        extra = f"  ({calls(root, n)} calls)" if best == 5 else ""
        old = "  [built (old flow)]" if best == 0 and on_main(f"units/unit-{n:02d}.html") else ""
        print(f"{n:2d}{t}  {STAGES[best]}" + (f"  [{where}]" if where else "") + extra + old)


if __name__ == "__main__":
    main({int(a) for a in sys.argv[1:]})
