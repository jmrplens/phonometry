#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for ISO 11654:1997 single-number sound absorption rating (alpha_w).

Validation strategy: the standard's own numbers, not self-consistency.

- The weighted coefficient, shape indicator and unfavourable-deviation sum
  are checked against the two worked examples of Annex A: Figure A.1
  (alpha_w = 0.60, no indicator, shift 0.40, Sigma unfav = 0.05) and
  Figure A.2 (alpha_w = 0.60(M), same shift, the 500 Hz band exceeding the
  shifted reference by 0.40 >= 0.25).
- The practical-coefficient rounding of Clause 4.1 is checked against the
  NOTE example (0.92 -> 0.90) and the neighbouring 0,05-grid boundaries,
  and the 1,00 cap for reverberation-room means above unity.
- The Table B.1 (Annex B) class boundaries are exercised at each edge.
- A perfect absorber (all alpha_p = 1.00) needs no shift; a weak absorber
  drives the shift loop until Clause 4.2 is satisfied.
- Mapping and sequence inputs agree; the result exposes the measured curve,
  the shifted reference and the band centres for plotting.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry.absorption_rating import (
    OCTAVE_BANDS_HZ,
    REFERENCE_CURVE,
    THIRD_OCTAVE_BANDS_HZ,
    AbsorptionRatingResult,
    absorption_class,
    practical_absorption_coefficient,
    weighted_absorption,
)

# ISO 11654:1997 Annex A worked examples (the "Absorber" alpha_p columns).
# Bands 250, 500, 1000, 2000, 4000 Hz (the 125 Hz row is not rated).
_ANNEX_A1_ALPHA_P = [0.35, 0.70, 0.65, 0.60, 0.55]
_ANNEX_A2_ALPHA_P = [0.35, 1.00, 0.65, 0.60, 0.55]
# The tabulated shifted reference curve (shift s = 0.40) shared by both.
_ANNEX_A_SHIFTED_REF = [0.40, 0.60, 0.60, 0.60, 0.50]


def _almost(a: float, b: float, eps: float = 1e-9) -> bool:
    """0,05-grid equality via magnitude, never float ``==``."""
    return abs(a - b) < eps


# --- fixed reference data -------------------------------------------------


def test_reference_curve_verbatim() -> None:
    assert REFERENCE_CURVE == {250: 0.80, 500: 1.00, 1000: 1.00, 2000: 1.00, 4000: 0.90}


def test_band_layout() -> None:
    assert OCTAVE_BANDS_HZ == (250, 500, 1000, 2000, 4000)
    assert len(THIRD_OCTAVE_BANDS_HZ) == 15
    # Each octave centre is the middle of its one-third-octave triple.
    for i, octave in enumerate(OCTAVE_BANDS_HZ):
        assert THIRD_OCTAVE_BANDS_HZ[3 * i + 1] == octave


# --- Annex A oracles ------------------------------------------------------


def test_annex_a1_no_indicator() -> None:
    res = weighted_absorption(_ANNEX_A1_ALPHA_P)
    assert _almost(res.alpha_w, 0.60)
    assert res.shape_indicator == ""
    assert _almost(res.shift, 0.40)
    assert _almost(res.unfavourable_sum, 0.05)
    assert res.absorption_class == "C"
    assert res.rating_label == "0.60"
    np.testing.assert_allclose(res.shifted_reference, _ANNEX_A_SHIFTED_REF)


def test_annex_a2_shape_indicator_m() -> None:
    res = weighted_absorption(_ANNEX_A2_ALPHA_P)
    assert _almost(res.alpha_w, 0.60)
    assert res.shape_indicator == "M"
    assert _almost(res.shift, 0.40)
    assert _almost(res.unfavourable_sum, 0.05)
    assert res.absorption_class == "C"
    assert res.rating_label == "0.60(M)"
    np.testing.assert_allclose(res.shifted_reference, _ANNEX_A_SHIFTED_REF)


