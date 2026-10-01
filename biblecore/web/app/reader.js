/* Reader features over the build's data layer (bible-core emit.py):
   verse references on every .v, reading modes, the interlinear, reference
   lookup, "continue where you left off", and the whole-study print page.

   Data (all static, fetched once and cached):
     data/words/<ch>.json  per-word translit, lemma key, morphology in words
     data/lemmas.json      lemma -> translit, gloss (Strong's for Hebrew, the
                           MorphGNT lexicon for Greek), count, refs
     data/text.json        the study's own English per built verse

   Glosses identify a word for the reader, never the study's rendering,
   and the interlinear says so. No native script: the data
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

/* "6:24" -> that verse. A verse with no block of its own (inside a
   data-verses table, or a block-formatted passage): its interlinear box if
   mounted, else the block that declares it, else the closest verse before
   it. "v24" (search's occurrence links) -> the first verse numbered 24. */
export function findVerse(root, anchor) {
  const cv = /^(\d+):(\d+)$/.exec(anchor);
  if (cv) {
    const want = [+cv[1], +cv[2]];
    const exact = root.querySelector(`.v[data-ref="${anchor}"], .il-gap[data-ref="${anchor}"]`);
    if (exact) return exact;
    const decl = declaredBlocks(root).find((d) => cmp(d.lo, want) <= 0 && cmp(want, d.hi) <= 0);
    if (decl) return decl.el;
    let best = null;
    for (const el of root.querySelectorAll(".v[data-ref]")) {
      if (cmp(el.dataset.ref.split(":").map(Number), want) <= 0) best = el;
    }
    return best;
  }
  const vm = /^v(\d+)$/.exec(anchor);
  if (vm) return [...root.querySelectorAll(".v")].find((v) => v.dataset.ref?.endsWith(`:${vm[1]}`));
  return null;
}

