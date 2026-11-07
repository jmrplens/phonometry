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
package re-exports and module attributes (``noise_control.plot_x``). Of the
``def``s, classes and imports that bind one name in a scope, the call reaches
those that may stand where it runs (:func:`ast_scan.live_bindings`): the
later of two in a row, whichever kind each is, either of two in the branches
of a ``try`` or an ``if``, against each of which the call is checked, and,
from a function written in the scope, every one that may stand from its
``def`` on, since the function may be called before a later binding.
A method is
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
from typing import TYPE_CHECKING, TypeGuard

from ast_scan import (
    assigned_value,
    assignment_target,
    binding_of,
    bindings_by_name,
    empty_type_checking_bodies,
    global_bindings,
    held_before,
    is_type_checking_block,
    live_bindings,
    own_names,
    scope_nodes,
    what_never_runs,
)
from ast_scan import parameters as with_defaults

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
        "scripts/figures/schematics.py:3014::animate_comb_filtering -> "
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


@dataclass(frozen=True, eq=False)
class Alias:
    """What an assignment of a name or a dotted one alone at the top of a
    module, or under ``global`` (``draw = axis``, ``(draw := axis)``), binds
    its *target*, the name or the assignment expression, to: what the value
    stands for where the assignment reads it.
    """

    module: Module
    target: ast.Name | ast.NamedExpr


@dataclass(frozen=True, eq=False)
class Computed:
    """What an assignment of a call's result alone (``draw = partial(axis)``,
    ``(draw := partial(axis))``) binds its *target*, the name or the
    assignment expression, to, in *scope*, the module or the function it is
    written in: what the call makes, read where the assignment runs
    (:meth:`Tree._computed_callee`).
    """

    module: Module
    target: ast.Name | ast.NamedExpr
    scope: ast.AST


@dataclass(frozen=True, eq=False)
class Opaque:
    """What any other binding of a name binds it to (a lambda, a loop's
    target, a ``del``): nothing the tree defines, which ends whatever the
    name stood for before it.
    """


#: What a statement binds a name to: a function or a class it defines, what
#: it imports, what an assignment of a name or of a call's result binds it
#: to, or nothing the tree defines.
_Bound = _DefinitionNode | Binding | Alias | Computed | Opaque

#: A statement, or the node of another binding of a name (an assignment's
#: target, a loop's), with what it binds the name to.
_Written = tuple[ast.AST, _Bound]


@dataclass(eq=False)
class Module:
    """One parsed source file, with what its top level defines and imports."""

    name: str
    path: Path
    package: bool
    node: ast.Module
    #: Every ``def``, class, import and assignment of a name or a dotted one
    #: alone (:class:`Alias`) of each name its top level binds, in the order
    #: of the source (:func:`_scope_names`, :func:`_module_aliases`), and
    #: those a function makes of a module name under ``global``.
    names: dict[str, list[_Written]] = field(default_factory=dict)
    #: Every function and class its top level defines, two of one name alike.
    definitions: list[_DefinitionNode] = field(default_factory=list)
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
    #: Every ``def``, class and import of each name it binds, in the order of
    #: the source (:func:`_scope_names`).
    names: dict[str, list[_Written]] = field(default_factory=dict)
    #: Every function and class defined in it, two of one name alike.
    definitions: list[_DefinitionNode] = field(default_factory=list)
    values: dict[str, list[ast.expr]] = field(default_factory=dict)
    #: What each parameter holds at a call that hands it nothing, read where the
    #: ``def`` runs its defaults: in the scope around, not here.
    defaults: dict[str, ast.expr] = field(default_factory=dict)
    annotations: dict[str, ast.expr] = field(default_factory=dict)
    inserts: set[str] = field(default_factory=set)
    removes: set[str] = field(default_factory=set)
    calls: list[ast.Call] = field(default_factory=list)
    #: The class whose body this scope reads, for a scope made of one
    #: (:meth:`Tree._define_body`).
    holder: ast.ClassDef | None = None

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
    """Where a helper takes the language: a positional index, or keyword only,
    and whether a keyword of its name fills it: a positional-only one takes
    none, which goes to the helper's ``**kwargs`` instead.
    """

    index: int | None
    keyword: bool = True


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


_Target = Scope | Class | ModuleRef | Local | Computed | None


def _own_nodes(roots: Iterable[ast.AST]) -> Iterator[ast.AST]:
    """Every node that runs in this scope, in the order of the source, not
    descending into a nested body.

    A nested function's decorators and defaults run here, and so do a class's
    bases, but their bodies do not. A lambda has no statements of its own, so a
    call inside one is counted as the enclosing function's. The order is the
    source's so that of two imports or two definitions of one name, the later,
    which Python leaves in place, is the one a table built from the walk keeps.
    """
    stack = list(roots)[::-1]
    while stack:
        node = stack.pop()
        yield node
        children: list[ast.AST]
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            children = [*node.decorator_list, *node.args.defaults]
            children.extend(d for d in node.args.kw_defaults if d is not None)
        elif isinstance(node, ast.ClassDef):
            children = [*node.decorator_list, *node.bases]
        else:
            children = list(ast.iter_child_nodes(node))
        stack.extend(children[::-1])


