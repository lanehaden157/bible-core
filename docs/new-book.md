# Starting a new book: checklist

**Lane** = you; **Claude** = Claude Code. The steps around `tools/new_book.py` (ARCHITECTURE.md §8), from picking the book to the unit loop. Written by the 2026-09 structural audit; keep it current when the tools change. `python -m biblecore book` in the book shows where it stands at any point.

## A. Before you start
1. **Lane**: pick the book. Check that `bible-core/biblecore/web/themes.json` has its accent and emblem (21 books do). If not, tell Claude the colours you want.
2. **Lane**: make sure `gh auth status` is logged in on this machine (needed for `--github`).
3. **Lane**: start a Claude Code session in `bible-core` and ask it to set up the book. Check that no other session is mid-release.

## B. Repo and site (Claude)
4. **Claude**: `git status` clean in bible-core, tests green (locally, and the latest bible-core Actions run).
5. **Claude**: `python tools/new_book.py ../<Book> --book <Book> --osis <OSIS> --github` (an NT book adds `--language greek`). In one command:
    - template copied with its placeholders filled (`book.json` `core` + `template` base), and its language blocks resolved (the Greek wording for an NT book)
    - core vendored, lexicon copied (Strong's, or the MorphGNT lexicon for Greek)
    - the corpus: npm (morphhb) for Hebrew; for Greek, `python -m biblecore fetch` (MorphGNT + LXX, pinned, every file sha1-checked, git-ignored), then `corpus`
    - first build, which writes the app shell and generated css
    - first commit, the public GitHub repo, Pages and the first sync (core's default sync set; no list to write)
    - the book's `canon/books.json` row (site, repo, kind `core`)
    - the CI workflow (`.github/workflows/tests.yml`, runs `biblecore test` on every push)
6. **Claude**: check the first push's Tests run is green (`gh run list -R <owner>/<slug>`).
7. **Claude**: record the corpus counts in the book's CLAUDE.md "Corpus" section, and flag anything to check against a printed edition (BHS for Hebrew, SBLGNT for Greek). For Greek, also record the MorphGNT pin and the `lexicon: N of N lemmas have a gloss` line `corpus` prints, and flag any lemma without one. A `fetch` sha1 failure is a stop, not a warning.
8. **Claude**: commit the `canon/books.json` row in bible-core; push when you OK it. The hub's daily rebuild clones the book from that row (no workflow edit).

## C. Claude.ai project (Lane)
9. **Lane**: create the claude.ai Project "<Book> Study".
10. **Lane**: connect GitHub to the project and point it at the new repo's `project-side/synced/` folder.
11. **Lane**: upload the commentaries (PDFs) to the project's knowledge. They never go in the repo. Send Claude the list: author, title, edition, file name.

## D. Book documents (Claude drafts, Lane approves)
12. **Claude**: fill `resources.md` from your list, and draft the ✎ sections of the style reference and `CHAT_SIDE_INSTRUCTIONS.md` (lens, genre cautions). Mark them tentative. A book-only synced file goes in `book.json` `sync.extra`. Run `python -m biblecore sync` once you OK the push.
13. **Lane**: paste `CHAT_SIDE_INSTRUCTIONS.md` into the project's instruction field, then tell Claude, who runs `sync-check --mark-pasted`. `biblecore book` and every build say when it needs a re-paste.

## E. Unit map
14. **Lane (chat side)**: first project conversation. Compile the resources and produce the literary unit map, using the Overview table format in style ref §9.
15. **Lane**: hand the map to Claude Code (drop it in the book folder as `<slug>-literary-unit-map.md`; core's default sync set already covers that name).
16. **Claude**: `python -m biblecore units-from-map --kinds <outer>,<inner>`, which writes unit 1's canon leads. Then build, `biblecore test`, commit explicit paths, and sync after your OK.

## F. Each unit (the loop)
17. **Lane (chat side)**: the four passes for unit N, then save the artifact as `source-artifacts/<slug>_NN_translation.html` in the repo.
18. **Claude**:
    - `port N`
    - the porter's questions go to you as popups
    - promotions, `colour`, `data-w`; what `data-w` can't decide and the port's coverage gaps go in `retrofit/retrofit-tags.json` (the recipe is in the book's CLAUDE.md)
    - `build`, `audit`, `test` (its `words` check re-reads the corpus and checks the interlinear data)
    - browser check
    - commit explicit paths (never hand-edit `index.html`, `app/` or the generated css; a shell change goes into bible-core)
    - after your OK: push and `sync`
    - the push runs the book's Tests workflow; a failure emails you
19. **Lane**: optional. Press "Run workflow" on the hub repo's Actions tab, or wait for the daily rebuild.
20. **Claude**: session files (`session_index.md`, `improvements_log.md`, summary). Record anything the unit taught about core as a proposed core change, not a book-only patch.

## NT books: things worth knowing first
Learned from porting copies of Matthew's units 9–14 into a scratch Greek book (Greek-in-core pass 2, 2026-10-01; `../greek-proof/README.md`). Strong suggestions, not rules; revise them once a real NT book has shipped a few units.
- **Palette, before unit 1.** A Gospel tracks something like 80 threads. The template's 65-colour starter well runs out of colours at ΔE 10 long before that, so give the book its own larger well at setup (step 5), not halfway through: `python tools/make_well.py ../<Book> --de 7` writes `data/palette.json` (about 124 colours at ΔE 7; ΔE 10 holds only ~60), and `"checks": {"colour_de_min": 7}` in `book.json` tells validation and the port the same spacing. A book that already shipped units can re-assign their colours from the new well with `tools/recolour.py` (colours only).
- **Block-formatted passages.** A prayer, hymn or long quotation set as one block should carry `data-verses="C:V–V"` naming the verses it holds. Then the audit counts those verses as covered and the interlinear puts their words right after the block. Without it, the verses look missing. The Lord's Prayer case is still untested on real data; the first one is worth a browser check (interlinear on, jump to a verse inside the block).
- **Artifacts to the template contract.** Matthew's older units tripped the porter on: a missing `threads.retro` list, Greek-script `stems` on candidates, a unit with no colour key, an aside anchored to the wrong verse, and itinerary `<sup>`s holding labels. A template-shaped artifact avoids all of these, so if the chat side drifts toward Matthew's habits, point it back at the style reference.
- **Phrase threads.** A title like *son of David* is a phrase thread: the candidate can propose `"seq": ["huios", "dauid"]` and the thread delta previews it like `ids`.
- **Chapter seams.** Units that cross a chapter can label the first verse `11:1`. Retrofit entries and gap stubs then name verses `"C:V"`.
- **English phrasal verbs.** Expect `data-w` to ask for eyes where one Greek word is two English spans ("hand … over"). The retrofit recipe in the book's CLAUDE.md covers it.
- **Itineraries** in a Gospel move by scene: a stop's `<sup>` may be a range (`12:1–8`).
- **A worked example of the loop.** `../greek-proof/replay.py` runs port, promotions, delta, `data-w`, retrofit, build, audit and test end to end. It's useful as a reference for the commands in order.

## G. When core moves (any session, as needed)
21. **Claude, in bible-core**: `tools/release.py X.Y.Z --note "..."`, then `tools/core_sync.py --all` (vendor, build, test, commit per book). Push after your OK; each push runs CI.
22. **Claude, in a book session**: occasionally `python ../bible-core/tools/core_diff.py . --template`; take what fits, then `--set-base`.
