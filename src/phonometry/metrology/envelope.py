#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Envelope and instantaneous phase via the Hilbert transform.

Signal-envelope analysis following Bendat & Piersol, *Random Data:
Analysis and Measurement Procedures* (4th ed., 2010), Chapter 13. The
analytic signal ``z(t) = x(t) + j·x̃(t)`` (Eq. 13.15, with ``x̃`` the
Hilbert transform of ``x``) yields

* the **envelope** ``A(t) = [x²(t) + x̃²(t)]^½`` (Eq. 13.17),
* the **instantaneous phase** ``θ(t) = arctan[x̃(t)/x(t)]``, unwrapped
  (Eq. 13.18), and
* the **instantaneous frequency** ``f(t) = (1/2π)·dθ/dt`` (Eq. 13.19).

The analytic signal is computed the way the book recommends
(Section 13.1.1): the one-sided spectrum construction
``Z(f) = 2·X(f)`` for ``f > 0``, ``X(0)`` at DC and ``0`` for ``f < 0``
(Eq. 13.25) - which is exactly what :func:`scipy.signal.hilbert`
implements, and the same construction the ECMA-418-2 psychoacoustic chain
of :mod:`phonometry.psychoacoustics` applies per auditory band (its
Formulae 65/119 take ``|hilbert|`` and subsample by 32; the standard can
subsample directly because each band is narrow). Closed-form pairs from
Table 13.1 (``cos → sin``, an AM envelope recovered exactly) anchor the
tests.

The envelope of a band-limited signal is itself low-frequency, so the
result offers optional **decimation**: an anti-aliased zero-phase FIR
decimator for general records, or plain subsampling (``antialias=False``)
matching the ECMA-internal convention when the input is already
narrowband.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .spectra import _positive, _validate_signal

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

__all__ = [
    "EnvelopeResult",
    "envelope",
]


@dataclass(frozen=True)
class EnvelopeResult:
    """Envelope and instantaneous phase of a signal (B&P Chapter 13).

    All output arrays share the (possibly decimated) time axis
    :attr:`times`; the original record is kept at full rate for plotting.

    :ivar times: Time axis of the outputs, in seconds.
    :ivar envelope: Envelope ``A(t) = |z(t)|`` (Eq. 13.17).
    :ivar phase: Unwrapped instantaneous phase ``θ(t)``, in radians
        (Eq. 13.18).
    :ivar instantaneous_frequency: ``f(t) = (1/2π)·dθ/dt``, in Hz
        (Eq. 13.19), differentiated at full rate before any decimation.
    :ivar fs: Sample rate of the outputs, in Hz (``signal_fs`` divided by
        :attr:`decimation_factor`).
    :ivar signal: The analysed record, at full rate.
    :ivar signal_fs: Sample rate of :attr:`signal`, in Hz.
    :ivar decimation_factor: Integer decimation applied to the outputs
        (1: none).
    :ivar antialias: Whether the decimation was anti-alias filtered.
    """

    times: "NDArray[np.float64]"
    envelope: "NDArray[np.float64]"
    phase: "NDArray[np.float64]"
    instantaneous_frequency: "NDArray[np.float64]"
    fs: float
    signal: "NDArray[np.float64]"
    signal_fs: float
    decimation_factor: int
    antialias: bool

    def plot(
        self, ax: "Axes | None" = None, **kwargs: Any
    ) -> "Axes | NDArray[Any]":
        """Plot the signal with its envelope and the instantaneous frequency."""
        from .._plot.metrology import plot_envelope

        return plot_envelope(self, ax=ax, **kwargs)


def _decimate_envelope(
    env: "NDArray[np.float64]", factor: int, antialias: bool
) -> "NDArray[np.float64]":
    """Decimate the envelope, anti-aliased (zero-phase FIR) or plain."""
    if not antialias:
        return env[::factor].copy()
    from scipy import signal as sp_signal

    return np.asarray(
        sp_signal.decimate(env, factor, ftype="fir", zero_phase=True),
        dtype=np.float64,
    )


def envelope(
    x: "NDArray[np.float64] | list[float]",
    fs: float,
    *,
    decimation_factor: int = 1,
    antialias: bool = True,
) -> EnvelopeResult:
    """Envelope, instantaneous phase and frequency via Hilbert transform.

    Builds the analytic signal by the one-sided spectrum construction of
    Bendat & Piersol Eq. 13.25 (``scipy.signal.hilbert``) and returns the
    envelope ``|z(t)|``, the unwrapped instantaneous phase and the
    instantaneous frequency (Eqs. 13.17-13.19). For an amplitude-modulated
    carrier ``u(t)·cos(2πf0t)`` with ``u`` low-frequency and non-negative
    the envelope recovers ``u(t)`` exactly in the ideal continuous case
    (Eq. 13.27); a discrete record shows small edge effects at the record
    boundaries.

    The optional decimation reduces the output rate by an integer factor:
    the envelope is anti-alias filtered with a zero-phase FIR decimator
    by default, or plainly subsampled with ``antialias=False`` - the
    convention the ECMA-418-2 loudness/roughness chain applies internally
    after its auditory bandpass, appropriate when the input is already
    narrowband. The phase and instantaneous frequency, smooth after
    unwrapping and differentiated at full rate, are subsampled onto the
    same time axis.

    :param x: Signal, 1-D.
    :param fs: Sample rate, in Hz.
    :param decimation_factor: Integer output decimation (default 1: off).
    :param antialias: Anti-alias filter the decimated envelope (default
        ``True``).
    :return: An :class:`EnvelopeResult`.
    :raises ValueError: If the inputs or parameters are invalid.
    """
    from scipy import signal as sp_signal

    xa = _validate_signal(x, "x", context="envelope analysis")
    fs_v = _positive(fs, "fs")
    factor = int(decimation_factor)
    if factor < 1:
        raise ValueError("'decimation_factor' must be a positive integer.")
    if factor >= xa.size:
        raise ValueError(
            "'decimation_factor' must be smaller than the record length."
        )

    analytic = sp_signal.hilbert(xa)
    env = np.asarray(np.abs(analytic), dtype=np.float64)
    phase = np.asarray(np.unwrap(np.angle(analytic)), dtype=np.float64)
    inst_freq = np.asarray(
        np.gradient(phase) * fs_v / (2.0 * np.pi), dtype=np.float64
    )

    if factor > 1:
        env = _decimate_envelope(env, factor, antialias)
        phase = phase[::factor].copy()
        inst_freq = inst_freq[::factor].copy()

    out_fs = fs_v / factor
    times = np.arange(env.size, dtype=np.float64) / out_fs
    return EnvelopeResult(
        times=times,
        envelope=env,
        phase=phase,
        instantaneous_frequency=inst_freq,
        fs=out_fs,
        signal=xa.copy(),
        signal_fs=fs_v,
        decimation_factor=factor,
        antialias=bool(antialias),
    )
