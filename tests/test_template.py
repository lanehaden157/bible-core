"""The starter template, end to end, through the real CLI.

1. An empty book made from the template builds clean.
2. Joshua re-made from the template -- its four source artifacts ported one
   by one with `python -m biblecore port N`, then `build` -- reproduces
   Joshua's committed units byte for byte, with a clean thread audit. This
   is the proof that a new book gets the same pipeline Joshua has.

Slow (it ports four units and scans the Hebrew Bible for canon leads).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import support
from template_book import make_book

J = support.JOSHUA
WLC = os.path.join(J, "node_modules", "morphhb", "wlc")


def _cli(root, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("BIBLECORE_BOOK", None)
    return subprocess.run([sys.executable, "-m", "biblecore", *args], cwd=root, env=env,
                          capture_output=True, text=True, encoding="utf-8")


def _set_paths(root, **paths):
    p = os.path.join(root, "book.json")
    bj = json.load(open(p, encoding="utf-8"))
    bj.update({k: v for k, v in paths.items() if k != "paths"})
    bj["paths"] = paths.get("paths", {})
    json.dump(bj, open(p, "w", encoding="utf-8"), indent=2)


def test_template_has_no_unfilled_placeholders_after_instantiation():
    d = tempfile.mkdtemp(prefix="bc-tpl-")
    try:
        make_book(d, "Numbers", "Num", "numbers")
        left = []
        for base, _dirs, files in os.walk(d):
            if "biblecore" in base:
                continue
            for f in files:
                path = os.path.join(base, f)
                if "{{" in f or "{{" in open(path, encoding="utf-8", errors="ignore").read():
                    left.append(os.path.relpath(path, d))
        return [f"placeholder left in {x}" for x in left]
    finally:
        shutil.rmtree(d)


def test_empty_book_builds():
    d = tempfile.mkdtemp(prefix="bc-empty-")
    try:
        make_book(d, "Numbers", "Num", "numbers")
        _set_paths(d, paths={"wlc": WLC})
        r = _cli(d, "corpus")
        if r.returncode:
            return [f"corpus failed: {r.stdout[-500:]}{r.stderr[-800:]}"]
        r = _cli(d, "build")
        if r.returncode or "build ok" not in r.stdout:
            return [f"empty build failed: {r.stdout[-800:]}{r.stderr[-800:]}"]
    finally:
        shutil.rmtree(d)


def test_joshua_from_template_reproduces_joshua():
    d = tempfile.mkdtemp(prefix="bc-joshua-")
    try:
        make_book(d, "Joshua", "Josh", "joshua")
        for f in ("Joshua-words.tsv", "Joshua-reading.txt"):
            shutil.copyfile(os.path.join(J, f), os.path.join(d, f))
        for f in os.listdir(os.path.join(J, "source-artifacts")):
            shutil.copyfile(os.path.join(J, "source-artifacts", f),
                            os.path.join(d, "source-artifacts", f))
        shutil.copyfile(os.path.join(J, "pipeline", "retrofit-tags.json"),
                        os.path.join(d, "retrofit", "retrofit-tags.json"))
        for f in ("threads.json", "roots.json"):
            shutil.copyfile(os.path.join(J, "data", f), os.path.join(d, "data", f))
        uj = json.load(open(os.path.join(J, "data", "units.json"), encoding="utf-8"))
        units = [{k: v for k, v in u.items() if k not in ("built", "roots")} | {"built": False}
                 for u in uj["units"]]
        json.dump({"book": "Joshua", "unit_count": uj["unit_count"],
                   "groupings": [dict(kind="movement", **m) for m in uj["movements"]],
                   "units": units},
                  open(os.path.join(d, "data", "units.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        _set_paths(d, groupings=["movement"],
                   palette=os.path.join(support.HERE, "joshua_well.json"),
                   paths={"wlc": WLC, "lexicon": os.path.join(
                       J, "pipeline", "corpus", "lexicon", "HebrewStrong.xml")})

        fails = []
        for n in (1, 2, 3, 4):
            r = _cli(d, "port", str(n))
            if r.returncode:
                return [f"port {n} failed: {r.stdout[-800:]}{r.stderr[-800:]}"]
        r = _cli(d, "build")
        if r.returncode or "build ok" not in r.stdout:
            return [f"build failed: {r.stdout[-800:]}{r.stderr[-800:]}"]
        if "0 gap(s), 0 wrong-id, 0 stray, 0 missing-data-w" not in r.stdout:
            fails.append("audit not clean after build")
        for n in (1, 2, 3, 4):
            ours = support.read(os.path.join(d, "units", f"unit-{n:02d}.html"))
            theirs = support.read(os.path.join(J, "units", f"unit-{n:02d}.html"))
            if ours != theirs:
                fails.append(f"unit {n} differs from Joshua's committed fragment")
        return fails
    finally:
        shutil.rmtree(d)
