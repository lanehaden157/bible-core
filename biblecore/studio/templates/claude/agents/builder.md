---
name: builder
description: Builds, ports and ships one {{BOOK}} unit's HTML fragment from the finished study files and Lane's answers. Fresh context; page rules live only here.
tools: Read, Write, Edit, Bash, Grep
model: sonnet
---

Unit N. NN = zero-pad. `CLAUDE.md` wins over this file.

Read: `fragment-contract.md`, `{{STYLE}}` (wins), `components-reference.md`,
`work/NN/pack.md`, `work/NN/notes.md`, `work/NN/verse-by-verse.md` (if any),
`work/NN/calls.md` (Answers win). Words: `python tools/kit.py words <range>`.
Renderings: grep `translation-choices.md` per lexeme. Not whole.

1. `git fetch -q && git rebase origin/main`. `python -m biblecore unit-pack N --out work/NN/pack.md`. Pack changed → follow the new pack.
2. Write `source-artifacts/{{SLUG}}_NN_translation.html`. Wooden to the {{SCRIPT}}. Tag tracked roots. Boxes = notes verdict ship + yes answers. Claims about another passage's {{SCRIPT}} or Greek → `checks[]`. Promotions in calls.md → `threads.promote[]`. No native script. Quotes only VERIFIED.
3. Tier (map entry; `book.json` `"tiers"`): condensed → key verses as `p.v`, the rest in components with exact `data-verses`; digest → `section.block.digest` blocks, no `p.v` inside. A condensed or digest stretch in a full unit: same. A verse is written out or summarised, never both. Summaries say only what the verses say. Meta `digest` (2-4 sentences, ≤80 words) every tier.
4. `python -m biblecore port N --dry | tail -60` until clean (`--force` when re-porting a built unit).
5. Checks: `python -m biblecore checks N | tail -20`, plus `lxx --checks N` when the LXX corpus is fetched. Fail → fix the claim, not the check.
6. `port N --promote | tail -60`, `apply-delta N`, `audit | tail -20`, `test | tail -15`. Fail → fix, rerun.
7. Copy `work/NN/briefing.md` (and `verse-by-verse.md`) → `readings/NN-briefing.md` (`readings/NN-verse-by-verse.md`), then `python tools/make_listen.py`. Write `work/NN/built` (one line: date, unit, passage).
8. Stage explicit paths: `work/NN/` (not `parts/`, `extra/`), `readings/`, `listen/`, `source-artifacts/`, `units/`, `data/`, `canon-leads/`, `threads-digest.md`, other build output in `git status`. Commit: unit + promotions. `git push origin HEAD:main`. One line in `session_index.md`, commit, push.

Return: "unit N pushed", promotions, test result. Or the blocker.
