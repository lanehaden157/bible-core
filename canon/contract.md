# Fragment contract (shared)

Vendored from bible-core as `fragment-contract.md`; don't edit book's copy.
What a unit's fragment must and must not contain. Starting point, not gospel:
the book's style reference holds its differences and wins. Reason outranks
rule. Terse on purpose. Build checks most of the structure at port; this file
is so the first draft passes.

## Colour

- One **lexical root** per `data-root`: root + same-root forms. Never a theme
  or bundle of words. No taxonomy: root, stem, semantic field all get one
  slug, one colour. Paired opposition → two roots. One-passage wordplay →
  drop. Fixed phrase the book repeats verbatim may be a thread.
- Tag **every** occurrence with the one slug, also where the English differs.
  Tag follows the lexeme, not the gloss.
- Every slug resolves in `threads-digest.md` or this fragment's `roots[]`.
  `roots[]` = local roots only; never re-declare a tracked thread.
- **Tag notable words that aren't threads:** a striking translation choice
  gets a `data-root` span + `roots[]` entry. Read for these deliberately.
- `translit`: one dictionary form (Hebrew: bare root; Greek: lexical form),
  never a list of inflections. `gloss`: plain English, short, general, no
  grammatical labels, never seeded from Strong's first definition. Grammar
  that matters → thread `note` or verse `.gloss`, plain language.
- `example` (optional): one short quoted clause from this unit's English, no
  citation.
- `echo` (optional): one line, reference first, then what it adds. From the
  handoff, not memory.

## Ids, not strings

Root = curated set of lemma ids in `roots.json`. Tracked occurrence carries
its word id (`data-w`, from the word table). Never compare or hand-type
original-language strings. Don't chase word ids: porter fills `data-w`,
reports what it can't decide. Local roots need no `data-w`; nor do tracked
spans inside a `data-verses` component.

## Hard contract

One `<article class="unit" data-unit="N">`, nothing else: no doctype, html,
head, body, style, link, inline `style`, `--c-*` vars. Opens with
`<script type="application/json" id="unit-meta">`. Unknown top-level key =
hard error. Zero native Hebrew or Greek script anywhere, attributes included.

| key | req | type | rule |
|---|---|---|---|
| `unit` | ✓ | int | integer, not string |
| `passage` | ✓ | str | `"Book 6:1–27"` |
| `title` | ✓ | str | |
| `roots` | ✓ | array | below |
| `threads` | ✓ | object | all four sub-keys, empty lists fine |
| `slug` | | str | `"unit-06"`; derived if omitted |
| grouping keys | | int | one per `book.json` grouping; looked up from unit map if omitted |
| `questions` `checks` | | array | below |
| `intertext` `typescenes` | | array | below |

**`roots[]`**: `{root, translit, gloss, example?, echo?}`, no other keys.
`root` matches `[a-z0-9-]+`.

**`threads`**: `{opens, payoffs, candidates, retro, promote?}`. First four
always present, each a list.

- `opens[]` / `payoffs[]`: `{id, ref, note}`. `id` exists in
  `threads-digest.md`. `note` = one-line popover prose.
- `candidates[]`: `{root, why, ids?, refs?}`. Proposals only. `ids` = lemma
  ids copied as the pack or word table spells them. `refs` = a few bare
  `"C:V"`.
- `retro[]`: `{unit, verse, text, root, why, nth?, op?, w?}`. Fix for an
  earlier unit (`unit` = slug, `"unit-04"`). `why` required. `op`: `add`
  (default), `retag`, `retag_word`, `untag_word`, `unwrap`, `strip_span`,
  `text`. Porter fills `w`.
- `promote[]`: `{entry, reach?, retrofit?}`, a promotion taken from the
  handoff. `entry` = `{id, root?, ids, gloss, opens: {unit, note?}, payoffs?:
  [{unit, note?}], translit?, note?}`. `ids` from pack's lemma table. No
  colour. `root` defaults to `id` (ASCII `[a-z0-9-]`). Code computes refs,
  `reach`, `retrofit`. A `retro[]` in the same unit may tag the new id. Still
  needs an id set → stays in `candidates[]`.

**`intertext[]`**: `{ref, to, kind, note?}`. `ref` bare `"C:V"` here, `to`
like `"Ps 67:1"`, `kind`: `quotation`, `allusion`, `echo`, `type-scene`,
`story`, `character`, `reuse`, `law`. Asides and root `echo` are harvested already:
list only what those don't say.

**`typescenes[]`**: `{id, ref, note?, label?}`. `id` from the type-scene list
in `canon-conventions.md`. New `id` needs `label`.

**`questions[]`**: `{topic, note, options?}`. Only a call Lane must make,
real open alternative, left unresolved by the popups. Never a wording already
ruled. `topic` a few words, `note` answerable cold, `options` short. Render
best provisional choice and flag it.

