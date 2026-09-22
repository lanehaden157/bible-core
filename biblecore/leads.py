"""Canon leads: where a unit's rare words and shared phrases occur elsewhere
in the Hebrew Bible, as a short reading list for the project side's
intertext pass.

    python -m biblecore leads 3            # -> canon-leads/canon-leads-unit-03.md
    python -m biblecore leads 3 --rare 30  # looser rare-word cutoff
    python -m biblecore leads --all        # every unit in data/units.json
    python -m biblecore leads              # built units + the next unbuilt one

LEADS, NOT CONCLUSIONS. The mechanical half of the intertext pass: Claude
Code finds where words recur, the project side decides which recurrences
mean anything. It lists only two kinds of hit, because listing every word is
useless (measured on Joshua 2: 147 lemmas, ~33,000 Torah verses):

  * rare words -- a lemma in the passage occurring in at most --rare verses
    across the Hebrew Bible (default 20), and somewhere outside this book
  * shared phrases -- two adjacent lemmas from one verse of the passage that
    stand adjacent in a Torah verse too, where neither word is ultra-common
    and the pair itself is not a stock formula

Blind by design to common words, themes, type-scenes and the New Testament.
For a Torah book, "shared with the Torah" includes the book itself; the
book's own verses are skipped as hits, so the phrases found are the ones
shared with the *other* four.

Source: morphhb's whole Hebrew Bible (book.json paths.wlc). Lemma identity
is the bare Strong's number. Everything printed is transliterated; no
native script reaches the output. Hebrew books only.
"""
import argparse
import collections
import json
import os
import re
import sys

from biblecore.audit import parse_range
from biblecore.book import book as current_book
from biblecore.lang import hebrew

BOOKS = ["Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam",
         "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job",
         "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan",
         "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph",
         "Hag", "Zech", "Mal"]
TORAH = set(BOOKS[:5])
DISPLAY = {"Ps": "Ps", "Song": "Song", "1Sam": "1 Sam", "2Sam": "2 Sam",
           "1Kgs": "1 Kgs", "2Kgs": "2 Kgs", "1Chr": "1 Chr", "2Chr": "2 Chr"}

RARE_DEFAULT = 20
PHRASE_WORD_MAX = 300    # a phrase word occurring in more verses than this is too common to signal
PHRASE_TOTAL_MAX = 15    # a pair in more Torah verses than this is a stock formula

VERSE_RE = re.compile(r'<verse osisID="([^"]+)">(.*?)</verse>', re.S)
WORD_RE = re.compile(r'<w [^>]*?lemma="([^"]+)"[^>]*?morph="([^"]+)"[^>]*>([^<]*)</w>')


def bare_ids(lemma):
    """'c/3722 b' -> ['3722']; '1007+' -> ['1007']; prefix segments dropped."""
    out = []
    for seg in lemma.split("/"):
        n = re.sub(r"[^0-9]", "", seg)
        if n:
            out.append(n)
    return out


def load_bible(wlc=None):
    """-> {book: [(ref, [(id, surface, lemma, morph), ...]), ...]} in canonical
    order. A word carrying two numeric lemmas (rare) yields one entry each."""
    wlc = wlc or current_book().path("wlc")
    if not os.path.isdir(wlc):
        sys.exit(f"morphhb not found at {wlc} -- run `npm ci` (package.json pins it)")
    bible = {}
    for book in BOOKS:
        with open(os.path.join(wlc, f"{book}.xml"), encoding="utf-8") as fh:
            text = fh.read()
        verses = []
        for ref, body in VERSE_RE.findall(text):
            words = []
            for lemma, morph, surface in WORD_RE.findall(body):
                for i in bare_ids(lemma):
                    words.append((i, surface, lemma, morph))
            verses.append((ref, words))
        bible[book] = verses
    return bible


def verse_freq(bible):
    freq = collections.Counter()
    for verses in bible.values():
        for _, words in verses:
            freq.update({w[0] for w in words})
    return freq


def load_glosses(path=None):
    """Strong's <def> phrases, joined -- a rough identifier for the reader,
    never a rendering (Strong's first sense misleads as a gloss)."""
    path = path or current_book().path("lexicon")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out = {}
    for num, body in re.findall(r'<entry id="H(\d+)">(.*?)</entry>', text, re.S):
        defs = re.findall(r"<def>(.*?)</def>", body, re.S)
        if defs:
            senses = list(dict.fromkeys(re.sub(r"<[^>]+>", "", d).strip() for d in defs))
            out[num] = "; ".join(senses[:3])
    return out


