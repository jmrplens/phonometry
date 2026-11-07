#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The Welch core every spectral density of the library is computed by.

One code path for the autospectrum, the cross-spectrum and the pair of them,
with the checks of the signal and of the segment parameters that go with it:
:mod:`phonometry.signals` builds its published estimates on it, and the
frequency response of :mod:`phonometry.electroacoustics`, the intensity of
:mod:`phonometry.emission`, the tonality of :mod:`phonometry.psychoacoustics`
and the data qualification of :mod:`phonometry.metrology` read it directly,
without importing another domain. Segments are tapered and overlapped and
never detrended, so absolute calibration is preserved (Bendat & Piersol
Section 11.5.2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .resolve import apply_calibration
from .validation import real_array, require_count, require_scalar

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

    from .signal import Signal
    from .types import WindowSpec

#: Default overlap fraction between Welch segments.
_DEFAULT_OVERLAP = 0.5
#: Minimum samples for a spectral estimate.
_MIN_SAMPLES = 32


def _positive(value: float, name: str) -> float:
    require_scalar(value, name)
    scalar = float(value)
    if not np.isfinite(scalar) or scalar <= 0.0:
        msg = f"'{name}' must be a positive, finite number."
        raise ValueError(msg)
    return scalar


def _validate_signal(
    x: Signal | ArrayLike,
    name: str,
    *,
    context: str = "a spectral estimate",
) -> NDArray[np.float64]:
    """Coerce, check and calibrate the signal argument of an estimate.

    Every one-dimensional consumer in ``signals`` and
    ``metrology.data_qualification`` enters here, which is what lets a
    :class:`phonometry.io.Signal` reach all of them at once and reach
    them the same way: the samples come out in pascals when the object
    carried a factor, and untouched otherwise. The shape and finiteness
    complaints are unchanged, and a multichannel Signal is refused by the
    same "must be one-dimensional" as a 2-D array, because these
    estimates are defined on one record.
    """
    xa = real_array(x, name)
    if xa.ndim != 1:
        msg = f"'{name}' must be one-dimensional."
        raise ValueError(msg)
    if xa.size < _MIN_SAMPLES:
        msg = f"Signal too short for {context}: {xa.size} samples."
        raise ValueError(msg)
    if not np.all(np.isfinite(xa)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return apply_calibration(x, xa)


def _validate_welch_params(
    n: int, fs: float, nperseg: int | np.integer[Any] | None, overlap: float
) -> tuple[int, float]:
    require_scalar(n, "n")
    require_scalar(overlap, "overlap")
    if not 0.0 <= float(overlap) < 1.0:
        msg = "'overlap' must be in [0, 1)."
        raise ValueError(msg)
    seg = (
        _default_nperseg(n, fs)
        if nperseg is None
        else require_count(nperseg, "nperseg", at_least=None)
    )
    if seg < _MIN_SAMPLES or seg > n:
        msg = f"'nperseg' must be between {_MIN_SAMPLES} and the signal length."
        raise ValueError(msg)
    return seg, float(overlap)


def _default_nperseg(n: int, fs: float) -> int:
    """Segment length for a bin spacing of at most 4 Hz (min 32 samples)."""
    nperseg = int(min(n, 2 ** int(np.ceil(np.log2(fs / 4.0)))))
    return max(nperseg, _MIN_SAMPLES)


def _noverlap_samples(nperseg: int, overlap: float) -> int:
    """Overlap fraction -> samples, capped one short of the segment."""
    return min(round(overlap * nperseg), nperseg - 1)


def _welch_autospectrum(
    x: NDArray[np.float64],
    fs: float,
    nperseg: int,
    noverlap: int,
    window: WindowSpec = "hann",
    scaling: str = "density",
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """One-sided Welch autospectrum ``(freqs, Gxx)``, no detrending."""
    from scipy import signal as sp_signal

    freqs, gxx = sp_signal.welch(
        x,
        fs=fs,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        detrend=False,
        scaling=scaling,
    )
    return (
        np.asarray(freqs, dtype=np.float64),
        np.asarray(gxx, dtype=np.float64),
    )


def _welch_cross_spectrum(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    fs: float,
    nperseg: int,
    noverlap: int,
    window: WindowSpec = "hann",
    scaling: str = "density",
) -> tuple[NDArray[np.float64], NDArray[np.complex128]]:
    """One-sided Welch cross-spectrum ``(freqs, Gxy)``, no detrending."""
    from scipy import signal as sp_signal

    freqs, gxy = sp_signal.csd(
        x,
        y,
        fs=fs,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        detrend=False,
        scaling=scaling,
    )
    return (
        np.asarray(freqs, dtype=np.float64),
        np.asarray(gxy, dtype=np.complex128),
    )


def _welch_pair(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    fs: float,
    nperseg: int,
    noverlap: int,
    window: WindowSpec = "hann",
    scaling: str = "density",
) -> tuple[
    NDArray[np.float64],
    NDArray[np.complex128],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """One-sided ``(freqs, Gxy, Gxx, Gyy)`` from Welch-averaged segments."""
    freqs, gxy = _welch_cross_spectrum(x, y, fs, nperseg, noverlap, window, scaling)
    _, gxx = _welch_autospectrum(x, fs, nperseg, noverlap, window, scaling)
    _, gyy = _welch_autospectrum(y, fs, nperseg, noverlap, window, scaling)
    return freqs, gxy, gxx, gyy
