"""tools/hub_build.py: the canon hub's data, read-only over the sibling
book repos."""
import os
import sys

import support

sys.path.insert(0, os.path.join(support.CORE, "tools"))
import hub_build  # noqa: E402


def teardown():
    support.joshua_book()


def test_hub_data():
    if not support.have_joshua():
        return ["Joshua checkout not found next to bible-core"]
    out = hub_build.build()
    books = out["books.json"]["books"]
    fails = []
    if len(books) != 66:
        fails.append(f"{len(books)} books in the canon map")
    started = {b["slug"]: b for b in books if b.get("site")}
    if "joshua" not in started:
        fails.append("Joshua missing from the started books")
    else:
        j = started["joshua"]
        if j["link"] != "v" or not j["groups"] or j["units_built"] < 4:
            fails.append(f"joshua entry: link={j['link']} groups={len(j['groups'])} built={j['units_built']}")
    lem = out["concordance.json"]["lemmas"]
    natan = lem.get("heb:5414", {}).get("books", {})
    if "joshua" not in natan or natan["joshua"]["n"] < 50:
        fails.append(f"natan across books: {natan and {k: v['n'] for k, v in natan.items()}}")
    canon = out["canon.json"]
    for k in ("arcs", "threads", "typescenes", "intertext", "paths"):
        if not canon.get(k):
            fails.append(f"canon.{k} empty")
    arcs = {a["id"] for a in canon["arcs"]}
    for p in canon["paths"]:
        if p["arc"] not in arcs:
            fails.append(f"path {p['id']} names unknown arc {p['arc']}")
    return fails


def test_hub_source_files_exist():
    return [f for f in hub_build.SOURCE_FILES
            if not os.path.exists(os.path.join(support.CORE, "hub", f))]
