# Project side

Files that round-trip with the {{BOOK}} Claude.ai research project. The list
is `book.json` → `sync`; `python -m biblecore sync` mirrors them flat into
`project-side/synced/` (commit + push), which the project's GitHub connector
reads. `python -m biblecore sync-check` reports which files changed since
they were last marked synced.

| file | direction | role |
|---|---|---|
| `{{SLUG}}_study_style_reference.md` | repo → project | the artifact contract |
| `translation-choices.md` | repo → project | the book's glossary |
| `canon-conventions.md` | repo → project | shared wording defaults (vendored from bible-core) |
| `threads-digest.md` | repo → project | tracked threads (generated) |
| `data/roots.json` | repo → project | tracked-thread id sets, declined ledger |
| `{{BOOK}}-words.tsv` | repo → project | the word table (ids for candidates) |
| `canon-leads/canon-leads-unit-NN.md` | repo → project | intertext pass reading lists |
| `CHAT_SIDE_INSTRUCTIONS.md` | pasted by hand | the project's instruction field |
| `resources.md` | project only | the commentary inventory |
| `source-artifacts/{{SLUG}}_NN_translation.html` | project → repo | each unit's artifact |
