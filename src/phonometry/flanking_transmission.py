#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Laboratory measurement of flanking sound transmission (ISO 10848:2006/2010).

This is the **measurement** counterpart of the flanking-transmission
*prediction* in :mod:`phonometry.building_prediction`. EN 12354-1 predicts the
apparent in-situ performance from, among other inputs, the **vibration
reduction index** ``Kij`` of each junction; ISO 10848 is the standard that
*measures* that ``Kij`` (and the overall flanking descriptors ``Dn,f`` /
``Ln,f``) in a qualified test facility. The measured ``Kij`` is a
situation-invariant junction descriptor that feeds straight into the
:func:`phonometry.flanking_path` model.

**Vibration reduction index (Part 1, Clause 3.9).** From the *direction
averaged* velocity level difference ``D̄v,ij = ½(Dv,ij + Dv,ji)`` (Formula (11))
this module forms, per one-third-octave band,
``Kij = D̄v,ij + 10 lg( lij / √(ai·aj) )`` (Formula (13)) with the common-edge
junction length ``lij`` and the equivalent absorption lengths ``ai``, ``aj`` of
the two elements. For lightweight, well-damped elements the equivalent
absorption length collapses to the element area (``aj = Sj / l0``, ``l0 = 1 m``,
Clause 3.8 Note 3) and Formula (13) reduces to Formula (14),
``Kij = D̄v,ij + 10 lg( lij / √(Si·Sj) )``. Because it uses the direction average,
``Kij`` is symmetric (``Kij = Kji``).

**Equivalent absorption length (Part 1, Formula (12)).**
``aj = (2,2 · π² · Sj) / (Ts,j · c0) · √(f_ref / f)`` with the structural
reverberation time ``Ts,j``, the element area ``Sj``, the speed of sound in air
``c0`` and the reference frequency ``f_ref = 1000 Hz``. The related total loss
factor is ``η = 2,2 / (f · Ts)`` (Clause 7.3.1).

**Overall flanking descriptors (Part 1, Clauses 3.2/3.3).** With airborne
excitation the normalized flanking level difference is
``Dn,f = L1 − L2 − 10 lg(A/A0)`` (Formula (4)); with a tapping machine on the
source-room floor the normalized flanking impact level is
``Ln,f = L2 + 10 lg(A/A0)`` (Formula (5)), both with the reference absorption
area ``A0 = 10 m²``. Their single-number ratings ``Dn,f,w (C; Ctr)`` and
``Ln,f,w (CI)`` follow ISO 717-1/-2 through the verified
:func:`phonometry.weighted_rating` / :func:`phonometry.weighted_impact_rating`
engines, reused unchanged.

**Validity of Kij.** ``Kij`` rests on a statistical-energy-analysis
simplification (weak coupling, diffuse vibration fields). This module exposes
the standard's own applicability checks: the strong-coupling inequality
(Formula (15)), and — for heavy junctions (Part 4) — the modal density,
in-band mode count and modal overlap factor (Formulas (5), (4), (6)) whose
thresholds bracket or exclude unreliable bands.

**c0 note.** ISO 10848 writes ``c0`` only as "the speed of sound in air" and
gives no number. This module defaults to ``343 m/s`` (20 °C) and exposes it as
a parameter so a facility can pin its own value.

**Frequency range (Part 1, Clause 7.5).** The mandatory one-third-octave range
is 100 Hz to 5000 Hz (18 bands). The single-number ``Kij`` is the arithmetic
mean over 200 Hz to 1250 Hz (Annex A); the automatic mean is formed only when
that band set is present in the supplied frequencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence

import numpy as np

