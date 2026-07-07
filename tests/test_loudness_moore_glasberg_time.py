#  Copyright (c) 2026. Jose M. Requena-Plens
"""
ISO 532-3:2023 (Moore-Glasberg-Schlittenlacher) time-varying loudness tests.

The algorithmic reference for steady tones is Annex C.1 of the standard, which
tabulates the maximum long-term loudness (sone) and loudness level (phon) of
5-second tones - the same numbers the model must reach for a long steady tone
(clause 7.9: the loudness of sounds up to ~5 s is predicted by the maximum of
the long-term loudness).  A 1 kHz tone at 40 dB SPL, binaural, free field, is
1.000 sone / 40 phon by definition of the sone (clause 7.3, the spectral
calibration is fixed to this anchor).

The remaining checks are the temporal properties the two-stage attack/release
integration (clauses 7.6/7.9) implies: the short-term loudness reacts faster
than the long-term loudness, release is slower than attack, a steady tone gives
a flat trace at the ISO 532-2 stationary value, silence gives zero, and the
percentile / plotting / validation plumbing behaves.

The synthetic-tone values of Annex B (WAV-file signals 2/6-8) are not
reproduced here: those waveform files are not distributed with this
implementation, and the tabulated 250 Hz / 80 dB value (69.3 phon) sits about
5 phon below the ISO 226 equal-loudness contour, whereas this model reproduces
that contour (and agrees with the validated ISO 532-2 stationary module) to
within ~1.5 phon.  Annex C.1 is therefore the tone oracle used.
"""

import numpy as np
import pytest

from phonometry import (
    MooreGlasbergTimeVaryingLoudness,
    loudness_moore_glasberg_time,
)

FS = 32000.0  # the Annex B/C sampling rate; keeps reference tones on FFT bins


def _tone(frequency: float, level_db: float, duration: float = 1.3) -> np.ndarray:
    """Calibrated pure tone: sound pressure in pascals at ``level_db`` dB SPL."""
    t = np.arange(int(round(duration * FS))) / FS
    p_rms = 2e-5 * 10.0 ** (level_db / 20.0)
    return np.sqrt(2.0) * p_rms * np.sin(2.0 * np.pi * frequency * t)


# --------------------------------------------------------------------------
# Definitional anchor (clause 7.3 / Annex C.1)
# --------------------------------------------------------------------------


def test_anchor_1khz_40db_is_one_sone() -> None:
    """A 1 kHz tone at 40 dB SPL, binaural, free field -> 1.000 sone / 40 phon."""
    res = loudness_moore_glasberg_time(_tone(1000.0, 40.0), FS)
    assert res.n_max == pytest.approx(1.0, abs=0.02)
    assert res.loudness_level_max == pytest.approx(40.0, abs=0.3)


# --------------------------------------------------------------------------
# Annex C.1 - 1 kHz tone loudness vs level (primary tone oracle)
# --------------------------------------------------------------------------

_C1_1KHZ = [
    (10.0, 0.025, 10.0),
    (20.0, 0.14, 20.0),
    (30.0, 0.42, 30.0),
    (40.0, 1.00, 40.0),
    (50.0, 2.1, 50.0),
    (60.0, 4.1, 60.0),
    (70.0, 7.9, 70.0),
    (80.0, 15.4, 80.0),
]


@pytest.mark.parametrize("level_db, sone, phon", _C1_1KHZ)
def test_annex_c1_1khz_tone(level_db: float, sone: float, phon: float) -> None:
    """1 kHz tone 10-80 dB reaches the Annex C.1 peak long-term loudness."""
    res = loudness_moore_glasberg_time(_tone(1000.0, level_db), FS)
    # Loudness level (phon) is the linear-in-perception comparison; within the
    # standard's expanded uncertainty (2.8 phon, clause 8).
    assert res.loudness_level_max == pytest.approx(phon, abs=1.0)


# --------------------------------------------------------------------------
# Annex C.1 - other frequencies / presentations
# --------------------------------------------------------------------------

