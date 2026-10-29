#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The clip scenes keep their fields on the engine's device between captures.

A scene that steps a public FDTD engine can be sent to a GPU
(``scripts/clip_placement.py``). What works on NumPy then fails or crawls
there: a host array added into a device field or mixed into an expression of
device arrays (CuPy refuses to mix them), a field written into a host array
or pulled out on every turn of the loop, by ``float()``, by a method such as
``.item()`` or by the test of an ``if`` (a device sync and a copy per step,
which can cost more than the step), a NumPy function called on a device
array. This reads every scene for those, inside each loop that steps an
engine one turn at a time (a ``while`` loop or a ``for`` over ``range``),
knowing which names hold device arrays and which hold host arrays from what
each name is assigned anywhere in the function. A method of a device array,
a reduction such as ``.max()`` among them, gives a device value. A field's
shape, size, rank and dtype are host values; so are an identity test
(``env is None``, which reads no value), one element of a host array picked
by an integer (``times[i]``), and a NumPy function of numbers
(``np.exp(-0.01)``: constants, the count of a ``for`` over ``range``, names
bound only to numbers, such elements, the named constants of NumPy, ``math``
and ``xp``), all of which a device array takes as numbers. A NumPy function
of a parameter or an attribute may be of an array, and is a host array.
Arithmetic would refuse an item of a host array that is an array, but a
write into a device array, and the engine's ``asarray``, copy it over
quietly, so there only an item of a host vector picked by a number is taken
for a number, a vector being a one-axis constructor by its binding or a
ufunc of one (a waveform on a time vector); any other item, and a name bound
to one, is an upload. A name unpacked from a call
(``xx, yy = np.meshgrid(...)``) holds what the call returns. The way through
is the backend: ``_host`` / ``to_host`` at a capture, the engine's namespace
(``xp``) for a reduction, and a host vector moved to the device once, before
the loop.
"""

from __future__ import annotations

import ast
import math
import pathlib
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

_FIELDS_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "figures" / "fields"
)

#: The arrays an engine stores or derives, read as ``sim.p`` or ``sims[0].vx``.
_FIELD_NAMES = frozenset({"p", "vx", "vy", "txx", "tyy", "txy"})
#: Calls on a backend or an engine that return a device array.
_DEVICE_MAKERS = frozenset({"zeros", "asarray", "index", "collocated"})
#: Calls that return a host array.
_HOST_ARRAYS = frozenset({"_host", "_blanked", "to_host", "numpy_field"})
#: The names the engine's array namespace goes by: ``xp``, ``sim._xp``,
#: ``sim._backend.xp``.
_DEVICE_NAMESPACES = frozenset({"xp", "_xp"})
#: Builtins that make a Python number of a device value, bringing it to the
#: host. ``abs`` is not one: on a device array it gives a device array.
_HOST_PULLS = frozenset({"bool", "complex", "float", "int", "max", "min", "round"})
#: Methods that make Python objects of a device array's values, on the host.
_METHOD_PULLS = frozenset({"item", "tolist"})
#: What an array says about itself rather than holds: host values on any device.
_DESCRIPTIONS = frozenset({"shape", "size", "ndim", "dtype", "itemsize", "nbytes"})
#: Builtins that give a number whatever they are given.
_TO_NUMBER = frozenset({"bool", "complex", "float", "int", "len", "round"})
#: Builtins that give a number when every argument is one.
_OF_NUMBERS = frozenset({"abs", "max", "min", "pow"})
#: The constants of the array API standard, on the engine's namespace.
_ARRAY_API_NUMBERS = frozenset({"e", "inf", "nan", "pi"})
#: NumPy constructors that always make one axis: ranges and windows.
_VECTOR_MAKERS = frozenset(
    {"arange", "linspace", "logspace", "geomspace"}
    | {"hanning", "hamming", "blackman", "bartlett", "kaiser"}
)
#: NumPy constructors whose first argument is the shape.
_SHAPED_MAKERS = frozenset({"empty", "full", "ones", "zeros"})
#: The NumPy functions that make a NumPy number of numbers: its universal
#: functions (``np.exp``, ``np.sin``) and its scalar types (``np.float64``).
_NUMPY_OF_NUMBERS = frozenset(
    name
    for name, value in vars(np).items()
    if isinstance(value, np.ufunc)
    or (isinstance(value, type) and issubclass(value, np.generic))
)


def _callee(call: ast.Call) -> tuple[str | None, str]:
    """The receiver name (None for a bare function) and the name called.

    The receiver is the last name before the call: ``xp`` for ``xp.max`` and
    for ``sim._backend.xp.max`` alike, ``""`` when it is not a name.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return None, func.id
    if not isinstance(func, ast.Attribute):
        return None, ""
    if isinstance(func.value, ast.Name):
        return func.value.id, func.attr
    if isinstance(func.value, ast.Attribute):
        return func.value.attr, func.attr
    return "", func.attr


def _arguments(call: ast.Call) -> list[ast.expr]:
    """What *call* is given, by position and by keyword."""
    return [*call.args, *(k.value for k in call.keywords)]


def _is_field(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr in _FIELD_NAMES
        and isinstance(node.value, ast.Name | ast.Subscript)
    )


@dataclass
class _Scope:
    """What the names of one function hold.

    :ivar device: The names ever bound to a device array.
    :ivar host: The names ever bound to a host array.
    :ivar numbers: The names bound only to numbers.
    :ivar vectors: The names bound only to one-dimensional host arrays.
    :ivar items: The names bound to an item of a host array that may be an
        array: a row of a matrix, or a pick by a parameter.
    """

    device: set[str] = field(default_factory=set)
    host: set[str] = field(default_factory=set)
    numbers: frozenset[str] = frozenset()
    vectors: frozenset[str] = frozenset()
    items: frozenset[str] = frozenset()


