#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the measured insulation of an enclosure (ISO 11546-1 and -2).

Neither part prints a worked example, so the oracles are the ones the two
documents do offer: the algebraic identities of the subtraction that is
Equations (1) to (5); the closed form behind Figure C.1 of part 2, which is
``S_V/S = 4/((10^(K2/10) - 1) alpha)`` and is cross-checked here against
:func:`phonometry.emission.environmental_correction`; the identity that makes
the A-weighted estimate of Annex C agree with the A-weighted totals of its own
inputs; and the printed thresholds, tables and band ranges.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import emission, noise_control
from phonometry.noise_control.enclosure_insulation import (
    ARTIFICIAL_SOURCE_PLATE_MM,
    MANDATORY_BAND_RANGE_HZ,
    PREFERRED_BAND_RANGE_HZ,
    ROOM_ABSORPTION_ESTIMATES,
    TEST_ENVIRONMENT_REQUIREMENTS,
    UNRESTRICTED_ENCLOSURE_VOLUME_M3,
    EnclosureInsulationWarning,
)

THIRD_OCTAVES = np.array(
    [
        100.0,
        125.0,
        160.0,
        200.0,
        250.0,
        315.0,
        400.0,
        500.0,
        630.0,
        800.0,
        1000.0,
        1250.0,
        1600.0,
        2000.0,
        2500.0,
        3150.0,
        4000.0,
        5000.0,
    ]
)
RATING_BANDS = THIRD_OCTAVES[:16]


def _levels(offset: float = 0.0) -> np.ndarray:
    return np.linspace(95.0, 80.0, THIRD_OCTAVES.size) + offset


def test_equation_one_is_the_difference() -> None:
    without = _levels()
    with_ = without - np.linspace(10.0, 30.0, without.size)
    res = noise_control.sound_power_insulation(
        without, with_, frequencies=THIRD_OCTAVES
    )
    assert np.allclose(res.insulation, without - with_)
    assert res.quantity == "sound_power"
    assert res.condition == "laboratory"
    assert res.source_kind == "actual"


def test_a_common_offset_leaves_the_insulation_alone() -> None:
    without = _levels()
    with_ = without - 12.0
    plain = noise_control.sound_power_insulation(
        without, with_, frequencies=THIRD_OCTAVES
    )
    raised = noise_control.sound_power_insulation(
        without + 7.5, with_ + 7.5, frequencies=THIRD_OCTAVES
    )
    assert np.allclose(plain.insulation, raised.insulation)
    assert plain.a_weighted_insulation == pytest.approx(raised.a_weighted_insulation)


def test_swapping_the_two_runs_changes_the_sign() -> None:
    without = _levels()
    with_ = without - 9.0
    forward = noise_control.sound_power_insulation(
        without, with_, frequencies=THIRD_OCTAVES
    )
    backward = noise_control.sound_power_insulation(
        with_, without, frequencies=THIRD_OCTAVES
    )
    assert np.allclose(forward.insulation, -backward.insulation)


def test_a_weighted_pair_is_used_as_given() -> None:
    res = noise_control.sound_power_insulation(
        _levels(),
        _levels() - 15.0,
        frequencies=THIRD_OCTAVES,
        a_weighted_without=101.3,
        a_weighted_with=84.9,
    )
    assert res.a_weighted_insulation == pytest.approx(101.3 - 84.9)


def test_without_frequencies_there_is_no_a_weighted_number() -> None:
    res = noise_control.sound_power_insulation(_levels(), _levels() - 15.0)
    assert res.a_weighted_insulation is None
    assert res.frequencies is None


def test_rounding_is_the_report_rule() -> None:
    with pytest.warns(EnclosureInsulationWarning):
        res = noise_control.sound_power_insulation(
            [90.0, 90.0], [79.4, 79.6], frequencies=[500.0, 1000.0]
        )
    assert res.rounded().tolist() == [11, 10]


def test_mismatched_spectra_are_refused() -> None:
    with pytest.raises(ValueError, match="level_with"):
        noise_control.sound_power_insulation([90.0, 90.0], [80.0])


