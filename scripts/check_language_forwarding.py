#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a call that leaves the caller's ``language`` behind.

A figure is drawn in Spanish by handing ``language="es"`` down from the result's
``.plot()`` to every helper that writes text, and every one of those helpers
defaults to English. A call that forgets to pass it on raises nothing, draws
nothing wrong to an English eye, and puts an English string or an English
decimal point into the Spanish figure. The K-weighting response drew its
lowest octave as ``31.5`` under ``plot(language="es")`` that way.

The frequency axis is where it shows, because nothing the library runs afterwards
can repair it. :func:`phonometry._i18n.localize_axes` runs at the end of a plot
and installs a comma formatter on each axis that still carries matplotlib's
default numeric one, and a frequency axis no longer does: it has been through
``format_frequency_axis``, which pins the octave centres with a fixed locator
and writes their labels as fixed strings. By then there is no number left to
reformat, only text, and rewriting text means guessing which dots are decimals.
So the comma can only be written where the label is made, by
``format_frequency_axis(..., language=language)``, and a call site that does not
pass it is the whole defect. The same holds for every other helper that takes
the language: ``_t`` returns its English key, ``format_number`` writes a period,
and a result's ``.plot()`` draws an English panel inside a Spanish figure.

This reads the source rather than a drawing. It indexes every function and
method of ``src/phonometry`` and ``scripts`` that takes a ``language``
parameter, and fails on any call to one of them, from anywhere a language is in
scope, that does not pass one on. A language is in scope where the function, or
a function it is nested in, names ``language`` as a parameter or a local, and
everywhere in the figure generators of ``scripts/figures``, which draw every
figure once per language and read the pass they are in from ``_LANG``. A module
body and a class body are read too, so a call that sits outside every function
is held to the same rule as one inside.

The callee is found the way the tree imports it: through relative imports,
package re-exports and module attributes (``noise_control.plot_x``). A method is
found through the class of its receiver, read from a parameter annotation, from
the class or function whose result was assigned to it, or from ``self``. Where
the receiver cannot be typed, a method name every method of which takes the
language still counts, with one exception: ``plot`` is also matplotlib's
``Axes.plot``, which always takes its data positionally, so an untyped
``.plot()`` is taken for a result's only when it passes no positional argument or
passes ``ax=``. A name only SOME of whose methods take the language switches
that fallback off, so it is reported in its own right rather than silently
(:meth:`Tree.partial_namesakes`), unless :data:`MIXED_NAMESAKES` records that
the name belongs to two unrelated things.

A helper is also followed through the two indirections the tree writes: a local
name bound to it (``draw = plot_x``) and ``functools.partial(plot_x, result)``,
whose bound arguments shift the slot the language is taken at. Three shapes stay
out of reach and are not claimed: a callable pulled out of a mapping
(``_TABLE["axis"](ax)``), one reached by ``getattr``, and one passed in as a
``Callable`` parameter. The tree has no such dispatch onto a helper that takes
the language today, and the report would be silent if it grew one.

Two forwarding shapes need reading rather than matching. A helper that takes
``**kwargs`` and hands them to one that takes the language takes the language
too, so a result's ``plot(ax, **kwargs)`` is held to the rule. A call that
passes ``**kwargs`` on counts as forwarding, unless the caller names
``language`` among its own parameters, in which case the parameter caught it
and the mapping cannot carry it. A string written in place of the language
(``language="en"``) does not forward the caller's, and is reported like an
omission.

A call that must stay English on purpose goes in :data:`EXEMPT` with the reason,
keyed by its line as well as its caller, so one approved call cannot cover a
second one written beside it. An entry whose call no longer drops the language,
or that has moved, fails too, so the table cannot rot.

Usage::

    python scripts/check_language_forwarding.py

Exit status 0 when every call passes the language on, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

ROOT = Path(__file__).resolve().parent.parent

#: Each tree read, as the directory it is imported from and the one walked.
#: ``scripts`` imports itself as ``figures.theme``, so it is its own base.
SOURCES: tuple[tuple[Path, Path], ...] = (
    (ROOT / "src", ROOT / "src" / "phonometry"),
    (ROOT / "scripts", ROOT / "scripts"),
)

#: The parameter a helper takes the rendering language by.
PARAMETER = "language"

#: Modules whose every function runs inside a language pass. ``generate_graphs``
#: draws each figure once per language, switching with ``set_lang``, and
#: ``figures._publish`` rebinds ``_LANG`` in each module of the package that
#: already holds the name, so a generator that reads it has the language of the
#: pass it is in. A module that never bound ``_LANG`` is treated as speaking
#: too, because the pass it runs in is what decides its output either way; the
#: advice printed for a call there names the import to add rather than a bare
#: ``_LANG`` the module would not resolve.
LANGUAGE_PASSES = ("figures", "generate_graphs")

