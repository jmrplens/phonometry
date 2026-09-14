#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What an enclosure is worth, measured rather than predicted (ISO 11546).

:mod:`phonometry.noise_control.enclosures` predicts what a box around a
machine will do from its walls and its lining. This module is the other half:
the measurement that says what the box built actually does, and the arithmetic
by which a manufacturer may declare it.

The quantity is a **difference of two runs**. Determine the machine's sound
power without the enclosure, determine it again with the enclosure in place,
and subtract band by band:

.. math::

   D_W = L_{W,\text{without}} - L_{W,\text{with}}

That is Equation (1) of both parts, and Equations (2) to (5) are the same
subtraction on the A-weighted total, on a sound pressure level at a stated
position and, in part 1, on the pair of levels the reciprocity method reads. Nothing here is a transmission loss: an insertion loss carries the
source, the room and the mounting with it, which is why the standard makes all
three reportable.

Two parts, one procedure
------------------------

**ISO 11546-1:1995** measures in a laboratory, for a **declaration**: the
manufacturer's figure, obtained under conditions the buyer can compare across
suppliers. **ISO 11546-2:1995** measures the same thing **in situ**, for an
**acceptance**: the enclosure as installed, in the room it was installed in,
with the machine it was built for. The two documents share their definitions,
their equations, their reporting rules and their artificial source word for
word; what changes is the environment, the base standard the levels come from
and, in part 2, an annex that asks whether the room is good enough at all.

Where the machine cannot be run, both parts substitute a source for it, and
the substitution is what the choice in :func:`applicable_methods` is about:

* an **actual** source, the machine itself, which is the normal case;
* the **reciprocity** method of part 1, 7.2, which puts the enclosure in a
  diffuse field and measures inside it, giving :math:`D_{pr}`;
* an **artificial** source, the tapping machine of Annex A on its undamped
  steel plate, used at several positions inside the enclosure.

Clause 1 draws the scope around the first of those: the part applies without
restriction to a free-standing enclosure smaller than
:data:`UNRESTRICTED_ENCLOSURE_VOLUME_M3`, and a larger one may still be
measured **with its actual source**, provided the base standard's own limit on
volume is met.

What this module computes, and what it refuses to
-------------------------------------------------

Every equation of clauses 6 and 7 is here, with the weighted rating of
ISO 717-1 delegated to :func:`phonometry.building.weighted_rating` rather than
re-derived, and the A-weighted estimate of the annexes written so that it
cannot disagree with its own inputs: :func:`estimated_a_weighted_insulation`
reduces algebraically to the difference of the two A-weighted totals computed
from the same assumed spectrum, which is the only exact oracle either part
offers.

Annex A is a hardware drawing and Annex B an illustration; their numbers are
constants here and nothing more. Clause 5 is instrumentation, clause 8 hands
its uncertainty to the base standard and to ISO 4871, and clauses 9 and 10 are
a report. The one piece of clause 9 that computes is the rounding of
9.4, which is :meth:`EnclosureInsulationResult.rounded`.

Neither part prints a worked example, so the tests are anchored where the
documents allow: the algebraic identities of the subtraction, the closed form
behind Figure C.1 of part 2, which is cross-checked against
:func:`phonometry.emission.environmental_correction`, and the printed
thresholds and tables.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.levels_math import energy_sum
from .._internal.validation import (
    require_choice,
    require_finite,
    require_finite_array,
    require_finite_matrix,
    require_positive,
)
from .._internal.warnings import PhonometryWarning
from ..emission._shared import ROOM_ABSORPTION_ESTIMATES, _a_weighting_corrections
from ._insulation_shared import (
    MANDATORY_BAND_RANGE_HZ,
    PREFERRED_BAND_RANGE_HZ,
    _band_fraction,
    _check_band_range,
    _rating_bands,
    _require_rating_bands,
    leak_ratio,
    seal_ratio,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ARTIFICIAL_SOURCE_DROP_MM",
    "ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB",
    "ARTIFICIAL_SOURCE_LEAK_RATIO_ADVISORY",
    "ARTIFICIAL_SOURCE_MAX_FILL_RATIO",
    "ARTIFICIAL_SOURCE_PLATE_MM",
    "ARTIFICIAL_SOURCE_STANDOFF_MM",
    "MANDATORY_BAND_RANGE_HZ",
    "PREFERRED_BAND_RANGE_HZ",
    "ROOM_ABSORPTION_ESTIMATES",
    "SOURCE_WALL_CLEARANCE_FACTOR",
    "TEST_ENVIRONMENT_REQUIREMENTS",
    "UNRESTRICTED_ENCLOSURE_VOLUME_M3",
    "EnclosureInsulationResult",
    "EnclosureInsulationWarning",
    "MethodEntry",
    "TestEnvironmentApplicability",
    "WeightedEnclosureInsulation",
    "applicable_methods",
    "artificial_source_insulation",
    "estimated_a_weighted_insulation",
    "fill_ratio",
    "leak_ratio",
    "reciprocity_insulation",
    "seal_ratio",
    "sound_power_insulation",
    "sound_pressure_insulation",
    "source_position_clearance_m",
    "test_environment_applicability",
    "weighted_insulation",
]