def test_annex_a_unfavourable_sum_within_budget() -> None:
    for alpha_p in (_ANNEX_A1_ALPHA_P, _ANNEX_A2_ALPHA_P):
        res = weighted_absorption(alpha_p)
        assert res.unfavourable_sum <= 0.10 + 1e-9


def test_shift_is_the_smallest_qualifying_one() -> None:
    # At the shift one step smaller (s = 0.35) the unfavourable sum is 0.15,
    # over the 0.10 budget, so s = 0.40 is the first that qualifies (A.1).
    res = weighted_absorption(_ANNEX_A1_ALPHA_P)
    ref_units = [16, 20, 20, 20, 18]
    meas_units = [7, 14, 13, 12, 11]
    smaller = sum(max(0, (r - 7) - m) for r, m in zip(ref_units, meas_units))
    assert smaller / 20.0 > 0.10
    assert _almost(res.shift, 0.40)


# --- Clause 4.1 rounding --------------------------------------------------


@pytest.mark.parametrize(
    ("mean", "expected"),
    [
        (0.92, 0.90),  # NOTE example: 0,92 -> 0,90
        (0.93, 0.95),  # up
        (0.97, 0.95),  # down
        (0.98, 1.00),  # up into the cap band
        (0.90, 0.90),  # already on grid
        (0.31, 0.30),  # nearest 0,05 below
        (0.325, 0.35),  # half rounds up
        (0.00, 0.00),
    ],
)
def test_practical_rounding_note(mean: float, expected: float) -> None:
    # Feed three identical one-third octaves so the octave mean equals `mean`.
    alpha_s = [mean] * 15
    alpha_p = practical_absorption_coefficient(alpha_s)
    assert all(_almost(v, expected) for v in alpha_p)


def test_practical_capped_at_unity() -> None:
    # Reverberation-room alpha_s can exceed 1,00; the octave mean is capped.
    alpha_s = [1.20] * 15
    alpha_p = practical_absorption_coefficient(alpha_s)
    assert all(_almost(v, 1.00) for v in alpha_p)


def test_practical_mean_of_three() -> None:
    # 250 Hz octave from thirds 0.10, 0.20, 0.30 -> mean 0.20 -> 0.20.
    alpha_s = [0.10, 0.20, 0.30] + [0.50] * 12
    alpha_p = practical_absorption_coefficient(alpha_s)
    assert _almost(alpha_p[0], 0.20)
    assert _almost(alpha_p[1], 0.50)


def test_practical_rejects_negative() -> None:
    with pytest.raises(ValueError):
        practical_absorption_coefficient([-0.1] + [0.5] * 14)


def test_practical_wrong_length() -> None:
    with pytest.raises(ValueError):
        practical_absorption_coefficient([0.5] * 14)


def test_practical_mapping_matches_sequence() -> None:
    seq = [0.10 + 0.05 * i for i in range(15)]
    mapping = dict(zip(THIRD_OCTAVE_BANDS_HZ, seq))
    np.testing.assert_allclose(
        practical_absorption_coefficient(mapping),
        practical_absorption_coefficient(seq),
    )


# --- Table B.1 class boundaries ------------------------------------------


@pytest.mark.parametrize(
    ("alpha_w", "letter"),
    [
        (1.00, "A"),
        (0.95, "A"),
        (0.90, "A"),
        (0.85, "B"),
        (0.80, "B"),
        (0.75, "C"),
        (0.60, "C"),
        (0.55, "D"),
        (0.30, "D"),
        (0.25, "E"),
        (0.15, "E"),
        (0.10, "Not classified"),
        (0.00, "Not classified"),
    ],
)
def test_absorption_class_boundaries(alpha_w: float, letter: str) -> None:
    assert absorption_class(alpha_w) == letter


# --- shift loop extremes --------------------------------------------------


def test_perfect_absorber_no_shift() -> None:
    res = weighted_absorption([1.00, 1.00, 1.00, 1.00, 1.00])
    assert _almost(res.alpha_w, 1.00)
    assert _almost(res.shift, 0.00)
    assert res.absorption_class == "A"
    assert res.shape_indicator == ""
    np.testing.assert_allclose(res.shifted_reference, [0.80, 1.00, 1.00, 1.00, 0.90])


