# {{BOOK}} Study — Style Reference

{{BOOK}}'s differences from `fragment-contract.md` (shared, read first). This
file wins. ✎ marks what the book decides. A book may instead keep a full
contract here.

## Components ✎

Optional components on: echo, list (`book.json` `"components"`; markup in
`components-reference.md`). Note here where this book uses each, and which
handoff box kinds it has.

<!-- lang: hebrew -->
## Hebrew in English ✎

**Transliteration** follows core's Hebrew adapter (`biblecore/lang/hebrew.py`):
diacritic only where the plain letter is already claimed (`ḥ ṭ ś`, `ʾ`/`ʿ`);
no vowel length; no spirantization; dagesh forte doubles; divine name `YHWH`,
rendered **Yahweh**.

**Translation.** Fresh, wooden-but-readable rendering from the Hebrew, not a
polish of an existing English version. Creative, intentional glosses
encouraged.

**Ids.** One root often spans several Strong's numbers, and one number can
bundle senses worth splitting. Bare id (`2416`) claims every lexeme under the
number; suffixed id (`2416e`) claims exactly one.

## Judgment ✎

- Structure markers: Masoretic paragraph breaks (`candidate-boundaries.md`).
- Names are joined by hand: place-name wordplay is real, Strong's etymology
  unreliable.
- ✎ Genre cautions (lists, law, poetry, …): add as units surface them.
<!-- /lang -->
<!-- lang: greek -->
## Greek in English ✎

**Transliteration** follows core's Greek adapter (`biblecore/lang/greek.py`):
η → `ē`, ω → `ō`; `th ph ch ps` for θ φ χ ψ; `y` for υ except in `ou au eu`;
γγ/γκ → `ng`/`nk`; rough breathing → initial `h`, initial ρ → `rh`; accents,
smooth breathing, iota subscript dropped. *kyrios* standing for the divine
name → **Yahweh**. A Hebrew word uses the Hebrew scheme (`ḥ ṭ ś`, `ʾ`/`ʿ`, no
vowel length).

**Translation.** Fresh, wooden-but-readable rendering from the Greek (SBLGNT),
not a polish of an existing English version. Creative, intentional glosses
encouraged.

**Ids.** Lemma ids are transliterated lemmas (`klēronomeō`), a digit only
where two lemmas share a spelling (`tis`, `tis2`). One root often spans
several lemmas.

## Judgment ✎

- Structure markers: the book's own formulae, transitions, changes of scene
  or speaker.
- Names are joined by hand: a Greek name often carries a Hebrew one (*Iēsous*
  is *Yehoshua*); say so where it matters.
- ✎ Genre cautions. Keep what fits, add as units surface them:
  - Gospels: a difference from a parallel is evidence about this book's
    emphasis, not the whole reading. Compare where it illuminates.
  - Old Testament quotations often follow the Septuagint; say which the
    wording follows when it matters.
  - Letters: follow the argument. Connecting words carry the structure; a
    unit ends where a step of the argument does.
  - Apocalyptic: trace images in the Prophets before reading them as code for
    later events.
<!-- /lang -->

## Unit map ✎

From the project side as `{{SLUG}}-literary-unit-map.md`.
`python -m biblecore units-from-map` loads its **Overview** table; keep this
shape:

    | # | Passage | Working title |
    |---|---|---|
    | | **PART ONE — Label (1:1–25:18)** | |
    | | *I. Label (1:1–10:10)* | |
    | 01 | 1:1–54 | Title |
<!-- lang: hebrew -->
    | 17 | 16:36–17:13 [Heb 17:1–28] | Title |

Bold row opens an outer grouping, italic an inner one; both optional. Passages
in English numbering, Hebrew difference in `[Heb ...]`.
<!-- /lang -->
<!-- lang: greek -->
    | 02 | 1:18–2:23 | Title |

Bold row opens an outer grouping, italic an inner one; both optional. Passages
in English numbering, which the SBLGNT shares.
<!-- /lang -->
Renumbering after units ship means editing `threads.json` opens/payoffs, every
`retro` entry and every fragment's meta block: confirm the map before unit 1.
