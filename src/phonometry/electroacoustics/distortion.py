#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Distortion metrics for electroacoustic equipment (IEC 60268-3 / AES17).

Harmonic and intermodulation distortion of amplifiers and audio equipment, from
a captured signal:

* **Total harmonic distortion** ``THD`` (IEC 60268-3 14.12.2-3), relative to the
  fundamental (``kind='F'``) or to the total RMS (``kind='R'``), and the
  **nth-order harmonic distortion** (14.12.5).
* **THD+N** and **SINAD** (AES17-2015 6.3): the fundamental is removed with a
  standard notch filter and the residual is compared with the total signal.
* **Modulation distortion** (SMPTE-type, IEC 60268-3 14.12.7) and
  **difference-frequency distortion** (CCIF-type, 14.12.8), plus the
  **total difference-frequency distortion** (14.12.10).
* **Dynamic intermodulation distortion** ``DIM`` (14.12.9) from the 15 kHz sine /
  3.15 kHz square-wave test signal.
* **Weighted THD** (14.12.11), the A-weighted harmonic residual.

All metrics have an exact analytic oracle: a signal synthesised with known
harmonic or intermodulation amplitudes reproduces the closed-form ratio. The
functions assume the tones fall on (or very near) FFT bins -- use coherent
sampling (an integer number of periods) or supply a low-leakage window, as audio
analysers do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: Default number of harmonics summed for the THD (IEC 60268-3).
_DEFAULT_N_HARMONICS = 10
#: Default standard-notch quality factor for THD+N (AES17 5.2.8: 1.2 <= Q <= 3).
_DEFAULT_NOTCH_Q = 2.0
#: Notch settling allowance, in fundamental cycles per unit Q, discarded from
#: each end of the notched residual so the ``filtfilt`` start/stop transient does
#: not leak fundamental energy into the THD+N residual.
_NOTCH_SETTLE_CYCLES = 8.0
#: Harmonic peak-search half-width, as a fraction of the fundamental. Wide
#: enough to catch a harmonic under window leakage or a slightly mistuned
#: fundamental, but well inside ±f0 so a nearby non-harmonic tone is not latched
#: onto a harmonic bin.
_HARMONIC_SEARCH_FACTOR = 0.1


def _positive(value: float, name: str) -> float:
    scalar = float(value)
    if not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"'{name}' must be a positive, finite number.")
    return scalar


def _validate_signal(signal: "NDArray[np.float64] | list[float]") -> "NDArray[np.float64]":
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError("'signal' must be one-dimensional.")
    if sig.size < 4:
        raise ValueError("'signal' must contain at least four samples.")
    if not np.all(np.isfinite(sig)):
        raise ValueError("'signal' must be finite.")
    return sig


def _amplitude_spectrum(
    signal: "NDArray[np.float64]", fs: float, window: str
) -> tuple["NDArray[np.float64]", "NDArray[np.float64]"]:
    """Coherent-gain-normalised amplitude spectrum (a tone on a bin reads its peak)."""
    from scipy import signal as sp_signal

    n = signal.size
    w = sp_signal.get_window(window, n, fftbins=True)
    spectrum = np.fft.rfft(signal * w)
    amp = np.abs(spectrum) * 2.0 / np.sum(w)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    return freqs, amp


def _tone_amplitude(
    freqs: "NDArray[np.float64]",
    amp: "NDArray[np.float64]",
    frequency: float,
    search_hz: float,
) -> float:
    """Peak amplitude within ``±search_hz`` of ``frequency`` (0 if out of range)."""
    lo, hi = frequency - search_hz, frequency + search_hz
    mask = (freqs >= lo) & (freqs <= hi)
    if not np.any(mask):
        return 0.0
    return float(np.max(amp[mask]))


def _fundamental_frequency(
    freqs: "NDArray[np.float64]", amp: "NDArray[np.float64]"
) -> float:
    """Frequency of the largest non-DC spectral peak."""
    idx = int(np.argmax(amp[1:])) + 1
    return float(freqs[idx])


