"""Run every tests/test_*.py:  python tests/run.py [name-substring ...]

A test is any module-level function named test_*. It fails if it raises,
returns a non-empty list of messages, or appends to a module-level failure
list (`fail` or `_fails` -- the styles Joshua's tests use). No pytest.
"""
import glob
import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))


def main(filters):
    files = sorted(glob.glob(os.path.join(HERE, "test_*.py")))
    if filters:
        files = [f for f in files if any(x in os.path.basename(f) for x in filters)]
    total = failed = 0
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            print(f"✗ {name}: import failed")
            traceback.print_exc()
            failed += 1
            total += 1
            continue
        tests = [(n, f) for n, f in vars(mod).items()
                 if n.startswith("test_") and callable(f)]
        bad = []
        sink = next((getattr(mod, n) for n in ("fail", "_fails")
                     if isinstance(getattr(mod, n, None), list)), None)
        for tname, fn in tests:
            total += 1
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
        failed += len(bad)
        mark = "✗" if bad else "✓"
        print(f"{mark} {name}: {len(tests) - len(bad)}/{len(tests)}")
        for tname, msg in bad:
            print(f"    - {tname}: {msg}")
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
