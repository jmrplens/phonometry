#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the sound reduction index of joints (ISO 10140-1:2021 Annex J).

Oracles:

- Formula (J.1) in closed form, with every term away from zero, and the
  3 dB a doubled joint length is worth.
- Formula (J.2) in closed form, and the printed 1,3 dB that ISO 10140-2:2021
  A.3 says "corresponds to a difference of 6 dB": the formula at 6 dB rounds
  to it.
- The four regimes of J.1 at their printed bounds, 10 dB, 6 dB and 3 dB,
  including a 6 dB margin that binary arithmetic puts a hair below six.
- The J.1 example of a lower limit, "(Rs >= 50,4 dB)".
- ISO 10140-2:2021 Table A.1, a flanking spectrum the standard rates itself,
  59 (-2; -7) dB, carried through the joint front end with no correction.
- The open-band rating checked by hand against ISO 717-1 Clauses 4.4 and 4.5:
  four indicative bands that limit the rating lift it from 51 to 59 dB, which
  puts the single numbers in brackets.
- The bounds of J.2.1, J.2.2 and J.4 as printed, and the three gap widths
  J.4 asks a variable slit to be measured at.
- The form of Figure J.7 read back out of the PDF: every labelled number,
  the single numbers J.1 puts in brackets, and the rating of the maximum
  of the arrangement, 61 (-1; -6) dB, with C100-5000 = 0 dB and
  Ctr,100-5000 = -4 dB for the example seal, checked by hand against the
  Table 4 spectra of ISO 717-1:2020.
