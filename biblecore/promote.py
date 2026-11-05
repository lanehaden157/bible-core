"""Fill a thread promotion's computed parts from the data.

A research handoff proposes a promotion as: id, lemma ids, gloss, an opener
note and a reason. Everything that can be looked up is computed here from the
word table and the unit registry, so nobody hand-writes the JSON shape:

    opens.unit / opens.ref   first occurrence of the id set, book-wide
    payoffs[].ref            for a payoff given as {unit, note}: its first
                             verse in that unit (a payoff with a ref is kept)
    reach                    "N occurrences, retrofit in units X, Y"
    retrofit                 built units, other than this one, holding it

`complete()` returns (item, notes): a full {entry, reach, retrofit} item
(the shape meta.validate and apply-delta always took) and plain-language
notes on anything it changed or could not compute. A value the chat did give
is kept unless the data disagrees about the opener, which is reported.
"""
import copy
import json

from biblecore import audit as atc
from biblecore.book import book


def _spans(units_json):
    out = []
    for u in units_json.get("units", []):
        try:
            out.append((u["n"], bool(u.get("built")), atc.parse_range(u["passage"])))
        except (AttributeError, TypeError, KeyError):
            pass
    return out


def occurrences(ids, words=None):
    """[(ch, v)] of every word the id set claims, in text order."""
    words = words if words is not None else atc.load_words()
    return list(atc.source_hits_for_root(words, ids).values())


def complete(item, this_unit=None, words=None, units_json=None):
    item = copy.deepcopy(item)
    notes = []
    e = item.setdefault("entry", {})
    ids = e.get("ids") or []
    if not ids:
        return item, ["no ids: nothing to compute from"]
    spans = _spans(units_json or json.load(open(book().data("units.json"), encoding="utf-8")))
    cvs = occurrences(ids, words)
    if not cvs:
        return item, [f"ids {ids} match no word in the word table"]

    def unit_of(cv):
        return next((n for n, _b, (lo, hi) in spans if lo <= cv <= hi), None)

    def ref(cv):
        return f"{cv[0]}:{cv[1]}"

    first = cvs[0]
    given = dict(e.get("opens") or {})
    comp = {"unit": unit_of(first), "ref": ref(first)}
    if given.get("unit") not in (None, comp["unit"]) or given.get("ref") not in (None, comp["ref"]):
        notes.append(f"opens given as unit {given.get('unit')} ({given.get('ref')}) but the id set "
                     f"first occurs at {comp['ref']} (unit {comp['unit']}); used the computed one")
    opens = {"unit": comp["unit"], "ref": comp["ref"]}
    if given.get("note"):
        opens["note"] = given["note"]
    e["opens"] = opens

    by_unit = {}
    for cv in cvs:
        by_unit.setdefault(unit_of(cv), []).append(cv)
    pays = []
    for p in e.get("payoffs") or []:
        p = dict(p)
        if not p.get("ref"):
            hits = by_unit.get(p.get("unit"))
            if hits:
                p["ref"] = ref(hits[0])
            else:
                notes.append(f"payoff for unit {p.get('unit')}: the id set does not occur there")
        pays.append(p)
    e["payoffs"] = pays

    built = [n for n, b, _r in spans if b and n != this_unit and n in by_unit]
    item.setdefault("retrofit", built)
    if not item.get("reach"):
        item["reach"] = (f"{len(cvs)} occurrences, " +
                         (f"retrofit in units {', '.join(map(str, item['retrofit']))}"
                          if item["retrofit"] else "no built unit to retrofit"))
    return item, notes
