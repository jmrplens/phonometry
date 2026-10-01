#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the quality assurance of outdoor sound software (ISO 17534-1:2015).

Oracle: BS ISO 17534-1:2015, whose pages carry the ISO 17534-1:2015(E) text.
Table B.2, the worked TRC form, on printed folio 16 (PDF page 24); Table C.1,
Formulas (C.1) and (C.2) and the worked example of C.4 on printed folio 20
(PDF page 28). The worked TRC form of ISO/TR 17534-3:2015, Table 69, on
printed page 53 (PDF page 59). The transcriptions live in
``reference_data.software_quality`` so the conformance report reads the same
numbers.

What DIN 45687:2006-05 says of Table C.1 and of the two formulas, which the
module docstring weighs before it keeps the seam at 50 values as printed, was
read in its Annex F.4 and Tables F.1 and F.2, printed folios 34 and 35. The
source F.4 names for the table, VDI 3723 Blatt 1:1993-05, was read on its
Seite 7 and 8 (Tables 5 and 6), and anchors Table C.1 a second time.
"""

from __future__ import annotations

import math
import statistics
import warnings
from fractions import Fraction
from types import MappingProxyType

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import environment
from phonometry.environment.propagation import software_quality as sq

# --------------------------------------------------------------------------- #
# Table C.1 and Formulas (C.1), (C.2)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("n", "r01", "r09"), ref.ISO17534_1_TABLE_C1)
def test_ranking_positions_read_every_row_of_table_c1(
    n: int, r01: int, r09: int
) -> None:
    assert environment.ranking_positions(n) == (r01, r09)


def test_the_published_table_is_the_printed_one_and_cannot_be_changed() -> None:
    assert isinstance(environment.RANKING_POSITIONS, MappingProxyType)
    printed = {n: (r01, r09) for n, r01, r09 in ref.ISO17534_1_TABLE_C1}
    assert dict(environment.RANKING_POSITIONS) == printed
    assert tuple(environment.RANKING_POSITIONS) == tuple(range(20, 51))
    assert all(isinstance(row, tuple) for row in environment.RANKING_POSITIONS.values())
    with pytest.raises(TypeError, match="does not support item assignment"):
        environment.RANKING_POSITIONS[51] = (5, 46)  # type: ignore[index]


def test_table_c1_is_symmetric_in_every_row() -> None:
    """R(q0,9) = N + 1 - R(q0,1): as many values below one as above the other."""
    for n, r01, r09 in ref.ISO17534_1_TABLE_C1:
        assert r09 == n + 1 - r01, n


def test_table_c1_is_the_k_columns_of_vdi_3723_blatt_1() -> None:
    """The source DIN 45687 F.4 names for the table gives the same 31 rows.

    R(q0,1) is the ranking position of L_x;90 in Table 6 of VDI 3723 Blatt 1
    and R(q0,9) that of L_x;10 in its Table 5, read on the guideline's own
    pages rather than on ISO 17534-1's, and the two columns are mirror images
    there too.
    """
    lx90 = dict(ref.VDI3723_1_TABLE_6_K)
    lx10 = dict(ref.VDI3723_1_TABLE_5_K)
    assert tuple(lx90) == tuple(lx10) == tuple(range(20, 51))
    for n in range(20, 51):
        assert environment.ranking_positions(n) == (lx90[n], lx10[n]), n
        assert lx10[n] == n + 1 - lx90[n], n


def test_formula_c1_reproduces_the_first_column_of_the_table() -> None:
    for n, r01, _ in ref.ISO17534_1_TABLE_C1:
        assert math.floor((n + 4) / 10) == r01, n


def test_formula_c2_misses_fifteen_rows_of_the_table_by_one_rank() -> None:
    """The seam the module docstring explains: (C.2) is not the table's rule."""
    missed = [
        n for n, _, r09 in ref.ISO17534_1_TABLE_C1 if math.floor(9 * n / 10) + 1 != r09
    ]
    assert missed == [*range(21, 26), *range(31, 36), *range(41, 46)]
    for n, _, r09 in ref.ISO17534_1_TABLE_C1:
        if n in missed:
            assert math.floor(9 * n / 10) + 1 == r09 - 1


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        # At 51 the formulas take over: (C.2) gives 46, one below the 47 the
        # table's symmetry would give, and R(q0,9) stands still across 50/51.
        (51, (5, 46)),
        (55, (5, 50)),
        (56, (6, 51)),
        (60, (6, 55)),
        (61, (6, 55)),
        (100, (10, 91)),
        (1000, (100, 901)),
    ],
)
def test_above_fifty_values_the_two_formulas_apply(
    n: int, expected: tuple[int, int]
) -> None:
    assert environment.ranking_positions(n) == expected