"""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING

import numpy as np
import pytest
import reference_data as ref

from phonometry import ReportMetadata, building
from phonometry.building.measurement.joint_insulation import (
    LabJointInsulationResult,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

#: The 18 bands of ISO 10140-2, 100 Hz to 5000 Hz.
_BANDS = [
    *(100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0),
    *(800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0),
]


def _j2(measured: float, maximum: float) -> float:
    """Formula (J.2) as printed."""
    return -10.0 * math.log10(10.0 ** (-measured / 10.0) - 10.0 ** (-maximum / 10.0))


def _one_band(
    measured: float, maximum: float, **kwargs: bool
) -> LabJointInsulationResult:
    return building.lab_joint_insulation([measured], [maximum], [1000.0], **kwargs)


# --- Formula (J.1) -------------------------------------------------------------


def test_formula_j1_closed_form() -> None:
    """Rs = L1 - L2 + 10 lg(Sn l / (A ln)) with Sn = 1 m2 and ln = 1 m."""
    got = building.joint_sound_reduction_index(
        [92.0, 90.0], [55.0, 50.0], [8.0, 12.5], joint_length_m=5.4
    )
    expected = [
        92.0 - 55.0 + 10.0 * math.log10(5.4 / 8.0),
        90.0 - 50.0 + 10.0 * math.log10(5.4 / 12.5),
    ]
    assert got == pytest.approx(expected, abs=1e-12)


def test_doubling_the_joint_length_is_worth_three_decibels() -> None:
    """Twice the joint lets twice the power through; per metre it is the same."""
    short = building.joint_sound_reduction_index(
        [90.0], [50.0], [10.0], joint_length_m=2.0
    )
    long = building.joint_sound_reduction_index(
        [90.0], [50.0], [10.0], joint_length_m=4.0
    )
    assert long[0] - short[0] == pytest.approx(10.0 * math.log10(2.0), abs=1e-12)


def test_positions_are_energy_averaged() -> None:
    """A (positions, bands) level array is averaged on energy (ISO 10140-2)."""
    got = building.joint_sound_reduction_index(
        [[90.0], [96.0]], [50.0], [10.0], joint_length_m=10.0
    )
    l1 = 10.0 * math.log10((10.0**9.0 + 10.0**9.6) / 2.0)
    assert got[0] == pytest.approx(l1 - 50.0, abs=1e-12)


def test_formula_j1_refuses_a_band_count_mismatch() -> None:
    with pytest.raises(ValueError, match="same shape"):
        building.joint_sound_reduction_index(
            [90.0, 91.0], [50.0], [10.0, 10.0], joint_length_m=5.0
        )


def test_formula_j1_refuses_a_zero_length() -> None:
    with pytest.raises(ValueError, match="joint_length_m"):
        building.joint_sound_reduction_index([90.0], [50.0], [10.0], joint_length_m=0.0)


def test_formula_j1_refuses_a_zero_absorption() -> None:
    with pytest.raises(ValueError, match="absorption_m2"):
        building.joint_sound_reduction_index([90.0], [50.0], [0.0], joint_length_m=5.0)


# --- The flanking correction of J.1 -------------------------------------------


def test_printed_limit_correction_is_formula_j2_at_six_decibels() -> None:
    """ISO 10140-2:2021 A.3: 1,3 dB "corresponds to a difference of 6 dB"."""
    margin = ref.ISO10140_1_J1_LIMIT_MARGIN_DB
    correction = _j2(50.0, 50.0 + margin) - 50.0
    assert round(correction, 1) == pytest.approx(ref.ISO10140_1_J1_LIMIT_CORRECTION_DB)
    res = _one_band(50.0, 50.0 + margin - 0.1)
    assert res.r_s_db[0] - 50.0 == pytest.approx(ref.ISO10140_1_J1_LIMIT_CORRECTION_DB)


@pytest.mark.parametrize(
    ("margin", "regime"),
    [
        (12.0, "uncorrected"),
        (10.0, "uncorrected"),
        (9.9, "corrected"),
        (6.0, "corrected"),
        (5.9, "limit"),
        (3.0, "limit"),
        (2.9, "maximum"),
        (0.0, "maximum"),
        (-1.0, "maximum"),
    ],
)
def test_regimes_at_their_printed_bounds(margin: float, regime: str) -> None:
    """10 dB and 6 dB are inclusive; "larger than Rs,max - 3 dB" is strict."""
    res = _one_band(45.0, 45.0 + margin)
    assert res.regime == (regime,)


def test_each_regime_gives_its_value() -> None:
    measured = np.array([45.0, 45.0, 45.0, 45.0])
    maximum = np.array([57.0, 52.0, 49.0, 46.5])
    res = building.lab_joint_insulation(
        measured, maximum, [500.0, 630.0, 800.0, 1000.0]
    )
    assert res.r_s_db == pytest.approx([45.0, _j2(45.0, 52.0), 46.3, 46.5], abs=1e-12)
    assert res.minimum_value.tolist() == [False, False, True, True]


def test_six_decibels_reached_in_decimals_is_still_formula_j2() -> None:
    """36,3 - 30,3 comes out a hair below 6 in binary; it is a 6 dB margin."""
    assert 36.3 - 30.3 < 6.0
    res = _one_band(30.3, 36.3)
    assert res.regime == ("corrected",)
    assert res.r_s_db[0] == pytest.approx(_j2(30.3, 36.3), abs=1e-12)


def test_the_maximum_rule_is_optional() -> None:
    """J.1 "may" set the lower limit to Rs,max; without it, 1,3 dB applies."""
    res = _one_band(48.0, 50.4, limit_at_maximum=False)
    assert res.regime == ("limit",)
    assert res.r_s_db[0] == pytest.approx(49.3)


def test_printed_lower_limit_example() -> None:
    """J.1: "(Rs >= 50,4 dB)" for a measured index within 3 dB of Rs,max."""
    maximum = ref.ISO10140_1_J1_EXAMPLE_MINIMUM_DB
    res = _one_band(maximum - 2.0, maximum)
    assert res.regime == ("maximum",)
    assert res.r_s_db[0] == pytest.approx(maximum)
    assert res.indicative.tolist() == [True]


def test_indicative_bands_follow_the_measured_index_whatever_the_rule() -> None:
    res = _one_band(48.0, 50.4, limit_at_maximum=False)
    assert res.indicative.tolist() == [True]


def test_result_refuses_mismatched_columns() -> None:
    good = _one_band(45.0, 60.0)
    two_bands = np.array([500.0, 1000.0])
    with pytest.raises(ValueError, match="band"):
        LabJointInsulationResult(
            frequencies_hz=two_bands,
            r_s_measured_db=good.r_s_measured_db,
            r_s_max_db=good.r_s_max_db,
            r_s_db=good.r_s_db,
            joint_length_m=None,
            rating=None,
            c_100_5000_db=None,
            ctr_100_5000_db=None,
            max_rating=None,
            open_band_rating=None,
        )


def _columns(good: LabJointInsulationResult) -> dict[str, object]:
    return {
        "frequencies_hz": good.frequencies_hz,
        "r_s_measured_db": good.r_s_measured_db,
        "r_s_max_db": good.r_s_max_db,
        "r_s_db": good.r_s_db,
        "joint_length_m": None,
        "rating": None,
        "c_100_5000_db": None,
        "ctr_100_5000_db": None,
        "max_rating": None,
        "open_band_rating": None,
    }


def test_result_takes_no_regime() -> None:
    """The regime is read from the columns, so none can be handed in beside them."""
    columns = _columns(_one_band(45.0, 60.0))
    with pytest.raises(TypeError, match="regime"):
        LabJointInsulationResult(**columns, regime=("maximum",))  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("maximum", "limit_at_maximum", "regime"),
    [
        (60.0, True, "uncorrected"),
        (52.0, True, "corrected"),
        (49.0, True, "limit"),
        (46.0, True, "maximum"),
        (46.0, False, "limit"),
    ],
)
def test_a_hand_built_result_reads_its_regime_from_its_columns(
    maximum: float, *, limit_at_maximum: bool, regime: str
) -> None:
    """The regime follows the measured and maximum indices and the J.1 rule."""
    columns = _columns(_one_band(45.0, maximum, limit_at_maximum=limit_at_maximum))
    res = LabJointInsulationResult(**columns, limit_at_maximum=limit_at_maximum)  # type: ignore[arg-type]
    assert res.regime == (regime,)


def test_a_hand_built_result_refuses_the_correction_of_another_rule() -> None:
    """Within 3 dB of the maximum, J.1 gives 1,3 dB or the maximum, not both."""
    columns = _columns(_one_band(45.0, 46.0, limit_at_maximum=True))
    with pytest.raises(ValueError, match="r_s_db"):
        LabJointInsulationResult(**columns, limit_at_maximum=False)  # type: ignore[arg-type]


def test_lab_joint_insulation_refuses_a_length_mismatch() -> None:
    with pytest.raises(ValueError, match="same shape"):
        building.lab_joint_insulation([45.0, 46.0], [60.0], [500.0, 630.0])


# --- Single numbers ------------------------------------------------------------


def test_table_a1_of_iso_10140_2_rates_as_printed() -> None:
    """R'F of ISO 10140-2:2021 Table A.1 rates 59 (-2; -7) dB, uncorrected."""
    measured = np.asarray(ref.ISO10140_2_TABLE_A1_R_F)
    res = building.lab_joint_insulation(measured, measured + 20.0, _BANDS)
    assert res.rating is not None
    got = (res.rating.rating, res.rating.c, res.rating.ctr)
    assert got == ref.ISO10140_2_TABLE_A1_RATING
    assert set(res.regime) == {"uncorrected"}
    assert res.open_band_rating is None
    assert res.bracketed is False


