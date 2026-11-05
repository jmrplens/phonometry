#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a conversion of a caller's numbers that reads a complex value or a text as numbers.

``np.asarray(x, dtype=np.float64)`` takes a complex value and gives back its
real part, with no more than a ``ComplexWarning``: ``[1 + 2j]`` comes back as
``[1.0]``, and so does a NumPy complex number held in a list or an array of
objects. It parses a text (``["94"]`` as ``[94.0]``) and reads a
``bytearray`` as the codes of its characters. ``np.asarray(x,
dtype=complex)`` parses a text the same way. A function that converts what its
caller gave it that way checks, computes and returns from a value the caller
never gave, and ISO/TS 12913-3's ``method_b_scale_values`` rated
``np.complex128(0.5 + 0.3j)`` as the mark at 0.5. The library reads a caller's
numbers through the shared readers of ``src/phonometry/_internal/validation.py``,
:func:`real_array` and, where a complex value belongs, :func:`complex_array`,
which refuse what they cannot read by the parameter's name, or asks one of the
shared checks first (:data:`CHECKS`).

This reads every module under ``src/phonometry`` and reports a conversion of
a caller's value that no check has read on every path to it:

- **A conversion to floats**: ``np.asarray``, ``np.array``,
  ``np.asanyarray``, ``np.ascontiguousarray``, ``np.asfortranarray``,
  ``np.require`` and ``np.fromiter`` with a real floating dtype, given by
  keyword or in second place; the fill value of ``np.full`` and
  ``np.full_like`` with one; ``.astype()`` of one; and ``np.float64()`` and
  its kin of a value. A real floating dtype is ``float``, ``np.float64`` and
  the rest, a text that names one (``"f8"``, ``"<f8"``, ``"float64"``),
  ``np.dtype()`` of one, or a name bound to one; a constructor imported from
  NumPy by name counts as one called through ``np``.
- **A conversion to complex numbers**: the same calls with a complex dtype
  (``complex``, ``np.complex128``, ``"c16"`` and the rest), and
  ``np.complex128()`` and its kin of a value. A complex value is what these
  read, but a text is parsed and a ``bytearray`` read as codes all the same.
- **A caller's value**: a parameter of the function that holds the
  conversion, a nested function's included, or a name a nested function or
  a ``lambda`` shares with the function around it, as that function holds
  it where it uses the nested one (or, used nowhere, where it defines it),
  read bare or through what keeps
  it the caller's (an item of it, ``x[0]``; ``np.atleast_1d(x)``,
  ``np.ravel(x)``, ``list(x)``, ``np.concatenate([x, y])``, ``x.T`` and the
  other calls and attributes that keep its values;
  ``getattr(x, name, x)``, whose default is the value itself), a tuple or a
  list that holds one, a name bound to one of those, or a name a ``for``
  loop or a comprehension takes from one, and a comprehension whose element
  is so read; arithmetic on one (``x * 2``, ``-x``, ``x += y``), which
  keeps a complex value complex and repeats or joins a list or a text,
  checked as far as every operand it is made of was; and, in a record's
  ``__post_init__``, a field, ``self.x``, which the caller set.
- **A helper read through its calls**: a function at the top of a module
  that no caller of the library reaches (its name, or a name of its
  module's path, opens with an underscore, and no ``__all__`` publishes it)
  and that the package only calls, never hands on, keeps in a table or
  decorates with. Its parameters hold what its calls across the package
  hand them, joined: a caller's value no check read where any call hands
  one, checked where every call hands a checked one, and none where only
  values the library computed reach it. The modules are read again until no
  call hands anything new. Any other function's parameters, a method's and
  a nested function's included, are a caller's values.
- **A check**: a call of one of :data:`CHECKS` with the value among its
  arguments, or of a function of the library that hands that parameter to
  one on every path that leaves it by its end or a ``return`` (found by
  following such calls through the package until no new one turns up): a
  call after an earlier ``return``, in the body of a ``try`` a handler of
  which goes on, or of a parameter rebound before it to another value
  counts for nothing; or a name rebound to what a check returns. A check
  handed a conditional expression reads what both of its branches hold, and
  the name its test finds ``None`` (``d if x is None else x``) where the
  branch that runs while it is not holds it; handed ``getattr(x, name, d)``,
  nothing of ``d``, which is read only when the attribute is missing. A check
  handed what NumPy made of a caller's value no check has refused a text in
  (``np.asarray(x)``, ``np.atleast_1d(x)`` and the other NumPy calls that
  keep its values, given no floating dtype, or a name bound to one on any
  path that reaches the check, an item a loop takes from one included) reads
  a ``bytearray`` as the codes of its characters, and the census lists that
  reading as a conversion no check precedes. What each check refuses is
  listed, a complex value, a text or both: a conversion to floats needs both
  refused, one to complex numbers a text. A check of an item (``x[0]``)
  reads that item, not the sequence it was taken from.
- **On every path**: the function is read the way it runs. A check inside
  an ``if`` holds after it only when the other branch checks too or leaves
  the function; a check in one branch does not reach the other; a check in
  a loop's body, a conditional expression, the right side of ``and`` or
  ``or``, a later link of a chained comparison, or a comprehension may not
  run, and holds only inside it; one in an ``assert``, which ``python -O``
  leaves out, holds nowhere.

A call is read as Python reads its name: a scope nearer than the module that
binds the name to anything else hides the function of that spelling, though a
parameter defaulting to it and a local assigned from it hold it all the same
(``float=float``, ``asarray = np.asarray``). So does the module's own binding: a
later ``def`` or assignment takes the name from a check or a NumPy function the
module imported, and a ``def float`` is no builtin. What a test on
``TYPE_CHECKING`` keeps from running converts and checks nothing, in a statement
or a conditional expression, negated or not, wherever it is written.

A value the function computed (a call of a function of the package that is
no check, a field of a record it was handed, which the record read when it
was built) is no caller's, and the census lists it as computed. A field a record's method
reads outside ``__post_init__`` is listed apart: the record's constructor is
where its caller's value was read.

``--census`` prints every conversion in the tree with what it reads, so that
the class is listed whole and not only what is left of it. ``--source``
reads another copy of the library, with that copy's own checks.

A conversion of a value that is no caller's number but that the rule cannot
tell from one (an array of objects an ``isinstance`` test has read item by
item, the quick path of the readers themselves, the drawing helper whose
source the published clips fingerprint, which draws what a result holds, a
stage handed to another function or to a root finder, a function held in a
table, a private method) is listed in :data:`EXEMPT`, keyed by file and
function with the reason; an entry that covers nothing is reported too.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal, TypeGuard

from ast_scan import (
    ROOT,
    assigned_value,
    binding_of,
    block_statements,
    empty_type_checking_bodies,
    exempted,
    for_the_type_checker,
    imported_names,
    is_type_checking_block,
    own_names,
    python_files,
    relative,
    spells,
    standing_bindings,
    values_bound,
    what_runs,
)
from ast_scan import parameters as with_defaults

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

#: The library this reads, the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"
#: The package every module of the library is named from.
PACKAGE = "phonometry"
#: The module that holds :data:`CHECKS`, by the name it is imported by.
SHARED = f"{PACKAGE}._internal.validation"

#: What a check refuses: a complex value, a text (a ``bytearray`` included).
Refusal = Literal["complex", "text"]
#: What a conversion is to.
Kind = Literal["real", "complex"]

_BOTH: frozenset[Refusal] = frozenset({"complex", "text"})
_TEXT: frozenset[Refusal] = frozenset({"text"})
_COMPLEX: frozenset[Refusal] = frozenset({"complex"})

#: What a conversion of each kind needs refused before it reads a caller's value.
NEEDS: dict[Kind, frozenset[Refusal]] = {"real": _BOTH, "complex": _TEXT}

#: The shared checks of ``_internal/validation.py``, by name, with what each
#: refuses of every argument it is given.
#: ``tests/test_check_real_conversions.py`` calls each with a complex value
#: and with a text and wants the refusals listed here.
CHECKS: dict[str, frozenset[Refusal]] = {
    "real_array": _BOTH,
    "complex_array": _TEXT,
    "real_number": _BOTH,
    "complex_number": _TEXT,
    "refuse_complex": _COMPLEX,
    "refuse_text": _TEXT,
    "refuse_text_beside_choice": _TEXT,
    "require_real": _BOTH,
    "require_scalar": _BOTH,
    "require_positive": _BOTH,
    "require_non_negative": _BOTH,
    "require_finite": _BOTH,
    "require_fraction": _BOTH,
    "require_count": _BOTH,
    "require_above_absolute_zero": _BOTH,
    "require_above_absolute_zero_array": _BOTH,
    "require_positive_array": _BOTH,
    "require_finite_array": _BOTH,
    "require_finite_matrix": _BOTH,
    "require_1d_signal": _BOTH,
    "require_per_band": _BOTH,
    "arrays_of": _BOTH,
    "pair_of_arrays": _BOTH,
    "floats_of": _BOTH,
    "pair_of_floats": _BOTH,
}

#: The NumPy constructors that convert their first argument to the dtype they
#: are given, in second place or by keyword.
_ARRAY_CONVERSIONS = frozenset(
    {
        "asarray",
        "array",
        "asanyarray",
        "ascontiguousarray",
        "asfortranarray",
        "require",
        "fromiter",
    }
)
#: The NumPy constructors that convert a fill value, second, to the dtype
#: they are given, third or by keyword.
_FILLS = frozenset({"full", "full_like"})
#: The floating dtypes by the name of their type.
_REAL_TYPES = frozenset(
    {
        "float",
        "float16",
        "float32",
        "float64",
        "float128",
        "float_",
        "double",
        "single",
        "half",
        "longdouble",
    }
)
_COMPLEX_TYPES = frozenset(
    {
        "complex",
        "complex64",
        "complex128",
        "complex256",
        "complex_",
        "cdouble",
        "csingle",
        "clongdouble",
    }
)
#: The dtypes by a text NumPy reads, after its byte order (``<``, ``>``,
#: ``=``, ``|``).
_REAL_TEXTS = _REAL_TYPES | {"f2", "f4", "f8", "f16", "d", "f", "e", "g"}
_COMPLEX_TEXTS = _COMPLEX_TYPES | {"c8", "c16", "c32", "D", "F", "G"}
#: Python's own conversions of one value: ``float("94")`` parses a text and
#: ``float(np.complex128(1 + 1j))`` keeps the real part with no more than a
#: ``ComplexWarning``; ``complex("1+2j")`` parses a text too.
_BUILTIN_SCALARS: dict[str, Kind] = {"float": "real", "complex": "complex"}
#: The NumPy scalar types whose call converts one value.
_SCALARS: dict[str, Kind] = {
    **dict.fromkeys(_REAL_TYPES - {"float", "float_"}, "real"),
    **dict.fromkeys(_COMPLEX_TYPES - {"complex", "complex_"}, "complex"),
}
#: The calls that keep their argument's values the caller's, as a method of
#: it (``x.ravel()``) or a function of their first argument
#: (``np.atleast_1d(x)``).
_KEEPING_CALLS = frozenset(
    {
        "asarray",
        "array",
        "asanyarray",
        "ascontiguousarray",
        "asfortranarray",
        "atleast_1d",
        "atleast_2d",
        "atleast_3d",
        "ravel",
        "squeeze",
        "copy",
        "list",
        "tuple",
        "sorted",
        "reversed",
        "enumerate",
        "flatten",
        "reshape",
        "transpose",
        "concatenate",
        "stack",
        "vstack",
        "hstack",
        "dstack",
        "column_stack",
        "row_stack",
        "broadcast_to",
        "expand_dims",
        "tile",
        "repeat",
        "flip",
        "fliplr",
        "flipud",
        "roll",
        "moveaxis",
        "swapaxes",
    }
)
#: The calls that keep the values of every argument they are given.
_KEEPING_ALL = frozenset({"zip", "append", "chain"})
#: The arguments of ``getattr(value, name, default)``, whose default is read
#: when the attribute is missing.
_GETATTR_WITH_DEFAULT = 3
#: The attributes of an array that keep its values.
_KEEPING_ATTRIBUTES = frozenset({"T", "mT"})

#: The conversions of a value that is no caller's number, which the rule
#: cannot tell, keyed by the file relative to the repository and the function
#: that holds them, with the reason.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_plot/common.py", "_plot_band_level_bars"): (
        "the levels of a result being drawn, a field the result read when it "
        "was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_internal/validation.py", "real_array"): (
        "the shared reader itself, whose quick path converts only an array of "
        "truth values, integers or floats, which holds no complex number"
    ),
    ("src/phonometry/_internal/validation.py", "complex_array"): (
        "the shared reader itself, which converts only after it has refused a "
        "text at any depth"
    ),
    ("src/phonometry/simulation/fdtd.py", "_held_map"): (
        "a map converted only when holds_complex and holds_text have found "
        "neither in it; anything else is handed back as given, for the checks "
        "of the medium to refuse in their own words"
    ),
    ("src/phonometry/_internal/catalogue.py", "PrintedNumber.__new__"): (
        "a number printed in a catalogue, built from the text the table or the "
        "user's file prints: reading that text is what it is for, and its "
        "Decimal reads it first"
    ),
    ("src/phonometry/io/_sidecar.py", "_real"): (
        "converts only once the value, read by NumPy, is one number of a real "
        "dtype kind, which no text and no complex value is"
    ),
    ("src/phonometry/simulation/fdtd.py", "_real_objects"): (
        "an array of objects converted only after an isinstance test that every "
        "item is a real number and no truth value"
    ),
    (
        "src/phonometry/environment/propagation/barrier_reflection.py",
        "_window_spectrum.piece",
    ): (
        "the closed form of one piece of the window, called by _window_spectrum "
        "with the start, the length and the coefficients of its own three pieces"
    ),
    (
        "src/phonometry/filters/weighting_compliance.py",
        "_analytic_weighting_db._c_gain",
    ): (
        "a stage of the analytic weighting, called only with the frequencies "
        "real_array read at the top of _analytic_weighting_db"
    ),
    (
        "src/phonometry/filters/weighting_compliance.py",
        "_analytic_weighting_db._a_gain",
    ): (
        "a stage of the analytic weighting, called only with the frequencies "
        "real_array read at the top of _analytic_weighting_db"
    ),
    (
        "src/phonometry/filters/weighting_compliance.py",
        "_analytic_weighting_db._b_gain",
    ): (
        "a stage of the analytic weighting, called only with the frequencies "
        "real_array read at the top of _analytic_weighting_db"
    ),
    ("src/phonometry/simulation/elastic_fdtd.py", "scholte_speed.characteristic"): (
        "the characteristic equation of the Scholte wave, called on a grid of "
        "trial values scholte_speed builds between bounds of its own and by the "
        "root finder it is handed to"
    ),
    ("src/phonometry/filters/compliance.py", "_reference_bandwidth_1995"): (
        "held in _BANDWIDTH_INTEGRALS and called with the fraction of the bank "
        "under test, which the bank read through require_scalar when it was built"
    ),
    ("src/phonometry/vibration/human/exposure.py", "_band_limiting"): (
        "a stage of the weighting handed to _evaluate_at, which calls it with the "
        "complex frequencies it builds from the frequencies real_array read"
    ),
    ("src/phonometry/vibration/human/exposure.py", "_overall_weighting"): (
        "a stage of the weighting handed to _evaluate_at, which calls it with the "
        "complex frequencies it builds from the frequencies real_array read"
    ),
    (
        "src/phonometry/vibration/structural/_impact_mobility.py",
        "SingleModeFitResult._synthesize",
    ): (
        "a private method whose pole is the record's own, made a complex number "
        "by the method that calls it; the frequencies are read through real_array"
    ),
}

