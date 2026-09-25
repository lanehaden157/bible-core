/* Search. One box, four kinds of answer, in this order:
     a reference ("Num 6:24", "6:24")       -> a link straight to the verse
     tagged roots (the concordance)         -> every tagged occurrence in built units
     lemmas ("barak", "bless", "=1288")     -> every verse in the book with that
                                               lemma, from the word table
     the study's own English (built verses) -> matching verses, highlighted
   fold() is diacritic-generic (NFD + strip combining marks), so it works for
   any transliteration scheme. "=<lemma key>" is an exact lemma lookup (the
   interlinear links to it as #/lemma/<key>). */

import { getOccurrences, getThreadFor, resolveUnit } from "./threads.js?v=5";
import { loadLemmas, loadText, parseRef, unitForRef } from "./reader.js?v=5";

export function renderSearch(container, units, prefix = "study", opts = {}) {
  const KEY = `${prefix}.search.q`;
  const q0 = opts.initial || sessionStorage.getItem(KEY) || "";
  container.innerHTML = `
    <div class="search-view">
      <h1>Search</h1>
      <p class="search-hint">A reference (<i>6:24</i>), a transliterated root or word
        (diacritics optional), or English. Searches the tagged roots, every word in the
        book by lemma, and the text of every built unit.</p>
      <input id="search-input" type="search" autocomplete="off" spellcheck="false"
        placeholder="reference, root, word or English…" value="${escAttr(q0)}">
      <div id="search-results" class="search-results"></div>
    </div>`;

  const input = container.querySelector("#search-input");
  const out = container.querySelector("#search-results");
  const index = buildIndex(units);
  let lemmas = null, text = null;
  Promise.all([loadLemmas(), loadText()]).then(([l, t]) => { lemmas = l; text = t; run(); });

  let t;
  const run = () => {
    const q = input.value.trim();
    sessionStorage.setItem(KEY, q);
    if (q.length < 2) { out.innerHTML = ""; return; }
    const parts = [
      refResult(q, units, opts.book || {}),
      q.startsWith("=") ? "" : results(q, index, units),
      lemmas ? lemmaResults(q, lemmas, units) : "",
      text && !q.startsWith("=") ? textResults(q, text, units) : "",
    ].filter(Boolean);
    out.innerHTML = parts.join("") ||
      `<p class="search-empty">Nothing matches “${esc(q)}”.</p>`;
  };
  input.addEventListener("input", () => { clearTimeout(t); t = setTimeout(run, 120); });
  input.focus();
  run();
}

/* ---- reference ---- */
function refResult(q, units, book) {
  const r = parseRef(q, book);
  if (!r) return "";
  const u = unitForRef(r[0], r[1], units);
  const label = `${esc(book.name || "")} ${r[0]}:${r[1]}`.trim();
  if (!u) return `<section class="sr-block"><h3>Reference</h3><p class="search-empty">${label}: no unit covers it.</p></section>`;
  return `<section class="sr-block"><h3>Reference</h3><p>` + (u.built
    ? `<a href="#/${u.slug}/${r[0]}:${r[1]}">${label}</a> · Unit ${u.n}, ${esc(u.title)}`
    : `${label} · Unit ${u.n}, ${esc(u.title)} (not yet built)`) + `</p></section>`;
}

/* ---- lemmas ---- */
function lemmaResults(q, lemmas, units) {
  let hits;
  if (q.startsWith("=")) {
    const k = q.slice(1).trim();
    hits = lemmas[k] ? [[k, lemmas[k]]] : [];
  } else {
    const f = fold(q);
    hits = Object.entries(lemmas).filter(([k, e]) =>
      k === q || fold(e.t).includes(f) || (f.length > 2 && fold(e.g).includes(f)));
    hits.sort((a, b) => (fold(b[1].t) === f) - (fold(a[1].t) === f) || b[1].n - a[1].n);
  }
  if (!hits.length) return "";
  const shown = hits.slice(0, 12);
  const one = hits.length === 1;
  return `<section class="sr-block"><h3>Words in the book, by lemma</h3>` + shown.map(([k, e]) => `
    <details class="sr-lemma"${one ? " open" : ""}>
      <summary><i>${esc(e.t || k)}</i> — ${esc(e.g || "")} <span class="sr-n">${e.n}× · Strong's ${esc(k)}</span></summary>
      <p class="sr-refs">${e.refs.map((r) => refLink(r, units)).join(" ")}</p>
    </details>`).join("") +
    (hits.length > shown.length ? `<p class="search-empty">${hits.length - shown.length} more; narrow the search.</p>` : "") +
    `</section>`;
}

function refLink(ref, units) {
  const [c, v] = ref.split(":").map(Number);
  const u = unitForRef(c, v, units);
  return u?.built ? `<a href="#/${u.slug}/${ref}">${ref}</a>` : `<span class="sr-unbuilt">${ref}</span>`;
}

/* ---- the study's English ---- */
function textResults(q, verses, units) {
  const f = fold(q);
  if (f.length < 3) return "";
  const hits = verses.filter((x) => fold(x.t).includes(f));
  if (!hits.length) return "";
  const byN = new Map(units.map((u) => [u.n, u]));
  return `<section class="sr-block"><h3>In the translation <span class="sr-n">${hits.length}</span></h3><ul class="sr-text">` +
    hits.slice(0, 60).map((x) => {
      const u = byN.get(x.u);
      return `<li><a href="#/${u ? u.slug : ""}/${x.r}"><span class="sr-v">${x.r}</span> ${mark(x.t, q)}</a></li>`;
    }).join("") + `</ul></section>`;
}

/* highlight the first match, diacritic-insensitively, on the original text */
function mark(t, q) {
  const f = fold(q), ft = fold(t);
  const i = ft.indexOf(f);
  if (i < 0 || ft.length !== t.length) return esc(t);
  return esc(t.slice(0, i)) + "<b>" + esc(t.slice(i, i + q.length)) + "</b>" + esc(t.slice(i + q.length));
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

  if (!matches.length) return "";

  matches.sort((a, b) => (b.thread ? 1 : 0) - (a.thread ? 1 : 0) || b.total - a.total);

  return `<section class="sr-block"><h3>Tagged roots</h3>` + matches.map((e) => {
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
  }).join("") + `</section>`;
}

/* fold diacritics so "nahalah" matches "naḥalah", "hoba" matches "ḥoba" */
function fold(s) {
  return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function escAttr(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
