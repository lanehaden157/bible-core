"""The app shell as core-owned, generated code (0.11.0; structural audit
F1/F2): `assets` writes index.html + app/*.js from biblecore/web/ with the
book name filled in and every same-origin link stamped with a content hash.
On a scratch book made from the template."""
import contextlib
import io
import json
import os
import re
import shutil
import tempfile

import support
from template_book import make_book
from biblecore import assets
from biblecore import book as bookmod

_tmp = None
SHELL = ["index.html"] + [f"app/{f}" for f in sorted(os.listdir(os.path.join(assets.WEB, "app")))]
HASHED = re.compile(r"\?v=[0-9a-f]{10}\b")


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-shell-")
    make_book(_tmp, "Leviticus", "Lev", "leviticus")
    bookmod.use(bookmod.Book.from_file(os.path.join(_tmp, "book.json")))


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _assets():
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assets.main([])
    return out.getvalue()


def _read(rel):
    return support.read(os.path.join(_tmp, rel))


def test_template_ships_no_shell():
    tpl = os.path.join(support.CORE, "template")
    return [f"template/{x} still exists: the shell is generated since 0.11.0"
            for x in ("index.html", "app") if os.path.exists(os.path.join(tpl, x))]


def test_assets_writes_the_shell():
    _assets()
    fails = []
    for rel in SHELL:
        p = os.path.join(_tmp, rel)
        if not os.path.exists(p):
            fails.append(f"{rel} not written")
            continue
        text = support.read(p)
        if "{{" in text:
            fails.append(f"{rel}: placeholder left")
        if "Don't edit it here" not in text[:400]:
            fails.append(f"{rel}: no 'generated, don't edit' mark")
        if b"\r\n" in open(p, "rb").read():
            fails.append(f"{rel}: CRLF")
        # every same-origin import is stamped, none left bare or hand-numbered
        for m in assets.IMPORT_RE.finditer(text):
            fails.append(f"{rel}: unstamped import ./{m[3]}")
        if re.search(r"\?v=\d{1,3}\b", text):
            fails.append(f"{rel}: a hand-numbered ?v= survived")
    html = _read("index.html")
    if not html.startswith("<!DOCTYPE html>\n<!-- Generated"):
        fails.append("index.html: the mark should follow the doctype")
    for want in ("<title>Leviticus Study</title>", "Book of Leviticus.",
                 '<div class="brand">Leviticus <span>'):
        if want not in html:
            fails.append(f"index.html lacks {want!r}")
    for link in ("css/core.css", "css/components.css", "css/division.css", "css/theme.css",
                 "app/main.js"):
        if not re.search(re.escape(link) + r"\?v=[0-9a-f]{10}\"", html):
            fails.append(f"index.html: {link} not hashed")
    for mod in ("threads.js", "spotlight.js", "search.js", "reader.js"):
        if not re.search(r'"\./' + re.escape(mod) + r'\?v=[0-9a-f]{10}"', _read("app/main.js")):
            fails.append(f"main.js: ./{mod} not hashed")
    return fails


def test_shell_is_idempotent_and_hashes_are_content():
    _assets()
    before = {rel: _read(rel) for rel in SHELL}
    fails = []
    if "up to date" not in _assets():
        fails.append("a second assets run wrote something")
    # a hash is the file's content: the link to a module names the module's hash
    js = {rel: _read(rel) for rel in SHELL if rel.endswith(".js")}
    main = js["app/main.js"]
    for rel, text in js.items():
        want = assets._hash(text)
        name = rel.split("/")[1]
        if name != "main.js" and f"./{name}?v={want}" not in main + js["app/search.js"]:
            fails.append(f"{name}'s hash in its importer isn't its content hash")
    if f"app/main.js?v={assets._hash(main)}" not in before["index.html"]:
        fails.append("index.html's main.js hash isn't main.js's content hash")
    # theme.css is the book's: editing it changes only its own link
    theme = os.path.join(_tmp, "css", "theme.css")
    old = support.read(theme)
    with open(theme, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n/* edit */\n")
    _assets()
    after = {rel: _read(rel) for rel in SHELL}
    changed = [r for r in SHELL if after[r] != before[r]]
    if changed != ["index.html"]:
        fails.append(f"a theme.css edit changed {changed}, want only index.html")
    diff = [(a, b) for a, b in zip(before["index.html"].splitlines(),
                                   after["index.html"].splitlines()) if a != b]
    if len(diff) != 1 or "css/theme.css?v=" not in diff[0][1]:
        fails.append(f"a theme.css edit changed index.html lines {diff}")
    with open(theme, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(old)
    _assets()
    return fails


def test_a_module_change_reaches_its_importers():
    """threads.js changes -> its own hash, search.js's and main.js's (they
    import it), and index.html's link to main.js; spotlight.js and reader.js
    keep theirs."""
    web = tempfile.mkdtemp(prefix="bc-web-")
    saved = assets.WEB
    try:
        shutil.copytree(os.path.join(saved, "app"), os.path.join(web, "app"))
        shutil.copyfile(os.path.join(saved, "index.html"), os.path.join(web, "index.html"))
        b = bookmod.book()
        assets.WEB = web
        before = assets.shell(b)
        with open(os.path.join(web, "app", "threads.js"), "a", encoding="utf-8",
                  newline="\n") as fh:
            fh.write("\n// changed\n")
        after = assets.shell(b)
    finally:
        assets.WEB = saved
        shutil.rmtree(web, ignore_errors=True)
    changed = sorted(r for r in before if before[r] != after[r])
    want = ["app/main.js", "app/search.js", "app/threads.js", "index.html"]
    return [] if changed == want else [f"threads.js change touched {changed}, want {want}"]


def test_single_file_css_gets_no_shell():
    """A book whose paths.css is one stylesheet keeps its own shell."""
    d = tempfile.mkdtemp(prefix="bc-shell1-")
    try:
        make_book(d, "Leviticus", "Lev", "leviticus")
        os.makedirs(os.path.join(d, "old"))
        shutil.copyfile(os.path.join(d, "css", "theme.css"), os.path.join(d, "old", "styles.css"))
        p = os.path.join(d, "book.json")
        cfg = json.load(open(p, encoding="utf-8"))
        cfg["paths"] = {"css": "old/styles.css"}
        json.dump(cfg, open(p, "w", encoding="utf-8"))
        bookmod.use(bookmod.Book.from_file(p))
        _assets()
        made = [x for x in ("index.html", "app") if os.path.exists(os.path.join(d, x))]
        return [f"shell written for a single-file css book: {made}"] if made else []
    finally:
        bookmod.use(bookmod.Book.from_file(os.path.join(_tmp, "book.json")))
        shutil.rmtree(d, ignore_errors=True)

