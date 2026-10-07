#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Find the result fields the library fills with a verdict it has just reached.

A field typed ``bool`` or named like a flag is easy to spot from the class
alone. A per-band mask annotated ``np.ndarray``, a class label held as a
string or an enum member are not: what makes them a verdict is where their
value comes from. This module reads the source of every public module and
follows each argument of a call that builds a public dataclass back to what
produced it. A field is reported when the value it is given is

* an ordering comparison (``margin < LIMIT``, ``a >= b``), or a combination of
  them (``and``/``or``/``not``, ``&``/``|``/``~``, ``np.all``, ``np.any``,
  ``np.asarray``, ``bool`` and the like), reached through local names, tuple
  unpacking, comprehensions and the module-level helpers of the package that
  return one; or
* a label (a string, a bool, an enum member, a string constant of the module)
  chosen by such a comparison: ``"a" if x < LIMIT else "b"``, ``np.where`` over
  a comparison between two labels, or a helper whose ``return`` of a label sits
  under an ``if`` on one.

What it cannot see is a verdict that reaches the constructor through
``**kwargs``, through :func:`dataclasses.replace`, through ``cls(...)`` or
``type(self)(...)``, or through a helper of another package; and a comparison
of equality, which is how a fact is checked rather than how a limit is judged.
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import functools
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from types import ModuleType

#: Packages whose dataclasses are rendering and validation helpers, not results.
PRIVATE_PACKAGES = ("phonometry._internal", "phonometry._plot", "phonometry._report")

_ORDER = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)

#: Calls whose value is the verdict of their arguments, or of their receiver.
_PASS_THROUGH = frozenset(
    {
        "all",
        "any",
        "array",
        "asarray",
        "ascontiguousarray",
        "astype",
        "bool",
        "bool_",
        "broadcast_to",
        "copy",
        "dict",
        "frozenset",
        "fromiter",
        "list",
        "logical_and",
        "logical_not",
        "logical_or",
        "logical_xor",
        "MappingProxyType",
        "read_only",
        "read_only_copy",
        "tuple",
    }
)

#: Methods that add their argument to the container they are called on.
_APPEND = frozenset({"add", "append", "appendleft", "extend", "insert"})

#: How deep a value is followed before the trace gives up on it.
_DEPTH = 8


@dataclasses.dataclass(frozen=True)
class _Unpacked:
    """The ``index``-th item of a tuple unpacked from ``value``."""

    value: ast.AST
    index: int


type _Local = Mapping[str, tuple[object, ...]]


@functools.cache
def _module_tree(name: str) -> ast.Module:
    module = importlib.import_module(name)
    return ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))


@functools.cache
def _functions(name: str) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node
        for node in _module_tree(name).body
        if isinstance(node, ast.FunctionDef)
    }


def _bind_loop(
    node: ast.For | ast.comprehension, bind: Callable[[ast.AST, object], None]
) -> None:
    iterable = node.iter
    if (
        isinstance(iterable, ast.Call)
        and isinstance(iterable.func, ast.Name)
        and iterable.func.id == "zip"
        and isinstance(node.target, ast.Tuple)
    ):
        for item, source in zip(node.target.elts, iterable.args, strict=False):
            bind(item, source)
    elif isinstance(node.target, ast.Name):
        bind(node.target, iterable)


@functools.cache
def _locals(func: ast.AST) -> dict[str, tuple[object, ...]]:
    """Every value each local name of *func* is bound to, anywhere in its body."""
    out: dict[str, list[object]] = {}

    def bind(target: ast.AST, value: object) -> None:
        if isinstance(target, ast.Name):
            out.setdefault(target.id, []).append(value)
        elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, ast.AST):
            for index, item in enumerate(target.elts):
                bind(item, _Unpacked(value, index))

    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                bind(target, node.value)
        elif (
            isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None
        ):
            bind(node.target, node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(
            node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)
        ):
            bind(node.target, ast.BinOp(left=node.target, op=node.op, right=node.value))
        elif isinstance(node, (ast.For, ast.comprehension)):
            _bind_loop(node, bind)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _APPEND
            and isinstance(node.func.value, ast.Name)
        ):
            for arg in node.args:
                bind(node.func.value, ast.List(elts=[arg]))
    return {name: tuple(values) for name, values in out.items()}


