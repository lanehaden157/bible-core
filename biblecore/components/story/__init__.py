"""aside.story: an earlier story told beside a verse (meta.check_anchored_aside
for the anchor), with its header and the parts a reader needs: the story,
what's different, what it does here. Nothing ships without a stated
difference, and nothing weak ships at all."""
import re

KINDS = ("type-scene", "story", "allusion", "character", "reuse")
STRENGTHS = ("strong", "possible")
REQUIRED = ("par-story", "par-diff", "par-does")

OPEN_RE = re.compile(r'<aside\s+class="story"([^>]*)>(.*?)</aside>', re.S)
ANCHOR_RE = re.compile(r'data-anchor="([^"]*)"')
SPAN_RE = re.compile(r'^\d+:\d+[–-](?:\d+:)?\d+$')
SCENE_ID_RE = re.compile(r'^[a-z0-9-]+$')
SCRIPT_RE = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff\u0590-\u05ff\ufb1d-\ufb4f]')
ROOT_RE = re.compile(r'data-root=|class="(?:[^"]*\s)?rl?(?:\s[^"]*)?"')
HEAD_RE = re.compile(r'<h4\b[^>]*>(.*?)</h4>', re.S)


def _attr(attrs, name):
    m = re.search(r'\b' + name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _has_class(body, cls):
    return re.search(r'class="(?:[^"]*\s)?' + re.escape(cls) + r'(?:\s[^"]*)?"', body) is not None


def check(html, meta):
    from biblecore import canon
    from biblecore import meta as um
    errs = um.check_anchored_aside(html, meta, "story")
    for attrs, body in OPEN_RE.findall(html):
        am = ANCHOR_RE.search(attrs)
        where = f"aside.story at {am.group(1)!r}" if am else "aside.story"
        kind = _attr(attrs, "data-kind")
        if kind not in KINDS:
            errs.append(f"{where}: data-kind={kind!r} must be one of {list(KINDS)}")
        strength = _attr(attrs, "data-strength")
        if strength not in STRENGTHS:
            errs.append(f"{where}: data-strength={strength!r} must be one of "
                        f"{list(STRENGTHS)} (a weak link never ships as a story box)")
        span = _attr(attrs, "data-span")
        if span is not None and not SPAN_RE.match(span):
            errs.append(f"{where}: data-span={span!r} must be 'C:V–C:V' or 'C:V–V'")
        scene = _attr(attrs, "data-scene")
        if kind == "type-scene" and not (scene and SCENE_ID_RE.match(scene)):
            errs.append(f"{where}: a type-scene box needs data-scene=\"<id>\" "
                        f"([a-z0-9-], e.g. 'water-crossing')")
        if scene is not None and kind != "type-scene":
            errs.append(f"{where}: data-scene belongs only on data-kind=\"type-scene\"")
        head = HEAD_RE.search(body)
        if not head:
            errs.append(f"{where}: no <h4> header (par-ref and par-title)")
        else:
            ref = re.search(r'<span class="par-ref">(.*?)</span>', head.group(1), re.S)
            if not ref or not canon.parse_refs(ref.group(1)):
                errs.append(f"{where}: the <h4> needs a <span class=\"par-ref\"> naming "
                            f"a reference like 'Gen 40:20–22'")
            if not _has_class(head.group(1), "par-title"):
                errs.append(f"{where}: the <h4> needs a <span class=\"par-title\">")
        for part in REQUIRED:
            if not _has_class(body, part):
                errs.append(f"{where}: no .{part}"
                            + (" (no story box ships without a stated difference)"
                               if part == "par-diff" else ""))
        if SCRIPT_RE.search(body) or SCRIPT_RE.search(attrs):
            errs.append(f"{where}: Greek or Hebrew script inside; transliterate it")
        if ROOT_RE.search(body):
            errs.append(f"{where}: no data-root, class=\"r\" or class=\"rl\" inside "
                        f"(the occurrence scanner counts every data-root)")
    return errs