def test_frequencies_must_match_the_spectra() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        noise_control.sound_power_insulation(
            [90.0, 90.0], [80.0, 80.0], frequencies=[500.0]
        )


def test_a_short_band_range_is_reported() -> None:
    low, high = MANDATORY_BAND_RANGE_HZ[3]
    assert (low, high) == (100.0, 5000.0)
    with pytest.warns(EnclosureInsulationWarning, match="100 Hz to 5000 Hz"):
        noise_control.sound_power_insulation(
            [90.0, 90.0], [80.0, 80.0], frequencies=[500.0, 1000.0]
        )


def test_the_preferred_range_is_wider_than_the_required_one() -> None:
    for fraction in (1, 3):
        preferred = PREFERRED_BAND_RANGE_HZ[fraction]
        required = MANDATORY_BAND_RANGE_HZ[fraction]
        assert preferred[0] < required[0]
        assert preferred[1] > required[1]


def test_a_survey_standard_cannot_declare_a_band_spectrum() -> None:
    without = _levels()
    with_box = without - 12.0
    with pytest.warns(EnclosureInsulationWarning, match="A-weighted value only"):
        noise_control.sound_power_insulation(
            without,
            with_box,
            frequencies=THIRD_OCTAVES,
            base_standard="ISO 3746",
        )


def test_the_only_value_of_a_survey_standard_is_the_a_weighted_one() -> None:
    """Table 1 gives ISO 3746 the quantity D_WA and no band value at all."""
    res = noise_control.sound_power_insulation(
        [94.0], [79.5], base_standard="ISO 3746", condition="in-situ"
    )
    assert res.a_weighted_insulation == pytest.approx(14.5)
    assert res.frequencies is None


def test_the_same_holds_for_the_survey_pressure_standard() -> None:
    res = noise_control.sound_pressure_insulation(
        [88.0], [76.0], base_standard="ISO 11202", condition="in-situ"
    )
    assert res.a_weighted_insulation == pytest.approx(12.0)


def test_a_measured_a_weighted_pair_still_wins_over_the_single_value() -> None:
    res = noise_control.sound_power_insulation(
        [94.0],
        [79.5],
        a_weighted_without=93.2,
        a_weighted_with=79.0,
        base_standard="ISO 3746",
        condition="in-situ",
    )
    assert res.a_weighted_insulation == pytest.approx(14.2)


def test_a_combination_table_one_does_not_print_is_refused() -> None:
    """7.2 is printed in part 1 alone, so there is no in-situ reciprocity."""
    without = _levels()
    with_box = without - 12.0
    with pytest.raises(ValueError, match="reciprocity method"):
        noise_control.sound_power_insulation(
            without,
            with_box,
            frequencies=THIRD_OCTAVES,
            condition="in-situ",
            source_kind="reciprocity",
        )


def test_sound_pressure_insulation_names_its_quantity() -> None:
    res = noise_control.sound_pressure_insulation(
        _levels(),
        _levels() - 11.0,
        frequencies=THIRD_OCTAVES,
        base_standard="ISO 11201",
        condition="in-situ",
    )
    assert res.quantity == "sound_pressure"
    assert res.condition == "in-situ"


def test_reciprocity_is_a_laboratory_quantity() -> None:
    res = noise_control.reciprocity_insulation(
        _levels(), _levels() - 20.0, frequencies=THIRD_OCTAVES
    )
    assert res.quantity == "reciprocity"
    assert res.condition == "laboratory"
    assert res.source_kind == "reciprocity"


def test_the_artificial_source_averages_positions_arithmetically() -> None:
    without = np.vstack([_levels(), _levels(4.0), _levels(-4.0)])
    with_ = without - 18.0
    res = noise_control.artificial_source_insulation(
        without, with_, frequencies=THIRD_OCTAVES
    )
    assert np.allclose(res.level_without, np.mean(without, axis=0))
    assert np.allclose(res.insulation, 18.0)
    assert res.source_kind == "artificial"
    assert res.quantity == "sound_power"


