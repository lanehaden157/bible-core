# {{BOOK}} Study — Style Reference

> **The artifact contract.** What a unit artifact must contain and must not.
> `CHAT_SIDE_INSTRUCTIONS.md` and `core-workflow.md` say how to work;
> `resources.md` says what's on hand; `CLAUDE.md` says how the repo behaves.
> Each rule lives in one of them. `synced-index.md` lists every synced file.

A guide, not a spec: where a rule gives a reason, the reason outranks the rule.
Rules marked **(learned)** cost something to find in an earlier book — read
the lesson before relaxing one. This file starts as the shared defaults from
`bible-core/ARCHITECTURE.md`; **sections marked ✎ are this book's to decide**,
and anything else can change too, with the reason written here.

---

## 1. Colour policy

One **lexical root** per `data-root` — the root and its same-root forms,
never a theme or a bundle of words. Split a paired opposition into two roots;
drop a one-passage wordplay. Fixed phrases the book repeats verbatim are the one
exception and live in `threads.json`.

Tag **every** occurrence with the one slug, **including where the English uses a
different word** — the tag follows the lexeme, not the gloss.

`translit` is one bare root form (Hebrew books), not a list of inflected forms;
`gloss` is plain English (§3). No stem/binyan labels. A stem split that matters
goes in a thread `note` or a verse `.gloss`, in plain language.

Every slug must resolve — in `threads-digest.md` or this artifact's `roots[]` —
or the build fails. **`roots[]` is local roots only**: don't re-declare a
tracked thread there; `data/threads.json` is its single source of truth.

**Tag notable words even when they aren't threads.** A single striking
translation choice in a single verse earns a `data-root` span and a full
`{root, translit, gloss}` entry. Read for these deliberately.

**`example`** — optional on any root: one short quoted clause from the unit's
own English, no citation.

**`echo`** — optional on any root: one line saying where the word has already
appeared, or where it reappears distinctively later, shown in the root's
popover with a "cf.". Lead with the reference, then what it adds. Echoes come
from the kept rows of the intertext pass's ledger, not from memory at
drafting time.

**Resist a richer taxonomy. (learned:** a root/motif two-tier model was built
and reverted the same day. Root vs. stem vs. semantic field gets the same
answer: one slug, one colour.**)**

---

## 2. Root identity — ids, not strings

**A root is a hand-curated set of lemma ids in `roots.json`; every tracked
thread occurrence carries its word id** (`data-w`, from `{{BOOK}}-words.tsv`).
No original-language string is ever compared to another. **(learned:**
consonant-substring matching measured 0–42% recall on Joshua's weak-root
verbs.**)**

One root often spans several Strong's numbers, and one number can bundle
senses worth splitting, so a root is a **decision**, recorded as an id set
with a note. A bare id (`2416`) claims every lexeme under the number; a
suffixed id (`2416e`) claims exactly one.

```html
<span class="r" data-root="devote" data-w="068w5">devoted</span>
```

Local roots don't need `data-w`. **You never hand-chase word ids**: the porter
fills them by per-verse alignment and reports the few it can't decide.

