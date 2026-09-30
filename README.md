# bible-core

The shared architecture for the books in the Bible study platform. Numbers and
Joshua run the core's app shell and pipeline. Matthew is standalone since
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
  book's root as `python -m biblecore <command>`. `biblecore/web/` holds the
  site's shared parts (core.css, themes, and the app shell: `index.html`,
  `app/*.js`), which the build writes into each book.
- `template/` — the starter a new book copies once and then owns.
- `tools/new_book.py` — start a new book (§8). `tools/core_sync.py`,
  `tools/core_diff.py` — vendor the package into a book (`--all`: every
  core book, built, tested and committed); report local edits to a book's
  copy (`--template`: the template changes a book hasn't taken).
- `tools/release.py` — cut a release: tests, version, the ARCHITECTURE line,
  commit and tag (ARCHITECTURE.md §5).
- `docs/data-shapes.md` — the published `data/*.json` shapes.
- `docs/new-book.md` — the checklist for starting a book, who does what.
- `hub/` + `tools/hub_build.py` — the canon hub site (ARCHITECTURE.md §8),
  built into the sibling `../hub` repo, which rebuilds itself daily from a
  GitHub Action.
- `corpus/` — shared corpus files a new book gets a copy of (the Strong's
  lexicon; for a Greek book, the MorphGNT lexicon).
- `tests/` — `python tests/run.py`. Reads the sibling `../Joshua` (the
  reference book), `../Numbers` and `../Matthew` checkouts through temporary
  copies (`tests/support.py`), which also refuses any write into them, and
  fails if one changed anyway. Clone each next to this repo, then
  `npm install` in Joshua and Numbers (morphhb) and
  `python pipeline/fetch_corpus.py` in Matthew (ARCHITECTURE.md §8).
- `.github/workflows/tests.yml` — the same suite on GitHub Actions, on every
  push and PR, with the siblings cloned beside it. The book-side workflow is
  `template/.github/workflows/tests.yml` (`biblecore test`), identical in
  every book.

Status and history: `../session_index.md` and the other `Bible/` session files
one level up.
