#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a result that keeps the caller's array instead of a copy of its own.

``np.asarray`` hands back the very array it was given when that array is
already of the asked type, and so does every validation helper built on it.
A result that stores such an array shares memory with the caller: changing
the caller's array afterwards (``levels[0] = 0.0``, ``freqs *= 2``) changes a
result that was computed, judged and perhaps printed before, and nothing
raises. A view does the same (``levels[:, 0]``, ``levels.T``, ``reshape``).
``read_only`` applied to such an array does not help: it clears the flag on
the caller's own array, or on a view that still shares the caller's memory.

The rule: an array a function was handed, or a view of one, is kept only as
a copy of its own. Every public record that can hold an array inherits
``phonometry._internal.frozen.OwnsArrays``, which makes that copy when the
record is built, whoever builds it: a function of the package or a caller
writing the record by hand. Anything else that keeps an array (a plain
class, a private record) copies it through
``phonometry._internal.frozen.read_only_copy``. The check has five parts.

The first reads the classes: a public record (a dataclass or a named tuple
that a public module defines or lists in ``__all__``) with a field annotated
as anything that may hold an array, and that does not inherit
``OwnsArrays``, itself or through a record it extends, fails. No trail of
the second part reaches a record a caller builds by hand, so the record has
to copy for itself. :data:`RECORD_EXEMPT` is that part's escape hatch.

The second reads every function of the package and follows each parameter
through the statements of its body: the numpy calls that may hand back their
argument or a view of it (``asarray``, ``atleast_1d``, ``reshape``, ``ravel``,
``diag`` and their kin), basic indexing, attribute access, containers and a
dictionary's or a list's shallow ``copy``, records, and the package's own
functions whose return carries a parameter through (the validation helpers
first among them, summarised once for the whole tree). A copy
(``np.array``, an array's ``.copy()``, ``astype`` with its default
``copy=True``), indexing by a mask or by positions, or any arithmetic ends
the trail; a helper of the package counts as positions only when every
return of its own is a mask or positions, so one that returns a ``slice``
selects a view. A parameter annotated with a record of the package is read
field by field, and a field the record copies (every field of one that
inherits ``OwnsArrays``, or one its own ``__post_init__`` copies) carries
nothing; what a record that inherits ``OwnsArrays`` reads back from ``self``
in its ``__post_init__`` is its own copy already. An annotation is read
through the package's type aliases, so ``float | Field2D`` may hold an array
when ``Field2D`` is ``NDArray[np.float64]``. Five places are where an array
is kept:

* a field of a public dataclass or named tuple, passed to its constructor
  (``cls(...)`` and ``type(self)(...)`` included), when the field is
  annotated as an array or anything that may hold one and the record does
  not copy it itself;
* ``object.__setattr__(record, name, value)``: in a method of such a record,
  where the value read back from ``self`` in ``__post_init__`` is the
  constructor's argument, so a field normalised with
  ``np.asarray(self.levels)`` keeps the caller's array, and anywhere else on
  a public record, such as a factory patching the record it just built;
* ``dataclasses.replace(record, ...)`` on a record parameter, which keeps
  every array field it is not given, unless the record inherits
  ``OwnsArrays`` and copies them again;
* an attribute of a plain public class set in any of its methods
  (``self.name = value``, ``self.name.append(value)``, or
  ``self.name[key] = value`` on an attribute annotated as a list or a
  mapping), when the attribute is annotated as an array, or, with no
  annotation of its own, when a parameter the value carries is annotated as
  one or not at all: ``self._distances = distances`` keeps the caller's
  array for every method that hands it out later, and ``self.fs = fs`` with
  ``fs: float`` keeps a number;
* ``read_only(value)`` anywhere.

The third keeps the copy from being made twice: an argument handed to a
public record that inherits ``OwnsArrays`` and written as a copy
(``read_only_copy(x)``, ``np.copy(x)``, ``x.astype(t)``, ``read_only``
around a copy, or ``x.copy()`` for a field annotated as an array alone)
fails, because the record copies it again; a type that has to change is
written ``np.asarray(x, dtype=t)``, which converts only when it must. So
does a local name handed over bare or through ``read_only`` when every
binding of it is such a copy and nothing in the function, or in a helper of
the package it is passed to, writes into it, binds it again or keeps it or a
view of it: the copy then does nothing the record does not do. The reading of that last part only vouches for what it
can see (arithmetic, comparisons, sizes and shapes, numpy calls that build a
new array, ``math``, a few builtins), so a copy it cannot vouch for is left
alone and the rule never asks for a copy that keeps the caller's array whole
to be dropped.

The fourth vouches for the one array a record keeps without a copy: one a
factory passes through ``phonometry._internal.frozen.handed_over``, so that
the frames of a simulation or the field of a march are not held twice while
the record is built. That is right only when nothing else can reach the
array, and each call is proved so from the syntax or fails: it is an
argument of a record that inherits ``OwnsArrays``, built in the ``return``
statement; its argument is a name bound once, in the function's own scope
and to it alone, to a new array (``np.zeros``, ``np.empty``, ``np.ones``,
or ``None`` in one branch of a conditional); the function is no generator
and does not hand out its frame (``locals()``, ``vars()``, ``eval``,
``exec``); and every other read of the name writes into the array
(``name[...] = value``, ``+=`` included), tests it against ``None``, or
passes it to a function of the package, with no decorator, whose parameter
is used the same way, down to three calls deep. A view, a second name, a
container, a closure or a lambda rules it out. The function is found
however it is spelt: imported under another name, read as an attribute of
a module bound by any import (``_internal.frozen.handed_over``), or named
in a string (``getattr``). A call anywhere else (at module level, in a
lambda, the function named but not called) fails too, and this part has no
exemption: an array that cannot be proved alone is copied, as every other
one is.

The fifth reads the records a caller builds: one a public function takes
(or a record such a record holds), or one ``scripts/check_parameter_annotations.py``
lists as built by hand (``CALLER_BUILT``); a result one function hands whole
to another (``HANDED_ON_RESULTS`` of ``scripts/check_parameter_units.py``) is
none. A field of such a record annotated as a container of a fixed kind (an
array, a ``tuple``, a ``list`` or a set, aliases read, in any member of a
union) is converted by the record: its ``__post_init__``, or a method it calls
on ``self``, stores a value of its own in it (``object.__setattr__(self,
"levels", ...)``, by name, through a loop over field names, or through a
setter handed the name). Otherwise a list given to an array field is kept as
a list, an array given to a tuple field as an array, and the record holds what
its annotation says it does not, a list a caller can still append to inside a
frozen record. A store that gives the field back as it was given, itself or
wrapped in ``MappingProxyType``, ``read_only`` or ``cast`` without a copy,
converts nothing. :data:`KEPT_EXEMPT` is that part's escape hatch.

A private helper is held to the rule whatever its callers pass today: the
next caller may hand it the caller's array. The analysis reads names, not
types, so a scalar that travels the same path as an array is read as one
where the field it lands in could hold an array. :data:`EXEMPT` is the
escape hatch, keyed by file and function, and each entry carries the reason
it is one; an entry that covers nothing fails the check too.

