#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a reference value in ``src`` that neither points at ISO 1683 nor says
where it was read.

Every level this library returns is a ratio to a reference value, and ISO
1683:2015 fixes one per quantity. The package publishes them once, as
``phonometry.metrology.ISO1683_REFERENCE_VALUES``, and before that table
existed the same 20 µPa had been typed out seventeen times, the same 1 pW
seven times, and one name, ``_P0``, meant a pressure in four modules and a power
in two. A copy is harmless until one of them is typed wrong, and nothing then says
which one is right. Some modules do count their decibels from another value,
and correctly: DIN 45672-2 refers railway vibration to the 5·10⁻⁸ m/s of the
1983 edition, ISO 532-1 prints its own squared pressure. What makes those
right is that the document they come from is named beside them.

So a reference value declared in ``src`` passes in one of two ways. Equal to a
value of the table, it has to be read from the table rather than typed again.
Different from it, it has to name the document it comes from, in the comment
above it or on its own line. The 50 nm/s of note b of Table 3 counts as a
different value here: it is the alternative the note allows, and a module
that uses it says which standard sent it there.

What counts as a reference value is decided by the name, because the value
alone cannot tell a reference from a tolerance: ``1e-12`` is the reference
sound power and also the floor under half the logarithms in the tree. A name
declares one when it carries a reference marker (``ref``, ``reference``, or a
symbol with a zero such as ``p0``) together with a quantity ISO 1683 lists,
spelled out (``pressure``, ``power``, ``velocity`` ...) or as its symbol
(``p``, ``w``, ``i``, ``e``). A name ending in ``db``, or one naming a
``level`` with no unit after it, holds a level and not a reference, and is
left alone. The places a name binds a number are an assignment at any scope, a
parameter default and a keyword argument. The one bare literal that is never
anything but a reference is also caught wherever it stands: ``2e-05``, the
20 µPa of air, and its square. :data:`EXEMPT_LITERALS` lists the places it is
something else, each with the reason.

The table's own values are read from the AST of the module that holds it, so
this runs without importing the package.

Usage::

    python scripts/check_reference_values.py [--root SRC_PACKAGE_DIR]

Exit status 0 when every reference value points at the table or names its
document, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import io
import math
import operator
import pathlib
import re
import sys
import tokenize
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "phonometry"

#: The module that holds the table, relative to the package. It is the one
#: place the literals are allowed, because it is where they are read.
TABLE_MODULE = pathlib.PurePosixPath("metrology/reference_values.py")

#: What a caller is told to use instead of a copy.
TABLE_NAME = "ISO1683_REFERENCE_VALUES"

#: The quantities the guard holds to the table, as the last word of the
#: table's own ``quantity`` field. ``distance`` is in Table 2 and is not here:
#: every standard that measures from a reference distance or area defines its
#: own, and a 1 m that agrees with the table is a coincidence of the document,
#: not a copy of it.
WORDS = frozenset(
    {
        "pressure",
        "exposure",
        "power",
        "energy",
        "intensity",
        "displacement",
        "velocity",
        "acceleration",
        "force",
    }
)

#: The symbols the tree writes these quantities with, and what each can mean.
#: ``p`` is read as a pressure or a power because both readings are in print:
#: ISO 9614 calls the sound power ``P``, and this tree once had a ``_P0`` that
#: was a pressure in three modules and a power in two. An exposure and an
#: energy share ``e`` the same way. A symbol is held to every value it could be
#: a copy of, so a copy is caught whichever meaning its author had in mind.
SYMBOLS: dict[str, frozenset[str]] = {
    "p": frozenset({"pressure", "power"}),
    "w": frozenset({"power"}),
    "i": frozenset({"intensity"}),
    "e": frozenset({"exposure", "energy"}),
}

#: The words that make a name a reference.
MARKERS = frozenset({"ref", "reference"})

#: A symbol with its reference marker glued on: ``p0``, ``wref``.
_GLUED = re.compile(r"^(?P<symbol>[pwie])(?:0|ref)$")

#: Last words that name a unit, so a name that says ``level`` and ends in one
#: holds the reference of that level in that unit, not a level.
UNIT_TAIL = frozenset(
    {"pa", "kpa", "mpa", "upa", "w", "j", "kj", "n", "m", "mm", "um", "s", "s2"}
)

