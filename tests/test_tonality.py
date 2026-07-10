#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Prominent discrete tones: TNR and PR per ECMA-418-1:2024.

Anchors transcribed from the official PDF:
- Clause 10 Formula (2) EXAMPLE: dfc = 162,2 Hz at 1 kHz; 117,3 Hz at 500 Hz.
- Clause 12.2 EXAMPLE: f1,M = 922,2 Hz and f2,M = 1084,4 Hz for ft = 1 kHz.
- Clause 11.6 Formula (14) EXAMPLE: dfprox = 23 Hz at 150 Hz; 63,8 Hz at 850 Hz.
- Prominence criteria: TNR >= 8,0 dB at/above 1 kHz, 8,0 + 8,33*lg(1000/ft)
  below (Formulae 12-13); PR >= 9,0 dB / 9,0 + 10*lg(1000/ft) (25-26).
"""

import numpy as np
import pytest
from reference_data import (
    ECMA418_1_DFC_500HZ,
    ECMA418_1_DFC_1KHZ,
    ECMA418_1_F1_1KHZ,
    ECMA418_1_F2_1KHZ,
    ECMA418_1_PROX_150HZ,
    ECMA418_1_PROX_850HZ,
)

from phonometry import prominence_ratio, tone_to_noise_ratio
from phonometry.tonality import _critical_band, _proximity_spacing

FS = 48000


def _tone_in_noise(
    tone_freq: float, tone_rms: float, noise_rms: float, seconds: float = 8.0
) -> np.ndarray:
    # 8 s default (was 30 s): enough averaging for the qualitative criteria
    # tests and the 0.4 dB TNR anchor (re-measured error ~0.15 dB at 8 s);
    # the two 0.1 dB exact anchors request 16 s explicitly below.
    rng = np.random.default_rng(1234)
    t = np.arange(int(FS * seconds)) / FS
    tone = np.sqrt(2.0) * tone_rms * np.sin(2 * np.pi * tone_freq * t)
    noise = noise_rms * rng.standard_normal(t.size)
    return tone + noise


def test_critical_band_examples() -> None:
    """Clause 10 and 12.2 worked examples from the standard text (shared
    oracles in tests/reference_data.py, also used by the CI report)."""
    _, _, dfc_1k = _critical_band(1000.0)
    assert dfc_1k == pytest.approx(ECMA418_1_DFC_1KHZ, abs=0.05)
    _, _, dfc_500 = _critical_band(500.0)
    assert dfc_500 == pytest.approx(ECMA418_1_DFC_500HZ, abs=0.05)
    f1, f2, _ = _critical_band(1000.0)
    assert f1 == pytest.approx(ECMA418_1_F1_1KHZ, abs=0.05)
    assert f2 == pytest.approx(ECMA418_1_F2_1KHZ, abs=0.05)


def test_proximity_spacing_examples() -> None:
    """Clause 11.6 Formula (14) worked examples."""
    assert _proximity_spacing(150.0) == pytest.approx(ECMA418_1_PROX_150HZ, abs=0.5)
    assert _proximity_spacing(850.0) == pytest.approx(ECMA418_1_PROX_850HZ, abs=0.5)


def test_tnr_of_synthetic_tone_matches_analytic() -> None:
    """White noise with PSD N0 masks a tone with power Pt:
    TNR = 10*lg(Pt / (N0 * dfc))."""
    tone_rms, noise_rms = 0.1, 0.05
    x = _tone_in_noise(1000.0, tone_rms, noise_rms)
    n0 = noise_rms**2 / (FS / 2)  # white-noise PSD
    _, _, dfc = _critical_band(1000.0)
    expected = 10 * np.log10(tone_rms**2 / (n0 * dfc))
    result = tone_to_noise_ratio(x, FS)
    assert result.frequency == pytest.approx(1000.0, abs=1.0)
    # Demonstrated error on this signal is ~0.18 dB; 0.4 keeps ~2x headroom
    # (was 0.7, ~4x looser than the achieved accuracy).
    assert result.ratio_db == pytest.approx(expected, abs=0.4)


def test_tnr_prominence_criteria() -> None:
    """Formulae (12)-(13): 8 dB at 1 kHz+, frequency-dependent below."""
    loud = tone_to_noise_ratio(_tone_in_noise(2000.0, 0.2, 0.02), FS)
    assert loud.criterion_db == pytest.approx(8.0)
    assert loud.prominent

    quiet = tone_to_noise_ratio(
        _tone_in_noise(2000.0, 0.008, 0.05), FS, tone_freq=2000.0
    )
    assert not quiet.prominent

    low = tone_to_noise_ratio(_tone_in_noise(200.0, 0.2, 0.02), FS)
    assert low.criterion_db == pytest.approx(8.0 + 8.33 * np.log10(5.0), abs=1e-6)


def test_pr_of_synthetic_tone_matches_analytic() -> None:
    """PR = 10*lg((Pt + N0*dfM) / (0.5*N0*(dfL + dfU)))."""
    tone_rms, noise_rms = 0.1, 0.05
    # 16 s (was 30 s): the 0.1 dB tolerance needs more spectral averaging than
    # the 8 s default (measured error: 0.12 dB at 8 s, 0.037 dB at 16 s).
    x = _tone_in_noise(1000.0, tone_rms, noise_rms, seconds=16.0)
    n0 = noise_rms**2 / (FS / 2)
    from phonometry.tonality import _LOWER_EDGE_COEFFS, _UPPER_EDGE_COEFFS, _fitted_edge

    f1_m, f2_m, _ = _critical_band(1000.0)
    df_l = f1_m - _fitted_edge(1000.0, _LOWER_EDGE_COEFFS)
    df_u = _fitted_edge(1000.0, _UPPER_EDGE_COEFFS) - f2_m
    expected = 10 * np.log10(
        (tone_rms**2 + n0 * (f2_m - f1_m)) / (0.5 * n0 * (df_l + df_u))
    )
    result = prominence_ratio(x, FS)
    assert result.frequency == pytest.approx(1000.0, abs=1.0)
    # Demonstrated error ~0.03 dB; 0.1 keeps ample headroom (was 0.7).
    assert result.ratio_db == pytest.approx(expected, abs=0.1)


def test_pr_criteria_and_noise_only() -> None:
    """9 dB at 1 kHz+ (Formula 26); pure noise is never prominent."""
    loud = prominence_ratio(_tone_in_noise(3000.0, 0.3, 0.02), FS)
    assert loud.criterion_db == pytest.approx(9.0)
    assert loud.prominent

    rng = np.random.default_rng(7)
    noise = rng.standard_normal(FS * 8)
    result = prominence_ratio(noise, FS, tone_freq=1000.0)
    assert not result.prominent
    assert abs(result.ratio_db) < 3.0  # flat spectrum: bands nearly equal


def test_pr_low_frequency_truncated_band() -> None:
    """ft <= 171.4 Hz uses the 20 Hz-truncated lower band rescaled to
    100 Hz (Formula 24) - the result must still be finite and sensible."""
    x = _tone_in_noise(120.0, 0.3, 0.02)
    result = prominence_ratio(x, FS, tone_freq=120.0)
    assert result.frequency == pytest.approx(120.0, abs=1.0)
    assert result.prominent
    assert result.criterion_db == pytest.approx(9.0 + 10 * np.log10(1000 / 120), abs=1e-6)


def test_tnr_proximate_tones_combine() -> None:
    """Clause 11.6: two tones 30 Hz apart at 1 kHz (always proximate at
    1 kHz+) are assessed as one tone with their combined level."""
    rng = np.random.default_rng(99)
    # 16 s (was 30 s): the 0.1 dB tolerance needs more spectral averaging than
    # the 8 s default (measured error: 0.18 dB at 8 s, 0.025 dB at 16 s).
    t = np.arange(FS * 16) / FS
    x = (
        np.sqrt(2) * 0.1 * np.sin(2 * np.pi * 1000 * t)
        + np.sqrt(2) * 0.1 * np.sin(2 * np.pi * 1030 * t)
        + 0.05 * rng.standard_normal(t.size)
    )
    n0 = 0.05**2 / (FS / 2)
    _, _, dfc = _critical_band(1000.0)
    expected = 10 * np.log10((0.1**2 + 0.1**2) / (n0 * dfc))
    result = tone_to_noise_ratio(x, FS, tone_freq=1000.0)
    # Demonstrated error ~0.01 dB; 0.1 keeps ample headroom (was 0.8).
    assert result.ratio_db == pytest.approx(expected, abs=0.1)


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="fs"):
        tone_to_noise_ratio(np.ones(1000), 0)
    with pytest.raises(ValueError, match="1D"):
        prominence_ratio(np.ones((2, FS)), FS)
    with pytest.raises(ValueError, match="too short"):
        tone_to_noise_ratio(np.ones(100), FS)


def test_invalid_resolution_and_tone_freq() -> None:
    with pytest.raises(ValueError, match="resolution_hz"):
        tone_to_noise_ratio(np.ones(FS), FS, resolution_hz=0.0)
    with pytest.raises(ValueError, match="tone_freq"):
        prominence_ratio(np.ones(FS), FS, tone_freq=-100.0)


def test_too_coarse_resolution_raises() -> None:
    with pytest.raises(ValueError, match="too coarse"):
        tone_to_noise_ratio(np.ones(FS), FS, resolution_hz=FS / 4.0)


def test_coarse_resolution_warns_at_low_frequency() -> None:
    """At 250 Hz (dfc ~ 115 Hz) a 4 Hz bin gives < 3 bins across the tone
    half-width, biasing the ratio; the function warns (it does not raise)."""
    x = _tone_in_noise(250.0, 0.2, 0.02)
    with pytest.warns(UserWarning, match="bins"):
        tone_to_noise_ratio(x, FS, tone_freq=250.0, resolution_hz=4.0)
    with pytest.warns(UserWarning, match="bins"):
        prominence_ratio(x, FS, tone_freq=250.0, resolution_hz=4.0)
