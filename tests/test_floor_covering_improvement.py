#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for ISO 16251-1:2014 floor-covering impact-sound improvement."""

from __future__ import annotations

import numpy as np
import pytest

import reference_data as ref
from phonometry import (
    acceleration_level,
    background_corrected_level,
    impact_improvement,
    improvement_octave_bands,
    weighted_impact_improvement,
    weighted_impact_rating,
)


# ---------------------------------------------------------------------------
# ISO 717-2 reference floor anchor (the numeric oracle)
# ---------------------------------------------------------------------------
def test_reference_floor_rating_is_78() -> None:
    """weighted_impact_rating of the ISO 717-2 Table 4 reference floor is 78 dB."""
    res = weighted_impact_rating(ref.ISO717_2_REFERENCE_FLOOR_LN_R0)
    assert res.rating == ref.ISO717_2_REFERENCE_FLOOR_LN_R0_W
    assert res.ci == ref.ISO717_2_REFERENCE_FLOOR_CI


def test_zero_improvement_gives_zero_delta_lw() -> None:
    assert weighted_impact_improvement(np.zeros(16)) == 0


def test_flat_improvement_shifts_delta_lw_one_for_one() -> None:
    # A uniform ΔL lowers Ln,r uniformly, so ΔLw equals the flat improvement.
    assert weighted_impact_improvement(np.full(16, 10.0)) == 10


def test_weighted_improvement_requires_16_bands() -> None:
    with pytest.raises(ValueError, match="16 one-third-octave"):
        weighted_impact_improvement(np.zeros(5))


def test_weighted_improvement_rejects_non_finite() -> None:
    bad = np.zeros(16)
    bad[0] = np.inf
    with pytest.raises(ValueError, match="finite"):
        weighted_impact_improvement(bad)


# ---------------------------------------------------------------------------
# Formula (1) - acceleration level
# ---------------------------------------------------------------------------
def test_acceleration_level_formula_1() -> None:
    # 20 lg(1e-3 / 1e-6) = 20 * 3 = 60 dB.
    np.testing.assert_allclose(acceleration_level(1e-3), [60.0])
    np.testing.assert_allclose(acceleration_level([1e-6, 1e-5]), [0.0, 20.0])


def test_acceleration_level_rejects_nonpositive() -> None:
    with pytest.raises(ValueError, match="positive"):
        acceleration_level(0.0)
    with pytest.raises(ValueError, match="'reference' must be positive"):
        acceleration_level(1e-3, reference=0.0)


# ---------------------------------------------------------------------------
# Formula (2) - background correction
# ---------------------------------------------------------------------------
def test_background_correction_three_branches() -> None:
    # margin 30 (>=15, unchanged), 10 (6..15, energy subtraction), 3 (<6, limit).
    lp = np.array([80.0, 80.0, 65.0])
    lb = np.array([50.0, 70.0, 62.0])
    corrected, limited = background_corrected_level(lp, lb)
    expected_mid = 10.0 * np.log10(10.0 ** 8 - 10.0 ** 7)  # ~79.54
    np.testing.assert_allclose(corrected, [80.0, expected_mid, 65.0 - 1.3])
    np.testing.assert_array_equal(limited, [False, False, True])


def test_background_correction_boundary_at_6_subtracts() -> None:
    # ISO 16251-1 (unlike ISO 10140-4) energy-subtracts at exactly margin = 6 dB.
    corrected, limited = background_corrected_level([56.0], [50.0])
    np.testing.assert_allclose(corrected, [10.0 * np.log10(10.0 ** 5.6 - 10.0 ** 5.0)])
    assert not bool(limited[0])


def test_background_correction_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="share their shape"):
        background_corrected_level([80.0, 70.0], [50.0])


# ---------------------------------------------------------------------------
# Formulae (3)/(4) - improvement
# ---------------------------------------------------------------------------
def test_impact_improvement_difference_and_rating() -> None:
    freqs = ref.ISO717_2_REFERENCE_FLOOR_FREQ
    bare = np.full(16, 75.0)
    cov = bare - np.array(
        [0, 0, 1, 2, 4, 7, 11, 15, 18, 21, 23, 25, 27, 28, 29, 30], dtype=float
    )
    res = impact_improvement(bare, cov, freqs)
    np.testing.assert_allclose(
        res.improvement, [0, 0, 1, 2, 4, 7, 11, 15, 18, 21, 23, 25, 27, 28, 29, 30]
    )
    # ΔLw computed automatically for the 16 rating bands.
    assert res.delta_lw == weighted_impact_improvement(res.improvement)
    assert not bool(np.any(res.limited))


