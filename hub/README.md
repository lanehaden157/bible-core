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

- **Hebrew text and morphology:** Open Scriptures Hebrew Bible (morphhb npm
  package; WLC text, OSHB morphology).
- **Lexicon glosses:** Open Scriptures HebrewLexicon (Strong's). They're shown
  as word identifiers, never as translations.
- **Translations:** each study's own.

**Before the hub quotes more text** (review H13), check the current terms of
every source it reproduces. That covers the Greek text (SBLGNT) before any
Greek data appears here, and any English base text.
