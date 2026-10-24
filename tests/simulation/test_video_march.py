#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The engine of a run, and the march a video writer steps it through."""

from __future__ import annotations

from typing import Any

import numpy as np

from phonometry.simulation import (
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    _observer,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation import elastic_fdtd as ef
from phonometry.simulation import fdtd as fd

_PULSE = GaussianPulse(ix=0, iy=0, half_width_s=4e-5)


def _acoustic_run(**changes: Any) -> FDTDRun:
    arguments: dict[str, Any] = {
        "sources": [GaussianPulse(ix=15, iy=10, half_width_s=4e-5)],
        "shape": (20, 30),
        "recording": FDTDRecording(
            probes=[(3, 3), (25, 15)], snapshot_every=4, snapshot_decimation=2
        ),
    }
    arguments.update(changes)
    return FDTDRun(c=343.0, dx=0.01, duration_s=1e-3, **arguments)


def _elastic_run(**changes: Any) -> ElasticRun:
    arguments: dict[str, Any] = {
        "sources": [ExplosionSource(ix=10, iy=8, waveform=_PULSE.value)],
        "rho": 2500.0,
        "shape": (16, 20),
        "recording": ElasticRecording(
            probes=[(5, 5), (0, 15)],
            probe_fields=("p", "vx", "vy"),
            snapshot_every=3,
            snapshot_field="vx",
            snapshot_decimation=2,
        ),
    }
    arguments.update(changes)
    return ElasticRun(c_p=4000.0, c_s=2300.0, dx=0.01, duration_s=1e-3, **arguments)


def test_a_march_without_frames_records_what_the_simulation_records() -> None:
    run = _acoustic_run(
        boundaries=FDTDBoundaries(
            sides={"top": "absorbing", "left": 900.0}, absorbing_layer_cells=6
        ),
        damping=20.0,
    )
    checks = run._checked
    sim = fd._acoustic_engine(run, None)
    reference = fdtd_simulation(run)
    pressures = np.zeros((checks.probe_ix.shape[0], checks.steps + 1))
    assert list(fd._march(sim, checks.steps, checks.probe_ix, None, 1, pressures)) == []
    assert sim.dt == reference.dt
    assert np.array_equal(pressures, reference.pressures)


def test_the_march_yields_every_frame_and_finishes_on_exhaustion() -> None:
    run = _acoustic_run()
    checks = run._checked
    sim = fd._acoustic_engine(run, None)
    pressures = np.zeros((checks.probe_ix.shape[0], checks.steps + 1))
    frames = fd._march(
        sim,
        checks.steps,
        checks.probe_ix,
        checks.snapshot_every,
        checks.snapshot_decimation,
        pressures,
    )
    taken = [np.array(field, copy=True) for field in frames]
    assert len(taken) == checks.steps // 4 + 1
    assert taken[0].shape == (10, 15)
    assert sim.n == checks.steps
    reference = fdtd_simulation(run)
    assert np.array_equal(pressures, reference.pressures)
    assert np.array_equal(np.stack(taken), reference.snapshots)


def test_the_march_reports_every_step() -> None:
    run = _acoustic_run()
    checks = run._checked
    seen: list[tuple[int, int]] = []
    with _observer.observing(lambda done, total: seen.append((done, total))):
        frames = fd._march(
            fd._acoustic_engine(run, None),
            checks.steps,
            checks.probe_ix,
            checks.snapshot_every,
            checks.snapshot_decimation,
            np.zeros((checks.probe_ix.shape[0], checks.steps + 1)),
        )
        for _ in frames:
            pass
    assert seen == [(k, checks.steps) for k in range(1, checks.steps + 1)]


def test_the_elastic_march_yields_the_frames_the_simulation_records() -> None:
    run = _elastic_run()
    checks = run._checked
    sim = ef._elastic_engine(run, None)
    signals = np.zeros((checks.probe_ix.shape[0], len(checks.fields), checks.steps + 1))
    frames = ef._elastic_march(
        sim,
        checks.steps,
        checks.probe_ix,
        checks.fields,
        checks.snapshot_every,
        checks.snapshot_field,
        checks.snapshot_decimation,
        signals,
    )
    taken = np.stack([np.array(field, copy=True) for field in frames])
    assert taken.shape == (checks.steps // 3 + 1, 8, 10)
    assert sim.n == checks.steps
    reference = elastic_fdtd_simulation(run)
    assert reference.snapshots is not None
    assert taken.dtype == reference.snapshots.dtype
    assert np.array_equal(taken, reference.snapshots)
    assert np.array_equal(signals, reference.signals)
