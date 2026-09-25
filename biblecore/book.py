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

ALLOWED_KEYS = {
    "book", "osis", "abbrev", "slug", "language", "corpus", "groupings",
    "components", "meta_keys", "checks", "palette", "sync", "storage_key",
    "paths", "core", "versification",
    # the canon hub's URL; the site links to it and reads its canon.json
    "hub",
}
# Which verse numbering the book displays and cites: "kjv" (English Bibles;
# the corpus numbering is converted through the corpus's own map) or
# "source" (the corpus numbering as is).
VERSIFICATIONS = ("kjv", "source")
REQUIRED_KEYS = {"book", "osis", "slug", "language", "corpus"}

CORPUS_KEYS = {"kind", "pin", "word_ids"}
CHECK_DEFAULTS = {"opens_note_required": True}
SYNC_KEYS = {"files", "globs"}

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
    "lexicon": "corpus/lexicon/HebrewStrong.xml",
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
    for k in ("groupings", "components", "meta_keys"):
        if k in cfg and not (isinstance(cfg[k], list)
                             and all(isinstance(x, str) for x in cfg[k])):
            errs.append(f"'{k}' must be a list of strings")
    for k in sorted(set(cfg.get("checks") or {}) - set(CHECK_DEFAULTS)):
        errs.append(f"checks: unknown check '{k}' (known: {sorted(CHECK_DEFAULTS)})")
    for k in sorted(set(cfg.get("paths") or {}) - set(PATH_DEFAULTS)):
        errs.append(f"paths: unknown path '{k}' (known: {sorted(PATH_DEFAULTS)})")
    for k in sorted(set(cfg.get("sync") or {}) - SYNC_KEYS):
        errs.append(f"sync: unknown key '{k}'")
    if "versification" in cfg and cfg["versification"] not in VERSIFICATIONS:
        errs.append(f"'versification' must be one of {list(VERSIFICATIONS)}")
    if "palette" in cfg and not isinstance(cfg["palette"], (str, list)):
        errs.append("'palette' must be a path or a list of hex colours")
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

    def check(self, name):
        return (self.cfg.get("checks") or {}).get(name, CHECK_DEFAULTS[name])

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
        """Repo-relative files that round-trip into the Claude.ai project."""
        import glob
        sync = self.cfg.get("sync") or {}
        files = list(sync.get("files", []))
        for pattern in sync.get("globs", []):
            files += sorted(os.path.relpath(p, self.root).replace(os.sep, "/")
                            for p in glob.glob(os.path.join(self.root, pattern)))
        return files


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
