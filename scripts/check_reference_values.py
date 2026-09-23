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
and correctly: DIN 45672-2 defines its own 5·10⁻⁸ m/s for railway vibration,
ISO 532-1 prints its own squared pressure. What makes those right is that the
document they come from is named beside them.

So a reference value declared in ``src`` passes in one of two ways:

1. Equal to a value of the table, it has to be read from the table rather
   than typed again, whatever the comment beside it says.
2. Different from it, it has to name the document it comes from, in the
   comment above it or on its own line, and it has to be listed in
   :data:`DIFFERENT_REFERENCES` with the value it holds. ISO 1683 itself does
   not count as that document, because it is the table the value departs
   from, and a pointer that has been replaced by a mistyped number keeps the
   comment it had, citations and all. The list is what catches that: it pins
   each deliberate departure to the number its document prints, so any other
   number fails. The 50 nm/s of note b of Table 3 counts as a different value
   here: it is the alternative the note allows, and a module that uses it
   says which standard sent it there.

What counts as a reference value is decided by the name, because the value
alone cannot tell a reference from a tolerance: ``1e-12`` is the reference
sound power and also the floor under half the logarithms in the tree. A name
declares one when it carries a reference marker (``ref``, ``reference``, or a
symbol with a zero such as ``p0``) together with a quantity ISO 1683 lists,
spelled out (``pressure``, ``power``, ``velocity`` ...) or as its symbol
(``p``, ``w``, ``i``, ``e``). The symbols of the vibratory and particle
quantities (``v``, ``a``, ``F``, ``x``, ``ξ``, ``d``) are also the everyday
names of a volume, an area, a frequency or a coordinate, so a name built on
one of them is held to the first rule only: ``v0 = 1e-9`` is a copy of the
velocity reference, and ``A0 = 10.0`` is left alone. A name ending in ``db``,
or one naming a ``level`` with no unit after it, holds a level and not a
reference, and is left alone. The places a name binds a number are an
assignment at any scope (a tuple unpacked into names included), a parameter
default, a keyword argument and a string key of a dict literal, and a number
wrapped in ``float(...)`` or ``np.float64(...)`` is still a number.

Two kinds of bare literal are caught wherever they stand. ``2e-05``, the
20 µPa of air, and its square are never anything but a reference. And any
value of the table written into the arithmetic of a level is its reference:
the divisor inside a logarithm, ``log10(w / 1e-12)``, or the factor of an
antilogarithm, ``10 ** (L / 10) * 1e-12``. :data:`EXEMPT_LITERALS` lists the
places such a literal is something else, each with the reason.

What is not seen: a reference bound to a name that states no quantity (a bare
``reference=1e-6``) and used outside a logarithm or an antilogarithm, because
``1e-6``, ``1e-9`` and ``1e-12`` are also tolerances all over the tree.

The table's own values are read from the AST of the module that holds it, so
this runs without importing the package.

Usage::

    python scripts/check_reference_values.py [--root SRC_PACKAGE_DIR]

Exit status 0 when every reference value points at the table or is a listed
departure that names its document, 1 otherwise.
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
#: was a pressure in four modules and a power in two. An exposure and an
#: energy share ``e`` the same way. A symbol is held to every value it could be
#: a copy of, so a copy is caught whichever meaning its author had in mind.
SYMBOLS: dict[str, frozenset[str]] = {
    "p": frozenset({"pressure", "power"}),
    "w": frozenset({"power"}),
    "i": frozenset({"intensity"}),
    "e": frozenset({"exposure", "energy"}),
}

#: The symbols the standards print for the vibratory and particle references
#: (``v0``, ``a0``, ``F0``, ``ξ0``), which are also the everyday names of a
#: volume, an area or a coefficient, a frequency and a coordinate or a
#: distance. A name built on one of them is held only to the values of the
#: table: equal to one, it is a copy; anything else is not an ISO 1683
#: quantity at all, and is left alone.
WEAK_SYMBOLS: dict[str, frozenset[str]] = {
    "v": frozenset({"velocity"}),
    "a": frozenset({"acceleration"}),
    "f": frozenset({"force"}),
    "x": frozenset({"displacement"}),
    "xi": frozenset({"displacement"}),
    "d": frozenset({"displacement"}),
}

