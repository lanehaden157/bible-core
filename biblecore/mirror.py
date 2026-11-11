"""Mirror: a book that reads another book backwards (Numbers 10-24 against
Exodus 5-18), as data, a check, a unit-pack section and a box.

    python -m biblecore mirror                  # check the data, fill the boxes' strength dots
    python -m biblecore mirror keep ID [--pos N] [--strength N]   # a proposal from out/mirror-delta.json -> the data file
    python -m biblecore mirror decline ID       # mark a proposal declined

A book declares what it mirrors in book.json:

    "mirrors": [{"with": "Exod", "file": "mirror-exodus.json"}]

`with` is the OSHB id of the other book; `file` sits in data/ and is POLICY,
like threads.json: the porter proposes (`mirror[]` in a unit's meta block,
`out/mirror-delta.json`), a human disposes (`mirror keep`). Nothing here is
specific to one pair of books. Only Hebrew books can mirror for now.

data/<file>.json
    {"version": 1,
     "centre":  {"span": "Exod 19:1 – Num 10:10", "label": "...", "note": "..."},   # optional
     "sources": [{"id", "cite", "what"?, "boundary_note"?}],                          # optional
     "pairs": [{"id", "tier": "chiasm"|"echo", "pos": 1.. (chiasm only),
                "here": "Num 11:10–17", "other": "Exod 18:13–18",
                "title", "strength": 1|2|3, "strength_why"?, "unverified"?: true,
                "poetry": "here"|"other"|"both"?,
                "shared": [{"label", "ids": ["3515"], "where": {"here": "Num 11:14", "other": "Exod 18:18"}}],
                "beats": [{"title", "here", "other", "shared"?}]?,
                "status": "seed"|"kept", "source", "note"?}]}

`here` is this book's side, `other` the mirrored book's (English verse
numbering for both; core converts the corpus through VerseMap.xml).
Strength is Lane's read: 3 = shared words, 2 = the same story beat, 1 =
thematic. A strength-3 pair needs at least one `shared` entry that passes;
a `shared` entry that fails is an error, never a quiet downgrade.
"""
import argparse
import json
import os
import re
import sys

from biblecore import audit as atc
from biblecore import lang
from biblecore.book import book, on_reset
from biblecore.corpus import oshb
from biblecore.roots import bare_id, is_id_segment, is_precise, lemma_key

TIERS = ("chiasm", "echo")
POETRY = ("here", "other", "both")
STATUSES = ("seed", "kept")
TOP_KEYS = {"_note", "version", "centre", "sources", "pairs"}
PAIR_KEYS = {"id", "tier", "pos", "here", "other", "title", "strength", "poetry",
             "shared", "beats", "status", "source", "note", "strength_why", "unverified"}
BEAT_KEYS = {"title", "here", "other", "shared"}
SHARED_KEYS = {"label", "ids", "where"}
PROPOSAL_KEYS = {"ref", "to", "tier", "title", "strength", "shared", "note"}
ID_RE = re.compile(r"^[A-Za-z0-9-]+$")
MAX_TWIN_VERSES = 30      # the pack prints at most this many twin verses
RARE_SHARED = 300         # a shared lead occurring in more verses than this is too common to signal
MAX_SHARED_LEADS = 12
MAX_EXODUS_LEADS = 10     # per kind, for a unit that has no pair

# a half-verse letter ('21:18a') is read as the whole verse, as audit.parse_range does
SPAN_RE = re.compile(r"^\s*((?:[1-3]\s?)?[A-Za-z]+)\s+(\d+):(\d+)[a-z]?"
                     r"(?:\s*[–-]\s*(?:(\d+):)?(\d+)[a-z]?)?\s*$")


class MirrorError(ValueError):
    pass


# ------------------------------------------------------------------- spans

def display(osis):
    """'1Sam' -> '1 Sam'; 'Exod' -> 'Exod' (how a study cites it)."""
    return re.sub(r"^(\d)", r"\1 ", osis)


_BY_NAME = {}
for _o in oshb.BOOK_IDS:
    _BY_NAME[_o] = _o
    _BY_NAME[display(_o)] = _o


def parse_span(text):
    """'Num 15:32–21:9' -> ('Num', (15, 32), (21, 9)); None if it isn't one
    span of one book. A single verse is a span with lo == hi."""
    m = SPAN_RE.match(text or "") if isinstance(text, str) else None
    if not m:
        return None
    osis = _BY_NAME.get(re.sub(r"\s+", " ", m.group(1)))
    if osis is None:
        return None
    lo = (int(m.group(2)), int(m.group(3)))
    if m.group(5):
        hi = (int(m.group(4)) if m.group(4) else lo[0], int(m.group(5)))
    else:
        hi = lo
    return (osis, lo, hi) if hi >= lo else None


def span_text(osis, lo, hi):
    a = f"{display(osis)} {lo[0]}:{lo[1]}"
    if hi == lo:
        return a
    return a + ("–" + (f"{hi[0]}:" if hi[0] != lo[0] else "") + str(hi[1]))


def contains(outer, inner):
    return (outer[0] == inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2])


