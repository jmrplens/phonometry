#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Impulse-response acquisition per BS EN ISO 18233:2006.

This module provides the deterministic-excitation front end for the "new
measurement methods" of ISO 18233: generate an excitation signal, play it
through the system under test, and recover the broadband impulse response
(IR) by deconvolution. Later processing (fractional-octave filtering,
Schroeder backward integration, reverberation time) consumes this IR.

Two excitation families are implemented:

* **Swept-sine (Annex B)** -- an exponential sine sweep (ESS). The frequency
  rises exponentially with time, which mimics a pink-noise source
  (ISO 18233:2006, B.3.2) and is the recommended broadband excitation. The
  IR is recovered by linear (zero-padded, non-circular) spectral
  deconvolution (B.5, Figure B.3): ``H = Y * conj(X) / (|X|^2 + reg)``. A
  Farina inverse-filter variant (``method="farina"``) convolves the
  recording with the time-reversed, amplitude-compensated sweep (B.5,
  Figure B.2). Because a low-to-high sweep places distortion products at
  negative arrival times, harmonic distortion is separated from the linear
  IR and discarded by keeping only the causal part (B.5).

* **Maximum-length sequence (Annex A)** -- an order-``N`` binary sequence of
  length ``2**N - 1`` generated with a linear-feedback shift register
  (LFSR). Its circular autocorrelation is a near-perfect delta (A.1), so the
  IR of a periodically excited linear system is recovered by circular
  cross-correlation of the recorded period with the sequence
  (equivalent to the Hadamard-transform recovery of A.1).

The recovered IR is broadband; ISO 18233 6.3.2 requires subsequent
fractional-octave-band weighting (IEC 61260) before computing levels or
decay curves -- that step belongs to downstream room-acoustics modules.
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Tuple

import numpy as np
from scipy import signal

from .utils import _typesignal

#: Warn from mls_impulse_response when the recovered IR still carries more than
#: this level (dB re its peak) in the last 10 % of the MLS period: an IR longer
#: than one period aliases circularly and this residual tail is the symptom.
_MLS_ALIAS_TAIL_DB = -35.0

#: A genuine (optionally faded) exponential sweep never ends in a run of
#: exact zeros; more trailing zeros than this small tolerance indicate the
#: reference was zero-padded (see the Farina guard in ``impulse_response``).
_FARINA_MAX_TRAILING_ZEROS = 8

# Primitive-polynomial feedback taps (1-indexed register positions, highest
# tap == order) yielding maximum-length sequences. Values from the standard
# LFSR tables (Xilinx XAPP052, "Efficient Shift Registers, LFSR Counters,
# and Long Pseudo-Random Sequence Generators", P. Alfke, 1996; equivalent to
# the primitive-polynomial tables used by Rife & Vanderkooy, JAES 37 (1989),
# ISO 18233 Bibliography [16]).
_MLS_TAPS: Dict[int, Tuple[int, ...]] = {
    2: (2, 1),
    3: (3, 2),
    4: (4, 3),
    5: (5, 3),
    6: (6, 5),
    7: (7, 6),
    8: (8, 6, 5, 4),
    9: (9, 5),
    10: (10, 7),
    11: (11, 9),
    12: (12, 6, 4, 1),
    13: (13, 4, 3, 1),
    14: (14, 5, 3, 1),
    15: (15, 14),
    16: (16, 15, 13, 4),
    17: (17, 14),
    18: (18, 11),
    19: (19, 6, 2, 1),
    20: (20, 17),
}


