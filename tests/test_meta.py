"""Regression tests for unit_meta.py's validate()/validate_fragment(),
reworked for phase-0.6-plan.md §F to match joshua_study_style_reference.md
(§3 the hard contract, §4 components, §7 the checklist) exactly. Proves
each hardened check fires (and that a clean fragment passes all of them).
No real unit fragments exist yet, so the fragment skeletons here are
synthetic -- but any Hebrew text embedded in them is pulled from
Joshua-reading.txt at test time, not hand-typed, same discipline as
pipeline/test_hebrew.py and verify_thread_coverage.py.
"""
import json
import os
import sys

import support  # noqa: E402
support.joshua_book()
from biblecore import meta as um  # noqa: E402

import re

ROOT = support.JOSHUA
READING_TXT = os.path.join(ROOT, "Joshua-reading.txt")
STYLE_REF_MD = os.path.join(ROOT, "joshua_study_style_reference.md")

fail = []


def _real_hebrew_word():
    """First word of Josh 1:1, pulled live from Joshua-reading.txt."""
    with open(READING_TXT, encoding="utf-8") as f:
        line = f.readline().rstrip("\n")
    _, verse = line.split("\t", 1)
    return verse.split(" ")[0]


HEB_WORD = _real_hebrew_word()  # וַ/יְהִ֗י as of this writing -- read, not typed

_EMPTY_THREADS = {"opens": [], "payoffs": [], "candidates": [], "retro": []}

# threads.json / roots.json fixtures a few checks need -- synthetic, self-
# contained (no real threads/roots exist yet).
_THREADS_JSON = {"threads": [{"id": "strong", "root": "strong"}]}


def _meta(**overrides):
    base = {
        "unit": 1,
        "slug": "unit-01",
        "passage": "Joshua 1:1-18",
        "title": "Commission",
        "roots": [{"root": "strong", "translit": "chazak", "gloss": "be strong"}],
        "threads": dict(_EMPTY_THREADS),
    }
    base.update(overrides)
    return base


def _fragment(meta, body_extra="", legend_class="block legend"):
    body = json.dumps(meta, indent=2, ensure_ascii=False)
    return (
        '<article class="unit">\n'
        f'<script type="application/json" id="unit-meta">\n{body}\n</script>\n'
        f'<h3 class="pericope">Commission <span>· 1:1-18</span></h3>\n'
        f'<section class="{legend_class}"><ul><li class="r">strong</li></ul></section>\n'
        '<p class="v"><span class="n">1</span> text'
        '<sup><a href="#u01-n1">1</a></sup></p>\n'
        '<section class="block notes"><p id="u01-n1">note text.</p></section>\n'
        f'{body_extra}'
        '</article>\n'
    )


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


# ----------------------------------------------------------------- check 1

def test_unknown_top_level_key():
    meta = _meta(movement=2)  # allowed, documented
    errs = um.validate(meta)
    _check("known-optional-key (movement) should not fail", not errs, errs)

    meta = _meta(footnote_style="chicago")  # NOT in ALLOWED_TOP_LEVEL_KEYS
    errs = um.validate(meta)
    _check("unknown top-level key must hard-fail",
           any("footnote_style" in e for e in errs), errs)


def test_descriptor_and_discourse_rejected():
    """§3's table has no descriptor/discourse -- this fork used to allow
    both; they must now hard-fail like any other unknown key."""
    for key, value in (("descriptor", "the masthead line"), ("discourse", True)):
        meta = _meta(**{key: value})
        errs = um.validate(meta)
        _check(f"'{key}' must be rejected (removed from ALLOWED_TOP_LEVEL_KEYS)",
               any(key in e for e in errs), errs)


def test_clean_meta_passes():
    errs = um.validate(_meta())
    _check("clean, minimal meta should validate with no errors", not errs, errs)


def test_threads_missing_subkey_fails():
    meta = _meta(threads={"opens": [], "payoffs": [], "candidates": []})  # no retro
    errs = um.validate(meta)
    _check("threads missing a required sub-key (retro) must fail",
           any("threads.retro" in e for e in errs), errs)


