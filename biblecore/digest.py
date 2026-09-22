"""data/threads.json -> threads-digest.md, the human-readable snapshot the
chat side reads. Never hand-edit the digest; regenerate it.

    python -m biblecore digest
"""

import json

from biblecore.book import book


def _ref(d):
    return f"{d.get('unit', '?')}" + (f" ({d['ref']})" if d.get("ref") else "")


def _declined():
    """roots.json's declined ledger, or {} when absent."""
    path = book().data("roots.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("declined") or {}
    except (OSError, ValueError):
        return {}


def main(argv=None):
    b = book()
    with open(b.data("threads.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    out = b.path("digest")
    words = b.path("words").replace(b.root, "").lstrip("\\/")
    threads = data["threads"]
    openc = sum(1 for t in threads if t.get("status") == "open")

    lines = [
        "# Cross-unit threads — canonical digest",
        "",
        f"Generated from `data/threads.json` (version {data.get('version', '?')}). "
        f"{len(threads)} threads, {openc} open.",
        "",
        "**This is the source of truth for thread tagging.** In a unit's fragment, "
        "a root that appears in the `id` column below is a *tracked thread*: tag "
        "every occurrence `<span class=\"r\" data-root=\"<id>\" data-w=\"<word "
        "id>\">…</span>` (the word id from `" + words + "`) and list it "
        "under `threads.opens` / `threads.payoffs` in the unit-meta block, with a "
        "matching id set in `data/roots.json`. A root that is recurring but *not* "
        "here is unit-local — tag it with its own name (no `data-w` needed) and "
        "just declare it in the unit's own `roots`. To propose promoting a local "
        "root to a tracked thread, add it to `threads.candidates` with a one-line "
        "reason (the Strong's/lemma `ids` you've actually observed in "
        "`" + words + "`, plus a few representative `refs`, if you have them). "
        "**Claude decides, biased toward book-wide**: a local root that later "
        "pays off is worse than a tracked one that doesn't, so promote on a "
        "real second sighting. Ask Lane only when genuinely unsure.",
        "",
    ]

    if not threads:
        lines += [
            "*(No threads defined yet — this file exists to prove the "
            "`threads.json` → `threads-digest.md` round trip works before unit "
            "1, not because there's anything to digest. Regenerate once Lane "
            "adds the first thread.)*",
            "",
        ]
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"wrote {out} — 0 threads (empty threads.json, round trip OK)")
        return 0

    lines += [
        "| id | root (data-root) | translit | gloss | opens | payoffs | status |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in sorted(threads, key=lambda x: (x.get("opens", {}).get("unit", 99), x["id"])):
        payoffs = " · ".join(_ref(p) for p in t.get("payoffs", [])) or "—"
        lines.append(
            f"| `{t['id']}` | `{t['root']}` | {t.get('translit', '')} | "
            f"{t.get('gloss', '')} | {_ref(t.get('opens', {}))} | {payoffs} | "
            f"{t.get('status', '')} |"
        )

    lines += ["", "## Notes per thread", ""]
    for t in sorted(threads, key=lambda x: x["id"]):
        lines.append(f"- **`{t['id']}`**: {t.get('note', '').strip()}")

    # Declined candidates (review A13). This is the half of the promotion
    # record that used to live only in a session log, so the same root got
    # re-proposed every few units and re-argued from scratch.
    declined = _declined()
    if declined:
        lines += ["", "## Considered and kept local", "",
                  "These were proposed as threads and deliberately declined. "
                  "Don't re-propose one without a specific new payoff in "
                  "view -- say what changed.", ""]
        for slug, e in sorted(declined.items()):
            unit = f", unit {e['unit']}" if e.get("unit") else ""
            lines.append(f"- **`{slug}`** (declined {e.get('date', '?')}"
                         f"{unit}): {e.get('why', '').strip()}")

    lines.append("")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {out} — {len(threads)} threads, {len(declined)} declined")
    return 0

