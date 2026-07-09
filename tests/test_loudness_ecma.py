#  Copyright (c) 2026. Jose M. Requena-Plens
"""
ECMA-418-2:2025 (Sottek Hearing Model) loudness conformance tests.

The primary oracle is the standard's own calibration (Clause 5.1.8): a
1 kHz sinusoid at 40 dB SPL yields 1 sone_HMS via the Clause 8 method. The
standard ships no reference WAVs and its Annex A is graphical only, so the
remaining checks are internal consistency properties the standard implies
(monotonicity in level, silence, field/resampling handling, structure).
"""

import numpy as np
import pytest

from phonometry import EcmaLoudness, loudness_ecma

FS = 48000


def _tone(freq: float, level_db: float, seconds: float = 1.2) -> np.ndarray:
    """Pure tone at an SPL (dB re 20 uPa), pressure in pascals."""
    t = np.arange(int(FS * seconds)) / FS
    amp = np.sqrt(2.0) * 2e-5 * 10 ** (level_db / 20.0)
    return amp * np.sin(2.0 * np.pi * freq * t)


@pytest.fixture(scope="module")
def ref_1k_40() -> EcmaLoudness:
    """The calibration signal result, computed once for the module."""
    return loudness_ecma(_tone(1000.0, 40.0), FS)


# --------------------------------------------------------------------------
# Primary reference value (Clause 5.1.8 calibration)
# --------------------------------------------------------------------------


def test_calibration_1khz_40db_is_one_sone(ref_1k_40: EcmaLoudness) -> None:
    # c_N is defined so the 1 kHz / 40 dB tone gives 1 sone_HMS; the standard
    # allows c_N to vary within 0.25 %, and implementation differences add a
    # little more, so a 3 % window is comfortably tight.
    assert ref_1k_40.loudness == pytest.approx(1.0, abs=0.03)


# --------------------------------------------------------------------------
# Internal cross-checks
# --------------------------------------------------------------------------


def test_monotonic_in_level() -> None:
    values = [loudness_ecma(_tone(1000.0, lvl), FS).loudness for lvl in (20, 40, 60, 80)]
    assert values[0] < values[1] < values[2] < values[3]
    # 40 dB is the 1-sone anchor; higher levels are clearly louder.
    assert values[1] == pytest.approx(1.0, abs=0.03)
    assert values[2] > 2.0
    assert values[3] > 5.0


def test_silence_is_zero() -> None:
    result = loudness_ecma(np.zeros(int(FS * 1.2)), FS)
    assert result.loudness == 0.0
    assert np.all(result.specific_loudness == 0.0)


def test_subthreshold_tone_is_inaudible() -> None:
    # A 1 kHz tone at -10 dB SPL is well below the threshold in quiet.
    result = loudness_ecma(_tone(1000.0, -10.0), FS)
    assert result.loudness < 0.01


def test_specific_loudness_peaks_near_tone(ref_1k_40: EcmaLoudness) -> None:
    peak_band = int(np.argmax(ref_1k_40.specific_loudness))
    assert ref_1k_40.centre_frequencies[peak_band] == pytest.approx(1000.0, rel=0.15)


# --------------------------------------------------------------------------
# Field handling and resampling
# --------------------------------------------------------------------------


def test_free_and_diffuse_fields_differ() -> None:
    free = loudness_ecma(_tone(1000.0, 60.0), FS, field="free").loudness
    diffuse = loudness_ecma(_tone(1000.0, 60.0), FS, field="diffuse").loudness
    # Both plausible loudspeaker-range values, but the ear filter differs.
    assert free > 1.0 and diffuse > 1.0
    assert free != diffuse


def test_resampling_matches_native_rate() -> None:
    fs_alt = 44100
    t = np.arange(int(fs_alt * 1.2)) / fs_alt
    amp = np.sqrt(2.0) * 2e-5 * 10 ** (40.0 / 20.0)
    x = amp * np.sin(2.0 * np.pi * 1000.0 * t)
    resampled = loudness_ecma(x, fs_alt).loudness
    assert resampled == pytest.approx(1.0, abs=0.05)


# --------------------------------------------------------------------------
# Result structure and validation
# --------------------------------------------------------------------------


def test_result_structure(ref_1k_40: EcmaLoudness) -> None:
    assert ref_1k_40.specific_loudness.shape == (53,)
    assert ref_1k_40.bark.shape == (53,)
    assert ref_1k_40.bark[0] == pytest.approx(0.5)
    assert ref_1k_40.bark[-1] == pytest.approx(26.5)
    assert ref_1k_40.centre_frequencies.shape == (53,)
    assert ref_1k_40.time.shape == ref_1k_40.loudness_vs_time.shape
    assert ref_1k_40.field == "free"
    # Time-dependent loudness is sampled at 187.5 Hz (Clause 6.2.6).
    dt = np.diff(ref_1k_40.time)
    assert np.allclose(dt, 1.0 / 187.5)


def test_invalid_field() -> None:
    with pytest.raises(ValueError):
        loudness_ecma(_tone(1000.0, 40.0, seconds=0.5), FS, field="reverberant")


def test_invalid_fs() -> None:
    with pytest.raises(ValueError):
        loudness_ecma(_tone(1000.0, 40.0, seconds=0.5), 0.0)


def test_empty_signal() -> None:
    with pytest.raises(ValueError):
        loudness_ecma(np.array([]), FS)


def test_plot_smoke(ref_1k_40: EcmaLoudness) -> None:
    import matplotlib

    matplotlib.use("Agg")
    axes = ref_1k_40.plot()
    assert axes.shape == (2,)
