"""Generate data/occurrences.json from the unit fragments.

    python -m biblecore scan

Pure markup logic: reads the English and data-root spans only.

Per unit, per data-root:
  count   -- occurrences in the verse translation only (what a reader sees)
  verses  -- the verse numbers those fall in
  hits    -- [{v, pre, hit, post}] context snippets, for the concordance search
  total   -- every data-root in the fragment (legend, glosses, diagrams too),
             kept for verify_occurrences' independent token cross-check

Never hand-edit data/occurrences.json -- re-run this.
"""

import glob
import json
import os
import re

from biblecore.book import book

VBLOCK = re.compile(r'<(div|p)\s+class="v"[^>]*>(.*?)</\1>', re.S)
NUM = re.compile(r'<span class="n">(\d+)</span>')
ROOTSPAN = re.compile(r'data-root="([a-z0-9-]+)"')
HITSPAN = re.compile(r'<span [^>]*\bdata-root="([a-z0-9-]+)"[^>]*>(.*?)</span>', re.S)
TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
PAD = 55


SUP = re.compile(r"<sup\b.*?</sup>", re.S)


def detag(s):
    return WS.sub(" ", TAGS.sub("", SUP.sub("", s))).strip()


def scan_unit(html):
    roots = {}
    for m in VBLOCK.finditer(html):
        seg = m.group(2)
        nums = NUM.findall(seg)
        verse = int(nums[0]) if nums else None
        # detag, then drop the leading verse-number marker from the snippet text
        plain = re.sub(r"^\d+\s*", "", detag(seg))

        for r in ROOTSPAN.findall(seg):
            e = roots.setdefault(r, blank())
            e["count"] += 1
            if verse:
                e["verses"].append(verse)

        # context snippets: walk the actual <span data-root> elements in order
        for hm in HITSPAN.finditer(seg):
            r, inner = hm.group(1), detag(hm.group(2))
            if not inner:
                continue
            idx = plain.find(inner)
            if idx < 0:
                pre, post = "", ""
            else:
                pre = plain[max(0, idx - PAD):idx].lstrip()
                post = plain[idx + len(inner):idx + len(inner) + PAD].rstrip()
            e = roots.setdefault(r, blank())
            e["hits"].append({"v": verse, "pre": ellip(pre, "l"),
                              "hit": inner, "post": ellip(post, "r")})

    for r in ROOTSPAN.findall(html):
        roots.setdefault(r, blank())["total"] += 1

    for e in roots.values():
        e["verses"] = sorted(set(e["verses"]))
    return dict(sorted(roots.items()))


def blank():
    return {"count": 0, "verses": [], "hits": [], "total": 0}


def ellip(s, side):
    if not s:
        return s
    return ("…" + s) if side == "l" else (s + "…")


def scan_all():
    data = {}
    for path in sorted(glob.glob(os.path.join(book().path("units"), "unit-*.html"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            data[slug] = scan_unit(fh.read())
    return data


def main(argv=None):
    data = scan_all()
    out = book().data("occurrences.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    tot = sum(r["count"] for u in data.values() for r in u.values())
    hits = sum(len(r["hits"]) for u in data.values() for r in u.values())
    print(f"wrote {out} -- {len(data)} units, {tot} in-verse occurrences, {hits} snippets")
    return 0
