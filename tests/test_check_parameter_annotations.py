#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on public parameters annotated narrower than what their body takes.

``scripts/check_parameter_annotations.py`` reads every public function and
method of the package and asks that a parameter the body converts with
``np.asarray`` and its kin, or hands to a function whose own parameter is
``ArrayLike``, admit ``ArrayLike``, and that no public parameter hold an
invariant ``list``, ``dict`` or ``set``. Its own run only says the tree is
clean today; these tests fix what it must catch, on small packages written
for the purpose (a multiline call into a helper, an alias of the narrow
union, an alias imported from another module, an overload head, a vararg
converted one argument at a time, a loop over a literal of parameters, a
sequence converted item by item, a closure), and what it must let through
(a pair of limits, a scalar validator, a private helper, a sequence whose
items take a sequence of numbers, a name a nested function, lambda or
comprehension binds for itself).
"""

from __future__ import annotations

import pathlib
import sys
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_parameter_annotations as cpa
import check_return_overloads as overloads

_IMPORTS = """
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, overload

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray
"""


def _package(tmp_path: pathlib.Path, **modules: str) -> pathlib.Path:
    """Write ``pkg`` with *modules*, each opened by the shared imports."""
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    for name, source in modules.items():
        path = root / f"{name.replace('.', '/')}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent != root and not (path.parent / "__init__.py").exists():
            (path.parent / "__init__.py").write_text("", encoding="utf-8")
        path.write_text(_IMPORTS + textwrap.dedent(source), encoding="utf-8")
    return root


def _refused(
    tmp_path: pathlib.Path, *, part: str | None = None, **modules: str
) -> dict[str, list[str]]:
    """The parameters refused, as ``function(parameter)``, with the reasons.

    With *part*, only the findings of that part of the rule.
    """
    root = _package(tmp_path, **modules)
    found: dict[str, list[str]] = {}
    for finding in cpa.findings_in(sorted(root.rglob("*.py")), root):
        if part is not None and finding.part != part:
            continue
        key = f"{finding.function}({finding.parameter})"
        found.setdefault(key, []).append(finding.problem)
    return found


def test_a_list_parameter_the_body_converts_is_refused_twice(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["mean_level"]

        def mean_level(levels: NDArray[np.float64] | list[float]) -> float:
            return float(np.mean(np.asarray(levels, dtype=np.float64)))
        """,
    )
    problems = refused["mean_level(levels)"]
    assert any("np.asarray() converts any array-like" in p for p in problems)
    assert any("holds list[float]" in p for p in problems)


def test_a_dict_parameter_is_refused_and_a_mapping_is_not(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["duct", "duct_mapped"]

        def duct(section: dict[str, float] | None = None) -> float:
            return 0.0 if section is None else sum(section.values())

        def duct_mapped(section: Mapping[str, float] | None = None) -> float:
            return 0.0 if section is None else sum(section.values())
        """,
    )
    assert list(refused) == ["duct(section)"]
    assert "holds dict[str, float]" in refused["duct(section)"][0]


def test_a_container_nested_inside_another_is_refused(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["Database"]

        class Database:
            def __init__(self, aircraft: Mapping[str, dict[str, str]]) -> None:
                self.aircraft = aircraft
        """,
    )
    assert list(refused) == ["Database.__init__(aircraft)"]


def test_a_bare_array_handed_to_a_helper_on_a_continuation_line_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._helpers import _mean

        __all__ = ["sound_power"]

        def sound_power(
            levels: np.ndarray,
            *,
            background_levels: np.ndarray | None = None,
        ) -> float:
            return _mean(
                0.0,
                levels,
            )
        """,
        _helpers="""
        def _mean(offset: float, values: np.ndarray) -> float:
            return offset + float(np.mean(np.asarray(values)))
        """,
    )
    assert list(refused) == ["sound_power(levels)"]
    assert refused["sound_power(levels)"] == [
        "annotated np.ndarray, and handed to _mean(values), np.asarray() converts "
        "any array-like"
    ]


def test_a_parameter_handed_by_keyword_or_through_a_local_name_is_followed(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["by_keyword", "by_name"]

        def _helper(*, values: Sequence[float]) -> np.ndarray:
            return np.atleast_1d(values)

        def by_keyword(levels: Sequence[float]) -> np.ndarray:
            return _helper(values=levels)

        def by_name(levels: Sequence[float]) -> np.ndarray:
            values = levels
            return np.array(values, dtype=float)
        """,
    )
    assert sorted(refused) == ["by_keyword(levels)", "by_name(levels)"]


def test_a_parameter_handed_to_one_typed_array_like_counts_as_converted(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._validation import require_finite_array

        __all__ = ["band_levels"]

        def band_levels(levels: Sequence[float] | np.ndarray) -> np.ndarray:
            return require_finite_array(levels, "levels")
        """,
        _validation="""
        def require_finite_array(x: ArrayLike, name: str) -> np.ndarray:
            raise NotImplementedError
        """,
    )
    assert refused["band_levels(levels)"] == [
        "annotated Sequence[float] | np.ndarray, and handed to "
        "require_finite_array(x: ArrayLike) converts any array-like"
    ]


def test_an_alias_of_the_narrow_union_is_read_through(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._resolve import SignalInput

        __all__ = ["Levels", "peak", "rms"]

        Levels = NDArray[np.float64] | Sequence[float]

        def peak(x: SignalInput) -> float:
            return float(np.max(np.asarray(x)))

        def rms(x: Levels) -> float:
            return float(np.sqrt(np.mean(np.asarray(x) ** 2)))
        """,
        _resolve="""
        class Signal:
            pass

        SignalInput = Signal | Sequence[float] | np.ndarray
        """,
    )
    assert sorted(refused) == ["peak(x)", "rms(x)"]


def test_the_signal_alias_spelled_with_array_like_is_let_through(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._resolve import SignalInput

        __all__ = ["peak"]

        def peak(x: SignalInput) -> float:
            return float(np.max(np.asarray(x)))
        """,
        _resolve="""
        from numpy.typing import ArrayLike

        class Signal:
            pass

        SignalInput = Signal | ArrayLike
        """,
    )
    assert refused == {}


def test_what_the_rule_leaves_alone_is_let_through(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._validation import require_positive

        __all__ = ["Result", "pair", "number", "bounded", "records", "converted"]

        def pair(limits: tuple[float, float] | None = None) -> np.ndarray:
            # A pair whose arity the annotation states, not an array input.
            return np.asarray(limits)

        def number(t60: float) -> float:
            # A single number is no array input, whatever converts it.
            return float(np.asarray(t60))

        def bounded(limits: Sequence[float]) -> float:
            # A function typed to take one number is not followed into.
            return require_positive(limits, "limits")

        def records(layers: Sequence[str]) -> np.ndarray:
            return np.asarray(layers)

        def converted(levels: ArrayLike) -> np.ndarray:
            return np.asarray(levels)

        def _private(levels: list[float]) -> np.ndarray:
            return np.asarray(levels)

        def not_exported(levels: list[float]) -> np.ndarray:
            return np.asarray(levels)

        class Result:
            def _hidden(self, levels: list[float]) -> None:
                np.asarray(levels)
        """,
        _validation="""
        def require_positive(value: float, name: str) -> float:
            return float(np.asarray(value))
        """,
    )
    assert refused == {}