def _is_named_number(node: ast.Attribute) -> bool:
    """Whether *node* is a named number of NumPy, ``math`` or the engine's namespace.

    ``np.pi`` and ``math.tau`` say, and the constants of the array API
    standard on ``xp``: ``xp.pi``, ``xp.e``, ``xp.inf``, ``xp.nan``, through
    ``sim._backend.xp`` as well.
    """
    modules = {"np": np, "math": math}
    value = node.value
    owner = value.id if isinstance(value, ast.Name) else ""
    if isinstance(value, ast.Attribute):
        owner = value.attr
    if owner in _DEVICE_NAMESPACES:
        return node.attr in _ARRAY_API_NUMBERS
    if owner not in modules:
        return False
    return isinstance(getattr(modules[owner], node.attr, None), int | float)


def _call_is_number(call: ast.Call, scope: _Scope) -> bool:
    """Whether *call* gives a number: ``float()``, ``math.*``, or a ufunc of numbers."""
    receiver, name = _callee(call)
    if (receiver is None and name in _TO_NUMBER) or receiver == "math":
        return True
    of_numbers = (receiver is None and name in _OF_NUMBERS) or (
        receiver == "np" and name in _NUMPY_OF_NUMBERS
    )
    return of_numbers and all(_is_number(a, scope) for a in _arguments(call))


