"""Verse numbering: the corpus's own (source) vs. the one the book displays.

OSHB numbers verses as the Leningrad Codex does; English Bibles (KJV and
nearly all since) differ in 27 Hebrew books -- Numbers 16-17, 25-26 and
29-30, Psalm superscriptions, Joel and Malachi's chapter splits, Daniel
3-4, and so on. Fragments, threads and unit rows cite the displayed
numbering (book.json "versification", default "kjv"), so every corpus read
converts through here. (learned: Numbers needed a hand-built map; morphhb
already ships one, wlc/VerseMap.xml, WLC -> KJV.)

Only verses that differ are listed; anything absent maps to itself. Several
source verses can share one display verse (Heb Num 25:19 + 26:1 = Eng
26:1). The map's handful of "partial" rows (a verse split mid-way, e.g.
1 Kgs 18:34) are applied at verse level: word-level splits aren't in the map.
"""
import os
import re

_cache = {}
_ROW_RE = re.compile(r'<verse wlc="([^"]+)" kjv="([^"]+)" type="([a-z]+)"')


def _ref(s):
    """'Num.17.1' / '1Kgs.18.34!a' -> ('Num', 17, 1)"""
    book, c, v = s.split("!")[0].split(".")
    return book, int(c), int(v)


def load(wlc_dir):
    """{osis: {(ch, v) source: (ch, v) display}} from wlc/VerseMap.xml;
    {} when the corpus ships no map."""
    path = os.path.join(wlc_dir, "VerseMap.xml")
    if path in _cache:
        return _cache[path]
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for src, dst, _type in _ROW_RE.findall(fh.read()):
                sb, sc, sv = _ref(src)
                _db, dc, dv = _ref(dst)
                out.setdefault(sb, {}).setdefault((sc, sv), (dc, dv))
    _cache[path] = out
    return out


def book_map(b=None, osis=None):
    """{(ch, v): (ch, v)} source -> display for one book ({} = identity)."""
    if b is None:
        from biblecore.book import book
        b = book()
    if b.versification == "source":
        return {}
    return load(b.path("wlc")).get(osis or b.osis, {})


def to_display(ch, v, vmap):
    return vmap.get((ch, v), (ch, v))


def to_source(ch, v, vmap, present=None):
    """Every source verse shown as display (ch, v), in order. The map
    doesn't say which source verses exist, so without `present` (the set of
    source (ch, v) in the corpus) an unmoved same-numbered verse is assumed
    (Eng 16:36 would come back as Heb 16:36 + 17:1, though Heb 16 ends at 35)."""
    hits = [s for s, d in vmap.items() if d == (ch, v)]
    if (ch, v) not in vmap:      # its own source verse didn't move away
        hits.append((ch, v))
    if present is not None:
        hits = [s for s in hits if s in present]
    return sorted(hits)


def differences(vmap):
    """[(source, display)] sorted by source, for a readable table."""
    return sorted(vmap.items())
