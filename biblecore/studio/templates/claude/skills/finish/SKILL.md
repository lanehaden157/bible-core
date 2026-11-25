---
name: finish
description: Conductor for many {{BOOK}} units. One session per unit, about three studying at once, builds in unit order. Use for "finish {{BOOK}}", "do units 5-9", or "where do units stand".
---

1. `python tools/unit_status.py`.
2. Each unit in range not started, in order: `start_session` (`initiation: "user_asked"`, `use_worktree: true`, `context: "fresh"`, `model` a Sonnet id, title `{{BOOK}} unit N`, prompt `/unit N`). Max three before calls; the next starts when one reaches calls.
3. Unit session reports:
   - at calls → tell Lane which units wait, links, earliest first (early answers can change later units);
   - shipped → `SendMessage` the next unit's session to resume its build if it waited.
4. After each shipped unit: `python tools/lessons.py report`. Flagged `core`/`source` key → tell Lane, offer a session (report lines as brief); flagged `book` key → fix it before the next unit.
5. Never answer Lane's calls. Never merge unit branches by hand.
