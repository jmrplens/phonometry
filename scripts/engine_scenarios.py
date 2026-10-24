#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The scenarios every FDTD backend is held to, one per engine feature.

Each scenario builds an engine from a module that provides ``FDTD2D`` or
``ElasticFDTD2D`` and their sources, steps it, and returns every stored field
as a host array. The same scenarios hold the NumPy path to its golden
digests (``scripts/engine_digests.py``), measure CuPy
(``scripts/gpu_parity.py``) and bound torch (the tolerance tests), so a
feature cannot be proven on one backend and skipped on another. Grids are
small: the point is every code path, not speed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from numpy.typing import NDArray

Kind = Literal["acoustic", "elastic"]
#: An engine built from ``fdtd`` or ``elastic_fdtd``. Each module has classes
#: of its own, so no one class or protocol names them both, and the attributes
#: a scenario reads are looked up when it runs.
Engine = Any

_ACOUSTIC_FIELDS = ("p", "vx", "vy")
_ELASTIC_FIELDS = ("txx", "tyy", "txy", "vx", "vy")


@dataclass(frozen=True)
class Scenario:
    """One engine feature, exercised on a small grid."""

    name: str
    kind: Kind
    build: Callable[[ModuleType, dict[str, Any]], Engine]
    steps: int = 60
    snapshot_every: int | None = None
    snapshot_decimation: int = 1


def _air(shape: tuple[int, int]) -> NDArray[np.float64]:
    ny, nx = shape
    c = np.full(shape, 343.0)
    c[ny // 3 : ny // 2, nx // 4 : nx // 2] = 520.0
    return c


def _sponge(m: ModuleType, kw: dict[str, Any]) -> Engine:
    sim = m.FDTD2D(_air((48, 64)), 0.01, absorbing_layer_cells=8, **kw)
    sim.add_source(m.GaussianPulse(ix=20, iy=24, half_width_s=4e-5))
    return sim


def _impedance(m: ModuleType, kw: dict[str, Any]) -> Engine:
    z = np.linspace(300.0, 900.0, 48)
    sim = m.FDTD2D(
        343.0, 0.01, shape=(48, 64), edge_impedance={"left": z, "top": 413.0}, **kw
    )
    sim.add_source(m.CWSource(ix=12, iy=14, frequency=2500.0))
    return sim


def _obstacle_damping(m: ModuleType, kw: dict[str, Any]) -> Engine:
    mask = np.zeros((48, 64), dtype=bool)
    mask[26:34, 22:26] = True
    damping = np.zeros((48, 64))
    damping[38:, :] = 400.0
    sim = m.FDTD2D(
        _air((48, 64)), 0.01, rho=1.21, obstacle_mask=mask, damping=damping, **kw
    )
    samples = np.sin(np.linspace(0.0, 30.0, 400))
    sim.add_source(m.SignalSource(ix=12, iy=28, samples=samples, fs=192000.0))
    return sim


def _plane_wave(m: ModuleType, kw: dict[str, Any]) -> Engine:
    sim = m.FDTD2D(
        343.0,
        0.01,
        shape=(64, 48),
        absorbing_layer_cells=10,
        absorbing_sides=("top", "bottom"),
        **kw,
    )
    pulse = m.GaussianPulse(ix=0, iy=0, half_width_s=5e-5)
    sim.add_source(m.PlaneWaveSource(direction="down", waveform=pulse.value, offset=12))
    sim.add_plane_wave("right", center_m=0.15, half_width_m=0.04, wavelength_m=0.05)
    return sim


def _contour(m: ModuleType, kw: dict[str, Any]) -> Engine:
    sim = m.FDTD2D(343.0, 0.01, shape=(48, 48), absorbing_layer_cells=8, **kw)
    sim.add_source(m.CWSource(ix=24, iy=24, frequency=3000.0))
    sim.add_contour_probe(14, 33, 14, 33, frequencies=[3000.0, 1500.0])
    return sim


def _elastic_layers(m: ModuleType, kw: dict[str, Any]) -> Engine:
    ny, nx = 32, 40
    c_p = np.full((ny, nx), 1480.0)
    c_s = np.zeros((ny, nx))
    rho = np.full((ny, nx), 1000.0)
    c_p[12:, :], c_s[12:, :], rho[12:, :] = 4000.0, 2300.0, 2500.0
    sim = m.ElasticFDTD2D(
        c_p,
        c_s,
        0.01,
        rho=rho,
        absorbing_layer_cells=8,
        absorbing_sides=("left", "right", "bottom"),
        free_sides=("top",),
        **kw,
    )
    pulse = m.ExplosionSource(
        ix=20, iy=5, waveform=lambda t: float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))
    )
    sim.add_source(pulse)
    return sim


