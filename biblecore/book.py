"""The book a command is running against, read from its book.json.

Every module asks `book()` for paths and settings instead of deriving them
from its own location, so one copy of the code serves any book. The book is
found from $BIBLECORE_BOOK (a directory or a book.json path), else by walking
up from the working directory to the first book.json. Tests pin one with
`use()`.

book.json is closed: an unknown key is an error, so the manifest can't
quietly collect settings nothing reads (ARCHITECTURE.md §4, review H5).
"""
import json
import os
import re

ALLOWED_KEYS = {
    "book", "osis", "abbrev", "slug", "language", "corpus", "groupings",
    "components", "meta_keys", "checks", "palette", "sync", "storage_key",
    "paths", "core", "versification",
    # the canon hub's URL; the site links to it and reads its canon.json
    "hub",
    # overrides for the book's entry in biblecore/web/themes.json
    # ({division?, primary?, secondary?, emblem?}); see theme.py
    "theme",
    # a secondary grouping kind (one of "groupings") the app draws over the
    # primary one: marks on unit chips, brackets on the book map, a line in
    # the placement (Matthew's discourses)
    "overlay",
    # a note shown in the book map's key; setting it turns on the overlay's
    # verse ranges and multi-membership (Deuteronomy's treaty; overlay.py)
    "overlay_note",
    # {component: label} for a toggle component's chip word, e.g.
    # {"synoptic": "Side by side"}; absent = the component's own chip
    "component_labels",
    # the bible-core commit whose template/ the book last took changes from
    # (its template base; structural audit D3). Read by
    # `tools/core_diff.py <book> --template`, moved by its `--set-base`.
    "template",
    # books this one mirrors: [{"with": "<OSIS id>", "file": "<name>.json"}];
    # the file sits in data/ (policy, like threads.json). See mirror.py.
    "mirrors",
    # true = a tiered book (units marked full | condensed | digest, a peaks
    # path, WEB text on expand). Absent = none of that exists in the build
    # or the shell (tiers.py)
    "tiers",
    # true = this book's echoes into a law (biblecore/laws.json) get a "Law
    # behind this" chip, from briefs the hub publishes. Absent = no chip code
    # in the shell (lawchip.js)
    "law_chips",
}
MIRROR_ENTRY_KEYS = {"with", "file"}
# Which verse numbering the book displays and cites: "kjv" (English Bibles;
# the corpus numbering is converted through the corpus's own map) or
# "source" (the corpus numbering as is).
VERSIFICATIONS = ("kjv", "source")
REQUIRED_KEYS = {"book", "osis", "slug", "language", "corpus"}

CORPUS_KEYS = {"kind", "pin", "word_ids"}
# `skip_fragment_checks` names hard fragment checks to switch off for a book
# (meta.FRAGMENT_CHECKS names, or "component:<name>" for one component's
# check). It exists for a book whose built units predate a check; a new
# book leaves it empty.
# `test_idempotent: false` drops `biblecore test`'s build-idempotence check
# for a book whose units are built by its own pipeline (Matthew).
# `colour_de_min` is the CIEDE2000 distance under which two colours read as
# one (colour.de_min). 10 is the default; a book that tracks more threads than
# a well of that spacing holds (about 60 colours) sets a lower floor and
# generates a well to match (tools/make_well.py).
# `doc_budget_kb` overrides selftest.DOC_BUDGET_KB per document for a book whose
# instruction files should stay tighter (or may run larger) than the default.
CHECK_DEFAULTS = {"opens_note_required": True, "skip_fragment_checks": [],
                  "test_idempotent": True, "colour_de_min": 10, "doc_budget_kb": {}}
# "sync" lists only what a book adds to or drops from core's default synced
# files (biblecore.sync.DEFAULT_SYNC): `extra` takes paths or glob patterns,
# `skip` takes paths or patterns matched against the resolved paths.
SYNC_KEYS = {"extra", "skip"}
# the pre-0.10.0 full lists; named in the error so a book knows what to do
OLD_SYNC_KEYS = {"files", "globs"}