# ------------------------------------------------------- opens/payoffs note

def test_opens_missing_note_fails():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "opens": [{"id": "strong", "ref": "1:6"}]})  # no note
    errs = um.validate(meta)
    _check("threads.opens[] entry missing 'note' must fail",
           any("threads.opens[0]" in e and "note" in e for e in errs), errs)


def test_opens_with_note_passes():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "opens": [{"id": "strong", "ref": "1:6", "note": "be strong"}]})
    errs = um.validate(meta)
    _check("threads.opens[] entry with a note should not fail on that account",
           not any("note" in e for e in errs), errs)


# --------------------------------------------------------------- candidates

def test_candidates_missing_why_fails():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "give"}]})  # no why
    errs = um.validate(meta)
    _check("threads.candidates[] entry missing 'why' must fail",
           any("why" in e for e in errs), errs)


# --------------------------------------------------------------- questions

def test_root_echo_accepted():
    m = _meta(roots=[{"root": "sole", "translit": "kap regel", "gloss": "sole of the foot",
                      "echo": "Gen 8:9 — the dove found no resting place"}])
    errs = um.validate(m)
    _check("a root with a string echo must validate", not errs, errs)


def test_root_echo_must_be_nonempty_string():
    for bad in ("", "   ", ["Gen 8:9"], 3):
        m = _meta(roots=[{"root": "sole", "translit": "kap regel", "gloss": "g", "echo": bad}])
        errs = um.validate(m)
        _check(f"root echo {bad!r} must fail", any("echo" in e for e in errs), errs)


def test_root_unknown_key_rejected():
    m = _meta(roots=[{"root": "sole", "translit": "kap regel", "gloss": "g", "note": "x"}])
    errs = um.validate(m)
    _check("an unknown key on a root must fail loudly, not be dropped on regen",
           any("unknown key 'note'" in e for e in errs), errs)


def test_questions_clean_entry_passes():
    meta = _meta(questions=[{"topic": "ḥerem rendering",
                              "note": "devoted to destruction vs. transliterated?",
                              "options": ["devoted to destruction", "ḥerem, glossed"]}])
    errs = um.validate(meta)
    _check("a well-formed questions[] entry should not fail",
           not errs, errs)


def test_questions_missing_topic_fails():
    meta = _meta(questions=[{"note": "which rendering?"}])  # no topic
    errs = um.validate(meta)
    _check("questions[] entry missing 'topic' must fail",
           any("questions[0]" in e and "topic" in e for e in errs), errs)


def test_questions_missing_note_fails():
    meta = _meta(questions=[{"topic": "ḥerem rendering"}])  # no note
    errs = um.validate(meta)
    _check("questions[] entry missing 'note' must fail",
           any("questions[0]" in e and "note" in e for e in errs), errs)


def test_questions_options_must_be_string_list():
    meta = _meta(questions=[{"topic": "x", "note": "y", "options": "not a list"}])
    errs = um.validate(meta)
    _check("questions[] 'options' must be a list of strings",
           any("options" in e for e in errs), errs)


def test_questions_is_dropped_by_generate():
    """questions[] is consumed at port time and never re-emitted -- a
    regenerated fragment should carry none, same as candidates/retro."""
    units_json = {"units": [{"n": 1, "slug": "unit-01", "passage": "Joshua 1:1-18",
                              "title": "Commission", "movement": 1, "roots": {}}]}
    threads_json = {"threads": []}
    meta = um.generate(1, units_json=units_json, threads_json=threads_json)
    _check("generate() never adds a 'questions' key",
           "questions" not in meta, meta)


def test_candidates_stems_exclude_rejected():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "give", "why": "testing",
                                         "stems": ["x"], "exclude": ["y"]}]})
    errs = um.validate(meta)
    _check("threads.candidates[] 'stems' must be rejected",
           any("'stems'" in e for e in errs), errs)
    _check("threads.candidates[] 'exclude' must be rejected",
           any("'exclude'" in e for e in errs), errs)


