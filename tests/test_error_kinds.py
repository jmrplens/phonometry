#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A wrong type raises ``TypeError``; a right type with a wrong value, ``ValueError``.

The Python documentation draws the line: ``TypeError`` is "raised when an
operation or function is applied to an object of inappropriate type", and
``ValueError`` "when an operation or function receives an argument that has
the right type but an inappropriate value". Seventy-six refusals in ``src``
tested the type of an argument and raised ``ValueError`` for it, nine of them
behind a ``# noqa: TRY004`` that said why ("keeps the module validation
errors uniform"), and thirty-two handlers turned a ``TypeError`` into a
``ValueError`` on its way out, while sixteen others raised ``TypeError`` for
the same mistake. A caller who catches ``TypeError`` around a call to tell a
programming error from a bad measurement could not rely on either.

The rule reads ``src`` with :mod:`ast` and finds the shapes a type refusal
takes:

* an ``if`` whose test asks only for a type (``isinstance``, ``issubclass``,
  ``is_scalar``, numpy's ``isscalar``, ``callable``, ``iscomplexobj``,
  ``isrealobj``, ``issubdtype``, a comparison of an array's
  ``dtype`` or ``dtype.kind``, a rank against zero such as ``x.ndim != 0``,
  any combination of them with ``not``, ``and``, ``or``, ``any``/``all``
  over them, and ``is None`` beside them) and whose body raises anything but
  ``TypeError``; and an ``if`` whose test joins such a type question to a
  value question with ``or``, which has to be split, because its one
  exception cannot be both;
* a chain of ``if isinstance(...): return ...`` that falls through to a
  ``raise`` of anything but ``TypeError``, and the ``else`` of an
  ``if``/``elif`` chain whose last test asks a type;
* an ``except TypeError`` that raises another class, which renames the
  refusal and changes its class with it (``relabelled_type_errors``).

An ``isinstance`` joined to a value question by ``and`` is not a type refusal:
``isinstance(x, Signal) and x.fs != fs`` asks the value of an object whose
type is already settled, and refuses that value.

The exemptions are named below, each with its reason: a file the library
reads is data, so a field of the wrong type in it is a malformed file and a
``ValueError`` naming the file, not a programming error of the caller's.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

SRC = Path(__file__).resolve().parent.parent / "src" / "phonometry"

#: The calls that ask a value for its type (``is_scalar`` and numpy's
#: ``isscalar`` ask its rank, which is the type question for one number against
#: an array; ``iscomplexobj``, ``isrealobj`` and ``issubdtype`` its dtype, a
#: complex value where a real one belongs or text where numbers do).
_TYPE_CALLS = frozenset(
    {
        "isinstance",
        "issubclass",
        "is_scalar",
        "isscalar",
        "callable",
        "iscomplexobj",
        "isrealobj",
        "issubdtype",
    }
)

#: The exceptions a type refusal may raise: ``TypeError`` itself.
_TYPE_ERRORS = frozenset({"TypeError"})

#: Exceptions whose type refusals are the data's, not the caller's.
#: ``CatalogueError`` is raised for a catalogue that does not hold what a row
#: needs, read from a file or built by hand, and is a ``ValueError`` on purpose
#: (see its docstring).
_DATA_ERRORS = frozenset({"CatalogueError"})

#: Functions whose type refusals stay ``ValueError``, keyed by
#: ``<path>:<qualified name>``, each with its reason.
EXEMPT: dict[str, str] = {
    # The sidecar payload parser: a field of the wrong type in a JSON file the
    # library reads is a malformed file, and the refusal names the file.
    "io/_sidecar.py:_optional_number": "parses a sidecar file's payload",
    "io/_sidecar.py:_load_sidecar_payload": "parses a sidecar file's payload",
    "io/_sidecar.py:_required_factor": "parses a sidecar file's payload",
    "io/_sidecar.py:_calibrator_fields": "parses a sidecar file's payload",
    "io/_sidecar.py:_channel_labels": "parses a sidecar file's payload",
    "io/_sidecar.py:_version": "parses a sidecar file's payload",
    # CalibrationSidecar checks its own fields through these, and a sidecar
    # read from a file is built through it: _record catches ValueError and
    # names the file, so a bad file keeps saying which file it was.
    "io/_sidecar.py:_real": "CalibrationSidecar's own checks",
    "io/_sidecar.py:_labels": "CalibrationSidecar's own checks",
    "io/_sidecar.py:_check_text": "CalibrationSidecar's own checks",
}


