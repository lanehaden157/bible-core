"""aside.calendar: the appointed times beside a verse (see biblecore/calendar.py).
`data-feast` names one feast in the calendar file, or "all" for the whole
table. Every row's reference, date and requirement is checked against that
file, so a box can't claim more than the data holds."""
import re

from biblecore import calendar as cal
from biblecore import mirror as mr

OPEN_RE = re.compile(r'<aside\s+class="calendar"([^>]*)>(.*?)</aside>', re.S)
ROW_RE = re.compile(r'<div class="row"([^>]*)>(.*?)</div>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile("[Ͱ-Ͽἀ-῿֐-׿יִ-ﭏ]")
ROOT_RE = re.compile(r'data-root=|class="(?:[^"]*\s)?rl?(?:\s[^"]*)?"')
TAKE_RE = re.compile(r'class="(?:[^"]*\s)?take(?:\s[^"]*)?"')


def _attr(attrs, name):
    m = re.search(r'\b' + name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _norm(s):
    return re.sub(r"\s+", " ", TAG_RE.sub("", s or "")).strip()


def _spans(row, cls):
    return [_norm(x) for x in re.findall(r'<span class="' + cls + r'">(.*?)</span>', row, re.S)]


def check(html, meta):
    from biblecore import meta as um
    errs = um.check_anchored_aside(html, meta, "calendar")
    boxes = OPEN_RE.findall(html)
    if not boxes:
        return errs
    try:
        table = cal.table()
    except (OSError, ValueError, KeyError) as exc:
        return errs + [f"aside.calendar: calendar file unreadable: {exc}"]
    for attrs, body in boxes:
        anchor = _attr(attrs, "data-anchor")
        where = f"aside.calendar at {anchor!r}" if anchor else "aside.calendar"
        fid = _attr(attrs, "data-feast")
        whole = fid == "all"
        if not fid:
            errs.append(f'{where}: no data-feast="<feast id>" (or "all" for the whole table)')
        elif not whole and fid not in table:
            errs.append(f"{where}: data-feast={fid!r} is not in the calendar file")
        if not re.search(r'<h4\b[^>]*>.*?<span class="cal-title">', body, re.S):
            errs.append(f'{where}: needs <h4><span class="cal-title"> (the feast, or the table, in a few words)')
        rows = ROW_RE.findall(body)
        if not rows:
            errs.append(f'{where}: no <div class="row"> (span.src ref, span.date, span.req)')
        seen = set()
        for rattrs, r in rows:
            own = _attr(rattrs, "data-feast")
            rf = own or (None if whole else fid)
            if whole and not rf:
                errs.append(f'{where}: a row of a whole-table box needs data-feast="<feast id>"')
                continue
            feast = table.get(rf)
            if rf and not feast:
                errs.append(f"{where}: row data-feast={rf!r} is not in the calendar file")
                continue
            if not whole and own not in (None, fid):
                errs.append(f"{where}: row data-feast={own!r} is not the box's feast {fid!r}")
            srcs, dates, reqs = _spans(r, "src"), _spans(r, "date"), _spans(r, "req")
            if len(srcs) != 1:
                errs.append(f"{where}: a row needs one span.src (the passage)")
                continue
            p = cal.passage_of(feast, srcs[0]) if feast else None
            if feast and not p:
                errs.append(f"{where}: row {srcs[0]!r} is not one of feast {rf}'s passages")
                continue
            if (rf, srcs[0]) in seen:
                errs.append(f"{where}: row {srcs[0]!r} appears twice")
            seen.add((rf, srcs[0]))
            if p:
                if p.get("date") and dates != [_norm(p["date"])]:
                    errs.append(f"{where}: row {srcs[0]!r}: span.date must be the file's date, copied exactly")
                if not p.get("date") and dates:
                    errs.append(f"{where}: row {srcs[0]!r}: the file gives no date, so no span.date")
                if not reqs:
                    errs.append(f"{where}: row {srcs[0]!r} needs a span.req (what the passage requires)")
                known = [_norm(x) for x in p["requires"]]
                for q in reqs:
                    if q not in known:
                        errs.append(f"{where}: row {srcs[0]!r}: span.req {q[:40]!r} is not one of the file's "
                                    f"requirements for it (copy one exactly)")
        if whole:
            want = {(f["id"], mr.parse_span(p["ref"])) for f in table.values() for p in f["passages"]}
            got = {(f, mr.parse_span(s)) for f, s in seen}
            miss = sorted(f"{f} {mr.span_text(*sp)}" for f, sp in want - got)
            if miss:
                errs.append(f"{where}: a whole-table box lists every passage; missing {', '.join(miss[:4])}")
        if not TAKE_RE.search(body):
            errs.append(f"{where}: no p.take (what the table shows here)")
        if SCRIPT_RE.search(body):
            errs.append(f"{where}: Greek or Hebrew script inside; transliterate it")
        if ROOT_RE.search(body):
            errs.append(f"{where}: no data-root, class=\"r\" or class=\"rl\" inside")
    return errs
