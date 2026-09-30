/* Per-verse asides, collapsed by default. A verse's following siblings are
   gathered until the next verse or structural block:
   - .gloss and every enabled "verse-aside" component without a `toggle`
     (aside.echo, aside.textform, ...) share one light note (*) per verse;
   - a component with a `toggle` (components.json, from its component.json)
     gets its own chip: `box` wraps the verse's asides of that kind in one
     panel headed `head` (compare -> a ✦ "Rendering" spotlight), `each` gives
     every aside its own chip and leaves it where it is (aside.synoptic, ✧).
   main.js passes the components in from data/components.json. Runs on the
   freshly loaded fragment; the fragments themselves are untouched. */

const BASE_SEL = ".gloss";
const STOP_SEL =
  "p.v, div.v, h3, section, header, .verses, .sectionhead, .panelhead, .movement, .ring, .structure, table";

export function enhanceSpotlights(root, comps = []) {
  if (typeof comps === "string") comps = comps ? [{ selector: comps }] : [];
  const noteSel = [BASE_SEL, ...comps.filter((c) => !c.toggle).map((c) => c.selector)].join(", ");
  const own = comps.filter((c) => c.toggle);
  let count = 0;

  for (const verse of root.querySelectorAll("p.v, div.v")) {
    const notes = [];
    const mine = own.map(() => []);
    let n = verse.nextElementSibling;
    while (n && !n.matches(STOP_SEL)) {
      const next = n.nextElementSibling;
      const i = own.findIndex((c) => n.matches(c.selector));
      if (i >= 0) mine[i].push(n);
      else if (n.matches(noteSel)) notes.push(n);
      else if (notes.length || mine.some((m) => m.length)) break;
      n = next;
    }

    let after = verse;
    if (notes.length) after = mountNote(verse, after, notes);
    own.forEach((c, i) => {
      if (!mine[i].length) return;
      if (c.toggle.each) mine[i].forEach((el) => mountEach(verse, el, c.toggle));
      else after = mountBox(verse, after, mine[i], c.toggle);
    });
    count += notes.length + mine.reduce((t, m) => t + m.length, 0);
  }

  if (count) addAllControl(root);
  return count;
}

function chipFor(verse, box, cls, sym, label, n) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = cls;
  btn.setAttribute("aria-expanded", "false");
  btn.setAttribute("aria-label", `Show ${label} for this verse${n > 1 ? ` (${n})` : ""}`);
  btn.textContent = sym;
  btn.addEventListener("click", (e) => { e.stopPropagation(); setOpen(box, btn, box.hidden); });
  verse.append(" ", btn);
  box._btn = btn;
}

function mountNote(verse, insertAfter, items) {
  const box = document.createElement("div");
  box.className = "verse-note";
  box.hidden = true;
  items.forEach((el) => box.append(el));
  insertAfter.after(box);
  chipFor(verse, box, "note-toggle", "*", "notes", items.length);
  return box;
}

function mountBox(verse, insertAfter, items, t) {
  const box = document.createElement("aside");
  box.className = `${t.box || "spotlight"} aside-box`;
  box.hidden = true;
  if (t.head) {
    const h = document.createElement("div");
    h.className = "spot-head";
    h.textContent = t.head;
    box.append(h);
  }
  items.forEach((el, i) => {
    if (i) {
      const d = document.createElement("div");
      d.className = "spot-div";
      box.append(d);
    }
    box.append(el);
  });
  insertAfter.after(box);
  chipFor(verse, box, `spot-toggle ${t.cls || ""}`.trim(), t.sym, t.label, items.length);
  return box;
}

function mountEach(verse, el, t) {
  el.classList.add("aside-box");
  el.hidden = true;
  chipFor(verse, el, `spot-toggle ${t.cls || ""}`.trim(), t.sym, t.label, 1);
}

function setOpen(box, btn, open) {
  box.hidden = !open;
  btn.setAttribute("aria-expanded", String(open));
  btn.classList.toggle("is-open", open);
}

/* open (or close) every verse note under root: the "every note open"
   reading mode and the print page */
export function openAll(root, open = true) {
  boxes(root).forEach((b) => setOpen(b, b._btn, open));
  const btn = root.querySelector(".spot-all");
  if (btn) {
    btn.textContent = open ? "Hide all notes" : "Show all notes";
    btn.dataset.mode = open ? "hide" : "show";
  }
}

function boxes(root) {
  return [...root.querySelectorAll(".verse-note, .aside-box")];
}

function addAllControl(root) {
  const article = root.querySelector("article.unit") || root;
  const firstVerse = article.querySelector("p.v, div.v");
  if (!firstVerse) return;

  // the level the verses sit at: the article, or a wrapper inside it that
  // also holds the masthead (some fragments wrap everything in div.wrap)
  let level = article;
  const mast = article.querySelector("header.mast");
  for (;;) {
    const w = [...level.children].find((c) => c.contains(firstVerse));
    if (w && w !== firstVerse && mast && w.contains(mast)) level = w;
    else break;
  }
  // the element at that level that is or contains the first verse
  let anchor = firstVerse;
  while (anchor.parentElement && anchor.parentElement !== level) {
    anchor = anchor.parentElement;
  }
  // if a section heading sits right above it, put the bar above that instead,
  // so the control always lands just under the structural blocks
  const prev = anchor.previousElementSibling;
  if (prev && prev.matches("h3.pericope")) {
    anchor = prev;
  }

  const bar = document.createElement("div");
  bar.className = "spot-controls";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "spot-all";
  const relabel = () => {
    const anyClosed = boxes(root).some((b) => b.hidden);
    btn.textContent = anyClosed ? "Show all notes" : "Hide all notes";
    btn.dataset.mode = anyClosed ? "show" : "hide";
  };
  btn.addEventListener("click", () => {
    const open = btn.dataset.mode === "show";
    boxes(root).forEach((b) => setOpen(b, b._btn, open));
    relabel();
  });
  relabel();
  bar.append(btn);
  anchor.before(bar);
}

/* print / PDF: open everything so nothing is lost on paper */
if (typeof window !== "undefined") {
  window.addEventListener("beforeprint", () => {
    document.querySelectorAll(".verse-note, .aside-box").forEach((b) => {
      b._wasHidden = b.hidden;
      b.hidden = false;
    });
  });
  window.addEventListener("afterprint", () => {
    document.querySelectorAll(".verse-note, .aside-box").forEach((b) => {
      if (b._wasHidden) b.hidden = true;
    });
  });
}
