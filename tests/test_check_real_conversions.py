#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for scripts/check_real_conversions.py, the guard of a caller's complex value.

The guard reads every module under ``src/phonometry`` and fails on a
conversion to floats of a caller's value that no check has read first, the
conversion that took ``0.5 + 0.3j`` for 0.5. These plant each shape it exists
for and each shape that answers it, check that every shared check it trusts
does refuse a complex value, and hold the package to the rule.
"""

from __future__ import annotations

import ast
import sys
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry._internal import validation

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_real_conversions as guard  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable


def _verdicts(tmp_path: Path, source: str) -> dict[str, str]:
    """``{function: verdict}`` for each conversion of *source*, one module of the package."""
    path = tmp_path / "phonometry" / "planted.py"
    path.parent.mkdir(exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return {c.function: c.verdict for c in guard.census([path], library=False)}


@pytest.fixture(scope="module")
def tree_census() -> list[guard.Conversion]:
    """Every conversion to floats of the library, taken once for the module."""
    return guard.census(sorted(guard.SOURCE.rglob("*.py")))


_UNCHECKED = """
import numpy as np

def bare(levels):
    return np.asarray(levels, dtype=np.float64)

def copied(levels):
    return np.array(levels, dtype=float)

def item(pair):
    return np.asarray(pair[0], dtype=np.float64)

def kept(levels):
    shaped = np.atleast_1d(levels)
    return np.asarray(shaped, dtype=np.float64)

def looped(rows):
    return [np.asarray(row, dtype=np.float64) for row in rows]

def cast(samples):
    return samples.astype(np.float64)

def scalar(value):
    return np.float64(value)

def positional(levels):
    return np.asarray(levels, float)

class Record:
    def __post_init__(self):
        object.__setattr__(self, "levels", np.asarray(self.levels, dtype=np.float64))
"""

_ANSWERED = """
import numpy as np

from phonometry._internal.validation import real_array, refuse_complex, require_finite_array

def read(levels):
    return real_array(levels, "levels")

def refused_first(levels):
    refuse_complex(levels, "'levels' must be real")
    return np.asarray(levels, dtype=np.float64)

def rebound(levels):
    levels = require_finite_array(levels, "levels")
    return np.asarray(levels, dtype=np.float64)

def _real_numbers(name, value):
    refuse_complex(value, f"{name} must be real")

def through_a_local_check(levels):
    _real_numbers("levels", levels)
    return np.asarray(levels, dtype=np.float64)

def computed(levels):
    return np.asarray(real_array(levels, "levels") + 3.0, dtype=np.float64)

def arithmetic(levels):
    return np.asarray(10.0 ** (levels / 10.0), dtype=np.float64)

def own(n):
    return np.asarray(np.arange(n), dtype=np.float64)

def integers(levels):
    return np.asarray(levels, dtype=np.int64)

class Record:
    def __post_init__(self):
        object.__setattr__(self, "levels", real_array(self.levels, "levels"))

    def total(self):
        return np.asarray(self.levels, dtype=np.float64).sum()
