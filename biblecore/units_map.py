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

A tiered book's table may add columns after the title:

    | # | Passage | Working title | Tier | Peak |
    | 07 | 24:1–25 | Title | full; 24:10–16 condensed; 24:17–25 digest | ★ |

`Tier` is full (default), condensed or digest, then `;`-separated stretches
inside the unit (`<verses> <tier>`); `Peak` is any mark (★, peak, yes).
A `## Digests` section after the table carries one `- NN: text` line per
unit. All of it is applied only to a book with `"tiers": true` (book.json);
for any other book the extra columns and section are ignored, and a map
without a Tier or Peak column reads exactly as before (an unknown extra
column, say Notes, is ignored). On an existing row this command updates
only tier, peak and stretches, and fills `digest` when the row has none; a
map digest that differs from the stored one is reported and kept, and
`--refresh-digests` overwrites it.

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

from biblecore.book import Book, book

ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")
HEAD_RE = re.compile(r"^\|\s*\|\s*(\*\*|\*)(.+?)\1\s*\|(?:\s*\|)+\s*$")
# a unit row with columns past the title (a tiered book's Tier, Peak)
WIDE_RE = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")
DIGEST_RE = re.compile(r"^\s*[-*]\s*(\d+)\s*[:.\u2014\u2013-]\s*(.+?)\s*$")
TIERS = ("full", "condensed", "digest")
SPAN_TIER_RE = re.compile(
    r"^(\d+:\d+(?:\s*[\u2013-]\s*(?:\d+:)?\d+)?)\s+(condensed|digest)$", re.I)
NO_MARK = {"", "-", "\u2014", "\u2013", "no", "n", "0"}
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
    cols = {}                  # extra column name -> index among the cells
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if in_table and units:
                break          # the Overview table has ended
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and cells[0] == "#" and len(cells) > 3:
            extra_cols = {c.lower(): i for i, c in enumerate(cells) if i > 2}
            # tier parsing starts only with a Tier or Peak column: a Notes
            # column (or a misspelt Tiers) must not reset rows to full
            cols = extra_cols if {"tier", "peak"} & set(extra_cols) else {}
            if extra_cols and not cols:
                notes.append("the table has columns past the title "
                             f"({', '.join(extra_cols)}) but no Tier or Peak: ignored")
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
        extra = {}
        if r:
            n, passage, title = int(r.group(1)), r.group(2).strip(), r.group(3).strip()
        elif cols and WIDE_RE.match(s) and len(cells) > 3:
            n, passage, title = int(cells[0]), cells[1], cells[2]
            extra = {k: cells[i] for k, i in cols.items() if i < len(cells)}
        else:
            continue           # header row, separator, or another table
        in_table = True
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
        if cols:
            u.update(_tier_cells(n, extra, notes))
        units.append(u)
    seen = set()
    for u in units:
        if u["n"] in seen:
            notes.append(f"unit {u['n']} listed twice -- first kept")
        seen.add(u["n"])
    return units, headings, notes


def _tier_cells(n, extra, notes):
    """The Tier and Peak cells of a wide row -> {tier, peak?, stretches?}.
    Anything unreadable is reported, never guessed."""
    out = {}
    head, *spans = [x.strip() for x in extra.get("tier", "").split(";")]
    tier = head.lower() or "full"
    if tier not in TIERS:
        notes.append(f"unit {n}: tier {head!r} is not full, condensed or digest")
        tier = "full"
    out["tier"] = tier
    stretches = []
    for sp in (x for x in spans if x):
        m = SPAN_TIER_RE.match(sp)
        if not m:
            notes.append(f"unit {n}: stretch {sp!r} is not '<verses> condensed|digest'")
            continue
        stretches.append({"tier": m.group(2).lower(),
                          "verses": re.sub(r"\s*[\u2013-]\s*", "\u2013", m.group(1).strip())})
    if stretches:
        out["stretches"] = stretches
    if extra.get("peak", "").strip().lower() not in NO_MARK:
        out["peak"] = True
    return out


def parse_digests(md):
    """{unit n: text} from the lines of a '## Digests' section. A bullet may
    wrap: the lines right after it (until a blank line, the next bullet or a
    heading) are its continuation."""
    out, on, cur = {}, False, None
    for line in md.splitlines():
        if line.lstrip().startswith("#"):
            on, cur = "digest" in line.lower(), None
            continue
        if not on:
            continue
        m = DIGEST_RE.match(line)
        if m:
            n = int(m.group(1))
            cur = n if n not in out else None
            if cur is not None:
                out[n] = m.group(2)
        elif cur is not None and line.strip() and not line.lstrip().startswith(("-", "*", "|")):
            out[cur] += " " + line.strip()
        else:
            cur = None
    return out


