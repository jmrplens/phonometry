#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public record that a notebook would show as its raw ``repr``.

Jupyter, VS Code, Colab and the IPython terminal display the last expression
of a cell whole. For a record with neither ``_repr_html_`` nor
``_repr_pretty_`` that is the ``repr`` :mod:`dataclasses` writes: every
field, and every array as numpy prints it, in full up to a thousand values
and cut short with ``...`` above that, so a record of a few arrays of some
hundred values scrolls past as pages of numbers.
``phonometry._internal.display.RichDisplay`` gives a record a table instead,
one line per field, an array summarised by its shape and range, and the
verdict of a record with ``passes`` as PASS or FAIL.

The rule: every public record (a dataclass or a named tuple that a public
module defines, or that a public module lists in ``__all__``; the set
``scripts/check_array_aliasing.py`` walks) inherits :data:`MECHANISM`,
itself or through the classes of the package it extends, and does not
define ``_repr_html_`` or ``_repr_pretty_`` of its own, which would set the
table aside. ``OwnsArrays``, which every record that can hold an array
inherits, is one of those classes: it gives a record the table because it
extends the mechanism, and only while it does. A named tuple cannot take a
base, so it defines the two methods, and each is a call to the function of
the mechanism that writes the table (:data:`NAMED_TUPLE_CALLS`).
:data:`EXEMPT` is the escape hatch, keyed by file and class, each entry with
its reason; an entry that covers nothing fails the check too.

Static, like the guard whose reading of the tree it shares: the classes,
their bases and the methods they define are read from the source.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from typing import TYPE_CHECKING

from ast_scan import exempted, python_files
from check_array_aliasing import SOURCE, ClassInfo, Finding, Tree

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The base that gives a record its table. ``OwnsArrays``, which every record
#: that can hold an array inherits, is read like any other class of the
#: package: it gives the table because it extends this, and only while it does.
MECHANISM = "RichDisplay"

#: What each display method of a named tuple calls.
NAMED_TUPLE_CALLS: Mapping[str, str] = {
    "_repr_html_": "record_html",
    "_repr_pretty_": "record_pretty",
}

#: Public records that keep a display of their own, keyed by file and class,
#: each with the reason.
EXEMPT: dict[tuple[str, str], str] = {}


def _base(tree: Tree, info: ClassInfo, name: str) -> ClassInfo | None:
    """The class of the package a base of *info* names, if it is one."""
    resolved = tree.resolve(info.module, name)
    if resolved is not None and resolved in tree.classes:
        return tree.classes[resolved]
    local = tree.classes.get((info.module, name))
    if local is not None:
        return local
    candidates = tree.class_by_name.get(name, [])
    return candidates[0] if len(candidates) == 1 else None


def displays(tree: Tree, info: ClassInfo, seen: frozenset[str] = frozenset()) -> bool:
    """Whether a class inherits :data:`MECHANISM`, itself or through a base."""
    if MECHANISM in info.bases:
        return True
    for name in info.bases:
        base = _base(tree, info, name)
        key = f"{base.module}.{base.name}" if base is not None else ""
        if base is not None and key not in seen and displays(tree, base, seen | {key}):
            return True
    return False


def _calls(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name | ast.Attribute)
        and (item.func.id if isinstance(item.func, ast.Name) else item.func.attr)
        == name
        for item in ast.walk(node)
    )


def records_without_display(
    files: Sequence[pathlib.Path],
    root: pathlib.Path = SOURCE,
    *,
    tree: Tree | None = None,
) -> list[Finding]:
    """Every public record a notebook would show as its raw ``repr``.

    *tree* is the package already read from *files*, when the caller has it.
    """
    if tree is None:
        tree = Tree(files, root)
    found: list[Finding] = []
    for key in sorted(tree.public):
        info = tree.classes[key]
        if not info.record:
            continue
        module, qualname = key
        own = {
            method
            for method in NAMED_TUPLE_CALLS
            if (module, f"{qualname}.{method}") in tree.functions
        }
        reason: str | None = None
        if "NamedTuple" in info.bases:
            missing = [
                method
                for method, call in NAMED_TUPLE_CALLS.items()
                if method not in own
                or not _calls(
                    tree.functions[(module, f"{qualname}.{method}")].node, call
                )
            ]
            if missing:
                reason = (
                    f"{info.name} is a named tuple whose "
                    f"{' and '.join(missing)} {'is' if len(missing) == 1 else 'are'} "
                    "not the mechanism's"
                )
        elif not displays(tree, info):
            reason = f"{info.name} does not inherit {MECHANISM}"
        elif own:
            reason = f"{info.name} defines its own {' and '.join(sorted(own))}"
        if reason is not None:
            found.append(Finding(tree.paths[module], qualname, info.line, reason, ()))
    return found


def main(argv: Sequence[str] | None = None) -> int:
    """Report every public record without the shared notebook display."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package",
        nargs="?",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to read (default: src/phonometry)",
    )
    arguments = parser.parse_args(argv)
    root = arguments.package.resolve()
    files = python_files([], root)
    found, stale = exempted(records_without_display(files, root), EXEMPT)
    if not (found or stale):
        print("Every public record shows itself as a table in a notebook.")
        return 0
    if found:
        print(
            "::error::a public record would show in a notebook as its raw repr, "
            "arrays printed as numpy prints them"
        )
        for finding in found:
            print(f"  {finding.path}:{finding.line}: {finding.sink}")
        print(
            "  -> inherit RichDisplay from phonometry._internal.display (a record "
            "that can hold an array inherits OwnsArrays, which extends it), and "
            "leave _repr_html_ and _repr_pretty_ to it; a named tuple defines "
            "the two as calls to record_html and record_pretty. A record that "
            "has to display itself otherwise goes in EXEMPT at the top of "
            "scripts/check_record_display.py with its reason."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which needs no exemption any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