def sweep_signal(
    fs: int,
    f1: float,
    f2: float,
    seconds: float,
    *,
    amplitude: float = 1.0,
    fade: float = 0.01,
) -> np.ndarray:
    """
    Generate an exponential sine sweep (ESS) with exact analytic phase.

    The instantaneous frequency rises exponentially from ``f1`` to ``f2``,
    ``f(t) = f1 * (f2/f1) ** (t/T)``, so the time spent per octave is
    constant and the sweep mimics a pink-noise excitation
    (ISO 18233:2006, B.3.2). The phase is the closed-form integral of
    ``2*pi*f(t)`` (Farina, AES 108th Conv., 2000; ISO 18233 Bibliography
    [14]), avoiding numerical phase accumulation.

    :param fs: Sampling frequency in Hz.
    :param f1: Start frequency in Hz (at or below the lowest band edge to be
        measured, ISO 18233 B.3.1). Must be > 0.
    :param f2: Stop frequency in Hz (at or above the highest band edge). Must
        satisfy ``f1 < f2 <= fs/2``.
    :param seconds: Sweep duration in seconds. Any duration may be used; a
        longer sweep raises the effective signal-to-noise ratio (B.2, B.6).
    :param amplitude: Peak amplitude of the sweep. Default 1.0.
    :param fade: Half-Hann fade-in/out length as a fraction of the sweep
        duration, applied to suppress start/stop transients (B.3.3). Default
        0.01. Set to 0.0 to disable. Because the sweep frequency is
        logarithmic in time, the fades consume roughly ``fade*log2(f2/f1)``
        octaves at each band edge (the fade-out lands on the highest
        frequencies): with the default 0.01 the top ~29 dB of the highest
        band is unusable, so choose ``f1``/``f2`` with margin beyond the
        analysis range (ISO 18233 B.3.1) rather than relying on a smaller
        fade.
    :return: The sweep samples, length ``round(seconds*fs)``.
    """
    if f1 <= 0.0:
        raise ValueError("f1 must be positive")
    if f2 <= f1:
        raise ValueError("f2 must be greater than f1")
    if f2 > fs / 2.0:
        raise ValueError("f2 must not exceed the Nyquist frequency fs/2")
    if not 0.0 <= fade < 0.5:
        raise ValueError("fade must be in [0, 0.5)")

    n = int(round(seconds * fs))
    if n < 2:
        raise ValueError("seconds*fs must yield at least 2 samples")

    t = np.arange(n) / fs
    ts = n / fs
    ratio = f2 / f1
    # phi(t) = 2*pi*f1*T/ln(f2/f1) * ((f2/f1)^(t/T) - 1)
    k = 2.0 * np.pi * f1 * ts / np.log(ratio)
    phase = k * (ratio ** (t / ts) - 1.0)
    sweep: np.ndarray = amplitude * np.sin(phase)

    if fade > 0.0:
        sweep = _apply_fade(sweep, fade)
    return sweep


def _apply_fade(x: np.ndarray, fade: float) -> np.ndarray:
    """Apply symmetric half-Hann fade windows to both ends of ``x``."""
    n = x.size
    m = int(round(fade * n))
    if m < 1:
        return x
    ramp = 0.5 * (1.0 - np.cos(np.pi * (np.arange(m) + 0.5) / m))
    window = np.ones(n)
    window[:m] = ramp
    window[-m:] = ramp[::-1]
    return x * window