def test_formula_c2_is_taken_in_integer_arithmetic() -> None:
    """9N/10 is formed exactly, so no rounding can push a rank across a whole."""
    for n in range(51, 5001):
        r01, r09 = environment.ranking_positions(n)
        assert r01 == (n + 4) // 10
        assert r09 == (9 * n) // 10 + 1


def test_ranking_positions_refuse_a_sample_below_twenty() -> None:
    with pytest.raises(ValueError, match="sample_size"):
        environment.ranking_positions(19)


@pytest.mark.parametrize("bad", [25.5, True, "25", math.nan])
def test_ranking_positions_refuse_what_is_not_a_count(bad: object) -> None:
    with pytest.raises(ValueError, match="sample_size"):
        environment.ranking_positions(bad)  # type: ignore[arg-type]


def test_a_whole_float_is_a_count() -> None:
    assert environment.ranking_positions(25.0) == (2, 24)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# C.4: the worked example and the characteristic values
# --------------------------------------------------------------------------- #


def test_the_worked_example_of_c4() -> None:
    result = environment.level_difference_quantiles(
        ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB
    )
    rank_q01, rank_q09 = ref.ISO17534_1_EXAMPLE_RANKS
    q01_db, q09_db = ref.ISO17534_1_EXAMPLE_QUANTILES_DB
    assert result.rank_q01 == rank_q01
    assert result.rank_q09 == rank_q09
    assert result.q01_db == pytest.approx(q01_db, abs=1e-12)
    assert result.q09_db == pytest.approx(q09_db, abs=1e-12)
    assert result.sample_size == 25
    assert result.from_table


def test_the_order_of_the_sample_does_not_matter() -> None:
    values = np.array(ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB)
    shuffled = np.random.default_rng(17534).permutation(values)
    result = environment.level_difference_quantiles(shuffled)
    np.testing.assert_array_equal(result.sorted_differences_db, values)
    assert result.q01_db == pytest.approx(-1.0, abs=1e-12)
    assert result.q09_db == pytest.approx(3.0, abs=1e-12)


def test_c5_mean_and_estimated_standard_deviation() -> None:
    """The systematic deviation and the uncertainty C.5 asks for."""
    values = ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB
    result = environment.level_difference_quantiles(values)
    assert result.mean_db == pytest.approx(statistics.fmean(values), rel=1e-12)
    assert result.standard_deviation_db == pytest.approx(
        statistics.stdev(values), rel=1e-12
    )
    # 39 dB over 25 values: the example's mean is 1,56 dB.
    assert result.mean_db == pytest.approx(1.56, abs=1e-12)


def test_above_fifty_the_quantiles_follow_the_formulas() -> None:
    """With the values 0 to N - 1 the quantile is its own rank minus one."""
    n = 73
    result = environment.level_difference_quantiles(np.arange(n, dtype=float)[::-1])
    assert not result.from_table
    assert result.rank_q01 == 7
    assert result.rank_q09 == 66
    assert result.q01_db == pytest.approx(6.0)
    assert result.q09_db == pytest.approx(65.0)


def test_the_sample_is_a_read_only_copy() -> None:
    values = np.array(ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB)
    result = environment.level_difference_quantiles(values)
    values[0] = 99.0
    assert result.sorted_differences_db[0] == pytest.approx(-1.4)
    assert not result.sorted_differences_db.flags.writeable


def test_fewer_than_twenty_differences_are_refused() -> None:
    values = ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB[:19]
    with pytest.raises(ValueError, match="at least 20"):
        environment.level_difference_quantiles(values)


def test_a_non_finite_difference_is_refused() -> None:
    values = [*ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB[:24], math.nan]
    with pytest.raises(ValueError, match="level_differences_db"):
        environment.level_difference_quantiles(values)


