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
or a ``nonlocal`` statement sends the name out.
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

    def binds(self, name: str) -> bool:
        """Whether *name* is the scope's own: bound in it, and not declared
        ``global`` or ``nonlocal`` there.
        """
        if name in self.declared_global or name in self.declared_nonlocal:
            return False
        return (
            name in self.parameters
            or name in self.defined
            or name in self.imported
            or name in self.stored
        )

    def how(self, name: str) -> Literal["definition", "import", "binding"]:
        """How the scope binds *name*, which :meth:`binds` says it does.

        ``"definition"`` and ``"import"`` when that is the only way it does;
        ``"binding"`` for a parameter, any other binding, and a name bound
        two ways, which may stand for either at a call.
        """
        if name in self.parameters or name in self.stored:
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
    }
    comprehension = isinstance(scope, _COMPREHENSIONS)
    for node in scope_nodes(scope):
        declared = _declared(node)
        if declared is not None:
            found[declared[0]].update(declared[1])
        else:
            found["stored"].update(_stored(node, comprehension=comprehension))
    return OwnNames(
        _parameter_names(scope),
        frozenset(found["defined"]),
        frozenset(found["imported"]),
        frozenset(found["stored"]),
        frozenset(found["declared_global"]),
        frozenset(found["declared_nonlocal"]),
    )


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
    parents = _parents(root)
    found: list[ast.AST] = []
    crossed = False
    grandchild: ast.AST | None = None
    child = node
    current = parents.get(node)
    while current is not None and current is not root:
        if isinstance(current, SCOPES) and _runs_inside(current, child, grandchild):
            if not (isinstance(current, ast.ClassDef) and crossed):
                found.append(current)
            crossed = crossed or not isinstance(current, ast.ClassDef)
        grandchild, child, current = child, current, parents.get(current)
    if not (isinstance(root, ast.ClassDef) and crossed):
        found.append(root)
    return found


def binding_of(
    root: ast.AST, node: ast.AST, name: str
) -> tuple[
    Literal["definition", "import", "binding", "global", "outside"], ast.AST | None
]:
    """How *name*, read at *node*, is bound inside *root*, and by which scope.

    The scopes around *node* are read innermost first (:func:`scopes_around`):
    the first that binds the name says how (:meth:`OwnNames.how`); one that
    declares it ``global`` sends it to the module (``"global"``), and one
    that declares it ``nonlocal`` passes it on outwards. ``"outside"`` when
    no scope up to *root* binds it.
    """
    for scope in scopes_around(root, node):
        names = own_names(scope)
        if name in names.declared_global:
            return "global", None
        if names.binds(name):
            return names.how(name), scope
    return "outside", None
