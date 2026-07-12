#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for fluctuation strength (Fastl & Zwicker Ch. 10; Osses et al. 2016).

The closed form for AM broadband noise (Eq. 10.2) is exact and tested against
hand values. The signal model (Osses 2016) has no numeric standard; it is
cross-checked against the literature reference values of Osses 2016 Table 1 and
the 1-vacil calibration point, to a documented tolerance.
"""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

import reference_data as ref
from phonometry import (
    FluctuationStrengthResult,
    fluctuation_strength,
    fluctuation_strength_am_noise,
)

_FS = 44100
_P_REF = 2e-5


def _am_tone(fc: float, level_db: float, m: float, fmod: float, dur: float = 4.0) -> np.ndarray:
    t = np.arange(int(_FS * dur)) / _FS
    x = (1.0 + m * np.sin(2 * np.pi * fmod * t)) * np.sin(2 * np.pi * fc * t)
    return np.asarray(x / np.sqrt(np.mean(x**2)) * _P_REF * 10 ** (level_db / 20))


# ---------------------------------------------------------------------------
# Closed form (Eq. 10.2) -- exact
# ---------------------------------------------------------------------------
def test_am_noise_matches_hand_value() -> None:
    assert fluctuation_strength_am_noise(60.0, 1.0, 4.0) == pytest.approx(
        ref.FS_BBN_60_1_4, abs=1e-3
    )


def test_am_noise_closed_form() -> None:
    for lvl, m, fmod in [(70.0, 0.5, 8.0), (55.0, 1.0, 2.0), (80.0, 0.8, 16.0)]:
        num = 5.8 * (1.25 * m - 0.25) * (0.05 * lvl - 1.0)
        den = (fmod / 5.0) ** 2 + (4.0 / fmod) + 1.5
        assert fluctuation_strength_am_noise(lvl, m, fmod) == pytest.approx(
            max(0.0, num / den)
        )


def test_am_noise_bandpass_peak_near_4hz() -> None:
    # Eq. 10.2 has a band-pass shape in fmod peaking around 4 Hz.
    vals = {f: fluctuation_strength_am_noise(60.0, 1.0, f) for f in (1, 2, 4, 8, 16, 32)}
    assert max(vals, key=lambda k: vals[k]) == 4


def test_am_noise_clamped_at_zero() -> None:
    # Low level / low modulation drive the formula negative -> clamped to 0.
    assert fluctuation_strength_am_noise(10.0, 1.0, 4.0) == 0.0
    assert fluctuation_strength_am_noise(60.0, 0.1, 4.0) == 0.0


@pytest.mark.parametrize("bad_m", [-0.1, 1.1, math.nan])
def test_am_noise_rejects_bad_modulation(bad_m: float) -> None:
    with pytest.raises(ValueError, match="modulation_factor"):
        fluctuation_strength_am_noise(60.0, bad_m, 4.0)


@pytest.mark.parametrize("bad_f", [0.0, -1.0, math.inf])
def test_am_noise_rejects_bad_frequency(bad_f: float) -> None:
    with pytest.raises(ValueError, match="mod_frequency"):
        fluctuation_strength_am_noise(60.0, 1.0, bad_f)


# ---------------------------------------------------------------------------
# Signal model (Osses 2016) -- clean-room, cross-checked to a tolerance
# ---------------------------------------------------------------------------
def test_signal_reference_is_one_vacil() -> None:
    # The 1 kHz / 60 dB / m=1 / 4 Hz AM tone defines 1 vacil; the model is
    # calibrated to it.
    res = fluctuation_strength(_am_tone(1000.0, 60.0, 1.0, 4.0), _FS)
    assert res.fluctuation_strength == pytest.approx(
        ref.FS_CALIBRATION_VACIL, abs=0.1
    )


def test_signal_result_fields_and_plot() -> None:
    res = fluctuation_strength(_am_tone(1000.0, 60.0, 1.0, 4.0), _FS)
    assert isinstance(res, FluctuationStrengthResult)
    assert res.specific.shape == (47,)
    assert res.bark_axis.shape == (47,)
    assert res.time_dependent.ndim == 1
    ax = res.plot()
    assert ax is not None


def test_signal_bandpass_shape_over_modulation() -> None:
    # Fluctuation strength peaks for modulation near 4 Hz and falls for very
    # slow and fast modulation (band-pass sensation).
    f_slow = fluctuation_strength(_am_tone(1000.0, 70.0, 1.0, 1.0), _FS).fluctuation_strength
    f_peak = fluctuation_strength(_am_tone(1000.0, 70.0, 1.0, 4.0), _FS).fluctuation_strength
    f_fast = fluctuation_strength(_am_tone(1000.0, 70.0, 1.0, 32.0), _FS).fluctuation_strength
    assert f_peak > f_slow
    assert f_peak > f_fast


def test_signal_am_tone_sweep_tracks_literature() -> None:
    # Cross-check the AM-tone 70 dB modulation sweep against the Osses 2016
    # Table 1 literature values: band-pass shape with the peak at 4 Hz and a
    # high correlation with the reference trend (no numeric standard exists).
    model = np.array(
        [
            fluctuation_strength(_am_tone(1000.0, 70.0, 1.0, fm), _FS).fluctuation_strength
            for fm in ref.FS_AM_TONE_FMOD_HZ
        ]
    )
    lit = np.array(ref.FS_AM_TONE_70DB_LITERATURE)
    # Peak of the model at 4 Hz (index 2).
    assert int(np.argmax(model)) == 2
    # Pearson correlation with the literature trend.
    r = float(np.corrcoef(model, lit)[0, 1])
    assert r >= 0.9
    # Every point within a factor of ~2 of the literature value.
    ratio = model / lit
    assert np.all((ratio > 0.5) & (ratio < 2.1))


def test_signal_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        fluctuation_strength(np.zeros((2, 2)), _FS)
    with pytest.raises(ValueError):
        fluctuation_strength(np.array([]), _FS)
    with pytest.raises(ValueError):
        fluctuation_strength(np.array([1.0, np.nan]), _FS)
    with pytest.raises(ValueError):
        fluctuation_strength(_am_tone(1000.0, 60.0, 1.0, 4.0), 0.0)