def test_a_sequence_of_pairs_the_body_converts_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["components"]

        def components(parts: Sequence[tuple[float, float]]) -> np.ndarray:
            return np.asarray(parts)
        """,
    )
    assert list(refused) == ["components(parts)"]


def test_a_vararg_converted_one_argument_at_a_time_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A vararg's annotation types each argument, which a loop takes in turn."""
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["cascade", "stacked", "widened"]

        def cascade(*matrices: NDArray[np.complex128]) -> list[np.ndarray]:
            arrays = []
            for i, matrix in enumerate(matrices):
                arrays.append(np.asarray(matrix, dtype=np.complex128))
            return arrays

        def stacked(*rows: NDArray[np.float64]) -> list[np.ndarray]:
            return [np.asarray(row) for row in sorted(rows, key=len)]

        def widened(*matrices: ArrayLike) -> list[np.ndarray]:
            return [np.asarray(matrix) for matrix in matrices]
        """,
    )
    assert sorted(refused) == ["cascade(matrices)", "stacked(rows)"]
    assert refused["cascade(matrices)"] == [
        "annotated NDArray[np.complex128], and np.asarray() converts any array-like"
    ]


def test_each_parameter_a_loop_over_a_literal_takes_is_followed(
    tmp_path: pathlib.Path,
) -> None:
    """``for v in (a, b)`` takes each parameter as it is, in a pair or alone."""
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["columns", "report"]

        def columns(fpi: Sequence[float] | np.ndarray, delta: np.ndarray) -> None:
            for values in (fpi, delta):
                np.asarray(values, dtype=float)

        def report(fpi: np.ndarray | None = None, delta: ArrayLike = None) -> None:
            _columns(fpi, delta)

        def _columns(fpi: np.ndarray | None, delta: ArrayLike) -> None:
            for name, values in (("fpi", fpi), ("delta", delta)):
                if values is not None:
                    np.asarray(values)
        """,
    )
    assert sorted(refused) == ["columns(delta)", "columns(fpi)", "report(fpi)"]


def test_an_item_converted_alone_asks_its_item_type_for_a_sequence(
    tmp_path: pathlib.Path,
) -> None:
    """A body that converts a copy of the parameter item by item reads its items.

    The parameter need not take ``ArrayLike``: each item takes a number, a
    sequence of numbers or an array. An item typed a fixed pair or an array
    alone refuses the list ``np.asarray`` takes, and is refused.
    """
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["budget", "pairs", "codes", "rows"]

        def budget(
            contributions: (
                Sequence[float | Sequence[float] | NDArray[Any]] | NDArray[Any]
            ),
        ) -> float:
            items = list(contributions)
            total = 0.0
            for item in items:
                total += float(np.sum(np.asarray(item)))
            return total

        def pairs(contributions: Sequence[tuple[float, float]]) -> float:
            items = list(contributions)
            return sum(float(np.prod(np.asarray(item))) for item in items)

        def codes(pair: tuple[np.ndarray, np.ndarray]) -> list[np.ndarray]:
            return [_signal(code) for code in pair]

        def rows(levels: Sequence[float]) -> list[np.ndarray]:
            return [np.asarray(level) for level in levels]

        def _signal(x: ArrayLike) -> np.ndarray:
            return np.asarray(x)
        """,
    )
    assert sorted(refused) == ["codes(pair)", "pairs(contributions)"]
    assert refused["pairs(contributions)"] == [
        "annotated Sequence[tuple[float, float]], whose items (tuple[float, float]) "
        "take no sequence of numbers, and an item np.asarray() converts any "
        "array-like"
    ]
    assert refused["codes(pair)"] == [
        "annotated tuple[np.ndarray, np.ndarray], whose items (np.ndarray) take no "
        "sequence of numbers, and an item handed to _signal(x: ArrayLike) converts "
        "any array-like"
    ]


def test_a_name_a_nested_scope_binds_for_itself_is_not_the_parameter(
    tmp_path: pathlib.Path,
) -> None:
    """A nested function, lambda or comprehension that rebinds the name holds another value.

    Its conversion is not the parameter's. A closure that reads the
    parameter, or a name assigned it, converts the parameter itself, and so
    does a method of a class defined in the body, which reads the scope
    around the class and not the class's own names; a comprehension that
    loops over the parameter under its own name takes one item at a time.
    """
    refused = _refused(
        tmp_path,
        api="""
        __all__ = [
            "by_def", "by_lambda", "by_loop", "by_local", "by_class",
            "closure", "closure_copy", "items",
        ]

        def by_def(levels: Sequence[float]) -> float:
            def peak(levels: Sequence[float]) -> float:
                return float(np.max(np.asarray(levels)))
            return sum(levels) + peak([1.0])

        def by_lambda(levels: Sequence[float]) -> float:
            peak = lambda levels: float(np.max(np.asarray(levels)))
            return sum(levels) + peak([1.0])

        def by_loop(levels: Sequence[float], rows: Sequence[float]) -> float:
            return sum(levels) + sum(float(np.sum(np.asarray(levels))) for levels in rows)

        def by_local(levels: Sequence[float]) -> float:
            def peak() -> float:
                levels = [1.0, 2.0]
                return float(np.max(np.asarray(levels)))
            return sum(levels) + peak()

        def by_class(levels: Sequence[float]) -> float:
            class Peak:
                levels = (1.0,)

                def value(self) -> float:
                    return float(np.max(np.asarray(levels)))
            return Peak().value()

        def closure(levels: Sequence[float]) -> float:
            def peak() -> float:
                return float(np.max(np.asarray(levels)))
            return peak()

        def closure_copy(levels: Sequence[float]) -> float:
            def peak() -> float:
                values = levels
                return float(np.max(np.asarray(values)))
            return peak()

        def items(rows: Sequence[tuple[float, float]]) -> list[float]:
            return [float(np.sum(np.asarray(rows))) for rows in rows]
        """,
    )
    assert sorted(refused) == [
        "by_class(levels)",
        "closure(levels)",
        "closure_copy(levels)",
        "items(rows)",
    ]
    assert refused["items(rows)"] == [
        "annotated Sequence[tuple[float, float]], whose items (tuple[float, float]) "
        "take no sequence of numbers, and an item np.asarray() converts any "
        "array-like"
    ]


def test_a_method_taken_from_a_private_base_class_is_read(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        from ._base import _Base

        __all__ = ["Bank"]

        class Bank(_Base):
            def __init__(self, limits: list[float]) -> None:
                self.limits = limits
        """,
        _base="""
        class _Base:
            def filter(self, x: np.ndarray) -> np.ndarray:
                return np.asarray(x)

            def _private(self, x: np.ndarray) -> np.ndarray:
                return np.asarray(x)
        """,
    )
    assert sorted(refused) == ["Bank.__init__(limits)", "_Base.filter(x)"]


def test_an_overload_head_narrower_than_its_implementation_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["weighted", "doubled"]

        class Signal:
            pass

        @overload
        def weighted(x: Signal) -> Signal: ...

        @overload
        def weighted(x: list[float] | np.ndarray) -> np.ndarray: ...

        def weighted(x: Signal | ArrayLike) -> Signal | np.ndarray:
            return x if isinstance(x, Signal) else np.asarray(x)

        @overload
        def doubled[S: float](x: S) -> float: ...

        @overload
        def doubled[V: Sequence[float] | NDArray[np.float64]](x: V) -> np.ndarray: ...

        @overload
        def doubled[A: ArrayLike](x: A) -> float | np.ndarray: ...

        def doubled(x: ArrayLike) -> float | np.ndarray:
            return 2.0 * np.asarray(x)
        """,
    )
    assert sorted(refused) == ["weighted(x)"]
    problems = refused["weighted(x)"]
    assert any(
        "an overload head takes it narrower than ArrayLike" in p for p in problems
    )
    assert any("holds list[float]" in p for p in problems)


def test_an_exemption_covers_only_the_parameter_it_names(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(
        tmp_path,
        api="""
        __all__ = ["write"]

        def write(
            labels: tuple[str, ...] | list[str] | None = None,
            levels: list[float] | None = None,
        ) -> None:
            return None
        """,
    )
    findings = cpa.findings_in(sorted(root.rglob("*.py")), root)
    path = findings[0].path
    exempt = {
        (path, "write", "labels"): "a text stays a type error",
        (path, "write", "gone"): "a parameter that no longer exists",
    }
    kept, stale = cpa.checked(findings, exempt)
    assert [finding.key for finding in kept] == [(path, "write", "levels")]
    assert stale == [(path, "write", "gone")]


def test_the_script_reports_and_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _package(
        tmp_path,
        api="""
        __all__ = ["level"]

        def level(x: list[float]) -> float:
            return float(np.sum(np.asarray(x)))
        """,
    )
    assert cpa.main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "::error::a public parameter is annotated narrower than its body" in out
    assert "api.py:" in out
    assert "level(x): holds list[float]" in out


def test_the_package_keeps_the_rule() -> None:
    """The tree today, with its exemptions, and none of them stale."""
    every = cpa.findings_in(ast_scan.python_files([], cpa.SOURCE), cpa.SOURCE)
    found, stale = cpa.judged(every)
    assert not found, "\n".join(
        f"{f.path}:{f.line}: {f.function}({f.parameter}): {f.problem}" for f in found
    )
    assert not stale


_VALIDATION = """
def require_count(value: object, name: str, *, at_least: int | None = 1) -> int:
    raise NotImplementedError

