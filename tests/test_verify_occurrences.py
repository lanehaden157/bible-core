"""Regression tests for verify_occurrences.py -- built as unit tests against
its functions directly (recount()) plus a scripted end-to-end run of main()
against temp files, since main() itself only reads from disk paths."""
import json
import os
import sys
import tempfile

import support  # noqa: E402
from biblecore import book as bookmod  # noqa: E402
from biblecore import verify_occurrences as vo  # noqa: E402

fail = []


def _check(name, condition, detail=""):
    if not condition:
        fail.append(f"{name}: {detail}")


def test_recount_counts_every_data_root_occurrence():
    html = ('<span class="r" data-root="kol">a</span>'
            '<span class="r" data-root="kol">b</span>'
            '<span class="rl" data-root="devote">c</span>')
    counts = vo.recount(html)
    _check("kol should recount to 2", counts.get("kol") == 2, counts)
    _check("devote should recount to 1", counts.get("devote") == 1, counts)


def _run_main_against(units, occurrences, threads):
    """Run verify_occurrences.main() against a scratch data/units tree,
    capturing whether it exits 0 or 1. Restores module globals afterward."""
    prev = bookmod._current
    with tempfile.TemporaryDirectory() as d:
        units_dir = os.path.join(d, "units")
        data_dir = os.path.join(d, "data")
        os.makedirs(units_dir)
        os.makedirs(data_dir)
        for slug, html in units.items():
            open(os.path.join(units_dir, slug + ".html"), "w", encoding="utf-8").write(html)
        json.dump(occurrences, open(os.path.join(data_dir, "occurrences.json"), "w", encoding="utf-8"))
        json.dump(threads, open(os.path.join(data_dir, "threads.json"), "w", encoding="utf-8"))
        cfg = json.load(open(support.FIXTURE, encoding="utf-8"))
        bookmod.use(bookmod.Book(cfg, d))
        try:
            failures = vo.check()
            code = vo.main()
        finally:
            bookmod.use(prev)
    return code, failures


def test_main_passes_when_counts_and_flags_agree():
    units = {"unit-01": '<span class="r" data-root="kol">all</span>'}
    occurrences = {"unit-01": {"kol": {"total": 1}}}
    threads = {"threads": [{"id": "kol", "root": "kol", "tagged": True}]}
    code, failures = _run_main_against(units, occurrences, threads)
    _check("main() should exit 0 on agreement", code in (0, None), (code, failures))


def test_main_fails_on_count_mismatch():
    units = {"unit-01": '<span class="r" data-root="kol">all</span>'}
    occurrences = {"unit-01": {"kol": {"total": 5}}}  # wrong on purpose
    threads = {"threads": []}
    code, failures = _run_main_against(units, occurrences, threads)
    _check("main() should exit 1 on a count mismatch", code == 1, (code, failures))
    _check("failure should mention the mismatch",
           any("count mismatch" in f for f in failures), failures)


def test_main_fails_when_tagged_true_but_root_absent():
    units = {"unit-01": '<span class="r" data-root="give">gave</span>'}
    occurrences = {"unit-01": {"give": {"total": 1}}}
    threads = {"threads": [{"id": "devote", "root": "devote", "tagged": True}]}
    code, failures = _run_main_against(units, occurrences, threads)
    _check("main() should exit 1 when tagged:true but root not in any fragment",
           code == 1, (code, failures))
    _check("failure should mention the tagged thread",
           any("devote" in f and "tagged:true" in f for f in failures), failures)


def test_main_fails_when_tagged_false_but_root_present():
    units = {"unit-01": '<span class="r" data-root="give">gave</span>'}
    occurrences = {"unit-01": {"give": {"total": 1}}}
    threads = {"threads": [{"id": "give", "root": "give", "tagged": False}]}
    code, failures = _run_main_against(units, occurrences, threads)
    _check("main() should exit 1 when tagged:false but root IS in a fragment",
           code == 1, (code, failures))
    _check("failure should mention flipping the flag",
           any("flip the flag" in f for f in failures), failures)


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
