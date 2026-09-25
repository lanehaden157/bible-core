"""Build the canon hub site (review F6, F7; plan Phase 4).

    python tools/hub_build.py ../hub          # write the site into ../hub
    python tools/hub_build.py ../hub --check  # say what would change

The hub is its own repo and Pages site (lanehaden157.github.io/bible/). It
federates the book sites rather than merging them (review H8): each book
keeps its own site, and the hub links into them.

Reads, all read-only:
  canon/books.json     the canon in order; started books name their repo
  canon/*.json         arcs, threads, typescenes, intertext, paths
  ../<repo>/data/      each started book's units, threads, occurrences
                       (and lemmas.json for core books)
  ../Joshua words      Joshua's lemma concordance is computed from its
                       word table through biblecore, since its site
                       predates emit.py

Writes into the hub folder:
  index.html, app/hub.js, css/hub.css    copied from bible-core hub/
  data/books.json      the canon map, with progress for started books
  data/canon.json      arcs, canon threads, type-scenes, intertext, paths
  data/concordance.json  Hebrew lemmas across books (F7) and every
                       book's tracked threads with counts

Deterministic. Commit and push the hub repo afterwards.
"""
import argparse
import json
import os
import shutil
import sys
from collections import OrderedDict

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.dirname(CORE)
sys.path.insert(0, CORE)


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def canon_file(name):
    return _load(os.path.join(CORE, "canon", f"{name}.json"), {})


# ------------------------------------------------------------------- books

def book_groups(units_json):
    """[{label, name, units}] for the first grouping kind; legacy
    'movements' ({n,name,units} in Joshua, {id,label,range} in Matthew)."""
    if units_json.get("groupings"):
        kind = units_json["groupings"][0]["kind"]
        return [{"n": g["n"], "label": g.get("label") or g.get("name", ""),
                 "units": g.get("units", [])}
                for g in units_json["groupings"] if g["kind"] == kind]
    out = []
    for m in units_json.get("movements", []):
        n = m.get("n", m.get("id"))
        units = m.get("units") or [u["n"] for u in units_json["units"] if u.get("movement") == n]
        out.append({"n": n, "label": m.get("name") or m.get("label", ""), "units": units})
    return out


def book_entry(b):
    root = os.path.join(BIBLE, b["repo"])
    data = os.path.join(root, "data")
    uj = _load(os.path.join(data, "units.json"), {"units": []})
    tj = _load(os.path.join(data, "threads.json"), {"threads": []})
    occ = _load(os.path.join(data, "occurrences.json"), {})
    counts = {}
    for roots in occ.values():
        for r, d in roots.items():
            counts[r] = counts.get(r, 0) + (d.get("count") or 0)
    units = [OrderedDict(n=u["n"], slug=u["slug"], title=u["title"],
                         passage=u["passage"], built=bool(u.get("built")))
             for u in uj["units"]]
    threads = [OrderedDict(id=t["id"], root=t["root"], translit=t.get("translit", ""),
                           gloss=t.get("gloss", ""), color=t.get("color"),
                           status=t.get("status", "open"), count=counts.get(t["root"], 0))
               for t in tj["threads"]]
    return OrderedDict(
        osis=b["osis"], name=b["name"], t=b["t"], slug=b["slug"], site=b["site"],
        kind=b["kind"], link="cv" if b["kind"] == "core" else "v",
        unit_count=uj.get("unit_count", len(units)),
        units_built=sum(u["built"] for u in units),
        groups=book_groups(uj), units=units, threads=threads)


# ------------------------------------------------------------ concordance

def joshua_lemmas(repo):
    """Joshua's lemma refs, computed from its word table through biblecore
    (read-only), in the same shape as a core book's data/lemmas.json."""
    from biblecore import book as bookmod
    from biblecore import emit
    cfg = _load(os.path.join(CORE, "tests", "joshua-book.json"))
    root = os.path.join(BIBLE, repo)
    if not cfg or not os.path.exists(os.path.join(root, "Joshua-words.tsv")):
        return {}
    b = bookmod.use(bookmod.Book(cfg, root))
    by_ch, refs = emit.words_by_chapter(b)
    counts = {}
    for ch in by_ch.values():
        for ws in ch.values():
            for w in ws:
                if w["l"]:
                    counts[w["l"]] = counts.get(w["l"], 0) + 1
    return emit.lemmas(b, refs, counts)


def concordance(books):
    lem = OrderedDict()
    for b in books:
        if b["t"] != "ot":
            continue
        if b["kind"] == "core":
            per = _load(os.path.join(BIBLE, b["repo"], "data", "lemmas.json"), {}).get("lemmas", {})
        elif b["slug"] == "joshua":
            per = joshua_lemmas(b["repo"])
        else:
            per = {}
        for key, e in per.items():
            k = f"heb:{key}"
            ent = lem.setdefault(k, OrderedDict(t=e.get("t", ""), g=e.get("g", ""), books=OrderedDict()))
            if not ent["t"] and e.get("t"):
                ent["t"] = e["t"]
            ent["books"][b["slug"]] = OrderedDict(n=e["n"], refs=e["refs"])
    ordered = OrderedDict(sorted(lem.items(), key=lambda kv: (int("".join(c for c in kv[0][4:] if c.isdigit()) or 0), kv[0])))
    return ordered


# ------------------------------------------------------------------ build

def build():
    books_cfg = canon_file("books")["books"]
    started = [b for b in books_cfg if b.get("repo") and os.path.isdir(os.path.join(BIBLE, b["repo"]))]
    entries = {b["osis"]: book_entry(b) for b in started}
    books = [entries.get(b["osis"]) or OrderedDict(osis=b["osis"], name=b["name"], t=b["t"])
             for b in books_cfg]
    canon = OrderedDict(
        arcs=canon_file("arcs").get("arcs", []),
        threads=canon_file("threads").get("threads", []),
        typescenes=canon_file("typescenes").get("typescenes", []),
        intertext=canon_file("intertext").get("edges", []),
        paths=canon_file("paths").get("paths", []),
        bridge=canon_file("bridge").get("rows", []),
    )
    conc = OrderedDict(
        _note="Hebrew lemmas across the books with word tables, keyed heb:<Strong's+letter>; "
              "glosses are Strong's short definitions (identifiers, not renderings).",
        lemmas=concordance([entries[b["osis"]] | {"repo": b["repo"]} for b in started]),
    )
    return {"books.json": {"books": books}, "canon.json": canon, "concordance.json": conc}


SOURCE_FILES = ["index.html", "app/hub.js", "css/hub.css", "README.md"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    files = {f"data/{k}": json.dumps(v, ensure_ascii=False, separators=(",", ":")) + "\n"
             for k, v in build().items()}
    for rel in SOURCE_FILES:
        with open(os.path.join(CORE, "hub", rel), encoding="utf-8") as fh:
            files[rel] = fh.read()
    changed = []
    for rel, text in files.items():
        p = os.path.join(out, rel)
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old != text:
            changed.append(rel)
            if not a.check:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    for rel in changed:
        print(f"  {'would write' if a.check else 'wrote'} {rel}")
    print(f"hub: {len(changed)} file(s) {'would change' if a.check else 'changed'} in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