#: Method names that a third-party object also answers to, and why an untyped
#: receiver is taken for one of this tree's objects only on a call that passes
#: no positional argument or passes ``ax=``.
FOREIGN_NAMESAKES: dict[str, str] = {
    "plot": (
        "matplotlib's Axes.plot, which takes its data positionally and has no "
        "ax parameter"
    ),
}

#: Method names an untyped receiver is never settled by, because the tree
#: defines the name for two unrelated things, and why. Without an entry a name
#: only some of whose methods take the language is reported by
#: :func:`partial_namesakes`: that is the state that silently switches the
#: untyped-receiver fallback off for every call to the name.
MIXED_NAMESAKES: dict[str, str] = {
    "__call__": (
        "The tree writes __call__ for two protocols of other libraries, not "
        "for one of its own: matplotlib's Formatter.__call__(value, pos), "
        "which the two decimal-comma tick formatters subclass, and the "
        "scipy.integrate derivative callback (t, y). Neither can take a "
        "language, and an untyped receiver says nothing about which is meant."
    ),
}

#: Calls that stay in English on purpose, keyed as the report prints them
#: (``path:line::caller -> helper``), each with the reason. The line is part of
#: the key so an entry exempts ONE call: a second call from the same caller to
#: the same helper has to be declared on its own, and a call that moves is
#: reported as stale and re-approved. Nothing belongs here that could pass the
#: language on instead.
EXEMPT: dict[str, str] = {
    (
        "scripts/figures/schematics.py:2816::animate_comb_filtering -> "
        "phonometry._plot.common.format_frequency_axis"
    ): (
        "The clip spans 50 Hz to 8 kHz, whose labelled centres (63 to 8k) are "
        "written the same in both languages, so its Spanish frames already "
        "read right. The call is part of the clip's fingerprint, and editing "
        "it would mark the committed clip stale for frames that cannot change."
    ),
}

_FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_DefinitionNode = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


@dataclass(frozen=True)
class Binding:
    """What an import binds: a module, or one name taken from a module."""

    module: str
    name: str | None = None


@dataclass(eq=False)
class Module:
    """One parsed source file, with what its top level defines and imports."""

    name: str
    path: Path
    package: bool
    node: ast.Module
    defs: dict[str, _DefinitionNode] = field(default_factory=dict)
    imports: dict[str, Binding] = field(default_factory=dict)
    speaks: bool = False


@dataclass(eq=False)
class Class:
    """A class, where it was defined and the members its body declares."""

    module: Module
    node: ast.ClassDef
    qualname: str
    scope: Scope | None
    members: dict[str, _DefinitionNode] = field(default_factory=dict)
    fields: dict[str, ast.expr] = field(default_factory=dict)


@dataclass(eq=False)
class Scope:
    """One function or method, with what a call inside it needs resolved."""

    module: Module
    node: _FunctionNode
    parent: Scope | None
    owner: Class | None
    qualname: str
    params: frozenset[str] = frozenset()
    locals: set[str] = field(default_factory=set)
    nested: dict[str, _DefinitionNode] = field(default_factory=dict)
    imports: dict[str, Binding] = field(default_factory=dict)
    values: dict[str, list[ast.expr]] = field(default_factory=dict)
    annotations: dict[str, ast.expr] = field(default_factory=dict)
    inserts: set[str] = field(default_factory=set)
    removes: set[str] = field(default_factory=set)
    calls: list[ast.Call] = field(default_factory=list)

    @property
    def static(self) -> bool:
        """Whether this is a static method, which binds no receiver."""
        return any(
            isinstance(dec, ast.Name) and dec.id == "staticmethod"
            for dec in self.node.decorator_list
        )

    @property
    def receiver(self) -> str | None:
        """The name a method binds its instance or class to, if it is one."""
        if self.owner is None or self.static:
            return None
        args = self.node.args
        positional = [*args.posonlyargs, *args.args]
        return positional[0].arg if positional else None

    @property
    def label(self) -> str:
        """The dotted name a report prints for this function."""
        return f"{self.module.name}.{self.qualname}"


@dataclass(frozen=True)
class ModuleRef:
    """A name that resolved to a module of the tree."""

    name: str


@dataclass(frozen=True)
class Local:
    """A name bound by a function's own parameters or assignments."""

    scope: Scope
    name: str


@dataclass(frozen=True)
class Slot:
    """Where a helper takes the language: a positional index, or keyword only."""

    index: int | None


