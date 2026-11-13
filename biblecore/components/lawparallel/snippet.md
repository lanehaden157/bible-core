## lawparallel — a law's other statements beside a verse

For a law the Torah states in more than one place (`biblecore/laws.json`).
Verse sibling: the other passages of that law, their stated differences and
the text's own reasons. Never a dating or source argument (those live in the
file's `footnote`). A wording link only = `aside.echo`.

```html
<aside class="lawparallel" data-anchor="15:12" data-law="release-of-slaves" data-at="Deut 15:12–18">
  <h4><span class="par-title">Release of a bound Hebrew</span></h4>
  <div class="row"><span class="src">Exod 21:2–6</span><span class="txt">Six years he serves; in the seventh he goes free.</span>
    <span class="diff">(copied from the file)</span><span class="why">(optional, copied)</span></div>
  <p class="take">What the parallel shows here.</p>
</aside>
```

- `data-law` = a law id in the file; `data-at` = this book's passage of it,
  exactly as listed; `data-anchor` = a verse inside it and inside the unit.
- One `div.row` per other passage, `span.src` exactly as the file lists it.
  `span.diff` is **copied verbatim** from that passage's `differences`;
  `span.why`, if used, from its `reasons`. `span.txt` is the unit's own
  rendering. A difference or reason the file lacks → no box; propose it.
- `take` required: one or two sentences. Transliteration only; no
  `data-root`, `class="r"` or `class="rl"` inside.
- Harvested into `data/canon.json` (intertext kind `law`, one row per `span.src`).
- **Briefs** (so a narrative book's echo can open this law): meta-block
  `lawbriefs[]`, each `{law, ref, brief}`. `ref` is a full reference inside
  one of the law's passages (`"Deut 15:1–11"`); `brief` at most two
  sentences. Merged at port into `data/canon.json`, read by the hub; adding
  one needs no re-vendor.
