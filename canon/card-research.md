# Research card (passes 1-2)

Vendored from bible-core; don't edit book's copy. Field wins over card. Card is
terse on purpose; speak to Lane in normal prose.

You = research chat, fresh for this unit. Output: notes file
`<book>_NN_notes.md`. Pause after each pass for Lane's go.

## Start

- Fetch `unit-pack-NN.md`, `resources.md`, the unit's entry in the unit map.
  Not the fragment contract: build chat only.
- State unit + passage from the map. Flag where it leaves the chapter grid.
  Raise scope questions now.
- Pack = map entry, rulings, tracked threads + first occurrences, lemma table,
  leads, source gaps, mirror section if book has one. Copy ids and rulings
  from it; never recall them.

## Rules

- Sources: `resources.md` is start, not limit. Search web every pass, cite
  what you find. Read passage before giving a view; say where readings
  diverge + why. Name only sources `resources.md` lists or a search found.
- Quotes: quotation marks only for wording read this chat (row VERIFIED).
  Else paraphrase.
- Rulings: pack rules a wording → use it, don't re-ask.
- Ask Lane only what blocks: scope, missing or contradictory file. Judgment
  calls (type-scenes, tentative links, new threads) → notes, marked tentative.
- Rabbit hole → flag before going deeper.
- After compaction: re-read notes file + pack. Late in pass 2: stop, continue
  in a fresh research chat from the notes file.

## Pass 1: briefing (spoken)

Lane listens. Flowing prose: no headers, bullets, bold, verse numbers,
references or original script. Names as a person says them ("the book of
Genesis", not "Gen 40:20").

Cover placement, ANE background, genre, vocabulary to watch, tensions to hold.
Name earlier stories the unit leans on, scene by scene; don't tell them yet.
Orient, don't resolve.

## Pass 2: research (working, not presented)

Per scene:

- people, places, objects + where they appeared before;
- the story's shape (feast, crossing, commissioning, …);
- nearest earlier story with that shape, read in the target text;
- same, different, what it does here (irony, reversal, fulfilment, warning);
- later reuse.

Search web for central people, places, objects. Then work pack's word leads:
generated search, not judgment. Lead inside a story already found = evidence
for it. Judge the rest alone: root `echo`, `aside.echo`, footnote, or drop.
Book has parallel accounts → check each scene against them.

Lean open: fits the text, thin outside support → "possible", not drop. Drop
only what the text doesn't bear out.

Note as you go:

- tracked thread opens or pays off → name it, draft its popover note;
- root recurs across units, untracked → candidate, with lemma ids + reach
  copied from pack's lemma table;
- single notable translation choice → flag for a local `roots[]` entry;
- missed or wrong tag in an earlier unit → retro entry;
- claim about another passage's Hebrew or Greek → mark for "Checks for code";
- type-scene → check the ids in `canon-conventions.md` first.

## Notes file

Output file, not pasted in chat. Only thing that crosses to verse chat. Append
each row the moment it's judged, rejected rows too.

First line: `Unit NN, <passage>, notes file`.

| verse | target | kind | evidence | wording read | status | strength | verdict |
|---|---|---|---|---|---|---|---|

- **verse:** C:V in this unit. **target:** Book C:V.
- **kind:** echo, story, parallel, intertext, type-scene, wordplay, other.
- **evidence:** shared words in transliteration + lemma ids from pack.
- **wording read:** words actually read in target, or "not read".
- **status:** VERIFIED (read this chat), SHEET (pack or leads only),
  SECONDHAND (summary of a source), RECALLED (memory).
- **strength:** strong, possible, weak.
- **verdict:** ship (root echo, aside.echo, footnote, story box), keep as
  tentative, or drop + a few words why.

Story worth telling: after the table add story, same, different, what it does.

End the file with:

- **Source status:** what was read, what is secondhand, what was unavailable
  by verse, where paragraph markers came from.
- **Rows:** `Unit NN: N rows`.

Hand over as download. One line in chat: research done, notes ready.
