"""The component registry (D5/D10/E13) and the poem, itin and textform
components, on a scratch book built from the template."""
import contextlib
import io
import json
import os
import shutil
import tempfile

import support
from template_book import make_book
from biblecore import assets, components, contract
from biblecore import book as bookmod
from biblecore import meta as um

_tmp = None
META = {"passage": "Numbers 6:22-27", "contract": "0.3.0"}


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-comp-")
    make_book(_tmp, "Numbers", "Num", "numbers")
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["components"] = ["echo", "list", "poem", "itin", "textform"]
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def test_registry_shape():
    reg = components.registry()
    fails = []
    if set(reg) != {"echo", "list", "poem", "itin", "textform"}:
        fails.append(f"registry has {sorted(reg)}")
    for c in reg.values():
        for f in ("style.css", "snippet.md", "__init__.py"):
            if not os.path.exists(os.path.join(c.folder, f)):
                fails.append(f"{c.name} lacks {f}")
        for cls in c.spec["classes"]:
            if f".{cls}" not in c.read("style.css"):
                fails.append(f"{c.name}: class {cls} has no rule in its style.css")
        contract.parse(c.spec["since"])
    return fails


def test_assets_written_and_whitelist_reads_them():
    _quiet(assets.main, [])
    fails = []
    for rel in ("css/core.css", "css/components.css", "data/components.json",
                "components-reference.md"):
        if not os.path.exists(os.path.join(_tmp, rel)):
            fails.append(f"{rel} not written")
    roles = {c["name"]: c["role"] for c in
             json.load(open(os.path.join(_tmp, "data", "components.json")))["components"]}
    if roles.get("textform") != "verse-aside" or roles.get("itin") != "inline-block":
        fails.append(f"roles {roles}")
    classes = um._css_classes()
    for cls in ("poem", "l", "itin", "stop", "textform", "list", "echo", "v", "gloss"):
        if cls not in classes:
            fails.append(f"class {cls} missing from css/")
    before = {f: support.read(os.path.join(_tmp, f)) for f in ("css/components.css",)}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assets.main([])
    if "up to date" not in out.getvalue() or support.read(os.path.join(_tmp, "css/components.css")) != before["css/components.css"]:
        fails.append("assets isn't idempotent")
    return fails


def test_disabled_component_is_named():
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["components"] = ["echo"]
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))
    _quiet(assets.main, [])
    errs = um.check_component_whitelist('<div class="poem"><section class="block legend"></section></div>')
    if not any("'poem' component" in e and "doesn't enable" in e for e in errs):
        return [f"disabled component not named: {errs}"]


POEM_OK = ('<div class="poem">'
           '<div class="v"><span class="n">24</span><span class="l">May Yahweh bless you</span>'
           '<span class="l in">and keep you.</span></div>'
           '<span class="gloss">g</span>'
           '<div class="v"><span class="n">25</span><span class="l" data-pair="A">May Yahweh shine</span>'
           '<span class="l in" data-pair="B">and be gracious.<sup class="en"><a href="#n1">1</a></sup></span></div>'
           '</div>')


def test_poem():
    chk = components.registry()["poem"].check
    fails = []
    if chk(POEM_OK, META):
        fails.append(f"good poem rejected: {chk(POEM_OK, META)}")
    bad = {
        "stray text": POEM_OK.replace('<span class="l">May Yahweh bless you</span>', 'May Yahweh bless you'),
        "no lines": '<div class="poem"><div class="v"><span class="n">1</span> text</div></div>',
        "line outside poem": '<p class="v"><span class="n">1</span><span class="l">x</span></p>',
        "nested poem": '<div class="poem"><div class="poem"></div></div>',
        "bad class": POEM_OK.replace('class="l in"', 'class="l big"', 1),
        "bad pair": POEM_OK.replace('data-pair="A"', 'data-pair="first"'),
        "in a block": '<section class="block">' + POEM_OK + '</section>',
        "foreign child": POEM_OK.replace('<span class="gloss">g</span>', '<h3 class="pericope">x</h3>'),
    }
    for name, html in bad.items():
        if not chk(html, META):
            fails.append(f"poem check missed: {name}")
    return fails


def test_poem_verses_still_audit_as_verses():
    """A poem is ordinary verse blocks: the verse regexes see both verses."""
    from biblecore import audit
    found = [m.group(0) for m in audit.VBLOCK.finditer(POEM_OK)]
    if len(found) != 2:
        return [f"audit sees {len(found)} verse blocks in a two-verse poem"]


ITIN_OK = ('<section class="block"><h2>Stations</h2><div class="itin" data-verses="33:5-6">'
           '<span class="stop"><span class="r" data-root="x">Rameses</span> <sup>33:5</sup></span>'
           '<span class="arr">→</span><span class="stop">Sukkot <sup>33:5</sup></span>'
           '</div></section>')


def test_itin():
    chk = components.registry()["itin"].check
    fails = []
    if chk(ITIN_OK, META):
        fails.append(f"good itin rejected: {chk(ITIN_OK, META)}")
    bad = {
        "outside block": ITIN_OK.replace('<section class="block"><h2>Stations</h2>', '').replace('</section>', ''),
        "ends on arrow": ITIN_OK.replace('</div></section>', '<span class="arr">→</span></div></section>'),
        "two stops": ITIN_OK.replace('<span class="arr">→</span>', ''),
        "bad sup": ITIN_OK.replace('<sup>33:5</sup></span>\n', '').replace('<sup>33:5</sup>', '<sup>five</sup>', 1),
        "stray child": ITIN_OK.replace('<span class="arr">→</span>', '<b>→</b>'),
        "empty stop": ITIN_OK.replace('Sukkot <sup>33:5</sup>', ''),
    }
    for name, html in bad.items():
        if not chk(html, META):
            fails.append(f"itin check missed: {name}")
    return fails


def test_textform():
    chk = components.registry()["textform"].check
    html = ('<p class="v"><span class="n">6:24</span> t.</p>'
            '<aside class="textform" data-anchor="6:24" data-src="lxx">lacks x.</aside>')
    fails = []
    if chk(html, META):
        fails.append(f"good textform rejected: {chk(html, META)}")
    for name, h in {
        "no src": html.replace(' data-src="lxx"', ''),
        "unknown src": html.replace('lxx', 'nets'),
        "wrong anchor": html.replace('data-anchor="6:24"', 'data-anchor="6:25"'),
    }.items():
        if not chk(h, META):
            fails.append(f"textform check missed: {name}")
    return fails


def test_new_components_skip_older_contracts():
    """poem/itin/textform arrived in 0.3.0: a 0.2.0 unit isn't held to them."""
    bad = '<div class="poem"><div class="v"><span class="n">1</span> text</div></div>'
    old = components.check(bad, {"passage": "Numbers 1:1-2"}, "0.2.0")
    new = components.check(bad, {"passage": "Numbers 1:1-2"}, "0.3.0")
    if old or not new:
        return [f"gating wrong: 0.2.0 -> {old}, 0.3.0 -> {new}"]
