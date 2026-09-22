/* Concordance search — type a transliterated root or an English gloss, get
   every tagged occurrence across the built units with a context snippet.
   fold() is diacritic-generic (NFD + strip combining marks), so it works for
   any transliteration scheme. Edit the hint text for this book's own
   examples once it has roots. */

import { getOccurrences, getThreadFor, resolveUnit } from "./threads.js?v=3";

export function renderSearch(container, units, prefix = "study") {
  const KEY = `${prefix}.search.q`;
  const q0 = sessionStorage.getItem(KEY) || "";
  container.innerHTML = `
    <div class="search-view">
      <h1>Concordance</h1>
      <p class="search-hint">Type a transliterated root (diacritics optional)
        or an English gloss. Searches every built unit.</p>
      <input id="search-input" type="search" autocomplete="off" spellcheck="false"
        placeholder="root or gloss…" value="${escAttr(q0)}">
      <div id="search-results" class="search-results"></div>
    </div>`;

  const input = container.querySelector("#search-input");
  const out = container.querySelector("#search-results");
  const index = buildIndex(units);

  let t;
  const run = () => {
    const q = input.value.trim();
    sessionStorage.setItem(KEY, q);
    out.innerHTML = q.length < 2 ? "" : results(q, index, units);
  };
  input.addEventListener("input", () => { clearTimeout(t); t = setTimeout(run, 120); });
  input.focus();
  run();
}

/* root -> { meta, translit, gloss, thread, units:[{unit, hits}] } over built units */
function buildIndex(units) {
  const occ = getOccurrences();
  const byN = new Map(units.map((u) => [u.n, u]));
  const idx = new Map();

  for (const [slug, roots] of Object.entries(occ)) {
    const n = Number(slug.split("-")[1]);
    const unit = byN.get(n);
    if (!unit || !unit.built) continue;
    const resolved = resolveUnit(unit);
    for (const [root, data] of Object.entries(roots)) {
      if (!data.hits || !data.hits.length) continue;
      let e = idx.get(root);
      if (!e) {
        const m = resolved.get(root) || {};
        e = {
          root,
          color: m.color || null,
          translit: m.translit || root,
          gloss: m.gloss || "",
          thread: getThreadFor(root),
          units: [],
          total: 0,
        };
        idx.set(root, e);
      }
      e.units.push({ unit, hits: data.hits });
      e.total += data.hits.length;
    }
  }
  return idx;
}

function results(query, idx, units) {
  const q = fold(query);
  const matches = [...idx.values()].filter((e) =>
    fold(e.translit).includes(q) || fold(e.gloss).includes(q) || e.root.includes(q));

  if (!matches.length) return `<p class="search-empty">No tagged root matches “${esc(query)}”.</p>`;

  matches.sort((a, b) => (b.thread ? 1 : 0) - (a.thread ? 1 : 0) || b.total - a.total);

  return matches.map((e) => {
    const units_ = e.units
      .sort((a, b) => a.unit.n - b.unit.n)
      .map((u) => `
        <div class="sr-unit">
          <a class="sr-unit-h" href="#/${u.unit.slug}">Unit ${u.unit.n} · ${esc(u.unit.title)}</a>
          <ul>${u.hits.map((h) => `
            <li><a href="#/${u.unit.slug}${h.v ? "/v" + h.v : ""}">
              ${h.v ? `<span class="sr-v">v.${h.v}</span> ` : ""}${esc(h.pre)}<b>${esc(h.hit)}</b>${esc(h.post)}</a></li>`).join("")}
          </ul>
        </div>`).join("");
    return `
      <section class="sr-root">
        <h3>
          ${e.color ? `<span class="swatch" style="background:${e.color}"></span>` : ""}
          <i>${esc(e.translit)}</i>${e.gloss ? ` — ${esc(e.gloss)}` : ""}
          ${e.thread ? `<span class="sr-tag">thread${e.thread.status === "closed" ? " · closed" : ""}</span>` : ""}
          <span class="sr-n">${e.total}</span>
        </h3>
        ${units_}
      </section>`;
  }).join("");
}

/* fold diacritics so "nahalah" matches "naḥalah", "hoba" matches "ḥoba" */
function fold(s) {
  return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function escAttr(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
