```html
<p class="v"><span class="n">3</span> …</p>
<aside class="echo" data-anchor="1:3">Deut 11:24 gave the same promise; Josh 1:3 repeats it almost word for word.</aside>
```

- **Following sibling** of the verse, like `.gloss`. Never nested in a gloss, always closed.
- `data-anchor` = the verse it follows (`C:V`); build checks it.
- Site prepends "cf." and folds it into the verse's note toggle: don't write "cf.".
- Verse-level link only. One word's history → that root's `echo` field.
- Harvested into `data/canon.json`: don't repeat in `intertext[]`.

**Verified =** target verse read, and link rests on shared words, a shared phrase or a recognised type-scene, not just a shared theme.
