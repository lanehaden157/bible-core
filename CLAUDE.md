# bible-core

How this repo behaves. `README.md` maps the files; `ARCHITECTURE.md` is the
shared shape, where books are expected to differ, and how the core changes
(§8 covers the release checklist). `../core-plan-remaining.md` is the open
plan.

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

    python tests/run.py                  # the whole suite (no pytest needed)
    python tools/core_sync.py <book-dir>  # vendor into a book (refuses if dirty)
    python tools/core_diff.py <book-dir>  # book-local edits made to biblecore/