def _is_number(node: ast.AST, scope: _Scope) -> bool:
    """Whether *node* is a number: a constant, a name bound only to numbers, or made of them.

    One element of a host array is a NumPy number. A parameter, an attribute
    and anything else unknown is not one.
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int | float | complex)
    if isinstance(node, ast.Name):
        return node.id in scope.numbers
    if isinstance(node, ast.Attribute):
        return _is_named_number(node)
    if isinstance(node, ast.Call):
        return _call_is_number(node, scope)
    if isinstance(node, ast.Subscript):
        return _is_axis_length(node, scope) or _is_host_element(node, scope)
    if isinstance(node, ast.UnaryOp | ast.BinOp | ast.IfExp):
        parts = [c for c in ast.iter_child_nodes(node) if isinstance(c, ast.expr)]
        return all(_is_number(part, scope) for part in parts)
    return False


def _is_axis_length(node: ast.Subscript, scope: _Scope) -> bool:
    """Whether *node* is the length of one axis of an array, ``x.shape[k]``."""
    shape = node.value
    return (
        isinstance(shape, ast.Attribute)
        and shape.attr == "shape"
        and not isinstance(node.slice, ast.Slice | ast.Tuple)
        and _is_number(node.slice, scope)
    )


def _is_shape_of_one_axis(node: ast.expr, scope: _Scope) -> bool:
    """Whether *node*, a shape, surely has one axis.

    A count (a constant, a name bound only to numbers, ``len(x)``,
    ``x.shape[k]``) or a tuple or list of one with nothing unpacked into it.
    A name that may hold a tuple, a parameter among them, and a tuple added
    to another may have more.
    """
    if isinstance(node, ast.Tuple | ast.List):
        return len(node.elts) == 1 and not isinstance(node.elts[0], ast.Starred)
    return _is_number(node, scope)


def _is_flat_literal(node: ast.expr) -> bool:
    """Whether *node* is a list or tuple literal with no list or tuple in it."""
    return isinstance(node, ast.List | ast.Tuple) and not any(
        isinstance(e, ast.List | ast.Tuple | ast.Starred) for e in node.elts
    )


def _makes_vector(call: ast.Call, scope: _Scope) -> bool:
    """Whether *call* makes a one-dimensional NumPy array, by what it is.

    A ufunc of vectors and numbers, at least one a vector, keeps the axis:
    a waveform drawn on a time vector (``np.sin(2 * np.pi * f * times)``).
    """
    receiver, name = _callee(call)
    if receiver != "np":
        return False
    if name in _VECTOR_MAKERS:
        return True
    if name in _NUMPY_OF_NUMBERS:
        given = _arguments(call)
        return any(_is_vector(a, scope) for a in given) and all(
            _is_vector(a, scope) or _is_number(a, scope) for a in given
        )
    first = call.args[0] if call.args else None
    if first is None:
        return False
    if name in _SHAPED_MAKERS:
        return _is_shape_of_one_axis(first, scope)
    return name in ("array", "asarray") and _is_flat_literal(first)


def _is_vector(node: ast.AST, scope: _Scope) -> bool:
    """Whether *node* is a one-dimensional host array, by its binding.

    A name bound only to vectors, a NumPy constructor of one axis
    (``np.zeros(n)``, ``np.ones((n,))``, ``np.arange``, ``np.linspace``, a
    window, ``np.asarray`` of a flat literal), and arithmetic of vectors and
    numbers.
    """
    if isinstance(node, ast.Name):
        return node.id in scope.vectors
    if isinstance(node, ast.Call):
        return _makes_vector(node, scope)
    if isinstance(node, ast.UnaryOp):
        return _is_vector(node.operand, scope)
    if isinstance(node, ast.BinOp):
        sides = (node.left, node.right)
        return any(_is_vector(side, scope) for side in sides) and all(
            _is_vector(side, scope) or _is_number(side, scope) for side in sides
        )
    return False


#: Stands for the integer a ``for`` over ``range`` binds its name to.
_COUNT = ast.Constant(0)


def _bound_values(node: ast.AST) -> list[tuple[ast.expr, ast.expr | None]]:
    """The targets *node* binds and the value each takes; None where it is not one value."""
    if isinstance(node, ast.Assign):
        return [(target, node.value) for target in node.targets]
    if isinstance(node, ast.AugAssign | ast.AnnAssign) and node.value is not None:
        return [(node.target, node.value)]
    if isinstance(node, ast.For):
        counts = isinstance(node.iter, ast.Call) and _callee(node.iter) == (
            None,
            "range",
        )
        return [(node.target, _COUNT if counts else None)]
    return []


def _stored(target: ast.expr) -> list[ast.Name]:
    """The names *target* binds: itself, or those it unpacks; none for an item or attribute."""
    return [
        n
        for n in ast.walk(target)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    ]


def _literal_pairs(
    target: ast.expr, value: ast.expr | None
) -> list[tuple[ast.expr, ast.expr]] | None:
    """The elements *target* and *value* unpack pair by pair; None when they do not.

    They do when both are tuple or list literals of one length with nothing
    starred in either.
    """
    if not isinstance(target, ast.Tuple | ast.List):
        return None
    if not isinstance(value, ast.Tuple | ast.List):
        return None
    if len(target.elts) != len(value.elts):
        return None
    if any(isinstance(e, ast.Starred) for e in [*target.elts, *value.elts]):
        return None
    return list(zip(target.elts, value.elts, strict=True))


def _paired(
    target: ast.expr, value: ast.expr | None
) -> list[tuple[ast.Name, ast.expr | None]]:
    """Each name *target* binds, with the value it takes; None where it is not one value.

    A tuple or list literal unpacked into a target of the same length, with
    nothing starred, gives each name its own element, at any depth; a name
    unpacked from anything else takes no one value.
    """
    if isinstance(target, ast.Name):
        return [(target, value)]
    pairs = _literal_pairs(target, value)
    if pairs is None:
        return [(name, None) for name in _stored(target)]
    return [named for element, item in pairs for named in _paired(element, item)]


def _bindings(func: ast.FunctionDef) -> dict[str, list[ast.expr | None]]:
    """Every value each name of *func* is bound to; None for a binding that is not one value.

    A parameter, a name unpacked from anything but a tuple literal of its own
    length, a ``with`` or comprehension name and any other way of binding a
    name is None.
    """
    found: dict[str, list[ast.expr | None]] = {}
    seen: set[int] = set()
    params = [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]
    for param in params:
        found.setdefault(param.arg, []).append(None)
    pairs = (pair for node in ast.walk(func) for pair in _bound_values(node))
    for name, value in (named for t, v in pairs for named in _paired(t, v)):
        found.setdefault(name.id, []).append(value)
        seen.add(id(name))
    others = (
        node
        for node in ast.walk(func)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and id(node) not in seen
    )
    for node in others:
        found.setdefault(node.id, []).append(None)
    return found


def _greatest(
    bound: dict[str, list[ast.expr | None]],
    holds: Callable[[ast.expr, frozenset[str]], bool],
) -> frozenset[str]:
    """The names every value of which *holds* of, given the names found so far.

    Every name with no binding but a value starts in, and a name leaves as
    soon as one of its values does not hold, until none leaves.
    """
    names = frozenset(
        name for name, values in bound.items() if all(v is not None for v in values)
    )
    while True:
        kept = frozenset(
            name
            for name in names
            if all(v is not None and holds(v, names) for v in bound[name])
        )
        if kept == names:
            return names
        names = kept


def _numbers(bound: dict[str, list[ast.expr | None]], base: _Scope) -> frozenset[str]:
    """The names bound only to numbers, an element of a host array of *base* among them."""
    return _greatest(
        bound, lambda value, names: _is_number(value, replace(base, numbers=names))
    )


def _of_device_array(call: ast.Call, scope: _Scope) -> bool:
    """Whether *call* is a method of a device array, ``sim.p.max()`` say."""
    return (
        isinstance(call.func, ast.Attribute)
        and _kind(call.func.value, scope) == "device"
    )


def _numpy_kind(call: ast.Call, scope: _Scope) -> str | None:
    """A host array, or None for ``np.errstate`` and for a NumPy number of numbers."""
    name = _callee(call)[1]
    if name == "errstate":
        return None
    if name in _NUMPY_OF_NUMBERS and all(
        _is_number(a, scope) for a in _arguments(call)
    ):
        return None
    return "host"


def _call_kind(call: ast.Call, scope: _Scope) -> str | None:
    """What *call* returns; ``abs`` leaves its argument where it is."""
    receiver, name = _callee(call)
    if (receiver, name) == (None, "abs"):
        return _merge(_kind(a, scope) for a in call.args)
    if name in _HOST_ARRAYS:
        return "host"
    if receiver == "np":
        return _numpy_kind(call, scope)
    if receiver in _DEVICE_NAMESPACES:
        return "device"
    if name in _DEVICE_MAKERS and receiver is not None:
        return "device"
    if _of_device_array(call, scope):
        return None if name in _METHOD_PULLS else "device"
    return None


def _merge(kinds: Iterable[str | None]) -> str | None:
    """``"device"`` if any of *kinds* is, else ``"host"`` if any is, else None."""
    found = set(kinds)
    if "device" in found:
        return "device"
    if "host" in found:
        return "host"
    return None


def _is_identity(node: ast.AST) -> bool:
    """Whether *node* compares by ``is`` or ``is not`` only, which reads no value."""
    return isinstance(node, ast.Compare) and all(
        isinstance(op, ast.Is | ast.IsNot) for op in node.ops
    )


def _is_host_element(node: ast.Subscript, scope: _Scope) -> bool:
    """Whether *node* picks one element of a host array by one integer index.

    The element is a NumPy number, which a device array takes as a number.
    A slice, a tuple of indexes or an array of them picks an array.
    """
    index = node.slice
    if isinstance(index, ast.Slice | ast.Tuple):
        return False
    if isinstance(index, ast.Constant) and not isinstance(index.value, int):
        return False
    return _kind(index, scope) is None and _kind(node.value, scope) == "host"


def _kind(node: ast.AST, scope: _Scope) -> str | None:
    """``"device"``, ``"host"`` or None (a number, or something unknown).

    A call is what it returns, an array's description, an identity test and
    an element of a host array are host numbers, and any other expression
    holds what its parts hold.
    """
    if _is_field(node):
        return "device"
    if isinstance(node, ast.Attribute) and node.attr in _DESCRIPTIONS:
        return None
    if _is_identity(node):
        return None
    if isinstance(node, ast.Name):
        return _merge(
            kind
            for kind, names in (("device", scope.device), ("host", scope.host))
            if node.id in names
        )
    if isinstance(node, ast.Call):
        return _call_kind(node, scope)
    if isinstance(node, ast.Subscript) and _is_host_element(node, scope):
        return None
    return _merge(_kind(child, scope) for child in ast.iter_child_nodes(node))


def _assignments(func: ast.AST) -> list[tuple[list[ast.expr], ast.expr]]:
    found: list[tuple[list[ast.expr], ast.expr]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            found.append((list(node.targets), node.value))
        elif isinstance(node, ast.AugAssign | ast.AnnAssign) and node.value is not None:
            found.append(([node.target], node.value))
    return found


def _unpacked(target: ast.expr, value: ast.expr) -> list[tuple[str, ast.expr]]:
    """Each name *target* binds, with the value it takes.

    A name unpacked from a tuple literal of the same length takes its own
    element; one unpacked from anything else, a call such as
    ``np.meshgrid`` say, takes what the whole holds.
    """
    if isinstance(target, ast.Name):
        return [(target.id, value)]
    if not isinstance(target, ast.Tuple | ast.List):
        return []
    pairs = _literal_pairs(target, value)
    if pairs is not None:
        return [named for element, item in pairs for named in _unpacked(element, item)]
    return [named for element in target.elts for named in _unpacked(element, value)]


def _bind(pairs: list[tuple[list[ast.expr], ast.expr]], scope: _Scope) -> None:
    """One pass over the assignments, adding each name to what its value holds."""
    for targets, value in pairs:
        for name, part in (pair for t in targets for pair in _unpacked(t, value)):
            kind = _kind(part, scope)
            if kind == "device":
                scope.device.add(name)
            elif kind == "host":
                scope.host.add(name)


def _held(func: ast.FunctionDef, numbers: frozenset[str]) -> _Scope:
    """The names *func* binds to device arrays and to host arrays, given its numbers.

    A name bound from another may come before it in the function, so the
    passes go on until one adds no name.
    """
    scope = _Scope(numbers=numbers)
    pairs = _assignments(func)
    known = -1
    while known != len(scope.device) + len(scope.host):
        known = len(scope.device) + len(scope.host)
        _bind(pairs, scope)
    return scope


def _names(func: ast.FunctionDef) -> _Scope:
    """What the names of *func* hold: device arrays, host arrays, numbers, vectors.

    A name bound to an element of a host array is a number, so the numbers
    are read twice: first with no host array known, then with those that
    reading found, which are as many as there can be.
    """
    bound = _bindings(func)
    widest = _held(func, _numbers(bound, _Scope()))
    scope = _held(func, _numbers(bound, widest))
    scope.vectors = _greatest(
        bound, lambda value, names: _is_vector(value, replace(scope, vectors=names))
    )
    scope.items = _items(bound, scope)
    return scope


def _items(bound: dict[str, list[ast.expr | None]], scope: _Scope) -> frozenset[str]:
    """The names bound to an item of a host array that may be an array.

    A name joins once one of its values may be one, through a name that has
    joined as well, until none joins.
    """
    items: frozenset[str] = frozenset()
    while True:
        here = replace(scope, items=items)
        grown = frozenset(
            name
            for name, values in bound.items()
            if any(v is not None and _uploads(v, here) for v in values)
        )
        if grown == items:
            return items
        items = grown


def _steps(node: ast.AST) -> bool:
    return any(
        isinstance(c, ast.Call)
        and isinstance(c.func, ast.Attribute)
        and c.func.attr == "step"
        for c in ast.walk(node)
    )


def _is_turn_loop(node: ast.AST) -> bool:
    if isinstance(node, ast.While):
        return True
    return (
        isinstance(node, ast.For)
        and isinstance(node.iter, ast.Call)
        and _callee(node.iter) == (None, "range")
    )


def _method_problem(node: ast.Call, scope: _Scope) -> str | None:
    """A device array's values pulled out, or copied where _host belongs."""
    func = node.func
    if not isinstance(func, ast.Attribute) or not _of_device_array(node, scope):
        return None
    name = func.attr
    if name in _METHOD_PULLS:
        return f".{name}() pulls a device value to the host on every turn"
    if name in ("astype", "copy") and not isinstance(func.value, ast.Call):
        return f".{name}() on a device array; bring it to the host with _host"
    return None


