# Project side

How files move between this repo and the {{BOOK}} Claude.ai research project.

**Repo → project: synced, never uploaded by hand.** `python -m biblecore sync`
mirrors the sync list flat into `project-side/synced/`, drops files that left
the list, writes `synced/synced-index.md` (the one complete list; don't restate
it elsewhere), then commits and pushes. It pushes on its own, so run it only
once Lane has OK'd the push. `python -m biblecore sync-check` reports what
changed since the last sync.

The default list is core's (`biblecore/sync.py` `DEFAULT_SYNC`). To sync
another file, add a path or glob to `book.json` → `sync.extra`; to drop a
default, add it to `sync.skip`.

A project chat downloads these whole from raw GitHub ("Where things are" in
`CHAT_SIDE_INSTRUCTIONS.md`).

**Not synced:**

| file | direction | why |
|---|---|---|
| `CHAT_SIDE_INSTRUCTIONS.md` | pasted by hand into the instruction field | the connector can't write the field. Tell Lane when it changed; nothing tracks the paste |
| `source-artifacts/{{SLUG}}_NN_translation.html` | project → repo | each unit's artifact, saved into the repo before `port` |
