#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a silencer does where it was installed (ISO 11820:1996).

:mod:`phonometry.noise_control.silencer_measurement` is the laboratory
measurement a catalogue figure comes from: a qualified rig, a substitution
duct, a stated uncertainty. This is the other one. The silencer is in the
plant, the plant is running, and the question is what the thing is doing
there.

Clause 1.1 puts the relationship between the two in one sentence: results
obtained here **cannot be compared** with performance data obtained from
laboratory measurements to ISO 7235. The reason is in the Introduction: what
is measured in situ carries the flanking transmission, the regenerated flow
noise and the operating conditions with it, and the standard treats all three
as properties of the silencer in that installation rather than as errors to be
removed. A number from this module and a number from a data sheet are two
different quantities, and this library keeps them in two different modules so
that they cannot be added by accident.

Two quantities, twenty installations
------------------------------------

**Transmission loss** :math:`D_{ts}` compares the sound power reaching the
silencer with the sound power leaving it, Equation (4). **Insertion loss**
:math:`D_{is}` compares the plant without the silencer with the plant with it,
Equation (8), and it is the only choice for a blowdown silencer, which does
not exist as a duct element to measure through.

Neither is a bare subtraction of levels. Each starts as a sound pressure level
difference, Equation (1) or (3), and becomes a loss by adding the area ratio
of the two measurement surfaces and the difference of the two field
corrections:

.. math::

   D_{ts} = D_{tps} + 10 \lg \frac{S_2}{S_1} + K_2 - K_1

Which areas those are is not a matter of taste. Figure 1 enumerates twenty
installations, sixteen for transmission and four for insertion, by what stands
on each side of the silencer, and clause 9.1.3 gives each of them its own rule
for :math:`S_1` and :math:`S_2`: a measurement surface in the duct, a quarter
or a half of the silencer intake, a quarter of the room absorption, or a
surface enveloping the open end. :func:`installation_case` is that figure and
those rules as data, so that a measurement says which case it is and the areas
follow.

The corrections that are not a correction
-----------------------------------------

Clause 4 corrects for background noise from a **printed table**, not from the
usual logarithmic subtraction, and the two do not agree: at a margin of 5 dB
the table takes off 2 dB where the formula takes off 1,7, and at 8 dB it takes
off 1 where the formula takes off 0,7. :func:`silencer_background_correction_db`
implements the table as printed, and says so.

Where the extraneous sound can be measured on its own, 9.1.1 and 9.1.2 offer
the energy route of Equations (17) and (18) instead, and cap it: **the maximum
correction is 3 dB**. A measurement that needs more than that does not yield
the quantity at all, and the clause says what may be stated instead, which is
an inequality. :func:`extraneous_corrected_mean_level_db` returns whether the
cap was reached so that a capped value cannot be reported as a determination.

Clause 9.1.5 is the one prohibition worth reading twice: converting
one-third-octave data to octave data is permissible **for measured sound
pressure levels only, but not for level differences**.
:func:`octave_levels_from_third_octave_db` does the permitted conversion, and
the docstring names the function in this library that does the forbidden one
for a different standard.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.levels_math import energy_mean
from .._internal.validation import (
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ISO11820_AIR_GAS_CONSTANT",
    "ISO11820_BACKGROUND_CORRECTIONS_DB",
    "DOWNSTREAM_DISTANCE_COEFFICIENTS",
    "INSTALLATION_CASES",
    "MAXIMUM_EXTRANEOUS_CORRECTION_DB",
    "ISO11820_MINIMUM_BACKGROUND_MARGIN_DB",
    "ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB",
    "ISO11820_OCTAVE_BAND_EXTENDED_RANGE_HZ",
    "ISO11820_OCTAVE_BAND_RANGE_HZ",
    "SABINE_AREA_COEFFICIENT",
    "ISO11820_SOUND_SPEED_M_S",
    "ISO11820_AMBIENT_PRESSURE_PA",
    "ISO11820_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ",
    "ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ",
    "TYPICAL_FIELD_CORRECTION_LIMIT_DB",
    "ISO11820_GAS_CONSTANT",
    "UPSTREAM_DISTANCE_DIAMETERS",
    "VELOCITY_UNIFORMITY_TOLERANCE_PERCENT",
    "InstallationCase",
    "SilencerInSituResult",
    "SilencerInSituWarning",
    "silencer_background_correction_db",
    "extraneous_corrected_mean_level_db",
    "flow_velocity_m_s",
    "gas_density_kg_m3",
    "in_situ_insertion_loss",
    "in_situ_transmission_loss",
    "insertion_level_difference_db",
    "installation_case",
    "mean_sound_pressure_level_db",
    "measurement_distance_downstream_m",
    "measurement_distance_upstream_m",
    "octave_levels_from_third_octave_db",
    "reverberant_surface_area_m2",
    "silencer_flow_velocity_m_s",
    "sound_power_level_db",
    "static_pressure_difference_pa",
    "temperature_field_correction_db",
    "total_pressure_loss_pa",
    "transmission_level_difference_db",
    "velocity_pressure_pa",
]

#: Table 1 (clause 4): the correction to subtract, in decibels, keyed by the
#: difference between the level with the source running and the background
#: alone, in decibels. The table is stepped and integer-indexed; below
#: :data:`ISO11820_MINIMUM_BACKGROUND_MARGIN_DB` it prints "measurements invalid", and
#: above :data:`ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB` it prints zero.
ISO11820_BACKGROUND_CORRECTIONS_DB: dict[int, float] = {
    3: 3.0,
    4: 2.0,
    5: 2.0,
    6: 1.0,
    7: 1.0,
    8: 1.0,
    9: 0.5,
    10: 0.5,
}

#: Clause 4: below this margin over the background the measurement does not
#: stand, and only an inequality may be stated.
ISO11820_MINIMUM_BACKGROUND_MARGIN_DB: float = 3.0

#: Table 1: above this margin the correction is zero.
ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB: float = 10.0

#: 9.1.1 and 9.1.2: "the maximum correction is 3 dB". The printed value is
#: the correction at a 3 dB margin, the "3 -> 3" row of Table 1, which the
#: energy subtraction writes unrounded as -10 lg(1 - 10^-0,3) = 3,0206 dB;
#: ISO 3746:2010 8.3.3 prints the same number the same way, as 3 dB and "the
#: value for" a 3 dB margin. The cap is therefore judged on the margin.
MAXIMUM_EXTRANEOUS_CORRECTION_DB: float = 3.0

