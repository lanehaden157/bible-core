"""Look up LXX verses in the fetched corpus (Rahlfs 1935), and run a unit's
`checks[]` against it.

    python -m biblecore lxx Isa 22:22
    python -m biblecore lxx Isa 51:1-2 --expect petra abraam
    python -m biblecore lxx Deut 5:26 --expect '!kleis'   # '!' = must be absent
    python -m biblecore lxx --checks 16        # source-artifacts/<slug>_16_*.html
    python -m biblecore lxx --checks unit-16
    python -m biblecore lxx --checks path/to/artifact.html   # or a .json list of checks

A verse prints as its words' lemma keys in text order: the transliterated
lemma ids the rest of the core uses (`petra`, `hades`; a homograph keeps its
digit, `tis2`), since that is what `expect` names. An expectation matches a
key exactly or with a digit suffix (`tis` matches `tis2`), ignoring macrons and accents.

A check is {ref, claim, expect}; `ref` may name several passages ("Isa 38:10 /
Wis 16:13"), whose words are pooled. Each `expect` entry is a lemma that
should be present, or `!lemma` that should be absent. The result is
confirmed (every entry holds), partial (some do) or not found (none do).
`checks[]` is dropped from a built unit at port time, so --checks reads the
source artifact. Needs `python -m biblecore fetch` to have been run once.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata

from biblecore.book import book

# LXX book code (corpus/lxx.py's own abbreviations) -> other spellings.
ALIASES = {
    "Gen": ["genesis", "gn"], "Exod": ["exodus", "ex", "exo"], "Lev": ["leviticus", "lv"],
    "Num": ["numbers", "nm", "nu"], "Deut": ["deuteronomy", "dt", "deu"],
    "Josh": ["joshua", "jos"], "Judg": ["judges", "jdg", "jg"], "Ruth": ["rth"],
    "1Sam": ["1samuel", "1sm"], "2Sam": ["2samuel", "2sm"],
    "1Kgs": ["1kings", "1ki", "1kg"], "2Kgs": ["2kings", "2ki", "2kg"],
    "1Chr": ["1chronicles", "1ch"], "2Chr": ["2chronicles", "2ch"],
    "1Esdr": ["1esdras"], "2Esdr": ["2esdras", "ezra", "ezr"],
    "Esth": ["esther", "est"], "Jdt": ["judith"], "1Mac": ["1maccabees"],
    "2Mac": ["2maccabees"], "3Mac": ["3maccabees"], "4Mac": ["4maccabees"],
    "Ps": ["psalm", "psalms", "psa", "pss"], "Prov": ["proverbs", "pr", "pro"],
    "Qoh": ["ecclesiastes", "eccl", "ecc", "eccles"], "Cant": ["song", "songofsongs",
        "songofsolomon", "sos", "canticles"], "Job": [], "Wis": ["wisdom", "wisdomofsolomon"],
    "Sir": ["sirach", "ecclesiasticus"], "Hos": ["hosea"], "Mic": ["micah"],
    "Amos": ["am"], "Joel": ["jl"], "Jonah": ["jon"], "Obad": ["obadiah", "ob"],
    "Nah": ["nahum"], "Hab": ["habakkuk"], "Zeph": ["zephaniah", "zep"],
    "Hag": ["haggai"], "Zech": ["zechariah", "zec"], "Mal": ["malachi"],
    "Isa": ["isaiah", "is"], "Jer": ["jeremiah"], "Bar": ["baruch"],
    "Lam": ["lamentations"], "Ezek": ["ezekiel", "eze", "ezk"],
    "Dan": ["daniel", "dn"], "Sus": ["susanna"], "Bel": ["belandthedragon"],
}

# "Isa 22:22", "2 Sam 22:2", "Isa 51:1-2", "Isa 51:1–52:2" (en dash too)
REF_RE = re.compile(
    r"((?:[1-4]\s?)?[A-Za-z][A-Za-z.]*(?:\s+of\s+[A-Za-z]+)?)\s+(\d+):(\d+)"
    r"(?:\s*[-–—]\s*(?:(\d+):)?(\d+))?")


# New Testament book names (first word of a ref): not in the LXX, so a check
# against one is skipped, not an error.
NT_BOOKS = {
    "matt", "matthew", "mt", "mark", "mk", "luke", "lk", "john", "jn", "acts",
    "rom", "romans", "cor", "corinthians", "gal", "galatians", "eph",
    "ephesians", "phil", "philippians", "col", "colossians", "thess",
    "thessalonians", "tim", "timothy", "titus", "phlm", "philemon", "heb",
    "hebrews", "jas", "james", "pet", "peter", "jude", "rev", "revelation",
}


def is_nt_ref(text):
    """True when every passage in a ref string names an NT book."""
    names = [m.group(1) for m in REF_RE.finditer(text)]
    return bool(names) and all(
        re.sub(r"^[1-3]", "", _norm(n)) in NT_BOOKS for n in names)


def _norm(name):
    return re.sub(r"[\s.]", "", name).lower()


def resolve_book(name, codes):
    """The LXX book code for a spelling ('2 Sam', 'Isaiah'), or None."""
    want = _norm(name)
    table = {_norm(c): c for c in codes}
    for code, alts in ALIASES.items():
        if code in codes:
            for a in alts:
                table.setdefault(a, code)
    if want in table:
        return table[want]
    hits = {c for k, c in table.items() if len(want) >= 3 and k.startswith(want)}
    return hits.pop() if len(hits) == 1 else None


def parse_refs(text, codes):
    """[(code, (c1, v1), (c2, v2)), ...] for every passage a ref string names;
    ValueError for a book it can't place."""
    out = []
    for m in REF_RE.finditer(text):
        code = resolve_book(m.group(1), codes)
        if code is None:
            raise ValueError(f"unknown LXX book {m.group(1)!r} in {text!r}")
        c1, v1 = int(m.group(2)), int(m.group(3))
        c2 = int(m.group(4)) if m.group(4) else c1
        v2 = int(m.group(5)) if m.group(5) else v1
        out.append((code, (c1, v1), (c2, v2)))
    if not out:
        raise ValueError(f"no passage like 'Isa 22:22' in {text!r}")
    return out


