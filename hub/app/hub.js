/* The canon hub: one page over the federated book sites.
   Data comes from bible-core tools/hub_build.py (data/books.json,
   canon.json, concordance.json). Routes:
     #/                 the canon map, with progress for started books
     #/book/<slug>      one book: groupings, tracked threads, link to its site
     #/arcs             arcs with their canon threads, type-scenes and paths
     #/thread/<id>      a canon thread's members across books
     #/scene/<id>       a type-scene's instances
     #/intertext        the quotation/allusion/echo graph as a matrix + list
     #/paths, #/path/<id>  curated reading paths
     #/search           references, lemmas across books, tracked threads
   No native script anywhere; lexicon glosses are identifiers. */

const DATA = (f) => new URL(`../data/${f}`, import.meta.url);
const content = document.getElementById("content");
let books = [], byOsis = new Map(), bySlug = new Map(), canon = {}, conc = null;

init();

async function init() {
  try {
    const [b, c] = await Promise.all([
      fetch(DATA("books.json")).then((r) => r.json()),
      fetch(DATA("canon.json")).then((r) => r.json()),
    ]);
    books = b.books;
    canon = c;
  } catch (e) {
    content.innerHTML = `<p class="missing">Could not load the hub's data.</p>`;
    return;
  }
  for (const b of books) {
    byOsis.set(b.osis, b);
    if (b.slug) bySlug.set(b.slug, b);
  }
  window.addEventListener("hashchange", route);
  route();
}

const loadConc = async () => conc || (conc = await fetch(DATA("concordance.json")).then((r) => r.json()));

/* ---------------------------------------------------------------- router */

