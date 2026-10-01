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

## G. When core moves (any session, as needed)
21. **Claude, in bible-core**: `tools/release.py X.Y.Z --note "..."`, then `tools/core_sync.py --all` (vendor, build, test, commit per book). Push after your OK; each push runs CI.
22. **Claude, in a book session**: occasionally `python ../bible-core/tools/core_diff.py . --template`; take what fits, then `--set-base`.
