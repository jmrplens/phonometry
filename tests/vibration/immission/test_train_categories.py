#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the railway assessment of E DIN 4150-2:2023-08 by category of train.

Anchored on the two worked examples of Annex B that use it: Example 8, a
tram and a metro next to a new residential building, with the 47 passages
of Table B.1 and every derived value printed, and Example 9, an existing
line extended by a second track, with the four assessment severities of its
Nullfall and Planfall. The night values of Example 9 are printed with 920
intervals where 6.5.3.2 fixes 960; the tests hold the library to 960 and
say what the print gives.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

# Table B.1 (printed page 38): the clock maxima of the 47 passages.
METRO_NORTH = [
    0.017, 0.036, 0.024, 0.035, 0.025, 0.036, 0.035, 0.037, 0.041, 0.042, 0.068,
    0.040, 0.022, 0.025,
]  # fmt: skip
METRO_SOUTH = [
    0.076, 0.034, 0.025, 0.054, 0.033, 0.018, 0.033, 0.060, 0.019, 0.092, 0.030,
    0.019, 0.024, 0.058,
]  # fmt: skip
TRAM_EAST = [0.379, 0.369, 0.348, 0.288, 0.270, 0.549, 0.320, 0.290, 0.663]
TRAM_WEST = [0.649, 0.717, 0.658, 0.508, 0.423, 0.332, 0.735, 0.363, 0.441, 0.663]


def test_table_2_as_printed() -> None:
    """Printed page 20: the ten weighting factors, and E DIN 45672-3 Table E.1."""
    assert im.TRAIN_WEIGHTING_FACTORS == {
        "tram_metro": {"surface": 0.7, "underground": 1.0},
        "s_bahn": {"surface": 0.8, "underground": 1.0},
        "passenger": {"surface": 0.9, "underground": 1.0},
        "freight": {"surface": 1.0, "underground": 1.0},
        "freight_long": {"surface": 1.3, "underground": 1.3},
    }
    assert im.train_weighting_factor("tram_metro") == 0.7
    assert im.train_weighting_factor("tram_metro", alignment="underground") == 1.0
    assert im.train_weighting_factor("freight_long", alignment="underground") == 1.3
    with pytest.raises(ValueError, match="kind"):
        im.train_weighting_factor("people_mover")


def test_example_8_table_b1_by_formula_5_and_7() -> None:
    """B.8: the r.m.s. of each category with nothing zeroed, and 1,5 times it."""
    categories = [METRO_NORTH, METRO_SOUTH, TRAM_EAST, TRAM_WEST]
    assert [len(c) for c in categories] == [14, 14, 9, 10]
    kb_ftm = [im.train_category_rms(c) for c in categories]
    assert [round(v, 3) for v in kb_ftm] == [0.037, 0.047, 0.406, 0.568]
    kb_fmax = im.train_kb_fmax(kb_ftm)
    # Formed from the unrounded r.m.s.: 1,5 times the printed 0,568 would be 0,852.
    assert [round(v, 3) for v in kb_fmax] == [0.055, 0.070, 0.609, 0.851]
    assert im.railway_kb_fmax(kb_ftm) == pytest.approx(kb_fmax[3])


def test_example_8_the_metro_is_zeroed_in_formula_6_only() -> None:
    """B.8.3.4: 144 metros a track at alpha 1 with r.m.s. below 0,1 count as
    zero, 80 trams a track at alpha 0,7 give 0,099 8 over the 1920 intervals
    of the day, above A_r = 0,07.
    """
    kb_ftm = [
        im.train_category_rms(c)
        for c in (METRO_NORTH, METRO_SOUTH, TRAM_EAST, TRAM_WEST)
    ]
    kb_ftr = im.train_assessment_severity(
        kb_ftm, [144, 144, 80, 80], alpha=[1.0, 1.0, 0.7, 0.7]
    )
    # The print says 0,099 8, which only the three-decimal r.m.s. values of
    # Table B.1 give; the four-decimal ones it prints beside the formula, and
    # the passages themselves, give 0,099 7.
    assert kb_ftr == pytest.approx(0.0997, abs=0.00005)
    assert im.train_assessment_severity(
        [0.0365, 0.0468, 0.406, 0.568], [144, 144, 80, 80], alpha=[1.0, 1.0, 0.7, 0.7]
    ) == pytest.approx(0.0998, abs=0.00005)
    guide = im.guide_values("residential", edition="2023")
    verdict = im.assess_people_in_buildings(
        im.railway_kb_fmax(kb_ftm),
        guide,
        kb_ftr=kb_ftr,
        source="railway",
        edition="2023",
    )
    assert not verdict.complies
    assert verdict.criterion == "A_r"
    # By night the trams exceed the A_o of 0,2 for a new building (6.5.3.7).
    night = im.guide_values("residential", time_of_day="night", edition="2023")
    at_night = im.assess_people_in_buildings(
        im.railway_kb_fmax(kb_ftm), night, source="railway", edition="2023"
    )
    assert not at_night.complies
    assert at_night.criterion == "A_o"


