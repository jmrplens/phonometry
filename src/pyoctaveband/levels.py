#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Integrated and statistical sound levels (Leq, LAeq, LN percentiles).
"""

from __future__ import annotations

from typing import List

import numpy as np

from .parametric_filters import time_weighting, weighting_filter
from .utils import _typesignal

_REF_PRESSURE = 2e-5


def _level_db(mean_square: np.ndarray, calibration_factor: float, dbfs: bool) -> np.ndarray:
    """Convert mean-square values to dB SPL (re 20 uPa) or dBFS."""
    eps = np.finfo(float).eps
    rms = np.sqrt(np.maximum(mean_square, eps)) * calibration_factor
    if dbfs:
        return np.asarray(20 * np.log10(np.maximum(rms, eps)))
    return np.asarray(20 * np.log10(np.maximum(rms, eps) / _REF_PRESSURE))


def leq(
    x: List[float] | np.ndarray,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
) -> float | np.ndarray:
    """
    Equivalent continuous sound level (Leq) over the whole signal.

    :param x: Input signal (1D or 2D [channels, samples]), raw pressure units.
    :param calibration_factor: Multiplier converting digital units to Pascals.
    :param dbfs: If True, return dBFS (0 dB = RMS 1.0) instead of dB SPL.
    :return: Scalar for 1D input, array of shape (channels,) for 2D input.
    """
    x_proc = _typesignal(x)
    ms = np.mean(x_proc**2, axis=-1)
    out = _level_db(np.asarray(ms), calibration_factor, dbfs)
    return float(out) if out.ndim == 0 else out


def laeq(
    x: List[float] | np.ndarray,
    fs: int,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
) -> float | np.ndarray:
    """
    A-weighted equivalent continuous sound level (LAeq).

    :param x: Input signal (1D or 2D [channels, samples]), raw pressure units.
    :param fs: Sample rate in Hz.
    :param calibration_factor: Multiplier converting digital units to Pascals.
    :param dbfs: If True, return dBFS instead of dB SPL.
    :return: Scalar for 1D input, array of shape (channels,) for 2D input.
    """
    return leq(weighting_filter(x, fs, "A"), calibration_factor, dbfs)
