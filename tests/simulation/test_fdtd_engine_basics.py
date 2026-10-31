#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Physics checks of the acoustic engine on small grids, and what it refuses.

A rigid box conserves energy, a sponge absorbs it, a centred pulse stays
symmetric, a faster region refracts, and the constructor, the two sources and
``run`` refuse what they should. The analytic-oracle validation and the check
that two runs are bit-identical are in ``test_fdtd.py``; these are the quick
checks that used to run through the documentation's import shim.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry.simulation.fdtd import FDTD2D, CWSource, GaussianPulse


def _pulse_box(absorbing_layer_cells: int) -> FDTD2D:
    """A homogeneous box with a centred Gaussian pulse (odd grid)."""
    sim = FDTD2D(
        343.0, 0.05, shape=(81, 101), absorbing_layer_cells=absorbing_layer_cells
    )
    sim.add_source(GaussianPulse(ix=50, iy=40, half_width_s=6 * sim.dt))
    return sim


def test_rigid_box_conserves_energy() -> None:
    sim = _pulse_box(absorbing_layer_cells=0)
    sim.run(200)
    e_ref = sim.energy()
    sim.run(600)
    # Leapfrog in a rigid box is lossless up to the O(dt) oscillation of the
    # staggered-in-time energy functional: no systematic gain or loss.
    assert sim.energy() == pytest.approx(e_ref, rel=1e-2)


def test_sponge_absorbs_energy() -> None:
    sim = _pulse_box(absorbing_layer_cells=20)
    sim.run(60)  # pulse radiated, front just reaching the layer
    e_ref = sim.energy()
    sim.run(740)  # wavefront crosses the absorbing layer
    assert sim.energy() < 1e-2 * e_ref


def test_centered_pulse_stays_symmetric() -> None:
    sim = _pulse_box(absorbing_layer_cells=0)
    sim.run(500)
    # A centred source in a homogeneous rigid box has both mirror symmetries.
    np.testing.assert_allclose(sim.p, sim.p[::-1, :], atol=1e-12)
    np.testing.assert_allclose(sim.p, sim.p[:, ::-1], atol=1e-12)


def test_heterogeneous_speed_refracts_faster() -> None:
    # A faster right half-space must carry the front further in x than the
    # slow left half does in the same time.
    ny, nx = 81, 161
    c = np.full((ny, nx), 200.0)
    c[:, nx // 2 :] = 400.0
    sim = FDTD2D(c, 0.05)
    sim.add_source(GaussianPulse(ix=nx // 2, iy=ny // 2, half_width_s=6 * sim.dt))
    sim.run(150)
    row = np.abs(sim.p[ny // 2])
    threshold = 1e-3 * row.max()
    reach_right = np.max(np.nonzero(row > threshold)[0]) - nx // 2
    reach_left = nx // 2 - np.min(np.nonzero(row > threshold)[0])
    assert reach_right > 1.5 * reach_left


def test_scalar_c_requires_shape() -> None:
    with pytest.raises(ValueError, match="shape is required"):
        FDTD2D(343.0, 0.05)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"cfl": 1.2}, "cfl"),
        ({"c": 0.0}, "c must be strictly positive"),
        ({"c": np.full((10, 10), np.nan)}, "c must be strictly positive"),
        ({"rho": -1.2}, "rho must be strictly positive"),
        ({"rho": np.full((10, 10), np.inf)}, "rho must be strictly positive"),
        ({"dx": 0.0}, "dx must be positive"),
        ({"dx": np.nan}, "dx must be positive"),
        ({"damping": -1.0}, "damping must be non-negative"),
        ({"damping": np.inf}, "damping must be non-negative"),
        ({"absorbing_layer_cells": -1}, "absorbing_layer_cells must be non-negative"),
        ({"absorbing_layer_cells": 10}, "absorbing_layer_cells must be fewer"),
        (
            {"absorbing_layer_cells": 4, "absorbing_layer_reflection": 0.0},
            "absorbing_layer_reflection must lie strictly between 0 and 1",
        ),
        (
            {"absorbing_layer_cells": 4, "absorbing_layer_reflection": 1.0},
            "absorbing_layer_reflection must lie strictly between 0 and 1",
        ),
        (
            {"absorbing_layer_cells": 4, "absorbing_sides": ("north",)},
            "'absorbing_sides' must be one of",
        ),
        (
            {"absorbing_layer_cells": 4, "absorbing_sides": "north"},
            "'absorbing_sides' must be one of",
        ),
        # A malformed grid shape used to be reported by somebody else: numpy,
        # or the absorbing_layer_cells guard for a zero-length side, or a message
        # blaming c. A complex c or rho ran to completion on its real part.
        ({"shape": (0, 10)}, "shape must be a pair of positive integers"),
        ({"shape": (-1, 10)}, "shape must be a pair of positive integers"),
        ({"shape": (10, 10.5)}, "shape must be a pair of positive integers"),
        ({"shape": (10, 10, 10)}, "shape must be a pair of positive integers"),
    ],
)
def test_constructor_rejects_invalid_arguments(
    kwargs: dict[str, object],
    match: str,
) -> None:
    full: dict[str, object] = {"c": 343.0, "dx": 0.05, "shape": (10, 10), **kwargs}
    c = full.pop("c")
    dx = full.pop("dx")
    with pytest.raises(ValueError, match=match):
        FDTD2D(c, dx, **full)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        # A number where the pair belongs, a count that is no number, and a
        # complex medium are each the wrong type.
        ({"shape": 10}, "shape must be a pair of positive integers"),
        ({"shape": (10, "10")}, "shape must be a pair of positive integers"),
        ({"c": 343.0 + 50.0j}, "c must be real"),
        ({"c": np.full((10, 10), 343.0 + 50.0j)}, "c must be real"),
        ({"rho": 1.2 + 3.0j}, "rho must be real"),
    ],
)
def test_constructor_rejects_arguments_of_the_wrong_type(
    kwargs: dict[str, object],
    match: str,
) -> None:
    full: dict[str, object] = {"c": 343.0, "dx": 0.05, "shape": (10, 10), **kwargs}
    c = full.pop("c")
    dx = full.pop("dx")
    with pytest.raises(TypeError, match=match):
        FDTD2D(c, dx, **full)  # type: ignore[arg-type]


