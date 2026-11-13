## calendar — the appointed times side by side

For a feast Lev 23, Num 28–29 and Deut 16 each date and each require
(`biblecore/calendar.json`). Verse sibling: one feast's passages, or the whole
table. Rows are copied from the file; a date or requirement it lacks → no box,
propose it.

```html
<aside class="calendar" data-anchor="23:5" data-feast="passover">
  <h4><span class="cal-title">Passover</span></h4>
  <div class="row"><span class="src">Lev 23:5</span><span class="date">(the file's date)</span>
    <span class="req">(a requirement, copied)</span></div>
  <p class="take">What the table shows here.</p>
</aside>
```

- `data-feast` = a feast id, or `all` (every passage of every feast; then each
  row carries `data-feast="<id>"`).
- One `div.row` per passage, `span.src` exactly as the file lists it;
  `span.date` copied verbatim (left out when the file gives none); one
  `span.req` per requirement, each copied verbatim.
- `take` required. Transliteration only; no `data-root`, `class="r"`, `class="rl"`.
