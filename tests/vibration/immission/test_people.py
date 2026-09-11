#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the assessment of DIN 4150-2:1999-06.

Anchored on the eight worked examples of Annex C, which print every
intermediate number, on the tables read off their pages, and on the two
readings of Figure D.1 that Annex D quotes. Where the standard prints a
result to two decimals the test holds the library to that rounding.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

HOUR = 3600.0


# -- Table 1 and the procedure of 6.2 (Examples 1, 3, 6) --------------------------


def test_table_1_as_printed() -> None:
    """Printed page 6, all thirty cells."""
    expected = {
        "industrial": ((0.4, 6.0, 0.2), (0.3, 0.6, 0.15)),
        "commercial": ((0.3, 6.0, 0.15), (0.2, 0.4, 0.1)),
        "mixed": ((0.2, 5.0, 0.1), (0.15, 0.3, 0.07)),
        "residential": ((0.15, 3.0, 0.07), (0.1, 0.2, 0.05)),
        "sensitive": ((0.1, 3.0, 0.05), (0.1, 0.15, 0.05)),
    }
    for area, (day, night) in expected.items():
        for period, cells in (("day", day), ("night", night)):
            guide = im.guide_values(area, time_of_day=period)
            values = (guide.a_u, guide.a_o, guide.a_r)
            assert values == cells, (area, period)


def test_example_1_meets_the_lower_value() -> None:
    """C.1: KB_Fmax = 0,25 against A_u = 0,3 of a commercial area, met."""
    guide = im.guide_values("commercial")
    verdict = im.assess_people_in_buildings(0.25, guide)
    assert verdict.complies
    assert verdict.criterion == "A_u"
    assert verdict.kb_ftr is None


def test_example_3_exceeds_a_u_within_the_measurement_uncertainty() -> None:
    """C.3: 0,17 against 0,15 by night in a mixed area, KB_FTr not needed as
    T_e = 8 h, and the excess is inside the 15 % of 5.4, so the standard
    concludes the requirement "can as a rule still be regarded as met".
    """
    guide = im.guide_values("mixed", time_of_day="night")
    verdict = im.assess_people_in_buildings(0.17, guide)
    assert verdict.complies
    assert verdict.criterion == "A_u"
    assert verdict.within_uncertainty
    assert verdict.kb_ftr is None
    # A hair over the 15 % and the verdict comes down to KB_FTr again.
    strict = im.assess_people_in_buildings(0.18, guide, kb_ftr=0.18)
    assert not strict.complies
    assert strict.criterion == "A_r"
    assert not strict.within_uncertainty


def test_a_reading_is_compared_as_printed_half_up() -> None:
    """Example 4 writes a KB_FTr of 0,154 as 0,15 and finds it at A_r = 0,15;
    0,155 is written 0,16, as a hand rounds, and is not.
    """
    guide = im.guide_values("commercial")
    assert im.assess_people_in_buildings(0.47, guide, kb_ftr=0.154).complies
    assert not im.assess_people_in_buildings(0.47, guide, kb_ftr=0.155).complies
    # A guide value raised by 1,5 carries three decimals and is compared at three.
    urban = im.guide_values("residential", time_of_day="night", source="urban_railway")
    assert urban.a_r == 0.075
    assert im.assess_people_in_buildings(
        0.9, urban, kb_ftr=0.0754, source="urban_railway"
    ).complies
    assert not im.assess_people_in_buildings(
        0.9, urban, kb_ftr=0.0755, source="urban_railway"
    ).complies


def test_quarry_blasting_takes_the_a_o_of_row_1_by_day_in_rows_3_and_4() -> None:
    """6.5.1: blasts on working days with warning, in the hours it names and
    one a day, are held to A_o = 6 in a mixed or residential area; not by
    night, and not elsewhere, and always as a rare short event.
    """
    quarry = im.guide_values("residential", source="quarry_blasting")
    assert quarry == im.GuideValues(0.15, 6.0, 0.07)
    assert im.guide_values("mixed", source="quarry_blasting").a_o == 6.0
    assert im.guide_values("commercial", source="quarry_blasting") == im.guide_values(
        "commercial"
    )
    night = im.guide_values(
        "residential", time_of_day="night", source="quarry_blasting"
    )
    assert night == im.guide_values("residential", time_of_day="night")
    verdict = im.assess_people_in_buildings(4.0, quarry, source="quarry_blasting")
    assert verdict.complies
    assert verdict.criterion == "A_o"
    assert im.BLASTING_EXCEPTION_KB_FMAX == 8.0
    assert im.RAILWAY_NIGHT_INVESTIGATION_KB == {"surface": 0.6, "underground": 0.3}


