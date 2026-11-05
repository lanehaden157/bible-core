# Core workflow (every book)

Vendored from `bible-core/canon/workflow.md`; don't edit the book's copy. The
project's instruction field holds the lens, the language rules and this book's
differences. The style reference owns every fragment ("artifact") rule.

## Precedence

Lane in chat > the book's project field > the book's style reference > this
file > the handoff > reference files (translation-choices, unit map, resources,
canon files). A conflict between two rungs is flagged to Lane, not resolved
silently.

## Terms and rules

- **Passes:** 1 briefing, 2 research (the intertext pass), 3 verse-by-verse,
  4 translation fragment. Passes 1-2 run in the research chat, pass 3 and the
  handoff in the verse chat, pass 4 in the build chat.
- **Unit pack:** `unit-pack-NN.md`, generated per unit and synced: the unit's
  map entry, the rulings its words trigger, its tracked threads with computed
  first occurrences, a lemma table (ids, transliteration, gloss, reach), the
  leads and the known source gaps. Chats copy ids and rulings from it; they
  don't recall them.
- **Notes file:** pass 2's output, appended row by row as each is judged. It is
  the state that survives a compaction, and the only thing that crosses from the
  research chat to the verse chat.
- **Box list:** pass 3's closing spoken list: Lane's veto point, before the
  handoff is written.
- **Translation fragment:** pass 4's output, the unit's HTML fragment, not a
  claude.ai Artifact-tool page.
- **Names:** the book's transliteration convention (Moshe, Aharon, Yahweh)
  covers spoken passes, fragments and handoffs; the book says whether its unit
  map is exempt.
- **Native script:** chat output and fragments carry none (the validator rejects
  it in a fragment); reference, corpus and source files may, with a "do not
  copy" warning.
- **Citing:** name only sources `resources.md` lists or you found by search, in
  chat and the handoff; fragment prose names none unless the style reference
  allows it.
- **Asking Lane:** the research and verse chats don't stop to ask judgment
  calls (type-scenes, tentative links, new threads); they go on the box list,
  marked tentative, where Lane approves or vetoes them with the verse-by-verse
  in front of them. Whatever stays open becomes "Calls for Lane" in the
  handoff. Those chats ask in chat only what blocks the work: unit scope, a
  missing or contradictory file. The build chat asks every open call by
  AskUserQuestion popup before drafting; a handoff listing none gets one line
  saying so. Books should not override this.
- **Promotions:** Claude decides, biased book-wide. A close call goes to Lane
  through the handoff's "Calls for Lane", with the retrofit cost in view.
- **Decisions made in chat:** a chat can't write to the repo. Wording and
  glossary calls go in the handoff's "Decisions" section (the build chat repeats
  them at its close); Claude Code applies them to the repo after the session.

## What's on hand

Read `resources.md` before pass 1. It's a start, not a limit: search
the web freely in every pass, and say which source you leaned on. Read a passage
before attributing a view, mark anything not read this chat RECALLED, and say
where readings diverge and why.

**Grep before read.** For a synced file over ~20 KB (the word table above all),
search it for the unit's lemma ids and verse range instead of reading it whole.
`synced-index.md` gives each file's size.

**Quotes.** Text in quotation marks, in a box or a handoff, is a VERIFIED quote
from the notes file (read this chat). Anything else is paraphrased, without
quotation marks.

`synced-index.md` lists every synced file and what it's for; the instruction
field's "Where things are" says how to get them.

## Per unit: four passes, three chats

Always three chats per unit, never two. Each starts fresh; what crosses is a file.

| Chat | Passes | Takes in | Hands on |
|---|---|---|---|
| Research | 1 briefing, 2 research | the pack | the notes file |
| Verse | 3 verse-by-verse, then the handoff | the notes file | `<book>_NN_handoff.md` |
| Build | 4 translation fragment | the pasted handoff | the fragment |

**Which chat am I in?** A pasted handoff means the build chat; an uploaded notes
file means the verse chat; otherwise the research chat. If a book's instruction
field says otherwise, flag it to Lane.

Before research, `python -m biblecore unit-pack NN` and `sync` give every chat the
same generated data. Passes 1 and 3 are spoken prose, since Lane listens to them; 2
and 4 are working passes. Pause after each pass for Lane's go-ahead.

1. **Briefing (research chat, for listening).** Start from the unit pack,
   `resources.md` and the style reference. Flowing prose, with no headers,
   bullets or bold. Cover placement, ANE background, genre, intertextual setup,
   vocabulary to watch, tensions to hold. The intertextual setup names the
   earlier stories the unit leans on, scene by scene, without telling them yet.
   Orient, don't resolve.

