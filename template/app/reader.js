/* Reader features over the build's data layer (bible-core emit.py):
   verse references on every .v, reading modes, the interlinear, reference
   lookup, "continue where you left off", and the whole-study print page.

   Data (all static, fetched once and cached):
     data/words/<ch>.json  per-word translit, lemma key, morphology in words
     data/lemmas.json      lemma -> translit, Strong's short gloss, count, refs
     data/text.json        the study's own English per built verse

   Strong's glosses are a word identifier for the reader, never the study's
   rendering, and the interlinear says so. No native script: the data
   layer carries none. */

const DATA = (p) => new URL(`../data/${p}`, import.meta.url);
const cache = new Map();
async function getJSON(p) {
  if (!cache.has(p)) {
    cache.set(p, fetch(DATA(p)).then((r) => (r.ok ? r.json() : null)).catch(() => null));
  }
  return cache.get(p);
}
export const loadLemmas = () => getJSON("lemmas.json").then((d) => d?.lemmas || {});
export const loadText = () => getJSON("text.json").then((d) => d?.verses || []);
const loadChapter = (c) => getJSON(`words/${c}.json`).then((d) => d?.verses || {});

/* ------------------------------------------------------------ references */

const RANGE_RE = /(\d+):(\d+)\s*[–-]\s*(?:(\d+):)?(\d+)/;

/* [lo, hi] as [c, v] pairs from "Numbers 16:36–17:13" or "Numbers 1:1–54" */
export function passageRange(passage) {
  const m = RANGE_RE.exec(passage || "");
  if (!m) {
    const one = /(\d+):(\d+)/.exec(passage || "");
    return one ? [[+one[1], +one[2]], [+one[1], +one[2]]] : null;
  }
  return [[+m[1], +m[2]], [+(m[3] || m[1]), +m[4]]];
}

const cmp = (a, b) => a[0] - b[0] || a[1] - b[1];

export function unitForRef(c, v, units) {
  return units.find((u) => {
    const r = passageRange(u.passage);
    return r && cmp(r[0], [c, v]) <= 0 && cmp([c, v], r[1]) <= 0;
  }) || null;
}

/* "Num 6:24", "numbers 6.24", "6:24" -> [6, 24]; a bare chapter "Num 6" -> [6, 1].
   The book name is optional; a different book's name doesn't match. */
export function parseRef(q, book) {
  const s = q.trim().toLowerCase();
  const m = /^(?:([1-3]?\s*[a-z]+)\.?\s*)?(\d+)(?:\s*[:.]\s*(\d+))?$/.exec(s);
  if (!m) return null;
  if (m[1]) {
    const names = [book.name, book.abbrev, book.osis].filter(Boolean).map((x) => x.toLowerCase());
    if (!names.some((n) => n.startsWith(m[1].replace(/\s+/g, "")) || m[1].startsWith(n))) return null;
  }
  if (!m[3] && !m[1]) return null; // a bare number isn't a reference
  return [+m[2], m[3] ? +m[3] : 1];
}

/* Stamp every verse block with data-ref="C:V", rolling the chapter the way
   the pipeline does (biblecore data_w.verse_blocks): an explicit C:V
   resets it, a bare number that goes backwards moves to the next chapter. */
export function indexVerses(root, unit) {
  const r = passageRange(unit.passage);
  let ch = r ? r[0][0] : 1, prev = null;
  for (const el of root.querySelectorAll("p.v, div.v")) {
    const t = el.querySelector(".n")?.textContent.trim() || "";
    const m = /^(?:(\d+):)?(\d+)$/.exec(t);
    if (!m) continue;
    const v = +m[2];
    if (m[1]) { ch = +m[1]; prev = null; }
    else if (prev !== null && v < prev) ch += 1;
    prev = v;
    el.dataset.ref = `${ch}:${v}`;
  }
}

export function findVerse(root, anchor) {
  const cv = /^(\d+):(\d+)$/.exec(anchor);
  if (cv) return root.querySelector(`.v[data-ref="${cv[1]}:${cv[2]}"]`);
  const vm = /^v(\d+)$/.exec(anchor);
  if (vm) return [...root.querySelectorAll(".v")].find((v) => v.dataset.ref?.endsWith(`:${vm[1]}`));
  return null;
}

