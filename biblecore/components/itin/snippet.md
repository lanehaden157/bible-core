```html
<section class="block">
  <h2>From Rameses to the plains of Moav <span class="cap">· 33:5–49</span></h2>
  <div class="itin" data-verses="33:5–49">
    <span class="stop">Rameses <sup>33:5</sup></span><span class="arr">→</span>
    <span class="stop">Sukkot <sup>33:5</sup></span><span class="arr">→</span>
    <span class="stop">Etam <sup>33:6</sup></span>
  </div>
</section>
```

- Inside a `section.block`, in line with the text.
- Direct children: only `span.stop` and `span.arr` ("→"), alternating, starting and ending with a stop.
- A stop may carry a `data-root` span (a tracked place name) and a `<sup>` with its verse (`C:V`), or a range (`C:V–V`) when the stop is a whole scene.
- `data-verses` on the `div.itin` when the chips replace the verses (formulaic station list). Prose verses also written out → leave it off; chips are a summary. Tracked spans inside a `data-verses` block need no `data-w`.

**Verified =** stops and order come from the verses. A route the text doesn't give (a reconstruction) → a note, not the chips.
