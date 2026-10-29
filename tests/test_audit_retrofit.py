"""audit.add_entry / candidate_text: the ready-to-paste retrofit `add` JSON
for an untagged gap, with the English text picked from renderings the root
already has. Pure functions over a synthetic fragment."""
import json

import support
support.joshua_book()
from biblecore import audit, retrofit

HTML = (
    '<article>'
    '<div class="v"><span class="n">3</span> He will <span class="r" data-root="love" '
    'data-w="1">love</span> them.</div>'
    '<div class="v"><span class="n">4</span> They hand the loaves over, and he loves '
    'them and Love wins.</div>'
    '<div class="v"><span class="n">5</span> Nothing known here.</div>'
    '<div class="v"><span class="n">6</span> To love and to cherish; loved too.</div>'
    '</article>')
GAP = {"root": "love", "word_id": "w9", "ch": 1, "v": 4, "translit": "agapaō"}


def test_the_one_free_rendering_is_used_as_the_verse_spells_it():
    # "loves" and "Love" are both free in v4: two different texts, so no guess
    assert audit.candidate_text(HTML, 4, {"love": 3, "loves": 1}) is None
    # one rendering known: it is found, capital and all
    assert audit.candidate_text(HTML, 4, {"loves": 1}) == "loves"
    assert audit.candidate_text(HTML, 4, {"Love": 1}) == "Love"


def test_no_free_rendering_or_no_verse_gives_none():
    assert audit.candidate_text(HTML, 5, {"love": 3}) is None
    assert audit.candidate_text(HTML, 99, {"love": 3}) is None


def test_a_tagged_occurrence_is_not_a_candidate():
    # v3's only "love" is already in a span
    assert audit.candidate_text(HTML, 3, {"love": 1}) is None


def test_entry_is_the_add_shape_retrofit_reads():
    gap = dict(GAP, v=6)
    e = audit.add_entry(gap, "unit-01", "Joshua 1:1-9", HTML, {"love": {"loved": 1}})
    assert e == {"unit": "unit-01", "verse": 6, "root": "love", "text": "loved",
                 "w": "w9", "why": "agapaō 1:6"}, e
    # and retrofit can place it, tagging the word id it names
    html, msg = retrofit.apply_add(HTML, e)
    assert msg.startswith("ADD") and 'data-w="w9">loved</span>' in html, msg


def test_unknown_text_stays_a_marked_blank():
    e = audit.add_entry(GAP, "unit-01", "Joshua 1:1-9", HTML, {"love": {"cherish": 1}})
    assert e["text"] == "???", e


def test_a_chapter_crossing_unit_names_the_verse_c_v():
    e = audit.add_entry(dict(GAP, ch=2, v=1), "unit-01", "Joshua 1:5-2:3", HTML,
                        {"love": {}})
    assert e["verse"] == "2:1", e


def test_the_line_is_pasteable_json():
    e = audit.add_entry(GAP, "unit-01", "Joshua 1:1-9", HTML, {"love": {}})
    line = audit.add_entry_line(e)
    assert json.loads(line.strip().rstrip(",")) == e, line
