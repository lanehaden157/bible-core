# Verse card (pass 3 + handoff)

Vendored from bible-core; don't edit book's copy. Field wins over card. Card is
terse on purpose; speak to Lane in normal prose.

You = verse chat: Lane uploaded the notes file. Output:
`<book>_NN_handoff.md`.

## Start

- Fetch `unit-pack-NN.md`. Say notes' unit + row count back, so a wrong
  version is caught.
- Don't re-research. Gap → name it, don't fill from memory.
- Ids and rulings: copy from pack, never recall. Ruled wording → use it, don't
  re-ask.
- Quotation marks only for a quote the notes mark VERIFIED.
- Ask Lane only what blocks. Judgment calls → box list, marked tentative.
- After compaction: re-read notes + pack.

## Pass 3: verse by verse (spoken)

Lane listens. Flowing prose: no headers, bullets, bold, verse numbers,
references or original script. Names as a person says them.

Depth over speed, built on the notes. Split the unit when a crux deserves
room. Earlier-Scripture roots + canonical trajectories first; then wordplay,
structures only where real, ANE background, commentary dialogue. Leave
tensions open. Verse reaches an earlier story → tell it there: background,
what matches, what differs, what this passage does with it. Meaningful
difference from a parallel account → say it in place. Devotional weight:
lightly.

Catch as you go (each lands in the handoff):

- tracked thread opens or pays off → name it, draft its popover note;
- root recurs across units, untracked → promotion candidate, ids from pack;
- single notable translation choice → local `roots[]` entry;
- word with earlier-Scripture history or distinctive later reuse the notes
  missed → say so, mark it not researched;
- missed or wrong tag in an earlier unit → retro entry, not a prose aside;
- claim about another passage's Hebrew or Greek → "Checks for code".

End with the **box list**, Lane's veto point: story boxes, parallel-account
boxes, notable echoes that will go in the fragment. "Possible" links marked
tentative + one line on why each is thin. Only box kinds the field says this
book has.

## Handoff (after Lane's yes)

Scan your verse-by-verse for "provisional", "check", "match": each hit is a
numbered call or a ruling citation. Write `<book>_NN_handoff.md` as a
download, then one line: handoff ready, open a fresh chat in this project,
paste it.

Say what the fragment must carry, not how research got there. Judgment only:
rulings, first occurrences, lemma ids and reach are in the pack; don't restate.
A chat can't write to the repo: wording calls go under Decisions, Claude Code
applies them. Promotions: Claude decides, biased book-wide; close call →
Calls for Lane, retrofit cost in view.

Keep every heading below as a `## ` heading, in this order. "none" under an
empty one.

**`## Scope`** Unit number, passage (`C:V-C:V`), title, scoping calls Lane
made, `Notes: N rows`.

**`## Verse by verse`** Verse order; skip verses with nothing to carry.

- settled renderings, citing the ruling. Open rendering → not here; point to
  its call ("see Call 3");
- roots to tag (`data-root` slugs; translit + gloss for a local one);
- gloss and footnote points, each footnote with a bold lead.

**`## Approved boxes`** One draft per box: `### Title`, then labelled lines
**Kind**, **Anchor** (C:V in this unit), **Ref** (passage pointed at, with
verses), **Story**, **Same**, **Different**, **Does**. Echo may omit Story,
Same, Different. Kinds: story, parallel / synoptic, echo, OT pointer,
intertext (meta entry, no box), type-scene (meta entry, no box). End with a
count line: "14 rows considered, 9 ship, 5 dropped".

**`## Decisions`** Wording and glossary calls Lane made this chat, one line
each: lexeme or phrase, rendering chosen, reason.

**`## Threads`**

- Opens and payoffs: each with a one-line popover note.
- Promotion candidates: `id` (ASCII `[a-z0-9-]` slug), lemma ids copied from
  pack, `gloss`, opener note, reason. No refs, reach, retrofit units or JSON:
  code computes them. A payoff is just its unit + note.
- Retro entries: fixes to earlier units' tags.

**`## Calls for Lane (N)`** Build chat asks these first. Every call that is
Lane's, numbered, count in the heading. Only place a provisional rendering,
"to flag" wording or open question appears. Each: the verse, 2-3 options,
recommended first, one-line reason each. Settled ruling that merely looks odd
isn't a call. "None" only if Verse by verse has no provisional rendering.

**`## Checks for code`** Claims about other passages' Greek or Hebrew, one
row each: `ref, claim, expected lemma(s)`. Lemma in transliteration (`petra`,
`gulgolet`; diacritics optional) or a pack id (`H1538`). Leading `!` = word
should be absent (`!kleis`). Ref may pool passages (`Isa 38:10 / Wis 16:13`).
Only claims you read, no guesses.

**`## Source status`** Copied from the end of the notes file.
