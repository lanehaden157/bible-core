"""Loader/validator for data/roots.json -- Lane's hand-curated registry of
tracked-thread root identity: which lemma ids belong to one root
(ARCHITECTURE.md §2 "Root identity"). Two rules are enforced: an id claimed
by two roots is a hard failure, and the registry holds tracked threads only
-- local roots stay in a unit's own meta roots[], with no id set.

Schema (data/roots.json):
    {"_note": "...", "version": 1,
     "roots": {"<slug>": {"ids": ["2763a", "2764a"], "note": "..."}},
     "declined": {"<slug>": {"why": "...", "date": "...", "unit"?: N, "ids"?: [...]}}}

Nothing in the pipeline writes this file -- it's policy, same as
threads.json. This module only reads and validates it.

    python -m biblecore roots        # validate the current book's roots.json
"""
import csv
import json
import os
import re

from biblecore.book import book

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")
_ID_RE = re.compile(r"^(\d+)\s?([a-z]|\+)?$")


# ---- the id scheme belongs to the language (review G7) --------------------
# Hebrew ids are Strong's numbers with OSHB's letter (the functions below).
# Another language's adapter may define bare_id / lemma_key /
# is_id_segment / is_precise to use its own scheme (Greek: transliterated
# lemmas, lang/greek.py); anything it leaves out falls back to these.

def _override(name):
    try:
        lang = book().language
    except Exception:
        return None
    if lang == "hebrew":
        return None
    from biblecore.lang import adapter
    return getattr(adapter(lang), name, None)


def is_id_segment(seg: str) -> bool:
    """Is this '/'-separated lemma segment an id (not a bound prefix like
    'c', 'b', 'l')?"""
    f = _override("is_id_segment")
    return f(seg) if f else bool(seg) and seg[0].isdigit()


def is_precise(key: str) -> bool:
    """Does this lemma key name exactly one lexeme (Hebrew: a trailing
    letter, '2416e'), rather than every variant under a bare id?"""
    f = _override("is_precise")
    return f(key) if f else key[-1:].isalpha()


def bare_id(id_str: str) -> str:
    """'2763a' -> '2763'; '310 a' -> '310'; '2764' -> '2764'; '1007+' ->
    '1007'. The trailing letter is an opaque OSHB disambiguator
    (joshua_study_style_reference.md §2), not part of the id used for
    matching -- accepted both compact (roots.json's own spelling, e.g.
    '2763a') and space-separated (Joshua-words.tsv's spelling, e.g.
    '310 a'). A trailing '+' is OSHB's own marker for a lemma that
    continues into an adjacent word as part of a multi-word proper name
    (e.g. "בֵּית" "1007+" + the next word, together "Bethel") -- also just
    stripped, same as the letter. Raises ValueError if id_str doesn't
    match digits plus one of these optional trailing markers."""
    f = _override("bare_id")
    if f:
        return f(id_str)
    m = _ID_RE.match(id_str)
    if not m:
        raise ValueError(
            f"malformed id {id_str!r}: expected digits with an optional "
            f"trailing lowercase letter or '+', e.g. '2763', '2763a', '1007+'"
        )
    return m.group(1)


def lemma_key(id_str: str) -> str:
    """Normalize an id while KEEPING its disambiguating letter.

    '310 a' -> '310a'; '2763a' -> '2763a'; '1007+' -> '1007'; '5414' ->
    '5414'. The two markers are not the same thing, which is why they are
    treated differently here (review A7):

    * The trailing **letter** separates genuinely distinct lexemes that
      share a Strong's number. In Joshua: 3885a *lodge* vs 3885b *murmur*;
      2416a *alive* vs 2416e *life*; 6924a *front* vs 6924b *eastward*.
      Stripping it makes those impossible to tell apart, so a root that
      wants one and not the other cannot say so.
    * The trailing **'+'** is OSHB's marker for a lemma continuing into an
      adjacent word as part of a multi-word proper name (Beth-el is '1007+'
      plus the next word). Same lexeme either way, so it is always stripped.

    Some letters really are inflectional rather than lexical -- 834a/b/c/d
    are all *ʾăšer* with different prefixes, 859a-e all *ʾattâ* by person
    and number. Writing the bare id still covers those, because a bare id
    in a root's id set matches every letter variant. Precision is opt-in.
    """
    f = _override("lemma_key_of_id")
    if f:
        return f(id_str)
    m = _ID_RE.match(id_str)
    if not m:
        raise ValueError(
            f"malformed id {id_str!r}: expected digits with an optional "
            f"trailing lowercase letter or '+', e.g. '2763', '2763a', '1007+'"
        )
    letter = (m.group(2) or "").strip()
    return m.group(1) + (letter if letter.isalpha() else "")


def split_ids(ids):
    """A root's id list -> (bare_ids, exact_ids).

    A bare id ('2416') matches every letter variant of that number; a
    suffixed id ('2416e') matches only that lexeme. So a root can be as
    coarse or as precise as the word actually needs.
    """
    bare, exact = set(), set()
    for i in ids:
        key = lemma_key(i)
        if is_precise(key):
            exact.add(key)
        else:
            bare.add(key)
    return bare, exact


