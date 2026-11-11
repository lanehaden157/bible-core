# bible-core

`README.md` maps the files. `ARCHITECTURE.md` has the shared shape, where books
differ, how core changes, and how to start a book (§8).

**State** isn't written here: the version is `biblecore/__init__.py`,
`python tests/run.py` prints the test count, and `python -m biblecore book` in a
book prints that book's state. Platform history is `../session_index.md`.

Core is built for future books. Numbers, Joshua and Matthew are on it. Matthew's
units 1-13 are boxed (`contract: "legacy"`, ARCHITECTURE §5): tag edits only.
The parity tests read Matthew's corpus and `archive/pipeline/` read-only.

## Concurrent sessions

Core and book sessions often edit these repos at the same time. Strong
suggestions:

- `git status` before editing. If it's dirty from another session, work in a
  `git worktree` and fast-forward back rather than committing over it.
- Stage explicit paths, not `git add -A`.
- `git log -3` before a release, in case main moved.
- `core_sync.py` refuses a dirty core. Don't commit someone else's half-finished
  edit to unblock it.

## Commands (run from this folder)

    python tests/run.py [filter]          # the whole suite (no pytest needed)
    python tools/release.py X.Y.Z --note "..."   # cut a release
    python tools/core_sync.py --all       # vendor into every core book
    python tools/core_sync.py <book-dir>  # vendor into one book
    python tools/core_diff.py <book-dir>  # book-local edits made to biblecore/
    python tools/core_diff.py <book-dir> --template  # template changes the book hasn't taken
    python tools/new_book.py ...          # start a book (docs/new-book.md)
    python tools/canon_collect.py         # refresh canon/*.json from the books
    python tools/hub_build.py ../hub      # preview the hub locally

Tests read the sibling `../Joshua`, `../Numbers` and `../Matthew` through
temporary copies, and `tests/support.py` refuses writes into them. A test gets
sibling data from `support.copy_of()`, `joshua_book()` or `numbers_book()`.

CI runs the suite on every push against the books' pushed `main`. Red there
after green locally usually means something unpushed.

## Releasing

1. Commit the change.
2. `python tools/release.py X.Y.Z --note "what changed"` refuses a dirty tree,
   runs the tests (`--skip-tests` if just run), sets the version, adds the
   ARCHITECTURE.md version line, commits and tags. `--dry-run` only checks.
3. `python tools/core_sync.py --all` (`--check` previews) vendors into each
   core book, builds, tests and commits the changed files by name. A dirty book
   is skipped and named: rerun once it's clean. A failed build or test leaves
   that book's changes uncommitted.
4. Neither command pushes. Push core, its tag and each book when Lane says so.
   Where the summary says chat-side files changed, run `python -m biblecore
   sync` in that book after pushing.

When writing a change:

- A new `checks` key goes in `book.py` `CHECK_DEFAULTS` with a test. A file
  every book syncs goes in `sync.py` `DEFAULT_SYNC` with a role in `ROLES`.
- File writers open with `newline="\n"`. The tests catch a build step that
  writes CRLF but not a tool's own writes, so check new writers by eye.
- A template fix reaches existing books only through `core_diff.py <book>
  --template`, which each book session runs when it chooses.

## The hub

`hub/` is the hub's page, app and CSS; `tools/hub_build.py` adds the data. The
hub repo (`lanehaden157/bible`) rebuilds itself from pushed code daily and on
"Run workflow". Don't edit it by hand. The local build also reads unpushed work,
so use it for previews only.
