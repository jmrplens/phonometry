#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the guards that read the repository's own Python files share.

``check_raises_blocks.py`` and ``check_fence_readers.py`` each walk a tree of
files, name a finding by the file and the function that holds it, and keep an
escape hatch keyed the same way, which reports itself once it covers nothing.
The walking, the naming and the hatch live here once, so that the guards agree
on what a key is and a hatch entry written for one reads the same in the other.
``check_boundary_comparisons.py`` keeps a hatch of its own: its key names the
comparison as well as the function, and a line excuses one copy of it, so a
split by ``(file, function)`` would let a new comparison in under an old line.

The guards that follow a call to the function it reaches look its name up as
Python does, and what a scope binds of its own is read here once
(:func:`own_names`, :func:`binding_of`): a function, a lambda, a class body or
a comprehension inside a scope binds its names for itself, and a ``global``
or a ``nonlocal`` statement sends the name out. The guards that read a
name as the strings it stands for find here the scope whose binding a read
or a write reaches (:func:`binding_scope`). Of two statements of one scope
that bind one name, a ``def`` or an import in each branch of an ``if`` or
one after the other, which the name holds at a call, or once the scope has
run, is read here too (:func:`live_bindings`), and which a function written
at a point may meet when it is called, from that point on
(:func:`bindings_from`); what a module's name may hold once the module has
run counts what a function inside it binds the name to under ``global``
(:func:`standing_bindings`).
"""

from __future__ import annotations

import ast
import functools
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Keyed(Protocol):
    """A finding that names its file and the function that holds it."""

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the qualified function."""
        ...


def relative(path: pathlib.Path) -> str:
    """The path as the repository spells it, or as given outside it."""
    resolved = path.resolve()
    return (
        resolved.relative_to(ROOT).as_posix()
        if resolved.is_relative_to(ROOT)
        else path.as_posix()
    )


def python_files(arguments: Sequence[str], default: pathlib.Path) -> list[pathlib.Path]:
    """The files named, the Python files under the directories named, or ``default``'s."""
    if not arguments:
        return sorted(default.rglob("*.py"))
    files: list[pathlib.Path] = []
    for argument in arguments:
        path = pathlib.Path(argument)
        files.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return files


def scoped(tree: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    """Every node with the qualified name of the function or class that holds it.

    A node at module level comes with ``"<module>"``.
    """

    def walk(node: ast.AST, scope: str) -> Iterator[tuple[str, ast.AST]]:
        for child in ast.iter_child_nodes(node):
            inner = scope
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
            yield inner or "<module>", child
            yield from walk(child, inner)

    yield from walk(tree, "")


def exempted[FindingT: Keyed](
    findings: Sequence[FindingT], exempt: Mapping[tuple[str, str], str]
) -> tuple[list[FindingT], list[tuple[str, str]]]:
    """The findings no exemption covers, and the exemptions that cover none.

    :param findings: Every finding, exempt or not.
    :param exempt: The escape hatch, ``(file, function)`` to reason.
    :return: The findings left to report, and the sorted stale keys.
    """
    used = {finding.key for finding in findings}
    kept = [finding for finding in findings if finding.key not in exempt]
    return kept, sorted(set(exempt) - used)


#: The nodes that open a scope of their own: what each binds is its own, and
#: the scope around it does not see it.
SCOPES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.ClassDef,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)

_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass(frozen=True)
class OwnNames:
    """The names one scope binds itself, by how it binds them.

    The scope is a function, a lambda, a class body, a comprehension or the
    module. A ``def`` or a ``class`` written in it binds its name there, and
    an assignment expression (``:=``) in a comprehension in it binds there
    too; anything else a function, a lambda, a class or a comprehension
    inside it binds is theirs, a comprehension's loop targets included.
    """

    #: A function's or a lambda's parameters.
    parameters: frozenset[str]
    #: The functions and classes the scope defines.
    defined: frozenset[str]
    #: The names its imports bind.
    imported: frozenset[str]
    #: Every other name it binds: an assignment, a loop, ``with ... as``,
    #: ``except ... as``, a ``match`` capture, ``del``, ``:=``.
    stored: frozenset[str]
    #: The names a ``global`` statement in it sends to the module.
    declared_global: frozenset[str]
    #: The names a ``nonlocal`` statement in it sends to the function around.
    declared_nonlocal: frozenset[str]
    #: The names a function or a class body annotates without a value
    #: (``flag: type``): its own, as Python makes them, though the annotation
    #: binds nothing to them. The module's annotation makes no name its own.
    annotated: frozenset[str] = frozenset()
    #: The type parameters of a generic function or class (``def f[T]``,
    #: ``class Box[T]``), which its body reads, and a generic class's methods
    #: too (:func:`binding_of`).
    type_parameters: frozenset[str] = frozenset()

    def binds(self, name: str) -> bool:
        """Whether *name* is the scope's own: bound in it, annotated in a
        function or a class body, or a type parameter of it, and not declared
        ``global`` or ``nonlocal`` there.
        """
        if name in self.declared_global or name in self.declared_nonlocal:
            return False
        return (
            name in self.parameters
            or name in self.defined
            or name in self.imported
            or name in self.stored
            or name in self.annotated
            or name in self.type_parameters
        )

    def rebinds(self, name: str) -> bool:
        """Whether the scope declares *name* ``global`` and binds it all the
        same, so that the module's name stands, at a call, for what the
        module bound or for what the scope put there.
        """
        return name in self.declared_global and (
            name in self.defined or name in self.imported or name in self.stored
        )

    def how(self, name: str) -> Literal["definition", "import", "binding"]:
        """How the scope binds *name*, which :meth:`binds` says it does.

        ``"definition"`` and ``"import"`` when that is the only way it does,
        an annotation without a value aside, which binds nothing;
        ``"binding"`` for a parameter, any other binding, a name bound two
        ways, which may stand for either at a call, and a name only
        annotated.
        """
        if (
            name in self.parameters
            or name in self.stored
            or name in self.type_parameters
        ):
            return "binding"
        if name in self.defined and name not in self.imported:
            return "definition"
        if name in self.imported and name not in self.defined:
            return "import"
        return "binding"


