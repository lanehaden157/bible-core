# Book on bible-core (shared guide)

Vendored with `biblecore/`; don't edit. The book's `CLAUDE.md` imports this,
holds the book's differences, and wins. Starting point, not gospel: a book may
drop the import and keep a full file of its own.

State isn't written down: `python -m biblecore book` prints it. Core version:
`biblecore/CORE_VERSION`. Shared design: `../bible-core/ARCHITECTURE.md`.

## Commands (book root)

    python -m biblecore book             # where the book stands
    python -m biblecore port 5 [--dry]   # port source-artifacts/<slug>_05_translation.html
                                         # (--force re-ports; --answers FILE carries a dry run's answers)
    python -m biblecore build            # everything downstream of units/*.html
    python -m biblecore audit            # thread coverage; gaps end with ready `add` JSON
    python -m biblecore test [--quick]   # pin, units, contracts, build idempotence
    python -m biblecore sync             # mirror chat-side files, commit, push (after Lane's OK)

`python -m biblecore` lists the rest. CI runs `test` on every push.

## Files

- `book.json` = everything book-specific. Unknown key = error.
- Don't edit `biblecore/`. Change behaviour with a book-local module wrapping
  a core function. `python ../bible-core/tools/core_diff.py .` lists edits
  there; `--template` lists template changes not taken. Re-vendor:
  `python ../bible-core/tools/core_sync.py .`.
- Generated or vendored, don't edit: `index.html`, `app/*.js`, `css/core.css`,
  `components.css`, `division.css`, `data/components.json`,
  `components-reference.md`, `card-*.md`, `fragment-contract.md`,
  `canon-conventions.md`. Look = `css/theme.css` + `book.json`. Shell change →
  bible-core `biblecore/web/`.
- Commit `data/`, `css/`, `app/`, `index.html`, `units/`, `canon-leads/`,
  `threads-digest.md` with the change that regenerated them. `out/` =
  gitignored scratch.
- Fragment rules: `fragment-contract.md` (shared) + the book's style
  reference (its differences; wins).

## Chat side

- Repo → project: `sync` mirrors the sync list flat into
  `project-side/synced/`, writes `synced-index.md` (the one list), commits,
  pushes. Add a file: `book.json` `sync.extra`. Drop a default: `sync.skip`.
- Not synced: `CHAT_SIDE_INSTRUCTIONS.md` (Lane pastes it into the instruction
  field; say when it changed) and
  `source-artifacts/<slug>_NN_translation.html` (project → repo, before
  `port`).

## Threads

`data/threads.json` + `data/roots.json` = policy: porter proposes, human
applies. Claude decides promotions, biased book-wide; close call → Lane.
Colours from `python -m biblecore colour`; hand-pick only if Lane asks.
Promotion → every occurrence in every built unit needs `data-w`:
`python -m biblecore data-w N` fills most and prints the recipe for the rest.

## Asking Lane

Questions (porter's `questions[]`, wording calls, thread decisions) →
AskUserQuestion popups, recommended first + marked, four per call.

## Concurrent sessions

Other sessions may be editing `../bible-core` or this repo. `git status`
first; dirty → worktree; stage explicit paths. More: `../bible-core/CLAUDE.md`.

## Session files

`session_index.md`: read first. Standing state + last three sessions, one line
each; older lines → `history/session_index_archive.md`. `history/` = was, not
is: `improvements_log.md` (only what git can't show), `session_summary_<date>.md`
(substantial sessions with open questions), old prompts, audits, reviews. Read
only if needed. A gotcha that still bites goes in a rule file or a code check.
