"""A small laws file for the tests (not book data): the release of a bound
Hebrew, as Exod 21, Lev 25 and Deut 15 state it. Differences and reasons are
the text's own words; the real file is biblecore/laws.json."""
import copy

SLAVE = {
    "id": "release-of-slaves",
    "title": "Release of a bound Hebrew",
    "note": "A kinsman who has to serve another, and when he goes free.",
    "passages": [
        {"ref": "Exod 21:2–6",
         "summary": "A Hebrew slave serves six years and goes out free in the seventh, without payment.",
         "differences": ["Speaks of a man only; if he refuses to go out, his ear is pierced at the door and he serves for life."],
         "reasons": [{"at": "Exod 21:5", "why": "The slave says: I love my master, my wife and my children; I will not go out free."}]},
        {"ref": "Lev 25:39–43",
         "summary": "A kinsman who sells himself because of poverty is not made to serve as a slave.",
         "differences": ["He serves as a hired worker, and goes out at the jubilee, not in the seventh year."],
         "reasons": [{"at": "Lev 25:42", "why": "They are my servants, whom I brought out of the land of Egypt; they shall not be sold as slaves."}],
         "footnote": "Whether the jubilee year overrides the seventh year is argued."},
        {"ref": "Deut 15:12–18",
         "summary": "A Hebrew man or woman who is sold serves six years and is sent out free in the seventh.",
         "differences": ["Names a Hebrew woman beside the man.",
                         "Requires a gift from the flock, threshing floor and winepress when he is sent out."],
         "reasons": [{"at": "Deut 15:15", "why": "You were a slave in the land of Egypt and the Lord your God redeemed you."}]},
    ],
}

SECOND = {
    "id": "first-fruits",
    "title": "First fruits",
    "passages": [
        {"ref": "Exod 23:19", "summary": "Bring the best first fruits of the ground to the house of the Lord.",
         "differences": ["A single command, with no ritual."]},
        {"ref": "Deut 26:1–11", "summary": "Bring first fruits in a basket and say the creed before the Lord.",
         "differences": ["Adds the basket and a spoken confession."]},
    ],
}


def data():
    return {"version": 1, "laws": [copy.deepcopy(SLAVE), copy.deepcopy(SECOND)]}


def box(anchor="15:12", law="release-of-slaves", at="Deut 15:12–18", rows=None):
    """A lawparallel box as a Deuteronomy unit would carry it."""
    if rows is None:
        rows = [
            ("Exod 21:2–6", "Six years he serves; in the seventh he goes out free.",
             SLAVE["passages"][0]["differences"][0], SLAVE["passages"][0]["reasons"][0]["why"]),
            ("Lev 25:39–43", "Not as a slave, but as a hired worker, until the jubilee.",
             SLAVE["passages"][1]["differences"][0], None),
        ]
    out = [f'<aside class="lawparallel" data-anchor="{anchor}" data-law="{law}" data-at="{at}">',
           '<h4><span class="par-title">Release of a bound Hebrew</span></h4>']
    for src, txt, diff, why in rows:
        out.append(f'<div class="row"><span class="src">{src}</span><span class="txt">{txt}</span>'
                   f'<span class="diff">{diff}</span>' + (f'<span class="why">{why}</span>' if why else "")
                   + "</div>")
    out.append('<p class="take">Each place sends him out free; they differ on when and with what.</p></aside>')
    return "\n".join(out)


def unit(aside=None):
    return ('<article class="unit" data-unit="1">\n'
            '<p class="v"><span class="n">12</span> If your kinsman is sold to you, he serves you six years.</p>\n'
            + (aside if aside is not None else box()) + "\n</article>\n")