def test_a_matrix_of_differences_is_refused() -> None:
    values = np.zeros((5, 5))
    with pytest.raises(ValueError, match="level_differences_db"):
        environment.level_difference_quantiles(values)


def test_the_result_refuses_fewer_than_twenty_differences() -> None:
    """The result keeps its own guard, which the function never reaches."""
    with pytest.raises(ValueError, match="at least 20"):
        environment.LevelDifferenceQuantiles(sorted_differences_db=np.arange(19.0))


def test_an_unsorted_sample_is_refused_by_the_result() -> None:
    values = np.array(ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB)[::-1]
    with pytest.raises(ValueError, match="ascending"):
        environment.LevelDifferenceQuantiles(sorted_differences_db=values)


# --------------------------------------------------------------------------- #
# C.2 and C.3: where the sample is taken
# --------------------------------------------------------------------------- #


def _ordinals(n: int, m: int) -> list[int]:
    """IP((i - 0,5) N / M) as C.2 writes it, in exact rational arithmetic."""
    from fractions import Fraction

    return [
        math.floor((Fraction(2 * i - 1, 2)) * Fraction(n, m)) for i in range(1, m + 1)
    ]


@pytest.mark.parametrize(
    ("n", "m"), [(300, 20), (2000, 20), (4567, 45), (20, 20), (39, 20)]
)
def test_uniform_sample_indices_are_the_ordinals_of_c2(n: int, m: int) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", environment.SoftwareQualityWarning)
        indices = environment.uniform_sample_indices(n, m)
    assert indices.tolist() == _ordinals(n, m)
    assert len(set(indices.tolist())) == m
    assert indices.min() >= 0
    assert indices.max() <= n - 1


def test_the_points_near_a_source_or_obstacle_are_left_out_first() -> None:
    clearances = np.full(60, 5.0)
    clearances[::3] = 1.9
    clearances[1] = 2.0
    indices = environment.uniform_sample_indices(
        60, 20, horizontal_clearances_m=clearances
    )
    eligible = np.flatnonzero(clearances >= 2.0)
    assert eligible.size == 40
    assert indices.tolist() == eligible[_ordinals(40, 20)].tolist()
    assert np.all(clearances[indices] >= 2.0)


def test_a_point_exactly_two_metres_away_is_kept() -> None:
    """C.2 leaves out the points at "less than 2 m", so one at 2,0 m stays.

    Twenty points and a sample of twenty: the sample takes every point, which
    it can only do if the point at 2,0 m is still among them.
    """
    clearances = np.full(20, 5.0)
    clearances[7] = 2.0
    indices = environment.uniform_sample_indices(
        20, 20, horizontal_clearances_m=clearances
    )
    assert indices.tolist() == list(range(20))


def test_a_sample_thinner_than_one_in_a_hundred_warns() -> None:
    with pytest.warns(environment.SoftwareQualityWarning, match="1:100"):
        environment.uniform_sample_indices(2001, 20)


def test_a_sample_of_one_in_a_hundred_does_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", environment.SoftwareQualityWarning)
        indices = environment.uniform_sample_indices(2000, 20)
    assert indices.size == 20


def test_a_sample_larger_than_the_points_left_is_refused() -> None:
    clearances = np.full(30, 1.0)
    clearances[:19] = 3.0
    with pytest.raises(ValueError, match="19 single points"):
        environment.uniform_sample_indices(30, 20, horizontal_clearances_m=clearances)


def test_a_sample_below_twenty_is_refused() -> None:
    with pytest.raises(ValueError, match="sample_size"):
        environment.uniform_sample_indices(1000, 19)


def test_one_clearance_per_point_is_required() -> None:
    clearances = np.full(10, 3.0)
    with pytest.raises(ValueError, match="one distance per point"):
        environment.uniform_sample_indices(30, 20, horizontal_clearances_m=clearances)


def test_a_negative_clearance_is_refused() -> None:
    clearances = np.full(30, 3.0)
    clearances[4] = -1.0
    with pytest.raises(ValueError, match="negative"):
        environment.uniform_sample_indices(30, 20, horizontal_clearances_m=clearances)