def _parameter_names(scope: ast.AST) -> frozenset[str]:
    """The parameters of a function or a lambda; none for any other scope."""
    if not isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
        return frozenset()
    arguments = scope.args
    return frozenset(
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


def _type_parameter_names(scope: ast.AST) -> frozenset[str]:
    """The type parameters of a generic function or class; none for any other scope."""
    if not isinstance(scope, _DEFINITIONS):
        return frozenset()
    return frozenset(
        parameter.name
        for parameter in scope.type_params
        if isinstance(parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple)
    )


def parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
) -> list[tuple[ast.arg, ast.expr | None]]:
    """Each parameter of a function or a lambda with its default, ``None`` for
    one that has none, in the order of the signature.

    The defaults of the positional parameters belong to the last of them;
    ``*args`` and ``**kwargs`` have none. A default runs in the scope around
    the function, once, where it is defined.
    """
    arguments = function.args
    positional = [*arguments.posonlyargs, *arguments.args]
    missing = len(positional) - len(arguments.defaults)
    defaults: list[ast.expr | None] = [None] * missing
    defaults.extend(arguments.defaults)
    found = list(zip(positional, defaults, strict=True))
    found.extend(zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True))
    found.extend(
        (extra, None) for extra in (arguments.vararg, arguments.kwarg) if extra
    )
    return found


def _opening(scope: ast.AST) -> list[ast.AST]:
    """The nodes a scope runs as its own, before any scope inside it is left out.

    A comprehension's first iterable is read in the scope around it, the
    rest of the comprehension in its own.
    """
    if isinstance(scope, _COMPREHENSIONS):
        generators = scope.generators
        own: list[ast.AST] = [
            *(
                [scope.key, scope.value]
                if isinstance(scope, ast.DictComp)
                else [scope.elt]
            ),
            *(generator.target for generator in generators),
            *(condition for generator in generators for condition in generator.ifs),
            *(generator.iter for generator in generators[1:]),
        ]
        return own
    if isinstance(scope, ast.Lambda):
        return [scope.body]
    body = getattr(scope, "body", [])
    return list(body) if isinstance(body, list) else [body]


def _same_scope(node: ast.AST) -> list[ast.AST]:
    """The children of *node* that run in the scope *node* runs in.

    A ``def``'s decorators and defaults, a ``class``'s decorators and
    bases, a lambda's defaults and a comprehension's first iterable run
    around them; their bodies do not, nor does the name ``:=`` stores in
    (:func:`own_names` reads it).
    """
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
        arguments = node.args
        outer: list[ast.AST] = [
            *arguments.defaults,
            *(default for default in arguments.kw_defaults if default is not None),
        ]
        if not isinstance(node, ast.Lambda):
            outer.extend(node.decorator_list)
        return outer
    if isinstance(node, ast.ClassDef):
        return [
            *node.decorator_list,
            *node.bases,
            *(keyword.value for keyword in node.keywords),
        ]
    if isinstance(node, _COMPREHENSIONS):
        return [node.generators[0].iter]
    if isinstance(node, ast.NamedExpr):
        return [node.value]
    return list(ast.iter_child_nodes(node))


def scope_nodes(scope: ast.AST) -> list[ast.AST]:
    """Every node *scope* runs as its own, a scope inside it met but not entered."""
    found: list[ast.AST] = []
    pending = _opening(scope)
    while pending:
        node = pending.pop()
        found.append(node)
        pending.extend(_same_scope(node))
    return found


def _walrus_targets(comprehension: ast.AST) -> set[str]:
    """The names ``:=`` stores in inside a comprehension, which the scope around binds.

    Through the comprehensions nested in it, not through a function, a
    lambda or a class written in it.
    """
    found: set[str] = set()
    pending = list(ast.iter_child_nodes(comprehension))
    while pending:
        node = pending.pop()
        if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
            found.add(node.target.id)
        if not isinstance(node, (*_DEFINITIONS, ast.Lambda)):
            pending.extend(ast.iter_child_nodes(node))
    return found


def imported_names(node: ast.Import | ast.ImportFrom) -> set[str]:
    """The names an import statement binds."""
    if isinstance(node, ast.Import):
        return {alias.asname or alias.name.partition(".")[0] for alias in node.names}
    return {alias.asname or alias.name for alias in node.names if alias.name != "*"}