#: 1.3 a): the octave range the standard asks for, and the wider one it would
#: rather have where the equipment reaches it.
ISO11820_OCTAVE_BAND_RANGE_HZ: tuple[float, float] = (63.0, 4000.0)
ISO11820_OCTAVE_BAND_EXTENDED_RANGE_HZ: tuple[float, float] = (31.5, 8000.0)

#: 1.3 a): the same in one-third octaves.
ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ: tuple[float, float] = (50.0, 5000.0)
ISO11820_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ: tuple[float, float] = (25.0, 10000.0)

#: The note under Equation (6): "c = 340 m/s at room temperature", in metres
#: per second. The standard prints this rounded value and not 343.
ISO11820_SOUND_SPEED_M_S: float = 340.0

#: Equations (6), (10) and (12): the :math:`6 \ln 10` of the Sabine equivalent
#: area, dimensionless.
SABINE_AREA_COEFFICIENT: float = 6.0 * math.log(10.0)

#: NOTE 4: the field corrections are "typically less than 3 dB in absolute
#: value" once the areas of 3.3 and 3.4 have been chosen.
TYPICAL_FIELD_CORRECTION_LIMIT_DB: float = 3.0

#: Equation (29): the universal gas constant as printed, in N m per kmol K.
ISO11820_GAS_CONSTANT: float = 8314.4

#: Equation (29): R/M for air as printed, in N m per kg K.
ISO11820_AIR_GAS_CONSTANT: float = 287.0

#: Equation (29): the ambient static pressure it assumes, in pascals.
ISO11820_AMBIENT_PRESSURE_PA: float = 100_000.0

#: Equation (15): the upstream measurement surface stands this many equivalent
#: diameters from the silencer.
UPSTREAM_DISTANCE_DIAMETERS: float = 1.5

#: Equation (16): the two coefficients of the downstream distance.
DOWNSTREAM_DISTANCE_COEFFICIENTS: tuple[float, float] = (12.0, 10.0)

#: 9.2: past this deviation from the mean the velocity distribution is
#: reported, because the pressure loss and the regenerated sound change with
#: it.
VELOCITY_UNIFORMITY_TOLERANCE_PERCENT: float = 10.0

InSituQuantity = Literal["transmission", "insertion"]
SideSpace = Literal["duct", "diffuse_room", "non_diffuse_room", "open_space", "any"]

_SIDES: tuple[str, ...] = (
    "duct",
    "diffuse_room",
    "non_diffuse_room",
    "open_space",
)

#: The area rules 9.1.3 and 9.1.4 name, as the clause words them.
_MEASUREMENT_SURFACE = "measurement surface in the duct cross-section"
_QUARTER_INTAKE = "one-quarter of the total silencer cross-section"
_HALF_INTAKE = "one-half of the total silencer intake cross-section"
_QUARTER_ABSORPTION = "one-quarter of the absorption of the receiver room"
_ENVELOPING = "measurement surface enveloping the end of the silencer"
_ENVELOPING_APERTURE = "measurement surface enveloping the aperture in the wall"
_DUCT_WITHOUT = "measurement cross-section in the duct without the silencer"
_DUCT_WITH = "measurement cross-section in the duct with the silencer installed"
_ABSORPTION_WITHOUT = "one-quarter of the absorption of the room without the silencer"
_ABSORPTION_WITH = "one-quarter of the absorption of the room with the silencer"
_ENVELOPING_OPEN_END = "measurement surface enveloping the open end of the silencer"
_ANY_SIDE = "any duct, room or space"

#: The three one-third-octave bands inside one octave, 9.1.5.
_THIRDS_PER_OCTAVE = 3

#: How far under the 3 dB of clause 4 the margin of two energy means may fall
#: in floating point and still be the printed 3 dB, in decibels. Levels 3,0 dB
#: apart come out of the two means up to 1,4e-14 dB either side of it.
_MARGIN_TOLERANCE_DB = 1e-9


class SilencerInSituWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 11820 states."""


@dataclass(frozen=True)
class InstallationCase:
    """One of the twenty installations of Figure 1, with its area rules.

    :ivar number: The case number Figure 1 prints, 1 to 20.
    :ivar source_side: What stands on the source side: ``"duct"``,
        ``"diffuse_room"``, ``"non_diffuse_room"``, ``"open_space"``, or
        ``"any"`` for the four insertion cases, whose source side is not part
        of the case.
    :ivar receiver_side: The same for the receiver side.
    :ivar quantity: ``"transmission"`` for cases 1 to 16, ``"insertion"`` for
        17 to 20.
    :ivar source_area_rule: How 9.1.3 or 9.1.4 says to read :math:`S_2`, the
        source side of a transmission case, or :math:`S_{II}`, the run without
        the silencer of an insertion one, in the clause's own words.
    :ivar receiver_area_rule: The same for :math:`S_1` or :math:`S_I`.
    """

    number: int
    source_side: str
    receiver_side: str
    quantity: str
    source_area_rule: str
    receiver_area_rule: str


#: 9.1.3 groups the sixteen transmission cases by what the source side is:
#: cases 1 to 4 have a duct there, cases 5 to 8 a room with a diffuse field,
#: and the rest a room without one or open space.
_LAST_DUCT_SOURCE_CASE = 4
_LAST_DIFFUSE_SOURCE_CASE = 8


def _transmission_source_rule(number: int) -> str:
    """The :math:`S_2` rule of 9.1.3, by case number."""
    if number <= _LAST_DUCT_SOURCE_CASE:
        return _MEASUREMENT_SURFACE
    if number <= _LAST_DIFFUSE_SOURCE_CASE:
        return _QUARTER_INTAKE
    return _HALF_INTAKE


def _transmission_receiver_rule(receiver: str) -> str:
    """The :math:`S_1` rule of 9.1.3, which follows the receiver side."""
    if receiver == "duct":
        return _MEASUREMENT_SURFACE
    if receiver == "diffuse_room":
        return _QUARTER_ABSORPTION
    return _ENVELOPING


def _build_cases() -> dict[int, InstallationCase]:
    """Figure 1 and the area rules of 9.1.3 and 9.1.4, as one table."""
    cases: dict[int, InstallationCase] = {}
    number = 1
    for source in _SIDES:
        for receiver in _SIDES:
            cases[number] = InstallationCase(
                number=number,
                source_side=source,
                receiver_side=receiver,
                quantity="transmission",
                source_area_rule=_transmission_source_rule(number),
                receiver_area_rule=_transmission_receiver_rule(receiver),
            )
            number += 1
    insertion_rules = {
        "duct": (_DUCT_WITHOUT, _DUCT_WITH),
        "diffuse_room": (_ABSORPTION_WITHOUT, _ABSORPTION_WITH),
        "non_diffuse_room": (_ENVELOPING_APERTURE, _ENVELOPING_OPEN_END),
        "open_space": (_ENVELOPING_APERTURE, _ENVELOPING_OPEN_END),
    }
    for receiver in _SIDES:
        without, with_ = insertion_rules[receiver]
        cases[number] = InstallationCase(
            number=number,
            source_side=_ANY_SIDE,
            receiver_side=receiver,
            quantity="insertion",
            source_area_rule=without,
            receiver_area_rule=with_,
        )
        number += 1
    return cases


#: Figure 1 as data: the twenty installations and the area rules clause 9
#: gives each of them. Cases 1 to 16 are transmission, 17 to 20 insertion.
INSTALLATION_CASES: dict[int, InstallationCase] = _build_cases()


def installation_case(number: int) -> InstallationCase:
    """One installation of Figure 1, with the area rules clause 9 gives it.

    The figure is a matrix: the source side may be a duct, a room with a
    diffuse field, a room with a non-diffuse field or an open space, and so
    may the receiver side, which is sixteen transmission cases. The four
    insertion cases are keyed by the receiver side alone, because the source
    side is not part of what is measured.

    :param number: The case number Figure 1 prints, 1 to 20.
    :return: The case, as an :class:`InstallationCase`.
    :raises ValueError: For a number outside the figure.
    """
    case = INSTALLATION_CASES.get(int(number))
    if case is None:
        msg = (
            "Figure 1 of ISO 11820 numbers its installations 1 to 20, "
            "sixteen for transmission and four for insertion; got "
            f"{number}."
        )
        raise ValueError(msg)
    return case


def silencer_background_correction_db(
    level_difference_db: ArrayLike,
) -> NDArray[np.float64]:
    r"""The background correction of Table 1, in decibels to subtract.

    The table is printed stepped and integer-indexed, and it is **not** the
    logarithmic subtraction :math:`-10 \lg(1 - 10^{-0,1 \Delta L})` that most
    emission standards use: at a margin of 5 dB it takes off 2 dB where the
    formula takes off 1,7, and at 8 dB it takes off 1 where the formula takes
    off 0,7. It is implemented as printed.

    The table gives no row between its integers. A difference that falls
    between two rows is read at the lower one, which is the larger correction
    and therefore the lower source level; the standard does not decide this,
    and the choice is stated here rather than smoothed away. Above
    :data:`ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB` there is no row to read
    at all: 10 dB is the last one the table prints, and anything over it takes
    nothing off, so 10,5 dB is corrected by zero rather than by the 0,5 dB of
    the 10 dB row.

    :param level_difference_db: The difference between the level measured with
        the source running and the background level alone, in decibels.
    :return: The correction to subtract, in decibels.
    :raises ValueError: For a margin under
        :data:`ISO11820_MINIMUM_BACKGROUND_MARGIN_DB`, which Table 1 calls invalid.
    """
    margin = require_finite_array(level_difference_db, "level_difference_db")
    if float(np.min(margin)) < ISO11820_MINIMUM_BACKGROUND_MARGIN_DB:
        msg = (
            f"Table 1 of ISO 11820 calls a margin under "
            f"{ISO11820_MINIMUM_BACKGROUND_MARGIN_DB:g} dB invalid; the smallest is "
            f"{float(np.min(margin)):.1f} dB. Only the inequality of clause 4 "
            "may be stated."
        )
        raise ValueError(msg)
    # The threshold is read before the table, not after flooring it: Table 1
    # prints 0,5 dB against a margin of 10 dB and nothing above it, so a margin
    # of 10,5 dB is one the standard corrects by nothing, not a 10 dB row.
    rows = np.floor(margin).astype(int)
    return np.asarray(
        [
            0.0
            if value > ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB
            else ISO11820_BACKGROUND_CORRECTIONS_DB[row]
            for value, row in zip(margin.tolist(), rows.tolist(), strict=True)
        ],
        dtype=np.float64,
    )


def mean_sound_pressure_level_db(levels_db: ArrayLike) -> float:
    r"""The mean level over the measuring points, Equation (2).

    .. math::

       \overline{L_p} = 10 \lg \left(\frac{1}{N} \sum_j 10^{0,1 L_{pj}}\right)

    An energy mean, which is what every clause of the standard means by "mean
    sound pressure level".

    :param levels_db: The levels at the measuring points, in decibels.
    :return: :math:`\overline{L_p}`, in decibels.
    :raises ValueError: For an empty or non-finite set of levels.
    """
    values = require_finite_array(levels_db, "levels_db")
    return float(energy_mean(values))


def extraneous_corrected_mean_level_db(
    levels_db: ArrayLike, extraneous_levels_db: ArrayLike
) -> tuple[float, bool]:
    r"""The mean level with the extraneous sound taken off, Equations (17) and (18).

    .. math::

       \overline{L_p} = 10 \lg \left[\frac{1}{N} \sum_j
       \left(10^{0,1 L_{pj}} - 10^{0,1 L_{ej}}\right)\right]

    The energy route 9.1.1 and 9.1.2 offer instead of Table 1, for the case
    where the sources the silencer works on can be switched off and the
    extraneous sound measured at the same positions: corrections are made
    "using table 1 or the relationship" (9.1.1, printed folio 10, PDF page 18
    of BS EN ISO 11820:1997).

    The clause caps it: **the maximum correction is 3 dB**. Past that the
    quantity is not determined, and what may be stated instead is the
    inequality of clause 4. Clause 4.1 (folio 4, PDF page 12) ties that to a
    correction of 3 dB that "is not sufficient", and Table 1 (folio 5, PDF
    page 13) prints where that starts: a margin under 3 dB is invalid, and a
    margin of 3 dB takes off 3 dB. The subtraction reaches 3,0206 dB at that
    same margin, which is the printed 3 dB unrounded, so the cap is judged on
    the margin of the two energy means:

    .. math::

       \overline{L_p} - \overline{L_e} \ge 3\ \mathrm{dB}

    That is the same condition as a correction of at most
    :math:`-10 \lg(1 - 10^{-0,3})` dB, and it keeps the two routes of the
    standard in agreement at their shared boundary. A margin that floating
    point leaves a few parts in :math:`10^{14}` under 3 dB counts as 3 dB.

    The second return value says whether the cap was reached, so that a
    capped number cannot be written down as a determination, and a capped
    measurement also emits a :class:`SilencerInSituWarning`. The corrected
    level itself is returned either way.

    :param levels_db: The levels with everything running, in decibels.
    :param extraneous_levels_db: The extraneous levels at the same positions,
        in decibels.
    :return: The corrected mean level in decibels, and whether the correction
        reached the cap, which is a margin under 3 dB.
    :raises ValueError: For inputs that do not match point for point, or an
        extraneous level at or above the level it is subtracted from.
    """
    levels = require_finite_array(levels_db, "levels_db")
    extraneous = require_finite_array(extraneous_levels_db, "extraneous_levels_db")
    if levels.shape != extraneous.shape:
        msg = "'levels_db' and 'extraneous_levels_db' must match point for point."
        raise ValueError(msg)
    difference = 10.0 ** (0.1 * levels) - 10.0 ** (0.1 * extraneous)
    if np.any(difference <= 0.0):
        msg = (
            "An extraneous level at or above the level measured with the "
            "source running leaves no source energy to report; Table 1 calls "
            "that measurement invalid."
        )
        raise ValueError(msg)
    corrected = float(10.0 * np.log10(np.mean(difference)))
    # The cap is judged on the margin of the two energy means and not on the
    # correction itself: the printed 3 dB is what Table 1 takes off at its
    # 3 dB row, which the subtraction writes unrounded as 3,0206 dB. The
    # tolerance keeps a printed 3,0 dB margin, which the two means can land a
    # few parts in 10^14 under, on the side Table 1 accepts.
    margin = float(energy_mean(levels)) - float(energy_mean(extraneous))
    capped = margin < ISO11820_MINIMUM_BACKGROUND_MARGIN_DB and not math.isclose(
        margin,
        ISO11820_MINIMUM_BACKGROUND_MARGIN_DB,
        rel_tol=0.0,
        abs_tol=_MARGIN_TOLERANCE_DB,
    )
    if capped:
        msg = (
            "ISO 11820 caps the extraneous correction at "
            f"{MAXIMUM_EXTRANEOUS_CORRECTION_DB:g} dB (9.1.1 and 9.1.2), the "
            "correction Table 1 applies at its "
            f"{ISO11820_MINIMUM_BACKGROUND_MARGIN_DB:g} dB row; this measurement "
            f"stands {margin:.2f} dB over the extraneous sound, so the level is "
            "not determined and only the inequality of clause 4 may be stated."
        )
        warnings.warn(msg, SilencerInSituWarning, stacklevel=2)
    return corrected, capped


def transmission_level_difference_db(
    source_levels_db: ArrayLike, receiver_levels_db: ArrayLike
) -> NDArray[np.float64]:
    r"""The level difference across the silencer, Equation (1).

    :math:`D_{tps} = \overline{L_{p2}} - \overline{L_{p1}}`, the mean level on
    the source side less the mean level on the receiver side. The arguments
    are named for the side rather than for the subscript, because 1 is the
    receiver and 2 the source, which is the opposite of the order most readers
    expect.

    NOTE 2 of 3.1: this is not a result of its own but the step Equation (19)
    turns into a transmission loss.

    :param source_levels_db: :math:`\overline{L_{p2}}` per band, in decibels.
    :param receiver_levels_db: :math:`\overline{L_{p1}}` per band, in decibels.
    :return: :math:`D_{tps}` per band, in decibels.
    :raises ValueError: For spectra that do not match band for band.
    """
    source = require_finite_array(source_levels_db, "source_levels_db")
    receiver = require_finite_array(receiver_levels_db, "receiver_levels_db")
    if source.shape != receiver.shape:
        msg = "'source_levels_db' and 'receiver_levels_db' must match band for band."
        raise ValueError(msg)
    return np.asarray(source - receiver, dtype=np.float64)


def insertion_level_difference_db(
    levels_without_db: ArrayLike, levels_with_db: ArrayLike
) -> NDArray[np.float64]:
    r"""The level difference the silencer made, Equation (3).

    :math:`D_{ips} = L_{pII} - L_{pI}`, the level before the silencer was
    installed less the level after. Here II is *without* and I is *with*,
    which is again the opposite of the reading order, so the arguments say
    which run they are.

    :param levels_without_db: :math:`L_{pII}` per band, in decibels.
    :param levels_with_db: :math:`L_{pI}` per band, in decibels.
    :return: :math:`D_{ips}` per band, in decibels.
    :raises ValueError: For spectra that do not match band for band.
    """
    without = require_finite_array(levels_without_db, "levels_without_db")
    with_ = require_finite_array(levels_with_db, "levels_with_db")
    if without.shape != with_.shape:
        msg = "'levels_without_db' and 'levels_with_db' must match band for band."
        raise ValueError(msg)
    return np.asarray(without - with_, dtype=np.float64)


def reverberant_surface_area_m2(
    volume_m3: float,
    reverberation_time_s: ArrayLike,
    *,
    speed_of_sound: float = ISO11820_SOUND_SPEED_M_S,
) -> NDArray[np.float64]:
    r"""A quarter of the room absorption, as an area, Equations (6), (10) and (12).

    .. math::

       S = \frac{6 \ln 10 \; V}{c \, T}

    The three equations are the same expression written three times, for the
    receiver room of the transmission measurement and for the room with and
    without the silencer of the insertion one. It is a quarter of the Sabine
    equivalent absorption area, which is what turns a reverberant level into a
    sound power.

    The standard prints :math:`c = 340` m/s "at room temperature"; that value
    is the default here and a measurement at another temperature should say
    so.

    :param volume_m3: The room volume, in cubic metres.
    :param reverberation_time_s: The reverberation time per band, in seconds.
    :param speed_of_sound: The speed of sound, in metres per second.
    :return: The area, in square metres.
    :raises ValueError: For a non-positive volume, time or speed.
    """
    volume = require_positive(volume_m3, "volume_m3")
    celerity = require_positive(speed_of_sound, "speed_of_sound")
    times = require_finite_array(reverberation_time_s, "reverberation_time_s")
    if np.any(times <= 0.0):
        msg = "'reverberation_time_s' must be strictly positive."
        raise ValueError(msg)
    return np.asarray(SABINE_AREA_COEFFICIENT * volume / (celerity * times))


def sound_power_level_db(
    mean_level_db: ArrayLike,
    *,
    area_m2: ArrayLike,
    field_correction_db: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    r"""A mean level read as a sound power, Equations (5), (7), (9) and (11).

    .. math::

       L_W = \overline{L_p} + 10 \lg \frac{S}{S_0} + K, \qquad S_0 = 1\ \text{m}^2

    The four equations differ only in which side of the silencer and which run
    they belong to. :math:`S` is whichever area the case calls for, from
    :func:`installation_case`, and :math:`K` the field correction of Annex A,
    which NOTE 4 expects to stay under
    :data:`TYPICAL_FIELD_CORRECTION_LIMIT_DB` in absolute value once the areas
    have been chosen as 3.3 and 3.4 define them.

    :param mean_level_db: :math:`\overline{L_p}` per band, in decibels.
    :param area_m2: :math:`S`, in square metres.
    :param field_correction_db: :math:`K`, in decibels.
    :return: :math:`L_W` per band, in decibels.
    :raises ValueError: For a non-positive area or mismatched shapes.
    """
    levels = require_finite_array(mean_level_db, "mean_level_db")
    area = require_finite_array(area_m2, "area_m2")
    correction = require_finite_array(field_correction_db, "field_correction_db")
    if np.any(area <= 0.0):
        msg = "'area_m2' must be strictly positive."
        raise ValueError(msg)
    if np.max(np.abs(correction)) > TYPICAL_FIELD_CORRECTION_LIMIT_DB:
        msg = (
            "NOTE 4 of ISO 11820 expects the field correction to stay under "
            f"{TYPICAL_FIELD_CORRECTION_LIMIT_DB:g} dB in absolute value once "
            "the areas of 3.3 and 3.4 are chosen; the largest here is "
            f"{float(np.max(np.abs(correction))):.1f} dB."
        )
        warnings.warn(msg, SilencerInSituWarning, stacklevel=2)
    return np.asarray(levels + 10.0 * np.log10(area) + correction, dtype=np.float64)


def temperature_field_correction_db(
    *, receiver_temperature_c: float, source_temperature_c: float
) -> float:
    r"""The field correction difference two temperatures make, Equations (20) and (22).

    .. math::

       K_2 - K_1 = 5 \lg \frac{273 + \theta_1}{273 + \theta_2}

    Unless Annex A gives a reason to say otherwise, the field corrections
    account for markedly different temperatures on the two sides and for
    nothing else. The standard explains the term by the speed of sound alone,
    and that is where the ratio comes out upside down: the factor from squared
    pressure to power is the characteristic impedance, and at one ambient
    pressure the standard's own Equation (29) makes the density fall as
    :math:`1/T` while :math:`c` rises as :math:`\sqrt{T}`, so
    :math:`\rho c` falls as :math:`T^{-1/2}` and the correction rises with
    temperature. The printed form is returned unchanged, because a reader
    holding ISO 11820 has to find the standard's own number; the defect is
    registered in ``docs/ERRATA.md`` under "ISO 11820:1996, Equations (20) and
    (22)".

    The same expression is Equation (22) with the two runs of an insertion
    measurement in place of the two sides: there :math:`\theta_I` is the
    temperature with the silencer and :math:`\theta_{II}` without, and the
    correction it returns is :math:`K_{II} - K_I`. Pass the with-silencer
    temperature as the receiver one and the without-silencer temperature as
    the source one, which is the ordering the two equations share.

    The standard writes 273 rather than 273,15, and that is what is used.

    :param receiver_temperature_c: :math:`\theta_1` on the receiver side, or
        :math:`\theta_I` with the silencer, in degrees Celsius.
    :param source_temperature_c: :math:`\theta_2` on the source side, or
        :math:`\theta_{II}` without the silencer, in degrees Celsius.
    :return: :math:`K_2 - K_1` or :math:`K_{II} - K_I`, in decibels.
    :raises ValueError: For a temperature that is not finite or at or below
        the absolute zero the equation uses.
    """
    receiver = require_finite(receiver_temperature_c, "receiver_temperature_c")
    source = require_finite(source_temperature_c, "source_temperature_c")
    offset = 273.0
    if receiver + offset <= 0.0 or source + offset <= 0.0:
        msg = (
            "Equations (20) and (22) of ISO 11820 divide by 273 plus the "
            "temperature in degrees Celsius, which must stay positive."
        )
        raise ValueError(msg)
    return 5.0 * math.log10((offset + receiver) / (offset + source))


@dataclass(frozen=True)
class SilencerInSituResult:
    r"""A silencer measured where it stands, ISO 11820 Equation (19) or (21).

    :ivar frequencies: Nominal band centres, in hertz, or ``None``.
    :ivar level_difference_db: :math:`D_{tps}` or :math:`D_{ips}`, the sound
        pressure level difference the loss is built on, per band.
    :ivar area_term_db: :math:`10 \lg(S_2/S_1)` or :math:`10 \lg(S_{II}/S_I)`
        per band, in decibels. Always one value per band, even where both areas
        were given as single values, because the area of a diffuse room moves
        with the reverberation time from band to band.
    :ivar field_correction_difference_db: :math:`K_2 - K_1` or
        :math:`K_{II} - K_I` per band, in decibels, on the same shape.
    :ivar loss_db: :math:`D_{ts}` or :math:`D_{is}` per band, in decibels.
    :ivar quantity: ``"transmission"`` or ``"insertion"``.
    :ivar case: The installation of Figure 1 the measurement was made in, or
        ``None`` where the caller did not name one.
    """

    frequencies: NDArray[np.float64] | None
    level_difference_db: NDArray[np.float64]
    area_term_db: NDArray[np.float64]
    field_correction_difference_db: NDArray[np.float64]
    loss_db: NDArray[np.float64]
    quantity: str
    case: InstallationCase | None

    @property
    def symbol(self) -> str:
        """The symbol clause 11 reports this as, ``"D_ts"`` or ``"D_is"``."""
        return "D_ts" if self.quantity == "transmission" else "D_is"

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the level difference and the loss it becomes.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.noise_control.plot_silencer_in_situ`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.noise_control import plot_silencer_in_situ

        check_language(language)
        return plot_silencer_in_situ(self, ax=ax, language=language, **kwargs)


def _per_band(
    values: NDArray[np.float64], name: str, shape: tuple[int, ...]
) -> NDArray[np.float64]:
    """One value per band, from a single value or from one given per band."""
    if values.size != 1 and values.shape != shape:
        msg = f"'{name}' must be one value or match the level difference band for band."
        raise ValueError(msg)
    return np.array(np.broadcast_to(values, shape), dtype=np.float64)


def _loss(
    level_difference: NDArray[np.float64],
    *,
    frequencies: ArrayLike | None,
    source_area_m2: ArrayLike,
    receiver_area_m2: ArrayLike,
    field_correction_difference_db: ArrayLike,
    names: tuple[str, str],
    quantity: str,
    case: InstallationCase | None,
) -> SilencerInSituResult:
    """The body Equations (19) and (21) share.

    ``names`` carries the public names of the two areas, so that a refusal
    names the argument the caller actually passed.
    """
    shape = level_difference.shape
    source_name, receiver_name = names
    source = _per_band(
        require_positive_array(source_area_m2, source_name), source_name, shape
    )
    receiver = _per_band(
        require_positive_array(receiver_area_m2, receiver_name), receiver_name, shape
    )
    correction = _per_band(
        require_finite_array(
            field_correction_difference_db, "field_correction_difference_db"
        ),
        "field_correction_difference_db",
        shape,
    )
    freqs: NDArray[np.float64] | None = None
    if frequencies is not None:
        freqs = require_positive_array(frequencies, "frequencies")
        if freqs.shape != shape:
            msg = "'frequencies' must match the level difference band for band."
            raise ValueError(msg)
    area_term = np.asarray(10.0 * np.log10(source / receiver), dtype=np.float64)
    return SilencerInSituResult(
        frequencies=freqs,
        level_difference_db=level_difference,
        area_term_db=area_term,
        field_correction_difference_db=correction,
        loss_db=np.asarray(level_difference + area_term + correction, dtype=np.float64),
        quantity=quantity,
        case=case,
    )


def in_situ_transmission_loss(
    source_levels_db: ArrayLike,
    receiver_levels_db: ArrayLike,
    *,
    source_area_m2: ArrayLike,
    receiver_area_m2: ArrayLike,
    frequencies: ArrayLike | None = None,
    field_correction_difference_db: ArrayLike = 0.0,
    case: int | None = None,
) -> SilencerInSituResult:
    r"""The transmission loss of a silencer in place, Equation (19).

    .. math::

       D_{ts} = D_{tps} + 10 \lg \frac{S_2}{S_1} + K_2 - K_1

    The level difference of Equation (1), the ratio of the two measurement
    areas, and the difference of the two field corrections.
    :func:`installation_case` says which areas the installation calls for;
    :func:`temperature_field_correction_db` is the correction difference two
    temperatures make.

    Every term is a band quantity (3.3, printed folio 3, PDF page 11). A
    measurement surface in a duct is one area for all bands, but where a side
    is a room with a diffuse field its area is a quarter of the absorption,
    :math:`(6 \ln 10) V / (c T)`, and moves with the reverberation time from
    band to band: pass the array :func:`reverberant_surface_area_m2` returns.
    Each area and the field correction may be one value, applied to every
    band, or one value per band.

    :param source_levels_db: :math:`\overline{L_{p2}}` per band, in decibels.
    :param receiver_levels_db: :math:`\overline{L_{p1}}` per band, in decibels.
    :param source_area_m2: :math:`S_2`, one value or one per band, in square
        metres.
    :param receiver_area_m2: :math:`S_1`, one value or one per band, in square
        metres.
    :param frequencies: Nominal band centres, in hertz.
    :param field_correction_difference_db: :math:`K_2 - K_1`, one value or one
        per band, in decibels.
    :param case: The installation of Figure 1, 1 to 16, carried into the
        result.
    :return: The loss, as a :class:`SilencerInSituResult`.
    :raises ValueError: For spectra that do not match, an area or a field
        correction that is neither one value nor one per band, a non-positive
        area or band centre, a field correction that is not finite, or a case
        that is not a transmission one.
    """
    difference = transmission_level_difference_db(source_levels_db, receiver_levels_db)
    entry = None
    if case is not None:
        entry = installation_case(case)
        if entry.quantity != "transmission":
            msg = (
                f"Case {entry.number} of Figure 1 is an insertion "
                "measurement; Equation (19) is the transmission one."
            )
            raise ValueError(msg)
    return _loss(
        difference,
        frequencies=frequencies,
        source_area_m2=source_area_m2,
        receiver_area_m2=receiver_area_m2,
        field_correction_difference_db=field_correction_difference_db,
        names=("source_area_m2", "receiver_area_m2"),
        quantity="transmission",
        case=entry,
    )


def in_situ_insertion_loss(
    levels_without_db: ArrayLike,
    levels_with_db: ArrayLike,
    *,
    area_without_m2: ArrayLike,
    area_with_m2: ArrayLike,
    frequencies: ArrayLike | None = None,
    field_correction_difference_db: ArrayLike = 0.0,
    case: int | None = None,
) -> SilencerInSituResult:
    r"""The insertion loss of a silencer in place, Equation (21).

    .. math::

       D_{is} = \overline{L_{pII}} - \overline{L_{pI}}
       + 10 \lg \frac{S_{II}}{S_I} + K_{II} - K_I

    The same shape as Equation (19) with the two runs in place of the two
    sides. NOTE 5 of 3.4 says that in most cases the two areas are equal and
    the two field corrections nearly so, and then both terms fall out and the
    loss is the level difference; the arguments are still explicit, because
    "in most cases" is not "always" and cases 17 and 19 of Figure 1 are where
    it fails.

    A blowdown silencer can only be measured this way: there is no duct to
    measure through.

    As in Equation (19), the terms are band quantities (3.4, printed folio 3,
    PDF page 11). Where the receiver side is a diffuse room, case 18 of
    Figure 1, both areas are a quarter of the room absorption, Equations (10)
    and (12), and move band by band with the reverberation time of each run:
    pass the two arrays :func:`reverberant_surface_area_m2` returns. Each area
    and the field correction may be one value, applied to every band, or one
    value per band.

    :param levels_without_db: :math:`\overline{L_{pII}}` per band, in decibels.
    :param levels_with_db: :math:`\overline{L_{pI}}` per band, in decibels.
    :param area_without_m2: :math:`S_{II}`, one value or one per band, in
        square metres.
    :param area_with_m2: :math:`S_I`, one value or one per band, in square
        metres.
    :param frequencies: Nominal band centres, in hertz.
    :param field_correction_difference_db: :math:`K_{II} - K_I`, one value or
        one per band, in decibels.
    :param case: The installation of Figure 1, 17 to 20, carried into the
        result.
    :return: The loss, as a :class:`SilencerInSituResult`.
    :raises ValueError: For spectra that do not match, an area or a field
        correction that is neither one value nor one per band, a non-positive
        area or band centre, a field correction that is not finite, or a case
        that is not an insertion one.
    """
    difference = insertion_level_difference_db(levels_without_db, levels_with_db)
    entry = None
    if case is not None:
        entry = installation_case(case)
        if entry.quantity != "insertion":
            msg = (
                f"Case {entry.number} of Figure 1 is a transmission "
                "measurement; Equation (21) is the insertion one."
            )
            raise ValueError(msg)
    return _loss(
        difference,
        frequencies=frequencies,
        source_area_m2=area_without_m2,
        receiver_area_m2=area_with_m2,
        field_correction_difference_db=field_correction_difference_db,
        names=("area_without_m2", "area_with_m2"),
        quantity="insertion",
        case=entry,
    )


def octave_levels_from_third_octave_db(levels_db: ArrayLike) -> NDArray[np.float64]:
    r"""One-third-octave levels folded into octaves, 9.1.5.

    The energy sum of each consecutive group of three. Clause 9.1.5 permits
    this conversion **for measured sound pressure levels only, but not for
    level differences**, and that sentence is the whole of the clause.

    The prohibition is worth stating twice, because this library does perform
    the forbidden operation for a different standard:
    :func:`phonometry.noise_control.octave_insertion_loss` folds a
    one-third-octave insertion loss into octaves, which is Equation (2) of
    ISO 11691 and is exactly what ISO 11820 forbids. The two are not
    interchangeable: one is a fold of a measured level, the other a fold of a
    difference, and ISO 11820 wants the levels folded on each side and the
    difference taken afterwards.

    :param levels_db: One-third-octave levels, in decibels, a multiple of
        three bands in ascending order.
    :return: The octave levels, in decibels.
    :raises ValueError: For a count that is not a multiple of three.
    """
    values = require_finite_array(levels_db, "levels_db")
    if values.size % _THIRDS_PER_OCTAVE:
        msg = (
            f"An octave is {_THIRDS_PER_OCTAVE} one-third-octave bands, so the "
            f"count must be a multiple of {_THIRDS_PER_OCTAVE}; got "
            f"{values.size}."
        )
        raise ValueError(msg)
    grouped = values.reshape(-1, _THIRDS_PER_OCTAVE)
    return np.asarray(
        10.0 * np.log10(np.sum(10.0 ** (0.1 * grouped), axis=1)), dtype=np.float64
    )


def total_pressure_loss_pa(
    upstream_total_pressure_pa: float, downstream_total_pressure_pa: float
) -> float:
    r"""The total pressure loss of the silencer, Equation (13).

    :math:`\Delta p_T = \overline{p_{Tu}} - \overline{p_{Td}}`, the mean total
    pressure upstream less the mean total pressure downstream, each of them
    the arithmetic mean of Equations (23) and (25). Where the inlet and outlet
    areas are equal and neither temperature nor density changes much, this is
    also the static pressure difference.

    :param upstream_total_pressure_pa: :math:`\overline{p_{Tu}}`, in pascals,
        as a difference from the ambient pressure.
    :param downstream_total_pressure_pa: :math:`\overline{p_{Td}}`, in
        pascals, on the same basis.
    :return: :math:`\Delta p_T`, in pascals.
    """
    return require_finite(
        upstream_total_pressure_pa, "upstream_total_pressure_pa"
    ) - require_finite(downstream_total_pressure_pa, "downstream_total_pressure_pa")


def static_pressure_difference_pa(
    total_pressure_loss_pa: float,
    *,
    volume_flow_m3_s: float,
    density_kg_m3: float,
    upstream_area_m2: float,
    downstream_area_m2: float,
) -> float:
    r"""The static pressure difference behind a change of area, Equation (14).

    .. math::

       \Delta p_S = \Delta p_T - \frac{\rho \, q_V^2}{2}
       \left(\frac{1}{S_u^2} - \frac{1}{S_d^2}\right)

    For a silencer whose inlet and outlet areas differ, where the gas
    temperature does not vary markedly. With equal areas the bracket vanishes
    and the two pressure differences are the same number, which is what 3.5
    says in words.

    :param total_pressure_loss_pa: :math:`\Delta p_T`, in pascals.
    :param volume_flow_m3_s: :math:`q_V`, in cubic metres per second.
    :param density_kg_m3: :math:`\rho`, in kilograms per cubic metre.
    :param upstream_area_m2: :math:`S_u`, in square metres.
    :param downstream_area_m2: :math:`S_d`, in square metres.
    :return: :math:`\Delta p_S`, in pascals.
    :raises ValueError: For a value that is not finite, or a non-positive
        density or area.
    """
    density = require_positive(density_kg_m3, "density_kg_m3")
    upstream = require_positive(upstream_area_m2, "upstream_area_m2")
    downstream = require_positive(downstream_area_m2, "downstream_area_m2")
    flow = require_finite(volume_flow_m3_s, "volume_flow_m3_s")
    loss = require_finite(total_pressure_loss_pa, "total_pressure_loss_pa")
    bracket = 1.0 / upstream**2 - 1.0 / downstream**2
    return loss - density * flow**2 / 2.0 * bracket


def measurement_distance_upstream_m(upstream_area_m2: float) -> float:
    r"""How far upstream the measurement surface stands, Equation (15).

    :math:`d_u = 1,5 \sqrt{4 S_u / \pi}`, which is one and a half equivalent
    diameters of the upstream measurement cross-section.

    :param upstream_area_m2: :math:`S_u`, in square metres.
    :return: :math:`d_u`, in metres.
    :raises ValueError: For a non-positive area.
    """
    area = require_positive(upstream_area_m2, "upstream_area_m2")
    return UPSTREAM_DISTANCE_DIAMETERS * math.sqrt(4.0 * area / math.pi)


def measurement_distance_downstream_m(
    downstream_area_m2: float, free_area_m2: float
) -> float:
    r"""How far downstream the measurement surface stands, Equation (16).

    :math:`d_d = 12 \sqrt{S_d} - 10 \sqrt{S_f}`, with :math:`S_f` the free
    cross-sectional area of the silencer, which NOTE 18 warns is not the same
    thing as its total intake cross-section.

    The expression can return zero or less for a silencer whose free area is a
    large fraction of the duct it sits in. 8.3.1 has its own escape for that,
    which is agreement between the parties on the distances, and the case is
    reported rather than returned as a distance nobody can stand at.

    :param downstream_area_m2: :math:`S_d`, in square metres.
    :param free_area_m2: :math:`S_f`, in square metres.
    :return: :math:`d_d`, in metres.
    :raises ValueError: For a non-positive area.
    """
    downstream = require_positive(downstream_area_m2, "downstream_area_m2")
    free = require_positive(free_area_m2, "free_area_m2")
    first, second = DOWNSTREAM_DISTANCE_COEFFICIENTS
    distance = first * math.sqrt(downstream) - second * math.sqrt(free)
    if distance <= 0.0:
        msg = (
            "Equation (16) of ISO 11820 returns a distance of "
            f"{distance:.2f} m for this free area, which is no distance at "
            "all; 8.3.1 sends that case to agreement between the parties."
        )
        warnings.warn(msg, SilencerInSituWarning, stacklevel=2)
    return distance


def velocity_pressure_pa(
    total_pressure_pa: ArrayLike, static_pressure_pa: ArrayLike
) -> NDArray[np.float64]:
    r"""The velocity pressure, Equation (27).

    :math:`p_v = p_T - p_S`, the total pressure less the static pressure, both
    reported as differences from the ambient atmospheric pressure as 8.3.2
    asks.

    :param total_pressure_pa: :math:`p_T`, in pascals.
    :param static_pressure_pa: :math:`p_S`, in pascals.
    :return: :math:`p_v`, in pascals.
    :raises ValueError: For inputs that do not match.
    """
    total = require_finite_array(total_pressure_pa, "total_pressure_pa")
    static = require_finite_array(static_pressure_pa, "static_pressure_pa")
    if total.shape != static.shape:
        msg = "'total_pressure_pa' and 'static_pressure_pa' must match."
        raise ValueError(msg)
    return np.asarray(total - static, dtype=np.float64)


def flow_velocity_m_s(
    velocity_pressure_pa: ArrayLike, density_kg_m3: float
) -> NDArray[np.float64]:
    r"""The flow velocity a velocity pressure stands for, Equation (28).

    :math:`w = \sqrt{2 p_v / \rho}`.

    :param velocity_pressure_pa: :math:`p_v`, in pascals.
    :param density_kg_m3: :math:`\rho`, in kilograms per cubic metre.
    :return: :math:`w`, in metres per second.
    :raises ValueError: For a non-positive density or a negative velocity
        pressure.
    """
    pressure = require_finite_array(velocity_pressure_pa, "velocity_pressure_pa")
    density = require_positive(density_kg_m3, "density_kg_m3")
    if np.any(pressure < 0.0):
        msg = "'velocity_pressure_pa' must not be negative; the root has no real value."
        raise ValueError(msg)
    return np.asarray(np.sqrt(2.0 * pressure / density), dtype=np.float64)


def gas_density_kg_m3(
    *,
    temperature_c: float,
    molar_mass_kg_kmol: float | None = None,
    ambient_pressure_pa: float = ISO11820_AMBIENT_PRESSURE_PA,
) -> float:
    r"""The density of the gas, Equation (29).

    .. math::

       \rho = \frac{M \, p_{\text{amb}}}{R \, (273 + \theta)}

    with :math:`R` the universal gas constant, printed as 8 314,4 N m per
    kmol K, and :math:`M` the molar mass. The standard adds that
    :math:`R/M = 287` N m per kg K for air, and that is what is used when no
    molar mass is given.

    :func:`phonometry.noise_control.normal_air_density` computes the same
    quantity for ISO 7235, from a gauge pressure and with that standard's own
    two constants; this one takes the absolute ambient pressure the way
    Equation (29) prints it and admits any gas through its molar mass.

    :param temperature_c: :math:`\theta`, in degrees Celsius.
    :param molar_mass_kg_kmol: :math:`M`, in kilograms per kilomole. Omit it
        for air.
    :param ambient_pressure_pa: :math:`p_{\text{amb}}`, in pascals.
    :return: :math:`\rho`, in kilograms per cubic metre.
    :raises ValueError: For a temperature that is not finite or at or below
        the absolute zero the equation uses, or a non-positive pressure or
        molar mass.
    """
    pressure = require_positive(ambient_pressure_pa, "ambient_pressure_pa")
    absolute = 273.0 + require_finite(temperature_c, "temperature_c")
    if absolute <= 0.0:
        msg = (
            "Equation (29) of ISO 11820 divides by 273 plus the temperature "
            "in degrees Celsius, which must stay positive."
        )
        raise ValueError(msg)
    if molar_mass_kg_kmol is None:
        return pressure / (ISO11820_AIR_GAS_CONSTANT * absolute)
    molar_mass = require_positive(molar_mass_kg_kmol, "molar_mass_kg_kmol")
    return molar_mass * pressure / (ISO11820_GAS_CONSTANT * absolute)


def silencer_flow_velocity_m_s(
    upstream_mean_velocity_m_s: float,
    *,
    upstream_area_m2: float,
    free_area_m2: float,
) -> float:
    r"""The mean velocity inside the silencer, Equation (31).

    :math:`\overline{w_f} = (S_u / S_f) \, \overline{w_u}`, the upstream mean
    velocity scaled by how much the silencer narrows the passage. It is the
    velocity the regenerated noise of the installation answers to, which is
    why 9.2 asks for it rather than for the duct velocity.

    :param upstream_mean_velocity_m_s: :math:`\overline{w_u}`, in metres per
        second, the arithmetic mean of Equation (30).
    :param upstream_area_m2: :math:`S_u`, in square metres.
    :param free_area_m2: :math:`S_f`, the free cross-section, in square
        metres.
    :return: :math:`\overline{w_f}`, in metres per second.
    :raises ValueError: For a non-positive area.
    """
    upstream = require_positive(upstream_area_m2, "upstream_area_m2")
    free = require_positive(free_area_m2, "free_area_m2")
    mean_velocity = require_finite(
        upstream_mean_velocity_m_s, "upstream_mean_velocity_m_s"
    )
    return mean_velocity * upstream / free
