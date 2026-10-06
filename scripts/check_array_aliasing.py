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
a copy of its own, through ``phonometry._internal.frozen.read_only_copy``.
This reads every function of the package and follows each parameter through
the statements of its body: the numpy calls that may hand back their
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
field by field, and a field the record copies in its own ``__post_init__``
carries nothing. An annotation is read through the package's type aliases,
so ``float | Field2D`` may hold an array when ``Field2D`` is
``NDArray[np.float64]``. Five places are where an array is kept:

* a field of a public dataclass or named tuple, passed to its constructor
  (``cls(...)`` and ``type(self)(...)`` included), when the field is
  annotated as an array or anything that may hold one; a class is public
  when a public module defines it or lists it in ``__all__``;
* ``object.__setattr__(record, name, value)``: in a method of such a record,
  where the value read back from ``self`` in ``__post_init__`` is the
  constructor's argument, so a field normalised with
  ``np.asarray(self.levels)`` keeps the caller's array, and anywhere else on
  a public record, such as a factory patching the record it just built;
* ``dataclasses.replace(record, ...)`` on a record parameter, which keeps
  every array field it is not given;
* an attribute of a plain public class set in any of its methods
  (``self.name = value``, ``self.name.append(value)``, or
  ``self.name[key] = value`` on an attribute annotated as a list or a
  mapping), when the attribute is annotated as an array, or, with no
  annotation of its own, when a parameter the value carries is annotated as
  one or not at all: ``self._distances = distances`` keeps the caller's
  array for every method that hands it out later, and ``self.fs = fs`` with
  ``fs: float`` keeps a number;
* ``read_only(value)`` anywhere.

A private helper is held to the rule whatever its callers pass today: the
next caller may hand it the caller's array. The analysis reads names, not
types, so a scalar that travels the same path as an array is read as one
where the field it lands in could hold an array. :data:`EXEMPT` is the
escape hatch, keyed by file and function, and each entry carries the reason
it is one; an entry that covers nothing fails the check too.

