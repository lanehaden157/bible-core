# bible-core

How this repo behaves. `README.md` maps the files; `ARCHITECTURE.md` is the
shared shape, where books are expected to differ, how the core changes, and
how to start a book (§8).

**State (2026-09-29):** core 0.9.10, tests 287/287. Numbers and Joshua are on
core; Matthew is standalone (below). The platform-level record (status and
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
- Bump `__version__` / `CORE_VERSION` / `template/book.json`'s `core` key
  only for a change you're committing in the same breath — don't leave a
  version bumped with unrelated uncommitted work sitting on top of it.
  Check `git log -3` right before bumping in case another session already
  moved main.
- A book's `core_sync.py` refuses to run against a dirty bible-core commit —
  don't route around that by committing someone else's half-finished edit
  just to unblock a vendor.
- After a vendor lands in a book, that book's `CLAUDE.md` should record
  which core commit/version it pulled, so a later session can tell whether
  it's behind.

## Commands (run from this folder)

    python tests/run.py [filter]         # the whole suite (no pytest needed)
    python tools/core_sync.py <book-dir>  # vendor into a book (refuses if dirty)
    python tools/core_diff.py <book-dir>  # book-local edits made to biblecore/
    python tools/new_book.py ...         # start a book from template/ (§8)
    python tools/canon_collect.py        # refresh canon/*.json from the books
    python tools/hub_build.py ../hub     # rebuild the hub by hand (see below)

The tests read the sibling `../Joshua`, `../Numbers` and `../Matthew`
checkouts read-only (README.md has the setup).

## Releasing a core change

1. `python tests/run.py` green; `git status` clean apart from the change.
2. Bump `biblecore/__init__.py` and `template/book.json`'s `core`, add a line
   to ARCHITECTURE.md's version list and its status line. Commit, tag
   `vX.Y.Z`, push both.
3. Vendor into each book: `python tools/core_sync.py <book>`, set the book's
   `book.json` `core`, run its `build` (Matthew is not synced), `python -m biblecore test`, then commit explicit
   paths and push. Run `python -m biblecore sync` where chat-side files changed.
   Stage explicit paths: `git add -A` in a book repo sweeps up other sessions'
   edits.
4. Book settings that gate checks (`checks` in `book.json`) are closed keys:
   a new one goes in `book.py` `CHECK_DEFAULTS` with a test.

## The hub

`hub/` here is the hub's page, app and CSS; `tools/hub_build.py` adds the data.
The hub repo (`lanehaden157/bible`, Pages) rebuilds itself from pushed code:
its `.github/workflows/rebuild.yml` runs daily and on "Run workflow", and
commits only on change. So after a core or unit push, press the button (or
wait a day); no manual rebuild needed. Don't edit the hub repo by hand. The
local `hub_build.py` also reads unpushed work, so use it for previews only.
