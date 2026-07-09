#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for :mod:`phonometry.ntacou112` (prominence of impulsive sounds).

Validated against the formulae of NT ACOU 112:2002: the predicted prominence
``P = 3*lg(onset_rate) + 2*lg(level_difference)`` (clause 7, Formula 1), the
graduated adjustment ``KI = 1.8*(P - 5)`` for ``P > 5`` (clause 8, Formula 2)
and the rating level of clause 8, Note 1, evaluated by hand.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from reference_data import NTACOU_ADJUSTMENT_P10, NTACOU_PROMINENCE

from phonometry import ntacou112 as nt


def test_predicted_prominence_formula_1() -> None:
    # P = 3*lg(1000) + 2*lg(30) = 9 + 2*1.477121 = 11.9542.
    p = float(nt.predicted_prominence(1000.0, 30.0))
    assert p == pytest.approx(9.0 + 2.0 * math.log10(30.0), abs=1e-9)
    assert p == pytest.approx(NTACOU_PROMINENCE, abs=1e-4)


def test_predicted_prominence_vectorised() -> None:
    p = nt.predicted_prominence([100.0, 1000.0], [10.0, 30.0])
    # P(100,10) = 3*2 + 2*1 = 8; P(1000,30) = 11.9542.
    np.testing.assert_allclose(p, [8.0, 9.0 + 2.0 * math.log10(30.0)], atol=1e-9)


def test_adjustment_formula_2_and_threshold() -> None:
    # KI at P = 10 is 1.8*(10-5) = 9.0.
    assert float(nt.impulse_adjustment(10.0)) == pytest.approx(NTACOU_ADJUSTMENT_P10)
    assert float(nt.impulse_adjustment(5.0)) == 0.0                   # threshold
    assert float(nt.impulse_adjustment(3.0)) == 0.0                   # below
    # Just above the threshold the adjustment is small and positive.
    assert 0.0 < float(nt.impulse_adjustment(5.5)) == pytest.approx(0.9)


def test_governing_impulse_is_the_highest_p() -> None:
    # The impulse with the highest prominence governs (clause 7).
    result = nt.impulse_prominence([50.0, 1000.0, 200.0], [12.0, 30.0, 20.0])
    assert result.per_impulse.shape == (3,)
    assert result.prominence == pytest.approx(float(result.per_impulse.max()))
    assert result.prominence == pytest.approx(NTACOU_PROMINENCE, abs=1e-4)
    assert result.adjustment == pytest.approx(1.8 * (result.prominence - 5.0))


def test_prominence_design_maximum() -> None:
    # P is designed to peak around 15 for very sudden, loud impulses.
    p = float(nt.predicted_prominence(10_000.0, 40.0))
    assert 14.0 < p < 16.0


def test_rating_level_single_period_reduces_to_laeq_plus_ki() -> None:
    # One sub-interval spanning the whole reference time: LAr = LAeq + KI.
    assert nt.rating_level([70.0], [6.0], [30.0], 30.0) == pytest.approx(76.0)
    assert nt.rating_level([70.0], [0.0], [30.0], 30.0) == pytest.approx(70.0)


def test_rating_level_energy_average() -> None:
    # Two 30-min periods; hand-computed energy average of the adjusted levels.
    got = nt.rating_level([70.0, 60.0], [6.0, 0.0], [30.0, 30.0], 60.0)
    expected = 10.0 * math.log10(
        (30.0 * 10 ** (76.0 / 10) + 30.0 * 10 ** (60.0 / 10)) / 60.0
    )
    assert got == pytest.approx(expected, abs=1e-9)


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="positive"):
        nt.predicted_prominence(0.0, 10.0)
    with pytest.raises(ValueError, match="positive"):
        nt.predicted_prominence(100.0, -1.0)
    with pytest.raises(ValueError, match="at least one"):
        nt.impulse_prominence([], [])
    with pytest.raises(ValueError, match="same shape"):
        nt.impulse_prominence([1.0, 2.0], [1.0])
    with pytest.raises(ValueError, match="equal length"):
        nt.rating_level([70.0, 60.0], [0.0], [30.0, 30.0], 60.0)
    with pytest.raises(ValueError, match="positive"):
        nt.rating_level([70.0], [0.0], [30.0], 0.0)
    with pytest.raises(ValueError, match="at least one"):
        nt.rating_level([], [], [], 60.0)


def test_plot_returns_axes() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    result = nt.impulse_prominence([1000.0, 200.0], [30.0, 15.0])
    assert isinstance(result.plot(), plt.Axes)
    plt.close("all")
