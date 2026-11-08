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
``warnings.catch_warnings(record=True)`` or ``pytest.warns``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

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


def _constant(node: ast.expr | None) -> object:
    """The value of *node* when it is a constant, else a marker no filter holds."""
    if isinstance(node, ast.Constant):
        return node.value
    return _UNKNOWN


#: What :func:`_constant` returns for an expression the text does not settle.
_UNKNOWN = object()


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
                if alias.name in {"simplefilter", "filterwarnings", "catch_warnings"}
            }
    return frozenset(modules), frozenset(bare)


def _function(
    call: ast.Call, modules: frozenset[str], bare: frozenset[str]
) -> str | None:
    """Which filter *call* is: ``simplefilter``, ``filterwarnings``, ``mark``, ``catch_warnings``."""
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


def _records(item: ast.withitem, modules: frozenset[str], bare: frozenset[str]) -> bool:
    """Whether the context manager of *item* records the warnings of its block."""
    call = item.context_expr
    if not isinstance(call, ast.Call):
        return False
    if _function(call, modules, bare) == "catch_warnings":
        return _constant(_argument(call, "record", 0)) is True
    func = call.func
    return isinstance(func, ast.Attribute) and func.attr in _RECORDERS


def _lets_through(call: ast.Call, what: str, *, recording: bool) -> str | None:
    """How *call*, a filter of kind *what*, lets a warning through by no message, or ``None``."""
    if what == "mark":
        for argument in call.args:
            text = _constant(argument)
            if not isinstance(text, str):
                continue
            head, pattern = [*text.split(":"), ""][:2]
            if head.strip() in _LETS_THROUGH and not pattern.strip():
                return f"mark {text!r} names no message"
        return None
    if what == "filterwarnings":
        given = _constant(_argument(call, "action", 0))
        message = _argument(call, "message", 1)
        if given in _LETS_THROUGH and (
            message is None or _constant(message) in {"", None}
        ):
            return f"filterwarnings({given!r}) names no message"
        return None
    action: object
    if what == "simplefilter":
        action = _constant(_argument(call, "action", 0))
    elif what == "catch_warnings":
        action = _constant(_argument(call, "action", None))
        if action is None:
            return None
        recording = recording or _constant(_argument(call, "record", 0)) is True
    else:
        return None
    if action not in _LETS_THROUGH or (recording and action in _RECORDS):
        return None
    category = _argument(call, "category", 1)
    named = ast.unparse(category) if category is not None else "every warning"
    return f"{what}({action!r}) lets {named} through by no message"


def _filters_in(source: str, where: str) -> list[tuple[str, str]]:
    """Each filter in the Python *source* of *where* that lets a warning through by no message."""
    tree = ast.parse(source, filename=where)
    modules, bare = _names(tree)
    found: list[tuple[str, str]] = []

    def visit(node: ast.AST, scope: str, *, recording: bool) -> None:
        key = f"{where}::{scope or '<module>'}"
        for child in ast.iter_child_nodes(node):
            inner, records = scope, recording
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
                records = False
            if isinstance(child, (ast.With, ast.AsyncWith)) and any(
                _records(item, modules, bare) for item in child.items
            ):
                for item in child.items:
                    visit(item, inner, recording=recording)
                for statement in child.body:
                    visit_one(statement, inner, recording=True)
                continue
            if isinstance(child, ast.Call):
                what = _function(child, modules, bare)
                if what is not None and (
                    how := _lets_through(child, what, recording=records)
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
