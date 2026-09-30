"""python -m biblecore <command> [args]   (run from the book's root)
python -m biblecore <command> --help     (that command's usage)

Commands:
  build                 re-derive everything downstream of the fragments
  assets                css + component list for the enabled components
  port N [--dry|--src X|--force]   port a research artifact
  audit [...]           tracked-thread coverage (--ids ROOT, --unit unit-06, --stub, --check)
  data-w N [--dry]      fill data-w on a built unit by alignment
  retrofit              apply the retrofit specs
  refresh               regenerate built fragments' meta blocks
  validate              hard-gate built fragments
  scan                  -> data/occurrences.json
  verify-occurrences    independent recount
  roots                 validate data/roots.json
  digest                -> threads-digest.md
  colour ROOT [...]     colours for threads about to be promoted
  leads [N|--all] [--rare N]
                        canon leads (Hebrew Bible; LXX + NT for a Greek book)
  canon                 echo edges + meta rows -> data/canon.json
  emit                  -> data/words/, lemmas.json, text.json (interlinear, search)
  manifest              -> data/manifest.json (index to the data files)
  migrate [--to X.Y.Z] [--dry] [--unit N]
                        move built units to a newer contract
  test [--quick]        check this book: core pin, units, audit, build idempotence
  corpus                build the word table and reading text from the corpus
  units-from-map [MAP] [--kinds outer,inner] [--dry]
                        unit rows + groupings from the literary unit map
  sync-check [--mark-synced [FILE ...] | --mark-pasted]
                        which chat-side files need syncing or re-pasting
  sync                  mirror chat-side files, commit, push
  book                  the book's state (core pin, units, threads, sync, pasted
                        field) and its resolved paths
"""
import importlib
import json
import sys

COMMANDS = {
    "build": ("biblecore.build", "main"),
    "assets": ("biblecore.assets", "main"),
    "port": ("biblecore.port", "main"),
    "audit": ("biblecore.audit", "main"),
    "data-w": ("biblecore.data_w", "main"),
    "retrofit": ("biblecore.retrofit", "main"),
    "refresh": ("biblecore.refresh", "main"),
    "validate": ("biblecore.validate_units", "main"),
    "scan": ("biblecore.scan", "main"),
    "verify-occurrences": ("biblecore.verify_occurrences", "main"),
    "roots": ("biblecore.roots", "main"),
    "digest": ("biblecore.digest", "main"),
    "colour": ("biblecore.colour", "main"),
    "leads": ("biblecore.leads", "main"),
    "canon": ("biblecore.canon", "main"),
    "units-from-map": ("biblecore.units_map", "main"),
    "emit": ("biblecore.emit", "main"),
    "manifest": ("biblecore.manifest", "main"),
    "migrate": ("biblecore.migrate", "main"),
    "test": ("biblecore.selftest", "main"),
    "sync-check": ("biblecore.sync", "check_main"),
    "sync": ("biblecore.sync", "push_main"),
}
# commands whose main() parses its arguments with argparse (its own --help);
# every other one gets its module docstring for -h/--help and doesn't run
ARGPARSED = {"port", "data-w", "leads", "migrate", "units-from-map"}
HELP = ("-h", "--help")


def _corpus(argv):
    from biblecore import corpus
    from biblecore.book import book
    counts = corpus.adapter().build(book())
    print(json.dumps(counts))
    print("check these counts against a printed edition before trusting the corpus")
    return 0


def _ranges(ns):
    """[1, 2, 3, 5] -> '1-3, 5'."""
    out, start = [], None
    for i, n in enumerate(ns):
        if start is None:
            start = n
        if i + 1 == len(ns) or ns[i + 1] != n + 1:
            out.append(str(start) if start == n else f"{start}-{n}")
            start = None
    return ", ".join(out)


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _template_line(b):
    """The book's template base (book.json "template"), with how many
    bible-core commits have touched template/ since, when a sibling
    bible-core checkout is there to ask."""
    import os
    import subprocess
    base = b.cfg.get("template")
    if not base:
        return "no base recorded -> ../bible-core/tools/core_diff.py . --template --set-base <commit>"
    core = os.path.join(os.path.dirname(os.path.abspath(b.root)), "bible-core")
    try:
        r = subprocess.run(["git", "rev-list", "--count", f"{base}..HEAD", "--", "template"],
                           cwd=core, capture_output=True, text=True)
    except OSError:
        r = None
    if not r or r.returncode:
        return f"base {base}"
    n = int(r.stdout.strip() or 0)
    if not n:
        return f"base {base} (template unchanged since)"
    return (f"base {base} ({n} template commit{'s' if n != 1 else ''} since -> "
            f"../bible-core/tools/core_diff.py . --template)")


