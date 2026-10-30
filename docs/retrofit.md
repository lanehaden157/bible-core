# Retrofit files

A book has two retrofit specs in `retrofit/`, both applied to `units/*.html`
by `python -m biblecore retrofit` (the build runs it every time; every op is
idempotent):

- `retrofit-tags.json` is **hand-authored**. Put audit gaps, one-off tag
  fixes and wording fixes here.
- `retro-tags.json` is **generated** by `port` from later units'
  `threads.retro[]`. Don't hand-edit it; fix the source artifact and port again.

Both use the same ops (`add`, `retag`, `unwrap`, `retag_word`, `untag_word`,
`text`, `strip_span`) and are merged at load time.

## Promoting a thread

1. In the unit that promotes, put the thread in `threads.promote[]` (`root`
   is optional and defaults to `id`) and, for earlier units, `threads.retro[]`
   entries naming the new id. The retro check accepts a root this unit
   promotes.
2. `port N` writes the thread delta. `apply-delta N` then creates the
   `threads.json` entry (colour assigned, status open, tagged true) and the
   `roots.json` entry, plus any payoffs.
3. `data-w M` for each retrofit unit, then `build` (it audits).
4. The audit prints each remaining gap as a ready `add` entry for
   `retrofit-tags.json`. `text` is filled when a rendering this root already
   has elsewhere sits free in the verse; otherwise it reads `"???"`. The corpus
   has no English-to-Greek alignment, so the audit can't guess further: fill
   those by hand from the verse.

An `add` is a no-op ("already tagged") when its text already sits inside a
span of the same root, including as part of a longer span ("trip" inside
"trip them up").
