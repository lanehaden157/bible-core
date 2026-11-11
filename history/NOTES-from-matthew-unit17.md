# Notes from Matthew unit 17 (2026-10-29)

1. **Story par-ref**: `components/story/__init__.py` requires a chapter:verse ref in `.par-ref`; a chat-built source with "Exod 24; 34" fails only at `build`. Make `port` run the component validators before writing, and add a line to the chat-side template: "par-ref must include verses, e.g. Exod 24:15–18".
2. **Half-written port**: a failed validate leaves `port --force` output on disk, and the "ported. view in the browser" message still prints. Validate first or roll back.
3. **`apply-delta N`**: parse "add to `X`.payoffs: {...}" lines in `out/thread-delta-N.md` into `data/threads.json` (skip duplicates, keep formatting). Currently a hand-written script.
4. **Windows stdout**: printing Greek crashes under cp1252; reconfigure stdout to UTF-8 in the CLI entry point.
