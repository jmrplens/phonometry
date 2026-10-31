#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a return whose type one argument decides, annotated as a union.

A multi-panel ``.plot()`` draws one panel on the axes a caller hands it and
returns that axes, and without one it makes a column of panels and returns
them all: the caller's ``ax`` decides which. Annotated ``Axes | tuple[Axes,
Axes]`` and nothing more, the return makes every typed caller narrow a value
whose type the call already fixed, and ``result.plot(ax=ax).set_title(...)``
is a type error for a call that cannot return anything but an ``Axes``. The
remedy is a pair of ``typing.overload`` heads, one per value of the argument
that decides, each with the one type it returns; the union stays on the
implementation, which a caller never sees.

The rule, read from the source of every function of the package, private
ones included, because a public method returns what its renderer returns:

* a return annotation that is a union of an axes class (a matplotlib or
  ``mpl_toolkits`` class whose name ends in ``Axes``, ``PolarAxes`` among
  them, or ``Axes3D``) with several axes (a ``tuple``, a ``list`` or a
  ``Sequence`` of them, or a numpy array) is allowed on an implementation
  only when overloads stand before it, and never on an overload head, which
  states one case;
* a function that reaches a polar axes, by making one (``projection="polar"``
  in a call or in a ``subplot_kw`` mapping, ``polar=True``, or either of them
  computed, which may be polar), by calling a
  function of the package whose return names ``PolarAxes``, or by calling
  one that reaches a polar axes itself, down any depth, is overloaded on the
  argument that decides the projection, one of its heads returning
  ``PolarAxes``, or says ``PolarAxes`` in its return: a plain ``Axes``, an
  ``Any``, or a tuple, list or ``Sequence`` of axes none of which is
  ``PolarAxes`` is refused.

Annotations are read through the package's type aliases (``type X = ...``,
``X: TypeAlias = ...``, and an assignment whose value is a subscript, a
``|`` union, a dotted name, or a bare name that stands for a class or for
another alias), and a name is followed through the imports that bring it
in, so an alias of an alias, or an axes class imported under another name,
is read for what it is. A name handed to ``projection=``, ``polar=``,
``subplot_kw=`` or a ``**`` mapping, when the function does not bind it
itself, is read through the module constant it names, in its own module or
imported from another. A call is followed through the imports of its module
and of its own function, through ``self`` and ``cls`` to the class's own
methods, and through an imported module to its functions, and a name a
module only re-exports is followed to the module that defines it. A method
called on any other object (``result.plot()``) is not followed: the source
does not say which class the object is.

:data:`EXEMPT` is the escape hatch, keyed by file and qualified function,
each entry with its reason. An overload head's key adds, in parentheses, the
parameters that tell it from the other heads, as they are annotated there
(``plot (overload ax: None)``), so that excusing one head excuses neither the
others nor the implementation. An entry that covers nothing fails the check
too.

Static and dependency-free, so it runs on its own.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, python_files, relative

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

#: Where the package lives; the default when no path is given.
SOURCE = ROOT / "src" / "phonometry"

#: Returns a caller's argument does not decide, keyed by file and qualified
#: function (an overload head's as :func:`head_key` writes it), each with the
#: reason.
EXEMPT: dict[tuple[str, str], str] = {
    (
        "src/phonometry/psychoacoustics/loudness/zwicker.py",
        "ZwickerLoudness.plot (overload ax: None)",
    ): (
        "without ax the panels follow the data, not an argument: a "
        "time-varying result draws loudness against time below the specific "
        "loudness and returns both axes, a stationary one returns its one "
        "axes; the head for a given ax returns that Axes"
    ),
    (
        "src/phonometry/_plot/psychoacoustics.py",
        "plot_zwicker_loudness (overload ax: None)",
    ): (
        "the renderer of ZwickerLoudness.plot, whose panel count without ax "
        "the data decide (see its entry)"
    ),
    ("src/phonometry/_plot/electroacoustics.py", "_plot_one_quantity"): (
        "draws one panel of either the loudspeaker or the microphone "
        "vocabulary, and the projection comes from the row of the table it "
        "is handed, not from an argument of its own; its two callers are "
        "overloaded on their quantity Literal and return PolarAxes for "
        "'directivity'"
    ),
}

#: The modules an axes class comes from.
_AXES_PACKAGES = ("matplotlib.", "mpl_toolkits.")

