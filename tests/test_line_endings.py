"""CRLF -> LF warnings on Windows: git warns when a tracked data/*.json or
retrofit/*.json is left with CRLF in the working tree. The core always writes
LF (every text write passes newline="\n"; the books' .gitattributes say
`* text=auto eol=lf`); `biblecore test` reports any such file that something
else wrote."""
import ast
import glob
import os
import shutil
import tempfile

import support
support.joshua_book()
from biblecore import selftest  # noqa: E402

CORE_PKG = os.path.join(support.CORE, "biblecore")


def _text_writes_without_newline():
    """(file:line) of every open(..., 'w'/'a'/'x') or write_text(...) in the
    package that doesn't say newline= (binary modes excepted)."""
    bad = []
    for path in sorted(glob.glob(os.path.join(CORE_PKG, "**", "*.py"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kw = {k.arg for k in node.keywords}
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for k in node.keywords:
                    if k.arg == "mode" and isinstance(k.value, ast.Constant):
                        mode = k.value.value
                if (isinstance(mode, str) and mode[:1] in "wax" and "b" not in mode
                        and "newline" not in kw):
                    bad.append(f"{os.path.relpath(path, CORE_PKG)}:{node.lineno}")
            elif isinstance(fn, ast.Attribute) and fn.attr == "write_text" and "newline" not in kw:
                bad.append(f"{os.path.relpath(path, CORE_PKG)}:{node.lineno}")
    return bad


def test_the_core_never_writes_text_without_saying_newline():
    bad = _text_writes_without_newline()
    assert not bad, ("text writes that would be CRLF on Windows (add newline=\"\\n\"): "
                     + ", ".join(bad))


def test_crlf_in_policy_files_is_noted_with_the_file_names():
    root = tempfile.mkdtemp(prefix="bc-crlf-")
    try:
        for rel, data in {"data/a.json": b'{\r\n "x": 1\r\n}\r\n',
                          "data/ok.json": b'{\n "x": 1\n}\n',
                          "retrofit/r.json": b'{\r\n}\r\n'}.items():
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            with open(os.path.join(root, rel), "wb") as fh:
                fh.write(data)
        from biblecore import book as bookmod
        real = bookmod.book()
        bookmod.use(bookmod.Book(dict(real.cfg), root))
        try:
            notes = selftest.crlf_notes()
        finally:
            bookmod.use(real)
        assert len(notes) == 1, notes
        assert "data/a.json" in notes[0] and "retrofit/r.json" in notes[0], notes
        assert "ok.json" not in notes[0], notes
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_lf_only_files_give_no_note():
    root = tempfile.mkdtemp(prefix="bc-lf-")
    try:
        os.makedirs(os.path.join(root, "data"))
        with open(os.path.join(root, "data", "a.json"), "wb") as fh:
            fh.write(b'{\n}\n')
        from biblecore import book as bookmod
        real = bookmod.book()
        bookmod.use(bookmod.Book(dict(real.cfg), root))
        try:
            assert selftest.crlf_notes() == []
        finally:
            bookmod.use(real)
    finally:
        shutil.rmtree(root, ignore_errors=True)
