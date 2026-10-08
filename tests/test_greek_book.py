"""The Greek path end to end on a tiny scratch book (greek_book.py), so it
runs without the Matthew checkout: the MorphGNT word table and reading
text, lemma ids across books, emit's Greek interlinear and glosses, and the
Greek canon leads (LXX + rest of the NT)."""
import contextlib
import io
import json
import os
import re

import greek_book
from biblecore import emit, leads
from biblecore.book import book
from biblecore.corpus import morphgnt

GREEK = re.compile("[Ͱ-Ͽἀ-῿]")
_root = None


def setup():
    global _root
    _root = greek_book.make()
    morphgnt._clear()


def teardown():
    morphgnt._clear()
    greek_book.remove(_root)


def _quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def test_word_table_and_reading_text():
    counts = morphgnt.build(book())
    assert counts == {"verses": 3, "words": 6}, counts
    rows = morphgnt.load_words()
    assert [r["word_id"] for r in rows[:3]] == ["01010101", "01010102", "01010201"]
    assert rows[0]["ref"] == "Matt.1.1" and (rows[0]["ch"], rows[0]["v"]) == (1, 1)
    assert rows[0]["surface"] == "Βίβλος" and rows[0]["morph"] == "N-:----NSF-"
    reading = morphgnt.load_reading()
    # the reading text keeps the punctuation (column 4); the table doesn't
    assert reading[0] == (1, 1, "Βίβλος γενέσεως."), reading[0]
    assert reading[1] == (1, 2, "τίς λέγει;"), reading[1]


def test_homographs_get_a_digit_by_first_appearance():
    ids = morphgnt.lemma_ids(book())
    assert ids["τίς"] == "tis" and ids["τις"] == "tis2", ids
    # the same lemma has the same id in every book
    nt = morphgnt.load_nt_corpus(book())
    assert set(nt) == {"Matt", "Mark", "John"}, set(nt)
    assert nt["John"][0] == (1, 1, "zēlōtēs", "zēlōtēs"), nt["John"][0]
    assert morphgnt.lemma_forms(book())["tis2"] == "τις"


def test_a_book_morphgnt_lacks_is_an_error():
    b = book()
    b.cfg["osis"] = "Josh"
    try:
        morphgnt.parse(b)
    except ValueError as exc:
        assert "isn't a MorphGNT book" in str(exc), exc
    else:
        raise AssertionError("an OT osis id should be refused")
    finally:
        b.cfg["osis"] = "Matt"


def test_emit_writes_a_greek_interlinear_with_glosses():
    morphgnt.build(book())
    _quiet(emit.main, [])
    data = os.path.join(_root, "data")
    ch1 = json.load(open(os.path.join(data, "words", "1.json"), encoding="utf-8"))
    v1 = ch1["verses"]["1"]
    assert [w["l"] for w in v1] == ["biblos", "genesis"], v1
    assert v1[0]["t"] == "Biblos" and v1[0]["m"] == "noun, nom. fem. sing.", v1[0]
    lem = json.load(open(os.path.join(data, "lemmas.json"), encoding="utf-8"))["lemmas"]
    assert lem["biblos"]["g"] == "book" and lem["genesis"]["g"] == "origin, birth", lem
    # a digit-suffixed id displays without its digit
    assert lem["tis2"]["t"] == "tis" and lem["tis2"]["refs"] == ["1:3"], lem["tis2"]
    assert lem["legō"]["g"] == "", lem["legō"]  # not in the lexicon: empty, not a guess
    blob = "".join(open(os.path.join(r, f), encoding="utf-8").read()
                   for r, _d, fs in os.walk(data) for f in fs
                   if os.path.basename(r) != "script")
    assert not GREEK.search(blob), "native Greek script in emitted data"
    # the one place native script is written: the interlinear's top line
    sc = json.load(open(os.path.join(data, "script", "1.json"), encoding="utf-8"))
    assert sc["verses"]["1"] == ["Βίβλος",
                                 "γενέσεως"], sc["verses"]["1"]


def test_leads_phrase_shared_with_the_lxx():
    nt, lxx, order = leads.load_greek_corpus()
    assert order == ["Gen", "Exod"], order
    freq = leads.verse_freq_greek(nt, lxx)
    uw = leads.passage_words_greek(nt, "Matthew 1:1–3")
    assert [r for r, _ in uw] == ["1:1", "1:2", "1:3"], uw
    phrases = {tuple(w[0] for w in p["words"]): p
               for p in leads.phrase_leads_greek(lxx, freq, uw)}
    p = phrases[("biblos", "genesis")]
    assert p["here"] == ["1:1"] and p["hits"] == [("Gen", 2, 4)], p