def _call_problem(node: ast.Call, scope: _Scope) -> str | None:
    receiver, name = _callee(node)
    kinds = {_kind(a, scope) for a in _arguments(node)}
    if receiver == "np" and name != "errstate" and "device" in kinds:
        return f"np.{name} on a device array; use the engine's namespace"
    if (
        receiver is None
        and name in _HOST_PULLS
        and any(_kind(a, scope) == "device" for a in node.args)
    ):
        return f"{name}() pulls a device value to the host on every turn"
    method = _method_problem(node, scope)
    if method:
        return method
    if _call_kind(node, scope) == "device" and (
        "host" in kinds or any(_uploads(a, scope) for a in _arguments(node))
    ):
        return _HOST_IN_DEVICE_EXPRESSION
    return None


_DEVICE_INTO_HOST = (
    "a device value written into a host array; bring it to the host with _host"
)
_HOST_INTO_DEVICE = "a host array written into a device array; move it to the device once, before the loop"
_HOST_IN_DEVICE_EXPRESSION = "a host array mixed into a device expression; move it to the device once, before the loop"
_TEST_PULL = "a test on a device value pulls it to the host on every turn"


def _is_known_element(node: ast.Subscript, scope: _Scope) -> bool:
    """Whether *node* is surely one number: a host vector picked by a number."""
    index = node.slice
    return (
        not isinstance(index, ast.Slice | ast.Tuple)
        and _is_number(index, scope)
        and _is_vector(node.value, scope)
    )


