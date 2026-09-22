/* Two-tier colour resolution + data-driven legend.
   Global tier: data/threads.json (a tracked root's colour is identical in every
   unit). Local tier: data/units.json roots {color,translit,gloss}.
   Ported unchanged from Projects/Matthew/app/threads.js -- entirely data-driven,
   no Greek/Matthew-specific logic. */

const bust = (u) => { const x = new URL(u); x.searchParams.set("v", Date.now()); return x; };
const THREADS_URL = new URL("../data/threads.json", import.meta.url);
const OCC_URL = new URL("../data/occurrences.json", import.meta.url);

let _threads = null; // { byRoot: Map, list: [] }
let _occ = null;

export async function loadThreadData() {
  if (!_threads) {
    const [t, o] = await Promise.all([
      fetch(bust(THREADS_URL)).then((r) => r.json()),
      fetch(bust(OCC_URL)).then((r) => r.json()).catch(() => ({})),
    ]);
    _threads = { list: t.threads, byRoot: new Map(t.threads.map((x) => [x.root, x])) };
    _occ = o;
  }
  return _threads;
}

export function getOccurrences() { return _occ || {}; }
export function getThreadFor(root) { return _threads?.byRoot.get(root) || null; }

/** root -> { color, translit, gloss, example, echo, threadId, status, count } */
export function resolveUnit(unit) {
  const out = new Map();
  const local = unit.roots || {};
  const counts = (_occ && _occ[unit.slug]) || {};
  const names = new Set([...Object.keys(local), ...Object.keys(counts)]);
  for (const root of names) {
    const th = _threads.byRoot.get(root);
    const lc = local[root];
    const lm = typeof lc === "string" ? { color: lc } : lc || {};
    out.set(root, {
      color: th ? th.color : lm.color || null,
      translit: (th && th.translit) || lm.translit || root,
      gloss: (th && th.gloss) || lm.gloss || "",
      example: (th && th.example) || lm.example || "",
      echo: (th && th.echo) || lm.echo || "",
      threadId: th ? th.id : null,
      status: th ? th.status : null,
      count: (counts[root] && counts[root].count) || 0,
    });
  }
  return out;
}

/** Inject `.unit[data-unit=N] [data-root=x]{color}` + legend swatch colours.
    Tracked-thread roots also get a dotted underline in their own colour
    (a "thread" stitched under the word) that glows on hover. */
export function injectPalette(unit, resolved) {
  document.getElementById("unit-palette")?.remove();
  const rules = [];
  const sel = `.unit[data-unit="${unit.n}"]`;
  for (const [root, m] of resolved) {
    if (!m.color) continue;
    const r = `[data-root="${cssEsc(root)}"]`;
    rules.push(`${sel} ${r}{color:${m.color}}`);
    rules.push(`${sel} .swatch[style*="--c-${cssEsc(root)}"]{background:${m.color}!important}`);
    // cross-unit thread -> dotted underline (the same word recurring across
    // units). plain local roots: colour only.
    if (m.threadId) {
      rules.push(
        `${sel} ${r}{text-decoration:underline dotted ${m.color};` +
        `text-underline-offset:3px;text-decoration-thickness:from-font}`);
      rules.push(
        `${sel} ${r}:hover{text-decoration-style:solid;` +
        `text-shadow:0 0 7px ${hexA(m.color, 0.4)}}`);
      rules.push(`${sel} ${r}.root-active{text-shadow:0 0 7px ${hexA(m.color, 0.45)}}`);
    }
  }
  const s = document.createElement("style");
  s.id = "unit-palette";
  s.textContent = rules.join("\n");
  document.head.appendChild(s);
}

function hexA(hex, a) {
  const h = hex.replace("#", "");
  const n = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16));
  return `rgba(${r},${g},${b},${a})`;
}

/** Rebuild the unit's colour-key from data, split into cross-unit threads
    and unit-local roots. */
export function rebuildLegend(contentEl, resolved) {
  const legend = contentEl.querySelector("section.legend, section.block.legend");
  if (!legend) return;
  const ul = legend.querySelector("ul");
  if (!ul) return;

  const all = [...resolved.entries()].filter(([, m]) => m.color && m.count > 0);
  const byCount = (a, b) => b[1].count - a[1].count;
  const threads = all.filter(([, m]) => m.threadId).sort(byCount);
  const roots = all.filter(([, m]) => !m.threadId).sort(byCount);

  const row = ([root, m]) => {
    const n = m.count > 1 ? ` <span class="tag">${m.count}×</span>` : "";
    const st = m.status === "closed" ? ` <span class="tag">closed</span>` : "";
    return `<li class="lg-${m.threadId ? "thread" : "root"}">` +
      `<span class="swatch" style="background:${m.color}"></span>` +
      `<span class="r" data-root="${escAttr(root)}">${esc(m.translit)}</span>` +
      `${m.gloss ? " — " + esc(m.gloss) : ""}${st}${n}</li>`;
  };

  const group = (label, items) => items.length
    ? `<div class="legend-group"><h3>${label}</h3>` +
      `<ul>${items.map(row).join("")}</ul></div>`
    : "";

  ul.outerHTML =
    group(`✦ Cross-unit threads`, threads) +
    group(`Roots in this unit`, roots);

  legend.querySelector(".cap")?.remove();
}

/* ---------------------------------------------- root hover tip + click popover */

let _tip, _pop, _popAnchor = null;

