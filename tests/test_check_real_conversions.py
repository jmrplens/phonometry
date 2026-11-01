#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for scripts/check_real_conversions.py, the guard of a caller's numbers.

The guard reads every module under ``src/phonometry`` and fails on a
conversion of a caller's value that no check has read on every path to it,
the conversion that took ``np.complex128(0.5 + 0.3j)`` for 0.5 and parsed
``["94"]`` as 94. These plant each shape it exists for and each shape that
answers it, check that every shared check it trusts refuses what the guard
says it refuses, and hold the package to the rule.
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
    return {c.function: c.verdict for c in guard.census([path], source=None)}


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

from phonometry._internal.validation import (
    real_array,
    refuse_complex,
    refuse_text,
    require_finite_array,
)

def read(levels):
    return real_array(levels, "levels")

def refused_first(levels):
    refuse_complex(levels, "'levels' must be real")
    refuse_text(levels, "'levels' must be numbers")
    return np.asarray(levels, dtype=np.float64)

def rebound(levels):
    levels = require_finite_array(levels, "levels")
    return np.asarray(levels, dtype=np.float64)

def _real_numbers(name, value):
    refuse_complex(value, f"{name} must be real")
    refuse_text(value, f"{name} must be numbers")

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


#: A call of each shared check with *value* where its number goes.
_CALLS: dict[str, Callable[[object], object]] = {
    "real_array": lambda v: validation.real_array(v, "x"),
    "complex_array": lambda v: validation.complex_array(v, "x"),
    "refuse_complex": lambda v: validation.refuse_complex(v, "x"),
    "refuse_text": lambda v: validation.refuse_text(v, "x"),
    "refuse_text_beside_choice": lambda v: validation.refuse_text_beside_choice(
        v, "x", ("rigid",)
    ),
    "require_real": lambda v: validation.require_real(v, "x"),
    "require_scalar": lambda v: validation.require_scalar(v, "x"),
    "require_positive": lambda v: validation.require_positive(v, "x"),
    "require_non_negative": lambda v: validation.require_non_negative(v, "x"),
    "require_finite": lambda v: validation.require_finite(v, "x"),
    "require_fraction": lambda v: validation.require_fraction(v, "x"),
    "require_count": lambda v: validation.require_count(v, "x"),
    "require_above_absolute_zero": lambda v: validation.require_above_absolute_zero(
        v, "x"
    ),
    "require_above_absolute_zero_array": (
        lambda v: validation.require_above_absolute_zero_array(v, "x")
    ),
    "require_positive_array": lambda v: validation.require_positive_array(v, "x"),
    "require_finite_array": lambda v: validation.require_finite_array(v, "x"),
    "require_finite_matrix": lambda v: validation.require_finite_matrix(v, "x"),
    "require_1d_signal": lambda v: validation.require_1d_signal(v, "x"),
    "require_per_band": lambda v: validation.require_per_band(
        v, "x", np.array([100.0]), "frequencies"
    ),
    "arrays_of": lambda v: validation.arrays_of((v, [1.0]), "x", "a pair", 2),
    "pair_of_arrays": lambda v: validation.pair_of_arrays((v, [1.0]), "x", "(a, b)"),
    "floats_of": lambda v: validation.floats_of(v, "x", "numbers"),
    "pair_of_floats": lambda v: validation.pair_of_floats((v, 2.0), "x", "(a, b)"),
}

#: What each check is given for one number, for an array, and the complex
#: value and the texts each kind is tried with.
_ONE_NUMBER = frozenset(
    {
        "require_real",
        "require_scalar",
        "require_positive",
        "require_non_negative",
        "require_finite",
        "require_fraction",
        "require_count",
        "require_above_absolute_zero",
        "pair_of_floats",
    }
)
_COMPLEX = {"one": np.complex128(0.5 + 0.25j), "many": [np.complex128(0.5 + 0.25j)]}
_TEXTS = {"one": ("0.5", b"0.5"), "many": (["0.5"], [bytearray(b"12")])}


def test_every_check_the_guard_trusts_is_listed_here() -> None:
    assert set(_CALLS) == set(guard.CHECKS)


@pytest.mark.parametrize(
    "name", sorted(n for n, refused in guard.CHECKS.items() if "complex" in refused)
)
def test_every_check_said_to_refuse_a_complex_value_does(name: str) -> None:
    value = _COMPLEX["one" if name in _ONE_NUMBER else "many"]
    with pytest.raises(TypeError):
        _CALLS[name](value)


