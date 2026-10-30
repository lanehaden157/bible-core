# Handoff template: `<book>_NN_handoff.md`

Vendored from `bible-core/canon/handoff-template.md`. The research chat fills
this in after Lane's yes on the box list and presents it as an output file;
Lane pastes it into a fresh chat in the project. Say what the artifact must
carry, not how the research got there. Leave an empty section's heading in with
"none", so the build chat knows it was considered.

## Scope

Unit number, passage, title, and any scoping calls Lane made.

## Rulings in play

Existing renderings this unit uses, so the build chat doesn't re-ask them, one
line each: lexeme or phrase, rendering, where it's ruled. Include a rendering
that looks odd here but is settled.

## Verse by verse

What the artifact must carry, in verse order, condensed from pass 3. Per verse
(skip verses with nothing to carry):

- settled renderings (cite the ruling). A rendering still open is not written
  here: point to its call ("see Call 3");
- roots to tag (`data-root` slugs, with translit and gloss for a local one);
- gloss and footnote points, each with a bold lead for a footnote.

## Approved boxes

One draft for each story box, parallel-account box, echo box and OT pointer Lane
approved: the verse it anchors to, the text it points at, then background, same,
different, and what it does here. End with a one-line count of what the ledger
dropped ("14 rows considered, 9 ship, 5 dropped").

## Threads

- **Opens and payoffs:** each with a one-line popover note.
- **Promotion candidates:** each as a ready `threads.json` entry (`id`, `root`,
  lemma ids, `gloss`, `opens`, `payoffs`) with its reach, e.g. "16 occurrences,
  retrofit in units 1, 2, 5, 11". These become `threads.promote[]`.
- **Retro entries:** fixes to earlier units' tags (`threads.retro[]`).
- **Rows citing this unit's verses:** thread rows in `threads-digest.md` for
  the code side to check against the unit map.

## Calls for Lane (N) (the build chat asks these first)

Every call that is Lane's to make, numbered, with the count in the heading: the
only place a provisional rendering, a "to flag" wording or an open question
appears. Each call: the verse, 2-3 options with the recommended one first, and a
one-line reason for each. A settled ruling that merely looks odd goes under
"Rulings in play". "None" is allowed only if "Verse by verse" has no provisional
rendering.

## Checks for code

Claims about other passages' Greek or Hebrew that the code side can verify
against the corpus, one row each: `ref, claim, expected lemma(s)`, the lemma in
transliteration (`petra`, `hades`; macrons optional). For a word that should be
*absent*, write a leading `!` (`!kleis`). A ref may name several passages
(`Isa 38:10 / Wis 16:13`); their words are pooled. These become `checks[]`, and
Lane doesn't answer them.