#: What a conversion reads, as the census lists it.
Verdict = Literal["unchecked", "checked", "computed", "field"]
#: How bad each verdict is, for a conversion a loop reads twice.
_SEVERITY: dict[Verdict, int] = {
    "computed": 0,
    "field": 1,
    "checked": 2,
    "unchecked": 3,
}


@dataclass(frozen=True)
class Conversion:
    """One conversion of a value, with what it reads."""

    path: pathlib.Path
    line: int
    function: str
    source: str
    verdict: Verdict
    kind: Kind = "real"
    file: str = ""

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the function, as EXEMPT keys them."""
        return self.file or relative(self.path), self.function

    def describe(self) -> str:
        """One line naming the place, the verdict and the code."""
        to = "" if self.kind == "real" else " (to complex)"
        return (
            f"{self.key[0]}:{self.line}  {self.function}  "
            f"{self.verdict}{to}: {self.source}"
        )


def _last_name(node: ast.expr) -> str | None:
    """``f`` of ``f``, of ``np.f`` and of ``a.b.f``; ``None`` for anything else."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _argument(call: ast.Call, place: int, name: str) -> ast.expr | None:
    """The argument of *call* given in *place* or by *name*."""
    if len(call.args) > place:
        return call.args[place]
    return _keyword(call, name)


def _text_kind(text: str) -> Kind | None:
    bare = text.lstrip("<>=|")
    if bare in _REAL_TEXTS:
        return "real"
    if bare in _COMPLEX_TEXTS:
        return "complex"
    return None


@dataclass(frozen=True)
class _Names:
    """How a module spells NumPy: the names it imports from it, and the names
    bound to a dtype, by kind.
    """

    numpy: frozenset[str] = frozenset()
    dtypes: Mapping[str, Kind] = field(default_factory=dict)
    #: Each call of the module, by its id, of a name a nearer scope binds
    #: (:func:`_calls_by_what_they_reach`), which reaches no function by name.
    hidden: frozenset[int] = frozenset()
    #: Each call, by its id, of a name read by its spelling that the module's
    #: own binding replaces, which reaches that and no builtin or NumPy function.
    replaced: frozenset[int] = frozenset()

    def callee(self, func: ast.expr) -> str | None:
        """The NumPy name a call reaches: any attribute, or a name imported from NumPy."""
        if isinstance(func, ast.Attribute):
            return func.attr
        if isinstance(func, ast.Name) and func.id in self.numpy:
            return func.id
        return None

    def kind(self, node: ast.expr | None) -> Kind | None:
        """The kind of dtype *node* names, ``None`` when it names none."""
        if node is None:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return _text_kind(node.value)
        if isinstance(node, ast.Name) and node.id in self.dtypes:
            return self.dtypes[node.id]
        if (
            isinstance(node, ast.Call)
            and _last_name(node.func) == "dtype"
            and node.args
        ):
            return self.kind(node.args[0])
        name = _last_name(node)
        if name in _REAL_TYPES:
            return "real"
        if name in _COMPLEX_TYPES:
            return "complex"
        return None


#: A module that imports nothing from NumPy and binds no dtype.
_PLAIN = _Names()


def converted(call: ast.Call, names: _Names = _PLAIN) -> tuple[ast.expr, Kind] | None:
    """The value *call* converts and to what, or ``None`` when it converts none."""
    if id(call) in names.hidden or id(call) in names.replaced:
        return None
    name = names.callee(call.func)
    if name in _ARRAY_CONVERSIONS:
        kind = names.kind(_argument(call, 1, "dtype"))
        value = _argument(call, 0, "a")
    elif name in _FILLS:
        kind = names.kind(_argument(call, 2, "dtype"))
        value = _argument(call, 1, "fill_value")
    elif name == "astype" and isinstance(call.func, ast.Attribute):
        kind = names.kind(_argument(call, 0, "dtype"))
        value = call.func.value
    elif name in _SCALARS and len(call.args) == 1:
        kind, value = _SCALARS[name], call.args[0]
    elif (
        isinstance(call.func, ast.Name)
        and call.func.id in _BUILTIN_SCALARS
        and len(call.args) == 1
        and not call.keywords
    ):
        kind, value = _BUILTIN_SCALARS[call.func.id], call.args[0]
    else:
        return None
    return None if kind is None or value is None else (value, kind)


def _dtype_names(
    nodes: Iterable[ast.AST], names: _Names, function: ast.AST | None = None
) -> dict[str, Kind]:
    """The names *nodes* bind to a dtype, and the parameters of *function* whose
    default is one.
    """
    found: dict[str, Kind] = {}
    for node in nodes:
        if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
            kind = names.kind(node.value)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            found.update(
                (target.id, kind)
                for target in targets
                if kind is not None and isinstance(target, ast.Name)
            )
    if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
        found.update(_default_dtypes(function, names))
    return found


def _default_dtypes(
    function: ast.FunctionDef | ast.AsyncFunctionDef, names: _Names
) -> dict[str, Kind]:
    """The parameters of *function* whose default names a dtype, by kind."""
    arguments = function.args
    positional = [*arguments.posonlyargs, *arguments.args]
    pairs = [
        *zip(
            positional[len(positional) - len(arguments.defaults) :],
            arguments.defaults,
            strict=True,
        ),
        *zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True),
    ]
    found: dict[str, Kind] = {}
    for parameter, default in pairs:
        if default is not None and (kind := names.kind(default)) is not None:
            found[parameter.arg] = kind
    return found


#: What a name holds at a place: ``None`` for no caller's value, or the
#: refusals checks have made of the caller's value it holds (empty when none).
State = frozenset[Refusal] | None


def join(first: State, second: State) -> State:
    """What a name holds where two paths meet: a caller's value if either path
    holds one, with only the refusals both made.
    """
    if first is None:
        return second
    if second is None:
        return first
    return first & second


#: What each name holds at a place.
Env = dict[str, State]


def _numpy_key(name: str) -> str:
    """The key under which an env marks *name* as bound to what NumPy made of
    a caller's value no check has refused a text in.

    The mark lives in the env, so each branch reads it as its own path left
    it, a join keeps it when any path does, and binding the name again drops
    it with the name's items; no source spells ``[<numpy>]``.
    """
    return f"{name}[<numpy>]"


def _join_envs(envs: Sequence[Env], default: Callable[[str], State]) -> Env:
    if not envs:
        return {}
    keys = set().union(*envs)
    joined: Env = {}
    for key in keys:
        state = envs[0].get(key, default(key))
        for env in envs[1:]:
            state = join(state, env.get(key, default(key)))
        joined[key] = state
    return joined


def _parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
) -> list[str]:
    """The parameters of *function*, in order, ``self`` and ``cls`` left out."""
    arguments = function.args
    named = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    named.extend(each for each in (arguments.vararg, arguments.kwarg) if each)
    return [p.arg for p in named if p.arg not in {"self", "cls"}]


def _targets(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        return [name for item in target.elts for name in _targets(item)]
    if isinstance(target, ast.Starred):
        return _targets(target.value)
    return []


def _none_test(test: ast.expr) -> tuple[str | None, bool]:
    """The name *test* compares with ``None`` by ``is`` or ``is not``, and
    whether the test holds when the name is ``None``; ``(None, False)`` for
    any other test.
    """
    if (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Is | ast.IsNot)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    ):
        return test.left.id, isinstance(test.ops[0], ast.Is)
    return None, False


def _or_a_number(node: ast.expr) -> TypeGuard[ast.BoolOp]:
    """Whether *node* is ``x or d`` with every operand after the first a
    number or ``None``: what a check handed it reads is *x* whenever *x* is
    a value at all, and otherwise the number, which the check accepts.
    """
    return (
        isinstance(node, ast.BoolOp)
        and isinstance(node.op, ast.Or)
        and all(
            isinstance(value, ast.Constant)
            and (value.value is None or type(value.value) in {int, float})
            for value in node.values[1:]
        )
    )


#: The types an ``isinstance`` test may name whose instances are real
#: numbers: neither a text nor a complex value passes the test.
_REAL_CLASSES = frozenset(
    {
        "bool",
        "int",
        "float",
        "Real",
        "Rational",
        "Integral",
        "Fraction",
        "Decimal",
        "bool_",
        "integer",
        "signedinteger",
        "unsignedinteger",
        "floating",
        *(f"{kind}{bits}" for kind in ("int", "uint") for bits in (8, 16, 32, 64)),
        "float16",
        "float32",
        "float64",
        "longdouble",
    }
)
#: The types an ``isinstance`` test may name whose instances are numbers,
#: complex ones among them: no text passes the test.
_NUMBER_CLASSES = _REAL_CLASSES | frozenset(
    {"complex", "Complex", "Number", "number", "inexact", "complexfloating"}
    | {"complex64", "complex128", "clongdouble"}
)


