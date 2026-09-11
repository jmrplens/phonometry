#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the railway prediction of E DIN 45672-3:2023-02.

Anchored on the worked example of Annex C, whose Table C.1 prints every term
of Formula (1) band by band and whose results chain from the sum level to a
peak velocity, on the six tables of Annex A read off their pages, on Table 2
against the KB weighting of DIN 45669-1 it is a rounding of, and on the
closed forms of Clauses 5.2, 5.3 and Annex B, which print no example.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

# Table C.1 (printed page 34): f_Tn, L_v,E, ΔL_v,BB, ΔL_v,DF and the printed L_v.
TABLE_C1 = [
    (4.0, 26.0, 0.9, 1.9, 28.9),
    (5.0, 27.0, 0.9, 2.3, 30.2),
    (6.3, 37.0, 0.9, 3.1, 41.0),
    (8.0, 54.0, 1.1, 3.5, 58.6),
    (10.0, 56.0, 1.1, 5.0, 62.1),
    (12.5, 57.0, 1.2, 6.9, 65.1),
    (16.0, 56.0, 1.3, 11.5, 68.8),
    (20.0, 57.0, 1.3, 17.3, 75.6),
    (25.0, 58.0, 1.4, 10.0, 69.4),
    (31.5, 58.0, 1.6, 5.4, 65.0),
    (40.0, 52.0, 1.7, 1.9, 55.7),
    (50.0, 52.0, 2.0, 1.5, 55.5),
    (63.0, 60.0, 2.2, -0.8, 61.4),
    (80.0, 58.0, 2.6, -2.3, 58.3),
    (100.0, 49.0, 3.0, -3.8, 48.1),
    (125.0, 45.0, 3.5, -5.4, 43.1),
    (160.0, 45.0, 3.1, -6.5, 41.6),
    (200.0, 33.0, 2.8, -8.1, 27.7),
    (250.0, 28.0, 2.4, -9.6, 20.8),
]
FREQS = np.array([row[0] for row in TABLE_C1])
EMISSION = np.array([row[1] for row in TABLE_C1])
GROUND = np.array([row[2] for row in TABLE_C1])
FLOOR = np.array([row[3] for row in TABLE_C1])
PRINTED = np.array([row[4] for row in TABLE_C1])


def test_annex_c_formula_1_band_by_band() -> None:
    """Every printed L_v is the sum of its printed terms, three of them a
    tenth off from rounding the terms after summing.
    """
    levels = im.predict_floor_spectrum(EMISSION, ground_db=GROUND, floor_db=FLOOR)
    assert np.all(np.abs(levels - PRINTED) <= 0.1 + 1e-9)
    assert np.count_nonzero(np.abs(levels - PRINTED) > 0.01) == 3
    assert list(FREQS) == list(im.PREDICTION_BAND_CENTRES_HZ)


def test_annex_c_the_chain_from_the_sum_level() -> None:
    """C.3: 78,1 dB over the 19 bands gives 0,4, 0,6 and 1,81 mm/s by
    Formulae (9), (10) and (12), the last only from the unrounded chain.
    """
    total = im.band_sum_level(PRINTED)
    assert round(total, 1) == 78.1
    assert im.takt_maximum_kb(PRINTED) == pytest.approx(0.4008, abs=0.0001)
    # The print carries the rounded 78,1 dB on: one band at that level.
    kb_ftm = im.takt_maximum_kb([78.1])
    assert kb_ftm == pytest.approx(0.4018, abs=0.0001)
    kb_fmax = im.TRAIN_KB_FMAX_FACTOR * kb_ftm
    assert round(kb_fmax, 1) == 0.6
    assert im.peak_velocity_from_kb_mm_s(kb_fmax) == pytest.approx(1.808, abs=0.001)
    assert round(im.peak_velocity_from_kb_mm_s(kb_fmax), 2) == 1.81