from .insulation import (
    ImpactRatingResult,
    WeightedRatingResult,
    weighted_impact_rating,
    weighted_rating,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

#: Reference equivalent sound absorption area ``A0`` for the normalized
#: flanking descriptors (ISO 10848-1:2006, Clauses 3.2/3.3): 10 m².
_REFERENCE_ABSORPTION_AREA = 10.0

#: Reference frequency ``f_ref`` in the equivalent absorption length
#: (ISO 10848-1:2006, Formula (12)): 1000 Hz (assumed critical frequency).
_REFERENCE_FREQUENCY = 1000.0

#: Reference coupling length ``l0`` (ISO 10848-1:2006, Clause 3.8 Note 3): 1 m.
_REFERENCE_LENGTH = 1.0

#: Constant ``2,2`` shared by the equivalent absorption length (Formula (12)),
#: the total loss factor ``η = 2,2/(f·Ts)`` and the modal overlap factor
#: (Part 4, Formula (6)).
_STRUCTURAL_CONSTANT = 2.2

#: ``2,2 · π²`` prefactor of the equivalent absorption length (Formula (12)).
_ABSORPTION_LENGTH_CONSTANT = _STRUCTURAL_CONSTANT * np.pi**2

#: Default speed of sound in air, in m/s (20 °C). ISO 10848 gives no value.
_DEFAULT_SPEED_OF_SOUND = 343.0

#: Constant ``1,8`` in the thin-plate critical frequency (Part 1, Formula (20)).
_CRITICAL_FREQUENCY_CONSTANT = 1.8

#: One-third-octave band range of the single-number ``Kij`` (Annex A): the
#: arithmetic mean is taken over 200 Hz to 1250 Hz inclusive.
_SINGLE_NUMBER_LOW = 200.0
_SINGLE_NUMBER_HIGH = 1250.0


def _as_1d(values: float | Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    """Coerce to a finite 1-D float array."""
    data = np.atleast_1d(np.asarray(values, dtype=np.float64))
    if data.ndim != 1:
        raise ValueError(f"'{name}' must be one-dimensional (one value per band).")
    if data.size == 0:
        raise ValueError(f"'{name}' must not be empty.")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"'{name}' must contain only finite values.")
    return data


def _positive(value: float, name: str) -> float:
    """Validate a positive, finite scalar."""
    scalar = float(value)
    if not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"'{name}' must be a positive, finite number.")
    return scalar


def _positive_array(
    values: float | Sequence[float] | np.ndarray, name: str
) -> np.ndarray:
    """Validate a 1-D array of positive, finite values."""
    data = _as_1d(values, name)
    if np.any(data <= 0.0):
        raise ValueError(f"'{name}' must contain positive values.")
    return data


