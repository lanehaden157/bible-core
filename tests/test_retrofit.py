"""Regression tests for apply_retrofit.py. Operates purely on English gloss
HTML (the fragment's visible text), so nothing here needs Hebrew -- the one
Joshua-specific addition (data-w injection on add/retag) is exercised with
made-up word ids, since the op itself doesn't care whether an id is real;
that's unit_meta.validate()'s job (see test_unit_meta.py's retro-w tests).
"""
import os
import sys

from biblecore import retrofit as ar  # noqa: E402

fail = []


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


def _verse(n, text):
    return f'<p class="v"><span class="n">{n}</span> {text}</p>'


# --------------------------------------------------------------------- add

def test_add_wraps_free_text():
    html = _verse(3, "and all Israel with him")
    new, msg = ar.apply_add(html, {"unit": "unit-01", "verse": 3,
                                    "root": "kol", "text": "all"})
    _check("add should wrap the free text", 'data-root="kol">all</span>' in new, new)
    _check("add message starts with ADD", msg.startswith("ADD"), msg)


def test_add_with_w_injects_data_w():
    html = _verse(3, "and all Israel with him")
    new, msg = ar.apply_add(html, {"unit": "unit-01", "verse": 3,
                                    "root": "kol", "text": "all", "w": "06XR4"})
    _check("add with w should inject data-w",
           'data-root="kol" data-w="06XR4">all</span>' in new, new)


def test_add_is_idempotent():
    html = _verse(3, "and all Israel with him")
    once, _ = ar.apply_add(html, {"unit": "unit-01", "verse": 3,
                                   "root": "kol", "text": "all", "w": "06XR4"})
    twice, msg = ar.apply_add(once, {"unit": "unit-01", "verse": 3,
                                      "root": "kol", "text": "all", "w": "06XR4"})
    _check("re-applying add should no-op", twice == once, (once, twice))
    _check("re-applying add should say 'ok'", msg.startswith("ok"), msg)


def test_add_miss_when_text_not_free():
    html = _verse(3, "nothing matches here")
    new, msg = ar.apply_add(html, {"unit": "unit-01", "verse": 3,
                                    "root": "kol", "text": "all"})
    _check("add should MISS when text isn't present", msg.startswith("MISS"), msg)
    _check("add should not modify html on MISS", new == html, (html, new))


def test_add_skip_when_no_verse_block():
    html = _verse(3, "and all Israel with him")
    new, msg = ar.apply_add(html, {"unit": "unit-01", "verse": 99,
                                    "root": "kol", "text": "all"})
    _check("add should SKIP when the verse block doesn't exist",
           msg.startswith("SKIP"), msg)


def test_add_respects_cls():
    html = _verse(3, "and all Israel with him")
    new, msg = ar.apply_add(html, {"unit": "unit-01", "verse": 3,
                                    "root": "kol", "text": "all", "cls": "rl"})
    _check("add should honor cls='rl'", '<span class="rl" data-root="kol">all</span>' in new, new)


# ------------------------------------------------------------------- retag

def test_retag_changes_root():
    html = _verse(5, 'the <span class="r" data-root="local-x">commander</span> of the army')
    new, msg = ar.apply_retag(html, {"unit": "unit-01", "verse": 5,
                                      "from": "local-x", "to": "devote",
                                      "text": "commander"})
    _check("retag should change data-root", 'data-root="devote">commander</span>' in new, new)
    _check("retag message starts with RTAG", msg.startswith("RTAG"), msg)


def test_retag_injects_w_when_converting_to_tracked():
    """A local span (no data-w) retagged onto a tracked thread must gain a
    data-w attribute when 'w' is supplied -- this is the case that motivated
    adding 'w' support to retag in the first place (§A / checklist 7)."""
    html = _verse(5, 'the <span class="r" data-root="local-x">commander</span> of the army')
    new, msg = ar.apply_retag(html, {"unit": "unit-01", "verse": 5,
                                      "from": "local-x", "to": "devote",
                                      "text": "commander", "w": "06UrB"})
    _check("retag should inject data-w",
           'data-root="devote" data-w="06UrB">commander</span>' in new, new)


