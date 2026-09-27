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
    full width above the notes, and a short centre cut (mini_ornament) under
    each section heading and between the colour key's groups (Lane,
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


def mini_ornament(svg):
    """The centre of a full ornament (its motif and a little of the rule on
    each side): the same drawing, cropped by its viewBox."""
    return svg.replace('viewBox="0 0 600 18"', 'viewBox="200 0 200 18"')


def _data_uri(svg):
    # '#' (colours) and quotes must be escaped inside a CSS url("…")
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="=:/,.()-")


def ornament_svg(div_id, sig, ink):
    """A thin section rule in the division's own idiom, 600x18."""
    a, b, c = sig
    w = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 18" preserveAspectRatio="xMidYMid meet" fill="none" stroke-linecap="round"'
    if div_id == "torah":
        wave = "C25 3 50 15 75 9S125 3 150 9 200 15 225 9 262 4 280 9"
        body = (f'<path d="M0 9{wave}" stroke="{a}" stroke-width="1"/>'
                f'<path d="M0 9C25 15 50 3 75 9S125 15 150 9 200 3 225 9 262 14 280 9" stroke="{c}" stroke-width="1"/>'
                f'<path d="M320 9C345 3 370 15 395 9S445 3 470 9 520 15 545 9 582 4 600 9" stroke="{a}" stroke-width="1"/>'
                f'<path d="M320 9C345 15 370 3 395 9S445 15 470 9 520 3 545 9 582 14 600 9" stroke="{c}" stroke-width="1"/>'
                f'<path d="M300 2L307 9L300 16L293 9Z" stroke="{b}" stroke-width="1"/>')
    elif div_id == "former":
        joints = "".join(f"M{x} 3V9" for x in list(range(20, 280, 40)) + list(range(340, 600, 40)))
        joints += "".join(f"M{x} 9V15" for x in list(range(40, 280, 40)) + list(range(360, 600, 40)))
        body = (f'<path d="M0 3H280M0 9H280M0 15H280M320 3H600M320 9H600M320 15H600{joints}" stroke="{b}" stroke-width=".8"/>'
                f'<path d="M290 2H310L306.5 16H293.5Z" stroke="{a}" stroke-width="1"/>')
    elif div_id == "latter":
        body = (f'<path d="M0 11H252M348 11H600" stroke="{b}" stroke-width="1"/>'
                f'<g fill="{a}"><circle cx="262" cy="10.5" r="1.2"/><circle cx="272" cy="8" r=".9"/><circle cx="338" cy="10.5" r="1.2"/><circle cx="328" cy="8" r=".9"/></g>'
                f'<path d="M300 16C293.5 13 296.5 7 300 1.5C303.5 7 306.5 13 300 16Z" stroke="{a}" stroke-width="1"/>')
    elif div_id == "writings":
        body = (f'<path d="M0 9C40 3 60 15 100 9S160 3 200 9 250 14 278 9M322 9C350 4 380 15 420 9S480 3 520 9 570 15 600 9" stroke="{a}" stroke-width="1"/>'
                f'<g stroke="{b}" stroke-width="1"><path d="M60 7C63 2.5 68 2.5 70 4C67 7 63 8 60 7Z"/><path d="M160 11C163 15.5 168 15.5 170 14C167 11 163 10 160 11Z"/><path d="M430 7C433 2.5 438 2.5 440 4C437 7 433 8 430 7Z"/><path d="M530 11C533 15.5 538 15.5 540 14C537 11 533 10 530 11Z"/></g>'
                f'<path d="M292 16C289 10 290.5 3.5 295 3M308 16C311 10 309.5 3.5 305 3M293.5 16H306.5M296.5 5V15M300 4.5V15.5M303.5 5V15" stroke="{c}" stroke-width="1"/>')
    else:  # nt: scroll ends, three dots at the centre
        body = (f'<path d="M14 9H286M314 9H586" stroke="{ink}" stroke-width=".9"/>'
                f'<path d="M14 9C8.5 9 5 5.5 7 2.5C9 .5 13 1.5 13 5C13 7.4 10 7.4 10 5.6" stroke="{ink}" stroke-width=".9"/>'
                f'<path d="M586 9C591.5 9 595 12.5 593 15.5C591 17.5 587 16.5 587 13C587 10.6 590 10.6 590 12.4" stroke="{ink}" stroke-width=".9"/>'
                f'<g fill="{a}"><circle cx="292" cy="9" r="1.4"/><circle cx="300" cy="9" r="1.8"/><circle cx="308" cy="9" r="1.4"/></g>')
    return f"<svg {w}>{body}</svg>"


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
    from biblecore import __version__
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
    out = [
        f"@import url('https://fonts.googleapis.com/css2?{'&'.join(fonts)}&display=swap');\n",
        f"/* division.css -- GENERATED by `python -m biblecore build` from bible-core {__version__}\n"
        f"   web/themes.json: {div['label']} ({div.get('motif', '')}), book accents "
        f"'{book.get('name', b.name)}'. Don't edit; override in theme.css or book.json \"theme\". */\n\n",
        _block(":root", light), "\n",
        _block(':root[data-theme="dark"]', dark),
        "@media (prefers-color-scheme: dark) {\n" + _block('  :root[data-theme="auto"]', dark).replace("\n  --", "\n    --") + "}\n\n",
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
    mini_l, mini_d = _data_uri(mini_ornament(orn_light)), _data_uri(mini_ornament(orn_dark))
    heads = ".unit h3.pericope::after, .unit .legend-group + .legend-group::before"
    out.append(
        "/* the short ornament in place of the heading underline and the key's group divider */\n"
        ".unit h3.pericope { border-bottom: none; padding-bottom: 0; }\n"
        ".unit .legend-group + .legend-group { border-top: none; padding-top: 0; }\n"
        f"{heads} {{\n"
        "  content: \"\"; display: block; height: 12px; width: 170px; margin: 5px 0 0;\n"
        f"  background: url(\"{mini_l}\") left center / contain no-repeat; opacity: .75;\n}}\n"
        ".unit .legend-group + .legend-group::before { margin: 0 auto 12px; background-position: center; }\n"
        "body.text-center .unit h3.pericope::after { margin-left: auto; margin-right: auto; background-position: center; }\n"
        # pseudo-elements can't sit inside :is(), so each selector is spelled out
        + ", ".join(f':root[data-theme="dark"] {h}' for h in heads.split(", "))
        + f' {{ background-image: url("{mini_d}"); }}\n'
        + "@media (prefers-color-scheme: dark) { "
        + ", ".join(f':root[data-theme="auto"] {h}' for h in heads.split(", "))
        + f' {{ background-image: url("{mini_d}"); }} }}\n\n')
    out.append(
        "/* tracked-word colours stay their own palette; in dark mode, lifted toward white */\n"
        ':root[data-theme="dark"] .unit [data-root] { --rc-shown: color-mix(in oklab, var(--rc) 58%, #fff); }\n'
        '@media (prefers-color-scheme: dark) { :root[data-theme="auto"] .unit [data-root] { --rc-shown: color-mix(in oklab, var(--rc) 58%, #fff); } }\n')
    return "".join(out)