def _definitions(body: Iterable[ast.AST], root: ast.AST) -> Iterator[_DefinitionNode]:
    """The functions and classes a body of the tree *root* defines, however
    deep in its blocks.

    One defined where a test on ``TYPE_CHECKING`` keeps it from running is
    never defined when the code runs (the constructor a record declares for
    the type checker): it is no definition of the program, and is passed over.
    """
    skipped = {
        id(child)
        for node in _own_nodes(body)
        if isinstance(node, ast.If) and is_type_checking_block(node, root)
        for child in what_never_runs(node)
    }
    for node in _own_nodes(body):
        if id(node) in skipped:
            continue
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


def _scope_names(
    module: Module,
    scope: ast.Module | _FunctionNode,
    holder: ast.AST | None = None,
) -> tuple[dict[str, list[_Written]], list[_DefinitionNode]]:
    """Every ``def``, ``class`` and import of each name *scope* binds, in the
    order of the source, and every function and class it defines; *holder*
    is the module or the class whose body a scope made to read that body
    holds (:meth:`Tree._define_body`), whose bindings are its own.

    Such a name is read with every other binding of it in *scope*
    (:func:`ast_scan.bindings_by_name`), and so is one an assignment of a
    name or a dotted one alone binds at the top of the module: an alias in
    a function stands for what its value names (:class:`Alias`), as one at
    the top does (:func:`_module_aliases`), an assignment of a call's result
    for what the call makes (:class:`Computed`), so a ``functools.partial``
    of the helper the name held still reaches it, and any other binding for
    nothing the tree defines (:class:`Opaque`), so a lambda after an import
    ends it. Which of them a call reaches is read where the call runs
    (:func:`_standing`).
    """
    top = isinstance(scope, ast.Module)
    definitions = list(_definitions(scope.body, module.node))
    written: dict[str, list[_Written]] = {}
    for definition in definitions:
        written.setdefault(definition.name, []).append((definition, definition))
    for node in _own_nodes(scope.body):
        if isinstance(node, ast.Import | ast.ImportFrom):
            for name, binding in _import_bindings(module, node).items():
                written.setdefault(name, []).append((node, binding))
    every = bindings_by_name(holder or scope) if top or written else {}
    for name, nodes in every.items():
        if name not in written and not top:
            continue
        aliases = [node for node in nodes if _aliases_a_name(node, module.node)]
        if (
            name not in written
            and not aliases
            and not any(_computes(node, module.node) for node in nodes)
        ):
            continue
        for node in nodes:
            if isinstance(node, _DefinitionNode | ast.Import | ast.ImportFrom):
                continue
            if _computes(node, module.node):
                written.setdefault(name, []).append(
                    (node, Computed(module, node, scope))
                )
            elif node not in aliases:
                written.setdefault(name, []).append((node, Opaque()))
            elif not top:
                written[name].append((node, Alias(module, node)))
    for pairs in written.values():
        pairs.sort(key=lambda pair: _position(pair[0]))
    return written, definitions


def _position(node: ast.AST) -> tuple[int, int]:
    """Where *node* is written: its line and its column."""
    return getattr(node, "lineno", 0), getattr(node, "col_offset", 0)


def _aliases_a_name(
    node: ast.AST, root: ast.AST
) -> TypeGuard[ast.Name | ast.NamedExpr]:
    """Whether *node*, under *root*, is a name an assignment binds to a name
    or a dotted one alone (``draw = axis``, ``label = helpers.axis``), or an
    assignment expression that does (``(draw := axis)``).
    """
    if assignment_target(node) is None or not isinstance(
        node, ast.Name | ast.NamedExpr
    ):
        return False
    value = assigned_value(root, node)
    while isinstance(value, ast.Attribute):
        value = value.value
    return isinstance(value, ast.Name)


def _computes(node: ast.AST, root: ast.AST) -> TypeGuard[ast.Name | ast.NamedExpr]:
    """Whether *node*, under *root*, is a name an assignment binds to a
    call's result alone (``draw = partial(axis)``), or an assignment
    expression that does.
    """
    return (
        isinstance(node, ast.Name | ast.NamedExpr)
        and assignment_target(node) is not None
        and isinstance(assigned_value(root, node), ast.Call)
    )


