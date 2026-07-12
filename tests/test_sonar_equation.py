#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the sonar equation (passive and active).

Oracles: a hand-worked textbook term balance (Urick via Etter, Table 10.2) —
pure arithmetic, independent of the implementation.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.sonar_equation import (
    SonarEquationResult,
    active_sonar_equation,
    passive_sonar_equation,
)


def test_passive_signal_excess_and_fom() -> None:
    # SE = SL - TL - (NL - DI) - DT ; hand values.
    res = passive_sonar_equation(140.0, 80.0, 60.0, directivity_index=10.0,
                                 detection_threshold=5.0)
    assert isinstance(res, SonarEquationResult)
    assert res.mode == "passive"
    # SE = 140 - 80 - (60 - 10) - 5 = 5
    assert res.signal_excess[0] == pytest.approx(5.0)
    # SNR = SE + DT = 10
    assert res.snr[0] == pytest.approx(10.0)
    # FOM = SL - (NL - DI) - DT = 140 - 50 - 5 = 85
    assert res.figure_of_merit == pytest.approx(85.0)


def test_passive_detection_at_fom() -> None:
    # At TL = FOM the signal excess is exactly zero (detection limit).
    res = passive_sonar_equation(140.0, [85.0], 60.0, directivity_index=10.0,
                                 detection_threshold=5.0)
    assert res.signal_excess[0] == pytest.approx(0.0, abs=1e-9)


def test_active_noise_limited() -> None:
    # SE = SL - 2 TL + TS - (NL - DI) - DT
    res = active_sonar_equation(220.0, 70.0, 15.0, 60.0, directivity_index=20.0,
                                detection_threshold=10.0)
    assert res.mode == "active"
    # SE = 220 - 140 + 15 - (60 - 20) - 10 = 45
    assert res.signal_excess[0] == pytest.approx(45.0)
    # FOM = (SL + TS - (NL - DI) - DT)/2 = (220 + 15 - 40 - 10)/2 = 92.5
    assert res.figure_of_merit == pytest.approx(92.5)


def test_active_reverberation_limited_ignores_di() -> None:
    # With RL given, masking is RL (DI does not apply to reverberation).
    res = active_sonar_equation(220.0, 70.0, 15.0, 60.0, directivity_index=20.0,
                                detection_threshold=10.0, reverberation_level=55.0)
    assert res.reverberation_limited is True
    # SE = 220 - 140 + 15 - 55 - 10 = 30
    assert res.signal_excess[0] == pytest.approx(30.0)
    assert res.figure_of_merit == pytest.approx((220.0 + 15.0 - 55.0 - 10.0) / 2.0)


def test_signal_excess_decreases_with_transmission_loss() -> None:
    tl = np.linspace(50.0, 120.0, 8)
    res = passive_sonar_equation(150.0, tl, 55.0)
    assert np.all(np.diff(res.signal_excess) < 0.0)
    # Passive SE decreases 1 dB per dB of one-way TL.
    np.testing.assert_allclose(np.diff(res.signal_excess), -np.diff(tl))


def test_active_two_way_loss() -> None:
    # Active SE loses 2 dB per dB of one-way TL.
    res = active_sonar_equation(200.0, [60.0, 61.0], 10.0, 50.0)
    assert res.signal_excess[1] - res.signal_excess[0] == pytest.approx(-2.0)


def test_rejects_non_finite() -> None:
    with pytest.raises(ValueError):
        passive_sonar_equation(float("nan"), 80.0, 60.0)


def test_plot_smoke() -> None:
    res = passive_sonar_equation(150.0, np.linspace(40.0, 110.0, 40), 55.0,
                                 detection_threshold=8.0)
    assert res.plot() is not None