def overlaps(a, b):
    return a[0] == b[0] and a[1] <= b[2] and b[1] <= a[2]


# ------------------------------------------------------------------- corpus

_cache = {}
on_reset(_cache.clear)


def words_of(b, osis):
    """The word rows of this book or of a mirrored one, ch/v in displayed numbering."""
    if osis == b.osis:
        return atc.load_words()
    return oshb.load_other_words(osis, b)


def verse_index(b, osis):
    """{(ch, v): [word rows]} in text order."""
    key = ("index", b.root, osis)
    if key not in _cache:
        idx = {}
        for w in words_of(b, osis):
            idx.setdefault((w["ch"], w["v"]), []).append(w)
        _cache[key] = idx
    return _cache[key]


def span_verses(idx, sp):
    return sorted(cv for cv in idx if sp[1] <= cv <= sp[2])


def lemma_keys(lemma_field):
    from biblecore.unit_pack import _lemma_keys
    return _lemma_keys(lemma_field)


def ids_in(idx, sp):
    """Every lemma key and bare id found in a span's words."""
    keys, bares = set(), set()
    for cv in span_verses(idx, sp):
        for w in idx[cv]:
            for k in lemma_keys(w["lemma"]):
                keys.add(k)
                bares.add(bare_id(k))
    return keys, bares


def has_id(found, wanted):
    keys, bares = found
    try:
        wk = lemma_key(wanted)
    except ValueError:
        return False
    return wk in keys if is_precise(wk) else wk in bares


# --------------------------------------------------------------------- data

def data_path(b, m):
    return os.path.join(b.path("data"), m["file"])


def load_all(b=None):
    """[(mirror entry, data dict)] for each book.json mirrors entry; raises
    MirrorError when a file is missing or isn't JSON."""
    b = b or book()
    out = []
    for m in b.mirrors:
        path = data_path(b, m)
        try:
            with open(path, encoding="utf-8") as fh:
                out.append((m, json.load(fh)))
        except FileNotFoundError:
            raise MirrorError(f"data/{m['file']} not found (book.json mirrors lists it)")
        except ValueError as exc:
            raise MirrorError(f"data/{m['file']} doesn't parse: {exc}")
    return out


def pair_table(b=None):
    """{pair id: (pair dict, mirrored book's OSHB id)} across the mirror files."""
    out = {}
    for m, data in load_all(b):
        for p in data.get("pairs", []) or []:
            if isinstance(p, dict) and isinstance(p.get("id"), str):
                out[p["id"]] = (p, m["with"])
    return out


def all_shared(pair):
    """The pair's shared entries, its beats' included."""
    out = list(pair.get("shared") or [])
    for bt in pair.get("beats") or []:
        out += bt.get("shared") or []
    return out


def pair_spans(pair, b, other):
    """(here spans, other spans) a box for this pair may sit in: the pair's
    own, widened by nothing. Unparseable entries are dropped (check reports them)."""
    here = parse_span(pair.get("here"))
    there = parse_span(pair.get("other"))
    return here, there


# -------------------------------------------------------------------- check

def _ref(text, osis, idx, where, errs):
    """A span of the expected book that exists in its corpus, else None."""
    sp = parse_span(text)
    if sp is None:
        errs.append(f"{where}: {text!r} is not a reference like "
                    f"'{display(osis)} 3:4' or '{display(osis)} 3:4–9'")
        return None
    if sp[0] != osis:
        errs.append(f"{where}: {text!r} is in {display(sp[0])}, expected {display(osis)}")
        return None
    if sp[1] not in idx or sp[2] not in idx:
        errs.append(f"{where}: {text!r} does not resolve in the {display(osis)} text "
                    f"(no such verse; English numbering)")
        return None
    return sp


def _check_shared(entries, where, here_sp, other_sp, mine, theirs, ho, oo, errs):
    """Verify each shared entry's lemma ids occur in both of its refs;
    returns how many entries passed."""
    passed = 0
    if not isinstance(entries, list):
        errs.append(f"{where}: 'shared' must be a list")
        return 0
    for j, s in enumerate(entries):
        w = f"{where}.shared[{j}]"
        if not isinstance(s, dict):
            errs.append(f"{w}: must be an object {{label, ids, where}}")
            continue
        for k in sorted(set(s) - SHARED_KEYS):
            errs.append(f"{w}: unknown key '{k}' -- {{label, ids, where}}")
        label = s.get("label")
        if not (isinstance(label, str) and label.strip()):
            errs.append(f"{w}: missing 'label'")
        ids = s.get("ids")
        if not (isinstance(ids, list) and ids and all(isinstance(x, str) for x in ids)):
            errs.append(f"{w}: 'ids' must be a non-empty list of lemma ids (Strong's, e.g. \"3515\")")
            continue
        wh = s.get("where")
        if not (isinstance(wh, dict) and set(wh) == {"here", "other"}):
            errs.append(f"{w}: 'where' must be {{here: ref, other: ref}}")
            continue
        a = _ref(wh["here"], ho, mine, f"{w}.where.here", errs)
        c = _ref(wh["other"], oo, theirs, f"{w}.where.other", errs)
        if a is None or c is None:
            continue
        if here_sp is not None and not contains(here_sp, a):
            errs.append(f"{w}.where.here: {wh['here']} lies outside the pair's {span_text(*here_sp)}")
            continue
        if other_sp is not None and not contains(other_sp, c):
            errs.append(f"{w}.where.other: {wh['other']} lies outside the pair's {span_text(*other_sp)}")
            continue
        fa, fc = ids_in(mine, a), ids_in(theirs, c)
        failed = False
        for i in ids:
            for side, found in (("here", fa), ("other", fc)):
                if not has_id(found, i):
                    errs.append(f"{w} ({label}): H{i} is not in {wh[side]}; "
                                f"the shared-word claim fails")
                    failed = True
        if not failed:
            passed += 1
    return passed


