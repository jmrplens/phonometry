#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 4869-1:2018 against its own printed tables.

Annex A works one earmuff on sixteen subjects through the uncertainty of the
mean (Table A.3), and Annex B compares that measurement with a second one
(Table B.1) and prints the minimum differences its typical uncertainties
imply (B.1.1, B.2). Tables A.2 and B.2 print the typical budgets. Every
derived cell of all four tables is checked here from the printed inputs: the
difference row of Table B.1 within the rounding of test 2's printed means,
every other cell to the printed decimal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import reference_data as ref

from phonometry import hearing

_A3 = np.asarray(ref.ISO4869_1_TABLE_A3, dtype=float)


def _table_a3() -> hearing.RealEarAttenuationResult:
    return hearing.real_ear_attenuation(_A3)


# ---------------------------------------------------------------------------
# 4.6 and Annex A: the attenuation of one protector and its uncertainty
# ---------------------------------------------------------------------------


def test_table_a3_derived_rows() -> None:
    """All 28 derived cells of Table A.3, computed at full precision."""
    result = _table_a3()
    assert result.subjects == 16
    assert result.frequencies.tolist() == ref.ISO4869_1_FREQUENCIES
    assert np.round(result.mean_db, 1).tolist() == ref.ISO4869_1_TABLE_A3_MEAN
    assert (
        np.round(result.standard_deviation_db, 1).tolist()
        == ref.ISO4869_1_TABLE_A3_SIGMA
    )
    assert (
        np.round(result.standard_uncertainty_db, 1).tolist() == ref.ISO4869_1_TABLE_A3_U
    )
    assert (
        np.round(result.expanded_uncertainty_db, 1).tolist()
        == ref.ISO4869_1_TABLE_A3_U95
    )


def test_uncertainty_is_the_standard_deviation_of_the_mean() -> None:
    """A.2: u = s / sqrt(N) with N = 16, so the divisor is 4, and U95 = 2u."""
    result = _table_a3()
    np.testing.assert_allclose(
        result.standard_uncertainty_db, result.standard_deviation_db / 4.0
    )
    np.testing.assert_allclose(
        result.expanded_uncertainty_db, 2.0 * result.standard_uncertainty_db
    )
    # The sample standard deviation, over N - 1: the population one over N
    # would print 3,8 at 125 Hz where the table prints 3,9.
    np.testing.assert_allclose(result.standard_deviation_db, _A3.std(axis=0, ddof=1))


def test_attenuation_is_occluded_minus_open_threshold() -> None:
    """4.6.2: the thresholds give the same result as their difference."""
    rng = np.random.default_rng(4869)
    open_ears = rng.uniform(-5.0, 15.0, size=_A3.shape)
    from_thresholds = hearing.real_ear_attenuation(
        open_threshold_db=open_ears, occluded_threshold_db=open_ears + _A3
    )
    np.testing.assert_allclose(from_thresholds.attenuation_db, _A3)
    np.testing.assert_allclose(from_thresholds.mean_db, _table_a3().mean_db)


def test_the_grid_feeds_iso_4869_2_unchanged() -> None:
    """The attenuation grid is what ISO 4869-2 starts from, seven bands and all."""
    grid = _table_a3().attenuation_db
    apv = hearing.assumed_protection_value(grid)
    assert apv.frequencies.tolist() == ref.ISO4869_1_FREQUENCIES
    np.testing.assert_allclose(apv.mean_attenuation, _table_a3().mean_db)
    # HML and SNR read 125 Hz to 8 kHz, which is exactly what 4.1 measures.
    assert hearing.hml_rating(grid).subject_h.shape == (16,)
    assert hearing.snr_rating(grid).subject_snr.shape == (16,)


def test_eight_bands_default_to_63_hz_upwards() -> None:
    """The optional 63 Hz test signal (4.1) makes eight columns from 63 Hz."""
    grid = np.column_stack([_A3[:, 0] - 3.0, _A3])
    assert hearing.real_ear_attenuation(grid).frequencies[0] == 63.0


def test_the_result_holds_its_own_copy_of_the_grid() -> None:
    """Changing the caller's array afterwards leaves the result alone."""
    grid = _A3.copy()
    result = hearing.real_ear_attenuation(grid)
    grid[0, 0] = 99.0
    assert result.attenuation_db[0, 0] == pytest.approx(9.6)


def test_the_result_holds_its_own_copy_of_the_frequencies() -> None:
    freqs = np.asarray(ref.ISO4869_1_FREQUENCIES, dtype=np.float64)
    result = hearing.real_ear_attenuation(_A3, frequencies=freqs)
    freqs[0] = 1.0
    assert result.frequencies[0] == 125.0


