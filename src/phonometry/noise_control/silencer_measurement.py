#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Insertion loss of a ducted silencer, measured by substitution.

Everything a silencer model computes comes from geometry. The figure a
supplier publishes does not: it is an **insertion loss measured by
substitution**, and this module is the arithmetic of that measurement.

Three standards describe how a duct element is measured in a laboratory. Two
of them share the substitution method and differ only in how much rigour they
ask:

* **ISO 7235:2003** (published in Europe as EN ISO 7235:2009) is the full
  procedure, with a modal filter between the source and the test object, a
  qualified receiving side, and a stated measurement uncertainty. It covers
  silencers, air-terminal units and other duct elements, with and without
  flow.
* **ISO 11691:1995** (EN ISO 11691:2009) is the survey-grade laboratory
  method, six printed pages carrying two equations. It measures silencers and
  nothing else, without flow and with none in the answer, up to a design
  velocity of 15 m/s. A measurement that needs flow, or an object that is not
  a silencer, is outside it and belongs to ISO 7235.

The third measures a different quantity by a different route.
**ISO 5135:1999** (EN ISO 5135:1998) determines the sound power an
air-terminal device, air-terminal unit, damper or valve radiates, in a
reverberation room to ISO 3741, and hands back the power in the duct behind
it with the end reflection loss of its Equation (2). That equation is
Equation (B.3) of ISO 7235 written out again, character for character, and
its solid-angle table is Table B.1: :func:`open_end_transmission_loss` is
both. What ISO 5135 adds of its own is :func:`fit_operating_line`, the
straight line 5.5.2 fits through the test points so that a level can be read
off at a duty the laboratory did not measure at.

The measurement is the same subtraction in both. Run the rig once with a
plain **substitution duct** in place of the silencer, run it again with the
silencer installed, and take the difference band by band:

.. math::

   D_\mathrm{i} = L_{W\mathrm{II}} - L_{W\mathrm{I}}

where :math:`\mathrm{I}` is the series with the test object and
:math:`\mathrm{II}` the series with the substitution duct. ISO 11691 writes
the same thing as :math:`D = L_{p1} - L_{p2}` with the substitution duct
first, and ISO 7235 6.3 adds the reverberation-time term
:math:`10 \lg(T_2 / T_1)` when the receiving room's absorption moved between
the two series. :func:`substitution_insertion_loss` is all three.

What the subtraction is **not** is a transmission loss. It is measured
against a particular substitution duct in a particular rig, so it carries
the rig with it: the flanking path along the duct walls sets a **limiting
insertion loss** the facility cannot measure past, and the receiving side
decides how much of the sound the microphones see at all. A catalogue
figure is a claim about the arrangement as much as about the device, which
is why ISO 7235 makes the arrangement reportable.

The rest of the module is the bookkeeping that goes with the subtraction:

* :func:`octave_insertion_loss` folds three one-third-octave values into
  the octave that contains them, which ISO 11691 does on the transmitted
  energy rather than on the decibels;
* :func:`microphone_spread_limit` and
  :func:`microphone_positions_required` are ISO 7235 Table 6, the rule that
  sends a test duct from three microphone positions to five;
* :func:`survey_reproducibility`, :func:`measurement_reproducibility` and
  :func:`measurement_expanded_uncertainty` are the two standards' own answers to how
  repeatable any of this is.

The open end of the duct is the other half. A duct radiating into a room does
not hand the room everything that reaches its mouth: at low frequency the
mouth is a poor radiator and reflects most of the energy back up the duct.
:func:`open_end_transmission_loss` is Equation (B.3), which is what stands
between the level measured in a reverberation room and the level travelling
in the duct, and it is needed twice over: by the transmission loss of
Equation (6) and by the flow-noise sound power of Equation (7).

The plane-wave modelling this measurement is compared against lives in
:mod:`phonometry.noise_control.silencers`, and the cut-on frequency above
which a duct stops carrying plane waves alone is in
:mod:`phonometry.noise_control.duct_modes`.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.validation import (
    require_choice,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "CIRCULAR_CUT_ON_COEFFICIENT",
    "DENSITY_RATIO_RANGE",
    "EXTRAPOLATION_MAX_DEVIATION_DB",
    "EXTRAPOLATION_RANGE_FACTORS",
    "ISO11691_REPRODUCIBILITY",
    "ISO7235_ABSOLUTE_ZERO_OFFSET",
    "ISO7235_COVERAGE_FACTOR",
    "ISO7235_GAS_CONSTANT",
    "ISO7235_REPRODUCIBILITY",
    "ISO7235_SPREAD_LIMITS",
    "MINIMUM_FLOW_RATES",
    "MINIMUM_PRESSURE_DIFFERENCE_PA",
    "MODAL_FILTER_ATTENUATION_DB",
    "OperatingLine",
    "RADIATION_SOLID_ANGLES",
    "RECTANGULAR_CUT_ON_COEFFICIENT",
    "REPORTING_RESOLUTION_DB",
    "SURVEY_AREA_RATIO_RANGE",
    "SURVEY_BAND_RANGE_HZ",
    "SURVEY_DIAMETER_RANGE_M",
    "SURVEY_MAX_VELOCITY_M_S",
    "SilencerMeasurementWarning",
    "UPSTREAM_STRAIGHT_DIAMETERS",
    "UPSTREAM_STRAIGHT_MIN_M",
    "VELOCITY_PROFILE_TOLERANCE_PERCENT",
    "average_pressure_loss_coefficient",
    "duct_sound_power_level",
    "dynamic_pressure",
    "fit_operating_line",
    "flow_noise_power_level",
    "measured_transmission_loss",
    "measurement_expanded_uncertainty",
    "measurement_reproducibility",
    "microphone_positions_required",
    "microphone_spread_limit",
    "modal_filter_cut_on",
    "normal_air_density",
    "octave_insertion_loss",
    "open_end_reflection_coefficient",
    "open_end_transmission_loss",
    "pressure_loss_coefficient",
    "substitution_area_ratio",
    "substitution_insertion_loss",
    "survey_reproducibility",
    "total_pressure",
    "total_pressure_loss",
    "upstream_straight_length",
    "volume_flow_rate",
]

#: ISO 11691:1995, 4.5. The cross-sectional area of the test duct divided by
#: that of the silencer or the substitution duct has to lie in this range;
#: inside it, transition elements between the duct and the silencer may be
#: used. :func:`substitution_area_ratio` checks it.
SURVEY_AREA_RATIO_RANGE: tuple[float, float] = (0.6, 1.7)

#: ISO 11691:1995, 1.1. The survey method is for silencers whose design
#: velocity does not exceed this, in m/s, because it does not include the
#: self-generated flow noise: the rig is run without flow at all.
SURVEY_MAX_VELOCITY_M_S = 15.0

#: ISO 11691:1995, 1.1. The circular diameters the survey method is intended
#: for, in m, and the range within which a rectangular silencer's
#: cross-sectional area is expected to fall.
SURVEY_DIAMETER_RANGE_M: tuple[float, float] = (0.080, 2.0)

#: ISO 11691:1995, clause 5, and ISO 7235:2003, 6.1. Both standards measure
#: in one-third-octave bands over this range, in Hz. Frequencies outside a
#: qualified environment may still be reported as long as they are marked.
SURVEY_BAND_RANGE_HZ: tuple[float, float] = (50.0, 10000.0)

#: ISO 11691:1995, Table 1. Estimated reproducibility standard deviation of
#: the survey method, in dB, as ``(upper band centre in Hz, sigma_R)`` pairs
#: read in order. ISO 11691 gives no interlaboratory result of its own and
#: states only that its ``sigma_R`` should be comparable to that of ISO 7235.
ISO11691_REPRODUCIBILITY: tuple[tuple[float, float], ...] = (
    (1250.0, 2.0),
    (10000.0, 3.0),
)

