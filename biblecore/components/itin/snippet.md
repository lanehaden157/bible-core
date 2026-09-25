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

- It goes inside a `section.block`, and it stays in line with the text.
- Its direct children are only `span.stop` and `span.arr` ("→"), alternating, starting and ending with a stop.
- A stop may carry a `data-root` span (a place name you're tracking) and a `<sup>` with its verse (`C:V`).
- `data-verses` goes on the `div.itin` when the chips replace the verses (a formulaic station list). When the prose verses are also written out, leave it off and the chips are a summary.

**What counts as verified:** the stops and their order come from the verses. A route the text doesn't give (a scholar's reconstruction) belongs in a note, not in the chips.
