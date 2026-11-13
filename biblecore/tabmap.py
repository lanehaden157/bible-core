"""The shared tabernacle map: a to-scale top-down plan and a schematic camp.

Only a book that enables the `ritual` component gets it. `assets` writes
`data/tabmap.html` (this module's `sheet()`) and `app/tabmap.js` reads it.

Orientation: east (the gate) at the bottom, west (the Holy of Holies) at the
top, so a reader enters from below and goes up into holiness; north is on the
right (facing west). Units are cubits; the plan's x runs south(0) to north,
y runs west(0) to east. Everything the SVG draws comes from DIMENSIONS and the
constants below it, so the comments and the picture cannot drift apart.

Each DIMENSIONS row: (what, value, kind, source, note). kind is "text" (the
verse states it), "derived" (arithmetic on stated numbers) or "schematic" (the
text gives no position or size: drawn from Milgrom's Fig. 1 or by convention,
and said so). The verses win over the figure.
"""
from html import escape

# ---- the cubit data, each with its verse --------------------------------------
DIMENSIONS = [
    ("court length (south and north sides)", 100, "text", "Exod 27:9, 27:11", "hangings 100 cubits"),
    ("court width (west and east sides)", 50, "text", "Exod 27:12-13", "50 cubits"),
    ("hangings each side of the gate", 15, "text", "Exod 27:14-15", ""),
    ("gate (screen) width", 20, "text", "Exod 27:16", "centred on the east side: 15 + 20 + 15 = 50"),
    ("pillar spacing", 5, "derived", "Exod 27:10", "20 pillars along 100 cubits; the text gives the count, not the spacing"),
    ("altar of going up offerings, length and width", 5, "text", "Exod 27:1", "5 x 5 cubits, square"),
    ("Dwelling length", 30, "text", "Exod 26:16-18", "20 boards of 1.5 cubits on the south side (and north)"),
    ("Dwelling width", 10, "derived", "Exod 26:22-23", "six boards on the west plus two corner boards; the text gives boards, not the width, "
                                                         "so 10 is the usual reading (Milgrom Fig. 1)"),
    ("curtain: distance from the entrance of the Dwelling", 20, "text", "Exod 26:31-33",
     "hung under the clasps; two sets of five curtains, each 20 cubits wide (26:2, 26:9)"),
    ("holy of holies length", 10, "derived", "Exod 26:33", "30 - 20"),
    ("holy place length", 20, "derived", "Exod 26:33", "the curtain divides the Dwelling at 20 from the entrance"),
    ("Dwelling: distance from the court's west wall", 20, "schematic", "none", "Exod 27 does not place the Dwelling in the court; Milgrom Fig. 1 "
                                                                              "has the front at 50 cubits from the gate, so 20 behind"),
    ("altar: position", 28, "schematic", "Exod 40:6", "'before the entrance of the Dwelling'; no distance given; "
                                                      "Fig. 1 puts it on the axis, nearer the gate than the basin"),
    ("basin: position", 40, "schematic", "Exod 40:7, 30:18", "'between the Tent of Meeting and the altar'; size and distance not given"),
    ("basin: radius", 1.5, "schematic", "Exod 30:18", "the text gives no size"),
    ("curtain: drawn thickness", 1, "schematic", "none", "thickness not stated; drawn wide enough to tap"),
    ("ark", "2.5 x 1.5", "text", "Exod 25:10", "inside the curtain, Exod 26:33-34"),
    ("table", "2 x 1", "text", "Exod 25:23", "north side outside the curtain, Exod 26:35"),
    ("lampstand", "round (schematic)", "schematic", "Exod 25:31-40", "south side opposite the table, Exod 26:35"),
    ("incense altar", "1 x 1", "text", "Exod 30:1-2", "before the curtain, Exod 30:6"),
]

# ---- geometry -------------------------------------------------------------------
COURT_W, COURT_L, GATE = 50, 100, 20
DW_W, DW_L, DW_FRONT = 10, 30, 50          # front (east face) 50 cubits from the west wall
CURTAIN_FROM_ENTRANCE = 20
ALTAR = 5
ALTAR_Y, BASIN_Y, BASIN_R = COURT_L - 28, COURT_L - 40, 1.5
APRON = 4                                   # the entrance zone: schematic strip before the door
CAMP_M, OUT_M = 8, 6                        # margins drawn around the court
AX = COURT_W / 2                            # the axis

ZONES = ["outside-camp", "camp", "entrance", "court", "altar", "basin",
         "holy-place", "veil", "most-holy"]
