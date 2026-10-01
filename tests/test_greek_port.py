"""The porter on a Greek unit, through the CLI (Greek-in-core pass 2, Lane's
L3): a Greek book made from the template, a tiny MorphGNT Matthew that
crosses a chapter, and an artifact shaped the way Matthew's chat side writes
them (a `2:1` label at the chapter seam, a phrase-thread candidate, an
itinerary whose stop covers a scene). What each step checks is what the
scratch-book replay of Matthew units 9-14 tripped on:

  * port fills data-w, and its gap stub names a cross-chapter verse "C:V"
    (with its word id), since a bare 1 would mean 1:1, not 2:1
  * a `seq` candidate gets an id preview like an `ids` one, with readable
    Greek ids (no \\u escapes)
  * retrofit `add` finds "2:1" by rolling the chapter
  * scan reads the seam label as its verse
  * an itinerary stop's sup may be a range
  * then build, audit and test pass
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import greek_book
from template_book import make_book

import new_book  # tools/ is on the path through template_book

# (bbccvv, pos, parse, text, word, lemma): Matthew 1:1-3, 2:1-2
MT = [
    ("010101", "N-", "----NSF-", "Βίβλος", "Βίβλος", "βίβλος"),
    ("010101", "N-", "----GSF-", "γενέσεως", "γενέσεως", "γένεσις"),
    ("010101", "N-", "----GSM-", "Ἰησοῦ.", "Ἰησοῦ", "Ἰησοῦς"),
    ("010102", "N-", "----GSM-", "υἱοῦ", "υἱοῦ", "υἱός"),
    ("010102", "N-", "----GSM-", "Δαυίδ.", "Δαυίδ", "Δαυίδ"),
    ("010103", "V-", "3AAI-S--", "ἐγέννησεν.", "ἐγέννησεν", "γεννάω"),
    ("010201", "N-", "----GSM-", "Ἰησοῦ", "Ἰησοῦ", "Ἰησοῦς"),
    ("010201", "V-", "AAPGSM-", "γεννηθέντος.", "γεννηθέντος", "γεννάω"),
    ("010202", "N-", "----NSM-", "υἱὸς", "υἱὸς", "υἱός"),
    ("010202", "N-", "----GSM-", "Δαυίδ.", "Δαυίδ", "Δαυίδ"),
]

META = {
    "unit": 1, "passage": "Matthew 1:1–2:2", "title": "The Book of the Origin",
    "roots": [],
    "threads": {
        "opens": [{"id": "beget", "ref": "1:1", "note": "the line begins"}],
        "payoffs": [],
        "candidates": [{"root": "son-of-david", "why": "the title, 1:2 and 2:2",
                        "seq": ["huios", "dauid"]}],
        "retro": [],
    },
}

ARTIFACT = """<article class="unit" data-unit="1">
<script type="application/json" id="unit-meta">
%s
</script>
<header class="mast"><h1>The Book of the Origin</h1></header>
<section class="block legend"><ul></ul></section>
<section class="block"><h2>Where it happens</h2>
<div class="itin"><span class="stop">Bethlehem <sup>2:1–2</sup></span><span class="arr">→</span><span class="stop">Judea <sup>2:1</sup></span></div>
</section>
<h3 class="pericope">The line <span>· 1:1–3</span></h3>
<p class="v"><span class="n">1</span> The book of the <span class="r" data-root="beget">origin</span> of Jesus.</p>
<p class="v"><span class="n">2</span> Son of David.</p>
<p class="v"><span class="n">3</span> He <span class="r" data-root="beget">fathered</span>.</p>
<h3 class="pericope">The birth <span>· 2:1–2</span></h3>
<p class="v"><span class="n">2:1</span> When Jesus was born.</p>
<p class="v"><span class="n">2</span> The son of David.</p>
<div class="notes"><h2>Notes</h2><ol></ol></div>
</article>
""" % json.dumps(META, ensure_ascii=False, indent=2)


def _cli(root, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("BIBLECORE_BOOK", None)
    return subprocess.run([sys.executable, "-m", "biblecore", *args], cwd=root, env=env,
                          capture_output=True, text=True, encoding="utf-8")


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _dump(p, d):
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _book():
    d = tempfile.mkdtemp(prefix="bc-greek-port-")
    make_book(d, "Matthew", "Matt", "matthew", language="greek")
    new_book.copy_lexicon(d, "greek")
    mgnt = os.path.join(d, "corpus", "morphgnt")
    os.makedirs(mgnt)
    with open(os.path.join(mgnt, "61-Mt-morphgnt.txt"), "w", encoding="utf-8", newline="\n") as fh:
        for bcv, pos, parse, text, word, lemma in MT:
            fh.write(f"{bcv} {pos} {parse} {text} {word} {word.lower()} {lemma}\n")
    greek_book.write_lxx(os.path.join(d, "corpus", "lxx"))
    bj = _load(os.path.join(d, "book.json"))
    bj["components"] = bj["components"] + ["itin"]
    _dump(os.path.join(d, "book.json"), bj)
    uj = _load(os.path.join(d, "data", "units.json"))
    uj["unit_count"] = 1
    uj["units"] = [{"n": 1, "slug": "unit-01", "passage": "Matthew 1:1–2:2",
                    "title": "The Book of the Origin", "built": False}]
    _dump(os.path.join(d, "data", "units.json"), uj)
    tj = _load(os.path.join(d, "data", "threads.json"))
    tj["threads"] = [{"id": "beget", "root": "beget", "translit": "gennaō · genesis",
                      "gloss": "beget", "color": "#a8324a", "status": "open", "tagged": False,
                      "opens": {"unit": 1, "ref": "1:1", "note": "the line begins"},
                      "payoffs": []}]
    _dump(os.path.join(d, "data", "threads.json"), tj)
    rj = _load(os.path.join(d, "data", "roots.json"))
    rj["roots"] = {"beget": {"ids": ["gennaō", "genesis"], "note": "x"}}
    _dump(os.path.join(d, "data", "roots.json"), rj)
    with open(os.path.join(d, "source-artifacts", "matthew_01_translation.html"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(ARTIFACT)
    return d


def test_a_greek_unit_ports_across_a_chapter_seam():
    d = _book()
    fails = []
    try:
        for args in (("corpus",), ("build",)):
            r = _cli(d, *args)
            if r.returncode:
                return [f"`biblecore {' '.join(args)}` before the port exited "
                        f"{r.returncode}:\n{(r.stdout + r.stderr)[-1500:]}"]
        r = _cli(d, "port", "1")
        frag_p = os.path.join(d, "units", "unit-01.html")
        if not os.path.exists(frag_p):
            return [f"port wrote no fragment:\n{(r.stdout + r.stderr)[-1500:]}"]
        frag = open(frag_p, encoding="utf-8").read()
        for w in ("01010102", "01010301"):
            if f'data-w="{w}"' not in frag:
                fails.append(f"port didn't fill data-w {w}")

        delta = open(os.path.join(d, "out", "thread-delta-01.md"), encoding="utf-8").read()
        if '"seq": ["huios", "dauid"]' not in delta:
            fails.append("the phrase candidate got no seq preview:\n" + delta)
        if "match **2** word(s)" not in delta:
            fails.append("the seq preview should find the phrase twice (1:2, 2:2)")
        if "\\u" in delta:
            fails.append("the thread delta escapes Greek ids (\\u...)")
        if '"verse": "2:1"' not in delta or '"w": "01020102"' not in delta:
            fails.append("the gap stub for 2:1 should say \"verse\": \"2:1\" with its word id:\n"
                         + delta)

        # the delta's "set tagged: true", and the gap fixed the way the stub says
        tj_p = os.path.join(d, "data", "threads.json")
        tj = _load(tj_p)
        tj["threads"][0]["tagged"] = True
        _dump(tj_p, tj)
        rf_p = os.path.join(d, "retrofit", "retrofit-tags.json")
        rf = _load(rf_p)
        rf.setdefault("add", []).append({"unit": "unit-01", "verse": "2:1", "text": "born",
                                         "root": "beget", "w": "01020102", "why": "gennaō 2:1"})
        _dump(rf_p, rf)
        for args in (("build",), ("test",)):
            r = _cli(d, *args)
            if r.returncode:
                fails.append(f"`biblecore {' '.join(args)}` exited {r.returncode}:\n"
                             + (r.stdout + r.stderr)[-1500:])
        frag = open(frag_p, encoding="utf-8").read()
        if '<span class="r" data-root="beget" data-w="01020102">born</span>' not in frag:
            fails.append("retrofit didn't tag 'born' in 2:1")
        r = _cli(d, "audit", "--unit", "unit-01")
        if "0 gap(s)" not in r.stdout:
            fails.append(f"audit still finds gaps:\n{r.stdout[-800:]}")
        occ = _load(os.path.join(d, "data", "occurrences.json"))["unit-01"]["beget"]
        if [h["v"] for h in occ["hits"]] != [1, 3, 1] or occ["hits"][2]["hit"] != "born":
            fails.append(f"scan should read the 2:1 label as verse 1: {occ['hits']}")
        return fails
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_retrofit_finds_a_chapter_verse_by_rolling():
    from biblecore import retrofit
    html = ('<script type="application/json" id="unit-meta">{"passage": "Matthew 9:35–11:1"}'
            '</script><p class="v"><span class="n">35</span> a.</p>'
            '<p class="v"><span class="n">1</span> ten one.</p>'
            '<p class="v"><span class="n">11:1</span> eleven one.</p>')
    fails = []
    for verse, want in (("10:1", "ten one"), ("11:1", "eleven one"), ("9:35", " a.")):
        span = retrofit.vblock(html, verse)
        if not span or want not in html[span[0]:span[1]]:
            fails.append(f"vblock({verse!r}) -> {span and html[span[0]:span[1]]}")
    if retrofit.vblock(html, "10:2") is not None:
        fails.append("vblock found a verse the fragment doesn't have")
    return fails
