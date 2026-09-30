"""The synced-file list (structural audit P4): core supplies the defaults,
book.json `sync` holds only extras and skips, and `sync` prunes mirror
files that have left the list."""
import contextlib
import io
import os
import shutil
import subprocess
import tempfile

import support
from template_book import make_book
from biblecore import book as bookmod
from biblecore import sync

MIN = {"book": "Leviticus", "osis": "Lev", "slug": "leviticus", "language": "hebrew",
       "corpus": {"kind": "oshb", "pin": "morphhb@2.0.2", "word_ids": True}}


def _touch(root, *rels):
    for rel in rels:
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rel + "\n")


def _book(root, **sync_cfg):
    cfg = dict(MIN, sync=sync_cfg) if sync_cfg else dict(MIN)
    return bookmod.Book(cfg, root)


def test_old_sync_keys_name_the_replacement():
    errs = bookmod.validate_config(dict(MIN, sync={"files": ["a.md"], "globs": []}))
    fails = []
    for k in ("files", "globs"):
        if not any(f"sync: '{k}' was replaced" in e and "sync.extra" in e for e in errs):
            fails.append(f"no replacement hint for sync.{k}: {errs}")
    if not any("sync.extra must be a list" in e
               for e in bookmod.validate_config(dict(MIN, sync={"extra": "a.md"}))):
        fails.append("a non-list sync.extra passed")
    return fails


def test_defaults_required_and_optional():
    d = tempfile.mkdtemp(prefix="bc-sync-")
    try:
        b = _book(d)
        got = sync.resolve(b)
        fails = []
        # required defaults are listed even when absent (sync-check says MISSING)
        for rel in ("leviticus_study_style_reference.md", "resources.md",
                    "data/roots.json", "Leviticus-words.tsv", "core-workflow.md"):
            if rel not in got:
                fails.append(f"required default {rel} not listed")
        # optional defaults only once they exist
        opt = ("leviticus-literary-unit-map.md", "canon-leads/canon-leads-unit-01.md",
               "leviticus-versification.md")
        fails += [f"{rel} listed before it exists" for rel in opt if rel in got]
        _touch(d, *opt)
        got = sync.resolve(b)
        fails += [f"{rel} not listed once it exists" for rel in opt if rel not in got]
        return fails
    finally:
        shutil.rmtree(d)


def test_extra_and_skip():
    d = tempfile.mkdtemp(prefix="bc-sync-")
    try:
        _touch(d, "notes/a.md", "notes/b.md", "canon-leads/canon-leads-unit-01.md",
               "canon-leads/canon-leads-unit-02.md")
        b = _book(d, extra=["Leviticus-reading.txt", "notes/*.md", "resources.md"],
                  skip=["canon-leads/*-02.md", "translation-choices.md"])
        got = sync.resolve(b)
        fails = []
        for rel in ("Leviticus-reading.txt", "notes/a.md", "notes/b.md",
                    "canon-leads/canon-leads-unit-01.md"):
            if rel not in got:
                fails.append(f"{rel} missing")
        for rel in ("canon-leads/canon-leads-unit-02.md", "translation-choices.md"):
            if rel in got:
                fails.append(f"skipped {rel} still listed")
        if got.count("resources.md") != 1:
            fails.append("an extra that repeats a default is listed twice")
        if got.index("Leviticus-reading.txt") < got.index("resources.md"):
            fails.append("extras should follow the defaults")
        return fails
    finally:
        shutil.rmtree(d)


def test_defaults_follow_path_overrides():
    d = tempfile.mkdtemp(prefix="bc-sync-")
    try:
        cfg = dict(MIN, paths={"digest": "docs/digest.md", "data": "store"})
        got = sync.resolve(bookmod.Book(cfg, d))
        want = ["docs/digest.md", "store/roots.json"]
        return [f"{w} not in {got}" for w in want if w not in got]
    finally:
        shutil.rmtree(d)


def test_every_default_has_a_role_and_exists_in_a_fresh_book():
    """synced-index.md is the one list of synced files; every default needs a
    role there (sync.ROLES), or the index says 'book file' and the chat side
    learns nothing. Every required default exists in a fresh book, apart
    from those the build generates."""
    d = tempfile.mkdtemp(prefix="bc-roles-")
    try:
        make_book(d, "Leviticus", "Lev", "leviticus")
        b = bookmod.Book.from_file(os.path.join(d, "book.json"))
        fails = []
        for entry, required in sync.DEFAULT_SYNC:
            rel = sync._fill(b, entry).replace("*", "01")
            if not sync.role_for(os.path.basename(rel), b):
                fails.append(f"{rel}: no role in sync.ROLES")
            generated = {"threads-digest.md", "Leviticus-words.tsv",
                         "components-reference.md"}
            if required and rel not in generated and not os.path.exists(os.path.join(d, rel)):
                fails.append(f"{rel}: missing from a fresh book")
        text = sync.index_text(b)
        if "resources.md" not in text or "core-workflow.md" not in text:
            fails.append("index misses resources.md or core-workflow.md")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)
        support.joshua_book()


def _git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   cwd=cwd, check=True, capture_output=True)


def test_sync_prunes_files_that_left_the_list():
    """A skipped (or renamed) file's old mirror copy is removed by the next
    sync, after sync-check reports it (step 1 had to `git rm` Joshua's old
    map copy by hand)."""
    d = tempfile.mkdtemp(prefix="bc-prune-")
    try:
        book_dir, remote = os.path.join(d, "book"), os.path.join(d, "remote.git")
        make_book(book_dir, "Leviticus", "Lev", "leviticus")
        _git(d, "init", "-q", "--bare", remote)
        _git(book_dir, "init", "-q", "-b", "main")
        _git(book_dir, "config", "user.name", "t")
        _git(book_dir, "config", "user.email", "t@t")
        _git(book_dir, "remote", "add", "origin", remote)
        _git(book_dir, "add", "-A")
        _git(book_dir, "commit", "-q", "-m", "start")
        _git(book_dir, "push", "-q", "-u", "origin", "main")
        bookmod.use(bookmod.Book.from_file(os.path.join(book_dir, "book.json")))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sync.push_main([])
        mirror = os.path.join(book_dir, "project-side", "synced")
        fails = []
        if not os.path.exists(os.path.join(mirror, "resources.md")):
            return ["first sync didn't mirror resources.md"]
        # the book now skips resources.md
        import json
        p = os.path.join(book_dir, "book.json")
        cfg = json.load(open(p, encoding="utf-8"))
        cfg["sync"] = {"extra": [], "skip": ["resources.md"]}
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(cfg, fh, indent=2)
        bookmod.use(bookmod.Book.from_file(p))
        if sync.orphans() != ["resources.md"]:
            fails.append(f"orphans() = {sync.orphans()}")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = sync.check_main([])
        if "NO LONGER SYNCED" not in buf.getvalue() or rc != 1:
            fails.append(f"sync-check didn't report the orphan (rc {rc})")
        with contextlib.redirect_stdout(io.StringIO()):
            sync.push_main([])
        if os.path.exists(os.path.join(mirror, "resources.md")):
            fails.append("sync left the skipped file in the mirror")
        tracked = subprocess.run(["git", "ls-files", "project-side/synced/resources.md"],
                                 cwd=book_dir, capture_output=True, text=True).stdout
        if tracked.strip():
            fails.append("the removal wasn't committed")
        if sync.orphans():
            fails.append(f"orphans left after sync: {sync.orphans()}")
        return fails
    finally:
        support.joshua_book()
        shutil.rmtree(d, ignore_errors=True)
