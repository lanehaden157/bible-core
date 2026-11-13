"""Sample ritual strips for the tests (not a Leviticus unit): Lev 1:3-9 and
Lev 16. Each step is (verse, who, zone, text), in the order the verses give,
worded with Leviticus' decided terms (translation-choices.md). Where a verse
leaves the place or the doer unsaid the zone is the one it implies; those
steps are listed in UNSAID so the test and the report can name them."""

LEV1 = [
    ("1:3", "offerer", "entrance", "Brings a male without blemish to the entrance of the Tent of Meeting."),
    ("1:4", "offerer", "entrance", "Lays his hand on the head of the going up offering; it is accepted for him, to cover for him."),
    ("1:5", "offerer", "court", "Slaughters the bull before the Lord."),
    ("1:5", "priest", "altar", "The sons of Aaron bring the blood near and dash it around on the altar."),
    ("1:6", "offerer", "court", "Flays the going up offering and cuts it into its pieces."),
    ("1:7", "priest", "altar", "The sons of Aaron put fire on the altar and lay wood in order on the fire."),
    ("1:8", "priest", "altar", "They lay the pieces, the head and the suet in order on the wood."),
    ("1:9", "offerer", "court", "Washes its entrails and its legs with water."),
    ("1:9", "priest", "altar", "The priest turns all of it into smoke on the altar: a going up offering, a fire offering, an aroma of rest for the Lord."),
]

LEV16 = [
    ("16:4", "high-priest", "court", "Bathes, and puts on the holy linen tunic, breeches, sash and turban."),
    ("16:5", "people", "court", "The community of Israel gives two goats for a sin offering and a ram for a going up offering."),
    ("16:6", "high-priest", "court", "Brings the bull near, the sin offering for himself."),
    ("16:7", "high-priest", "entrance", "Has the two goats stand before the Lord at the entrance of the Tent of Meeting."),
    ("16:8", "high-priest", "entrance", "Casts lots over the two goats: one lot for the Lord, one for Azazel."),
    ("16:9", "high-priest", "entrance", "Brings near the goat the Lord's lot fell on and makes it a sin offering."),
    ("16:10", "high-priest", "entrance", "The goat Azazel's lot fell on stands alive before the Lord, to cover over it, to send it to Azazel in the wilderness."),
    ("16:11", "high-priest", "court", "Slaughters the bull of the sin offering for himself and covers for himself and his house."),
    ("16:12", "high-priest", "altar", "Takes a censer full of coals of fire from the altar before the Lord, and two handfuls of fine fragrant incense."),
    ("16:12–13", "high-priest", "most-holy", "Brings them inside the curtain and puts the incense on the fire before the Lord, so the cloud of incense covers the place of covering."),
    ("16:14", "high-priest", "most-holy", "Takes some of the bull's blood and sprinkles it with his finger on the east face of the place of covering, and seven times before it."),
    ("16:15", "high-priest", "court", "Slaughters the goat of the sin offering for the people."),
    ("16:15", "high-priest", "most-holy", "Brings its blood inside the curtain and does with it as he did with the bull's blood."),
    ("16:16", "high-priest", "most-holy", "Covers for the holy place, because of the uncleanness of the Israelites and their breaking away."),
    ("16:16", "high-priest", "holy-place", "Does the same for the Tent of Meeting, which dwells with them in the midst of their uncleanness."),
    ("16:18", "high-priest", "altar", "Goes out to the altar before the Lord and covers for it: puts some of the bull's blood and the goat's blood on its horns all around."),
    ("16:19", "high-priest", "altar", "Sprinkles some of the blood on it with his finger seven times and makes it clean."),
    ("16:20", "high-priest", "court", "When he has finished covering for the holy place, the Tent of Meeting and the altar, he brings near the live goat."),
    ("16:21", "high-priest", "court", "Lays both hands on the live goat's head, confesses over it all the iniquities of the Israelites and puts them on its head."),
    ("16:21–22", "people", "outside-camp", "A man appointed leads it away into the wilderness; the goat carries all their iniquities to a land cut off."),
    ("16:23", "high-priest", "holy-place", "Goes into the Tent of Meeting, takes off the linen garments and leaves them there."),
    ("16:24", "high-priest", "court", "Bathes his body in water, puts on his garments, goes out, and makes his going up offering and the people's, covering for himself and the people."),
    ("16:25", "high-priest", "altar", "Turns the fat of the sin offering into smoke on the altar."),
    ("16:26", "people", "camp", "The man who led the goat to Azazel washes his clothes and bathes, and afterward comes into the camp."),
    ("16:27", "priest", "outside-camp", "The bull and the goat of the sin offering, whose blood was brought in to cover in the holy place, are carried outside the camp and their skins, flesh and dung burned."),
    ("16:28", "priest", "camp", "The one who burns them washes his clothes and bathes, and afterward comes into the camp."),
    ("16:29", "people", "camp", "In the seventh month, on the tenth day, they afflict themselves and do no work."),
]

# the doer or the place is not stated in these verses (the zone/who is implied)
UNSAID = {
    "1:5 slaughter": "place: 'before the Lord'; 1:11 gives the altar's north side only for the flock",
    "1:6": "place not stated",
    "1:9 wash": "place not stated",
    "16:4": "place of the bath not stated (16:24 says 'a holy place')",
    "16:5": "place not stated",
    "16:6": "place not stated",
    "16:11": "place not stated",
    "16:15 slaughter": "place not stated",
    "16:20": "place not stated",
    "16:21": "place not stated",
    "16:24": "the bath: 'in a holy place', not named",
    "16:27": "'one shall carry': doer not stated (priest by 4:12's parallel)",
    "16:28": "doer: 'the one who burns them'",
}


def strip(title, ref, steps, verses=None):
    d = f' data-verses="{verses}"' if verses else ""
    items = "\n".join(
        f'    <li data-who="{who}" data-at="{at}">{text} <sup>{v}</sup></li>' for v, who, at, text in steps)
    return (f'<section class="block ritual"{d}>\n  <h2>{title} <span class="cap">· {ref}</span></h2>\n'
            f'  <ol class="steps">\n{items}\n  </ol>\n</section>\n')


def lev1():
    return strip("The going up offering of the herd", "1:3–9", LEV1, "1:3–9")


def lev16():
    return strip("The Day of Coverings", "16:4–29", LEV16)
