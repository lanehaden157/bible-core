# corpus/

Shared corpus files `tools/new_book.py` copies into a new book. The Greek
book's larger corpora are fetched instead (below).

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

## Fetched for a Greek book (`python -m biblecore fetch`)

Not kept here: `biblecore/fetch.py` pins them and downloads them into the book
(git-ignored there), checking every file's sha1. The commits are Matthew's
`pipeline/fetch_corpus.py`'s; the sha1s were taken 2026-10-01 and match
Matthew's copies.

- **MorphGNT SBLGNT** (https://github.com/morphgnt/sblgnt, commit
  `aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d`): all 27 `*-morphgnt.txt`
  files, ~11 MB, into `paths.morphgnt` (`corpus/morphgnt`). The SBLGNT text
  is under the SBLGNT EULA (https://sblgnt.com/license); the morphology and
  lemmatization are CC BY-SA 3.0. The site footer credits both (main.js
  `SOURCES`).
- **CenterBLC LXX** (https://github.com/CenterBLC/LXX, commit
  `4829f3746c84d75576702498e75a68856358f289`, `tf/1935/`, Rahlfs 1935):
  `book.tf`, `chapter.tf`, `verse.tf`, `lex_utf8.tf`, ~15.5 MB, into
  `paths.lxx` (`corpus/lxx`). MIT. Read by canon leads only.
