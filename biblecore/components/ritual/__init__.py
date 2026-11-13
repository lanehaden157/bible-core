"""section.block.ritual: a rite as an ordered strip of steps, and the map.

What the site relies on:
  1. the opening tag is `<section class="block ritual">`, optionally with
     `data-verses="C:V–V"` (validated with every other declaration);
  2. it holds one `<ol class="steps">` of `<li>`s in the order the verses give;
  3. every step has `data-who` (offerer, priest, high-priest, people),
     `data-at` (a zone id of the map, tabmap.ZONES), text, and a `<sup>`
     that is its verse, `C:V` or a range;
  4. `<div class="tabmap">` (empty; optional `data-layer` holy|enter|camp,
     `data-at` a zone id) puts the map in a unit that has no strip.
Enabling this component also writes the map (tabmap.py, app/tabmap.js).
"""
import re

from biblecore import tabmap

OPEN_RE = re.compile(r'<section\b([^>]*\bclass="[^"]*\britual\b[^"]*"[^>]*)>', re.I)
LI_RE = re.compile(r"<li\b([^>]*)>(.*?)</li>", re.S)
SUP_RE = re.compile(r"<sup>(.*?)</sup>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
CV_RE = re.compile(r"^\d+:\d+(?:\s*[–-]\s*(?:\d+:)?\d+)?$")
MARK_RE = re.compile(r'<div\b([^>]*\bclass="tabmap"[^>]*)>(.*?)</div>', re.S)


def _attr(attrs, name):
    m = re.search(rf'\b{name}="([^"]*)"', attrs)
    return m.group(1) if m else None


def check(html, meta):
    errs = []
    for i, m in enumerate(OPEN_RE.finditer(html), 1):
        where = f"section.ritual #{i}"
        if not re.search(r'\bclass="block\s+ritual"', m.group(1)):
            errs.append(f'{where}: class must be exactly "block ritual"')
        end = html.find("</section>", m.end())
        body = html[m.end():end if end >= 0 else len(html)]
        ol = re.search(r'<ol\s+class="steps"[^>]*>(.*?)</ol>', body, re.S)
        if not ol:
            errs.append(f'{where}: needs an <ol class="steps">')
            continue
        steps = LI_RE.findall(ol.group(1))
        if not steps:
            errs.append(f"{where}: no steps")
        for n, (attrs, inner) in enumerate(steps, 1):
            s = f"{where} step {n}"
            who, at = _attr(attrs, "data-who"), _attr(attrs, "data-at")
            if who not in tabmap.WHO:
                errs.append(f"{s}: data-who={who!r} is not one of {tabmap.WHO}")
            if at not in tabmap.ZONES:
                errs.append(f"{s}: data-at={at!r} is not a map zone ({', '.join(tabmap.ZONES)})")
            sups = SUP_RE.findall(inner)
            if not sups:
                errs.append(f"{s}: needs a <sup> verse (C:V)")
            for v in sups:
                if not CV_RE.match(v.strip()):
                    errs.append(f"{s}: <sup>{v}</sup> is not a verse, 'C:V' or 'C:V–V'")
            if not TAG_RE.sub("", SUP_RE.sub("", inner)).strip():
                errs.append(f"{s}: empty")
    for i, m in enumerate(MARK_RE.finditer(html), 1):
        where = f"div.tabmap #{i}"
        if m.group(2).strip():
            errs.append(f"{where}: must be empty")
        layer, at = _attr(m.group(1), "data-layer"), _attr(m.group(1), "data-at")
        if layer not in (None, "holy", "enter", "camp"):
            errs.append(f"{where}: data-layer={layer!r} is not holy, enter or camp")
        if at is not None and at not in tabmap.ZONES:
            errs.append(f"{where}: data-at={at!r} is not a map zone")
    return errs
