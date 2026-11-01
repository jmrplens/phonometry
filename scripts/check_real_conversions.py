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
  is so read; and, in a record's ``__post_init__``, a field, ``self.x``,
  which the caller set. A private function's parameter counts as much as a
  public one's: a public function hands its caller's value on to the helper
  that converts it.
- **A check**: a call of one of :data:`CHECKS` with the value among its
  arguments, or of a function of the library that hands that parameter to
  one on every path that leaves it by its end or a ``return`` (found by
  following such calls through the package until no new one turns up): a
  call after an earlier ``return``, in the body of a ``try`` a handler of
  which goes on, or of a parameter rebound before it to another value
  counts for nothing; or a name rebound to what a check returns. A check
  handed what NumPy made of a caller's value no check has refused a text in
  (``np.asarray(x)``, ``np.atleast_1d(x)`` and the other NumPy calls that
  keep its values, given no floating dtype, or a name bound to one) reads a
  ``bytearray`` as the codes of its characters, and the census lists that
  reading as a conversion no check precedes. What each check refuses is listed, a complex value, a text or
  both: a conversion to floats needs both refused, one to complex numbers a
  text. A check of an item (``x[0]``) reads that item, not the sequence it
  was taken from.
- **On every path**: the function is read the way it runs. A check inside
  an ``if`` holds after it only when the other branch checks too or leaves
  the function; a check in one branch does not reach the other; a check in
  a loop's body, a conditional expression, the right side of ``and`` or
  ``or``, or a comprehension may not run, and holds only inside it.

A value the function computed (a local of its own arithmetic, a field of a
record it was handed, which the record read when it was built) is no
caller's, and the census lists it as computed. A field a record's method
reads outside ``__post_init__`` is listed apart: the record's constructor is
where its caller's value was read.

``--census`` prints every conversion in the tree with what it reads, so that
the class is listed whole and not only what is left of it. ``--source``
reads another copy of the library, with that copy's own checks.

