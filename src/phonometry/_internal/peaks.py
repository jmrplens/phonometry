#  Copyright (c) 2026. Jose M. Requena-Plens
"""Inter-sample peak recovery by polyphase oversampling (private).

The true peak of a band-limited continuous waveform generally falls between
samples, so a raw on-grid maximum under-reads it (worst for sustained tones
near integer submultiples of the sample rate). Both the C-weighted peak
level (:func:`phonometry.metrology.levels.lc_peak`, IEC 61672-1) and the
true-peak programme level (:func:`phonometry.broadcast.true_peak_level`,
ITU-R BS.1770-5 Annex 2) recover the inter-sample peak the same way:
polyphase-oversample the signal, then take the absolute maximum. This module
is the single home of that machinery.
"""

from __future__ import annotations

import numpy as np
from scipy import signal


def inter_sample_peak(x: np.ndarray, factor: int) -> np.ndarray:
    """Absolute peak along the last axis after ``factor``-times oversampling.

    Zero-stuffs and low-pass interpolates via
    :func:`scipy.signal.resample_poly` (a Kaiser-windowed FIR polyphase
    interpolator, the "similar or superior" filter that ITU-R BS.1770-5
    Annex 2 admits in place of its example 48-tap filter), then returns the
    absolute maximum. ``factor=1`` skips the oversampling and reduces to the
    on-grid sample peak.

    :param x: Input signal, 1D or 2D ``[channels, samples]``.
    :param factor: Integer oversampling factor (>= 1).
    :return: The absolute peak per channel, in the input's linear units
        (0-d array for 1D input).
    """
    if factor > 1 and x.shape[-1] > 0:
        # Recover inter-sample peaks: the on-grid maximum misses the true
        # continuous peak between samples for sustained HF tones.
        x = signal.resample_poly(x, factor, 1, axis=-1)
    return np.asarray(np.max(np.abs(x), axis=-1))