@dataclass(frozen=True)
class Callee:
    """A call's target, reduced to what forwarding needs: a name and slots."""

    label: str
    slots: tuple[Slot, ...]


@dataclass(frozen=True)
class Finding:
    """One call that drops the language."""

    path: str
    line: int
    caller: str
    helper: str

    @property
    def key(self) -> str:
        """The key an :data:`EXEMPT` entry is written under.

        The line is in it, so an exemption speaks for the one call it was
        written for: a caller that grows a second call to the same helper does
        not inherit the first one's reason.
        """
        return f"{self.path}:{self.line}::{self.caller} -> {self.helper}"


_Target = Scope | Class | ModuleRef | Local | None


def _own_nodes(roots: Iterable[ast.AST]) -> Iterator[ast.AST]:
    """Every node that runs in this scope, not descending into a nested body.

    A nested function's decorators and defaults run here, and so do a class's
    bases, but their bodies do not. A lambda has no statements of its own, so a
    call inside one is counted as the enclosing function's.
    """
    stack = list(roots)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            stack.extend(node.decorator_list)
            stack.extend(node.args.defaults)
            stack.extend(d for d in node.args.kw_defaults if d is not None)
            continue
        if isinstance(node, ast.ClassDef):
            stack.extend(node.decorator_list)
            stack.extend(node.bases)
            continue
        stack.extend(ast.iter_child_nodes(node))


def _definitions(body: Iterable[ast.AST]) -> Iterator[_DefinitionNode]:
    """The functions and classes a body defines, however deep in its blocks."""
    for node in _own_nodes(body):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            yield node


def _import_bindings(module: Module, node: ast.AST) -> dict[str, Binding]:
    """The names one import statement binds, resolved to absolute modules."""
    if isinstance(node, ast.Import):
        return {
            alias.asname or alias.name.split(".")[0]: Binding(
                alias.name if alias.asname else alias.name.split(".")[0]
            )
            for alias in node.names
        }
    if not isinstance(node, ast.ImportFrom):
        return {}
    base = node.module or ""
    if node.level:
        parts = module.name.split(".")
        if not module.package:
            parts = parts[:-1]
        parts = parts[: len(parts) - (node.level - 1)]
        base = ".".join([*parts, node.module] if node.module else parts)
    return {
        alias.asname or alias.name: Binding(base, alias.name)
        for alias in node.names
        if alias.name != "*"
    }


def _removes_language(node: ast.AST) -> str | None:
    """The mapping a call pops the ``language`` key out of, if it does."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.attr == "pop"
        and node.args
        and _names_language(node.args[0])
    ):
        return node.func.value.id
    return None


def _inserts_language(node: ast.AST) -> str | None:
    """The mapping a statement writes a ``language`` key into, if it does."""
    if isinstance(node, ast.Assign | ast.AugAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == PARAMETER
            ):
                return target.value.id
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.attr in {"setdefault", "update"}
    ):
        keyed = bool(node.args) and _names_language(node.args[0])
        if keyed or any(k.arg == PARAMETER for k in node.keywords):
            return node.func.value.id
    return None


def _names_language(expr: ast.expr) -> bool:
    """Whether *expr* is the string ``"language"`` or a dict holding that key."""
    if isinstance(expr, ast.Constant):
        return expr.value == PARAMETER
    if isinstance(expr, ast.Dict):
        return any(
            isinstance(key, ast.Constant) and key.value == PARAMETER
            for key in expr.keys
        )
    return False


def _build_scope(
    module: Module,
    node: _FunctionNode,
    parent: Scope | None,
    owner: Class | None,
    qualname: str,
) -> Scope:
    """Read one function's parameters, locals, imports, calls and nested defs."""
    args = node.args
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    every += [a for a in (args.vararg, args.kwarg) if a is not None]
    scope = Scope(
        module,
        node,
        parent,
        owner,
        qualname,
        params=frozenset(a.arg for a in every),
        annotations={a.arg: a.annotation for a in every if a.annotation is not None},
    )
    scope.nested = {d.name: d for d in _definitions(node.body)}
    for child in _own_nodes(node.body):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            scope.locals.add(child.id)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            scope.locals.add(child.name)
        elif isinstance(child, ast.Import | ast.ImportFrom):
            scope.imports.update(_import_bindings(module, child))
        elif isinstance(child, ast.Call):
            scope.calls.append(child)
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    scope.values.setdefault(target.id, []).append(child.value)
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            scope.annotations[child.target.id] = child.annotation
            if child.value is not None:
                scope.values.setdefault(child.target.id, []).append(child.value)
        inserted = _inserts_language(child)
        if inserted is not None:
            scope.inserts.add(inserted)
        removed = _removes_language(child)
        if removed is not None:
            scope.removes.add(removed)
    # The walk is a stack, so the calls are put back into source order.
    scope.calls.sort(key=lambda call: (call.lineno, call.col_offset))
    return scope


