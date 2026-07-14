#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for electroacoustic distortion metrics (IEC 60268-3 / AES17).

Every metric has an exact analytic oracle: a signal synthesised with known
harmonic or intermodulation amplitudes reproduces the closed-form ratio. Tones
are placed on FFT bins (coherent sampling) so the FFT reads their amplitudes
without leakage.
"""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

import reference_data as ref
from phonometry import (
    HarmonicDistortionResult,
    difference_frequency_distortion,
    dynamic_intermodulation_distortion,
    harmonic_analysis,
    harmonic_distortion,
    modulation_distortion,
    sinad,
    thd,
    thd_plus_noise,
    total_difference_frequency_distortion,
    weighted_thd,
)

FS = 48000
N = 48000  # 1 s -> 1 Hz bin resolution, every test tone lands on a bin.
_T = np.arange(N) / FS


def _tone(freq: float, amp: float = 1.0) -> np.ndarray:
    return amp * np.sin(2 * np.pi * freq * _T)


def _harmonic_signal() -> np.ndarray:
    a1, a2, a3, a4 = ref.DISTORTION_HARMONICS
    return (
        _tone(1000.0, a1)
        + _tone(2000.0, a2)
        + _tone(3000.0, a3)
        + _tone(4000.0, a4)
    )


def test_thd_f_matches_closed_form() -> None:
    x = _harmonic_signal()
    assert thd(x, FS, 1000.0, kind="F") == pytest.approx(ref.DISTORTION_THD_F, rel=1e-6)


def test_thd_r_matches_closed_form() -> None:
    x = _harmonic_signal()
    assert thd(x, FS, 1000.0, kind="R") == pytest.approx(ref.DISTORTION_THD_R, rel=1e-6)


def test_thd_auto_detects_fundamental() -> None:
    x = _harmonic_signal()
    assert thd(x, FS) == pytest.approx(ref.DISTORTION_THD_F, rel=1e-6)


def test_nth_order_harmonic_distortion() -> None:
    x = _harmonic_signal()
    assert harmonic_distortion(x, FS, 1000.0, 2) == pytest.approx(
        ref.DISTORTION_D2, rel=1e-6
    )


def test_harmonic_distortion_rejects_order_below_two() -> None:
    with pytest.raises(ValueError):
        harmonic_distortion(_tone(1000.0), FS, 1000.0, 1)


def test_thd_plus_noise_recovers_noise_floor() -> None:
    # Fundamental (RMS 1/sqrt2) + white noise of RMS 0.01; the notch removes
    # the fundamental, so THD+N ~ noise_rms / total_rms.
    rng = np.random.default_rng(0)
    noise = rng.standard_normal(N) * 0.01
    x = _tone(1000.0) + noise
    expected = 0.01 / np.sqrt(0.5)
    # The notch also removes a small noise band, so the measured value is a
    # little below the broadband ratio.
    assert thd_plus_noise(x, FS, 1000.0) == pytest.approx(expected, rel=0.1)


def test_sinad_is_negative_thd_plus_noise_db() -> None:
    rng = np.random.default_rng(1)
    x = _tone(1000.0) + rng.standard_normal(N) * 0.01
    thdn_db = thd_plus_noise(x, FS, 1000.0, as_db=True)
    assert sinad(x, FS, 1000.0) == pytest.approx(-thdn_db)


def test_thd_plus_noise_pure_tone_is_tiny() -> None:
    # A pure fundamental has no distortion or noise; THD+N ~ 0.
    assert thd_plus_noise(_tone(1000.0), FS, 1000.0) < 1e-3


def test_thd_plus_noise_rejects_q_out_of_range() -> None:
    with pytest.raises(ValueError):
        thd_plus_noise(_tone(1000.0), FS, 1000.0, notch_q=5.0)


def test_weighted_thd_attenuates_low_harmonics() -> None:
    # A-weighting attenuates a 100 Hz fundamental's 200 Hz harmonic relative to
    # the unweighted residual, so weighted THD < the plain harmonic ratio.
    x = _tone(100.0) + _tone(200.0, 0.1)
    plain = thd(x, FS, 100.0, kind="R")
    weighted = weighted_thd(x, FS, 100.0, weighting="A")
    assert 0.0 < weighted < plain


def test_weighted_thd_rejects_bad_notch_q() -> None:
    with pytest.raises(ValueError):
        weighted_thd(_tone(1000.0), FS, 1000.0, notch_q=5.0)


def test_thd_plus_noise_rejects_fundamental_above_nyquist() -> None:
    # A fundamental at/above fs/2 cannot be notched (iirnotch would fail).
    with pytest.raises(ValueError):
        thd_plus_noise(_tone(1000.0), FS, FS / 2.0)


def test_modulation_distortion_iec_per_order() -> None:
    # IEC 60268-3 14.12.7.2 g)-h): carrier f_high = 8 kHz (amp 0.25),
    # modulator f_low = 250 Hz; 2nd-order sidebands at f_high +/- f_low
    # (0.02 each), 3rd-order at f_high +/- 2 f_low (0.01 each). Per-order
    # values are ARITHMETIC sideband sums over the f_high amplitude:
    # d_m,2 = (0.02+0.02)/0.25 = 0.16, d_m,3 = (0.01+0.01)/0.25 = 0.08.
    fl, fh, ah = 250.0, 8000.0, 0.25
    x = (
        _tone(fl)
        + _tone(fh, ah)
        + _tone(fh + fl, 0.02)
        + _tone(fh - fl, 0.02)
        + _tone(fh + 2 * fl, 0.01)
        + _tone(fh - 2 * fl, 0.01)
    )
    res = modulation_distortion(x, FS, fl, fh)
    assert res.d2 == pytest.approx(0.16, rel=1e-6)
    assert res.d3 == pytest.approx(0.08, rel=1e-6)
    # The SMPTE-analyzer combined RMS convention is kept, explicitly labelled.
    smpte = math.sqrt(0.02**2 + 0.02**2 + 0.01**2 + 0.01**2) / ah
    assert res.smpte == pytest.approx(smpte, rel=1e-6)


def test_difference_frequency_distortion_iec() -> None:
    # IEC 60268-3 14.12.8.1: equal tones f1 = 13 kHz, f2 = 14 kHz (amp 0.5);
    # 2nd-order product at f2 - f1 = 1 kHz (0.03); 3rd-order at 2f1 - f2 and
    # 2f2 - f1 (0.02 each). The reference is U_2,ref = 2*U_2,f2 (the sum of
    # both tone amplitudes = 1.0) and the 3rd order sums ARITHMETICALLY:
    # d_d,2 = 0.03/1.0, d_d,3 = (0.02+0.02)/1.0.
    f1, f2 = 13000.0, 14000.0
    x = (
        _tone(f1, 0.5)
        + _tone(f2, 0.5)
        + _tone(f2 - f1, 0.03)
        + _tone(2 * f1 - f2, 0.02)
        + _tone(2 * f2 - f1, 0.02)
    )
    assert difference_frequency_distortion(x, FS, f1, f2, order=2) == pytest.approx(
        0.03, rel=1e-6
    )
    assert difference_frequency_distortion(x, FS, f1, f2, order=3) == pytest.approx(
        0.04, rel=1e-6
    )


def test_total_difference_frequency_distortion_iec() -> None:
    # IEC 60268-3 14.12.10: the standard tones f1 = 8 kHz, f2 = 11.95 kHz
    # (f0 = 4 kHz, delta = 50 Hz), products U' at f2-f1 = 3950 Hz (0.02) and
    # 2f1-f2 = 4050 Hz (0.03), tones 0.5 each. Only these two in-band
    # products enter, rms-summed over the tone-amplitude sum:
    # d_TDFD = sqrt(0.02^2 + 0.03^2) / (0.5 + 0.5) = sqrt(0.0013).
    f1, f2 = 8000.0, 11950.0
    x = (
        _tone(f1, 0.5)
        + _tone(f2, 0.5)
        + _tone(f2 - f1, 0.02)
        + _tone(2 * f1 - f2, 0.03)
        + _tone(2 * f2 - f1, 0.05)  # out-of-band product: must NOT count
    )
    expected = 0.03605551275463989  # sqrt(0.0013), exact
    assert total_difference_frequency_distortion(x, FS) == pytest.approx(
        expected, rel=1e-6
    )
    # Explicit tone arguments give the same value as the standard defaults.
    assert total_difference_frequency_distortion(x, FS, f1, f2) == pytest.approx(
        expected, rel=1e-6
    )


def test_difference_frequency_clean_octave_tones_read_zero() -> None:
    # Search-window hygiene: with octave-spaced clean tones the old
    # half-difference window latched a primary tone and reported d2 = 1.0.
    # A clean signal must read zero for both orders and both spacings.
    for f1, f2 in ((1000.0, 2000.0), (1000.0, 3000.0)):
        x = _tone(f1, 0.5) + _tone(f2, 0.5)
        # Numerical floor only (window leakage of the FFT at ~1e-16).
        assert difference_frequency_distortion(x, FS, f1, f2, order=2) < 1e-12
        assert difference_frequency_distortion(x, FS, f1, f2, order=3) < 1e-12


def test_difference_frequency_dc_offset_not_counted() -> None:
    # 2f1 - f2 <= 0 clamps to zero and a DC offset must not leak into d3
    # (the old window at negative/zero product frequencies included bin 0).
    f1, f2 = 1000.0, 2500.0
    x = _tone(f1, 0.5) + _tone(f2, 0.5) + 0.5
    assert difference_frequency_distortion(x, FS, f1, f2, order=3) < 1e-12
    assert difference_frequency_distortion(x, FS, f1, f2, order=2) < 1e-12


def test_difference_frequency_rejects_bad_args() -> None:
    with pytest.raises(ValueError):
        difference_frequency_distortion(_tone(1000.0), FS, 2000.0, 1000.0)
    with pytest.raises(ValueError):
        difference_frequency_distortion(_tone(1000.0), FS, 1000.0, 2000.0, order=4)
    with pytest.raises(ValueError):
        total_difference_frequency_distortion(_tone(1000.0), FS, 2000.0, 1000.0)


def test_dynamic_intermodulation_distortion() -> None:
    # IEC 60268-3 Table 2: the standard 15 kHz / 3.15 kHz signal has NINE
    # difference products at |k*3150 - 15000| < 15000 for k = 1..9, spanning
    # 750 Hz (k=5) to 13350 Hz (k=9). Enumerated here from the standard, not
    # from the implementation, so an off-by-one in the loop bound is caught.
    fsine, fsq = 15000.0, 3150.0
    comps = sorted(
        round(abs(k * fsq - fsine), 6) for k in range(1, 10) if abs(k * fsq - fsine) < fsine
    )
    assert comps == pytest.approx(
        [750.0, 2400.0, 3900.0, 5550.0, 7050.0, 8700.0, 10200.0, 11850.0, 13350.0]
    )
    amps = [0.01 * (i + 1) for i in range(len(comps))]
    # The captured DIM signal ALSO carries the strong 3.15 kHz square-wave
    # fundamental (0.8, ~in the 1:4 ratio); it must not be mistaken for a
    # product even though it sits 750 Hz from the k=4 (2400) and k=6 (3900)
    # products. DIM = sqrt(sum products^2) / sine_amp, excluding the 3150 tone.
    x = _tone(fsine) + _tone(fsq, 0.8)
    for c, a in zip(comps, amps):
        x = x + _tone(c, a)
    expected = math.sqrt(sum(a**2 for a in amps))
    assert dynamic_intermodulation_distortion(x, FS) == pytest.approx(
        expected, rel=1e-6
    )


def test_harmonic_analysis_bundle_and_plot() -> None:
    res = harmonic_analysis(_harmonic_signal(), FS, 1000.0)
    assert isinstance(res, HarmonicDistortionResult)
    assert res.fundamental == pytest.approx(1000.0)
    assert res.thd_f == pytest.approx(ref.DISTORTION_THD_F, rel=1e-6)
    assert res.thd_r == pytest.approx(ref.DISTORTION_THD_R, rel=1e-6)
    assert res.harmonic_amplitudes[0] == pytest.approx(1.0, rel=1e-6)
    ax = res.plot()
    assert ax is not None


@pytest.mark.parametrize(
    "func", [thd, thd_plus_noise, lambda s, fs: sinad(s, fs)]
)
def test_rejects_non_finite_signal(func) -> None:  # type: ignore[no-untyped-def]
    bad = np.array([np.nan] * 100)
    with pytest.raises(ValueError):
        func(bad, FS)


def test_rejects_bad_fs_and_kind() -> None:
    with pytest.raises(ValueError):
        thd(_tone(1000.0), 0.0)
    with pytest.raises(ValueError):
        thd(_tone(1000.0), FS, 1000.0, kind="X")  # type: ignore[arg-type]


def test_rejects_too_short_signal() -> None:
    with pytest.raises(ValueError):
        thd(np.array([0.0, 1.0, 0.0]), FS)
