# Condensed card (one chat)

Vendored from bible-core; don't edit book's copy. Field wins over card. Card is
terse on purpose; speak to Lane in normal prose.

You = the one chat for a condensed or digest unit (unit map Tier). Output: the
unit's fragment, `<slug>_NN_translation.html`, a file, not an Artifact-tool
page. Fragment rules, open calls, drafting and saving: `card-build.md`, so
fetch it and follow it, with the changes below.

## Start

Fetch what `card-build.md` lists, plus `unit-pack-NN.md`, `resources.md` and
the unit's map row (Tier, Peak, stretches, Digests). No handoff exists: you
are all three chats, shortened, and your own findings stand in for it. Say the
unit, passage, tier and stretches back to Lane before drafting.

## Research, short

- One pass over the passage and the pack's leads. Search the web for what the
  passage leans on. Keep only links the text bears out; the rest are tentative
  or dropped. Quotation marks only for wording read this chat.
- No spoken briefing, no verse-by-verse pass. What a handoff would carry (calls
  for Lane, checks for code, thread notes, wording decisions) goes straight
  where `card-build.md` says: popups first, then `checks[]`, `threads`,
  `questions[]`.

## Build

- Meta keys: `unit`, `passage`, `title`, `roots`, `threads` (all four
  sub-keys), `digest`; `checks`, `questions` when needed
  (see `fragment-contract.md`; `digest` is in components-reference.md).
- Tier condensed: translate the key verses as `p.v` blocks. The rest go in
  components (`table.list`, `div.itin`, others the book enables) with exact
  `data-verses`. Tier digest: `section.block.digest` blocks with exact
  `data-verses`; write no `p.v` inside a digest stretch.
- A stretch the map marks condensed or digest inside a full unit: same rules
  for that stretch.
- A verse is written out or summarised, never both (`data-verses` is checked).
  Tracked-thread spans inside a summary are colour-only.
- Summaries say only what the verses say. Add no echo, structure or link the
  text doesn't show; the lens's "tentative" rule applies.
- `digest`: two to four sentences, 80 words at most, the unit whole, for a
  reader on the peaks path. Required, every tier.

Revision → surgical edits, not a rebuild.