def _standing(
    module: Module, written: list[_Written], point: ast.AST | None
) -> list[_Bound]:
    """What a name *written* binds may stand for at *point*, or once its scope
    has run when *point* is None (:func:`ast_scan.live_bindings`).

    The later of two in a row, a ``def`` or an import alike, and either of
    two in the branches of a ``try`` or an ``if``; from a function written
    in the scope, every one that may stand from the ``def`` on, since the
    function may be called at once or once the scope has run. A ``def`` or
    an import that a function makes of a module name under ``global``
    (:func:`ast_scan.global_bindings`) may stand anywhere, since that
    function may run at any time.
    """
    inside = {
        id(node) for nodes in global_bindings(module.node).values() for node in nodes
    }
    anywhere = [bound for statement, bound in written if id(statement) in inside]
    own = [
        (statement, bound)
        for statement, bound in written
        if id(statement) not in inside
    ]
    if len(own) < 2:
        return [*(bound for _, bound in own), *anywhere]
    statements = [statement for statement, _ in own]
    live = live_bindings(module.node, statements, point)
    return [
        *(bound for statement, bound in own if any(statement is s for s in live)),
        *anywhere,
    ]


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
    holder: ast.AST | None = None,
) -> Scope:
    """Read one function's parameters, locals, imports, calls and nested defs;
    *holder* is the module or the class a scope made of its body stands for
    (:func:`_scope_names`).
    """
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
        defaults={
            a.arg: default for a, default in with_defaults(node) if default is not None
        },
    )
    scope.names, scope.definitions = _scope_names(module, node, holder)
    if isinstance(holder, ast.ClassDef):
        scope.holder = holder
    # As Python scopes them: a comprehension's variable and a lambda's
    # parameter are not the function's (:func:`_bound_inside`).
    names = own_names(node)
    scope.locals |= names.stored | names.annotated
    for child in _own_nodes(node.body):
        if isinstance(child, ast.Call):
            scope.calls.append(child)
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    scope.values.setdefault(target.id, []).append(child.value)
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            scope.annotations[child.target.id] = child.annotation
            if child.value is not None:
                scope.values.setdefault(child.target.id, []).append(child.value)
        elif isinstance(child, ast.NamedExpr) and isinstance(child.target, ast.Name):
            scope.values.setdefault(child.target.id, []).append(child.value)
        inserted = _inserts_language(child)
        if inserted is not None:
            scope.inserts.add(inserted)
        removed = _removes_language(child)
        if removed is not None:
            scope.removes.add(removed)
    # Calls are read in the order of their position in the source.
    scope.calls.sort(key=lambda call: (call.lineno, call.col_offset))
    return scope


def _unbound_in_class(
    module: Module, holder: ast.ClassDef, name: str, point: ast.AST
) -> bool:
    """Whether the class body *holder* binds *name* and none of its bindings
    of it may have run where *point*, in the body, reads it
    (:func:`ast_scan.held_before`): Python then reads the module's name, not
    the body's, since a class body that binds a name looks it up in its own
    namespace and then the module's.
    """
    nodes = bindings_by_name(holder).get(name, [])
    return bool(nodes) and not held_before(module.node, nodes, point)


def _bound_inside(scope: Scope, point: ast.AST, name: str) -> bool:
    """Whether a comprehension or a lambda around *point*, inside *scope*, binds
    *name* for itself, which then stands for nothing a scope's name does.
    """
    binder = binding_of(scope.node, point, name)[1]
    return binder is not None and binder is not scope.node


def _one(targets: list[_Target]) -> _Target:
    """The one thing every reading of a name agrees on, or None when they differ."""
    first = targets[0] if targets else None
    return first if all(t is first or t == first for t in targets) else None


#: What an import binds ``dataclasses.dataclass`` and its module as.
_DATACLASS = Binding("dataclasses", "dataclass")
_DATACLASSES = Binding("dataclasses")


def _generates_init(klass: Class) -> bool:
    """Whether ``@dataclass`` writes *klass* an ``__init__``: a decorator of
    it is the one ``dataclasses`` defines, by a name or an attribute of the
    module its scope or module imports, and it does not say ``init=False``.
    """
    names = klass.scope.names if klass.scope is not None else {}

    def binds(name: str, binding: Binding) -> bool:
        written = names.get(name) or klass.module.names.get(name, [])
        return any(bound == binding for _, bound in written)

    for decorator in klass.node.decorator_list:
        called = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(called, ast.Name):
            named = binds(called.id, _DATACLASS)
        else:
            named = (
                isinstance(called, ast.Attribute)
                and called.attr == "dataclass"
                and isinstance(called.value, ast.Name)
                and binds(called.value.id, _DATACLASSES)
            )
        if named:
            return not (
                isinstance(decorator, ast.Call)
                and any(
                    keyword.arg == "init"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is False
                    for keyword in decorator.keywords
                )
            )
    return False