def _class_refusals(node: ast.expr) -> frozenset[Refusal]:
    """What an ``isinstance`` test of the types *node* names refuses in what
    passes it: a text and a complex value for real numbers, a text for
    numbers of any kind, nothing when one of the types is anything else.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _class_refusals(node.left) & _class_refusals(node.right)
    if isinstance(node, ast.Tuple):
        refused = _BOTH
        for member in node.elts:
            refused &= _class_refusals(member)
        return refused
    name = _last_name(node)
    if name in _REAL_CLASSES:
        return _BOTH
    if name in _NUMBER_CLASSES:
        return _TEXT
    return frozenset()


#: The arguments of ``isinstance(value, types)``.
_ISINSTANCE_ARGUMENTS = 2


def _narrowed(test: ast.expr, *, holds: bool) -> dict[str, frozenset[Refusal]]:
    """The names *test* finds to be numbers where it *holds* (or fails), with
    what that refuses in each: ``isinstance(x, float)`` where it holds,
    ``not isinstance(x, float)`` where it fails, each test of an ``and``
    where it holds and each test of an ``or`` where it fails.
    """
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return _narrowed(test.operand, holds=not holds)
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And) == holds:
        # Each test of an ``and`` holds where it holds, and each test of an
        # ``or`` fails where it fails.
        found: dict[str, frozenset[Refusal]] = {}
        for value in test.values:
            found.update(_narrowed(value, holds=holds))
        return found
    if (
        holds
        and isinstance(test, ast.Call)
        and isinstance(test.func, ast.Name)
        and test.func.id == "isinstance"
        and len(test.args) == _ISINSTANCE_ARGUMENTS
        and isinstance(test.args[0], ast.Name)
    ):
        refused = _class_refusals(test.args[1])
        return {test.args[0].id: refused} if refused else {}
    return {}


def _kept(call: ast.Call, names: _Names) -> list[ast.expr]:
    """The values a call that keeps them reads: its object as a method, its
    first argument as a function, every argument for ``zip`` and its kin;
    nothing for a call that keeps none, a conversion included.
    """
    callee = _last_name(call.func)
    if (
        id(call) in names.hidden
        or id(call) in names.replaced
        or converted(call, names) is not None
    ):
        return []
    if callee == "getattr" and len(call.args) == _GETATTR_WITH_DEFAULT:
        return [call.args[2]]
    if callee in _KEEPING_ALL:
        return list(call.args)
    if callee not in _KEEPING_CALLS:
        return []
    func = call.func
    if isinstance(func, ast.Attribute) and not (
        isinstance(func.value, ast.Name) and func.value.id in {"np", "numpy"}
    ):
        return [func.value]
    return call.args[:1]


def _numpy_function(call: ast.Call, names: _Names) -> bool:
    """Whether *call* is a NumPy function that keeps its argument's values,
    given no floating or complex dtype: ``np.asarray(x)``, ``np.atleast_1d(x)``
    and their kin, which read a ``bytearray`` as the codes of its characters.
    """
    if id(call) in names.hidden or id(call) in names.replaced:
        return False
    func = call.func
    through_numpy = (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in {"np", "numpy"}
    ) or (isinstance(func, ast.Name) and func.id in names.numpy)
    return (
        through_numpy
        and _last_name(func) in _KEEPING_CALLS
        and converted(call, names) is None
    )


def _operands(
    node: ast.IfExp | ast.BoolOp | ast.BinOp | ast.UnaryOp,
) -> list[ast.expr]:
    """The values *node* may hand on: both branches of a conditional
    expression, every operand of ``and`` and ``or``, and the operands of
    arithmetic, which keep a bytearray's codes numbers.
    """
    if isinstance(node, ast.BoolOp):
        return list(node.values)
    if isinstance(node, ast.IfExp):
        return [node.body, node.orelse]
    if isinstance(node, ast.BinOp):
        return [node.left, node.right]
    return [node.operand] if isinstance(node.op, _ARITHMETIC_SIGNS) else []


def _ends(block: Sequence[ast.stmt]) -> bool:
    """Whether *block* leaves the function or the loop at its end on every path."""
    if not block:
        return False
    last = block[-1]
    if isinstance(last, ast.Return | ast.Raise | ast.Continue | ast.Break):
        return True
    if isinstance(last, ast.If):
        return _ends(last.body) and _ends(last.orelse)
    return False


def _raises(block: Sequence[ast.stmt]) -> bool:
    """Whether *block* ends in a ``raise`` on every path."""
    if not block:
        return False
    last = block[-1]
    if isinstance(last, ast.Raise):
        return True
    if isinstance(last, ast.If):
        return _raises(last.body) and _raises(last.orelse)
    return False


#: The signs of arithmetic, which keep a complex value complex and a text
#: a text where they run at all; ``not`` and ``~`` are no arithmetic.
_ARITHMETIC_SIGNS = (ast.USub, ast.UAdd)

_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)


@dataclass
class _Flow:
    """A function read the way it runs, with what each name holds at each
    conversion of a value.
    """

    checks: Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]]]
    names: _Names
    fields: bool
    #: The module the function is written in, which says what a test on
    #: ``TYPE_CHECKING`` reads (:func:`ast_scan.is_type_checking_block`).
    root: ast.AST
    #: What a call of a check of the library hands back: the arguments it
    #: returns, each with what the check refused in it (:func:`_checker`);
    #: ``None`` for a call of anything else.
    handed: Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]] | None] = (
        lambda _call: None
    )
    found: dict[int, tuple[ast.Call, ast.expr, Kind, Verdict]] = field(
        default_factory=dict
    )
    breaks: list[list[Env]] = field(default_factory=list)
    #: What the names hold where each nested function is defined, and where
    #: it is used (called, handed on or returned), by the definition's id.
    defined: dict[int, list[Env]] = field(default_factory=dict)
    used: dict[int, list[Env]] = field(default_factory=dict)
    nested: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = field(
        default_factory=dict
    )
    #: Each ``lambda`` met, with what the names hold where it is written.
    lambdas: list[tuple[ast.Lambda, Env]] = field(default_factory=list)
    #: Each ``class`` written in the function, with what the names hold there.
    classes: list[tuple[ast.ClassDef, Env]] = field(default_factory=list)
    #: Told of each call with what the names hold there, so that what a
    #: private helper of the package is handed is read where it is called.
    calling: Callable[[_Flow, ast.Call, Env], None] = lambda _flow, _call, _env: None

    # What a value holds.

    def default(self, name: str) -> State:
        """What a name no binding reached holds: a field in ``__post_init__``
        the caller's value, anything else none.
        """
        return frozenset() if self.fields and name.startswith("self.") else None

    def lookup(self, env: Env, name: str) -> State:
        return env[name] if name in env else self.default(name)

    def state(self, node: ast.expr, env: Env) -> State:
        """What *node* holds: the caller's value, with its refusals, or none."""
        if isinstance(node, ast.Name):
            return self.lookup(env, node.id)
        if isinstance(node, ast.Attribute):
            return self._attribute(node, env)
        if isinstance(node, ast.Subscript):
            key = ast.unparse(node)
            return env[key] if key in env else self.state(node.value, env)
        if isinstance(node, ast.Starred | ast.NamedExpr):
            return self.state(node.value, env)
        if isinstance(node, ast.IfExp):
            return join(self.state(node.body, env), self.state(node.orelse, env))
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            return self._joined(node.elts, env)
        if isinstance(node, ast.Call):
            return self._call(node, env)
        if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp):
            inner = self._comprehension_env(node, env, record=False)
            return self.state(node.elt, inner)
        if isinstance(node, ast.BinOp):
            return join(self.state(node.left, env), self.state(node.right, env))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ARITHMETIC_SIGNS):
            return self.state(node.operand, env)
        return None

    def _attribute(self, node: ast.Attribute, env: Env) -> State:
        if self.fields and isinstance(node.value, ast.Name) and node.value.id == "self":
            return self.lookup(env, f"self.{node.attr}")
        if node.attr in _KEEPING_ATTRIBUTES:
            return self.state(node.value, env)
        return None

    def _joined(self, nodes: Iterable[ast.expr], env: Env) -> State:
        state: State = None
        for node in nodes:
            state = join(state, self.state(node, env))
        return state

    def _call(self, call: ast.Call, env: Env) -> State:
        handed = self.handed(call)
        if handed is not None:
            # A check of the library hands back what it returns of its
            # arguments, checked as far as it checked them: a parameter it
            # never checked comes back the caller's value as it was.
            state: State = None
            for argument, refused in handed:
                held = self.state(argument, env)
                state = join(state, None if held is None else held | refused)
            return state
        read = self.checks(call)
        if read:
            refusals: frozenset[Refusal] = frozenset()
            for _, refused in read:
                refusals |= refused
            return refusals
        return self._joined(_kept(call, self.names), env)

    def names_read(self, node: ast.expr) -> list[str]:
        """The names *node* holds the value of as it is on every path, as a
        check reads them: of a conditional expression, those both of its
        branches hold (see :meth:`_branches_read`).
        """
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.Attribute):
            return self._attribute_names(node)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            return [ast.unparse(node)]
        if isinstance(node, ast.IfExp):
            return self._branches_read(node)
        if _or_a_number(node):
            return self.names_read(node.values[0])
        return [name for part in self._parts(node) for name in self.names_read(part)]

    def _branches_read(self, node: ast.IfExp) -> list[str]:
        """The names both branches of *node* hold, and the name its test finds
        ``None`` (``d if x is None else x``) when the branch that runs while
        it is not holds it: the other runs on no caller's number.
        """
        body = self.names_read(node.body)
        orelse = self.names_read(node.orelse)
        found = [name for name in body if name in orelse]
        name, when_none = _none_test(node.test)
        valued = orelse if when_none else body
        if name is not None and name in valued and name not in found:
            found.append(name)
        return found

    def _attribute_names(self, node: ast.Attribute) -> list[str]:
        if self.fields and isinstance(node.value, ast.Name) and node.value.id == "self":
            return [f"self.{node.attr}"]
        return self.names_read(node.value) if node.attr in _KEEPING_ATTRIBUTES else []

    def _parts(self, node: ast.expr) -> list[ast.expr]:
        """The parts of *node* that hold its value as they are on every path:
        none of ``getattr``, whose default is read only when the attribute is
        missing.
        """
        if isinstance(node, ast.Starred | ast.NamedExpr):
            return [node.value]
        if isinstance(node, ast.Tuple | ast.List):
            return list(node.elts)
        if isinstance(node, ast.Call) and _last_name(node.func) != "getattr":
            return _kept(node, self.names)
        return []

    # Bindings and checks.

    def bind(
        self,
        target: ast.expr,
        value: ast.expr | None,
        state: State,
        env: Env,
        *,
        read: bool | None = None,
    ) -> None:
        """Bind *target* to *value*, which holds *state*, member by member
        where both are tuples of the same length; mark each name bound to
        NumPy's reading of a caller's value (*read*, else read off *value*).
        """
        if (
            isinstance(target, ast.Tuple | ast.List)
            and isinstance(value, ast.Tuple | ast.List)
            and len(target.elts) == len(value.elts)
            and not any(isinstance(e, ast.Starred) for e in (*target.elts, *value.elts))
        ):
            for inner, item in zip(target.elts, value.elts, strict=True):
                self.bind(inner, item, self.state(item, env), env)
            return
        if self.fields and isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name) and target.value.id == "self":
                env[f"self.{target.attr}"] = state
            return
        if isinstance(target, ast.Subscript):
            self._bind_item(target, state, env)
            return
        if read is None:
            read = value is not None and self._numpy_reading(value, env)
        for name in _targets(target):
            self._set(env, name, state)
            if read:
                env[_numpy_key(name)] = frozenset()

    def _bind_item(self, target: ast.Subscript, state: State, env: Env) -> None:
        """``x[i] = value``: the item holds *state* from here on, and *x*, a
        caller's value, holds it among its items, so what a check made of *x*
        as a whole holds only as far as *value* was checked too.
        """
        names = [name for name in self.names_read(target.value) if "[" not in name]
        if not names:
            return
        env[ast.unparse(target)] = state
        for name in names:
            held = self.lookup(env, name)
            if held is not None:
                env[name] = join(held, state)

    @staticmethod
    def _set(env: Env, name: str, state: State) -> None:
        for key in [k for k in env if k.startswith(f"{name}[")]:
            del env[key]
        env[name] = state

    def check(self, call: ast.Call, env: Env) -> None:
        """Add to what each argument *call* checks holds the refusals it makes."""
        for argument, refused in self.checks(call):
            for name in self.names_read(argument):
                held = (
                    self.lookup(env, name)
                    if "[" not in name
                    else self.state(argument, env)
                )
                if held is not None:
                    env[name] = held | refused

    # Expressions.

    def expression(self, node: ast.AST, env: Env, *, sure: bool = True) -> None:
        """Read *node* in the order it runs: record each conversion with what
        its value holds, and, where it surely runs, each check and binding.
        """
        if self._scope(node, env):
            return
        if isinstance(node, ast.IfExp):
            self.expression(node.test, env, sure=sure)
            self.expression(
                node.body, self.narrowed(node.test, env, holds=True), sure=False
            )
            self.expression(
                node.orelse, self.narrowed(node.test, env, holds=False), sure=False
            )
        elif isinstance(node, ast.BoolOp):
            self.expression(node.values[0], env, sure=sure)
            for value in node.values[1:]:
                self.expression(value, env, sure=False)
        elif isinstance(node, ast.Compare) and len(node.comparators) > 1:
            # A chained comparison stops at the first link that fails.
            self.expression(node.left, env, sure=sure)
            self.expression(node.comparators[0], env, sure=sure)
            for comparator in node.comparators[1:]:
                self.expression(comparator, env, sure=False)
        elif isinstance(node, _COMPREHENSIONS):
            self._comprehension_env(node, env, record=True)
        elif isinstance(node, ast.NamedExpr):
            self.expression(node.value, env, sure=sure)
            self._walrus(node, env, sure=sure)
        else:
            for child in ast.iter_child_nodes(node):
                self.expression(child, env, sure=sure)
            if isinstance(node, ast.Call):
                self._at_call(node, env, sure=sure)

    def _walrus(self, node: ast.NamedExpr, env: Env, *, sure: bool) -> None:
        """Bind the target of a ``:=``, which, where it may not run, may
        still hold what it held before.
        """
        name = node.target.id
        state = self.state(node.value, env)
        read = self._numpy_reading(node.value, env)
        if not sure:
            state = join(state, self.lookup(env, name))
            read = read or self._numpy_reading(node.target, env)
        self.bind(node.target, None, state, env, read=read)

    def _scope(self, node: ast.AST, env: Env) -> bool:
        """Keep what the names hold at a ``lambda`` or at a use of a nested
        function; whether *node* is a scope of its own, read apart.
        """
        if isinstance(node, ast.Lambda):
            self.lambdas.append((node, dict(env)))
        elif isinstance(node, ast.Name) and node.id in self.nested:
            self.used.setdefault(id(self.nested[node.id]), []).append(dict(env))
        return isinstance(node, _SCOPES)

    def _at_call(self, call: ast.Call, env: Env, *, sure: bool) -> None:
        self.calling(self, call, env)
        if (found := converted(call, self.names)) is not None:
            value, kind = found
            self._record(call, value, kind, self._verdict(value, kind, env))
            return
        for argument, refused in self.checks(call):
            # A check handed NumPy's reading of the value reads a bytearray's
            # codes as numbers: the reading is a conversion no check precedes.
            if "text" in refused and self._numpy_reading(argument, env):
                read: Kind = "real" if "complex" in refused else "complex"
                self._record(call, argument, read, "unchecked")
        if sure:
            self.check(call, env)

    def _numpy_reading(self, node: ast.expr, env: Env) -> bool:
        """Whether *node* may be what NumPy made of a caller's value no check
        has refused a text in (``np.asarray(x)``, ``np.atleast_1d(x)`` and the
        other NumPy calls that keep its values), or a name bound to it on a
        path that reaches here, on either side of a conditional expression,
        an ``and`` or an ``or``.
        """
        if isinstance(node, ast.Name):
            return _numpy_key(node.id) in env
        if isinstance(node, ast.NamedExpr):
            return self._numpy_reading(node.value, env)
        if isinstance(node, ast.IfExp | ast.BoolOp | ast.BinOp | ast.UnaryOp):
            return any(self._numpy_reading(part, env) for part in _operands(node))
        if not isinstance(node, ast.Call) or not _numpy_function(node, self.names):
            return False
        state = self._joined(_kept(node, self.names), env)
        return state is not None and "text" not in state

    def _verdict(self, value: ast.expr, kind: Kind, env: Env) -> Verdict:
        state = self.state(value, env)
        if state is not None:
            return "checked" if NEEDS[kind] <= state else "unchecked"
        return "field" if self._reads_field(value) else "computed"

    def _reads_field(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Attribute):
            return isinstance(node.value, ast.Name) and node.value.id == "self"
        if isinstance(node, ast.Subscript | ast.Starred):
            return self._reads_field(node.value)
        if isinstance(node, ast.Call):
            return any(self._reads_field(item) for item in _kept(node, self.names))
        return False

    def _record(
        self, call: ast.Call, value: ast.expr, kind: Kind, verdict: Verdict
    ) -> None:
        previous = self.found.get(id(call))
        if previous is None or _SEVERITY[verdict] > _SEVERITY[previous[3]]:
            self.found[id(call)] = (call, value, kind, verdict)

    def _comprehension_env(
        self,
        node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp,
        env: Env,
        *,
        record: bool,
    ) -> Env:
        """The names a comprehension's loops bind, over *env*; with *record*,
        its parts read as well, none of which surely runs.
        """
        inner = dict(env)
        for number, generator in enumerate(node.generators):
            if record:
                self.expression(generator.iter, inner, sure=number == 0)
            self.bind(
                generator.target,
                None,
                self.state(generator.iter, inner),
                inner,
                read=self._numpy_reading(generator.iter, inner),
            )
            for condition in generator.ifs if record else ():
                self.expression(condition, inner, sure=False)
        if record:
            parts = (
                (node.key, node.value)
                if isinstance(node, ast.DictComp)
                else (node.elt,)
            )
            for part in parts:
                self.expression(part, inner, sure=False)
        return inner

    # Statements.

    def block(self, statements: Sequence[ast.stmt], env: Env) -> tuple[Env, bool]:
        """Read *statements* from *env*: what each name holds at the end, and
        whether every path leaves before it.
        """
        for statement in statements:
            env, ends = self.statement(statement, env)
            if ends:
                return env, True
        return env, False

    def statement(self, node: ast.stmt, env: Env) -> tuple[Env, bool]:
        handler = _STATEMENTS.get(type(node))
        if handler is not None:
            return handler(self, node, env)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            self.nested[node.name] = node
            self.defined.setdefault(id(node), []).append(dict(env))
            return env, False
        if isinstance(node, ast.ClassDef):
            self.classes.append((node, dict(env)))
            return env, False
        if isinstance(node, _SCOPES):
            return env, False
        for child in ast.iter_child_nodes(node):
            self.expression(child, env)
        return env, isinstance(node, ast.Return | ast.Raise | ast.Continue)

    def narrowed(self, test: ast.expr, env: Env, *, holds: bool) -> Env:
        """A copy of *env* where *test* holds (or fails): each caller's value
        an ``isinstance`` test finds to be a number holds what it refuses
        (:func:`_narrowed`).
        """
        inner = dict(env)
        for name, refused in _narrowed(test, holds=holds).items():
            held = self.lookup(inner, name)
            if held is not None:
                inner[name] = held | refused
        return inner

    def _assign(
        self, node: ast.Assign | ast.AnnAssign | ast.AugAssign, env: Env
    ) -> tuple[Env, bool]:
        if node.value is None:
            return env, False
        self.expression(node.value, env)
        if isinstance(node, ast.AugAssign):
            self._augment(node, env)
            return env, False
        state = self.state(node.value, env)
        read = self._numpy_reading(node.value, env)
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            self.bind(target, node.value, state, env, read=read)
        return env, False

    def _augment(self, node: ast.AugAssign, env: Env) -> None:
        """``x += y``: *x* holds what arithmetic on both holds, a caller's
        value when either is one, with only the refusals both made.
        """
        target = node.target
        state = join(self.state(target, env), self.state(node.value, env))
        if isinstance(target, ast.Name):
            env[target.id] = state
        elif isinstance(target, ast.Subscript):
            self._bind_item(target, state, env)
        elif self.fields and self._reads_field(target):
            env[f"self.{target.attr}"] = state

    def _if(self, node: ast.If, env: Env) -> tuple[Env, bool]:
        if is_type_checking_block(node, self.root):
            # One branch never runs, and the other always does.
            return self.block(what_runs(node), env)
        self.expression(node.test, env)
        body, body_ends = self.block(
            node.body, self.narrowed(node.test, env, holds=True)
        )
        other, other_ends = self.block(
            node.orelse, self.narrowed(node.test, env, holds=False)
        )
        reached = [
            e for e, ends in ((body, body_ends), (other, other_ends)) if not ends
        ]
        if not reached:
            return env, True
        return _join_envs(reached, self.default), False

    def _loop(
        self, node: ast.For | ast.AsyncFor | ast.While, env: Env
    ) -> tuple[Env, bool]:
        """A loop's body may run any number of times, none included: it is
        read twice, the second time from what the first left joined with
        what came in, and what follows sees every way out.
        """
        head = dict(env)
        if isinstance(node, ast.While):
            self.expression(node.test, head)
        else:
            self.expression(node.iter, head)
        self.breaks.append([])
        entry = head
        for _ in range(2):
            inner = dict(entry)
            if not isinstance(node, ast.While):
                read = self._numpy_reading(node.iter, inner)
                state = self.state(node.iter, inner)
                self.bind(node.target, None, state, inner, read=read)
            end, _ = self.block(node.body, inner)
            entry = _join_envs([head, end], self.default)
        breaks = self.breaks.pop()
        after, ends = self.block(node.orelse, entry)
        reached = [*([] if ends else [after]), *breaks]
        if not reached:
            return after, True
        return _join_envs(reached, self.default), False

    def captured(
        self, function: ast.FunctionDef | ast.AsyncFunctionDef, end: Env
    ) -> Env:
        """What the names a nested *function* shares with this one hold for
        it: where it is used, or, used nowhere here, where it is defined,
        joined with what they hold at the end of this one, *end*, after which
        a closure handed out may still be called.
        """
        envs = self.used.get(id(function)) or self.defined.get(id(function), [])
        return _join_envs([*envs, end], self.default)

    def _assert(self, node: ast.Assert, env: Env) -> tuple[Env, bool]:
        """Read an ``assert``, which ``python -O`` leaves out: a conversion in
        it is a conversion, but no check or binding in it holds after it.
        """
        self.expression(node.test, env, sure=False)
        if node.msg is not None:
            self.expression(node.msg, env, sure=False)
        return env, False

    def _break(self, node: ast.Break, env: Env) -> tuple[Env, bool]:
        del node
        if self.breaks:
            self.breaks[-1].append(dict(env))
        return env, True

    def _with(self, node: ast.With | ast.AsyncWith, env: Env) -> tuple[Env, bool]:
        for item in node.items:
            self.expression(item.context_expr, env)
            if item.optional_vars is not None:
                state = self.state(item.context_expr, env)
                read = self._numpy_reading(item.context_expr, env)
                self.bind(item.optional_vars, None, state, env, read=read)
        return self.block(node.body, env)

    def _try(self, node: ast.Try | ast.TryStar, env: Env) -> tuple[Env, bool]:
        start = dict(env)
        body, body_ends = self.block(node.body, dict(env))
        caught = _join_envs([start, body], self.default)
        reached: list[Env] = []
        for handler in node.handlers:
            inner, ends = self.block(handler.body, dict(caught))
            if not ends:
                reached.append(inner)
        if not body_ends:
            other, other_ends = self.block(node.orelse, body)
            if not other_ends:
                reached.append(other)
        if not reached:
            final, _ = self.block(node.finalbody, caught)
            return final, True
        return self.block(node.finalbody, _join_envs(reached, self.default))

    def _match(self, node: ast.Match, env: Env) -> tuple[Env, bool]:
        self.expression(node.subject, env)
        subject = self.state(node.subject, env)
        read = self._numpy_reading(node.subject, env)
        reached: list[Env] = []
        for case in node.cases:
            inner = self._bind_captures(case, dict(env), subject, read=read)
            if case.guard is not None:
                self.expression(case.guard, inner)
            end, ends = self.block(case.body, inner)
            if not ends:
                reached.append(end)
        last = node.cases[-1].pattern if node.cases else None
        if not (isinstance(last, ast.MatchAs) and last.pattern is None):
            reached.append(env)
        if not reached:
            return env, True
        return _join_envs(reached, self.default), False

    def _bind_captures(
        self, case: ast.match_case, inner: Env, subject: State, *, read: bool
    ) -> Env:
        """*inner* with each name the pattern of *case* captures bound.

        Each is bound to *subject*, and to NumPy's reading of it where the
        subject is one (*read*).
        """
        for capture in ast.walk(case.pattern):
            name = getattr(capture, "name", None)
            if isinstance(name, str):
                self._set(inner, name, subject)
                if read:
                    inner[_numpy_key(name)] = frozenset()
        return inner


