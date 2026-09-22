"""Instantiate the starter template as a scratch book (test helper).

make_book(dest, name, osis, slug) copies template/ to dest, fills the
{{BOOK}}/{{OSIS}}/{{ABBREV}}/{{SLUG}} placeholders (file names included),
and vendors this checkout's biblecore/ + canon conventions, the same way
tools/core_sync.py does minus the git bookkeeping.
"""
import os
import shutil

import support

TEMPLATE = os.path.join(support.CORE, "template")
TEXT_EXT = (".md", ".json", ".html", ".js", ".css", ".gitignore")


def make_book(dest, name, osis, slug, abbrev=None):
    subs = {"{{BOOK}}": name, "{{OSIS}}": osis, "{{ABBREV}}": abbrev or osis,
            "{{SLUG}}": slug}

    def fill(s):
        for k, v in subs.items():
            s = s.replace(k, v)
        return s

    for d, _dirs, files in os.walk(TEMPLATE):
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
    shutil.copytree(os.path.join(support.CORE, "biblecore"), os.path.join(dest, "biblecore"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(os.path.join(support.CORE, "canon", "conventions.md"),
                    os.path.join(dest, "canon-conventions.md"))
    from biblecore import __version__
    with open(os.path.join(dest, "biblecore", "CORE_VERSION"), "w") as fh:
        fh.write(f"{__version__} test\n")
    return dest
