# Canon hub

The canon hub for the Bible study books: <https://lanehaden157.github.io/bible/>.

**Generated.** Every file here comes from bible-core: the page, app and CSS
from `bible-core/hub/`, and the data from the book repos plus
`bible-core/canon/`. Don't edit here.

**It rebuilds itself.** `.github/workflows/rebuild.yml` runs daily (06:17 UTC)
and on the Actions tab's "Run workflow" button. It clones the pushed
bible-core and every book, runs `tools/hub_build.py`, and commits only when
something changed. So the hub shows pushed work only, and is at most a day
behind unless you press the button. To rebuild by hand from local folders
(this reads unpushed work too):

    python tools/hub_build.py ../hub

then commit and push this repo. GitHub pauses a scheduled workflow after 60
days without repo activity; re-enable it from the Actions tab.

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
