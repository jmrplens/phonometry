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
    eighteen_bands = np.zeros(18)
    with pytest.raises(ValueError, match="16 bands"):
        noise_control.weighted_insulation(eighteen_bands)


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


#: ISO 11546-2:1995, Annex C, Table C.2, printed folio 13 (PDF page 17), read
#: on the printed page and checked again against the identical table of
#: BS EN ISO 11546-2:2009, printed folio 13 (PDF page 19). Both columns, because
#: the description is what this table says and the coefficient is only its key.
_PRINTED_TABLE_C2: dict[float, str] = {
    0.05: (
        "Nearly empty room with smooth hard walls made of concrete, brick, "
        "plaster or tile"
    ),
    0.1: "Partly empty room; room with smooth walls",
    0.15: "Room with furniture; rectangular machinery room; rectangular industrial room",
    0.2: (
        "Irregularly shaped room with furniture; irregularly shaped machinery "
        "room or industrial room"
    ),
    0.25: (
        "Room with upholstered furniture; machinery or industrial room with a "
        "small amount of sound-absorbing material on ceiling or walls "
        "(e.g. partially absorptive ceiling)"
    ),
    0.35: "Room with sound-absorbing materials on both ceiling and walls",
    0.5: "Room with large amounts of sound-absorbing materials on ceiling and walls",
}


def test_table_c2_reproduces_its_seven_rows() -> None:
    assert ROOM_ABSORPTION_ESTIMATES == _PRINTED_TABLE_C2


@pytest.mark.parametrize("alpha", sorted(_PRINTED_TABLE_C2))
def test_every_room_description_is_the_printed_one(alpha: float) -> None:
    assert ROOM_ABSORPTION_ESTIMATES[alpha] == _PRINTED_TABLE_C2[alpha]


def test_the_2010_editions_print_a_different_table() -> None:
    # ISO 3744:2010 Table A.1 (printed folio 36) and ISO 3746:2010 Table A.1
    # (printed folio 24) have eight rows and reword two of these seven. Table
    # C.2 is the source of this constant, so neither of their variants may
    # reach it: no 0,30 row, "rectangular" rather than "right cuboid", and the
    # worked example the 0,25 row ends on.
    assert 0.3 not in ROOM_ABSORPTION_ESTIMATES
    assert "right cuboid" not in ROOM_ABSORPTION_ESTIMATES[0.15].lower()
    assert "on part of ceiling or walls" not in ROOM_ABSORPTION_ESTIMATES[0.25]
    assert ROOM_ABSORPTION_ESTIMATES[0.25].endswith(
        "(e.g. partially absorptive ceiling)"
    )


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
            a_weighted_with=math.nan,
        )


# ---------------------------------------------------------------------------
# Oracles from outside the standard.
#
# ISO 11546-2 prints no worked example, so the numbers below come from five
# documents that measured or worked the same quantities and owe nothing to
# this library. Each block names the document, its edition, the page of the
# PDF it was read on and the folio printed on that page.
# ---------------------------------------------------------------------------

# R. C. Payne and D. J. Simmons, "Environmental correction factor K2A",
# National Physical Laboratory report CIRA(EXT) 009, April 1996, Crown
# copyright. Table 8 on PDF page 19, printed folio 15: the area of each of the
# four measurement surfaces, in square metres. Surfaces 1 and 2 share an area.
NPL_SURFACE_M2 = {1: 14.1, 2: 14.1, 3: 28.2, 4: 49.6}

# Table 9 on PDF page 20, printed folio 16: for each of the five rooms, the
# area of its boundary surfaces in square metres, its volume in cubic metres,
# the A-weighted reverberation time in seconds, and the two ends of the range
# of mean absorption coefficients the report reads off the table of room
# descriptions in Annex A of ISO 3744:1994 and ISO 3746:1995, the editions its
# references 4 and 5 name. Its Table 1 reproduces that table, seven rows that
# are Table C.2 of ISO 11546-2 under another name; the 2010 editions print a
# different one with eight.
NPL_ROOMS = {
    # S_V, V, T (A-weighted), alpha from, alpha to
    "A": (134.0, 91.5, 0.2, 0.5, 0.5),
    "B": (168.0, 116.0, 0.5, 0.1, 0.25),
    "C": (373.0, 428.0, 1.3, 0.1, 0.25),
    "D": (834.0, 1188.0, 1.0, 0.2, 0.5),
    "E": (358.0, 274.0, 2.3, 0.05, 0.05),
}

