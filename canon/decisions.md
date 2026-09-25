# Canon decisions: settled across books

Vendored from `bible-core/canon/decisions.md` as `canon-decisions.md` and
synced into each project. It holds calls that apply across books, so a new
book's project doesn't re-argue them (review F22). Wording defaults live in
`canon-conventions.md`, and each book's own declined candidates live in its
`data/roots.json` `declined{}`. A book may depart from any row here, as long as it
records the change and the reason in its own style reference.

Add a row when Lane settles something that a second book would otherwise
ask again.

## Decided

| date | call | where it shows |
|---|---|---|
| 2026-09-22 | ḥesed stays untranslated as the Hebrew Bible default. | `canon-conventions.md` |
| 2026-09-22 | The promotion policy is Joshua's: Claude decides, mostly autonomously, and asks when unsure. | style reference, core workflow |
| 2026-09-22 | Each book's unit map comes from its own project side, once its resources are compiled. | book setup |
| 2026-09-24 | Studies cite English (KJV) verse numbering. The word table and reading text keep the corpus's own. | `book.json` `versification`, `<book>-versification.md` |
| 2026-09-24 | Canon registries are four flat files in bible-core `canon/`: arcs (creation, covenant, exile, presence; extendable), canon threads, type-scenes, intertext. | `canon/*.json` |
| 2026-09-24 | Canon threads so far: inheritance, rest, fear, torah, tassels, charge. Book thread slugs are never renamed to match a canon thread. The canon thread maps to them instead. | `canon/threads.json` |
| 2026-09-24 | Type-scenes so far: commissioning, scouts, water-crossing, census, mountain-theophany, annunciation. | `canon/typescenes.json` |
| 2026-09-24 | Transliteration schemes are frozen per language and never harmonised across languages. | language adapters |

## Declined

| date | proposal | why |
|---|---|---|
| 2026-09-22 | Migrating Joshua and Matthew onto the shared core | Forward-only. They keep their own code and cherry-pick fixes. |