#: The words that make a name a reference.
MARKERS = frozenset({"ref", "reference"})

#: A symbol with its reference marker glued on: ``p0``, ``wref``, ``xi0``.
_GLUED = re.compile(r"^(?P<symbol>xi|[pwievafxd])(?:0|ref)$")

#: Last words that name a unit, so a name that says ``level`` and ends in one
#: holds the reference of that level in that unit, not a level.
UNIT_TAIL = frozenset(
    {"pa", "kpa", "mpa", "upa", "w", "j", "kj", "n", "m", "mm", "um", "s", "s2"}
)

#: A document named beside the value: a standard by its issuing body and a
#: number of at least two digits, or a book or paper by its author and year.
#: The body is followed by its number within a few characters, so ``ECAC Doc
#: 29``, ``ITU-R BS.1770`` and ``DIN EN 21683`` all count, and a word that
#: happens to be in capitals does not. A single author needs the year in
#: brackets or after a comma, ``Hopkins (2007)``, so that a sentence that
#: starts ``In 2019`` is not read as a citation; two authors or ``et al.``
#: may be followed by a bare year.
DOCUMENT = re.compile(
    r"\b(?:ISO|IEC|EN|DIN|BS|NF|UNE|JIS|ANSI|ASA|ASTM|ECMA|VDI|SAE|ITU|EBU|AES"
    r"|IEEE|ECAC|ICAO|CEN|OIML|IMO|NORDTEST)\b[\s/A-Za-z.\-]{0,12}?\d\d"
    r"|\b[A-Z][a-z]+(?: et al\.| (?:and|&) [A-Z][a-z]+),? \(?(?:1[89]|20)\d\d\b"
    r"|\b[A-Z][a-z]+(?:, | ?\()(?:1[89]|20)\d\d\b"
)

#: ISO 1683 in the edition the table transcribes, however it is written,
#: dated or not: the table itself, so never the *other* document a different
#: value comes from. An earlier edition (``ISO 1683:1983``, or ``DIN EN
#: 21683``, its German adoption) is another document and still counts.
TABLE_STANDARD = re.compile(
    r"(?:\b(?:UNE|DIN|BS|NF)[\s-]+)?(?:\bEN[\s-]+)?\bISO[\s-]*1683(?!\d)"
    r"(?!\s*:\s*(?:19\d\d|200\d))(?:\s*:\s*20\d\d)?"
)

#: Bare literals that are a reference wherever they stand, and what they are.
DISTINCTIVE: dict[float, str] = {
    2e-5: "20 µPa, the sound pressure of ISO 1683:2015 Table 1",
    4e-10: "(20 µPa)² s, the sound exposure of ISO 1683:2015 Table 1",
}

#: Places a literal the guard would read as a reference is something else,
#: keyed by module and the function it is written in, each with the reason. A
#: bare module would clear every literal in it, including the next copy of the
#: reference.
EXEMPT_LITERALS: dict[tuple[str, str], str] = {
    ("phonometry.fluids.water", "_pressure_mpa"): (
        "the 2e-5 per metre of depth in the gravity term of the Leroy and "
        "Parthiot standard-ocean pressure, not a sound pressure"
    ),
}

