```html
<section class="block">
  <h2>The first accounting <span class="cap">· 1:20–46</span></h2>
  <table class="list" data-verses="1:20–43">
    <thead><tr><th>Tribe</th><th>Counted</th></tr></thead>
    <tbody><tr><td>Reuven</td><td>46,500</td></tr></tbody>
    <tfoot><tr><td>All Israel</td><td>603,550</td></tr></tfoot>
  </table>
</section>
```

- It goes inside a `section.block`. Its first row is a header row of `<th>`, and every row has the same number of cells.
- The last column is the number, and it's right-aligned.
- A total the text itself gives goes in `<tfoot>`.
- It stays in line with the text; it isn't hoisted to the top with the structure blocks.
- Cells may carry `data-root` spans.
- `data-verses` names exactly the verses the table replaces, when it condenses a repeated formula. Say so in the pericope's gloss.

**What counts as verified:** every number and name comes from the verses. The table condenses the text; it doesn't add to it.
