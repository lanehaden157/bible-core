/* Tiers: the peaks/full view, the tier-shaded outline, and World English
   Bible text under any data-verses block. Written into a book only when
   book.json has "tiers": true (assets.py); main.js and threads.js reach it
   through //tiers: marker lines that a tierless build strips, so a book
   without tiers has none of this. Styles: the `digest` component's style.css.

   View: ?view=peaks|full (this load only) > the device's saved choice >
   peaks. Peaks shows a non-peak unit as its digest card with an "Open the
   full unit" button; a link to one verse opens the unit in full. */

const bust = (u) => { const x = new URL(u); x.searchParams.set("v", Date.now()); return x; };

const S = { on: false, prefix: "", units: [], reload: () => {}, stored: null,
            override: null, opened: new Set(), boxes: new Set() };
const KEY = () => `${S.prefix}:view`;
const TIER_LABEL = { full: "Full", condensed: "Condensed", digest: "Digest" };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

export function init({ info, units, prefix, reload }) {
  S.on = !!info?.tiers;
  if (!S.on) return;
  S.prefix = prefix;
  S.units = units.units || [];
  S.reload = reload;
  try { S.stored = localStorage.getItem(KEY()); } catch (e) { S.stored = null; }
  const q = new URLSearchParams(location.search).get("view");
  S.override = q === "peaks" || q === "full" ? q : null;
}

export const view = () => (S.override || (["peaks", "full"].includes(S.stored) ? S.stored : "peaks"));

function setView(v) {
  S.override = null;
  S.stored = v;
  S.opened.clear();
  try { localStorage.setItem(KEY(), v); } catch (e) { /* private mode */ }
  for (const box of S.boxes) { if (box.isConnected) mark(box); else S.boxes.delete(box); }
  S.reload();
}

const mark = (box) => box.querySelectorAll("button").forEach((b) =>
  b.setAttribute("aria-checked", String(b.dataset.v === view())));

/* Peaks | Full, a radio pill like the top bar's */
function pill(box) {
  box.classList.add("seg");
  box.setAttribute("role", "radiogroup");
  box.setAttribute("aria-label", "Study view");
  box.innerHTML =
    `<button type="button" role="radio" data-v="peaks" title="Peaks in full, the other units as a short digest">Peaks</button>` +
    `<button type="button" role="radio" data-v="full" title="Every unit in full">Full study</button>`;
  mark(box);
  box.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (b && b.getAttribute("aria-checked") !== "true") setView(b.dataset.v);
  });
  S.boxes.add(box);
  return box;
}

/* the Contents drawer: the toggle on top, tier shading on the outline */
export function decorateNav(nav, units) {
  if (!S.on) return;
  const sw = document.createElement("div");
  sw.className = "view-switch";
  sw.innerHTML = `<span class="settings-h">View</span> `;
  sw.append(pill(document.createElement("span")));
  nav.prepend(sw);

  const by = new Map(units.map((u) => [u.slug, u]));
  for (const el of nav.querySelectorAll(".bm-tick, .unit-chip")) {
    const u = by.get(el.dataset.slug);
    if (!u) continue;
    const tier = u.tier || "full";
    el.classList.add(`tier-${tier}`);
    if (u.peak) el.classList.add("peak");
    if (u.stretches?.length) el.classList.add("has-stretch");
    const note = [TIER_LABEL[tier], u.peak ? "peak" : "", u.stretches?.length ? "with condensed/digest stretches" : ""]
      .filter(Boolean).join(", ");
    if (el.classList.contains("bm-tick")) el.title += ` · ${note}`;
    else el.querySelector(".passage")?.append(` · ${note.toLowerCase()}`);
  }

  const key = `<div class="bm-key-row"><span class="bm-key-h">Tiers</span><span class="bm-key-items">` +
    ["full", "condensed", "digest"].map((t) =>
      `<span class="bm-key-tier"><i class="tier-${t}"></i>${TIER_LABEL[t]}</span>`).join("") +
    `<span class="bm-key-tier">&#9733; peak</span></span></div>`;
  const host = nav.querySelector(".bm-key") || nav.querySelector(".book-map");
  host?.insertAdjacentHTML("beforeend", key);
}

/* the settings panel: the same toggle, above Reading */
export function mountSettings(panel) {
  if (!S.on || !panel) return;
  const head = document.createElement("div");
  head.className = "settings-h";
  head.textContent = "Study view";
  const box = pill(document.createElement("div"));
  box.classList.add("settings-modes");
  const reading = [...panel.querySelectorAll(".settings-h")].find((h) => h.textContent === "Reading");
  if (reading) reading.before(head, box); else panel.append(head, box);
}

