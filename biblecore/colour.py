"""Colour: perceptual distance and palette assignment (ARCHITECTURE.md §2).

Every colour on the site is assigned here, never picked by eye. Local roots
get a per-unit colour (assign_hues); newly promoted tracked threads get a
book-wide one (assign_tracked_colors). Both draw from the book's palette
well (book.json "palette"), in order, taking the first colour at least
DE_MIN CIEDE2000 from everything already in play.

Seeded from Joshua's port_artifact.py / validate_units.py.
"""
import json
import math

from biblecore.book import book

DE_MIN = 10          # CIEDE2000 distance below which two roots read as one


def _lab(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    def f(t): return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _de(a, b):
    """CIE76 -- plain Euclidean distance in Lab. Kept for callers that want
    the cheap metric; prefer ciede2000() for anything a reader looks at."""
    return sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))) ** 0.5


def ciede2000(a, b):
    """Perceptual distance between two hex colours (CIEDE2000, kL=kC=kH=1).

    Raw hue distance lies about how different two colours look -- two
    golds 20 degrees apart read as one colour, while two blues the same
    distance apart read as two. CIE76 (_de) is better but still uneven
    across the space. CIEDE2000 adds the lightness/chroma/hue weighting
    and the blue-region rotation term, so one threshold means roughly the
    same thing everywhere in the palette.
    """
    L1, a1, b1 = _lab(a)
    L2, a2, b2 = _lab(b)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7))) if Cb else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def _h(ap, bp):
        if ap == 0 and bp == 0:
            return 0.0
        return math.degrees(math.atan2(bp, ap)) % 360

    h1p, h2p = _h(a1p, b1), _h(a2p, b2)
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)

    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2

    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTheta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    RC = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7)) if Cbp else 0.0
    SL = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    SC = 1 + 0.045 * Cbp
    SH = 1 + 0.015 * Cbp * T
    RT = -math.sin(math.radians(2 * dTheta)) * RC

    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2
                     + RT * (dCp / SC) * (dHp / SH))


def assign_hues(local_roots, taken, well=None):
    """local_roots: [names]; taken: [hex already used in this unit]. Return {name: hex}.

    Picks the first well colour at least DE_MIN from everything already in
    play. When the well is exhausted against this unit, falls back to the
    colour *furthest* from what is taken (never an exact duplicate by
    rote), and validate_units reports the compromise.
    """
    well = well if well is not None else book().palette()
    out, used = {}, list(taken)
    for name in local_roots:
        pick = next((c for c in well
                     if all(ciede2000(c, u) >= DE_MIN for u in used)), None)
        if pick is None:
            pick = max(well, key=lambda c: min((ciede2000(c, u) for u in used),
                                               default=float("inf")))
        out[name] = pick
        used.append(pick)
    return out


def assign_tracked_colors(names, threads_json=None, units_json=None, well=None):
    """Colour(s) for NEWLY PROMOTED tracked threads. A tracked thread can
    appear in any unit, so it avoids every other tracked colour and every
    local-root colour on record, book-wide."""
    b = book()
    if threads_json is None:
        with open(b.data("threads.json"), encoding="utf-8") as f:
            threads_json = json.load(f)
    if units_json is None:
        with open(b.data("units.json"), encoding="utf-8") as f:
            units_json = json.load(f)
    taken = [t["color"] for t in threads_json["threads"] if t.get("color")]
    for u in units_json["units"]:
        for name, r in (u.get("roots") or {}).items():
            if name in names:
                continue
            if isinstance(r, dict) and r.get("color"):
                taken.append(r["color"])
    return assign_hues(names, taken, well)


def closest_pairs(colours, limit=3):
    """[(dE, root_a, hex_a, root_b, hex_b)] for the closest pairs, ranked."""
    items = sorted(colours.items())
    pairs = [(ciede2000(ca, cb), ra, ca, rb, cb)
             for i, (ra, ca) in enumerate(items)
             for rb, cb in items[i + 1:]]
    pairs.sort(key=lambda p: p[0])
    return pairs[:limit]


def main(argv=None):
    """python -m biblecore colour NAME [NAME ...] -- colours for threads
    about to be promoted, to paste into threads.json."""
    import sys
    names = list(sys.argv[1:] if argv is None else argv)
    if not names:
        print("usage: python -m biblecore colour <thread-root> [...]")
        return 2
    for name, hexv in assign_tracked_colors(names).items():
        print(f"{name}: {hexv}")
    return 0