def validate_data(b, other, data, file="mirror file", unit_rows=None, seen_ids=None):
    """-> (errors, notes) for one mirror file against both corpora."""
    errs, notes = [], []
    if not isinstance(data, dict):
        return [f"{file}: must be a JSON object"], []
    for k in sorted(set(data) - TOP_KEYS):
        errs.append(f"{file}: unknown key '{k}' -- {sorted(TOP_KEYS - {'_note'})}")
    if data.get("version") != 1:
        errs.append(f"{file}: 'version' must be 1")
    mine, theirs = verse_index(b, b.osis), verse_index(b, other)
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return errs + [f"{file}: 'pairs' must be a non-empty list"], notes

    c = data.get("centre")
    if c is not None:
        if not (isinstance(c, dict) and isinstance(c.get("span"), str)):
            errs.append(f"{file}: 'centre' must be {{span, label?, note?}}")
        else:
            ends = re.split(r"\s+[–-]\s+", c["span"])
            if len(ends) != 2:
                errs.append(f"{file}: centre.span must be 'Book C:V – Book C:V'")
            else:
                for end in ends:
                    sp = parse_span(end)
                    idx = verse_index(b, sp[0]) if sp and sp[0] in (b.osis, other) else None
                    if idx is None or sp[1] not in idx:
                        errs.append(f"{file}: centre end {end!r} does not resolve")
    srcs = data.get("sources")
    if srcs is not None:
        if not (isinstance(srcs, list) and all(
                isinstance(s, dict) and isinstance(s.get("id"), str) and isinstance(s.get("cite"), str)
                for s in srcs)):
            errs.append(f"{file}: 'sources' must be a list of {{id, cite, what?, boundary_note?}}")

    ids, poss, spans = {}, {}, {}
    seen_ids = seen_ids if seen_ids is not None else {}
    for i, p in enumerate(pairs):
        where = f"pair[{i}]"
        if not isinstance(p, dict):
            errs.append(f"{where}: must be an object")
            continue
        pid = p.get("id")
        where = f"pair {pid}" if isinstance(pid, str) else where
        for k in sorted(set(p) - PAIR_KEYS):
            errs.append(f"{where}: unknown key '{k}'")
        if not (isinstance(pid, str) and ID_RE.match(pid)):
            errs.append(f"{where}: 'id' must match [A-Za-z0-9-]")
        elif pid in ids or pid in seen_ids:
            errs.append(f"{where}: id used twice")
        else:
            ids[pid] = p
            seen_ids[pid] = file
        tier = p.get("tier")
        if tier not in TIERS:
            errs.append(f"{where}: 'tier' must be one of {list(TIERS)}")
        pos = p.get("pos")
        if tier == "chiasm":
            if not (isinstance(pos, int) and not isinstance(pos, bool) and pos >= 1):
                errs.append(f"{where}: a chiasm pair needs 'pos' (1 = outermost)")
            elif pos in poss:
                errs.append(f"{where}: 'pos' {pos} is also pair {poss[pos]}'s")
            else:
                poss[pos] = pid
        elif p.get("pos") is not None:
            errs.append(f"{where}: an echo pair has no 'pos'")
        st = p.get("strength")
        if st not in (1, 2, 3) or isinstance(st, bool):
            errs.append(f"{where}: 'strength' must be 1, 2 or 3")
        if p.get("status") not in STATUSES:
            errs.append(f"{where}: 'status' must be one of {list(STATUSES)}")
        if p.get("poetry") is not None and p["poetry"] not in POETRY:
            errs.append(f"{where}: 'poetry' must be one of {list(POETRY)}")
        for k in ("title", "source"):
            if not (isinstance(p.get(k), str) and p[k].strip()):
                errs.append(f"{where}: missing '{k}'")
        if "note" in p and not isinstance(p["note"], str):
            errs.append(f"{where}: 'note' must be a string")
        if "strength_why" in p and not isinstance(p["strength_why"], str):
            errs.append(f"{where}: 'strength_why' must be a string")
        if "unverified" in p and not isinstance(p["unverified"], bool):
            errs.append(f"{where}: 'unverified' must be true or false")
        hs = _ref(p.get("here"), b.osis, mine, f"{where}.here", errs)
        os_ = _ref(p.get("other"), other, theirs, f"{where}.other", errs)
        spans[pid] = (hs, os_)
        passed = _check_shared(p.get("shared") or [], where, hs, os_, mine, theirs,
                               b.osis, other, errs)
        beats = p.get("beats")
        if beats is not None and not (isinstance(beats, list) and beats):
            errs.append(f"{where}: 'beats' must be a non-empty list")
            beats = None
        for j, bt in enumerate(beats or []):
            w = f"{where}.beats[{j}]"
            if not isinstance(bt, dict):
                errs.append(f"{w}: must be an object {{title, here, other, shared?}}")
                continue
            for k in sorted(set(bt) - BEAT_KEYS):
                errs.append(f"{w}: unknown key '{k}'")
            if not (isinstance(bt.get("title"), str) and bt["title"].strip()):
                errs.append(f"{w}: missing 'title'")
            bh = _ref(bt.get("here"), b.osis, mine, f"{w}.here", errs)
            bo = _ref(bt.get("other"), other, theirs, f"{w}.other", errs)
            if bh and hs and not contains(hs, bh):
                errs.append(f"{w}.here: {bt.get('here')} lies outside the pair's {span_text(*hs)}")
            if bo and os_ and not contains(os_, bo):
                errs.append(f"{w}.other: {bt.get('other')} lies outside the pair's {span_text(*os_)}")
            passed += _check_shared(bt.get("shared") or [], w, bh or hs, bo or os_,
                                    mine, theirs, b.osis, other, errs)
        if st == 3 and not passed:
            errs.append(f"{where}: strength 3 needs a passing 'shared' entry (shared words "
                        f"present in both passages). Add the evidence or set strength 2; "
                        f"a failed claim never keeps its third dot")

    notes += _structure_notes(b, ids, spans, unit_rows)
    return errs, notes