def _carried(node: ast.AST) -> list[ast.expr]:
    """The parts *node* carries a value through: operands, branches, NumPy arguments."""
    if isinstance(node, ast.UnaryOp | ast.BinOp):
        return [c for c in ast.iter_child_nodes(node) if isinstance(c, ast.expr)]
    if isinstance(node, ast.IfExp):
        return [node.body, node.orelse]
    if isinstance(node, ast.Call) and _callee(node)[0] == "np":
        return _arguments(node)
    return []


def _picks_an_array(node: ast.Subscript, scope: _Scope) -> bool:
    """Whether *node* is an item of a host array that may itself be an array."""
    base = node.value
    of_host = _kind(base, scope) == "host" or _uploads(base, scope)
    return of_host and not _is_known_element(node, scope)


def _uploads(node: ast.AST, scope: _Scope) -> bool:
    """Whether *node*, of no array kind, may still be a host array CuPy copies over.

    An item of a host array the guard cannot show to be one number, alone,
    in arithmetic or in a NumPy function, or a name bound to one: a row of a
    matrix, or a pick by a parameter that may be an array of indexes.
    """
    if isinstance(node, ast.Name):
        return node.id in scope.items
    if isinstance(node, ast.Subscript):
        return _picks_an_array(node, scope)
    return any(_uploads(part, scope) for part in _carried(node))


def _write_problem(target: ast.expr, value: ast.expr, scope: _Scope) -> str | None:
    """A host array written into a device array, or a device value into a host one.

    A write into a device array copies a host value over quietly, so one
    that may be a host array is named even where arithmetic would take it
    for a number.
    """
    kind = _kind(value, scope)
    base = _kind(target.value, scope) if isinstance(target, ast.Subscript) else None
    if _is_field(target) or base == "device":
        uploads = kind == "host" or (kind is None and _uploads(value, scope))
        return _HOST_INTO_DEVICE if uploads else None
    if isinstance(target, ast.Subscript) and kind == "device":
        return _DEVICE_INTO_HOST
    if isinstance(target, ast.Name) and target.id in scope.host and kind == "device":
        return f"{target.id} is a host array and takes a device value; make it with the backend"
    return None


def _mix_problem(node: ast.BinOp | ast.Compare, scope: _Scope) -> str | None:
    """A host array and a device array as the operands of one operator.

    ``is`` and ``is not`` compare the objects, never their values.
    """
    if _is_identity(node):
        return None
    operands = (
        [node.left, node.right]
        if isinstance(node, ast.BinOp)
        else [node.left, *node.comparators]
    )
    kinds = {_kind(operand, scope) for operand in operands}
    return _HOST_IN_DEVICE_EXPRESSION if {"host", "device"} <= kinds else None