# Every path a module reads or writes, relative to the book root. A book
# overrides any of these under "paths" in book.json (Joshua's layout differs
# from a fresh book's, and that is fine).
PATH_DEFAULTS = {
    "data": "data",
    "units": "units",
    # a folder (theme.css + generated core.css/components.css), or one file
    "css": "css",
    "source": "source-artifacts",
    "out": "out",
    "retrofit": "retrofit/retrofit-tags.json",
    "retro": "retrofit/retro-tags.json",
    "digest": "threads-digest.md",
    "canon_leads": "canon-leads",
    "wlc": "node_modules/morphhb/wlc",
    "morphgnt": "corpus/morphgnt",
    "lxx": "corpus/lxx",
    # World English Bible USFM, one file per book (tiered books; fetch.py)
    "web": "corpus/web",
    "lexicon": "corpus/lexicon/HebrewStrong.xml",
    "greek_lexicon": "corpus/lexicon/lexemes.yaml",
    "synced": "project-side/synced",
    "sync_state": "project-side/sync-state.json",
    # pasted by hand into the Claude.ai project's instruction field
    "chat_side": "CHAT_SIDE_INSTRUCTIONS.md",
    "palette": "data/palette.json",
    # Derived from the book name unless overridden; see Book.path().
    "words": None,
    "reading": None,
    "boundaries": "candidate-boundaries.md",
    "style_reference": None,
    "verse_map": None,
    "components_ref": "components-reference.md",
}


class BookError(ValueError):
    pass


def validate_config(cfg):
    """Problems with a parsed book.json ([] == clean)."""
    errs = []
    if not isinstance(cfg, dict):
        return ["book.json must be a JSON object"]
    for k in sorted(set(cfg) - ALLOWED_KEYS):
        errs.append(f"unknown key '{k}' -- add it to biblecore.book.ALLOWED_KEYS "
                    f"along with the code that reads it, or remove it")
    for k in sorted(REQUIRED_KEYS - set(cfg)):
        errs.append(f"missing required key '{k}'")
    corpus = cfg.get("corpus")
    if corpus is not None:
        if not isinstance(corpus, dict):
            errs.append("'corpus' must be an object")
        else:
            for k in sorted(set(corpus) - CORPUS_KEYS):
                errs.append(f"corpus: unknown key '{k}'")
            if "kind" not in corpus:
                errs.append("corpus: missing 'kind'")
    if "tiers" in cfg and not isinstance(cfg["tiers"], bool):
        errs.append("'tiers' must be true or false")
    if "law_chips" in cfg and not isinstance(cfg["law_chips"], bool):
        errs.append("'law_chips' must be true or false")
    for k in ("groupings", "components", "meta_keys"):
        if k in cfg and not (isinstance(cfg[k], list)
                             and all(isinstance(x, str) for x in cfg[k])):
            errs.append(f"'{k}' must be a list of strings")
    for k in sorted(set(cfg.get("checks") or {}) - set(CHECK_DEFAULTS)):
        errs.append(f"checks: unknown check '{k}' (known: {sorted(CHECK_DEFAULTS)})")
    de = (cfg.get("checks") or {}).get("colour_de_min", CHECK_DEFAULTS["colour_de_min"])
    if isinstance(de, bool) or not isinstance(de, (int, float)) or not 3 <= de <= 20:
        errs.append("checks.colour_de_min must be a number from 3 to 20")
    budget = (cfg.get("checks") or {}).get("doc_budget_kb", {})
    if not isinstance(budget, dict):
        errs.append("checks.doc_budget_kb must be an object of {document: KB}")
    else:
        from biblecore.selftest import DOC_BUDGET_KB
        for k, v in sorted(budget.items()):
            if k not in DOC_BUDGET_KB:
                errs.append(f"checks.doc_budget_kb: unknown document '{k}' "
                            f"(known: {sorted(DOC_BUDGET_KB)})")
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                errs.append(f"checks.doc_budget_kb.{k} must be a positive number")
    skip = (cfg.get("checks") or {}).get("skip_fragment_checks", [])
    if not (isinstance(skip, list) and all(isinstance(x, str) for x in skip)):
        errs.append("checks.skip_fragment_checks must be a list of strings")
    else:
        from biblecore import components, meta
        known = {n for _, n, _ in meta.FRAGMENT_CHECKS if n != "components"}
        known |= {f"component:{n}" for n in components.registry()}
        for k in sorted(set(skip) - known):
            errs.append(f"checks.skip_fragment_checks: unknown check '{k}' "
                        f"(known: {sorted(known)})")
    for k in sorted(set(cfg.get("paths") or {}) - set(PATH_DEFAULTS)):
        errs.append(f"paths: unknown path '{k}' (known: {sorted(PATH_DEFAULTS)})")
    sync = cfg.get("sync") or {}
    for k in sorted(set(sync) - SYNC_KEYS):
        if k in OLD_SYNC_KEYS:
            errs.append(f"sync: '{k}' was replaced in core 0.10.0 -- core supplies the "
                        f"default synced files (biblecore.sync.DEFAULT_SYNC); list only "
                        f"additions under sync.extra and exclusions under sync.skip")
        else:
            errs.append(f"sync: unknown key '{k}' (known: {sorted(SYNC_KEYS)})")
    for k in SYNC_KEYS & set(sync):
        if not (isinstance(sync[k], list) and all(isinstance(x, str) for x in sync[k])):
            errs.append(f"sync.{k} must be a list of strings")
    if "versification" in cfg and cfg["versification"] not in VERSIFICATIONS:
        errs.append(f"'versification' must be one of {list(VERSIFICATIONS)}")
    if "overlay" in cfg and cfg["overlay"] not in (cfg.get("groupings") or [])[1:]:
        errs.append("'overlay' must name one of the groupings after the first")
    if "overlay_note" in cfg:
        if not (isinstance(cfg["overlay_note"], str) and cfg["overlay_note"].strip()):
            errs.append("'overlay_note' must be a non-empty string")
        if "overlay" not in cfg:
            errs.append("'overlay_note' needs 'overlay'")
    if "component_labels" in cfg:
        cl = cfg["component_labels"]
        if not (isinstance(cl, dict) and all(isinstance(k, str) and isinstance(v, str) and v.strip()
                                             for k, v in cl.items())):
            errs.append("'component_labels' must be {component: label}")
        else:
            from biblecore import components as _c
            reg = _c.registry()
            for k in sorted(cl):
                if k not in reg or "toggle" not in reg[k].spec:
                    errs.append(f"component_labels: '{k}' is not a toggle component")
    if "template" in cfg and not (isinstance(cfg["template"], str)
                                  and re.fullmatch(r"[0-9a-f]{7,40}", cfg["template"])):
        errs.append("'template' must be a bible-core commit hash (7-40 hex digits)")
    if "palette" in cfg and not isinstance(cfg["palette"], (str, list)):
        errs.append("'palette' must be a path or a list of hex colours")
    if "mirrors" in cfg:
        errs += _validate_mirrors(cfg)
    return errs


