"""MorphGNT parsing codes in plain words, for the interlinear.

    describe("V-:3AAI-S--") -> "verb, aorist active indicative, 3rd sing."

The corpus adapter stores each word's morph as "<pos>:<parse>", MorphGNT's
two columns joined: the part-of-speech code (N-, V-, RA, ...) and the
8-slot parse (person, tense, voice, mood, case, number, gender, degree;
'-' for an empty slot). The scheme is MorphGNT's
(https://github.com/morphgnt/sblgnt). An unknown code comes back raw,
never guessed.
"""

POS = {
    "A-": "adjective", "C-": "conjunction", "D-": "adverb", "I-": "interjection",
    "N-": "noun", "P-": "preposition", "RA": "the", "RD": "demonstrative pronoun",
    "RI": "interrogative/indefinite pronoun", "RP": "personal pronoun",
    "RR": "relative pronoun", "V-": "verb", "X-": "particle",
}
PERSON = {"1": "1st", "2": "2nd", "3": "3rd"}
TENSE = {"P": "present", "I": "imperfect", "F": "future", "A": "aorist",
         "X": "perfect", "Y": "pluperfect"}
VOICE = {"A": "active", "M": "middle", "P": "passive"}
MOOD = {"I": "indicative", "D": "imperative", "S": "subjunctive", "O": "optative",
        "N": "infinitive", "P": "participle"}
CASE = {"N": "nom.", "G": "gen.", "D": "dat.", "A": "acc.", "V": "voc."}
NUMBER = {"S": "sing.", "P": "pl."}
GENDER = {"M": "masc.", "F": "fem.", "N": "neut."}
DEGREE = {"C": "comparative", "S": "superlative"}


def describe(code):
    if not code or ":" not in code:
        return code or ""
    pos, parse = code.split(":", 1)
    head = POS.get(pos)
    if head is None or len(parse) != 8:
        return code
    p, t, v, m, c, n, g, d = parse
    verbal = " ".join(x for x in (TENSE.get(t), VOICE.get(v), MOOD.get(m)) if x)
    nominal = " ".join(x for x in (CASE.get(c), GENDER.get(g), NUMBER.get(n)) if x)
    person = " ".join(x for x in (PERSON.get(p), NUMBER.get(n) if p != "-" else None) if x)
    parts = [head]
    if verbal:
        parts.append(verbal)
    if p != "-":
        parts.append(person)
    elif nominal:
        parts.append(nominal)
    if DEGREE.get(d):
        parts.append(DEGREE[d])
    return ", ".join(parts)