What the check does not read: a record a caller builds by hand holds what it
is given, as a tuple does, and a result that holds a record it was given
whole (``BandPath`` objects in a prediction's ``paths``) holds that record,
not a copy of it; a function that returns the caller's array bare, not
inside a result, is outside the rule; and a value whose path runs through
code outside the package (a callback, a library call it does not know) is
read as a new value.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, python_files, relative

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

#: Where the package lives; the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"

#: Functions that may keep a parameter's array, keyed by file and qualified
#: function, each with the reason.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/phonometry/_report/duct_path.py", "render_duct_path_report"): (
        "the copy made with dataclasses.replace only carries the requirement "
        "onto the fiche being drawn; it is dropped when the page is written and "
        "never reaches the caller"
    ),
    ("src/phonometry/signals/windows.py", "window_metrics"): (
        "keeps the window's specification through _own_window, which hands a "
        "name or a number on as given and an array parameter as a read-only "
        "copy (a list one as a tuple); the check reads the pass-through branch "
        "for the numbers as the caller's array"
    ),
}

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
    fields: list[tuple[str, str]] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)
    #: The fields ``__post_init__`` stores again, each with whether every
    #: value it stores there is a copy: those the record owns, whoever built it.
    owned: dict[str, bool] = field(default_factory=dict)
    #: The same fields, each with whether every value stored there is passed
    #: through ``read_only`` or ``read_only_copy``: a copy nobody can write
    #: into, which a result may share without sharing anyone's edits.
    sealed: dict[str, bool] = field(default_factory=dict)


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
        self.class_by_name: dict[str, list[ClassInfo]] = {}
        self.functions: dict[tuple[str, str], FunctionInfo] = {}
        self.imports: dict[str, dict[str, tuple[str, str | None]]] = {}
        self.numpy_names: dict[str, set[str]] = {}
        self.numpy_functions: dict[str, dict[str, str]] = {}
        self.exported: dict[str, tuple[str, ...]] = {}
        self.typed_cache: dict[tuple[str, str, str], Value] = {}
        #: Type aliases of the package, by name, as their definition reads.
        self.aliases: dict[str, str] = {}
        #: The aliases that stand for an array or for anything that may hold one.
        self.array_aliases: set[str] = set()
        #: The functions whose every return is a mask or an array of positions.
        self.positions: set[tuple[str, str]] = set()
        for path in files:
            module = _module_name(path, root)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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
                resolved = self.resolve(module, name)
                if resolved in self.classes:
                    self.public.add(resolved)

    def _read_module(self, module: str, tree: ast.Module) -> None:
        imports: dict[str, tuple[str, str | None]] = {}
        numpy_names: set[str] = set()
        numpy_functions: dict[str, str] = {}
        package = module if module in self.packages else module.rpartition(".")[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "numpy":
                        numpy_names.add(alias.asname or "numpy")
                    elif _inside(alias.name, self.package) and alias.asname:
                        imports[alias.asname] = (alias.name, None)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package.split(".")
                    base = base[: len(base) - node.level + 1]
                    source = ".".join([*base, node.module] if node.module else base)
                else:
                    source = node.module or ""
                if source.startswith("numpy"):
                    for alias in node.names:
                        numpy_functions[alias.asname or alias.name] = alias.name
                    continue
                if not _inside(source, self.package):
                    continue
                for alias in node.names:
                    local = alias.asname or alias.name
                    if f"{source}.{alias.name}" in self.modules:
                        imports[local] = (f"{source}.{alias.name}", None)
                    else:
                        imports[local] = (source, alias.name)
        self.imports[module] = imports
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
                self.class_by_name.setdefault(node.name, []).append(info)
                self._read_body(module, node.body, qualname, info)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qualname = f"{scope}.{node.name}" if scope else node.name
                kind = "function"
                if owner is not None:
                    kind = "method"
                    for decorator in node.decorator_list:
                        name = _base_name(decorator)
                        if name in {"classmethod", "staticmethod"}:
                            kind = name
                self.functions[(module, qualname)] = FunctionInfo(
                    module, qualname, node, path, owner, kind, nested=nested
                )
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
                self._read_body(module, node.body, qualname, None, nested=True)
            elif isinstance(node, ast.If | ast.Try | ast.With | ast.For | ast.While):
                self._read_body(
                    module, _nested_statements(node), scope, owner, nested=nested
                )

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

    def functions_named(self, module: str) -> set[str]:
        """The bare names *module* binds to functions of the package."""
        names = {q for (m, q) in self.functions if m == module and "." not in q}
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

    def owns(self, info: ClassInfo, name: str) -> bool:
        """Whether a record copies a field itself, in its own or a base's
        ``__post_init__``.
        """
        if info.owned.get(name):
            return True
        for base in info.bases:
            for candidate in self.class_by_name.get(base, []):
                if candidate.record and self.owns(candidate, name):
                    return True
        return False

    def seals(self, info: ClassInfo, name: str) -> bool:
        """Whether a record publishes a field as a read-only copy of its own."""
        if info.sealed.get(name) and self.owns(info, name):
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
        if isinstance(node, ast.If | ast.Try):
            yield from _module_statements(_nested_statements(node))
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


def _nested_statements(node: ast.stmt) -> list[ast.stmt]:
    out: list[ast.stmt] = []
    for name in ("body", "orelse", "finalbody", "handlers"):
        for child in getattr(node, name, []) or []:
            if isinstance(child, ast.ExceptHandler):
                out.extend(child.body)
            else:
                out.append(child)
    return out


def holds_array(annotation: str | None) -> bool:
    """Whether a field so annotated may hold an array."""
    if annotation is None:
        return True
    return any(word in annotation for word in _ARRAY_WORDS)


@dataclass
class Summary:
    """What a function's return value carries of its parameters."""

    value: Value = _CLEAN


class Reader:
    """Follows the parameters of one function through its body."""

    def __init__(
        self,
        tree: Tree,
        function: FunctionInfo,
        summaries: Mapping[tuple[str, str], Summary],
        findings: list[Finding] | None,
        closure: Mapping[str, Value] | None = None,
    ) -> None:
        self.tree = tree
        self.function = function
        self.closure = dict(closure or {})
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
        """Every parameter carries itself; ``self`` and ``cls`` carry nothing."""
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
        env: dict[str, Value] = dict(self.closure)
        for index, name in enumerate(names):
            if index == 0 and self.function.kind in {"method", "classmethod"}:
                env[name] = _CLEAN
                continue
            env[name] = self.typed(name, annotations.get(name))
        if self.post_init and self.function.owner is not None:
            for name, _ in self.tree.record_fields(self.function.owner):
                env[f"self.{name}"] = frozenset({f"self.{name}"})
        return env

    def typed(self, name: str, annotation: ast.expr | None) -> Value:
        """What a parameter carries, read through its annotation.

        A record of the package carries the parameter in each field that can
        hold an array and that the record does not copy for itself; a sequence
        of records carries one such record per item. Anything else carries the
        parameter whole.
        """
        cache = self.tree.typed_cache
        key = (self.function.module, self.function.qualname, name)
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
        """Read the body, report the kept arrays, and return what is returned."""
        self.block(self.function.node.body, self.start())
        return self.returned

    # -- statements ------------------------------------------------------
    def block(
        self, body: Iterable[ast.stmt], env: dict[str, Value]
    ) -> dict[str, Value]:
        for statement in body:
            env = self.statement(statement, env)
        return env

    def statement(self, node: ast.stmt, env: dict[str, Value]) -> dict[str, Value]:  # noqa: C901, PLR0911, PLR0912
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
            inner = self.tree.functions.get(
                (self.module, f"{self.function.qualname}.{node.name}")
            )
            if inner is not None and inner.node is node:
                Reader(self.tree, inner, self.summaries, self.findings, env).run()
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

    def built_record(self, node: ast.expr | None) -> ClassInfo | None:
        """The record class a call builds, if *node* is such a call."""
        if not isinstance(node, ast.Call):
            return None
        func = node.func
        owner = self.function.owner
        if isinstance(func, ast.Name) and func.id == "cls":
            return owner if owner is not None and owner.record else None
        key = self.callee(func)
        info = self.tree.classes.get(key) if key is not None else None
        return info if info is not None and info.record else None

    def callee(self, func: ast.expr) -> tuple[str, str] | None:
        """The function or class of the package a call names, if it names one."""
        if isinstance(func, ast.Name):
            return self.tree.resolve(self.module, func.id)
        if isinstance(func, ast.Attribute):
            target = self.method_target(func)
            if target is not None:
                return target
            module = self.module_of(func.value)
            if module is not None:
                return self.tree.resolve(module, func.attr)
        return None

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
            return self.callee(node.func) in self.tree.positions
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
    def expr(self, node: ast.expr, env: dict[str, Value]) -> Value:  # noqa: C901, PLR0911, PLR0912
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

    def call(self, node: ast.Call, env: dict[str, Value]) -> Value:  # noqa: C901, PLR0911, PLR0912
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
                resolved = self.tree.resolve(module, func.attr)
                if resolved is not None:
                    return self.apply(resolved, node, arguments, keywords, bound=False)
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
            resolved = self.tree.resolve(self.module, name)
            if resolved is not None:
                if name == "read_only" or resolved[1] == "read_only":
                    self.flag(node, "read_only(...)", first)
                    return flat(first)
                return self.apply(resolved, node, arguments, keywords, bound=False)
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
    ) -> Value:
        """What a call to a function or a class of the package returns."""
        if target in self.tree.classes:
            info = self.tree.classes[target]
            if info.record:
                return self.constructor_sink(
                    info, node, arguments, keywords, public=target in self.tree.public
                )
            return _CLEAN
        function = self.tree.functions[target]
        summary = self.summaries.get(target)
        if summary is None or not flat(summary.value):
            return _CLEAN
        mapping = bind(function, arguments, keywords, bound=bound)
        return substitute(summary.value, mapping)

    # -- the places an array is kept --------------------------------------
    def constructor_sink(
        self,
        info: ClassInfo,
        node: ast.Call,
        arguments: list[Value],
        keywords: dict[str | None, Value],
        *,
        public: bool,
    ) -> Value:
        """Report what a record keeps, and return the record as a value."""
        fields = self.tree.record_fields(info)
        annotations = dict(fields)
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

    def replace_sink(
        self, node: ast.Call, arguments: list[Value], keywords: dict[str | None, Value]
    ) -> Value:
        """``dataclasses.replace``: the new record keeps every field not named."""
        if not node.args:
            return _CLEAN
        original = arguments[0]
        info = self.annotated_record(node.args[0])
        if info is not None:
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
        """Whether a record class reaches a caller."""
        return any(self.tree.classes.get(key) is info for key in self.tree.public)

    def setattr_sink(
        self, node: ast.Call, arguments: list[Value], env: dict[str, Value]
    ) -> None:
        owner = self.function.owner
        if len(node.args) < 3:  # noqa: PLR2004
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
            if len(inner.elts) != 2 or not (  # noqa: PLR2004
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
) -> dict[str, Value]:
    """What each parameter of *function* receives from one call."""
    spec = function.node.args
    positional = [a.arg for a in (*spec.posonlyargs, *spec.args)]
    if bound and function.kind in {"method", "classmethod"}:
        positional = positional[1:]
    mapping: dict[str, Value] = {}
    extra: list[Value] = []
    for index, value in enumerate(arguments):
        if index < len(positional):
            mapping[positional[index]] = value
        else:
            extra.append(value)
    if spec.vararg is not None:
        mapping[spec.vararg.arg] = union(_CLEAN, *extra)
    else:
        for value in extra:
            for name in positional:
                mapping[name] = union(mapping.get(name, _CLEAN), value)
    names = set(positional) | {a.arg for a in spec.kwonlyargs}
    spill: list[Value] = []
    unpacked: list[Value] = []
    for keyword, value in keywords.items():
        if keyword is None:
            unpacked.append(value)
        elif keyword in names:
            mapping[keyword] = value
        else:
            spill.append(value)
    # ``**options`` can only reach the parameters nothing else has filled.
    for value in unpacked:
        for parameter in names - set(mapping):
            mapping[parameter] = flat(value)
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
    empty = {key: Summary() for key in tree.functions}
    for _ in range(20):
        found: set[tuple[str, str]] = set()
        for key, function in tree.functions.items():
            if function.nested:
                continue
            reader = Reader(tree, function, empty, None)
            reader.run()
            if reader.index_returns and all(reader.index_returns):
                found.add(key)
        if found == tree.positions:
            break
        tree.positions = found
    # What the pass above learnt of the records' own copies was read without
    # the summaries; it is read again on them.
    for info in tree.classes.values():
        info.owned.clear()
        info.sealed.clear()
    tree.typed_cache.clear()


