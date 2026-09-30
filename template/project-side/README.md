# Project side

How files move between this repo and the {{BOOK}} Claude.ai research project.

**Repo → project: synced, never uploaded by hand.** Core supplies the
default list (`biblecore/sync.py` `DEFAULT_SYNC`); `book.json` → `sync` holds
only this book's additions (`extra`) and exclusions (`skip`).
`python -m biblecore sync` mirrors the resolved files flat into
`project-side/synced/`, removes any mirror file that has left the list, then
commits and pushes it, and the project's GitHub connector reads that folder. It pushes on its own, so run it when Lane has OK'd
the push (normally together with the commit that caused the change). Each sync also writes
`synced/synced-index.md`, the complete list with each file's role. That's
the only list, so don't restate it elsewhere. `python -m biblecore sync-check`
reports which files changed since they were last synced (the build runs it too).

To sync another file, add it to `book.json` → `sync.extra` (a path or a glob
pattern); to stop syncing a default, add it to `sync.skip`. A file every book
should sync belongs in core's `DEFAULT_SYNC`, with a role in `ROLES`.

**Not synced:**

| file | direction | why |
|---|---|---|
| `CHAT_SIDE_INSTRUCTIONS.md` | pasted by hand into the instruction field | the connector can't write the field. `sync-check` says when it needs re-pasting; run `sync-check --mark-pasted` after pasting |
| `source-artifacts/{{SLUG}}_NN_translation.html` | project → repo | each unit's artifact, saved into the repo before `port` |