#: The reference values in ``src`` that are deliberately not the ISO 1683:2015
#: value, keyed by module and name, each with the number it holds and the
#: document that prints it. A different value that is not listed fails, and so
#: does a listed one that holds another number, which is what catches a
#: pointer replaced by a mistyped number whose comment still cites a document.
#: Several are references of something ISO 1683 does not cover (a static
#: pressure, an airflow velocity) whose name happens to say ``p0`` or
#: ``reference velocity``.
DIFFERENT_REFERENCES: dict[tuple[str, str], tuple[float, str]] = {
    ("phonometry.aircraft.airport_noise", "_P0_KPA"): (
        101.325,
        "ECAC Doc 29 Eq. 4-7, the mean-sea-level static pressure in kPa",
    ),
    ("phonometry.building.measurement.heavy_impact", "_FORCE_REFERENCE"): (
        1.0,
        "ISO 16283-2:2020 Formula (A.1), a force level re 1 N",
    ),
    (
        "phonometry.building.measurement.structure_borne_power",
        "FREE_VELOCITY_REFERENCE",
    ): (5e-8, "ISO 9611:1996 clause 7, the 50 nm/s of note b of Table 3"),
    ("phonometry.emission.vibration_sound_power", "REFERENCE_VELOCITY"): (
        5e-8,
        "ISO/TS 7849-1:2009 Equation 3, the 50 nm/s of note b of Table 3",
    ),
    (
        "phonometry.materials.absorbers.airflow_resistance",
        "_STATIC_REFERENCE_VELOCITY",
    ): (
        5e-4,
        "ISO 9053-1:2018 clause 7.5, an airflow velocity",
    ),
    ("phonometry.materials.absorbers.four_microphone", "_ASTM_P_REF"): (
        101.325,
        "ASTM E2611-19 Eq. (5), the atmospheric pressure in kPa",
    ),
    ("phonometry.materials.absorbers.impedance_tube", "_ISO_P_REF"): (
        101.325,
        "ISO 10534-2 Eq. (7), the atmospheric pressure in kPa",
    ),
    ("phonometry.noise_control.valves_hydrodynamic", "REFERENCE_INLET_PRESSURE_PA"): (
        6e5,
        "IEC 60534-8-4 Equation (3a), the inlet pressure of its figures",
    ),
    ("phonometry.psychoacoustics.loudness.contours", "_P0_SQUARED_PA2"): (
        4e-10,
        "ISO 226:2023 Formulae (1) and (2), the squared pressure as printed",
    ),
    ("phonometry.psychoacoustics.loudness.zwicker", "_I_REF"): (
        4e-10,
        "ISO 532-1:2017 Annex A, the constant I_REF",
    ),
    ("phonometry.vibration.immission.prediction", "_REFERENCE_ENERGY_KJ"): (
        1.0,
        "DIN 4150-1:2001-06 Formula (6), 1 kJ",
    ),
    ("phonometry.vibration.immission.railway", "VELOCITY_LEVEL_REFERENCE_MM_S"): (
        5e-5,
        "DIN 45672-2:1995-07 Formula (2), 5e-8 m/s written in mm/s",
    ),
}

#: The functions whose argument is the ratio a level is the logarithm of.
_LOGARITHMS = frozenset({"log10", "log", "log2", "lg"})

#: The calls that wrap a literal without changing it.
_WRAPPERS = frozenset({"float", "float64", "float32", "double", "asarray", "array"})


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


class FileResult(NamedTuple):
    """The findings in one file, and the entries of each list it used."""

    findings: list[Finding]
    exempt_used: set[tuple[str, str]]
    different_used: set[tuple[str, str]]


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


_EMPTY: frozenset[str] = frozenset()


def _claims(name: str) -> tuple[frozenset[str], frozenset[str]]:
    """The quantities *name* declares a reference of: named, and by weak symbol."""
    tokens = [token for token in name.lower().split("_") if token]
    if not tokens or "db" in tokens:
        return _EMPTY, _EMPTY
    if {"level", "levels"} & set(tokens) and tokens[-1] not in UNIT_TAIL:
        return _EMPTY, _EMPTY
    glued = [_GLUED.match(token) for token in tokens]
    if not (MARKERS & set(tokens) or any(glued)):
        return _EMPTY, _EMPTY
    named = {token for token in tokens if token in WORDS}
    weak: set[str] = set()
    for token, match in zip(tokens, glued, strict=True):
        symbol = match["symbol"] if match else token
        named |= SYMBOLS.get(symbol, _EMPTY)
        weak |= WEAK_SYMBOLS.get(symbol, _EMPTY)
    return frozenset(named), frozenset(weak - named)


