"""Audit tracked-thread tag coverage by set arithmetic over word ids -- no
original-language string is ever compared to another.

Root identity is a curated set of lemma ids in data/roots.json, and every
tracked-thread span carries the word id it refers to (`data-w`). For each
unit: what the source has (every word whose lemma is in a root's id set,
inside the unit's passage) minus what the fragment tagged, and the reverse.
Reports gap / wrong / stray / missing_data_w. Local roots (no id set) get an
informational per-verse listing instead.

Seeded from Joshua's pipeline/audit_thread_coverage.py; words and verses now
come from the book's corpus adapter, transliteration from its language
adapter. (learned: substring-stem matching measured 0-42% recall on Joshua's
weak-root verbs, which is why this is id-based.)

    python -m biblecore audit             # every tracked thread
    python -m biblecore audit give devote  # just these
    python -m biblecore audit --stub give  # retrofit-tags stubs
                                                           # for give's gaps
    python -m biblecore audit --ids kol give
                        # every surface form + ref a root's id set pulls in,
                        # counted by word id (not lemma occurrence -- Beth-el
                        # is two tagged words sharing one id, style ref §6).
                        # Run this on every id set before Lane commits it.
    python -m biblecore audit --unit unit-06
                        # just one unit (coverage_for_unit is the same call
                        # the Phase 3 porter will use)

Informational: exits 0 even with gaps (most units don't exist yet, so most
threads legitimately show gaps past whatever's built).
"""

import json
import os
import re
import sys

from biblecore import corpus, lang
from biblecore.book import book
from biblecore.meta import declared_ranges
from biblecore.roots import bare_id, lemma_key, load_roots, split_ids


def _translit_row(row):
    """Transliterate a word-table row WITH its lemma overrides (bare
    transliterate() never applies them: kol would render `kal`)."""
    ad = lang.adapter()
    try:
        return ad.transliterate_word(row["surface"], row.get("lemma", ""),
                                     row.get("morph"))
    except Exception:  # alignment edge case
        return ad.transliterate(row["surface"])


def _data(name):
    with open(book().data(name), encoding="utf-8") as f:
        return json.load(f)


VBLOCK = re.compile(r'<(?:div|p)\s+class="v"[^>]*>(.*?)</(?:div|p)>', re.S)
NUM = re.compile(r'<span class="n">(\d+)</span>')
SPAN_ATTRS = re.compile(r'<span\s+class="r"([^>]*)>')
DATA_ROOT = re.compile(r'data-root="([a-z0-9-]+)"')
DATA_W = re.compile(r'data-w="([^"]*)"')
TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

def detag(s):
    return WS.sub(" ", TAGS.sub("", s)).strip()


# ------------------------------------------------------------- source text

def load_hebrew():
    """[(ch, v, line_text), ...] from the book's reading text -- used for
    the local-root per-verse view and verse_text(). (Name kept from Joshua;
    it is whatever language the book is in.)"""
    return corpus.adapter().load_reading()


# ------------------------------------------------------------ word-id side

def load_words():
    """Every running-text word row, variants resolved, with integer ch/v."""
    return corpus.adapter().load_words()


def _lemma_bare_ids(lemma_field):
    """Every bare numeric id among a row's '/'-separated lemma segments
    (bound-prefix segments like 'c'/'b'/'l' aren't ids, skipped)."""
    ids = set()
    for seg in lemma_field.split("/"):
        seg = seg.strip()
        if not seg or not seg[0].isdigit():
            continue
        try:
            ids.add(bare_id(seg))
        except ValueError:
            pass
    return ids


def words_by_id(words):
    return {row["word_id"]: row for row in words}


def _lemma_id_forms(lemma_field):
    """(bare_ids, exact_keys) for a row's '/'-separated lemma segments.

    Bound-prefix segments ('c'/'b'/'l') aren't ids and are skipped.
    """
    bares, keys = set(), set()
    for seg in lemma_field.split("/"):
        seg = seg.strip()
        if not seg or not seg[0].isdigit():
            continue
        try:
            bares.add(bare_id(seg))
            keys.add(lemma_key(seg))
        except ValueError:
            pass
    return bares, keys


