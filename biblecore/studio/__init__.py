"""Studio: the in-Claude-Code unit flow (`/unit`, `/finish`, `builder`,
`fact-checker`, `tools/kit.py` and friends), for a book whose book.json has a
"studio" object. No Claude.ai project, chat cards or field in such a book.

    python -m biblecore studio            # install or update the studio files
    python -m biblecore studio --check    # what would change, write nothing
    python -m biblecore studio --force    # overwrite files the book edited

templates/ is copied into the book (`claude/` -> `.claude/`), with
{{BOOK}} {{SLUG}} {{MAP}} {{STYLE}} {{SCRIPT}} filled in .md files. The files
are core's: tools/core_sync.py reinstalls them on every vendor. A book's own
differences go in its CLAUDE.md (which every skill and agent reads first) or
in a tool of its own under another name. `.claude/studio.json` records what
was installed, so an edit made in the book is noticed and not overwritten
(the edit belongs in bible-core, or in the book's CLAUDE.md).

book.json "studio": {"whole": [source keys read whole per unit; the rest by
range], "lxx_numbering": "hebrew" (Brenton's English follows the Hebrew verse
numbers)}. Both optional.
"""
import argparse
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")
STUDIO_KEYS = {"whole", "lxx_numbering"}
RECORD = ".claude/studio.json"


def validate(cfg):
    """Problems with book.json "studio" ([] = fine)."""
    s = cfg.get("studio")
    if s is None:
        return []
    if not isinstance(s, dict):
        return ["'studio' must be an object ({} for the defaults)"]
    errs = [f"studio: unknown key '{k}' (known: {sorted(STUDIO_KEYS)})" for k in sorted(set(s) - STUDIO_KEYS)]
    if "whole" in s and not (isinstance(s["whole"], list) and all(isinstance(x, str) for x in s["whole"])):
        errs.append("studio.whole must be a list of source keys")
    if s.get("lxx_numbering", "english") not in ("english", "hebrew"):
        errs.append("studio.lxx_numbering must be 'english' or 'hebrew'")
    return errs


def is_studio(book_root):
    try:
        with open(os.path.join(book_root, "book.json"), encoding="utf-8") as fh:
            return isinstance(json.load(fh).get("studio"), dict)
    except (OSError, ValueError):
        return False


def values(book_root):
    with open(os.path.join(book_root, "book.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    slug = cfg["slug"]
    style = (cfg.get("paths") or {}).get("style_reference") or f"{slug}_study_style_reference.md"
    return {"BOOK": cfg["book"], "SLUG": slug, "MAP": f"{slug}-literary-unit-map.md",
            "STYLE": style, "SCRIPT": "Hebrew" if cfg.get("language") == "hebrew" else "Greek"}


def rendered(book_root):
    """{book-relative path: bytes} for every studio file."""
    vals = values(book_root)
    out = {}
    for d, dirs, files in os.walk(TEMPLATES):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            src = os.path.join(d, f)
            rel = os.path.relpath(src, TEMPLATES).replace(os.sep, "/")
            if rel.startswith("claude/"):
                rel = "." + rel
            with open(src, encoding="utf-8") as fh:
                text = fh.read().replace("\r\n", "\n")
            if f.endswith(".md"):
                for k, v in vals.items():
                    text = text.replace("{{" + k + "}}", v)
            out[rel] = text.encode("utf-8")
    return out


def _sha(b):
    return hashlib.sha1(b.replace(b"\r\n", b"\n")).hexdigest()


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


def plan(book_root):
    """([(action, rel)], [rel edited in the book])."""
    rp = os.path.join(book_root, RECORD)
    record = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
    acts, edited = [], []
    want = rendered(book_root)
    for rel, data in sorted(want.items()):
        p = os.path.join(book_root, rel)
        if not os.path.exists(p):
            acts.append(("add", rel))
            continue
        have = _sha(_read(p))
        if have == _sha(data):
            continue
        if rel in record and record[rel] != have:
            edited.append(rel)
        acts.append(("update", rel))
    for rel in sorted(set(record) - set(want)):
        if os.path.exists(os.path.join(book_root, rel)):
            acts.append(("remove", rel))
    return acts, edited


def install(book_root, check=False, force=False, log=print):
    """0 done (or nothing to do), 1 refused: the book edited a studio file."""
    acts, edited = plan(book_root)
    if edited and not force:
        log("studio files edited in the book (move the change into bible-core or the "
            "book's CLAUDE.md, or pass --force to overwrite):")
        for rel in edited:
            log(f"   {rel}")
        return 1
    for act, rel in acts:
        log(f"  {act:6} {rel}")
    if check:
        return 0
    want = rendered(book_root)
    for act, rel in acts:
        p = os.path.join(book_root, rel)
        if act == "remove":
            os.remove(p)
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(want[rel])
    rp = os.path.join(book_root, RECORD)
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    with open(rp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({rel: _sha(b) for rel, b in sorted(want.items())}, indent=1) + "\n")
    return 0


def main(argv=None):
    from biblecore.book import book
    ap = argparse.ArgumentParser(prog="biblecore studio")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    b = book()
    if not is_studio(b.root):
        print('not a studio book: add "studio": {} to book.json first')
        return 2
    rc = install(b.root, a.check, a.force)
    if rc == 0 and not a.check:
        print("studio files current")
    return rc
