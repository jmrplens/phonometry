#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Railway vibration by category of train (E DIN 4150-2:2023-08).

The draft of August 2023 that is to replace DIN 4150-2:1999-06 rewrites the
assessment of a railway, and its Annex B works two examples through the new
formulae with every number printed. Example 8 is a tram and a metro next to
a new residential building: Table B.1 lists the clock maximum of each of 47
passages and the r.m.s. of each category by Formula (5), then 1,5 times it
by Formula (7), and the day's assessment severity by Formula (6) with the
weighting factors of Table 2. Example 9 is an existing line extended by a
second track: the assessment severity of the case without the project and
of the planned case, by day and by night. The draft's Table 1 changes one
cell of the 1999 table, and its Table 3 prints the days two to six of a
construction site that the 1999 Figure 3 made one read off a curve.

Every row runs the library on the example's inputs and compares with the
printed result at the decimals it is printed with. The two night rows of
Example 9 compare with the value the draft's own 960 intervals give, because
the print divides by 920 and gets 0,066 and 0,096 instead; the entry is in
``docs/ERRATA.md``.

Oracle: E DIN 4150-2:2023-08, Table 1 on printed page 14, Table 3 on printed
page 24, Table B.1 on printed page 38, Example 8 on printed page 39 and
Example 9 on printed page 44.
"""

from __future__ import annotations

import functools

import phonometry as ph

from ..registry import Outcome, numeric, register

_TRAINS = "Railway vibration by category of train (E DIN 4150-2:2023-08)"
_EDITION = "E DIN 4150-2:2023-08"

#: Half a unit in the last printed place.
_TWO_DECIMALS = 0.005
_THREE_DECIMALS = 0.0005
_FOUR_DECIMALS = 0.00005

#: Table B.1 (printed page 38): the clock maxima of the four categories.
_METRO_NORTH = (
    0.017, 0.036, 0.024, 0.035, 0.025, 0.036, 0.035, 0.037, 0.041, 0.042, 0.068,
    0.040, 0.022, 0.025,
)  # fmt: skip
_METRO_SOUTH = (
    0.076, 0.034, 0.025, 0.054, 0.033, 0.018, 0.033, 0.060, 0.019, 0.092, 0.030,
    0.019, 0.024, 0.058,
)  # fmt: skip
_TRAM_EAST = (0.379, 0.369, 0.348, 0.288, 0.270, 0.549, 0.320, 0.290, 0.663)
_TRAM_WEST = (0.649, 0.717, 0.658, 0.508, 0.423, 0.332, 0.735, 0.363, 0.441, 0.663)
_CATEGORIES = {
    "metro north": (_METRO_NORTH, 0.037, 0.055),
    "metro south": (_METRO_SOUTH, 0.047, 0.070),
    "tram east": (_TRAM_EAST, 0.406, 0.609),
    "tram west": (_TRAM_WEST, 0.568, 0.851),
}

#: Example 9 (printed page 44): the categories of the two cases, as
#: (KB_FTm,Zug, trains by day, trains by night, alpha).
_NULLFALL = ((0.24, 28, 12, 0.9), (0.44, 8, 18, 1.0))
_PLANFALL = (
    (0.24, 17, 7, 0.9),
    (0.22, 17, 7, 0.9),
    (0.44, 4, 12, 1.0),
    (0.40, 4, 12, 1.0),
    (0.44, 2, 6, 1.3),
    (0.40, 2, 6, 1.3),
)
_EXAMPLE_9 = {
    ("nullfall", "day"): 0.039,
    ("nullfall", "night"): 0.065,
    ("planfall", "day"): 0.046,
    ("planfall", "night"): 0.094,
}
_CASES = {"nullfall": _NULLFALL, "planfall": _PLANFALL}

#: Table 3 (printed page 24): a few of the cells the draft prints for the
#: days two to six, as (stage, days, A_u, A_r).
_TABLE_3 = (("I", 3, 0.67, 0.37), ("II", 5, 0.93, 0.67), ("III", 6, 1.27, 1.03))


def _chk_table_b1(name: str, quantity: str) -> Outcome:
    maxima, kb_ftm, kb_fmax = _CATEGORIES[name]
    rms = ph.vibration.train_category_rms(maxima)
    if quantity == "kb_ftm":
        return numeric(kb_ftm, rms, _THREE_DECIMALS, places=4)
    return numeric(
        kb_fmax, float(ph.vibration.train_kb_fmax([rms])[0]), _THREE_DECIMALS, places=4
    )


@register(
    _TRAINS,
    f"{_EDITION} Annex B, Example 8",
    "KB_FTr of the day by Formula (6), 144 metros at 1,0 and 80 trams at 0,7 a track "
    "(the print says 0,099 8, which its three-decimal r.m.s. give; its four-decimal "
    "inputs give 0,099 7)",
)
def _chk_example_8_kb_ftr() -> Outcome:
    kb_ftm = [ph.vibration.train_category_rms(c[0]) for c in _CATEGORIES.values()]
    computed = ph.vibration.train_assessment_severity(
        kb_ftm, [144, 144, 80, 80], alpha=[1.0, 1.0, 0.7, 0.7]
    )
    return numeric(0.0997, computed, _FOUR_DECIMALS, places=4)


def _chk_example_9(case: str, time_of_day: str) -> Outcome:
    rows = _CASES[case]
    counts = [row[1] if time_of_day == "day" else row[2] for row in rows]
    computed = ph.vibration.train_assessment_severity(
        [row[0] for row in rows],
        counts,
        alpha=[row[3] for row in rows],
        time_of_day=time_of_day,
    )
    return numeric(_EXAMPLE_9[(case, time_of_day)], computed, _THREE_DECIMALS, places=4)


@register(
    _TRAINS,
    f"{_EDITION} Table 1",
    "Night A_u of a mixed area, the one cell that changes",
)
def _chk_table_1() -> Outcome:
    computed = ph.vibration.guide_values(
        "mixed", time_of_day="night", edition="2023"
    ).a_u
    return numeric(0.1, computed, _FOUR_DECIMALS, places=2)


def _chk_table_3(stage: str, days: int, a_u: float, a_r: float, which: str) -> Outcome:
    guide = ph.vibration.construction_guide_values(days, stage=stage)
    if which == "A_u":
        return numeric(a_u, guide.a_u, _TWO_DECIMALS, places=3)
    return numeric(a_r, guide.a_r, _TWO_DECIMALS, places=3)


def _register_rows() -> None:
    for name in _CATEGORIES:
        register(
            _TRAINS,
            f"{_EDITION} Annex B, Table B.1",
            f"KB_FTm,Zug of the {name} by Formula (5)",
        )(functools.partial(_chk_table_b1, name, "kb_ftm"))
        register(
            _TRAINS,
            f"{_EDITION} Annex B, Table B.1",
            f"KB_Fmax,Zug of the {name} by Formula (7)",
        )(functools.partial(_chk_table_b1, name, "kb_fmax"))
    for case, time_of_day in _EXAMPLE_9:
        note = (
            " (the print divides by 920 and gets 0,066)"
            if (case, time_of_day) == ("nullfall", "night")
            else ""
        )
        if (case, time_of_day) == ("planfall", "night"):
            note = " (the print divides by 920 and gets 0,096)"
        register(
            _TRAINS,
            f"{_EDITION} Annex B, Example 9",
            f"KB_FTr of the {case} by {time_of_day}, Formula (6) with N_r = {ph.vibration.ASSESSMENT_TAKT_COUNT[time_of_day]}{note}",
        )(functools.partial(_chk_example_9, case, time_of_day))
    for stage, days, a_u, a_r in _TABLE_3:
        for which in ("A_u", "A_r"):
            register(
                _TRAINS,
                f"{_EDITION} Table 3",
                f"{which} of stage {stage} for {days} working days, as printed",
            )(functools.partial(_chk_table_3, stage, days, a_u, a_r, which))


_register_rows()