def _is_dtype(expr: ast.AST) -> bool:
    return isinstance(expr, (ast.Name, ast.Attribute)) and (
        getattr(expr, "id", None) in {"bool", "float", "int"}
        or getattr(expr, "attr", None) in {"bool_", "float64", "int64"}
    )


class _Tracer:
    """Whether an expression of one module is a verdict: a comparison, or a label one chose."""

    def __init__(self, module: ModuleType) -> None:
        self.namespace = vars(module)

    def label(self, expr: object) -> bool:
        """Whether *expr* is a label: a string or bool, a module string, an enum member."""
        if isinstance(expr, ast.Constant):
            return isinstance(expr.value, (str, bool))
        if isinstance(expr, ast.Name):
            return isinstance(self.namespace.get(expr.id), str)
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            owner = self.namespace.get(expr.value.id)
            return isinstance(owner, type) and issubclass(owner, enum.Enum)
        return False

    def verdict(
        self, expr: object, local: _Local, seen: frozenset[str], depth: int = 0
    ) -> bool:
        """Whether *expr*, read through *local*, is a verdict."""
        if depth > _DEPTH:
            return False
        if isinstance(expr, _Unpacked):
            return self._unpacked(expr, local, seen, depth)
        if isinstance(expr, ast.Compare):
            return any(isinstance(op, _ORDER) for op in expr.ops)
        if isinstance(expr, ast.IfExp):
            return self._choice(expr, local, seen, depth)
        if isinstance(expr, ast.Name):
            return self._name(expr, local, seen, depth)
        if isinstance(expr, ast.Call):
            return self._call(expr, local, seen, depth)
        return any(self.verdict(part, local, seen, depth + 1) for part in _parts(expr))

    def _name(
        self, expr: ast.Name, local: _Local, seen: frozenset[str], depth: int
    ) -> bool:
        key = f"{id(local)}:{expr.id}"
        if key in seen:
            return False
        return any(
            self.verdict(value, local, seen | {key}, depth + 1)
            for value in local.get(expr.id, ())
        )

    def _call(
        self, expr: ast.Call, local: _Local, seen: frozenset[str], depth: int
    ) -> bool:
        func = expr.func
        name = (
            func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        )
        if name == "where" and len(expr.args) == 3:  # noqa: PLR2004 - np.where(c, a, b)
            return (
                self.label(expr.args[1])
                and self.label(expr.args[2])
                and self.verdict(expr.args[0], local, seen, depth + 1)
            )
        if name in _PASS_THROUGH:
            parts = [*expr.args, *(k.value for k in expr.keywords)]
            if isinstance(func, ast.Attribute):
                parts.append(func.value)
            return any(
                self.verdict(part, local, seen, depth + 1)
                for part in parts
                if not _is_dtype(part)
            )
        target = self._function(func)
        if target is None or target[1].name in seen:
            return False
        return _Tracer(target[0]).returns_verdict(
            target[1], seen | {target[1].name}, depth + 1
        )

    def _choice(
        self, expr: ast.IfExp, local: _Local, seen: frozenset[str], depth: int
    ) -> bool:
        # A label chosen by a verdict: ``"a" if x < LIMIT else "b"``, nested.
        if not all(self._labels_only(b) for b in (expr.body, expr.orelse)):
            return False
        return self.verdict(expr.test, local, seen, depth + 1) or any(
            isinstance(b, ast.IfExp) and self._choice(b, local, seen, depth + 1)
            for b in (expr.body, expr.orelse)
        )

    def _labels_only(self, expr: object) -> bool:
        if isinstance(expr, ast.IfExp):
            return all(self._labels_only(b) for b in (expr.body, expr.orelse))
        return self.label(expr)

    def _function(self, func: ast.AST) -> tuple[ModuleType, ast.FunctionDef] | None:
        if not isinstance(func, ast.Name):
            return None
        obj = self.namespace.get(func.id)
        if not inspect.isfunction(obj) or not obj.__module__.startswith("phonometry"):
            return None
        node = _functions(obj.__module__).get(obj.__name__)
        if node is None:
            return None
        return importlib.import_module(obj.__module__), node

    def _unpacked(
        self, item: _Unpacked, local: _Local, seen: frozenset[str], depth: int
    ) -> bool:
        value = item.value
        if isinstance(value, ast.Tuple) and item.index < len(value.elts):
            return self.verdict(value.elts[item.index], local, seen, depth + 1)
        if not isinstance(value, ast.Call):
            return False
        target = self._function(value.func)
        if target is None or target[1].name in seen:
            return False
        tracer = _Tracer(target[0])
        inner = _locals(target[1])
        return any(
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Tuple)
            and item.index < len(node.value.elts)
            and tracer.verdict(
                node.value.elts[item.index],
                inner,
                seen | {target[1].name},
                depth + 1,
            )
            for node in ast.walk(target[1])
        )

    def returns_verdict(
        self, func: ast.FunctionDef, seen: frozenset[str], depth: int
    ) -> bool:
        """Whether *func* returns a verdict, or a label chosen under an ``if`` on one."""
        local = _locals(func)
        for node in ast.walk(func):
            if (
                isinstance(node, ast.If)
                and self.verdict(node.test, local, seen, depth + 1)
                and self._labels_under(node)
            ):
                return True
            if (
                isinstance(node, ast.Return)
                and node.value is not None
                and not isinstance(node.value, ast.Tuple)
                and self.verdict(node.value, local, seen, depth + 1)
            ):
                return True
        return False

    def _labels_under(self, branch: ast.If) -> bool:
        for inner in ast.walk(branch):
            if (
                isinstance(inner, ast.Return)
                and inner.value is not None
                and self.label(inner.value)
            ):
                return True
            if (
                isinstance(inner, ast.Assign)
                and self.label(inner.value)
                and any(isinstance(t, ast.Subscript) for t in inner.targets)
            ):
                return True
        return False


