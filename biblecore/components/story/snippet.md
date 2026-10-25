## story — an earlier story beside a verse

A verse sibling for a *different, earlier* event with the same shape, told
with its background: Herod's feast beside Pharaoh's birthday feast, Elisha's
loaves beside the wilderness meal. The same event told by another gospel (or
Chronicles beside Kings) is a `synoptic`, never a story box. A link one
sentence can carry is an `aside.echo`.

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

- It follows the verse it bears on, or the last verse of the scene it covers;
  `data-anchor` must match that verse. `data-span="14:3–12"` is optional.
- `data-kind`: `type-scene`, `story`, `allusion`, `character` or `reuse`. A
  `type-scene` box also names its type-scene: `data-scene="<id>"`. Check the
  canon's type-scene list first; a new id is the book owner's call.
- `data-strength`: `strong` or `possible`. A weak link never ships as a story
  box; it stays in the notes or becomes a footnote.
- Required: the `<h4>` with `par-title` and `par-ref`, then `par-story`,
  `par-diff` and `par-does`. **No box ships without a stated difference.**
  `par-match` and `par-later` are optional.
- The site supplies the labels (Same, Different, What it does, Later), so
  don't write them. It hides each box behind its own ◈ chip, labelled
  "Type scene" for a type-scene and "Earlier story" otherwise.
- Transliteration only, and no `data-root`, `class="r"` or `class="rl"`
  inside (the occurrence scanner counts every `data-root`). When the box
  rests on shared words, put them in the box as evidence; don't also write
  an `aside.echo` for the same link. An argument about the link goes in a
  footnote; the box says only what the parallel is.
- Story boxes are harvested into `data/canon.json` (an intertext row per
  reference, a type-scene row for `data-scene`), so don't repeat them in
  `intertext[]` or `typescenes[]`.