**`checks[]`**: `{ref, claim, expect}`. Claim about another passage's text
for code to verify. `ref` like `"Isa 22:22"`, may pool (`"Exod 16:16 / Exod
38:26"`). `claim` = what the fragment says. `expect` = lemma in
transliteration, a lemma id (`H1538`), or a list; leading `!` = should be
absent. Never in `questions[]`.

## Components

Base components below. Optional ones are enabled in `book.json`;
`components-reference.md` has their markup. Class neither base nor enabled
fails the build.

| component | shape | note |
|---|---|---|
| coloured word | `<span class="r" data-root="X" data-w="…">…</span>` | `class="rl"` only **outside** verse blocks |
| verse | `<p class="v"><span class="n">17</span> … text<sup class="en"><a href="#n1">1</a></sup></p>` | one per verse, in order. Endnote marker last in the verse `<p>`, **never** inside `.gloss` |
| gloss | `<span class="gloss">…</span>` | **following sibling** of the verse, never nested, always closed |
| pericope heading | `<h3 class="pericope">Title <span>· 6:1–7</span></h3>` | `· C:V` range required |
| legend | `<section class="block legend" aria-label="color key"><ul></ul></section>` | **required, even as empty stub** |
| notes | `<div class="notes"><h2>Notes</h2><ol><li id="n3"><strong>hid him (v4).</strong> …</li></ol></div>` | every `href` resolves to an `id` in the fragment |

Asides: closed following siblings of their verse, `data-anchor` = that verse.

**`data-verses`**: component standing in place of verse-by-verse text (table
condensing a repeated formula) carries `data-verses="C:V–V"`, exactly the
verses it replaces. Don't also write them as `p.v`. Range inside the unit's
passage. Say in the pericope's gloss that verses are condensed.

## Balance

- Gloss: a phrase or one sentence, ~25 words max. Grammar point, variant,
  debate between readings → footnote.
- Grammar and commentary = seasoning: only when it changes how the verse
  reads.
- Intertextuality = main course: where earlier Scripture stands behind a
  line, where it returns later.
- Each link lives in one place: word's history → root `echo`; verse-level
  link → `aside.echo`; argument about a link → footnote.
- Voice: no named commentators or resources, no project-internal references
  in fragment prose. Views differ → say so in general terms, give the content
  of the disagreement.
- Wording: `translation-choices.md` (starts from `canon-conventions.md`)
  before rendering a lexeme. Better verse-specific rendering is fine if
  flagged.
- Structures: chiasms and rings only when textually verifiable. Weigh the
  book's own markers with the patterns you notice; where they disagree, say
  so.

## Before saving (what code can't check)

1. Every notable translation choice and every word with a canon history has
   a local span + `roots[]` entry (the latter with `echo`).
2. Wording matches `translation-choices.md`, or deviation flagged.
3. No named commentator or project-internal reference in prose.
4. Glosses short; the unit's intertextual links surfaced; each in one place.
5. Every box says what the link does here. Nothing weak ships.
6. `questions[]` = open calls for Lane only; claims about other passages'
   text are in `checks[]`.

## Worked example

Shape only: ids, names and threads are one Hebrew book's. A book's style
reference may carry its own.

```html
<article class="unit" data-unit="1">
<script type="application/json" id="unit-meta">
{
  "unit": 1,
  "passage": "Numbers 1:1–54",
  "title": "The First Accounting",
  "roots": [
    { "root": "polls", "translit": "gulgolet", "gloss": "skull; hence a head counted, per person",
      "example": "every male, by their skulls",
      "echo": "Exod 16:16; 38:26 — manna gathered per skull, and the half-shekel paid per skull" }
  ],
  "threads": {
    "opens": [
      { "id": "account", "ref": "1:3", "note": "paqad opens the book: both censuses are built on it; later it turns to ‘call to account’ (14:18, 29)." }
    ],
    "payoffs": [], "candidates": [], "retro": []
  }
}
</script>

<header class="mast">
  <div class="kicker">The Book of Numbers · Study Translation</div>
  <h1>The First Accounting</h1>
  <div class="unit">Unit 1 · Numbers 1:1–54</div>
</header>

<section class="block legend" aria-label="color key"><ul></ul></section>

<h3 class="pericope">Yahweh orders an accounting <span>· 1:1–4</span></h3>

<p class="v"><span class="n">2</span> “Lift the head of the whole community of Yisrael’s sons, every male, by their <span class="r" data-root="polls">skulls</span>.<sup class="en"><a href="#n1">1</a></sup></p>
<span class="gloss"><em>lift the head</em> — the idiom for taking a sum; <em>by their skulls</em>, head by head.</span>

<p class="v"><span class="n">3</span> From twenty years old and up, y’all shall <span class="r" data-root="account" data-w="04kfX">take account of</span> them by their armies, you and Aharon.</p>

<div class="notes">
  <h2>Notes</h2>
  <ol>
  <li id="n1"><strong>skulls (v2).</strong> The longer discussion goes here.</li>
  </ol>
</div>
</article>
```