def summarise(tree: Tree) -> dict[tuple[str, str], Summary]:
    """What each function's return carries of its parameters, to a fixed point."""
    summaries = {key: Summary() for key in tree.functions}
    for _ in range(20):
        changed = False
        for key, function in tree.functions.items():
            if function.nested:
                continue
            value = Reader(tree, function, summaries, None).run()
            grown = union(summaries[key].value, value)
            if grown != summaries[key].value:
                summaries[key] = Summary(grown)
                changed = True
        if not changed:
            break
    return summaries


def findings_in(
    files: Sequence[pathlib.Path], root: pathlib.Path = SOURCE
) -> list[Finding]:
    """Every place a function keeps an array it was handed without a copy."""
    tree = Tree(files, root)
    find_positions(tree)
    summaries = summarise(tree)
    # What each record's ``__post_init__`` copies, read once more on the
    # final summaries so that a factory is not held to a copy the record
    # already makes.
    for info in tree.classes.values():
        info.owned.clear()
        info.sealed.clear()
    for function in tree.functions.values():
        if function.node.name == "__post_init__":
            Reader(tree, function, summaries, None).run()
    tree.typed_cache.clear()
    found: list[Finding] = []
    for function in tree.functions.values():
        if not function.nested:
            Reader(tree, function, summaries, found).run()
    return sorted(set(found), key=lambda f: (f.path, f.line, f.sink))


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
    found, stale = exempted(findings_in(files, root), EXEMPT)
    if not found and not stale:
        print("Every array a result keeps is a copy of its own.")
        return 0
    if found:
        print("::error::a result keeps an array it was handed, not a copy of it")
        for finding in found:
            print(
                f"  {finding.path}:{finding.line}: {finding.function}: {finding.sink} "
                f"<- {', '.join(finding.parameters)}"
            )
        print(
            "  -> store read_only_copy(value) from phonometry._internal.frozen (a "
            "copy of its own, read only); "
            "a function that has to keep the caller's array goes in EXEMPT at the "
            "top of scripts/check_array_aliasing.py with its reason."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which keeps no array any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
