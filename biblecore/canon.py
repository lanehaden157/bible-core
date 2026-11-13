"""A book's canon rows: intertext edges and type-scene instances (G9).

    python -m biblecore canon          # re-harvest echo + story rows -> data/canon.json

data/canon.json holds two lists, each row tagged with where it came from:

  intertext   {from, to, kind, unit, note?, source}
              kind: quotation | allusion | echo | type-scene | story |
                    character | reuse | mirror | law
  typescenes  {id, ref, unit, note?, label?, source}
  lawbriefs   {law, ref, brief, unit, source}   (only when a unit has any;
              meta `lawbriefs[]`: a two-sentence brief of a law id keyed by a
              verse range, read by the hub for "Law behind this" chips)

`source` is "echo" for edges harvested from the built fragments' own
`aside.echo` lines and roots[].echo fields (re-derived on every build, so
editing an echo updates its edges), "story" for rows harvested the same way
from `aside.story` boxes (one intertext row per reference in the box's
par-ref, kind = its data-kind; a type-scene row for its data-scene),
"mirror" for rows from `aside.mirror` boxes (kind "mirror": the anchor verse
to each reference in the box's par-ref, the twin in the mirrored book), or
"law" for rows from `aside.lawparallel` boxes (kind "law": the anchor verse
to each row's span.src, another statement of the same law), or
"meta" for rows the chat side put in
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

KINDS = ("quotation", "allusion", "echo", "type-scene", "story", "character", "reuse", "mirror", "law")
HARVESTED = ("echo", "story", "mirror", "law")   # sources re-derived from the fragments on every build

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
# a continuation ('; 22:17', ', 8') -- but never the number of a numbered
# book ('Gen 1:1, 2 Sam 7:12' is two references, not Gen 1:2)
_NAMES = r"(?:" + "|".join(BOOK_NAMES) + r")\b"
_MORE = re.compile(r"\s*([;,])\s*(?:(\d+):)?(\d+)(?:" + _DASH + r"(\d+(?::\d+)?))?(?![\d:])"
                   r"(?!\s*" + _NAMES + ")")

ECHO_RE = re.compile(r'<aside\s+class="echo"\s+data-anchor="(\d+):(\d+)"[^>]*>(.*?)</aside>', re.S)
STORY_RE = re.compile(r'<aside\s+class="story"([^>]*)>(.*?)</aside>', re.S)
MIRROR_RE = re.compile(r'<aside\s+class="mirror"([^>]*)>(.*?)</aside>', re.S)
LAW_RE = re.compile(r'<aside\s+class="lawparallel"([^>]*)>(.*?)</aside>', re.S)
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


def _attr(attrs, name):
    m = re.search(r'\b' + name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _span_text(body, cls):
    m = re.search(r'<span class="' + cls + r'">(.*?)</span>', body, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def harvest_stories(html, n, abbrev=None):
    """(intertext rows, typescene rows) from one built fragment's aside.story
    boxes (source "story")."""
    abbrev = abbrev or book().abbrev
    it, ts = [], []
    for attrs, body in STORY_RE.findall(html):
        frm = _attr(attrs, "data-anchor")
        kind = _attr(attrs, "data-kind")
        if not frm or not CV_RE.match(frm) or kind not in KINDS:
            continue    # the component check reports it; don't harvest junk
        title = _span_text(body, "par-title")
        for to in parse_refs(_span_text(body, "par-ref")):
            it.append({"from": f"{abbrev} {frm}", "to": to, "kind": kind,
                       "unit": n, "note": title, "source": "story"})
        scene = _attr(attrs, "data-scene")
        if kind == "type-scene" and scene and ID_RE.match(scene):
            where = _attr(attrs, "data-span") or frm
            ts.append({"id": scene, "ref": f"{abbrev} {where}", "unit": n,
                       "note": title, "source": "story"})
    return it, ts


def harvest_mirrors(html, n, abbrev=None):
    """Intertext rows from one built fragment's aside.mirror boxes (source
    "mirror", kind "mirror"): one per reference in the box's par-ref."""
    abbrev = abbrev or book().abbrev
    rows = []
    for attrs, body in MIRROR_RE.findall(html):
        frm = _attr(attrs, "data-anchor")
        if not frm or not CV_RE.match(frm):
            continue    # the component check reports it; don't harvest junk
        pair = _attr(attrs, "data-pair") or ""
        title = _span_text(body, "par-title")
        for to in parse_refs(_span_text(body, "par-ref")):
            rows.append({"from": f"{abbrev} {frm}", "to": to, "kind": "mirror", "unit": n,
                         "note": (f"pair {pair}: " if pair else "") + title, "source": "mirror"})
    return rows