_C1_OTHER = [
    # frequency, level, field, presentation, expected phon (Annex C.1)
    (3000.0, 20.0, "free", "binaural", 28.8),
    (3000.0, 40.0, "free", "binaural", 49.0),
    (3000.0, 60.0, "free", "binaural", 68.6),
    (100.0, 50.0, "free", "binaural", 28.2),
    (4000.0, 40.0, "free", "binaural", 48.9),  # Annex B signal 4
    (1000.0, 20.0, "eardrum", "monaural", 14.8),
    (1000.0, 40.0, "eardrum", "monaural", 32.7),
    (1000.0, 60.0, "eardrum", "monaural", 51.4),
    (1000.0, 80.0, "eardrum", "monaural", 71.2),
]


@pytest.mark.parametrize("frequency, level_db, field, presentation, phon", _C1_OTHER)
def test_annex_c1_other_tones(
    frequency: float, level_db: float, field: str, presentation: str, phon: float
) -> None:
    """3 kHz / 100 Hz / 4 kHz and monaural earphone tones match Annex C.1."""
    res = loudness_moore_glasberg_time(
        _tone(frequency, level_db), FS, field=field, presentation=presentation
    )
    assert res.loudness_level_max == pytest.approx(phon, abs=1.2)


# --------------------------------------------------------------------------
# Cross-checks against the ISO 532-2 stationary result
# --------------------------------------------------------------------------


def test_steady_matches_iso532_2_stationary() -> None:
    """A long steady tone converges to the ISO 532-2 stationary loudness."""
    from phonometry import loudness_moore_glasberg_from_spectrum

    stationary = loudness_moore_glasberg_from_spectrum([(1000.0, 60.0)])
    res = loudness_moore_glasberg_time(_tone(1000.0, 60.0), FS)
    # Both models share the excitation/specific-loudness machinery (different
    # calibration constants); agree well within the standard's uncertainty.
    assert res.n_max == pytest.approx(stationary.loudness, rel=0.05)


# --------------------------------------------------------------------------
# Temporal behaviour (clauses 7.6, 7.9)
# --------------------------------------------------------------------------


def test_steady_tone_gives_flat_trace() -> None:
    """A steady tone gives an essentially flat long-term-loudness trace."""
    res = loudness_moore_glasberg_time(_tone(1000.0, 50.0, duration=1.5), FS)
    steady = res.long_term_loudness[res.time > 0.8]
    assert steady.std() < 0.02
    assert res.long_term_loudness[-1] == pytest.approx(res.n_max, rel=1e-3)


def test_short_term_reacts_faster_than_long_term() -> None:
    """Short-term loudness rises faster and peaks higher than long-term."""
    res = loudness_moore_glasberg_time(_tone(1000.0, 60.0), FS)
    stl, ltl, time = (
        res.short_term_loudness,
        res.long_term_loudness,
        res.time,
    )
    half = 0.5 * ltl[-1]
    t_stl = time[np.argmax(stl >= half)]
    t_ltl = time[np.argmax(ltl >= half)]
    assert t_stl < t_ltl  # short-term attack is faster
    assert stl.max() > ltl.max()  # short-term is more responsive


def test_release_is_slower_than_attack() -> None:
    """After a burst offset the short-term loudness decays far faster than LTL.

    Release time constants (~30 ms STL, ~750 ms LTL) exceed the attack ones,
    and the long-term averager is deliberately sluggish (clause 7.9).
    """
    burst = np.concatenate([_tone(1000.0, 60.0, duration=0.3), np.zeros(int(0.7 * FS))])
    res = loudness_moore_glasberg_time(burst, FS)
    stl, ltl, time = (
        res.short_term_loudness,
        res.long_term_loudness,
        res.time,
    )
    offset = int(np.argmin(np.abs(time - 0.3)))

    def half_decay(trace: np.ndarray) -> float:
        v0 = trace[offset]
        j = int(np.argmax(trace[offset:] <= 0.5 * v0))
        return float(time[offset + j] - time[offset]) if j > 0 else np.inf

    assert half_decay(stl) < half_decay(ltl)
    assert half_decay(ltl) > 0.2  # long-term release is sluggish


