#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A warning filter a test sets names the message it lets through.

The configuration turns every ``UserWarning`` and ``RuntimeWarning`` no test
asked for into an error (``pyproject.toml``, rule T28 of the contributor
guide). A filter in a test that lets a whole class through, or every
warning, undoes that for whatever else the call meets: a new advisory of the
library, a new deprecation of a dependency, a NumPy overflow. So a filter
that ignores, or shows without raising, names the message it means:
``warnings.filterwarnings`` with ``message=``, a ``filterwarnings`` mark
with its message part. ``warnings.simplefilter`` takes no message and passes
only where it hands each warning to a recorder the test reads,
``pytest.warns`` or a ``warnings.catch_warnings(record=True)`` bound by
``as`` to a name the test reads before it binds that name again, and so does
``warnings.resetwarnings``, which drops the configuration's errors with
every other filter. A recorder bound to no name, or to one nothing reads
while it holds the list, hides what its block meets. A comprehension or a
class body reads the name where it stands; a function reads it when it is
called, at a time the text does not say, so its read counts only where
nothing else binds that name. A filter whose action, or whose mark, the text
does not settle is one the check cannot clear: a name bound once, at module
level, to a constant is read as its value, and anything else, a loop
variable or an argument, stands in the table below with its reason.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

_ROOT = Path(__file__).resolve().parents[1]
_TESTS = _ROOT / "tests"
#: The actions of a filter that let a warning through instead of raising it.
_LETS_THROUGH = frozenset({"ignore", "default", "always", "all", "module", "once"})
#: The actions that still hand each warning to a recorder, once or every time.
_RECORDS = frozenset({"always", "all", "default"})
#: The context managers that record what their block raises for the test to read.
_RECORDERS = frozenset({"warns", "deprecated_call"})
#: Filters that let a warning through by no message, keyed by
#: ``"path::function"``, each with its reason.
_BY_CLASS: dict[str, str] = {
    "tests/refusal_order.py::_enter": (
        "the recorder of a pytest.raises block, entered by hand rather than in "
        "a with statement: it holds every warning of the block and, once the "
        "block ends, fails on an advisory ahead of the refusal or hands each "
        "warning back"
    ),
    "tests/simulation/test_remote_node.py::_under_a_node_s_filters": (
        "the block serves one job under the filters a node starts with, "
        "Python's defaults, in place of the suite's, so that the job meets what "
        "it meets on a node; the node records every warning the job raises and "
        "sends it back with the result, where the tests of what it sends read "
        "it"
    ),
    "tests/test_census_of_number_returns.py::_first_call": (
        "the census calls every public function of numbers with values chosen "
        "for their type, never for a clause, and reads only the kind of what "
        "it returns; what advisory each call meets is that function's own "
        "tests' subject, and one raised as an error here would read as a "
        "refusal"
    ),
    "tests/test_curated_examples.py::stale_examples": (
        "ast.parse of the code spans of the documentation pages, prose among "
        "them: Python warns on a span's escapes as it would on code, and no code "
        "of the library or a dependency runs in the block"
    ),
    "tests/test_scalar_guards.py::_quietly": (
        "the census calls every public function with values chosen for their "
        "type, never for a clause, and reads only whether it refuses and by "
        "which name; what advisory each call meets is that function's own "
        "tests' subject, and one raised as an error here would read as a refusal"
    ),
}


#: No name read as a constant.
_NO_NAMES: Mapping[str, object] = MappingProxyType({})


