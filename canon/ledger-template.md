# Ledger template: `<book>_NN_notes.md`

Vendored from `bible-core/canon/ledger-template.md`. Pass 2's notes file: one
table row per link considered, appended as each is judged (not written up at
the end), rejected rows included. It is what survives a compaction and what the
verse chat is given, so a row says how it is known.

Header, first: `Unit NN, <passage>, notes file`.

| verse | target | kind | evidence | wording read | status | strength | verdict |
|---|---|---|---|---|---|---|---|

- **verse:** where in this unit (C:V).
- **target:** the earlier or later passage it links to (Book C:V).
- **kind:** echo, story, parallel, intertext, type-scene, wordplay, other.
- **evidence:** the shared words, in transliteration, with lemma ids from the
  unit pack where it gives them.
- **wording read:** the words actually read in the target, in English or
  transliteration, or "not read". Only a row with real wording is VERIFIED.
- **status:** VERIFIED (read this chat), SHEET (from the pack or leads only),
  SECONDHAND (a summary of a source) or RECALLED (from memory).
- **strength:** strong, possible, weak.
- **verdict:** ship (root echo, aside.echo, footnote, story box), keep as
  tentative, or drop, with a few words why.

For a story worth telling, follow the table with its story, same, different and
what it does here.

End the file with:

- **Source status:** what was read, what is secondhand, what was unavailable by
  verse, and where the paragraph markers came from.
- **Rows:** `Unit NN: N rows` (the count of table rows), so the next chat can
  say it back.
