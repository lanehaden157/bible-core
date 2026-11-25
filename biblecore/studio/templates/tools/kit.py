"""Verse-keyed reads of the book and its sources, in pieces small enough to open.

    python tools/kit.py sources                    # keys, labels, section counts
    python tools/kit.py words 1:1-9                # per verse: English, words (translit, lemma, gloss, parsing), LXX English
    python tools/kit.py parts N [--cap 80]         # the unit's "whole" sources as files <= cap KB
    python tools/kit.py extra N                    # every other source over the unit, one file each
    python tools/kit.py range 1:1-9 [--source a,b] [--cap 28] [--out FILE]
    python tools/kit.py bible EXO 29:38-42 [--lxx] # WEB (or Brenton's LXX English) for any book
    python tools/kit.py calls N                    # the Calls for Lane section of work/NN/calls.md

Vendored from bible-core (studio); the book's copy is overwritten on sync.
Ranges: C:V, C:V-V, C:V-C:V, English numbering. Book codes are the WEB's
(GEN EXO LEV NUM DEU JOS ... PSA ISA JER EZE ... MAT MAR LUK JOH ... REV).
A source key also matches its numbered volumes (`milgrom` = milgrom-1, -2, -3).
Settings: book.json "studio" {"whole": [keys read whole per unit],
"lxx_numbering": "hebrew" when Brenton follows the Hebrew verse numbers}.
`words` prints no native script: transliteration only.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # Windows console default is cp1252
sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_sources import DASH, INTRO, book_cfg, eng_to_heb, overlaps, parse_range, v  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEC = ROOT / "sources" / "sections"
TEXT = ROOT / "sources" / "text"
if not SEC.exists():   # inside a worktree without the copy: use the main checkout's
    for up in ROOT.parents:
        if (up / "sources" / "sections").exists():
            SEC, TEXT = up / "sources" / "sections", up / "sources" / "text"
            break
CAP_KB = 28          # range output (shell output stops near 30k characters)
PARTS_KB = 80        # comfortably opened with Read
CFG = book_cfg()
STUDIO = CFG.get("studio") if isinstance(CFG.get("studio"), dict) else {}
WEB_CODES = {"Gen": "GEN", "Exod": "EXO", "Lev": "LEV", "Num": "NUM", "Deut": "DEU", "Josh": "JOS",
             "Judg": "JDG", "Ruth": "RUT", "Matt": "MAT", "Mark": "MAR", "Luke": "LUK", "John": "JOH"}
CODE = WEB_CODES.get(CFG.get("osis", ""), CFG.get("osis", "").upper()[:3])


def rng(s):
    r = parse_range(s)
    if not r:
        sys.exit(f"bad range: {s}")
    return r


def fmt(r):
    if tuple(r) == INTRO:
        return "intro"
    e = r[1] % 1000
    return f"{r[0] // 1000}:{r[0] % 1000}-{r[1] // 1000}:{'end' if e == 999 else e}"


def unit_range(n):
    for u in json.loads((ROOT / "data" / "units.json").read_text("utf-8"))["units"]:
        if u["n"] == n:
            m = re.search(rf"(\d+:\d+\s*(?:{DASH}\s*(?:\d+:)?\d+)?)", u["passage"])
            return rng(m.group(1))
    sys.exit(f"no unit {n} in data/units.json")


def all_keys():
    return sorted(f.stem for f in SEC.glob("*.jsonl"))


def expand(names):
    keys = all_keys()
    out = []
    for n in names:
        hit = [k for k in keys if k == n or re.fullmatch(rf"{re.escape(n)}-\d+", k)]
        if not hit:
            print(f"[no source {n!r}; have: {', '.join(keys)}]")
        out += hit
    return list(dict.fromkeys(out))


def whole_keys():
    return expand(STUDIO.get("whole", []))


def records(key):
    f = SEC / f"{key}.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text("utf-8").splitlines() if l.strip()]


def labels():
    f = SEC / "labels.json"
    return json.loads(f.read_text("utf-8")) if f.exists() else {}


def pieces(text, cap):
    """Split an oversize text at paragraph breaks into <= cap bytes."""
    if len(text.encode()) <= cap:
        return [text]
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if cur and len((cur + para).encode()) > cap:
            out.append(cur)
            cur = ""
        cur += para + "\n\n"
    return out + ([cur] if cur.strip() else [])


def hits(key, r):
    return [x for x in records(key) if (x["s"], x["e"]) != INTRO and overlaps((x["s"], x["e"]), r)]


def block(key, recs):
    return "".join(f"## {key}: {x['title']} [{fmt((x['s'], x['e']))}]\n\n{x['text']}\n\n" for x in recs)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ---- commands -----------------------------------------------------------
def cmd_sources():
    lab = labels()
    whole = set(whole_keys())
    for k in all_keys():
        recs = records(k)
        n_intro = sum(1 for x in recs if (x["s"], x["e"]) == INTRO)
        print(f"{k}{' (whole)' if k in whole else ''}: {len(recs)} sections"
              f"{f', {n_intro} intro' if n_intro else ''}. {lab.get(k, '')}")


def cmd_parts(n, cap):
    r = unit_range(n)
    out = ROOT / "work" / f"{n:02d}" / "parts"
    out.mkdir(parents=True, exist_ok=True)
    lab = labels()
    for key in whole_keys():
        recs = hits(key, r)
        if not recs:
            continue
        parts, cur, titles = [], "", []
        for x in recs:
            for p in pieces(x["text"], cap * 1000):
                if cur and len((cur + p).encode()) > cap * 1000:
                    parts.append((cur, titles))
                    cur, titles = "", []
                cur += p + "\n\n---\n\n"
                titles.append(f"{x['title']} [{fmt((x['s'], x['e']))}]")
        if cur:
            parts.append((cur, titles))
        for k, (text, ts) in enumerate(parts, 1):
            f = out / f"{key}-{k}.md"
            head = (f"# {key} part {k}/{len(parts)}, unit {n}\n\n{lab.get(key, '')}\n\n"
                    f"Holds: {'; '.join(dict.fromkeys(ts))}\n\n---\n\n")
            write(f, head + text)
            print(f"{f.relative_to(ROOT).as_posix()}  {f.stat().st_size // 1000} KB")


def cmd_extra(n):
    r = unit_range(n)
    out = ROOT / "work" / f"{n:02d}" / "extra"
    out.mkdir(parents=True, exist_ok=True)
    lab, whole = labels(), set(whole_keys())
    for key in all_keys():
        if key in whole:
            continue
        recs = hits(key, r)
        if recs:
            f = out / f"{key}.md"
            write(f, f"# {key}, unit {n}\n\n{lab.get(key, '')}\n\n" + block(key, recs))
            print(f"{f.relative_to(ROOT).as_posix()}  {f.stat().st_size // 1000} KB")


def cmd_range(r, keys, cap, out=None):
    text = "".join(block(k, hits(k, r)) for k in keys)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        write(Path(out), text)
        print(f"{out}  {len(text.encode()) // 1000} KB")
        return
    b = text.encode()
    print(b[:cap * 1000].decode("utf-8", errors="ignore") or "[nothing in range]")
    if len(b) > cap * 1000:
        print(f"\n[cut at {cap} KB of {len(b) // 1000}: narrow the range, pass --source, or --out FILE and Read it]")


def bible_lines(code, r, lxx):
    f = TEXT / ("brenton-lxx.txt" if lxx else "web-bible.txt")
    if not f.exists():
        return [(0, f"[{f.name} missing from sources/text/]")]
    table = eng_to_heb() if lxx and code == CODE and STUDIO.get("lxx_numbering") == "hebrew" else {}
    want = {}
    for c in range(r[0] // 1000, r[1] // 1000 + 1):
        for n in range(1, 200):
            k = v(c, n)
            if r[0] <= k <= r[1]:
                want[table.get(k, k)] = k
    out = []
    for line in f.read_text("utf-8").splitlines():
        m = re.match(r"(\w{3}) (\d+):(\d+) (.*)", line)
        if m and m.group(1) == code:
            k = v(int(m.group(2)), int(m.group(3)))
            if k in want:
                e = want[k]
                note = f" [LXX {m.group(2)}:{m.group(3)}]" if e != k else ""
                out.append((e, f"{code} {e // 1000}:{e % 1000}{note} {m.group(4)}"))
    return sorted(out)


def cmd_bible(code, r, lxx):
    print("\n".join(t for _, t in bible_lines(code.upper(), r, lxx)))


def cmd_words(r):
    lem = json.loads((ROOT / "data" / "lemmas.json").read_text("utf-8")).get("lemmas", {})
    lxx = dict(bible_lines(CODE, r, True))
    for c in range(r[0] // 1000, r[1] // 1000 + 1):
        wf, ef = ROOT / "data" / "words" / f"{c}.json", ROOT / "data" / "web" / f"{c}.json"
        if not wf.exists():
            continue
        words = json.loads(wf.read_text("utf-8"))["verses"]
        eng = json.loads(ef.read_text("utf-8"))["verses"] if ef.exists() else {}
        for vs in sorted(words, key=int):
            k = v(c, int(vs))
            if not r[0] <= k <= r[1]:
                continue
            print(f"\n{c}:{vs}  {eng.get(vs, '')}")
            row = []
            for w in words[vs]:
                g = lem.get(w.get("l", ""), {}).get("g", "")
                row.append(f"{w['t']} [{w.get('l', '')}{' ' + g.split(';')[0] if g else ''}; {w.get('m', '')}]")
            print("   " + " | ".join(row))
            if k in lxx:
                print(f"   LXX: {lxx[k].split(' ', 2)[2]}")


def cmd_calls(n):
    h = ROOT / "work" / f"{n:02d}" / "calls.md"
    m = re.search(r"^## Calls for Lane.*?(?=^## |\Z)", h.read_text("utf-8"), re.M | re.S)
    print(m.group(0).strip() if m else "no Calls for Lane section")


def main(a):
    if not a:
        sys.exit(__doc__)
    opt = {a[i]: a[i + 1] for i in range(len(a) - 1) if a[i].startswith("--") and a[i] != "--lxx"}
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and not (i and a[i - 1] in opt)]
    c = pos[0]
    if c == "sources":
        cmd_sources()
    elif c == "words":
        cmd_words(rng(pos[1]))
    elif c == "parts":
        cmd_parts(int(pos[1]), int(opt.get("--cap", PARTS_KB)))
    elif c == "extra":
        cmd_extra(int(pos[1]))
    elif c == "range":
        keys = expand(opt["--source"].split(",")) if "--source" in opt else all_keys()
        cmd_range(rng(pos[1]), keys, int(opt.get("--cap", CAP_KB)), opt.get("--out"))
    elif c == "bible":
        cmd_bible(pos[1], rng(pos[2]), "--lxx" in a)
    elif c == "calls":
        cmd_calls(int(pos[1]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
