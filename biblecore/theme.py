"""The book's division theme -> css/division.css (plan: division themes).

    python -m biblecore assets     # writes it, with the other shared assets

A division (Torah, Former Prophets, Later Prophets, Writings, New
Testament) sets paper, ink, three signature colours and two typefaces; a
book sets an accent pair and an emblem. Both come from web/themes.json,
keyed by the book's OSIS id; book.json "theme" overrides any part:
{"division": "torah", "primary": "#…", "secondary": "#…", "emblem": "tree"}.

division.css carries, in this order:
  - the division's Google Fonts @import;
  - light tokens on :root: the same names core.css already uses (--bg,
    --ink, --accent-clay, --display, …), all derived from paper/ink/accents,
    with text-role colours darkened until they read on the paper;
  - dark tokens, active for `html[data-theme="dark"]`, or for "auto" when the
    system prefers dark. A page with no data-theme (a site whose app doesn't
    set it) stays light;
  - the banner masthead: book colour band, emblem in a circle (CSS mask
    over an inlined SVG, so nothing extra to publish);
  - the division's ornament in place of the straight rules inside a unit:
    full width above the notes, and cut in three (mini_ornament) under
    each section heading and between the colour key's groups, where the
    motif keeps its size and the rules stretch to the heading's width (Lane,
    2026-09-26: "ornaments used more ... instead of those straight lines");
  - tracked-word colours lifted toward white in dark mode (threads.js sets
    --rc; see core.css).

Tracked-word colours are never taken from the accents (ARCHITECTURE §2).
Returns None when the book has no theme entry: core.css's defaults apply.
"""
import json
import os
import urllib.parse

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

FONT_AXES = {
    "Cinzel": "wght@400;500;600",
    "EB Garamond": "ital,wght@0,400;0,500;0,600;1,400;1,500",
    "Crimson Pro": "ital,wght@0,400;0,500;0,600;1,400;1,500",
    "Marcellus": None,
    "Spectral": "ital,wght@0,400;0,500;0,600;1,400;1,500",
    "Cormorant Garamond": "ital,wght@0,400;0,500;0,600;1,400;1,500",
    "Uncial Antiqua": None,
    "Source Serif 4": "ital,wght@0,400;0,500;0,600;1,400;1,500",
}


# ------------------------------------------------------------------ colour