def _captured(node: ast.AST) -> str | None:
    """The name a ``match`` pattern captures, if it captures one."""
    if isinstance(node, ast.MatchAs | ast.MatchStar):
        return node.name
    if isinstance(node, ast.MatchMapping):
        return node.rest
    return None


def _declared(node: ast.AST) -> tuple[str, set[str]] | None:
    """The field of :class:`OwnNames` a definition, an import, a ``global``
    or a ``nonlocal`` statement binds names in, and which; ``None`` for any
    other node.
    """
    if isinstance(node, _DEFINITIONS):
        return "defined", {node.name}
    if isinstance(node, ast.Import | ast.ImportFrom):
        return "imported", imported_names(node)
    if isinstance(node, ast.Global):
        return "declared_global", set(node.names)
    if isinstance(node, ast.Nonlocal):
        return "declared_nonlocal", set(node.names)
    return None


def _annotated_only(nodes: Sequence[ast.AST]) -> set[int]:
    """The ids of the names among *nodes* that an annotation without a value
    targets (``flag: type``), which binds nothing to the name.
    """
    return {
        id(node.target)
        for node in nodes
        if isinstance(node, ast.AnnAssign)
        and node.value is None
        and isinstance(node.target, ast.Name)
    }


def _stored(node: ast.AST, *, comprehension: bool) -> set[str]:
    """The names any other binding of *node* stores in, in the scope it runs in.

    *comprehension* says the scope is a comprehension, which binds no name
    an assignment expression in it stores: the scope around it does.
    """
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del):
        return {node.id}
    if isinstance(node, ast.ExceptHandler) and node.name:
        return {node.name}
    if comprehension:
        return set()
    if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        return {node.target.id}
    if isinstance(node, _COMPREHENSIONS):
        return _walrus_targets(node)
    captured = _captured(node)
    return {captured} if captured is not None else set()


@functools.cache
def own_names(scope: ast.AST) -> OwnNames:
    """What *scope* binds of its own (:class:`OwnNames`).

    Read once for each scope, as every name a guard looks up in it asks; a
    guard reads every function of the package again on each pass of its
    fixed point, so no bounded cache would keep them.
    """
    found: dict[str, set[str]] = {
        "defined": set(),
        "imported": set(),
        "stored": set(),
        "declared_global": set(),
        "declared_nonlocal": set(),
        "annotated": set(),
    }
    comprehension = isinstance(scope, _COMPREHENSIONS)
    nodes = scope_nodes(scope)
    bare = _annotated_only(nodes)
    for node in nodes:
        declared = _declared(node)
        if declared is not None:
            found[declared[0]].update(declared[1])
        elif isinstance(node, ast.Name) and id(node) in bare:
            # A function's annotation makes the name local, and a class
            # body's keeps the name of the function around from it; the
            # module's name is the module's either way.
            if not isinstance(scope, ast.Module):
                found["annotated"].add(node.id)
        else:
            found["stored"].update(_stored(node, comprehension=comprehension))
    return OwnNames(
        _parameter_names(scope),
        frozenset(found["defined"]),
        frozenset(found["imported"]),
        frozenset(found["stored"]),
        frozenset(found["declared_global"]),
        frozenset(found["declared_nonlocal"]),
        frozenset(found["annotated"]),
        _type_parameter_names(scope),
    )


def bindings_by_name(scope: ast.AST) -> dict[str, list[ast.AST]]:
    """Each name *scope* binds itself, with every node that binds it, in the
    order of the source.

    A ``def`` or a ``class`` statement, an import statement, and the node of
    every other binding :class:`OwnNames` reads: an assignment's target, a
    loop's, ``with ... as``, ``except ... as``, a ``match`` capture, ``del``
    and ``:=``. An annotation without a value (``flag: type``) binds nothing,
    and the name keeps what it held. A name the scope declares ``global`` or
    ``nonlocal`` is another scope's, and is left out. What the name holds
    where it is read is :func:`live_bindings` of the nodes.
    """
    names = own_names(scope)
    sent_out = names.declared_global | names.declared_nonlocal
    return {
        name: nodes
        for name, nodes in _binding_nodes(scope).items()
        if name not in sent_out
    }


def _binding_nodes(scope: ast.AST) -> dict[str, list[ast.AST]]:
    """Each name a statement of *scope* binds, its ``global`` and
    ``nonlocal`` names among them, with every node that binds it, in the
    order of the source (:func:`bindings_by_name`).
    """
    comprehension = isinstance(scope, _COMPREHENSIONS)
    found: dict[str, list[ast.AST]] = {}
    nodes = scope_nodes(scope)
    bare = _annotated_only(nodes)
    for node in nodes:
        if id(node) in bare:
            continue
        declared = _declared(node)
        if declared is None:
            bound = _stored(node, comprehension=comprehension)
        else:
            bound = declared[1] if declared[0] in {"defined", "imported"} else set()
        for name in bound:
            found.setdefault(name, []).append(node)
    for nodes in found.values():
        nodes.sort(key=_position)
    return found


def _position(node: ast.AST) -> tuple[int, int]:
    """Where *node* is written: its line and its column."""
    return getattr(node, "lineno", 0), getattr(node, "col_offset", 0)


