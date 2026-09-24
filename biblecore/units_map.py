"""Load unit rows and groupings from the project side's literary unit map.

    python -m biblecore units-from-map                 # finds *unit*map*.md
    python -m biblecore units-from-map MAP.md --dry    # show, write nothing
    python -m biblecore units-from-map --kinds part,movement

Stage two of starting a book (stage one is bible-core's tools/new_book.py):
the map arrives from the project side after bootstrap, and `leads` has
nothing to work from until units.json has a row for the next unit. (learned:
Numbers' canon leads came back empty until unit 1's row was added by hand.)

Reads the map's Overview table, the layout Numbers' map uses:

    | # | Passage | Working title |
    |---|---|---|
    | | **PART ONE — The generation of the exodus (1:1–25:18)** | |
    | | *I. At Sinai: ordering the camp (1:1–10:10)* | |
    | 01 | 1:1–54 | The first accounting |
    | 17 | 16:36–17:13 [Heb 17:1–28] | Two memorials |

A bold row opens an outer grouping, an italic row an inner one. `--kinds`
names them outer to inner; without it, book.json's `groupings` read
innermost first (the order the site's book map wants). A map with no
heading rows is fine: units only.

Additive, so it's safe to re-run as the map grows: existing unit rows are
never touched (a built unit's row belongs to the porter), existing
groupings are kept and only compared, and anything it can't read is
reported rather than guessed. A `[Heb ...]` bracket is dropped from the
passage (which stays in English numbering; versify.py converts) and reported.
"""
import argparse
import glob
import json
import os
import re
import sys

from biblecore.book import book

ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")
HEAD_RE = re.compile(r"^\|\s*\|\s*(\*\*|\*)(.+?)\1\s*\|\s*\|\s*$")
SPAN_RE = re.compile(r"\s*\(([^()]*\d+:\d+[^()]*)\)\s*$")
HEB_RE = re.compile(r"\s*\[\s*Heb\.?\s+([^\]]+)\]\s*")
NUMERAL_RE = re.compile(r"^(?:[IVXLC]+|\d+)\.\s+")
DASH_RE = re.compile(r"\s+[—–-]\s+")
STOP = {"the", "a", "an", "of", "and", "to", "on", "in"}


def find_map(root):
    hits = sorted(glob.glob(os.path.join(root, "*unit*map*.md")))
    return hits[0] if hits else None


def _slug(label, words=4):
    """'At Sinai: ordering the camp' -> 'at-sinai'. The part before a colon
    is usually the name; leading and trailing filler words are dropped."""
    toks = re.findall(r"[a-z0-9]+", label.split(":")[0].lower())
    while toks and toks[0] in STOP:
        toks = toks[1:]
    toks = toks[:words]
    while toks and toks[-1] in STOP:
        toks = toks[:-1]
    return "-".join(toks) or "group"


def _heading(text):
    """'I. At Sinai: ordering the camp (1:1–10:10)' -> (label, span)."""
    text = text.strip()
    span = ""
    m = SPAN_RE.search(text)
    if m:
        span = HEB_RE.sub("", m.group(1)).strip()
        text = text[:m.start()].strip()
    text = NUMERAL_RE.sub("", text)
    parts = DASH_RE.split(text, maxsplit=1)
    if len(parts) == 2 and re.match(r"^part\b", parts[0], re.I):
        text = parts[1]
    return text.strip(), span


def parse(md):
    """-> (units, headings, notes).

    units: [{n, passage, title, heb?, under: [heading index per level]}]
    headings: [{level, label, span}] in document order (level 0 = bold)
    notes: lines about anything skipped or adjusted.
    """
    units, headings, notes = [], [], []
    current = {}
    in_table = False
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if in_table and units:
                break          # the Overview table has ended
            continue
        h = HEAD_RE.match(s)
        if h:
            level = 0 if h.group(1) == "**" else 1
            label, span = _heading(h.group(2))
            headings.append({"level": level, "label": label, "span": span})
            current[level] = len(headings) - 1
            if level == 0:
                current.pop(1, None)
            in_table = True
            continue
        r = ROW_RE.match(s)
        if not r:
            continue           # header row, separator, or another table
        in_table = True
        n, passage, title = int(r.group(1)), r.group(2).strip(), r.group(3).strip()
        heb = HEB_RE.search(passage)
        u = {"n": n, "passage": HEB_RE.sub(" ", passage).strip(),
             "title": title, "under": dict(current)}
        if heb:
            u["heb"] = heb.group(1).strip()
            notes.append(f"unit {n}: passage {u['passage']} (Hebrew {u['heb']}) "
                         f"-- English numbering, converted through versify.py; "
                         f"check the generated versification table agrees")
        if not title:
            notes.append(f"unit {n}: no title in the map")
        units.append(u)
    seen = set()
    for u in units:
        if u["n"] in seen:
            notes.append(f"unit {u['n']} listed twice -- first kept")
        seen.add(u["n"])
    return units, headings, notes