class Tree:
    """Every module of the scanned trees, ready to say what a call reaches."""

    def __init__(self, modules: dict[str, Module], root: Path) -> None:
        self.modules = modules
        self.root = root
        self.scopes: list[Scope] = []
        self.functions: dict[ast.AST, Scope] = {}
        self.classes: dict[ast.AST, Class] = {}
        self.methods: dict[str, list[Scope]] = {}
        self._slots: dict[tuple[Scope, bool], Slot | None] = {}
        for module in modules.values():
            for child in _own_nodes(module.node.body):
                module.imports.update(_import_bindings(module, child))
            module.defs = {d.name: d for d in _definitions(module.node.body)}
            module.speaks = any(
                module.name == name or module.name.startswith(f"{name}.")
                for name in LANGUAGE_PASSES
            )
            for definition in module.defs.values():
                self._define(definition, module, None, None, "")
            self._define_body(module.node.body, module, None, None, "<module>")

    @classmethod
    def load(
        cls, sources: Iterable[tuple[Path, Path]] = SOURCES, root: Path = ROOT
    ) -> Tree:
        """Parse every ``.py`` file under each walked directory."""
        modules: dict[str, Module] = {}
        for base, walked in sources:
            for path in sorted(walked.rglob("*.py")):
                parts = path.relative_to(base).with_suffix("").parts
                package = parts[-1] == "__init__"
                name = ".".join(parts[:-1] if package else parts)
                source = path.read_text(encoding="utf-8")
                node = ast.parse(source, filename=str(path))
                modules[name] = Module(name, path, package, node)
        return cls(modules, root)

    def _define(
        self,
        node: _DefinitionNode,
        module: Module,
        parent: Scope | None,
        owner: Class | None,
        prefix: str,
    ) -> None:
        qualname = prefix + node.name
        if isinstance(node, ast.ClassDef):
            klass = Class(module, node, qualname, parent)
            klass.members = {d.name: d for d in _definitions(node.body)}
            klass.fields = {
                s.target.id: s.annotation
                for s in node.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
            }
            self.classes[node] = klass
            for member in klass.members.values():
                self._define(member, module, parent, klass, qualname + ".")
            self._define_body(node.body, module, parent, None, qualname + ".<class>")
            return
        scope = _build_scope(module, node, parent, owner, qualname)
        self.scopes.append(scope)
        self.functions[node] = scope
        if owner is not None:
            self.methods.setdefault(node.name, []).append(scope)
        for nested in scope.nested.values():
            self._define(nested, module, scope, None, qualname + ".<locals>.")

    def _define_body(
        self,
        body: list[ast.stmt],
        module: Module,
        parent: Scope | None,
        owner: Class | None,
        qualname: str,
    ) -> None:
        """Index the calls of a module body or a class body.

        Neither is a function, so neither was scanned at all, and a call there
        was never looked at: a module of ``scripts/figures`` runs inside a
        language pass wherever its code sits, and a class body nested in a
        function that takes the language has it in scope like any other
        statement of that function. The pseudo-scope takes no parameters and
        declares no locals, so ``speaks`` reads the enclosing function's, and
        failing that the module's, exactly as a real scope does.
        """
        node = ast.FunctionDef(
            name=qualname,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=list(body),
            decorator_list=[],
            returns=None,
            type_params=[],
        )
        self.scopes.append(_build_scope(module, node, parent, owner, qualname))

    # -- names ------------------------------------------------------------

    def _definition(self, node: _DefinitionNode) -> Scope | Class | None:
        return self.functions.get(node) or self.classes.get(node)

    def attribute(
        self, module_name: str, attr: str, seen: set[tuple[str, str]] | None = None
    ) -> _Target:
        """What ``module.attr`` is, following re-exports to where it is defined."""
        seen = set() if seen is None else seen
        child = f"{module_name}.{attr}"
        module = self.modules.get(module_name)
        if module is None:
            return ModuleRef(child) if child in self.modules else None
        if attr in module.defs:
            return self._definition(module.defs[attr])
        binding = module.imports.get(attr)
        if binding is not None and (module_name, attr) not in seen:
            seen.add((module_name, attr))
            found = self.bound(binding, seen)
            if found is not None:
                return found
        return ModuleRef(child) if child in self.modules else None

    def bound(
        self, binding: Binding, seen: set[tuple[str, str]] | None = None
    ) -> _Target:
        """What an import binding refers to, when it is part of the tree."""
        if binding.name is None:
            return ModuleRef(binding.module) if binding.module in self.modules else None
        return self.attribute(binding.module, binding.name, seen)

    def lookup(self, name: str, scope: Scope | None, module: Module) -> _Target:
        """Resolve a bare name the way Python would inside *scope*."""
        current = scope
        while current is not None:
            if name in current.nested:
                return self._definition(current.nested[name])
            if name in current.imports:
                return self.bound(current.imports[name])
            if name in current.params or name in current.locals:
                return Local(current, name)
            current = current.parent
        if name in module.defs:
            return self._definition(module.defs[name])
        if name in module.imports:
            return self.bound(module.imports[name])
        return None

    def resolve(self, expr: ast.expr, scope: Scope | None, module: Module) -> _Target:
        """Resolve a name or a dotted module path to what it refers to."""
        if isinstance(expr, ast.Name):
            return self.lookup(expr.id, scope, module)
        if isinstance(expr, ast.Attribute):
            base = self.resolve(expr.value, scope, module)
            if isinstance(base, ModuleRef):
                return self.attribute(base.name, expr.attr)
            if isinstance(base, Class):
                return self.member(base, expr.attr)
        return None

    # -- classes ----------------------------------------------------------

    def _bases(self, klass: Class) -> Iterator[Class]:
        for base in klass.node.bases:
            found = self.resolve(base, klass.scope, klass.module)
            if isinstance(found, Class):
                yield found

    def member(
        self, klass: Class, name: str, seen: set[int] | None = None
    ) -> Scope | None:
        """The method *name* of *klass*, or of the first base of the tree with it."""
        seen = set() if seen is None else seen
        if id(klass) in seen:
            return None
        seen.add(id(klass))
        node = klass.members.get(name)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return self.functions[node]
        for base in self._bases(klass):
            found = self.member(base, name, seen)
            if found is not None:
                return found
        return None

    def _field_type(self, klass: Class, name: str, depth: int) -> Class | None:
        annotation = klass.fields.get(name)
        if annotation is not None:
            return self.annotation_type(annotation, klass.scope, klass.module, klass)
        prop = klass.members.get(name)
        if isinstance(prop, ast.FunctionDef | ast.AsyncFunctionDef):
            return self.returns(self.functions[prop], klass)
        for base in self._bases(klass):
            if depth < _DEPTH:
                found = self._field_type(base, name, depth + 1)
                if found is not None:
                    return found
        return None

    def annotation_type(
        self,
        annotation: ast.expr,
        scope: Scope | None,
        module: Module,
        receiver: Class | None = None,
    ) -> Class | None:
        """The class of the tree an annotation names, through ``X | None``."""
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            try:
                parsed = ast.parse(annotation.value, mode="eval").body
            except SyntaxError:
                return None
            return self.annotation_type(parsed, scope, module, receiver)
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return self.annotation_type(
                annotation.left, scope, module, receiver
            ) or self.annotation_type(annotation.right, scope, module, receiver)
        if isinstance(annotation, ast.Subscript):
            head = annotation.value
            name = (
                head.attr
                if isinstance(head, ast.Attribute)
                else getattr(head, "id", "")
            )
            if name in {"Optional", "Annotated"}:
                inner = annotation.slice
                if isinstance(inner, ast.Tuple) and inner.elts:
                    inner = inner.elts[0]
                return self.annotation_type(inner, scope, module, receiver)
            return None
        if isinstance(annotation, ast.Name) and annotation.id == "Self":
            return receiver
        found = self.resolve(annotation, scope, module)
        return found if isinstance(found, Class) else None

    def returns(self, function: Scope, receiver: Class | None = None) -> Class | None:
        """The class of the tree a function's return annotation names."""
        annotation = function.node.returns
        if annotation is None:
            return None
        return self.annotation_type(
            annotation, function.parent, function.module, receiver or function.owner
        )

    def type_of(self, expr: ast.expr, scope: Scope, depth: int = 0) -> Class | None:
        """The class of the tree an expression evaluates to, where it can be read."""
        if depth > _DEPTH:
            return None
        if isinstance(expr, ast.Name):
            found = self.lookup(expr.id, scope, scope.module)
            if not isinstance(found, Local):
                return None
            where = found.scope
            if expr.id == where.receiver:
                return where.owner
            if expr.id in where.annotations:
                return self.annotation_type(
                    where.annotations[expr.id], where.parent, where.module
                )
            for value in where.values.get(expr.id, ()):
                typed = self.type_of(value, where, depth + 1)
                if typed is not None:
                    return typed
            return None
        if isinstance(expr, ast.Call):
            target = self.resolve(expr.func, scope, scope.module)
            if isinstance(target, Class):
                return target
            if isinstance(target, Scope):
                return self.returns(target)
            if isinstance(expr.func, ast.Attribute):
                owner = self.type_of(expr.func.value, scope, depth + 1)
                method = self.member(owner, expr.func.attr) if owner else None
                if method is not None:
                    return self.returns(method, owner)
            return None
        if isinstance(expr, ast.Attribute):
            owner = self.type_of(expr.value, scope, depth + 1)
            if owner is not None:
                return self._field_type(owner, expr.attr, depth)
        return None

    # -- the language -----------------------------------------------------

    def speaks(self, scope: Scope) -> bool:
        """Whether a language is in scope where *scope*'s body runs."""
        current: Scope | None = scope
        while current is not None:
            if PARAMETER in current.params or PARAMETER in current.locals:
                return True
            current = current.parent
        return scope.module.speaks

    def slot(self, function: Scope, *, bound: bool) -> Slot | None:
        """Where *function* takes the language, directly or through ``**kwargs``."""
        key = (function, bound)
        if key in self._slots:
            return self._slots[key]
        self._slots[key] = None  # a cycle through **kwargs forwards nothing
        args = function.node.args
        positional = [a.arg for a in (*args.posonlyargs, *args.args)]
        if bound and positional:
            positional = positional[1:]
        found: Slot | None = None
        if PARAMETER in positional:
            found = Slot(positional.index(PARAMETER))
        elif any(a.arg == PARAMETER for a in args.kwonlyargs):
            found = Slot(None)
        elif args.kwarg is not None:
            spread = args.kwarg.arg
            for call in function.calls:
                if not any(
                    k.arg is None
                    and isinstance(k.value, ast.Name)
                    and k.value.id == spread
                    for k in call.keywords
                ):
                    continue
                if self.callee(call, function) is not None:
                    found = Slot(None)
                    break
        self._slots[key] = found
        return found

    def callee(self, call: ast.Call, scope: Scope) -> Callee | None:
        """The helper *call* reaches, if it is one that takes the language."""
        func = call.func
        module = scope.module
        if isinstance(func, ast.Name):
            target = self.lookup(func.id, scope, module)
            if isinstance(target, Scope):
                return self._callee(target, bound=False)
            if isinstance(target, Class):
                init = self.member(target, "__init__")
                return self._callee(init, bound=True) if init else None
            if isinstance(target, Local):
                typed = self.type_of(func, scope)
                method = self.member(typed, "__call__") if typed else None
                if method is not None:
                    return self._callee(method, bound=True)
                return self._value_callee(target)
            return None
        if isinstance(func, ast.Call):
            # ``functools.partial(helper, ax)(...)``, called where it is built.
            return self._partial_callee(func, scope)
        if not isinstance(func, ast.Attribute):
            return None
        base = self.resolve(func.value, scope, module)
        if isinstance(base, ModuleRef):
            target = self.attribute(base.name, func.attr)
            if isinstance(target, Scope):
                return self._callee(target, bound=False)
            if isinstance(target, Class):
                init = self.member(target, "__init__")
                return self._callee(init, bound=True) if init else None
            return None
        if isinstance(base, Class):
            method = self.member(base, func.attr)
            return self._callee(method, bound=False) if method else None
        receiver = self._receiver(func.value, scope)
        if receiver is not None:
            method = self.member(receiver, func.attr)
            return self._callee(method, bound=not method.static) if method else None
        return self._by_name(call, func.attr)

    def _receiver(self, expr: ast.expr, scope: Scope) -> Class | None:
        if (
            isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Name)
            and expr.func.id == "super"
        ):
            current: Scope | None = scope
            while current is not None and current.owner is None:
                current = current.parent
            if current is None or current.owner is None:
                return None
            bases = list(self._bases(current.owner))
            return bases[0] if bases else None
        return self.type_of(expr, scope)

    def _callee(self, function: Scope, *, bound: bool) -> Callee | None:
        slot = self.slot(function, bound=bound)
        return Callee(function.label, (slot,)) if slot is not None else None

    def _binding(self, name: str, scope: Scope) -> Binding | None:
        """The import *name* is bound by, whether or not it is of this tree."""
        current: Scope | None = scope
        while current is not None:
            if name in current.imports:
                return current.imports[name]
            if (
                name in current.nested
                or name in current.params
                or name in current.locals
            ):
                return None
            current = current.parent
        return scope.module.imports.get(name)

    def _is_partial(self, func: ast.expr, scope: Scope) -> bool:
        """Whether *func* names ``functools.partial``, imported either way."""
        if isinstance(func, ast.Name):
            binding = self._binding(func.id, scope)
            return (
                binding is not None
                and binding.module == "functools"
                and binding.name == "partial"
            )
        if isinstance(func, ast.Attribute) and func.attr == "partial":
            if not isinstance(func.value, ast.Name):
                return False
            binding = self._binding(func.value.id, scope)
            return (
                binding is not None
                and binding.module == "functools"
                and binding.name is None
            )
        return False

    def _partial_callee(
        self, call: ast.Call, scope: Scope, depth: int = 0
    ) -> Callee | None:
        """``functools.partial(helper, ...)`` reduced to the helper it wraps.

        The bound arguments shift the slot: ``partial(plot_x, result)`` leaves
        the language one place earlier than ``plot_x`` takes it. A partial that
        binds the language itself, or that spreads a mapping that may hold it,
        forwards it already and is not a call to report.
        """
        if depth > _DEPTH or not self._is_partial(call.func, scope) or not call.args:
            return None
        if any(k.arg in {PARAMETER, None} for k in call.keywords):
            return None
        inner = self._expression_callee(call.args[0], scope, depth + 1)
        if inner is None:
            return None
        bound = len(call.args) - 1
        slots: list[Slot] = []
        for slot in inner.slots:
            if slot.index is None:
                slots.append(slot)
                continue
            if slot.index < bound:
                return None  # the partial already fills the language slot
            slots.append(Slot(slot.index - bound))
        return Callee(inner.label, tuple(slots))

    def _expression_callee(
        self, expr: ast.expr, scope: Scope, depth: int = 0
    ) -> Callee | None:
        """The helper an expression evaluates to, where it can be read."""
        if depth > _DEPTH:
            return None
        if isinstance(expr, ast.Name | ast.Attribute):
            target = self.resolve(expr, scope, scope.module)
            if isinstance(target, Scope):
                return self._callee(target, bound=False)
            if isinstance(target, Local):
                return self._value_callee(target, depth + 1)
            return None
        if isinstance(expr, ast.Call):
            return self._partial_callee(expr, scope, depth)
        return None

    def _value_callee(self, local: Local, depth: int = 0) -> Callee | None:
        """The helper a local name holds: an alias, or a ``partial`` of one."""
        if depth > _DEPTH:
            return None
        for value in local.scope.values.get(local.name, ()):
            found = self._expression_callee(value, local.scope, depth + 1)
            if found is not None:
                return found
        return None

    def _by_name(self, call: ast.Call, name: str) -> Callee | None:
        """An untyped receiver's method, when the name alone settles it."""
        candidates = self.methods.get(name, [])
        if not candidates:
            return None
        if name in FOREIGN_NAMESAKES and (
            call.args and not any(k.arg == "ax" for k in call.keywords)
        ):
            return None
        slots = [self.slot(m, bound=not m.static) for m in candidates]
        if not all(slots):
            return None
        return Callee(f"?.{name}", tuple(s for s in slots if s is not None))

    def partial_namesakes(self) -> list[tuple[str, list[Scope]]]:
        """Method names only some of whose namesakes take the language.

        The untyped-receiver fallback of :meth:`_by_name` needs every method of
        a name to take the language, because a receiver it cannot type could be
        any of them. One namesake without the parameter therefore switches the
        whole name off, and until this reported it, silently: the day a
        ``report`` or a ``plot`` is written without a language, every untyped
        call to that name stops being checked and the gate stays green.

        So a name in this state is a finding of its own unless
        :data:`MIXED_NAMESAKES` says the name belongs to two unrelated things.
        The outliers are named, and the fix is usually theirs: give the method
        the language its namesakes take.
        """
        mixed: list[tuple[str, list[Scope]]] = []
        for name, candidates in sorted(self.methods.items()):
            if name in MIXED_NAMESAKES:
                continue
            without = [
                m for m in candidates if self.slot(m, bound=not m.static) is None
            ]
            if without and len(without) != len(candidates):
                mixed.append((name, without))
        return mixed

    # -- forwarding -------------------------------------------------------

    def forwards(self, call: ast.Call, callee: Callee, scope: Scope) -> bool:
        """Whether *call* passes the caller's language on to *callee*."""
        for keyword in call.keywords:
            if keyword.arg == PARAMETER:
                return not isinstance(keyword.value, ast.Constant)
        for slot in callee.slots:
            if slot.index is None:
                continue
            # A star-argument at or before the slot may fill it; one can never
            # reach a keyword-only parameter, so it forwards nothing there.
            reached = call.args[: slot.index + 1]
            if any(isinstance(arg, ast.Starred) for arg in reached):
                return True
            if slot.index < len(call.args):
                return not isinstance(call.args[slot.index], ast.Constant)
        return any(
            keyword.arg is None and self._may_carry(keyword.value, scope)
            for keyword in call.keywords
        )

    def _may_carry(self, expr: ast.expr, scope: Scope, depth: int = 0) -> bool:
        """Whether a ``**mapping`` can hold a ``language`` key.

        Only what is provably without one says no: a dict literal that lacks
        the key, a mapping the key was popped from and never written back, or
        the caller's own ``**kwargs`` when the caller names the language among
        its parameters, which is where Python put it instead.
        """
        if depth > _DEPTH:
            return True
        if isinstance(expr, ast.Dict):
            return any(
                key is None
                or (isinstance(key, ast.Constant) and key.value == PARAMETER)
                for key in expr.keys
            )
        if (
            isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Name)
            and expr.func.id == "dict"
        ):
            if any(k.arg in {PARAMETER, None} for k in expr.keywords):
                return True
            return any(self._may_carry(arg, scope, depth + 1) for arg in expr.args)
        if not isinstance(expr, ast.Name):
            return True
        found = self.lookup(expr.id, scope, scope.module)
        if not isinstance(found, Local):
            return True
        where = found.scope
        if expr.id in where.inserts:
            return True
        if expr.id in where.removes:
            return False
        spread = where.node.args.kwarg
        if spread is not None and spread.arg == expr.id:
            return PARAMETER not in where.params
        values = where.values.get(expr.id)
        if not values:
            return True
        return any(self._may_carry(value, where, depth + 1) for value in values)

    def dropped(self) -> Iterator[Finding]:
        """Every call that reaches a language helper without passing it on."""
        for scope in self.scopes:
            if not self.speaks(scope):
                continue
            for call in scope.calls:
                callee = self.callee(call, scope)
                if callee is None or self.forwards(call, callee, scope):
                    continue
                path = scope.module.path
                shown = (
                    path.relative_to(self.root)
                    if path.is_relative_to(self.root)
                    else path
                )
                yield Finding(
                    shown.as_posix(), call.lineno, scope.qualname, callee.label
                )