# Table 8 again: the A-weighted sound power level of the reference sound
# source as ISO 3744 measured it in each room and on each surface, in decibels
# re 1 pW. The source was calibrated to 90,9 dB under ISO 6926.
NPL_SOUND_POWER_DB = {
    "A": {1: 90.9, 2: 91.5, 3: 91.9, 4: 92.0},
    "B": {1: 94.2, 2: 94.3, 3: 95.2},
    "C": {1: 94.3, 2: 94.4, 3: 96.0},
    "D": {1: 91.2, 2: 91.8, 3: 92.2, 4: 92.8},
    "E": {1: 96.1, 2: 96.4, 3: 98.6},
}
NPL_REFERENCE_SOURCE_DB = 90.9

# Tables 10 to 14 on PDF pages 22 to 24, printed folios 18 to 20, "absolute"
# row: the measured environmental correction of each room and surface, in
# decibels. A measurement, not an evaluation of a formula, and so the ground
# truth the applicability tests below are judged against.
NPL_MEASURED_K2A = {
    "A": {1: 0.0, 2: 0.6, 3: 1.0, 4: 1.1},
    "B": {1: 3.3, 2: 3.4, 3: 4.3},
    "C": {1: 3.4, 2: 3.5, 3: 5.1},
    "D": {1: 0.3, 2: 0.9, 3: 1.3, 4: 1.9},
    "E": {1: 5.2, 2: 5.5, 3: 7.7},
}

# The same tables, "reverberation (A-wt)" row: the correction the authors
# computed from their Eq. (3), K_2 = 10 lg (1 + 4 S/A), with the absorption of
# their Eq. (5), A = 0,16 V/T. That is the pair ISO 3744 prints as Eq. (A.2)
# and Eq. (A.3).
NPL_REVERBERATION_K2A = {
    "A": {1: 2.5, 2: 2.5, 3: 4.0, 4: 5.7},
    "B": {1: 4.0, 2: 4.0, 3: 6.0},
    "C": {1: 3.2, 2: 3.2, 3: 5.0},
    "D": {1: 1.1, 2: 1.1, 3: 2.0, 4: 3.1},
    "E": {1: 5.9, 2: 5.9, 3: 8.4},
}

# The same tables, "estimated room absorption" row, as the two bounds each
# cell prints. The lower bound goes with the upper end of the absorption
# range. These values are printed, and they are still not an oracle: see
# test_the_npl_estimated_absorption_column_drops_the_factor_four.
NPL_ESTIMATED_K2A = {
    "A": {1: (0.8, 0.8), 2: (0.8, 0.8), 3: (1.5, 1.5), 4: (2.4, 2.4)},
    "B": {1: (1.3, 2.6), 2: (1.3, 2.6), 3: (2.2, 4.3)},
    "C": {1: (0.6, 1.3), 2: (0.6, 1.3), 3: (1.1, 2.3)},
    "D": {1: (0.1, 0.4), 2: (0.1, 0.4), 3: (0.3, 0.7), 4: (0.1, 1.1)},
    "E": {1: (2.7, 2.7), 2: (2.7, 2.7), 3: (4.3, 4.3)},
}

# F. Heisterkamp, "Machine Noise: Experimental Study of the Local
# Environmental Correction for the Emission Sound Pressure Level", Acoustics
# 2024, 6(1), 177-203, open access. Table 3 on PDF page 10, printed folio 186:
# what three test engineers of different experience assessed for one and the
# same BAuA workroom, and the correction each assessment gives on the two
# reference measurement surfaces the same folio defines. The table's fourth
# column holds column means rather than a fourth assessment.
BAUA_ENGINEERS = {
    # alpha, S_V, A = alpha S_V, K_2A at 0,5 m, K_2A at 1 m
    "Test Eng. 1": (0.15, 174.0, 26.1, 7.1, 9.2),
    "Test Eng. 2": (0.15, 173.0, 25.9, 7.1, 9.3),
    "Test Eng. 3": (0.30, 174.3, 52.3, 4.9, 6.7),
}

# Folio 186: the reference measurement surface for a workstation 0,5 m from
# the machine, and for one at 1 m, in square metres.
BAUA_SURFACES_M2 = (26.9, 48.3)

