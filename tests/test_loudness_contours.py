#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Normal equal-loudness-level contours (ISO 226:2023).

Formula (1) (clause 4.1, p. 2) derives the SPL of a pure tone from its
loudness level; Formula (2) (clause 4.2, p. 3) is the inverse. Both use the
Table 1 (p. 4) parameters (alpha_f, L_U, T_f) at the 29 preferred
third-octave frequencies. Validity (clause 4.1): 20 phon up to 90 phon for
20 Hz - 4 kHz and up to 80 phon for 5 kHz - 12.5 kHz. Expected values below
are spot checks from the informative Annex B tables (pp. 6-8), which are
rounded to 0.1 dB / 0.1 phon.
"""

import numpy as np
import pytest
from reference_data import ISO226_2023_TABLE_B1_ANCHOR

from phonometry import equal_loudness_contour, hearing_threshold, loudness_level

# (phon, frequency Hz, expected SPL dB) - ISO 226:2023 Table B.1. The
# (60 phon, 100 Hz) anchor is imported from tests/reference_data.py (shared
# with the CI conformance report) so the two copies cannot drift.
TABLE_B1 = [
    (20, 20.0, 89.5), (20, 1000.0, 20.0), (20, 12500.0, 33.0),
    (40, 20.0, 99.7), (40, 63.0, 73.0), (40, 250.0, 50.3),
    (40, 1000.0, 40.0), (40, 4000.0, 36.7), (40, 8000.0, 51.6),
    ISO226_2023_TABLE_B1_ANCHOR, (60, 500.0, 62.1), (60, 2000.0, 60.0),
    (80, 20.0, 118.9), (80, 1000.0, 80.0), (80, 12500.0, 85.6),
    (90, 20.0, 123.6), (90, 4000.0, 88.8),
]

# (SPL dB, frequency Hz, expected phon) - ISO 226:2023 Table B.2
TABLE_B2 = [
    (60.0, 63.0, 21.6), (40.0, 1000.0, 40.0),
    (80.0, 8000.0, 68.6), (90.0, 20.0, 20.8),
    (70.0, 400.0, 67.1), (50.0, 3150.0, 53.9),
]


@pytest.mark.parametrize(("phon", "freq", "expected"), TABLE_B1)
def test_contour_matches_annex_b1(phon: float, freq: float, expected: float) -> None:
    freqs, spl = equal_loudness_contour(phon)
    idx = int(np.argmin(np.abs(freqs - freq)))
    assert freqs[idx] == pytest.approx(freq)
    assert spl[idx] == pytest.approx(expected, abs=0.05)


@pytest.mark.parametrize(("spl", "freq", "expected"), TABLE_B2)
def test_loudness_level_matches_annex_b2(spl: float, freq: float, expected: float) -> None:
    assert loudness_level(spl, freq) == pytest.approx(expected, abs=0.05)


def test_identity_at_1khz() -> None:
    """3.3: at 1 kHz the loudness level equals the SPL by definition."""
    for phon in (20.0, 47.3, 90.0):
        freqs, spl = equal_loudness_contour(phon)
        assert spl[freqs == 1000.0][0] == pytest.approx(phon, abs=1e-9)


def test_roundtrip() -> None:
    freqs, spl = equal_loudness_contour(55.0)
    back = [loudness_level(s, f) for f, s in zip(freqs, spl, strict=True)]
    np.testing.assert_allclose(back, 55.0, atol=1e-9)


def test_validity_limits() -> None:
    """Clause 4.1: 20-90 phon; above 80 phon only 20 Hz - 4 kHz remains."""
    with pytest.raises(ValueError, match="phon"):
        equal_loudness_contour(19.0)
    with pytest.raises(ValueError, match="phon"):
        equal_loudness_contour(91.0)
    freqs80, _ = equal_loudness_contour(80.0)
    freqs81, _ = equal_loudness_contour(81.0)
    assert freqs80.max() == 12500.0
    assert freqs81.max() == 4000.0


def test_untabulated_frequency_raises() -> None:
    """Table 1 defines parameters only at the 29 preferred frequencies; the
    standard specifies no interpolation between them."""
    with pytest.raises(ValueError, match="frequency"):
        loudness_level(60.0, 440.0)


def test_hearing_threshold_is_table1_tf() -> None:
    freqs, tf = hearing_threshold()
    assert len(freqs) == 29
    assert tf[freqs == 20.0][0] == pytest.approx(78.1)
    assert tf[freqs == 1000.0][0] == pytest.approx(2.4)
    assert tf[freqs == 3150.0][0] == pytest.approx(-6.0)


def test_multichannel_shapes() -> None:
    freqs, spl = equal_loudness_contour(40.0)
    assert freqs.shape == spl.shape == (29,)
