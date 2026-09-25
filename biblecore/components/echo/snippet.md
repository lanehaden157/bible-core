```html
<p class="v"><span class="n">3</span> …</p>
<aside class="echo" data-anchor="1:3">Deut 11:24 gave the same promise; Josh 1:3 repeats it almost word for word.</aside>
```

- It's a **following sibling** of the verse, like `.gloss`. Never nest it inside a gloss, and always close it.
- `data-anchor` is the verse it follows (`C:V`), and the build checks that it matches.
- The site prepends "cf." and collapses it into the verse's note toggle, so don't write "cf." yourself.
- Use it for a verse-level link. A single word's history goes in that root's `echo` field instead.
- Echo asides are harvested into `data/canon.json` automatically, so don't repeat them in `intertext[]`.

**What counts as verified:** you've read the target verse, and the link rests on shared words, a shared phrase or a recognised type-scene, not just a shared theme.