def source_hits_for_root(words, ids):
    """{word_id: (ch, v)} for every non-Ketiv word this root's ids claim.

    `ids` is the root's raw id list. A bare id ('2416') matches every
    letter variant of that number; a suffixed id ('2416e') matches only
    that lexeme, so a root can distinguish 3885a *lodge* from 3885b
    *murmur* (review A7). One entry per word id (§6: Beth-el is two
    tagged words sharing one id -- counted as two occurrences here, by
    design, not folded into one)."""
    bare_set, exact_set = split_ids(ids)
    hits = {}
    for row in words:
        bares, keys = _lemma_id_forms(row["lemma"])
        if (bares & bare_set) or (keys & exact_set):
            hits[row["word_id"]] = (row["ch"], row["v"])
    return hits


# ----------------------------------------------------------------- fragment side

NUM_CV = re.compile(r'<span class="n">\s*(?:(\d+):)?(\d+)\s*</span>')


def parse_range(passage):
    m = re.search(r"(\d+):(\d+)\s*[-–]\s*(?:(\d+):)?(\d+)", passage)
    if not m:
        m2 = re.search(r"(\d+):(\d+)", passage)
        c, v = int(m2.group(1)), int(m2.group(2))
        return (c, v), (c, v)
    c1, v1 = int(m.group(1)), int(m.group(2))
    c2 = int(m.group(3)) if m.group(3) else c1
    v2 = int(m.group(4))
    return (c1, v1), (c2, v2)


def hebrew_index(verses):
    maxv, present = {}, set()
    for ch, v, _ in verses:
        maxv[ch] = max(maxv.get(ch, 0), v)
        present.add((ch, v))
    return maxv, present


def expected_seq(lo, hi, maxv, present):
    (c1, v1), (c2, v2) = lo, hi
    seq, ch, v = [], c1, v1
    while (ch, v) <= (c2, v2):
        if (ch, v) in present:
            seq.append((ch, v))
        if ch < c2 and v >= maxv.get(ch, v):
            ch, v = ch + 1, 1
        else:
            v += 1
    return seq


def parse_tagged_spans(html):
    """[(data_root, data_w_or_None), ...] for every <span class="r"> in
    html, document order. data_w is None when the attribute is missing --
    a hard error for a tracked-thread span, harmless for a local one."""
    out = []
    for m in SPAN_ATTRS.finditer(html):
        attrs = m.group(1)
        rm = DATA_ROOT.search(attrs)
        if not rm:
            continue
        wm = DATA_W.search(attrs)
        out.append((rm.group(1), wm.group(1) if wm else None))
    return out


def tagged_map(html, lo, hi, maxv, present, slug="?"):
    """{ (ch,v): set(data-root) } from the fragment -- the local-root
    per-verse view. Language-agnostic (reads only the English gloss HTML
    and verse numbering); unchanged from before this rework."""
    seq = expected_seq(lo, hi, maxv, present)
    blocks = [(m.start(), m.end(), m.group(1)) for m in VBLOCK.finditer(html)]
    numbered = [(s, e, seg, NUM_CV.search(seg)) for s, e, seg in blocks]
    numbered = [(s, e, seg, m) for s, e, seg, m in numbered if m]

    tagged, warn, si = {}, [], 0
    holefilled = set()
    placed = []
    for bi, (s, e, seg, m) in enumerate(numbered):
        if m.group(1):
            cv = (int(m.group(1)), int(m.group(2)))
            while si < len(seq) and seq[si] < cv:
                si += 1
        else:
            v = int(m.group(2))
            ahead = next((k for k in range(si, len(seq)) if seq[k][1] == v), None)
            if ahead is None:
                warn.append(f"{slug}: verse block #{bi} (v{v}) has no match in "
                            f"the expected sequence from {seq[si] if si < len(seq) else 'end'}"
                            f" — numbering drift")
                continue
            cv = seq[ahead]
            si = ahead
        tagged.setdefault(cv, set()).update(r for r, _w in parse_tagged_spans(seg))
        if placed:
            prev_cv, prev_end = placed[-1]
            skipped = [q for q in seq if prev_cv < q < cv]
            if skipped:
                roots = {r for r, _w in parse_tagged_spans(html[prev_end:s])}
                tagged.setdefault(prev_cv, set()).update(roots)
                holefilled.add(prev_cv)
                for q in skipped:
                    tagged.setdefault(q, set()).update(roots)
                    holefilled.add(q)
        si += 1
        placed.append((cv, e))
    return tagged, warn, holefilled


def verse_text(html, v):
    """Best-effort detagged English of a verse, for the report."""
    for m in VBLOCK.finditer(html):
        seg = m.group(1)
        nums = NUM.findall(seg)
        if nums and int(nums[0]) == v:
            t = detag(re.sub(r"<sup\b.*?</sup>", "", seg, flags=re.S))
            return re.sub(r"^\d+\s*", "", t)
    return ""