def _add_global_bindings(module: Module) -> None:
    """Add to the names of *module* every ``def``, ``class`` and import that a
    function, a method or a class body inside it makes of a module name
    under ``global`` (:func:`ast_scan.global_bindings`), which may be what
    the name stands for at any call.
    """
    for name, nodes in global_bindings(module.node).items():
        for node in nodes:
            if isinstance(node, ast.Import | ast.ImportFrom):
                binding = _import_bindings(module, node).get(name)
                if binding is not None:
                    module.names.setdefault(name, []).append((node, binding))
            elif isinstance(
                node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                module.names.setdefault(name, []).append((node, node))


def _module_aliases(tree: ast.Module) -> dict[str, list[ast.Name | ast.NamedExpr]]:
    """Each name an assignment of a name or a dotted one alone binds at the
    top of *tree*, or in a function, a method or a class body inside it under
    ``global`` (:func:`ast_scan.global_bindings`), with every such target.
    """
    found: dict[str, list[ast.Name | ast.NamedExpr]] = {}
    candidates = [
        *scope_nodes(tree),
        *(node for nodes in global_bindings(tree).values() for node in nodes),
    ]
    for node in candidates:
        if _aliases_a_name(node, tree) and (target := assignment_target(node)):
            found.setdefault(target.id, []).append(node)
    return found


def _one_import(bound: list[_Bound]) -> Binding | None:
    """The import every binding of a name that may stand is, or None."""
    first = bound[0] if bound else None
    if isinstance(first, Binding) and all(b == first for b in bound):
        return first
    return None


class Tree:
    """Every module of the scanned trees, ready to say what a call reaches."""

    def __init__(self, modules: dict[str, Module], root: Path) -> None:
        self.modules = modules
        self.root = root
        self.scopes: list[Scope] = []
        self.functions: dict[ast.AST, Scope] = {}
        self.classes: dict[ast.AST, Class] = {}
        self.methods: dict[str, list[Scope]] = {}
        #: What :meth:`linearization` found, read once for each class.
        self._lines: dict[Class, tuple[Class, ...]] = {}
        self._slots: dict[tuple[Scope, bool], Slot | None] = {}
        self._aliasing: set[int] = set()
        self._computing: set[int] = set()
        #: The scope of each module body and class body read as a function
        #: of its own (:meth:`_define_body`), by the node that stands for it.
        self._bodies: dict[ast.AST, Scope] = {}
        #: The scope of each class body, by its ``class`` statement.
        self._class_bodies: dict[ast.AST, Scope] = {}
        for module in modules.values():
            module.names, module.definitions = _scope_names(module, module.node)
            _add_global_bindings(module)
            for name, targets in _module_aliases(module.node).items():
                written = module.names.setdefault(name, [])
                written.extend((target, Alias(module, target)) for target in targets)
                written.sort(key=lambda pair: _position(pair[0]))
            module.speaks = any(
                module.name == name or module.name.startswith(f"{name}.")
                for name in LANGUAGE_PASSES
            )
            for definition in module.definitions:
                self._define(definition, module, None, None, "")
            self._define_body(module.node, module, None, None, "<module>")

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
                node = empty_type_checking_bodies(ast.parse(source, filename=str(path)))
                modules[name] = Module(name, path, package, node)
        return cls(modules, root)

    def _define(
        self,
        node: _DefinitionNode,
        module: Module,
        parent: Scope | None,
        owner: Class | None,
        prefix: str,
        hidden: frozenset[str] = frozenset(),
    ) -> None:
        """Index a definition; *hidden* holds the type parameters of the
        generic classes it is written in, which it reads as theirs.
        """
        qualname = prefix + node.name
        if isinstance(node, ast.ClassDef):
            hidden |= own_names(node).type_parameters
            klass = Class(module, node, qualname, parent)
            klass.members = {d.name: d for d in _definitions(node.body, module.node)}
            klass.fields = {
                s.target.id: s.annotation
                for s in node.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
            }
            self.classes[node] = klass
            for member in klass.members.values():
                self._define(member, module, parent, klass, qualname + ".", hidden)
            self._define_body(node, module, parent, None, qualname + ".<class>", hidden)
            return
        scope = _build_scope(module, node, parent, owner, qualname)
        scope.locals |= hidden | own_names(node).type_parameters
        self.scopes.append(scope)
        self.functions[node] = scope
        if owner is not None:
            self.methods.setdefault(node.name, []).append(scope)
        for nested in scope.definitions:
            self._define(nested, module, scope, None, qualname + ".<locals>.")

    def _define_body(
        self,
        holder: ast.Module | ast.ClassDef,
        module: Module,
        parent: Scope | None,
        owner: Class | None,
        qualname: str,
        hidden: frozenset[str] = frozenset(),
    ) -> None:
        """Index the calls of a module body or a class body.

        Neither is a function, so neither was scanned at all, and a call there
        was never looked at: a module of ``scripts/figures`` runs inside a
        language pass wherever its code sits, and a class body nested in a
        function that takes the language has it in scope like any other
        statement of that function. The pseudo-scope takes no parameters and
        declares no locals but the type parameters of a generic class
        (*hidden*), so ``speaks`` reads the enclosing function's, and failing
        that the module's, exactly as a real scope does.
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
            body=list(holder.body),
            decorator_list=[],
            returns=None,
            type_params=[],
        )
        scope = _build_scope(module, node, parent, owner, qualname, holder)
        scope.locals |= hidden
        self.scopes.append(scope)
        self._bodies[node] = scope
        if isinstance(holder, ast.ClassDef):
            self._class_bodies[holder] = scope

    # -- names ------------------------------------------------------------

    def _definition(self, node: _DefinitionNode) -> Scope | Class | None:
        return self.functions.get(node) or self.classes.get(node)

    def _targets(
        self, bound: _Bound, seen: frozenset[tuple[str, str]] = frozenset()
    ) -> list[_Target]:
        """What one binding of a name refers to: a definition, an import's, or
        what an assignment of a name binds it to (:meth:`_aliased`).
        """
        if isinstance(bound, Binding):
            return self.bounds(bound, seen)
        if isinstance(bound, Alias):
            return self._aliased(bound)
        if isinstance(bound, Computed):
            return [bound]
        if isinstance(bound, Opaque):
            return []
        found = self._definition(bound)
        return [found] if found is not None else []

    def attributes(
        self,
        module_name: str,
        attr: str,
        seen: frozenset[tuple[str, str]] = frozenset(),
    ) -> list[_Target]:
        """What ``module.attr`` may be, following re-exports to where it is defined.

        Each binding of the name that may stand once the module has run, so
        two imports of it in the branches of a ``try`` give two.
        """
        child = f"{module_name}.{attr}"
        fallback: list[_Target] = [ModuleRef(child)] if child in self.modules else []
        module = self.modules.get(module_name)
        if module is None or (module_name, attr) in seen:
            return fallback
        inner = seen | {(module_name, attr)}
        found = [
            target
            for bound in _standing(module, module.names.get(attr, []), None)
            for target in self._targets(bound, inner)
        ]
        return found or fallback

    def attribute(self, module_name: str, attr: str) -> _Target:
        """What ``module.attr`` is, when every binding it may hold agrees."""
        return _one(self.attributes(module_name, attr))

    def bounds(
        self, binding: Binding, seen: frozenset[tuple[str, str]] = frozenset()
    ) -> list[_Target]:
        """What an import binding may refer to, when it is part of the tree."""
        if binding.name is None:
            return [ModuleRef(binding.module)] if binding.module in self.modules else []
        return self.attributes(binding.module, binding.name, seen)

    def bound(self, binding: Binding) -> _Target:
        """What an import binding refers to, when every reading of it agrees."""
        return _one(self.bounds(binding))

    def lookups(
        self,
        name: str,
        scope: Scope | None,
        module: Module,
        point: ast.AST | None = None,
    ) -> list[_Target]:
        """Everything a bare name may stand for inside *scope*, read as Python reads it.

        The innermost scope that binds the name holds it: its ``def``s,
        classes and imports that may stand where *point* reads it, or once it
        has run when no point is given (:func:`_standing`), or its parameters
        and locals. A comprehension or a lambda around *point* that binds the
        name holds nothing the tree defines (:func:`_bound_inside`). A class
        body read at *point* before any binding it makes of the name has run
        reads the module's, as Python does (:func:`_unbound_in_class`).
        """
        if (
            scope is not None
            and point is not None
            and _bound_inside(scope, point, name)
        ):
            return []
        current = scope
        while current is not None:
            written = current.names.get(name)
            if (
                point is not None
                and current.holder is not None
                and _unbound_in_class(module, current.holder, name, point)
            ):
                break
            if written:
                bound = _standing(module, written, point)
                return [target for b in bound for target in self._targets(b)]
            if name in current.params or name in current.locals:
                return [Local(current, name)]
            current = current.parent
        bound = _standing(module, module.names.get(name, []), point)
        return [target for b in bound for target in self._targets(b)]

    def _aliased(self, alias: Alias) -> list[_Target]:
        """What an assignment of a name or a dotted one alone binds its name
        to: what the value stands for where the assignment reads it, in the
        scope that binds the value's first name, the module's or that of the
        function the assignment is written in (an import there, under
        ``global`` too) or of the class body, and as that name stands at the
        assignment; nothing for a name a lambda or a comprehension binds.
        """
        module, target = alias.module, alias.target
        value = assigned_value(module.node, target)
        head = value
        while isinstance(head, ast.Attribute):
            head = head.value
        if not isinstance(head, ast.Name) or id(target) in self._aliasing:
            return []
        how, binder = binding_of(module.node, head, head.id)
        scope: Scope | None = None
        if how != "global" and binder is not None and binder is not module.node:
            scope = self.functions.get(binder) or self._class_bodies.get(binder)
            if scope is None:
                return []
        found: list[_Target] = []
        self._aliasing.add(id(target))
        try:
            if isinstance(value, ast.Name):
                found.extend(self.lookups(value.id, scope, module, value))
            elif value is not None:
                found.append(self.resolve(value, scope, module, value))
        finally:
            self._aliasing.discard(id(target))
        return [target for target in found if target is not None]

    def lookup(
        self,
        name: str,
        scope: Scope | None,
        module: Module,
        point: ast.AST | None = None,
    ) -> _Target:
        """Resolve a bare name the way Python would inside *scope*, where
        *point* reads it, or once the scope has run when it is None.

        None when the bindings it may hold disagree (:meth:`lookups`).
        """
        return _one(self.lookups(name, scope, module, point))

    def resolve(
        self,
        expr: ast.expr,
        scope: Scope | None,
        module: Module,
        point: ast.AST | None = None,
    ) -> _Target:
        """Resolve a name or a dotted module path to what it refers to, its
        first name read where *point* reads it (:meth:`lookup`).
        """
        if isinstance(expr, ast.Name):
            return self.lookup(expr.id, scope, module, point)
        if isinstance(expr, ast.Attribute):
            base = self.resolve(expr.value, scope, module, point)
            if isinstance(base, ModuleRef):
                return self.attribute(base.name, expr.attr)
            if isinstance(base, Class):
                return self.member(base, expr.attr)
        return None

    # -- classes ----------------------------------------------------------

    def _bases(self, klass: Class) -> Iterator[Class]:
        """Each base of *klass* that is a class of the tree: what its name
        stands for where the ``class`` statement reads it (:meth:`resolve`),
        so a base a later ``class`` of its name replaces is the class it was
        when the statement ran.
        """
        for base in klass.node.bases:
            found = self.resolve(base, klass.scope, klass.module, base)
            if isinstance(found, Class):
                yield found

    def linearization(self, klass: Class) -> tuple[Class, ...]:
        """The method resolution order of *klass*, the class first: the C3
        merge Python builds of its bases' orders and the bases themselves,
        those of the tree alone (:meth:`_bases`), read once for each class.
        A class Python cannot linearize, or one reached again while it is
        read, is the class alone.
        """
        found = self._lines.get(klass)
        if found is not None:
            return found
        self._lines[klass] = (klass,)
        bases = list(self._bases(klass))
        order: list[Class] = [klass]
        pending = [list(self.linearization(base)) for base in bases] + [bases]
        pending = [sequence for sequence in pending if sequence]
        while pending:
            chosen = next(
                (
                    sequence[0]
                    for sequence in pending
                    if not any(
                        sequence[0] is later for other in pending for later in other[1:]
                    )
                ),
                None,
            )
            if chosen is None:
                order = [klass]
                break
            order.append(chosen)
            pending = [
                rest
                for sequence in pending
                if (rest := sequence[1:] if sequence[0] is chosen else sequence)
            ]
        found = tuple(order)
        self._lines[klass] = found
        return found

    def member(self, klass: Class, name: str, *, after: bool = False) -> Scope | None:
        """The method *name* of *klass*: that of the first class of its
        method resolution order (:meth:`linearization`) that defines it, or
        with *after*, of the first after *klass*, as ``super()`` reads it.
        """
        for later in self.linearization(klass)[1 if after else 0 :]:
            node = later.members.get(name)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                return self.functions[node]
        return None

    def constructor(self, klass: Class) -> Scope | None:
        """The ``__init__`` a call of *klass* runs, when the tree writes it:
        that of the first class of its method resolution order
        (:meth:`linearization`) with one of its own, written in its body,
        or generated by ``@dataclass``, which the tree does not hold, over
        any its bases write (:func:`_generates_init`).
        """
        for later in self.linearization(klass):
            node = later.members.get("__init__")
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                return self.functions[node]
            if _generates_init(later):
                return None
        return None

    def _field_type(self, klass: Class, name: str, depth: int) -> Class | None:
        """The class an attribute of *klass* holds: as the first class of its
        method resolution order (:meth:`linearization`) that annotates it,
        or defines it as a property, gives it.
        """
        if depth > _DEPTH:
            return None
        for later in self.linearization(klass):
            annotation = later.fields.get(name)
            if annotation is not None:
                return self.annotation_type(
                    annotation, later.scope, later.module, later
                )
            prop = later.members.get(name)
            if isinstance(prop, ast.FunctionDef | ast.AsyncFunctionDef):
                return self.returns(self.functions[prop], later)
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

    def type_of(
        self,
        expr: ast.expr,
        scope: Scope,
        depth: int = 0,
        point: ast.AST | None = None,
    ) -> Class | None:
        """The class of the tree an expression evaluates to, where it can be
        read: its names as they stand where *point* reads them, or once the
        scope has run when it is None. A local's value is read where its
        assignment runs, so a later binding of a name the value reads leaves
        the class the local holds as it was.
        """
        if depth > _DEPTH:
            return None
        if isinstance(expr, ast.Name):
            found = self.lookup(expr.id, scope, scope.module, point)
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
                typed = self.type_of(value, where, depth + 1, value)
                if typed is not None:
                    return typed
            return None
        if isinstance(expr, ast.Call):
            target = self.resolve(expr.func, scope, scope.module, point)
            if isinstance(target, Class):
                return target
            if isinstance(target, Scope):
                return self.returns(target)
            if isinstance(expr.func, ast.Attribute):
                owner = self.type_of(expr.func.value, scope, depth + 1, point)
                method = self.member(owner, expr.func.attr) if owner else None
                if method is not None:
                    return self.returns(method, owner)
            return None
        if isinstance(expr, ast.Attribute):
            owner = self.type_of(expr.value, scope, depth + 1, point)
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
            found = Slot(
                positional.index(PARAMETER),
                keyword=all(a.arg != PARAMETER for a in args.posonlyargs),
            )
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
                if self.callees(call, function):
                    found = Slot(None)
                    break
        self._slots[key] = found
        return found

    def callees(self, call: ast.Call, scope: Scope) -> list[Callee]:
        """The helpers *call* may reach that take the language.

        A name that two bindings may hold, two imports in the branches of a
        ``try`` say, gives one for each that takes it.
        """
        func = call.func
        module = scope.module
        found: list[Callee | None] = []
        if isinstance(func, ast.Name):
            found = [
                self._target_callee(target, func, scope)
                for target in self.lookups(func.id, scope, module, call)
            ]
        elif isinstance(func, ast.Call):
            # ``functools.partial(helper, ax)(...)``, called where it is built,
            # its names read there.
            found = [self._partial_callee(func, scope, module, point=func)]
        elif isinstance(func, ast.Attribute):
            found = self._attribute_callees(call, func, scope)
        unique: list[Callee] = []
        for callee in found:
            if callee is not None and callee not in unique:
                unique.append(callee)
        return unique

    def _target_callee(
        self, target: _Target, func: ast.Name, scope: Scope
    ) -> Callee | None:
        """The helper a name reaches when it stands for *target*."""
        if isinstance(target, Scope):
            return self._callee(target, bound=False)
        if isinstance(target, Class):
            init = self.constructor(target)
            return self._callee(init, bound=True) if init else None
        if isinstance(target, Computed):
            return self._computed_callee(target)
        if isinstance(target, Local):
            typed = self.type_of(func, scope)
            method = self.member(typed, "__call__") if typed else None
            if method is not None:
                return self._callee(method, bound=True)
            return self._value_callee(target)
        return None

    def _attribute_callees(
        self, call: ast.Call, func: ast.Attribute, scope: Scope
    ) -> list[Callee | None]:
        """The helpers ``owner.name(...)`` may reach."""
        if isinstance(func.value, ast.Name) and _bound_inside(
            scope, call, func.value.id
        ):
            return [self._by_name(call, func.attr)]
        base = self.resolve(func.value, scope, scope.module)
        if isinstance(base, ModuleRef):
            found: list[Callee | None] = []
            for target in self.attributes(base.name, func.attr):
                if isinstance(target, Scope):
                    found.append(self._callee(target, bound=False))
                elif isinstance(target, Computed):
                    found.append(self._computed_callee(target))
                elif isinstance(target, Class):
                    init = self.constructor(target)
                    found.append(self._callee(init, bound=True) if init else None)
            return found
        if isinstance(base, Class):
            method = self.member(base, func.attr)
            return [self._callee(method, bound=False) if method else None]
        receiver, after = self._receiver(func.value, scope)
        if receiver is not None:
            method = self.member(receiver, func.attr, after=after)
            return [self._callee(method, bound=not method.static) if method else None]
        return [self._by_name(call, func.attr)]

    def _receiver(self, expr: ast.expr, scope: Scope) -> tuple[Class | None, bool]:
        """The class whose method a call on *expr* reaches, and whether it is
        the method of the first class after it in its method resolution
        order: ``super()`` in a method is the class the method is written in,
        read past itself.
        """
        if (
            isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Name)
            and expr.func.id == "super"
        ):
            current: Scope | None = scope
            while current is not None and current.owner is None:
                current = current.parent
            if current is None or current.owner is None:
                return None, False
            return current.owner, True
        return self.type_of(expr, scope), False

    def _callee(self, function: Scope, *, bound: bool) -> Callee | None:
        slot = self.slot(function, bound=bound)
        return Callee(function.label, (slot,)) if slot is not None else None

    def _binding(
        self,
        name: str,
        scope: Scope | None,
        module: Module,
        point: ast.AST | None = None,
    ) -> Binding | None:
        """The import *name* is bound by, whether or not it is of this tree,
        in *scope*, or at the top of *module* when it is None, where *point*
        reads it, or once the scope has run when it is None
        (:func:`_standing`).
        """
        current = scope
        while current is not None:
            written = current.names.get(name)
            if written:
                return _one_import(_standing(module, written, point))
            if name in current.params or name in current.locals:
                return None
            current = current.parent
        return _one_import(_standing(module, module.names.get(name, []), point))

    def _is_partial(
        self,
        func: ast.expr,
        scope: Scope | None,
        module: Module,
        point: ast.AST | None = None,
    ) -> bool:
        """Whether *func* names ``functools.partial``, imported either way,
        where *point* reads it (:meth:`_binding`).
        """
        if isinstance(func, ast.Name):
            binding = self._binding(func.id, scope, module, point)
            return (
                binding is not None
                and binding.module == "functools"
                and binding.name == "partial"
            )
        if isinstance(func, ast.Attribute) and func.attr == "partial":
            if not isinstance(func.value, ast.Name):
                return False
            binding = self._binding(func.value.id, scope, module, point)
            return (
                binding is not None
                and binding.module == "functools"
                and binding.name is None
            )
        return False

    def _partial_callee(
        self,
        call: ast.Call,
        scope: Scope | None,
        module: Module,
        depth: int = 0,
        point: ast.AST | None = None,
    ) -> Callee | None:
        """``functools.partial(helper, ...)`` reduced to the helper it wraps,
        written in *scope*, or at the top of *module* when it is None, and
        read where *point* reads it.

        The bound arguments shift the slot: ``partial(plot_x, result)`` leaves
        the language one place earlier than ``plot_x`` takes it. A partial that
        binds the language itself, or that spreads a mapping that may hold it,
        forwards it already and is not a call to report.
        """
        if (
            depth > _DEPTH
            or not self._is_partial(call.func, scope, module, point)
            or not call.args
        ):
            return None
        inner = self._expression_callee(call.args[0], scope, module, depth + 1, point)
        if inner is None:
            return None
        if any(k.arg in {PARAMETER, None} for k in call.keywords) and any(
            slot.keyword for slot in inner.slots
        ):
            return None
        bound = len(call.args) - 1
        slots: list[Slot] = []
        for slot in inner.slots:
            if slot.index is None:
                slots.append(slot)
                continue
            if slot.index < bound:
                return None  # the partial already fills the language slot
            slots.append(Slot(slot.index - bound, slot.keyword))
        return Callee(inner.label, tuple(slots))

    def _expression_callee(
        self,
        expr: ast.expr,
        scope: Scope | None,
        module: Module,
        depth: int = 0,
        point: ast.AST | None = None,
    ) -> Callee | None:
        """The helper an expression evaluates to, where it can be read: in
        *scope*, or at the top of *module* when it is None, its names as they
        stand where *point* reads them, or once the scope has run.
        """
        if depth > _DEPTH:
            return None
        if isinstance(expr, ast.Name | ast.Attribute):
            target = self.resolve(expr, scope, module, point)
            if isinstance(target, Scope):
                return self._callee(target, bound=False)
            if isinstance(target, Local):
                return self._value_callee(target, depth + 1)
            if isinstance(target, Computed):
                return self._computed_callee(target, depth + 1)
            return None
        if isinstance(expr, ast.Call):
            return self._partial_callee(expr, scope, module, depth, point)
        return None

    def _computed_callee(self, computed: Computed, depth: int = 0) -> Callee | None:
        """The helper the call an assignment binds a name to makes: what a
        ``functools.partial`` of a helper wraps (:meth:`_partial_callee`),
        its names read in the scope the assignment is written in, as they
        stand there; None for any other call.
        """
        module, target = computed.module, computed.target
        value = assigned_value(module.node, target)
        if not isinstance(value, ast.Call) or id(target) in self._computing:
            return None
        scope: Scope | None = None
        if computed.scope is not module.node:
            scope = self.functions.get(computed.scope) or self._bodies.get(
                computed.scope
            )
            if scope is None:
                return None
        self._computing.add(id(target))
        try:
            return self._partial_callee(value, scope, module, depth, value)
        finally:
            self._computing.discard(id(target))

    def _value_callee(self, local: Local, depth: int = 0) -> Callee | None:
        """The helper a local name holds: an alias, a ``partial`` of one, or a
        parameter's default that names one.

        Each value is read where its assignment runs, its names as they
        stand there, so a later binding of a name the value reads leaves
        what the local holds as it was.
        """
        if depth > _DEPTH:
            return None
        for value in local.scope.values.get(local.name, ()):
            found = self._expression_callee(
                value, local.scope, local.scope.module, depth + 1, value
            )
            if found is not None:
                return found
        default = local.scope.defaults.get(local.name)
        if isinstance(default, ast.Name | ast.Attribute):
            # The default runs once, where the ``def`` does: its name holds
            # what the bindings that may stand there make it.
            if isinstance(default, ast.Name):
                target = _one(
                    self.lookups(
                        default.id, local.scope.parent, local.scope.module, default
                    )
                )
            else:
                target = self.resolve(
                    default, local.scope.parent, local.scope.module, default
                )
            if isinstance(target, Scope):
                return self._callee(target, bound=False)
            if isinstance(target, Local):
                return self._value_callee(target, depth + 1)
            if isinstance(target, Computed):
                return self._computed_callee(target, depth + 1)
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
        """Whether *call* passes the caller's language on to *callee*.

        A keyword, or a ``**`` mapping, reaches only a slot that takes a
        keyword: one of a positional-only language goes to ``**kwargs``.
        """
        by_name = any(slot.keyword for slot in callee.slots)
        for keyword in call.keywords:
            if keyword.arg == PARAMETER and by_name:
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
        return by_name and any(
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
            path = scope.module.path
            shown = (
                path.relative_to(self.root) if path.is_relative_to(self.root) else path
            )
            for call in scope.calls:
                for callee in self.callees(call, scope):
                    if not self.forwards(call, callee, scope):
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