#: ISO 7235:2003, Table 6. The largest difference, in dB, tolerated between
#: the highest and the lowest of three microphone positions in a test duct
#: before five positions are required, as ``(band centre in Hz, limit)``.
#:
#: The printed table names the bands 50, 63, 80, 100 and 125 Hz and then
#: ``> 160`` Hz, so the 160 Hz one-third octave falls between the rows and is
#: given no limit at all. Every other row names a single band, and 160 Hz is
#: a one-third-octave centre like the rest, so the last row is read here as
#: "160 Hz and above". The gap is registered in ``docs/ERRATA.md``.
ISO7235_SPREAD_LIMITS: tuple[tuple[float, float], ...] = (
    (50.0, 10.0),
    (63.0, 10.0),
    (80.0, 8.0),
    (100.0, 8.0),
    (125.0, 7.0),
    (160.0, 6.0),
)

#: ISO 7235:2003, Table 7. Estimated reproducibility standard deviation, in
#: dB, keyed by quantity and read as ``(upper band centre in Hz, sigma_R)``
#: pairs in order.
#:
#: The insertion-loss column comes from tests on 1 m long parallel-baffle
#: silencers; the other two are estimates based on experience (7.9). The
#: sound-intensity column is qualified by a footnote limiting it to 5 000 Hz,
#: which is why its last pair stops there rather than at 10 000 Hz.
ISO7235_REPRODUCIBILITY: dict[str, tuple[tuple[float, float], ...]] = {
    "insertion_loss": (
        (100.0, 1.5),
        (500.0, 1.0),
        (1250.0, 2.0),
        (10000.0, 3.0),
    ),
    "transmission_loss": (
        (100.0, 3.0),
        (500.0, 3.0),
        (1250.0, 3.0),
        (10000.0, 3.0),
    ),
    "intensity": (
        (100.0, 3.0),
        (500.0, 1.5),
        (1250.0, 1.0),
        (5000.0, 1.0),
    ),
}

#: ISO 7235:2003, 7.9. The expanded uncertainty for a coverage probability of
#: 95 % is twice the reproducibility standard deviation of Table 7.
ISO7235_COVERAGE_FACTOR = 2.0

#: ISO 7235:2003, Table B.1, and the identical Table 1 of ISO 5135:1999. The
#: solid angle of radiation at a duct end, in sr, for the five configurations
#: of Figure B.2: **A** flush in a wall, **B** at the junction of a wall and
#: the floor, **C** a duct end projecting into the room, **D** a box standing
#: on the floor, **E** a duct in the middle of the room.
RADIATION_SOLID_ANGLES: dict[str, float] = {
    "A": 2.0 * math.pi,
    "B": math.pi,
    "C": 4.0 * math.pi,
    "D": 2.0 * math.pi,
    "E": 4.0 * math.pi,
}

#: ISO 7235:2003, 5.2.2.3. The longitudinal attenuation of the fundamental
#: mode the modal filter has to provide, in dB: at least the first at the
#: low-frequency end, and at least the second above the cut-on frequency of
#: the higher-order modes in the connected ducts.
MODAL_FILTER_ATTENUATION_DB: tuple[float, float] = (3.0, 5.0)

#: ISO 7235:2003, Equation (4). The coefficient of the cut-on frequency of the
#: first higher-order mode of a circular duct, ``f = 0,59 c / d``. The exact
#: value is the first zero of the derivative of the Bessel function of order
#: one, 1,8412 / pi = 0,58607, so the printed constant sits 0,67 % high.
CIRCULAR_CUT_ON_COEFFICIENT = 0.59

#: ISO 7235:2003, Equation (5). The same for a rectangular duct of larger
#: dimension ``H``, ``f = 0,5 c / H``. This one is exact: the first mode is a
#: half wavelength across the duct.
RECTANGULAR_CUT_ON_COEFFICIENT = 0.5

#: The speed of sound in air the two standards work at, in m/s. ISO 7235 B.2.3
#: writes 340 m/s into its two-microphone spacing rule; the value here is the
#: library's own 20 degree Celsius figure, and every function that uses it
#: takes a ``sound_speed`` argument.
_SOUND_SPEED_M_S = 343.0

#: ISO 7235:2003, Equation (10). The specific gas constant of air as the
#: standard prints it, in N·m/(kg·K). The accurate value for dry air is
#: 287,05; the printed 287 is 0,017 % low, which with the temperature offset
#: scales a pressure loss coefficient by 0,069 % rather than shifting it.
ISO7235_GAS_CONSTANT = 287.0

#: ISO 7235:2003, Equations (10), (21) and (22). The offset the standard adds
#: to a Celsius temperature to get an absolute one, in degrees. It prints 273
#: rather than 273,15, which puts a density 0,051 % high at 20 °C; the value
#: is kept as printed so that a result can be reproduced as the standard
#: gives it.
ISO7235_ABSOLUTE_ZERO_OFFSET = 273.0

#: ISO 7235:2003, 6.5.2.1. The window the density ratio between the flow
#: meter and the test object may sit in before Equation (9) has to replace
#: Equation (8): outside it the meter is not measuring the flow the test
#: object sees.
DENSITY_RATIO_RANGE: tuple[float, float] = (0.98, 1.02)

#: ISO 7235:2003, 6.5.2.1. The pressure difference, in Pa, the lowest of the
#: airflow rates has to exceed, so that the smallest number in the fit is
#: still a measurement.
MINIMUM_PRESSURE_DIFFERENCE_PA = 10.0

#: ISO 7235:2003, 6.5.2.1 and 6.5.2.2.1. How many airflow rates each series
#: is measured at, spread evenly over the test range.
MINIMUM_FLOW_RATES = 5

#: ISO 7235:2003, 6.5.2.2.1. The upstream test duct is straight for at least
#: this many equivalent diameters, or the length below, whichever is greater.
UPSTREAM_STRAIGHT_DIAMETERS = 5.0

#: ISO 7235:2003, 6.5.2.2.1. The floor on that straight length, in m.
UPSTREAM_STRAIGHT_MIN_M = 2.0

#: ISO 7235:2003, 6.5.2.2.1. How uniform the velocity profile has to be near
#: the upstream connection, as a percentage of the mean over the cross
#: section, excluding the 15 mm nearest the walls.
VELOCITY_PROFILE_TOLERANCE_PERCENT = 10.0

#: ISO 5135:1999, 5.5.2. The largest distance, in dB, a measured point may
#: sit from the least-squares line fitted through the test points before the
#: fit stops being a straight line in that variable.
EXTRAPOLATION_MAX_DEVIATION_DB = 3.0

#: ISO 5135:1999, 5.5.2. How far outside the measured duties the fitted line
#: may be read: down to half the smallest and up to twice the largest.
EXTRAPOLATION_RANGE_FACTORS: tuple[float, float] = (0.5, 2.0)

#: ISO 5135:1999, 8 k). The resolution the fully corrected sound power levels
#: are tabulated or plotted to, in dB.
REPORTING_RESOLUTION_DB = 0.5

_MINIMUM_FIT_POINTS = 2

_THIRDS_PER_OCTAVE = 3


class SilencerMeasurementWarning(PhonometryWarning):
    """A substitution measurement is outside the range its method covers.

    Raised when a test arrangement falls outside a limit the standard writes
    down but does not make an error: an area ratio outside the 0,6 to 1,7 of
    ISO 11691 4.5, or a band outside the 50 Hz to 10 kHz both standards
    measure over. The arithmetic still runs, because a laboratory may report
    such a value as long as it says so.
    """