def test_example_6_meets_a_u_and_needs_no_a_r() -> None:
    """C.6: hammer a) at 0,23 against A_u = 0,3, met on A_u although the
    rest-time weighting would put KB_FTr at 0,18 above A_r = 0,15.
    """
    guide = im.guide_values("commercial")
    verdict = im.assess_people_in_buildings(0.23, guide)
    assert verdict.complies
    assert verdict.criterion == "A_u"
    kb_ftr = im.assessment_vibration_severity(
        [0.16, 0.16], [12.0 * HOUR, 4.0 * HOUR], in_rest_time=[False, True]
    )
    assert round(kb_ftr, 2) == 0.18
    assert kb_ftr > guide.a_r


def test_above_a_o_fails_unless_the_events_are_rare() -> None:
    """6.2 and 6.5.1: A_o ends the question either way."""
    guide = im.guide_values("residential")
    assert not im.assess_people_in_buildings(3.5, guide).complies
    assert im.assess_people_in_buildings(3.5, guide).criterion == "A_o"
    rare = im.assess_people_in_buildings(2.0, guide, rare_short_events=True)
    assert rare.complies
    assert rare.criterion == "A_o"


def test_example_7_a_blast_is_met_on_a_o_alone() -> None:
    """C.7: one event a day, KB_Fmax = 2 against A_o = 3 of a dwelling."""
    guide = im.guide_values("residential")
    verdict = im.assess_people_in_buildings(2.0, guide, rare_short_events=True)
    assert verdict.complies
    assert verdict.criterion == "A_o"


def test_between_the_values_the_verdict_needs_kb_ftr() -> None:
    guide = im.guide_values("residential")
    with pytest.raises(ValueError, match="supply kb_ftr"):
        im.assess_people_in_buildings(0.5, guide)


def test_a_railway_is_judged_on_a_u_and_a_r_only() -> None:
    """6.5.3.1 and 6.5.3.5: A_o is not a verdict for rail traffic."""
    guide = im.guide_values("residential", time_of_day="night", source="railway")
    verdict = im.assess_people_in_buildings(0.9, guide, kb_ftr=0.04, source="railway")
    assert verdict.complies
    assert verdict.criterion == "A_r"
    assert guide.a_o < 0.9


def test_an_urban_surface_railway_raises_a_u_and_a_r_by_half() -> None:
    """6.5.3.3: the factor 1,5 on A_u and A_r, not on A_o."""
    plain = im.guide_values("residential")
    urban = im.guide_values("residential", source="urban_railway")
    assert urban.a_u == pytest.approx(1.5 * plain.a_u)
    assert urban.a_r == pytest.approx(1.5 * plain.a_r)
    assert urban.a_o == plain.a_o


# -- Formulae (4a), (4b) and (5) (Examples 2, 4, 5) ----------------------------------


def test_example_2_admissible_exposure() -> None:
    """C.2: KB_FTm = 0,23 against A_r = 0,07 leaves T_e = 1,48 h of a 16 h day."""
    exposure = im.admissible_exposure_s(0.23, 0.07)
    assert round(exposure / HOUR, 2) == 1.48
    assert im.assessment_vibration_severity(0.23, exposure) == pytest.approx(0.07)


def test_example_4_two_hammers_formula_4a() -> None:
    """C.4: 6 h at 0,16 and 1,5 h at 0,39 over 16 h give 0,15, met at A_r.

    The unrounded value is 0,154, and the standard writes it as 0,15 and
    calls it met: the comparison is made at the decimals of Table 1.
    """
    kb_ftr = im.assessment_vibration_severity([0.16, 0.39], [6.0 * HOUR, 1.5 * HOUR])
    assert round(kb_ftr, 2) == 0.15
    assert kb_ftr > 0.15
    guide = im.guide_values("commercial")
    verdict = im.assess_people_in_buildings(0.47, guide, kb_ftr=kb_ftr)
    assert verdict.complies
    assert verdict.criterion == "A_r"


def test_example_5_hammer_b_in_the_rest_hours_formula_5() -> None:
    """C.5: the same 1,5 h weighted twice give 0,20, above A_r = 0,15."""
    kb_ftr = im.assessment_vibration_severity(
        [0.16, 0.39], [6.0 * HOUR, 1.5 * HOUR], in_rest_time=[False, True]
    )
    assert round(kb_ftr, 2) == 0.20
    assert kb_ftr > 0.15


