# Bible Study Platform — Shared Architecture

**Status:** built and tested (see §8). Expect it to change. The version is
`biblecore/__init__.py` (the last line below); status and history are in
`../session_index.md`.

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
- 0.9.9: performance, same output (checked byte for byte on Numbers and Joshua builds). `audit` builds a lemma-id index once per word table instead of scanning every word per root; `leads` indexes occurrences and pairs once per corpus instead of per rare lemma and per unit; `roots._override`, `known_lemma_ids`, `hebrew.transliterate_word` and `greek._word` are cached; `sync-check` hashes all files with one `git hash-object`; `core_diff` reads the pin with one `git cat-file --batch`. Numbers `build` 18.6s to ~4.5s, `core_diff` 6.4s to 0.55s, core tests 2m15s to ~1m.
- 0.9.10: line endings. Every file core writes is LF on every OS (`newline` on each writer), to match the `.gitattributes` (`* text=auto eol=lf`) now in core, the template and each book; before this a Windows build wrote CRLF, which shows as modified under `eol=lf`. `test_template` checks that a build writes no CRLF, and that a new book gets the template's `.gitattributes`.
- 0.10.0: less hand upkeep (structural audit step 2). Core supplies the default synced files (`sync.DEFAULT_SYNC`); `book.json` `sync` lists only `extra` and `skip` (§4), and `sync` prunes mirror files that leave the list. `python -m biblecore book` prints the book's state (units, threads, core pin, sync, pasted field), so CLAUDE.md files no longer keep state lines. `tools/new_book.py` fills the book's `canon/books.json` row and the hub workflow clones every book listed there (§8). Tests work on temp copies of the sibling books, and `tests/support.py` refuses any write into them; Numbers is a test fixture; the Joshua fixture matches Joshua's `book.json`.
- 0.11.0: the app shell is core-owned (structural audit F1/F2). `index.html` and `app/*.js` moved from `template/` into `biblecore/web/`, and the `assets` step writes them into each book with the book name filled in, marked "generated, don't edit". Every same-origin link and import carries `?v=<content hash>` computed by the build, replacing the hand-bumped `?v=N`. `biblecore test`'s idempotence check now covers `css/`, `app/` and `index.html` too. Numbers and Joshua moved in the same release; their shells changed only in the `?v` values and the comments.
- 0.11.1: release tooling (structural audit F3/F4/D3). `tools/release.py` cuts a release (the version is written only in `biblecore/__init__.py`; `template/book.json` holds placeholders that `new_book.py` fills), `tools/core_sync.py --all` vendors, builds, tests and commits every core book, and `tools/core_diff.py <book> --template` reports the template changes a book has not taken since its base, the new `book.json` `template` key (`--set-base` moves it; `biblecore book` prints it). The components.css/division.css headers no longer carry the version, so a release rewrites them only when the css changes.
- 0.12.0: Greek books from day one (Greek-in-core pass 1). `new_book.py --language greek` writes a Greek book.json (morphgnt corpus, pinned; versification source), copies the MorphGNT lexicon, and fetches MorphGNT + LXX with the new `python -m biblecore fetch` (pins and sha1s in `biblecore/fetch.py`; a mismatch exits 1). Template files carry language blocks, so a Greek book gets Greek chat-side text, style reference, CLAUDE.md corpus section, .gitignore and CI workflow (G12 closed); Hebrew output unchanged apart from Lane's boundary wording (§6, the field's lens line). `--no-register` for scratch books; `corpus` checks Greek lemmas against the lexicon; `units-from-map` writes Greek leads; port/data-w messages name the book's language.
- 0.13.0: Greek proven end to end and the interlinear from Matthew's pilot (Greek-in-core pass 2). The porter ran copies of Matthew units 9-14 in a scratch Greek book, reproducibly; from that: chapter-seam verse labels read everywhere and "C:V" retrofit verses and gap stubs, `seq` candidates, itinerary ranges, the retrofit recipe in the template CLAUDE.md. `verify-words` (in `biblecore test` as `words`) re-reads MorphGNT or OSHB without the transliterator. Interlinear, every book: labelled boxes for verses with no block (after their data-verses element), a generation counter against the mount race, language wording (Strong's / lexicon gloss) with the book name, the key above the first verse, word tap to #/search/<id> with the word first (#/lemma/ redirects), a 4.5:1 --gloss token.
- 0.14.0: the `legacy` contract stamp (Matthew onto core, pass 1). A unit stamped `legacy` in its units.json row and meta block is held to no versioned fragment check and `migrate` leaves it alone; set by hand, never by the porter (§5). `selftest` reports the boxed count.
- 0.15.0: per-book colour spacing (Matthew onto core, pass 1). `book.json` `checks.colour_de_min` (default 10) is the floor validation and the porter use; `tools/make_well.py` generates a book's own readable, contrast-checked well at that spacing (ΔE 7 holds 124 colours, ΔE 10 only ~60); `tools/recolour.py` re-assigns a shipped book's colours from it, colours only.
- 0.15.1: Matthew is a core book (pass 1 of 2): the shell takes old `#/unit-NN/vN` links, `canon/books.json` lists Matthew as kind core, ARCHITECTURE's Matthew paragraph says boxed units; core's tests and CI read Matthew's corpus from `corpus/` and its retired pipeline from `archive/pipeline`.
- 0.15.2: retrofit add with a w is idempotent by word id, so a verse can add the same English twice (Matthew 14:19 loaves)
- 0.15.3: core-workflow.md and the resources template no longer limit citation to listed commentaries
- 0.15.4: synoptic (and any display:block aside-box) now collapses: .aside-box[hidden] wins over the component's display

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
stamp. Matthew joined on 2026-10-01 with units 1-13 boxed (`legacy`, §5): tag
edits only, and unit 14 on through core's loop. Core's Greek work was proven
against its data.