def _structure_notes(b, ids, spans, unit_rows):
    """Reported, never failing: nesting, overlap, an order that doesn't reverse,
    and pairs wider than one unit."""
    notes = []
    for side, name in ((0, "here"), (1, "other")):
        sp = {pid: spans[pid][side] for pid in ids if spans.get(pid) and spans[pid][side]}
        for a in sp:
            inside = [q for q in sp if q != a and sp[q] != sp[a] and contains(sp[a], sp[q])]
            if inside:
                notes.append(f"nesting: {a} contains {', '.join(inside)} ({name} side)")
            for q in sp:
                if (q > a and overlaps(sp[a], sp[q])
                        and not contains(sp[a], sp[q]) and not contains(sp[q], sp[a])):
                    notes.append(f"overlap: {a} and {q} overlap ({name} side)")
    chi = sorted((p["pos"], pid) for pid, p in ids.items()
                 if p.get("tier") == "chiasm" and isinstance(p.get("pos"), int)
                 and spans.get(pid) and all(spans[pid]))
    for (_pa, a), (_pb, c) in zip(chi, chi[1:]):
        (ha, oa), (hc, oc) = spans[a], spans[c]
        if contains(oa, oc) or contains(oc, oa) or contains(ha, hc) or contains(hc, ha):
            continue    # nested pairs are reported as nesting, not as an order fault
        if oc[1] < oa[1] or hc[1] > ha[1]:
            notes.append(f"order: {a} then {c} does not reverse cleanly "
                         f"(the other book's order should rise and this book's fall with position)")
    if unit_rows:
        for pid in ids:
            hs = spans.get(pid, (None, None))[0]
            if hs:
                us = [n for n, lo, hi in unit_rows if overlaps(hs, (b.osis, lo, hi))]
                if len(us) > 1:
                    notes.append(f"wide: {pid} ({span_text(*hs)}) spans units {us[0]}-{us[-1]}")
    return list(dict.fromkeys(notes))


def check(b=None):
    """-> (errors, notes) over every mirror file; ([], []) when the book mirrors nothing."""
    b = b or book()
    if not b.mirrors:
        return [], []
    try:
        loaded = load_all(b)
    except MirrorError as exc:
        return [str(exc)], []
    from biblecore import unit_pack
    try:
        units = json.load(open(b.data("units.json"), encoding="utf-8"))["units"]
        unit_rows = unit_pack.unit_ranges(units)
    except (OSError, KeyError, ValueError):
        unit_rows = None
    errs, notes, seen = [], [], {}
    total = 0
    for m, data in loaded:
        e, n = validate_data(b, m["with"], data, m["file"], unit_rows, seen)
        errs += e
        notes += n
        total += len(data.get("pairs") or []) if isinstance(data, dict) else 0
    return errs, ([f"{total} pair(s)"] + notes)


# -------------------------------------------------------- strength dots (build)

BOX_RE = re.compile(r'(<aside\s+class="mirror"([^>]*)>)(.*?)(</aside>)', re.S)
STRENGTH_RE = re.compile(r'<span class="strength"[^>]*>.*?</span>', re.S)


def dots(n):
    return "●" * n + "○" * (3 - n)


def strength_span(n):
    return (f'<span class="strength" data-n="{n}" title="Lane\'s read" '
            f'aria-label="Lane\'s read: {n} of 3">{dots(n)}</span>')


