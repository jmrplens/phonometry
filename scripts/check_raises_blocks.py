#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on an exception or warning test that more than one call could satisfy.

A ``with pytest.raises(...)`` block passes as soon as anything inside it
raises the error it names. When the block holds the call under test and also
the call that builds its input, a refusal from the builder satisfies the test
as well as one from the code it says it checks, and the test goes on passing
the day the code under test stops refusing. Seven tests of the catalogue
writer were in that state, each with ``io.write_catalogue(_mine(), path)``
inside the block, before a review caught them. ``pytest.warns`` and
``pytest.deprecated_call`` have the same shape and the same failure.

Ruff's PT012 and PT031 hold such a block to one simple statement. One
statement can still hold two calls, and that is the case this reads: SonarCloud
reports it as python:S5778 for exceptions and python:S9088 for warnings, but
only after a pull request is open, and the same mistake came back three times
that way. The definition is Sonar's, so the two agree on what they refuse.
Every call in the block counts, nested ones included, except the ones Sonar
holds safe because they are almost never the error under test: the
conversions and containers of the builtins (``float("nan")``, ``len(x)``,
``list(...)``), ``set()``, ``frozenset()`` and ``object()`` called without
arguments, the ``pathlib`` paths, ``uuid``, ``copy`` and anything in NumPy or
SciPy. A call inside a ``lambda`` or a nested ``def`` is deferred, not made, so
it does not count; a ``class`` statement runs its bases and its body as it is
read, so theirs do, and the lambda passed to ``pytest.raises(Error, lambda: ...)``
is the block itself, so its calls do too. Unlike Ruff, this also refuses a block of
several statements, so a ``noqa: PT012`` does not let one through.

The fix is the one Sonar suggests: build the input before the block, so that
the only call inside it is the one the test is about. :data:`EXEMPT` is the
escape hatch for a block that cannot be written that way, keyed by file and
test with the reason.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, python_files, relative, scoped

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterable

#: Where the tests live; the default when no path is given.
TESTS = ROOT / "tests"

#: The context managers that wait for one call to raise or warn.
WAITERS = frozenset({"pytest.raises", "pytest.warns", "pytest.deprecated_call"})

#: The builtins Sonar never counts: conversions, containers and inspection.
_SAFE_BUILTINS = (
    "str",
    "bytes",
    "bytearray",
    "repr",
    "ascii",
    "format",
    "bool",
    "int",
    "float",
    "complex",
    "memoryview",
    "list",
    "tuple",
    "dict",
    "print",
    "len",
    "abs",
    "round",
    "id",
    "hash",
    "hex",
    "oct",
    "bin",
    "ord",
    "chr",
    "range",
    "enumerate",
    "zip",
    "reversed",
    "sorted",
    "slice",
    "callable",
)
#: Calls Sonar never counts, by the name they resolve to.
_SAFE_CALLS = frozenset(
    {
        *(f"builtins.{name}" for name in _SAFE_BUILTINS),
        *(
            f"pathlib.{name}"
            for name in (
                "Path",
                "PurePath",
                "PosixPath",
                "WindowsPath",
                "PurePosixPath",
                "PureWindowsPath",
            )
        ),
        "uuid.UUID",
        *(f"uuid.uuid{version}" for version in (1, 3, 4, 5, 6, 7, 8)),
        "copy.copy",
        "copy.deepcopy",
    }
)
#: Packages every call into which Sonar holds safe.
_SAFE_PACKAGES = ("numpy.", "scipy.")
#: Constructors Sonar holds safe only when called with no argument at all.
_SAFE_WITHOUT_ARGUMENTS = frozenset(
    {"builtins.set", "builtins.frozenset", "builtins.object"}
)

#: Blocks that keep several calls, and why, keyed by the file relative to the
#: repository and the name of the test function that holds the block. Nothing
#: belongs here that could instead build its input before the block.
EXEMPT: dict[tuple[str, str], str] = {}


