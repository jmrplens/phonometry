#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Signal processing utilities for pyoctaveband.
"""

from __future__ import annotations

from typing import List, Tuple, cast

import numpy as np
from scipy import signal


def _typesignal(x: List[float] | np.ndarray | Tuple[float, ...]) -> np.ndarray:
    """
    Ensure signal is a float64 numpy array.

    Integer inputs (e.g. int16 audio from ``scipy.io.wavfile.read``) are
    converted to float64 to prevent silent overflow when the signal is
    squared internally. Float64 arrays are passed through without copying.

    :param x: Input signal.
    :return: Numpy float64 array.
    """
    return np.atleast_1d(np.asarray(x, dtype=np.float64))


def _resample_to_length(y: np.ndarray, factor: int, target_length: int) -> np.ndarray:
    """
    Resample signal and ensure the output matches target_length exactly.
    Handles both 1D and 2D (channels, samples) arrays.

    :param y: Input signal.
    :param factor: Resampling factor.
    :param target_length: Target length.
    :return: Resampled signal.
    """
    if factor == 1:
        # Nothing to resample: fall through to the slice/pad logic only.
        y_resampled = y
    else:
        y_resampled = cast(np.ndarray, signal.resample_poly(y, factor, 1, axis=-1))
    current_length = y_resampled.shape[-1]
    
    if current_length > target_length:
        # Slice along the last axis (works for both 1D and 2D)
        y_resampled = y_resampled[..., :target_length]
            
    elif current_length < target_length:
        diff = target_length - current_length
        # Pad only the last axis. This works for both 1D and 2D arrays.
        # For 1D, pad_width becomes `[(0, diff)]`.
        # For 2D, pad_width becomes `[(0, 0), (0, diff)]`.
        pad_width: List[Tuple[int, int]] = [(0, 0)] * (y_resampled.ndim - 1) + [(0, diff)]
            
        y_resampled = np.pad(y_resampled, pad_width, mode='constant')
        
    return y_resampled


def _downsamplingfactor(freq: List[float], fs: int, headroom: float = 1.25) -> np.ndarray:
    """
    Compute optimal downsampling factors for filter stability.

    :param freq: Band upper-edge frequencies.
    :param fs: Sample rate.
    :param headroom: Required ratio between the decimated Nyquist and the
        band's upper edge. 1.25 reproduces the classic ``fs / (2 + 0.5)``
        guard; filter types whose design extends above the upper edge
        (cheby2 stopband) need more.
    :return: Array of factors.
    """
    factor = (np.floor((fs / 2) / (headroom * np.array(freq)))).astype("int")
    return cast(np.ndarray, np.clip(factor, 1, 500))
