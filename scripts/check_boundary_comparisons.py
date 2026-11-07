#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a verdict that compares a computed decimal with a printed limit unsettled.

A standard prints a limit in decimal, and the quantity judged against it is
computed: the difference of two readings, the mean of three, the ratio of two
areas. In binary a difference that is 6,0 dB in decimal comes out
5,999 999 999 999 996 as often as 6,000 000 000 000 004, so a verdict read
straight off ``margin >= 6.0`` turns on the last bit, and which bit depends on
the readings, on the order of a sum and on the machine. The tree settles such a
quantity first, through :mod:`phonometry._internal.boundary`, or compares it
with a named slack; the sweep that put that helper in found more than a hundred
sites that did neither, and nothing stopped the next one. This guard does.

What it refuses
---------------

An ordered comparison (``<``, ``<=``, ``>``, ``>=``, and the ``is_positive``
and ``is_at_most`` predicates of :mod:`phonometry._internal.validation`, which
are the same comparisons by name) where

* one side is a **computed decimal**: a caller's value went through float
  arithmetic (a sum, a difference, a product, a ratio, a mean, a spread, an
  interpolation, a percentile) on its way to the comparison, and nothing on
  that way settled it or rounded it to a fixed number of decimals; settling
  the limit instead (``margin >= settled(LIMIT)``) leaves a published limit;
* the other side is a **published limit**: a literal, an upper-case constant,
  an entry of an upper-case table or a field of one
  (``TABLE[key].tolerance_db``), or anything built from those alone;
* and neither side carries a **slack**: a name with ``SLACK`` in it, a name
  that ends in ``TOL`` or ``EPS``, or a constant whose magnitude is a
  micro-unit or less (a degenerate fit judged by a named threshold such as
  ``_NO_DECREASE_STI_PER_M``). A slack counts where it is added to a side or
  taken from it, or where it scales a side as a constant factor
  (``x * (1 + _REL_TOL)``, ``_GEOMETRY_TOLERANCE * scale``); an epsilon that
  only keeps a divisor off zero (``a / (b + _DIV_EPS)``) is no slack.

Against **zero** the rule is narrower, because one rounding operation on
exact operands has an exact sign: a difference of two floats is zero only when
they are equal. A comparison with zero is refused when the computed side is a
computed decimal less a published constant (``margin - LIMIT >= 0`` is
``margin >= LIMIT``), a least-squares fit (a fit through data that do not change returns a slope of
:math:`10^{-17}` with either sign), a sum or a mean of terms that can cancel
(a net power, a mean signed intensity), or the root of a difference whose
operands were themselves rounded (a discriminant). A sum of terms that cannot
be negative, magnitudes, squares, roots, is zero only when every term is, and
is not refused.

How it sees "computed"
----------------------

Each function is read flow-insensitively: a local name stands for the join of
everything assigned to it, an element stored into it or appended to it
included. A comprehension's variable stands for an item of what it walks
inside the comprehension only, as Python keeps it there. A parameter of a public function is the caller's value; a parameter
of a private function, a private method or a nested function stands for
whatever the file passes it at its call sites. A call into a function of the
same file, or of a sibling module it imports by a relative import, is read in
that function with its parameters bound to what the call passes, so a helper
that only converts its argument does not make every caller look computed. A
field of a dataclass of the file, read on ``self`` or on a local name that
builds it here (``result = Result(...)``), stands for what the file builds it
from, and a property for what it returns. Selections (``max``, ``min``,
indexing, ``float``, ``np.asarray``, ``np.where``) keep what they select;
transcendental functions (``log10``, ``exp``, powers that are not small whole
ones) end a decimal: a level in decibels of an energy sum cannot sit on a
printed decimal.

What it cannot see
------------------

* A limit that is itself computed or given by the caller: a threshold built
  from a reading (``lv > l70 + margin``), a requirement passed in, a count
  against a computed minimum. Only a published constant or zero is a limit
  here. Most of what the sweep fixed and this guard would not have refused is
  of this kind; widening the rule to it refuses many times more comparisons
  that cannot sit on anything.
* A value that reaches the comparison through a field of a class another
  module builds, of an instance a function returns rather than one built in
  place, through a container stored under another name, or through a method
  of an object another module returns.
* A call it does not know ends a decimal, and so does a root: a length
  computed from its components (``np.hypot``, ``np.sqrt``) is not judged
  against a printed length, and a root only against zero.
* A factor of a micro-unit or less reads as a relative slack, so a change of
  unit by one (``pressure_pa * 1e-6`` against a limit in megapascals) hides
  the product; and the side a slack moves the edge to is not checked.
* A product with a transcendental factor is still a decimal to the scan (a
  weighted mean has transcendental weights and is still a mean of readings),
  so a few such quantities are refused and exempted below.
* Rounding at a half (``floor(x + 0.5)``, ``np.rint``) and a table lookup by a
  computed key (``searchsorted``, ``ceil``): the same class, not a comparison.
* Anything under ``_plot`` and ``_report``, where a comparison places a label
  and decides no verdict.

Whether a computed quantity can equal a printed limit in decimal, and whether
the outcome changes there, depends on the formula, so no static rule is exact.
The comparisons of the refused shape that cannot sit on their limit, or whose
outcome does not change there, are listed in
``scripts/boundary_comparison_exemptions.tsv``, each with its reason. An
exemption names a file, a function and the comparison as written, and excuses
one comparison: a function that writes the same comparison twice lists it
twice, so a third copy is refused rather than covered by the lines written for
the first two, and a line left over once a copy is gone fails the guard, so the
list cannot outlive what it excuses. A chained comparison (``low <= x < high``)
is one comparison. The key carries the comparison and the count, which is why
the split is this guard's own and not :func:`ast_scan.exempted`, whose keys
name a function alone.

Usage::

    python scripts/check_boundary_comparisons.py           # the guard
    python scripts/check_boundary_comparisons.py --list    # every comparison of the shape

Exit status 0 when every comparison of the shape is exempted with a reason, 1
otherwise, naming the file, the line and the comparison.
"""

from __future__ import annotations

import argparse
import ast
import collections
import dataclasses
import functools
import itertools
import pathlib
import re
import sys
from typing import TYPE_CHECKING, TypeGuard

from ast_scan import (
    argument_places,
    assigned_value,
    assignment_target,
    binding_of,
    bindings_by_name,
    empty_type_checking_bodies,
    for_the_type_checker,
    global_bindings,
    live_bindings,
    own_names,
    scope_nodes,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "phonometry"
#: The comparisons of the refused shape kept on purpose, with their reasons.
EXEMPTIONS = (
    pathlib.Path(__file__).resolve().with_name("boundary_comparison_exemptions.tsv")
)

#: Packages whose comparisons place a figure's labels or a fiche's layout and
#: decide no verdict.
PRESENTATION = ("_plot", "_report")
#: The helper the class is settled through; its own comparisons are the fix.
SETTLING_MODULE = "_internal/boundary.py"

#: Calls whose result is a settled quantity: the helpers of
#: :mod:`phonometry._internal.boundary`.
SETTLING = frozenset(
    {
        "settled",
        "settled_ratio",
        "settled_net_share",
        "round_half_up",
        "round_half_even",
        "round_half_away_from_zero",
    }
)
#: The predicates of :mod:`phonometry._internal.validation` that are ordered
#: comparisons by name: ``is_positive(x)`` is ``x > 0`` and ``is_at_most(x, y)``
#: is ``x <= y``.
PREDICATES = frozenset({"is_positive", "is_at_most"})

#: Calls that hand back what they are given, converted or selected, without
#: arithmetic: a maximum of two readings is one of the readings.
SELECTING = frozenset(
    {
        "float",
        "float64",
        "asarray",
        "asanyarray",
        "array",
        "atleast_1d",
        "atleast_2d",
        "atleast_3d",
        "ravel",
        "flatten",
        "copy",
        "astype",
        "squeeze",
        "reshape",
        "broadcast_to",
        "abs",
        "fabs",
        "absolute",
        "real",
        "max",
        "min",
        "amax",
        "amin",
        "nanmax",
        "nanmin",
        "maximum",
        "minimum",
        "fmax",
        "fmin",
        "sort",
        "sorted",
        "clip",
        "list",
        "tuple",
        "take",
        "take_along_axis",
        "compress",
        "extract",
        "concatenate",
        "stack",
        "hstack",
        "vstack",
        "column_stack",
        "append",
        "where",
        "select",
        "flip",
        "roll",
        "transpose",
        "expand_dims",
        "full_like",
        "nan_to_num",
        "read_only",
        "tolist",
        "item",
        "values",
    }
)
#: The selecting calls that select from every argument, not the first.
_SELECTING_ALL = frozenset(
    {"max", "min", "maximum", "minimum", "fmax", "fmin", "clip", "append"}
)
#: Selections that return a magnitude, never negative.
_MAGNITUDES = frozenset({"abs", "fabs", "absolute"})
#: Spreads about a mean: never negative, and not zero for identical readings.
_SPREADS = frozenset({"std", "nanstd", "var", "nanvar"})
#: Methods that put a value into the container they are called on.
_GROWING = frozenset({"append", "extend", "insert", "add", "appendleft"})
#: Roots: zero exactly when their argument is.
ROOTS = frozenset({"sqrt", "cbrt"})
#: Calls that compute on what they are given with the four operations: a mean
#: of decimal readings is decimal and its binary value can sit either side.
ARITHMETIC = frozenset(
    {
        "sum",
        "fsum",
        "nansum",
        "mean",
        "nanmean",
        "average",
        "median",
        "nanmedian",
        "percentile",
        "nanpercentile",
        "quantile",
        "nanquantile",
        "std",
        "nanstd",
        "var",
        "nanvar",
        "ptp",
        "diff",
        "cumsum",
        "dot",
        "inner",
        "vdot",
        "matmul",
        "prod",
        "trapezoid",
        "trapz",
        "interp",
        "fmean",
        "outer",
        "subtract",
        "add",
        "multiply",
        "divide",
        "true_divide",
        "negative",
        "square",
    }
)
#: The calls of :data:`ARITHMETIC` that multiply or divide, and so keep the
#: exactness of their operands' signs.
_MULTIPLYING = frozenset(
    {"multiply", "divide", "true_divide", "square", "prod", "outer", "negative"}
)
#: The calls of :data:`ARITHMETIC` that add up any number of terms.
_SUMMING = frozenset(
    {
        "sum",
        "fsum",
        "nansum",
        "mean",
        "nanmean",
        "average",
        "median",
        "nanmedian",
        "percentile",
        "nanpercentile",
        "quantile",
        "nanquantile",
        "std",
        "nanstd",
        "var",
        "nanvar",
        "cumsum",
        "dot",
        "inner",
        "vdot",
        "matmul",
        "trapezoid",
        "trapz",
        "interp",
        "fmean",
    }
)
#: Least-squares fits: a fit through data that do not change returns a slope
#: a few units in the last place either side of zero.
FITTING = frozenset({"polyfit", "lstsq", "linregress", "curve_fit", "fit"})
#: Calls whose result is a whole number, a count or an index.
COUNTING = frozenset(
    {
        "len",
        "int",
        "count_nonzero",
        "argmax",
        "argmin",
        "argsort",
        "searchsorted",
        "flatnonzero",
        "nonzero",
        "floor",
        "ceil",
        "rint",
        "trunc",
        "bit_length",
        "index",
        "count",
        "digitize",
        "bincount",
        "isqrt",
        "ord",
        "hash",
        "range",
    }
)
#: Calls whose result is a truth value.
TESTING = frozenset(
    {
        "bool",
        "all",
        "any",
        "isfinite",
        "isnan",
        "isinf",
        "isclose",
        "allclose",
        "array_equal",
        "isinstance",
        "issubclass",
        "callable",
        "hasattr",
        "startswith",
        "endswith",
        "logical_and",
        "logical_or",
        "logical_not",
        "is_positive",
        "is_at_most",
        "signbit",
    }
)
#: The decorators that make a method read as an attribute.
PROPERTY_DECORATORS = frozenset({"property", "cached_property"})
#: A constant whose name says it is a slack, or a tolerance of the arithmetic
#: rather than of the standard.
SLACK_NAME = re.compile(r"SLACK|(?:^|_)[AR]?TOL$|EPS(?:ILON)?$")
#: Below this magnitude a constant is a slack or a degenerate-data threshold,
#: never a printed limit: the settled grain is a nano-unit, and no standard
#: prints a micro-unit limit in the units this library uses.
SLACK_MAGNITUDE = 1e-6
#: The largest whole power read as arithmetic: a square or a cube of decimals
#: is still a decimal; a larger or a fractional power is not.
_LARGEST_POWER = 3
#: Module names whose attributes are functions or constants, never data.
_NAMESPACES = frozenset({"np", "numpy", "math", "scipy", "cmath"})
#: Attributes that are counts or shapes.
_WHOLE_ATTRIBUTES = frozenset(
    {"size", "ndim", "shape", "nbytes", "year", "month", "day"}
)


@dataclasses.dataclass(frozen=True)
class Value:
    """What the scan knows about an expression, joined over the paths to it.

    :param const: Built from literals and published constants alone.
    :param number: The resolved value of a constant, when it is one number.
    :param whole: A count, an index or another whole number.
    :param decimal: A caller's value reaches it through selection or the four
        operations, so it can sit on a printed decimal.
    :param depth: Rounding operations on the way, capped at two.
    :param cancels: Its sign is not exact: it is a sum or a difference with an
        operand that was itself rounded, or a sum of many terms, so terms that
        cancel in decimal leave a few units in the last place of either sign.
        One rounding operation on exact operands has an exact sign (a
        difference is zero only when the two are equal), and so does a product
        or a ratio of values whose signs are exact.
    :param summed: A reduction over an array (a sum, a mean) is on the way.
    :param offset: A computed decimal less or plus a published constant: set
        against zero, it is that decimal set against the constant, the form a
        margin over a printed limit takes.
    :param nonnegative: Never below zero by construction (a magnitude, a
        square, a root, a sum of those), so a sum of such terms is zero only
        when every term is, and its sign is exact.
    :param fit: The result of a least-squares fit.
    :param settled: Rounded to fixed decimals on every path.
    :param slack: Carries a slack on every path.
    :param root: Went through a root: zero exactly when what was under it is,
        but no longer a decimal that can sit on a printed limit.
    """

    const: bool = False
    number: float | None = None
    whole: bool = False
    decimal: bool = False
    depth: int = 0
    cancels: bool = False
    summed: bool = False
    offset: bool = False
    nonnegative: bool = False
    fit: bool = False
    settled: bool = False
    slack: bool = False
    root: bool = False

    @property
    def computed(self) -> bool:
        """A caller's decimal that went through arithmetic and was not settled."""
        return self.decimal and self.depth > 0 and not (self.settled or self.whole)


