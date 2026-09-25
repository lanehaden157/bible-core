"""div.poem: verse blocks whose text is set in lines.

The lines live inside ordinary `div.v` blocks, so the audit, data-w, scan
and the verse anchors read a poem exactly as they read prose (review B12:
Matthew's `.prayer` block replaced verses and defeated the audit). What
the site relies on:
  1. `div.poem` sits at the top level of the verses, not inside another poem
     or a section.block, and holds only verse blocks, glosses and asides;
  2. every `div.v` in a poem sets all its text in `span.l` lines: nothing
     but the verse number, whitespace and the endnote marker outside them;
  3. `span.l` appears only there, is never nested, and its only extra
     class is `in` (an indented, continuing line);
  4. `data-pair`, if used, is a short label ("A", "B", "A'") marking
     parallel lines.
"""
import re
from html.parser import HTMLParser

PAIR_RE = re.compile(r"^[A-Z]'{0,2}$")
VOID = {"br", "img", "hr", "wbr"}


class _Walk(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # [(tag, classes)]
        self.errs = []
        self.verse = None        # current poem verse: {"lines": n, "stray": str, "n": ...}

    def _cls(self, attrs):
        return (dict(attrs).get("class") or "").split()

    def _inside(self, cls):
        return any(cls in c for _t, c in self.stack)

    def handle_starttag(self, tag, attrs):
        cls = self._cls(attrs)
        a = dict(attrs)
        if tag == "div" and "poem" in cls:
            if self._inside("poem"):
                self.errs.append("div.poem nested inside another div.poem")
            if any(t == "section" for t, _c in self.stack):
                self.errs.append("div.poem inside a section -- a poem is verse text, "
                                 "not a structure block")
        in_poem_top = self.stack and "poem" in self.stack[-1][1]
        if in_poem_top:
            ok = ((tag in ("div", "p") and cls == ["v"]) or "gloss" in cls or tag == "aside")
            if not ok:
                self.errs.append(f"div.poem holds <{tag} class=\"{' '.join(cls)}\"> -- only "
                                 f"verse blocks, glosses and asides go directly inside")
            if tag in ("div", "p") and cls == ["v"]:
                self.verse = {"lines": 0, "stray": "", "tag": tag}
        if tag == "span" and "l" in cls:
            if self.verse is None or not (self.stack and self.stack[-1][1] == ["v"]):
                self.errs.append("span.l outside a verse block of a div.poem (or nested "
                                 "in another element) -- lines are direct children of the verse")
            extra = set(cls) - {"l", "in"}
            if extra:
                self.errs.append(f"span.l carries unknown class(es) {sorted(extra)} -- only 'in'")
            if "data-pair" in a and not PAIR_RE.match(a["data-pair"] or ""):
                self.errs.append(f"data-pair={a['data-pair']!r} -- use a short label like 'A', 'B', \"A'\"")
            if self.verse is not None:
                self.verse["lines"] += 1
        if tag not in VOID:
            self.stack.append((tag, cls))

    def handle_endtag(self, tag):
        # pop to the matching tag (tolerant of sloppy nesting elsewhere)
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                closed = self.stack[i]
                del self.stack[i:]
                break
        else:
            return
        if self.verse is not None and closed[0] == self.verse["tag"] and closed[1] == ["v"] \
                and self.stack and "poem" in self.stack[-1][1]:
            if self.verse["lines"] == 0:
                self.errs.append("a verse in div.poem has no span.l lines")
            if self.verse["stray"].strip():
                self.errs.append(f"text outside span.l in a poem verse: "
                                 f"{self.verse['stray'].strip()[:40]!r}")
            self.verse = None

    def handle_data(self, data):
        if self.verse is None or not self.stack:
            return
        # directly inside the verse block, not inside a line / number / marker
        if self.stack[-1][1] == ["v"]:
            self.verse["stray"] += data


def check(html, meta):
    if 'class="poem"' not in html and 'class="l' not in html:
        return []
    w = _Walk()
    w.feed(html)
    return [f"poem: {e}" for e in dict.fromkeys(w.errs)]
