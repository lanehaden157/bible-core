# bible-core

The shared architecture for new books in the Bible study platform. Joshua and
Matthew are the reference implementations and don't use it.

- `ARCHITECTURE.md` — the shared shape, where books differ, how the core
  changes, and how to start a book (§8).
- `canon/conventions.md`, `canon/decisions.md`, `canon/workflow.md` —
  shared wording defaults, settled cross-book calls, and the chat-side
  loop. Each book gets a copy (`canon-conventions.md`, `canon-decisions.md`,
  `core-workflow.md`) that syncs to its project side.
- `canon/*.json` — the canon registries: arcs, canon threads, intertext
  edges, type-scenes (ARCHITECTURE.md §2). `python tools/canon_collect.py`
  refreshes them from the books.
- `biblecore/` — the shared package, vendored into each book and run from the
  book's root as `python -m biblecore <command>`.
- `template/` — the starter a new book copies once and then owns.
- `tools/new_book.py` — start a new book (§8). `tools/core_sync.py`,
  `tools/core_diff.py` — vendor the package into a book; report local edits
  to a book's copy.
- `docs/data-shapes.md` — the published `data/*.json` shapes.
- `corpus/` — shared corpus files a new book gets a copy of (the Strong's
  lexicon).
- `tests/` — `python tests/run.py`. Runs against the sibling `../Joshua`
  checkout, read-only.

Plan and status: `../g6-plan.md`. Session notes live one level up, in the
`Bible/` session files.