def _validate_mirrors(cfg):
    """`mirrors`: a list of {with, file}. `with` is the OSIS id of another
    book in the corpus (not this one), `file` a bare .json name in data/.
    Only Hebrew books can mirror for now: the second book is read through
    the OSHB adapter."""
    ms = cfg["mirrors"]
    if not (isinstance(ms, list) and ms):
        return ["'mirrors' must be a non-empty list of {with, file}"]
    from biblecore.corpus import oshb
    errs, seen = [], set()
    if cfg.get("language") != "hebrew":
        errs.append("'mirrors' needs language 'hebrew' (the mirrored book is read "
                    "through OSHB; a Greek book's mirror comes later)")
    for i, m in enumerate(ms):
        where = f"mirrors[{i}]"
        if not isinstance(m, dict):
            errs.append(f"{where}: must be an object {{with, file}}")
            continue
        for k in sorted(set(m) - MIRROR_ENTRY_KEYS):
            errs.append(f"{where}: unknown key '{k}' -- {{with, file}}")
        w, f = m.get("with"), m.get("file")
        if w not in oshb.BOOK_IDS:
            errs.append(f"{where}: 'with' ({w!r}) must be an OSHB book id such as 'Exod'")
        elif w == cfg.get("osis"):
            errs.append(f"{where}: a book cannot mirror itself")
        elif w in seen:
            errs.append(f"{where}: '{w}' is listed twice")
        seen.add(w)
        if not (isinstance(f, str) and re.fullmatch(r"[A-Za-z0-9_.-]+\.json", f)):
            errs.append(f"{where}: 'file' ({f!r}) must be a bare file name ending .json "
                        f"(it lives in the data folder)")
    return errs


