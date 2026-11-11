## mirror — the mirrored book's twin beside a verse

For a book that declares a mirror in `book.json` (`mirrors`): a verse sibling
that sets the unit's passage beside its twin in the other book (Numbers 11
beside Exodus 18), with the words the two share. The pairing is a scholar's
reading, never a fact; say "one reading" in the prose if the box needs
qualifying. A link one sentence can carry is an `aside.echo`; the same event
told twice in the same book family is a `synoptic`; an unrelated earlier story
is a `story`.

```html
<aside class="mirror" data-anchor="11:14" data-pair="H" data-span="11:10–17">
  <h4><span class="par-title">The burden: too heavy … alone</span>
      <span class="par-ref">Exod 18:13–18</span>
      <span class="strength"></span></h4>
  <div class="row"><span class="src">Exod 18:18</span><span class="txt">… <span class="sh" data-ids="3515">heavy</span> … <span class="sh" data-ids="905">alone</span></span></div>
  <p class="take">What the mirror shows here.</p>
</aside>
```

- It follows the verse it bears on; `data-anchor` must match that verse and
  sit inside the pair's side of this book. `data-span` is optional.
- `data-pair` names a pair in the book's mirror data file (status `seed` or
  `kept`). **Boxes make no claim the data file doesn't hold:** the
  `par-ref` must lie inside the pair's twin passage, and every `span.sh`
  carries `data-ids` (Strong's, comma-separated) that the pair lists under
  `shared`. A word the pair doesn't list is not highlighted.
- Leave `span.strength` empty. The build writes the dots (and `data-n`) from
  the data file, so changing a strength there changes every box. An echo-tier
  pair has no strength span.
- One box per beat. A wide pair (several beats, several units) gets a box in
  each unit it touches, all with the same `data-pair`, each with its own
  `par-ref` inside the pair's twin passage.
- Translate the twin in the unit's own voice: the unit pack's mirror section
  has the Hebrew word order, transliteration and Strong's numbers, with a
  gloss only where the book already has one. **Never raise a strength above
  what the shared words support**, and don't ship a box for a link the data
  file does not hold; propose it in the meta block's `mirror[]` instead.
- A poetry twin (`poetry` in the pair) gets the header only: `par-title`,
  `par-ref`, `take`, no rows.
- `take` is required: one or two sentences on what the mirror shows here.
- Transliteration only, and no `data-root`, `class="r"` or `class="rl"`
  inside (the occurrence scanner counts every `data-root`).
- Mirror boxes are harvested into `data/canon.json` (an intertext row of kind
  `mirror` per reference in `par-ref`), so don't repeat them in `intertext[]`.