def test_annex_c_run_as_clause_7_prints_it() -> None:
    """The example feeds Formula (9) the unweighted sum of all 19 bands; the
    chain of Clause 7.1 weights the 14 bands from 4 Hz to 80 Hz first and
    gets 77,7 dB, 0,39 and 1,73 mm/s. Both are held: the printed chain above,
    the standard's own here.
    """
    prediction = im.predict_train_category(EMISSION, ground_db=GROUND, floor_db=FLOOR)
    assert np.allclose(prediction.floor_db, EMISSION + GROUND + FLOOR)
    assert len(prediction.weighted_db) == 14
    assert list(prediction.weighted_frequencies_hz) == list(FREQS[:14])
    assert prediction.sum_level_db == pytest.approx(77.73, abs=0.02)
    assert prediction.kb_ftm == pytest.approx(0.385, abs=0.002)
    assert round(prediction.kb_fmax, 1) == 0.6
    assert prediction.peak_velocity_mm_s == pytest.approx(1.73, abs=0.01)


def test_annex_c_formula_11_with_the_printed_inputs() -> None:
    """C.3: 200 trams by day and 20 by night at alpha 0,7 and KB_FTm 0,4 give
    0,090 and 0,040; the print says 0,11 and 0,05, which the printed inputs
    give only with alpha under the root once instead of squared, and the
    daytime verdict turns on it. See the errata.
    """
    day = im.train_assessment_severity([0.4], [200], alpha=0.7)
    night = im.train_assessment_severity([0.4], [20], alpha=0.7, time_of_day="night")
    assert day == pytest.approx(0.7 * 0.4 * math.sqrt(200 / 1920))
    assert night == pytest.approx(0.7 * 0.4 * math.sqrt(20 / 960))
    assert round(0.4 * math.sqrt(0.7 * 200 / 1920), 2) == 0.11
    assert round(0.4 * math.sqrt(0.7 * 20 / 960), 2) == 0.05
    assert round(day, 3) == 0.090
    assert round(night, 3) == 0.040
    guide = im.guide_values("mixed", edition="2023")
    assert guide == im.GuideValues(0.2, 5.0, 0.1, edition="2023")
    assert im.assess_people_in_buildings(
        0.6, guide, kb_ftr=day, source="railway", edition="2023"
    ).complies


def test_table_2_is_the_kb_weighting_rounded_to_a_tenth() -> None:
    """Printed page 22: the 14 corrections equal 20 lg of the DIN 45669-1
    response at the nominal centres, rounded.
    """
    freqs = np.array(list(im.KB_WEIGHTING_TABLE_DB))
    response = 10.0 * np.log10(1.0 / (1.0 + (im.KB_CORNER_HZ / freqs) ** 2))
    assert [round(float(v), 1) for v in response] == list(
        im.KB_WEIGHTING_TABLE_DB.values()
    )
    # Without the band limitation of the meter, which would take 1,5 dB off at 80 Hz.
    limited = 20.0 * np.log10(np.abs(im.kb_weighting_response(freqs)))
    assert limited[-1] < response[-1] - 1.0
    weighted = im.kb_weighted_levels_db(np.zeros(14), freqs)
    assert list(weighted) == list(im.KB_WEIGHTING_TABLE_DB.values())
    with pytest.raises(ValueError, match="nominal third-octave centre"):
        im.kb_weighted_levels_db([0.0], [100.0])
    with pytest.raises(ValueError, match="14 bands"):
        im.predict_train_category(np.zeros(10), frequencies_hz=FREQS[:10])