def _require_finite_scalar(value: float, name: str) -> float:
    """One finite number, and not the first of several.

    ``require_finite_array`` accepts a scalar and a sequence alike, and
    taking ``[0]`` of the result reads the first element of a sequence and
    drops the rest without a word. A static pressure or a temperature is one
    measurement in one plane, so a sequence is a mistake and is said to be
    one.
    """
    values = require_finite_array(value, name)
    if values.size != 1:
        msg = (
            f"'{name}' is one measurement in one plane, so one number is "
            f"expected; got {values.size}."
        )
        raise ValueError(msg)
    return float(values[0])


def _require_matching_bands(
    counts: dict[str, int], *, broadcast: dict[str, int] | None = None
) -> None:
    """Every band-indexed argument of one call describes the same bands.

    ``counts`` holds the arguments that carry one value per band; they have
    to agree exactly, because a level given for one band and a loss given for
    six are not a measurement of anything.

    ``broadcast`` holds the arguments a laboratory may reasonably measure
    once for a whole run rather than band by band, such as a reverberation
    time or the room correction of Equation (7). Those may be a single value
    or one per band, and nothing in between. Letting a singleton anywhere
    silently set the length is what turns one measured level and two
    reverberation times into two answers.
    """
    listed = dict(counts) | dict(broadcast or {})
    if len(set(counts.values())) > 1:
        _raise_band_mismatch(listed)
    bands = next(iter(counts.values()))
    for size in (broadcast or {}).values():
        if size not in (1, bands):
            _raise_band_mismatch(listed)


def _raise_band_mismatch(counts: dict[str, int]) -> None:
    """Report which argument brought how many bands, and stop."""
    listed = ", ".join(f"'{name}' has {size}" for name, size in counts.items())
    msg = (
        "The arguments of one measurement describe the same bands, so they "
        f"need one length, and only a value measured once for the whole run "
        f"may be given on its own; {listed}."
    )
    raise ValueError(msg)


def substitution_insertion_loss(
    substitution_level: ArrayLike,
    object_level: ArrayLike,
    *,
    reverberation_times: tuple[ArrayLike, ArrayLike] | None = None,
) -> NDArray[np.float64]:
    r"""The insertion loss of the two test series, band by band.

    .. math::

       D_\mathrm{i} = L_{W\mathrm{II}} - L_{W\mathrm{I}}
                    \quad\text{and}\quad
       D_\mathrm{i} = \overline{L_{p1}} - \overline{L_{p2}}
                      + 10 \lg \frac{T_2}{T_1}\ \text{dB}

    Both printings are the same subtraction: the level measured **without**
    the test object minus the level measured **with** it. ISO 7235 numbers
    the series so that :math:`\mathrm{I}` carries the test object and
    :math:`\mathrm{II}` the substitution duct (Equation (1)); ISO 11691
    numbers them the other way, :math:`L_{p1}` for the substitution duct and
    :math:`L_{p2}` for the silencer (Equation (1) of that standard). The
    argument names here follow what was in the duct rather than either
    numbering, so neither convention can be entered backwards without the
    sign of the answer saying so.

    The optional reverberation times are ISO 7235 6.3: if the receiving
    room's absorption moved between the two series, the level difference is
    not yet the insertion loss and :math:`10 \lg(T_2 / T_1)` puts it right,
    with :math:`T_2` the time measured with the test object installed. When
    the test object sits outside the room, 6.3 allows :math:`T_2 = T_1`, and
    then the term is zero and the pair can be left out.

    :param substitution_level: The band levels of the series run with the
        substitution duct in place of the test object, in dB.
    :param object_level: The band levels of the series run with the test
        object installed, in dB.
    :param reverberation_times: Optionally ``(T_1, T_2)`` in s, the
        reverberation times of the substitution series and of the test-object
        series, for the correction of 6.3. One value stands for every band.
    :return: :math:`D_\mathrm{i}`, in dB, one value per band.
    :raises ValueError: If a level is not finite, if the arguments do not all
        carry the same number of bands, or if a reverberation time is not
        positive and finite.
    """
    without = require_finite_array(substitution_level, "substitution_level")
    with_object = require_finite_array(object_level, "object_level")
    _require_matching_bands(
        {"substitution_level": without.size, "object_level": with_object.size}
    )
    difference = without - with_object
    if reverberation_times is None:
        return np.asarray(difference, dtype=np.float64)
    first, second = reverberation_times
    t1 = require_positive_array(first, "reverberation_times[0]")
    t2 = require_positive_array(second, "reverberation_times[1]")
    _require_matching_bands(
        {"substitution_level": without.size, "object_level": with_object.size},
        broadcast={
            "reverberation_times[0]": t1.size,
            "reverberation_times[1]": t2.size,
        },
    )
    return np.asarray(difference + 10.0 * np.log10(t2 / t1), dtype=np.float64)


def octave_insertion_loss(insertion_loss: ArrayLike) -> NDArray[np.float64]:
    r"""ISO 11691 Equation (2): three one-third octaves into their octave.

    .. math::

       D_\mathrm{oct} = -10 \lg\left[\frac{1}{3}\left(
           10^{-D_1/10} + 10^{-D_2/10} + 10^{-D_3/10}
       \right)\right]\ \text{dB}

    The average is taken on what the silencer *lets through*, not on the
    decibels, and the two are not the same thing. A silencer that gives 30,
    30 and 5 dB across an octave gives 9,8 dB over the octave, not 21,7: the
    band that leaks decides the answer, because it is the one carrying nearly
    all of the transmitted energy. That is the whole reason the standard
    writes the equation out rather than letting a reader average the numbers.

    ISO 11691 states the assumption it rests on: the sound pressure levels of
    the three one-third octaves are taken to be equal in the series run with
    the substitution duct, so their energies can be weighted equally here.

    :param insertion_loss: One-third-octave insertion losses in dB, in
        ascending frequency order, a multiple of three of them. Each
        consecutive group of three is one octave.
    :return: :math:`D_\mathrm{oct}`, in dB, a third as many values.
    :raises ValueError: If a value is not finite, if the array is empty, or
        if it does not hold a multiple of three bands.
    """
    thirds = require_finite_array(insertion_loss, "insertion_loss")
    if thirds.size % _THIRDS_PER_OCTAVE:
        msg = (
            "Equation (2) folds three one-third octaves into one octave, so "
            "'insertion_loss' has to hold a multiple of three bands; got "
            f"{thirds.size}."
        )
        raise ValueError(msg)
    grouped = thirds.reshape(-1, _THIRDS_PER_OCTAVE)
    transmitted = np.mean(10.0 ** (-grouped / 10.0), axis=-1)
    return np.asarray(-10.0 * np.log10(transmitted), dtype=np.float64)


def _from_table(
    table: tuple[tuple[float, float], ...], frequency: float, name: str, source: str
) -> float:
    """The first tabulated value whose upper band centre reaches ``frequency``."""
    band = require_positive(frequency, name)
    for upper, value in table:
        if band <= upper:
            return value
    msg = (
        f"{source} stops at {table[-1][0]:.0f} Hz, and no value is tabulated "
        f"above it; got {frequency!r} Hz."
    )
    raise ValueError(msg)