def fill_html(html, table):
    """A fragment with each chiasm box's strength span written from the data
    file (inserted before </h4> when the box has none). Echo boxes and boxes
    of unknown pairs are left for the component check to report."""
    def one(m):
        open_tag, attrs, body, close = m.groups()
        pm = re.search(r'data-pair="([^"]*)"', attrs)
        hit = table.get(pm.group(1)) if pm else None
        if not hit or hit[0].get("tier") != "chiasm" or hit[0].get("strength") not in (1, 2, 3):
            return m.group(0)
        span = strength_span(hit[0]["strength"])
        if STRENGTH_RE.search(body):
            body = STRENGTH_RE.sub(lambda _m: span, body, count=1)
        else:
            body = re.sub(r"</h4>", " " + span + "</h4>", body, count=1)
        return open_tag + body + close
    return BOX_RE.sub(one, html)


def fill_units(b=None):
    """Write the dots into every built unit that has a mirror box; returns the
    unit numbers changed."""
    b = b or book()
    table = pair_table(b)
    changed = []
    for u in json.load(open(b.data("units.json"), encoding="utf-8"))["units"]:
        path = b.unit_path(u["n"])
        if not u.get("built") or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            html = fh.read()
        if 'class="mirror"' not in html:
            continue
        new = fill_html(html, table)
        if new != html:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new)
            changed.append(u["n"])
    return changed


# ------------------------------------------------------------- the pack section

_bible = {}
on_reset(_bible.clear)


def _bible_and_freq(b):
    key = b.path("wlc")
    if key not in _bible:
        from biblecore import leads
        bible = leads.load_bible()
        _bible[key] = (bible, leads.verse_freq(bible))
    return _bible[key]


def _bare_ids_of(lemma):
    out = []
    for seg in lemma.split("/"):
        seg = seg.strip()
        if is_id_segment(seg):
            try:
                out.append(bare_id(seg))
            except ValueError:
                pass
    return out


def _token(w):
    try:
        tr = lang.adapter().transliterate_word(w["surface"], w["lemma"], w.get("morph"))
    except Exception:
        tr = lang.adapter().transliterate(w["surface"])
    ids = "+".join("H" + i for i in _bare_ids_of(w["lemma"]))
    return f"{tr} [{ids}]" if ids else tr


def _twin_lines(idx, osis, sp, prefer, cap=MAX_TWIN_VERSES):
    """(lines, trimmed note) for a twin span; past `cap` verses it keeps the
    verses with a preferred lemma, then the opening ones."""
    verses = span_verses(idx, sp)
    note = ""
    if len(verses) > cap:
        want = [cv for cv in verses if any(
            set(_bare_ids_of(w["lemma"])) & prefer for w in idx[cv])]
        keep = want[:cap]
        keep += [cv for cv in verses if cv not in keep][:max(0, cap - len(keep))]
        verses, note = sorted(keep), (f"_Trimmed to {len(keep)} of {len(span_verses(idx, sp))} "
                                      f"verses (those with the pair's shared or rare shared words, "
                                      f"then the opening ones); read the rest from the word table._")
    lines = [f"- {display(osis)} {cv[0]}:{cv[1]} — " + " ".join(_token(w) for w in idx[cv])
             for cv in verses]
    return lines, note


def _gloss_rows(b, idx, sps, lem):
    """Lemma rows for the twin text: gloss only where lemmas.json has it."""
    seen = {}
    for sp in sps:
        for cv in span_verses(idx, sp):
            for w in idx[cv]:
                for k in lemma_keys(w["lemma"]):
                    seen.setdefault(k, _token(w).split(" [")[0])
    rows = []
    for k in sorted(seen, key=lambda x: (int(bare_id(x)), x)):
        e = lem.get(k) or lem.get(bare_id(k)) or {}
        rows.append(f"| {k} | {seen[k]} | {e.get('g') or '— (chat supplies)'} |")
    return rows


def pack_section(b, n, lo, hi, row):
    """Markdown lines for a unit-pack's mirror section(s), '' per mirror when
    the book mirrors nothing. `lo`/`hi` are the unit's (ch, v) ends."""
    if not b.mirrors:
        return []
    out = []
    unit_sp = (b.osis, lo, hi)
    try:
        loaded = load_all(b)
    except MirrorError as exc:
        return ["## Mirror", "", f"_{exc}_", ""]
    try:
        lem = json.load(open(b.data("lemmas.json"), encoding="utf-8")).get("lemmas", {})
    except (OSError, ValueError):
        lem = {}
    mine = verse_index(b, b.osis)
    for m, data in loaded:
        other = m["with"]
        name = oshb.BOOK_NAMES[other]
        theirs = verse_index(b, other)
        hits = []
        for p in data.get("pairs") or []:
            hs = parse_span(p.get("here"))
            if hs and overlaps(hs, unit_sp):
                hits.append(p)
        out += [f"## {name} mirror", "",
                f"From data/{m['file']}. **A reading, not a fact:** the pairing and its "
                f"boundaries are a scholar's reading (see the file's `sources`); the strength "
                f"dots are Lane's (3 = shared words, 2 = the same story beat, 1 = thematic). "
                f"Shared words below are leads in the same sense as the leads sheet. "
                f"Translate the {name} twin in the unit's voice; the glosses given are Strong's "
                f"identifiers, not renderings, and {name}-only lemmas have none.", ""]
        if data.get("centre"):
            c = data["centre"]
            out += [f"Centre of the mirror: {c.get('span', '')}"
                    + (f" ({c['label']})" if c.get("label") else "")
                    + (f". {c['note']}" if c.get("note") else ""), ""]
        if not hits:
            out += _no_pair_leads(b, row, other, name, theirs)
            continue
        for p in sorted(hits, key=lambda x: (x.get("pos") or 99, x["id"])):
            out += _pair_block(b, p, other, name, mine, theirs, unit_sp, lem)
    return out