# Table 4 on PDF page 11, printed folio 187: the absorption area each of the
# two rooms was measured to have with a reference sound source, in square
# metres, and the correction computed from it at 0,5 m, at 1 m and on the
# measurement surface the source itself stood on.
BAUA_DIRECT = {
    # A, K_2A at 0,5 m, K_2A at 1 m, K_2A on the 25,1 m2 surface
    "workroom": (55.2, 4.7, 6.5, 4.5),
    "former reverberation room": (97.7, 3.2, 4.7, 3.1),
}
BAUA_DIRECT_SURFACE_M2 = 25.1
BAUA_SOURCE_POWER_DB = 90.67

# Folio 187 again: the average A-weighted level on that surface in each room.
# The workroom cell closes on its own absorption area through the author's
# Eq. (9); the other does not, which is why only the absorption areas of that
# column are used as inputs.
BAUA_LEVEL_IN_SITU_DB = {"workroom": 81.17, "former reverberation room": 81.08}

# R. F. Barron, Industrial Noise Control and Acoustics, Marcel Dekker 2003,
# Example 7-8. Table 7-5 on PDF page 320, printed folio 308: the octave sound
# pressure levels at the operator position without the enclosure and with it,
# in decibels; and on PDF pages 321 and 323, printed folios 309 and 311, the
# A-weighted total of each.
BARRON_OCTAVES_HZ = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
BARRON_WITHOUT_DB = np.array([93.4, 98.5, 102.9, 104.6, 102.8, 95.5])
BARRON_WITH_DB = np.array([82.4, 84.9, 85.9, 85.8, 83.9, 71.2])
BARRON_TOTALS_DBA = (108.4, 89.8)

# R. J. Peters, B. J. Smith and M. Hollins, Acoustics and Noise Control, 3rd
# edition, Routledge 2011, Example 1.13 on PDF pages 31 and 32, printed folios
# 16 and 17: two machines measured at one reception point in octave bands, the
# attenuation of one enclosure, and the A-weighted attenuation the answer box
# gives for each machine. The example carries its own A-weighting, the ISO 3744
# Annex E values rounded to whole decibels.
SMITH_OCTAVES_HZ = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
SMITH_ATTENUATION_DB = np.array([4.0, 9.0, 15.0, 21.0, 24.0, 30.0, 27.0, 26.0])
SMITH_MACHINES = {
    "machine A": ([105.0, 107.0, 99.0, 94.0, 91.0, 87.0, 82.0, 79.0], 14.0),
    "machine B": ([68.0, 79.0, 82.0, 87.0, 92.0, 96.0, 89.0, 81.0], 27.0),
}

# W. Schirmer (ed.), Technischer Laermschutz, 2nd edition, Springer 2006,
# 10.8.1 on PDF pages 323 and 324, printed folios 303 and 304: an enclosure
# 6 m by 5 m by 3 m high with a 0,25 m2 exhaust opening, whose walls and roof
# come to 96 m2 with the opening counted in, and the opening fraction q the
# book prints for it to two significant figures.
SCHIRMER_OPENING_M2 = 0.25
SCHIRMER_WALLS_M2 = 95.75
SCHIRMER_LEAK_RATIO = 2.6e-3

# DGUV, "Laermschutz-Arbeitsblatt IFA-LSA 01-243: Geraeuschminderung durch
# Kapselung", October 2014, Anhang. Beispiel 1 on PDF page 22, printed folio
# 22 and Beispiel 3 on PDF pages 23 and 25, printed folios 23 and 25: the
# A-weighted level at the workstation before and after the enclosure was
# built, and the reduction the sheet prints. Its second example is left out:
# the level with the enclosure is never printed there, so the only way to feed
# it is to subtract the printed reduction from the printed level.
IFA_ENCLOSURES = {
    "punching machine": (100.0, 80.0, 20.0),
    "emery machine": (104.0, 84.0, 20.0),
}


def test_the_npl_reverberation_factors_follow_the_environmental_correction() -> None:
    # A tenth of a decibel rather than a twentieth: the study prints its
    # answers to 0,1 dB and prints the volume and the reverberation time it
    # fed them rounded as well, so the inputs carry rounding of their own.
    for room, printed in NPL_REVERBERATION_K2A.items():
        _, volume_m3, time_s, _, _ = NPL_ROOMS[room]
        for surface, want in printed.items():
            got = emission.environmental_correction(
                NPL_SURFACE_M2[surface],
                reverberation_time=time_s,
                volume=volume_m3,
            )
            assert float(got) == pytest.approx(want, abs=0.1), f"{room}{surface}"