def test_enlarged_range_terms_need_the_bands_to_5000_hz() -> None:
    measured = np.asarray(ref.ISO10140_2_TABLE_A1_R_F)
    full = building.lab_joint_insulation(measured, measured + 20.0, _BANDS)
    core = building.lab_joint_insulation(
        measured[:16], measured[:16] + 20.0, _BANDS[:16]
    )
    extended = building.weighted_rating_extended(measured, _BANDS)
    assert (full.c_100_5000_db, full.ctr_100_5000_db) == (
        extended.c_100_5000,
        extended.ctr_100_5000,
    )
    assert core.c_100_5000_db is None
    assert core.ctr_100_5000_db is None
    assert core.rating is not None


def test_no_rating_without_the_core_bands() -> None:
    res = building.lab_joint_insulation([45.0] * 3, [60.0] * 3, [500.0, 630.0, 800.0])
    assert res.rating is None
    assert res.r_s_w_db is None
    assert res.r_s_w_ctr_db is None
    assert res.bracketed is False


def test_single_number_properties() -> None:
    measured = np.asarray(ref.ISO10140_2_TABLE_A1_R_F)
    res = building.lab_joint_insulation(measured, measured + 20.0, _BANDS)
    assert (res.r_s_w_db, res.r_s_w_c_db, res.r_s_w_ctr_db) == (59, 57, 52)


def test_maximum_of_the_arrangement_is_rated() -> None:
    maximum = np.asarray(ref.ISO10140_2_TABLE_A1_R_F)
    res = building.lab_joint_insulation(maximum - 15.0, maximum, _BANDS)
    assert res.max_rating is not None
    assert res.max_rating.rating == ref.ISO10140_2_TABLE_A1_RATING[0]


def _dip_case() -> LabJointInsulationResult:
    """A joint whose limiting bands 400 Hz to 800 Hz are indicative."""
    maximum = np.full(18, 70.0)
    maximum[6:10] = 44.0
    measured = maximum - 12.0
    measured[6:10] = 42.0
    return building.lab_joint_insulation(measured, maximum, _BANDS)


def test_open_bands_rated_by_hand() -> None:
    """Four limiting bands taken as open lift Rs,w from 51 dB to 59 dB.

    By hand, from ISO 717-1:2020 Clause 4.4: with 400 Hz to 800 Hz open the
    twelve remaining bands sit at 58 dB, and the reference shifted by +7 dB
    leaves 29 dB of unfavourable deviations (4 dB at 1000 Hz and 5 dB at
    each of the five bands from 1250 Hz) where +8 dB would leave 35 dB, so
    Rs,w = 52 + 7 = 59 dB. Clause 4.5 with spectrum No 1 over those twelve
    bands gives XA = 58 - 10 lg 0,7787 = 59,1 dB, so C = 0 dB.
    """
    res = _dip_case()
    assert res.rating is not None
    assert res.rating.rating == 51
    opened = res.open_band_rating
    assert opened is not None
    assert opened.open_frequencies_hz == (400.0, 500.0, 630.0, 800.0)
    assert (opened.r_s_w_db, opened.c_db) == (59, 0)
    assert res.bracketed is True