# ----------------------------------------------------------------- audit

def built_units(units_json):
    for u in units_json["units"]:
        if u.get("built"):
            path = os.path.join(book().path("units"), u["slug"] + ".html")
            if os.path.exists(path):
                yield u, open(path, encoding="utf-8").read()


def in_range(cv, lo, hi):
    return lo <= cv <= hi


def _tracked_roots(threads_json):
    """{thread_id: root_slug} for every entry in threads.json."""
    return {t["id"]: t["root"] for t in threads_json.get("threads", [])}


def ids_report(root_slugs):
    """For each named root, list every surface form its id set pulls in
    from the whole book -- counts (by word id) and refs. The review step
    before Lane commits an id set to data/roots.json."""
    roots_data = load_roots()
    words = load_words()
    roots = roots_data.get("roots", {})

    for slug in root_slugs:
        entry = roots.get(slug)
        if entry is None:
            print(f"  (no data/roots.json entry for '{slug}')")
            continue
        hits = source_hits_for_root(words, entry["ids"])
        wbi = words_by_id(words)

        by_form = {}
        for wid, cv in hits.items():
            surface = wbi[wid]["surface"]
            e = by_form.setdefault(surface, {"n": 0, "refs": [], "wid": wid})
            e["n"] += 1
            e["refs"].append(f"{cv[0]}:{cv[1]}")

        print(f"\n=== {slug}  ids: {', '.join(entry['ids'])}  "
              f"({len(hits)} word(s) total) ===")
        for surface, e in sorted(by_form.items(), key=lambda kv: -kv[1]["n"]):
            refs = ", ".join(e["refs"][:10])
            more = f" ... +{len(e['refs']) - 10} more" if len(e["refs"]) > 10 else ""
            print(f"    {surface:16} {_translit_row(wbi[e['wid']]):18} "
                  f"{e['n']:2}x  {refs}{more}")
    return 0


def local_root_verses(html, lo, hi, tracked_root_slugs, slug="?"):
    """{root_slug: [(ch, v), ...]} for every data-root in this fragment
    that is NOT a tracked thread -- the informational per-verse view for
    local roots (style reference §2: they don't carry data-w, and have no
    id set to audit against, so this is a listing, not a gap/wrong/stray
    report). Returns (local, warnings)."""
    verses = load_hebrew()
    maxv, present = hebrew_index(verses)
    tmap, warnings, _holefilled = tagged_map(html, lo, hi, maxv, present, slug)

    local = {}
    for cv, roots_here in tmap.items():
        for root in roots_here:
            if root in tracked_root_slugs:
                continue
            local.setdefault(root, []).append(cv)
    for root in local:
        local[root].sort()
    return local, warnings


def coverage_for_fragment(slug, html, passage, threads_json=None, roots_json=None):
    """Structured coverage report for one fragment string across every
    tracked thread -- no units.json lookup, so it works during a port
    before the row exists. Returns {"gaps": [...], "wrong": [...],
    "strays": [...], "missing_data_w": N, "local": {root: [(ch,v),...]},
    "warnings": [...]}."""
    threads_json = threads_json or _data("threads.json")
    roots_json = roots_json or load_roots()
    tracked = _tracked_roots(threads_json)
    roots = roots_json.get("roots", {})

    lo, hi = parse_range(passage)
    words = load_words()
    wbi = words_by_id(words)
    spans = parse_tagged_spans(html)

    gaps, wrong, strays, warnings = [], [], [], []
    covered = []
    missing_data_w = 0
    declared = declared_ranges(html)

    local, local_warnings = local_root_verses(html, lo, hi, set(tracked.values()), slug)
    warnings += local_warnings

    for tid, root_slug in tracked.items():
        entry = roots.get(root_slug)
        if entry is None:
            warnings.append(f"thread '{tid}': root '{root_slug}' has no "
                             f"data/roots.json entry")
            continue
        source_hits = source_hits_for_root(words, entry["ids"])
        in_range_hits = {wid: cv for wid, cv in source_hits.items()
                          if in_range(cv, lo, hi)}

        tagged_ids = set()
        for r, w in spans:
            if r != root_slug:
                continue
            if w is None:
                missing_data_w += 1
                continue
            tagged_ids.add(w)

        for wid, cv in sorted(in_range_hits.items(), key=lambda kv: kv[1]):
            if wid not in tagged_ids:
                if any(a <= cv <= b for a, b in declared):
                    covered.append({"thread": tid, "root": root_slug, "word_id": wid,
                                    "ch": cv[0], "v": cv[1]})
                    continue
                gaps.append({"thread": tid, "root": root_slug, "word_id": wid,
                             "ch": cv[0], "v": cv[1], "surface": wbi[wid]["surface"],
                             "translit": _translit_row(wbi[wid]),
                             "text": verse_text(html, cv[1])})
        for wid in sorted(tagged_ids):
            row = wbi.get(wid)
            if row is None:
                strays.append({"thread": tid, "root": root_slug, "word_id": wid,
                                "reason": "does not exist in the word table"})
                continue
            cv = (row["ch"], row["v"])
            if not in_range(cv, lo, hi):
                strays.append({"thread": tid, "root": root_slug, "word_id": wid,
                                "reason": f"ref {cv[0]}:{cv[1]} is outside this "
                                          f"unit's passage {passage!r}"})
                continue
            if wid not in source_hits:
                wrong.append({"thread": tid, "root": root_slug, "word_id": wid,
                               "ch": cv[0], "v": cv[1], "surface": row["surface"]})

    return {"gaps": gaps, "wrong": wrong, "strays": strays, "covered": covered,
            "missing_data_w": missing_data_w, "local": local, "warnings": warnings}


