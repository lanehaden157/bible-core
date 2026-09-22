# bible-core

The shared architecture for new books in the Bible study platform. Joshua and
Matthew are the reference implementations and don't use it.

- `ARCHITECTURE.md` — the shared shape, where books differ, how the core
  changes, and how to start a book (§8).
- `canon/conventions.md` — shared wording defaults each book's glossary
  starts from.
- `biblecore/` — the shared package, vendored into each book and run from the
  book's root as `python -m biblecore <command>`.
- `template/` — the starter a new book copies once and then owns.
- `tools/core_sync.py`, `tools/core_diff.py` — vendor the package into a
  book; report local edits to a book's copy.
- `tests/` — `python tests/run.py`. Runs against the sibling `../Joshua`
  checkout, read-only.

Plan and status: `../g6-plan.md`. Session notes live one level up, in the
`Bible/` session files.
