/* "Law behind this": an echo into a law gets a chip that opens a two-sentence
   brief of that law and links to the unit that studies it. Only for a book with
   "law_chips": true in book.json (the shell keeps this module and its calls
   between //law: marker lines for such a book, and nothing otherwise).

   The briefs are the hub's <hub>/data/law-briefs.json, fetched once in the
   background, so a new brief needs no re-vendor. A missing or unreachable hub,
   a bad file or no brief for an echo means no chip and no error.

   Brief row: {law, ref, refbook, span: [c1, v1, c2, v2], brief, site, slug,
   unit, book, link} -- `ref` is the range the brief covers, `book` the book
   whose unit wrote it, `link` "cv" (verse links as c:v) or "v". */

const REF = /((?:[1-3]\s?)?[A-Z][a-z]+)\.?\s+(\d+):(\d+)(?:\s*[–-]\s*(?:(\d+):)?(\d+))?/g;
let briefs = [];
let lastRoot = null;

const norm = (s) => s.toLowerCase().replace(/[\s.]/g, "");

export function load(hub) {
  if (!hub) return;
  const base = hub.endsWith("/") ? hub : hub + "/";
  fetch(new URL("data/law-briefs.json", base)).then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      briefs = Array.isArray(d?.briefs) ? d.briefs.filter((b) => b && Array.isArray(b.span) && b.brief) : [];
      if (briefs.length && lastRoot) mount(lastRoot);
    }).catch(() => {});
}

/* briefs whose range overlaps a reference the echo names */
function hits(text) {
  const out = [];
  for (const m of text.matchAll(REF)) {
    const book = norm(m[1]);
    const lo = +m[2] * 1000 + +m[3];
    const hi = (m[5] ? (m[4] ? +m[4] : +m[2]) * 1000 + +m[5] : lo);
    for (const b of briefs) {
      if (norm(b.refbook || "") !== book) continue;
      const [c1, v1, c2, v2] = b.span;
      if (lo <= c2 * 1000 + v2 && c1 * 1000 + v1 <= hi && !out.includes(b)) out.push(b);
    }
  }
  return out;
}

function href(b) {
  if (!b.site || !b.slug) return null;
  const site = b.site.endsWith("/") ? b.site : b.site + "/";
  let anchor = "";
  if (b.book === b.refbook) anchor = "/" + (b.link === "cv" ? `${b.span[0]}:${b.span[1]}` : `v${b.span[1]}`);
  return `${site}#/${b.slug}${anchor}`;
}

function style() {
  if (document.getElementById("law-chip-style")) return;
  const s = document.createElement("style");
  s.id = "law-chip-style";
  s.textContent = `
.law-chip { margin: 6px 0 0; font: inherit; font-size: 13px; padding: 2px 10px; cursor: pointer;
  color: var(--accent-law, var(--accent-clay)); background: transparent;
  border: 1px solid var(--accent-law, var(--accent-clay)); border-radius: 12px; }
.law-chip:hover, .law-chip.is-open { color: var(--panel); background: var(--accent-law, var(--accent-clay)); }
.law-brief { margin: 6px 0 0; padding: 8px 12px; font-size: 14.5px; line-height: 1.5; text-indent: 0;
  border-left: 3px solid var(--accent-law, var(--accent-clay)); background: color-mix(in srgb, var(--panel) 78%, var(--bg)); }
.law-brief p { margin: 0 0 4px; text-indent: 0; }
.law-brief .law-ref { font-variant: small-caps; letter-spacing: .05em; color: var(--ink-soft); }
.law-brief a { font-size: 13.5px; }`;
  document.head.append(s);
}

export function mount(root) {
  lastRoot = root;
  if (!briefs.length) return;
  for (const echo of root.querySelectorAll("aside.echo:not([data-law-chip])")) {
    const found = hits(echo.textContent || "");
    if (!found.length) continue;
    echo.dataset.lawChip = "1";
    style();
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "law-chip";
    btn.setAttribute("aria-expanded", "false");
    btn.textContent = "§ Law behind this";
    const panel = document.createElement("div");
    panel.className = "law-brief";
    panel.hidden = true;
    for (const b of found) {
      const p = document.createElement("p");
      const ref = document.createElement("span");
      ref.className = "law-ref";
      ref.textContent = b.ref;
      p.append(ref, " ", b.brief);
      const url = href(b);
      if (url) {
        const a = document.createElement("a");
        a.href = url;
        a.textContent = "Read the law unit";
        p.append(" ", a);
      }
      panel.append(p);
    }
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      panel.hidden = !panel.hidden;
      btn.setAttribute("aria-expanded", String(!panel.hidden));
      btn.classList.toggle("is-open", !panel.hidden);
    });
    echo.append(" ", btn, panel);
  }
}
