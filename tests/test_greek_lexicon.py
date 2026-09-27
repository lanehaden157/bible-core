"""lang/greek_lexicon.py: the MorphGNT morphological lexicon parser (plan
D1/phase A). A small dependency-free reader over lexemes.yaml, not a real
YAML parser -- these cases are the ones that would break a naive one: a
bare phrase, a quoted phrase with an internal comma, a bare apostrophe, and
the handful of entries with a `gloss: ['a', 'b']` list (first sense kept,
matching how Hebrew's Strong's gloss works)."""
import os
import tempfile

from biblecore.lang import greek_lexicon

SAMPLE = """\
Ἀαρών:
    pos: N
    full-citation-form: Ἀαρών, ὁ
    strongs: 2
    gloss: Aaron
ἀβαρής:
    pos: A
    gloss: not burdensome
ἄπειμι:
    pos: V
    gloss: ['I am absent', 'I go away, depart']
Ἄρειος:
    pos: N
    gloss: Areopagus, Mars' Hill
μαρᾱνᾰ́θᾰ:
    pos: X
    gloss: "marana (Aramaic: our Lord)"
"""


def _write(text):
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def test_parses_bare_quoted_and_list_glosses():
    path = _write(SAMPLE)
    try:
        d = greek_lexicon.load_glosses(path)
    finally:
        os.remove(path)
    want = {
        "Ἀαρών": "Aaron",
        "ἀβαρής": "not burdensome",
        "ἄπειμι": "I am absent",
        "Ἄρειος": "Areopagus, Mars' Hill",
        "μαρᾱνᾰ́θᾰ": "marana (Aramaic: our Lord)",
    }
    fails = [f"{k}: got {d.get(k)!r}, want {v!r}" for k, v in want.items() if d.get(k) != v]
    if len(d) != len(want):
        fails.append(f"{len(d)} entries parsed, want {len(want)}: {sorted(d)}")
    return fails


def test_missing_file_returns_empty():
    if greek_lexicon.load_glosses("C:/nope/not-here.yaml") != {}:
        return ["a missing lexicon should return {}, not raise"]
    if greek_lexicon.load_glosses(None) != {}:
        return ["no path should return {}"]
    return []
