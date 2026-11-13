# Bible Study Platform — Shared Architecture

The shared shape, where books differ, how core changes. Expect it to change.
Version: `biblecore/__init__.py`. Release list: `history/versions.md`. Using
it (starting a book, reader features, hub): `docs/using.md`.

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
  never regenerated. A `questions[]` entry has a genuinely open alternative
  the unit's argument depends on; a wording already ruled (`translation-choices.md`,
  earlier units' meta) is a note in the artifact's prose.
- `checks[]` = `{ref, claim, expect}` (0.18.0). Claims about other passages'
  text for the code side to verify against the corpus; `expect` is a string
  or a list of lemma(s), `"!lemma"` for one that should be absent. A Greek
  book runs them with `lxx --checks N` (0.19.0). `port` prints them in their own section and the
  thread delta lists them; they are never questions. Consumed at port.
- `threads.promote[]` (optional, 0.18.0) = `{entry, reach, retrofit}`: a thread
  ready for `threads.json` (`id, root, ids, gloss, opens, payoffs`, no
  colour), its reach in words, and the units that need a retrofit. `port`
  turns it into a ready delta with the id-set preview. Consumed at port;
  `candidates[]` stays for proposals that still need an id set.

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

**Tiers.** A book opts in with `"tiers": true`; units are then full,
condensed or digest, some are peaks, and the site opens on the peaks path
(`docs/using.md`, "Tiers"). Every tier code path is gated on that key, and the
shell carries its part between `//tiers:` marker lines that `assets` strips
for any other book, so a tierless book's output is byte-identical to before
(`tests/test_tiers_noop.py`).

**Tabernacle map and `ritual` (opt-in).** A book that lists `ritual` in
`components` gets the shared map: `biblecore/tabmap.py` draws it as SVG from
one cited dimension table (Exod 26-27, 40; Milgrom's Fig. 1 only for positions
the text leaves open, marked schematic), `assets` writes `data/tabmap.html` and
`app/tabmap.js`, and `main.js` calls it between `//ritual:` marker lines that
`assets` strips for any other book (shell text unchanged; no CSS either). It
lives in core, not the `web/` shell, so the dimensions, zone ids (`veil` is
drawn "curtain") and the strip check share one module. `ritual` steps name a
zone with `data-at`; tapping one lights it on the unit's map inset and sheet.