def _pair_block(b, p, other, name, mine, theirs, unit_sp, lem):
    hs, os_ = parse_span(p["here"]), parse_span(p["other"])
    head = (f"### Pair {p['id']}: {p['title']} ({p['tier']}"
            + (f", position {p['pos']}" if p.get("pos") else "")
            + f", strength {p['strength']} of 3, {p['status']})")
    L = [head, "",
         f"- This book: {p['here']}" + (" (pair spans several units; this unit overlaps it)"
                                        if not contains(unit_sp, hs) else ""),
         f"- {name} twin: {p['other']}",
         f"- Source: {p['source']}"]
    if p.get("poetry"):
        side = {"here": b.name, "other": name, "both": "both sides"}[p["poetry"]]
        L.append(f"- Poetry: {side}. A poetry twin gets its reference and title in the box, no rows.")
    if p.get("note"):
        L.append(f"- Note: {p['note']}")
    # beats overlapping the unit narrow the twin text
    beats = [bt for bt in (p.get("beats") or [])
             if (parse_span(bt.get("here")) and overlaps(parse_span(bt["here"]), unit_sp))]
    for bt in beats:
        L.append(f"- Beat in this unit: {bt['title']}: {bt['here']} ↔ {bt['other']}")
    twin_spans = [parse_span(bt["other"]) for bt in beats] or [os_]
    shared = list(p.get("shared") or []) + [s for bt in beats for s in bt.get("shared") or []]
    if shared:
        L += ["", "Shared words (verified against the corpus when the book last built):"]
        for s in shared:
            L.append(f"- {s['label']} ({', '.join('H' + i for i in s['ids'])}): "
                     f"{s['where']['here']} ↔ {s['where']['other']}")
    prefer = {bare_id(i) for s in shared for i in s["ids"]}
    # overlap of the unit's words and the twin's, rarest first
    bible, freq = _bible_and_freq(b)
    unit_ids = {i for cv in span_verses(mine, (b.osis, max(unit_sp[1], hs[1]), min(unit_sp[2], hs[2])))
                for w in mine[cv] for i in _bare_ids_of(w["lemma"])}
    twin_ids = {i for sp in twin_spans for cv in span_verses(theirs, sp)
                for w in theirs[cv] for i in _bare_ids_of(w["lemma"])}
    common = sorted((i for i in unit_ids & twin_ids if freq[i] <= RARE_SHARED),
                    key=lambda i: (freq[i], int(i)))[:MAX_SHARED_LEADS]
    if common:
        L += ["", "Words in both the unit and the twin, rarest first (leads, not conclusions):"]
        for i in common:
            e = lem.get(i) or {}
            mark = " — a shared entry above" if i in prefer else ""
            L.append(f"- H{i}{', ' + e['g'] if e.get('g') else ''}: "
                     f"{freq[i]} verses in the Hebrew Bible{mark}")
    prefer |= set(common)
    L += ["", f"{name} twin text (word order, transliteration, Strong's number; native script is never in the pack):"]
    for sp in twin_spans:
        lines, note = _twin_lines(theirs, other, sp, prefer)
        L += lines
        if note:
            L += ["", note]
    L += ["", "| lemma | form | gloss (lemmas.json) |", "|---|---|---|"]
    L += _gloss_rows(b, theirs, twin_spans, lem)
    L.append("")
    return L


