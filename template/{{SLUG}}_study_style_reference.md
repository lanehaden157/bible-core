# {{BOOK}} Study — Style Reference

The artifact contract: what a unit's fragment must and must not contain. How
to work is in `core-workflow.md`. Where a rule gives a reason, the reason
outranks the rule. Sections marked ✎ are this book's to decide.

## 1. Colour policy

- One **lexical root** per `data-root`: the root and its same-root forms,
  never a theme or a bundle of words. No richer taxonomy (root vs. stem vs.
  semantic field all get one slug, one colour). Split a paired opposition into
  two roots; drop a one-passage wordplay. A fixed phrase the book repeats
  verbatim may be a thread in `threads.json`.
- Tag **every** occurrence with the one slug, including where the English uses
  a different word. The tag follows the lexeme, not the gloss.
- Every slug resolves in `threads-digest.md` or this fragment's `roots[]`, or
  the build fails. `roots[]` holds local roots only; never re-declare a
  tracked thread there.
- **Tag notable words that aren't threads.** A single striking translation
  choice earns a `data-root` span and a `roots[]` entry. Read for these
  deliberately.
<!-- lang: hebrew -->
- `translit` is one bare root form, not a list of inflected forms. `gloss` is
  plain English with no stem or binyan labels. A stem split that matters goes
  in a thread `note` or a verse `.gloss`, in plain language.
<!-- /lang -->
<!-- lang: greek -->
- `translit` is the lexical form (`klēronomeō`), not a list of inflected
  forms. `gloss` is plain English with no tense or voice labels. A grammatical
  point that matters goes in a thread `note` or a verse `.gloss`, in plain
  language.
<!-- /lang -->
- `example` (optional): one short quoted clause from the unit's own English,
  no citation.
- `echo` (optional): one line on where the word already appeared or
  distinctively returns, reference first, then what it adds. Take echoes from
  the kept rows of the notes file, not from memory.

## 2. Root identity: ids, not strings

A root is a hand-curated set of lemma ids in `roots.json`, and every tracked
occurrence carries its word id (`data-w`, from `{{BOOK}}-words.tsv`).
Original-language strings are never compared or hand-typed.

<!-- lang: hebrew -->
One root often spans several Strong's numbers, and one number can bundle
senses worth splitting, so a root is a decision recorded as an id set with a
note. A bare id (`2416`) claims every lexeme under the number; a suffixed id
(`2416e`) claims exactly one.

```html
<span class="r" data-root="devote" data-w="068w5">devoted</span>
```
<!-- /lang -->
<!-- lang: greek -->
Lemma ids are transliterated lemmas (`klēronomeō`), with a digit only where
two lemmas share a spelling (`tis`, `tis2`). One root often spans several
lemmas (`klēronomeō`, `klēronomia`, `klēronomos`), so a root is a decision
recorded as an id set with a note.

```html
<span class="r" data-root="inherit" data-w="01050506">will inherit</span>
```
<!-- /lang -->

Don't hand-chase word ids: the porter fills `data-w` and reports what it can't
decide. Local roots don't need `data-w`, and neither do tracked spans inside a
`data-verses` component.

## 3. The hard contract

The fragment is one `<article class="unit" data-unit="N">` and nothing else:
no doctype, html, head, body, style or link, no inline `style`, no `--c-*`
vars. It opens with `<script type="application/json" id="unit-meta">`.

Unknown top-level keys are a hard error.

| key | required | type | rule |
|---|---|---|---|
| `unit` | ✓ | int | an integer, not a string |
| `passage` | ✓ | str | `"{{BOOK}} 6:1–27"` |
| `title` | ✓ | str | |
| `roots` | ✓ | array | §1 |
| `threads` | ✓ | object | all four sub-keys, empty lists fine |
| `slug` | — | str | `"unit-06"`; derived from `unit` if omitted |
| ✎ grouping keys | — | int | one per grouping kind in `book.json` (e.g. `movement`); looked up from the unit map if omitted |
| `questions` | — | array | §3a |
| `checks` | — | array | §3a |
| `intertext` | — | array | below |
| `typescenes` | — | array | below |

