"""Start a new book from the template (stage one; ARCHITECTURE.md §8).

    python tools/new_book.py ../Leviticus --book Leviticus --osis Lev
    python tools/new_book.py ../Leviticus --book Leviticus --osis Lev --github
    python tools/new_book.py ../Mark --book Mark --osis Mark --language greek

Written from Numbers' setup log (H14). In order:

  1. copy template/ to the new folder, filling {{BOOK}} {{OSIS}} {{ABBREV}}
     {{SLUG}} in file names and contents, and book.json's {{CORE}} (this
     checkout's version) and {{TEMPLATE}} (its commit: the book's template
     base, read by `core_diff.py --template`). Template files carry
     language blocks (`<!-- lang: greek -->` ... `<!-- /lang -->`, or `#`
     comments in yml/.gitignore); the book keeps its language's blocks and
     loses the others' (keep_language). A Greek book's book.json gets its
     language, corpus and versification (greek_config); LANGUAGE_ONLY files
     (package.json) go only to their language's books
  2. vendor biblecore/ + canon files (core_sync.py, which also sets
     book.json "core")
  3. copy the language's lexicon from corpus/lexicon/ (sha1-checked): Strong's
     for Hebrew, read by canon leads' glosses (learned: Numbers' glosses were
     all "?" until it was copied over by hand); the MorphGNT lexicon for
     Greek, read by the interlinear's glosses
  4. the corpus: Hebrew `npm install` (morphhb, the pin in package.json),
     Greek `python -m biblecore fetch` (MorphGNT + LXX, pinned and
     sha1-checked in biblecore/fetch.py); then `python -m biblecore corpus`
  5. `python -m biblecore build` on the empty book (its `assets` step writes
     the app shell: index.html, app/*.js)
  6. git init + first commit
  7. --github only: create the GitHub repo (public, since Pages needs it on
     a free plan), push, enable Pages from main, and run the first sync
  8. add the book's row to canon/books.json here in bible-core (site, repo
     folder, kind core), so the hub picks it up; the hub's rebuild workflow
     clones every book with a row. Commit it in bible-core. --no-register
     skips this (a scratch or test book; a scratch Matthew would otherwise
     overwrite Matthew's legacy row).

Stage two runs once the project side delivers the literary unit map:
`python -m biblecore units-from-map` in the new book loads its unit rows
and groupings and writes the next unit's canon leads.

Stops at the first failed step and says which; the folder is left as it is
so the step can be finished by hand.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(CORE, "template")
LEXICON = os.path.join(CORE, "corpus", "lexicon", "HebrewStrong.xml")
# sha1 of the file with LF line endings: a checkout with core.autocrlf
# (Windows) has CRLF on disk, one without has LF, and both must pass
LEXICON_SHA1 = "15861be1f825151a59513fae0117574ff46b7e56"
GREEK_LEXICON = os.path.join(CORE, "corpus", "lexicon", "lexemes.yaml")
GREEK_LEXICON_SHA1 = "9db21bd70bc88510d6b4caefe436ea744b684a65"
# language -> (core's copy, its LF sha1)
LEXICONS = {"hebrew": (LEXICON, LEXICON_SHA1),
            "greek": (GREEK_LEXICON, GREEK_LEXICON_SHA1)}
LANGUAGES = tuple(LEXICONS)
# template files only one language's books get
LANGUAGE_ONLY = {"package.json": "hebrew"}
TEXT_EXT = (".md", ".json", ".html", ".js", ".css", ".gitignore", ".yml")
BOOKS_JSON = os.path.join(CORE, "canon", "books.json")

sys.path.insert(0, CORE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def placeholders(name, osis, slug, abbrev=None, core=None, template=None):
    """The template's placeholders and their values. {{CORE}} and
    {{TEMPLATE}} (book.json's "core" and "template") default to this
    checkout's version and commit: biblecore/__init__.py is the one place
    the version is written (structural audit F4)."""
    if core is None:
        from biblecore import __version__ as core
    if template is None:
        template = template_commit()
    return {"{{BOOK}}": name, "{{OSIS}}": osis, "{{ABBREV}}": abbrev or osis,
            "{{SLUG}}": slug, "{{CORE}}": core, "{{TEMPLATE}}": template}


_LANG_OPEN = re.compile(r"^\s*(?:<!--|#)\s*lang:\s*([a-z]+)\s*(?:-->)?\s*$")
_LANG_CLOSE = re.compile(r"^\s*(?:<!--|#)\s*/lang\s*(?:-->)?\s*$")


def keep_language(text, language="hebrew"):
    """A template file as a `language` book gets it: the lines inside its own
    language blocks kept, other languages' blocks dropped, and the marker
    lines themselves removed. A block opens with a line that is only
    `<!-- lang: greek -->` (or `# lang: greek` where # is a comment) and
    closes with `<!-- /lang -->` (`# /lang`). Blocks don't nest."""
    out, block = [], None
    for n, line in enumerate(text.splitlines(True), 1):
        m = _LANG_OPEN.match(line)
        if m:
            if block:
                raise ValueError(f"line {n}: a lang block opens inside the {block} block")
            if m.group(1) not in LANGUAGES:
                raise ValueError(f"line {n}: unknown language {m.group(1)!r} "
                                 f"(known: {', '.join(LANGUAGES)})")
            block = m.group(1)
            continue
        if _LANG_CLOSE.match(line):
            if not block:
                raise ValueError(f"line {n}: /lang with no open block")
            block = None
            continue
        if block is None or block == language:
            out.append(line)
    if block:
        raise ValueError(f"the {block} block is never closed")
    return "".join(out)


def for_language(rel, language="hebrew"):
    """Whether a template file (path relative to template/) goes to a
    `language` book."""
    return LANGUAGE_ONLY.get(rel.replace(os.sep, "/"), language) == language


def greek_config(cfg):
    """book.json for a Greek book: the template's (Hebrew) config with the
    language, corpus and versification swapped, key order kept. The Greek
    paths (morphgnt, lxx, greek_lexicon) are book.py's defaults, so none is
    written."""
    from biblecore import fetch
    out = {}
    for k, v in cfg.items():
        if k == "language":
            v = "greek"
        elif k == "corpus":
            v = {"kind": "morphgnt", "pin": fetch.corpus_pin(), "word_ids": True}
        out[k] = v
        if k == "corpus":
            # SBLGNT numbers verses as English Bibles do
            out["versification"] = "source"
    return out


def fill(s, subs):
    for k, v in subs.items():
        if v is not None:
            s = s.replace(k, v)
    return s


def template_commit(rev="HEAD"):
    """Short hash of a bible-core commit (a book's template base), or None
    outside a git checkout."""
    r = subprocess.run(["git", "rev-parse", "--short=7", rev], cwd=CORE,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def instantiate(dest, name, osis, slug, abbrev=None, language="hebrew"):
    """Copy template/ to dest with the placeholders filled (names too) and
    the language blocks resolved for `language`."""
    if language not in LANGUAGES:
        raise ValueError(f"unknown language {language!r} (known: {', '.join(LANGUAGES)})")
    subs = placeholders(name, osis, slug, abbrev)

    for d, _dirs, files in os.walk(TEMPLATE):
        _dirs[:] = [x for x in _dirs if x != "__pycache__"]
        rel_dir = os.path.relpath(d, TEMPLATE)
        out_dir = os.path.join(dest, fill(rel_dir, subs)) if rel_dir != "." else dest
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            src = os.path.join(d, f)
            if not for_language(os.path.normpath(os.path.join(rel_dir, f)), language):
                continue
            dst = os.path.join(out_dir, fill(f, subs))
            if f.endswith(TEXT_EXT) or f == ".gitignore":
                with open(src, encoding="utf-8") as fh:
                    text = keep_language(fh.read(), language)
                if subs["{{TEMPLATE}}"] is None and "{{TEMPLATE}}" in text:
                    # no git: leave the base unrecorded rather than write a bad one
                    text = "".join(ln for ln in text.splitlines(True)
                                   if "{{TEMPLATE}}" not in ln).replace('",\n}', '"\n}')
                text = fill(text, subs)
                if language == "greek" and rel_dir == "." and f == "book.json":
                    text = json.dumps(greek_config(json.loads(text)), indent=2,
                                      ensure_ascii=False) + "\n"
                with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
            else:
                shutil.copyfile(src, dst)
    return dest


def sha1(path):
    """sha1 of a text file's content with CRLF read as LF, so the check
    doesn't depend on how git checked the file out."""
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def copy_lexicon(dest, language="hebrew"):
    src, want = LEXICONS[language]
    out = os.path.join(dest, "corpus", "lexicon", os.path.basename(src))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(src, out)
    got = sha1(out)
    if got != want:
        raise RuntimeError(f"lexicon sha1 {got} != expected {want}")
    return out


def pages_owner(path=BOOKS_JSON):
    """The GitHub owner of the started books' Pages sites (all one owner)."""
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)["books"]
    for r in rows:
        if r.get("site", "").startswith("https://") and ".github.io/" in r["site"]:
            return r["site"][len("https://"):].split(".github.io/")[0]
    return None


def register_book(osis, slug, repo, owner, path=BOOKS_JSON):
    """Fill the book's row in canon/books.json: slug, site (its Pages URL,
    which also names the GitHub repo the hub workflow clones), repo (the
    folder name next to bible-core) and kind "core". The file keeps one row
    per line; only this book's line changes. Returns the new row."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    key = f'"osis": "{osis}"'
    hits = [i for i, ln in enumerate(lines) if key in ln]
    if len(hits) != 1:
        raise RuntimeError(f"expected one canon/books.json row for {osis}, found {len(hits)}")
    i = hits[0]
    body = lines[i].strip()
    comma = body.endswith(",")
    row = json.loads(body.rstrip(","))
    row.update(slug=slug, site=f"https://{owner.lower()}.github.io/{slug}/",
               repo=repo, kind="core")
    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
    lines[i] = indent + json.dumps(row, ensure_ascii=False) + ("," if comma else "")
    text = "\n".join(lines)
    json.loads(text)  # still valid
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return row


def run(cmd, cwd, check=True):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("BIBLECORE_BOOK", None)
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
    for ln in tail:
        print("   ", ln)
    if check and r.returncode:
        raise RuntimeError(f"{cmd[0]} exited {r.returncode}")
    return r


def tool(name):
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} not found on PATH")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="new_book.py")
    ap.add_argument("dest", help="the new book's folder, e.g. ../Leviticus")
    ap.add_argument("--book", required=True, help="display name, e.g. Leviticus")
    ap.add_argument("--osis", required=True, help="OSIS id, e.g. Lev")
    ap.add_argument("--slug", help="file/repo slug (default: book name, lowercased)")
    ap.add_argument("--abbrev", help="short citation form (default: the OSIS id)")
    ap.add_argument("--language", choices=LANGUAGES, default="hebrew",
                    help="the book's language (default hebrew); greek fetches "
                         "MorphGNT + LXX instead of npm's morphhb")
    ap.add_argument("--skip-corpus", "--skip-npm", dest="skip_npm", action="store_true",
                    help="skip the corpus step (npm install or fetch, then corpus; "
                         "e.g. offline); run them later")
    ap.add_argument("--no-register", action="store_true",
                    help="don't add the canon/books.json row (a scratch or test book)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="vendor even with uncommitted core changes (testing only)")
    ap.add_argument("--github", action="store_true",
                    help="also create the GitHub repo, push, enable Pages, first sync")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    dest = os.path.abspath(a.dest)
    slug = a.slug or a.book.lower().replace(" ", "-")
    if os.path.exists(dest) and os.listdir(dest):
        print(f"{dest} exists and isn't empty -- refusing to write into it")
        return 1

    from biblecore import __version__
    step = "start"
    try:
        step = "template"
        print(f"[1] template -> {dest}")
        instantiate(dest, a.book, a.osis, slug, a.abbrev, a.language)

        step = "vendor"
        print("[2] vendor bible-core")
        import core_sync
        if core_sync.main([dest] + (["--allow-dirty"] if a.allow_dirty else [])):
            raise RuntimeError("core_sync refused (see above)")

        step = "lexicon"
        greek = a.language == "greek"
        print("[3] MorphGNT lexicon" if greek else "[3] Strong's lexicon")
        copy_lexicon(dest, a.language)
        print(f"    sha1 ok ({LEXICONS[a.language][1][:10]})")

        if a.skip_npm:
            print(f"[4] {'fetch' if greek else 'npm'} + corpus skipped (--skip-corpus): "
                  f"run `{'python -m biblecore fetch' if greek else 'npm install'}` "
                  f"then `python -m biblecore corpus`")
        elif greek:
            step = "fetch"
            print("[4] fetch (MorphGNT + LXX, sha1-checked) + corpus")
            run([sys.executable, "-m", "biblecore", "fetch"], dest)
            step = "corpus"
            run([sys.executable, "-m", "biblecore", "corpus"], dest)
        else:
            step = "npm"
            print("[4] npm install + corpus")
            run([tool("npm"), "install", "--no-fund", "--no-audit"], dest)
            step = "corpus"
            run([sys.executable, "-m", "biblecore", "corpus"], dest)

        step = "build"
        print("[5] build")
        run([sys.executable, "-m", "biblecore", "build"], dest, check=not a.skip_npm)

        step = "git"
        print("[6] git init + first commit")
        git = tool("git")
        commit = core_sync.core_commit() or "unknown"
        with open(os.path.join(dest, "improvements_log.md"), "a", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(f"\n- Bootstrapped with `tools/new_book.py` from bible-core "
                     f"{__version__} (`{commit[:7]}`): template, vendored core, "
                     f"lexicon"
                     + ("" if a.skip_npm else ", fetch + corpus" if greek
                        else ", npm + corpus")
                     + ". Check the corpus counts against a printed edition.\n")
        run([git, "init", "-q", "-b", "main"], dest)
        run([git, "add", "-A"], dest)
        run([git, "commit", "-q", "-m",
             f"Bootstrap {a.book} from bible-core {__version__} ({commit[:7]})"], dest)

        if a.github:
            step = "github"
            print("[7] GitHub repo + Pages + first sync")
            gh = tool("gh")
            run([gh, "repo", "create", slug, "--public", "--source", ".",
                 "--remote", "origin", "--push"], dest)
            owner = run([gh, "api", "user", "-q", ".login"], dest).stdout.strip()
            run([gh, "api", "-X", "POST", f"repos/{owner}/{slug}/pages",
                 "-f", "source[branch]=main", "-f", "source[path]=/"], dest)
            print(f"    site: https://{owner.lower()}.github.io/{slug}/")
            step = "sync"
            run([sys.executable, "-m", "biblecore", "sync"], dest)
        else:
            owner = pages_owner()
            if not owner and not a.no_register:
                raise RuntimeError("no GitHub owner found in canon/books.json; "
                                   "add the book's row by hand")

        step = "hub row"
        if a.no_register:
            print("[8] canon/books.json row skipped (--no-register)")
        else:
            print("[8] canon/books.json row (the hub)")
            row = register_book(a.osis, slug, os.path.basename(dest), owner)
            print(f"    {row['name']}: {row['site']} (repo folder {row['repo']}); "
                  f"commit canon/books.json in bible-core")
    except RuntimeError as exc:
        print(f"\nstopped at '{step}': {exc}\nthe folder is left as it is; "
              f"finish that step by hand and carry on from the list in this "
              f"script's docstring.")
        return 1

    print(f"\n{a.book} is set up at {dest}.")
    if not a.github:
        print("No remote yet. When ready:\n"
              f"  gh repo create {slug} --public --source . --remote origin --push\n"
              f"  gh api -X POST repos/<owner>/{slug}/pages "
              "-f source[branch]=main -f source[path]=/\n"
              "  python -m biblecore sync")
    print("Next: fill the style reference and chat-side ✎ sections; once the "
          "project side delivers the unit map, run\n"
          "  python -m biblecore units-from-map --kinds <outer>,<inner>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
