"""Roll every book's canon rows up into bible-core/canon/ (G9).

    python tools/canon_collect.py          # rewrite canon/intertext.json + typescenes.json
    python tools/canon_collect.py --check  # report only, write nothing

Books are the sibling folders of bible-core. A book on core contributes its
data/canon.json (echo + meta rows; `python -m biblecore build` keeps it
current). A book that predates core (Joshua) has its built units' echoes
harvested here, read-only -- nothing is written into its folder.

Rows marked "source": "hand" in canon/ are curated there and always kept;
every other row is rewritten from the books on each run, so a changed echo
or a re-ported unit is reflected next time. Checks (warnings, not
failures): an arc that isn't in canon/arcs.json, a canon-thread member
naming a book thread that doesn't exist, a type-scene id a book used that
the index doesn't have yet (a stub entry is added for it).
"""
import argparse
import glob
import json
import os
import re
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_ROOT = os.path.dirname(CORE)
CANON = os.path.join(CORE, "canon")
sys.path.insert(0, CORE)

from biblecore import canon  # noqa: E402
from biblecore import meta as um  # noqa: E402

# Books built before core, harvested read-only: slug -> (folder, abbrev)
LEGACY = {"joshua": ("Joshua", "Josh")}


def _load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def _save(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def book_dirs(root=BOOKS_ROOT):
    """{slug: folder} for every sibling folder that is a book."""
    out = {}
    for d in sorted(os.listdir(root)):
        full = os.path.join(root, d)
        bj = _load(os.path.join(full, "book.json"))
        if isinstance(bj, dict) and bj.get("slug"):
            out[bj["slug"]] = full
    for slug, (folder, _abbrev) in LEGACY.items():
        full = os.path.join(root, folder)
        if os.path.isdir(full):
            out.setdefault(slug, full)
    return out


def core_rows(slug, folder):
    """(intertext, typescenes) rows from a core book's data/canon.json."""
    d = _load(os.path.join(folder, "data", "canon.json"), {}) or {}
    it = [dict(r, book=slug) for r in d.get("intertext", [])]
    ts = [dict(r, book=slug) for r in d.get("typescenes", [])]
    return it, ts


def legacy_rows(slug, folder, abbrev):
    """Echo edges harvested read-only from a pre-core book's built units."""
    units = _load(os.path.join(folder, "data", "units.json"), {"units": []})
    built = {u["n"] for u in units.get("units", []) if u.get("built")}
    rows = []
    for path in sorted(glob.glob(os.path.join(folder, "units", "unit-*.html"))):
        n = int(re.search(r"unit-(\d+)", path).group(1))
        if n not in built:
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        rows += [dict(r, book=slug)
                 for r in canon.harvest(html, n, abbrev=abbrev, meta=um.parse(html) or {})]
    return rows


def collect(root=BOOKS_ROOT, canon_dir=CANON):
    """-> (intertext_json, typescenes_json, warnings)."""
    warns = []
    arcs = {a["id"] for a in _load(os.path.join(canon_dir, "arcs.json"), {"arcs": []})["arcs"]}
    it_json = _load(os.path.join(canon_dir, "intertext.json"), {"edges": []})
    ts_json = _load(os.path.join(canon_dir, "typescenes.json"), {"typescenes": []})
    th_json = _load(os.path.join(canon_dir, "threads.json"), {"threads": []})

    books = book_dirs(root)
    book_it, book_ts = [], []
    for slug, folder in books.items():
        if os.path.exists(os.path.join(folder, "book.json")):
            it, ts = core_rows(slug, folder)
            book_it += it
            book_ts += ts
        elif slug in LEGACY:
            book_it += legacy_rows(slug, folder, LEGACY[slug][1])

    edges = [e for e in it_json.get("edges", []) if e.get("source") == "hand"] + book_it
    def cv(ref):
        m = re.search(r"(\d+):(\d+)", ref)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    edges.sort(key=lambda e: (e.get("book", ""), e.get("unit") or 0, cv(e["from"]),
                              e.get("source", ""), e["to"]))
    it_json["edges"] = edges

    scenes = ts_json.get("typescenes", [])
    by_id = {s["id"]: s for s in scenes}
    for s in scenes:
        s["instances"] = [i for i in s.get("instances", []) if i.get("source") == "hand"]
    for r in book_ts:
        s = by_id.get(r["id"])
        if s is None:
            s = {"id": r["id"], "label": r.get("label") or r["id"], "arc": None,
                 "note": "", "instances": []}
            scenes.append(s)
            by_id[r["id"]] = s
            warns.append(f"type-scene '{r['id']}' is new (from {r['book']} unit "
                         f"{r['unit']}); stub added -- give it a label and an arc")
        s["instances"].append({k: r[k] for k in ("book", "ref", "unit", "note", "source")
                               if k in r})

    for kind, rows in (("thread", th_json.get("threads", [])), ("type-scene", scenes)):
        for row in rows:
            if row.get("arc") and row["arc"] not in arcs:
                warns.append(f"{kind} '{row['id']}': arc '{row['arc']}' isn't in arcs.json")
    for t in th_json.get("threads", []):
        for m in t.get("members", []):
            folder = books.get(m.get("book"))
            if not (m.get("thread") and folder):
                continue
            tj = _load(os.path.join(folder, "data", "threads.json"), {"threads": []})
            if m["thread"] not in {x.get("id") for x in tj.get("threads", [])}:
                warns.append(f"canon thread '{t['id']}': {m['book']} has no thread "
                             f"'{m['thread']}'")
    return it_json, ts_json, warns


def main(argv=None):
    ap = argparse.ArgumentParser(prog="canon_collect.py")
    ap.add_argument("--check", action="store_true", help="report only")
    a = ap.parse_args(argv)
    it_json, ts_json, warns = collect()
    edges = it_json["edges"]
    by_src = {}
    for e in edges:
        by_src[e.get("source")] = by_src.get(e.get("source"), 0) + 1
    n_inst = sum(len(s["instances"]) for s in ts_json["typescenes"])
    print(f"intertext: {len(edges)} edge(s) {by_src}; type-scenes: "
          f"{len(ts_json['typescenes'])} with {n_inst} instance(s)")
    for w in warns:
        print("  warn:", w)
    if a.check:
        return 0
    _save(os.path.join(CANON, "intertext.json"), it_json)
    _save(os.path.join(CANON, "typescenes.json"), ts_json)
    print("wrote canon/intertext.json, canon/typescenes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
