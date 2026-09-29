# bible-core

The shared architecture for the books in the Bible study platform. Numbers and
Joshua run the template's app shell and pipeline. Matthew is standalone since
2026-09-29 (reverted to its own shell and `pipeline/`); core is for future
books.

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
- `hub/` + `tools/hub_build.py` — the canon hub site (ARCHITECTURE.md §8),
  built into the sibling `../hub` repo, which rebuilds itself daily from a
  GitHub Action.
- `corpus/` — shared corpus files a new book gets a copy of (the Strong's
  lexicon; for a Greek book, the MorphGNT lexicon).
- `tests/` — `python tests/run.py`. Reads the sibling `../Joshua` (the
  reference book), `../Numbers` and `../Matthew` checkouts, read-only, and
  fails if it writes to them. Clone each next to this repo, then
  `npm install` in Joshua and Numbers (morphhb) and
  `python pipeline/fetch_corpus.py` in Matthew (ARCHITECTURE.md §8).

Status and history: `../session_index.md` and the other `Bible/` session files
one level up.