def require_band_fraction(value: object, name: str) -> int:
    raise NotImplementedError
"""


def test_a_count_a_validator_takes_admits_a_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from ._internal.validation import require_count

            __all__ = ["grid", "grid_or_default", "grid_typed"]

            def _points(offset: float, n: int) -> int:
                return require_count(
                    n,
                    "n_points",
                )

            def grid(n_points: int) -> int:
                return _points(
                    0.0,
                    n_points,
                )

            def grid_or_default(n_points: int | None = None) -> int:
                return 1 if n_points is None else require_count(n_points, "n")

            def grid_typed(n_points: int | np.integer[Any]) -> int:
                return _points(0.0, n_points)
            """,
        },
    )
    assert sorted(refused) == ["grid(n_points)", "grid_or_default(n_points)"]
    assert refused["grid(n_points)"] == [
        "annotated int, which refuses np.integer[Any], while handed to "
        "_points(n), require_count() takes it"
    ]


def test_a_band_fraction_alias_imported_from_another_module_is_read_through(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "_internal.types": """
            from typing import Literal

            BandFraction = Literal[1, 3]
            """,
            "api": """
            from ._internal.types import BandFraction
            from ._internal.validation import require_band_fraction

            __all__ = ["rating", "rating_wide"]

            def rating(fraction: BandFraction = 3) -> int:
                return require_band_fraction(fraction, "fraction")

            def rating_wide(fraction: BandFraction | np.integer[Any] = 3) -> int:
                return require_band_fraction(fraction, "fraction")
            """,
        },
    )
    assert list(refused) == ["rating(fraction)"]
    assert refused["rating(fraction)"] == [
        "annotated BandFraction, which refuses np.integer[Any], while "
        "require_band_fraction() takes it"
    ]


def test_a_flag_an_isinstance_check_lets_through_admits_np_bool_and_a_refusal_keeps_it_out(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["accepts", "accepts_typed", "refuses", "refuses_styled", "real"]

        def accepts(small_room: bool) -> bool:
            if not isinstance(small_room, (bool, np.bool_)):
                raise TypeError("small_room")
            return bool(small_room)

        def accepts_typed(small_room: bool | np.bool_) -> bool:
            if not isinstance(small_room, bool | np.bool_):
                raise TypeError("small_room")
            return bool(small_room)

        def refuses(count: int) -> int:
            if isinstance(count, (bool, np.bool_)):
                raise TypeError("count")
            return count

        def refuses_styled(timeout_s: float = 1.0) -> float:
            if isinstance(timeout_s, bool | np.bool_):
                msg = f"'timeout_s' must be a number of seconds, got {timeout_s!r}."
                raise TypeError(msg)
            return float(timeout_s)

        def real(overlap: float) -> float:
            if not isinstance(overlap, (int, float, np.integer, np.floating)):
                raise TypeError("overlap")
            return float(overlap)
        """,
    )
    assert list(refused) == ["accepts(small_room)"]
    assert refused["accepts(small_room)"] == [
        "annotated bool, which refuses np.bool_, while isinstance(..., np.bool_) "
        "admits it"
    ]


def test_items_validated_one_at_a_time_admit_the_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from ._internal.validation import require_count

            __all__ = ["corners", "corners_either", "pair"]

            def corners(excluded: Sequence[int] = ()) -> list[int]:
                return [require_count(i, "excluded", at_least=0) for i in excluded]

            def corners_either(
                excluded: Sequence[int] | Sequence[np.integer[Any]] = (),
            ) -> list[int]:
                return [require_count(i, "excluded", at_least=0) for i in excluded]

            def pair(limits: tuple[int, int]) -> list[int]:
                checked = []
                for k in limits:
                    checked.append(require_count(k, "limits"))
                return checked
            """,
        },
    )
    assert sorted(refused) == ["corners(excluded)", "pair(limits)"]
    assert refused["pair(limits)"] == [
        "annotated tuple[int, int], whose items (int) refuse np.integer[Any], "
        "while an item require_count() takes it"
    ]


def test_an_unpacked_or_indexed_item_and_its_elements_admit_the_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    """``ny, nx = shape``, ``shape[0]``, ``ix, iy = entry`` and ``for ix, iy in
    cells`` read the items of a parameter, or the elements of each item, as
    a validator takes them.
    """
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from collections.abc import Iterable

            from ._internal.validation import require_count

            __all__ = [
                "grid",
                "grid_wide",
                "first",
                "probes",
                "probes_wide",
                "cells",
                "rows",
            ]

            def _pairs(found: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
                held = []
                for k, entry in enumerate(found):
                    ix, iy = entry
                    held.append((require_count(ix, "ix"), require_count(iy, "iy")))
                return held

            def grid(shape: tuple[int, int]) -> int:
                ny, nx = shape
                return require_count(ny, "ny") * require_count(nx, "nx")

            def grid_wide(shape: Sequence[int | np.integer[Any]]) -> int:
                ny, nx = shape
                return require_count(ny, "ny") * require_count(nx, "nx")

            def first(shape: tuple[int, int]) -> int:
                return require_count(shape[0], "shape[0]")

            def probes(found: Iterable[tuple[int, int]]) -> int:
                return len(_pairs(found))

            def probes_wide(
                found: Iterable[Sequence[int | np.integer[Any]]]
                | NDArray[np.integer[Any]],
            ) -> int:
                return len(_pairs(found))

            def cells(found: Sequence[tuple[int, int]]) -> list[int]:
                return [require_count(ix, "ix") for ix, iy in found]

            def rows(found: Sequence[tuple[int, int]]) -> list[int]:
                return [require_count(row[-1], "iy") for row in found]
            """,
        },
    )
    assert sorted(refused) == [
        "cells(found)",
        "first(shape)",
        "grid(shape)",
        "probes(found)",
        "rows(found)",
    ]
    assert refused["first(shape)"] == [
        "annotated tuple[int, int], whose items (int) refuse np.integer[Any], "
        "while an item require_count() takes it"
    ]
    assert refused["probes(found)"] == [
        "annotated Iterable[tuple[int, int]], whose items' elements (int) refuse "
        "np.integer[Any], while an element of an item handed to _pairs(found), "
        "require_count() takes it"
    ]


def test_an_overload_head_a_none_selects_is_left_alone(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from ._internal.validation import require_count

            __all__ = ["average", "average_narrow"]

            @overload
            def average(levels: ArrayLike, *, axis: None = None) -> float: ...
            @overload
            def average(
                levels: ArrayLike, *, axis: int | np.integer[Any]
            ) -> np.ndarray: ...
            def average(
                levels: ArrayLike, *, axis: int | np.integer[Any] | None = None
            ) -> float | np.ndarray:
                if axis is not None:
                    require_count(axis, "axis", at_least=None)
                return float(np.mean(np.asarray(levels)))

            @overload
            def average_narrow(levels: ArrayLike, *, axis: None = None) -> float: ...
            @overload
            def average_narrow(levels: ArrayLike, *, axis: int) -> np.ndarray: ...
            def average_narrow(
                levels: ArrayLike, *, axis: int | np.integer[Any] | None = None
            ) -> float | np.ndarray:
                if axis is not None:
                    require_count(axis, "axis", at_least=None)
                return float(np.mean(np.asarray(levels)))
            """,
        },
    )
    assert list(refused) == ["average_narrow(axis)"]


