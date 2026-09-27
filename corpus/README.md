# corpus/

Shared corpus files `tools/new_book.py` copies into a new book.

- `lexicon/HebrewStrong.xml` — Strong's Hebrew dictionary in XML, from the
  OpenScriptures HebrewLexicon project
  (https://github.com/openscriptures/HebrewLexicon; see that repo for its
  license). The canon-leads glosses read it. sha1
  `9f3ab556ebc0870d59f3f192ba79b54531faf4ee`, identical to the copies in
  Joshua (`pipeline/corpus/lexicon/`) and Numbers (`corpus/lexicon/`).

- `lexicon/lexemes.yaml` — the MorphGNT morphological lexicon (Tauber, ed.,
  https://github.com/morphgnt/morphological-lexicon, commit
  `0dca2af89f413cbb24f617ddbdc347e9d798ddf3`, fetched 2026-09-27), CC BY-SA
  3.0. `lang/greek_lexicon.py` reads its `gloss` field, keyed by the Greek
  lemma text; `emit.py` looks a word's lemma up through
  `corpus/morphgnt.py`'s `lemma_forms()`. Every one of Matthew's 1,680
  lemmas matched a lexicon entry exactly (2026-09-27 check) — worth
  re-checking on any future NT book, since MorphGNT sub-projects have
  occasionally drifted on accentuation. sha1
  `9db21bd70bc88510d6b4caefe436ea744b684a65`. **CC BY-SA (share-alike):** this
  vendored copy, and `data/lemmas.json`'s `g` field it feeds, stay under
  the same licence — the site's own text, notes and code are unaffected,
  since they are separate works shown alongside it, not built from it. The
  site credits both MorphGNT projects (main.js `SOURCES`, `.site-foot`).