def _harmonic_amplitudes(
    signal: "NDArray[np.float64]",
    fs: float,
    fundamental: float | None,
    n_harmonics: int,
    window: str,
) -> tuple[float, "NDArray[np.float64]"]:
    """Return ``(f0, amplitudes)`` with ``amplitudes[k]`` the (k+1)-th harmonic."""
    freqs, amp = _amplitude_spectrum(signal, fs, window)
    f0 = _fundamental_frequency(freqs, amp) if fundamental is None else float(fundamental)
    if f0 <= 0.0:
        raise ValueError("Could not determine a positive fundamental frequency.")
    search = f0 * _HARMONIC_SEARCH_FACTOR
    nyquist = fs / 2.0
    amps = []
    for k in range(1, n_harmonics + 1):
        fk = k * f0
        if fk >= nyquist:
            break
        amps.append(_tone_amplitude(freqs, amp, fk, search))
    return f0, np.asarray(amps, dtype=np.float64)


# --------------------------------------------------------------------------- #
# Harmonic distortion (IEC 60268-3 14.12.2-3 / 14.12.5, AES17 6.3)
# --------------------------------------------------------------------------- #
def thd(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float | None = None,
    *,
    kind: Literal["F", "R"] = "F",
    n_harmonics: int = _DEFAULT_N_HARMONICS,
    window: str = "hann",
) -> float:
    """Total harmonic distortion (IEC 60268-3 14.12.2-3).

    ``THD_F = √(Σ_{n≥2} aₙ²) / a₁`` (relative to the fundamental, ``kind='F'``)
    or ``THD_R = √(Σ_{n≥2} aₙ²) / √(Σ_{n≥1} aₙ²)`` (relative to the total RMS,
    ``kind='R'``), from the harmonic amplitudes ``aₙ``.

    :param signal: Captured signal (1-D). Coherent sampling (integer periods) or
        a low-leakage window gives the exact value.
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency ``f₁`` in Hz, or ``None`` to take
        the largest spectral peak.
    :param kind: ``'F'`` (relative to the fundamental, the default) or ``'R'``
        (relative to the total RMS).
    :param n_harmonics: Highest harmonic order summed (default 10).
    :param window: FFT window (default ``'hann'``).
    :return: Total harmonic distortion, as a ratio (0..).
    :raises ValueError: If the signal/parameters are invalid or ``kind`` unknown.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    if kind not in ("F", "R"):
        raise ValueError("'kind' must be 'F' or 'R'.")
    f0, amps = _harmonic_amplitudes(sig, fs_v, fundamental, n_harmonics, window)
    if amps.size == 0 or amps[0] <= 0.0:
        raise ValueError("No fundamental component found in the signal.")
    harmonic_rms = float(np.sqrt(np.sum(amps[1:] ** 2)))
    if kind == "F":
        return float(harmonic_rms / amps[0])
    total_rms = float(np.sqrt(np.sum(amps**2)))
    return float(harmonic_rms / total_rms)


def harmonic_distortion(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float,
    order: int,
    *,
    n_harmonics: int = _DEFAULT_N_HARMONICS,
    window: str = "hann",
) -> float:
    """nth-order harmonic distortion ``dₙ`` (IEC 60268-3 14.12.5).

    ``dₙ = aₙ / √(Σ_{k≥1} a_k²)`` -- the nth harmonic amplitude relative to the
    total RMS.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency ``f₁``, in Hz.
    :param order: Harmonic order ``n`` (>= 2).
    :param n_harmonics: Highest harmonic order used for the total RMS.
    :param window: FFT window (default ``'hann'``).
    :return: nth-order harmonic distortion, as a ratio.
    :raises ValueError: If ``order`` < 2 or the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    f0 = _positive(fundamental, "fundamental")
    if order < 2:
        raise ValueError("'order' must be at least 2.")
    n = max(n_harmonics, order)
    _, amps = _harmonic_amplitudes(sig, fs_v, f0, n, window)
    if amps.size < order or amps[0] <= 0.0:
        raise ValueError("The requested harmonic order exceeds the Nyquist limit.")
    total_rms = float(np.sqrt(np.sum(amps**2)))
    return float(amps[order - 1] / total_rms)


def _notched_residual(
    signal: "NDArray[np.float64]", fs: float, f0: float, notch_q: float
) -> "NDArray[np.float64]":
    """Signal with the fundamental removed by the AES17 standard notch filter."""
    from scipy import signal as sp_signal

    if f0 >= fs / 2.0:
        raise ValueError(
            "'fundamental' must be below the Nyquist frequency (fs / 2)."
        )
    b, a = sp_signal.iirnotch(f0, notch_q, fs)
    return np.asarray(sp_signal.filtfilt(b, a, signal), dtype=np.float64)


