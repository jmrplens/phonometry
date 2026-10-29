#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a reader in the library that opens a file without asking what it is.

A name a caller or the environment hands the library can hold something other
than a file: a named pipe no one writes to keeps an open waiting for a writer
that may never come, a device such as ``/dev/zero`` keeps a read going
without end, and a directory holds nothing to read. Every reader of such a
name refuses each before it waits on it, through the shared check of
``src/phonometry/_internal/json_input.py``: :func:`open_regular` and
:func:`read_at_most` look at the name, open it without waiting and ask the
open file again, and :func:`not_regular_at` says what is at a name that a
reader of another library is about to open itself.

This reads every module under ``src/phonometry`` but the shared one and
reports two shapes:

- **An open of its own**: ``open()``, ``io.open()`` or ``os.open()``, a
  ``.open()`` with no mode or a mode that reads without writing (``"rb"``,
  ``"r"``), and ``.read_bytes()`` and ``.read_text()``. A reader opens a
  file through the shared check instead; a mode that writes (``"wb"``,
  ``"xb"``, ``"ab"``, ``"r+b"``) is a writer's, and a ``.open()`` whose
  first argument is not a text is no file's.
- **A reader of another library that opens the name itself**: SciPy's
  ``wavfile.read``, python-soundfile's ``read``, ``info``, ``blocks`` and
  ``SoundFile``, NumPy's ``load``, ``loadtxt``, ``genfromtxt``, ``fromfile``
  and ``memmap``, and the ``open`` of ``wave``, ``aifc``, ``gzip``, ``bz2``,
  ``lzma``, ``tarfile``, ``codecs`` and Pillow's ``Image``, and
  ``zipfile.ZipFile``, each unless its mode writes. Each must follow, in the same
  function, a call of a check on the same name: one of the three shared
  functions, or a function of the library whose first parameter it hands to
  one of them (found by following such calls until no new one turns up, so
  ``require_regular_audio(path)`` counts, and so does a reader that calls it
  on its own first parameter). The name is compared as written, once
  ``str()``, ``Path()`` and ``os.fspath()`` around it are taken off.

The order is read from the source, not from the paths the function can take:
a check inside one branch of an ``if`` and a read after the ``if`` pass. A
``.open()`` given its mode through a name is not read either. The check is
there to keep the readers on the shared route, and the tests of each reader
(a pipe, a device and a directory at the name, each refused within seconds)
are what prove they refuse.

A read of the library's own files, which no caller names (the package's data
through ``importlib.resources``, its own modules), goes in :data:`EXEMPT`,
keyed by file and function with the reason; an entry that covers nothing is
reported too.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, python_files, relative

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator, Sequence

#: The library this reads, the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"
#: The module that holds the shared check, whose opens are the check itself,
#: by the end of its path, so that another checkout of the library is read the
#: same way.
OWNER = ("phonometry", "_internal", "json_input.py")

#: The shared functions that look at what a name holds before it is read.
CHECKS = frozenset({"not_regular_at", "open_regular", "read_at_most"})

#: The readers of other libraries that open a name themselves, by the name the
#: library is imported as and the function.
FOREIGN_READERS = frozenset(
    {
        ("wavfile", "read"),
        ("sf", "read"),
        ("sf", "info"),
        ("sf", "blocks"),
        ("sf", "SoundFile"),
        ("soundfile", "read"),
        ("soundfile", "info"),
        ("soundfile", "blocks"),
        ("soundfile", "SoundFile"),
        ("np", "load"),
        ("np", "loadtxt"),
        ("np", "genfromtxt"),
        ("np", "fromfile"),
        ("np", "memmap"),
        ("numpy", "load"),
        ("numpy", "loadtxt"),
        ("numpy", "genfromtxt"),
        ("numpy", "fromfile"),
        ("numpy", "memmap"),
        ("wave", "open"),
        ("aifc", "open"),
        ("gzip", "open"),
        ("bz2", "open"),
        ("lzma", "open"),
        ("tarfile", "open"),
        ("zipfile", "ZipFile"),
        ("codecs", "open"),
        ("Image", "open"),
    }
)
#: The readers of :data:`FOREIGN_READERS` that write when their mode says so,
#: and the position of the mode among their arguments.
_MODE_POSITION = {"SoundFile": 1, "open": 1, "ZipFile": 1}
#: The calls taken off a name before two names are compared.
_WRAPPERS = frozenset({"str", "Path", "PurePath", "fspath"})
#: The methods that read a whole file by its name.
_WHOLE_FILE_READS = frozenset({"read_bytes", "read_text"})

