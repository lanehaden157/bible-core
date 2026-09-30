# {{BOOK}}

How this repo behaves. The artifact contract lives in
`{{SLUG}}_study_style_reference.md` and is authoritative over this file.

Built on **bible-core** (vendored in `biblecore/`, version in
`biblecore/CORE_VERSION`). The shared shape and the ways a book is expected to
differ are in `bible-core/ARCHITECTURE.md`; shared wording defaults in
`bible-core/canon/conventions.md`.

**State:** `python -m biblecore book` prints where the book stands (units
built and planned, tracked threads, core pin vs vendored copy, sync and paste
status), read from its data. It isn't written here, so it can't go stale.

## Commands (run from this folder)

    python -m biblecore book             # where the book stands (see State above)
    python -m biblecore port 5 [--dry]   # port source-artifacts/{{SLUG}}_05_translation.html (--force re-ports)
    python -m biblecore build            # everything downstream of units/*.html
    python -m biblecore audit            # tracked-thread coverage (--ids ROOT to preview an id set)
    python -m biblecore test [--quick]   # check the book: pin, units, contracts, build idempotence
    python -m biblecore sync             # mirror chat-side files, commit and push (after Lane's OK)

`python -m biblecore` lists the rest: `colour` and `data-w` for promoting a
thread, `leads`, `units-from-map`, `corpus`, `migrate` after re-vendoring,
`sync-check --mark-pasted` after pasting the instruction field.

`book.json` holds everything book-specific (closed keys: an unknown key is an
error). Change behaviour for this book by adding a book-local module that
wraps a core function, not by editing `biblecore/`; `python ../bible-core/tools/core_diff.py`
reports edits made there. Update the vendored copy with
`python ../bible-core/tools/core_sync.py .`.

## Policy files

`data/threads.json` and `data/roots.json` are policy: the porter proposes, a
human applies. Who decides whether a candidate becomes a tracked thread is set
in the style reference §3. Thread colours come from `python -m biblecore colour`
by default (colours picked by eye collided before); hand-pick one only if Lane
asks.

## Asking Lane

Lane prefers questions (the porter's `questions[]`, wording calls, thread
decisions) as AskUserQuestion multiple-choice popups, best provisional choice
first and marked "(Recommended)", batched four per call, rather than a list in
chat.

## Concurrent sessions

Other sessions may be editing `../bible-core` or sibling books at the same
time. See "Concurrent sessions" in `../bible-core/CLAUDE.md`: check `git status`
first and stage explicit paths.

## Corpus

✎ Record the morphhb pin, the verse/word/paragraph counts `python -m biblecore corpus`
reports, and the check against a printed edition. If a count drifts on
re-fetch, flag it loudly.

## Session files

`session_index.md` (read first), `improvements_log.md`, and a
`session_summary_<date>.md` per session.
