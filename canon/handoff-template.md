# Handoff template: `<book>_NN_handoff.md`

Vendored from `bible-core/canon/handoff-template.md`. The verse chat fills this
in after Lane's yes on the box list; Lane pastes it into a fresh build chat.
Say what the fragment must carry, not how the research got there. Judgment
only: rulings, first occurrences, lemma ids and reach are in the unit pack, so
don't restate them. Keep every heading; write "none" under an empty one.

## Scope

Unit number, passage (`C:V-C:V`), title, any scoping calls Lane made, and
`Notes: N rows` (the notes file's row count as confirmed).

## Verse by verse

In verse order, skipping verses with nothing to carry:

- settled renderings, citing the ruling. An open rendering isn't written here:
  point to its call ("see Call 3");
- roots to tag (`data-root` slugs, with translit and gloss for a local one);
- gloss and footnote points, each footnote with a bold lead.

## Approved boxes

One draft per approved box: `### Title`, then labelled lines **Kind**,
**Anchor** (the C:V in this unit), **Ref** (the passage it points at),
**Story**, **Same**, **Different**, **Does**. An echo may omit Story, Same and
Different. Quotation marks only for a quote the notes mark VERIFIED.

| kind | where it lands |
|---|---|
| story | `aside.story` box |
| parallel / synoptic | `aside.synoptic` box |
| echo | `aside.echo` box |
| OT pointer | the book's own pointer form, if its style reference defines one |
| intertext | `intertext[]` entry in the unit meta (no box) |
| type-scene | `typescenes[]` entry in the unit meta (no box) |

Use only kinds the book's style reference enables. End with a one-line count
("14 rows considered, 9 ship, 5 dropped").

## Decisions

Wording and glossary calls Lane made in this chat, one line each: the lexeme
or phrase, the rendering chosen, the reason. Claude Code applies them.

## Threads

- **Opens and payoffs:** each with a one-line popover note.
- **Promotion candidates:** `id` (an ASCII `[a-z0-9-]` slug), lemma ids copied
  from the pack, `gloss`, the opener note and the reason. No refs, reach,
  retrofit units or JSON: code computes them. A payoff you want is just its
  unit and note.
- **Retro entries:** fixes to earlier units' tags.

## Calls for Lane (N) (the build chat asks these first)

Every call that is Lane's, numbered, with the count in the heading. This is the
only place a provisional rendering, a "to flag" wording or an open question
appears. Each call: the verse, 2-3 options with the recommended one first, and
a one-line reason for each. A settled ruling that merely looks odd isn't a
call. "None" only if "Verse by verse" has no provisional rendering.

## Checks for code

Claims about other passages' Greek or Hebrew for the code side to verify, one
row each: `ref, claim, expected lemma(s)`. Give the lemma in transliteration
(`petra`, `gulgolet`; diacritics optional) or as a pack id (`H1538`). A leading
`!` means the word should be absent (`!kleis`). A ref may pool several passages
(`Isa 38:10 / Wis 16:13`). Write only claims you read, not guesses.

## Source status

Copied from the end of the notes file: what was read this chat, what is
secondhand, what was unavailable by verse, and where the paragraph markers
came from.