def test_contour_chainages_are_those_of_c3_in_whole_metres() -> None:
    chainages = environment.contour_sample_chainages_m(1234.5, 20)
    expected = [math.floor((i - 0.5) * 1234.5 / 20) for i in range(1, 21)]
    assert chainages.tolist() == expected
    assert chainages[0] == 30.0
    assert np.all(np.diff(chainages) > 0.0)


def _c3_chainages(length: Fraction, size: int) -> list[int]:
    """IP((i - 0,5) x (L/M)) of C.3, term by term in exact arithmetic."""
    return [
        math.floor((i - Fraction(1, 2)) * (length / size)) for i in range(1, size + 1)
    ]


def test_a_whole_metre_chainage_is_not_put_a_metre_short() -> None:
    """IP(12,5 x 184/20) is IP(115) = 115, which the rounded quotient 9,2 puts at 114."""
    chainages = environment.contour_sample_chainages_m(184.0, 20)
    assert chainages[12] == 115.0
    assert chainages.tolist() == _c3_chainages(Fraction(184), 20)


@pytest.mark.parametrize(("length", "size"), [(328, 20), (10000, 120), (184, 20)])
def test_c3_is_exact_on_the_lengths_a_rounded_quotient_gets_wrong(
    length: int, size: int
) -> None:
    chainages = environment.contour_sample_chainages_m(float(length), size)
    assert chainages.tolist() == _c3_chainages(Fraction(length), size)


def test_c3_is_exact_for_every_whole_metre_length() -> None:
    for size in (20, 23, 50, 64):
        for length in range(size, 1500):
            chainages = environment.contour_sample_chainages_m(float(length), size)
            assert chainages.tolist() == _c3_chainages(Fraction(length), size), length


@pytest.mark.parametrize(
    ("length", "size", "point", "chainage"),
    [(22.4, 20, 12, 14.0), (38.4, 24, 2, 4.0), (44.8, 24, 22, 42.0)],
)
def test_c3_reads_a_decimal_length_as_written(
    length: float, size: int, point: int, chainage: float
) -> None:
    """12,5 x 22,4/20 is 14 exactly; the binary fraction nearest 22,4 is a hair below."""
    chainages = environment.contour_sample_chainages_m(length, size)
    assert chainages[point] == chainage
    assert chainages.tolist() == _c3_chainages(Fraction(str(length)), size)


def test_contours_one_metre_per_point_long_are_sampled_at_every_metre() -> None:
    """From L = M on, every point has a whole metre of its own."""
    chainages = environment.contour_sample_chainages_m(20.0, 20)
    np.testing.assert_array_equal(chainages, np.arange(20.0))


@pytest.mark.parametrize("length", [19.5, 19.49])
def test_contours_a_little_shorter_than_one_metre_per_point_are_sampled(
    length: float,
) -> None:
    """Down to 2M(M - 1)/(2M - 1) = 760/39 m, 20 points still fall on 20 metres."""
    chainages = environment.contour_sample_chainages_m(length, 20)
    np.testing.assert_array_equal(chainages, np.arange(20.0))


@pytest.mark.parametrize("length", [19.48, 19.0, 10.0])
def test_contours_on_which_two_points_share_a_metre_are_refused(length: float) -> None:
    with pytest.raises(ValueError, match="same whole metre"):
        environment.contour_sample_chainages_m(length, 20)


@pytest.mark.parametrize("bad", [0.0, -10.0, math.inf, math.nan])
def test_the_contour_length_must_be_finite_and_positive(bad: float) -> None:
    with pytest.raises(ValueError, match="total_length_m"):
        environment.contour_sample_chainages_m(bad, 20)


@pytest.mark.parametrize("bad", ["100", b"100", True], ids=["str", "bytes", "bool"])
def test_the_contour_length_must_be_a_number(bad: object) -> None:
    """A string or a bool converts through float() and would pass for a length."""
    with pytest.raises(ValueError, match="total_length_m"):
        environment.contour_sample_chainages_m(bad, 20)  # type: ignore[arg-type]