**`roots[]`**: `{root, translit, gloss, example?, echo?}` and no other keys
(no `color`, `kind`, `members`). `root` matches `[a-z0-9-]+`. `gloss` is a
short general definition with no grammatical labels.
<!-- lang: hebrew -->
Never seed a gloss from Strong's first definition.
<!-- /lang -->

**`threads`**: `{opens, payoffs, candidates, retro, promote?}`. The first four
are always present, each a list.

- `opens[]` / `payoffs[]`: `{id, ref, note}`. `id` must exist in
  `threads-digest.md`; `note` is the one-line popover prose.
<!-- lang: hebrew -->
- `candidates[]`: `{root, why, ids?, refs?}`. Proposals only. `ids` are the
  lemma ids you saw, copied as the word table spells them (`"6485 a"` is
  fine); `refs` a few representative verses as bare `C:V`.
<!-- /lang -->
<!-- lang: greek -->
- `candidates[]`: `{root, why, ids?, refs?}`. Proposals only. `ids` are the
  lemma ids you saw, copied as the word table spells them (`klēronomeō`);
  `refs` a few representative verses as bare `C:V`.
<!-- /lang -->
  Claude decides whether a candidate is promoted, biased toward book-wide, and
  asks Lane only when unsure.
- `retro[]`: `{unit, verse, text, root, why, nth?, op?, w?}`. Fixes for
  earlier units (`unit` is a slug like `"unit-04"`). `why` is required. `op` is
  one of `add` (default), `retag`, `retag_word`, `untag_word`, `unwrap`,
  `strip_span`, `text`. The porter fills `w`.
- `promote[]`: `{entry, reach?, retrofit?}`, a thread Claude has decided to
  promote, taken from the handoff. `entry` is `{id, root?, ids, gloss, opens:
  {unit, note?}, payoffs?: [{unit, note?}], translit?, note?}`: `ids` from the
  pack's lemma table, no colour, and `root` defaults to `id` (ASCII
  `[a-z0-9-]`, `kerdaino` not `kerdainō`). Code computes the refs, `reach` and
  `retrofit` at port. A `retro[]` in the same unit may tag the new id. A
  proposal that still needs an id set stays in `candidates[]`.

**`intertext[]`**: `{ref, to, kind, note?}`. `ref` is a bare `"C:V"` in this
book, `to` a reference like `"Ps 67:1"`, `kind` one of `quotation`,
`allusion`, `echo`, `type-scene`, `story`, `character`, `reuse`. An
`aside.echo`, a root's `echo` and an `aside.story` box are already harvested
into the canon, so list only what those don't say.

**`typescenes[]`**: `{id, ref, note?, label?}`. `id` comes from the type-scene
index (`commissioning`, `scouts`, `water-crossing`, `census`,
`mountain-theophany`, `annunciation`, ...). A new `id` needs a `label`.

## 3a. `questions[]` and `checks[]`

**`questions[]`**: `{topic, note, options?}`. Only a call Lane must make, with
a real open alternative, that the build chat's popups left unresolved. Never a
wording `translation-choices.md` or an earlier unit already rules. `topic` is
a few words, `note` the question answerable cold, `options` short answers.
Render your best provisional choice and flag it.

**`checks[]`**: `{ref, claim, expect}`. A claim about another passage's text
for the code side to verify: `ref` like `"Isa 22:22"`, `claim` what the
fragment says, `expect` the lemma or lemmas it should find (`"!lemma"` for a
word that should be absent). These never go in `questions[]`.

## 4. Components

The base components are in every book. Optional ones (echo, list, poem,
itinerary, text-form, …) are enabled in `book.json` `"components"`, and
`components-reference.md` holds their markup and rules. A class that is
neither base nor enabled fails the build.

