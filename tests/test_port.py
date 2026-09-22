"""End-to-end test for the porter, run against a scratch book so nothing
touches a real registry. Uses Joshua's style reference §8 worked example as
the incoming artifact -- real, internally consistent content that exercises
roots, tracked-thread opens/payoffs, a candidate with real ids, and a retro
fix targeting an earlier unit. The scratch book borrows Joshua's word table,
reading text and stylesheet (read-only); everything it writes is in a temp
dir. run_retrofit_and_scan is stubbed: those steps have their own tests.
"""
import json
import os
import re
import sys
import tempfile

import support  # noqa: E402
from biblecore import book as bookmod  # noqa: E402
from biblecore import meta as um  # noqa: E402
from biblecore import port as pa  # noqa: E402

STYLE_REF_MD = os.path.join(support.JOSHUA, "joshua_study_style_reference.md")

fail = []


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


def _extract_worked_example():
    with open(STYLE_REF_MD, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"## 8\. Worked example.*?```html\n(.*?)```", text, re.S)
    if not m:
        raise AssertionError("could not find the §8 worked example")
    return m.group(1)


class _ScratchProject:
    """Sets up a scratch source-artifacts/units/data/pipeline-out tree and
    monkeypatches every module-level path global that needs to point at it,
    restoring everything on exit."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.src = os.path.join(d, "source-artifacts")
        self.units = os.path.join(d, "units")
        self.data = os.path.join(d, "data")
        self.out = os.path.join(d, "pipeline_out")
        for p in (self.src, self.units, self.data, self.out):
            os.makedirs(p, exist_ok=True)
        self.retro_spec = os.path.join(d, "retro-tags.json")

        # -- seed scratch data files --
        json.dump({
            "book": "Joshua", "unit_count": 1, "movements": [], "discourses": [],
            "units": [{"n": 5, "slug": "unit-05", "passage": "Joshua 5:1-15",
                       "title": "Gilgal", "movement": 1, "built": True}],
        }, open(os.path.join(self.data, "units.json"), "w", encoding="utf-8"))
        json.dump({"threads": [
            {"id": "devote", "root": "devote", "tagged": False, "status": "open"},
            {"id": "give", "root": "give", "tagged": False, "status": "open"},
        ]}, open(os.path.join(self.data, "threads.json"), "w", encoding="utf-8"))
        json.dump({"version": 1, "roots": {
            "devote": {"ids": ["2764"], "note": "ban, devote to destruction"},
            "give": {"ids": ["5414"], "note": "give, hand over"},
        }}, open(os.path.join(self.data, "roots.json"), "w", encoding="utf-8"))

        # unit-05 fragment: needs "commander" free in verse 14, matching the
        # worked example's retro fix target.
        open(os.path.join(self.units, "unit-05.html"), "w", encoding="utf-8").write(
            '<article class="unit" data-unit="5">\n'
            '<p class="v"><span class="n">14</span> "I am the commander of '
            'the army of Yahweh."</p>\n'
            '</article>\n'
        )

        # incoming artifact: the real §8 worked example
        open(os.path.join(self.src, "joshua_06_translation.html"), "w",
             encoding="utf-8").write(_extract_worked_example())

        cfg = json.load(open(support.FIXTURE, encoding="utf-8"))
        cfg["palette"] = os.path.join(support.HERE, "joshua_well.json")
        J = support.JOSHUA
        cfg["paths"] = {
            "out": self.out, "retro": self.retro_spec,
            "retrofit": os.path.join(d, "retrofit-tags.json"),
            "words": os.path.join(J, "Joshua-words.tsv"),
            "reading": os.path.join(J, "Joshua-reading.txt"),
            "css": os.path.join(J, "css", "styles.css"),
        }
        self._prev = bookmod._current
        bookmod.use(bookmod.Book(cfg, d))
        self._orig_run = pa.run_retrofit_and_scan
        pa.run_retrofit_and_scan = lambda: True
        return self

    def __exit__(self, *exc):
        pa.run_retrofit_and_scan = self._orig_run
        bookmod.use(self._prev)
        self.tmp.cleanup()

    def read(self, *parts):
        return open(os.path.join(self.tmp.name, *parts), encoding="utf-8").read()

    def path(self, *parts):
        return os.path.join(self.tmp.name, *parts)


def test_dry_run_writes_nothing():
    with _ScratchProject() as sp:
        pa.port_one(6, dry=True, src=None)
        _check("dry run should not write the fragment",
               not os.path.exists(os.path.join(sp.units, "unit-06.html")), None)
        units_after = json.load(open(os.path.join(sp.data, "units.json"), encoding="utf-8"))
        _check("dry run should not modify units.json",
               all(u["n"] != 6 for u in units_after["units"]), units_after)
        delta_path = os.path.join(sp.out, "thread-delta-06.md")
        _check("dry run should still write the thread-delta report",
               os.path.exists(delta_path), delta_path)


def test_real_port_writes_fragment_and_merges_units_json():
    with _ScratchProject() as sp:
        pa.port_one(6, dry=False, src=None)

        frag_path = os.path.join(sp.units, "unit-06.html")
        _check("real port should write the fragment", os.path.exists(frag_path), frag_path)
        frag = open(frag_path, encoding="utf-8").read()
        _check("fragment should carry data-unit=\"6\"", 'data-unit="6"' in frag, frag[:200])
        _check("fragment should be a single article with an injected meta block",
               um.parse(frag) is not None, frag[:400])

        uj = json.load(open(os.path.join(sp.data, "units.json"), encoding="utf-8"))
        row = next((u for u in uj["units"] if u["n"] == 6), None)
        _check("unit 6 should be merged into units.json", row is not None, uj)
        _check("unit 6 should be marked built", row and row.get("built") is True, row)
        _check("unit 6 passage should match the worked example",
               row and row["passage"] == "Joshua 6:1–27", row)


def test_real_port_fragment_validates_clean():
    with _ScratchProject() as sp:
        pa.port_one(6, dry=False, src=None)
        frag = open(os.path.join(sp.units, "unit-06.html"), encoding="utf-8").read()
        meta = um.parse(frag)
        threads_json = json.load(open(os.path.join(sp.data, "threads.json"), encoding="utf-8"))
        errs = um.validate(meta, threads_json=threads_json)
        _check("the ported fragment's meta must validate clean", not errs, errs)
        frag_errs = um.validate_fragment(frag, meta=meta, threads_json=threads_json)
        _check("the ported fragment itself must validate clean", not frag_errs, frag_errs)


def test_real_port_merges_retro_into_earlier_unit_target():
    """The worked example's retro entry (unit-05, op add, root devote,
    w=06UrB, text 'commander') should dry-check clean against the scratch
    unit-05 fragment (which has 'commander' free in verse 14) and get
    merged into retro-tags.json."""
    with _ScratchProject() as sp:
        pa.port_one(6, dry=False, src=None)
        _check("retro-tags.json should be written", os.path.exists(sp.retro_spec),
               sp.retro_spec)
        rt = json.load(open(sp.retro_spec, encoding="utf-8"))
        adds = rt.get("add", [])
        _check("retro-tags.json should carry the devote/commander add",
               any(e.get("unit") == "unit-05" and e.get("root") == "devote"
                   and e.get("w") == "06UrB" for e in adds), adds)


def test_real_port_tracked_roots_produce_no_local_entry():
    """devote and give are both tracked threads in this fixture, so the
    worked example's roots[] should produce NO local-roots entries at all
    -- a tracked thread's colour lives in threads.json, not units.json."""
    with _ScratchProject() as sp:
        pa.port_one(6, dry=False, src=None)
        uj = json.load(open(os.path.join(sp.data, "units.json"), encoding="utf-8"))
        row = next(u for u in uj["units"] if u["n"] == 6)
        _check("no local-roots entries for this unit (both roots are tracked)",
               not row.get("roots"), row.get("roots"))


