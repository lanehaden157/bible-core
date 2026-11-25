---
name: unit
description: Do one {{BOOK}} unit: study it here (research, notes, briefing, verse by verse), fact-check, Lane's calls, then hand the build to the builder agent. Use for "do unit N", "/unit N", or from the finish conductor. Resumes where the unit stands.
---

# Unit N

You study. `fact-checker` checks. `builder` builds. NN = zero-pad. Files in
`work/NN/`. Where it stands: `python tools/unit_status.py N`; resume at the
first missing file. `CLAUDE.md` and `lens.md` win over this file. Book commands: `cd` to the book's root first.
Runs on Sonnet: from an Opus session, `start_session` a Sonnet one with `/unit N`.

## 1. Read

- `python tools/lessons.py known`: mistakes this book has made. Don't repeat them.
- `python -m biblecore unit-pack N --out work/NN/pack.md`. Read. Ids, rulings, threads, leads, parallels: copy, never recall.
- `lens.md`. Unit's map entry (`{{MAP}}`): passage, tier, stretches.
- `python tools/kit.py words <range>`: English, each word's transliteration, lemma, gloss, parsing, LXX English. Native script stays out of everything you write.
- `python tools/kit.py parts N`, Read all `work/NN/parts/` (the sources read whole).
- `python tools/kit.py extra N`, Read `work/NN/extra/` (every other source over the unit). Key verses' sections first (`grep -n '^## '`), then the rest in pieces. Name unopened ones in **Source status**.
- Targets: `kit.py bible <CODE> <range> [--lxx]`; `python -m biblecore lxx <Book> <C:V>`.
- Web: voices the sources lack (`resources.md`).
- Other books' Hebrew (pack leads) and the NT Greek are never VERIFIED.
- Long output → `| tail -40`. Scope doubt → a call.

## 2. notes.md

Per scene: people, places, objects, earlier appearances; its shape + nearest earlier same-shape passage (read the target); same / different / does; later reuse (prophets, NT); pack leads. One row per link, dropped too.

| verse | target | kind | evidence | wording read | status | strength | verdict |
|---|---|---|---|---|---|---|---|

- kind: echo, story, parallel, intertext, type-scene, wordplay, other.
- evidence: shared words (translit, lemma ids).
- status: VERIFIED (original's words read this unit), ENGLISH, SHEET (pack), SECONDHAND, RECALLED.
- strength: strong, possible, weak.
- verdict: ship (root echo / aside.echo / footnote / box kind the book enables), tentative, drop + why.

Also note: thread opens/payoffs (draft the popover note), recurring untracked roots (ids + reach from the pack), single notable renderings (local root), missed tags (retro), claims about another passage's {{SCRIPT}} or Greek (→ checks), type-scenes (ids from `canon-conventions.md`).

End: **Source status** (read / secondhand / unavailable, by source).

## 3. briefing.md, verse-by-verse.md

Read aloud. Flowing prose; scene headings ok. No bullets, bold, tables, verse numbers, refs, native script. Names spoken ("the book of Exodus"). Quotes only VERIFIED.

- Briefing: placement, background, genre, words to watch, tensions, earlier passages leaned on (name only). Orient; don't resolve. Full tier 600-900 words; condensed or digest 300-500, and no verse-by-verse.
- Verse by verse (full tier; skip stretches the map marks condensed or digest): depth. Scripture roots and canon trajectories first; then wordplay, structures, background, commentators in dialogue. Verse reaches an earlier passage → tell it there: background, match, differ, what this book does. Tensions open.

## 4. Fact-check

`fact-checker` agent, unit N. Unsettled → calls. Its token use → `work/NN/cost.md`. Then `python tools/lessons.py report`: flagged `book` key → fix CLAUDE.md or lens.md now, then `resolve`; flagged `core`/`source` → name it in your last message. Commit `lessons.jsonl`.

## 5. calls.md

Decide all you can: pack-ruled renderings, strong boxes, promotions (book-wide bias, retrofit cost).

- `## Calls for Lane (N)`: numbered. Verse, 2-3 options, recommended first, one-line reason each. Only: provisional renderings, new renderings the pack doesn't rule, scope doubts, close-call promotions, unsettled fact-checks, tentative boxes (yes/no). 
- `## Decided without Lane`: one line each, why. Lane audits.
- `## Answers`: empty till 6.

## 6. Ask

Lane absent: `PushNotification` "Unit N: K calls ready", end turn. Lane here: AskUserQuestion, four per popup, recommended first. Answers → `## Answers`.

## 7. Build

Unit N-1 not shipped (`unit_status`) → say so, end turn. Else `builder` agent, unit N. Relay its result.
