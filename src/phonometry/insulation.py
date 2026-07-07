#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Field airborne sound insulation (ISO 16283-1:2014) and single-number
weighted ratings with spectrum adaptation terms (ISO 717-1).

**Field quantities (ISO 16283-1:2014).** From the energy-average sound
pressure levels in the source and receiving rooms this module forms the
level difference ``D = L1 - L2`` (Clause 3.12, Formula (1)), the
standardized level difference ``DnT = D + 10 lg(T/T0)`` with the
reference reverberation time ``T0 = 0,5 s`` (Clause 3.13, Formula (2)),
and the apparent sound reduction index
``R' = D + 10 lg(S/A)`` with the Sabine equivalent absorption area
``A = 0,16 V / T`` (Clause 3.14/3.15, Formula (4) and (5)). Source and
receiving levels may be supplied already averaged (one value per band) or
as several microphone positions, which are then energy-averaged with
``10 lg( (1/n) sum 10^(Li/10) )`` (Clause 7.8, Formula (9)). All
quantities are evaluated per one-third-octave band over the core range
100 Hz to 3150 Hz (Clause 5), the caller having already applied any
background-noise correction (Clause 9.2).

**Weighted rating (ISO 717-1).** The reference-curve method of Clause 4.4
shifts the reference curve of Table 3 in 1 dB steps towards the measured
curve until the sum of unfavourable deviations (measured below the
shifted reference) is as large as possible but not more than 32,0 dB for
the 16 one-third-octave bands (100 Hz to 3150 Hz) or 10,0 dB for the 5
octave bands (125 Hz to 2000 Hz). The weighted rating (``Rw``, ``R'w``,
``Dn,w``, ``DnT,w`` ...) is the shifted reference read at 500 Hz. The
spectrum adaptation terms are ``C = XA1 - Xw`` and ``Ctr = XA2 - Xw``
with ``XAj = -10 lg sum 10^((Lij - Xi)/10)`` rounded to an integer, using
the A-weighted spectra No. 1 (pink noise, ``C``) and No. 2 (urban traffic,
``Ctr``) of Table 4 (Clause 4.5, Formula (1) and (2)). Input levels are
reduced to one decimal place before use (Clause 4.4, footnote 1). The
reference values, spectra and shifting rule are identical in the 2013 and
2020 editions of ISO 717-1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

# --- ISO 717-1 Table 3 reference values ----------------------------------

#: One-third-octave reference values, 100 Hz to 3150 Hz (Table 3).
_REF_THIRD_OCTAVE: Tuple[int, ...] = (
    33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56,
)
#: Octave reference values, 125 Hz to 2000 Hz (Table 3).
_REF_OCTAVE: Tuple[int, ...] = (36, 45, 52, 55, 56)

#: Index of the 500 Hz band in each band set (the rating is read there).
_INDEX_500_THIRD = 7
_INDEX_500_OCTAVE = 2

#: Maximum sum of unfavourable deviations (Clause 4.4).
_MAX_UNFAVOURABLE_THIRD = 32.0
_MAX_UNFAVOURABLE_OCTAVE = 10.0

# --- ISO 717-1 Table 4 spectra (A-weighted, normalized to 0 dB) ----------

#: Spectrum No. 1 (pink noise, for C), one-third octave 100-3150 Hz.
_SPECTRUM1_THIRD: Tuple[int, ...] = (
    -29, -26, -23, -21, -19, -17, -15, -13, -12, -11, -10, -9, -9, -9, -9, -9,
)
#: Spectrum No. 2 (urban traffic, for Ctr), one-third octave 100-3150 Hz.
_SPECTRUM2_THIRD: Tuple[int, ...] = (
    -20, -20, -18, -16, -15, -14, -13, -12, -11, -9, -8, -9, -10, -11, -13, -15,
)
#: Spectrum No. 1 (for C), octave 125-2000 Hz.
_SPECTRUM1_OCTAVE: Tuple[int, ...] = (-21, -14, -8, -5, -4)
#: Spectrum No. 2 (for Ctr), octave 125-2000 Hz.
_SPECTRUM2_OCTAVE: Tuple[int, ...] = (-14, -10, -7, -4, -6)


