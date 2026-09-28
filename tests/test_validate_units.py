"""validate_units.py (`python -m biblecore validate`, the build's hard gate):
its colour helpers on their own, then the whole gate on a scratch copy of
Joshua -- clean as shipped, failing once a fragment is broken."""
import contextlib
import io
import os
import shutil

import support
from biblecore import validate_units as vu

_tmp = None


def setup():
    global _tmp
    _tmp = support.scratch_book()


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)
    support.joshua_book()


def _run():
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = vu.main([])
    return rc, out.getvalue()


def test_unit_colours_tracked_wins_over_local():
    threads = {"give": {"color": "#aa0000"}}
    units = {"units": [{"slug": "unit-01", "roots": {
        "give": {"color": "#00aa00"}, "stone": "#0000aa", "plain": {"color": "#111111"}}}]}
    got = vu.unit_colours("unit-01", {"give", "stone", "none"}, threads, units)
    assert got == {"give": "#aa0000", "stone": "#0000aa"}, got


def test_thread_hexes_must_be_unique_case_blind():
    threads = {"a": {"id": "a", "color": "#AA0000"}, "b": {"id": "b", "color": "#aa0000"},
               "c": {"id": "c", "color": "#00aa00"}}
    warns = vu.check_thread_hexes_unique(threads)
    assert len(warns) == 1 and "'a', 'b'" in warns[0], warns


def test_close_colours_warn():
    warns = vu.check_colours("u", {"x": "#aa0000", "y": "#ab0101", "z": "#0000aa"})
    assert any("colours close: 'x'" in w for w in warns), warns
    assert not any("colours close" in w for w in vu.check_colours("u", {"x": "#aa0000",
                                                                         "z": "#0000aa"}))


def test_joshua_passes_and_a_broken_fragment_fails():
    rc, out = _run()
    assert rc == 0 and "0 error(s)" in out, out[-500:]
    path = os.path.join(_tmp, "units", "unit-02.html")
    html = support.read(path)
    start = html.index('<script type="application/json" id="unit-meta">')
    end = html.index("</script>", start) + len("</script>")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(html[:start] + html[end:])
    rc, out = _run()
    assert rc == 1 and "unit-02.html: FAIL" in out and "no meta block" in out, out[-500:]


def test_a_tracked_span_without_data_w_points_at_data_w():
    path = os.path.join(_tmp, "units", "unit-01.html")
    html = support.read(path)
    i = html.index(' data-w="')
    j = html.index('"', i + len(' data-w="')) + 1
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(html[:i] + html[j:])
    rc, out = _run()
    assert rc == 1 and "python -m biblecore data-w 1" in out, out[-800:]
