#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The simulation functions take a placement, decimate their snapshots and record where they ran."""

from __future__ import annotations

import re
import warnings
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    Compute,
    ComputeDeviceError,
    ComputeFallbackWarning,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    Material,
    PlaneWaveSource,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Callable

    from phonometry.simulation import ElasticFDTDResult, FDTDResult
    from phonometry.simulation.elastic_fdtd import Field


def _acoustic(recording: FDTDRecording | None = None, **kwargs: Any) -> FDTDResult:
    """A small acoustic run with one pulse, recorded as the test asks."""
    return fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-3,
            shape=(30, 41),
            sources=[GaussianPulse(ix=15, iy=15, half_width_s=4e-5)],
            recording=recording,
        ),
        **kwargs,
    )


def _pulse(t: float) -> float:
    return float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))


def _elastic(recording: ElasticRecording, **kwargs: Any) -> ElasticFDTDResult:
    """A small solid struck by an explosion, recorded as the test asks."""
    return elastic_fdtd_simulation(
        ElasticRun(
            c_p=4000.0,
            c_s=2300.0,
            dx=0.01,
            duration_s=1e-4,
            rho=2500.0,
            shape=(20, 21),
            sources=[ExplosionSource(ix=10, iy=9, waveform=_pulse)],
            recording=recording,
        ),
        **kwargs,
    )


def test_a_run_records_where_it_ran() -> None:
    res = fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-3,
            shape=(30, 30),
            sources=[GaussianPulse(ix=15, iy=15, half_width_s=4e-5)],
        )
    )
    assert res.provenance.device == "cpu"
    assert res.provenance.dtype == "float64"
    assert res.provenance.numpy_version == np.__version__
    assert res.snapshot_decimation == 1


def test_snapshots_are_decimated_and_checked_against_the_grid() -> None:
    res = _acoustic(FDTDRecording(snapshot_every=5, snapshot_decimation=4))
    assert res.snapshots is not None
    assert res.snapshots.shape[1:] == (8, 11)
    assert res.snapshot_decimation == 4


def test_a_decimated_snapshot_is_every_d_th_cell_of_the_full_one() -> None:
    full = _acoustic(FDTDRecording(snapshot_every=5))
    decimated = _acoustic(FDTDRecording(snapshot_every=5, snapshot_decimation=4))
    assert full.snapshots is not None
    assert decimated.snapshots is not None
    assert np.abs(full.snapshots[-1]).max() > 0.0
    assert np.array_equal(decimated.snapshots, full.snapshots[:, ::4, ::4])


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (0, ValueError),
        (-1, ValueError),
        (2.5, ValueError),
        (True, TypeError),
        ("4", TypeError),
    ],
)
def test_the_decimation_is_a_count_of_one_or_more(
    value: object, error: type[Exception]
) -> None:
    with pytest.raises(error, match="snapshot_decimation"):
        FDTDRecording(snapshot_every=5, snapshot_decimation=value)  # type: ignore[arg-type]


def test_a_result_refuses_snapshots_of_another_decimated_grid() -> None:
    res = _acoustic(FDTDRecording(snapshot_every=5, snapshot_decimation=4))
    assert res.snapshots is not None
    # The floor of 41 / 4 instead of its ceiling: one column short.
    floor = res.snapshots[:, :, :10]
    with pytest.raises(ValueError, match="decimated grid column"):
        replace(res, snapshots=floor)
    with pytest.raises(ValueError, match="decimated grid row"):
        replace(res, snapshot_decimation=3)
    with pytest.raises(ValueError, match="snapshot_decimation"):
        replace(res, snapshot_decimation=0)


@pytest.mark.parametrize("value", [4.0, np.int64(4)], ids=["float", "numpy integer"])
def test_a_result_holds_its_decimation_as_an_int(value: object) -> None:
    res = _acoustic(FDTDRecording(snapshot_every=5, snapshot_decimation=4))
    rebuilt = replace(res, snapshot_decimation=value)
    assert type(rebuilt.snapshot_decimation) is int
    assert rebuilt.snapshot_decimation == 4


def _run_route(every: object, decimation: object) -> object:
    return FDTD2D(343.0, 0.01, shape=(8, 8)).run(
        4,
        snapshot_every=every,  # type: ignore[arg-type]
        snapshot_decimation=decimation,  # type: ignore[arg-type]
    )


def _elastic_run_route(every: object, decimation: object) -> object:
    return ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(8, 8)).run(
        4,
        snapshot_every=every,  # type: ignore[arg-type]
        snapshot_decimation=decimation,  # type: ignore[arg-type]
    )


