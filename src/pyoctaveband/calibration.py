#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Calibration utilities for mapping digital signals to physical SPL levels.
"""

from __future__ import annotations

import warnings
from typing import List

import numpy as np


class CalibrationWarning(UserWarning):
    """The calibration reference recording looks unreliable."""


def calculate_sensitivity(
    ref_signal: List[float] | np.ndarray,
    target_spl: float = 94.0,
    ref_pressure: float = 2e-5,
    fs: int | None = None,
    validate: bool = True,
    max_fluctuation_db: float = 0.10,
) -> float:
    """
    Calculate the calibration factor (multiplier) to convert digital units
    to Pascals based on a reference recording (e.g., 1kHz @ 94dB).

    When ``fs`` is provided (and ``validate`` is True), the recording's
    stability is checked the way IEC 60942 specifies for the calibrator
    itself: the short-term level fluctuation — one-half of the difference
    between the maximum and minimum F-time-weighted levels (BS EN 60942:2003,
    5.2.3) — must not exceed ``max_fluctuation_db`` (Table 1: 0.10 dB for a
    class 1 calibrator between 160 Hz and 1.25 kHz). A larger fluctuation
    usually means a badly coupled microphone or handling noise in the
    recording, which would silently corrupt every calibrated level; a
    :class:`CalibrationWarning` is emitted.

    :param ref_signal: Recording of the calibration tone.
    :param target_spl: The known SPL level of the calibrator (default 94 dB).
    :param ref_pressure: Reference pressure (default 20 microPascals).
    :param fs: Sample rate of the recording in Hz. Required for the
        stability validation; without it the check is skipped.
    :param validate: If True (default) and ``fs`` is given, warn when the
        recording's short-term level fluctuation exceeds the limit.
    :param max_fluctuation_db: Fluctuation limit in dB (default 0.10, the
        IEC 60942 class 1 tolerance).
    :return: Calibration factor (sensitivity multiplier).
    """
    signal_arr = np.asarray(ref_signal, dtype=np.float64)
    if signal_arr.size == 0:
        raise ValueError("Reference signal is empty, cannot calibrate.")
    rms_ref = np.sqrt(np.mean(signal_arr ** 2))
    if rms_ref == 0:
        raise ValueError("Reference signal is silent, cannot calibrate.")

    if validate and fs is not None:
        _validate_reference_stability(signal_arr, fs, max_fluctuation_db)

    factor = (ref_pressure * 10 ** (target_spl / 20)) / rms_ref
    return float(factor)


def _validate_reference_stability(
    signal_arr: np.ndarray, fs: int, max_fluctuation_db: float
) -> None:
    """Warn if the F-weighted level of the recording fluctuates too much."""
    from .parametric_filters import time_weighting

    # The integrator attack lasts ~8*tau (1 s for F); we need at least
    # another second of settled envelope to assess the fluctuation.
    if signal_arr.shape[-1] < 2 * fs:
        warnings.warn(
            "Calibration tone is shorter than 2 s: too short to validate its "
            "stability (IEC 60942 measures the generated level over 20 s). "
            "Record a longer, steady tone.",
            CalibrationWarning,
            stacklevel=3,
        )
        return
    envelope = time_weighting(signal_arr, fs, mode="fast")
    skip = int(1.0 * fs)
    steady = np.maximum(envelope[..., skip:], np.finfo(float).eps)
    levels_db = 10 * np.log10(steady)
    fluctuation = float(levels_db.max() - levels_db.min()) / 2.0
    if fluctuation > max_fluctuation_db:
        warnings.warn(
            f"Calibration tone level fluctuation is {fluctuation:.2f} dB "
            f"(limit {max_fluctuation_db:.2f} dB per IEC 60942 Table 1). "
            "Check the microphone coupling and trim handling noise before "
            "trusting the resulting sensitivity.",
            CalibrationWarning,
            stacklevel=3,
        )
