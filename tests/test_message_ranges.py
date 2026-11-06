#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A range of frequencies in a message a caller reads is written with "to".

The docstrings write a band range as "125 Hz to 8 kHz", and the refusals of
the same functions still wrote "(125 Hz - 8 kHz", a spaced hyphen that reads
as a minus beside numbers. This reads every text of the library that is no
docstring, the messages of its errors and warnings among them, and refuses a
frequency followed by a spaced hyphen.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

import phonometry

_SOURCE = pathlib.Path(phonometry.__file__).parent
#: A frequency and a spaced hyphen after it: the start of a range.
_RANGE = re.compile(r"Hz - ")


def _docstrings(tree: ast.AST) -> set[int]:
    """The ids of the docstrings of *tree*: its own, its classes' and functions'."""
    found = set()
    for node in ast.walk(tree):
        if (
            isinstance(
                node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
            )
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            found.add(id(node.body[0].value))
    return found


def _hyphenated_ranges() -> list[str]:
    found = []
    for path in sorted(_SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstrings(tree)
        found.extend(
            f"{path.relative_to(_SOURCE)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _RANGE.search(node.value)
        )
    return found


@pytest.mark.whole_tree
def test_no_message_writes_a_frequency_range_with_a_hyphen() -> None:
    assert _hyphenated_ranges() == []
