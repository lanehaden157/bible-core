## compare — a rendering spotlight

A verse sibling (right after the verse's `<p class="v">`, like `.gloss`) that
sets the original beside this translation and others, with a note:

```html
<div class="compare">
  <div class="row"><span class="src">Greek (translit.)</span><span class="txt translit">…</span></div>
  <div class="row"><span class="src">This translation</span><span class="txt">“…”</span></div>
  <div class="row"><span class="src">NASB</span><span class="txt">“…”</span></div>
  <div class="row"><span class="src">Note</span><span class="txt">…</span></div>
</div>
```

Every `.row` starts with its `.src` label. The site hides it behind a ✦ chip
on the verse; several on one verse share one "✦ Rendering" panel. Use it for
a rendering choice worth arguing, not for every gloss.
