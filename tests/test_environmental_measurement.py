#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for ISO 1996-2:2017 environmental-noise determination.

Anchored on the Annex C.5 tonal-audibility worked examples and the Annex G.2
uncertainty budget (genuine numeric oracles), plus closed-form checks of the
survey method, the residual correction and the uncertainty combination.
"""

from __future__ import annotations

import numpy as np
import pytest

import reference_data as ref
from phonometry import (
    RepeatedMeasurementResult,
    assess_tonal_audibility,
    combined_standard_uncertainty,
    critical_bandwidth,
    environmental_expanded_uncertainty,
    gaussian_residual_level,
    residual_correction_uncertainty,
    residual_sound_correction,
    tonal_adjustment,
    tonal_adjustment_from_mean_audibility,
    tonal_audibility,
    tonal_seeking_survey,
    uncertainty_from_repeated_measurements,
)
from phonometry.environmental_measurement import EnvironmentalMeasurementWarning


# ---------------------------------------------------------------------------
# Tonal audibility -- Annex C.5 oracles
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("lpt", "lpn", "fc", "delta_expected", "kt"), ref.ISO1996_2_TONAL_EXAMPLES)
def test_tonal_audibility_annex_c5(
    lpt: float, lpn: float, fc: float, delta_expected: float, kt: float
) -> None:
    """Formula (C.3) reproduces Annex C.5 examples 1/2/4 within 0.05 dB."""
    delta = tonal_audibility(lpt, lpn, fc)
    assert delta == pytest.approx(delta_expected, abs=0.05)
    assert tonal_adjustment(delta) == pytest.approx(kt)


def test_tonal_audibility_example3_loose() -> None:
    """Example 3 is within 0.7 dB (printed value rounded in the figure)."""
    lpt, lpn, fc, delta_expected, kt = ref.ISO1996_2_TONAL_EXAMPLE3
    delta = tonal_audibility(lpt, lpn, fc)
    assert delta == pytest.approx(delta_expected, abs=0.7)
    assert tonal_adjustment(delta) == pytest.approx(kt)


def test_tonal_adjustment_piecewise() -> None:
    """Kt piecewise (Formulae C.4-C.6): 0 below 4, sloped 4-10, 6 above 10."""
    assert tonal_adjustment(3.0) == 0.0
    assert tonal_adjustment(4.0) == 0.0
    assert tonal_adjustment(7.0) == pytest.approx(3.0)
    assert tonal_adjustment(10.0) == pytest.approx(6.0)
    assert tonal_adjustment(15.0) == 6.0


def test_tonal_adjustment_is_continuous_and_fractional() -> None:
    """Kt is not restricted to integers on the sloped branch."""
    assert tonal_adjustment(6.4) == pytest.approx(2.4)


def test_assess_tonal_audibility_bundles() -> None:
    lpt, lpn, fc, delta_expected, kt = ref.ISO1996_2_TONAL_EXAMPLES[0]
    res = assess_tonal_audibility(lpt, lpn, fc)
    assert res.audibility == pytest.approx(delta_expected, abs=0.05)
    assert res.adjustment == pytest.approx(kt)
    assert res.critical_bandwidth == pytest.approx(0.2 * fc)


# ---------------------------------------------------------------------------
# Critical bandwidth (Table C.1)
# ---------------------------------------------------------------------------
def test_critical_bandwidth_table_c1() -> None:
    assert critical_bandwidth(200.0) == 100.0
    assert critical_bandwidth(500.0) == 100.0
    assert critical_bandwidth(430.0) == 100.0     # example 2 band width
    assert critical_bandwidth(4000.0) == 800.0    # example 1 band width
    assert critical_bandwidth(755.0) == pytest.approx(151.0)  # example 4


# ---------------------------------------------------------------------------
# Mean-audibility route (Table J.1)
# ---------------------------------------------------------------------------
def test_table_j1_mapping() -> None:
    cases = {-1.0: 0, 0.0: 0, 1.0: 1, 3.0: 2, 5.0: 3, 8.0: 4, 11.0: 5, 13.0: 6}
    for delta_l, kt in cases.items():
        assert tonal_adjustment_from_mean_audibility(delta_l) == kt


def test_table_j1_coarse() -> None:
    assert tonal_adjustment_from_mean_audibility(2.0, coarse=True) == 0
    assert tonal_adjustment_from_mean_audibility(5.0, coarse=True) == 3
    assert tonal_adjustment_from_mean_audibility(10.0, coarse=True) == 6


# ---------------------------------------------------------------------------
# Survey method (Annex K)
# ---------------------------------------------------------------------------
def test_survey_thresholds() -> None:
    """A band flagged only when it exceeds both neighbours by the threshold."""
    freqs = [80.0, 100.0, 125.0, 160.0, 200.0, 500.0, 630.0, 800.0]
    # 125 Hz band +20 over neighbours (>15 low-freq threshold) -> flagged
    # 630 Hz band +6 over neighbours (>5 high-freq threshold) -> flagged
    levels = [40.0, 40.0, 60.0, 40.0, 40.0, 50.0, 56.0, 50.0]
    flags = tonal_seeking_survey(levels, freqs)
    assert flags[2]        # 125 Hz
    assert flags[6]        # 630 Hz
    assert not flags[0] and not flags[-1]   # end bands never flagged


def test_survey_below_threshold_not_flagged() -> None:
    freqs = [160.0, 200.0, 250.0]
    levels = [40.0, 45.0, 40.0]   # +5 < 8 dB mid-freq threshold
    assert not tonal_seeking_survey(levels, freqs)[1]


# ---------------------------------------------------------------------------
# Residual-noise correction (Formula 16, Annex I)
# ---------------------------------------------------------------------------
def test_residual_correction_formula16() -> None:
    res = residual_sound_correction(58.0, 50.0)
    expected = 10.0 * np.log10(10.0 ** 5.8 - 10.0 ** 5.0)
    assert res.corrected_level == pytest.approx(expected)
    assert res.margin == pytest.approx(8.0)
    assert res.reliable


def test_residual_correction_unreliable_warns() -> None:
    with pytest.warns(EnvironmentalMeasurementWarning, match="upper bound"):
        res = residual_sound_correction(50.0, 48.0)   # margin 2 dB <= 3
    assert not res.reliable


def test_residual_not_below_raises() -> None:
    with pytest.raises(ValueError, match="below"):
        residual_sound_correction(50.0, 50.0)


def test_gaussian_residual_i1_i2() -> None:
    assert gaussian_residual_level(50.0, l90=40.0) == pytest.approx(
        50.0 + 0.115 * (10.0 / 1.28) ** 2
    )
    assert gaussian_residual_level(50.0, l95=38.0) == pytest.approx(
        50.0 + 0.115 * (12.0 / 1.65) ** 2
    )


def test_gaussian_residual_needs_one_percentile() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        gaussian_residual_level(50.0, l90=40.0, l95=38.0)
    with pytest.raises(ValueError, match="exactly one"):
        gaussian_residual_level(50.0)


# ---------------------------------------------------------------------------
# Measurement uncertainty (Clause 4, Annex F, Annex G oracle)
# ---------------------------------------------------------------------------
def test_combined_uncertainty_g2() -> None:
    """Annex G.2 component products combine to u = 2.18 dB."""
    u = combined_standard_uncertainty(ref.ISO1996_2_G2_CONTRIBUTIONS)
    assert u == pytest.approx(ref.ISO1996_2_G2_COMBINED, abs=0.01)


def test_expanded_uncertainty_g2() -> None:
    """k = 2 (95 %) expansion of the G.2 uncertainty -> 4.36 dB."""
    u = combined_standard_uncertainty(ref.ISO1996_2_G2_CONTRIBUTIONS)
    assert environmental_expanded_uncertainty(u) == pytest.approx(
        ref.ISO1996_2_G2_EXPANDED, abs=0.01
    )
    assert environmental_expanded_uncertainty(u, confidence=0.80) == pytest.approx(1.3 * u)


def test_combined_uncertainty_accepts_pairs() -> None:
    """(uncertainty, sensitivity) pairs give the same result as the products."""
    pairs = [(1.0, 2.0), (3.0, 1.0)]
    assert combined_standard_uncertainty(pairs) == pytest.approx(np.hypot(2.0, 3.0))


def test_expanded_uncertainty_bad_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        environmental_expanded_uncertainty(1.0, confidence=0.90)


def test_residual_correction_uncertainty_f9() -> None:
    """Formulae (F.7)/(F.8)/(F.9): sensitivity-weighted quadrature."""
    lp, lres, u_lp, u_res = 58.0, 50.0, 0.5, 2.0
    m = 10.0 ** (-0.1 * (lp - lres))
    c_lp = 1.0 / (1.0 - m)
    c_res = -m / (1.0 - m)
    expected = np.hypot(c_lp * u_lp, c_res * u_res)
    assert residual_correction_uncertainty(lp, lres, u_lp, u_res) == pytest.approx(expected)


def test_repeated_measurements() -> None:
    """Formulae (18)/(20): energy mean and sample standard deviation."""
    levels = [58.0, 59.0, 57.0, 60.0]
    res = uncertainty_from_repeated_measurements(levels)
    assert isinstance(res, RepeatedMeasurementResult)
    # Lk is the energy mean (Formula 18); the uncertainty (Formula 20) takes the
    # deviations from that energy mean, not from the arithmetic mean.
    lk = 10.0 * np.log10(np.mean(10.0 ** (0.1 * np.array(levels))))
    expected_uk = np.sqrt(np.sum((np.array(levels) - lk) ** 2) / (len(levels) - 1))
    assert res.mean_level == pytest.approx(lk)
    assert res.standard_uncertainty == pytest.approx(expected_uk)
    assert res.n == 4


def test_repeated_measurements_needs_two() -> None:
    with pytest.raises(ValueError, match="at least two"):
        uncertainty_from_repeated_measurements([58.0])


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = assess_tonal_audibility(54.1, 45.2, 430.0)
    assert res.plot() is not None
