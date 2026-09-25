```html
<div class="poem">
  <div class="v"><span class="n">24</span><span class="l">May Yahweh <span class="r" data-root="bless">bless</span> you</span><span class="l in">and keep you.</span></div>
  <span class="gloss">Three lines, each longer than the last …</span>
  <div class="v"><span class="n">25</span><span class="l">May Yahweh make his face shine on you</span><span class="l in">and be gracious to you.<sup class="en"><a href="#n4">4</a></sup></span></div>
</div>
```

- Poetry stays in **ordinary verse blocks** (`div.v`, one per verse), so tagging, `data-w`, the audit and verse links work exactly as in prose. The poem only sets the text in lines.
- Every word of a poem verse sits inside a `span.l` line; only the verse number and whitespace sit outside. Put the endnote marker at the end of the last line.
- Add `class="l in"` for an indented, continuing line (a second or third colon).
- Glosses and asides go between verses inside the `div.poem`, as they do in prose.
- `data-pair="A"` / `"B"` on lines is optional. Use it only when the parallelism is the point of a note.
- A `div.poem` never sits inside a `section.block`, and poems don't nest.
- A short poetic inset inside prose (a song, an oracle, a blessing) gets its own `div.poem` between the prose verses.

**What counts as verified:** line breaks follow the Masoretic accents (the major disjunctives, ʾatnaḥ first) or an established critical layout, not the English rhythm. Say which in a note when a break is debatable.