#: The name of an axes class: one that ends in ``Axes`` (``PolarAxes``,
#: ``HostAxes``), or ``Axes3D``; ``AxesImage`` and ``AxesWidget`` are not.
_AXES_NAME = re.compile(r"Axes(?:3D)?$")

#: What ``Any`` is spelled with.
_ANY = frozenset({"typing.Any", "typing_extensions.Any"})

#: The keywords whose value says whether a new axes is polar.
_PROJECTION_KEYWORDS = frozenset({"projection", "polar"})

#: The keywords whose value is a mapping that may say so (``None`` is ``**``).
_MAPPING_KEYWORDS = frozenset({"subplot_kw", None})

#: The containers that hold several axes.
_SEVERAL = frozenset(
    {
        "builtins.tuple",
        "builtins.list",
        "typing.Tuple",
        "typing.List",
        "typing.Sequence",
        "collections.abc.Sequence",
    }
)

#: The numpy arrays, of any dtype, that hold several axes.
_ARRAYS = frozenset({"numpy.ndarray", "numpy.typing.NDArray"})

#: What a union is spelled with besides ``|``.
_UNIONS = frozenset({"typing.Union", "typing.Optional"})

#: The decorator that makes a definition an overload head.
_OVERLOAD = frozenset({"typing.overload", "typing_extensions.overload"})