def plan(md, kinds, book_name, units_json):
    """Work out the merged units.json without writing. -> (new_json, report)."""
    units, headings, notes = parse(md)
    report = list(notes)
    if not units:
        return None, report + ["no unit rows found -- expected a '| NN | C:V–C:V | "
                               "title |' Overview table (see this module's docstring)"]
    levels = sorted({h["level"] for h in headings})
    if len(levels) > len(kinds):
        return None, report + [
            f"the map has {len(levels)} heading level(s) (bold, italic) but "
            f"{len(kinds)} grouping kind(s) were given -- pass --kinds outer,inner"]
    level_kind = dict(zip(levels, kinds))

    uj = json.loads(json.dumps(units_json))  # deep copy
    by_n = {u["n"]: u for u in uj.get("units", [])}
    first = {}
    for u in units:
        if u["n"] in first:
            continue
        first[u["n"]] = u

    added, kept = [], []
    for n, u in sorted(first.items()):
        if n in by_n:
            kept.append(n)
            continue
        row = {"n": n, "slug": f"unit-{n:02d}",
               "passage": f"{book_name} {u['passage']}", "title": u["title"]}
        for level, hidx in sorted(u["under"].items(), reverse=True):
            kind = level_kind.get(level)
            if kind:
                # grouping n = its position among headings of that level
                row[kind] = sum(1 for h in headings[:hidx + 1] if h["level"] == level)
        row["built"] = False
        uj.setdefault("units", []).append(row)
        added.append(n)
    uj["units"].sort(key=lambda r: r["n"])
    uj["unit_count"] = max(uj.get("unit_count") or 0, len(first))

    parsed = []
    counters = {}
    for i, h in enumerate(headings):
        kind = level_kind.get(h["level"])
        if not kind:
            continue
        counters[kind] = counters.get(kind, 0) + 1
        members = [u["n"] for u in first.values() if u["under"].get(h["level"]) == i]
        parsed.append({"kind": kind, "n": counters[kind], "name": _slug(h["label"]),
                       "label": h["label"], "span": h["span"], "units": members})
    parsed.sort(key=lambda g: (kinds.index(g["kind"]) * -1, g["n"]))
    # innermost kind first, matching book.json's order
    have = uj.get("groupings") or []
    if not have:
        uj["groupings"] = parsed
        if parsed:
            report.append(f"groupings: wrote {len(parsed)} "
                          f"({', '.join(sorted({g['kind'] for g in parsed}))}); "
                          f"names are generated from labels, rename freely")
    else:
        old = {(g["kind"], g["n"]): g for g in have}
        for g in parsed:
            o = old.get((g["kind"], g["n"]))
            if o is None:
                report.append(f"groupings: map has {g['kind']} {g['n']} "
                              f"({g['label']}) that units.json lacks -- kept units.json")
            elif sorted(o.get("units", [])) != g["units"]:
                report.append(f"groupings: {g['kind']} {g['n']} members differ "
                              f"(units.json {o.get('units')}, map {g['units']}) "
                              f"-- kept units.json")
    if added:
        report.insert(0, f"units: added {len(added)} row(s) "
                         f"({added[0]}–{added[-1]})")
    if kept:
        report.insert(1 if added else 0,
                      f"units: kept {len(kept)} existing row(s) untouched")
    return uj, report


def _kinds(arg):
    if arg:
        return [k.strip() for k in arg.split(",") if k.strip()]
    return list(reversed(book().groupings))


def _update_book_json(root, kinds, map_rel):
    """Fill book.json groupings (innermost first) if empty, and add the map
    to the synced files. Returns lines describing what changed."""
    path = os.path.join(root, "book.json")
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    out = []
    if kinds and not cfg.get("groupings"):
        cfg["groupings"] = list(reversed(kinds))
        out.append(f"book.json: groupings = {cfg['groupings']}")
    files = cfg.setdefault("sync", {}).setdefault("files", [])
    if map_rel not in files:
        files.append(map_rel)
        out.append(f"book.json: sync.files += {map_rel}")
    if out:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore units-from-map")
    ap.add_argument("map", nargs="?", help="default: the book root's *unit*map*.md")
    ap.add_argument("--kinds", help="grouping kinds, outer to inner (bold, italic); "
                                    "default: book.json groupings, reversed")
    ap.add_argument("--dry", action="store_true", help="report, write nothing")
    ap.add_argument("--no-leads", action="store_true",
                    help="skip canon leads for the next unit")
    a = ap.parse_args(argv)

    b = book()
    path = a.map or find_map(b.root)
    if not path or not os.path.exists(path):
        print("no unit map found (looked for *unit*map*.md in the book root); "
              "pass its path")
        return 1
    with open(path, encoding="utf-8") as fh:
        md = fh.read()
    with open(b.data("units.json"), encoding="utf-8") as fh:
        units_json = json.load(fh)

    kinds = _kinds(a.kinds)
    new, report = plan(md, kinds, b.name, units_json)
    for line in report:
        print(" ", line)
    if new is None:
        return 1
    if a.dry:
        print("(--dry: nothing written)")
        return 0

    with open(b.data("units.json"), "w", encoding="utf-8") as fh:
        json.dump(new, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {os.path.relpath(b.data('units.json'), b.root)}")
    map_rel = os.path.relpath(os.path.abspath(path), b.root).replace(os.sep, "/")
    used = sorted({g["kind"] for g in new.get("groupings", [])},
                  key=lambda k: kinds.index(k) if k in kinds else 99)
    for line in _update_book_json(b.root, used, map_rel):
        print(line)

    if not a.no_leads and b.language == "hebrew":
        nxt = next((u["n"] for u in new["units"] if not u.get("built")), None)
        if nxt is not None:
            if os.path.exists(b.path("lexicon")):
                from biblecore import leads
                leads.main([str(nxt)])
            else:
                print(f"no lexicon at {os.path.relpath(b.path('lexicon'), b.root)} "
                      f"-- canon leads skipped (tools/new_book.py copies it)")
    print("next: python -m biblecore build, then sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
