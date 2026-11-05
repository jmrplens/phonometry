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

def arithmetic(levels):
    return np.asarray(10.0 ** (levels / 10.0), dtype=np.float64)

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

def checked_arithmetic(levels):
    return np.asarray(real_array(levels, "levels") + 3.0, dtype=np.float64)

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
    dtype, through arithmetic, and a field in ``__post_init__``.
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
        "arithmetic": "unchecked",
        "Record.__post_init__": "unchecked",
    }


def test_each_shape_that_answers_it_passes(tmp_path: Path) -> None:
    """The shared reader, a check first, a name rebound to a check, a check of the
    module on any parameter, arithmetic on a checked value, a value the function
    computed, a field a method reads.
    """
    verdicts = _verdicts(tmp_path, _ANSWERED)
    assert verdicts == {
        "refused_first": "checked",
        "rebound": "checked",
        "through_a_local_check": "checked",
        "checked_arithmetic": "checked",
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
    "real_number": lambda v: validation.real_number(v, "x"),
    "complex_number": lambda v: validation.complex_number(v, "x"),
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
        "real_number",
        "complex_number",
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
    "python_s_float_of_a_parameter": """
        def f(value):
            return float(value)
    """,
    "python_s_complex_of_a_parameter": """
        def f(value):
            return complex(value)
    """,
    "an_item_replaced_after_its_check": """
        def f(levels, other):
            require_finite(levels[0], "levels")
            levels[0] = other
            return np.float64(levels[0])
    """,
    "an_item_replaced_after_the_whole_check": """
        def f(levels, other):
            levels = real_array(levels, "levels")
            levels[0] = other
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_check_that_hands_back_a_parameter_it_never_checked": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return levels

        def f(reference, levels):
            out = _helper(reference, levels)
            return np.asarray(out, dtype=np.float64)
    """,
    "a_check_that_hands_back_arithmetic_on_a_parameter_it_never_checked": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return levels * 2

        def f(reference, levels):
            out = _helper(reference, levels)
            return np.asarray(out, dtype=np.float64)
    """,
    "a_check_that_hands_back_a_negated_parameter_it_never_checked": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return -levels

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_a_transposed_parameter_it_never_checked": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return levels.T

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_call_in_a_comprehension_s_first_iterable_reaches_the_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x
                return [x]

            _ = [y for inner in inner(levels) for y in [inner]]
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_local_spelt_like_a_private_check_checks_nothing": """
        def _check(x):
            real_array(x, "x")

        def f(levels):
            _check = print
            _check(levels)
            return float(levels)
    """,
    "a_parameter_spelt_like_a_private_check_checks_nothing": """
        def _check(x):
            real_array(x, "x")

        def f(levels, _check):
            _check(levels)
            return float(levels)
    """,
    "a_nested_function_spelt_like_a_private_check_checks_nothing": """
        def _check(x):
            real_array(x, "x")

        def f(levels):
            def _check(x):
                return None

            _check(levels)
            return float(levels)
    """,
    "a_local_spelt_like_a_shared_check_checks_nothing": """
        def f(levels):
            real_array = print
            real_array(levels, "levels")
            return float(levels)
    """,
    "a_local_spelt_like_a_private_check_hands_on_no_check_to_its_caller": """
        def _check(x):
            real_array(x, "x")

        def _forward(values):
            _check = print
            _check(values)

        def f(levels):
            _forward(levels)
            return float(levels)
    """,
    "a_check_only_a_type_checker_imports_beside_the_function_that_runs": """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from phonometry._internal.validation import real_array as _check

        def _check(x, name):
            return x

        def f(levels):
            _check(levels, "levels")
            return float(levels)
    """,
    "a_check_that_hands_back_a_comprehension_of_a_parameter": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return [level * 2 for level in levels]

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_a_comprehension_naming_its_own_variable": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            return [out for out in levels]

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_a_nested_comprehension_of_a_parameter": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            return [[v for v in row] for row in levels]

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_what_a_walrus_bound": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            if (out := levels) is None:
                return 0.0
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_walrus_in_a_comprehension_bound": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            last = 0.0
            _ = [(last := level) for level in levels]
            return last

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_nested_function_rebinds_nonlocal": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner():
                nonlocal out
                out = levels

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_nested_function_adds_nonlocal": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 0.0

            def inner():
                nonlocal out
                for level in levels:
                    out += level

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_list_a_nested_function_fills": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = [0.0]

            def inner():
                out[0] = levels

            inner()
            return out[0]

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_nested_function_s_parameter_is_handed": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            inner(levels)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_nested_namesake_parameter_is_handed": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(levels):
                nonlocal out
                out = levels

            inner(levels)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_nested_function_s_keyword_is_handed": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = [0.0]

            def inner(scale, x=0.0):
                out[0] = x * scale

            inner(2.0, x=levels)
            return out[0]

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_starred_list_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            inner(*[levels])
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_starred_name_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(scale, x, *rest):
                nonlocal out
                out = rest[0] if rest else x

            arguments = (levels, levels)
            inner(2.0, *arguments)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_mapping_literal_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            inner(**{"x": levels})
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_mapping_name_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(scale=1.0, **options):
                nonlocal out
                out = options["x"]

            settings = {"x": levels}
            inner(**settings)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_nested_function_s_default": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x=levels):
                nonlocal out
                out = x

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_sibling_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            def outer_call():
                inner(levels)

            outer_call()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_comprehension_hands_a_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = [0.0]

            def inner(x):
                out[0] = x

            _ = [inner(level) for level in levels]
            return out[0]

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_module_name_a_nested_function_binds": """
        def _helper(reference, levels):
            real_array(reference, "reference")

            def inner():
                global out
                out = levels

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_module_name_both_functions_declare_global": """
        def _helper(reference, levels):
            global out
            real_array(reference, "reference")
            out = 1.0

            def inner():
                global out
                out = levels

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_an_item_of_a_module_list_a_nested_function_fills": """
        def _helper(reference, levels):
            real_array(reference, "reference")

            def inner():
                OUT[0] = levels

            inner()
            return OUT[0]

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_what_a_match_captured": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            match levels:
                case [first, *_]:
                    return first
            return 0.0

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_loop_s_item_of_a_parameter": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            for level in levels:
                return level
            return 0.0

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_a_sum_it_added_a_parameter_to": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            total = 0.0
            for level in levels:
                total += level
            return total

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_check_that_hands_back_an_array_it_added_a_parameter_to": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = np.zeros(3)
            out += levels
            return out

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_an_array_it_set_a_parameter_in": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = np.zeros(3)
            out[0] = levels
            return out

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "a_check_that_hands_back_an_array_it_added_a_parameter_to_an_item_of": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = np.zeros((2, 3))
            out[0][1] += levels
            return out

        def f(reference, levels):
            return np.asarray(_helper(reference, levels), dtype=np.float64)
    """,
    "numpy_s_reading_captured_by_a_match": """
        def f(levels):
            match np.asarray(levels):
                case captured:
                    return refuse_text(captured, "no")
    """,
    "numpy_s_reading_bound_by_a_with": """
        def f(levels):
            with np.asarray(levels) as held:
                return refuse_text(held, "no")
    """,
    "a_closure_handed_out_before_its_function_rebinds_what_it_reads": """
        def f(levels, other, sink):
            levels = real_array(levels, "levels")

            def read():
                return np.asarray(levels, dtype=np.float64)

            sink.append(read)
            levels = other
    """,
    "a_method_of_a_class_written_in_the_function": """
        def f(levels):
            class Reader:
                def read(self):
                    return np.asarray(levels, dtype=np.float64)

            return Reader()
    """,
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
    "checked_in_a_later_link_of_a_comparison": """
        def f(levels, flag):
            ok = 0 < flag < require_finite_array(levels, "levels")
            return ok, np.asarray(levels, dtype=np.float64)
    """,
    "checked_in_an_assert": """
        def f(levels):
            assert require_finite_array(levels, "levels") is None
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_in_a_later_link_of_a_comparison": """
        def _read(levels, flag):
            return 0 < flag < real_array(levels, "levels")

        def f(levels, flag):
            _read(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_in_an_assert": """
        def _read(levels):
            assert real_array(levels, "levels") is not None

        def f(levels):
            _read(levels)
            return np.asarray(levels, dtype=np.float64)
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
    "a_helper_that_returns_before_its_check": """
        def _maybe(levels, flag):
            if flag:
                return levels
            real_array(levels, "levels")
            return levels

        def f(levels, flag):
            _maybe(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_returns_from_a_loop_before_its_check": """
        def _first(levels, rows):
            for row in rows:
                if row:
                    return row
            real_array(levels, "levels")
            return None

        def f(levels, rows):
            _first(levels, rows)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_whose_handler_swallows_its_check": """
        def _quiet(levels):
            try:
                real_array(levels, "levels")
            except TypeError:
                pass

        def f(levels):
            _quiet(levels)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_a_rebound_parameter": """
        def _other(levels, default):
            levels = default
            real_array(levels, "levels")

        def f(levels, default):
            _other(levels, default)
            return np.asarray(levels, dtype=np.float64)
    """,
    "captured_by_a_nested_function": """
        def f(levels):
            def g():
                return np.asarray(levels, dtype=np.float64)

            return g()
    """,
    "captured_by_a_lambda": """
        def f(levels, apply):
            return apply(lambda: np.asarray(levels, dtype=np.float64))
    """,
    "a_check_handed_numpy_s_reading": """
        def f(levels):
            return real_array(np.asarray(levels), "levels")
    """,
    "a_check_handed_a_name_bound_to_numpy_s_reading": """
        def f(levels):
            arr = np.atleast_1d(levels)
            return real_array(arr, "levels")
    """,
    "a_helper_handed_numpy_s_reading": """
        def _read(name, arr):
            return real_array(arr, name)

        def f(levels):
            return _read("levels", np.asarray(levels))
    """,
    "captured_and_used_before_the_check": """
        def f(levels):
            def g():
                return np.asarray(levels, dtype=np.float64)

            first = g()
            levels = real_array(levels, "levels")
            return first, g()
    """,
    "checked_through_one_branch_of_a_conditional": """
        def f(levels, flag):
            real_array(levels if flag else [1.0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_through_a_conditional_in_a_list": """
        def f(levels, flag):
            real_array([levels if flag else 1.0, 2.0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_through_the_default_of_getattr": """
        def f(levels, record):
            real_array(getattr(record, "levels", levels), "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_one_branch_of_a_conditional": """
        def _read(levels, flag):
            real_array(levels if flag else [1.0], "levels")

        def f(levels, flag):
            _read(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_rebinds_to_one_branch_of_a_conditional": """
        def _read(levels, flag):
            levels = levels if flag else [1.0]
            real_array(levels, "levels")

        def f(levels, flag):
            _read(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_unless_another_name_is_none": """
        def f(levels, other):
            real_array([1.0] if other is None else levels, "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_unless_it_is_none_the_other_way_round": """
        def f(levels=None):
            real_array(levels if levels is None else [1.0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "numpy_s_reading_bound_in_one_branch": """
        def f(levels, flag):
            if flag:
                arr = np.atleast_1d(levels)
            else:
                arr = 0.0
            return real_array(arr, "levels")
    """,
    "numpy_s_reading_bound_in_a_try_a_handler_rebinds": """
        def f(levels):
            try:
                arr = np.asarray(levels)
            except ValueError:
                arr = 0.0
            return real_array(arr, "levels")
    """,
    "numpy_s_reading_kept_when_a_loop_does_not_run": """
        def f(levels, rows):
            arr = np.asarray(levels)
            for row in rows:
                arr = row
            return real_array(arr, "levels")
    """,
    "numpy_s_reading_bound_in_a_tuple": """
        def f(levels):
            arr, count = np.asarray(levels), 0
            return real_array(arr, "levels"), count
    """,
    "an_item_a_loop_takes_from_numpy_s_reading": """
        def f(levels):
            for row in np.atleast_2d(levels):
                real_array(row, "levels")
    """,
    "an_item_a_comprehension_takes_from_numpy_s_reading": """
        def f(levels):
            return [real_array(row, "levels") for row in np.asarray(levels)]
    """,
    "numpy_s_reading_in_one_branch_of_a_conditional": """
        def f(levels, flag):
            arr = np.asarray(levels) if flag else 0.0
            return real_array(arr, "levels")
    """,
    "numpy_s_reading_bound_by_a_walrus": """
        def f(levels):
            if (arr := np.asarray(levels)).size:
                return real_array(arr, "levels")
            return None
    """,
    "arithmetic_on_the_value": """
        def f(levels):
            return np.asarray(levels * 2, dtype=np.float64)
    """,
    "a_sign_on_the_value": """
        def f(levels):
            return np.asarray(-levels, dtype=np.float64)
    """,
    "arithmetic_of_a_checked_value_with_one_no_check_read": """
        def f(levels, gain):
            return np.asarray(real_array(levels, "levels") * gain, dtype=np.float64)
    """,
    "an_augmented_assignment_of_the_value": """
        def f(levels, gain):
            scaled = real_array(levels, "levels")
            scaled *= gain
            return np.asarray(scaled, dtype=np.float64)
    """,
    "one_number_of_arithmetic_on_the_value": """
        def f(level):
            return float(level / 2.0)
    """,
    "a_check_handed_arithmetic_on_numpy_s_reading": """
        def f(levels):
            return real_array(np.asarray(levels) * 2, "levels")
    """,
}

#: The shapes that answer one: a check on every path, or no caller's value.
_PLANTED_ANSWERED = {
    "a_mapping_reaches_no_place_a_keyword_fills_in_a_nested_function": """
        def _helper(reference, levels):
            out = 1.0

            def inner(x, y=None):
                nonlocal out
                out = x

            inner(x=real_array(reference, "reference"), **{"y": levels})
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_mapping_reaches_no_place_an_argument_fills_in_a_nested_function": """
        def _helper(reference, levels):
            out = 1.0

            def inner(x, y=None):
                nonlocal out
                out = x

            inner(real_array(reference, "reference"), **{"y": levels})
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_starred_argument_reaches_no_place_a_keyword_fills_in_a_nested_function": """
        def _helper(reference, levels):
            out = 1.0

            def inner(x, y=None):
                nonlocal out
                out = x

            extra = [levels] if reference is None else []
            inner(*extra, x=real_array(reference, "reference"))
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_call_of_a_name_a_comprehension_binds_reaches_no_nested_function": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            _ = [inner(levels) for inner in [lambda x: None]]
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_call_of_a_name_a_later_loop_of_a_comprehension_binds": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            _ = [y for inner in [lambda x: [x]] for y in inner(levels)]
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_call_of_a_name_a_comprehension_binds_reaches_no_module_function": """
        def _keep(x):
            return x

        def _helper(reference, levels):
            real_array(reference, "reference")
            return [_keep(levels) for _keep in [lambda x: 1.0]]

        def f(reference, levels):
            return float(_helper(reference, levels)[0])
    """,
    "a_call_of_a_nested_function_spelt_like_a_module_function": """
        def _keep(x):
            return x

        def _helper(reference, levels):
            real_array(reference, "reference")

            def _keep(x):
                return 1.0

            return _keep(levels)

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_call_of_a_name_a_comprehension_binds_spelt_like_float": """
        def f(levels):
            return [float(levels) for float in [lambda x: 1.0]]
    """,
    "a_call_of_a_parameter_spelt_like_float": """
        def f(levels, float):
            return float(levels)
    """,
    "a_value_only_a_type_checker_block_hands_back": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            if TYPE_CHECKING:
                out = levels
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_value_a_nested_function_writes_under_global_only_for_the_type_checker": """
        def _helper(reference, levels):
            real_array(reference, "reference")

            def inner():
                global out
                if TYPE_CHECKING:
                    out = levels

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_name_only_the_else_of_a_type_checker_block_binds": """
        def f(levels):
            if TYPE_CHECKING:
                x = levels
            else:
                x = 1.0
            return float(x)
    """,
    "a_check_in_the_else_of_a_type_checker_block": """
        def f(levels):
            if TYPE_CHECKING:
                pass
            else:
                real_array(levels, "levels")
            return float(levels)
    """,
    "a_private_check_whose_check_sits_in_the_else_of_a_type_checker_block": """
        def _check(values):
            if TYPE_CHECKING:
                pass
            else:
                real_array(values, "values")

        def f(levels):
            _check(levels)
            return float(levels)
    """,
    "a_check_handed_the_value_or_a_number": """
        def f(value):
            require_finite(value or 0.0, "value")
            return np.float64(value)
    """,
    "an_isinstance_test_of_real_numbers": """
        def f(value):
            if isinstance(value, float | int):
                return np.float64(value)
            if not isinstance(value, numbers.Real):
                raise TypeError("value")
            return np.float64(value)
    """,
    "a_check_that_hands_back_what_it_checked": """
        def _helper(levels):
            return real_array(levels, "levels")

        def f(levels):
            out = _helper(levels)
            return np.asarray(out, dtype=np.float64)
    """,
    "a_check_that_hands_back_arithmetic_on_what_it_checked": """
        def _helper(levels):
            return -real_array(levels, "levels") * 2

        def f(levels):
            return np.asarray(_helper(levels), dtype=np.float64)
    """,
    "a_comprehension_s_variable_is_its_own": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            _ = [out for out in levels]
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_generator_s_variable_is_its_own": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            _ = any(out for out in levels)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_dict_comprehension_s_variable_is_its_own": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            _ = {out: 0 for out in levels}
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_nested_function_s_variables_are_its_own": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner():
                out = levels
                return [out for out in levels]

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_lambda_s_comprehension_is_its_own": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            _ = lambda: [out for out in levels]
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_nested_function_s_parameter_handed_a_computed_value": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(x):
                nonlocal out
                out = x

            inner(2.0)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_nested_function_s_own_parameter_named_like_the_helper_s": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner(levels):
                nonlocal out
                out = levels

            inner(3.0)
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_nested_function_s_type_parameter_is_its_own": """
        def f(T):
            def g[T]():
                return np.asarray(T, dtype=np.float64)

            return g(), real_array(T, "T")
    """,
    "a_generic_class_s_type_parameter_is_its_methods_own": """
        def f(T):
            class Box[T]:
                def get(self):
                    return np.asarray(T, dtype=np.float64)

            return Box().get(), real_array(T, "T")
    """,
    "a_generic_class_s_type_parameter_reaches_a_class_inside_it": """
        def f(T):
            class Box[T]:
                class Inner:
                    def get(self):
                        return np.asarray(T, dtype=np.float64)

            return Box.Inner().get(), real_array(T, "T")
    """,
    "a_generic_class_s_type_parameter_is_not_what_its_method_writes": """
        def _helper(reference, T):
            real_array(reference, "reference")
            out = [0.0]

            class Box[T]:
                def fill(self):
                    out[0] = T

            Box().fill()
            return out[0]

        def f(reference, T):
            return float(_helper(reference, T))
    """,
    "a_name_a_nested_function_declares_global_is_the_module_s": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner():
                global out
                out = levels

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_name_a_function_two_levels_down_declares_global_is_the_module_s": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            def inner():
                def deeper():
                    global out
                    out = levels

                deeper()

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_method_s_global_name_is_the_module_s": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0

            class Writer:
                def write(self):
                    global out
                    out = levels

            Writer().write()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_global_name_a_nested_function_reads_is_the_module_s": """
        def _helper(reference, levels):
            real_array(reference, "reference")
            out = 1.0
            scale = levels

            def inner():
                nonlocal out
                global scale
                out = scale

            inner()
            return out

        def f(reference, levels):
            return float(_helper(reference, levels))
    """,
    "a_global_name_a_nested_function_converts_is_the_module_s": """
        def f(levels):
            def g():
                global levels
                return np.asarray(levels, dtype=np.float64)

            return g(), real_array(levels, "levels")
    """,
    "python_s_float_after_the_shared_reader": """
        def f(value):
            value = real_number(value, "value")
            return float(value)
    """,
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
    "checked_in_the_first_link_of_a_comparison": """
        def f(levels, flag):
            ok = require_finite_array(levels, "levels") is None is not flag
            return ok, np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_in_the_first_link_of_a_comparison": """
        def _read(levels, flag):
            return real_array(levels, "levels") is not None is not flag

        def f(levels, flag):
            _read(levels, flag)
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
    "a_helper_that_rebinds_to_what_keeps_the_value": """
        def _read(levels):
            levels = np.atleast_1d(levels)
            real_array(levels, "levels")

        def f(levels):
            _read(levels)
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_whose_handler_raises": """
        def _read(levels):
            try:
                real_array(levels, "levels")
            except ValueError:
                raise TypeError("no") from None

        def f(levels):
            _read(levels)
            return np.asarray(levels, dtype=np.float64)
    """,
    "numpy_s_reading_after_a_text_refusal": """
        def f(levels):
            refuse_text(levels, "no")
            return real_array(np.asarray(levels), "levels")
    """,
    "numpy_s_reading_rebound_to_a_reading": """
        def f(levels):
            arr = np.asarray(levels)
            arr = real_array(levels, "levels")
            return refuse_text(arr, "no")
    """,
    "captured_after_the_check": """
        def f(levels):
            levels = real_array(levels, "levels")

            def g():
                return np.asarray(levels, dtype=np.float64)

            return g()
    """,
    "captured_and_checked_before_the_use": """
        def f(levels):
            def g():
                return np.asarray(levels, dtype=np.float64)

            levels = real_array(levels, "levels")
            return g()
    """,
    "a_nested_function_s_own_binding": """
        def f(levels):
            def g():
                levels = [1.0, 2.0]
                return np.asarray(levels, dtype=np.float64)

            return g(), real_array(levels, "levels")
    """,
    "the_same_value_in_both_branches_of_a_conditional": """
        def f(levels, flag):
            real_array(levels.T if flag else levels, "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_checks_both_branches_of_a_conditional": """
        def _read(levels, flag):
            real_array(levels.T if flag else levels, "levels")

        def f(levels, flag):
            _read(levels, flag)
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_unless_it_is_none": """
        def f(levels=None):
            real_array([1.0] if levels is None else levels, "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "checked_while_it_is_not_none": """
        def f(levels=None):
            real_array(levels if levels is not None else [1.0], "levels")
            return np.asarray(levels, dtype=np.float64)
    """,
    "a_helper_that_rebinds_a_missing_value_to_its_default": """
        def _read(levels=None):
            levels = [1.0] if levels is None else levels
            real_array(levels, "levels")

        def f(levels=None):
            _read(levels)
            return np.asarray(levels, dtype=np.float64)
    """,
    "numpy_s_reading_rebound_in_every_branch": """
        def f(levels, flag):
            arr = np.asarray(levels)
            if flag:
                arr = real_array(levels, "levels")
            else:
                arr = real_array(levels.T, "levels")
            return refuse_text(arr, "no")
    """,
    "numpy_s_reading_in_a_branch_that_returns": """
        def f(levels, other, flag):
            arr = real_array(levels, "levels")
            if flag:
                arr = np.asarray(other)
                return arr.size
            return refuse_text(arr, "no")
    """,
}

#: A private helper of the package, read through its calls: each caller
#: hands it something, and the helper's conversion reads what it is handed.
_HELPER = """
def _convert(values):
    return np.asarray(values, dtype=np.float64)
"""

#: What a public function hands the helper, and what the helper's conversion
#: then reads: a parameter of a private function is no caller's value of its
#: own, but what its calls hand it, joined over all of them.
_HANDED = {
    "the_caller_s_value": (
        "def f(levels):\n    return _convert(levels)\n",
        "unchecked",
    ),
    "arithmetic_on_the_caller_s_value": (
        "def f(levels):\n    return _convert(levels * 2)\n",
        "unchecked",
    ),
    "the_value_a_check_read": (
        "def f(levels):\n    return _convert(real_array(levels, 'levels'))\n",
        "checked",
    ),
    "a_value_the_library_computed": (
        "def f(levels):\n    return _convert(np.zeros(3))\n",
        "computed",
    ),
    "a_value_by_keyword": (
        "def f(levels):\n    return _convert(values=np.zeros(3))\n",
        "computed",
    ),
    "the_caller_s_value_through_another_helper": (
        "def _relay(values):\n    return _convert(values)\n\n"
        "def f(levels):\n    return _relay(levels)\n",
        "unchecked",
    ),
    "a_computed_value_through_another_helper": (
        "def _relay(values):\n    return _convert(values)\n\n"
        "def f(levels):\n    return _relay(np.zeros(3))\n",
        "computed",
    ),
    "a_computed_value_and_elsewhere_the_caller_s": (
        "def f(levels):\n    return _convert(np.zeros(3))\n\n"
        "def g(levels):\n    return _convert(levels)\n",
        "unchecked",
    ),
    "the_helper_handed_on_rather_than_called": (
        "def f(levels):\n    return list(map(_convert, [np.zeros(3)]))\n",
        "unchecked",
    ),
    "an_unpacked_argument": (
        "def f(levels):\n    return _convert(*levels)\n",
        "unchecked",
    ),
    "a_mapping": (
        "def f(options):\n    return _convert(**options)\n",
        "unchecked",
    ),
    # A place an argument of the call fills is that argument's alone: a
    # ``*`` argument or a ``**`` mapping that filled it too would raise.
    "a_keyword_beside_an_unpacked_argument": (
        "def f(rest):\n    return _convert(*rest, values=np.zeros(3))\n",
        "computed",
    ),
    "a_keyword_beside_a_mapping": (
        "def f(options):\n    return _convert(values=np.zeros(3), **options)\n",
        "computed",
    ),
    "an_argument_in_its_place_beside_a_mapping": (
        "def f(options):\n    return _convert(np.zeros(3), **options)\n",
        "computed",
    ),
}


@pytest.mark.parametrize("shape", sorted(_HANDED))
def test_a_private_helper_reads_what_its_calls_hand_it(
    tmp_path: Path, shape: str
) -> None:
    caller, verdict = _HANDED[shape]
    source = _PLANTED_HEADER + _HELPER + "\n" + caller
    assert _verdicts(tmp_path, source)["_convert"] == verdict


def _read_apart(tmp_path: Path, published: str) -> str:
    """The verdict on a conversion in a private module that a public one calls."""
    package = tmp_path / "phonometry"
    package.mkdir()
    inner = package / "_inner.py"
    inner.write_text(
        _PLANTED_HEADER + "\ndef convert(values):\n"
        "    return np.asarray(values, dtype=np.float64)\n",
        encoding="utf-8",
    )
    outer = package / "outer.py"
    outer.write_text(
        "import numpy as np\n\nfrom ._inner import convert\n\n"
        f"{published}\n\ndef f(levels):\n    return convert(np.zeros(3))\n",
        encoding="utf-8",
    )
    found = guard.census([inner, outer], source=None)
    return next(c.verdict for c in found if c.function == "convert")


def test_a_function_of_a_private_module_is_read_through_its_calls(
    tmp_path: Path,
) -> None:
    assert _read_apart(tmp_path, "") == "computed"


def test_a_function_a_public_module_publishes_reads_a_caller_s_value(
    tmp_path: Path,
) -> None:
    assert _read_apart(tmp_path, '__all__ = ["convert"]') == "unchecked"


_PLANTED_HEADER = """
import numbers

import numpy as np

from phonometry._internal.validation import (
    complex_array,
    real_array,
    real_number,
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


@pytest.mark.parametrize(
    "body",
    [
        """
        def f(levels):
            return [float(real_array(levels, "levels")) for real_array in [print]]
        """,
        """
        def _check(x):
            real_array(x, "x")
            return x

        def f(levels):
            return [float(_check(levels)) for _check in [print]]
        """,
    ],
)
def test_a_check_a_comprehension_binds_answers_for_nothing(
    tmp_path: Path, body: str
) -> None:
    """A comprehension's variable spelt like a check is another name: what it
    calls hands back something the guard does not follow, no refusal of a check.
    """
    assert _planted(tmp_path, body) == {"computed"}


#: A nearer name that holds the very function its spelling names, written whole
#: with its own imports, since the header imports NumPy under its usual name.
_NEARER_HOLDS_THE_SAME = {
    "a_parameter_defaulting_to_the_builtin": """
        def f(levels, float=float):
            return float(levels)
    """,
    "a_keyword_only_parameter_defaulting_to_the_builtin": """
        def f(levels, *, complex=complex):
            return complex(levels)
    """,
    "a_parameter_defaulting_to_builtins_float": """
        import builtins

        def f(levels, float=builtins.float):
            return float(levels)
    """,
    "a_local_assigned_from_builtins_float": """
        import builtins

        def f(levels):
            float = builtins.float
            return float(levels)
    """,
    "a_parameter_defaulting_to_the_numpy_function": """
        from numpy import asarray

        def f(levels, asarray=asarray):
            return asarray(levels, dtype=float)
    """,
    "a_parameter_defaulting_to_np_asarray": """
        import numpy as np
        from numpy import asarray

        def f(levels, asarray=np.asarray):
            return asarray(levels, dtype=float)
    """,
    "a_local_assigned_from_np_asarray": """
        import numpy as np
        from numpy import asarray

        def f(levels):
            asarray = np.asarray
            return asarray(levels, dtype=float)
    """,
    "a_lambda_parameter_defaulting_to_the_builtin": """
        def f(levels):
            return (lambda float=float: float(levels))()
    """,
    "a_nested_function_reads_the_parameter_around_it": """
        def f(levels, float=float):
            def g(x):
                return float(x)
            return g(levels)
    """,
}


@pytest.mark.parametrize("shape", sorted(_NEARER_HOLDS_THE_SAME))
def test_a_nearer_name_that_holds_the_same_function_still_converts(
    tmp_path: Path, shape: str
) -> None:
    """A parameter defaulting to the builtin or the NumPy function it is spelt
    as, or a local assigned from it, holds that very function, so the call is
    the conversion it reads as. The binder's kind alone hid it, and the
    conversion vanished from the census.
    """
    found = _verdicts(tmp_path, _NEARER_HOLDS_THE_SAME[shape])
    assert found
    assert set(found.values()) == {"unchecked"}


@pytest.mark.parametrize(
    "body",
    [
        """
        def f(levels, float):
            return float(levels)
        """,
        """
        def f(levels, float=print):
            return float(levels)
        """,
        """
        def f(levels, float=None):
            return float(levels)
        """,
        """
        def f(levels):
            float = print
            return float(levels)
        """,
        """
        import builtins

        def f(levels, other):
            float = builtins.float
            float = other
            return float(levels)
        """,
    ],
)
def test_a_nearer_name_that_holds_anything_else_is_no_conversion(
    tmp_path: Path, body: str
) -> None:
    """A parameter with no default or another one, and a local that holds or may
    hold anything else, are other names: what they call is no conversion.
    """
    assert _verdicts(tmp_path, body) == {}


def test_a_check_a_nearer_name_holds_still_answers_for_the_conversion(
    tmp_path: Path,
) -> None:
    """A parameter defaulting to the check it is spelt as is that check: it read
    as no check, so a checked value read as unchecked.
    """
    assert _planted(
        tmp_path,
        """
        def f(levels, real_array=real_array):
            real_array(levels, "levels")
            return float(levels)
        """,
    ) == {"checked"}


#: A name the module imports and its own binding replaces, written whole, since
#: the header imports the checks. Each stands for the later binding.
_REPLACED_AT_THE_TOP = {
    "a_def_after_the_import_of_a_check": """
        from phonometry._internal.validation import real_array as _check

        def _check(x, name):
            return x

        def f(levels):
            _check(levels, "levels")
            return float(levels)
    """,
    "an_assignment_after_the_import_of_a_check": """
        from phonometry._internal.validation import real_array

        real_array = print

        def f(levels):
            real_array(levels, "levels")
            return float(levels)
    """,
    "a_check_of_its_own_spelling_defined_by_the_module": """
        def real_array(x, name):
            return x

        def f(levels):
            real_array(levels, "levels")
            return float(levels)
    """,
    "a_check_a_function_replaces_under_global": """
        from phonometry._internal.validation import real_array

        def _swap():
            global real_array
            real_array = print

        def f(levels):
            real_array(levels, "levels")
            return float(levels)
    """,
    "a_check_in_one_branch_of_a_try_and_none_in_the_other": """
        try:
            from phonometry._internal.validation import real_array
        except ImportError:
            real_array = print

        def f(levels):
            real_array(levels, "levels")
            return float(levels)
    """,
}


@pytest.mark.parametrize("shape", sorted(_REPLACED_AT_THE_TOP))
def test_a_binding_of_the_module_replaces_the_check_it_imported(
    tmp_path: Path, shape: str
) -> None:
    """An import is a check only while it stands: a later ``def`` or assignment
    takes the name from it, in the module or from a function under ``global``, and
    a branch that binds anything else may leave no check. Each read as checked.
    """
    assert _verdicts(tmp_path, _REPLACED_AT_THE_TOP[shape]) == {"f": "unchecked"}


def test_a_function_s_own_import_stands_past_the_module_s_binding(
    tmp_path: Path,
) -> None:
    """A function that imports the name holds the import, whatever the module
    binds of that spelling, and every other function holds the module's binding.
    The module's binding took the name from the whole module, so the conversion
    left the census and the check answered for nothing.
    """
    assert _verdicts(
        tmp_path,
        """
        def asarray(x, dtype=None):
            return x

        def imports_it(levels):
            from numpy import asarray
            return asarray(levels, dtype=float)

        def reads_the_module_s(levels):
            return asarray(levels, dtype=float)
        """,
    ) == {"imports_it": "unchecked"}
    assert _verdicts(
        tmp_path,
        """
        def real_array(x, name):
            return x

        def imports_it(levels):
            from phonometry._internal.validation import real_array
            real_array(levels, "levels")
            return float(levels)

        def reads_the_module_s(levels):
            real_array(levels, "levels")
            return float(levels)
        """,
    ) == {"imports_it": "checked", "reads_the_module_s": "unchecked"}


def test_a_function_of_a_check_s_spelling_hands_back_no_refusal(tmp_path: Path) -> None:
    """What the module's own ``real_array`` hands back is a value it computed, as
    of any function that is no check; it read as the shared check's refusal.
    """
    assert _verdicts(
        tmp_path,
        """
        def real_array(x, name):
            return x

        def f(levels):
            return float(real_array(levels, "levels"))
        """,
    ) == {"f": "computed"}


def test_a_check_for_the_type_checker_replaces_nothing_that_runs(
    tmp_path: Path,
) -> None:
    """An ``if TYPE_CHECKING:`` block's binding never runs: it takes the check
    from no import beside it, and it answers for nothing on its own.
    """
    assert _verdicts(
        tmp_path,
        """
        from typing import TYPE_CHECKING

        from phonometry._internal.validation import real_array

        if TYPE_CHECKING:
            real_array = print

        def f(levels):
            real_array(levels, "levels")
            return float(levels)
        """,
    ) == {"f": "checked"}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            def float(x):
                return 1.0

            def f(levels):
                return float(levels)
            """,
            id="a-def-of-float",
        ),
        pytest.param(
            """
            float = print

            def f(levels):
                return float(levels)
            """,
            id="an-assignment-to-float",
        ),
        pytest.param(
            """
            def _swap():
                global float
                float = print

            def f(levels):
                return float(levels)
            """,
            id="float-a-function-replaces-under-global",
        ),
        pytest.param(
            """
            def float(x):
                return 1.0

            def f(levels, float=float):
                return float(levels)
            """,
            id="a-default-of-the-module-s-float",
        ),
        pytest.param(
            """
            from decimal import Decimal as float

            def f(levels):
                return float(levels)
            """,
            id="an-import-of-float-from-elsewhere",
        ),
        pytest.param(
            """
            from numpy import asarray

            def asarray(x, dtype=None):
                return x

            def f(levels):
                return asarray(levels, dtype=float)
            """,
            id="a-def-after-the-import-from-numpy",
        ),
        pytest.param(
            """
            import numpy as np

            def f(levels):
                return [np.asarray(levels, dtype=np.float64) for np in [print]]
            """,
            id="a-comprehension-binds-a-plain-import",
        ),
        pytest.param(
            """
            import math

            def f(levels):
                return (lambda math: math.float64(levels))(print)
            """,
            id="a-lambda-binds-a-plain-import",
        ),
    ],
)
def test_a_binding_of_the_module_is_no_conversion_of_that_spelling(
    tmp_path: Path, source: str
) -> None:
    """The module's own ``float`` is no builtin, and a comprehension's or a
    lambda's variable hides a plain import as it hides a ``from`` import. Each
    read as a conversion of the caller's value.
    """
    assert _verdicts(tmp_path, source) == {}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            import builtins

            float = builtins.float

            def f(levels):
                return float(levels)
            """,
            id="an-assignment-from-builtins",
        ),
        pytest.param(
            """
            from builtins import float

            def f(levels):
                return float(levels)
            """,
            id="an-import-from-builtins",
        ),
        pytest.param(
            """
            from numpy import float64 as float

            def f(levels):
                return float(levels)
            """,
            id="an-import-from-numpy",
        ),
        pytest.param(
            """
            import numpy as np

            def f(levels, np):
                return np.asarray(levels, dtype=float)
            """,
            id="a-parameter-spelt-as-the-module",
        ),
        pytest.param(
            """
            import numpy as np

            def f(levels):
                return (lambda np: np.asarray(levels, dtype=float))(np)
            """,
            id="a-lambda-parameter-spelt-as-the-module",
        ),
        pytest.param(
            """
            import numpy as np

            def f(levels):
                return [np.asarray(row, dtype=float) for row in levels]
            """,
            id="a-comprehension-beside-the-module",
        ),
        pytest.param(
            """
            if not_defined_here:
                float = print

            import builtins
            float = builtins.float

            def f(levels):
                return float(levels)
            """,
            id="a-later-binding-that-holds-the-builtin",
        ),
    ],
)
def test_a_binding_that_keeps_the_function_of_its_spelling_still_converts(
    tmp_path: Path, source: str
) -> None:
    """What holds the builtin or NumPy's function stays a conversion, and a
    parameter spelt ``np``, a lambda's as a function's, is the module handed in.
    """
    assert set(_verdicts(tmp_path, source).values()) == {"unchecked"}


def test_a_function_of_the_module_read_for_float_is_still_followed(
    tmp_path: Path,
) -> None:
    """The module's ``float`` that checks its parameter answers for a conversion
    as any function of the module does: it was read as a conversion itself, and
    as nothing, since the read stopped at the builtin of that spelling.
    """
    assert _verdicts(
        tmp_path,
        """
        import numpy as np

        from phonometry._internal.validation import real_array

        def float(x):
            real_array(x, "x")

        def f(levels):
            float(levels)
            return np.asarray(levels, dtype=np.float64)
        """,
    ) == {"f": "checked"}


def test_a_keeping_call_the_module_replaces_keeps_nothing(tmp_path: Path) -> None:
    """A ``def list`` of the module hands back what it computes, not the caller's
    value, as a nested function of that spelling does.
    """
    assert _verdicts(
        tmp_path,
        """
        def list(values):
            return [1.0]

        def f(levels):
            return float(list(levels))
        """,
    ) == {"f": "computed"}


#: What a test on ``TYPE_CHECKING`` keeps from running, each holding a conversion
#: a caller's value would reach if it ran.
_NEVER_RUNS = {
    "a_nested_function_in_the_block": """
        def f(levels):
            if TYPE_CHECKING:
                def g(x):
                    return float(x)
            return 1.0
    """,
    "the_else_of_a_negated_test": """
        def f(levels):
            if not TYPE_CHECKING:
                return 1.0
            else:
                return float(levels)
    """,
    "a_function_at_the_top_in_the_block": """
        if TYPE_CHECKING:
            def g(x):
                return float(x)
    """,
    "a_function_at_the_top_in_the_else_of_a_negated_test": """
        if not TYPE_CHECKING:
            pass
        else:
            def g(x):
                return float(x)
    """,
    "a_method_in_the_block": """
        class Record:
            if TYPE_CHECKING:
                def method(self, x):
                    return float(x)
    """,
    "a_conversion_in_a_branch_of_an_expression": """
        def f(levels):
            return float(levels) if TYPE_CHECKING else 1.0
    """,
    "the_same_in_a_lambda": """
        def f(levels):
            return (lambda: float(levels) if TYPE_CHECKING else 1.0)()
    """,
}


@pytest.mark.parametrize("shape", sorted(_NEVER_RUNS))
def test_what_a_test_on_type_checking_keeps_from_running_converts_nothing(
    tmp_path: Path, shape: str
) -> None:
    """A conversion no run reaches reads nothing of a caller's. Each was reported."""
    source = "from typing import TYPE_CHECKING\n" + textwrap.dedent(_NEVER_RUNS[shape])
    assert _verdicts(tmp_path, source) == {}


@pytest.mark.parametrize(
    ("source", "verdict"),
    [
        pytest.param(
            """
            def f(levels):
                out = 1.0
                if not TYPE_CHECKING:
                    pass
                else:
                    out = levels
                return float(out)
            """,
            "computed",
            id="a-binding-in-the-else-of-a-negated-test",
        ),
        pytest.param(
            """
            def f(levels):
                return float(levels if TYPE_CHECKING else 1.0)
            """,
            "computed",
            id="a-value-in-the-branch-of-an-expression",
        ),
        pytest.param(
            """
            def f(levels):
                return float(1.0 if not TYPE_CHECKING else levels)
            """,
            "computed",
            id="a-value-in-the-else-of-a-negated-expression",
        ),
        pytest.param(
            """
            def f(levels):
                if not TYPE_CHECKING:
                    return float(levels)
                return 1.0
            """,
            "unchecked",
            id="the-body-of-a-negated-test-runs",
        ),
        pytest.param(
            """
            def f(levels):
                if not TYPE_CHECKING:
                    levels = 1.0
                return float(levels)
            """,
            "computed",
            id="a-binding-in-the-body-of-a-negated-test-always-runs",
        ),
        pytest.param(
            """
            def f(levels):
                return float(1.0 if TYPE_CHECKING else levels)
            """,
            "unchecked",
            id="the-else-of-an-expression-runs",
        ),
        pytest.param(
            """
            def f(levels):
                return float(levels if not TYPE_CHECKING else 1.0)
            """,
            "unchecked",
            id="the-body-of-a-negated-expression-runs",
        ),
    ],
)
def test_the_flow_reads_the_branch_of_a_test_on_type_checking_that_runs(
    tmp_path: Path, source: str, verdict: str
) -> None:
    """The branch that runs always runs and the other never does, in a statement
    and in a conditional expression, whichever way the test is spelt.
    """
    planted = "from typing import TYPE_CHECKING\n" + textwrap.dedent(source)
    assert _verdicts(tmp_path, planted) == {"f": verdict}


def test_a_function_in_the_body_of_a_negated_test_is_read(tmp_path: Path) -> None:
    """``if not TYPE_CHECKING:`` is what the program runs, the module's
    ``__getattr__`` at the top of the package among such functions.
    """
    source = """
        from typing import TYPE_CHECKING

        if not TYPE_CHECKING:
            def g(x):
                return float(x)
        """
    assert _verdicts(tmp_path, source) == {"g": "unchecked"}


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