@functools.cache
def global_bindings(module: ast.Module) -> dict[str, list[ast.AST]]:
    """Each name of *module* that a function, a method or a class body inside
    it declares ``global`` and binds, with every node that binds it there,
    in the order of the source.

    Such a scope may run at any time once it is defined, before a call into
    the module or after it has run, so each of these may be what the
    module's name holds then (:func:`standing_bindings`).
    """
    found: dict[str, list[ast.AST]] = {}
    for scope in ast.walk(module):
        if not isinstance(scope, _DEFINITIONS):
            continue
        sent = own_names(scope).declared_global
        for name, nodes in _binding_nodes(scope).items():
            if name in sent:
                found.setdefault(name, []).extend(nodes)
    for nodes in found.values():
        nodes.sort(key=_position)
    return found


def standing_bindings(
    module: ast.Module, bindings: Mapping[str, Sequence[ast.AST]] | None = None
) -> dict[str, list[ast.AST]]:
    """Each name *module* binds, with every binding of it that may stand once
    the module has run.

    Of the bindings at the top of the module (:func:`bindings_by_name`, or
    *bindings* when given, a part of them), those :func:`live_bindings`
    keeps: the later of two in a row, either of two in the branches of an
    ``if`` or a ``try``. And every binding a function, a method or a class
    body inside the module makes of the name under ``global``
    (:func:`global_bindings`), which may have run by then.
    """
    own = bindings_by_name(module) if bindings is None else bindings
    inside = global_bindings(module)
    found: dict[str, list[ast.AST]] = {}
    for name in [*own, *(name for name in inside if name not in own)]:
        nodes = list(own.get(name, ()))
        live = nodes if len(nodes) < 2 else live_bindings(module, nodes)
        found[name] = [*live, *inside.get(name, ())]
    return found


@functools.cache
def _parents(root: ast.AST) -> dict[ast.AST, ast.AST]:
    """Each node under *root* with the node that holds it, read once for each root."""
    return {
        child: node for node in ast.walk(root) for child in ast.iter_child_nodes(node)
    }


def _runs_inside(scope: ast.AST, child: ast.AST, grandchild: ast.AST | None) -> bool:
    """Whether *child* of *scope*, on the way to a node, runs in *scope*'s own namespace.

    A ``def``'s or a ``class``'s body does, its decorators, defaults and
    bases do not; a comprehension's first iterable does not either.
    """
    if isinstance(scope, _COMPREHENSIONS):
        first = scope.generators[0]
        return not (child is first and grandchild is first.iter)
    if isinstance(scope, ast.Lambda):
        return child is scope.body
    return any(child is statement for statement in getattr(scope, "body", ()))


def scopes_around(root: ast.AST, node: ast.AST) -> list[ast.AST]:
    """The scopes a name read at *node* is looked up in, innermost first, up to *root*.

    Each function, lambda, comprehension and class body inside *root* that
    *node* runs in, then *root* itself. A class body is left out once a
    function, a lambda or a comprehension lies between it and *node*, as
    Python leaves it out.
    """
    return [scope for scope, crossed in _lookup_scopes(root, node) if not crossed]


def _lookup_scopes(root: ast.AST, node: ast.AST) -> list[tuple[ast.AST, bool]]:
    """:func:`scopes_around`, each scope with whether a function, a lambda or
    a comprehension lies between it and *node*, kept for a generic class
    then: its methods read its type parameters, though not its other names.
    """
    parents = _parents(root)
    found: list[tuple[ast.AST, bool]] = []
    crossed = False
    grandchild: ast.AST | None = None
    child = node
    current = parents.get(node)
    while current is not None and current is not root:
        if isinstance(current, SCOPES) and _runs_inside(current, child, grandchild):
            skipped = isinstance(current, ast.ClassDef) and crossed
            if not skipped or _type_parameter_names(current):
                found.append((current, skipped))
            crossed = crossed or not isinstance(current, ast.ClassDef)
        grandchild, child, current = child, current, parents.get(current)
    skipped = isinstance(root, ast.ClassDef) and crossed
    if not skipped or _type_parameter_names(root):
        found.append((root, skipped))
    return found


def binding_of(
    root: ast.AST, node: ast.AST, name: str
) -> tuple[
    Literal["definition", "import", "binding", "global", "outside"], ast.AST | None
]:
    """How *name*, read at *node*, is bound inside *root*, and by which scope.

    The scopes around *node* are read innermost first (:func:`scopes_around`):
    the first that binds the name says how (:meth:`OwnNames.how`), a type
    parameter of a generic function or class among its bindings, which a
    method of a generic class reads too; one that declares it ``global``
    sends it to the module (``"global"``), unless it binds it too
    (:meth:`OwnNames.rebinds`), and one that declares it ``nonlocal`` passes
    it on outwards. ``"outside"`` when no scope up to *root* binds it.
    """
    for scope, crossed in _lookup_scopes(root, node):
        names = own_names(scope)
        if crossed:
            # A method reads its generic class's type parameters alone.
            if name in names.type_parameters:
                return "binding", scope
            continue
        if names.rebinds(name):
            return "binding", scope
        if name in names.declared_global:
            return "global", None
        if names.binds(name):
            return names.how(name), scope
    return "outside", None


