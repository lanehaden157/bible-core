"""lxx_lookup: `biblecore lxx BOOK C:V [--expect ...]` and `--checks`, on the
tiny Text-Fabric LXX greek_book.make() writes (Gen 1:1 tis2 lego; Gen 2:4
biblos genesis; Exod 1:1 zelotes), so no real corpus is needed."""
import contextlib
import io
import json
import os

import greek_book
from biblecore import lxx_lookup as lx
from biblecore.leads import load_greek_corpus

_root = None
_lxx = None
_codes = None


def setup():
    global _root, _lxx, _codes
    _root = greek_book.make()
    _nt, _lxx, _codes = load_greek_corpus()


def teardown():
    greek_book.remove(_root)


def _run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = lx.main(list(argv))
    return rc, out.getvalue()


def test_refs_parse_ranges_lists_and_book_spellings():
    assert lx.parse_refs("Gen 1:1", _codes) == [("Gen", (1, 1), (1, 1))]
    assert lx.parse_refs("Genesis 1:1–2:4", _codes) == [("Gen", (1, 1), (2, 4))]
    assert lx.parse_refs("Exod 1:1 / Gen 1:1-2", _codes) == [
        ("Exod", (1, 1), (1, 1)), ("Gen", (1, 1), (1, 2))]
    assert lx.parse_refs("Gen 1:1, Exod 1:1", _codes)[1][0] == "Exod"


def test_unknown_book_and_non_ref_are_errors():
    for bad in ("Foo 1:1", "no passage here"):
        try:
            lx.parse_refs(bad, _codes)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should not parse")


def test_a_verse_prints_its_lemmas_in_order():
    rc, out = _run("Gen", "2:4")
    assert rc == 0 and "Gen 2:4: biblos genesis" in out, out


def test_expect_present_absent_and_partial():
    rc, out = _run("Gen", "2:4", "--expect", "biblos", "genesis")
    assert rc == 0 and "CONFIRMED" in out, out
    rc, out = _run("Gen", "2:4", "--expect", "biblos", "kleis")
    assert rc == 1 and "PARTIAL" in out and "NO kleis" in out, out
    rc, out = _run("Gen", "2:4", "--expect", "kleis")
    assert rc == 1 and "NOT FOUND" in out, out
    rc, out = _run("Gen", "2:4", "--expect", "!kleis")   # an absence claim
    assert rc == 0 and "CONFIRMED" in out, out
    rc, out = _run("Gen", "2:4", "--expect", "!biblos")  # present: claim fails
    assert rc == 1, out


def test_matching_ignores_macrons_and_digit_suffixes():
    assert lx.evaluate(["tis2"], "tis")[0] == "confirmed"
    assert lx.evaluate(["zēlōtēs"], "zelotes")[0] == "confirmed"
    assert lx.evaluate(["tis2"], "ti")[0] == "not found"  # a prefix isn't a lemma


def test_a_check_pools_its_passages():
    c = {"ref": "Gen 1:1 / Exod 1:1", "claim": "x", "expect": ["lego", "zelotes"]}
    r = lx.run_check(_lxx, _codes, c)
    assert r["status"] == "confirmed" and not r["missing"], r


def test_a_verse_the_lxx_lacks_is_reported():
    r = lx.run_check(_lxx, _codes, {"ref": "Gen 9:9", "claim": "x", "expect": "lego"})
    assert r["status"] == "not found" and r["missing"] == ["Gen 9:9"], r


def test_checks_run_from_a_json_file_and_count_each_status():
    path = os.path.join(_root, "checks.json")
    checks = [{"ref": "Gen 2:4", "claim": "a", "expect": "biblos"},
              {"ref": "Gen 2:4", "claim": "b", "expect": ["biblos", "kleis"]},
              {"ref": "Gen 2:4", "claim": "c", "expect": "kleis"},
              {"ref": "Foo 1:1", "claim": "d", "expect": "x"}]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(checks, fh)
    rc, out = _run("--checks", path)
    assert rc == 0, out
    for want in ("CONFIRMED", "PARTIAL", "NOT FOUND", "unknown LXX book",
                 "1 confirmed, 1 error, 1 not found, 1 partial"):
        assert want in out, (want, out)


def test_nt_refs_are_skipped_not_errors():
    _check_ = lx.is_nt_ref
    assert _check_("Matt 5:3") and _check_("1 Cor 3:1") and not _check_("Gen 1:1")
    path = os.path.join(_root, "nt-checks.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([{"ref": "Matt 5:3", "claim": "a", "expect": "x"},
                   {"ref": "Gen 2:4", "claim": "b", "expect": "biblos"}], fh)
    rc, out = _run("--checks", path)
    assert "1 confirmed" in out and "1 skipped (not LXX)" in out and "error" not in out, out


def test_checks_are_read_from_a_source_artifact():
    src = os.path.join(_root, "source-artifacts")
    os.makedirs(src, exist_ok=True)
    meta = {"unit": 1, "checks": [{"ref": "Gen 1:1", "claim": "x", "expect": "lego"}]}
    with open(os.path.join(src, "matthew_01_translation.html"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write('<article><script type="application/json" id="unit-meta">'
                 + json.dumps(meta) + "</script></article>")
    for arg in ("1", "unit-01"):
        rc, out = _run("--checks", arg)
        assert rc == 0 and "CONFIRMED" in out, (arg, out)


def test_no_arguments_is_a_usage_error():
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            _run()
    except SystemExit as exc:
        assert exc.code == 2, exc
    else:
        raise AssertionError("expected a usage error")
