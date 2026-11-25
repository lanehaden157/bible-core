---
name: unit
description: Do one {{BOOK}} unit: study it here (research, notes, briefing, verse by verse), fact-check, Lane's calls, then a builder session builds it. Use for "/unit N" or from /finish. Resumes where the unit stands.
---

# Unit N

You study; `fact-checker` checks; a `/build` session builds. NN = zero-pad. Files in
`work/NN/`. Where it stands: `python tools/unit_status.py N`; resume at the
first missing file. `CLAUDE.md` and `lens.md` win over this file. Run commands from the book root.
Runs on Sonnet: from Opus, `start_session` a Sonnet one with `/unit N`.

## 1. Read

- `python tools/lessons.py known`: mistakes this book has made. Don't repeat them.
- `python -m biblecore unit-pack N --out work/NN/pack.md`. Read. Ids, rulings, threads, leads, parallels: copy, never recall.
- `lens.md`. Unit's map entry (`{{MAP}}`): passage, tier, stretches.
- `python tools/kit.py words <range>`: English, each word's translit, lemma, gloss, parsing, LXX English. No native script in anything you write.
- Sources by rank (`kit.py sources` marks tiers; `book.json` `studio` sets them). Whole: `kit.py parts N`, Read all of `work/NN/parts/`. Voices: `kit.py keyverses N` lists candidates (thread opens and payoffs, pack word and phrase leads, verses a map bullet names; most signals first). Add or drop verses you know matter, then `kit.py extra N --key <verses>` and Read `work/NN/extra/`. Rest: `kit.py grep N term ...`, Read `work/NN/grep.md`; open a hit with `kit.py range`. Unopened → Source status.
- Targets: `kit.py bible <CODE> <range> [--lxx]` (WEB, or the LXX in English); `python -m biblecore lxx <Book> <C:V>` for a Hebrew book's Greek claims (the NT has no `lxx`). Web: voices the sources lack (`resources.md`).
- Other books' Hebrew (pack leads) is SHEET or English, and NT Greek is English: neither is VERIFIED.
- Long output → `| tail -40`. Scope doubt → a call, not a stop.

## 2. notes.md

Per scene: people, places, objects, earlier appearances; its shape + nearest same-shape passage (read it); same / different / does; later reuse (prophets, NT); pack leads. One row per link, dropped too.

| verse | target | kind | evidence | wording read | status | strength | verdict |
|---|---|---|---|---|---|---|---|

- kind: echo, story, parallel, intertext, type-scene, wordplay, other. evidence: shared words (translit, ids).
- status: VERIFIED (original's words read this unit), ENGLISH, SHEET (pack), SECONDHAND, RECALLED.
- strength: strong, possible, weak.
- verdict: ship (root echo, aside.echo, footnote or an enabled box kind), tentative, drop + why.

Also: thread opens/payoffs (draft the popover note), recurring untracked roots (pack ids + reach), notable single renderings (local root), missed tags (retro), claims about another passage's {{SCRIPT}} or Greek (→ checks), type-scenes (`canon-conventions.md` ids).

End: **Source status** (read / secondhand / unavailable, by source).

## 3. briefing.md, verse-by-verse.md

Read aloud: flowing prose, scene headings ok; no lists, tables, bold, digits (verse numbers, refs) or native script. Names spoken ("the book of Exodus"). Quotes only VERIFIED.

- Briefing: placement, background, genre, words to watch, tensions, earlier passages leaned on (name, don't tell). Orient, don't resolve. Full tier 600-900 words; condensed or digest 300-500, and no verse-by-verse.
- Verse by verse (full tier; skip stretches the map marks condensed or digest): depth. Scripture roots and canon trajectories first; then wordplay, structures, background, commentators in dialogue. A verse that reaches an earlier passage: tell it there (background, match, differ, what this book does). Tensions open. Devotion light.

## 4. Fact-check

`python tools/lint_study.py N`, fix what it lists. Then `fact-checker` agent, unit N. Unsettled → calls. Its tokens → `work/NN/cost.md`. Then `python tools/lessons.py report`: flagged `book` key → fix CLAUDE.md or lens.md now, then `resolve`; flagged `core`/`source` → name it in your last message. Commit `lessons.jsonl`.

## 5. calls.md

Decide all you can (pack rulings, strong boxes, promotions: book-wide bias, retrofit cost).

- `## Calls for Lane (N)`: numbered. Verse, 2-3 options, recommended first, one-line reason each. Only: provisional or unruled renderings, scope doubts, close-call promotions, unsettled fact-checks, tentative boxes (yes/no). An odd-looking ruling isn't a call. A call you can't decide: ask, don't guess; no answer yet → the unit waits at calls.
- `## Decided without Lane`: one line each, why. Lane audits.
- `## Answers`: empty till 6.

## 6. Ask

Lane away: `PushNotification` "Unit N: K calls ready", end turn. Here: AskUserQuestion, four per popup, recommended first. Answers → `## Answers`.

## 7. Build

Answers in. Unit N-1 unshipped (`unit_status`) → say so, end turn (builds go in unit order: N-1's promotions, threads and data feed this build; /finish resumes this one). Else `start_session` (`user_asked`, `use_worktree: false`, `fresh`, a Sonnet `model`, title `{{BOOK}} unit N build`, prompt `/build N`), link it, end turn.