#: How far a name is followed through assignments and bases before giving up.
_DEPTH = 8


def classify(tree: Tree, exempt: dict[str, str]) -> tuple[list[Finding], list[str]]:
    """Split the dropped calls into the undeclared ones and the stale entries.

    :param tree: The parsed trees.
    :param exempt: The escape hatch, ``path:line::caller -> helper`` to reason.
    :return: The calls that drop the language and are not exempt, and the
        exemption keys that no longer match a call that does.
    """
    found = sorted(tree.dropped(), key=lambda f: (f.path, f.line, f.helper))
    keys = {f.key for f in found}
    return [f for f in found if f.key not in exempt], sorted(set(exempt) - keys)


def main(argv: list[str] | None = None) -> int:
    """Report every call that leaves the caller's language behind."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.parse_args(argv)

    tree = Tree.load()
    dropped, stale = classify(tree, EXEMPT)
    mixed = tree.partial_namesakes()
    if not dropped and not stale and not mixed:
        print(
            f"Every call to a helper that takes the language passes it on: "
            f"{len(tree.modules)} modules, {len(EXEMPT)} exempt."
        )
        return 0
    for finding in dropped:
        print(
            f"{finding.path}:{finding.line}: {finding.helper} is called from "
            f"{finding.caller} without the language"
        )
    if dropped:
        print()
        print(
            f"{len(dropped)} call(s) leave the language behind. Pass "
            f"language=language on (in a figure generator, language=_LANG, "
            "imported from figures.i18n where the module does not hold it "
            "already); if the call must stay English on purpose, add its key "
            "(path:line::caller -> helper) to EXEMPT in "
            "scripts/check_language_forwarding.py with the reason."
        )
    for name, without in mixed:
        total = len(tree.methods[name])
        print()
        print(
            f"{total - len(without)} of the {total} methods named {name} take "
            f"the language, so a call on a receiver that cannot be typed is no "
            f"longer checked for any of them. Give the language to:"
        )
        for outlier in without:
            print(f"  {outlier.module.path.name}: {outlier.label}")
        print(
            "or, if the name belongs to two unrelated things, declare it in "
            "MIXED_NAMESAKES with the reason."
        )
    for key in stale:
        print(f"EXEMPT lists {key}, which no longer drops the language: drop the entry")
    return 1


if __name__ == "__main__":
    sys.exit(main())
