"""python -m biblecore: every subcommand answers -h/--help with its usage and
does nothing else. (`sync --help` used to mirror, commit and push;
`colour --help` printed a colour for a thread named '--help'.)"""
import contextlib
import importlib
import io

import support
from biblecore import __main__ as cli

support.joshua_book()

# these parse their arguments with argparse, which prints the usage and
# exits 0 on --help before anything runs (checked below)
ARGPARSED = cli.ARGPARSED


def _ran(*_a, **_k):
    raise AssertionError("the command ran")


def test_help_never_runs_a_command():
    fails = []
    for cmd, (mod, fn) in sorted(cli.COMMANDS.items()):
        if cmd in ARGPARSED:
            continue
        m = importlib.import_module(mod)
        real = getattr(m, fn)
        setattr(m, fn, _ran)
        try:
            for flag in ("--help", "-h"):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    rc = cli.main([cmd, flag])
                if rc != 0 or "python -m biblecore" not in out.getvalue():
                    fails.append(f"{cmd} {flag}: rc {rc}, printed {out.getvalue()[:80]!r}")
        except AssertionError:
            fails.append(f"{cmd} --help ran the command")
        finally:
            setattr(m, fn, real)
    for cmd, fn in (("corpus", "_corpus"), ("book", "_show_book")):
        real = getattr(cli, fn)
        setattr(cli, fn, _ran)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cli.main([cmd, "--help"])
            if rc != 0:
                fails.append(f"{cmd} --help: rc {rc}")
        except AssertionError:
            fails.append(f"{cmd} --help ran the command")
        finally:
            setattr(cli, fn, real)
    return fails


def test_argparse_commands_print_usage_and_exit_0():
    fails = []
    for cmd in sorted(ARGPARSED):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                cli.main([cmd, "--help"])
            fails.append(f"{cmd} --help didn't exit")
        except SystemExit as exc:
            if exc.code != 0 or "usage:" not in out.getvalue():
                fails.append(f"{cmd} --help: exit {exc.code}, printed {out.getvalue()[:80]!r}")
    return fails
