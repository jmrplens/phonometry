#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the ISO 2631-5:2018 multiple-shock model (Clause 5 + Annex C).

Validated against the standard's own Annex C worked example and the Annex D
digital-filter realization of the seat-to-spine transfer function.
"""

from __future__ import annotations

import numpy as np
import pytest
from reference_data import (
    ISO2631_5_DZD_MALE,
    ISO2631_5_PI_MALE,
    ISO2631_5_R_MALE,
)
from scipy.signal import freqz

from phonometry import iso2631_5 as v

# Annex D digital filter coefficients for fs = 256 Hz (Table D.1).
_ANNEX_D_B = [
    -0.000005710, 0.000020010, 0.001373900, 0.014541920, 0.025152310,
    -0.014242050, -0.044262840, -0.008888510, 0.017715720, 0.010216420,
    0.002030740, 0.000055980,
]
_ANNEX_D_A = [
    1.000000000, -3.323217600, 4.256126150, -1.980417270, -1.488735470,
    3.329511290, -2.949072140, 1.653403410, -0.635677800, 0.167519420,
    -0.028076980, 0.002348730,
]


# ---------------------------------------------------------------------------
# Clause 5.2 - seat-to-spine transfer function.
# ---------------------------------------------------------------------------


def test_transfer_unity_at_dc() -> None:
    # The transmissibility of the spine model is 1.0 at 0 Hz (clause 5.2 note).
    assert v.seat_to_spine_transfer([0.0])[0] == pytest.approx(1.0)


def test_transfer_matches_annex_d_filter() -> None:
    # Formula 1 must reproduce the Annex D 256-Hz digital realization within the
    # clause 5.2 magnitude tolerance (+/-0.04 up to 40 Hz, +/-0.08 to 80 Hz).
    freqs = np.array([0.5, 2.0, 5.0, 10.0, 20.0, 40.0, 60.0, 80.0])
    formula = np.abs(v.seat_to_spine_transfer(freqs))
    _, h = freqz(_ANNEX_D_B, _ANNEX_D_A, worN=2.0 * np.pi * freqs / 256.0)
    assert np.max(np.abs(formula - np.abs(h))) < 0.04


# ---------------------------------------------------------------------------
# Clause 5.3 - response peaks and acceleration dose.
# ---------------------------------------------------------------------------


def test_response_peaks_positive_only() -> None:
    # One positive peak per cycle; negative excursions are ignored.
    t = np.linspace(0.0, 1.0, 2001)
    peaks = v.response_peaks(np.sin(2.0 * np.pi * 5.0 * t))
    assert peaks.size == 5
    assert np.allclose(peaks, 1.0, atol=1e-3)


def test_response_peaks_takes_segment_maximum() -> None:
    # Within a positive run only the maximum is a peak; the sign flip closes it.
    sig = [0.0, 1.0, 3.0, 2.0, -1.0, -4.0, 5.0, 1.0]
    assert np.allclose(v.response_peaks(sig), [3.0, 5.0])


def test_dose_from_peaks_formula_3() -> None:
    # Dz = 1.07 * (sum Az_i**6)**(1/6); the Annex C example uses 5 x 40 m/s2.
    dz = v.dose_from_peaks([40.0] * 5)
    assert dz == pytest.approx(1.07 * (5.0 * 40.0**6) ** (1.0 / 6.0))
    assert dz == pytest.approx(ISO2631_5_DZD_MALE, abs=0.01)


def test_dose_dominated_by_largest_peak() -> None:
    # A peak three times smaller barely contributes to the 6th-power dose.
    base = v.dose_from_peaks([40.0])
    with_small = v.dose_from_peaks([40.0, 13.0])
    assert with_small == pytest.approx(base, rel=1e-3)


def test_acceleration_dose_through_filter() -> None:
    # spinal_response then peak picking then Formula 3 is what acceleration_dose does.
    rng = np.random.default_rng(1)
    az = rng.standard_normal(2560)
    response = v.spinal_response(az, 256.0)
    manual = v.dose_from_peaks(v.response_peaks(response))
    assert v.acceleration_dose(az, 256.0) == pytest.approx(manual)


def test_spinal_response_matches_manual_fft() -> None:
    az = np.zeros(512)
    az[10] = 5.0
    spec = np.fft.rfft(az)
    freq = np.fft.rfftfreq(az.size, d=1.0 / 256.0)
    manual = np.fft.irfft(spec * v.seat_to_spine_transfer(freq), n=az.size)
    assert np.allclose(v.spinal_response(az, 256.0), manual)


# ---------------------------------------------------------------------------
# Clause 5.3 - daily dose (Formulae 4 and 5).
# ---------------------------------------------------------------------------


def test_daily_dose_equal_times_is_identity() -> None:
    assert v.daily_dose(50.0, 8.0, 8.0) == pytest.approx(50.0)


def test_daily_dose_scaling() -> None:
    assert v.daily_dose(50.0, 8.0, 2.0) == pytest.approx(50.0 * (8.0 / 2.0) ** (1.0 / 6.0))


def test_daily_dose_multi_matches_single() -> None:
    # A single condition with td = tm reduces to Dz.
    assert v.daily_dose_multi([50.0], [4.0], [4.0]) == pytest.approx(50.0)
    combined = v.daily_dose_multi([50.0, 30.0], [8.0, 4.0], [4.0, 4.0])
    expected = (50.0**6 * 2.0 + 30.0**6 * 1.0) ** (1.0 / 6.0)
    assert combined == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Annex C - health-effect assessment (worked example).
# ---------------------------------------------------------------------------


def test_ultimate_strength_formula_c4() -> None:
    # Su = 6.75 - Sage*(b+i); male Sage = 0.052.
    assert float(v.ultimate_strength(20.0, sex="male")) == pytest.approx(6.75 - 0.052 * 20.0)
    assert float(v.ultimate_strength(20.0, sex="female")) == pytest.approx(6.75 - 0.039 * 20.0)


def test_annex_c_male_worked_example() -> None:
    # 5 x 40 m/s2, 82 kg male, b = 20, n = 20, N = 120: R = 1.22, Pi = 0.37.
    dz = v.dose_from_peaks([40.0] * 5)
    sd = v.compression_dose(dz, mz=v.MZ_MALE)
    assert sd == pytest.approx(0.029 * ISO2631_5_DZD_MALE, abs=1e-3)
    r = v.injury_risk(sd, start_age=20, years=20, days_per_year=120, sex="male")
    assert r == pytest.approx(ISO2631_5_R_MALE, abs=0.01)
    pi = v.injury_probability(r, sex="male")
    assert pi == pytest.approx(ISO2631_5_PI_MALE, abs=0.01)


def test_annex_c_female_worked_example() -> None:
    # Same exposure, 64 kg female: Sd ~ 1.40 MPa, R ~ 0.97 (Annex C note 5).
    dz = v.dose_from_peaks([40.0] * 5)
    sd = v.compression_dose(dz, mz=v.MZ_FEMALE)
    assert sd == pytest.approx(1.40, abs=0.01)
    r = v.injury_risk(sd, start_age=20, years=20, days_per_year=120, sex="female")
    assert r == pytest.approx(0.97, abs=0.02)


def test_static_stress_male() -> None:
    # Sstat = mz * 9.81; the exact product is 0.284 MPa (the standard's Annex C
    # text rounds this to 0.281, but the worked R = 1.22 uses the exact value).
    assert v.static_stress(v.MZ_MALE) == pytest.approx(v.MZ_MALE * v.GRAVITY)
    assert v.static_stress(v.MZ_MALE) == pytest.approx(0.284, abs=1e-3)


def test_injury_probability_bounds_and_monotonic() -> None:
    assert v.injury_probability(0.0) == 0.0
    assert v.injury_probability(-1.0) == 0.0
    probs = [v.injury_probability(r, sex="male") for r in (0.5, 1.0, 2.0, 4.0)]
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert probs == sorted(probs)


def test_injury_probability_at_thresholds() -> None:
    # Table C.2: the R for 10 / 50 / 90 % risk should map back to those risks.
    for r_val, expected in zip(v.RISK_THRESHOLDS_MALE, (0.10, 0.50, 0.90)):
        assert v.injury_probability(r_val, sex="male") == pytest.approx(expected, abs=0.02)


# ---------------------------------------------------------------------------
# High-level assessment and validation.
# ---------------------------------------------------------------------------


def test_multiple_shock_assessment_end_to_end() -> None:
    az = np.zeros(2560)
    az[::400] = 60.0
    result = v.multiple_shock_assessment(
        az, 256.0, start_age=20, years=20, days_per_year=120, sex="male"
    )
    assert result.sex == "male"
    assert result.acceleration_dose > 0.0
    assert 0.0 <= result.probability <= 1.0
    assert result.risk_thresholds == v.RISK_THRESHOLDS_MALE
    assert result.peaks.size > 0


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="fs must be positive"):
        v.spinal_response([1.0, 2.0], 0.0)
    with pytest.raises(ValueError, match="empty"):
        v.spinal_response([], 256.0)
    with pytest.raises(ValueError, match="positive"):
        v.daily_dose(50.0, 8.0, 0.0)
    with pytest.raises(ValueError, match="must match"):
        v.daily_dose_multi([1.0, 2.0], [1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="years must be"):
        v.injury_risk(1.0, start_age=20, years=0, days_per_year=120)
    with pytest.raises(ValueError, match="sex must be"):
        v.injury_probability(1.0, sex="other")


def test_injury_risk_rejects_exhausted_strength() -> None:
    # By ~age 125 the male ultimate strength minus static stress goes negative.
    with pytest.raises(ValueError, match="non-positive"):
        v.injury_risk(1.0, start_age=20, years=120, days_per_year=120, sex="male")
