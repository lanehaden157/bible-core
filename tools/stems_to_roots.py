"""One-shot: propose data/roots.json id sets from a Greek book's stem-based
thread policy (Matthew's pipeline/thread-stems.json is the model this reads --
ARCHITECTURE.md plan B).

For every thread with a `stems` entry (not `phrase: true`), applies the same
match rule audit_thread_coverage.py uses -- accent-stripped, lowercase,
substring (or `^`-anchored word-start), minus `exclude` -- against a book's
own word table, and collects the MorphGNT lemma id (roots.py's id scheme,
lang/greek.lemma_key) of every word that matches. The result is a proposed
`ids` list per thread, ready to paste into data/roots.json after review.

Two things a stem match can get wrong that this script surfaces rather than
silently resolving:
  * a stem matches more than one distinct lemma id (a real homograph the
    thread-stems.json `exclude` list didn't catch, or two lexemes that
    happen to share a stem) -- printed as "MIXED", for a human to split
  * two different threads' proposed id sets share an id -- printed as
    "CLASH", the same ownership check roots.py's validate() enforces

Neither is fixed automatically. Read the report, adjust `exclude` in
thread-stems.json or split the thread's ids by hand, and re-run.

    python tools/stems_to_roots.py <book-root> <thread-stems.json> [<threads.json>]

Prints a JSON object {"roots": {slug: {"ids": [...], "note": "TODO"}}} for
the clean threads to stdout, and a report of MIXED/CLASH cases to stderr.
Nothing is written -- paste the reviewed result into data/roots.json by hand.
"""
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from biblecore.lang import greek  # noqa: E402

GREEKWORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def strip_accents(s):
    d = unicodedata.normalize("NFD", s)
    return ("".join(c for c in d if not unicodedata.combining(c))
            .lower().replace("ς", "σ"))  # final sigma -> medial


def compile_stems(stem_list):
    subs = [strip_accents(s[1:]) if s.startswith("^") else strip_accents(s)
            for s in stem_list]
    anchored = [s.startswith("^") for s in stem_list]
    pairs = list(zip(subs, anchored))

    def match(sw):
        return any(sw.startswith(s) if a else s in sw for s, a in pairs)
    return match


def load_book_words(book_root):
    """Read <book>-words.tsv (bible-core's own corpus format: word_id, ref,
    surface, lemma, morph) straight off disk, no book.json/book() context
    needed -- this tool runs standalone against any book root."""
    import glob
    cands = glob.glob(os.path.join(book_root, "*-words.tsv"))
    if not cands:
        sys.exit(f"no *-words.tsv in {book_root} -- run `python -m biblecore corpus` there first")
    with open(cands[0], encoding="utf-8") as f:
        import csv
        return list(csv.DictReader(f, delimiter="\t"))


def propose(words, stems_data):
    """-> {tid: {"ids": sorted[...], "surfaces": {lemma_id: {surface,...}}}}
    for every non-phrase thread in stems_data, using each word's surface
    form (accented Greek, no punctuation) as the match target and its
    already-resolved MorphGNT lemma id as what gets collected."""
    out = {}
    for tid, spec in stems_data["stems"].items():
        if spec.get("phrase"):
            continue
        stems = spec.get("stems")
        if not stems:
            continue
        match = compile_stems(stems)
        exclude = {strip_accents(x) for x in spec.get("exclude", [])}
        ids = {}  # lemma_id -> set(surface forms seen)
        for w in words:
            sw = strip_accents(w["surface"])
            if sw in exclude or not match(sw):
                continue
            ids.setdefault(w["lemma"], set()).add(w["surface"])
        out[tid] = ids
    return out


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: python tools/stems_to_roots.py <book-root> <thread-stems.json> [<threads.json>]")
    book_root = args[0]
    stems_path = args[1] if len(args) > 1 else None
    threads_path = args[2] if len(args) > 2 else None
    if not stems_path:
        sys.exit("usage: python tools/stems_to_roots.py <book-root> <thread-stems.json> [<threads.json>]")

    words = load_book_words(book_root)
    stems_data = json.load(open(stems_path, encoding="utf-8"))
    proposals = propose(words, stems_data)

    threads_roots = {}
    if threads_path and os.path.exists(threads_path):
        td = json.load(open(threads_path, encoding="utf-8"))
        threads_roots = {t["id"]: t.get("root", t["id"]) for t in td["threads"]}

    roots_out = {}
    mixed, empty, malformed = [], [], []
    for tid, ids in sorted(proposals.items()):
        slug = threads_roots.get(tid, tid)
        if not ids:
            empty.append(tid)
            continue
        if len(ids) > 1:
            mixed.append((tid, slug, ids))
        for id_str in ids:
            try:
                greek.bare_id(id_str)
            except ValueError:
                malformed.append((tid, slug, id_str))
        roots_out[slug] = {
            "ids": sorted(ids.keys()),
            "note": "TODO",
        }

    # id-clash check across proposed roots (roots.py's own ownership rule)
    owner = {}
    clashes = []
    for slug, entry in roots_out.items():
        for id_str in entry["ids"]:
            try:
                bare = greek.bare_id(id_str)
            except ValueError:
                bare = id_str
            if bare in owner and owner[bare] != slug:
                clashes.append((id_str, owner[bare], slug))
            else:
                owner[bare] = slug

    print(json.dumps({"roots": roots_out}, indent=2, ensure_ascii=False))

    if mixed:
        print(f"\n--- MIXED: {len(mixed)} thread(s) whose stems matched more than "
              f"one lemma id (check for an uncaught homograph) ---", file=sys.stderr)
        for tid, slug, ids in mixed:
            print(f"  {tid} (root={slug}):", file=sys.stderr)
            for lemma_id, surfaces in sorted(ids.items()):
                print(f"      {lemma_id:16} {', '.join(sorted(surfaces))}", file=sys.stderr)
    if clashes:
        print(f"\n--- CLASH: {len(clashes)} id(s) proposed for more than one root ---",
              file=sys.stderr)
        for id_str, a, b in clashes:
            print(f"  {id_str!r}: {a!r} and {b!r}", file=sys.stderr)
    if empty:
        print(f"\n--- EMPTY: stems matched nothing for: {', '.join(empty)} ---",
              file=sys.stderr)
    if malformed:
        print(f"\n--- MALFORMED: {len(malformed)} id(s) don't fit the Greek lemma-id "
              f"shape (roots.validate() would reject these) ---", file=sys.stderr)
        for tid, slug, id_str in malformed:
            print(f"  {tid} (root={slug}): {id_str!r}", file=sys.stderr)
    print(f"\n{len(roots_out)} thread(s) proposed, {len(mixed)} mixed, "
          f"{len(clashes)} clash(es), {len(empty)} empty, "
          f"{len(malformed)} malformed.", file=sys.stderr)


if __name__ == "__main__":
    main()