def _called(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_none_test(node: ast.expr) -> bool:
    """``name is None`` or ``name is not None``, on a plain name.

    An attribute asked whether it is ``None`` (``x.calibration_factor is
    None``) is a question about the value of an object, not about the type of
    the argument.
    """
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.Is, ast.IsNot))
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value is None
    )


def _is_dtype_test(node: ast.expr) -> bool:
    """A comparison of an array's ``dtype`` or ``dtype.kind`` with a type.

    ``x.dtype.kind in "USb"`` asks what type the elements are, the question
    ``iscomplexobj`` asks of a complex array: an array of text where numbers
    belong is the wrong type, like a text where one number does.
    """
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.Eq, ast.NotEq, ast.In, ast.NotIn))
    ):
        return False
    left = node.left
    if isinstance(left, ast.Attribute) and left.attr == "kind":
        left = left.value
    return isinstance(left, ast.Attribute) and left.attr == "dtype"


def _is_rank_test(node: ast.expr) -> bool:
    """``x.ndim != 0`` or ``np.ndim(x) > 0``: an array where one number belongs.

    The question ``is_scalar`` asks, written out: the rank of a value is its
    type for the purpose of one number against an array.
    """
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.NotEq, ast.Gt))
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == 0
    ):
        return False
    left = node.left
    return (isinstance(left, ast.Attribute) and left.attr == "ndim") or (
        isinstance(left, ast.Call) and _called(left) == "ndim"
    )