def test_both_input_forms_at_once_is_refused() -> None:
    open_ears = np.zeros_like(_A3)
    with pytest.raises(ValueError, match="not both forms"):
        hearing.real_ear_attenuation(
            _A3, open_threshold_db=open_ears, occluded_threshold_db=_A3
        )


def test_one_threshold_alone_is_refused() -> None:
    with pytest.raises(ValueError, match="not both forms"):
        hearing.real_ear_attenuation(open_threshold_db=_A3)


def test_thresholds_of_different_shapes_are_refused() -> None:
    occluded = _A3[:, :6]
    with pytest.raises(ValueError, match="same subjects and bands"):
        hearing.real_ear_attenuation(
            open_threshold_db=_A3, occluded_threshold_db=occluded
        )


def test_a_single_subject_is_refused() -> None:
    one = _A3[:1]
    with pytest.raises(ValueError, match="at least two subjects"):
        hearing.real_ear_attenuation(one)


def test_a_flat_list_is_refused() -> None:
    row = _A3[0]
    with pytest.raises(ValueError, match="subjects, bands"):
        hearing.real_ear_attenuation(row)


def test_a_missing_value_is_refused() -> None:
    grid = _A3.copy()
    grid[3, 2] = np.nan
    with pytest.raises(ValueError, match="only finite values"):
        hearing.real_ear_attenuation(grid)


# ---------------------------------------------------------------------------
# Tables A.2 and B.2: the typical budgets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("library", "printed"),
    [
        (hearing.REAT_WITHIN_LABORATORY_UNCERTAINTY, ref.ISO4869_1_TABLE_A2),
        (hearing.REAT_BETWEEN_LABORATORY_UNCERTAINTY, ref.ISO4869_1_TABLE_B2),
    ],
    ids=["A.2", "B.2"],
)
def test_typical_budgets_reproduce_the_printed_tables(
    library: dict[str, dict[str, hearing.ProtectorUncertaintyBudget]],
    printed: dict[str, list[tuple[float, float, float, float, float]]],
) -> None:
    """The components are transcribed; u and U95 come out of them, rounded last."""
    assert set(library) == set(printed)
    for protector, columns in printed.items():
        budgets = [library[protector][name] for name in hearing.REAT_FREQUENCY_RANGES]
        for budget, (meth, eq, env, u, u95) in zip(budgets, columns, strict=True):
            assert (budget.method_db, budget.equipment_db, budget.environment_db) == (
                meth,
                eq,
                env,
            )
            assert round(budget.combined_db, 1) == u
            assert round(budget.expanded_db, 1) == u95


def test_budgets_are_read_only() -> None:
    table = hearing.REAT_WITHIN_LABORATORY_UNCERTAINTY
    with pytest.raises(TypeError, match="does not support item assignment"):
        table["earplug"]["below 250 Hz"] = hearing.ProtectorUncertaintyBudget(0, 0, 0)  # type: ignore[index]


def test_typical_uncertainty_follows_the_frequency_columns() -> None:
    """63 and 125 Hz fall below 250 Hz; 250 Hz and 4 kHz are inside the middle."""
    freqs = [63.0, 125.0, 250.0, 4000.0, 8000.0]
    within = hearing.reat_expanded_uncertainty(freqs, protector="earplug")
    assert np.round(within, 1).tolist() == [3.2, 3.2, 2.3, 2.3, 3.2]
    between = hearing.reat_expanded_uncertainty(
        freqs, protector="earmuff", between_laboratories=True
    )
    assert np.round(between, 1).tolist() == [4.0, 4.0, 4.9, 4.9, 6.6]


def test_typical_uncertainty_refuses_an_unknown_protector() -> None:
    with pytest.raises(ValueError, match="'protector' must be one of"):
        hearing.reat_expanded_uncertainty([1000.0], protector="helmet")


def test_typical_uncertainty_refuses_a_non_positive_frequency() -> None:
    with pytest.raises(ValueError, match="positive, finite centre frequencies"):
        hearing.reat_expanded_uncertainty([0.0], protector="earplug")


# ---------------------------------------------------------------------------
# Annex B: is the difference significant?
# ---------------------------------------------------------------------------


def _table_b1() -> hearing.AttenuationDifferenceResult:
    return hearing.assess_attenuation_difference(
        _table_a3(),
        ref.ISO4869_1_TABLE_B1_MEAN_2,
        second_expanded_uncertainty_db=ref.ISO4869_1_TABLE_B1_U95_2,
    )