TIER_KEYS = ("tier", "peak", "stretches")


def plan(md, kinds, book_name, units_json, tiers=False, refresh_digests=False):
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

    added, kept, tiered = [], [], []
    for n, u in sorted(first.items()):
        if n in by_n:
            kept.append(n)
            if tiers and "tier" in u:
                row = by_n[n]
                new = {k: u[k] for k in TIER_KEYS if k in u}
                if any(row.get(k) != new.get(k) for k in TIER_KEYS):
                    for k in TIER_KEYS:
                        row.pop(k, None)
                    row.update(new)
                    tiered.append(n)
            continue
        row = {"n": n, "slug": f"unit-{n:02d}",
               "passage": f"{book_name} {u['passage']}", "title": u["title"]}
        for level, hidx in sorted(u["under"].items(), reverse=True):
            kind = level_kind.get(level)
            if kind:
                # grouping n = its position among headings of that level
                row[kind] = sum(1 for h in headings[:hidx + 1] if h["level"] == level)
        if tiers:
            row.update({k: u[k] for k in TIER_KEYS if k in u})
        row["built"] = False
        uj.setdefault("units", []).append(row)
        added.append(n)
    uj["units"].sort(key=lambda r: r["n"])
    if tiers:
        # a digest fills a row that has none (a unit's own meta digest wins)
        by_n = {r["n"]: r for r in uj["units"]}
        dig = []
        for n, text in sorted(parse_digests(md).items()):
            row = by_n.get(n)
            if row is None:
                report.append(f"digests: unit {n} has no row -- skipped")
            elif not row.get("digest") or (refresh_digests and row["digest"] != text):
                row["digest"] = text
                dig.append(n)
            elif row["digest"] != text:
                report.append(f"digests: unit {n}: the map's digest differs from the "
                              f"stored one -- kept (--refresh-digests overwrites)")
        if dig:
            report.append(f"units: digest set on {len(dig)} row(s) ({dig[0]}–{dig[-1]})")
    elif any("tier" in u for u in first.values()) or parse_digests(md):
        report.append("the map has Tier/Peak columns or a Digests section but "
                      "book.json \"tiers\" is not true -- ignored")
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
    if tiered:
        report.insert(0, f"units: tier, peak and stretches updated on "
                         f"{len(tiered)} existing row(s) ({tiered[0]}–{tiered[-1]})")
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
    to sync.extra unless core's defaults already sync it (they do for
    `<slug>-literary-unit-map.md`). Returns lines describing what changed."""
    from biblecore import sync
    path = os.path.join(root, "book.json")
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    out = []
    if kinds and not cfg.get("groupings"):
        cfg["groupings"] = list(reversed(kinds))
        out.append(f"book.json: groupings = {cfg['groupings']}")
    if map_rel not in sync.resolve(Book(cfg, root)):
        cfg.setdefault("sync", {}).setdefault("extra", []).append(map_rel)
        out.append(f"book.json: sync.extra += {map_rel}")
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
    ap.add_argument("--refresh-digests", action="store_true",
                    help="tiered books: overwrite stored digests with the map's")
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
    new, report = plan(md, kinds, b.name, units_json, tiers=b.tiers,
                       refresh_digests=a.refresh_digests)
    for line in report:
        print(" ", line)
    if new is None:
        return 1
    if a.dry:
        print("(--dry: nothing written)")
        return 0

    with open(b.data("units.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(new, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {os.path.relpath(b.data('units.json'), b.root)}")
    map_rel = os.path.relpath(os.path.abspath(path), b.root).replace(os.sep, "/")
    used = sorted({g["kind"] for g in new.get("groupings", [])},
                  key=lambda k: kinds.index(k) if k in kinds else 99)
    for line in _update_book_json(b.root, used, map_rel):
        print(line)

    if not a.no_leads and b.language in ("hebrew", "greek"):
        nxt = next((u["n"] for u in new["units"] if not u.get("built")), None)
        # Hebrew leads read Strong's glosses; Greek ones the fetched NT + LXX
        need = ["lexicon"] if b.language == "hebrew" else ["morphgnt", "lxx"]
        missing = [k for k in need if not os.path.exists(b.path(k))]
        if nxt is not None and not missing:
            from biblecore import leads
            leads.main([str(nxt)])
        elif nxt is not None:
            how = ("tools/new_book.py copies it" if b.language == "hebrew"
                   else "run `python -m biblecore fetch`")
            what = "lexicon at " if b.language == "hebrew" else ""
            print(f"no {what}{' or '.join(os.path.relpath(b.path(k), b.root) for k in missing)} "
                  f"-- canon leads skipped ({how})")
    print("next: python -m biblecore build, then sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
