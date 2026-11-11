```html
<div class="poem">
  <div class="v"><span class="n">24</span><span class="l">May Yahweh <span class="r" data-root="bless">bless</span> you</span><span class="l in">and keep you.</span></div>
  <span class="gloss">Three lines, each longer than the last …</span>
  <div class="v"><span class="n">25</span><span class="l">May Yahweh make his face shine on you</span><span class="l in">and be gracious to you.<sup class="en"><a href="#n4">4</a></sup></span></div>
</div>
```

- Poetry stays in **ordinary verse blocks** (`div.v`, one per verse): tagging, `data-w`, audit and verse links work as in prose. The poem only sets lines.
- Every word of a poem verse sits inside a `span.l`; only verse number and whitespace outside. Endnote marker at the end of the last line.
- `class="l in"` = indented, continuing line (second or third colon).
- Glosses and asides go between verses inside the `div.poem`, as in prose.
- `data-pair="A"` / `"B"` on lines: optional, only when the parallelism is the point of a note.
- A `div.poem` never sits inside a `section.block`; poems don't nest.
- Short poetic inset in prose (song, oracle, blessing) → its own `div.poem` between the prose verses.

**Verified =** line breaks follow the Masoretic accents (major disjunctives, ʾatnaḥ first) or an established critical layout, not English rhythm. Debatable break → say which in a note.
