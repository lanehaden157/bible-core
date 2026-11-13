# Using bible-core

ARCHITECTURE.md §8, kept apart from the design. Starting a book, the reader
features, the hub, Greek, themes.

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

**Tiers (a book opts in with `"tiers": true`).** A tiered book marks each
unit full (every verse translated), condensed (key verses translated; the
rest as tables and strips) or digest (a stretch as one short summary), and
marks some units peaks. The site opens on the peaks path: a peak in full, any
other unit as a short digest card with "Open the full unit". A device
remembers its Peaks/Full choice (`localStorage`); `?view=peaks|full` in a link
overrides it for that load; a link to one verse opens its unit in full. The
Contents drawer's outline shades each unit by tier and stars the peaks.
- **Opt in:** `new_book.py --tiers` (book.json `tiers`, the `digest`
  component, the tier route in the field, `fetch` for WEB), or add the key and
  component to an existing book. A book without the key has none of this: no
  extra build output, and a shell with no tier code.
- **Unit map:** the Overview table may add `| Tier | Peak |` columns; Tier is
  `full` (default), `condensed` or `digest`, then `;`-separated stretches
  inside the unit (`24:10–16 digest`); Peak is any mark (★). A `## Digests`
  section adds `- NN: text` lines. `units-from-map` writes `tier`, `peak`,
  `stretches` and `digest` into `units.json`, including onto built rows, so a
  shipped unit gets a peak mark or a digest from the map alone. A unit's own
  meta `digest` fills its row at port and wins over the map's.
- **Digests:** every built unit carries two to four sentences, at most 80
  words (`python -m biblecore tiers` and `validate` fail a missing or long
  one). A stretch the map marks digest is covered by `section.block.digest`
  blocks with exact `data-verses` (component `digest`).
- **World English Bible:** an expand button under any `data-verses` block
  shows WEB text, labelled as not the study's translation. The pinned USFM is
  tracked in `corpus/web/` (`corpus/README.md`); `emit` writes
  `data/web/<ch>.json` in the book's numbering and fails if a chapter's verses
  differ from the corpus's.
- **Thread counts:** `occurrences.json` gives each root an `untr` entry for
  occurrences in the unit's verses that are not written out, counted from the
  corpus; popovers show them as "not translated here" and a timeline still
  lists the unit.
- **Chat side:** `card-condensed.md` (vendored only into a tiered book) is the
  one-chat card. New books' pasted field sends every chat to the synced
  `lens.md`, the book's reading lens.
- **Shell:** tier code lives in `app/tiers.js` and between `//tiers:begin`
  / `//tiers:end` marker lines in `main.js` and `threads.js`. `assets` strips
  the markers (and omits `tiers.js`) for a tierless book, so its generated
  shell is byte-identical to before. `tests/test_tiers_noop.py` holds that
  against a base commit (`BIBLECORE_NOOP_BASE=<commit>`, Joshua/Numbers/Matthew).

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
- `emit` writes a Greek interlinear with no native script outside `data/script/`.

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

**Tabernacle map and rituals (a book opts in with `"ritual"` in `components`).**
A unit with a `section.block.ritual` strip (steps in verse order, each with
`data-who`, `data-at` and a verse `<sup>`) or an empty `div.tabmap` gets a
map thumbnail in its header (tap: the full sheet with layers Holiness, Who may
enter, The camp) and an inset beside each strip. Tapping a step lights its
zone; a camp zone switches to the camp view. The plan is to scale from Exod
25-27 with positions the text omits marked schematic, and the sheet lists
every measurement with its verse. A book without `ritual` gets no map code,
CSS or data file. Markup and zone ids: `components-reference.md`.

**Laws (a book opts in with `"lawparallel"` in `components`, and/or
`"law_chips": true`).** `biblecore/laws.json` lists each law the Torah
restates: its passages in Bible order, each with a summary, stated
differences and the text's own reasons (a dating or source debate only in
`footnote`). `python -m biblecore.laws` checks it. A `lawparallel` box in a
law's unit names the law (`data-law`) and its own passage (`data-at`), copies
each row's difference and reason from the file, and fails the check on
anything the file doesn't hold. A law unit also writes two-sentence briefs in
its meta block, `lawbriefs[]` (`{law, ref, brief}`); `canon` merges them into
`data/canon.json`, and the hub publishes them as `data/law-briefs.json`.
A narrative book with `"law_chips": true` fetches that file from the hub at
page load and puts a "Law behind this" chip on any `aside.echo` whose target
falls in a brief's range; hub unreachable → no chip. A new brief needs no
re-vendor, a new law does (the file is in the package). The hub's Laws page
lists every law with links to the units where built.

Two things came across from Matthew's time on it (0.9.0):
- **Overlay grouping.** book.json `"overlay"` names a secondary grouping kind
  (Matthew: `"discourse"`). The shell draws it over the primary one: a
  ◆ mark on unit chips, brackets under the book map, a key row, and a line in
  each unit's placement ("◆ Discourse I: Sermon on the Mount (1 of 3)").
- **Toggle components.** A verse-aside component may declare `"toggle"` in its
  component.json. Instead of joining the shared * note, it gets its own chip:
  `compare` (✦, several on one verse share a "Rendering" panel) and
  `synoptic` (✧, one chip per parallel).

**Side by side (a book sets `"component_labels": {"synoptic": "Side by side"}`).**
The `synoptic` box, with its chip reading "Side by side"; the other account
can be a Hebrew-Bible passage (Deut 1:9–18 beside Exod 18:13–26).

**Calendar (`"calendar"` in `components`).** `biblecore/calendar.json` lists
each appointed time with the passages that date it and what each requires.
`python -m biblecore.calendar` checks it. An `aside.calendar` box names a feast
(`data-feast`) or `all` and copies each row's date and requirements from the
file. A new feast is a core release.

**Overlay with verse ranges (`"overlay"` plus `"overlay_note"`).** The note
shows in the book map's key. Each `groupings[]` entry of the overlay kind may
add `verses` (`{"4": "4:26", "30": "30:19; 31:28"}`, per member unit, inside
its passage); members may be non-contiguous, and a unit may be in several
entries. The map brackets the units, and a unit's placement line reads
"◆ Treaty: witnesses (4:26)". `python -m biblecore validate` checks the shape.
Without `overlay_note` the overlay behaves as before.

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

**Mirrors (0.29.0).** A book may read another book backwards (Numbers 10-24
against Exodus 5-18, Carmen Imes's reading). `book.json` `mirrors` names the
other book (`with`, an OSHB id; Hebrew books only for now) and a policy file
in `data/` (`file`) of pairs: each has a `here` span and an `other` span in
English numbering, a `tier` (`chiasm` with a `pos`, or `echo`), Lane's
`strength` (3 = shared words, 2 = same story beat, 1 = thematic), and the
`shared` words with the verse each is found in on both sides. The core
checks the file against both corpora (`biblecore/mirror.py`, run by `build`
and `biblecore test`; the second book is read by `corpus/oshb.load_other_words`
through the same `VerseMap.xml` conversion): every ref resolves, every shared
lemma is in both passages, and a strength-3 pair has a passing shared entry. A
claim that fails is an error and never a quiet downgrade. Nesting, overlap, an
order that does not reverse and pairs wider than a unit are reported, not
failed. The unit pack gets a mirror section; the `mirror` component is the
box (the build writes its strength dots from the file); a unit's `mirror[]`
meta key proposes pairs, which land in `out/mirror-delta.json` and reach the
file only through `python -m biblecore mirror keep`, as `status: kept`.
Nothing in core names a particular pair of books. The data file shape is in
`docs/data-shapes.md`.
