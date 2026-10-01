"""Put a Greek book's corpus on disk: pinned downloads with sha1 checks.

    python -m biblecore fetch            # fetch what's missing; check every file
    python -m biblecore fetch --force    # download everything again
    python -m biblecore fetch --check    # check the files on disk, no network

The Greek counterpart of `npm ci` for a Hebrew book (Lane's L1, 2026-10-01):
the pins live here, in the vendored core, so a book's corpus moves only when
its core does. Destinations are the book's paths (`paths.morphgnt`,
`paths.lxx`), git-ignored in the book. A Hebrew book has nothing to fetch
(morphhb comes from npm, package.json pins it), so this is a no-op there.

Every file is checked against its sha1, whether it was just downloaded or
already there. A download that doesn't match is discarded; a file on disk
that doesn't match is reported and left alone (`--force` replaces it).
Either way the command exits 1, so a corrupted corpus never builds quietly.

What's fetched, and why all of it:
  * MorphGNT SBLGNT, all 27 books (~11 MB): the book's own words, and the
    rest of the NT for canon leads (leads.py). The lemma ids depend on it
    too: corpus/morphgnt.py numbers a shared transliteration (`tis`,
    `tis2`) by first appearance across every NT file on disk, so a book
    with fewer files could spell an id differently from another book.
  * CenterBLC's Text-Fabric LXX (Rahlfs 1935), the four feature files
    corpus/lxx.py reads (~15.5 MB): canon leads in the Greek Old Testament.
The morphological lexicon (lexemes.yaml, the interlinear's glosses) is not
fetched: tools/new_book.py copies core's sha1-checked copy into the book.
Pins, sizes and licences: bible-core/corpus/README.md. The pins are
Matthew's pipeline/fetch_corpus.py's; the sha1s were taken 2026-10-01 from
those commits and match Matthew's copies.
"""
import argparse
import hashlib
import os
import sys
import urllib.request

RAW = "https://raw.githubusercontent.com"

# name -> {repo, commit, dir (in the repo), path (the book.json paths key),
#          files {file name: sha1 of its bytes}}
SOURCES = {
    "morphgnt": {
        "repo": "morphgnt/sblgnt",
        "commit": "aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d",
        "dir": "",
        "path": "morphgnt",
        "files": {
            "61-Mt-morphgnt.txt": "5d95a94e0be33cda02891246feb47d16175f2e53",
            "62-Mk-morphgnt.txt": "921ce094b673277a2bb5dcd0744f5d8e0e912619",
            "63-Lk-morphgnt.txt": "55d391db1a4cdaba0a57047bd9126461218a304a",
            "64-Jn-morphgnt.txt": "c0f3971b7c951bbc32625b7be510577f321e2e09",
            "65-Ac-morphgnt.txt": "fb0c81c2be33407e0c3e80e8ff6cba32e04f2a53",
            "66-Ro-morphgnt.txt": "18da493cdd7be5e2b10fa9259d14c6e75627c6d5",
            "67-1Co-morphgnt.txt": "a3f185446882d0114848d0ff56d70e4774808a9f",
            "68-2Co-morphgnt.txt": "55ffcf6d24090352fd3377ceb7cdf98b2b6a4cc5",
            "69-Ga-morphgnt.txt": "fd2e54dbae40e2c6d05c591c7120f6c1bc5869ef",
            "70-Eph-morphgnt.txt": "bd4a11731a19a8f8d17c2748160d68f6aa836f55",
            "71-Php-morphgnt.txt": "b330374e4fd5f155124f3d963bb41d36b32c44a7",
            "72-Col-morphgnt.txt": "fa47911b45264484cf131789e78666d28a4985da",
            "73-1Th-morphgnt.txt": "9c01e58d7694a57b263a0daf30a17c44d470109d",
            "74-2Th-morphgnt.txt": "0c458170a6699657af84e2afe7919f8eb3968fa2",
            "75-1Ti-morphgnt.txt": "cdb139c83fafb5c09486b02cbfb0483aae3bbbe2",
            "76-2Ti-morphgnt.txt": "02ef59ffece94e160ad3e5b949c30cb5ab3a37c4",
            "77-Tit-morphgnt.txt": "03424257ed469178cb4c5aec8b18114d5f75b960",
            "78-Phm-morphgnt.txt": "df7ff0529391b80f62fbede0769ef94e490650e7",
            "79-Heb-morphgnt.txt": "897263ec2ecc6670681729f534cb16eb14d7e848",
            "80-Jas-morphgnt.txt": "14e6374c326d008955824540031b7c00cc82e14c",
            "81-1Pe-morphgnt.txt": "012876bc638bd521bd72a0f3012bb7832bfb6e1f",
            "82-2Pe-morphgnt.txt": "8ee19def54f56f2415842c5f59a62cf76a06ea1f",
            "83-1Jn-morphgnt.txt": "811d9147b5a8b194ec86f493772184c177c6a3c5",
            "84-2Jn-morphgnt.txt": "5b2491461f9ce65c4cb076830263c1172a297fcb",
            "85-3Jn-morphgnt.txt": "7300c2b28ee08b9d88b1bb280cd54203e75487c7",
            "86-Jud-morphgnt.txt": "181cbea5e6b8104ba0ecfa9e5c9db6333d71860a",
            "87-Re-morphgnt.txt": "dccec67d59eb5f5f6e91107c9fc11044ca5fb3b3",
        },
    },
    "lxx": {
        "repo": "CenterBLC/LXX",
        "commit": "4829f3746c84d75576702498e75a68856358f289",
        "dir": "tf/1935",
        "path": "lxx",
        "files": {
            "book.tf": "d6c21c5bac2b78e8793bd13c3f260b1307d49087",
            "chapter.tf": "dd03deeba24e75801bab96d77aa6f9340dc2f52b",
            "verse.tf": "e676ae45361f2e095e365c076ff175c337f2b176",
            "lex_utf8.tf": "06170879b06f23e2b666550d075637d250da03bc",
        },
    },
}
# which sources each language's books fetch
BY_LANGUAGE = {"greek": ("morphgnt", "lxx")}