**Laws and `lawparallel` (opt-in).** `biblecore/laws.json` is the one list of
laws the Torah restates (a law id, its passages in Bible order, each with a
summary, stated differences, the text's own reasons, and a `footnote` that is
the only place a dating or source debate may go); `biblecore/laws.py`
validates it. It lives in the package, not `canon/` or a book's `data/`:
laws cross books, and the box check has to read the same file in every
vendored book that the hub draws its law index from (`canon/` is not
vendored). The cost is that a new law is a core release; briefs don't cost
that. `aside.lawparallel` works like `mirror`, but its rows are copied: a
row's `span.diff` and `span.why` must equal a difference or reason the file
holds, and `data-at` must be this book's passage of the named law. Canon kind
`law` (intertext rows from the box's `span.src` refs, source `law`). **Law
behind this:** a law unit's meta `lawbriefs[]` (`{law, ref, brief}`, at most
two sentences, ref inside one of the law's passages) is merged at port into
`data/canon.json` (`lawbriefs`, written only when present), `hub_build.py`
rolls the built units' briefs into the hub's `data/law-briefs.json` (with
the unit's slug and site), and a book with `"law_chips": true` fetches it at
page load (`app/lawchip.js`, between `//law:` marker lines like ritual) and
chips each `aside.echo` whose target overlaps a brief's range. An unreachable
hub or an empty file means no chip. The hub's `#/laws` page lists every law.
A book without these gets no changed byte (tests/test_laws.py).

**Side by side, `calendar`, and the overlay with verse ranges (group 4).**
*Side by side* is `aside.synoptic` under a per-book chip word: book.json
`"component_labels": {"synoptic": "Side by side"}` is merged into that
component's `toggle.labels` in `data/components.json` (Hebrew-OT pairs need
nothing else; Matthew has no label and no changed byte). *Calendar*:
`biblecore/calendar.json` (feasts → passages in Bible order, each with an
optional `date` and `requires` statements; `biblecore/calendar.py` validates)
sits in the package for the same reason as `laws.json`: Lev 23, Num 28–29 and
Deut 16 cross books, and the box check must read one file in every vendored
book; a new feast is a core release. `aside.calendar` names one feast
(`data-feast`) or `all`, and every row's date and requirement is copied from
the file. The file ships empty; book sessions fill it. *Treaty overlay*: not a
new component but the existing overlay grouping, extended. A book that sets
`"overlay_note"` (shown in the book map's key) gets, in `units.json`
`groupings[]`, optional `verses` per member (`{"4": "4:26"}`, inside that
unit's passage), elements with non-contiguous members, and a unit in several
elements; the map brackets each run of neighbours (overlapping brackets take
their own rows), the placement line names every element with its verses
(`biblecore/overlay.py` validates, `app/main.js` between `//overlayx:` marker
lines, `web/overlay.css` appended to core.css). No marks go in the text. A
book without `overlay_note` gets no changed byte (tests/test_sbs_calendar_treaty.py).

**Inbound leads.** The unit pack's "Already cited from" section
(`biblecore/inbound.py`) is the reverse of the outward word leads: every canon
row (echo, story, mirror, law, intertext) whose *target* overlaps the unit,
grouped by the book and unit that made it, with anchor, kind and note. No
store of its own: it reads this book's `data/canon.json` and mirror files,
those of every sibling folder with a `book.json`, and bible-core's
`canon/intertext.json` when a `bible-core/` folder sits beside the book (a
book vendored alone sees only its own rows). All refs are in displayed
numbering already, so no map is applied. A row the unit made itself is left
out, duplicates across stores are listed once, and none found says so in one
line (tests/test_inbound.py).

**Optional components are enabled per book** in `book.json`. Each ships as
one piece: CSS, a check, a JS handler and a style-reference snippet, in the
same commit, and only when a unit actually wants it. **(learned:** Matthew
`67b2712`: asides spliced inside unclosed glosses silently collapsed. And the
port analysis found seven classes that had never been registered.**)** The
known ones so far are `aside.echo` (Joshua); ring, correspondence table,
itinerary, compare and `aside.synoptic` (Matthew); `digest` (tiers); `ritual` (Leviticus); `lawparallel` (Leviticus, Deuteronomy); `calendar` (Leviticus, Deuteronomy).

### Voice and balance (defaults)

- No named commentators or resources in fragment prose, and no
  project-internal references. Say "one reading" and give the content of the
  disagreement. (Matthew adopts this from unit 13, C3.) Research and chat use
  real names freely.
- Glosses are short, about 25 words or fewer. Depth goes in footnotes.
- **Intertextuality is the main course.** Grammar and medieval commentary are
  seasoning, not the meal.
- Transliterate everything. There is no native script anywhere, attributes
  included. The one exception is the site's interlinear, whose top line
  shows each word in the original script, from `data/script/` (generated by
  `emit`, never written by hand or in a fragment).
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
instruction field (`CHAT_SIDE_INSTRUCTIONS.md`, pasted by hand when Lane is told it changed; nothing tracks that) keeps only the
study's language rules, the lens and the book's departures, and points at
that file. Every other chat-side file is synced from the repo, including
`resources.md` (0.7.1: repo-owned, never uploaded by hand), and each sync
writes `synced-index.md`, the one generated list of synced files with their
roles (`sync.ROLES`). Nothing else restates that list. **(learned:** four
hand-written lists drifted the day files were added.**)** Settled cross-book calls go in `canon/decisions.md`
(`canon-decisions.md`, F22). The loop, as a default:

1. Briefing (flowing prose, for listening), naming the earlier stories the
   unit leans on without telling them.
2. **Research** (a working pass): scene by scene, the earlier stories with the
   same shape, then the generated `canon-leads` sheet (word leads and a noun
   sweep), then the parallel accounts. Its output is a notes file that keeps
   its rejected rows; chat gets one line.
3. Verse-by-verse (flowing prose, for listening; commentators named freely),
   telling each earlier story where a verse reaches it, and ending with the
   list of what goes in the artifact (Lane's veto point).
   After Lane's yes, the research chat writes `<book>_NN_handoff.md`
   (`canon/handoff-template.md`, synced as `canon-handoff-template.md`).
4. Artifact (a working pass), in a **fresh build chat** that opens with the
   pasted handoff (0.18.0): built from the handoff, the style reference and
   the synced files, without redoing the research. It asks Lane about
   anything missing or contradictory instead of re-researching, puts the
   handoff's questions to Lane in chat, and uses `questions[]` only for what
   remains. The handoff carries the ledger rows that ship plus a count of
   what was dropped; the full ledger stays in the research chat.

(0.18.0 split passes 1-3 and pass 4 into two chats so each gets a whole
context; the research can run on a lighter model and the build on a heavier one.)

(0.17.0 reordered this: the intertext work used to be a separate pass 3 after
the verse-by-verse, so what it found never reached the passes Lane listens to.)
The seven standing moves (thread opens/pays off, candidate, notable choice,
canon echo, retro, story or type-scene, question) go in the template. A book changes the lens
(commentary set, genre cautions) in its own instructions.

**How a chat reaches the files.** Synced files aren't on disk in a project
chat, don't show in listings, and reach project search only as excerpts, so
the access rule can't live in a synced file. The field's "Where things are"
block holds it: download whole files from raw GitHub (the repos are public),
with the fetch tool and then search as fallbacks. Keep paths and chat tool
names in that block where you can, because they've changed underneath the
docs before. **(learned:** the rule sat in Joshua's `resources.md`, which a
chat couldn't read until it already knew the rule.**)**

Claude Code side: port, then fill `data-w`, then validate, then build and
audit, then check in a browser, then commit. The project-side sync is a
mirror, so the instruction field **points at the synced files instead of
restating them (H12)**.

**Precedence.** The instruction field beats `core-workflow.md`; the style
reference owns the artifact rules; a conflict between the field and the style
reference goes to Lane rather than being resolved silently.

---

## 8. Using it

Moved to `docs/using.md`.

## 9. Parked

Lane parked these (2026-09-24/25); none is planned: F8 maps, F9 timelines, F10
structures as data, F12 vocab app, F19 annotations, EPUB. E3-E10 genre
profiles are built with the book that needs them (H4). Tag **1.0** after a few
more Numbers units are built on the current shape (Lane's call). Housekeeping:
the throwaway GitHub repo `lanehaden157/biblecore-newbook-test` still exists
(deleting it needs the `delete_repo` scope).