def test_the_npl_absolute_factors_are_the_measured_power_less_the_source() -> None:
    # The oracle checked against itself before it is trusted: the absolute
    # rows of Tables 10 to 14 are Table 8 minus the 90,9 dB the reference
    # source was calibrated to, so the two tables are mutually consistent.
    for room, printed in NPL_MEASURED_K2A.items():
        for surface, want in printed.items():
            level = NPL_SOUND_POWER_DB[room][surface]
            assert round(level - NPL_REFERENCE_SOURCE_DB, 1) == want


def test_annex_c_agrees_with_the_npl_measurement_at_the_survey_ceiling() -> None:
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3746"][0]
    assert ceiling == 7.0
    for room, printed in NPL_MEASURED_K2A.items():
        room_surface_m2, _, _, _, alpha = NPL_ROOMS[room]
        for surface, measured in printed.items():
            verdict = noise_control.test_environment_applicability(
                base_standard="ISO 3746",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=NPL_SURFACE_M2[surface],
            )
            assert verdict.applicable is (measured <= ceiling), f"{room}{surface}"


def test_annex_c_refuses_the_hemi_anechoic_room_at_the_precision_ceiling() -> None:
    # Room A is hemi-anechoic and its true absorption is above the 0,5 that
    # Table C.2 stops at, so the annex calls it unfit for ISO 3744 while its
    # measured correction is 0 dB to 1,1 dB. The report says as much in print
    # on folio 18. That is the table running out of room descriptions, not a
    # defect of the closed form, and it is the only room where the two differ.
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3744"][0]
    assert ceiling == 2.0
    differing = []
    for room, printed in NPL_MEASURED_K2A.items():
        room_surface_m2, _, _, _, alpha = NPL_ROOMS[room]
        for surface, measured in printed.items():
            verdict = noise_control.test_environment_applicability(
                base_standard="ISO 3744",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=NPL_SURFACE_M2[surface],
            )
            if verdict.applicable is not (measured <= ceiling):
                differing.append(f"{room}{surface}")
    assert differing == ["A1", "A2", "A3", "A4"]


def test_the_npl_room_e_area_conflict_decides_two_of_its_three_surfaces() -> None:
    # Table 6 on folio 11 prints S_V = 258 m2 for room E and Table 9 on folio
    # 16 prints 358 m2 for the same room and the same volume. Table 9 is the
    # one that pairs the area with the volume and the reverberation time, and
    # it is the one that puts the annex back on the measurement.
    agreeing = {}
    for room_surface_m2 in (358.0, 258.0):
        agreeing[room_surface_m2] = [
            noise_control.test_environment_applicability(
                base_standard="ISO 3746",
                mean_absorption_coefficient=NPL_ROOMS["E"][4],
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=NPL_SURFACE_M2[surface],
            ).applicable
            is (measured <= 7.0)
            for surface, measured in NPL_MEASURED_K2A["E"].items()
        ]
    assert agreeing[358.0] == [True, True, True]
    assert agreeing[258.0] == [False, False, True]


def test_the_npl_estimated_absorption_column_drops_the_factor_four() -> None:
    # The warning this pins: the "estimated room absorption" rows of Tables 10
    # to 14 do not follow the report's own Eq. (3) and Eq. (4). Every one of
    # the 17 cells sits at least 0,45 dB away from it. What the column follows
    # instead is 10 lg (1 + S/(alpha S_V)), the factor 4 dropped, and how
    # closely is asserted as it is rather than under one loose tolerance: 10
    # cells to the half tenth the column is printed to; rooms C and E within
    # 0,2 dB; and the lower bound of room D, surface 4, printed on folio 20 as
    # 0,1 dB where that form gives 0,49 dB, a reading the table's own
    # difference column of -1,8 dB against the measured 1,9 dB confirms.
    # Anyone who anchored the absorption route on that column would read this
    # library as wrong by up to 4,6 dB while it is right.
    departures: dict[str, float] = {}
    for room, printed in NPL_ESTIMATED_K2A.items():
        room_surface_m2, _, _, alpha_from, alpha_to = NPL_ROOMS[room]
        for surface, bounds in printed.items():
            surface_m2 = NPL_SURFACE_M2[surface]
            for bound, alpha in zip(bounds, (alpha_to, alpha_from), strict=True):
                correct = float(
                    emission.environmental_correction(
                        surface_m2,
                        mean_absorption_coefficient=alpha,
                        room_surface=room_surface_m2,
                    )
                )
                without_four = 10.0 * math.log10(
                    1.0 + surface_m2 / (alpha * room_surface_m2)
                )
                assert abs(bound - correct) > 0.4, f"{room}{surface}"
                cell = f"{room}{surface}"
                departures[cell] = max(
                    departures.get(cell, 0.0), abs(bound - without_four)
                )
    within_rounding = {cell for cell, gap in departures.items() if gap <= 0.05}
    assert len(within_rounding) == 10
    assert set(departures) - within_rounding == {
        "C1",
        "C2",
        "C3",
        "D4",
        "E1",
        "E2",
        "E3",
    }
    assert max(gap for cell, gap in departures.items() if cell != "D4") < 0.2
    assert departures["D4"] == pytest.approx(0.388, abs=0.001)