def forget_trees() -> None:
    """Let go of every tree the scopes and the blocks were read from.

    What :func:`own_names`, :func:`binding_of` and :func:`live_bindings` read
    of a tree is kept for as long as the process runs, which a guard that
    reads one package again on each pass of its fixed point needs; a guard
    that reads each file once calls this when it is done with the file, so
    that the trees of a whole directory are not all kept at once.
    """
    for cached in (own_names, _parents, _blocks, _class_is_live, global_bindings):
        cached.cache_clear()


def binding_scope(root: ast.Module, node: ast.AST, name: str) -> ast.AST:
    """The scope whose binding of *name* a read or a write at *node* reaches.

    The scope :func:`binding_of` finds: a ``:=`` in a comprehension reaches
    the function around it, a name a scope declares ``nonlocal`` the
    function that binds it, and a method passes over the class body around
    it. The module, *root*, for a name declared ``global`` where it is read
    or written, and for one no scope around *node* binds, which the module
    stands for once a function has declared it ``global`` and bound it.
    """
    scope = binding_of(root, node, name)[1]
    if scope is None or name in own_names(scope).declared_global:
        return root
    return scope


#: The compound statements: those whose blocks hold statements of the scope
#: they are written in.
COMPOUND_STATEMENTS = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.TryStar,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


def block_statements(node: ast.AST) -> list[ast.stmt]:
    """The statements of every block a compound statement holds, in the order
    of the source: its body, each ``except`` clause's and each ``case``'s
    body, its ``else`` and its ``finally``; none for any other node.

    A walker that lists the blocks itself forgets one sooner or later: a
    ``match``, a ``try`` with ``except*``, an ``async for`` or an ``async
    with`` were each missing from one guard or another.
    """
    if not isinstance(node, COMPOUND_STATEMENTS):
        return []
    found: list[ast.stmt] = []
    for field in ("body", "handlers", "cases", "orelse", "finalbody"):
        for child in getattr(node, field, None) or []:
            if isinstance(child, ast.ExceptHandler | ast.match_case):
                found.extend(child.body)
            else:
                found.append(child)
    return found


#: The fields of a node that hold a block of statements: a compound
#: statement's, an ``except`` clause's and a ``case``'s.
_BLOCKS = ("body", "orelse", "finalbody", "handlers", "cases")

#: The order a ``try``, a loop or an ``if`` runs its blocks in: a block runs
#: after those of a lower rank of the same statement, when it runs at all.
_RANK = {"body": 0, "handlers": 1, "orelse": 2, "finalbody": 3}

#: The scopes whose bodies are blocks of statements: where a binding is read.
_STATEMENT_SCOPES = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

#: One block a statement is written in: the node whose field holds it, the
#: field, and the place of the statement (or of the clause around it) there.
type Frame = tuple[ast.AST, str, int]


@functools.cache
def _blocks(root: ast.AST) -> dict[ast.AST, Frame]:
    """Each statement under *root*, and each ``except`` clause and ``case``,
    with the block that holds it; read once for each root, through the
    blocks alone, never into an expression.
    """
    found: dict[ast.AST, Frame] = {}
    pending = [root]
    while pending:
        holder = pending.pop()
        for field in _BLOCKS:
            block = getattr(holder, field, None)
            if not isinstance(block, list):
                continue
            for index, item in enumerate(block):
                found[item] = (holder, field, index)
                pending.append(item)
    return found


def _frames(root: ast.AST, node: ast.AST) -> tuple[Frame, ...]:
    """The blocks *node* is written in, outermost first, up to its scope.

    The scope is the function, the class body or the module whose own
    statements hold *node*; an expression is read in the statement that
    holds it, through a lambda or a comprehension around it, which holds no
    statement.
    """
    blocks = _blocks(root)
    current: ast.AST | None = node
    if current not in blocks:
        parents = _parents(root)
        while current is not None and current not in blocks:
            current = parents.get(current)
    found: list[Frame] = []
    while current is not None and current in blocks:
        frame = blocks[current]
        found.append(frame)
        current = None if isinstance(frame[0], _STATEMENT_SCOPES) else frame[0]
    return tuple(reversed(found))


def _shared(one: Sequence[Frame], other: Sequence[Frame]) -> int:
    """How many blocks, from the outside in, *one* and *other* are written in alike."""
    count = 0
    for mine, theirs in zip(one, other, strict=False):
        if mine[0] is not theirs[0] or mine[1:] != theirs[1:]:
            break
        count += 1
    return count


def _runs_into(holder: ast.AST, field: str, later: str) -> bool:
    """Whether a statement of block *field* of *holder* may run before one of
    its block *later*: not across the branches of an ``if``, nor from an
    ``except`` clause to the ``else`` of a ``try``, which never both run.
    """
    if isinstance(holder, ast.If) or {field, later} == {"handlers", "orelse"}:
        return False
    return _RANK.get(field, 0) < _RANK.get(later, 0)


def _may_run_before(binding: Sequence[Frame], point: Sequence[Frame]) -> bool:
    """Whether a statement written at *binding* may run before *point* does.

    Before it in a block they share, or in a block of their statement that
    runs first. Not when one holds the other, a binding in the body of the
    statement whose header reads the name; nor between two ``except``
    clauses or two ``case`` blocks, of which one runs.
    """
    shared = _shared(binding, point)
    if shared in {len(binding), len(point)}:
        return False
    holder, field, index = binding[shared]
    _, other, place = point[shared]
    if field == other:
        return field not in {"handlers", "cases"} and index < place
    return _runs_into(holder, field, other)


