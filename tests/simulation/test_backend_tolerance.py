#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tolerance the guide publishes for each backend holds on every scenario.

The bound is the largest relative difference from the NumPy float64 run,
``max|a - b| / max|b|``, over every number each scenario records: the
fields, the snapshot frames, the energy, the collocated velocities and the
contour phasors (the modulus of the complex difference over the largest
modulus). A derived reduction carries a tolerance like a field does. The
numbers in ``backend_tolerance.json`` are what the guide quotes; a backend
that drifts past its number fails here, and the number is raised only with a
new measurement and the guide changed with it. A backend with no number yet
fails too, and says what it measured. A difference that is not finite, or a
reference with nothing to scale by, fails naming its scenario and key. Every
run prints its worst number and where it fell, so a CI log keeps it.
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

_HERE = pathlib.Path(__file__).resolve().parent
_SCRIPTS = str(_HERE.parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import engine_scenarios as es

from phonometry.simulation import Compute, elastic_fdtd, fdtd

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from phonometry.simulation.compute import Device, Dtype

_RECORD: dict[str, dict[str, object]] = json.loads(
    (_HERE / "backend_tolerance.json").read_text(encoding="utf-8")
)


def _relative(where: str, got: NDArray[np.generic], want: NDArray[np.generic]) -> float:
    """``max|got - want| / max|want|``, in the reference's precision.

    A NaN or an infinity in *got* comes back as a non-finite difference,
    which :func:`_worst_of` refuses.

    :param where: ``"<scenario>/<key>"``, named by a failure.
    """
    scale = float(np.abs(want).max())
    if not math.isfinite(scale):
        pytest.fail(f"{where}: the NumPy float64 reference is not finite")
    if scale <= 0.0:
        pytest.fail(
            f"{where}: the NumPy float64 reference is all zero, so a relative "
            "difference has nothing to scale by"
        )
    return float(np.abs(got.astype(want.dtype) - want).max()) / scale


def _measure(compute: Compute) -> dict[str, float]:
    """The relative difference from NumPy float64 of every recorded number.

    :return: ``{"<scenario>/<key>": difference}``, one entry per key
        ``engine_scenarios.run`` returns for each scenario.
    """
    measured: dict[str, float] = {}
    for scenario in es.SCENARIOS:
        module = fdtd if scenario.kind == "acoustic" else elastic_fdtd
        want = es.run(scenario, module)
        got = es.run(scenario, module, compute=compute)
        assert got.keys() == want.keys(), scenario.name
        for key, reference in want.items():
            where = f"{scenario.name}/{key}"
            measured[where] = _relative(where, got[key], reference)
    return measured


def _worst_of(measured: dict[str, float]) -> tuple[str, float]:
    """The ``(scenario/key, difference)`` with the largest difference.

    Every difference has to be finite first: a NaN compares false with
    everything, so a plain ``max`` keeps whatever came before it.
    """
    broken = [where for where, value in measured.items() if not math.isfinite(value)]
    if broken:
        pytest.fail(f"non-finite difference from NumPy at {', '.join(broken)}")
    where = max(measured, key=measured.__getitem__)
    return where, measured[where]


def _worst(compute: Compute) -> tuple[str, float]:
    """The largest of :func:`_measure` and where it fell, what the record bounds."""
    return _worst_of(_measure(compute))


def _hold(backend: str, where: str, worst: float) -> None:
    """Fail unless *worst* is within the tolerance the record publishes for *backend*.

    The measurement is printed either way, so a run that passes still
    leaves its number in the log (``pytest -rP``).
    """
    bound = _RECORD[backend]["max_relative"]
    measured = f"measured {worst!r} at {where}"
    if bound is None:
        pytest.fail(f"no published tolerance for {backend}; {measured}")
    if isinstance(bound, bool) or not isinstance(bound, int | float):
        pytest.fail(f"{backend}: the published tolerance {bound!r} is not a number")
    print(f"{backend}: {measured}, published {bound!r}")
    assert worst <= bound, f"{backend}: {measured}, published {bound!r}"


_BACKENDS: list[tuple[Device, Dtype]] = [
    # NumPy itself in float32: no optional library, so it runs on every runner.
    ("cpu", "float32"),
    ("torch:cpu", "float64"),
    ("torch:cpu", "float32"),
    ("torch:mps", "float32"),
]


@pytest.mark.parametrize(("device", "dtype"), _BACKENDS)
def test_each_backend_stays_within_its_published_tolerance(
    device: Device, dtype: Dtype
) -> None:
    if device.startswith("torch:"):
        torch = pytest.importorskip("torch")
        pytest.importorskip("array_api_compat")
        if device == "torch:mps" and not torch.backends.mps.is_available():
            pytest.skip("no MPS device here")
    _hold(f"{device}/{dtype}", *_worst(Compute(device=device, dtype=dtype)))


def test_the_record_publishes_one_entry_per_backend_tested() -> None:
    assert set(_RECORD) == {f"{device}/{dtype}" for device, dtype in _BACKENDS}


def test_the_record_describes_the_matrix_it_was_measured_over() -> None:
    """The scenario count, grids and steps an entry states are the matrix's own."""
    shapes = [
        scenario.build(
            fdtd if scenario.kind == "acoustic" else elastic_fdtd, {}
        ).p.shape
        for scenario in es.SCENARIOS
    ]
    cells = [rows * columns for rows, columns in shapes]
    steps = [scenario.steps for scenario in es.SCENARIOS]
    described = [entry for entry in _RECORD.values() if "scenarios" in entry]
    assert described
    for entry in described:
        assert entry["scenarios"] == len(es.SCENARIOS)
        assert entry["steps"] == f"{min(steps)} to {max(steps)}"
        grids = re.fullmatch(
            r"(\d+) by (\d+) to (\d+) by (\d+) cells", str(entry["grids"])
        )
        assert grids is not None, entry["grids"]
        low, high = (
            (int(grids[1]), int(grids[2])),
            (int(grids[3]), int(grids[4])),
        )
        assert low in shapes, entry["grids"]
        assert high in shapes, entry["grids"]
        assert (low[0] * low[1], high[0] * high[1]) == (min(cells), max(cells))


# The helpers on their own, with no backend: these run on every runner.


def test_a_non_finite_difference_fails_naming_its_key() -> None:
    """A NaN after a finite value is not lost the way ``max`` would lose it."""
    with pytest.raises(
        pytest.fail.Exception, match=re.escape("non-finite difference from NumPy at b")
    ):
        _worst_of({"a": 1e-7, "b": math.nan})


def test_a_nan_in_the_backend_run_is_a_non_finite_difference() -> None:
    got = np.array([1.0, math.nan])
    assert math.isnan(_relative("s/p", got, np.array([1.0, 2.0])))


def test_an_all_zero_reference_fails_naming_its_key() -> None:
    with pytest.raises(
        pytest.fail.Exception,
        match=re.escape("s/p: the NumPy float64 reference is all zero"),
    ):
        _relative("s/p", np.zeros(3), np.zeros(3))


def test_a_non_finite_reference_fails_naming_its_key() -> None:
    with pytest.raises(
        pytest.fail.Exception,
        match=re.escape("s/p: the NumPy float64 reference is not finite"),
    ):
        _relative("s/p", np.zeros(2), np.array([1.0, math.inf]))


def test_the_worst_difference_is_named_by_its_key() -> None:
    assert _worst_of({"a": 1e-7, "b": 3e-7, "c": 2e-7}) == ("b", 3e-7)


def test_a_backend_without_a_published_tolerance_fails_with_its_measurement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A null in the record is a failure that names the number to write there."""
    monkeypatch.setitem(_RECORD, "torch:cpu/float32", {"max_relative": None})
    with pytest.raises(
        pytest.fail.Exception,
        match=re.escape(
            "no published tolerance for torch:cpu/float32; measured 3e-07 at s/p"
        ),
    ):
        _hold("torch:cpu/float32", "s/p", 3e-07)


def test_a_measurement_past_the_published_tolerance_fails_naming_its_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``capsys`` keeps the made-up numbers out of a CI log read for real ones."""
    monkeypatch.setitem(_RECORD, "torch:cpu/float32", {"max_relative": 4e-07})
    _hold("torch:cpu/float32", "s/p", 4e-07)
    with pytest.raises(
        AssertionError, match=re.escape("measured 5e-07 at s/vy, published 4e-07")
    ):
        _hold("torch:cpu/float32", "s/vy", 5e-07)
    assert "at s/vy" in capsys.readouterr().out


def test_a_passing_measurement_is_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(_RECORD, "torch:cpu/float32", {"max_relative": 4e-07})
    _hold("torch:cpu/float32", "s/p", 1e-07)
    assert capsys.readouterr().out == (
        "torch:cpu/float32: measured 1e-07 at s/p, published 4e-07\n"
    )


def test_an_integer_bound_is_a_number(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON writes an exact zero as ``0``; it bounds like ``0.0``."""
    monkeypatch.setitem(_RECORD, "torch:cpu/float64", {"max_relative": 0})
    _hold("torch:cpu/float64", "s/p", 0.0)
    with pytest.raises(AssertionError, match="published 0"):
        _hold("torch:cpu/float64", "s/p", 1e-20)
    assert "published 0\n" in capsys.readouterr().out


def test_a_bound_that_is_not_a_number_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(_RECORD, "torch:cpu/float64", {"max_relative": "1e-15"})
    with pytest.raises(pytest.fail.Exception, match="'1e-15' is not a number"):
        _hold("torch:cpu/float64", "s/p", 0.0)