def _parts(expr: object) -> list[object]:
    """The sub-expressions whose verdict is the verdict of *expr*."""
    if isinstance(expr, ast.BoolOp):
        return list(expr.values)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, (ast.Not, ast.Invert)):
        return [expr.operand]
    if isinstance(expr, ast.BinOp) and isinstance(
        expr.op, (ast.BitAnd, ast.BitOr, ast.BitXor)
    ):
        return [expr.left, expr.right]
    if isinstance(expr, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        return [expr.elt]
    if isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
        return list(expr.elts)
    if isinstance(expr, ast.Dict):
        return [v for v in expr.values if v is not None]
    return []


def _built_class(call: ast.Call, namespace: Mapping[str, object]) -> type | None:
    """The public result dataclass *call* builds, or ``None``."""
    if not isinstance(call.func, ast.Name):
        return None
    cls = namespace.get(call.func.id)
    if not (
        isinstance(cls, type)
        and dataclasses.is_dataclass(cls)
        and not cls.__name__.startswith("_")
        and not cls.__module__.startswith(PRIVATE_PACKAGES)
    ):
        return None
    return cls


def module_verdict_fields(name: str) -> dict[str, str]:
    """The fields module *name* fills with a verdict, each with where.

    :param name: An importable module name.
    :return: ``{"module.Class.field": "module:line"}`` for every field a call
        in the module gives a verdict to.
    """
    module = importlib.import_module(name)
    tracer = _Tracer(module)
    namespace = vars(module)
    found: dict[str, str] = {}
    for func in ast.walk(_module_tree(name)):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        local = _locals(func)
        chosen: set[int] = set()
        for node in ast.walk(func):
            if isinstance(node, ast.If) and tracer.verdict(
                node.test, local, frozenset()
            ):
                chosen.update(id(inner) for inner in ast.walk(node))
        for call in ast.walk(func):
            if not isinstance(call, ast.Call):
                continue
            cls = _built_class(call, namespace)
            if cls is None:
                continue
            names = [f.name for f in dataclasses.fields(cls) if f.init]
            pairs = list(zip(names, call.args, strict=False))
            pairs += [(k.arg, k.value) for k in call.keywords if k.arg]
            for field, value in pairs:
                if tracer.verdict(value, local, frozenset()) or (
                    id(call) in chosen and tracer.label(value)
                ):
                    key = f"{cls.__module__}.{cls.__qualname__}.{field}"
                    found.setdefault(key, f"{name}:{call.lineno}")
    return found


def verdict_fields(package: ModuleType) -> dict[str, str]:
    """The fields every module of *package* fills with a verdict, each with where.

    :param package: The package to walk, ``phonometry``.
    :return: ``{"module.Class.field": "module:line"}``.
    """
    names: Iterable[str] = (
        info.name
        for info in pkgutil.walk_packages(package.__path__, f"{package.__name__}.")
    )
    found: dict[str, str] = {}
    for name in names:
        for key, where in module_verdict_fields(name).items():
            found.setdefault(key, where)
    return found