A conversion of a value that is no caller's number but that the rule cannot
tell from one (the samples SciPy decoded from a file, a mask the engine
builds, an array of objects an ``isinstance`` test has read item by item, the
quick path of the readers themselves, the drawing helpers whose source the
published clips fingerprint, which draw what a result holds) is listed in
:data:`EXEMPT`, keyed by file and function with the reason; an entry that
covers nothing is reported too.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ast_scan import ROOT, exempted, python_files, relative

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
    ("src/phonometry/_plot/common.py", "_srgb_to_lab"): (
        "an sRGB triple of the figure's own palette, which the contrast checks "
        "of every drawing read; no caller hands it, and the clips fingerprint "
        "this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_facade_x_axis"): (
        "the band axis of a result being drawn, a field the result read when "
        "it was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_bar_width"): (
        "the bar positions a renderer computed from a result's band axis; the "
        "clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_plot_band_level_bars"): (
        "the levels of a result being drawn, a field the result read when it "
        "was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_plot/common.py", "_plot_two_runs"): (
        "the band axis of a result being drawn, a field the result read when "
        "it was built; the clips fingerprint this module's source"
    ),
    ("src/phonometry/_internal/validation.py", "real_array"): (
        "the shared reader itself, whose quick path converts only an array of "
        "truth values, integers or floats, which holds no complex number"
    ),
    ("src/phonometry/_internal/validation.py", "complex_array"): (
        "the shared reader itself, which converts only after it has refused a "
        "text at any depth"
    ),
    ("src/phonometry/_internal/display.py", "_sequence_summary"): (
        "a record's display, after an isinstance test that every item is an int "
        "or a float; reading it through real_array would import the validation "
        "module into the display module it imports"
    ),
    ("src/phonometry/io/_wav.py", "_scale_to_float"): (
        "the samples SciPy decoded from a WAV file, an integer or a float array "
        "by the format; no caller hands them"
    ),
    ("src/phonometry/simulation/elastic_fdtd.py", "_device_mask"): (
        "a boolean mask the engine builds from the grid, sent to the device as "
        "zeros and ones; no caller hands it"
    ),
    ("src/phonometry/simulation/fdtd.py", "_held_map"): (
        "a map converted only when holds_complex and holds_text have found "
        "neither in it; anything else is handed back as given, for the checks "
        "of the medium to refuse in their own words"
    ),
    ("src/phonometry/filters/weighting_compliance.py", "_edition_masks"): (
        "the tolerance table of a published edition, the module's own "
        "_WEIGHTING_EDITIONS that every caller looks up by the edition's name; "
        "no caller hands it"
    ),
    ("src/phonometry/materials/absorbers/uncertainty.py", "_table_constants"): (
        "the m and n of the standard's Tables 1 and 2, the module's own tables, "
        "looked up per band; the caller's frequencies, read through "
        "_finite_bands first, are only the keys"
    ),
    ("src/phonometry/simulation/fdtd.py", "_real_objects"): (
        "an array of objects converted only after an isinstance test that every "
        "item is a real number and no truth value"
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


def _kept(call: ast.Call, names: _Names) -> list[ast.expr]:
    """The values a call that keeps them reads: its object as a method, its
    first argument as a function, every argument for ``zip`` and its kin;
    nothing for a call that keeps none, a conversion included.
    """
    callee = _last_name(call.func)
    if converted(call, names) is not None:
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
    #: The names bound to what NumPy made of a caller's value no check has
    #: refused a text in, in which a ``bytearray`` is the codes of its
    #: characters.
    numpy_read: set[str] = field(default_factory=set)

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
        read = self.checks(call)
        if read:
            refusals: frozenset[Refusal] = frozenset()
            for _, refused in read:
                refusals |= refused
            return refusals
        return self._joined(_kept(call, self.names), env)

    def names_read(self, node: ast.expr) -> list[str]:
        """The names *node* holds the value of as it is, as a check reads them."""
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.Attribute):
            return self._attribute_names(node)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            return [ast.unparse(node)]
        return [name for part in self._parts(node) for name in self.names_read(part)]

    def _attribute_names(self, node: ast.Attribute) -> list[str]:
        if self.fields and isinstance(node.value, ast.Name) and node.value.id == "self":
            return [f"self.{node.attr}"]
        return self.names_read(node.value) if node.attr in _KEEPING_ATTRIBUTES else []

    def _parts(self, node: ast.expr) -> list[ast.expr]:
        """The parts of *node* that hold its value as they are."""
        if isinstance(node, ast.Starred | ast.NamedExpr):
            return [node.value]
        if isinstance(node, ast.Tuple | ast.List):
            return list(node.elts)
        if isinstance(node, ast.IfExp):
            return [node.body, node.orelse]
        if isinstance(node, ast.Call):
            return _kept(node, self.names)
        return []

    # Bindings and checks.

    def bind(
        self, target: ast.expr, value: ast.expr | None, state: State, env: Env
    ) -> None:
        """Bind *target* to *value*, which holds *state*, member by member
        where both are tuples of the same length.
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
        for name in _targets(target):
            self._set(env, name, state)

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
            self.expression(node.body, env, sure=False)
            self.expression(node.orelse, env, sure=False)
        elif isinstance(node, ast.BoolOp):
            self.expression(node.values[0], env, sure=sure)
            for value in node.values[1:]:
                self.expression(value, env, sure=False)
        elif isinstance(node, _COMPREHENSIONS):
            self._comprehension_env(node, env, record=True)
        elif isinstance(node, ast.NamedExpr):
            self.expression(node.value, env, sure=sure)
            state = self.state(node.value, env)
            held = state if sure else join(state, self.lookup(env, node.target.id))
            self._set(env, node.target.id, held)
        else:
            for child in ast.iter_child_nodes(node):
                self.expression(child, env, sure=sure)
            if isinstance(node, ast.Call):
                self._at_call(node, env, sure=sure)

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
        if (found := converted(call, self.names)) is not None:
            value, kind = found
            self._record(call, value, kind, self._verdict(value, kind, env))
            return
        for argument, refused in self.checks(call):
            # A check handed NumPy's reading of the value reads a bytearray's
            # codes as numbers: the reading is a conversion no check precedes.
            if "text" in refused and self._numpy_reading(argument, env):
                kind: Kind = "real" if "complex" in refused else "complex"
                self._record(call, argument, kind, "unchecked")
        if sure:
            self.check(call, env)

    def _numpy_reading(self, node: ast.expr, env: Env) -> bool:
        """Whether *node* is what NumPy made of a caller's value no check has
        refused a text in (``np.asarray(x)``, ``np.atleast_1d(x)`` and the
        other NumPy calls that keep its values), or a name bound to it.
        """
        if isinstance(node, ast.Name):
            return node.id in self.numpy_read
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
            self.bind(generator.target, None, self.state(generator.iter, inner), inner)
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
        if isinstance(node, _SCOPES):
            return env, False
        for child in ast.iter_child_nodes(node):
            self.expression(child, env)
        return env, isinstance(node, ast.Return | ast.Raise | ast.Continue)

    def _assign(
        self, node: ast.Assign | ast.AnnAssign | ast.AugAssign, env: Env
    ) -> tuple[Env, bool]:
        if node.value is None:
            return env, False
        self.expression(node.value, env)
        if isinstance(node, ast.AugAssign):
            return env, False
        state = self.state(node.value, env)
        read = self._numpy_reading(node.value, env)
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            self.bind(target, node.value, state, env)
            for name in _targets(target):
                if read and isinstance(target, ast.Name):
                    self.numpy_read.add(name)
                else:
                    self.numpy_read.discard(name)
        return env, False

    def _if(self, node: ast.If, env: Env) -> tuple[Env, bool]:
        self.expression(node.test, env)
        body, body_ends = self.block(node.body, dict(env))
        other, other_ends = self.block(node.orelse, dict(env))
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
                self.bind(node.target, None, self.state(node.iter, inner), inner)
            end, _ = self.block(node.body, inner)
            entry = _join_envs([head, end], self.default)
        breaks = self.breaks.pop()
        after, ends = self.block(node.orelse, entry)
        reached = [*([] if ends else [after]), *breaks]
        if not reached:
            return after, True
        return _join_envs(reached, self.default), False

    def captured(self, function: ast.FunctionDef | ast.AsyncFunctionDef) -> Env:
        """What the names a nested *function* shares with this one hold for
        it: where it is used, or, used nowhere here, where it is defined.
        """
        envs = self.used.get(id(function)) or self.defined.get(id(function), [])
        return _join_envs(envs, self.default)

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
                self.bind(item.optional_vars, None, state, env)
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
        reached: list[Env] = []
        for case in node.cases:
            inner = dict(env)
            for capture in ast.walk(case.pattern):
                name = getattr(capture, "name", None)
                if isinstance(name, str):
                    self._set(inner, name, subject)
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


_STATEMENTS: dict[type[ast.stmt], Callable[[_Flow, Any, Env], tuple[Env, bool]]] = {
    ast.Assign: _Flow._assign,
    ast.AnnAssign: _Flow._assign,
    ast.AugAssign: _Flow._assign,
    ast.If: _Flow._if,
    ast.For: _Flow._loop,
    ast.AsyncFor: _Flow._loop,
    ast.While: _Flow._loop,
    ast.Break: _Flow._break,
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
    """``{name: "module.name"}`` for each ``from`` import of the module."""
    package = module if is_package else module.rpartition(".")[0]
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            parts = package.split(".")
            base = parts[: len(parts) - (node.level - 1)]
            source = ".".join([*base, *([node.module] if node.module else [])])
        else:
            source = node.module or ""
        for alias in node.names:
            found[alias.asname or alias.name] = f"{source}.{alias.name}"
    return found


def _numpy_names(tree: ast.Module, imports: Mapping[str, str]) -> _Names:
    """How the module of *tree* spells NumPy's constructors and dtypes."""
    numpy = frozenset(
        name for name, dotted in imports.items() if dotted.startswith("numpy.")
    )
    plain = _Names(numpy)
    return _Names(numpy, _dtype_names(tree.body, plain))


