# Bible Study Platform — Shared Architecture

**Status:** core 0.9.10, 2026-09-29. Built and tested (see §8). Expect it to
change. Status and history are in `../session_index.md`.

- 0.2.0: shaped by Numbers unit 1 (`data-verses`, in-place promotion,
  `new_book.py` + `units-from-map`, `table.list`, versification E1).
- 0.3.0: contract versions and migrations, the data manifest, the book-side
  `test`, the synced core workflow and canon decisions, and Aramaic word
  language.
- 0.4.0: the component registry and the core.css/theme.css split, with poem,
  itin and textform alongside echo and list.
- 0.5.0: the reading data layer (`emit`) and the reader features (§8).
- 0.6.0: the canon hub (§8), with each book site linked back to it.
- 0.7.0: Greek, a second language adapter and corpus adapter, proven on
  Matthew's data read-only, and the Hebrew -> LXX -> NT bridge (§8).
- 0.8.0: division themes (§8).
- 0.9.0: Joshua and Matthew on the template app shell, with an overlay
  grouping and chip-toggled asides for Matthew (§8).
- 0.9.1: tracked spans inside a `data-verses` component may go without
  `data-w` (colour-only summary tags; Numbers unit 3).
- 0.9.2: a working Greek interlinear for Matthew (a vendored MorphGNT
  lexicon, `lang/greek_lexicon.py`), phrase threads (`roots.json` `seq`,
  plan D2), the LXX corpus adapter and Matthew's canon leads ported into
  `leads.py` (plan D4), and a site-wide source-credit footer (main.js
  `SOURCES`). See "Matthew fully on bible-core" below.
- 0.9.3: MorphGNT's movable-letter parens stripped from Greek lemma ids;
  `tools/stems_to_roots.py`.
- 0.9.4: phrase threads take `alt` (the same title in another word order).
- 0.9.5: audit pass (8 fixes: `--help` no longer runs commands, LXX homograph ids, `seq` backtracking, and others), tests that run without the sibling repos, and the Greek source credit corrected to CC BY-SA 3.0. (The hub polish that shipped in this release was reverted the same day, `8e80045`.)
- 0.9.6/0.9.7: `book.json` `checks.skip_fragment_checks`, a list of hard fragment checks a book switches off (`meta.FRAGMENT_CHECKS` names, or `component:<name>`), and `checks.test_idempotent: false` to drop `biblecore test`'s build-idempotence check; Matthew used both. The hub now rebuilds itself from a GitHub Action in the hub repo (§8).
- 0.9.8: `audit` caches `_lemma_id_forms` (`biblecore test` on a 14-unit book went from minutes to ~16s); `selftest.check_audit` no longer calls `len()` on the audit's int return.
- 0.9.10: line endings. Every file core writes is LF on every OS (`newline` on each writer), to match the `.gitattributes` (`* text=auto eol=lf`) now in core, the template and each book; before this a Windows build wrote CRLF, which shows as modified under `eol=lf`. `test_template` checks that a build writes no CRLF, and that a new book gets the template's `.gitattributes`.
- 0.9.9: performance, same output (checked byte for byte on Numbers and Joshua builds). `audit` builds a lemma-id index once per word table instead of scanning every word per root; `leads` indexes occurrences and pairs once per corpus instead of per rare lemma and per unit; `roots._override`, `known_lemma_ids`, `hebrew.transliterate_word` and `greek._word` are cached; `sync-check` hashes all files with one `git hash-object`; `core_diff` reads the pin with one `git cat-file --batch`. Numbers `build` 18.6s to ~4.5s, `core_diff` 6.4s to 0.55s, core tests 2m15s to ~1m.

## What this is

This is the rough shape every new book shares: the machinery the books have in
common, and the defaults a new book starts from. **It is not a rulebook.**
Hebrew and Greek books, narrative and law, poetry and letters will each need
their own approach and will keep changing as units ship. Anything here marked
*default* can be changed by a book; record the change and the reason in that
book's own style reference.