LABELS = {"outside-camp": "outside the camp", "camp": "camp", "entrance": "entrance of the Tent of Meeting",
          "court": "court", "altar": "altar", "basin": "basin", "holy-place": "holy place",
          "veil": "curtain", "most-holy": "holy of holies"}
# holiness rank, 0 (outside) to 7 (innermost); shades the zones
RANK = {"outside-camp": 0, "camp": 1, "court": 2, "entrance": 3, "basin": 3, "altar": 4,
        "holy-place": 5, "veil": 6, "most-holy": 7}
WHO = ["offerer", "priest", "high-priest", "people"]

# who may enter (Lev 16, Num 18); zone -> who
ACCESS = [
    ("people", "the court, up to the altar", ["court", "entrance"],
     "Lev 1:3-5 (the offerer brings it to the entrance and slaughters it). "
     "Milgrom reads the limit as the altar (Fig. 8); the verses do not draw a line."),
    ("priests", "the altar, the basin and the holy place", ["altar", "basin", "holy-place"],
     "Exod 28:43; 30:19-20 (they wash at the basin first); Num 18:3-5, 7 (the altar is the priests' charge)."),
    ("high priest", "the holy of holies, once a year", ["veil", "most-holy"],
     "Lev 16:2-3, 16:34; Exod 30:10."),
]

# the camp (Num 2-3), schematic
TRIBES = {"east": ("Judah", "Issachar", "Zebulun"), "south": ("Reuben", "Simeon", "Gad"),
          "west": ("Ephraim", "Manasseh", "Benjamin"), "north": ("Dan", "Asher", "Naphtali")}
TRIBE_SRC = {"east": "Num 2:3-9", "south": "Num 2:10-16", "west": "Num 2:18-24", "north": "Num 2:25-31"}
LEVITES = {"east": ("Moses, Aaron and his sons", "Num 3:38"), "west": ("Gershon", "Num 3:23"),
           "south": ("Kohath", "Num 3:29"), "north": ("Merari", "Num 3:35")}


def _n(v):
    return f"{v:g}"


def _r(cls, x, y, w, h, zone=None, title=None, extra=""):
    z = f' data-zone="{zone}"' if zone else ""
    t = f"<title>{escape(title)}</title>" if title else ""
    return f'<rect class="{cls}"{z} x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}"{extra}>{t}</rect>'


def _t(x, y, text, cls="zl", anchor="start", rot=None):
    tr = f' transform="rotate({rot} {_n(x)} {_n(y)})"' if rot is not None else ""
    return f'<text class="{cls}" x="{_n(x)}" y="{_n(y)}" text-anchor="{anchor}"{tr}>{escape(text)}</text>'