function route() {
  const [page, arg] = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  for (const a of document.querySelectorAll(".topnav a")) {
    const target = a.getAttribute("href").replace(/^#\/?/, "");
    a.toggleAttribute("aria-current", target === (page || "") ||
      (target === "arcs" && ["thread", "scene"].includes(page)) ||
      (target === "paths" && page === "path"));
  }
  const views = {
    "": home, book: bookView, arcs, thread: threadView, scene: sceneView,
    intertext, paths, path: pathView, search,
  };
  window.scrollTo(0, 0);
  (views[page || ""] || notFound)(arg);
}

function notFound() { content.innerHTML = `<p class="missing">Nothing here. <a href="#/">Back to the books.</a></p>`; }

/* ------------------------------------------------------------ references */

const norm = (s) => s.toLowerCase().replace(/[\s.]/g, "");

/* "Num 26:52–56" -> {book, c, v, text}; book is the books.json entry */
function parseRef(ref) {
  const m = /^\s*((?:[1-3]\s*)?[A-Za-z]+)\.?\s*(\d+)(?::(\d+))?/.exec(ref || "");
  if (!m) return null;
  const key = norm(m[1]);
  const book = books.find((b) => norm(b.osis) === key) ||
    books.find((b) => norm(b.name) === key) ||
    books.find((b) => key.length >= 3 && norm(b.name).startsWith(key));
  return book ? { book, c: +m[2], v: m[3] ? +m[3] : 1, text: ref } : null;
}

const RANGE_RE = /(\d+):(\d+)\s*[–-]\s*(?:(\d+):)?(\d+)/;
function unitFor(book, c, v) {
  return (book.units || []).find((u) => {
    const m = RANGE_RE.exec(u.passage);
    const one = /(\d+):(\d+)/.exec(u.passage);
    const lo = m ? [+m[1], +m[2]] : one && [+one[1], +one[2]];
    const hi = m ? [+(m[3] || m[1]), +m[4]] : lo;
    if (!lo) return false;
    const x = c * 1000 + v;
    return lo[0] * 1000 + lo[1] <= x && x <= hi[0] * 1000 + hi[1];
  });
}

/* a reference as a link into its book's site when that verse is built */
function refLink(ref, label) {
  const r = parseRef(ref);
  const text = esc(label || ref);
  if (!r || !r.book.site) return `<span class="ref">${text}</span>`;
  const u = unitFor(r.book, r.c, r.v);
  if (!u || !u.built) {
    return `<span class="ref pending" title="${u ? `Unit ${u.n}, not yet built` : "not in the study yet"}">${text}</span>`;
  }
  const anchor = r.book.link === "cv" ? `${r.c}:${r.v}` : `v${r.v}`;
  return `<a class="ref" href="${r.book.site}#/${u.slug}/${anchor}">${text}</a>`;
}

/* ---------------------------------------------------------------- views */

function home() {
  document.title = "Canon — study hub";
  const started = books.filter((b) => b.site);
  const tile = (b) => {
    if (!b.site) return `<span class="tile" title="${esc(b.name)}">${esc(b.osis)}</span>`;
    const pct = b.unit_count ? Math.round(100 * b.units_built / b.unit_count) : 0;
    return `<a class="tile started" href="#/book/${b.slug}" title="${esc(b.name)}: ${b.units_built} of ${b.unit_count} units">
      ${esc(b.osis)}<span class="bar"><i style="width:${pct}%"></i></span></a>`;
  };
  const grid = (t, label) => `<section class="canon-half"><h2>${label}</h2>
    <div class="tiles">${books.filter((b) => b.t === t).map(tile).join("")}</div></section>`;
  content.innerHTML = `
    <h1 class="page-h">The canon, one book at a time</h1>
    <p class="lede">Literary-canonical study translations, each its own site. This hub
      tracks their progress and what runs between them: the arcs of the one story,
      threads that cross books, type-scenes, and every quotation, allusion and echo.</p>
    <div class="cards">${started.map((b) => `
      <a class="card" href="#/book/${b.slug}">
        <b>${esc(b.name)}</b>
        <span>${b.units_built} of ${b.unit_count} units built · ${b.threads.length} tracked threads</span>
        <span class="bar"><i style="width:${Math.round(100 * b.units_built / (b.unit_count || 1))}%"></i></span>
      </a>`).join("")}</div>
    ${grid("ot", "Hebrew Bible")}${grid("nt", "New Testament")}
    <section><h2>Arcs</h2><div class="cards">${(canon.arcs || []).map((a) => `
      <a class="card" href="#/arcs/${a.id}"><b>${esc(a.label)}</b><span>${esc(a.note || "")}</span></a>`).join("")}
    </div></section>`;
}

function bookView(slug) {
  const b = bySlug.get(slug);
  if (!b) return notFound();
  document.title = `${b.name} — study hub`;
  const byN = new Map(b.units.map((u) => [u.n, u]));
  const groups = b.groups.length ? b.groups : [{ n: 0, label: "", units: b.units.map((u) => u.n) }];
  content.innerHTML = `
    <p class="crumb"><a href="#/">Books</a> › ${esc(b.name)}</p>
    <h1 class="page-h">${esc(b.name)}</h1>
    <p class="lede">${b.units_built} of ${b.unit_count} units built. <a href="${b.site}">Open the study →</a></p>
    ${groups.map((g) => `<section class="group"><h2>${g.label ? esc(g.label) : "Units"}</h2><div class="units">${
      g.units.map((n) => byN.get(n)).filter(Boolean).map((u) => u.built
        ? `<a class="unit built" href="${b.site}#/${u.slug}" title="${esc(u.passage)}"><b>${u.n}</b> ${esc(u.title)}</a>`
        : `<span class="unit" title="${esc(u.passage)} · not yet built"><b>${u.n}</b> ${esc(u.title)}</span>`).join("")
    }</div></section>`).join("")}
    <section><h2>Tracked threads</h2><ul class="threads">${b.threads.map((t) => `
      <li><span class="swatch" style="background:${t.color || "transparent"}"></span>
        <i>${esc(t.translit)}</i> — ${esc(t.gloss)} <span class="n">${t.count}×</span>
        ${canonFor(b.slug, t.id).map((c) => `<a class="tag" href="#/thread/${c.id}">canon: ${esc(c.label)}</a>`).join(" ")}</li>`).join("")}
    </ul></section>`;
}

function canonFor(slug, threadId) {
  return (canon.threads || []).filter((c) => c.members.some((m) => m.book === slug && m.thread === threadId));
}

function arcs(id) {
  document.title = "Arcs — study hub";
  const list = (xs, route_) => xs.length
    ? `<ul class="plain">${xs.map((x) => `<li><a href="#/${route_}/${x.id}">${esc(x.label)}</a> <span class="muted">${esc(x.note || "")}</span></li>`).join("")}</ul>`
    : `<p class="muted">None yet.</p>`;
  content.innerHTML = `<h1 class="page-h">Arcs</h1>
    <p class="lede">Creation, covenant, exile, presence: the one story the studies read every book inside.
      Each canon thread, type-scene and reading path belongs to an arc.</p>
    ${(canon.arcs || []).map((a) => `
      <section class="arc" id="${a.id}"><h2>${esc(a.label)}</h2><p class="muted">${esc(a.note || "")}</p>
        <h3>Canon threads</h3>${list((canon.threads || []).filter((t) => t.arc === a.id), "thread")}
        <h3>Type-scenes</h3>${list((canon.typescenes || []).filter((t) => t.arc === a.id), "scene")}
        <h3>Reading paths</h3>${list((canon.paths || []).filter((t) => t.arc === a.id), "path")}
      </section>`).join("")}`;
  if (id) requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView());
}