def test_annex_a_tables_as_printed() -> None:
    """Spot cells of the six tables, and their shapes."""
    concrete = im.ground_to_floor_transfer_db(
        "concrete", floor_natural_frequency_hz=8.0
    )
    assert list(concrete[:6]) == [-0.51, 1.42, 6.88, 15.0, 5.87, 0.17]
    assert (
        im.ground_to_floor_transfer_db("concrete", floor_natural_frequency_hz=20.0)[7]
        == 13.12
    )
    assert (
        im.ground_to_floor_transfer_db("concrete", floor_natural_frequency_hz=63.0)[12]
        == 9.5
    )
    timber = im.ground_to_floor_transfer_db("timber", floor_natural_frequency_hz=8.0)
    assert list(timber[:4]) == [5.14, 7.55, 12.59, 20.0]
    assert (
        im.ground_to_floor_transfer_db("timber", floor_natural_frequency_hz=80.0)[-1]
        == -1.35
    )
    for floor in im.GROUND_TO_FLOOR_DB.values():
        assert all(len(column) == 19 for column in floor.values())
    # The columns 8 to 16 Hz of the concrete table are one template shifted band by band.
    columns = im.GROUND_TO_FLOOR_DB["concrete"]
    assert columns[10.0][1:] == columns[8.0][:-1]
    assert columns[16.0][3:] == columns[8.0][:-3]
    basement = im.ground_to_foundation_transfer_db("basement")
    assert basement[9] == -9.3
    assert (
        im.ground_to_foundation_transfer_db("basement", statistic="lower")[9] == -15.6
    )
    assert im.ground_to_foundation_transfer_db("basement", statistic="upper")[9] == -2.7
    assert im.ground_to_foundation_transfer_db("ground_floor")[5] == -1.9
    with pytest.raises(ValueError, match="nominal third-octave centre"):
        im.ground_to_floor_transfer_db("concrete", floor_natural_frequency_hz=15.0)


def test_foundation_to_floor_at_the_tabulated_ratios_and_between() -> None:
    """A.5 and A.6 read at f/f_e: the peak of 17,26 dB for concrete and 21,93
    for timber at the natural frequency, the mean of 1,60 at a ratio of 0,2,
    and nan where the table prints none.
    """
    at_20 = im.foundation_to_floor_transfer_db(
        [4.0, 20.0, 100.0, 160.0], floor="concrete", floor_natural_frequency_hz=20.0
    )
    assert at_20[0] == pytest.approx(1.60)
    assert at_20[1] == pytest.approx(17.26)
    assert at_20[2] == pytest.approx(2.83)
    assert math.isnan(at_20[3])
    timber = im.foundation_to_floor_transfer_db(
        [20.0, 126.0, 160.0, 1.6, 2.0],
        floor="timber",
        floor_natural_frequency_hz=20.0,
    )
    assert timber[0] == pytest.approx(21.93)
    assert timber[1] == pytest.approx(3.35)
    assert timber[2] == pytest.approx(1.85)
    assert math.isnan(timber[3])  # ratio 0,08: the timber mean starts at 0,125
    assert math.isnan(timber[4])
    upper = im.foundation_to_floor_transfer_db(
        [4.0, 5.0], floor="timber", floor_natural_frequency_hz=20.0, statistic="upper"
    )
    assert math.isnan(upper[0])  # ratio 0,2, printed as a dash
    assert upper[1] == pytest.approx(8.1)
    # Between two tabulated ratios: linear in decibels over the logarithm.
    between = im.foundation_to_floor_transfer_db(
        [math.sqrt(0.8 * 1.0) * 20.0], floor="concrete", floor_natural_frequency_hz=20.0
    )
    assert between[0] == pytest.approx((9.94 + 17.26) / 2)


def test_formula_3_rescales_a_spectrum_and_stops_at_30_percent() -> None:
    shifted = im.rescale_emission_for_speed(
        [50.0, 60.0], speed_from_km_h=50.0, speed_to_km_h=65.0
    )
    assert shifted[0] == pytest.approx(50.0 + 20.0 * math.log10(1.3))
    assert shifted[1] - 60.0 == pytest.approx(2.28, abs=0.005)
    with pytest.raises(ValueError, match="30%"):
        im.rescale_emission_for_speed([50.0], speed_from_km_h=50.0, speed_to_km_h=100.0)


