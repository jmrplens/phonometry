#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for plane-wave seabed reflection (fluid-fluid Rayleigh model).

Oracles (independent of the implementation): the normal-incidence impedance
reflection coefficient ``R = (Z2 − Z1)/(Z2 + Z1)``; the analytic critical grazing
angle ``arccos(c1/c2)``; and total reflection (``|R| = 1``) below it.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.seabed_reflection import (
    BottomLossResult,
    bottom_reflection_loss,
    critical_angle,
    reflection_coefficient,
)

# Water over a fast sandy bottom.
_WATER = dict(rho1=1000.0, c1=1500.0)
_SAND = dict(rho2=1900.0, c2=1650.0)


def test_normal_incidence_matches_impedance_formula() -> None:
    # At 90 deg grazing (normal incidence) R = (Z2 - Z1)/(Z2 + Z1), Z = rho*c.
    z1 = 1000.0 * 1500.0
    z2 = 1900.0 * 1650.0
    r_expected = (z2 - z1) / (z2 + z1)  # 0.35275
    r = reflection_coefficient(90.0, **_WATER, **_SAND)
    assert float(np.real(r[0])) == pytest.approx(r_expected, abs=1e-6)
    assert float(np.abs(r[0])) == pytest.approx(0.35275, abs=1e-4)


def test_normal_incidence_bottom_loss() -> None:
    # BL = -20 log10|R| ~= 9.05 dB for the sand/water pair at normal incidence.
    res = bottom_reflection_loss(90.0, **_WATER, **_SAND)
    assert isinstance(res, BottomLossResult)
    assert float(res.reflection_loss[0]) == pytest.approx(9.055, abs=1e-2)


def test_critical_angle_analytic() -> None:
    # phi_c = arccos(c1/c2) = arccos(1500/1650) = 24.620 deg.
    assert critical_angle(1500.0, 1650.0) == pytest.approx(
        np.degrees(np.arccos(1500.0 / 1650.0)), abs=1e-6
    )
    assert critical_angle(1500.0, 1650.0) == pytest.approx(24.620, abs=1e-3)


def test_total_reflection_below_critical_angle() -> None:
    # Below the critical grazing angle the wave is totally reflected: |R| = 1,
    # bottom loss ~ 0 dB.
    phi_c = critical_angle(1500.0, 1650.0)
    res = bottom_reflection_loss(np.array([5.0, 15.0, 24.0]), **_WATER, **_SAND)
    assert np.all(np.array([5.0, 15.0, 24.0]) < phi_c)
    assert np.allclose(np.abs(res.reflection_coefficient), 1.0, atol=1e-9)
    assert np.allclose(res.reflection_loss, 0.0, atol=1e-6)
    assert res.critical_angle == pytest.approx(phi_c)


def test_no_critical_angle_for_slow_bottom() -> None:
    # A slower bottom (mud, c2 < c1) has no critical angle.
    with pytest.raises(ValueError, match="c2 > c1"):
        critical_angle(1500.0, 1450.0)
    res = bottom_reflection_loss(45.0, rho1=1000.0, c1=1500.0, rho2=1500.0, c2=1450.0)
    assert res.critical_angle is None
    assert np.all(res.reflection_loss > 0.0)


def test_grazing_angle_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="grazing_angle"):
        reflection_coefficient(120.0, **_WATER, **_SAND)


def test_bottom_loss_plot_smoke() -> None:
    res = bottom_reflection_loss(np.linspace(0.0, 90.0, 91), **_WATER, **_SAND)
    assert res.plot() is not None