#: A document named beside the value: a standard by its issuing body and
#: number, or a book or paper by its author and year. The body is followed by
#: a number within a few characters, so ``ECAC Doc 29``, ``ITU-R BS.1770`` and
#: ``DIN EN 21683`` all count, and a word that happens to be in capitals does
#: not.
DOCUMENT = re.compile(
    r"\b(?:ISO|IEC|EN|DIN|BS|NF|UNE|JIS|ANSI|ASA|ASTM|ECMA|VDI|SAE|ITU|EBU|AES"
    r"|IEEE|ECAC|ICAO|CEN|OIML|IMO|NORDTEST)\b[\s/A-Za-z.\-]{0,12}?\d"
    r"|\b[A-Z][a-z]+(?: et al\.| (?:and|&) [A-Z][a-z]+)?,? \(?(?:1[89]|20)\d\d\b"
)

#: Bare literals that are a reference wherever they stand, and what they are.
DISTINCTIVE: dict[float, str] = {
    2e-5: "20 µPa, the sound pressure of ISO 1683:2015 Table 1",
    4e-10: "(20 µPa)² s, the sound exposure of ISO 1683:2015 Table 1",
}

#: Places a distinctive literal is something else, keyed by module and the
#: function it is written in, each with the reason. A bare module would clear
#: every literal in it, including the next copy of the reference.
EXEMPT_LITERALS: dict[tuple[str, str], str] = {
    ("phonometry.fluids.water", "_pressure_mpa"): (
        "the 2e-5 per metre of depth in the gravity term of the Leroy and "
        "Parthiot standard-ocean pressure, not a sound pressure"
    ),
}


class Finding(NamedTuple):
    """One declaration that fails, with where it is and why."""

    path: pathlib.Path
    line: int
    name: str
    detail: str


class TableRow(NamedTuple):
    """One value of the table, as the guard reads it from the source."""

    key: str
    quantity: str
    value: float
    alternative: bool


def _literal(node: ast.expr, name: str) -> object:
    """The literal a keyword of a table row was written with."""
    try:
        return ast.literal_eval(node)
    except ValueError as error:  # pragma: no cover - the table is literal
        msg = f"{TABLE_MODULE}: the {name!r} of a row is not a literal"
        raise ValueError(msg) from error


def table_rows(source: pathlib.Path = SOURCE) -> list[TableRow]:
    """Every row of the table, read from the AST of the module holding it.

    :param source: The package directory, ``src/phonometry`` by default.
    :return: One entry per ``ReferenceValue(...)`` in the module, keyed
        ``"<medium>/<quantity key>"``.
    :raises ValueError: If the module holds no row, which would make every
        comparison vacuous.
    """
    tree = ast.parse((source / TABLE_MODULE).read_text(encoding="utf-8"))
    rows: list[TableRow] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values, strict=True):
            if not (
                isinstance(key, ast.Constant)
                and isinstance(value, ast.Call)
                and getattr(value.func, "id", "") == "ReferenceValue"
            ):
                continue
            fields = {kw.arg: _literal(kw.value, str(kw.arg)) for kw in value.keywords}
            number_field = fields["value"]
            if isinstance(number_field, bool) or not isinstance(
                number_field, int | float
            ):  # pragma: no cover - the table is literal
                msg = f"{TABLE_MODULE}: row {key.value!r} has no numeric value"
                raise ValueError(msg)
            rows.append(
                TableRow(
                    key=f"{fields['medium']}/{key.value!s}",
                    quantity=str(fields["quantity"]),
                    value=float(number_field),
                    alternative="note" in str(fields["table"]),
                )
            )
    if not rows:
        msg = f"{TABLE_MODULE} holds no ReferenceValue row"
        raise ValueError(msg)
    return rows