def _node_problem(node: ast.AST, scope: _Scope) -> str | None:
    if isinstance(node, ast.Call):
        return _call_problem(node, scope)
    if isinstance(node, ast.Assign | ast.AugAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        reasons = (_write_problem(t, node.value, scope) for t in targets)
        return next((r for r in reasons if r), None)
    if isinstance(node, ast.BinOp | ast.Compare):
        return _mix_problem(node, scope)
    if isinstance(node, ast.If | ast.While | ast.IfExp | ast.Assert):
        return _TEST_PULL if _kind(node.test, scope) == "device" else None
    return None


def _problems_in(func: ast.FunctionDef, label: str) -> list[str]:
    scope = _names(func)
    found: set[str] = set()
    loops = (n for n in ast.walk(func) if _is_turn_loop(n) and _steps(n))
    for loop in loops:
        for node in ast.walk(loop):
            reason = _node_problem(node, scope)
            if reason and isinstance(node, ast.stmt | ast.expr):
                found.add(f"{label}:{node.lineno}: {reason}")
    return sorted(found)


def problems(source: str, label: str) -> list[str]:
    """Every host round trip inside a stepping loop of *source*."""
    tree = ast.parse(source)
    found: list[str] = []
    for func in ast.walk(tree):
        if isinstance(func, ast.FunctionDef):
            found.extend(_problems_in(func, label))
    return sorted(set(found))


_SCENES = sorted(p for p in _FIELDS_DIR.glob("*.py") if p.name != "__init__.py")


@pytest.mark.parametrize("path", _SCENES, ids=lambda p: p.name)
def test_a_scene_keeps_its_fields_on_the_device_between_captures(
    path: pathlib.Path,
) -> None:
    found = problems(path.read_text(encoding="utf-8"), path.name)
    assert not found, "\n".join(found)


def test_every_kind_of_round_trip_is_seen() -> None:
    source = """
def build(sim, sims, frames):
    taper = np.hanning(10)
    trace = np.empty(10)
    energy = np.zeros_like(sim.p)
    for i in range(10):
        sim.step()
        sim.vy[3] += taper * np.sin(i)
        trace[i] = sim.p[1, 2]
        level = float(sim.p[0, 0])
        frames.append(sim.p[::2, ::2].astype(np.float32))
        energy += sim.p**2
        np.maximum(trace, np.abs(sim.p[0]), out=trace)
        trace[i] = abs(sim.p[1, 2])
        trace[i] = sim._backend.xp.max(sim.p)
        sim.vy += taper
        sims[0].p *= taper
        count = int(sim.p[2, 2])
        peak = max(sim.p[0])
        snapshot = sim.p.copy()
        np.multiply(taper, 2.0, out=sim.vx)
"""
    reasons = [line.split(": ", 1)[1] for line in problems(source, "scene")]
    assert sorted(reasons) == sorted(
        [
            _HOST_INTO_DEVICE,
            _HOST_INTO_DEVICE,
            _HOST_INTO_DEVICE,
            _DEVICE_INTO_HOST,
            _DEVICE_INTO_HOST,
            _DEVICE_INTO_HOST,
            "float() pulls a device value to the host on every turn",
            "int() pulls a device value to the host on every turn",
            "max() pulls a device value to the host on every turn",
            ".astype() on a device array; bring it to the host with _host",
            ".copy() on a device array; bring it to the host with _host",
            "energy is a host array and takes a device value; make it with the backend",
            "np.abs on a device array; use the engine's namespace",
            "np.multiply on a device array; use the engine's namespace",
        ]
    )


def test_the_way_through_the_backend_is_clean() -> None:
    source = """
def build(sim, frames):
    backend = sim._backend
    xp = backend.xp
    taper = backend.asarray(np.hanning(10))
    history = backend.zeros((10,))
    energy = backend.zeros((4, 4))
    envelope = backend.zeros((4, 4))
    for i in range(10):
        sim.step()
        sim.vy[3] += taper * xp.sin(1.0 * i)
        sim.vy *= taper
        history[i] = sim.p[1, 2]
        energy += sim.p**2
        envelope = sim._backend.xp.maximum(envelope, abs(sim.p))
        if i % 2 == 0:
            frames.append(_host(sim, sim.p[::2, ::2]))
            with np.errstate(divide="ignore"):
                level = 10.0 * xp.log10(energy)
"""
    assert problems(source, "scene") == []


def test_a_loop_over_frequencies_is_not_a_stepping_turn() -> None:
    source = """
def build(make):
    for f in (100.0, 200.0):
        c = np.full((4, 4), 343.0)
        sim = make(c, f)
        for _ in range(10):
            sim.step()
"""
    assert problems(source, "scene") == []


#: A scene with host vectors (taper, ramp, times, trail, cells, shaped,
#: counted, and the pulse and gauss waveforms), host matrices (mask, plane,
#: rows, buffers of a shape the guard cannot count, a meshgrid unpacked and
#: picked), a row of one, the grid on the device and unpacked there, a NumPy
#: number, and a stepping loop that runs one line more.
_ONE_LINE_SCENE = """
def build(sim, omega, t, k, geom, idx, shape_p):
    xp = sim._backend.xp
    taper = np.hanning(10)
    mask = np.ones((4, 4), dtype=bool)
    plane = np.zeros((4, 4))
    first_row = plane[0]
    x_host = np.linspace(0.0, 1.0, 10)
    x_d = sim._backend.asarray(x_host)
    ramp = np.linspace(0.0, 1.0, 10)
    times = np.arange(10) * 0.1
    trail = np.zeros(10)
    cells = np.asarray([1.0, 2.0, 3.0])
    shaped = np.ones((10,))
    n_cells = 10
    counted = np.zeros(n_cells)
    rows = np.sin(times)[:, None] * taper
    pulse = np.sin(2.0 * np.pi * 500.0 * times)
    gauss = np.exp(-((times - 0.3) / 0.05) ** 2)
    shape = (4, 4)
    buf = np.zeros(shape)
    bufp = np.zeros(shape_p)
    buf3 = np.zeros((10,) + sim.p.shape)
    bufs = np.zeros([*shape])
    grid0 = np.meshgrid(x_host, ramp)[0]
    xx, yy = np.meshgrid(ramp, ramp)
    ud, vd = xp.meshgrid(x_d, x_d)
    decay = np.exp(-0.01)
    for i in range(10):
        sim.step()
        {line}
"""


def _reasons(line: str) -> list[str]:
    """What the guard says of *line* in the stepping loop of the scene above."""
    found = problems(_ONE_LINE_SCENE.format(line=line), "scene")
    return [entry.split(": ", 1)[1] for entry in found]


@pytest.mark.parametrize(
    "line",
    [
        "count = min(sim.p.shape[0], 5)",
        "middle = round(sim.p.shape[1] / 2)",
        "cells = int(sim.vx.size)",
        "rank = max(sim.vy.ndim, 1)",
        "sim.p *= np.exp(-0.01)",
        "sim.p *= decay",
        "sim.p *= np.cos(2.0 * i)",
        "trail[i] = 1.0; sim.p *= np.cos(2.0 * i)",
        "sim.p *= np.sin(np.pi * 0.25)",
        "sim.vy[3] += np.float64(0.5) * xp.sin(omega * t)",
        "t = times[i]; sim.vy[3] += xp.sin(omega * t - k * x_d)",
        "sim.vy[3] += ramp[i] * xp.sin(omega * t)",
        "sim.vy[3] += ramp[-1] * xp.sin(omega * t)",
        "sim.p *= ramp[i]",
        "sim.p *= np.sin(times[i])",
        "w = times[i]; sim.p *= np.sin(2.0 * w)",
        "sim.p *= np.cos(xp.pi)",
        "sim.p *= np.cos(sim._backend.xp.pi / 4.0)",
        "sim.p *= np.exp(-xp.e) + xp.nan * 0.0",
    ],
)
def test_a_field_s_shape_and_a_numpy_number_are_not_device_arrays(line: str) -> None:
    """A field's shape is a host tuple, and a NumPy number mixes with a device array.

    A NumPy number is one element of a host array picked by an integer, or a
    NumPy function of numbers: constants, the count of a ``for`` over
    ``range``, names bound only to numbers, such elements, and the named
    constants of NumPy, ``math`` and the engine's namespace (``xp.pi``).
    """
    assert _reasons(line) == []


@pytest.mark.parametrize(
    "line",
    [
        "sim.p[0, 0] = ramp[i]",
        "sim.p[0, 0] = trail[3]",
        "sim.p[0, 0] = shaped[-1]",
        "sim.p[0, 0] = cells[i]",
        "sim.p[0, 0] = times[i + 1]",
        "sim.p[0, 0] = np.zeros(len(ramp))[i]",
        "sim.p[0, 0] = 2.0 * taper[i]",
        "sim.p[0, 0] = np.sin(times[i])",
        "sim.p[0, 0] = counted[i]",
        "sim.p[0, 0] = np.zeros(sim.p.shape[0])[i]",
        "v = ramp[i]; sim.p[0, 0] = v",
        "v = times[i]; sim.p *= v",
        "sim.p[2, 3] += pulse[i]",
        "sim.p *= pulse[i]",
        "sim.p[2, 3] += gauss[i]",
        "sim.vy[3] += pulse[i] * xp.sin(omega * t)",
        "sim.vy[3] += xp.asarray(ramp[i])",
        "sim.p *= ud",
        "v0, v1 = ramp, taper; sim.p[0, 0] = v0[i]",
        "t0, t1 = times[0], times[-1]; sim.p *= np.exp(-t0)",
        "a, b = 0.5, 2.0; sim.p *= np.exp(-a)",
        "(a, b), c = (0.5, 2.0), 1.0; sim.p *= np.exp(-b * c)",
    ],
)
def test_an_element_of_a_host_vector_written_into_a_field_is_a_number(
    line: str,
) -> None:
    """A vector by its binding (zeros, ones, arange, linspace, a 1-D literal) and an integer index."""
    assert _reasons(line) == []


@pytest.mark.parametrize(
    "line",
    [
        "sim.p[:, 0] = plane[i]",
        "sim.vx = plane[1]",
        "sim.p[:, 0] = ramp[idx]",
        "sim.p[0] = 2.0 * plane[i]",
        "sim.p[:, 0] = np.sin(plane[i])",
        "sim.p[:, 0] = np.zeros(sim.p.shape)[i]",
        "sim.p[:, 0] = np.ones((4, 4))[i]",
        "row = plane[i]; sim.p[:, 0] = row",
        "row = rows[i]; sim.vy[3, :] = row",
        "s = np.sin(plane[i]); sim.p[:, 0] = s",
        "sim.p[:, 0] = first_row",
        "sim.p *= grid0",
        "sim.p[:, 0] = grid0[i]",
        "sim.p[:, 0] = buf[i]",
        "sim.p[:, 0] = bufp[i]",
        "sim.p[:, 0] = buf3[i]",
        "sim.p[:, 0] = bufs[i]",
        "sim.p *= xx",
        "sim.p[:, 0] = yy[i]",
        "row, col = plane[i], plane[0]; sim.p[:, 0] = row",
        "first, (second, third) = ramp[i], (plane[i], ramp); sim.p[:, 0] = second",
        "u, v = np.gradient(plane); sim.p[:, 0] = u[i]",
    ],
)
def test_a_row_or_a_gather_of_a_host_array_written_into_a_field_is_an_upload(
    line: str,
) -> None:
    """CuPy copies a host value written into a device array quietly, on every turn.

    Only a host array known to be a vector, picked by an integer, is surely
    one number: a row of a matrix and a pick by a parameter that may be an
    array of indexes are arrays.
    """
    assert _reasons(line) == [_HOST_INTO_DEVICE]


@pytest.mark.parametrize(
    "line",
    [
        "env = xp.abs(sim.p) if env is None else xp.maximum(env, xp.abs(sim.p))",
        "if env is None: env = xp.abs(sim.p)",
        "if env is not None: env = xp.maximum(env, xp.abs(sim.p))",
        "if env is not taper: env = xp.abs(sim.p)",
    ],
)
def test_an_identity_test_on_a_device_array_reads_no_value(line: str) -> None:
    """``is`` and ``is not`` compare objects: a lazy start of a running envelope pulls nothing."""
    assert _reasons(line) == []


@pytest.mark.parametrize(
    "line",
    [
        "sim.p *= np.cos(geom.x)",
        "sim.p *= np.exp(-omega)",
        "sim.p *= np.cos(xp.newaxis)",
    ],
)
def test_a_numpy_function_of_what_may_be_an_array_is_a_host_array(line: str) -> None:
    """A parameter or an attribute may hold anything, so a ufunc of one is a host array."""
    assert _reasons(line) == [_HOST_INTO_DEVICE]


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("sim.vy[3] += taper * xp.sin(omega * t)", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.p = sim.p * mask", _HOST_IN_DEVICE_EXPRESSION),
        ("drive = xp.sin(omega * t - k * x_host)", _HOST_IN_DEVICE_EXPRESSION),
        ("inside = sim.p > taper[0:4]", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.vy[3] += ramp[2:5] * xp.sin(omega * t)", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.vy[3] += ramp * xp.sin(omega * t)", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.p += mask[0, 1:3] * sim.vx", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.vy[3] += xp.asarray(rows[i])", _HOST_IN_DEVICE_EXPRESSION),
        ("sim.vy[3] += xp.asarray(rows[i, :])", _HOST_IN_DEVICE_EXPRESSION),
        (
            "src = sim._backend.asarray(rows[i]); sim.vy[3] += src",
            _HOST_IN_DEVICE_EXPRESSION,
        ),
        (
            "row, col = rows[i], rows[0]; sim.vy[3] += xp.asarray(row)",
            _HOST_IN_DEVICE_EXPRESSION,
        ),
        ("trail[i] = ud[0, 0]", _DEVICE_INTO_HOST),
        (
            "level = float(sim.p.max())",
            "float() pulls a device value to the host on every turn",
        ),
        ("trail[i] = sim.p.max()", _DEVICE_INTO_HOST),
        ("trail[i] = xp.abs(sim.p).max()", _DEVICE_INTO_HOST),
        (
            "level = sim.p[1, 2].item()",
            ".item() pulls a device value to the host on every turn",
        ),
        (
            "row = sim.p[0].tolist()",
            ".tolist() pulls a device value to the host on every turn",
        ),
        (
            "loud = bool(xp.any(sim.p > 1.0))",
            "bool() pulls a device value to the host on every turn",
        ),
        ("assert xp.isfinite(sim.p).all()", _TEST_PULL),
    ],
)
def test_a_host_array_in_a_device_expression_and_a_reduction_brought_back_are_seen(
    line: str, reason: str
) -> None:
    assert _reasons(line) == [reason]