def test_candidates_tsv_id_spelling_normalized():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "wrath", "why": "testing",
                                         "ids": ["6485 a", "7110", "2763a"]}]})
    notes = um.normalize_candidates(meta)
    ids = meta["threads"]["candidates"][0]["ids"]
    _check("'6485 a' (word-table spelling) must normalize to '6485a'",
           ids == ["6485a", "7110", "2763a"], ids)
    _check("one note per rewritten id", len(notes) == 1, notes)
    _check("normalized candidate must then validate",
           not um.validate(meta), um.validate(meta))
    _check("normalize is a no-op on meta without candidates",
           um.normalize_candidates(_meta()) == [])


def test_candidates_ids_refs_valid_passes():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "give", "why": "testing",
                                         "ids": ["5414", "2763a"], "refs": ["6:5", "6:20"]}]})
    errs = um.validate(meta)
    _check("threads.candidates[] with valid ids/refs should pass", not errs, errs)


def test_candidates_ids_bad_format_fails():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "give", "why": "testing",
                                         "ids": ["not-an-id"]}]})
    errs = um.validate(meta)
    _check("threads.candidates[] malformed 'ids' entry must fail",
           any("'ids'" in e for e in errs), errs)


def test_candidates_refs_bad_format_fails():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "give", "why": "testing",
                                         "refs": ["chapter six verse five"]}]})
    errs = um.validate(meta)
    _check("threads.candidates[] malformed 'refs' entry must fail",
           any("'refs'" in e for e in errs), errs)


# ------------------------------------------------------------------- retro

def test_retro_add_tracked_root_without_w_passes():
    """`w` is optional in the incoming artifact (review A6).

    The chat side is instructed not to hand-chase word ids, so requiring
    `w` here made the contract unsatisfiable from that end.
    assign_data_w.py fills them during the port, and the guarantee that a
    shipped tracked span carries data-w is enforced on the built fragment
    by check_tracked_spans_have_data_w() instead.
    """
    meta = _meta(threads={**_EMPTY_THREADS,
                          "retro": [{"unit": "unit-02", "verse": 5, "text": "gave",
                                    "root": "strong", "why": "testing"}]})  # no w
    errs = um.validate(meta, threads_json=_THREADS_JSON)
    _check("retro 'add' onto a tracked thread may omit 'w'",
           not any("'w'" in e for e in errs), errs)


def test_retro_add_tracked_root_with_w_passes():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "retro": [{"unit": "unit-02", "verse": 5, "text": "gave",
                                    "root": "strong", "why": "testing", "w": "06abc"}]})
    errs = um.validate(meta, threads_json=_THREADS_JSON)
    _check("retro 'add' targeting a tracked thread with a valid 'w' should pass",
           not any("valid 'w'" in e for e in errs), errs)


def test_retro_retag_tracked_root_may_omit_w():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "retro": [{"unit": "unit-02", "verse": 5, "text": "gave",
                                    "from": "local-only", "to": "strong",
                                    "op": "retag", "why": "testing"}]})
    errs = um.validate(meta, threads_json=_THREADS_JSON)
    _check("retro 'retag' onto a tracked thread may omit 'w'",
           not any("'w'" in e for e in errs), errs)


def test_retro_local_root_needs_no_w():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "retro": [{"unit": "unit-02", "verse": 5, "text": "gave",
                                    "root": "local-only", "why": "testing"}]})
    errs = um.validate(meta, threads_json={"threads": []})
    _check("retro targeting a non-tracked (local) root needs no 'w'",
           not any("'w'" in e for e in errs), errs)


def test_retro_malformed_w_fails():
    meta = _meta(threads={**_EMPTY_THREADS,
                          "retro": [{"unit": "unit-02", "verse": 5, "text": "gave",
                                    "root": "strong", "why": "testing", "w": "!!not-an-id"}]})
    errs = um.validate(meta, threads_json=_THREADS_JSON)
    _check("retro with a malformed 'w' must still fail",
           any("not a valid word id" in e for e in errs), errs)


# -------------------------------------------------------------------- roots