def test_table_b1_criterion_row_and_verdict() -> None:
    """The root-sum-of-squares row, all seven cells, and 'significant at 8 kHz'."""
    result = _table_b1()
    assert np.round(result.criterion_db, 1).tolist() == ref.ISO4869_1_TABLE_B1_CRITERION
    assert result.significant_frequencies.tolist() == ref.ISO4869_1_TABLE_B1_SIGNIFICANT
    assert result.any_significant


def test_the_comparison_holds_its_own_copies() -> None:
    """The means and bands it carries are not the arrays it was given."""
    first = _table_a3()
    means = np.asarray(ref.ISO4869_1_TABLE_B1_MEAN_2, dtype=np.float64)
    result = hearing.assess_attenuation_difference(
        first, means, second_expanded_uncertainty_db=ref.ISO4869_1_TABLE_B1_U95_2
    )
    assert not np.shares_memory(result.first_mean_db, first.mean_db)
    assert not np.shares_memory(result.frequencies, first.frequencies)
    assert not np.shares_memory(result.second_mean_db, means)


def test_table_b1_difference_row_within_the_rounding_of_test_2() -> None:
    """|m1 - m2| is consistent with every printed cell once m2 is unrounded.

    Test 2 prints its means to one decimal, so the m2 behind the difference
    row lies within 0,05 dB of the printed one, and the printed difference is
    that value rounded again: a cell is consistent when some m2 in that
    interval rounds to it, which is a distance of at most 0,1 dB. Six cells
    round to the printed value outright; at 8 kHz the full-precision m1 of
    34,956 dB against the printed m2 of 38,9 dB gives 3,94 dB where the table
    prints 4,0, which an m2 of 38,906 dB or more would give.
    """
    result = _table_b1()
    printed = np.asarray(ref.ISO4869_1_TABLE_B1_DIFFERENCE)
    assert np.abs(result.difference_db - printed).max() <= 0.1
    matching = np.abs(result.difference_db - printed) < 0.05
    assert matching.tolist() == [True] * 6 + [False]


def test_table_b1_test_2_uncertainty_is_consistent_with_its_spread() -> None:
    """The printed U95,2 is 2 sigma_2 / 4 within the rounding of sigma_2."""
    sigma = np.asarray(ref.ISO4869_1_TABLE_B1_SIGMA_2)
    u95 = np.asarray(ref.ISO4869_1_TABLE_B1_U95_2)
    assert np.all(np.abs(u95 - sigma / 2.0) <= 0.05 / 2.0 + 0.05 + 1e-9)


def test_the_test_is_symmetric() -> None:
    forward = _table_b1()
    backward = hearing.assess_attenuation_difference(
        ref.ISO4869_1_TABLE_B1_MEAN_2,
        _table_a3(),
        first_expanded_uncertainty_db=ref.ISO4869_1_TABLE_B1_U95_2,
    )
    np.testing.assert_allclose(backward.difference_db, forward.difference_db)
    assert backward.significant.tolist() == forward.significant.tolist()


def test_a_difference_equal_to_the_criterion_is_not_significant() -> None:
    """B.1.2: significant when the difference is *greater* than the last row."""
    result = hearing.assess_attenuation_difference(
        [30.0],
        [33.0],
        first_expanded_uncertainty_db=3.0,
        second_expanded_uncertainty_db=0.0,
        frequencies=[1000.0],
    )
    assert result.criterion_db[0] == pytest.approx(3.0)
    assert not result.significant[0]


@pytest.mark.parametrize(
    "key",
    list(ref.ISO4869_1_MINIMUM_DIFFERENCES),
    ids=[f"{t} {p}" for t, p in ref.ISO4869_1_MINIMUM_DIFFERENCES],
)
def test_minimum_differences_as_the_text_computes_them(key: tuple[str, str]) -> None:
    """B.1.1 and B.2: sqrt(2) times the rounded U95 the text quotes."""
    u95, printed = ref.ISO4869_1_MINIMUM_DIFFERENCES[key]
    assert round(hearing.minimum_significant_difference(u95), 1) == printed