def test_example_9_nullfall_and_planfall_by_formula_6() -> None:
    """B.9: 28 regional at 0,9 and 8 freight at 1,0 by day give 0,039; the
    planned case with a second track, one third of its freight over 600 m at
    1,3, gives 0,046 by day and, with the 960 intervals of the night, 0,094.
    The print divides the night by 920 and gets 0,096; see the errata.
    """
    nullfall_day = im.train_assessment_severity([0.24, 0.44], [28, 8], alpha=[0.9, 1.0])
    assert round(nullfall_day, 3) == 0.039
    planfall_day = im.train_assessment_severity(
        [0.24, 0.22, 0.44, 0.40, 0.44, 0.40],
        [17, 17, 4, 4, 2, 2],
        alpha=[0.9, 0.9, 1.0, 1.0, 1.3, 1.3],
    )
    assert round(planfall_day, 3) == 0.046
    nullfall_night = im.train_assessment_severity(
        [0.24, 0.44], [12, 18], alpha=[0.9, 1.0], time_of_day="night"
    )
    planfall_night = im.train_assessment_severity(
        [0.24, 0.22, 0.44, 0.40, 0.44, 0.40],
        [7, 7, 12, 12, 6, 6],
        alpha=[0.9, 0.9, 1.0, 1.0, 1.3, 1.3],
        time_of_day="night",
    )
    assert round(nullfall_night, 3) == 0.065
    assert round(planfall_night, 3) == 0.094
    # The print's 920 intervals reproduce its 0,066 and 0,096.
    assert nullfall_night * math.sqrt(960 / 920) == pytest.approx(0.066, abs=0.0005)
    assert planfall_night * math.sqrt(960 / 920) == pytest.approx(0.096, abs=0.0005)
    assert im.railway_kb_fmax([0.24, 0.44]) == pytest.approx(0.66)


def test_example_9_the_change_of_the_night_severity_exceeds_25_percent() -> None:
    """B.9.4: A_r = 0,07 exceeded by night and KB_FTr up by more than 25 %
    against the case without the project, so mitigation is to be looked into.
    """
    guide = im.railway_guide_values("mixed", time_of_day="night")
    assert guide == im.GuideValues(0.1, 0.6, 0.07, time_of_day="night", edition="2023")
    change = im.assess_railway_change(
        kb_fmax_before=0.66,
        kb_fmax_after=0.66,
        kb_ftr_before=0.065,
        kb_ftr_after=0.094,
        guide=guide,
        time_of_day="night",
    )
    assert not change.complies
    assert change.kb_fmax_met  # 0,66 above the 0,6 of a surface line, but no increase
    assert not change.kb_ftr_met
    assert change.kb_fmax_increase_percent == 0.0
    assert change.kb_ftr_increase_percent == pytest.approx(44.6, abs=0.1)
    within = im.assess_railway_change(
        kb_fmax_before=0.66,
        kb_fmax_after=0.7,
        kb_ftr_before=0.08,
        kb_ftr_after=0.09,
        guide=guide,
        time_of_day="night",
    )
    assert within.complies
    assert within.kb_ftr_increase_percent == pytest.approx(12.5)