#: The reads of the library's own files, which no caller names, keyed by the
#: file relative to the repository and the function that holds the read.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_version.py", "<module>"): (
        "the VERSION file of a source checkout, two directories above the "
        "package, read only when the package is not installed"
    ),
    ("src/phonometry/_internal/catalogue.py", "read_packaged"): (
        "a published table of the package's own data, through importlib.resources"
    ),
    ("src/phonometry/aircraft/anp_fleet.py", "_table_text"): (
        "an ANP table of the package's own data when the package is inside a zip "
        "archive; a caller's table, and the package's on a file system, go "
        "through read_at_most"
    ),
    ("src/phonometry/simulation/_remote/client.py", "_inline_bootstrap"): (
        "the library's own bootstrap module, sent to a node as its source"
    ),
    ("src/phonometry/simulation/_remote/package.py", "package_from"): (
        "the files of the imported phonometry package itself, each taken only "
        "when is_file() finds a regular file there"
    ),
    ("src/phonometry/simulation/video.py", "_node_video"): (
        "_PartialFile.open, a method of the library's own that creates the "
        "partial video exclusively; no file is read"
    ),
}


@dataclass(frozen=True)
class Finding:
    """One read of a file by its name that skips the shared check."""

    path: pathlib.Path
    line: int
    function: str
    shape: str
    source: str

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the function, as EXEMPT keys them."""
        return relative(self.path), self.function

    def describe(self) -> str:
        """One line naming the place, the shape and the code."""
        return (
            f"{relative(self.path)}:{self.line}  {self.function}  "
            f"{self.shape}: {self.source}"
        )


def _callee(call: ast.Call) -> str | None:
    """The name a call is made through: ``f`` of ``f()`` and of ``a.b.f()``."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _receiver(call: ast.Call) -> str | None:
    """The last name before the method: ``b`` of ``a.b.f()``, ``a`` of ``a.f()``."""
    if not isinstance(call.func, ast.Attribute):
        return None
    value = call.func.value
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return None


def _subject(node: ast.expr) -> str:
    """A name as written, with ``str()``, ``Path()`` and ``os.fspath()`` taken off."""
    while (
        isinstance(node, ast.Call)
        and _callee(node) in _WRAPPERS
        and len(node.args) == 1
        and not node.keywords
    ):
        node = node.args[0]
    return ast.unparse(node)


def _first_argument(call: ast.Call) -> ast.expr | None:
    """The first argument of *call*, positional or the only keyword one."""
    if call.args:
        first = call.args[0]
        return None if isinstance(first, ast.Starred) else first
    if len(call.keywords) == 1 and call.keywords[0].arg is not None:
        return call.keywords[0].value
    return None


def _mode(call: ast.Call, position: int) -> ast.expr | None:
    """The mode a call opens with: the argument at *position* or ``mode=``."""
    for keyword in call.keywords:
        if keyword.arg == "mode":
            return keyword.value
    if len(call.args) > position:
        return call.args[position]
    return None


def _reads_only(mode: ast.expr | None) -> bool:
    """Whether a mode reads without writing; an unknown mode counts as a read."""
    if mode is None:
        return True
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return "r" in mode.value and "+" not in mode.value
    return True


def _own_open(call: ast.Call) -> bool:
    """Whether *call* opens or reads a file by its name, by itself."""
    callee = _callee(call)
    receiver = _receiver(call)
    if isinstance(call.func, ast.Name) and callee == "open":
        return _reads_only(_mode(call, 1))
    if callee == "open" and receiver == "io":
        return _reads_only(_mode(call, 1))
    if callee == "open" and receiver == "os":
        return True
    if callee in _WHOLE_FILE_READS and isinstance(call.func, ast.Attribute):
        return True
    if callee == "open" and isinstance(call.func, ast.Attribute):
        mode = _mode(call, 0)
        if mode is None:
            return True
        # A first argument that is not a text is no mode: a method of
        # another object that is called open.
        return (
            isinstance(mode, ast.Constant)
            and isinstance(mode.value, str)
            and _reads_only(mode)
        )
    return False


def _foreign_read(call: ast.Call) -> bool:
    """Whether *call* is a reader of another library that opens a name itself."""
    callee = _callee(call)
    receiver = _receiver(call)
    if callee is None or (receiver, callee) not in FOREIGN_READERS:
        return False
    position = _MODE_POSITION.get(callee)
    return position is None or _reads_only(_mode(call, position))