def _type_leaves(node: ast.expr) -> list[ast.expr] | None:
    """The leaves of a test made only of type questions, or ``None``.

    A leaf is a type call (possibly inside ``any``/``all`` over a generator),
    a comparison of a ``dtype``, or an ``is None`` comparison; ``not``,
    ``and`` and ``or`` join them.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _type_leaves(node.operand)
    if isinstance(node, ast.BoolOp):
        leaves: list[ast.expr] = []
        for value in node.values:
            inner = _type_leaves(value)
            if inner is None:
                return None
            leaves += inner
        return leaves
    if isinstance(node, ast.Call):
        name = _called(node)
        if name in _TYPE_CALLS:
            return [node]
        if (
            name in {"any", "all"}
            and len(node.args) == 1
            and isinstance(node.args[0], ast.GeneratorExp)
        ):
            return _type_leaves(node.args[0].elt)
    if _is_none_test(node) or _is_dtype_test(node) or _is_rank_test(node):
        return [node]
    return None


def _asks_only_the_type(node: ast.expr) -> bool:
    """Whether a test asks for a type and nothing else (``is None`` aside)."""
    leaves = _type_leaves(node)
    return leaves is not None and any(not _is_none_test(leaf) for leaf in leaves)


def _joins_type_and_value(node: ast.expr) -> bool:
    """Whether an ``or`` puts a type question beside a value question.

    The ``or`` may sit under an ``and``, as in ``n is not None and (not
    isinstance(n, int) or n < 1)``: one refusal still answers two questions.
    """
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return any(_joins_type_and_value(value) for value in node.values)
    return (
        isinstance(node, ast.BoolOp)
        and isinstance(node.op, ast.Or)
        and any(_asks_only_the_type(value) for value in node.values)
        and not all(_type_leaves(value) is not None for value in node.values)
    )


def _refusal(statements: list[ast.stmt]) -> list[str]:
    """What a block that only refuses raises, or nothing for any other block.

    A refusal is the wording of a message and the raise: a block that also
    returns, loops or branches is a dispatch on the type (``if isinstance(x,
    str):`` and then the choices a text may name), whose raise refuses a value
    of that type, not the type.
    """
    plain = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Pass)
    if not statements or not isinstance(statements[-1], ast.Raise):
        return []
    if not all(isinstance(statement, plain) for statement in statements[:-1]):
        return []
    return _raised(statements[-1:])


def _raised(statements: list[ast.stmt]) -> list[str]:
    """The names of the exceptions the statements raise directly."""
    names: list[str] = []
    for statement in statements:
        if isinstance(statement, ast.Raise) and statement.exc is not None:
            exc = statement.exc
            target = exc.func if isinstance(exc, ast.Call) else exc
            names.append(
                target.id
                if isinstance(target, ast.Name)
                else target.attr
                if isinstance(target, ast.Attribute)
                else ast.unparse(target)
            )
    return names


def _dispatches_before(statements: list[ast.stmt]) -> list[ast.If]:
    """The type dispatches a ``raise`` at the end of *statements* falls out of.

    Walking back from the ``raise`` over the wording of its message, the
    statements just before it have to be ``if ...: return ...`` with no
    ``else``, at least one of them asking only for a type: ``if isinstance(x,
    A): return ...``, ``if isinstance(x, B): return ...``, ``raise``. Anything
    else between them (a loop, a computation) makes the ``raise`` the end of
    an algorithm, whose refusal is about a value.
    """
    plain = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Pass)
    position = len(statements)
    while position and isinstance(statements[position - 1], plain):
        position -= 1
    chain: list[ast.If] = []
    while position:
        before = statements[position - 1]
        if not (
            isinstance(before, ast.If)
            and not before.orelse
            and isinstance(before.body[-1], ast.Return)
        ):
            break
        chain.append(before)
        position -= 1
    if any(_asks_only_the_type(link.test) for link in chain):
        return chain
    return []


def _fallen_through(statement: ast.If) -> tuple[int, str] | None:
    """The ``else`` of an ``if``/``elif`` chain that refuses what no type matched.

    ``if ...: ... elif isinstance(x, T): ... else: raise ValueError(...)``
    reaches its ``else`` only for an ``x`` that is not a ``T``, so the
    refusal there is a type refusal, whatever the earlier branches test.
    """
    branch = statement
    while len(branch.orelse) == 1 and isinstance(branch.orelse[0], ast.If):
        branch = branch.orelse[0]
    wrong = _wrong(_refusal(branch.orelse))
    if wrong and _asks_only_the_type(branch.test):
        return branch.orelse[-1].lineno, wrong[0]
    return None


def _functions(
    tree: ast.AST, prefix: str = ""
) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield f"{prefix}{node.name}", node
            yield from _functions(node, f"{prefix}{node.name}.")
        elif isinstance(node, ast.ClassDef):
            yield from _functions(node, f"{prefix}{node.name}.")


def _wrong(names: list[str]) -> list[str]:
    return [
        name for name in names if name not in _TYPE_ERRORS and name not in _DATA_ERRORS
    ]


def _blocks(node: ast.AST) -> Iterator[list[ast.stmt]]:
    """Every statement list under *node*, not entering nested functions."""
    for field in ("body", "orelse", "finalbody"):
        block = getattr(node, field, None)
        if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
            yield block
            for statement in block:
                if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield from _blocks(statement)
    for handler in getattr(node, "handlers", ()):
        yield from _blocks(handler)
    for case in getattr(node, "cases", ()):
        yield from _blocks(case)


def type_refusals_as_value_errors(source: str, path: str = "") -> list[str]:
    """Every type refusal in *source* that raises something but ``TypeError``."""
    found: list[str] = []
    for qualname, function in _functions(ast.parse(source)):
        if (
            f"{path}:{qualname}" in EXEMPT
            or f"{path}:{qualname.split('.')[-1]}" in EXEMPT
        ):
            continue
        for block in _blocks(function):
            for index, statement in enumerate(block):
                if isinstance(statement, ast.If):
                    fallen = _fallen_through(statement)
                    if fallen is not None:
                        found.append(
                            f"{qualname}:{fallen[0]} falls through a type "
                            f"dispatch to {fallen[1]}"
                        )
                    wrong = _wrong(_refusal(statement.body))
                    if not wrong:
                        continue
                    if _asks_only_the_type(statement.test):
                        found.append(
                            f"{qualname}:{statement.lineno} refuses a type "
                            f"with {wrong[0]}"
                        )
                    elif _joins_type_and_value(statement.test):
                        found.append(
                            f"{qualname}:{statement.lineno} joins a type and a "
                            f"value question in one refusal ({wrong[0]})"
                        )
                elif isinstance(statement, ast.Raise):
                    wrong = _wrong(_raised([statement]))
                    earlier = _dispatches_before(block[:index])
                    if wrong and earlier:
                        found.append(
                            f"{qualname}:{statement.lineno} falls through "
                            f"{len(earlier)} type dispatches to {wrong[0]}"
                        )
    # An ``elif`` is visited as the chain it ends and as a block of its own.
    return list(dict.fromkeys(found))


def _handler_names(handler: ast.ExceptHandler) -> list[str]:
    caught = handler.type
    if caught is None:
        return []
    parts = caught.elts if isinstance(caught, ast.Tuple) else [caught]
    return [ast.unparse(part) for part in parts]


def relabelled_type_errors(source: str, path: str = "") -> list[str]:
    """Every ``except`` that catches a ``TypeError`` and raises another class.

    ``except (TypeError, ValueError): raise ValueError(msg)`` renames the
    refusal and changes its class with it, so an array handed to a guard that
    refuses it with ``TypeError`` came out as a ``ValueError``. A handler that
    rewords the refusal keeps its class: one ``except TypeError`` raising
    ``TypeError`` and one ``except ValueError`` raising ``ValueError``, or a
    re-raise of ``type(error)``.
    """
    found: list[str] = []
    for qualname, function in _functions(ast.parse(source)):
        if (
            f"{path}:{qualname}" in EXEMPT
            or f"{path}:{qualname.split('.')[-1]}" in EXEMPT
        ):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if "TypeError" not in _handler_names(node):
                continue
            raised = [
                name
                for statement in node.body
                for name in _raised(
                    [
                        inner
                        for inner in ast.walk(statement)
                        if isinstance(inner, ast.Raise)
                    ]
                )
            ]
            wrong = [name for name in _wrong(raised) if not name.startswith("type(")]
            if wrong:
                found.append(
                    f"{qualname}:{node.lineno} catches TypeError and raises {wrong[0]}"
                )
    return found


def _offences() -> list[str]:
    return [
        f"{rel}:{where}"
        for file in sorted(SRC.rglob("*.py"))
        for rel in [file.relative_to(SRC).as_posix()]
        for source in [file.read_text(encoding="utf-8")]
        for where in type_refusals_as_value_errors(source, rel)
        + relabelled_type_errors(source, rel)
    ]


def test_a_wrong_type_raises_type_error() -> None:
    found = _offences()
    assert not found, (
        "type refusals that raise something but TypeError (split a mixed "
        "condition into its type and its value refusal):\n  " + "\n  ".join(found)
    )


def test_every_exemption_names_a_function_that_exists() -> None:
    """An exemption outliving its function would excuse the next one."""
    defined = {
        f"{file.relative_to(SRC).as_posix()}:{name}"
        for file in SRC.rglob("*.py")
        for qualname, _ in _functions(ast.parse(file.read_text(encoding="utf-8")))
        for name in (qualname, qualname.split(".")[-1])
    }
    assert sorted(set(EXEMPT) - defined) == []


_PLANTED = """
def flag(small_room):
    if not isinstance(small_room, bool):
        raise ValueError("'small_room' must be a bool")
    return small_room