def _steady_slice(n: int, fs: float, f0: float, notch_q: float) -> slice:
    """Interior slice discarding the notch ``filtfilt`` start/stop transient.

    The zero-phase notch needs several fundamental cycles to settle; without
    trimming, its start/stop transient leaks fundamental energy into the
    residual (a spurious THD+N floor). The trim is capped at a quarter of the
    signal from each end so at least the middle half always survives.
    """
    settle = int(round(_NOTCH_SETTLE_CYCLES * notch_q * fs / f0))
    settle = min(settle, n // 4)
    return slice(settle, n - settle) if settle > 0 else slice(None)


def thd_plus_noise(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float | None = None,
    *,
    notch_q: float = _DEFAULT_NOTCH_Q,
    window: str = "hann",
    as_db: bool = False,
) -> float:
    """THD+N ratio (AES17-2015 6.3.1).

    The fundamental is removed with the standard notch filter (``1.2 ≤ Q ≤ 3``)
    and the residual RMS is compared with the total RMS:
    ``THD+N = V_residual / V_total`` (a ratio, or ``20·lg`` of it in dB).

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency, or ``None`` to auto-detect.
    :param notch_q: Notch quality factor (AES17: 1.2..3; default 2.0).
    :param window: FFT window used only for fundamental auto-detection.
    :param as_db: Return ``20·lg(ratio)`` in dB instead of the ratio.
    :return: THD+N as a ratio (default) or in dB.
    :raises ValueError: If the inputs are invalid or ``notch_q`` out of range.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    if not 1.2 <= float(notch_q) <= 3.0:
        raise ValueError("'notch_q' must be within the AES17 range [1.2, 3].")
    if fundamental is None:
        freqs, amp = _amplitude_spectrum(sig, fs_v, window)
        f0 = _fundamental_frequency(freqs, amp)
    else:
        f0 = _positive(fundamental, "fundamental")
    residual = _notched_residual(sig, fs_v, f0, float(notch_q))
    sl = _steady_slice(sig.size, fs_v, f0, float(notch_q))
    total_rms = float(np.sqrt(np.mean(sig[sl] ** 2)))
    if total_rms <= 0.0:
        raise ValueError("Signal has no energy.")
    residual_rms = float(np.sqrt(np.mean(residual[sl] ** 2)))
    ratio = residual_rms / total_rms
    if as_db:
        return float(20.0 * np.log10(ratio)) if ratio > 0.0 else -np.inf
    return ratio


def sinad(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float | None = None,
    *,
    notch_q: float = _DEFAULT_NOTCH_Q,
    window: str = "hann",
) -> float:
    """Signal-to-noise-and-distortion ratio SINAD, in dB (AES17-2015).

    ``SINAD = −(THD+N in dB) = 20·lg(V_total / V_residual)`` -- the reciprocal,
    in dB, of the THD+N ratio.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency, or ``None`` to auto-detect.
    :param notch_q: Notch quality factor (AES17: 1.2..3; default 2.0).
    :param window: FFT window used only for fundamental auto-detection.
    :return: SINAD, in dB.
    :raises ValueError: If the inputs are invalid.
    """
    thdn_db = thd_plus_noise(
        signal, fs, fundamental, notch_q=notch_q, window=window, as_db=True
    )
    return float(-thdn_db)


def weighted_thd(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float | None = None,
    *,
    notch_q: float = _DEFAULT_NOTCH_Q,
    weighting: Literal["A", "C"] = "A",
    window: str = "hann",
) -> float:
    """Weighted total harmonic distortion (IEC 60268-3 14.12.11).

    The fundamental is notched out and the residual is frequency-weighted (A by
    default) before its RMS is compared with the total signal RMS, so the
    perceptual emphasis of the distortion products is accounted for.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency, or ``None`` to auto-detect.
    :param notch_q: Notch quality factor (default 2.0).
    :param weighting: Frequency weighting applied to the residual (``'A'`` or
        ``'C'``).
    :param window: FFT window used only for fundamental auto-detection.
    :return: Weighted THD, as a ratio.
    :raises ValueError: If the inputs are invalid.
    """
    from ..metrology.parametric_filters import weighting_filter

    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    if weighting not in ("A", "C"):
        raise ValueError("'weighting' must be 'A' or 'C'.")
    if not 1.2 <= float(notch_q) <= 3.0:
        raise ValueError("'notch_q' must be within the AES17 range [1.2, 3].")
    if fundamental is None:
        freqs, amp = _amplitude_spectrum(sig, fs_v, window)
        f0 = _fundamental_frequency(freqs, amp)
    else:
        f0 = _positive(fundamental, "fundamental")
    residual = _notched_residual(sig, fs_v, f0, float(notch_q))
    weighted = weighting_filter(residual, int(fs_v), curve=weighting)
    sl = _steady_slice(sig.size, fs_v, f0, float(notch_q))
    total_rms = float(np.sqrt(np.mean(sig[sl] ** 2)))
    if total_rms <= 0.0:
        raise ValueError("Signal has no energy.")
    return float(np.sqrt(np.mean(weighted[sl] ** 2)) / total_rms)


# --------------------------------------------------------------------------- #
# Intermodulation distortion (IEC 60268-3 14.12.7-10)
# --------------------------------------------------------------------------- #

#: Intermodulation product search half-width, in FFT bins. Wide enough to catch
#: a product under mild window leakage, narrow enough (together with the
#: spacing-based cap below) that neighbouring products, the primary tones and
#: DC are never swallowed into a product's window.
_IMD_SEARCH_BINS = 5.0


def _imd_component(
    freqs: "NDArray[np.float64]",
    amp: "NDArray[np.float64]",
    frequency: float,
    half_width: float,
    exclude: tuple[float, ...] = (),
) -> float:
    """Peak amplitude within ``±half_width`` of an intermodulation product.

    Returns 0 for products outside (0, Nyquist). The window is shrunk so it
    never contains the DC bin or an excluded component (a primary tone): a
    product that cannot be separated from a primary reads 0 rather than the
    primary's amplitude (e.g. octave-spaced clean tones must not report
    ``d2 = 1``).
    """
    df = float(freqs[1] - freqs[0]) if freqs.size > 1 else 0.0
    nyquist = float(freqs[-1])
    if frequency <= 0.0 or frequency >= nyquist:
        return 0.0
    half = min(half_width, frequency - df)  # keep the DC bin out
    for fx in exclude:
        half = min(half, abs(frequency - fx) - df)
    if half < 0.0:
        return 0.0
    return _tone_amplitude(freqs, amp, frequency, half)


@dataclass(frozen=True)
class ModulationDistortionResult:
    """Modulation (intermodulation) distortion (IEC 60268-3 14.12.7).

    :ivar d2: Second-order modulation distortion ``d_m,2`` (14.12.7.2 g):
        the *arithmetic* sum of the sideband amplitudes at ``f2 ± f1``
        relative to the output amplitude at ``f2``.
    :ivar d3: Third-order modulation distortion ``d_m,3`` (14.12.7.2 h):
        the arithmetic sum of the sidebands at ``f2 ± 2·f1`` relative to
        the output amplitude at ``f2``.
    :ivar smpte: Combined-RMS convention of SMPTE-type analyzers (not an
        IEC 60268-3 quantity): ``√(Σ aₛ²) / a_f2`` over all four sidebands.
    """

    d2: float
    d3: float
    smpte: float


def modulation_distortion(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    f_low: float,
    f_high: float,
    *,
    window: str = "hann",
) -> ModulationDistortionResult:
    """Modulation distortion of the nth order (IEC 60268-3 14.12.7).

    A low-frequency tone ``f1 = f_low`` (large) and a high-frequency tone
    ``f2 = f_high`` (small, amplitude ratio preferably 4:1) are applied; the
    nth-order distortion shows up as modulation sidebands at
    ``f2 ± (n−1)·f1``. Per 14.12.7.2 g)-h) the per-order values use the
    *arithmetic* sum of the two sideband amplitudes, referenced to the output
    voltage at ``f2``:

    ``d_m,2 = (a_{f2+f1} + a_{f2−f1}) / a_{f2}`` and
    ``d_m,3 = (a_{f2+2f1} + a_{f2−2f1}) / a_{f2}``.

    (The alternative presentation ``d'_m,n = 5·d_m,n`` references the 4:1
    reference output voltage ``U_2,ref = 5·U_2,f2`` instead.) The combined
    root-sum-square that SMPTE-type analyzers report is returned alongside
    as ``smpte``.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param f_low: Low modulating tone ``f1``, in Hz (e.g. 60 Hz).
    :param f_high: High carrier tone ``f2``, in Hz (e.g. 7 kHz).
    :param window: FFT window (default ``'hann'``).
    :return: A :class:`ModulationDistortionResult` with ``d2``, ``d3`` and
        the ``smpte`` combined RMS.
    :raises ValueError: If the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    fl = _positive(f_low, "f_low")
    fh = _positive(f_high, "f_high")
    freqs, amp = _amplitude_spectrum(sig, fs_v, window)
    df = float(freqs[1] - freqs[0]) if freqs.size > 1 else 0.0
    # Sidebands are spaced f1 apart: cap the search window well inside that.
    half = min(_IMD_SEARCH_BINS * df, fl / 4.0)
    carrier = _tone_amplitude(freqs, amp, fh, half)
    if carrier <= 0.0:
        raise ValueError("No carrier component found at 'f_high'.")
    sidebands = {
        n: tuple(
            _imd_component(freqs, amp, fh + sign * (n - 1) * fl, half, exclude=(fl, fh))
            for sign in (1.0, -1.0)
        )
        for n in (2, 3)
    }
    d2 = (sidebands[2][0] + sidebands[2][1]) / carrier
    d3 = (sidebands[3][0] + sidebands[3][1]) / carrier
    smpte = float(
        np.sqrt(sum(a**2 for pair in sidebands.values() for a in pair)) / carrier
    )
    return ModulationDistortionResult(d2=float(d2), d3=float(d3), smpte=smpte)


