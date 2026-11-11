"""One unit's lookup data for the research chat, as a single synced file.

    python -m biblecore unit-pack N [--out FILE] [--min-count K]

Writes <canon_leads>/unit-pack-NN.md. Anything a research chat could look up
(and has misremembered) comes from here instead: the unit's map entry and
versification notes, the wording rulings its words trigger, the tracked
threads that occur in it with their COMPUTED first occurrence, a lemma table
(id, transliteration, gloss, reach), the leads sheet and the book's known
source gaps. No native script and no `surface` column: a chat copies ids and
transliteration from a table instead of recalling them.

Rulings are tied to the unit by transliteration (a consonant skeleton), since
translation-choices.md is prose; rows that could not be tied are listed by
headword so nothing is lost silently. Everything else is computed from the
word table by lemma id.

A book that declares `mirrors` in book.json also gets a "<Book> mirror"
section (biblecore/mirror.py): the pairs whose side of this book overlaps the
unit, the twin's word-by-word text, and the shared words as leads.
"""
import argparse
import collections
import json
import os
import re
import sys

from biblecore import audit as atc
from biblecore import lang
from biblecore.book import book
from biblecore.roots import bare_id, is_id_segment, lemma_key

MIN_COUNT = 3          # a lemma with this many occurrences in the unit gets a row
COMMON_TOP = 30        # ...unless it is among the book's most frequent lemmas
SIZE_WARN = 40 * 1024  # prompt B: past this, move the leads back out


def unit_ranges(units):
    """[(n, lo, hi)] from data/units.json passages ((ch, v) pairs)."""
    out = []
    for u in units:
        try:
            lo, hi = atc.parse_range(u["passage"])
        except (AttributeError, TypeError):
            continue
        out.append((u["n"], lo, hi))
    return out


def unit_of(cv, ranges):
    for n, lo, hi in ranges:
        if lo <= cv <= hi:
            return n
    return None


def _lemma_keys(lemma_field):
    """The lexeme ids of a word row: each '/'-segment that is an id, with
    its disambiguating letter kept ('6485a'). Prefix segments are skipped."""
    keys = []
    for seg in lemma_field.split("/"):
        seg = seg.strip()
        if is_id_segment(seg):
            try:
                keys.append(lemma_key(seg))
            except ValueError:
                pass
    return keys




def scrub_script(text):
    """Drop native Hebrew/Greek script (the rulings files keep a script column
    for reference; the pack must carry none) and tidy what it leaves behind."""
    text = re.sub("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in (
        (0x590, 0x5FF), (0x370, 0x3FF), (0x1F00, 0x1FFF), (0xFB1D, 0xFB4F))) + "]+", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    return re.sub(r"[ 	]{2,}", " ", text)


def _ref(ch, v):
    return f"{ch}:{v}"


# -------------------------------------------------------------- map entry

def map_entry(b, n):
    """The unit's block from the literary unit map (`**UNN · ...**` plus its
    bullets), or ''."""
    path = os.path.join(b.root, f"{b.slug}-literary-unit-map.md")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    head = re.compile(rf"^\*\*U0*{n}\b")
    out, on = [], False
    for ln in lines:
        if head.match(ln):
            on = True
        elif on and (re.match(r"^\*\*U\d+\b", ln) or ln.startswith("#")):
            break
        if on:
            out.append(ln)
    return "\n".join(out).strip()


def versification_notes(b, lo, hi):
    """Rows of the generated verse-number table that fall inside the unit.
    English column is the displayed numbering."""
    path = b.path("verse_map")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            m = re.match(r"^\|\s*(\d+):(\d+)\s*\|\s*(\d+):(\d+)\s*\|", ln)
            if m and lo <= (int(m.group(1)), int(m.group(2))) <= hi:
                rows.append(f"{m.group(1)}:{m.group(2)} = Hebrew {m.group(3)}:{m.group(4)}")
    return rows


# ---------------------------------------------------------------- rulings

_ROW = re.compile(r"^\|(.+)\|\s*$")


