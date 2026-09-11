#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Vibration and the people in a building (DIN 4150-2:1999-06).

DIN 4150-2 is the assessment the DIN 45669-1 meter exists for. The meter
produces two numbers for a record, the maximum weighted vibration severity
:math:`KB_{F\mathrm{max}}` and the clock maximum r.m.s. :math:`KB_{FTm}`, and
this standard says what they may be for the people who live or work where the
vibration arrives: a table of guide values by kind of area and time of day,
a procedure that reads them in a fixed order, and the special rules for the
sources that most often bring vibration into a house.

**The two assessment quantities** (Clause 6.1). :math:`KB_{F\mathrm{max}}` is
what the vibration felt like at its worst. The **assessment vibration
severity** :math:`KB_{FTr}` of Formulae (4a), (4b) and (5) is what it added
up to over the whole assessment period, 16 h by day and 8 h by night: the
clock maximum r.m.s. of each stretch of exposure, weighted by its share of the
period, and doubled in weight where the stretch falls in the rest hours of the
day. The largest of the three directions is the one assessed.

**The procedure** (Clause 6.2, Figure 2). If :math:`KB_{F\mathrm{max}}` is at
or below the lower guide value :math:`A_u`, the requirement is met and the
question is over. If it is above the upper guide value :math:`A_o`, it is not
met. In between, rare and short events are accepted as they are, and
everything else is decided by :math:`KB_{FTr}` against :math:`A_r`. The guide
values of Table 1 are not to be applied mechanically, the standard says, and
Example 3 of its Annex C shows what it means: 0,17 against an :math:`A_u` of
0,15 is inside the 15 % a measurement of :math:`KB_F` is uncertain by, and
the requirement "can as a rule still be regarded as met".

**The sources** (Clause 6.5). Up to three short events a day, blasting among
them, are judged on :math:`A_o` alone, and quarry blasting by day in a mixed
or residential area, under the conditions of 6.5.1, on the :math:`A_o` of an
industrial one. Road traffic uses the procedure without the rest-time factor.
A railway is judged on :math:`A_u` and :math:`A_r` only, with the factor 1,5
on both for an urban surface line; :math:`A_o` is not a verdict for it, and
6.5.3.5 sets its own night-time thresholds, 0,6 on a surface line and 0,3
underground, above which a single clock maximum is a reason to look into the
cause. A construction site has its own Table 2, by how many working days it
shakes the neighbours and how far the operator is prepared to go, with the
values for two to six days interpolated as Figure 3 draws them.

**A railway, in detail** (Annex A). The trains of one class occupy a few
clock intervals each, so their :math:`KB_{FTm}` is formed over the occupied
intervals alone (Formula (A.1)), a standard deviation is put on its square
(Formula (A.2)), and the assessment severity weights each class by the
intervals it occupies in the period, 1920 by day and 960 by night (Formula
(A.3)). Figure D.1 turns that around: how many trains an hour a class may run
before :math:`KB_{FTr}` reaches :math:`A_r`.

**From a velocity record** (Clause 7). Where only an unweighted record
exists, Formula (6) turns its peak and its frequency into a KB value and
Formula (7) scales that by an empirical factor of Table 3 to an estimate of
:math:`KB_{F\mathrm{max}}`, marked with an asterisk in the standard because
it is one.

**A formula printed wrong.** Formula (A.1b) equates :math:`KB_{FTm,j}` to a
mean of squares with no root over it; Formula (A.1a) beside it, Formula (A.2)
and the worked Example 8 all take the root. Registered in ``docs/ERRATA.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_finite_array,
    require_non_negative,
    require_positive,
)
from .vibration_meter import (
    KB_CORNER_HZ,
    TAKT_DURATION_S,
    TAKT_SUPPRESSION_THRESHOLD,
    takt_maximum_rms,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ASSESSMENT_PERIOD_S",
    "ASSESSMENT_TAKT_COUNT",
    "BLASTING_EXCEPTION_KB_FMAX",
    "CONSTRUCTION_BLASTING_A_O",
    "CONSTRUCTION_GUIDE_VALUES",
    "CONSTRUCTION_STAGES",
    "DAY_REST_TIME_S",
    "GUIDE_VALUES",
    "KB_UNCERTAINTY_PERCENT",
    "PEAK_TO_KB_FACTORS",
    "RAILWAY_NIGHT_INVESTIGATION_KB",
    "RARE_EVENTS_PER_DAY",
    "REST_TIME_WEIGHT",
    "URBAN_RAILWAY_FACTOR",
    "GuideValues",
    "PeopleAssessment",
    "RailwayAssessment",
    "admissible_exposure_s",
    "admissible_trains_per_hour",
    "assess_people_in_buildings",
    "assessment_vibration_severity",
    "construction_guide_values",
    "guide_values",
    "kb_fmax_from_peak_velocity",
    "kb_from_peak_velocity",
    "railway_assessment_severity",
    "railway_takt_maximum_rms",
    "railway_takt_spread",
]