def test_open_bands_that_do_not_limit_leave_no_brackets() -> None:
    maximum = np.asarray(ref.ISO10140_2_TABLE_A1_R_F)
    measured = maximum - 15.0
    measured[-1] = maximum[-1] - 2.0
    res = building.lab_joint_insulation(measured, maximum, _BANDS)
    assert res.open_band_rating is not None
    assert res.open_band_rating.open_frequencies_hz == (5000.0,)
    assert res.bracketed is False


def test_every_band_open_is_unbounded() -> None:
    res = building.lab_joint_insulation(np.full(18, 38.5), np.full(18, 40.0), _BANDS)
    opened = res.open_band_rating
    assert opened is not None
    assert opened.r_s_w_db is None
    assert opened.c_100_5000_db is None
    assert res.bracketed is True


def test_indicative_bands_are_read_on_the_measured_index() -> None:
    """A band 3,5 dB under the maximum is not indicative, whatever its Rs.

    With the 1,3 dB correction its corrected index sits 2,2 dB under
    Rs,max: read on Rs it would look indicative, read on R's (J.1) it is not,
    and the rating is not formed a second time.
    """
    maximum = np.full(18, 60.0)
    measured = maximum - 12.0
    measured[7] = maximum[7] - 3.5
    res = building.lab_joint_insulation(measured, maximum, _BANDS)
    assert res.regime[7] == "limit"
    assert res.r_s_max_db[7] - res.r_s_db[7] == pytest.approx(2.2)
    assert not res.indicative.any()
    assert res.open_band_rating is None


def test_octave_bands_average_the_transmitted_power() -> None:
    res = building.lab_joint_insulation(
        [40.0, 43.0, 46.0], [80.0, 80.0, 80.0], [400.0, 500.0, 630.0]
    )
    centres, values = res.octave_bands()
    expected = -10.0 * math.log10(
        np.mean(10.0 ** (-np.array([40.0, 43.0, 46.0]) / 10.0))
    )
    assert centres.tolist() == [500.0]
    assert values[0] == pytest.approx(expected, abs=1e-12)


# --- J.2: the test element ------------------------------------------------------


@pytest.mark.parametrize(
    ("length_m", "width_mm", "gap", "passes"),
    [
        (1.0, 20.0, False, False),
        (1.01, 20.0, False, True),
        (2.0, 50.0, False, True),
        (2.0, 50.1, False, False),
        (4.99, 5.0, True, False),
        (5.0, 5.0, True, True),
    ],
)
def test_test_element_bounds(
    length_m: float, width_mm: float, *, gap: bool, passes: bool
) -> None:
    """Longer than 1 m, at most 50 mm wide, and 5,0 m for a window or door gap."""
    check = building.check_joint_test_element(
        length_m, width_mm, window_or_door_gap=gap
    )
    assert check.passes is passes


def test_test_element_check_has_no_truth_value() -> None:
    check = building.check_joint_test_element(2.0, 10.0)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_test_element_check_refuses_a_negative_width() -> None:
    with pytest.raises(ValueError, match="joint_width_mm"):
        building.check_joint_test_element(2.0, -1.0)


def test_gap_width_is_the_average_of_four_readings() -> None:
    """J.2.2: "The average value is denoted as gap width, b"; not the median.

    The readings have a mean of 5,075 mm and a median of 5,0 mm.
    """
    check = building.check_gap_width([5.0, 5.0, 5.0, 5.3])
    assert check.gap_width_mm == pytest.approx(5.075)
    assert check.spread_mm == pytest.approx(0.3)
    assert check.passes is True


def test_gap_width_spread_bound_is_inclusive_in_decimals() -> None:
    """4,9 - 4,6 comes out a hair above 0,3 in binary: still 0,3 mm."""
    assert 4.9 - 4.6 > 0.3
    assert building.check_gap_width([4.6, 4.9, 4.7, 4.8]).uniform is True


def test_gap_width_readings_spread_too_far() -> None:
    check = building.check_gap_width([4.9, 5.25, 5.0, 5.1])
    assert check.uniform is False
    assert check.passes is False


def test_gap_width_needs_four_positions() -> None:
    check = building.check_gap_width([5.0, 5.0, 5.0])
    assert check.enough_positions is False
    assert check.passes is False


def test_gap_width_check_has_no_truth_value() -> None:
    check = building.check_gap_width([5.0, 5.0, 5.0, 5.0])
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_gap_width_refuses_a_negative_reading() -> None:
    with pytest.raises(ValueError, match="readings_mm"):
        building.check_gap_width([5.0, -0.1, 5.0, 5.0])


# --- J.4 and J.5: a variable slit ---------------------------------------------


def _series() -> building.JointGapSeries:
    maximum = np.asarray(ref.ISO10140_2_TABLE_A1_R_F) + 5.0
    widths = [8.0, 3.0, 5.0]
    drops = {3.0: 6.0, 5.0: 10.0, 8.0: 18.0}
    results = [
        building.lab_joint_insulation(maximum - drops[w], maximum, _BANDS)
        for w in widths
    ]
    return building.joint_gap_series(widths, results, minimum_gap_mm=3.0)