def test_minimum_difference_from_the_unrounded_budget() -> None:
    """The same rule on the unrounded U95: 3,21 dB and 9,37 dB for the earplug.

    Only the earplug columns move; the earmuff ones round to the printed
    2,3 dB and 6,9 dB either way.
    """
    middle = "250 Hz up to 4 kHz"
    within = hearing.REAT_WITHIN_LABORATORY_UNCERTAINTY
    between = hearing.REAT_BETWEEN_LABORATORY_UNCERTAINTY
    plug_within = hearing.minimum_significant_difference(
        within["earplug"][middle].expanded_db
    )
    plug_between = hearing.minimum_significant_difference(
        between["earplug"][middle].expanded_db
    )
    assert plug_within == pytest.approx(3.2125, abs=5e-5)
    assert plug_between == pytest.approx(9.3680, abs=5e-5)
    muff_within = hearing.minimum_significant_difference(
        within["earmuff"][middle].expanded_db
    )
    muff_between = hearing.minimum_significant_difference(
        between["earmuff"][middle].expanded_db
    )
    assert (round(muff_within, 1), round(muff_between, 1)) == (2.3, 6.9)


def test_minimum_difference_is_the_criterion_for_two_equal_uncertainties() -> None:
    """NOTE 1 to Table B.1: equal uncertainties turn B.1.2 into B.2's form."""
    result = hearing.assess_attenuation_difference(
        [20.0, 30.0],
        [23.0, 31.0],
        first_expanded_uncertainty_db=[2.3, 1.6],
        second_expanded_uncertainty_db=[2.3, 1.6],
        frequencies=[250.0, 1000.0],
    )
    np.testing.assert_allclose(
        result.criterion_db, hearing.minimum_significant_difference([2.3, 1.6])
    )


def test_minimum_difference_returns_a_float_for_a_scalar() -> None:
    assert isinstance(hearing.minimum_significant_difference(2.3), float)
    assert hearing.minimum_significant_difference([1.0, 2.0]).shape == (2,)


def test_minimum_difference_refuses_a_negative_uncertainty() -> None:
    with pytest.raises(ValueError, match="expanded_uncertainty_db"):
        hearing.minimum_significant_difference(-1.0)


def test_bare_means_need_their_uncertainty() -> None:
    first = ref.ISO4869_1_TABLE_B1_MEAN_2
    second = _table_a3()
    with pytest.raises(ValueError, match="'first_expanded_uncertainty_db' is required"):
        hearing.assess_attenuation_difference(first, second)


def test_a_result_does_not_take_a_second_uncertainty() -> None:
    result = _table_a3()
    with pytest.raises(ValueError, match="carried by the first result"):
        hearing.assess_attenuation_difference(
            result,
            result,
            first_expanded_uncertainty_db=1.0,
        )


def test_measurements_over_different_bands_are_refused() -> None:
    first = _table_a3()
    short = ref.ISO4869_1_TABLE_B1_MEAN_2[:6]
    with pytest.raises(ValueError, match="same test signals"):
        hearing.assess_attenuation_difference(
            first, short, second_expanded_uncertainty_db=1.0
        )


def test_results_at_different_frequencies_are_refused() -> None:
    eight = np.column_stack([_A3[:, 0], _A3])[:, :7]
    other = hearing.real_ear_attenuation(
        eight, frequencies=[63, 125, 250, 500, 1000, 2000, 4000]
    )
    first = _table_a3()
    with pytest.raises(ValueError, match="different test signals"):
        hearing.assess_attenuation_difference(first, other)


def test_the_difference_has_no_truth_value() -> None:
    result = _table_b1()
    with pytest.raises(TypeError, match="no truth value"):
        bool(result)


# ---------------------------------------------------------------------------
# 4.2.2 and Table 1: the sound field of the test site
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rejection", "allowed"),
    [(30.0, 20.0), (25.0, 20.0), (24.9, 15.0), (20.0, 15.0), (15.0, 10.0), (10.0, 5.0)],
)
def test_table_1_boundaries(rejection: float, allowed: float) -> None:
    """Each row's lower edge belongs to it (25 <= FFR, 20 <= FFR < 25, ...)."""
    assert hearing.allowable_field_variation(rejection) == allowed


def test_table_1_transcription() -> None:
    assert [tuple(row) for row in ref.ISO4869_1_TABLE_1] == list(
        hearing.REAT_FIELD_VARIATION_LIMITS
    )


def test_a_microphone_below_10_db_rejection_is_not_suitable() -> None:
    with pytest.raises(ValueError, match="not suitable"):
        hearing.allowable_field_variation(9.9)


_SIX = ("front", "back", "left", "right", "up", "down")


def _positions(values: tuple[float, ...], bands: int = 7) -> dict[str, np.ndarray]:
    return {
        name: np.full(bands, value) for name, value in zip(_SIX, values, strict=True)
    }


