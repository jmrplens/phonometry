#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A warning filter a test sets names the message it lets through.

The configuration turns every ``UserWarning`` and ``RuntimeWarning`` no test
asked for into an error (``pyproject.toml``, rule T28 of the contributor
guide). A filter in a test that lets a whole class through, or every
warning, undoes that for whatever else the call meets: a new advisory of the
library, a new deprecation of a dependency, a NumPy overflow. So a filter
that ignores, or shows without raising, names the message it means:
``warnings.filterwarnings`` with ``message=``, a ``filterwarnings`` mark
with its message part. ``warnings.simplefilter`` takes no message and
passes only where it hands each warning to a recorder the test reads, inside
``warnings.catch_warnings(record=True)`` or ``pytest.warns``, and so does
``warnings.resetwarnings``, which drops the configuration's errors with
every other filter. A filter whose action, or whose mark, the text does not
settle is one the check cannot clear: a name bound once, at module level,
to a constant is read as its value, and anything else, a loop variable or
an argument, stands in the table below with its reason.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping

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


def _records(
    item: ast.withitem,
    modules: frozenset[str],
    bare: frozenset[str],
    known: Mapping[str, object],
) -> bool:
    """Whether the context manager of *item* records the warnings of its block."""
    call = item.context_expr
    if not isinstance(call, ast.Call):
        return False
    if _function(call, modules, bare) == "catch_warnings":
        return _constant(_argument(call, "record", 0), known) is True
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
        recording = recording or _constant(_argument(call, "record", 0), known) is True
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

    def visit(node: ast.AST, scope: str, *, recording: bool) -> None:
        key = f"{where}::{scope or '<module>'}"
        for child in ast.iter_child_nodes(node):
            inner, records = scope, recording
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
                records = False
            if isinstance(child, (ast.With, ast.AsyncWith)) and any(
                _records(item, modules, bare, known) for item in child.items
            ):
                for item in child.items:
                    visit(item, inner, recording=recording)
                for statement in child.body:
                    visit_one(statement, inner, recording=True)
                continue
            if isinstance(child, ast.Call):
                what = _function(child, modules, bare)
                if what is not None and (
                    how := _lets_through(child, what, recording=records, known=known)
                ):
                    found.append((key, f"line {child.lineno}: {how}"))
            visit(child, inner, recording=records)

    def visit_one(statement: ast.AST, scope: str, *, recording: bool) -> None:
        holder = ast.Module(body=[statement], type_ignores=[])  # type: ignore[list-item]
        visit(holder, scope, recording=recording)

    visit(tree, "", recording=False)
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
        "with warnings.catch_warnings(record=True) as seen:\n    warnings.simplefilter('always')",
        "with warnings.catch_warnings(record=True):\n    warnings.simplefilter('default', UserWarning)",
        "with warnings.catch_warnings(action='always', record=True):\n    pass",
        "with pytest.warns(UserWarning):\n    warnings.simplefilter('always')",
        "warnings.catch_warnings()",
        "text.filterwarnings('ignore')",
        "with warnings.catch_warnings(record=True):\n    warnings.resetwarnings()",
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
        "    with warnings.catch_warnings(record=True):\n"
        "        warnings.simplefilter('always')\n"
        "        def helper():\n"
        "            warnings.simplefilter('always')\n"
        "    warnings.simplefilter('always')\n"
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