def test_the_artificial_source_may_report_either_quantity() -> None:
    without = np.vstack([_levels(), _levels(4.0)])
    res = noise_control.artificial_source_insulation(
        without,
        without - 15.0,
        frequencies=THIRD_OCTAVES,
        quantity="sound_pressure",
    )
    assert res.quantity == "sound_pressure"
    with pytest.raises(ValueError, match="quantity"):
        noise_control.artificial_source_insulation(
            without, without - 15.0, frequencies=THIRD_OCTAVES, quantity="D_W"
        )


def test_one_source_position_is_not_enough() -> None:
    without = [_levels()]
    with_box = [_levels() - 10.0]
    with pytest.raises(ValueError, match="positions"):
        noise_control.artificial_source_insulation(
            without, with_box, frequencies=THIRD_OCTAVES
        )


def test_the_two_position_matrices_must_match() -> None:
    without = np.vstack([_levels(), _levels(2.0)])
    with_box = np.vstack([_levels(), _levels(2.0), _levels(4.0)])
    with pytest.raises(ValueError, match="one row per source position"):
        noise_control.artificial_source_insulation(
            without, with_box, frequencies=THIRD_OCTAVES
        )


def test_the_rating_reads_the_rating_bands() -> None:
    insulation = np.linspace(12.0, 40.0, RATING_BANDS.size)
    rating = noise_control.weighted_insulation(insulation)
    assert rating.band_centres_hz.tolist() == RATING_BANDS.tolist()
    assert rating.quantity == "sound_power"
    assert isinstance(rating.rating, int)


def test_a_spectrum_that_is_not_the_rating_bands_is_refused() -> None:
    with pytest.raises(ValueError, match="16 bands"):
        noise_control.weighted_insulation(np.zeros(18))


def test_the_octave_rating_reads_five_bands() -> None:
    rating = noise_control.weighted_insulation(
        [15.0, 20.0, 25.0, 30.0, 35.0], band_fraction=1
    )
    assert rating.band_centres_hz.tolist() == [125.0, 250.0, 500.0, 1000.0, 2000.0]


def test_a_flat_insulation_estimates_itself() -> None:
    spectrum = _levels()
    for value in (0.0, 7.5, 23.0):
        estimate = noise_control.estimated_a_weighted_insulation(
            spectrum, np.full(spectrum.size, value), frequencies=THIRD_OCTAVES
        )
        assert estimate == pytest.approx(value)


def test_the_estimate_is_the_difference_of_two_a_weighted_totals() -> None:
    spectrum = _levels()
    insulation = np.linspace(5.0, 35.0, spectrum.size)
    estimate = noise_control.estimated_a_weighted_insulation(
        spectrum, insulation, frequencies=THIRD_OCTAVES
    )
    res = noise_control.sound_power_insulation(
        spectrum, spectrum - insulation, frequencies=THIRD_OCTAVES
    )
    assert estimate == pytest.approx(res.a_weighted_insulation)


def test_the_estimate_needs_matching_inputs() -> None:
    with pytest.raises(ValueError, match="band for band"):
        noise_control.estimated_a_weighted_insulation(
            [90.0, 90.0], [10.0], frequencies=[500.0, 1000.0]
        )


def test_the_source_stands_a_fifth_of_the_shortest_dimension_from_a_wall() -> None:
    assert noise_control.source_position_clearance_m(1.5) == pytest.approx(0.3)


def test_the_two_ratios_are_reciprocal() -> None:
    theta = noise_control.leak_ratio(0.02, 6.0)
    assert theta == pytest.approx(0.02 / 6.0)
    assert noise_control.seal_ratio(theta) == pytest.approx(300.0)


def test_the_fill_ratio_is_the_volume_fraction() -> None:
    assert noise_control.fill_ratio(0.4, 1.6) == pytest.approx(0.25)


def test_a_non_positive_area_is_refused() -> None:
    with pytest.raises(ValueError, match="opening_area_m2"):
        noise_control.leak_ratio(0.0, 6.0)


