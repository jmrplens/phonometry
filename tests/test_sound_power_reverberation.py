#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Sound power in a reverberation test room: ISO 3741:2010 (precision, grade 1).

Physics / normative anchors (ISO 3741:2010):
- Direct method, Eq. (20):
  LW = Lp(ST) + 10 lg(A/A0) + 4,34*(A/S) + 10 lg(1 + S*c/(8*V*f)) + C1 + C2 - 6.
- A = (55,26/c)*(V/T60); c = 20,05*sqrt(273 + theta) (Sabine, clause 9.1.4).
- Waterhouse boundary term 10 lg(1 + S*c/(8*V*f)) -> 0 as f -> infinity.
- Comparison method, Eq. (21): LW = LW(RSS) + (Lp(ST) - Lp(RSS) + C2).
"""

import numpy as np
import pytest

from phonometry import (
    ReverberationSoundPowerResult,
    SoundPowerWarning,
    room_parameters,
    sound_power_comparison,
    sound_power_reverberation,
)

# Reference-quantity / radiation-impedance constants (ISO 3741 clause 9.1.4).
_PS0 = 101.325  # kPa
_THETA0 = 314.0  # K (reference-quantity correction C1)
_THETA1 = 296.0  # K (radiation-impedance correction C2)


def _c1(theta: float, ps: float) -> float:
    return -10.0 * np.log10(ps / _PS0) + 5.0 * np.log10((273.15 + theta) / _THETA0)


def _c2(theta: float, ps: float) -> float:
    return -10.0 * np.log10(ps / _PS0) + 15.0 * np.log10((273.15 + theta) / _THETA1)


def _bracket(t60, volume, surface, freq, theta, ps):
    """Independent re-implementation of the Eq. (20) bracket, for inversion."""
    c = 20.05 * np.sqrt(273.0 + theta)
    a = (55.26 / c) * (volume / np.asarray(t60, dtype=float))
    waterhouse = 10.0 * np.log10(1.0 + surface * c / (8.0 * volume * np.asarray(freq)))
    return (
        10.0 * np.log10(a / 1.0)
        + 4.34 * (a / surface)
        + waterhouse
        + _c1(theta, ps)
        + _c2(theta, ps)
        - 6.0
    )


# --------------------------------------------------------------------------
# Direct method — exact inversion of Eq. (20)
# --------------------------------------------------------------------------
def test_direct_method_exact_inversion() -> None:
    """Generate Lp(ST) from a known LW with Eq. (20), recover LW digit-exact."""
    volume, surface = 200.0, 210.0
    freqs = np.array([100.0, 500.0, 1000.0, 5000.0, 10000.0])
    t60 = np.array([2.0, 1.8, 1.5, 1.0, 0.6])
    theta, ps = 23.0, 101.325
    lw_target = np.array([80.0, 85.0, 90.0, 82.0, 75.0])

    # Invert: Lp(ST) that yields exactly lw_target (the bracket is Lp-free).
    lp = lw_target - _bracket(t60, volume, surface, freqs, theta, ps)

    res = sound_power_reverberation(
        lp, t60, volume, surface, freqs,
        temperature=theta, static_pressure=ps,
    )
    assert isinstance(res, ReverberationSoundPowerResult)
    assert np.allclose(res.sound_power_level, lw_target, atol=1e-9, rtol=0.0)


def test_direct_method_multi_position_energy_average() -> None:
    """Several microphone rows are energy-averaged (Eq. 16) before Eq. (20)."""
    volume, surface = 200.0, 210.0
    freqs = np.array([1000.0])
    t60 = np.array([1.5])
    # Two positions differing by 6 dB -> energy mean is between them.
    levels = np.array([[80.0], [86.0]])
    res = sound_power_reverberation(levels, t60, volume, surface, freqs)
    mean = 10.0 * np.log10((10 ** 8.0 + 10 ** 8.6) / 2.0)
    assert np.isclose(res.mean_pressure_level[0], mean)


# --------------------------------------------------------------------------
# Waterhouse boundary correction -> 0 at high frequency
# --------------------------------------------------------------------------
def test_waterhouse_term_vanishes_at_high_frequency() -> None:
    """10 lg(1 + S c /(8 V f)) decreases monotonically to ~0 as f grows."""
    volume, surface = 200.0, 210.0
    freqs = np.array([100.0, 1000.0, 10000.0, 1.0e7])
    t60 = np.full(freqs.shape, 1.5)
    lp = np.full(freqs.shape, 80.0)
    res = sound_power_reverberation(lp, t60, volume, surface, freqs)
    w = res.waterhouse_correction
    assert np.all(np.diff(w) < 0.0)  # strictly decreasing with frequency
    assert w[0] > w[-1]
    assert w[-1] < 1e-3  # ~0 at 10 MHz
    assert w[2] < 0.1  # already small at 10 kHz


# --------------------------------------------------------------------------
# Comparison method — exact by construction (Eq. 21)
# --------------------------------------------------------------------------
def test_comparison_method_exact_by_construction() -> None:
    """LW = LW(RSS) + (Lp(ST) - Lp(RSS) + C2), recovered digit-exact."""
    theta, ps = 20.0, 100.0
    lw_ref = np.array([90.0, 92.0, 88.0])
    lp_rss = np.array([70.0, 71.0, 69.0])
    # Choose a target LW and back out Lp(ST).
    lw_target = np.array([85.0, 95.0, 80.0])
    lp_st = lw_target - lw_ref + lp_rss - _c2(theta, ps)

    res = sound_power_comparison(
        lp_st, lp_rss, lw_ref, temperature=theta, static_pressure=ps,
    )
    assert isinstance(res, ReverberationSoundPowerResult)
    assert res.method == "comparison"
    assert np.allclose(res.sound_power_level, lw_target, atol=1e-9, rtol=0.0)


def test_comparison_reference_conditions_c2_near_zero() -> None:
    """At theta=23 C, ps=101,325 kPa the C2 correction is ~0 (theta1=296 K)."""
    lw_ref = np.array([90.0])
    lp_rss = np.array([70.0])
    lp_st = np.array([80.0])
    res = sound_power_comparison(lp_st, lp_rss, lw_ref)
    # LW ~ 90 + (80 - 70) = 100, plus a ~0,003 dB C2 term.
    assert np.isclose(res.sound_power_level[0], 100.0, atol=0.01)


# --------------------------------------------------------------------------
# Synergy — room_parameters T30 feeds the direct method
# --------------------------------------------------------------------------
def test_synergy_room_parameters_feeds_direct_method() -> None:
    """A T60 estimate from room_parameters composes into Eq. (20)."""
    fs = 48000
    # Synthetic exponentially decaying broadband IR (T60 ~ 1 s).
    rng = np.random.default_rng(0)
    n = fs  # 1 s
    t = np.arange(n) / fs
    t60_true = 1.0
    decay = 10.0 ** (-3.0 * t / t60_true)  # -60 dB over t60
    ir = rng.standard_normal(n) * decay
    ir[0] += 5.0  # a clear direct-sound peak

    room = room_parameters(ir, fs, limits=(500.0, 1000.0), fraction=1)
    t60_bands = room.t30  # decay time (s) extrapolated to 60 dB
    freqs = np.asarray(room.frequency, dtype=float)
    assert np.all(np.isfinite(t60_bands))

    lp = np.full(freqs.shape, 80.0)
    res = sound_power_reverberation(lp, t60_bands, 200.0, 210.0, freqs)
    assert res.sound_power_level.shape == freqs.shape
    assert np.all(np.isfinite(res.sound_power_level))


# --------------------------------------------------------------------------
# Background correction (Eq. 14) and A-weighted total (Annex F)
# --------------------------------------------------------------------------
def test_background_correction_reduces_level_and_warns_below_criterion() -> None:
    """dLp = 4 dB (< 6 dB) at 100 Hz -> K1 clamped, upper-bound warning."""
    freqs = np.array([100.0])
    t60 = np.array([1.5])
    levels = np.array([[74.0]])
    background = np.array([[70.0]])  # dLp = 4 dB
    with pytest.warns(SoundPowerWarning):
        res = sound_power_reverberation(
            levels, t60, 200.0, 210.0, freqs, background_levels=background,
        )
    assert res.background_correction[0] > 0.0


def test_a_weighted_total_from_bands() -> None:
    """LWA combines bands with Annex F A-weighting (Eq. F.2)."""
    freqs = np.array([500.0, 1000.0, 2000.0])
    t60 = np.full(freqs.shape, 1.5)
    lp = np.full(freqs.shape, 80.0)
    res = sound_power_reverberation(lp, t60, 200.0, 210.0, freqs)
    assert np.isfinite(res.sound_power_level_a)
    # A-weighted total is an energy sum >= the largest single weighted band.
    assert res.sound_power_level_a > np.max(res.sound_power_level) - 10.0


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def test_invalid_volume_raises() -> None:
    with pytest.raises(ValueError):
        sound_power_reverberation(
            np.array([80.0]), np.array([1.5]), -1.0, 210.0, np.array([1000.0])
        )


def test_mismatched_shapes_raise() -> None:
    with pytest.raises(ValueError):
        sound_power_reverberation(
            np.array([80.0, 81.0]), np.array([1.5]), 200.0, 210.0,
            np.array([1000.0]),
        )
