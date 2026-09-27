## compare — a rendering spotlight

A verse sibling (right after the verse's `<p class="v">`, like `.gloss`) that
sets the original beside this translation and others, with a note:

```html
<span class="compare">
  <span class="row"><span class="src">Greek</span> <span class="translit">…</span></span>
  <span class="row"><span class="src">This translation</span> “…”</span>
  <span class="row"><span class="src">NASB</span> “…”</span>
  <span class="row"><span class="src">Note</span> …</span>
</span>
```

Every `.row` starts with its `.src` label. The site hides it behind a ✦ chip
on the verse; several on one verse share one "✦ Rendering" panel. Use it for
a rendering choice worth arguing, not for every gloss.