def plan_svg():
    """The to-scale plan. Zone rectangles carry data-zone; labels don't take taps."""
    x0, y0 = -(CAMP_M + OUT_M), -(CAMP_M + OUT_M)
    w, h = COURT_W + 2 * (CAMP_M + OUT_M), COURT_L + 2 * (CAMP_M + OUT_M)
    dw_x = AX - DW_W / 2
    west_end = DW_FRONT - DW_L                   # y of the Dwelling's west wall (20)
    curtain_y = DW_FRONT - CURTAIN_FROM_ENTRANCE # y of the curtain (30)
    ct = 1
    o = [f'<svg class="tm-plan" viewBox="{_n(x0)} {_n(y0)} {_n(w)} {_n(h)}" xmlns="http://www.w3.org/2000/svg" '
         f'role="img" aria-label="Plan of the tabernacle court, to scale; east at the bottom">']
    o.append("<!-- Dimensions: see the table in the sheet; every figure is cited there (Exod 25-27, 30, 40). "
             "Court 100 x 50 (27:9-13), gate 20 (27:16), altar 5 x 5 (27:1), Dwelling 30 x 10 (26:16-18, 26:22-23), "
             "curtain at 20 from the entrance (26:31-33). Positions of the Dwelling, altar and basin are "
             "schematic (text silent; Milgrom Fig. 1, Exod 40:6-7). -->")
    o.append(_r("z", x0, y0, w, h, "outside-camp", LABELS["outside-camp"]))
    o.append(_r("z", -CAMP_M, -CAMP_M, COURT_W + 2 * CAMP_M, COURT_L + 2 * CAMP_M, "camp",
                "camp (Num 2-3; edge schematic)"))
    o.append(_r("z", 0, 0, COURT_W, COURT_L, "court", LABELS["court"]))
    # hangings with the gate gap; pillars every 5 cubits
    g0, g1 = (COURT_W - GATE) / 2, (COURT_W + GATE) / 2
    wall = [(0, 0, COURT_W, 0), (0, 0, 0, COURT_L), (COURT_W, 0, COURT_W, COURT_L),
            (0, COURT_L, g0, COURT_L), (g1, COURT_L, COURT_W, COURT_L)]
    for a, b, c, d in wall:
        o.append(f'<line class="wall" x1="{_n(a)}" y1="{_n(b)}" x2="{_n(c)}" y2="{_n(d)}"/>')
    for i in range(0, COURT_W + 1, 5):
        for yy in (0, COURT_L):
            if yy == COURT_L and g0 < i < g1:
                continue
            o.append(f'<circle class="post" cx="{i}" cy="{yy}" r=".55"/>')
    for j in range(5, COURT_L, 5):
        o.append(f'<circle class="post" cx="0" cy="{j}" r=".55"/><circle class="post" cx="{COURT_W}" cy="{j}" r=".55"/>')
    # the Dwelling
    o.append(_r("z", dw_x, curtain_y, DW_W, DW_FRONT - curtain_y, "holy-place", LABELS["holy-place"]))
    o.append(_r("z", dw_x, west_end, DW_W, curtain_y - west_end, "most-holy", LABELS["most-holy"]))
    o.append(_r("z", dw_x, curtain_y - ct / 2, DW_W, ct, "veil", LABELS["veil"]))
    o.append(_r("wall", dw_x, west_end, DW_W, DW_L, None, None, ' fill="none"'))
    o.append(_r("z", dw_x, DW_FRONT, DW_W, APRON, "entrance", LABELS["entrance"]))
    # furniture
    o.append(_r("f", AX - 1.25, west_end + 5 - 0.75, 2.5, 1.5, None, "ark of the covenant (Exod 25:10)"))
    o.append(_r("f", AX - 0.5, curtain_y + 2.5, 1, 1, None, "altar of incense (Exod 30:1-6)"))
    o.append(_r("f", AX + DW_W / 2 - 2, curtain_y + 6, 1, 2, None, "table (Exod 25:23; north side, 26:35)"))
    o.append(f'<circle class="f" cx="{_n(AX - DW_W / 2 + 2)}" cy="{_n(curtain_y + 7)}" r=".8"><title>lampstand (Exod 25:31; south side, 26:35)</title></circle>')
    o.append(f'<circle class="z" data-zone="basin" cx="{_n(AX)}" cy="{_n(BASIN_Y)}" r="{_n(BASIN_R)}"><title>{LABELS["basin"]}</title></circle>')
    o.append(_r("z", AX - ALTAR / 2, ALTAR_Y - ALTAR / 2, ALTAR, ALTAR, "altar", "altar of going up offerings (Exod 27:1)"))
    # labels (never on taps)
    lx = dw_x - 1.5
    o.append(_t(lx, west_end + 6, "holy of holies", anchor="end"))
    o.append(_t(lx, curtain_y + 0.7, "curtain", anchor="end"))
    o.append(_t(lx, curtain_y + 12, "holy place", anchor="end"))
    o.append(_t(dw_x + DW_W + 1.5, DW_FRONT + 3, "entrance", anchor="start"))
    o.append(_t(AX + ALTAR / 2 + 1.5, ALTAR_Y + 1, "altar"))
    o.append(_t(AX + BASIN_R + 1.5, BASIN_Y + 1, "basin"))
    o.append(_t(COURT_W - 1.5, COURT_L - 3, "court", anchor="end"))
    o.append(_t(g0 + GATE / 2, COURT_L + 3.6, "gate · 20 cubits", cls="zl sm", anchor="middle"))
    o.append(_t(x0 + 1.5, y0 + 3, "outside the camp", cls="zl sm"))
    o.append(_t(-CAMP_M + 1.5, -CAMP_M + 3, "camp", cls="zl sm"))
    o.append(_t(COURT_W + CAMP_M - 1, -CAMP_M + 3, "N →", cls="zl sm", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def camp_svg():
    """The camp, schematic, not to scale: Num 2 tribes by side, Num 3 clans."""
    o = ['<svg class="tm-camp" viewBox="0 0 120 150" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="The camp around the Dwelling; schematic, east at the bottom">']
    o.append("<!-- Schematic, not to scale. Tribes by side, Num 2:3-31 (three each). Levite clans, Num 3:23, 29, 35, 38 "
             "(Gershon west, Kohath south, Merari north, Moses, Aaron and his sons east). The Tent in the midst, "
             "Num 2:17. Distances are not stated (2:2 'at some distance'). -->")
    o.append(_r("z", 0, 0, 120, 150, "outside-camp", LABELS["outside-camp"]))
    o.append(_r("z", 4, 8, 112, 134, "camp", "camp"))
    o.append(_r("z", 48, 51, 24, 48, "court", "court and Dwelling (Num 2:17)"))
    o.append(_t(60, 75, "Dwelling", cls="zl sm", anchor="middle"))
    # Levites, inner ring
    o.append(_r("cb", 36, 31, 48, 10, None, f"Gershon, west (Num 3:23)"))
    o.append(_t(60, 38, "Gershon", cls="zl sm", anchor="middle"))
    o.append(_r("cb", 36, 109, 48, 10, None, "Moses, Aaron and his sons, east (Num 3:38)"))
    o.append(_t(60, 116, "Moses · Aaron · sons", cls="zl sm", anchor="middle"))
    o.append(_r("cb", 26, 44, 10, 62, None, "Kohath, south (Num 3:29)"))
    o.append(_t(33.6, 75, "Kohath", cls="zl sm", anchor="middle", rot=-90))
    o.append(_r("cb", 84, 44, 10, 62, None, "Merari, north (Num 3:35)"))
    o.append(_t(91.6, 75, "Merari", cls="zl sm", anchor="middle", rot=-90))
    # tribes, outer ring (read in Num 2's order along each side)
    for side, names in TRIBES.items():
        for i, nm in enumerate(names):
            if side in ("east", "west"):
                x, y = 22 + i * 26, (126 if side == "east" else 12)
                o.append(_r("cb", x, y, 24, 12, None, f"{nm} ({TRIBE_SRC[side]})"))
                o.append(_t(x + 12, y + 7.2, nm, cls="zl sm", anchor="middle"))
            else:
                x, y = (9 if side == "south" else 99), 30 + i * 30
                o.append(_r("cb", x, y, 12, 28, None, f"{nm} ({TRIBE_SRC[side]})"))
                o.append(_t(x + 7.4, y + 14, nm, cls="zl sm", anchor="middle", rot=-90))
    o.append(_t(6, 146, "outside the camp", cls="zl sm"))
    o.append(_t(114, 146, "N →", cls="zl sm", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def sheet():
    """The whole sheet fragment: layer tabs, both views, keys, sources."""
    rows = "".join(f"<tr><td>{escape(w)}</td><td>{escape(str(v))}</td><td>{k}</td><td>{escape(s)}</td><td>{escape(n)}</td></tr>"
                   for w, v, k, s, n in DIMENSIONS)
    enter = "".join(f'<li class="who-{escape(k.replace(" ", "-"))}"><b>{escape(k)}</b>: {escape(w)} <small>({escape(s)})</small></li>'
                    for k, w, _, s in ACCESS)
    camp = "".join(f"<li><b>{escape(side)}</b>: {escape(', '.join(names))} <small>({TRIBE_SRC[side]})</small>; "
                   f"{escape(LEVITES[side][0])} <small>({LEVITES[side][1]})</small></li>"
                   for side, names in TRIBES.items())
    return (
        '<div class="tm" data-layer="holy">\n'
        '<div class="tm-tabs" role="group" aria-label="Map layer">'
        '<button type="button" data-layer="holy" aria-pressed="true">Holiness</button>'
        '<button type="button" data-layer="enter" aria-pressed="false">Who may enter</button>'
        '<button type="button" data-layer="camp" aria-pressed="false">The camp</button></div>\n'
        + plan_svg() + "\n" + camp_svg() + "\n"
        '<p class="tm-cap tm-cap-holy">To scale from Exod 25-27; where the text gives no position the plan is '
        'schematic. In the holiness layer, darker is holier.</p>\n'
        f'<ul class="tm-key tm-key-enter">{enter}</ul>\n'
        '<p class="tm-cap tm-cap-camp">Not to scale. The Tent stands in the midst of the camp (Num 2:17).</p>\n'
        f'<ul class="tm-key tm-key-camp">{camp}</ul>\n'
        '<details class="tm-src"><summary>Measurements and where each comes from</summary>'
        '<table><thead><tr><th>what</th><th>cubits</th><th>kind</th><th>verse</th><th>note</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></details>\n</div>\n')