def _function_route(every: object, decimation: object) -> object:
    recording = FDTDRecording(
        snapshot_every=every,  # type: ignore[arg-type]
        snapshot_decimation=decimation,  # type: ignore[arg-type]
    )
    return fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-4,
            shape=(8, 8),
            sources=[GaussianPulse(ix=4, iy=4, half_width_s=4e-5)],
            recording=recording,
        )
    )


def _elastic_function_route(every: object, decimation: object) -> object:
    recording = ElasticRecording(
        snapshot_every=every,  # type: ignore[arg-type]
        snapshot_decimation=decimation,  # type: ignore[arg-type]
    )
    return elastic_fdtd_simulation(
        ElasticRun(
            c_p=4000.0,
            c_s=2300.0,
            dx=0.01,
            duration_s=1e-5,
            rho=2500.0,
            shape=(8, 8),
            sources=[ExplosionSource(ix=4, iy=4, waveform=_pulse)],
            recording=recording,
        )
    )


#: Every way to ask for snapshots, each handed the cadence and the decimation.
_SNAPSHOT_ROUTES: dict[str, Callable[[object, object], object]] = {
    "FDTD2D.run": _run_route,
    "ElasticFDTD2D.run": _elastic_run_route,
    "fdtd_simulation": _function_route,
    "elastic_fdtd_simulation": _elastic_function_route,
}

#: What every route says to each bad count, ``{name}`` the option it went to.
_SNAPSHOT_REFUSALS: dict[str, tuple[type[Exception], str]] = {
    "flag": (TypeError, "'{name}' must be a whole number, got True."),
    "fraction": (ValueError, "'{name}' must be a whole number, at least 1, got 2.5."),
    "zero": (ValueError, "'{name}' must be a whole number, at least 1, got 0."),
    "negative": (ValueError, "'{name}' must be a whole number, at least 1, got -1."),
    "text": (TypeError, "'{name}' must be one number, not a text."),
}
_BAD_COUNTS: dict[str, object] = {
    "flag": True,
    "fraction": 2.5,
    "zero": 0,
    "negative": -1,
    "text": "4",
}


@pytest.mark.parametrize("route", sorted(_SNAPSHOT_ROUTES))
@pytest.mark.parametrize("option", ["snapshot_every", "snapshot_decimation"])
@pytest.mark.parametrize("bad", sorted(_BAD_COUNTS))
def test_a_bad_snapshot_count_is_refused_alike_on_every_route(
    route: str, option: str, bad: str
) -> None:
    """The engines' ``run()`` and the two recordings share one check."""
    counts: dict[str, object] = {"snapshot_every": 2, "snapshot_decimation": 1}
    counts[option] = _BAD_COUNTS[bad]
    error, message = _SNAPSHOT_REFUSALS[bad]
    ask = _SNAPSHOT_ROUTES[route]
    every, decimation = counts["snapshot_every"], counts["snapshot_decimation"]
    with pytest.raises(error, match=re.escape(message.format(name=option))):
        ask(every, decimation)


def test_a_float32_run_keeps_float32_snapshots() -> None:
    res = fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=5e-4,
            shape=(20, 20),
            sources=[GaussianPulse(ix=10, iy=10, half_width_s=4e-5)],
            recording=FDTDRecording(probes=[(4, 4)], snapshot_every=5),
        ),
        compute=Compute(dtype="float32"),
    )
    assert res.snapshots is not None
    assert res.snapshots.dtype == np.float32
    assert res.pressures.dtype == np.float64
    assert res.provenance.dtype == "float32"


def test_a_plane_wave_runs_through_the_function() -> None:
    pulse = GaussianPulse(ix=0, iy=0, half_width_s=5e-5)
    res = fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=1e-3,
            shape=(40, 30),
            boundaries=FDTDBoundaries(sides="absorbing", absorbing_layer_cells=8),
            sources=[
                PlaneWaveSource(direction="down", waveform=pulse.value, offset=10)
            ],
            recording=FDTDRecording(probes=[(15, 30)]),
        )
    )
    assert np.abs(res.pressures).max() > 0.0
    assert isinstance(res.sources[0], PlaneWaveSource)


def test_a_plane_wave_run_draws_its_snapshot_with_the_point_sources_only() -> None:
    import matplotlib.pyplot as plt

    pulse = GaussianPulse(ix=5, iy=30, half_width_s=5e-5)
    res = fdtd_simulation(
        FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=5e-4,
            shape=(40, 30),
            sources=[PlaneWaveSource(direction="down", waveform=pulse.value), pulse],
            recording=FDTDRecording(snapshot_every=10),
        )
    )
    ax = res.plot(kind="snapshot")
    stars = [line for line in ax.lines if line.get_marker() == "*"]
    assert [(line.get_xdata()[0], line.get_ydata()[0]) for line in stars] == [
        pytest.approx((0.055, 0.305))
    ]
    plt.close(ax.figure)