def inverse_filter(
    fs: int,
    f1: float,
    f2: float,
    seconds: float,
    *,
    amplitude: float = 1.0,
    fade: float = 0.01,
) -> np.ndarray:
    """
    Build the Farina inverse filter for an exponential sine sweep.

    The inverse filter is the time-reversed sweep multiplied by an amplitude
    envelope that rises by 6 dB/octave (``prop. to the instantaneous
    frequency``), which whitens the ESS's pink (-3 dB/octave) spectrum so
    that convolving the sweep with its inverse yields an impulse
    (ISO 18233:2006, B.5, Figure B.2; Farina 2000, Bibliography [14]). The
    filter is scaled to unit in-band magnitude: it is normalised by the
    median in-band magnitude of the compressed pulse ``sweep * inverse`` so
    that the deconvolution reproduces a system's true in-band level, matching
    the spectral-division convention (rather than a unit pulse peak).

    :param fs: Sampling frequency in Hz.
    :param f1: Sweep start frequency in Hz (same value used for the sweep).
    :param f2: Sweep stop frequency in Hz.
    :param seconds: Sweep duration in seconds.
    :param amplitude: Peak amplitude used for the source sweep. Default 1.0.
    :param fade: Fade fraction used for the source sweep. Default 0.01.
    :return: The inverse-filter samples (same length as the sweep).
    """
    sweep = sweep_signal(fs, f1, f2, seconds, amplitude=amplitude, fade=fade)
    n = sweep.size
    ts = n / fs
    t = np.arange(n) / fs
    ratio = f2 / f1
    # Reversed-sweep instantaneous frequency, normalised to f2:
    # f_rev(t) = f2 * (f1/f2) ** (t/T) = f2 * ratio ** (-t/T). Multiplying the
    # reversed sweep by f_rev(t)/f2 = ratio ** (-t/T) weights the spectrum by
    # a factor proportional to frequency (+6 dB/octave), which flattens the
    # ESS's pink (-3 dB/octave) magnitude so the compressed output is an
    # impulse (Farina 2000).
    env = ratio ** (-t / ts)  # decreases from 1 (at f2) to f1/f2 (at f1)
    inv = sweep[::-1] * env
    # Normalise so that the compressed pulse (sweep * inverse) has unit
    # magnitude across the sweep band. Scaling by the in-band gain (rather
    # than the pulse peak) makes the deconvolution reproduce a system's true
    # in-band level, matching the spectral-division convention.
    comp = signal.fftconvolve(sweep, inv)
    freqs = np.fft.rfftfreq(comp.size, d=1.0 / fs)
    band = (freqs >= f1) & (freqs <= f2)
    if not np.any(band):
        raise ValueError(
            "no frequency bin falls within the sweep band [f1, f2]; the "
            "sweep is too short for this frequency resolution — increase "
            "'seconds' or widen the (f1, f2) range."
        )
    gain = float(np.median(np.abs(np.fft.rfft(comp)[band])))
    if gain > 0.0:
        inv = inv / gain
    return inv


def _farina_deconvolve(
    rec: np.ndarray,
    ref: np.ndarray,
    fs: int,
    f_range: Tuple[float, float] | None,
) -> np.ndarray:
    """Farina inverse-filter deconvolution (ISO 18233:2006, Figure B.2).

    Rebuilds the analytic inverse filter from ``ref`` and convolves it with the
    recording, returning the full sequence with the causal IR rolled to index
    0 (matching the spectral-method layout). Raises ``ValueError`` if
    ``f_range`` is missing or if ``ref`` is zero-padded (the correct input for
    the spectral method, which would silently produce a wrong inverse filter).
    """
    if f_range is None:
        raise ValueError("method='farina' requires f_range=(f1, f2)")
    # A reference that was zero-padded to the recording length - the correct
    # input for method="spectral" - makes the rebuilt sweep longer than the
    # real excitation, silently producing a wrong inverse filter (the IR peak
    # is mislocated and orders of magnitude too small). Detect trailing
    # zero-padding and reject it: a genuine (optionally faded) sweep has no
    # trailing run of exact zeros.
    nonzero = np.flatnonzero(ref)
    last_nonzero = int(nonzero[-1]) if nonzero.size else -1
    n_trailing = ref.size - 1 - last_nonzero
    if n_trailing > _FARINA_MAX_TRAILING_ZEROS:
        raise ValueError(
            f"method='farina' requires the unpadded excitation sweep as "
            f"'reference', but it ends in {n_trailing} zero samples "
            "(zero-padding to the recording length is only correct for "
            "method='spectral'). Pass the exact-length sweep from "
            "sweep_signal(), or use method='spectral'."
        )
    inv = inverse_filter(fs, f_range[0], f_range[1], ref.size / fs)
    conv = signal.fftconvolve(rec, inv)
    # The linear IR peaks where the inverse aligns with the sweep, at index
    # len(reference)-1. Roll it to index 0 so the layout matches the spectral
    # method (causal at 0, negative times in the tail).
    return np.roll(conv, -(ref.size - 1))