"""


def test_each_shape_of_a_caller_s_value_is_found(tmp_path: Path) -> None:
    """A parameter read bare, copied, by an item, through a call that keeps its
    dtype or in a loop, cast with ``astype``, a NumPy scalar, a positional
    dtype, and a field in ``__post_init__``.
    """
    verdicts = _verdicts(tmp_path, _UNCHECKED)
    assert verdicts == {
        "bare": "unchecked",
        "copied": "unchecked",
        "item": "unchecked",
        "kept": "unchecked",
        "looped": "unchecked",
        "cast": "unchecked",
        "scalar": "unchecked",
        "positional": "unchecked",
        "Record.__post_init__": "unchecked",
    }


def test_each_shape_that_answers_it_passes(tmp_path: Path) -> None:
    """The shared reader, a check first, a name rebound to a check, a check of the
    module on any parameter, a value the function computed, a field a method reads.
    """
    verdicts = _verdicts(tmp_path, _ANSWERED)
    assert verdicts == {
        "refused_first": "checked",
        "rebound": "checked",
        "through_a_local_check": "checked",
        "computed": "computed",
        "arithmetic": "computed",
        "own": "computed",
        "Record.total": "field",
    }


def test_a_check_after_the_conversion_does_not_answer_it(tmp_path: Path) -> None:
    source = """
    import numpy as np

    from phonometry._internal.validation import refuse_complex

    def late(levels):
        out = np.asarray(levels, dtype=np.float64)
        refuse_complex(levels, "'levels' must be real")
        return out
    """
    assert _verdicts(tmp_path, source) == {"late": "unchecked"}


def test_a_check_of_another_module_is_known_by_the_module(tmp_path: Path) -> None:
    """A function of the module's own that only shares a check's name checks nothing."""
    source = """
    import numpy as np

    def refuse_complex(value, msg):
        return None

    def shadowed(levels):
        refuse_complex(levels, "no check")
        return np.asarray(levels, dtype=np.float64)
    """
    assert _verdicts(tmp_path, source) == {"shadowed": "unchecked"}


#: A call of each shared check with a complex value where its number goes.
_COMPLEX_CALLS: dict[str, Callable[[], object]] = {
    "real_array": lambda: validation.real_array([1 + 2j], "x"),
    "refuse_complex": lambda: validation.refuse_complex([np.complex128(1)], "x"),
    "holds_complex": lambda: None,
    "require_real": lambda: validation.require_real(np.complex128(1 + 1j), "x"),
    "require_scalar": lambda: validation.require_scalar(np.complex128(1 + 1j), "x"),
    "require_positive": lambda: validation.require_positive(np.complex128(2 + 1j), "x"),
    "require_non_negative": lambda: validation.require_non_negative(
        np.complex128(2 + 1j), "x"
    ),
    "require_finite": lambda: validation.require_finite(np.complex128(2 + 1j), "x"),
    "require_fraction": lambda: validation.require_fraction(np.complex128(0.5j), "x"),
    "require_count": lambda: validation.require_count(np.complex128(2), "x"),
    "require_above_absolute_zero": lambda: validation.require_above_absolute_zero(
        np.complex128(20 + 1j), "x"
    ),
    "require_above_absolute_zero_array": (
        lambda: validation.require_above_absolute_zero_array([20 + 1j], "x")
    ),
    "require_positive_array": lambda: validation.require_positive_array([2 + 1j], "x"),
    "require_finite_array": lambda: validation.require_finite_array([2 + 1j], "x"),
    "require_finite_matrix": lambda: validation.require_finite_matrix([[2 + 1j]], "x"),
    "require_1d_signal": lambda: validation.require_1d_signal([2 + 1j], "x"),
    "require_per_band": lambda: validation.require_per_band(
        [2 + 1j], "x", np.array([100.0]), "frequencies"
    ),
    "arrays_of": lambda: validation.arrays_of(([1 + 1j], [1.0]), "x", "a pair", 2),
    "pair_of_arrays": lambda: validation.pair_of_arrays(
        ([1 + 1j], [1.0]), "x", "(a, b)"
    ),
    "floats_of": lambda: validation.floats_of([np.complex128(1)], "x", "numbers"),
    "pair_of_floats": lambda: validation.pair_of_floats(
        (np.complex128(1), 2.0), "x", "(a, b)"
    ),
}


def test_every_check_the_guard_trusts_is_listed_here() -> None:
    assert set(_COMPLEX_CALLS) == guard.CHECKS


@pytest.mark.parametrize("name", sorted(set(_COMPLEX_CALLS) - {"holds_complex"}))
def test_every_check_the_guard_trusts_refuses_a_complex_value(name: str) -> None:
    with pytest.raises(TypeError):
        _COMPLEX_CALLS[name]()


def test_the_predicate_the_guard_trusts_finds_a_complex_value() -> None:
    assert validation.holds_complex(np.array([1.0, np.complex128(1j)], dtype=object))
    assert not validation.holds_complex(np.array([1.0, 2.0]))


def test_every_exemption_names_a_function_that_exists() -> None:
    for (file, function), reason in guard.EXEMPT.items():
        tree = ast.parse((ROOT / file).read_text(encoding="utf-8"))
        names = {qualified for qualified, _ in guard._functions(tree)}
        assert function in names, (file, function)
        assert reason


def test_the_package_keeps_the_rule(tree_census: list[guard.Conversion]) -> None:
    unchecked = [c for c in tree_census if c.verdict == "unchecked"]
    left, stale = guard.exempted(unchecked, guard.EXEMPT)
    assert [c.describe() for c in left] == []
    assert stale == []


def test_the_census_lists_the_whole_class(
    tree_census: list[guard.Conversion],
) -> None:
    """Every kind of conversion is there, and none of a caller's value is left."""
    census = tree_census
    kinds = {c.verdict for c in census}
    assert kinds == {"unchecked", "checked", "computed", "field"}
    unchecked = {c.key for c in census if c.verdict == "unchecked"}
    assert unchecked <= set(guard.EXEMPT)
