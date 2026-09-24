"""A book's canon rows: intertext edges and type-scene instances (G9).

    python -m biblecore canon          # re-harvest echo edges -> data/canon.json

data/canon.json holds two lists, each row tagged with where it came from:

  intertext   {from, to, kind, unit, note?, source}
              kind: quotation | allusion | echo | type-scene
  typescenes  {id, ref, unit, note?, label?, source}

`source` is "echo" for edges harvested from the built fragments' own
`aside.echo` lines and roots[].echo fields (re-derived on every build, so
editing an echo updates its edges), or "meta" for rows the chat side put in
a unit's meta block (`intertext[]`, `typescenes[]`), merged by the porter
and kept until that unit is re-ported. bible-core's tools/canon_collect.py
rolls every book's file up into bible-core/canon/.

References are strings in the book's displayed numbering: "Num 1:2",
"Isa 40:26", "Exod 30:12". Leads, not proof: the harvest records what an
echo names; whether an edge matters is still a reading judgement.
"""
import json
import os
import re

from biblecore.book import book

KINDS = ("quotation", "allusion", "echo", "type-scene")

# Book names as fragments write them (English abbreviations, both
# testaments). A ref needs one of these in front of it, so prose like
# "verses 22-43" or "Rise 1:2" is never read as a reference.
BOOK_NAMES = (
    "Gen Exod Lev Num Deut Josh Judg Ruth Sam Kgs Chr Ezra Neh Esth Job Ps Pss "
    "Prov Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab "
    "Zeph Hag Zech Mal Matt Mark Luke John Acts Rom Cor Gal Eph Phil Col Thess "
    "Tim Titus Phlm Heb Jas Pet Jude Rev"
).split()
_BOOK = r"(?:[1-3]\s?)?(?:" + "|".join(BOOK_NAMES) + r")\b"
_DASH = r"[–-]"
_START = re.compile(r"(" + _BOOK + r")\s+(\d+):(\d+)(?:" + _DASH + r"(\d+(?::\d+)?))?")
_MORE = re.compile(r"\s*([;,])\s*(?:(\d+):)?(\d+)(?:" + _DASH + r"(\d+(?::\d+)?))?(?![\d:])")

ECHO_RE = re.compile(r'<aside\s+class="echo"\s+data-anchor="(\d+):(\d+)"[^>]*>(.*?)</aside>', re.S)
CV_RE = re.compile(r"^\d+:\d+$")
ID_RE = re.compile(r"^[a-z0-9-]+$")


def parse_refs(text):
    """Every scripture reference in prose, continuations included:
    'Gen 15:5; 22:17' -> ['Gen 15:5', 'Gen 22:17'];
    'Deut 31:6, 8' -> ['Deut 31:6', 'Deut 31:8']."""
    text = re.sub(r"<[^>]+>", "", text or "")
    out, pos = [], 0
    while True:
        m = _START.search(text, pos)
        if not m:
            return out
        name = re.sub(r"\s+", " ", m.group(1))
        ch = m.group(2)
        out.append(f"{name} {ch}:{m.group(3)}" + (f"–{m.group(4)}" if m.group(4) else ""))
        pos = m.end()
        while True:
            c = _MORE.match(text, pos)
            if not c:
                break
            sep, ch2, v, tail = c.groups()
            if sep == "," and ch2:          # ', 3:4' still reads as a new chapter
                ch = ch2
            elif sep == ";":
                if not ch2:                 # '; 8' after a ref: ambiguous, stop
                    break
                ch = ch2
            out.append(f"{name} {ch}:{v}" + (f"–{tail}" if tail else ""))
            pos = c.end()


def _first_verse_with_root(html, root, default_ch):
    """'C:V' of the first verse block tagging data-root=root, else None."""
    from biblecore.data_w import verse_blocks
    for s, e, ch, v in verse_blocks(html, default_ch):
        if f'data-root="{root}"' in html[s:e]:
            return f"{ch}:{v}"
    return None


def harvest(html, n, abbrev=None, meta=None):
    """Intertext rows from one built fragment's echoes (source "echo")."""
    from biblecore import meta as um
    abbrev = abbrev or book().abbrev
    meta = meta if meta is not None else (um.parse(html) or {})
    rows, seen = [], set()

    def add(frm, to, note):
        key = (frm, to)
        if key in seen or to == f"{abbrev} {frm}":
            return
        seen.add(key)
        rows.append({"from": f"{abbrev} {frm}", "to": to, "kind": "echo",
                     "unit": n, "note": note, "source": "echo"})

    for m in ECHO_RE.finditer(html):
        frm = f"{m.group(1)}:{m.group(2)}"
        for to in parse_refs(m.group(3)):
            add(frm, to, "")
    first_ch = 1
    pm = re.search(r"(\d+):\d+", meta.get("passage", ""))
    if pm:
        first_ch = int(pm.group(1))
    for r in meta.get("roots", []) or []:
        if not r.get("echo"):
            continue
        frm = _first_verse_with_root(html, r["root"], first_ch)
        if frm:
            for to in parse_refs(r["echo"]):
                add(frm, to, f"root {r['root']}")
    return rows