def test_series_is_sorted_by_width_and_defaults_to_five_millimetres() -> None:
    series = _series()
    assert series.gap_widths_mm.tolist() == [3.0, 5.0, 8.0]
    assert series.working_range_mm == (5.0, 8.0)
    assert series.r_s_w_db[0] > series.r_s_w_db[-1]


def test_series_reads_the_line_between_the_measured_widths() -> None:
    series = _series()
    expected = np.interp(6.5, series.gap_widths_mm, series.r_s_w_ctr_db)
    assert series.at_gap(6.5) == pytest.approx(expected)
    assert series.at_gap(5.0, "r_s_w") == pytest.approx(series.r_s_w_db[1])


def test_series_never_extrapolates() -> None:
    series = _series()
    with pytest.raises(ValueError, match="outside the measured widths"):
        series.at_gap(9.0)


def test_series_refuses_a_repeated_width() -> None:
    results = _series().results
    with pytest.raises(ValueError, match="repeat"):
        building.joint_gap_series([3.0, 3.0, 5.0], results)


def test_series_refuses_a_result_without_rating() -> None:
    bare = building.lab_joint_insulation([45.0], [60.0], [1000.0])
    with pytest.raises(ValueError, match="rating"):
        building.joint_gap_series([5.0], [bare])


def test_series_refuses_a_count_mismatch() -> None:
    results = _series().results
    with pytest.raises(ValueError, match="one result per width"):
        building.joint_gap_series([3.0, 5.0], results)


def test_series_refuses_an_unknown_quantity() -> None:
    series = _series()
    with pytest.raises(ValueError, match="quantity"):
        series.single_number("r_s_w_c_tr")  # type: ignore[arg-type]


def test_series_measured_at_the_three_widths_of_j4_passes() -> None:
    check = building.check_joint_gap_series(_series())
    assert (
        check.nominal_measured,
        check.minimum_measured,
        check.working_range_measured,
    ) == (True, True, True)
    assert check.passes is True


def test_series_without_the_working_range_end_fails() -> None:
    """J.4 c): the test "shall be repeated" at bn + 3, here 8 mm."""
    series = _series()
    short = building.joint_gap_series(
        series.gap_widths_mm[:2], series.results[:2], minimum_gap_mm=3.0
    )
    check = building.check_joint_gap_series(short)
    assert check.working_range_measured is False
    assert check.nominal_measured is True
    assert check.passes is False


def test_series_that_names_no_minimum_width_fails() -> None:
    """J.4 b): nothing shows which width was bmin unless the series says."""
    series = _series()
    unnamed = building.joint_gap_series(series.gap_widths_mm, series.results)
    check = building.check_joint_gap_series(unnamed)
    assert check.minimum_gap_mm is None
    assert check.minimum_measured is False
    assert check.passes is False


@pytest.mark.parametrize(("nominal", "measured"), [(4.7, True), (4.69, False)])
def test_series_width_within_the_reading_spread_counts(
    nominal: float, *, measured: bool
) -> None:
    """A width within the 0,3 mm of J.2.2 of bn is bn; 0,31 mm away is not."""
    series = _series()
    moved = building.joint_gap_series(
        series.gap_widths_mm,
        series.results,
        nominal_gap_mm=nominal,
        minimum_gap_mm=3.0,
    )
    check = building.check_joint_gap_series(moved)
    assert check.nominal_measured is measured
    assert check.tolerance_mm == pytest.approx(0.3)


def test_series_check_has_no_truth_value() -> None:
    check = building.check_joint_gap_series(_series())
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# --- The form of Figure J.7 ------------------------------------------------------


def _example_joint() -> LabJointInsulationResult:
    maximum = np.array(
        [40.2, 42.8, 45.1, 48.6, 51.9, 54.3, 56.8, 58.9, 60.7]
        + [62.4, 63.8, 65.1, 66.2, 67.0, 67.6, 68.1, 68.5, 69.0]
    )
    measured = np.array(
        [33.4, 35.1, 37.9, 40.6, 43.0, 45.2, 46.1, 46.8, 47.0]
        + [46.2, 45.1, 46.9, 49.8, 52.6, 55.4, 58.9, 63.1, 66.2]
    )
    return building.lab_joint_insulation(measured, maximum, _BANDS, joint_length_m=5.4)


def _text(path: Path) -> str:
    from pypdf import PdfReader

    return " ".join(
        " ".join(page.extract_text() for page in PdfReader(str(path)).pages).split()
    )