def _constant(node: ast.expr | None, known: Mapping[str, object] = _NO_NAMES) -> object:
    """The value of *node* when the text settles it, else a marker no filter holds.

    A constant settles it, and so does a name in *known*.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in known:
        return known[node.id]
    return _UNKNOWN


#: What :func:`_constant` returns for an expression the text does not settle.
_UNKNOWN = object()


def _bound(tree: ast.AST) -> dict[str, int]:
    """How many times each name is bound anywhere in *tree*, in any scope."""
    counts: dict[str, int] = {}
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            names.append(node.id)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.TypeVar,
                ast.ParamSpec,
                ast.TypeVarTuple,
            ),
        ):
            names.append(node.name)
        elif isinstance(node, ast.alias):
            names.append((node.asname or node.name).partition(".")[0])
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
            names.extend([node.name] if node.name else [])
        elif isinstance(node, ast.MatchMapping):
            names.extend([node.rest] if node.rest else [])
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.extend(node.names)
    for name in names:
        counts[name] = counts.get(name, 0) + 1
    return counts


def _module_constants(tree: ast.Module) -> Mapping[str, object]:
    """The names *tree* binds once, at module level, to a constant, with their values.

    A name bound anywhere else as well, in a function, a loop or an import,
    is left out: which value a filter reads under it is not in the text.
    """
    bound = _bound(tree)
    known: dict[str, object] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value = statement.targets[0], statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            target, value = statement.target, statement.value
        else:
            continue
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and bound.get(target.id) == 1
        ):
            known[target.id] = value.value
    return MappingProxyType(known)


def _argument(call: ast.Call, name: str, position: int | None) -> ast.expr | None:
    """The argument *call* passes as *name*, by keyword or at *position*; ``None`` when absent."""
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    if position is None or len(call.args) <= position:
        return None
    return call.args[position]


def _names(tree: ast.AST) -> tuple[frozenset[str], frozenset[str]]:
    """The names ``warnings`` goes by in *tree*, and the functions it imported bare."""
    modules = {"warnings"}
    bare: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {
                alias.asname or alias.name
                for alias in node.names
                if alias.name == "warnings"
            }
        elif isinstance(node, ast.ImportFrom) and node.module == "warnings":
            bare |= {
                alias.asname or alias.name
                for alias in node.names
                if alias.name
                in {"simplefilter", "filterwarnings", "catch_warnings", "resetwarnings"}
            }
    return frozenset(modules), frozenset(bare)


def _function(
    call: ast.Call, modules: frozenset[str], bare: frozenset[str]
) -> str | None:
    """Which filter *call* is: ``simplefilter``, ``filterwarnings``, ``mark``, ``catch_warnings``, ``resetwarnings``."""
    func = call.func
    if isinstance(func, ast.Name) and func.id in bare:
        return func.id
    if not isinstance(func, ast.Attribute):
        return None
    if isinstance(func.value, ast.Name) and func.value.id in modules:
        return func.attr
    owner = func.value
    if func.attr == "filterwarnings" and isinstance(owner, ast.Attribute):
        return "mark" if owner.attr == "mark" else None
    return None


#: The nodes whose body runs when something calls it, not where it stands.
_DEFERRED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
#: The comprehensions, each a scope of its own; all but a generator's run where they stand.
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _parameters(arguments: ast.arguments) -> list[ast.arg]:
    """Every parameter *arguments* declares, by position, by keyword or gathered."""
    gathered = [
        each for each in (arguments.vararg, arguments.kwarg) if each is not None
    ]
    return [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs, *gathered]


def _defaults(arguments: ast.arguments) -> list[ast.expr]:
    """The default values *arguments* gives, which Python evaluates where the function stands."""
    return [*arguments.defaults, *(each for each in arguments.kw_defaults if each)]


def _binds_itself(node: ast.AST, name: str) -> bool:
    """Whether the comprehension or class *node* binds *name* in its own scope.

    A comprehension binds its loop targets; a class body binds whatever
    its own statements do, its functions and comprehensions apart.
    """
    if isinstance(node, _COMPREHENSIONS):
        roots: list[ast.AST] = [each.target for each in node.generators]
    elif isinstance(node, ast.ClassDef):
        roots = list(node.body)
    else:
        return False
    return any(
        _binding(each, name) is not None
        or (
            isinstance(each, ast.Name)
            and each.id == name
            and not isinstance(each.ctx, ast.Load)
        )
        or (isinstance(each, (ast.Global, ast.Nonlocal)) and name in each.names)
        for root in roots
        for each in (root, *_in_place(root, name, opaque=True))
    )


def _in_place(scope: ast.AST, name: str, *, opaque: bool) -> Iterator[ast.AST]:
    """The nodes under *scope* that run where they stand, in the order of the text.

    A function or a lambda runs when something calls it: it is yielded
    whole, and only its decorators and the defaults of its parameters are
    opened, which Python evaluates where it stands. A class body and a
    list, set or dict comprehension run where they stand and are opened,
    unless they bind *name* themselves: then only the parts that read the
    enclosing scope are, a class's decorators, bases and keywords and a
    comprehension's first iterable. A generator expression evaluates its
    first iterable where it stands and the rest as it is consumed, so only
    that iterable is opened and the expression is yielded whole. With
    *opaque*, *scope* is a class body, whose names no comprehension or
    class in it reads past its first iterable or its header.
    """
    for child in ast.iter_child_nodes(scope):
        yield child
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parts: list[ast.AST] = [*child.decorator_list, *_defaults(child.args)]
        elif isinstance(child, ast.Lambda):
            parts = list(_defaults(child.args))
        elif isinstance(child, ast.ClassDef):
            parts = [*child.decorator_list, *child.bases, *child.keywords]
            if not opaque and not _binds_itself(child, name):
                parts.extend(child.body)
        elif isinstance(child, _COMPREHENSIONS):
            if (
                opaque
                or isinstance(child, ast.GeneratorExp)
                or _binds_itself(child, name)
            ):
                parts = [child.generators[0].iter]
            else:
                parts = list(ast.iter_child_nodes(child))
        else:
            yield from _in_place(child, name, opaque=opaque)
            continue
        for part in parts:
            yield part
            yield from _in_place(part, name, opaque=opaque)


#: The nodes that open a scope of their own.
_SCOPES = (*_DEFERRED, ast.ClassDef, *_COMPREHENSIONS)


def _scope_code(node: ast.AST) -> list[ast.AST]:
    """What runs inside the scope *node* opens, rather than in the scope around it.

    A function's or a class's body and a lambda's expression; for a
    comprehension, everything but its first iterable, which the scope
    around it evaluates.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return list(node.body)
    if isinstance(node, ast.Lambda):
        return [node.body]
    if isinstance(node, _COMPREHENSIONS):
        first, *rest = node.generators
        heads = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
        return [
            *heads,
            first.target,
            *first.ifs,
            *(part for each in rest for part in ast.iter_child_nodes(each)),
        ]
    return []


