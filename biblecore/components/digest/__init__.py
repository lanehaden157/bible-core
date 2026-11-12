"""section.block.digest: a summary standing in for a stretch of verses.

What the site relies on:
  1. the opening tag is `<section class="block digest" data-verses="C:V–V">`;
  2. it holds at least one `<p>` with text;
  3. `data-verses` is validated with every other (meta.check_declared_verses),
     so a verse can't be both summarised and written out.
A tiered book's units.json says which stretches are digests (tiers.py checks
that blocks cover them). `since` is 0.1.0: only a tiered book enables this.
"""
import re

OPEN_RE = re.compile(r'<section\b([^>]*\bclass="[^"]*\bdigest\b[^"]*"[^>]*)>', re.I)
CLOSE_RE = re.compile(r"</section>", re.I)
P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def check(html, meta):
    errs = []
    for i, m in enumerate(OPEN_RE.finditer(html), 1):
        where = f"section.digest #{i}"
        attrs = m.group(1)
        if not re.search(r'\bclass="block\s+digest"', attrs):
            errs.append(f'{where}: class must be exactly "block digest"')
        if not re.search(r'\bdata-verses="[^"]+"', attrs):
            errs.append(f'{where}: needs data-verses="C:V–V" (the verses it sums up)')
        end = CLOSE_RE.search(html, m.end())
        body = html[m.end():end.start() if end else len(html)]
        if not any(TAG_RE.sub("", p).strip() for p in P_RE.findall(body)):
            errs.append(f"{where}: holds no <p> text")
    return errs