def test_figure_c1_is_the_environmental_correction_solved_for_the_room() -> None:
    # At the ratio the closed form returns, K_2 is exactly the Table C.1 limit.
    for alpha in ROOM_ABSORPTION_ESTIMATES:
        surface = 14.1
        limit = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3744"][0]
        assert limit is not None
        required = 4.0 / ((10.0 ** (limit / 10.0) - 1.0) * alpha)
        k2 = emission.environmental_correction(
            surface,
            mean_absorption_coefficient=alpha,
            room_surface=required * surface,
        )
        assert float(k2) == pytest.approx(limit)


def test_a_room_at_the_required_ratio_is_applicable() -> None:
    surface = 14.1
    verdict = noise_control.test_environment_applicability(
        base_standard="ISO 3744",
        mean_absorption_coefficient=0.15,
        room_surface_area_m2=surface * 60.0,
        measurement_surface_area_m2=surface,
    )
    assert verdict.required_area_ratio is not None
    assert verdict.actual_area_ratio == pytest.approx(60.0)
    assert verdict.applicable is (60.0 >= verdict.required_area_ratio)
    assert verdict.background_margin_limit_db == 6.0


def test_a_hard_small_room_fails_the_precision_method() -> None:
    verdict = noise_control.test_environment_applicability(
        base_standard="ISO 3744",
        mean_absorption_coefficient=0.05,
        room_surface_area_m2=100.0,
        measurement_surface_area_m2=14.1,
    )
    assert verdict.applicable is False


def test_a_comparison_method_states_no_environmental_limit() -> None:
    verdict = noise_control.test_environment_applicability(
        base_standard="ISO 3747",
        mean_absorption_coefficient=0.05,
        room_surface_area_m2=100.0,
        measurement_surface_area_m2=14.1,
    )
    assert verdict.environmental_correction_limit_db is None
    assert verdict.required_area_ratio is None
    assert verdict.applicable is True


def test_an_absorption_coefficient_above_one_is_refused() -> None:
    with pytest.raises(ValueError, match="mean_absorption_coefficient"):
        noise_control.test_environment_applicability(
            base_standard="ISO 3744",
            mean_absorption_coefficient=1.5,
            room_surface_area_m2=100.0,
            measurement_surface_area_m2=14.1,
        )


def test_an_unknown_base_standard_is_refused() -> None:
    with pytest.raises(ValueError, match="base_standard"):
        noise_control.test_environment_applicability(
            base_standard="ISO 3740",
            mean_absorption_coefficient=0.15,
            room_surface_area_m2=100.0,
            measurement_surface_area_m2=14.1,
        )


def test_table_c1_reproduces_its_printed_pairs() -> None:
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 3744"] == (2.0, 6.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 3746"] == (7.0, 3.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 11201"] == (2.0, 6.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 11202"] == (7.0, 3.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 11204"] == (7.0, 6.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 3743-1"] == (None, 6.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 3747"] == (None, 3.0)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 9614-1"] == (None, None)
    assert TEST_ENVIRONMENT_REQUIREMENTS["ISO 9614-2"] == (None, None)
    assert "ISO 10204" not in TEST_ENVIRONMENT_REQUIREMENTS


def test_table_c2_reproduces_its_seven_rows() -> None:
    assert sorted(ROOM_ABSORPTION_ESTIMATES) == [
        0.05,
        0.1,
        0.15,
        0.2,
        0.25,
        0.35,
        0.5,
    ]
    assert "empty" in ROOM_ABSORPTION_ESTIMATES[0.05].lower()


def test_table_one_gives_bands_only_where_the_method_can() -> None:
    rows = {
        entry.base_standard: entry
        for entry in noise_control.applicable_methods(condition="in-situ")
    }
    assert rows["ISO 3744"].band_values is True
    assert rows["ISO 3746"].band_values is False
    assert rows["ISO 3746"].quantities == ("D_WA",)
    assert rows["ISO 11202"].quantities == ("D_pA",)


def test_the_laboratory_table_admits_no_survey_grade_row() -> None:
    laboratory = {
        entry.base_standard
        for entry in noise_control.applicable_methods(condition="laboratory")
    }
    assert {"ISO 3746", "ISO 3747", "ISO 11202"}.isdisjoint(laboratory)
    assert {"ISO 3741", "ISO 3742", "ISO 3743-2"} <= laboratory