def test_a_record_field_kept_as_given_is_held_and_one_stored_is_not(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from dataclasses import dataclass

            from ._internal.validation import require_count

            __all__ = ["Tubes", "Meter"]

            _FLAGS = ("latched", "indicated")

            @dataclass(frozen=True)
            class Tubes:
                n_tubes: int
                n_stored: int
                n_wide: int | np.integer[Any] = 1

                def __post_init__(self) -> None:
                    require_count(self.n_tubes, "n_tubes")
                    object.__setattr__(
                        self, "n_stored", require_count(self.n_stored, "n_stored")
                    )
                    require_count(self.n_wide, "n_wide")

            @dataclass(frozen=True)
            class Meter:
                latched: bool | None = None
                indicated: bool | None = None
                stored: bool | None = None

                def __post_init__(self) -> None:
                    self._check("latched")
                    for name in ("stored",):
                        value = getattr(self, name)
                        if not isinstance(value, bool | np.bool_):
                            raise TypeError(name)
                        object.__setattr__(self, name, bool(value))
                    self._hold()

                def _check(self, name: str) -> None:
                    value = getattr(self, name)
                    if value is not None and not isinstance(value, bool | np.bool_):
                        raise TypeError(name)

                def _hold(self) -> None:
                    if self.indicated is not None and not isinstance(
                        self.indicated, bool | np.bool_
                    ):
                        raise TypeError("indicated")
            """,
        },
    )
    assert sorted(refused) == [
        "Meter(indicated)",
        "Meter(latched)",
        "Tubes(n_tubes)",
    ]
    assert refused["Meter(latched)"] == [
        "annotated bool | None, which refuses np.bool_, while handed by name to "
        "Meter._check(name), isinstance(..., np.bool_) admits it"
    ]
    assert refused["Meter(indicated)"] == [
        "annotated bool | None, which refuses np.bool_, while read in "
        "Meter._hold(), isinstance(..., np.bool_) admits it"
    ]


def test_a_field_is_read_scope_by_scope(tmp_path: pathlib.Path) -> None:
    """A field read by name in a comprehension or a closure is the field; one a nested scope rebinds is not.

    ``getattr(self, name)`` in a comprehension over field names reads each of
    them, as a ``for`` loop does, and a nested function that reads ``self``
    from the body around it reads the record. A nested function whose own
    ``self`` is another value, and a comprehension that takes ``name`` for
    itself, read something else under the same spelling.
    """
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from dataclasses import dataclass

            from ._internal.validation import require_count

            __all__ = ["Counts"]

            _ROWS = ("n_rows",)

            @dataclass(frozen=True)
            class Counts:
                n_rows: int
                n_cols: int
                n_spare: int = 0
                n_other: int = 0

                def __post_init__(self) -> None:
                    [require_count(getattr(self, name), name) for name in _ROWS]

                    def _cols() -> int:
                        return require_count(self.n_cols, "n_cols")

                    def _spare(self: Counts) -> int:
                        return require_count(self.n_spare, "n_spare")

                    for name in ("n_other",):
                        [require_count(getattr(self, name), name) for name in ("x",)]
                    _cols()
                    _spare(self)
            """,
        },
    )
    assert sorted(refused) == ["Counts(n_cols)", "Counts(n_rows)"]


_RECORDS = """
from dataclasses import dataclass

from ._internal.validation import require_count

__all__ = ["Device", "Typed", "Handed", "Result", "run", "summary"]

@dataclass(frozen=True, kw_only=True)
class Device:
    fallback: bool = True
    index: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.fallback, bool | np.bool_):
            msg = f"'fallback' must be a bool, got {self.fallback!r}."
            raise TypeError(msg)
        object.__setattr__(self, "fallback", bool(self.fallback))
        object.__setattr__(self, "index", require_count(self.index, "index", at_least=0))

@dataclass(frozen=True, kw_only=True)
class Typed:
    fallback: bool = True

    if TYPE_CHECKING:
        def __init__(self, *, fallback: bool | np.bool_ = True) -> None: ...

    def __post_init__(self) -> None:
        if not isinstance(self.fallback, bool | np.bool_):
            raise TypeError("fallback")
        object.__setattr__(self, "fallback", bool(self.fallback))

@dataclass(frozen=True, kw_only=True)
class Handed:
    index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", require_count(self.index, "index"))

@dataclass(frozen=True, kw_only=True)
class Result:
    index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", require_count(self.index, "index"))

def run(device: Device | None = None, typed: Typed | None = None) -> Handed:
    return Handed()

def summary(handed: Sequence[Handed]) -> Result:
    return Result()
"""


def test_a_field_a_caller_built_record_stores_is_held_through_its_constructor(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(tmp_path, **{"_internal.validation": _VALIDATION, "api": _RECORDS})
    files = sorted(root.rglob("*.py"))
    found = cpa.findings_in(files, root, handed_on=frozenset({"pkg.api.Handed"}))
    assert sorted((f.function, f.parameter, f.constructor) for f in found) == [
        ("Device", "fallback", True),
        ("Device", "index", True),
    ]
    assert found[0].problem.endswith(
        "Device is built by its caller and stores the value it validates, so its "
        "constructor takes the numpy scalar (a TYPE_CHECKING __init__)"
    )
    # Handed on whole from run() to summary(), Handed is a result too.
    unclassed = cpa.findings_in(files, root, handed_on=frozenset())
    assert sorted((f.function, f.parameter) for f in unclassed) == [
        ("Device", "fallback"),
        ("Device", "index"),
        ("Handed", "index"),
    ]


_HELD_BY_NAME = """
from dataclasses import dataclass

from ._internal.validation import require_count

__all__ = ["Pulse", "Line", "Typed", "run"]

Cells = int

def _hold(record: object, *names: str) -> None:
    for name in names:
        object.__setattr__(record, name, require_count(getattr(record, name), name))

def _hold_one(record: object, name: str) -> None:
    object.__setattr__(record, name, require_count(getattr(record, name), name))

@dataclass(frozen=True, kw_only=True)
class Pulse:
    ix: int
    iy: int
    width: float = 1.0

    def __post_init__(self) -> None:
        _hold(self, "ix",
              "iy")

@dataclass(frozen=True, kw_only=True)
class Line:
    offset: Cells = 0

    def __post_init__(self) -> None:
        _hold_one(self, "offset")

@dataclass(frozen=True, kw_only=True)
class Typed:
    ix: int

    if TYPE_CHECKING:
        def __init__(self, *, ix: int | np.integer[Any]) -> None: ...

    def __post_init__(self) -> None:
        _hold(self, "ix")

def run(sources: Sequence[Pulse | Line | Typed]) -> None:
    return None
"""


def test_a_field_handed_by_name_with_the_record_is_followed_and_stored(
    tmp_path: pathlib.Path,
) -> None:
    """``_hold(self, "ix", "iy")`` validates and stores each field it is named.

    The record and the names go to a function of the package, which reads
    ``getattr(record, name)`` for each name of its vararg (or the one its
    parameter holds) and stores what the validator returns: the fields are
    validated by ``require_count`` and stored, so the constructor of a record
    a caller builds takes the numpy integer.
    """
    root = _package(
        tmp_path, **{"_internal.validation": _VALIDATION, "api": _HELD_BY_NAME}
    )
    reader = cpa.Reader(
        overloads.Package(sorted(root.rglob("*.py")), root), handed_on=frozenset()
    )
    assert cpa.converted_fields(reader, "pkg.api.Pulse") == {"ix", "iy"}
    assert cpa.converted_fields(reader, "pkg.api.Line") == {"offset"}
    found = cpa.findings_in(sorted(root.rglob("*.py")), root, handed_on=frozenset())
    assert sorted((f.function, f.parameter, f.constructor) for f in found) == [
        ("Line", "offset", True),
        ("Pulse", "ix", True),
        ("Pulse", "iy", True),
    ]
    by_key = {(f.function, f.parameter): f.problem for f in found}
    assert by_key["Pulse", "ix"].startswith(
        "annotated int, which refuses np.integer[Any], while handed by name to "
        "_hold(names), require_count() takes it"
    )
    assert by_key["Line", "offset"].startswith(
        "annotated Cells, which refuses np.integer[Any], while handed by name to "
        "_hold_one(name), require_count() takes it"
    )


def test_a_whole_number_a_scalar_check_reads_admits_a_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION
            + """
def require_scalar(value: object, name: str) -> None:
    raise NotImplementedError

def require_positive(value: float, name: str) -> float:
    raise NotImplementedError
""",
            "api": """
            from ._internal.validation import (
                require_count,
                require_positive,
                require_scalar,
            )

            __all__ = ["blades", "orders", "gain", "counted", "typed"]

            def blades(rpm: float, n_blades: int) -> float:
                require_scalar(n_blades, "n_blades")
                if n_blades <= 0 or not float(n_blades).is_integer():
                    msg = "'n_blades' must be a positive integer."
                    raise ValueError(msg)
                return rpm * n_blades

            def orders(n: Sequence[int]) -> float:
                return sum(require_positive(i, "n") for i in n)

            def gain(level_db: float) -> float:
                return require_positive(level_db, "level_db")

            def counted(n_blades: int) -> int:
                require_scalar(n_blades, "n_blades")
                return require_count(n_blades, "n_blades")

            def typed(n_blades: int | np.integer[Any]) -> float:
                require_scalar(n_blades, "n_blades")
                return float(n_blades)
            """,
        },
    )
    assert sorted(refused) == ["blades(n_blades)", "counted(n_blades)", "orders(n)"]
    assert refused["blades(n_blades)"] == [
        "annotated int, which refuses np.integer[Any], while require_scalar() takes it"
    ]
    # Reported once, from the count validator, not again from the scalar check.
    assert refused["counted(n_blades)"] == [
        "annotated int, which refuses np.integer[Any], while require_count() takes it"
    ]
    assert refused["orders(n)"] == [
        "annotated Sequence[int], whose items (int) refuse np.integer[Any], while "
        "an item require_positive() takes it"
    ]


