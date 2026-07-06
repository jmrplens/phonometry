#  Copyright (c) 2026. Jose M. Requena-Plens
"""
G frequency weighting for infrasound (ISO 7196:1995).

Clause 4: the G frequency response is the pole-zero configuration of
Table 1 (transcribed below from the official PDF, p. 2), with 0 dB gain at
10 Hz, a 12 dB/octave rise from 1 Hz to 20 Hz and 24 dB/octave cut-offs
below 1 Hz and above 20 Hz. Table 2 (p. 2) lists the nominal relative
response at one-third-octave frequencies from 0,25 Hz to 315 Hz. Annex A.3
(informative) gives the instrumentation tolerance: +/- 1 dB from 1 Hz to
20 Hz and (-inf, +1] dB below 1 Hz / above 20 Hz.
"""

import numpy as np
import pytest
from scipy import signal as sp_signal

from phonometry import WeightingFilter, weighting_filter

FS = 48000

# ISO 7196:1995 Table 2 - Nominal frequency response (Hz, dB).
TABLE2 = [
    (0.25, -88.0), (0.315, -80.0), (0.4, -72.1),
    (0.5, -64.3), (0.63, -56.6), (0.8, -49.5),
    (1.00, -43.0), (1.25, -37.5), (1.6, -32.6),
    (2.0, -28.3), (2.5, -24.1), (3.15, -20.0),
    (4.0, -16.0), (5.0, -12.0), (6.3, -8.0),
    (8.0, -4.0), (10.0, 0.0), (12.5, 4.0),
    (16.0, 7.7), (20.0, 9.0), (25.0, 3.7),
    (31.5, -4.0), (40.0, -12.0), (50.0, -20.0),
    (63.0, -28.0), (80.0, -36.0), (100.0, -44.0),
    (125.0, -52.0), (160.0, -60.0), (200.0, -68.0),
    (250.0, -76.0), (315.0, -84.0),
]


def _response_db(freqs: list[float], fs: int = FS) -> np.ndarray:
    sos = WeightingFilter(fs, "G").sos
    _, h = sp_signal.sosfreqz(sos, worN=np.asarray(freqs), fs=fs)
    return 20 * np.log10(np.abs(h))


def test_g_gain_is_0db_at_10hz() -> None:
    """Clause 4: the curve is defined with a gain of 0 dB at 10 Hz."""
    assert _response_db([10.0])[0] == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize(("freq", "expected_db"), TABLE2)
def test_g_matches_iso7196_table2(freq: float, expected_db: float) -> None:
    """Digital response vs the Table 2 values (given at nominal one-third-
    octave frequencies; evaluated at the exact base-10 frequencies
    10^(n/10), the same convention as IEC 61672-1 Annex D)."""
    exact = 10 ** (round(10 * np.log10(freq)) / 10)
    assert _response_db([exact])[0] == pytest.approx(expected_db, abs=0.3)


def test_g_cutoff_slopes() -> None:
    """Clause 4: 12 dB/oct in 1-20 Hz; 24 dB/oct cut-offs outside."""
    rise = _response_db([2.0, 4.0])
    assert rise[1] - rise[0] == pytest.approx(12.0, abs=1.0)
    hi = _response_db([100.0, 200.0])
    assert hi[1] - hi[0] == pytest.approx(-24.0, abs=0.5)
    lo = _response_db([0.25, 0.5])
    assert lo[1] - lo[0] == pytest.approx(24.0, abs=1.0)


def test_g_weighting_filter_function() -> None:
    """A 10 Hz tone passes unchanged; a 40 Hz tone drops ~12 dB."""
    t = np.arange(int(FS * 10.0)) / FS
    x10 = np.sin(2 * np.pi * 10.0 * t)
    y10 = weighting_filter(x10, FS, "G")
    # Skip the (long, low-frequency) transient before comparing RMS.
    s = slice(5 * FS, None)
    gain10 = 20 * np.log10(np.std(y10[s]) / np.std(x10[s]))
    assert gain10 == pytest.approx(0.0, abs=0.2)

    x40 = np.sin(2 * np.pi * 40.0 * t)
    y40 = weighting_filter(x40, FS, "G")
    gain40 = 20 * np.log10(np.std(y40[s]) / np.std(x40[s]))
    assert gain40 == pytest.approx(-12.0, abs=0.5)


def test_g_multichannel_and_stateful() -> None:
    t = np.arange(FS) / FS
    x = np.stack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 20 * t)])
    y = weighting_filter(x, FS, "G")
    assert y.shape == x.shape

    wf = WeightingFilter(FS, "G", stateful=True)
    blocks = [wf.filter(x[:, i : i + 4800]) for i in range(0, FS, 4800)]
    y_blocks = np.concatenate(blocks, axis=-1)
    y_ref = WeightingFilter(FS, "G", high_accuracy=False).filter(x)
    np.testing.assert_allclose(y_blocks, y_ref, atol=1e-12)


def test_invalid_curve_message_mentions_g() -> None:
    with pytest.raises(ValueError, match="G"):
        WeightingFilter(FS, "Q")
