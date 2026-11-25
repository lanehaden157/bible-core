"""Verse-keyed reads of the book and its sources, in pieces small enough to open.

    python tools/kit.py sources                    # keys, labels, section counts
    python tools/kit.py words 1:1-9                # per verse: English, words (translit, lemma, gloss, parsing), LXX English
    python tools/kit.py parts N [--cap 80]         # the unit's "whole" sources as files <= cap KB
    python tools/kit.py keyverses N [--top 20]     # candidate key verses from work/NN/pack.md, most signals first
    python tools/kit.py extra N [--key 1:4,1:9]    # the "voices" sources over the unit (only sections touching the key verses with --key), one file each
    python tools/kit.py grep N TERM [TERM ...]     # every other source: only the lines where a term occurs, to work/NN/grep.md
    python tools/kit.py range 1:1-9 [--source a,b] [--cap 28] [--out FILE]
    python tools/kit.py bible EXO 29:38-42 [--lxx] # WEB (or Brenton's LXX English) for any book
    python tools/kit.py calls N                    # the Calls for Lane section of work/NN/calls.md

Vendored from bible-core (studio); the book's copy is overwritten on sync.
Ranges: C:V, C:V-V, C:V-C:V, English numbering. Book codes are the WEB's
(GEN EXO LEV NUM DEU JOS ... PSA ISA JER EZE ... MAT MAR LUK JOH ... REV).
A source key also matches its numbered volumes (`milgrom` = milgrom-1, -2, -3).
Reading rank: "whole" sources (`parts`), then "voices" (`extra`, key verses; `keyverses` suggests them), then every other source (`grep`).
Settings: book.json "studio" {"whole": [keys read whole per unit], "voices": [keys read by key verses],
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


def voice_keys():
    return expand(STUDIO.get("voices", []))


def rest_keys():
    taken = set(whole_keys()) | set(voice_keys())
    return [k for k in all_keys() if k not in taken]


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
    whole, voices = set(whole_keys()), set(voice_keys())
    for k in all_keys():
        recs = records(k)
        n_intro = sum(1 for x in recs if (x["s"], x["e"]) == INTRO)
        tier = " (whole)" if k in whole else " (voice)" if k in voices else ""
        print(f"{k}{tier}: {len(recs)} sections"
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


def pack_text(n):
    f = ROOT / "work" / f"{n:02d}" / "pack.md"
    if not f.exists():
        sys.exit(f"{f.relative_to(ROOT).as_posix()} missing: run `python -m biblecore unit-pack {n} --out work/{n:02d}/pack.md`")
    return f.read_text("utf-8")


def section(text, head):
    m = re.search(rf"^#+ {head}.*?$(.*?)(?=^#{{1,3}} |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def map_verses(line, lo, hi):
    """Verses a map bullet names (C:V, C:V-V, C:V-C:V, 'vv. 3-5'), kept inside the unit."""
    out = set()
    for m in re.finditer(rf"(\d+):(\d+)(?:\s*{DASH}\s*(?:(\d+):)?(\d+))?", line):
        c, a = int(m.group(1)), int(m.group(2))
        c2 = int(m.group(3)) if m.group(3) else c
        b = int(m.group(4)) if m.group(4) else a
        if c2 == c:
            out.update((c, k) for k in range(a, b + 1))
        else:
            out.update([(c, a), (c2, b)])
    for m in re.finditer(rf"\bvv?\.\s*(\d+)(?:\s*{DASH}\s*(\d+))?", line):
        c = lo // 1000
        a = int(m.group(1))
        out.update((c, k) for k in range(a, int(m.group(2) or a) + 1))
    return {x for x in out if lo <= v(*x) <= hi}


def cmd_keyverses(n, top=20):
    """Candidates for `extra --key`: the verses where a tracked thread opens or pays off,
    verses holding the pack's rare-word and phrase leads, verses a map bullet names.
    Pair leads ("two rare words in a Torah verse") count once per verse, however many."""
    lo, hi = unit_range(n)
    text = pack_text(n)
    sig = {}

    def add(c, k, kind):
        if lo <= v(c, k) <= hi:
            sig.setdefault((c, k), []).append(kind)

    for line in section(text, "Tracked threads in this unit").splitlines():   # thread opens
        m = re.match(r"\|\s*`([^`]+)`\s*\|.*?\|\s*(\d+):(\d+) \(unit \d+\)\s*\|\s*yes\s*\|", line)
        if m:
            add(int(m.group(2)), int(m.group(3)), f"opens {m.group(1)}")
    tj = ROOT / "data" / "threads.json"                                       # thread payoffs
    if tj.exists():
        for t in json.loads(tj.read_text("utf-8")).get("threads", []):
            for p in t.get("payoffs") or []:
                m = re.match(r"(\d+):(\d+)", str(p.get("ref", "")))
                if p.get("unit") == n and m:
                    add(int(m.group(1)), int(m.group(2)), f"payoff {t['id']}")
    leads = [("Shared phrases", "phrase"), ("Rare words together", "pair"), (r"Rare words \(", "rare")]
    for head, kind in leads:
        body = section(text, head)
        pairs = set()
        for line in body.splitlines():
            if not line.startswith("- **") or " — " not in line:
                continue
            refs = re.findall(r"(\d+):(\d+)", line.rsplit(" — ", 1)[1].split(";")[0])
            word = re.match(r"- \*\*(.*?)\*\*", line).group(1)
            for c, k in refs:
                if kind == "pair":
                    pairs.add((int(c), int(k)))
                else:
                    add(int(c), int(k), f"{kind} {word}")
        for c, k in pairs:
            add(c, k, "pair leads")
    for line in section(text, "Map entry").splitlines():                       # map bullets
        if line.startswith("- "):
            for c, k in map_verses(line, lo, hi):
                add(c, k, "map")
    if not sig:
        print("[no signals: the pack has no thread opens, leads or map bullets for this unit]")
        return
    rows = sorted(sig.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:top]
    for (c, k), kinds in rows:
        print(f"{c}:{k}  {len(kinds)}  " + "; ".join(dict.fromkeys(kinds)))
    pick = [x for x in rows if len(x[1]) >= 3] or rows[:8]
    keys = ",".join(f"{c}:{k}" for (c, k), _ in sorted(pick))
    print(f"\nStart from: python tools/kit.py extra {n} --key {keys}")


def cmd_extra(n, key=None):
    r = unit_range(n)
    ks = [rng(x) for x in key.split(",")] if key else None
    out = ROOT / "work" / f"{n:02d}" / "extra"
    out.mkdir(parents=True, exist_ok=True)
    lab = labels()
    for k in voice_keys():
        recs = hits(k, r)
        if ks:
            recs = [x for x in recs if any(overlaps((x["s"], x["e"]), q) for q in ks)]
        if recs:
            f = out / f"{k}.md"
            write(f, f"# {k}, unit {n}\n\n{lab.get(k, '')}\n\n" + block(k, recs))
            print(f"{f.relative_to(ROOT).as_posix()}  {f.stat().st_size // 1000} KB")


def cmd_grep(n, terms, cap=40):
    r = unit_range(n)
    pat = re.compile("|".join(re.escape(t) for t in terms), re.I)
    text, seen = "", []
    for k in rest_keys():
        recs = hits(k, r)
        seen.append(f"{k} ({len(recs)})")
        for x in recs:
            lines = x["text"].split("\n")
            idx = [i for i, l in enumerate(lines) if pat.search(l)][:6]
            if idx:
                text += f"## {k}: {x['title']} [{fmt((x['s'], x['e']))}]\n\n"
                text += "\n".join(f"- {lines[i].strip()[:400]}" for i in idx) + "\n\n"
    f = ROOT / "work" / f"{n:02d}" / "grep.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    head = f"# grep, unit {n}: {', '.join(terms)}\n\nSources scanned (sections in range): {'; '.join(seen)}\n\n"
    write(f, (head + text)[: cap * 1000])
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
    elif c == "keyverses":
        cmd_keyverses(int(pos[1]), int(opt.get("--top", 20)))
    elif c == "extra":
        cmd_extra(int(pos[1]), opt.get("--key"))
    elif c == "grep":
        cmd_grep(int(pos[1]), pos[2:])
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
