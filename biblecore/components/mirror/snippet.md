## mirror — the mirrored book's twin beside a verse

For a book with `mirrors` in `book.json`: verse sibling setting the unit's
passage beside its twin in the other book (Numbers 11 beside Exodus 18), with
the words the two share. The pairing is a scholar's reading, never a fact; say
"one reading" if the box needs qualifying. Link one sentence can carry =
`aside.echo`; same event told twice in one book family = `synoptic`;
unrelated earlier story = `story`.

```html
<aside class="mirror" data-anchor="11:14" data-pair="H" data-span="11:10–17">
  <h4><span class="par-title">The burden: too heavy … alone</span>
      <span class="par-ref">Exod 18:13–18</span>
      <span class="strength"></span></h4>
  <div class="row"><span class="src">Exod 18:18</span><span class="txt">… <span class="sh" data-ids="3515">heavy</span> … <span class="sh" data-ids="905">alone</span></span></div>
  <p class="take">What the mirror shows here.</p>
</aside>
```

- Follows the verse it bears on; `data-anchor` = that verse, inside the pair's
  side of this book. `data-span` optional.
- `data-pair` names a pair in the mirror data file (status `seed` or `kept`).
  **Boxes make no claim the data file doesn't hold:** `par-ref` lies inside
  the pair's twin passage, and every `span.sh` carries `data-ids` (Strong's,
  comma-separated) the pair lists under `shared`. Word the pair doesn't list
  → not highlighted.
- Leave `span.strength` empty: build writes the dots (and `data-n`) from the
  data file. Echo-tier pair has no strength span.
- One box per beat. A wide pair (several beats, several units) gets a box in
  each unit it touches: same `data-pair`, own `par-ref` inside the twin
  passage.
- Translate the twin in the unit's own voice: the unit pack's mirror section
  has the Hebrew word order, transliteration and Strong's numbers, with a
  gloss only where the book already has one. **Never raise a strength above
  what the shared words support.** Link the data file doesn't hold → no box;
  propose it in the meta block's `mirror[]`.
- Poetry twin (`poetry` in the pair) → header only: `par-title`, `par-ref`,
  `take`, no rows.
- `take` required: one or two sentences on what the mirror shows here.
- Transliteration only. No `data-root`, `class="r"` or `class="rl"` inside.
- Harvested into `data/canon.json` (an intertext row of kind `mirror` per
  reference in `par-ref`): don't repeat in `intertext[]`.