def test_retag_updates_existing_w():
    html = _verse(5, 'the <span class="r" data-root="local-x" data-w="06wrong">'
                     'commander</span> of the army')
    new, msg = ar.apply_retag(html, {"unit": "unit-01", "verse": 5,
                                      "from": "local-x", "to": "devote",
                                      "text": "commander", "w": "06UrB"})
    _check("retag should update an existing data-w, not duplicate it",
           new.count("data-w=") == 1 and 'data-w="06UrB"' in new, new)


def test_retag_is_idempotent():
    html = _verse(5, 'the <span class="r" data-root="local-x">commander</span> of the army')
    once, _ = ar.apply_retag(html, {"unit": "unit-01", "verse": 5,
                                     "from": "local-x", "to": "devote",
                                     "text": "commander", "w": "06UrB"})
    twice, msg = ar.apply_retag(once, {"unit": "unit-01", "verse": 5,
                                        "from": "local-x", "to": "devote",
                                        "text": "commander", "w": "06UrB"})
    _check("re-applying retag should no-op", twice == once, (once, twice))
    _check("re-applying retag should say 'ok'", msg.startswith("ok"), msg)


def test_retag_miss_when_not_present():
    html = _verse(5, "the commander of the army")
    new, msg = ar.apply_retag(html, {"unit": "unit-01", "verse": 5,
                                      "from": "local-x", "to": "devote",
                                      "text": "commander"})
    _check("retag should MISS when the from-span isn't present",
           msg.startswith("MISS"), msg)


def test_retag_occ_picks_nth_duplicate_text():
    """Two untagged-w spans with the same root and the same English text in
    one verse (e.g. a Hebrew word occurring twice, each rendered 'possess')
    can't be told apart by a bare search -- 'occ' disambiguates them."""
    html = _verse(11, 'go in to <span class="r" data-root="possess">possess</span> '
                       'the land Yahweh is giving you to '
                       '<span class="r" data-root="possess">possess</span>')
    once, msg1 = ar.apply_retag(html, {"unit": "unit-01", "verse": 11,
                                        "from": "possess", "to": "possess",
                                        "text": "possess", "w": "06XyU", "occ": 1})
    twice, msg2 = ar.apply_retag(once, {"unit": "unit-01", "verse": 11,
                                         "from": "possess", "to": "possess",
                                         "text": "possess", "w": "06TW6", "occ": 2})
    _check("occ=1 should tag the first occurrence",
           'data-w="06XyU">possess</span> the land' in twice, twice)
    _check("occ=2 should tag the second occurrence, not re-tag the first",
           twice.count('data-w="06XyU"') == 1 and 'data-w="06TW6"' in twice, twice)


def test_retag_occ_is_idempotent():
    html = _verse(11, 'go in to <span class="r" data-root="possess">possess</span> '
                       'the land Yahweh is giving you to '
                       '<span class="r" data-root="possess">possess</span>')
    once, _ = ar.apply_retag(html, {"unit": "unit-01", "verse": 11,
                                     "from": "possess", "to": "possess",
                                     "text": "possess", "w": "06XyU", "occ": 1})
    once, _ = ar.apply_retag(once, {"unit": "unit-01", "verse": 11,
                                     "from": "possess", "to": "possess",
                                     "text": "possess", "w": "06TW6", "occ": 2})
    twice, msg = ar.apply_retag(once, {"unit": "unit-01", "verse": 11,
                                        "from": "possess", "to": "possess",
                                        "text": "possess", "w": "06TW6", "occ": 2})
    _check("re-applying occ=2 should no-op", twice == once, (once, twice))
    _check("re-applying occ=2 should say 'ok'", msg.startswith("ok"), msg)


# ------------------------------------------------------------------ unwrap

def test_unwrap_strips_span():
    html = _verse(5, 'the <span class="r" data-root="devote">commander</span> came')
    new, msg = ar.apply_unwrap(html, {"unit": "unit-01", "root": "devote",
                                       "text": "commander"})
    _check("unwrap should strip the data-root span",
           "data-root" not in new and "the commander came" in new, new)
    _check("unwrap message starts with UNWR", msg.startswith("UNWR"), msg)


# -------------------------------------------------------------- retag_word