What the check does not read: a result that holds a record it was given
whole (``BandPath`` objects in a prediction's ``paths``) holds that record,
not a copy of it, and the record answers for its own arrays; a function that
returns the caller's array bare, not inside a result, is outside the rule;
a record whose fields are all annotated as something that holds no array is
not required to inherit ``OwnsArrays``, so an array a caller puts in its
``float`` field anyway is kept as it was handed; a copy made by a helper
that returns it (``return values.copy()``) and handed to a record is not
read as made twice, since the helper's other callers may need it; and a
value whose path runs through code outside the package (a callback, a
library call it does not know) is read as a new value. The fourth part reads
names, so a frame reached by introspection (``sys._getframe``,
``inspect.currentframe``) from code a factory calls could still reach an
array handed over; no module of the package does that.
"""

from __future__ import annotations

import argparse
import ast
import functools
import pathlib
import re
import sys
from collections import ChainMap
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeGuard

from ast_scan import (
    COMPOUND_STATEMENTS,
    ROOT,
    assigned_value,
    assignment_target,
    binding_of,
    bindings_by_name,
    block_statements,
    empty_type_checking_bodies,
    exempted,
    for_the_type_checker,
    global_bindings,
    imported_names,
    live_bindings,
    live_class_members,
    own_names,
    python_files,
    relative,
    scope_nodes,
    scopes_around,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

#: Where the package lives; the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"

#: The base a record inherits to copy every array it is built with
#: (``phonometry._internal.frozen.OwnsArrays``).
MECHANISM = "OwnsArrays"

#: The function through which a factory hands the record it returns an array
#: it built, for the record to keep without a copy
#: (``phonometry._internal.frozen.handed_over``).
HANDOVER = "handed_over"

#: Public records that can hold an array and do not inherit :data:`MECHANISM`,
#: keyed by file and class, each with the reason.
RECORD_EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/io/_signal.py", "Signal"): (
        "copies its samples itself, into the C-ordered float64 layout it "
        "promises, and keeps them writeable for processing in place, as "
        "io.read's contract says (tests/io/test_io_read.py); its other "
        "fields hold no array"
    ),
}

#: Functions that may keep a parameter's array, keyed by file and qualified
#: function, each with the reason.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_internal/frozen.py", "_adopted"): (
        f"the {MECHANISM} mechanism keeping an array handed over: it seals "
        f"the array {HANDOVER} marked, which the check's fourth part proves "
        "nothing but the record can reach, and any other array it returns "
        "None for, so the record copies it"
    ),
    ("src/phonometry/_internal/frozen.py", "_take_ownership"): (
        f"the {MECHANISM} mechanism itself: what it stores on the record is "
        "the read-only copy _owned makes of each array, or the value as it "
        "was when it holds none; the check reads _owned's pass-through branch "
        "for the values with no array as the caller's array"
    ),
}

#: Fields of records a caller builds that keep a container of a fixed kind as
#: they were given, keyed by file and ``Record.field``, each with the reason.
KEPT_EXEMPT: dict[tuple[str, str], str] = {}

#: The numpy functions that may return their first argument, or a view of it.
_NUMPY_ALIASING = frozenset(
    {
        "asarray",
        "asanyarray",
        "ascontiguousarray",
        "asfortranarray",
        "asarray_chkfinite",
        "require",
        "atleast_1d",
        "atleast_2d",
        "atleast_3d",
        "ravel",
        "squeeze",
        "reshape",
        "transpose",
        "matrix_transpose",
        "permute_dims",
        "broadcast_to",
        "expand_dims",
        "moveaxis",
        "swapaxes",
        "rollaxis",
        "flip",
        "flipud",
        "fliplr",
        "rot90",
        "diagonal",
        "diag",
        "trim_zeros",
        "real",
        "imag",
        "real_if_close",
        "split",
        "array_split",
        "hsplit",
        "vsplit",
        "dsplit",
        "unstack",
        "sliding_window_view",
        "as_strided",
        "frombuffer",
    }
)

#: The numpy functions that return one view per array argument.
_NUMPY_ALIASING_EACH = frozenset(
    {"broadcast_arrays", "atleast_1d", "atleast_2d", "atleast_3d"}
)

#: The numpy functions whose result indexes an array by position or by mask,
#: so that indexing with it copies rather than views.
_NUMPY_INDEX = frozenset(
    {
        "argsort",
        "argwhere",
        "nonzero",
        "flatnonzero",
        "searchsorted",
        "digitize",
        "arange",
        "isfinite",
        "isnan",
        "isinf",
        "isclose",
        "isin",
        "logical_and",
        "logical_or",
        "logical_not",
        "logical_xor",
        "greater",
        "greater_equal",
        "less",
        "less_equal",
        "equal",
        "not_equal",
    }
)

#: The numpy functions that build an array from what they are given, whose
#: result selects by position when what they are given does or when they are
#: asked for integers or booleans.
_NUMPY_BUILDERS = frozenset(
    {"array", "asarray", "asanyarray", "ascontiguousarray", "atleast_1d", "fromiter"}
)

#: The numpy functions that allocate a new array from a shape alone, the only
#: arrays a factory may hand over (:data:`HANDOVER`).
_NUMPY_FRESH = frozenset({"zeros", "empty", "ones"})

#: Array methods that may return the array itself or a view of it.
_METHOD_ALIASING = frozenset(
    {
        "reshape",
        "ravel",
        "view",
        "squeeze",
        "transpose",
        "swapaxes",
        "diagonal",
        "__array__",
        # A mapping or a sequence of arrays hands its items out unchanged.
        "get",
        "values",
        "items",
        "pop",
        "setdefault",
    }
)

#: Attributes of an array that are plain numbers or metadata, never its data.
_SCALAR_ATTRIBUTES = frozenset(
    {"size", "shape", "ndim", "dtype", "itemsize", "nbytes", "flags", "strides"}
)

#: Builtins whose result holds the items of their argument unchanged.
_PASS_THROUGH_BUILTINS = frozenset(
    {
        "tuple",
        "list",
        "sorted",
        "reversed",
        "iter",
        "next",
        "dict",
        "set",
        "frozenset",
        "max",
        "min",
    }
)

#: Calls that wrap a container without copying what it holds.
_WRAPPERS = frozenset({"MappingProxyType", "read_only", "cast"})

#: The numpy functions that write into the array handed to them first
#: (``np.add.at`` and the other ``ufunc.at`` read as ``at``).
_NUMPY_WRITERS = frozenset(
    {
        "copyto",
        "put",
        "place",
        "putmask",
        "put_along_axis",
        "fill_diagonal",
        "shuffle",
        "at",
    }
)

#: Array methods that write into the array they are called on.
_METHOD_WRITERS = frozenset(
    {"sort", "fill", "resize", "put", "itemset", "setfield", "partition", "byteswap"}
)

#: Array methods whose result is a number or a new array, never the array
#: they are called on nor a view of it.
_METHOD_FRESH = frozenset(
    {
        "all",
        "any",
        "argmax",
        "argmin",
        "argsort",
        "astype",
        "clip",
        "conj",
        "conjugate",
        "cumprod",
        "cumsum",
        "dot",
        "item",
        "max",
        "mean",
        "min",
        "nonzero",
        "prod",
        "round",
        "searchsorted",
        "std",
        "sum",
        "tolist",
        "var",
    }
)

#: Attributes of an array that are views of its data.
_VIEW_ATTRIBUTES = frozenset({"T", "mT", "real", "imag", "flat"})

#: Builtins whose result holds none of the array they are handed.
_READING_BUILTINS = frozenset(
    {
        "abs",
        "bool",
        "complex",
        "float",
        "format",
        "int",
        "isinstance",
        "len",
        "repr",
        "str",
    }
)

#: Methods that put their argument into the container they are called on.
_CONTAINER_FILLERS = frozenset(
    {"append", "extend", "insert", "update", "add", "appendleft"}
)

#: Annotation words that say a field may hold an array.
_ARRAY_WORDS = ("ndarray", "NDArray", "ArrayLike", "Any", "object", "Real", "Complex")

Labels = frozenset[str]
_CLEAN: Labels = frozenset()


@dataclass(frozen=True)
class Shaped:
    """A tuple whose items are known one by one, as ``return a, b`` builds."""

    items: tuple[Value, ...]


@dataclass(frozen=True)
class Fields:
    """A record whose fields are known one by one.

    Built by its constructor, it carries what each field was given; read from
    a parameter annotated with a record class, each field that can hold an
    array carries the parameter, and :attr:`rest` is what any other attribute
    (a property, say) may carry.
    """

    items: tuple[tuple[str, Value], ...]
    rest: Labels = frozenset()

    def get(self, name: str) -> Value:
        """What one field carries.

        A name that is not a field the constructor was given is a default or a
        property; a property computes a new value from the fields, except on a
        record the caller handed over, where it may hand one of them out.
        """
        for key, value in self.items:
            if key == name:
                return value
        return self.rest


@dataclass(frozen=True)
class Many:
    """A sequence whose items all carry the same, as ``Sequence[Record]`` does."""

    item: Value


Value = Labels | Shaped | Fields | Many


def flat(value: Value) -> Labels:
    """Every parameter a value may carry, whatever its shape."""
    out: set[str] = set()
    if isinstance(value, Shaped):
        for item in value.items:
            out |= flat(item)
        return frozenset(out)
    if isinstance(value, Fields):
        for _, item in value.items:
            out |= flat(item)
        return frozenset(out | value.rest)
    if isinstance(value, Many):
        return flat(value.item)
    return value


def union(*values: Value) -> Value:
    """The value that may be any of *values*.

    A value that carries nothing adds nothing, so it keeps the shape of a
    tuple or a record the other branches agree on (``return None`` beside
    ``return a, b``).
    """
    carrying = [v for v in values if isinstance(v, Shaped | Fields) or v]
    if len(carrying) == 1:
        return carrying[0]
    shaped = [v for v in carrying if isinstance(v, Shaped)]
    if (
        shaped
        and len(shaped) == len(carrying)
        and len({len(v.items) for v in shaped}) == 1
    ):
        return Shaped(
            tuple(
                union(*parts) for parts in zip(*(v.items for v in shaped), strict=True)
            )
        )
    records = [v for v in carrying if isinstance(v, Fields)]
    if records and len(records) == len(carrying):
        merged: dict[str, Value] = {}
        rest: set[str] = set()
        for record in records:
            rest |= record.rest
            for key, item in record.items:
                merged[key] = union(merged[key], item) if key in merged else item
        return Fields(tuple(merged.items()), frozenset(rest))
    sequences = [v for v in carrying if isinstance(v, Many)]
    if sequences and len(sequences) == len(carrying):
        return Many(union(*(v.item for v in sequences)))
    out: set[str] = set()
    for value in carrying:
        out |= flat(value)
    return frozenset(out)


@dataclass(frozen=True)
class Finding:
    """One place where a parameter's array is kept without a copy."""

    path: str
    function: str
    line: int
    sink: str
    parameters: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the qualified function."""
        return self.path, self.function


@dataclass
class ClassInfo:
    """What the check needs to know of a class of the package."""

    name: str
    module: str
    record: bool
    bases: tuple[str, ...]
    line: int = 0
    fields: list[tuple[str, str]] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)
    #: The fields ``__post_init__`` stores again, each with whether every
    #: value it stores there is a copy: those the record owns, whoever built it.
    owned: dict[str, bool] = field(default_factory=dict)
    #: The same fields, each with whether every value stored there is passed
    #: through ``read_only`` or ``read_only_copy``: a copy nobody can write
    #: into, which a result may share without sharing anyone's edits.
    sealed: dict[str, bool] = field(default_factory=dict)
    #: The ``class`` statement read, one of several a key may have.
    node: ast.ClassDef | None = None


@dataclass
class FunctionInfo:
    """One function of the package, with the module it is read in."""

    module: str
    qualname: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    path: str
    owner: ClassInfo | None
    kind: str  # "function", "method", "classmethod" or "staticmethod"
    #: Defined inside another function, and read there, with its closure.
    nested: bool = False
    #: The definition of the function this one is written in, a class body
    #: around it passed over, as Python passes it over; ``None`` at the top
    #: of a module or of a class there.
    parent: FunctionInfo | None = None


#: What a name read where a ``def`` or a ``class`` of it stands, at the top of
#: a module or in a function that defines it, stood for there, by its key:
#: each ``def`` that stood, and each ``class`` statement that did, as the
#: class that statement makes (:meth:`Tree.stood_for`). A function and a
#: class of one name share a key, and so do two ``class`` statements of it,
#: so a name read in two places, or in a branch of each, may hold several.
_Pins = dict[tuple[str, str], list[FunctionInfo | ClassInfo]]


def _merge_pins(into: _Pins | None, found: _Pins) -> None:
    """Add what *found* pins to *into*, each definition once."""
    if into is None:
        return
    for key, definitions in found.items():
        held = into.setdefault(key, [])
        held.extend(
            definition
            for definition in definitions
            if all(definition is not other for other in held)
        )


def _pinned_functions(
    pins: _Pins | None, target: tuple[str, str]
) -> list[FunctionInfo]:
    """The definitions of *target* that stood where its name was read (*pins*)."""
    held = pins.get(target, []) if pins is not None else []
    return [found for found in held if isinstance(found, FunctionInfo)]


def _is_record_decorator(node: ast.expr) -> bool:
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id == "dataclass"
    return isinstance(target, ast.Attribute) and target.attr == "dataclass"


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def _module_name(path: pathlib.Path, root: pathlib.Path) -> str:
    parts = list(path.relative_to(root.parent).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


class Tree:
    """Every module, class and function of the package, and how names resolve."""

    def __init__(self, files: Sequence[pathlib.Path], root: pathlib.Path) -> None:
        self.package = root.name
        self.modules: dict[str, ast.Module] = {}
        self.paths: dict[str, str] = {}
        self.packages: set[str] = set()
        self.classes: dict[tuple[str, str], ClassInfo] = {}
        #: Every ``class`` statement of each class, by the key of
        #: :attr:`classes`, as :attr:`definitions` holds a function's: one
        #: written in each branch of an ``if``, or one a later one replaces
        #: after an alias took it, is a class of its own, with its own fields
        #: and bases. :attr:`classes` holds the last.
        self.class_definitions: dict[tuple[str, str], list[ClassInfo]] = {}
        self.class_by_name: dict[str, list[ClassInfo]] = {}
        self.functions: dict[tuple[str, str], FunctionInfo] = {}
        #: Every definition of each function, by the key of :attr:`functions`:
        #: one written in each branch of an ``if`` or a ``try`` is either at
        #: run time, and each is read. :attr:`functions` holds the last.
        self.definitions: dict[tuple[str, str], list[FunctionInfo]] = {}
        self.imports: dict[str, dict[str, tuple[str, str | None]]] = {}
        #: The statements each module binds a name with at its top, not inside
        #: a function or a class: its ``def`` and ``class`` statements and its
        #: imports, by the name, in the order of the source. What a bare name
        #: no function binds stands for is read from those it may hold.
        self.top_bindings: dict[str, dict[str, list[ast.AST]]] = {}
        #: The ``def``, ``class`` and import statements a function, a method
        #: or a class body of each module makes of a module name under
        #: ``global`` (:func:`ast_scan.global_bindings`), by the name: that
        #: function may have run before any read of the name, so each may
        #: stand wherever it is read, and through an import of it too.
        self.global_top: dict[str, dict[str, list[ast.AST]]] = {}
        #: The key of :attr:`functions` or :attr:`classes` of each ``def``
        #: and ``class`` statement of the package.
        self.qualnames: dict[ast.AST, tuple[str, str]] = {}
        #: The function or the class each of those statements makes.
        self.made_by: dict[ast.AST, FunctionInfo | ClassInfo] = {}
        #: What :meth:`resolve_top` and :meth:`live_definitions` found, read
        #: once for each name, as every pass of the fixed point asks again.
        self.top_cache: dict[
            tuple[str, str], tuple[tuple[tuple[str, str], ...], _Pins]
        ] = {}
        #: What :meth:`resolve_all` found, read once for each name.
        self.all_cache: dict[
            tuple[str, str], tuple[tuple[tuple[str, str], ...], _Pins]
        ] = {}
        self.live_cache: dict[tuple[str, str], list[FunctionInfo]] = {}
        self.numpy_names: dict[str, set[str]] = {}
        self.numpy_functions: dict[str, dict[str, str]] = {}
        self.exported: dict[str, tuple[str, ...]] = {}
        self.typed_cache: dict[tuple[ast.AST, str], Value] = {}
        #: Type aliases of the package, by name, as their definition reads.
        self.aliases: dict[str, str] = {}
        #: The aliases that stand for an array or for anything that may hold one.
        self.array_aliases: set[str] = set()
        #: The functions whose every return is a mask or an array of positions.
        self.positions: set[tuple[str, str]] = set()
        #: For each function read for a copy made twice, each node of its
        #: body with the node that holds it, and each name with its uses.
        self.syntax: dict[
            ast.AST, tuple[dict[ast.AST, ast.AST], dict[str, list[ast.Name]]]
        ] = {}
        for path in files:
            module = _module_name(path, root)
            tree = empty_type_checking_bodies(
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            )
            self.modules[module] = tree
            self.paths[module] = relative(path)
            if path.name == "__init__.py":
                self.packages.add(module)
        for module, tree in self.modules.items():
            self._read_module(module, tree)
        self._read_aliases()
        self.public: set[tuple[str, str]] = set()
        for (module, qualname), info in self.classes.items():
            if (
                not info.name.startswith("_")
                and "." not in qualname
                and _public_path(module)
            ):
                self.public.add((module, qualname))
        # A class of a private module reaches a caller only when a public
        # module lists it in ``__all__``; importing it to use it is not that.
        for module, names in self.exported.items():
            if not _public_path(module):
                continue
            for name in names:
                for resolved in self.resolve_all(module, name):
                    if resolved in self.classes:
                        self.public.add(resolved)

    def _read_module(self, module: str, tree: ast.Module) -> None:
        imports: dict[str, tuple[str, str | None]] = {}
        numpy_names: set[str] = set()
        numpy_functions: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                self._read_numpy_import(module, node, numpy_names, numpy_functions)
                imports.update(self._import_targets(module, node))
        self.imports[module] = imports
        # Read again, in the order of the source, from the module's own
        # statements alone: an import inside a function, read last by the
        # walk above, binds the name for that function. A name the top binds
        # to a function, a class, an import or an alias keeps every binding
        # of it there, so one of another kind (a lambda, a loop's target, a
        # call's result) ends what came before it and stands for nothing.
        self.top_bindings[module] = {
            name: list(nodes)
            for name, nodes in bindings_by_name(tree).items()
            if any(
                isinstance(node, _TOP_BINDINGS) or _aliases_a_name(node, tree)
                for node in nodes
            )
        }
        made: dict[str, list[ast.AST]] = {}
        for name, nodes in global_bindings(tree).items():
            statements: list[ast.AST] = [
                n
                for n in nodes
                if isinstance(n, _TOP_BINDINGS) or _aliases_a_name(n, tree)
            ]
            if statements:
                made[name] = statements
        self.global_top[module] = made
        self.exported[module] = _exported(tree)
        self.numpy_names[module] = numpy_names
        self.numpy_functions[module] = numpy_functions
        self._read_body(module, tree.body, "", None)

    def _read_aliases(self) -> None:
        """Which type aliases of the package may hold an array.

        ``Field2D = NDArray[np.float64]`` makes ``c: float | Field2D`` an
        array as surely as the alias's own text; an alias of an alias counts
        too.
        """
        for tree in self.modules.values():
            for node in _module_statements(tree.body):
                found = _alias(node)
                if found is not None:
                    self.aliases[found[0]] = found[1]
        changed = True
        while changed:
            changed = False
            for name, text in self.aliases.items():
                if name not in self.array_aliases and self.holds_array(text):
                    self.array_aliases.add(name)
                    changed = True

    def holds_array(self, annotation: str | None) -> bool:
        """Whether something so annotated may hold an array, aliases read."""
        if holds_array(annotation):
            return True
        return annotation is not None and any(
            word in self.array_aliases for word in _words(annotation)
        )

    def _read_body(
        self,
        module: str,
        body: Iterable[ast.stmt],
        scope: str,
        owner: ClassInfo | None,
        *,
        nested: bool = False,
        parent: FunctionInfo | None = None,
    ) -> None:
        path = self.paths[module]
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualname = f"{scope}.{node.name}" if scope else node.name
                record = any(
                    _is_record_decorator(d) for d in node.decorator_list
                ) or any(_base_name(b) == "NamedTuple" for b in node.bases)
                info = ClassInfo(
                    node.name,
                    module,
                    record,
                    tuple(_base_name(b) for b in node.bases),
                    node.lineno,
                    node=node,
                )
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(
                        item.target, ast.Name
                    ):
                        annotation = ast.unparse(item.annotation)
                        if annotation.startswith(("ClassVar", "typing.ClassVar")):
                            continue
                        if annotation in {"KW_ONLY", "dataclasses.KW_ONLY"}:
                            continue
                        if _excluded_from_init(item.value):
                            info.attributes[item.target.id] = annotation
                            continue
                        info.fields.append((item.target.id, annotation))
                        info.attributes[item.target.id] = annotation
                self.classes[(module, qualname)] = info
                self.class_definitions.setdefault((module, qualname), []).append(info)
                self.qualnames[node] = (module, qualname)
                self.made_by[node] = info
                self.class_by_name.setdefault(node.name, []).append(info)
                self._read_body(module, node.body, qualname, info, parent=parent)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qualname = f"{scope}.{node.name}" if scope else node.name
                kind = "function"
                if owner is not None:
                    kind = "method"
                    for decorator in node.decorator_list:
                        name = _base_name(decorator)
                        if name in {"classmethod", "staticmethod"}:
                            kind = name
                function = FunctionInfo(
                    module, qualname, node, path, owner, kind, nested, parent
                )
                self.functions[(module, qualname)] = function
                self.qualnames[node] = (module, qualname)
                self.made_by[node] = function
                self.definitions.setdefault((module, qualname), []).append(function)
                if owner is not None and not owner.record:
                    # ``self.p: Field2D = ...`` in a method annotates the
                    # attribute for every method of a plain class.
                    for inner in ast.walk(node):
                        if (
                            isinstance(inner, ast.AnnAssign)
                            and isinstance(inner.target, ast.Attribute)
                            and isinstance(inner.target.value, ast.Name)
                            and inner.target.value.id == "self"
                        ):
                            owner.attributes.setdefault(
                                inner.target.attr, ast.unparse(inner.annotation)
                            )
                self._read_body(
                    module, node.body, qualname, None, nested=True, parent=function
                )
            elif isinstance(node, COMPOUND_STATEMENTS):
                self._read_body(
                    module,
                    block_statements(node),
                    scope,
                    owner,
                    nested=nested,
                    parent=parent,
                )

    def _read_numpy_import(
        self,
        module: str,
        node: ast.Import | ast.ImportFrom,
        names: set[str],
        functions: dict[str, str],
    ) -> None:
        """Add the names an import binds to NumPy, or to a function of it."""
        if isinstance(node, ast.Import):
            names.update(
                alias.asname or "numpy" for alias in node.names if alias.name == "numpy"
            )
        elif self.source_of(module, node).startswith("numpy"):
            for alias in node.names:
                functions[alias.asname or alias.name] = alias.name

    def _import_targets(
        self, module: str, node: ast.Import | ast.ImportFrom
    ) -> dict[str, tuple[str, str | None]]:
        """What each name an import of the package binds stands for: a module
        (its name and ``None``), or a name of a module.
        """
        if isinstance(node, ast.Import):
            return {
                alias.asname: (alias.name, None)
                for alias in node.names
                if alias.asname and _inside(alias.name, self.package)
            }
        source = self.source_of(module, node)
        if not _inside(source, self.package) or source.startswith("numpy"):
            return {}
        targets: dict[str, tuple[str, str | None]] = {}
        for alias in node.names:
            local = alias.asname or alias.name
            if f"{source}.{alias.name}" in self.modules:
                targets[local] = (f"{source}.{alias.name}", None)
            else:
                targets[local] = (source, alias.name)
        return targets

    def source_of(self, module: str, node: ast.ImportFrom) -> str:
        """The module an ``from ... import`` written in *module* reads from."""
        if not node.level:
            return node.module or ""
        package = module if module in self.packages else module.rpartition(".")[0]
        base = package.split(".")
        base = base[: len(base) - node.level + 1]
        return ".".join([*base, node.module] if node.module else base)

    def imported(
        self,
        module: str,
        node: ast.AST,
        name: str,
        depth: int = 0,
        *,
        pins: _Pins | None = None,
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package an import in *module* may
        bind *name* to, when *node* is a ``from ... import`` that binds it
        (:meth:`resolve_all`).
        """
        if not isinstance(node, ast.ImportFrom):
            return ()
        source = self.source_of(module, node)
        for alias in node.names:
            if (alias.asname or alias.name) != name:
                continue
            if f"{source}.{alias.name}" in self.modules:
                return ()
            return self.resolve_all(source, alias.name, depth, pins=pins)
        return ()

    def every_definition(self) -> Iterator[FunctionInfo]:
        """Every definition of every function, two of one name included."""
        for found in self.definitions.values():
            yield from found

    def resolve_top(
        self,
        module: str,
        name: str,
        point: ast.AST | None = None,
        depth: int = 0,
        *,
        pins: _Pins | None = None,
    ) -> tuple[tuple[str, str], ...]:
        """Each ``(module, qualname)`` a bare name may stand for at the top of *module*.

        What the module defines, imports or assigns a dotted name to at its
        top (:meth:`aliased`), that the name may hold where *point*, a node
        of the module, reads it, or once the module has run when it is None
        (:func:`ast_scan.live_bindings`): a ``def`` in each branch of an
        ``if``, or an import in a ``try`` and another in its ``except``
        clause, is either, and a read inside a function meets every one from
        the ``def`` on, since the function may be called during the import.
        An import written inside one of its functions binds the name for that
        function alone. Each ``def`` that stands there is pinned in *pins*
        (:meth:`_bound_at_top`), so an alias holds the definition its value
        named where it was bound.
        """
        if depth > _DEPTH:
            return ()
        key = (module, name)
        if point is None and depth == 0 and key in self.top_cache:
            cached, pinned = self.top_cache[key]
            _merge_pins(pins, pinned)
            return cached
        held: _Pins = {}
        statements = self.top_bindings.get(module, {}).get(name, [])
        found = [
            target
            for statement in live_bindings(self.modules[module], statements, point)
            for target in self._bound_at_top(module, statement, name, depth, pins=held)
        ]
        swapped = self.made_under_global(module, name, depth, pins=held)
        resolved = tuple(dict.fromkeys((*found, *swapped)))
        _merge_pins(pins, held)
        if point is None and depth == 0:
            self.top_cache[key] = (resolved, held)
        return resolved

    def made_under_global(
        self, module: str, name: str, depth: int = 0, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package that a function, a method or
        a class body of *module* binds the module's *name* to under
        ``global`` (:attr:`global_top`), which may stand at any read of it.
        """
        found = (
            target
            for statement in self.global_top.get(module, {}).get(name, [])
            for target in self._bound_at_top(module, statement, name, depth, pins=pins)
        )
        return tuple(dict.fromkeys(found))

    def live_definitions(self, target: tuple[str, str]) -> list[FunctionInfo]:
        """The definitions of a function of a module, or of a class there,
        that the name may hold once the module has run: a method of a class
        a later ``class`` of its name replaces is none
        (:func:`ast_scan.live_class_members`).
        """
        if target not in self.live_cache:
            definitions = self.definitions[target]
            root = self.modules[definitions[0].module]
            nodes = {definition.node: definition for definition in definitions}
            self.live_cache[target] = [
                nodes[node] for node in live_class_members(root, list(nodes))
            ]
        return self.live_cache[target]

    def _bound_at_top(
        self,
        module: str,
        statement: ast.AST,
        name: str,
        depth: int = 0,
        *,
        pins: _Pins | None = None,
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package one statement of *module*
        that binds the module's *name* may bind it to: its own ``def`` or
        ``class``, at the top or inside a function that declares the name
        ``global``, what an import reads (:meth:`imported`), or what the
        dotted name an assignment binds it to names (:meth:`aliased`).

        A ``def`` of a function at the top of the module goes into *pins*
        under its key, as the definition the name stands for where it was
        read, and a ``class`` there goes in as the class that statement
        makes, which a call of it makes an instance of (:meth:`stood_for`):
        a name read in two places, an alias bound to a ``def`` in one branch
        and to the ``class`` of its name in the other, holds both, and one
        bound before a later ``class`` of its name replaced the class holds
        the class it was bound to.
        """
        if assignment_target(statement) is not None:
            return self.aliased(module, statement, depth, pins=pins)
        if isinstance(statement, ast.Import | ast.ImportFrom):
            return self.imported(module, statement, name, depth, pins=pins)
        key = self.qualnames.get(statement)
        known = key is not None and (key in self.functions or key in self.classes)
        if key is None or not known:
            return ()
        definitions = self.definitions.get(key, [])
        if pins is not None and all(
            definition.parent is None and definition.owner is None
            for definition in definitions
        ):
            _merge_pins(pins, {key: self.stood_for(key, statement)})
        return (key,)

    def classes_stood(
        self, key: tuple[str, str], pins: _Pins | None
    ) -> list[ClassInfo]:
        """The classes a name of *key* may stand for: each ``class``
        statement of it that stood where the name was read (*pins*), or
        every one of the key when none was pinned there, as each may stand.
        """
        held = pins.get(key, []) if pins is not None else []
        stood = [found for found in held if isinstance(found, ClassInfo)]
        return stood or list(self.class_definitions.get(key, []))

    def stood_for(
        self, key: tuple[str, str], statement: ast.AST
    ) -> list[FunctionInfo | ClassInfo]:
        """The function or the class one ``def`` or ``class`` *statement* of
        *key* makes: what a name it binds stands for where that statement
        stood.
        """
        made = self.made_by.get(statement)
        return [made] if made is not None and self.qualnames[statement] == key else []

    def aliased(
        self, module: str, target: ast.AST, depth: int = 0, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package an assignment in *module* of
        a dotted name alone (``alias = handing_back``, ``check =
        validation.require_finite_array``, ``(fn := handing_back)``) binds
        *target*, its target or the assignment expression, to: what that name
        stands for where the assignment reads it (:meth:`named_at`).
        """
        value = assigned_value(self.modules[module], target)
        if value is None or depth > _DEPTH:
            return ()
        return self.named_at(module, value, depth + 1, pins=pins)

    def named_at(
        self, module: str, value: ast.expr, depth: int = 0, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package a dotted name read in
        *module* stands for where it is read.

        A bare name is looked up as Python looks it up
        (:func:`ast_scan.binding_of`): what the module binds it to there
        (:meth:`resolve_top`), or what the scope that binds it does
        (:meth:`bound_in`). An attribute of a module of the package is what
        that module binds the name to once it has run (:meth:`resolve_all`).
        """
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
            source = self.resolve_module(module, value.value.id)
            if source is None:
                return ()
            return self.resolve_all(source, value.attr, depth, pins=pins)
        if not isinstance(value, ast.Name):
            return ()
        root = self.modules[module]
        how, scope = binding_of(root, value, value.id)
        if how == "global" or scope is None or scope is root:
            return self.resolve_top(module, value.id, value, depth, pins=pins)
        return self.bound_in(module, scope, value.id, value, depth, pins=pins)

    def bound_in(
        self,
        module: str,
        scope: ast.AST,
        name: str,
        point: ast.AST | None,
        depth: int = 0,
        *,
        pins: _Pins | None = None,
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package *name* stands for in *scope*
        of *module*, which binds it itself, where *point* reads it, or
        anywhere in it when *point* is None: its ``def`` or ``class``, what
        its imports read, and what its assignments of a dotted name name
        (:meth:`aliased`). A parameter, or any other binding that may hold
        it there, stands for what the guard cannot tell, and so the name
        stands for nothing of the package. Each ``def`` and ``class`` of a
        name a class takes that stands there goes into *pins*
        (:meth:`stood_for`).
        """
        if depth > _DEPTH or name in own_names(scope).parameters:
            return ()
        nodes = bindings_by_name(scope).get(name, [])
        if point is not None:
            nodes = live_bindings(scope, nodes, point)
        found: list[tuple[str, str]] = []
        for node in nodes:
            if assignment_target(node) is not None:
                if not _aliases_a_name(node, self.modules[module]):
                    return ()
                found.extend(self.aliased(module, node, depth, pins=pins))
            elif isinstance(node, ast.Import | ast.ImportFrom):
                found.extend(self.imported(module, node, name, depth, pins=pins))
            elif (key := self.qualnames.get(node)) is not None and (
                key in self.functions or key in self.classes
            ):
                found.append(key)
                if key in self.classes:
                    _merge_pins(pins, {key: self.stood_for(key, node)})
            else:
                return ()
        return tuple(dict.fromkeys(found))

    def resolve(self, module: str, name: str, depth: int = 0) -> tuple[str, str] | None:
        """The ``(module, qualname)`` a bare name of *module* stands for."""
        if (module, name) in self.functions or (module, name) in self.classes:
            return module, name
        target = self.imports.get(module, {}).get(name)
        if target is None or depth > 8:
            return None
        source, attribute = target
        if attribute is None:
            return None
        return self.resolve(source, attribute, depth + 1)

    def resolve_all(
        self, module: str, name: str, depth: int = 0, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each ``(module, qualname)`` a bare name of *module* may stand for
        once it has run, read from another module or as the module's
        attribute: what the bindings of its top that still stand at its end
        bind it to (:meth:`resolve_top`), so a ``def``, an import or an
        alias a later one replaces stands for nothing, and every function or
        class a function of a module on the way binds the name to under
        ``global`` (:meth:`made_under_global`). A name its top never binds is
        what :meth:`resolve` finds.
        """
        if depth > _DEPTH:
            return ()
        if self.top_bindings.get(module, {}).get(name):
            key = (module, name)
            if depth == 0 and key in self.all_cache:
                cached, pinned = self.all_cache[key]
                _merge_pins(pins, pinned)
                return cached
            held: _Pins = {}
            found = self.resolve_top(module, name, None, depth + 1, pins=held)
            _merge_pins(pins, held)
            if depth == 0:
                self.all_cache[key] = (found, held)
            return found
        swapped = self.made_under_global(module, name, depth + 1, pins=pins)
        if (module, name) in self.functions or (module, name) in self.classes:
            return tuple(dict.fromkeys(((module, name), *swapped)))
        target = self.imports.get(module, {}).get(name)
        if target is None or target[1] is None:
            return swapped
        found = self.resolve_all(target[0], target[1], depth + 1, pins=pins)
        return tuple(dict.fromkeys((*found, *swapped)))

    def functions_named(self, module: str) -> set[str]:
        """The bare names *module* binds to functions of the package."""
        names = {q for (m, q) in self.functions if m == module and "." not in q}
        names |= {
            name
            for name in (*self.global_top.get(module, {}), *self.top_bindings[module])
            if any(key in self.functions for key in self.resolve_top(module, name))
        }
        names |= {
            local
            for local, (source, attribute) in self.imports.get(module, {}).items()
            if attribute is not None
        }
        return names

    def resolve_module(self, module: str, name: str) -> str | None:
        """The module a bare name of *module* stands for, if it is one."""
        target = self.imports.get(module, {}).get(name)
        if target is not None and target[1] is None:
            return target[0]
        return None

    def record_fields(self, info: ClassInfo) -> list[tuple[str, str]]:
        """The constructor's fields of a record, the inherited ones first."""
        fields: list[tuple[str, str]] = []
        for base in info.bases:
            for candidate in self.class_by_name.get(base, []):
                if candidate.record:
                    fields.extend(self.record_fields(candidate))
                    break
        names = {name for name, _ in info.fields}
        return [f for f in fields if f[0] not in names] + info.fields

    def copies_arrays(self, info: ClassInfo) -> bool:
        """Whether a record inherits :data:`MECHANISM`, itself or through a
        record it extends, and so copies every array it is built with.
        """
        if MECHANISM in info.bases:
            return True
        return any(
            candidate.record and self.copies_arrays(candidate)
            for base in info.bases
            for candidate in self.class_by_name.get(base, [])
        )

    def owns(self, info: ClassInfo, name: str) -> bool:
        """Whether a record copies a field itself: every field of one that
        inherits :data:`MECHANISM`, or one its own or a base's
        ``__post_init__`` copies.
        """
        if info.owned.get(name) or self.copies_arrays(info):
            return True
        for base in info.bases:
            for candidate in self.class_by_name.get(base, []):
                if candidate.record and self.owns(candidate, name):
                    return True
        return False

    def seals(self, info: ClassInfo, name: str) -> bool:
        """Whether a record publishes a field as a read-only copy of its own."""
        if self.copies_arrays(info) or (
            info.sealed.get(name) and self.owns(info, name)
        ):
            return True
        for base in info.bases:
            for candidate in self.class_by_name.get(base, []):
                if candidate.record and self.seals(candidate, name):
                    return True
        return False

    def attribute_annotation(self, info: ClassInfo, name: str) -> str | None:
        """The annotation of an attribute of a class, looked up its bases too."""
        if name in info.attributes:
            return info.attributes[name]
        for base in info.bases:
            for candidate in self.class_by_name.get(base, []):
                found = self.attribute_annotation(candidate, name)
                if found is not None:
                    return found
        return None


def _inside(module: str, package: str) -> bool:
    """Whether a dotted module name belongs to *package*."""
    return module == package or module.startswith(f"{package}.")


def _exported(tree: ast.Module) -> tuple[str, ...]:
    """The names a module's ``__all__`` lists, however it is spelt."""
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign | ast.AugAssign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                continue
            if node.value is None:
                continue
            names.extend(
                item.value
                for item in ast.walk(node.value)
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
    return tuple(names)


def _public_path(module: str) -> bool:
    """Whether every part of a dotted module name is public."""
    return not any(part.startswith("_") for part in module.split("."))


def _excluded_from_init(value: ast.expr | None) -> bool:
    """Whether a dataclass field is declared ``field(init=False)``."""
    if not isinstance(value, ast.Call) or _base_name(value.func) != "field":
        return False
    return any(
        k.arg == "init" and isinstance(k.value, ast.Constant) and k.value.value is False
        for k in value.keywords
    )


def _module_statements(body: Iterable[ast.stmt]) -> Iterable[ast.stmt]:
    """A module's statements, those under ``if TYPE_CHECKING:`` and the like too."""
    for node in body:
        if isinstance(node, COMPOUND_STATEMENTS):
            yield from _module_statements(block_statements(node))
        else:
            yield node


def _alias(node: ast.stmt) -> tuple[str, str] | None:
    """The name and the text of a type alias a statement defines, if it does.

    ``type Name = ...``, ``Name: TypeAlias = ...`` and a plain assignment whose
    value reads as a type (a subscript, a union, a dotted name) are aliases;
    a call, a number or a tuple of values is not.
    """
    if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
        return node.name.id, ast.unparse(node.value)
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
        and _base_name(node.annotation) == "TypeAlias"
    ):
        return node.target.id, ast.unparse(node.value)
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Subscript | ast.BinOp | ast.Attribute)
        and (
            not isinstance(node.value, ast.BinOp)
            or isinstance(node.value.op, ast.BitOr)
        )
    ):
        return node.targets[0].id, ast.unparse(node.value)
    return None


#: Annotation words that say a field holds a container, whose ``copy`` is
#: the container's.
_CONTAINER_WORDS = frozenset(
    {"dict", "Mapping", "MappingProxyType", "list", "Sequence", "tuple", "set"}
)


def _method_copy(node: ast.Call) -> bool:
    """Whether a call is ``something.copy()``, with no argument."""
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "copy"
        and not node.args
        and not node.keywords
    )


def _method_astype(node: ast.Call) -> bool:
    """Whether a call is ``something.astype(...)`` that copies.

    It copies unless ``copy=False`` is written, even when the array already
    has the type asked for.
    """
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "astype"
        and not any(
            keyword.arg == "copy"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in node.keywords
        )
    )