def status_lines(b):
    """The book's state, read from its data (structural audit D1): the
    CLAUDE.md files point here instead of keeping hand-written state lines."""
    import os
    from collections import Counter
    from biblecore import __version__
    lines = []
    pinned = b.cfg.get("core", "?")
    vf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CORE_VERSION")
    vendored = open(vf, encoding="utf-8").read().split() if os.path.exists(vf) else []
    stamp = f" ({vendored[1][:7]})" if len(vendored) > 1 else ""
    flag = "" if pinned == __version__ else "  <- MISMATCH: vendor with core_sync.py, then set book.json core"
    lines.append(f"core      book.json pins {pinned}; vendored {__version__}{stamp}{flag}")
    lines.append("template  " + _template_line(b))

    uj = _load(b.data("units.json"))
    if uj:
        built = sorted(u["n"] for u in uj.get("units", []) if u.get("built"))
        planned = uj.get("unit_count") or len(uj.get("units", []))
        lines.append(f"units     {len(built)} built of {planned} planned"
                     + (f" ({_ranges(built)})" if built else ""))
    else:
        lines.append("units     no data/units.json yet")
    th = _load(b.data("threads.json"))
    threads = (th or {}).get("threads", [])
    by = Counter(t.get("status", "?") for t in threads)
    lines.append(f"threads   {len(threads)} tracked"
                 + (f" ({', '.join(f'{n} {s}' for s, n in sorted(by.items()))})" if threads else ""))

    try:
        from biblecore import sync
        st = sync.status(b)
    except Exception as exc:  # no git, not a repo yet
        lines.append(f"sync      unavailable ({type(exc).__name__}: {exc})")
        return lines
    todo = [f"{len(st['stale'])} need syncing" if st["stale"] else "",
            f"{len(st['missing'])} missing" if st["missing"] else "",
            f"{len(st['orphans'])} no longer synced" if st["orphans"] else ""]
    todo = [t for t in todo if t]
    lines.append(f"sync      {len(st['tracked'])} files, "
                 + (", ".join(todo) + " -> python -m biblecore sync-check" if todo
                    else "all in sync"))
    paste = {"pasted": f"pasted{' ' + st['pasted_at'][:10] if st['pasted_at'] else ''}; "
                       f"no changes since",
             "changed": "changed since the last paste -> PASTE BY HAND, then "
                        "sync-check --mark-pasted",
             "never": "no paste recorded -> paste it, then sync-check --mark-pasted",
             None: "no instruction-field file"}[st["paste"]]
    lines.append(f"field     {st['chat_side'] or '-'}: {paste}")
    return lines


def _show_book(argv):
    from biblecore.book import book
    b = book()
    print(f"{b.name} ({b.osis}) at {b.root}")
    for line in status_lines(b):
        print(line)
    print("paths")
    for k in ("words", "reading", "units", "data", "css", "source", "out",
              "retrofit", "retro", "wlc"):
        print(f"  {k:10} {b.path(k)}")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    wants_help = any(a in HELP for a in rest)
    if cmd in ("corpus", "book"):
        if wants_help:
            print(__doc__)
            return 0
        return _corpus(rest) if cmd == "corpus" else _show_book(rest)
    if cmd not in COMMANDS:
        print(f"unknown command {cmd!r}\n{__doc__}")
        return 2
    mod, fn = COMMANDS[cmd]
    module = importlib.import_module(mod)
    if wants_help and cmd not in ARGPARSED:
        print((module.__doc__ or __doc__).strip())
        return 0
    return getattr(module, fn)(rest) or 0


if __name__ == "__main__":
    sys.exit(main())