def test_a_test_on_a_device_value_is_seen_in_a_branch_and_in_the_loop_itself() -> None:
    source = """
def build(sim, limit):
    while sim.p.max() < limit:
        sim.step()
        if xp.abs(sim.vx).max() > limit:
            break
"""
    reasons = [entry.split(": ", 1)[1] for entry in problems(source, "scene")]
    assert reasons == [_TEST_PULL, _TEST_PULL]


def test_a_name_is_known_however_long_the_chain_that_binds_it() -> None:
    """Five names bound back to front: each pass over the function reaches one more."""
    source = """
def build(sim):
    trail = np.zeros(10)
    for i in range(10):
        sim.step()
        trail[i] = e
        e = d
        d = c
        c = b
        b = a
        a = sim.p
"""
    reasons = [entry.split(": ", 1)[1] for entry in problems(source, "scene")]
    assert reasons == [_DEVICE_INTO_HOST]


#: The engines a figure may build, and the functions that build one; each is
#: told where to step.
_ENGINES = frozenset(
    {
        "FDTD2D",
        "ElasticFDTD2D",
        "fdtd_simulation",
        "elastic_fdtd_simulation",
        "write_fdtd_animation",
        "write_elastic_fdtd_animation",
    }
)
_FIGURE_MODULES = sorted(_FIELDS_DIR.parent.rglob("*.py"))


