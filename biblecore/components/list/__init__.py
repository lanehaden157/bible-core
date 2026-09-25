"""table.list: inside a section.block, a <th> header row, equal cell counts
(meta.check_table_list)."""


def check(html, meta):
    from biblecore import meta as um
    return um.check_table_list(html)