def test_a_count_and_its_items_handed_to_a_generated_constructor_are_followed(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        **{
            "_internal.validation": _VALIDATION,
            "api": """
            from dataclasses import KW_ONLY, dataclass

            from ._internal.validation import require_count

            __all__ = ["contour", "contour_by_position", "contour_typed", "Layout"]

            @dataclass(frozen=True)
            class Layout:
                height_m: float
                n_positions: int
                omitted: tuple[int, ...] = ()
                _: KW_ONLY
                label: int = 0

                def __post_init__(self) -> None:
                    object.__setattr__(
                        self, "n_positions", require_count(self.n_positions, "n")
                    )
                    object.__setattr__(
                        self,
                        "omitted",
                        tuple(require_count(i, "omitted") for i in self.omitted),
                    )

            def contour(n_positions: int, omitted: Sequence[int] = ()) -> Layout:
                kept = tuple(omitted)
                return Layout(height_m=1.0, n_positions=n_positions, omitted=kept)

            def contour_by_position(n_positions: int, label: int = 0) -> Layout:
                return Layout(1.0, n_positions, label=label)

            def contour_typed(
                n_positions: int | np.integer[Any],
                omitted: Sequence[int | np.integer[Any]] = (),
            ) -> Layout:
                return Layout(1.0, int(n_positions), tuple(map(int, omitted)))
            """,
        },
    )
    assert sorted(refused) == [
        "contour(n_positions)",
        "contour(omitted)",
        "contour_by_position(n_positions)",
    ]
    assert refused["contour(n_positions)"] == [
        "annotated int, which refuses np.integer[Any], while handed to "
        "Layout(n_positions), require_count() takes it"
    ]
    assert refused["contour(omitted)"] == [
        "annotated Sequence[int], whose items (int) refuse np.integer[Any], while "
        "an item handed to Layout(omitted), require_count() takes it"
    ]


def test_a_count_handed_to_a_public_function_that_takes_a_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        api="""
        __all__ = ["bank", "decay", "decay_through_a_helper"]

        def bank(bandwidth: float | np.integer[Any] = 1) -> float:
            return float(bandwidth)

        def _rate(fs: float | np.integer[Any] | None) -> float:
            return 1.0 if fs is None else float(fs)

        def decay(bandwidth: int = 1) -> float:
            return bank(bandwidth)

        def decay_through_a_helper(fs: float | None = None) -> float:
            return _rate(fs)
        """,
    )
    assert list(refused) == ["decay(bandwidth)"]
    assert refused["decay(bandwidth)"] == [
        "annotated int, which refuses np.integer[Any], while handed to "
        "bank(bandwidth: np.integer[Any])"
    ]


def test_a_mapping_keyed_by_float_is_offered_beside_one_keyed_by_int(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        part="key",
        api="""
        from typing import Literal

        Side = Literal["left", "right"]
        BandMapping = Mapping[int, float] | Mapping[float, float]

        __all__ = [
            "rating", "rating_both", "limits", "limits_both", "burst", "burst_named",
            "sides",
        ]

        def rating(values: Mapping[float, float] | ArrayLike) -> float:
            return 0.0

        def rating_both(values: BandMapping | ArrayLike) -> float:
            return 0.0

        def limits(per_direction: Mapping[str, Mapping[float, float]]) -> float:
            return 0.0

        def limits_both(per_direction: Mapping[str, BandMapping]) -> float:
            return 0.0

        def burst(measured: Mapping[int | None, Mapping[str, float]]) -> float:
            return 0.0

        def burst_named(
            measured: Mapping[int, Mapping[str, float]]
            | Mapping[int | None, Mapping[str, float]]
            | Mapping[None, Mapping[str, float]],
        ) -> float:
            return 0.0

        def sides(by_side: Mapping[Side, float]) -> float:
            return 0.0
        """,
    )
    assert sorted(refused) == [
        "burst(measured)",
        "limits(per_direction)",
        "rating(values)",
    ]
    assert refused["rating(values)"] == [
        "holds Mapping[float, float] with no mapping keyed by int, which refuses "
        "a typed caller's dict of the narrower key"
    ]
    assert refused["burst(measured)"] == [
        "holds Mapping[int | None, Mapping[str, float]] with no mapping keyed by "
        "None, int, which refuses a typed caller's dict of the narrower key"
    ]


def test_a_head_is_offered_keys_only_by_heads_that_take_its_other_arguments(
    tmp_path: pathlib.Path,
) -> None:
    """A key offered by a head that a call of this one misses offers it nothing.

    ``rating("b", by_band)`` with a ``dict[int, float]`` matches no head:
    the head keyed by ``int`` takes ``kind="a"`` only, and the one of
    ``defaulted`` keyed by ``int`` asks for the ``kind`` the other lets a
    call leave out. Heads that differ only in the mapping, that spell one
    ``Literal`` once through an alias and once in full, that name a
    positional-only parameter apart, or whose head keyed by ``int`` takes
    more choices than the other, offer each other their keys.
    """
    refused = _refused(
        tmp_path,
        part="key",
        api="""
        from typing import Literal

        Kind = Literal["a", "b"]

        __all__ = ["rating", "spelt", "defaulted", "positional", "wider"]

        @overload
        def rating(kind: Literal["a"], by_band: Mapping[int, float]) -> float: ...
        @overload
        def rating(kind: Literal["b"], by_band: Mapping[float, float]) -> float: ...
        def rating(
            kind: Kind, by_band: Mapping[int, float] | Mapping[float, float]
        ) -> float:
            return 0.0

        @overload
        def spelt(kind: Kind, by_band: Mapping[int, float]) -> float: ...
        @overload
        def spelt(kind: Literal["b", "a"], by_band: Mapping[float, float]) -> float: ...
        def spelt(
            kind: Kind, by_band: Mapping[int, float] | Mapping[float, float]
        ) -> float:
            return 0.0

        @overload
        def defaulted(by_band: Mapping[int, float], *, kind: Kind) -> float: ...
        @overload
        def defaulted(
            by_band: Mapping[float, float], *, kind: Kind = "a"
        ) -> float: ...
        def defaulted(
            by_band: Mapping[int, float] | Mapping[float, float], *, kind: Kind = "a"
        ) -> float:
            return 0.0

        @overload
        def positional(by_band: Mapping[int, float], kind: Kind, /) -> float: ...
        @overload
        def positional(by_band: Mapping[float, float], other: Kind, /) -> float: ...
        def positional(
            by_band: Mapping[int, float] | Mapping[float, float], kind: Kind, /
        ) -> float:
            return 0.0

        @overload
        def wider(
            by_band: Mapping[int, float], kind: Kind | None = None
        ) -> float: ...
        @overload
        def wider(by_band: Mapping[float, float], kind: Literal["a"]) -> float: ...
        def wider(
            by_band: Mapping[int, float] | Mapping[float, float],
            kind: Kind | None = None,
        ) -> float:
            return 0.0
        """,
    )
    assert sorted(refused) == ["defaulted(by_band)", "rating(by_band)"]
    assert refused["rating(by_band)"] == [
        "holds Mapping[float, float] with no mapping keyed by int, which refuses "
        "a typed caller's dict of the narrower key"
    ]


