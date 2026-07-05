#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Integrated and statistical sound levels (Leq, LAeq, LN percentiles).
"""

from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np

from .parametric_filters import time_weighting, weighting_filter
from .utils import _typesignal

_REF_PRESSURE = 2e-5


def _level_db(mean_square: np.ndarray, calibration_factor: float, dbfs: bool) -> np.ndarray:
    """Convert mean-square values to dB SPL (re 20 uPa) or dBFS."""
    eps = np.finfo(float).eps
    rms = np.sqrt(np.maximum(mean_square, eps))
    if dbfs:
        # dBFS is relative to digital full scale: calibration does not apply
        # (consistent with OctaveFilterBank's dbfs mode).
        return np.asarray(20 * np.log10(np.maximum(rms, eps)))
    rms = rms * calibration_factor
    return np.asarray(20 * np.log10(np.maximum(rms, eps) / _REF_PRESSURE))


def _validate_level_input(x_proc: np.ndarray, calibration_factor: float) -> None:
    """Shared validation for the public level functions."""
    if x_proc.shape[-1] == 0:
        raise ValueError("Input signal 'x' cannot be empty.")
    if calibration_factor <= 0:
        raise ValueError("'calibration_factor' must be positive.")


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
    _validate_level_input(x_proc, calibration_factor)
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


def ln_levels(
    x: List[float] | np.ndarray,
    fs: int,
    n: Sequence[int] = (10, 50, 90),
    mode: str = "fast",
    weighting: str | None = None,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
) -> Dict[int, float | np.ndarray]:
    """
    Statistical percentile levels (LN) from the time-weighted level envelope.

    L10 is the level exceeded 10% of the time (90th percentile of the level
    distribution), L90 the level exceeded 90% of the time, etc.

    :param x: Input signal (1D or 2D [channels, samples]), raw pressure units.
    :param fs: Sample rate in Hz.
    :param n: Percentile exceedance values, e.g. (10, 50, 90).
    :param mode: Time weighting for the envelope: 'fast', 'slow' or 'impulse'.
    :param weighting: Optional frequency weighting: 'A', 'C', 'Z' or None.
    :param calibration_factor: Multiplier converting digital units to Pascals.
    :param dbfs: If True, return dBFS instead of dB SPL.
    :return: Dict mapping each N to its level (scalar for 1D input,
        array (channels,) for 2D input).
    """
    x_proc = _typesignal(x)
    _validate_level_input(x_proc, calibration_factor)
    for value in n:
        if not 0 < value < 100:
            raise ValueError("Percentile values in 'n' must be between 0 and 100.")
    if weighting is not None and weighting.upper() != "Z":
        x_proc = weighting_filter(x_proc, fs, weighting)

    envelope = time_weighting(x_proc, fs, mode=mode)
    # Discard the attack transient of the exponential integrator (~2*tau)
    tau = {"fast": 0.125, "slow": 1.0, "impulse": 0.035}[mode.lower()]
    skip = min(int(2 * tau * fs), envelope.shape[-1] // 2)
    levels_db = _level_db(envelope[..., skip:], calibration_factor, dbfs)

    result: Dict[int, float | np.ndarray] = {}
    for value in n:
        p = np.percentile(levels_db, 100 - value, axis=-1)
        result[value] = float(p) if np.ndim(p) == 0 else np.asarray(p)
    return result
