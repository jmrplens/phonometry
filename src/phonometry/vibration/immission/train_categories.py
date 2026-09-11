#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Railway vibration by category of train (E DIN 4150-2:2023-08, 6.5.3).

The draft of August 2023 that is to replace DIN 4150-2:1999-06 rewrites how a
railway is assessed for the people in a building. The 1999 edition formed the
clock maximum r.m.s. over the intervals a class of train occupied, raised the
guide values by 1,5 for an urban line and left the upper value out of the
railway's verdict altogether. The draft keeps the two assessment quantities
and changes what feeds them:

- every train passage counts as **one** clock interval, however long it
  lasts (6.5.3.2), so :math:`KB_{FTm,Zug}` of Formula (5) is the r.m.s. of one
  clock maximum per passage, with nothing set to zero below 0,1;
- :math:`KB_{F\mathrm{max}}` of a railway is not the largest clock maximum
  observed but **1,5 times** :math:`KB_{FTm,Zug}` of each category and the
  largest of those (Formulae (7) and (8)), because a single passage with a
  flat spot on a wheel is not what the line is like;
- the assessment vibration severity of Formula (6) weights each category by
  the number of its trains in the period, out of the 1920 or 960 clock
  intervals of the day or the night, and by a **weighting factor**
  :math:`\alpha_{Zug}` of Table 2 for the kind of train and whether the line
  runs on the surface or underground: 0,7 for a tram on the surface, 1,3 for
  a freight train over 600 m anywhere. A category whose r.m.s. is at or below
  0,1 enters Formula (6) as zero;
- a line to be built new is held at night to an upper value of its own
  (6.5.3.5): 0,6 on the surface in any area, and underground the Table 1
  value in an industrial or commercial area and 0,3 elsewhere;
- an existing line that is altered or extended is judged by the **change**
  it brings (6.5.3.6): the planned case is first held to the guide values as
  any immission is, and where :math:`A_o` or :math:`A_r` is exceeded the
  requirement still counts as met if :math:`KB_{F\mathrm{max}}` or
  :math:`KB_{FTr}` grows by less than 25 % against the case without the
  project, which is the least increase a laboratory study found people to
  notice. The clause says the requirements are met if *one* of its
  conditions holds, and its own Example 9 sends a line whose
  :math:`KB_{F\mathrm{max}}` does not change at all to mitigation because
  :math:`KB_{FTr}` grows by more; every condition that applies has to hold
  here, as in the example, and the sentence is in ``docs/ERRATA.md``.

E DIN 45672-3:2023-02, the draft prediction method for railways, takes the
sum of Formula (6) as its Formula (11) and the same factors as its Annex E,
though it prints the sum without the sentence that zeroes a category at or
below 0,1, so the functions here serve both; the prediction chain that leads
up to them is in :mod:`phonometry.vibration.immission.railway_prediction`.

Every example of Annex B that the draft works with these formulae is a
conformance row: the 47 passages of Table B.1 and their eight derived values,
and the four assessment severities of Example 9. The two night-time
severities of those four are printed over 920 intervals where 6.5.3.2 fixes
960, and the day-time one of Example 8 is printed as 0,099 8 where its own
four-decimal inputs give 0,099 7; both are registered in ``docs/ERRATA.md``,
and the rows run the standard's own 960 and its own inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_finite_array,
    require_non_negative,
)
from .people import (
    _PERIODS,
    ASSESSMENT_TAKT_COUNT,
    GUIDE_VALUES_2023,
    GuideValues,
    _keeps_to,
)
from .vibration_meter import TAKT_SUPPRESSION_THRESHOLD

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "RAILWAY_CHANGE_TOLERANCE_PERCENT",
    "RAILWAY_NEW_LINE_NIGHT_A_O",
    "TRAIN_KB_FMAX_FACTOR",
    "TRAIN_KINDS",
    "TRAIN_WEIGHTING_FACTORS",
    "RailwayChange",
    "assess_railway_change",
    "railway_guide_values",
    "railway_kb_fmax",
    "train_assessment_severity",
    "train_category_rms",
    "train_kb_fmax",
    "train_weighting_factor",
]