@pytest.mark.parametrize("length", [100, np.float64(100.0), np.int64(100)])
def test_an_integer_or_a_numpy_length_is_a_length(length: object) -> None:
    np.testing.assert_array_equal(
        environment.contour_sample_chainages_m(length, 20),  # type: ignore[arg-type]
        environment.contour_sample_chainages_m(100.0, 20),
    )


# --------------------------------------------------------------------------- #
# 4.5.2 and A.3: the round robin
# --------------------------------------------------------------------------- #


def _round_robin_levels() -> np.ndarray:
    """Forty receivers, four programs, each receiver's spread set by hand."""
    base = np.linspace(40.0, 70.0, 40)
    spread = np.linspace(0.05, 2.0, 40)
    offsets = np.array([-1.0, -0.2, 0.2, 1.0])
    return base[:, None] + spread[:, None] * offsets[None, :]


def test_round_robin_deviations_are_from_the_arithmetic_mean() -> None:
    levels = _round_robin_levels()
    result = environment.round_robin_precision(levels)
    np.testing.assert_allclose(result.mean_levels_db, np.linspace(40.0, 70.0, 40))
    np.testing.assert_allclose(
        result.deviations_db, levels - levels.mean(axis=1)[:, None]
    )
    np.testing.assert_allclose(result.max_abs_deviations_db, np.linspace(0.05, 2.0, 40))
    assert result.receivers == 40
    assert result.participants == 4


def test_round_robin_result_is_the_q09_of_the_largest_deviations() -> None:
    result = environment.round_robin_precision(_round_robin_levels())
    # Table C.1 for 40 receivers: R(q0,9) = 37.
    assert result.rank_q09 == 37
    assert result.q09_db == pytest.approx(np.linspace(0.05, 2.0, 40)[36])


def test_the_mean_is_not_an_energetic_average() -> None:
    levels = np.tile([50.0, 60.0], (20, 1))
    result = environment.round_robin_precision(levels)
    np.testing.assert_allclose(result.mean_levels_db, 55.0)
    assert result.q09_db == pytest.approx(5.0)


def test_the_largest_deviation_is_absolute_and_from_the_arithmetic_mean() -> None:
    """4.5.2 and A.3: |dL_n|max, the largest absolute deviation from the mean.

    Levels of 50, 54, 54 and 54 dB have the arithmetic mean 53 dB, and the
    largest absolute deviation is the 3 dB of the one program below it. The
    largest signed deviation would be 1 dB, and deviations from the median
    (54 dB) would give 4 dB.
    """
    levels = np.tile([50.0, 54.0, 54.0, 54.0], (20, 1))
    result = environment.round_robin_precision(levels)
    np.testing.assert_allclose(result.mean_levels_db, 53.0)
    np.testing.assert_allclose(result.max_abs_deviations_db, 3.0)
    assert result.q09_db == pytest.approx(3.0)


def test_round_robin_levels_are_a_read_only_copy() -> None:
    levels = _round_robin_levels()
    result = environment.round_robin_precision(levels)
    levels[0, 0] = 0.0
    assert result.levels_db[0, 0] == pytest.approx(39.95)
    assert not result.levels_db.flags.writeable


def test_a_round_robin_needs_twenty_receivers() -> None:
    levels = np.zeros((19, 3))
    with pytest.raises(ValueError, match="19 receivers"):
        environment.round_robin_precision(levels)


def test_a_round_robin_needs_two_participants() -> None:
    levels = np.zeros((25, 1))
    with pytest.raises(ValueError, match="1 participants"):
        environment.round_robin_precision(levels)


def test_a_round_robin_needs_a_matrix() -> None:
    levels = np.zeros(40)
    with pytest.raises(ValueError, match="two-dimensional"):
        environment.round_robin_precision(levels)


def test_a_round_robin_refuses_complex_levels() -> None:
    """A float64 cast would keep the real part and only warn."""
    levels = np.ones((20, 2)) * (1.0 + 1.0j)
    with pytest.raises(ValueError, match="levels_db"):
        environment.round_robin_precision(levels)
    with pytest.raises(ValueError, match="levels_db"):
        environment.RoundRobinPrecision(levels_db=levels)


