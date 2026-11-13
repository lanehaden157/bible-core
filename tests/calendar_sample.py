"""A small calendar file for the tests (not book data): Passover and
Unleavened Bread as Lev 23, Num 28 and Deut 16 give them. The real file is
biblecore/calendar.json."""
import copy

PASSOVER = {
    "id": "passover-unleavened-bread",
    "title": "Passover and Unleavened Bread",
    "passages": [
        {"ref": "Lev 23:5–8",
         "date": "first month, fourteenth day, at twilight; the next day begins seven days of unleavened bread",
         "requires": ["Passover to the Lord.",
                      "Eat unleavened bread seven days; no ordinary work on the first and seventh days.",
                      "Bring a food offering to the Lord for seven days."]},
        {"ref": "Num 28:16–25",
         "date": "first month, fourteenth day",
         "requires": ["Each day of the seven: a food offering, a going up offering of two bulls, one ram and seven lambs, with a goat as a sin offering."]},
        {"ref": "Deut 16:1–8",
         "date": "the month of Abib, at night",
         "requires": ["Sacrifice the Passover from flock or herd at the place the Lord chooses, in the evening at sunset.",
                      "Eat unleavened bread seven days; none of the flesh is left until morning."]},
    ],
}

SECOND = {
    "id": "weeks",
    "title": "Weeks",
    "passages": [
        {"ref": "Lev 23:15–21", "date": "seven weeks, then fifty days",
         "requires": ["Bring two loaves of fine flour, baked with leaven."]},
        {"ref": "Deut 16:9–12",
         "requires": ["Count seven weeks and keep the feast with a freewill offering."]},
    ],
}


def data():
    return {"version": 1, "feasts": [copy.deepcopy(PASSOVER), copy.deepcopy(SECOND)]}


def box(anchor="23:5", feast="passover-unleavened-bread", rows=None):
    p = PASSOVER["passages"]
    if rows is None:
        rows = [(p[0]["ref"], p[0]["date"], p[0]["requires"][:1]),
                (p[2]["ref"], p[2]["date"], p[2]["requires"][:1])]
    out = [f'<aside class="calendar" data-anchor="{anchor}" data-feast="{feast}">',
           '<h4><span class="cal-title">Passover and Unleavened Bread</span></h4>']
    for ref, date, reqs in rows:
        out.append(f'<div class="row"><span class="src">{ref}</span>'
                   + (f'<span class="date">{date}</span>' if date else "")
                   + "".join(f'<span class="req">{r}</span>' for r in reqs) + "</div>")
    out.append('<p class="take">The same feast, dated in each place.</p></aside>')
    return "\n".join(out)


def unit(aside=None):
    return ('<article class="unit" data-unit="1">\n'
            '<p class="v"><span class="n">5</span> In the first month, on the fourteenth day, is the Passover.</p>\n'
            + (aside if aside is not None else box()) + "\n</article>\n")