#: The factor Formula (7) puts on :math:`KB_{FTm,Zug}` to estimate the
#: :math:`KB_{F\mathrm{max}}` of a category of train: 1,5. E DIN 45672-3
#: Formula (10) is the same number.
TRAIN_KB_FMAX_FACTOR: float = 1.5

#: The kinds of train Table 2 distinguishes, by the rules they run under:
#: trams, light rail and metros (BOStrab); S-Bahn; other passenger trains;
#: freight trains up to 600 m; and freight trains over 600 m (EBO).
TRAIN_KINDS: tuple[str, ...] = (
    "tram_metro",
    "s_bahn",
    "passenger",
    "freight",
    "freight_long",
)

#: Table 2 (printed page 20): the weighting factor :math:`\alpha_{Zug}` of
#: Formula (6) by kind of train and alignment of the line, ``"surface"`` or
#: ``"underground"``. E DIN 45672-3:2023-02 Table E.1 prints the same ten
#: values. A people mover or any other very short vehicle with a short
#: passage takes the tram row.
TRAIN_WEIGHTING_FACTORS: dict[str, dict[str, float]] = {
    "tram_metro": {"surface": 0.7, "underground": 1.0},
    "s_bahn": {"surface": 0.8, "underground": 1.0},
    "passenger": {"surface": 0.9, "underground": 1.0},
    "freight": {"surface": 1.0, "underground": 1.0},
    "freight_long": {"surface": 1.3, "underground": 1.3},
}

#: The upper guide value :math:`A_o` a line to be built new is held to at
#: night (6.5.3.5): 0,6 on the surface in any area; underground, the night
#: :math:`A_o` of Table 1 in an industrial or commercial area and 0,3 in a
#: mixed, residential or sensitive one. The same values bound the planned
#: case of an altered line (6.5.3.6 b)).
RAILWAY_NEW_LINE_NIGHT_A_O: dict[str, float] = {"surface": 0.6, "underground": 0.3}

#: The least increase of :math:`KB_{F\mathrm{max}}` or :math:`KB_{FTr}` that
#: an altered or extended line may bring where a guide value is exceeded
#: (6.5.3.6): 25 %, below which a laboratory study found no one notices.
RAILWAY_CHANGE_TOLERANCE_PERCENT: float = 25.0

_ALIGNMENTS = ("surface", "underground")
#: The areas of Table 1 rows 1 and 2, which keep their own night A_o
#: underground (6.5.3.5).
_UNDERGROUND_TABLE_AREAS = ("industrial", "commercial")
#: The edition 6.5.3 belongs to, which the guide values it is read with
#: must be of.
_DRAFT = "2023"


def train_weighting_factor(kind: str, *, alignment: str = "surface") -> float:
    r"""The weighting factor :math:`\alpha_{Zug}` of Table 2 for one category.

    :param kind: The kind of train, as :data:`TRAIN_KINDS` lists them.
    :param alignment: ``"surface"`` (default) or ``"underground"``.
    :return: :math:`\alpha_{Zug}`, dimensionless.
    :raises ValueError: For an unknown kind or alignment.
    """
    row = TRAIN_WEIGHTING_FACTORS[require_choice(str(kind), "kind", TRAIN_KINDS)]
    return row[require_choice(str(alignment), "alignment", _ALIGNMENTS)]


def _passages(kb_fti_zug: ArrayLike) -> NDArray[np.float64]:
    values = require_finite_array(kb_fti_zug, "kb_fti_zug")
    if np.any(values < 0.0):
        msg = "'kb_fti_zug' must not be negative; a clock maximum never is."
        raise ValueError(msg)
    return values


