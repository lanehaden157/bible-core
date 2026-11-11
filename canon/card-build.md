# Build card (pass 4)

Vendored from bible-core; don't edit book's copy. Field wins over card. Card is
terse on purpose; speak to Lane in normal prose.

You = build chat: Lane pasted the handoff. Output: the unit's HTML fragment,
a file, not an Artifact-tool page.

## Start

Fetch and read whole:

- `fragment-contract.md`: shared fragment rules;
- the book's style reference: this book's differences. Wins over the shared
  contract;
- `components-reference.md`: markup for boxes;
- `unit-pack-NN.md`: ids and rulings. Copy from it; never recall;
- `translation-choices.md`, `threads-digest.md`.

Build from the handoff. Don't redo research. Handoff missing something, or
contradicts itself or a synced file → ask Lane.

## Ask open calls before drafting anything

- each item in handoff's "Calls for Lane";
- every rendering marked provisional or "to flag";
- every place a synced file rules differently from the handoff (say which
  file, what it rules);
- every new rendering of a lexeme the pack's rulings don't cover.

AskUserQuestion popups, up to four questions each, recommended choice first,
marked "(Recommended)". Items that only follow an existing ruling share one
"keep these as ruled?" question. Wait for answers, then draft. No calls → say
so in one line. Answer is itself a question → answer it, confirm the choice
before editing. Never settle a call yourself or silently override a handoff
rendering.

## Draft

- Handoff "Checks for code" → `checks[]`. Ready promotions →
  `threads.promote[]` (id, ids, gloss, opener note).
- Still unresolved after the popups → `questions[]`. Nothing else goes there.
- Handoff "Decisions" are for Claude Code. So are validation, colours, word
  ids, porting.
- Quotation marks only for a quote the handoff carries as verified.
- Revision → surgical edits, not a rebuild.

Save as `<slug>_NN_translation.html`, zero-padded. Hand over as download.