def impulse_response(
    recorded: List[float] | np.ndarray,
    reference: List[float] | np.ndarray,
    fs: int,
    *,
    method: str = "spectral",
    f_range: Tuple[float, float] | None = None,
    regularization: float = 1e-6,
    length: int | None = None,
    return_full: bool = False,
) -> np.ndarray:
    """
    Recover the broadband impulse response by sweep deconvolution.

    Implements the linear (non-circular) deconvolution of ISO 18233:2006,
    B.5. Both signals are zero-padded to ``len(recorded)+len(reference)-1``
    to avoid circular convolution (B.5). The causal IR occupies the start of
    the result; distortion products from a low-to-high sweep fall at negative
    arrival times (the wrapped tail) and are discarded by returning only the
    causal part (B.5).

    :param recorded: Recorded system response to the sweep.
    :param reference: The emitted sweep (excitation signal).
    :param fs: Sampling frequency in Hz (kept for API symmetry; the
        deconvolution itself is sample-rate agnostic).
    :param method: ``"spectral"`` for spectral division
        ``H = Y*conj(X)/(|X|^2+reg)`` (Figure B.3, default) or ``"farina"``
        for convolution with the analytic inverse filter (Figure B.2). The
        Farina method requires ``f_range`` and the **exact-length, unpadded**
        excitation sweep as ``reference`` (it rebuilds the inverse filter from
        ``reference.size/fs`` as the sweep duration); a reference zero-padded
        to the recording length - the correct input for the spectral method -
        is rejected with a ``ValueError`` because it would silently produce a
        wrong inverse filter. It also assumes the reference sweep was
        generated with the default ``amplitude``/``fade`` of
        :func:`sweep_signal`; a non-unit amplitude or custom fade yields a
        scaled IR, so use the spectral method in that case.
    :param f_range: ``(f1, f2)`` of the sweep, required for ``method="farina"``
        to rebuild the inverse filter; ignored for the spectral method.
    :param regularization: Tikhonov term added to the denominator, expressed
        as a fraction of the peak spectral energy ``max(|X|^2)`` (spectral
        method only). Guards against amplifying noise where the sweep has
        little energy, e.g. outside its frequency range (B.5). Default 1e-6.
    :param length: Number of samples of the causal IR to return. Defaults to
        ``len(recorded)``. Ignored when ``return_full`` is True.
    :param return_full: If True, return the full deconvolution sequence
        (causal IR at index 0, negative-time distortion products in the
        tail) instead of the trimmed causal IR. Default False.
    :return: The recovered impulse response.
    """
    rec = _typesignal(recorded)
    ref = _typesignal(reference)
    if rec.ndim != 1 or ref.ndim != 1:
        raise ValueError("'recorded' and 'reference' must be one-dimensional.")
    if rec.size == 0 or ref.size == 0:
        raise ValueError("'recorded' and 'reference' must be non-empty.")
    out_len = length if length is not None else rec.size
    n = rec.size + ref.size - 1

    if method == "spectral":
        spec_x = np.fft.rfft(ref, n=n)
        spec_y = np.fft.rfft(rec, n=n)
        power = np.abs(spec_x) ** 2
        reg = regularization * float(power.max()) if power.size else 0.0
        h_spec = spec_y * np.conj(spec_x) / (power + reg)
        full = np.fft.irfft(h_spec, n=n)
    elif method == "farina":
        full = _farina_deconvolve(rec, ref, fs, f_range)
    else:
        raise ValueError(f"unknown method {method!r}")

    if return_full:
        return full
    return full[:out_len]


def mls_signal(order: int) -> np.ndarray:
    """
    Generate a maximum-length sequence (MLS) of the given order.

    A Fibonacci LFSR with primitive-polynomial feedback taps produces a
    binary sequence of length ``2**order - 1`` whose circular
    autocorrelation is a near-perfect periodic delta
    (ISO 18233:2006, A.1). The binary values are mapped to ``+1``/``-1``.

    :param order: Register length ``N`` (2 to 20). The sequence length is
        ``2**order - 1``.
    :return: The bipolar MLS samples (values in ``{-1.0, +1.0}``).
    """
    if order not in _MLS_TAPS:
        raise ValueError(
            f"order must be one of {sorted(_MLS_TAPS)} (got {order})"
        )
    taps = _MLS_TAPS[order]
    length = (1 << order) - 1
    # LFSR state as a boolean register, seeded with all ones (any non-zero
    # seed produces the same sequence up to a cyclic shift).
    state = np.ones(order, dtype=np.int8)
    out = np.empty(length, dtype=np.float64)
    tap_idx = [t - 1 for t in taps]
    for i in range(length):
        bit = state[-1]
        out[i] = 1.0 - 2.0 * bit  # 0 -> +1, 1 -> -1
        feedback = 0
        for t in tap_idx:
            feedback ^= state[t]
        state[1:] = state[:-1]
        state[0] = feedback
    return out


