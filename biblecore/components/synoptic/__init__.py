"""aside.synoptic: a parallel passage after a verse, with data-anchor and its
own <h4> header (meta.check_anchored_aside for the anchor)."""
import re


def check(html, meta):
    from biblecore import meta as um
    errs = um.check_anchored_aside(html, meta, "synoptic")
    for body in re.findall(r'<aside class="synoptic"[^>]*>(.*?)</aside>', html, re.S):
        if "<h4" not in body:
            errs.append("synoptic: an aside.synoptic without its <h4> header")
    return errs