def test_real_port_local_root_gets_a_colour():
    """A genuinely local (non-tracked) root gets {color, translit, gloss}
    in units.json -- Phase 4's hue-well assignment, ported from Matthew."""
    with _ScratchProject() as sp:
        artifact = (
            '<article class="unit" data-unit="7">\n'
            '<script type="application/json" id="unit-meta">\n' +
            json.dumps({
                "unit": 7, "slug": "unit-07", "passage": "Joshua 8:1-29",
                "title": "Ai", "movement": 2,
                "roots": [{"root": "shout", "translit": "teruʿah", "gloss": "war cry"}],
                "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
            }) +
            '\n</script>\n'
            '<section class="block legend" aria-label="color key"><ul></ul></section>\n'
            '<p class="v"><span class="n">1</span> '
            '<span class="r" data-root="shout">Shout!</span></p>\n'
            '</article>\n'
        )
        open(os.path.join(sp.src, "joshua_07_translation.html"), "w",
             encoding="utf-8").write(artifact)
        pa.port_one(7, dry=False, src=None)
        uj = json.load(open(os.path.join(sp.data, "units.json"), encoding="utf-8"))
        row = next(u for u in uj["units"] if u["n"] == 7)
        shout = row.get("roots", {}).get("shout")
        _check("local root 'shout' should be present with a colour",
               shout and shout.get("color") in bookmod.book().palette(), shout)
        _check("local root 'shout' should keep its translit/gloss",
               shout and shout.get("translit") == "teruʿah"
               and shout.get("gloss") == "war cry", shout)


