"""aside.mirror: the twin passage of a mirrored book beside a verse (see
biblecore/mirror.py). The box names its pair in data-pair; the pair must be in
the book's mirror data file with status seed or kept. Anchor, span, ref, shared
words and strength dots are all checked against that file, so a box can't claim
more than the data holds."""
import re

from biblecore import mirror as mr

OPEN_RE = re.compile(r'<aside\s+class="mirror"([^>]*)>(.*?)</aside>', re.S)
SPAN_RE = re.compile(r'^\d+:\d+[–-](?:\d+:)?\d+$')
SCRIPT_RE = re.compile(r'[Ͱ-Ͽἀ-῿֐-׿יִ-ﭏ]')
ROOT_RE = re.compile(r'data-root=|class="(?:[^"]*\s)?rl?(?:\s[^"]*)?"')
HEAD_RE = re.compile(r'<h4\b[^>]*>(.*?)</h4>', re.S)
SH_RE = re.compile(r'<span class="sh"([^>]*)>')
IDS_RE = re.compile(r'^[0-9]+[a-z]?(?:,[0-9]+[a-z]?)*$')
STATUSES_OK = ("seed", "kept")


def _attr(attrs, name):
    m = re.search(r'\b' + name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _has_class(body, cls):
    return re.search(r'class="(?:[^"]*\s)?' + re.escape(cls) + r'(?:\s[^"]*)?"', body) is not None


def _listed(i, shared):
    """Is span.sh id `i` one of the pair's shared ids ('3515' covers '3515a')?"""
    try:
        ik = mr.lemma_key(i)
    except ValueError:
        return False
    for s in shared:
        try:
            sk = mr.lemma_key(s)
        except ValueError:
            continue
        if ik == sk or mr.bare_id(ik) == sk:
            return True
    return False


def check(html, meta):
    from biblecore import audit as atc
    from biblecore import canon
    from biblecore import meta as um
    from biblecore.book import book
    errs = um.check_anchored_aside(html, meta, "mirror")
    boxes = OPEN_RE.findall(html)
    if not boxes:
        return errs
    b = book()
    if not b.mirrors:
        return errs + ["aside.mirror: book.json declares no mirrors"]
    try:
        table = mr.pair_table(b)
    except mr.MirrorError as exc:
        return errs + [f"aside.mirror: {exc}"]
    rng = None
    if meta and meta.get("passage"):
        try:
            rng = atc.parse_range(meta["passage"])
        except (AttributeError, TypeError):
            rng = None
    for attrs, body in boxes:
        anchor = _attr(attrs, "data-anchor")
        where = f"aside.mirror at {anchor!r}" if anchor else "aside.mirror"
        pid = _attr(attrs, "data-pair")
        hit = table.get(pid) if pid else None
        if not pid:
            errs.append(f"{where}: no data-pair=\"<pair id>\"")
        elif not hit:
            errs.append(f"{where}: data-pair={pid!r} is not in the mirror data file")
        elif hit[0].get("status") not in STATUSES_OK:
            errs.append(f"{where}: pair {pid} has status {hit[0].get('status')!r}")
        pair, other = hit if hit else ({}, None)
        span = _attr(attrs, "data-span")
        if span is not None:
            if not SPAN_RE.match(span):
                errs.append(f"{where}: data-span={span!r} must be 'C:V–C:V' or 'C:V–V'")
            elif rng:
                sp = mr.parse_span(f"{b.osis} {span}")
                if sp and not (rng[0] <= sp[1] and sp[2] <= rng[1]):
                    errs.append(f"{where}: data-span={span!r} is outside the unit")
        hs = mr.parse_span(pair.get("here")) if pair else None
        os_ = mr.parse_span(pair.get("other")) if pair else None
        if anchor and re.fullmatch(r"\d+:\d+", anchor):
            cv = tuple(int(x) for x in anchor.split(":"))
            if rng and not (rng[0] <= cv <= rng[1]):
                errs.append(f"{where}: the anchor is outside the unit")
            if hs and not (hs[1] <= cv <= hs[2]):
                errs.append(f"{where}: the anchor is outside pair {pid}'s {mr.span_text(*hs)}")
        head = HEAD_RE.search(body)
        if not head:
            errs.append(f"{where}: no <h4> header (par-title, par-ref)")
        else:
            h = head.group(1)
            ref = re.search(r'<span class="par-ref">(.*?)</span>', h, re.S)
            refs = canon.parse_refs(ref.group(1)) if ref else []
            if not refs:
                errs.append(f"{where}: the <h4> needs a <span class=\"par-ref\"> naming the twin, "
                            f"like 'Exod 18:13–18'")
            for r in refs:
                sp = mr.parse_span(r)
                if sp is None or (other and sp[0] != other):
                    errs.append(f"{where}: par-ref {r!r} is not in the mirrored book")
                elif os_ and not mr.contains(os_, sp):
                    errs.append(f"{where}: par-ref {r!r} is outside pair {pid}'s {mr.span_text(*os_)}")
            if not _has_class(h, "par-title"):
                errs.append(f"{where}: the <h4> needs a <span class=\"par-title\">")
            sm = re.search(r'<span class="strength"([^>]*)>(.*?)</span>', h, re.S)
            if sm and pair:
                if pair.get("tier") == "echo":
                    errs.append(f"{where}: an echo-tier pair carries no strength dots")
                else:
                    n = _attr(sm.group(1), "data-n")
                    dots = sm.group(2).count("●")
                    if (n is not None and n != str(pair.get("strength"))) or (
                            n is None and sm.group(2).strip() and dots != pair.get("strength")):
                        errs.append(f"{where}: strength dots ({n or dots}) don't match the data "
                                    f"file ({pair.get('strength')}); leave the span empty and "
                                    f"the build fills it")
        rows = re.findall(r'<div class="row">(.*?)</div>', body, re.S)
        if pair.get("poetry") in ("other", "both"):
            if _has_class(body, "row"):
                errs.append(f"{where}: pair {pid} has a poetry twin: reference and title only, no rows")
        elif pair and not rows:
            errs.append(f"{where}: no <div class=\"row\"> (a span.src ref and a span.txt text)")
        for r in rows:
            if not (_has_class(r, "src") and _has_class(r, "txt")):
                errs.append(f"{where}: a row needs both span.src and span.txt")
        if not _has_class(body, "take"):
            errs.append(f"{where}: no p.take (what the mirror shows here)")
        shared = [i for s in mr.all_shared(pair) for i in s.get("ids", [])] if pair else []
        for sattrs in SH_RE.findall(body):
            ids = _attr(sattrs, "data-ids")
            if not ids or not IDS_RE.match(ids):
                errs.append(f"{where}: span.sh needs data-ids=\"3515\" (Strong's, comma-separated)")
                continue
            for i in ids.split(","):
                if pair and not _listed(i, shared):
                    errs.append(f"{where}: span.sh H{i} is not in pair {pid}'s shared list "
                                f"(shared words come from the data file, or the porter's mirror[])")
        if SCRIPT_RE.search(body) or SCRIPT_RE.search(attrs):
            errs.append(f"{where}: Greek or Hebrew script inside; transliterate it")
        if ROOT_RE.search(body):
            errs.append(f"{where}: no data-root, class=\"r\" or class=\"rl\" inside "
                        f"(the occurrence scanner counts every data-root)")
    return errs