@dataclass(frozen=True)
class AirborneInsulationResult:
    """Per-band field airborne sound insulation (ISO 16283-1:2014).

    :ivar d: Level difference ``D = L1 - L2`` per band, in dB
        (Clause 3.12, Formula (1)).
    :ivar dnt: Standardized level difference ``DnT`` per band, in dB
        (Clause 3.13, Formula (2)).
    :ivar r_prime: Apparent sound reduction index ``R'`` per band, in dB
        (Clause 3.14, Formula (4)), or ``None`` when the partition area
        and receiving-room volume were not supplied.
    """

    d: np.ndarray
    dnt: np.ndarray
    r_prime: np.ndarray | None


@dataclass(frozen=True)
class WeightedRatingResult:
    """Single-number weighted rating and adaptation terms (ISO 717-1).

    :ivar rating: Weighted rating (``Rw``, ``R'w``, ``DnT,w`` ...), the
        shifted reference read at 500 Hz, in dB (Clause 4.4). Integer.
    :ivar c: Spectrum adaptation term ``C`` (spectrum No. 1), in dB
        (Clause 4.5). Integer.
    :ivar ctr: Spectrum adaptation term ``Ctr`` (spectrum No. 2), in dB
        (Clause 4.5). Integer.
    :ivar unfavourable_sum: Sum of unfavourable deviations at the final
        shift, in dB (Clause 4.4); at most 32,0 (16 bands) or 10,0 (5
        bands).
    """

    rating: int
    c: int
    ctr: int
    unfavourable_sum: float


def _round_half_up_tenths(values: np.ndarray) -> np.ndarray:
    """Reduce levels to one decimal place (ISO 717-1 Clause 4.4, note 1).

    Rounds each value to the nearest tenth of a decibel, half away from
    zero (``floor(x*10 + 0,5)/10`` for non-negative values, mirrored for
    negative ones).
    """
    return np.sign(values) * np.floor(np.abs(values) * 10.0 + 0.5) / 10.0


def energy_average_level(
    levels: Sequence[float] | np.ndarray, axis: int = -1
) -> np.ndarray | float:
    """
    Energy-average sound pressure level (ISO 16283-1:2014, Formula (9)).

    Combines sound pressure levels measured at several microphone
    positions into ``L = 10 lg( (1/n) sum_i 10^(Li/10) )``.

    :param levels: Sound pressure levels, in dB, at the ``n`` positions to
        be averaged along ``axis``.
    :param axis: Axis over which to average (default the last axis).
    :return: The energy-average level, in dB; a scalar ``float`` when the
        result is zero-dimensional, otherwise an array.
    :raises ValueError: If ``levels`` is empty or contains non-finite
        values.
    """
    data = np.asarray(levels, dtype=np.float64)
    if data.size == 0:
        raise ValueError("'levels' must not be empty.")
    if not np.all(np.isfinite(data)):
        raise ValueError("'levels' must contain only finite values.")
    n = data.shape[axis]
    result: np.ndarray = 10.0 * np.log10(
        np.sum(10.0 ** (data / 10.0), axis=axis) / n
    )
    if result.ndim == 0:
        return float(result)
    return result


def _as_band_levels(
    levels: Sequence[float] | np.ndarray, name: str
) -> np.ndarray:
    """Coerce room levels to per-band values, energy-averaging positions.

    A one-dimensional input is taken as one already-averaged level per
    band; a two-dimensional input is read as ``(positions, bands)`` and
    energy-averaged over the positions (Formula (9)).
    """
    data = np.asarray(levels, dtype=np.float64)
    if data.ndim == 1:
        out = data
    elif data.ndim == 2:
        out = np.asarray(energy_average_level(data, axis=0), dtype=np.float64)
    else:
        raise ValueError(f"'{name}' must be 1-D or 2-D (positions x bands).")
    if out.size == 0:
        raise ValueError(f"'{name}' must not be empty.")
    if not np.all(np.isfinite(out)):
        raise ValueError(f"'{name}' must contain only finite values.")
    return out