#: The loops: a statement in the body of one may run again after a later one.
_LOOPS = (ast.For, ast.AsyncFor, ast.While)

#: The statements whose own body an exception may leave and the program go
#: on after them: a ``try`` catches it, a ``with`` may hand it to a context
#: manager that swallows it.
_CATCHING = (ast.Try, ast.TryStar, ast.With, ast.AsyncWith)

#: The definitions a jump inside them belongs to: never one of the scope around.
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _may_be_caught(later: Sequence[Frame], point: Sequence[Frame] | None) -> bool:
    """Whether an exception raised on the way to the binding at *later* may be
    caught and the scope go on to *point* without it.

    The body of a ``try`` or a ``with`` around *later* may be left that way;
    so may an ``except`` clause or the ``else`` of a ``try`` whose
    ``finally`` holds *point*, which runs on the way out.
    """
    for depth, (holder, field, _) in enumerate(later):
        if isinstance(holder, _CATCHING) and field == "body":
            return True
        if (
            isinstance(holder, ast.Try | ast.TryStar)
            and field in {"handlers", "orelse"}
            and point is not None
            and len(point) > depth
            and _shared(point, later) >= depth
            and point[depth][:2] == (holder, "finalbody")
        ):
            return True
    return False


def _jumps(statements: Sequence[ast.AST], *, returns: bool) -> bool:
    """Whether *statements* hold a ``break`` or a ``continue`` of a loop around
    them, or, with *returns*, a ``return``: a jump past what follows them.

    A ``break`` or a ``continue`` in the body of a loop among them belongs to
    that loop; a ``return`` there still leaves the scope.
    """
    pending = [(statement, False) for statement in statements]
    while pending:
        node, looped = pending.pop()
        if isinstance(node, ast.Return):
            if returns:
                return True
        elif isinstance(node, ast.Break | ast.Continue):
            if not looped:
                return True
        elif not isinstance(node, _DEFINITIONS):
            pending.extend(_inner_statements(node, looped=looped))
    return False


def _inner_statements(node: ast.AST, *, looped: bool) -> Iterator[tuple[ast.AST, bool]]:
    """The statements of each block of *node*, each with whether a loop among
    them or around them, *looped*, holds it.
    """
    for field in _BLOCKS:
        block = getattr(node, field, None)
        if isinstance(block, list):
            inner = looped or (isinstance(node, _LOOPS) and field == "body")
            yield from ((child, inner) for child in block)


def _later_in_block(statement: Sequence[Frame], point: Sequence[Frame] | None) -> bool:
    """Whether *point* is written after the statement at *statement* in the
    block that holds it, or inside a later statement of that block.

    A block is entered at its top, and whatever leaves it before *point*
    (an exception, a ``break``, a ``continue``, a ``return``) leaves *point*
    behind too, so every way to *point* runs the statement first.
    """
    depth = len(statement) - 1
    if point is None or len(point) <= depth or _shared(point, statement) < depth:
        return False
    _, field, index = statement[depth]
    _, read_in, read_at = point[depth]
    return read_in == field and read_at > index


def _replaces(
    later: Sequence[Frame], earlier: Sequence[Frame], point: Sequence[Frame] | None
) -> bool:
    """Whether the binding at *later* runs after the one at *earlier* on every
    way from it to *point*, or to the end of the scope when *point* is None.

    *later* sits after *earlier*, or after the statement that holds it, in a
    block they share. A *point* later in that block is reached only through
    *later* (:func:`_later_in_block`). Elsewhere, nothing between the two
    may skip *later*: an exception that a ``try`` or a ``with`` around it
    may catch (:func:`_may_be_caught`), a ``break`` or a ``continue``, or a
    ``return`` before the end of the scope (:func:`_jumps`). A *point*
    between them in that block is reached before *later* runs; one outside
    the statement that holds the block, or in a block of it that runs
    after, is reached after.
    """
    depth = len(later) - 1
    holder, field, index = later[-1]
    if len(earlier) <= depth or _shared(later, earlier) < depth:
        return False
    _, written_in, place = earlier[depth]
    if written_in != field or place >= index:
        return False
    if _later_in_block(later, point):
        return True
    between = getattr(holder, field)[place:index]
    if _may_be_caught(later, point) or _jumps(between, returns=point is None):
        return False
    if point is None or len(point) <= depth or _shared(point, later) < depth:
        return True
    _, read_in, read_at = point[depth]
    return read_in != field or read_at > index


def _turns_back(binding: Sequence[Frame], point: Sequence[Frame]) -> int | None:
    """The depth of the innermost loop on whose earlier turn the binding at
    *binding* may run before *point*, or None when no loop takes it there.

    Both written in the body of the loop, or the binding in the body of a
    ``while`` whose test holds *point*, which reads it again after each turn.
    """
    shared = _shared(binding, point)
    found = None
    for depth in range(min(shared + 1, len(binding), len(point))):
        holder, field, _ = binding[depth]
        if isinstance(holder, _LOOPS) and field == "body" == point[depth][1]:
            found = depth
    if shared == len(point) < len(binding):
        holder, field, _ = binding[shared]
        if isinstance(holder, ast.While) and field == "body":
            found = shared
    return found


