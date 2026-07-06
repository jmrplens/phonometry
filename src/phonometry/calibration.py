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


# IEC 60942:2017 Table 2 (p. 16): short-term level fluctuation acceptance
# limits in dB by range of nominal frequencies, class 1 column. Classes LS
# and 2 are only specified for 160 Hz to 1250 Hz (0,03 / 0,15 dB); the other
# rows carry "-" for them, so this table exposes the class 1 limits only.
# Rows: (lower bound exclusive*, upper bound inclusive, limit). *The first
# row starts at the 31,5 Hz nominal band edge, treated as inclusive here.
_FLUCTUATION_LIMITS_CLASS1_DB = (
    (31.5, 63.0, 0.20),
    (63.0, 160.0, 0.10),  # Table 2: "> 63 to < 160"; 160 belongs to next row
    (160.0, 1250.0, 0.07),
    (1250.0, 4000.0, 0.07),
    (4000.0, 8000.0, 0.07),
    (8000.0, 16000.0, 0.07),
)


def _class1_fluctuation_limit(frequency: float) -> float:
    """Class 1 short-term fluctuation limit for a nominal calibrator frequency.

    IEC 60942:2017 Table 2. Frequencies outside the specified 31,5 Hz to
    16 kHz span fall back to the strictest limit (0,07 dB).
    """
    for low, high, limit in _FLUCTUATION_LIMITS_CLASS1_DB:
        if low <= frequency <= high:
            return limit
    return 0.07


def calculate_sensitivity(
    ref_signal: List[float] | np.ndarray,
    target_spl: float = 94.0,
    ref_pressure: float = 2e-5,
    fs: int | None = None,
    validate: bool = True,
    max_fluctuation_db: float | None = None,
    frequency: float = 1000.0,
) -> float:
    """
    Calculate the calibration factor (multiplier) to convert digital units
    to Pascals based on a reference recording (e.g., 1kHz @ 94dB).

    When ``fs`` is provided (and ``validate`` is True), the recording's
    stability is checked the way IEC 60942:2017 specifies for the calibrator
    itself (5.3.3): levels are measured with time-weighting F and the
    *short-term level fluctuation* — the absolute difference between each of
    the maximum and minimum levels and the mean level — must not exceed the
    Table 2 acceptance limit for the calibrator class (class 1: 0.07 dB
    between 160 Hz and 1.25 kHz, relaxed to 0.10/0.20 dB below 160/63 Hz
    because the F time-weighting itself ripples at low frequencies). A larger
    fluctuation usually means a badly coupled microphone or handling noise in
    the recording, which would silently corrupt every calibrated level; a
    :class:`CalibrationWarning` is emitted.

    .. note:: IEC 60942 certifies calibrators over 60 s of operation sampled
       at least 30 times; this check applies the same criterion to whatever
       settled portion of the recording is available (>= 1 s after the 1 s
       integrator attack).

    :param ref_signal: Recording of the calibration tone.
    :param target_spl: The known SPL level of the calibrator (default 94 dB).
    :param ref_pressure: Reference pressure (default 20 microPascals).
    :param fs: Sample rate of the recording in Hz. Required for the
        stability validation; without it the check is skipped.
    :param validate: If True (default) and ``fs`` is given, warn when the
        recording's short-term level fluctuation exceeds the limit.
    :param max_fluctuation_db: Explicit fluctuation limit in dB. Default
        (None) resolves the IEC 60942:2017 Table 2 class 1 limit for
        ``frequency``.
    :param frequency: Nominal frequency of the calibration tone in Hz
        (default 1000.0), used to select the Table 2 row.
    :return: Calibration factor (sensitivity multiplier).
    """
    signal_arr = np.asarray(ref_signal, dtype=np.float64)
    if signal_arr.size == 0:
        raise ValueError("Reference signal is empty, cannot calibrate.")
    rms_ref = np.sqrt(np.mean(signal_arr ** 2))
    if rms_ref == 0:
        raise ValueError("Reference signal is silent, cannot calibrate.")

    if validate and fs is not None:
        limit = (
            max_fluctuation_db
            if max_fluctuation_db is not None
            else _class1_fluctuation_limit(frequency)
        )
        _validate_reference_stability(signal_arr, fs, limit)

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
            "stability (IEC 60942 measures the generated level over 60 s). "
            "Record a longer, steady tone.",
            CalibrationWarning,
            stacklevel=3,
        )
        return
    envelope = time_weighting(signal_arr, fs, mode="fast")
    skip = int(1.0 * fs)
    steady = np.maximum(envelope[..., skip:], np.finfo(float).eps)
    levels_db = 10 * np.log10(steady)
    # IEC 60942:2017 5.3.3: |max - mean| and |min - mean| shall each not
    # exceed the limit. Computed per channel: channels may sit at different
    # (individually stable) levels, which must not read as fluctuation.
    mean = np.mean(levels_db, axis=-1, keepdims=True)
    deviation = np.max(np.abs(levels_db - mean), axis=-1)
    fluctuation = float(np.max(deviation))
    if fluctuation > max_fluctuation_db:
        warnings.warn(
            f"Calibration tone level fluctuation is {fluctuation:.2f} dB "
            f"(limit {max_fluctuation_db:.2f} dB per IEC 60942:2017 Table 2). "
            "Check the microphone coupling and trim handling noise before "
            "trusting the resulting sensitivity.",
            CalibrationWarning,
            stacklevel=3,
        )
