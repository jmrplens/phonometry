#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Calibration-tone stability validation (IEC 60942:2017).

IEC 60942:2017 (EN IEC 60942:2018) 5.3.3: the short-term level fluctuation is
measured with time-weighting F over 60 s, sampling at least 30 times; the
absolute value of the difference between each of the maximum and minimum
levels and the mean level shall not exceed the Table 2 (p. 16) acceptance
limits. Class 1: 0.20 dB in 31,5-63 Hz, 0.10 dB in >63-<160 Hz, 0.07 dB from
160 Hz up (classes LS/2 are only specified in 160-1250 Hz: 0.03/0.15 dB).
"""

import warnings
from contextlib import contextmanager
from typing import Iterator

import numpy as np
import pytest

from phonometry import CalibrationWarning, calculate_sensitivity

FS = 48000


def _cal_tone(seconds: float = 5.0, am_depth: float = 0.0) -> np.ndarray:
    """94 dB-style 1 kHz calibrator tone, optionally amplitude-modulated."""
    t = np.arange(int(FS * seconds)) / FS
    am = 1.0 + am_depth * np.sin(2 * np.pi * 2.0 * t)
    return 0.5 * am * np.sin(2 * np.pi * 1000 * t)


@contextmanager
def _assert_no_calibration_warning() -> Iterator[None]:
    with warnings.catch_warnings():
        warnings.simplefilter("error", CalibrationWarning)
        yield


def test_stable_tone_no_warning() -> None:
    with _assert_no_calibration_warning():
        factor = calculate_sensitivity(_cal_tone(), fs=FS)
    assert factor > 0


def test_unstable_tone_warns() -> None:
    """5% AM -> ~0.4 dB fluctuation, far beyond the 0.10 dB class 1 limit."""
    with pytest.warns(CalibrationWarning, match="fluctuation"):
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS)


def test_validation_can_be_disabled() -> None:
    with _assert_no_calibration_warning():
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, validate=False)


def test_custom_fluctuation_limit() -> None:
    with pytest.warns(CalibrationWarning):
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, max_fluctuation_db=0.1)
    with _assert_no_calibration_warning():
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, max_fluctuation_db=1.0)


def test_empty_reference_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        calculate_sensitivity(np.array([]), fs=FS)


def test_too_short_recording_warns() -> None:
    with pytest.warns(CalibrationWarning, match="shorter than 2 s"):
        calculate_sensitivity(_cal_tone(seconds=1.0), fs=FS)


def test_multichannel_stable_at_different_levels_no_warning() -> None:
    """Per-channel stability: a level offset between channels is not fluctuation."""
    x = np.stack([_cal_tone(), 0.5 * _cal_tone()])
    with _assert_no_calibration_warning():
        calculate_sensitivity(x, fs=FS)


def test_default_limit_follows_iec_60942_2017_table2() -> None:
    """~0.13 dB fluctuation: over the 0.07 dB class 1 limit at 1 kHz, but
    within the 0.20 dB limit for a 31.5-63 Hz nominal frequency (Table 2)."""
    x = _cal_tone(am_depth=0.015)
    with pytest.warns(CalibrationWarning, match="Table 2"):
        calculate_sensitivity(x, fs=FS)
    with _assert_no_calibration_warning():
        calculate_sensitivity(x, fs=FS, frequency=50.0)


def test_asymmetric_fluctuation_uses_max_min_vs_mean() -> None:
    """A one-sided dip must be judged by |min - mean|, not (max - min) / 2."""
    x = _cal_tone(seconds=5.0)
    dip = np.ones_like(x)
    # 200 ms one-sided level dip of ~0.2 dB in the settled region
    i0, i1 = int(3.0 * FS), int(3.2 * FS)
    dip[i0:i1] = 10 ** (-0.2 / 20)
    with pytest.warns(CalibrationWarning, match="fluctuation"):
        calculate_sensitivity(x * dip, fs=FS)


def test_table2_row_boundaries() -> None:
    """IEC 60942:2017 Table 2: 160 Hz belongs to the 0.07 dB row and 63 Hz
    to the 0.20 dB row; the open interval between them gets 0.10 dB."""
    from phonometry.calibration import _class1_fluctuation_limit

    assert _class1_fluctuation_limit(63.0) == pytest.approx(0.20)
    assert _class1_fluctuation_limit(100.0) == pytest.approx(0.10)
    assert _class1_fluctuation_limit(160.0) == pytest.approx(0.07)
    assert _class1_fluctuation_limit(1000.0) == pytest.approx(0.07)
