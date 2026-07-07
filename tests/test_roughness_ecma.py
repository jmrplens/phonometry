#  Copyright (c) 2026. Jose M. Requena-Plens
"""
ECMA-418-2:2025 (Sottek Hearing Model) roughness conformance tests.

The primary oracle is the standard's own calibration (Clause 7, intro and
7.1.7): a 1 kHz carrier, 100 % amplitude-modulated (m = 1) at 70 Hz and a
sound pressure level of 60 dB SPL yields 1 asper. That is the only reference
value the standard tabulates for roughness. The remaining checks are the
behaviours the standard states qualitatively (roughness peaks near a 70 Hz
modulation rate and falls off toward low and high rates, grows with modulation
depth, an unmodulated tone and silence give ~0) plus result-structure guards.
"""

import numpy as np
import pytest

from phonometry import EcmaRoughness, roughness_ecma

FS = 48000
P0 = 2e-5


def _am_tone(
    fc: float,
    fmod: float,
    depth: float,
    level_db: float,
    seconds: float = 2.0,
) -> np.ndarray:
    """Amplitude-modulated tone, carrier RMS at ``level_db`` (pressure in Pa)."""
    t = np.arange(int(FS * seconds)) / FS
    amp = np.sqrt(2.0) * P0 * 10.0 ** (level_db / 20.0)  # carrier peak
    carrier = np.sin(2.0 * np.pi * fc * t)
    return amp * (1.0 + depth * np.cos(2.0 * np.pi * fmod * t)) * carrier


def _tone(fc: float, level_db: float, seconds: float = 2.0) -> np.ndarray:
    """Unmodulated tone, carrier RMS at ``level_db``."""
    return _am_tone(fc, 0.0, 0.0, level_db, seconds)


@pytest.fixture(scope="module")
def ref_calibration() -> EcmaRoughness:
    """The 1 kHz / 70 Hz / m=1 / 60 dB calibration signal (1 asper)."""
    return roughness_ecma(_am_tone(1000.0, 70.0, 1.0, 60.0), FS)


# --------------------------------------------------------------------------
# Primary reference value (Clause 7 calibration)
# --------------------------------------------------------------------------


def test_calibration_1khz_70hz_is_one_asper(ref_calibration: EcmaRoughness) -> None:
    # c_R (Formula 104) is the standard's tabulated value, not reverse-fit, so
    # the output lands near but not exactly 1.000; c_R may vary +/- 0.25 % and
    # implementation differences add a little, so a 10 % window is comfortable.
    assert ref_calibration.roughness == pytest.approx(1.0, abs=0.1)


# --------------------------------------------------------------------------
# Standard's qualitative behaviours
# --------------------------------------------------------------------------


def test_unmodulated_tone_is_near_zero() -> None:
    result = roughness_ecma(_tone(1000.0, 60.0), FS)
    assert result.roughness < 0.1


def test_silence_is_zero() -> None:
    result = roughness_ecma(np.zeros(FS), FS)
    assert result.roughness == pytest.approx(0.0, abs=1e-6)
    assert np.all(result.specific_roughness == 0.0)


def test_peaks_near_70hz_modulation() -> None:
    # Roughness is maximal around 70 Hz modulation and falls off toward slow
    # (< 20 Hz) and fast (> 200 Hz) modulation (Clause 7 intro, Annex C).
    r70 = roughness_ecma(_am_tone(1000.0, 70.0, 1.0, 60.0), FS).roughness
    r10 = roughness_ecma(_am_tone(1000.0, 10.0, 1.0, 60.0), FS).roughness
    r300 = roughness_ecma(_am_tone(1000.0, 300.0, 1.0, 60.0), FS).roughness
    assert r70 > r10
    assert r70 > r300


def test_grows_with_modulation_depth() -> None:
    r_full = roughness_ecma(_am_tone(1000.0, 70.0, 1.0, 60.0), FS).roughness
    r_half = roughness_ecma(_am_tone(1000.0, 70.0, 0.5, 60.0), FS).roughness
    assert r_full > r_half > 0.05


# --------------------------------------------------------------------------
# Result structure and API guards
# --------------------------------------------------------------------------


def test_result_structure(ref_calibration: EcmaRoughness) -> None:
    res = ref_calibration
    assert res.specific_roughness.shape == res.bark.shape == (53,)
    assert res.roughness_vs_time.shape == res.time.shape
    assert res.specific_roughness_vs_time.shape == (
        res.time.size,
        res.bark.size,
    )
    assert np.all(res.specific_roughness >= 0.0)
    assert np.all(res.roughness_vs_time >= 0.0)
    assert res.field == "free"


def test_invalid_field_raises() -> None:
    with pytest.raises(ValueError):
        roughness_ecma(_tone(1000.0, 60.0, 0.5), FS, field="bogus")


def test_empty_signal_raises() -> None:
    with pytest.raises(ValueError):
        roughness_ecma(np.array([]), FS)


def test_deterministic(ref_calibration: EcmaRoughness) -> None:
    again = roughness_ecma(_am_tone(1000.0, 70.0, 1.0, 60.0), FS)
    assert again.roughness == pytest.approx(ref_calibration.roughness, abs=1e-9)


def test_free_and_diffuse_differ() -> None:
    sig = _am_tone(1000.0, 70.0, 1.0, 60.0)
    free = roughness_ecma(sig, FS, field="free").roughness
    diffuse = roughness_ecma(sig, FS, field="diffuse").roughness
    assert free != diffuse