def test_the_night_has_no_rest_hours_and_the_period_is_a_ceiling() -> None:
    with pytest.raises(ValueError, match="night has none"):
        im.assessment_vibration_severity(
            0.2, HOUR, time_of_day="night", in_rest_time=True
        )
    with pytest.raises(ValueError, match="more than the 8 h"):
        im.assessment_vibration_severity(0.2, 9.0 * HOUR, time_of_day="night")
    with pytest.raises(ValueError, match="one severity per stretch"):
        im.assessment_vibration_severity([0.2, 0.3], [HOUR])
    assert im.ASSESSMENT_PERIOD_S == {"day": 16.0 * HOUR, "night": 8.0 * HOUR}
    assert im.ASSESSMENT_TAKT_COUNT == {"day": 1920, "night": 960}


# -- Clause 7 (Example 7) -------------------------------------------------------------


def test_example_7_formula_6_and_7() -> None:
    """C.7: 4 mm/s at 14 Hz with c_F = 0,8 estimate KB*_Fmax = 2,1."""
    kb = im.kb_from_peak_velocity(4.0, 14.0)
    assert kb == pytest.approx(
        4.0 / math.sqrt(2.0) / math.sqrt(1.0 + (5.6 / 14.0) ** 2)
    )
    estimate = im.kb_fmax_from_peak_velocity(4.0, 14.0, kind="single_event_resonant")
    assert round(estimate, 1) == 2.1


def test_table_3_as_printed() -> None:
    assert im.PEAK_TO_KB_FACTORS == {
        "harmonic": 0.9,
        "harmonic_distorted": 0.8,
        "stochastic_resonant": 0.8,
        "stochastic": 0.7,
        "single_event_resonant": 0.8,
        "single_event": 0.6,
    }
    with pytest.raises(ValueError, match="kind"):
        im.kb_fmax_from_peak_velocity(4.0, 14.0, kind="loud")


# -- Annex A (Example 8) and Figure D.1 -------------------------------------------------


def test_example_8_the_two_classes_of_train() -> None:
    """C.8: KB_FTm of each class by (A.1), its square, and the spread of (A.2)."""
    class_1 = [0.92, 0.6, 0.9]
    class_2 = [0.2, 0.24]
    assert round(im.railway_takt_maximum_rms(class_1), 2) == 0.82
    assert round(im.railway_takt_maximum_rms(class_1) ** 2, 3) == 0.672
    assert round(im.railway_takt_maximum_rms(class_2), 2) == 0.22
    # The standard prints 0,048 4, which is 0,22 squared; the mean square of
    # the two maxima is 0,048 8, and the difference does not reach KB_FTr.
    assert round(im.railway_takt_maximum_rms(class_2) ** 2, 4) == 0.0488
    assert round(im.railway_takt_spread(class_1), 2) == 0.27
    assert round(im.railway_takt_spread(class_2), 3) == 0.012


def test_example_8_formula_a3_and_its_interval() -> None:
    """C.8: 288 and 192 occupied intervals of 1920 give 0,325, +0,059/-0,073."""
    result = im.railway_assessment_severity(
        [0.82, 0.22], [288, 192], spread=[0.27, 0.012]
    )
    assert round(result.kb_ftr, 3) == 0.325
    assert result.upper is not None
    assert result.lower is not None
    assert round(result.upper - result.kb_ftr, 3) == 0.059
    assert result.kb_ftr - result.lower == pytest.approx(0.073, abs=0.0015)
    assert not im.assess_people_in_buildings(
        0.92, im.guide_values("residential"), kb_ftr=result.kb_ftr, source="railway"
    ).complies


def test_example_8_formula_3_over_the_whole_record_agrees() -> None:
    """C.8: the 20 clock intervals of the 10 min record give the same 0,325,
    and the passage maxima alone 0,318.
    """
    maxima = np.zeros(20)
    maxima[:5] = [0.92, 0.6, 0.2, 0.9, 0.24]
    assert round(im.takt_maximum_rms(maxima), 3) == 0.325
    only_peaks = np.zeros(20)
    only_peaks[:3] = [0.92, 0.6, 0.9]
    assert round(im.takt_maximum_rms(only_peaks), 3) == 0.318
    single = im.railway_assessment_severity(0.325, 1920)
    assert single.kb_ftr == pytest.approx(0.325)


