#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Insertion loss of a ducted silencer, measured by substitution.

Everything a silencer model computes comes from geometry. The figure a
supplier publishes does not: it is an **insertion loss measured by
substitution**, and this module is the arithmetic of that measurement.

Two standards share the method and differ only in how much rigour they ask
of the laboratory:

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

The plane-wave modelling this measurement is compared against lives in
:mod:`phonometry.noise_control.silencers`, and the cut-on frequency above
which a duct stops carrying plane waves alone is in
:mod:`phonometry.noise_control.duct_modes`.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np

from .._internal.validation import (
    require_choice,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ISO11691_REPRODUCIBILITY",
    "ISO7235_COVERAGE_FACTOR",
    "ISO7235_REPRODUCIBILITY",
    "ISO7235_SPREAD_LIMITS",
    "SURVEY_AREA_RATIO_RANGE",
    "SURVEY_BAND_RANGE_HZ",
    "SURVEY_DIAMETER_RANGE_M",
    "SURVEY_MAX_VELOCITY_M_S",
    "SilencerMeasurementWarning",
    "measurement_expanded_uncertainty",
    "measurement_reproducibility",
    "microphone_positions_required",
    "microphone_spread_limit",
    "octave_insertion_loss",
    "substitution_area_ratio",
    "substitution_insertion_loss",
    "survey_reproducibility",
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

_THIRDS_PER_OCTAVE = 3


class SilencerMeasurementWarning(PhonometryWarning):
    """A substitution measurement is outside the range its method covers.

    Raised when a test arrangement falls outside a limit the standard writes
    down but does not make an error: an area ratio outside the 0,6 to 1,7 of
    ISO 11691 4.5, or a band outside the 50 Hz to 10 kHz both standards
    measure over. The arithmetic still runs, because a laboratory may report
    such a value as long as it says so.
    """


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
