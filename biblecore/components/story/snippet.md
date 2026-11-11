## story — an earlier story beside a verse

Verse sibling for a *different, earlier* event with the same shape, told with
its background (Herod's feast beside Pharaoh's birthday feast). Same event in
another gospel, or Chronicles beside Kings = `synoptic`, never a story box.
Link one sentence can carry = `aside.echo`.

```html
<aside class="story" data-anchor="14:6" data-kind="type-scene" data-scene="royal-birthday-feast" data-strength="strong">
  <h4><span class="par-title">Pharaoh's birthday feast</span> <span class="par-ref">Gen 40:20–22</span></h4>
  <p class="par-story">Two to four plain sentences telling the earlier story.</p>
  <ul class="par-match"><li>what's the same</li><li>…</li></ul>
  <p class="par-diff">What's different.</p>
  <p class="par-does">What it does here: irony, reversal, identification, fulfilment, warning.</p>
  <p class="par-later">Later reuse, only if there is one.</p>
</aside>
```

- Follows the verse it bears on, or the last verse of the scene it covers;
  `data-anchor` = that verse. `data-span="14:3–12"` optional.
- `data-kind`: `type-scene`, `story`, `allusion`, `character` or `reuse`. A
  `type-scene` box also names it: `data-scene="<id>"`. Check the canon's
  type-scene list first; a new id is the book owner's call.
- `data-strength`: `strong` or `possible`. Ship a `possible` link when it's
  worth Lane's eye, worded as tentative. A weak link never ships as a story
  box: notes or a footnote.
- Required: `<h4>` with `par-title` and `par-ref`, then `par-story`,
  `par-diff`, `par-does`. **No box ships without a stated difference.**
  `par-ref` must include verses (`Exod 24:15–18`); a bare chapter list
  (`Exod 24; 34`) fails at build. `par-match`, `par-later` optional.
- Site supplies the labels (Same, Different, What it does, Later): don't
  write them. Each box hides behind its own ◈ chip ("Type scene" or "Earlier
  story").
- Transliteration only. No `data-root`, `class="r"` or `class="rl"` inside
  (the occurrence scanner counts every `data-root`). Box rests on shared
  words → put them in the box as evidence; no `aside.echo` for the same
  link. Argument about the link → footnote.
- Harvested into `data/canon.json` (an intertext row per reference, a
  type-scene row for `data-scene`): don't repeat in `intertext[]` or
  `typescenes[]`.