#: The assessment period :math:`T_r` of 3.7.3, in seconds: 16 h by day (6:00
#: to 22:00) and 8 h by night.
ASSESSMENT_PERIOD_S: dict[str, float] = {"day": 16.0 * 3600.0, "night": 8.0 * 3600.0}

#: :math:`N_r` of Annex A: the 30 s clock intervals in an assessment period,
#: 1920 by day and 960 by night.
ASSESSMENT_TAKT_COUNT: dict[str, int] = {
    period: round(seconds / TAKT_DURATION_S)
    for period, seconds in ASSESSMENT_PERIOD_S.items()
}

#: The rest hours of the day (3.7.4), in seconds: 6:00 to 7:00 and 19:00 to
#: 22:00 on working days, four hours; on Sundays and holidays the whole day.
DAY_REST_TIME_S: float = 4.0 * 3600.0

#: The weight an exposure in the rest hours carries in Formula (5): 2.
REST_TIME_WEIGHT: float = 2.0

#: The uncertainty 5.4 attaches to a measured KB value, in per cent: about 15.
KB_UNCERTAINTY_PERCENT: float = 15.0

#: The most events a day that 6.5.1 calls rare and short: 3.
RARE_EVENTS_PER_DAY: int = 3

#: The :math:`KB_{F\mathrm{max}}` quarry blasting may reach a few times a
#: year in exceptional cases (6.5.1): 8. The rule it is an exception to is the
#: one ``source="quarry_blasting"`` applies: blasts on working days with the
#: neighbours warned, between 7:00 and 13:00 or 15:00 and 19:00, one event a
#: day, are held to the :math:`A_o` of Table 1 row 1 in the areas of rows 3
#: and 4.
BLASTING_EXCEPTION_KB_FMAX: float = 8.0

#: The :math:`A_o` a construction site's blasting is held to (6.5.4.2): 8,
#: with lower values to be aimed for.
CONSTRUCTION_BLASTING_A_O: float = 8.0

#: The factor 6.5.3.3 puts on :math:`A_u` and :math:`A_r` for an urban
#: surface railway (tram, light rail, S-Bahn): 1,5.
URBAN_RAILWAY_FACTOR: float = 1.5

#: The night-time thresholds of 6.5.3.5 for a railway, by kind of line: a
#: single clock maximum :math:`KB_{FTi}` above 0,6 on a surface line, in any
#: area, or above 0,3 on an underground line in the areas of rows 3 to 5, is
#: a reason to look into the cause (flat spots on wheels, for one) and to put
#: it right, not a verdict. The value still counts in :math:`KB_{FTr}`.
RAILWAY_NIGHT_INVESTIGATION_KB: dict[str, float] = {
    "surface": 0.6,
    "underground": 0.3,
}


@dataclass(frozen=True)
class GuideValues:
    r"""One row of Table 1 or Table 2 for one period: the three guide values.

    :ivar a_u: :math:`A_u`, the lower value, which :math:`KB_{F\mathrm{max}}`
        is compared with first.
    :ivar a_o: :math:`A_o`, the upper value, above which the requirement is
        not met however short the exposure.
    :ivar a_r: :math:`A_r`, the value the assessment vibration severity
        :math:`KB_{FTr}` is compared with.
    """

    a_u: float
    a_o: float
    a_r: float


#: Table 1 (printed page 6): the guide values by kind of area, keyed by the
#: BauNVO use the row names, and by period. ``"industrial"`` is row 1 (only
#: commercial installations around, dwellings for owners and supervisors at
#: most), ``"commercial"`` row 2 (mainly commercial), ``"mixed"`` row 3
#: (neither mainly commercial nor mainly dwellings: core, mixed and village
#: areas), ``"residential"`` row 4 (mainly or only dwellings, small
#: settlements) and ``"sensitive"`` row 5 (hospitals, spas and the like).
GUIDE_VALUES: dict[str, dict[str, GuideValues]] = {
    "industrial": {
        "day": GuideValues(0.4, 6.0, 0.2),
        "night": GuideValues(0.3, 0.6, 0.15),
    },
    "commercial": {
        "day": GuideValues(0.3, 6.0, 0.15),
        "night": GuideValues(0.2, 0.4, 0.1),
    },
    "mixed": {
        "day": GuideValues(0.2, 5.0, 0.1),
        "night": GuideValues(0.15, 0.3, 0.07),
    },
    "residential": {
        "day": GuideValues(0.15, 3.0, 0.07),
        "night": GuideValues(0.1, 0.2, 0.05),
    },
    "sensitive": {
        "day": GuideValues(0.1, 3.0, 0.05),
        "night": GuideValues(0.1, 0.15, 0.05),
    },
}

