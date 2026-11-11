# bible-core versions

One line per release; `tools/release.py` appends. History, not instructions.

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
- 0.16.0: Interlinear: verse-number toggle, original script (data/script/), Plain/Notes/Original mode pill, restyled settings
- 0.17.0: Earlier-story boxes (aside.story, labelled chips, canon harvest), research pass before the verse-by-verse in the workflow, Greek noun sweep on the leads sheet, no synoptic cap
- 0.18.0: Two-chat workflow: research chat writes a handoff (canon/handoff-template.md), fresh build chat does pass 4; unit meta gains checks[] and threads.promote[]; questions[] limited to Lane-only calls
- 0.19.0: lxx command (verse lemmas, --expect, --checks runs a unit's checks[], '!lemma' = absent); audit prints ready retrofit add JSON with candidate text; port --answers FILE; biblecore test notes CRLF policy files
- 0.20.0: Calls for Lane: one handoff section, build chat asks every open call by popup before drafting, handoff-check lint
- 0.21.0: port validates the fragment before writing (--write-invalid to override); apply-delta N applies a thread delta's ready payoffs/opens; story par-ref needs verses; UTF-8 stderr
- 0.22.0: Instruction trim: leaner workflow, handoff template and digest; compare snippet uses div
- 0.22.1: biblecore test: warn-only size budget for instruction files
- 0.23.0: promote[] and retro[] work in one unit (retro accepts the unit's own promotions), root defaults to id, apply-delta creates promoted threads and roots, retro add skips text inside a same-root span, lxx --checks skips NT refs, docs/retrofit.md
- 0.23.1: handoff template: promotion root optional (defaults to id), ASCII slug
- 0.23.2: chat access: field block for reaching synced files, wording no longer assumes a folder or a tool name
- 0.24.0: consistency audit: workflow precedence ladder + single rules (questions, passes, box list, promotion, citing, script, names), handoff Decisions section and per-book box kinds, warn-only logs check in biblecore test
- 0.25.0: instruction-field paste tracking removed: no --mark-pasted, no PASTE BY HAND warning, no field line in book; Lane pastes when told
- 0.26.0: Research leans open: thin-sourced links are 'possible' and flagged tentative to Lane, not dropped (workflow, story snippet, chat-side lens template)
- 0.27.0: Research accuracy: unit-pack, checks, promote.complete, opener audit warning, handoff-check extended, three-chat workflow and ledger template
- 0.28.0: Three chats per unit always (table of passes, which-chat-am-I rule), Asking Lane timing (judgment calls on the box list, blockers only in chat); light-form promotions completed before the port overlay; Joshua test fixtures caught up
- 0.29.0: Mirror: book.json mirrors + a policy file of pairs (shared words verified against both corpora, strength 3 needs evidence); second-book reader, unit-pack mirror section, mirror component and canon kind, mirror[] proposals (out/mirror-delta.json, mirror keep|decline)
- 0.29.1: python -m biblecore mirror (the command was missing from the 0.29.0 registry)
