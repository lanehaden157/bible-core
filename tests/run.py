"""Run every tests/test_*.py:  python tests/run.py [-jN] [--times] [name-substring ...]

A test is any module-level function named test_*. It fails if it raises,
returns a non-empty list of messages, or appends to a module-level failure
list (`fail` or `_fails` -- the styles Joshua's tests use). No pytest.

The sibling book repos (../Joshua, ../Numbers, ../Matthew) are read-only
inputs. The run snapshots them first and fails if any file there was
written, added or removed by the time it ends.

Files run in parallel, each in its own worker process (-jN workers, default
one per CPU), heaviest first by the last run's times. A file's tests run in
order in one process, as before, except that a file whose last run took
over SPLIT_SECS gets one worker per test (each with the file's setup and
teardown); the run then checks every test the file defines was run. -j1 runs
everything in this process, the way the suite ran before it went parallel.
Each file's output is printed as a block, in file order.

--times prints where the run's seconds went: each file (import plus its
tests), the slowest test functions, and the sibling snapshots.
"""
import ast
import glob
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

# Parity tests import Matthew's own pipeline modules; importing writes
# __pycache__/ beside them unless bytecode writing is off.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

SIBLINGS = [os.path.normpath(os.path.join(HERE, "..", "..", b))
            for b in ("Joshua", "Numbers", "Matthew")]
SKIP_DIRS = {".git", "node_modules"}
# last run's seconds per file, for scheduling the heaviest first (not in the
# repo: it's per machine, and a missing or stale file only costs ordering)
TIMES_FILE = os.path.join(tempfile.gettempdir(), "biblecore-test-times.json")
SPLIT_SECS = 8


def snapshot(roots=SIBLINGS):
    """{path: (mtime_ns, size)} for every file in the sibling repos."""
    out = {}
    for root in roots:
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in files:
                p = os.path.join(d, f)
                st = os.stat(p)
                out[p] = (st.st_mtime_ns, st.st_size)
    return out


def sibling_writes(before, after):
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    return [os.path.relpath(p, os.path.dirname(os.path.dirname(HERE))) for p in changed]


def run_file(path, only=None):
    """Import one test file and run its tests in order (only those named in
    `only`, if given). -> {"name", "total", "failed", "lines" (the ✓/✗
    report), "secs", "tests": [[secs, name]], "found": every test the file
    defines, "ran": the ones run, "bad": [[test, message]]}. What the tests
    themselves print goes to stdout as it happens."""
    t_file = time.perf_counter()
    name = os.path.splitext(os.path.basename(path))[0]
    res = {"name": name, "total": 0, "failed": 0, "lines": [], "tests": [],
           "found": [], "ran": [], "bad": []}
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        res.update(total=1, failed=1, secs=time.perf_counter() - t_file,
                   lines=[f"✗ {name}: import failed", traceback.format_exc().rstrip()])
        return res
    tests = [(n, f) for n, f in vars(mod).items()
             if n.startswith("test_") and callable(f)]
    res["found"] = [n for n, _f in tests]
    if only is not None:
        tests = [(n, f) for n, f in tests if n in only]
    res["ran"] = [n for n, _f in tests]
    bad = []
    sink = next((getattr(mod, n) for n in ("fail", "_fails")
                 if isinstance(getattr(mod, n, None), list)), None)
    for tname, fn in tests:
        t_test = time.perf_counter()
        try:
            if hasattr(mod, "setup"):
                mod.setup()
            before = len(sink) if sink is not None else 0
            result = fn()
            if result:
                bad.append((tname, "\n      ".join(map(str, result))))
            elif sink is not None and len(sink) > before:
                bad.append((tname, "\n      ".join(map(str, sink[before:]))))
        except Exception as exc:
            bad.append((tname, f"{type(exc).__name__}: {exc}\n"
                               + traceback.format_exc(limit=3)))
        finally:
            if hasattr(mod, "teardown"):
                mod.teardown()
            res["tests"].append([time.perf_counter() - t_test, f"{name}.{tname}"])
    mark = "✗" if bad else "✓"
    res["lines"] = [f"{mark} {name}: {len(tests) - len(bad)}/{len(tests)}"]
    res["lines"] += [f"    - {tname}: {msg}" for tname, msg in bad]
    res.update(total=len(tests), failed=len(bad), secs=time.perf_counter() - t_file,
               bad=[list(b) for b in bad])
    return res


def worker(out_json, path, only=None):
    """run.py --worker OUT.json FILE [TEST,TEST...]: one file (or the named
    tests of it) in this process, the result written to OUT.json for the
    parent."""
    res = run_file(path, only and only.split(","))
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(res, fh)
    return 0


