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
:class:`~phonometry.io.Signal` is accepted too).

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
  it takes each argument in (``for i, m in enumerate(matrices)``). A
  function whose parameter is annotated a single number, a text or a record
  says it takes no array, and is not followed. A ``tuple`` of a fixed length
  at the top of the annotation (``tuple[float, float]``, a pair of limits)
  is a record of numbers whose arity the annotation states, not an array
  input;
* a parameter the body converts item by item (``for item in contributions:
  np.asarray(item)``) need not take ``ArrayLike``, but the item type of each
  sequence it is annotated takes what numpy converts of one item: a number,
  a sequence of numbers of any length, or ``ArrayLike``. An item type that
  holds several numbers only in an array or in a ``tuple`` of a fixed
  length (``Sequence[tuple[float, float]]``, ``tuple[NDArray, NDArray]``)
  refuses the list the conversion takes, and fails;
* when the function is overloaded, a caller sees only the heads, so a head
  that takes such a parameter narrower than ``ArrayLike`` fails as well,
  unless it takes it as a type parameter: that is a head that tells the
  shape of its argument apart (rule A57), beside a last head that takes
  ``ArrayLike``;
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
record's own contract governs, and is not read here.

:data:`EXEMPT` is the escape hatch, keyed by file, qualified function and
parameter, each with its reason; an entry that covers nothing fails the
check too. The files ``scripts/gpu_parity.py`` fingerprints are exempt as a
whole, read from its ``_COVERED`` so that the list cannot drift: an
annotation edit there moves the fingerprint the GPU parity lock holds, and
their parameters are typed in one batch with a GPU run of their own; the
report counts what they hold back. A copy of the package read elsewhere
(the scratch tree a defect is put into to see the check fail) names its
files as the repository does, so the exemptions read it the same way.

Static and dependency-free, so it runs on its own.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import check_return_overloads as overloads
from ast_scan import ROOT, python_files

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

#: Where the package lives; the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"

#: The script whose ``_COVERED`` names the files the GPU parity lock holds.
GPU_PARITY = ROOT / "scripts" / "gpu_parity.py"

#: Why the GPU-parity files are exempt as a whole.
GPU_PARITY_REASON = (
    "an edit to a file scripts/gpu_parity.py fingerprints invalidates "
    "gpu-parity.lock, so the parameters of those files are typed in one "
    "batch of their own, with the GPU run that records the lock again"
)

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


@dataclass(frozen=True)
class Finding:
    """A public parameter annotated narrower than what its body accepts."""

    path: str
    line: int
    function: str
    parameter: str
    problem: str

    @property
    def key(self) -> tuple[str, str, str]:
        """The file, the qualified function and the parameter."""
        return self.path, self.function, self.parameter


def gpu_parity_files(script: pathlib.Path = GPU_PARITY) -> tuple[str, ...]:
    """The files the GPU parity lock holds, as ``_COVERED`` of *script* names them.

    Read from the source, so that this script needs neither numpy nor the
    package that ``gpu_parity.py`` imports; each entry is a path joined
    onto the repository root with ``/``.
    """
    if not script.is_file():
        return ()
    tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    for node in tree.body:
        assigned = overloads._assigned(node)
        if assigned is None or assigned[0] != "_COVERED":
            continue
        if not isinstance(assigned[1], ast.Tuple | ast.List):
            break
        return tuple(
            element.right.value
            for element in assigned[1].elts
            if isinstance(element, ast.BinOp)
            and isinstance(element.right, ast.Constant)
            and isinstance(element.right.value, str)
        )
    return ()


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


def _carries(node: ast.expr | None, names: frozenset[str]) -> bool:
    """Whether an expression is one of *names*, or chooses between them."""
    if isinstance(node, ast.Name):
        return node.id in names
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
    #: One item of a whole value, which a loop over it takes in turn.
    item: frozenset[str]


#: What each kind of name holds once a loop reads it item by item: a pack
#: gives its arguments, each a whole value; a whole value gives its items.
#: An item of an item is not followed.
_ITERATED = {"pack": "whole", "whole": "item"}


def _kind(node: ast.expr | None, names: dict[str, set[str]]) -> str | None:
    """What an expression holds of the parameter, if it holds it at all."""
    for kind, bound in names.items():
        if _carries(node, frozenset(bound)):
            return kind
    copied = _single_argument(node, _COPIES)
    return _kind(copied, names) if copied is not None else None


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
    if kind in _ITERATED and isinstance(target, ast.Name):
        yield target.id, _ITERATED[kind]