def _own_nodes(node: ast.AST, name: str) -> Iterator[ast.AST]:
    """The nodes that run in the scope *node* opens, each scope inside it yielded whole."""
    holder = ast.Module(body=_scope_code(node), type_ignores=[])
    return _in_place(holder, name, opaque=True)


def _walrus_binds(node: ast.AST, name: str) -> bool:
    """Whether an assignment expression in the comprehension *node* binds *name* in the scope around it.

    Python binds the target of ``:=`` in a comprehension, or in one nested
    in it, in the nearest scope that is no comprehension.
    """
    return any(
        (
            isinstance(each, ast.NamedExpr)
            and isinstance(each.target, ast.Name)
            and each.target.id == name
        )
        or (isinstance(each, _COMPREHENSIONS) and _walrus_binds(each, name))
        for each in _own_nodes(node, name)
    )


def _reads_later(node: ast.AST, name: str) -> tuple[bool, bool]:
    """Whether the scope *node* opens reads *name* from the scope around it, and whether it binds it there.

    Each scope is read on its own, as Python resolves a name: the scope
    reads the enclosing name when it, or a scope inside it, reads the name
    and no scope between binds it as a parameter, a target, an import, a
    ``def`` or a class of its own, unless that scope declares it
    ``nonlocal`` or ``global``. It binds the enclosing name when it
    declares it so and binds it, or a scope inside it does so through it.
    A class body is a scope the functions and comprehensions inside it
    pass over, as Python passes over it; a comprehension leaves the target
    of an assignment expression to the scope around it.
    """
    comprehension = isinstance(node, _COMPREHENSIONS)
    local = isinstance(node, _DEFERRED) and any(
        each.arg == name for each in _parameters(node.args)
    )
    declared = reads = inner_reads = inner_binds = False
    leaked: set[int] = set()
    for each in _own_nodes(node, name):
        if isinstance(each, _SCOPES):
            read_inside, bound_inside = _reads_later(each, name)
            inner_reads = inner_reads or read_inside
            inner_binds = inner_binds or bound_inside
            local = local or (
                isinstance(each, _COMPREHENSIONS) and _walrus_binds(each, name)
            )
        if comprehension and isinstance(each, ast.NamedExpr):
            leaked.add(id(each.target))
        if _binding(each, name) is not None:
            local = True
        if isinstance(each, (ast.Global, ast.Nonlocal)) and name in each.names:
            declared = True
        if isinstance(each, ast.Name) and each.id == name:
            if isinstance(each.ctx, ast.Load):
                reads = True
            elif id(each) not in leaked:
                local = True
    passes = declared or not local
    if isinstance(node, ast.ClassDef):
        return (reads and passes) or inner_reads, (declared and local) or inner_binds
    return (reads or inner_reads) and passes, (declared and local) or (
        inner_binds and passes
    )