def test_roots_kind_members_rejected():
    meta = _meta(roots=[{"root": "strong", "translit": "chazak", "gloss": "be strong",
                         "kind": "verb"}])
    errs = um.validate(meta)
    _check("roots[] 'kind' must be rejected",
           any("kind" in e for e in errs), errs)


# ----------------------------------------------------------------- check 2

def test_component_whitelist_unstyled_class():
    html = _fragment(_meta(), body_extra='<div class="not-a-real-class">x</div>\n')
    errs = um.validate_fragment(html)
    _check("class absent from css/styles.css must fail",
           any("not-a-real-class" in e for e in errs), errs)


def test_component_whitelist_missing_legend():
    body = (
        '<article class="unit">\n'
        f'<script type="application/json" id="unit-meta">\n{json.dumps(_meta())}\n</script>\n'
        '<p class="v"><span class="n">1</span> text</p>\n'
        '</article>\n'
    )
    errs = um.validate_fragment(body)
    _check("fragment missing required 'legend' component must fail",
           any("legend" in e and "missing" in e.lower() for e in errs), errs)


def test_component_whitelist_legend_without_block_fails():
    """The legend must be section.block.legend -- both classes required,
    not just 'legend' (style reference §4). Built without _fragment()'s
    default notes section, which would otherwise supply a 'block' class
    from elsewhere and mask this check."""
    body = (
        '<article class="unit">\n'
        f'<script type="application/json" id="unit-meta">\n{json.dumps(_meta())}\n</script>\n'
        '<section class="legend"><ul><li class="r">strong</li></ul></section>\n'
        '<p class="v"><span class="n">1</span> text</p>\n'
        '</article>\n'
    )
    errs = um.validate_fragment(body)
    _check("legend present without 'block' must still fail (block missing)",
           any("'block'" in e and "missing" in e.lower() for e in errs), errs)


def test_component_whitelist_clean_fragment_passes():
    html = _fragment(_meta())
    errs = um.check_component_whitelist(html)
    _check("clean fragment (whitelisted classes + block+legend present) should "
           "pass the component-whitelist check", not errs, errs)


# ----------------------------------------------------------------- check 3

def test_endnote_mismatch_orphan_id():
    html = _fragment(_meta()).replace(
        '<p id="u01-n1">note text.</p>',
        '<p id="u01-n2">note text.</p>',  # id with no matching href
    )
    errs = um.check_endnote_integrity(html)
    _check("id with no matching href must fail",
           any("u01-n2" in e and "href" in e for e in errs), errs)


def test_endnote_mismatch_orphan_href():
    html = _fragment(_meta()).replace(
        '<sup><a href="#u01-n1">1</a></sup>',
        '<sup><a href="#u01-n2">1</a></sup>',  # href with no matching id
    )
    errs = um.check_endnote_integrity(html)
    _check("href with no matching id must fail",
           any("u01-n2" in e and "id=" in e for e in errs), errs)


def test_endnote_balanced_pair_passes():
    html = _fragment(_meta())
    errs = um.check_endnote_integrity(html)
    _check("balanced id/href endnote pair should pass", not errs, errs)


# ----------------------------------------------------------------- check 4

def test_hebrew_script_in_text_node_fails():
    html = _fragment(_meta(), body_extra=f'<div class="v">{HEB_WORD}</div>\n')
    errs = um.check_no_native_script(html)
    _check("Hebrew script in a fragment text node must fail", len(errs) == 1, errs)


def test_hebrew_script_in_candidates_no_longer_exempt():
    """This fork used to exempt threads.candidates[].stems -- that field
    doesn't exist in the schema anymore (§3: ids/refs only), and no field
    is exempt now (checklist 12: no exceptions). Hebrew anywhere in the
    meta block, including inside a candidate's own text, must fail."""
    meta = _meta(threads={**_EMPTY_THREADS,
                          "candidates": [{"root": "test-root", "why": HEB_WORD}]})
    html = _fragment(meta)
    errs = um.check_no_native_script(html)
    _check("Hebrew script anywhere in threads.candidates[] must fail (no exemption)",
           len(errs) == 1, errs)