def load_roots(path: str = None) -> dict:
    """path defaults to the current book's data/roots.json, resolved at
    call time."""
    if path is None:
        path = book().data("roots.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def known_lemma_ids(words_tsv: str = None) -> set:
    """Every lemma id that actually occurs in the book's word table, in both
    forms -- bare ('2416') and letter-preserving ('2416e') -- so a root
    declaring either spelling can be checked against reality. A lemma
    field may hold several "/"-separated
    segments (one per surface morpheme); bound-prefix segments (c, b, d,
    k, l, m, ...) aren't ids and are skipped."""
    words_tsv = words_tsv or book().path("words")
    known = set()
    with open(words_tsv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            for seg in row["lemma"].split("/"):
                seg = seg.strip()
                if not is_id_segment(seg):
                    continue
                known.add(bare_id(seg))
                known.add(lemma_key(seg))
    return known


def validate(data: dict, words_tsv: str = None, threads_data: dict = None) -> list:
    """Validate a parsed roots.json document. Returns a list of error
    strings (empty if clean).

    threads_data, if given, is a parsed threads.json document -- every
    thread's `root` must resolve to a slug declared here."""
    words_tsv = words_tsv or book().path("words")
    errors = []
    roots = data.get("roots")
    if not isinstance(roots, dict):
        return ["roots.json's top-level 'roots' must be an object (slug -> entry)"]

    known_ids = known_lemma_ids(words_tsv)
    bare_owner = {}   # '2416'  -> slug claiming every lexeme under it
    exact_owner = {}  # '2416e' -> slug claiming just that lexeme

    for slug, entry in roots.items():
        if not _SLUG_RE.match(slug):
            errors.append(f"{slug!r}: slug must match [a-z0-9-]+")
        if "kind" in entry or "members" in entry:
            errors.append(f"{slug}: 'kind'/'members' are not allowed (reverted taxonomy, see §1)")
        if "translit" in entry or "gloss" in entry or "color" in entry or "colour" in entry:
            errors.append(f"{slug}: translit/gloss/colour don't belong in roots.json -- this file is id-sets only")

        ids = entry.get("ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"{slug}: 'ids' must be a non-empty list")
            continue
        if not entry.get("note"):
            errors.append(f"{slug}: missing required 'note'")

        for id_str in ids:
            try:
                bare = bare_id(id_str)
            except ValueError as exc:
                errors.append(f"{slug}: {exc}")
                continue
            if bare not in known_ids:
                errors.append(
                    f"{slug}: id {id_str!r} (bare {bare}) is not a lemma in "
                    f"{os.path.basename(words_tsv)}"
                )
            elif is_precise(lemma_key(id_str)) and lemma_key(id_str) not in known_ids:
                # The number exists but not this lexeme. Under A7 a
                # suffixed id matches only its own lexeme, so this would
                # match nothing at all -- a silent zero, which is worse
                # than a loud error.
                errors.append(
                    f"{slug}: id {id_str!r} -- {bare} occurs in "
                    f"{os.path.basename(words_tsv)} but not with that "
                    f"letter, so this id would match nothing. Use the bare "
                    f"id {bare!r} to match every variant."
                )
            key = lemma_key(id_str)
            precise = is_precise(key)

            # A bare id claims every lexeme under that number; a suffixed
            # id claims exactly one. So 3885a and 3885b may sit in
            # different roots (lodge vs murmur), but a bare 3885 collides
            # with either (review A7).
            clash = None
            if bare_owner.get(bare) not in (None, slug):
                clash = bare_owner[bare]
            elif precise and exact_owner.get(key) not in (None, slug):
                clash = exact_owner[key]
            elif not precise:
                other = next((o for k, o in exact_owner.items()
                              if bare_id(k) == bare and o != slug), None)
                clash = other

            if clash is not None:
                errors.append(
                    f"id {id_str!r} claimed by both {clash!r} and {slug!r} "
                    f"roots (§A5: an id in two roots is a hard failure)"
                )
            elif precise:
                exact_owner[key] = slug
            else:
                bare_owner[bare] = slug

    # `declined` is the ledger of candidates considered and deliberately
    # kept local (review A13). Without it the decision lives only in a
    # session log, so the same root gets re-proposed every few units and
    # re-argued from scratch.
    declined = data.get("declined")
    if declined is not None:
        if not isinstance(declined, dict):
            errors.append("roots.json's 'declined' must be an object "
                          "(slug -> {why, date, unit?, ids?})")
        else:
            for slug, entry in declined.items():
                if not _SLUG_RE.match(slug):
                    errors.append(f"declined {slug!r}: slug must match [a-z0-9-]+")
                if not isinstance(entry, dict):
                    errors.append(f"declined {slug}: entry must be an object")
                    continue
                if not entry.get("why"):
                    errors.append(f"declined {slug}: missing required 'why' -- "
                                  "a bare 'no' gets re-litigated")
                if not entry.get("date"):
                    errors.append(f"declined {slug}: missing required 'date'")
                if slug in roots:
                    errors.append(f"declined {slug}: also a tracked root -- a "
                                  "slug is one or the other, not both")

    if threads_data is not None:
        thread_roots = {
            t.get("root") for t in threads_data.get("threads", []) if isinstance(t, dict)
        }
        for root_slug in thread_roots:
            if root_slug not in roots:
                errors.append(
                    f"threads.json thread root {root_slug!r} has no matching "
                    f"data/roots.json entry"
                )

    return errors


def main(argv=None):
    data = load_roots()
    threads_data = None
    threads_path = book().data("threads.json")
    if os.path.exists(threads_path):
        with open(threads_path, encoding="utf-8") as f:
            threads_data = json.load(f)
    errs = validate(data, threads_data=threads_data)
    if errs:
        print(f"FAIL: {len(errs)} error(s)")
        for e in errs:
            print(" -", e)
        return 1
    print(f"PASS: {len(data.get('roots', {}))} root(s) valid")
    return 0