_STATEMENTS: dict[type[ast.stmt], Callable[[_Flow, Any, Env], tuple[Env, bool]]] = {
    ast.Assign: _Flow._assign,
    ast.AnnAssign: _Flow._assign,
    ast.AugAssign: _Flow._assign,
    ast.If: _Flow._if,
    ast.For: _Flow._loop,
    ast.AsyncFor: _Flow._loop,
    ast.While: _Flow._loop,
    ast.Break: _Flow._break,
    ast.Assert: _Flow._assert,
    ast.With: _Flow._with,
    ast.AsyncWith: _Flow._with,
    ast.Try: _Flow._try,
    ast.TryStar: _Flow._try,
    ast.Match: _Flow._match,
}


def _functions(
    tree: ast.AST, scope: str = ""
) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Every function and method of *tree*, with its qualified name."""
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            inner = f"{scope}.{child.name}" if scope else child.name
            if not isinstance(child, ast.ClassDef):
                yield inner, child
            yield from _functions(child, inner)
        else:
            yield from _functions(child, scope)


def _module_name(path: pathlib.Path) -> str:
    """The dotted name of a module of the library, from its path."""
    parts = list(path.with_suffix("").parts)
    start = len(parts) - 1 - parts[::-1].index(PACKAGE)
    dotted = parts[start:]
    if dotted[-1] == "__init__":
        dotted = dotted[:-1]
    return ".".join(dotted)


def _imports(tree: ast.Module, module: str, *, is_package: bool) -> dict[str, str]:
    """``{name: "module.name"}`` for each ``from`` import of the module, but
    one an ``if TYPE_CHECKING:`` block holds, which never runs, and one anything
    else the module binds the name to may stand for: a later ``def`` or
    assignment, the other branch of a ``try``, a function that binds it under
    ``global`` (:func:`ast_scan.standing_bindings`). The name is then the
    module's own, and no check or NumPy function it imported, unless a function
    or a class body imports it for itself: the table then holds that import,
    and a call that finds the module's binding reaches none (:func:`_reach`).
    """
    package = module if is_package else module.rpartition(".")[0]
    checker = for_the_type_checker(tree)
    standing = standing_bindings(tree, checker)
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or id(node) in checker:
            continue
        if node.level:
            parts = package.split(".")
            base = parts[: len(parts) - (node.level - 1)]
            source = ".".join([*base, *([node.module] if node.module else [])])
        else:
            source = node.module or ""
        for alias in node.names:
            found[alias.asname or alias.name] = f"{source}.{alias.name}"
    own_imports = {
        name
        for scope in ast.walk(tree)
        if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        for name in own_names(scope).imported - own_names(scope).declared_global
    }
    return {
        name: dotted
        for name, dotted in found.items()
        if name in own_imports
        or all(isinstance(bound, ast.ImportFrom) for bound in standing.get(name, ()))
    }


def _numpy_names(tree: ast.Module, imports: Mapping[str, str]) -> _Names:
    """How the module of *tree* spells NumPy's constructors and dtypes."""
    numpy = frozenset(
        name for name, dotted in imports.items() if dotted.startswith("numpy.")
    )
    plain = _Names(numpy)
    hidden, replaced = _calls_by_what_they_reach(tree, imports)
    return _Names(numpy, _dtype_names(tree.body, plain), hidden, replaced)