def difference_frequency_distortion(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    f1: float,
    f2: float,
    *,
    order: int = 2,
    window: str = "hann",
) -> float:
    """Difference-frequency distortion of the nth order (IEC 60268-3 14.12.8).

    Two equal-amplitude tones ``f1 < f2`` are applied. Per 14.12.8.1 the
    reference voltage is ``U_2,ref = 2·U_2,f2`` -- realised here as the sum of
    both measured tone amplitudes, identical for the standard equal-amplitude
    tones -- and

    ``d_d,2 = a_{f2−f1} / (a_{f1} + a_{f2})``,
    ``d_d,3 = (a_{2f2−f1} + a_{2f1−f2}) / (a_{f1} + a_{f2})``

    with the third order an *arithmetic* sum of the two products. Products
    that fall outside (0, Nyquist) or that cannot be separated from a primary
    tone or DC read zero.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param f1: Lower tone, in Hz.
    :param f2: Upper tone, in Hz.
    :param order: Product order (2 or 3).
    :param window: FFT window (default ``'hann'``).
    :return: nth-order difference-frequency distortion, as a ratio.
    :raises ValueError: If ``order`` is not 2 or 3 or the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    fa = _positive(f1, "f1")
    fb = _positive(f2, "f2")
    if fa >= fb:
        raise ValueError("'f1' must be lower than 'f2'.")
    if order not in (2, 3):
        raise ValueError("'order' must be 2 or 3.")
    freqs, amp = _amplitude_spectrum(sig, fs_v, window)
    df = float(freqs[1] - freqs[0]) if freqs.size > 1 else 0.0
    half = min(_IMD_SEARCH_BINS * df, (fb - fa) / 4.0)
    ref = _tone_amplitude(freqs, amp, fa, half) + _tone_amplitude(freqs, amp, fb, half)
    if ref <= 0.0:
        raise ValueError("No primary tones found at 'f1'/'f2'.")
    if order == 2:
        value = _imd_component(freqs, amp, fb - fa, half, exclude=(fa, fb))
    else:
        value = _imd_component(
            freqs, amp, 2 * fa - fb, half, exclude=(fa, fb)
        ) + _imd_component(freqs, amp, 2 * fb - fa, half, exclude=(fa, fb))
    return float(value / ref)


def total_difference_frequency_distortion(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    f1: float = 8000.0,
    f2: float = 11950.0,
    *,
    window: str = "hann",
) -> float:
    """Total difference-frequency distortion (IEC 60268-3 14.12.10).

    A specific two-tone test with ``f1 = 2·f0`` and ``f2 = 3·f0 − δ`` (the
    standard values, kept as defaults, are ``f1 = 8 kHz``, ``f2 = 11,95 kHz``,
    so ``f0 = 4 kHz`` and ``δ = 50 Hz``). Only the two in-band products at
    ``f0 ∓ δ`` enter -- the second-order product at ``f2 − f1`` and the
    third-order product at ``2·f1 − f2`` -- combined in RMS over the
    arithmetic sum of the two tone output amplitudes (14.12.10.2 g):

    ``d_TDFD = √(a²_{f2−f1} + a²_{2f1−f2}) / (a_{f1} + a_{f2})``.

    (The out-of-band product at ``2·f2 − f1`` is explicitly not part of it.)

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param f1: Lower tone, in Hz (default 8 kHz, per 14.12.10.2 b).
    :param f2: Upper tone, in Hz (default 11,95 kHz, per 14.12.10.2 b).
    :param window: FFT window (default ``'hann'``).
    :return: Total difference-frequency distortion, as a ratio.
    :raises ValueError: If the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    fa = _positive(f1, "f1")
    fb = _positive(f2, "f2")
    if fa >= fb:
        raise ValueError("'f1' must be lower than 'f2'.")
    freqs, amp = _amplitude_spectrum(sig, fs_v, window)
    df = float(freqs[1] - freqs[0]) if freqs.size > 1 else 0.0
    p_lo, p_hi = fb - fa, 2 * fa - fb  # f0 - delta and f0 + delta
    # The two products sit 2*delta apart: cap the window well inside that
    # so they are never double-counted, besides the usual bin-based cap.
    spacing = abs(p_hi - p_lo)
    half = min(_IMD_SEARCH_BINS * df, (fb - fa) / 4.0)
    if spacing > 0.0:
        half = min(half, spacing / 4.0)
    ref = _tone_amplitude(freqs, amp, fa, half) + _tone_amplitude(freqs, amp, fb, half)
    if ref <= 0.0:
        raise ValueError("No primary tones found at 'f1'/'f2'.")
    a_lo = _imd_component(freqs, amp, p_lo, half, exclude=(fa, fb))
    a_hi = _imd_component(freqs, amp, p_hi, half, exclude=(fa, fb))
    return float(np.sqrt(a_lo**2 + a_hi**2) / ref)


