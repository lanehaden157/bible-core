# {{BOOK}}

@biblecore/BOOK_CLAUDE.md

Above = shared guide (commands, files, chat side, threads). Below = what
{{BOOK}} does differently; it wins.

## Corpus

<!-- lang: hebrew -->
✎ morphhb pin, the counts `python -m biblecore corpus` reports, the check
against a printed edition. Count drifts on re-fetch → flag loudly.
<!-- /lang -->
<!-- lang: greek -->
MorphGNT and LXX are git-ignored. Fresh clone → `python -m biblecore fetch`
restores them at the pinned versions and checks every sha1. sha1 failure =
wrong corpus: flag loudly, don't build on it.

✎ MorphGNT pin (book.json `corpus.pin`), the counts `python -m biblecore
corpus` reports, the check against a printed SBLGNT.
<!-- /lang -->
