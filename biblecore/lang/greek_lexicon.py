"""The MorphGNT morphological lexicon (`corpus/lexicon/lexemes.yaml`):
Greek lemma -> a short English gloss (plan D1/phase A: Matthew's interlinear
had none).

    Tauber, J. K., ed. MorphGNT: Morphological Lexicon of the Greek New
    Testament. https://github.com/morphgnt/morphological-lexicon
    CC BY-SA 3.0 -- attribution required (site footer, main.js SOURCES),
    and this vendored copy stays under the same licence (corpus/README.md).

The file is YAML, but small and regular enough that a dependency-free reader
suffices (bible-core has no third-party dependencies, ARCHITECTURE.md §1):
one top-level `<lemma>:` line per entry, its fields indented under it. We
read only `gloss`, which is either a bare phrase, a quoted string, or (a
handful of entries) a `['sense one', 'sense two']` list -- the first sense
is kept, matching how Hebrew's Strong's gloss is "a reader's identifier,
never a rendering" (emit.py).
"""
import re

ENTRY_RE = re.compile(r"^(\S.*):\s*$", re.M)
GLOSS_RE = re.compile(r"^\s+gloss:\s*(.+?)\s*$", re.M)
LIST_ITEM_RE = re.compile(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"")

_cache = {}


def _unquote(raw):
    raw = raw.strip()
    if raw[:1] == "[" and raw[-1:] == "]":
        m = LIST_ITEM_RE.search(raw)
        if m:
            raw = m.group(1) if m.group(1) is not None else m.group(2)
        else:
            raw = raw[1:-1]
    elif len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        raw = raw[1:-1]
    return raw


def load_glosses(path):
    """{greek lemma (with accents, as MorphGNT itself writes it): gloss}."""
    if path in _cache:
        return _cache[path]
    if not path or not __import__("os").path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    out = {}
    starts = [(m.start(), m.end(), m.group(1)) for m in ENTRY_RE.finditer(text)]
    for i, (_start, end, lemma) in enumerate(starts):
        block_end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        g = GLOSS_RE.search(text, end, block_end)
        if g:
            out[lemma] = _unquote(g.group(1))
    _cache[path] = out
    return out