def test_weak_absorber_drives_shift() -> None:
    # A curve well below the reference forces the loop to shift far down.
    res = weighted_absorption([0.10, 0.10, 0.10, 0.10, 0.10])
    # Reference 1.00 at 500 Hz must drop to within 0.10 total of measured.
    assert res.alpha_w <= 0.15
    assert res.unfavourable_sum <= 0.10 + 1e-9
    assert res.shift > 0.0


def test_curve_needing_shift_from_reference() -> None:
    # Exactly the reference-shaped curve one notch low: unfav > 0.10 at s=0.
    res = weighted_absorption([0.80, 0.90, 0.90, 0.90, 0.80])
    assert res.shift > 0.0
    assert res.unfavourable_sum <= 0.10 + 1e-9


# --- result plumbing ------------------------------------------------------


def test_result_is_frozen() -> None:
    res = weighted_absorption(_ANNEX_A1_ALPHA_P)
    assert isinstance(res, AbsorptionRatingResult)
    with pytest.raises(AttributeError):
        res.alpha_w = 0.0  # type: ignore[misc]


def test_result_exposes_curves_for_plotting() -> None:
    res = weighted_absorption(_ANNEX_A1_ALPHA_P)
    np.testing.assert_allclose(res.band_centers, OCTAVE_BANDS_HZ)
    np.testing.assert_allclose(res.measured, _ANNEX_A1_ALPHA_P)
    assert res.measured.shape == res.shifted_reference.shape == res.band_centers.shape


def test_weighted_mapping_matches_sequence() -> None:
    mapping = dict(zip(OCTAVE_BANDS_HZ, _ANNEX_A2_ALPHA_P))
    res_map = weighted_absorption(mapping)
    res_seq = weighted_absorption(_ANNEX_A2_ALPHA_P)
    assert _almost(res_map.alpha_w, res_seq.alpha_w)
    assert res_map.shape_indicator == res_seq.shape_indicator


def test_end_to_end_from_third_octaves() -> None:
    # Build a 15-band alpha_s whose octave means reproduce the A.1 alpha_p,
    # then rate it: identical alpha_w to feeding alpha_p directly.
    alpha_s = []
    for value in _ANNEX_A1_ALPHA_P:
        alpha_s.extend([value, value, value])
    alpha_p = practical_absorption_coefficient(alpha_s)
    res = weighted_absorption(alpha_p)
    assert _almost(res.alpha_w, 0.60)
    assert res.shape_indicator == ""


def test_weighted_absorption_rejects_multidimensional_input() -> None:
    # A wrongly-shaped (3, 5) array must not be silently flattened (CodeRabbit).
    with pytest.raises(ValueError, match="1-D"):
        weighted_absorption(np.zeros((3, 5)))


def test_weighted_absorption_rejects_non_finite() -> None:
    # NaN/inf must fail fast with a clear message, not a cryptic downstream error.
    with pytest.raises(ValueError, match="finite"):
        weighted_absorption([0.35, float("nan"), 0.65, 0.60, 0.55])
    with pytest.raises(ValueError, match="finite"):
        weighted_absorption({250: 0.35, 500: float("inf"), 1000: 0.65,
                             2000: 0.60, 4000: 0.55})


def test_plot_smoke() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = weighted_absorption(_ANNEX_A2_ALPHA_P)
    ax = res.plot()
    assert ax.get_ylabel() == "Sound absorption coefficient"


def test_public_exports() -> None:
    import phonometry

    for name in (
        "AbsorptionRatingResult", "OCTAVE_BANDS_HZ", "REFERENCE_CURVE",
        "THIRD_OCTAVE_BANDS_HZ", "absorption_class",
        "practical_absorption_coefficient", "weighted_absorption",
    ):
        assert hasattr(phonometry, name), name
