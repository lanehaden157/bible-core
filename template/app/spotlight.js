/* Per-verse asides, collapsed by default behind one toggle per verse:
   .gloss (a light note) and aside.echo (a cross-book echo, "cf."). A book
   that enables another verse-sibling component adds its selector to
   ASIDE_SEL, with its CSS and check, in the same commit
   (ARCHITECTURE.md §2: optional components ship as one piece). Runs on the
   freshly loaded fragment; the fragments themselves are untouched. */

const ASIDE_SEL = ".gloss, aside.echo";
const STOP_SEL =
  "p.v, div.v, h3, section, header, .verses, table";

export function enhanceSpotlights(root) {
  let count = 0;

  for (const verse of root.querySelectorAll("p.v, div.v")) {
    const asides = [];
    let n = verse.nextElementSibling;
    while (n && !n.matches(STOP_SEL)) {
      const next = n.nextElementSibling;
      if (n.matches(ASIDE_SEL)) asides.push(n);
      else if (asides.length) break;
      n = next;
    }
    if (!asides.length) continue;

    mount(verse, verse, asides);
    count += asides.length;
  }

  if (count) addAllControl(root);
  return count;
}

function mount(verse, insertAfter, items) {
  const box = document.createElement("div");
  box.className = "verse-note";
  box.hidden = true;
  items.forEach((el) => box.append(el));
  insertAfter.after(box);

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "note-toggle";
  btn.setAttribute("aria-expanded", "false");
  btn.setAttribute("aria-label",
    `Show notes for this verse${items.length > 1 ? ` (${items.length})` : ""}`);
  btn.textContent = "*";
  btn.addEventListener("click", (e) => { e.stopPropagation(); setOpen(box, btn, box.hidden); });
  verse.append(" ", btn);
  box._btn = btn;
  return box;
}

function setOpen(box, btn, open) {
  box.hidden = !open;
  btn.setAttribute("aria-expanded", String(open));
  btn.classList.toggle("is-open", open);
}

function boxes(root) {
  return [...root.querySelectorAll(".verse-note")];
}

function addAllControl(root) {
  const article = root.querySelector("article.unit") || root;
  const firstVerse = article.querySelector("p.v, div.v");
  if (!firstVerse) return;

  // the article-level element that is or contains the first verse
  let anchor = firstVerse;
  while (anchor.parentElement && anchor.parentElement !== article) {
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
    document.querySelectorAll(".verse-note").forEach((b) => {
      b._wasHidden = b.hidden;
      b.hidden = false;
    });
  });
  window.addEventListener("afterprint", () => {
    document.querySelectorAll(".verse-note").forEach((b) => {
      if (b._wasHidden) b.hidden = true;
    });
  });
}
