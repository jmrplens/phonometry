#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public parameter annotated narrower than what its body accepts.

A function that hands its ``levels`` to ``np.asarray`` takes a list, a
tuple, an array of any dtype, a nested list for a 2-D input and a number
for a 1-element one: that is what ``np.asarray`` converts. Annotated
``NDArray[np.float64]``, ``list[float]`` or ``Sequence[float]``, the same
parameter makes a type checker refuse most of them: a tuple, an integer
array, a list of lists, and, for ``list[float]``, even a ``list[int]``,
because ``list`` is invariant (a ``list[int]`` is not a ``list[float]``,
since a function could append a float to it). The caller's code runs and
the type checker says it does not. The remedy is the type numpy gives
for what it converts, ``ArrayLike`` (``Signal | ArrayLike`` where a
:class:`~phonometry.io.Signal` is accepted too). A count, a band fraction
or a flag the body validates the way numpy code hands it over, a
``np.int64`` from ``np.argmax`` or a ``np.True_`` from a comparison, is
the same defect on one number.

The rule, read from the source of every public function and method of the
package (a function or class in the ``__all__`` of a public module, the
public methods of such a class and of the classes of the package it
extends, an explicit ``__init__`` or ``__call__`` included):

* a parameter whose annotation names an array (``np.ndarray``,
  ``NDArray``) or a sequence of numbers (``list``, ``tuple``,
  ``Sequence``, ``Iterable`` of ``float`` and its kin, nested or not), and
  no ``ArrayLike``, fails when the parameter reaches a conversion: a numpy
  function that takes any array-like (``np.asarray``, ``np.array``,
  ``np.atleast_1d`` and their kin) or a function of the package whose own
  parameter is annotated ``ArrayLike``. The parameter is followed into
  the functions of the package it is handed to, by position or by
  keyword, into their own conversions, up to six calls deep, and through
  the local names bound to it: a name assigned it (``values = levels``) or
  a copy of it (``list(levels)``), the name a loop over a literal of
  parameters takes each of them in (``for values in (fpi, delta)``), and,
  for a vararg, whose annotation types each argument, the name a loop over
  it takes each argument in (``for i, m in enumerate(matrices)``). Names
  are read scope by scope: a nested function, lambda or comprehension that
  binds the parameter's name for itself (its own parameter, an assignment,
  a loop variable) holds another value under it, which is not followed,
  while one that reads the name from the body around it, a closure, reads
  the parameter. A function whose parameter is annotated a single number, a
  text or a record says it takes no array, and is not followed. A ``tuple``
  of a fixed length at the top of the annotation (``tuple[float, float]``,
  a pair of limits) is a record of numbers whose arity the annotation
  states, not an array input;
* a parameter the body converts item by item (``for item in contributions:
  np.asarray(item)``) need not take ``ArrayLike``, but the item type of each
  sequence it is annotated takes what numpy converts of one item: a number,
  a sequence of numbers of any length, or ``ArrayLike``. An item type that
  holds several numbers only in an array or in a ``tuple`` of a fixed
  length (``Sequence[tuple[float, float]]``, ``tuple[NDArray, NDArray]``)
  refuses the list the conversion takes, and fails;
* a parameter that reaches a validator taking a numpy integer
  (``require_count``, ``require_band_fraction``, ``is_class_designation``),
  an ``isinstance`` check that lets one through (``not isinstance(n, (int,
  np.integer))`` before a ``raise``; one that also names a float reads a
  real number, not a count), or a public function whose own parameter is
  annotated ``np.integer``, admits ``np.integer[Any]`` (``int |
  np.integer[Any]``, ``BandFraction | np.integer[Any]``); one an
  ``isinstance`` check lets ``np.bool_`` through admits ``np.bool_``
  (``bool | np.bool_``). It is followed as a conversion is, a validation one
  item at a time holding each item type to it: an item a loop takes, an
  unpacking binds (``ny, nx = shape``) or an index reads (``shape[0]``), and
  an element of an item unpacked or indexed in turn (``ix, iy = entry``),
  read against the elements of the annotation's items. A parameter annotated a
  whole number (``int``, ``Sequence[int]``) that reaches one of the shared
  scalar checks (``require_scalar``, ``require_positive`` and their kin,
  :data:`COUNTED`), which take a numpy integer as they take an int, admits
  it too. A whole float such as ``3.0``, which ``require_count`` also takes,
  stays a leniency the annotation does not state;
* a parameter that reaches a function of :mod:`scipy.signal` that reads a
  window (``get_window``, ``welch``, ``csd``, ``stft`` and the others of
  :data:`_WINDOW_READERS`), followed through the helpers it is handed to as
  a conversion is, takes a tuple of the window's name and its parameters
  (``("kaiser", 8.6)``, ``("general_cosine", weights)``) as it takes the
  name: ``str | tuple[ArrayLike, ...]``;