def test_retag_word_bulk_reclassifies():
    html = (_verse(1, '<span class="r" data-root="local-x">kingdom</span>')
            + _verse(2, '<span class="r" data-root="local-x">kingdom</span>'))
    new, msg = ar.apply_retag_word(html, {"unit": "unit-01", "from": "local-x",
                                          "to": "reign", "match": "kingdom"})
    _check("retag_word should reclassify both occurrences",
           new.count('data-root="reign"') == 2, new)
    _check("retag_word message starts with RTAGW", msg.startswith("RTAGW"), msg)


def test_retag_word_preserves_existing_data_w():
    """retag_word never touches data-w -- see module docstring."""
    html = _verse(1, '<span class="r" data-root="local-x" data-w="06abc">kingdom</span>')
    new, msg = ar.apply_retag_word(html, {"unit": "unit-01", "from": "local-x",
                                          "to": "reign", "match": "kingdom"})
    _check("retag_word must leave data-w untouched", 'data-w="06abc"' in new, new)
    _check("retag_word must not duplicate data-w", new.count("data-w=") == 1, new)


# -------------------------------------------------------------- untag_word

def test_untag_word_by_match():
    html = _verse(1, '<span class="r" data-root="devote">devoted them</span>')
    new, msg = ar.apply_untag_word(html, {"unit": "unit-01", "root": "devote",
                                          "match": "devoted them"})
    _check("untag_word should strip the matching span",
           "data-root" not in new and "devoted them" in new, new)


# -------------------------------------------------------------------- text

def test_text_find_replace():
    html = _verse(1, "the LORD spoke")
    new, msg = ar.apply_text(html, {"unit": "unit-01", "from": "LORD", "to": "Yahweh"})
    _check("text should replace the wording", "Yahweh spoke" in new, new)
    _check("text message starts with TEXT", msg.startswith("TEXT"), msg)


def test_text_idempotent():
    html = _verse(1, "the LORD spoke")
    once, _ = ar.apply_text(html, {"unit": "unit-01", "from": "LORD", "to": "Yahweh"})
    twice, msg = ar.apply_text(once, {"unit": "unit-01", "from": "LORD", "to": "Yahweh"})
    _check("re-applying text should no-op", twice == once, (once, twice))
    _check("re-applying text should say 'ok'", msg.startswith("ok"), msg)


# -------------------------------------------------------------- strip_span

def test_strip_span_unwraps_class():
    html = _verse(1, 'a <span class="star">gold</span> motif')
    new, msg = ar.apply_strip_span(html, {"unit": "unit-01", "class": "star"})
    _check("strip_span should unwrap the class",
           'class="star"' not in new and "gold" in new, new)
    _check("strip_span message starts with STRIP", msg.startswith("STRIP"), msg)


# --------------------------------------------------------------- load_specs

def test_load_specs_merges_retro_spec(tmp_paths=None):
    """load_specs() must merge the retro spec (generated) into the
    hand-authored retrofit-tags.json's ops, without mutating the file on
    disk -- exercised via real temp files so the merge logic itself (not
    just the two JSON blobs) is under test."""
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        spec_path = os.path.join(d, "retrofit-tags.json")
        retro_path = os.path.join(d, "retro-tags.json")
        json.dump({"add": [{"unit": "unit-01", "verse": 1, "root": "kol",
                            "text": "all"}]}, open(spec_path, "w", encoding="utf-8"))
        json.dump({"add": [{"unit": "unit-02", "verse": 5, "root": "devote",
                            "text": "commander", "w": "06UrB"}]},
                  open(retro_path, "w", encoding="utf-8"))

        merged = ar.load_specs(spec_path, retro_path)

    _check("load_specs should merge both files' 'add' entries",
           len(merged.get("add", [])) == 2, merged)
    units = {e["unit"] for e in merged["add"]}
    _check("load_specs should keep entries from both files",
           units == {"unit-01", "unit-02"}, units)


# ------------------------------------------------------------------- runner

def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        before = len(fail)
        t()
        print(("  ok  " if len(fail) == before else "FAIL  ") + t.__name__)

    if fail:
        print(f"\nFAIL: {len(fail)} problem(s)")
        for f in fail:
            print(" -", f)
        sys.exit(1)
    print(f"\nPASS: {len(tests)} checks")


if __name__ == "__main__":
    main()