def _runs_each_turn(
    binding: Sequence[Frame], point: Sequence[Frame], loop: int
) -> bool:
    """Whether the binding at *binding* runs before *point* on every turn of
    the loop at depth *loop* that reaches it: written straight in a block
    that holds *point*, before it, inside that loop's body.

    A block is entered at its top, so what it holds before the statement
    around *point* has run whenever *point* is reached from it.
    """
    depth = len(binding) - 1
    if depth < loop or len(point) <= depth or _shared(binding, point) < depth:
        return False
    _, field, index = binding[depth]
    _, read_in, read_at = point[depth]
    return field == read_in and index < read_at


def live_bindings[NodeT: ast.AST](
    root: ast.AST, bindings: Sequence[NodeT], point: ast.AST | None = None
) -> list[NodeT]:
    """Of *bindings*, statements of one scope under *root* that bind one name
    (a ``def`` of it, an import of it), those the name may hold at *point*,
    or once the scope has run to its end when *point* is None.

    A binding that runs before the point and that no other one replaces on
    the way to it (:func:`_replaces`): one in each branch of an ``if`` is
    either, and a later one in a block that holds an earlier one, or the
    statement around it, replaces it. A binding in the body of a loop that
    holds the point may run before it on an earlier turn (:func:`_turns_back`),
    unless another one runs before the point on every turn
    (:func:`_runs_each_turn`). When none runs before the point (a call read
    before any binding of its scope), every one may be what it holds.

    A point inside a scope nested in the bindings' (:func:`_lifted`) is read
    where that scope is written: a class body or a list comprehension runs
    there, and a function, a lambda or a generator expression runs when it
    is called or consumed, so it meets every binding from there on
    (:func:`bindings_from`).
    """
    if point is not None and bindings:
        point, deferred = _lifted(root, bindings[0], point)
        if deferred:
            return _met_from(root, bindings, point)
    return _held_at(root, bindings, point)


def _held_at[NodeT: ast.AST](
    root: ast.AST, bindings: Sequence[NodeT], point: ast.AST | None
) -> list[NodeT]:
    """:func:`live_bindings` at a *point* written in the bindings' own scope."""
    frames = {binding: _frames(root, binding) for binding in bindings}
    target = _frames(root, point) if point is not None else None
    forward = [
        binding
        for binding in bindings
        if target is None or _may_run_before(frames[binding], target)
    ]
    live = [
        binding
        for binding in forward
        if not any(
            other is not binding and _replaces(frames[other], frames[binding], target)
            for other in forward
        )
    ]
    if target is not None:
        live.extend(_back_from_a_turn(bindings, frames, target, forward))
    return live or list(bindings)


def _back_from_a_turn[NodeT: ast.AST](
    bindings: Sequence[NodeT],
    frames: Mapping[NodeT, tuple[Frame, ...]],
    target: Sequence[Frame],
    forward: Sequence[NodeT],
) -> list[NodeT]:
    """Of *bindings* not in *forward*, those an earlier turn of a loop around
    *target* may leave in place there (:func:`_turns_back`).

    Not one that another binding of the same loop replaces before the turn
    ends (:func:`_replaces`), nor any when a binding runs before *target* on
    every turn (:func:`_runs_each_turn`).
    """
    turns = {
        binding: loop
        for binding in bindings
        if binding not in forward
        and (loop := _turns_back(frames[binding], target)) is not None
    }
    return [
        binding
        for binding, loop in turns.items()
        if not any(_runs_each_turn(frames[other], target, loop) for other in bindings)
        and not any(
            other is not binding
            and turns[other] == loop
            and _replaces(frames[other], frames[binding], None)
            for other in turns
        )
    ]


#: The statements that bind every name they bind each time they run.
_SURE_BINDINGS = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Import, ast.ImportFrom)


def runs_before(root: ast.AST, binding: ast.AST, point: ast.AST) -> bool:
    """Whether the binding at *binding* runs on every way to *point*, a read
    in the same scope.

    The binding is an assignment or an import, the name a target of it or
    one it imports, written straight in a block that holds the statement of
    *point*, before it; not a loop's target or a ``:=``, which may not run,
    nor an annotation without a value, which binds nothing.
    A block is entered at its top and an exception leaves it whole, so a
    read later in the block, or in a later statement of it, is reached only
    once the binding has run, in the body of a ``try`` or a ``with`` too; a
    read after that statement is not in the block, and an exception the
    statement catches before the binding ran may reach it.
    """
    frames = _frames(root, binding)
    target = _frames(root, point)
    if not frames or not target:
        return False
    holder, field, index = frames[-1]
    statement = getattr(holder, field)[index]
    if not isinstance(statement, _SURE_BINDINGS) or _annotates_only(statement):
        return False
    if binding is not statement and not any(
        binding is target_name
        for written in _assigned_targets(statement)
        for target_name in ast.walk(written)
    ):
        return False
    return _later_in_block(frames, target)


def _annotates_only(statement: ast.stmt) -> bool:
    """Whether *statement* annotates a name without a value (``flag: type``)."""
    return isinstance(statement, ast.AnnAssign) and statement.value is None


