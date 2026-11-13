/* The tabernacle map for a book that enables the `ritual` component.
   data/tabmap.html (written by `assets` from biblecore/tabmap.py) holds the
   sheet: layer tabs, a to-scale plan, the schematic camp, keys and the cited
   measurements. A unit with a ritual strip or a .tabmap marker gets a
   thumbnail in its header (tap: the full sheet) and a small inset beside each
   strip; tapping a step lights its zone in all of them. */

const SHEET_URL = new URL("../data/tabmap.html", import.meta.url);
const CAMP_ZONES = ["camp", "outside-camp"];
let sheetHtml = null;
let dialog = null;
let lit = null;

async function sheet() {
  if (sheetHtml === null) {
    try {
      const r = await fetch(SHEET_URL);
      sheetHtml = r.ok ? await r.text() : "";
    } catch (e) { sheetHtml = ""; }
  }
  return sheetHtml;
}

function parts(html) {
  const box = document.createElement("div");
  box.innerHTML = html;
  return box;
}

function setLayer(root, layer) {
  root.dataset.layer = layer;
  for (const b of root.querySelectorAll(".tm-tabs button")) b.setAttribute("aria-pressed", String(b.dataset.layer === layer));
}

function light(zone) {
  lit = zone;
  for (const el of document.querySelectorAll(".tm [data-zone], .tm-thumb [data-zone], .tm-inset [data-zone]")) {
    el.classList.toggle("lit", el.dataset.zone === zone);
  }
  const camp = CAMP_ZONES.includes(zone);
  for (const inset of document.querySelectorAll(".tm-inset")) inset.dataset.view = camp ? "camp" : "plan";
  if (dialog && zone) {
    const tm = dialog.querySelector(".tm");
    if (camp) setLayer(tm, "camp");
    else if (tm.dataset.layer === "camp") setLayer(tm, "holy");
  }
  for (const cap of document.querySelectorAll(".tm-inset .tm-lit")) {
    cap.textContent = zone ? (zoneLabel(zone) || zone) : "";
  }
}

function zoneLabel(zone) {
  const t = document.querySelector(`[data-zone="${zone}"] title`);
  return t ? t.textContent : "";
}

async function openSheet(html) {
  if (!dialog) {
    dialog = document.createElement("dialog");
    dialog.className = "tm-dialog";
    dialog.innerHTML = `<form method="dialog"><button class="tm-close" aria-label="Close the map">×</button></form>` + html;
    document.body.appendChild(dialog);
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) dialog.close();
      const b = e.target.closest(".tm-tabs button");
      if (b) setLayer(dialog.querySelector(".tm"), b.dataset.layer);
    });
  }
  light(lit);
  if (!dialog.open) dialog.showModal();
}

export async function mount(root) {
  lit = null;
  const strips = [...root.querySelectorAll("section.ritual")];
  const marks = [...root.querySelectorAll(".tabmap")];
  if (!strips.length && !marks.length) return;
  const html = await sheet();
  if (!html) return;
  const planOf = () => parts(html).querySelector(".tm-plan");
  const campOf = () => parts(html).querySelector(".tm-camp");

  // the thumbnail in the unit header
  const head = root.querySelector(".mast") || root.querySelector("article.unit");
  if (head && !head.querySelector(".tm-thumb")) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tm-thumb";
    btn.setAttribute("aria-label", "Open the tabernacle map");
    btn.append(planOf());
    btn.insertAdjacentHTML("beforeend", "<span>Map</span>");
    btn.addEventListener("click", () => openSheet(html));
    head.appendChild(btn);
  }

  for (const strip of strips) {
    const inset = document.createElement("div");
    inset.className = "tm-inset";
    inset.dataset.view = "plan";
    inset.append(planOf(), campOf());
    inset.insertAdjacentHTML("beforeend", `<span class="tm-lit" aria-live="polite"></span>`);
    strip.classList.add("has-map");
    strip.appendChild(inset);
    const steps = [...strip.querySelectorAll("ol.steps > li[data-at]")];
    for (const li of steps) {
      li.tabIndex = 0;
      li.setAttribute("role", "button");
      const go = () => {
        const on = li.getAttribute("aria-pressed") !== "true";
        for (const o of root.querySelectorAll("ol.steps > li")) o.setAttribute("aria-pressed", "false");
        li.setAttribute("aria-pressed", String(on));
        light(on ? li.dataset.at : null);
      };
      li.addEventListener("click", go);
      li.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    }
  }
  for (const m of marks) {
    const layer = m.dataset.layer || "holy";
    const inset = document.createElement("div");
    inset.className = "tm-inset tm-mark";
    inset.dataset.view = layer === "camp" ? "camp" : "plan";
    inset.append(planOf(), campOf());
    m.appendChild(inset);
    if (m.dataset.at) for (const el of inset.querySelectorAll(`[data-zone="${m.dataset.at}"]`)) el.classList.add("lit");
  }
}
