## ritual — a rite as steps, tied to the map

A strip of steps in the order the verses give, each placed on the tabernacle
map. Enabling `ritual` also gives the unit a map thumbnail in its header (tap:
the full sheet) and an inset beside each strip; tapping a step lights its zone.

```html
<section class="block ritual" data-verses="1:3–9">
  <h2>The going up offering <span class="cap">· 1:3–9</span></h2>
  <ol class="steps">
    <li data-who="offerer" data-at="entrance">Brings a male without blemish. <sup>1:3</sup></li>
    <li data-who="priest" data-at="altar">Dashes the blood around the altar. <sup>1:5</sup></li>
  </ol>
</section>
<div class="tabmap" data-layer="camp"></div>
```

- `data-who`: `offerer`, `priest`, `high-priest`, `people`. `data-at`: a zone id,
  `outside-camp camp entrance court altar basin holy-place veil most-holy`
  (`veil` is drawn and labelled "curtain"; `most-holy` is the holy of holies).
- Every step carries a `<sup>` verse, and the order is the verses' order.
  Where the text leaves the place or the doer unsaid, pick the zone it
  implies and say so in the unit's notes.
- `data-verses` (on the section) only when the strip replaces those verses.
- `div.tabmap` (empty) puts the map in a unit with no strip: `data-layer`
  `holy` | `enter` | `camp`, `data-at` to light a zone.
- Labels follow `translation-choices.md`; the map's are already set.
