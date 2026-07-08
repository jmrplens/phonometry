#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Field airborne sound insulation (ISO 16283-1:2014) and impact sound
insulation (ISO 16283-2), with single-number weighted ratings and
spectrum adaptation terms (ISO 717-1 airborne, ISO 717-2 impact).

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

**Field impact quantities (ISO 16283-2).** With the tapping machine as the
impact source this module forms, from the energy-average impact sound
pressure level ``Li`` in the receiving room, the standardized impact sound
pressure level ``L'nT = Li - 10 lg(T/T0)`` with ``T0 = 0,5 s`` (Clause
3.13, Formula (1)) and the normalized impact sound pressure level
``L'n = Li + 10 lg(A/A0)`` with the Sabine absorption area ``A = 0,16 V/T``
and the reference area ``A0 = 10 m²`` (Clause 3.14, Formula (2)). Levels
may be supplied already averaged or as several microphone positions, then
energy-averaged (Clause 7.8, Formula (10)), over the core one-third-octave
range 100 Hz to 3150 Hz (Clause 5.1).

**Field façade quantities (ISO 16283-3:2016).** With an outdoor sound
source this module forms, from the level 2 m in front of the façade
``L1,2m`` and the receiving-room level ``L2``, the level difference
``D2m = L1,2m - L2`` (Clause 3.14), its standardized form
``D2m,nT = D2m + 10 lg(T/T0)`` with ``T0 = 0,5 s`` (Clause 3.15) and
normalized form ``D2m,n = D2m - 10 lg(A/A0)`` with the Sabine absorption
area ``A = 0,16 V/T`` (Clause 3.17) and reference ``A0 = 10 m²``
(Clause 3.16) — the global loudspeaker / traffic quantities
``Dls,2m,*`` / ``Dtr,2m,*``. When a surface level ``L1,s`` (microphone on
the test element) with the element area ``S`` and volume are given it
forms the apparent sound reduction index
``R'45° = L1,s - L2 + 10 lg(S/A) - 1,5`` for the loudspeaker element method
(Clause 3.12) or ``R'tr,s = L1,s - L2 + 10 lg(S/A) - 3`` for the
road-traffic element method (Clause 3.13). These quantities are defined by
unnumbered formulas inline in the Clause 3 terms; positions are
energy-averaged with the surface-level formula (Clause 9.5.1, Formula (7)).
Quantities are evaluated over the core one-third-octave range 100 Hz to
3150 Hz (Clause 5), optionally extended to 50-5000 Hz. The façade quantity
is airborne, so its single-number rating uses the **ISO 717-1 airborne**
reference curve and method (Clause 2, Annex F) via :func:`weighted_rating`
unchanged.

**Weighted impact rating (ISO 717-2).** The reference-curve method of
Clause 4.3 shifts the Table 3 impact reference curve towards the measured
curve until the sum of unfavourable deviations (here where the
**measurement exceeds** the reference, the sign opposite to airborne) is
as large as possible but not more than 32,0 dB (16 one-third-octave bands)
or 10,0 dB (5 octave bands). The rating (``Ln,w``, ``L'n,w``, ``L'nT,w``)
is the shifted reference read at 500 Hz, reduced by a further 5 dB for
octave bands (Clause 4.3.2). The spectrum adaptation term
``CI = Ln,sum - 15 - Ln,w`` uses the energetic sum ``Ln,sum`` over
100 Hz to 2500 Hz (one-third octave) or 125 Hz to 2000 Hz (octave),
rounded to an integer (Clause A.2.1, Formulae (A.1) to (A.3)). The Table 3
reference values, the shifting rule and CI are identical in the 2013 and
2020 editions of ISO 717-2 (the 2020 edition only adds Annex D for the
rubber-ball heavy/soft impactor, out of scope here).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence, Tuple

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

# --- ISO 717-1 Table 3 reference values ----------------------------------