def _elastic_force_obstacle(m: ModuleType, kw: dict[str, Any]) -> Engine:
    ny, nx = 40, 40
    mask = np.zeros((ny, nx), dtype=bool)
    mask[15:20, 15:20] = True
    sim = m.ElasticFDTD2D(
        5000.0,
        3000.0,
        0.01,
        rho=7800.0,
        shape=(ny, nx),
        obstacle_mask=mask,
        free_sides=("top", "left"),
        damping=1000.0,
        **kw,
    )
    sim.add_source(
        m.ForceSource(
            ix=30, iy=8, direction="y", waveform=lambda t: float(np.sin(2e4 * t))
        )
    )
    sim.add_source(
        m.ForceSource(
            ix=8, iy=30, direction="x", waveform=lambda t: float(np.cos(2e4 * t))
        )
    )
    return sim


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("sponge", "acoustic", _sponge, steps=100, snapshot_every=10),
    Scenario("impedance", "acoustic", _impedance, steps=80),
    Scenario(
        "obstacle_damping",
        "acoustic",
        _obstacle_damping,
        steps=100,
        snapshot_every=7,
        snapshot_decimation=3,
    ),
    Scenario("plane_wave", "acoustic", _plane_wave, steps=80),
    Scenario("contour", "acoustic", _contour, steps=90),
    Scenario(
        "elastic_layers", "elastic", _elastic_layers, steps=120, snapshot_every=10
    ),
    Scenario(
        "elastic_force_obstacle",
        "elastic",
        _elastic_force_obstacle,
        snapshot_every=9,
        snapshot_decimation=4,
    ),
)


def _host(engine: Engine, name: str) -> NDArray[np.floating]:
    reader = getattr(engine, "numpy_field", None)
    if reader is not None:
        return np.asarray(reader(name))
    return np.array(getattr(engine, name))


def run(
    scenario: Scenario, module: ModuleType, **engine_kwargs: Any
) -> dict[str, NDArray[Any]]:
    """Step *scenario* on *module*'s engine and return every stored field."""
    engine = scenario.build(module, engine_kwargs)
    out: dict[str, NDArray[Any]] = {}
    if scenario.snapshot_every is None:
        engine.run(scenario.steps)
    else:
        out["frames"] = np.asarray(
            _run_frames(
                engine,
                scenario.steps,
                scenario.snapshot_every,
                scenario.snapshot_decimation,
            )
        )
    names = _ACOUSTIC_FIELDS if scenario.kind == "acoustic" else _ELASTIC_FIELDS
    for name in names:
        out[name] = _host(engine, name)
    out["energy"] = np.asarray(engine.energy())
    if scenario.kind == "elastic":
        for field in ("vx", "vy"):
            out[f"collocated_{field}"] = np.asarray(_collocated(engine, field))
    for k, probe in enumerate(getattr(engine, "_contour_probes", [])):
        for f in probe.frequencies:
            phasors = probe.phasors(f)
            pressure, velocity = (
                (phasors.pressure, phasors.normal_velocity)
                if hasattr(phasors, "pressure")
                else phasors
            )
            out[f"contour{k}_{f:g}_p"] = np.asarray(pressure)
            out[f"contour{k}_{f:g}_v"] = np.asarray(velocity)
    return out


def _run_frames(engine: Engine, steps: int, every: int, decimation: int) -> object:
    """``run`` with the snapshot options, by name."""
    return engine.run(steps, snapshot_every=every, snapshot_decimation=decimation)


def _collocated(engine: Engine, field: str) -> object:
    out = engine.collocated(field)
    reader = getattr(engine, "_backend", None)
    return reader.to_host(out) if reader is not None else out