def train_category_rms(kb_fti_zug: ArrayLike) -> float:
    r"""The clock maximum r.m.s. of one category of train, Formula (5).

    :math:`KB_{FTm,Zug} = \sqrt{\frac{1}{Z}\sum_{i=1}^{Z} KB^2_{FTi,Zug}}` over
    the :math:`Z` passages measured, one clock maximum per passage whatever
    the passage lasted. Unlike Formula (1) and the 1999 edition's (A.1), a
    maximum at or below 0,1 enters as it is: the suppression is applied to
    the category's r.m.s. in Formula (6), not to the passages (C.2), because
    :math:`KB_{F\mathrm{max}}` of Formula (7) is formed from this value.

    :param kb_fti_zug: :math:`KB_{FTi,Zug}` of each passage, dimensionless.
    :return: :math:`KB_{FTm,Zug}`.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    values = _passages(kb_fti_zug)
    return float(np.sqrt(np.mean(values**2)))


def train_kb_fmax(kb_ftm_zug: ArrayLike) -> NDArray[np.float64]:
    r"""The :math:`KB_{F\mathrm{max},Zug}` of each category, Formula (7).

    :math:`KB_{F\mathrm{max},Zug} = 1{,}5 \cdot KB_{FTm,Zug}`, the estimate the
    draft uses instead of the largest clock maximum observed, which a single
    passage with an out-of-round wheel would decide. Formed from the value
    before rounding: Table B.1 prints 0,851 for a category whose r.m.s. it
    prints as 0,568.

    :param kb_ftm_zug: :math:`KB_{FTm,Zug}` of each category.
    :return: :math:`KB_{F\mathrm{max},Zug}` of each, in the same order.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    values = require_finite_array(kb_ftm_zug, "kb_ftm_zug")
    if np.any(values < 0.0):
        msg = "'kb_ftm_zug' must not be negative."
        raise ValueError(msg)
    return TRAIN_KB_FMAX_FACTOR * values