#: One-third-octave reference values, 100 Hz to 3150 Hz (Table 3).
_REF_THIRD_OCTAVE: Tuple[int, ...] = (
    33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56,
)
#: Octave reference values, 125 Hz to 2000 Hz (Table 3).
_REF_OCTAVE: Tuple[int, ...] = (36, 45, 52, 55, 56)

#: One-third-octave band centre frequencies, 100 Hz to 3150 Hz (16 bands).
_FREQ_THIRD_OCTAVE: Tuple[float, ...] = (
    100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0,
    630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0,
)
#: Octave band centre frequencies, 125 Hz to 2000 Hz (5 bands).
_FREQ_OCTAVE: Tuple[float, ...] = (125.0, 250.0, 500.0, 1000.0, 2000.0)

#: Index of the 500 Hz band in each band set (the rating is read there).
_INDEX_500_THIRD = 7
_INDEX_500_OCTAVE = 2

#: Maximum sum of unfavourable deviations. These bounds are shared by both
#: rating paths: ISO 717-1 Clause 4.4 (airborne) and ISO 717-2 Clause 4.3
#: (impact) specify the identical 32,0 dB (16 one-third-octave bands) and
#: 10,0 dB (5 octave bands) limits.
_MAX_UNFAVOURABLE_THIRD = 32.0
_MAX_UNFAVOURABLE_OCTAVE = 10.0

#: Tolerance absorbing floating-point noise when comparing the
#: unfavourable-deviation sum (a true multiple of 0,1 dB) to the bound.
_SHIFT_TOLERANCE = 1e-6

# --- ISO 717-2 Table 3 impact reference values ---------------------------

#: One-third-octave impact reference values, 100 Hz to 3150 Hz (Table 3).
_REF_IMPACT_THIRD_OCTAVE: Tuple[int, ...] = (
    62, 62, 62, 62, 62, 62, 61, 60, 59, 58, 57, 54, 51, 48, 45, 42,
)
#: Octave impact reference values, 125 Hz to 2000 Hz (Table 3).
_REF_IMPACT_OCTAVE: Tuple[int, ...] = (67, 67, 65, 62, 49)

#: Octave-band single-number reduction applied to L'n,w / L'nT,w
#: (ISO 717-2 Clause 4.3.2): the shifted reference at 500 Hz minus 5 dB.
_IMPACT_OCTAVE_OFFSET = -5

#: One-third-octave band count for CI (100 Hz to 2500 Hz, excludes 3150 Hz).
_CI_THIRD_OCTAVE_BANDS = 15

#: Reference absorption area A0 for the normalized level (Clause 3.14).
_A0_IMPACT = 10.0

# --- ISO 16283-3 façade sound insulation ---------------------------------

#: Reference absorption area A0 for D2m,n (Clause 3.16, dwellings).
_A0_FACADE = 10.0

#: Angle-of-incidence corrections in the apparent sound reduction index:
#: -1,5 dB for the loudspeaker method at 45° (Clause 3.12) and -3 dB for
#: the road-traffic method with all-angle incidence (Clause 3.13).
_FACADE_CORRECTION = {"loudspeaker": 1.5, "road_traffic": 3.0}

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
    :ivar band_centers: Band centre frequencies of the measured curve, in
        Hz. Defaults to ``None`` for backward-compatible construction.
    :ivar measured: The measured band quantities used for the rating (after
        the one-decimal reduction of Clause 4.4), in dB. Defaults to
        ``None``.
    :ivar shifted_reference: Table 3 reference curve after the final shift,
        in dB. Defaults to ``None``.
    """

    rating: int
    c: int
    ctr: int
    unfavourable_sum: float
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None
    shifted_reference: np.ndarray | None = None

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes:
        """Plot the measured curve vs the shifted reference (ISO 717-1).

        Unfavourable deviations (reference above measurement) are shaded and
        ``Rw (C; Ctr)`` annotated. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_weighted_rating

        return plot_weighted_rating(self, ax=ax, **kwargs)


