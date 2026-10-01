"""A Greek book from day one (Greek-in-core pass 1, 2026-10-01).

  * the template's language blocks (new_book.keep_language): each language
    gets its own text and no markers; a Greek book gets no Hebrew-only text
  * new_book's Greek book.json, lexicon and file set
  * `biblecore fetch`: pinned files with sha1 checks, served here from a
    local file:// mirror so the suite needs no network; a corrupted or
    mismatched file fails loudly
  * the pins agree with Matthew's fetched corpus, read-only (the data the
    MorphGNT/LXX parity tests use)
  * a Greek book made from the template, on greek_book.py's small corpus:
    corpus, build, `biblecore test`, `biblecore book` and units-from-map's
    canon leads all pass through the real CLI
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

import greek_book
import support
from template_book import make_book

import new_book  # tools/ is on the path through template_book
from biblecore import book as bookmod
from biblecore import fetch

TEMPLATE = os.path.join(support.CORE, "template")
MATTHEW_CORPUS = support.MATTHEW_CORPUS
# words a Greek book's template text shouldn't carry (they belong to the
# Hebrew blocks), and the reverse
HEBREW_ONLY = ("Strong's", "Masoretic", "HebrewStrong", "morphhb", "binyan", "npm ci",
               "[Heb ")
GREEK_ONLY = ("biblecore fetch", "SBLGNT", "MorphGNT", "Septuagint", "lexemes.yaml")


def _cli(root, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("BIBLECORE_BOOK", None)
    return subprocess.run([sys.executable, "-m", "biblecore", *args], cwd=root, env=env,
                          capture_output=True, text=True, encoding="utf-8")


def _template_texts():
    for d, dirs, files in os.walk(TEMPLATE):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(new_book.TEXT_EXT) or f == ".gitignore":
                p = os.path.join(d, f)
                yield os.path.relpath(p, TEMPLATE).replace(os.sep, "/"), \
                    open(p, encoding="utf-8").read()


# ---- language blocks ---------------------------------------------------------

def test_keep_language_keeps_one_block_and_drops_markers():
    text = ("a\n<!-- lang: hebrew -->\nH\n<!-- /lang -->\n<!-- lang: greek -->\nG\n"
            "<!-- /lang -->\nb\n  # lang: greek\n  g2\n  # /lang\nc\n")
    fails = []
    if new_book.keep_language(text, "hebrew") != "a\nH\nb\nc\n":
        fails.append(f"hebrew: {new_book.keep_language(text, 'hebrew')!r}")
    if new_book.keep_language(text, "greek") != "a\nG\nb\n  g2\nc\n":
        fails.append(f"greek: {new_book.keep_language(text, 'greek')!r}")
    if new_book.keep_language("no blocks\n", "greek") != "no blocks\n":
        fails.append("text without blocks changed")
    for bad in ("<!-- lang: greek -->\nx\n",                              # unclosed
                "<!-- /lang -->\n",                                       # stray close
                "<!-- lang: greek -->\n<!-- lang: hebrew -->\n<!-- /lang -->\n",  # nested
                "<!-- lang: latin -->\nx\n<!-- /lang -->\n"):             # unknown
        try:
            new_book.keep_language(bad, "greek")
            fails.append(f"accepted {bad!r}")
        except ValueError:
            pass
    return fails


def test_template_renders_for_each_language():
    fails = []
    for rel, text in _template_texts():
        for language in new_book.LANGUAGES:
            if not new_book.for_language(rel, language) or rel == "book.json":
                continue  # not given to this language / patched by greek_config
            try:
                out = new_book.keep_language(text, language)
            except ValueError as exc:
                fails.append(f"{rel}: {exc}")
                break
            if any(new_book._LANG_OPEN.match(ln) or new_book._LANG_CLOSE.match(ln)
                   for ln in out.splitlines()):
                fails.append(f"{rel} ({language}): a block marker is left")
            other = HEBREW_ONLY if language == "greek" else GREEK_ONLY
            for w in other:
                if w in out:
                    fails.append(f"{rel} ({language}): has {w!r}")
    return fails


def test_new_book_greek_files_and_book_json():
    fails = []
    d = tempfile.mkdtemp(prefix="bc-greek-")
    h = tempfile.mkdtemp(prefix="bc-heb-")
    try:
        new_book.instantiate(d, "Mark", "Mark", "mark", language="greek")
        new_book.instantiate(h, "Leviticus", "Lev", "leviticus")
        cfg = json.load(open(os.path.join(d, "book.json"), encoding="utf-8"))
        fails += bookmod.validate_config(cfg)
        want = {"language": "greek", "versification": "source",
                "corpus": {"kind": "morphgnt", "pin": fetch.corpus_pin(), "word_ids": True}}
        for k, v in want.items():
            if cfg.get(k) != v:
                fails.append(f"book.json {k} = {cfg.get(k)!r}, want {v!r}")
        if "paths" in cfg:
            fails.append("book.json has paths; the Greek defaults are book.py's")
        heb = json.load(open(os.path.join(h, "book.json"), encoding="utf-8"))
        if [k for k in cfg if k != "versification"] != list(heb):
            fails.append("the Greek book.json's keys aren't the template's, in order")
        if os.path.exists(os.path.join(d, "package.json")):
            fails.append("a Greek book got package.json (morphhb)")
        if not os.path.exists(os.path.join(h, "package.json")):
            fails.append("a Hebrew book lost package.json")
        ignore = open(os.path.join(d, ".gitignore"), encoding="utf-8").read()
        if "corpus/morphgnt/" not in ignore or "corpus/lxx/" not in ignore:
            fails.append("a Greek book's .gitignore doesn't ignore the fetched corpus")
        out = new_book.copy_lexicon(d, "greek")
        if os.path.basename(out) != "lexemes.yaml":
            fails.append(f"Greek lexicon copied as {out}")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)
        shutil.rmtree(h, ignore_errors=True)


def test_greek_lexicon_pin_matches_shipped_file():
    got = new_book.sha1(new_book.GREEK_LEXICON)
    if got != new_book.GREEK_LEXICON_SHA1:
        return [f"corpus/lexicon/lexemes.yaml sha1 {got} != pin {new_book.GREEK_LEXICON_SHA1}"]
    return []


# ---- fetch -------------------------------------------------------------------

def _sha(data):
    return hashlib.sha1(data).hexdigest()


class _Mirror:
    """A local stand-in for raw.githubusercontent.com: two tiny pinned
    sources, laid out as <repo>/<commit>/<dir>/<file>, with fetch.SOURCES
    pointed at them for the test's duration."""
    FILES = {"morphgnt": {"62-Mk-morphgnt.txt": b"020101 N- ----NSM- a a a a\n"},
             "lxx": {"book.tf": b"@node\n\nGen\n", "lex_utf8.tf": b"@node\n\nx\n"}}

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="bc-fetch-")
        self.saved = fetch.SOURCES
        sources = {}
        for name, files in self.FILES.items():
            src = {"repo": f"test/{name}", "commit": "c0ffee" * 6 + "abcd", "dir": "d",
                   "path": name, "files": {f: _sha(b) for f, b in files.items()}}
            folder = os.path.join(self.tmp, "mirror", src["repo"], src["commit"], "d")
            os.makedirs(folder)
            for f, b in files.items():
                open(os.path.join(folder, f), "wb").write(b)
            sources[name] = src
        fetch.SOURCES = sources
        self.base = "file:///" + os.path.join(self.tmp, "mirror").replace(os.sep, "/").lstrip("/")
        self.root = os.path.join(self.tmp, "book")
        os.makedirs(self.root)
        self.book = bookmod.Book({"book": "Mark", "osis": "Mark", "slug": "mark",
                                  "language": "greek", "corpus": {"kind": "morphgnt"}},
                                 self.root)
        return self

    def run(self, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return fetch.fetch(self.book, base=self.base, **kw)

    def local(self, name, f):
        return os.path.join(self.root, "corpus", name, f)

    def __exit__(self, *exc):
        fetch.SOURCES = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)


