"""aside.textform: a verse sibling like aside.echo (same anchor and nesting
rules, meta.check_anchored_aside), plus a `data-src` naming the witness
from SOURCES. Review E11: a home for "absent from the Greek" notes, which a
future LXX corpus adapter could fill from data."""
import re

# data-src -> label the site prints (style.css ::before)
SOURCES = {
    "mt": "MT", "lxx": "LXX", "sp": "Samaritan", "dss": "Qumran",
    "qere": "Qere", "ketiv": "Ketiv", "targum": "Targum",
    "peshitta": "Peshitta", "vulgate": "Vulgate",
}
OPEN_RE = re.compile(r'<aside\s+class="textform"([^>]*)>')
SRC_RE = re.compile(r'data-src="([^"]*)"')


def check(html, meta):
    from biblecore import meta as um
    errs = um.check_anchored_aside(html, meta, "textform")
    for m in OPEN_RE.finditer(html):
        s = SRC_RE.search(m.group(1))
        if not s:
            errs.append("aside.textform has no data-src (one of "
                        f"{', '.join(SOURCES)})")
        elif s.group(1) not in SOURCES:
            errs.append(f"aside.textform data-src={s.group(1)!r} -- use one of "
                        f"{', '.join(SOURCES)}")
    return errs