@dataclass(frozen=True)
class Finding:
    """A function whose return one argument decides, written as one type."""

    path: str
    line: int
    function: str
    sink: str

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the qualified function."""
        return self.path, self.function


@dataclass
class Function:
    """One function of the package: its implementation and its overload heads."""

    module: str
    qualname: str
    owner: str | None
    implementation: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    heads: list[ast.FunctionDef | ast.AsyncFunctionDef] = field(default_factory=list)

    @property
    def definitions(self) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        """The heads first, then the implementation."""
        tail = [self.implementation] if self.implementation is not None else []
        return [*self.heads, *tail]


def _module_name(path: pathlib.Path, root: pathlib.Path) -> str:
    parts = list(path.relative_to(root.parent).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(
    nodes: Iterable[ast.AST], package: str, *, into: dict[str, str]
) -> dict[str, str]:
    """What each imported name stands for, as a dotted path."""
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    into[alias.asname] = alias.name
                else:
                    head = alias.name.split(".")[0]
                    into[head] = head
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                base = base[: len(base) - node.level + 1]
                source = ".".join([*base, node.module] if node.module else base)
            else:
                source = node.module or ""
            for alias in node.names:
                into[alias.asname or alias.name] = f"{source}.{alias.name}"
    return into


def _alias(node: ast.stmt) -> tuple[str, ast.expr] | None:
    """The name and the value of a type alias a statement may define.

    A bare name on the right (``Panel = Axes``) is only a candidate: the
    package keeps it when the name stands for a class or another alias.
    """
    if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
        return node.name.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
        and ast.unparse(node.annotation).rpartition(".")[2] == "TypeAlias"
    ):
        return node.target.id, node.value
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Subscript | ast.BinOp | ast.Attribute | ast.Name)
        and (
            not isinstance(node.value, ast.BinOp)
            or isinstance(node.value.op, ast.BitOr)
        )
    ):
        return node.targets[0].id, node.value
    return None


def _statements(body: Iterable[ast.stmt]) -> Iterator[ast.stmt]:
    """The statements of a body, the branches of its ``if`` and ``try`` blocks read through."""
    for node in body:
        if isinstance(node, ast.If | ast.Try | ast.With):
            nested: list[ast.stmt] = []
            for name in ("body", "orelse", "finalbody"):
                nested.extend(getattr(node, name, []) or [])
            for handler in getattr(node, "handlers", []) or []:
                nested.extend(handler.body)
            yield from _statements(nested)
        else:
            yield node


def _assigned(node: ast.stmt) -> tuple[str, ast.expr] | None:
    """The name and the value a module-level assignment binds, if it binds one."""
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return node.target.id, node.value
    return None


def _parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, ast.arg]:
    """Every parameter of a definition, by name, in the order written."""
    arguments = node.args
    every = [*arguments.posonlyargs, *arguments.args]
    if arguments.vararg is not None:
        every.append(arguments.vararg)
    every.extend(arguments.kwonlyargs)
    if arguments.kwarg is not None:
        every.append(arguments.kwarg)
    return {parameter.arg: parameter for parameter in every}


def _annotation(parameter: ast.arg | None) -> str | None:
    if parameter is None or parameter.annotation is None:
        return None
    return ast.unparse(parameter.annotation)


def head_key(
    qualname: str,
    head: ast.FunctionDef | ast.AsyncFunctionDef,
    heads: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
) -> str:
    """The key of an overload head: its function, and what tells it from the others.

    The parameters a head annotates otherwise than one of its siblings (or
    that a sibling lacks) are the ones that decide which head a call takes,
    so they name the head: ``plot (overload ax: None)``.
    """
    siblings = [_parameters(other) for other in heads]
    own = _parameters(head)
    deciding = [
        f"{name}: {_annotation(parameter)}"
        if parameter.annotation is not None
        else name
        for name, parameter in own.items()
        if len({_annotation(parameters.get(name)) for parameters in siblings}) > 1
    ]
    return f"{qualname} (overload {', '.join(deciding)})".replace(" )", ")")


def _entries(node: ast.AST) -> list[tuple[str | None, ast.expr]]:
    """The keyword arguments of a call, or the entries of a dict literal, by name.

    ``None`` names a ``**`` spread; a dict key that is not a text is left out.
    """
    if isinstance(node, ast.keyword):
        return [(node.arg, node.value)]
    if not isinstance(node, ast.Dict):
        return []
    entries: list[tuple[str | None, ast.expr]] = []
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None:
            entries.append((None, value))
        elif isinstance(key, ast.Constant) and isinstance(key.value, str):
            entries.append((key.value, value))
    return entries


def _bound(node: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[str]:
    """The names a function binds itself: its parameters, and what it assigns."""
    names = {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store | ast.Del)
    }
    names.update(child.arg for child in ast.walk(node) if isinstance(child, ast.arg))
    return frozenset(names)


class Package:
    """Every function of the package, its aliases, and how its names resolve."""

    def __init__(self, files: Sequence[pathlib.Path], root: pathlib.Path) -> None:
        self.paths: dict[str, str] = {}
        self.trees: dict[str, ast.Module] = {}
        self.imports: dict[str, dict[str, str]] = {}
        #: Every name a module defines at its top level.
        self.defined: dict[str, set[str]] = {}
        #: Type aliases, by their dotted name, with the module that reads them.
        self.aliases: dict[str, tuple[str, ast.expr]] = {}
        #: Module-level assignments, by their dotted name, with their module.
        self.constants: dict[str, tuple[str, ast.expr]] = {}
        #: Every class a module defines at its top level, by its dotted name.
        self.classes: set[str] = set()
        #: Every function, by its dotted name.
        self.functions: dict[str, Function] = {}
        #: The imports a function makes in its own body.
        self.local_imports: dict[ast.AST, dict[str, str]] = {}
        for path in files:
            module = _module_name(path, root)
            self.paths[module] = relative(path)
            self.trees[module] = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
        candidates: dict[str, tuple[str, ast.expr]] = {}
        for module, tree in self.trees.items():
            package = (
                module
                if self.paths[module].endswith("__init__.py")
                else module.rpartition(".")[0]
            )
            self.imports[module] = _imports(_statements(tree.body), package, into={})
            self.defined[module] = set()
            for node in _statements(tree.body):
                assigned = _assigned(node)
                if assigned is not None:
                    self.constants[f"{module}.{assigned[0]}"] = (module, assigned[1])
                    self.defined[module].add(assigned[0])
                found = _alias(node)
                if found is not None:
                    into = (
                        candidates if isinstance(found[1], ast.Name) else self.aliases
                    )
                    into[f"{module}.{found[0]}"] = (module, found[1])
                    self.defined[module].add(found[0])
                elif isinstance(
                    node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
                ):
                    self.defined[module].add(node.name)
                    if isinstance(node, ast.ClassDef):
                        self.classes.add(f"{module}.{node.name}")
            self._read_body(module, package, tree.body, "", None)
        self._keep_type_names(candidates)

    def _keep_type_names(self, candidates: dict[str, tuple[str, ast.expr]]) -> None:
        """Keep, as aliases, the bare names that stand for a class or an alias."""
        changed = True
        while changed:
            changed = False
            for dotted, (module, value) in list(candidates.items()):
                if self._names_a_type(module, value):
                    self.aliases[dotted] = candidates.pop(dotted)
                    changed = True

    def _names_a_type(self, module: str, value: ast.expr) -> bool:
        """Whether a name stands for a class or an alias, as far as the source says.

        A builtin is a type when Python says so, and a name of the package
        when it is a class or an alias there; a name imported from outside
        the package (``Axes``) is taken for a type, since only a type is
        worth an alias in an annotation.
        """
        target = self.resolve(module, value)
        if target is None:
            return False
        home, _, name = target.rpartition(".")
        if home == "builtins":
            return isinstance(getattr(builtins, name, None), type)
        if home in self.trees:
            return target in self.aliases or target in self.classes
        return True

    def _read_body(
        self,
        module: str,
        package: str,
        body: Iterable[ast.stmt],
        scope: str,
        owner: str | None,
    ) -> None:
        for node in _statements(body):
            if isinstance(node, ast.ClassDef):
                inner = f"{scope}.{node.name}" if scope else node.name
                self._read_body(module, package, node.body, inner, inner)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qualname = f"{scope}.{node.name}" if scope else node.name
                function = self.functions.setdefault(
                    f"{module}.{qualname}", Function(module, qualname, owner)
                )
                if self.overload(module, node):
                    function.heads.append(node)
                else:
                    function.implementation = node
                self.local_imports[node] = _imports(ast.walk(node), package, into={})
                self._read_body(module, package, node.body, qualname, None)

    def overload(
        self, module: str, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        """Whether a definition is an overload head."""
        return any(
            self.resolve(module, decorator) in _OVERLOAD
            for decorator in node.decorator_list
        )

    def resolve(
        self, module: str, node: ast.expr, local: dict[str, str] | None = None
    ) -> str | None:
        """The dotted path a name or an attribute chain stands for."""
        if isinstance(node, ast.Name):
            if local and node.id in local:
                return self.canonical(local[node.id])
            if node.id in self.defined.get(module, ()):
                return f"{module}.{node.id}"
            if node.id in self.imports.get(module, {}):
                return self.canonical(self.imports[module][node.id])
            if hasattr(builtins, node.id):
                return f"builtins.{node.id}"
            return None
        if isinstance(node, ast.Attribute):
            base = self.resolve(module, node.value, local)
            return self.canonical(f"{base}.{node.attr}") if base else None
        return None

    def canonical(self, dotted: str, depth: int = 0) -> str:
        """A re-exported name followed to the module that defines it."""
        module, _, name = dotted.rpartition(".")
        if depth > 8 or module not in self.trees or name in self.defined[module]:
            return dotted
        target = self.imports[module].get(name)
        return dotted if target is None else self.canonical(target, depth + 1)

    def members(
        self, module: str, node: ast.expr | None, seen: frozenset[str] = frozenset()
    ) -> list[tuple[str, ast.expr]]:
        """The members of a union, each with the module that reads it, aliases expanded."""
        if node is None:
            return []
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                parsed = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return [(module, node)]
            return self.members(module, parsed, seen)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return [
                *self.members(module, node.left, seen),
                *self.members(module, node.right, seen),
            ]
        if (
            isinstance(node, ast.Subscript)
            and self.resolve(module, node.value) in _UNIONS
        ):
            items = (
                node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            )
            return [m for item in items for m in self.members(module, item, seen)]
        dotted = self.resolve(module, node)
        if dotted in self.aliases and dotted not in seen:
            where, value = self.aliases[dotted]
            return self.members(where, value, seen | {dotted})
        return [(module, node)]

    def axes(self, module: str, node: ast.expr) -> str | None:
        """The axes class a member names, as its dotted path, if it is one."""
        dotted = self.resolve(module, node)
        if (
            dotted is not None
            and dotted.startswith(_AXES_PACKAGES)
            and _AXES_NAME.search(dotted.rpartition(".")[2])
        ):
            return dotted
        return None

    def held_axes(self, module: str, node: ast.expr) -> list[str]:
        """The axes classes a ``tuple``, ``list`` or ``Sequence`` member holds."""
        if not (
            isinstance(node, ast.Subscript)
            and self.resolve(module, node.value) in _SEVERAL
        ):
            return []
        items = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        return [
            name
            for item in items
            for where, member in self.members(module, item)
            if (name := self.axes(where, member)) is not None
        ]

    def several_axes(self, module: str, node: ast.expr) -> bool:
        """Whether a member holds several axes: a container of them, or an array."""
        base = node.value if isinstance(node, ast.Subscript) else node
        return self.resolve(module, base) in _ARRAYS or bool(
            self.held_axes(module, node)
        )

    def hides_polar(self, module: str, node: ast.expr | None) -> bool:
        """Whether the return of a function that reaches a polar axes leaves it unsaid.

        A plain axes class, an ``Any``, or a container of axes none of which
        is ``PolarAxes`` leaves it unsaid; ``None``, a figure, an array, or a
        container with a ``PolarAxes`` among its panels does not.
        """
        for where, member in self.members(module, node):
            if self.resolve(where, member) in _ANY:
                return True
            name = self.axes(where, member)
            if name is not None and not _is_polar(name):
                return True
            held = self.held_axes(where, member)
            if held and not any(_is_polar(axes) for axes in held):
                return True
        return False

    def decided(
        self, module: str, node: ast.expr | None
    ) -> tuple[list[str], list[str]]:
        """The axes classes, and the members holding several, of a return annotation."""
        single: list[str] = []
        several: list[str] = []
        for where, member in self.members(module, node):
            name = self.axes(where, member)
            if name is not None:
                single.append(name)
            elif self.several_axes(where, member):
                several.append(ast.unparse(member))
        return single, several

    def callees(self, function: Function) -> Iterator[str]:
        """The functions of the package a function's implementation calls."""
        node = function.implementation
        if node is None:
            return
        local = self.local_imports.get(node, {})
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            target: str | None = None
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in {"self", "cls"}
                and function.owner is not None
            ):
                target = f"{function.module}.{function.owner}.{func.attr}"
            else:
                target = self.resolve(function.module, func, local)
            if target is not None and target in self.functions:
                yield target

    def makes_polar(self, function: Function) -> bool:
        """Whether a function's implementation makes a polar axes itself, or may."""
        node = function.implementation
        if node is None:
            return False
        local = self.local_imports.get(node, {})
        bound = _bound(node) - set(local)
        return self._asks_polar(function.module, node, local, bound, frozenset())

    def _asks_polar(
        self,
        module: str,
        node: ast.AST,
        local: dict[str, str],
        bound: frozenset[str],
        seen: frozenset[str],
    ) -> bool:
        """Whether code asks matplotlib for a polar axes, or may."""
        return any(
            self._entry_asks_polar(module, name, value, local, bound, seen)
            for child in ast.walk(node)
            for name, value in _entries(child)
        )

    def _entry_asks_polar(
        self,
        module: str,
        name: str | None,
        value: ast.expr,
        local: dict[str, str],
        bound: frozenset[str],
        seen: frozenset[str],
    ) -> bool:
        """Whether one keyword argument, or one dict entry, may ask for polar."""
        if name in _PROJECTION_KEYWORDS:
            return self._polar_value(
                module, value, local, bound, seen, flag=name == "polar"
            )
        if name not in _MAPPING_KEYWORDS:
            return False
        found = self._constant(module, value, local, bound, seen)
        return found is not None and self._asks_polar(
            found[1], found[2], {}, frozenset(), seen | {found[0]}
        )

    def _constant(
        self,
        module: str,
        value: ast.expr,
        local: dict[str, str],
        bound: frozenset[str],
        seen: frozenset[str],
    ) -> tuple[str, str, ast.expr] | None:
        """The module constant a name stands for: its dotted name, module and value.

        ``None`` for anything else: a name the function binds itself, one
        no module of the package assigns, or one already being read.
        """
        if not isinstance(value, ast.Name) or value.id in bound:
            return None
        dotted = self.resolve(module, value, local)
        if dotted is None or dotted in seen or dotted not in self.constants:
            return None
        where, constant = self.constants[dotted]
        return dotted, where, constant

    def _polar_value(
        self,
        module: str,
        value: ast.expr,
        local: dict[str, str],
        bound: frozenset[str],
        seen: frozenset[str],
        *,
        flag: bool,
    ) -> bool:
        """Whether a ``projection=`` value, or a ``polar=`` flag, may ask for polar."""
        found = self._constant(module, value, local, bound, seen)
        if found is not None:
            dotted, where, constant = found
            return self._polar_value(
                where, constant, {}, frozenset(), seen | {dotted}, flag=flag
            )
        return _may_be_polar(value, flag=flag)