def _local_root_artifact(root_entry):
    return (
        '<article class="unit" data-unit="7">\n'
        '<script type="application/json" id="unit-meta">\n' +
        json.dumps({
            "unit": 7, "slug": "unit-07", "passage": "Joshua 8:1-29",
            "title": "Ai", "movement": 2, "roots": [root_entry],
            "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
        }) +
        '\n</script>\n'
        '<section class="block legend" aria-label="color key"><ul></ul></section>\n'
        '<p class="v"><span class="n">1</span> '
        f'<span class="r" data-root="{root_entry["root"]}">Shout!</span></p>\n'
        '</article>\n'
    )


def test_real_port_keeps_local_root_example_and_echo():
    """Regression (2026-09-21): merge_units_json() wrote only {color,
    translit, gloss}, so a local root's `example` never reached units.json
    and generate() -- which rebuilds roots[] from that row -- dropped it
    from the built fragment. Unit 2 lost four examples this way. `echo`
    rides the same path."""
    with _ScratchProject() as sp:
        entry = {"root": "shout", "translit": "teruʿah", "gloss": "war cry",
                 "example": "raise a great shout", "echo": "1 Sam 4:5 — the shout at the ark"}
        open(os.path.join(sp.src, "joshua_07_translation.html"), "w",
             encoding="utf-8").write(_local_root_artifact(entry))
        pa.port_one(7, dry=False, src=None)
        meta = um.parse(open(os.path.join(sp.units, "unit-07.html"), encoding="utf-8").read())
        got = next((r for r in meta["roots"] if r["root"] == "shout"), {})
        _check("built fragment keeps the local root's example",
               got.get("example") == entry["example"], got)
        _check("built fragment keeps the local root's echo",
               got.get("echo") == entry["echo"], got)


def test_reporting_a_built_unit_needs_force():
    """A re-port replaces the fragment wholesale; 7af1a59 did it by accident
    and regressed unit 1. Without --force an existing fragment is refused."""
    with _ScratchProject() as sp:
        entry = {"root": "shout", "translit": "teruʿah", "gloss": "war cry"}
        open(os.path.join(sp.src, "joshua_07_translation.html"), "w",
             encoding="utf-8").write(_local_root_artifact(entry))
        pa.port_one(7, dry=False, src=None)
        dest = os.path.join(sp.units, "unit-07.html")
        open(dest, "a", encoding="utf-8").write("<!-- hand fix -->\n")
        try:
            pa.port_one(7, dry=False, src=None)
            refused = False
        except SystemExit:
            refused = True
        _check("re-port of a built unit without force must refuse", refused, None)
        _check("refused re-port must leave the fragment untouched",
               "hand fix" in open(dest, encoding="utf-8").read(), None)
        pa.port_one(7, dry=False, src=None, force=True)
        _check("force=True re-port replaces the fragment",
               "hand fix" not in open(dest, encoding="utf-8").read(), None)