**Never hand-type Hebrew; pull by word id. (learned:** NFC normalisation alone
reorders marks in 47% of Joshua's words.**)**

---

## 3. The hard contract

The artifact is **one `<article class="unit" data-unit="N">` and nothing
else** — no doctype/html/head/body/style/link, no inline `style`, no `--c-*`
vars. It opens with `<script type="application/json" id="unit-meta">`.

**Unknown top-level keys are a hard error. (learned:** Matthew's `descriptor`
and `discourse` were authored for eleven units and silently discarded.**)**

### Top-level keys

| key | required | type | rule |
|---|---|---|---|
| `unit` | ✓ | int | an integer, not a string |
| `passage` | ✓ | str | `"{{BOOK}} 6:1–27"` |
| `title` | ✓ | str | |
| `roots` | ✓ | array | §1 |
| `threads` | ✓ | object | all four sub-keys, empty lists fine |
| `slug` | — | str | `"unit-06"`; derived from `unit` if omitted |
| ✎ grouping keys | — | int | one per grouping kind in `book.json` (e.g. `movement`); looked up from the unit map if omitted |
| `questions` | — | array | wording/data calls only Lane can make, §3a |
| `intertext` | — | array | cross-book links worth recording, below |
| `typescenes` | — | array | type-scene instances in this unit, below |

### `intertext[]` and `typescenes[]` — canon rows (optional)

The porter moves these into `data/canon.json` and the canon registries in
`bible-core/canon/`; they aren't re-emitted in the built meta block.

- `intertext[]` — `{ref, to, kind, note?}`: `ref` a bare `"C:V"` in this
  book, `to` a reference like `"Ps 67:1"`, `kind` one of `quotation`,
  `allusion`, `echo`, `type-scene`. An `aside.echo` or a root's `echo` is
  already harvested as an `echo` edge, so list here only what those don't
  say: a quotation, an allusion without an aside, a link worth keeping
  without cluttering the page.
- `typescenes[]` — `{id, ref, note?, label?}`: `id` from the type-scene
  index (`commissioning`, `scouts`, `water-crossing`, `census`,
  `mountain-theophany`, `annunciation`, ...). A new `id` is fine; give it a
  `label` and it's added to the index for Lane to place under an arc.

### `roots[]` — every entry `{root, translit, gloss, example?, echo?}`

`root` matches `[a-z0-9-]+`. **No** `color`/`colour`, **no** `kind`/`members`,
no other keys. `gloss` is a short general definition — no stem or
part-of-speech labels. Never seed a gloss from Strong's first definition
(misleading in 9 of 16 sampled Joshua words).

### `threads` — `{opens, payoffs, candidates, retro}`

All four present, each a list, empty allowed.

**`opens[]` / `payoffs[]`** — `{id, ref, note}`. `id` must exist in
`threads-digest.md` (propose new ones via `candidates`); `note` is the
one-line popover prose.

**`candidates[]`** — `{root, why, ids?, refs?}`. Proposals only; `ids` are the
lemma ids you saw (evidence), copied as the word table spells them (`"6485 a"`
is fine; the porter reads it as `6485a`), `refs` a few representative verses
as bare `C:V`. **Claude
decides whether a candidate is promoted, biased toward book-wide**, and asks
Lane only when genuinely unsure.

**`retro[]`** — `{unit, verse, text, root, why, nth?, op?, w?}`. Fixes for
**earlier** units (`unit` is a slug like `"unit-04"`). `why` required. `op` ∈
`add` (default), `retag`, `retag_word`, `untag_word`, `unwrap`, `strip_span`,
`text`. `w` is optional — the porter fills it.

---

## 3a. `questions[]` — asking Lane in Claude Code, not on the project side

**`questions[]`** — `{topic, note, options?}`. A wording or data call only Lane
can make goes here **instead of** being asked in chat. `topic` is a few words;
`note` is the question, answerable cold; `options` optional short answers.
Render your best provisional choice so the draft keeps moving, and flag it.
The porter prints every question at port time; the decision then goes in
`translation-choices.md` or the thread/root entry.

---

## 4. Components

Deliberately small. The base components below are in every book. **Optional
components** (echo, count table, poem, itinerary, text-form, …) come from
bible-core's component registry: `book.json` `"components"` enables them, any
unit may use any enabled one, and **`components-reference.md`** (synced,
generated by the build) holds the markup and rules for each one. A class
that's neither base nor an enabled component fails the build by name. **A new
class is a decision**, so it goes into the registry with its CSS, its check and
its snippet.

| component | shape | note |
|---|---|---|
| coloured word | `<span class="r" data-root="X" data-w="…">…</span>` | `class="rl"` only **outside** verse blocks |
| verse | `<p class="v"><span class="n">17</span> … text<sup class="en"><a href="#n1">1</a></sup></p>` | one per verse, in order. The endnote marker is the last thing in the verse `<p>`, **never** inside the `.gloss` |
| gloss | `<span class="gloss">…</span>` | **following sibling** of the verse, never nested, always closed. Short |
| pericope heading | `<h3 class="pericope">Title <span>· 6:1–7</span></h3>` | `· C:V` range required |
| legend | `<section class="block legend" aria-label="color key"><ul></ul></section>` | **required, even as an empty stub** |
| notes | `<div class="notes"><h2>Notes</h2><ol><li id="n3"><strong>hid him (v4).</strong> …</li></ol></div>` | every `href` resolves to an `id` in the fragment |

**`data-verses`** — any component that presents verses *in place of*
verse-by-verse text (a table that condenses a repeated formula, say) carries
`data-verses="C:V–V"` (or `C:V–C:V`) naming exactly the verses it replaces.
Tracked-thread occurrences in those verses are then reported as covered by
the component, not as untagged gaps. The build fails if a declared verse is
also written out as a `p.v`, or if the range reaches outside the unit's
passage, so the declaration can't quietly excuse text a reader actually sees.
Say in the pericope's gloss that the verses are condensed.

✎ **This book's optional components:** echo and list (see
`components-reference.md`). Enable more in `book.json` when a unit needs
them, and note here anything this book does differently with one.

**(learned:** endnote markers inside `.gloss` hid the footnote behind the
toggle; the legend was once "optional" and a unit shipped with no colour key;
asides spliced inside unclosed glosses silently collapsed.**)**

### Balance — what goes where

Strong suggestions:

- **Glosses stay short** — a phrase or one sentence, roughly 25 words or
  fewer. A grammar point, a textual variant, a debate between readings goes
  in a **footnote**.
- **Grammar and medieval commentary are seasoning, not the meal.** Include a
  grammar point when it changes how the verse reads.
- **Intertextuality is the main course.** Say where earlier Scripture stands
  behind a line and where a line reappears later, including in the New
  Testament. `aside.echo` for a verse-level link, a root `echo` for a word.

