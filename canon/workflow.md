# Core workflow (every book)

Vendored from `bible-core/canon/workflow.md` and synced into each project's
`synced/` folder. Don't edit the book's copy. The project's own instruction
field holds the lens, the language rules and anything this book does
differently, and **where the two disagree, the instruction field wins for
that book.**

## What's on hand

`resources.md` lists the texts, digests and commentaries, with what each is
good for. Read it before pass 1. Cite only commentaries listed there. Say where
readings diverge and why. Where the set can't reach something, say so and search
the web in pass 2.

The synced folder also carries the book's style reference (every artifact
rule), `translation-choices.md` (wording, starting from
`canon-conventions.md`), `canon-decisions.md` (calls already settled across
books), `threads-digest.md` (tracked threads so far), the word table, and the
canon-leads sheets.

## Per unit: four passes, pause and present after each

1. **Pre-read briefing.** Flowing prose, with no headers, bullets or bold. Cover
   placement, ANE background, genre, intertextual setup, vocabulary to watch,
   and tensions to hold. Orient; don't resolve.

2. **Verse-by-verse.** Same prose, depth over speed; split a unit when a crux
   deserves room. Earlier-Scripture roots and canonical trajectories come first,
   then wordplay, structures only where real, ANE background, and the commentary
   dialogue with tensions left open. Note devotional weight lightly. Search the
   web throughout. Cite commentators by name freely here.

3. **Intertext pass.** Its own turn, after Lane confirms pass 2. Start from
   `canon-leads-unit-NN.md` in the synced folder: a generated list of where the
   unit's rare words and shared two-word phrases occur elsewhere in the canon.
   It's a word search, not a judgment. It's blind to common words, themes,
   type-scenes and the New Testament, so the pass starts there but doesn't
   end there.

   The deliverable is a ledger, as a table. It has one row per link considered,
   with the verse, the target text, the kind of link (shared word, shared phrase,
   type-scene, allusion, later reuse, New Testament reception), the evidence, where
   you found it, a strength (strong, possible, weak), and a verdict: a root `echo`,
   an `aside.echo`, a footnote, or drop, with the reason. Rejected rows stay in the
   ledger. Some strong suggestions:
   - Every lead on the sheet gets a row, and you read the target verse.
   - Every tracked thread and notable word gets "where does this first appear,
     and where does it come back?"
   - Central people, places and objects get a web search for later reuse and
     type-scenes.

   A typical unit considers fifteen to thirty links and keeps six to twelve.

   Present the ledger and pause. Lane marks what to keep before the artifact is
   drafted.

4. **Artifact skeleton.** Only after Lane confirms. Draft it in the shape of
   the book's style reference (`<book>_study_style_reference.md`), which holds
   every artifact rule.
   - Mark roots with `data-root` only. Don't hand-chase `data-w` ids; the porter
     fills them.
   - Keep glosses short. Longer material goes in footnotes with a bold lead.
   - Any wording or data call Lane needs to make goes in `questions[]`, not
     asked in chat.

   Lane's Claude Code session handles transliteration, validation, colours,
   word ids and porting.

## Seven standing moves during pass 2

Each one turns an observation into an action:

- A tracked thread opens or pays off → name it and draft the one-line popover
  note now.
- A root recurs across units but isn't tracked → flag it as a candidate, with the
  lemma ids you saw.
- A single notable translation choice → flag it for a local `roots[]` entry.
- A word with an earlier-Scripture history, or a distinctive later reuse → note
  it for the intertext pass's ledger.
- A missed or wrong tag in an earlier unit → a `threads.retro` entry, not a
  prose aside.
- A quotation, allusion or type-scene (commissioning, scouts, water crossing,
  census, …) → an `intertext[]` or `typescenes[]` entry in the meta block.
  Echo asides are harvested automatically, so don't repeat them. Check
  `canon-decisions.md` before proposing a canon thread or type-scene that may
  already be settled.
- A wording or data call only Lane can make → don't ask here. Render your best
  provisional choice, flag it in the fragment, and add a `questions[]` entry.

## Scope

Before each walkthrough, state the unit and passage from the Literary Unit
Map, flag where it diverges from the chapter grid, and raise any scoping questions.
Flag rabbit holes and ask before going deeper. If a request conflicts with a
shipped unit, ask rather than silently rebuild.

## Working style

Prefer surgical edits to rewrites. Confirm scope before each deliverable. When
design or scope is unclear, ask Lane rather than guess.