#: The three stages of 6.5.4.2 a construction site may be held to: below
#: stage I no considerable annoyance is expected; below stage II none either
#: provided the measures of 6.5.4.3 are taken; above stage III the exposure is
#: unreasonable and special agreements are needed.
CONSTRUCTION_STAGES: tuple[str, ...] = ("I", "II", "III")

#: Table 2 (printed page 9): the daytime guide values for a construction
#: site, keyed by stage and by the longest duration of the column in working
#: days: up to 1 day, from 7 to 26 days, from 27 to 78 days. The values for 2
#: to 6 days are interpolated (Figure 3), and beyond 78 days the standard
#: makes no statement. :math:`A_o` is 5 in every cell, or 6 in a commercial
#: or industrial area.
CONSTRUCTION_GUIDE_VALUES: dict[str, dict[int, GuideValues]] = {
    "I": {
        1: GuideValues(0.8, 5.0, 0.4),
        26: GuideValues(0.4, 5.0, 0.3),
        78: GuideValues(0.3, 5.0, 0.2),
    },
    "II": {
        1: GuideValues(1.2, 5.0, 0.8),
        26: GuideValues(0.8, 5.0, 0.6),
        78: GuideValues(0.6, 5.0, 0.4),
    },
    "III": {
        1: GuideValues(1.6, 5.0, 1.2),
        26: GuideValues(1.2, 5.0, 1.0),
        78: GuideValues(0.8, 5.0, 0.6),
    },
}

#: Table 3 (printed page 10): the empirical factor :math:`c_F` of Formula (7)
#: by kind of vibration, rows 1 to 4 with their a) and b). Mean values from
#: experience, the table says, and about 15 % either way.
PEAK_TO_KB_FACTORS: dict[str, float] = {
    "harmonic": 0.9,
    "harmonic_distorted": 0.8,
    "stochastic_resonant": 0.8,
    "stochastic": 0.7,
    "single_event_resonant": 0.8,
    "single_event": 0.6,
}

_PERIODS = tuple(ASSESSMENT_PERIOD_S)
_AREAS = tuple(GUIDE_VALUES)
_SOURCES = ("general", "road", "railway", "urban_railway", "quarry_blasting")
_RAILWAYS = ("railway", "urban_railway")
#: The areas of Table 1 rows 3 and 4, where quarry blasting under the
#: conditions of 6.5.1 is held to the :math:`A_o` of row 1.
_QUARRY_BLASTING_AREAS = ("mixed", "residential")
_ROW_1 = "industrial"
#: The decimals a raised guide value keeps: 1,5 times a two-decimal value.
_RAISED_DECIMALS = 3
_CONSTRUCTION_AREAS = ("commercial", "industrial")
#: The area Table 2 is not applicable to (6.5.4.2): hospitals and the like
#: need their own investigation and agreement.
_NO_CONSTRUCTION_TABLE = "sensitive"
#: The longest duration, in working days, of the middle and the last column
#: of Table 2.
_CONSTRUCTION_MIDDLE_DAYS = 26
_CONSTRUCTION_MAX_DAYS = 78
#: The fewest clock maxima a spread can be formed from.
_MIN_MAXIMA_FOR_SPREAD = 2
#: Where the interpolation of Figure 3 starts and ends, in working days: the
#: one-day column holds through day 1 and the next column from day 7.
_INTERPOLATION_DAYS = (1, 7)
#: The :math:`A_o` of Table 2 in a commercial or industrial area (footnote).
_CONSTRUCTION_A_O_COMMERCIAL = 6.0
#: The clock intervals in an hour, which is what Figure D.1 counts trains in.
_TAKTE_PER_HOUR = 3600.0 / TAKT_DURATION_S
#: The decimals the guide values are printed with, and the ones a quantity is
#: compared at: Example 4 of Annex C forms a KB_FTr of 0,154, writes it as
#: 0,15 and finds it at the A_r of 0,15, met.
_GUIDE_DECIMALS = 2


def _printed(value: float, decimals: int) -> float:
    """The value written with that many decimals, half up, as a hand rounds.

    Not :func:`round`, which writes 0,155 as 0,15 because the float is a hair
    under it and ties go to even; the standard reads its numbers as printed.
    """
    quantum = Decimal(1).scaleb(-decimals)
    return float(Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_UP))


def _keeps_to(value: float, guide: float) -> bool:
    """Whether the value, written with the decimals of the guide value, is at or below it.

    Table 1, Table 2 and the steps of Figure 3 are printed with two decimals
    and the guide values 6.5.3.3 raises by 1,5 with three, so each is compared
    at its own.
    """
    decimals = _GUIDE_DECIMALS
    if _printed(guide, decimals) != guide:
        decimals = _RAISED_DECIMALS
    return _printed(value, decimals) <= guide