def test_footnote_two_of_part_one_marks_two_rows() -> None:
    marked = {
        entry.base_standard
        for entry in noise_control.applicable_methods(condition="laboratory")
        if entry.survey_grade_excluded
    }
    assert marked == {"ISO 9614-1", "ISO 11204"}
    in_situ = [
        entry
        for entry in noise_control.applicable_methods(condition="in-situ")
        if entry.survey_grade_excluded
    ]
    assert in_situ == []


def test_each_row_names_its_test_environment() -> None:
    rows = noise_control.applicable_methods(condition="laboratory")
    environments = {entry.base_standard: entry.test_environment for entry in rows}
    assert environments["ISO 3741"] == "Reverberation room"
    assert environments["ISO 3743-1"] == "Hard-walled test room"
    assert environments["ISO 9614-1"] == "No special test environment"


def test_the_reciprocity_row_exists_in_part_one_only() -> None:
    laboratory = noise_control.applicable_methods(
        condition="laboratory", source_kind="reciprocity"
    )
    assert laboratory[0].subclause == "7.2"
    with pytest.raises(ValueError, match="reciprocity method"):
        noise_control.applicable_methods(condition="in-situ", source_kind="reciprocity")


def test_the_in_situ_table_adds_the_survey_methods() -> None:
    names = {
        entry.base_standard
        for entry in noise_control.applicable_methods(condition="in-situ")
    }
    assert {"ISO 3746", "ISO 3747", "ISO 11202"} <= names
    assert {"ISO 3741", "ISO 3742", "ISO 3743-2"}.isdisjoint(names)


def test_the_printed_constants_of_annex_a_and_clause_one() -> None:
    assert UNRESTRICTED_ENCLOSURE_VOLUME_M3 == 2.0
    assert ARTIFICIAL_SOURCE_PLATE_MM == (4.0, 800.0, 300.0)


def test_the_plot_draws_three_series() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.sound_power_insulation(
        _levels(), _levels() - 14.0, frequencies=THIRD_OCTAVES
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    twin = [other for other in drawn.figure.axes if other is not drawn]
    assert len(drawn.lines) == 2
    assert len(twin) == 1
    assert len(twin[0].lines) == 1
    assert drawn.get_title()
    plt.close(fig)


def test_the_spanish_plot_translates_its_labels() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.sound_power_insulation(
        _levels(), _levels() - 14.0, frequencies=THIRD_OCTAVES
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "Aislamiento" in drawn.get_title()
    assert "Frecuencia" in drawn.get_xlabel()
    plt.close(fig)


def test_the_insulation_of_a_two_metre_enclosure_is_a_plain_subtraction() -> None:
    # A worked reading of clause 6.2: the machine at 97 dB in the 1 kHz band,
    # 74 dB once the enclosure is on, is 23 dB of insulation and nothing else.
    with pytest.warns(EnclosureInsulationWarning):
        res = noise_control.sound_power_insulation(
            [97.0], [74.0], frequencies=[1000.0], band_fraction=3
        )
    assert res.insulation[0] == pytest.approx(23.0)
    assert math.isclose(
        res.a_weighted_insulation or 0.0, 23.0, rel_tol=0.0, abs_tol=1e-9
    )


def test_half_an_a_weighted_pair_is_refused() -> None:
    without = _levels()
    with_box = without - 12.0
    with pytest.raises(ValueError, match="both"):
        noise_control.sound_power_insulation(
            without, with_box, frequencies=THIRD_OCTAVES, a_weighted_without=99.0
        )


def test_an_infinite_a_weighted_level_is_refused() -> None:
    without = _levels()
    with_box = without - 12.0
    with pytest.raises(ValueError, match="a_weighted_with"):
        noise_control.sound_power_insulation(
            without,
            with_box,
            frequencies=THIRD_OCTAVES,
            a_weighted_without=99.0,
            a_weighted_with=float("nan"),
        )
