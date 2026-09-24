# Bible Study Platform — Shared Architecture

**Status:** core 0.1.0, 2026-09-22. Built and tested (see §8); Numbers, the
first book on it, will shape it further. Expect it to change.

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
| **Shared package** (`biblecore/`) | this repo, vendored into each book as `<book>/biblecore/` at a pinned version | shared | Fix it here and re-vendor (`tools/core_sync.py`). A book adopts a new version when it chooses. |
| **Starter template** (`template/`) | copied once into a new book | the book, from the moment it's copied | Freely, in the book. Improvements worth sharing come back to the template by hand. |
| **Book-only** | the book repo | the book | Freely. |

**Shared package: mechanism, not taste.** Code where a bug fixed once should
be fixed everywhere, run from a book's root as `python -m biblecore <command>`:

- `book.py` — reads `book.json`; every module asks it for paths and settings;
- `meta.py` — the meta block (parse, validate, generate, inject) and the
  fragment checks (endnote pairing, no Hebrew *or* Greek script, `data-root`
  resolves, tracked spans carry `data-w`, pericope ranges, echo anchors and
  nesting, no inline style, component whitelist read from the book's CSS);
- `audit.py` — thread coverage as set arithmetic over word ids; `data_w.py`
  fills `data-w` by alignment; `roots.py` validates the id sets;
- `colour.py` — CIEDE2000 distance and palette assignment for local roots and
  newly promoted threads;
- `port.py` and `build.py` — the default porter and build. They're mechanism
  too, but a book that needs a different sequence writes its own script that
  calls the same steps, rather than editing these;
- `retrofit.py`, `scan.py`, `verify_occurrences.py`, `refresh.py`,
  `validate_units.py`, `digest.py`, `leads.py` (canon leads), `sync.py`;
- language adapters (`lang/hebrew.py`) and corpus adapters (`corpus/oshb.py`).

**Starter template: taste, and anything likely to vary by genre.** The app
shell (JS, `index.html`) with generic groupings, the stylesheet (starting as
Joshua's theme, to be re-themed), empty `data/` seeds and a starter palette,
the style-reference and chat-side skeletons (✎ marks what the book decides),
`translation-choices.md` starting from `canon-conventions.md`, `CLAUDE.md`,
and the session-context files.

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
- Stem-mode auditing (Matthew's `thread-stems.json`) is **not** built: every
  planned book has a corpus with word ids (OSHB for Hebrew; a Greek corpus
  with ids when the first Greek book starts). A corpus without ids would
  need a stem-matching audit added then.
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

**Declared verses.** A component that stands in for verse-by-verse text (a
table condensing a repeated formula) names the verses it replaces with
`data-verses="C:V–V"`. The audit then reports thread occurrences there as
*covered*, not as gaps; the build fails if a declared verse is also written
out as a verse, or falls outside the unit (Lane, 2026-09-23, from Numbers
1:22–43).

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

One closed-key manifest per book (`biblecore/book.py`). It holds everything
that used to be scattered through Joshua's code.

```json
{
  "book": "Numbers", "osis": "Num", "abbrev": "Num", "slug": "numbers",
  "language": "hebrew",
  "corpus": {"kind": "oshb", "pin": "morphhb@2.0.2", "word_ids": true},
  "groupings": ["movement"],
  "components": ["echo"],
  "meta_keys": [],
  "checks": {"opens_note_required": true},
  "palette": "data/palette.json",
  "sync": {"files": ["numbers_study_style_reference.md", "..."],
           "globs": ["canon-leads/canon-leads-unit-*.md"]},
  "storage_key": "numbers",
  "paths": {},
  "core": "0.1.0"
}
```

- `groupings` — the kinds of grouping a unit belongs to. Each becomes an
  optional integer key in the meta block and the unit's `units.json` row;
  `units.json` `groupings[]` holds `{kind, n, name, label?, span, units}`,
  and the first kind drives the site's book map. Numbers could use
  `generation`, Kings `reign`, Psalms `book`.
- `meta_keys` — extra meta-block keys this book wants; validated and
  round-tripped by `generate()`.
- `checks` — switches for checks that reasonably differ by book.
- `paths` — override any default location (Joshua's layout is expressed
  this way in `tests/joshua-book.json`).

Unknown keys are an error, and every key is read by code (H5). New keys are
easy to add in `book.py`; keys nothing reads don't stay.

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
- **Divergence report.** `tools/core_diff.py` lists edits made directly to a
  book's `biblecore/` copy, against the exact commit in its `CORE_VERSION`. It is there to catch accidental forks and never blocks a
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
  Numbers (around chs. 16–17 and 29–30 at least). A scratch build of
  morphhb's Numbers gives **1,289 verses** (English Bibles: 1,288), 16,422
  words, 94 petuḥot and 65 setumot, to be checked against printed BHS during
  setup. The map should be
  **derived from the corpus and an English versification source, not typed
  from memory**, and built before unit 1.
- **Canon leads** carry over directly. Numbers' echoes run back into Exodus
  and Leviticus and forward into Deuteronomy, Joshua itself, the Psalms, and
  the New Testament (1 Cor 10, John 3:14, Jude 11, Rev 2:14).
- **Shared vocabulary with Joshua** (ʾaron, ḥerem, naḥalah, nefesh, qadash) is
  already decided in `canon/conventions.md`. Start from those decisions.

---

## 8. Using it

**Starting a book** comes in two stages, because the unit map arrives from the
project side after bootstrap (the order Numbers went in):

1. `python tools/new_book.py ../<Book> --book <Book> --osis <OSIS> [--github]`
   copies the template with its placeholders filled, vendors the core, copies
   the Strong's lexicon (`corpus/lexicon/`, sha1-checked), runs `npm install` +
   `python -m biblecore corpus` + `build`, and makes the first commit.
   `--github` also creates the public repo, enables Pages and runs the first
   sync; without it the script prints those commands. Check the corpus counts
   against a printed edition.
2. Once the map is delivered, run `python -m biblecore units-from-map --kinds
   <outer>,<inner>` in the book. It reads the map's Overview table, adds
   unit rows and groupings to `data/units.json` (additive: existing rows and
   groupings are kept), fills `book.json` groupings, and writes the next
   unit's canon leads. Rename the generated grouping names freely.

**Testing the core:** `python tests/run.py [filter]` (no pytest needed). The
suite runs against Joshua's real data, read-only. Its strongest check:
Joshua rebuilt from the template, porting its four source artifacts through
the CLI, reproduces Joshua's committed units byte for byte with a clean
thread audit (`tests/test_template.py`). It also checks the corpus builder
against Joshua's word table, the audit against Joshua's own audit, and
generate/scan against Joshua's committed files.

---

## 9. Open questions

- Whether the template's app shell and stylesheet should split into shared
  structure plus per-book theme tokens (D10, the component registry D5) —
  wait until Numbers needs its first new component.
