#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for EN 15657:2018 structure-borne sound power (reception-plate method).

Anchored on the closed-form reception-plate relations: the energetic spatial
mean velocity level (Formula 12), the loss factor eta = 2.2/(f Ts) (Formula 13),
and the characteristic power level L_Ws = 10 lg(2 pi f eta m S) + L_v - 60 dB
(Formula 14). The physical oracle is the resonant-plate power balance
P = omega eta (m S) <v^2>, whose level equals L_Ws exactly.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import (
    StructureBornePowerResult,
    plate_loss_factor,
    reception_plate_power,
    spatial_mean_velocity_level,
    structure_borne_power_level,
    total_loss_factor,
)

V0, P0 = 1.0e-9, 1.0e-12


# ---------------------------------------------------------------------------
# Spatial mean velocity level (Formula 12)
# ---------------------------------------------------------------------------
def test_spatial_mean_is_energetic_average() -> None:
    levels = np.array([78.0, 80.0, 82.0, 79.0, 81.0, 80.0])
    expected = 10.0 * math.log10(np.mean(10.0 ** (0.1 * levels)))
    assert spatial_mean_velocity_level(levels) == pytest.approx(expected)


def test_spatial_mean_uniform_levels() -> None:
    assert spatial_mean_velocity_level([75.0, 75.0, 75.0]) == pytest.approx(75.0)


# ---------------------------------------------------------------------------
# Loss factor (Formula 13) == ISO 10848 total loss factor
# ---------------------------------------------------------------------------
def test_loss_factor_formula() -> None:
    f, ts = np.array([500.0, 1000.0]), 0.3
    assert np.allclose(plate_loss_factor(f, ts), 2.2 / (f * ts))


def test_loss_factor_matches_iso10848() -> None:
    f, ts = np.array([250.0, 500.0, 1000.0]), 0.4
    assert np.allclose(plate_loss_factor(f, ts), total_loss_factor(f, ts))


# ---------------------------------------------------------------------------
# Power level (Formula 14) and the resonant-plate power balance
# ---------------------------------------------------------------------------
def test_power_level_hand_value() -> None:
    lw = float(structure_borne_power_level(80.0, 1000.0, 10.0, 1.0, 0.01))
    assert lw == pytest.approx(47.982, abs=1e-3)


def test_power_level_equals_dissipated_power() -> None:
    """L_Ws equals the level of P = omega eta (m S) <v^2>."""
    lv, f, m, s, eta = 82.0, 800.0, 15.0, 1.5, 0.02
    lw = float(structure_borne_power_level(lv, f, m, s, eta))
    v2 = V0**2 * 10.0 ** (0.1 * lv)
    p = 2.0 * math.pi * f * eta * (m * s) * v2
    assert lw == pytest.approx(10.0 * math.log10(p / P0))


def test_power_level_offset_is_minus_60() -> None:
    # With v0 = 1e-9 and P0 = 1e-12 the reference term is exactly -60 dB.
    # L_Ws - L_v - 10 lg(2 pi f eta m S) = -60
    f, m, s, eta = 1000.0, 10.0, 1.0, 0.01
    lw = float(structure_borne_power_level(0.0, f, m, s, eta))
    log_term = 10.0 * math.log10(2.0 * math.pi * f * eta * m * s)
    assert lw - log_term == pytest.approx(-60.0)


def test_power_level_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="mass_per_area"):
        structure_borne_power_level(80.0, 1000.0, 0.0, 1.0, 0.01)
    with pytest.raises(ValueError, match="area"):
        structure_borne_power_level(80.0, 1000.0, 10.0, 0.0, 0.01)
    with pytest.raises(ValueError, match="frequency"):
        structure_borne_power_level(80.0, 0.0, 10.0, 1.0, 0.01)


# ---------------------------------------------------------------------------
# Reception-plate constructor / result
# ---------------------------------------------------------------------------
def test_reception_plate_from_reverberation_time() -> None:
    f = np.array([500.0, 1000.0, 2000.0])
    res = reception_plate_power(
        np.array([80.0, 82.0, 79.0]), f, mass_per_area=25.0, area=1.2,
        reverberation_time=0.4,
    )
    assert isinstance(res, StructureBornePowerResult)
    assert np.allclose(res.loss_factor, 2.2 / (f * 0.4))
    assert np.allclose(
        res.power_level,
        structure_borne_power_level(res.velocity_level, f, 25.0, 1.2, res.loss_factor),
    )


def test_reception_plate_explicit_loss_factor_broadcasts() -> None:
    f = np.array([500.0, 1000.0, 2000.0])
    res = reception_plate_power(80.0, f, mass_per_area=25.0, area=1.2, loss_factor=0.02)
    assert res.loss_factor.shape == (3,)
    assert np.all(res.loss_factor == 0.02)
    assert np.all(res.velocity_level == 80.0)


def test_reception_plate_total_level() -> None:
    res = reception_plate_power(
        np.array([80.0, 82.0, 79.0]), np.array([500.0, 1000.0, 2000.0]),
        mass_per_area=25.0, area=1.2, loss_factor=0.01,
    )
    expected = 10.0 * math.log10(np.sum(10.0 ** (0.1 * res.power_level)))
    assert res.total_level == pytest.approx(expected)


def test_reception_plate_requires_eta_or_ts() -> None:
    with pytest.raises(ValueError, match="loss_factor"):
        reception_plate_power(80.0, 1000.0, 25.0, 1.2)


def test_reception_plate_velocity_shape_mismatch() -> None:
    # a non-broadcastable velocity_level vs frequency length raises
    with pytest.raises(ValueError):
        reception_plate_power(
            [80.0, 82.0, 79.0], [500.0, 1000.0, 2000.0, 4000.0],
            mass_per_area=25.0, area=1.2, loss_factor=0.01,
        )


def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = reception_plate_power(
        np.array([80.0, 82.0, 79.0]), np.array([500.0, 1000.0, 2000.0]),
        mass_per_area=25.0, area=1.2, loss_factor=0.01,
    )
    assert res.plot() is not None