Joshua and Matthew are the **reference implementations**. Everything here was
learned there. **Joshua runs on this core since 2026-09-26** (Lane reversed
the 2026-09-22 "not migrating" call): vendored package, `book.json`, core
build and sync, and since 0.8.5 the template's app shell with its own
`theme.css`. Its units came through byte-identical apart from the contract
stamp. Matthew is **standalone** (decided 2026-09-29): its own app shell and
`pipeline/`, no core syncs (§8). Core's Greek work was proven against its data.

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
  resolves, tracked spans carry `data-w` outside `data-verses` components, pericope ranges, echo anchors and
  nesting, no inline style, component whitelist read from the book's CSS);
- `audit.py` — thread coverage as set arithmetic over word ids; `data_w.py`
  fills `data-w` by alignment; `roots.py` validates the id sets;
- `colour.py` — CIEDE2000 distance and palette assignment for local roots and
  newly promoted threads;
- `components/` — the component registry (D5): one folder per optional
  component (`component.json`, `style.css`, a `check()`, `snippet.md`).
  `book.json` `components` enables a set; `assets.py` (first build step)
  writes `css/core.css` (shared structure, `web/core.css`),
  `css/components.css`, `data/components.json` (roles for the app shell)
  and `components-reference.md` (synced). Echo, list, poem, itin, textform so far;
- `port.py` and `build.py` — the default porter and build. They're mechanism
  too, but a book that needs a different sequence writes its own script that
  calls the same steps, rather than editing these;
- `retrofit.py`, `scan.py`, `verify_occurrences.py`, `refresh.py`,
  `validate_units.py`, `digest.py`, `leads.py` (canon leads), `sync.py`;
- language adapters (`lang/hebrew.py`) and corpus adapters (`corpus/oshb.py`).

**Starter template: taste, and anything likely to vary by genre.** The app
shell (JS, `index.html`) with generic groupings, `css/theme.css` (colour and
font tokens plus book-only rules, starting as Joshua's look; the structure
is the shared, generated `core.css`, D10), empty `data/` seeds and a starter palette,
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
  per-unit colour. Both are **assigned by algorithm** (colours picked by eye
  collided before; hand-pick one only if Lane asks). Each book supplies its
  own palette well.
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

### Canon registries (G9)

