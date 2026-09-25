"""aside.echo: anchor present, well-formed and matching the verse it follows,
and never started inside an open .gloss (meta.check_anchored_aside)."""


def check(html, meta):
    from biblecore import meta as um
    return um.check_anchored_aside(html, meta, "echo")
