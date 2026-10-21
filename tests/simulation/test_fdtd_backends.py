#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The acoustic engine on a backend other than NumPy."""

from __future__ import annotations

import dataclasses
import pathlib
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import engine_scenarios as es

from phonometry.simulation import FDTD2D, Compute, GaussianPulse, fdtd
from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import NDArray


@pytest.mark.parametrize(
    "scenario",
    [s for s in es.SCENARIOS if s.kind == "acoustic"],
    ids=lambda s: s.name,
)
def test_every_acoustic_scenario_runs_on_the_strict_backend(
    on_strict: None, scenario: es.Scenario
) -> None:
    got = es.run(scenario, fdtd)
    for key, value in got.items():
        assert np.all(np.isfinite(value)), key


def test_the_strict_guard_refuses_a_numpy_call_on_a_device_array(
    on_strict: None,
) -> None:
    sim = FDTD2D(343.0, 0.01, shape=(8, 8))
    with pytest.raises(TypeError, match="through __array__ or the buffer protocol"):
        np.concatenate((sim.p, sim.p))


_CONTOUR_KEYS = tuple(f"contour0_{f}_{q}" for f in ("3000", "1500") for q in ("p", "v"))


@pytest.mark.parametrize(
    ("name", "keys"),
    [
        ("sponge", ("p", "vx", "vy", "frames")),
        ("contour", ("p", "vx", "vy", *_CONTOUR_KEYS)),
    ],
    ids=["sponge", "contour"],
)
def test_the_strict_backend_agrees_with_numpy(
    go_strict: Callable[[], None], name: str, keys: tuple[str, ...]
) -> None:
    scenario = next(s for s in es.SCENARIOS if s.name == name)
    want = es.run(scenario, fdtd)
    go_strict()
    got = es.run(scenario, fdtd)
    for key in keys:
        assert got[key].dtype == want[key].dtype, key
        assert np.array_equal(got[key], want[key]), key


#: Steps of the float32 contour check: long enough that float32 sums drift
#: (9.1e-7 at the source frequency, measured) while float64 sums, and float32
#: sums with Neumaier's compensation, stay at the float32 field's own
#: rounding (4.5e-8, measured).
_FLOAT32_STEPS = 3000
#: Four times that floor, so a runner that rounds differently still passes,
#: and four and a half times under the drift of uncompensated float32 sums.
_FLOAT32_BOUND = 2e-7


def _source_phasors(
    **engine_kwargs: object,
) -> tuple[fdtd.ContourProbe, NDArray[np.complex128], NDArray[np.complex128]]:
    """The contour scenario's 3000 Hz (source) phasors after the check's steps."""
    scenario = next(s for s in es.SCENARIOS if s.name == "contour")
    sim = scenario.build(fdtd, engine_kwargs)
    sim.run(_FLOAT32_STEPS)
    probe = sim._contour_probes[0]
    phasors = probe.phasors(3000.0)
    return probe, phasors.pressure, phasors.normal_velocity


#: Where the float32 contour check runs: NumPy and the conformance backend,
#: each with float64 sums and with the float32 sums of MPS forced on them,
#: and MPS itself, where a compiler that reassociated ``(s - t) + term``
#: would lose the compensation.
_CONTOUR_RUNS = {
    "numpy-float64-sums": ("numpy", "float64"),
    "numpy-mps-like-float32-sums": ("numpy", "float32"),
    "strict-float64-sums": ("array-api-strict", "float64"),
    "strict-mps-like-float32-sums": ("array-api-strict", "float32"),
    "torch:mps-float32-sums": ("torch:mps", "float32"),
}


def _float32_request(
    monkeypatch: pytest.MonkeyPatch,
    go_strict: Callable[[], None],
    backend: str,
    sums: str,
) -> Compute:
    """The float32 request of one contour run, with its backend in place."""
    if backend == "torch:mps":
        torch = pytest.importorskip("torch")
        pytest.importorskip("array_api_compat")
        if not torch.backends.mps.is_available():
            pytest.skip("no MPS device here")
        return Compute(device="torch:mps", dtype="float32")
    if backend == "array-api-strict":
        # The float32 fields times the float64 phases, and the compensated
        # sums, on the conformance backend.
        go_strict()
    if sums == "float32":
        # The float32 sums of torch:mps, to reach the compensated path on a
        # machine without MPS.
        loader = bk.LOADERS["cpu"]
        monkeypatch.setitem(
            bk.LOADERS,
            "cpu",
            lambda c: dataclasses.replace(loader(c), accumulator_dtype="float32"),
        )
    return Compute(dtype="float32")