def unplaced_engines(source: str, label: str) -> list[str]:
    """Every engine *source* builds, or simulation it runs, without ``compute=``.

    Without it an engine follows ``use()`` and ``PHONOMETRY_COMPUTE``: a
    shell set up to render the clips on a GPU would send it there, past the
    registry (with a host in the variable, a static figure's simulation would
    even be sent to the node), and on a node lane it would open a CUDA
    context in a child forked from a parent that already holds one.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = _callee(node)[1]
        if name in _ENGINES and not any(k.arg == "compute" for k in node.keywords):
            found.append(f"{label}:{node.lineno}: {name} without compute=")
    return sorted(found)


@pytest.mark.parametrize(
    "path", _FIGURE_MODULES, ids=lambda p: str(p.relative_to(_FIELDS_DIR.parent))
)
def test_every_engine_a_figure_builds_is_told_where_to_step(path: pathlib.Path) -> None:
    found = unplaced_engines(path.read_text(encoding="utf-8"), path.name)
    assert not found, "\n".join(found)


def test_an_engine_built_without_a_placement_is_seen() -> None:
    source = """
def poster(cp, cs, dx):
    a = FDTD2D(c=343.0, dx=0.01, shape=(3, 8)).dt
    b = fdtd2d.FDTD2D(c=343.0, dx=0.01, shape=(3, 8))
    c = simulation.ElasticFDTD2D(c_p=cp, c_s=cs, dx=dx)
    d = FDTD2D(c=343.0, dx=0.01, shape=(3, 8), compute=Compute()).dt
    e = simulation.fdtd_simulation(run)
    f = simulation.fdtd_simulation(run, compute=Compute())
    g = simulation.write_elastic_fdtd_animation("x.webm", elastic_run)
"""
    assert [line.split(": ", 1)[1] for line in unplaced_engines(source, "scene")] == [
        "FDTD2D without compute=",
        "FDTD2D without compute=",
        "ElasticFDTD2D without compute=",
        "fdtd_simulation without compute=",
        "write_elastic_fdtd_animation without compute=",
    ]