OPAQUE = Value()
CALLER = Value(decimal=True)
WHOLE = Value(whole=True)
SETTLED = Value(settled=True)


def constant(number: float | None) -> Value:
    """A literal or a published constant, with its value when known."""
    slack = number is not None and 0.0 < abs(number) <= SLACK_MAGNITUDE
    return Value(
        const=True,
        number=number,
        whole=number is not None and float(number).is_integer(),
        slack=slack,
    )


def join(values: Iterable[Value]) -> Value:
    """What a name assigned on several paths can be: the union of the risks.

    A path that is not settled makes the name not settled, a path that brings
    a caller's decimal makes it decimal, and so on; a name is a constant only
    when every path is the same constant.
    """
    items = list(values)
    if not items:
        return OPAQUE
    numbers = {item.number for item in items}
    return Value(
        const=all(item.const for item in items),
        number=numbers.pop() if len(numbers) == 1 else None,
        whole=all(item.whole for item in items),
        decimal=any(item.decimal for item in items),
        depth=max(item.depth for item in items),
        cancels=any(item.cancels for item in items),
        summed=any(item.summed for item in items),
        offset=any(item.offset for item in items),
        nonnegative=all(item.nonnegative for item in items),
        fit=any(item.fit for item in items),
        settled=all(item.settled for item in items),
        slack=all(item.slack for item in items),
        root=any(item.root for item in items),
    )


def carried_slack(items: list[Value], *, additive: bool) -> bool:
    """Whether arithmetic on ``items``, not all constants, still carries a slack.

    Added to the quantity or taken from it, a slack moves it by its own size,
    and it still does once the sum is scaled by constants. In a product or a
    ratio with another computed value it does only as a constant factor, a
    relative slack such as ``1 + _REL_TOL`` or ``_GEOMETRY_TOLERANCE * scale``:
    an epsilon that keeps a divisor off zero, ``a / (b + _DIV_EPS)``, moves the
    ratio by an amount the caller's ``b`` decides, which is nothing at all once
    ``b`` is large.
    """
    carriers = [item for item in items if item.slack]
    if not carriers:
        return False
    return (
        additive
        or any(item.const for item in carriers)
        or all(item.const for item in items if not item.slack)
    )


def combine(
    values: Iterable[Value],
    *,
    additive: bool,
    many: bool = False,
    subtracts: bool = False,
) -> Value:
    """The result of arithmetic on ``values``: one more rounding operation deep.

    Arithmetic on whole numbers stays whole (a ratio of two counts is
    correctly rounded, so it equals the literal of the same decimal), on
    constants stays constant, and on anything else is a computed decimal as
    soon as one operand brings a caller's value or a settled one, which is a
    decimal again once something is added to it.

    :param values: The operands.
    :param additive: A sum or a difference, whose sign is exact only when its
        operands are exact; a product or a ratio keeps its operands' signs.
    :param many: A reduction over an array, a sum of any number of terms.
    :param subtracts: A difference: its result can be negative whatever its
        operands are.
    """
    items = list(values)
    if all(item.const for item in items):
        slack = any(item.slack for item in items)
        return Value(const=True, whole=all(item.whole for item in items), slack=slack)
    if all(item.whole for item in items):
        return WHOLE
    slack = carried_slack(items, additive=additive)
    carried = [item for item in items if item.decimal or item.settled]
    if not carried:
        return Value(slack=slack)
    depth = max(item.depth for item in carried) + 1
    nonnegative = not subtracts and all(
        item.nonnegative
        or (item.const and item.number is not None and item.number >= 0.0)
        for item in items
    )
    offset = False
    if additive:
        cancels = not nonnegative and (
            many or any(item.depth or item.cancels for item in carried)
        )
        # Only the difference itself: ``margin - LIMIT``. A formula that adds a
        # constant to a computed term, ``331.4 + 0.6 t``, is not a margin.
        offset = (
            subtracts
            and not many
            and any(item.computed for item in carried)
            and any(
                item.const and not item.slack and item.number != 0.0 for item in items
            )
        )
    else:
        cancels = any(item.cancels for item in carried)
    return Value(
        decimal=True,
        depth=min(depth, 2),
        cancels=cancels,
        nonnegative=nonnegative,
        summed=many or any(item.summed for item in carried),
        offset=offset,
        fit=any(item.fit for item in items),
        slack=slack,
        root=any(item.root for item in carried),
    )