@dataclass(frozen=True)
class Finding:
    """One block that more than one call, or more than one statement, could satisfy."""

    path: pathlib.Path
    line: int
    test: str
    waiter: str
    calls: tuple[str, ...]
    statements: int

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the test, as EXEMPT keys them."""
        return relative(self.path), self.test

    def describe(self) -> str:
        """One line naming the block, the test and what is in it."""
        where = f"{relative(self.path)}:{self.line}"
        what = (
            f"{self.statements} statements"
            if self.statements > 1
            else f"{len(self.calls)} calls: {', '.join(self.calls)}"
        )
        return f"{where}  {self.test}  {self.waiter}  {what}"


def _aliases(tree: ast.AST) -> dict[str, str]:
    """The dotted name each imported name stands for, anywhere in the file."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    found[alias.asname] = alias.name
                else:
                    head = alias.name.split(".")[0]
                    found[head] = head
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                found[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return found


def _bound(tree: ast.AST) -> set[str]:
    """Every name the file binds itself, which then no longer means a builtin."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


class _Resolver:
    """Resolves what a callee names, through the imports of one file."""

    def __init__(self, tree: ast.AST) -> None:
        self._aliases = _aliases(tree)
        self._bound = _bound(tree) - set(self._aliases)

    def name(self, expression: ast.expr) -> str | None:
        """The dotted name a callee resolves to, or ``None`` when it is computed."""
        attributes: list[str] = []
        while isinstance(expression, ast.Attribute):
            attributes.append(expression.attr)
            expression = expression.value
        if not isinstance(expression, ast.Name):
            return None
        base = self._aliases.get(expression.id)
        if base is None:
            is_builtin = hasattr(builtins, expression.id)
            base = (
                f"builtins.{expression.id}"
                if is_builtin and expression.id not in self._bound
                else expression.id
            )
        return ".".join([base, *reversed(attributes)])

    def is_safe(self, call: ast.Call) -> bool:
        """Whether Sonar holds this call safe inside an exception test."""
        name = self.name(call.func)
        if name is None:
            return False
        if name in _SAFE_CALLS or name.startswith(_SAFE_PACKAGES):
            return True
        return name in _SAFE_WITHOUT_ARGUMENTS and not (call.args or call.keywords)


class _Calls(ast.NodeVisitor):
    """The calls a block makes, deferred ones left out."""

    def __init__(self, resolver: _Resolver) -> None:
        self.resolver = resolver
        self.found: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Count the call unless it is safe, then look inside it."""
        if not self.resolver.is_safe(node):
            self.found.append(node)
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """A lambda's body runs later, if at all."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """A nested function's body runs later, if at all."""

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """A nested coroutine's body runs later, if at all."""


def _unsafe_calls(nodes: Iterable[ast.AST], resolver: _Resolver) -> list[ast.Call]:
    """The calls that could raise among these nodes, in source order."""
    collector = _Calls(resolver)
    for node in nodes:
        collector.visit(node)
    return sorted(collector.found, key=lambda call: (call.lineno, call.col_offset))


def _label(call: ast.Call, resolver: _Resolver) -> str:
    """How a call is named in the report: its callee, as written or resolved."""
    name = resolver.name(call.func)
    if name is not None:
        return name.removeprefix("builtins.")
    if isinstance(call.func, ast.Attribute):
        return f"(...).{call.func.attr}"
    return ast.unparse(call.func)


def _block(node: ast.AST, resolver: _Resolver) -> tuple[str, list[ast.AST], int] | None:
    """What waits in a node, its body and its statement count, or ``None``.

    A ``with`` block waits on its body. ``pytest.raises(Error, lambda: ...)``
    waits on the lambda, which runs inside the check.
    """
    if isinstance(node, ast.With | ast.AsyncWith):
        waiters = [
            name
            for item in node.items
            if isinstance(item.context_expr, ast.Call)
            and (name := resolver.name(item.context_expr.func)) in WAITERS
        ]
        return (
            (" + ".join(waiters), list(node.body), len(node.body)) if waiters else None
        )
    if not isinstance(node, ast.Call) or resolver.name(node.func) not in WAITERS:
        return None
    lambdas = [argument for argument in node.args if isinstance(argument, ast.Lambda)]
    return (str(resolver.name(node.func)), [lambdas[0].body], 1) if lambdas else None


def findings(path: pathlib.Path) -> list[Finding]:
    """The blocks of one file that more than one call could satisfy.

    :param path: A Python file.
    :return: One :class:`Finding` per offending block, in source order.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    resolver = _Resolver(tree)
    found: list[Finding] = []
    for test, node in scoped(tree):
        block = _block(node, resolver)
        if block is None:
            continue
        waiter, body, statements = block
        calls = _unsafe_calls(body, resolver)
        if len(calls) > 1 or statements > 1:
            found.append(
                Finding(
                    path=path,
                    line=getattr(node, "lineno", 0),
                    test=test,
                    waiter=waiter,
                    calls=tuple(_label(call, resolver) for call in calls),
                    statements=statements,
                )
            )
    return found


def check(
    paths: Iterable[pathlib.Path], exempt: dict[tuple[str, str], str]
) -> tuple[list[Finding], list[tuple[str, str]], int]:
    """The offending blocks, the stale exemptions and the number of files read.

    :param paths: The Python files to read.
    :param exempt: The escape hatch, ``(file, test)`` to reason.
    :return: The findings no exemption covers, the exemptions that cover no
        finding any more, and how many files were read.
    """
    files = list(paths)
    kept, stale = exempted([f for path in files for f in findings(path)], exempt)
    return kept, stale, len(files)


def main(argv: list[str] | None = None) -> int:
    """Report every exception or warning test that more than one call could satisfy."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="*", help="files or directories to read (default: tests/)"
    )
    arguments = parser.parse_args(argv)
    found, stale, read = check(python_files(arguments.paths, TESTS), EXEMPT)
    if not found and not stale:
        print(
            f"Every pytest.raises, pytest.warns and pytest.deprecated_call "
            f"block in {read} files waits on one call."
        )
        return 0
    if found:
        print(
            f"::error::{len(found)} exception or warning test(s) wait on more than one call"
        )
        for finding in found:
            print(f"  {finding.describe()}")
        print(
            "  -> build the input before the block, so that the only call inside "
            "it is the one the test is about (Sonar python:S5778 and S9088). If "
            "it cannot be, add it to EXEMPT in scripts/check_raises_blocks.py "
            "with the reason."
        )
    for path, test in stale:
        print(f"::error::EXEMPT lists {path} {test}, which no longer has such a block")
    return 1


if __name__ == "__main__":
    sys.exit(main())