def test_fallback_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent(_c: Compute) -> bk.Backend:
        msg = "no CUDA device"
        raise ComputeDeviceError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = fdtd_simulation(
            FDTDRun(
                c=343.0,
                dx=0.01,
                duration_s=5e-4,
                shape=(16, 16),
                sources=[GaussianPulse(ix=8, iy=8, half_width_s=4e-5)],
            ),
            compute=Compute(device="cupy", fallback=True),
        )
    assert [w.category for w in caught] == [ComputeFallbackWarning]
    assert res.provenance.device == "cpu"


def test_the_elastic_recording_decimates() -> None:
    res = _elastic(ElasticRecording(snapshot_every=4, snapshot_decimation=5))
    assert res.snapshots is not None
    assert res.snapshots.shape[1:] == (4, 5)
    assert res.snapshot_decimation == 5
    assert res.provenance.device == "cpu"


@pytest.mark.parametrize("field", ["p", "vx", "vy"])
def test_a_decimated_elastic_snapshot_is_every_d_th_cell_of_the_full_one(
    field: Field,
) -> None:
    full = _elastic(ElasticRecording(snapshot_every=4, snapshot_field=field))
    decimated = _elastic(
        ElasticRecording(snapshot_every=4, snapshot_field=field, snapshot_decimation=3)
    )
    assert full.snapshots is not None
    assert decimated.snapshots is not None
    assert np.abs(full.snapshots[-1]).max() > 0.0
    assert np.array_equal(decimated.snapshots, full.snapshots[:, ::3, ::3])


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (0, ValueError),
        (-1, ValueError),
        (2.5, ValueError),
        (True, TypeError),
        ("5", TypeError),
    ],
)
def test_the_elastic_decimation_is_a_count_of_one_or_more(
    value: object, error: type[Exception]
) -> None:
    with pytest.raises(error, match="snapshot_decimation"):
        ElasticRecording(snapshot_every=4, snapshot_decimation=value)  # type: ignore[arg-type]


def test_an_elastic_result_holds_its_decimation_as_an_int() -> None:
    res = _elastic(ElasticRecording(snapshot_every=4, snapshot_decimation=5))
    rebuilt = replace(res, snapshot_decimation=5.0)
    assert type(rebuilt.snapshot_decimation) is int
    assert rebuilt.snapshot_decimation == 5


def test_an_elastic_run_takes_its_placement() -> None:
    res = _elastic(
        ElasticRecording(probes=[(4, 4)], snapshot_every=4),
        compute=Compute(dtype="float32"),
    )
    assert res.provenance.dtype == "float32"
    assert res.snapshots is not None
    assert res.snapshots.dtype == np.float32
    assert res.signals.dtype == np.float64


def test_a_decimated_run_on_the_strict_backend_agrees_with_numpy(
    go_strict: Callable[[], None],
) -> None:
    """The snapshot is sliced on the device and then copied, on every backend."""
    want = _acoustic(
        FDTDRecording(probes=[(3, 7)], snapshot_every=5, snapshot_decimation=4)
    )
    elastic_want = _elastic(ElasticRecording(snapshot_every=4, snapshot_decimation=3))
    go_strict()
    got = _acoustic(
        FDTDRecording(probes=[(3, 7)], snapshot_every=5, snapshot_decimation=4)
    )
    elastic_got = _elastic(ElasticRecording(snapshot_every=4, snapshot_decimation=3))
    assert got.provenance.array_library is not None
    assert got.provenance.array_library.startswith("array-api-strict")
    assert np.array_equal(got.pressures, want.pressures)
    assert got.snapshots is not None
    assert want.snapshots is not None
    assert np.array_equal(got.snapshots, want.snapshots)
    assert elastic_got.snapshots is not None
    assert elastic_want.snapshots is not None
    assert np.array_equal(elastic_got.snapshots, elastic_want.snapshots)


#: The record each simulation function takes.
_RECORDS: dict[str, type[FDTDRecording] | type[ElasticRecording]] = {
    "acoustic": FDTDRecording,
    "elastic": ElasticRecording,
}


def _run(kind: str, recording: object) -> object:
    """A small run of the *kind* engine, handed *recording* as it is."""
    if kind == "acoustic":
        return _acoustic(recording)  # type: ignore[arg-type]
    return _elastic(recording)  # type: ignore[arg-type]


