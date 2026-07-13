#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for NPD event-level interpolation (ECAC Doc 29 §4.2).

Oracles (independent of the implementation): recovery of the tabulated nodes,
hand-computed log-linear (distance) and linear (power) interpolation, monotonic
decrease with distance, and the terminal-segment extrapolation.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.airport_noise import NpdLevelResult, npd_curve, npd_level

# Two powers, four log-spaced distances; levels drop 6 dB per doubling.
_P = [1000.0, 2000.0]
_D = [200.0, 400.0, 800.0, 1600.0]
_L = [[100.0, 94.0, 88.0, 82.0], [110.0, 104.0, 98.0, 92.0]]


def test_recovers_tabulated_nodes() -> None:
    assert npd_level(_P, _D, _L, 1000.0, 200.0)[0] == pytest.approx(100.0)
    assert npd_level(_P, _D, _L, 2000.0, 1600.0)[0] == pytest.approx(92.0)
    assert npd_level(_P, _D, _L, 1000.0, 800.0)[0] == pytest.approx(88.0)


def test_log_linear_distance_interpolation() -> None:
    # Midpoint in log distance between 200 and 400 is sqrt(200*400); the level is
    # the arithmetic mean of the two node levels.
    dm = np.sqrt(200.0 * 400.0)
    assert npd_level(_P, _D, _L, 1000.0, dm)[0] == pytest.approx(97.0)


def test_linear_power_interpolation() -> None:
    # Halfway in power (1500) at a tabulated distance is the mean of the rows.
    assert npd_level(_P, _D, _L, 1500.0, 200.0)[0] == pytest.approx(105.0)
    assert npd_level(_P, _D, _L, 1500.0, 800.0)[0] == pytest.approx(93.0)


def test_monotonic_decrease_with_distance() -> None:
    lv = npd_level(_P, _D, _L, 1500.0, np.array([200.0, 400.0, 800.0, 1600.0]))
    # At the tabulated nodes the P = 1500 row is the mean of the two power rows.
    assert np.allclose(lv, [105.0, 99.0, 93.0, 87.0])
    assert np.all(np.diff(lv) < 0.0)


def test_distance_extrapolation_uses_terminal_slope() -> None:
    # Below 6 dB/doubling on the last segment (800->1600), one more doubling to
    # 3200 m gives 82 - 6 = 76 dB at P = 1000.
    assert npd_level(_P, _D, _L, 1000.0, 3200.0)[0] == pytest.approx(76.0)
    # And inward from 200 m: one halving to 100 m gives 100 + 6 = 106 dB.
    assert npd_level(_P, _D, _L, 1000.0, 100.0)[0] == pytest.approx(106.0)


def test_power_extrapolation() -> None:
    # Beyond the last power (2000): linear on the terminal power segment. At
    # P = 3000, d = 200: 100 + 2*(110-100) = 120 dB.
    assert npd_level(_P, _D, _L, 3000.0, 200.0)[0] == pytest.approx(120.0)
    # Below the first power (1000): linear extrapolation downward. At P = 500,
    # d = 200: 100 + (-0.5)*(110-100) = 95 dB.
    assert npd_level(_P, _D, _L, 500.0, 200.0)[0] == pytest.approx(95.0)


def test_npd_curve_result_and_plot() -> None:
    res = npd_curve(_P, _D, _L, 1500.0)
    assert isinstance(res, NpdLevelResult)
    assert res.distance.shape == res.level.shape
    assert res.table_distances.shape == res.table_levels.shape
    # tabulated levels at P=1500 are the row means
    assert np.allclose(res.table_levels, [105.0, 99.0, 93.0, 87.0])
    assert res.plot() is not None


def test_invalid_table_rejected() -> None:
    with pytest.raises(ValueError, match="shape"):
        npd_level(_P, _D, [[100.0, 94.0]], 1000.0, 200.0)  # wrong levels shape
    with pytest.raises(ValueError, match="increasing"):
        npd_level([2000.0, 1000.0], _D, _L[::-1], 1500.0, 200.0)
    with pytest.raises(ValueError, match="distance"):
        npd_level(_P, _D, _L, 1000.0, -100.0)
