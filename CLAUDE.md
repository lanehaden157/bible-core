# bible-core

How this repo behaves. `README.md` maps the files; `ARCHITECTURE.md` is the
shared shape, where books are expected to differ, how the core changes, and
how to start a book (§8).

**State:** the version is `biblecore/__init__.py`; `python tests/run.py`
prints the test count; each book's state (units, threads, core pin, sync,
pasted field) is `python -m biblecore book` in that book. None of it is
written here, so it can't go stale. Numbers and Joshua are on core; Matthew
is standalone (below). The platform-level record (status and
history) is `../session_index.md`. The core is forward-looking, built for future books.
Matthew is **standalone** (decided 2026-09-29): Lane reverted it to its
pre-core state (old app shell, own `pipeline/`, no `book.json`, units 1-13; the
core-era work is at its tag `pre-revert-2026-09-29`). It is a 'legacy' book in
the hub (`vN` links) and gets no core syncs. Core stays for future books;
don't plan a Matthew migration. Core's Greek work (MorphGNT, LXX) was proven
against Matthew's data and still reads it read-only for parity tests.

## Concurrent sessions

Multiple sessions — a core session and one or more book sessions (Numbers,
Joshua, Matthew) — routinely edit this repo and its worktrees at the same
time, sometimes minutes apart. It usually goes fine, but it has caused real
near-misses: one session's `git add -A` can sweep up another's half-finished
edit, and two sessions can vendor different core versions into the same book
back to back. Good habits, not hard rules:

- `git status` before editing here directly. If it's dirty from another
  session's work, don't commit over it — use `git worktree add` instead and
  merge back with a fast-forward when done, or ask the other session what
  it's mid-edit on.
- Let `tools/release.py` do the version bump: it refuses a dirty tree, so
  a version never sits on top of unrelated uncommitted work. Check
  `git log -3` first in case another session already moved main.
- A book's `core_sync.py` refuses to run against a dirty bible-core commit —
  don't route around that by committing someone else's half-finished edit
  just to unblock a vendor.
- After a vendor, `python -m biblecore book` in that book shows its pin and
  the vendored commit, so a later session can tell whether it's behind
  without anything recorded by hand.

## Commands (run from this folder)

    python tests/run.py [filter]         # the whole suite (no pytest needed)
    python tools/release.py X.Y.Z --note "..."  # cut a release (below)
    python tools/core_sync.py --all       # take it to every core book (below)
    python tools/core_sync.py <book-dir>  # vendor into one book (refuses if dirty)
    python tools/core_diff.py <book-dir>  # book-local edits made to biblecore/
    python tools/core_diff.py <book-dir> --template  # template changes the book hasn't taken
    python tools/new_book.py ...         # start a book from template/ (§8); fills its canon/books.json row
    python tools/canon_collect.py        # refresh canon/*.json from the books
    python tools/hub_build.py ../hub     # rebuild the hub by hand (see below)

The tests read the sibling `../Joshua`, `../Numbers` and `../Matthew`
checkouts through temporary copies, and `tests/support.py` refuses any write
into them, even from a harness that skips `run.py` (README.md has the setup).
A test that needs sibling data gets it from `support.copy_of()` or
`support.joshua_book()` / `numbers_book()`.

## Releasing a core change

Two commands, after the change itself is committed:

1. `python tools/release.py X.Y.Z --note "what changed"`. It refuses a dirty
   tree, runs `python tests/run.py` (`--skip-tests` if you just ran it), sets
   `biblecore/__init__.py` (the one place the version is written), adds the
   line to ARCHITECTURE.md's version list, commits and tags `vX.Y.Z`.
   `--dry-run` checks without changing anything.
2. `python tools/core_sync.py --all` (`--check` first to preview). For each
   `kind: core` book in `canon/books.json` found next to this folder, it
   vendors, sets `book.json` `core`, runs the book's `build` and `python -m
   biblecore test`, then stages the changed files by name and commits. The
   build rewrites the generated css and app shell from `biblecore/web/`, so
   their diff is only what changed there. A book with a dirty tree is
   skipped and named (usually another session mid-edit): rerun `--all` once
   it's clean. A failed build or test leaves that book's changes uncommitted
   to inspect.
3. Neither command pushes. Both print the push commands; push core, its tag
   and each book once Lane says so. Where the summary says chat-side files
   changed, run `python -m biblecore sync` in that book after pushing (it
   commits and pushes the mirror).

When writing the change:

- Book settings that gate checks (`checks` in `book.json`) are closed keys:
  a new one goes in `book.py` `CHECK_DEFAULTS` with a test. A file every
  book should sync goes in `sync.py` `DEFAULT_SYNC` (with a role in
  `ROLES`), not in each book's `book.json`.
- Every file writer opens with `newline="\n"` (since 0.9.10), so a Windows
  run writes LF like the `.gitattributes` expects. `test_template` catches a
  build step that writes CRLF, but not a tool's own writes (`new_book.py`,
  `sync.py`), so check new writers by eye.
- A template fix reaches existing books only through `core_diff.py <book>
  --template`, which each book session runs when it chooses.

## The hub

`hub/` here is the hub's page, app and CSS; `tools/hub_build.py` adds the data.
The hub repo (`lanehaden157/bible`, Pages) rebuilds itself from pushed code:
its `.github/workflows/rebuild.yml` runs daily and on "Run workflow", and
commits only on change. So after a core or unit push, press the button (or
wait a day); no manual rebuild needed. The workflow clones every book with a
row in `canon/books.json` (site + repo), and `tools/new_book.py` adds that
row, so a new book needs no workflow edit. Don't edit the hub repo by hand. The
local `hub_build.py` also reads unpushed work, so use it for previews only.