function threadView(id) {
  const t = (canon.threads || []).find((x) => x.id === id);
  if (!t) return notFound();
  document.title = `${t.label} — study hub`;
  content.innerHTML = `<p class="crumb"><a href="#/arcs">Arcs</a> › ${esc(arcLabel(t.arc))}</p>
    <h1 class="page-h">${esc(t.label)}</h1><p class="lede">${esc(t.note || "")}</p>
    <ul class="members">${t.members.map((m) => {
      const b = bySlug.get(m.book);
      const bt = b && m.thread ? b.threads.find((x) => x.id === m.thread) : null;
      return `<li><b>${esc(b ? b.name : cap(m.book))}</b>
        ${m.ref ? refLink(m.ref) : ""}
        ${bt ? `<span class="swatch" style="background:${bt.color || "transparent"}"></span><i>${esc(bt.translit)}</i> — ${esc(bt.gloss)} <span class="n">${bt.count}× tagged</span>`
             : m.thread ? `<span class="muted">thread ${esc(m.thread)}</span>` : `<span class="muted">not a tracked thread there yet</span>`}
        ${m.lemma ? `<span class="tag">${esc(m.lemma)}</span>` : ""}</li>`;
    }).join("")}</ul>`;
}

function sceneView(id) {
  const s = (canon.typescenes || []).find((x) => x.id === id);
  if (!s) return notFound();
  document.title = `${s.label} — study hub`;
  content.innerHTML = `<p class="crumb"><a href="#/arcs">Arcs</a> › ${esc(arcLabel(s.arc))}</p>
    <h1 class="page-h">${esc(s.label)}</h1><p class="lede">${esc(s.note || "")}</p>
    <ol class="members">${s.instances.map((i) => `<li>${refLink(i.ref)} <span class="muted">${esc(i.note || "")}</span></li>`).join("")}</ol>`;
}

