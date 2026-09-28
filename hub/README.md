# Canon hub

The canon hub for the Bible study books: <https://lanehaden157.github.io/bible/>.

**Generated.** Every file here comes from bible-core: the page, app and CSS
from `bible-core/hub/`, and the data from the book repos plus
`bible-core/canon/`. Rebuild from bible-core rather than editing here:

    python tools/hub_build.py ../hub

Then commit and push this repo.

Each book stays its own site (review H8). The hub shows:
- progress across the canon;
- the arcs, canon threads and type-scenes;
- the intertext graph;
- the curated reading paths;
- a cross-book concordance.

Links go into the book sites.

## Data and licences

The site credits every source in its footer and, in full, at `#/sources`;
`data/canon.json` and `data/concordance.json` carry the same credits in a
`_sources` string.

- **Hebrew text, lemmas and morphology:** Original work of the Open Scriptures
  Hebrew Bible available at <https://github.com/openscriptures/morphhb>.
  Lemma and morphology data CC BY 4.0; the Westminster Leningrad Codex text is
  in the public domain.
- **Hebrew lexicon glosses:** Open Scriptures HebrewLexicon
  (<https://github.com/openscriptures/HebrewLexicon>), Open Scriptures Hebrew
  Bible Project, CC BY 4.0 (Strong's text public domain). Shown as word
  identifiers, never as translations.
- **Greek New Testament lemmas:** Tauber, J. K., ed. *MorphGNT: SBLGNT
  Edition* (<https://github.com/morphgnt/sblgnt>, doi:10.5281/zenodo.376200),
  parsing and lemmatization CC BY-SA 3.0, of the SBL Greek New Testament,
  © 2010 Society of Biblical Literature and Logos Bible Software, under the
  SBLGNT license. No Greek text is reproduced; lemmas are transliterated.
- **Septuagint lemmas:** LXX-Rahlfs-1935, © 2017 Eliran Wong
  (<https://github.com/eliranwong/LXX-Rahlfs-1935>), CC BY-NC-SA 4.0, based
  on the CCAT LXX morphology (University of Pennsylvania), read through the
  Center of Biblical Languages and Technology's Text-Fabric edition
  (<https://github.com/CenterBLC/LXX>).
- **Typefaces:** Cinzel, EB Garamond, Crimson Pro, Source Serif 4 and Uncial
  Antiqua, via Google Fonts, SIL Open Font License 1.1.
- **Translations, notes and the canon registries:** the studies' own.

**Non-commercial and share-alike terms.** The Septuagint data is
CC BY-NC-SA and MorphGNT's is CC BY-SA, so the hub must stay non-commercial,
and what it derives from them is subject to share-alike.

**Before the hub quotes more text** (review H13), check the current terms of
every source it reproduces, including any Greek or English base text.
