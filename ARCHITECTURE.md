# Bible Study Platform — Shared Architecture

**Status:** draft 0.1, 2026-09-22. It will be shaped by Numbers, the first book
built on it. Expect it to change.

## What this is

This is the rough shape every new book shares: the machinery the books have in
common, and the defaults a new book starts from. **It is not a rulebook.**
Hebrew and Greek books, narrative and law, poetry and letters will each need
their own approach and will keep changing as units ship. Anything here marked
*default* can be changed by a book; record the change and the reason in that
book's own style reference.

Joshua and Matthew are the **reference implementations**. Everything here was
learned there. They are not migrating onto this core (Lane, 2026-09-22). They
keep their own code, and they copy a core fix across only when it clearly
helps.

Where a rule gives a reason, the reason matters more than the rule. Items
marked **(learned)** each cost a real mistake. Read the lesson before relaxing
one of them.

---

## 1. Three layers

| layer | lives in | who owns it | changes how |
|---|---|---|---|
| **Shared package** (`biblecore/`) | this repo, vendored into each book as `core/` at a pinned version | shared | Fix it here and re-vendor. A book adopts a new version when it chooses. |
| **Starter template** | this repo's `template/`, copied once into a new book | the book, from the moment it's copied | Freely, in the book. Improvements worth sharing come back to the template by hand. |
| **Book-only** | the book repo | the book | Freely. |

**Shared package: mechanism, not taste.** This is code where a bug fixed once
should be fixed everywhere:

- the meta block (parse, validate, generate, inject), with core default keys
  that a book can extend;