def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def mix(a, b, t):
    """a moved t of the way toward b (0 = a, 1 = b)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable(c, ground, toward, need=3.6):
    """c, moved toward `toward` in small steps until it reads on `ground`."""
    t = 0.0
    out = c
    while contrast(out, ground) < need and t < 1:
        t += 0.05
        out = mix(c, toward, t)
    return out


def _rgba(h, a):
    r, g, b = _rgb(h)
    return f"rgba({r}, {g}, {b}, {a})"


# ------------------------------------------------------------------ data

def themes():
    with open(os.path.join(HERE, "themes.json"), encoding="utf-8") as fh:
        return json.load(fh)


def resolve(b):
    """(division, book) dicts for this book, book.json overrides applied;
    None if neither themes.json nor book.json names a division."""
    t = themes()
    entry = dict(t["books"].get(b.osis, {}))
    entry.update(b.cfg.get("theme") or {})
    div_id = entry.get("division")
    if not div_id or div_id not in t["divisions"]:
        return None
    entry.setdefault("primary", t["divisions"][div_id]["signature"][0])
    entry.setdefault("secondary", t["divisions"][div_id]["signature"][1])
    return dict(t["divisions"][div_id], id=div_id), entry


def emblem_svg(name):
    p = os.path.join(HERE, "emblems", f"{name}.svg")
    return open(p, encoding="utf-8").read().strip() if name and os.path.exists(p) else None


ORN_FAR = -600    # the drawn rule runs this far left: headings up to ~1200px never run out
MOTIF = (250, 350)  # the centre cut: the motif and a little rule either side


def _wave(x0, step, dx, ys, until, taper):
    """A smooth wave from x0 in `step`-wide segments (y 9, controls
    alternating between ys), stopping at `until`, then the taper segment."""
    d = f"M{x0} 9C{x0 + step - dx} {ys[0]} {x0 + dx} {ys[1]} {x0 + step} 9"
    x, i = x0 + step, 1
    while x < until:
        d += f"S{x + dx} {ys[i % 2 == 0]} {x + step} 9"
        x, i = x + step, i + 1
    return d + taper


def mini_ornament(svg):
    """The heading ornament, as three cuts of the same drawing: a long left
    rule (anchored at its right end), the centre motif, a long right rule
    (anchored at its left end). Laid side by side as CSS background layers,
    the rules stretch to any width while the motif keeps its size."""
    far = 300 - ORN_FAR
    a, b = MOTIF
    return (svg.replace('viewBox="0 0 600 18" preserveAspectRatio="xMidYMid meet"',
                        f'viewBox="{ORN_FAR} 0 {a - ORN_FAR} 18" preserveAspectRatio="xMaxYMid slice"'),
            svg.replace('viewBox="0 0 600 18"', f'viewBox="{a} 0 {b - a} 18"'),
            svg.replace('viewBox="0 0 600 18" preserveAspectRatio="xMidYMid meet"',
                        f'viewBox="{b} 0 {600 + far - b} 18" preserveAspectRatio="xMinYMid slice"'))


def _data_uri(svg):
    # '#' (colours) and quotes must be escaped inside a CSS url("…")
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="=:/,.()-")


def ornament_svg(div_id, sig, ink, full=True):
    """A thin section rule in the division's own idiom, 600x18. Each division
    draws its left half (running out to ORN_FAR) and a centre motif; the right
    half is the left mirrored about x=300, so the rule is always symmetric.
    full=False is the drawing the heading cuts are taken from."""
    a, b, c = sig
    w = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 18" preserveAspectRatio="xMidYMid meet" fill="none" stroke-linecap="round"'
    F = ORN_FAR
    ends = ""
    if div_id == "torah":
        half = (f'<path d="{_wave(F, 75, 25, (3, 15), 225, "S262 4 280 9")}" stroke="{a}" stroke-width="1"/>'
                f'<path d="{_wave(F, 75, 25, (15, 3), 225, "S262 14 280 9")}" stroke="{c}" stroke-width="1"/>')
        motif = f'<path d="M300 2L307 9L300 16L293 9Z" stroke="{b}" stroke-width="1"/>'
    elif div_id == "former":
        joints = "".join(f"M{x} 3V9" for x in range(F + 20, 280, 40))
        joints += "".join(f"M{x} 9V15" for x in range(F + 40, 280, 40))
        half = f'<path d="M{F} 3H280M{F} 9H280M{F} 15H280{joints}" stroke="{b}" stroke-width=".8"/>'
        motif = f'<path d="M290 2H310L306.5 16H293.5Z" stroke="{a}" stroke-width="1"/>'
    elif div_id == "latter":
        half = (f'<path d="M{F} 11H252" stroke="{b}" stroke-width="1"/>'
                f'<g fill="{a}"><circle cx="262" cy="10.5" r="1.2"/><circle cx="272" cy="8" r=".9"/></g>')
        motif = f'<path d="M300 16C293.5 13 296.5 7 300 1.5C303.5 7 306.5 13 300 16Z" stroke="{a}" stroke-width="1"/>'
    elif div_id == "writings":
        leaves = "".join(f'<path d="M{x} 7C{x + 3} 2.5 {x + 8} 2.5 {x + 10} 4C{x + 7} 7 {x + 3} 8 {x} 7Z"/>'
                         f'<path d="M{x + 100} 11C{x + 103} 15.5 {x + 108} 15.5 {x + 110} 14C{x + 107} 11 {x + 103} 10 {x + 100} 11Z"/>'
                         for x in range(F + 60, 200, 200))
        half = (f'<path d="{_wave(F, 100, 60, (3, 15), 200, "S250 14 278 9")}" stroke="{a}" stroke-width="1"/>'
                f'<g stroke="{b}" stroke-width="1">{leaves}</g>')
        motif = f'<path d="M292 16C289 10 290.5 3.5 295 3M308 16C311 10 309.5 3.5 305 3M293.5 16H306.5M296.5 5V15M300 4.5V15.5M303.5 5V15" stroke="{c}" stroke-width="1"/>'
    else:  # nt: scroll ends, three dots at the centre
        half = f'<path d="M{14 if full else F} 9H286" stroke="{ink}" stroke-width=".9"/>'
        motif = f'<g fill="{a}"><circle cx="292" cy="9" r="1.4"/><circle cx="300" cy="9" r="1.8"/><circle cx="308" cy="9" r="1.4"/></g>'
        # the scroll's two ends turn opposite ways, as a scroll's do; only the
        # full ornament has them (the heading cuts run on instead)
        ends = (f'<path d="M14 9C8.5 9 5 5.5 7 2.5C9 .5 13 1.5 13 5C13 7.4 10 7.4 10 5.6" stroke="{ink}" stroke-width=".9"/>'
                f'<path d="M586 9C591.5 9 595 12.5 593 15.5C591 17.5 587 16.5 587 13C587 10.6 590 10.6 590 12.4" stroke="{ink}" stroke-width=".9"/>') if full else ""
    return f'<svg {w}>{half}<g transform="matrix(-1 0 0 1 600 0)">{half}</g>{motif}{ends}</svg>'


# ------------------------------------------------------------------ tokens

def _palette(div, book, dark):
    paper, ink = div["paper"], div["ink"]
    sig = div["signature"]
    if not dark:
        bg, fg = paper, ink
        tokens = {
            "--bg": bg, "--panel": mix(paper, "#ffffff", .45), "--panel-2": mix(paper, ink, .10),
            "--ink": fg, "--ink-soft": mix(ink, paper, .38),
            "--rule": mix(paper, ink, .25), "--rule-soft": mix(paper, ink, .14),
            "--glow-1": mix(paper, "#ffffff", .55), "--glow-2": mix(paper, ink, .15),
        }
    else:
        bg = mix(ink, "#000000", .25)
        fg = mix(paper, "#ffffff", .15)
        tokens = {
            "--bg": bg, "--panel": mix(bg, paper, .07), "--panel-2": mix(bg, paper, .13),
            "--ink": fg, "--ink-soft": mix(paper, bg, .38),
            "--rule": mix(bg, paper, .28), "--rule-soft": mix(bg, paper, .16),
            "--glow-1": mix(bg, paper, .05), "--glow-2": mix(bg, book["primary"], .14),
        }
    toward = ink if not dark else paper
    p, s = book["primary"], book["secondary"]
    tokens.update({
        "--accent-clay": readable(p, bg, toward),
        "--accent-bronze": readable(s, bg, toward),
        "--accent-jordan": readable(sig[0], bg, toward),
        "--accent-olive": readable(sig[1], bg, toward),
        "--accent-wine": readable(sig[2], bg, toward),
        "--topbar-bg": _rgba(bg, .94),
        "--root-active-bg": _rgba(s, .16),
        "--flash": mix(s, bg, .5),
        "--book-primary": p, "--book-secondary": s,
        "--mast-fg": paper if contrast(paper, p) >= contrast(ink, p) else ink,
        "--emblem-fg": paper if contrast(paper, s) >= contrast(ink, s) else ink,
    })
    return tokens


def _block(sel, tokens):
    return sel + " {\n" + "".join(f"  {k}: {v};\n" for k, v in tokens.items()) + "}\n"


def build_css(b):
    r = resolve(b)
    if r is None:
        return None
    div, book = r
    fonts = []
    title = div.get("title", div["display"])
    for f in dict.fromkeys([title, div["display"], div["text"]]):
        axes = FONT_AXES.get(f)
        fonts.append("family=" + f.replace(" ", "+") + (f":{axes}" if axes else ""))
    light = _palette(div, book, False)
    dark = _palette(div, book, True)
    for tok in (light, dark):
        tok["--display"] = f'"{div["display"]}", Georgia, serif'
        tok["--serif"] = f'"{div["text"]}", Georgia, "Times New Roman", serif'
        # a decorative face (the NT's uncials) goes on the masthead title only
        tok["--title"] = f'"{title}", Georgia, serif'
    emblem = emblem_svg(book.get("emblem"))
    orn_light = ornament_svg(div["id"], div["signature"], div["ink"])
    orn_dark = ornament_svg(div["id"], [readable(c, dark["--bg"], div["paper"]) for c in div["signature"]],
                            dark["--ink-soft"])
    dark_sig = [readable(c, dark["--bg"], div["paper"]) for c in div["signature"]]
    cuts_l = mini_ornament(ornament_svg(div["id"], div["signature"], div["ink"], full=False))
    cuts_d = mini_ornament(ornament_svg(div["id"], dark_sig, dark["--ink-soft"], full=False))
    out = [
        f"@import url('https://fonts.googleapis.com/css2?{'&'.join(fonts)}&display=swap');\n",
        f"/* division.css -- GENERATED by `python -m biblecore build` from bible-core\n"
        f"   web/themes.json: {div['label']} ({div.get('motif', '')}), book accents "
        f"'{book.get('name', b.name)}'. Don't edit; override in theme.css or book.json \"theme\". */\n\n",
        # color-scheme, so native parts (scrollbars, form controls) follow the theme
        _block(":root", {**light, "color-scheme": "light"}), "\n",
        _block(':root[data-theme="dark"]', {**dark, "color-scheme": "dark"}),
        "@media (prefers-color-scheme: dark) {\n"
        + _block('  :root[data-theme="auto"]', {**dark, "color-scheme": "dark"}).replace("\n  ", "\n    ") + "}\n\n",
        """/* the banner masthead: the book's colour, its emblem in a circle */