def test_joint_form_renders_one_page(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")
    from report_assertions import assert_one_page

    out = tmp_path / "j7.pdf"
    metadata = ReportMetadata(
        client="Example client",
        specimen="EPDM rebate seal",
        test_date="2026-10-01",
        separating_element="Lead-lined filler wall",
        test_signal="Pink noise",
        source_volume=53.0,
        receiving_volume=51.0,
        mounting="Leaf closed to the nominal gap",
        receiving_temperature_c=20.5,
        receiving_relative_humidity_percent=47.0,
        laboratory="Example laboratory",
        report_id="J-1",
        requirement=45.0,
    )
    _example_joint().report(str(out), metadata=metadata)
    assert_one_page(out)
    text = _text(out)
    assert "Rs,w (C; Ctr) = 49 (-1; -4) dB" in text
    assert "Test length l [m]: 5.4" in text
    assert (
        "Maximum joint sound reduction index: Rs,max,w (C; Ctr) = 61 (-1; -6) dB"
        in (text)
    )
    assert "C100-5000 = +0 dB; Ctr,100-5000 = -4 dB" in text
    assert "Climate in the test rooms: receiving room 20.5 °C, 47 %" in text
    assert "Pink noise" in text
    assert "(≥ 69.0)" in text
    assert "≥ 64.4" in text
    assert "PASS" in text


def test_joint_form_brackets_the_single_numbers(tmp_path: Path) -> None:
    """J.1 brackets every single number on the form, the enlarged range too."""
    pytest.importorskip("reportlab")
    out = tmp_path / "bracketed.pdf"
    _dip_case().report(str(out))
    text = _text(out)
    assert "(Rs,w (C; Ctr) = 51 (-1; -2) dB)" in text
    assert "(C100-5000 = +0 dB; Ctr,100-5000 = -2 dB)" in text
    assert (
        "Rs,w (C; Ctr) = 59 (+0; +1) dB; C100-5000 = +0 dB; Ctr,100-5000 = +0 dB"
        in (text)
    )


def test_joint_form_shows_the_enlarged_range_term_that_moved(
    tmp_path: Path,
) -> None:
    """Only Rw + C100-5000 moves (37 dB to 56 dB): the note shows its +1 dB."""
    pytest.importorskip("reportlab")
    maximum = np.full(18, 70.0)
    maximum[-2:] = 30.0
    measured = maximum - 15.0
    measured[-2:] = 29.0
    res = building.lab_joint_insulation(measured, maximum, _BANDS)
    assert res.bracketed is True
    out = tmp_path / "wide.pdf"
    res.report(str(out))
    text = _text(out)
    assert "(Rs,w (C; Ctr) = 55 (+0; +0) dB)" in text
    assert "(C100-5000 = -18 dB; Ctr,100-5000 = -11 dB)" in text
    assert "C100-5000 = +1 dB; Ctr,100-5000 = +0 dB (J.1)" in text


@pytest.mark.parametrize(
    ("fields", "climate"),
    [
        (
            {
                "source_temperature_c": 21.3,
                "source_relative_humidity_percent": 44.0,
                "receiving_temperature_c": 20.5,
                "receiving_relative_humidity_percent": 47.0,
            },
            "source room 21.3 °C, 44 % / receiving room 20.5 °C, 47 %",
        ),
        (
            {"source_temperature_c": 21.3, "source_relative_humidity_percent": 44.0},
            "source room 21.3 °C, 44 %",
        ),
        ({"temperature_c": 21.0, "relative_humidity_percent": 50.0}, "21 °C, 50 %"),
    ],
)
def test_joint_form_prints_the_climate_of_both_rooms(
    tmp_path: Path, fields: dict[str, float], climate: str
) -> None:
    """Figure J.7 asks for the "Climate in the test rooms", both of them."""
    pytest.importorskip("reportlab")
    out = tmp_path / "climate.pdf"
    _example_joint().report(str(out), metadata=ReportMetadata(**fields))
    assert f"Climate in the test rooms: {climate}" in _text(out)


def test_joint_form_draws_the_printed_diagram_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The diagram of Figure J.7 runs from 30 dB to 80 dB, widened by 10 dB."""
    pytest.importorskip("reportlab")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    from phonometry._report import iso10140_1

    drawn: list[tuple[float, float]] = []

    def capture(path: str, **kwargs: object) -> str:
        plot = kwargs["plot"]
        _fig, ax = plt.subplots()
        plot.draw(ax=ax)  # type: ignore[attr-defined]
        drawn.append(ax.get_ylim())
        plt.close("all")
        return path

    monkeypatch.setattr(iso10140_1, "compose_insulation_fiche", capture)
    _example_joint().report(str(tmp_path / "a.pdf"))
    quiet = building.lab_joint_insulation(np.full(18, 22.0), np.full(18, 85.0), _BANDS)
    quiet.report(str(tmp_path / "b.pdf"))
    assert drawn == [(30.0, 80.0), (20.0, 90.0)]


def test_joint_form_in_spanish_and_verbose(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")
    from report_assertions import assert_one_page

    out = tmp_path / "j7_es.pdf"
    _example_joint().report(str(out), verbose=True, language="es")
    assert_one_page(out)
    text = _text(out)
    assert "Índice de reducción acústica de juntas" in text
    assert "64,4" in text


def test_joint_form_needs_a_rating(tmp_path: Path) -> None:
    bare = building.lab_joint_insulation([45.0], [60.0], [1000.0])
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="rating"):
        bare.report(out)


def test_joint_form_refuses_an_unknown_engine(tmp_path: Path) -> None:
    res = _example_joint()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        res.report(out, engine="latex")


# --- What the figures draw -------------------------------------------------------


@pytest.fixture
def agg_backend() -> Iterator[None]:
    """Draw on the Agg backend and close every figure afterwards."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    yield
    plt.close("all")


@pytest.mark.usefixtures("agg_backend")
def test_joint_figure_marks_the_minimum_values() -> None:
    res = _example_joint()
    ax = res.plot()
    triangles = [line for line in ax.lines if line.get_marker() == "^"]
    assert len(triangles) == 1
    assert len(triangles[0].get_xdata()) == int(np.sum(res.minimum_value))
    labels = ax.get_legend_handles_labels()[1]
    assert any("shifted reference" in label for label in labels)
    assert "49" in ax.get_title()


@pytest.mark.usefixtures("agg_backend")
def test_joint_figure_brackets_its_headline() -> None:
    ax = _dip_case().plot(language="es")
    headline = ax.get_title().splitlines()[-1]
    assert headline.startswith("(")
    assert headline.endswith(")")


@pytest.mark.usefixtures("agg_backend")
def test_gap_series_figure_marks_the_working_range() -> None:
    series = _series()
    ax = series.plot(quantity="r_s_w")
    verticals = sorted(
        float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_linestyle() in {"--", ":", "-."}
    )
    assert verticals == [3.0, 5.0, 8.0]
    measured = [line for line in ax.lines if line.get_marker() == "o"]
    assert measured[0].get_ydata().tolist() == series.r_s_w_db.tolist()


@pytest.mark.usefixtures("agg_backend")
def test_gap_series_octave_figure_draws_the_sealed_element_and_each_width() -> None:
    """J.5.1: Figure J.9 gives the closed and sealed element (b = 0) as Rs,max."""
    from phonometry.building.measurement.floor_covering_improvement import (
        improvement_octave_bands,
    )

    series = _series()
    ax = series.plot_octave_bands()
    assert len(ax.lines) == len(series.gap_widths_mm) + 1
    sealed = series.results[0]
    _, maximum = improvement_octave_bands(sealed.r_s_max_db, sealed.frequencies_hz)
    assert ax.lines[0].get_ydata() == pytest.approx(maximum)
    assert "R_\\mathrm{s,max}" in ax.lines[0].get_label()
    for line, result in zip(ax.lines[1:], series.results, strict=True):
        assert line.get_ydata() == pytest.approx(result.octave_bands()[1])
    assert "Figure J.9" in ax.get_title()
    legend = ax.get_legend()
    assert legend is not None
    assert len(legend.get_texts()) == len(series.gap_widths_mm) + 1


@pytest.mark.usefixtures("agg_backend")
def test_joint_figure_draws_each_column_as_its_curve() -> None:
    res = _example_joint()
    ax = res.plot()
    by_label = {line.get_label(): line for line in ax.lines}
    corrected = next(v for k, v in by_label.items() if "corrected" in k)
    measured = next(v for k, v in by_label.items() if "measured" in k)
    maximum = next(v for k, v in by_label.items() if "sealed joint" in k)
    assert corrected.get_ydata() == pytest.approx(res.r_s_db)
    assert measured.get_ydata() == pytest.approx(res.r_s_measured_db)
    assert maximum.get_ydata() == pytest.approx(res.r_s_max_db)


def test_joint_figure_lines_keep_three_to_one_on_a_dark_page() -> None:
    """The maximum and the measured index read on the dark theme too."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb

    from phonometry._plot.common import contrast_ratio

    with plt.style.context("dark_background"):
        ax = _example_joint().plot()
        page = to_rgb(ax.get_facecolor())
        ratios = [
            contrast_ratio(to_rgb(line.get_color()), page)
            for line in ax.lines
            if "sealed joint" in line.get_label() or "measured" in line.get_label()
        ]
    plt.close("all")
    assert len(ratios) == 2
    assert min(ratios) >= 3.0


@pytest.mark.usefixtures("agg_backend")
def test_open_band_figure_draws_and_labels_every_value() -> None:
    opened = _dip_case().open_band_rating
    assert opened is not None
    ax = opened.plot()
    heights = [patch.get_height() for patch in ax.patches]
    assert heights == [59.0, 0.0, 1.0, 0.0, 0.0]
    labels = [text.get_text() for text in ax.texts]
    assert labels == ["59", "0", "+1", "0", "0"]


@pytest.mark.usefixtures("agg_backend")
def test_open_band_figure_speaks_of_single_numbers_in_spanish() -> None:
    opened = _dip_case().open_band_rating
    assert opened is not None
    ax = opened.plot(language="es")
    assert ax.get_title().startswith("Magnitudes globales")
    assert ax.get_ylabel() == "magnitud global [dB]"


@pytest.mark.usefixtures("agg_backend")
def test_test_element_figure_draws_each_ratio_to_its_bound() -> None:
    check = building.check_joint_test_element(5.4, 20.0, window_or_door_gap=True)
    ax = check.plot()
    widths = [patch.get_width() for patch in ax.patches]
    assert widths == pytest.approx([5.4 / 5.0, 20.0 / 50.0])


@pytest.mark.usefixtures("agg_backend")
def test_test_element_figure_never_prints_a_false_inequality() -> None:
    """A 62 mm joint reads "required ≤ 50 mm", not "62.0 mm ≤ 50 mm"."""
    ax = building.check_joint_test_element(1.0, 62.0).plot()
    labels = [label.get_text() for label in ax.get_yticklabels()]
    assert labels == [
        "length 1.00 m\nrequired > 1.0 m",
        "width 62.0 mm\nrequired ≤ 50 mm",
    ]


@pytest.mark.usefixtures("agg_backend")
@pytest.mark.parametrize(
    ("language", "label"),
    [
        ("en", "0.3 mm from the smallest reading"),
        ("es", "0,3 mm desde la lectura menor"),
    ],
)
def test_gap_width_figure_writes_the_bound_in_its_language(
    language: str, label: str
) -> None:
    ax = building.check_gap_width([5.0, 5.1, 4.9, 5.05, 5.15]).plot(language=language)
    assert label in ax.get_legend_handles_labels()[1]


@pytest.mark.usefixtures("agg_backend")
def test_gap_series_figure_writes_the_printed_symbol() -> None:
    """Figure J.8 and J.5.1 print Rs,Atr."""
    ax = _series().plot()
    assert "R_\\mathrm{s,Atr}" in ax.get_ylabel()


@pytest.mark.usefixtures("agg_backend")
def test_gap_series_check_figure_marks_the_three_widths() -> None:
    check = building.check_joint_gap_series(_series())
    ax = check.plot()
    verticals = sorted(
        float(line.get_xdata()[0])
        for line in ax.lines
        if line.get_linestyle() in {"--", ":", "-."}
    )
    assert verticals == [3.0, 5.0, 8.0]
    points = [line for line in ax.lines if line.get_marker() == "o"]
    assert points[0].get_xdata().tolist() == [3.0, 5.0, 8.0]
    assert ax.get_title().endswith("conforms")


@pytest.mark.usefixtures("agg_backend")
def test_verdict_figures_name_the_verdict() -> None:
    passing = building.check_joint_test_element(5.4, 5.0, window_or_door_gap=True)
    failing = building.check_gap_width([4.9, 5.25, 5.0, 5.1])
    assert "does not conform" not in passing.plot().get_title()
    assert "does not conform" in failing.plot().get_title()


@pytest.mark.parametrize(("lift", "bracketed"), [(1, False), (2, True)])
def test_brackets_take_more_than_one_decibel(lift: int, *, bracketed: bool) -> None:
    """J.1: "If that result differs by more than 1 dB" the numbers go in brackets."""
    base = _dip_case()
    assert base.rating is not None
    opened = building.JointOpenBandRating(
        open_frequencies_hz=(500.0,),
        r_s_w_db=base.rating.rating + lift,
        c_db=base.rating.c - lift,
        ctr_db=base.rating.ctr - lift,
        c_100_5000_db=base.c_100_5000_db,
        ctr_100_5000_db=base.ctr_100_5000_db,
    )
    shifted = dataclasses.replace(base, open_band_rating=opened)
    # Rs,w moves by the lift; Rs,w + C and Rs,w + Ctr stay where they were.
    assert shifted.bracketed is bracketed


@pytest.mark.parametrize("term", ["c_db", "ctr_db", "c_100_5000_db", "ctr_100_5000_db"])
@pytest.mark.parametrize(("lift", "bracketed"), [(1, False), (2, True)])
def test_brackets_follow_every_single_number(
    term: str, lift: int, *, bracketed: bool
) -> None:
    """Rs,w unchanged, one term moved: Rs,w + that term decides the brackets."""
    base = _dip_case()
    assert base.rating is not None
    unchanged = building.JointOpenBandRating(
        open_frequencies_hz=(500.0,),
        r_s_w_db=base.rating.rating,
        c_db=base.rating.c,
        ctr_db=base.rating.ctr,
        c_100_5000_db=base.c_100_5000_db,
        ctr_100_5000_db=base.ctr_100_5000_db,
    )
    assert dataclasses.replace(base, open_band_rating=unchanged).bracketed is False
    current = getattr(unchanged, term)
    assert current is not None
    moved = dataclasses.replace(unchanged, **{term: current + lift})
    assert dataclasses.replace(base, open_band_rating=moved).bracketed is bracketed