2. **Research (research chat; a working pass, not presented).** Scene by scene:
   - the people, places and objects, and where they appeared before;
   - the story's shape (a feast, a crossing, a commissioning, a prophet rejected
     at home, …);
   - the nearest earlier story with that shape, read in the target text;
   - what's the same and what's different;
   - what it does here (irony, reversal, fulfilment, warning);
   - later reuse.

   Search the web for the central people, places, objects. Then the word
   leads (in the pack), a generated word search, not a judgment. A lead inside a
   story already found is evidence for it; judge the rest on their own (root
   `echo`, `aside.echo`, footnote, or drop). Where the book has parallel
   accounts (the other gospels, Chronicles beside Kings), check each scene
   against them. Ask of every tracked thread and notable word where it first
   appears and returns: the pack computes that for the tracked ones. Prune as you
   go, but lean open: a link that fits the text and has thin outside support is
   "possible", not a drop. Thin sources or a skeptical literature are not a
   verdict; drop only what the text itself doesn't bear out.

   **Write the notes file as you go.** An output file, not pasted into chat.
   Append each row the moment it is judged; don't hold rows for a tidy-up at the
   end. A row: verse, target text, kind, evidence (shared words in
   transliteration, with lemma ids from the pack), the wording actually read or
   "not read", **status**, strength (strong, possible, weak) and verdict,
   rejected rows included. Status is one of:
   - VERIFIED: the wording was read this chat;
   - SHEET: taken from the pack or leads only;
   - SECONDHAND: a summary of a source, not the source;
   - RECALLED: from memory.

   For a story worth telling, add the story, same, different, what it does. The
   file ends with a **source-status block** (what was read, what is secondhand,
   what was unavailable by verse, where the paragraph markers came from) and a
   **row count** with the unit number. Hand it to Lane as a download. In chat,
   say one line: research done, notes ready.

   **After any compaction, re-read the notes file and the pack before going
   on.** If it happens late in pass 2, stop and continue in a fresh research chat
   from the notes file: the notes hold every judged row, a summary does not.

   Two checks keep later work cheap:
   - Before raising anything for Lane, read the pack's rulings (and
     `translation-choices.md` for anything the pack doesn't cover) and the
     earlier units' meta; a ruled wording is used, not re-asked.
   - For any thread you mean to propose, the pack's lemma table gives its
     occurrences and reach; copy the ids, don't recall them. Promotion needs a
     retrofit in each earlier unit, so a close call goes to Lane (see
     Promotions).

3. **Verse-by-verse (verse chat, for listening).** Lane uploads the notes file.
   The chat fetches the pack and says the notes' unit and row count back, so a
   wrong version is caught. It does not re-research: a gap is named, not filled
   from memory. Flowing prose, depth over speed, built on the notes; split a
   unit when a crux deserves room. Earlier-Scripture roots and canonical
   trajectories come first, then wordplay, structures only where real, ANE
   background, and the commentary dialogue, tensions left open. When a verse
   reaches an earlier story, tell it there: its background, what matches, what's
   different, and what this passage does with it. Speak meaningful differences
   from a parallel account in place too. Spoken style throughout: no verse
   numbers, references or original script, and names said as a person would
   ("the book of Genesis", not "Gen 40:20"). Note devotional weight lightly.

   End with the box list: the story boxes, the parallel-account boxes and the
   notable echoes that will go into the fragment. Include the "possible" links
   too, marked tentative with one line on why they're thin, so Lane decides.

   **After the yes, write the handoff.** Fill `canon-handoff-template.md` into
   `<book>_NN_handoff.md` as an output file for download, then say one line:
   handoff ready, open a fresh chat in this project and paste it. The handoff
   carries judgment only (verses, boxes, decisions, thread notes, promotion
   proposals, calls, checks, source status); lookup data stays in the pack.

4. **Translation fragment (build chat; a working pass).** Build from the
   handoff, the style reference and the synced files; rulings come from the unit
   pack, not the handoff. Don't redo the research. If the handoff is missing
   something or contradicts itself or a synced file, ask Lane; don't re-research
   to fill the gap.

   **Ask the open calls before drafting anything.** List every call that is
   Lane's: each item in the handoff's "Calls for Lane"; every rendering marked
   provisional or "to flag"; every place a synced file rules differently from
   the handoff (say which file and what it rules); and every new rendering of a
   lexeme the pack's rulings don't cover. Ask them by AskUserQuestion
   popup (see Asking Lane), up to 4 per call, batched across calls, best
   provisional choice first and marked "(Recommended)". Items that only follow an
   existing ruling share one "keep these as ruled?" question. Wait for the
   answers, then draft. A handoff saying "none" doesn't skip this: say so in one
   line. If an answer is itself a question, answer it and confirm the choice
   before editing. Never settle a call yourself or override a handoff rendering
   silently. Only what's still unresolved goes in `questions[]`.

   Carry the handoff's "Checks for code" into `checks[]` and its ready thread
   promotions into `threads.promote[]` (id, ids, gloss, opener note; code
   computes `opens`/`payoffs` refs, reach and retrofit when the unit is ported);
   its "Decisions" are for Claude Code to apply, not yours. Lane's Claude Code
   session handles validation, colours, word ids and porting. After the build,
   code runs `handoff-check` (with the notes file), the port, and `checks`
   (transliteration resolved to lemma ids; any that don't resolve come back to
   Lane as a list).

## Seven standing moves (passes 2-3)

- A tracked thread opens or pays off → name it and draft the popover note now.
- A root recurs across units but isn't tracked → flag it as a candidate, with
  lemma ids.
- A single notable translation choice → flag it for a local `roots[]` entry.
- A word with an earlier-Scripture history or a distinctive later reuse that
  the notes missed → add it to the notes file with its verdict.
- A missed or wrong tag in an earlier unit → a `threads.retro` entry, not a
  prose aside.
- An earlier story or type-scene → an `aside.story` box where the book enables
  it, otherwise (and for a quotation or allusion) an `intertext[]` or
  `typescenes[]` entry. Boxes and echo asides are harvested into the canon, so
  don't repeat them; check `canon-decisions.md` first.
- Something for another reader of the handoff → a call only Lane can make goes
  in "Calls for Lane" with your provisional choice; a claim about another
  passage's Greek or Hebrew, in "Checks for code".

Before writing the handoff, scan "Verse by verse" for "provisional", "check"
and "match": each hit is a numbered call or a ruling citation.

## Scope

Before each walkthrough, state the unit and passage from the unit map, flag
where it diverges from the chapter grid, and raise scoping questions. Flag
rabbit holes before going deeper. If a request conflicts with a shipped
unit, ask rather than rebuild.

## Working style

Prefer surgical edits. When scope is unclear, ask Lane.