def harvest_laws(html, n, abbrev=None):
    """Intertext rows from one built fragment's aside.lawparallel boxes
    (source "law", kind "law"): the anchor verse to each row's span.src."""
    abbrev = abbrev or book().abbrev
    rows = []
    for attrs, body in LAW_RE.findall(html):
        frm = _attr(attrs, "data-anchor")
        if not frm or not CV_RE.match(frm):
            continue    # the component check reports it; don't harvest junk
        law = _attr(attrs, "data-law") or ""
        for row in re.findall(r'<div class="row">(.*?)</div>', body, re.S):
            for to in parse_refs(_span_text(row, "src")):
                rows.append({"from": f"{abbrev} {frm}", "to": to, "kind": "law", "unit": n,
                             "note": f"law {law}" if law else "", "source": "law"})
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
    errs += validate_lawbriefs(meta)
    return errs


BRIEF_KEYS = {"law", "ref", "brief"}
MAX_BRIEF = 400


def validate_lawbriefs(meta):
    """Problems with a meta block's optional lawbriefs[]: each {law, ref,
    brief}, the ref inside one of that law's passages, at most two sentences."""
    entries = meta.get("lawbriefs")
    if entries is None:
        return []
    if not isinstance(entries, list):
        return ["lawbriefs must be a list of {law, ref, brief}"]
    from biblecore import laws, mirror
    try:
        table = laws.table()
    except (OSError, ValueError, KeyError):
        table = {}
    errs = []
    for i, e in enumerate(entries):
        where = f"lawbriefs[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{where}: must be an object {{law, ref, brief}}")
            continue
        for k in sorted(set(e) - BRIEF_KEYS):
            errs.append(f"{where}: unknown key '{k}' -- {{law, ref, brief}}")
        law = table.get(e.get("law"))
        if not law:
            errs.append(f"{where}: 'law' {e.get('law')!r} is not in the laws file")
        sp = mirror.parse_span(e.get("ref"))
        if sp is None:
            errs.append(f"{where}: 'ref' must be a full reference like 'Deut 15:1–11'")
        elif law and not laws.containing(law, sp):
            errs.append(f"{where}: 'ref' {e['ref']} is not inside one of law {e['law']}'s passages")
        b = e.get("brief")
        if not isinstance(b, str) or not b.strip():
            errs.append(f"{where}: needs a 'brief'")
        else:
            if len(b) > MAX_BRIEF or len(re.findall(r"[.!?](?:\s|$)", b)) > 2:
                errs.append(f"{where}: a brief is at most two sentences ({MAX_BRIEF} characters)")
            if laws.DATING_RE.search(b):
                errs.append(f"{where}: no dating or source argument in a brief")
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
    out = {"intertext": d.get("intertext", []), "typescenes": d.get("typescenes", [])}
    if d.get("lawbriefs"):
        out["lawbriefs"] = d["lawbriefs"]
    return out


def save(d):
    briefs = d.get("lawbriefs")
    d = {"_note": "Canon rows for this book (biblecore/canon.py). 'echo' rows are "
                  "re-harvested every build; 'meta' rows come from ported meta blocks.",
         "intertext": sorted(d["intertext"], key=_sort_key),
         "typescenes": sorted(d["typescenes"], key=lambda r: (r["unit"], r["id"], r["ref"]))}
    if briefs:      # absent for a book with none: its file is unchanged
        d["lawbriefs"] = sorted(briefs, key=lambda r: (r["unit"], r["law"], r["ref"]))
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
    briefs = [r for r in d.get("lawbriefs", []) if r["unit"] != n] + [
        {"law": e["law"], "ref": e["ref"], "brief": e["brief"], "unit": n, "source": "meta"}
        for e in meta.get("lawbriefs", []) or []]
    if briefs:
        d["lawbriefs"] = briefs
    else:
        d.pop("lawbriefs", None)
    save(d)
    return len(it), len(ts)


def main(argv=None):
    """Re-harvest echo and story rows from every built unit; keep meta rows."""
    from biblecore import meta as um
    b = book()
    built = {u["n"] for u in um._load("units.json")["units"] if u.get("built")}
    d = load()
    echo_rows, story_rows, story_ts, mirror_rows, law_rows = [], [], [], [], []
    for n in sorted(built):
        path = b.unit_path(n)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                html = fh.read()
            echo_rows += harvest(html, n)
            it, ts = harvest_stories(html, n)
            story_rows += it
            story_ts += ts
            mirror_rows += harvest_mirrors(html, n)
            law_rows += harvest_laws(html, n)
    d["intertext"] = ([r for r in d["intertext"] if r["source"] not in HARVESTED]
                      + echo_rows + story_rows + mirror_rows + law_rows)
    d["typescenes"] = [r for r in d["typescenes"] if r["source"] not in HARVESTED] + story_ts
    save(d)
    meta_n = sum(1 for r in d["intertext"] if r["source"] == "meta")
    print(f"canon: {len(echo_rows)} echo edge(s), {len(story_rows)} story edge(s), "
          + (f"{len(mirror_rows)} mirror edge(s), " if mirror_rows else "")
          + (f"{len(law_rows)} law edge(s), " if law_rows else "")
          + f"{meta_n} meta edge(s), "
          f"{len(d['typescenes'])} type-scene instance(s) -> "
          f"{os.path.relpath(_path(), b.root)}")
    return 0