def test_a_whole_float_grid_shape_is_taken_as_its_counts() -> None:
    sim = FDTD2D(343.0, 0.05, shape=(10.0, 12))  # type: ignore[arg-type]
    assert sim.c.shape == (10, 12)


def test_absorbing_sides_accepts_a_bare_string() -> None:
    # A single side name must mean that side, not its individual characters.
    sim = FDTD2D(
        343.0, 0.05, shape=(20, 20), absorbing_layer_cells=5, absorbing_sides="left"
    )
    assert float(sim._decay_p[10, 0]) < 1.0  # left edge absorbs
    assert float(sim._decay_p[10, -1]) == 1.0  # right edge stays rigid


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"half_width_s": 0.0}, "half_width_s must be positive"),
        ({"half_width_s": np.inf}, "half_width_s must be positive"),
        ({"half_width_s": 1e-4, "amplitude": np.nan}, "amplitude must be finite"),
        ({"half_width_s": 1e-4, "t0": np.inf}, "t0 must be finite"),
    ],
)
def test_gaussian_pulse_rejects_invalid_parameters(
    kwargs: dict[str, float],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        GaussianPulse(ix=0, iy=0, **kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"frequency": 0.0}, "frequency must be positive"),
        ({"frequency": np.nan}, "frequency must be positive"),
        ({"frequency": 100.0, "ramp_cycles": -1.0}, "ramp_cycles"),
        ({"frequency": 100.0, "amplitude": np.inf}, "amplitude must be finite"),
    ],
)
def test_cw_source_rejects_invalid_parameters(
    kwargs: dict[str, float],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        CWSource(ix=0, iy=0, **kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"n_steps": -1}, "'n_steps' must be non-negative"),
        (
            {"n_steps": 1, "snapshot_every": 0},
            "'snapshot_every' must be a whole number, at least 1",
        ),
        (
            {"n_steps": 1, "snapshot_every": 1, "snapshot_decimation": 0},
            "'snapshot_decimation' must be a whole number, at least 1",
        ),
    ],
)
def test_run_rejects_invalid_recording_controls(
    kwargs: dict[str, int],
    match: str,
) -> None:
    sim = FDTD2D(343.0, 0.05, shape=(10, 10))
    with pytest.raises(ValueError, match=match):
        sim.run(**kwargs)