.unit .mast {
  position: relative; text-align: left;
  background: var(--book-primary); color: var(--mast-fg);
  border: none; border-radius: 8px; border-bottom: 4px solid var(--book-secondary);
  padding: 20px 104px 18px 24px; margin: 0 0 18px;
}
.unit .mast .kicker, .unit .mast .unit, .unit .mast .unit-place, .unit .mast .greek-title,
.unit .mast h1 { color: var(--mast-fg); }
.unit .mast .kicker { opacity: .85; }
.unit .mast h1 { margin: .12em 0 .1em; font-family: var(--title); }
.unit .mast .unit-place { border-color: currentColor; }
""",
    ]
    if emblem:
        out.append(
            ".unit .mast::before, .unit .mast::after {\n"
            "  content: \"\"; position: absolute; top: 50%; transform: translateY(-50%);\n}\n"
            ".unit .mast::before { right: 22px; width: 62px; height: 62px; border-radius: 50%; background: var(--book-secondary); }\n"
            f".unit .mast::after {{ right: 35px; width: 36px; height: 36px; background: var(--emblem-fg);\n"
            f"  -webkit-mask: url(\"{_data_uri(emblem)}\") center / contain no-repeat;\n"
            f"  mask: url(\"{_data_uri(emblem)}\") center / contain no-repeat; }}\n")
    else:
        out.append(".unit .mast { padding-right: 24px; }\n")
    out.append(
        "@media (max-width: 720px) {\n"
        "  .unit .mast { padding: 16px 78px 14px 16px; }\n"
        "  .unit .mast::before { right: 14px; width: 50px; height: 50px; }\n"
        "  .unit .mast::after { right: 24px; width: 30px; height: 30px; }\n}\n\n")
    out.append(
        "/* the division's ornament, a light rule above the notes */\n"
        ".unit .notes::before, .print-unit + .print-unit::before {\n"
        "  content: \"\"; display: block; height: 18px; margin: 0 auto 22px; max-width: 520px;\n"
        f"  background: url(\"{_data_uri(orn_light)}\") center / contain no-repeat; opacity: .8;\n}}\n"
        f':root[data-theme="dark"] .unit .notes::before {{ background-image: url("{_data_uri(orn_dark)}"); }}\n'
        f'@media (prefers-color-scheme: dark) {{ :root[data-theme="auto"] .unit .notes::before {{ background-image: url("{_data_uri(orn_dark)}"); }} }}\n\n')
    # the motif cut is 100 units wide; at the 12px height (2/3 scale) that is
    # 66.7px, and the two rule cuts fill the rest, overlapping it by a hair
    def layers(cuts):
        l, m, r = (_data_uri(x) for x in cuts)
        return (f'url("{l}") left center / calc(50% - 33px) 12px no-repeat, '
                f'url("{m}") center / 67px 12px no-repeat, '
                f'url("{r}") right center / calc(50% - 33px) 12px no-repeat')
    heads = ".unit h3.pericope::after, .unit .legend-group + .legend-group::before"
    out.append(
        "/* the heading ornament, in place of the heading underline and the key's group divider:\n"
        "   the motif stays its size, the rule either side stretches to the heading's width */\n"
        ".unit h3.pericope { border-bottom: none; padding-bottom: 0; width: fit-content; max-width: 100%; }\n"
        ".unit .legend-group + .legend-group { border-top: none; padding-top: 0; }\n"
        f"{heads} {{\n"
        "  content: \"\"; display: block; height: 12px; min-width: 110px; margin: 5px 0 0;\n"
        f"  background: {layers(cuts_l)}; opacity: .75;\n}}\n"
        ".unit .legend-group + .legend-group::before { margin: 0 0 12px; }\n"
        # pseudo-elements can't sit inside :is(), so each selector is spelled out
        + ", ".join(f':root[data-theme="dark"] {h}' for h in heads.split(", "))
        + f" {{ background: {layers(cuts_d)}; }}\n"
        + "@media (prefers-color-scheme: dark) { "
        + ", ".join(f':root[data-theme="auto"] {h}' for h in heads.split(", "))
        + f" {{ background: {layers(cuts_d)}; }} }}\n\n")
    out.append(
        "/* tracked-word colours stay their own palette; in dark mode, lifted toward white */\n"
        ':root[data-theme="dark"] .unit [data-root] { --rc-shown: color-mix(in oklab, var(--rc) 58%, #fff); }\n'
        '@media (prefers-color-scheme: dark) { :root[data-theme="auto"] .unit [data-root] { --rc-shown: color-mix(in oklab, var(--rc) 58%, #fff); } }\n')
    return "".join(out)
