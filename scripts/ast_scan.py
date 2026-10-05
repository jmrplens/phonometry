#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the guards that read the repository's own Python files share.

``check_raises_blocks.py`` and ``check_fence_readers.py`` each walk a tree of
files, name a finding by the file and the function that holds it, and keep an
escape hatch keyed the same way, which reports itself once it covers nothing.
The walking, the naming and the hatch live here once, so that the guards agree
on what a key is and a hatch entry written for one reads the same in the other.
``check_boundary_comparisons.py`` keeps a hatch of its own: its key names the
comparison as well as the function, and a line excuses one copy of it, so a
split by ``(file, function)`` would let a new comparison in under an old line.
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Keyed(Protocol):
    """A finding that names its file and the function that holds it."""

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the qualified function."""
        ...


def relative(path: pathlib.Path) -> str:
    """The path as the repository spells it, or as given outside it."""
    resolved = path.resolve()
    return (
        resolved.relative_to(ROOT).as_posix()
        if resolved.is_relative_to(ROOT)
        else path.as_posix()
    )


def python_files(arguments: Sequence[str], default: pathlib.Path) -> list[pathlib.Path]:
    """The files named, the Python files under the directories named, or ``default``'s."""
    if not arguments:
        return sorted(default.rglob("*.py"))
    files: list[pathlib.Path] = []
    for argument in arguments:
        path = pathlib.Path(argument)
        files.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return files


def scoped(tree: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    """Every node with the qualified name of the function or class that holds it.

    A node at module level comes with ``"<module>"``.
    """

    def walk(node: ast.AST, scope: str) -> Iterator[tuple[str, ast.AST]]:
        for child in ast.iter_child_nodes(node):
            inner = scope
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
            yield inner or "<module>", child
            yield from walk(child, inner)

    yield from walk(tree, "")


def exempted[FindingT: Keyed](
    findings: Sequence[FindingT], exempt: Mapping[tuple[str, str], str]
) -> tuple[list[FindingT], list[tuple[str, str]]]:
    """The findings no exemption covers, and the exemptions that cover none.

    :param findings: Every finding, exempt or not.
    :param exempt: The escape hatch, ``(file, function)`` to reason.
    :return: The findings left to report, and the sorted stale keys.
    """
    used = {finding.key for finding in findings}
    kept = [finding for finding in findings if finding.key not in exempt]
    return kept, sorted(set(exempt) - used)
