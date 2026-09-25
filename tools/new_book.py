"""Start a new book from the template (stage one; ARCHITECTURE.md §8).

    python tools/new_book.py ../Leviticus --book Leviticus --osis Lev
    python tools/new_book.py ../Leviticus --book Leviticus --osis Lev --github

Written from Numbers' setup log (H14). In order:

  1. copy template/ to the new folder, filling {{BOOK}} {{OSIS}} {{ABBREV}}
     {{SLUG}} in file names and contents
  2. vendor biblecore/ + canon files (core_sync.py); book.json "core"
     set to this checkout's version
  3. copy the Strong's lexicon from corpus/lexicon/ (sha1-checked); canon
     leads' glosses read it (learned: Numbers' glosses were all "?" until
     it was copied over by hand)
  4. npm install (morphhb, the pin in package.json), then
     `python -m biblecore corpus`
  5. `python -m biblecore build` on the empty book
  6. git init + first commit
  7. --github only: create the GitHub repo (public, since Pages needs it on
     a free plan), push, enable Pages from main, and run the first sync

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
import shutil
import subprocess
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(CORE, "template")
LEXICON = os.path.join(CORE, "corpus", "lexicon", "HebrewStrong.xml")
LEXICON_SHA1 = "9f3ab556ebc0870d59f3f192ba79b54531faf4ee"
TEXT_EXT = (".md", ".json", ".html", ".js", ".css", ".gitignore")

sys.path.insert(0, CORE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def instantiate(dest, name, osis, slug, abbrev=None):
    """Copy template/ to dest with the placeholders filled (names too)."""
    subs = {"{{BOOK}}": name, "{{OSIS}}": osis, "{{ABBREV}}": abbrev or osis,
            "{{SLUG}}": slug}

    def fill(s):
        for k, v in subs.items():
            s = s.replace(k, v)
        return s

    for d, _dirs, files in os.walk(TEMPLATE):
        _dirs[:] = [x for x in _dirs if x != "__pycache__"]
        rel_dir = os.path.relpath(d, TEMPLATE)
        out_dir = os.path.join(dest, fill(rel_dir)) if rel_dir != "." else dest
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            src = os.path.join(d, f)
            dst = os.path.join(out_dir, fill(f))
            if f.endswith(TEXT_EXT) or f == ".gitignore":
                with open(src, encoding="utf-8") as fh:
                    text = fill(fh.read())
                with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
            else:
                shutil.copyfile(src, dst)
    return dest


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_lexicon(dest):
    out = os.path.join(dest, "corpus", "lexicon", "HebrewStrong.xml")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(LEXICON, out)
    got = sha1(out)
    if got != LEXICON_SHA1:
        raise RuntimeError(f"lexicon sha1 {got} != expected {LEXICON_SHA1}")
    return out


def set_core_version(dest):
    from biblecore import __version__
    p = os.path.join(dest, "book.json")
    with open(p, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["core"] = __version__
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


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
    ap.add_argument("--skip-npm", action="store_true",
                    help="skip npm install + corpus (e.g. offline); run them later")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="vendor even with uncommitted core changes (testing only)")
    ap.add_argument("--github", action="store_true",
                    help="also create the GitHub repo, push, enable Pages, first sync")
    a = ap.parse_args(argv)

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
        instantiate(dest, a.book, a.osis, slug, a.abbrev)

        step = "vendor"
        print("[2] vendor bible-core")
        import core_sync
        if core_sync.main([dest] + (["--allow-dirty"] if a.allow_dirty else [])):
            raise RuntimeError("core_sync refused (see above)")
        set_core_version(dest)

        step = "lexicon"
        print("[3] Strong's lexicon")
        copy_lexicon(dest)
        print(f"    sha1 ok ({LEXICON_SHA1[:10]})")

        if a.skip_npm:
            print("[4] npm + corpus skipped (--skip-npm): run `npm install` then "
                  "`python -m biblecore corpus`")
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
                     + ("" if a.skip_npm else ", npm + corpus")
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
