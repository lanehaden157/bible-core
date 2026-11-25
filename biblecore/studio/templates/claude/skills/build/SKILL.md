---
name: build
description: Build and ship one {{BOOK}} unit from its finished study files and Lane's answers. Use for "/build N"; the unit session starts it.
---

Unit N. First `python tools/lessons.py known`. Read `.claude/agents/builder.md` and follow it as written, in this session (no subagent). Study files are in `work/NN/`; `calls.md` Answers win. Blockers → `lessons.py add --stage build` (builder.md has the form).
After the unit ships: `python tools/lessons.py report`. Name any flagged `core` or `source` key in your final message; a flagged `book` key → fix CLAUDE.md or lens.md, then `resolve`.
Report: "unit N pushed", promotions, test result, or the blocker.