def _calls_by_what_they_reach(
    tree: ast.Module, imports: Mapping[str, str]
) -> tuple[frozenset[int], frozenset[int]]:
    """Each call of *tree*, by its id, that reaches no function of its spelling.

    First those whose callee is a name, or an attribute of a name the module
    imports with ``from``, that a scope inside the module binds nearer than the
    module does: a parameter, a local, a comprehension's variable, a nested
    function. A plain import's name is hidden by a comprehension's variable and a
    lambda's parameter alone: a parameter spelt ``np`` is the module handed in,
    and a lambda's is a parameter too. A scope's own import is read as the
    module's (:func:`_imports`).

    Then those of a name read by its spelling (:data:`_READ_BY_SPELLING`) that
    the module's own binding replaces (:func:`_reach`).
    """
    checker = for_the_type_checker(tree)
    standing = standing_bindings(tree, checker)
    plain = {
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import) and id(node) not in checker
        for name in imported_names(node)
    }
    hidden: set[int] = set()
    replaced: set[int] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        head = call.func
        while isinstance(head, ast.Attribute):
            head = head.value
        if not isinstance(head, ast.Name):
            continue
        name = head.id
        bare = head is call.func
        if (
            not bare
            and name not in imports
            and (name not in plain or not _names_its_own_module(tree, head))
        ):
            continue
        reached = _reach(tree, head, name, standing, imports)
        if reached == "nearer":
            hidden.add(id(call))
        elif reached == "replaced" and bare:
            replaced.add(id(call))
    return frozenset(hidden), frozenset(replaced)


def _names_its_own_module(tree: ast.Module, read: ast.Name) -> bool:
    """Whether a comprehension's variable or a lambda's parameter is what *read*
    finds, which stands for nothing the module imports; a lambda's parameter
    spelt as NumPy is the module handed in, as a function's is.
    """
    binder = binding_of(tree, read, read.id)[1]
    if isinstance(binder, ast.Lambda):
        return read.id not in {"np", "numpy"}
    return isinstance(binder, _COMPREHENSIONS)


#: The names a call is read by the spelling of: the builtins that convert, and
#: the calls that keep their values.
_READ_BY_SPELLING = (
    frozenset(_BUILTIN_SCALARS) | _KEEPING_ALL | _KEEPING_CALLS | {"getattr"}
)


def _reach(
    tree: ast.Module,
    read: ast.expr,
    name: str,
    standing: Mapping[str, Sequence[ast.AST]],
    imports: Mapping[str, str],
) -> Literal["nearer", "replaced", "spelt"]:
    """What *name*, read at *read*, reaches.

    ``"nearer"`` when a scope inside the module binds it to anything but what the
    spelling names; a parameter defaulting to that and a local assigned from it
    (``float=float``, ``asarray = np.asarray``) hide nothing, and a default of the
    name itself is read where the ``def`` runs its defaults. ``"nearer"`` too when
    the read finds a binding of the module that replaces its imports, while
    *imports* holds a function's own import of the name, which this read does not
    reach. ``"replaced"`` when the module's own bindings of a name read by its
    spelling, those that may stand once it has run, hold nothing of that spelling.
    ``"spelt"`` otherwise.
    """
    how, binder = binding_of(tree, read, name)
    if binder is None or binder is tree:
        live = standing.get(name, ())
        if name in imports and not all(
            isinstance(node, ast.ImportFrom) for node in live
        ):
            return "nearer"
        replaced = (
            name in _READ_BY_SPELLING
            and bool(live)
            and all(_replaces_the_spelling(tree, node, name) for node in live)
        )
        return "replaced" if replaced else "spelt"
    if how == "import":
        return "spelt"
    values = values_bound(tree, binder, name)
    if not values or not all(spells(value, name) for value in values):
        return "nearer"
    for value in values:
        if (
            isinstance(value, ast.Name)
            and binding_of(tree, value, name)[1] is not binder
        ):
            reached = _reach(tree, value, name, standing, imports)
            if reached != "spelt":
                return reached
    return "spelt"


def _replaces_the_spelling(tree: ast.Module, node: ast.AST, name: str) -> bool:
    """Whether *node*, a binding of *name* the module may hold, holds anything but
    what the spelling names.

    Any ``def``, ``class`` and other binding does, and an assignment of anything
    else. An import of a builtin's name does unless it comes from ``builtins`` or
    NumPy; any other import is read by its spelling as it always was, since what
    keeps a value may well be imported from anywhere.
    """
    if isinstance(node, ast.ImportFrom):
        source = "" if node.level else (node.module or "").partition(".")[0]
        return name in _BUILTIN_SCALARS and source not in {"builtins", "numpy"}
    if isinstance(node, ast.Import):
        return name in _BUILTIN_SCALARS
    return not spells(assigned_value(tree, node), name)


@dataclass(frozen=True, eq=False)
class _Module:
    """A module of the library, parsed, with what its imports bind."""

    path: pathlib.Path
    name: str
    tree: ast.Module
    imports: dict[str, str]
    numpy: _Names


def _module(path: pathlib.Path) -> _Module:
    tree = empty_type_checking_bodies(
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    )
    name = _module_name(path)
    imports = _imports(tree, name, is_package=path.stem == "__init__")
    return _Module(path, name, tree, imports, _numpy_names(tree, imports))


def _returns(node: ast.AST) -> bool:
    """Whether *node* holds a ``return`` of the function it runs in."""
    if isinstance(node, ast.Return):
        return True
    if isinstance(node, _SCOPES):
        return False
    return any(_returns(child) for child in ast.iter_child_nodes(node))


def _swallows(node: ast.Try | ast.TryStar) -> bool:
    """Whether a handler of *node* can take an exception and go on, so that a
    check in its body that raised leaves no refusal behind.
    """
    return not all(_raises(handler.body) for handler in node.handlers)


class _Sure:
    """The calls of a function's body that run on every path that leaves it
    by its end or a ``return``, each with the names bound before it.

    A ``return`` ends what is sure: what follows it in the source runs on the
    other paths only. A call in the body of a ``try`` whose handler can take
    the exception and go on may have raised for nothing, and a call in a
    loop's body or a ``match`` case may not run, nor one in an ``assert``,
    which ``python -O`` leaves out. A name bound before a call
    holds what it was bound to there, and no longer the caller's value,
    unless it was bound to what keeps that value (``x = np.atleast_1d(x)``).
    """

    def __init__(self, reader: _Flow) -> None:
        self.reader = reader
        self.bound: set[str] = set()
        self.found: list[tuple[ast.Call, frozenset[str]]] = []

    def block(self, statements: Sequence[ast.stmt], *, sure: bool) -> None:
        for statement in statements:
            self.statement(statement, sure=sure)
            self.bound |= self._binds(statement)
            sure = sure and not _returns(statement)

    def statement(self, node: ast.stmt, *, sure: bool) -> None:
        if isinstance(node, ast.If) and is_type_checking_block(node, self.reader.root):
            # One branch never runs, and the other always does.
            self.block(what_runs(node), sure=sure)
        elif isinstance(node, ast.If):
            self.calls(node.test, sure=sure)
            self.block(node.body, sure=sure and _raises(node.orelse))
            self.block(node.orelse, sure=sure and _raises(node.body))
        elif isinstance(node, ast.Try | ast.TryStar):
            kept = sure and not _swallows(node)
            self.block(node.body, sure=kept)
            self.block(node.orelse, sure=kept)
            self.block(node.finalbody, sure=sure)
        elif isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                self.calls(item.context_expr, sure=sure)
            self.block(node.body, sure=sure)
        elif isinstance(node, ast.For | ast.AsyncFor | ast.While | ast.Match):
            self.calls(_header(node), sure=sure)
        elif not isinstance(node, (*_SCOPES, ast.Assert)):
            # ``python -O`` leaves an ``assert`` out, and a call in it with it.
            for child in ast.iter_child_nodes(node):
                self.calls(child, sure=sure)

    def calls(self, node: ast.AST, *, sure: bool) -> None:
        """Keep the calls of *node* that surely run, with the names bound so far."""
        if not sure:
            return
        bound = frozenset(self.bound)
        self.found.extend(
            (call, bound) for call, runs in _expression_calls(node, sure=True) if runs
        )

    def _binds(self, node: ast.stmt) -> set[str]:
        """The names *node* binds in its function, but a name bound to what
        keeps the value it held.
        """
        if (
            isinstance(node, ast.Assign | ast.AnnAssign)
            and node.value is not None
            and len(targets := _assigned(node)) == 1
            and isinstance(targets[0], ast.Name)
            and targets[0].id in self.reader.names_read(node.value)
        ):
            return set()
        return _bound_names(node)


def _assigned(node: ast.Assign | ast.AnnAssign) -> list[ast.expr]:
    return node.targets if isinstance(node, ast.Assign) else [node.target]


def _filled(target: ast.expr) -> list[str]:
    """The names an assignment to *target* puts a value inside: ``x`` for
    ``x[i] = y`` and ``x[i][j] += y``, which holds *y* among its items, as
    :meth:`_Flow._bind_item` reads it; each of a tuple's or a list's items
    alike.
    """
    if isinstance(target, ast.Tuple | ast.List):
        return [name for item in target.elts for name in _filled(item)]
    if isinstance(target, ast.Starred):
        return _filled(target.value)
    if not isinstance(target, ast.Subscript):
        return []
    owner: ast.expr = target
    while isinstance(owner, ast.Subscript):
        owner = owner.value
    return [owner.id] if isinstance(owner, ast.Name) else []


def _header(node: ast.For | ast.AsyncFor | ast.While | ast.Match) -> ast.expr:
    """The part of a loop or a ``match`` that surely runs."""
    if isinstance(node, ast.While):
        return node.test
    if isinstance(node, ast.Match):
        return node.subject
    return node.iter


def _bound_names(node: ast.AST) -> set[str]:
    """The names *node* binds in the scope it runs in: an assignment's, a
    loop's, a ``with``'s and a handler's targets, a ``match``'s captures and a
    nested definition's name, but not what a nested scope or a comprehension
    binds of its own.
    """
    found: set[str] = set()
    pending: list[ast.AST] = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, ast.Name) and not isinstance(current.ctx, ast.Load):
            found.add(current.id)
        elif isinstance(current, ast.alias):
            found.add((current.asname or current.name).partition(".")[0])
        elif isinstance(name := getattr(current, "name", None), str):
            found.add(name)
        if not isinstance(current, (*_SCOPES, *_COMPREHENSIONS)):
            pending.extend(ast.iter_child_nodes(current))
    return found


