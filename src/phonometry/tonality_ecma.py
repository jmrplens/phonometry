#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Psychoacoustic tonality per ECMA-418-2:2025 (4th ed., Sottek Hearing Model).

Clean-room implementation of the tonality signal chain of ECMA-418-2:2025
(Clause 6.2). The shared auditory front-end (Clause 5) and the ACF-based
tonal/noise decomposition (Clause 6.2.2-6.2.7) are reused from
:mod:`.loudness_ecma`; this module adds

* the **full Clause 6.2.3 band averaging** (:func:`_average_bands_full`),
  including the cross-block-size-group ACF recomputation that the loudness
  path deliberately omits (see the boundary marker in
  :func:`loudness_ecma._average_bands`);
* the tonal frequency f_ton(l, z) (Formulae 38-39), tracked through the
  common-grid resampling; and
* the tonality output stages (Clause 6.2.8-6.2.11): the overall-SNR gate
  q(l) (Formulae 49-50), the time-dependent specific tonality
  T'(l, z) = c_T * q(l) * N'_tonal(l, z) (Formula 51), the average specific
  tonality T'(z) and its frequency f_ton,z(z) (Formulae 53-55), the
  time-dependent tonality T(l) with its frequency f_ton(l) (Formulae 61-62)
  and the representative single value T (Formulae 63-64).

The calibration factor ``c_T`` of Formula (51) is fixed by the standard so
that a 1 kHz sinusoid at 40 dB SPL yields 1 tu_HMS.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Tuple

import numpy as np
from scipy import signal

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from .loudness_ecma import (
    _CBF,
    _EPS,
    _F_CENTRE,
    _FS,
    _G_Z,
    _INTERP,
    _N_B_BY_SB,
    _R_SD,
    _S_B,
    _S_B_MAX,
    _Z,
    _auditory_bandpass,
    _band_acf,
    _average_blocks,
    _ear_filter_sos,
    _lowpass_time,
    _preprocess,
    _resample_common,
    _specific_basis_loudness,
    _tonal_estimate,
)
from ._validation import require_1d_signal
from .utils import _typesignal

# Noise reduction sigmoid parameters (Table 7), reused on the tonality path.
_NR_ALPHA = 20.0
_NR_BETA = 0.07

# Overall-SNR scaling gate q(l) (Formula 50, Table 9).
_Q_A = 35.0
_Q_B = 0.003

# Tonality calibration factor c_T (Formula 51); 1 kHz/40 dB -> 1 tu_HMS.
_C_T = 2.8758615

# Averaging gate (Clause 6.2.9/6.2.11) and transient discard (Clause 6.2.9).
_T_GATE = 0.02  # tu_HMS
_TRANSIENT_BLOCKS = 56  # discard l in [0, 56]


@dataclass(frozen=True)
class EcmaTonality:
    """Result of an ECMA-418-2:2025 (Sottek) tonality calculation.

    ``tonality`` is the single representative tonality T in tu_HMS
    (Formula 63). ``specific_tonality`` is the average specific tonality
    T'(z) in tu_HMS over the 53 auditory bands (Formula 53), with ``bark``
    the critical-band-rate scale z (0.5..26.5 Bark_HMS), ``centre_frequencies``
    the band centre frequencies F(z) and ``tonal_frequencies`` the per-band
    tonal frequency f_ton,z(z) (Formula 55). ``time`` and ``tonality_vs_time``
    hold the time-dependent tonality T(l) at 187.5 Hz (Formula 61) and
    ``tonal_frequency_vs_time`` its frequency f_ton(l) (Formula 62). ``field``
    records the assumed sound field.
    """

    tonality: float
    specific_tonality: np.ndarray
    bark: np.ndarray
    centre_frequencies: np.ndarray
    tonal_frequencies: np.ndarray
    time: np.ndarray
    tonality_vs_time: np.ndarray
    tonal_frequency_vs_time: np.ndarray
    field: str

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes | np.ndarray:
        """Plot the average specific tonality T'(z) (see :mod:`._plotting`).

        Adds a tonality-vs-time panel. Requires matplotlib
        (``pip install phonometry[plot]``).
        """
        from ._plotting import plot_ecma_tonality

        return plot_ecma_tonality(self, ax=ax, **kwargs)