@dataclass(frozen=True)
class ImpactInsulationResult:
    """Per-band field impact sound insulation (ISO 16283-2).

    :ivar l_n_t: Standardized impact sound pressure level
        ``L'nT = Li - 10 lg(T/T0)`` per band, in dB (Clause 3.13,
        Formula (1)).
    :ivar l_n: Normalized impact sound pressure level
        ``L'n = Li + 10 lg(A/A0)`` per band, in dB (Clause 3.14,
        Formula (2)), or ``None`` when the receiving-room volume was not
        supplied.
    """

    l_n_t: np.ndarray
    l_n: np.ndarray | None


@dataclass(frozen=True)
class ImpactRatingResult:
    """Single-number weighted impact rating and CI (ISO 717-2).

    :ivar rating: Weighted impact rating (``Ln,w``, ``L'n,w``,
        ``L'nT,w``), the shifted reference read at 500 Hz, in dB
        (Clause 4.3; octave-band ratings include the -5 dB reduction of
        Clause 4.3.2). Integer.
    :ivar ci: Spectrum adaptation term ``CI`` (Clause A.2.1), in dB.
        Integer.
    :ivar unfavourable_sum: Sum of unfavourable deviations at the final
        shift, in dB (Clause 4.3); at most 32,0 (16 bands) or 10,0 (5
        bands).
    :ivar band_centers: Band centre frequencies of the measured curve, in
        Hz. Defaults to ``None`` for backward-compatible construction.
    :ivar measured: The measured impact levels used for the rating (after
        the one-decimal reduction of Clause 4.3.1), in dB. Defaults to
        ``None``.
    :ivar shifted_reference: Table 3 impact reference curve after the final
        shift, in dB. Defaults to ``None``.
    """

    rating: int
    ci: int
    unfavourable_sum: float
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None
    shifted_reference: np.ndarray | None = None

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes:
        """Plot the measured curve vs the shifted reference (ISO 717-2).

        Unfavourable deviations (measurement above the reference, the sign
        opposite to airborne) are shaded and ``Ln,w (CI)`` annotated.
        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_impact_rating

        return plot_impact_rating(self, ax=ax, **kwargs)


@dataclass(frozen=True)
class FacadeInsulationResult:
    """Per-band field façade sound insulation (ISO 16283-3).

    :ivar d_2m: Level difference ``D2m = L1,2m - L2`` per band, in dB
        (Clause 3.14; ``Dls,2m`` loudspeaker, ``Dtr,2m`` traffic).
    :ivar d_2m_nt: Standardized level difference
        ``D2m,nT = D2m + 10 lg(T/T0)`` per band, in dB (Clause 3.15).
    :ivar d_2m_n: Normalized level difference
        ``D2m,n = D2m - 10 lg(A/A0)`` per band, in dB (Clause 3.16), or
        ``None`` when the receiving-room volume was not supplied.
    :ivar r_prime: Apparent sound reduction index ``R'45°`` (loudspeaker,
        Clause 3.12) or ``R'tr,s`` (road traffic, Clause 3.13) per band, in
        dB, or ``None`` unless a surface level
        together with the element area and receiving-room volume were
        supplied.
    :ivar frequencies: Band centre frequencies, in Hz, or ``None``.
    """

    d_2m: np.ndarray
    d_2m_nt: np.ndarray
    d_2m_n: np.ndarray | None
    r_prime: np.ndarray | None
    frequencies: np.ndarray | None = None

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes:
        """Plot the per-band façade insulation profile (ISO 16283-3).

        Draws the standardized level difference and any other available
        quantities (``D2m``, ``D2m,n``, ``R'``) against frequency. Requires
        matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_facade_insulation

        return plot_facade_insulation(self, ax=ax, **kwargs)


def _round_half_up_tenths(values: np.ndarray) -> np.ndarray:
    """Reduce levels to one decimal place (ISO 717-1 Clause 4.4, note 1).

    Rounds each value to the nearest tenth of a decibel, half away from
    zero (``floor(x*10 + 0,5)/10`` for non-negative values, mirrored for
    negative ones).
    """
    rounded: np.ndarray = np.sign(values) * np.floor(np.abs(values) * 10.0 + 0.5) / 10.0
    return rounded


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

    Measured levels are multiples of 0,1 dB (Clause 4.4 footnote 1) and the
    reference and shift are integers, so every deviation sum is a true
    multiple of 0,1 dB; a small tolerance absorbs floating-point noise so
    that a sum of exactly 32,0 (or 10,0) dB is not spuriously rejected.
    """
    # Start below any feasible shift, then climb while the bound holds.
    k = int(np.floor(np.min(measured - reference))) - 1
    while True:
        next_sum = float(np.sum(np.maximum(0.0, reference + (k + 1) - measured)))
        if next_sum > limit + _SHIFT_TOLERANCE:
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
    centers = _FREQ_THIRD_OCTAVE if data.size == 16 else _FREQ_OCTAVE
    return WeightedRatingResult(
        rating=rating,
        c=c,
        ctr=ctr,
        unfavourable_sum=unfavourable,
        band_centers=np.asarray(centers, dtype=np.float64),
        measured=measured,
        shifted_reference=ref + shift,
    )


# --- ISO 16283-2 field impact sound insulation ---------------------------


def impact_insulation(
    li: Sequence[float] | np.ndarray,
    t2: Sequence[float] | np.ndarray,
    *,
    volume: float | None = None,
    t0: float = 0.5,
) -> ImpactInsulationResult:
    """
    Field impact sound insulation per ISO 16283-2 (tapping machine).

    Computes, per frequency band, the standardized impact sound pressure
    level ``L'nT = Li - 10 lg(T/T0)`` (Formula (1)) and, when the
    receiving-room volume is given, the normalized impact sound pressure
    level ``L'n = Li + 10 lg(A/A0)`` with the Sabine equivalent absorption
    area ``A = 0,16 V / T`` (Formula (6)) and the reference absorption area
    ``A0 = 10 m²`` (Formula (2)).

    ``li`` may be one value per band (already energy-averaged) or a
    two-dimensional ``(positions, bands)`` array, in which case the
    positions are energy-averaged with Formula (10). The band levels are
    assumed already corrected for background noise (Clause 9).

    :param li: Energy-average impact sound pressure levels, in dB.
    :param t2: Receiving-room reverberation time per band, in seconds.
    :param volume: Receiving-room volume ``V``, in m³ (optional; required
        for ``L'n``).
    :param t0: Reference reverberation time ``T0``, in seconds (default
        0,5 s for dwellings, Clause 3.13).
    :return: :class:`ImpactInsulationResult` with ``l_n_t`` and ``l_n``
        (the latter ``None`` unless ``volume`` is given).
    :raises ValueError: If the band counts of ``li`` and ``t2`` differ, if
        ``t2``/``t0``/``volume`` are not positive, or if inputs are
        non-finite.
    """
    li_bands = _as_band_levels(li, "li")
    t = np.asarray(t2, dtype=np.float64)

    if li_bands.shape != t.shape:
        raise ValueError("'li' and 't2' must share the same band count.")
    if t.ndim != 1:
        raise ValueError("'t2' must be one-dimensional (one value per band).")
    if not np.all(np.isfinite(t)) or np.any(t <= 0.0):
        raise ValueError("'t2' must contain positive, finite values.")
    if t0 <= 0.0:
        raise ValueError("'t0' must be positive.")

    l_n_t = li_bands - 10.0 * np.log10(t / t0)

    l_n: np.ndarray | None = None
    if volume is not None:
        if volume <= 0.0:
            raise ValueError("'volume' must be positive.")
        absorption = 0.16 * volume / t
        l_n = li_bands + 10.0 * np.log10(absorption / _A0_IMPACT)

    return ImpactInsulationResult(l_n_t=l_n_t, l_n=l_n)


def facade_insulation(
    l1_2m: Sequence[float] | np.ndarray,
    l2: Sequence[float] | np.ndarray,
    t2: Sequence[float] | np.ndarray,
    *,
    area: float | None = None,
    volume: float | None = None,
    surface_level: Sequence[float] | np.ndarray | None = None,
    method: str = "loudspeaker",
    t0: float = 0.5,
    frequencies: Sequence[float] | np.ndarray | None = None,
) -> FacadeInsulationResult:
    """
    Field façade sound insulation per ISO 16283-3:2016.

    Computes, per frequency band, the global-method level difference
    ``D2m = L1,2m - L2`` (Clause 3.14), its standardized form
    ``D2m,nT = D2m + 10 lg(T/T0)`` (Clause 3.15) and, when the
    receiving-room volume is given, its normalized form
    ``D2m,n = D2m - 10 lg(A/A0)`` with the Sabine equivalent absorption
    area ``A = 0,16 V/T`` (Clause 3.17) and ``A0 = 10 m²`` (Clause 3.16).
    When a surface level ``L1,s`` (microphone on the test element),
    together with the element area ``S`` and the volume, is supplied it
    also computes the apparent sound reduction index of the element
    method: ``R'45° = L1,s - L2 + 10 lg(S/A) - 1,5`` for a loudspeaker
    source (Clause 3.12) or ``R'tr,s = L1,s - L2 + 10 lg(S/A) - 3`` for a
    road-traffic source (Clause 3.13). The defining formulas are unnumbered
    inline in the Clause 3 terms.

    ``l1_2m``, ``l2`` and ``surface_level`` may be one value per band
    (already energy-averaged) or a two-dimensional ``(positions, bands)``
    array, in which case the positions are energy-averaged with the
    surface-level formula (Clause 9.5.1, Formula (7)). Band levels are
    assumed already corrected for background
    noise. The single-number rating uses the ISO 717-1 airborne reference
    curve (Annex F); pass the desired 16-band quantity to
    :func:`weighted_rating`.

    :param l1_2m: Outdoor sound pressure levels 2 m in front of the façade,
        in dB.
    :param l2: Receiving-room sound pressure levels, in dB.
    :param t2: Receiving-room reverberation time per band, in seconds.
    :param area: Area ``S`` of the test element, in m² (optional; required
        with ``volume`` and ``surface_level`` for ``R'``).
    :param volume: Receiving-room volume ``V``, in m³ (optional; required
        for ``D2m,n`` and for ``R'``).
    :param surface_level: Outdoor surface level ``L1,s`` on the test
        element, in dB (optional; required with ``area`` and ``volume`` for
        ``R'``).
    :param method: ``"loudspeaker"`` (45° incidence, -1,5 dB) or
        ``"road_traffic"`` (all-angle incidence, -3 dB); selects the ``R'``
        correction (Clause 3.12 / 3.13).
    :param t0: Reference reverberation time ``T0``, in seconds (default
        0,5 s for dwellings, Clause 3.15).
    :param frequencies: Optional band centre frequencies, in Hz, carried
        on the result for plotting.
    :return: :class:`FacadeInsulationResult` with ``d_2m``, ``d_2m_nt``,
        ``d_2m_n`` (``None`` unless ``volume`` is given) and ``r_prime``
        (``None`` unless ``surface_level``, ``area`` and ``volume`` are all
        given).
    :raises ValueError: If band counts differ, if ``method`` is unknown, if
        ``t2``/``t0``/``area``/``volume`` are not positive, if ``area`` is
        given without ``surface_level``, if ``surface_level`` and ``area`` are
        given without ``volume``, if ``frequencies`` is given with a length
        that differs from the band count, or if inputs are non-finite.
        Supplying ``surface_level`` alone is not an error: ``r_prime`` simply
        stays ``None``.
    """
    if method not in _FACADE_CORRECTION:
        raise ValueError(
            "'method' must be 'loudspeaker' or 'road_traffic', got "
            f"{method!r}."
        )

    l1_bands = _as_band_levels(l1_2m, "l1_2m")
    l2_bands = _as_band_levels(l2, "l2")
    t = np.asarray(t2, dtype=np.float64)

    if not (l1_bands.shape == l2_bands.shape == t.shape):
        raise ValueError(
            "'l1_2m', 'l2' and 't2' must share the same band count."
        )
    if t.ndim != 1:
        raise ValueError("'t2' must be one-dimensional (one value per band).")
    if not np.all(np.isfinite(t)) or np.any(t <= 0.0):
        raise ValueError("'t2' must contain positive, finite values.")
    if t0 <= 0.0:
        raise ValueError("'t0' must be positive.")

    d_2m = l1_bands - l2_bands
    d_2m_nt = d_2m + 10.0 * np.log10(t / t0)

    if volume is not None and volume <= 0.0:
        raise ValueError("'volume' must be positive.")
    if area is not None and area <= 0.0:
        raise ValueError("'area' must be positive.")
    if area is not None and surface_level is None:
        raise ValueError(
            "'area' requires 'surface_level' to compute the apparent sound "
            "reduction index R'."
        )
    if surface_level is not None and area is not None and volume is None:
        raise ValueError(
            "'volume' is required with 'surface_level' and 'area' to compute "
            "the apparent sound reduction index R'."
        )

    # Sabine equivalent absorption area A = 0,16 V / T (Clause 3.17).
    absorption = 0.16 * volume / t if volume is not None else None

    d_2m_n: np.ndarray | None = None
    if absorption is not None:
        d_2m_n = d_2m - 10.0 * np.log10(absorption / _A0_FACADE)

    r_prime: np.ndarray | None = None
    if surface_level is not None and area is not None and absorption is not None:
        surf_bands = _as_band_levels(surface_level, "surface_level")
        if surf_bands.shape != l2_bands.shape:
            raise ValueError(
                "'surface_level' must share the band count of 'l2'."
            )
        r_prime = (
            surf_bands
            - l2_bands
            + 10.0 * np.log10(area / absorption)
            - _FACADE_CORRECTION[method]
        )

    freqs = (
        np.asarray(frequencies, dtype=np.float64)
        if frequencies is not None
        else None
    )
    if freqs is not None and freqs.shape != d_2m.shape:
        raise ValueError(
            "'frequencies' must have one value per band; got "
            f"{freqs.size} for {d_2m.size} bands."
        )
    return FacadeInsulationResult(
        d_2m=d_2m,
        d_2m_nt=d_2m_nt,
        d_2m_n=d_2m_n,
        r_prime=r_prime,
        frequencies=freqs,
    )


def _resolve_impact_band_set(
    n: int, bands: str | None
) -> Tuple[Tuple[int, ...], float, int, int, int]:
    """Select the impact reference curve, bound, indices for the band set.

    :return: ``(reference, max_unfavourable, index_500, octave_offset,
        ci_band_count)``.
    """
    if bands == "third-octave" or (bands is None and n == 16):
        if n != 16:
            raise ValueError(
                "One-third-octave impact rating needs 16 bands "
                f"(100-3150 Hz), got {n}."
            )
        return (
            _REF_IMPACT_THIRD_OCTAVE,
            _MAX_UNFAVOURABLE_THIRD,
            _INDEX_500_THIRD,
            0,
            _CI_THIRD_OCTAVE_BANDS,
        )
    if bands == "octave" or (bands is None and n == 5):
        if n != 5:
            raise ValueError(
                "Octave impact rating needs 5 bands (125-2000 Hz), "
                f"got {n}."
            )
        return (
            _REF_IMPACT_OCTAVE,
            _MAX_UNFAVOURABLE_OCTAVE,
            _INDEX_500_OCTAVE,
            _IMPACT_OCTAVE_OFFSET,
            5,
        )
    if bands is not None:
        raise ValueError("'bands' must be 'third-octave', 'octave' or None.")
    raise ValueError(
        "Expected 16 one-third-octave (100-3150 Hz) or 5 octave "
        f"(125-2000 Hz) values, got {n}."
    )


def _impact_ci(measured: np.ndarray, rating: int, n_bands: int) -> int:
    """Spectrum adaptation term ``CI`` (ISO 717-2 Clause A.2.1).

    ``CI = Ln,sum - 15 - Ln,w`` with the energetic sum ``Ln,sum = 10 lg
    Σ 10^(Li/10)`` over the CI range (one-third octave 100-2500 Hz, i.e.
    the first 15 bands; octave 125-2000 Hz), rounded to an integer
    (round half up), Formulae (A.1) to (A.3).
    """
    l_sum = 10.0 * np.log10(np.sum(10.0 ** (measured[:n_bands] / 10.0)))
    return int(math.floor(l_sum + 0.5)) - 15 - rating


def weighted_impact_rating(
    values_by_band: Sequence[float] | np.ndarray,
    bands: str | None = None,
) -> ImpactRatingResult:
    """
    Single-number weighted impact rating and CI per ISO 717-2.

    Applies the reference-curve method of Clause 4.3: the Table 3 impact
    reference curve is shifted in 1 dB steps towards the measured curve
    until the sum of unfavourable deviations is as large as possible but
    not more than 32,0 dB (16 one-third-octave bands, 100 Hz to 3150 Hz)
    or 10,0 dB (5 octave bands, 125 Hz to 2000 Hz). For impact sound an
    unfavourable deviation occurs where the **measurement exceeds** the
    reference (the sign opposite to ISO 717-1 airborne). The rating is the
    shifted reference read at 500 Hz; for octave bands it is then reduced
    by 5 dB (Clause 4.3.2). The spectrum adaptation term ``CI`` follows
    Clause A.2.1. Input values are first reduced to one decimal place
    (Clause 4.3.1, footnote 1).

    The shift search reuses the verified engine of :func:`weighted_rating`
    on the negated curves: minimising ``Σ max(0, measured - (ref + k))``
    over ``k`` equals maximising ``Σ max(0, (-ref) + (-k) - (-measured))``,
    the airborne problem, so no separate search is duplicated.

    :param values_by_band: Measured impact levels (``Ln``, ``L'n``,
        ``L'nT``) in dB. 16 values are read as one-third-octave bands, 5
        values as octave bands.
    :param bands: ``"third-octave"``, ``"octave"`` or ``None`` to infer
        the band set from the number of values.
    :return: :class:`ImpactRatingResult` with ``rating``, ``ci`` and
        ``unfavourable_sum``.
    :raises ValueError: If the number of values does not match the band
        set, or if any value is non-finite.
    """
    data = np.asarray(values_by_band, dtype=np.float64)
    if data.ndim != 1:
        raise ValueError("'values_by_band' must be one-dimensional.")
    if not np.all(np.isfinite(data)):
        raise ValueError("'values_by_band' must contain only finite values.")

    reference, limit, index_500, octave_offset, ci_bands = (
        _resolve_impact_band_set(int(data.size), bands)
    )
    measured = _round_half_up_tenths(data)
    ref = np.asarray(reference, dtype=np.float64)

    # Impact shift is the airborne search on the negated curves: the
    # returned shift m maximises Σ max(0, (-ref)+m-(-meas)); the impact
    # shift is k = -m, so the rating is ref_500 - m. The unfavourable sum
    # is identical under negation.
    shift, unfavourable = _best_shift(-measured, -ref, limit)
    rating = int(reference[index_500]) - shift + octave_offset
    ci = _impact_ci(measured, rating, ci_bands)
    centers = _FREQ_THIRD_OCTAVE if data.size == 16 else _FREQ_OCTAVE
    return ImpactRatingResult(
        rating=rating,
        ci=ci,
        unfavourable_sum=unfavourable,
        band_centers=np.asarray(centers, dtype=np.float64),
        measured=measured,
        shifted_reference=ref - shift,
    )
