#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Calibration-tone stability validation (IEC 60942).

BS EN 60942:2003 §5.2.3 and Table 1: short-term level fluctuation of the
generated level, measured with time-weighting F, as one-half of the
difference between the maximum and minimum levels; class 1 limit 0.10 dB
(class LS 0.05 dB) for nominal frequencies 160 Hz to 1.25 kHz.
"""

import numpy as np
import pytest

from pyoctaveband import CalibrationWarning, calculate_sensitivity

FS = 48000


def _cal_tone(seconds: float = 5.0, am_depth: float = 0.0) -> np.ndarray:
    """94 dB-style 1 kHz calibrator tone, optionally amplitude-modulated."""
    t = np.arange(int(FS * seconds)) / FS
    am = 1.0 + am_depth * np.sin(2 * np.pi * 2.0 * t)
    return 0.5 * am * np.sin(2 * np.pi * 1000 * t)


def test_stable_tone_no_warning() -> None:
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", CalibrationWarning)
        factor = calculate_sensitivity(_cal_tone(), fs=FS)
    assert factor > 0


def test_unstable_tone_warns() -> None:
    """5% AM -> ~0.4 dB fluctuation, far beyond the 0.10 dB class 1 limit."""
    with pytest.warns(CalibrationWarning, match="fluctuation"):
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS)


def test_validation_can_be_disabled() -> None:
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", CalibrationWarning)
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, validate=False)


def test_custom_fluctuation_limit() -> None:
    with pytest.warns(CalibrationWarning):
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, max_fluctuation_db=0.1)
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", CalibrationWarning)
        calculate_sensitivity(_cal_tone(am_depth=0.05), fs=FS, max_fluctuation_db=1.0)