class Book:
    def __init__(self, cfg, root):
        errs = validate_config(cfg)
        if errs:
            raise BookError("book.json: " + "; ".join(errs))
        self.cfg = cfg
        self.root = os.path.abspath(root)

    @classmethod
    def from_file(cls, path, root=None):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cls(cfg, root or os.path.dirname(os.path.abspath(path)))

    # -- identity ------------------------------------------------------------
    @property
    def name(self):
        return self.cfg["book"]

    @property
    def osis(self):
        """OSHB/OSIS book id ('Num'); also the ref prefix in the reading text."""
        return self.cfg["osis"]

    @property
    def abbrev(self):
        """Display abbreviation for references ('Num 3:4')."""
        return self.cfg.get("abbrev", self.osis)

    @property
    def slug(self):
        """Lowercase file-name stem ('numbers' -> numbers_05_translation.html)."""
        return self.cfg["slug"]

    @property
    def language(self):
        return self.cfg["language"]

    @property
    def language_name(self):
        """The language as printed in messages ('Hebrew', 'Greek')."""
        return self.language.capitalize()

    @property
    def versification(self):
        return self.cfg.get("versification", "kjv")

    @property
    def word_ids(self):
        return bool(self.cfg["corpus"].get("word_ids", True))

    @property
    def groupings(self):
        """Grouping kinds a unit belongs to ('movement', ...). Each is an
        optional integer key in a unit's meta block and its units.json row."""
        return list(self.cfg.get("groupings", []))

    @property
    def components(self):
        return list(self.cfg.get("components", []))

    @property
    def meta_keys(self):
        return list(self.cfg.get("meta_keys", []))

    @property
    def tiers(self):
        """True for a tiered book; every tier code path is gated on this."""
        return self.cfg.get("tiers") is True

    @property
    def law_chips(self):
        """True when echoes into a law get a "Law behind this" chip."""
        return self.cfg.get("law_chips") is True

    @property
    def mirrors(self):
        """[{with, file}] the books this one mirrors (empty for most)."""
        return [dict(m) for m in self.cfg.get("mirrors", [])]

    def check(self, name):
        v = (self.cfg.get("checks") or {}).get(name, CHECK_DEFAULTS[name])
        return list(v) if isinstance(v, list) else v

    @property
    def storage_key(self):
        return self.cfg.get("storage_key", self.slug)

    # -- paths ---------------------------------------------------------------
    def path(self, key):
        rel = (self.cfg.get("paths") or {}).get(key, PATH_DEFAULTS[key])
        if rel is None:
            rel = {"words": f"{self.name}-words.tsv",
                   "reading": f"{self.name}-reading.txt",
                   "style_reference": f"{self.slug}_study_style_reference.md",
                   "verse_map": f"{self.slug}-versification.md",
                   }[key]
        return os.path.join(self.root, rel)

    def data(self, name):
        return os.path.join(self.path("data"), name)

    def unit_path(self, n):
        return os.path.join(self.path("units"), f"unit-{n:02d}.html")

    def source_glob(self, n):
        return os.path.join(self.path("source"), f"{self.slug}_{n:02d}_*.html")

    def palette(self):
        """The colour well, in preference order."""
        p = self.cfg.get("palette")
        if isinstance(p, list):
            return list(p)
        path = os.path.join(self.root, p) if p else self.path("palette")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return list(data["well"] if isinstance(data, dict) else data)

    def sync_files(self):
        """Repo-relative files that round-trip into the Claude.ai project:
        core's defaults plus sync.extra, minus sync.skip (biblecore.sync)."""
        from biblecore import sync
        return sync.resolve(self)


_current = None


def _discover():
    env = os.environ.get("BIBLECORE_BOOK")
    if env:
        path = env if env.endswith(".json") else os.path.join(env, "book.json")
        return Book.from_file(path)
    d = os.getcwd()
    while True:
        cand = os.path.join(d, "book.json")
        if os.path.exists(cand):
            return Book.from_file(cand)
        parent = os.path.dirname(d)
        if parent == d:
            raise BookError("no book.json found in the working directory or any "
                            "parent, and $BIBLECORE_BOOK is not set")
        d = parent


def book():
    global _current
    if _current is None:
        _current = _discover()
    return _current


def use(b):
    """Pin the current book (tests, or a caller that already has one).
    Clears every module cache keyed on the previous book."""
    global _current
    _current = b
    for fn in _reset_hooks:
        fn()
    return b


_reset_hooks = []


def on_reset(fn):
    """Register a cache-clearing function to run whenever the book changes."""
    _reset_hooks.append(fn)
    return fn