def test_the_baua_engineers_reach_the_printed_environmental_corrections() -> None:
    for name, (alpha, room_surface_m2, _, *printed) in BAUA_ENGINEERS.items():
        for surface_m2, want in zip(BAUA_SURFACES_M2, printed, strict=True):
            got = emission.environmental_correction(
                surface_m2,
                mean_absorption_coefficient=alpha,
                room_surface=room_surface_m2,
            )
            assert float(got) == pytest.approx(want, abs=0.05), name


def test_the_baua_absorption_areas_are_alpha_times_the_boundary_surface() -> None:
    # Eq. (7) of the study, A = alpha S_V, which is Eq. (A.7) of ISO 3744.
    # The tolerance is a hair over half the last printed digit because
    # engineer 2's cell prints 25,9 where 0,15 x 173,0 lands exactly on the
    # tie at 25,95 and the paper rounds it down. That is why alpha and S_V are
    # the inputs the other tests feed, never this rounded area.
    for name, (alpha, room_surface_m2, want, *_) in BAUA_ENGINEERS.items():
        assert alpha * room_surface_m2 == pytest.approx(want, abs=0.06), name


def test_the_baua_engineers_disagree_about_the_same_workroom() -> None:
    # The point of the study. Two engineers put the workroom outside ISO 11202
    # even at 0,5 m and the third, the most experienced, puts it inside at both
    # distances, from assessments of one and the same room. Engineer 1 sits
    # 0,09 dB over the 7 dB ceiling, so a sign slip would not survive this.
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 11202"][0]
    assert ceiling == 7.0
    verdicts = {}
    for name, (alpha, room_surface_m2, _, *printed) in BAUA_ENGINEERS.items():
        verdicts[name] = []
        for surface_m2, want in zip(BAUA_SURFACES_M2, printed, strict=True):
            verdict = noise_control.test_environment_applicability(
                base_standard="ISO 11202",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=surface_m2,
            )
            assert verdict.environmental_correction_limit_db == ceiling
            assert verdict.applicable is (want <= ceiling)
            verdicts[name].append(verdict.applicable)
    assert verdicts["Test Eng. 1"] == [False, False]
    assert verdicts["Test Eng. 2"] == [False, False]
    assert verdicts["Test Eng. 3"] == [True, True]


def test_the_baua_direct_method_absorption_areas_give_the_printed_factors() -> None:
    surfaces = (*BAUA_SURFACES_M2, BAUA_DIRECT_SURFACE_M2)
    for name, (absorption_m2, *printed) in BAUA_DIRECT.items():
        for surface_m2, want in zip(surfaces, printed, strict=True):
            got = emission.environmental_correction(
                surface_m2, absorption_area=absorption_m2
            )
            assert float(got) == pytest.approx(want, abs=0.05), name


