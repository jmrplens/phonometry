#  Copyright (c) 2026. Jose M. Requena-Plens
"""
p-p sound intensity (IEC 61043:1994) and ISO 9614-1:1993 field indicators.

Physics anchors:
- Plane progressive wave: I = p_rms^2 / (rho*c), so Lp - LI =
  10*lg(rho*c/400) = 0,14 dB (IEC 61043:1994 clause 5 note).
- Finite-difference estimator bias sin(k*dr)/(k*dr) (IEC 61043:1994, 7.3;
  Table 3 nominal -10,5 dB at 6,3 kHz for 25 mm separation).
- Field indicators from ISO 9614-1:1993 Annex A, equations (A.3)-(A.9).
"""

import numpy as np
import pytest

from phonometry import (
    FieldIndicators,
    IntensityResult,
    dynamic_capability_index,
    field_indicators,
    sound_intensity,
)

FS = 48000
SPACING = 0.012  # 12 mm microphone separation
RHO = 1.204
C = 343.0


def _plane_wave_pair(
    delay_s: float,
    f_lo: float = 50.0,
    f_hi: float = 2000.0,
    seconds: float = 10.0,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Band-limited noise observed at two points; the second is a pure
    (fractional, circular) delay of the first: p2(t) = p1(t - delay)."""
    rng = np.random.default_rng(seed)
    n = int(FS * seconds)
    freqs = np.fft.rfftfreq(n, 1.0 / FS)
    spec = np.zeros(freqs.size, dtype=complex)
    band = (freqs >= f_lo) & (freqs <= f_hi)
    spec[band] = np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, int(band.sum())))
    p1 = np.fft.irfft(spec, n)
    p2 = np.fft.irfft(spec * np.exp(-2j * np.pi * freqs * delay_s), n)
    scale = 1.0 / np.sqrt(np.mean(p1**2))  # 1 Pa rms (94 dB)
    return p1 * scale, p2 * scale


def test_plane_progressive_wave_broadband() -> None:
    """I = p_rms^2/(rho*c) within 3 % in the valid band, F2 = 0,14 dB."""
    p1, p2 = _plane_wave_pair(delay_s=SPACING / C)
    res = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C)
    p_center = (p1 + p2) / 2.0
    expected = float(np.mean(p_center**2)) / (RHO * C)
    assert res.total_intensity == pytest.approx(expected, rel=0.03)
    assert res.total_direction == 1
    # IEC 61043:1994 clause 5: Lp - LI = 10*lg(rho*c/400) = 0,14 dB.
    assert res.total_pressure_intensity_index == pytest.approx(
        10 * np.log10(RHO * C / 400.0), abs=0.35
    )
    assert res.total_pressure_level == pytest.approx(94.0, abs=0.2)
    # The whole excitation band lies below the usable-bandwidth bound.
    assert res.max_valid_frequency == pytest.approx(0.1 * C / SPACING)
    assert res.max_valid_frequency > 2000.0


def test_reversing_microphones_flips_the_sign() -> None:
    p1, p2 = _plane_wave_pair(delay_s=SPACING / C)
    fwd = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C)
    rev = sound_intensity(p2, p1, FS, SPACING, rho=RHO, c=C)
    assert rev.total_direction == -1
    assert rev.total_intensity == pytest.approx(-fwd.total_intensity, rel=1e-6)
    assert rev.total_intensity_level == pytest.approx(fwd.total_intensity_level, abs=1e-6)


def test_plane_wave_third_octave_bands() -> None:
    """Per-band F2 = 0 dB and positive direction inside the excited band."""
    p1, p2 = _plane_wave_pair(delay_s=SPACING / C)
    res = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C, fraction=3)
    assert res.frequency is not None
    assert res.intensity is not None
    assert res.direction is not None
    assert res.pressure_intensity_index is not None
    assert res.bias_correction is not None
    active = (res.frequency >= 80.0) & (res.frequency <= 1600.0)
    assert np.any(active)
    assert np.all(res.direction[active] == 1)
    # Free-field: per-band pressure-intensity index stays near 0,14 dB.
    assert np.all(np.abs(res.pressure_intensity_index[active]) < 1.0)
    # Correction factor grows monotonically with frequency, >= 1 in-band.
    assert np.all(res.bias_correction[active] >= 1.0)
    assert res.bias_correction[active][-1] > res.bias_correction[active][0]


def test_standing_wave_high_pressure_intensity_index() -> None:
    """Two equal opposing waves: |I| near zero while Lp is high."""
    t = np.arange(int(FS * 5.0)) / FS
    f0 = 500.0
    k = 2.0 * np.pi * f0 / C
    x1, x2 = 0.10, 0.10 + SPACING
    p1 = 2.0 * np.cos(k * x1) * np.cos(2.0 * np.pi * f0 * t)
    p2 = 2.0 * np.cos(k * x2) * np.cos(2.0 * np.pi * f0 * t)
    res = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C)
    p_center = (p1 + p2) / 2.0
    plane_equivalent = float(np.mean(p_center**2)) / (RHO * C)
    assert abs(res.total_intensity) < 1e-3 * plane_equivalent
    assert res.total_pressure_level > 90.0
    assert res.total_pressure_intensity_index > 20.0


def test_1khz_tone_exact_analytic_intensity() -> None:
    """Pure tone with exact phase lag k*dr: the cross-spectral estimator
    must return (A^2/(2*rho*c)) * sin(k*dr)/(k*dr) exactly."""
    t = np.arange(int(FS * 5.0)) / FS
    f0 = 1000.0
    amp = np.sqrt(2.0)  # 1 Pa rms
    phi = 2.0 * np.pi * f0 * SPACING / C  # k*dr
    p1 = amp * np.cos(2.0 * np.pi * f0 * t)
    p2 = amp * np.cos(2.0 * np.pi * f0 * t - phi)
    res = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C, fraction=3)
    true_plane = amp**2 / (2.0 * RHO * C)
    expected = true_plane * np.sin(phi) / phi
    assert res.total_intensity == pytest.approx(expected, rel=0.01)
    assert res.total_intensity_level == pytest.approx(
        10 * np.log10(expected / 1e-12), abs=0.05
    )
    # All the power falls in the 1 kHz third-octave band.
    assert res.frequency is not None
    assert res.intensity is not None
    assert res.bias_correction is not None
    idx = int(np.argmin(np.abs(res.frequency - 1000.0)))
    assert res.intensity[idx] == pytest.approx(expected, rel=0.01)
    # Applying the documented sin(k*dr)/(k*dr) correction recovers the
    # unbiased plane-wave intensity (IEC 61043:1994, 7.3).
    corrected = res.intensity[idx] * res.bias_correction[idx]
    assert corrected == pytest.approx(true_plane, rel=0.01)


def test_band_integration_consistency() -> None:
    """Sum of band intensities and pressures matches the broadband totals."""
    p1, p2 = _plane_wave_pair(delay_s=SPACING / C, f_lo=100.0, f_hi=4000.0)
    res = sound_intensity(p1, p2, FS, SPACING, rho=RHO, c=C, fraction=3)
    assert res.intensity is not None
    assert res.pressure_level is not None
    assert float(np.sum(res.intensity)) == pytest.approx(res.total_intensity, rel=0.01)
    band_lp_sum = 10 * np.log10(np.sum(10 ** (0.1 * res.pressure_level)))
    assert band_lp_sum == pytest.approx(res.total_pressure_level, abs=0.05)


def test_octave_fraction_and_limits() -> None:
    p1, p2 = _plane_wave_pair(delay_s=SPACING / C)
    res = sound_intensity(
        p1, p2, FS, SPACING, rho=RHO, c=C, fraction=1, limits=[63.0, 4000.0]
    )
    assert isinstance(res, IntensityResult)
    assert res.frequency is not None
    assert res.frequency[0] >= 63.0 / np.sqrt(2.0)
    assert res.frequency[-1] <= 4000.0 * np.sqrt(2.0)


def test_validation_errors() -> None:
    good = np.random.default_rng(0).standard_normal(FS)
    with pytest.raises(ValueError, match="same length"):
        sound_intensity(good, good[:-1], FS, SPACING)
    with pytest.raises(ValueError, match="spacing"):
        sound_intensity(good, good, FS, 0.0)
    with pytest.raises(ValueError, match="spacing"):
        sound_intensity(good, good, FS, -0.01)
    with pytest.raises(ValueError, match="fs"):
        sound_intensity(good, good, 0, SPACING)
    with pytest.raises(ValueError, match="fs"):
        sound_intensity(good, good, -48000, SPACING)
    with pytest.raises(ValueError, match="rho"):
        sound_intensity(good, good, FS, SPACING, rho=0.0)
    with pytest.raises(ValueError, match="'c'"):
        sound_intensity(good, good, FS, SPACING, c=-1.0)
    with pytest.raises(ValueError, match="fraction"):
        sound_intensity(good, good, FS, SPACING, fraction=2)
    with pytest.raises(ValueError, match="limits"):
        sound_intensity(good, good, FS, SPACING, limits=[100.0])
    with pytest.raises(ValueError, match="limits"):
        sound_intensity(good, good, FS, SPACING, limits=[1000.0, 100.0])
    with pytest.raises(ValueError, match="1D"):
        sound_intensity(np.zeros((2, 100)), np.zeros((2, 100)), FS, SPACING)
    with pytest.raises(ValueError, match="too short"):
        sound_intensity(good[:8], good[:8], FS, SPACING)


def test_field_indicators_uniform_field() -> None:
    """Uniform positive intensity: F4 = 0 and F2 = F3; a plane-wave-like
    surface gives F2 = 10*lg(rho*c/400) = 0,14 dB."""
    i_n = np.full(8, 1.0 / (RHO * C))  # plane-wave intensity for 1 Pa^2
    lp = np.full(8, 93.98)  # 1 Pa^2 mean-square pressure
    ind = field_indicators(lp, i_n)
    assert isinstance(ind, FieldIndicators)
    assert ind.f4 == pytest.approx(0.0, abs=1e-12)
    assert ind.f2 == pytest.approx(ind.f3, abs=1e-12)
    assert ind.f2 == pytest.approx(10 * np.log10(RHO * C / 400.0), abs=0.02)


def test_field_indicators_negative_partial_power() -> None:
    """A negative-intensity segment raises F3 above F2 (A.6 vs A.3)."""
    i_n = np.array([2.0e-3, 1.5e-3, 1.0e-3, -0.5e-3])
    lp = np.full(4, 90.0)
    ind = field_indicators(lp, i_n)
    assert ind.f3 > ind.f2
    assert ind.f4 > 0.0
    # Hand-computed anchors: mean|In| = 1,25e-3, mean In = 1,0e-3.
    lp_surf = 90.0
    assert ind.f2 == pytest.approx(lp_surf - 10 * np.log10(1.25e-3 / 1e-12), abs=1e-9)
    assert ind.f3 == pytest.approx(lp_surf - 10 * np.log10(1.0e-3 / 1e-12), abs=1e-9)


def test_field_indicators_validation() -> None:
    with pytest.raises(ValueError, match="same length"):
        field_indicators([90.0, 91.0], [1e-3])
    with pytest.raises(ValueError, match="two measurement positions"):
        field_indicators([90.0], [1e-3])
    with pytest.raises(ValueError, match="not positive"):
        field_indicators([90.0, 90.0], [1e-3, -2e-3])


def test_dynamic_capability_index() -> None:
    """Ld = delta_pI0 - K (ISO 9614-1 equation (10)); adequate when
    Ld > F2 (criterion 1, equation (B.1))."""
    assert dynamic_capability_index(18.0) == pytest.approx(8.0)
    assert dynamic_capability_index(18.0, bias_error_factor=7.0) == pytest.approx(11.0)
    with pytest.raises(ValueError, match="bias_error_factor"):
        dynamic_capability_index(18.0, bias_error_factor=0.0)