def guide_values(
    area: str, *, time_of_day: str = "day", source: str = "general"
) -> GuideValues:
    """The guide values of Table 1 for one area, time of day and kind of source.

    :param area: The row of Table 1, as :data:`GUIDE_VALUES` keys it.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :param source: ``"general"`` (default), ``"road"`` or ``"railway"``, for
        which Table 1 applies as printed; ``"urban_railway"``, the surface
        line of a public transport system, for which 6.5.3.3 raises
        :math:`A_u` and :math:`A_r` by the factor 1,5; or
        ``"quarry_blasting"``, blasts on working days with the neighbours
        warned, between 7:00 and 13:00 or 15:00 and 19:00, one event a day,
        for which 6.5.1 lets a mixed or residential area take the daytime
        :math:`A_o` of row 1, which is 6.
    :return: The three values, as a :class:`GuideValues`.
    :raises ValueError: For an unknown area, time of day or source.
    """
    row = GUIDE_VALUES[require_choice(str(area), "area", _AREAS)]
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    values = row[which]
    kind = require_choice(str(source), "source", _SOURCES)
    if kind == "urban_railway":
        # Rounded to the decimals of the table, so 0,05 times 1,5 is 0,075
        # and not a float with a tail the verdict would then round anyway.
        return GuideValues(
            round(values.a_u * URBAN_RAILWAY_FACTOR, _RAISED_DECIMALS),
            values.a_o,
            round(values.a_r * URBAN_RAILWAY_FACTOR, _RAISED_DECIMALS),
        )
    if kind == "quarry_blasting" and which == "day" and area in _QUARRY_BLASTING_AREAS:
        return GuideValues(values.a_u, GUIDE_VALUES[_ROW_1][which].a_o, values.a_r)
    return values


def _interpolated(low: float, high: float, days: int) -> float:
    """A Table 2 value between the one-day column and the next, Figure 3.

    Written with the two decimals the steps of Figure 3 are printed with, so
    the sixth day of stage I is the 0,47 the figure shows and not 0,4667.
    """
    first, next_column = _INTERPOLATION_DAYS
    return _printed(
        low + (high - low) * (days - first) / (next_column - first), _GUIDE_DECIMALS
    )


def construction_guide_values(
    duration_days: int, *, stage: str = "I", area: str = "residential"
) -> GuideValues:
    """The daytime guide values of Table 2 for a construction site (6.5.4.2).

    The duration is the number of working days on which the site actually
    shakes the neighbours, not how long it stands. A duration of two to six
    days takes the values Figure 3 interpolates between the one-day column
    and the column that starts at seven days, and a duration over 78 days is
    outside the table. Vibration at night is judged by Table 1 instead, and
    the site's blasting by :data:`CONSTRUCTION_BLASTING_A_O` alone. Table 2
    is not applicable to an especially sensitive area, a hospital for one;
    6.5.4.2 sends those to their own investigation and agreement.

    :param duration_days: :math:`D`, a whole number of working days from 1
        to 78.
    :param stage: ``"I"`` (default), ``"II"`` or ``"III"``.
    :param area: The area the site is in; a commercial or industrial one has
        an :math:`A_o` of 6 rather than 5, and ``"sensitive"`` is refused.
    :return: The three values, as a :class:`GuideValues`.
    :raises ValueError: For a duration that is not a whole number of days
        from 1 to 78, an unknown stage, an unknown area or a sensitive one.
    """
    if isinstance(duration_days, bool) or float(duration_days) != int(duration_days):
        msg = f"'duration_days' must be a whole number of working days, got {duration_days!r}."
        raise ValueError(msg)
    days = int(duration_days)
    if days < 1 or days > _CONSTRUCTION_MAX_DAYS:
        msg = (
            "Table 2 covers 1 to 78 working days; the standard makes no "
            f"statement beyond that. Got {duration_days!r}."
        )
        raise ValueError(msg)
    columns = CONSTRUCTION_GUIDE_VALUES[
        require_choice(str(stage), "stage", CONSTRUCTION_STAGES)
    ]
    kind = require_choice(str(area), "area", _AREAS)
    if kind == _NO_CONSTRUCTION_TABLE:
        msg = (
            "Table 2 is not applicable to an especially sensitive area (6.5.4.2); "
            "the standard asks for a separate investigation and agreement there."
        )
        raise ValueError(msg)
    one_day, to_26, to_78 = (columns[bound] for bound in sorted(columns))
    a_o = _CONSTRUCTION_A_O_COMMERCIAL if kind in _CONSTRUCTION_AREAS else one_day.a_o
    first, next_column = _INTERPOLATION_DAYS
    if days <= first:
        column = one_day
    elif days < next_column:
        return GuideValues(
            _interpolated(one_day.a_u, to_26.a_u, days),
            a_o,
            _interpolated(one_day.a_r, to_26.a_r, days),
        )
    else:
        column = to_26 if days <= _CONSTRUCTION_MIDDLE_DAYS else to_78
    return GuideValues(column.a_u, a_o, column.a_r)