def _no_pair_leads(b, row, other, name, theirs):
    """For a unit with no pair: verses of the other book that share rare words
    or two-word phrases with the unit, as raw material for a proposal."""
    from biblecore import leads
    bible, freq = _bible_and_freq(b)
    uv = leads.passage_verses(bible, row["passage"])
    glosses = leads.load_glosses()
    L = [f"No pair of the {name} mirror overlaps this unit. Verses of {name} that share rare "
         f"words or a two-word phrase with it follow, as raw material if you see a connection "
         f"to propose in `mirror[]` (leads, not conclusions).", ""]
    rare = []
    for lead in leads.rare_leads(bible, freq, uv):
        hits = [(r, w) for r, w in lead["hits"] if r.split(".")[0] == other]
        if hits:
            rare.append((lead, hits))
    rare.sort(key=lambda x: x[0]["freq"])
    L.append(f"**Rare words** ({min(len(rare), MAX_EXODUS_LEADS)} of {len(rare)}):")
    if not rare:
        L.append("- _none_")
    for lead, hits in rare[:MAX_EXODUS_LEADS]:
        here = ", ".join(leads.fmt_ref(r).split(" ", 1)[1] for r in lead["here"][:4])
        L.append(f"- {leads.translit(lead['word'])} (H{lead['id']}, {glosses.get(lead['id'], '?')}): "
                 f"{b.abbrev} {here} ↔ " + "; ".join(leads.fmt_ref(r) for r, _w in hits[:4])
                 + f" ({lead['freq']} verses in the Hebrew Bible)")
    phrases = []
    for lead in leads.phrase_leads(bible, freq, uv):
        hits = [(r, p) for r, p in lead["hits"] if r.split(".")[0] == other]
        if hits:
            phrases.append((lead, hits))
    L += ["", f"**Two-word phrases** ({min(len(phrases), MAX_EXODUS_LEADS)} of {len(phrases)}):"]
    if not phrases:
        L.append("- _none_")
    for lead, hits in phrases[:MAX_EXODUS_LEADS]:
        ws = lead["words"]
        here = ", ".join(leads.fmt_ref(r).split(" ", 1)[1] for r in lead["here"][:4])
        L.append(f"- {' '.join(leads.translit(w) for w in ws)} ({' + '.join('H' + w[0] for w in ws)}): "
                 f"{b.abbrev} {here} ↔ " + "; ".join(leads.fmt_ref(r) for r, _p in hits[:4]))
    L.append("")
    return L


# ------------------------------------------------- proposals (meta `mirror[]`)

def validate_meta(meta):
    """Shape problems with a unit meta block's optional mirror[] (no corpus)."""
    errs = []
    ms = meta.get("mirror")
    if ms is None:
        return errs
    if not isinstance(ms, list):
        return ["mirror must be a list"]
    for i, e in enumerate(ms):
        w = f"mirror[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{w}: must be an object {{ref, to, tier, title, strength, shared?, note}}")
            continue
        for k in sorted(set(e) - PROPOSAL_KEYS):
            errs.append(f"{w}: unknown key '{k}' -- {{ref, to, tier, title, strength, shared?, note}}")
        if not re.fullmatch(r"\d+:\d+(?:[–-](?:\d+:)?\d+)?", str(e.get("ref", ""))):
            errs.append(f"{w}: 'ref' must be a bare 'C:V' or 'C:V–V' in this book (e.g. '11:14–17')")
        if not parse_span(e.get("to")):
            errs.append(f"{w}: 'to' must name a span like 'Exod 18:13–18'")
        if e.get("tier") not in TIERS:
            errs.append(f"{w}: 'tier' must be one of {list(TIERS)}")
        if e.get("strength") not in (1, 2, 3) or isinstance(e.get("strength"), bool):
            errs.append(f"{w}: 'strength' must be 1, 2 or 3")
        for k in ("title", "note"):
            if not (isinstance(e.get(k), str) and e[k].strip()):
                errs.append(f"{w}: missing '{k}'")
        if "shared" in e and not isinstance(e["shared"], list):
            errs.append(f"{w}: 'shared' must be a list")
    return errs


def delta_path(b=None):
    return os.path.join((b or book()).path("out"), "mirror-delta.json")


def _load_delta(b):
    try:
        with open(delta_path(b), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"proposals": []}


