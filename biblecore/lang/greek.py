"""Greek -> Latin transliteration (review E12, G7).

The scheme is Matthew's (pipeline/greek.py), carried over unchanged, since
schemes are frozen per language (review H10). tests/test_greek.py is its
authoritative definition. If this docstring and the tests disagree, the
tests win.

  letters     a b g d e z ē th i k l m n x o p r s t y ph ch ps ō
              (η -> ē and ω -> ō: the macron marks the letter, not vowel
              length. It's what tells η from ε and ω from ο, the same
              "diacritic only where the plain letter is taken" principle as
              the Hebrew scheme.)
  diphthongs  ou au eu ēu ai ei oi ui
  nasal gamma gg -> ng, gk -> nk, gx -> nx, gch -> nch
  breathing   rough breathing on the first vowel or diphthong -> initial h;
              initial rho -> rh; smooth breathing is silent
  dropped     accents, diaeresis, iota subscript, smooth breathing
  case        a leading capital is kept

Lemma ids (the identity roots and the audit use) are the transliterated
lemma in lower case: `lemma_key("κληρονομέω") == "klēronomeō"`. That's
Matthew's key too (greek_corpus.py), so its thread notes and canon leads
line up. The corpus adapter (corpus/morphgnt.py) appends a digit only if
two distinct lemmas ever land on the same key.
"""
import re
import unicodedata

_BASE = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "ō",
}
_DIPH = {
    "ου": "ou", "αυ": "au", "ευ": "eu", "ηυ": "ēu",
    "αι": "ai", "ει": "ei", "οι": "oi", "υι": "ui",
    "γγ": "ng", "γκ": "nk", "γξ": "nx", "γχ": "nch",
}
_VOWELS = "aeiouēōy"

# Greek and Coptic block plus Greek Extended: what counts as a Greek word
_GREEK_RE = re.compile("[Ͱ-Ͽἀ-῿]")
# the lemma-id shape roots.json and candidates use for a Greek book
LEMMA_ID_RE = re.compile(r"^[a-zēō]+\d?$")


def _stripaccents(s):
    out = [ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn"]
    return unicodedata.normalize("NFC", "".join(out))


def _has_rough_breathing(word):
    for ch in unicodedata.normalize("NFD", word[:2]):
        if ch == "̔":  # combining reversed comma above
            return True
    for ch in word[:2]:
        name = unicodedata.name(ch, "")
        if "DASIA" in name or "ROUGH" in name:
            return True
    return False


def _split_keep(text):
    """Tokens with the separators (spaces, punctuation) kept."""
    tok, cur = [], []
    for ch in text:
        if ch.isalpha() or "̀" <= ch <= "ͯ":
            cur.append(ch)
        else:
            if cur:
                tok.append("".join(cur))
                cur = []
            tok.append(ch)
    if cur:
        tok.append("".join(cur))
    return tok


def _word(word):
    rough = _has_rough_breathing(word)
    w = _stripaccents(word).lower()
    i, buf = 0, []
    while i < len(w):
        pair = w[i:i + 2]
        if pair in _DIPH:
            buf.append(_DIPH[pair])
            i += 2
            continue
        buf.append(_BASE.get(w[i], w[i]))
        i += 1
    out = "".join(buf)
    if out.startswith("r"):
        out = "rh" + out[1:]
    if rough and out and out[0] in _VOWELS:
        out = "h" + out
    if word[:1].isupper():
        out = out[:1].upper() + out[1:]
    return out


def transliterate(text):
    """Transliterate Greek words; anything that isn't Greek passes through."""
    return "".join(_word(t) if _GREEK_RE.search(t) else t for t in _split_keep(text))


def transliterate_word(surface, lemma=None, morph=None):
    """Same signature as hebrew.transliterate_word, so emit and the leads
    can call either adapter. Greek needs no lemma-keyed overrides."""
    return transliterate(surface)


def lemma_key(lemma):
    """A Greek lemma's id: its transliteration, lower case."""
    return transliterate(lemma).lower()


# ---- the id scheme roots.py and the audit use (see roots._override) ------
# An id is a lemma key, optionally with a digit when two lemmas share a
# transliteration ("kaleō2"). A bare key matches every digit variant; a
# digit names exactly one, the same way Hebrew's letters work.

def is_id_segment(seg):
    return bool(LEMMA_ID_RE.match(seg or ""))


def is_precise(key):
    return key[-1:].isdigit()


def lemma_key_of_id(id_str):
    s = (id_str or "").strip().lower()
    if not LEMMA_ID_RE.match(s):
        raise ValueError(f"malformed Greek lemma id {id_str!r}: a transliterated "
                         f"lemma, optionally with one digit (e.g. 'klēronomeō', 'kaleō2')")
    return s


def bare_id(id_str):
    return lemma_key_of_id(id_str).rstrip("0123456789")
