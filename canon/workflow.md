# Core workflow (every book)

Vendored from `bible-core/canon/workflow.md` and synced into each project's
`synced/` folder. Don't edit the book's copy. The project's own instruction
field holds the lens, the language rules and anything this book does
differently, and **where the two disagree, the instruction field wins for
that book.**

## What's on hand

`resources.md` lists the texts, digests and commentaries, with what each is
good for. Read it before pass 1. It's a starting point, not a limit: search the
web freely in every pass and cite any commentator or source by name, saying
which you leaned on. Read the passage before attributing a view, and mark
anything you haven't read this chat as "recalled, unverified". Say where
readings diverge and why.

`synced-index.md` in the synced folder lists every synced file and what it's
for. It's generated on every sync, so it's always complete. Everything in that
folder round-trips from the repo automatically; nothing there is uploaded by
hand. The style reference holds every artifact rule.

## Per unit: four passes, one turn each

Passes 1 and 3 are for Lane, who listens to them read aloud, so they're spoken
prose. Passes 2 and 4 are working passes, split out so no one turn carries too
much and loses context. Pause after each pass for Lane's go-ahead.

1. **Briefing (for listening).** Flowing prose, with no headers, bullets or
   bold. Cover placement, ANE background, genre, intertextual setup, vocabulary
   to watch, and tensions to hold. The intertextual setup also names the
   earlier stories the unit seems to lean on, scene by scene, without telling
   them yet. Orient; don't resolve.

2. **Research (a working pass, not presented).** Scene by scene, in writing:
   - the people, places and objects, and where they appeared before;
   - the story's shape (a feast, a feeding in want, a crossing, a commissioning,
     a prophet rejected at home, …);
   - the nearest earlier story with that shape, read in the target text;
   - what's the same and what's different;
   - what it does here (irony, reversal, identification, fulfilment, warning);
   - later reuse.

   Search the web for the central people, places and objects. Then the word
   leads, `canon-leads-unit-NN.md` in the synced folder: a generated list of
   where the unit's rare words and shared two-word phrases occur elsewhere, and
   (for a Greek book) a noun sweep of the unit's people, places and objects
   with their first LXX verse and the other gospels' verses. It's a word
   search, not a judgment. A lead that falls inside a story already found is
   evidence for it; the rest are judged on their own (root `echo`,
   `aside.echo`, footnote, or drop). Then, where the book has parallel
   accounts (the other gospels for a gospel, Chronicles beside Kings), each
   scene against them. Every tracked thread and notable word gets "where does
   this first appear, and where does it come back?" Prune as you go.

   The output is a **notes file** (a chat-side output file, not pasted into
   chat). It doubles as the full ledger: every link considered, with the
   verse, the target text, the kind, the evidence, a strength (strong,
   possible, weak) and the verdict, rejected rows included; and for a story
   worth telling, the story, same, different and what it does. Passes 3 and 4
   read it. In chat, say one line: research done, ready for the
   verse-by-verse. Lane doesn't read the notes file.

3. **Verse-by-verse (for listening).** Flowing prose, depth over speed, built
   on the notes; split a unit when a crux deserves room. Earlier-Scripture
   roots and canonical trajectories come first, then wordplay, structures only
   where real, ANE background, and the commentary dialogue with tensions left
   open. When a verse reaches an earlier story, tell it there: its
   background, what matches, what's different, and what this passage does with
   it. Meaningful differences from a parallel account are spoken in place
   too. Spoken style throughout: no verse numbers, references or original
   script in the telling, and names said the way a person would say them ("the
   book of Genesis", not "Gen 40:20"). Note devotional weight lightly. Search
   the web throughout. Cite commentators by name freely here.

   End with a short spoken list of what will go into the artifact: the story
   boxes, the parallel-account boxes, the notable echoes. That list is Lane's
   veto point, usually a quick yes.

4. **Artifact (a working pass).** Only after Lane confirms. Build it from the
   notes file and pass 3, in the shape of the book's style reference
   (`<book>_study_style_reference.md`), which holds every artifact rule.
   - Mark roots with `data-root` only. Don't hand-chase `data-w` ids; the porter
     fills them.
   - Keep glosses short. Longer material goes in footnotes with a bold lead.
   - Any wording or data call Lane needs to make goes in `questions[]`, not
     asked in chat.

   Lane's Claude Code session handles transliteration, validation, colours,
   word ids and porting.

## Seven standing moves during pass 3

Each one turns an observation into an action:

- A tracked thread opens or pays off → name it and draft the one-line popover
  note now.
- A root recurs across units but isn't tracked → flag it as a candidate, with the
  lemma ids you saw.
- A single notable translation choice → flag it for a local `roots[]` entry.
- A word with an earlier-Scripture history, or a distinctive later reuse, that
  the notes missed → add it to the notes file with its verdict.
- A missed or wrong tag in an earlier unit → a `threads.retro` entry, not a
  prose aside.
- An earlier story or type-scene (commissioning, scouts, water crossing,
  census, …) → an `aside.story` box where the book enables it (it's harvested
  into the canon, type-scene included, so no meta entry); otherwise, and for a
  quotation or allusion, an `intertext[]` or `typescenes[]` entry in the meta
  block. Echo asides are harvested automatically too, so don't repeat them.
  Check `canon-decisions.md` before proposing a canon thread or type-scene that
  may already be settled.
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