`bible-core/canon/` holds the cross-book layer as flat JSON, no UI until
the hub: `arcs.json` (creation, covenant, exile, presence; extendable),
`threads.json` (canon threads linking book threads, F1), `intertext.json`
(edges, F3) and `typescenes.json` (F4). Each book keeps its own rows in
`data/canon.json`: `echo` edges re-harvested from its `aside.echo` lines and
root echoes on every build, `meta` rows from the optional `intertext[]` /
`typescenes[]` meta keys, merged by the porter. `tools/canon_collect.py`
rolls the books up (Joshua's echoes read-only), keeps rows marked `hand`,
and warns on unknown arcs, missing book threads and new type-scene ids.

### Editorial firewall

`threads.json`, `roots.json` and each book's glossary are **policy**. The
porter proposes and a human disposes. Nothing in the pipeline writes policy on
its own. Who decides whether a candidate becomes a tracked thread is set in
each book's style reference §3; the default is Joshua's (`canon/decisions.md`).
Matthew keeps its own "Lane decides" policy.

---

## 3. Where books are expected to differ

| axis | Joshua | Matthew | default for a new book |
|---|---|---|---|
| language / transliteration | Hebrew, `hebrew.py`, no vowel length | Greek, `greek.py`, ē/ō | from the language adapter. **Schemes are frozen per language, never harmonised (H10).** |
| corpus | OSHB, word ids | MorphGNT (SBLGNT), word ids (0.7.0) | a corpus with word ids whenever one exists |
| groupings | 4 movements | 3 movements + 5 discourses | `groupings: [{kind, n, label, span, units}]`, where the book picks the kinds (D11) |
| optional components | echo | ring, table, itinerary, compare, synoptic | from the registry (`biblecore/components/`), enabled in `book.json`; template enables echo + list |
| `opens.note` | required | optional | required |
| promotion policy | Claude decides, biased book-wide | Lane decides | Joshua's: Claude decides, asks when unsure |
| unit map | Lane-authored | Lane-authored | from the book's own project side, once its resources are compiled |
| palette / theme | clay, bronze, Jordan teal | its own | the book's own. A new book is a new token block. |
| glossary | own file | own file | starts from `canon/conventions.md`, records deviations |
| versification | matches English | matches English | `book.json` `versification`: `kjv` (default) converts the corpus numbering through morphhb's `VerseMap.xml` (`biblecore/versify.py`); `source` keeps it |

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
  "checks": {"opens_note_required": true, "skip_fragment_checks": [], "test_idempotent": true},
  "palette": "data/palette.json",
  "sync": {"files": ["numbers_study_style_reference.md", "..."],
           "globs": ["canon-leads/canon-leads-unit-*.md"]},
  "storage_key": "numbers",
  "paths": {},
  "core": "0.2.0"
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
- `versification` — `kjv` (default): fragments, threads, unit rows and
  leads cite English numbering, and every corpus read converts through
  morphhb's `wlc/VerseMap.xml`; `python -m biblecore corpus` writes the
  differences to `<slug>-versification.md`. `source` keeps the corpus
  numbering (Joshua's sheets were written that way). The generated word
  table, reading text and boundaries stay in source numbering.
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
- **Contract versions (D7, 0.3.0).** The porter stamps each unit's meta
  block and `units.json` row with `contract`, the core version that ported it.
  `meta.FRAGMENT_CHECKS` records the version each check arrived in, and a unit
  is held only to the checks at or below its stamp (unstamped units count as
  0.2.0). A new check therefore never fails a shipped unit. To hold old units
  to it, add a migration to `biblecore/migrate.py` and run
  `python -m biblecore migrate`, which runs the migrations, moves the stamps and
  refreshes the meta blocks.
- **Data as an API (F17).** The build writes `data/manifest.json` (book,
  core, progress, schema version per file). Shapes are in
  `docs/data-shapes.md`. Bump a file's schema in `manifest.SCHEMAS` on any
  incompatible change.
- **No submodules (H2).** Vendor a copy.

---

## 6. Workflow defaults (chat side + Claude Code)

The shared loop lives in `canon/workflow.md`, vendored into each book as
`core-workflow.md` and synced to the project side (D6). The project's
instruction field (`CHAT_SIDE_INSTRUCTIONS.md`, pasted by hand) keeps only the
study's language rules, the lens and the book's departures, and points at
that file. `sync-check` says when the field needs re-pasting (`--mark-pasted`
after pasting). Every other chat-side file is synced from the repo, including
`resources.md` (0.7.1: repo-owned, never uploaded by hand), and each sync
writes `synced-index.md`, the one generated list of synced files with their
roles (`sync.ROLES`). Nothing else restates that list. **(learned:** four
hand-written lists drifted the day files were added.**)** Settled cross-book calls go in `canon/decisions.md`
(`canon-decisions.md`, F22). The loop, as a default:

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

**Precedence.** The instruction field beats `core-workflow.md`; the style
reference owns the artifact rules; a conflict between the field and the style
reference goes to Lane rather than being resolved silently.

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

**Reader features (0.5.0).** The build's `emit` step writes the reading
data layer (`data/words/<ch>.json`, `lemmas.json`, `text.json`;
`docs/data-shapes.md`), and the template's `app/reader.js` uses it:
- reading modes: notes, every note open, translation only, interlinear;
- the interlinear itself, with transliteration, Strong's senses (labelled as
  an identifier, not the translation) and morphology in plain words
  (`lang/hebrew_morph.py`). Tap a word for every occurrence of its lemma;
- search across references, tagged roots, lemmas and the study's English;
- `#/ref/<C:V>` and `#/lemma/<key>` routes;
- "continue where you left off";
- `#/print`, the whole study on one page with every note open.

**The canon hub (0.6.0).** `python tools/hub_build.py ../hub` builds
<https://lanehaden157.github.io/bible/>, its own repo (`lanehaden157/bible`)
federating the book sites (H8). The page, app and CSS live in this repo's
`hub/`. Data comes from each started book's `data/*.json` (read-only;
`lemmas.json` wherever a book's build emits one, Joshua included), plus `canon/books.json`
(the canon in order, which names each started book's site, repo and kind) and
the canon registries, including `canon/paths.json` (reading paths, F21). Pages:
- canon map with progress (F6), and a page per book;
- arcs, canon threads, type-scenes;
- intertext, as a book-by-book matrix plus a filtered list (F3);
- reading paths;
- cross-book search: references, Hebrew lemmas across books, tracked threads (F7).

Book sites whose `book.json` has `"hub"` get an "All books" link (F13), and a
thread popover row, "In the canon: …" (F15), read from the hub's
`data/canon.json`. Starting a new book: add its site/repo/kind to
`canon/books.json`, then rebuild the hub.

**Greek (0.7.0, G7/E12).** `lang/greek.py` is Matthew's transliteration
scheme, frozen (H10). `tests/test_greek.py` defines it: 25 hand-worked
cases, plus parity with Matthew's own `pipeline/greek.py` over every word of
Matthew. `corpus/morphgnt.py` reads MorphGNT (SBLGNT) with the same
interface as `corpus/oshb.py`:
- word ids are `bbccvv` plus position;
- lemma ids are transliterated lemmas (`klēronomeō`), with a digit only when
  two NT lemmas share a transliteration;
- morphology is `<pos>:<parse>`, spelled out by `lang/greek_morph.py`.

A language adapter can now define its own id scheme (`is_id_segment`,
`is_precise`, `bare_id`, `lemma_key_of_id`, `LEMMA_ID_RE`), so roots, the
audit and candidate validation work on Greek ids unchanged. Proof, on
Matthew's MorphGNT and SBLGNT files read-only (`tests/test_corpus_morphgnt.py`):
- the reading text matches Matthew's SBLGNT text word for word, differing only
  in a few punctuation marks;
- `roots.validate` and the audit find *klēronomeō* at 5:5 and *eleos* at 9:13;
- `emit` writes a Greek interlinear with no native script.

A Greek book sets `"language": "greek"`, `"corpus": {"kind": "morphgnt", …}`,
`"versification": "source"` and `paths.morphgnt` (plus `paths.greek_lexicon`
and `paths.lxx` since 0.9.2). The template's chat-side
text and style reference are still Hebrew-shaped, so adapt them when the
first NT book starts (G12).

**Lexical bridge (F2).** `canon/bridge.json` holds one row per canon thread's
key word: the Hebrew ids, the LXX lemma(s) with a verse, and the NT lemma(s)
with a verse. `tests/test_bridge.py` checks every cited word against Numbers'
and Joshua's word tables, Matthew's LXX build and MorphGNT, all read-only. The
hub shows the bridge on each canon-thread page and at `#/bridge`.

**Division themes (0.8.0).** `biblecore/web/themes.json` holds Lane's picks:
- **Five divisions**, each with its own paper, ink, three signature colours and
  typefaces: Torah, Former Prophets, Later Prophets, Writings and New
  Testament. The last two are provisional.
- **Per book:** an accent pair and an emblem. The emblems are in
  `web/emblems/*.svg`, simplified line drawings.

The `assets` step turns the book's entry into `css/division.css`
(`theme.py`). That file carries:
- **Tokens** under core.css's own names. Text-role colours are darkened until
  they read on the paper, and a test checks every book in light and dark.
- **Dark palette:** used for `html[data-theme=dark]`, or for `auto` when the
  system prefers dark. The index.html head script sets data-theme from the
  shared `bible:theme` choice (Settings → Appearance).
- **Banner masthead:** the book's colour, with the emblem in a circle (CSS
  mask over an inlined SVG).
- **Ornament:** a light rule above the notes.
- **Dark-mode tracked words:** lifted toward white (threads.js sets `--rc`;
  the colours themselves never change).

A division may name a `title` face, used on the masthead title only (the
NT's uncials). `tools/legacy_theme.py` opted a pre-core site with its own
app shell into its theme (Lane, 2026-09-26). It is retired now that Joshua
(0.8.5) runs the template shell, and kept for a future site with its own
shell. A book overrides any part in `book.json` `"theme"`. A book with no entry gets
no division.css, and its theme.css fallback tokens (`:where(:root)`) apply.

**Checking a book:** `python -m biblecore test` in the book (`--quick` skips
the build rerun). It checks that the core pin agrees, the corpus loads, the
data parses, every built unit validates, the contract stamps, the style
reference's worked example, and that re-running the build changes no file.
Audit gaps are reported but don't fail it.

**Testing the core:** `python tests/run.py [filter]` (no pytest needed). The
suite reads the sibling book checkouts, read-only: Joshua's real data above
all (scratch copies where a test writes), plus Numbers' word table and
Matthew's MorphGNT, LXX and pipeline for parity checks. `run.py` fails the
run if any file in them changes. Set up with `git clone` of each next to
bible-core, `npm install` in `../Joshua` and `../Numbers` (morphhb), and
`python pipeline/fetch_corpus.py` in `../Matthew`. The Greek path also has
its own small scratch book (`tests/greek_book.py`), so it is tested without
Matthew. Its strongest check:
Joshua rebuilt from the template, porting its four source artifacts through
the CLI, reproduces Joshua's committed units byte for byte with a clean
thread audit (`tests/test_template.py`). It also checks the corpus builder
against Joshua's word table and generate/scan against Joshua's committed
files. (The comparison with Joshua's own audit script went when Joshua
moved onto the core.)

---

**The template shell (0.8.5 / 0.9.0).** Joshua moved off its forked app shell
onto the template's in 0.8.5, so a shell change now reaches every book on core.
Two things came across from Matthew's time on it (0.9.0):
- **Overlay grouping.** book.json `"overlay"` names a secondary grouping kind
  (Matthew: `"discourse"`). The shell draws it over the primary one: a
  ◆ mark on unit chips, brackets under the book map, a key row, and a line in
  each unit's placement ("◆ Discourse I: Sermon on the Mount (1 of 3)").
- **Toggle components.** A verse-aside component may declare `"toggle"` in its
  component.json. Instead of joining the shared * note, it gets its own chip:
  `compare` (✦, several on one verse share a "Rendering" panel) and
  `synoptic` (✧, one chip per parallel).

A book's one-off fragment styling stays in its own `theme.css`. A grouping's
display name is `label`, falling back to `name`.

**Matthew and core: standalone (decided 2026-09-29).** Lane reverted Matthew to
its pre-core state (tag `pre-revert-2026-09-29` keeps the core-era work); the
hub treats it as 'legacy' and it gets no core syncs. Core's Greek work came
from Matthew's data and is where any future Greek book starts:
`corpus/morphgnt.py`, the MorphGNT lexicon (`lang/greek_lexicon.py`, CC BY-SA
3.0, `corpus/README.md`), phrase threads (`roots.json` `seq`/`alt`, matched in
`audit.py`), the LXX adapter and Greek canon leads (`corpus/lxx.py`,
`leads.py`), and the source-credit footer (`main.js` `SOURCES`). The mechanics
are in those modules' docstrings and their tests. Matthew's own `pipeline/`
keeps porting, colours, retrofit, leads, the digest and the sync.

## 9. Parked

Lane parked these (2026-09-24/25); none is planned: F8 maps, F9 timelines, F10
structures as data, F12 vocab app, F19 annotations, EPUB. E3-E10 genre
profiles are built with the book that needs them (H4). Tag **1.0** after a few
more Numbers units are built on the current shape (Lane's call). Housekeeping:
the throwaway GitHub repo `lanehaden157/biblecore-newbook-test` still exists
(deleting it needs the `delete_repo` scope).
