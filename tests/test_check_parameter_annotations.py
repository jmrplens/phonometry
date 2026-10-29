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
sequence converted item by item), and what it must let through (a pair of
limits, a scalar validator, a private helper, a sequence whose items take a
sequence of numbers).
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


def _refused(tmp_path: pathlib.Path, **modules: str) -> dict[str, list[str]]:
    """The parameters refused, as ``function(parameter)``, with the reasons."""
    root = _package(tmp_path, **modules)
    found: dict[str, list[str]] = {}
    for finding in cpa.findings_in(sorted(root.rglob("*.py")), root):
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


def test_the_gpu_parity_files_are_those_the_lock_holds() -> None:
    import gpu_parity

    assert cpa.gpu_parity_files() == tuple(
        path.relative_to(ast_scan.ROOT).as_posix() for path in gpu_parity._COVERED
    )


def test_the_gpu_parity_files_are_held_back_in_a_copy_of_the_package(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(
        tmp_path,
        **{
            "simulation.fdtd": """
            __all__ = ["FDTD2D"]

            class FDTD2D:
                def __init__(self, c: float | np.ndarray) -> None:
                    self.c = np.asarray(c)
            """,
            "api": """
            __all__ = ["level"]

            def level(x: np.ndarray) -> float:
                return float(np.sum(np.asarray(x)))
            """,
        },
    )
    every = cpa.findings_in(sorted(root.rglob("*.py")), root)
    kept, held = cpa.held_for_gpu(every, cpa.gpu_parity_files())
    assert [finding.function for finding in kept] == ["level"]
    assert [finding.function for finding in held] == ["FDTD2D.__init__"]


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
    kept, _held = cpa.held_for_gpu(every, cpa.gpu_parity_files())
    found, stale = cpa.checked(kept, cpa.EXEMPT)
    assert not found, "\n".join(
        f"{f.path}:{f.line}: {f.function}({f.parameter}): {f.problem}" for f in found
    )
    assert not stale
