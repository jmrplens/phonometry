#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for :mod:`phonometry.iso1999` (noise-induced hearing loss).

Validated against the worked examples of ISO 1999:2013 Annex D (Tables D.1 to
D.4), which tabulate the NIPTS in dB for the six audiometric frequencies, four
exposure levels (85, 90, 95, 100 dB), four durations (10, 20, 30, 40 years) and
the 90 % / 50 % / 10 % fractiles. In the standard's notation the percentage is
the fraction of the population with worse hearing, so its 10 % column is the
most-susceptible tenth (fractile 0.9 here) and its 90 % column the least
(fractile 0.1).
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import iso1999 as m

# Annex D, per (level, years): rows are the six frequencies 500..6000 Hz,
# columns the (90 %, 50 %, 10 %) fractiles -> here (0.10, 0.50, 0.90).
_ANNEX_D = {
    (85.0, 40.0): [(0, 0, 0), (0, 0, 0), (1, 2, 2), (3, 5, 7), (5, 7, 9), (2, 4, 6)],
    (90.0, 20.0): [(0, 0, 0), (0, 0, 0), (2, 4, 8), (7, 10, 16), (9, 13, 18), (4, 8, 14)],
    (95.0, 10.0): [(0, 0, 1), (1, 2, 4), (0, 5, 13), (8, 16, 25), (13, 20, 27), (5, 14, 23)],
    (100.0, 40.0): [(5, 7, 11), (8, 11, 19), (16, 24, 39), (29, 38, 60),
                    (30, 41, 56), (19, 30, 48)],
}


@pytest.mark.parametrize(("key", "expected"), _ANNEX_D.items())
def test_nipts_matches_annex_d(key: tuple[float, float], expected: list) -> None:
    l_ex, years = key
    got = np.column_stack([
        np.round(m.nipts(l_ex, years, frac).value).astype(int)
        for frac in (0.10, 0.50, 0.90)
    ])
    np.testing.assert_array_equal(got, np.array(expected))


def test_median_formula_2_by_hand() -> None:
    # 4000 Hz, 20 years, 90 dB: N50 = (u + v*lg t)*(L - L0)^2
    # = (0.025 + 0.025*log10(20)) * (90 - 75)^2 = 12.94 dB.
    r = m.nipts(90.0, 20.0, 0.5)
    assert r.median[4] == pytest.approx(12.9435, abs=1e-3)
    assert r.frequencies[4] == 4000.0


def test_level_below_cutoff_gives_zero() -> None:
    # At 85 dB the 500 Hz (L0 = 93) and 1000 Hz (L0 = 89) bands are below the
    # cut-off, so the NIPTS is zero at every fractile.
    for frac in (0.1, 0.5, 0.9):
        r = m.nipts(85.0, 30.0, frac)
        assert r.value[0] == 0.0  # 500 Hz
        assert r.value[1] == 0.0  # 1000 Hz


def test_fractile_ordering_and_median() -> None:
    # The median is the 0.5 fractile; higher fractile => larger (worse) NIPTS.
    low = m.nipts(95.0, 30.0, 0.1).value
    mid = m.nipts(95.0, 30.0, 0.5).value
    high = m.nipts(95.0, 30.0, 0.9).value
    np.testing.assert_allclose(mid, m.nipts(95.0, 30.0, 0.5).median)
    assert np.all(low <= mid) and np.all(mid <= high)


def test_negative_nipts_clamped_to_zero() -> None:
    # For short durations the lower-fractile NIPTS can go negative and must be
    # clamped to zero (clause 6.3.2).
    r = m.nipts(90.0, 1.0, 0.05)
    assert np.all(r.value >= 0.0)


def test_short_duration_extrapolation() -> None:
    # Formula (3): N50(t<10) = lg(t+1)/lg(11) * N50(t=10).
    n50_10 = m.nipts(95.0, 10.0, 0.5).median
    n50_5 = m.nipts(95.0, 5.0, 0.5).median
    factor = np.log10(5.0 + 1.0) / np.log10(11.0)
    np.testing.assert_allclose(n50_5, factor * n50_10, rtol=1e-9)


def test_htlan_formula_1() -> None:
    # H' = H + N - H*N/120 at each frequency (clause 6.1).
    r = m.htlan(60, "male", 90.0, 30.0, 0.5)
    expected = r.htla + r.nipts - r.htla * r.nipts / 120.0
    np.testing.assert_allclose(r.threshold, expected)
    # The combined threshold is at least the age component alone.
    assert np.all(r.threshold >= r.htla - 1e-9)


def test_htlan_matches_components() -> None:
    r = m.htlan(50, "female", 100.0, 20.0, 0.9)
    np.testing.assert_allclose(
        r.nipts, m.nipts(100.0, 20.0, 0.9).value)


def test_frequency_subset() -> None:
    r = m.nipts(95.0, 20.0, 0.5, frequencies=[4000.0, 6000.0])
    full = m.nipts(95.0, 20.0, 0.5)
    np.testing.assert_allclose(r.frequencies, [4000.0, 6000.0])
    np.testing.assert_allclose(r.value, full.value[[4, 5]])


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="years must be positive"):
        m.nipts(90.0, 0.0)
    with pytest.raises(ValueError, match="fractile"):
        m.nipts(90.0, 20.0, 1.5)
    with pytest.raises(ValueError, match="not an ISO 1999"):
        m.nipts(90.0, 20.0, frequencies=[1234.0])
    with pytest.raises(ValueError, match="at least 18"):
        m.htlan(10, "male", 90.0, 20.0)


def test_plots_return_axes() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    assert isinstance(m.nipts(95.0, 20.0, 0.9).plot(), plt.Axes)
    assert isinstance(m.htlan(60, "male", 95.0, 20.0, 0.9).plot(), plt.Axes)
    plt.close("all")
