"""Opt a pre-core book site into its division theme. Retired: Joshua (0.8.5)
and Matthew (0.9.0) now run the template shell, so no book uses it. Kept for
a future site with its own shell.

    python tools/legacy_theme.py ../Joshua          # write / refresh the theme
    python tools/legacy_theme.py ../Joshua --check  # say what would change

Lane's call (2026-09-26): Joshua and Matthew get the division themes, as a
small opt-in patch, not a migration (they keep their own code, H3). Re-run
after a core theme change. Idempotent. What it touches in the book:

  css/division.css  theme.py's output for the book (tokens, dark palette,
                    banner masthead + emblem, ornament, dark-mode lift for
                    tracked words), plus LEGACY below: aliases for the book's
                    own token names and the few colours its stylesheet
                    hard-codes, so dark mode reaches them
  index.html        the data-theme head script, the division.css link after
                    styles.css (so it wins), no separate font link (the
                    division imports its fonts), and Settings -> Appearance
                    wired by a small inline script (main.js untouched)
  app/threads.js    one line: the root colour goes through --rc, so dark
                    mode can lift it; the colours themselves don't change

Units, data, and tracked-word colours are never touched.
"""
import argparse
import hashlib
import json
import os
import re
import sys

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)

from biblecore import book as bookmod  # noqa: E402
from biblecore import theme  # noqa: E402

BOOKS = {  # folder name -> (osis, display name); Joshua and Matthew have left
}

COMMON = """
/* ---- legacy site: colours its stylesheet hard-codes, now tokens ---- */
body {
  background:
    radial-gradient(circle at 16% -5%, var(--glow-1) 0%, transparent 55%),
    radial-gradient(circle at 106% 104%, var(--glow-2) 0%, transparent 52%),
    var(--bg);
}
.topbar { background: var(--topbar-bg); }
.unit [data-root].root-active { background: var(--root-active-bg); }
.unit [data-root] { --rc-shown: var(--rc); }
"""

LEGACY = {
    "Josh": COMMON,
    "Matt": COMMON + """
/* Matthew's own accent names */
:root, :root[data-theme] {
  --accent-crimson: var(--accent-clay);
  --accent-gold: var(--accent-bronze);
  --accent-slate: var(--accent-jordan);
  --accent-warm: var(--accent-olive);
  --accent-rust: var(--accent-wine);
}
.bm-tick.in-disc { background: var(--panel-2); color: var(--ink); }
.unit-chip.in-disc { background: var(--panel-2); border-color: var(--rule); }
.unit .ringrow.center { background: var(--panel-2); }
""",
}

HEAD_SCRIPT = ('<script>try{document.documentElement.dataset.theme=localStorage.getItem("bible:theme")'
               '||"auto"}catch(e){document.documentElement.dataset.theme="auto"}</script>')
APPEARANCE = """    <div class="settings-row" style="display:block"><b style="font-weight:600">Appearance</b>
      <label style="display:block"><input type="radio" name="appearance" value="auto"> Match the system</label>
      <label style="display:block"><input type="radio" name="appearance" value="light"> Light</label>
      <label style="display:block"><input type="radio" name="appearance" value="dark"> Dark</label>
    </div>
"""
WIRE = ("<script>(function(){var c=document.documentElement.dataset.theme||'auto';"
        "document.querySelectorAll('input[name=appearance]').forEach(function(i){i.checked=i.value===c;"
        "i.addEventListener('change',function(){document.documentElement.dataset.theme=i.value;"
        "try{localStorage.setItem('bible:theme',i.value)}catch(e){}})})})();</script>")


def plan(root):
    folder = os.path.basename(os.path.normpath(root))
    if folder not in BOOKS:
        raise SystemExit(f"{folder}: not a known legacy book ({', '.join(BOOKS)})")
    osis, name = BOOKS[folder]
    cfg = {"book": name, "osis": osis, "slug": name.lower(), "language": "hebrew",
           "corpus": {"kind": "oshb"}}
    b = bookmod.Book(cfg, root)
    css = theme.build_css(b)
    if css is None:
        raise SystemExit(f"{osis} has no entry in biblecore/web/themes.json")
    files = {"css/division.css": css + LEGACY[osis]}

    idx = open(os.path.join(root, "index.html"), encoding="utf-8").read()
    if HEAD_SCRIPT not in idx:
        idx = idx.replace("<head>\n", "<head>\n" + HEAD_SCRIPT + "\n", 1)
    idx = re.sub(r'<link href="https://fonts\.googleapis\.com/css2[^"]*" rel="stylesheet">\n', "", idx)
    idx = re.sub(r'<link rel="stylesheet" href="css/division\.css[^"]*">\n', "", idx)
    # the version is the css's own hash, so a re-run after a theme change busts caches
    ver = hashlib.sha1(files["css/division.css"].encode("utf-8")).hexdigest()[:8]
    idx = re.sub(r'(<link rel="stylesheet" href="css/styles\.css[^"]*">\n)',
                 r'\1<link rel="stylesheet" href="css/division.css?v=' + ver + r'">\n', idx, count=1)
    if 'name="appearance"' not in idx:
        idx = idx.replace('  <div id="settings-panel" class="settings-panel" role="menu" aria-label="display settings" hidden>\n',
                          '  <div id="settings-panel" class="settings-panel" role="menu" aria-label="display settings" hidden>\n' + APPEARANCE, 1)
    if WIRE not in idx:
        idx = idx.replace("</body>", WIRE + "\n</body>", 1)
    files["index.html"] = idx

    tj = open(os.path.join(root, "app", "threads.js"), encoding="utf-8").read()
    tj = tj.replace("rules.push(`${sel} ${r}{color:${m.color}}`);",
                    "rules.push(`${sel} ${r}{--rc:${m.color};color:var(--rc-shown,${m.color})}`);")
    files["app/threads.js"] = tj
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.book)
    changed = []
    for rel, text in plan(root).items():
        p = os.path.join(root, rel)
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old != text:
            changed.append(rel)
            if not a.check:
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    for rel in changed:
        print(f"  {'would change' if a.check else 'changed'} {rel}")
    print(f"legacy theme: {len(changed)} file(s) {'would change' if a.check else 'changed'} in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
