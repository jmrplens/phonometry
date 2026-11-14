#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Every script writes its text files with line feeds, whatever the platform.

The scripts write files the repository commits: the generated site pages,
``llms.txt`` and its shards, the catalogue data, the conformance badges, the
figure baselines and the lock files. A text write in Python translates each
``\n`` to the platform's line end unless it is told otherwise, so on Windows
``Path.write_text(text, encoding="utf8")`` writes a carriage return before
every line feed. The file then differs, byte for byte, from the one CI
writes, and a ``--check`` that reads it back through universal newlines does
not see it. ``scripts/generate_site_reports.py`` wrote its pages that way,
and so did thirty-odd other writers.

This reads every module under ``scripts/`` and fails on a text write that
does not name its ``newline``: a ``write_text`` call, and an ``open`` (the
built-in, ``io.open`` or a path's ``.open``) whose mode writes text. A binary
mode, and the ``open`` of an archive module, write bytes and are left alone.

A script can write a file through its standard output too, when a recipe
redirects it, and ``sys.stdout`` turns each ``\n`` into ``\r\n`` on Windows
as a text file does: ``make conformance`` wrote ``docs/CONFORMANCE.md`` as
``scripts/conformance_report.py --file-header > docs/CONFORMANCE.md``. So the
Makefile, the git hooks and the workflows are read as well, and a command
that runs Python with its output redirected into a file git tracks fails
here: the script has to write that file itself.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess

import pytest

pytestmark = pytest.mark.whole_tree

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

#: The files whose commands a contributor or CI runs: the Makefile, the git
#: hooks and the workflows, by their paths from the repository root.
COMMAND_FILES = (
    "Makefile",
    "hooks/*",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
)

#: A command that runs Python, as the Makefile, a hook or a workflow spells it.
_PYTHON = re.compile(r"(?:\$\(PYTHON\)|\$\{?PYTHON\}?|\bpython3?\b|/bin/python3?\b)")

#: A redirect of standard output into a file, and the file it names: ``>``
#: or ``>>`` not preceded by a digit or ``&`` (``2>``, ``&>`` redirect other
#: streams too, which a write of the report never wants) and not ``>&``.
_REDIRECT = re.compile(r"(?<![0-9&>])>>?(?!&)\s*(?P<path>[^\s;|&)]+)")

#: A ``tee`` and the first file it writes.
_TEE = re.compile(r"\btee\s+(?:-a\s+)?(?P<path>[^\s;|&)-][^\s;|&)]*)")

#: Modules whose ``open`` writes bytes whatever its mode says.
ARCHIVES = frozenset({"bz2", "gzip", "lzma", "tarfile", "zipfile"})


def _mode(call: ast.Call, position: int) -> str | None:
    """The mode a call opens with, when it is written as a literal."""
    for keyword in call.keywords:
        if keyword.arg == "mode":
            value = keyword.value
            return (
                value.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
                else None
            )
    if len(call.args) > position:
        value = call.args[position]
        return (
            value.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
            else None
        )
    return "r"


def text_writes_without_newline(source: str) -> list[int]:
    """The lines of the text writes in *source* that do not name ``newline``.

    :param source: A module's text.
    :return: One line number per such call, in order.
    """
    found: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or any(
            k.arg == "newline" for k in node.keywords
        ):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "write_text":
            found.append(node.lineno)
            continue
        if isinstance(func, ast.Name) and func.id == "open":
            mode = _mode(node, 1)
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            receiver = func.value
            if isinstance(receiver, ast.Name) and receiver.id in ARCHIVES:
                continue
            builtin_style = isinstance(receiver, ast.Name) and receiver.id == "io"
            mode = _mode(node, 1 if builtin_style else 0)
        else:
            continue
        if (
            mode is not None
            and "b" not in mode
            and any(flag in mode for flag in "wax+")
        ):
            found.append(node.lineno)
    return sorted(found)


def test_every_script_writes_its_text_with_line_feeds() -> None:
    """No text write under ``scripts/`` leaves its line ends to the platform."""
    offenders = [
        f"{path.relative_to(SCRIPTS.parent).as_posix()}:{line}"
        for path in sorted(SCRIPTS.rglob("*.py"))
        for line in text_writes_without_newline(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


@pytest.mark.parametrize(
    "call",
    [
        'path.write_text(text, encoding="utf-8")',
        'open(path, "w", encoding="utf-8")',
        'open(path, mode="a", encoding="utf-8")',
        'io.open(path, "w", encoding="utf-8")',
        'path.open("w", encoding="utf-8")',
        'path.open(mode="x", encoding="utf-8")',
        'open(path, "r+", encoding="utf-8")',
    ],
)
def test_a_text_write_without_its_newline_is_found(call: str) -> None:
    """Each form of a text write, written without ``newline``."""
    assert text_writes_without_newline(call) == [1]


@pytest.mark.parametrize(
    "call",
    [
        'path.write_text(text, encoding="utf-8", newline="\\n")',
        'open(path, "w", encoding="utf-8", newline="\\n")',
        'path.open("w", encoding="utf-8", newline="")',
        'open(path, "wb")',
        "open(path)",
        'path.open("r", encoding="utf-8")',
        'tarfile.open(fileobj=buffer, mode="w")',
        "path.write_bytes(data)",
    ],
)
def test_a_write_that_names_its_newline_or_writes_bytes_passes(call: str) -> None:
    """A newline named, a binary mode, a read and an archive are no offence."""
    assert text_writes_without_newline(call) == []


def _logical_lines(text: str) -> list[str]:
    """The commands of a file, a line continued with a backslash joined to the next."""
    return re.sub(r"\\\r?\n", " ", text).splitlines()


def python_redirects(text: str) -> list[str]:
    """The files *text* saves the output of a Python command into.

    A redirect of the command itself, and one of a later stage of its
    pipeline or a ``tee`` there, since the bytes Python wrote reach it as
    they are.

    :param text: A Makefile, a hook or a workflow.
    :return: Each path, as written, in order.
    """
    found: list[str] = []
    for line in _logical_lines(text):
        if line.lstrip().startswith("#"):
            continue
        for command in re.split(r"&&|\|\||;", line):
            ran_python = False
            for stage in command.split("|"):
                ran_python = ran_python or bool(_PYTHON.search(stage))
                if not ran_python:
                    continue
                found.extend(match["path"] for match in _REDIRECT.finditer(stage))
                found.extend(match["path"] for match in _TEE.finditer(stage))
    return [path.strip("'\"") for path in found]


def _tracked() -> frozenset[str]:
    """The files git tracks in this checkout."""
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=120,
    ).stdout
    return frozenset(name for name in listed.split("\0") if name)


@pytest.mark.git_checkout
def test_no_command_writes_a_tracked_file_through_the_output_of_python() -> None:
    """No recipe, hook or workflow saves a Python command's output to a tracked file."""
    tracked = _tracked()
    offenders = [
        f"{path.relative_to(ROOT).as_posix()}: > {target}"
        for pattern in COMMAND_FILES
        for path in sorted(ROOT.glob(pattern))
        if path.is_file()
        for target in python_redirects(path.read_text(encoding="utf-8"))
        if target in tracked
    ]
    assert offenders == []


@pytest.mark.parametrize(
    ("text", "paths"),
    [
        (
            "\t$(PYTHON) scripts/report.py --file-header > docs/REPORT.md\n",
            ["docs/REPORT.md"],
        ),
        ("\tpython3 scripts/a.py >> docs/log.md\n", ["docs/log.md"]),
        ("        run: python scripts/a.py > out.md\n", ["out.md"]),
        ("\t$(PYTHON) scripts/a.py \\\n\t\t--flag >docs/x.md\n", ["docs/x.md"]),
        ("\tcd site && $(PYTHON) ../scripts/a.py > 'docs/y.md'\n", ["docs/y.md"]),
        ("\t$(PYTHON) scripts/a.py 2> err.txt\n", []),
        ("\t$(PYTHON) scripts/a.py >&2\n", []),
        ("\t$(PYTHON) scripts/a.py --output docs/REPORT.md\n", []),
        ("\tgrep -E x requirements.txt > pins.txt\n", []),
        ("\t$(PYTHON) scripts/a.py | tee docs/z.md\n", ["docs/z.md"]),
        ("\t$(PYTHON) scripts/a.py | sort > docs/sorted.md\n", ["docs/sorted.md"]),
        ("\tgrep x f.txt > a.txt && $(PYTHON) scripts/a.py\n", []),
        ("\t# $(PYTHON) scripts/a.py > docs/old.md\n", []),
    ],
)
def test_a_redirect_of_python_output_is_read(text: str, paths: list[str]) -> None:
    """Each spelling of a redirect, and the ones that write no file of a Python command."""
    assert python_redirects(text) == paths