export function wireRoots(root, unit, units) {
  root._rootsAbort?.abort();
  const ac = new AbortController();
  root._rootsAbort = ac;
  const opt = { signal: ac.signal };

  const resolved = resolveUnit(unit);
  const builtByN = new Map(units.map((u) => [u.n, u]));

  const hoverable = () => window.matchMedia("(hover: hover)").matches;

  root.addEventListener("pointerover", (e) => {
    if (!hoverable() || _popAnchor) return;
    const el = e.target.closest("[data-root]");
    if (el && !el.closest("a")) showTip(el, resolved);
  }, opt);
  root.addEventListener("pointerout", (e) => {
    if (e.target.closest("[data-root]")) hideTip();
  }, opt);

  root.addEventListener("click", (e) => {
    const el = e.target.closest("[data-root]");
    if (!el || e.target.closest("a")) return;
    e.preventDefault();
    hideTip();
    if (_popAnchor === el) return closePop();
    openPop(el, resolved, unit, builtByN);
  }, opt);
}

function tipEl() {
  if (!_tip) {
    _tip = document.createElement("div");
    _tip.className = "root-tip";
    _tip.hidden = true;
    document.body.append(_tip);
  }
  return _tip;
}

function showTip(el, resolved) {
  const m = resolved.get(el.dataset.root);
  if (!m) return;
  const t = tipEl();
  t.innerHTML = `<i>${esc(m.translit)}</i>${m.gloss ? " — " + esc(m.gloss) : ""}`;
  place(el, t, 6);
}
function hideTip() { if (_tip) _tip.hidden = true; }

function popEl() {
  if (!_pop) {
    _pop = document.createElement("div");
    _pop.className = "root-pop";
    _pop.hidden = true;
    _pop.setAttribute("role", "dialog");
    document.body.append(_pop);
  }
  return _pop;
}

function openPop(el, resolved, unit, builtByN) {
  const root = el.dataset.root;
  const m = resolved.get(root);
  if (!m) return;
  const th = _threads.byRoot.get(root);
  const occ = (_occ[unit.slug] || {})[root] || { count: 0, verses: [] };

  const rows = [];
  rows.push(`<div class="rp-head">
    <span class="swatch" style="background:${m.color || "transparent"}"></span>
    <i>${esc(m.translit)}</i>
    <span class="rp-tag">root${th ? " · thread" : ""}${th && th.status === "closed" ? " · closed" : ""}</span>
  </div>`);
  if (m.gloss) rows.push(`<p class="rp-gloss">${esc(m.gloss)}</p>`);
  if (m.example) rows.push(`<p class="rp-example">${esc(m.example)}</p>`);
  if (m.echo) rows.push(`<p class="rp-echo">${esc(m.echo)}</p>`);

  if (occ.count) {
    const vv = (occ.verses || []).length
      ? ` · ${occ.verses.length > 6 ? occ.verses.length + " verses" : "vv. " + occ.verses.join(", ")}`
      : "";
    rows.push(`<p class="rp-count">${occ.count}× in this unit${vv}</p>`);
  }

  if (th) {
    const leg = [];
    if (th.opens) leg.push(`opens ${esc(th.opens.ref)}`);
    for (const p of th.payoffs || []) {
      const u = builtByN.get(p.unit);
      const label = `Unit ${p.unit}${p.ref ? ` (${esc(p.ref)})` : ""}`;
      leg.push(u && u.built
        ? `<a href="#/${u.slug}">${label}</a>`
        : `<span class="rp-soon">${label}</span>`);
    }
    if (leg.length) rows.push(`<p class="rp-traj">${leg.join(" → ")}</p>`);

    const elsewhere = Object.keys(_occ)
      .filter((s) => s !== unit.slug && (_occ[s][root]?.count))
      .map((s) => builtByN.get(Number(s.split("-")[1]))).filter(Boolean);
    if (elsewhere.length) {
      rows.push(`<p class="rp-also">also in ${elsewhere
        .map((u) => `<a href="#/${u.slug}">Unit ${u.n}</a>`).join(", ")}</p>`);
    }
    if (th.note) rows.push(`<p class="rp-note">${esc(th.note)}</p>`);
  }

  const p = popEl();
  p.innerHTML = rows.join("");
  p.querySelectorAll("a[href^='#/']").forEach((a) =>
    a.addEventListener("click", () => closePop()));
  _popAnchor = el;
  el.classList.add("root-active");
  place(el, p, 8);
  bindDismiss();
}

function closePop() {
  if (_pop) _pop.hidden = true;
  _popAnchor?.classList.remove("root-active");
  _popAnchor = null;
  unbindDismiss();
}

let _dismiss;
function bindDismiss() {
  unbindDismiss();
  _dismiss = new AbortController();
  const s = { signal: _dismiss.signal };
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".root-pop") && !e.target.closest("[data-root]")) closePop();
  }, s);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePop(); }, s);
  window.addEventListener("scroll", closePop, { ...s, passive: true });
  window.addEventListener("resize", closePop, s);
}
function unbindDismiss() { _dismiss?.abort(); _dismiss = null; }

function place(anchor, node, gap) {
  const r = anchor.getBoundingClientRect();
  node.hidden = false;
  node.style.visibility = "hidden";
  const w = node.offsetWidth, h = node.offsetHeight;
  let left = r.left + r.width / 2 - w / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
  let top = r.bottom + gap;
  if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - gap);
  node.style.left = `${Math.round(left)}px`;
  node.style.top = `${Math.round(top)}px`;
  node.style.visibility = "";
}

function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function escAttr(s) { return String(s).replace(/"/g, "&quot;"); }
function cssEsc(s) { return s.replace(/[^a-zA-Z0-9_-]/g, "\\$&"); }