def test_impact_improvement_with_background_flags_limited() -> None:
    freqs = [500.0, 1000.0]
    bare = np.array([80.0, 80.0])
    cov = np.array([70.0, 79.0])
    bg = np.array([50.0, 79.5])  # 2nd band: signal within 6 dB of background
    res = impact_improvement(bare, cov, freqs, background=bg)
    assert bool(res.limited[1])
    assert res.delta_lw is None  # not the 16 rating bands


def test_impact_improvement_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="share their shape"):
        impact_improvement([75.0, 75.0], [70.0], [500.0, 1000.0])


def test_impact_improvement_per_position_averages_after_difference() -> None:
    # Two tapping positions, two bands; no background => ΔL is the mean over
    # positions of (L0 - L1).
    freqs = [500.0, 1000.0]
    l0 = np.array([[80.0, 78.0], [82.0, 76.0]])
    l1 = np.array([[70.0, 70.0], [74.0, 66.0]])
    res = impact_improvement(l0, l1, freqs)
    np.testing.assert_allclose(res.improvement, [(10 + 8) / 2, (8 + 10) / 2])
    assert res.improvement.shape == (2,)


def test_background_correction_precedes_averaging() -> None:
    # Formula (2) is non-linear, so per-position correction then averaging must
    # differ from averaging then correcting when margins are heterogeneous.
    freqs = [500.0]
    l0 = np.array([[80.0], [80.0]])
    l1 = np.array([[62.0], [80.0]])  # pos 1 close to background, pos 2 not
    bg = np.array([60.0])            # margins: L1 pos1 = 2 dB (<6 -> limit)
    res = impact_improvement(l0, l1, freqs, background=bg)
    assert bool(res.limited[0])  # a position hit the 1.3 dB limit
    # Averaging-then-correcting would miss that per-position limit flag.


def test_impact_improvement_background_shape_validation() -> None:
    with pytest.raises(ValueError, match="'background' must be"):
        impact_improvement(
            np.full((2, 2), 80.0), np.full((2, 2), 70.0), [500.0, 1000.0],
            background=np.full((3, 2), 50.0),
        )


# ---------------------------------------------------------------------------
# Formula (5) - octave conversion
# ---------------------------------------------------------------------------
def test_octave_conversion_formula_5() -> None:
    freqs = [400.0, 500.0, 630.0]  # the 500 Hz octave triplet
    dl = np.array([10.0, 10.0, 10.0])
    oct_f, oct_dl = improvement_octave_bands(dl, freqs)
    np.testing.assert_allclose(oct_f, [500.0])
    # Equal thirds => octave equals the common value.
    np.testing.assert_allclose(oct_dl, [10.0])


def test_octave_conversion_energy_mean() -> None:
    freqs = [400.0, 500.0, 630.0]
    dl = np.array([6.0, 10.0, 14.0])
    _, oct_dl = improvement_octave_bands(dl, freqs)
    expected = -10.0 * np.log10(
        np.mean([10.0 ** (-6 / 10), 10.0 ** (-10 / 10), 10.0 ** (-14 / 10)])
    )
    np.testing.assert_allclose(oct_dl, [expected])


# ---------------------------------------------------------------------------
# Result helpers / plotting
# ---------------------------------------------------------------------------
def test_result_octave_bands_method() -> None:
    freqs = ref.ISO717_2_REFERENCE_FLOOR_FREQ
    bare = np.full(16, 75.0)
    res = impact_improvement(bare, bare - 5.0, freqs)
    oct_f, oct_dl = res.octave_bands()
    assert oct_f.tolist() == [125.0, 250.0, 500.0, 1000.0, 2000.0]
    np.testing.assert_allclose(oct_dl, np.full(5, 5.0))


def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    freqs = ref.ISO717_2_REFERENCE_FLOOR_FREQ
    bare = np.full(16, 75.0)
    res = impact_improvement(bare, bare - 8.0, freqs)
    ax = res.plot()
    assert ax.get_title().startswith("ISO 16251-1")