def test_a_union_split_across_heads_of_different_calls_offers_no_context(
    tmp_path: pathlib.Path,
) -> None:
    """Each mapping alone in a head, but no call reaches both heads.

    ``split("a", {None: {"rms": 1.0}})`` runs and matches no head; the heads
    of ``covered`` that take ``Kind`` offer both mappings to every call,
    and its narrower head beside them changes nothing.
    """
    refused = _refused(
        tmp_path,
        part="pairing",
        api="""
        from typing import Literal

        Kind = Literal["a", "b"]
        Columns = Mapping[Literal["rms", "vdv"], float]

        __all__ = ["split", "covered"]

        @overload
        def split(kind: Literal["a"], measured: Mapping[int, Columns]) -> float: ...
        @overload
        def split(kind: Literal["b"], measured: Mapping[None, Columns]) -> float: ...
        def split(
            kind: Kind, measured: Mapping[int, Columns] | Mapping[None, Columns]
        ) -> float:
            return 0.0

        @overload
        def covered(
            kind: Literal["a"], measured: Mapping[int, Columns]
        ) -> float: ...
        @overload
        def covered(kind: Kind, measured: Mapping[int, Columns]) -> float: ...
        @overload
        def covered(kind: Kind, measured: Mapping[None, Columns]) -> float: ...
        def covered(
            kind: Kind, measured: Mapping[int, Columns] | Mapping[None, Columns]
        ) -> float:
            return 0.0
        """,
    )
    assert refused == {
        "split(measured)": [
            "takes Mapping[int, Columns] | Mapping[None, Columns], and the "
            "overload heads that take each of them alone take different calls "
            "but for it, so a dict written in a call one of them takes is read "
            "against that head's mapping, never against the others: offer each "
            "mapping alone in heads that take the same other arguments"
        ]
    }


