"""div.itin: a row of stops. Ported from Matthew's itinerary chips.

What the site relies on:
  1. it sits inside a `section.block` (kept in line with the text, like a
     count table);
  2. its direct children are only `span.stop` and `span.arr`, alternating,
     starting and ending with a stop;
  3. every stop names a place, and a `<sup>` in a stop, if present, is a
     verse reference `C:V`.
"""
import re

ITIN_RE = re.compile(r'<div\s+class="itin"[^>]*>(.*?)</div>', re.S)
SECTION_OPEN_RE = re.compile(r'<section\s+class="block"[^>]*>')
CHILD_RE = re.compile(r'<span\s+class="(stop|arr)"[^>]*>((?:(?!<span\s+class="(?:stop|arr)").)*?)</span>(?=\s*(?:<span\s+class="(?:stop|arr)"|$))', re.S)
SUP_RE = re.compile(r"<sup>(.*?)</sup>", re.S)
CV_RE = re.compile(r"^\d+:\d+$")
TAG_RE = re.compile(r"<[^>]+>")


def check(html, meta):
    errs = []
    for i, m in enumerate(ITIN_RE.finditer(html), 1):
        where = f"div.itin #{i}"
        before = html[:m.start()]
        opens = [s.end() for s in SECTION_OPEN_RE.finditer(before)]
        if not opens or "</section>" in before[opens[-1]:]:
            errs.append(f"{where}: not inside <section class=\"block\">")
        body = m.group(1).strip()
        kids = list(CHILD_RE.finditer(body))
        rebuilt = "".join(k.group(0) for k in kids)
        if re.sub(r"\s+", "", rebuilt) != re.sub(r"\s+", "", body):
            errs.append(f"{where}: holds something other than span.stop / span.arr")
        kinds = [k.group(1) for k in kids]
        if not kinds:
            errs.append(f"{where}: has no stops")
            continue
        if kinds[0] != "stop" or kinds[-1] != "stop" or any(
                a == b for a, b in zip(kinds, kinds[1:])):
            errs.append(f"{where}: stops and arrows must alternate, starting and "
                        f"ending with a stop")
        for k in kids:
            if k.group(1) != "stop":
                continue
            name = TAG_RE.sub("", SUP_RE.sub("", k.group(2))).strip()
            if not name:
                errs.append(f"{where}: an empty stop")
            for s in SUP_RE.findall(k.group(2)):
                if not CV_RE.match(s.strip()):
                    errs.append(f"{where}: stop '{name}' has <sup>{s}</sup> -- a "
                                f"stop's sup is its verse, 'C:V'")
    return errs