def _bound(
    node: ast.FunctionDef | ast.AsyncFunctionDef, name: str, *, vararg: bool
) -> Bound:
    """The local names a body binds to parameter *name*, as it stands or item by item."""
    names: dict[str, set[str]] = {"whole": set(), "pack": set(), "item": set()}
    names["pack" if vararg else "whole"].add(name)
    changed = True
    while changed:
        changed = False
        for child in ast.walk(node):
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
    return Bound(
        whole=frozenset(names["whole"]),
        pack=frozenset(names["pack"]),
        item=frozenset(names["item"]),
    )


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
    """Follows a parameter from a public function to a conversion of it."""

    def __init__(self, package: overloads.Package) -> None:
        self.package = package
        self.annotations = Annotations(package)

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

    def _callee(
        self, function: overloads.Function, call: ast.Call
    ) -> tuple[str, bool] | None:
        """What a call reaches: a function of the package, or a numpy conversion.

        With whether the callee's first parameter is filled by the call
        itself (``self`` of a method, the instance of a constructor).
        """
        func = call.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in {"self", "cls"}
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
        if target in _CONVERTERS:
            return target, False
        if target in self.annotations.classes:
            constructor = self._method(target, "__init__")
            return (constructor, True) if constructor is not None else None
        if target in self.package.functions:
            callee = self.package.functions[target]
            node = callee.implementation
            is_method = (
                callee.owner is not None and node is not None and not _is_static(node)
            )
            return target, is_method and isinstance(func, ast.Attribute)
        return None

    def conversion(
        self, function: overloads.Function, name: str, *, item: bool = False
    ) -> str | None:
        """How parameter *name* of *function* reaches a conversion, if it does.

        With *item*, how one item of it does, the body reading the parameter
        item by item.
        """
        for how, of_item in self._routes(function, name, 0, frozenset()):
            if of_item == item:
                return how
        return None

    def _routes(
        self,
        function: overloads.Function,
        name: str,
        depth: int,
        seen: frozenset[str],
    ) -> Iterator[tuple[str, bool]]:
        """Each way parameter *name* reaches a conversion, and whether an item of it does."""
        node = function.implementation
        if node is None or depth > DEPTH:
            return
        vararg = node.args.vararg is not None and node.args.vararg.arg == name
        bound = _bound(node, name, vararg=vararg)
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            for names, of_item in (
                (bound.whole | bound.pack, False),
                (bound.item, True),
            ):
                positions = [
                    index
                    for index, value in enumerate(call.args)
                    if _holds(value, names)
                ]
                keywords = [
                    keyword.arg
                    for keyword in call.keywords
                    if keyword.arg is not None and _holds(keyword.value, names)
                ]
                if not (positions or keywords):
                    continue
                callee = self._callee(function, call)
                if callee is None:
                    continue
                target, bound_self = callee
                if target in _CONVERTERS:
                    where, keyword = _CONVERTERS[target]
                    if where is None or where in positions or keyword in keywords:
                        yield f"{target.replace('numpy.', 'np.')}()", of_item
                    continue
                for how, deeper in self._handed(
                    target,
                    positions,
                    keywords,
                    bound=bound_self,
                    depth=depth,
                    seen=seen,
                ):
                    if not (of_item and deeper):
                        yield how, of_item or deeper

    def _handed(
        self,
        target: str,
        positions: list[int],
        keywords: list[str],
        *,
        bound: bool,
        depth: int,
        seen: frozenset[str],
    ) -> Iterator[tuple[str, bool]]:
        """What the function a parameter is handed to does with it."""
        callee = self.package.functions[target]
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
        for parameter in received:
            key = f"{target}({parameter})"
            if key in seen:
                continue
            annotation = parameters[parameter].annotation
            if self.annotations.names_array_like(callee.module, annotation, bounds):
                yield f"handed to {callee.qualname}({parameter}: ArrayLike)", False
                continue
            if not self.annotations.may_hold_numbers(callee.module, annotation, bounds):
                continue
            for deeper, of_item in self._routes(
                callee, parameter, depth + 1, seen | {key}
            ):
                yield f"handed to {callee.qualname}({parameter}), {deeper}", of_item


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


def findings_in(files: Sequence[pathlib.Path], root: pathlib.Path) -> list[Finding]:
    """Every public parameter annotated narrower than what its body accepts."""
    package = overloads.Package(files, root)
    reader = Reader(package)
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
        how = reader.conversion(function, name, item=True) if narrow else None
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
    how = reader.conversion(function, name, item=True) if items else None
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


def repository_path(path: str, root: pathlib.Path) -> str:
    """A file of the package as the repository names it, a copy's included.

    The repository's own ``src/phonometry/room/acoustics.py`` keeps its
    name, and the same file of a copy of the package read elsewhere (a
    scratch tree a defect is put into to see the check fail) is given that
    name too, so that :data:`EXEMPT` and the GPU-parity files key a copy
    the way they key the package.
    """
    absolute = pathlib.Path(path)
    absolute = (absolute if absolute.is_absolute() else ROOT / absolute).resolve()
    if not absolute.is_relative_to(root):
        return path
    below = absolute.relative_to(root).as_posix()
    return f"{SOURCE.relative_to(ROOT).as_posix()}/{below}"


def held_for_gpu(
    findings: Sequence[Finding], gpu_files: Iterable[str]
) -> tuple[list[Finding], list[Finding]]:
    """The findings outside the GPU-parity files, and those in them."""
    held_files = set(gpu_files)
    kept = [finding for finding in findings if finding.path not in held_files]
    held = [finding for finding in findings if finding.path in held_files]
    return kept, held


def checked(
    findings: Sequence[Finding], exempt: dict[tuple[str, str, str], str]
) -> tuple[list[Finding], list[tuple[str, str, str]]]:
    """The findings no exemption covers, and the exemptions that cover none."""
    used = {finding.key for finding in findings}
    kept = [finding for finding in findings if finding.key not in exempt]
    return kept, sorted(set(exempt) - used)


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
    every = findings_in(python_files([], root), root)
    kept, held = held_for_gpu(every, gpu_parity_files())
    found, stale = checked(kept, EXEMPT)
    if held:
        print(
            f"{len(held)} parameter(s) of the GPU-parity files are left out: "
            f"{GPU_PARITY_REASON}."
        )
    if not (found or stale):
        print(
            "Every public parameter admits what its body converts, and none "
            "holds an invariant list, dict or set."
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
            "Mapping[...]. A parameter narrower on purpose goes in EXEMPT at "
            "the top of scripts/check_parameter_annotations.py with its reason."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which needs no exemption any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