def microphone_spread_limit(frequency: float) -> float:
    r"""ISO 7235 Table 6: how far three positions may disagree.

    A spatial average in a test duct is taken from at least three microphone
    positions equally spaced on a line across the duct. If the highest and
    the lowest of the three differ by more than the limit of Table 6, three
    positions are not enough to describe the field and five shall be used.

    The limit falls with frequency, from 10 dB at 50 and 63 Hz to 6 dB from
    160 Hz upwards, because a duct at low frequency has a standing-wave
    pattern the three points sample badly and at high frequency does not.

    The argument is a one-third-octave band centre, which is where the table
    is defined. A frequency between two of them takes the limit of the next
    centre at or above it, so the step from 7 dB to 6 dB sits immediately
    above 125 Hz rather than anywhere in the gap the printed table leaves
    between 125 and its ``> 160`` row.

    :param frequency: The one-third-octave band centre, in Hz.
    :return: The largest tolerated difference between the three positions, in
        dB.
    :raises ValueError: If the frequency is not positive and finite.
    """
    band = require_positive(frequency, "frequency")
    for centre, limit in ISO7235_SPREAD_LIMITS:
        if band <= centre:
            return limit
    return ISO7235_SPREAD_LIMITS[-1][1]


def microphone_positions_required(levels: ArrayLike, frequency: float) -> int:
    """ISO 7235 6.2.1: three microphone positions, or five.

    :param levels: The band levels measured at the three key positions, in
        dB. Exactly three are expected, because the rule is about whether
        three were enough.
    :param frequency: The one-third-octave band centre, in Hz.
    :return: ``3`` if the three positions agree closely enough for the band,
        ``5`` if the standard asks for two more.
    :raises ValueError: If a level is not finite, if there are not three of
        them, or if the frequency is not positive and finite.
    """
    measured = require_finite_array(levels, "levels")
    if measured.shape != (_THIRDS_PER_OCTAVE,):
        msg = (
            "'levels' is the three key positions of Figure 8, so exactly "
            f"three levels are expected; got shape {measured.shape}."
        )
        raise ValueError(msg)
    spread = float(np.max(measured) - np.min(measured))
    return 5 if spread > microphone_spread_limit(frequency) else 3


def survey_reproducibility(frequency: float) -> float:
    r"""ISO 11691 Table 1: the survey method's own reproducibility.

    Two decibels up to the 1,25 kHz one-third octave and three above it.
    ISO 11691 makes no claim of its own beyond that: it says outright that
    exact information on the precision cannot be given, that interlaboratory
    tests would be needed for a real ``sigma_R``, and that this estimate is
    what makes it a survey standard.

    :param frequency: The one-third-octave band centre, in Hz.
    :return: :math:`\sigma_R`, in dB.
    :raises ValueError: If the frequency is not positive and finite, or above
        the 10 kHz the table stops at.
    """
    return _from_table(
        ISO11691_REPRODUCIBILITY, frequency, "frequency", "ISO 11691 Table 1"
    )


def measurement_reproducibility(
    frequency: float, *, quantity: str = "insertion_loss"
) -> float:
    r"""ISO 7235 Table 7: the reproducibility standard deviation.

    The three columns do not agree with one another, and that is the useful
    part. Insertion loss is measured best in the middle of the range, 1 dB
    from 125 to 500 Hz, and worst at the top, 3 dB above 1,6 kHz. The
    sound-intensity route runs the other way, 3 dB at the bottom and 1 dB in
    the top two ranges. Transmission loss is a flat 3 dB everywhere, which is
    the mark of an estimate rather than a measurement: 7.9 says only the
    insertion-loss column came from tests, on 1 m long parallel-baffle
    silencers, and that the other two rest on experience.

    :param frequency: The one-third-octave band centre, in Hz.
    :param quantity: ``"insertion_loss"``, ``"transmission_loss"`` or
        ``"intensity"``, choosing the column.
    :return: :math:`\sigma_R`, in dB.
    :raises ValueError: If the frequency is not positive and finite, if it is
        above the range the column covers, or if the quantity is not one of
        the three the table prints.
    """
    column = require_choice(quantity, "quantity", tuple(ISO7235_REPRODUCIBILITY))
    return _from_table(
        ISO7235_REPRODUCIBILITY[column],
        frequency,
        "frequency",
        f"ISO 7235 Table 7 for the {column.replace('_', ' ')}",
    )


def measurement_expanded_uncertainty(
    frequency: float, *, quantity: str = "insertion_loss"
) -> float:
    """ISO 7235 7.9: twice the reproducibility, for 95 % coverage.

    Unless the laboratory knows better, the expanded uncertainty it records
    is twice the standard deviation of Table 7. That puts a measured
    insertion loss of 25 dB at 250 Hz within 2 dB of the truth and the same
    figure at 4 kHz within 6.

    :param frequency: The one-third-octave band centre, in Hz.
    :param quantity: The column of Table 7, as in :func:`measurement_reproducibility`.
    :return: The expanded uncertainty, in dB.
    :raises ValueError: As :func:`measurement_reproducibility`.
    """
    return ISO7235_COVERAGE_FACTOR * measurement_reproducibility(
        frequency, quantity=quantity
    )


def substitution_area_ratio(duct_area: float, element_area: float) -> float:
    """ISO 11691 4.5: the test duct against the silencer it feeds.

    The survey method wants the test ducts to be close in cross section to
    what they connect to. Outside the range of 0,6 to 1,7 the ducts are no
    longer standing in for the installation the silencer will see, and the
    reflections at the two joints stop being negligible; inside it,
    transition elements may be fitted.

    :param duct_area: The cross-sectional area of the test duct, in m².
    :param element_area: The cross-sectional area of the silencer or of the
        substitution duct, in m².
    :return: The ratio of the two areas, dimensionless.
    :raises ValueError: If an area is not positive and finite.
    :warns SilencerMeasurementWarning: If the ratio is outside 0,6 to 1,7.
    """
    duct = require_positive(duct_area, "duct_area")
    element = require_positive(element_area, "element_area")
    ratio = duct / element
    low, high = SURVEY_AREA_RATIO_RANGE
    if not low <= ratio <= high:
        msg = (
            f"ISO 11691 4.5 asks for a test duct between {low} and {high} "
            f"times the area of the silencer or the substitution duct; this "
            f"arrangement is at {ratio:.2f}, so the joints reflect more than "
            "the survey method allows for."
        )
        warnings.warn(msg, SilencerMeasurementWarning, stacklevel=2)
    return float(ratio)


def open_end_transmission_loss(
    frequency: ArrayLike,
    area: float,
    *,
    solid_angle: float = 2.0 * math.pi,
    sound_speed: float = _SOUND_SPEED_M_S,
) -> NDArray[np.float64]:
    r"""ISO 7235 Equation (B.3): what the open end of a duct keeps in.

    .. math::

       D_\mathrm{td} = 10 \lg\left[1 +
           \frac{\Omega}{\left(\dfrac{4\pi f \sqrt{S}}{c}\right)^{2}}
       \right]\ \text{dB}

    A duct radiating into a room does not hand the room everything that
    reaches its mouth. Well below the frequency at which the mouth is a
    wavelength across it is a poor radiator, and most of the energy turns
    round and goes back up the duct; well above it the mouth is transparent
    and the loss goes to zero. The group :math:`4\pi f \sqrt{S} / c` is the
    mouth measured in wavelengths, and the solid angle says how much room
    there is to radiate into. It works the way round that surprises people:
    :math:`\Omega` is in the numerator, so a duct ending in the middle of a
    room (:math:`4\pi`) keeps **more** sound in than one flush with a wall
    (:math:`2\pi`). A baffle is what makes an opening a good radiator,
    because it stops the pressure relieving round the rim, and an unbaffled
    mouth of the same size sends more of the sound back up the duct.

    ISO 5135 prints the identical formula as its own Equation (2), where it
    is called the end reflection loss of the open duct and is added to the
    sound power radiated into the room. The two names are one quantity.

    The library also carries a different closed form for the same physics,
    :func:`phonometry.noise_control.end_reflection_loss_closed_form`, which
    is Reynolds' as given by Long and raises the same argument to 1,88
    rather than to 2. For a circular duct in free space the two are
    :math:`10\lg[1 + (c/\pi f d)^2]` against
    :math:`10\lg[1 + (c/\pi f d)^{1,88}]`, so they part company where the
    argument is far from 1, which is at the ends of the range rather than in
    the middle.

    :param frequency: Band centre frequencies :math:`f`, in Hz.
    :param area: :math:`S`, the cross-sectional area of the duct, in m².
    :param solid_angle: :math:`\Omega`, the solid angle of radiation at the
        duct end, in sr. The five configurations of Table B.1 are in
        :data:`RADIATION_SOLID_ANGLES`; the default is a duct flush with one
        surface.
    :param sound_speed: :math:`c`, in m/s.
    :return: :math:`D_\mathrm{td}`, in dB, one value per frequency.
    :raises ValueError: If a value is not positive and finite.
    """
    bands = require_positive_array(frequency, "frequency")
    section = require_positive(area, "area")
    angle = require_positive(solid_angle, "solid_angle")
    speed = require_positive(sound_speed, "sound_speed")
    mouth = 4.0 * math.pi * bands * math.sqrt(section) / speed
    return np.asarray(10.0 * np.log10(1.0 + angle / mouth**2), dtype=np.float64)