def test_the_night_upper_value_of_a_new_line() -> None:
    """6.5.3.5: 0,6 on the surface anywhere, Table 1 underground in rows 1
    and 2, 0,3 underground in rows 3 to 5, and Table 1 by day.
    """
    assert im.railway_guide_values("residential", time_of_day="night").a_o == 0.6
    assert (
        im.railway_guide_values(
            "industrial", time_of_day="night", alignment="underground"
        ).a_o
        == 0.6
    )
    assert (
        im.railway_guide_values(
            "commercial", time_of_day="night", alignment="underground"
        ).a_o
        == 0.4
    )
    assert (
        im.railway_guide_values(
            "residential", time_of_day="night", alignment="underground"
        ).a_o
        == 0.3
    )
    assert im.railway_guide_values("residential") == im.guide_values(
        "residential", edition="2023"
    )
    # The draft's Table 1 cell: a mixed area's night A_u is 0,1.
    assert im.railway_guide_values("mixed", time_of_day="night").a_u == 0.1


def test_formula_6_suppresses_a_category_and_refuses_bad_inputs() -> None:
    assert im.train_assessment_severity(
        [0.1, 0.5], [10, 10], alpha=1.0
    ) == pytest.approx(0.5 * math.sqrt(10 / 1920))
    with pytest.raises(ValueError, match="one entry per category"):
        im.train_assessment_severity([0.3, 0.2], [10], alpha=1.0)
    with pytest.raises(ValueError, match="whole"):
        im.train_assessment_severity([0.3], [10.5], alpha=1.0)
    # Nothing bounds the trains by the intervals: two tracks can each carry
    # a train in the same interval, and the draft prints no such limit.
    assert im.train_assessment_severity(
        [0.3] * 6, [400] * 6, alpha=0.8, time_of_day="night"
    ) == pytest.approx(0.8 * 0.3 * math.sqrt(2400 / 960))
    with pytest.raises(ValueError, match="one value or one per category"):
        im.train_assessment_severity([0.3, 0.4, 0.5], [1, 1, 1], alpha=[1.0, 1.1])
    with pytest.raises(ValueError, match="never is"):
        im.train_category_rms([0.3, -0.1])
    with pytest.raises(ValueError, match="kb_fmax_after"):
        im.assess_railway_change(
            kb_fmax_before=0.5,
            kb_fmax_after=-0.5,
            kb_ftr_before=0.05,
            kb_ftr_after=0.05,
            guide=im.railway_guide_values("mixed"),
        )


def test_the_change_of_nothing_is_nothing() -> None:
    change = im.assess_railway_change(
        kb_fmax_before=0.0,
        kb_fmax_after=0.0,
        kb_ftr_before=0.0,
        kb_ftr_after=0.0,
        guide=im.railway_guide_values("mixed"),
    )
    assert change.complies
    assert change.kb_fmax_increase_percent == 0.0
    grown = im.assess_railway_change(
        kb_fmax_before=0.0,
        kb_fmax_after=6.0,
        kb_ftr_before=0.0,
        kb_ftr_after=0.2,
        guide=im.railway_guide_values("mixed"),
    )
    assert not grown.complies
    assert np.isinf(grown.kb_ftr_increase_percent)


def test_the_module_lists_what_it_publishes() -> None:
    from phonometry.vibration.immission import train_categories

    for name in train_categories.__all__:
        assert getattr(im, name) is getattr(train_categories, name)


def test_a_planned_case_within_a_u_is_met_before_any_change_is_looked_at() -> None:
    """Printed page 22, 6.5.3.6: the planned case is first held to A_u or A_r;
    a KB_Fmax at or below A_u settles it, however KB_FTr moved. The clause
    belongs to the draft, so 1999 guide values and the other period are
    refused.
    """
    guide = im.railway_guide_values("mixed", time_of_day="night")
    change = im.assess_railway_change(
        kb_fmax_before=0.10,
        kb_fmax_after=0.10,
        kb_ftr_before=0.05,
        kb_ftr_after=0.09,
        guide=guide,
        time_of_day="night",
    )
    assert change.complies
    assert change.kb_fmax_met
    assert change.kb_ftr_met
    assert change.kb_ftr_increase_percent == pytest.approx(80.0)
    with pytest.raises(ValueError, match="2023 edition"):
        im.assess_railway_change(
            kb_fmax_before=0.66,
            kb_fmax_after=0.66,
            kb_ftr_before=0.065,
            kb_ftr_after=0.094,
            guide=im.guide_values("mixed", time_of_day="night"),
            time_of_day="night",
        )
    with pytest.raises(ValueError, match="of the day"):
        im.assess_railway_change(
            kb_fmax_before=0.66,
            kb_fmax_after=0.66,
            kb_ftr_before=0.065,
            kb_ftr_after=0.094,
            guide=guide,
            time_of_day="day",
        )
