"""biblecore/studio: installing the /unit flow into a book, and its tools
(split_sources, kit, unit_status) on a scratch book."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

import support
from biblecore import studio
from biblecore.book import validate_config

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import core_sync  # noqa: E402

BOOK = {"book": "Leviticus", "osis": "Lev", "slug": "leviticus", "language": "hebrew",
        "corpus": {"kind": "oshb"}, "studio": {"whole": ["milgrom"], "lxx_numbering": "hebrew"}}
VERSIFICATION = "| English | Hebrew |\n|---|---|\n| 6:1 | 5:20 |\n| 6:2 | 5:21 |\n| 6:8 | 6:1 |\n"
MARKED = """#source: milgrom-1
#label: Milgrom vol 1. Private copy.
#numbering: hebrew
@@ intro | Introduction
General matters.
@@ 1:1-17 | The burnt offering
Burnt offering text [p. 133].
@@ 5:20-21 | Reparation
Reparation text.
"""


def _scratch():
    d = tempfile.mkdtemp(prefix="bc-studio-")
    with open(os.path.join(d, "book.json"), "w", encoding="utf-8") as fh:
        json.dump(BOOK, fh)
    with open(os.path.join(d, "leviticus-versification.md"), "w", encoding="utf-8") as fh:
        fh.write(VERSIFICATION)
    os.makedirs(os.path.join(d, "data", "words"))
    os.makedirs(os.path.join(d, "data", "web"))
    with open(os.path.join(d, "data", "units.json"), "w", encoding="utf-8") as fh:
        json.dump({"units": [{"n": 1, "passage": "Leviticus 1:1–17", "tier": "full"},
                             {"n": 2, "passage": "Leviticus 2:1–16", "tier": "condensed"}]}, fh)
    with open(os.path.join(d, "data", "lemmas.json"), "w", encoding="utf-8") as fh:
        json.dump({"lemmas": {"7121": {"t": "qaraʾ", "g": "call; proclaim"}}}, fh)
    with open(os.path.join(d, "data", "words", "1.json"), "w", encoding="utf-8") as fh:
        json.dump({"c": 1, "verses": {"1": [{"w": "x", "t": "wa-yyiqraʾ", "l": "7121", "m": "verb"}]}}, fh)
    with open(os.path.join(d, "data", "web", "1.json"), "w", encoding="utf-8") as fh:
        json.dump({"c": 1, "verses": {"1": "Yahweh called to Moses"}}, fh)
    os.makedirs(os.path.join(d, "sources", "marked"))
    os.makedirs(os.path.join(d, "sources", "text"))
    with open(os.path.join(d, "sources", "marked", "milgrom-1.txt"), "w", encoding="utf-8") as fh:
        fh.write(MARKED)
    with open(os.path.join(d, "sources", "text", "brenton-lxx.txt"), "w", encoding="utf-8") as fh:
        fh.write("LEV 1:1 And the Lord called Moses again\nLEV 5:20 And the Lord spoke\n")
    return d


def _run(d, *args):
    r = subprocess.run([sys.executable, *args], cwd=d, capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, r.stdout + r.stderr


def test_validate():
    fails = []
    if validate_config(BOOK):
        fails.append(f"valid studio book rejected: {validate_config(BOOK)}")
    bad = dict(BOOK, studio={"wole": []})
    if not any("studio" in e for e in validate_config(bad)):
        fails.append("unknown studio key accepted")
    return fails


def test_install_renders_and_guards_edits():
    d = _scratch()
    try:
        fails = []
        with contextlib.redirect_stdout(io.StringIO()):
            rc = studio.install(d)
        unit = os.path.join(d, ".claude", "skills", "unit", "SKILL.md")
        if rc or not os.path.exists(unit):
            return ["install wrote no .claude/skills/unit/SKILL.md"]
        text = open(unit, encoding="utf-8").read()
        if "{{" in text or "leviticus-literary-unit-map.md" not in text:
            fails.append("placeholders not filled in the unit skill")
        for rel in ("tools/kit.py", "tools/split_sources.py", "tools/unit_status.py", "tools/lessons.py", "tools/lint_study.py", ".claude/skills/build/SKILL.md",
                    ".claude/agents/builder.md", ".claude/agents/fact-checker.md"):
            if not os.path.exists(os.path.join(d, rel)):
                fails.append(f"{rel} not installed")
        if "model: sonnet" not in open(os.path.join(d, ".claude", "agents", "builder.md"),
                                       encoding="utf-8").read():
            fails.append("builder agent lost its model line")
        if studio.plan(d)[0]:
            fails.append(f"second plan not empty: {studio.plan(d)[0]}")
        with open(unit, "a", encoding="utf-8") as fh:
            fh.write("\nlocal edit\n")
        with contextlib.redirect_stdout(io.StringIO()):
            if studio.install(d) != 1:
                fails.append("an edited studio file was overwritten without --force")
            if studio.install(d, force=True) != 0 or "local edit" in open(unit, encoding="utf-8").read():
                fails.append("--force did not restore the file")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_studio_book_takes_no_chat_cards():
    d = _scratch()
    try:
        names = set(core_sync.canon_files(d).values())
        fails = [f"{n} vendored into a studio book" for n in names if n.startswith("card-")]
        if "card-research.md" not in core_sync.retired_files(d):
            fails.append("card-research.md not retired from a studio book")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_tools_on_a_scratch_book():
    d = _scratch()
    try:
        fails = []
        with contextlib.redirect_stdout(io.StringIO()):
            studio.install(d)
        rc, out = _run(d, "tools/split_sources.py")
        recs = [json.loads(l) for l in open(os.path.join(d, "sources", "sections", "milgrom-1.jsonl"),
                                            encoding="utf-8")]
        if rc or len(recs) != 3:
            return [f"split_sources: rc {rc}, {len(recs)} records: {out}"]
        if (recs[2]["s"], recs[2]["e"]) != (6001, 6002):
            fails.append(f"Hebrew 5:20-21 not mapped to English 6:1-2: {recs[2]}")
        if (recs[0]["s"], recs[0]["e"]) != (0, 0):
            fails.append("intro section not 0-0")
        with open(os.path.join(d, "sources", "marked", "milgrom-3.txt"), "w", encoding="utf-8") as fh:
            fh.write("#source: milgrom-3\n#label: v3\n@@ 23:1-4 | A\ntext\n@@ 25:1-2 | B\ntext\n")
        rc, out = _run(d, "tools/split_sources.py", "--check", "milgrom-3")
        if "ch. [24]" not in out or "ch. [1" in out:
            fails.append(f"split_sources gaps should lie between a source's first and last chapter: {out}")
        rc, out = _run(d, "tools/kit.py", "range", "1:3", "--source", "milgrom")
        if "Burnt offering text" not in out or "General matters" in out:
            fails.append(f"kit range by volume prefix wrong: {out}")
        rc, out = _run(d, "tools/kit.py", "parts", "1")
        if rc or not os.path.exists(os.path.join(d, "work", "01", "parts", "milgrom-1-1.md")):
            fails.append(f"kit parts wrote nothing: {out}")
        rc, out = _run(d, "tools/kit.py", "words", "1:1")
        if "wa-yyiqraʾ [7121 call; verb]" not in out or "called Moses again" not in out:
            fails.append(f"kit words: {out}")
        rc, out = _run(d, "tools/kit.py", "bible", "LEV", "6:1", "--lxx")
        if "[LXX 5:20]" not in out:
            fails.append(f"kit bible --lxx did not follow the Hebrew numbering: {out}")
        subprocess.run(["git", "init", "-q"], cwd=d)
        rc, out = _run(d, "tools/unit_status.py")
        if rc or "not started" not in out or "(condensed)" not in out:
            fails.append(f"unit_status: {out}")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_lessons_loop():
    d = _scratch()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            studio.install(d)
        fails = []
        add = ["tools/lessons.py", "add", "quote-unread", "--stage", "factcheck", "--owner", "book",
               "--what", "quote not read", "--fix", "paraphrase"]
        rc, out = _run(d, *add, "--unit", "1")
        if "seen once" not in out:
            fails.append(f"first lesson not 'seen once': {out}")
        rc, out = _run(d, *add, "--unit", "2")
        if "RECURRING" not in out:
            fails.append(f"same key in a second unit not RECURRING: {out}")
        rc, out = _run(d, "tools/lessons.py", "report")
        if "owner: book" not in out or "quote-unread" not in out:
            fails.append(f"report misses the recurring key: {out}")
        _run(d, "tools/lessons.py", "resolve", "quote-unread", "--note", "lens.md rule")
        rc, out = _run(d, "tools/lessons.py", "report")
        if "0 to act on" not in out:
            fails.append(f"resolved key still flagged: {out}")
        rc, out = _run(d, *add, "--unit", "3")
        if "REGRESSION" not in out:
            fails.append(f"a repeat after resolve not REGRESSION: {out}")
        rc, out = _run(d, "tools/lessons.py", "known")
        if "quote-unread [REGRESSION]" not in out:
            fails.append(f"known does not show the regression: {out}")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_unit_pack_ties_short_rulings_and_reads_table_maps():
    from biblecore import unit_pack as up
    fails = []
    segs = {up._skeleton(x, gutturals=True) for f in ("tamim", "zakar") for x in [f]}
    if not up.tie_rulings([("t.md", [("Glossary", "tamim", ["tamim"], "| tamim |")])],
                          {up._skeleton("tamim")}, (), {"tamim", "zakar"})[0]:
        fails.append("a short ruling (tamim) with no guttural never ties")
    d = _scratch()
    try:
        with open(os.path.join(d, "leviticus-literary-unit-map.md"), "w", encoding="utf-8") as fh:
            rows = ["| # | Passage | Working title | Tier | Peak |", "|---|---|---|---|---|",
                    "| 01 | 1:1-17 | The model | full | |", "| 02 | 2:1-16 | Grain | condensed | |", "",
                    "- 01: full. The pattern.", "- 02: condensed."]
            fh.write(chr(10).join(rows) + chr(10))

        class B:
            root = d
            slug = "leviticus"
        got = up.map_entry(B, 1)
        if "The model" not in got or "The pattern" not in got or "Grain" in got:
            fails.append(f"table-style map entry wrong: {got!r}")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return fails


def test_tiered_reading_and_lint():
    d = _scratch()
    try:
        cfg = json.load(open(os.path.join(d, "book.json"), encoding="utf-8"))
        cfg["studio"] = {"whole": ["milgrom"], "voices": ["rashi"], "lxx_numbering": "hebrew"}
        json.dump(cfg, open(os.path.join(d, "book.json"), "w", encoding="utf-8"))
        with contextlib.redirect_stdout(io.StringIO()):
            studio.install(d)
        mk = os.path.join(d, "sources", "marked")
        with open(os.path.join(mk, "rashi.txt"), "w", encoding="utf-8") as fh:
            fh.write(chr(10).join(["#source: rashi", "#label: R", "@@ 1:1 | one", "Called first.",
                                   "@@ 1:9 | nine", "Aroma text.", ""]))
        with open(os.path.join(mk, "henry.txt"), "w", encoding="utf-8") as fh:
            fh.write(chr(10).join(["#source: henry", "#label: H", "@@ 1:1-17 | ch", "A line.",
                                   "The aroma of rest.", ""]))
        _run(d, "tools/split_sources.py")
        fails = []
        rc, out = _run(d, "tools/kit.py", "extra", "1", "--key", "1:9")
        txt = open(os.path.join(d, "work", "01", "extra", "rashi.md"), encoding="utf-8").read()
        if "Aroma text" not in txt or "Called first" in txt:
            fails.append(f"extra --key did not narrow to the key verse: {txt!r}")
        rc, out = _run(d, "tools/kit.py", "grep", "1", "aroma")
        g = open(os.path.join(d, "work", "01", "grep.md"), encoding="utf-8").read()
        if "aroma of rest" not in g.lower() or "Aroma text" in g:
            fails.append(f"grep covered the wrong sources: {g!r}")
        rc, out = _run(d, "tools/kit.py", "sources")
        if "milgrom-1 (whole)" not in out or "rashi (voice)" not in out:
            fails.append(f"sources lacks the tiers: {out}")
        os.makedirs(os.path.join(d, "work", "01"), exist_ok=True)
        with open(os.path.join(d, "work", "01", "briefing.md"), "w", encoding="utf-8") as fh:
            fh.write("- a bullet" + chr(10))
        rc, out = _run(d, "tools/lint_study.py", "1")
        if rc != 1 or "a bullet" not in out or "words" not in out:
            fails.append(f"lint missed a bullet or the length: {out}")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


TESTS = [test_validate, test_install_renders_and_guards_edits, test_studio_book_takes_no_chat_cards,
         test_tools_on_a_scratch_book, test_lessons_loop, test_tiered_reading_and_lint,
         test_unit_pack_ties_short_rulings_and_reads_table_maps]
