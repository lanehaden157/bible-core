# {{BOOK}}

How this repo behaves. The artifact contract lives in
`{{SLUG}}_study_style_reference.md` and is authoritative over this file.

Built on **bible-core** (vendored in `biblecore/`, version in
`biblecore/CORE_VERSION`). The shared shape and the ways a book is expected to
differ are in `bible-core/ARCHITECTURE.md`; shared wording defaults in
`bible-core/canon/conventions.md`.

**State:** new book, no units built.

## Commands (run from this folder)

    python -m biblecore build            # everything downstream of units/*.html
    python -m biblecore port 5 [--dry]   # port source-artifacts/{{SLUG}}_05_translation.html
    python -m biblecore port 5 --force   # re-port a built unit (source must be current)
    python -m biblecore audit            # tracked-thread coverage (--ids ROOT to preview an id set)
    python -m biblecore colour ROOT      # colour for a thread about to be promoted
    python -m biblecore data-w 5         # after promoting: fill the new thread's spans in place
    python -m biblecore leads            # canon-leads for built units + the next one
    python -m biblecore corpus           # rebuild the word table from morphhb (npm ci first)
    python -m biblecore sync             # push chat-side files to the synced mirror
    python -m biblecore book             # show resolved settings

`book.json` holds everything book-specific (closed keys: an unknown key is an
error). Change behaviour for this book by adding a book-local module that
wraps a core function, not by editing `biblecore/`; `python ../bible-core/tools/core_diff.py`
reports edits made there. Update the vendored copy with
`python ../bible-core/tools/core_sync.py .`.

## Policy files

`data/threads.json` and `data/roots.json` are policy: the porter proposes, a
human applies. Thread colours come from `python -m biblecore colour`, never
picked by eye. Claude decides whether a candidate becomes a tracked thread,
biased toward book-wide, and asks Lane only when genuinely unsure.

## Corpus

✎ Record the morphhb pin, the verse/word/paragraph counts `python -m biblecore corpus`
reports, and the check against a printed edition. If a count drifts on
re-fetch, flag it loudly.

## Session files

`session_index.md` (read first), `improvements_log.md`, and a
`session_summary_<date>.md` per session.