function intertext() {
  document.title = "Intertext — study hub";
  const edges = canon.intertext || [];
  const src = [...new Set(edges.map((e) => parseRef(e.from)?.book.osis).filter(Boolean))];
  const tgtBook = (e) => parseRef(e.to)?.book;
  const order = new Map(books.map((b, i) => [b.osis, i]));
  const tgt = [...new Set(edges.map((e) => tgtBook(e)?.osis).filter(Boolean))].sort((a, b) => order.get(a) - order.get(b));
  const count = (s, t) => edges.filter((e) => parseRef(e.from)?.book.osis === s && tgtBook(e)?.osis === t).length;
  const max = Math.max(1, ...src.flatMap((s) => tgt.map((t) => count(s, t))));
  const kinds = [...new Set(edges.map((e) => e.kind))];
  content.innerHTML = `<h1 class="page-h">Intertext</h1>
    <p class="lede">${edges.length} links from the studies to the rest of the canon: quotations and allusions
      entered by hand, and echoes harvested from each unit's echo asides. Rows are the studied book,
      columns the book it points to.</p>
    <div class="matrix-wrap"><table class="matrix"><thead><tr><th></th>${tgt.map((t) => `<th><span>${esc(t)}</span></th>`).join("")}</tr></thead>
      <tbody>${src.map((s) => `<tr><th>${esc(byOsis.get(s)?.name || s)}</th>${tgt.map((t) => {
        const n = count(s, t);
        return `<td${n ? ` style="--a:${(0.15 + 0.85 * n / max).toFixed(2)}" title="${n} link(s) ${s} → ${t}"` : ""}>${n || ""}</td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>
    <div class="filters">
      <label>From <select id="f-src"><option value="">any book</option>${src.map((s) => `<option>${s}</option>`).join("")}</select></label>
      <label>Kind <select id="f-kind"><option value="">any</option>${kinds.map((k) => `<option>${k}</option>`).join("")}</select></label>
    </div>
    <ul id="edges" class="edges"></ul>`;
  const draw = () => {
    const s = document.getElementById("f-src").value, k = document.getElementById("f-kind").value;
    const xs = edges.filter((e) => (!s || parseRef(e.from)?.book.osis === s) && (!k || e.kind === k));
    document.getElementById("edges").innerHTML = xs.slice(0, 400).map((e) =>
      `<li>${refLink(e.from)} <span class="arrow">→</span> ${refLink(e.to)} <span class="tag">${esc(e.kind)}</span>
        ${e.note ? `<span class="muted">${esc(e.note)}</span>` : ""}</li>`).join("") +
      (xs.length > 400 ? `<li class="muted">${xs.length - 400} more; filter to narrow.</li>` : "");
  };
  content.querySelectorAll("select").forEach((s) => s.addEventListener("change", draw));
  draw();
}

function paths() {
  document.title = "Reading paths — study hub";
  content.innerHTML = `<h1 class="page-h">Reading paths</h1>
    <p class="lede">Sequences across books, each following one strand of the story.</p>
    <div class="cards">${(canon.paths || []).map((p) => `
      <a class="card" href="#/path/${p.id}"><b>${esc(p.label)}</b><span>${esc(p.note || "")}</span>
      <span class="muted">${p.steps.length} steps · ${esc(arcLabel(p.arc))}</span></a>`).join("")}</div>`;
}

function pathView(id) {
  const p = (canon.paths || []).find((x) => x.id === id);
  if (!p) return notFound();
  document.title = `${p.label} — study hub`;
  content.innerHTML = `<p class="crumb"><a href="#/paths">Paths</a> › ${esc(arcLabel(p.arc))}</p>
    <h1 class="page-h">${esc(p.label)}</h1><p class="lede">${esc(p.note || "")}</p>
    <ol class="steps">${p.steps.map((s) => `<li><b>${refLink(s.ref)}</b><span>${esc(s.note || "")}</span></li>`).join("")}</ol>`;
}

async function search() {
  document.title = "Search — study hub";
  content.innerHTML = `<h1 class="page-h">Search the canon</h1>
    <p class="lede">A reference (<i>Josh 1:6</i>), a transliterated word (<i>naḥalah</i>, diacritics optional),
      an English gloss, or a Strong's number (<i>=5159</i>). Searches every book's word table and tracked threads.</p>
    <input id="q" type="search" autocomplete="off" spellcheck="false" placeholder="reference, word, gloss or =number…">
    <div id="out"></div>`;
  const input = document.getElementById("q"), out = document.getElementById("out");
  input.value = sessionStorage.getItem("hub.q") || "";
  const c = await loadConc();
  const run = () => {
    const q = input.value.trim();
    sessionStorage.setItem("hub.q", q);
    if (q.length < 2) { out.innerHTML = ""; return; }
    out.innerHTML = [refHit(q), lemmaHits(q, c.lemmas), threadHits(q)].filter(Boolean).join("") ||
      `<p class="muted">Nothing matches “${esc(q)}”.</p>`;
  };
  let t;
  input.addEventListener("input", () => { clearTimeout(t); t = setTimeout(run, 120); });
  input.focus();
  run();
}

function refHit(q) {
  if (!/\d/.test(q)) return "";
  const r = parseRef(q);
  if (!r) return "";
  return `<section class="hits"><h2>Reference</h2><p>${refLink(q)} ${r.book.site ? "" : `<span class="muted">${esc(r.book.name)} has no study yet.</span>`}</p></section>`;
}

function lemmaHits(q, lemmas) {
  let hits;
  if (q.startsWith("=")) {
    const k = `heb:${q.slice(1).trim()}`;
    hits = lemmas[k] ? [[k, lemmas[k]]] : [];
  } else {
    const f = fold(q);
    hits = Object.entries(lemmas).filter(([, e]) => fold(e.t).includes(f) || (f.length > 2 && fold(e.g).includes(f)));
    hits.sort((a, b) => (fold(b[1].t) === f) - (fold(a[1].t) === f) || total(b[1]) - total(a[1]));
  }
  if (!hits.length) return "";
  return `<section class="hits"><h2>Hebrew words across books</h2>${hits.slice(0, 12).map(([k, e]) => `
    <details class="lemma"${hits.length === 1 ? " open" : ""}><summary><i>${esc(e.t)}</i> — ${esc(e.g)}
      <span class="n">${total(e)}× · Strong's ${esc(k.slice(4))}</span></summary>
      ${Object.entries(e.books).map(([slug, x]) => {
        const b = bySlug.get(slug);
        return `<p class="refs"><b>${esc(b?.name || slug)}</b> ${x.n}× · ${x.refs.map((r) => refLink(`${b?.osis} ${r}`, r)).join(" ")}</p>`;
      }).join("")}</details>`).join("")}</section>`;
}

function threadHits(q) {
  const f = fold(q);
  const hits = [];
  for (const b of books.filter((x) => x.threads)) {
    for (const t of b.threads) {
      if (fold(t.translit).includes(f) || fold(t.gloss).includes(f) || t.id.includes(f)) hits.push([b, t]);
    }
  }
  if (!hits.length) return "";
  return `<section class="hits"><h2>Tracked threads</h2><ul class="threads">${hits.map(([b, t]) => `
    <li><span class="swatch" style="background:${t.color || "transparent"}"></span><i>${esc(t.translit)}</i> — ${esc(t.gloss)}
      <span class="n">${t.count}×</span> <a href="#/book/${b.slug}">${esc(b.name)}</a>
      ${canonFor(b.slug, t.id).map((c) => `<a class="tag" href="#/thread/${c.id}">canon: ${esc(c.label)}</a>`).join(" ")}</li>`).join("")}</ul></section>`;
}

/* --------------------------------------------------------------- helpers */

const total = (e) => Object.values(e.books).reduce((s, x) => s + x.n, 0);
const arcLabel = (id) => (canon.arcs || []).find((a) => a.id === id)?.label || id || "";
const cap = (s) => (s || "").charAt(0).toUpperCase() + (s || "").slice(1);
function fold(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
function esc(s) { return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