**Voice: no named commentators or resources, and no project-internal
references, anywhere in fragment prose.** Where views differ, say so in
general terms and give the content of the disagreement. **(learned:** Joshua
unit 1's first draft named eight sources and two repo files.**)**

---

## 5. Hebrew in English ✎

**Transliteration** comes only from the core's Hebrew adapter
(`biblecore/lang/hebrew.py`; its test file is the authoritative definition).
Scheme: a diacritic only where the plain letter is already claimed (`ḥ ṭ ś`,
`ʾ`/`ʿ`); no vowel length; no spirantization; dagesh forte doubles; `יהוה` →
`YHWH`, rendered **Yahweh**.

**Translation philosophy.** A fresh, wooden-but-readable rendering from the
Hebrew, not a polish of an existing English version. Creative, intentional
glosses are encouraged.

**Wording.** Check `translation-choices.md` (which starts from
`canon-conventions.md`) before rendering a lexeme. A better
verse-specific rendering is fine — **flag the deviation**. Update the file in
the same turn as any wording decision. **(learned:** Matthew started its
glossary at unit 10 and paid with a retroactive audit.**)**

---

## 6. Judgment

**Be tough on structures.** Chiasms and rings only when textually verifiable.
Prefer the Masoretic paragraph breaks (`candidate-boundaries.md`) over
patterns you noticed. **(learned:** eight over-reaching chiasms were cut from
Matthew.**)**

**`threads.json` and `roots.json` are Lane's policy.** Nothing in the pipeline
writes either.

**Names are joined by hand.** Place-name wordplay is real but Strong's
etymology is unreliable. Add names to `roots.json` one at a time, with the
reason.

✎ **Genre cautions for this book** (lists, law, poetry, …): add them here as
units surface them.

---

## 7. Before saving — the checklist

1. One `<article>`, nothing above or below it.
2. Meta parses as JSON; required keys and all four `threads` sub-keys; no
   unknown top-level keys.
3. Every `roots[]` entry: `root` + bare `translit` + plain `gloss`, optional
   `example`/`echo`; nothing else.
4. Every notable translation choice has a local span and `roots[]` entry, and
   so does every word with a canon history, with an `echo`.
5. Every `opens`/`payoffs` `id` is in `threads-digest.md` and has a `note`.
6. Every `retro` targets an earlier unit, has a `why`, and resolves.
7. Every `data-root` is in `threads-digest.md` or `roots[]`.
8. Legend present, stub or filled.
9. Every pericope heading has its `· C:V` range.
10. `.gloss` and `aside.echo` blocks are closed following siblings, never
    nested; every `aside.echo` has a `data-anchor` matching its verse.
11. Every endnote `href` resolves to an `id` in the file.
12. **Zero native Hebrew or Greek anywhere — attribute values included.**
13. No inline `style`, no `--c-*` vars, no class the stylesheet doesn't know.
14. Wording matches `translation-choices.md`, or the deviation is flagged.
15. No named commentator or project-internal reference in prose.
16. Glosses are short, longer material is in footnotes, and the unit's
    intertextual links are surfaced.

Save as `{{SLUG}}_NN_translation.html`, zero-padded, and present the file.

---

## 8. Worked example ✎

Replace with a minimal, valid example from this book's own unit 1 once it
exists. Until then the shape is:

```html
<article class="unit" data-unit="1">
<script type="application/json" id="unit-meta">
{
  "unit": 1,
  "passage": "{{BOOK}} 1:1–10",
  "title": "Working Title",
  "roots": [
    { "root": "count", "translit": "paqad", "gloss": "count, muster, attend to",
      "echo": "Gen 50:24 — 'God will surely attend to you'" }
  ],
  "threads": { "opens": [], "payoffs": [], "candidates": [], "retro": [] }
}
</script>

<header class="mast">
  <div class="kicker">The Book of {{BOOK}} · Study Translation</div>
  <h1>Working Title</h1>
  <div class="unit">Unit 1 · {{BOOK}} 1:1–10</div>
</header>

<section class="block legend" aria-label="color key"><ul></ul></section>

<h3 class="pericope">Heading <span>· 1:1–3</span></h3>

<p class="v"><span class="n">1</span> Verse text with a
<span class="r" data-root="count">counted</span> word.<sup class="en"><a href="#n1">1</a></sup></p>
<span class="gloss"><em>counted</em> — a short note.</span>

<div class="notes">
  <h2>Notes</h2>
  <ol>
  <li id="n1"><strong>counted (v1).</strong> The longer discussion.</li>
  </ol>
</div>
</article>
```

---

## 9. The Literary Unit Map ✎

Comes from the project side once resources are compiled, as
`{{SLUG}}-literary-unit-map.md`. `python -m biblecore units-from-map` loads it
from its **Overview** table, so keep that table in this shape (Numbers' map is
the model):

    | # | Passage | Working title |
    |---|---|---|
    | | **PART ONE — Label (1:1–25:18)** | |
    | | *I. Label (1:1–10:10)* | |
    | 01 | 1:1–54 | Title |
    | 17 | 16:36–17:13 [Heb 17:1–28] | Title |

Bold rows open an outer grouping, italic rows an inner one; both are
optional. Passages are in English numbering, with any Hebrew difference in
`[Heb ...]`. Renumbering after units ship means editing
`threads.json` opens/payoffs, every `retro` entry, and every fragment's meta
block, so confirm it before unit 1.