def test_formulae_4_to_6_the_transmission_through_the_ground() -> None:
    freqs = np.array([8.0, 16.0, 63.0])
    none = im.ground_transmission_db(
        freqs, distance_m=10.0, reference_distance_m=10.0, exponent=0.3
    )
    assert np.allclose(none, 0.0)
    doubled = im.ground_transmission_db(
        freqs, distance_m=20.0, reference_distance_m=10.0, exponent=0.3
    )
    assert np.allclose(doubled, -20.0 * 0.3 * math.log10(2.0))
    assert doubled[0] == pytest.approx(-1.806, abs=0.001)
    alpha = im.ground_attenuation_coefficient_per_m(
        freqs, damping_ratio=0.03, shear_wave_speed_m_s=200.0
    )
    assert alpha[0] == pytest.approx(2 * math.pi * 8.0 * 0.03 / 200.0)
    damped = im.ground_transmission_db(
        freqs,
        distance_m=20.0,
        reference_distance_m=10.0,
        exponent=0.3,
        damping_ratio=0.03,
        shear_wave_speed_m_s=200.0,
    )
    assert np.all(damped < doubled)
    assert damped[0] - doubled[0] == pytest.approx(
        -20.0 * math.log10(math.e) * alpha[0] * 10.0
    )
    per_band = im.ground_transmission_db(
        freqs, distance_m=20.0, reference_distance_m=10.0, exponent=[0.2, 0.3, 0.4]
    )
    assert per_band[2] == pytest.approx(-20.0 * 0.4 * math.log10(2.0))
    with pytest.raises(ValueError, match="shear wave speed"):
        im.ground_transmission_db(
            freqs,
            distance_m=20.0,
            reference_distance_m=10.0,
            exponent=0.3,
            damping_ratio=0.03,
        )


def test_formula_13_and_the_line_source_of_annex_b() -> None:
    assert im.velocity_spectrum_um_s([0.0])[0] == pytest.approx(0.05)
    assert im.velocity_spectrum_um_s([78.1])[0] == pytest.approx(401.8, abs=0.1)
    assert im.point_to_line_transition_distance_m(30.0, wavelength_m=10.0) == 90.0
    assert im.line_source_correction_db(
        100.0, reference_distance_m=10.0, exponent_correction=0.3
    ) == pytest.approx(6.0)
    assert im.train_decay_exponent(1.0) == 0.7
    assert im.train_decay_exponent(1.0, fitted_with="power_law") == 0.5
    # Annex B prints no floor: a point exponent below the correction goes negative.
    assert im.train_decay_exponent(0.2) == pytest.approx(-0.1)
    ratio = im.train_velocity_ratio(
        [10.0, 90.0, 900.0],
        reference_distance_m=10.0,
        transition_distance_m=90.0,
        point_exponent=1.0,
        exponent_correction=0.3,
    )
    assert ratio[0] == 1.0
    assert ratio[1] == pytest.approx(9.0**-0.7)
    assert ratio[2] == pytest.approx(9.0**-0.7 * 10.0**-1.0)
    with pytest.raises(ValueError, match="0.3 to 0.5"):
        im.line_source_correction_db(
            100.0, reference_distance_m=10.0, exponent_correction=0.6
        )


def test_table_1_distances_and_the_plot() -> None:
    assert im.RECOMMENDED_DISTANCES_M["urban"] == {"tunnel": 20.0, "surface": 25.0}
    assert im.RECOMMENDED_DISTANCES_M["freight_soft_soil"]["tunnel"] is None
    assert im.RECOMMENDED_DISTANCES_M["mainline"]["surface"] == 60.0
    prediction = im.predict_train_category(EMISSION, ground_db=GROUND, floor_db=FLOOR)
    pytest.importorskip("matplotlib")
    ax = prediction.plot()
    assert len(ax.get_lines()) == 3
    ax_es = prediction.plot(language="es")
    assert "forjado" in ax_es.get_legend().get_texts()[1].get_text()


def test_the_module_lists_what_it_publishes() -> None:
    from phonometry.vibration.immission import railway_prediction

    for name in railway_prediction.__all__:
        assert getattr(im, name) is getattr(railway_prediction, name)