def run_in_worker(path, only=None):
    """One file (or the named tests of it) in a child process. -> run_file()'s
    dict, plus "output": whatever the tests printed."""
    name = os.path.splitext(os.path.basename(path))[0]
    fd, out_json = tempfile.mkstemp(prefix="biblecore-test-", suffix=".json")
    os.close(fd)
    t0 = time.perf_counter()
    try:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        cmd = [sys.executable, os.path.abspath(__file__), "--worker", out_json, path]
        r = subprocess.run(cmd + ([",".join(only)] if only else []),
                           cwd=os.getcwd(), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        output = (r.stdout + r.stderr).rstrip()
        try:
            with open(out_json, encoding="utf-8") as fh:
                res = json.load(fh)
        except (OSError, ValueError):
            what = f"{name} ({', '.join(only)})" if only else name
            res = {"name": name, "total": 1, "failed": 1, "tests": [], "found": [],
                   "ran": [], "secs": time.perf_counter() - t0, "bad": [],
                   "lines": [f"✗ {what}: worker died (exit {r.returncode})"]}
    finally:
        os.remove(out_json)
    res["output"] = output
    return res


def load_times():
    try:
        with open(TIMES_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def test_names(path):
    """The test_* functions a file defines, read without importing it."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return [n.name for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]


def merge(name, parts):
    """One file's result from its per-test workers' results. A test the
    file defines that no worker ran fails the file."""
    if len(parts) == 1:
        return parts[0]
    res = {"name": name, "output": "\n".join(p["output"] for p in parts if p.get("output")),
           "secs": sum(p["secs"] for p in parts),
           "tests": [t for p in parts for t in p["tests"]]}
    died = [ln for p in parts if not p["found"] for ln in p["lines"]]
    found = next((p["found"] for p in parts if p["found"]), [])
    ran = [n for p in parts for n in p["ran"]]
    bad = [b for p in parts for b in p["bad"]]
    missed = [n for n in found if n not in ran]
    lines = [f"    - {t}: {m}" for t, m in bad]
    if missed:
        lines.append(f"    - not run (the split by test missed them): {', '.join(missed)}")
    failed = len(bad) + len(died) + (1 if missed else 0)
    head = f"{'✗' if failed else '✓'} {name}: {len(ran) - len(bad)}/{len(ran)}"
    res.update(total=len(ran) + len(died) + (1 if missed else 0), failed=failed,
               lines=died + [head] + lines)
    return res


def save_times(results):
    times = load_times()
    times.update({r["name"]: r["secs"] for r in results})
    times.update({n: t for r in results for t, n in r["tests"]})
    try:
        with open(TIMES_FILE, "w", encoding="utf-8") as fh:
            json.dump(times, fh, indent=1, sort_keys=True)
    except OSError:
        pass


def main(filters, times=False, jobs=None):
    t_run = time.perf_counter()
    files = sorted(glob.glob(os.path.join(HERE, "test_*.py")))
    if filters:
        files = [f for f in files if any(x in os.path.basename(f) for x in filters)]
    jobs = max(1, min(jobs or os.cpu_count() or 1, len(files) or 1))
    t0 = time.perf_counter()
    siblings_before = snapshot()
    t_snap = time.perf_counter() - t0

    def show(res):
        if res.get("output"):
            print(res["output"])
        for ln in res["lines"]:
            print(ln)
        sys.stdout.flush()

    results = []
    if jobs == 1:
        for path in files:
            res = run_file(path)
            show(res)
            results.append(res)
    else:
        # a slow file is split into one job per test; jobs go heaviest
        # first (unknown ones count as heavy); results show in file order
        last = load_times()
        inf = float("inf")
        work = []    # (estimated secs, path, test names or None)
        for path in files:
            name = os.path.splitext(os.path.basename(path))[0]
            names = test_names(path) if last.get(name, 0) > SPLIT_SECS else []
            if len(names) > 1:
                work += [(last.get(f"{name}.{n}", inf), path, [n]) for n in names]
            else:
                work.append((last.get(name, inf), path, None))
        work.sort(key=lambda w: -w[0])
        with ThreadPoolExecutor(jobs) as pool:
            futures = [(path, pool.submit(run_in_worker, path, only))
                       for _t, path, only in work]
            for path in files:
                name = os.path.splitext(os.path.basename(path))[0]
                res = merge(name, [f.result() for p, f in futures if p == path])
                show(res)
                results.append(res)
    save_times(results)

    total = sum(r["total"] for r in results)
    failed = sum(r["failed"] for r in results)
    t0 = time.perf_counter()
    touched = sibling_writes(siblings_before, snapshot())
    t_snap += time.perf_counter() - t0
    if touched:
        failed += 1
        total += 1
        print(f"✗ sibling repos written to (tests must only read them): "
              + ", ".join(touched[:10]) + (" ..." if len(touched) > 10 else ""))
    print(f"\n{total - failed}/{total} passed")
    if times:
        print(f"\n{time.perf_counter() - t_run:.1f}s in all ({jobs} worker"
              f"{'s' if jobs > 1 else ''}); sibling snapshots {t_snap:.1f}s")
        print("slowest files (import + tests):")
        for r in sorted(results, key=lambda r: -r["secs"])[:15]:
            print(f"  {r['secs']:7.2f}s  {r['name']}")
        print("slowest tests:")
        for t, n in sorted((t for r in results for t in r["tests"]), reverse=True)[:20]:
            print(f"  {t:7.2f}s  {n}")
    return 1 if failed else 0


def parse_args(args):
    filters, times, jobs = [], False, None
    it = iter(args)
    for a in it:
        if a == "--times":
            times = True
        elif a == "-j":
            jobs = int(next(it))
        elif a.startswith("-j"):
            jobs = int(a[2:])
        else:
            filters.append(a)
    return filters, times, jobs


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        sys.exit(worker(*sys.argv[2:5]))
    filters, times, jobs = parse_args(sys.argv[1:])
    sys.exit(main(filters, times=times, jobs=jobs))
