#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for ISO 16283-1:2014 field airborne sound insulation and
ISO 717-1 weighted ratings (C / Ctr).

Validation strategy: the standards' own numbers, not self-consistency.

- The weighted rating and C / Ctr are checked against the worked example
  of ISO 717-1 Annex C, Table C.1 (measured R gives Rw = 30 with an
  unfavourable-deviation sum of 31,8 dB, C = -2, Ctr = -3).
- The unfavourable-deviation bound (Clause 4.4: <= 32,0 dB for 16
  one-third-octave bands, <= 10,0 dB for 5 octave bands) is exercised
  with a curve that hits the bound exactly and one that tips over,
  forcing one more decibel of shift.
- DnT (Formula (2)) reduces to D when T = T0 = 0,5 s; R' (Formula (4)
  with A = 0,16 V / T, Formula (5)) reduces to D for S T = 0,16 V.
- The energy-average level (Formula (9)) is checked against hand values.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import (
    AirborneInsulationResult,
    WeightedRatingResult,
    airborne_insulation,
    energy_average_level,
    weighted_rating,
)

# One-third-octave reference values, ISO 717-1 Table 3 (100 Hz to 3150 Hz).
_REF_THIRD = [33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56]
# Octave reference values, ISO 717-1 Table 3 (125 Hz to 2000 Hz).
_REF_OCTAVE = [36, 45, 52, 55, 56]

# ISO 717-1 Annex C, Table C.1 measured sound reduction index R (100-3150).
_ANNEX_C_R = [
    20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
    28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5,
]


# --------------------------------------------------------------------------
# ISO 717-1 weighted rating and spectrum adaptation terms
# --------------------------------------------------------------------------

def test_annex_c_worked_example_third_octave() -> None:
    """ISO 717-1 Annex C Table C.1: Rw(C;Ctr) = 30(-2;-3) dB."""
    res = weighted_rating(_ANNEX_C_R)
    assert isinstance(res, WeightedRatingResult)
    assert res.rating == 30
    assert res.c == -2
    assert res.ctr == -3
    # Sum of unfavourable deviations at the final shift: 31,8 dB (< 32,0).
    assert res.unfavourable_sum == pytest.approx(31.8, abs=1e-9)


def test_reference_curve_rates_itself() -> None:
    """Measured == reference => shift up by 2 dB (16 * 2 = 32,0), Rw = 54."""
    res = weighted_rating(_REF_THIRD)
    assert res.rating == 54
    assert res.unfavourable_sum == pytest.approx(32.0, abs=1e-9)


def test_unfavourable_sum_exactly_at_bound_third_octave() -> None:
    """Measured = reference - 2 everywhere => sum = 32,0 exactly, Rw = 52."""
    measured = [r - 2.0 for r in _REF_THIRD]
    res = weighted_rating(measured)
    assert res.rating == 52
    assert res.unfavourable_sum == pytest.approx(32.0, abs=1e-9)


def test_unfavourable_sum_tips_over_forces_one_more_db() -> None:
    """0,1 dB over the 32,0 bound forces one more decibel of shift."""
    measured = [r - 2.0 for r in _REF_THIRD]
    measured[0] -= 0.1  # sum would be 32,1 at the previous shift
    res = weighted_rating(measured)
    assert res.rating == 51
    # At Rw = 51 the 15 untouched bands contribute 1,0 dB each and the
    # tipped band 1,1 dB => 16,1 dB (<= 32,0).
    assert res.unfavourable_sum == pytest.approx(16.1, abs=1e-9)


def test_octave_band_rating_bound() -> None:
    """5 octave bands: bound is 10,0 dB; measured = ref - 2 => Rw = 52."""
    measured = [r - 2.0 for r in _REF_OCTAVE]
    res = weighted_rating(measured)
    assert res.rating == 52
    assert res.unfavourable_sum == pytest.approx(10.0, abs=1e-9)


def test_octave_reference_rates_itself() -> None:
    """Octave reference == measured => 5 * 2 = 10,0 => Rw = 54."""
    res = weighted_rating(_REF_OCTAVE)
    assert res.rating == 54
    assert res.unfavourable_sum == pytest.approx(10.0, abs=1e-9)


def test_explicit_band_set_override() -> None:
    """Band count 16/5 is inferred but can be stated explicitly."""
    res = weighted_rating(_ANNEX_C_R, bands="third-octave")
    assert res.rating == 30


def test_measured_data_rounded_to_one_decimal() -> None:
    """Clause 4.4 footnote 1: inputs reduced to 0,1 dB (round half up)."""
    # 30,04 -> 30,0 and 30,05 -> 30,1 must not change already-tenths data.
    res = weighted_rating(_ANNEX_C_R)
    perturbed = [v + 0.049 for v in _ANNEX_C_R]  # rounds back to originals
    assert weighted_rating(perturbed).rating == res.rating