def quantities_of(name: str) -> frozenset[str]:
    """The ISO 1683 quantities *name* declares a reference of, if any.

    :param name: An identifier as it is written.
    :return: The quantities, empty when the name is not a reference of one.
    """
    tokens = [token for token in name.lower().split("_") if token]
    if not tokens or "db" in tokens:
        return frozenset()
    if {"level", "levels"} & set(tokens) and tokens[-1] not in UNIT_TAIL:
        return frozenset()
    glued = [_GLUED.match(token) for token in tokens]
    marked = bool(MARKERS & set(tokens)) or any(glued)
    if not marked:
        return frozenset()
    found = {token for token in tokens if token in WORDS}
    for token, match in zip(tokens, glued, strict=True):
        if match:
            found |= SYMBOLS[match["symbol"]]
        elif token in SYMBOLS:
            found |= SYMBOLS[token]
    return frozenset(found)


_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def number(node: ast.expr | None) -> float | None:
    """The value of *node* when it is a number written as literals.

    :param node: An expression, or ``None`` for a parameter with no default.
    :return: The number, or ``None`` when the expression reads anything else,
        which is what a value pointing at the table does.
    """
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        return float(value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        inner = number(node.operand)
        if inner is None:
            return None
        return -inner if isinstance(node.op, ast.USub) else inner
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = number(node.left), number(node.right)
        if left is None or right is None:
            return None
        try:
            return float(_OPERATORS[type(node.op)](left, right))
        except (ArithmeticError, ValueError):
            return None
    return None


def comments(text: str) -> dict[int, str]:
    """The comment on each line of *text* that has one, keyed by line number.

    Read with :mod:`tokenize`, so a ``#`` inside a string is not a comment.
    """
    found: dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            found[token.start[0]] = token.string.lstrip("#:").strip()
    return found


def citation_near(
    first: int, last: int, lines: list[str], notes: dict[int, str]
) -> str:
    """The comments that belong to lines *first* to *last* (1-based).

    That is the comment on each of those lines and the block of whole-line
    comments immediately above the first, which is where this tree documents
    a constant, with ``#:`` or with ``#``.
    """
    parts = [notes[line] for line in range(first, last + 1) if line in notes]
    cursor = first - 1
    above: list[str] = []
    while cursor >= 1 and lines[cursor - 1].lstrip().startswith("#"):
        above.append(notes.get(cursor, ""))
        cursor -= 1
    return " ".join([*reversed(above), *parts])


def _module_of(path: pathlib.Path, source: pathlib.Path) -> str:
    parts = list(path.relative_to(source.parent).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


class _Declaration(NamedTuple):
    name: str
    value_node: ast.expr
    first: int
    last: int


def _target_name(target: ast.expr) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def declarations(tree: ast.AST) -> Iterator[_Declaration]:
    """Every place a name is bound to an expression: the three the rule reads."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                name = _target_name(target)
                if name is not None:
                    yield _Declaration(
                        name, node.value, node.lineno, node.end_lineno or node.lineno
                    )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            args = node.args
            positional = [*args.posonlyargs, *args.args]
            defaulted = positional[len(positional) - len(args.defaults) :]
            pairs = [
                *zip(defaulted, args.defaults, strict=True),
                *zip(args.kwonlyargs, args.kw_defaults, strict=True),
            ]
            for arg, default in pairs:
                if default is not None:
                    yield _Declaration(
                        arg.arg,
                        default,
                        default.lineno,
                        default.end_lineno or default.lineno,
                    )
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg is not None:
                    yield _Declaration(
                        keyword.arg,
                        keyword.value,
                        keyword.value.lineno,
                        keyword.value.end_lineno or keyword.value.lineno,
                    )


def _enclosing_functions(tree: ast.AST) -> dict[int, str]:
    """The innermost function each line belongs to, for the literal hatch."""
    owner: dict[int, tuple[str, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for line in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                current = owner.get(line)
                if current is None or node.lineno >= current[1]:
                    owner[line] = (node.name, node.lineno)
    return {line: name for line, (name, _start) in owner.items()}


def _same(value: float, reference: float) -> bool:
    return math.isclose(value, reference, rel_tol=1e-12, abs_tol=0.0)


def check_file(
    path: pathlib.Path,
    rows: list[TableRow],
    source: pathlib.Path = SOURCE,
    exempt: dict[tuple[str, str], str] | None = None,
) -> tuple[list[Finding], set[tuple[str, str]]]:
    """The findings in one file, and the literal exemptions it used.

    :param path: A Python file under *source*.
    :param rows: The table, from :func:`table_rows`.
    :param source: The package directory the file belongs to.
    :param exempt: The literal hatch, :data:`EXEMPT_LITERALS` by default.
    :return: The findings, and the ``(module, function)`` keys of the hatch
        that cleared a literal here, so a stale entry can be reported.
    """
    exempt = EXEMPT_LITERALS if exempt is None else exempt
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()
    notes = comments(text)
    module = _module_of(path, source)
    primary: dict[str, list[TableRow]] = {}
    for row in rows:
        if not row.alternative:
            primary.setdefault(row.quantity.split()[-1], []).append(row)
    findings: list[Finding] = []
    judged: set[int] = set()
    for declaration in declarations(tree):
        quantities = quantities_of(declaration.name)
        value = number(declaration.value_node)
        if not quantities or value is None:
            continue
        judged.update(id(node) for node in ast.walk(declaration.value_node))
        same = [
            row
            for quantity in sorted(quantities)
            for row in primary.get(quantity, [])
            if _same(value, row.value)
        ]
        if same:
            keys = ", ".join(sorted({row.key for row in same}))
            findings.append(
                Finding(
                    path,
                    declaration.first,
                    declaration.name,
                    f"repeats the ISO 1683 value {value:g}; read it from "
                    f"{TABLE_NAME} ({keys}) instead of typing it again",
                )
            )
            continue
        cited = citation_near(declaration.first, declaration.last, lines, notes)
        if not DOCUMENT.search(cited):
            wanted = " or ".join(sorted(quantities))
            article = "an" if wanted[0] in "aeiou" else "a"
            findings.append(
                Finding(
                    path,
                    declaration.first,
                    declaration.name,
                    f"declares {article} {wanted} reference of {value:g} that is "
                    "not the ISO 1683 value and names no document it comes from",
                )
            )
    owners = _enclosing_functions(tree)
    used: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if id(node) in judged or not isinstance(node, ast.Constant):
            continue
        value = number(node)
        if value is None:
            continue
        what = next((w for ref, w in DISTINCTIVE.items() if _same(value, ref)), None)
        if what is None:
            continue
        key = (module, owners.get(node.lineno, ""))
        if key in exempt:
            used.add(key)
            continue
        findings.append(
            Finding(
                path,
                node.lineno,
                f"{value:g}",
                f"is {what}, written out; read it from {TABLE_NAME}",
            )
        )
    return findings, used


def check_tree(
    source: pathlib.Path = SOURCE,
    exempt: dict[tuple[str, str], str] | None = None,
) -> tuple[list[Finding], list[str]]:
    """Every finding under *source*, and the stale entries of the hatch.

    :param source: The package directory, ``src/phonometry`` by default.
    :param exempt: The literal hatch, :data:`EXEMPT_LITERALS` by default.
    :return: The findings in file order, and the hatch keys nothing used.
    """
    exempt = EXEMPT_LITERALS if exempt is None else exempt
    rows = table_rows(source)
    findings: list[Finding] = []
    used: set[tuple[str, str]] = set()
    for path in sorted(source.rglob("*.py")):
        if path.relative_to(source).as_posix() == str(TABLE_MODULE):
            continue
        found, cleared = check_file(path, rows, source, exempt)
        findings.extend(found)
        used |= cleared
    stale = sorted(f"{module}.{function}" for module, function in set(exempt) - used)
    return findings, stale


def main(argv: list[str] | None = None) -> int:
    """Report every reference value that is a copy or has no document."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=SOURCE,
        help="package directory to scan (default: src/phonometry)",
    )
    args = parser.parse_args(argv)
    source: pathlib.Path = args.root.resolve()
    findings, stale = check_tree(source)
    if not findings and not stale:
        rows = table_rows(source)
        print(
            f"Every reference value in {source.name} points at the {len(rows)} "
            "ISO 1683 values or names its document."
        )
        return 0
    if findings:
        print("::error::a reference value that is a copy, or has no document")
        for finding in findings:
            where = finding.path.relative_to(source.parent)
            print(f"  {where}:{finding.line}: {finding.name} {finding.detail}")
        print(
            f"  -> point it at phonometry.metrology.{TABLE_NAME}, or, if the "
            "value comes from another document, name that document in the "
            "comment above it."
        )
    for key in stale:
        print(f"::error::EXEMPT_LITERALS lists {key}, which no longer needs it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