@dataclass(frozen=True, eq=False)
class _Module:
    """A module of the library, parsed, with what its imports bind."""

    path: pathlib.Path
    name: str
    tree: ast.Module
    imports: dict[str, str]
    numpy: _Names


def _module(path: pathlib.Path) -> _Module:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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
    loop's body or a ``match`` case may not run. A name bound before a call
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
        if isinstance(node, ast.If):
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
        elif not isinstance(node, _SCOPES):
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


def _first_part(node: ast.expr) -> ast.expr | None:
    """The part of a conditional expression that surely runs: the test of an
    ``if`` expression, the first operand of ``and`` and ``or``, the first
    iterable of a comprehension; ``None`` for an expression that runs whole.
    """
    if isinstance(node, ast.IfExp):
        return node.test
    if isinstance(node, ast.BoolOp):
        return node.values[0]
    if isinstance(node, _COMPREHENSIONS):
        return node.generators[0].iter
    return None


def _expression_calls(node: ast.AST, *, sure: bool) -> Iterator[tuple[ast.Call, bool]]:
    if isinstance(node, _SCOPES):
        return
    first = _first_part(node) if isinstance(node, ast.expr) else None
    if first is not None:
        yield from _expression_calls(first, sure=sure)
        for call, _ in _nested_calls(node):
            if not _within(call, first):
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
    """What the search for the checks of the package needs of one function."""

    dotted: str
    positional: tuple[str, ...]
    parameters: frozenset[str]
    calls: tuple[_Call, ...]