@pytest.mark.parametrize(
    "bad",
    [[[50.0, 51.0], [52.0]] * 10, [["a", "b"]] * 20],
    ids=["ragged", "strings"],
)
def test_a_round_robin_names_the_levels_it_cannot_read(bad: object) -> None:
    with pytest.raises(ValueError, match="levels_db"):
        environment.round_robin_precision(bad)  # type: ignore[arg-type]


def test_a_round_robin_refuses_a_non_finite_level() -> None:
    levels = np.zeros((25, 3))
    levels[4, 1] = np.nan
    with pytest.raises(ValueError, match="finite"):
        environment.round_robin_precision(levels)


# --------------------------------------------------------------------------- #
# 7.1 and Annex B: the TRC form
# --------------------------------------------------------------------------- #


def _table_b2() -> environment.CalculationVerification:
    rows = ref.ISO17534_1_TABLE_B2
    return environment.verify_calculation_results(
        [row[3] for row in rows],
        [row[2] for row in rows],
        [row[1] for row in rows],
        labels=[row[0] for row in rows],
    )


def test_every_row_of_table_b2_is_inside_its_tolerances() -> None:
    result = _table_b2()
    assert result.inside == (True,) * 9
    assert result.passes
    assert result.failing_labels == ()
    assert result.labels[-1] == "Total"


def test_the_limits_of_table_b2_are_the_certified_result_plus_minus_the_tolerance() -> (
    None
):
    for _, upper, lower, _ in ref.ISO17534_1_TABLE_B2:
        assert upper - lower == pytest.approx(
            2 * environment.CERTIFIED_RESULT_TOLERANCE_DB
        )


def test_a_result_on_a_limit_is_inside() -> None:
    """A deviation that reaches the tolerance does not exceed it, even in floating point."""
    certified = 13.70
    tol = environment.CERTIFIED_RESULT_TOLERANCE_DB
    result = environment.verify_calculation_results(
        [certified - tol, certified + tol],
        [certified - tol] * 2,
        [certified + tol] * 2,
    )
    assert result.inside == (True, True)
    np.testing.assert_allclose(result.margins_db, 0.0, atol=1e-12)


@pytest.mark.parametrize(
    ("result_db", "lower_db", "upper_db"),
    [(13.70 - 0.05, 13.65, 13.75), (21.10 + 0.05, 21.05, 21.15)],
)
def test_a_result_formed_on_a_printed_limit_is_inside(
    result_db: float, lower_db: float, upper_db: float
) -> None:
    """A certified result plus or minus 0,05 dB lands on the printed limit.

    In floating point 13,70 - 0,05 falls a last bit below 13,65, and
    21,10 + 0,05 a last bit above 21,15; both reach the tolerance and do not
    exceed it.
    """
    assert result_db < lower_db or result_db > upper_db
    verdict = environment.verify_calculation_results(
        [result_db], [lower_db], [upper_db]
    )
    assert verdict.inside == (True,)


def test_table_69_of_iso_tr_17534_3_fails_only_at_250_hz() -> None:
    """The worked TRC form of ISO/TR 17534-3 answers "yes" in every row.

    Its 250 Hz result, 31,0 dB, lies 0,05 dB below the lower limit 31,05 dB,
    which docs/ERRATA.md records; the 1 000 Hz result sits on its lower limit
    and is inside.
    """
    rows = ref.ISO17534_3_TABLE_69
    result = environment.verify_calculation_results(
        [row[3] for row in rows],
        [row[2] for row in rows],
        [row[1] for row in rows],
        labels=[row[0] for row in rows],
    )
    assert result.failing_labels == ("250 Hz",)
    assert result.inside == (True, True, False, True, True, True, True, True, True)
    assert result.margins_db[2] == pytest.approx(-0.05)
    assert result.margins_db[4] == pytest.approx(0.0, abs=1e-12)


def test_a_result_outside_its_limits_fails_the_form() -> None:
    rows = ref.ISO17534_1_TABLE_B2
    results = [row[3] for row in rows]
    results[2] = 21.17
    result = environment.verify_calculation_results(
        results,
        [row[2] for row in rows],
        [row[1] for row in rows],
        labels=[row[0] for row in rows],
    )
    assert not result.passes
    assert result.failing_labels == ("250 Hz",)
    assert result.margins_db[2] == pytest.approx(-0.02)
    assert result.deviations_db[2] == pytest.approx(0.07)