Where a rule gives a reason, the reason matters more than the rule. Items
marked **(learned)** each cost a real mistake. Read the lesson before relaxing
one of them.

---

## 1. Three layers

| layer | lives in | who owns it | changes how |
|---|---|---|---|
| **Shared package** (`biblecore/`) | this repo, vendored into each book as `<book>/biblecore/` at a pinned version | shared | Fix it here and re-vendor (`tools/core_sync.py`). A book adopts a new version when it chooses. |
| **Generated into the book** (`css/core.css`, `css/components.css`, `css/division.css`, `index.html`, `app/*.js`, `data/components.json`) | the book repo, written by the build's `assets` step from `biblecore/web/` and the components | shared (the package's output) | Change the source in `biblecore/web/` and rebuild. The build overwrites edits made in the book, and `biblecore test` reports them. |
| **Starter template** (`template/`) | copied once into a new book | the book, from the moment it's copied | Freely, in the book. Improvements worth sharing come back to the template by hand; `tools/core_diff.py <book> --template` shows a book the template changes it hasn't taken (§5). |
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
- `web/` — the site's shared parts: `core.css`, the division themes, and
  since 0.11.0 the **app shell** (`index.html`, `app/*.js`, with generic
  groupings). `assets` writes the shell into the book with the book name
  filled in and a content hash on every link and import (§8);
- `port.py` and `build.py` — the default porter and build. They're mechanism
  too, but a book that needs a different sequence writes its own script that
  calls the same steps, rather than editing these;
- `retrofit.py`, `scan.py`, `verify_occurrences.py`, `refresh.py`,
  `validate_units.py`, `digest.py`, `leads.py` (canon leads), `sync.py`;
- language adapters (`lang/hebrew.py`) and corpus adapters (`corpus/oshb.py`).