def _write_delta(b, d):
    os.makedirs(os.path.dirname(delta_path(b)), exist_ok=True)
    with open(delta_path(b), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def port_proposals(meta, n, write=True):
    """Resolve a unit's mirror[] proposals against both corpora, write them to
    out/mirror-delta.json (replacing this unit's earlier ones) and return
    (proposals, errors). Refs that don't resolve are errors; a shared-word claim
    that fails is recorded on the proposal (and a strength 3 without evidence is
    marked unsupported) but the proposal still goes to Lane."""
    b = book()
    ms = meta.get("mirror") or []
    if not ms:
        return [], []
    if not b.mirrors:
        return [], ["mirror[]: this book's book.json declares no mirrors"]
    out, errs = [], []
    others = {m["with"] for m in b.mirrors}
    mine = verse_index(b, b.osis)
    for i, e in enumerate(ms):
        w = f"mirror[{i}]"
        to = parse_span(e["to"])
        if to[0] not in others:
            errs.append(f"{w}: {e['to']!r} is not in a book this one mirrors ({sorted(others)})")
            continue
        theirs = verse_index(b, to[0])
        local = []
        here = _ref(f"{display(b.osis)} {e['ref']}", b.osis, mine, f"{w}.ref", local)
        twin = _ref(e["to"], to[0], theirs, f"{w}.to", local)
        sh_errs, passed = [], 0
        if here and twin:
            passed = _check_shared(e.get("shared") or [], w, here, twin, mine, theirs,
                                   b.osis, to[0], sh_errs)
        errs += local
        if local:
            continue
        out.append({"unit": n, "ref": f"{display(b.osis)} {e['ref']}", "to": e["to"], "with": to[0],
                    "tier": e["tier"], "title": e["title"], "strength": e["strength"],
                    "shared": e.get("shared") or [], "note": e["note"],
                    "shared_failures": sh_errs, "shared_passed": passed,
                    "strength_supported": not (e["strength"] == 3 and not passed),
                    "status": "proposed"})
    for k, p in enumerate(out, 1):
        p["id"] = f"u{n}-{k}"
    if write:
        d = _load_delta(b)
        merged = [p for p in d["proposals"] if p.get("unit") != n] + out
        _write_delta(b, {"_note": "Mirror proposals from ported units. Lane decides: "
                                  "`python -m biblecore mirror keep ID` writes one to the data file; "
                                  "nothing writes it on its own. Scratch (out/ is gitignored).",
                         "proposals": merged})
    return out, errs


def print_proposals(props):
    """The port's section: each proposal as a question for Lane."""
    if not props:
        return
    print("")
    print(f"=== {len(props)} mirror proposal(s) for Lane ===")
    for p in props:
        print(f"  [{p['id']}] {p['ref']} ↔ {p['to']} — {p['title']} "
              f"({p['tier']}, strength {p['strength']})")
        print(f"      {p['note'].strip()}")
        if p["shared"]:
            print(f"      shared words: {p['shared_passed']} of {len(p['shared'])} entries pass")
        for f in p["shared_failures"]:
            print(f"      FAILS: {f}")
        if not p["strength_supported"]:
            print("      strength 3 has no passing shared word: it cannot be kept at 3")
        print("      keep / decline? (keep: python -m biblecore mirror keep ID)")


# ---------------------------------------------------------------- keep / decline

def _next_id(table):
    nums = [int(m.group(1)) for i in table if (m := re.fullmatch(r"K(\d+)", i))]
    return f"K{max(nums, default=0) + 1}"


def keep(pid, pos=None, strength=None):
    """Write a proposal from out/mirror-delta.json into its data file as
    status 'kept'. Re-checks the file and rolls back if the check fails."""
    b = book()
    d = _load_delta(b)
    p = next((x for x in d["proposals"] if x.get("id") == pid), None)
    if p is None:
        raise MirrorError(f"no proposal {pid!r} in {delta_path(b)}")
    if p["status"] != "proposed":
        raise MirrorError(f"{pid} is already {p['status']}")
    m = next(x for x in b.mirrors if x["with"] == p["with"])
    path = data_path(b, m)
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    data = json.loads(raw)
    table = {q["id"]: q for q in data["pairs"]}
    st = strength if strength is not None else p["strength"]
    pair = {"id": _next_id(table), "tier": p["tier"]}
    if p["tier"] == "chiasm":
        if pos is None:
            raise MirrorError("a chiasm proposal needs --pos N (1 = outermost)")
        pair["pos"] = pos
    pair.update({"here": p["ref"], "other": p["to"], "title": p["title"],
                 "strength": st, "status": "kept", "source": f"proposed in unit {p['unit']}"})
    if p["shared"]:
        pair["shared"] = p["shared"]
    pair["note"] = p["note"]
    data["pairs"].append(pair)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    errs, _notes = check(b)
    if errs:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(raw)
        raise MirrorError(f"{pid} not kept; the data file would fail its check:\n  - "
                          + "\n  - ".join(errs))
    p["status"], p["kept_as"] = "kept", pair["id"]
    _write_delta(b, d)
    return pair


def decline(pid):
    b = book()
    d = _load_delta(b)
    p = next((x for x in d["proposals"] if x.get("id") == pid), None)
    if p is None:
        raise MirrorError(f"no proposal {pid!r} in {delta_path(b)}")
    p["status"] = "declined"
    _write_delta(b, d)
    return p


# ---------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore mirror", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", nargs="?", choices=["keep", "decline"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--pos", type=int)
    ap.add_argument("--strength", type=int, choices=[1, 2, 3])
    a = ap.parse_args(argv)
    b = book()
    if a.action:
        if not a.id:
            sys.exit(f"mirror {a.action} needs a proposal id (see out/mirror-delta.json)")
        try:
            if a.action == "keep":
                pair = keep(a.id, a.pos, a.strength)
                print(f"kept {a.id} as pair {pair['id']} in data/"
                      f"{next(m['file'] for m in b.mirrors if m['with'] == _other_of(pair, b))}")
            else:
                decline(a.id)
                print(f"declined {a.id}")
        except MirrorError as exc:
            sys.exit(str(exc))
        return 0
    if not b.mirrors:
        print("mirror: this book mirrors nothing")
        return 0
    errs, notes = check(b)
    for e in errs:
        print("  ERROR", e)
    for n in notes[1:]:
        print("  note:", n)
    if errs:
        print(f"mirror: {len(errs)} problem(s)")
        return 1
    changed = fill_units(b)
    print(f"mirror: {notes[0]} ok" + (f"; strength dots written in unit(s) {changed}" if changed else ""))
    return 0


def _other_of(pair, b):
    sp = parse_span(pair["other"])
    return sp[0]