#: A numpy scalar class written with its type argument, ``np.integer[Any]``:
#: one number, whose ``Any`` says nothing about an array.
_NUMPY_SCALAR_ARGUMENT = re.compile(
    r"\b(?:np|numpy)\.(?:generic|number|integer|signedinteger|unsignedinteger"
    r"|inexact|floating|complexfloating)\[[^\[\]]*\]"
)


def holds_array(annotation: str | None) -> bool:
    """Whether a field so annotated may hold an array.

    The type argument of a numpy scalar class is left out first, so that
    ``int | np.integer[Any]``, a count numpy code hands over, is one number
    and not the ``Any`` that may be an array.
    """
    if annotation is None:
        return True
    text = _NUMPY_SCALAR_ARGUMENT.sub("number", annotation)
    return any(word in text for word in _ARRAY_WORDS)


@dataclass
class Summary:
    """What a function's return value carries of its parameters."""

    value: Value = _CLEAN


def _helpers_written_in(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """How many functions are written in *function*'s own body, through its
    compound statements, not inside another function or a class.
    """
    count = 0
    pending: list[ast.stmt] = list(function.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            count += 1
        else:
            pending.extend(block_statements(node))
    return count


class Reader:
    """Follows the parameters of one function through its body."""

    def __init__(
        self,
        tree: Tree,
        function: FunctionInfo,
        summaries: Mapping[ast.AST, Summary],
        findings: list[Finding] | None,
        closure: Mapping[str, Value] | None = None,
        enclosing: Mapping[ast.AST, tuple[Value, frozenset[str]]] | None = None,
        helpers: Mapping[ast.AST, tuple[Value, frozenset[str]]] | None = None,
    ) -> None:
        self.tree = tree
        self.function = function
        self.closure = dict(closure or {})
        #: What each function written in the functions around this one returns,
        #: read where it is defined (:attr:`nested_returns` of those): a
        #: sibling helper this one calls hands back its closure through it.
        self.enclosing: Mapping[ast.AST, tuple[Value, frozenset[str]]] = (
            enclosing if enclosing is not None else {}
        )
        self.module = function.module
        self.summaries = summaries
        self.findings = findings
        self.returned: Value = _CLEAN
        self.constants: dict[str, tuple[str, ...]] = {}
        self.index_names: set[str] = set()
        self.container_names: set[str] = set()
        #: Local names bound to a record built here, with its class.
        self.record_names: dict[str, ClassInfo] = {}
        #: Whether each ``return`` read so far hands out a mask or positions.
        self.index_returns: list[bool] = []
        #: What each function defined here returns, read where it is defined
        #: with what its closure holds there, and the labels that closure
        #: carries, which a call of it hands back as they are.
        #: *helpers* seeds it: what each returned on a pass before, so that a
        #: helper written before a sibling it calls reads what that returns.
        self.nested_returns: dict[ast.AST, tuple[Value, frozenset[str]]] = dict(
            helpers or {}
        )
        self.post_init = (
            function.owner is not None and function.node.name == "__post_init__"
        )
        self.plain_method = (
            function.owner is not None
            and not function.owner.record
            and function.kind == "method"
        )

    # -- the parameters -------------------------------------------------
    def start(self) -> dict[str, Value]:
        """Every parameter carries itself; ``self`` and ``cls`` carry nothing;
        a name of a type parameter is the function's, not its closure's.
        """
        arguments = self.function.node.args
        names = [
            a.arg
            for a in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        ]
        if arguments.vararg:
            names.append(arguments.vararg.arg)
        if arguments.kwarg:
            names.append(arguments.kwarg.arg)
        annotations = {
            a.arg: a.annotation
            for a in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        }
        types = own_names(self.function.node).type_parameters
        env: dict[str, Value] = {
            name: value for name, value in self.closure.items() if name not in types
        }
        for index, name in enumerate(names):
            if index == 0 and self.function.kind in {"method", "classmethod"}:
                env[name] = _CLEAN
                continue
            env[name] = self.typed(name, annotations.get(name))
        owner = self.function.owner
        if self.post_init and owner is not None:
            # A record that copies its arrays has done so before its own
            # ``__post_init__`` runs: what that reads back from ``self`` is
            # the record's copy, not the constructor's argument.
            copied = self.tree.copies_arrays(owner)
            for name, _ in self.tree.record_fields(owner):
                env[f"self.{name}"] = _CLEAN if copied else frozenset({f"self.{name}"})
        return env

    def typed(self, name: str, annotation: ast.expr | None) -> Value:
        """What a parameter carries, read through its annotation.

        A record of the package carries the parameter in each field that can
        hold an array and that the record does not copy for itself; a sequence
        of records carries one such record per item. Anything else carries the
        parameter whole.
        """
        cache = self.tree.typed_cache
        # By the definition: two of one name, one in each branch of an
        # ``if``, may annotate the parameter with two records.
        key = (self.function.node, name)
        if key not in cache:
            cache[key] = self._typed(name, annotation)
        return cache[key]

    def _typed(self, name: str, annotation: ast.expr | None) -> Value:
        label: Labels = frozenset({name})
        if annotation is None:
            return label
        shape = _record_annotation(annotation)
        if shape is None:
            return label
        word, many = shape
        candidates = [i for i in self.tree.class_by_name.get(word, []) if i.record]
        if len(candidates) != 1:
            return label
        info = candidates[0]
        record = Fields(
            tuple(
                (
                    field_name,
                    label
                    if self.tree.holds_array(annotation_text)
                    and not self.tree.seals(info, field_name)
                    else _CLEAN,
                )
                for field_name, annotation_text in self.tree.record_fields(info)
            ),
            label,
        )
        return Many(record) if many else record

    def run(self) -> Value:
        """Read the body, report the kept arrays, and return what is returned.

        A function with two helpers or more written in it is read first, with
        no finding kept, until what each helper returns settles
        (:meth:`settled_helpers`): a helper is read where it is written, so
        one written before a sibling it calls would otherwise read that
        sibling as returning nothing.
        """
        if _helpers_written_in(self.function.node) > 1:
            self.nested_returns.update(self.settled_helpers())
        self.block(self.function.node.body, self.start())
        return self.returned

    def settled_helpers(self) -> dict[ast.AST, tuple[Value, frozenset[str]]]:
        """What each helper written in this function returns, once a pass of
        the body over what the pass before found finds no more.

        Each pass only adds to what a helper may return, and settles at least
        one more helper of a chain written before the sibling each calls, so
        one more pass than the helpers written in the function finds nothing
        new. Past that bound the guard stops with an error rather than read
        the helpers as they stood: a value no pass settled is no reading.

        :raises RuntimeError: when the helpers have not settled by the bound.
        """
        held: dict[ast.AST, tuple[Value, frozenset[str]]] = {}
        passes = _helpers_written_in(self.function.node) + 1
        for _ in range(passes):
            trial = Reader(
                self.tree,
                self.function,
                self.summaries,
                None,
                self.closure,
                self.enclosing,
                held,
            )
            trial.block(self.function.node.body, trial.start())
            if trial.nested_returns == held:
                return held
            held = trial.nested_returns
        msg = (
            f"{self.function.path}: what the helpers written in "
            f"{self.function.qualname} return did not settle in {passes} passes"
        )
        raise RuntimeError(msg)

    # -- statements ------------------------------------------------------
    def block(
        self, body: Iterable[ast.stmt], env: dict[str, Value]
    ) -> dict[str, Value]:
        for statement in body:
            env = self.statement(statement, env)
        return env

    def statement(self, node: ast.stmt, env: dict[str, Value]) -> dict[str, Value]:
        if isinstance(node, ast.Assign):
            value = self.expr(node.value, env)
            for target in node.targets:
                self.assign(target, value, env, node.value)
            return env
        if isinstance(node, ast.AnnAssign):
            if node.value is not None:
                value = self.expr(node.value, env)
                if isinstance(node.target, ast.Attribute):
                    self.keep_attribute(
                        node.target, value, ast.unparse(node.annotation)
                    )
                else:
                    self.assign(node.target, value, env, node.value)
            return env
        if isinstance(node, ast.AugAssign):
            # ``items += [x]`` keeps x in a list; ``levels += x`` adds x's
            # values into an array.
            value = self.expr(node.value, env)
            if (
                isinstance(node.target, ast.Name)
                and node.target.id in self.container_names
            ):
                env[node.target.id] = union(env.get(node.target.id, _CLEAN), value)
            return env
        if isinstance(node, ast.Expr):
            self.expr(node.value, env)
            return env
        if isinstance(node, ast.Return):
            self.index_returns.append(
                node.value is not None and self.indexes(node.value)
            )
            if node.value is not None:
                self.returned = union(self.returned, self.expr(node.value, env))
            return env
        if isinstance(node, ast.If):
            self.expr(node.test, env)
            return merge(
                self.block(node.body, dict(env)), self.block(node.orelse, dict(env))
            )
        if isinstance(node, ast.For | ast.AsyncFor):
            return self.loop(node, env)
        if isinstance(node, ast.While):
            self.expr(node.test, env)
            after = env
            for _ in range(2):
                after = merge(after, self.block(node.body, dict(after)))
            return merge(after, self.block(node.orelse, dict(after)))
        if isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                value = self.expr(item.context_expr, env)
                if item.optional_vars is not None:
                    self.assign(item.optional_vars, value, env, item.context_expr)
            return self.block(node.body, env)
        if isinstance(node, ast.Try | ast.TryStar):
            body = self.block(node.body, dict(env))
            branches = [
                body,
                self.block(node.orelse, dict(body)),
                *(
                    self.block(handler.body, merge(env, body))
                    for handler in node.handlers
                ),
            ]
            joined = merge(*branches)
            return self.block(node.finalbody, joined)
        if isinstance(node, ast.Match):
            self.expr(node.subject, env)
            return merge(
                env, *(self.block(case.body, dict(env)) for case in node.cases)
            )
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # A nested function is read where it is defined, with what its
            # closure holds there.
            key = (self.module, f"{self.function.qualname}.{node.name}")
            for inner in self.tree.definitions.get(key, ()):
                if inner.node is node:
                    returned = Reader(
                        self.tree,
                        inner,
                        self.summaries,
                        self.findings,
                        env,
                        ChainMap(self.nested_returns, dict(self.enclosing)),
                    ).run()
                    closure = frozenset().union(*(flat(v) for v in env.values()))
                    self.nested_returns[node] = (returned, closure)
            return env
        if isinstance(node, ast.Delete):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env.pop(target.id, None)
            return env
        return env

    def loop(
        self, node: ast.For | ast.AsyncFor, env: dict[str, Value]
    ) -> dict[str, Value]:
        names = _constant_strings(node.iter, self.constants)
        if self.post_init and names is not None and isinstance(node.target, ast.Name):
            # ``for name in ("a", "b"): object.__setattr__(self, name, ...)``
            for name in names:
                self.constants[node.target.id] = (name,)
                env = self.block(node.body, env)
            self.constants.pop(node.target.id, None)
            return self.block(node.orelse, env)
        element = self.element(node.iter, env)
        after = env
        for _ in range(2):
            inner = dict(after)
            self.assign(node.target, element, inner, None)
            after = merge(after, self.block(node.body, inner))
        return merge(after, self.block(node.orelse, dict(after)))

    def element(self, node: ast.expr, env: dict[str, Value]) -> Value:
        """What one item of an iteration over *node* carries."""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "enumerate" and node.args:
                return Shaped((_CLEAN, self.element(node.args[0], env)))
            if node.func.id == "zip":
                return Shaped(tuple(self.element(a, env) for a in node.args))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "items"
        ):
            return Shaped((_CLEAN, flat(self.expr(node.func.value, env))))
        value = self.expr(node, env)
        if isinstance(value, Shaped):
            return union(*value.items) if value.items else _CLEAN
        if isinstance(value, Many):
            return value.item
        return value

    def assign(
        self,
        target: ast.expr,
        value: Value,
        env: dict[str, Value],
        source: ast.expr | None,
    ) -> None:
        if isinstance(target, ast.Name):
            env[target.id] = value
            strings = (
                _constant_strings(source, self.constants)
                if source is not None
                else None
            )
            if strings is not None:
                self.constants[target.id] = strings
            self.index_names.discard(target.id)
            self.container_names.discard(target.id)
            self.record_names.pop(target.id, None)
            if source is not None and self.indexes(source):
                self.index_names.add(target.id)
            if source is not None and self.builds_container(source):
                self.container_names.add(target.id)
            built = self.built_record(source)
            if built is not None:
                self.record_names[target.id] = built
            return
        if isinstance(target, ast.Tuple | ast.List):
            if (
                isinstance(value, Shaped)
                and len(value.items) == len(target.elts)
                and not any(isinstance(e, ast.Starred) for e in target.elts)
            ):
                for element, item in zip(target.elts, value.items, strict=True):
                    self.assign(element, item, env, None)
                return
            for element in target.elts:
                inner = element.value if isinstance(element, ast.Starred) else element
                self.assign(inner, flat(value), env, None)
            return
        if isinstance(target, ast.Subscript):
            # ``out[i] = x`` keeps x in a list or a dictionary built here, and
            # copies x's values into an array.
            container = _root_name(target.value)
            if container is not None and container in self.container_names:
                env[container] = union(env.get(container, _CLEAN), flat(value))
            if isinstance(target.value, ast.Attribute):
                self.keep_attribute(target.value, value, None, into="item")
            return
        if isinstance(target, ast.Attribute):
            self.keep_attribute(target, value, None)
            return

    def keep_attribute(
        self,
        target: ast.Attribute,
        value: Value,
        annotation: str | None,
        *,
        into: str = "",
    ) -> None:
        """``self.name = value`` in a method of a plain public class.

        The attribute's own annotation, in the class body or on an assignment
        in any of its methods, says whether it may hold an array; an attribute
        with neither is read through the parameters the value carries, so
        that ``self._distances = distances`` is held to the annotation of
        ``distances`` and ``self.fs = fs`` to that of ``fs``.

        *into* is ``"item"`` for ``self.name[key] = value`` and the method's
        name for ``self.name.append(value)`` and its kin: the value is kept
        in a list or a mapping the object holds. An item written into an
        attribute that is not annotated as one is taken for an element of an
        array, which copies.
        """
        owner = self.function.owner
        if (
            not self.plain_method
            or owner is None
            or not isinstance(target.value, ast.Name)
            or target.value.id != "self"
            or not self.owner_public()
        ):
            return
        if annotation is None:
            annotation = self.tree.attribute_annotation(owner, target.attr)
        sink = f"self.{target.attr}"
        if into == "item":
            if annotation is None or not _collection_text(annotation):
                return
            sink += "[...]"
        elif into:
            sink += f".{into}(...)"
        if annotation is not None:
            if self.tree.holds_array(annotation):
                self.flag(target, sink, value)
            return
        if any(self.parameter_holds_array(label) for label in flat(value)):
            self.flag(target, sink, value)

    def parameter_holds_array(self, name: str) -> bool:
        """Whether a parameter of the function read may hold an array."""
        arguments = self.function.node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            if argument.arg == name:
                if argument.annotation is None:
                    return True
                return self.tree.holds_array(ast.unparse(argument.annotation))
        return True

    def built_records(self, node: ast.expr | None) -> list[ClassInfo]:
        """Each record class a call may build, if *node* is a call that
        builds a record whichever path runs (:meth:`records_built`); ``cls``
        in a method of a record is that record. No record for any other call.
        """
        if not isinstance(node, ast.Call):
            return []
        func = node.func
        owner = self.function.owner
        if isinstance(func, ast.Name) and func.id == "cls":
            return [owner] if owner is not None and owner.record else []
        pins: _Pins = {}
        return self.records_built(self.callees(func, pins=pins), pins)

    def built_record(self, node: ast.expr | None) -> ClassInfo | None:
        """The record class a call builds, if *node* is a call that builds
        that one record whichever path runs (:meth:`built_records`); none for
        one that may build either of two.
        """
        built = self.built_records(node)
        if not built or any(info is not built[0] for info in built):
            return None
        return built[0]

    def records_built(
        self, targets: Sequence[tuple[str, str]], pins: _Pins | None
    ) -> list[ClassInfo]:
        """Each record class a call that may name each of *targets* builds,
        when it builds a record whichever path runs.

        Every one of them is a class with no ``def`` of its name standing
        where the name was read (*pins*, :meth:`Tree.resolve_top`), and each
        ``class`` statement of it the call may build (:meth:`classes_built`)
        is a record: two records bound to a name in two branches, or a class
        written in each, are each built. A call that may run a function
        instead, one bound to the name in another branch or a ``def`` that
        took the name from the class, or build a class that is no record,
        builds none the guard can vouch for.
        """
        built: list[ClassInfo] = []
        for key in targets:
            if key not in self.tree.classes or _pinned_functions(pins, key):
                return []
            for info in self.classes_built(key, pins):
                if not info.record:
                    return []
                built.append(info)
        return built

    def builds_class(self, target: tuple[str, str], pins: _Pins | None) -> bool:
        """Whether a call that reaches *target* may make an instance of the
        class of that key: there is one, and what stood where the name was
        read (*pins*) holds no ``def`` of it, or holds the class beside them.
        """
        if target not in self.tree.classes:
            return False
        held = pins.get(target, []) if pins is not None else []
        return not _pinned_functions(pins, target) or any(
            isinstance(found, ClassInfo) for found in held
        )

    def copies_on_every_path(
        self, targets: Sequence[tuple[str, str]], pins: _Pins | None
    ) -> bool:
        """Whether a call that may name each of *targets* builds a record
        that copies whichever path runs: it builds a record on every path
        (:meth:`records_built`, *pins* what stood where each name was read),
        and each of them inherits :data:`MECHANISM`.

        A copy handed to such a call is made twice whichever path runs; one
        handed to a call that may also run a function, or build a class that
        does not copy, may be what keeps the caller's array out on that path.
        """
        built = self.records_built(targets, pins)
        return bool(built) and all(self.tree.copies_arrays(info) for info in built)

    def classes_built(
        self, target: tuple[str, str], pins: _Pins | None
    ) -> list[ClassInfo]:
        """The classes of *target* a call that may make an instance of one
        (:meth:`builds_class`) may build (:meth:`Tree.classes_stood`).
        """
        return self.tree.classes_stood(target, pins)

    def resolve_name(
        self, name: str, node: ast.AST | None = None, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package a bare name may stand for, here.

        Looked up as Python looks it up (:func:`ast_scan.own_names`): a lambda
        or a comprehension around *node* that binds the name hides every
        function; then this function and the definitions of those it is
        written in (a class body around it is skipped, as Python skips it):
        the nearest that binds the name says what it is (:meth:`_bound_to`),
        and one that declares it ``global`` sends it to the module, as one
        that binds it nowhere does; one that declares it ``nonlocal`` passes
        it on. At the module, what it defines or imports at its top. What a
        function of a module stood for where its name was read goes into
        *pins* (:meth:`Tree.resolve_top`).
        """
        if node is not None:
            how, binder = binding_of(self.function.node, node, name)
            if binder is not None and binder is not self.function.node:
                return ()
            if how == "global":
                return self.tree.resolve_top(self.module, name, node, pins=pins)
        scope: FunctionInfo | None = self.function
        while scope is not None:
            names = own_names(scope.node)
            if names.rebinds(name):
                return ()
            if name in names.declared_global:
                break
            if names.binds(name):
                return self._bound_to(scope, name, node, pins=pins)
            scope = scope.parent
        return self.tree.resolve_top(self.module, name, node, pins=pins)

    def _bound_to(
        self,
        scope: FunctionInfo,
        name: str,
        node: ast.AST | None,
        *,
        pins: _Pins | None = None,
    ) -> tuple[tuple[str, str], ...]:
        """What *name* may stand for in *scope*, which binds it itself.

        A function or a class it defines, and for a class each ``def`` and
        ``class`` of the name that may stand where *node* reads it
        (:func:`ast_scan.live_bindings`: in a function written in *scope*,
        any from that function's ``def`` on) pinned in *pins*
        (:meth:`Tree.stood_for`), as a ``def`` and a ``class`` of one name
        share a key; what each of its imports of the name that may have run before
        *node* reads (:meth:`Tree.imported`), and so for an assignment of a
        dotted name to it (:meth:`Tree.bound_in`). Nothing of the package for
        any other binding, a parameter or an assignment of anything else,
        nor for a name it both defines and binds otherwise, which may stand
        for either at a call.
        """
        how = own_names(scope.node).how(name)
        if how == "definition":
            own = (self.module, f"{scope.qualname}.{name}")
            if own not in self.tree.functions and own not in self.tree.classes:
                return ()
            # A function alone of its name is read where the call runs
            # (:meth:`reached`); a class needs the statement that stood.
            if pins is not None and own in self.tree.classes:
                made = bindings_by_name(scope.node).get(name, [])
                if node is not None:
                    made = live_bindings(scope.node, made, node)
                for statement in made:
                    _merge_pins(pins, {own: self.tree.stood_for(own, statement)})
            return (own,)
        if how == "binding":
            point = node if scope is self.function else None
            return self.tree.bound_in(self.module, scope.node, name, point, pins=pins)
        if how != "import":
            return ()
        imports = list(_imports_of(scope.node).get(name, ()))
        if scope is self.function and node is not None:
            imports = live_bindings(scope.node, imports, node)
        found = (
            key
            for binding in imports
            for key in self.tree.imported(self.module, binding, name, pins=pins)
        )
        return tuple(dict.fromkeys(found))

    def callees(
        self, func: ast.expr, *, pins: _Pins | None = None
    ) -> tuple[tuple[str, str], ...]:
        """Each function or class of the package a call may name."""
        if isinstance(func, ast.Name):
            return self.resolve_name(func.id, func, pins=pins)
        if isinstance(func, ast.Attribute):
            target = self.method_target(func)
            if target is not None:
                return (target,)
            module = self.module_of(func.value)
            if module is not None:
                return self.tree.resolve_all(module, func.attr, pins=pins)
        return ()

    def reached_by(self, func: ast.expr, call: ast.AST) -> list[FunctionInfo]:
        """Every definition a call can reach (:meth:`reached`), when each
        function it may name is a function of the package; none otherwise,
        nor when it may make an instance of a class of a function's name
        (:meth:`builds_class`).
        """
        pins: _Pins = {}
        targets = self.callees(func, pins=pins)
        if any(
            target not in self.tree.functions
            or (target in self.tree.classes and self.builds_class(target, pins))
            for target in targets
        ):
            return []
        return [
            found
            for target in targets
            for found in self.reached(target, call, pins=pins)
        ]

    def selects_positions(self, func: ast.expr) -> bool:
        """Whether every function of the package a call may name returns a
        mask or positions on every return of its own, and none of them is a
        class of a function's name the call may make an instance of
        (:meth:`builds_class`), which may index as one number.
        """
        pins: _Pins = {}
        targets = self.callees(func, pins=pins)
        return bool(targets) and all(
            key in self.tree.positions
            and not (key in self.tree.classes and self.builds_class(key, pins))
            for key in targets
        )

    # -- what kind of thing a name holds ----------------------------------
    def indexes(self, node: ast.expr) -> bool:
        """Whether *node* is a mask or an array of positions.

        Indexing with one copies what it selects, where a slice, a number or
        an ellipsis hands out a view.
        """
        if isinstance(node, ast.Compare | ast.List | ast.ListComp):
            return True
        if isinstance(node, ast.UnaryOp):
            return isinstance(node.op, ast.Invert | ast.Not)
        if isinstance(node, ast.BinOp):
            return isinstance(node.op, ast.BitAnd | ast.BitOr | ast.BitXor)
        if isinstance(node, ast.Name):
            return node.id in self.index_names
        if isinstance(node, ast.Tuple):
            return any(self.indexes(element) for element in node.elts)
        if isinstance(node, ast.Call):
            numpy_name = self.numpy_function(node.func)
            if numpy_name is not None:
                if numpy_name in {"where", "clip"}:
                    return bool(node.args) and (
                        len(node.args) == 1 or self.indexes(node.args[0])
                    )
                if numpy_name in _NUMPY_BUILDERS:
                    # ``np.asarray(indices, dtype=np.intp)`` of positions, or
                    # any array of integers or booleans, selects by position.
                    return _dtype_bool_or_int(node) or (
                        bool(node.args) and self.indexes(node.args[0])
                    )
                return numpy_name in _NUMPY_INDEX
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "argsort",
                "nonzero",
                "astype",
            }:
                return node.func.attr != "astype" or _names_bool_or_int(node)
            # A helper of the package selects by position only when every
            # return of its own is a mask or positions; one that hands out a
            # slice, or anything else, is read as a view.
            return self.selects_positions(node.func)
        return False

    def builds_container(self, node: ast.expr) -> bool:
        """Whether *node* builds a new list, tuple, set or dictionary."""
        if isinstance(
            node,
            ast.List
            | ast.Tuple
            | ast.Set
            | ast.Dict
            | ast.ListComp
            | ast.SetComp
            | ast.DictComp
            | ast.GeneratorExp,
        ):
            return True
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"list", "tuple", "dict", "set", "sorted", "zip"}
        )

    def is_collection(self, node: ast.expr) -> bool:
        """Whether *node* is a mapping, list or set rather than an array."""
        if self.is_container(node):
            return True
        if not isinstance(node, ast.Name):
            return False
        arguments = self.function.node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            if argument.arg == node.id and argument.annotation is not None:
                return _collection_annotation(argument.annotation)
        return False

    def is_container(self, node: ast.expr) -> bool:
        """Whether *node* is a list, tuple or the like built in this function."""
        if isinstance(node, ast.Name):
            return node.id in self.container_names
        return self.builds_container(node)

    # -- expressions -----------------------------------------------------
    def expr(self, node: ast.expr, env: dict[str, Value]) -> Value:
        if isinstance(node, ast.Name):
            return env.get(node.id, _CLEAN)
        if isinstance(node, ast.Attribute):
            if (
                self.post_init
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
            ):
                return env.get(f"self.{node.attr}", _CLEAN)
            inner = self.expr(node.value, env)
            if node.attr in _SCALAR_ATTRIBUTES:
                return _CLEAN
            if isinstance(inner, Fields):
                return inner.get(node.attr)
            return flat(inner)
        if isinstance(node, ast.Subscript):
            value = self.expr(node.value, env)
            self.expr(node.slice, env)
            if isinstance(value, Shaped) and isinstance(node.slice, ast.Constant):
                index = node.slice.value
                if isinstance(index, int) and -len(value.items) <= index < len(
                    value.items
                ):
                    return value.items[index]
            if self.indexes(node.slice):
                return _CLEAN
            if isinstance(value, Many):
                return value if isinstance(node.slice, ast.Slice) else value.item
            return flat(value)
        if isinstance(node, ast.Call):
            return self.call(node, env)
        if isinstance(node, ast.IfExp):
            self.expr(node.test, env)
            return union(self.expr(node.body, env), self.expr(node.orelse, env))
        if isinstance(node, ast.BoolOp):
            return union(*(self.expr(v, env) for v in node.values))
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            items = tuple(self.expr(e, env) for e in node.elts)
            if isinstance(node, ast.Tuple) and not any(
                isinstance(e, ast.Starred) for e in node.elts
            ):
                return Shaped(items)
            return union(_CLEAN, *items)
        if isinstance(node, ast.Starred):
            return flat(self.expr(node.value, env))
        if isinstance(node, ast.Dict):
            parts = [self.expr(v, env) for v in node.values]
            for key in node.keys:
                if key is not None:
                    self.expr(key, env)
            keys = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            ]
            if len(keys) == len(node.keys):
                # Keyword arguments in waiting: ``Record(**{"a": x})``.
                return Fields(tuple(zip(keys, parts, strict=True)))
            return union(_CLEAN, *parts)
        if isinstance(
            node, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
        ):
            scope = dict(env)
            for generator in node.generators:
                self.assign(
                    generator.target, self.element(generator.iter, scope), scope, None
                )
                for condition in generator.ifs:
                    self.expr(condition, scope)
            if isinstance(node, ast.DictComp):
                self.expr(node.key, scope)
                return flat(self.expr(node.value, scope))
            return flat(self.expr(node.elt, scope))
        if isinstance(node, ast.NamedExpr):
            value = self.expr(node.value, env)
            self.assign(node.target, value, env, node.value)
            return value
        if isinstance(node, ast.Await):
            return self.expr(node.value, env)
        # Arithmetic, comparisons, f-strings, lambdas, constants: a new value.
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr) and not isinstance(node, ast.Lambda):
                self.expr(child, env)
        return _CLEAN

    def call(self, node: ast.Call, env: dict[str, Value]) -> Value:
        func = node.func
        arguments = [self.expr(a, env) for a in node.args]
        keywords = {k.arg: self.expr(k.value, env) for k in node.keywords}
        first = arguments[0] if arguments else _CLEAN
        numpy_name = self.numpy_function(func)
        if numpy_name is not None:
            if numpy_name == "array":
                copy = _keyword_constant(node, "copy", default=True)
                return flat(first) if copy is not True else _CLEAN
            if numpy_name in _NUMPY_ALIASING_EACH and len(arguments) > 1:
                return Shaped(
                    tuple(
                        _CLEAN if self.is_container(a) else flat(v)
                        for a, v in zip(node.args, arguments, strict=True)
                    )
                )
            if numpy_name in _NUMPY_ALIASING:
                # A list or a tuple built here becomes a new array.
                if node.args and self.is_container(node.args[0]):
                    return _CLEAN
                return flat(first)
            return _CLEAN
        if isinstance(func, ast.Attribute):
            receiver = self.expr(func.value, env)
            name = func.attr
            if name == "replace" and _base_name(func.value) == "dataclasses":
                return self.replace_sink(node, arguments, keywords)
            if name == "__setattr__" and _base_name(func.value) == "object":
                self.setattr_sink(node, arguments, env)
                return _CLEAN
            if name in _CONTAINER_FILLERS:
                container = _root_name(func.value)
                if container is not None:
                    env[container] = union(
                        env.get(container, _CLEAN),
                        *map(flat, arguments),
                        *keywords.values(),
                    )
                if isinstance(func.value, ast.Attribute):
                    self.keep_attribute(
                        func.value,
                        union(_CLEAN, *map(flat, arguments), *keywords.values()),
                        None,
                        into=name,
                    )
                return _CLEAN
            if name == "astype":
                copy = _keyword_constant(node, "copy", default=True)
                return flat(receiver) if copy is not True else _CLEAN
            if name == "copy" and self.is_collection(func.value):
                # A dictionary's or a list's ``copy`` is shallow: the arrays
                # it holds are the same ones.
                return receiver
            if name in _METHOD_ALIASING:
                return flat(receiver)
            target = self.method_target(func)
            if target is not None:
                return self.apply(target, node, arguments, keywords, bound=True)
            module = self.module_of(func.value)
            if module is not None:
                pins: _Pins = {}
                resolved = self.tree.resolve_all(module, func.attr, pins=pins)
                if resolved:
                    return union(
                        *(
                            self.apply(
                                key,
                                node,
                                arguments,
                                keywords,
                                bound=False,
                                pins=pins,
                                alone=self.copies_on_every_path(resolved, pins),
                            )
                            for key in resolved
                        )
                    )
            if name in _WRAPPERS:
                return flat(first)
            return _CLEAN
        if isinstance(func, ast.Name):
            name = func.id
            if name == "getattr" and arguments:
                if (
                    self.post_init
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == "self"
                ):
                    names = (
                        _constant_strings(node.args[1], self.constants)
                        if len(node.args) > 1
                        else None
                    )
                    if names is not None:
                        return union(
                            _CLEAN, *(env.get(f"self.{n}", _CLEAN) for n in names)
                        )
                return union(first, *arguments[2:])
            if (
                name in {"list", "tuple", "sorted", "reversed"}
                and len(arguments) == 1
                and isinstance(first, Many)
            ):
                return first
            if name in _PASS_THROUGH_BUILTINS or name in {"enumerate", "zip"}:
                return union(_CLEAN, *map(flat, arguments))
            if name == "cls" and self.function.owner is not None:
                if not self.function.owner.record:
                    return _CLEAN
                return self.constructor_sink(
                    self.function.owner,
                    node,
                    arguments,
                    keywords,
                    public=self.owner_public(),
                )
            if name == "replace" and name not in self.tree.functions_named(self.module):
                return self.replace_sink(node, arguments, keywords)
            named: _Pins = {}
            targets = self.resolve_name(name, node.func, pins=named)
            if targets:
                if name == "read_only" or any(key[1] == "read_only" for key in targets):
                    self.flag(node, "read_only(...)", first)
                    return flat(first)
                return union(
                    *(
                        self.apply(
                            key,
                            node,
                            arguments,
                            keywords,
                            bound=False,
                            pins=named,
                            alone=self.copies_on_every_path(targets, named),
                        )
                        for key in targets
                    )
                )
            if name in _WRAPPERS:
                return flat(first)
            return _CLEAN
        if (
            isinstance(func, ast.Call)
            and isinstance(func.func, ast.Name)
            and func.func.id == "type"
            and self.function.owner is not None
        ):
            if not self.function.owner.record:
                return _CLEAN
            return self.constructor_sink(
                self.function.owner,
                node,
                arguments,
                keywords,
                public=self.owner_public(),
            )
        self.expr(func, env)
        return _CLEAN

    def owner_public(self) -> bool:
        """Whether the class this method belongs to reaches a caller."""
        owner = self.function.owner
        if owner is None:
            return False
        qualname = self.function.qualname.rpartition(".")[0]
        return (owner.module, qualname) in self.tree.public

    def numpy_function(self, func: ast.expr) -> str | None:
        """The numpy function a call names, or ``None``."""
        if isinstance(func, ast.Name):
            return self.tree.numpy_functions[self.module].get(func.id)
        if isinstance(func, ast.Attribute):
            root = func.value
            while isinstance(root, ast.Attribute):
                root = root.value
            if (
                isinstance(root, ast.Name)
                and root.id in self.tree.numpy_names[self.module]
            ):
                return func.attr
        return None

    def module_of(self, node: ast.expr) -> str | None:
        """The package module an expression names, if it names one."""
        if isinstance(node, ast.Name):
            return self.tree.resolve_module(self.module, node.id)
        return None

    def method_target(self, func: ast.Attribute) -> tuple[str, str] | None:
        """The method ``self.name`` or ``cls.name`` names, in the class read."""
        owner = self.function.owner
        if owner is None or not isinstance(func.value, ast.Name):
            return None
        if func.value.id not in {"self", "cls"} and func.value.id != owner.name:
            return None
        key = (owner.module, f"{self.function.qualname.rpartition('.')[0]}.{func.attr}")
        if key in self.tree.functions:
            return key
        return None

    def apply(
        self,
        target: tuple[str, str],
        node: ast.Call,
        arguments: list[Value],
        keywords: dict[str | None, Value],
        *,
        bound: bool,
        pins: _Pins | None = None,
        alone: bool = True,
    ) -> Value:
        """What a call to a function or a class of the package returns, each
        definition it reaches read (:meth:`reached`, *pins* what its name
        stood for where it was read; *alone* when every function or class
        the call may name is a record that copies, :meth:`copies_on_every_path`).

        A function and a class of one name share a key: the class is what
        the call reaches unless *pins* holds a ``def`` of the key, which an
        alias bound before the class keeps, and both are when *pins* holds
        the class beside it (:meth:`builds_class`), an alias bound to the
        ``def`` in one branch and to the class in another. The class is each
        ``class`` statement of the key the call may build
        (:meth:`classes_built`), the one an alias was bound to when a later
        one replaced it, and each read with its own fields. A copy handed to
        a record that copies is made twice only when every class the call
        may build or function it may run is a record that copies: on another
        path the copy may be what keeps the caller's array out.
        """
        values: list[Value] = []
        if target in self.tree.classes and self.builds_class(target, pins):
            built = self.classes_built(target, pins)
            pinned = _pinned_functions(pins, target)
            alone = (
                alone
                and not pinned
                and all(info.record and self.tree.copies_arrays(info) for info in built)
            )
            values.extend(
                self.constructor_sink(
                    info,
                    node,
                    arguments,
                    keywords,
                    public=target in self.tree.public,
                    alone=alone,
                )
                if info.record
                else _CLEAN
                for info in built
            )
            if not pinned:
                return values[0] if len(values) == 1 else union(_CLEAN, *values)
        spread = next(
            (
                index
                for index, argument in enumerate(node.args)
                if isinstance(argument, ast.Starred)
            ),
            None,
        )
        values.extend(
            self._returned_by(function, arguments, keywords, bound=bound, spread=spread)
            for function in self.reached(target, node, pins=pins)
        )
        return union(*values) if values else _CLEAN

    def _returned_by(
        self,
        function: FunctionInfo,
        arguments: list[Value],
        keywords: dict[str | None, Value],
        *,
        bound: bool,
        spread: int | None = None,
    ) -> Value:
        """What one definition returns of the arguments given to it, bound
        to its own parameters (:func:`bind`, *spread* the place of the first
        ``*`` argument).

        A function defined in this one, or in one around it (a sibling
        helper), is read as it was where it is defined, so what it returns of
        its closure (the caller's array a helper with no parameter hands
        back) is handed back too.
        """
        held = self.nested_returns.get(function.node)
        if held is None:
            held = self.enclosing.get(function.node)
        if held is not None:
            returned, closure = held
            mapping: dict[str, Value] = {label: frozenset({label}) for label in closure}
            mapping.update(
                bind(function, arguments, keywords, bound=bound, spread=spread)
            )
            return substitute(returned, mapping)
        summary = self.summaries.get(function.node)
        if summary is None or not flat(summary.value):
            return _CLEAN
        mapping = bind(function, arguments, keywords, bound=bound, spread=spread)
        return substitute(summary.value, mapping)

    def reached(
        self, target: tuple[str, str], call: ast.AST, *, pins: _Pins | None = None
    ) -> list[FunctionInfo]:
        """Every definition of *target* a call of it written here can reach.

        A function whose name was read where a ``def`` of it stands, at the
        top of its module or in a function that defines it, on the way to the
        call, by the call itself or by an alias the call reaches, is each
        definition that stood where it was read (*pins*,
        :meth:`Tree.resolve_top`), so an alias holds what its value named
        where it was bound. Otherwise one of a module, or of a class,
        is each definition the name may hold once the module has run
        (:func:`ast_scan.live_bindings`): one in each branch of an ``if`` is
        either, and a later one in a block that holds an earlier one
        replaces it; a function at the top of this module is read where the
        call runs instead, so a call inside a function meets every
        definition from the ``def`` on. One written inside a function is each
        written in the nearest of this function and those around it that
        holds any; in this function itself, each that may have run before
        the call and that no later one replaced on the way to it.
        """
        definitions = self.tree.definitions.get(target)
        if not definitions:
            found = self.tree.functions.get(target)
            return [found] if found is not None else []
        if pins is not None and target in pins:
            return _pinned_functions(pins, target)
        if all(definition.parent is None for definition in definitions):
            if target[0] == self.module and all(d.owner is None for d in definitions):
                return _live(self.tree.modules[self.module], definitions, call)
            return self.tree.live_definitions(target)
        scope: FunctionInfo | None = self.function
        while scope is not None:
            here = [d for d in definitions if d.parent is scope]
            if here:
                if scope is self.function:
                    return _live(self.function.node, here, call)
                return here
            scope = scope.parent
        return definitions

    # -- the places an array is kept --------------------------------------
    def constructor_sink(
        self,
        info: ClassInfo,
        node: ast.Call,
        arguments: list[Value],
        keywords: dict[str | None, Value],
        *,
        public: bool,
        alone: bool = True,
    ) -> Value:
        """Report what a record keeps, and return the record as a value.

        A copy handed to a record that copies is reported only when every
        class the call may build is a record that copies, and no function it
        may run hands its argument back instead (*alone*, :meth:`apply`).
        """
        fields = self.tree.record_fields(info)
        annotations = dict(fields)
        if self.tree.copies_arrays(info):
            # Every array it is built with, however it is passed, is replaced
            # by a copy of its own: the record carries nothing of the caller.
            if public and alone and self.findings is not None:
                self.copied_twice(info, node, fields)
            return Fields(tuple((name, _CLEAN) for name, _ in fields))
        kept: dict[str, Value] = {}
        spilled: list[Value] = []
        for index, value in enumerate(arguments):
            if isinstance(node.args[index], ast.Starred) or index >= len(fields):
                spilled.append(value)
                continue
            kept[fields[index][0]] = value
        for name, value in keywords.items():
            if name is None and isinstance(value, Fields):
                for key, item in value.items:
                    if key in annotations:
                        kept[key] = item
                    else:
                        spilled.append(item)
            elif name is None or name not in annotations:
                spilled.append(value)
            else:
                kept[name] = value
        # A field the record copies itself, or one that cannot hold an array,
        # carries nothing a later read could keep.
        kept = {
            name: _CLEAN
            if self.tree.owns(info, name)
            or not self.tree.holds_array(annotations[name])
            else value
            for name, value in kept.items()
        }
        if public:
            for name, value in kept.items():
                if self.tree.holds_array(annotations[name]):
                    self.flag(node, f"{info.name}.{name}", value)
            if any(
                self.tree.holds_array(annotation) for annotation in annotations.values()
            ):
                for value in spilled:
                    self.flag(node, f"{info.name}(*...)", value)
        if spilled:
            extra = union(_CLEAN, *map(flat, spilled))
            kept = {name: union(value, extra) for name, value in kept.items()}
        return Fields(tuple(kept.items()))

    def is_copy(self, node: ast.expr, annotation: str) -> bool:
        """Whether an argument is a copy made of an array.

        ``read_only_copy(x)``, ``np.copy(x)``, ``x.astype(t)`` (whose default
        ``copy=True`` copies even when ``x`` already has the type; written
        ``np.asarray(x, dtype=t)`` it converts only when it has to) and
        ``read_only`` around any of them or around ``np.array`` are copies
        whatever ``x`` is; ``x.copy()`` is one when the field is annotated as
        an array alone, since a mapping's or a list's ``copy`` copies the
        container. ``np.array(x)`` is not read as one: it is how a list
        becomes an array.
        """
        if isinstance(node, ast.IfExp):
            return self.is_copy(node.body, annotation) or self.is_copy(
                node.orelse, annotation
            )
        if not isinstance(node, ast.Call):
            return False
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if (
            name == "read_only_copy"
            or self.numpy_function(node.func) == "copy"
            or _method_astype(node)
        ):
            return True
        if name == "read_only" and node.args:
            inner = node.args[0]
            return isinstance(inner, ast.Call) and (
                _method_copy(inner)
                or _method_astype(inner)
                or self.numpy_function(inner.func) in {"array", "copy"}
            )
        return _method_copy(node) and self.array_only(annotation)

    def array_only(self, annotation: str) -> bool:
        """Whether a field so annotated holds an array and no container."""
        words = _words(annotation)
        if any(word in _CONTAINER_WORDS for word in words):
            return False
        return any(
            word in {"ndarray", "NDArray", "ArrayLike", "NumericArrayLike"}
            or word in self.tree.array_aliases
            for word in words
        )

    def copied_twice(
        self, info: ClassInfo, node: ast.Call, fields: Sequence[tuple[str, str]]
    ) -> None:
        """Report a copy made of an array handed to a record that copies it.

        The record makes a read-only copy of every array it is built with, so
        a ``read_only_copy`` (or a ``.copy()``) written around the argument
        copies the same array twice. So does a copy bound to a name first and
        handed over by that name, bare or through ``read_only``, when the
        copy does nothing else: see :meth:`copy_only_handed_over`.
        """
        annotations = dict(fields)
        given: list[tuple[str, ast.expr]] = [
            (fields[index][0], argument)
            for index, argument in enumerate(node.args)
            if index < len(fields) and not isinstance(argument, ast.Starred)
        ]
        given += [(k.arg, k.value) for k in node.keywords if k.arg in annotations]
        for name, argument in given:
            if self.is_copy(argument, annotations[name]):
                self.mark(argument, f"{info.name}.{name} (copied twice)")
                continue
            local = _handed_name(argument)
            if local is not None and self.copy_only_handed_over(
                local, annotations[name]
            ):
                self.mark(argument, f"{info.name}.{name} (copied twice, as {local})")

    # -- a copy bound to a name and handed over ----------------------------
    def copy_only_handed_over(self, name: str, annotation: str) -> bool:
        """Whether a local name holds a copy that only reaches a record.

        Every binding of the name in the function is a copy (as
        :meth:`is_copy` reads one, for a field so annotated), the name is not
        a parameter, and every use of it is harmless (:meth:`harmless`):
        nothing writes into the copy, keeps it or a view of it, or hands it
        anywhere but to records that copy it again. Read this way, the copy
        is never what makes the code right, and dropping it changes nothing
        but the memory. Anything the reading cannot vouch for counts as a use
        that needs the copy, so the rule never asks for a copy that matters
        to be dropped.
        """
        function = self.function.node
        if name in _parameter_names(function):
            return False
        parents, uses = self.syntax()
        if not all(
            isinstance(parents.get(use), ast.Assign | ast.AnnAssign)
            for use in uses.get(name, ())
            if isinstance(use.ctx, ast.Store)
        ):
            return False
        bindings = _bindings(function, name)
        if not bindings or any(
            value is None or not self.is_copy(value, annotation) for value in bindings
        ):
            return False
        return self.uses_harmless(name, depth=0)

    def uses_harmless(self, name: str, depth: int) -> bool:
        """Whether every read of *name* in the function is harmless.

        A binding of the name is read as the caller's business: a parameter
        rebound in the function, or deleted, is not vouched for.
        """
        parents, uses = self.syntax()
        for node in uses.get(name, ()):
            if isinstance(node.ctx, ast.Store | ast.Del):
                if depth > 0:
                    return False
                continue
            if not self.harmless(node, parents, depth):
                return False
        return True

    def syntax(self) -> tuple[dict[ast.AST, ast.AST], dict[str, list[ast.Name]]]:
        """Each node of the function with the node that holds it, and each
        name with the places it is written, read once per function: the
        places that name the function's own variable, not a variable a
        nested function, a lambda or a comprehension keeps for itself.
        """
        node = self.function.node
        if node not in self.tree.syntax:
            parents: dict[ast.AST, ast.AST] = {}
            uses: dict[str, list[ast.Name]] = {}
            for parent in ast.walk(node):
                for child in ast.iter_child_nodes(parent):
                    parents[child] = parent
                if isinstance(parent, ast.Name) and _of_the_function(node, parent):
                    uses.setdefault(parent.id, []).append(parent)
            self.tree.syntax[node] = (parents, uses)
        return self.tree.syntax[node]

    def harmless(
        self, node: ast.expr, parents: Mapping[ast.AST, ast.AST], depth: int
    ) -> bool:
        """Whether what *node* holds (the array, or a view of it) is only read.

        Read: an operand of arithmetic or of a comparison, a truth test, a
        number in an f-string, its size or shape, a method or a numpy
        function whose result is a new array, an index into something else,
        a builtin that reads it, a record that copies it whichever path of
        the call runs (:meth:`built_records`), and a function of the package
        whose parameter is used the same way. A view of it
        (indexing, ``.T``, ``read_only``, ``np.asarray``) is followed to its
        own use. Anything else is not.
        """
        parent = parents.get(node)
        if isinstance(parent, ast.BinOp | ast.UnaryOp | ast.Compare):
            return True
        if isinstance(parent, ast.BoolOp):
            # ``a or levels`` is ``levels`` itself when ``a`` is false.
            return self.harmless(parent, parents, depth)
        if isinstance(parent, ast.FormattedValue):
            return True
        if isinstance(parent, ast.If | ast.While | ast.Assert) and parent.test is node:
            return True
        if isinstance(parent, ast.IfExp):
            return parent.test is node or self.harmless(parent, parents, depth)
        if isinstance(parent, ast.Subscript):
            if parent.value is not node:
                # An index into another array: indexing by an array copies.
                return parent.slice is node
            return isinstance(parent.ctx, ast.Load) and self.harmless(
                parent, parents, depth
            )
        if isinstance(parent, ast.Attribute):
            if not isinstance(parent.ctx, ast.Load):
                return False
            if parent.attr in _SCALAR_ATTRIBUTES - {"flags", "strides"}:
                return True
            if parent.attr in _VIEW_ATTRIBUTES:
                return self.harmless(parent, parents, depth)
            call = parents.get(parent)
            if not isinstance(call, ast.Call) or call.func is not parent:
                return False
            if any(k.arg == "out" for k in call.keywords):
                return False
            if parent.attr in _METHOD_FRESH:
                return _keyword_constant(call, "copy", default=True) is True
            if parent.attr in _METHOD_ALIASING:
                return self.harmless(call, parents, depth)
            return False
        if isinstance(parent, ast.keyword):
            call = parents.get(parent)
            if (
                parent.arg is None
                or parent.arg == "out"
                or not isinstance(call, ast.Call)
            ):
                return False
            return self.harmless_argument(call, node, parent.arg, parents, depth)
        if (
            isinstance(parent, ast.Call)
            and parent.func is not node
            and any(argument is node for argument in parent.args)
        ):
            return self.harmless_argument(parent, node, None, parents, depth)
        if isinstance(parent, ast.List | ast.Tuple) and isinstance(
            parent.ctx, ast.Load
        ):
            # ``np.concatenate([levels, extra])``: the items go into a new
            # array when the list goes straight to a numpy function that
            # builds one.
            call = parents.get(parent)
            return (
                isinstance(call, ast.Call)
                and any(argument is parent for argument in call.args)
                and self.numpy_function(call.func)
                not in {
                    None,
                    "array",
                    *_NUMPY_ALIASING,
                    *_NUMPY_ALIASING_EACH,
                    *_NUMPY_WRITERS,
                }
            )
        return False

    def harmless_argument(
        self,
        call: ast.Call,
        node: ast.expr,
        keyword: str | None,
        parents: Mapping[ast.AST, ast.AST],
        depth: int,
    ) -> bool:
        """Whether a call only reads the array *node* holds."""
        func = call.func
        if isinstance(func, ast.Name) and func.id in {"read_only", "cast"}:
            return self.harmless(call, parents, depth)
        if isinstance(func, ast.Name) and func.id in _READING_BUILTINS:
            return True
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "math"
        ):
            return True
        numpy_name = self.numpy_function(func)
        if numpy_name is not None:
            first = keyword is None and bool(call.args) and call.args[0] is node
            if numpy_name in _NUMPY_WRITERS and first:
                return False
            if numpy_name in _NUMPY_ALIASING | _NUMPY_ALIASING_EACH or (
                numpy_name == "array"
                and _keyword_constant(call, "copy", default=True) is not True
            ):
                return self.harmless(call, parents, depth)
            return True
        built = self.built_records(call)
        if built:
            return all(self.tree.copies_arrays(info) for info in built)
        if depth >= 3:
            return False
        # Every definition the call can reach only reads what it is given.
        reached = self.reached_by(func, call)
        return bool(reached) and all(
            self._reads_only(function, call, node, keyword, depth)
            for function in reached
        )

    def _reads_only(
        self,
        function: FunctionInfo,
        call: ast.Call,
        node: ast.expr,
        keyword: str | None,
        depth: int,
    ) -> bool:
        """Whether one definition a call reaches only reads the argument *node*."""
        parameter = _bound_parameter(function, call, node, keyword)
        if parameter is None:
            return False
        reader = Reader(self.tree, function, self.summaries, None)
        return reader.uses_harmless(parameter, depth + 1)

    # -- an array handed over without a copy --------------------------------
    def handover_refused(self, call: ast.Call) -> str | None:
        """Why the reading cannot vouch for an array handed over, or ``None``.

        ``handed_over(name)`` lets the record keep the array without a copy,
        which is right only when nothing else can reach it, now or later.
        That is proved here from the syntax alone: the call is an argument of
        a record that inherits :data:`MECHANISM` whichever path of the call
        runs (:meth:`built_records`), built in the ``return`` statement, so nothing of the function runs after the record holds the
        array; the name is bound once, in the function's own scope, to an
        array a numpy allocation makes (:data:`_NUMPY_FRESH`, or ``None`` in
        one branch of a conditional); and every other read of it only writes
        into the array (:meth:`writes_into`). No view, no second name and no
        container ever holds it, so when the function returns, the record's
        is the only reference left.
        """
        parents, uses = self.syntax()
        holder = parents.get(call)
        record = parents.get(holder) if isinstance(holder, ast.keyword) else holder
        if not isinstance(record, ast.Call) or not (
            (isinstance(holder, ast.keyword) and holder.arg is not None)
            or any(argument is call for argument in record.args)
        ):
            return "it is not an argument of a record"
        built = self.built_records(record)
        if not built or not all(self.tree.copies_arrays(info) for info in built):
            return f"it is not an argument of a record that inherits {MECHANISM}"
        if not isinstance(parents.get(record), ast.Return):
            return "the record is not built in the return statement"
        if (
            len(call.args) != 1
            or call.keywords
            or not isinstance(call.args[0], ast.Name)
        ):
            return "its argument is not a name"
        name = call.args[0].id
        function = self.function.node
        if name in _parameter_names(function):
            return f"{name} is a parameter"
        if _frame_escapes(function):
            return "the function can reach its own frame (a generator, locals())"
        bindings = _bindings(function, name)
        stores = [
            use for use in uses.get(name, ()) if not isinstance(use.ctx, ast.Load)
        ]
        store = stores[0] if len(stores) == 1 else None
        if (
            len(bindings) != 1
            or bindings[0] is None
            or not self.allocates(bindings[0])
            or store is None
            or not _single_target(parents.get(store), store)
            or not _own_scope(store, parents, function)
        ):
            return (
                f"{name} is not bound once, in the function and to it alone, to a "
                f"new array (np.{', np.'.join(sorted(_NUMPY_FRESH))})"
            )
        for use in uses.get(name, ()):
            if use is call.args[0] or use is store:
                continue
            if not self.writes_into(use, parents, depth=0):
                return f"{name} is read where it may be kept (line {use.lineno})"
        return None

    def allocates(self, node: ast.expr) -> bool:
        """Whether *node* is a new array a numpy allocation makes, or one of
        two such branches with ``None`` in the other.
        """
        if isinstance(node, ast.IfExp):
            branches = (node.body, node.orelse)
            return any(not _is_none(b) for b in branches) and all(
                _is_none(b) or self.allocates(b) for b in branches
            )
        return (
            isinstance(node, ast.Call)
            and self.numpy_function(node.func) in _NUMPY_FRESH
            and not any(k.arg in {None, "like"} for k in node.keywords)
        )

    def writes_into(
        self, node: ast.Name, parents: Mapping[ast.AST, ast.AST], depth: int
    ) -> bool:
        """Whether a read of a handed-over name only writes into the array.

        The array is written into (``name[...] = value``, or ``+=``), tested
        against ``None``, or passed to a function of the package whose
        parameter is used the same way, read in its own body down to three
        calls deep. Nothing else: not a view, not a container, not a closure
        of a nested function or a lambda, and not a function behind a
        decorator, whose wrapper is code the body does not show and may keep
        what it is passed.
        """
        if not _own_scope(node, parents, self.function.node):
            return False
        parent = parents.get(node)
        if isinstance(parent, ast.Subscript):
            return parent.value is node and isinstance(parent.ctx, ast.Store)
        if isinstance(parent, ast.Compare):
            operands = (parent.left, *parent.comparators)
            return all(isinstance(op, ast.Is | ast.IsNot) for op in parent.ops) and all(
                operand is node or _is_none(operand) for operand in operands
            )
        if isinstance(parent, ast.keyword):
            call, keyword = parents.get(parent), parent.arg
            if keyword is None:
                return False
        else:
            call, keyword = parent, None
            if not isinstance(call, ast.Call) or all(a is not node for a in call.args):
                return False
        if not isinstance(call, ast.Call) or depth >= 3:
            return False
        # Every definition the call can reach only writes into what it is given.
        reached = self.reached_by(call.func, call)
        return bool(reached) and all(
            self._writes_only(function, call, node, keyword, depth)
            for function in reached
        )

    def _writes_only(
        self,
        function: FunctionInfo,
        call: ast.Call,
        node: ast.expr,
        keyword: str | None,
        depth: int,
    ) -> bool:
        """Whether one definition a call reaches only writes into the argument *node*."""
        parameter = _bound_parameter(function, call, node, keyword)
        if (
            parameter is None
            or function.node.decorator_list
            or _frame_escapes(function.node)
        ):
            return False
        reader = Reader(self.tree, function, self.summaries, None)
        return reader.only_written(parameter, depth + 1)

    def only_written(self, name: str, depth: int) -> bool:
        """Whether a parameter is never bound again and only written into."""
        parents, uses = self.syntax()
        return all(
            isinstance(use.ctx, ast.Load) and self.writes_into(use, parents, depth)
            for use in uses.get(name, ())
        )

    def replace_sink(
        self, node: ast.Call, arguments: list[Value], keywords: dict[str | None, Value]
    ) -> Value:
        """``dataclasses.replace``: the new record keeps every field not named.

        A record that copies its arrays copies the kept ones again when the
        new record is built, so nothing is kept there.
        """
        if not node.args:
            return _CLEAN
        original = arguments[0]
        info = self.annotated_record(node.args[0])
        if info is not None and not self.tree.copies_arrays(info):
            annotations = dict(self.tree.record_fields(info))
            for name, annotation in annotations.items():
                if name in keywords or not self.tree.holds_array(annotation):
                    continue
                carried = (
                    original.get(name) if isinstance(original, Fields) else original
                )
                if self.tree_public(info):
                    self.flag(node, f"{info.name}.{name} (kept by replace)", carried)
        if isinstance(original, Fields):
            items = dict(original.items)
            items.update({k: v for k, v in keywords.items() if k is not None})
            return Fields(tuple(items.items()))
        return union(original, *keywords.values())

    def annotated_record(self, node: ast.expr) -> ClassInfo | None:
        """The record class a parameter is annotated with, if it names one."""
        if not isinstance(node, ast.Name):
            return None
        arguments = self.function.node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            if argument.arg != node.id or argument.annotation is None:
                continue
            for word in _words(ast.unparse(argument.annotation)):
                for info in self.tree.class_by_name.get(word, []):
                    if info.record:
                        return info
        return None

    def tree_public(self, info: ClassInfo) -> bool:
        """Whether a record class, any ``class`` statement of its key,
        reaches a caller.
        """
        return any(
            found is info
            for key in self.tree.public
            for found in self.tree.class_definitions[key]
        )

    def setattr_sink(
        self, node: ast.Call, arguments: list[Value], env: dict[str, Value]
    ) -> None:
        owner = self.function.owner
        if len(node.args) < 3:
            return
        names = _constant_strings(node.args[1], self.constants) or ()
        target = node.args[0]
        if owner is None or not (isinstance(target, ast.Name) and target.id == "self"):
            self.foreign_setattr(node, target, names, arguments[2])
            return
        if self.post_init:
            stored = node.args[2]
            sealed = isinstance(stored, ast.Call) and _base_name(stored.func) in {
                "read_only",
                "read_only_copy",
            }
            for name in names:
                owner.owned[name] = owner.owned.get(name, True) and not flat(
                    arguments[2]
                )
                owner.sealed[name] = owner.sealed.get(name, True) and sealed
        if not self.owner_public():
            for name in names:
                if self.post_init:
                    env[f"self.{name}"] = arguments[2]
            return
        for name in names:
            annotation = self.tree.attribute_annotation(owner, name)
            if self.tree.holds_array(annotation):
                self.flag(node, f"{owner.name}.{name}", arguments[2])
            if self.post_init:
                # The field holds what was stored, for the reads that follow.
                env[f"self.{name}"] = arguments[2]

    def foreign_setattr(
        self,
        node: ast.Call,
        target: ast.expr,
        names: tuple[str, ...],
        value: Value,
    ) -> None:
        """``object.__setattr__(record, name, value)`` outside the record's methods.

        A factory that patches a field of the record it just built keeps the
        value as surely as the constructor would. The record is known when it
        was built here or came in annotated; one that is neither is held to
        the rule whatever it is, since a field set this way is seldom a
        number.
        """
        info = (
            self.record_names.get(target.id) if isinstance(target, ast.Name) else None
        )
        if info is None:
            info = self.annotated_record(target)
        if info is not None and not self.tree_public(info):
            return
        label = info.name if info is not None else ast.unparse(target)
        for name in names or ("?",):
            annotation = (
                self.tree.attribute_annotation(info, name) if info is not None else None
            )
            if self.tree.holds_array(annotation):
                self.flag(node, f"{label}.{name}", value)

    def mark(self, node: ast.AST, sink: str) -> None:
        """Record a finding that is not about a parameter carried."""
        if self.findings is None:
            return
        self.findings.append(
            Finding(
                self.function.path,
                self.function.qualname,
                getattr(node, "lineno", 0),
                sink,
                (),
            )
        )

    def flag(self, node: ast.AST, sink: str, value: Value) -> None:
        carried = flat(value)
        if not carried or self.findings is None:
            return
        self.findings.append(
            Finding(
                self.function.path,
                self.function.qualname,
                getattr(node, "lineno", 0),
                sink,
                tuple(sorted(carried)),
            )
        )


def merge(*envs: dict[str, Value]) -> dict[str, Value]:
    """The names after any of several branches, each carrying all it may."""
    out: dict[str, Value] = {}
    for env in envs:
        for name, value in env.items():
            out[name] = union(out[name], value) if name in out else value
    return out


_SEQUENCES = frozenset(
    {
        "Sequence",
        "list",
        "tuple",
        "Iterable",
        "Collection",
        "Iterator",
        "set",
        "frozenset",
    }
)


def _record_annotation(node: ast.expr) -> tuple[str, bool] | None:
    """The class an annotation names, and whether it is a sequence of it.

    ``Record``, ``Record | None``, ``Sequence[Record]`` and
    ``tuple[Record, ...]`` are read; anything else is not.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            node = ast.parse(node.value, mode="eval").body
        except SyntaxError:
            return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        sides = {
            _record_annotation(n) for n in (node.left, node.right) if not _is_none(n)
        }
        return sides.pop() if len(sides) == 1 else None
    if isinstance(node, ast.Name | ast.Attribute):
        return _base_name(node), False
    if isinstance(node, ast.Subscript) and _base_name(node.value) in _SEQUENCES:
        inner = node.slice
        if isinstance(inner, ast.Tuple):
            if len(inner.elts) != 2 or not (
                isinstance(inner.elts[1], ast.Constant)
                and inner.elts[1].value is Ellipsis
            ):
                return None
            inner = inner.elts[0]
        found = _record_annotation(inner)
        if found is None or found[1]:
            return None
        return found[0], True
    return None


#: Annotations of a mapping, a sequence or a set, whose ``copy`` is shallow.
_COLLECTIONS = frozenset(
    {
        "dict",
        "Dict",
        "Mapping",
        "MutableMapping",
        "defaultdict",
        "OrderedDict",
        "ChainMap",
        "Counter",
        "list",
        "List",
        "Sequence",
        "MutableSequence",
        "set",
        "Set",
        "MutableSet",
        "deque",
    }
)


def _collection_annotation(node: ast.expr) -> bool:
    """Whether an annotation names a mapping, a list or a set (or ``None`` of one)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            node = ast.parse(node.value, mode="eval").body
        except SyntaxError:
            return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        sides = [n for n in (node.left, node.right) if not _is_none(n)]
        return bool(sides) and all(_collection_annotation(n) for n in sides)
    return _base_name(node) in _COLLECTIONS


def _collection_text(annotation: str) -> bool:
    """:func:`_collection_annotation` on an annotation's text."""
    try:
        node = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return False
    return _collection_annotation(node)


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _words(text: str) -> list[str]:
    """The identifiers in an annotation's text."""
    out: list[str] = []
    word = ""
    for character in text:
        if character.isalnum() or character == "_":
            word += character
            continue
        if word:
            out.append(word)
        word = ""
    if word:
        out.append(word)
    return out


def _dtype_bool_or_int(node: ast.Call) -> bool:
    """Whether an array-building call asks for booleans or integers."""
    dtype = next((k.value for k in node.keywords if k.arg == "dtype"), None)
    if dtype is None and len(node.args) > 1:
        dtype = node.args[1]
    if dtype is None:
        return False
    text = ast.unparse(dtype)
    return "bool" in text or "int" in text


def _names_bool_or_int(node: ast.Call) -> bool:
    """Whether an ``astype`` call converts to booleans or integers."""
    for argument in node.args[:1]:
        text = ast.unparse(argument)
        return "bool" in text or "int" in text
    return False


def _root_name(node: ast.expr) -> str | None:
    while isinstance(node, ast.Subscript | ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _handed_name(node: ast.expr) -> str | None:
    """The local name an argument hands over, bare or through ``read_only``."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "read_only"
        and len(node.args) == 1
        and not node.keywords
    ):
        node = node.args[0]
    return node.id if isinstance(node, ast.Name) else None


def _parameter_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    arguments = function.args
    names = {
        a.arg for a in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
    }
    names.update(a.arg for a in (arguments.vararg, arguments.kwarg) if a is not None)
    return names


def _of_the_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef, name: ast.Name
) -> bool:
    """Whether *name* reads or binds the function's own variable of its
    spelling, or one no scope inside the function binds: not a variable a
    nested function, a lambda or a comprehension keeps for itself, which
    Python keeps apart (:func:`ast_scan.binding_of`).
    """
    scope = binding_of(function, name, name.id)[1]
    return scope is None or scope is function


def _names_in(target: ast.AST, name: str) -> bool:
    """Whether *name* is among the names a target or an expression holds."""
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(target))


def _own_scope(
    node: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Whether *node* is in the function's own scope, not in a nested
    function, a lambda, a class body or a comprehension.
    """
    current = parents.get(node)
    while current is not None and current is not function:
        if isinstance(
            current,
            ast.FunctionDef
            | ast.AsyncFunctionDef
            | ast.Lambda
            | ast.ClassDef
            | ast.ListComp
            | ast.SetComp
            | ast.DictComp
            | ast.GeneratorExp,
        ):
            return False
        current = parents.get(current)
    return current is function


def _single_target(statement: ast.AST | None, target: ast.Name | None) -> bool:
    """Whether *statement* binds *target* alone (``a = b = ...`` binds two)."""
    if isinstance(statement, ast.Assign):
        return len(statement.targets) == 1 and statement.targets[0] is target
    return isinstance(statement, ast.AnnAssign) and statement.target is target


#: Builtins through which a function hands out its own local names.
_FRAME_BUILTINS = frozenset({"locals", "vars", "eval", "exec"})


def _frame_escapes(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a function's locals may be reached from outside it: a
    coroutine or a generator, whose frame outlives the call, or a body that
    calls ``locals()``, ``vars()``, ``eval`` or ``exec``.
    """
    if isinstance(function, ast.AsyncFunctionDef):
        return True
    for node in ast.walk(function):
        if isinstance(node, ast.Yield | ast.YieldFrom | ast.Await):
            return True
        if isinstance(node, ast.Name) and node.id in _FRAME_BUILTINS:
            return True
    return False


def _bindings(
    function: ast.FunctionDef | ast.AsyncFunctionDef, name: str
) -> list[ast.expr | None]:
    """What each binding of *name* in the function binds it to.

    A plain assignment binds it to its value; any other binding (an
    augmented assignment, unpacking, a loop or ``with`` target, ``:=``, an
    import, a nested definition, ``global``) to ``None``, a value the reading
    does not know. A binding of a variable a nested function, a lambda or a
    comprehension keeps for itself binds another name, and is left out; one
    a nested function declares ``nonlocal`` is the function's.
    """
    found: list[tuple[ast.AST, ast.expr | None]] = []
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    found.append((node, node.value))
                elif isinstance(target, ast.Tuple | ast.List | ast.Starred) and (
                    _names_in(target, name)
                ):
                    found.append((node, None))
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            found.append((node, node.value))
        elif _binds_unknown(node, name, function):
            found.append((node, None))
    return [
        value
        for node, value in found
        # A ``global`` the function itself declares makes the name the
        # module's, a value the reading does not know.
        if binding_of(function, node, name)[1] is function
        or (
            isinstance(node, ast.Global)
            and scopes_around(function, node)[0] is function
        )
    ]


def _binds_unknown(
    node: ast.AST, name: str, function: ast.FunctionDef | ast.AsyncFunctionDef
) -> bool:
    """Whether *node* binds *name* to something other than a plain value."""
    if isinstance(node, ast.AugAssign | ast.NamedExpr):
        return isinstance(node.target, ast.Name) and node.target.id == name
    if isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
        return _names_in(node.target, name)
    if isinstance(node, ast.withitem):
        return node.optional_vars is not None and _names_in(node.optional_vars, name)
    if isinstance(node, ast.ExceptHandler):
        return node.name == name
    if isinstance(node, ast.Import | ast.ImportFrom):
        return any((a.asname or a.name).split(".")[0] == name for a in node.names)
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node is not function and node.name == name
    if isinstance(node, ast.Global | ast.Nonlocal):
        return name in node.names
    return False


#: The statements at the top of a module that bind a name a call may reach.
_TOP_BINDINGS = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Import,
    ast.ImportFrom,
)


#: How many names, imports and assignments deep a name is followed to what
#: it stands for, past which it stands for nothing the guard can name.
_DEPTH = 8


def _aliases_a_name(
    node: ast.AST, root: ast.AST
) -> TypeGuard[ast.Name | ast.NamedExpr]:
    """Whether *node*, under *root*, is a name an assignment binds to a dotted
    name alone (``alias = handing_back``, ``check = validation.check``), or
    an assignment expression that does (``(fn := handing_back)``).
    """
    if assignment_target(node) is None:
        return False
    value = assigned_value(root, node)
    while isinstance(value, ast.Attribute):
        value = value.value
    return isinstance(value, ast.Name)


def _live(
    root: ast.AST, definitions: list[FunctionInfo], call: ast.AST | None
) -> list[FunctionInfo]:
    """Of *definitions* of one name in one scope under *root*, those the name
    may hold at *call*, or once the scope has run when *call* is None
    (:func:`ast_scan.live_bindings`).
    """
    nodes = {definition.node: definition for definition in definitions}
    return [nodes[node] for node in live_bindings(root, list(nodes), call)]


@functools.cache
def _imports_of(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, tuple[ast.Import | ast.ImportFrom, ...]]:
    """Each name an import of the function's own scope binds, with every
    import that binds it in the order of the source; read once for each
    function, as every pass of the fixed point asks again.
    """
    found: dict[str, list[ast.Import | ast.ImportFrom]] = {}
    own = [
        node
        for node in scope_nodes(function)
        if isinstance(node, ast.Import | ast.ImportFrom)
    ]
    for node in sorted(own, key=lambda node: (node.lineno, node.col_offset)):
        for name in imported_names(node):
            found.setdefault(name, []).append(node)
    return {name: tuple(nodes) for name, nodes in found.items()}


def _bound_parameter(
    function: FunctionInfo, call: ast.Call, node: ast.expr, keyword: str | None
) -> str | None:
    """The parameter of *function* a call binds *node* to, if it can tell."""
    arguments = function.node.args
    positional = [a.arg for a in (*arguments.posonlyargs, *arguments.args)]
    bound = function.kind == "classmethod" or (
        function.kind == "method"
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "self"
    )
    if bound:
        positional = positional[1:]
    if keyword is not None:
        named = {a.arg for a in (*arguments.args, *arguments.kwonlyargs)}
        return keyword if keyword in named else None
    for index, argument in enumerate(call.args):
        if isinstance(argument, ast.Starred):
            return None
        if argument is node:
            return positional[index] if index < len(positional) else None
    return None


def _keyword_constant(node: ast.Call, name: str, *, default: object) -> object:
    for keyword in node.keywords:
        if keyword.arg == name:
            if isinstance(keyword.value, ast.Constant):
                return keyword.value.value
            return None
    return default


def _constant_strings(
    node: ast.expr | None, constants: Mapping[str, tuple[str, ...]]
) -> tuple[str, ...] | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    if isinstance(node, ast.Name) and node.id in constants:
        return constants[node.id]
    if isinstance(node, ast.Tuple | ast.List):
        out: list[str] = []
        for element in node.elts:
            found = _constant_strings(element, constants)
            if found is None:
                return None
            out.extend(found)
        return tuple(out)
    return None


def bind(
    function: FunctionInfo,
    arguments: list[Value],
    keywords: dict[str | None, Value],
    *,
    bound: bool,
    spread: int | None = None,
) -> dict[str, Value]:
    """What each parameter of *function* receives from one call.

    From *spread*, the place of the first ``*`` argument, on, the number of
    values the call hands is unknown: that argument and every one after it
    may land in any place from its own on, or in ``*args``, and a place they
    may leave unfilled is one a keyword or ``**options`` may fill. A place an
    explicit keyword fills is that keyword's alone.
    """
    spec = function.node.args
    positional = [a.arg for a in (*spec.posonlyargs, *spec.args)]
    if bound and function.kind in {"method", "classmethod"}:
        positional = positional[1:]
    mapping: dict[str, Value] = {}
    extra: list[Value] = []
    beyond: list[Value] = []
    maybe: set[str] = set()
    for index, value in enumerate(arguments):
        if spread is not None and index >= spread:
            for name in positional[spread:]:
                mapping[name] = union(mapping.get(name, _CLEAN), value)
            maybe.update(positional[spread:])
            beyond.append(value)
        elif index < len(positional):
            mapping[positional[index]] = value
        else:
            extra.append(value)
    if spec.vararg is not None:
        mapping[spec.vararg.arg] = union(_CLEAN, *extra, *beyond)
    else:
        for value in extra:
            for name in positional:
                mapping[name] = union(mapping.get(name, _CLEAN), value)
    # A keyword, or a mapping, fills no positional-only parameter: what it
    # hands under that name goes to ``**kwargs``.
    names = (set(positional) - {a.arg for a in spec.posonlyargs}) | {
        a.arg for a in spec.kwonlyargs
    }
    spill: list[Value] = []
    unpacked: list[Value] = []
    for keyword, value in keywords.items():
        if keyword is None:
            unpacked.append(value)
        elif keyword in names:
            # The place is the keyword's alone: a ``*`` argument or a
            # mapping that filled it too would make the call raise.
            mapping[keyword] = value
            maybe.discard(keyword)
        else:
            spill.append(value)
    # ``**options`` can only reach the parameters nothing else has filled,
    # or that only a ``*`` argument, which may unpack nothing, may fill.
    for value in unpacked:
        for parameter in names - (set(mapping) - maybe):
            mapping[parameter] = union(mapping.get(parameter, _CLEAN), flat(value))
        spill.append(value)
    if spec.kwarg is not None:
        mapping[spec.kwarg.arg] = union(_CLEAN, *spill)
    return mapping


def substitute(value: Value, mapping: Mapping[str, Value]) -> Value:
    """A summary's value with each parameter replaced by what the call gave it."""
    if isinstance(value, Shaped):
        return Shaped(tuple(substitute(item, mapping) for item in value.items))
    if isinstance(value, Fields):
        return Fields(
            tuple((key, substitute(item, mapping)) for key, item in value.items),
            flat(substitute(value.rest, mapping)),
        )
    if isinstance(value, Many):
        return Many(substitute(value.item, mapping))
    out: set[str] = set()
    for label in value:
        out |= flat(mapping.get(label, _CLEAN))
    return frozenset(out)


def find_positions(tree: Tree) -> None:
    """Which functions return a mask or an array of positions, to a fixed point.

    Indexing with what such a function returns copies; indexing with what
    any other function returns, a ``slice`` say, may hand out a view.
    """
    empty: dict[ast.AST, Summary] = {
        function.node: Summary() for function in tree.every_definition()
    }
    for _ in range(20):
        found: set[tuple[str, str]] = set()
        for key, definitions in tree.definitions.items():
            if definitions[-1].nested:
                continue
            # A name defined twice hands out positions only when each
            # definition of it does.
            if all(_returns_positions(tree, d, empty) for d in definitions):
                found.add(key)
        if found == tree.positions:
            break
        tree.positions = found
    # What the pass above learnt of the records' own copies was read without
    # the summaries; it is read again on them, for every class statement.
    for infos in tree.class_definitions.values():
        for info in infos:
            info.owned.clear()
            info.sealed.clear()
    tree.typed_cache.clear()


def _returns_positions(
    tree: Tree, function: FunctionInfo, summaries: Mapping[ast.AST, Summary]
) -> bool:
    """Whether every ``return`` of *function* hands out a mask or positions."""
    reader = Reader(tree, function, summaries, None)
    reader.run()
    return bool(reader.index_returns) and all(reader.index_returns)


def summarise(tree: Tree) -> dict[ast.AST, Summary]:
    """What each definition's return carries of its parameters, to a fixed point.

    By the definition itself: a name defined in each branch of an ``if``,
    or in each of two definitions of the function around it, has a summary
    for each, which a call reads with that definition's own parameters
    (:meth:`Reader.reached`).
    """
    summaries: dict[ast.AST, Summary] = {
        function.node: Summary() for function in tree.every_definition()
    }
    for _ in range(20):
        changed = False
        # A nested function is summarised too, as a helper of the module
        # is, for the calls the function around it makes to it.
        for function in tree.every_definition():
            value = Reader(tree, function, summaries, None).run()
            grown = union(summaries[function.node].value, value)
            if grown != summaries[function.node].value:
                summaries[function.node] = Summary(grown)
                changed = True
        if not changed:
            break
    return summaries


def findings_in(
    files: Sequence[pathlib.Path],
    root: pathlib.Path = SOURCE,
    *,
    tree: Tree | None = None,
) -> list[Finding]:
    """Every place a function keeps an array it was handed without a copy.

    *tree* is the package already read from *files*, when the caller has it.
    """
    if tree is None:
        tree = Tree(files, root)
    find_positions(tree)
    summaries = summarise(tree)
    # What each record's ``__post_init__`` copies, read once more on the
    # final summaries so that a factory is not held to a copy the record
    # already makes.
    for infos in tree.class_definitions.values():
        for info in infos:
            info.owned.clear()
            info.sealed.clear()
    for function in tree.every_definition():
        if function.node.name == "__post_init__":
            Reader(tree, function, summaries, None).run()
    tree.typed_cache.clear()
    found: list[Finding] = []
    for function in tree.every_definition():
        # A function written where it never runs keeps nothing.
        never_runs = for_the_type_checker(tree.modules[function.module])
        if not function.nested and id(function.node) not in never_runs:
            Reader(tree, function, summaries, found).run()
    return sorted(set(found), key=lambda f: (f.path, f.line, f.sink))


def records_without_mechanism(
    files: Sequence[pathlib.Path],
    root: pathlib.Path = SOURCE,
    *,
    tree: Tree | None = None,
) -> list[Finding]:
    """Every public record that can hold an array and does not copy it.

    A record a caller builds by hand never passes through a function of the
    package, so no trail the analysis above follows reaches it; the record
    has to copy for itself. One that inherits :data:`MECHANISM`, directly or
    through a record it extends, does; any other public record with a field
    annotated as something that can hold an array is reported, at its class.
    Each ``class`` statement of a public name is read, as a caller may build
    the one written in either branch of an ``if``, or one an alias keeps
    after a later one replaced it.
    *tree* is the package already read from *files*, when the caller has it.
    """
    if tree is None:
        tree = Tree(files, root)
    found: list[Finding] = []
    for key in sorted(tree.public):
        for info in tree.class_definitions[key]:
            if not info.record or tree.copies_arrays(info):
                continue
            annotations = dict(tree.record_fields(info)) | info.attributes
            holding = sorted(
                name
                for name, annotation in annotations.items()
                if tree.holds_array(annotation)
            )
            if holding:
                found.append(
                    Finding(
                        tree.paths[key[0]],
                        key[1],
                        info.line,
                        f"{info.name} can hold an array ({', '.join(holding)}) "
                        f"and does not inherit {MECHANISM}",
                        (),
                    )
                )
    return found


def handovers_in(
    files: Sequence[pathlib.Path],
    root: pathlib.Path = SOURCE,
    *,
    tree: Tree | None = None,
) -> list[Finding]:
    """Every array handed over to a record that the reading cannot vouch for.

    Each call to :data:`HANDOVER`, however it is spelt
    (:func:`_names_target`), is read where it stands
    (:meth:`Reader.handover_refused`); a call outside a function the tree
    reads (at module level, in a class body, in a lambda), and the function
    named anywhere but as the callee of a call, are refused outright, since
    nothing can then be proved of the array. No exemption covers this part:
    an array that cannot be proved alone is copied, as every other one is.
    *tree* is the package already read from *files*, when the caller has it.
    """
    if tree is None:
        tree = Tree(files, root)
    target = (f"{tree.package}._internal.frozen", HANDOVER)
    by_node = {function.node: function for function in tree.every_definition()}
    found: list[Finding] = []
    for module, syntax in tree.modules.items():
        named = [
            node
            for node in ast.walk(syntax)
            if _names_target(node, tree, module, target)
        ]
        if not named:
            continue
        parents = {
            child: parent
            for parent in ast.walk(syntax)
            for child in ast.iter_child_nodes(parent)
        }
        for node in named:
            call = parents.get(node)
            scope = parents.get(node)
            while scope is not None and not isinstance(
                scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
            ):
                scope = parents.get(scope)
            function = (
                by_node.get(scope)
                if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef)
                else None
            )
            reason: str | None
            if not isinstance(call, ast.Call) or call.func is not node:
                reason = "the function is named where it is not called"
            elif function is None:
                reason = "it is not called in a function"
            else:
                reason = Reader(tree, function, {}, None).handover_refused(call)
            if reason is not None:
                found.append(
                    Finding(
                        tree.paths[module],
                        function.qualname if function is not None else "<module>",
                        getattr(node, "lineno", 0),
                        f"{HANDOVER}(...): {reason}",
                        (),
                    )
                )
    return sorted(set(found), key=lambda f: (f.path, f.line, f.sink))


def _names_target(
    node: ast.AST, tree: Tree, module: str, target: tuple[str, str]
) -> bool:
    """Whether *node* may name the function *target* in *module*.

    A bare name imported from its module under any name counts, and so,
    spelt as the function's own name, does any other bare name, any
    attribute whatever it is read from (``frozen.handed_over``,
    ``_internal.frozen.handed_over``, a module bound by any import) and the
    string itself (``getattr(frozen, "handed_over")``). The reading errs on
    the side of the proof: a spelling it cannot follow to the module is held
    to it all the same, since nothing else in the package bears that name.
    """
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        return node.id == target[1] or target in tree.resolve_all(module, node.id)
    if isinstance(node, ast.Attribute):
        return node.attr == target[1]
    return isinstance(node, ast.Constant) and node.value == target[1]


def containers_kept_as_given(root: pathlib.Path = SOURCE) -> list[Finding]:
    """The fields of records a caller builds that keep a fixed container as given.

    The fifth part: a field annotated as an array, a ``tuple``, a ``list`` or
    a set that the record does not convert. The records and their fields are
    read as ``scripts/check_parameter_annotations.py`` reads them, aliases
    spelt out.
    """
    import check_parameter_annotations as constructors
    import check_return_overloads as overloads

    package = overloads.Package(python_files([], root), root)
    reader = constructors.Reader(package)
    found: list[Finding] = []
    for record in sorted(constructors.built_records(reader)):
        module = reader.annotations.classes[record][0]
        path = constructors.repository_path(package.paths[module], root)
        name = record.rpartition(".")[2]
        for kept_field, fixed in constructors.kept_as_given(reader, record):
            found.append(
                Finding(
                    path,
                    f"{name}.{kept_field.name}",
                    kept_field.line,
                    f"{name}.{kept_field.name} is annotated {', '.join(fixed)} "
                    "and keeps whatever it is given: nothing converts it",
                    (),
                )
            )
    return found


def main(argv: Sequence[str] | None = None) -> int:
    """Report every array kept without a copy of its own."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package",
        nargs="?",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to read (default: src/phonometry); the "
        "whole package is read, because a helper in one module carries an "
        "array into another",
    )
    arguments = parser.parse_args(argv)
    root = arguments.package.resolve()
    files = python_files([], root)
    tree = Tree(files, root)
    unequipped, stale_records = exempted(
        records_without_mechanism(files, root, tree=tree), RECORD_EXEMPT
    )
    found, stale = exempted(findings_in(files, root, tree=tree), EXEMPT)
    unproved = handovers_in(files, root, tree=tree)
    kept, stale_kept = exempted(containers_kept_as_given(root), KEPT_EXEMPT)
    if not (
        found or stale or unequipped or stale_records or unproved or kept or stale_kept
    ):
        print(
            "Every array a result keeps is a copy of its own, or an array "
            "nothing else can reach, and every record a caller builds "
            "converts the containers it holds."
        )
        return 0
    if kept:
        print("::error::a record a caller builds keeps a container as it was given")
        for finding in kept:
            print(f"  {finding.path}:{finding.line}: {finding.sink}")
        print(
            "  -> convert the field in __post_init__ (read_only(np.asarray(...)) "
            "for an array, tuple(...) for a tuple) and declare what the "
            "constructor takes in a TYPE_CHECKING __init__; a field that has to "
            "keep what it is given goes in KEPT_EXEMPT at the top of "
            "scripts/check_array_aliasing.py with its reason."
        )
    for key in stale_kept:
        print(f"::error::KEPT_EXEMPT lists {key}, which needs no exemption any more")
    if unequipped:
        print(
            "::error::a public record can hold an array and keeps whatever "
            "array a caller hands it"
        )
        for finding in unequipped:
            print(f"  {finding.path}:{finding.line}: {finding.sink}")
        print(
            f"  -> inherit {MECHANISM} from phonometry._internal.frozen, last "
            "among the bases; a record that has to keep the caller's array goes "
            "in RECORD_EXEMPT at the top of scripts/check_array_aliasing.py "
            "with its reason."
        )
    if found:
        print("::error::a result keeps an array it was handed, not a copy of it")
        for finding in found:
            carried = (
                f" <- {', '.join(finding.parameters)}" if finding.parameters else ""
            )
            print(
                f"  {finding.path}:{finding.line}: {finding.function}: "
                f"{finding.sink}{carried}"
            )
        print(
            f"  -> hand a record that inherits {MECHANISM} the array as it is (it "
            "makes the copy), or np.asarray(value, dtype=...) for a type it has "
            "to change; anything else stores read_only_copy(value) from "
            "phonometry._internal.frozen (a copy of its own, read only); a "
            "function that has to keep the caller's array goes in EXEMPT at the "
            "top of scripts/check_array_aliasing.py with its reason."
        )
    if unproved:
        print(
            f"::error::an array is handed to a record through {HANDOVER} and "
            "nothing proves that the record is the only one to hold it"
        )
        for finding in unproved:
            print(
                f"  {finding.path}:{finding.line}: {finding.function}: {finding.sink}"
            )
        print(
            "  -> hand the record the array as it is, and the record copies it; "
            f"{HANDOVER} is only for an array the function allocates itself "
            "(np.zeros, np.empty, np.ones), only writes into, there or in the "
            "helpers it passes it to, and hands to the record it returns."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which keeps no array any more")
    for key in stale_records:
        print(f"::error::RECORD_EXEMPT lists {key}, which needs no exemption any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
