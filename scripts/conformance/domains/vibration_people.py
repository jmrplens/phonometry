#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Vibration and the people in a building (DIN 4150-2).

DIN 4150-2 is the assessment the DIN 45669-1 meter's readings are judged by,
and its Annex C works eight examples through the procedure with every
intermediate number printed. Those numbers are the rows: the admissible
exposure Example 2 solves Formula (4b) for, the assessment vibration severity
of two hammers by Formula (4a) and again with one of them in the rest hours
by Formula (5), the estimate of Formula (7) from a peak velocity, and the
whole of Example 8, a railway with two classes of train, from the clock
maximum r.m.s. of each class and the spread of its square to the assessment
severity of Formula (A.3) and the interval the spread puts on it. Annex D
reads two points off Figure D.1, and Figure 3 draws the interpolation of
Table 2 for two to six days, both reproduced here.

Every row runs the library on the example's inputs and compares with the
printed result at the decimals it is printed with.

Oracle: DIN 4150-2:1999-06, Figure 3 on printed page 9, Annex C on printed
pages 13 to 18 and Annex D on printed page 19.
"""

from __future__ import annotations

import functools
import math

import numpy as np

import phonometry as ph

from ..registry import Outcome, numeric, register

_PEOPLE = "Vibration and people in buildings (DIN 4150-2)"
_EDITION = "DIN 4150-2:1999-06"
_HOUR = 3600.0

#: Half a unit in the last printed place, by the decimals the example prints.
_TWO_DECIMALS = 0.005
_THREE_DECIMALS = 0.0005

#: Example 8 (printed pages 17 and 18): the clock maxima of the two classes,
#: the intervals each occupies in 16 h, and what the standard prints for them.
_CLASS_1 = (0.92, 0.6, 0.9)
_CLASS_2 = (0.2, 0.24)
_OCCUPIED = (288, 192)
_EXAMPLE_8 = {
    "kb_ftm_1": 0.82,
    "kb_ftm_2": 0.22,
    "spread_1": 0.27,
    "spread_2": 0.012,
    "kb_ftr": 0.325,
    "upper": 0.059,
    "lower": 0.073,
    "whole_record": 0.325,
    "peaks_only": 0.318,
}

#: Figure 3 (printed page 9): the stage I A_u for two to six working days,
#: read off the steps of the figure.
_FIGURE_3 = {2: 0.73, 3: 0.67, 4: 0.6, 5: 0.53, 6: 0.47}

#: Annex D (printed page 19): the trains an hour Figure D.1 allows at
#: KB_FTm = 0,2 for two values of A_r.
_FIGURE_D1 = {0.05: 7, 0.07: 14}


@register(_PEOPLE, f"{_EDITION} Annex C, Example 2", "Admissible exposure at A_r, h")
def _chk_example_2() -> Outcome:
    hours = ph.vibration.admissible_exposure_s(0.23, 0.07) / _HOUR
    return numeric(1.48, hours, _TWO_DECIMALS, unit="h", places=3)


@register(
    _PEOPLE, f"{_EDITION} Annex C, Example 4", "KB_FTr of two hammers, Formula (4a)"
)
def _chk_example_4() -> Outcome:
    computed = ph.vibration.assessment_vibration_severity(
        [0.16, 0.39], [6.0 * _HOUR, 1.5 * _HOUR]
    )
    return numeric(0.15, computed, _TWO_DECIMALS, places=3)


@register(
    _PEOPLE,
    f"{_EDITION} Annex C, Example 5",
    "KB_FTr with hammer b) in the rest hours, Formula (5)",
)
def _chk_example_5() -> Outcome:
    computed = ph.vibration.assessment_vibration_severity(
        [0.16, 0.39], [6.0 * _HOUR, 1.5 * _HOUR], in_rest_time=[False, True]
    )
    return numeric(0.20, computed, _TWO_DECIMALS, places=3)


@register(
    _PEOPLE,
    f"{_EDITION} Annex C, Example 6",
    "KB_FTr of hammer a) over 16 h with 4 h in the rest hours",
)
def _chk_example_6() -> Outcome:
    computed = ph.vibration.assessment_vibration_severity(
        [0.16, 0.16], [12.0 * _HOUR, 4.0 * _HOUR], in_rest_time=[False, True]
    )
    return numeric(0.18, computed, _TWO_DECIMALS, places=3)


@register(
    _PEOPLE,
    f"{_EDITION} Annex C, Example 7",
    "KB*_Fmax from 4 mm/s at 14 Hz, Formulae (6) and (7)",
)
def _chk_example_7() -> Outcome:
    computed = ph.vibration.kb_fmax_from_peak_velocity(
        4.0, 14.0, kind="single_event_resonant"
    )
    return numeric(2.1, computed, 0.05, places=3)


def _chk_example_8(quantity: str) -> Outcome:
    vibration = ph.vibration
    kb_ftm = (
        vibration.railway_takt_maximum_rms(_CLASS_1),
        vibration.railway_takt_maximum_rms(_CLASS_2),
    )
    spread = (
        vibration.railway_takt_spread(_CLASS_1),
        vibration.railway_takt_spread(_CLASS_2),
    )
    result = vibration.railway_assessment_severity(kb_ftm, _OCCUPIED, spread=spread)
    upper = result.upper if result.upper is not None else math.nan
    lower = result.lower if result.lower is not None else math.nan
    whole = np.zeros(20)
    whole[:5] = [0.92, 0.6, 0.2, 0.9, 0.24]
    peaks = np.zeros(20)
    peaks[:3] = _CLASS_1
    computed = {
        "kb_ftm_1": (kb_ftm[0], _TWO_DECIMALS),
        "kb_ftm_2": (kb_ftm[1], _TWO_DECIMALS),
        "spread_1": (spread[0], _TWO_DECIMALS),
        "spread_2": (spread[1], _THREE_DECIMALS),
        "kb_ftr": (result.kb_ftr, _THREE_DECIMALS),
        "upper": (upper - result.kb_ftr, _THREE_DECIMALS),
        # The example carries its rounded intermediates into this one, and
        # the print sits a unit in the third place from the unrounded chain.
        "lower": (result.kb_ftr - lower, 0.0015),
        "whole_record": (vibration.takt_maximum_rms(whole), _THREE_DECIMALS),
        "peaks_only": (vibration.takt_maximum_rms(peaks), _THREE_DECIMALS),
    }
    value, tolerance = computed[quantity]
    return numeric(_EXAMPLE_8[quantity], value, tolerance, places=4)


def _chk_figure_3(days: int) -> Outcome:
    computed = ph.vibration.construction_guide_values(days, stage="I").a_u
    return numeric(_FIGURE_3[days], computed, _TWO_DECIMALS, places=3)


def _chk_figure_d1(a_r: float) -> Outcome:
    computed = math.floor(ph.vibration.admissible_trains_per_hour(0.2, a_r))
    return numeric(float(_FIGURE_D1[a_r]), float(computed), 1e-9, places=0)


def _register_example_8() -> None:
    labels = {
        "kb_ftm_1": "KB_FTm of class 1 by Formula (A.1)",
        "kb_ftm_2": "KB_FTm of class 2 by Formula (A.1)",
        "spread_1": "s(KB²_FTm) of class 1 by Formula (A.2)",
        "spread_2": "s(KB²_FTm) of class 2 by Formula (A.2)",
        "kb_ftr": "KB_FTr of both classes by Formula (A.3)",
        "upper": "KB_FTr one spread up, above the value",
        "lower": "KB_FTr one spread down, below the value",
        "whole_record": "KB_FTm over the 20 intervals of the record, Formula (3)",
        "peaks_only": "KB_FTm over the record with the passage maxima alone",
    }
    for quantity, label in labels.items():
        register(_PEOPLE, f"{_EDITION} Annex C, Example 8", label)(
            functools.partial(_chk_example_8, quantity)
        )


def _register_figures() -> None:
    for days in _FIGURE_3:
        register(
            _PEOPLE,
            f"{_EDITION} Figure 3",
            f"Stage I A_u interpolated for {days} working days",
        )(functools.partial(_chk_figure_3, days))
    for a_r in _FIGURE_D1:
        register(
            _PEOPLE,
            f"{_EDITION} Annex D, Figure D.1",
            f"Trains an hour at KB_FTm = 0,2 for A_r = {a_r:g}",
        )(functools.partial(_chk_figure_d1, a_r))


_register_example_8()
_register_figures()