def test_weighted_rating_rejects_bad_length() -> None:
    with pytest.raises(ValueError):
        weighted_rating([1.0, 2.0, 3.0])


def test_weighted_rating_rejects_nan() -> None:
    bad = list(_ANNEX_C_R)
    bad[0] = float("nan")
    with pytest.raises(ValueError):
        weighted_rating(bad)


# --------------------------------------------------------------------------
# ISO 16283-1 field quantities
# --------------------------------------------------------------------------

def test_energy_average_level_formula9() -> None:
    """Formula (9): equal levels average to themselves; 60 & 70 -> 67,4."""
    assert energy_average_level([60.0, 60.0, 60.0]) == pytest.approx(60.0)
    expected = 10.0 * np.log10((10 ** 6 + 10 ** 7) / 2.0)
    assert energy_average_level([60.0, 70.0]) == pytest.approx(expected)


def test_dnt_equals_d_when_t_is_half_second() -> None:
    """Formula (2): T = T0 = 0,5 s => DnT = D exactly."""
    l1 = np.array([80.0, 82.0, 85.0])
    l2 = np.array([40.0, 45.0, 50.0])
    t2 = np.full(3, 0.5)
    res = airborne_insulation(l1, l2, t2)
    assert isinstance(res, AirborneInsulationResult)
    np.testing.assert_allclose(res.d, l1 - l2)
    np.testing.assert_allclose(res.dnt, l1 - l2)


def test_dnt_scales_with_reverberation_time() -> None:
    """T = 5 s, T0 = 0,5 s => 10 lg(10) = 10 dB added to D."""
    l1 = np.array([80.0])
    l2 = np.array([40.0])
    res = airborne_insulation(l1, l2, np.array([5.0]))
    np.testing.assert_allclose(res.dnt, [50.0])


def test_apparent_reduction_index_formula4() -> None:
    """Formula (4)+(5): S*T = 0,16*V => 10 lg(S/A) = 0 => R' = D."""
    l1 = np.array([80.0, 82.0])
    l2 = np.array([40.0, 45.0])
    t2 = np.array([1.0, 1.0])
    # A = 0,16 * V / T = 0,16; S = 0,16 => S/A = 1.
    res = airborne_insulation(l1, l2, t2, area=0.16, volume=1.0)
    assert res.r_prime is not None
    np.testing.assert_allclose(res.r_prime, l1 - l2)


def test_apparent_reduction_index_ten_db_offset() -> None:
    """S = 1,6, V = 1, T = 1 => A = 0,16, S/A = 10 => R' = D + 10."""
    l1 = np.array([80.0])
    l2 = np.array([40.0])
    res = airborne_insulation(
        l1, l2, np.array([1.0]), area=1.6, volume=1.0
    )
    assert res.r_prime is not None
    np.testing.assert_allclose(res.r_prime, [50.0])


def test_r_prime_none_without_geometry() -> None:
    res = airborne_insulation(
        np.array([80.0]), np.array([40.0]), np.array([0.5])
    )
    assert res.r_prime is None


def test_airborne_energy_averages_positions() -> None:
    """2-D inputs (positions x bands) are energy-averaged (Formula (9))."""
    l1 = np.array([[80.0, 80.0], [80.0, 80.0]])  # two positions, two bands
    l2 = np.array([[40.0, 50.0], [50.0, 40.0]])
    res = airborne_insulation(l1, l2, np.array([0.5, 0.5]))
    l2_avg = 10.0 * np.log10((10 ** 4 + 10 ** 5) / 2.0)
    np.testing.assert_allclose(res.d, 80.0 - l2_avg)


def test_airborne_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError):
        airborne_insulation(
            np.array([80.0, 80.0]), np.array([40.0]), np.array([0.5])
        )


def test_airborne_requires_both_area_and_volume() -> None:
    with pytest.raises(ValueError):
        airborne_insulation(
            np.array([80.0]), np.array([40.0]), np.array([0.5]), area=10.0
        )


def test_field_rating_pipeline_dnt_w() -> None:
    """DnT per band (T = 0,5 s) fed to weighted_rating gives DnT,w."""
    l2 = np.array([float(80 - r) for r in _REF_THIRD])  # D = ref
    l1 = np.full(16, 80.0)
    t2 = np.full(16, 0.5)
    res = airborne_insulation(l1, l2, t2)
    rating = weighted_rating(res.dnt)
    # D == reference curve => rating 54 (2 dB up, sum 32,0).
    assert rating.rating == 54