* the same holds for the fields of a public record that its
  ``__post_init__`` (or a method it calls on ``self``, or ``super()``'s)
  validates: by attribute, by ``getattr``, in a loop over field names (a
  name the loop skips with ``continue`` left out) or handed by name to a
  method that reads it with ``getattr``; and a value handed to a record's
  generated ``__init__``, by keyword or by position in field order, is
  followed there as ``self.<field>``. A field a result record stores a value
  of its own in holds what it stores (the int a validator returns) and keeps
  that annotation; a record a caller builds (taken by a public function, the
  results ``scripts/check_parameter_units.py`` lists as handed on left out)
  that stores one takes the numpy scalar in its constructor, a
  ``TYPE_CHECKING`` ``__init__``, or is listed in :data:`CONSTRUCTOR_EXEMPT`;
* a mapping a parameter takes is keyed by what a typed caller's ``dict``
  matches: ``Mapping`` is invariant in its key, so one keyed by ``float``
  stands beside one keyed by ``int`` in the same union (``BandMapping``),
  and one keyed by a union of several members beside one keyed by each
  member. A key of ``Literal`` choices is narrowed by the caller as a
  ``Literal`` parameter is, and is left as it stands. An overload head is
  read with the keys every head of the function offers alone, which is what
  a caller sees;
* a union of two or more mappings, one of whose key or value is not a
  plain number, text or record (a ``Literal``, a mapping, a sequence,
  ``ArrayLike`` or a union), gives a ``dict`` written in the call no type
  context: mypy reads such a display against the type it is passed for only
  when that type holds one mapping, and otherwise on its own, a ``Literal``
  key as a ``str`` and nested mappings of two key types as ``object``, so a
  call that runs is refused. Each of those mappings is offered alone in an
  overload head, the implementation keeping the union; a head that takes
  two of them, and a union of them below the top of a parameter or in the
  field of a public record, where no head can split it, fail;
* the scalar quantities of the vocabulary (:data:`NAME_FAMILIES`: a sample
  rate ``fs``, ``volume``, ``coverage``, ``confidence``,
  ``energy_fraction``, ``fraction``) keep one family of numbers across the
  API, parameters and record fields alike: a sample rate is a ``float``
  wherever a function takes one, so the rate one function returns is the
  rate the next one takes. One of another family on purpose is listed in
  :data:`FAMILY_EXEMPT` with its reason;
* when the function is overloaded, a caller sees only the heads, so a head
  that takes such a parameter narrower than ``ArrayLike`` (or than the
  numpy scalar) fails as well, unless it takes it as a type parameter:
  that is a head that tells the shape of its argument apart (rule A57),
  beside a last head that takes ``ArrayLike``; a head that a ``None``
  selects takes no number;
* a parameter whose annotation holds ``list``, ``dict`` or ``set``
  anywhere, at the top or inside (``Mapping[str, dict[str, str]]``),
  fails whatever the body does, on the implementation and on every head:
  each is invariant, so a typed caller's ``list[int]`` or
  ``dict[str, int]`` is refused, and none of them takes a tuple or a
  read-only mapping. ``Sequence``, ``Mapping`` and ``AbstractSet`` say
  what the body reads, and ``ArrayLike`` what it converts.

Annotations are read through the package's type aliases and the imports
that bring them in, as ``scripts/check_return_overloads.py`` reads them
(an alias of an alias, a renamed import, a type parameter's bound), so a
parameter typed with an alias is held to what the alias stands for. A
parameter of a dataclass's generated ``__init__`` is a field, which the
record's own contract governs, and is not read by the array part.

:data:`EXEMPT` is the escape hatch of the array part, keyed by file,
qualified function and parameter, each with its reason; an entry that
covers nothing fails the check too, as one of :data:`FAMILY_EXEMPT` or
:data:`CONSTRUCTOR_EXEMPT` does. An ``isinstance`` check whose branch only
raises, after any assignments that build its message, keeps out what it
names. A copy of the package read elsewhere (the scratch tree a defect
is put into to see the check fail) names its files as the repository does,
so the exemptions read it the same way.

Static and dependency-free, so it runs on its own.
"""

from __future__ import annotations

import argparse
import ast
import copy
import functools
import pathlib
import sys
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

import check_return_overloads as overloads
from ast_scan import ROOT, python_files

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        Collection,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )

#: Where the package lives; the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"

#: The script whose ``RECORD_AXIS_EXEMPT`` and ``HANDED_ON_RESULTS`` name the
#: results one public function hands whole to another.
UNITS_GUARD = ROOT / "scripts" / "check_parameter_units.py"

#: The tables of that script that name a handed-on result.
_HANDED_ON_TABLES = frozenset({"RECORD_AXIS_EXEMPT", "HANDED_ON_RESULTS"})

#: A key of those tables: the module and the qualified name of the record.
_HANDED_ON_KEY = 2

#: Public parameters held narrower on purpose, keyed by file, qualified
#: function and parameter, each with the reason.
EXEMPT: dict[tuple[str, str, str], str] = {
    ("src/phonometry/io/_sidecar.py", "write_sidecar", "channel_labels"): (
        "names the two containers the sidecar takes, a tuple or a list of "
        "texts, so that one text, which is a Sequence[str] too, stays a type "
        "error as it is a ValueError when the call runs; list is invariant "
        "only in its item, and a label is str"
    ),
    (
        "src/phonometry/vibration/human/exposure.py",
        "daily_vibration_exposure",
        "labels",
    ): (
        "a list or a tuple of operation labels, named so that one text, "
        "which is a Sequence[str] too, stays a type error; list is "
        "invariant only in its item, and a label is str"
    ),
}


#: Fields of caller-built records that store the value their check returns,
#: whose constructor does not say yet that it takes the numpy scalar, keyed by
#: file, record and field, each with the reason. Every such record declares
#: its constructor (a ``TYPE_CHECKING`` ``__init__``), so none is listed.
CONSTRUCTOR_EXEMPT: dict[tuple[str, str, str], str] = {}

#: How many calls deep a parameter handed on is followed.
DEPTH = 6

#: How many containers deep the items of an annotation are read
#: (``Sequence[Sequence[float]]`` is two).
_NESTING = 4

#: How many members of one annotation are read for an invariant container,
#: a bound that keeps an alias that names itself from reading forever.
_MEMBERS_READ = 200

#: How many classes up a class hierarchy a method is looked for.
_HIERARCHY = 8

#: The type numpy gives for what it converts to an array.
_ARRAY_LIKE = frozenset(
    {
        "numpy.typing.ArrayLike",
        "numpy._typing.ArrayLike",
        "numpy._typing._array_like.ArrayLike",
    }
)

#: Annotations that admit anything, an array-like among it.
_ANYTHING = frozenset({"typing.Any", "typing_extensions.Any", "builtins.object"})

#: The containers whose element type is invariant, by every spelling.
_INVARIANT = frozenset(
    {
        "builtins.list",
        "builtins.dict",
        "builtins.set",
        "typing.List",
        "typing.Dict",
        "typing.Set",
        "typing.DefaultDict",
        "typing.OrderedDict",
        "collections.defaultdict",
        "collections.OrderedDict",
    }
)

#: Containers of several values, whose items say what each value is.
_CONTAINERS = frozenset(
    {
        "builtins.list",
        "builtins.tuple",
        "builtins.set",
        "builtins.frozenset",
        "typing.List",
        "typing.Tuple",
        "typing.Set",
        "typing.FrozenSet",
        "typing.Sequence",
        "typing.Iterable",
        "typing.Collection",
        "typing.MutableSequence",
        "typing.AbstractSet",
        "collections.abc.Sequence",
        "collections.abc.Iterable",
        "collections.abc.Collection",
        "collections.abc.MutableSequence",
        "collections.abc.Set",
    }
)

#: The fixed-length tuple, by both spellings.
_TUPLES = frozenset({"builtins.tuple", "typing.Tuple"})

#: The numbers a sequence of numbers holds: the scalars of the return
#: gate, without the text and the ``Literal`` choices.
_NUMBERS = overloads._SCALARS - {
    "builtins.str",
    "typing.Literal",
    "typing_extensions.Literal",
    "numpy.str_",
    "numpy.bytes_",
    "numpy.void",
    "numpy.object_",
    "numpy.character",
    "numpy.flexible",
}

#: The numpy functions that take any array-like, and which of their
#: positional arguments it is (``None``: every one of them), with the
#: keyword that names it.
_CONVERTERS: dict[str, tuple[int | None, str | None]] = {
    "numpy.asarray": (0, "a"),
    "numpy.asanyarray": (0, "a"),
    "numpy.asarray_chkfinite": (0, "a"),
    "numpy.array": (0, "object"),
    "numpy.ascontiguousarray": (0, "a"),
    "numpy.asfortranarray": (0, "a"),
    "numpy.ravel": (0, "a"),
    "numpy.broadcast_to": (0, "array"),
    "numpy.atleast_1d": (None, None),
    "numpy.atleast_2d": (None, None),
    "numpy.atleast_3d": (None, None),
    "numpy.broadcast_arrays": (None, None),
}

#: Dunder methods a caller calls with arguments of its own.
_CALLED_DUNDERS = frozenset({"__init__", "__new__", "__call__"})

#: The builtins whose result holds what their one argument holds: a copy
#: ``list(x)`` of a parameter is the parameter.
_COPIES = frozenset({"list", "tuple", "sorted"})

#: The builtins a loop reads the items of their first argument through, in
#: its order or another: ``for x in sorted(xs)`` takes the items of ``xs``.
_ORDERS = frozenset({"sorted", "reversed", "iter", "list", "tuple"})

#: The names a loop over ``enumerate(xs)`` unpacks: the index and the item.
_INDEXED = 2

#: The comprehensions, each a scope of its own for the names its loops take.
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)

#: What opens a scope of its own: a name it binds (a parameter, an
#: assignment, a loop variable) is another variable than the enclosing
#: body's name of the same spelling.
_SCOPES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.ClassDef,
    *_COMPREHENSIONS,
)

#: The names a method reads its own fields through.
_OWNERS = frozenset({"self", "cls"})

#: The arguments of ``getattr(self, "name")``: the object and the name.
_GETATTR = 2

#: The numpy integers, abstract and sized, by every name: what an
#: ``isinstance`` check that admits a numpy integer names.
_NUMPY_INTEGERS = frozenset(
    name
    for name in overloads._SCALARS
    if name.startswith(("numpy.int", "numpy.uint"))
    or name
    in {
        "numpy.integer",
        "numpy.signedinteger",
        "numpy.unsignedinteger",
        "numpy.byte",
        "numpy.short",
        "numpy.long",
        "numpy.longlong",
        "numpy.ubyte",
        "numpy.ushort",
        "numpy.ulong",
        "numpy.ulonglong",
    }
)

#: The numpy truth value, by both its names.
_NUMPY_BOOLS = frozenset({"numpy.bool_", "numpy.bool"})

#: The protocols every numpy integer satisfies, which admit one as they stand.
_INDEX_PROTOCOLS = frozenset(
    {
        "typing.SupportsIndex",
        "typing.SupportsInt",
        "typing_extensions.SupportsIndex",
        "typing_extensions.SupportsInt",
    }
)

#: The validators of the package that take a numpy integer as a count or a
#: band fraction, by their name below the package, and which argument of
#: theirs the value is: ``require_count(n, "n")``.
_INTEGER_VALIDATORS: dict[str, tuple[int | None, str | None]] = {
    "_internal.validation.require_count": (0, "value"),
    "_internal.validation.require_band_fraction": (0, "value"),
    "_internal.validation.is_class_designation": (0, "value"),
}


@dataclass(frozen=True)
class Target:
    """What one part of the rule follows a parameter to.

    The array part ends at a conversion; a scalar part ends where the body
    admits a numpy scalar of its kind: a validator of the package that takes
    one, or an ``isinstance`` check that names one and lets it through.
    """

    #: The kind a route ends in: ``"array"``, ``"integer"`` or ``"flag"``.
    kind: str
    #: The calls that end a route, by dotted name (below the package for the
    #: package's own), with the argument that is the value: its position
    #: (``None``: every one of them) and its keyword.
    calls: dict[str, tuple[int | None, str | None]]
    #: The numpy types an ``isinstance`` check names to admit the kind.
    accepted: frozenset[str] = frozenset()
    #: Whether the calls are named below the package (``_internal...``).
    relative: bool = False
    #: The types that make an ``isinstance`` check one of another kind: a
    #: check that admits a float with a numpy integer reads a real number,
    #: not a count.
    excluded: frozenset[str] = frozenset()
    #: The types that end a route where a function of the package annotates
    #: the parameter it is handed to with one of them: ``ArrayLike`` for the
    #: array part, the numpy scalar for a scalar part.
    typed: frozenset[str] = frozenset()
    #: The numpy scalar the parameter then admits, as :data:`_ADMITS` keys
    #: it, when it is not named by the kind itself.
    scalar: str = ""
    #: Whether only a parameter annotated a whole number is held to it.
    whole_only: bool = False

    @property
    def admitted(self) -> str:
        """The numpy scalar a parameter that reaches the end of a route admits."""
        return self.scalar or self.kind


#: The array part: a conversion of any array-like.
CONVERSION = Target("array", _CONVERTERS, typed=_ARRAY_LIKE)

#: A count, a band fraction or a class designation a validator takes a
#: numpy integer for, or an ``isinstance`` check lets one through.
INTEGER = Target(
    "integer",
    _INTEGER_VALIDATORS,
    accepted=_NUMPY_INTEGERS | {"numbers.Integral"},
    relative=True,
    typed=frozenset({"numpy.integer"}),
    excluded=frozenset(
        {
            "builtins.float",
            "builtins.complex",
            "numpy.number",
            "numpy.inexact",
            "numpy.floating",
            "numpy.float64",
            "numpy.float32",
            "numbers.Real",
            "numbers.Number",
        }
    ),
)

#: A flag an ``isinstance`` check lets ``np.bool_`` through for.
FLAG = Target("flag", {}, accepted=_NUMPY_BOOLS, typed=_NUMPY_BOOLS)

#: The shared scalar guards of the package: each reads its value as one
#: number, and takes a numpy integer as it takes an int.
_SCALAR_GUARDS: dict[str, tuple[int | None, str | None]] = {
    f"_internal.validation.{name}": (0, "value")
    for name in (
        "require_scalar",
        "require_real",
        "require_positive",
        "require_finite",
        "require_non_negative",
        "require_above_absolute_zero",
        "require_fraction",
    )
}

#: A whole number a scalar guard reads, with no count validator on its way:
#: an order, an index or a count the body takes the numpy integer of as it
#: takes an int. A real number the same guard reads is not held to it: a
#: ``float`` parameter takes the ``np.float64`` numpy code hands a real over
#: as, which is a ``float``.
COUNTED = Target(
    "count",
    _SCALAR_GUARDS,
    relative=True,
    scalar="integer",
    whole_only=True,
)

#: The scalar parts of the rule.
SCALAR_TARGETS = (INTEGER, FLAG, COUNTED)

#: The functions of :mod:`scipy.signal` that read a window specification, and
#: which of their arguments it is. Each takes a window name or a tuple of a
#: name and its parameters (``("kaiser", 8.6)``); ``firwin`` and ``firwin2``
#: take it by keyword only, so their position is one no call fills.
_WINDOW_READERS: dict[str, tuple[int | None, str | None]] = {
    "scipy.signal.get_window": (0, "window"),
    "scipy.signal.windows.get_window": (0, "window"),
    "scipy.signal.welch": (2, "window"),
    "scipy.signal.csd": (3, "window"),
    "scipy.signal.periodogram": (2, "window"),
    "scipy.signal.coherence": (3, "window"),
    "scipy.signal.spectrogram": (2, "window"),
    "scipy.signal.stft": (2, "window"),
    "scipy.signal.istft": (2, "window"),
    "scipy.signal.check_COLA": (0, "window"),
    "scipy.signal.check_NOLA": (0, "window"),
    "scipy.signal.resample_poly": (4, "window"),
    "scipy.signal.firwin": (3, "window"),
    "scipy.signal.firwin2": (4, "window"),
    "scipy.signal.ShortTimeFFT.from_window": (0, "win_param"),
}

#: The window part: a specification :mod:`scipy.signal` reads, which takes a
#: tuple of a window's name and its parameters as it takes the name.
WINDOW = Target("window", _WINDOW_READERS)

#: What each scalar kind's annotation must name to admit the numpy scalar.
_ADMITS: dict[str, frozenset[str]] = {
    "integer": frozenset({"numpy.integer"}) | _INDEX_PROTOCOLS,
    "flag": _NUMPY_BOOLS,
}

#: How a finding names the numpy scalar of each kind.
_SCALAR_NAMES = {"integer": "np.integer[Any]", "flag": "np.bool_"}

#: What a parameter that may hold one number is annotated with: a function
#: whose parameter is typed otherwise (a text, a record, an array) is not
#: followed by a scalar part.
_SCALAR_HOLDERS = (
    _NUMBERS
    | _INDEX_PROTOCOLS
    | _ARRAY_LIKE
    | _ANYTHING
    | {
        "typing.SupportsFloat",
        "typing_extensions.SupportsFloat",
        "numbers.Number",
        "numbers.Real",
        "numbers.Integral",
        "typing.Literal",
        "typing_extensions.Literal",
    }
)


@dataclass(frozen=True)
class Finding:
    """A public parameter annotated narrower than what its body accepts."""

    path: str
    line: int
    function: str
    parameter: str
    problem: str
    #: The part of the rule it breaks: ``"array"`` (a conversion, or an
    #: invariant container), ``"integer"`` or ``"flag"`` (a numpy scalar),
    #: ``"key"`` (a mapping's key), ``"context"`` (a union of mappings a
    #: written ``dict`` is not read against), ``"window"`` (a window SciPy
    #: reads) or ``"name"`` (a quantity's family).
    part: str = "array"
    #: Whether it is a field a caller-built record stores the validated value
    #: in, which its constructor, not its field, is to admit.
    constructor: bool = False

    @property
    def key(self) -> tuple[str, str, str]:
        """The file, the qualified function and the parameter."""
        return self.path, self.function, self.parameter


@functools.cache
def handed_on_results(script: pathlib.Path = UNITS_GUARD) -> frozenset[str]:
    """The results one public function hands whole to another, by dotted name.

    Read from the keys of the tables of *script* that list them, so that the
    two checks class a record the same way: a result a caller does not build
    is no input record, whatever function takes it.
    """
    tree = ast.parse(script.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in tree.body:
        assigned = overloads._assigned(node)
        if not (
            assigned is not None
            and assigned[0] in _HANDED_ON_TABLES
            and isinstance(assigned[1], ast.Dict)
        ):
            continue
        for key in assigned[1].keys:
            parts = key.elts if isinstance(key, ast.Tuple) else []
            texts = [
                part.value
                for part in parts
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            ]
            if len(texts) == len(parts) == _HANDED_ON_KEY:
                found.add(".".join(texts))
    return frozenset(found)


def _items(node: ast.expr) -> list[ast.expr]:
    """The arguments of a subscript, one or several."""
    if not isinstance(node, ast.Subscript):
        return []
    inner = node.slice
    return list(inner.elts) if isinstance(inner, ast.Tuple) else [inner]


class Annotations:
    """How the package's annotations read, through its aliases and imports."""

    def __init__(self, package: overloads.Package) -> None:
        self.package = package
        #: Every class of the package, by its dotted name, with its module.
        self.classes: dict[str, tuple[str, ast.ClassDef]] = {}
        for module, tree in package.trees.items():
            for node in overloads._statements(tree.body):
                if isinstance(node, ast.ClassDef):
                    self.classes[f"{module}.{node.name}"] = (module, node)

    def members(
        self,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr] | None = None,
    ) -> list[tuple[str, ast.expr]]:
        """The members of an annotation, aliases and type parameters expanded."""
        found: list[tuple[str, ast.expr]] = []
        for where, member in self.package.members(module, node):
            if (
                bounds
                and isinstance(member, ast.Name)
                and member.id in bounds
                and where == module
            ):
                found.extend(self.members(where, bounds[member.id]))
            else:
                found.append((where, member))
        return found

    def resolve(self, module: str, node: ast.expr) -> str | None:
        """The dotted name a member's base stands for."""
        base = node.value if isinstance(node, ast.Subscript) else node
        return self.package.resolve(module, base)

    def admits_array_like(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation lets any array-like through: ``ArrayLike``, or anything."""
        return any(
            self.resolve(where, member) in _ARRAY_LIKE | _ANYTHING
            for where, member in self.members(module, node, bounds)
        )

    def names(
        self,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr],
        wanted: frozenset[str],
    ) -> str | None:
        """The member of an annotation that is one of *wanted*, as written, if one is."""
        for where, member in self.members(module, node, bounds):
            if self.resolve(where, member) in wanted:
                return ast.unparse(member)
        return None

    def names_array_like(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation says ``ArrayLike``: what the function converts."""
        return any(
            self.resolve(where, member) in _ARRAY_LIKE
            for where, member in self.members(module, node, bounds)
        )

    def may_hold_numbers(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation leaves room for several numbers.

        None at all, ``Any`` or ``object``, an unbound type parameter, or a
        member that holds several numbers; a function whose parameter is
        typed a single number, a text or a record of the package is not
        followed, since its annotation says it takes no array.
        """
        if node is None:
            return True
        for where, member in self.members(module, node, bounds):
            dotted = self.resolve(where, member)
            if dotted in _ANYTHING or dotted is None:
                return True
            if self._holds_numbers(where, member, depth=0, top=False):
                return True
        return False

    def may_hold_a_number(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation leaves room for one number.

        None at all, an unbound type parameter, or a member that is a number,
        a protocol a number satisfies, ``ArrayLike``, ``Any`` or a
        ``Literal``; a function whose parameter is typed a text, a record or
        an array is not followed by a scalar part.
        """
        if node is None:
            return True
        return any(
            dotted is None or dotted in _SCALAR_HOLDERS
            for dotted in (
                self.resolve(where, member)
                for where, member in self.members(module, node, bounds)
                if not _is_none(member)
            )
        )

    def may_hold_scalars(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation leaves room for one number, or for one in each item.

        What a scalar part follows a value into: a parameter or a field that
        may be one number, a sequence whose items may each be one, which a
        body validates one item at a time (``for i in omitted: require_count(i,
        ...)``), or a sequence of sequences whose elements may, which a body
        unpacks item by item (``ix, iy = entry``).
        """
        return self._scalars_within(module, node, bounds, depth=0)

    def _scalars_within(
        self,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr],
        *,
        depth: int,
    ) -> bool:
        if self.may_hold_a_number(module, node, bounds):
            return True
        if depth >= _DEEPEST:
            return False
        return any(
            self.resolve(where, member) in _CONTAINERS
            and any(
                self._scalars_within(where, item, {}, depth=depth + 1)
                for item in _items(member)
                if not _is_ellipsis(item)
            )
            for where, member in self.members(module, node, bounds)
        )

    def admits_window(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> bool:
        """Whether an annotation lets a window's ``(name, parameters)`` tuple through.

        A ``tuple``, ``ArrayLike`` (a tuple of a text and numbers is one) or
        anything; no annotation at all admits it too.
        """
        if node is None:
            return True
        return any(
            self.resolve(where, member) in _TUPLES | _ARRAY_LIKE | _ANYTHING
            for where, member in self.members(module, node, bounds)
        )

    def admits_scalar(
        self,
        kind: str,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr],
    ) -> bool:
        """Whether an annotation lets the numpy scalar of *kind* through.

        ``np.integer[Any]`` (or a protocol every numpy integer satisfies,
        ``SupportsIndex``) for an integer, ``np.bool_`` for a flag; or
        ``ArrayLike`` or anything, which take every numpy scalar. No
        annotation at all admits it too.
        """
        if node is None:
            return True
        return any(
            self.resolve(where, member) in _ADMITS[kind] | _ARRAY_LIKE | _ANYTHING
            for where, member in self.members(module, node, bounds)
        )

    def items_refusing(
        self,
        kind: str,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr],
    ) -> list[str]:
        """The item types of an annotation's sequences that refuse the numpy scalar of *kind*.

        A body that validates a parameter one item at a time (``for n in
        orders: require_count(n, ...)``) takes each item as the validator
        does. One sequence of the annotation whose items admit it is enough:
        ``Sequence[int] | Sequence[np.integer[Any]]`` takes a list of numpy
        integers as it takes a list of ints.
        """
        if node is None or self.admits_array_like(module, node, bounds):
            return []
        found: dict[str, None] = {}
        for where, member in self.members(module, node, bounds):
            if self.resolve(where, member) not in _CONTAINERS:
                continue
            refusing = [
                ast.unparse(item)
                for item in _items(member)
                if not (_is_ellipsis(item) or self.admits_scalar(kind, where, item, {}))
            ]
            if not refusing:
                return []
            found.update(dict.fromkeys(refusing))
        return list(found)

    def elements_refusing(
        self,
        kind: str,
        module: str,
        node: ast.expr | None,
        bounds: dict[str, ast.expr],
    ) -> list[str]:
        """The element types of an annotation's nested sequences that refuse the numpy scalar of *kind*.

        A body that unpacks each item of a parameter (``for entry in probes:
        ix, iy = entry``) and validates each element takes it as the
        validator does: the items of the annotation's sequences hold the
        element types :meth:`items_refusing` reads. One sequence of the
        annotation whose items all admit it in their elements is enough.
        """
        if node is None or self.admits_array_like(module, node, bounds):
            return []
        found: dict[str, None] = {}
        for where, member in self.members(module, node, bounds):
            if self.resolve(where, member) not in _CONTAINERS:
                continue
            refusing = [
                element
                for item in _items(member)
                if not _is_ellipsis(item)
                for element in self.items_refusing(kind, where, item, {})
            ]
            if not refusing:
                return []
            found.update(dict.fromkeys(refusing))
        return list(found)

    def several_numbers(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> list[str]:
        """The members of an annotation that hold several numbers.

        An array, or a container whose items are numbers or hold several
        numbers themselves (``Sequence[Sequence[float]]``).
        """
        return [
            ast.unparse(member)
            for where, member in self.members(module, node, bounds)
            if self._holds_numbers(where, member, depth=0, top=True)
        ]

    def _holds_numbers(
        self, module: str, node: ast.expr, *, depth: int, top: bool = False
    ) -> bool:
        """Whether a member holds several numbers.

        At the top of an annotation, a ``tuple`` of a fixed length
        (``tuple[float, float]``) is a record of numbers whose arity the
        annotation states, a pair of limits or a triple of dimensions, not
        an array input; inside a sequence it is a row of one.
        """
        dotted = self.resolve(module, node)
        if dotted in overloads._ARRAYS:
            return True
        if dotted not in _CONTAINERS or depth > _NESTING:
            return False
        if top and dotted in _TUPLES and not any(map(_is_ellipsis, _items(node))):
            return False
        items = [item for item in _items(node) if not _is_ellipsis(item)]
        return bool(items) and all(
            self._number_or_numbers(where, member, depth=depth + 1)
            for item in items
            for where, member in self.members(module, item)
        )

    def _number_or_numbers(self, module: str, node: ast.expr, *, depth: int) -> bool:
        dotted = self.resolve(module, node)
        return dotted in _NUMBERS or self._holds_numbers(module, node, depth=depth)

    def narrow_items(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> list[str]:
        """The item types of an annotation's sequences that take no sequence of numbers.

        A body that converts a parameter one item at a time takes, for each
        item, what numpy converts. An item type that holds several numbers
        takes a sequence of them of any length (``Sequence[float]``) or
        ``ArrayLike``; one that holds them only in an array or in a ``tuple``
        of a fixed length refuses the list the conversion takes. An item that
        is one number, a text or a record is typed as it is read, and the
        items of an array are numbers or rows of one, which no annotation
        narrows.
        """
        if node is None or self.admits_array_like(module, node, bounds):
            return []
        found: dict[str, None] = {}
        for where, member in self.members(module, node, bounds):
            if self.resolve(where, member) not in _CONTAINERS:
                continue
            for item in _items(member):
                if not (_is_ellipsis(item) or self._takes_an_item(where, item)):
                    found[ast.unparse(item)] = None
        return list(found)

    def _takes_an_item(self, module: str, item: ast.expr) -> bool:
        members = self.members(module, item)
        if any(
            self.resolve(where, m) in _ARRAY_LIKE | _ANYTHING for where, m in members
        ):
            return True
        if not any(self._holds_numbers(where, m, depth=0) for where, m in members):
            return True
        return any(self._open_numbers(where, m) for where, m in members)

    def _open_numbers(self, module: str, node: ast.expr) -> bool:
        """Whether a member is a sequence of numbers of any length."""
        if self.resolve(module, node) in _TUPLES and not any(
            map(_is_ellipsis, _items(node))
        ):
            return False
        return self.resolve(module, node) in _CONTAINERS and self._holds_numbers(
            module, node, depth=0
        )

    def named_within(
        self, module: str, node: ast.expr | None, wanted: frozenset[str]
    ) -> list[str]:
        """The members of an annotation that are one of *wanted*, at the top or inside.

        Aliases are spelt out at every level, so ``Untyped = Any`` is read as
        ``Any`` and ``Table = Dict[str, float]`` as ``typing.Dict``. The type
        parameter of a NumPy generic (``NDArray[Any]``, ``np.integer[Any]``)
        says what the array or the scalar holds, not what the value is, and
        is read past, as are the choices a ``Literal`` lists, which are
        values.
        """
        found: list[str] = []
        stack = self.members(module, node)
        seen = 0
        while stack and seen < _MEMBERS_READ:
            seen += 1
            where, member = stack.pop()
            dotted = self.resolve(where, member)
            if dotted in wanted:
                found.append(ast.unparse(member))
            if dotted in _LITERALS or (
                dotted is not None and dotted.partition(".")[0] == "numpy"
            ):
                continue
            for item in _items(member):
                for inner in item.elts if isinstance(item, ast.List) else [item]:
                    stack.extend(self.members(where, inner))
        return sorted(set(found))

    def invariant(
        self, module: str, node: ast.expr | None, bounds: dict[str, ast.expr]
    ) -> list[str]:
        """The invariant containers an annotation holds, at the top or inside."""
        found: list[str] = []
        stack = self.members(module, node, bounds)
        seen = 0
        while stack and seen < _MEMBERS_READ:
            seen += 1
            where, member = stack.pop()
            dotted = self.resolve(where, member)
            if dotted in _INVARIANT:
                found.append(ast.unparse(member))
            for item in _items(member):
                for inner in item.elts if isinstance(item, ast.List) else [item]:
                    stack.extend(self.members(where, inner))
        return sorted(set(found))


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _is_ellipsis(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _type_bounds(
    *nodes: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | None,
) -> dict[str, ast.expr]:
    """The bound (or the constraints, as a union) of each PEP 695 type parameter."""
    bounds: dict[str, ast.expr] = {}
    for node in nodes:
        for parameter in getattr(node, "type_params", None) or []:
            if not isinstance(parameter, ast.TypeVar) or parameter.bound is None:
                continue
            bound = parameter.bound
            if isinstance(bound, ast.Tuple):
                members = list(bound.elts)
                union: ast.expr = members[0]
                for member in members[1:]:
                    union = ast.BinOp(left=union, op=ast.BitOr(), right=member)
                bound = union
            bounds[parameter.name] = bound
    return bounds


def _is_type_parameter(written: ast.expr | None, own: dict[str, ast.expr]) -> bool:
    """Whether an annotation is the bare name of one of the head's type parameters."""
    return isinstance(written, ast.Name) and written.id in own


def _named(node: ast.expr | None) -> str | None:
    """The name an expression reads: a local name, or a field of ``self`` or ``cls``.

    ``self.fraction`` and ``getattr(self, "fraction")`` read the field a
    record's ``__post_init__`` validates, named ``self.fraction``. A field
    read by a name a local holds, ``getattr(self, name)``, is named
    ``self.{name}``, and so is one read off any parameter that holds the
    record (``getattr(record, name)`` in a helper the record is handed to,
    named ``record.{name}``).
    """
    if isinstance(node, ast.Name):
        return node.id
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in _OWNERS
    ):
        return f"{node.value.id}.{node.attr}"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= _GETATTR
        and isinstance(node.args[0], ast.Name)
    ):
        holder, field = node.args[0].id, node.args[1]
        if (
            holder in _OWNERS
            and isinstance(field, ast.Constant)
            and isinstance(field.value, str)
        ):
            return f"{holder}.{field.value}"
        if isinstance(field, ast.Name):
            return _by_name(holder, field.id)
    return None


def _is_super(node: ast.expr) -> bool:
    """Whether an expression is ``super()``."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "super"
    )


def _by_name(owner: str, name: str) -> str:
    """How a body names the field a local name holds the name of: ``getattr(self, name)``."""
    return f"{owner}.{{{name}}}"


def _carries(node: ast.expr | None, names: frozenset[str]) -> bool:
    """Whether an expression is one of *names*, or chooses between them."""
    named = _named(node)
    if named is not None:
        return named in names
    if isinstance(node, ast.IfExp):
        return _carries(node.body, names) or _carries(node.orelse, names)
    if isinstance(node, ast.BoolOp):
        return any(_carries(value, names) for value in node.values)
    if isinstance(node, ast.Starred | ast.NamedExpr):
        return _carries(node.value, names)
    return False


@dataclass(frozen=True)
class Bound:
    """The local names a body binds to a parameter, by what each one holds."""

    #: The value the annotation types: the parameter, a name assigned it, a
    #: copy of it (``list(x)``, ``tuple(x)``, ``sorted(x)``), a name a loop
    #: over a literal of parameters takes each of them in, and, for a
    #: vararg, each of its arguments, which its annotation types.
    whole: frozenset[str]
    #: The tuple a vararg collects, and the names bound to it.
    pack: frozenset[str]
    #: One item of a whole value, which a loop over it takes in turn, an
    #: unpacking of it binds (``ny, nx = shape``) or an index reads
    #: (``shape[0]``).
    item: frozenset[str]
    #: One element of an item, which an unpacking of the item binds (``ix,
    #: iy = entry`` for each ``entry`` of ``probes``), an index reads or a
    #: loop over the item takes.
    element: frozenset[str] = frozenset()


#: What each kind of name holds once a loop, an unpacking or an index reads
#: it item by item: a pack gives its arguments, each a whole value; a whole
#: value gives its items, and an item its elements. An element is not read
#: further.
_ITERATED = {"pack": "whole", "whole": "item", "item": "element"}

#: How deep a route reads a parameter: 0 the whole value, 1 one item of it,
#: 2 one element of an item.
_LEVELS = {"whole": 0, "pack": 0, "item": 1, "element": 2}
_DEEPEST = 2


def _indexed(node: ast.expr | None) -> ast.expr | None:
    """What a subscript by a whole-number constant indexes: ``shape`` of ``shape[0]``.

    A slice keeps the sequence it cuts, and a text indexes a mapping by a
    key, so neither reads an item.
    """
    if not isinstance(node, ast.Subscript):
        return None
    index = node.slice
    if isinstance(index, ast.UnaryOp) and isinstance(index.op, ast.USub):
        index = index.operand
    if (
        isinstance(index, ast.Constant)
        and isinstance(index.value, int)
        and not isinstance(index.value, bool)
    ):
        return node.value
    return None


def _kind(node: ast.expr | None, names: dict[str, set[str]]) -> str | None:
    """What an expression holds of the parameter, if it holds it at all.

    A copy holds what it copies, and a subscript by a whole-number constant
    one item of what it indexes.
    """
    for kind, bound in names.items():
        if _carries(node, frozenset(bound)):
            return kind
    copied = _single_argument(node, _COPIES)
    if copied is not None:
        return _kind(copied, names)
    indexed = _indexed(node)
    if indexed is None:
        return None
    whole = _kind(indexed, names)
    return _ITERATED.get(whole) if whole is not None else None


def _level(node: ast.expr | None, bound: Bound) -> int | None:
    """How deep a call argument reads the parameter: :data:`_LEVELS`, or ``None``.

    The parameter or a copy of it, one of the names bound to an item or to
    an element of one, or a subscript by a whole-number constant of any of
    them, which reads one level deeper: ``shape[0]`` is an item of
    ``shape``, and ``args[0]`` of a vararg's pack one whole argument.
    """
    if node is None:
        return None
    for names, at in (
        (bound.whole | bound.pack, 0),
        (bound.item, 1),
        (bound.element, 2),
    ):
        if names and _holds(node, names):
            return at
    indexed = _indexed(node)
    if indexed is None:
        return None
    if bound.pack and _holds(indexed, bound.pack):
        return 0
    deeper = _level(indexed, bound)
    return deeper + 1 if deeper is not None and deeper < _DEEPEST else None


def _single_argument(
    node: ast.expr | None, builtins: frozenset[str]
) -> ast.expr | None:
    """The one positional argument of a call to one of *builtins*, if it is one."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in builtins
        and len(node.args) == 1
        and not isinstance(node.args[0], ast.Starred)
    ):
        return node.args[0]
    return None


def _unpacked(
    target: ast.expr, value: ast.expr, names: dict[str, set[str]]
) -> Iterator[tuple[str, str]]:
    """The names an assignment of *value* to *target* binds, and what each holds."""
    if isinstance(target, ast.Name):
        kind = _kind(value, names)
        if kind is not None:
            yield target.id, kind
    elif (
        isinstance(target, ast.Tuple | ast.List)
        and isinstance(value, ast.Tuple | ast.List)
        and len(target.elts) == len(value.elts)
    ):
        for part, element in zip(target.elts, value.elts, strict=True):
            yield from _unpacked(part, element, names)
    elif isinstance(target, ast.Tuple | ast.List):
        # ``ny, nx = shape`` binds each item of a whole value, and ``ix, iy =
        # entry`` each element of an item.
        yield from _spread(target, _kind(value, names))


def _spread(
    target: ast.Tuple | ast.List, kind: str | None
) -> Iterator[tuple[str, str]]:
    """The names an unpacking of a value of *kind* binds, each one level deeper."""
    deeper = _ITERATED.get(kind) if kind is not None else None
    if deeper is None:
        return
    for part in target.elts:
        if isinstance(part, ast.Name):
            yield part.id, deeper


def _taken(
    target: ast.expr, source: ast.expr, names: dict[str, set[str]]
) -> Iterator[tuple[str, str]]:
    """The names a loop over *source* binds in *target*, and what each holds.

    A loop over a literal (``for v in (a, b)``) takes each element as it is
    written, a parameter itself; ``enumerate``, ``zip``, ``sorted`` and their
    kin hand on the items of what they are given; any other loop over a name
    bound to the parameter takes one item of it at a time.
    """
    if isinstance(source, ast.Tuple | ast.List):
        for element in source.elts:
            yield from _unpacked(target, element, names)
        return
    if isinstance(source, ast.Call) and isinstance(source.func, ast.Name):
        builtin, arguments = source.func.id, source.args
        parts = target.elts if isinstance(target, ast.Tuple | ast.List) else []
        if builtin == "enumerate" and arguments and len(parts) == _INDEXED:
            yield from _taken(parts[1], arguments[0], names)
            return
        if builtin == "zip" and arguments and len(parts) == len(arguments):
            for part, iterable in zip(parts, arguments, strict=True):
                yield from _taken(part, iterable, names)
            return
        if builtin in _ORDERS and arguments:
            yield from _taken(target, arguments[0], names)
            return
    kind = _kind(source, names)
    if kind not in _ITERATED:
        return
    if isinstance(target, ast.Name):
        yield target.id, _ITERATED[kind]
    elif isinstance(target, ast.Tuple | ast.List):
        # ``for ix, iy in probes`` unpacks each item it takes.
        yield from _spread(target, _ITERATED[kind])


def _enclosing_parts(scope: ast.AST) -> list[ast.AST]:
    """What a nested scope evaluates where it is written, outside its own scope.

    A function's decorators and default values, a class's decorators and
    bases, and the iterable of a comprehension's first loop.
    """
    if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
        decorators = [] if isinstance(scope, ast.Lambda) else scope.decorator_list
        defaults = [value for value in scope.args.kw_defaults if value is not None]
        return [*decorators, *scope.args.defaults, *defaults]
    if isinstance(scope, ast.ClassDef):
        return [*scope.decorator_list, *scope.bases, *scope.keywords]
    if isinstance(scope, _COMPREHENSIONS):
        return [scope.generators[0].iter]
    return []


def _own_parts(scope: ast.AST) -> list[ast.AST]:
    """What a scope evaluates in itself: a body, or a comprehension's result, tests and later loops."""
    if isinstance(scope, ast.Lambda):
        return [scope.body]
    if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return list(scope.body)
    if isinstance(scope, _COMPREHENSIONS):
        first, *later = scope.generators
        results = (
            [scope.key, scope.value] if isinstance(scope, ast.DictComp) else [scope.elt]
        )
        return [*results, *first.ifs, *later]
    return []


def _scope_nodes(scope: ast.AST) -> tuple[list[ast.AST], list[ast.AST]]:
    """The nodes a scope evaluates itself, in ``ast.walk`` order, and the scopes nested in it."""
    own: list[ast.AST] = []
    nested: list[ast.AST] = []
    todo = deque(_own_parts(scope))
    while todo:
        node = todo.popleft()
        if isinstance(node, _SCOPES):
            nested.append(node)
            todo.extend(_enclosing_parts(node))
            continue
        own.append(node)
        todo.extend(ast.iter_child_nodes(node))
    return own, nested


def _own_bindings(
    scope: ast.AST, own: list[ast.AST], nested: list[ast.AST]
) -> frozenset[str]:
    """The names a nested scope binds for itself, which hide the enclosing body's.

    A function's or a lambda's parameters and the names its body assigns,
    loops over, imports or defines, less those it declares ``nonlocal`` or
    ``global``; a class body's own names; the names a comprehension's
    loops take.
    """
    if isinstance(scope, _COMPREHENSIONS):
        return frozenset(
            node.id
            for loop in scope.generators
            for node in ast.walk(loop.target)
            if isinstance(node, ast.Name)
        )
    names: set[str] = set()
    if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
        arguments = scope.args
        names.update(
            argument.arg
            for argument in (
                *arguments.posonlyargs,
                *arguments.args,
                *arguments.kwonlyargs,
                arguments.vararg,
                arguments.kwarg,
            )
            if argument is not None
        )
    declared: set[str] = set()
    for node in own:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del):
            names.add(node.id)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.Global | ast.Nonlocal):
            declared.update(node.names)
    names.update(
        inner.name
        for inner in nested
        if isinstance(inner, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    )
    return frozenset(names - declared)


def _close(own: list[ast.AST], names: dict[str, set[str]]) -> None:
    """Add to *names* every local name the nodes of one scope bind to the parameter."""
    statements = [
        child
        for child in own
        if isinstance(
            child,
            ast.Assign | ast.AnnAssign | ast.For | ast.AsyncFor | ast.comprehension,
        )
    ]
    changed = True
    while changed:
        changed = False
        for child in statements:
            if isinstance(child, ast.Assign):
                found = [
                    pair
                    for target in child.targets
                    for pair in _unpacked(target, child.value, names)
                ]
            elif isinstance(child, ast.AnnAssign) and child.value is not None:
                found = list(_unpacked(child.target, child.value, names))
            elif isinstance(child, ast.For | ast.AsyncFor | ast.comprehension):
                found = list(_taken(child.target, child.iter, names))
            else:
                continue
            for local, kind in found:
                if local not in names[kind]:
                    names[kind].add(local)
                    changed = True


def _visible(name: str, hidden: frozenset[str]) -> bool:
    """Whether a name bound to the parameter reads it in a nested scope that binds *hidden* for itself.

    ``self.n_tubes`` reads the field while ``self`` is the enclosing body's,
    and ``getattr(self, name)`` while ``name`` is too.
    """
    owner, _, field = name.partition(".")
    if owner in hidden:
        return False
    return not (field.startswith("{") and field[1:-1] in hidden)


#: How a scope splits into the nodes it evaluates itself and the scopes
#: nested in it (:func:`_scope_nodes`).
type Splitter = Callable[[ast.AST], tuple[list[ast.AST], list[ast.AST]]]


@dataclass(frozen=True)
class Reading:
    """One parameter read through the scopes of a body."""

    #: The parameter, or a field of the record a method reads (``self.n_tubes``).
    name: str
    #: The texts a constant of the module holds, a tuple of field names.
    texts: Callable[[ast.expr], tuple[str, ...]]
    #: How a scope splits, read once per scope by a reader of several names.
    split: Splitter

    def by_name(self, loops: list[ast.AST], names: dict[str, set[str]]) -> set[str]:
        """The names ``getattr(self, name)`` reads the field under in the loops of one scope.

        A loop over field names that holds the field's (``for name in
        ("n_tubes", ...)``, or over a constant of the module that holds
        them, read by :attr:`texts`) binds ``getattr(self, name)`` to it,
        where the field is the enclosing body's.
        """
        owner, _, field = self.name.partition(".")
        if (
            owner not in _OWNERS
            or not field
            or field.startswith("{")
            or self.name not in names["whole"]
        ):
            return set()
        return {
            _by_name(owner, loop.target.id)
            for loop in loops
            if isinstance(loop, ast.For | ast.AsyncFor | ast.comprehension)
            and isinstance(loop.target, ast.Name)
            and field in _field_names(loop.iter, self.texts)
            and not _passed_over(loop, loop.target.id, field)
        }


def _scoped(
    scope: ast.AST,
    names: dict[str, set[str]],
    reading: Reading,
    outside: dict[str, set[str]] | None = None,
) -> Iterator[tuple[ast.Call, Bound]]:
    """Each call of a scope and of its nested scopes, with the names bound to the parameter there.

    A name a nested scope binds for itself (a parameter of a nested
    function or lambda, a name its body assigns, a comprehension's loop
    variable) is another variable there than the enclosing body's name of
    the same spelling, and is not the parameter; a name it reads from the
    enclosing body, a closure, is. The scopes nested in a class body read
    the scope around the class (*outside*), not the class's own names.
    """
    own, nested = reading.split(scope)
    first = [scope.generators[0]] if isinstance(scope, _COMPREHENSIONS) else []
    names["whole"].update(reading.by_name([*first, *own], names))
    _close(own, names)
    bound = Bound(
        whole=frozenset(names["whole"]),
        pack=frozenset(names["pack"]),
        item=frozenset(names["item"]),
        element=frozenset(names["element"]),
    )
    for node in own:
        if isinstance(node, ast.Call):
            yield node, bound
    around = (
        outside if isinstance(scope, ast.ClassDef) and outside is not None else names
    )
    for inner in nested:
        hidden = _own_bindings(inner, *reading.split(inner))
        seeds = {
            kind: {value for value in values if _visible(value, hidden)}
            for kind, values in around.items()
        }
        if isinstance(inner, _COMPREHENSIONS):
            first_loop = inner.generators[0]
            for local, kind in _taken(first_loop.target, first_loop.iter, names):
                seeds[kind].add(local)
        yield from _scoped(inner, seeds, reading, names)


def _bound(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    *,
    vararg: bool,
    texts: Callable[[ast.expr], tuple[str, ...]] = lambda _node: (),
    split: Splitter = _scope_nodes,
) -> list[tuple[ast.Call, Bound]]:
    """Each call of a body, with the local names bound to parameter *name* where it is made.

    For a field, ``self.n_tubes``, a loop over field names that holds its
    name binds ``getattr(self, name)`` to it (:meth:`Reading.by_name`).
    *split* is how a scope splits (:func:`_scope_nodes`), which a reader of
    several names of one body reads once per scope.
    """
    names: dict[str, set[str]] = {
        "whole": set(),
        "pack": set(),
        "item": set(),
        "element": set(),
    }
    names["pack" if vararg else "whole"].add(name)
    return list(_scoped(node, names, Reading(name, texts, split)))


def _passed_over(
    loop: ast.For | ast.AsyncFor | ast.comprehension, target: str, field: str
) -> bool:
    """Whether a loop over field names skips *field* before it reads it.

    ``for name in _FEATURES: if value is None or name == "n_level_ranges":
    continue`` reads every feature but that one: an ``if`` of the loop's body
    whose branch is ``continue`` and whose test, or one alternative of an
    ``or``, compares the loop's name to the field's.
    """
    if isinstance(loop, ast.comprehension):
        return False
    for statement in loop.body:
        if not (
            isinstance(statement, ast.If)
            and len(statement.body) == 1
            and isinstance(statement.body[0], ast.Continue)
        ):
            continue
        test = statement.test
        tests = (
            test.values
            if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or)
            else [test]
        )
        if any(
            isinstance(alternative, ast.Compare)
            and isinstance(alternative.left, ast.Name)
            and alternative.left.id == target
            and len(alternative.ops) == 1
            and isinstance(alternative.ops[0], ast.Eq)
            and isinstance(alternative.comparators[0], ast.Constant)
            and alternative.comparators[0].value == field
            for alternative in tests
        ):
            return True
    return False