def _end(node: ast.AST) -> tuple[int, int]:
    """Where *node* ends in the text, as a line and a column."""
    line = getattr(node, "end_lineno", None) or getattr(node, "lineno", 0)
    column = getattr(node, "end_col_offset", None)
    return line, getattr(node, "col_offset", 0) if column is None else column


def _evaluated_first(node: ast.AST) -> Iterator[tuple[ast.expr, ast.expr]]:
    """Each target *node* binds, with the expression Python evaluates before it binds it."""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            yield target, node.value
    elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
        yield node.target, node.value
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        yield node.target, node.iter
    elif isinstance(node, ast.withitem) and node.optional_vars is not None:
        yield node.optional_vars, node.context_expr


def _binding(node: ast.AST, name: str) -> tuple[int, int] | None:
    """Where *node* binds *name* other than as a target of an assignment, or ``None``.

    A function or a class binds its name once its statement has run; an
    import, an ``except`` clause and a pattern of ``match`` bind theirs
    where they stand.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return _end(node) if node.name == name else None
    if isinstance(node, ast.alias):
        bound = (node.asname or node.name).partition(".")[0]
    elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        bound = node.name or ""
    elif isinstance(node, ast.MatchMapping):
        bound = node.rest or ""
    else:
        return None
    return (node.lineno, node.col_offset) if bound == name else None


def _read_while_bound(owner: ast.AST, item: ast.withitem) -> bool:
    """Whether *owner* reads the list *item* binds before its name holds anything else.

    A read that runs where it stands counts when it follows the binding
    with no other binding of the name between them, in the order Python
    runs a statement: the value of an assignment, the iterable of a loop
    and the manager of a ``with`` before their targets, and the target of
    an augmented assignment read before it is bound. A comprehension and a
    class body read where they stand. A function, a lambda or the body of a
    generator expression reads the name when it is called or consumed, at
    a time the text does not say, so its read counts only when nothing in
    *owner* but *item* binds the name; in a class body it never does, since
    Python looks a name up past the class.
    """
    target = item.optional_vars
    if not isinstance(target, ast.Name):
        return False
    name = target.id
    opaque = isinstance(owner, ast.ClassDef)
    bound_after: dict[int, tuple[int, int]] = {}
    read_first: set[int] = set()
    events: list[tuple[tuple[int, int], bool]] = []
    read_later = bound_elsewhere = False
    for node in _in_place(owner, name, opaque=opaque):
        if isinstance(node, (*_DEFERRED, ast.GeneratorExp)):
            reads, binds = _reads_later(node, name)
            read_later = read_later or (reads and not opaque)
            bound_elsewhere = bound_elsewhere or binds
        if (where := _binding(node, name)) is not None:
            events.append((where, False))
        for bound, value in _evaluated_first(node):
            for each in ast.walk(bound):
                bound_after[id(each)] = _end(value)
        if isinstance(node, ast.AugAssign):
            read_first.add(id(node.target))
        if not isinstance(node, ast.Name) or node.id != name or node is target:
            continue
        where = (node.lineno, node.col_offset)
        if isinstance(node.ctx, ast.Load) or id(node) in read_first:
            events.append((where, True))
        else:
            events.append((bound_after.get(id(node), where), False))
    later = sorted(event for event in events if event[0] > _end(item.context_expr))
    if later and later[0][1]:
        return True
    bound_elsewhere = bound_elsewhere or any(not read for _, read in events)
    return read_later and not bound_elsewhere


def _records(
    item: ast.withitem,
    modules: frozenset[str],
    bare: frozenset[str],
    known: Mapping[str, object],
    owner: ast.AST,
) -> bool:
    """Whether the context manager of *item* records the warnings of its block for the test.

    ``catch_warnings(record=True)`` does only when its list is bound by ``as``
    to a name that *owner*, the function, class or module the ``with``
    stands in, reads before it binds the name again: a list no one reads
    hides every warning of the block.
    """
    call = item.context_expr
    if not isinstance(call, ast.Call):
        return False
    if _function(call, modules, bare) == "catch_warnings":
        return _constant(
            _argument(call, "record", 0), known
        ) is True and _read_while_bound(owner, item)
    func = call.func
    return isinstance(func, ast.Attribute) and func.attr in _RECORDERS


def _spelled(node: ast.expr | None) -> str:
    """*node* as the source spells it, or nothing where the call passes none."""
    return "" if node is None else ast.unparse(node)


def _lets_through(
    call: ast.Call, what: str, *, recording: bool, known: Mapping[str, object]
) -> str | None:
    """How *call*, a filter of kind *what*, lets a warning through by no message, or ``None``."""
    if what == "mark":
        for argument in call.args:
            text = _constant(argument, known)
            if not isinstance(text, str):
                return f"mark {_spelled(argument)} is a filter the check cannot read"
            head, pattern = [*text.split(":"), ""][:2]
            if head.strip() in _LETS_THROUGH and not pattern.strip():
                return f"mark {text!r} names no message"
        return None
    if what == "resetwarnings":
        if recording:
            return None
        return "resetwarnings() lets every warning through by no message"
    if what == "filterwarnings":
        spelled = _argument(call, "action", 0)
        given = _constant(spelled, known)
        message = _argument(call, "message", 1)
        if message is not None and _constant(message, known) not in {"", None}:
            return None
        if given is _UNKNOWN:
            return (
                f"filterwarnings({_spelled(spelled)}) takes an action the check "
                "cannot read and names no message"
            )
        if given in _LETS_THROUGH:
            return f"filterwarnings({given!r}) names no message"
        return None
    if what == "simplefilter":
        spelled = _argument(call, "action", 0)
    elif what == "catch_warnings":
        spelled = _argument(call, "action", None)
        if spelled is None:
            return None
    else:
        return None
    action = _constant(spelled, known)
    if action is _UNKNOWN:
        return f"{what}({_spelled(spelled)}) takes an action the check cannot read"
    if action not in _LETS_THROUGH or (recording and action in _RECORDS):
        return None
    category = _argument(call, "category", 1)
    named = ast.unparse(category) if category is not None else "every warning"
    return f"{what}({action!r}) lets {named} through by no message"


def _filters_in(source: str, where: str) -> list[tuple[str, str]]:
    """Each filter in the Python *source* of *where* that lets a warning through by no message."""
    tree = ast.parse(source, filename=where)
    modules, bare = _names(tree)
    known = _module_constants(tree)
    found: list[tuple[str, str]] = []

    def visit(node: ast.AST, scope: str, owner: ast.AST, *, recording: bool) -> None:
        key = f"{where}::{scope or '<module>'}"
        for child in ast.iter_child_nodes(node):
            inner, inner_owner, records = scope, owner, recording
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
                inner_owner = child
                records = False
            if isinstance(child, (ast.With, ast.AsyncWith)) and any(
                _records(item, modules, bare, known, owner) for item in child.items
            ):
                # Python enters the items in order, so a recorder an item
                # opens also records the warnings of every item after it.
                entered = recording
                for item in child.items:
                    entered = entered or _records(item, modules, bare, known, owner)
                    visit(item, inner, owner, recording=entered)
                for statement in child.body:
                    visit_one(statement, inner, owner, recording=True)
                continue
            if isinstance(child, ast.Call):
                what = _function(child, modules, bare)
                if what is not None and (
                    how := _lets_through(child, what, recording=records, known=known)
                ):
                    found.append((key, f"line {child.lineno}: {how}"))
            visit(child, inner, inner_owner, recording=records)

    def visit_one(
        statement: ast.AST, scope: str, owner: ast.AST, *, recording: bool
    ) -> None:
        holder = ast.Module(body=[statement], type_ignores=[])  # type: ignore[list-item]
        visit(holder, scope, owner, recording=recording)

    visit(tree, "", tree, recording=False)
    return found


@pytest.mark.parametrize(
    "source",
    [
        "warnings.simplefilter('ignore')",
        "warnings.simplefilter('ignore', UserWarning)",
        "warnings.simplefilter('ignore', category=SoundPowerWarning)",
        "warnings.simplefilter('always')",
        "warnings.filterwarnings('ignore')",
        "warnings.filterwarnings('ignore', category=RuntimeWarning)",
        "warnings.filterwarnings('ignore', '', RuntimeWarning)",
        "warnings.filterwarnings(action='default', category=UserWarning)",
        "pytestmark = pytest.mark.filterwarnings('ignore::phonometry.PhonometryWarning')",
        "pytest.mark.filterwarnings('ignore')",
        "pytest.mark.filterwarnings('default::UserWarning')",
        "pytest.mark.filterwarnings('ignore:Low rate:UserWarning', 'ignore::UserWarning')",
        "warnings.catch_warnings(action='ignore')",
        "with warnings.catch_warnings(record=True):\n    warnings.simplefilter('ignore')",
        "with pytest.warns(UserWarning):\n    warnings.simplefilter('ignore', RuntimeWarning)",
        "import warnings as w\nw.simplefilter('ignore')",
        "from warnings import simplefilter\nsimplefilter('ignore')",
        "warnings.resetwarnings()",
        "with warnings.catch_warnings():\n    warnings.resetwarnings()",
        "from warnings import resetwarnings\nresetwarnings()",
        "for action in ACTIONS:\n    warnings.filterwarnings(action, category=UserWarning)",
        "warnings.filterwarnings(*spec)",
        "warnings.simplefilter(action)",
        "with warnings.catch_warnings(record=True):\n    warnings.simplefilter(action)",
        "with warnings.catch_warnings(record=True):\n    warnings.simplefilter('default', UserWarning)",
        "with warnings.catch_warnings(record=True):\n    warnings.simplefilter('always')\n    call()",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = []",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\ndef other(seen):\n    assert seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nwith warnings.catch_warnings(record=True) as seen:\n    pass\nassert not seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = []\nassert not seen",
        "seen = []\nassert not seen\nwith warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check(seen):\n        assert seen\n    check([])",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        return lambda seen: seen\n    check()",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        return [seen for seen in range(2)]\n    check()",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nfor seen in cases:\n    assert seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = []\nassert not [w for w in seen]",
        "seen = []\nassert not [w for w in seen]\nwith warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = []\nassert not any(w for w in seen)",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = []\nclass Check:\n    found = seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\npending = (seen for _ in range(1))\nseen = []\nassert not next(pending)",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nassert not [seen for seen in cases]",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    seen = []\n    def check():\n        assert not seen\n    check()",
        "class TestIt:\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def test_it(self):\n        assert not seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\ndef seen():\n    pass\nassert seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\ntry:\n    call()\nexcept OSError as seen:\n    assert seen",
        "with warnings.catch_warnings(action='always', record=True):\n    pass",
        "with warnings.catch_warnings(action='always'), warnings.catch_warnings(record=True) as seen:\n    pass\nassert not seen",
        "with warnings.catch_warnings(record=True):\n    warnings.resetwarnings()",
        "warnings.catch_warnings(action=chosen)",
        "pytest.mark.filterwarnings(spec)",
        "ACTION = 'ignore'\nwarnings.simplefilter(ACTION, UserWarning)",
        "SPEC = 'ignore::UserWarning'\npytest.mark.filterwarnings(SPEC)",
        "SPEC = 'ignore:Low rate:UserWarning'\nSPEC = 'ignore'\npytest.mark.filterwarnings(SPEC)",
        "SPEC = 'ignore:Low rate:UserWarning'\ndef test_it(SPEC):\n    pytest.mark.filterwarnings(SPEC)",
    ],
)
def test_a_filter_that_names_no_message_is_found(source: str) -> None:
    assert _filters_in(source, "tests/example.py")


@pytest.mark.parametrize(
    "source",
    [
        "warnings.simplefilter('error')",
        "warnings.simplefilter('error', UserWarning)",
        "warnings.filterwarnings('ignore', message='Low sampling rate')",
        "warnings.filterwarnings('ignore', 'Low sampling rate', UserWarning)",
        "warnings.filterwarnings('ignore', message=re.escape(text))",
        "pytest.mark.filterwarnings('ignore:Low sampling rate:UserWarning')",
        "pytest.mark.filterwarnings('error::UserWarning')",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nassert not seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('default', UserWarning)\nassert len(seen) == 1",
        "with warnings.catch_warnings(action='always', record=True) as seen:\n    pass\nassert not seen",
        "with warnings.catch_warnings(record=True) as seen, warnings.catch_warnings(action='always'):\n    pass\nassert not seen",
        "with pytest.warns(UserWarning), warnings.catch_warnings(action='always'):\n    pass",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        assert seen\n    check()",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        assert not seen\n        return lambda seen: seen\n    check()",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        assert not seen\n        def inner():\n            seen = 1\n            return seen\n        return [seen for seen in range(2)], inner\n    check()",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check():\n        class Kept:\n            seen = 1\n        return (lambda: seen)()\n    assert not check()",
        "with pytest.warns(UserWarning):\n    warnings.simplefilter('always')",
        "warnings.catch_warnings()",
        "text.filterwarnings('ignore')",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.resetwarnings()\nassert not seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\n    call()\n    assert not seen",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen = [w.message for w in seen]",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nfor seen in seen:\n    pass",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nseen += []",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nassert not [w for w in seen]",
        "def test_it():\n    def check():\n        assert not seen\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    check()",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nassert not any(w for w in seen)",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nassert not [seen for _ in range(1)][0]",
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')\nclass Check:\n    found = seen",
        "def test_it():\n    with warnings.catch_warnings(record=True) as seen:\n        warnings.simplefilter('always')\n    def check(found=seen):\n        assert not found\n    seen = []\n    check()",
        "warnings.filterwarnings(action, message='Low sampling rate')",
        "ACTION = 'error'\nwarnings.simplefilter(ACTION, UserWarning)",
        "SPEC = 'ignore:Low rate:UserWarning'\npytest.mark.filterwarnings(SPEC)",
        "SPEC = (\n    'ignore:Low rate'\n    ':UserWarning'\n)\npytest.mark.filterwarnings(SPEC)",
    ],
)
def test_a_filter_that_names_its_message_or_records_passes(source: str) -> None:
    assert _filters_in(source, "tests/example.py") == []


def test_a_recorder_covers_its_own_block_and_no_function_defined_in_it() -> None:
    source = (
        "def test_it():\n"
        "    with warnings.catch_warnings(record=True) as seen:\n"
        "        warnings.simplefilter('always')\n"
        "        def helper():\n"
        "            warnings.simplefilter('always')\n"
        "    warnings.simplefilter('always')\n"
        "    assert not seen\n"
    )
    found = _filters_in(source, "tests/example.py")
    assert found == [
        (
            "tests/example.py::test_it.helper",
            "line 5: simplefilter('always') lets every warning through by no message",
        ),
        (
            "tests/example.py::test_it",
            "line 6: simplefilter('always') lets every warning through by no message",
        ),
    ]


def test_filters_put_back_to_python_s_defaults_are_found() -> None:
    """The shape the remote node's tests use: the suite's filters cleared, others set.

    ``resetwarnings`` drops the configuration's errors, so every warning the
    block meets is shown and none raised, and an action read off a loop is
    one the text does not settle. The check read neither, and passed the
    block that lets every ``UserWarning`` and ``RuntimeWarning`` of a served
    job through by no message.
    """
    source = (
        "def _under_a_node_s_filters():\n"
        "    with warnings.catch_warnings():\n"
        "        warnings.resetwarnings()\n"
        "        for action, category, module in _NODE_FILTERS:\n"
        "            warnings.filterwarnings(\n"
        "                action, category=category, module=module, append=True\n"
        "            )\n"
        "        yield\n"
    )
    assert _filters_in(source, "tests/example.py") == [
        (
            "tests/example.py::_under_a_node_s_filters",
            "line 3: resetwarnings() lets every warning through by no message",
        ),
        (
            "tests/example.py::_under_a_node_s_filters",
            "line 5: filterwarnings(action) takes an action the check cannot "
            "read and names no message",
        ),
    ]


@pytest.mark.whole_tree
def test_every_warning_filter_in_the_suite_names_its_message() -> None:
    """A test lets a warning through by its message, never by its class alone.

    Where the warning is what the test is about, ``pytest.warns`` names its
    class and its message; where it comes with an input the test needs, a
    filter names the message, with the reason beside it (T28).
    """
    found = [
        each
        for path in sorted(_TESTS.rglob("*.py"))
        for each in _filters_in(
            path.read_text(encoding="utf-8"), path.relative_to(_ROOT).as_posix()
        )
    ]
    unexplained = [f"{key}: {what}" for key, what in found if key not in _BY_CLASS]
    assert not unexplained, (
        "warning filters that let a warning through by no message:\n"
        + "\n".join(unexplained)
    )
    stale = sorted(set(_BY_CLASS) - {key for key, _ in found})
    assert not stale, f"exemptions that no longer match a filter: {stale}"


def _t28_exceptions() -> str:
    """The Exceptions paragraph of rule T28 in the contributor guide."""
    guide = (_ROOT / "docs" / "contributing" / "tests.md").read_text(encoding="utf-8")
    rule = guide.split("### T28.", 1)[1].split("\n### ", 1)[0]
    return rule.split("**Exceptions.**", 1)[1].split("\n\n", 1)[0]


def test_the_guide_names_the_file_of_every_exemption() -> None:
    """Rule T28 names each filter that lets warnings through by no message.

    The census of number returns took its exemption with the module that
    added it while the rule's list of exceptions kept the four before it.
    """
    exceptions = _t28_exceptions()
    unnamed = sorted(
        key for key in _BY_CLASS if f"`{key.split('::', 1)[0]}`" not in exceptions
    )
    assert not unnamed, f"T28 names no file for: {unnamed}"