def corpus_pin():
    """book.json's corpus "pin" for a Greek book (new_book.py writes it)."""
    return f"{SOURCES['morphgnt']['repo']}@{SOURCES['morphgnt']['commit'][:7]}"


def sha1_of(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def url_of(src, name, base=None):
    """The pinned URL of one file. `base` replaces the raw.githubusercontent
    root (the tests point it at a local folder with file://)."""
    parts = [base or RAW, src["repo"], src["commit"], src["dir"], name]
    return "/".join(p.strip("/") for p in parts if p)


def _download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "bible-core-fetch"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def fetch(b, force=False, check_only=False, base=None, log=print):
    """Fetch and check the book's corpus files. Returns a list of problems
    ([] == every file is in place and matches its pin)."""
    problems = []
    names = BY_LANGUAGE.get(b.language, ())
    if not names:
        log(f"nothing to fetch for a {b.language} book"
            + (" (morphhb comes from npm: package.json pins it)" if b.language == "hebrew" else ""))
        return problems
    got = ok = 0
    for name in names:
        src = SOURCES[name]
        folder = b.path(src["path"])
        for fname, want in src["files"].items():
            dest = os.path.join(folder, fname)
            rel = os.path.relpath(dest, b.root).replace(os.sep, "/")
            if os.path.exists(dest) and not force:
                have = sha1_of(dest)
                if have == want:
                    ok += 1
                else:
                    problems.append(f"{rel}: sha1 {have} != pinned {want} -- the file "
                                    f"on disk isn't the pinned one (corrupted or edited); "
                                    f"`python -m biblecore fetch --force` replaces it")
                continue
            if check_only:
                problems.append(f"{rel}: missing -- run `python -m biblecore fetch`")
                continue
            os.makedirs(folder, exist_ok=True)
            part = dest + ".part"
            url = url_of(src, fname, base)
            try:
                _download(url, part)
            except OSError as exc:
                problems.append(f"{rel}: download failed ({url}): {exc}")
                if os.path.exists(part):
                    os.remove(part)
                continue
            have = sha1_of(part)
            if have != want:
                os.remove(part)
                problems.append(f"{rel}: downloaded sha1 {have} != pinned {want} "
                                f"({url}); discarded")
                continue
            os.replace(part, dest)
            got += 1
            log(f"fetched {rel}")
    for name in names:
        src = SOURCES[name]
        log(f"{name}: {src['repo']}@{src['commit'][:7]} -> "
            f"{os.path.relpath(b.path(src['path']), b.root).replace(os.sep, '/')}")
    log(f"{got} fetched, {ok} already in place, {len(problems)} problem(s)")
    pin = (b.cfg.get("corpus") or {}).get("pin")
    if b.language == "greek" and pin and pin != corpus_pin():
        log(f"note: book.json corpus.pin is {pin!r}; this core fetches {corpus_pin()!r}")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m biblecore fetch",
                                 description="fetch a Greek book's pinned corpus (sha1-checked)")
    ap.add_argument("--force", action="store_true", help="download every file again")
    ap.add_argument("--check", action="store_true",
                    help="only check the files on disk against their sha1s (no network)")
    a = ap.parse_args(argv)
    from biblecore.book import book
    problems = fetch(book(), force=a.force, check_only=a.check)
    for p in problems:
        print("FAIL", p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