def railway_kb_fmax(kb_ftm_zug: ArrayLike) -> float:
    r"""The :math:`KB_{F\mathrm{max}}` of a railway, Formula (8).

    The largest :math:`KB_{F\mathrm{max},Zug}` of Formula (7) over the
    categories, which is what the draft compares with :math:`A_u` and
    :math:`A_o`.

    :param kb_ftm_zug: :math:`KB_{FTm,Zug}` of each category.
    :return: :math:`KB_{F\mathrm{max}}`.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    return float(np.max(train_kb_fmax(kb_ftm_zug)))


def train_assessment_severity(
    kb_ftm_zug: ArrayLike,
    trains: ArrayLike,
    *,
    alpha: ArrayLike,
    time_of_day: str = "day",
) -> float:
    r"""The assessment vibration severity of a railway, Formula (6).

    :math:`KB_{FTr} = \sqrt{\sum_{Zug} \frac{n_{Zug}}{N_r} (\alpha_{Zug}
    KB_{FTm,Zug})^2}`: each category weighted by the trains it runs in the
    period, out of the :math:`N_r` = 1920 clock intervals of the day or 960
    of the night, and by its factor of Table 2. A category whose r.m.s. is
    at or below 0,1 enters as zero. The rest hours of the day are not
    applied to a railway (6.5.3.2). E DIN 45672-3:2023-02 Formula (11) is
    the same sum, printed without the sentence on 0,1. The categories are at
    least one per track or direction and kind of train, and their trains are
    counted apart, so nothing bounds their sum by the intervals of the
    period: two tracks can each carry a train in the same interval.

    :param kb_ftm_zug: :math:`KB_{FTm,Zug}` of each category, as
        :func:`train_category_rms` gives them.
    :param trains: :math:`n_{Zug}`, the trains of each category in the
        period, from the timetable.
    :param alpha: :math:`\alpha_{Zug}` of each category, from
        :func:`train_weighting_factor`, or one value for all.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :return: :math:`KB_{FTr}`.
    :raises ValueError: For mismatched, negative or non-finite inputs, a
        count that is not whole, or an unknown time of day.
    """
    severities = require_finite_array(kb_ftm_zug, "kb_ftm_zug")
    counts = require_finite_array(trains, "trains")
    if counts.shape != severities.shape:
        msg = "'kb_ftm_zug' and 'trains' must match, one entry per category."
        raise ValueError(msg)
    try:
        factors = np.broadcast_to(
            require_finite_array(alpha, "alpha"), severities.shape
        ).astype(np.float64)
    except ValueError as error:
        msg = "'alpha' must be one value or one per category of 'kb_ftm_zug'."
        raise ValueError(msg) from error
    if (
        np.any(severities < 0.0)
        or np.any(counts < 0.0)
        or np.any(factors <= 0.0)
        or not np.all(counts == np.round(counts))
    ):
        msg = (
            "'kb_ftm_zug' and 'trains' must not be negative, 'trains' must be "
            "whole and 'alpha' positive."
        )
        raise ValueError(msg)
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    total = ASSESSMENT_TAKT_COUNT[which]
    counted = np.where(severities <= TAKT_SUPPRESSION_THRESHOLD, 0.0, severities)
    return float(np.sqrt(np.sum(counts * (factors * counted) ** 2) / total))


def railway_guide_values(
    area: str, *, time_of_day: str = "day", alignment: str = "surface"
) -> GuideValues:
    r"""The guide values a line to be built new is held to (6.5.3.5).

    :math:`A_u` and :math:`A_r` are Table 1 of the draft, by day and by
    night, and :math:`A_o` is Table 1 by day. At night the upper value is the
    line's own: 0,6 on the surface whatever the area; underground, the
    Table 1 value in an industrial or commercial area and 0,3 in a mixed,
    residential or sensitive one. The same values bound the planned case of
    an altered or extended line (6.5.3.6 b)).

    :param area: The row of Table 1, as :data:`~phonometry.vibration.GUIDE_VALUES`
        keys it.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :param alignment: ``"surface"`` (default) or ``"underground"``.
    :return: The three values, as a :class:`~phonometry.vibration.GuideValues`
        of the 2023 edition.
    :raises ValueError: For an unknown area, time of day or alignment.
    """
    kind = require_choice(str(area), "area", tuple(GUIDE_VALUES_2023))
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    where = require_choice(str(alignment), "alignment", _ALIGNMENTS)
    values = GUIDE_VALUES_2023[kind][which]
    if which == "day" or (where == "underground" and kind in _UNDERGROUND_TABLE_AREAS):
        return values
    return replace(values, a_o=RAILWAY_NEW_LINE_NIGHT_A_O[where])


@dataclass(frozen=True)
class RailwayChange:
    r"""The verdict of 6.5.3.6 on an altered or extended line.

    :ivar complies: Whether the requirements count as met for the planned
        case: :math:`KB_{F\mathrm{max}}` keeps to :math:`A_u`, or both the
        :math:`KB_{F\mathrm{max}}` and the :math:`KB_{FTr}` condition hold.
    :ivar kb_fmax_met: Whether :math:`KB_{F\mathrm{max}}` of the planned
        case keeps to :math:`A_u` or :math:`A_o`, or exceeds :math:`A_o` by
        an increase under 25 % against the case without the project.
    :ivar kb_ftr_met: Whether :math:`KB_{FTr}` of the planned case keeps to
        :math:`A_r`, or exceeds it by an increase under 25 %; true without
        looking when :math:`KB_{F\mathrm{max}}` keeps to :math:`A_u`, which
        settles the verdict on its own.
    :ivar kb_fmax_increase_percent: The increase of :math:`KB_{F\mathrm{max}}`,
        planned against existing, in per cent.
    :ivar kb_ftr_increase_percent: The same for :math:`KB_{FTr}`.
    :ivar guide: The guide values the planned case was held to.
    :ivar time_of_day: ``"day"`` or ``"night"``.
    """

    complies: bool
    kb_fmax_met: bool
    kb_ftr_met: bool
    kb_fmax_increase_percent: float
    kb_ftr_increase_percent: float
    guide: GuideValues
    time_of_day: str


def _increase_percent(before: float, after: float) -> float:
    # Both are non-negative already; a case without the project at zero has
    # no percentage to grow by, so any growth from it is unbounded.
    if before <= 0.0:
        return 0.0 if after <= 0.0 else float("inf")
    return (after / before - 1.0) * 100.0


def assess_railway_change(
    *,
    kb_fmax_before: float,
    kb_fmax_after: float,
    kb_ftr_before: float,
    kb_ftr_after: float,
    guide: GuideValues,
    time_of_day: str = "day",
) -> RailwayChange:
    r"""Judge an altered or extended line by the change it brings (6.5.3.6).

    The case without the project, the Prognosenullfall, is the existing
    line with its present or its forecast timetable; the planned case, the
    Prognoseplanfall, is the line with the project. The planned case is
    first held to the guide values in the order of 6.3: a
    :math:`KB_{F\mathrm{max}}` at or below :math:`A_u` meets the
    requirements on its own, and so does one at or below :math:`A_o` with a
    :math:`KB_{FTr}` at or below :math:`A_r`, and then the change is beside
    the point. Where :math:`KB_{F\mathrm{max}}` exceeds :math:`A_o`, or
    :math:`KB_{FTr}` exceeds :math:`A_r`, the requirements still count as
    met if the quantity grows by less than 25 % against the case without the
    project; otherwise mitigation is to be looked into. Example 9 of Annex B
    finds a night-time :math:`KB_{FTr}` of 0,096 against 0,066 before, an
    increase of over 25 % above an :math:`A_r` of 0,07, and sends the
    project to mitigation although its :math:`KB_{F\mathrm{max}}` does not
    change, which is why every condition that applies has to hold here and
    not one of them, as the clause is printed.

    :param kb_fmax_before: :math:`KB_{F\mathrm{max}}` of Formula (8) without
        the project.
    :param kb_fmax_after: The same with the project.
    :param kb_ftr_before: :math:`KB_{FTr}` of Formula (6) without the project.
    :param kb_ftr_after: The same with the project.
    :param guide: The guide values of the planned case, from
        :func:`railway_guide_values` for the night-time :math:`A_o` of
        6.5.3.6 b); they must be of the 2023 edition and of the same period.
    :param time_of_day: ``"day"`` (default) or ``"night"``.
    :return: The verdict, as a :class:`RailwayChange`.
    :raises ValueError: For a negative quantity, an unknown time of day, or
        guide values of the 1999 edition or of the other period.
    """
    fmax_before = require_non_negative(kb_fmax_before, "kb_fmax_before")
    fmax_after = require_non_negative(kb_fmax_after, "kb_fmax_after")
    ftr_before = require_non_negative(kb_ftr_before, "kb_ftr_before")
    ftr_after = require_non_negative(kb_ftr_after, "kb_ftr_after")
    which = require_choice(str(time_of_day), "time_of_day", _PERIODS)
    if guide.edition != _DRAFT or guide.time_of_day != which:
        msg = (
            "6.5.3.6 is a clause of the draft: the guide values must be of the "
            f"2023 edition and of the {which}, got {guide!r}."
        )
        raise ValueError(msg)
    fmax_increase = _increase_percent(fmax_before, fmax_after)
    ftr_increase = _increase_percent(ftr_before, ftr_after)
    tolerable = RAILWAY_CHANGE_TOLERANCE_PERCENT
    if _keeps_to(fmax_after, guide.a_u):
        fmax_met = ftr_met = True
    else:
        fmax_met = _keeps_to(fmax_after, guide.a_o) or fmax_increase < tolerable
        ftr_met = _keeps_to(ftr_after, guide.a_r) or ftr_increase < tolerable
    return RailwayChange(
        complies=fmax_met and ftr_met,
        kb_fmax_met=fmax_met,
        kb_ftr_met=ftr_met,
        kb_fmax_increase_percent=fmax_increase,
        kb_ftr_increase_percent=ftr_increase,
        guide=guide,
        time_of_day=which,
    )