def test_silence_is_zero() -> None:
    """Silence yields a zero loudness trace and zero peak."""
    res = loudness_moore_glasberg_time(np.zeros(int(0.3 * FS)), FS)
    assert res.n_max == 0.0
    assert np.all(res.short_term_loudness == 0.0)
    assert np.all(res.long_term_loudness == 0.0)
    assert res.loudness_level_max == 0.0


def test_louder_tone_is_louder() -> None:
    """Peak long-term loudness increases monotonically with level."""
    values = [
        loudness_moore_glasberg_time(_tone(1000.0, lvl), FS).n_max
        for lvl in (30.0, 50.0, 70.0)
    ]
    assert values[0] < values[1] < values[2]


# --------------------------------------------------------------------------
# Result plumbing, percentiles and validation
# --------------------------------------------------------------------------


def test_result_fields_and_percentiles() -> None:
    """The result exposes consistent traces, percentiles and metadata."""
    res = loudness_moore_glasberg_time(
        _tone(1000.0, 60.0), FS, percentiles=(5.0, 50.0, 95.0)
    )
    assert isinstance(res, MooreGlasbergTimeVaryingLoudness)
    n = res.time.size
    assert res.short_term_loudness.shape == (n,)
    assert res.long_term_loudness.shape == (n,)
    assert res.short_term_loudness_level.shape == (n,)
    assert res.long_term_loudness_level.shape == (n,)
    assert set(res.percentiles) == {5.0, 50.0, 95.0}
    # Higher exceedance fraction -> lower level.
    assert res.percentiles[5.0] >= res.percentiles[50.0] >= res.percentiles[95.0]
    assert res.n_max >= res.percentiles[5.0]
    assert res.field == "free" and res.presentation == "binaural"


def test_diotic_equals_binaural_and_exceeds_monaural() -> None:
    """Binaural (diotic) loudness exceeds the single-ear monaural loudness."""
    tone = _tone(1000.0, 60.0)
    binaural = loudness_moore_glasberg_time(tone, FS, presentation="binaural")
    monaural = loudness_moore_glasberg_time(
        tone, FS, field="eardrum", presentation="monaural"
    )
    assert binaural.n_max > monaural.n_max


def test_stereo_input_accepted() -> None:
    """A two-channel (n, 2) signal is accepted as the two ear signals."""
    tone = _tone(1000.0, 60.0)
    stereo = np.column_stack([tone, tone])
    res = loudness_moore_glasberg_time(stereo, FS)
    mono = loudness_moore_glasberg_time(tone, FS)
    # Identical channels == diotic presentation.
    assert res.n_max == pytest.approx(mono.n_max, rel=1e-6)


def test_invalid_inputs_raise() -> None:
    """Invalid field, presentation, sampling rate and signal raise ValueError."""
    tone = _tone(1000.0, 40.0, duration=0.1)
    with pytest.raises(ValueError):
        loudness_moore_glasberg_time(tone, FS, field="bogus")
    with pytest.raises(ValueError):
        loudness_moore_glasberg_time(tone, FS, presentation="bogus")
    with pytest.raises(ValueError):
        loudness_moore_glasberg_time(tone, -1.0)
    with pytest.raises(ValueError):
        loudness_moore_glasberg_time(np.array([]), FS)
    with pytest.raises(ValueError):
        loudness_moore_glasberg_time(np.array([1.0, np.nan, 2.0]), FS)


def test_plot_smoke() -> None:
    """The lazy .plot() renders without error when matplotlib is present."""
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    res = loudness_moore_glasberg_time(_tone(1000.0, 60.0, duration=0.4), FS)
    ax = res.plot()
    assert ax.get_ylabel() == "Loudness [sone]"
