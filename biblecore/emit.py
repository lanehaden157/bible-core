"""The site's reading data layer (review F11, F14; plan Phase 3).

    python -m biblecore emit

Writes, for the app's interlinear, reading modes and search:

  data/words/<ch>.json  {"c": 1, "verses": {"1": [{"w", "t", "l", "m", "a"?}]}}
                        every word of the chapter in text order (Ketiv rows
                        dropped): OSHB word id, transliteration, lemma key,
                        morphology in plain words, "a": 1 on Aramaic words.
                        Displayed (English) numbering.
  data/lemmas.json      {"lemmas": {"1696": {"t", "g", "n", "refs"}}}: lexical
                        form transliterated, Strong's short definition
                        (a reader's identifier, never a rendering), count,
                        and every verse it occurs in.
  data/text.json        {"verses": [{"r": "1:3", "u": 1, "t": "..."}]}: the
                        study's own English for every built verse, tags and
                        endnote markers stripped. Condensed verses (data-verses)
                        have no entry, since the fragment doesn't write them out.

No native script is written anywhere. Deterministic, so re-running changes
nothing. The whole book's words are emitted, not only built units, so
"every occurrence of this lemma" covers the book.
"""
import json
import os
import re
from collections import OrderedDict, defaultdict

from biblecore import corpus, roots
from biblecore import meta as um
from biblecore.book import book

SUP_RE = re.compile(r"<sup\b.*?</sup>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
FORM_RE = re.compile(r'<entry id="H(\d+)">.*?<w[^>]*>(.*?)</w>', re.S)


def main_lemma(lemma):
    """'c/1696' -> '1696'; 'l/6485 a' -> '6485a'; '' if none."""
    segs = [s for s in (lemma or "").split("/") if re.search(r"\d", s)]
    return roots.lemma_key(segs[-1].strip()) if segs else ""


def _lexicon_forms(path):
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    return {num: form for num, form in FORM_RE.findall(text)}


def words_by_chapter(b):
    from biblecore.lang import hebrew
    from biblecore.lang.hebrew_morph import describe
    by_ch = defaultdict(lambda: defaultdict(list))
    lemma_refs = defaultdict(list)
    for w in corpus.adapter().load_words(b):
        key = main_lemma(w["lemma"])
        row = OrderedDict(w=w["word_id"],
                          t=hebrew.transliterate_word(w["surface"], w["lemma"], w["morph"]),
                          l=key, m=describe(w["morph"]))
        if w.get("lang") == "aramaic":
            row["a"] = 1
        by_ch[w["ch"]][str(w["v"])].append(row)
        if key:
            ref = f"{w['ch']}:{w['v']}"
            if not lemma_refs[key] or lemma_refs[key][-1] != ref:
                lemma_refs[key].append(ref)
    return by_ch, lemma_refs


def lemmas(b, lemma_refs, counts):
    from biblecore import leads
    from biblecore.lang import hebrew
    glosses = leads.load_glosses(b.path("lexicon"))
    forms = _lexicon_forms(b.path("lexicon"))
    out = OrderedDict()
    for key in sorted(lemma_refs, key=lambda k: (int(re.match(r"\d+", k).group()), k)):
        bare = re.match(r"\d+", key).group()
        form = forms.get(bare)
        out[key] = OrderedDict(
            t=hebrew.transliterate_word(form, bare, None) if form else "",
            g=glosses.get(bare, ""), n=counts[key], refs=lemma_refs[key])
    return out


def verse_text(b):
    import glob
    from biblecore import data_w
    out = []
    uj = um._load("units.json")
    built = {u["n"]: u for u in uj["units"] if u.get("built")}
    for path in sorted(glob.glob(os.path.join(b.path("units"), "unit-*.html"))):
        n = int(re.search(r"unit-(\d+)", os.path.basename(path)).group(1))
        if n not in built:
            continue
        html = open(path, encoding="utf-8").read()
        m = um.PASSAGE_FIRST_CH_RE.search(built[n]["passage"])
        for start, end, ch, v in data_w.verse_blocks(html, int(m.group(1)) if m else 1):
            seg = SUP_RE.sub("", html[start:end])
            seg = re.sub(r'<span class="n">.*?</span>', "", seg, count=1, flags=re.S)
            text = WS_RE.sub(" ", TAG_RE.sub(" ", seg)).strip()
            text = re.sub(r"\s+([,.;:!?’”)])", r"\1", text)
            out.append(OrderedDict(r=f"{ch}:{v}", u=n, t=text))
    return out


def _write_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != text:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return 1
    return 0


def main(argv=None):
    b = book()
    by_ch, lemma_refs = words_by_chapter(b)
    counts = defaultdict(int)
    for ch in by_ch.values():
        for ws in ch.values():
            for w in ws:
                if w["l"]:
                    counts[w["l"]] += 1
    wrote = 0
    wdir = os.path.join(b.path("data"), "words")
    for ch in sorted(by_ch):
        verses = OrderedDict((v, by_ch[ch][v]) for v in sorted(by_ch[ch], key=int))
        wrote += _write_json(os.path.join(wdir, f"{ch}.json"), {"c": ch, "verses": verses})
    lem = lemmas(b, lemma_refs, counts)
    wrote += _write_json(b.data("lemmas.json"), {"lemmas": lem})
    text = verse_text(b)
    wrote += _write_json(b.data("text.json"), {"verses": text})
    print(f"emit: {len(by_ch)} chapter word files, {len(lem)} lemmas, "
          f"{len(text)} built verses ({wrote} file(s) changed)")
    return 0