def test_heads_that_pair_each_mapping_with_another_parameter_are_listed(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run that refuses a mapping beside a value of another parameter.

    ``budget`` takes the components of one table with ``field="pressure"``,
    those of the other with ``field="free"`` and those both list with a
    field held in a variable, as the IEC 61094 budgets do: its heads take
    different calls on purpose, which only :data:`PAIRED_MAPPINGS` can say.
    Listed, it passes; the listing excuses no mapping that no head offers
    alone (``unsplit``), and an entry that covers no pairing is stale.
    """
    root = _package(
        tmp_path,
        api="""
        from typing import Literal

        Field = Literal["pressure", "free"]
        Pressure = Literal["impedance", "reference"]
        Free = Literal["positioning", "reference"]
        Shared = Literal["reference"]

        __all__ = ["budget", "unsplit"]

        @overload
        def budget(
            parts: Mapping[Pressure, float], field: Literal["pressure"] = "pressure"
        ) -> float: ...
        @overload
        def budget(parts: Mapping[Free, float], field: Literal["free"]) -> float: ...
        @overload
        def budget(parts: Mapping[Shared, float], field: Field) -> float: ...
        def budget(
            parts: Mapping[Pressure, float]
            | Mapping[Free, float]
            | Mapping[Shared, float],
            field: Field = "pressure",
        ) -> float:
            return 0.0

        @overload
        def unsplit(
            parts: Mapping[Pressure, float], field: Literal["pressure"] = "pressure"
        ) -> float: ...
        @overload
        def unsplit(parts: Mapping[Shared, float], field: Field) -> float: ...
        def unsplit(
            parts: Mapping[Pressure, float]
            | Mapping[Free, float]
            | Mapping[Shared, float],
            field: Field = "pressure",
        ) -> float:
            return 0.0
        """,
    )
    findings = cpa.findings_in(sorted(root.rglob("*.py")), root)
    assert sorted((f.function, f.part) for f in findings) == [
        ("budget", "pairing"),
        ("unsplit", "context"),
    ]
    path = findings[0].path
    monkeypatch.setattr(
        cpa,
        "PAIRED_MAPPINGS",
        {
            (path, "budget", "parts"): "each table's components go with its field",
            (path, "unsplit", "parts"): "a mapping no head offers alone",
            (path, "gone", "parts"): "a function that no longer exists",
        },
    )
    found, stale = cpa.judged(findings)
    assert [(f.function, f.part) for f in found] == [("unsplit", "context")]
    assert [key for table, key in stale if table == "PAIRED_MAPPINGS"] == [
        (path, "gone", "parts"),
        (path, "unsplit", "parts"),
    ]


def test_a_union_of_mappings_offers_a_written_dict_one_head_at_a_time(
    tmp_path: pathlib.Path,
) -> None:
    """mypy reads a ``dict`` written in a call against one mapping, not a union.

    With two or more mappings in a union, the ``dict`` is read on its own: a
    ``Literal`` key becomes a ``str`` and nested mappings of two key types
    join to ``object``, so a call that runs is refused. Each mapping is
    offered in an overload head of its own, every head together offering
    the keys the key rule asks for; a union whose mappings hold only plain
    numbers, and a head that takes one mapping, pass.
    """
    refused = _refused(
        tmp_path,
        api="""
        from typing import Literal

        Quantity = Literal["rms", "vdv"]
        Columns = Mapping[Quantity, float]
        BandMapping = Mapping[int, float] | Mapping[float, float]
        Indications = (
            Mapping[int, Columns] | Mapping[int | None, Columns] | Mapping[None, Columns]
        )

        __all__ = [
            "named", "headed", "missing", "two_in_a_head", "nested", "bands",
            "directional",
        ]

        def named(measured: Indications) -> float:
            return 0.0

        @overload
        def headed(measured: Mapping[int, Columns]) -> float: ...
        @overload
        def headed(measured: Mapping[None, Columns]) -> float: ...
        @overload
        def headed(measured: Mapping[int | None, Columns]) -> float: ...
        def headed(measured: Indications) -> float:
            return 0.0

        @overload
        def missing(measured: Mapping[int, Columns]) -> float: ...
        @overload
        def missing(measured: Mapping[int | None, Columns]) -> float: ...
        def missing(measured: Indications) -> float:
            return 0.0

        @overload
        def two_in_a_head(measured: Mapping[int, Columns]) -> float: ...
        @overload
        def two_in_a_head(
            measured: Mapping[int | None, Columns] | Mapping[None, Columns],
        ) -> float: ...
        def two_in_a_head(measured: Indications) -> float:
            return 0.0

        def nested(per_direction: Mapping[str, Indications]) -> float:
            return 0.0

        def bands(values: BandMapping | None = None) -> float:
            return 0.0

        def directional(
            *,
            by_band: Mapping[int, BandMapping]
            | Mapping[float, BandMapping]
            | None = None,
        ) -> float:
            return 0.0
        """,
    )
    assert sorted(refused) == [
        "directional(by_band)",
        "missing(measured)",
        "named(measured)",
        "nested(per_direction)",
        "two_in_a_head(measured)",
    ]
    assert refused["named(measured)"] == [
        "takes Mapping[int, Columns] | Mapping[int | None, Columns] | "
        "Mapping[None, Columns] with no overload head that takes Mapping[int, "
        "Columns] or Mapping[int | None, Columns] or Mapping[None, Columns] "
        "alone, so a dict written in the call is read against none of them: a "
        "Literal key is read as a str and nested mappings of two key types as "
        "object, and a call that runs is refused"
    ]
    assert sorted(refused["missing(measured)"]) == [
        "holds Mapping[int | None, Columns] with no mapping keyed by None, which "
        "refuses a typed caller's dict of the narrower key",
        "takes Mapping[int, Columns] | Mapping[int | None, Columns] | "
        "Mapping[None, Columns] with no overload head that takes Mapping[None, "
        "Columns] alone, so a dict written in the call is read against none of "
        "them: a Literal key is read as a str and nested mappings of two key "
        "types as object, and a call that runs is refused",
    ]
    head, implementation = refused["two_in_a_head(measured)"]
    assert head == (
        "an overload head takes Mapping[int | None, Columns] | Mapping[None, "
        "Columns], which gives a dict written in the call no mapping to be read "
        "against"
    )
    assert "no overload head that takes Mapping[int | None, Columns] or " in (
        implementation
    )
    assert refused["nested(per_direction)"] == [
        "holds Mapping[int, Columns] | Mapping[int | None, Columns] | "
        "Mapping[None, Columns] inside, where no overload can give a dict "
        "written in the call the one mapping it is read against"
    ]
    assert refused["directional(by_band)"][0].startswith(
        "takes Mapping[int, BandMapping] | Mapping[float, BandMapping] with no "
        "overload head"
    )


def test_a_window_scipy_reads_takes_a_name_and_its_parameters(
    tmp_path: pathlib.Path,
) -> None:
    """``get_window`` takes ``("kaiser", 8.6)`` as it takes ``"hann"``.

    A parameter followed into a helper, on a multiline call, into a SciPy
    reader by keyword or by position (``resample`` and ``firwin_2d`` among
    them), and one typed by an alias of ``str``, are refused; one typed with
    a tuple, or never handed to SciPy, passes.
    """
    refused = _refused(
        tmp_path,
        part="window",
        api="""
        from scipy import signal as sp_signal

        Taper = str
        Spec = str | tuple[ArrayLike, ...]

        __all__ = [
            "psd", "taper", "spectrum", "named", "taken", "labelled", "resampled",
            "resampled_at", "design",
        ]

        def _segments(x: ArrayLike, window: str) -> float:
            return float(sp_signal.welch(x, fs=1.0, window=window)[1][0])

        def psd(x: ArrayLike, *, window: str = "hann") -> float:
            return _segments(
                x,
                window,
            )

        def taper(window: Taper, n: int) -> float:
            return float(sp_signal.get_window(window, n)[0])

        def spectrum(x: ArrayLike, window: str = "hann") -> float:
            return float(sp_signal.stft(x, 1.0, window)[2][0, 0])

        def named(window: str) -> str:
            return window

        def taken(window: Spec = "hann") -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def labelled(window: tuple[ArrayLike, ...] | str) -> float:
            return _segments([0.0] * 8, window)  # type: ignore[arg-type]

        def resampled(x: ArrayLike, window: str) -> float:
            return float(sp_signal.resample(x, 8, window=window)[0])

        def resampled_at(x: ArrayLike, window: str) -> float:
            return float(sp_signal.resample(x, 8, None, 0, window)[0])

        def design(window: str = "hamming") -> float:
            return float(sp_signal.firwin_2d((5, 5), window, fc=0.5)[0, 0])
        """,
    )
    assert sorted(refused) == [
        "design(window)",
        "psd(window)",
        "resampled(window)",
        "resampled_at(window)",
        "spectrum(window)",
        "taper(window)",
    ]
    assert refused["psd(window)"] == [
        "annotated str, which refuses a window given as a tuple of its name and "
        "parameters, such as ('kaiser', 8.6), while handed to _segments(window), "
        "welch() takes it"
    ]
    assert refused["taper(window)"][0].startswith("annotated Taper, which refuses")


def test_a_window_tuple_takes_a_name_and_any_count_of_parameters(
    tmp_path: pathlib.Path,
) -> None:
    """A tuple of the annotation takes every window SciPy reads.

    ``("kaiser", 8.6)``, ``("general_gaussian", 1.5, 7.0)`` and
    ``("general_cosine", [0.5, 0.5])``: a text first, then any count of
    numbers or sequences of numbers. A tuple of floats refuses the name, one
    of a fixed length refuses a second parameter, one of a name and floats
    or integers refuses the weights; a bare tuple, one of ``ArrayLike`` or
    anything, a name unpacked beside them, or items that take a text, a
    float and a sequence of numbers take every window.
    """
    refused = _refused(
        tmp_path,
        part="window",
        api="""
        from typing import Unpack

        from scipy import signal as sp_signal

        Parameters = tuple[ArrayLike, ...]

        __all__ = [
            "floats", "pair", "named", "scalars", "counts", "empty", "bare",
            "spec", "unpacked", "aliased", "spelt", "anything", "spread",
        ]

        def floats(window: str | tuple[float, ...]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def pair(window: str | tuple[str, float]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def named(window: str | tuple[str]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def scalars(window: str | tuple[str, *tuple[float, ...]]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def counts(window: str | tuple[str, Unpack[tuple[int, ...]]]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def empty(window: str | tuple[()]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def bare(window: str | tuple) -> float:  # type: ignore[type-arg]
            return float(sp_signal.get_window(window, 8)[0])

        def spec(window: str | tuple[ArrayLike, ...]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def unpacked(window: str | tuple[str, *tuple[ArrayLike, ...]]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def aliased(window: str | tuple[str, Unpack[Parameters]]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def spelt(window: str | tuple[str | float | Sequence[float], ...]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def anything(window: str | tuple[Any, ...]) -> float:
            return float(sp_signal.get_window(window, 8)[0])

        def spread[*Ts](window: str | tuple[str, *Ts]) -> float:
            return float(sp_signal.get_window(window, 8)[0])
        """,
    )
    assert sorted(refused) == [
        "counts(window)",
        "empty(window)",
        "floats(window)",
        "named(window)",
        "pair(window)",
        "scalars(window)",
    ]
    assert refused["floats(window)"] == [
        "annotated str | tuple[float, ...], which refuses a window given as a "
        "tuple of its name and parameters, such as ('kaiser', 8.6), while "
        "get_window() takes it"
    ]


def test_every_window_reader_of_scipy_is_listed() -> None:
    """Each callable of ``scipy.signal`` that takes a window is a reader.

    A ``window`` or ``win_param`` parameter of SciPy goes to ``get_window``;
    one missing from the list lets a public ``window: str`` handed to it
    through. Each is listed with its place, or with a place no call fills
    when SciPy takes it by keyword only.
    """
    import inspect

    from scipy import signal

    readers: dict[str, tuple[int | None, str | None]] = {}
    callables = [
        (f"scipy.signal.{name}", getattr(signal, name)) for name in dir(signal)
    ]
    callables.append(
        ("scipy.signal.ShortTimeFFT.from_window", signal.ShortTimeFFT.from_window)
    )
    for dotted, member in callables:
        if not inspect.isfunction(member) and not inspect.ismethod(member):
            continue
        parameters = list(inspect.signature(member).parameters.values())
        for index, parameter in enumerate(parameters):
            if parameter.name in {"window", "win_param"}:
                readers[dotted] = (index, parameter.name)
    listed = {
        dotted: cpa._WINDOW_READERS[dotted]
        for dotted in readers
        if dotted in cpa._WINDOW_READERS
    }
    assert listed == readers


def test_a_record_field_offers_a_written_dict_one_mapping(
    tmp_path: pathlib.Path,
) -> None:
    """A record's generated constructor has no heads to split a union with."""
    refused = _refused(
        tmp_path,
        part="context",
        api="""
        from dataclasses import dataclass
        from typing import Literal

        Quantity = Literal["rms", "vdv"]

        __all__ = ["Readings", "Bands"]

        @dataclass(frozen=True)
        class Readings:
            measured: Mapping[int, Mapping[Quantity, float]] | Mapping[
                None, Mapping[Quantity, float]
            ]

        @dataclass(frozen=True)
        class Bands:
            values: Mapping[int, float] | Mapping[float, float]
        """,
    )
    assert list(refused) == ["Readings(measured)"]


def test_a_sample_rate_keeps_one_family_across_the_api(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(
        tmp_path,
        api="""
        from dataclasses import dataclass

        __all__ = ["level", "level_whole", "Recording", "Fixed"]

        def level(x: ArrayLike, fs: float | None = None) -> float:
            return 0.0

        def level_whole(x: ArrayLike, fs: int | None = None) -> float:
            return 0.0

        @dataclass(frozen=True)
        class Recording:
            fs: float

        @dataclass(frozen=True)
        class Fixed:
            fs: int
        """,
    )
    findings = [
        finding
        for finding in cpa.findings_in(sorted(root.rglob("*.py")), root)
        if finding.part == "name"
    ]
    assert [(f.function, f.parameter) for f in findings] == [
        ("level_whole", "fs"),
        ("Fixed", "fs"),
    ]
    assert findings[0].problem == (
        "annotated int | None, a whole number, where every 'fs' of the API is a "
        "real one"
    )
    path = findings[0].path
    exempt = {
        (path, "Fixed", "fs"): "the whole rate its function validated",
        (path, "Gone", "fs"): "a record that no longer exists",
    }
    kept, stale = cpa.checked(findings, exempt)
    assert [f.function for f in kept] == ["level_whole"]
    assert stale == [(path, "Gone", "fs")]


_NUMERIC_TYPES = """
from collections.abc import Iterator
from typing import Protocol


class SupportsNumericArray(Protocol):
    def __array__(self) -> np.ndarray[Any, np.dtype[np.number[Any] | np.bool_]]: ...


class NestedSequence[T](Protocol):
    def __len__(self, /) -> int: ...
    def __getitem__(self, index: int, /) -> T | NestedSequence[T]: ...
    def __contains__(self, value: object, /) -> bool: ...
    def __iter__(self, /) -> Iterator[T | NestedSequence[T]]: ...


NumericArrayLike = (
    complex
    | NestedSequence[complex]
    | SupportsNumericArray
    | NestedSequence[SupportsNumericArray]
)
"""


def test_a_choice_beside_an_alternative_that_takes_any_text_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``ArrayLike`` admits any ``str``, so a misspelt choice beside it type-checks.

    A ``Literal`` of texts is refused beside ``ArrayLike``, ``str``,
    ``LiteralString``, numpy's ``DTypeLike``, a sequence of texts or a type
    parameter that takes a text (one bound to ``str``, or one with no bound,
    which a type checker solves to ``str``), at the top or inside a
    container, written or behind an alias of an alias, on an overload head,
    in a record's field, a generic record's included, and in the constructor
    a record declares. Beside the package's array-like of numbers, beside a
    pair, beside a type parameter bound to a number or as a mapping's key,
    and as integer choices, it passes, and so does a private helper.
    """
    refused = _refused(
        tmp_path,
        part="choice",
        **{
            "_internal.types": _NUMERIC_TYPES,
            "api": """
            from dataclasses import dataclass
            from typing import Literal, LiteralString

            from numpy.typing import DTypeLike

            from ._internal.types import NumericArrayLike

            Termination = Literal["rigid", "free"]
            Spelt = Termination | ArrayLike
            Values = Mapping[str, float] | ArrayLike

            __all__ = [
                "written", "aliased", "banded", "nested", "texts", "text",
                "headed", "Ground", "Built", "numeric", "paired", "keyed",
                "whole", "dtyped", "spelt_text", "bound", "bound_inside",
                "bound_items", "open_parameter", "Held", "bound_numbers",
            ]

            def written(termination: Literal["rigid", "free"] | ArrayLike) -> None: ...

            def aliased(termination: Spelt = "rigid") -> None: ...

            def banded(values: Literal["auto"] | Values) -> None: ...

            def nested(terms: Sequence[Termination | ArrayLike]) -> None: ...

            def texts(labels: Literal["auto"] | Sequence[str]) -> None: ...

            def text(name: Termination | str | None = None) -> None: ...

            @overload
            def headed(x: ArrayLike, state: Termination | ArrayLike) -> None: ...
            @overload
            def headed(x: None, state: Termination | NumericArrayLike) -> None: ...
            def headed(
                x: ArrayLike | None, state: Termination | NumericArrayLike
            ) -> None: ...

            @dataclass(frozen=True)
            class Ground:
                resistivity: Literal["G", "H"] | ArrayLike = "G"

            @dataclass(frozen=True, kw_only=True)
            class Built:
                resistivity: float | Literal["G", "H"] | NDArray[np.float64] = "G"

                if TYPE_CHECKING:

                    def __init__(
                        self, *, resistivity: Literal["G", "H"] | ArrayLike = "G"
                    ) -> None: ...

            def numeric(termination: Termination | NumericArrayLike) -> None: ...

            def paired(window: Termination | tuple[ArrayLike, ArrayLike]) -> None: ...

            def keyed(by_side: Mapping[Termination, ArrayLike]) -> None: ...

            def whole(fraction: Literal[1, 3] | ArrayLike) -> None: ...

            def dtyped(dtype: Literal["auto"] | DTypeLike = "auto") -> None: ...

            def spelt_text(name: Termination | LiteralString) -> None: ...

            def bound[T: str](state: Termination | T) -> None: ...

            def bound_inside[T: (str, bytes)](terms: Sequence[Termination | T]) -> None: ...

            def bound_items[T: str](labels: Literal["auto"] | Sequence[T]) -> None: ...

            def open_parameter[T](state: Termination | T) -> T: ...

            @dataclass(frozen=True)
            class Held[T: str]:
                resistivity: Literal["G", "H"] | T

            def bound_numbers[T: float](state: Termination | T) -> None: ...

            def _helper(termination: Termination | ArrayLike) -> None: ...
            """,
        },
    )
    assert sorted(refused) == [
        "Built.__init__(resistivity)",
        "Ground(resistivity)",
        "Held(resistivity)",
        "aliased(termination)",
        "banded(values)",
        "bound(state)",
        "bound_inside(terms)",
        "bound_items(labels)",
        "dtyped(dtype)",
        "headed(state)",
        "nested(terms)",
        "open_parameter(state)",
        "spelt_text(name)",
        "text(name)",
        "texts(labels)",
        "written(termination)",
    ]
    assert refused["written(termination)"] == [
        "sets Literal['rigid', 'free'] beside ArrayLike, which takes any text, so "
        "a misspelt choice type-checks as that alternative and only the call "
        "refuses it"
    ]
    assert refused["texts(labels)"][0].startswith(
        "sets Literal['auto'] beside Sequence[str]"
    )
    assert len(refused["headed(state)"]) == 1


def test_the_array_like_of_numbers_is_read_as_one(tmp_path: pathlib.Path) -> None:
    """The package's array-like of numbers converts, as ``ArrayLike`` does.

    A parameter handed to a helper that takes it ends its route there, a
    record whose constructor takes it for a converted field says what that
    constructor takes, and the live package names the two classes the alias
    is made of, so renaming one or the alias cannot silently turn it off.
    """
    root = _package(
        tmp_path,
        **{
            "_internal.types": _NUMERIC_TYPES,
            "api": """
            from dataclasses import dataclass
            from typing import Literal

            from ._internal.types import NumericArrayLike

            __all__ = ["level", "Ground"]

            def _state(state: Literal["zero"] | NumericArrayLike) -> float:
                return 0.0 if isinstance(state, str) else float(np.sum(state))

            def level(state: list[float]) -> float:
                return _state(state)

            @dataclass(frozen=True, kw_only=True)
            class Ground:
                resistivity: float | Literal["G"] | NDArray[np.float64] = "G"

                if TYPE_CHECKING:

                    def __init__(
                        self, *, resistivity: Literal["G"] | NumericArrayLike = "G"
                    ) -> None: ...

                def __post_init__(self) -> None:
                    if not isinstance(self.resistivity, str):
                        held = np.asarray(self.resistivity, dtype=np.float64)
                        object.__setattr__(self, "resistivity", held)
            """,
        },
    )
    package = overloads.Package(sorted(root.rglob("*.py")), root)
    reader = cpa.Reader(package, frozenset())
    assert reader.annotations.numeric == {
        "pkg._internal.types.NestedSequence",
        "pkg._internal.types.SupportsNumericArray",
    }
    findings = cpa.findings_in(sorted(root.rglob("*.py")), root, handed_on=frozenset())
    assert {(f.function, f.parameter) for f in findings} == {("level", "state")}
    assert any(
        "handed to _state(state: NumericArrayLike) converts" in f.problem
        for f in findings
    ), [f.problem for f in findings]
    assert cpa.constructor_problems(reader, "pkg.api.Ground") == []
    live = cpa.Reader(
        overloads.Package(ast_scan.python_files([], cpa.SOURCE), cpa.SOURCE)
    )
    assert live.annotations.numeric == {
        "phonometry._internal.types.NestedSequence",
        "phonometry._internal.types.SupportsNumericArray",
    }
