#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The elastic engine on a backend other than NumPy."""

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import engine_scenarios as es

from phonometry.simulation import (
    WATER,
    Compute,
    CWSource,
    ElasticFDTD2D,
    ElasticFDTDResult,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDResult,
    FDTDRun,
    elastic_fdtd,
    elastic_fdtd_simulation,
    fdtd_simulation,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from phonometry.simulation.elastic_fdtd import Field

_ELASTIC = [s for s in es.SCENARIOS if s.kind == "elastic"]


@pytest.mark.parametrize("scenario", _ELASTIC, ids=lambda s: s.name)
def test_every_elastic_scenario_runs_on_the_strict_backend(
    on_strict: None, scenario: es.Scenario
) -> None:
    assert scenario.build(elastic_fdtd, {}).provenance.array_library.startswith(
        "array-api-strict"
    )
    got = es.run(scenario, elastic_fdtd)
    for key, value in got.items():
        assert np.all(np.isfinite(value)), key


@pytest.mark.parametrize("scenario", _ELASTIC, ids=lambda s: s.name)
def test_the_strict_backend_agrees_with_numpy(
    go_strict: Callable[[], None], scenario: es.Scenario
) -> None:
    want = es.run(scenario, elastic_fdtd)
    go_strict()
    got = es.run(scenario, elastic_fdtd)
    assert got.keys() == want.keys()
    for key in want:
        assert got[key].dtype == want[key].dtype, key
        assert np.array_equal(got[key], want[key]), key


def _pulse(t: float) -> float:
    return float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))


def _layered_run(snapshot_field: Field, snapshot_every: int) -> ElasticFDTDResult:
    """Water over a solid, probed on every edge and corner and inside."""
    ny, nx = 18, 22
    c_p = np.full((ny, nx), 1480.0)
    c_s = np.zeros((ny, nx))
    rho = np.full((ny, nx), 1000.0)
    c_p[9:, :], c_s[9:, :], rho[9:, :] = 4000.0, 2300.0, 2500.0
    probes = [(0, 0), (nx - 1, 0), (0, ny - 1), (nx - 1, ny - 1), (7, 4), (11, 12)]
    return elastic_fdtd_simulation(
        ElasticRun(
            c_p,
            c_s,
            0.01,
            1e-4,
            sources=[ExplosionSource(ix=10, iy=6, waveform=_pulse)],
            rho=rho,
            recording=ElasticRecording(
                probes=probes,
                probe_fields=("p", "vx", "vy"),
                snapshot_every=snapshot_every,
                snapshot_field=snapshot_field,
            ),
        )
    )


def test_a_recorded_elastic_run_agrees_with_numpy(
    go_strict: Callable[[], None],
) -> None:
    want = _layered_run("p", 5)
    go_strict()
    got = _layered_run("p", 5)
    assert want.snapshots is not None
    assert got.snapshots is not None
    # Every probe records every field, the edge ones included, so each
    # clamped index and each edge mask is read with the wave on it.
    assert np.all(np.abs(want.signals).max(axis=2) > 0.0)
    assert np.array_equal(got.signals, want.signals)
    assert np.array_equal(got.snapshots, want.snapshots)


@pytest.mark.parametrize("backend", ["numpy", "strict"])
@pytest.mark.parametrize("field", ["p", "vx", "vy"])
def test_each_probe_reads_its_cell_of_the_collocated_field(
    go_strict: Callable[[], None], backend: str, field: Field
) -> None:
    """Each probe's trace is its cell of the snapshots, bit for bit.

    The probes gather through flat indices and edge masks, and the collocated
    field is built by slicing; both average the same faces in the same order.
    The frozen copies have no recorder, so the recorder is held to them by
    composition: the frozen parity pins the fields, and this pins the probes
    to the fields.
    """
    if backend == "strict":
        go_strict()
    res = _layered_run(field, 1)
    assert res.snapshots is not None
    j = res.probe_fields.index(field)
    for k, (ix, iy) in enumerate(res.probes):
        assert np.array_equal(res.signals[k, j], res.snapshots[:, iy, ix]), (ix, iy)


def test_a_recorded_acoustic_run_agrees_with_numpy(
    go_strict: Callable[[], None],
) -> None:
    """The acoustic probes take a flat-index gather too.

    Each probe's trace is its cell of the snapshots, and the strict backend
    records what NumPy does.
    """

    def simulate() -> FDTDResult:
        return fdtd_simulation(
            FDTDRun(
                343.0,
                0.01,
                1e-3,
                shape=(16, 20),
                sources=[CWSource(ix=6, iy=7, frequency=2000.0)],
                recording=FDTDRecording(
                    probes=[(0, 0), (19, 15), (12, 3)], snapshot_every=1
                ),
            )
        )

    want = simulate()
    assert want.snapshots is not None
    assert np.all(np.abs(want.pressures).max(axis=1) > 0.0)
    for k, (ix, iy) in enumerate(want.probes):
        assert np.array_equal(want.pressures[k], want.snapshots[:, iy, ix]), (ix, iy)
    go_strict()
    got = simulate()
    assert got.snapshots is not None
    assert np.array_equal(got.pressures, want.pressures)
    assert np.array_equal(got.snapshots, want.snapshots)


def test_a_stress_written_from_outside_is_stepped(on_strict: None) -> None:
    sim = ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(20, 20))
    sim.txx[10, 4:8] -= 1.0
    sim.step()
    assert np.abs(sim.host_field("vx")).max() > 0.0


def test_from_regions_takes_the_placement() -> None:
    sim = ElasticFDTD2D.from_regions(
        (12, 12), 0.01, background=WATER, compute=Compute(dtype="float32")
    )
    assert sim.provenance.dtype == "float32"
    assert sim.txx.dtype == np.float32


def test_host_field_reads_the_stresses_as_stored() -> None:
    sim = ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(10, 12))
    assert sim.host_field("txy").shape == (9, 11)
    with pytest.raises(ValueError, match="'name' must be one of"):
        sim.host_field("p")  # type: ignore[arg-type]


def test_the_lame_maps_are_read_only_host_copies() -> None:
    sim = ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(10, 12))
    for name in ("mu", "lam"):
        with pytest.raises(ValueError, match="read-only"):
            getattr(sim, name)[0, 0] = 1.0
