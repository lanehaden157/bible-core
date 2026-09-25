# Project side

How files move between this repo and the {{BOOK}} Claude.ai research project.

**Repo → project: synced, never uploaded by hand.** `book.json` → `sync` is
the list. `python -m biblecore sync` mirrors those files flat into
`project-side/synced/`, then commits and pushes, and the project's GitHub
connector reads that folder. Each sync also writes
`synced/synced-index.md`, the complete list with each file's role. That's
the only list, so don't restate it elsewhere. `python -m biblecore sync-check`
reports which files changed since they were last synced (the build runs it too).

To sync a new file, add it to `book.json` → `sync`. If it's a core file,
also give it a role in `biblecore/sync.py` `ROLES`.

**Not synced:**

| file | direction | why |
|---|---|---|
| `CHAT_SIDE_INSTRUCTIONS.md` | pasted by hand into the instruction field | the connector can't write the field. `sync-check` says when it needs re-pasting; run `sync-check --mark-pasted` after pasting |
| `source-artifacts/{{SLUG}}_NN_translation.html` | project → repo | each unit's artifact, saved into the repo before `port` |