| component | shape | note |
|---|---|---|
| coloured word | `<span class="r" data-root="X" data-w="…">…</span>` | `class="rl"` only **outside** verse blocks |
| verse | `<p class="v"><span class="n">17</span> … text<sup class="en"><a href="#n1">1</a></sup></p>` | one per verse, in order. The endnote marker is the last thing in the verse `<p>`, **never** inside the `.gloss` |
| gloss | `<span class="gloss">…</span>` | **following sibling** of the verse, never nested, always closed. Short |
| pericope heading | `<h3 class="pericope">Title <span>· 6:1–7</span></h3>` | `· C:V` range required |
| legend | `<section class="block legend" aria-label="color key"><ul></ul></section>` | **required, even as an empty stub** |
| notes | `<div class="notes"><h2>Notes</h2><ol><li id="n3"><strong>hid him (v4).</strong> …</li></ol></div>` | every `href` resolves to an `id` in the fragment |

**`data-verses`**: a component that presents verses in place of
verse-by-verse text (a table condensing a repeated formula) carries
`data-verses="C:V–V"` naming exactly the verses it replaces. Don't also write
those verses as `p.v`, keep the range inside the unit's passage, and say in
the pericope's gloss that the verses are condensed.

✎ **This book's optional components:** echo and list. Enable more in
`book.json` when a unit needs them, and note here anything this book does
differently with one.

### Balance

- **Glosses stay short:** a phrase or one sentence, about 25 words at most. A
  grammar point, a textual variant or a debate between readings goes in a
  footnote.
- **Grammar and commentary are seasoning.** Include a grammar point when it
  changes how the verse reads.
- **Intertextuality is the main course.** Say where earlier Scripture stands
  behind a line and where it reappears later. `aside.echo` for a verse-level
  link, a root `echo` for a word.
- **Voice:** no named commentators or resources and no project-internal
  references anywhere in fragment prose. Where views differ, say so in general
  terms and give the content of the disagreement.

<!-- lang: hebrew -->
## 5. Hebrew in English ✎

**Transliteration** follows the core's Hebrew adapter
(`biblecore/lang/hebrew.py`): a diacritic only where the plain letter is
already claimed (`ḥ ṭ ś`, `ʾ`/`ʿ`); no vowel length; no spirantization; dagesh
forte doubles; the divine name is `YHWH`, rendered **Yahweh**.

**Translation.** A fresh, wooden-but-readable rendering from the Hebrew, not a
polish of an existing English version. Creative, intentional glosses are
encouraged.
<!-- /lang -->
<!-- lang: greek -->
## 5. Greek in English ✎

**Transliteration** follows the core's Greek adapter
(`biblecore/lang/greek.py`): η → `ē` and ω → `ō`; `th ph ch ps` for θ φ χ ψ;
`y` for υ except in `ou au eu`; γγ/γκ → `ng`/`nk`; rough breathing → initial
`h`, initial ρ → `rh`; accents, smooth breathing and iota subscript dropped.
*kyrios* standing for the divine name is rendered **Yahweh**. A Hebrew word
uses the Hebrew scheme (`ḥ ṭ ś`, `ʾ`/`ʿ`, no vowel length).

**Translation.** A fresh, wooden-but-readable rendering from the Greek
(SBLGNT), not a polish of an existing English version. Creative, intentional
glosses are encouraged.
<!-- /lang -->

**Wording.** Check `translation-choices.md` (which starts from
`canon-conventions.md`) before rendering a lexeme. A better verse-specific
rendering is fine if you flag the deviation.

## 6. Judgment

<!-- lang: hebrew -->
- **Be tough on structures.** Chiasms and rings only when textually
  verifiable. Weigh the Masoretic paragraph breaks
  (`candidate-boundaries.md`) together with the patterns you notice; where
  they disagree, say so and argue for the boundary you choose.
- **Names are joined by hand.** Place-name wordplay is real, but Strong's
  etymology is unreliable.

