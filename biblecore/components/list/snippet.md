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

- Inside a `section.block`, in line with the text (not hoisted with the structure blocks). First row = header row of `<th>`; every row has the same number of cells.
- Last column = the number, right-aligned. A total the text gives → `<tfoot>`.
- Cells may carry `data-root` spans, tracked threads too. Inside a `data-verses` table these are summary tags: colour only, no `data-w`; audit counts the declared verses as covered.
- `data-verses` = exactly the verses the table replaces, when it condenses a repeated formula. Say so in the pericope's gloss.

**Verified =** every number and name comes from the verses. Table condenses the text, adds nothing.
