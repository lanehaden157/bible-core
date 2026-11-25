"""The book's memory of its own mistakes: lessons.jsonl.

    python tools/lessons.py known                       # keys + one line each: read before you start
    python tools/lessons.py add KEY --unit N --stage S --owner O --what "..." [--fix "..."]
    python tools/lessons.py report                      # recurring keys, by who should change what
    python tools/lessons.py resolve KEY --note "changed X in Y"

Vendored from bible-core (studio); the book's copy is overwritten on sync.

An entry is one kind of mistake seen in one unit. KEY is a short kebab slug for
the *kind* (`commentator-misattributed`, `quote-not-verified`), reused every
time the kind comes back; that is what lets a repeat be noticed. --stage:
study | factcheck | build | tools. --owner = where the fix belongs:

    book   this book's CLAUDE.md, lens.md or translation-choices.md (a unit session fixes it)
    core   a skill, agent, tool or pack (bible-core: report it, don't edit .claude/ here)
    source a source file or converter (tools/sources/)

A key is *recurring* when it was seen in 2+ units (or 3+ times) and is not
resolved. A key seen again after `resolve` is a REGRESSION: the fix did not
hold, so say so and try something else. Only the tool writes the file.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
FILE = Path(__file__).resolve().parent.parent / "lessons.jsonl"
STAGES = ("study", "factcheck", "build", "tools")
OWNERS = ("book", "core", "source")


def load():
    if not FILE.exists():
        return []
    return [json.loads(x) for x in FILE.read_text("utf-8").splitlines() if x.strip()]


def save(rec):
    with open(FILE, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def by_key(rows):
    """{key: {'seen': [rows], 'resolved': last resolve row | None, 'after': seen rows after it}}"""
    out = {}
    for r in rows:
        k = out.setdefault(r["key"], {"seen": [], "resolved": None, "after": []})
        if r.get("resolve"):
            k["resolved"], k["after"] = r, []
        else:
            k["seen"].append(r)
            if k["resolved"]:
                k["after"].append(r)
    return out


def status(k):
    seen = [r for r in k["seen"]]
    live = k["after"] if k["resolved"] else seen
    units = {r.get("unit") for r in live}
    if k["resolved"] and k["after"]:
        return "REGRESSION"
    if k["resolved"]:
        return "resolved"
    return "RECURRING" if len(units) >= 2 or len(live) >= 3 else "seen once"


def cmd_known(rows):
    ks = by_key(rows)
    if not ks:
        print("No lessons yet.")
    for key, k in sorted(ks.items()):
        last = (k["after"] or k["seen"])[-1]
        mark = "" if status(k) == "seen once" else f" [{status(k)}]"
        fix = k["resolved"]["note"] if k["resolved"] else last.get("fix", "")
        print(f"- {key}{mark}: {last['what']}" + (f" Do: {fix}" if fix else ""))


def cmd_report(rows):
    ks = by_key(rows)
    act = {key: k for key, k in ks.items() if status(k) in ("RECURRING", "REGRESSION")}
    print(f"{len(ks)} kinds of mistake, {len(act)} to act on.")
    for owner in OWNERS:
        mine = {key: k for key, k in act.items() if (k["seen"][-1].get("owner") == owner)}
        if not mine:
            continue
        print(f"\n## owner: {owner}")
        for key, k in sorted(mine.items()):
            live = k["after"] or k["seen"]
            units = sorted({r.get("unit") for r in live if r.get("unit") is not None})
            print(f"- {key} [{status(k)}] units {units}, {len(live)} times")
            for r in live[-3:]:
                print(f"    unit {r.get('unit')} ({r.get('stage')}): {r['what']}")
            fixes = [r["fix"] for r in live if r.get("fix")]
            if fixes:
                print(f"    suggested fix: {fixes[-1]}")
            if k["resolved"]:
                print(f"    earlier fix that did not hold: {k['resolved']['note']}")
    quiet = [key for key in ks if key not in act and status(ks[key]) == "seen once"]
    if quiet:
        print("\nSeen once (no action yet): " + ", ".join(sorted(quiet)))
    if act:
        print("\nNext: owner book → edit that file now, then `resolve`; owner core or source → "
              "tell Lane, with these lines as the brief for a bible-core / source session.")


def main(a):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("known")
    sub.add_parser("report")
    p = sub.add_parser("add")
    p.add_argument("key")
    p.add_argument("--unit", type=int, required=True)
    p.add_argument("--stage", choices=STAGES, required=True)
    p.add_argument("--owner", choices=OWNERS, required=True)
    p.add_argument("--what", required=True)
    p.add_argument("--fix", default="")
    p = sub.add_parser("resolve")
    p.add_argument("key")
    p.add_argument("--note", required=True)
    n = ap.parse_args(a)
    rows = load()
    if n.cmd == "known":
        cmd_known(rows)
    elif n.cmd == "report":
        cmd_report(rows)
    elif n.cmd == "add":
        if any(r["key"] == n.key and r.get("unit") == n.unit and r["what"] == n.what and not r.get("resolve")
               for r in rows):
            print("already recorded")
            return
        save({"date": datetime.date.today().isoformat(), "key": n.key, "unit": n.unit, "stage": n.stage,
              "owner": n.owner, "what": n.what, "fix": n.fix})
        k = by_key(load())[n.key]
        print(f"recorded {n.key} (unit {n.unit}): {status(k)}")
    else:
        if n.key not in by_key(rows):
            sys.exit(f"no lesson with key {n.key!r}; keys: {', '.join(sorted(by_key(rows)))}")
        save({"date": datetime.date.today().isoformat(), "key": n.key, "resolve": True, "note": n.note})
        print(f"resolved {n.key}")


if __name__ == "__main__":
    main(sys.argv[1:])
