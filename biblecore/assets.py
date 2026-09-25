"""Write the shared site assets for the enabled components (review D5, D10).

    python -m biblecore assets

  css/core.css             shared structure, from biblecore/web/core.css
  css/components.css       each enabled component's style.css
  data/components.json     [{name, role, selector}] for app/main.js + spotlight.js
  components-reference.md  each enabled component's snippet (synced)

All generated, so don't edit them. The book's own look is css/theme.css. Runs
first in the build, since validate's whitelist reads every css/*.css.

A book whose `paths.css` points at a single stylesheet (Joshua's layout, in
the tests) keeps it: nothing is written into css/ then, only the data file
and the reference.
"""
import json
import os

from biblecore import components
from biblecore.book import book

HERE = os.path.dirname(os.path.abspath(__file__))


def _write(path, text):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != text:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return True
    return False


def main(argv=None):
    b = book()
    comps = components.enabled(b)
    wrote = []
    css = b.path("css")
    if os.path.isdir(css):
        core = open(os.path.join(HERE, "web", "core.css"), encoding="utf-8").read()
        if _write(os.path.join(css, "core.css"), core):
            wrote.append("css/core.css")
        if _write(os.path.join(css, "components.css"), components.css_bundle(comps)):
            wrote.append("css/components.css")
    data = json.dumps(components.app_manifest(comps), indent=2, ensure_ascii=False) + "\n"
    if _write(b.data("components.json"), data):
        wrote.append("data/components.json")
    if _write(b.path("components_ref"), components.reference(comps, b.name)):
        wrote.append(os.path.basename(b.path("components_ref")))
    print(f"assets: components {[c.name for c in comps]}"
          + (f"; wrote {', '.join(wrote)}" if wrote else "; up to date"))
    return 0
