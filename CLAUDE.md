# bible-core

`README.md` maps the files. `ARCHITECTURE.md`: shared shape, where books
differ, how core changes. `docs/using.md`: how to start a book.

State isn't written here. Version: `biblecore/__init__.py`. Test count:
`python tests/run.py`. A book's state: `python -m biblecore book` in the book.
Platform state: `../session_index.md`; history: `../history/`.

Core is for future books; it's a starting point, not gospel, and a book's own
file always wins. Numbers, Joshua, Matthew are on it. Matthew units 1-13 are
boxed (`contract: "legacy"`, ARCHITECTURE §5): tag edits only. Parity tests
read Matthew's corpus and `archive/pipeline/` read-only.

## Instruction files

- `canon/card-research.md`, `card-verse.md`, `card-build.md`: one card per
  chat (`card-condensed.md` too, vendored only into a tiered book; every card
  fetches the book's synced `lens.md`). `canon/contract.md` → book's `fragment-contract.md` (build chat only).
  `canon/conventions.md` → `canon-conventions.md`. All vendored + synced.
- `biblecore/BOOK_CLAUDE.md`: shared book guide; a book's `CLAUDE.md` imports
  it and adds its differences.
- Component `snippet.md` files are build-enforced: tighten wording only.

Keeping them lean (`tests/test_docs.py` fails when a core-owned file passes
its budget in `selftest.DOC_BUDGET_KB`; raising a budget is Lane's call):

- One home per rule: edit it where it lives, no second copy, no pointer
  paragraph. Each chat reads only its card, so a rule goes on the card of the
  chat that acts on it; all three chats → the field template.
- Over budget → cut or move something to add something.
- A rule code can check → a check (`meta.py`, `handoff_check.py`,
  `selftest.py`), not prose. A recipe a command can print → the command.
- Rule files say how it is: no dates, no "learned", no version history. That
  goes in `history/` or the commit message. A gotcha that still bites → a
  rule or a check.
- Book-specific → the book's file, not core. Core is a starting point.
- Terse wording; exact strings (keys, markup, file names, commands) stay
  exact. Output to Lane is normal prose.
- New doc file → only when a different reader needs it. Otherwise extend an
  existing one.

## Concurrent sessions

Core and book sessions often edit these repos at once. Strong suggestions:

- `git status` before editing. Dirty from another session → work in a
  `git worktree`, fast-forward back; don't commit over it.
- Stage explicit paths, not `git add -A`.
- `git log -3` before a release, in case main moved.
- `core_sync.py` refuses a dirty core. Don't commit someone else's
  half-finished edit to unblock it.

## Commands (this folder)

    python tests/run.py [filter]          # the whole suite (no pytest needed)
    python tools/release.py X.Y.Z --note "..."   # cut a release
    python tools/core_sync.py --all       # vendor into every core book
    python tools/core_sync.py <book-dir>  # vendor into one book
    python tools/core_diff.py <book-dir>  # book-local edits made to biblecore/
    python tools/core_diff.py <book-dir> --template  # template changes the book hasn't taken
    python tools/new_book.py ...          # start a book (docs/new-book.md)
    python tools/canon_collect.py         # refresh canon/*.json from the books
    python tools/hub_build.py ../hub      # preview the hub locally

Tests read sibling `../Joshua`, `../Numbers`, `../Matthew` through temporary
copies; `tests/support.py` refuses writes into them. Get sibling data from
`support.copy_of()`, `joshua_book()` or `numbers_book()`. On Windows run with
`PYTHONIOENCODING=utf-8`.

CI runs the suite on every push against the books' pushed `main`. Red there
after green locally usually = something unpushed.

## Releasing

1. Commit the change.
2. `python tools/release.py X.Y.Z --note "what changed"`: refuses a dirty
   tree, runs tests (`--skip-tests` if just run), sets the version, adds the
   `history/versions.md` line, commits, tags. `--dry-run` only checks.
3. `python tools/core_sync.py --all` (`--check` previews): vendors into each
   core book, builds, tests, commits changed files by name. Dirty book =
   skipped and named; rerun once clean. Failed build or test leaves that
   book's changes uncommitted.
4. Neither command pushes. Push core, its tag and each book when Lane says.
   Summary says chat-side files changed → `python -m biblecore sync` in that
   book after pushing. Field changed → tell Lane to re-paste.

Writing a change:

- New `checks` key → `book.py` `CHECK_DEFAULTS` + a test. File every book
  syncs → `sync.py` `DEFAULT_SYNC` + a role in `ROLES`.
- File writers open with `newline="\n"`. Tests catch a build step writing
  CRLF but not a tool's own writes: check new writers by eye.
- Template fix reaches existing books only through `core_diff.py <book>
  --template`, which each book session runs when it chooses.

## The hub

`hub/` = the hub's page, app, CSS; `tools/hub_build.py` adds the data. Hub repo
(`lanehaden157/bible`) rebuilds itself from pushed code daily and on "Run
workflow". Don't edit it by hand. Local build also reads unpushed work:
previews only.
