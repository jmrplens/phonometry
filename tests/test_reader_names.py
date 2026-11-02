#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A reader of a caller's number names the parameter the number came from.

Every check of ``_internal/validation.py`` that takes ``(value, name)`` writes
``name`` into what it refuses, and the caller looks for that name among the
parameters of the function they called. A reading inside a loop that handed
the loop's own variable named nothing the caller wrote:
``signals.tone_burst(pre_silence="0.1")`` was refused as ``'value' must be one
number``, ``environment.amplitude_modulation_block(modulation_frequency_range_hz=
("0.5", 2.0))`` as ``'v' must be one number``, and a reading in an error
message of the pile-driving spectrum named ``'np'``, the alias of NumPy.

The calls below hold each public function that reads such a number to the
parameter's name, and the AST check holds the tree: a name handed to a reader
is never a variable a ``for`` or a comprehension binds where the call is, never
the alias of an imported module, and never the iterable of another variable
of the same ``zip`` (``real_number(i, "ks")`` over
``zip(ks, pressure, intensity)``).
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import textwrap
from typing import TYPE_CHECKING

import numpy as np
import pytest

import phonometry
from phonometry import broadcast, environment, hearing, materials, room, signals
from phonometry._internal import validation

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_SOURCE = pathlib.Path(phonometry.__file__).parent


def _readers() -> frozenset[str]:
    """The checks of the validation module that take ``(value, name)``."""
    found = set()
    for attribute, member in vars(validation).items():
        if not inspect.isfunction(member) or member.__module__ != validation.__name__:
            continue
        parameters = list(inspect.signature(member).parameters)
        if len(parameters) >= 2 and parameters[1] == "name":  # noqa: PLR2004
            found.add(attribute)
    return frozenset(found)


_READERS = _readers()


