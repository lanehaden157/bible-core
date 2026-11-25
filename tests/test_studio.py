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
        for rel in ("tools/kit.py", "tools/split_sources.py", "tools/unit_status.py",
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


TESTS = [test_validate, test_install_renders_and_guards_edits, test_studio_book_takes_no_chat_cards,
         test_tools_on_a_scratch_book]