/* ---------------------------------------------------------- reading modes */

export const MODES = [
  ["notes", "Translation with notes (tap * to open)"],
  ["open", "Translation with every note open"],
  ["plain", "Translation only"],
  ["interlinear", "Interlinear (word by word)"],
];

export function applyMode(mode) {
  for (const [m] of MODES) document.body.classList.toggle(`mode-${m}`, m === mode);
}

/* ------------------------------------------------------------ interlinear */

/* Strong's senses, as the lexicon lists them (up to three). Never just the
   first: Strong's orders senses by root meaning, so the first misleads
   (dabar comes out "arrange"). */
const senses = (g) => (g || "").split(";").map((x) => x.trim()).filter(Boolean).join("; ");

export async function mountInterlinear(root) {
  if (root.querySelector(".il")) return;
  const verses = [...root.querySelectorAll(".v[data-ref]")];
  const chapters = [...new Set(verses.map((v) => +v.dataset.ref.split(":")[0]))];
  const [lemmas, ...chs] = await Promise.all([loadLemmas(), ...chapters.map(loadChapter)]);
  const byCh = new Map(chapters.map((c, i) => [c, chs[i]]));
  for (const el of verses) {
    const [c, v] = el.dataset.ref.split(":");
    const words = byCh.get(+c)?.[v];
    if (!words?.length) continue;
    const box = document.createElement("div");
    box.className = "il";
    box.setAttribute("aria-label", `Interlinear, ${c}:${v}`);
    box.innerHTML = words.map((w) => {
      const lem = lemmas[w.l] || {};
      const title = [lem.g && `Strong's: ${lem.g}`, w.m, lem.n && `${lem.n}× in the book`]
        .filter(Boolean).join(" · ");
      return `<a class="il-w${w.a ? " il-arc" : ""}" href="#/lemma/${encodeURIComponent(w.l)}" title="${esc(title)}">` +
        `<i>${esc(w.t)}</i><b>${esc(senses(lem.g) || "—")}</b><small>${esc(w.m)}</small></a>`;
    }).join("");
    el.after(box);
  }
  if (!root.querySelector(".il-key")) {
    const key = document.createElement("p");
    key.className = "il-key";
    key.textContent = "Interlinear: transliteration, a Strong's gloss (a word identifier, not " +
      "this study's translation) and the grammar. Tap a word for every place its lemma occurs.";
    (root.querySelector(".verses") || root.querySelector("article.unit") || root).prepend(key);
  }
}

export function unmountInterlinear(root) {
  root.querySelectorAll(".il, .il-key").forEach((e) => e.remove());
}

/* ------------------------------------------------ continue where you left off */

export function rememberPosition(prefix, slug, ref) {
  try { localStorage.setItem(`${prefix}:last`, JSON.stringify({ slug, ref: ref || null })); } catch (e) { /* private mode */ }
}
export function lastPosition(prefix) {
  try { return JSON.parse(localStorage.getItem(`${prefix}:last`) || "null"); } catch (e) { return null; }
}

/* ------------------------------------------------------------- print page */

export async function renderPrint(container, units, book, prepare) {
  const built = units.filter((u) => u.built);
  container.innerHTML = `<div class="print-view"><header class="print-head">
      <h1>${esc(book.name)}</h1><p>${built.length} of ${units.length} units · study translation</p>
      <button type="button" class="spot-all print-go">Print or save as PDF</button></header>
      <div class="print-units"></div></div>`;
  container.querySelector(".print-go").addEventListener("click", () => window.print());
  const out = container.querySelector(".print-units");
  for (const u of built) {
    const html = await fetch(new URL(`../units/${u.slug}.html`, import.meta.url)).then((r) => r.text()).catch(() => "");
    const wrap = document.createElement("div");
    wrap.className = "print-unit";
    wrap.innerHTML = html;
    out.append(wrap);
    prepare(wrap, u);
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