@pytest.mark.parametrize("run", sorted(_CONTOUR_RUNS))
def test_a_float32_run_gives_the_float64_contour_phasors(
    monkeypatch: pytest.MonkeyPatch,
    go_strict: Callable[[], None],
    run: str,
) -> None:
    backend, sums = _CONTOUR_RUNS[run]
    _, *want = _source_phasors()
    request = _float32_request(monkeypatch, go_strict, backend, sums)
    probe, *got = _source_phasors(compute=request)
    assert probe._backend.name == backend
    assert (probe._carry is not None) == (sums == "float32")
    for g, w in zip(got, want, strict=True):
        assert g.dtype == np.complex128
        assert np.linalg.norm(g - w) / np.linalg.norm(w) < _FLOAT32_BOUND


@pytest.mark.parametrize(
    "sums", ["float64", "float32"], ids=["sums", "compensated-sums"]
)
def test_a_contour_probe_resets_on_the_strict_backend(
    monkeypatch: pytest.MonkeyPatch, on_strict: None, sums: str
) -> None:
    """``reset`` clears the sums, and the carry of compensated ones, on the device."""
    if sums == "float32":
        loader = bk.LOADERS["cpu"]
        monkeypatch.setitem(
            bk.LOADERS,
            "cpu",
            lambda c: dataclasses.replace(loader(c), accumulator_dtype="float32"),
        )
    sim = FDTD2D(343.0, 0.01, shape=(20, 20), compute=Compute(dtype="float32"))
    sim.add_source(GaussianPulse(ix=10, iy=10, half_width_s=4e-5))
    probe = sim.add_contour_probe(5, 14, 5, 14, frequencies=[1000.0])
    sim.run(20)
    backend = probe._backend
    assert backend.name == "array-api-strict"
    assert np.abs(backend.to_host(probe._sums)).max() > 0.0
    probe.reset()
    assert probe.samples == 0
    assert not backend.to_host(probe._sums).any()
    if probe._carry is not None:
        assert not backend.to_host(probe._carry).any()
    assert (probe._carry is not None) == (sums == "float32")


def test_a_write_into_the_field_from_outside_is_stepped(on_strict: None) -> None:
    sim = FDTD2D(343.0, 0.01, shape=(20, 20))
    ref = sim.p
    sim.p[10, 10] = 1.0
    sim.step()
    assert ref is sim.p
    assert np.abs(sim.host_field("p")).max() > 0.0


def test_host_field_is_a_copy_in_numpy() -> None:
    sim = FDTD2D(343.0, 0.01, shape=(8, 8))
    got = sim.host_field("vx")
    assert isinstance(got, np.ndarray)
    got[...] = 7.0
    assert float(np.abs(sim.host_field("vx")).max()) == 0.0


def test_host_field_refuses_a_field_it_does_not_store() -> None:
    sim = FDTD2D(343.0, 0.01, shape=(8, 8))
    with pytest.raises(ValueError, match="'name' must be one of"):
        sim.host_field("txx")  # type: ignore[arg-type]


def test_the_engine_records_where_it_ran() -> None:
    sim = FDTD2D(343.0, 0.01, shape=(8, 8), compute=Compute(dtype="float32"))
    assert sim.provenance.device == "cpu"
    assert sim.provenance.dtype == "float32"
    assert sim.p.dtype == np.float32


def test_run_takes_the_snapshot_names() -> None:
    sim = FDTD2D(343.0, 0.01, shape=(20, 21))
    sim.add_source(GaussianPulse(ix=5, iy=5, half_width_s=4e-5))
    frames = sim.run(12, snapshot_every=4, snapshot_decimation=4)
    assert frames.shape == (4, 5, 6)


def test_the_material_maps_are_read_only_host_copies() -> None:
    sim = FDTD2D(343.0, 0.01, shape=(8, 8))
    assert isinstance(sim.kappa, np.ndarray)
    with pytest.raises(ValueError, match="read-only"):
        sim.kappa[0, 0] = 1.0
