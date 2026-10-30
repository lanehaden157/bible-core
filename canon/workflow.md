# Core workflow (every book)

Vendored from `bible-core/canon/workflow.md`; don't edit the book's copy. The
project's instruction field holds the lens, the language rules and this book's
differences, and **wins over this file where the two disagree.** The style
reference owns every artifact rule.

## What's on hand

Read `resources.md` before pass 1. It's a starting point, not a limit: search
the web freely in every pass and cite any commentator or source by name, saying
which you leaned on. Read a passage before attributing a view, mark anything you
haven't read this chat as "recalled, unverified", and say where readings diverge
and why.

`synced-index.md` lists every synced file and what it's for. That folder
round-trips from the repo; nothing there is uploaded by hand.

## Per unit: four passes, two chats

Passes 1-3 run in a **research chat**; pass 4 runs in a fresh **build chat**
opened with the pasted handoff, the only thing that crosses between them.
Passes 1 and 3 are spoken prose, because Lane listens to them read aloud;
passes 2 and 4 are working passes. Pause after each pass for Lane's go-ahead.

1. **Briefing (for listening).** Flowing prose, with no headers, bullets or
   bold. Cover placement, ANE background, genre, intertextual setup, vocabulary
   to watch, and tensions to hold. The intertextual setup names the earlier
   stories the unit seems to lean on, scene by scene, without telling them yet.
   Orient; don't resolve.

2. **Research (a working pass, not presented).** Scene by scene, in writing:
   - the people, places and objects, and where they appeared before;
   - the story's shape (a feast, a feeding in want, a crossing, a commissioning,
     a prophet rejected at home, …);
   - the nearest earlier story with that shape, read in the target text;
   - what's the same and what's different;
   - what it does here (irony, reversal, identification, fulfilment, warning);
   - later reuse.

   Search the web for the central people, places and objects. Then the word
   leads, `canon-leads-unit-NN.md`: a generated word search, not a judgment. A
   lead inside a story already found is evidence for it; judge the rest on
   their own (root `echo`, `aside.echo`, footnote, or drop). Where the book has
   parallel accounts (the other gospels, Chronicles beside Kings), check each
   scene against them. Ask of every tracked thread and notable word where it
   first appears and where it comes back. Prune as you go.

   The output is a **notes file** (a chat-side output file, not pasted into
   chat): the full ledger of every link considered, with verse, target text,
   kind, evidence, strength (strong, possible, weak) and verdict, rejected rows
   included; and for a story worth telling, the story, same, different and what
   it does. It stays in the research chat. In chat, say one line: research
   done, ready for the verse-by-verse.

   Two checks here keep later work cheap:
   - Before raising anything for Lane, read `translation-choices.md` and the
     earlier units' meta. A wording that's already ruled is used, not re-asked.
   - For any thread you mean to propose, count its occurrences in the word
     table and name the earlier units it reaches. Promotion needs a retrofit
     in each, so a close call goes to Lane with that cost in view.

3. **Verse-by-verse (for listening).** Flowing prose, depth over speed, built
   on the notes; split a unit when a crux deserves room. Earlier-Scripture
   roots and canonical trajectories come first, then wordplay, structures only
   where real, ANE background, and the commentary dialogue with tensions left
   open. When a verse reaches an earlier story, tell it there: its background,
   what matches, what's different, and what this passage does with it. Speak
   meaningful differences from a parallel account in place too. Spoken style
   throughout: no verse numbers, references or original script, and names said
   the way a person would say them ("the book of Genesis", not "Gen 40:20").
   Note devotional weight lightly.

   End with a short spoken list of what will go into the artifact: the story
   boxes, the parallel-account boxes, the notable echoes. That list is Lane's
   veto point.

   **After the yes, write the handoff.** Fill `canon-handoff-template.md` into
   `<book>_NN_handoff.md` as a chat-side output file and present it, then say
   one line: handoff ready, open a fresh chat in this project and paste it.

4. **Artifact (a working pass, in the build chat).** Build from the handoff,
   the style reference and the synced files. Don't redo the research. If the
   handoff is missing something or contradicts itself or a synced file, ask
   Lane; don't re-research to fill the gap.

   **Ask the open calls before drafting anything.** List every call that is
   Lane's: each item in the handoff's "Calls for Lane"; every rendering marked
   provisional or "to flag"; every place a synced file rules differently from
   the handoff (say which file and what it rules); and every new rendering of a
   lexeme `translation-choices.md` doesn't cover. Ask them by AskUserQuestion
   popup, up to 4 per call, batched across calls, best provisional choice first
   and marked "(Recommended)". Items that only follow an existing ruling can
   share one "keep these as ruled?" question. Wait for the answers, then draft.
   A handoff saying "none" doesn't skip this; if there is truly nothing to ask,
   say so in one line. If an answer is itself a question, answer it and confirm
   the choice before editing. Never settle a call yourself or override a
   handoff rendering silently. Only what's still unresolved goes in
   `questions[]`.

   Carry the handoff's "Checks for code" into `checks[]` and its ready thread
   promotions into `threads.promote[]`. Lane's Claude Code session handles
   validation, colours, word ids and porting.

## Seven standing moves during pass 3

- A tracked thread opens or pays off → name it and draft the one-line popover
  note now.
- A root recurs across units but isn't tracked → flag it as a candidate, with
  the lemma ids you saw.
- A single notable translation choice → flag it for a local `roots[]` entry.
- A word with an earlier-Scripture history or a distinctive later reuse that
  the notes missed → add it to the notes file with its verdict.
- A missed or wrong tag in an earlier unit → a `threads.retro` entry, not a
  prose aside.
- An earlier story or type-scene → an `aside.story` box where the book enables
  it, otherwise (and for a quotation or allusion) an `intertext[]` or
  `typescenes[]` entry. Boxes and echo asides are harvested into the canon, so
  don't repeat them. Check `canon-decisions.md` first.
- Something for another reader of the handoff → a call only Lane can make goes
  in "Calls for Lane" with your provisional choice; a claim about another
  passage's Greek or Hebrew goes in "Checks for code"; a thread row citing this
  unit's verses gets listed for the code side, which alone can see it.

Before writing the handoff, scan "Verse by verse" for "provisional", "check"
and "match": each hit is a numbered call or a ruling citation.

## Scope

Before each walkthrough, state the unit and passage from the unit map, flag
where it diverges from the chapter grid, and raise any scoping questions. Flag
rabbit holes and ask before going deeper. If a request conflicts with a shipped
unit, ask rather than silently rebuild.

## Working style

Prefer surgical edits to rewrites. When design or scope is unclear, ask Lane
rather than guess.