def _assigned_targets(statement: ast.stmt) -> list[ast.expr]:
    """The targets an assignment statement stores in; none for an import."""
    if isinstance(statement, ast.Assign):
        return list(statement.targets)
    if isinstance(statement, ast.AnnAssign | ast.AugAssign):
        return [statement.target]
    return []


def bindings_from[NodeT: ast.AST](
    root: ast.AST, bindings: Sequence[NodeT], point: ast.AST | None
) -> list[NodeT]:
    """Of *bindings*, statements of one scope under *root* that bind one name,
    those the name may hold at *point* or at any moment after it while the
    scope runs, and once it has run; those it holds once the scope has run
    when *point* is None.

    What a function, a lambda or a generator expression written at *point*
    reads of the name: it reads it when it is called or consumed, which may
    be at once, before a later binding, or once the scope has run.
    """
    if point is None or not bindings:
        return _held_at(root, bindings, None)
    point, _ = _lifted(root, bindings[0], point)
    return _met_from(root, bindings, point)


#: The scopes that run when they are called or consumed, not where they are
#: written.
_DEFERRED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.GeneratorExp)


def _lifted(root: ast.AST, binding: ast.AST, point: ast.AST) -> tuple[ast.AST, bool]:
    """Where the scope that holds *binding* reads a name read at *point*, and
    whether it reads it later than that.

    *point* itself when it runs in that scope; otherwise the function, the
    class, the lambda or the comprehension written there that it runs in,
    and whether a function, a lambda or a generator expression lies on the
    way, which runs when it is called or consumed. A ``def``'s defaults and
    decorators, a class's bases and a comprehension's first iterable run
    where they are written (:func:`_runs_inside`).
    """
    scope = _scope_holding(root, binding)
    parents = _parents(root)
    lifted, deferred = point, False
    grandchild: ast.AST | None = None
    child = point
    current = parents.get(point)
    while current is not None and current is not scope:
        if isinstance(current, SCOPES) and _runs_inside(current, child, grandchild):
            lifted = current
            deferred = deferred or isinstance(current, _DEFERRED)
        grandchild, child, current = child, current, parents.get(current)
    if current is None:
        return point, False
    return lifted, deferred


def _met_from[NodeT: ast.AST](
    root: ast.AST, bindings: Sequence[NodeT], point: ast.AST
) -> list[NodeT]:
    """Those the name holds at *point*, written in the bindings' own scope
    (:func:`_held_at`), and every one that may run after it
    (:func:`_may_run_after`).
    """
    live = _held_at(root, bindings, point)
    target = _frames(root, point)
    return [
        binding
        for binding in bindings
        if any(binding is other for other in live)
        or _may_run_after(_frames(root, binding), target)
    ]


def _may_run_after(binding: Sequence[Frame], point: Sequence[Frame]) -> bool:
    """Whether a statement written at *binding* may run after *point* does.

    After it in a block they share, or in a block of their statement that
    runs after (:func:`_may_run_before`, read the other way); on a later
    turn of a loop whose body holds both (:func:`_turns_back`); and in the
    body of the statement whose header holds *point*, or as the statement
    that holds *point* itself, a loop's target bound again on its next turn.
    """
    shared = _shared(binding, point)
    return (
        shared in {len(binding), len(point)}
        or _may_run_before(point, binding)
        or _turns_back(binding, point) is not None
    )


def _scope_holding(root: ast.AST, node: ast.AST) -> ast.AST:
    """The module, function or class body whose own statements hold *node*."""
    frames = _frames(root, node)
    return frames[0][0] if frames else root


@functools.cache
def _class_is_live(root: ast.AST, node: ast.AST) -> bool:
    """Whether *node*, when it is a ``class`` statement, is what its name holds
    once the scope around it has run, and so is every class around it.

    Of two ``class`` statements of one name in one scope, one in each branch
    of an ``if`` is either and a later one replaces an earlier one it always
    follows (:func:`live_bindings`). Any other node is live.
    """
    if not isinstance(node, ast.ClassDef):
        return True
    scope = _scope_holding(root, node)
    namesakes = [
        statement
        for statement in _blocks(root)
        if isinstance(statement, ast.ClassDef)
        and statement.name == node.name
        and _scope_holding(root, statement) is scope
    ]
    return node in live_bindings(root, namesakes) and _class_is_live(root, scope)


def live_class_members[NodeT: ast.AST](
    root: ast.AST, bindings: Sequence[NodeT]
) -> list[NodeT]:
    """Of *bindings*, definitions of one qualified name under *root* (a
    function of the module, or a method of a class, which two ``class``
    statements of one name may each define), those the name holds once the
    module has run.

    Each class is read first, in the scope that holds it
    (:func:`_class_is_live`), and only the definitions of a live class are
    read against one another (:func:`live_bindings`): the methods of two
    classes of one name share no block, so read together each would be kept.
    """
    by_scope: dict[ast.AST, list[NodeT]] = {}
    for binding in bindings:
        by_scope.setdefault(_scope_holding(root, binding), []).append(binding)
    return [
        binding
        for scope, members in by_scope.items()
        if _class_is_live(root, scope)
        for binding in live_bindings(root, members)
    ]