def airborne_insulation(
    l1: Sequence[float] | np.ndarray,
    l2: Sequence[float] | np.ndarray,
    t2: Sequence[float] | np.ndarray,
    *,
    area: float | None = None,
    volume: float | None = None,
    t0: float = 0.5,
) -> AirborneInsulationResult:
    """
    Field airborne sound insulation per ISO 16283-1:2014.

    Computes, per frequency band, the level difference ``D = L1 - L2``
    (Formula (1)), the standardized level difference
    ``DnT = D + 10 lg(T/T0)`` (Formula (2)) and, when the partition area
    and receiving-room volume are given, the apparent sound reduction
    index ``R' = D + 10 lg(S/A)`` with ``A = 0,16 V / T`` (Formula (4)
    and (5)).

    ``l1`` and ``l2`` may be one value per band (already energy-averaged)
    or a two-dimensional ``(positions, bands)`` array, in which case the
    positions are energy-averaged with Formula (9). The band levels are
    assumed already corrected for background noise (Clause 9.2).

    :param l1: Source-room sound pressure levels, in dB.
    :param l2: Receiving-room sound pressure levels, in dB.
    :param t2: Receiving-room reverberation time per band, in seconds.
    :param area: Area ``S`` of the common partition, in m² (optional;
        required together with ``volume`` for ``R'``).
    :param volume: Receiving-room volume ``V``, in m³ (optional; required
        together with ``area`` for ``R'``).
    :param t0: Reference reverberation time ``T0``, in seconds (default
        0,5 s for dwellings, Clause 3.13).
    :return: :class:`AirborneInsulationResult` with ``d``, ``dnt`` and
        ``r_prime`` (the latter ``None`` unless ``area`` and ``volume``
        are both given).
    :raises ValueError: If the band counts of ``l1``, ``l2`` and ``t2``
        differ, if only one of ``area``/``volume`` is supplied, if
        ``t2``/``t0`` are not positive, or if inputs are non-finite.
    """
    l1_bands = _as_band_levels(l1, "l1")
    l2_bands = _as_band_levels(l2, "l2")
    t = np.asarray(t2, dtype=np.float64)

    if not (l1_bands.shape == l2_bands.shape == t.shape):
        raise ValueError("'l1', 'l2' and 't2' must share the same band count.")
    if t.ndim != 1:
        raise ValueError("'t2' must be one-dimensional (one value per band).")
    if not np.all(np.isfinite(t)) or np.any(t <= 0.0):
        raise ValueError("'t2' must contain positive, finite values.")
    if t0 <= 0.0:
        raise ValueError("'t0' must be positive.")

    d = l1_bands - l2_bands
    dnt = d + 10.0 * np.log10(t / t0)

    if (area is None) != (volume is None):
        raise ValueError(
            "'area' and 'volume' must be given together to compute R'."
        )
    r_prime: np.ndarray | None = None
    if area is not None and volume is not None:
        if area <= 0.0 or volume <= 0.0:
            raise ValueError("'area' and 'volume' must be positive.")
        absorption = 0.16 * volume / t
        r_prime = d + 10.0 * np.log10(area / absorption)

    return AirborneInsulationResult(d=d, dnt=dnt, r_prime=r_prime)


def _resolve_band_set(
    n: int, bands: str | None
) -> Tuple[Tuple[int, ...], float, int, Tuple[int, ...], Tuple[int, ...]]:
    """Select the reference curve, bound and spectra for the band set.

    :return: ``(reference, max_unfavourable, index_500, spectrum1,
        spectrum2)``.
    """
    if bands == "third-octave" or (bands is None and n == 16):
        if n != 16:
            raise ValueError(
                "One-third-octave rating needs 16 bands (100-3150 Hz), "
                f"got {n}."
            )
        return (
            _REF_THIRD_OCTAVE,
            _MAX_UNFAVOURABLE_THIRD,
            _INDEX_500_THIRD,
            _SPECTRUM1_THIRD,
            _SPECTRUM2_THIRD,
        )
    if bands == "octave" or (bands is None and n == 5):
        if n != 5:
            raise ValueError(
                "Octave rating needs 5 bands (125-2000 Hz), " f"got {n}."
            )
        return (
            _REF_OCTAVE,
            _MAX_UNFAVOURABLE_OCTAVE,
            _INDEX_500_OCTAVE,
            _SPECTRUM1_OCTAVE,
            _SPECTRUM2_OCTAVE,
        )
    if bands is not None:
        raise ValueError("'bands' must be 'third-octave', 'octave' or None.")
    raise ValueError(
        "Expected 16 one-third-octave (100-3150 Hz) or 5 octave "
        f"(125-2000 Hz) values, got {n}."
    )