def open_end_reflection_coefficient(
    frequency: ArrayLike,
    area: float,
    *,
    solid_angle: float = 2.0 * math.pi,
    sound_speed: float = _SOUND_SPEED_M_S,
) -> NDArray[np.float64]:
    r"""ISO 7235 Equation (B.4): the pressure reflection coefficient there.

    .. math::

       r = \left[\frac{1}{\Omega}
           \left(\frac{4\pi f \sqrt{S}}{c}\right)^{2} + 1\right]^{-1/2}

    The same physics as Equation (B.3) said the other way round, and the two
    close exactly: what is not transmitted is reflected, so
    :math:`D_\mathrm{td} = -10\lg(1 - r^2)` for every frequency, area and
    solid angle. That identity is the conformance anchor for both, because
    neither standard prints a worked example of either.

    Clause 5.2.4 puts this quantity to work as a requirement rather than as a
    result: a test duct with an anechoic termination qualifies only if its
    reflection coefficient is no greater than 0,3.

    :param frequency: Band centre frequencies :math:`f`, in Hz.
    :param area: :math:`S`, the cross-sectional area of the duct, in m².
    :param solid_angle: :math:`\Omega`, in sr.
    :param sound_speed: :math:`c`, in m/s.
    :return: :math:`r`, dimensionless, one value per frequency.
    :raises ValueError: If a value is not positive and finite.
    """
    bands = require_positive_array(frequency, "frequency")
    section = require_positive(area, "area")
    angle = require_positive(solid_angle, "solid_angle")
    speed = require_positive(sound_speed, "sound_speed")
    mouth = 4.0 * math.pi * bands * math.sqrt(section) / speed
    return np.asarray((mouth**2 / angle + 1.0) ** -0.5, dtype=np.float64)


def measured_transmission_loss(
    insertion_loss: ArrayLike, open_end_loss: ArrayLike
) -> NDArray[np.float64]:
    r"""ISO 7235 Equation (6): the transmission loss of an air-terminal unit.

    .. math::

       D_\mathrm{t} = D_\mathrm{i} + D_\mathrm{td}

    An air-terminal unit is measured in a reverberation room, so what the two
    series give is an insertion loss against the substitution duct. The unit's
    own transmission loss is that plus what the open end of the duct was
    keeping in anyway, which is why Equation (6) needs the theoretical
    :math:`D_\mathrm{td}` of Annex B rather than a second measurement.

    Well above the frequency at which the duct mouth is a wavelength across,
    :math:`D_\mathrm{td}` goes to zero and the two quantities meet.

    :param insertion_loss: :math:`D_\mathrm{i}`, in dB, from
        :func:`substitution_insertion_loss`.
    :param open_end_loss: :math:`D_\mathrm{td}`, in dB, from
        :func:`open_end_transmission_loss`.
    :return: :math:`D_\mathrm{t}`, in dB, one value per band.
    :raises ValueError: If a value is not finite, or if the two arrays carry
        different numbers of bands. Both are per-band quantities, so neither
        stands in for a whole run.
    """
    insertion = require_finite_array(insertion_loss, "insertion_loss")
    open_end = require_finite_array(open_end_loss, "open_end_loss")
    _require_matching_bands(
        {"insertion_loss": insertion.size, "open_end_loss": open_end.size}
    )
    return np.asarray(insertion + open_end, dtype=np.float64)


def flow_noise_power_level(
    pressure_level: ArrayLike,
    open_end_loss: ArrayLike,
    room_correction: ArrayLike,
) -> NDArray[np.float64]:
    r"""ISO 7235 Equation (7): the sound power of the flow noise.

    .. math::

       L_W = \overline{L_p} + D_\mathrm{td} + C

    Three terms, and each is a different kind of quantity. :math:`L_p` is the
    spatial energy-average level measured in the reverberation room, and 6.4
    is explicit that it is taken **without** a background correction, because
    the two series are reported separately and the reader subtracts them.
    :math:`D_\mathrm{td}` puts back what the open end of the duct kept in.
    :math:`C` is the level difference between the sound power radiated into
    the room and the average pressure in it, which ISO 3741 supplies from the
    room's volume and reverberation time.

    :param pressure_level: :math:`\overline{L_p}`, in dB, per band.
    :param open_end_loss: :math:`D_\mathrm{td}`, in dB, from
        :func:`open_end_transmission_loss`.
    :param room_correction: :math:`C`, in dB, per band or one value for all.
    :return: :math:`L_W`, in dB, one value per band.
    :raises ValueError: If a value is not finite, if the level and the
        open-end loss carry different numbers of bands, or if the room
        correction is neither a single value nor one per band.
    """
    level = require_finite_array(pressure_level, "pressure_level")
    open_end = require_finite_array(open_end_loss, "open_end_loss")
    correction = require_finite_array(room_correction, "room_correction")
    _require_matching_bands(
        {"pressure_level": level.size, "open_end_loss": open_end.size},
        broadcast={"room_correction": correction.size},
    )
    return np.asarray(level + open_end + correction, dtype=np.float64)


