""".compare: a verse sibling of labelled rows (.row > .src + text). Checked
only for shape: every row has its .src label."""
import re

ROW_RE = re.compile(r'<(span|div) class="row">(.*?)</\1>', re.S)


def check(html, meta):
    errs = []
    for block in re.findall(r'<(?:span|div) class="compare">(.*?)\n</(?:span|div)>', html, re.S):
        for _, row in ROW_RE.findall(block):
            if 'class="src"' not in row:
                errs.append("compare: a .row without its .src label")
    return errs