def _nested_calls(node: ast.AST) -> Iterator[tuple[ast.Call, bool]]:
    """Each call under *node*, none of which surely runs."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            yield child, False


def _sure_parts(node: ast.expr) -> list[ast.expr] | None:
    """The parts of a conditional expression that surely run: the test of an
    ``if`` expression, the first operand of ``and`` and ``or``, the first link
    of a chained comparison, the first iterable of a comprehension; ``None``
    for an expression that runs whole.
    """
    if isinstance(node, ast.IfExp):
        return [node.test]
    if isinstance(node, ast.BoolOp):
        return [node.values[0]]
    if isinstance(node, ast.Compare) and len(node.comparators) > 1:
        return [node.left, node.comparators[0]]
    if isinstance(node, _COMPREHENSIONS):
        return [node.generators[0].iter]
    return None


def _expression_calls(node: ast.AST, *, sure: bool) -> Iterator[tuple[ast.Call, bool]]:
    if isinstance(node, _SCOPES):
        return
    sure_parts = _sure_parts(node) if isinstance(node, ast.expr) else None
    if sure_parts is not None:
        for part in sure_parts:
            yield from _expression_calls(part, sure=sure)
        for call, _ in _nested_calls(node):
            if not any(_within(call, part) for part in sure_parts):
                yield call, False
        return
    for child in ast.iter_child_nodes(node):
        yield from _expression_calls(child, sure=sure)
    if isinstance(node, ast.Call):
        yield node, sure


def _within(node: ast.AST, outer: ast.AST) -> bool:
    return any(child is node for child in ast.walk(outer))


@dataclass(frozen=True)
class _Call:
    """A call a function makes by a plain name on every path, kept without its tree.

    The function it reaches, by the module that defines it, and the names
    each argument is read from: in order for the positional ones, by keyword
    for the rest.
    """

    target: str
    positional: tuple[frozenset[str], ...]
    keywords: tuple[tuple[str | None, frozenset[str]], ...]


@dataclass(frozen=True)
class _Signature:
    """What the search for the checks of the package needs of one function.

    With what its ``return`` statements hand back of its parameters: those
    returned as the caller gave them (*returned*), and the calls of the
    library whose result is returned (*returned_calls*), each with the
    parameters its arguments are read from (:func:`_returns_of`).
    """

    dotted: str
    positional: tuple[str, ...]
    parameters: frozenset[str]
    calls: tuple[_Call, ...]
    returned: Provenance = field(default_factory=dict)
    returned_calls: tuple[_Handing, ...] = ()


def _signatures(module: _Module) -> list[_Signature]:
    """The functions at the top of *module*, each without its tree.

    A method is called through an object the rule does not follow, so only
    a function at the top of a module can be a check of its own; and only a
    call that runs on every path that leaves it by its end or a ``return``,
    and is not in the body of a ``try`` a handler of which goes on, makes it
    one, of a parameter the call reads before anything rebinds it.
    """
    reader = _Flow(lambda _: [], module.numpy, fields=False, root=module.tree)
    found = []
    for node in module.tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        sure = _Sure(reader)
        sure.block(node.body, sure=True)
        calls = tuple(
            _Call(
                module.imports.get(call.func.id, f"{module.name}.{call.func.id}"),
                tuple(_held(reader, a, bound) for a in call.args),
                tuple((k.arg, _held(reader, k.value, bound)) for k in call.keywords),
            )
            for call, bound in sure.found
            if isinstance(call.func, ast.Name) and id(call) not in module.numpy.hidden
        )
        arguments = node.args
        positional = tuple(a.arg for a in arguments.posonlyargs + arguments.args)
        parameters = frozenset(_parameters(node))
        returned, returned_calls = _Returns(module, node, parameters).read()
        found.append(
            _Signature(
                f"{module.name}.{node.name}",
                positional,
                parameters,
                calls,
                returned,
                returned_calls,
            )
        )
    return found


def _private(name: str) -> bool:
    """Whether *name* is a private one: a leading underscore, and no dunder."""
    return name.startswith("_") and not name.startswith("__")


def _dotted(module: _Module, node: ast.AST) -> str | None:
    """The function of the package *node* names in *module*: a name, by what
    the module imports or defines, or an attribute of a module it imports;
    ``None`` for anything else.
    """
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        return module.imports.get(node.id, f"{module.name}.{node.id}")
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in module.imports
    ):
        return f"{module.imports[node.value.id]}.{node.attr}"
    return None


@dataclass(frozen=True)
class _Helper:
    """A function at the top of a module of the package that no caller of the
    library reaches, which every module that names it calls: what it is
    handed is read where it is called, and its parameters hold that, not a
    caller's value of their own.
    """

    path: pathlib.Path
    positional: tuple[str, ...]
    keywords: frozenset[str]
    vararg: str | None
    kwarg: str | None

    def handed(
        self, call: ast.Call, state_of: Callable[[ast.expr], State]
    ) -> Iterator[tuple[str, State]]:
        """Each parameter *call* hands a value, with what the value holds; an
        unpacked argument may reach any parameter from its place on.
        """
        spread: tuple[str, ...] | None = None
        for place, argument in enumerate(call.args):
            if isinstance(argument, ast.Starred) and spread is None:
                spread = self.positional[place:] + tuple(filter(None, [self.vararg]))
            value = argument.value if isinstance(argument, ast.Starred) else argument
            if spread is not None:
                yield from ((name, state_of(value)) for name in spread)
            elif place < len(self.positional):
                yield self.positional[place], state_of(value)
            elif self.vararg is not None:
                yield self.vararg, state_of(value)
        for keyword in call.keywords:
            yield from self._keyword(keyword, state_of(keyword.value))

    def _keyword(
        self, keyword: ast.keyword, state: State
    ) -> Iterator[tuple[str, State]]:
        if keyword.arg is None:
            for name in (*sorted(self.keywords), *filter(None, [self.kwarg])):
                yield name, state
        elif keyword.arg in self.keywords:
            yield keyword.arg, state
        elif self.kwarg is not None:
            yield self.kwarg, state


def _published(module: _Module) -> set[str]:
    """The functions *module* publishes in its ``__all__``, its own or those it
    imports, by the name the package knows them by.
    """
    found: set[str] = set()
    for node in module.tree.body:
        for name in _all_names(node):
            found.add(module.imports.get(name, f"{module.name}.{name}"))
    return found


def _all_names(node: ast.stmt) -> list[str]:
    """The names *node* writes into ``__all__``, when it is an assignment to it."""
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign | ast.AugAssign):
        targets = [node.target]
    else:
        return []
    value = node.value
    if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets) or (
        not isinstance(value, ast.List | ast.Tuple)
    ):
        return []
    return [
        item.value
        for item in value.elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    ]


def _helpers(module: _Module) -> tuple[dict[str, _Helper], set[str]]:
    """The functions at the top of *module* no caller of the library reaches,
    by the name the package knows them by, and every function of the package
    *module* names other than by calling it (handed on, kept in a table,
    decorated with) or publishes, whose parameters a call cannot be read for.

    A function no caller reaches is a private one, or one of a private module
    (a name of its path opens with an underscore); one that a module
    publishes in its ``__all__`` is reached all the same.
    """
    inner = any(_private(part) for part in module.name.split("."))
    defined: dict[str, _Helper] = {}
    for node in module.tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and (
            inner or _private(node.name)
        ):
            arguments = node.args
            defined[f"{module.name}.{node.name}"] = _Helper(
                module.path,
                tuple(a.arg for a in arguments.posonlyargs + arguments.args),
                frozenset(a.arg for a in arguments.args + arguments.kwonlyargs),
                arguments.vararg.arg if arguments.vararg else None,
                arguments.kwarg.arg if arguments.kwarg else None,
            )
    called = {id(n.func) for n in ast.walk(module.tree) if isinstance(n, ast.Call)}
    named = {
        dotted
        for node in ast.walk(module.tree)
        if id(node) not in called and (dotted := _dotted(module, node)) is not None
    }
    return defined, named | _published(module)


#: What each parameter of each helper (:class:`_Helper`) is handed, joined
#: over its calls: by the helper's name, then the parameter's.
Seeds = dict[str, dict[str, State]]


def _joined_seeds(handed: Iterable[Seeds]) -> Seeds:
    """What each helper's parameters are handed across every module's calls."""
    joined: Seeds = {}
    for seeds in handed:
        for helper, parameters in seeds.items():
            into = joined.setdefault(helper, {})
            for name, state in parameters.items():
                into[name] = join(into[name], state) if name in into else state
    return joined


#: What a value may hand back of a function's parameters: each parameter it
#: may be read from as the caller gave it, with what the checks on the way
#: refused in it (a parameter returned through ``real_array`` is refused a
#: complex value and a text).
Provenance = dict[str, frozenset[Refusal]]


def _either(one: Provenance, other: Provenance) -> Provenance:
    """What either of two values may hand back: a parameter either may be read
    from, with only what the checks of both refused in it.
    """
    found = dict(one)
    for name, refused in other.items():
        found[name] = found[name] & refused if name in found else refused
    return found


@dataclass(frozen=True)
class _Handing:
    """A call of a function of the library whose result a ``return`` hands
    back: what it reaches, and what each argument is read from
    (:data:`Provenance`), in order for the positional ones, by keyword for
    the rest.
    """

    target: str
    positional: tuple[Provenance, ...]
    keywords: tuple[tuple[str | None, Provenance], ...]


#: The names a comprehension binds where its element is read: each with
#: what it walks and the names in scope where that is read.
type _Local = Mapping[str, tuple[ast.expr, _Local]]

#: The scope of the function itself, where no comprehension binds a name.
_FUNCTION_SCOPE: _Local = {}

#: The names already being read, each by the function (or the module's
#: table) that holds it, so that a name bound to itself ends the reading.
type _Seen = frozenset[tuple[int, str]]

#: What a name stands for: each value, where it is read, and the function
#: whose names it is read with.
type _Values = list[tuple[ast.expr, _Local, _Returns]]


def _captures(pattern: ast.pattern) -> list[str]:
    """The names a ``case`` pattern binds, the whole subject or a part of it."""
    return [
        name
        for node in ast.walk(pattern)
        for name in (
            getattr(node, "name", None),
            getattr(node, "rest", None),
        )
        if isinstance(name, str)
    ]


def _walking(generator: ast.comprehension, local: _Local) -> _Local:
    """*local* with each name *generator* binds standing for the items of
    what it walks, which is read where *local* holds.
    """
    walked = (generator.iter, local)
    return {**local, **dict.fromkeys(_targets(generator.target), walked)}


class _Returns:
    """What a function's ``return`` statements hand back of its parameters.

    Read without the order the function runs in: a name stands for every
    value an assignment in the function binds it to, a ``:=`` among them,
    adds to it (``x += y``) or puts in one of its items (``x[i] = y``), the
    items of what a loop walks and what a ``case`` captures of its subject
    among them, and a parameter for itself as well. A comprehension's own
    names stand for the items of what it walks while its element is read,
    and for nothing outside it, as Python keeps them; what a nested function
    or a lambda binds is its own, but a name it declares ``nonlocal`` and an
    item it fills of a name it does not bind are the function's that binds
    the name, each value read where the nested function writes it. A name a
    function declares ``global`` is the module's, not the name of that
    spelling a function around it binds: what any function of the nest
    writes into it, and into an item of a name none of them binds, is what
    the module's name stands for where one reads it. A parameter of a nested
    function stands for what each call of its name in the nest hands it, by
    place or by keyword, unpacked by ``*`` or ``**`` into any place it may
    reach, read where the call is made, and for its default; what reaches
    it otherwise (``map(inner, values)``) is not followed. A value is handed
    back as the caller gave it bare, in a tuple, a list or among the values
    of a mapping, on either side of a
    conditional expression or of an ``and`` or an ``or``, by an item,
    transposed, in arithmetic with anything (its sign turned or kept, as
    :meth:`_Flow.state` reads it), as the element of a comprehension,
    through a call that keeps its values, and through a shared check
    (:data:`CHECKS`), which returns its first argument with what it refuses
    refused; a call of a function of the library hands back what that
    function returns (:func:`returned_parameters`); anything else is a value
    the function computed.
    """

    def __init__(
        self,
        module: _Module,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        parameters: frozenset[str],
        outer: _Returns | None = None,
        hidden: frozenset[str] = frozenset(),
    ) -> None:
        self.module = module
        self.function = function
        self.parameters = parameters
        #: The type parameters of the generic classes a method is written
        #: in, which it reads as theirs, not as names of the function around.
        self.hidden = hidden
        #: The function this one is nested in, which binds the names it
        #: reads but does not bind.
        self.outer = outer
        #: What each name stands for: the value, where it is read, and the
        #: function whose names it is read with.
        self.assigned: dict[str, _Values] = {}
        #: What each name of the module stands for where a function of the
        #: nest writes it: one table, the outermost function's, for them all.
        self.module_names: dict[str, _Values] = (
            {} if outer is None else outer.module_names
        )
        #: Every function of the nest, the outermost first: one list for all.
        self.nest: list[_Returns] = [] if outer is None else outer.nest
        self.nest.append(self)
        #: The functions this one defines, by name, whose parameters hold what
        #: the calls of the nest hand them (:meth:`_hand_parameters`).
        self.defined: dict[str, list[_Returns]] = {}
        #: Each call this function makes by a bare name, with the names a
        #: comprehension binds where it is made.
        self.calls: list[tuple[ast.Call, _Local]] = []
        self.declared_global = own_names(function).declared_global
        self.returns: list[ast.expr] = []
        pending: list[ast.stmt] = list(function.body)
        while pending:
            node = pending.pop()
            if isinstance(node, ast.Return) and node.value is not None:
                self.returns.append(node.value)
            elif isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                self._nested(node)
            elif isinstance(node, ast.Assign | ast.AnnAssign) and node.value:
                for target in _assigned(node):
                    for name in [*_targets(target), *_filled(target)]:
                        self._bind(name, node.value)
            elif isinstance(node, ast.AugAssign):
                # x += y holds what arithmetic on both holds: y joins what x
                # was bound to, as it joins an array an item of which it adds to.
                for name in [*_targets(node.target), *_filled(node.target)]:
                    self._bind(name, node.value)
            elif isinstance(node, ast.For | ast.AsyncFor):
                for name in _targets(node.target):
                    self._bind(name, node.iter)
            elif isinstance(node, ast.Match):
                for case in node.cases:
                    for name in _captures(case.pattern):
                        self._bind(name, node.subject)
            for child in ast.iter_child_nodes(node):
                self._walruses(child, _FUNCTION_SCOPE)
            pending.extend(
                what_runs(node)
                if isinstance(node, ast.If)
                and is_type_checking_block(node, self.module.tree)
                else block_statements(node)
            )
        if outer is None:
            self._hand_parameters()

    def _hand_parameters(self) -> None:
        """Let each parameter of a function nested in this one stand for what
        the calls of the nest hand it, by place or by keyword, and for its
        default, which the function around reads where the ``def`` is.

        A call reaches the functions of its name that the nearest function
        binding the name defines; a name declared ``global``, or one a
        comprehension binds where the call is made, reaches none of them. What
        a nested function is handed by anything but a call of its name
        (``map(inner, values)``, a callback) is not followed.
        """
        for caller in self.nest:
            for call, local in caller.calls:
                name = call.func.id if isinstance(call.func, ast.Name) else ""
                if name in local:
                    continue
                holder: _Returns | None = caller
                while not (
                    holder is None
                    or holder.binds(name)
                    or name in holder.declared_global
                ):
                    holder = holder.outer
                if holder is None or name in holder.declared_global:
                    continue
                for callee in holder.defined.get(name, []):
                    callee._handed(call, local, caller)

    def _handed(self, call: ast.Call, local: _Local, caller: _Returns) -> None:
        """Bind this function's parameters to what *call*, made by *caller*
        where *local* holds, hands them.

        An argument stands for the parameter in its place, or for ``*args``
        past them; once a ``*`` argument unpacks an unknown number of
        values, it and every argument after it may land in any place from
        its own on, or in ``*args``. A keyword stands for the parameter of
        its name, or for ``**kwargs``; a ``**`` mapping may hand its values
        to any parameter that takes a keyword, or to ``**kwargs``.
        """
        arguments = self.function.args
        positional = [*arguments.posonlyargs, *arguments.args]
        unpacked: int | None = None
        for index, value in enumerate(call.args):
            if isinstance(value, ast.Starred) and unpacked is None:
                unpacked = index
            places = (
                positional[index : index + 1]
                if unpacked is None
                else (positional[unpacked:])
            )
            for parameter in places:
                self._bind(parameter.arg, value, local, reader=caller)
            if arguments.vararg is not None and (
                unpacked is not None or index >= len(positional)
            ):
                self._bind(arguments.vararg.arg, value, local, reader=caller)
        by_keyword = [*arguments.args, *arguments.kwonlyargs]
        for keyword in call.keywords:
            if keyword.arg is None:
                for parameter in by_keyword:
                    self._bind(parameter.arg, keyword.value, local, reader=caller)
                if arguments.kwarg is not None:
                    self._bind(arguments.kwarg.arg, keyword.value, local, reader=caller)
            elif any(parameter.arg == keyword.arg for parameter in by_keyword):
                self._bind(keyword.arg, keyword.value, local, reader=caller)
            elif arguments.kwarg is not None:
                self._bind(arguments.kwarg.arg, keyword.value, local, reader=caller)

    def _bind(
        self,
        name: str,
        value: ast.expr,
        local: _Local = _FUNCTION_SCOPE,
        *,
        reader: _Returns | None = None,
    ) -> None:
        """Let *name* stand for *value*, read where *local* holds with the
        names of *reader*, this function by default: the module's name, when
        the function declares it ``global``.
        """
        table = self.module_names if name in self.declared_global else self.assigned
        table.setdefault(name, []).append((value, local, reader or self))

    def binds(self, name: str) -> bool:
        """Whether *name* is the function's own, as Python scopes it, a type
        parameter of a generic class the method is written in among them.
        """
        return own_names(self.function).binds(name) or name in self.hidden

    def _nested(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        *,
        method: bool = False,
        hidden: frozenset[str] = frozenset(),
    ) -> None:
        """Take in what a function nested in this one writes into a name of a
        function around it: a name it declares ``nonlocal``, rebound, added
        to or walked into, and an item it fills of a name it does not bind.

        Each value is read where it is written, with the nested function's
        names. A class body binds nothing a method reads but the type
        parameters of a generic class (:attr:`hidden`), and a method's writes
        go to the function around the class. A name the nested
        function declares ``global`` is the module's, and its writes are
        already the module's (:meth:`_bind`); an item it fills of a name no
        function around it binds, or one that the function binding it first
        declares ``global``, is an item of the module's name.
        """
        if isinstance(node, ast.ClassDef):
            inside = hidden | own_names(node).type_parameters
            pending: list[ast.stmt] = list(node.body)
            while pending:
                statement = pending.pop()
                if isinstance(
                    statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
                ):
                    self._nested(statement, method=True, hidden=inside)
                pending.extend(block_statements(statement))
            return
        inner = _Returns(self.module, node, frozenset(), outer=self, hidden=hidden)
        if not method:
            # A method is called through its object, which is not followed.
            self.defined.setdefault(node.name, []).append(inner)
            for parameter, default in with_defaults(node):
                if default is not None:
                    inner._bind(parameter.arg, default, reader=self)
        for name, values in inner.assigned.items():
            if inner.binds(name):
                continue
            holder: _Returns | None = self
            while not (
                holder is None or holder.binds(name) or name in holder.declared_global
            ):
                holder = holder.outer
            if holder is None or name in holder.declared_global:
                self.module_names.setdefault(name, []).extend(values)
            else:
                holder.assigned.setdefault(name, []).extend(values)

    def _walruses(self, node: ast.AST, local: _Local) -> None:
        """Bind the target of each ``:=`` in *node* that binds a name of the
        function: one in a comprehension's too, read in that comprehension,
        but none in a statement of its own, a nested function or a lambda.
        """
        if isinstance(node, (ast.stmt, *_SCOPES)):
            return
        if isinstance(node, ast.NamedExpr):
            self._bind(node.target.id, node.value, local)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            self.calls.append((node, local))
        if isinstance(node, _COMPREHENSIONS):
            inner = local
            for generator in node.generators:
                self._walruses(generator.iter, inner)
                inner = _walking(generator, inner)
                for test in generator.ifs:
                    self._walruses(test, inner)
            parts = (
                [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            )
            for part in parts:
                self._walruses(part, inner)
            return
        for child in ast.iter_child_nodes(node):
            self._walruses(child, local)

    def read(self) -> tuple[Provenance, tuple[_Handing, ...]]:
        """What the returns hand back as the caller gave it, and the calls whose
        result they hand back.
        """
        found: Provenance = {}
        calls: list[_Handing] = []
        for value in self.returns:
            provenance, through = self.sources(value, frozenset(), _FUNCTION_SCOPE)
            found = _either(found, provenance)
            calls.extend(through)
        return found, tuple(calls)

    def sources(
        self, node: ast.expr, seen: _Seen, local: _Local
    ) -> tuple[Provenance, list[_Handing]]:
        """What *node*, read where *local* holds, may hand back, and the calls
        whose result it may be.
        """
        if isinstance(node, ast.Name):
            if node.id in local:
                walked, around = local[node.id]
                return self.sources(walked, seen, around)
            return self._name(node.id, seen)
        if isinstance(node, ast.Call):
            return self._call(node, seen, local)
        if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp):
            inner = local
            for generator in node.generators:
                inner = _walking(generator, inner)
            return self.sources(node.elt, seen, inner)
        parts: list[ast.expr]
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            parts = list(node.elts)
        elif isinstance(node, ast.Dict):
            # A mapping hands on its values: one ``**`` hands to a parameter
            # of a nested function, or one read back by its key.
            parts = list(node.values)
        elif isinstance(node, ast.IfExp):
            parts = [node.body, node.orelse]
        elif isinstance(node, ast.BoolOp):
            parts = list(node.values)
        elif isinstance(node, ast.Subscript | ast.Starred | ast.NamedExpr) or (
            isinstance(node, ast.Attribute) and node.attr in _KEEPING_ATTRIBUTES
        ):
            parts = [node.value]
        elif isinstance(node, ast.BinOp):
            parts = [node.left, node.right]
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, _ARITHMETIC_SIGNS):
            parts = [node.operand]
        else:
            parts = []
        return self._joined(((part, local) for part in parts), seen)

    def _joined(
        self, parts: Iterable[tuple[ast.expr, _Local]], seen: _Seen
    ) -> tuple[Provenance, list[_Handing]]:
        """What any of *parts*, each read where its scope holds, may hand back."""
        found: Provenance = {}
        calls: list[_Handing] = []
        for part, local in parts:
            provenance, through = self.sources(part, seen, local)
            found = _either(found, provenance)
            calls.extend(through)
        return found, calls

    def _name(self, name: str, seen: _Seen) -> tuple[Provenance, list[_Handing]]:
        if name in self.declared_global:
            values = self.module_names.get(name, [])
            key = (id(self.module_names), name)
        elif self.binds(name):
            values = self.assigned.get(name, [])
            key = (id(self), name)
        elif self.outer is not None:
            return self.outer._name(name, seen)
        else:
            # A name no function of the nest binds is the module's, and so
            # is an item this one fills of it.
            values = [*self.assigned.get(name, []), *self.module_names.get(name, [])]
            key = (id(self.module_names), name)
        if key in seen:
            return {}, []
        found: Provenance = {}
        calls: list[_Handing] = []
        for value, local, reader in values:
            provenance, through = reader.sources(value, seen | {key}, local)
            found = _either(found, provenance)
            calls.extend(through)
        if name in self.parameters:
            found = _either(found, {name: frozenset()})
        return found, calls

    def _target(self, name: str) -> str:
        """The function of the package a call of *name* reaches, by its module."""
        return self.module.imports.get(name, f"{self.module.name}.{name}")

    def _call(
        self, call: ast.Call, seen: _Seen, local: _Local
    ) -> tuple[Provenance, list[_Handing]]:
        if id(call) in self.module.numpy.hidden:
            return {}, []
        func = call.func
        if (
            isinstance(func, ast.Name)
            and func.id in CHECKS
            and call.args
            and self._target(func.id) == f"{SHARED}.{func.id}"
        ):
            found, calls = self.sources(call.args[0], seen, local)
            refused = CHECKS[func.id]
            return {name: held | refused for name, held in found.items()}, calls
        kept = _kept(call, self.module.numpy)
        if kept:
            return self._joined(((part, local) for part in kept), seen)
        if not isinstance(func, ast.Name):
            return {}, []
        handed = _Handing(
            self._target(func.id),
            tuple(self.sources(a, seen, local)[0] for a in call.args),
            tuple(
                (k.arg, self.sources(k.value, seen, local)[0]) for k in call.keywords
            ),
        )
        return {}, [handed]


def returned_parameters(signatures: Sequence[_Signature]) -> dict[str, Provenance]:
    """What each function of *signatures* may hand back of its parameters,
    through the functions of the library whose result it returns too,
    followed until no new one turns up.
    """
    by_name = {signature.dotted: signature for signature in signatures}
    found = {signature.dotted: dict(signature.returned) for signature in signatures}
    grown = True
    while grown:
        grown = False
        for signature in signatures:
            more = found[signature.dotted]
            for call in signature.returned_calls:
                callee = by_name.get(call.target)
                if callee is not None:
                    more = _either(
                        more, _handed_back(call, callee, found[callee.dotted])
                    )
            if more != found[signature.dotted]:
                found[signature.dotted] = more
                grown = True
    return found


def _handed_back(
    call: _Handing, callee: _Signature, returned: Provenance
) -> Provenance:
    """What the arguments of *call* that *callee* hands back are read from,
    with what *callee* refused in each on the way.
    """
    found: Provenance = {}
    pairs = [
        *zip(callee.positional, call.positional, strict=False),
        *((name, provenance) for name, provenance in call.keywords if name),
    ]
    for name, provenance in pairs:
        if name in returned:
            refused = returned[name]
            found = _either(
                found, {source: held | refused for source, held in provenance.items()}
            )
    return found


def _held(reader: _Flow, argument: ast.expr, bound: frozenset[str]) -> frozenset[str]:
    """The names *argument* reads the value of as it is, but those bound before."""
    return frozenset(
        name
        for name in reader.names_read(argument)
        if name.partition("[")[0] not in bound
    )


@dataclass(frozen=True)
class Check:
    """A function that refuses a complex value or a text in some of its parameters.

    A shared check of :data:`CHECKS` refuses *every* in every argument it
    is given (the value; the name or the message beside it is no caller's
    number). A function of the library lists its positional parameters in
    order, none for one whose parameters are all keyword-only, and what it
    refuses in each it hands to a check.
    """

    parameters: tuple[str, ...] = ()
    every: frozenset[Refusal] = frozenset()
    refused: Mapping[str, frozenset[Refusal]] = field(default_factory=dict)
    shared: bool = False

    def arguments(self, call: ast.Call) -> list[tuple[ast.expr, frozenset[Refusal]]]:
        """The arguments of *call* this check reads, with what it refuses in each."""
        if self.shared:
            return [
                (a, self.every) for a in (*call.args, *(k.value for k in call.keywords))
            ]
        found = [
            (argument, self.refused[name])
            for name, argument in zip(self.parameters, call.args, strict=False)
            if name in self.refused
        ]
        return found + [
            (k.value, self.refused[k.arg])
            for k in call.keywords
            if k.arg is not None and k.arg in self.refused
        ]

    def names(self, call: _Call) -> list[tuple[frozenset[str], frozenset[Refusal]]]:
        """The names the arguments of *call* this check reads are read from,
        with what it refuses in each.
        """
        if self.shared:
            read = [*call.positional, *(names for _, names in call.keywords)]
            return [(names, self.every) for names in read]
        found = [
            (names, self.refused[name])
            for name, names in zip(self.parameters, call.positional, strict=False)
            if name in self.refused
        ]
        return found + [
            (names, self.refused[name])
            for name, names in call.keywords
            if name is not None and name in self.refused
        ]


def _checker(
    module: _Module, checks: Mapping[str, Check]
) -> Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]]]:
    """The arguments a call made in *module* hands to a check, by the module
    that defines the check, with what it refuses in each.
    """

    def checked_by(call: ast.Call) -> list[tuple[ast.expr, frozenset[Refusal]]]:
        if not isinstance(call.func, ast.Name) or id(call) in module.numpy.hidden:
            return []
        name = call.func.id
        check = checks.get(module.imports.get(name, f"{module.name}.{name}"))
        return [] if check is None else check.arguments(call)

    return checked_by


def _hander(
    module: _Module,
    checks: Mapping[str, Check],
    returned: Mapping[str, Provenance],
) -> Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]] | None]:
    """What a call made in *module* of a check of the library hands back:
    each argument the check returns (*returned*), with what it refused in it;
    ``None`` for a call of a shared check or of anything else.
    """

    def handed(call: ast.Call) -> list[tuple[ast.expr, frozenset[Refusal]]] | None:
        if not isinstance(call.func, ast.Name) or id(call) in module.numpy.hidden:
            return None
        name = call.func.id
        target = module.imports.get(name, f"{module.name}.{name}")
        check = checks.get(target)
        if check is None or check.shared:
            return None
        back = returned.get(target, {})
        pairs = [
            *zip(check.parameters, call.args, strict=False),
            *((k.arg, k.value) for k in call.keywords if k.arg is not None),
        ]
        return [
            (argument, check.refused.get(parameter, frozenset()) | back[parameter])
            for parameter, argument in pairs
            if parameter in back
        ]

    return handed


def package_checks(signatures: Sequence[_Signature]) -> dict[str, Check]:
    """Every check of the package, shared and local, by the module that defines it.

    The shared :data:`CHECKS`, then each function of *signatures* that hands
    a parameter to a check already found on every path, until no new one
    turns up.
    """
    checks = {
        f"{SHARED}.{name}": Check(every=refused, shared=True)
        for name, refused in CHECKS.items()
    }
    grown = True
    while grown:
        grown = False
        for signature in signatures:
            # Every function is read on each pass, a check found early or not.
            grown = _grow(signature, checks) or grown
    return checks


def _grow(signature: _Signature, checks: dict[str, Check]) -> bool:
    """Make the function of *signature* a check, or widen it, when it hands a
    parameter to one.

    :return: Whether a check was added or widened.
    """
    previous = checks.get(signature.dotted)
    if previous is not None and previous.shared:
        return False
    refused: dict[str, frozenset[Refusal]] = {}
    for call in signature.calls:
        check = checks.get(call.target)
        for names, refusals in check.names(call) if check is not None else ():
            for name in names & signature.parameters:
                refused[name] = refused.get(name, frozenset()) | refusals
    if not refused or (previous is not None and refused == dict(previous.refused)):
        return False
    checks[signature.dotted] = Check(signature.positional, frozenset(), refused)
    return True


def _function_names(
    module: _Module, function: ast.FunctionDef | ast.AsyncFunctionDef
) -> _Names:
    """How *function* spells NumPy: its module's names and the dtypes it binds."""
    own = _dtype_names(ast.walk(function), module.numpy, function)
    if not own:
        return module.numpy
    return replace(module.numpy, dtypes={**module.numpy.dtypes, **own})