def call_name(node: ast.Call) -> str:
    """The last component of what a call calls: ``np.mean`` is ``mean``."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def is_constant_name(name: str) -> bool:
    """An upper-case name, optionally private: a published constant."""
    stripped = name.lstrip("_")
    return (
        bool(stripped)
        and stripped.upper() == stripped
        and any(c.isalpha() for c in stripped)
    )


def literal_number(node: ast.expr) -> float | None:
    """The number a literal expression spells, or ``None``."""
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    ):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        inner = literal_number(node.operand)
        if inner is None:
            return None
        return -inner if isinstance(node.op, ast.USub) else inner
    return None


@dataclasses.dataclass(frozen=True)
class Finding:
    """One comparison the guard refuses."""

    path: str
    line: int
    scope: str
    text: str
    reason: str

    @property
    def key(self) -> tuple[str, str, str]:
        """How an exemption names it: file, enclosing function, comparison."""
        return (self.path, self.scope, self.text)


Function = ast.FunctionDef | ast.AsyncFunctionDef
#: Parameters bound to the values one call passes, sorted by name; ``None``
#: when a function is read on its own, for every call at once.
Bindings = tuple[tuple[str, Value], ...] | None


@dataclasses.dataclass(frozen=True)
class Context:
    """Where an expression is evaluated: a function, and how it was called.

    A helper that only converts its argument (``_check_finite(x)``) is called
    with a reading at one site and a difference at another; read once for all
    its callers it would make every one of them look computed. So a call into
    this file's own functions is read with the parameters bound to what that
    call passes, and only a function read on its own (the one a comparison
    sits in) joins what all its call sites pass.
    """

    function: Function | None
    bindings: Bindings = None


class Module:
    """One source file, indexed for the scan.

    The index is what the evaluation needs to follow a value across the file:
    the parent of every node, the bindings of every function, the call sites of
    each function, the places each class is built, and the module-level names
    with what they are assigned.
    """

    def __init__(
        self,
        path: pathlib.Path,
        relative: str,
        package: Package | None = None,
        source: str | None = None,
    ) -> None:
        self.path = path
        self.relative = relative
        self.package = package
        self.source = path.read_text(encoding="utf-8") if source is None else source
        self.tree = empty_type_checking_bodies(ast.parse(self.source))
        self.parent: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                self.parent[child] = node
        self.module_names: dict[str, list[ast.expr]] = {}
        for node in self.tree.body:
            for target, value in _assignments(node):
                self.module_names.setdefault(target, []).append(value)
        self.imports = _imported_names(self.tree, path)
        #: The relative imports the module makes at its top, by the name each
        #: binds, in the order of the source: an import inside a function
        #: binds the name for that function alone.
        self.top_imports = _imports_by_name(scope_nodes(self.tree))
        # A function written inside an ``if``, a ``try`` or a ``with`` at the
        # top of the module is the module's own as well, and one written in
        # each branch is either at run time; one a later one replaces is not,
        # whether the later one is a ``def`` or an import of the name.
        self.top_functions, self.top_live_imports = _top_bindings(
            self.tree, self.top_imports
        )
        #: Every ``def`` at the top of the module, by name, which a function
        #: reads from its own ``def`` on (:meth:`top_at`), and every other
        #: binding of a name there that is no alias: an import, and what
        #: stands for no function (:func:`_top_names`).
        self.top_defined, self.top_others = _top_names(self.tree)
        #: The names an assignment of another name alone binds (``_spread =
        #: _range``), at the top of the module and under ``global`` in a
        #: function, by the name each binds (:meth:`_aliased`).
        self.top_aliases: dict[str, list[ast.Name | ast.NamedExpr]] = {}
        for node in scope_nodes(self.tree):
            if _aliases_a_name(node, self.tree) and (stored := assignment_target(node)):
                self.top_aliases.setdefault(stored.id, []).append(node)
        for targets in self.top_aliases.values():
            targets.sort(key=lambda target: (target.lineno, target.col_offset))
        self.global_aliases = {
            name: found
            for name, nodes in global_bindings(self.tree).items()
            if (found := [node for node in nodes if _aliases_a_name(node, self.tree)])
        }
        self._aliasing: set[int] = set()
        self.locals: dict[Function, dict[str, list[tuple[str, ast.AST, int]]]] = {}
        self.comprehended: dict[
            Function, dict[int, list[tuple[str, ast.AST, int]]]
        ] = {}
        self.calls: dict[Function, list[tuple[ast.Call, Function | None]]] = {}
        self.constructions: dict[
            ast.ClassDef, list[tuple[ast.Call, Function | None]]
        ] = {}
        self._written: (
            dict[str, list[tuple[tuple[str, ast.AST, int], Function]]] | None
        ) = None
        self._index_calls()
        self._memo: dict[object, Value] = {}
        self._classes: dict[object, ast.ClassDef | None] = {}
        self._busy: set[object] = set()
        self._provisional: dict[object, Value] = {}
        self._cut = False
        for name in {*self.top_aliases, *self.global_aliases}:
            functions = self.top_at(name, None)[0]
            if functions:
                self.top_functions[name] = functions
            else:
                self.top_functions.pop(name, None)

    # -- structure -----------------------------------------------------

    def enclosing(self, node: ast.AST) -> Function | None:
        """The innermost function a node sits in."""
        current = self.parent.get(node)
        while current is not None:
            if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
                return current
            current = self.parent.get(current)
        return None

    def holder(self, node: ast.AST) -> ast.AST | None:
        """The function or class a node is written in, through the ``if``, the
        ``try`` and the ``with`` around it, which open no scope of their own.
        """
        current = self.parent.get(node)
        while current is not None and not isinstance(
            current, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            current = self.parent.get(current)
        return current

    def owner_class(self, function: Function | None) -> ast.ClassDef | None:
        """The class whose method a function is, or is nested in."""
        current: ast.AST | None = function
        while current is not None:
            current = self.holder(current)
            if isinstance(current, ast.ClassDef):
                return current
        return None

    def is_method(self, function: Function) -> bool:
        """Whether *function* is written in a class body: an ``if`` in it too."""
        return isinstance(self.holder(function), ast.ClassDef)

    def qualname(self, node: ast.AST) -> str:
        """``Class.method.inner`` for the function a node sits in."""
        parts: list[str] = []
        current = self.parent.get(node)
        while current is not None:
            if isinstance(
                current, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                parts.append(current.name)
            current = self.parent.get(current)
        return ".".join(reversed(parts)) or "<module>"

    def resolve_functions(
        self, call: ast.Call, scope: Function | None
    ) -> tuple[Function, ...]:
        """The functions of this file a call can reach, none when it reaches none.

        A bare name is looked up as Python looks it up (:meth:`lookup`): among
        the functions the calling function and those around it define
        (inside an ``if``, a ``try`` or a ``with`` too), as far as the
        nearest of them that binds the name otherwise, by a parameter, an
        import or an assignment, which reaches no function of the module;
        then at the top of the module. A name defined in each branch of an
        ``if`` reaches every definition of it, as a method a class defines
        that way does.
        """
        func = call.func
        if isinstance(func, ast.Name):
            return self.lookup(func.id, scope, call) or ()
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in {"self", "cls"}
        ):
            owner = self.owner_class(scope)
            if owner is not None:
                return _methods(owner, func.attr)
        return ()

    def _index_calls(self) -> None:
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            scope = self.enclosing(node)
            for target in self.resolve_functions(node, scope):
                self.calls.setdefault(target, []).append((node, scope))
            name = node.func.id if isinstance(node.func, ast.Name) else None
            built = (
                self.owner_class(scope)
                if name == "cls"
                else self.class_named(name, scope, node)
                if name is not None
                else None
            )
            if built is not None:
                self.constructions.setdefault(built, []).append((node, scope))

    def class_named(
        self, name: str, scope: Function | None, node: ast.AST
    ) -> ast.ClassDef | None:
        """The class of this file *name*, read at *node* in *scope*, stands for.

        Looked up as Python looks it up, from *scope* outwards to the module:
        the nearest scope that binds the name says what it is, and it stands
        for a class only when every way it binds it there is a ``class``
        statement and one of them is the name's at *node*: from a function
        inside that scope, one that may stand from the ``def`` on
        (:func:`ast_scan.live_bindings`). ``None`` otherwise: a name bound
        to a class in each branch of an ``if`` stands for no one class.
        """
        current = scope
        while current is not None:
            names = own_names(current)
            if names.rebinds(name):
                return None
            if name in names.declared_global:
                break
            if names.binds(name):
                return self._class_in(current, name, node)
            current = self.enclosing(current)
        return self._class_in(self.tree, name, node)

    def _class_in(
        self, holder: ast.AST, name: str, node: ast.AST | None
    ) -> ast.ClassDef | None:
        """The ``class`` statement of *name* that *holder* binds it to at
        *node*, or once it has run when *node* is None, when it binds the
        name by ``class`` statements alone and one of them is the name's.
        """
        if own_names(holder).how(name) != "definition":
            return None
        classes = [
            statement
            for statement in scope_nodes(holder)
            if isinstance(statement, ast.ClassDef) and statement.name == name
        ]
        live = live_bindings(holder, classes, node) if classes else []
        return live[0] if len(live) == 1 else None

    def lookup(
        self, name: str, scope: Function | None, node: ast.AST | None = None
    ) -> tuple[Function, ...] | None:
        """The functions of this file *name* stands for at *node*, in *scope*.

        Read as Python reads it (:func:`ast_scan.own_names`), from the
        calling function outwards: a comprehension, a lambda or a class body
        around *node* inside *scope* that binds the name hides every
        function; then the nearest function that binds it says what it is,
        the functions of that name it defines, none for an import (which the
        package follows), and ``None`` for a parameter or an assignment, or
        a definition and another binding both, which may stand for either. A
        function that declares the name ``global`` sends it to the top of
        the module, whose functions of that name come last. ``None`` means a
        binding hides the name, so that no import of the module stands for
        it either.
        """
        if scope is not None and node is not None:
            how, binder = binding_of(scope, node, name)
            if how == "global":
                return self.top_at(name, node)[0]
            if binder is not None and binder is not scope:
                return None
        current = scope
        while current is not None:
            names = own_names(current)
            if names.rebinds(name):
                return None
            if name in names.declared_global:
                break
            if names.binds(name):
                return self._bound_as(current, name, node)
            current = self.enclosing(current)
        return self.top_at(name, node)[0]

    def _bound_as(
        self, function: Function, name: str, node: ast.AST | None
    ) -> tuple[Function, ...] | None:
        """The functions *name* stands for in *function*, which binds it itself.

        The functions of that name it defines (inside an ``if``, a ``try`` or
        a ``with`` too): those that may have run before *node* and that no
        later one replaced on the way, and from a function inside *function*
        every one that may stand from its ``def`` on
        (:func:`ast_scan.live_bindings`), or every one when no *node* is
        given; none for an import, which the package follows; and ``None``
        for any other binding: the name is then the function's, and no
        function of the module or of an import is the one it calls.
        """
        how = own_names(function).how(name)
        if how == "definition":
            defined = _by_name(_own_definitions(function)).get(name, ())
            if node is None:
                return defined
            return tuple(live_bindings(function, list(defined), node))
        if how == "import":
            return ()
        if how != "binding" or name in own_names(function).parameters:
            return None
        nodes = bindings_by_name(function).get(name, [])
        if node is not None:
            nodes = live_bindings(function, nodes, node)
        aliases = [found for found in nodes if _aliases_a_name(found, self.tree)]
        if not nodes or len(aliases) < len(nodes):
            return None
        return tuple(
            dict.fromkeys(found for alias in aliases for found in self._aliased(alias))
        )

    def _aliased(self, target: ast.Name | ast.NamedExpr) -> tuple[Function, ...]:
        """The functions of this file an assignment of another name alone
        binds *target*, its target or the assignment expression, to: those
        that name stands for where the assignment reads it (:meth:`lookup`).
        """
        value = assigned_value(self.tree, target)
        if not isinstance(value, ast.Name) or id(target) in self._aliasing:
            return ()
        self._aliasing.add(id(target))
        try:
            return self.lookup(value.id, self.enclosing(value), value) or ()
        finally:
            self._aliasing.discard(id(target))

    def imports_at(
        self, name: str, scope: Function | None, node: ast.AST
    ) -> list[tuple[pathlib.Path, str]]:
        """Where *name*, read at *node* in *scope*, is imported from.

        From the nearest of *scope* and the functions around it that binds
        the name, its imports of it that may stand for it at *node*
        (:func:`ast_scan.live_bindings`): in *scope* itself, those that may
        have run before *node*, and in a function around it, those that may
        stand from the ``def`` of the one *node* runs in on. From the top of
        the module when none binds it, the same (:meth:`top_at`). None for a
        name a scope binds otherwise.
        """
        current = scope
        while current is not None:
            names = own_names(current)
            if names.rebinds(name):
                return []
            if name in names.declared_global:
                break
            if names.binds(name):
                statements = _imports_by_name(scope_nodes(current)).get(name, [])
                statements = live_bindings(current, statements, node)
                return _import_targets(statements, name, self.path)
            current = self.enclosing(current)
        return _import_targets(self.top_at(name, node)[1], name, self.path)

    def top_at(
        self, name: str, node: ast.AST | None
    ) -> tuple[tuple[Function, ...], list[ast.ImportFrom]]:
        """The functions and the relative imports at the top of the module
        that *name* may hold where *node* reads it (:func:`_top_live`), or
        once the module has run when *node* is None.

        A read in a function meets every one that may stand from the
        function's ``def`` on, since it may be called during the import.
        """
        if name in self.top_aliases or name in self.global_aliases:
            return self._top_with_aliases(name, node)
        if node is None:
            return self.top_functions.get(name, ()), self.top_live_imports.get(name, [])
        return _top_live(
            self.tree, self.top_defined, self.top_others, self.top_imports, name, node
        )

    def _top_with_aliases(
        self, name: str, node: ast.AST | None
    ) -> tuple[tuple[Function, ...], list[ast.ImportFrom]]:
        """:meth:`top_at` for a name an assignment of another name binds at
        the top of the module or under ``global`` (:attr:`top_aliases`): its
        ``def`` statements, its other bindings and those assignments are read
        in one order (:func:`ast_scan.live_bindings`), and each assignment
        that may stand for it stands for the functions its value names
        (:meth:`_aliased`), as one a function makes under ``global`` may.
        """
        defined = self.top_defined.get(name, ())
        aliases = self.top_aliases.get(name, [])
        live = live_bindings(
            self.tree, [*defined, *self.top_others.get(name, []), *aliases], node
        )
        inside_defined, inside_imported = _made_under_global(self.tree)
        functions = (
            *(found for found in defined if found in live),
            *(
                found
                for alias in aliases
                if alias in live
                for found in self._aliased(alias)
            ),
            *inside_defined.get(name, ()),
            *(
                found
                for alias in self.global_aliases.get(name, [])
                for found in self._aliased(alias)
            ),
        )
        imports = [found for found in self.top_imports.get(name, []) if found in live]
        return (
            tuple(dict.fromkeys(functions)),
            [*imports, *inside_imported.get(name, [])],
        )

    def top_import_targets(self, name: str) -> list[tuple[pathlib.Path, str]]:
        """Where the imports at the top of the module the name may hold once
        it has run read it from (:func:`_top_bindings`).
        """
        statements = self.top_live_imports.get(name, [])
        return _import_targets(statements, name, self.path)

    def named_functions(
        self, name: str, scope: Function | None
    ) -> tuple[Function, ...]:
        """The functions of this file *name* stands for, called from *scope* (:meth:`lookup`)."""
        return self.lookup(name, scope) or ()

    def comprehension_names(
        self, function: Function | None
    ) -> dict[int, list[tuple[str, ast.AST, int]]]:
        """The names a comprehension of *function* reads of its own variables
        (:func:`_comprehension_names`), keyed by the node of each.
        """
        if function is None:
            return {}
        if function not in self.comprehended:
            self.comprehended[function] = _comprehension_names(function)
        return self.comprehended[function]

    def local_bindings(
        self, function: Function
    ) -> dict[str, list[tuple[str, ast.AST, int]]]:
        """Every binding of a name inside a function, not inside nested ones.

        Each binding is ``(how, node, index)``: ``"value"`` for an assignment
        (``node`` is the assigned expression, ``index`` the position in a
        tuple unpacking or -1), ``"loop"`` for a ``for`` target (``node`` is
        the iterable), ``"opaque"`` for anything else. A comprehension's
        variables are its own (:func:`_comprehension_names`), and a ``:=``
        inside it binds the function's name. What an ``if TYPE_CHECKING:``
        block holds never runs, and binds nothing.
        """
        if function in self.locals:
            return self.locals[function]
        bindings: dict[str, list[tuple[str, ast.AST, int]]] = {}
        checker = for_the_type_checker(self.tree)
        for node in _walk_own(function):
            if id(node) in checker:
                continue
            if isinstance(
                node, ast.Assign | ast.AnnAssign | ast.AugAssign | ast.NamedExpr
            ):
                if node.value is None:
                    continue
                value: ast.AST = node.value
                if isinstance(node, ast.AugAssign):
                    value = ast.BinOp(
                        left=_load(node.target), op=node.op, right=node.value
                    )
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    _bind(bindings, target, "value", value)
            elif isinstance(node, ast.For | ast.AsyncFor):
                _bind_loop(bindings, node.target, node.iter)
            elif isinstance(node, ast.With | ast.AsyncWith):
                for item in node.items:
                    if item.optional_vars is not None:
                        _bind(bindings, item.optional_vars, "opaque", item.context_expr)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                bindings.setdefault(node.name, []).append(("opaque", node, -1))
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.attr in _GROWING
                and node.args
            ):
                # ``values.append(x)``: what the list holds is what was put in.
                bindings.setdefault(node.func.value.id, []).append(
                    ("value", node.args[-1], -1)
                )
        self.locals[function] = bindings
        return bindings

    # -- evaluation ----------------------------------------------------

    def _guarded(self, key: object, compute: Callable[[], Value]) -> Value:
        """Memoised evaluation that reads a cycle (``x = x + d``) as opaque.

        A value worked out while a cycle was cut short is what the key reads
        from inside that cycle, not what it reads on its own: it is kept only
        while the comparison being judged is read (:meth:`judge` forgets it),
        so the verdict on one comparison does not depend on which comparison
        of the file happened to be read first.
        """
        if key in self._memo:
            return self._memo[key]
        if key in self._provisional:
            self._cut = True
            return self._provisional[key]
        if key in self._busy:
            self._cut = True
            return OPAQUE
        outer_cut = self._cut
        self._cut = False
        self._busy.add(key)
        try:
            result = compute()
        finally:
            self._busy.discard(key)
        if self._cut:
            self._provisional[key] = result
        else:
            self._memo[key] = result
        self._cut = self._cut or outer_cut
        return result

    def value(self, node: ast.AST, context: Context) -> Value:
        """What an expression evaluated in ``context`` can be."""
        number = literal_number(node) if isinstance(node, ast.expr) else None
        if number is not None:
            return constant(number)
        if isinstance(node, ast.Constant | ast.JoinedStr):
            return Value(const=True)
        if isinstance(node, ast.Name):
            walked = self.comprehension_names(context.function).get(id(node))
            if walked is not None:
                return join(self.binding(item, context) for item in walked)
            return self.name(node.id, context)
        if isinstance(node, ast.Attribute):
            return self.attribute(node, context)
        if isinstance(node, ast.Subscript):
            base = self.value(node.value, context)
            return (
                Value(const=True)
                if base.const
                else dataclasses.replace(base, number=None)
            )
        if isinstance(node, ast.UnaryOp):
            return (
                WHOLE
                if isinstance(node.op, ast.Not)
                else self.value(node.operand, context)
            )
        if isinstance(node, ast.BinOp):
            return self.binop(node, context)
        if isinstance(node, ast.Call):
            return self.call(node, context)
        if isinstance(node, ast.IfExp):
            return join(
                [self.value(node.body, context), self.value(node.orelse, context)]
            )
        if isinstance(node, ast.Compare | ast.BoolOp):
            return WHOLE
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            if not node.elts:
                return Value(const=True)
            return join(self.value(element, context) for element in node.elts)
        if isinstance(node, ast.Starred | ast.NamedExpr):
            return self.value(node.value, context)
        if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp):
            return self.value(node.elt, context)
        return OPAQUE

    def binop(self, node: ast.BinOp, context: Context) -> Value:
        """Arithmetic; a small whole power is arithmetic, any other one is not."""
        left = self.value(node.left, context)
        right = self.value(node.right, context)
        if isinstance(node.op, ast.Pow):
            exponent = literal_number(node.right)
            if (
                exponent is not None
                and exponent.is_integer()
                and 0 < exponent <= _LARGEST_POWER
            ):
                power = combine([left], additive=False)
                if exponent % 2 == 0 and power.decimal:
                    power = dataclasses.replace(power, nonnegative=True)
                return power
            return Value(const=True) if left.const and right.const else OPAQUE
        if isinstance(node.op, ast.FloorDiv):
            # A floor division is a whole number whatever it divides.
            return Value(const=True) if left.const and right.const else WHOLE
        if not isinstance(
            node.op, ast.Add | ast.Sub | ast.Mult | ast.Div | ast.MatMult
        ):
            return (
                WHOLE
                if left.whole and right.whole
                else combine([left, right], additive=True)
            )
        if isinstance(node.op, ast.Div) and left.whole and right.whole:
            # A ratio of two whole numbers is correctly rounded: it equals the
            # literal of the same decimal, so it cannot fall either side of it.
            return Value(const=True) if left.const and right.const else WHOLE
        result = combine(
            [left, right],
            additive=isinstance(node.op, ast.Add | ast.Sub),
            subtracts=isinstance(node.op, ast.Sub),
        )
        if (
            isinstance(node.op, ast.Mult)
            and ast.dump(node.left) == ast.dump(node.right)
            and result.decimal
        ):
            # A square written as a product: never negative.
            result = dataclasses.replace(result, nonnegative=True)
        return result

    def name(self, name: str, context: Context) -> Value:
        """A name, looked up the way Python does: local, enclosing, module."""
        if name in {"True", "False", "None"}:
            return Value(const=True)
        current = context
        while current.function is not None:
            function = current.function
            if name in self.local_bindings(function):
                key = ("local", current, name)
                if key in self._busy and _parameter(function, name) is not None:
                    # Read inside its own binding, ``levels =
                    # np.asarray(levels)``, a parameter's name still holds the
                    # caller's value: the binding has not happened yet. Cut
                    # as a cycle, the caller's decimal went missing.
                    return self._guarded(
                        ("param", current, name),
                        functools.partial(self.parameter, current, name),
                    )
                return self._guarded(
                    key,
                    functools.partial(self.local, current, name),
                )
            if _parameter(function, name) is not None:
                return self._guarded(
                    ("param", current, name),
                    functools.partial(self.parameter, current, name),
                )
            if name in self.type_parameters_of(function):
                return OPAQUE
            current = Context(self.enclosing(function))
        if is_constant_name(name):
            return self.published(name)
        written = self.written_under_global().get(name, [])
        if name in self.module_names or written:
            return self._guarded(
                ("module", name),
                lambda: join(
                    [
                        *(
                            self.value(value, Context(None))
                            for value in self.module_names.get(name, [])
                        ),
                        *(
                            self.binding(item, Context(function))
                            for item, function in written
                        ),
                    ]
                ),
            )
        return OPAQUE

    def type_parameters_of(self, function: Function) -> frozenset[str]:
        """The type parameters *function* reads as names of its own: those it
        declares, and those of the generic classes around it, up to the
        function they are written in.
        """
        found = own_names(function).type_parameters
        current = self.parent.get(function)
        while current is not None and not isinstance(
            current, ast.FunctionDef | ast.AsyncFunctionDef
        ):
            if isinstance(current, ast.ClassDef):
                found |= own_names(current).type_parameters
            current = self.parent.get(current)
        return found

    def written_under_global(
        self,
    ) -> dict[str, list[tuple[tuple[str, ast.AST, int], Function]]]:
        """Each binding a function of the file makes of a module name it
        declares ``global`` (:meth:`local_bindings`), with that function, by
        the name: once the function has run, the module's name holds what it
        wrote, wherever another function reads it.
        """
        if self._written is None:
            found: dict[str, list[tuple[tuple[str, ast.AST, int], Function]]] = {}
            for node in ast.walk(self.tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                bindings = self.local_bindings(node)
                for name in sorted(own_names(node).declared_global):
                    for item in bindings.get(name, []):
                        found.setdefault(name, []).append((item, node))
            self._written = found
        return self._written

    def local(self, context: Context, name: str) -> Value:
        """A local name: the join of every binding it has in the function."""
        if context.function is None:
            return OPAQUE
        bindings = self.local_bindings(context.function)[name]
        return join(self.binding(item, context) for item in bindings)

    def published(self, name: str) -> Value:
        """An upper-case constant, with its value when this file or its source spells it."""
        number = _spelled(self.module_names, name)
        if number is None and name in self.imports:
            source, original = self.imports[name]
            number = _spelled(_module_constants(source), original)
        value = constant(number)
        if SLACK_NAME.search(name):
            value = dataclasses.replace(value, slack=True)
        return value

    def binding(self, binding: tuple[str, ast.AST, int], context: Context) -> Value:
        """One binding of a local name."""
        how, node, index = binding
        if how == "opaque":
            return OPAQUE
        if how == "loop":
            return self.element(node, index, context)
        if (
            index >= 0
            and isinstance(node, ast.Tuple | ast.List)
            and index < len(node.elts)
        ):
            return self.value(node.elts[index], context)
        return self.value(node, context)

    def element(self, iterable: ast.AST, index: int, context: Context) -> Value:
        """An element of what a loop runs over, or one name of its tuple target."""
        if isinstance(iterable, ast.Call):
            name = call_name(iterable)
            if name == "range":
                return WHOLE
            if name == "enumerate" and iterable.args:
                return WHOLE if index == 0 else self.value(iterable.args[0], context)
            if name == "zip" and 0 <= index < len(iterable.args):
                return self.value(iterable.args[index], context)
            if name in {"items", "keys"}:
                return OPAQUE
        return self.value(iterable, context)

    def parameter(self, context: Context, name: str) -> Value:
        """A parameter: what this call passes, what the file passes, or the caller's.

        Bound by the call being followed, it is what that call passes. Read on
        its own, a public function's parameter is the user's value, and a
        private function's, a private method's or a nested function's is
        whatever this file passes at its call sites, the default included.
        """
        function = context.function
        if function is None or name in {"self", "cls"}:
            return OPAQUE
        if context.bindings is not None:
            return dict(context.bindings).get(name, OPAQUE)
        default = _default(function, name)
        public = not function.name.startswith("_") and self.enclosing(function) is None
        sites = self.calls.get(function, [])
        if public or not sites:
            return (
                CALLER
                if default is None
                else join([CALLER, self.value(default, Context(None))])
            )
        return join(
            dict(self.bind(function, call, Context(scope))).get(name, OPAQUE)
            for call, scope in sites
        )

    def bind(
        self, function: Function, call: ast.Call, context: Context
    ) -> tuple[tuple[str, Value], ...]:
        """The parameters of ``function`` bound to what ``call`` passes."""
        arguments = function.args
        skip = 1 if self.is_method(function) and not _is_static(function) else 0
        positional = [arg.arg for arg in [*arguments.posonlyargs, *arguments.args]][
            skip:
        ]
        names = positional + [arg.arg for arg in arguments.kwonlyargs]
        by_place = {arg.arg for arg in arguments.posonlyargs}
        starred = _has_star(call)
        bound: dict[str, Value] = {}
        for name in names:
            argument = _argument(call, positional, name, keyword=name not in by_place)
            if argument is not None:
                bound[name] = self.value(argument, context)
                continue
            default = _default(function, name)
            unpacked = [
                self.value(value, context)
                for value in _unpacked_into(
                    call, positional, name, keyword=name not in by_place
                )
            ]
            if unpacked:
                if default is not None:
                    unpacked.append(self.value(default, Context(None)))
                bound[name] = join(unpacked)
            elif starred or default is None:
                bound[name] = OPAQUE
            else:
                bound[name] = self.value(default, Context(None))
        for extra in (arguments.vararg, arguments.kwarg):
            if extra is not None:
                bound[extra.arg] = OPAQUE
        return tuple(sorted(bound.items()))

    def attribute(self, node: ast.Attribute, context: Context) -> Value:
        """An attribute: a constant by its name, a count, a field or a property."""
        if node.attr in {"T", "flat"}:
            # A transpose or a flat view is what it views, not a constant ``T``.
            return self.value(node.value, context)
        if is_constant_name(node.attr):
            return Value(const=True, slack=bool(SLACK_NAME.search(node.attr)))
        if isinstance(node.value, ast.Name) and node.value.id in _NAMESPACES:
            return Value(const=True)
        if node.attr in _WHOLE_ATTRIBUTES:
            return WHOLE
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            owner = self.owner_class(context.function)
            if owner is not None:
                return self._guarded(
                    ("self", owner, node.attr),
                    functools.partial(self.member, owner, node.attr),
                )
            return OPAQUE
        base = self.value(node.value, context)
        if node.attr in {"real", "imag"}:
            # A complex quantity is a wave, not a reading: its parts are not
            # decimals a standard prints, and the sign of a root's imaginary
            # part picks a branch, not a verdict.
            return OPAQUE
        if base.const:
            # A field of a row of a published table (``TABLE[key].tolerance_db``,
            # ``_row(symbol).just_noticeable_difference``) is a published limit.
            return Value(const=True, slack=bool(SLACK_NAME.search(node.attr)))
        built = self.instance_class(node.value, context)
        if built is not None:
            return self._guarded(
                ("self", built, node.attr),
                functools.partial(self.member, built, node.attr),
            )
        if base.decimal and not base.depth:
            return CALLER
        return OPAQUE

    def instance_class(self, node: ast.expr, context: Context) -> ast.ClassDef | None:
        """The class of this file an expression is an instance of, when it is built here.

        ``Result(...)`` is one, and so is a local name every binding of which
        builds the same class; its field then stands for what the file builds
        it from, as ``self.field`` does inside the class. So is the parameter
        of a private function that every call in the file hands ``self`` of
        one class, or one instance built here: a ``__post_init__`` that passes
        ``self`` to a helper has the helper read the fields as the class
        would. An instance that a function or another module returns is not
        followed.
        """
        if isinstance(node, ast.Call):
            return (
                self.class_named(node.func.id, context.function, node)
                if isinstance(node.func, ast.Name)
                else None
            )
        if not isinstance(node, ast.Name):
            return None
        if id(node) in self.comprehension_names(context.function):
            # An item a comprehension walks, as a loop's item, is followed no
            # further.
            return None
        current = context.function
        while current is not None:
            bindings = self.local_bindings(current).get(node.id)
            if bindings is not None:
                owners = [
                    self.instance_class(value, Context(current))
                    if how == "value" and index < 0 and isinstance(value, ast.Call)
                    else None
                    for how, value, index in bindings
                ]
                first = owners[0]
                return first if all(owner is first for owner in owners) else None
            if _parameter(current, node.id) is not None:
                return self._guarded_class(
                    ("parameter", current, node.id),
                    functools.partial(self.parameter_class, current, node.id),
                )
            current = self.enclosing(current)
        return None

    def _guarded_class(
        self, key: object, compute: Callable[[], ast.ClassDef | None]
    ) -> ast.ClassDef | None:
        """:meth:`parameter_class` once per parameter, reading a cycle as no class."""
        if key in self._classes:
            return self._classes[key]
        if key in self._busy:
            return None
        self._busy.add(key)
        try:
            result = compute()
        finally:
            self._busy.discard(key)
        self._classes[key] = result
        return result

    def parameter_class(self, function: Function, name: str) -> ast.ClassDef | None:
        """The class a private function's parameter is an instance of, at every call.

        ``None`` for a public function, whose parameter is the user's, and for
        one that some call hands anything else.
        """
        public = not function.name.startswith("_") and self.enclosing(function) is None
        sites = self.calls.get(function, [])
        if public or not sites:
            return None
        skip = 1 if self.is_method(function) and not _is_static(function) else 0
        arguments = function.args
        positional = [arg.arg for arg in [*arguments.posonlyargs, *arguments.args]][
            skip:
        ]
        by_place = {arg.arg for arg in arguments.posonlyargs}
        owners: list[ast.ClassDef | None] = []
        for call, scope in sites:
            argument = _argument(call, positional, name, keyword=name not in by_place)
            if isinstance(argument, ast.Name) and argument.id == "self":
                owners.append(self.owner_class(scope))
            elif argument is not None:
                owners.append(self.instance_class(argument, Context(scope)))
            else:
                return None
        first = owners[0]
        return first if first is not None and all(o is first for o in owners) else None

    def member(self, owner: ast.ClassDef, attr: str) -> Value:
        """``self.attr``: a property's result, or what the file builds the field from."""
        methods = _methods(owner, attr)
        if methods:
            return join(
                self.returns(method, None) if _is_property(method) else OPAQUE
                for method in methods
            )
        fields = _fields(owner)
        if attr not in fields:
            return OPAQUE
        sites = self.constructions.get(owner, [])
        default = _field_default(owner, attr)
        if not sites:
            return (
                CALLER
                if default is None
                else join([CALLER, self.value(default, Context(None))])
            )
        values: list[Value] = []
        for call, scope in sites:
            argument = _argument(call, fields, attr, keyword=True)
            unpacked = _unpacked_into(call, fields, attr, keyword=True)
            if argument is not None:
                values.append(self.value(argument, Context(scope)))
            elif unpacked:
                values.extend(self.value(value, Context(scope)) for value in unpacked)
                if default is not None:
                    values.append(self.value(default, Context(None)))
            elif _has_star(call) or default is None:
                values.append(OPAQUE)
            else:
                values.append(self.value(default, Context(None)))
        return join(values)

    def returns(self, function: Function, bindings: Bindings) -> Value:
        """What a function of this file returns, for one call or for all."""
        context = Context(function, bindings)

        def compute() -> Value:
            values = [
                self.value(node.value, context)
                for node in _walk_own(function)
                if isinstance(node, ast.Return) and node.value is not None
            ]
            return join(values) if values else OPAQUE

        return self._guarded(("returns", context), compute)

    def call(self, node: ast.Call, context: Context) -> Value:
        """A call: settling, selecting, computing, fitting, counting, or this file's."""
        name = call_name(node)
        if name in SETTLING:
            # Settling a published constant leaves a published constant: it is
            # the computed side that has to be settled, not the limit.
            settled = [self.value(argument, context) for argument in node.args]
            if settled and all(item.const for item in settled):
                return (
                    constant(settled[0].number)
                    if len(settled) == 1
                    else Value(const=True)
                )
            return SETTLED
        if name in {"round", "around"}:
            return SETTLED if len(node.args) > 1 or node.keywords else WHOLE
        if name in TESTING or name in COUNTING:
            return WHOLE
        if name in FITTING:
            return Value(decimal=True, depth=2, cancels=True, fit=True)
        arguments = [self.value(argument, context) for argument in node.args]
        func = node.func
        method = isinstance(func, ast.Attribute) and not (
            isinstance(func.value, ast.Name) and func.value.id in _NAMESPACES
        )
        if method and isinstance(func, ast.Attribute):
            arguments.append(self.value(func.value, context))
        if name in ARITHMETIC:
            if all(item.const for item in arguments):
                return Value(const=True)
            result = combine(
                arguments or [OPAQUE],
                additive=name not in _MULTIPLYING,
                many=name in _SUMMING,
                subtracts=name in {"diff", "ptp", "subtract", "negative"},
            )
            if name in _SPREADS and result.decimal:
                # A standard deviation is never negative, but the mean it is
                # taken about is rounded, so identical readings give a few
                # units in the last place rather than zero.
                result = dataclasses.replace(result, nonnegative=True, cancels=True)
            elif name == "square" and result.decimal:
                result = dataclasses.replace(result, nonnegative=True)
            return result
        if name.startswith(("require_", "_require_")):
            return arguments[0] if arguments else OPAQUE
        if name in SELECTING or name == "get":
            chosen = (
                join(self.selected(node, name, context))
                if node.args or method
                else OPAQUE
            )
            if name in _MAGNITUDES and chosen.decimal:
                chosen = dataclasses.replace(chosen, nonnegative=True)
            return chosen
        if name in ROOTS:
            # The root of a value is zero exactly when the value is, so it keeps
            # the sign of a sum that cancels; it is no longer the decimal.
            inner = join(arguments) if arguments else OPAQUE
            return (
                dataclasses.replace(inner, root=True, nonnegative=True)
                if inner.decimal
                else OPAQUE
            )
        values = [
            self.returns(target, self.bind(target, node, context))
            for target in self.resolve_functions(node, context.function)
        ]
        if (
            isinstance(func, ast.Name)
            and self.package is not None
            # A name the caller, or a scope around the call, binds is not
            # the module's import of it.
            and self.lookup(func.id, context.function, node) is not None
        ):
            # A ``def`` in one branch and an import in the other: either.
            values.extend(
                owner.returns(function, self.bind(function, node, context))
                for owner, functions in self.package.functions(
                    self.imports_at(func.id, context.function, node)
                )
                for function in functions
            )
        return join(values) if values else OPAQUE

    def selected(self, node: ast.Call, name: str, context: Context) -> list[Value]:
        """What a selecting call hands back: which of its arguments it selects from.

        A method selects from what it is called on (``x.max()``, ``x.astype(t)``,
        ``table.get(key, default)`` adds the default); ``np.where(c, a, b)``
        selects from ``a`` and ``b``, never from the condition; ``max(a, b)`` and
        ``np.clip(x, lo, hi)`` from every argument; the rest from the first.
        """
        func = node.func
        if isinstance(func, ast.Attribute) and not (
            isinstance(func.value, ast.Name) and func.value.id in _NAMESPACES
        ):
            chosen = [self.value(func.value, context)]
            if name in {"get", "clip"}:
                chosen += [self.value(argument, context) for argument in node.args[1:]]
            return chosen
        if name in {"where", "select", "full", "full_like", "compress", "extract"}:
            sources = node.args[1:]
        elif name in _SELECTING_ALL:
            sources = node.args
        else:
            sources = node.args[:1]
        return [self.value(argument, context) for argument in sources]

    # -- the scan ------------------------------------------------------

    def comparisons(self) -> Iterator[tuple[ast.expr, ast.expr, ast.expr]]:
        """Every ordered comparison, pairwise, and the predicate calls."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Compare):
                operands = [node.left, *node.comparators]
                for index, operator in enumerate(node.ops):
                    if isinstance(operator, ast.Lt | ast.LtE | ast.Gt | ast.GtE):
                        yield node, operands[index], operands[index + 1]
            elif (
                isinstance(node, ast.Call)
                and call_name(node) in PREDICATES
                and node.args
            ):
                limit = node.args[1] if len(node.args) > 1 else ast.Constant(value=0.0)
                yield node, node.args[0], limit

    def findings(self) -> Iterator[Finding]:
        """The comparisons of the class in this file, one per comparison written.

        A chained comparison (``low <= x < high``) is one comparison: it is
        refused once, for the first of its pairs that is. What a test on
        ``TYPE_CHECKING`` keeps from running decides nothing, in a function
        written in such a block at the top of the module or in a class too.
        """
        refused: set[ast.expr] = set()
        never_runs = for_the_type_checker(self.tree)
        for node, left, right in self.comparisons():
            if node in refused or id(node) in never_runs:
                continue
            reason = self.judge(left, right, Context(self.enclosing(node)))
            if reason is None:
                continue
            refused.add(node)
            segment = ast.get_source_segment(self.source, node) or ast.unparse(node)
            yield Finding(
                self.relative,
                node.lineno,
                self.qualname(node),
                " ".join(segment.split()),
                reason,
            )

    def judge(self, left: ast.expr, right: ast.expr, context: Context) -> str | None:
        """Why a pair of operands is a boundary comparison left unsettled, or None."""
        self._provisional.clear()
        sides = (self.value(left, context), self.value(right, context))
        if any(side.slack for side in sides):
            # A slack moves the edge whichever side it is written on.
            return None
        for computed, limit in (sides, sides[::-1]):
            # Only the computed side settled takes it off the edge.
            if not limit.const or computed.settled:
                continue
            if limit.number is not None and not limit.number:
                if computed.fit:
                    return "a fitted value compared with zero"
                if (
                    computed.computed
                    and computed.cancels
                    and (computed.summed or computed.root)
                ):
                    return "a sum whose terms can cancel compared with zero"
                if computed.computed and computed.offset and not computed.root:
                    return "a computed decimal less a printed limit compared with zero"
            elif computed.computed and not computed.root:
                return "a computed decimal compared with a printed limit"
        return None


# -- AST helpers -------------------------------------------------------------


def _spelled(names: dict[str, list[ast.expr]], name: str) -> float | None:
    """The number a module-level name is assigned, when it is one literal."""
    numbers = [literal_number(value) for value in names.get(name, [])]
    if numbers and None not in numbers and len(set(numbers)) == 1:
        return numbers[0]
    return None


_CONSTANTS: dict[pathlib.Path, dict[str, list[ast.expr]]] = {}


def _module_constants(path: pathlib.Path) -> dict[str, list[ast.expr]]:
    """The module-level assignments of another file, read once."""
    if path not in _CONSTANTS:
        names: dict[str, list[ast.expr]] = {}
        if path.is_file():
            for node in ast.parse(path.read_text(encoding="utf-8")).body:
                for target, value in _assignments(node):
                    names.setdefault(target, []).append(value)
        _CONSTANTS[path] = names
    return _CONSTANTS[path]


def _imported_names(
    tree: ast.Module, path: pathlib.Path
) -> dict[str, tuple[pathlib.Path, str]]:
    """Each name a file imports from a sibling module, with the file it is in.

    Only relative imports are followed, which is how the package imports its
    own modules; the target is the module file or the package's ``__init__``.
    """
    found: dict[str, tuple[pathlib.Path, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.level:
            continue
        source = _import_source(node, path)
        for alias in node.names:
            found[alias.asname or alias.name] = (source, alias.name)
    return found


def _import_source(node: ast.ImportFrom, path: pathlib.Path) -> pathlib.Path:
    """The file a relative import written in *path* reads: the module file or
    the package's ``__init__``.
    """
    base = path.parent
    for _ in range(node.level - 1):
        base = base.parent
    target = base.joinpath(*(node.module or "").split(".")) if node.module else base
    return (
        target.with_suffix(".py")
        if target.with_suffix(".py").is_file()
        else target / "__init__.py"
    )


#: Nodes that open a scope of their own, whose names are not the function's.
_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)


def _own_definitions(scope: ast.AST) -> Iterator[Function]:
    """The functions *scope* defines as its own, in the order of the source.

    Those directly in its body and those written inside an ``if``, a
    ``try``, a ``with`` or a loop in it, which open no scope of their own;
    not those of a function or a class inside it.
    """
    for node in ast.iter_child_nodes(scope):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node
        elif not isinstance(node, _NESTED_SCOPES):
            yield from _own_definitions(node)


def _walk_own(function: Function) -> Iterator[ast.AST]:
    """The nodes of a function body, not those of functions nested in it."""
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        yield node
        stack.extend(
            child
            for child in ast.iter_child_nodes(node)
            if not isinstance(child, _NESTED_SCOPES)
        )


def _comprehension_names(
    function: Function,
) -> dict[int, list[tuple[str, ast.AST, int]]]:
    """Each name a comprehension of *function* reads of a variable it binds
    itself, keyed by the node of the name, with that binding: an item of
    what the comprehension walks.

    Python keeps a comprehension's variables inside it: the function's name
    of the same spelling is another name, and so is the comprehension's
    outside it. The first iterable is read in the scope around the
    comprehension, the rest of it in its own; an inner comprehension that
    binds the name again holds its own.
    """
    found: dict[int, list[tuple[str, ast.AST, int]]] = {}

    def visit(node: ast.AST, held: dict[str, list[tuple[str, ast.AST, int]]]) -> None:
        if isinstance(node, _NESTED_SCOPES):
            return
        if isinstance(node, ast.Name) and node.id in held:
            found[id(node)] = held[node.id]
        if not isinstance(node, _COMPREHENSIONS):
            for child in ast.iter_child_nodes(node):
                visit(child, held)
            return
        inner = dict(held)
        for generator in node.generators:
            visit(generator.iter, inner)
            bound: dict[str, list[tuple[str, ast.AST, int]]] = {}
            _bind_loop(bound, generator.target, generator.iter)
            inner.update(bound)
            for test in generator.ifs:
                visit(test, inner)
        parts = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
        for part in parts:
            visit(part, inner)

    for statement in function.body:
        visit(statement, {})
    return found


def _load(target: ast.expr) -> ast.expr:
    """An assignment target read back as an expression."""
    if isinstance(target, ast.Name):
        return ast.Name(id=target.id, ctx=ast.Load())
    return target


def _assignments(node: ast.stmt) -> Iterator[tuple[str, ast.expr]]:
    """``(name, value)`` for a module-level assignment of plain names."""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                yield target.id, node.value
    elif (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        yield node.target.id, node.value


def _bind(
    bindings: dict[str, list[tuple[str, ast.AST, int]]],
    target: ast.AST,
    how: str,
    value: ast.AST,
) -> None:
    while isinstance(target, ast.Subscript):
        # ``s[i] = x`` puts ``x`` in ``s``: the array holds what is stored in it.
        target = target.value
    if isinstance(target, ast.Name):
        bindings.setdefault(target.id, []).append((how, value, -1))
    elif isinstance(target, ast.Tuple | ast.List):
        for index, element in enumerate(target.elts):
            if isinstance(element, ast.Name):
                bindings.setdefault(element.id, []).append((how, value, index))
            elif isinstance(element, ast.Starred) and isinstance(
                element.value, ast.Name
            ):
                bindings.setdefault(element.value.id, []).append((how, value, -1))
            else:
                _bind(bindings, element, "opaque", value)


def _bind_loop(
    bindings: dict[str, list[tuple[str, ast.AST, int]]],
    target: ast.AST,
    iterable: ast.AST,
) -> None:
    if isinstance(target, ast.Name):
        bindings.setdefault(target.id, []).append(("loop", iterable, -1))
    elif isinstance(target, ast.Tuple | ast.List):
        for index, element in enumerate(target.elts):
            if isinstance(element, ast.Name):
                bindings.setdefault(element.id, []).append(("loop", iterable, index))
            elif isinstance(element, ast.Tuple | ast.List):
                _bind(bindings, element, "opaque", iterable)


def _parameter(function: Function, name: str) -> ast.arg | None:
    arguments = function.args
    for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]:
        if arg.arg == name:
            return arg
    for extra in (arguments.vararg, arguments.kwarg):
        if extra is not None and extra.arg == name:
            return extra
    return None


def _default(function: Function, name: str) -> ast.expr | None:
    arguments = function.args
    positional = [*arguments.posonlyargs, *arguments.args]
    for arg, default in zip(
        positional[len(positional) - len(arguments.defaults) :],
        arguments.defaults,
        strict=True,
    ):
        if arg.arg == name:
            return default
    for keyword, keyword_default in zip(
        arguments.kwonlyargs, arguments.kw_defaults, strict=True
    ):
        if keyword.arg == name:
            return keyword_default
    return None


def _argument(
    call: ast.Call, positional: list[str], name: str, *, keyword: bool
) -> ast.expr | None:
    """The argument *call* hands the parameter *name* of its own: the keyword
    of its name, when the parameter takes a keyword (*keyword*), or the
    argument in its place before the first ``*`` one. A keyword that names a
    positional-only parameter goes to ``**kwargs``.
    """
    for item in call.keywords if keyword else ():
        if item.arg == name:
            return item.value
    if name in positional:
        # An argument before the first ``*`` keeps its place; one after it
        # may land anywhere from there on (:func:`_unpacked_into`).
        index = positional.index(name)
        placed = itertools.takewhile(
            lambda argument: not isinstance(argument, ast.Starred), call.args
        )
        plain = list(placed)
        if index < len(plain):
            return plain[index]
    return None


def _unpacked_into(
    call: ast.Call, positional: list[str], name: str, *, keyword: bool
) -> list[ast.expr]:
    """What a call that unpacks its arguments may hand the parameter *name*
    when no argument of its own does (:func:`_argument`).

    A ``*`` argument, and every argument after it, may land in any place
    from the lowest it may take on (:func:`ast_scan.argument_places`): in
    the place of *name* when that is one of them, so ``f(*head, 1, value)``
    hands ``value`` to no first parameter. A ``**`` mapping may hand any
    parameter that takes a keyword (*keyword*) one of its values: those of
    a ``{...}`` written there, or the mapping.
    """
    found: list[ast.expr] = []
    if name in positional:
        place = positional.index(name)
        found.extend(
            argument.value if isinstance(argument, ast.Starred) else argument
            for argument, (lowest, spreads) in zip(
                call.args, argument_places(call.args), strict=True
            )
            if spreads and lowest <= place
        )
    if keyword:
        for item in call.keywords:
            if item.arg is not None:
                continue
            if isinstance(item.value, ast.Dict):
                found.extend(item.value.values)
            else:
                found.append(item.value)
    return found


def _has_star(call: ast.Call) -> bool:
    return any(isinstance(argument, ast.Starred) for argument in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    )


def _decorator_names(function: Function) -> set[str]:
    names: set[str] = set()
    for decorator in function.decorator_list:
        node = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _is_property(function: Function) -> bool:
    return bool(_decorator_names(function) & PROPERTY_DECORATORS)


def _is_static(function: Function) -> bool:
    return "staticmethod" in _decorator_names(function)


def _methods(owner: ast.ClassDef, name: str) -> tuple[Function, ...]:
    """The methods *owner* defines by *name*: one in each branch of an ``if``
    in its body too, which is either at run time, and not one a later one
    replaces.
    """
    return _live_by_name(owner, _own_definitions(owner)).get(name, ())


def _live_by_name(
    scope: ast.AST, functions: Iterable[Function]
) -> dict[str, tuple[Function, ...]]:
    """:func:`_by_name`, each name with the definitions it may hold once
    *scope* has run (:func:`ast_scan.live_bindings`).
    """
    return {
        name: tuple(live_bindings(scope, list(defined)))
        for name, defined in _by_name(functions).items()
    }


def _aliases_a_name(
    node: ast.AST, root: ast.AST
) -> TypeGuard[ast.Name | ast.NamedExpr]:
    """Whether *node*, under *root*, is a name an assignment binds to another
    name alone (``_spread = _range``), or an assignment expression that does
    (``(_spread := _range)``).
    """
    return assignment_target(node) is not None and isinstance(
        assigned_value(root, node), ast.Name
    )


def _top_names(
    tree: ast.Module,
) -> tuple[dict[str, tuple[Function, ...]], dict[str, list[ast.AST]]]:
    """Every ``def`` at the top of *tree*, by the name each binds, and every
    other binding of a name there that is no alias of another name
    (:func:`ast_scan.bindings_by_name`): an import, a ``class``, an
    assignment of anything else, a loop's target. Each is read beside the
    ``def`` statements and the aliases of its name, and one that is no
    import stands for no function, so it ends what came before it.
    """
    others: dict[str, list[ast.AST]] = {}
    for name, nodes in bindings_by_name(tree).items():
        rest = [
            node
            for node in nodes
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and not _aliases_a_name(node, tree)
        ]
        if rest:
            others[name] = rest
    return _by_name(_own_definitions(tree)), others


def _top_live(
    tree: ast.Module,
    defined: Mapping[str, tuple[Function, ...]],
    others: Mapping[str, list[ast.AST]],
    relative: Mapping[str, list[ast.ImportFrom]],
    name: str,
    point: ast.AST | None,
) -> tuple[tuple[Function, ...], list[ast.ImportFrom]]:
    """The functions and the relative imports at the top of *tree* that
    *name* may hold at *point*, or once the module has run when it is None.

    Its ``def`` statements and its other bindings (:func:`_top_names`) are
    read in one order (:func:`ast_scan.live_bindings`): an import after a
    ``def`` replaces it, a ``def`` after an import replaces that, a lambda
    or a ``class`` after either leaves no function, one in each branch of
    an ``if`` is either, and a read in a function meets every one from its
    ``def`` on.
    A ``def`` or a relative import that a function makes of the name under
    ``global`` (:func:`_made_under_global`) may stand at any point, since
    that function may have run before it.
    """
    live = live_bindings(tree, [*defined.get(name, ()), *others.get(name, [])], point)
    kept = tuple(node for node in defined.get(name, ()) if node in live)
    imports = [node for node in relative.get(name, []) if node in live]
    inside_defined, inside_imported = _made_under_global(tree)
    return (
        (*kept, *inside_defined.get(name, ())),
        [*imports, *inside_imported.get(name, [])],
    )


@functools.cache
def _made_under_global(
    tree: ast.Module,
) -> tuple[dict[str, tuple[Function, ...]], dict[str, list[ast.ImportFrom]]]:
    """Every ``def`` and every relative import a function, a method or a
    class body of *tree* makes of a module name under ``global``
    (:func:`ast_scan.global_bindings`), by the name: each may be what the
    name holds once that function has run, at any call.
    """
    defined: dict[str, tuple[Function, ...]] = {}
    imported: dict[str, list[ast.ImportFrom]] = {}
    for name, nodes in global_bindings(tree).items():
        functions = tuple(
            node
            for node in nodes
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        )
        if functions:
            defined[name] = functions
        imports = _imports_by_name(nodes).get(name, [])
        if imports:
            imported[name] = imports
    return defined, imported


def _top_bindings(
    tree: ast.Module, relative: Mapping[str, list[ast.ImportFrom]]
) -> tuple[dict[str, tuple[Function, ...]], dict[str, list[ast.ImportFrom]]]:
    """The functions and the relative imports at the top of *tree* each name
    holds once the module has run (:func:`_top_live`).

    A name none of whose functions is live has no entry among the functions,
    so a re-export is followed through its import.
    """
    defined, others = _top_names(tree)
    functions: dict[str, tuple[Function, ...]] = {}
    imports: dict[str, list[ast.ImportFrom]] = {}
    inside_defined, inside_imported = _made_under_global(tree)
    names = defined.keys() | relative.keys() | inside_defined.keys()
    for name in names | inside_imported.keys():
        kept, live_imports = _top_live(tree, defined, others, relative, name, None)
        if kept:
            functions[name] = kept
        imports[name] = live_imports
    return functions, imports


def _imports_by_name(
    nodes: Iterable[ast.AST],
) -> dict[str, list[ast.ImportFrom]]:
    """The relative imports among *nodes*, by each name they bind, in the order
    of the source: how the package imports its own modules.
    """
    found: dict[str, list[ast.ImportFrom]] = {}
    imports = [
        node for node in nodes if isinstance(node, ast.ImportFrom) and node.level
    ]
    for node in sorted(imports, key=lambda node: (node.lineno, node.col_offset)):
        for alias in node.names:
            found.setdefault(alias.asname or alias.name, []).append(node)
    return found


def _import_targets(
    statements: Iterable[ast.ImportFrom], name: str, path: pathlib.Path
) -> list[tuple[pathlib.Path, str]]:
    """Where each relative import of *statements* written in the file *path*
    reads *name* from: the module file, or the package's ``__init__``.
    """
    found: list[tuple[pathlib.Path, str]] = []
    for node in statements:
        source = _import_source(node, path)
        found.extend(
            (source, alias.name)
            for alias in node.names
            if (alias.asname or alias.name) == name
        )
    return found


def _by_name(functions: Iterable[Function]) -> dict[str, tuple[Function, ...]]:
    """*functions* by their names, each name with every definition of it."""
    found: dict[str, tuple[Function, ...]] = {}
    for function in functions:
        found[function.name] = (*found.get(function.name, ()), function)
    return found


def _fields(owner: ast.ClassDef) -> list[str]:
    """The constructor fields of a dataclass or named tuple, in order."""
    fields: list[str] = []
    for node in owner.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            annotation = ast.unparse(node.annotation)
            if "ClassVar" in annotation:
                continue
            if isinstance(node.value, ast.Call) and any(
                keyword.arg == "init"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
                for keyword in node.value.keywords
            ):
                continue
            fields.append(node.target.id)
    return fields


def _field_default(owner: ast.ClassDef, name: str) -> ast.expr | None:
    for node in owner.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
            and not isinstance(node.value, ast.Call)
        ):
            return node.value
    return None


# -- the guard ---------------------------------------------------------------


def scanned_files(root: pathlib.Path = SOURCE) -> Iterator[tuple[pathlib.Path, str]]:
    """Every file of the package the guard reads, with its path below it."""
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative.split("/", 1)[0] in PRESENTATION or relative == SETTLING_MODULE:
            continue
        yield path, relative


class Package:
    """Every file of the package, read once, so a call can follow an import.

    A value computed in one module and judged in another is the common case
    (a field indicator computed by one standard's module and graded by
    another's), so a call to a function this file imports from a sibling is
    read in that sibling, with its parameters bound to what the call passes.
    """

    def __init__(
        self, root: pathlib.Path, sources: Mapping[pathlib.Path, str] | None = None
    ) -> None:
        """Index nothing yet: a module is read the first time it is asked for.

        :param root: The package directory, ``src/phonometry``.
        :param sources: Text to read in place of a file's, by resolved path:
            how a test reads the tree with one comparison changed.
        """
        self.root = root.resolve()
        self.sources = dict(sources or {})
        self.modules: dict[pathlib.Path, Module] = {}

    def module(self, path: pathlib.Path) -> Module | None:
        """The indexed module of a file under the root, or ``None``."""
        path = path.resolve()
        if path not in self.modules:
            if not path.is_file() or not path.is_relative_to(self.root):
                return None
            relative = path.relative_to(self.root).as_posix()
            self.modules[path] = Module(path, relative, self, self.sources.get(path))
        return self.modules[path]

    def functions(
        self, targets: Iterable[tuple[pathlib.Path, str]], hops: int = 3
    ) -> list[tuple[Module, tuple[Function, ...]]]:
        """The functions each import of *targets* can be, through re-exports:
        every definition of it the module that defines it holds once it has
        run, each with that module.
        """
        found: list[tuple[Module, tuple[Function, ...]]] = []
        for source, original in targets:
            owner = self.module(source)
            if owner is None:
                continue
            if original in owner.top_functions:
                found.append((owner, owner.top_functions[original]))
            if hops > 1:
                found.extend(
                    self.functions(owner.top_import_targets(original), hops - 1)
                )
        return found


def scan(
    root: pathlib.Path = SOURCE, sources: Mapping[pathlib.Path, str] | None = None
) -> list[Finding]:
    """Every comparison of the refused shape under ``root``.

    :param root: The package directory.
    :param sources: Text to read in place of some files', as :class:`Package`.
    :return: The findings, file by file.
    """
    package = Package(root, sources)
    found: list[Finding] = []
    for path, _relative in scanned_files(root):
        module = package.module(path)
        if module is not None:
            found.extend(sorted(module.findings(), key=lambda item: item.line))
    return found


Key = tuple[str, str, str]


def read_exemptions(path: pathlib.Path = EXEMPTIONS) -> dict[Key, list[str]]:
    """The exemptions file, keyed as :attr:`Finding.key`, one reason per comparison.

    A line excuses one comparison. A function that writes the same comparison
    twice needs it listed twice, so that a third copy added later is refused
    rather than covered by the line written for the first.

    :param path: The file: comment lines start with ``#``; every other line
        is four tab-separated fields, file, function, comparison and reason.
    :return: The reasons by key, one per comparison the key excuses.
    :raises ValueError: On a line without four fields or without a reason;
        an exemption that says nothing is no decision.
    """
    exemptions: dict[Key, list[str]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != _EXEMPTION_FIELDS or not fields[3].strip():
            msg = f"{path.name}:{number}: expected file, function, comparison and reason, tab-separated"
            raise ValueError(msg)
        key = (fields[0], fields[1], fields[2])
        exemptions.setdefault(key, []).append(fields[3].strip())
    return exemptions


#: The fields of an exemption line.
_EXEMPTION_FIELDS = 4


#: An exemption that covers fewer comparisons than it lists: the key, how
#: many comparisons it lists and how many the scan finds.
Stale = tuple[Key, int, int]


def classify(
    findings: list[Finding], exempt: Mapping[Key, Sequence[str]]
) -> tuple[list[Finding], list[Stale]]:
    """Split the findings into the refused ones and the stale exemptions.

    The split counts: a key is a file, a function and the text of a
    comparison, and the same text can be written more than once in a function,
    so a key excuses as many comparisons as it has lines and no more.

    :param findings: Every comparison of the shape, exempt or not.
    :param exempt: The exemptions, one reason per comparison, by key.
    :return: Every finding of a key that has more comparisons than exemptions,
        and the sorted exemptions that list more comparisons than there are.
    """
    found = collections.Counter(finding.key for finding in findings)
    refused = [
        finding
        for finding in findings
        if found[finding.key] > len(exempt.get(finding.key, ()))
    ]
    stale = sorted(
        (key, len(reasons), found[key])
        for key, reasons in exempt.items()
        if len(reasons) > found[key]
    )
    return refused, stale


def main(argv: list[str] | None = None) -> int:
    """Report every boundary comparison left unsettled and every stale exemption."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--list",
        action="store_true",
        help="print every comparison of the refused shape, exempted or not, and exit 0",
    )
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to scan (default: src/phonometry)",
    )
    options = parser.parse_args(argv)
    findings = scan(options.root)
    if options.list:
        for finding in findings:
            print(
                f"{finding.path}:{finding.line} [{finding.scope}] {finding.text}  ({finding.reason})"
            )
        return 0
    exempt = read_exemptions()
    refused, stale = classify(findings, exempt)
    if not refused and not stale:
        print(
            f"No unsettled boundary comparison in src: {len(findings)} of the shape, "
            "each exempted with a reason."
        )
        return 0
    if refused:
        print(
            "::error::a verdict compares a computed decimal with a printed limit unsettled - see below"
        )
        for finding in refused:
            print(
                f"  src/phonometry/{finding.path}:{finding.line} in {finding.scope}: {finding.text}"
            )
            print(f"    {finding.reason}")
            listed = len(exempt.get(finding.key, ()))
            if listed:
                print(
                    f"    the function writes it more often than the {listed} "
                    "exempted: list the new one, or settle it"
                )
        print(
            "  -> settle the computed side through phonometry._internal.boundary (settled,"
            " settled_ratio, settled_net_share) or compare it with a named slack; if it cannot"
            " sit on the limit, add it to scripts/boundary_comparison_exemptions.tsv with the reason."
        )
    for (path, scope, text), listed, matched in stale:
        print(
            f"::error::boundary_comparison_exemptions.tsv lists {text!r} in {path} {scope} "
            f"{listed} time(s), and {matched} comparison(s) of the shape match it"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