/* the strip under a unit's heading, and the digest card of a non-peak unit */
export function applyView(content, unit, anchor) {
  if (!S.on) return;
  const art = content.querySelector("article.unit");
  if (!art) return;
  const v = view();
  const strip = document.createElement("div");
  strip.className = "view-strip";
  const label = document.createElement("span");
  strip.append(label, pill(document.createElement("span")));
  const mast = art.querySelector("header.mast");
  if (mast) mast.after(strip); else art.prepend(strip);

  const verseLink = !!anchor && /^\d+:\d+$/.test(anchor);
  const peak = !!unit.peak;
  const collapse = v === "peaks" && !peak && !!unit.digest && !S.opened.has(unit.slug) && !verseLink;
  label.textContent = v === "full" ? "Full study" : peak ? "Peaks view · a peak, in full" : collapse ? "Peaks view" : "Peaks view · opened in full";
  if (!collapse) return;

  art.classList.add("tier-collapsed");
  const card = document.createElement("div");
  card.className = "digest-card";
  card.innerHTML = `<span class="tier-tag">Digest of this unit${unit.tier && unit.tier !== "full" ? ` · ${esc(TIER_LABEL[unit.tier].toLowerCase())}` : ""}</span>` +
    `<p>${esc(unit.digest)}</p>` +
    `<button type="button" class="open-full">Open the full unit</button>`;
  strip.after(card);
  card.querySelector("button").addEventListener("click", () => {
    S.opened.add(unit.slug);
    art.classList.remove("tier-collapsed");
    card.remove();
    label.textContent = "Peaks view · opened in full";
  });
}

/* ------------------------------------------------------------ WEB on expand */

const WEB_RANGE = /^\s*(\d+):(\d+)\s*(?:[-–]\s*(?:(\d+):)?(\d+))?\s*$/;
const _web = new Map();
const webChapter = (c) => {
  if (!_web.has(c)) {
    _web.set(c, fetch(bust(new URL(`../data/web/${c}.json`, import.meta.url)))
      .then((r) => (r.ok ? r.json() : null)).catch(() => null));
  }
  return _web.get(c);
};

export function credit(foot) {
  if (!S.on || !foot) return;
  foot.insertAdjacentHTML("beforeend",
    `<p>Where a passage isn't translated here, its text is the World English Bible (public domain), shown only on request and labelled as not this study's translation.</p>`);
}

async function webHtml(range) {
  const m = WEB_RANGE.exec(range);
  if (!m) return `<p class="not-translated">No World English Bible text for this range.</p>`;
  const lo_ = [+m[1], +m[2]];
  const hi_ = [+(m[3] || m[1]), +(m[4] || m[2])];
  const parts = [];
  for (let c = lo_[0]; c <= hi_[0]; c++) {
    const d = await webChapter(c);
    // keys are "5" or a bridge "3-4"; a range that touches the verses shown is kept
    const ents = Object.entries(d?.verses || {}).map(([k, t]) => {
      const [lo, hi] = k.split("-").map(Number);
      return [lo, hi || lo, t];
    }).sort((x, y) => x[0] - y[0]);
    for (const [lo, hi, t] of ents) {
      if ((c === lo_[0] && hi < lo_[1]) || (c === hi_[0] && lo > hi_[1])) continue;
      parts.push(`<sup>${c}:${lo}${hi > lo ? "–" + hi : ""}</sup>${esc(t)}`);
    }
  }
  return parts.length
    ? `<p>${parts.join(" ")}</p>`
    : `<p class="not-translated">The World English Bible text isn't available for this passage.</p>`;
}

export function wireWeb(content) {
  if (!S.on) return;
  for (const el of content.querySelectorAll("[data-verses]")) {
    if (el.nextElementSibling?.classList.contains("web-wrap")) continue;
    const wrap = document.createElement("div");
    wrap.className = "web-wrap";
    wrap.innerHTML = `<button type="button" class="web-open" aria-expanded="false">World English Bible text</button>` +
      `<div class="web-text" hidden></div>`;
    el.after(wrap);
    const btn = wrap.querySelector("button");
    const box = wrap.querySelector(".web-text");
    btn.addEventListener("click", async () => {
      const open = box.hidden;
      box.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
      if (open && !box.dataset.loaded) {
        box.innerHTML = `<p class="web-label">World English Bible (public domain) &mdash; not this study's translation</p>` +
          await webHtml(el.dataset.verses);
        box.dataset.loaded = "1";
      }
    });
  }
}