# --------------------------------------------------------------------------
# Full Clause 6.2.3 band averaging (cross-block-size-group recomputation)
# --------------------------------------------------------------------------


def _segment_bs(p_band: np.ndarray, block_size: int, n_new: int) -> np.ndarray:
    """Segment a band-pass signal at an arbitrary block size (Clause 5.1.5).

    Mirrors :func:`loudness_ecma._segment` but takes the block size directly so
    a band can be re-segmented at a *foreign* block size for the cross-group
    averaging of Clause 6.2.3. Returns an array of shape ``(n_blocks, block_size)``.
    """
    s_h = block_size // 4  # 75 % overlap
    i_start = _S_B_MAX - block_size  # Formula 19
    l_last = math.ceil((n_new + s_h) / s_h) - 1  # Formula 20
    starts = i_start + s_h * np.arange(l_last + 1)
    starts = starts[starts + block_size <= p_band.size]
    idx = starts[:, None] + np.arange(block_size)[None, :]
    return np.asarray(p_band[idx], dtype=np.float64)


def _scaled_acf_at(
    p_bands: List[np.ndarray],
    band: int,
    block_size: int,
    n_new: int,
    cache: Dict[Tuple[int, int], np.ndarray],
) -> np.ndarray:
    """Scaled ACF phi'_z(m) of ``band`` computed at ``block_size`` (Formulae 22-30).

    Segments the band-pass signal at ``block_size``, half-wave rectifies
    (Formula 21), forms the block RMS (Formula 22) and specific basis loudness
    (Formula 25), the unbiased normalized ACF (Formulae 27-29) and scales it by
    the basis loudness (Formula 30). Cached by ``(band, block_size)``.
    """
    key = (band, block_size)
    cached = cache.get(key)
    if cached is not None:
        return cached
    seg = _segment_bs(p_bands[band], block_size, n_new)
    rect = np.where(seg > 0.0, seg, 0.0)  # Formula 21
    rms = np.sqrt((2.0 / block_size) * np.sum(rect**2, axis=1))  # Formula 22
    basis = _specific_basis_loudness(rms, band)  # Formulae 23-25
    acf = _band_acf(rect, block_size)  # Formulae 27-29
    scaled = np.asarray(acf * basis[:, None], dtype=np.float64)  # Formula 30
    cache[key] = scaled
    return scaled


def _average_bands_full(
    p_bands: List[np.ndarray], n_new: int
) -> List[np.ndarray]:
    """Full Clause 6.2.3 band averaging with cross-group recomputation.

    For each target band z (block size B = s_b(z), reach = min(N_B, z, 52-z)),
    the neighbouring bands are re-segmented and re-correlated **at block size
    B** so the average is over identical block sizes (the requirement the
    loudness path skips). The result stays on band z's native time grid.
    """
    cache: Dict[Tuple[int, int], np.ndarray] = {}
    out: List[np.ndarray] = []
    for band in range(_CBF):
        block_size = int(_S_B[band])
        n_b = _N_B_BY_SB[block_size]
        native = _scaled_acf_at(p_bands, band, block_size, n_new, cache)
        if n_b == 0:
            out.append(native)
            continue
        if band == 0:  # lowest band: averaged only with the second-lowest
            other = _scaled_acf_at(p_bands, 1, block_size, n_new, cache)
            out.append(0.5 * (native + other))
            continue
        # The ``_CBF-1-band`` upper-edge term is a defensive guard that cannot
        # fire: bands with N_B > 0 all sit at low index (0..24, block size
        # >= 2048), so their distance to the top band (>= 28) never limits the
        # symmetric reach (n_b <= 2).  Only the ``band`` lower-edge term bites.
        reach = min(n_b, band, _CBF - 1 - band)
        if reach == 0:
            out.append(native)
            continue
        stack = [
            _scaled_acf_at(p_bands, band + off, block_size, n_new, cache)
            for off in range(-reach, reach + 1)
        ]
        out.append(np.mean(np.stack(stack, axis=0), axis=0))
    return out


# --------------------------------------------------------------------------
# Tonal / noise loudness with tonal-frequency tracking (Clause 6.2.4-6.2.8)
# --------------------------------------------------------------------------


