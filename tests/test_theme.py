"""theme.py: division.css from web/themes.json (division themes)."""
import json
import os
import shutil
import tempfile

import support
from template_book import make_book
from biblecore import book as bookmod
from biblecore import theme

_tmp = None


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-theme-")
    make_book(_tmp, "Numbers", "Num", "numbers")
    bookmod.use(bookmod.Book.from_file(os.path.join(_tmp, "book.json")))


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def test_every_book_resolves_with_an_emblem():
    t = theme.themes()
    fails = []
    for osis, e in t["books"].items():
        if e["division"] not in t["divisions"]:
            fails.append(f"{osis}: unknown division {e['division']}")
        if not theme.emblem_svg(e.get("emblem")):
            fails.append(f"{osis}: no emblem file for {e.get('emblem')!r}")
    return fails


def test_numbers_division_css():
    css = theme.build_css(bookmod.book())
    fails = []
    for want in ("fonts.googleapis.com", "EB+Garamond", "--bg: #efe6d2", "--book-primary: #b8783a",
                 ':root[data-theme="dark"]', "prefers-color-scheme: dark", "mask:", ".unit .notes::before",
                 "--rc-shown"):
        if want not in css:
            fails.append(f"missing {want!r}")
    return fails


def test_text_colours_read_on_their_paper():
    """Every accent token, light and dark, meets the contrast floor on its ground."""
    t = theme.themes()
    fails = []
    for osis, e in t["books"].items():
        div = dict(t["divisions"][e["division"]], id=e["division"])
        for dark in (False, True):
            tok = theme._palette(div, e, dark)
            for k in ("--accent-clay", "--accent-bronze", "--accent-jordan", "--ink"):
                c = theme.contrast(tok[k], tok["--bg"])
                if c < 3.5:
                    fails.append(f"{osis} {'dark' if dark else 'light'} {k} {tok[k]} on {tok['--bg']}: {c:.2f}")
            # the interlinear gloss is small text on the word box's panel
            c = theme.contrast(tok["--gloss"], tok["--panel"])
            if c < 4.5:
                fails.append(f"{osis} {'dark' if dark else 'light'} --gloss {tok['--gloss']} "
                             f"on --panel {tok['--panel']}: {c:.2f}")
            if theme.contrast(tok["--mast-fg"], e["primary"]) < 3:
                fails.append(f"{osis}: masthead text {tok['--mast-fg']} on {e['primary']}")
    return fails[:10]


def test_book_json_overrides_and_no_theme():
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["theme"] = {"primary": "#123456", "emblem": "fish"}
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    b = bookmod.use(bookmod.Book.from_file(p))
    css = theme.build_css(b)
    fails = [] if "--book-primary: #123456" in css else ["book.json theme.primary ignored"]
    cfg["osis"], cfg["theme"] = "Obad", {}
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    if theme.build_css(bookmod.use(bookmod.Book.from_file(p))) is not None:
        fails.append("a book with no division should get no division.css")
    return fails