def modal_filter_cut_on(
    *,
    diameter: float | None = None,
    larger_dimension: float | None = None,
    sound_speed: float = _SOUND_SPEED_M_S,
) -> float:
    r"""ISO 7235 Equations (4) and (5): where higher-order modes start.

    .. math::

       f_{Cd} = \frac{0{,}59\,c}{d}
       \qquad
       f_{CH} = \frac{0{,}5\,c}{H}

    NOTE 2 to 5.2.2.3 prints these for the duct the modal filter is connected
    to, because the filter's requirement changes there: at least 3 dB of
    longitudinal attenuation of the fundamental mode at the low-frequency end,
    and at least 5 dB above this frequency, where the higher-order modes the
    filter exists to suppress can propagate.

    The rectangular form is exact: the first mode of a rigid rectangular duct
    is a half wavelength across the larger dimension, so :math:`c / 2H`. The
    circular constant is rounded: the exact value is the first zero of
    :math:`J_1'`, which puts the coefficient at 0,58607 rather than 0,59, so
    Equation (4) sits 0,67 % high. The exact eigenvalues are in
    :func:`phonometry.noise_control.circular_duct_cut_on`, which also carries
    the mean-flow correction this equation does not have.

    :param diameter: :math:`d` of a circular duct, in m. Exactly one of the
        two dimensions is given.
    :param larger_dimension: :math:`H`, the larger cross-sectional dimension
        of a rectangular duct, in m.
    :param sound_speed: :math:`c`, in m/s.
    :return: :math:`f_{Cd}` or :math:`f_{CH}`, in Hz.
    :raises ValueError: If neither dimension or both are given, or if a value
        is not positive and finite.
    """
    speed = require_positive(sound_speed, "sound_speed")
    if diameter is not None and larger_dimension is None:
        return float(
            CIRCULAR_CUT_ON_COEFFICIENT * speed / require_positive(diameter, "diameter")
        )
    if larger_dimension is not None and diameter is None:
        return float(
            RECTANGULAR_CUT_ON_COEFFICIENT
            * speed
            / require_positive(larger_dimension, "larger_dimension")
        )
    given = [
        name
        for name, value in (
            ("diameter", diameter),
            ("larger_dimension", larger_dimension),
        )
        if value is not None
    ]
    msg = (
        "Equation (4) is for a circular duct and Equation (5) for a "
        "rectangular one, so exactly one of 'diameter' and "
        f"'larger_dimension' is expected; got {given or 'neither'}."
    )
    raise ValueError(msg)


def normal_air_density(
    static_gauge_pressure: float,
    ambient_pressure: float,
    temperature_celsius: float,
) -> float:
    r"""ISO 7235 Equations (10), (21) and (22): the density where it matters.

    .. math::

       \rho_{1n} = \frac{1}{R}\,
                   \frac{p_{s1} + p_a}{\theta_1 + 273\ ^\circ\mathrm{C}}

    The ideal gas law with the standard's own numbers. The static pressure in
    the duct is measured as a **gauge** pressure against the ambient, so the
    two are added to get the absolute pressure the gas law wants, and the
    temperature is the one in the plane the pressure was measured in.

    Three equations print this: (10) for the normalised flow rate of (9),
    and (21) and (22) for the two series of the computational route of
    6.5.2.2.3. They differ only in which measurement they are given.

    Both printed constants are a little off the accurate figures. The offset
    273 rather than 273,15 puts the density 0,051 % high at 20 °C, and
    :math:`R = 287` rather than 287,05 adds 0,017 % to that, for 0,069 % in
    all. It does not cancel out of the pressure loss coefficient: the same
    density is in the dynamic pressure of both series, so the whole
    coefficient is scaled by that one factor rather than shifted, which
    leaves it 0,069 % low. That is far under the uncertainty of a
    pressure-loss test, and using the printed constants is what reproduces a
    result computed to the standard, which is why
    :data:`ISO7235_ABSOLUTE_ZERO_OFFSET` and :data:`ISO7235_GAS_CONSTANT`
    carry them as printed.

    :param static_gauge_pressure: :math:`p_{s1}`, the duct static pressure
        relative to the ambient, in Pa.
    :param ambient_pressure: :math:`p_a`, the absolute ambient pressure, in
        Pa.
    :param temperature_celsius: :math:`\theta_1`, in °C.
    :return: :math:`\rho_{1n}`, in kg/m³.
    :raises ValueError: If the ambient pressure is not positive and finite,
        if the gauge pressure is not finite, if the absolute pressure they
        make is not positive, or if the temperature is at or below the
        printed absolute zero.
    """
    ambient = require_positive(ambient_pressure, "ambient_pressure")
    gauge = _require_finite_scalar(static_gauge_pressure, "static_gauge_pressure")
    celsius = _require_finite_scalar(temperature_celsius, "temperature_celsius")
    absolute = gauge + ambient
    if absolute <= 0.0:
        msg = (
            "'static_gauge_pressure' is measured against the ambient, so the "
            "two add to the absolute pressure of the gas law, which has to "
            f"be positive; got {static_gauge_pressure!r} Pa against "
            f"{ambient_pressure!r} Pa."
        )
        raise ValueError(msg)
    kelvin = celsius + ISO7235_ABSOLUTE_ZERO_OFFSET
    if kelvin <= 0.0:
        msg = (
            "Equation (10) divides by the absolute temperature, which "
            f"ISO 7235 writes as theta + {ISO7235_ABSOLUTE_ZERO_OFFSET:.0f} "
            f"degrees Celsius; got {temperature_celsius!r} °C."
        )
        raise ValueError(msg)
    return float(absolute / (ISO7235_GAS_CONSTANT * kelvin))


def volume_flow_rate(mass_flow: float, density: float) -> float:
    r"""ISO 7235 Equations (8) and (9): mass flow into volume flow.

    .. math::

       q_V = \frac{q_m}{\rho_1}
       \qquad\text{or}\qquad
       q_V = \frac{q_m}{\rho_{1n}}

    The two printings are one division and differ only in which density goes
    in. Equation (8) uses the density upstream of the test object. Equation
    (9) uses the normalised density of Equation (10), and 6.5.2.1 says when:
    if the flow meter and the test object are far enough apart in temperature
    or static pressure that their density ratio leaves 0,98 to 1,02, the
    meter is no longer measuring the flow the test object sees.
    :data:`DENSITY_RATIO_RANGE` carries that window.

    :param mass_flow: :math:`q_m`, in kg/s.
    :param density: :math:`\rho_1` or :math:`\rho_{1n}`, in kg/m³.
    :return: :math:`q_V`, in m³/s.
    :raises ValueError: If a value is not positive and finite.
    """
    flow = require_positive(mass_flow, "mass_flow")
    rho = require_positive(density, "density")
    return float(flow / rho)


def dynamic_pressure(volume_flow: float, area: float, density: float) -> float:
    r"""ISO 7235 Equations (13), (16), (19) and (20): the velocity head.

    .. math::

       p_\mathrm{d} = \frac{\rho}{2}\left(\frac{q_V}{S}\right)^{2}

    One equation printed four times, once for each place the pressure loss
    coefficient needs it: the inlet of the simplified method (13), the chosen
    mid-range point of the fundamental method (16), and the two series of the
    computational route (19) and (20). The group :math:`q_V / S` is the face
    velocity, so this is :math:`\rho v^2 / 2` with the velocity written the
    way a flow meter reports it.

    :param volume_flow: :math:`q_V`, in m³/s.
    :param area: :math:`S`, the cross-sectional area the flow passes, in m².
    :param density: :math:`\rho`, in kg/m³.
    :return: :math:`p_\mathrm{d}`, in Pa.
    :raises ValueError: If a value is not positive and finite.
    """
    flow = require_positive(volume_flow, "volume_flow")
    section = require_positive(area, "area")
    rho = require_positive(density, "density")
    return float(0.5 * rho * (flow / section) ** 2)


def total_pressure(
    static_pressure: float, volume_flow: float, area: float, density: float
) -> float:
    r"""ISO 7235 Equation (11): static plus dynamic, in one plane.

    .. math::

       p_\mathrm{t} = p_\mathrm{s} + \frac{\rho}{2}
                      \left(\frac{q_V}{S}\right)^{2}

    :param static_pressure: :math:`p_\mathrm{s}`, in Pa, in the same
        reference as the answer is wanted in.
    :param volume_flow: :math:`q_V`, in m³/s.
    :param area: :math:`S`, in m².
    :param density: :math:`\rho`, in kg/m³.
    :return: :math:`p_\mathrm{t}`, in Pa.
    :raises ValueError: If the static pressure is not finite, or if another
        value is not positive and finite.
    """
    static = _require_finite_scalar(static_pressure, "static_pressure")
    return static + dynamic_pressure(volume_flow, area, density)