def test_figure_d1_trains_per_hour() -> None:
    """Annex D reads 7 trains at A_r = 0,05 and 14 at 0,07, for KB_FTm = 0,2."""
    assert math.floor(im.admissible_trains_per_hour(0.2, 0.05)) == 7
    assert math.floor(im.admissible_trains_per_hour(0.2, 0.07)) == 14
    seven = im.railway_assessment_severity(0.2, 7 * 16)
    assert seven.kb_ftr <= 0.05
    eight = im.railway_assessment_severity(0.2, 8 * 16)
    assert eight.kb_ftr > 0.05


def test_a_railway_refuses_more_intervals_than_the_period_holds() -> None:
    with pytest.raises(ValueError, match="more than the 960"):
        im.railway_assessment_severity([0.3], [1000], time_of_day="night")
    with pytest.raises(ValueError, match="one entry per class"):
        im.railway_assessment_severity([0.3, 0.2], [10])
    with pytest.raises(ValueError, match="occupied_takte"):
        im.railway_assessment_severity([0.3], [np.inf])
    with pytest.raises(ValueError, match="at least two"):
        im.railway_takt_spread([0.3])


def test_the_spread_is_about_the_mean_square_the_rms_returns() -> None:
    """Formula (3)'s rule that a maximum at or below 0,1 counts as zero holds
    in (A.2) as in (A.1), so the spread of [0,1, 0,3] is about 0,045, the
    mean square (A.1) gives, and not about 0,05.
    """
    maxima = [0.1, 0.3]
    mean_square = im.railway_takt_maximum_rms(maxima) ** 2
    assert mean_square == pytest.approx(0.045)
    assert im.railway_takt_spread(maxima) == pytest.approx(
        math.sqrt(((0.0 - 0.045) ** 2 + (0.09 - 0.045) ** 2) / 1)
    )


# -- Construction sites: Table 2 and Figure 3 --------------------------------------------


def test_table_2_as_printed() -> None:
    """Printed page 9, the three columns of each stage."""
    for stage, cells in {
        "I": ((0.8, 0.4), (0.4, 0.3), (0.3, 0.2)),
        "II": ((1.2, 0.8), (0.8, 0.6), (0.6, 0.4)),
        "III": ((1.6, 1.2), (1.2, 1.0), (0.8, 0.6)),
    }.items():
        for days, (a_u, a_r) in zip((1, 26, 78), cells, strict=True):
            guide = im.construction_guide_values(days, stage=stage)
            values = (guide.a_u, guide.a_o, guide.a_r)
            assert values == (a_u, 5.0, a_r), (stage, days)
    assert im.construction_guide_values(7, stage="I").a_u == 0.4
    assert im.construction_guide_values(27, stage="I").a_u == 0.3


def test_figure_3_interpolates_two_to_six_days() -> None:
    """Printed page 9: 0,73, 0,67, 0,6, 0,53 and 0,47 for stage I."""
    steps = [im.construction_guide_values(days, stage="I").a_u for days in range(2, 7)]
    # As the figure prints them, not 0,7333 and 0,4667: a reading of 0,47 on
    # the sixth day is at the value, not a third of a hundredth above it.
    assert steps == [0.73, 0.67, 0.6, 0.53, 0.47]
    assert im.construction_guide_values(4, stage="I").a_r == 0.35
    sixth = im.construction_guide_values(6, stage="I")
    assert im.assess_people_in_buildings(0.47, sixth).complies


def test_a_commercial_site_has_a_o_of_six_and_the_table_ends_at_78_days() -> None:
    assert im.construction_guide_values(10, area="commercial").a_o == 6.0
    assert im.construction_guide_values(10, area="industrial").a_o == 6.0
    with pytest.raises(ValueError, match="1 to 78"):
        im.construction_guide_values(79)
    with pytest.raises(ValueError, match="stage"):
        im.construction_guide_values(3, stage="IV")


def test_table_2_is_not_applicable_to_a_sensitive_area_or_to_part_days() -> None:
    """6.5.4.2: hospitals and the like need their own investigation, and D
    counts whole working days.
    """
    with pytest.raises(ValueError, match="not applicable"):
        im.construction_guide_values(10, area="sensitive")
    with pytest.raises(ValueError, match="whole number"):
        im.construction_guide_values(6.9)
    a_flag = True
    with pytest.raises(ValueError, match="whole number"):
        im.construction_guide_values(a_flag)


def test_the_module_lists_what_it_publishes() -> None:
    from phonometry.vibration.immission import people

    for name in people.__all__:
        assert getattr(im, name) is getattr(people, name)
