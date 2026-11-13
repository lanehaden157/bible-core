"""Inbound leads: canon rows elsewhere whose *target* falls inside a unit.

The unit pack's "already cited from" section. Canon leads (leads.py) run
outward from a unit; this is the other direction: every echo, story, mirror,
intertext and law row in the canon that points into the unit's span, grouped
by the book and unit that made it, so a research chat sees what the canon
already says about these verses before it writes a new cross-reference.

No store of its own. Rows are read from where they live:

  * this book's data/canon.json and mirror files;
  * every sibling folder (beside this book) that has a book.json: its
    data/canon.json and the pairs of its mirror files;
  * bible-core's canon/intertext.json when a bible-core folder sits beside
    the book (carries 'hand' rows and Joshua's harvested echoes).

All references are in displayed (English) numbering, so no versification
mapping is needed. A row is listed once however many stores carry it.
A row made by the unit itself is not inbound and is left out.
"""
import json
import os

from biblecore import canon, mirror

KIND_ORDER = ("quotation", "allusion", "echo", "story", "type-scene", "character",
              "reuse", "mirror", "law")


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _units_of(folder):
    d = _load(os.path.join(folder, "data", "units.json")) or {}
    return {u["n"]: u.get("title", "") for u in d.get("units", []) if "n" in u}


def _folders(b):
    """[(folder, book.json dict)] for this book and its siblings."""
    root = os.path.dirname(b.root)
    out = [(b.root, _load(os.path.join(b.root, "book.json")) or {})]
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return out
    for name in names:
        full = os.path.join(root, name)
        if os.path.abspath(full) == b.root or not os.path.isdir(full):
            continue
        cfg = _load(os.path.join(full, "book.json"))
        if isinstance(cfg, dict) and cfg.get("slug"):
            out.append((full, cfg))
    return out


def collect(b):
    """[row] with keys from, to, kind, note, unit, book (slug), name, abbrev,
    unit_title, via. Mirror-file pairs become kind-'mirror' rows from the
    declaring book's span to the other's."""
    rows, titles, names = [], {}, {}
    for folder, cfg in _folders(b):
        slug = cfg.get("slug")
        names[slug] = (cfg.get("book") or slug, cfg.get("abbrev") or "")
        titles[slug] = _units_of(folder)
        d = _load(os.path.join(folder, "data", "canon.json")) or {}
        for r in d.get("intertext", []) or []:
            rows.append({**r, "book": slug, "via": "canon.json"})
        for m in cfg.get("mirrors") or []:
            md = _load(os.path.join(folder, "data", m.get("file", ""))) or {}
            for p in md.get("pairs", []) or []:
                if isinstance(p, dict) and p.get("here") and p.get("other"):
                    rows.append({"from": p["here"], "to": p["other"], "kind": "mirror",
                                 "unit": None, "book": slug, "via": "mirror file",
                                 "note": f"pair {p.get('id', '?')}"
                                         + (f": {p['title']}" if p.get("title") else "")})
    core = _load(os.path.join(os.path.dirname(b.root), "bible-core", "canon", "intertext.json")) or {}
    for r in core.get("edges", []) or []:
        slug = r.get("book")
        rows.append({**r, "via": "canon/"})
        names.setdefault(slug, (slug, ""))
    for r in rows:
        r["name"] = names.get(r.get("book"), (r.get("book") or "?", ""))[0]
        r["unit_title"] = titles.get(r.get("book"), {}).get(r.get("unit"), "")
    return rows


def inbound(b, lo, hi, n=None):
    """Rows whose target overlaps (b.osis, lo..hi), deduplicated, as a list of
    {book, name, unit, unit_title, from, to, kind, note}. Rows the unit made
    itself (this book, unit n) are skipped."""
    unit_sp = (b.osis, lo, hi)
    seen, out = set(), []
    for r in collect(b):
        sp = mirror.parse_span(r.get("to"))
        if sp is None or not mirror.overlaps(sp, unit_sp):
            continue
        if r.get("book") == b.slug and n is not None and r.get("unit") == n:
            continue
        key = (r.get("book"), r.get("from"), r.get("to"), r.get("kind"))
        if key in seen:
            continue
        seen.add(key)
        out.append({"book": r.get("book"), "name": r["name"], "unit": r.get("unit"),
                    "unit_title": r["unit_title"], "from": r.get("from", ""),
                    "to": r.get("to", ""), "kind": r.get("kind", ""),
                    "note": (r.get("note") or "").strip()})
    return out


def _kind_key(k):
    return KIND_ORDER.index(k) if k in KIND_ORDER else len(KIND_ORDER)


def _cv(ref):
    sp = mirror.parse_span(ref)
    return sp[1] if sp else (999, 999)


def pack_section(b, n, lo, hi):
    """Markdown lines for the unit pack's "Already cited from" section."""
    rows = inbound(b, lo, hi, n)
    L = ["## Already cited from", "",
         "Canon rows elsewhere (echoes, stories, mirrors, laws, intertext) whose target falls "
         f"inside this unit ({b.osis} {lo[0]}:{lo[1]}–{hi[0]}:{hi[1]}), grouped by the book and "
         "unit that made them. Read from the books' data/canon.json, mirror files and bible-core's "
         "canon/; leads, not proof. Use them to see what is already connected; "
         "don't re-propose a row that is listed.", ""]
    if not rows:
        return L[:2] + ["_None: no canon row points into this unit yet._", ""]
    groups = {}
    for r in rows:
        groups.setdefault((r["name"], r["unit"] if r["unit"] is not None else -1), []).append(r)
    order = {s: i for i, s in enumerate(canon_book_order(b))}
    for (name, unit), rs in sorted(groups.items(), key=lambda kv: (
            order.get(kv[1][0]["book"], 99), kv[0][1], kv[0][0])):
        title = rs[0]["unit_title"]
        head = f"**{name}" + (f" unit {unit}" if unit != -1 else " (mirror file)") \
            + (f": {title}" if title else "") + "**"
        L.append(head)
        for r in sorted(rs, key=lambda r: (_kind_key(r["kind"]), _cv(r["to"]), r["from"])):
            L.append(f"- {r['to']} ← {r['from']} · {r['kind']}" + (f" · {r['note']}" if r["note"] else ""))
        L.append("")
    L.append(f"_{len(rows)} row(s)._")
    L.append("")
    return L


def canon_book_order(b):
    """Slugs in canon order, for grouping: bible-core/canon/books.json when
    present, else this book first."""
    d = _load(os.path.join(os.path.dirname(b.root), "bible-core", "canon", "books.json")) or {}
    books = d.get("books") if isinstance(d, dict) else d
    slugs = []
    for x in books or []:
        if isinstance(x, dict) and x.get("slug"):
            slugs.append(x["slug"])
    return slugs or [b.slug]