def test_leads_rare_words_skip_the_book_itself_and_the_synoptics():
    nt, lxx, _order = leads.load_greek_corpus()
    freq = leads.verse_freq_greek(nt, lxx)
    uw = leads.passage_words_greek(nt, "Matthew 1:1–3")
    rare = {r["key"]: r for r in leads.rare_leads_greek(nt, lxx, freq, uw)}
    z = rare["zēlōtēs"]
    assert z["lxx"] == [("Exod", 1, 1)], z
    # Mark is a Synoptic (SYNOPTIC_EXCLUDE_GREEK); Matthew is the book itself
    assert z["nt"] == [("John", 1, 1, "zēlōtēs")], z
    assert z["freq"] == 4 and z["here"] == ["1:3"], z


def test_leads_file_is_transliterated_only():
    out = os.path.join(_root, "canon-leads")
    path = _quiet(leads.build, 1, leads.RARE_DEFAULT, out)
    md = open(path, encoding="utf-8").read()
    assert os.path.basename(path) == "canon-leads-unit-01.md"
    assert "- **Biblos geneseōs** (biblos + genesis) — Matt 1:1\n  - Gen 2:4\n" in md, md
    assert "- **zēlōtēs** (zēlōtēs) — Matt 1:3; 4 verses across the LXX + NT\n" in md, md
    assert not GREEK.search(md), "native Greek script in the leads file"


def test_leads_keep_homographs_apart_in_the_lxx():
    # 'τις' (someone, NT id tis2) is at Gen 1:1; 'τίς' (who?, id tis) isn't
    # in this LXX at all. The LXX is keyed by the same ids as the NT, so
    # each lead gets only its own lexeme's hits.
    nt, lxx, _order = leads.load_greek_corpus()
    freq = leads.verse_freq_greek(nt, lxx)
    uw = leads.passage_words_greek(nt, "Matthew 1:1–3")
    rare = {r["key"]: r for r in leads.rare_leads_greek(nt, lxx, freq, uw)}
    assert rare["tis2"]["lxx"] == [("Gen", 1, 1)], rare.get("tis2")
    assert "tis" not in rare, rare.get("tis")  # no hits outside Matthew
    assert freq["tis"] == 1 and freq["tis2"] == 2, (freq["tis"], freq["tis2"])
    phrases = [tuple(w[0] for w in p["words"]) for p in leads.phrase_leads_greek(lxx, freq, uw)]
    assert ("tis", "legō") not in phrases, phrases  # 'who says' is not 'someone says'


def test_a_phrase_thread_aligns_and_audits_clean():
    # one span over the whole phrase gets the id of its last word, and the
    # audit then finds the phrase covered
    from biblecore import audit, data_w
    morphgnt.build(book())
    threads = {"threads": [{"id": "book-of-origins", "root": "book-of-origins"}]}
    roots = {"roots": {"book-of-origins": {"seq": ["biblos", "genesis"], "note": "x"}}}
    html = ('<p class="v"><span class="n">1</span> The <span class="r" '
            'data-root="book-of-origins">book of the origin</span>.</p>\n'
            '<p class="v"><span class="n">2</span> Who says?</p>\n'
            '<p class="v"><span class="n">3</span> Someone zealous.</p>\n')
    edits, report = data_w.plan(html, "Matthew 1:1–3", threads, roots)
    assert report == [] and [e[2] for e in edits] == ["01010102"], (edits, report)
    tagged = data_w.apply_edits(html, edits)
    assert 'data-root="book-of-origins" data-w="01010102"' in tagged, tagged
    cov = audit.coverage_for_fragment("unit-01", tagged, "Matthew 1:1–3", threads, roots)
    assert not (cov["gaps"] or cov["wrong"] or cov["strays"] or cov["missing_data_w"]), cov
    cov = audit.coverage_for_fragment("unit-01", html.replace(
        'class="r" data-root="book-of-origins"', 'class="x"'), "Matthew 1:1–3", threads, roots)
    assert [g["word_id"] for g in cov["gaps"]] == ["01010102"], cov["gaps"]