def coverage_for_unit(slug, threads_json=None, roots_json=None):
    """coverage_for_fragment for a BUILT unit, reading its passage from
    units.json and its html from units/<slug>.html."""
    uj = _data("units.json")
    row = next((u for u in uj["units"] if u["slug"] == slug), None)
    if row is None:
        return {"gaps": [], "wrong": [], "strays": [], "covered": [], "missing_data_w": 0,
                "local": {}, "warnings": [f"{slug}: not in units.json"]}
    with open(os.path.join(book().path("units"), slug + ".html"), encoding="utf-8") as f:
        html = f.read()
    return coverage_for_fragment(slug, html, row["passage"], threads_json, roots_json)


def audit(only=None, stub_for=None, unit_slugs=None):
    threads_json = _data("threads.json")
    roots_json = load_roots()
    units_json = _data("units.json")
    tracked = _tracked_roots(threads_json)
    roots = roots_json.get("roots", {})

    units = [(u, h) for u, h in built_units(units_json)
             if not unit_slugs or u["slug"] in unit_slugs]

    defined = [tid for tid, r in tracked.items() if r in roots]
    undefined = [tid for tid, r in tracked.items() if r not in roots]
    targets = defined if not only else [t for t in defined if t in only]

    total_gaps = 0
    total_wrong = 0
    total_strays = 0
    total_missing_w = 0
    stub_lines = []
    covs = {}  # slug -> coverage_for_fragment result, computed once, reused below

    for u, html in units:
        cov = coverage_for_fragment(u["slug"], html, u["passage"], threads_json, roots_json)
        covs[u["slug"]] = cov
        by_thread_gaps = {}
        for g in cov["gaps"]:
            if only and g["thread"] not in only:
                continue
            by_thread_gaps.setdefault(g["thread"], []).append(g)
        by_thread_wrong = {}
        for w in cov["wrong"]:
            if only and w["thread"] not in only:
                continue
            by_thread_wrong.setdefault(w["thread"], []).append(w)
        by_thread_stray = {}
        for s in cov["strays"]:
            if only and s["thread"] not in only:
                continue
            by_thread_stray.setdefault(s["thread"], []).append(s)

        for tid in targets:
            gs = by_thread_gaps.get(tid, [])
            ws = by_thread_wrong.get(tid, [])
            ss = by_thread_stray.get(tid, [])
            if not gs and not ws and not ss:
                continue
            print(f"  ✗ {u['slug']}/{tid:14} {len(gs)} gap(s), "
                  f"{len(ws)} wrong-id, {len(ss)} stray")
            for g in gs:
                total_gaps += 1
                print(f"      GAP    {g['ch']}:{g['v']}  {g['word_id']}  "
                      f"‹{g['surface']}› ({g['translit']})")
                if g["text"]:
                    print(f"             “{g['text'][:96]}”")
                stub_lines.append((tid,
                    f'    {{ "unit": "{u["slug"]}", "verse": {g["v"]}, '
                    f'"text": "???", "root": "{g["root"]}", '
                    f'"why": "{g["translit"]} {g["ch"]}:{g["v"]} ({g["word_id"]})" }},'))
            for w in ws:
                total_wrong += 1
                print(f"      WRONG  {w['ch']}:{w['v']}  {w['word_id']}  "
                      f"‹{w['surface']}› tagged {w['root']}, but that id's "
                      f"lemma isn't in the root's set")
            for s in ss:
                total_strays += 1
                print(f"      STRAY  {s['word_id']}  tagged {s['root']}: {s['reason']}")
        total_missing_w += cov["missing_data_w"]
        if cov["missing_data_w"]:
            print(f"  ✗ {u['slug']}: {cov['missing_data_w']} tracked-thread "
                  f"span(s) with no data-w attribute (hard error)")
        covered = [c for c in cov["covered"] if not only or c["thread"] in only]
        if covered:
            by = {}
            for c in covered:
                by[c["thread"]] = by.get(c["thread"], 0) + 1
            ranges = ", ".join(f"{a[0]}:{a[1]}–{b[0]}:{b[1]}"
                               for a, b in declared_ranges(html))
            print(f"  · {u['slug']}: {len(covered)} occurrence(s) in verses a "
                  f"component presents in place of verse text ({ranges}), not "
                  f"gaps: " + ", ".join(f"{t} {n}" for t, n in sorted(by.items())))
        for warning in cov["warnings"]:
            print(f"  ⚠ {u['slug']}: {warning}")
        if cov["local"] and not only:
            print(f"  · {u['slug']}: local roots (informational, no id set to "
                  f"audit against):")
            for root, cvs in sorted(cov["local"].items()):
                refs = ", ".join(f"{c}:{v}" for c, v in cvs)
                print(f"      {root:14} {len(cvs)} verse(s) — {refs}")

    if not stub_for:
        scope = (f"{len(units)} built unit" + ("s" if len(units) != 1 else "")
                 if not unit_slugs else ", ".join(unit_slugs))

        def _has_issue(tid):
            return any(
                any(x["thread"] == tid for x in cov["gaps"] + cov["wrong"] + cov["strays"])
                for cov in covs.values()
            )

        for tid in targets:
            if not _has_issue(tid):
                occ = len(source_hits_for_root(
                    load_words(), roots[tracked[tid]]["ids"]))
                print(f"  ✓ {tid:14} clean across {scope} ({occ} occ. book-wide)")

    if undefined and not unit_slugs:
        print(f"\n  NO ROOT DEFINED — add to data/roots.json:")
        for tid in sorted(undefined):
            print(f"      {tid:14} root=‹{tracked[tid]}›")

    if stub_for is not None:
        want = set(stub_for)
        lines = [ln for tid, ln in stub_lines if not want or tid in want]
        print(f"\n--- retrofit-tags.json stubs "
              f"({'all audited' if not want else ', '.join(sorted(want))}) — "
              f"fill in \"text\", paste into retrofit-tags.json 'add' ---")
        for ln in lines:
            print(ln)
        if not lines:
            print("    (no gaps)")

    scope = "built-unit" if not unit_slugs else "/".join(unit_slugs)
    print(f"\n{total_gaps} gap(s), {total_wrong} wrong-id, {total_strays} stray, "
          f"{total_missing_w} missing-data-w across {len(targets)} audited "
          f"thread(s) ({scope}).")
    return total_gaps + total_wrong + total_strays + total_missing_w


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    stub = None
    if "--stub" in args:
        i = args.index("--stub")
        stub = args[i + 1:] if len(args) > i + 1 else []
        args = args[:i]
    unit_slugs = None
    if "--unit" in args:
        i = args.index("--unit")
        unit_slugs = [a for a in args[i + 1:] if not a.startswith("--")]
        args = args[:i]
    ids_mode = "--ids" in args
    if ids_mode:
        i = args.index("--ids")
        ids_targets = [a for a in args[i + 1:] if not a.startswith("--")]
        args = args[:i]
    check = "--check" in args
    args = [a for a in args if not a.startswith("--")]
    only = args or None

    if ids_mode:
        print("root id sets — every word form each root's ids pull in\n")
        return ids_report(ids_targets or (only or []))

    scope = f" — {', '.join(unit_slugs)}" if unit_slugs else " vs. built fragments"
    print(f"thread coverage audit — {book().name}{scope}\n")
    problems = audit(only=only, stub_for=stub, unit_slugs=unit_slugs)
    if check and problems:
        print("\n[audit] built-unit issues exist — see above "
              "(warning only, not a build failure)")
    return 0