def _exposures(
    kb_ftm: ArrayLike, exposure_s: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Matched, finite, non-negative stretches of exposure."""
    severities = require_finite_array(kb_ftm, "kb_ftm")
    durations = require_finite_array(exposure_s, "exposure_s")
    if severities.shape != durations.shape:
        msg = "'kb_ftm' and 'exposure_s' must match, one severity per stretch."
        raise ValueError(msg)
    if np.any(severities < 0.0) or np.any(durations < 0.0):
        msg = "'kb_ftm' and 'exposure_s' must not be negative."
        raise ValueError(msg)
    return severities, durations


def assessment_vibration_severity(
    kb_ftm: ArrayLike,
    exposure_s: ArrayLike,
    *,
    time_of_day: str = "day",
    in_rest_time: ArrayLike | None = None,
) -> float:
    r"""The assessment vibration severity :math:`KB_{FTr}`, Formulae (4) and (5).

    :math:`KB_{FTr} = \sqrt{\frac{1}{T_r} \sum_j w_j T_{e,j} KB_{FTm,j}^2}`:
    the clock maximum r.m.s. of each stretch of exposure, weighted by the
    share of the assessment period it lasts for. One stretch is Formula
    (4b), several are Formula (4a), and a stretch in the rest hours of the
    day carries the weight 2 of Formula (5), which 6.5.2 and 6.5.3.1 say is
    not applied to road or rail traffic.

    :param kb_ftm: :math:`KB_{FTm}` of each stretch, dimensionless, as
        :func:`~phonometry.vibration.takt_maximum_rms` gives it.
    :param exposure_s: :math:`T_{e,j}`, how long each stretch lasts within the
        period, in seconds.
    :param time_of_day: ``"day"`` (default, :math:`T_r` = 16 h) or ``"night"``
        (8 h).
    :param in_rest_time: Whether each stretch falls in the rest hours of the
        day, one flag per stretch; ``None`` (default) for none. Rest hours
        exist by day only.
    :return: :math:`KB_{FTr}`, dimensionless.
    :raises ValueError: For mismatched or negative inputs, an unknown time of day,
        an exposure longer than the period, or a rest-time flag by night.
    """
    severities, durations = _exposures(kb_ftm, exposure_s)
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    total = ASSESSMENT_PERIOD_S[which]
    if float(np.sum(durations)) > total * (1.0 + 1e-9):
        msg = (
            f"the exposures add up to {np.sum(durations) / 3600.0:g} h, more than "
            f"the {total / 3600.0:g} h assessment period."
        )
        raise ValueError(msg)
    weights = np.ones_like(severities)
    if in_rest_time is not None:
        flags = np.atleast_1d(np.asarray(in_rest_time, dtype=bool))
        if flags.shape != severities.shape:
            msg = "'in_rest_time' must carry one flag per stretch."
            raise ValueError(msg)
        if which == "night" and np.any(flags):
            msg = "rest times are hours of the day (3.7.4); the night has none."
            raise ValueError(msg)
        weights = np.where(flags, REST_TIME_WEIGHT, 1.0)
    return float(np.sqrt(np.sum(weights * durations * severities**2) / total))


def admissible_exposure_s(
    kb_ftm: float, a_r: float, *, time_of_day: str = "day"
) -> float:
    r"""How long a source may act before :math:`KB_{FTr}` reaches :math:`A_r`.

    Formula (4b) turned around, as Example 2 of Annex C does it:
    :math:`T_e = (A_r / KB_{FTm})^2 \, T_r`. Longer than the period means
    the source may run all day and still keep to :math:`A_r`.

    :param kb_ftm: :math:`KB_{FTm}` of the source, positive.
    :param a_r: :math:`A_r`, the guide value it is held to.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :return: The exposure, in seconds.
    :raises ValueError: For a non-positive severity or guide value, or an
        unknown time of day.
    """
    severity = require_positive(kb_ftm, "kb_ftm")
    guide = require_positive(a_r, "a_r")
    total = ASSESSMENT_PERIOD_S[
        require_choice(str(time_of_day), "time_of_day", _PERIODS)
    ]
    return (guide / severity) ** 2 * total


def admissible_trains_per_hour(kb_ftm: float, a_r: float) -> float:
    r"""How many trains an hour keep :math:`KB_{FTr}` at :math:`A_r` (Figure D.1).

    With one class of train and each train occupying one clock interval,
    Formula (A.4) reads :math:`KB_{FTr} = KB_{FTm}\sqrt{n / 120}` for
    :math:`n` trains an hour, so the most an hour may carry is
    :math:`120 (A_r / KB_{FTm})^2`. Annex D reads the figure at 7 trains for
    an :math:`A_r` of 0,05 and 14 for 0,07, both at a :math:`KB_{FTm}` of 0,2.

    :param kb_ftm: :math:`KB_{FTm}` of one passage, positive.
    :param a_r: :math:`A_r`.
    :return: Trains per hour, not rounded; the standard rounds down.
    :raises ValueError: For a non-positive severity or guide value.
    """
    severity = require_positive(kb_ftm, "kb_ftm")
    guide = require_positive(a_r, "a_r")
    return _TAKTE_PER_HOUR * (guide / severity) ** 2


def railway_takt_maximum_rms(kb_fti: ArrayLike) -> float:
    r"""The clock maximum r.m.s. of one class of train, Formula (A.1).

    The root of the mean square of the clock maxima the trains of the class
    occupied, :math:`Z_j` of them, with nothing counted for the intervals
    between trains: Formula (A.1b), with the root Formula (A.1a) and the
    worked Example 8 carry and the print of (A.1b) lost. The rule of Formula
    (3) that a maximum at or below 0,1 enters as zero applies here as well.

    :param kb_fti: The clock maxima the class occupied, dimensionless.
    :return: :math:`KB_{FTm,j}`.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    return takt_maximum_rms(_maxima(kb_fti))


def _maxima(kb_fti: ArrayLike) -> NDArray[np.float64]:
    values = require_finite_array(kb_fti, "kb_fti")
    if np.any(values < 0.0):
        msg = "'kb_fti' must not be negative; a clock maximum never is."
        raise ValueError(msg)
    return values


def railway_takt_spread(kb_fti: ArrayLike) -> float:
    r"""The standard deviation of the square of the clock maxima, Formula (A.2).

    :math:`s(KB^2_{FTm,j}) = \sqrt{\frac{1}{Z_j - 1} \sum_i (KB^2_{FTi,j} -
    KB^2_{FTm,j})^2}`, on the square because it is the square that Formula
    (A.3) averages, so the spread of :math:`KB_{FTr}` follows from it by
    adding and subtracting it there. The maxima enter as they enter
    :func:`railway_takt_maximum_rms`, a value at or below 0,1 as zero, so the
    spread is about the mean square that function returns.

    :param kb_fti: The clock maxima the class occupied, at least two.
    :return: :math:`s(KB^2_{FTm,j})`.
    :raises ValueError: For fewer than two maxima, or a bad input.
    """
    values = _maxima(kb_fti)
    if values.size < _MIN_MAXIMA_FOR_SPREAD:
        msg = "'kb_fti' must hold at least two clock maxima for a spread."
        raise ValueError(msg)
    squares = np.where(values <= TAKT_SUPPRESSION_THRESHOLD, 0.0, values) ** 2
    return float(np.sqrt(np.sum((squares - np.mean(squares)) ** 2) / (values.size - 1)))


@dataclass(frozen=True)
class RailwayAssessment:
    r"""The assessment vibration severity of a railway, Formula (A.3).

    :ivar kb_ftr: :math:`KB_{FTr}` over the assessment period.
    :ivar kb_ftm: :math:`KB_{FTm,j}` of each class of train.
    :ivar occupied_takte: :math:`M_j`, the clock intervals each class occupies
        in the period.
    :ivar lower: :math:`KB_{FTr}` with every class's mean square one spread
        below its value, or ``None`` when no spread was given.
    :ivar upper: The same, one spread above.
    :ivar time_of_day: ``"day"`` or ``"night"``.
    """

    kb_ftr: float
    kb_ftm: NDArray[np.float64]
    occupied_takte: NDArray[np.int64]
    lower: float | None
    upper: float | None
    time_of_day: str


def railway_assessment_severity(
    kb_ftm: ArrayLike,
    occupied_takte: ArrayLike,
    *,
    time_of_day: str = "day",
    spread: ArrayLike | None = None,
) -> RailwayAssessment:
    r"""The assessment vibration severity of a railway, Formulae (A.3) and (A.4).

    :math:`KB_{FTr} = \sqrt{\frac{1}{N_r} \sum_j M_j KB^2_{FTm,j}}`: each class
    of train weighted by the clock intervals it occupies in the period, out
    of the 1920 of a day or the 960 of a night. With one class that is
    Formula (A.4). Given the spread of Formula (A.2) for each class, the same
    sum is formed with each mean square one spread up and one down, which is
    how Example 8 reports :math:`0{,}325^{+0{,}059}_{-0{,}073}`.

    :param kb_ftm: :math:`KB_{FTm,j}`, one per class, as
        :func:`railway_takt_maximum_rms` gives them.
    :param occupied_takte: :math:`M_j`, the clock intervals each class
        occupies in the period, one per class, which is about the number of
        its trains in the period when a train occupies one interval.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :param spread: :math:`s(KB^2_{FTm,j})` of each class, or ``None``.
    :return: The severity and, with a spread, its interval, as a
        :class:`RailwayAssessment`.
    :raises ValueError: For mismatched or negative inputs, more occupied
        intervals than the period holds, or an unknown time of day.
    """
    severities = require_finite_array(kb_ftm, "kb_ftm")
    takte = require_finite_array(occupied_takte, "occupied_takte")
    if takte.shape != severities.shape:
        msg = "'kb_ftm' and 'occupied_takte' must match, one entry per class."
        raise ValueError(msg)
    if (
        np.any(severities < 0.0)
        or np.any(takte < 0.0)
        or not np.all(takte == np.round(takte))
    ):
        msg = "'kb_ftm' must not be negative and 'occupied_takte' must be whole and not negative."
        raise ValueError(msg)
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    total = ASSESSMENT_TAKT_COUNT[which]
    if float(np.sum(takte)) > total:
        msg = f"the classes occupy {int(np.sum(takte))} clock intervals, more than the {total} of the {which}."
        raise ValueError(msg)
    squares = severities**2

    def severity(mean_squares: NDArray[np.float64]) -> float:
        return float(np.sqrt(np.sum(takte * np.maximum(mean_squares, 0.0)) / total))

    lower = upper = None
    if spread is not None:
        spreads = require_finite_array(spread, "spread")
        if spreads.shape != severities.shape or np.any(spreads < 0.0):
            msg = "'spread' must carry one non-negative value per class."
            raise ValueError(msg)
        lower = severity(squares - spreads)
        upper = severity(squares + spreads)
    return RailwayAssessment(
        kb_ftr=severity(squares),
        kb_ftm=severities,
        occupied_takte=takte.astype(np.int64),
        lower=lower,
        upper=upper,
        time_of_day=which,
    )


def kb_from_peak_velocity(peak_velocity_mm_s: float, frequency_hz: float) -> float:
    r"""The KB value of a peak velocity at a frequency, Formula (6).

    :math:`KB = \frac{1}{\sqrt 2}\, \frac{v_\mathrm{max}}{\sqrt{1 + (f_o/f)^2}}`
    with :math:`f_o` = 5,6 Hz, the corner of the KB weighting: the value the
    weighted severity settles at for a sine of that peak and frequency, which
    the note under the formula says is the KB of the 1975 edition.

    :param peak_velocity_mm_s: :math:`v_\mathrm{max}`, in millimetres per
        second.
    :param frequency_hz: :math:`f`, the frequency of the record, in hertz.
    :return: :math:`KB`, dimensionless.
    :raises ValueError: For a negative velocity or a non-positive frequency.
    """
    peak = require_non_negative(peak_velocity_mm_s, "peak_velocity_mm_s")
    freq = require_positive(frequency_hz, "frequency_hz")
    return peak / math.sqrt(2.0) / math.sqrt(1.0 + (KB_CORNER_HZ / freq) ** 2)


def kb_fmax_from_peak_velocity(
    peak_velocity_mm_s: float, frequency_hz: float, *, kind: str
) -> float:
    r"""An estimate of :math:`KB_{F\mathrm{max}}` from an unweighted record, Formula (7).

    :math:`KB^*_{F\mathrm{max}} = KB \cdot c_F`, Formula (6) scaled by the
    factor of Table 3 for the kind of vibration. An estimate, which is what
    the asterisk marks: Table 3 puts its factors at about 15 % either way.

    :param peak_velocity_mm_s: :math:`v_\mathrm{max}`, in millimetres per
        second.
    :param frequency_hz: :math:`f`, in hertz.
    :param kind: The row of Table 3, as :data:`PEAK_TO_KB_FACTORS` keys it:
        ``"harmonic"`` (little distortion, a sawmill at a distance),
        ``"harmonic_distorted"`` (more than about 20 %),
        ``"stochastic_resonant"`` and ``"stochastic"`` (looms, pile driving,
        with and without a resonating floor), ``"single_event_resonant"``
        and ``"single_event"``.
    :return: :math:`KB^*_{F\mathrm{max}}`.
    :raises ValueError: For a bad velocity or frequency, or an unknown kind.
    """
    factor = PEAK_TO_KB_FACTORS[
        require_choice(str(kind), "kind", tuple(PEAK_TO_KB_FACTORS))
    ]
    return kb_from_peak_velocity(peak_velocity_mm_s, frequency_hz) * factor


@dataclass(frozen=True)
class PeopleAssessment:
    r"""The verdict of Clause 6.2 on one immission, and how it was reached.

    :ivar complies: Whether the requirement of the standard is met.
    :ivar criterion: The comparison that decided it: ``"A_u"`` when
        :math:`KB_{F\mathrm{max}}` kept to the lower value, or exceeded it by
        less than the measurement is uncertain by; ``"A_o"`` when it exceeded
        the upper one or, for a rare short event, kept to it; and ``"A_r"``
        when :math:`KB_{FTr}` decided.
    :ivar kb_fmax: :math:`KB_{F\mathrm{max}}` as assessed.
    :ivar kb_ftr: :math:`KB_{FTr}`, or ``None`` when it was not needed.
    :ivar guide: The three guide values it was held to.
    :ivar source: The kind of source the rules were read for.
    :ivar within_uncertainty: Whether the verdict rests on the 15 % of 5.4:
        :math:`KB_{F\mathrm{max}}` above :math:`A_u` but by less than a
        measurement of :math:`KB_F` is uncertain by, which Annex C Example 3
        concludes "can as a rule still be regarded as met". A stricter reading
        treats such a verdict as open.
    """

    complies: bool
    criterion: str
    kb_fmax: float
    kb_ftr: float | None
    guide: GuideValues
    source: str
    within_uncertainty: bool

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two assessment quantities against the three guide values.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_people_assessment`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_people_assessment

        check_language(language)
        return plot_people_assessment(self, ax=ax, language=language, **kwargs)


def assess_people_in_buildings(
    kb_fmax: float,
    guide: GuideValues,
    *,
    kb_ftr: float | None = None,
    source: str = "general",
    rare_short_events: bool = False,
) -> PeopleAssessment:
    r"""Read the guide values in the order of Clause 6.2 (Figure 2).

    :math:`KB_{F\mathrm{max}}` at or below :math:`A_u` meets the requirement,
    and so, as a rule, does one above it by less than the 15 % of 5.4 that a
    measurement of :math:`KB_F` is uncertain by, which is how the standard's
    own Example 3 concludes on 0,17 against an :math:`A_u` of 0,15; the
    verdict says so in ``within_uncertainty``. Above :math:`A_o` it is not
    met, unless the source is a railway, which 6.5.3.1 judges on :math:`A_u`
    and :math:`A_r` alone. Between the two, up to three short events a day
    are met as they are (6.5.1), and anything else is decided by
    :math:`KB_{FTr}` against :math:`A_r`, which has to be supplied then: it is
    formed from the record by :func:`assessment_vibration_severity` or, for a
    railway, by :func:`railway_assessment_severity`. The note to 6.2 says when
    that is not worth doing: a steady vibration acting for much longer than
    4 h by day or 2 h by night keeps to :math:`A_r` only if it keeps to
    :math:`A_u`.

    Each comparison is made at the decimals the guide value is printed with,
    which is how Example 4 reads a :math:`KB_{FTr}` of 0,154 as meeting an
    :math:`A_r` of 0,15; and the standard says the values are not to be
    applied mechanically in any case.

    :param kb_fmax: :math:`KB_{F\mathrm{max}}`, the largest of the three
        directions.
    :param guide: The guide values, from :func:`guide_values` or
        :func:`construction_guide_values`.
    :param kb_ftr: :math:`KB_{FTr}`, needed only when the verdict comes down
        to it.
    :param source: ``"general"`` (default), ``"road"``, ``"railway"``,
        ``"urban_railway"`` or ``"quarry_blasting"``, which is a rare short
        event by definition.
    :param rare_short_events: Whether the immission is at most three short
        events a day, such as blasting, which 6.5.1 judges on :math:`A_o`
        alone.
    :return: The verdict, as a :class:`PeopleAssessment`.
    :raises ValueError: For a negative severity, an unknown source, or a
        verdict that needs :math:`KB_{FTr}` without one given.
    """
    peak = require_non_negative(kb_fmax, "kb_fmax")
    kind = require_choice(str(source), "source", _SOURCES)
    rare = rare_short_events or kind == "quarry_blasting"

    def verdict(
        *, complies: bool, criterion: str, kb_ftr: float | None, uncertain: bool = False
    ) -> PeopleAssessment:
        return PeopleAssessment(
            complies=complies,
            criterion=criterion,
            kb_fmax=peak,
            kb_ftr=kb_ftr,
            guide=guide,
            source=kind,
            within_uncertainty=uncertain,
        )

    if _keeps_to(peak, guide.a_u):
        return verdict(complies=True, criterion="A_u", kb_ftr=None)
    if peak <= guide.a_u * (1.0 + KB_UNCERTAINTY_PERCENT / 100.0):
        return verdict(complies=True, criterion="A_u", kb_ftr=None, uncertain=True)
    # A railway skips the upper value: 6.5.3.1 judges it on A_u and A_r, and
    # 6.5.3.5 has its own night-time thresholds for looking into the cause of
    # single clock maxima, which are not a verdict either.
    if kind not in _RAILWAYS:
        if not _keeps_to(peak, guide.a_o):
            return verdict(complies=False, criterion="A_o", kb_ftr=None)
        if rare:
            return verdict(complies=True, criterion="A_o", kb_ftr=None)
    if kb_ftr is None:
        msg = (
            f"KB_Fmax = {peak:g} exceeds A_u = {guide.a_u:g}, so the verdict comes "
            "down to KB_FTr against A_r; supply kb_ftr."
        )
        raise ValueError(msg)
    severity = require_non_negative(kb_ftr, "kb_ftr")
    return verdict(
        complies=_keeps_to(severity, guide.a_r), criterion="A_r", kb_ftr=severity
    )
