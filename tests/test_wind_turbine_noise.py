#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for wind-turbine acoustic noise (IEC 61400-11:2012+A1:2018).

The oracles are the closed-form geometry / critical bandwidth and a synthetic
clean tone on a flat noise floor whose tonal audibility is hand-derived
independently of the implementation.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.wind_turbine_noise import (
    apparent_sound_power_level,
    critical_bandwidth,
    slant_distance,
    wind_turbine_tonality,
)


def test_critical_bandwidth_formula() -> None:
    # 25 + 75*(1 + 1.4*0.25)^0.69 = 117.256 Hz at 500 Hz.
    assert critical_bandwidth(500.0) == pytest.approx(117.256, abs=0.02)


def test_critical_bandwidth_low_frequency_band() -> None:
    # A candidate tone in 20-70 Hz uses the fixed 20-120 Hz (100 Hz) band.
    assert critical_bandwidth(50.0) == 100.0


def test_slant_distance() -> None:
    # R0 = 80 + 100/2 = 130; R1 = sqrt(80^2 + 130^2).
    assert slant_distance(80.0, 100.0) == pytest.approx(np.hypot(80.0, 130.0))


def test_apparent_sound_power_single_band() -> None:
    r1 = 150.0
    expected = 100.0 - 6.0 + 10.0 * np.log10(4.0 * np.pi * r1**2)
    assert apparent_sound_power_level([100.0], r1) == pytest.approx(expected, rel=1e-9)


def test_apparent_sound_power_energy_sum() -> None:
    r1 = 120.0
    bands = np.array([90.0, 92.0, 88.0])
    geom = 10.0 * np.log10(4.0 * np.pi * r1**2)
    expected = 10.0 * np.log10(np.sum(10.0 ** ((bands - 6.0 + geom) / 10.0)))
    assert apparent_sound_power_level(bands, r1) == pytest.approx(expected, rel=1e-9)


def _synthetic_tone() -> tuple[np.ndarray, np.ndarray]:
    df = 2.0
    freqs = np.arange(440.0, 560.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[int(np.argmin(np.abs(freqs - 500.0)))] = 60.0
    return levels, freqs


def test_tonal_audibility_synthetic_tone() -> None:
    # Hand-derived: CBW=117.256, ENBW=3.0, L_pn,avg=30 ->
    #   L_pn = 30 + 10 lg(117.256/3.0) = 45.92 dB
    #   L_pt = 60 (single line), ΔL_tn = 14.08
    #   L_a = -2 - lg(1+(500/502)^2.5) = -2.299
    #   ΔL_a = 14.08 - (-2.299) = 16.38 dB
    levels, freqs = _synthetic_tone()
    res = wind_turbine_tonality(levels, freqs)
    assert res.tone_frequency == pytest.approx(500.0)
    assert res.critical_bandwidth == pytest.approx(117.256, abs=0.02)
    assert res.tone_level == pytest.approx(60.0, abs=1e-6)
    assert res.masking_level == pytest.approx(45.92, abs=0.05)
    assert res.tonality == pytest.approx(14.08, abs=0.05)
    assert res.audibility_criterion == pytest.approx(-2.299, abs=0.01)
    assert res.tonal_audibility == pytest.approx(16.38, abs=0.06)
    assert res.is_audible is True


def test_low_frequency_fixed_critical_band() -> None:
    # A candidate tone at 40 Hz uses the FIXED 20-120 Hz band, not one centred
    # on 40 Hz. Loud lines below 20 Hz must be excluded (a centred band
    # [-10, 90] would wrongly fold them into the tone/masking classification).
    df = 2.0
    freqs = np.arange(0.0, 140.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[freqs < 20.0] = 58.0  # excluded by the fixed 20-120 band
    levels[int(np.argmin(np.abs(freqs - 40.0)))] = 60.0
    res = wind_turbine_tonality(levels, freqs, tone_frequency=40.0)
    # Only the 40 Hz tone survives -> single tone line, masking noise = 30 dB.
    assert res.tone_level == pytest.approx(60.0, abs=0.05)
    assert res.masking_level == pytest.approx(30.0 + 10.0 * np.log10(100.0 / 3.0), abs=0.05)


def test_non_contiguous_tone_lines_counted() -> None:
    # IEC 61400-11+A1:2018: tone lines need not be adjacent to the peak. Two
    # separated lines within 10 dB of the peak both count toward L_pt.
    df = 2.0
    freqs = np.arange(240.0, 360.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[int(np.argmin(np.abs(freqs - 300.0)))] = 60.0
    levels[int(np.argmin(np.abs(freqs - 260.0)))] = 56.0  # isolated, within 10 dB
    res = wind_turbine_tonality(levels, freqs)
    # Both separated tones (no Hanning: neither run has >= 2 adjacent lines).
    expected = 10.0 * np.log10(10.0**6.0 + 10.0**5.6)
    assert res.tone_level == pytest.approx(expected, abs=0.05)


def test_tonal_audibility_flat_spectrum_not_audible() -> None:
    freqs = np.arange(440.0, 560.0, 2.0)
    levels = np.full(freqs.size, 30.0)
    res = wind_turbine_tonality(levels, freqs)
    assert res.is_audible is False


def test_tonal_audibility_rejects_short_input() -> None:
    with pytest.raises(ValueError):
        wind_turbine_tonality([1.0, 2.0], [10.0, 12.0])


def test_tonal_audibility_rejects_non_monotonic_frequencies() -> None:
    # A non-increasing frequency axis is not a valid narrowband spectrum.
    with pytest.raises(ValueError, match="strictly increasing"):
        wind_turbine_tonality([30.0, 30.0, 30.0], [100.0, 98.0, 104.0])


def test_tonal_audibility_rejects_non_uniform_spacing() -> None:
    # Formulae 30-34 assume a uniform frequency resolution df.
    with pytest.raises(ValueError, match="uniformly spaced"):
        wind_turbine_tonality([30.0, 30.0, 30.0, 30.0], [100.0, 102.0, 104.0, 120.0])


def test_tonal_audibility_plot_smoke_and_export() -> None:
    import phonometry

    levels, freqs = _synthetic_tone()
    res = phonometry.wind_turbine_tonality(levels, freqs)
    assert res.plot() is not None
    assert phonometry.apparent_sound_power_level is apparent_sound_power_level