def _functions(tree: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    """Every function with its qualified name, and the module as ``<module>``."""

    def walk(node: ast.AST, scope: str) -> Iterator[tuple[str, ast.AST]]:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
                if not isinstance(child, ast.ClassDef):
                    yield inner, child
                yield from walk(child, inner)

    yield "<module>", tree
    yield from walk(tree, "")


def _own_calls(scope: ast.AST) -> list[ast.Call]:
    """The calls of *scope* in source order, leaving out those of nested functions.

    The body of a class belongs to the scope that holds the class, its methods
    to themselves.
    """
    calls: list[ast.Call] = []
    pending = list(ast.iter_child_nodes(scope))
    while pending:
        node = pending.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if isinstance(node, ast.Call):
            calls.append(node)
        pending.extend(ast.iter_child_nodes(node))
    calls.sort(key=lambda call: (call.lineno, call.col_offset))
    return calls


@dataclass(frozen=True)
class _Scope:
    """A function of a module, or the module itself, with the calls it makes."""

    path: pathlib.Path
    name: str
    node: ast.AST
    calls: list[ast.Call]


def _scopes(path: pathlib.Path, tree: ast.AST) -> list[_Scope]:
    """Every function of *tree*, and the module, each with its own calls."""
    return [
        _Scope(path, name, node, _own_calls(node)) for name, node in _functions(tree)
    ]


def _first_parameter(function: ast.AST) -> str | None:
    """The first parameter of a function that is not ``self`` or ``cls``."""
    if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
        return None
    for parameter in (*function.args.posonlyargs, *function.args.args):
        if parameter.arg not in {"self", "cls"}:
            return parameter.arg
    return None


def checking_functions(scopes: Sequence[_Scope]) -> frozenset[str]:
    """:data:`CHECKS` and every function that hands its first parameter to one.

    Followed until no new function turns up, so a reader that checks its name
    through a helper counts as a check for its own callers.
    """
    # Each function with the callees it hands its first parameter to, worked
    # out once; the search below only grows the set of checks.
    candidates: list[tuple[str, set[str]]] = []
    for scope in scopes:
        parameter = _first_parameter(scope.node)
        if parameter is None or not isinstance(
            scope.node, ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        handed = {
            callee
            for call in scope.calls
            if (callee := _callee(call)) is not None
            and (argument := _first_argument(call)) is not None
            and _subject(argument) == parameter
        }
        if handed:
            candidates.append((scope.node.name, handed))
    found = set(CHECKS)
    grew = True
    while grew:
        grew = False
        for name, handed in candidates:
            if name not in found and not handed.isdisjoint(found):
                found.add(name)
                grew = True
    return frozenset(found)


def _checked_before(
    calls: Sequence[ast.Call], read: ast.Call, checks: frozenset[str]
) -> bool:
    """Whether a check of the name *read* opens comes before it in the function."""
    argument = _first_argument(read)
    if argument is None:
        return False
    name = _subject(argument)
    place = (read.lineno, read.col_offset)
    for call in calls:
        if call is read or (call.lineno, call.col_offset) >= place:
            continue
        checked = _first_argument(call)
        if (
            _callee(call) in checks
            and checked is not None
            and _subject(checked) == name
        ):
            return True
    return False


def scan(scope: _Scope, checks: frozenset[str]) -> list[Finding]:
    """Every read of a file by its name in *scope* that skips the shared check."""
    findings: list[Finding] = []
    for call in scope.calls:
        if _own_open(call):
            shape = "an open of its own; read through open_regular or read_at_most"
        elif _foreign_read(call) and not _checked_before(scope.calls, call, checks):
            shape = (
                "a reader of another library with no check of the name before it; "
                "ask not_regular_at, or a check of the library, first"
            )
        else:
            continue
        findings.append(
            Finding(scope.path, call.lineno, scope.name, shape, ast.unparse(call))
        )
    return findings


def check(files: Sequence[pathlib.Path]) -> tuple[list[Finding], list[tuple[str, str]]]:
    """The findings :data:`EXEMPT` does not cover, and its entries that cover none.

    :param files: The modules to read; the shared module is left out.
    """
    scopes = [
        scope
        for path in files
        for scope in _scopes(
            path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        )
    ]
    checks = checking_functions(scopes)
    findings = [
        finding
        for scope in scopes
        if scope.path.resolve().parts[-len(OWNER) :] != OWNER
        for finding in scan(scope, checks)
    ]
    return exempted(findings, EXEMPT)


def main(argv: Sequence[str] | None = None) -> int:
    """Report every read that skips the shared check; 1 when there is one."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        help="modules or directories to read (default: src/phonometry)",
    )
    args = parser.parse_args(argv)
    files = python_files(args.paths, SOURCE)
    findings, stale = check(files)
    if args.paths:
        # An exemption is stale only against the whole library.
        stale = []
    for finding in findings:
        print(finding.describe())
    for file, function in stale:
        print(f"{file}  {function}  exempt, but reads nothing there any more")
    if findings or stale:
        print(
            f"\n{len(findings)} read(s) of a file by its name skip the shared check, "
            f"and {len(stale)} exemption(s) cover none.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Every reader of the {len(files)} modules read asks what a name holds first."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
