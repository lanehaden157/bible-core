"""Drop one research artifact into the site.

    python -m biblecore port 5              # port source-artifacts/<slug>_05_translation.html
    python -m biblecore port 5 --dry        # show what would change, write nothing
    python -m biblecore port 6 --src X.html # build the thread-delta report from X, write nothing
    python -m biblecore port 1 --force      # re-port an already-built unit
    python -m biblecore port 5 --answers a.json  # {question topic: answer}: those questions print as
                                            # answered, and go in the delta as such

For a new unit N:
  1. read source-artifacts/<slug>_NN_*.html
  2. validate its unit-meta block (a hard gate) and print any questions[] and, in a separate
     section, any checks[] for code
  3. prefix endnote ids (u0N-n1, ...) so they stay unique site-wide
  4. fill data-w by per-verse alignment (data_w.py), reporting what it can't
  5. merge the unit into data/units.json (local roots get a colour here)
  6. merge threads.retro (fixes for EARLIER units) into the retro spec,
     dry-checking each against its target first
  7. write units/unit-NN.html, then retrofit + scan + verify occurrences
  8. write the thread-delta report (out/thread-delta-NN.md): opens/payoffs
     to fold into threads.json, candidates with an id-set preview, ready
     promotions (threads.promote[]), checks, open questions, fragment findings, and tracked-thread coverage

Nothing is committed and threads.json is never written: review the fragment
in the browser, apply the delta by hand if accepted, then commit.

Re-porting a built unit needs --force. (learned: a re-port from a stale
source artifact silently regressed Joshua unit 1 -- four local roots, the
voice rule and a markup fix, all lost.)
"""

import argparse
import glob
import json
import os
import re
import sys

from biblecore import audit as atc
from biblecore import data_w as adw
from biblecore import meta as um
from biblecore.book import book
from biblecore.colour import assign_hues, assign_tracked_colors  # noqa: F401


# --------------------------------------------------------------- fragment build

def prefix_endnotes(body, n):
    """id="n1" -> id="u06-n1", href="#n1" -> href="#u06-n1" -- keeps
    endnote ids unique once every unit's fragment lives on one page."""
    p = f"u{n:02d}-"
    body = re.sub(r'id="(n\d+)"', lambda m: f'id="{p}{m.group(1)}"', body)
    body = re.sub(r'href="#(n\d+)"', lambda m: f'href="#{p}{m.group(1)}"', body)
    return body


def to_fragment(raw, n):
    """Normalize an incoming artifact into the bare <article> fragment.
    Idempotent: re-running on an already-ported fragment changes only the
    endnote-id prefix (already prefixed -> no-op) and the re-injected meta
    block (regenerated fresh either way)."""
    html = raw.strip()
    if not re.search(r'<article class="unit"[^>]*>', html):
        sys.exit('artifact has no <article class="unit"> -- see the style '
                 "reference's hard contract")
    body = um.strip(html)  # remove any existing meta block
    m = re.search(r'<article class="unit"[^>]*>\n?', body)
    inner = body[m.end():]
    inner = re.sub(r'\s*</article>\s*$', "", inner)
    inner = prefix_endnotes(inner, n)
    return f'<article class="unit" data-unit="{n}">\n{inner.strip()}\n</article>\n'


# --------------------------------------------------------------- units.json merge

def roots_in_fragment(html):
    """Every distinct data-root slug actually tagged in the fragment.

    The authority on which roots a unit uses is the markup, not meta.roots
    -- since roots[] is local-only (style reference §1), a tracked thread
    never appears there, so seeding collision-avoidance from meta.roots
    alone is blind to every tracked colour in the unit."""
    return set(re.findall(r'data-root="([a-z0-9-]+)"', html or ""))


