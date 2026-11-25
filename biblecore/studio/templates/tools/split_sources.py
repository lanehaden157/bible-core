"""Index the sources by verse range: sources/marked/*.txt -> sources/sections/*.jsonl.

    python tools/split_sources.py            # every marked file
    python tools/split_sources.py rashi      # one key
    python tools/split_sources.py --check    # parse, report coverage, write nothing

Vendored from bible-core (studio); the book's copy is overwritten on sync.

A marked file is plain text with a header and `@@` section lines:

    #source: rashi
    #label: Rashi on Leviticus (Sefaria, tr. ...). Public domain.
    #numbering: hebrew        (optional; refs are the Hebrew/Masoretic ones)
    @@ intro | Introduction
    @@ 1:1-17 | The burnt offering
    @@ 5:20-26 | ...          (converted to English with <slug>-versification.md)

Range: C:V, C:V-V, C:V-C:V, C, C-C, or `intro` (no verses). Each section
becomes one record {s, e, title, text}; s/e = chapter*1000 + verse (a
whole-chapter end is verse 999; intro is 0-0). `tools/kit.py` reads them.
A book converter that can't write the marked format may write
sources/sections/<key>.jsonl itself (and its labels.json entry): this
script leaves files it didn't make alone.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources"
MARKED = SRC / "marked"
OUT = SRC / "sections"
DASH = "[-–—]"
INTRO = (0, 0)


def v(c, n):
    return c * 1000 + n


def overlaps(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def parse_range(s):
    """'21:18-22:46' | '19:1-12' | '23' | '24-25' | '1:1' -> (start, end); None if not a range."""
    s = s.strip().rstrip(".").replace(".", ":")
    m = re.fullmatch(rf"(\d+)(?::(\d+))?(?:\s*{DASH}\s*(\d+)(?::(\d+))?)?", s)
    if not m:
        return None
    c1, v1, x, y = m.groups()
    c1 = int(c1)
    if v1 is None:
        if y is not None:                      # '6-7:3': chapter to verse
            return v(c1, 1), v(int(x), int(y))
        return v(c1, 1), v(int(x) if x else c1, 999)
    start = v(c1, int(v1))
    if x is None:
        return start, start
    if y is None:
        return start, v(c1, int(x))
    return start, v(int(x), int(y))


def book_cfg():
    f = ROOT / "book.json"
    return json.loads(f.read_text("utf-8")) if f.exists() else {}


def heb_to_eng():
    """{hebrew v-key: english v-key} from the generated versification table
    (`<slug>-versification.md`, rows `| 6:1 | 5:20 |`). Empty = same numbering."""
    slug = book_cfg().get("slug", "")
    f = ROOT / f"{slug}-versification.md"
    out = {}
    if f.exists():
        for m in re.finditer(r"^\|\s*(\d+):(\d+)\s*\|\s*(\d+):(\d+)\s*\|", f.read_text("utf-8"), re.M):
            e1, e2, h1, h2 = map(int, m.groups())
            out[v(h1, h2)] = v(e1, e2)
    return out


def eng_to_heb():
    return {e: h for h, e in heb_to_eng().items()}


def to_english(r, table):
    if not table or r == INTRO:
        return r
    s = table.get(r[0], r[0])
    e = r[1]
    if e % 1000 == 999:                         # whole chapter: map its last listed verse
        last = [k for k in table if k // 1000 == e // 1000]
        e = table[max(last)] if last else e
    else:
        e = table.get(e, e)
    return s, max(s, e)


def parse_marked(path, table=None):
    """-> (meta dict, [((s, e), title, text)])."""
    meta, chunks, cur = {}, [], None
    for line in path.read_text("utf-8").split("\n"):
        if cur is None and (m := re.match(r"#(\w+):\s*(.*)", line)):
            meta[m.group(1)] = m.group(2).strip()
            continue
        if line.startswith("@@ "):
            if cur:
                chunks.append(cur)
            ref, _, title = line[3:].partition("|")
            ref = ref.strip()
            r = INTRO if ref.lower() == "intro" else parse_range(ref)
            if r is None:
                print(f"  {path.name}: bad range {ref!r}, kept as intro")
                r = INTRO
            cur = [r, title.strip() or ref, []]
            continue
        if cur:
            cur[2].append(line)
    if cur:
        chunks.append(cur)
    hebrew = meta.get("numbering", "english").lower() == "hebrew"
    t = (table if table is not None else heb_to_eng()) if hebrew else {}
    out = [(to_english(r, t), title, "\n".join(body).strip()) for r, title, body in chunks]
    return meta, [c for c in out if c[2]]


def coverage(chunks):
    chs = {c for (s, e), _, _ in chunks if (s, e) != INTRO for c in range(s // 1000, e // 1000 + 1)}
    return chs


def main(a):
    check = "--check" in a
    keys = [x for x in a if not x.startswith("--")]
    files = sorted(MARKED.glob("*.txt"))
    if keys:
        files = [f for f in files if f.stem in keys]
    if not files:
        sys.exit(f"no marked files in {MARKED}")
    OUT.mkdir(parents=True, exist_ok=True)
    lf = OUT / "labels.json"
    labels = json.loads(lf.read_text("utf-8")) if lf.exists() else {}
    table = heb_to_eng()
    n_ch = book_cfg().get("chapters")
    for f in files:
        meta, chunks = parse_marked(f, table)
        key = meta.get("source", f.stem)
        chs = coverage(chunks)
        top = n_ch or max(chs, default=0)
        gaps = [c for c in range(1, top + 1) if c not in chs]
        print(f"{key}: {len(chunks)} sections, {sum(len(c[2]) for c in chunks) // 1000} KB"
              + (f", no section for ch. {gaps}" if gaps else ""))
        if check:
            continue
        with open(OUT / f"{key}.jsonl", "w", encoding="utf-8", newline="\n") as fh:
            for (s, e), title, text in chunks:
                fh.write(json.dumps({"s": s, "e": e, "title": title, "text": text}, ensure_ascii=False) + "\n")
        labels[key] = meta.get("label", key)
    if not check:
        with open(lf, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(labels, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