/* elements that stand in for verses (data-verses="1:22–43", "6:9–7:2") */
function declaredBlocks(root) {
  return [...root.querySelectorAll("[data-verses]")].map((el) => {
    const r = passageRange(el.dataset.verses);
    return r && { el, lo: r[0], hi: r[1] };
  }).filter(Boolean);
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
   (dabar comes out "arrange"). A Greek lexicon gloss is shown as it is. */
const senses = (g) => (g || "").split(";").map((x) => x.trim()).filter(Boolean).join("; ");

/* What the gloss is, by the book's language (Matthew's pilot, note 7):
   Strong's for Hebrew, the MorphGNT lexicon for Greek. */
const GLOSS_KEY = {
  hebrew: "a Strong's gloss (a word identifier, not this study's translation)",
  greek: "a lexicon gloss (it identifies the word; it isn't this study's translation)",
};
const LANGUAGE = { hebrew: "Hebrew", greek: "Greek" };

const HEADING_SEL = "h2, h3, .sectionhead, .spot-controls";

/* Word boxes under every indexed verse of root (indexVerses first). opts:
   {book: the book's name, language: "hebrew" | "greek", passage: the
   unit's passage}. A verse with no block of its own gets a labelled box:
   right after the element that declares it (data-verses), or, when nothing
   does, just before the next verse (Lane, 2026-10-01). Resolves once the
   boxes are in; an unmount or a newer mount meanwhile cancels this one
   (Matthew's pilot, note 5), so a mode or unit switch mid-fetch never
   leaves boxes behind or doubles them. */
export async function mountInterlinear(root, opts = {}) {
  if (root.querySelector(".il")) return;
  const gen = (root._ilGen = (root._ilGen || 0) + 1);
  const verses = [...root.querySelectorAll(".v[data-ref]")];
  if (!verses.length) return;
  const refs = verses.map((el) => el.dataset.ref.split(":").map(Number));
  const range = passageRange(opts.passage || unitPassage(root)) || [refs[0], refs[refs.length - 1]];
  const chapters = [];
  for (let c = range[0][0]; c <= range[1][0]; c++) chapters.push(c);
  const [lemmas, ...chs] = await Promise.all([loadLemmas(), ...chapters.map(loadChapter)]);
  if (root._ilGen !== gen || root.querySelector(".il")) return;
  const byCh = new Map(chapters.map((c, i) => [c, chs[i] || {}]));
  const o = { book: opts.book || "the book", language: opts.language || "hebrew" };

  verses.forEach((el, i) => {
    const ws = byCh.get(refs[i][0])?.[refs[i][1]];
    if (ws?.length) el.after(box(ws, refs[i], lemmas, o, false));
  });

  // the passage's other verses: declared by a block, or not written out
  const have = new Set(verses.map((el) => el.dataset.ref));
  const declared = declaredBlocks(root);
  const after = new Map();  // declaring element -> the last box put after it
  for (const c of chapters) {
    const vs = Object.keys(byCh.get(c)).map(Number).sort((a, b) => a - b);
    for (const v of vs) {
      const cv = [c, v];
      if (have.has(`${c}:${v}`) || cmp(cv, range[0]) < 0 || cmp(range[1], cv) < 0) continue;
      const b = box(byCh.get(c)[v], cv, lemmas, o, true);
      const d = declared.find((x) => cmp(x.lo, cv) <= 0 && cmp(cv, x.hi) <= 0);
      if (d) {
        (after.get(d.el) || d.el).after(b);
        after.set(d.el, b);
        continue;
      }
      const next = verses[refs.findIndex((r) => cmp(r, cv) > 0)];
      if (next) gapAnchor(next).before(b);
      else (lastBox(verses[verses.length - 1]) || verses[verses.length - 1]).after(b);
    }
  }

  if (!root.querySelector(".il-key")) {
    const key = document.createElement("p");
    key.className = "il-key";
    key.textContent = `Interlinear: the ${LANGUAGE[o.language] || "original"} transliterated, ` +
      `${GLOSS_KEY[o.language] || GLOSS_KEY.hebrew} and the grammar. Tap a word to find every ` +
      `place it occurs in ${o.book}.`;
    keyAnchor(root)?.before(key);
  }
}

export function unmountInterlinear(root) {
  root._ilGen = (root._ilGen || 0) + 1;
  root.querySelectorAll(".il, .il-key").forEach((e) => e.remove());
}

function box(ws, [c, v], lemmas, o, gap) {
  const el = document.createElement("div");
  el.className = gap ? "il il-gap" : "il";
  el.setAttribute("aria-label", `Interlinear, ${c}:${v}`);
  if (gap) el.dataset.ref = `${c}:${v}`;
  const gloss = o.language === "hebrew" ? senses : (g) => g || "";
  el.innerHTML = (gap ? `<span class="il-ref">${c}:${v}</span>` : "") + ws.map((w) => {
    const lem = lemmas[w.l] || {};
    const title = [lem.g && `Gloss: ${lem.g}`, w.m, lem.n && `${lem.n}× in ${o.book}`]
      .filter(Boolean).join(" · ");
    return `<a class="il-w${w.a ? " il-arc" : ""}" href="#/search/${encodeURIComponent(w.l)}" title="${esc(title)}">` +
      `<i>${esc(w.t)}</i><b>${esc(gloss(lem.g) || "—")}</b><small>${esc(w.m)}</small></a>`;
  }).join("");
  return el;
}

function unitPassage(root) {
  try { return JSON.parse(root.querySelector("#unit-meta")?.textContent || "{}").passage || ""; }
  catch (e) { return ""; }
}

/* the last box right after a verse (its own, then any gap boxes) */
function lastBox(verse) {
  let at = null;
  for (let n = verse.nextElementSibling; n?.classList.contains("il"); n = n.nextElementSibling) at = n;
  return at;
}

/* before the next verse, but above any heading that opens it */
function gapAnchor(verse) {
  let at = verse;
  while (at.previousElementSibling?.matches(HEADING_SEL)) at = at.previousElementSibling;
  return at;
}

/* above the first verse (and the heading or notes bar over it). Core
   fragments have no wrapper around their verses, so prepending to the unit
   would put the key above the masthead (Matthew's pilot, note 6). */
function keyAnchor(root) {
  const article = root.querySelector("article.unit") || root;
  const bar = article.querySelector(".spot-controls");
  if (bar) return bar;
  let at = article.querySelector(".v[data-ref]");
  if (!at) return null;
  while (at.parentElement && at.parentElement !== article) at = at.parentElement;
  return gapAnchor(at);
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