#: Highest square-wave harmonic order that produces a DIM difference product
#: below f_sine. For the standard 15 kHz / 3.15 kHz signal the nine products of
#: IEC 60268-3 Table 2 span 0.75 kHz (k=5) to 13.35 kHz (k=9), so k must reach 9.
_DIM_MAX_ORDER = 9
#: DIM product search half-width, as a fraction of f_square. Kept well below the
#: spacing between a product and the square-wave fundamental/harmonics (750 Hz
#: for the standard signal) so a strong f_square component is never mistaken for
#: an intermodulation product.
_DIM_SEARCH_FACTOR = 0.1


def _dim_components(f_sine: float, f_square: float, nyquist: float) -> list[float]:
    """DIM difference products ``|k·f_square − f_sine|`` below ``f_sine`` (Table 2)."""
    products: set[float] = set()
    for k in range(1, _DIM_MAX_ORDER + 1):
        for sign in (-1.0, 1.0):
            f = abs(k * f_square + sign * f_sine)
            if 0.0 < f < min(f_sine, nyquist):
                products.add(round(f, 6))
    return sorted(products)


def dynamic_intermodulation_distortion(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    *,
    f_sine: float = 15000.0,
    f_square: float = 3150.0,
    window: str = "hann",
) -> float:
    """Dynamic intermodulation distortion DIM (IEC 60268-3 14.12.9).

    From the standard test signal -- a ``f_sine`` = 15 kHz sine plus a
    low-pass-filtered ``f_square`` = 3.15 kHz square wave in a 1:4 peak ratio --
    the DIM is the RMS of the intermodulation products ``|k·f_square ± f_sine|``
    that fall below ``f_sine`` (IEC 60268-3 Table 2), relative to the 15 kHz
    sine amplitude.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param f_sine: High sine frequency, in Hz (default 15 kHz).
    :param f_square: Square-wave fundamental, in Hz (default 3.15 kHz).
    :param window: FFT window (default ``'hann'``).
    :return: Dynamic intermodulation distortion, as a ratio.
    :raises ValueError: If the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    fsine = _positive(f_sine, "f_sine")
    fsq = _positive(f_square, "f_square")
    freqs, amp = _amplitude_spectrum(sig, fs_v, window)
    search = fsq * _DIM_SEARCH_FACTOR
    # Reference: the output amplitude at f_s, per the 14.12.9.1 definition
    # ("the ratio of the r.m.s. sum of the output voltages ... to the
    # amplitude of the output voltage at the frequency f_s"). The 14.12.9.2 f)
    # formula prints the denominator as "U2", which contradicts 14.12.9.1 and
    # is an editorial defect of IEC 60268-3:2013 (see docs/ERRATA.md); the
    # Otala convention implemented here follows the 14.12.9.1 definition.
    ref = _tone_amplitude(freqs, amp, fsine, search)
    if ref <= 0.0:
        raise ValueError("No 15 kHz sine component found.")
    power = 0.0
    for f in _dim_components(fsine, fsq, fs_v / 2.0):
        power += _tone_amplitude(freqs, amp, f, search) ** 2
    return float(np.sqrt(power) / ref)


# --------------------------------------------------------------------------- #
# Result bundle
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HarmonicDistortionResult:
    """Harmonic analysis of a signal (IEC 60268-3 / AES17).

    :ivar fundamental: Fundamental frequency ``f₁``, in Hz.
    :ivar harmonic_frequencies: Harmonic frequencies ``n·f₁`` present, in Hz.
    :ivar harmonic_amplitudes: Peak amplitudes ``aₙ`` of the harmonics.
    :ivar thd_f: Total harmonic distortion relative to the fundamental.
    :ivar thd_r: Total harmonic distortion relative to the total RMS.
    :ivar thd_plus_noise: THD+N ratio (AES17).
    :ivar sinad_db: SINAD, in dB.
    """

    fundamental: float
    harmonic_frequencies: "NDArray[np.float64]"
    harmonic_amplitudes: "NDArray[np.float64]"
    thd_f: float
    thd_r: float
    thd_plus_noise: float
    sinad_db: float

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the magnitude spectrum with the harmonics marked."""
        from .._plot.electroacoustics import plot_harmonic_distortion

        return plot_harmonic_distortion(self, ax=ax, **kwargs)