def _may_be_polar(value: ast.expr | None, *, flag: bool) -> bool:
    """Whether a ``projection=`` value, or a ``polar=`` flag, may ask for polar.

    A constant says what it says; anything computed (a variable, a
    conditional) may be the polar one, and is read as if it were.
    """
    if not isinstance(value, ast.Constant):
        return value is not None
    if flag:
        return value.value not in {False, None}
    return value.value == "polar"


def _is_polar(dotted: str) -> bool:
    return dotted.rpartition(".")[2] == "PolarAxes"


def reaching_polar(package: Package) -> set[str]:
    """Every function that makes a polar axes, or calls one that returns or reaches one."""
    returns_polar = {
        name
        for name, function in package.functions.items()
        if any(
            _is_polar(axes)
            for definition in function.definitions
            for axes in package.decided(function.module, definition.returns)[0]
        )
    }
    calls = {name: set(package.callees(f)) for name, f in package.functions.items()}
    reached = {
        name
        for name, function in package.functions.items()
        if package.makes_polar(function)
    }
    changed = True
    while changed:
        changed = False
        for name, targets in calls.items():
            if name not in reached and targets & (reached | returns_polar):
                reached.add(name)
                changed = True
    return reached


def findings_in(files: Sequence[pathlib.Path], root: pathlib.Path) -> list[Finding]:
    """Every return one argument decides that is written as one type."""
    package = Package(files, root)
    polar = reaching_polar(package)
    found: list[Finding] = []
    for name, function in sorted(package.functions.items()):
        path = package.paths[function.module]
        module = function.module
        for head in function.heads:
            single, several = package.decided(module, head.returns)
            if single and several:
                found.append(
                    Finding(
                        path,
                        head.lineno,
                        head_key(function.qualname, head, function.heads),
                        f"an overload head returns {ast.unparse(head.returns)}"
                        if head.returns is not None
                        else "an overload head returns a union",
                    )
                )
        implementation = function.implementation
        if implementation is None or implementation.returns is None:
            continue
        single, several = package.decided(module, implementation.returns)
        returns = ast.unparse(implementation.returns)
        if single and several and not function.heads:
            found.append(
                Finding(
                    path,
                    implementation.lineno,
                    function.qualname,
                    f"returns {returns}, and no overload says which argument decides",
                )
            )
        if name not in polar:
            continue
        if function.heads:
            if not any(
                _is_polar(axes)
                for head in function.heads
                for axes in package.decided(module, head.returns)[0]
            ):
                found.append(
                    Finding(
                        path,
                        implementation.lineno,
                        function.qualname,
                        "reaches a polar axes, and none of its overloads returns "
                        "PolarAxes",
                    )
                )
        elif package.hides_polar(module, implementation.returns):
            found.append(
                Finding(
                    path,
                    implementation.lineno,
                    function.qualname,
                    f"reaches a polar axes and returns {returns}",
                )
            )
    return found