@pytest.mark.parametrize("wrong", ["dict", "other record", "text"])
@pytest.mark.parametrize("kind", sorted(_RECORDS))
def test_a_simulation_takes_only_its_own_recording(kind: str, wrong: str) -> None:
    """The elastic record has the acoustic one's fields, and would run unread."""
    other = ElasticRecording() if kind == "acoustic" else FDTDRecording()
    recording = {"dict": {"probes": [(4, 4)]}, "other record": other, "text": "p"}[
        wrong
    ]
    message = (
        f"'recording' must be an {_RECORDS[kind].__name__} or None, "
        f"got {type(recording).__name__}."
    )
    with pytest.raises(TypeError, match=re.escape(message)):
        _run(kind, recording)


@pytest.mark.parametrize("kind", sorted(_RECORDS))
def test_a_recording_takes_any_iterable_of_probes_as_int_pairs(kind: str) -> None:
    probes = ((np.int64(i), 2.0 * i) for i in (1, 3))
    recording = _RECORDS[kind](probes=probes)  # type: ignore[arg-type]
    assert recording.probes == ((1, 2), (3, 6))
    assert all(type(i) is int for pair in recording.probes for i in pair)


@pytest.mark.parametrize(
    ("probes", "error", "entry"),
    [
        ([(1, 2), (1, 2, 3), 5], ValueError, "entry 1 is (1, 2, 3)"),
        ([(1, 2), 5, (1, 2, 3)], TypeError, "entry 1 is 5"),
    ],
    ids=["triple first", "bare index first"],
)
@pytest.mark.parametrize("kind", sorted(_RECORDS))
def test_a_recording_reports_its_first_malformed_probe(
    kind: str, probes: list[object], error: type[Exception], entry: str
) -> None:
    message = f"probes must hold (ix, iy) index pairs; {entry}"
    with pytest.raises(error, match=re.escape(message)):
        _RECORDS[kind](probes=probes)  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", sorted(_RECORDS))
def test_a_run_reports_its_first_probe_off_the_grid(kind: str) -> None:
    recording = _RECORDS[kind](probes=[(1, 1), (99, 0), (0, 99)])
    with pytest.raises(ValueError, match=re.escape("probe (99, 0) lies outside")):
        _run(kind, recording)


@pytest.mark.parametrize(
    "provenance", [None, "cpu", Compute()], ids=["none", "text", "request"]
)
@pytest.mark.parametrize("kind", ["acoustic", "elastic"])
def test_a_result_refuses_a_provenance_that_is_not_a_run_provenance(
    kind: str, provenance: object
) -> None:
    """A result that cannot say where it stepped could pass for any device's."""
    res = _acoustic() if kind == "acoustic" else _elastic(ElasticRecording())
    with pytest.raises(TypeError, match="'provenance' must be a RunProvenance"):
        replace(res, provenance=provenance)


# An engine steps in this process: it refuses a node, after its arguments.


def _acoustic_engine(**kwargs: Any) -> FDTD2D:
    return FDTD2D(343.0, 0.01, shape=(8, 8), **kwargs)


def _elastic_engine(**kwargs: Any) -> ElasticFDTD2D:
    return ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(8, 8), **kwargs)


def _elastic_from_regions(**kwargs: Any) -> ElasticFDTD2D:
    solid = Material(c_p=4000.0, c_s=2300.0, rho=2500.0)
    return ElasticFDTD2D.from_regions((8, 8), 0.01, background=solid, **kwargs)


@pytest.mark.parametrize(
    ("build", "owner"),
    [
        (_acoustic_engine, "FDTD2D"),
        (_elastic_engine, "ElasticFDTD2D"),
        (_elastic_from_regions, "ElasticFDTD2D"),
    ],
)
def test_an_engine_refuses_a_host_it_is_given(
    build: Callable[..., object], owner: str
) -> None:
    request = Compute(device="cupy", host="nas")
    with pytest.raises(
        ValueError, match=f"{owner} steps in this process and cannot run on a node"
    ):
        build(compute=request)


def test_an_engine_under_a_host_from_the_environment_asks_for_compute_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas")
    with pytest.raises(
        ValueError, match="PHONOMETRY_COMPUTE names host 'nas': pass compute="
    ):
        _acoustic_engine()


@pytest.mark.parametrize(
    ("build", "bad", "match"),
    [
        (_acoustic_engine, {"rho": -1.0}, "rho must be strictly positive"),
        (_acoustic_engine, {"sponge_width": 9}, "sponge_width must be narrower"),
        (_elastic_engine, {"free_sides": "middle"}, "unknown free sides"),
    ],
)
def test_an_engine_checks_its_arguments_before_it_refuses_the_host(
    build: Callable[..., object], bad: dict[str, object], match: str
) -> None:
    request = Compute(host="nas")
    with pytest.raises(ValueError, match=match):
        build(compute=request, **bad)