def mls_impulse_response(
    recorded: List[float] | np.ndarray,
    mls: List[float] | np.ndarray,
    *,
    length: int | None = None,
) -> np.ndarray:
    """
    Recover an impulse response from a periodic MLS excitation.

    The recording must span an integer number of MLS periods; the periods
    are averaged (raising the effective signal-to-noise ratio by 3 dB per
    doubling, ISO 18233:2006, 6.3.6) and the IR is obtained by circular
    cross-correlation of the averaged period with the sequence, normalised by
    ``2**N`` (A.1). Because the sequence is periodic, the recovery is a
    circular deconvolution: a system IR longer than one period aliases back
    into the record (A.1).

    :param recorded: Recorded response, length a multiple of ``2**N - 1``.
    :param mls: The excitation sequence returned by :func:`mls_signal`.
    :param length: Number of IR samples to return. Defaults to the sequence
        length ``2**N - 1``.
    :return: The recovered impulse response.

    .. note::
        A ``UserWarning`` is emitted when the recovered IR retains significant
        energy at the end of the period (a circular-aliasing symptom). The
        tail-RMS heuristic is advisory: a high ambient noise floor in the
        recording raises the tail RMS on its own and can trigger a
        false positive even when the IR fits within one period, so treat the
        warning as a prompt to check the noise floor and MLS order rather than
        a definitive aliasing diagnosis.
    """
    rec = _typesignal(recorded)
    seq = _typesignal(mls)
    if rec.ndim != 1 or seq.ndim != 1:
        raise ValueError("'recorded' and 'mls' must be one-dimensional.")
    if rec.size == 0 or seq.size == 0:
        raise ValueError("'recorded' and 'mls' must be non-empty.")
    period = seq.size
    if rec.size == 0 or rec.size % period != 0:
        raise ValueError(
            "recorded length must be a positive multiple of the MLS length"
        )
    # Average the recorded periods (synchronous averaging, ISO 18233 6.3.6).
    averaged = rec.reshape(-1, period).mean(axis=0)
    # Circular cross-correlation: DFT{corr} = conj(SEQ) * REC.
    spec = np.conj(np.fft.rfft(seq)) * np.fft.rfft(averaged)
    corr = np.fft.irfft(spec, n=period)
    ir = corr / (period + 1.0)  # normalise by 2**N so the delta peaks at 1

    # Circular-aliasing guard: if the system IR is longer than one MLS period
    # it folds back into the record (A.1). The symptom is undecayed energy in
    # the last part of the period; warn (do not raise) so short-order misuse is
    # visible instead of silently biasing the result.
    peak = float(np.max(np.abs(ir)))
    if peak > 0.0:
        tail = ir[int(0.9 * period):]
        tail_rms = float(np.sqrt(np.mean(tail ** 2)))
        if tail_rms > peak * 10.0 ** (_MLS_ALIAS_TAIL_DB / 20.0):
            warnings.warn(
                "Recovered MLS impulse response still has energy near the end "
                f"of the {period}-sample period ({20 * np.log10(tail_rms / peak):.0f} "
                f"dB re peak, above {_MLS_ALIAS_TAIL_DB:.0f} dB): the impulse "
                "response is likely longer than one period and aliases "
                "circularly. Use a higher MLS order.",
                UserWarning,
                stacklevel=2,
            )

    out_len = length if length is not None else period
    if out_len <= period:
        return ir[:out_len]
    # Periodic extension for requests longer than one period.
    reps = (out_len + period - 1) // period
    return np.tile(ir, reps)[:out_len]
