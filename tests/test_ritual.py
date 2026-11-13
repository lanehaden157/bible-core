"""The tabernacle map (biblecore/tabmap.py) and the `ritual` component: the
geometry against Exod 25-27 and 26, the zone list, the strip check, the sample
Lev 1 and Lev 16 strips, and the opt-in (a book without `ritual` gets no map
code at all)."""
import contextlib
import io
import json
import os
import re
import shutil
import tempfile

import support
from template_book import make_book
import ritual_sample as rs
from biblecore import assets, components, tabmap
from biblecore import book as bookmod

_tmp = None
META = {"passage": "Leviticus 1:1–17", "contract": "0.31.0"}
TERMS_NOT = ["burnt offering", "atonement", "atone", "veil", "laver", "purification offering",
             "mercy seat", "Holy of Holies", "Most Holy", "holocaust"]


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-ritual-")
    make_book(_tmp, "Leviticus", "Lev", "leviticus")
    p = os.path.join(_tmp, "book.json")
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["components"] = ["echo", "list", "ritual"]
    json.dump(cfg, open(p, "w", encoding="utf-8"))
    bookmod.use(bookmod.Book.from_file(p))


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def _rects(svg):
    out = {}
    for m in re.finditer(r'<rect class="[^"]*" data-zone="([\w-]+)" x="([-\d.]+)" y="([-\d.]+)" '
                         r'width="([-\d.]+)" height="([-\d.]+)"', svg):
        out.setdefault(m.group(1), []).append(tuple(float(g) for g in m.groups()[1:]))
    return out