def test_greek_script_fails_too():
    """Core checks every original-language script, not just the book's own:
    a Hebrew book quoting the LXX still transliterates."""
    greek = chr(0x03BB) + chr(0x03CC) + chr(0x03B3) + chr(0x03BF) + chr(0x03C2)
    html = _fragment(_meta(), body_extra=f'<div class="v">{greek}</div>\n')
    errs = um.check_no_native_script(html)
    _check("Greek script in a fragment must fail", len(errs) == 1, errs)


_TABLE = ('<section class="block"><h2>Count <span class="cap">· 1:20–46</span></h2>'
          '<table class="list"><thead><tr><th>Tribe</th><th>Count</th></tr></thead>'
          '<tbody><tr><td>Reuven</td><td>46,500</td></tr></tbody>'
          '<tfoot><tr><td>Total</td><td>603,550</td></tr></tfoot></table></section>')


def test_table_list_clean_passes():
    errs = um.check_table_list(_TABLE)
    _check("a wrapped table.list with a header row passes", not errs, errs)


def test_table_list_outside_block_fails():
    bare = _TABLE.replace('<section class="block">', "").replace("</section>", "")
    errs = um.check_table_list(bare)
    _check("table.list outside section.block must fail",
           any("section class" in e for e in errs), errs)
    closed = '<section class="block"></section>' + bare
    errs = um.check_table_list(closed)
    _check("a section.block closed before the table doesn't count",
           any("section class" in e for e in errs), errs)


def test_table_list_needs_header_row():
    errs = um.check_table_list(_TABLE.replace("<th>", "<td>").replace("</th>", "</td>"))
    _check("table.list without a <th> header row must fail",
           any("header row" in e for e in errs), errs)


def test_table_list_ragged_rows_fail():
    errs = um.check_table_list(_TABLE.replace("<td>46,500</td>", "<td>1:21</td><td>46,500</td>"))
    _check("table.list rows with different cell counts must fail",
           any("same count" in e for e in errs), errs)


def test_declared_verses_clean():
    m = _meta()
    html = _fragment(m, body_extra='<table class="list" data-verses="1:2–17"></table>\n')
    errs = um.check_declared_verses(html, m)
    _check("a well-formed declaration inside the passage should pass", not errs, errs)
    _check("declared_ranges parses it",
           um.declared_ranges(html) == [((1, 2), (1, 17))], um.declared_ranges(html))


def test_declared_verses_malformed_fails():
    m = _meta()
    for bad in ("22-43", "1:43–22", "one"):
        html = _fragment(m, body_extra=f'<table class="list" data-verses="{bad}"></table>\n')
        errs = um.check_declared_verses(html, m)
        _check(f"data-verses={bad!r} must fail", len(errs) == 1, errs)


def test_declared_verses_outside_passage_fails():
    m = _meta()
    html = _fragment(m, body_extra='<table class="list" data-verses="2:1–3"></table>\n')
    errs = um.check_declared_verses(html, m)
    _check("a declaration outside the passage must fail",
           any("outside" in e for e in errs), errs)


def test_declared_verse_also_written_out_fails():
    """_fragment writes verse 1 as a .v block, so declaring 1:1 would excuse
    a verse that is really there from the audit."""
    m = _meta()
    html = _fragment(m, body_extra='<table class="list" data-verses="1:1–5"></table>\n')
    errs = um.check_declared_verses(html, m)
    _check("a declared verse that is also a verse block must fail",
           any("written out" in e for e in errs), errs)


def test_clean_fragment_no_hebrew():
    html = _fragment(_meta())
    errs = um.check_no_native_script(html)
    _check("clean fragment with no Hebrew anywhere should pass", not errs, errs)


# ------------------------------------------------------- checklist 6, 7, 9, 13

