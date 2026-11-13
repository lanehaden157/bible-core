"""aside.lawparallel: the other places a law is restated, beside the verse
where this book states it (see biblecore/laws.py). The box names its law in
data-law and the passage it sits at in data-at; both must be in the laws
file. Every row's reference, difference and reason is checked against that
file, so a box can't claim more than the data holds."""
import re

from biblecore import laws
from biblecore import mirror as mr

OPEN_RE = re.compile(r'<aside\s+class="lawparallel"([^>]*)>(.*?)</aside>', re.S)
ROW_RE = re.compile(r'<div class="row">(.*?)</div>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile('[Ͱ-Ͽἀ-῿֐-׿יִ-ﭏ]')
ROOT_RE = re.compile(r'data-root=|class="(?:[^"]*\s)?rl?(?:\s[^"]*)?"')
CV_RE = re.compile(r"^\d+:\d+$")


def _attr(attrs, name):
    m = re.search(r'\b' + name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _has_class(body, cls):
    return re.search(r'class="(?:[^"]*\s)?' + re.escape(cls) + r'(?:\s[^"]*)?"', body) is not None


def _span(row, cls):
    m = re.search(r'<span class="' + cls + r'">(.*?)</span>', row, re.S)
    return re.sub(r"\s+", " ", TAG_RE.sub("", m.group(1))).strip() if m else None


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def check(html, meta):
    from biblecore import audit as atc
    from biblecore import meta as um
    from biblecore.book import book
    errs = um.check_anchored_aside(html, meta, "lawparallel")
    boxes = OPEN_RE.findall(html)
    if not boxes:
        return errs
    b = book()
    try:
        table = laws.table()
    except (OSError, ValueError, KeyError) as exc:
        return errs + [f"aside.lawparallel: laws file unreadable: {exc}"]
    rng = None
    if meta and meta.get("passage"):
        try:
            rng = atc.parse_range(meta["passage"])
        except (AttributeError, TypeError):
            rng = None
    for attrs, body in boxes:
        anchor = _attr(attrs, "data-anchor")
        where = f"aside.lawparallel at {anchor!r}" if anchor else "aside.lawparallel"
        lid, at = _attr(attrs, "data-law"), _attr(attrs, "data-at")
        law = table.get(lid) if lid else None
        if not lid:
            errs.append(f'{where}: no data-law="<law id>"')
        elif not law:
            errs.append(f"{where}: data-law={lid!r} is not in the laws file")
        here, here_p = (mr.parse_span(at) if at else None), None
        if not at:
            errs.append(f'{where}: no data-at="<passage ref>" (the passage this box sits at)')
        elif here is None:
            errs.append(f"{where}: data-at={at!r} is not a passage reference")
        elif here[0] != b.osis:
            errs.append(f"{where}: data-at={at!r} is not in this book ({b.osis})")
        elif law:
            here_p = laws.passage_of(law, at)
            if not here_p:
                errs.append(f"{where}: data-at={at!r} is not one of law {lid}'s passages")
        if anchor and CV_RE.match(anchor):
            cv = tuple(int(x) for x in anchor.split(":"))
            if rng and not (rng[0] <= cv <= rng[1]):
                errs.append(f"{where}: the anchor is outside the unit")
            if here and here_p and not (here[1] <= cv <= here[2]):
                errs.append(f"{where}: the anchor is outside data-at {at}")
        if not re.search(r"<h4\b[^>]*>.*?<span class=\"par-title\">", body, re.S):
            errs.append(f'{where}: needs <h4><span class="par-title"> (the law, in a few words)')
        rows = ROW_RE.findall(body)
        if not rows:
            errs.append(f"{where}: no <div class=\"row\"> (span.src ref, span.txt, span.diff)")
        seen = set()
        for r in rows:
            ref, txt, diff, why = (_span(r, c) for c in ("src", "txt", "diff", "why"))
            if ref is None or not txt:
                errs.append(f"{where}: a row needs span.src (the passage) and span.txt")
                continue
            p = laws.passage_of(law, ref) if law else None
            if law and not p:
                errs.append(f"{where}: row {ref!r} is not one of law {lid}'s passages")
                continue
            if p and here_p and p is here_p:
                errs.append(f"{where}: row {ref!r} is the passage the box sits at")
            if ref in seen:
                errs.append(f"{where}: row {ref!r} appears twice")
            seen.add(ref)
            if not diff:
                errs.append(f"{where}: row {ref!r} needs a span.diff (a stated difference)")
            elif p and _norm(diff) not in [_norm(d) for d in p["differences"]]:
                errs.append(f"{where}: row {ref!r}: span.diff is not one of the file's "
                            f"differences for it (copy one exactly)")
            if why is not None and p and _norm(why) not in [_norm(x["why"]) for x in p.get("reasons", [])]:
                errs.append(f"{where}: row {ref!r}: span.why is not one of the file's "
                            f"reasons for it (the text's own reason, copied exactly)")
        if not _has_class(body, "take"):
            errs.append(f"{where}: no p.take (what the parallel shows here)")
        if SCRIPT_RE.search(body):
            errs.append(f"{where}: Greek or Hebrew script inside; transliterate it")
        if ROOT_RE.search(body):
            errs.append(f"{where}: no data-root, class=\"r\" or class=\"rl\" inside")
        m = laws.DATING_RE.search(TAG_RE.sub(" ", body))
        if m:
            errs.append(f"{where}: dating or source argument ({m.group(0)!r}); the file's footnote carries those")
    return errs
