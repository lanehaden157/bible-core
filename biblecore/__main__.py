"""python -m biblecore <command> [args]   (run from the book's root)

Commands:
  build                 re-derive everything downstream of the fragments
  assets                css + component list for the enabled components
  port N [--dry|--src X|--force]   port a research artifact
  audit [...]           tracked-thread coverage (--ids ROOT, --unit unit-06, --stub)
  data-w N [--dry]      fill data-w on a built unit by alignment
  retrofit              apply the retrofit specs
  refresh               regenerate built fragments' meta blocks
  validate              hard-gate built fragments
  scan                  -> data/occurrences.json
  verify-occurrences    independent recount
  roots                 validate data/roots.json
  digest                -> threads-digest.md
  colour ROOT [...]     colours for threads about to be promoted
  leads [N|--all]       canon leads (Hebrew books)
  canon                 echo edges + meta rows -> data/canon.json
  manifest              -> data/manifest.json (index to the data files)
  migrate [--to X.Y.Z] [--dry] [--unit N]
                        move built units to a newer contract
  test [--quick]        check this book: core pin, units, audit, build idempotence
  corpus                build the word table and reading text from the corpus
  units-from-map [MAP] [--kinds outer,inner] [--dry]
                        unit rows + groupings from the literary unit map
  sync-check [--mark-synced [FILE ...]]
  sync                  mirror chat-side files, commit, push
  book                  show the resolved book.json settings
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
    "manifest": ("biblecore.manifest", "main"),
    "migrate": ("biblecore.migrate", "main"),
    "test": ("biblecore.selftest", "main"),
    "sync-check": ("biblecore.sync", "check_main"),
    "sync": ("biblecore.sync", "push_main"),
}


def _corpus(argv):
    from biblecore import corpus
    from biblecore.book import book
    counts = corpus.adapter().build(book())
    print(json.dumps(counts))
    print("check these counts against a printed edition before trusting the corpus")
    return 0


def _show_book(argv):
    from biblecore import __version__
    from biblecore.book import book
    b = book()
    print(f"{b.name} ({b.osis}) at {b.root}")
    print(f"core {__version__}; book.json pins {b.cfg.get('core', '?')}")
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
    if cmd == "corpus":
        return _corpus(rest)
    if cmd == "book":
        return _show_book(rest)
    if cmd not in COMMANDS:
        print(f"unknown command {cmd!r}\n{__doc__}")
        return 2
    mod, fn = COMMANDS[cmd]
    return getattr(importlib.import_module(mod), fn)(rest) or 0


if __name__ == "__main__":
    sys.exit(main())