def main(argv: Sequence[str] | None = None) -> int:
    """Report every return one argument decides that is written as one type."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package",
        nargs="?",
        type=pathlib.Path,
        default=SOURCE,
        help="the package directory to read (default: src/phonometry); the "
        "whole package is read, because a function reaches a polar axes "
        "through the functions of other modules it calls",
    )
    arguments = parser.parse_args(argv)
    root = arguments.package.resolve()
    found, stale = exempted(findings_in(python_files([], root), root), EXEMPT)
    if not (found or stale):
        print(
            "Every return that one argument decides has an overload for each "
            "case, and every polar axes is typed PolarAxes."
        )
        return 0
    if found:
        print("::error::a return that one argument decides is written as one type")
        for finding in found:
            print(
                f"  {finding.path}:{finding.line}: {finding.function}: {finding.sink}"
            )
        print(
            "  -> overload the function on the argument that decides, one "
            "typing.overload head per case, each returning the one type it "
            "gives (Axes for a given ax, a tuple of Axes for none; PolarAxes "
            "where the axes is polar), and keep the union on the "
            "implementation; a polar axes the function always returns is "
            "annotated PolarAxes. A return the data decide, not an argument, "
            "goes in EXEMPT at the top of scripts/check_return_overloads.py "
            "with its reason."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which needs no exemption any more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
