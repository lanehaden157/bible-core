# {{BOOK}}

The artifact contract is `{{SLUG}}_study_style_reference.md`; it wins over this
file. Built on bible-core, vendored in `biblecore/` (version in
`biblecore/CORE_VERSION`). The shared design is `../bible-core/ARCHITECTURE.md`.

State isn't written here: `python -m biblecore book` prints it.

## Commands (run from this folder)

    python -m biblecore book             # where the book stands
    python -m biblecore port 5 [--dry]   # port source-artifacts/{{SLUG}}_05_translation.html
                                         # (--force re-ports; --answers FILE carries a dry run's answers)
    python -m biblecore build            # everything downstream of units/*.html
    python -m biblecore audit            # thread coverage; gaps end with ready `add` JSON
    python -m biblecore test [--quick]   # pin, units, contracts, build idempotence
    python -m biblecore sync             # mirror chat-side files, commit and push (after Lane's OK)

`python -m biblecore` lists the rest. CI runs `test` on every push.

- `book.json` holds everything book-specific. An unknown key is an error.
- Don't edit `biblecore/`. Change this book's behaviour with a book-local
  module that wraps a core function. `python ../bible-core/tools/core_diff.py .`
  reports edits made there, and with `--template` the template changes this
  book hasn't taken.
- Re-vendor with `python ../bible-core/tools/core_sync.py .`.
- `index.html`, `app/*.js`, `css/core.css`, `components.css` and
  `division.css` are generated: don't edit them. This book's look is
  `css/theme.css` plus `book.json`. A shell change goes in bible-core's
  `biblecore/web/`.
- Commit `data/`, `css/`, `app/`, `index.html`, `units/`, `canon-leads/` and
  `threads-digest.md` with the change that regenerated them. `out/` is
  gitignored scratch.

## Threads

`data/threads.json` and `data/roots.json` are policy: the porter proposes, a
human applies (the style reference §3 says who decides). Colours come from
`python -m biblecore colour`; hand-pick one only if Lane asks.

Promoting a thread means every occurrence in every built unit needs `data-w`.
`python -m biblecore data-w N` fills most. The verses it can't decide go in
`retrofit/retrofit-tags.json`:

1. Compare the root's words for the verse in `{{BOOK}}-words.tsv` with the
   fragment's `data-root="ROOT"` spans, in order.
2. Where the counts differ: one span over two source words (`retag`, or split
   by hand); one source word as two spans (`unwrap` one, or give both the same
   `w` with `retag`'s `occ`); an untagged occurrence (`add`).
3. One entry per occurrence: `{"unit", "verse", "from", "to", "text", "w"}`.
   `occ` (1-based) picks between identical spans in a verse. `verse` is `"C:V"`
   in a unit that crosses a chapter.
4. `python -m biblecore build` replays the file and audits. Every promoted
   root should report clean.

## Asking Lane

Ask questions (the porter's `questions[]`, wording calls, thread decisions) as
AskUserQuestion popups, recommended choice first and marked, four per call.

## Concurrent sessions

Other sessions may be editing `../bible-core` or sibling books. `git status`
first and stage explicit paths. More in `../bible-core/CLAUDE.md`.

## Corpus

<!-- lang: hebrew -->
✎ Record the morphhb pin, the counts `python -m biblecore corpus` reports, and
the check against a printed edition. If a count drifts on re-fetch, flag it
loudly.
<!-- /lang -->
<!-- lang: greek -->
MorphGNT and the LXX are git-ignored. After a fresh clone,
`python -m biblecore fetch` restores them at the pinned versions and checks
every sha1. A sha1 failure means the wrong corpus: flag it loudly and don't
build on it.

✎ Record the MorphGNT pin (book.json `corpus.pin`), the counts
`python -m biblecore corpus` reports, and the check against a printed SBLGNT.
<!-- /lang -->

## Session files

`session_index.md` (read first), `improvements_log.md` (only what git can't
show) and `session_summary_<date>.md` (substantial sessions with open questions
only).