#: Clause 1: below this volume, in cubic metres, the part applies to a
#: free-standing enclosure without any restriction. Above it, only the actual
#: sound source will do, and only while the base standard's own maximum
#: permissible volume is met.
UNRESTRICTED_ENCLOSURE_VOLUME_M3: float = 2.0

#: The most of the enclosure's interior the artificial source may occupy
#: (7.2 of part 1, 7.2 of part 2).
ARTIFICIAL_SOURCE_MAX_FILL_RATIO: float = 0.25

#: The leak ratio above which clause 4 stops calling an enclosure
#: sealed, and the artificial source stops being representative.
ARTIFICIAL_SOURCE_LEAK_RATIO_ADVISORY: float = 0.02

#: Annex A, the steel plate of the artificial source: thickness, length and
#: width, in millimetres.
ARTIFICIAL_SOURCE_PLATE_MM: tuple[float, float, float] = (4.0, 800.0, 300.0)

#: Annex A: the height the hammer falls from, in millimetres.
ARTIFICIAL_SOURCE_DROP_MM: float = 40.0

#: Annex A: the distance from the plate to the enclosure wall, in millimetres.
ARTIFICIAL_SOURCE_STANDOFF_MM: float = 60.0

#: Annex B: the A-weighted sound power level of the example spectrum, in
#: decibels. The spectrum is an illustration measured on a 600 mm plate, not
#: the 800 mm plate Annex A specifies, so it is not a calibration target; see
#: ``docs/ERRATA.md``.
ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB: float = 110.0

#: 7.2 of part 2: the artificial source stands at least this fraction of the
#: shortest interior dimension away from any enclosure wall.
SOURCE_WALL_CLEARANCE_FACTOR: float = 0.2

#: The base standards Table 1 of the two parts names, spelled once each. The
#: table of methods, the room requirements of Annex C and the warnings all key
#: on these strings, so one spelling each keeps them from drifting apart.
_ISO_3741 = "ISO 3741"
_ISO_3742 = "ISO 3742"
_ISO_3743_1 = "ISO 3743-1"
_ISO_3743_2 = "ISO 3743-2"
_ISO_3744 = "ISO 3744"
_ISO_3746 = "ISO 3746"
_ISO_3747 = "ISO 3747"
_ISO_9614_1 = "ISO 9614-1"
_ISO_9614_2 = "ISO 9614-2"
_ISO_11201 = "ISO 11201"
_ISO_11202 = "ISO 11202"
_ISO_11204 = "ISO 11204"

#: Table C.1 of part 2: what each base standard asks of the room, as the
#: largest environmental correction ``K2`` it tolerates and the smallest
#: margin ``dL`` it needs over the background, both in decibels. A standard
#: that works by comparison with a reference source states no ``K2`` at all,
#: and the intensity pair states neither requirement, so those cells carry
#: ``None``. The last column of the printed table is headed ISO 10204, which
#: is no standard; its own footnote names ISO 11204, and that is the key here
#: (see the errata).
TEST_ENVIRONMENT_REQUIREMENTS: dict[str, tuple[float | None, float | None]] = {
    _ISO_3743_1: (None, 6.0),
    _ISO_3744: (2.0, 6.0),
    _ISO_3746: (7.0, 3.0),
    _ISO_3747: (None, 3.0),
    _ISO_9614_1: (None, None),
    _ISO_9614_2: (None, None),
    _ISO_11201: (2.0, 6.0),
    _ISO_11202: (7.0, 3.0),
    _ISO_11204: (7.0, 6.0),
}

#: The base standards that hand back an A-weighted number and nothing per
#: band, so a band quantity cannot be asked of them.
_A_WEIGHTED_ONLY = (_ISO_3746, _ISO_11202)

EnclosureCondition = Literal["laboratory", "in-situ"]
SourceKind = Literal["actual", "reciprocity", "artificial"]
_CONDITIONS: tuple[str, ...] = ("laboratory", "in-situ")
_SOURCE_KINDS: tuple[str, ...] = ("actual", "reciprocity", "artificial")
#: The quantities the ISO 717-1 rating of clause 7 may be asked for.
_RATEABLE_QUANTITIES: tuple[str, ...] = ("sound_power", "reciprocity")
#: The quantities the artificial source of Annex A may be read as, which the
#: clause decides by sending the levels to Equation (1) or to Equation (3).
_ARTIFICIAL_QUANTITIES: tuple[str, ...] = ("sound_power", "sound_pressure")
#: The fewest source positions 7.3 of part 1 and 7.2 of part 2 accept.
_MIN_ARTIFICIAL_POSITIONS = 2


class EnclosureInsulationWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 11546 states."""


def _a_weighted_total(
    levels: NDArray[np.float64], frequencies: NDArray[np.float64]
) -> float:
    """The A-weighted total of a band spectrum, ISO 3744 Annex E."""
    return float(energy_sum(levels + _a_weighting_corrections(frequencies)))


def _pair(
    level_without: ArrayLike,
    level_with: ArrayLike,
    frequencies: ArrayLike | None,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64] | None]:
    """The two spectra and their band centres, checked against each other."""
    without = require_finite_array(level_without, "level_without")
    with_ = require_finite_array(level_with, "level_with")
    if without.shape != with_.shape:
        msg = "'level_without' and 'level_with' must match band for band."
        raise ValueError(msg)
    freqs = None
    if frequencies is not None:
        freqs = require_finite_array(frequencies, "frequencies")
        if freqs.shape != without.shape:
            msg = "'frequencies' must match the spectra band for band."
            raise ValueError(msg)
        if np.any(freqs <= 0.0):
            msg = "'frequencies' must be positive."
            raise ValueError(msg)
    return without, with_, freqs


@dataclass(frozen=True)
class EnclosureInsulationResult:
    r"""The insertion loss of an enclosure, band by band.

    :ivar frequencies: Nominal band centre frequencies, in hertz, or ``None``
        when the levels were given without them.
    :ivar level_without: The level measured without the enclosure, in decibels.
    :ivar level_with: The level measured with it, in decibels.
    :ivar insulation: :math:`D_W`, :math:`D_p` or :math:`D_{pr}` per band, in
        decibels.
    :ivar quantity: What was subtracted: ``"sound_power"``,
        ``"sound_pressure"`` or ``"reciprocity"``.
    :ivar a_weighted_insulation: :math:`D_{WA}` or :math:`D_{pA}` of Equation
        (2) or (4), in decibels, or ``None`` when no band centres were given
        and no A-weighted pair was supplied. For the two standards of Table 1
        that determine an A-weighted value alone, a single pair of levels is
        that value, and it is carried here.
    :ivar condition: ``"laboratory"`` (part 1) or ``"in-situ"`` (part 2).
    :ivar source_kind: ``"actual"``, ``"reciprocity"`` or ``"artificial"``.
    :ivar base_standard: The standard the levels were determined by.
    :ivar band_fraction: 3 for one-third octaves, 1 for octaves.
    """

    frequencies: NDArray[np.float64] | None
    level_without: NDArray[np.float64]
    level_with: NDArray[np.float64]
    insulation: NDArray[np.float64]
    quantity: str
    a_weighted_insulation: float | None
    condition: str
    source_kind: str
    base_standard: str
    band_fraction: int

    def rounded(self) -> NDArray[np.int_]:
        """The band values as clause 9.4 reports them, to the nearest decibel."""
        return np.asarray(np.rint(self.insulation), dtype=np.int_)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two runs and the difference between them.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.noise_control.plot_enclosure_insulation`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.noise_control import plot_enclosure_insulation

        check_language(language)
        return plot_enclosure_insulation(self, ax=ax, language=language, **kwargs)


@dataclass(frozen=True)
class WeightedEnclosureInsulation:
    r"""The single-number rating of an insertion loss spectrum, ISO 717-1.

    :ivar rating: :math:`D_{W,w}` or :math:`D_{pr,w}`, in decibels.
    :ivar c: The spectrum adaptation term :math:`C`, in decibels.
    :ivar ctr: The spectrum adaptation term :math:`C_{tr}`, in decibels.
    :ivar unfavourable_sum: The sum of unfavourable deviations the shift left,
        in decibels.
    :ivar band_centres_hz: The bands the rating was read over, in hertz.
    :ivar quantity: What was rated, ``"sound_power"`` or ``"reciprocity"``.
    """

    rating: int
    c: int
    ctr: int
    unfavourable_sum: float
    band_centres_hz: NDArray[np.float64]
    quantity: str


@dataclass(frozen=True)
class TestEnvironmentApplicability:
    r"""Whether a room is good enough for a base standard, Annex C of part 2.

    :ivar base_standard: The standard asked about.
    :ivar environmental_correction_limit_db: The largest :math:`K_2` Table C.1
        allows it, in decibels, or ``None`` where the standard states none.
    :ivar background_margin_limit_db: The smallest margin over the background
        Table C.1 asks of it, in decibels, or ``None`` where the table states
        none.
    :ivar required_area_ratio: The smallest :math:`S_V/S` that meets the
        :math:`K_2` limit at this absorption coefficient.
    :ivar actual_area_ratio: The :math:`S_V/S` of the room and the measurement
        surface given.
    :ivar applicable: Whether the room meets the limit.
    :ivar mean_absorption_coefficient: The :math:`\alpha` the answer was read
        at.
    """

    base_standard: str
    environmental_correction_limit_db: float | None
    background_margin_limit_db: float | None
    required_area_ratio: float | None
    actual_area_ratio: float
    applicable: bool
    mean_absorption_coefficient: float


@dataclass(frozen=True)
class MethodEntry:
    """One row of Table 1: a way of measuring and what it yields.

    :ivar base_standard: The standard the levels come from.
    :ivar test_environment: The environment the row names for it, as printed.
    :ivar quantities: The symbols the row can give, such as ``("D_W", "D_WA")``.
    :ivar subclause: The subclause of ISO 11546 that describes it.
    :ivar band_values: Whether the row gives values per band, or only the
        A-weighted number.
    :ivar survey_grade_excluded: Whether footnote 2 of Table 1 of part 1 marks
        the row, which excludes the survey-grade variant of that standard. Part
        2 carries no such footnote.
    """

    base_standard: str
    test_environment: str
    quantities: tuple[str, ...]
    subclause: str
    band_values: bool
    survey_grade_excluded: bool = False


def _insulation(
    level_without: ArrayLike,
    level_with: ArrayLike,
    *,
    frequencies: ArrayLike | None,
    a_weighted_without: float | None,
    a_weighted_with: float | None,
    quantity: str,
    base_standard: str,
    condition: str,
    source_kind: str,
    band_fraction: int,
) -> EnclosureInsulationResult:
    """The body every one of Equations (1) to (5) shares."""
    without, with_, freqs = _pair(level_without, level_with, frequencies)
    fraction = _band_fraction(band_fraction)
    where, kind = _method_pair(condition, source_kind)
    _check_band_range(
        freqs,
        fraction,
        standard="ISO 11546",
        category=EnclosureInsulationWarning,
    )
    if base_standard in _A_WEIGHTED_ONLY and without.size > 1:
        msg = (
            f"{base_standard} determines an A-weighted value only (Table 1 of "
            "ISO 11546), so a band spectrum cannot be declared from it."
        )
        warnings.warn(msg, EnclosureInsulationWarning, stacklevel=3)
    insulation = without - with_
    weighted: float | None = None
    if (a_weighted_without is None) != (a_weighted_with is None):
        msg = (
            "Equation (2) is a difference, so give both 'a_weighted_without' "
            "and 'a_weighted_with' or neither."
        )
        raise ValueError(msg)
    if a_weighted_without is not None and a_weighted_with is not None:
        weighted = require_finite(
            a_weighted_without, "a_weighted_without"
        ) - require_finite(a_weighted_with, "a_weighted_with")
    elif freqs is not None:
        weighted = _a_weighted_total(without, freqs) - _a_weighted_total(with_, freqs)
    elif base_standard in _A_WEIGHTED_ONLY and without.size == 1:
        # Table 1 gives these two standards the A-weighted number and nothing
        # per band, so a single pair of levels is that number: naming it as
        # such is what keeps the result from passing a total off as a band.
        weighted = float(insulation[0])
    return EnclosureInsulationResult(
        frequencies=freqs,
        level_without=without,
        level_with=with_,
        insulation=np.asarray(insulation, dtype=np.float64),
        quantity=quantity,
        a_weighted_insulation=weighted,
        condition=where,
        source_kind=kind,
        base_standard=str(base_standard),
        band_fraction=fraction,
    )


def sound_power_insulation(
    level_without: ArrayLike,
    level_with: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    a_weighted_without: float | None = None,
    a_weighted_with: float | None = None,
    base_standard: str = "ISO 3744",
    condition: EnclosureCondition = "laboratory",
    source_kind: SourceKind = "actual",
    band_fraction: int = 3,
) -> EnclosureInsulationResult:
    r"""Insertion loss from two sound power determinations, Equations (1) and (2).

    :math:`D_W = L_{W,\text{without}} - L_{W,\text{with}}` band by band, and
    :math:`D_{WA}` the same difference of the A-weighted totals. Where the
    A-weighted pair is not supplied it is computed from the band spectra with
    the ISO 3744 Annex E table, which is what the note to clause 6.2 prefers.

    :param level_without: Sound power levels of the machine without the
        enclosure, in decibels.
    :param level_with: The same with the enclosure in place, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param a_weighted_without: :math:`L_{WA}` without the enclosure, in
        decibels, when it was measured rather than computed.
    :param a_weighted_with: The same with the enclosure, in decibels.
    :param base_standard: The standard the sound power came from, as Table 1
        lists them.
    :param condition: ``"laboratory"`` for part 1, ``"in-situ"`` for part 2.
    :param source_kind: ``"actual"``, ``"reciprocity"`` or ``"artificial"``.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The insertion loss, as an :class:`EnclosureInsulationResult`.
    :raises ValueError: For spectra that do not match, non-finite values, half
        an A-weighted pair, an unknown condition, source kind or band
        fraction, or a combination of condition and source kind Table 1 does
        not have.
    """
    return _insulation(
        level_without,
        level_with,
        frequencies=frequencies,
        a_weighted_without=a_weighted_without,
        a_weighted_with=a_weighted_with,
        quantity="sound_power",
        base_standard=base_standard,
        condition=condition,
        source_kind=source_kind,
        band_fraction=band_fraction,
    )


def sound_pressure_insulation(
    level_without: ArrayLike,
    level_with: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    a_weighted_without: float | None = None,
    a_weighted_with: float | None = None,
    base_standard: str = "ISO 11201",
    condition: EnclosureCondition = "laboratory",
    source_kind: SourceKind = "actual",
    band_fraction: int = 3,
) -> EnclosureInsulationResult:
    r"""Insertion loss from two sound pressure levels, Equations (3) and (4).

    :math:`D_p = L_{p,\text{without}} - L_{p,\text{with}}` at one stated
    position, with the same microphone positions in both runs, and
    :math:`D_{pA}` the difference of the A-weighted values. The position is
    part of the answer: the standard requires it in the report, because an
    insertion loss at the operator's ear and one a metre from the panel are
    different numbers about the same enclosure.

    :param level_without: Sound pressure levels without the enclosure, in
        decibels.
    :param level_with: The same with the enclosure, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param a_weighted_without: :math:`L_{pA}` without the enclosure, in
        decibels, when it was measured rather than computed.
    :param a_weighted_with: The same with the enclosure, in decibels.
    :param base_standard: The standard the pressure levels came from.
    :param condition: ``"laboratory"`` for part 1, ``"in-situ"`` for part 2.
    :param source_kind: ``"actual"``, ``"reciprocity"`` or ``"artificial"``.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The insertion loss, as an :class:`EnclosureInsulationResult`.
    :raises ValueError: For spectra that do not match, non-finite values, half
        an A-weighted pair, an unknown condition, source kind or band
        fraction, or a combination of condition and source kind Table 1 does
        not have.
    """
    return _insulation(
        level_without,
        level_with,
        frequencies=frequencies,
        a_weighted_without=a_weighted_without,
        a_weighted_with=a_weighted_with,
        quantity="sound_pressure",
        base_standard=base_standard,
        condition=condition,
        source_kind=source_kind,
        band_fraction=band_fraction,
    )


def reciprocity_insulation(
    external_levels: ArrayLike,
    internal_levels: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    band_fraction: int = 3,
) -> EnclosureInsulationResult:
    r"""Insertion loss measured from the outside in, Equation (5) of part 1.

    :math:`D_{pr} = \overline{L_{p,\text{ext}}} - \overline{L_{p,\text{int}}}`:
    the enclosure is put in a diffuse field, the field is measured around it
    and again inside it, and the difference is the insulation the enclosure
    would give a source within it. The method belongs to the laboratory, and it
    is the one case where the enclosure is measured without any source inside
    at all.

    :param external_levels: The averaged level in the field outside, per band,
        in decibels.
    :param internal_levels: The averaged level inside the enclosure standing in
        that field, per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The insertion loss, as an :class:`EnclosureInsulationResult` whose
        quantity is ``"reciprocity"``.
    :raises ValueError: For spectra that do not match, non-finite values or an
        unknown band fraction.
    """
    return _insulation(
        external_levels,
        internal_levels,
        frequencies=frequencies,
        a_weighted_without=None,
        a_weighted_with=None,
        quantity="reciprocity",
        base_standard="ISO 3741",
        condition="laboratory",
        source_kind="reciprocity",
        band_fraction=band_fraction,
    )


def artificial_source_insulation(
    level_without_by_position: ArrayLike,
    level_with_by_position: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    quantity: str = "sound_power",
    condition: EnclosureCondition = "laboratory",
    band_fraction: int = 3,
) -> EnclosureInsulationResult:
    r"""Insertion loss with the tapping source of Annex A, 7.3 of part 1 and 7.2 of part 2.

    The plate is dropped at each of several positions, the band difference is
    formed at each, and the positions are averaged **arithmetically**: "express
    the final result as the arithmetic mean value of the results for the
    different source positions" is the clause's own sentence, and it is not the
    energy mean used almost everywhere else in this library, so it is written
    out here rather than borrowed.

    The clause sends the levels to Equation (1) or to Equation (3) depending on
    which determination was made, so the method yields :math:`D_W` or
    :math:`D_p` and 9.4 e) reports whichever it was. That is ``quantity``.

    :param level_without_by_position: Levels without the enclosure, one row per
        source position, in decibels.
    :param level_with_by_position: The same with the enclosure, row for row, in
        decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param quantity: ``"sound_power"`` (default) for Equation (1), or
        ``"sound_pressure"`` for Equation (3).
    :param condition: ``"laboratory"`` for part 1, ``"in-situ"`` for part 2.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The averaged insertion loss, as an
        :class:`EnclosureInsulationResult`.
    :raises ValueError: For arrays that are not two-dimensional and matched,
        fewer than two source positions, or an unknown quantity.
    """
    kind = require_choice(str(quantity), "quantity", _ARTIFICIAL_QUANTITIES)
    without = require_finite_matrix(
        level_without_by_position, "level_without_by_position"
    )
    with_ = require_finite_matrix(level_with_by_position, "level_with_by_position")
    if without.shape != with_.shape:
        msg = (
            "'level_without_by_position' and 'level_with_by_position' must "
            "match, one row per source position and one column per band."
        )
        raise ValueError(msg)
    if without.shape[0] < _MIN_ARTIFICIAL_POSITIONS:
        msg = (
            f"The artificial source is used at {_MIN_ARTIFICIAL_POSITIONS} "
            "positions or more (7.3 of ISO 11546-1, 7.2 of ISO 11546-2); got "
            f"{without.shape[0]}."
        )
        raise ValueError(msg)
    mean_without = np.mean(without, axis=0)
    mean_with = np.mean(with_, axis=0)
    return _insulation(
        mean_without,
        mean_with,
        frequencies=frequencies,
        a_weighted_without=None,
        a_weighted_with=None,
        quantity=kind,
        base_standard="ISO 11546 Annex A",
        condition=condition,
        source_kind="artificial",
        band_fraction=band_fraction,
    )


def weighted_insulation(
    insulation: ArrayLike,
    *,
    quantity: str = "sound_power",
    band_fraction: int = 3,
) -> WeightedEnclosureInsulation:
    r"""The single-number rating of an insertion loss, 7.4 of part 1 and 7.3 of part 2.

    Both parts say the same thing: rate the spectrum by ISO 717-1, putting
    :math:`D_W` or :math:`D_{pr}` where that standard writes :math:`R`. The
    reference curve, the shift and the adaptation terms come from
    :func:`phonometry.building.weighted_rating`, which has its own conformance
    rows; what is done here is the trim to the rating bands.

    :param insulation: The insertion loss per band, in decibels, over exactly
        the 16 one-third-octave rating bands of 100 Hz to 3,15 kHz or the 5
        octave ones of 125 Hz to 2 kHz; a wider spectrum is refused rather
        than trimmed, because which bands it holds is the caller's to say.
    :param quantity: ``"sound_power"`` (default) or ``"reciprocity"``.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The rating, as a :class:`WeightedEnclosureInsulation`.
    :raises ValueError: For a spectrum that does not carry the rating bands.
    """
    from ..building import weighted_rating

    values = require_finite_array(insulation, "insulation")
    fraction = _band_fraction(band_fraction)
    kind = require_choice(str(quantity), "quantity", _RATEABLE_QUANTITIES)
    bands, band_set = _rating_bands(fraction)
    _require_rating_bands(values, bands)
    result = weighted_rating(values, band_set)
    return WeightedEnclosureInsulation(
        rating=int(result.rating),
        c=int(result.c),
        ctr=int(result.ctr),
        unfavourable_sum=float(result.unfavourable_sum),
        band_centres_hz=bands,
        quantity=kind,
    )


def estimated_a_weighted_insulation(
    spectrum_levels: ArrayLike,
    insulation: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> float:
    r"""The A-weighted insulation an enclosure would give a stated spectrum.

    Annex C of part 1 and Annex D of part 2, the same formula:

    .. math::

       D_{WA,e} = L_A - 10 \lg \sum_i 10^{0,1 (L_i - A_i - D_i)}

    where :math:`L_i` is the assumed source spectrum, :math:`A_i` the
    A-weighting of the band and :math:`D_i` the measured insulation. The sign
    of :math:`A_i` is the trap: the standard prints an attenuation, positive
    where the weighting takes level away, while this library's band
    corrections are the correction itself, so :math:`A_i = -C_k`. Both terms
    are formed here from the same table, so the total and the sum cannot
    disagree, and with :math:`D_i = 0` the answer is exactly zero.

    The same formula serves :math:`D_W` (giving :math:`D_{WA,e}`),
    :math:`D_p` and :math:`D_{pr}`; which one it is, is the caller's.

    :param spectrum_levels: The assumed source spectrum :math:`L_i` per band,
        in decibels.
    :param insulation: The measured insulation :math:`D_i` per band, in
        decibels.
    :param frequencies: Nominal band centres, in hertz.
    :return: :math:`D_{WA,e}`, in decibels.
    :raises ValueError: For inputs that do not match band for band.
    """
    levels = require_finite_array(spectrum_levels, "spectrum_levels")
    loss = require_finite_array(insulation, "insulation")
    freqs = require_finite_array(frequencies, "frequencies")
    if levels.shape != loss.shape or levels.shape != freqs.shape:
        msg = "'spectrum_levels', 'insulation' and 'frequencies' must match band for band."
        raise ValueError(msg)
    corrections = _a_weighting_corrections(freqs)
    unenclosed = energy_sum(levels + corrections)
    enclosed = energy_sum(levels + corrections - loss)
    return float(unenclosed - enclosed)


def source_position_clearance_m(shortest_inner_dimension_m: float) -> float:
    r"""How far the artificial source stands from a wall, 7.3 of part 1 and 7.2 of part 2.

    :math:`0,2\,d` with :math:`d` the shortest interior dimension of the
    enclosure, so that the plate is never against a panel it is meant to
    excite through the air. Both parts print the same sentence, and both add
    that the source is used in two orientations 90 degrees apart where the
    enclosure has room for them.

    :param shortest_inner_dimension_m: :math:`d`, in metres.
    :return: The least distance to any wall, in metres.
    :raises ValueError: For a non-positive dimension.
    """
    dimension = require_positive(
        shortest_inner_dimension_m, "shortest_inner_dimension_m"
    )
    return SOURCE_WALL_CLEARANCE_FACTOR * dimension


def fill_ratio(source_volume_m3: float, interior_volume_m3: float) -> float:
    r"""How much of the enclosure the source fills, 3.15 of part 1 and 3.13 of part 2.

    :math:`\phi = V_S / V_E`. The artificial source of Annex A is
    representative only up to
    :data:`ARTIFICIAL_SOURCE_MAX_FILL_RATIO`; past that it is changing the
    interior field it is supposed to be measuring through.

    :param source_volume_m3: The volume of the source, in cubic metres.
    :param interior_volume_m3: The interior volume of the enclosure, in cubic
        metres.
    :return: The ratio, dimensionless.
    :raises ValueError: For a non-positive volume.
    """
    source = require_positive(source_volume_m3, "source_volume_m3")
    interior = require_positive(interior_volume_m3, "interior_volume_m3")
    return source / interior


def test_environment_applicability(
    *,
    base_standard: str,
    mean_absorption_coefficient: float,
    room_surface_area_m2: float,
    measurement_surface_area_m2: float,
) -> TestEnvironmentApplicability:
    r"""Is this room good enough for that base standard? Annex C of part 2.

    Annex C asks the question the other way round from the emission
    standards: not what the environmental correction of this room is, but how
    much room a method needs. With
    :math:`K_2 = 10 \lg (1 + 4 S / (\alpha S_V))` held at the limit Table C.1
    sets, the ratio the room must reach is

    .. math::

       \frac{S_V}{S} = \frac{4}{(10^{K_2/10} - 1)\,\alpha}

    which is Figure C.1 in closed form, the curve the annex asks the reader to
    read off by eye. Take :math:`\alpha` from
    :data:`ROOM_ABSORPTION_ESTIMATES` when nobody measured it.

    A standard that works by comparison with a reference sound source, ISO
    3743-1 and ISO 3747, states no :math:`K_2` requirement at all; for those
    the answer carries the background margin and nothing else, and
    ``applicable`` is decided by the margin alone, which this function does
    not see. It is reported as ``True`` there, with
    ``required_area_ratio`` at ``None``, so that the caller reads the table
    rather than a number the annex does not give.

    :param base_standard: One of the columns of Table C.1, as
        :data:`TEST_ENVIRONMENT_REQUIREMENTS` keys them.
    :param mean_absorption_coefficient: :math:`\alpha` of the room,
        dimensionless.
    :param room_surface_area_m2: :math:`S_V`, the total area of the room's
        boundary surfaces, in square metres.
    :param measurement_surface_area_m2: :math:`S`, the area of the measurement
        surface around the source, in square metres.
    :return: The verdict, as a :class:`TestEnvironmentApplicability`.
    :raises ValueError: For an unknown standard, a coefficient outside
        ``(0, 1]`` or a non-positive area.
    """
    name = require_choice(
        str(base_standard), "base_standard", tuple(TEST_ENVIRONMENT_REQUIREMENTS)
    )
    alpha = require_positive(mean_absorption_coefficient, "mean_absorption_coefficient")
    if alpha > 1.0:
        msg = "'mean_absorption_coefficient' must be in the range (0, 1]."
        raise ValueError(msg)
    room = require_positive(room_surface_area_m2, "room_surface_area_m2")
    surface = require_positive(
        measurement_surface_area_m2, "measurement_surface_area_m2"
    )
    limit, margin = TEST_ENVIRONMENT_REQUIREMENTS[name]
    ratio = room / surface
    required: float | None = None
    applicable = True
    if limit is not None:
        required = 4.0 / ((10.0 ** (limit / 10.0) - 1.0) * alpha)
        applicable = ratio >= required
    return TestEnvironmentApplicability(
        base_standard=name,
        environmental_correction_limit_db=limit,
        background_margin_limit_db=margin,
        required_area_ratio=required,
        actual_area_ratio=ratio,
        applicable=applicable,
        mean_absorption_coefficient=alpha,
    )


#: Table 1 of each part, as data: the environment, the standard, the symbols
#: it may give and the subclause that describes it. Part 1 and part 2 print
#: different rows, and the difference is the point: the laboratory table has no
#: survey-grade row and carries a reciprocity block, while the in-situ table
#: adds ISO 3746, ISO 3747 and ISO 11202 and has no reciprocity at all.
_REVERBERATION = "Reverberation room"
_HARD_WALLED = "Hard-walled test room"
_SPECIAL_REVERBERATION = "Special reverberation room"
_OUTDOORS = "Outdoors or in large room"
_NO_SPECIAL = "No special test environment"
_FREE_FIELD = "Free-field over a reflecting plane; indoor or outdoor"

_POWER = ("D_W", "D_WA")
_PRESSURE = ("D_p", "D_pA")
_RATED_POWER = ("D_W", "D_W,w")

_METHODS: dict[tuple[str, str], tuple[MethodEntry, ...]] = {
    ("laboratory", "actual"): (
        MethodEntry(_ISO_3741, _REVERBERATION, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_3742, _REVERBERATION, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_3743_1, _HARD_WALLED, _POWER, "6.2", band_values=True),
        MethodEntry(
            _ISO_3743_2, _SPECIAL_REVERBERATION, _POWER, "6.2", band_values=True
        ),
        MethodEntry(_ISO_3744, _OUTDOORS, _POWER, "6.2", band_values=True),
        MethodEntry(
            _ISO_9614_1,
            _NO_SPECIAL,
            _POWER,
            "6.2",
            band_values=True,
            survey_grade_excluded=True,
        ),
        MethodEntry(_ISO_9614_2, _NO_SPECIAL, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_11201, _FREE_FIELD, _PRESSURE, "6.3", band_values=True),
        MethodEntry(
            _ISO_11204,
            _OUTDOORS,
            _PRESSURE,
            "6.3",
            band_values=True,
            survey_grade_excluded=True,
        ),
    ),
    ("laboratory", "reciprocity"): (
        MethodEntry(
            _ISO_3741,
            "Test room complying with ISO 3741",
            ("D_pr", "D_pr,w"),
            "7.2",
            band_values=True,
        ),
    ),
    ("laboratory", "artificial"): (
        MethodEntry(_ISO_3741, _REVERBERATION, _RATED_POWER, "7.3", band_values=True),
        MethodEntry(_ISO_3743_1, _HARD_WALLED, _RATED_POWER, "7.3", band_values=True),
        MethodEntry(
            _ISO_3743_2, _SPECIAL_REVERBERATION, _RATED_POWER, "7.3", band_values=True
        ),
        MethodEntry(_ISO_3744, _OUTDOORS, _RATED_POWER, "7.3", band_values=True),
        MethodEntry(
            _ISO_9614_1,
            _NO_SPECIAL,
            _RATED_POWER,
            "7.3",
            band_values=True,
            survey_grade_excluded=True,
        ),
        MethodEntry(_ISO_9614_2, _NO_SPECIAL, _RATED_POWER, "7.3", band_values=True),
        MethodEntry(_ISO_11201, _FREE_FIELD, ("D_p",), "7.3", band_values=True),
        MethodEntry(
            _ISO_11204,
            _OUTDOORS,
            ("D_p",),
            "7.3",
            band_values=True,
            survey_grade_excluded=True,
        ),
    ),
    ("in-situ", "actual"): (
        MethodEntry(_ISO_3743_1, _HARD_WALLED, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_3744, _OUTDOORS, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_3746, _NO_SPECIAL, ("D_WA",), "6.2", band_values=False),
        MethodEntry(_ISO_3747, _NO_SPECIAL, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_9614_1, _NO_SPECIAL, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_9614_2, _NO_SPECIAL, _POWER, "6.2", band_values=True),
        MethodEntry(_ISO_11201, _FREE_FIELD, _PRESSURE, "6.3", band_values=True),
        MethodEntry(_ISO_11202, _NO_SPECIAL, ("D_pA",), "6.3", band_values=False),
        MethodEntry(_ISO_11204, _OUTDOORS, _PRESSURE, "6.3", band_values=True),
    ),
    ("in-situ", "artificial"): (
        MethodEntry(_ISO_3743_1, _HARD_WALLED, _RATED_POWER, "7.2", band_values=True),
        MethodEntry(_ISO_3744, _OUTDOORS, _RATED_POWER, "7.2", band_values=True),
        MethodEntry(_ISO_3747, _NO_SPECIAL, _RATED_POWER, "7.2", band_values=True),
        MethodEntry(_ISO_9614_1, _NO_SPECIAL, _RATED_POWER, "7.2", band_values=True),
        MethodEntry(_ISO_9614_2, _NO_SPECIAL, _RATED_POWER, "7.2", band_values=True),
        MethodEntry(_ISO_11201, _FREE_FIELD, ("D_p",), "7.2", band_values=True),
        MethodEntry(_ISO_11204, _OUTDOORS, ("D_p",), "7.2", band_values=True),
    ),
}


def _method_pair(condition: str, source_kind: str) -> tuple[str, str]:
    """The condition and the source kind of a combination Table 1 prints.

    Reading the table before anything else is what stops a result claiming a
    method the standard does not have: the reciprocity method of 7.2 is
    printed in part 1 alone, so there is no in-situ row for it.

    :param condition: ``"laboratory"`` or ``"in-situ"``.
    :param source_kind: ``"actual"``, ``"reciprocity"`` or ``"artificial"``.
    :return: The pair, normalised.
    :raises ValueError: For an unknown condition or source kind, or a
        combination the standard does not have.
    """
    where = require_choice(str(condition), "condition", _CONDITIONS)
    kind = require_choice(str(source_kind), "source_kind", _SOURCE_KINDS)
    if (where, kind) not in _METHODS:
        msg = (
            f"ISO 11546 has no {kind} source in the {where} condition: the "
            "reciprocity method of 7.2 belongs to part 1 alone."
        )
        raise ValueError(msg)
    return where, kind


def applicable_methods(
    *,
    condition: EnclosureCondition = "laboratory",
    source_kind: SourceKind = "actual",
) -> tuple[MethodEntry, ...]:
    """The rows of Table 1 open to a given condition and source.

    Reading the table is what stops a declaration claiming more than its
    method can give: a survey-grade determination hands back an A-weighted
    number and nothing per band, so :math:`D_W` cannot be declared from it,
    and the reciprocity method exists only in the laboratory.

    :param condition: ``"laboratory"`` (default) or ``"in-situ"``.
    :param source_kind: ``"actual"`` (default), ``"reciprocity"`` or
        ``"artificial"``.
    :return: The rows, as :class:`MethodEntry` values.
    :raises ValueError: For an unknown condition or source kind, or a
        combination the standard does not have.
    """
    return _METHODS[_method_pair(condition, source_kind)]