# --------------------------------------------------------------------------- #
# Velocity level differences (Part 1, Clauses 3.6/3.7)
# --------------------------------------------------------------------------- #
def velocity_level_difference(
    source_level: Sequence[float] | np.ndarray,
    receive_level: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Velocity level difference ``Dv,ij = Lv,i − Lv,j`` (Formula (8)).

    :param source_level: Average velocity level ``Lv,i`` of the excited
        element, in dB, per band.
    :param receive_level: Average velocity level ``Lv,j`` of the receiving
        element, in dB, per band.
    :return: ``Dv,ij`` per band, in dB.
    :raises ValueError: If the inputs are empty, non-finite, or differ in
        length.
    """
    lv_i = _as_1d(source_level, "source_level")
    lv_j = _as_1d(receive_level, "receive_level")
    if lv_i.size != lv_j.size:
        raise ValueError("'source_level' and 'receive_level' must share their length.")
    return np.asarray(lv_i - lv_j, dtype=np.float64)


def direction_averaged_level_difference(
    dv_ij: Sequence[float] | np.ndarray,
    dv_ji: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Direction-averaged velocity level difference (Formula (11)).

    ``D̄v,ij = ½ (Dv,ij + Dv,ji)`` with ``Dv,ij`` measured exciting element
    ``i`` and ``Dv,ji`` exciting element ``j``. The average makes the derived
    ``Kij`` symmetric.

    :param dv_ij: ``Dv,ij`` (element ``i`` excited), in dB, per band.
    :param dv_ji: ``Dv,ji`` (element ``j`` excited), in dB, per band.
    :return: ``D̄v,ij`` per band, in dB.
    :raises ValueError: If the inputs are empty, non-finite, or differ in
        length.
    """
    a = _as_1d(dv_ij, "dv_ij")
    b = _as_1d(dv_ji, "dv_ji")
    if a.size != b.size:
        raise ValueError("'dv_ij' and 'dv_ji' must share their length.")
    return np.asarray(0.5 * (a + b), dtype=np.float64)


# --------------------------------------------------------------------------- #
# Structural quantities (Part 1, Clauses 3.5/3.8)
# --------------------------------------------------------------------------- #
def total_loss_factor(
    frequency: Sequence[float] | np.ndarray,
    structural_reverberation_time: float | Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Total loss factor ``η = 2,2 / (f · Ts)`` (Clause 7.3.1).

    :param frequency: Band centre frequency ``f``, in Hz, per band.
    :param structural_reverberation_time: Structural reverberation time
        ``Ts``, in s, per band (or a single value broadcast to all bands).
    :return: Total loss factor ``η`` (dimensionless) per band.
    :raises ValueError: If the inputs are not positive/finite or their band
        counts are incompatible.
    """
    f = _positive_array(frequency, "frequency")
    ts = _positive_array(structural_reverberation_time, "structural_reverberation_time")
    ts = _broadcast(ts, f.size, "structural_reverberation_time")
    return np.asarray(_STRUCTURAL_CONSTANT / (f * ts), dtype=np.float64)


def equivalent_absorption_length(
    area: float,
    structural_reverberation_time: float | Sequence[float] | np.ndarray,
    frequency: Sequence[float] | np.ndarray,
    *,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray:
    """Equivalent absorption length ``aj`` (Formula (12)).

    ``aj = (2,2 · π² · Sj) / (Ts,j · c0) · √(f_ref / f)`` with
    ``f_ref = 1000 Hz``.

    :param area: Element surface area ``Sj``, in m².
    :param structural_reverberation_time: Structural reverberation time
        ``Ts,j``, in s, per band (or a single value broadcast to all bands).
    :param frequency: Band centre frequency ``f``, in Hz, per band.
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s
        (default 343 m/s).
    :return: Equivalent absorption length ``aj``, in m, per band.
    :raises ValueError: If any input is not positive/finite or the band counts
        are incompatible.
    """
    s = _positive(area, "area")
    c0 = _positive(speed_of_sound, "speed_of_sound")
    f = _positive_array(frequency, "frequency")
    ts = _positive_array(structural_reverberation_time, "structural_reverberation_time")
    ts = _broadcast(ts, f.size, "structural_reverberation_time")
    return _ABSORPTION_LENGTH_CONSTANT * s / (ts * c0) * np.sqrt(_REFERENCE_FREQUENCY / f)


def _broadcast(values: np.ndarray, n_bands: int, name: str) -> np.ndarray:
    """Broadcast a scalar-per-band array to ``n_bands``, or validate the count."""
    if values.size == 1:
        return np.full(n_bands, values[0], dtype=np.float64)
    if values.size != n_bands:
        raise ValueError(f"'{name}' must have one value per band (or a single value).")
    return values


# --------------------------------------------------------------------------- #
# Vibration reduction index (Part 1, Clause 3.9)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class VibrationReductionResult:
    """Per-band vibration reduction index ``Kij`` (ISO 10848-1:2006).

    :ivar frequencies: Band centre frequencies, in Hz, or ``None`` when they
        were not supplied.
    :ivar k_ij: Vibration reduction index ``Kij`` per band, in dB (Formula (13)
        or the simplified Formula (14)).
    :ivar single_number: Arithmetic-mean single-number ``K̄ij`` over
        200 Hz to 1250 Hz (Annex A), in dB, or ``None`` when the frequencies do
        not cover that band set.
    """

    frequencies: np.ndarray | None
    k_ij: np.ndarray
    single_number: float | None

    def octave_bands(self) -> "VibrationReductionResult":
        """Combine one-third-octave ``Kij`` into octave bands.

        ``Kij,oct = −10 lg[ (1/3) Σ 10^(−Kij/10) ]`` over each group of three
        one-third-octave bands (Part 2/3/4). Requires a band count that is a
        multiple of three and, for the frequency labels, that frequencies were
        supplied.

        :return: A new :class:`VibrationReductionResult` on octave centres.
        :raises ValueError: If the band count is not a multiple of three.
        """
        if self.k_ij.size % 3 != 0:
            raise ValueError(
                "octave_bands() needs a band count that is a multiple of three."
            )
        groups = self.k_ij.reshape(-1, 3)
        oct_k = -10.0 * np.log10(np.mean(10.0 ** (-groups / 10.0), axis=1))
        oct_f: np.ndarray | None = None
        if self.frequencies is not None:
            oct_f = self.frequencies.reshape(-1, 3)[:, 1]
        return VibrationReductionResult(
            frequencies=oct_f,
            k_ij=oct_k,
            single_number=_single_number_kij(oct_f, oct_k),
        )

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot ``Kij`` against frequency.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_vibration_reduction

        return plot_vibration_reduction(self, ax=ax, **kwargs)


def _single_number_kij(
    frequencies: np.ndarray | None, k_ij: np.ndarray
) -> float | None:
    """Arithmetic-mean ``K̄ij`` over 200-1250 Hz (Annex A), or ``None``."""
    if frequencies is None:
        return None
    mask = (frequencies >= _SINGLE_NUMBER_LOW) & (frequencies <= _SINGLE_NUMBER_HIGH)
    if not np.any(mask):
        return None
    return float(np.mean(k_ij[mask]))


def vibration_reduction_index(
    velocity_level_difference: Sequence[float] | np.ndarray,
    junction_length: float,
    area_i: float,
    area_j: float,
    *,
    frequency: Sequence[float] | np.ndarray | None = None,
    structural_reverberation_time_i: float | Sequence[float] | np.ndarray | None = None,
    structural_reverberation_time_j: float | Sequence[float] | np.ndarray | None = None,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> VibrationReductionResult:
    """Vibration reduction index ``Kij`` (Formula (13), or simplified (14)).

    ``Kij = D̄v,ij + 10 lg( lij / √(ai·aj) )``. When the structural reverberation
    times and the frequencies are supplied, the equivalent absorption lengths
    ``ai``, ``aj`` come from Formula (12) and the full Formula (13) is used.
    Otherwise the lightweight, well-damped simplification ``aj = Sj / l0``
    (``l0 = 1 m``) applies and Formula (14),
    ``Kij = D̄v,ij + 10 lg( lij / √(Si·Sj) )``, is used.

    :param velocity_level_difference: Direction-averaged velocity level
        difference ``D̄v,ij`` (see :func:`direction_averaged_level_difference`),
        in dB, per band.
    :param junction_length: Common-edge junction length ``lij``, in m.
    :param area_i: Area ``Si`` of element ``i``, in m².
    :param area_j: Area ``Sj`` of element ``j``, in m².
    :param frequency: Band centre frequencies, in Hz. Required for Formula (12)
        and for the single-number mean; optional for the simplified form.
    :param structural_reverberation_time_i: ``Ts,i`` per band (or a single
        value), in s. Supply together with ``structural_reverberation_time_j``
        and ``frequency`` to use Formula (12); omit for the simplified form.
    :param structural_reverberation_time_j: ``Ts,j`` per band (or a single
        value), in s.
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s.
    :return: A :class:`VibrationReductionResult`.
    :raises ValueError: On incompatible band counts, non-positive geometry, or
        if only one of the two structural reverberation times is supplied.
    """
    dv = _as_1d(velocity_level_difference, "velocity_level_difference")
    lij = _positive(junction_length, "junction_length")
    s_i = _positive(area_i, "area_i")
    s_j = _positive(area_j, "area_j")

    freq = None if frequency is None else _positive_array(frequency, "frequency")
    if freq is not None and freq.size != dv.size:
        raise ValueError("'frequency' must share the band count of the level input.")

    ts_given = (structural_reverberation_time_i is not None) + (
        structural_reverberation_time_j is not None
    )
    if ts_given == 1:
        raise ValueError(
            "Supply both structural reverberation times (i and j) or neither."
        )

    if ts_given == 2:
        if freq is None:
            raise ValueError(
                "'frequency' is required when structural reverberation times are "
                "supplied (Formula (12))."
            )
        a_i = equivalent_absorption_length(
            s_i, structural_reverberation_time_i, freq, speed_of_sound=speed_of_sound  # type: ignore[arg-type]
        )
        a_j = equivalent_absorption_length(
            s_j, structural_reverberation_time_j, freq, speed_of_sound=speed_of_sound  # type: ignore[arg-type]
        )
    else:
        a_i = np.full(dv.size, s_i / _REFERENCE_LENGTH, dtype=np.float64)
        a_j = np.full(dv.size, s_j / _REFERENCE_LENGTH, dtype=np.float64)

    k_ij = dv + 10.0 * np.log10(lij / np.sqrt(a_i * a_j))
    return VibrationReductionResult(
        frequencies=freq,
        k_ij=k_ij,
        single_number=_single_number_kij(freq, k_ij),
    )


def vibration_reduction_index_from_flanking(
    normalized_flanking_level_difference: Sequence[float] | np.ndarray,
    reduction_index_i: Sequence[float] | np.ndarray,
    reduction_index_j: Sequence[float] | np.ndarray,
    junction_length: float,
    area_i: float,
    area_j: float,
    absorption_length_i: Sequence[float] | np.ndarray,
    absorption_length_j: Sequence[float] | np.ndarray,
    *,
    reference_area: float = _REFERENCE_ABSORPTION_AREA,
) -> np.ndarray:
    """Indirect ``Kij`` from the normalized flanking level difference.

    ISO 10848-1:2006, Clause 4.3.1 Note 2 (unnumbered)::

        Kij = Dn,f − (Ri + Rj)/2 − 10 lg(√(ai·aj)/lij) + 10 lg(√(Si·Sj)/A0)

    The standard warns this holds only for resonant-only transmission; measured
    ``R`` also includes forced transmission, so a direct measurement of ``Kij``
    (Formula (13)) is preferred. Provided for completeness.

    :param normalized_flanking_level_difference: ``Dn,f`` per band, in dB.
    :param reduction_index_i: Sound reduction index ``Ri`` per band, in dB.
    :param reduction_index_j: Sound reduction index ``Rj`` per band, in dB.
    :param junction_length: ``lij``, in m.
    :param area_i: ``Si``, in m².
    :param area_j: ``Sj``, in m².
    :param absorption_length_i: ``ai`` per band, in m.
    :param absorption_length_j: ``aj`` per band, in m.
    :param reference_area: ``A0``, in m² (default 10 m²).
    :return: ``Kij`` per band, in dB.
    :raises ValueError: On incompatible band counts or non-positive geometry.
    """
    dn_f = _as_1d(normalized_flanking_level_difference, "normalized_flanking_level_difference")
    r_i = _as_1d(reduction_index_i, "reduction_index_i")
    r_j = _as_1d(reduction_index_j, "reduction_index_j")
    a_i = _positive_array(absorption_length_i, "absorption_length_i")
    a_j = _positive_array(absorption_length_j, "absorption_length_j")
    lij = _positive(junction_length, "junction_length")
    s_i = _positive(area_i, "area_i")
    s_j = _positive(area_j, "area_j")
    a0 = _positive(reference_area, "reference_area")
    sizes = {dn_f.size, r_i.size, r_j.size, a_i.size, a_j.size}
    if len(sizes) != 1:
        raise ValueError("All per-band inputs must share the same length.")
    k_ij = (
        dn_f
        - 0.5 * (r_i + r_j)
        - 10.0 * np.log10(np.sqrt(a_i * a_j) / lij)
        + 10.0 * np.log10(np.sqrt(s_i * s_j) / a0)
    )
    return np.asarray(k_ij, dtype=np.float64)


# --------------------------------------------------------------------------- #
# Overall flanking descriptors (Part 1, Clauses 3.2/3.3)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FlankingLevelDifferenceResult:
    """Normalized flanking level difference ``Dn,f`` (airborne, Formula (4)).

    :ivar d_n_f: ``Dn,f = L1 − L2 − 10 lg(A/A0)`` per band, in dB.
    :ivar rating: Single-number ``Dn,f,w`` with ``C``/``Ctr`` (ISO 717-1), or
        ``None`` when the band count is neither 16 nor 5.
    """

    d_n_f: np.ndarray
    rating: WeightedRatingResult | None

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot ``Dn,f`` against the shifted ISO 717-1 reference curve."""
        if self.rating is None:
            raise ValueError(
                "No single-number rating is available to plot (need 16 "
                "one-third-octave or 5 octave bands)."
            )
        return self.rating.plot(ax=ax, **kwargs)


@dataclass(frozen=True)
class FlankingImpactLevelResult:
    """Normalized flanking impact level ``Ln,f`` (Formula (5)).

    :ivar l_n_f: ``Ln,f = L2 + 10 lg(A/A0)`` per band, in dB.
    :ivar rating: Single-number ``Ln,f,w`` with ``CI`` (ISO 717-2), or ``None``
        when the band count is neither 16 nor 5.
    """

    l_n_f: np.ndarray
    rating: ImpactRatingResult | None

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot ``Ln,f`` against the shifted ISO 717-2 reference curve."""
        if self.rating is None:
            raise ValueError(
                "No single-number rating is available to plot (need 16 "
                "one-third-octave or 5 octave bands)."
            )
        return self.rating.plot(ax=ax, **kwargs)


def normalized_flanking_level_difference(
    source_level: Sequence[float] | np.ndarray,
    receive_level: Sequence[float] | np.ndarray,
    absorption_area: Sequence[float] | np.ndarray,
    *,
    reference_area: float = _REFERENCE_ABSORPTION_AREA,
    bands: str | None = None,
) -> FlankingLevelDifferenceResult:
    """Normalized flanking level difference ``Dn,f`` (airborne, Formula (4)).

    ``Dn,f = L1 − L2 − 10 lg(A/A0)`` with the reference absorption area
    ``A0 = 10 m²``.

    :param source_level: Source-room average SPL ``L1`` per band, in dB.
    :param receive_level: Receiving-room average SPL ``L2`` per band, in dB.
    :param absorption_area: Receiving-room equivalent absorption area ``A`` per
        band, in m².
    :param reference_area: ``A0``, in m² (default 10 m²).
    :param bands: Band spacing passed to :func:`phonometry.weighted_rating`;
        auto-detected when ``None``.
    :return: A :class:`FlankingLevelDifferenceResult`; the single-number
        rating is formed only for 16 (one-third-octave) or 5 (octave) bands.
    :raises ValueError: On incompatible band counts or non-positive areas.
    """
    l1 = _as_1d(source_level, "source_level")
    l2 = _as_1d(receive_level, "receive_level")
    area = _positive_array(absorption_area, "absorption_area")
    a0 = _positive(reference_area, "reference_area")
    if not (l1.size == l2.size == area.size):
        raise ValueError("'source_level', 'receive_level' and 'absorption_area' must share their length.")
    d_n_f = l1 - l2 - 10.0 * np.log10(area / a0)
    rating = _maybe_rating(d_n_f, bands)
    return FlankingLevelDifferenceResult(d_n_f=d_n_f, rating=rating)


def normalized_flanking_impact_level(
    receive_level: Sequence[float] | np.ndarray,
    absorption_area: Sequence[float] | np.ndarray,
    *,
    reference_area: float = _REFERENCE_ABSORPTION_AREA,
    bands: str | None = None,
) -> FlankingImpactLevelResult:
    """Normalized flanking impact level ``Ln,f`` (Formula (5)).

    ``Ln,f = L2 + 10 lg(A/A0)`` with the reference absorption area
    ``A0 = 10 m²``, from the receiving-room impact level with the tapping
    machine on the source-room floor.

    :param receive_level: Receiving-room average impact SPL ``L2`` per band,
        in dB.
    :param absorption_area: Receiving-room equivalent absorption area ``A`` per
        band, in m².
    :param reference_area: ``A0``, in m² (default 10 m²).
    :param bands: Band spacing passed to
        :func:`phonometry.weighted_impact_rating`; auto-detected when ``None``.
    :return: A :class:`FlankingImpactLevelResult`; the single-number rating is
        formed only for 16 (one-third-octave) or 5 (octave) bands.
    :raises ValueError: On incompatible band counts or non-positive areas.
    """
    l2 = _as_1d(receive_level, "receive_level")
    area = _positive_array(absorption_area, "absorption_area")
    a0 = _positive(reference_area, "reference_area")
    if l2.size != area.size:
        raise ValueError("'receive_level' and 'absorption_area' must share their length.")
    l_n_f = l2 + 10.0 * np.log10(area / a0)
    rating: ImpactRatingResult | None = None
    if l_n_f.size in (16, 5):
        rating = weighted_impact_rating(l_n_f, bands)
    return FlankingImpactLevelResult(l_n_f=l_n_f, rating=rating)


def _maybe_rating(
    values: np.ndarray, bands: str | None
) -> WeightedRatingResult | None:
    """Form the ISO 717-1 rating when the band count is 16 or 5, else ``None``."""
    if values.size in (16, 5):
        return weighted_rating(values, bands)
    return None


# --------------------------------------------------------------------------- #
# Validity criteria (Part 1 Formulas (15)/(20); Part 4 Formulas (4)-(6))
# --------------------------------------------------------------------------- #
def critical_frequency(
    longitudinal_wave_speed: float,
    thickness: float,
    *,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> float:
    """Thin-plate critical frequency ``fc`` (Part 1, Formula (20)).

    ``fc = c0² / (1,8 · cL · h · π)`` for a homogeneous isotropic element.

    :param longitudinal_wave_speed: Longitudinal wave speed ``cL``, in m/s.
    :param thickness: Element thickness ``h``, in m.
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s.
    :return: Critical frequency ``fc``, in Hz.
    :raises ValueError: If any input is not positive/finite.
    """
    c0 = _positive(speed_of_sound, "speed_of_sound")
    c_l = _positive(longitudinal_wave_speed, "longitudinal_wave_speed")
    h = _positive(thickness, "thickness")
    return c0**2 / (_CRITICAL_FREQUENCY_CONSTANT * c_l * h * np.pi)


def strong_coupling_satisfied(
    velocity_level_difference: Sequence[float] | np.ndarray,
    mass_i: float,
    mass_j: float,
    critical_frequency_i: float,
    critical_frequency_j: float,
) -> np.ndarray:
    """Strong-coupling applicability check (Part 1, Formula (15)).

    ``Kij`` is relevant only where
    ``D̄v,ij ≥ 3 − 10 lg( (mi·fcj)/(mj·fci) )``.

    :param velocity_level_difference: Direction-averaged ``D̄v,ij`` per band,
        in dB.
    :param mass_i: Mass per unit area ``mi`` of element ``i``, in kg/m².
    :param mass_j: Mass per unit area ``mj`` of element ``j``, in kg/m².
    :param critical_frequency_i: Critical frequency ``fci`` of element ``i``,
        in Hz.
    :param critical_frequency_j: Critical frequency ``fcj`` of element ``j``,
        in Hz.
    :return: Boolean array, ``True`` where the inequality holds.
    :raises ValueError: If any scalar input is not positive/finite.
    """
    dv = _as_1d(velocity_level_difference, "velocity_level_difference")
    m_i = _positive(mass_i, "mass_i")
    m_j = _positive(mass_j, "mass_j")
    fc_i = _positive(critical_frequency_i, "critical_frequency_i")
    fc_j = _positive(critical_frequency_j, "critical_frequency_j")
    threshold = 3.0 - 10.0 * np.log10((m_i * fc_j) / (m_j * fc_i))
    return np.asarray(dv >= threshold, dtype=np.bool_)


def modal_density(
    area: float,
    critical_frequency: float,
    *,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> float:
    """Modal density ``n = π · S · fc / c0²`` (Part 4, Formula (5)).

    :param area: Element area ``S``, in m².
    :param critical_frequency: Critical frequency ``fc``, in Hz.
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s.
    :return: Modal density ``n``, in modes per Hz.
    :raises ValueError: If any input is not positive/finite.
    """
    s = _positive(area, "area")
    fc = _positive(critical_frequency, "critical_frequency")
    c0 = _positive(speed_of_sound, "speed_of_sound")
    return np.pi * s * fc / c0**2


def modal_overlap_factor(
    area: float,
    critical_frequency: float,
    structural_reverberation_time: float | Sequence[float] | np.ndarray,
    *,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray:
    """Modal overlap factor ``M = 2,2 · n / Ts`` (Part 4, Formula (6)).

    With the modal density ``n`` from :func:`modal_density`. Part 4 prefers
    ``M ≥ 1`` at 250 Hz and above; ``M < 0,25`` bands are bracketed and excluded
    from the single-number rating.

    :param area: Element area ``S``, in m².
    :param critical_frequency: Critical frequency ``fc``, in Hz.
    :param structural_reverberation_time: ``Ts``, in s, per band (or a single
        value).
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s.
    :return: Modal overlap factor ``M`` per band (dimensionless).
    :raises ValueError: If any input is not positive/finite.
    """
    n = modal_density(area, critical_frequency, speed_of_sound=speed_of_sound)
    ts = _positive_array(structural_reverberation_time, "structural_reverberation_time")
    return _STRUCTURAL_CONSTANT * n / ts


def band_mode_count(
    frequency: Sequence[float] | np.ndarray,
    area: float,
    critical_frequency: float,
    *,
    speed_of_sound: float = _DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray:
    """In-band mode count ``N = B · n`` (Part 4, Formula (4)).

    With the one-third-octave bandwidth approximation ``B = 0,23 · f`` and the
    modal density ``n`` from :func:`modal_density`. ``N ≥ 5`` modes per band is
    "always satisfactory".

    :param frequency: Band centre frequency ``f``, in Hz, per band.
    :param area: Element area ``S``, in m².
    :param critical_frequency: Critical frequency ``fc``, in Hz.
    :param speed_of_sound: Speed of sound in air ``c0``, in m/s.
    :return: In-band mode count ``N`` per band (dimensionless).
    :raises ValueError: If any input is not positive/finite.
    """
    f = _positive_array(frequency, "frequency")
    n = modal_density(area, critical_frequency, speed_of_sound=speed_of_sound)
    return 0.23 * f * n
