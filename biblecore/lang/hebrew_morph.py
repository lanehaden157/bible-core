"""OSHB morphology codes in plain words, for the interlinear (review F11).

    describe("HC/Vqw3ms") -> "and + verb, qal wayyiqtol, 3rd masc. sing."

A code is a language letter (H Hebrew, A Aramaic) followed by one or more
morphemes separated by "/": prefixes, the main word, suffixes. Each
morpheme starts with a part-of-speech letter. The scheme is OpenScriptures'
(https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html).

Anything this doesn't recognise comes back as the raw morpheme, never as
an error or a guess: the corpus is the authority, this is only a reading aid.
The verb-form names are the ones Lane's study uses (wayyiqtol,
weqatal), not "consecutive imperfect".
"""

PERSON = {"1": "1st", "2": "2nd", "3": "3rd"}
GENDER = {"m": "masc.", "f": "fem.", "c": "common", "b": "masc./fem."}
NUMBER = {"s": "sing.", "p": "pl.", "d": "dual"}
STATE = {"a": "absolute", "c": "construct", "d": "determined"}

HEB_STEMS = {
    "q": "qal", "N": "niphal", "p": "piel", "P": "pual", "h": "hiphil",
    "H": "hophal", "t": "hithpael", "o": "polel", "O": "polal", "r": "hithpolel",
    "m": "poel", "M": "poal", "k": "palel", "K": "pulal", "Q": "qal passive",
    "l": "pilpel", "L": "polpal", "f": "hithpalpel", "D": "nithpael",
    "j": "pealal", "i": "pilel", "u": "hothpaal", "c": "tiphil",
    "v": "hishtaphel", "w": "nithpalel", "y": "nithpoel", "z": "hithpoel",
}
ARAM_STEMS = {
    "q": "peal", "Q": "peil", "u": "hithpeel", "p": "pael", "P": "ithpaal",
    "M": "hithpaal", "a": "aphel", "h": "haphel", "s": "saphel", "e": "shaphel",
    "H": "hophal", "i": "ithpeel", "t": "hishtaphel", "v": "ishtaphel",
    "w": "hithaphel", "o": "polel", "z": "ithpoel", "r": "hithpolel",
    "f": "hithpalpel", "b": "hephal", "c": "tiphel", "m": "poel", "l": "palpel",
    "L": "ithpalpel", "O": "ithpolel", "G": "ittaphal",
}
VERB_TYPES = {
    "p": "qatal", "q": "weqatal", "i": "yiqtol", "w": "wayyiqtol",
    "h": "cohortative", "j": "jussive", "v": "imperative",
    "r": "participle", "s": "passive participle",
    "a": "infinitive absolute", "c": "infinitive construct",
}
ADJ_TYPES = {"a": "adjective", "c": "cardinal number", "g": "gentilic",
             "o": "ordinal number"}
NOUN_TYPES = {"c": "noun", "g": "gentilic noun", "p": "proper noun", "x": "noun"}
PROPER = {"m": "personal name", "f": "personal name", "l": "place name",
          "t": "title"}
PRON_TYPES = {"d": "demonstrative pronoun", "f": "indefinite pronoun",
              "i": "interrogative pronoun", "p": "personal pronoun",
              "r": "relative pronoun"}
SUFFIX_TYPES = {"d": "directional -ah", "h": "paragogic he", "n": "paragogic nun",
                "p": "pronoun suffix"}
PARTICLES = {"a": "particle of affirmation", "d": "the", "e": "exhortation particle",
             "i": "interrogative", "j": "interjection", "m": "demonstrative particle",
             "n": "negative", "o": "object marker", "r": "relative particle"}


# slot order after the type letter(s), per OSHB: nouns and adjectives are
# gender-number-state; finite verbs, pronouns and suffixes person-gender-
# number; participles gender-number-state
NOMINAL = (GENDER, NUMBER, STATE)
FINITE = (PERSON, GENDER, NUMBER)


def _pgn(s, slots):
    """'3ms' / 'msc' -> readable pieces, read positionally ('c' is common as
    a gender and construct as a state)."""
    out = []
    for ch, table in zip(s, slots):
        if ch in table:
            out.append(table[ch])
        elif ch != "x":
            out.append(ch)
    return " ".join(out)


def _morpheme(m, aramaic):
    if not m:
        return ""
    pos, rest = m[0], m[1:]
    if pos == "C":
        return "and"
    if pos == "D":
        return "adverb"
    if pos == "R":
        return "preposition + the" if rest == "d" else "preposition"
    if pos == "T":
        return PARTICLES.get(rest[:1], "particle")
    if pos == "V" and rest:
        stems = ARAM_STEMS if aramaic else HEB_STEMS
        stem, form, pgn = rest[:1], rest[1:2], rest[2:]
        head = f"verb, {stems.get(stem, stem)} {VERB_TYPES.get(form, form)}".strip()
        slots = NOMINAL if form in ("r", "s") else FINITE
        return f"{head}, {_pgn(pgn, slots)}" if pgn else head
    if pos == "N" and rest:
        if rest[0] == "p":
            return PROPER.get(rest[1:2], "proper noun")
        kind = NOUN_TYPES.get(rest[0], "noun")
        return f"{kind}, {_pgn(rest[1:], NOMINAL)}" if rest[1:] else kind
    if pos == "A" and rest:
        kind = ADJ_TYPES.get(rest[0], "adjective")
        return f"{kind}, {_pgn(rest[1:], NOMINAL)}" if rest[1:] else kind
    if pos == "P" and rest:
        kind = PRON_TYPES.get(rest[0], "pronoun")
        return f"{kind}, {_pgn(rest[1:], FINITE)}" if rest[1:] else kind
    if pos == "S" and rest:
        kind = SUFFIX_TYPES.get(rest[0], "suffix")
        return f"{kind}, {_pgn(rest[1:], FINITE)}" if rest[1:] else kind
    return m  # unknown: the raw code, never a guess


def describe(code):
    """Plain-words reading of an OSHB morph code; '' for an empty code."""
    if not code:
        return ""
    aramaic = code.startswith("A")
    body = code[1:] if code[:1] in ("H", "A") else code
    parts = [_morpheme(m, aramaic) for m in body.split("/")]
    text = " + ".join(p for p in parts if p)
    return f"Aramaic: {text}" if aramaic else text