def test_a_qualifying_sound_field() -> None:
    check = hearing.check_reat_sound_field(
        _positions((1.0, -1.0, 1.4, -1.4, 2.5, -2.5)),
        np.zeros(7),
        rotation_levels_db=np.vstack([np.zeros(7), np.full(7, 5.0)]),
        free_field_rejection_db=12.0,
    )
    assert check.passes
    assert check.allowable_variation_db == 5.0
    # 4.2.2 b) starts at 500 Hz: the two bands below are not read.
    assert np.isnan(check.rotation_variation_db[:2]).all()
    assert check.rotation_variation_db[2:].tolist() == [5.0] * 5


@pytest.mark.parametrize(
    "offsets",
    [(0.0, 0.0, 0.0, 0.0, 2.6, 0.0), (0.0, 0.0, 0.0, 0.0, 0.0, -2.6)],
    ids=["up above", "down below"],
)
def test_a_position_past_2_5_db_fails_the_band(offsets: tuple[float, ...]) -> None:
    """±2,5 dB either way: a position 2,6 dB below fails as one above does."""
    check = hearing.check_reat_sound_field(_positions(offsets), np.zeros(7))
    assert not check.passes
    assert not check.uniform.any()


@pytest.mark.parametrize(
    ("left", "right"), [(-1.6, 1.6), (1.6, -1.6)], ids=["right louder", "left louder"]
)
def test_right_and_left_within_2_5_db_can_still_be_3_db_apart(
    left: float, right: float
) -> None:
    """Both side positions inside ±2,5 dB, yet 3,2 dB apart: a) fails on balance."""
    check = hearing.check_reat_sound_field(
        _positions((0.0, 0.0, left, right, 0.0, 0.0)), np.zeros(7)
    )
    assert check.uniform.all()
    assert not check.balanced.any()
    np.testing.assert_allclose(check.left_right_difference_db, 3.2)
    assert not check.passes


def test_without_the_rotation_the_room_is_not_shown_to_qualify() -> None:
    """4.2.2 b) is a 'shall': a) alone does not make the room qualify."""
    check = hearing.check_reat_sound_field(_positions((0.0,) * 6), np.zeros(7))
    assert check.uniform.all()
    assert check.balanced.all()
    assert not check.directionality_judged
    assert not check.passes


def test_bands_below_500_hz_need_no_rotation() -> None:
    """b) starts at 500 Hz, so a check that stops below it is judged whole."""
    check = hearing.check_reat_sound_field(
        _positions((0.0,) * 6, bands=2), np.zeros(2), frequencies=[125.0, 250.0]
    )
    assert check.directionality_judged
    assert check.passes


def test_a_rotation_past_table_1_fails_only_from_500_hz() -> None:
    rotation = np.vstack([np.zeros(7), np.full(7, 11.0)])
    rotation[:, :2] = np.nan  # below 500 Hz, not measured
    check = hearing.check_reat_sound_field(
        _positions((0.0,) * 6),
        np.zeros(7),
        rotation_levels_db=rotation,
        free_field_rejection_db=20.0,
    )
    assert check.diffuse.tolist() == [True, True] + [True] * 5
    stricter = hearing.check_reat_sound_field(
        _positions((0.0,) * 6),
        np.zeros(7),
        rotation_levels_db=rotation,
        free_field_rejection_db=15.0,
    )
    assert stricter.diffuse.tolist() == [True, True] + [False] * 5
    assert not stricter.passes


def test_a_missing_position_is_refused() -> None:
    five = _positions((0.0,) * 6)
    del five["down"]
    reference = np.zeros(7)
    with pytest.raises(ValueError, match="six positions of 4.2.2"):
        hearing.check_reat_sound_field(five, reference)


def test_a_rotation_without_its_microphone_is_refused() -> None:
    rotation = np.zeros((2, 7))
    six = _positions((0.0,) * 6)
    reference = np.zeros(7)
    with pytest.raises(ValueError, match="together"):
        hearing.check_reat_sound_field(six, reference, rotation_levels_db=rotation)


def test_the_sound_field_check_has_no_truth_value() -> None:
    check = hearing.check_reat_sound_field(_positions((0.0,) * 6), np.zeros(7))
    with pytest.raises(TypeError, match="no truth value"):
        bool(check)


def test_the_coverage_factor_is_two() -> None:
    budget = hearing.ProtectorUncertaintyBudget(0.6, 0.3, 0.4)
    assert budget.expanded_db == pytest.approx(2.0 * math.sqrt(0.61))