def test_the_verdict_has_no_truth_value() -> None:
    result = _table_b2()
    with pytest.raises(TypeError, match="passes"):
        bool(result)


def test_rows_are_numbered_when_not_named() -> None:
    result = environment.verify_calculation_results([1.0, 2.0], [0.9, 1.9], [1.1, 2.1])
    assert result.labels == ("1", "2")


def test_the_three_columns_must_have_one_value_per_row() -> None:
    results = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError, match="one value per row"):
        environment.verify_calculation_results(results, [0.9, 1.9], [1.1, 2.1])


def test_a_lower_limit_above_its_upper_limit_is_refused() -> None:
    results = [1.0]
    with pytest.raises(ValueError, match="lower limit"):
        environment.verify_calculation_results(results, [1.2], [1.1])


def test_every_row_must_be_named_once() -> None:
    results = [1.0, 2.0]
    with pytest.raises(ValueError, match="labels"):
        environment.verify_calculation_results(
            results, [0.9, 1.9], [1.1, 2.1], labels=["only one"]
        )


def test_the_columns_are_read_only_copies() -> None:
    results = np.array([1.0, 2.0])
    verdict = environment.verify_calculation_results(results, [0.9, 1.9], [1.1, 2.1])
    results[0] = 5.0
    assert verdict.results_db[0] == pytest.approx(1.0)
    assert not verdict.results_db.flags.writeable


def test_the_module_publishes_its_names_through_environment() -> None:
    for name in sq.__all__:
        assert getattr(environment, name) is getattr(sq, name)


# --------------------------------------------------------------------------- #
# The figures each result draws
# --------------------------------------------------------------------------- #


def _legend_texts(ax: plt.Axes) -> list[str]:
    legend = ax.get_legend()
    assert legend is not None
    return [text.get_text() for text in legend.get_texts()]


def test_the_quantiles_plot_marks_both_ranks_and_values() -> None:
    result = environment.level_difference_quantiles(
        ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB
    )
    ax = result.plot()
    labels = _legend_texts(ax)
    assert any("$q_{0,1}$ = −1.00 dB" in label and "= 2" in label for label in labels)
    assert any("$q_{0,9}$ = 3.00 dB" in label and "= 24" in label for label in labels)
    assert "25 level differences" in ax.get_title()
    plt.close("all")


def test_the_quantiles_plot_speaks_spanish() -> None:
    result = environment.level_difference_quantiles(
        ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB
    )
    ax = result.plot(language="es")
    labels = _legend_texts(ax)
    assert any("−1,00 dB en $R$ = 2" in label for label in labels)
    assert "diferencias de nivel" in ax.get_title()
    assert ax.get_xlabel() == "Posición en la ordenación $R$"
    plt.close("all")


def test_the_round_robin_plot_counts_every_receiver() -> None:
    result = environment.round_robin_precision(_round_robin_levels())
    ax = result.plot()
    heights = [patch.get_height() for patch in ax.patches]
    assert sum(heights) == 40
    assert "4 programs at 40 receivers" in ax.get_title()
    assert any(label.startswith("$q_{0,9}$") for label in _legend_texts(ax))
    plt.close("all")


def test_the_verification_plot_crosses_out_a_failing_row() -> None:
    rows = ref.ISO17534_1_TABLE_B2
    results = [row[3] for row in rows]
    results[0] = 13.8
    verdict = environment.verify_calculation_results(
        results,
        [row[2] for row in rows],
        [row[1] for row in rows],
        labels=[row[0] for row in rows],
    )
    ax = verdict.plot()
    assert "Outside the limits" in _legend_texts(ax)
    assert "8 of 9 results inside" in ax.get_title()
    assert [tick.get_text() for tick in ax.get_xticklabels()][0] == "63 Hz"
    plt.close("all")


def test_the_verification_plot_in_spanish_has_no_cross_when_all_pass() -> None:
    ax = _table_b2().plot(language="es")
    labels = _legend_texts(ax)
    assert "Fuera de los límites" not in labels
    assert "Intervalo certificado" in labels
    assert "9 de 9 resultados dentro" in ax.get_title()
    plt.close("all")