def fmt_ref(ref):
    book, c, v = ref.split(".")
    return f"{DISPLAY.get(book, book)} {c}:{v}"


def translit(word):
    _, surface, lemma, morph = word
    return hebrew.transliterate_word(surface, lemma, morph)


def passage_verses(bible, passage):
    lo, hi = parse_range(passage)
    return [(ref, words) for ref, words in bible[current_book().osis]
            if lo <= tuple(int(x) for x in ref.split(".")[1:]) <= hi]


def rare_leads(bible, freq, unit_verses, rare=RARE_DEFAULT):
    """Rare lemmas in the passage, with every occurrence outside this book."""
    own = current_book().osis
    seen = collections.OrderedDict()
    for ref, words in unit_verses:
        for w in words:
            if freq[w[0]] <= rare:
                seen.setdefault(w[0], {"word": w, "refs": []})
                if ref not in seen[w[0]]["refs"]:
                    seen[w[0]]["refs"].append(ref)
    leads = []
    for lid, info in seen.items():
        hits = []
        for book in BOOKS:
            if book == own:
                continue
            for ref, words in bible[book]:
                match = next((w for w in words if w[0] == lid), None)
                if match:
                    hits.append((ref, match))
        if hits:
            leads.append({"id": lid, "word": info["word"], "here": info["refs"],
                          "freq": freq[lid], "hits": hits})
    # Torah hits first, then fewest total occurrences -- the rarest link is the strongest signal
    leads.sort(key=lambda L: (not any(r.split(".")[0] in TORAH for r, _ in L["hits"]), L["freq"]))
    return leads


def phrase_leads(bible, freq, unit_verses):
    """Adjacent lemma pairs in the passage that also stand adjacent in the
    Torah. Both words must be under PHRASE_WORD_MAX verses; the pair must be
    in at most PHRASE_TOTAL_MAX Torah verses. Overlapping pairs in one verse
    merge into a single phrase ("Reubenite, Gadite, half-tribe of Manasseh"
    is one lead, not four), with the Torah verses of all its pairs."""
    own = current_book().osis
    torah_pairs = collections.defaultdict(list)
    for book in BOOKS[:5]:
        if book == own:
            continue
        for ref, words in bible[book]:
            for a, b in zip(words, words[1:]):
                torah_pairs[(a[0], b[0])].append((ref, a, b))

    def qualifies(a, b):
        key = (a[0], b[0])
        return (a[0] != b[0] and key in torah_pairs
                and freq[a[0]] <= PHRASE_WORD_MAX and freq[b[0]] <= PHRASE_WORD_MAX
                and len({h[0] for h in torah_pairs[key]}) <= PHRASE_TOTAL_MAX)

    leads = collections.OrderedDict()
    for ref, words in unit_verses:
        idx = [i for i in range(len(words) - 1) if qualifies(words[i], words[i + 1])]
        runs = []
        for i in idx:
            if runs and runs[-1][-1] == i - 1:
                runs[-1].append(i)
            else:
                runs.append([i])
        for run in runs:
            span = words[run[0]:run[-1] + 2]
            key = tuple(w[0] for w in span)
            hits = collections.OrderedDict()
            for i in run:
                for h_ref, x, y in torah_pairs[(words[i][0], words[i + 1][0])]:
                    hits.setdefault(h_ref, []).append((x, y))
            lead = leads.setdefault(key, {"words": span, "here": [], "hits": hits})
            if ref not in lead["here"]:
                lead["here"].append(ref)
    for lead in leads.values():
        order = {b: i for i, b in enumerate(BOOKS)}
        lead["hits"] = sorted(lead["hits"].items(), key=lambda kv: (
            order[kv[0].split(".")[0]], int(kv[0].split(".")[1]), int(kv[0].split(".")[2])))
    return list(leads.values())