def label(value, name):
    if not isinstance(value, str):
        msg = f"'{name}' must be a string"
        raise ValueError(msg)
    return value.strip()

def stories(n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("'n' must be a positive whole number")
    return n

def material(value):
    if isinstance(value, Material):
        return value
    if isinstance(value, Sequence):
        return Material(*value)
    msg = "a Material or a triple"
    raise ValueError(msg)

def optional(value):
    if value is not None and not isinstance(value, int):
        raise ValueError("'value' must be an int or None")
    return value

def mask(obstacle_mask):
    if np.asarray(obstacle_mask).dtype != np.bool_:
        raise ValueError("'obstacle_mask' must be a boolean array")
    return obstacle_mask

def counts(line_counts):
    if line_counts.dtype.kind not in "iu" or np.any(line_counts < 0):
        raise ValueError("'line_counts' must be non-negative integers")
    return line_counts

def real(spectrum):
    if np.iscomplexobj(spectrum):
        raise ValueError("'spectrum' must be real")
    return spectrum

def window(kind):
    if kind is None:
        return "hann"
    elif isinstance(kind, str):
        return kind.lower()
    else:
        raise ValueError("'kind' must be a window name")

def altitude(value):
    height = np.asarray(value, dtype=float)
    if height.ndim != 0:
        raise ValueError("'altitude' must be a single value")
    return float(height)
"""

_ANSWERED = """
def flag(small_room):
    if not isinstance(small_room, bool):
        raise TypeError("'small_room' must be a bool")
    return small_room

def label(value, name):
    if not isinstance(value, str):
        msg = f"'{name}' must be a string"
        raise TypeError(msg)
    return value.strip()

def stories(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("'n' must be a whole number")
    if n < 1:
        raise ValueError("'n' must be at least 1")
    return n

def material(value):
    if isinstance(value, Material):
        return value
    if isinstance(value, Sequence):
        return Material(*value)
    msg = "a Material or a triple"
    raise TypeError(msg)

def rated(x, fs):
    if isinstance(x, Signal) and x.fs != fs:
        raise ValueError("the signal's rate is not 'fs'")
    return x

def counts(line_counts):
    if line_counts.dtype.kind not in "iu":
        raise TypeError("'line_counts' must be integers")
    if np.any(line_counts < 0):
        raise ValueError("'line_counts' must not be negative")
    return line_counts
"""


def test_the_rule_finds_each_shape_of_the_refusal() -> None:
    found = type_refusals_as_value_errors(_PLANTED)
    assert [where.split(":")[0] for where in found] == [
        "flag",
        "label",
        "stories",
        "material",
        "optional",
        "mask",
        "counts",
        "real",
        "window",
        "altitude",
    ]
    assert "joins a type and a value" in found[2]
    assert "falls through 2 type dispatches" in found[3]
    assert "joins a type and a value" in found[6]
    assert "falls through a type dispatch" in found[8]


def test_the_rule_accepts_the_answered_shapes() -> None:
    assert type_refusals_as_value_errors(_ANSWERED) == []


_RELABELLED = """
def numbers(values, name):
    try:
        return np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
"""

_KEPT = """
def numbers(values, name):
    try:
        return np.asarray(values, dtype=float)
    except TypeError as exc:
        msg = f"'{name}' must be numeric."
        raise TypeError(msg) from exc
    except ValueError as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc

def counted(events, owner):
    try:
        return require_count(events, "events")
    except (TypeError, ValueError) as error:
        msg = f"{owner}: {error}"
        raise type(error)(msg) from None
"""


def test_the_rule_finds_a_handler_that_relabels_a_type_error() -> None:
    assert [w.split(":")[0] for w in relabelled_type_errors(_RELABELLED)] == ["numbers"]
    assert relabelled_type_errors(_KEPT) == []


@pytest.mark.parametrize(
    "name", ["_optional_number", "_real"], ids=["payload", "own-checks"]
)
def test_an_exempt_function_is_exempt_by_its_path(name: str) -> None:
    source = f"""
def {name}(value):
    if not isinstance(value, float):
        raise ValueError("a sidecar holds a number here")
    return value
"""
    assert type_refusals_as_value_errors(source, "io/_sidecar.py") == []
    assert type_refusals_as_value_errors(source, "io/elsewhere.py") != []


# ---------------------------------------------------------------------------
# A whole number goes through require_count
# ---------------------------------------------------------------------------

#: The annotations of a parameter that takes a whole number.
_WHOLE = frozenset({"int", "Integral", "numbers.Integral", "np.integer"})

#: The checks that read a whole number: ``require_count`` and the FDTD grid's
#: ``_integer``, which is ``require_count`` with no lower bound.
_COUNT_CHECKS = frozenset({"require_count", "_integer"})


def _takes_a_whole_number(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        text = annotation.value
    else:
        text = ast.unparse(annotation)
    kept = [part.strip() for part in text.split("|") if part.strip() != "None"]
    return bool(kept) and all(part in _WHOLE for part in kept)


def truncated_whole_numbers(source: str) -> list[str]:
    """Every ``int(x)`` of a parameter annotated ``int`` that no count check reads.

    :func:`int` truncates ``2.5`` to ``2`` without a word, takes ``True`` as
    ``1`` and parses ``"3"``, so a count read through it alone accepts a
    fractional count, a flag and a text, and refuses an unreadable text with
    a ``ValueError``. ``require_count`` refuses the bool, the text and the
    array with ``TypeError`` and the fraction with ``ValueError``, and takes a
    whole float such as ``5.0`` as ``5``.
    """
    found: list[str] = []
    for function in ast.walk(ast.parse(source)):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        arguments = function.args
        whole = {
            argument.arg
            for argument in arguments.posonlyargs
            + arguments.args
            + arguments.kwonlyargs
            if _takes_a_whole_number(argument.annotation)
        }
        if not whole:
            continue
        truncated: dict[str, int] = {}
        checked: set[str] = set()
        for node in ast.walk(function):
            if not (
                isinstance(node, ast.Call)
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in whole
            ):
                continue
            called = _called(node)
            if called == "int":
                truncated.setdefault(node.args[0].id, node.lineno)
            elif called in _COUNT_CHECKS:
                checked.add(node.args[0].id)
        found += [
            f"{function.name}({name}):{line}"
            for name, line in sorted(truncated.items())
            if name not in checked
        ]
    return found


def test_a_whole_number_goes_through_require_count() -> None:
    found = [
        f"{file.relative_to(SRC).as_posix()}:{where}"
        for file in sorted(SRC.rglob("*.py"))
        for where in truncated_whole_numbers(file.read_text(encoding="utf-8"))
    ]
    assert not found, (
        "whole numbers read through int() alone (route them through "
        "require_count):\n  " + "\n  ".join(found)
    )


_TRUNCATED = """
def zoom(x, n_points: int = 512):
    require_scalar(n_points, "n_points")
    return x[: int(n_points)]

def harmonics(n_harmonics: int | None = None):
    return range(1, int(n_harmonics) + 1)
"""

_COUNTED = """
def zoom(x, n_points: int = 512):
    return x[: require_count(n_points, "n_points", at_least=2)]

def scaled(gain: float):
    return int(gain)

def ordered(order: int):
    order = require_count(order, "order")
    return int(order)
"""


def test_the_whole_number_rule_finds_a_bare_int() -> None:
    assert [w.split(":")[0] for w in truncated_whole_numbers(_TRUNCATED)] == [
        "zoom(n_points)",
        "harmonics(n_harmonics)",
    ]
    assert truncated_whole_numbers(_COUNTED) == []


# ---------------------------------------------------------------------------
# A TypeError a public function raises is documented
# ---------------------------------------------------------------------------

#: The methods of a public class whose refusals reach the caller.
_PUBLIC_METHODS = frozenset({"__post_init__", "__init__", "__getitem__", "__call__"})


def _own_statements(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[ast.AST]:
    """The nodes of *function*, leaving out the functions and classes it defines."""
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        yield node
        stack.extend(
            child
            for child in ast.iter_child_nodes(node)
            if not isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            )
        )


def _raises_type_error(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int | None:
    for node in _own_statements(function):
        if isinstance(node, ast.Raise) and node.exc is not None:
            raised = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(raised, ast.Name) and raised.id == "TypeError":
                return node.lineno
    return None


def _validators_raising_type_error() -> frozenset[str]:
    """The public validators of ``_internal/validation.py`` that raise TypeError.

    A validator raises it itself, or calls another of the module that does,
    as :func:`require_positive` reaches it through the number check every
    scalar guard shares.
    """
    tree = ast.parse((SRC / "_internal" / "validation.py").read_text(encoding="utf-8"))
    functions = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    raising = {
        name for name, function in functions.items() if _raises_type_error(function)
    }
    grown = True
    while grown:
        grown = False
        for name, function in functions.items():
            called = {
                node.func.id
                for node in ast.walk(function)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            if name not in raising and called & raising:
                raising.add(name)
                grown = True
    return frozenset(name for name in raising if not name.startswith("_"))


#: What a parameter goes through on its way to a validator and stays itself:
#: ``float(x)`` is still the caller's ``x``.
_PASS_THROUGH = frozenset(
    {
        "float",
        "int",
        "complex",
        "tuple",
        "list",
        "np.asarray",
        "np.array",
        "np.atleast_1d",
        "np.asanyarray",
        "operator.index",
    }
)


def _handed_parameter(
    argument: ast.expr, parameters: set[str], *, through_self: bool
) -> str | None:
    """The parameter *argument* is, as given (``x``, ``float(x)``, ``self.x``)."""
    while (
        isinstance(argument, ast.Call)
        and ast.unparse(argument.func) in _PASS_THROUGH
        and argument.args
    ):
        argument = argument.args[0]
    if isinstance(argument, ast.Name) and argument.id in parameters:
        return argument.id
    if (
        through_self
        and isinstance(argument, ast.Attribute)
        and isinstance(argument.value, ast.Name)
        and argument.value.id == "self"
    ):
        return argument.attr
    return None


def _parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    arguments = function.args
    return [
        a.arg
        for a in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *([arguments.vararg] if arguments.vararg else []),
            *([arguments.kwarg] if arguments.kwarg else []),
        )
    ]


def _hands_to_a_type_checking_validator(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    helpers: dict[str, ast.FunctionDef],
    validators: frozenset[str],
    *,
    through_self: bool,
    depth: int = 0,
) -> set[str]:
    """The parameters *function* hands as given to a validator raising TypeError.

    The validator is called with the parameter itself as its first argument,
    by *function* or by a private helper of the same module it hands the
    parameter to, four calls deep at most. A parameter only read to build
    another value (``fluid.density``) is not handed: the validator refuses
    that value, not the caller's argument.
    """
    parameters = set(_parameters(function)) - {"self", "cls"}
    handed: set[str] = set()
    for node in _own_statements(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        name = node.func.id
        if name in validators and node.args:
            parameter = _handed_parameter(
                node.args[0], parameters, through_self=through_self
            )
            if parameter is not None:
                handed.add(parameter)
        # Four calls deep
        elif name in helpers and depth < 4:  # noqa: PLR2004
            helper = helpers[name]
            reached = _hands_to_a_type_checking_validator(
                helper, helpers, validators, through_self=False, depth=depth + 1
            )
            bound = dict(zip(_parameters(helper), node.args, strict=False))
            bound.update({k.arg: k.value for k in node.keywords if k.arg})
            for helper_parameter in reached:
                if helper_parameter in bound:
                    parameter = _handed_parameter(
                        bound[helper_parameter], parameters, through_self=through_self
                    )
                    if parameter is not None:
                        handed.add(parameter)
    return handed


#: The text of the ``:raises TypeError:`` fields of a docstring, each up to the
#: next field; a continuation line that opens with a role (``:class:``) stays.
_TYPE_ERROR_FIELD = re.compile(
    r":raises TypeError:(.*?)"
    r"(?=\n\s*:(?:param|raises|return|returns|rtype|ivar|var|cvar|type|yields?)\b|\Z)",
    re.DOTALL,
)


def _unnamed(handed: set[str], documented: str) -> list[str]:
    """The parameters of *handed* no ``:raises TypeError:`` field names."""
    field = " ".join(m.group(1) for m in _TYPE_ERROR_FIELD.finditer(documented))
    return sorted(p for p in handed if not re.search(rf"\b{re.escape(p)}\b", field))


def undocumented_type_errors(
    source: str, validators: frozenset[str] | None = None
) -> list[str]:
    """Every public function that raises ``TypeError`` and does not say so.

    The API reference is generated from the ``:raises`` fields, so a refusal
    whose class changed to ``TypeError`` while the docstring kept listing the
    case under ``ValueError`` publishes the old class. A public function (or
    the constructor of a public class, whose class docstring may carry the
    field instead) that raises ``TypeError`` itself, or hands a parameter as
    it was given to a shared validator of ``_internal/validation.py`` that
    raises it (:func:`require_band_fraction` for a band set written as a word,
    :func:`require_scalar` for an array where one number goes), documents it
    with ``:raises TypeError:``, and that field names every parameter it hands
    on: a field about one parameter does not tell the caller that another is
    refused the same way.
    """
    if validators is None:
        validators = _validators_raising_type_error()
    tree = ast.parse(source)
    helpers = {
        f.name: f
        for f in tree.body
        if isinstance(f, ast.FunctionDef) and f.name.startswith("_")
    }
    found: list[str] = []

    def visit(node: ast.AST, owner: ast.ClassDef | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, child)
                continue
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if owner is None:
                public = not child.name.startswith("_")
            else:
                public = not owner.name.startswith("_") and (
                    not child.name.startswith("_") or child.name in _PUBLIC_METHODS
                )
            if not public:
                continue
            through_self = owner is not None and child.name in _PUBLIC_METHODS
            handed = _hands_to_a_type_checking_validator(
                child, helpers, validators, through_self=through_self
            )
            line = _raises_type_error(child)
            if line is None and handed:
                line = child.lineno
            if line is None:
                continue
            documented = ast.get_docstring(child) or ""
            if owner is not None and child.name in {"__post_init__", "__init__"}:
                documented += "\n" + (ast.get_docstring(owner) or "")
            where = child.name if owner is None else f"{owner.name}.{child.name}"
            if ":raises TypeError" not in documented:
                found.append(f"{where}:{line}")
            elif unnamed := _unnamed(handed, documented):
                found.append(f"{where}:{line} names no {', '.join(unnamed)}")

    visit(tree, None)
    return found


def test_a_public_function_that_raises_type_error_documents_it() -> None:
    found = [
        f"{file.relative_to(SRC).as_posix()}:{where}"
        for file in sorted(SRC.rglob("*.py"))
        for where in undocumented_type_errors(file.read_text(encoding="utf-8"))
    ]
    assert not found, (
        "public functions that raise TypeError without a ':raises TypeError:' "
        "field:\n  " + "\n  ".join(found)
    )


_UNDOCUMENTED = '''
def flag(small_room):
    """Whether the room is small.

    :raises ValueError: if small_room is not True or False.
    """
    if not isinstance(small_room, bool):
        raise TypeError("'small_room' must be True or False")
    return small_room

class Rating:
    def __post_init__(self):
        """Check the rating.

        :raises ValueError: if the rating is not an integer.
        """
        if not isinstance(self.rating, int):
            raise TypeError("'rating' must be an integer")
'''

_DOCUMENTED = '''
def flag(small_room):
    """Whether the room is small.

    :raises TypeError: if small_room is not True or False.
    """
    if not isinstance(small_room, bool):
        raise TypeError("'small_room' must be True or False")
    return small_room

class Rating:
    """A rating.

    :raises TypeError: if the rating is not an integer.
    """

    def __post_init__(self):
        if not isinstance(self.rating, int):
            raise TypeError("'rating' must be an integer")

def _private(value):
    raise TypeError("a helper's own refusal is its caller's to document")
'''


def test_the_docstring_rule_finds_an_undocumented_type_error() -> None:
    assert [w.split(":")[0] for w in undocumented_type_errors(_UNDOCUMENTED)] == [
        "flag",
        "Rating.__post_init__",
    ]
    assert undocumented_type_errors(_DOCUMENTED) == []


_THROUGH_VALIDATORS = '''
def rating(levels, fraction=3):
    """A rating.

    :raises ValueError: for a fraction other than 1 and 3.
    """
    require_band_fraction(fraction)
    return levels


def corrected(level, fs):
    """A correction, its sample rate checked by a helper.

    :raises ValueError: for a negative level.
    """
    return _checked(float(fs)) + level


def _checked(rate):
    return require_positive(rate, "fs")


def derived(fluid):
    """A value read off a record: the record is not the number refused.

    :raises ValueError: for a negative density.
    """
    return require_positive(fluid.density, "density")


def documented(levels, fraction=3):
    """A rating.

    :raises TypeError: if ``fraction`` is not an integer.
    """
    require_band_fraction(fraction)
    return levels


class Check:
    def __post_init__(self):
        """Check the check.

        :raises ValueError: for an unknown mode.
        """
        require_choice(self.mode, "mode", ("a", "b"))
'''


def test_a_type_error_a_shared_validator_raises_is_documented_too() -> None:
    """A parameter handed as given to a validator that raises TypeError makes
    the TypeError the function's own, called directly, through a private
    helper or off ``self`` in a constructor; a value read off a record is not
    the caller's argument and does not count.
    """
    validators = frozenset(
        {"require_band_fraction", "require_positive", "require_choice"}
    )
    found = [
        where.split(":")[0]
        for where in undocumented_type_errors(_THROUGH_VALIDATORS, validators)
    ]
    assert found == ["rating", "corrected", "Check.__post_init__"]


_NAMES_ANOTHER = '''
def sound_power(speed, alpha, *, reference=None):
    """A source spectrum.

    :raises TypeError: If ``reference`` is not a spectrum.
    """
    require_scalar(speed, "speed")
    require_scalar(alpha, "alpha")
    if reference is not None and not isinstance(reference, tuple):
        raise TypeError("'reference' must be a spectrum")
    return speed


def named(speed, alpha):
    """A source spectrum.

    :raises TypeError: If ``reference`` is not a spectrum, or ``speed`` or
        ``alpha`` is not one number.
    """
    require_scalar(speed, "speed")
    return require_scalar(alpha, "alpha")
'''


def test_a_type_error_field_names_every_parameter_it_hands_on() -> None:
    """A field about another parameter does not document the refusal of the
    ones handed to a validator: each is named in a ``:raises TypeError:``.
    """
    found = undocumented_type_errors(_NAMES_ANOTHER, frozenset({"require_scalar"}))
    assert found == ["sound_power:10 names no alpha, speed"]


def test_the_validators_the_rule_follows_include_the_band_set_and_the_scalar() -> None:
    validators = _validators_raising_type_error()
    assert {"require_band_fraction", "require_scalar", "require_choice"} <= validators
    assert not any(name.startswith("_") for name in validators)