✎ **Genre cautions for this book** (lists, law, poetry, …): add them here as
units surface them.
<!-- /lang -->
<!-- lang: greek -->
- **Be tough on structures.** Chiasms and rings only when textually
  verifiable. Weigh the book's own markers (formulae, transitions, a change of
  scene or speaker) together with the patterns you notice; where they
  disagree, say so and argue for the boundary you choose.
- **Names are joined by hand.** A Greek name often carries a Hebrew one
  (*Iēsous* is *Yehoshua*); say so where it matters.

✎ **Genre cautions for this book.** Keep the ones that fit and add more as
units surface them.

- **Gospels:** a difference from a parallel is evidence about this book's
  emphasis, not the whole reading. Compare where it illuminates, not verse by
  verse.
- **Old Testament quotations** often follow the Septuagint; say which the
  wording follows when it matters.
- **Letters:** follow the argument. The connecting words carry the structure,
  and a unit should end where a step of the argument does.
- **Apocalyptic:** trace the images in the Prophets before reading them as a
  code for later events.
<!-- /lang -->

## 7. Before saving

1. One `<article>`, nothing above or below it.
2. Meta parses as JSON: required keys, the four `threads` sub-keys, no unknown
   top-level keys.
3. Every `roots[]` entry has `root`, bare `translit`, plain `gloss`, and
   nothing beyond `example` and `echo`.
4. Every notable translation choice and every word with a canon history has a
   local span and a `roots[]` entry (the latter with an `echo`).
5. Every `opens`/`payoffs` `id` is in `threads-digest.md` and has a `note`.
6. Every `retro` targets an earlier unit and has a `why`.
7. Every `data-root` is in `threads-digest.md` or `roots[]`.
8. Legend present, stub or filled.
9. Every pericope heading has its `· C:V` range.
10. `.gloss` and `aside.echo` blocks are closed following siblings, never
    nested; every `aside.echo` has a `data-anchor` matching its verse.
11. Every endnote `href` resolves to an `id` in the file.
12. **Zero native Hebrew or Greek anywhere, attribute values included.**
13. No inline `style`, no `--c-*` vars, no unknown class.
14. Wording matches `translation-choices.md`, or the deviation is flagged.
15. No named commentator or project-internal reference in prose.
16. Glosses are short, and the unit's intertextual links are surfaced.
17. `questions[]` holds only open calls for Lane; claims about other
    passages' text are in `checks[]`.
18. Every `threads.promote[]` entry has an `entry` with `id` and `ids`.

Save as `{{SLUG}}_NN_translation.html`, zero-padded, and hand it over as a
download.

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
<!-- lang: hebrew -->
    { "root": "count", "translit": "paqad", "gloss": "count, muster, attend to",
      "echo": "Gen 50:24 — 'God will surely attend to you'" }
<!-- /lang -->
<!-- lang: greek -->
    { "root": "count", "translit": "logizomai", "gloss": "count, reckon, credit to",
      "echo": "Gen 15:6 — 'it was counted to him as righteousness'" }
<!-- /lang -->
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

## 9. The Literary Unit Map ✎

Comes from the project side as `{{SLUG}}-literary-unit-map.md`.
`python -m biblecore units-from-map` loads its **Overview** table, so keep the
table in this shape:

    | # | Passage | Working title |
    |---|---|---|
    | | **PART ONE — Label (1:1–25:18)** | |
    | | *I. Label (1:1–10:10)* | |
    | 01 | 1:1–54 | Title |
<!-- lang: hebrew -->
    | 17 | 16:36–17:13 [Heb 17:1–28] | Title |

Bold rows open an outer grouping, italic rows an inner one; both are
optional. Passages are in English numbering, with any Hebrew difference in
`[Heb ...]`. Renumbering after units ship means editing
<!-- /lang -->
<!-- lang: greek -->
    | 02 | 1:18–2:23 | Title |

Bold rows open an outer grouping, italic rows an inner one; both are
optional. Passages are in English numbering, which the SBLGNT shares.
Renumbering after units ship means editing
<!-- /lang -->
`threads.json` opens/payoffs, every `retro` entry and every fragment's meta
block, so confirm it before unit 1.