**Starter template: taste, and anything likely to vary by genre.**
`css/theme.css` (colour and font tokens plus book-only rules, starting as
Joshua's look; the structure is the shared, generated `core.css`, D10), empty
`data/` seeds and a starter palette,
the style-reference and chat-side skeletons (✎ marks what the book decides),
`translation-choices.md` starting from `canon-conventions.md`, `CLAUDE.md`,
and the session-context files.

**Book-only:** `book.json`, `data/`, `units/`, `source-artifacts/`, the unit
map, the glossary, the theme, and any scripts only that book needs. A book
changes its site through `theme.css` and `book.json` settings (groupings,
overlay, components, theme), not by editing the generated shell.

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
  own palette well. Two roots in a unit read as one colour under CIEDE2000
  10, but only about 60 colours fit at that spacing, so a book that tracks
  more threads than that (a Gospel) sets `checks.colour_de_min` (Matthew: 7,
  a 124-colour well), generates its well with `tools/make_well.py`, and, if
  units already shipped, re-assigns their colours with `tools/recolour.py`
  (colours only; no tag or word changes).
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
| corpus | OSHB, word ids | MorphGNT (SBLGNT), word ids (0.7.0) | a corpus with word ids whenever one exists, pinned: npm (morphhb) for Hebrew, `python -m biblecore fetch` for Greek |
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
  "sync": {"extra": [], "skip": []},
  "storage_key": "numbers",
  "paths": {},
  "core": "0.2.0",
  "template": "ecd5bf6"
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
- `sync` — which files round-trip into the Claude.ai project. Core supplies
  the default set (`biblecore/sync.py` `DEFAULT_SYNC`: the style reference,
  resources, translation choices, the vendored canon and workflow files, the
  generated reference, digest, roots and word table, and, once they exist,
  the unit map, canon leads and versification list). A book lists only what
  it adds (`extra`, paths or glob patterns) and drops (`skip`, matched
  against the resolved paths). Joshua adds its reading text, English text
  and boundary list; Numbers adds nothing. `sync` prunes mirror files that
  leave the list. Before 0.10.0 each book listed every file (`files` +
  `globs`), and a new core file had to be added to every book by hand.
- `paths` — override any default location (none of the current books needs
  one; the tests use it to read big inputs in place).
- `core`, `template` — written by the tools, not by hand: `core` is the
  vendored version (`tools/core_sync.py` sets it), `template` the bible-core
  commit whose `template/` the book last took (`new_book.py` fills it,
  `core_diff.py --template --set-base` moves it; §5).

Unknown keys are an error, and every key is read by code (H5). New keys are
easy to add in `book.py`; keys nothing reads don't stay.

---

## 5. How it changes

- **Pinned versions.** Each book records `core` in `book.json` and a
  `CORE_VERSION` file, and upgrades when it chooses. A core change never
  reaches a book by surprise.
- **Releasing is two commands** (structural audit F3/F4). Commit the change,
  then `python tools/release.py X.Y.Z --note "..."`: it refuses a dirty tree,
  runs the suite, sets `biblecore/__init__.py` (the only place the version is
  written), adds the line to the version list above, commits and tags. Then
  `python tools/core_sync.py --all` takes it to every `kind: core` book in
  `canon/books.json`: vendor, set `book.json` `core`, build, `biblecore
  test`, stage the changed files by name and commit. It skips a book whose
  tree is dirty (another session's work) and says so. Neither pushes.
- **Template drift is reported, not pushed** (D3). The template's files
  become the book's own when copied, so a template fix doesn't reach an
  existing book by itself. `python tools/core_diff.py <book> --template`
  lists each template-seeded file the template changed since the book's
  `template` base, with the diff and whether the book's copy is untouched
  (`take`: replace it whole) or has its own edits (`review`). Taking any of it
  stays optional; `--set-base` records what was taken.
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
- **The `legacy` stamp (0.14.0).** A book that joins core after shipping units
  can box them: `"contract": "legacy"` in the unit's `units.json` row and
  meta block means the unit is held to no versioned fragment check and
  `migrate` leaves it alone. It is set by hand (the porter never writes it, so
  a new unit can't land in it), and it replaces a book-wide
  `skip_fragment_checks`, which would also excuse the book's new units. A
  legacy unit's prose and structure stay as shipped; threads are book-wide, so
  it can still take tag edits (`retrofit`, `data-w`), and `biblecore test`
  reports how many units are boxed. Matthew's units 1-13 are the first.
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
project side after bootstrap (the order Numbers went in). `docs/new-book.md`
is the full checklist around them (who does what, the claude.ai project, the
unit loop):

1. `python tools/new_book.py ../<Book> --book <Book> --osis <OSIS> [--language greek] [--github]`
   copies the template with its placeholders filled, vendors the core, copies
   the lexicon (`corpus/lexicon/`, sha1-checked), puts the corpus on disk
   and runs `python -m biblecore corpus` + `build` (whose `assets` step
   writes the app shell), and makes the first commit. `book.json` gets
   `core` and the template base (`template`, this checkout's commit) filled
   in. `--github` also creates the public repo, enables Pages and runs the
   first sync; without it the script prints those commands. Check the corpus
   counts against a printed edition. The language (default `hebrew`) picks:
   - **Hebrew:** Strong's lexicon, `npm install` (morphhb, pinned in
     `package.json`), `versification` `kjv`.
   - **Greek:** the MorphGNT lexicon, `python -m biblecore fetch` (below),
     `"corpus": {"kind": "morphgnt", …}` and `versification` `source` in
     `book.json` (the Greek paths are `book.py`'s defaults), no
     `package.json`. `biblecore corpus` also checks that every lemma finds
     a lexicon gloss. Read "NT books: things worth knowing first" in
     `docs/new-book.md` before the first unit.
   - **Template text:** template files carry language blocks
     (`<!-- lang: greek -->` … `<!-- /lang -->`, `# lang:` in yml and
     `.gitignore`), and the book keeps its own language's. That covers the
     pasted field, the style reference, `translation-choices.md`, CLAUDE.md's
     corpus section, `.gitignore` and the CI workflow. `core_diff --template`
     resolves them the same way.

   `--no-register` skips the `canon/books.json` row (a scratch or test book;
   a scratch Matthew would otherwise overwrite Matthew's legacy row).
2. Once the map is delivered, run `python -m biblecore units-from-map --kinds
   <outer>,<inner>` in the book. It reads the map's Overview table, adds
   unit rows and groupings to `data/units.json` (additive: existing rows and
   groupings are kept), fills `book.json` groupings, and writes the next
   unit's canon leads. Rename the generated grouping names freely.

**Reader features (0.5.0).** The build's `emit` step writes the reading
data layer (`data/words/<ch>.json`, `lemmas.json`, `text.json`;
`docs/data-shapes.md`), and the shell's `app/reader.js` uses it:
- reading modes: notes, every note open, translation only, interlinear;
- the interlinear itself, with transliteration, a gloss labelled as an
  identifier and not the translation (Strong's senses for Hebrew, "a lexicon
  gloss" for Greek; the key line and tooltips name the book), and morphology
  in plain words (`lang/hebrew_morph.py`, `lang/greek_morph.py`). Since
  0.13.0, learned from Matthew's interlinear pilot (`Matthew/docs/interlinear-pilot.md`):
  - a verse with no block of its own (inside a `data-verses` table, or a
    block-formatted passage) gets a box labelled with its reference, right
    after the element that declares it, or before the next verse when
    nothing declares it (Lane, 2026-10-01). A verse jump resolves to that
    box, or to the declaring element when the interlinear is off;
  - a mount waits on a generation counter, so switching mode or unit
    mid-fetch never leaves boxes behind or doubles them, and a jump waits
    for the boxes;
  - the key line sits above the first verse (core fragments have no verse
    wrapper);
  - the gloss has its own `--gloss` token, 4.5:1 on the box in both themes;
- tapping a word opens `#/search/<lemma id>`: that word's block first and
  open, then the tracked roots and the other words that match (Lane's L4,
  every book). A Strong's number shows only its own word, never loose
  matches on the digits;
- search across references, tagged roots, lemmas and the study's English;
  the address follows the box (`#/search/<query>`);
- `#/ref/<C:V>` and `#/search/<query>` routes (`#/lemma/<key>`, the old
  word link, still redirects there);
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
`data/canon.json`. Starting a new book: `tools/new_book.py` fills its
`canon/books.json` row (site, repo folder, kind `core`); commit that in
bible-core. The hub repo's rebuild workflow clones every book with a `site`
and a `repo` from `canon/books.json` (the GitHub repo named by the Pages URL,
into the folder `repo` names), so no workflow edit is needed.

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

A Greek book sets `"language": "greek"`, `"corpus": {"kind": "morphgnt", …}`
and `"versification": "source"`; its corpus paths (`morphgnt`, `lxx`,
`greek_lexicon`) default to `corpus/…`. `new_book.py --language greek`
writes all of this (0.12.0, Greek-in-core pass 1).

**The Greek corpus (0.12.0, Lane's L1).** `python -m biblecore fetch` is the
Greek book's `npm ci`. The pins live in `biblecore/fetch.py`, the same commits
as Matthew's `pipeline/fetch_corpus.py`, so a book's corpus moves only with its
vendored core:
- MorphGNT SBLGNT, all 27 books. Leads read the rest of the NT, and the
  lemma ids number a shared transliteration by first appearance across every
  file on disk, so a book with fewer files could spell an id differently.
- The four CenterBLC LXX feature files that `corpus/lxx.py` reads.

Every file has a sha1, checked on download and on every run. A mismatch
exits 1 and names the file (`--force` replaces it, `--check` checks without
the network). The files are git-ignored in the book; `lexemes.yaml` is copied
from core and committed. For a Hebrew book `fetch` does nothing.

**Chat-side text for Greek (G12, closed 0.12.0).** The template's language
blocks carry the Greek wording, written fresh for core books (Lane's calls,
2026-10-01). Greek books get:
- "a little Greek and Hebrew", with grammar categories named;
- the LXX-first lens, with the Hebrew behind it where it matters;
- the transliteration scheme spelled out in style reference §5, since the
  chat side can't run `lang/greek.py`;
- general gloss rules, with no Strong's;
- boundaries argued from the book's own markers and the patterns noticed,
  weighed together (Hebrew got the same change);
- four NT genre cautions as strong suggestions: Gospel parallels, LXX
  quotations, the argument of a letter, apocalyptic imagery;
- a `logizomai` worked example.

**Greek proven end to end (0.13.0, Lane's L3).** The porter has run Greek
units: a scratch Matthew made with `new_book.py --language greek` took
copies of Matthew's contract-shaped source artifacts for units 9-14 (read
only; Matthew is untouched) through the normal loop: `port`, promotions
with `colour`, the thread delta, `data-w`, retrofit, `build`, `audit`,
`test`. Every unit passed `biblecore test`, and two runs from nothing gave
byte-identical books (191 files), the way the system map's unit-4 replay
did for Hebrew. The replay and its log are in `../greek-proof/`. What it
taught core:
- chapter-seam verse labels (`11:1`) are read everywhere the porter looks,
  and retrofit and the gap stubs say `"verse": "C:V"` in a unit that
  crosses a chapter;
- a candidate may propose `seq` (a phrase thread), previewed like `ids`;
- an itinerary stop may cite a range (`12:1–8`);
- the retrofit recipe `data-w` points to ships in the template's CLAUDE.md.
`tests/test_greek_port.py` ports a small Greek unit through the CLI, and
`verify-words` (in `biblecore test` as `words`) re-reads MorphGNT or OSHB
without the transliterator and checks the interlinear data against it.
What Matthew's older artifacts needed and a template-shaped one won't (a
missing `retro` list, Greek-script `stems`, legend-less units, itinerary
labels in `<sup>`) was fixed in the copies, not in core.

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
(0.8.5) runs the shared shell, and kept for a future site with its own
shell. A book overrides any part in `book.json` `"theme"`. A book with no entry gets
no division.css, and its theme.css fallback tokens (`:where(:root)`) apply.

**Checking a book:** `python -m biblecore test` in the book (`--quick` skips
the build rerun). It checks that the core pin agrees, the corpus loads, the
data parses, every built unit validates, the contract stamps, the style
reference's worked example, and that re-running the build changes no file
(data, units, digest, and since 0.11.0 the generated `css/`, `app/` and
`index.html`, so a hand edit to the shell is reported).
Audit gaps are reported but don't fail it.

**Testing the core:** `python tests/run.py [filter]` (no pytest needed). The
suite reads the sibling book checkouts: Joshua's real data above all, Numbers
(`biblecore test` on a copy, as the template-shaped fixture), and Matthew's
MorphGNT, LXX and pipeline for parity checks. `tests/support.py` gives each
test a temporary copy of the book it needs (`copy_of()`; big read-only
inputs such as morphhb and the lexicons are read in place), and importing it
installs a guard that refuses any write into the siblings for the rest of
the process, so a harness that calls test functions directly is covered too
(structural audit B1). `run.py` still fails the run if a file there
changes, which also covers child processes. Set up with `git clone` of each next to
bible-core, `npm install` in `../Joshua` and `../Numbers` (morphhb), and
`python pipeline/fetch_corpus.py` in `../Matthew` (`test_greek_setup` checks
those files against core's `fetch.py` pins). The Greek path also has its own
small scratch book (`tests/greek_book.py`), so it is tested without Matthew.
On it, `test_greek_setup` runs a Greek book made from the template through
the CLI: `corpus`, `build`, `test`, `book` and `units-from-map`. It also tests
the fetch's sha1 failures against a local `file://` mirror, so the suite
needs no network. Its strongest check:
Joshua rebuilt from the template, porting its four source artifacts through
the CLI, reproduces Joshua's committed units byte for byte with a clean
thread audit, and its build writes the same app shell as Joshua's
(`tests/test_template.py`). It also checks the corpus builder
against Joshua's word table and generate/scan against Joshua's committed
files. (The comparison with Joshua's own audit script went when Joshua
moved onto the core.)

**Continuous integration (structural audit B3).** Both halves also run on
GitHub Actions, on every push and pull request:
- bible-core's `.github/workflows/tests.yml` checks out this repo (full
  history, for the template-drift tests) with Joshua, Numbers and Matthew
  beside it from their pushed `main`, installs morphhb and Matthew's corpus
  (cached), checks that data is in place (the sibling tests would otherwise
  skip quietly), and runs `python tests/run.py`.
- Each book runs `python -m biblecore test` from `.github/workflows/tests.yml`.
  A Hebrew book runs `npm ci` first, since without morphhb's verse map its
  English numbering quietly falls back to the Hebrew. A Greek book runs a
  cached `python -m biblecore fetch`, which checks every sha1 on a cache hit
  too. The template ships the workflow unchanged apart from its language
  block (`test_template` checks both), so a new book has CI from its first
  push. Commits touching only `project-side/` or session files skip it.
A failed run emails the pusher (GitHub's default notification).

---

**The app shell (0.8.5 / 0.9.0 / 0.11.0).** Joshua moved off its forked app
shell onto the template's in 0.8.5. Since 0.11.0 the shell is core-owned
(structural audit F1/F2): `biblecore/web/index.html` and
`biblecore/web/app/*.js`, written into each book by `assets` (`assets.shell()`):
- **Filled from `book.json`:** the title, description and brand come from
  the book name (Lane, 2026-09-29: no separate key for custom wording).
- **Marked generated:** each file starts with a "generated, don't edit"
  comment. A rebuild overwrites a hand edit, and `biblecore test` reports it.
- **Content-hashed cache-busting:** the sources import plain `"./x.js"`. The
  build stamps every same-origin import, and every `css/` and `app/` link in
  `index.html`, with `?v=<first 10 hex of sha256>`. A module's hash covers
  its text after its own imports are stamped, so a change reaches every
  importer and index.html. Stylesheet hashes cover the css as the build
  leaves it, so editing `theme.css` changes only its own link. The import
  graph has to stay acyclic; `assets` stops with a message if it isn't.
- **A book with a single-file `paths.css`** (the old Joshua layout, kept in
  the tests) gets no shell and keeps its own.
- **Where a book hook would go (not built).** Neither book needs one yet
  (Lane, 2026-09-29). The planned shape is an optional, book-owned
  `app/book.js`. `assets` would link it after `main.js` in `index.html` with
  its own hash, only when the file exists, and never write it. `main.js`
  would expose the few calls it needs (routes, per-unit enhancers). Build it
  when a book first needs something `theme.css` and `book.json` can't
  express. `assets` never deletes files it didn't write, so a book's own
  file in `app/` is safe.

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

**Matthew and core (2026-10-01).** Matthew is a core book with its first 13
units boxed: they are stamped `contract: "legacy"` (§5), keep their prose and
structure as built, and take only tag edits. Units from 14 on go through core's
`port` loop like Numbers and Joshua. (Lane reverted Matthew to its own
pre-core state on 2026-09-29, tag `pre-revert-2026-09-29` keeps that core-era
work, and chose this boxed form the next day.) Core's Greek work came from
Matthew's data: `corpus/morphgnt.py`, the MorphGNT lexicon
(`lang/greek_lexicon.py`, CC BY-SA 3.0, `corpus/README.md`), phrase threads
(`roots.json` `seq`/`alt`, matched in `audit.py`), the LXX adapter and Greek
canon leads (`corpus/lxx.py`, `leads.py`), and the source-credit footer
(`main.js` `SOURCES`). The mechanics are in those modules' docstrings and their
tests. Matthew's colours come from its own 124-colour well at ΔE 7 (§2).

## 9. Parked

Lane parked these (2026-09-24/25); none is planned: F8 maps, F9 timelines, F10
structures as data, F12 vocab app, F19 annotations, EPUB. E3-E10 genre
profiles are built with the book that needs them (H4). Tag **1.0** after a few
more Numbers units are built on the current shape (Lane's call). Housekeeping:
the throwaway GitHub repo `lanehaden157/biblecore-newbook-test` still exists
(deleting it needs the `delete_repo` scope).