def _tonal_noise_tonality(
    x: np.ndarray, field: str
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """Specific tonal/noise loudness and tonal frequency on the common grid.

    Returns ``(N'_tonal(l, z), N'_noise(l, z), f_ton(l, z), n_common,
    n_samples)`` (Formulae 41-48 plus the tonal frequency of Formula 39). Uses
    the full Clause 6.2.3 band averaging.
    """
    padded, n_samples, n_new = _preprocess(x)
    p_om = signal.sosfilt(_ear_filter_sos(field), padded)
    p_bands = [_auditory_bandpass(p_om, band) for band in range(_CBF)]

    averaged = _average_blocks(_average_bands_full(p_bands, n_new))

    n_common = max(averaged[b].shape[0] * int(_INTERP[b]) for b in range(_CBF))
    n_tonal = np.zeros((n_common, _CBF))
    n_signal = np.zeros((n_common, _CBF))
    f_ton = np.zeros((n_common, _CBF))
    for band in range(_CBF):
        tonal_b, signal_b, fton_b = _tonal_estimate(averaged[band], band)
        n_tonal[:, band] = _resample_common(tonal_b, band, n_common)
        n_signal[:, band] = _resample_common(signal_b, band, n_common)
        f_ton[:, band] = _resample_common(fton_b, band, n_common)

    # Noise reduction (Formulae 42-48).
    snr_hat = n_tonal / (n_signal - n_tonal + _EPS)  # Formula 42
    n_tonal_lp = _lowpass_time(n_tonal)  # Formula 43
    snr_lp = _lowpass_time(snr_hat)  # Formula 44
    n_signal_lp = _lowpass_time(n_signal)
    arg = _NR_ALPHA * (snr_lp / _G_Z[None, :] - _NR_BETA)  # Formula 45
    nr = np.where(arg > 0.0, 1.0 - np.exp(-arg), 0.0)
    n_tonal_final = nr * n_tonal_lp  # Formula 47
    n_noise_final = np.maximum(n_signal_lp - n_tonal_final, 0.0)  # Formula 48
    return n_tonal_final, n_noise_final, f_ton, n_common, n_samples


# --------------------------------------------------------------------------
# Tonality assembly (Clause 6.2.8-6.2.11)
# --------------------------------------------------------------------------


def _band_range(f_low: float | None, f_high: float | None) -> Tuple[int, int]:
    """Critical-band index range [z_L, z_H] for a user band (Formulae 56-60).

    ``None`` limits default to the full 0..52 band range.  A band z is included
    when its edge midpoints to the neighbouring bands straddle the user edge:
    ``f_low < (F(z) + F(z+0.5))/2`` selects z_L (Formula 56) and
    ``f_high > (F(z) + F(z-0.5))/2`` selects z_H (Formula 57).  ``mid[i]`` is
    the boundary between bands ``i`` and ``i+1`` on the 0.5-Bark_HMS grid.
    """
    z_lo = 0
    z_hi = _CBF - 1
    mid = (_F_CENTRE[:-1] + _F_CENTRE[1:]) / 2.0  # inter-band boundaries
    if f_low is not None:
        # z_L: lowest band whose upper boundary exceeds f_low (Formula 56).
        candidates = np.where(f_low < mid)[0]
        z_lo = int(candidates[0]) if candidates.size else _CBF - 1
    if f_high is not None:
        # z_H: highest band whose lower boundary is below f_high (Formula 57);
        # f_high > mid[j] admits band j+1, so shift the index up by one.
        candidates = np.where(f_high > mid)[0]
        z_hi = int(candidates[-1]) + 1 if candidates.size else 0
    if z_hi < z_lo:
        z_lo, z_hi = z_hi, z_lo
    return z_lo, z_hi


def _assemble_tonality(
    n_tonal: np.ndarray,
    n_noise: np.ndarray,
    f_ton: np.ndarray,
    n_samples: int,
    z_lo: int,
    z_hi: int,
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the tonality metric (Clause 6.2.8-6.2.11).

    Returns ``(T, T'(z), f_ton,z(z), T(l), f_ton(l), time)``.
    """
    n_blocks = n_tonal.shape[0]
    # Overall-SNR gate (Formulae 49-50).
    snr = np.max(n_tonal, axis=1) / (_EPS + np.sum(n_noise, axis=1))  # F.49
    q = np.where(snr > _Q_B, 1.0 - np.exp(-_Q_A * (snr - _Q_B)), 0.0)  # F.50
    t_spec_lz = _C_T * q[:, None] * n_tonal  # Formula 51: T'(l, z)

    # Averaging window: discard transient, bound by l_end (Formulae 40, 54).
    l_end = min(math.ceil(n_samples / _FS * _R_SD), n_blocks - 1)
    keep = slice(_TRANSIENT_BLOCKS + 1, l_end + 1)
    if t_spec_lz[keep].shape[0] == 0:  # very short signals: fall back to all
        keep = slice(0, n_blocks)  # (matches loudness_ecma's fallback)
    t_win = t_spec_lz[keep]  # (n_kept, z)
    f_win = f_ton[keep]

    # Average specific tonality T'(z) and frequency f_ton,z(z) (Formulae 53-55).
    gate = t_win > _T_GATE
    counts = gate.sum(axis=0)
    t_spec = np.where(counts > 0, (t_win * gate).sum(axis=0) / (counts + _EPS), 0.0)
    f_spec = np.where(counts > 0, (f_win * gate).sum(axis=0) / (counts + _EPS), 0.0)

    # Time-dependent tonality T(l) and its frequency (Formulae 61-62).
    band_slice = slice(z_lo, z_hi + 1)
    t_time = np.max(t_spec_lz[:, band_slice], axis=1)  # Formula 61
    z_max = z_lo + np.argmax(t_spec_lz[:, band_slice], axis=1)
    f_time = f_ton[np.arange(n_blocks), z_max]  # Formula 62

    # Representative single value T (Formulae 63-64).
    t_time_win = t_time[keep]
    tmask = t_time_win > _T_GATE
    n_sel = int(tmask.sum())
    t_single = float(t_time_win[tmask].sum() / (n_sel + _EPS)) if n_sel else 0.0

    time = np.arange(n_blocks) / _R_SD  # Formula 52
    return t_single, t_spec, f_spec, t_time, f_time, time


def tonality_ecma(
    signal_in: np.ndarray,
    fs: float,
    field: Literal["free", "diffuse"] = "free",
    f_low: float | None = None,
    f_high: float | None = None,
) -> EcmaTonality:
    """Psychoacoustic tonality per ECMA-418-2:2025 (Sottek Hearing Model).

    :param signal_in: Calibrated sound pressure signal in pascals.
    :param fs: Sampling rate in Hz. Signals not at 48 kHz are resampled
        (Clause 5.1.1).
    :param field: ``"free"`` (default) or ``"diffuse"`` sound field, selecting
        the outer/middle-ear filter of Clause 5.1.3.
    :param f_low: Optional lower edge (Hz) of a user frequency band for the
        time-dependent tonality maximum search (Formulae 56-60). ``None`` uses
        the full range.
    :param f_high: Optional upper edge (Hz) of the user frequency band.
    :return: An :class:`EcmaTonality` with the single value T (Formula 63),
        the average specific tonality T'(z) (Formula 53), the tonal
        frequencies f_ton,z(z) (Formula 55) and the time-dependent tonality
        T(l) (Formula 61) with its frequency (Formula 62).

    The 1 kHz / 40 dB SPL sinusoid yields 1 tu_HMS by construction of the
    calibration factor of Formula (51).
    """
    if field not in ("free", "diffuse"):
        raise ValueError("field must be 'free' or 'diffuse'")
    x = require_1d_signal(_typesignal(signal_in))
    if x.size == 0:
        raise ValueError("signal must not be empty")
    fs = float(fs)
    if fs <= 0.0:
        raise ValueError("fs must be positive")
    if fs != _FS:
        x = signal.resample(x, int(round(x.size * _FS / fs)))

    z_lo, z_hi = _band_range(f_low, f_high)
    n_tonal, n_noise, f_ton, _, n_samples = _tonal_noise_tonality(x, field)
    t_single, t_spec, f_spec, t_time, f_time, time = _assemble_tonality(
        n_tonal, n_noise, f_ton, n_samples, z_lo, z_hi
    )
    return EcmaTonality(
        tonality=t_single,
        specific_tonality=t_spec,
        bark=_Z.copy(),
        centre_frequencies=_F_CENTRE.copy(),
        tonal_frequencies=f_spec,
        time=time,
        tonality_vs_time=t_time,
        tonal_frequency_vs_time=f_time,
        field=field,
    )