def _skeleton(s):
    """Consonant skeleton of a transliteration, for tying a ruling row to a
    word: marks and vowels dropped, digraphs folded, doubles collapsed."""
    import unicodedata
    s = s.lower().replace("ḥ", "h")          # chet is h here, so chat "ch" (chet) agrees
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower())
                if not unicodedata.combining(c))
    s = re.sub(r"[ʾʿ'’`\-\s]", "", s)
    for a, b_ in (("ph", "p"), ("f", "p"), ("th", "t"), ("kh", "k"), ("ch", "h"),
                  ("sh", "s"), ("ts", "s"), ("tz", "s"), ("q", "k"),
                  ("w", "v"), ("c", "k")):
        s = s.replace(a, b_)
    s = re.sub(r"(?<=[aeiou])h$", "", s)      # a silent final -ah / -eh
    s = re.sub(r"[aeiouy]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def ruling_rows(path):
    """[(heading, headword, translit_tokens, line)] for each glossary table
    row of a rulings file (translation-choices.md, canon-conventions.md).
    Table rows only: the prose around them is not matched."""
    if not os.path.exists(path):
        return []
    rows, heading = [], ""
    with open(path, encoding="utf-8") as fh:
        for ln in fh.read().splitlines():
            if ln.startswith("#"):
                heading = ln.lstrip("# ").strip()
                continue
            m = _ROW.match(ln)
            if not m:
                continue
            cells = [c.strip() for c in m.group(1).split("|")]
            if len(cells) < 3 or set(cells[0]) <= set("-: ") or cells[0].lower() in ("word", "english"):
                continue
            toks = []
            for c in cells[1:3]:
                for grp in re.findall(r"\(([^()]*)\)", c):
                    toks += [t.strip() for t in re.split(r"[/,;]", grp) if t.strip()]
            rows.append((heading, cells[0], toks, ln))
    return rows


def tie_rulings(row_sets, unit_skeletons, thread_keys=()):
    """-> (tied [(file, heading, line)], untied [(file, headword)])."""
    tied, untied = [], []
    for fname, rows in row_sets:
        for heading, head, toks, line in rows:
            hit = re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-") in thread_keys
            for t in toks:
                sk = _skeleton(t)
                if len(sk) >= 3 and any(sk in w for w in unit_skeletons):
                    hit = True
                    break
            (tied if hit else untied).append(
                (fname, heading, line) if hit else (fname, head))
    return tied, untied


# ---------------------------------------------------------------- the pack

def build_pack(b, n, min_count=MIN_COUNT):
    """-> (markdown, stats dict)."""
    units = json.load(open(b.data("units.json"), encoding="utf-8"))["units"]
    row = next((u for u in units if u["n"] == n), None)
    if row is None:
        raise ValueError(f"unit {n} is not in data/units.json")
    ranges = unit_ranges(units)
    lo, hi = atc.parse_range(row["passage"])
    words = atc.load_words()
    ad = lang.adapter()

    in_unit = [w for w in words if lo <= (w["ch"], w["v"]) <= hi]
    if not in_unit:
        raise ValueError(f"no words of {row['passage']} in the word table")

    # lemma statistics: whole book, then this unit
    book_count = collections.Counter()
    where = collections.defaultdict(set)         # lemma key -> units reached
    for w in words:
        u = unit_of((w["ch"], w["v"]), ranges)
        for k in set(_lemma_keys(w["lemma"])):
            book_count[k] += 1
            if u:
                where[k].add(u)
    unit_count = collections.Counter()
    forms = collections.defaultdict(collections.Counter)
    unit_refs = collections.defaultdict(list)
    for w in in_unit:
        for k in set(_lemma_keys(w["lemma"])):
            unit_count[k] += 1
            forms[k][atc._translit_row(w)] += 1
            r = _ref(w["ch"], w["v"])
            if r not in unit_refs[k]:
                unit_refs[k].append(r)
    common = {k for k, _ in book_count.most_common(COMMON_TOP)}

    # threads
    th = json.load(open(b.data("threads.json"), encoding="utf-8"))["threads"]
    from biblecore.roots import load_roots
    root_ids = load_roots().get("roots", {})
    thread_rows, thread_lemmas = [], set()
    for t in th:
        ids = (root_ids.get(t.get("root") or t["id"]) or {}).get("ids") or []
        if not ids:
            continue
        hits = atc.source_hits_for_root(words, ids)
        if not hits:
            continue
        thread_lemmas.update(lemma_key(i) for i in ids)
        order = list(hits.items())
        first_cv = order[0][1]
        first_unit = unit_of(first_cv, ranges)
        here = [cv for _w, cv in order if lo <= cv <= hi]
        if not here:
            continue
        rec = (t.get("opens") or {})
        thread_rows.append({
            "id": t["id"], "gloss": t.get("gloss", ""), "translit": t.get("translit", ""),
            "ids": ids, "first": first_cv, "first_unit": first_unit,
            "opens_here": first_unit == n, "recorded": (rec.get("unit"), rec.get("ref")),
            "here": here, "total": len(order)})

    # leads (folded in: one fetch) and the lemma ids it names
    leads_path = os.path.join(b.path("canon_leads"), f"canon-leads-unit-{n:02d}.md")
    leads_text, leads_ids = "", set()
    if os.path.exists(leads_path):
        leads_text = open(leads_path, encoding="utf-8").read()
        leads_ids = {m for m in re.findall(r"\bH(\d+)", leads_text)}

    # lemma table
    gloss = {}
    try:
        from biblecore import leads as _leads
        gloss = _leads.load_glosses() if b.language == "hebrew" else {}
    except Exception:  # missing lexicon: the table just has no gloss column text
        gloss = {}
    pick = [k for k in unit_count
            if (unit_count[k] >= min_count and k not in common)
            or k in thread_lemmas or bare_id(k) in leads_ids or k in leads_ids]
    pick.sort(key=lambda k: (-unit_count[k], k))

    skeletons = {_skeleton(f) for k in unit_count for f in forms[k]}

    # rulings
    row_sets = [("translation-choices.md", ruling_rows(os.path.join(b.root, "translation-choices.md"))),
                ("canon-conventions.md", ruling_rows(os.path.join(b.root, "canon-conventions.md")))]
    tied, untied = tie_rulings(row_sets, skeletons, {t["id"] for t in thread_rows})

    # source gaps
    gaps = ""
    rpath = os.path.join(b.root, "resources.md")
    if os.path.exists(rpath):
        txt = open(rpath, encoding="utf-8").read()
        m = re.search(r"^##\s+Gaps[^\n]*\n(.*?)(?=^##\s|\Z)", txt, re.S | re.M)
        gaps = m.group(1).strip() if m else ""

    L = [f"# Unit pack — {b.name} unit {n}: {row.get('title', '')}", "",
         f"Passage {row['passage']}. Generated by `python -m biblecore unit-pack {n}` from the "
         "word table, data/threads.json, data/roots.json and the book's reference files; don't "
         "edit it, regenerate it. It holds no native script: copy lemma ids from the tables "
         "below instead of recalling them.", ""]

    L += ["## Map entry", "", map_entry(b, n) or "_No entry for this unit in the literary unit map._", ""]
    vn = versification_notes(b, lo, hi)
    L += ["## Versification", "",
          ("\n".join(f"- {x}" for x in vn) if vn else
           "Verse numbers match the corpus throughout this unit."), ""]

    L += ["## Rulings that apply", "",
          "Wording already decided for words in this unit (tied by transliteration; the full "
          "files are in the synced index). Use these; don't re-ask.", ""]
    if tied:
        cur = None
        for fname, heading, line in tied:
            if fname != cur:
                L.append(f"**{fname}**")
                cur = fname
            L.append(f"- {line.strip().strip('|').strip()}  _(under: {heading})_")
    else:
        L.append("_None tied to this unit's words._")
    if untied:
        L += ["", "Rows not tied to a word here (check these headwords yourself): "
              + "; ".join(sorted({h for _f, h in untied}))[:900], ""]

    L += ["", "## Tracked threads in this unit", "",
          "First occurrence is computed from the word table by id set, not recalled. "
          "A mismatch with the recorded opener is flagged: report it, don't resolve it.", ""]
    if thread_rows:
        L += ["| thread | gloss | ids | first (unit) | opens here? | recorded opener | in this unit | book total |",
              "|---|---|---|---|---|---|---|---|"]
        for t in sorted(thread_rows, key=lambda x: x["first"]):
            ru, rr = t["recorded"]
            rec = f"unit {ru} ({rr})" if ru else "—"
            flag = "" if (not ru or ru == t["first_unit"]) else " **mismatch**"
            L.append("| {id} | {g} | {ids} | {f} (unit {fu}) | {o} | {rec}{flag} | {here} | {tot} |".format(
                id=f"`{t['id']}`", g=t["gloss"][:60], ids=" ".join(t["ids"]),
                f=_ref(*t["first"]), fu=t["first_unit"] or "?",
                o="yes" if t["opens_here"] else "no", rec=rec,
                here=", ".join(_ref(*c) for c in dict.fromkeys(t["here"]))[:120],
                tot=t["total"], flag=flag))
    else:
        L.append("_No tracked thread occurs in this unit._")

    L += ["", "## Lemma table", "",
          "Lemma ids as the word table and `roots.json` write them (a trailing letter is a "
          "distinct lexeme). `reach` lists the book's units where the lemma occurs; a gap means "
          "it is absent there.", "",
          "| lemma id | common form | gloss | in unit | book | reach (units) | refs here |",
          "|---|---|---|---|---|---|---|"]
    for k in pick:
        tr = forms[k].most_common(1)[0][0]
        g = gloss.get(bare_id(k), "")[:48]
        reach = ", ".join(str(u) for u in sorted(where[k]))
        L.append(f"| {k} | {tr} | {g} | {unit_count[k]} | {book_count[k]} | {reach} | "
                 f"{', '.join(unit_refs[k][:6])}{'…' if len(unit_refs[k]) > 6 else ''} |")
    L += ["", f"_{len(pick)} lemmas: those the leads sheet or a tracked thread names, plus any "
          f"with {min_count}+ occurrences here (the book's {COMMON_TOP} commonest left out)._"]

    L += ["", "## Leads", ""]
    if leads_text:
        body = leads_text.split("\n", 1)[1] if leads_text.startswith("# ") else leads_text
        L.append(body.strip())
    else:
        L.append(f"_No canon-leads-unit-{n:02d}.md yet: run `python -m biblecore leads {n}`._")

    if b.mirrors:
        from biblecore import mirror
        L += [""] + mirror.pack_section(b, n, lo, hi, row)

    L += ["", "## Known source gaps", "", gaps or "_resources.md records none._", ""]

    md = scrub_script("\n".join(L).rstrip() + "\n")
    stats = {"bytes": len(md.encode("utf-8")), "lemmas": len(pick),
             "threads": len(thread_rows), "rulings": len(tied), "untied": len(untied),
             "mismatches": sum(1 for t in thread_rows
                               if t["recorded"][0] and t["recorded"][0] != t["first_unit"])}
    return md, stats


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore unit-pack")
    ap.add_argument("unit", type=int)
    ap.add_argument("--out", help="write here instead of <canon_leads>/unit-pack-NN.md")
    ap.add_argument("--min-count", type=int, default=MIN_COUNT,
                    help=f"occurrences in the unit for a lemma row (default {MIN_COUNT})")
    a = ap.parse_args(argv)
    b = book()
    try:
        md, st = build_pack(b, a.unit, a.min_count)
    except ValueError as exc:
        sys.exit(str(exc))
    path = a.out or os.path.join(b.path("canon_leads"), f"unit-pack-{a.unit:02d}.md")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(f"wrote {path} ({st['bytes'] / 1024:.1f} KB): {st['threads']} threads, "
          f"{st['lemmas']} lemmas, {st['rulings']} rulings tied, {st['untied']} not tied")
    if st["mismatches"]:
        print(f"{st['mismatches']} thread(s) whose recorded opener differs from the first occurrence "
              "(flagged in the pack; `audit` warns too)")
    if st["bytes"] > SIZE_WARN:
        print(f"warning: over {SIZE_WARN // 1024} KB; consider moving the leads back to their own file")
    return 0
