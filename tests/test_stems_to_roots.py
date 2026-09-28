"""tools/stems_to_roots.py: proposing roots.json id sets from a Greek book's
stem policy (thread-stems.json), on a word table written into a temp
folder."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import support

TOOL = os.path.join(support.CORE, "tools", "stems_to_roots.py")
sys.path.insert(0, os.path.dirname(TOOL))
import stems_to_roots as s2r  # noqa: E402

# word_id, ref, surface, lemma
WORDS = [
    ("01010101", "Matt.1.1", "κληρονομήσουσιν", "klēronomeō"),
    ("01010102", "Matt.1.1", "κληρονομίαν", "klēronomia"),
    ("01010103", "Matt.1.1", "ἔλεος", "eleos"),
    ("01010104", "Matt.1.1", "ἐλεήμονες", "eleēmōn"),
    ("01010105", "Matt.1.1", "ἆρα", "ara2"),
    ("01010106", "Matt.1.1", "ἀρᾶς", "ara3"),
]
_tmp = None


def setup():
    global _tmp
    _tmp = tempfile.mkdtemp(prefix="bc-s2r-")
    with open(os.path.join(_tmp, "Test-words.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("word_id\tref\tsurface\tlemma\tmorph\n")
        for row in WORDS:
            fh.write("\t".join(row) + "\tN-:----NSF-\n")


def teardown():
    shutil.rmtree(_tmp, ignore_errors=True)


def _run(stems, threads=None):
    sp = os.path.join(_tmp, "thread-stems.json")
    json.dump({"stems": stems}, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    args = [sys.executable, TOOL, _tmp, sp]
    if threads is not None:
        tp = os.path.join(_tmp, "threads.json")
        json.dump({"threads": threads}, open(tp, "w", encoding="utf-8"))
        args.append(tp)
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["roots"], r.stderr


def test_stem_match_is_accent_blind_and_honours_anchor_and_exclude():
    words = [{"surface": w[2], "lemma": w[3]} for w in WORDS]
    got = s2r.propose(words, {"stems": {
        "inherit": {"stems": ["κληρονομ"]},
        "mercy": {"stems": ["^ελε"], "exclude": ["ἐλεήμονες"]},
        "phrase": {"stems": ["ελε"], "phrase": True},
    }})
    assert set(got) == {"inherit", "mercy"}, got  # a phrase thread is skipped
    assert set(got["inherit"]) == {"klēronomeō", "klēronomia"}, got["inherit"]
    assert set(got["mercy"]) == {"eleos"}, got["mercy"]


def test_report_names_mixed_and_empty_threads_and_maps_thread_to_root():
    roots, err = _run({"inherit": {"stems": ["κληρονομ"]}, "nothing": {"stems": ["ψψψ"]}},
                      threads=[{"id": "inherit", "root": "inheritance"}])
    assert roots == {"inheritance": {"ids": ["klēronomeō", "klēronomia"], "note": "TODO"}}, roots
    assert "MIXED: 1 thread(s)" in err and "EMPTY: stems matched nothing for: nothing" in err, err


def test_one_id_in_two_roots_is_a_clash():
    roots, err = _run({"mercy": {"stems": ["ελεος"]}, "pity": {"stems": ["^ελεο"]}})
    assert roots["mercy"]["ids"] == roots["pity"]["ids"] == ["eleos"], roots
    assert "CLASH: 1 id(s)" in err and "'eleos': 'mercy' and 'pity'" in err, err