def test_thread_delta_reports_coverage_and_candidate():
    with _ScratchProject() as sp:
        pa.port_one(6, dry=False, src=None)
        delta = open(os.path.join(sp.out, "thread-delta-06.md"), encoding="utf-8").read()
        _check("thread delta should report the 'shout' candidate",
               "`shout`" in delta, delta)
        _check("thread delta should preview the candidate's id-matched forms",
               "word(s) book-wide" in delta, delta)
        _check("thread delta should report real tracked-thread coverage gaps "
               "(the worked example only tags v1-2 of a passage declared as "
               "6:1-27, so occurrences elsewhere in the chapter are genuine "
               "gaps -- this also exercises load_roots() picking up the "
               "scratch-patched roots.json rather than a stale import-time default)",
               "occurrence(s) the Hebrew has but the fragment leaves untagged" in delta
               and '"root": "give"' in delta and '"root": "devote"' in delta, delta)
        _check("thread delta should report the retro fix for unit-05",
               "unit-05" in delta and "devote" in delta, delta)


def test_thread_delta_reports_open_questions():
    with _ScratchProject() as sp:
        meta = {
            "unit": 6, "slug": "unit-06", "passage": "Joshua 6:1-27",
            "title": "Jericho", "roots": [],
            "threads": {"opens": [], "payoffs": [], "candidates": [], "retro": []},
            "questions": [{"topic": "ḥerem rendering",
                           "note": "devoted to destruction, or transliterated?",
                           "options": ["devoted to destruction", "ḥerem, glossed"]}],
        }
        path = pa.thread_delta(meta)
        delta = open(path, encoding="utf-8").read()
        _check("thread delta should have an open-questions section",
               "## Open questions for Lane" in delta, delta)
        _check("thread delta should report the topic",
               "ḥerem rendering" in delta, delta)
        _check("thread delta should report the options",
               "devoted to destruction" in delta and "ḥerem, glossed" in delta, delta)


def test_print_questions_writes_to_stdout():
    import io
    import contextlib
    meta = {"questions": [{"topic": "Yam Suf",
                            "note": "Reed Sea or Red Sea?",
                            "options": ["Reed Sea", "Red Sea"]}]}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        pa.print_questions(meta)
    out = buf.getvalue()
    _check("print_questions should print the topic and note to stdout",
           "Yam Suf" in out and "Reed Sea or Red Sea?" in out, out)


def test_missing_meta_block_is_a_hard_error():
    with _ScratchProject() as sp:
        open(os.path.join(sp.src, "joshua_07_translation.html"), "w",
             encoding="utf-8").write('<article class="unit" data-unit="7">no meta here</article>')
        try:
            pa.port_one(7, dry=True, src=None)
            failed = False
        except SystemExit:
            failed = True
        _check("porting an artifact with no meta block must sys.exit", failed, None)


def test_invalid_meta_is_a_hard_error():
    with _ScratchProject() as sp:
        bad_meta = json.dumps({"unit": 7, "passage": "Joshua 7:1-26", "title": "Achan"})
        # missing roots/threads entirely -> validate() must reject it
        open(os.path.join(sp.src, "joshua_07_translation.html"), "w",
             encoding="utf-8").write(
            f'<article class="unit" data-unit="7">\n'
            f'<script type="application/json" id="unit-meta">\n{bad_meta}\n</script>\n'
            f'<p class="v"><span class="n">1</span> text</p>\n</article>\n'
        )
        try:
            pa.port_one(7, dry=True, src=None)
            failed = False
        except SystemExit:
            failed = True
        _check("porting an artifact with invalid meta must sys.exit", failed, None)


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