def conversions_in(
    module: _Module,
    checks: Mapping[str, Check],
    file: str = "",
    returned: Mapping[str, Provenance] | None = None,
) -> list[Conversion]:
    """Every conversion in *module*, with what it reads.

    *returned* says what each check of the library hands back of its
    parameters (:func:`returned_parameters`); without it, none.
    """
    found, _ = _read_module(module, checks, file, returned or {}, {}, {})
    return found


def _read_module(
    module: _Module,
    checks: Mapping[str, Check],
    file: str,
    returned: Mapping[str, Provenance],
    helpers: Mapping[str, _Helper],
    seeds: Seeds,
) -> tuple[list[Conversion], Seeds]:
    """Every conversion in *module*, with what it reads, and what its calls
    hand each helper of *helpers*, whose parameters hold what *seeds* says
    they are handed.
    """
    reading = _Reading(
        module,
        _checker(module, checks),
        file,
        _hander(module, checks, returned),
        helpers,
        seeds,
    )
    never_runs = for_the_type_checker(module.tree)
    for qualified, function in _functions(module.tree):
        if id(function) not in never_runs:
            reading.function(qualified, function)
    found = sorted(reading.found, key=lambda c: (c.key[0], c.line, c.source))
    return found, reading.handing


@dataclass
class _Reading:
    """The functions of a module read one after the other, each nested one
    with what the names it shares with the function around it hold for it.
    """

    module: _Module
    checks: Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]]]
    file: str
    handed: Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]] | None]
    #: The private helpers of the package, read through their calls, and what
    #: their parameters are handed (:data:`Seeds`).
    helpers: Mapping[str, _Helper] = field(default_factory=dict)
    seeds: Seeds = field(default_factory=dict)
    #: What this module's calls hand each helper.
    handing: Seeds = field(default_factory=dict)
    found: list[Conversion] = field(default_factory=list)
    #: What a nested function's enclosing names hold, and whether it reads a
    #: record's fields, by the definition's id, kept until it is read.
    enclosed: dict[int, tuple[Env, bool]] = field(default_factory=dict)

    def function(
        self, qualified: str, function: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        captured, fields = self.enclosed.pop(id(function), ({}, False))
        flow = _Flow(
            self.checks,
            _function_names(self.module, function),
            fields=fields or function.name == "__post_init__",
            root=self.module.tree,
            handed=self.handed,
            calling=self._calling,
        )
        dotted = f"{self.module.name}.{qualified}"
        env = _scope_env(
            captured,
            function,
            function.body,
            self.seeds.get(dotted, {}) if dotted in self.helpers else None,
        )
        end, _ = flow.block(function.body, env)
        self._keep(qualified, flow)
        for inner in flow.nested.values():
            self.enclosed[id(inner)] = (flow.captured(inner, end), flow.fields)
        for node, defined in flow.classes:
            # A method of a class written here reads the names it shares with
            # this function as they stand where the class is written, or at
            # the end, whenever an instance's method is called; not the names
            # of a generic class's type parameters, which are the class's.
            shared = _join_envs([defined, end], flow.default)
            for method, hidden in _methods_and_type_parameters(node):
                kept = {
                    name: state for name, state in shared.items() if name not in hidden
                }
                self.enclosed[id(method)] = (kept, False)

    def _lambda(
        self, qualified: str, node: ast.Lambda, captured: Env, outer: _Flow
    ) -> None:
        flow = _Flow(
            self.checks,
            outer.names,
            fields=outer.fields,
            root=outer.root,
            handed=self.handed,
            calling=self._calling,
        )
        env = _scope_env(captured, node, [node.body])
        flow.expression(node.body, env)
        self._keep(qualified, flow)

    def _calling(self, flow: _Flow, call: ast.Call, env: Env) -> None:
        """Join what *call* hands a helper into what its parameters are handed."""
        if id(call) in self.module.numpy.hidden:
            return
        target = _dotted(self.module, call.func)
        helper = self.helpers.get(target) if target is not None else None
        if target is None or helper is None:
            return
        into = self.handing.setdefault(target, {})
        for name, state in helper.handed(call, lambda node: flow.state(node, env)):
            into[name] = join(into[name], state) if name in into else state

    def _keep(self, qualified: str, flow: _Flow) -> None:
        for call, value, kind, verdict in flow.found.values():
            self.found.append(
                Conversion(
                    self.module.path,
                    call.lineno,
                    qualified,
                    ast.unparse(value),
                    verdict,
                    kind,
                    self.file,
                )
            )
        for node, captured in flow.lambdas:
            self._lambda(f"{qualified}.<lambda>", node, captured, flow)


def _methods_and_type_parameters(
    node: ast.ClassDef,
) -> Iterator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, frozenset[str]]]:
    """Each method of a class, through its compound statements and the
    classes written in it, whose methods share the same enclosing names, with
    the type parameters of the generic classes it is written in, this one and
    any between, which it reads as theirs and not as names of the function
    around.
    """
    pending: list[tuple[ast.stmt, frozenset[str]]] = [
        (statement, own_names(node).type_parameters) for statement in node.body
    ]
    while pending:
        statement, hidden = pending.pop()
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            yield statement, hidden
        elif isinstance(statement, ast.ClassDef):
            inner = hidden | own_names(statement).type_parameters
            pending.extend((child, inner) for child in statement.body)
        else:
            pending.extend((child, hidden) for child in block_statements(statement))