def test_fetch_downloads_and_checks_every_file():
    with _Mirror() as m:
        fails = []
        problems = m.run()
        if problems:
            fails.append(f"first fetch: {problems}")
        for name, files in m.FILES.items():
            for f, data in files.items():
                p = m.local(name, f)
                if not os.path.exists(p) or open(p, "rb").read() != data:
                    fails.append(f"{name}/{f} not fetched intact")
        if m.run() or m.run(check_only=True):
            fails.append("a second fetch / --check found problems in good files")
        return fails


def test_fetch_fails_loudly_on_a_corrupted_file():
    with _Mirror() as m:
        fails = []
        m.run()
        p = m.local("lxx", "book.tf")
        open(p, "ab").write(b"corrupted\n")
        for kw in ({}, {"check_only": True}):
            problems = m.run(**kw)
            if not (len(problems) == 1 and "corpus/lxx/book.tf" in problems[0]
                    and "sha1" in problems[0]):
                fails.append(f"{kw or 'fetch'}: {problems}")
        if not open(p, "rb").read().endswith(b"corrupted\n"):
            fails.append("a plain fetch replaced the corrupted file instead of reporting it")
        if m.run(force=True) or open(p, "rb").read() != m.FILES["lxx"]["book.tf"]:
            fails.append("--force didn't put the pinned file back")
        return fails


def test_fetch_discards_a_download_that_doesnt_match_its_pin():
    with _Mirror() as m:
        fetch.SOURCES["morphgnt"]["files"]["62-Mk-morphgnt.txt"] = "0" * 40
        problems = m.run()
        fails = []
        if not (len(problems) == 1 and "downloaded sha1" in problems[0]):
            fails.append(f"problems: {problems}")
        folder = os.path.join(m.root, "corpus", "morphgnt")
        if os.path.exists(folder) and os.listdir(folder):
            fails.append(f"left behind: {os.listdir(folder)}")
        return fails