def total_pressure_loss(
    static_pressure_loss: float,
    inlet_dynamic_pressure: float,
    inlet_area: float,
    outlet_area: float,
) -> float:
    r"""ISO 7235 Equation (12): the total pressure loss across the object.

    .. math::

       \Delta p_\mathrm{t} = \Delta p_\mathrm{s}
           + p_\mathrm{d1}\left[1 - \left(\frac{S_1}{S_2}\right)^2\right]

    Measuring static pressures on both sides is not enough when the two sides
    are different sizes: an object that widens the duct converts velocity
    head back into static pressure, and a static-pressure difference alone
    would credit it with a recovery that is only bookkeeping. The bracket is
    that correction, and the NOTE to Equation (14) says what usually happens
    to it: as a rule :math:`S_1 = S_2`, and it vanishes.

    :param static_pressure_loss: :math:`\Delta p_\mathrm{s}`, in Pa.
    :param inlet_dynamic_pressure: :math:`p_\mathrm{d1}` from
        :func:`dynamic_pressure` at the inlet, in Pa.
    :param inlet_area: :math:`S_1`, the inlet test duct, in m².
    :param outlet_area: :math:`S_2`, the outlet test duct, in m².
    :return: :math:`\Delta p_\mathrm{t}`, in Pa.
    :raises ValueError: If the static loss is not finite, or if another value
        is not positive and finite.
    """
    static = _require_finite_scalar(static_pressure_loss, "static_pressure_loss")
    head = require_positive(inlet_dynamic_pressure, "inlet_dynamic_pressure")
    first = require_positive(inlet_area, "inlet_area")
    second = require_positive(outlet_area, "outlet_area")
    return float(static + head * (1.0 - (first / second) ** 2))


def pressure_loss_coefficient(
    total_loss: float, inlet_dynamic_pressure: float
) -> float:
    r"""ISO 7235 Equations (14) and (17): the loss in velocity heads.

    .. math::

       \zeta = \frac{\Delta p_\mathrm{t}}{p_\mathrm{d1}}

    A pressure loss on its own says nothing without the flow it was measured
    at, because it grows as the square of the velocity. Dividing by the
    velocity head of Equation (13) takes that out and leaves a number that
    belongs to the object: how many velocity heads it costs to push air
    through it. Equation (17) is the same division with the mid-range point
    of the fundamental method, :math:`\Delta p_{tot,n} / p_{dn}`.

    :param total_loss: :math:`\Delta p_\mathrm{t}` or
        :math:`\Delta p_{tot,n}`, in Pa.
    :param inlet_dynamic_pressure: :math:`p_\mathrm{d1}` or
        :math:`p_\mathrm{dn}`, in Pa.
    :return: :math:`\zeta`, dimensionless.
    :raises ValueError: If the loss is not finite, or if the dynamic pressure
        is not positive and finite.
    :warns SilencerMeasurementWarning: If the loss does not exceed the 10 Pa
        6.5.2.1 asks even the lowest airflow rate of a series to produce.
        The clause reads *greater than*, so a point sitting exactly on 10 Pa
        is one the series may not be built from and warns like any below it.
    """
    loss = _require_finite_scalar(total_loss, "total_loss")
    head = require_positive(inlet_dynamic_pressure, "inlet_dynamic_pressure")
    if abs(loss) <= MINIMUM_PRESSURE_DIFFERENCE_PA:
        msg = (
            "6.5.2.1 wants the lowest airflow rate of a series to produce a "
            f"pressure difference greater than {MINIMUM_PRESSURE_DIFFERENCE_PA:.0f} "
            f"Pa, so that the smallest number in the fit is still a "
            f"measurement; this point is {loss!r} Pa."
        )
        warnings.warn(msg, SilencerMeasurementWarning, stacklevel=2)
    return float(loss / head)


def average_pressure_loss_coefficient(
    object_static_pressure: ArrayLike,
    object_dynamic_pressure: ArrayLike,
    substitution_static_pressure: ArrayLike,
    substitution_dynamic_pressure: ArrayLike,
) -> float:
    r"""ISO 7235 Equation (18): the substitution method, averaged.

    .. math::

       \zeta = \frac{1}{N}\sum_{i=1}^{N}
                 \frac{p_{s1(\mathrm{I})i}}{p_{\mathrm{d}i}}
             - \frac{1}{M}\sum_{k=1}^{M}
                 \frac{p_{s1(\mathrm{II})k}}{p_{\mathrm{d}k}}

    The fundamental method of 6.5.2.2 is a substitution measurement like the
    acoustic one: run the rig with the test object and again with the
    substitution duct, and the difference belongs to the object. The
    computational route of 6.5.2.2.3 does it on the coefficients rather than
    on the pressures, so the two series need not be run at matching flow
    rates and need not even have the same number of points.

    Each series is at least five airflow rates spread over the test range,
    and the lowest has to produce more than
    :data:`MINIMUM_PRESSURE_DIFFERENCE_PA`.

    :param object_static_pressure: :math:`p_{s1(\mathrm{I})i}`, the upstream
        static pressures of the series with the test object, in Pa.
    :param object_dynamic_pressure: :math:`p_{\mathrm{d}i}` of that series,
        in Pa, from :func:`dynamic_pressure`.
    :param substitution_static_pressure: :math:`p_{s1(\mathrm{II})k}` of the
        series with the substitution duct, in Pa.
    :param substitution_dynamic_pressure: :math:`p_{\mathrm{d}k}` of that
        series, in Pa.
    :return: :math:`\zeta`, dimensionless.
    :raises ValueError: If a value is not finite, if a dynamic pressure is
        not positive, or if a series' two arrays are of different lengths.
    :warns SilencerMeasurementWarning: If either series has fewer points than
        the five 6.5.2.2.1 asks for.
    """
    first = require_finite_array(object_static_pressure, "object_static_pressure")
    first_head = require_positive_array(
        object_dynamic_pressure, "object_dynamic_pressure"
    )
    second = require_finite_array(
        substitution_static_pressure, "substitution_static_pressure"
    )
    second_head = require_positive_array(
        substitution_dynamic_pressure, "substitution_dynamic_pressure"
    )
    _require_matching_bands(
        {
            "object_static_pressure": first.size,
            "object_dynamic_pressure": first_head.size,
        }
    )
    _require_matching_bands(
        {
            "substitution_static_pressure": second.size,
            "substitution_dynamic_pressure": second_head.size,
        }
    )
    for name, size in (("test object", first.size), ("substitution duct", second.size)):
        if size < MINIMUM_FLOW_RATES:
            msg = (
                f"6.5.2.2.1 asks for at least {MINIMUM_FLOW_RATES} airflow "
                f"rates in each series; the {name} series has {size}, so the "
                "average is over fewer points than the standard allows for."
            )
            warnings.warn(msg, SilencerMeasurementWarning, stacklevel=2)
    return float(np.mean(first / first_head) - np.mean(second / second_head))


def upstream_straight_length(area: float) -> float:
    r"""ISO 7235 6.5.2.2.1: how much straight duct the flow needs first.

    The upstream test duct is straight for at least :math:`5 d_e` or 2 m,
    whichever is greater, where :math:`d_e = \sqrt{4S/\pi}` is the equivalent
    diameter. Below about 0,126 m² the 2 m floor is what binds; above it the
    five diameters are.

    The length is there so the velocity profile has settled by the time it
    reaches the test object: 6.5.2.2.1 wants it uniform to ±10 % of the mean
    over the cross section, excluding the 15 mm nearest the walls, surveyed
    at ten points along each of two perpendicular axes about
    :math:`1{,}5 d_e` upstream.

    :param area: :math:`S`, the cross-sectional area of the duct, in m².
    :return: The straight length required, in m.
    :raises ValueError: If the area is not positive and finite.
    """
    section = require_positive(area, "area")
    equivalent = math.sqrt(4.0 * section / math.pi)
    return float(max(UPSTREAM_STRAIGHT_DIAMETERS * equivalent, UPSTREAM_STRAIGHT_MIN_M))