def _scope_env(
    captured: Env,
    scope: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
    body: Sequence[ast.AST],
    handed: Mapping[str, State] | None = None,
) -> Env:
    """What a function's names hold where it starts: its parameters the
    caller's values, or, for a helper read through its calls, what *handed*
    says they are handed (none where no call hands one), and what it shares
    with the function around it as that function holds it, but a name it
    binds of its own and one it declares ``global``, which is the module's.
    """
    names = own_names(scope)
    shared = names.declared_global | names.declared_nonlocal
    own = {name for node in body for name in _bound_names(node)} - shared
    # A name it declares ``global`` is the module's, and one of its type
    # parameters its own, whatever a function around it binds of that
    # spelling.
    own |= set(_parameters(scope)) | names.declared_global | names.type_parameters
    env = {
        name: state
        for name, state in captured.items()
        if name.partition("[")[0].partition(".")[0] not in own
    }
    for name in _parameters(scope):
        env[name] = frozenset() if handed is None else handed.get(name)
    return env


def _spelled(path: pathlib.Path, source: pathlib.Path | None) -> str:
    """*path* as the repository that holds *source* spells it."""
    if source is not None:
        top = source.resolve().parent.parent
        if path.is_relative_to(top):
            return path.relative_to(top).as_posix()
    return relative(path)


def census(
    paths: Iterable[pathlib.Path], *, source: pathlib.Path | None = SOURCE
) -> list[Conversion]:
    """Every conversion under *paths*, with what each reads.

    The checks are found across the files read and, with *source*, across
    every module of the library there, so that a file read alone still knows
    the checks its package defines; another copy of the library is read with
    its own checks only. Each module is parsed twice, once for the checks it
    defines and once for its conversions, and one at a time, so that no more
    than one tree is held at once.
    """
    read = [path.resolve() for path in paths]
    sources = set(read)
    if source is not None:
        sources |= {path.resolve() for path in source.rglob("*.py")}
    signatures: list[_Signature] = []
    helpers: dict[str, _Helper] = {}
    named: set[str] = set()
    for path in sorted(sources):
        module = _module(path)
        signatures.extend(_signatures(module))
        defined, names = _helpers(module)
        helpers.update(defined)
        named |= names
    helpers = {name: h for name, h in helpers.items() if name not in named}
    checks = package_checks(signatures)
    returned = returned_parameters(signatures)
    found = _through_callers(read, sources, source, (checks, returned), helpers)
    return [c for path in read for c in found[path]]


def _through_callers(
    read: Sequence[pathlib.Path],
    sources: set[pathlib.Path],
    source: pathlib.Path | None,
    package: tuple[Mapping[str, Check], Mapping[str, Provenance]],
    helpers: Mapping[str, _Helper],
) -> dict[pathlib.Path, list[Conversion]]:
    """The conversions of each module of *read*, every helper's parameters
    holding what its calls across *sources* hand it.

    Every module is read once with the helpers handed nothing, and then each
    module that defines a helper whose calls hand it something new is read
    again, until no call hands anything new: what a parameter is handed only
    grows, toward a caller's value no check has read, so the reading ends.
    """
    checks, returned = package
    wanted = set(read)
    seeds: Seeds = {}
    handing: dict[pathlib.Path, Seeds] = {}
    found: dict[pathlib.Path, list[Conversion]] = {}
    pending = sorted(sources)
    while pending:
        for path in pending:
            conversions, handing[path] = _read_module(
                _module(path), checks, _spelled(path, source), returned, helpers, seeds
            )
            if path in wanted:
                found[path] = conversions
        joined = _joined_seeds(handing.values())
        moved = {
            name
            for name in joined.keys() | seeds.keys()
            if joined.get(name) != seeds.get(name)
        }
        seeds = joined
        pending = sorted({helpers[name].path for name in moved})
    return found


def unchecked(
    paths: Iterable[pathlib.Path],
    exempt: Mapping[tuple[str, str], str] | None = None,
    *,
    source: pathlib.Path | None = SOURCE,
) -> tuple[list[Conversion], list[tuple[str, str]]]:
    """The conversions of a caller's value no check precedes, and stale exemptions."""
    found = [c for c in census(paths, source=source) if c.verdict == "unchecked"]
    return exempted(found, EXEMPT if exempt is None else exempt)


def main(argv: Sequence[str] | None = None) -> int:
    """Report each unchecked conversion of a caller's value; with --census, all."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="files or directories to read")
    parser.add_argument(
        "--census", action="store_true", help="print every conversion and what it reads"
    )
    parser.add_argument(
        "--source",
        type=pathlib.Path,
        default=SOURCE,
        help="the library to read, another copy of src/phonometry with its own checks",
    )
    arguments = parser.parse_args(argv)
    source: pathlib.Path = arguments.source
    files = python_files(arguments.paths, source)
    if arguments.census:
        for conversion in census(files, source=source):
            print(conversion.describe())
        return 0
    left, stale = unchecked(files, EXEMPT if not arguments.paths else {}, source=source)
    for conversion in left:
        print(conversion.describe())
    for key in stale:
        print(f"{key[0]}  {key[1]}  exemption that covers nothing")
    if left or stale:
        print(
            f"{len(left)} conversion(s) read a caller's value no check has read "
            "on every path: read it through real_array(value, name) or "
            "complex_array(value, name) of phonometry._internal.validation, or "
            "check it first.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