def quantities_of(name: str) -> frozenset[str]:
    """The ISO 1683 quantities *name* declares a reference of, if any.

    Only the quantities the name states beyond doubt, by a word or by one of
    :data:`SYMBOLS`; the weak symbols are :func:`symbol_quantities_of`.

    :param name: An identifier as it is written.
    :return: The quantities, empty when the name is not a reference of one.
    """
    return _claims(name)[0]


def symbol_quantities_of(name: str) -> frozenset[str]:
    """The quantities *name* could be a reference of by one of the weak symbols.

    :param name: An identifier as it is written.
    :return: The quantities of :data:`WEAK_SYMBOLS` the name carries with a
        reference marker, empty when :func:`quantities_of` already reads it.
    """
    return _claims(name)[1]


_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _callee(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else ""


def number(node: ast.expr | None) -> float | None:
    """The value of *node* when it is a number written as literals.

    :param node: An expression, or ``None`` for a parameter with no default.
    :return: The number, or ``None`` when the expression reads anything else,
        which is what a value pointing at the table does. A literal wrapped
        in ``float(...)``, ``np.float64(...)`` or ``np.asarray(...)`` is still
        the literal.
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
    if (
        isinstance(node, ast.Call)
        and _callee(node) in _WRAPPERS
        and len(node.args) == 1
        and all(keyword.arg == "dtype" for keyword in node.keywords)
    ):
        return number(node.args[0])
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


def names_a_document(cited: str) -> bool:
    """Whether *cited* names a document other than ISO 1683:2015 itself."""
    return bool(DOCUMENT.search(TABLE_STANDARD.sub(" ", cited)))


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


def _bindings(
    target: ast.expr, value: ast.expr, first: int, last: int
) -> Iterator[_Declaration]:
    """The names *target* binds, each with the part of *value* it receives."""
    if isinstance(target, ast.Name):
        yield _Declaration(target.id, value, first, last)
    elif isinstance(target, ast.Attribute):
        yield _Declaration(target.attr, value, first, last)
    elif (
        isinstance(target, ast.Tuple | ast.List)
        and isinstance(value, ast.Tuple | ast.List)
        and len(target.elts) == len(value.elts)
    ):
        for inner_target, inner_value in zip(target.elts, value.elts, strict=True):
            yield from _bindings(inner_target, inner_value, first, last)


def _span(node: ast.expr) -> tuple[int, int]:
    return node.lineno, node.end_lineno or node.lineno


def declarations(tree: ast.AST) -> Iterator[_Declaration]:
    """Every place a name is bound to an expression."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            last = node.end_lineno or node.lineno
            for target in targets:
                yield from _bindings(target, node.value, node.lineno, last)
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
                    yield _Declaration(arg.arg, default, *_span(default))
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg is not None:
                    yield _Declaration(
                        keyword.arg, keyword.value, *_span(keyword.value)
                    )
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    yield _Declaration(key.value, value, *_span(value))


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


def level_values(rows: list[TableRow]) -> dict[float, str]:
    """The values a level can be counted from, each with the rows it is.

    Every value of the table but the distance of note c of Table 2, and the
    square of each, because a level of a squared quantity divides by the
    squared reference.
    """
    keys: dict[float, list[str]] = {}
    for row in rows:
        if row.quantity == "distance":
            continue
        for value, key in ((row.value, row.key), (row.value**2, f"({row.key})²")):
            same = next((known for known in keys if _same(value, known)), value)
            keys.setdefault(same, []).append(key)
    return {value: _some(found) for value, found in keys.items()}


def _some(keys: list[str]) -> str:
    """A few row keys for a message, the plain values before the squares."""
    ordered = sorted(keys, key=lambda key: (key.startswith("("), key))
    shown = ", ".join(ordered[:3])
    return shown if len(ordered) <= 3 else f"{shown} and {len(ordered) - 3} more"


def _is_antilog(node: ast.expr) -> bool:
    """``10 ** x`` or ``np.power(10, x)``: a level turned back into a ratio."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        base = number(node.left)
        return base is not None and _same(base, 10.0)
    if isinstance(node, ast.Call) and _callee(node) in {"power", "pow"} and node.args:
        base = number(node.args[0])
        return base is not None and _same(base, 10.0)
    return False


def _factors(node: ast.expr) -> list[ast.expr]:
    """The operands of a chain of products, ``a * b * c`` read as three."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return [*_factors(node.left), *_factors(node.right)]
    return [node]


def level_arithmetic(tree: ast.AST) -> Iterator[ast.expr]:
    """Every literal the arithmetic of a level uses as its reference.

    That is the divisor of a ratio inside a logarithm, ``log10(w / 1e-12)``,
    and a literal factor beside an antilogarithm, ``10 ** (L / 10) * 1e-12``.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee(node) in _LOGARITHMS:
            for argument in node.args:
                for inner in ast.walk(argument):
                    if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Div):
                        yield inner.right
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            factors = _factors(node)
            if any(_is_antilog(factor) for factor in factors):
                yield from (factor for factor in factors if not _is_antilog(factor))


def _judge_declaration(
    declaration: _Declaration,
    primary: dict[str, list[TableRow]],
    context: tuple[pathlib.Path, str, list[str], dict[int, str]],
    different: dict[tuple[str, str], tuple[float, str]],
    used: set[tuple[str, str]],
) -> Finding | None:
    """The finding of one declaration, or ``None`` when it passes."""
    path, module, lines, notes = context
    named, weak = _claims(declaration.name)
    value = number(declaration.value_node)
    if value is None or not (named or weak):
        return None
    same = [
        row
        for quantity in sorted(named | weak)
        for row in primary.get(quantity, [])
        if _same(value, row.value)
    ]
    where = (path, declaration.first, declaration.name)
    if same:
        keys = ", ".join(sorted({row.key for row in same}))
        return Finding(
            *where,
            f"repeats the ISO 1683 value {value:g}; read it from "
            f"{TABLE_NAME} ({keys}) instead of typing it again",
        )
    if not named:
        return None
    wanted = " or ".join(sorted(named))
    article = "an" if wanted[0] in "aeiou" else "a"
    what = (
        f"declares {article} {wanted} reference of {value:g}, not the ISO 1683 value,"
    )
    key = (module, declaration.name)
    if key in different:
        used.add(key)
    cited = citation_near(declaration.first, declaration.last, lines, notes)
    if not names_a_document(cited):
        return Finding(
            *where,
            f"{what} and names no document it comes from (ISO 1683 itself "
            "does not count: it is the table the value departs from)",
        )
    if key not in different:
        return Finding(
            *where,
            f"{what} and is not listed in DIFFERENT_REFERENCES; list it there "
            "with its value and its document, or read it from the table",
        )
    expected, document = different[key]
    if not _same(value, expected):
        return Finding(
            *where,
            f"holds {value:g} where DIFFERENT_REFERENCES records {expected:g} "
            f"({document})",
        )
    return None


def check_file(
    path: pathlib.Path,
    rows: list[TableRow],
    source: pathlib.Path = SOURCE,
    exempt: dict[tuple[str, str], str] | None = None,
    different: dict[tuple[str, str], tuple[float, str]] | None = None,
) -> FileResult:
    """The findings in one file, and the entries of each list it used.

    :param path: A Python file under *source*.
    :param rows: The table, from :func:`table_rows`.
    :param source: The package directory the file belongs to.
    :param exempt: The literal hatch, :data:`EXEMPT_LITERALS` by default.
    :param different: The deliberate departures from the table,
        :data:`DIFFERENT_REFERENCES` by default.
    :return: The findings, and the keys of the hatch and of the departures
        that something in this file used, so a stale entry can be reported.
    """
    exempt = EXEMPT_LITERALS if exempt is None else exempt
    different = DIFFERENT_REFERENCES if different is None else different
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    context = (path, _module_of(path, source), text.splitlines(), comments(text))
    primary: dict[str, list[TableRow]] = {}
    for row in rows:
        if not row.alternative:
            primary.setdefault(row.quantity.split()[-1], []).append(row)
    findings: list[Finding] = []
    judged: set[int] = set()
    different_used: set[tuple[str, str]] = set()
    for declaration in declarations(tree):
        finding = _judge_declaration(
            declaration, primary, context, different, different_used
        )
        if finding is not None:
            findings.append(finding)
        read = finding is not None or quantities_of(declaration.name)
        if read and number(declaration.value_node) is not None:
            judged.update(id(node) for node in ast.walk(declaration.value_node))
    owners = _enclosing_functions(tree)
    exempt_used: set[tuple[str, str]] = set()

    def literal(node: ast.expr, value: float, what: str) -> None:
        judged.update(id(inner) for inner in ast.walk(node))
        key = (context[1], owners.get(node.lineno, ""))
        if key in exempt:
            exempt_used.add(key)
            return
        findings.append(
            Finding(
                path,
                node.lineno,
                f"{value:g}",
                f"is {what}, written out; read it from {TABLE_NAME}",
            )
        )

    references = level_values(rows)
    for node in level_arithmetic(tree):
        value = number(node)
        if value is None or id(node) in judged:
            continue
        rows_of = next((k for ref, k in references.items() if _same(value, ref)), None)
        if rows_of is not None:
            literal(
                node,
                value,
                f"the ISO 1683 value of {rows_of}, as the reference of a level",
            )
    for candidate in ast.walk(tree):
        if id(candidate) in judged or not isinstance(
            candidate, ast.Constant | ast.BinOp | ast.UnaryOp
        ):
            continue
        value = number(candidate)
        if value is None:
            continue
        what = next((w for ref, w in DISTINCTIVE.items() if _same(value, ref)), None)
        if what is not None:
            literal(candidate, value, what)
    return FileResult(findings, exempt_used, different_used)


def check_tree(
    source: pathlib.Path = SOURCE,
    exempt: dict[tuple[str, str], str] | None = None,
    different: dict[tuple[str, str], tuple[float, str]] | None = None,
) -> tuple[list[Finding], list[str]]:
    """Every finding under *source*, and the stale entries of both lists.

    :param source: The package directory, ``src/phonometry`` by default.
    :param exempt: The literal hatch, :data:`EXEMPT_LITERALS` by default.
    :param different: The deliberate departures from the table,
        :data:`DIFFERENT_REFERENCES` by default.
    :return: The findings in file order, and each entry nothing used, as
        ``"<list>: <module>.<name>"``.
    """
    exempt = EXEMPT_LITERALS if exempt is None else exempt
    different = DIFFERENT_REFERENCES if different is None else different
    rows = table_rows(source)
    findings: list[Finding] = []
    exempt_used: set[tuple[str, str]] = set()
    different_used: set[tuple[str, str]] = set()
    for path in sorted(source.rglob("*.py")):
        if path.relative_to(source).as_posix() == str(TABLE_MODULE):
            continue
        result = check_file(path, rows, source, exempt, different)
        findings.extend(result.findings)
        exempt_used |= result.exempt_used
        different_used |= result.different_used
    stale = sorted(
        [f"EXEMPT_LITERALS: {m}.{f}" for m, f in set(exempt) - exempt_used]
        + [f"DIFFERENT_REFERENCES: {m}.{n}" for m, n in set(different) - different_used]
    )
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
            f"ISO 1683 values, or is one of the {len(DIFFERENT_REFERENCES)} "
            "listed departures and names its document."
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
            "comment above it and list it in DIFFERENT_REFERENCES."
        )
    for entry in stale:
        print(f"::error::{entry} is listed and nothing needs it any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