def test_the_baua_reverberation_room_level_does_not_fit_its_absorption_area() -> None:
    # A defect in the study, recorded so that the cell is not mistaken for an
    # input later. Eq. (9) of the study, A = 4S / ((S/S0) 10^(0,1 (L_pA - L_W))
    # - 1), closes on the printed 55,2 m2 for the workroom. For the former
    # reverberation room the printed 81,08 dB gives 57,1 m2 rather than the
    # 97,7 m2 beside it; that column would need 79,74 dB. The absorption area
    # is the value the study carries downstream, so it is the one to use.
    def absorption_area(level_db: float) -> float:
        surface_m2 = BAUA_DIRECT_SURFACE_M2
        ratio = surface_m2 * 10.0 ** (0.1 * (level_db - BAUA_SOURCE_POWER_DB))
        return 4.0 * surface_m2 / (ratio - 1.0)

    assert absorption_area(BAUA_LEVEL_IN_SITU_DB["workroom"]) == pytest.approx(
        BAUA_DIRECT["workroom"][0], abs=0.1
    )
    astray = absorption_area(BAUA_LEVEL_IN_SITU_DB["former reverberation room"])
    assert astray == pytest.approx(57.1, abs=0.1)
    assert astray != pytest.approx(BAUA_DIRECT["former reverberation room"][0], abs=1.0)


def test_the_barron_example_prints_both_a_weighted_totals() -> None:
    # The difference of two A-weighted totals hardly constrains the weighting
    # table at all: a whole decibel of error in any one band moves D_pA by at
    # most 0,07 dB. The totals themselves do, and the result object does not
    # publish them, so this reaches the helper that forms them.
    from phonometry.noise_control.enclosure_insulation import _a_weighted_total

    without, with_ = BARRON_TOTALS_DBA
    assert _a_weighted_total(BARRON_WITHOUT_DB, BARRON_OCTAVES_HZ) == pytest.approx(
        without, abs=0.05
    )
    assert _a_weighted_total(BARRON_WITH_DB, BARRON_OCTAVES_HZ) == pytest.approx(
        with_, abs=0.05
    )
    result = noise_control.sound_pressure_insulation(
        BARRON_WITHOUT_DB,
        BARRON_WITH_DB,
        frequencies=BARRON_OCTAVES_HZ,
        base_standard="ISO 11201",
        condition="in-situ",
        source_kind="actual",
        band_fraction=1,
    )
    # Each total carries a twentieth of rounding, so their difference carries a
    # tenth, and that is what D_pA is held to.
    assert result.a_weighted_insulation == pytest.approx(without - with_, abs=0.1)


def test_the_smith_example_gives_one_enclosure_two_a_weighted_values() -> None:
    # Annex D in one page: the same measured band attenuation, applied to two
    # different source spectra, is worth 14 dBA against one machine and
    # 27 dBA against the other, which is why the annex calls its answer an
    # estimate tied to an assumed spectrum rather than a property of the
    # enclosure. The book says so in as many words under its answer box.
    estimates = {
        name: noise_control.estimated_a_weighted_insulation(
            spectrum, SMITH_ATTENUATION_DB, frequencies=SMITH_OCTAVES_HZ
        )
        for name, (spectrum, _) in SMITH_MACHINES.items()
    }
    for name, (_, want) in SMITH_MACHINES.items():
        assert round(estimates[name]) == want
        assert estimates[name] == pytest.approx(want, abs=0.5)
    spread = estimates["machine B"] - estimates["machine A"]
    assert spread == pytest.approx(13.0, abs=0.5)


def test_definition_3_14_counts_the_opening_in_the_interior_surface() -> None:
    # The book prints the wall area without the opening, 95,75 m2, and the
    # opening fraction over the two added back together. The leak ratio of
    # definition 3.14 takes the interior surface with the openings counted in,
    # which is the same 96 m2, and reaches the same printed 2,6e-3.
    ratio = noise_control.leak_ratio(
        SCHIRMER_OPENING_M2, SCHIRMER_WALLS_M2 + SCHIRMER_OPENING_M2
    )
    assert ratio == pytest.approx(SCHIRMER_LEAK_RATIO, abs=5e-5)
    assert noise_control.seal_ratio(ratio) == pytest.approx(384.0)


def test_two_installed_enclosures_give_their_printed_a_weighted_reduction() -> None:
    # Two enclosures measured where they stand, before and after. The levels
    # are printed rounded ("rund 100 dB(A)", "ca. 104 dB"), so what this pins
    # is the order of the subtraction of Equation (4) against real
    # installations, not a precise figure.
    for name, (without, with_, reduction) in IFA_ENCLOSURES.items():
        result = noise_control.sound_pressure_insulation(
            [without],
            [with_],
            a_weighted_without=without,
            a_weighted_with=with_,
            base_standard="ISO 11202",
            condition="in-situ",
            source_kind="actual",
        )
        assert result.a_weighted_insulation == pytest.approx(reduction, abs=0.5), name
        assert result.condition == "in-situ"
