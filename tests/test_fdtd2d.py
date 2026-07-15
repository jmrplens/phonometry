#  Copyright (c) 2026. Jose M. Requena-Plens
"""Basic physics and determinism tests for the scripts/fdtd2d.py helper.

The engine renders the committed FDTD documentation animations, so what
matters here is that (a) the physics is not obviously wrong (a rigid box
conserves energy, a sponge absorbs it, a centred pulse stays symmetric),
and (b) the output is bit-reproducible run to run.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import fdtd2d  # noqa: E402


def _pulse_box(sponge_width: int) -> fdtd2d.FDTD2D:
    """A homogeneous box with a centred Gaussian pulse (odd grid)."""
    sim = fdtd2d.FDTD2D(343.0, 0.05, shape=(81, 101),
                        sponge_width=sponge_width)
    sim.add_source(fdtd2d.GaussianPulse(ix=50, iy=40, width=6 * sim.dt))
    return sim


def test_rigid_box_conserves_energy() -> None:
    sim = _pulse_box(sponge_width=0)
    sim.run(200)
    e_ref = sim.energy()
    sim.run(600)
    # Leapfrog in a rigid box is lossless up to the O(dt) oscillation of the
    # staggered-in-time energy functional: no systematic gain or loss.
    assert sim.energy() == pytest.approx(e_ref, rel=1e-2)


def test_sponge_absorbs_energy() -> None:
    sim = _pulse_box(sponge_width=20)
    sim.run(60)    # pulse radiated, front just reaching the layer
    e_ref = sim.energy()
    sim.run(740)   # wavefront crosses the absorbing layer
    assert sim.energy() < 1e-2 * e_ref


def test_centered_pulse_stays_symmetric() -> None:
    sim = _pulse_box(sponge_width=0)
    sim.run(500)
    # A centred source in a homogeneous rigid box has both mirror symmetries.
    np.testing.assert_allclose(sim.p, sim.p[::-1, :], atol=1e-12)
    np.testing.assert_allclose(sim.p, sim.p[:, ::-1], atol=1e-12)


def test_two_runs_are_bit_identical() -> None:
    frames = [
        _pulse_box(sponge_width=10).run(300, record_every=50) for _ in range(2)
    ]
    assert frames[0].shape == (7, 81, 101)
    assert np.array_equal(frames[0], frames[1])


def test_cw_source_and_decimation() -> None:
    sim = fdtd2d.FDTD2D(343.0, 0.05, shape=(80, 100), damping=5.0)
    sim.add_source(fdtd2d.CWSource(ix=10, iy=10, frequency=200.0))
    frames = sim.run(400, record_every=100, decimate=2)
    assert frames.shape == (5, 40, 50)
    assert float(np.abs(frames[-1]).max()) > 0.0


def test_heterogeneous_speed_refracts_faster() -> None:
    # A faster right half-space must carry the front further in x than the
    # slow left half does in the same time.
    ny, nx = 81, 161
    c = np.full((ny, nx), 200.0)
    c[:, nx // 2:] = 400.0
    sim = fdtd2d.FDTD2D(c, 0.05)
    sim.add_source(fdtd2d.GaussianPulse(ix=nx // 2, iy=ny // 2,
                                        width=6 * sim.dt))
    sim.run(150)
    row = np.abs(sim.p[ny // 2])
    threshold = 1e-3 * row.max()
    reach_right = np.max(np.nonzero(row > threshold)[0]) - nx // 2
    reach_left = nx // 2 - np.min(np.nonzero(row > threshold)[0])
    assert reach_right > 1.5 * reach_left


def test_invalid_arguments_are_rejected() -> None:
    with pytest.raises(ValueError, match="shape is required"):
        fdtd2d.FDTD2D(343.0, 0.05)
    with pytest.raises(ValueError, match="cfl"):
        fdtd2d.FDTD2D(343.0, 0.05, shape=(10, 10), cfl=0.9)
    with pytest.raises(ValueError, match="sponge sides"):
        fdtd2d.FDTD2D(343.0, 0.05, shape=(10, 10), sponge_width=4,
                      sponge_sides=("north",))
    sim = fdtd2d.FDTD2D(343.0, 0.05, shape=(10, 10))
    with pytest.raises(ValueError, match="outside the grid"):
        sim.add_source(fdtd2d.GaussianPulse(ix=99, iy=0, width=1e-4))