def harmonic_analysis(
    signal: "NDArray[np.float64] | list[float]",
    fs: float,
    fundamental: float | None = None,
    *,
    n_harmonics: int = _DEFAULT_N_HARMONICS,
    notch_q: float = _DEFAULT_NOTCH_Q,
    window: str = "hann",
) -> HarmonicDistortionResult:
    """Full harmonic analysis of a signal (THD, THD+N, SINAD).

    Bundles the fundamental, the harmonic amplitudes and the THD (both
    conventions), THD+N and SINAD into a plottable result.

    :param signal: Captured signal (1-D).
    :param fs: Sample rate, in Hz.
    :param fundamental: Fundamental frequency, or ``None`` to auto-detect.
    :param n_harmonics: Highest harmonic order (default 10).
    :param notch_q: Notch quality factor for THD+N (default 2.0).
    :param window: FFT window (default ``'hann'``).
    :return: A :class:`HarmonicDistortionResult`.
    :raises ValueError: If the inputs are invalid.
    """
    sig = _validate_signal(signal)
    fs_v = _positive(fs, "fs")
    f0, amps = _harmonic_amplitudes(sig, fs_v, fundamental, n_harmonics, window)
    if amps.size == 0 or amps[0] <= 0.0:
        raise ValueError("No fundamental component found in the signal.")
    freqs = np.array([(k + 1) * f0 for k in range(amps.size)], dtype=np.float64)
    thd_f = thd(sig, fs_v, f0, kind="F", n_harmonics=n_harmonics, window=window)
    thd_r = thd(sig, fs_v, f0, kind="R", n_harmonics=n_harmonics, window=window)
    thdn = thd_plus_noise(sig, fs_v, f0, notch_q=notch_q, window=window)
    sinad_db = sinad(sig, fs_v, f0, notch_q=notch_q, window=window)
    return HarmonicDistortionResult(
        fundamental=f0,
        harmonic_frequencies=freqs,
        harmonic_amplitudes=amps,
        thd_f=thd_f,
        thd_r=thd_r,
        thd_plus_noise=thdn,
        sinad_db=sinad_db,
    )
