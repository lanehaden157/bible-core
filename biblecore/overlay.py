"""The overlay grouping with verse ranges (book.json "overlay_note").

A plain overlay (Matthew's discourses) is a grouping whose entries list whole
units. A book that sets `overlay_note` (Deuteronomy's treaty pattern) draws
the same overlay with three extensions, all in units.json `groupings[]`:

    {"kind": "treaty", "n": 3, "name": "witnesses", "label": "Witnesses",
     "units": [4, 24, 30],                    # may be non-contiguous
     "verses": {"4": "4:26", "30": "30:19"}}  # optional, per member unit

- an element lists its member units and, per unit, the exact verses in it
  ("4:26", "4:26; 30:19", "4:26–31"): inside that unit's passage;
- a unit may belong to several elements (the rows are independent);
- the book map brackets the units, each unit's placement line names its
  element(s) with verses, and `overlay_note` shows in the map's key.

Units without `verses` keep the plain overlay's behaviour. `validate` checks
the shape; the shell reads it (app/main.js, the //overlayx blocks).
"""
import re

from biblecore import audit

VERSES_RE = re.compile(r"^\d+:\d+(?:\s*[–-]\s*(?:\d+:)?\d+)?$")


def parse_verses(text):
    """'4:26; 30:19–20' -> [((4,26),(4,26)), ((30,19),(30,20))]; None if malformed."""
    if not isinstance(text, str) or not text.strip():
        return None
    out = []
    for part in text.split(";"):
        part = part.strip()
        if not VERSES_RE.match(part):
            return None
        lo, hi = audit.parse_range(part)
        if hi < lo:
            return None
        out.append((lo, hi))
    return out


def validate(units_json, b):
    """Problems with the overlay entries of units.json (strings; [] if sound)."""
    kind = b.cfg.get("overlay")
    if not kind:
        return []
    errs = []
    rows = {u["n"]: u for u in units_json.get("units", [])}
    extended = bool(b.cfg.get("overlay_note"))
    seen = set()
    for g in units_json.get("groupings", []):
        if g.get("kind") != kind:
            continue
        where = f"{kind} {g.get('n')}"
        if g.get("n") in seen:
            errs.append(f"{where}: duplicate n")
        seen.add(g.get("n"))
        us = g.get("units")
        if not (isinstance(us, list) and us and all(isinstance(n, int) for n in us)):
            errs.append(f"{where}: 'units' must be a list of unit numbers")
            continue
        for n in us:
            if n not in rows:
                errs.append(f"{where}: unit {n} is not in units.json")
        if len(set(us)) != len(us):
            errs.append(f"{where}: a unit is listed twice")
        verses = g.get("verses")
        if verses is None:
            continue
        if not extended:
            errs.append(f"{where}: 'verses' needs overlay_note in book.json")
            continue
        if not isinstance(verses, dict):
            errs.append(f"{where}: 'verses' must be {{unit: verses}}")
            continue
        for k, text in verses.items():
            n = int(k) if str(k).isdigit() else None
            if n not in us:
                errs.append(f"{where}: verses names unit {k}, not a member")
                continue
            spans = parse_verses(text)
            if spans is None:
                errs.append(f"{where}: unit {k} verses {text!r} is not like '4:26' or '4:26; 30:19–20'")
                continue
            row = rows.get(n) or {}
            if row.get("passage"):
                lo, hi = audit.parse_range(row["passage"])
                for s, e in spans:
                    if s < lo or e > hi:
                        errs.append(f"{where}: unit {k} verses {text!r} fall outside {row['passage']}")
                        break
    return errs