def test_fetch_check_reports_missing_without_downloading():
    with _Mirror() as m:
        problems = m.run(check_only=True)
        if len(problems) != 3 or not all("missing" in p for p in problems):
            return [f"problems: {problems}"]
        if os.path.exists(os.path.join(m.root, "corpus")):
            return ["--check downloaded"]
        return []


def test_fetch_is_a_no_op_for_hebrew():
    root = tempfile.mkdtemp(prefix="bc-fetch-")
    try:
        b = bookmod.Book({"book": "Lev", "osis": "Lev", "slug": "lev", "language": "hebrew",
                          "corpus": {"kind": "oshb"}}, root)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            problems = fetch.fetch(b, base="file:///nowhere")
        if problems or os.listdir(root) or "npm" not in out.getvalue():
            return [f"problems {problems}, wrote {os.listdir(root)}, said {out.getvalue()!r}"]
        return []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fetch_pins_match_matthews_corpus():
    """Core's pins are the commits in Matthew's retired fetch_corpus.py (archive/pipeline); its fetched files
    (the ones the parity tests read) must have the pinned sha1s."""
    if not os.path.isdir(MATTHEW_CORPUS):
        print("  skipped: no ../Matthew/corpus (python -m biblecore fetch there)")
        return []
    fails = []
    for name, src in fetch.SOURCES.items():
        for f, want in src["files"].items():
            p = os.path.join(MATTHEW_CORPUS, name, f)
            if not os.path.exists(p):
                fails.append(f"Matthew has no {name}/{f}")
            elif fetch.sha1_of(p) != want:
                fails.append(f"{name}/{f}: Matthew's sha1 {fetch.sha1_of(p)} != pin {want}")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_matthew_fetch", os.path.join(support.MATTHEW_PIPE, "fetch_corpus.py"))
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    if mf.MORPHGNT_SHA != fetch.SOURCES["morphgnt"]["commit"]:
        fails.append("MorphGNT commit differs from Matthew's fetch_corpus.py")
    if mf.LXX_SHA != fetch.SOURCES["lxx"]["commit"]:
        fails.append("LXX commit differs from Matthew's fetch_corpus.py")
    if sorted(mf.MORPHGNT_FILES) != sorted(fetch.SOURCES["morphgnt"]["files"]):
        fails.append("MorphGNT file list differs from Matthew's")
    if sorted(mf.LXX_FILES) != sorted(fetch.SOURCES["lxx"]["files"]):
        fails.append("LXX file list differs from Matthew's")
    return fails


# ---- a Greek book from the template, through the CLI --------------------------

def test_greek_book_from_the_template_builds_and_tests():
    d = tempfile.mkdtemp(prefix="bc-greek-tpl-")
    fails = []
    try:
        make_book(d, "Mark", "Mark", "mark", language="greek")
        new_book.copy_lexicon(d, "greek")
        # greek_book.py's tiny NT and LXX stand in for the fetched corpus
        mgnt = os.path.join(d, "corpus", "morphgnt")
        os.makedirs(mgnt)
        for stem, rows in greek_book.NT.items():
            with open(os.path.join(mgnt, f"{stem}-morphgnt.txt"), "w", encoding="utf-8",
                      newline="\n") as fh:
                for bcv, pos, parse, text, word, lemma in rows:
                    fh.write(f"{bcv} {pos} {parse} {text} {word} {word.lower()} {lemma}\n")
        greek_book.write_lxx(os.path.join(d, "corpus", "lxx"))
        for args in (("corpus",), ("build",), ("test",), ("book",)):
            r = _cli(d, *args)
            if r.returncode:
                fails.append(f"`biblecore {' '.join(args)}` exited {r.returncode}:\n"
                             + (r.stdout + r.stderr)[-1500:])
                return fails
            if args == ("corpus",) and "lemmas have a gloss" not in r.stdout:
                fails.append(f"`biblecore corpus` printed no lexicon check:\n{r.stdout}")
        r = _cli(d, "book")
        for want in ("morphgnt", "lxx", "greek_lexicon"):
            if want not in r.stdout:
                fails.append(f"`biblecore book` doesn't show the {want} path")
        if "wlc" in r.stdout:
            fails.append("`biblecore book` shows morphhb's wlc for a Greek book")
        with open(os.path.join(d, "mark-literary-unit-map.md"), "w", encoding="utf-8") as fh:
            fh.write("## Overview\n\n| # | Passage | Working title |\n|---|---|---|\n"
                     "| | **PART ONE — Start (1:1–1:1)** | |\n| 01 | 1:1 | One |\n")
        r = _cli(d, "units-from-map", "--kinds", "part")
        leads = os.path.join(d, "canon-leads", "canon-leads-unit-01.md")
        if r.returncode or not os.path.exists(leads):
            fails.append(f"units-from-map wrote no Greek canon leads:\n{(r.stdout + r.stderr)[-800:]}")
        elif "LXX" not in open(leads, encoding="utf-8").read():
            fails.append("the canon leads aren't the Greek (LXX + NT) kind")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)