# ------------------------------------------------------------ meta entries

def validate_meta(meta):
    """Problems with a meta block's optional intertext[] / typescenes[]."""
    errs = []
    for i, e in enumerate(meta.get("intertext", []) or []):
        where = f"intertext[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{where}: must be an object {{ref, to, kind, note?}}")
            continue
        if not CV_RE.match(str(e.get("ref", ""))):
            errs.append(f"{where}: 'ref' must be a bare 'C:V' in this book (e.g. '6:24')")
        if not parse_refs(str(e.get("to", ""))):
            errs.append(f"{where}: 'to' must name a reference like 'Ps 67:1'")
        if e.get("kind") not in KINDS:
            errs.append(f"{where}: 'kind' must be one of {list(KINDS)}")
        for k in set(e) - {"ref", "to", "kind", "note"}:
            errs.append(f"{where}: unknown key '{k}' -- {{ref, to, kind, note?}}")
    for i, e in enumerate(meta.get("typescenes", []) or []):
        where = f"typescenes[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{where}: must be an object {{id, ref, note?, label?}}")
            continue
        if not ID_RE.match(str(e.get("id", ""))):
            errs.append(f"{where}: 'id' must match [a-z0-9-] (e.g. 'commissioning')")
        if not CV_RE.match(str(e.get("ref", ""))):
            errs.append(f"{where}: 'ref' must be a bare 'C:V' in this book")
        for k in set(e) - {"id", "ref", "note", "label"}:
            errs.append(f"{where}: unknown key '{k}' -- {{id, ref, note?, label?}}")
    return errs


def rows_from_meta(meta, n, abbrev=None):
    """(intertext rows, typescene rows) for a unit's meta entries."""
    abbrev = abbrev or book().abbrev
    it = [{"from": f"{abbrev} {e['ref']}", "to": e["to"], "kind": e["kind"],
           "unit": n, "note": e.get("note", ""), "source": "meta"}
          for e in meta.get("intertext", []) or []]
    ts = []
    for e in meta.get("typescenes", []) or []:
        row = {"id": e["id"], "ref": f"{abbrev} {e['ref']}", "unit": n,
               "note": e.get("note", ""), "source": "meta"}
        if e.get("label"):
            row["label"] = e["label"]
        ts.append(row)
    return it, ts


# ------------------------------------------------------------ data/canon.json

def _path():
    return book().data("canon.json")


def load():
    try:
        with open(_path(), encoding="utf-8") as fh:
            d = json.load(fh)
    except FileNotFoundError:
        d = {}
    return {"intertext": d.get("intertext", []), "typescenes": d.get("typescenes", [])}


def save(d):
    d = {"_note": "Canon rows for this book (biblecore/canon.py). 'echo' rows are "
                  "re-harvested every build; 'meta' rows come from ported meta blocks.",
         "intertext": sorted(d["intertext"], key=_sort_key),
         "typescenes": sorted(d["typescenes"], key=lambda r: (r["unit"], r["id"], r["ref"]))}
    with open(_path(), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _sort_key(r):
    cv = re.search(r"(\d+):(\d+)", r["from"])
    return (r["unit"], int(cv.group(1)) if cv else 0, int(cv.group(2)) if cv else 0,
            r["source"], r["to"])


def merge_meta(meta, n):
    """Porter step: replace unit n's meta-sourced rows with this meta's."""
    d = load()
    it, ts = rows_from_meta(meta, n)
    d["intertext"] = [r for r in d["intertext"]
                      if not (r["source"] == "meta" and r["unit"] == n)] + it
    d["typescenes"] = [r for r in d["typescenes"]
                       if not (r["source"] == "meta" and r["unit"] == n)] + ts
    save(d)
    return len(it), len(ts)


def main(argv=None):
    """Re-harvest echo rows from every built unit; keep meta rows."""
    from biblecore import meta as um
    b = book()
    built = {u["n"] for u in um._load("units.json")["units"] if u.get("built")}
    d = load()
    echo_rows = []
    for n in sorted(built):
        path = b.unit_path(n)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                echo_rows += harvest(fh.read(), n)
    d["intertext"] = [r for r in d["intertext"] if r["source"] != "echo"] + echo_rows
    save(d)
    meta_n = sum(1 for r in d["intertext"] if r["source"] == "meta")
    print(f"canon: {len(echo_rows)} echo edge(s), {meta_n} meta edge(s), "
          f"{len(d['typescenes'])} type-scene instance(s) -> "
          f"{os.path.relpath(_path(), b.root)}")
    return 0