def render(n, passage, rare_list, phrase_list, glosses, rare):
    ab = current_book().abbrev
    L = [f"# Canon leads — Unit {n} ({passage})", "",
         "Generated by `python -m biblecore leads` from the Hebrew Bible (morphhb). "
         "**Leads, not conclusions.** This lists where the unit's rare words and "
         "two-word phrases occur elsewhere. Deciding which ones matter is the "
         "intertext pass's job. Every lead gets a verdict in the ledger, a rejection included.", "",
         f"It cannot see: common words (rare cutoff: {rare} verses in the Hebrew Bible), "
         "links by theme or type-scene, or the New Testament. Search for those separately. "
         "Glosses are rough Strong's identifiers, not renderings.", ""]

    L += [f"## Shared phrases with the Torah ({len(phrase_list)})", ""]
    if not phrase_list:
        L += ["_None under the cutoffs._", ""]
    for p in phrase_list:
        ws = p["words"]
        here = ", ".join(fmt_ref(r).split(" ", 1)[1] for r in p["here"])
        ids = " + ".join(f"H{w[0]}" for w in ws)
        gl = " / ".join(glosses.get(w[0], "?") for w in ws)
        L.append(f"- **{' '.join(translit(w) for w in ws)}** ({ids}: {gl}) — {ab} {here}")
        for ref, pairs in p["hits"]:
            frag = " … ".join(f"{translit(x)} {translit(y)}" for x, y in pairs)
            L.append(f"  - {fmt_ref(ref)} — {frag}")
    L.append("")

    L += [f"## Rare words ({len(rare_list)})", ""]
    if not rare_list:
        L += ["_None under the cutoff._", ""]
    for r in rare_list:
        here = ", ".join(fmt_ref(x).split(" ", 1)[1] for x in r["here"])
        torah = [h for h in r["hits"] if h[0].split(".")[0] in TORAH]
        later = [h for h in r["hits"] if h[0].split(".")[0] not in TORAH]
        L.append(f"- **{translit(r['word'])}** (H{r['id']}, {glosses.get(r['id'], '?')}) — "
                 f"{ab} {here}; {r['freq']} verses in the Hebrew Bible")
        if torah:
            L.append("  - Torah: " + "; ".join(f"{fmt_ref(ref)} ({translit(w)})" for ref, w in torah))
        if later:
            L.append("  - Later: " + "; ".join(f"{fmt_ref(ref)} ({translit(w)})" for ref, w in later))
    L.append("")
    return "\n".join(L)


def _units():
    with open(current_book().data("units.json"), encoding="utf-8") as fh:
        return json.load(fh)["units"]


def build(n, rare=RARE_DEFAULT, bible=None, freq=None, glosses=None, out_dir=None):
    out_dir = out_dir or current_book().path("canon_leads")
    row = next((u for u in _units() if u["n"] == n), None)
    if row is None:
        raise ValueError(f"unit {n} is not in data/units.json")
    bible = bible or load_bible()
    freq = freq or verse_freq(bible)
    glosses = glosses if glosses is not None else load_glosses()
    uv = passage_verses(bible, row["passage"])
    md = render(n, row["passage"], rare_leads(bible, freq, uv, rare),
                phrase_leads(bible, freq, uv), glosses, rare)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"canon-leads-unit-{n:02d}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md)
    return path


def current_units(units):
    """Every built unit, plus the first unbuilt one -- the unit the project
    side is about to research, so its leads are waiting before pass 1."""
    out = [u["n"] for u in units if u.get("built")]
    nxt = next((u["n"] for u in sorted(units, key=lambda u: u["n"]) if not u.get("built")), None)
    if nxt is not None:
        out.append(nxt)
    return out


def main(argv=None):
    if current_book().language != "hebrew":
        print(f"canon leads read the Hebrew Bible; {current_book().name} is "
              f"{current_book().language} -- skipped")
        return 0
    ap = argparse.ArgumentParser(prog="biblecore leads")
    ap.add_argument("unit", nargs="?", type=int)
    ap.add_argument("--all", action="store_true", help="every unit in data/units.json")
    ap.add_argument("--rare", type=int, default=RARE_DEFAULT,
                    help=f"rare-word cutoff, in verses across the Hebrew Bible (default {RARE_DEFAULT})")
    a = ap.parse_args(argv)
    bible = load_bible()
    freq = verse_freq(bible)
    glosses = load_glosses()
    rows = _units()
    if a.unit:
        units = [a.unit]
    elif a.all:
        units = [u["n"] for u in rows]
    else:
        units = current_units(rows)
    for n in units:
        print("wrote", build(n, a.rare, bible, freq, glosses))
    return 0