def test_plan_matches_exodus():
    svg = tabmap.plan_svg()
    z = _rects(svg)
    fails = []
    court = z["court"][0]
    if (court[2], court[3]) != (50, 100):
        fails.append(f"court is {court[2]} x {court[3]}, Exod 27:9-13 says 50 x 100")
    altar = z["altar"][0]
    if (altar[2], altar[3]) != (5, 5):
        fails.append(f"altar {altar[2]} x {altar[3]}, Exod 27:1 says 5 x 5")
    holy, most, veil = z["holy-place"][0], z["most-holy"][0], z["veil"][0]
    if (holy[2], holy[3] + most[3]) != (10, 30):
        fails.append(f"Dwelling is {holy[2]} x {holy[3] + most[3]}; Exod 26:16-18 gives 30 long")
    if most[3] != 10 or holy[3] != 20:
        fails.append(f"holy place {holy[3]} / holy of holies {most[3]}, expected 20 / 10")
    # the curtain sits 20 cubits from the entrance of the Dwelling (26:31-33)
    door = holy[1] + holy[3]
    curtain_mid = veil[1] + veil[3] / 2
    if door - curtain_mid != 20:
        fails.append(f"curtain is {door - curtain_mid} cubits from the entrance, Exod 26:33 says 20")
    # the gate: the east wall has a gap of 20, centred (15 + 20 + 15, 27:14-16)
    lines = re.findall(r'<line class="wall" x1="([-\d.]+)" y1="100" x2="([-\d.]+)" y2="100"/>', svg)
    segs = sorted((float(a), float(b)) for a, b in lines)
    if len(segs) != 2 or segs[1][0] - segs[0][1] != 20 or segs[0][1] != 15 or segs[1][1] != 50:
        fails.append(f"gate segments {segs}: want 15 + 20 + 15")
    # centred axis; altar and basin on it, order from the gate: altar, basin, Dwelling (Exod 40:6-7)
    cx = lambda r: r[0] + r[2] / 2
    if not (cx(altar) == cx(holy) == 25):
        fails.append("altar and Dwelling are not on the court's axis")
    basin = re.search(r'data-zone="basin" cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg)
    by = float(basin.group(2))
    if not (altar[1] + altar[3] / 2 > by > door):
        fails.append("basin is not between the altar and the Dwelling (Exod 40:7)")
    return fails


def test_zones_and_labels():
    fails = []
    both = tabmap.plan_svg() + tabmap.camp_svg()
    drawn = set(re.findall(r'data-zone="([\w-]+)"', both))
    if drawn != set(tabmap.ZONES):
        fails.append(f"drawn zones {sorted(drawn)} != ZONES")
    if tabmap.ZONES != ["outside-camp", "camp", "entrance", "court", "altar", "basin",
                        "holy-place", "veil", "most-holy"]:
        fails.append("zone ids changed")
    if re.search(r'\bid="', both):
        fails.append("the SVG carries ids; copies of it sit on one page")
    sheet = tabmap.sheet()
    for word in ("curtain", "holy of holies", "basin", "holy place", "altar", "court",
                 "entrance of the Tent of Meeting"):
        if word not in sheet:
            fails.append(f"label '{word}' missing")
    words = re.sub(r'data-(zone|at)="[\w-]+"', "", sheet)   # zone ids keep `veil`
    for bad in TERMS_NOT:
        if re.search(bad, words):
            fails.append(f"the map uses '{bad}', not a decided term")
    for what, v, kind, src, note in tabmap.DIMENSIONS:
        if kind not in ("text", "derived", "schematic"):
            fails.append(f"{what}: kind {kind}")
        if kind != "schematic" and not re.search(r"\d+:\d+", src):
            fails.append(f"{what}: no verse cited")
        if kind == "schematic" and not note:
            fails.append(f"{what}: a schematic item must say why")
    return fails


def test_camp_layer_from_numbers():
    svg = tabmap.camp_svg()
    fails = []
    for name in ("Judah", "Reuben", "Ephraim", "Dan", "Gershon", "Kohath", "Merari", "Moses"):
        if name not in svg:
            fails.append(f"{name} missing from the camp")
    sides = {s: n for s, n in tabmap.TRIBES.items()}
    if sides["east"][0] != "Judah" or sides["south"][0] != "Reuben" or sides["west"][0] != "Ephraim" \
            or sides["north"][0] != "Dan" or sum(len(v) for v in sides.values()) != 12:
        fails.append(f"tribes by side wrong: {sides}")
    if tabmap.LEVITES["west"][0] != "Gershon" or tabmap.LEVITES["south"][0] != "Kohath" \
            or tabmap.LEVITES["north"][0] != "Merari" or "Moses" not in tabmap.LEVITES["east"][0]:
        fails.append("Levite clans misplaced (Num 3:23, 29, 35, 38)")
    return fails


def test_samples_pass_check_and_follow_the_verses():
    comp = components.registry()["ritual"]
    fails = []
    for label, steps, html in (("Lev 1", rs.LEV1, rs.lev1()), ("Lev 16", rs.LEV16, rs.lev16())):
        errs = comp.check(html, META)
        if errs:
            fails.append(f"{label}: {errs}")
        order = [tuple(int(x) for x in re.findall(r"\d+", v)[:2]) for v, *_ in steps]
        if order != sorted(order):
            fails.append(f"{label}: steps are out of verse order {order}")
        for v, who, at, text in steps:
            for bad in TERMS_NOT:
                if re.search(bad, text, re.I):
                    fails.append(f"{label} {v}: '{bad}' is not a decided term")
        if html.count("<li ") != len(steps):
            fails.append(f"{label}: step count")
    # facts straight from the verses
    def at(steps, v, who=None):
        return [a for vv, w, a, _ in steps if vv == v and (who is None or w == who)]
    if at(rs.LEV1, "1:5", "priest") != ["altar"] or at(rs.LEV1, "1:9", "priest") != ["altar"]:
        fails.append("Lev 1:5, 1:9: the priest's acts are at the altar")
    if at(rs.LEV16, "16:12–13") != ["most-holy"] or at(rs.LEV16, "16:14") != ["most-holy"]:
        fails.append("Lev 16:12-14 happen inside the curtain")
    if at(rs.LEV16, "16:16", "high-priest") != ["most-holy", "holy-place"]:
        fails.append("Lev 16:16: the holy place, then the Tent of Meeting")
    if any(w != "high-priest" for v, w, a, _ in rs.LEV16 if a == "most-holy"):
        fails.append("only the high priest enters the holy of holies (16:2, 16:17)")
    if [a for v, w, a, _ in rs.LEV16 if v == "16:21–22"] != ["outside-camp"]:
        fails.append("the goat for Azazel goes out of the camp")
    return fails


def test_check_rejects_bad_steps():
    comp = components.registry()["ritual"]
    ok = rs.lev1()
    bad = {
        "who": ok.replace('data-who="priest"', 'data-who="levite"', 1),
        "zone": ok.replace('data-at="altar"', 'data-at="laver"', 1),
        "no at": ok.replace(' data-at="entrance"', '', 1),
        "no verse": ok.replace("<sup>1:3</sup>", "", 1),
        "bad verse": ok.replace("<sup>1:3</sup>", "<sup>v3</sup>", 1),
        "no list": re.sub(r"<ol.*</ol>", "", ok, flags=re.S),
        "class": ok.replace('class="block ritual"', 'class="ritual"', 1),
        "marker": '<div class="tabmap" data-layer="east">x</div>',
        "marker zone": '<div class="tabmap" data-at="laver"></div>',
    }
    fails = []
    for name, html in bad.items():
        if not comp.check(html, META):
            fails.append(f"'{name}' passed the check")
    if comp.check('<div class="tabmap" data-layer="camp" data-at="camp"></div>', META):
        fails.append("a good tabmap marker failed")
    return fails


def test_sample_validates_as_a_fragment():
    """A fragment holding the strip passes the whole fragment check with the
    declared verses honoured (core's own validate)."""
    from biblecore import meta as um
    frag = ('<article class="unit" data-unit="1">\n<script type="application/json" id="unit-meta">\n'
            + json.dumps({"unit": 1, "passage": "Leviticus 1:3–9", "title": "t", "roots": [],
                          "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
                          "contract": "0.31.0"}) + "\n</script>\n" + rs.lev1() + "</article>\n")
    errs = components.check(frag, {"passage": "Leviticus 1:3–9"}, "0.31.0")
    errs += um.check_declared_verses(frag, {"passage": "Leviticus 1:3–9"})
    return errs


def test_assets_write_the_map_only_when_enabled():
    _quiet(assets.main, [])
    fails = []
    b = bookmod.book()
    for rel in ("data/tabmap.html", "app/tabmap.js"):
        if not os.path.exists(os.path.join(_tmp, rel)):
            fails.append(f"{rel} not written for a book enabling ritual")
    main = support.read(os.path.join(_tmp, "app", "main.js"))
    if "tabmap.mount(content)" not in main or "//ritual:" in main:
        fails.append("main.js lacks the map hook, or kept a marker line")
    if "ritual" not in support.read(os.path.join(_tmp, "css", "components.css")):
        fails.append("components.css lacks the ritual rules")
    # and a book that doesn't enable it
    other = tempfile.mkdtemp(prefix="bc-ritual-off-")
    try:
        make_book(other, "Numbers", "Num", "numbers")
        bo = bookmod.Book.from_file(os.path.join(other, "book.json"))
        shell = assets.shell(bo)
        if "app/tabmap.js" in shell:
            fails.append("a book without ritual got app/tabmap.js")
        for rel, text in shell.items():
            if re.search(r"tabmap|ritual", text, re.I):
                fails.append(f"{rel} mentions the map in a book without ritual")
        gen = assets.generated(bo)
        if any(re.search(r"\.tm\b|ritual", t) for k, t in gen.items() if k.endswith(".css")):
            fails.append("css for a book without ritual carries map rules")
    finally:
        shutil.rmtree(other, ignore_errors=True)
        bookmod.use(b)
    return fails


def test_shell_text_is_unchanged_by_the_markers():
    """Stripping the ritual markers gives the source with those lines removed,
    so a book without the component builds the shell it built before."""
    src = open(os.path.join(support.CORE, "biblecore", "web", "app", "main.js"), encoding="utf-8").read()
    gone = assets.ritual_text(src, False)
    kept = assets.ritual_text(src, True)
    fails = []
    if "tabmap" in gone or "//ritual" in gone:
        fails.append("the off text still has map code")
    if "tabmap.mount" not in kept or "//ritual" in kept:
        fails.append("the on text lacks the hook or a marker")
    if gone.replace("\n", "") + "" == kept.replace("\n", ""):
        fails.append("on and off are the same")
    return fails
