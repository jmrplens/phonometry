#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 4869-6:2019 against its printed Annex A and ISO's calculation workbook.

Annex A prints the active insertion loss of sixteen subjects (Table A.3) and a
typical budget (Table A.2). Clause 5.5 names the calculation workbook ISO
publishes beside the standard as the example of its chain, and every step of
that chain the workbook stores is pinned here: the lower-ear selection (rows
134-149), the interpolated passive attenuation (182-197), the one-third-octave
and octave totals (206-221, 230-245), and the mean, standard deviation and APV
they reduce to (247-249). The workbook rounds the interpolation, Formula (1),
the mean and the standard deviation to 0,1 dB, and leaves the lower-ear
selection and the sums as they come; the library rounds nothing, so each
comparison states the rounding it allows for. Linear operation (5.4.4) prints
no example and is held to its clause on constructed data.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pytest
import reference_data as ref

from phonometry import hearing

_A3 = np.asarray(ref.ISO4869_6_TABLE_A3, dtype=float)
_OCTAVES = [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0]


def _half_up(values: np.ndarray) -> np.ndarray:
    """Round to one decimal, halves away from zero, as the workbook's ROUND does."""

    def one(value: float) -> float:
        exact = Decimal(repr(round(float(value), 9)))
        return float(exact.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    return np.vectorize(one)(np.asarray(values, dtype=float))


def _workbook_insertion_loss() -> hearing.ActiveInsertionLossResult:
    return hearing.active_insertion_loss(
        passive_levels_db=ref.ISO4869_6_WORKBOOK_PASSIVE_LEVELS,
        active_levels_db=ref.ISO4869_6_WORKBOOK_ACTIVE_LEVELS,
    )


def _workbook_total() -> hearing.AnrTotalAttenuationResult:
    return hearing.anr_total_attenuation(
        ref.ISO4869_6_WORKBOOK_REAT, _workbook_insertion_loss()
    )


# ---------------------------------------------------------------------------
# Annex A: the uncertainty of the mean active insertion loss
# ---------------------------------------------------------------------------


def test_table_a3_mean_and_spread() -> None:
    """The mean and sigma rows of Table A.3, all 16 cells, at full precision."""
    result = hearing.active_insertion_loss(_A3)
    assert result.subjects == 16
    assert result.frequencies.tolist() == _OCTAVES
    assert np.round(result.mean_db, 1).tolist() == ref.ISO4869_6_TABLE_A3_MEAN
    assert (
        np.round(result.standard_deviation_db, 1).tolist()
        == ref.ISO4869_6_TABLE_A3_SIGMA
    )


def test_table_a3_uncertainty_rows_come_from_the_rounded_row_above() -> None:
    """u = sigma/4 and U95 = 2u reproduce the print only from the rounded rows.

    Table A.3 forms its u row from the sigma it displays (1,4 / 4 = 0,35,
    printed 0,4) and its U95 row from the u it displays. At full precision
    one u cell and six U95 cells come out a tenth lower. The library returns
    the full-precision values; see docs/ERRATA.md.
    """
    result = hearing.active_insertion_loss(_A3)
    printed_sigma = np.asarray(ref.ISO4869_6_TABLE_A3_SIGMA)
    as_printed_u = _half_up(printed_sigma / 4.0)
    assert as_printed_u.tolist() == ref.ISO4869_6_TABLE_A3_U
    assert _half_up(2.0 * as_printed_u).tolist() == ref.ISO4869_6_TABLE_A3_U95
    # The library is A.1 and A.2 applied to the printed rows, rounded once.
    spread = _A3.std(axis=0, ddof=1)
    np.testing.assert_allclose(result.standard_uncertainty_db, spread / 4.0)
    np.testing.assert_allclose(result.expanded_uncertainty_db, spread / 2.0)
    full_u = _half_up(result.standard_uncertainty_db)
    full_u95 = _half_up(result.expanded_uncertainty_db)
    differing_u = np.flatnonzero(full_u != np.asarray(ref.ISO4869_6_TABLE_A3_U))
    differing_u95 = np.flatnonzero(full_u95 != np.asarray(ref.ISO4869_6_TABLE_A3_U95))
    assert tuple(differing_u) == ref.ISO4869_6_TABLE_A3_U_ROUNDED_FROM_SIGMA
    assert tuple(differing_u95) == ref.ISO4869_6_TABLE_A3_U95_ROUNDED_FROM_U
    # Every one of them is a tenth low, never high.
    printed_u95 = np.asarray(ref.ISO4869_6_TABLE_A3_U95)
    np.testing.assert_allclose(
        (printed_u95 - full_u95)[list(differing_u95)], 0.1, atol=1e-9
    )


def test_table_a3_negative_values_are_kept_with_their_sign() -> None:
    """Above 500 Hz the circuit adds sound: the means are negative and stay so."""
    result = hearing.active_insertion_loss(_A3)
    assert (result.mean_db[4:] < 0.0).all()
    np.testing.assert_allclose(result.insertion_loss_db, _A3)


def test_table_a2_budget() -> None:
    """u = 0,78 dB and U95 = 1,6 dB from the three components of Table A.2."""
    budget = hearing.ANR_WITHIN_LABORATORY_UNCERTAINTY
    meth, eq, env, u, u95 = ref.ISO4869_6_TABLE_A2
    assert (budget.method_db, budget.equipment_db, budget.environment_db) == (
        meth,
        eq,
        env,
    )
    assert round(budget.combined_db, 2) == u
    assert round(budget.expanded_db, 1) == u95


# ---------------------------------------------------------------------------
# 5.4.1 and 5.5 b): the insertion loss and the lower ear
# ---------------------------------------------------------------------------


def test_lower_ear_matches_the_workbook() -> None:
    """All 384 lower-ear cells of the workbook (rows 134-149)."""
    result = _workbook_insertion_loss()
    np.testing.assert_allclose(
        result.insertion_loss_db, ref.ISO4869_6_WORKBOOK_LOWER_EAR, atol=1e-9
    )
    assert result.frequencies.tolist() == ref.ISO4869_6_THIRD_OCTAVES
    assert result.per_ear_db is not None
    assert result.per_ear_db.shape == (16, 2, 24)


def test_the_result_holds_its_own_copy_of_the_grid() -> None:
    """Changing the caller's array afterwards leaves the result alone."""
    per_ear = np.asarray(ref.ISO4869_6_WORKBOOK_PASSIVE_LEVELS) - np.asarray(
        ref.ISO4869_6_WORKBOOK_ACTIVE_LEVELS
    )
    left = float(per_ear[0, 0, 0])
    result = hearing.active_insertion_loss(per_ear)
    per_ear[0, 0, 0] = 99.0
    assert result.per_ear_db is not None
    assert result.per_ear_db[0, 0, 0] == pytest.approx(left)
    assert result.insertion_loss_db[0, 0] == pytest.approx(
        ref.ISO4869_6_WORKBOOK_LOWER_EAR[0][0]
    )


def test_the_workbook_lower_ear_at_the_octaves_is_table_a3() -> None:
    """The standard's Table A.3 is the workbook's lower-ear rows at 63 Hz to 8 kHz."""
    result = _workbook_insertion_loss()
    columns = [ref.ISO4869_6_THIRD_OCTAVES.index(f) for f in _OCTAVES]
    np.testing.assert_allclose(result.insertion_loss_db[:, columns], _A3, atol=1e-9)


def test_insertion_loss_per_ear_equals_levels() -> None:
    passive = np.asarray(ref.ISO4869_6_WORKBOOK_PASSIVE_LEVELS)
    active = np.asarray(ref.ISO4869_6_WORKBOOK_ACTIVE_LEVELS)
    direct = hearing.active_insertion_loss(passive - active)
    np.testing.assert_allclose(
        direct.insertion_loss_db, _workbook_insertion_loss().insertion_loss_db
    )


def test_the_lower_ear_is_chosen_band_by_band() -> None:
    """5.5 b) picks the ear per band, not per subject."""
    per_ear = np.array(
        [
            [[10.0, 2.0, 7.0], [8.0, 5.0, 7.0]],
            [[1.0, 9.0, -1.0], [3.0, 4.0, -2.0]],
        ]
    )
    result = hearing.active_insertion_loss(per_ear, frequencies=[100, 125, 160])
    np.testing.assert_allclose(result.insertion_loss_db, [[8, 2, 7], [1, 4, -2]])


def test_both_input_forms_at_once_is_refused() -> None:
    levels = ref.ISO4869_6_WORKBOOK_PASSIVE_LEVELS
    with pytest.raises(ValueError, match="not both forms"):
        hearing.active_insertion_loss(
            _A3, passive_levels_db=levels, active_levels_db=levels
        )


def test_one_ear_per_subject_is_refused_for_levels() -> None:
    one_ear = np.asarray(ref.ISO4869_6_WORKBOOK_PASSIVE_LEVELS)[:, :1, :]
    with pytest.raises(ValueError, match="both ears"):
        hearing.active_insertion_loss(
            passive_levels_db=one_ear, active_levels_db=one_ear
        )


def test_an_unknown_band_count_needs_frequencies() -> None:
    five = _A3[:, :5]
    with pytest.raises(ValueError, match="pass 'frequencies' explicitly"):
        hearing.active_insertion_loss(five)


def test_a_missing_value_is_refused() -> None:
    grid = _A3.copy()
    grid[2, 3] = np.nan
    with pytest.raises(ValueError, match="finite values"):
        hearing.active_insertion_loss(grid)


# ---------------------------------------------------------------------------
# 5.5 a) to e): the total attenuation, against the workbook
# ---------------------------------------------------------------------------


def test_interpolated_reat_matches_the_workbook() -> None:
    """All 384 cells of rows 182-197, once rounded the way the workbook rounds."""
    result = _workbook_total()
    assert result.third_octave_frequencies.tolist() == ref.ISO4869_6_THIRD_OCTAVES
    assert (
        _half_up(result.reat_third_octave_db).tolist()
        == ref.ISO4869_6_WORKBOOK_REAT_THIRDS
    )


def test_interpolation_is_linear_in_hertz() -> None:
    """80 Hz sits (80 - 63) / (125 - 63) of the way, as the workbook has it."""
    reat = np.tile([10.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 30.0], (2, 1))
    active = np.zeros((2, 24))
    result = hearing.anr_total_attenuation(reat, active)
    at_80 = result.reat_third_octave_db[0, 2]
    assert at_80 == pytest.approx(10.0 + 10.0 * (80.0 - 63.0) / (125.0 - 63.0))
    # The ends continue the first and the last segment.
    assert result.reat_third_octave_db[0, 0] == pytest.approx(10.0 - 10.0 * 13.0 / 62.0)
    assert result.reat_third_octave_db[0, -1] == pytest.approx(30.0 + 10.0 * 0.5)


def test_total_thirds_match_the_workbook() -> None:
    """Rows 206-221, within the 0,05 dB the workbook's rounding of a) leaves."""
    result = _workbook_total()
    workbook = np.asarray(ref.ISO4869_6_WORKBOOK_TOTAL_THIRDS)
    assert np.abs(result.total_third_octave_db - workbook).max() <= 0.05 + 1e-9


def test_octave_totals_match_the_workbook() -> None:
    """Rows 230-245 (Formula (1)), within the 0,1 dB two roundings leave.

    The workbook rounds the interpolated passive value and then the octave
    result, each by up to 0,05 dB; the library rounds neither.
    """
    result = _workbook_total()
    workbook = np.asarray(ref.ISO4869_6_WORKBOOK_TOTAL_OCTAVES)
    assert result.total_octave_db.shape == (16, 8)
    assert np.abs(result.total_octave_db - workbook).max() <= 0.1


def test_formula_1_on_the_workbook_thirds_gives_every_octave_cell_exactly() -> None:
    """The library's Formula (1) on the workbook's own one-third-octave totals.

    That separates the arithmetic from the rounding. A passive attenuation of
    zero interpolates to zero in every band, so the library's one-third-octave
    totals are the workbook's rows 206-221 exactly, and its octave totals,
    rounded the way the workbook's ROUND rounds, are all 128 cells of rows
    230-245.
    """
    thirds = np.asarray(ref.ISO4869_6_WORKBOOK_TOTAL_THIRDS)
    result = hearing.anr_total_attenuation(np.zeros((16, 8)), thirds)
    np.testing.assert_array_equal(result.total_third_octave_db, thirds)
    assert _half_up(result.total_octave_db).tolist() == (
        ref.ISO4869_6_WORKBOOK_TOTAL_OCTAVES
    )


def test_mean_sd_and_apv_match_the_workbook() -> None:
    """Rows 247-249: mean and SD to 0,1 dB, and APV84 as the workbook forms it."""
    result = _workbook_total()
    apv = result.assumed_protection
    assert apv.performance == 84
    mean = _half_up(apv.mean_attenuation)
    spread = _half_up(apv.standard_deviation)
    assert mean.tolist() == ref.ISO4869_6_WORKBOOK_MEAN
    assert spread.tolist() == ref.ISO4869_6_WORKBOOK_SD
    assert _half_up(mean - spread).tolist() == ref.ISO4869_6_WORKBOOK_APV84
    # Unrounded, the APV is within 0,1 dB of the workbook's row.
    assert np.abs(apv.apv - np.asarray(ref.ISO4869_6_WORKBOOK_APV84)).max() <= 0.1


def test_ratings_are_iso_4869_2_at_84_percent() -> None:
    """5.5 e): the octave totals go into ISO 4869-2 unchanged."""
    result = _workbook_total()
    grid = result.total_octave_db
    assert result.hml.reported == hearing.hml_rating(grid).reported
    assert result.snr.reported == hearing.snr_rating(grid).reported
    assert result.hml.performance == result.snr.performance == 84


def test_a_reat_result_and_its_grid_give_the_same_total() -> None:
    reat = hearing.real_ear_attenuation(ref.ISO4869_6_WORKBOOK_REAT)
    from_result = hearing.anr_total_attenuation(reat, _workbook_insertion_loss())
    np.testing.assert_allclose(
        from_result.total_octave_db, _workbook_total().total_octave_db
    )


def test_reat_from_125_hz_uses_the_bands_from_100_hz() -> None:
    reat = np.asarray(ref.ISO4869_6_WORKBOOK_REAT)[:, 1:]
    result = hearing.anr_total_attenuation(reat, _workbook_insertion_loss())
    assert result.frequencies.tolist() == _OCTAVES[1:]
    assert result.third_octave_frequencies[0] == 100.0
    assert result.total_octave_db.shape == (16, 7)


def test_insertion_loss_from_100_hz_gives_the_total_from_125_hz() -> None:
    """5.3.1: without the bands below 100 Hz the total starts at 125 Hz."""
    from_100 = hearing.active_insertion_loss(
        np.asarray(ref.ISO4869_6_WORKBOOK_LOWER_EAR)[:, 3:]
    )
    result = hearing.anr_total_attenuation(ref.ISO4869_6_WORKBOOK_REAT, from_100)
    assert result.frequencies.tolist() == _OCTAVES[1:]
    np.testing.assert_allclose(
        result.total_octave_db, _workbook_total().total_octave_db[:, 1:]
    )


def test_different_subjects_are_refused() -> None:
    fifteen = np.asarray(ref.ISO4869_6_WORKBOOK_REAT)[:15]
    active = _workbook_insertion_loss()
    with pytest.raises(ValueError, match="same subjects"):
        hearing.anr_total_attenuation(fifteen, active)


def test_an_octave_insertion_loss_is_refused() -> None:
    """Table A.3 is on octave bands; the chain needs one-third octaves."""
    octave_only = hearing.active_insertion_loss(_A3)
    with pytest.raises(ValueError, match="one-third-octave band"):
        hearing.anr_total_attenuation(ref.ISO4869_6_WORKBOOK_REAT, octave_only)


def test_a_reat_off_the_octave_bands_is_refused() -> None:
    reat = hearing.real_ear_attenuation(
        ref.ISO4869_6_WORKBOOK_REAT,
        frequencies=[50, 100, 200, 400, 800, 1600, 3150, 6300],
    )
    active = _workbook_insertion_loss()
    with pytest.raises(ValueError, match="octave bands 63 Hz or 125 Hz"):
        hearing.anr_total_attenuation(reat, active)


# ---------------------------------------------------------------------------
# 5.4.4: linear operation
# ---------------------------------------------------------------------------

_EXTERNAL = [90.0, 95.0, 100.0, 105.0, 110.0]


def _ears(steps: list[float], ears: int = 4) -> np.ndarray:
    """Ear levels whose steps are the given increments, the same at every ear."""
    start = np.full((ears, 1), 60.0)
    return np.hstack([start, start + np.cumsum(steps)[None, :].repeat(ears, 0)])


def test_linear_to_110_db() -> None:
    result = hearing.assess_anr_linearity(_EXTERNAL, _ears([5.0, 5.0, 5.0, 5.0]))
    assert result.passes
    assert result.linear_to_110_db
    assert result.maximum_linear_level_db == 110.0


def test_the_tolerance_is_one_decibel_either_way_inclusive() -> None:
    """Steps of 4 dB and 6 dB are linear, and the reported level agrees."""
    result = hearing.assess_anr_linearity(_EXTERNAL, _ears([4.0, 6.0, 4.0, 6.0]))
    assert result.passes
    assert result.linear_to_110_db
    assert result.maximum_linear_level_db == 110.0


def test_linear_throughout_but_stopping_below_110_db() -> None:
    """Linear over every step taken, yet 5.6 i) cannot state 110 dB."""
    result = hearing.assess_anr_linearity(
        [90.0, 95.0, 100.0, 105.0], _ears([5.0, 5.0, 5.0])
    )
    assert result.passes
    assert result.maximum_linear_level_db == 105.0
    assert not result.linear_to_110_db


def test_a_short_step_caps_the_linear_level_below_it() -> None:
    """A 3,9 dB step from 100 dB to 105 dB leaves 100 dB as the highest linear level."""
    levels = _ears([5.0, 5.0, 5.0, 5.0])
    levels[2, 3:] -= 1.1  # one ear falls behind on the step to 105 dB
    result = hearing.assess_anr_linearity(_EXTERNAL, levels)
    assert not result.passes
    assert not result.linear_to_110_db
    assert result.maximum_linear_level_db == 100.0
    assert result.linear[2].tolist() == [True, True, False, True]


def test_the_first_step_failing_leaves_the_starting_level() -> None:
    result = hearing.assess_anr_linearity(_EXTERNAL, _ears([7.0, 5.0, 5.0, 5.0]))
    assert result.maximum_linear_level_db == 90.0


def test_any_leading_axes_are_ears() -> None:
    """Samples, subjects and ears can be separate axes; each row is one ear."""
    levels = _ears([5.0] * 4, ears=4 * 16 * 2).reshape(4, 16, 2, 5)
    result = hearing.assess_anr_linearity(_EXTERNAL, levels)
    assert result.ear_levels_db.shape == (128, 5)
    assert result.passes


def test_third_octaves_are_summed_into_the_125_hz_octave() -> None:
    octave = _ears([5.0, 5.0, 5.0, 5.0], ears=2)
    thirds = np.stack([octave - 10.0 * np.log10(3.0)] * 3, axis=-1)
    from_thirds = hearing.assess_anr_linearity(
        _EXTERNAL, ear_third_octave_levels_db=thirds
    )
    np.testing.assert_allclose(from_thirds.ear_levels_db, octave)


def test_steps_other_than_5_db_are_refused() -> None:
    external = [90.0, 94.0, 100.0]
    ears = _ears([4.0, 6.0])
    with pytest.raises(ValueError, match="5 dB steps"):
        hearing.assess_anr_linearity(external, ears)


def test_levels_above_110_db_are_refused() -> None:
    external = [100.0, 105.0, 110.0, 115.0]
    ears = _ears([5.0, 5.0, 5.0])
    with pytest.raises(ValueError, match="above 110 dB"):
        hearing.assess_anr_linearity(external, ears)


def test_both_ear_forms_are_refused() -> None:
    octave = _ears([5.0] * 4)
    thirds = np.stack([octave] * 3, axis=-1)
    with pytest.raises(ValueError, match="not both"):
        hearing.assess_anr_linearity(
            _EXTERNAL, octave, ear_third_octave_levels_db=thirds
        )


def test_the_linearity_verdict_has_no_truth_value() -> None:
    result = hearing.assess_anr_linearity(_EXTERNAL, _ears([5.0] * 4))
    with pytest.raises(TypeError, match="no truth value"):
        bool(result)