def _roots(node: ast.AST) -> set[str]:
    """The names and attributes an expression is written from."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)
    }


def _bind(target: ast.expr, iterable: ast.expr, into: dict[str, ast.expr]) -> None:
    """Record what each variable of a loop *target* runs over."""
    if isinstance(target, ast.Name):
        into[target.id] = iterable
        return
    if not isinstance(target, ast.Tuple | ast.List):
        return
    if (
        isinstance(iterable, ast.Call)
        and isinstance(iterable.func, ast.Name)
        and iterable.func.id == "zip"
        and len(iterable.args) == len(target.elts)
    ):
        for element, argument in zip(target.elts, iterable.args, strict=True):
            _bind(element, argument, into)
        return
    for element in target.elts:
        _bind(element, iterable, into)


def _module_aliases(tree: ast.Module) -> frozenset[str]:
    """The names an ``import`` statement of *tree* binds to a module."""
    return frozenset(
        alias.asname or alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )


class _Reader(ast.NodeVisitor):
    """Walks one module, keeping what each loop variable in scope runs over."""

    def __init__(self, where: str, aliases: frozenset[str]) -> None:
        self.where = where
        self.aliases = aliases
        self.loops: list[dict[str, ast.expr]] = [{}]
        self.found: list[str] = []

    def _scope(self, node: ast.AST) -> None:
        self.loops.append({})
        self.generic_visit(node)
        self.loops.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_Lambda = _scope

    def _with_loop(self, bound: dict[str, ast.expr], body: list[ast.AST]) -> None:
        self.loops.append({**self.loops[-1], **bound})
        for node in body:
            self.visit(node)
        self.loops.pop()

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        bound: dict[str, ast.expr] = {}
        _bind(node.target, node.iter, bound)
        self._with_loop(bound, [*node.body, *node.orelse])

    visit_AsyncFor = visit_For

    def _comprehension(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> None:
        bound: dict[str, ast.expr] = {}
        for generator in node.generators:
            self.visit(generator.iter)
            _bind(generator.target, generator.iter, bound)
        parts = [part for generator in node.generators for part in generator.ifs]
        if isinstance(node, ast.DictComp):
            parts += [node.key, node.value]
        else:
            parts.append(node.elt)
        self._with_loop(bound, parts)

    visit_ListComp = visit_SetComp = visit_GeneratorExp = visit_DictComp = (
        _comprehension
    )

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id in _READERS
            and len(node.args) >= 2  # noqa: PLR2004
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            return
        reason = self._misnaming(node.args[0], node.args[1].value)
        if reason:
            self.found.append(
                f"{self.where}:{node.lineno}: {ast.unparse(node)} {reason}"
            )

    def _misnaming(self, value: ast.expr, name: str) -> str | None:
        loops = self.loops[-1]
        if name in self.aliases:
            return "names an imported module"
        if name in loops:
            return "names a loop's variable"
        if not (isinstance(value, ast.Name) and value.id in loops):
            return None
        own = _roots(loops[value.id])
        others = set().union(*(_roots(it) for it in loops.values())) - own
        if name in others:
            return "names another value of the loop"
        return None


def misnamed_readings(root: pathlib.Path) -> list[str]:
    """Every reading under *root* whose name is no parameter the value came from."""
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        reader = _Reader(str(path.relative_to(root)), _module_aliases(tree))
        reader.visit(tree)
        found += reader.found
    return found


def _misnamed_in(source: str) -> list[str]:
    tree = ast.parse(textwrap.dedent(source))
    reader = _Reader("planted.py", _module_aliases(tree))
    reader.visit(tree)
    return reader.found


def test_the_library_hands_every_reader_a_parameter_s_name() -> None:
    assert misnamed_readings(_SOURCE) == []


@pytest.mark.parametrize(
    "source",
    [
        # The loop's own variable.
        """
        def burst(pre, post):
            for name, value in (("pre", pre), ("post", post)):
                real_number(value, "value")
        """,
        # A comprehension's variable.
        """
        def band(range_hz):
            return tuple(real_number(v, "v") for v in range_hz)
        """,
        # A variable of a generator expression handed to any().
        """
        def deltas(a, b):
            return any(require_finite(d, "d") for d in (a, b))
        """,
        # The alias of an imported module.
        """
        import numpy as np

        def message(frequencies, i):
            return real_number(np.asarray(frequencies)[i], "np")
        """,
        # The iterable of another variable of the same zip.
        """
        def annex(ks, pressure, intensity):
            for k, p, i in zip(ks, pressure, intensity, strict=True):
                complex_number(i, "ks")
        """,
    ],
)
def test_the_check_finds_a_reading_named_after_no_parameter(source: str) -> None:
    assert len(_misnamed_in(source)) == 1


@pytest.mark.parametrize(
    "source",
    [
        # The loop hands the reader the parameter's name it carries.
        """
        def burst(pre, post):
            for name, value in (("pre", pre), ("post", post)):
                real_number(value, name)
        """,
        # The iterable's own name.
        """
        def band(range_hz):
            return tuple(real_number(v, "range_hz") for v in range_hz)
        """,
        # A helper's parameter that shares a name with a loop elsewhere.
        """
        def outer(values):
            for value in values:
                pass

            def fmt(value):
                return real_number(value, "value")

            return fmt
        """,
    ],
)
def test_the_check_passes_a_reading_named_after_its_parameter(source: str) -> None:
    assert _misnamed_in(source) == []


_LEVELS = np.full(22, 90.0)
_OCCLUDED = np.full((3, 22), 70.0)

#: A public call per reading the tree named after a loop, given a text where
#: one number goes, and the parameter the refusal must name.
_CALLS: list[tuple[str, Callable[[], object], str]] = [
    (
        "signals.tone_burst pre_silence",
        lambda: signals.tone_burst(48_000, 1000, 4, pre_silence="0.1"),
        "pre_silence",
    ),
    (
        "signals.tone_burst post_silence",
        lambda: signals.tone_burst(48_000, 1000, 4, post_silence="0.1"),
        "post_silence",
    ),
    (
        "environment.amplitude_modulation_block",
        lambda: environment.amplitude_modulation_block(
            np.full(100, 40.0), modulation_frequency_range_hz=("0.5", 2.0)
        ),
        "modulation_frequency_range_hz",
    ),
    (
        "hearing.earmuff_insertion_loss fixture",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, fixture_uncertainty_db="1"
        ),
        "fixture_uncertainty_db",
    ),
    (
        "hearing.earmuff_insertion_loss sound field",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, sound_field_uncertainty_db="1"
        ),
        "sound_field_uncertainty_db",
    ),
    (
        "hearing.earmuff_insertion_loss equipment",
        lambda: hearing.earmuff_insertion_loss(
            _LEVELS, _OCCLUDED, equipment_uncertainty_db="1"
        ),
        "equipment_uncertainty_db",
    ),
    (
        "broadcast.QuasiPeakDynamicsResult",
        lambda: broadcast.QuasiPeakDynamicsResult(
            fs=48_000.0, readings_percent=("50",) * 11
        ),
        "readings_percent",
    ),
    (
        "room.sabine_reverberation_time",
        lambda: room.sabine_reverberation_time(100.0, [("10", 0.5)]),
        "surfaces",
    ),
    (
        "room.reverberation_time_models",
        lambda: room.reverberation_time_models(("5", 4.0, 3.0), (0.2, 0.2, 0.2)),
        "dimensions",
    ),
    (
        "materials.frame_bulk_modulus",
        lambda: materials.frame_bulk_modulus("1e5", 0.3),
        "shear_modulus",
    ),
]


def _ids() -> Iterator[str]:
    return (label for label, _, _ in _CALLS)


@pytest.mark.parametrize(("label", "call", "parameter"), _CALLS, ids=list(_ids()))
def test_a_text_is_refused_by_the_parameter_s_name(
    label: str, call: Callable[[], object], parameter: str
) -> None:
    with pytest.raises(TypeError, match=f"'{parameter}' must be"):
        call()