def duct_sound_power_level(
    room_sound_power_level: ArrayLike, end_reflection_loss: ArrayLike
) -> NDArray[np.float64]:
    r"""ISO 5135 Equation (1): back from the room to the duct.

    .. math::

       L_{W\mathrm{duct}} = L_W + \Delta L_\mathrm{r}

    An air-terminal device is measured by what it radiates into a
    reverberation room, and what a designer needs is what it puts into the
    duct behind it. The two differ by the end reflection loss of the open
    duct, which is Equation (2) of ISO 5135 and, written out, is exactly
    Equation (B.3) of ISO 7235: the same formula, the same solid-angle table,
    two names. :func:`open_end_transmission_loss` is both.

    The NOTE to Table 1 offers a way out of the correction rather than a
    second formula for it: a transmission element to ISO 7235 may be fitted
    instead, and then no correction is applied at all.

    :param room_sound_power_level: :math:`L_W`, the sound power radiated into
        the room, in dB, from ISO 3741.
    :param end_reflection_loss: :math:`\Delta L_\mathrm{r}`, in dB, from
        :func:`open_end_transmission_loss`.
    :return: :math:`L_{W\mathrm{duct}}`, in dB, one value per band.
    :raises ValueError: If a value is not finite, or if the two arrays do not
        carry the same number of bands.
    """
    level = require_finite_array(room_sound_power_level, "room_sound_power_level")
    reflection = require_finite_array(end_reflection_loss, "end_reflection_loss")
    _require_matching_bands(
        {
            "room_sound_power_level": level.size,
            "end_reflection_loss": reflection.size,
        },
        broadcast_singletons=True,
    )
    return np.asarray(level + reflection, dtype=np.float64)


@dataclass(frozen=True)
class OperatingLine:
    r"""ISO 5135 5.5.2: a level fitted against the logarithm of a duty.

    An air-terminal device is not tested at the one operating point a
    designer will use it at. It is tested at several, and the standard fits a
    straight line through the levels against :math:`\lg q_V` or
    :math:`\lg \Delta p_\mathrm{t}` by least squares. Between the points
    that is interpolation; outside them 5.5.2 allows the line to be extended
    down to half the smallest duty measured and up to twice the largest, and
    no further.

    Two things make the fit reportable. The maximum deviation between the
    measured points and the line has to be within
    :data:`EXTRAPOLATION_MAX_DEVIATION_DB`; past that the levels are not a
    straight line in this variable and the extrapolation means nothing.
    And clause 8 k) requires the report to say which of the values it gives
    are extrapolated rather than measured directly.

    :ivar slope: dB per decade of the duty.
    :ivar intercept: The level, in dB, at a duty of 1 in whatever unit the
        duty was given in.
    :ivar maximum_deviation: The largest distance, in dB, between a measured
        point and the line.
    :ivar smallest_duty: The lowest duty measured.
    :ivar largest_duty: The highest duty measured.
    :ivar duty: The duties the fit was made from, as given.
    :ivar levels: The levels, in dB, as given.
    """

    slope: float
    intercept: float
    maximum_deviation: float
    smallest_duty: float
    largest_duty: float
    duty: NDArray[np.float64]
    levels: NDArray[np.float64]

    @property
    def valid_range(self) -> tuple[float, float]:
        """The duties 5.5.2 lets the line be read at, half to twice."""
        low, high = EXTRAPOLATION_RANGE_FACTORS
        return (low * self.smallest_duty, high * self.largest_duty)

    def level_at(self, duty: float) -> float:
        """The fitted level at one duty, in dB.

        :param duty: The volume flow rate or total pressure loss to read the
            line at, in the unit the fit was made in.
        :return: The level, in dB, rounded to nothing: clause 8 k) asks for
            half a decibel in the report and
            :data:`REPORTING_RESOLUTION_DB` carries that, but rounding here
            would compound through a chain.
        :raises ValueError: If the duty is not positive and finite.
        :warns SilencerMeasurementWarning: If the duty is outside the range
            5.5.2 allows the line to be extended over.
        """
        point = require_positive(duty, "duty")
        low, high = self.valid_range
        if not low <= point <= high:
            msg = (
                "ISO 5135 5.5.2 extends a fitted line down to half the "
                f"smallest duty measured and up to twice the largest, so to "
                f"{low:.4g} and {high:.4g}; got {duty!r}, which is an "
                "extrapolation the standard does not offer."
            )
            warnings.warn(msg, SilencerMeasurementWarning, stacklevel=2)
        return float(self.slope * math.log10(point) + self.intercept)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the measured points and the line fitted through them.

        Requires matplotlib (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.noise_control import plot_operating_line

        check_language(language)
        return plot_operating_line(self, ax=ax, language=language, **kwargs)


def fit_operating_line(duty: ArrayLike, levels: ArrayLike) -> OperatingLine:
    r"""ISO 5135 5.5.2: the least-squares line through the test points.

    The abscissa is the logarithm of the duty, which is the volume flow rate
    when the tests were made at a constant pressure loss coefficient and the
    total pressure loss when they were made at a constant flow rate. The
    ordinate is the band level or the A-weighted level, and the same fit
    serves both.

    :param duty: :math:`q_V` in m³/s or :math:`\Delta p_\mathrm{t}` in Pa,
        one per test point, at least two of them.
    :param levels: The level at each of those points, in dB.
    :return: An :class:`OperatingLine`.
    :raises ValueError: If a duty is not positive and finite, if a level is
        not finite, if the two arrays are of different lengths, if there are
        fewer than two points, or if every point is at the same duty.
    :warns SilencerMeasurementWarning: If a point lies further from the line
        than the 3 dB of 5.5.2.
    """
    duties = require_positive_array(duty, "duty")
    measured = require_finite_array(levels, "levels")
    _require_matching_bands({"duty": duties.size, "levels": measured.size})
    if duties.size < _MINIMUM_FIT_POINTS:
        msg = (
            "A straight line needs at least two points to be fitted through; "
            f"got {duties.size}."
        )
        raise ValueError(msg)
    abscissa = np.log10(duties)
    if float(np.ptp(abscissa)) <= 0.0:
        msg = (
            "5.5.2 fits the levels against the logarithm of the duty, so the "
            "test points have to be at more than one duty; every one of "
            f"these is at {float(duties[0])!r}."
        )
        raise ValueError(msg)
    slope, intercept = np.polyfit(abscissa, measured, 1)
    deviation = float(np.max(np.abs(measured - (slope * abscissa + intercept))))
    if deviation > EXTRAPOLATION_MAX_DEVIATION_DB:
        msg = (
            f"5.5.2 asks for the measured points to sit within "
            f"{EXTRAPOLATION_MAX_DEVIATION_DB:.0f} dB of the fitted line; the "
            f"worst of these is {deviation:.2f} dB away, so the levels are "
            "not a straight line in this variable and reading the line off "
            "outside the points would not mean anything."
        )
        warnings.warn(msg, SilencerMeasurementWarning, stacklevel=2)
    return OperatingLine(
        slope=float(slope),
        intercept=float(intercept),
        maximum_deviation=deviation,
        smallest_duty=float(np.min(duties)),
        largest_duty=float(np.max(duties)),
        duty=duties,
        levels=measured,
    )
