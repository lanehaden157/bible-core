# Handoff template: `<book>_NN_handoff.md`

Vendored from `bible-core/canon/handoff-template.md`. The research chat fills
this in after Lane's yes on the box list (pass 3) and presents it as an output
file named `<book>_NN_handoff.md`. Lane pastes it into a fresh chat in the same
project, and that build chat does pass 4 from it. Keep it short: each section
says what the artifact must carry, not how the research got there. The full
ledger stays in the research chat's notes file.

Leave a section's heading in with "none" when it's empty, so the build chat
knows it was considered and not forgotten.

## Scope

Unit number, passage, title, and any scoping calls Lane made (where the unit
diverges from the chapter grid, what was split or held back).

## Rulings in play

Existing renderings this unit uses, so the build chat doesn't re-ask them. One
line each: the lexeme or phrase, the rendering, where it's ruled
(`translation-choices.md`, or an earlier unit's meta). Include a rendering
that looks odd here but is settled.

## Verse by verse

What the artifact must carry, in verse order, condensed from pass 3. Not the
spoken prose. Per verse (skip verses with nothing to carry):

- renderings, with the provisional choice where it's still open;
- roots to tag (`data-root` slugs, tracked or local, with translit and gloss
  for a local one);
- gloss and footnote points, each with a bold lead for a footnote.

## Approved boxes

One draft for each story box, parallel-account (synoptic) box, echo box and OT
pointer Lane approved. Each: the verse it anchors to, the earlier text or
parallel it points at, then background, same, different, and what it does here.
Only the rows that ship. End with a one-line count of what the ledger dropped
("14 rows considered, 9 ship, 5 dropped").

## Threads

- **Opens and payoffs:** the tracked threads this unit opens or pays off, each
  with a one-line popover note.
- **Promotion candidates:** each as a ready `threads.json` entry (`id`, `root`,
  lemma ids, `gloss`, `opens`, `payoffs`) with its reach, e.g. "16 occurrences,
  retrofit in units 1, 2, 5, 11". These become `threads.promote[]`.
- **Retro entries:** fixes to earlier units' tags (`threads.retro[]`).
- **Rows citing this unit's verses:** thread rows (in `threads-digest.md`) that
  cite verses of this unit, flagged for the code side to check against the
  unit map.

## Questions for Lane

Only genuinely open calls the unit's argument depends on. Checked first against
`translation-choices.md` and earlier units' meta. Each with its options and the
provisional choice. The build chat asks these in chat before building.

## Checks for code

Claims about other passages' Greek or Hebrew that the code side can verify
against the corpus. One row each: `ref, claim, expected lemma(s)`. These become
`checks[]` in the unit meta. They are not questions and Lane doesn't answer
them.