@pytest.mark.parametrize(
    "name", sorted(n for n, refused in guard.CHECKS.items() if "text" in refused)
)
def test_every_check_said_to_refuse_a_text_does(name: str) -> None:
    for value in _TEXTS["one" if name in _ONE_NUMBER else "many"]:
        with pytest.raises(TypeError):
            _CALLS[name](value)


def test_a_predicate_is_no_check(tmp_path: Path) -> None:
    """``holds_complex`` answers a question and refuses nothing, so the guard
    does not trust it: a conversion after it is the caller's value still.
    """
    assert "holds_complex" not in guard.CHECKS
    source = """
    import numpy as np

    from phonometry._internal.validation import holds_complex

    def asked(levels):
        flag = holds_complex(levels)
        return flag, np.asarray(levels, dtype=np.float64)
    """
    assert _verdicts(tmp_path, source) == {"asked": "unchecked"}


#: Each shape a caller's value reaches a conversion in, one function each,
#: that no check has read on every path to it: what the guard must report.
_PLANTED_UNCHECKED = {
    "checked_in_one_branch": """
        def f(levels, flag):
            if flag:
                levels = real_array(levels, "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_in_the_other_branch": """
        def f(levels, flag):
            if flag:
                require_finite_array(levels, "levels")
            else:
                return np.asarray(levels, dtype=np.float64)
            return None
    """,
    "checked_in_a_loop": """
        def f(levels, rows):
            for _ in rows:
                levels = real_array(levels, "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_after_or": """
        def f(levels, flag):
            ok = flag or require_finite_array(levels, "levels")
            return ok, np.asarray(levels, dtype=np.float64)
    """,
    "rebound_in_a_branch": """
        def f(levels, other, flag):
            levels = real_array(levels, "levels")
            if flag:
                levels = other
            return np.asarray(levels, dtype=np.float64)
    """,
    "an_item_checked": """
        def f(levels):
            require_finite(levels[0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "an_item_read": """
        def f(levels):
            real_array(levels[0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "default_of_getattr": """
        def f(value):
            values = getattr(value, "values", value)
            return np.asarray(values, dtype=np.float64)
    """,
    "comprehension_of_items": """
        def f(periods):
            return np.array([h for _, h, _ in periods], dtype=float)
    """,
    "comprehension_of_a_part": """
        def f(rows):
            return np.array([row[1] for row in rows], dtype=float)
    """,
    "dtype_object": """
        def f(levels):
            return np.asarray(levels, dtype=np.dtype(float))
    """,
    "byte_order": """
        def f(levels):
            return np.asarray(levels, dtype="<f8")
    """,
    "dtype_in_a_name": """
        REAL = np.float64

        def f(levels):
            return np.asarray(levels, dtype=REAL)
    """,
    "dtype_by_default": """
        def f(levels, dtype=np.float64):
            return np.asarray(levels, dtype=dtype)
    """,
    "imported_by_name": """
        from numpy import asarray

        def f(levels):
            return asarray(levels, dtype=float)
    """,
    "fromiter": """
        def f(levels):
            return np.fromiter(levels, dtype=float)
    """,
    "require": """
        def f(levels):
            return np.require(levels, dtype=float)
    """,
    "fill": """
        def f(level, n):
            return np.full(n, level, dtype=float)
    """,
    "fill_like": """
        def f(level, like):
            return np.full_like(like, level, dtype=float)
    """,
    "joined": """
        def f(levels, more):
            return np.concatenate([levels, more]).astype(float)
    """,
    "stacked": """
        def f(rows):
            return np.vstack(rows).astype(np.float64)
    """,
    "transposed": """
        def f(matrix):
            return np.asarray(matrix.T, dtype=np.float64)
    """,
    "nested": """
        def f(levels):
            def g(values):
                return np.asarray(values, dtype=np.float64)

            return g(real_array(levels, "levels"))
    """,
    "complex_only_refused": """
        def f(levels):
            refuse_complex(levels, "'levels' must be real")
            return np.asarray(levels, dtype=np.float64)
    """,
    "to_complex": """
        def f(impedance):
            return np.asarray(impedance, dtype=np.complex128)
    """,
    "to_complex_text": """
        def f(impedance):
            return np.asarray(impedance, dtype="c16")
    """,
    "to_complex_scalar": """
        def f(impedance):
            return np.complex128(impedance)
    """,
    "to_complex_after_a_complex_refusal": """
        def f(impedance):
            refuse_complex(impedance, "no")
            return np.asarray(impedance, dtype=complex)
    """,
    "a_check_in_a_branch_of_a_helper": """
        def _maybe(levels, flag):
            if flag:
                real_array(levels, "levels")

        def f(levels, flag):
            _maybe(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
}

#: The shapes that answer one: a check on every path, or no caller's value.
_PLANTED_ANSWERED = {
    "checked_in_both_branches": """
        def f(levels, flag):
            if flag:
                levels = real_array(levels, "levels")
            else:
                levels = real_array(levels[::-1], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "other_branch_leaves": """
        def f(levels, flag):
            if flag:
                levels = real_array(levels, "levels")
            else:
                raise ValueError("no")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_in_the_same_branch": """
        def f(levels, flag):
            if flag:
                levels = real_array(levels, "levels")
                return np.asarray(levels, dtype=np.float64)
            return None
    """,
    "checked_before_a_try": """
        def f(levels):
            try:
                levels = real_array(levels, "levels")
            except ValueError:
                raise TypeError("no") from None
            return np.asarray(levels, dtype=np.float64)
    """,
    "the_item_checked_is_the_item_read": """
        def f(levels):
            require_finite(levels[0], "levels")
            return np.float64(levels[0])
    """,
    "attribute_of_a_record": """
        def f(result):
            return np.asarray(getattr(result, "levels"), dtype=np.float64)
    """,
    "keyword_only_local_check": """
        def _read(*, levels):
            return real_array(levels, "levels")

        def f(levels):
            _read(levels=levels)
            return np.asarray(levels, dtype=np.float64)
    """,
    "to_complex_after_a_text_refusal": """
        def f(impedance):
            refuse_text(impedance, "no")
            return np.asarray(impedance, dtype=complex)
    """,
    "to_complex_read": """
        def f(impedance):
            z = complex_array(impedance, "impedance")
            return np.asarray(z, dtype=np.complex128)
    """,
    "real_read_then_complex": """
        def f(levels):
            levels = real_array(levels, "levels")
            return levels.astype(np.complex128)
    """,
}

_PLANTED_HEADER = """
import numpy as np

from phonometry._internal.validation import (
    complex_array,
    real_array,
    refuse_complex,
    refuse_text,
    require_finite,
    require_finite_array,
)
"""


def _planted(tmp_path: Path, body: str) -> set[str]:
    source = _PLANTED_HEADER + textwrap.dedent(body)
    return {
        verdict
        for function, verdict in _verdicts(tmp_path, source).items()
        if function == "f" or function.startswith("f.")
    }


@pytest.mark.parametrize("shape", sorted(_PLANTED_UNCHECKED))
def test_a_caller_s_value_no_check_reads_on_every_path_is_found(
    tmp_path: Path, shape: str
) -> None:
    assert "unchecked" in _planted(tmp_path, _PLANTED_UNCHECKED[shape])


@pytest.mark.parametrize("shape", sorted(_PLANTED_ANSWERED))
def test_a_check_on_every_path_answers_it(tmp_path: Path, shape: str) -> None:
    assert _planted(tmp_path, _PLANTED_ANSWERED[shape]) <= {
        "checked",
        "computed",
        "field",
    }


def test_another_copy_of_the_library_is_read_with_its_own_checks(
    tmp_path: Path,
) -> None:
    """A copy of the library elsewhere is read with the checks it defines,
    not with this tree's: a check only this tree has answers nothing there.
    """
    package = tmp_path / "src" / "phonometry"
    (package / "_internal").mkdir(parents=True)
    (package / "_internal" / "validation.py").write_text(
        "def real_array(x, name):\n    return x\n", encoding="utf-8"
    )
    (package / "reader.py").write_text(
        textwrap.dedent(
            """
            import numpy as np

            from .local import resolve

            def f(levels):
                resolve(levels)
                return np.asarray(levels, dtype=np.float64)
            """
        ),
        encoding="utf-8",
    )
    (package / "local.py").write_text(
        "def resolve(x):\n    return x\n", encoding="utf-8"
    )
    found = guard.census(sorted(package.rglob("*.py")), source=package)
    reader = [c for c in found if c.function == "f"]
    assert [(c.key, c.verdict) for c in reader] == [
        (("src/phonometry/reader.py", "f"), "unchecked")
    ]


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