def _signatures(path: pathlib.Path) -> list[_Signature]:
    """The functions at the top of the module at *path*, each without its tree.

    A method is called through an object the rule does not follow, so only
    a function at the top of a module can be a check of its own; and only a
    call that runs on every path that leaves it by its end or a ``return``,
    and is not in the body of a ``try`` a handler of which goes on, makes it
    one, of a parameter the call reads before anything rebinds it.
    """
    module = _module(path)
    reader = _Flow(lambda _: [], module.numpy, fields=False)
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
            if isinstance(call.func, ast.Name)
        )
        arguments = node.args
        positional = tuple(a.arg for a in arguments.posonlyargs + arguments.args)
        found.append(
            _Signature(
                f"{module.name}.{node.name}",
                positional,
                frozenset(_parameters(node)),
                calls,
            )
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
        if not isinstance(call.func, ast.Name):
            return []
        name = call.func.id
        check = checks.get(module.imports.get(name, f"{module.name}.{name}"))
        return [] if check is None else check.arguments(call)

    return checked_by


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
    return _Names(module.numpy.numpy, {**module.numpy.dtypes, **own})


def conversions_in(
    module: _Module, checks: Mapping[str, Check], file: str = ""
) -> list[Conversion]:
    """Every conversion in *module*, with what it reads."""
    reading = _Reading(module, _checker(module, checks), file)
    for qualified, function in _functions(module.tree):
        reading.function(qualified, function)
    return sorted(reading.found, key=lambda c: (c.key[0], c.line, c.source))


@dataclass
class _Reading:
    """The functions of a module read one after the other, each nested one
    with what the names it shares with the function around it hold for it.
    """

    module: _Module
    checks: Callable[[ast.Call], list[tuple[ast.expr, frozenset[Refusal]]]]
    file: str
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
        )
        env = _scope_env(captured, function, function.body)
        flow.block(function.body, env)
        self._keep(qualified, flow)
        for inner in flow.nested.values():
            self.enclosed[id(inner)] = (flow.captured(inner), flow.fields)

    def _lambda(
        self, qualified: str, node: ast.Lambda, captured: Env, outer: _Flow
    ) -> None:
        flow = _Flow(self.checks, outer.names, fields=outer.fields)
        env = _scope_env(captured, node, [node.body])
        flow.expression(node.body, env)
        self._keep(qualified, flow)

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


def _scope_env(
    captured: Env,
    scope: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
    body: Sequence[ast.AST],
) -> Env:
    """What a function's names hold where it starts: its parameters the
    caller's values, and what it shares with the function around it as that
    function holds it, but a name it binds of its own.
    """
    shared = _declared_shared(body)
    own = {name for node in body for name in _bound_names(node)} - shared
    own |= set(_parameters(scope))
    env = {
        name: state
        for name, state in captured.items()
        if name.partition("[")[0].partition(".")[0] not in own
    }
    env.update(dict.fromkeys(_parameters(scope), frozenset()))
    return env


def _declared_shared(body: Sequence[ast.AST]) -> set[str]:
    """The names a function declares ``nonlocal`` or ``global``."""
    return {
        name
        for node in body
        for child in ast.walk(node)
        if isinstance(child, ast.Nonlocal | ast.Global)
        for name in child.names
    }


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
    checks = package_checks([s for path in sorted(sources) for s in _signatures(path)])
    return [
        c
        for path in read
        for c in conversions_in(_module(path), checks, _spelled(path, source))
    ]


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