def _best_shift(
    measured: np.ndarray, reference: np.ndarray, limit: float
) -> Tuple[int, float]:
    """Largest 1 dB shift with unfavourable-deviation sum within ``limit``.

    Shifts the reference by integer ``k`` and returns the largest ``k``
    for which ``sum max(0, reference + k - measured) <= limit`` (the sum
    is monotone non-decreasing in ``k``), together with that sum.
    """
    # Start below any feasible shift, then climb while the bound holds.
    k = int(np.floor(np.min(measured - reference))) - 1
    while True:
        next_sum = float(np.sum(np.maximum(0.0, reference + (k + 1) - measured)))
        if next_sum > limit:
            break
        k += 1
    unfavourable = float(np.sum(np.maximum(0.0, reference + k - measured)))
    return k, unfavourable


def _adaptation_term(
    measured: np.ndarray, spectrum: Tuple[int, ...], rating: int
) -> int:
    """Spectrum adaptation term ``Xaj - rating`` (Clause 4.5, Formula (2))."""
    x_aj = -10.0 * np.log10(
        np.sum(10.0 ** ((np.asarray(spectrum, dtype=np.float64) - measured) / 10.0))
    )
    return int(math.floor(x_aj + 0.5)) - rating


def weighted_rating(
    values_by_band: Sequence[float] | np.ndarray,
    bands: str | None = None,
) -> WeightedRatingResult:
    """
    Single-number weighted rating and C / Ctr per ISO 717-1.

    Applies the reference-curve method of Clause 4.4: the Table 3
    reference curve is shifted in 1 dB steps towards the measured curve
    until the sum of unfavourable deviations is as large as possible but
    not more than 32,0 dB (16 one-third-octave bands, 100 Hz to 3150 Hz)
    or 10,0 dB (5 octave bands, 125 Hz to 2000 Hz). The rating is the
    shifted reference read at 500 Hz. The spectrum adaptation terms
    ``C`` and ``Ctr`` follow Clause 4.5 with the Table 4 spectra No. 1 and
    No. 2. Input values are first reduced to one decimal place
    (Clause 4.4, footnote 1).

    :param values_by_band: Measured band quantities (``R``, ``R'``,
        ``Dn``, ``DnT`` ...) in dB. 16 values are read as one-third-octave
        bands, 5 values as octave bands.
    :param bands: ``"third-octave"``, ``"octave"`` or ``None`` to infer
        the band set from the number of values.
    :return: :class:`WeightedRatingResult` with ``rating``, ``c``,
        ``ctr`` and ``unfavourable_sum``.
    :raises ValueError: If the number of values does not match the band
        set, or if any value is non-finite.
    """
    data = np.asarray(values_by_band, dtype=np.float64)
    if data.ndim != 1:
        raise ValueError("'values_by_band' must be one-dimensional.")
    if not np.all(np.isfinite(data)):
        raise ValueError("'values_by_band' must contain only finite values.")

    reference, limit, index_500, spectrum1, spectrum2 = _resolve_band_set(
        int(data.size), bands
    )
    measured = _round_half_up_tenths(data)
    ref = np.asarray(reference, dtype=np.float64)

    shift, unfavourable = _best_shift(measured, ref, limit)
    rating = int(reference[index_500]) + shift
    c = _adaptation_term(measured, spectrum1, rating)
    ctr = _adaptation_term(measured, spectrum2, rating)
    return WeightedRatingResult(
        rating=rating, c=c, ctr=ctr, unfavourable_sum=unfavourable
    )
