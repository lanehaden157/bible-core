# Handoff template: `<book>_NN_handoff.md`

Vendored from `bible-core/canon/handoff-template.md`. The verse chat fills
this in after Lane's yes on the box list (the closing spoken list of pass 3) and hands it over as a download;
Lane pastes it into a fresh chat in the project. Say what the fragment must
carry, not how the research got there. The handoff holds judgment only: rulings,
first occurrences, lemma ids and reach are in the unit pack (`unit-pack-NN.md`),
so don't restate them. Leave an empty section's heading in with "none", so the
build chat knows it was considered.

## Scope

Unit number, passage (`C:V-C:V`), title, and any scoping calls Lane made. Add
`Notes: N rows`, the notes file's row count as the verse chat confirmed it.

## Verse by verse

What the fragment must carry, in verse order, condensed from pass 3. Per verse
(skip verses with nothing to carry):

- settled renderings (cite the ruling). A rendering still open is not written
  here: point to its call ("see Call 3");
- roots to tag (`data-root` slugs, with translit and gloss for a local one);
- gloss and footnote points, each with a bold lead for a footnote.

## Approved boxes

One draft for each box Lane approved, as `### Title` followed by labelled lines:
**Kind**, **Anchor** (the C:V in this unit it sits at), **Ref** (the passage it
points at, with verses), **Story**, **Same**, **Different** and **Does** (what
it does here). An echo may leave Story, Same and Different out. Text in
quotation marks is a quote the notes mark VERIFIED; paraphrase without them
otherwise. The kinds are a per-book mapping (the style reference says which
the book enables; a kind it doesn't enable isn't used):

| kind | where it lands |
|---|---|
| story | `aside.story` box |
| parallel / synoptic | `aside.synoptic` box |
| echo | `aside.echo` box |
| OT pointer | the book's own pointer form, if its style reference defines one |
| intertext | `intertext[]` entry in the unit meta (no box) |
| type-scene | `typescenes[]` entry in the unit meta (no box) |

End with a one-line count of what the ledger dropped ("14 rows considered, 9
ship, 5 dropped").

## Decisions

Wording and glossary calls Lane made in this research chat (a chat can't write to
the repo): lexeme or phrase, the rendering chosen, and the reason, one line each.
Claude Code applies them to `translation-choices.md` and the glossary after the
session. "None" if there are none.

## Threads

- **Opens and payoffs:** each with a one-line popover note.
- **Promotion candidates:** each as `id` (an ASCII `[a-z0-9-]` slug), lemma ids
  copied from the pack's lemma table, `gloss`, the opener note, and the reason.
  Don't write `opens`/`payoffs` refs, reach or retrofit units, and don't write
  JSON: code computes them from the lemma set when the unit is ported. A payoff
  you want is just its unit and note. These become `threads.promote[]`.
- **Retro entries:** fixes to earlier units' tags (`threads.retro[]`).

## Calls for Lane (N) (the build chat asks these first)

Every call that is Lane's to make, numbered, with the count in the heading: the
only place a provisional rendering, a "to flag" wording or an open question
appears. Each call: the verse, 2-3 options with the recommended one first, and a
one-line reason for each. A settled ruling that merely looks odd is not a call:
the pack carries it. "None" is allowed only if "Verse by verse" has no provisional
rendering.

## Checks for code

Claims about other passages' Greek or Hebrew that the code side can verify
against the corpus, one row each: `ref, claim, expected lemma(s)`, the lemma in
transliteration (`petra`, `hades`, `gulgolet`; macrons, apostrophes and doubled
letters optional). A lemma id from the pack works too (`H1538`). For a word that
should be *absent*, write a leading `!` (`!kleis`). A ref may name several
passages (`Isa 38:10 / Wis 16:13`); their words are pooled. These become
`checks[]`; code resolves the transliteration to lemma ids and returns any that
don't match as one list for Lane, so write only claims you read, not guesses.

## Source status

Copied from the end of the notes file: what was read this chat, what is
secondhand, what was unavailable by verse, and where the paragraph markers came
from. The build chat and Lane use it to see what was actually read. Quote only
what the notes mark VERIFIED, and without quotation marks for anything else.