def verse_words(lxx, code, lo, hi):
    """{(c, v): [lemma keys]} for the verses of one passage, in text order."""
    out = {}
    for c, v, key in lxx.get(code, ()):
        if lo <= (c, v) <= hi:
            out.setdefault((c, v), []).append(key)
    return out


def _fold(s):
    """Lowercase without macrons/accents: 'pylē' and 'pyle' are one key."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if not unicodedata.combining(c))


def _has(keys, lemma):
    lemma = _fold(lemma)
    return any(f == lemma or (f.startswith(lemma) and f[len(lemma):].isdigit())
               for f in map(_fold, keys))


def evaluate(keys, expect):
    """-> (status, [(entry, held)]) for the pooled lemma keys of a check."""
    entries = [expect] if isinstance(expect, str) else list(expect)
    held = []
    for e in entries:
        e = e.strip()
        if e.startswith("!"):
            held.append((e, not _has(keys, e[1:].strip())))
        else:
            held.append((e, _has(keys, e)))
    n = sum(1 for _e, ok in held if ok)
    status = "confirmed" if n == len(held) else "partial" if n else "not found"
    return status, held


def run_check(lxx, codes, check):
    """-> dict {status, held, keys, missing_verses} for one {ref, claim, expect}."""
    keys, missing = [], []
    for code, lo, hi in parse_refs(check["ref"], codes):
        words = verse_words(lxx, code, lo, hi)
        if not words:
            missing.append(f"{code} {lo[0]}:{lo[1]}")
        for ks in words.values():
            keys.extend(ks)
    status, held = evaluate(keys, check["expect"])
    return {"status": status, "held": held, "keys": keys, "missing": missing}


def checks_from(arg):
    """The checks[] a --checks argument names: a unit number or slug (its
    source artifact), an artifact .html, or a .json list (or meta object)."""
    from biblecore import meta as um
    if os.path.isfile(arg):
        path = arg
    else:
        m = re.fullmatch(r"(?:unit-)?(\d+)", arg)
        if not m:
            sys.exit(f"--checks: {arg!r} is neither a unit number nor a file")
        matches = sorted(glob.glob(book().source_glob(int(m.group(1)))))
        if not matches:
            sys.exit(f"no source artifact: "
                     f"{os.path.relpath(book().source_glob(int(m.group(1))), book().root)}")
        path = matches[0]
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    if path.endswith(".json"):
        data = json.loads(raw)
        return data.get("checks", []) if isinstance(data, dict) else data
    meta = um.parse(raw)
    if meta is None:
        sys.exit(f"{path} has no unit-meta block")
    return meta.get("checks", []) or []


def _print_verses(lxx, codes, ref):
    for code, lo, hi in parse_refs(ref, codes):
        words = verse_words(lxx, code, lo, hi)
        if not words:
            print(f"{code} {lo[0]}:{lo[1]}: no such verse in this LXX")
        for (c, v), ks in words.items():
            print(f"{code} {c}:{v}: {' '.join(ks)}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore lxx", description=__doc__.split("\n\n")[0])
    ap.add_argument("ref", nargs="*", help="Book C:V[-V], e.g. Isa 22:22")
    ap.add_argument("--expect", nargs="+", metavar="LEMMA",
                    help="lemma keys that should be present ('!lemma': absent)")
    ap.add_argument("--checks", metavar="UNIT|FILE",
                    help="run a unit's checks[] (unit number, artifact .html or .json)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # lemma keys carry macrons
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not a.checks and not a.ref:
        ap.error("give a passage (Isa 22:22) or --checks UNIT")

    from biblecore.leads import load_greek_corpus
    _nt, lxx, codes = load_greek_corpus()

    if a.checks:
        checks = checks_from(a.checks)
        if not checks:
            print("no checks[] in that source")
            return 0
        counts = {}
        for c in checks:
            if is_nt_ref(c.get("ref", "")):
                print(f"{'SKIPPED':10} {c['ref']} — not LXX (New Testament)")
                counts["skipped (not LXX)"] = counts.get("skipped (not LXX)", 0) + 1
                continue
            try:
                r = run_check(lxx, codes, c)
            except ValueError as exc:
                print(f"? {c.get('ref', '?')}: {exc}")
                counts["error"] = counts.get("error", 0) + 1
                continue
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            print(f"{r['status'].upper():10} {c['ref']} — {c.get('claim', '').strip()}")
            for e, ok in r["held"]:
                print(f"{'':12}{'ok ' if ok else 'NO '} {e}")
            for m in r["missing"]:
                print(f"{'':12}no such verse in this LXX: {m}")
            if r["status"] != "confirmed":
                print(f"{'':12}lemmas: {' '.join(r['keys'])}")
        print("\n" + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
        return 0

    ref = " ".join(a.ref)
    try:
        _print_verses(lxx, codes, ref)
        if a.expect:
            r = run_check(lxx, codes, {"ref": ref, "expect": a.expect})
            print(f"\n{r['status'].upper()}: " + "; ".join(
                f"{'ok' if ok else 'NO'} {e}" for e, ok in r["held"]))
            return 0 if r["status"] == "confirmed" else 1
    except ValueError as exc:
        sys.exit(str(exc))
    return 0