def test_data_root_resolves_via_threads_json():
    html = _fragment(_meta(), body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="strong" data-w="x">strong</span></p>\n')
    errs = um.check_data_root_resolves(html, meta=_meta(), threads_json=_THREADS_JSON)
    _check("data-root matching a threads.json thread's root should resolve",
           not errs, errs)


def test_data_root_resolves_via_own_roots():
    meta = _meta(roots=[{"root": "local-only", "translit": "x", "gloss": "y"}])
    html = _fragment(meta, body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="local-only">strong</span></p>\n')
    errs = um.check_data_root_resolves(html, meta=meta, threads_json={"threads": []})
    _check("data-root matching this fragment's own roots[] should resolve",
           not errs, errs)


def test_data_root_unresolved_fails():
    html = _fragment(_meta(), body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="nowhere" data-w="x">strong</span></p>\n')
    errs = um.check_data_root_resolves(html, meta=_meta(), threads_json={"threads": []})
    _check("data-root resolving to nothing must fail (checklist 6)",
           any("nowhere" in e for e in errs), errs)


def test_tracked_span_missing_data_w_fails():
    html = _fragment(_meta(), body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="strong">strong</span></p>\n')
    errs = um.check_tracked_spans_have_data_w(html, threads_json=_THREADS_JSON)
    _check("tracked-thread span with no data-w must fail (checklist 7)",
           any("strong" in e for e in errs), errs)


def test_tracked_span_with_data_w_passes():
    html = _fragment(_meta(), body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="strong" data-w="06abc">strong</span></p>\n')
    errs = um.check_tracked_spans_have_data_w(html, threads_json=_THREADS_JSON)
    _check("tracked-thread span with data-w should pass", not errs, errs)


def test_local_span_without_data_w_is_fine():
    html = _fragment(_meta(), body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="local-only">x</span></p>\n')
    errs = um.check_tracked_spans_have_data_w(html, threads_json={"threads": []})
    _check("a span for a root NOT in threads.json needs no data-w",
           not errs, errs)


def test_pericope_heading_with_range_passes():
    html = '<h3 class="pericope">Title <span>· 6:1–5</span></h3>'
    errs = um.check_pericope_headings(html)
    _check("pericope heading with a C:V range should pass", not errs, errs)


def test_pericope_heading_missing_range_fails():
    html = '<h3 class="pericope">Title with no range</h3>'
    errs = um.check_pericope_headings(html)
    _check("pericope heading missing its C:V range must fail (checklist 9)",
           len(errs) == 1, errs)


_ECHO_META = {"passage": "Joshua 3:1-17"}


def test_echo_clean_passes():
    html = ('<p class="v"><span class="n">3:2</span> text.</p>'
            '<aside class="echo" data-anchor="3:2">cf. Deut 27:2-4, the '
            'command this fulfils.</aside>')
    errs = um.check_echo(html, _ECHO_META)
    _check("a clean aside.echo with a matching anchor should pass",
           not errs, errs)


def test_echo_missing_anchor_fails():
    html = ('<p class="v"><span class="n">3:2</span> t.</p>'
            '<aside class="echo">no anchor</aside>')
    errs = um.check_echo(html, _ECHO_META)
    _check("aside.echo with no data-anchor must fail",
           any("no data-anchor" in e for e in errs), errs)


def test_echo_malformed_anchor_fails():
    html = ('<p class="v"><span class="n">3:2</span> t.</p>'
            '<aside class="echo" data-anchor="three-two">x</aside>')
    errs = um.check_echo(html, _ECHO_META)
    _check("aside.echo with a malformed data-anchor must fail",
           any("is not 'C:V'" in e for e in errs), errs)


def test_echo_anchor_mismatched_with_verse_fails():
    html = ('<p class="v"><span class="n">3:2</span> t.</p>'
            '<aside class="echo" data-anchor="3:5">x</aside>')
    errs = um.check_echo(html, _ECHO_META)
    _check("aside.echo data-anchor that doesn't match the verse it "
           "follows must fail",
           any("doesn't match the verse" in e for e in errs), errs)


def test_echo_nested_inside_unclosed_gloss_fails():
    """The exact 67b2712 regression: an aside spliced into gloss content
    that was never properly closed collapsed silently in the browser."""
    html = ('<p class="v"><span class="n">3:2</span> text.</p>'
            '<span class="gloss">discussion '
            '<aside class="echo" data-anchor="3:2">nested!</aside>'
            ' more text</span>')
    errs = um.check_echo(html, _ECHO_META)
    _check("aside.echo nested inside an unclosed .gloss span must fail "
           "(67b2712)",
           any("67b2712" in e for e in errs), errs)


def test_echo_bare_verse_number_rollover():
    """Bare `<span class="n">2</span>` inherits the chapter from the
    nearest preceding explicit C:V, same convention as
    assign_data_w.verse_blocks()."""
    html = ('<p class="v"><span class="n">3:1</span> a</p>'
            '<p class="v"><span class="n">2</span> b</p>'
            '<aside class="echo" data-anchor="3:2">x</aside>')
    errs = um.check_echo(html, _ECHO_META)
    _check("a bare verse number should still resolve to the right "
           "chapter for anchor matching",
           not errs, errs)


def test_echo_unclosed_aside_fails():
    html = ('<p class="v"><span class="n">3:2</span> t.</p>'
            '<aside class="echo" data-anchor="3:2">never closed')
    errs = um.check_echo(html, _ECHO_META)
    _check("an aside.echo missing its closing tag must fail",
           any("open/close count mismatch" in e for e in errs), errs)


def test_echo_class_is_in_css_whitelist():
    """echo must be a real css/styles.css class, not just accepted by
    check_echo() -- otherwise check_component_whitelist() would reject
    any fragment that actually uses it."""
    classes = um._css_classes()
    _check("'echo' must be defined in css/styles.css",
           classes is not None and "echo" in classes, classes)


def test_no_inline_style_fails():
    html = '<div style="color: red">x</div>'
    errs = um.check_no_inline_style(html)
    _check("inline style= must fail (checklist 13)",
           any("style=" in e for e in errs), errs)


def test_css_var_fails():
    html = '<div class="r" data-root="give">x</div><style>.r{color:var(--c-give)}</style>'
    errs = um.check_no_inline_style(html)
    _check("--c-* colour var must fail (checklist 13)",
           any("--c-give" in e for e in errs), errs)


def test_clean_fragment_no_inline_style():
    html = _fragment(_meta())
    errs = um.check_no_inline_style(html)
    _check("clean fragment should have no inline style/--c-* var issues",
           not errs, errs)


def test_rl_inside_verse_block_warns():
    html = ('<p class="v"><span class="n">1</span> '
            '<span class="rl" data-root="give">natan</span></p>')
    warnings = um.warnings_for_fragment(html)
    _check("class=\"rl\" inside a .v block should produce a warning (§4)",
           len(warnings) == 1, warnings)
    # This must be a WARNING, not a hard validate_fragment() failure.
    hard_errs = [e for e in um.validate_fragment(html) if "rl" in e]
    _check("rl-inside-verse-block must NOT be a hard validate_fragment() failure",
           not hard_errs, hard_errs)


def test_rl_outside_verse_block_is_clean():
    html = ('<p class="v"><span class="n">1</span> text</p>\n'
            '<span class="gloss"><span class="rl" data-root="give">natan</span></span>')
    warnings = um.warnings_for_fragment(html)
    _check("class=\"rl\" outside a .v block should not warn", not warnings, warnings)


def test_clean_fragment_passes_validate_fragment_fully():
    """The whole validate_fragment() pipeline together, on one clean
    fragment with a tracked-thread span correctly tagged."""
    meta = _meta()
    html = _fragment(meta, body_extra=
                      '<p class="v"><span class="n">2</span> '
                      '<span class="r" data-root="strong" data-w="06abc">strong</span></p>\n')
    errs = um.validate_fragment(html, meta=meta, threads_json=_THREADS_JSON)
    _check("a fully clean fragment should pass validate_fragment() with no errors",
           not errs, errs)


# --------------------------------------------------------- generate() round-trip

def test_generate_output_validates_clean():
    """generate()'s own output must satisfy validate() -- the same
    all-four-threads-subkeys requirement that bit this fork once already
    (generate() omitted 'retro' until this test caught it)."""
    units_json = {
        "book": "Joshua",
        "units": [{"n": 1, "slug": "unit-01", "passage": "Joshua 1:1-18",
                   "title": "Rights of Passage", "movement": 1}],
    }
    threads_json = {"threads": []}
    meta = um.generate(1, units_json=units_json, threads_json=threads_json)
    errs = um.validate(meta, threads_json=threads_json)
    _check("generate()'s output must validate clean", not errs, errs)


def test_generate_round_trips_opens_and_payoffs_notes():
    """The same round-trip, but with threads that actually touch the unit.

    The empty-threads fixture above passed all the way through the A1 bug:
    generate() built opens/payoffs entries as {id, ref} while validate()
    required a `note` on both, so every refresh_meta run wrote unit-01 into
    a shape the project's own validator rejected -- and no test noticed,
    because with zero threads there were zero entries to get wrong.
    """
    units_json = {
        "book": "Joshua",
        "units": [{"n": 1, "slug": "unit-01", "passage": "Joshua 1:1-18",
                   "title": "Rights of Passage", "movement": 1}],
    }
    threads_json = {"threads": [
        {"id": "give", "root": "give", "translit": "natan", "gloss": "give",
         "color": "#b1481f", "status": "open", "tagged": True,
         "opens": {"unit": 1, "ref": "1:2", "note": "the land as gift."},
         "payoffs": [], "note": "natan across the book."},
        {"id": "rest", "root": "rest", "translit": "nuakh", "gloss": "rest",
         "color": "#2f5f6b", "status": "open", "tagged": True,
         "opens": {"unit": 0, "ref": "0:0", "note": "opens elsewhere."},
         "payoffs": [{"unit": 1, "ref": "1:13", "note": "rest promised."}],
         "note": "nuakh across the book."},
    ]}
    meta = um.generate(1, units_json=units_json, threads_json=threads_json)
    errs = um.validate(meta, threads_json=threads_json)
    _check("generate() must validate clean with threads touching the unit",
           not errs, errs)

    opens = meta["threads"]["opens"]
    _check("generate() must carry opens.note through from threads.json",
           opens and opens[0].get("note") == "the land as gift.", opens)
    payoffs = meta["threads"]["payoffs"]
    _check("generate() must carry payoffs[].note through from threads.json",
           payoffs and payoffs[0].get("note") == "rest promised.", payoffs)


# --------------------------------------------------- §8 worked-example contract

def _extract_worked_example():
    """Pull the §8 worked example's fenced ```html block straight out of
    joshua_study_style_reference.md at test time -- not copied into this
    file, so the two can never quietly drift apart (phase-0.6-plan.md §G:
    "this test is the contract between the style reference and the
    validator; if either drifts, it fails")."""
    with open(STYLE_REF_MD, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"## 8\. Worked example.*?```html\n(.*?)```", text, re.S)
    if not m:
        raise AssertionError(
            "could not find the §8 worked example's fenced ```html block in "
            "joshua_study_style_reference.md -- did the heading or fence "
            "syntax change?"
        )
    return m.group(1)


def test_worked_example_validates_clean():
    """The §8 worked example, run through validate() and validate_fragment()
    against a threads.json fixture declaring 'devote' and 'give', must pass
    with zero errors. If this ever fails, either the style reference's
    worked example or this validator has drifted from the other."""
    html = _extract_worked_example()
    meta = um.parse(html)
    _check("§8 worked example's meta block must parse as JSON", meta is not None)
    if meta is None:
        return

    threads_json = {"threads": [{"id": "devote", "root": "devote"},
                                {"id": "give", "root": "give"}]}
    errs = um.validate(meta, threads_json=threads_json)
    errs += um.validate_fragment(html, meta=meta, threads_json=threads_json)
    _check("§8 worked example must validate clean against a devote/give "
           "threads.json fixture", not errs, errs)


# ------------------------------------------------------------------- runner

def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        before = len(fail)
        t()
        if len(fail) == before:
            print(f"  ok  {t.__name__}")
        else:
            print(f"FAIL  {t.__name__}")

    if fail:
        print(f"\nFAIL: {len(fail)} problem(s)")
        for f in fail:
            print(" -", f)
        sys.exit(1)
    print(f"\nPASS: {len(tests)} checks")


if __name__ == "__main__":
    main()
