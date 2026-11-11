# Core workflow (every book)

Vendored from `bible-core/canon/workflow.md`; don't edit the book's copy. The
instruction field holds the lens, the language rules and this book's
differences. The style reference owns every fragment rule.

**Precedence:** Lane in chat > the instruction field > the style reference >
this file > the handoff > reference files. Flag a conflict to Lane; don't
resolve it silently.

## Three chats, four passes

Always three chats per unit, each fresh. What crosses is a file.

| Chat | Passes | Takes in | Hands on |
|---|---|---|---|
| Research | 1 briefing, 2 research | the unit pack | the notes file |
| Verse | 3 verse-by-verse, then the handoff | the notes file | `<book>_NN_handoff.md` |
| Build | 4 translation fragment | the pasted handoff | the fragment |

A pasted handoff means you are the build chat; an uploaded notes file, the
verse chat; otherwise the research chat. Pause after each pass for Lane's
go-ahead.

Passes 1 and 3 are spoken: Lane listens to them. Flowing prose with no headers,
bullets, bold, verse numbers, references or original script, and names said as
a person would ("the book of Genesis", not "Gen 40:20").

## Rules for every pass

- **Unit pack** (`unit-pack-NN.md`, generated and synced): the unit's map
  entry, rulings, tracked threads with first occurrences, lemma table, leads
  and source gaps, plus a mirror section where the book mirrors another. Copy
  ids and rulings from it; never recall them.
- **Sources:** read `resources.md` before pass 1 and search the web freely.
  Read a passage before attributing a view, and say where readings diverge.
  Name only sources `resources.md` lists or a search found, and only in chat
  and the handoff.
- **Quotes:** quotation marks mean a quote the notes file marks VERIFIED.
  Paraphrase everything else without them.
- **Large files:** grep a synced file over ~20 KB for the unit's lemma ids and
  verses instead of reading it whole. `synced-index.md` gives sizes.
- **Script and names:** no native script in chat or fragments. Names follow
  the book's transliteration convention (Moshe, Aharon, Yahweh).
- **Rulings:** before raising a wording, check the pack's rulings, then
  `translation-choices.md` and the earlier units' meta. A ruled wording is
  used, not re-asked.
- **Asking Lane:** the research and verse chats ask only what blocks the work
  (unit scope, a missing or contradictory file). Judgment calls (type-scenes,
  tentative links, new threads) go on the box list, marked tentative; what
  Lane leaves open becomes "Calls for Lane" in the handoff. The build chat
  asks every open call by popup before drafting. Books should not override
  this.
- **Promotions:** Claude decides, biased book-wide. A close call goes to
  "Calls for Lane" with the retrofit cost in view.
- **Decisions:** a chat can't write to the repo. Wording and glossary calls go
  in the handoff's "Decisions"; Claude Code applies them afterwards.
- **Compaction:** afterwards, re-read the notes file and the pack before going
  on. Late in pass 2, stop and continue in a fresh research chat from the
  notes file.
- **Scope:** first state the unit and passage from the unit map, flag where it
  leaves the chapter grid, and raise scoping questions. Flag rabbit holes
  before going deeper. If a request conflicts with a shipped unit, ask rather
  than rebuild. Prefer surgical edits.

## Pass 1: briefing (research chat, spoken)

Start from the pack, `resources.md` and the style reference. Cover placement,
ANE background, genre, vocabulary to watch and tensions to hold. Name the
earlier stories the unit leans on, scene by scene, without telling them yet.
Orient, don't resolve.

## Pass 2: research (research chat, working, not presented)

Scene by scene:

- the people, places and objects, and where they appeared before;
- the story's shape (a feast, a crossing, a commissioning, …);
- the nearest earlier story with that shape, read in the target text;
- what's the same, what's different, and what it does here (irony, reversal,
  fulfilment, warning);
- later reuse.

Search the web for the central people, places and objects. Then work the
pack's word leads: a generated search, not a judgment. A lead inside a story
already found is evidence for it; judge the rest on their own (root `echo`,
`aside.echo`, footnote, or drop). Where the book has parallel accounts, check
each scene against them. For any thread you mean to propose, copy its ids and
reach from the pack's lemma table.

Lean open: a link that fits the text but has thin outside support is
"possible", not a drop. Drop only what the text itself doesn't bear out.

**The notes file** is an output file, not pasted into chat, in the shape
`canon-ledger-template.md` gives. Append each row the moment it is judged,
rejected rows included. It is the only thing that crosses to the verse chat.
For a story worth telling, add the story, same, different and what it does.
End with the source-status block and the row count. Hand it over as a
download and say one line in chat: research done, notes ready.

## Pass 3: verse-by-verse (verse chat, spoken)

Lane uploads the notes file. Fetch the pack and say the notes' unit and row
count back, so a wrong version is caught. Don't re-research: name a gap, don't
fill it from memory.

Depth over speed, built on the notes; split a unit when a crux deserves room.
Earlier-Scripture roots and canonical trajectories first, then wordplay,
structures only where real, ANE background and the commentary dialogue, with
tensions left open. When a verse reaches an earlier story, tell it there:
background, what matches, what differs, what this passage does with it. Speak
meaningful differences from a parallel account in place. Note devotional
weight lightly.

End with the **box list**, Lane's veto point: the story boxes, parallel-account
boxes and notable echoes that will go into the fragment, with the "possible"
links marked tentative and one line on why each is thin.

**After the yes, write the handoff.** Scan your verse-by-verse for
"provisional", "check" and "match": each hit is a numbered call or a ruling
citation. Fill `canon-handoff-template.md` into `<book>_NN_handoff.md` as a
download, then say one line: handoff ready, open a fresh chat in this project
and paste it. The handoff carries judgment only; lookup data stays in the
pack.

## Pass 4: translation fragment (build chat, working)

The output is the unit's HTML fragment, not an Artifact-tool page. Build from
the handoff, the style reference and the synced files, with rulings from the
pack. Don't redo the research. If the handoff is missing something or
contradicts itself or a synced file, ask Lane.

**Ask the open calls before drafting anything:**

- each item in the handoff's "Calls for Lane";
- every rendering marked provisional or "to flag";
- every place a synced file rules differently from the handoff (say which file
  and what it rules);
- every new rendering of a lexeme the pack's rulings don't cover.

Use AskUserQuestion popups, up to four questions per popup, recommended choice
first and marked "(Recommended)". Items that only follow an existing ruling
share one "keep these as ruled?" question. Wait for the answers, then draft. A
handoff with no calls still gets one line saying so. If an answer is itself a
question, answer it and confirm the choice before editing. Never settle a call
yourself or silently override a handoff rendering. Only what's still unresolved
goes in `questions[]`.

Carry the handoff's "Checks for code" into `checks[]` and its ready promotions
into `threads.promote[]` (id, ids, gloss, opener note). Its "Decisions" are for
Claude Code, which also handles validation, colours, word ids, porting and
`handoff-check`.

## Standing moves (passes 2-3)

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
  `typescenes[]` entry. Check `canon-decisions.md` first, and don't repeat in
  those lists what a box or echo aside already says.
- A claim about another passage's Greek or Hebrew → "Checks for code".