def _field_names(
    node: ast.expr, texts: Callable[[ast.expr], tuple[str, ...]]
) -> tuple[str, ...]:
    """The texts a loop takes in turn: a literal of them, or a constant that holds them."""
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return tuple(
            element.value
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        )
    return texts(node)


def _holds(node: ast.expr, names: frozenset[str]) -> bool:
    """Whether a call argument is one of *names*, or a copy of one."""
    copied = _single_argument(node, _COPIES)
    return _carries(node, names) or (copied is not None and _carries(copied, names))


def _positional(
    node: ast.FunctionDef | ast.AsyncFunctionDef, *, bound: bool
) -> list[ast.arg]:
    """The parameters a call fills by position, ``self`` or ``cls`` left out when bound."""
    every = [*node.args.posonlyargs, *node.args.args]
    return every[1:] if bound and every else every


def _is_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
        for decorator in node.decorator_list
    )


class Reader:
    """Follows a parameter from a public function to where its body admits it."""

    def __init__(
        self, package: overloads.Package, handed_on: frozenset[str] | None = None
    ) -> None:
        self.package = package
        self.annotations = Annotations(package)
        #: The results one public function hands whole to another: no input
        #: records, though a public function takes them.
        self.handed_on = handed_on if handed_on is not None else handed_on_results()
        #: The package's own top-level name, which names its validators.
        self.root = min(package.trees, key=len).split(".")[0] if package.trees else ""
        self._binding: dict[tuple[int, str, bool], list[tuple[ast.Call, Bound]]] = {}
        self._scopes: dict[int, tuple[list[ast.AST], list[ast.AST]]] = {}
        self._rebound: dict[int, frozenset[str]] = {}
        self._calls: dict[int, list[ast.Call]] = {}
        self._refusing: dict[int, frozenset[int]] = {}
        self._memo: dict[tuple[str, str, str, str], list[tuple[str, int, int]]] = {}
        self._active: set[tuple[str, str, str, str]] = set()
        self._cut = False
        self._public: frozenset[str] | None = None
        self._public_records: frozenset[str] | None = None
        self._inputs: frozenset[str] | None = None

    def _bounds(self, function: overloads.Function) -> dict[str, ast.expr]:
        owner = (
            self.annotations.classes.get(
                f"{function.module}.{function.owner.split('.')[-1]}"
            )
            if function.owner
            else None
        )
        return _type_bounds(function.implementation, owner[1] if owner else None)

    def _method(self, owner: str, name: str, depth: int = 0) -> str | None:
        """A method a class defines or takes from a class of the package it extends."""
        dotted = f"{owner}.{name}"
        if dotted in self.package.functions or depth > _HIERARCHY:
            return dotted if dotted in self.package.functions else None
        found = self.annotations.classes.get(owner)
        if found is None:
            return None
        module, node = found
        for base in node.bases:
            target = self.package.resolve(module, base)
            if target is not None and target in self.annotations.classes:
                method = self._method(target, name, depth + 1)
                if method is not None:
                    return method
        return None

    @property
    def public_names(self) -> frozenset[str]:
        """The dotted names of the public functions and methods of the package.

        A scalar part ends where a parameter is handed to one of them that
        takes the numpy scalar: the public API takes a count the same way at
        each step of a hand-off. A private helper typed widely, a resolver
        that also serves the functions of a whole-number rate, says nothing
        about what its callers take.
        """
        if self._public is None:
            self._public = frozenset(
                f"{function.module}.{function.qualname}"
                for function in public_functions(self.package)
            )
        return self._public

    def _inherited(self, owner: str, name: str) -> str | None:
        """The method ``super().name`` reaches from a class: its bases' first."""
        found = self.annotations.classes.get(owner)
        if found is None:
            return None
        module, node = found
        for base in node.bases:
            target = self.package.resolve(module, base)
            if target is not None and target in self.annotations.classes:
                method = self._method(target, name)
                if method is not None:
                    return method
        return None

    def _ends(self, target: Target) -> dict[str, tuple[int | None, str | None]]:
        """The calls that end a route of *target*, by their dotted name."""
        if not target.relative:
            return target.calls
        return {f"{self.root}.{name}": where for name, where in target.calls.items()}

    def _callee(
        self, function: overloads.Function, call: ast.Call, ends: Iterable[str]
    ) -> tuple[str, bool] | None:
        """What a call reaches: a function of the package, or one that ends a route.

        With whether the callee's first parameter is filled by the call
        itself (``self`` of a method, the instance of a constructor).
        """
        func = call.func
        if (
            isinstance(func, ast.Attribute)
            and _is_super(func.value)
            and function.owner is not None
        ):
            method = self._inherited(f"{function.module}.{function.owner}", func.attr)
            if method is None:
                return None
            node = self.package.functions[method].implementation
            return method, node is not None and not _is_static(node)
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in _OWNERS
            and function.owner is not None
        ):
            owner = f"{function.module}.{function.owner}"
            method = self._method(owner, func.attr)
            if method is None:
                return None
            node = self.package.functions[method].implementation
            return method, node is not None and not _is_static(node)
        local = (
            self.package.local_imports.get(function.implementation, {})
            if function.implementation is not None
            else {}
        )
        target = self.package.resolve(function.module, func, local)
        if target is None:
            return None
        if target in ends or target == "builtins.isinstance":
            return target, False
        if target in self.annotations.classes:
            constructor = self._method(target, "__init__")
            if constructor is not None:
                return constructor, True
            if record_fields(self.package, self.annotations, target):
                return target, True
            return None
        if target in self.package.functions:
            callee = self.package.functions[target]
            node = callee.implementation
            is_method = (
                callee.owner is not None and node is not None and not _is_static(node)
            )
            return target, is_method and isinstance(func, ast.Attribute)
        return None

    def conversion(
        self,
        function: overloads.Function,
        name: str,
        *,
        level: int = 0,
        target: Target = CONVERSION,
    ) -> str | None:
        """How parameter *name* of *function* reaches the end of a route of *target*.

        A conversion for the array part, a validator or a check that admits
        a numpy scalar for a scalar part. At *level* 1, how one item of it
        does, the body reading the parameter item by item; at level 2, how
        one element of an item does (``ix, iy = entry``).
        """
        for how, at in self._routes(function, name, 0, target):
            if at == level:
                return how
        return None

    def _bound(
        self,
        function: overloads.Function,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        name: str,
        *,
        vararg: bool,
    ) -> list[tuple[ast.Call, Bound]]:
        """Each call of a body, with the names bound to *name* where it is made, read once."""
        key = (id(node), name, vararg)
        if key not in self._binding:
            self._binding[key] = _bound(
                node,
                name,
                vararg=vararg,
                texts=lambda found: self._texts(function.module, found),
                split=self._split,
            )
        return self._binding[key]

    def _split(self, scope: ast.AST) -> tuple[list[ast.AST], list[ast.AST]]:
        """How a scope splits (:func:`_scope_nodes`), read once per scope."""
        if id(scope) not in self._scopes:
            self._scopes[id(scope)] = _scope_nodes(scope)
        return self._scopes[id(scope)]

    def rebound(self, function: overloads.Function) -> frozenset[str]:
        """The fields a method stores a value of its own in, by name.

        ``object.__setattr__(self, "n", ...)``, ``setattr(self, "n", ...)``,
        or either of them in a loop over field names (``for name in
        _FEATURES: object.__setattr__(self, name, ...)``).
        """
        node = function.implementation
        if node is None:
            return frozenset()
        if id(node) not in self._rebound:
            self._rebound[id(node)] = _rebound(
                node, lambda found: self._texts(function.module, found)
            )
        return self._rebound[id(node)]

    def _texts(self, module: str, node: ast.expr) -> tuple[str, ...]:
        """The texts a module constant holds, a tuple of field names."""
        dotted = self.package.resolve(module, node)
        if dotted is None or dotted not in self.package.constants:
            return ()
        where, value = self.package.constants[dotted]
        if isinstance(value, ast.Call) and value.args:
            value = value.args[0]
        return _field_names(value, lambda _node: ())

    def _calls_of(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
        if id(node) not in self._calls:
            self._calls[id(node)] = [
                call for call in ast.walk(node) if isinstance(call, ast.Call)
            ]
        return self._calls[id(node)]

    def _admits(
        self, function: overloads.Function, call: ast.Call, target: Target
    ) -> bool:
        """Whether an ``isinstance`` call lets the numpy scalar of *target* through.

        It names one of the types the target accepts and is not a refusal:
        a check that raises when it holds (``if isinstance(x, np.bool_):
        raise``) keeps that type out.
        """
        node = function.implementation
        if node is None or len(call.args) != _GETATTR or not target.accepted:
            return False
        named = self._type_names(function.module, call.args[1], 0)
        if not named & target.accepted or named & target.excluded:
            return False
        if id(node) not in self._refusing:
            self._refusing[id(node)] = _refusals(node)
        return id(call) not in self._refusing[id(node)]

    def _type_names(self, module: str, node: ast.expr, depth: int) -> set[str]:
        """The classes the second argument of ``isinstance`` names, constants read through."""
        if depth > _NESTING:
            return set()
        if isinstance(node, ast.Tuple | ast.List):
            return {
                name
                for element in node.elts
                for name in self._type_names(module, element, depth + 1)
            }
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return self._type_names(module, node.left, depth + 1) | self._type_names(
                module, node.right, depth + 1
            )
        dotted = self.package.resolve(module, node)
        if dotted is None:
            return set()
        if dotted in self.package.constants:
            where, value = self.package.constants[dotted]
            return self._type_names(where, value, depth + 1)
        return {dotted}

    def _routes(
        self,
        function: overloads.Function,
        name: str,
        depth: int,
        target: Target,
    ) -> Iterator[tuple[str, int]]:
        """Each way parameter *name* reaches the end of a route, and how deep it reads it.

        Only the routes that stay within :data:`DEPTH` calls of the public
        function, *depth* calls having been made to reach this one.
        """
        for how, level, hops in self._known_routes(function, name, target):
            if hops <= DEPTH - depth:
                yield how, level

    def _known_routes(
        self, function: overloads.Function, name: str, target: Target
    ) -> list[tuple[str, int, int]]:
        """Every route of one parameter, with the calls it takes, read once.

        A helper several public functions hand a value to is read once per
        part of the rule. A route that comes back to a parameter still being
        read (a recursion) ends there, as a path that visits a parameter twice
        does; what was read along it is not kept, so another way in reads it
        whole.
        """
        key = (function.module, function.qualname, name, target.kind)
        if key in self._memo:
            return self._memo[key]
        if key in self._active:
            self._cut = True
            return []
        self._active.add(key)
        outer, self._cut = self._cut, False
        found = list(self._read_routes(function, name, target))
        self._active.discard(key)
        if not self._cut:
            self._memo[key] = found
        self._cut = self._cut or outer
        return found

    def _read_routes(
        self, function: overloads.Function, name: str, target: Target
    ) -> Iterator[tuple[str, int, int]]:
        node = function.implementation
        if node is None:
            return
        vararg = node.args.vararg is not None and node.args.vararg.arg == name
        for call, bound in self._bound(function, node, name, vararg=vararg):
            given = [_level(value, bound) for value in call.args]
            named = [
                (keyword.arg, _level(keyword.value, bound))
                for keyword in call.keywords
                if keyword.arg is not None
            ]
            for level in range(_DEEPEST + 1):
                positions = [index for index, at in enumerate(given) if at == level]
                keywords = [keyword for keyword, at in named if at == level]
                if not (positions or keywords):
                    continue
                yield from self._called(
                    function, call, positions, keywords, level, target
                )
            yield from self._handed_by_name(function, call, name, target)
            yield from self._read_in_method(function, call, name, target)

    def _called(  # noqa: PLR0913
        self,
        function: overloads.Function,
        call: ast.Call,
        positions: list[int],
        keywords: list[str],
        level: int,
        target: Target,
    ) -> Iterator[tuple[str, int, int]]:
        """Where a call takes the parameter, read at *level* (:data:`_LEVELS`), leads.

        A route the callee reads one item of its own parameter along reads
        one level deeper here, as far as an element of an item.
        """
        ends = self._ends(target)
        callee = self._callee(function, call, ends)
        if callee is None:
            return
        reached, bound_self = callee
        if reached == "builtins.isinstance":
            if 0 in positions and self._admits(function, call, target):
                accepted = sorted(
                    self._type_names(function.module, call.args[1], 0) & target.accepted
                )
                shown = accepted[0].replace("numpy.", "np.")
                yield f"isinstance(..., {shown}) admits it", level, 0
            return
        if reached in ends:
            where, keyword = ends[reached]
            if where is None or where in positions or keyword in keywords:
                yield _ending(reached, target), level, 0
            return
        handed = (
            self._constructed(reached, positions, keywords, target)
            if reached in self.annotations.classes
            else self._handed(
                reached, positions, keywords, bound=bound_self, target=target
            )
        )
        for how, deeper, hops in handed:
            if level + deeper <= _DEEPEST:
                yield how, level + deeper, hops

    def _read_in_method(
        self,
        function: overloads.Function,
        call: ast.Call,
        name: str,
        target: Target,
    ) -> Iterator[tuple[str, int, int]]:
        """A field a method of the record reads for itself (``self._hold_counts()``)."""
        owner, _, field = name.partition(".")
        func = call.func
        if not (
            owner in _OWNERS
            and field
            and isinstance(func, ast.Attribute)
            and (
                (isinstance(func.value, ast.Name) and func.value.id == owner)
                or _is_super(func.value)
            )
        ):
            return
        callee = self._callee(function, call, ())
        if callee is None or callee[0] not in self.package.functions:
            return
        method = self.package.functions[callee[0]]
        for deeper, level, hops in self._known_routes(method, name, target):
            yield f"read in {method.qualname}(), {deeper}", level, hops + 1

    def stored_fields(
        self, function: overloads.Function, depth: int = 0
    ) -> frozenset[str]:
        """The fields a method, or a method of its class it calls on ``self``, stores in."""
        node = function.implementation
        if node is None or depth > _HIERARCHY:
            return frozenset()
        stored = set(self.rebound(function))
        looping = _loop_names(node, lambda found: self._texts(function.module, found))
        for call in self._calls_of(node):
            stored |= _handed_stores(self, function, call, looping)
            func = call.func
            if not (
                isinstance(func, ast.Attribute)
                and (
                    (isinstance(func.value, ast.Name) and func.value.id == "self")
                    or _is_super(func.value)
                )
            ):
                continue
            callee = self._callee(function, call, ())
            if callee is None or callee[0] not in self.package.functions:
                continue
            stored |= self.stored_fields(self.package.functions[callee[0]], depth + 1)
        return frozenset(stored)

    def _handed_by_name(
        self,
        function: overloads.Function,
        call: ast.Call,
        name: str,
        target: Target,
    ) -> Iterator[tuple[str, int, int]]:
        """A field handed by its name to a method that reads it with ``getattr``.

        ``self._check_bool("overload_latched", ...)`` hands the field
        ``self.overload_latched`` to a method whose parameter holds its name.
        A function handed the record itself reads the field off the
        parameter that holds it, by a name a parameter holds or by each name
        of a vararg it loops over: ``_hold_cells(self, "ix", "iy")`` reads
        ``getattr(record, name)`` for each ``name`` of ``names``.
        """
        owner, _, field = name.partition(".")
        if owner not in _OWNERS or not field or field.startswith("{"):
            return
        given = [
            index
            for index, value in enumerate(call.args)
            if isinstance(value, ast.Constant) and value.value == field
        ]
        keywords = [
            keyword.arg
            for keyword in call.keywords
            if keyword.arg is not None
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == field
        ]
        if not (given or keywords):
            return
        callee = self._callee(function, call, ())
        if callee is None or callee[0] not in self.package.functions:
            return
        reached, bound_self = callee
        node = self.package.functions[reached].implementation
        if node is None:
            return
        positional = _positional(node, bound=bound_self)
        holder = owner if bound_self else _holder(call, positional, owner)
        if holder is None:
            return
        received = [positional[index].arg for index in given if index < len(positional)]
        received.extend(keywords)
        names = [(parameter, parameter) for parameter in dict.fromkeys(received)]
        vararg = node.args.vararg
        if vararg is not None and any(index >= len(positional) for index in given):
            names.extend((vararg.arg, loop) for loop in _loops_over(node, vararg.arg))
        method = self.package.functions[reached]
        for parameter, local in names:
            for deeper, level, hops in self._known_routes(
                method, _by_name(holder, local), target
            ):
                yield (
                    f"handed by name to {method.qualname}({parameter}), {deeper}",
                    level,
                    hops + 1,
                )

    @property
    def public_record_names(self) -> frozenset[str]:
        """The dotted names of the public records of the package."""
        if self._public_records is None:
            self._public_records = frozenset(
                public_records(self.package, self.annotations)
            )
        return self._public_records

    @property
    def input_records(self) -> frozenset[str]:
        """The public records a caller builds, by dotted name.

        A record a public function takes (a parameter annotation names it, in
        a union, a sequence or a mapping too), or one such a record holds in a
        field, as ``scripts/check_parameter_units.py`` reads them; a result one
        function hands whole to another (:func:`handed_on_results`) is none,
        nor are the records it holds.
        """
        if self._inputs is None:
            taken: set[str] = set()
            for function in public_functions(self.package):
                method = function.owner is not None
                for definition in function.definitions:
                    for parameter in _arguments(definition, method=method):
                        taken |= self._records_named(
                            function.module, parameter.annotation
                        )
            inputs = {record for record in taken if record not in self.handed_on}
            queue = list(inputs)
            while queue:
                fields = record_fields(self.package, self.annotations, queue.pop())
                for field in fields.values():
                    for named in self._records_named(field.module, field.annotation):
                        if named not in inputs and named not in self.handed_on:
                            inputs.add(named)
                            queue.append(named)
            self._inputs = frozenset(inputs) & self.public_record_names
        return self._inputs

    def _records_named(self, module: str, node: ast.expr | None) -> set[str]:
        """The classes of the package an annotation names, at the top or inside."""
        found: set[str] = set()
        stack = self.annotations.members(module, node)
        seen = 0
        while stack and seen < _MEMBERS_READ:
            seen += 1
            where, member = stack.pop()
            dotted = self.annotations.resolve(where, member)
            if dotted is not None and dotted in self.annotations.classes:
                found.add(dotted)
            for item in _items(member):
                for inner in item.elts if isinstance(item, ast.List) else [item]:
                    stack.extend(self.annotations.members(where, inner))
        return found

    def _constructed(
        self,
        record: str,
        positions: list[int],
        keywords: list[str],
        target: Target,
    ) -> Iterator[tuple[str, int, int]]:
        """What a record built with its generated ``__init__`` does with a value.

        The argument fills the field of its keyword, or of its position in
        the order the fields are declared (a keyword-only field takes no
        position), and the record's ``__post_init__`` reads that field as
        ``self.<field>``: a count handed to a record that validates it is
        followed there as it is into a function.
        """
        fields = record_fields(self.package, self.annotations, record)
        positional = [field for field in fields.values() if field.positional]
        received = [
            positional[index].name for index in positions if index < len(positional)
        ]
        received.extend(keyword for keyword in keywords if keyword in fields)
        dotted = self._method(record, "__post_init__")
        post_init = self.package.functions[dotted] if dotted is not None else None
        shown = record.rpartition(".")[2]
        annotations = self.annotations
        for name in dict.fromkeys(received):
            field = fields[name]
            named = annotations.names(field.module, field.annotation, {}, target.typed)
            if named is not None and (
                target is CONVERSION or record in self.public_record_names
            ):
                yield f"handed to {shown}({name}: {named})", False, 1
                continue
            if target is CONVERSION:
                if not annotations.may_hold_numbers(field.module, field.annotation, {}):
                    continue
            elif not annotations.may_hold_scalars(field.module, field.annotation, {}):
                continue
            if post_init is None:
                continue
            for deeper, level, hops in self._known_routes(
                post_init, f"self.{name}", target
            ):
                yield f"handed to {shown}({name}), {deeper}", level, hops + 1

    def _handed(
        self,
        reached: str,
        positions: list[int],
        keywords: list[str],
        *,
        bound: bool,
        target: Target,
    ) -> Iterator[tuple[str, int, int]]:
        """What the function a parameter is handed to does with it."""
        callee = self.package.functions[reached]
        node = callee.implementation
        if node is None:
            return
        parameters = overloads._parameters(node)
        positional = _positional(node, bound=bound)
        received = [
            positional[index].arg for index in positions if index < len(positional)
        ]
        received.extend(keyword for keyword in keywords if keyword in parameters)
        bounds = self._bounds(callee)
        annotations = self.annotations
        for parameter in dict.fromkeys(received):
            annotation = parameters[parameter].annotation
            named = annotations.names(callee.module, annotation, bounds, target.typed)
            if named is not None and (
                target is CONVERSION or reached in self.public_names
            ):
                yield f"handed to {callee.qualname}({parameter}: {named})", False, 1
                continue
            if target is CONVERSION:
                if not annotations.may_hold_numbers(callee.module, annotation, bounds):
                    continue
            elif target is not WINDOW and not annotations.may_hold_scalars(
                callee.module, annotation, bounds
            ):
                continue
            for deeper, level, hops in self._known_routes(callee, parameter, target):
                yield (
                    f"handed to {callee.qualname}({parameter}), {deeper}",
                    level,
                    hops + 1,
                )


def _ending(reached: str, target: Target) -> str:
    """How a route names the call it ends in: ``np.asarray()``, ``require_count() takes it``."""
    short = reached.rpartition(".")[2]
    if target is CONVERSION:
        return f"{'np.' if reached.startswith('numpy.') else ''}{short}()"
    return f"{short}() takes it"


def _refusals(node: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[int]:
    """The ``isinstance`` calls of a body that keep a type out.

    A call an ``if`` tests as it stands, not negated, whose branch raises
    (``if isinstance(x, bool | np.bool_): raise TypeError``) refuses what it
    names; one tested under ``not`` (``if not isinstance(x, (int,
    np.integer)): raise``) admits it, as does any other use. The branch
    raises whether the ``raise`` comes first or after the assignments that
    build its message, the house form (``msg = ...`` then ``raise
    TypeError(msg)``).
    """
    refusing: set[int] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.If) and _raises(child.body):
            refusing.update(
                id(call) for call, negated in _tested(child.test) if not negated
            )
    return frozenset(refusing)


def _raises(body: list[ast.stmt]) -> bool:
    """Whether a branch only raises: a ``raise``, after any assignments."""
    return (
        bool(body)
        and isinstance(body[-1], ast.Raise)
        and all(
            isinstance(statement, ast.Assign | ast.AnnAssign | ast.AugAssign)
            for statement in body[:-1]
        )
    )


def _tested(
    node: ast.expr, *, negated: bool = False
) -> Iterator[tuple[ast.Call, bool]]:
    """The ``isinstance`` calls a condition tests, each with whether it is negated."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        yield from _tested(node.operand, negated=not negated)
    elif isinstance(node, ast.BoolOp):
        for value in node.values:
            yield from _tested(value, negated=negated)
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
    ):
        yield node, negated


def public_functions(package: overloads.Package) -> Iterator[overloads.Function]:
    """Every public function and method of the package, each once.

    A function or class a public module lists in ``__all__``, followed to
    the module that defines it; a class's public methods and the dunders a
    caller calls (``__init__``, ``__call__``), its own and those of the
    classes of the package it extends.
    """
    annotations = Annotations(package)
    seen: set[str] = set()
    for module, tree in sorted(package.trees.items()):
        if any(part.startswith("_") for part in module.split(".")[1:]):
            continue
        for name in _exported(tree):
            target = package.canonical(f"{module}.{name}")
            if target in package.functions and target not in seen:
                seen.add(target)
                yield package.functions[target]
            elif target in annotations.classes:
                for method in _methods(package, annotations, target):
                    if method not in seen:
                        seen.add(method)
                        yield package.functions[method]


def _exported(tree: ast.Module) -> list[str]:
    for node in tree.body:
        assigned = overloads._assigned(node)
        if (
            assigned is not None
            and assigned[0] == "__all__"
            and isinstance(assigned[1], ast.List | ast.Tuple)
        ):
            return [
                element.value
                for element in assigned[1].elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
    return []


def _methods(
    package: overloads.Package,
    annotations: Annotations,
    owner: str,
    depth: int = 0,
) -> Iterator[str]:
    """The public methods a class defines or takes from the package's classes it extends."""
    found = annotations.classes.get(owner)
    if found is None or depth > _HIERARCHY:
        return
    module, node = found
    for child in node.body:
        if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if child.name.startswith("_") and child.name not in _CALLED_DUNDERS:
            continue
        dotted = f"{owner}.{child.name}"
        if dotted in package.functions:
            yield dotted
    for base in node.bases:
        target = package.resolve(module, base)
        if target is not None and target in annotations.classes:
            yield from _methods(package, annotations, target, depth + 1)


def _arguments(
    node: ast.FunctionDef | ast.AsyncFunctionDef, *, method: bool
) -> list[ast.arg]:
    """The parameters a caller fills, ``self`` and ``cls`` left out."""
    every = list(overloads._parameters(node).values())
    if method and every and every[0].arg in {"self", "cls"}:
        every = every[1:]
    return every


def findings_in(
    files: Sequence[pathlib.Path],
    root: pathlib.Path,
    *,
    handed_on: frozenset[str] | None = None,
) -> list[Finding]:
    """Every public parameter annotated narrower than what its body accepts.

    *handed_on* names the results one public function hands whole to another,
    read from ``scripts/check_parameter_units.py`` when it is not given.
    """
    package = overloads.Package(files, root)
    reader = Reader(package, handed_on)
    found: list[Finding] = []
    for function in public_functions(package):
        path = repository_path(package.paths[function.module], root)
        method = function.owner is not None
        bounds = reader._bounds(function)
        for head in function.heads:
            found.extend(
                _invariant_findings(reader, function, head, path, bounds, method=method)
            )
        node = function.implementation
        if node is None:
            continue
        found.extend(
            _invariant_findings(reader, function, node, path, bounds, method=method)
        )
        found.extend(
            _conversion_findings(reader, function, path, bounds, method=method)
        )
        found.extend(_scalar_findings(reader, function, path, bounds, method=method))
        found.extend(_window_findings(reader, function, path, bounds, method=method))
        for definition in function.definitions:
            found.extend(
                _key_findings(reader, function, definition, path, bounds, method=method)
            )
        found.extend(_context_findings(reader, function, path, bounds, method=method))
    found.extend(_field_findings(reader, root))
    found.extend(_field_context_findings(reader, root))
    found.extend(_name_findings(reader, root))
    return sorted(set(found), key=lambda item: (item.path, item.line, item.parameter))


def _conversion_findings(
    reader: Reader,
    function: overloads.Function,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters a function converts while its signature refuses an array-like.

    The implementation's annotation is what the body is read against; when
    the function is overloaded, a caller sees only the heads, so each head
    that names the parameter takes ``ArrayLike`` for it too, unless the head
    takes it as a type parameter: that is a head that tells the shape of
    its argument apart (a sequence or an array returns an array), beside a
    last head that takes ``ArrayLike``, which rule A57 asks for.
    """
    node = function.implementation
    if node is None:
        return []
    module = function.module
    annotations = reader.annotations
    found: list[Finding] = []
    for parameter in _arguments(node, method=method):
        name = parameter.arg
        annotation = parameter.annotation
        if not annotations.admits_array_like(module, annotation, bounds):
            problem = _unconverted(reader, function, name, annotation, bounds)
            if problem is not None:
                found.append(
                    Finding(path, node.lineno, function.qualname, name, problem)
                )
            continue
        heads = [
            (head, overloads._parameters(head)[name].annotation, _type_bounds(head))
            for head in function.heads
            if name in overloads._parameters(head)
        ]
        narrow = [
            head
            for head, written, own in heads
            if not _is_type_parameter(written, own)
            and annotations.several_numbers(module, written, {**bounds, **own})
            and not annotations.admits_array_like(module, written, {**bounds, **own})
        ]
        how = reader.conversion(function, name) if narrow else None
        if how is not None:
            found.append(
                Finding(
                    path,
                    narrow[0].lineno,
                    function.qualname,
                    name,
                    "an overload head takes it narrower than ArrayLike, and "
                    f"{how} converts any array-like",
                )
            )
            continue
        narrow = [
            head
            for head, written, own in heads
            if not _is_type_parameter(written, own)
            and annotations.narrow_items(module, written, {**bounds, **own})
        ]
        how = reader.conversion(function, name, level=1) if narrow else None
        if how is not None:
            found.append(
                Finding(
                    path,
                    narrow[0].lineno,
                    function.qualname,
                    name,
                    "an overload head takes its items narrower than a sequence of "
                    f"numbers, and an item {how} converts any array-like",
                )
            )
    return found


def _unconverted(
    reader: Reader,
    function: overloads.Function,
    name: str,
    annotation: ast.expr | None,
    bounds: dict[str, ast.expr],
) -> str | None:
    """Why an implementation's parameter refuses what its body converts, if it does.

    The parameter is converted as it stands, and its annotation holds an
    array or a sequence of numbers; or it is converted item by item, and the
    item type of a sequence it is annotated takes no sequence of numbers.
    """
    module = function.module
    annotations = reader.annotations
    written = ast.unparse(annotation) if annotation else "?"
    if annotations.several_numbers(module, annotation, bounds):
        how = reader.conversion(function, name)
        if how is not None:
            return f"annotated {written}, and {how} converts any array-like"
    items = annotations.narrow_items(module, annotation, bounds)
    how = reader.conversion(function, name, level=1) if items else None
    if how is not None:
        return (
            f"annotated {written}, whose items ({', '.join(items)}) take no "
            f"sequence of numbers, and an item {how} converts any array-like"
        )
    return None


def _invariant_findings(
    reader: Reader,
    function: overloads.Function,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters of one definition whose annotation holds an invariant container."""
    found: list[Finding] = []
    own = {**bounds, **_type_bounds(node)}
    for parameter in _arguments(node, method=method):
        held = reader.annotations.invariant(function.module, parameter.annotation, own)
        if held:
            found.append(
                Finding(
                    path,
                    node.lineno,
                    function.qualname,
                    parameter.arg,
                    f"holds {', '.join(held)}, which refuses a typed caller's "
                    "list or dict of a narrower item, a tuple and a read-only "
                    "mapping",
                )
            )
    return found


def _definitions(
    function: overloads.Function,
    name: str,
    bounds: dict[str, ast.expr],
    *,
    heads_only: bool = False,
) -> list[
    tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.expr | None, dict[str, ast.expr]]
]:
    """The implementation and each head that names parameter *name*, with its annotation.

    A head that takes the parameter as one of its own type parameters tells
    the shape of its argument apart (rule A57) and is left out. With
    *heads_only*, the implementation is left out too.
    """
    found: list[
        tuple[
            ast.FunctionDef | ast.AsyncFunctionDef, ast.expr | None, dict[str, ast.expr]
        ]
    ] = []
    node = function.implementation
    if node is not None and not heads_only and name in overloads._parameters(node):
        found.append((node, overloads._parameters(node)[name].annotation, bounds))
    for head in function.heads:
        parameters = overloads._parameters(head)
        if name not in parameters:
            continue
        written, own = parameters[name].annotation, _type_bounds(head)
        if not _is_type_parameter(written, own):
            found.append((head, written, {**bounds, **own}))
    return found


def _scalar_findings(
    reader: Reader,
    function: overloads.Function,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters whose body admits a numpy scalar their annotation refuses.

    A count a validator such as ``require_count`` takes a numpy integer for,
    a band fraction ``require_band_fraction`` takes one for, a flag an
    ``isinstance`` check lets ``np.bool_`` through for: the implementation
    and every head that names the parameter admit that numpy scalar too, as
    a whole or, for a body that validates one item at a time, in each item.
    """
    node = function.implementation
    if node is None:
        return []
    found: list[Finding] = []
    for parameter in _arguments(node, method=method):
        found.extend(
            _scalar_problems(
                reader,
                function,
                f"{function.module}",
                parameter.arg,
                _definitions(function, parameter.arg, bounds),
                path,
            )
        )
    return found


def _window_findings(
    reader: Reader,
    function: overloads.Function,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters handed to a window reader of SciPy that refuse a tuple.

    ``scipy.signal.get_window`` and the estimators that call it take a
    window as a name or as a tuple of a name and its parameters
    (``("kaiser", 8.6)``, ``("general_cosine", weights)``): a parameter
    that reaches one, through the helpers it is handed to, takes the tuple
    too, on the implementation and on every head that names it.
    """
    node = function.implementation
    if node is None:
        return []
    found: list[Finding] = []
    for parameter in _arguments(node, method=method):
        how = reader.conversion(function, parameter.arg, target=WINDOW)
        if how is None:
            continue
        for definition, written, own in _definitions(function, parameter.arg, bounds):
            if reader.annotations.admits_window(function.module, written, own):
                continue
            found.append(
                Finding(
                    path,
                    definition.lineno,
                    function.qualname,
                    parameter.arg,
                    f"annotated {_shown(written)}, which refuses a window given as "
                    "a tuple of its name and parameters, such as ('kaiser', 8.6), "
                    f"while {how}",
                    part="window",
                )
            )
            break
    return found


def _scalar_problems(
    reader: Reader,
    function: overloads.Function,
    module: str,
    name: str,
    definitions: Sequence[tuple[ast.AST | _Line, ast.expr | None, dict[str, ast.expr]]],
    path: str,
    *,
    owner: str | None = None,
    constructor: bool = False,
) -> list[Finding]:
    """The scalar findings of one parameter or field, read against its definitions.

    With *constructor*, a field a caller-built record stores the validated
    value in, read against the parameter of its constructor.
    """
    annotations = reader.annotations
    shown = owner if owner is not None else function.qualname
    field = name.removeprefix("self.")
    built = (
        f"; {shown} is built by its caller and stores the value it validates, "
        "so its constructor takes the numpy scalar (a TYPE_CHECKING __init__)"
        if constructor
        else ""
    )
    found: list[Finding] = []
    for target in SCALAR_TARGETS:
        kind = target.admitted
        numpy_name = _SCALAR_NAMES[kind]
        held = definitions
        if target.whole_only:
            # A count a validator already holds is reported once, from there.
            if any(finding.part == kind for finding in found):
                continue
            held = [
                (definition, written, own)
                for definition, written, own in definitions
                if _whole(annotations, module, written, own)
            ]
            if not held:
                continue
        how = reader.conversion(function, name, target=target)
        if how is not None:
            for definition, written, own in held:
                if annotations.admits_scalar(
                    kind, module, written, own
                ) or not annotations.may_hold_a_number(module, written, own):
                    continue
                found.append(
                    Finding(
                        path,
                        getattr(definition, "lineno", 0),
                        shown,
                        field,
                        f"annotated {_shown(written)}, which refuses {numpy_name}, "
                        f"while {how}{built}",
                        part=kind,
                        constructor=constructor,
                    )
                )
                break
        for level, refusing, reads in (
            (1, annotations.items_refusing, ("items", "an item")),
            (
                2,
                annotations.elements_refusing,
                ("items' elements", "an element of an item"),
            ),
        ):
            how = reader.conversion(function, name, level=level, target=target)
            if how is None:
                continue
            for definition, written, own in held:
                items = refusing(kind, module, written, own)
                if not items:
                    continue
                found.append(
                    Finding(
                        path,
                        getattr(definition, "lineno", 0),
                        shown,
                        field,
                        f"annotated {_shown(written)}, whose {reads[0]} "
                        f"({', '.join(items)}) refuse {numpy_name}, while "
                        f"{reads[1]} {how}{built}",
                        part=kind,
                        constructor=constructor,
                    )
                )
                break
    return found


def _shown(annotation: ast.expr | None) -> str:
    return ast.unparse(annotation) if annotation is not None else "nothing"


def _whole(
    annotations: Annotations,
    module: str,
    written: ast.expr | None,
    own: dict[str, ast.expr],
) -> bool:
    """Whether an annotation is a whole number, or a sequence of them.

    What :data:`COUNTED` holds: a count, an order or an index annotated
    ``int`` (``int | None``, ``Sequence[int]``), not a real number a scalar
    guard reads too.
    """
    if written is None:
        return False
    if family(annotations, module, written, own) == "whole":
        return True
    return any(
        annotations.resolve(where, member) in _CONTAINERS
        and any(
            family(annotations, where, item, {}) == "whole"
            for item in _items(member)
            if not _is_ellipsis(item)
        )
        for where, member in annotations.members(module, written, own)
    )


#: The containers whose key a typed caller's ``dict`` must match exactly.
_MAPPINGS = frozenset(
    {
        "typing.Mapping",
        "typing.MutableMapping",
        "collections.abc.Mapping",
        "collections.abc.MutableMapping",
    }
)

#: The choices a key may be a ``Literal`` of, which a typed caller narrows.
_LITERALS = frozenset({"typing.Literal", "typing_extensions.Literal"})

#: A key a ``dict`` of a narrower key does not match: a mapping keyed by
#: ``float`` refuses a ``dict[int, ...]``, one keyed by ``complex`` a
#: ``dict[int, ...]`` and a ``dict[float, ...]`` too.
_WIDENED_KEYS: dict[str, tuple[str, ...]] = {
    "builtins.float": ("builtins.int",),
    "builtins.complex": ("builtins.int", "builtins.float"),
}

#: What a finding calls each key a mapping must also be offered with.
_KEY_NAMES = {"builtins.int": "int", "builtins.float": "float", "None": "None"}


def _key(annotations: Annotations, module: str, node: ast.expr) -> str:
    """One member of a mapping's key, by its dotted name (``None`` for ``None``)."""
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    dotted = annotations.resolve(module, node)
    return dotted if dotted is not None else ast.unparse(node)


def _keyed_mappings(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
) -> list[tuple[ast.expr, list[str]]]:
    """The mappings at the top of an annotation, each with its key's members.

    A key member that is a ``Literal`` of choices is left out: the caller
    narrows it as a ``Literal`` parameter is narrowed.
    """
    keyed: list[tuple[ast.expr, list[str]]] = []
    for where, member in annotations.members(module, node, bounds):
        if annotations.resolve(where, member) not in _MAPPINGS:
            continue
        items = _items(member)
        if not items:
            continue
        keys = [
            _key(annotations, inner_module, inner)
            for inner_module, inner in annotations.members(where, items[0])
            if annotations.resolve(inner_module, inner) not in _LITERALS
        ]
        keyed.append((member, keys))
    return keyed


def offered_keys(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
) -> frozenset[str]:
    """The keys an annotation offers a mapping keyed by one of them alone."""
    return frozenset(
        keys[0]
        for _, keys in _keyed_mappings(annotations, module, node, bounds)
        if len(keys) == 1
    )


def key_problems(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
    depth: int = 0,
    *,
    offered_beside: frozenset[str] = frozenset(),
) -> list[str]:
    """The mappings of an annotation whose key refuses a typed caller's ``dict``.

    ``Mapping`` is invariant in its key, so a ``dict[int, float]`` is not a
    ``Mapping[float, float]``, and a ``dict[int, M]`` is not a
    ``Mapping[int | None, M]``. A mapping keyed by ``float`` (or ``complex``)
    is offered beside one keyed by ``int`` (and ``float``) in the same union,
    and one keyed by a union of several members beside one keyed by each
    member: ``Mapping[int, float] | Mapping[float, float]``. A key that is a
    ``Literal`` of choices is narrowed by the caller as a ``Literal``
    parameter is, and is left as it stands. Mappings inside the items of a
    container or the values of a mapping are read too.

    *offered_beside* names the keys the other overload heads of the function
    offer the same parameter alone: an overloaded function offers each
    mapping in a head of its own, so that a ``dict`` written in the call is
    read against one of them, and a caller sees every head.
    """
    if node is None or depth > _NESTING:
        return []
    members = annotations.members(module, node, bounds)
    keyed = _keyed_mappings(annotations, module, node, bounds)
    offered = {keys[0] for _, keys in keyed if len(keys) == 1} | set(offered_beside)
    problems: list[str] = []
    for member, keys in keyed:
        wanted = set(keys) if len(keys) > 1 else set()
        for key in keys:
            wanted.update(_WIDENED_KEYS.get(key, ()))
        missing = sorted(wanted - offered)
        if missing:
            names = ", ".join(
                _KEY_NAMES.get(key, key.rpartition(".")[2]) for key in missing
            )
            problems.append(f"{ast.unparse(member)} with no mapping keyed by {names}")
    for where, member in members:
        if annotations.resolve(where, member) in _LITERALS:
            continue
        for item in _items(member):
            for inner in item.elts if isinstance(item, ast.List) else [item]:
                problems.extend(key_problems(annotations, where, inner, {}, depth + 1))
    return list(dict.fromkeys(problems))


def _key_findings(
    reader: Reader,
    function: overloads.Function,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters of one definition with a mapping a typed caller's ``dict`` cannot match.

    A head is read with the keys every head of the function offers the same
    parameter alone, which is what a caller of the overloaded function sees.
    """
    found: list[Finding] = []
    own = {**bounds, **_type_bounds(node)}
    is_head = any(node is head for head in function.heads)
    for parameter in _arguments(node, method=method):
        beside: frozenset[str] = frozenset()
        if is_head:
            beside = frozenset().union(
                *(
                    offered_keys(reader.annotations, function.module, written, scope)
                    for _, written, scope in _definitions(
                        function, parameter.arg, bounds, heads_only=True
                    )
                )
            )
        problems = key_problems(
            reader.annotations,
            function.module,
            parameter.annotation,
            own,
            offered_beside=beside,
        )
        if problems:
            found.append(
                Finding(
                    path,
                    node.lineno,
                    function.qualname,
                    parameter.arg,
                    f"holds {'; '.join(problems)}, which refuses a typed caller's "
                    "dict of the narrower key",
                    part="key",
                )
            )
    return found


#: What a ``dict`` written in a call holds that it is inferred as on its own:
#: a number, a text, ``None``, a record. A ``Literal`` choice is inferred as a
#: ``str``, the numbers of a ``float`` key written ``125`` as an ``int``, a
#: nested ``dict`` as one of its own, and values of two kinds as what they
#: share (``object`` for a ``dict[int, float]`` beside a ``dict[float,
#: float]``), so a key or a value of any other type needs the mapping the
#: ``dict`` is passed for as its context.
_CONTEXT_FREE_REFUSED = _LITERALS | _MAPPINGS | _CONTAINERS | _INVARIANT | _ARRAY_LIKE


def _needs_context(annotations: Annotations, module: str, node: ast.expr) -> bool:
    """Whether a key or a value of this type needs the context of its mapping.

    One member besides ``None`` that is a plain type (a number, a text, a
    record) is inferred the same with or without it; a union of several, a
    ``Literal``, a mapping, a sequence or ``ArrayLike`` is not.
    """
    members = [
        (where, member)
        for where, member in annotations.members(module, node)
        if not _is_none(member)
    ]
    if len(members) != 1:
        return len(members) > 1
    where, member = members[0]
    return annotations.resolve(where, member) in _CONTEXT_FREE_REFUSED


def _arm_needs_context(annotations: Annotations, module: str, arm: ast.expr) -> bool:
    """Whether a ``dict`` written for this mapping is inferred wrong without it."""
    items = [item for item in _items(arm) if not _is_ellipsis(item)]
    return any(_needs_context(annotations, module, item) for item in items)


def context_unions(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
    depth: int = 0,
) -> list[tuple[int, tuple[str, ...]]]:
    """The unions of two or more mappings a ``dict`` written in a call cannot meet.

    mypy reads a ``dict`` display against the type it is passed for when
    that type holds one mapping; with two or more in a union it reads the
    display on its own, so a ``Literal`` key is a ``str``, an ``int`` key is
    not a ``float`` one, and nested displays of two key types join to
    ``object``: a call that runs is refused. Each union with two or more
    mappings, one of whose key or value needs the context
    (:func:`_needs_context`), comes with its depth (0 at the top of the
    annotation) and its mappings as written, aliases spelt out.
    """
    if node is None or depth > _NESTING:
        return []
    members = annotations.members(module, node, bounds)
    arms = [
        (where, member)
        for where, member in members
        if annotations.resolve(where, member) in _MAPPINGS
    ]
    found: list[tuple[int, tuple[str, ...]]] = []
    if len(arms) > 1 and any(
        _arm_needs_context(annotations, where, member) for where, member in arms
    ):
        found.append((depth, tuple(ast.unparse(member) for _, member in arms)))
    for where, member in members:
        if annotations.resolve(where, member) in _LITERALS:
            continue
        for item in _items(member):
            for inner in item.elts if isinstance(item, ast.List) else [item]:
                found.extend(context_unions(annotations, where, inner, {}, depth + 1))
    return list(dict.fromkeys(found))


def _sole_mapping(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
) -> str | None:
    """The one mapping at the top of an annotation, as written, if it holds one."""
    arms = [
        member
        for where, member in annotations.members(module, node, bounds)
        if annotations.resolve(where, member) in _MAPPINGS
    ]
    return ast.unparse(arms[0]) if len(arms) == 1 else None


def _context_findings(
    reader: Reader,
    function: overloads.Function,
    path: str,
    bounds: dict[str, ast.expr],
    *,
    method: bool,
) -> list[Finding]:
    """The parameters that offer a ``dict`` written in the call no mapping to be read against.

    A union of two or more mappings at the top of a parameter is offered
    one mapping at a time, each in an overload head of its own, so that mypy
    reads the ``dict`` against each in turn: the implementation keeps the
    union, and every mapping of it is the one mapping of a head. A head that
    takes two or more of them, or a union of them below the top, where no
    head can split it, is refused.
    """
    annotations = reader.annotations
    module = function.module
    found: list[Finding] = []
    for definition in function.definitions:
        is_head = any(definition is head for head in function.heads)
        own = {**bounds, **_type_bounds(definition)}
        for parameter in _arguments(definition, method=method):
            for depth, arms in context_unions(
                annotations, module, parameter.annotation, own
            ):
                shown = " | ".join(arms)
                if depth > 0:
                    problem = (
                        f"holds {shown} inside, where no overload can give a dict "
                        "written in the call the one mapping it is read against"
                    )
                elif is_head:
                    problem = (
                        f"an overload head takes {shown}, which gives a dict "
                        "written in the call no mapping to be read against"
                    )
                else:
                    alone = {
                        _sole_mapping(annotations, module, written, scope)
                        for _, written, scope in _definitions(
                            function, parameter.arg, bounds, heads_only=True
                        )
                    }
                    missing = [arm for arm in arms if arm not in alone]
                    if not missing:
                        continue
                    problem = (
                        f"takes {shown} with no overload head that takes "
                        f"{' or '.join(missing)} alone, so a dict written in the "
                        "call is read against none of them: a Literal key is "
                        "read as a str and nested mappings of two key types as "
                        "object, and a call that runs is refused"
                    )
                found.append(
                    Finding(
                        path,
                        definition.lineno,
                        function.qualname,
                        parameter.arg,
                        problem,
                        part="context",
                    )
                )
    return found


def _field_context_findings(reader: Reader, root: pathlib.Path) -> list[Finding]:
    """The fields of public records that offer a ``dict`` written for them no mapping.

    A record's generated ``__init__`` has no overload heads, so a field takes
    at most one mapping that needs a written ``dict``'s context, at any depth.
    """
    package = reader.package
    annotations = reader.annotations
    found: list[Finding] = []
    for record in public_records(package, annotations):
        for field in record_fields(package, annotations, record).values():
            for _, arms in context_unions(
                annotations, field.module, field.annotation, {}
            ):
                found.append(
                    Finding(
                        repository_path(package.paths[field.module], root),
                        field.line,
                        record.removeprefix(f"{field.module}."),
                        field.name,
                        f"holds {' | '.join(arms)}, which gives a dict written "
                        "for it no mapping to be read against, and a record's "
                        "constructor has no overload to offer them one at a time",
                        part="context",
                    )
                )
    return found


#: The decorator that makes a class a record with generated fields.
_DATACLASS = frozenset({"dataclasses.dataclass"})

#: The sentinel after which a record's fields are keyword-only.
_KW_ONLY = frozenset({"dataclasses.KW_ONLY"})

#: The annotations that make a class attribute something other than a field.
_NOT_FIELDS = frozenset(
    {"typing.ClassVar", "typing_extensions.ClassVar", "dataclasses.InitVar"}
)


@dataclass(frozen=True)
class Field:
    """A field of a public record: where it is written, and its annotation."""

    #: The record the field belongs to, by its dotted name.
    record: str
    #: The module the field is written in, and the line.
    module: str
    line: int
    name: str
    annotation: ast.expr
    #: Whether the generated ``__init__`` takes it by position too: not a
    #: field of a ``kw_only`` record, after ``KW_ONLY`` or ``field(kw_only=True)``.
    positional: bool = True


def _is_dataclass(package: overloads.Package, module: str, node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        called = decorator.func if isinstance(decorator, ast.Call) else decorator
        if package.resolve(module, called) in _DATACLASS:
            return True
    return False


def _field_default_off(
    node: ast.AnnAssign, package: overloads.Package, module: str
) -> bool:
    """Whether a field is left out of ``__init__`` (``field(init=False)``)."""
    return _field_option(node, package, module, "init") is False


def _field_option(
    node: ast.AnnAssign, package: overloads.Package, module: str, option: str
) -> object:
    """The value a field's ``field(...)`` gives an option, ``None`` when it gives none."""
    value = node.value
    if not (
        isinstance(value, ast.Call)
        and package.resolve(module, value.func) == "dataclasses.field"
    ):
        return None
    for keyword in value.keywords:
        if keyword.arg == option and isinstance(keyword.value, ast.Constant):
            return keyword.value.value
    return None


def _keyword_only_record(
    package: overloads.Package, module: str, node: ast.ClassDef
) -> bool:
    """Whether a record's decorator makes every field keyword-only (``kw_only=True``)."""
    return any(
        isinstance(decorator, ast.Call)
        and package.resolve(module, decorator.func) in _DATACLASS
        and any(
            keyword.arg == "kw_only"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in decorator.keywords
        )
        for decorator in node.decorator_list
    )


def record_fields(
    package: overloads.Package, annotations: Annotations, record: str, depth: int = 0
) -> dict[str, Field]:
    """The fields a record's ``__init__`` takes, its bases' first, by name."""
    found = annotations.classes.get(record)
    if found is None or depth > _HIERARCHY:
        return {}
    module, node = found
    fields: dict[str, Field] = {}
    for base in node.bases:
        target = package.resolve(module, base)
        if target is not None and target in annotations.classes:
            fields.update(record_fields(package, annotations, target, depth + 1))
    if not _is_dataclass(package, module, node):
        return fields
    keyword_only = _keyword_only_record(package, module, node)
    for child in node.body:
        if not (
            isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Name)
            and child.simple
        ):
            continue
        written = child.annotation
        if package.resolve(module, written) in _KW_ONLY:
            keyword_only = True
            continue
        base = written.value if isinstance(written, ast.Subscript) else written
        if package.resolve(module, base) in _NOT_FIELDS:
            continue
        if _field_default_off(child, package, module):
            fields.pop(child.target.id, None)
            continue
        own = _field_option(child, package, module, "kw_only")
        fields[child.target.id] = Field(
            record,
            module,
            child.lineno,
            child.target.id,
            written,
            positional=not (keyword_only if own is None else own),
        )
    return fields


def public_records(
    package: overloads.Package, annotations: Annotations
) -> Iterator[str]:
    """Every public record of the package, by its dotted name, each once."""
    seen: set[str] = set()
    for module, tree in sorted(package.trees.items()):
        if any(part.startswith("_") for part in module.split(".")[1:]):
            continue
        for name in _exported(tree):
            target = package.canonical(f"{module}.{name}")
            if target in seen or target not in annotations.classes:
                continue
            seen.add(target)
            where, node = annotations.classes[target]
            if _is_dataclass(package, where, node):
                yield target


def _rebound(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    texts: Callable[[ast.expr], tuple[str, ...]],
) -> frozenset[str]:
    """The fields a method stores a value of its own in, by name.

    By the field's name, or through a loop over field names
    (``for name in _FEATURES: object.__setattr__(self, name, ...)``).
    """
    looping: dict[str, tuple[str, ...]] = {}
    for loop in ast.walk(node):
        if isinstance(loop, ast.For | ast.AsyncFor | ast.comprehension) and isinstance(
            loop.target, ast.Name
        ):
            looping.setdefault(loop.target.id, ())
            looping[loop.target.id] += _field_names(loop.iter, texts)
    stored: set[str] = set()
    for call in ast.walk(node):
        if not (isinstance(call, ast.Call) and len(call.args) >= _SETATTR):
            continue
        func = call.func
        setter = (
            isinstance(func, ast.Attribute)
            and func.attr == "__setattr__"
            and isinstance(func.value, ast.Name)
            and func.value.id == "object"
        ) or (isinstance(func, ast.Name) and func.id == "setattr")
        if not setter:
            continue
        field = call.args[1]
        if isinstance(field, ast.Constant) and isinstance(field.value, str):
            stored.add(field.value)
        elif isinstance(field, ast.Name):
            stored.update(looping.get(field.id, ()))
    return frozenset(stored)


#: The arguments of ``object.__setattr__(self, "name", value)``.
_SETATTR = 3


def _holder(call: ast.Call, positional: Sequence[ast.arg], owner: str) -> str | None:
    """The parameter of a function that a call hands the record to, by name.

    ``_hold_cells(self, "ix", "iy")`` hands ``self`` to the parameter
    ``record`` of ``_hold_cells(record, *names)``.
    """
    for index, value in enumerate(call.args):
        if isinstance(value, ast.Name) and value.id == owner:
            return positional[index].arg if index < len(positional) else None
    return None


def _loops_over(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> list[str]:
    """The loop names a body takes each item of its local *name* in."""
    return [
        loop.target.id
        for loop in ast.walk(node)
        if isinstance(loop, ast.For | ast.AsyncFor | ast.comprehension)
        and isinstance(loop.target, ast.Name)
        and isinstance(loop.iter, ast.Name)
        and loop.iter.id == name
    ]


def _handed_stores(
    reader: Reader,
    function: overloads.Function,
    call: ast.Call,
    looping: dict[str, tuple[str, ...]],
) -> set[str]:
    """The fields a function handed the record stores in, by the names it is handed.

    ``_hold_cells(self, "ix", "iy")`` hands the record and two field names to
    a function of the package that stores in each,
    ``object.__setattr__(record, name, ...)`` in a loop over its vararg: the
    record stores in ``ix`` and ``iy``. A name the function stores by is a
    text, a parameter filled by the call, or a loop name over its vararg;
    *looping* reads the call's own arguments when they are loop names of the
    caller. A method called on ``self`` is read where it is called.
    """
    if not any(
        isinstance(value, ast.Name) and value.id in _OWNERS for value in call.args
    ):
        return set()
    callee = reader._callee(function, call, ())
    if callee is None or callee[0] not in reader.package.functions or callee[1]:
        return set()
    node = reader.package.functions[callee[0]].implementation
    if node is None:
        return set()
    positional = _positional(node, bound=False)
    owners = {
        holder
        for owner in _OWNERS
        if (holder := _holder(call, positional, owner)) is not None
    }
    vararg = node.args.vararg
    rest = call.args[len(positional) :]
    by_vararg = set(_loops_over(node, vararg.arg)) if vararg is not None else set()
    places = {argument.arg: index for index, argument in enumerate(positional)}
    helper = reader.package.functions[callee[0]]
    stored: set[str] = set()
    for inner in ast.walk(node):
        if not (
            isinstance(inner, ast.Call)
            and _is_setter(inner.func)
            and len(inner.args) >= _SETATTR
            and isinstance(inner.args[0], ast.Name)
            and inner.args[0].id in owners
        ):
            continue
        field = inner.args[1]
        if _given_back(reader, helper, inner.args[2], field, owners):
            continue
        handed: list[ast.expr] = []
        if isinstance(field, ast.Constant) and isinstance(field.value, str):
            stored.add(field.value)
        elif isinstance(field, ast.Name) and field.id in by_vararg:
            handed.extend(rest)
        elif (
            isinstance(field, ast.Name)
            and field.id in places
            and places[field.id] < len(call.args)
        ):
            handed.append(call.args[places[field.id]])
        for value in handed:
            named = _field_named(value, looping)
            if named is not None:
                stored.update(named)
    return stored


def _is_setter(func: ast.expr) -> bool:
    """Whether a call is ``object.__setattr__`` or ``setattr``."""
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "__setattr__"
        and isinstance(func.value, ast.Name)
        and func.value.id == "object"
    ) or (isinstance(func, ast.Name) and func.id == "setattr")


def _field_findings(reader: Reader, root: pathlib.Path) -> list[Finding]:
    """The fields of public records whose ``__post_init__`` admits a numpy scalar their annotation refuses.

    A field a validator takes a numpy integer for, or an ``isinstance``
    check lets ``np.bool_`` through for, and that the record keeps as it was
    given, holds that numpy scalar: its annotation names it. A field the
    ``__post_init__`` stores a value of its own in holds what it stores (the
    int a validator returns) and keeps that annotation; when the record is
    one a caller builds (:attr:`Reader.input_records`), what the caller hands
    over is typed by its constructor instead, a ``TYPE_CHECKING``
    ``__init__`` whose parameter admits the numpy scalar. A result's stored
    field is the library's own business.
    """
    package = reader.package
    annotations = reader.annotations
    inputs = reader.input_records
    found: list[Finding] = []
    for record in public_records(package, annotations):
        dotted = reader._method(record, "__post_init__")
        if dotted is None:
            continue
        post_init = package.functions[dotted]
        node = post_init.implementation
        if node is None:
            continue
        stored = reader.stored_fields(post_init)
        stub = _constructor_stub(annotations, record) if record in inputs else None
        given = overloads._parameters(stub) if stub is not None else {}
        for field in record_fields(package, annotations, record).values():
            constructor = field.name in stored
            if constructor and record not in inputs:
                continue
            definition: ast.AST | _Line = _Line(field.line)
            written: ast.expr | None = field.annotation
            if constructor and field.name in given and stub is not None:
                definition, written = stub, given[field.name].annotation
            found.extend(
                _scalar_problems(
                    reader,
                    post_init,
                    field.module,
                    f"self.{field.name}",
                    [(definition, written, {})],
                    repository_path(package.paths[field.module], root),
                    owner=record.removeprefix(f"{field.module}."),
                    constructor=constructor,
                )
            )
    return found


def _declared_constructor(
    annotations: Annotations, record: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The ``__init__`` a record declares under ``if TYPE_CHECKING:``, as written, if it declares one.

    A caller-built record that converts or normalises a field says what its
    constructor takes there, while its generated ``__init__`` runs.
    """
    found = annotations.classes.get(record)
    if found is None:
        return None
    for child in found[1].body:
        if not (isinstance(child, ast.If) and _is_type_checking(child.test)):
            continue
        for inner in child.body:
            if (
                isinstance(inner, ast.FunctionDef | ast.AsyncFunctionDef)
                and inner.name == "__init__"
            ):
                return inner
    return None


def _constructor_stub(
    annotations: Annotations, record: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The ``__init__`` a record declares for the type checker, its keywords spelt out.

    :func:`_declared_constructor` read through :func:`_spelt_out`, so a
    reader of the parameters reads a constructor that takes its keywords as
    a ``TypedDict`` as it reads one that lists them.
    """
    declared = _declared_constructor(annotations, record)
    if declared is None:
        return None
    return _spelt_out(annotations, record, declared)


#: The most parameters a function takes besides ``self``: the limit of
#: Sonar's rule S107. A constructor that takes more keywords than that
#: declares them as the keys of a ``TypedDict`` it takes whole,
#: ``def __init__(self, **measurements: Unpack[Keywords]) -> None: ...``,
#: which a type checker reads key by key as it reads keyword parameters.
MOST_PARAMETERS = 13

#: ``Unpack``, which types a ``**`` parameter as the keys of a ``TypedDict``.
_UNPACK = frozenset({"typing.Unpack", "typing_extensions.Unpack"})

#: ``TypedDict``, the base of the dictionary a constructor takes its keywords as.
_TYPED_DICT = frozenset({"typing.TypedDict", "typing_extensions.TypedDict"})

#: The wrappers that say whether a caller may leave a key of a ``TypedDict`` out.
_NOT_REQUIRED = frozenset({"typing.NotRequired", "typing_extensions.NotRequired"})
_REQUIRED = frozenset({"typing.Required", "typing_extensions.Required"})


@dataclass(frozen=True)
class _Key:
    """A key of the ``TypedDict`` a constructor takes its keywords as."""

    name: str
    #: The key's annotation, without the ``NotRequired`` or ``Required`` around it.
    annotation: ast.expr
    #: Whether a caller may leave the key out.
    optional: bool


def _keys(
    annotations: Annotations,
    module: str,
    stub: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[_Key] | None:
    """The keys of the ``TypedDict`` a stub takes as ``**keywords: Unpack[Keywords]``, in order.

    ``None`` when the stub's ``**`` parameter is no ``Unpack`` of a
    ``TypedDict`` written in the record's own module, whose annotations are
    then read in that module, as the stub's are. A key a caller may leave
    out is one of a ``total=False`` dictionary not marked ``Required``, or
    one marked ``NotRequired``.
    """
    kwarg = stub.args.kwarg
    if kwarg is None or not isinstance(kwarg.annotation, ast.Subscript):
        return None
    if annotations.resolve(module, kwarg.annotation) not in _UNPACK:
        return None
    dotted = annotations.package.resolve(module, kwarg.annotation.slice)
    found = annotations.classes.get(dotted) if dotted is not None else None
    if found is None or found[0] != module:
        return None
    node = found[1]
    if not any(annotations.resolve(module, base) in _TYPED_DICT for base in node.bases):
        return None
    total = not any(
        keyword.arg == "total"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is False
        for keyword in node.keywords
    )
    keys: list[_Key] = []
    for child in node.body:
        if not (
            isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
        ):
            continue
        annotation, optional = child.annotation, not total
        if isinstance(annotation, ast.Subscript):
            wrapper = annotations.resolve(module, annotation)
            if wrapper in _NOT_REQUIRED | _REQUIRED:
                annotation, optional = annotation.slice, wrapper in _NOT_REQUIRED
        keys.append(_Key(child.target.id, annotation, optional))
    return keys


def _spelt_out(
    annotations: Annotations,
    record: str,
    stub: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """A stub whose ``**`` parameter unpacks a ``TypedDict``, with each key a keyword parameter.

    Each key follows the stub's own keyword-only parameters, with its
    annotation and the default its field has (none for a field without
    one), so the stub reads as the list of keywords a type checker reads
    it as. Whether a caller may leave a key out against whether its field
    has a default is :func:`_keyword_problems`' to hold. A stub that
    unpacks no ``TypedDict`` comes back as it is.
    """
    module = annotations.classes[record][0]
    keys = _keys(annotations, module, stub)
    if keys is None:
        return stub
    written = _field_defaults(annotations.package, annotations, record)
    defaults: list[ast.expr | None] = []
    for key in keys:
        text = written.get(key.name)
        if text is None:
            defaults.append(None)
        elif text == "...":
            defaults.append(ast.Constant(Ellipsis))
        else:
            defaults.append(ast.parse(text, mode="eval").body)
    arguments = copy.copy(stub.args)
    arguments.kwonlyargs = [
        *stub.args.kwonlyargs,
        *(ast.arg(key.name, key.annotation) for key in keys),
    ]
    arguments.kw_defaults = [*stub.args.kw_defaults, *defaults]
    arguments.kwarg = None
    spelt = copy.copy(stub)
    spelt.args = arguments
    return spelt


def _keyword_problems(
    annotations: Annotations,
    record: str,
    stub: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    """What is wrong with how a declared constructor takes its parameters.

    More than :data:`MOST_PARAMETERS` besides ``self`` is a list too long
    for one signature, which goes into a ``TypedDict`` instead; a ``**``
    parameter is an ``Unpack`` of one written in the record's module, and
    a caller may leave a key of it out exactly when the key's field has a
    default.
    """
    arguments = stub.args
    taken = [
        *arguments.posonlyargs,
        *arguments.args,
        *([arguments.vararg] if arguments.vararg else []),
        *arguments.kwonlyargs,
        *([arguments.kwarg] if arguments.kwarg else []),
    ]
    problems: list[str] = []
    count = len(taken) - 1
    if count > MOST_PARAMETERS:
        problems.append(
            f"its TYPE_CHECKING __init__ takes {count} parameters besides self, "
            f"more than the {MOST_PARAMETERS} a function takes (Sonar S107): it "
            "takes them as the keys of a TypedDict, **keywords: Unpack[...]"
        )
    if arguments.kwarg is None:
        return problems
    module = annotations.classes[record][0]
    keys = _keys(annotations, module, stub)
    if keys is None:
        written = arguments.kwarg.annotation
        problems.append(
            f"its TYPE_CHECKING __init__ takes **{arguments.kwarg.arg}: "
            f"{ast.unparse(written) if written is not None else '?'}, which is no "
            "Unpack of a TypedDict written in the record's module"
        )
        return problems
    defaults = _field_defaults(annotations.package, annotations, record)
    for key in keys:
        default = defaults.get(key.name)
        if key.optional and default is None and key.name in defaults:
            problems.append(
                f"{key.name} is a key a caller may leave out, and its field has "
                "no default"
            )
        elif not key.optional and default is not None:
            problems.append(
                f"{key.name} is a key a caller must give, and its field defaults "
                f"to {default}"
            )
    return problems


def _is_type_checking(node: ast.expr) -> bool:
    """Whether a test reads ``TYPE_CHECKING``, as a name or as ``typing.TYPE_CHECKING``."""
    return (isinstance(node, ast.Name) and node.id == "TYPE_CHECKING") or (
        isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING"
    )


# ---------------------------------------------------------------------------
# Records a caller builds: what their constructor takes, what they hold
# ---------------------------------------------------------------------------

#: Records a caller builds that no public function takes as an argument, by
#: dotted name, each with where its construction is documented. A record a
#: public function takes is one already (:attr:`Reader.input_records`).
#: ``tests/test_record_constructors.py`` reads the Python blocks of every
#: guide and fails a record one builds that is neither.
CALLER_BUILT: dict[str, str] = {
    "phonometry.io._sidecar.CalibrationSidecar": (
        "written beside an audio file by hand as well as by write_sidecar: its "
        "docstring documents the numbers and the labels it takes"
    ),
    "phonometry.environment.propagation.air_absorption.AtmosphericAttenuation": (
        "the docstring of its __post_init__ documents a curve built directly, "
        "from a list given by hand as from an array"
    ),
    "phonometry.materials.absorbers.four_microphone.TransferMatrix": (
        "the impedance-tube guide builds one from the four entries of a chain "
        "matrix, and its docstring documents a scalar entry"
    ),
    "phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult": (
        "the transfer-stiffness guide builds one from the frequencies and the "
        "stiffness of the direct method"
    ),
    "phonometry.vibration.human.multiple_shock.MultipleShockResult": (
        "the multiple-shock guide builds one by hand, with its peaks and the "
        "risk thresholds of a sex"
    ),
    "phonometry.room._impulse_response.ImpulseResponseResult": (
        "the migration guide wraps a measured impulse response in one, to plot "
        "it as the deconvolution's result"
    ),
    "phonometry.building.datasheets.SoundReductionSpectrum": (
        "the datasheet guide builds one from the third-octave sound reduction "
        "a manufacturer prints"
    ),
    "phonometry.building.datasheets.ImpactImprovementSpectrum": (
        "the datasheet guide builds one from the improvement a floor covering's "
        "sheet prints"
    ),
    "phonometry.materials.absorbers.datasheets.ThirdOctaveAbsorptionSpectrum": (
        "the datasheet guide builds one from the absorption coefficients a "
        "panel's sheet prints"
    ),
    "phonometry.electroacoustics.headphones.HeadphoneClassification": (
        "the headphone guide builds one to read the IEC 60268-7 code of a "
        "headphone it describes"
    ),
    "phonometry.emission.declaration.OperatingModeDeclaration": (
        "the sound-power guide builds two, one per operating mode of the "
        "machine it declares"
    ),
    "phonometry.emission.declaration.NoiseEmissionDeclaration": (
        "the sound-power guide builds one from the declarations of its operating modes"
    ),
    "phonometry.environment.assessment.soundscape.SoundscapeReport": (
        "the soundscape guide builds one to report a study by hand"
    ),
    "phonometry.environment.assessment.soundscape.SoundscapeParticipants": (
        "the soundscape guide builds one for the report of a study"
    ),
    "phonometry.environment.assessment.soundscape.SoundscapeAcousticEnvironment": (
        "the soundscape guide builds one for the report of a study"
    ),
    "phonometry.environment.assessment.soundscape.SoundscapeDataCollection": (
        "the soundscape guide builds one for the report of a study"
    ),
}

#: What a field may be annotated that holds a container of a fixed kind: an
#: array, a ``tuple``, a ``list`` or a set. A value of another kind given to a
#: record that keeps it as given (a list for an array field, an array for a
#: tuple field) breaks the annotation the reader trusts.
_FIXED_CONTAINERS = overloads._ARRAYS | frozenset(
    {
        "builtins.tuple",
        "builtins.list",
        "builtins.frozenset",
        "builtins.set",
        "typing.Tuple",
        "typing.List",
        "typing.FrozenSet",
        "typing.Set",
    }
)

#: What a constructor parameter may be annotated that takes the sequence a
#: conversion takes: ``ArrayLike``, anything, or an open sequence, set or
#: list of items.
_TAKES_A_SEQUENCE = (
    _ARRAY_LIKE
    | _ANYTHING
    | frozenset(
        {
            "builtins.list",
            "typing.List",
            "typing.Sequence",
            "typing.Iterable",
            "typing.Collection",
            "typing.AbstractSet",
            "collections.abc.Sequence",
            "collections.abc.Iterable",
            "collections.abc.Collection",
            "collections.abc.Set",
        }
    )
)

#: A name every field of the record stands for: a field stored through a
#: loop over a collection the reading cannot list (the record's own fields,
#: a table built from them).
_EVERY_FIELD = "*"

#: Records whose constructor need not say what it converts, with the reason:
#: each of their subclasses is held to it as they are.
STUB_EXEMPT: dict[str, str] = {
    "phonometry._internal.catalogue.CatalogueRow": (
        "a catalogue row is built from a published table or a catalogue file, "
        "where a set of field names arrives as a JSON list; the row takes the "
        "list for that reader and holds the frozenset its field names, which "
        "a caller writing a row by hand passes, so the list is the file "
        "format's leniency, as a whole float is a count's"
    ),
}


def fixed_containers(
    annotations: Annotations, module: str, node: ast.expr | None
) -> list[str]:
    """The members of an annotation that are a container of a fixed kind, as written."""
    return [
        ast.unparse(member)
        for where, member in annotations.members(module, node)
        if annotations.resolve(where, member) in _FIXED_CONTAINERS
    ]


#: What a field may be annotated that holds a table of keys and values: a
#: mapping, a ``dict``, or a read-only mapping. A ``frozen=True`` record
#: stops the field from being rebound, not the caller's ``dict`` in it from
#: being edited after the record checked it, so a record a caller builds
#: copies it into a read-only mapping.
_KEYED_CONTAINERS = _MAPPINGS | frozenset(
    {"builtins.dict", "typing.Dict", "types.MappingProxyType"}
)


def keyed_containers(
    annotations: Annotations, module: str, node: ast.expr | None
) -> list[str]:
    """The members of an annotation that are a mapping, as written."""
    return [
        ast.unparse(member)
        for where, member in annotations.members(module, node)
        if annotations.resolve(where, member) in _KEYED_CONTAINERS
    ]


def takes_a_sequence(
    annotations: Annotations, module: str, node: ast.expr | None
) -> bool:
    """Whether a constructor parameter takes the sequence a conversion takes."""
    return node is None or any(
        annotations.resolve(where, member) in _TAKES_A_SEQUENCE
        for where, member in annotations.members(module, node)
    )


def holds_numeric_items(
    annotations: Annotations, module: str, node: ast.expr | None
) -> bool:
    """Whether a field holds a container of numbers or of arrays, and nothing else but ``None``.

    ``tuple[float, float, float]`` and ``tuple[NDArray[np.float64],
    NDArray[np.float64]]`` do: a conversion that builds either reads its
    argument item by item, and an array is a sequence of its rows to it,
    so the constructor takes one. ``tuple[Resonator, ...]`` does not.
    """
    found = False
    for where, member in annotations.members(module, node):
        if isinstance(member, ast.Constant) and member.value is None:
            continue
        if annotations.resolve(where, member) not in _CONTAINERS:
            return False
        items = [item for item in _items(member) if not _is_ellipsis(item)]
        if not items or not all(
            annotations._number_or_numbers(inner, part, depth=1)
            for item in items
            for inner, part in annotations.members(where, item)
        ):
            return False
        found = True
    return found


#: The open sequences a constructor parameter may take: any sequence,
#: iterable or collection of the items, which a numpy array of them is at run
#: time and is not to a type checker. A parameter that names its containers
#: instead (``tuple[int, int] | list[int]``) says it refuses the others.
_OPEN_SEQUENCES = frozenset(
    {
        "typing.Sequence",
        "typing.Iterable",
        "typing.Collection",
        "collections.abc.Sequence",
        "collections.abc.Iterable",
        "collections.abc.Collection",
    }
)


def open_without_an_array(
    annotations: Annotations, module: str, node: ast.expr | None
) -> bool:
    """Whether a constructor parameter takes an open sequence and no numpy array.

    ``Sequence[ArrayLike]`` and ``Sequence[float]`` do: they claim every
    sequence of the items and refuse, to a type checker, the array whose
    rows the conversion reads as well. ``ArrayLike``, an array type or
    anything beside it takes the array; named containers claim no more than
    they take.
    """
    members = [
        annotations.resolve(where, member)
        for where, member in annotations.members(module, node)
    ]
    return any(dotted in _OPEN_SEQUENCES for dotted in members) and not any(
        dotted in _ARRAY_LIKE | _ANYTHING | overloads._ARRAYS for dotted in members
    )


def _setattr_name(call: ast.Call) -> ast.expr | None:
    """The field name ``object.__setattr__(self, name, ...)`` or ``setattr(self, ...)`` stores in."""
    func = call.func
    setter = (
        isinstance(func, ast.Attribute)
        and func.attr == "__setattr__"
        and isinstance(func.value, ast.Name)
        and func.value.id == "object"
    ) or (isinstance(func, ast.Name) and func.id == "setattr")
    if not (setter and len(call.args) >= _SETATTR):
        return None
    owner = call.args[0]
    if not (isinstance(owner, ast.Name) and owner.id in _OWNERS):
        return None
    return call.args[1]


def _loop_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    texts: Callable[[ast.expr], tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """What each loop name of a method takes in turn: field names, or every field."""
    looping: dict[str, tuple[str, ...]] = {}
    for loop in ast.walk(node):
        if not isinstance(loop, ast.For | ast.AsyncFor | ast.comprehension):
            continue
        targets = (
            [loop.target]
            if isinstance(loop.target, ast.Name)
            else [
                element
                for element in getattr(loop.target, "elts", [])
                if isinstance(element, ast.Name)
            ]
        )
        names = _field_names(loop.iter, texts)
        literal = isinstance(loop.iter, ast.Tuple | ast.List | ast.Set)
        for target in targets:
            taken = names if names or literal else (_EVERY_FIELD,)
            looping[target.id] = looping.get(target.id, ()) + taken
    return looping


def _parameter_positions(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, int]:
    """The position of each parameter of a method a call fills, ``self`` left out."""
    every = [*node.args.posonlyargs, *node.args.args]
    if every and every[0].arg in _OWNERS:
        every = every[1:]
    return {argument.arg: index for index, argument in enumerate(every)}


def _field_named(
    node: ast.expr, looping: dict[str, tuple[str, ...]]
) -> tuple[str, ...] | None:
    """The field names an argument stands for: a text, or a loop name over field names.

    The ``name`` of a loop name over the record's fields
    (``for field in fields(self): ... field.name``) stands for every field.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    if isinstance(node, ast.Name) and node.id in looping:
        return looping[node.id]
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "name"
        and isinstance(node.value, ast.Name)
        and _EVERY_FIELD in looping.get(node.value.id, ())
    ):
        return (_EVERY_FIELD,)
    return None


#: The calls that hand back what they are given, or a read-only view of it,
#: without a copy, by their name below the package or their dotted name: a
#: field stored back as one of them of itself still holds the caller's
#: container. ``typing.cast`` hands back its second argument.
_NOT_COPIED = frozenset(
    {"types.MappingProxyType", "typing.cast", "typing_extensions.cast"}
)
_NOT_COPIED_HERE = frozenset(
    {"_internal.frozen.read_only", "_internal.frozen.handed_over"}
)


def _reads_field(value: ast.expr, field: ast.expr, owners: Collection[str]) -> bool:
    """Whether *value* reads the field a setter stores in: ``self.sides`` or ``getattr(self, name)``."""
    if (
        isinstance(field, ast.Constant)
        and isinstance(field.value, str)
        and isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id in owners
        and value.attr == field.value
    ):
        return True
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "getattr"
        and len(value.args) == _GETATTR
        and isinstance(value.args[0], ast.Name)
        and value.args[0].id in owners
    ):
        return False
    # The same text, the same loop name, or the same ``each.name``.
    return ast.dump(value.args[1]) == ast.dump(field)


def _given_back(
    reader: Reader,
    function: overloads.Function,
    value: ast.expr,
    field: ast.expr,
    owners: Collection[str],
) -> bool:
    """Whether a setter stores the field back as the caller gave it, converting nothing.

    The field itself (``object.__setattr__(self, "sides", self.sides)``), or
    a call of :data:`_NOT_COPIED` on it (``MappingProxyType(self.sides)``),
    which wraps the caller's dictionary and copies none of it: a change the
    caller makes afterwards still reaches the record. ``dict(self.sides)``,
    a comprehension or a helper that builds a value of its own converts it.
    """
    for _ in range(_NESTING):
        if _reads_field(value, field, owners):
            return True
        if not (isinstance(value, ast.Call) and value.args):
            return False
        local = (
            reader.package.local_imports.get(function.implementation, {})
            if function.implementation is not None
            else {}
        )
        dotted = reader.package.resolve(function.module, value.func, local)
        if dotted is None:
            return False
        below = dotted.removeprefix(f"{reader.root}.")
        if dotted not in _NOT_COPIED and below not in _NOT_COPIED_HERE:
            return False
        value = value.args[-1] if dotted.endswith(".cast") else value.args[0]
    return False


def _stores(
    reader: Reader, function: overloads.Function, depth: int = 0
) -> tuple[frozenset[str], frozenset[int]]:
    """The fields a method stores a value of its own in, and the parameters it stores in.

    ``object.__setattr__(self, "n", ...)`` or ``setattr(self, ...)`` by name,
    or through a loop over field names (every field, when the loop runs
    over a collection the reading cannot list), and a method of the record
    it calls on ``self`` or ``super()``, a setter that stores in the field
    whose name it is handed (``self._set(name, value)``) included. The
    second set holds the positions of the method's own parameters it stores
    in by name, which make it such a setter.
    """
    node = function.implementation
    if node is None or depth > _HIERARCHY:
        return frozenset(), frozenset()
    looping = _loop_names(node, lambda found: reader._texts(function.module, found))
    positions = _parameter_positions(node)
    stored: set[str] = set()
    setter: set[int] = set()
    for call in reader._calls_of(node):
        name = _setattr_name(call)
        if name is not None:
            if _given_back(reader, function, call.args[2], name, _OWNERS):
                continue
            named = _field_named(name, looping)
            if named is not None:
                stored.update(named)
            elif isinstance(name, ast.Name) and name.id in positions:
                setter.add(positions[name.id])
            continue
        stored |= _handed_stores(reader, function, call, looping)
        func = call.func
        if not (
            isinstance(func, ast.Attribute)
            and (
                (isinstance(func.value, ast.Name) and func.value.id in _OWNERS)
                or _is_super(func.value)
            )
        ):
            continue
        callee = reader._callee(function, call, ())
        if callee is None or callee[0] not in reader.package.functions:
            continue
        inner, handed = _stores(reader, reader.package.functions[callee[0]], depth + 1)
        stored |= inner
        for position in handed:
            if position < len(call.args):
                named = _field_named(call.args[position], looping)
                if named is not None:
                    stored.update(named)
    return frozenset(stored), frozenset(setter)


def converted_fields(reader: Reader, record: str) -> frozenset[str]:
    """The fields a record's ``__post_init__`` (or a method it calls) stores a value of its own in."""
    fields = record_fields(reader.package, reader.annotations, record)
    dotted = reader._method(record, "__post_init__")
    if dotted is None:
        return frozenset()
    stored, _ = _stores(reader, reader.package.functions[dotted])
    if _EVERY_FIELD in stored:
        return frozenset(fields)
    return stored & frozenset(fields)


def built_records(reader: Reader) -> frozenset[str]:
    """The records a caller builds: those a public function takes, and :data:`CALLER_BUILT`."""
    return reader.input_records | (
        frozenset(CALLER_BUILT) & frozenset(reader.annotations.classes)
    )


def _bases(
    annotations: Annotations, package: overloads.Package, record: str
) -> set[str]:
    """A record and every class of the package it extends, by dotted name."""
    found: set[str] = set()
    stack = [record]
    while stack:
        current = stack.pop()
        if current in found or current not in annotations.classes:
            continue
        found.add(current)
        module, node = annotations.classes[current]
        for base in node.bases:
            target = package.resolve(module, base)
            if target is not None:
                stack.append(target)
    return found


def stub_exemption(
    reader: Reader, record: str, exempt: Mapping[str, str] | None = None
) -> str | None:
    """The entry of *exempt* (:data:`STUB_EXEMPT`) a record falls under, itself or through a base."""
    table = STUB_EXEMPT if exempt is None else exempt
    for base in _bases(reader.annotations, reader.package, record):
        if base in table:
            return base
    return None


def kept_as_given(reader: Reader, record: str) -> list[tuple[Field, list[str]]]:
    """The fields of a record a caller builds that hold a container nothing converts.

    A list given to an array field, or an array to a tuple field, is kept as
    it was handed: the record then holds what its annotation says it does
    not, and a frozen record holds a list a caller can still append to. A
    ``dict`` given to a mapping field is kept as the caller's own, which the
    caller can still edit after the record checked it.
    """
    annotations = reader.annotations
    converted = converted_fields(reader, record)
    found: list[tuple[Field, list[str]]] = []
    for field in record_fields(reader.package, annotations, record).values():
        if field.name in converted:
            continue
        kept = fixed_containers(
            annotations, field.module, field.annotation
        ) + keyed_containers(annotations, field.module, field.annotation)
        if kept:
            found.append((field, kept))
    return found


def _field_defaults(
    package: overloads.Package, annotations: Annotations, record: str, depth: int = 0
) -> dict[str, str | None]:
    """The default of each field a record's ``__init__`` takes, as a stub writes it.

    ``None`` for a field with no default, ``"..."`` for one a factory makes
    (``field(default_factory=...)``), the default's source text otherwise.
    """
    found = annotations.classes.get(record)
    if found is None or depth > _HIERARCHY:
        return {}
    module, node = found
    defaults: dict[str, str | None] = {}
    for base in node.bases:
        target = package.resolve(module, base)
        if target is not None and target in annotations.classes:
            defaults.update(_field_defaults(package, annotations, target, depth + 1))
    for child in node.body:
        if not (
            isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
        ):
            continue
        value = child.value
        if value is None:
            defaults[child.target.id] = None
        elif isinstance(value, ast.Call) and package.resolve(module, value.func) == (
            "dataclasses.field"
        ):
            options = {keyword.arg: keyword.value for keyword in value.keywords}
            if "default" in options:
                defaults[child.target.id] = ast.unparse(options["default"])
            elif "default_factory" in options:
                defaults[child.target.id] = "..."
            else:
                defaults[child.target.id] = None
        else:
            defaults[child.target.id] = ast.unparse(value)
    return defaults


def _covers_member(
    annotations: Annotations,
    field: tuple[str, ast.expr],
    taken: tuple[str, ast.expr],
) -> bool:
    """Whether one member of a parameter's annotation takes one member of a field's.

    The same member as written; ``ArrayLike`` or anything, which take any
    value; or the same generic whose every argument takes the field's
    (``Mapping[K, ArrayLike]`` takes a ``Mapping[K, Sequence[float]]``).
    """
    (field_module, field_member), (taken_module, taken_member) = field, taken
    if annotations.resolve(taken_module, taken_member) in _ARRAY_LIKE | _ANYTHING:
        return True
    if ast.unparse(field_member) == ast.unparse(taken_member):
        return True
    if not (
        isinstance(field_member, ast.Subscript)
        and isinstance(taken_member, ast.Subscript)
        and annotations.resolve(field_module, field_member)
        == annotations.resolve(taken_module, taken_member)
    ):
        return False
    given, takes = _items(field_member), _items(taken_member)
    return len(given) == len(takes) and all(
        _covers(annotations, field_module, item, taken_module, other)
        for item, other in zip(given, takes, strict=True)
    )


def _covers(
    annotations: Annotations,
    field_module: str,
    field_node: ast.expr | None,
    taken_module: str,
    taken_node: ast.expr | None,
) -> bool:
    """Whether every member of a field's annotation is taken by a member of a parameter's."""
    if taken_node is None:
        return True
    taken = annotations.members(taken_module, taken_node)
    return all(
        any(_covers_member(annotations, member, other) for other in taken)
        for member in annotations.members(field_module, field_node)
    )


def _widens(
    annotations: Annotations,
    field: Field,
    stub_module: str,
    parameter: ast.arg,
) -> bool:
    """Whether a constructor parameter takes every value its field's annotation names.

    Each member of the field's annotation, aliases spelt out on both sides,
    is a member of the parameter's, or is taken by one (:func:`_covers`).
    """
    return _covers(
        annotations, field.module, field.annotation, stub_module, parameter.annotation
    )


def constructor_problems(
    reader: Reader, record: str, exempt: Mapping[str, str] | None = None
) -> list[str]:
    """What is wrong with the constructor a record declares, or the one it needs.

    A record a caller builds that converts a field it annotates as a
    container of a fixed kind, or as a sequence of numbers, declares the
    constructor a type checker reads, a ``TYPE_CHECKING`` ``__init__`` that
    takes the sequence the conversion takes (``ArrayLike``, or an open
    sequence of the items, beside an array where the items are numbers or
    arrays, which is a sequence of them too). Any record that declares one
    keeps it in step
    with its fields: the same names, in the same order, each keyword-only
    exactly when the field is, each with the field's default (``...`` for
    one a factory makes), and a parameter for a field it does not convert
    takes every value the field's annotation names. A constructor of more
    than :data:`MOST_PARAMETERS` keywords takes them as the keys of a
    ``TypedDict`` (:func:`_keyword_problems`), each read as the keyword it
    stands for (:func:`_spelt_out`).
    """
    annotations = reader.annotations
    package = reader.package
    module = annotations.classes[record][0]
    fields = record_fields(package, annotations, record)
    declaration = _declared_constructor(annotations, record)
    converted = converted_fields(reader, record)
    problems: list[str] = []
    needs = [
        field
        for field in fields.values()
        if field.name in converted
        and not annotations.admits_array_like(field.module, field.annotation, {})
        and (
            fixed_containers(annotations, field.module, field.annotation)
            or annotations.several_numbers(field.module, field.annotation, {})
        )
    ]
    if declaration is None:
        if (
            needs
            and record in built_records(reader)
            and not stub_exemption(reader, record, exempt)
        ):
            problems.append(
                "converts "
                + ", ".join(field.name for field in needs)
                + " and declares no TYPE_CHECKING __init__ that says what it takes"
            )
        return problems
    problems.extend(_keyword_problems(annotations, record, declaration))
    stub = _spelt_out(annotations, record, declaration)
    parameters = [*stub.args.posonlyargs, *stub.args.args]
    if not parameters or parameters[0].arg not in _OWNERS:
        return ["its TYPE_CHECKING __init__ takes no self"]
    positional = parameters[1:]
    padding: list[ast.expr | None] = [None] * (
        len(parameters) - len(stub.args.defaults)
    )
    defaults = dict(
        zip(
            [argument.arg for argument in parameters],
            [*padding, *stub.args.defaults],
            strict=True,
        )
    )
    defaults.update(
        {
            argument.arg: default
            for argument, default in zip(
                stub.args.kwonlyargs, stub.args.kw_defaults, strict=True
            )
        }
    )
    declared = [(argument, True) for argument in positional] + [
        (argument, False) for argument in stub.args.kwonlyargs
    ]
    names = [argument.arg for argument, _ in declared]
    if names != list(fields):
        return [
            *problems,
            f"its TYPE_CHECKING __init__ takes {names}, its fields are {list(fields)}",
        ]
    written = _field_defaults(package, annotations, record)
    for (argument, by_position), field in zip(declared, fields.values(), strict=True):
        if by_position != field.positional:
            kind = "by position" if field.positional else "by keyword only"
            problems.append(f"{field.name} is a field taken {kind}, not so in the stub")
        default = defaults.get(argument.arg)
        shown = None if default is None else ast.unparse(default)
        if shown != written.get(field.name):
            problems.append(
                f"{field.name} defaults to {written.get(field.name)} as a field and "
                f"to {shown} in the stub"
            )
        if field in needs:
            taken = ast.unparse(argument.annotation) if argument.annotation else "?"
            if not takes_a_sequence(annotations, module, argument.annotation):
                problems.append(
                    f"{field.name} is converted, and the stub takes {taken}"
                    ", which is no ArrayLike nor an open sequence"
                )
            elif holds_numeric_items(
                annotations, field.module, field.annotation
            ) and open_without_an_array(annotations, module, argument.annotation):
                problems.append(
                    f"{field.name} is converted from numbers or arrays, and the "
                    f"stub takes {taken}, an open sequence that refuses the "
                    "numpy array of them"
                )
        elif not _widens(annotations, field, module, argument):
            problems.append(
                f"{field.name} is {ast.unparse(field.annotation)} as a field and the "
                f"stub takes {ast.unparse(argument.annotation) if argument.annotation else '?'}"
                ", which does not take all of it"
            )
    return problems


@dataclass(frozen=True)
class _Line:
    """A line a finding is reported on, where no definition stands."""

    lineno: int


#: The scalar quantities of the library's vocabulary (rule N12 of
#: ``docs/contributing/naming.md``), and the family of numbers each one is
#: annotated with across the API: a sample rate is a real number wherever a
#: function takes one, so that the rate one function returns is the rate
#: another one takes.
NAME_FAMILIES: dict[str, str] = {
    "fs": "real",
    "volume": "real",
    "coverage": "real",
    "confidence": "real",
    "energy_fraction": "real",
    "fraction": "whole",
}

#: Why a generator takes a whole number of samples per second.
_GENERATED_AT_A_WHOLE_RATE = (
    "builds its record sample by sample at a whole number of samples per "
    "second, the rate a converter plays it at, and refuses a fraction "
    "(require_count): a whole rate takes an int or a numpy integer"
)

#: Why an analysis takes a whole number of samples per second.
_RESAMPLED_BY_AN_INTEGER_RATIO = (
    "resamples the record by an integer ratio (scipy.signal.resample_poly), "
    "which a fractional rate has none of, and refuses one (require_count)"
)

#: Why a function that hands its rate to loudness_zwicker takes a whole one.
_HANDED_TO_ZWICKER = (
    "hands its rate to loudness_zwicker, which resamples by an integer ratio "
    "and takes a whole number of samples per second"
)

#: Why a record of a whole-rate function holds an int.
_HOLDS_THE_WHOLE_RATE = (
    "holds the whole rate its function validated (require_count), as the int it is"
)

#: Why the filter functions take any positive bandwidth.
_BANDWIDTH_DESIGNATOR = (
    "the bandwidth designator b of a 1/b-octave filter (IEC 61260-1), any "
    "positive number (1.5, 6, 12 and 24 run), not the 1 or 3 of a band set"
)

_SRC = "src/phonometry/"

#: The parameters and fields named for a quantity of :data:`NAME_FAMILIES`
#: that keep another family on purpose, keyed by file, function or record,
#: and name, each with the reason.
FAMILY_EXEMPT: dict[tuple[str, str, str], str] = {
    (
        f"{_SRC}electroacoustics/headphones.py",
        "headphone_modulation_signal",
        "fs",
    ): _GENERATED_AT_A_WHOLE_RATE,
    (
        f"{_SRC}electroacoustics/headphones.py",
        "headphone_difference_frequency_signal",
        "fs",
    ): _GENERATED_AT_A_WHOLE_RATE,
    (
        f"{_SRC}electroacoustics/induction_loop.py",
        "loop_test_noise",
        "fs",
    ): _GENERATED_AT_A_WHOLE_RATE,
    (
        f"{_SRC}electroacoustics/induction_loop.py",
        "combi_signal",
        "fs",
    ): _GENERATED_AT_A_WHOLE_RATE,
    (
        f"{_SRC}electroacoustics/program_signal.py",
        "simulated_program_signal",
        "fs",
    ): _GENERATED_AT_A_WHOLE_RATE,
    (f"{_SRC}room/image_source.py", "image_source_rir", "fs"): (
        "samples the impulse response on a grid of a whole number of samples "
        "per second, the rate the record it is convolved with or written to "
        "holds, and refuses a fraction (require_count)"
    ),
    (
        f"{_SRC}electroacoustics/induction_loop.py",
        "field_strength_meter",
        "fs",
    ): (
        "reads a record taken at a whole number of samples per second through "
        "its weighting and time-weighting filters and refuses a fraction "
        "(require_count), as the meter of IEC 60118-4 Annex B does"
    ),
    (
        f"{_SRC}psychoacoustics/loudness/zwicker.py",
        "loudness_zwicker",
        "fs",
    ): _RESAMPLED_BY_AN_INTEGER_RATIO,
    (f"{_SRC}speech/objective_intelligibility.py", "stoi", "fs"): (
        _RESAMPLED_BY_AN_INTEGER_RATIO
    ),
    (
        f"{_SRC}psychoacoustics/quality/annoyance.py",
        "psychoacoustic_annoyance_from_signal",
        "fs",
    ): _HANDED_TO_ZWICKER,
    (f"{_SRC}psychoacoustics/quality/sharpness.py", "sharpness_din", "fs"): (
        _HANDED_TO_ZWICKER
    ),
    (
        f"{_SRC}electroacoustics/induction_loop.py",
        "FieldStrengthReading",
        "fs",
    ): _HOLDS_THE_WHOLE_RATE,
    (f"{_SRC}room/image_source.py", "ImageSourceResult", "fs"): (_HOLDS_THE_WHOLE_RATE),
    (f"{_SRC}speech/objective_intelligibility.py", "STOIResult", "fs"): (
        "the 10 kHz the measure resamples every record to, a whole number "
        "fixed by the method"
    ),
    (f"{_SRC}io/_wav.py", "AudioFileInfo", "fs"): (
        "read from the file's header, which stores a whole number of samples per second"
    ),
    (
        f"{_SRC}emission/_sound_power_intensity.py",
        "PrecisionFieldIndicators",
        "fs",
    ): (
        "F_S, the field non-uniformity indicator of ISO 9614-3 Annex B, one "
        "value per band: the symbol the standard prints, not a sample rate"
    ),
    (f"{_SRC}room/auditorium.py", "LateralEnergyResult", "energy_fraction"): (
        "the early lateral energy fraction of each band, which a result "
        "holds as an array, one per band"
    ),
    (f"{_SRC}filters/compliance.py", "class_limits", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (f"{_SRC}filters/core.py", "OctaveFilterBank.__init__", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (f"{_SRC}filters/core.py", "octave_filter", "fraction"): _BANDWIDTH_DESIGNATOR,
    (f"{_SRC}filters/frequencies.py", "nominal_frequencies", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (
        f"{_SRC}filters/periodic_tests.py",
        "periodic_test_frequencies",
        "fraction",
    ): _BANDWIDTH_DESIGNATOR,
    (
        f"{_SRC}filters/periodic_tests.py",
        "FilterPeriodicVerification",
        "fraction",
    ): _BANDWIDTH_DESIGNATOR,
    (f"{_SRC}filters/periodic_tests.py", "verify_filter_periodic", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (f"{_SRC}filters/time_invariance.py", "swept_band_level", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (f"{_SRC}filters/time_invariance.py", "TimeInvarianceResult", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
    (f"{_SRC}signals/spectra.py", "fractional_octave_smoothing", "fraction"): (
        _BANDWIDTH_DESIGNATOR
    ),
}

#: The real numbers, as an annotation names them.
_REALS = frozenset(
    {
        "builtins.float",
        "numpy.floating",
        "numpy.float16",
        "numpy.float32",
        "numpy.float64",
        "numpy.half",
        "numpy.single",
        "numpy.double",
        "numpy.longdouble",
        "typing.SupportsFloat",
        "typing_extensions.SupportsFloat",
        "numbers.Real",
    }
)

#: The whole numbers, as an annotation names them; a ``Literal`` of them
#: (``BandFraction``) is one too.
_WHOLES = _NUMPY_INTEGERS | _INDEX_PROTOCOLS | {"builtins.int", "numbers.Integral"}


def family(
    annotations: Annotations,
    module: str,
    node: ast.expr | None,
    bounds: dict[str, ast.expr],
) -> str:
    """The family of numbers an annotation takes: ``"array"``, ``"real"``, ``"whole"``.

    The widest one it names, ``None`` left out: an array or a sequence, then
    a real number, then a whole one. An annotation that names none of them is
    its own family, written as it stands.
    """
    if node is None:
        return "unannotated"
    kinds: set[str] = set()
    for where, member in annotations.members(module, node, bounds):
        if isinstance(member, ast.Constant) and member.value is None:
            continue
        dotted = annotations.resolve(where, member)
        if dotted in overloads._ARRAYS | _ARRAY_LIKE | _CONTAINERS:
            kinds.add("array")
        elif dotted in _REALS:
            kinds.add("real")
        elif dotted in _WHOLES or (
            dotted in _LITERALS and _literal_values(member, int)
        ):
            kinds.add("whole")
        else:
            kinds.add(ast.unparse(member))
    for kind in ("array", "real", "whole"):
        if kind in kinds:
            return kind
    return " | ".join(sorted(kinds))


def _literal_values(node: ast.expr, kind: type) -> bool:
    """Whether every choice of a ``Literal`` is of *kind* (``int`` for ``Literal[1, 3]``)."""
    values = _items(node)
    return bool(values) and all(
        isinstance(value, ast.Constant) and type(value.value) is kind
        for value in values
    )


def _name_findings(reader: Reader, root: pathlib.Path) -> list[Finding]:
    """The parameters and fields named for a quantity whose annotation leaves its family.

    Every public parameter (of the implementation and of each overload
    head) and every field of a public record named for a quantity of
    :data:`NAME_FAMILIES`.
    """
    package = reader.package
    annotations = reader.annotations
    found: list[Finding] = []
    for function in public_functions(package):
        path = repository_path(package.paths[function.module], root)
        method = function.owner is not None
        bounds = reader._bounds(function)
        for definition in function.definitions:
            own = {**bounds, **_type_bounds(definition)}
            for parameter in _arguments(definition, method=method):
                expected = NAME_FAMILIES.get(parameter.arg)
                if expected is None:
                    continue
                kind = family(annotations, function.module, parameter.annotation, own)
                if kind != expected:
                    found.append(
                        _family_finding(
                            path,
                            definition.lineno,
                            function.qualname,
                            parameter.arg,
                            parameter.annotation,
                            kind,
                            expected,
                        )
                    )
    for record in public_records(package, annotations):
        for field in record_fields(package, annotations, record).values():
            expected = NAME_FAMILIES.get(field.name)
            if expected is None:
                continue
            kind = family(annotations, field.module, field.annotation, {})
            if kind != expected:
                found.append(
                    _family_finding(
                        repository_path(package.paths[field.module], root),
                        field.line,
                        record.removeprefix(f"{field.module}."),
                        field.name,
                        field.annotation,
                        kind,
                        expected,
                    )
                )
    return found


def _family_finding(
    path: str,
    line: int,
    owner: str,
    name: str,
    annotation: ast.expr | None,
    kind: str,
    expected: str,
) -> Finding:
    return Finding(
        path,
        line,
        owner,
        name,
        f"annotated {_shown(annotation)}, a {kind} number, where every '{name}' "
        f"of the API is a {expected} one",
        part="name",
    )


def repository_path(path: str, root: pathlib.Path) -> str:
    """A file of the package as the repository names it, a copy's included.

    The repository's own ``src/phonometry/room/acoustics.py`` keeps its
    name, and the same file of a copy of the package read elsewhere (a
    scratch tree a defect is put into to see the check fail) is given that
    name too, so that :data:`EXEMPT` and the other tables key a copy the
    way they key the package.
    """
    absolute = pathlib.Path(path)
    absolute = (absolute if absolute.is_absolute() else ROOT / absolute).resolve()
    if not absolute.is_relative_to(root):
        return path
    below = absolute.relative_to(root).as_posix()
    return f"{SOURCE.relative_to(ROOT).as_posix()}/{below}"


def checked(
    findings: Sequence[Finding], exempt: dict[tuple[str, str, str], str]
) -> tuple[list[Finding], list[tuple[str, str, str]]]:
    """The findings no exemption covers, and the exemptions that cover none."""
    used = {finding.key for finding in findings}
    kept = [finding for finding in findings if finding.key not in exempt]
    return kept, sorted(set(exempt) - used)


def judged(
    findings: Sequence[Finding],
) -> tuple[list[Finding], list[tuple[str, tuple[str, str, str]]]]:
    """The findings no exemption covers, and each exemption that covers none.

    :data:`EXEMPT` covers the array part, :data:`FAMILY_EXEMPT` the
    quantities kept in another family; the numpy-scalar and mapping-key
    parts have no exemption. A stale exemption comes with the table that
    lists it.
    """
    found, stale = checked([f for f in findings if f.part == "array"], EXEMPT)
    named, stale_named = checked(
        [f for f in findings if f.part == "name"], FAMILY_EXEMPT
    )
    built, stale_built = checked(
        [f for f in findings if f.constructor], CONSTRUCTOR_EXEMPT
    )
    rest = [
        f for f in findings if f.part not in {"array", "name"} and not f.constructor
    ]
    every = sorted(
        [*found, *named, *built, *rest],
        key=lambda item: (item.path, item.line, item.parameter),
    )
    return every, [
        *(("EXEMPT", key) for key in stale),
        *(("FAMILY_EXEMPT", key) for key in stale_named),
        *(("CONSTRUCTOR_EXEMPT", key) for key in stale_built),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Report every public parameter annotated narrower than what its body accepts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package",
        nargs="?",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to read (default: src/phonometry); the "
        "whole package is read, because a parameter reaches its conversion "
        "through the functions of other modules it is handed to",
    )
    arguments = parser.parse_args(argv)
    root = arguments.package.resolve()
    found, stale = judged(findings_in(python_files([], root), root))
    if not (found or stale):
        print(
            "Every public parameter admits what its body converts and the "
            "numpy scalar its body validates, none holds an invariant list, "
            "dict or set or a mapping a narrower key cannot match, each "
            "mapping a written dict is read against is offered alone, every "
            "window takes its parameters, and every quantity of the vocabulary "
            "keeps its family of numbers."
        )
        return 0
    if found:
        print("::error::a public parameter is annotated narrower than its body")
        for finding in found:
            print(
                f"  {finding.path}:{finding.line}: {finding.function}"
                f"({finding.parameter}): {finding.problem}"
            )
        print(
            "  -> annotate a parameter the body converts with ArrayLike "
            "(Signal | ArrayLike where a Signal is taken too), a list of "
            "records or texts with Sequence[...], and a mapping with "
            "Mapping[...]; a count a validator takes a numpy integer for with "
            "int | np.integer[Any], a band fraction with BandFraction | "
            "np.integer[Any], a flag with bool | np.bool_; a mapping keyed by "
            "float beside one keyed by int (BandMapping), and each mapping of a "
            "union a dict written in the call needs as its context in an "
            "overload head of its own; a window SciPy reads as a name or a "
            "tuple of a name and its parameters; a sample rate as the "
            "float every 'fs' of the API is. A parameter narrower on purpose "
            "goes in EXEMPT, a quantity of another family in FAMILY_EXEMPT, a "
            "field a caller-built record stores is admitted by its constructor "
            "(a TYPE_CHECKING __init__) or goes in CONSTRUCTOR_EXEMPT, at "
            "the top of scripts/check_parameter_annotations.py with its reason."
        )
    for table, key in stale:
        print(f"::error::{table} lists {key}, which needs no exemption any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