- the fragment checks (endnote pairing, no native script, `data-root`
  resolves, no inline style, component whitelist read from the book's CSS),
  each of which a book can switch off;
- the thread-coverage audit, as set arithmetic in *id* mode or *stem* mode;
- colour (Lab / CIEDE2000 distance, well selection, collision checks);
- retrofit ops, the occurrence scan and verify, the thread digest, and the
  project-side sync;
- language adapters (`lang/hebrew.py` first) and corpus adapters
  (`corpus/oshb.py` first).

**Starter template: taste, and anything likely to vary by genre.** This covers
the porter and the build steps, the app shell (JS and `index.html`), the
stylesheet, a style-reference skeleton, a chat-side instructions skeleton,
`translation-choices.md` pointing at `canon/conventions.md`, and the
session-context files.

**Book-only:** `book.json`, `data/`, `units/`, `source-artifacts/`, the unit
map, the glossary, the theme, and any scripts only that book needs.

**Seed from Joshua.** Joshua's pipeline is the hardened, tested one.
Matthew's `unit_meta.py`, `audit_thread_coverage.py` and `port_artifact.py`
are only 37–50% similar to Joshua's and have no tests. Matthew is the
reference for the Greek adapter and for components Joshua never needed (ring,
correspondence table, itinerary, compare, synoptic).

---

## 2. The shared shape (defaults)

### The fragment

A unit is **one `<article class="unit" data-unit="N">` and nothing else**. It
opens with `<script type="application/json" id="unit-meta">`. There is no
head, no `<style>`, no inline style and no hand-picked colour. The site
assigns every colour.

### The meta block

Required keys are `unit` (int), `passage`, `title`, `roots` and `threads`.
Optional keys are `slug`, the grouping number, and `questions`. `book.json`
declares any other keys a book wants. **Unknown keys are an error**, not
silently dropped. **(learned:** Matthew's `descriptor` and `discourse` were
authored for eleven units and silently discarded.**)** Every key that
`validate()` allows must also be round-tripped by `generate()`. **(learned:**
Joshua A1/A2: a regenerated meta block failed the project's own validator.**)**

- `roots[]` holds **local roots only**: `{root, translit, gloss, example?,
  echo?}`. A tracked thread's colour, translit and gloss live only in
  `threads.json`. **(learned:** Joshua A3.**)**
- `threads` = `{opens, payoffs, candidates, retro}`. All four are present,
  empty lists are fine. `opens`/`payoffs` entries are `{id, ref, note}`.
  Whether `note` is required is a book setting. Joshua requires it; Matthew
  doesn't.
- `questions[]` = `{topic, note, options?}`. These are wording and data calls
  that only Lane can make. They surface in Claude Code at port time rather
  than being asked on the project side. They are consumed at port time and
  never regenerated.

### Colour and tagging

- **One lexical root per `data-root`.** That means the root and its same-root
  forms, never a theme or a bundle. The one exception is fixed phrases the
  book repeats verbatim. **(learned:** a root/motif two-tier model was built
  and reverted the same day, in Matthew `8d096c9`/`98b721a`.**)**
- **Tag every occurrence, following the lexeme rather than the English
  gloss.**
- Tracked threads have fixed colours across the book, and local roots get a
  per-unit colour. Both are **assigned by algorithm, never picked by eye**.
  Each book supplies its own palette well.
- Notable one-off translation choices, and words with a canon history, get a
  local root (with an `echo` for the canon history).
- `translit` shape is a **language** setting (C1). Hebrew uses one bare root
  form. Greek lists same-stem forms joined by `·`.

### Root identity

- **If the corpus has word ids, use them.** A root is a curated set of
  lemma ids (`roots.json`), every tracked-thread span carries `data-w`, and
  the audit does set arithmetic. **(learned:** consonant-substring matching
  hit 0–42% recall on Joshua's weak-root verbs.**)**
- If it has no word ids, the book supplies a stem matcher (Matthew's
  `thread-stems.json`) and the audit runs in stem mode.
- The chat side never hand-chases word ids. The porter fills `data-w` by
  per-verse alignment (Joshua's `assign_data_w.py`).
- **Never hand-type the original-language script. Pull it by word id.**
  **(learned:** NFC normalisation alone reorders marks in 47% of Joshua's
  words.**)**

### Base components

These are in every book, and the app depends on them:

| component | shape |
|---|---|
| verse | `<p class="v"><span class="n">N</span> … <sup class="en"><a href="#nK">K</a></sup></p>`. The endnote marker comes at the end of the verse material and is never inside another span. |
| coloured word | `span.r[data-root]`, plus `data-w` when the book has word ids. Use `span.rl` for root-linked mentions that aren't counted. |
| gloss | `span.gloss`, a **following sibling** of the verse, never nested, always closed |
| pericope heading | `<h3 class="pericope">Title <span>· C:V–V</span></h3>`. The range is required. |
| legend | `<section class="block legend"><ul></ul></section>`. It is **required even as a stub**. **(learned:** Matthew unit 11 shipped with no colour key.**)** |
| notes | `<div class="notes"><h2>Notes</h2><ol><li id="nK"><strong>lead (vN).</strong> …</li></ol></div>` (C7) |

**Optional components are enabled per book** in `book.json`. Each ships as
one piece: CSS, a check, a JS handler and a style-reference snippet, in the
same commit, and only when a unit actually wants it. **(learned:** Matthew
`67b2712`: asides spliced inside unclosed glosses silently collapsed. And the
port analysis found seven classes that had never been registered.**)** The
known ones so far are `aside.echo` (Joshua); ring, correspondence table,
itinerary, compare and `aside.synoptic` (Matthew).

### Voice and balance (defaults)

- No named commentators or resources in fragment prose, and no
  project-internal references. Say "one reading" and give the content of the
  disagreement. (Matthew adopts this from unit 13, C3.) Research and chat use
  real names freely.
- Glosses are short, about 25 words or fewer. Depth goes in footnotes.
- **Intertextuality is the main course.** Grammar and medieval commentary are
  seasoning, not the meal.
- Transliterate everything. There is no native script anywhere, attributes
  included.
- Structures (chiasms, rings) only when textually verifiable. Prefer the
  text's own markers (Masoretic breaks, formulae) over patterns you've
  noticed. **(learned:** Matthew `e9105a5` cut eight over-reaching chiasms.**)**

### Editorial firewall

`threads.json`, `roots.json` and each book's glossary are **policy**. The
porter proposes and a human disposes. Nothing in the pipeline writes policy on
its own. **Default promotion policy is Joshua's** (Lane, 2026-09-22): Claude
decides whether a candidate becomes a tracked thread, biased toward
book-wide, works mostly autonomously, and asks Lane when genuinely unsure.
A book can change this in its own settings (C2). Matthew keeps its "always
ask Lane" policy.

---

## 3. Where books are expected to differ

| axis | Joshua | Matthew | default for a new book |
|---|---|---|---|
| language / transliteration | Hebrew, `hebrew.py`, no vowel length | Greek, `greek.py`, ē/ō | from the language adapter. **Schemes are frozen per language, never harmonised (H10).** |
| corpus | OSHB, word ids | SBLGNT, no word ids | a corpus with word ids whenever one exists |
| audit mode | id | stem | id |
| groupings | 4 movements | 3 movements + 5 discourses | `groupings: [{kind, n, label, span, units}]`, where the book picks the kinds (D11) |
| optional components | echo | ring, table, itinerary, compare, synoptic | none until a unit asks |
| `opens.note` | required | optional | required |
| promotion policy | Claude decides, biased book-wide | Lane decides | Joshua's: Claude decides, asks when unsure |
| unit map | Lane-authored | Lane-authored | from the book's own project side, once its resources are compiled |
| palette / theme | clay, bronze, Jordan teal | its own | the book's own. A new book is a new token block. |
| glossary | own file | own file | starts from `canon/conventions.md`, records deviations |
| versification | matches English | matches English | a map from Hebrew to English wherever they differ (E1) |

If a book diverges on an axis that isn't listed, add a row.

---

## 4. `book.json`

One closed-key manifest per book. It holds everything that is currently
scattered through code (the palette in the porter, the storage key in
`main.js`, fonts in `index.html`, the `book[:4]` prefix heuristic in the
audit).

```json
{
  "book": "Numbers",
  "abbrev": "Num",
  "language": "hebrew",
  "corpus": { "kind": "oshb", "pin": "morphhb@2.0.2", "word_ids": true },
  "audit": "id",
  "versification": "versification.json",
  "groupings": ["movement"],
  "components": [],
  "meta_keys": [],
  "checks": { "opens_note_required": true },
  "palette": "palette.json",
  "storage_key": "numbers",
  "core": "0.1.0"
}
```

Unknown keys are an error, and every key must be read by some code (H5).
New keys are easy to add; keys nothing reads don't stay.

---

## 5. How it changes

- **Pinned versions.** Each book records `core` in `book.json` and a
  `CORE_VERSION` file, and upgrades when it chooses. A core change never
  reaches a book by surprise.
- **`0.x` while Numbers shapes it**, so breaking changes are fine. **`1.0`**
  once Numbers has a few units built and the shape has held.
- **Override, don't edit.** To change shared behaviour for one book, wrap or
  replace the function in a book-local module. If the change turns out to be
  right everywhere, move it into core and re-vendor.
- **Divergence report.** `core_diff.py` lists edits made directly to a book's
  `core/` copy. It is there to catch accidental forks and never blocks a
  build.
- **Shipped units are never silently regenerated into a new shape.** A schema
  change that affects built units comes with an explicit migration script and
  a report, or it applies only to new units. **(learned:** Joshua A1, and
  Matthew's `extract_units` incident, where eight units silently
  diverged.**)**
- **No submodules (H2).** Vendor a copy.

---

## 6. Workflow defaults (chat side + Claude Code)

The template's chat-side skeleton carries Joshua's current loop, as a default:

1. Pre-read briefing (flowing prose).
2. Verse-by-verse (flowing prose; commentators named freely).
3. **Intertext pass**, starting from the generated `canon-leads` sheet, with a
   ledger that keeps its rejected rows. Lane marks what to keep.
4. Artifact skeleton, with `questions[]` for Lane's calls.

The six standing moves (thread opens/pays off, candidate, notable choice,
canon echo, retro, question) go in the template. A book changes the lens
(commentary set, genre cautions) in its own instructions.

Claude Code side: port, then fill `data-w`, then validate, then build and
audit, then check in a browser, then commit. The project-side sync is a
mirror, so the instruction field **points at the synced files instead of
restating them (H12)**.

---

## 7. Numbers: what to expect first

These are notes, not builds. Nothing here is built until a unit asks for it
(H4).

- **Genre mix.** Narrative, law (chs. 5–6, 15, 18–19, 28–30, 35), lists
  (censuses 1 and 26, camp order 2, the Levite duties 3–4, the twelve
  near-identical tribal offerings of ch. 7, the itinerary of 33, the borders of
  34), and poetry (the priestly blessing 6:24–26, the ark songs 10:35–36, the
  songs of ch. 21, the Balaam oracles 23–24). It is the first test of whether
  the shape bends.
- **Likely first new components:** a list/table component (E15) for the
  censuses and ch. 7, and a poetry/line block (E2) by the Balaam unit.
- **Unit map and groupings** come from the Numbers project side once its
  resources are compiled (Lane, 2026-09-22). That is the same path Joshua's
  map took. Claude Code doesn't draft one. The two candidate framings are the
  census frame (chs. 1 and 26: old generation → new) and geography (Sinai →
  wilderness → plains of Moab); the project side will pick.
- **Versification.** Hebrew and English chapter/verse numbers diverge in
  Numbers (around chs. 16–17 and 29–30 at least). The map should be
  **derived from the corpus and an English versification source, not typed
  from memory**, and built before unit 1.
- **Canon leads** carry over directly. Numbers' echoes run back into Exodus
  and Leviticus and forward into Deuteronomy, Joshua itself, the Psalms, and
  the New Testament (1 Cor 10, John 3:14, Jude 11, Rev 2:14).
- **Shared vocabulary with Joshua** (ʾaron, ḥerem, naḥalah, nefesh, qadash) is
  already decided in `canon/conventions.md`. Start from those decisions.

---

## 8. Open questions

- Whether the starter template's app shell starts from Joshua's `main.js`
  with D11 groupings added, or from a fresh cut (to be decided at step 1).