def merge_units_json(meta, dry, fragment_html=None):
    """Merge the unit's row into data/units.json. Local (non-tracked) roots
    get {color, translit, gloss} -- a local hue is assigned here (Phase 4),
    avoiding collisions with this unit's own existing local hues AND the
    global colour of every tracked thread the unit actually tags (read from
    the fragment's data-root spans, not from meta.roots)."""
    uj = um._load("units.json")
    n = meta["unit"]
    row = um._unit_row(uj, n)
    if row is None:
        row = {"n": n, "slug": meta.get("slug", f"unit-{n:02d}"),
               "passage": meta["passage"], "title": meta["title"], "built": False}
        for g in book().groupings:
            if meta.get(g) is not None:
                row[g] = meta[g]
        uj["units"].append(row)
        uj["units"].sort(key=lambda u: u["n"])

    threads = {t["root"]: t for t in um._load("threads.json")["threads"]}
    existing = row.get("roots") or {}
    local = [r["root"] for r in meta["roots"] if r["root"] not in threads]
    taken = [e["color"] for e in existing.values()
             if isinstance(e, dict) and e.get("color")]
    tagged = roots_in_fragment(fragment_html) | {r["root"] for r in meta["roots"]}
    taken += [threads[r]["color"] for r in sorted(tagged)
              if r in threads and threads[r].get("color")]
    hues = assign_hues([r for r in local if r not in existing], taken)

    local_roots = {}
    for r in meta["roots"]:
        name = r["root"]
        if name in threads:
            continue  # this root's registry entry is threads.json's job
        prev = existing.get(name) if isinstance(existing.get(name), dict) else {}
        local_roots[name] = {
            "color": prev.get("color") or hues.get(name) or book().palette()[0],
            "translit": r["translit"],
            "gloss": r["gloss"],
        }
        # optional fields ride along, or generate() -- which rebuilds roots[]
        # from this row -- silently drops them on the next regen
        for k in ("example", "echo"):
            if r.get(k):
                local_roots[name][k] = r[k]

    # A port writes the unit under this core's contract (D7), whatever
    # version the artifact or an earlier port claimed.
    from biblecore import contract
    row.update({"slug": meta.get("slug", row["slug"]), "passage": meta["passage"],
                "title": meta["title"], "built": True, "roots": local_roots,
                "contract": contract.current()})
    for g in book().groupings + book().meta_keys:
        if meta.get(g) is not None:
            row[g] = meta[g]

    if not dry:
        with open(book().data("units.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(uj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return local_roots


# --------------------------------------------------------------- thread delta

def thread_delta(meta, fragment_html=None, retrofit_applied=True, answers=None):
    threads = {t["id"]: t for t in um._load("threads.json")["threads"]}
    n = meta["unit"]
    slug = meta.get("slug", f"unit-{n:02d}")
    lines = [f"# Thread delta — Unit {n}", "",
             "Apply to `data/threads.json` if accepted: `python -m biblecore apply-delta "
             f"{n}` takes the ready lines below. The porter does not touch threads.json.", ""]

    th = meta.get("threads", {})
    touched = []
    for kind in ("opens", "payoffs"):
        for e in th.get(kind, []) or []:
            t = threads.get(e["id"])
            if not t:
                continue
            touched.append(e["id"])
            flags = []
            if not t.get("tagged"):
                flags.append("set `tagged: true`")
            if kind == "payoffs" and t.get("status") == "open":
                flags.append("consider `status: \"closed\"` if this is the final payoff")
            note = f" — {'; '.join(flags)}" if flags else " — already consistent"
            lines.append(f"- **{kind[:-1]}** `{e['id']}` at {e.get('ref', '?')}{note}")
            if kind == "payoffs" and not any(
                    p.get("unit") == n for p in t.get("payoffs", [])):
                entry = {"unit": n, "ref": e.get("ref", "")}
                if e.get("note"):
                    entry["note"] = e["note"]
                lines.append(f"    - add to `{e['id']}`.payoffs: "
                             f"`{json.dumps(entry, ensure_ascii=False)}`")
            elif kind == "opens" and not (t.get("opens") or {}).get("note"):
                entry = {"unit": n, "ref": e.get("ref", "")}
                if e.get("note"):
                    entry["note"] = e["note"]
                lines.append(f"    - set `{e['id']}`.opens: "
                             f"`{json.dumps(entry, ensure_ascii=False)}`")

    cands = th.get("candidates", []) or []
    if cands:
        lines += ["", "## New-thread candidates "
                  "(Claude decides, biased book-wide)", "",
                  f"After promoting any of these into threads.json/roots.json, "
                  f"`python -m biblecore data-w {n}` fills their spans in "
                  f"place; no `--force` re-port needed.", ""]
        declined = (um._load("roots.json").get("declined") or {})
        for c in cands:
            root = c.get("root", "?")
            lines.append(f"- `{root}` — {c.get('why', '').strip()}")
            if root in declined:
                d = declined[root]
                lines.append(f"    - **previously declined** "
                             f"{d.get('date', '?')}: {d.get('why', '').strip()}")
                lines.append("    - re-proposing is fine, but say what "
                             "changed -- a new payoff, not the same argument "
                             "(review A13).")
            _append_candidate_preview(lines, root, c)

    promote = th.get("promote", []) or []
    if promote:
        lines += ["", "## Thread promotions (ready to apply)", "",
                  "Each is a ready `data/threads.json` entry and `data/roots.json` "
                  "id set. Add them if accepted, take the colour from `python -m "
                  "biblecore colour`, then run `data-w N` for each retrofit unit "
                  "and `build` (it audits).", ""]
        for p_ in promote:
            lines += _promotion_lines(p_)

    checks = meta.get("checks", []) or []
    if checks:
        lines += ["", "## Checks for code", ""] + _check_lines(checks)

    questions = meta.get("questions", []) or []
    if questions:
        answers = answers or {}
        open_qs = [q for q in questions if q.get("topic") not in answers]
        if open_qs:
            lines += ["", "## Open questions for Lane", ""]
            for q in open_qs:
                lines.append(f"- **{q.get('topic', '?')}** — {q.get('note', '').strip()}")
                for opt in q.get("options", []) or []:
                    lines.append(f"    - {opt}")
        done = [q for q in questions if q.get("topic") in answers]
        if done:
            lines += ["", "## Questions answered (--answers)", ""]
            for q in done:
                lines.append(f"- **{q['topic']}** — {answers[q['topic']]}")

    retro = th.get("retro", []) or []
    if retro:
        lines += ["", "## Retro fixes for earlier units", "",
                  "Dry-checked against its target fragment, then merged into "
                  "the retro spec (a real port only — not "
                  "`--dry`/`--src`):", ""]
        for e in retro:
            op = e.get("op", "add")
            lines.append(f"- `{e.get('unit','?')}` {op} `{e.get('root', e.get('to','?'))}` "
                         f"— {e.get('why','').strip()}")
            body = {k: v for k, v in e.items() if k not in ("op", "why")}
            lines.append(f"    `{json.dumps(body, ensure_ascii=False)}`")

    if fragment_html is not None:
        _append_fragment_findings(lines, fragment_html, meta)
        _append_coverage(lines, slug, fragment_html, meta.get("passage", ""),
                         retrofit_applied)

    if not (touched or cands or retro or questions or promote or checks):
        lines.append("_no tracked threads opened or paid off in this unit, "
                     "no candidates, no promotions, no retro fixes, no checks, "
                     "no open questions._")

    out = book().path("out")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"thread-delta-{n:02d}.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def _promotion_lines(p):
    """One threads.promote[] item as a ready delta: the threads.json entry,
    the roots.json id set, the reach and the id-set preview."""
    e = p.get("entry", {})
    entry = {"id": e.get("id"), "root": e.get("root")}
    for k in ("translit", "gloss"):
        if e.get(k):
            entry[k] = e[k]
    entry.update({"status": "open", "tagged": True, "opens": e.get("opens"),
                  "payoffs": e.get("payoffs", [])})
    if e.get("note"):
        entry["note"] = e["note"]
    rf = p.get("retrofit") or []
    out = [f"- `{e.get('id')}` — reach: {p.get('reach', '').strip()}",
           f"    - threads.json (no colour yet): "
           f"`{json.dumps(entry, ensure_ascii=False)}`",
           f"    - retrofit in units: "
           + (", ".join(str(u) for u in rf) if rf else "none")
           + (" (`python -m biblecore data-w N`; leftovers to "
              "`retrofit/retrofit-tags.json`)" if rf else "")]
    _append_candidate_preview(out, e.get("root", "?"), {"ids": e.get("ids")})
    return out


def _check_lines(checks):
    out = []
    for c in checks:
        exp = c.get("expect")
        exp = ", ".join(exp) if isinstance(exp, list) else exp
        out.append(f"- `{c.get('ref', '?')}` — {c.get('claim', '').strip()} "
                   f"(expect: {exp})")
    return out


def _append_candidate_preview(lines, root, cand):
    """Preview what a candidate's proposed `ids` would pull in book-wide --
    the review step before Lane commits an id set to data/roots.json (the
    id-based analogue of Matthew's stem preview, Joshua's
    archive/phase-0.6-plan.md §1)."""
    ids, seq = cand.get("ids"), cand.get("seq")
    if not ids and not seq:
        lines.append(f"    - no ids proposed yet (or `seq`, for a fixed phrase); once "
                     f"some are, run `python -m biblecore audit --ids {root}` "
                     f"against a draft data/roots.json entry to preview coverage")
        return
    # a phrase thread (roots.json `seq`, ordered lemma ids) previews the same way
    entry = {"seq": seq} if seq else {"ids": ids}
    try:

        words = atc.load_words()
        hits = atc.source_hits_for_entry(words, entry)
        wbi = atc.words_by_id(words)
    except Exception as exc:  # pragma: no cover
        lines.append(f"    - (id preview unavailable: {exc})")
        return

    by_form = {}
    for wid, cv in hits.items():
        surface = wbi[wid]["surface"]
        e = by_form.setdefault(surface, {"n": 0, "wid": wid})
        e["n"] += 1
    key, val = ("seq", seq) if seq else ("ids", ids)
    lines.append(f"    - if promoted, data/roots.json entry: "
                 f"`\"{root}\": {{\"{key}\": {json.dumps(val, ensure_ascii=False)}, \"note\": \"...\"}}`")
    total = sum(e["n"] for e in by_form.values())
    lines.append(f"    - those ids match **{total}** word(s) book-wide "
                 f"({len(by_form)} distinct surface form(s)):")
    for surface, e in sorted(by_form.items(), key=lambda kv: -kv[1]["n"])[:12]:
        lines.append(f"        {surface} ({atc._translit_row(wbi[e['wid']])}) "
                     f"×{e['n']}")
    extra = len(by_form) - 12
    if extra > 0:
        lines.append(f"        …and {extra} more form" + ("s" if extra != 1 else ""))


def _append_fragment_findings(lines, html, meta):
    """unit_meta.validate_fragment()'s findings, reported -- NOT a hard gate
    (the port still writes the fragment for review; only validate() on the
    meta dict blocks the write, see port_one)."""
    try:
        threads_json = um._load("threads.json")
    except Exception:
        threads_json = {"threads": []}
    errs = um.validate_fragment(html, meta=meta, threads_json=threads_json)
    warnings = um.warnings_for_fragment(html)
    if errs or warnings:
        lines += ["", "## Fragment findings — fix before committing", ""]
        lines += [f"- **FAIL** {e}" for e in errs]
        lines += [f"- warning: {w}" for w in warnings]


def _append_coverage(lines, slug, html, passage, retrofit_applied=True):
    try:
        cov = atc.coverage_for_fragment(slug, html, passage)
    except Exception as exc:  # pragma: no cover
        lines.append(f"\n## Tracked-thread coverage\n\n(unavailable: {exc})")
        return
    lines += ["", "## Tracked-thread coverage in this unit", ""]
    if not retrofit_applied:
        lines.append("_(checked on the raw fragment — retrofit-tags.json not yet "
                     "applied; entries already there will show as gaps)_")
        lines.append("")
    if cov["warnings"]:
        lines.append("**alignment warnings — check these first:**")
        lines += [f"- {w}" for w in cov["warnings"]] + [""]
    if cov.get("covered"):
        lines.append(f"_{len(cov['covered'])} occurrence(s) fall in verses a "
                     f"component declares with `data-verses` (e.g. a table), "
                     f"so they aren't gaps._")
        lines.append("")
    if not cov["gaps"] and not cov["wrong"] and not cov["strays"] and not cov["missing_data_w"]:
        lines.append("Every tracked-thread occurrence in this passage is tagged. ✓")
        return
    if cov["gaps"]:
        lines.append(f"**{len(cov['gaps'])} occurrence(s) the "
                     f"{book().language_name} has but the "
                     f"fragment leaves untagged** — add to `retrofit-tags.json` "
                     f"`add` (check any `???` text):")
        lines.append("")
        renderings = {}
        for g in cov["gaps"]:
            txt = (g["text"][:90] + "…") if len(g["text"]) > 90 else g["text"]
            lines.append(atc.add_entry_line(
                atc.add_entry(g, slug, passage, html, renderings)))
            if txt:
                lines.append(f"        # “{txt}”")
    if cov["wrong"]:
        lines += ["", f"**{len(cov['wrong'])} tagged id whose lemma isn't in the "
                      f"root's set — mistyped id?**"]
        for w in cov["wrong"]:
            lines.append(f"- `{w['word_id']}` (‹{w['surface']}›) tagged "
                         f"{w['root']} at {w['ch']}:{w['v']}")
    if cov["strays"]:
        lines += ["", f"**{len(cov['strays'])} tagged id that's out of range or "
                      f"doesn't exist — wrong verse or typo?**"]
        for s in cov["strays"]:
            lines.append(f"- `{s['word_id']}` tagged {s['root']}: {s['reason']}")
    if cov["missing_data_w"]:
        lines += ["", f"**{cov['missing_data_w']} tracked-thread span(s) with no "
                      f"data-w attribute — hard error, must fix before committing**"]


# --------------------------------------------------------------- retro + retrofit

RETRO_FIELDS = {
    "add": ("unit", "verse", "text", "root", "why", "nth", "cls", "w"),
    "retag": ("unit", "verse", "from", "to", "text", "why", "nth", "w"),
    "retag_word": ("unit", "from", "to", "match", "why"),
    "untag_word": ("unit", "root", "match", "why"),
    "unwrap": ("unit", "text", "root", "why"),
    "strip_span": ("unit", "class", "why"),
    "text": ("unit", "from", "to", "why"),
}


def merge_retro(meta, dry):
    """Merge meta.threads.retro (fixes for earlier units) into the generated
    retro spec (paths.retro), which retrofit.py loads alongside the
    hand-authored retrofit-tags.json. Each entry is dry-checked against its
    target fragment first; ones that wouldn't apply cleanly are reported,
    not written."""
    from biblecore import retrofit as ar
    retro = (meta.get("threads", {}) or {}).get("retro", []) or []
    if not retro:
        return 0, []
    retro_spec = book().path("retro")
    rt = {}
    if os.path.exists(retro_spec):
        with open(retro_spec, encoding="utf-8") as fh:
            rt = json.load(fh)
    n = meta["unit"]
    stamp = f"from Unit {n} port ({_today()})"
    written, skips = 0, []
    for e in retro:
        op = e.get("op", "add")
        entry = {k: e[k] for k in RETRO_FIELDS.get(op, ()) if k in e}
        target_path = os.path.join(book().path("units"), e["unit"] + ".html")
        if not os.path.exists(target_path):
            skips.append(f"MISS {e['unit']}: fragment doesn't exist yet "
                         f"({e.get('why','').strip()})")
            continue
        with open(target_path, encoding="utf-8") as fh:
            html = fh.read()
        _, msg = ar.FNS[op](html, entry)
        if msg.startswith(("MISS", "SKIP")):
            skips.append(f"{msg}  ({e.get('why','').strip()})")
            continue
        if msg.startswith("ok"):
            continue  # already applied — nothing to record
        arr = rt.setdefault(op, [])
        if any(x == entry for x in arr):
            continue
        entry["_from"] = stamp
        arr.append(entry)
        written += 1
    if (written or skips) and not dry:
        os.makedirs(os.path.dirname(retro_spec), exist_ok=True)
        with open(retro_spec, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rt, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return written, skips


def _today():
    import datetime
    return datetime.date.today().isoformat()


def run_retrofit_and_scan():
    from biblecore import retrofit, scan, verify_occurrences
    for name, fn in (("retrofit", retrofit.main), ("scan", scan.main),
                     ("verify-occurrences", verify_occurrences.main)):
        print(f"\n=== {name} ===")
        if fn([]) and name != "retrofit":
            print(f"FAILED at {name}")
            return False
    return True


# --------------------------------------------------------------- commands

def load_answers(path):
    """{topic: answer} from a --answers JSON file. The answer is the chosen
    option or free text; anything but a string is read as its JSON text."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.exit(f"--answers {path}: {exc}")
    if not isinstance(data, dict):
        sys.exit(f"--answers {path}: expected an object {{topic: answer}}")
    return {str(k): v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            for k, v in data.items()}


def print_questions(meta, answers=None):
    """Wording/data calls the chat side flagged for Lane (meta.questions[]) --
    printed straight to stdout, at the top of the port, so whoever is
    running port_artifact.py sees them immediately and can ask Lane right
    here instead of the chat side asking on the project side (2026-09-21,
    Lane: 'i dont wanna be answering those on project side'). Also folded
    into the thread-delta report by thread_delta() for the written record,
    but this is the copy meant to actually get read.

    `answers` ({topic: answer}, from --answers) marks questions already
    decided: they print as resolved, only the rest as open, and a topic
    that matches no question is warned about (a misspelt key would
    otherwise leave its question open without a word)."""
    questions = meta.get("questions", []) or []
    answers = answers or {}
    topics = {q.get("topic") for q in questions}
    for t in sorted(set(answers) - topics):
        print(f"  warning: --answers has '{t}', but no question has that topic")
    if not questions:
        return
    open_qs = [q for q in questions if q.get("topic") not in answers]
    done = [q for q in questions if q.get("topic") in answers]
    if done:
        print("")
        print(f"=== {len(done)} question(s) answered from --answers ===")
        for q in done:
            print(f"  [{q['topic']}] -> {answers[q['topic']]}")
    if not open_qs:
        return
    print("")
    print(f"=== {len(open_qs)} open question(s) for Lane ===")
    for q in open_qs:
        print(f"  [{q.get('topic', '?')}] {q.get('note', '').strip()}")
        for opt in q.get("options", []) or []:
            print(f"      - {opt}")


def print_checks(meta):
    """Claims about other passages' text that the chat side wants the code
    side to verify (meta.checks[]). Their own section: not questions, Lane
    doesn't answer them."""
    checks = meta.get("checks", []) or []
    if not checks:
        return
    print("")
    print(f"=== {len(checks)} check(s) for code (not for Lane) ===")
    for line in _check_lines(checks):
        print(" ", line)


def port_one(n, dry, src=None, force=False, answers=None, write_invalid=False):
    b = book()
    os.makedirs(b.path("out"), exist_ok=True)
    if src:
        if not os.path.exists(src):
            sys.exit(f"--src not found: {src}")
        with open(src, encoding="utf-8") as fh:
            raw = fh.read()
    else:
        matches = sorted(glob.glob(b.source_glob(n)))
        if not matches:
            sys.exit(f"no source artifact: {os.path.relpath(b.source_glob(n), b.root)}")
        with open(matches[0], encoding="utf-8") as fh:
            raw = fh.read()

    meta = um.parse(raw)
    if meta is None:
        sys.exit('artifact has no <script id="unit-meta"> block -- see the '
                 "style reference's hard contract")
    meta.setdefault("unit", n)
    meta.setdefault("slug", f"unit-{n:02d}")
    for note in um.normalize_candidates(meta):
        print("  normalized", note)
    from biblecore import contract
    meta["contract"] = contract.current()   # stamped by the port (D7)
    errs = um.validate(meta, um._load("threads.json"))
    if errs:
        print("METADATA INVALID:")
        for e in errs:
            print("  -", e)
        sys.exit(1)

    print_questions(meta, answers)
    print_checks(meta)

    fragment = to_fragment(raw, n)

    # A6: the chat side is told to mark roots with data-root only and not to
    # hand-chase word ids, so the artifact arrives without data-w. Fill them
    # here by per-verse alignment; anything ambiguous is reported and left
    # for a human rather than guessed at.
    w_edits, w_report = adw.plan(fragment, meta["passage"])
    if w_edits:
        fragment = adw.apply_edits(fragment, w_edits)
    print("")
    print("=== data-w assignment ===")
    print(f"assigned {len(w_edits)} span(s) by per-verse alignment"
          + (f"; {len(w_report)} need(s) a human:" if w_report else ""))
    for line in w_report:
        print("  needs eyes:", line)

    no_write = dry or bool(src)
    with open(b.data("units.json"), encoding="utf-8", newline="") as fh:
        units_before = fh.read()
    local_roots = merge_units_json(meta, no_write, fragment)
    r = um._unit_row(um._load("units.json"), n)
    for g in b.groupings:
        if not meta.get(g) and r and r.get(g):
            meta[g] = r[g]
    fragment = um.inject(fragment, um.generate(n) if not no_write else meta)

    # Validate before anything lands on disk: a failed fragment check used to
    # leave a half-written --force port and still print "ported". units.json
    # was merged above, so put it back if the fragment is refused.
    if not no_write and not write_invalid:
        try:
            threads_json = um._load("threads.json")
        except Exception:
            threads_json = {"threads": []}
        ferrs = um.validate_fragment(fragment, meta=meta, threads_json=threads_json)
        if not os.path.exists(os.path.join(b.path("css"), "core.css")):
            # a book's first port runs before its first build has made core.css
            ferrs = [e for e in ferrs if "no stylesheet in css/" not in e
                     and "doesn't enable" not in e]
        if ferrs:
            with open(b.data("units.json"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(units_before)
            print("FRAGMENT INVALID -- nothing written:")
            for e in ferrs:
                print("  -", e)
            print("Fix the source artifact and port again, or --write-invalid to "
                  "write it anyway for review.")
            sys.exit(1)

    dest = b.unit_path(n)
    if no_write:
        why = "dry run" if dry else "--src: writing nothing"
        delta = thread_delta(meta, fragment, retrofit_applied=False, answers=answers)
        print(f"[{why}] would write {dest}")
        print(f"[{why}] local hues: { {k: v['color'] for k, v in local_roots.items()} }")
        nretro = len((meta.get("threads", {}) or {}).get("retro", []) or [])
        if nretro:
            print(f"[{why}] {nretro} retro fix(es) for earlier units — would be "
                  f"merged into the retro spec (see the thread delta)")
        print(f"[{why}] thread delta -> {delta}  "
              f"(coverage checked before retrofit-tags.json is applied)")
        return

    # A re-port replaces the whole built fragment with whatever the source
    # artifact says. The unit 2 port (7af1a59) re-ported unit 1 from a source
    # artifact that predated a day of hand fixes, and silently regressed it
    # (four local roots lost, named commentators back, C7 undone). A re-port
    # is legitimate -- it is how a reworked artifact ships -- but it should
    # never happen by accident.
    if os.path.exists(dest) and not force:
        sys.exit(f"{dest} already exists. Re-porting replaces it wholesale with "
                 f"the source artifact -- make sure the source is current "
                 f"(not older than the built fragment), then pass --force.\n"
                 f"Just promoted a thread? No re-port needed: "
                 f"python -m biblecore data-w {n}, then build.")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(fragment)
    print(f"wrote {dest}")
    print(f"local hues: { {k: v['color'] for k, v in local_roots.items()} }")
    if meta.get("intertext") or meta.get("typescenes"):
        from biblecore import canon
        n_it, n_ts = canon.merge_meta(meta, n)
        print(f"canon: {n_it} intertext edge(s), {n_ts} type-scene instance(s) "
              f"-> data/canon.json")
    written, skips = merge_retro(meta, dry=False)
    if written:
        print(f"merged {written} retro fix(es) for earlier units -> "
              f"{os.path.relpath(b.path('retro'), b.root)}")
    for s in skips:
        print(f"  retro NOT merged — {s}")
    run_retrofit_and_scan()
    # coverage against the fragment as it now stands on disk (retrofit applied)
    with open(dest, encoding="utf-8") as fh:
        final = fh.read()
    delta = thread_delta(meta, final, retrofit_applied=True, answers=answers)
    print(f"\n>>> REVIEW THE THREAD DELTA: {delta}")
    print("\nported. view in the browser, apply the thread delta if accepted, then commit.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="biblecore port")
    ap.add_argument("unit", nargs="?", type=int)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--src", metavar="PATH",
                    help="port from this file instead of source-artifacts/; "
                         "writes nothing, just builds the thread-delta report "
                         "(for dry-running the porter on a practice fragment)")
    ap.add_argument("--force", action="store_true",
                    help="allow replacing an already-built units/unit-NN.html")
    ap.add_argument("--write-invalid", action="store_true",
                    help="write the fragment even if its fragment checks fail "
                         "(default: refuse, leaving the built unit untouched)")
    ap.add_argument("--answers", metavar="FILE",
                    help="JSON {question topic: answer} for the artifact's "
                         "questions[]: those print as answered (and go in the "
                         "thread delta as such), only the rest as open. Lets "
                         "the dry run and the real port share one set of answers")
    a = ap.parse_args(argv)
    if not a.unit:
        ap.error("give a unit number")
    port_one(a.unit, a.dry, a.src, a.force, load_answers(a.answers) if a.answers else None, a.write_invalid)
    return 0

