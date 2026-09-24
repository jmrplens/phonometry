#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tests for :mod:`phonometry.environment.assessment.soundscape` (ISO/TS 12913).

ISO/TS 12913-3:2019 prints no worked example, so the oracles are closed
forms: every attribute at the same score puts a respondent at the origin of
Figure A.1, the extremes of the scales at :math:`\pm(4 + \sqrt{32})`, and one
attribute raised alone along its own axis of the figure; Spearman's
coefficient without ties is Pearson's of the ranks, and with ties Formula
(A.4) is checked against :func:`scipy.stats.spearmanr`, Pearson's of (B.1)
and (B.2) against :func:`scipy.stats.pearsonr`. The printed values (the 9,66
of A.3, Tables A.1, B.1) come from ``reference_data``. The derived subset of
the International Soundscape Database (CC BY 4.0) is a consistency check: real
ordinal answers with heavy ties, and 26 real sites whose pleasantness falls as
their level rises.
"""

from __future__ import annotations

import dataclasses
import math
from types import MappingProxyType
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import (
    ISD_LOCATION_MEDIANS,
    ISD_REGENTS_PARK_JAPAN_ANSWERS,
    ISO12913_3_COORDINATE_RANGE_PRINTED,
    ISO12913_3_TABLE_A1_SCALE_VALUES,
    ISO12913_3_TABLE_B1_RANKS,
)
from scipy import stats

from phonometry import environment
from phonometry.environment.assessment import soundscape as sc

if TYPE_CHECKING:
    from matplotlib.axes import Axes

_ATTRIBUTES = sc.PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES
_RANGE = 4.0 + math.sqrt(32.0)


def _neutral(n: int = 1, value: float = 3.0) -> dict[str, list[float]]:
    return {name: [value] * n for name in _ATTRIBUTES}


def _isd_answers() -> np.ndarray:
    return np.array(
        [
            [np.nan if v is None else v for v in row]
            for row in ISD_REGENTS_PARK_JAPAN_ANSWERS
        ],
        dtype=float,
    )


def _isd_site_coordinates() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    medians = np.array([row[3] for row in ISD_LOCATION_MEDIANS], dtype=float)
    result = sc.pleasantness_eventfulness(
        medians, sites=[row[0] for row in ISD_LOCATION_MEDIANS]
    )
    laeq = np.array([row[4] for row in ISD_LOCATION_MEDIANS])
    n5 = np.array([row[5] for row in ISD_LOCATION_MEDIANS])
    return result.pleasantness, laeq, n5


# ---------------------------------------------------------------------------
# The questionnaire of ISO/TS 12913-2 Annex C
# ---------------------------------------------------------------------------


def test_method_a_scale_values_are_table_a1() -> None:
    """Parts 1 and 4 run 1 to 5 from the left, parts 2 and 3 run 5 to 1."""
    for part, printed in ISO12913_3_TABLE_A1_SCALE_VALUES.items():
        assert sc.METHOD_A_SCALES[part].scale_values == printed
        assert len(sc.METHOD_A_SCALES[part].categories) == len(printed)
    assert (
        sc.METHOD_A_ALTERNATIVE_PART_1.scale_values
        == ISO12913_3_TABLE_A1_SCALE_VALUES[1]
    )


def test_method_a_categories_are_the_printed_ones() -> None:
    """The end categories A.2 names, at the ends A.2 puts them."""
    assert sc.METHOD_A_SCALES[1].categories[0] == "Not at all"
    assert sc.METHOD_A_SCALES[1].categories[-1] == "Dominates completely"
    assert sc.METHOD_A_SCALES[2].categories[0] == "Strongly agree"
    assert sc.METHOD_A_SCALES[2].categories[-1] == "Strongly disagree"
    assert sc.METHOD_A_SCALES[3].categories[0] == "Very good"
    assert sc.METHOD_A_SCALES[3].categories[-1] == "Very bad"
    assert sc.METHOD_A_SCALES[4].categories[0] == "Not at all"
    assert sc.METHOD_A_SCALES[4].categories[-1] == "Perfectly"
    assert sc.METHOD_A_SCALES[2].items == _ATTRIBUTES
    assert len(sc.METHOD_A_SCALES[1].items) == 4
    assert len(sc.METHOD_A_ALTERNATIVE_PART_1.items) == 3


def test_attribute_order_is_figure_c4() -> None:
    assert _ATTRIBUTES == (
        "pleasant",
        "chaotic",
        "vibrant",
        "uneventful",
        "calm",
        "annoying",
        "eventful",
        "monotonous",
    )


def test_method_b_scales_are_figure_c7() -> None:
    """Four scales, as the figure prints them, all 1 to 5 (Table B.1)."""
    assert len(sc.METHOD_B_SCALES) == 4
    assert all(scale.continuous for scale in sc.METHOD_B_SCALES)
    assert all(scale.scale_values == (1, 2, 3, 4, 5) for scale in sc.METHOD_B_SCALES)
    assert sc.METHOD_B_SCALES[0].categories == (
        "not at all",
        "slightly",
        "moderately",
        "very",
        "extremely",
    )
    assert sc.METHOD_B_SCALES[3].categories[0] == "never"
    assert sc.METHOD_B_MAXIMUM_SOURCES == max(ISO12913_3_TABLE_B1_RANKS)


def test_published_tables_are_read_only() -> None:
    assert isinstance(sc.METHOD_A_SCALES, MappingProxyType)
    with pytest.raises(TypeError, match="does not support item assignment"):
        sc.METHOD_A_SCALES[5] = sc.METHOD_A_SCALES[1]  # type: ignore[index]
    scale = sc.METHOD_A_SCALES[2]
    with pytest.raises(dataclasses.FrozenInstanceError, match="question"):
        scale.question = "?"  # type: ignore[misc]


def test_questionnaire_misprints_are_transcribed() -> None:
    """The figures print "extend" and "reponse"; the table keeps them."""
    assert "To what extend" in sc.METHOD_A_SCALES[1].question
    assert "reponse" in sc.METHOD_A_SCALES[2].instruction
    assert "to what extent" in sc.METHOD_A_SCALES[4].question


# ---------------------------------------------------------------------------
# Method A: scale values, median and range
# ---------------------------------------------------------------------------


def test_scale_values_from_box_positions() -> None:
    positions = [1, 2, 3, 4, 5]
    np.testing.assert_array_equal(
        sc.method_a_scale_values(positions, part=1), [1, 2, 3, 4, 5]
    )
    np.testing.assert_array_equal(
        sc.method_a_scale_values(positions, part=2), [5, 4, 3, 2, 1]
    )
    np.testing.assert_array_equal(
        sc.method_a_scale_values(positions, part=3), [5, 4, 3, 2, 1]
    )
    np.testing.assert_array_equal(
        sc.method_a_scale_values(positions, part=4), [1, 2, 3, 4, 5]
    )
    assert sc.method_a_scale_values(1, part=2) == 5.0
    assert math.isnan(float(sc.method_a_scale_values([np.nan], part=2)[0]))


@pytest.mark.parametrize("part", [0, 5, True])
def test_scale_values_refuse_an_unknown_part(part: int) -> None:
    with pytest.raises(ValueError, match="'part'"):
        sc.method_a_scale_values([1], part=part)


@pytest.mark.parametrize("position", [0, 6, 2.5, np.inf])
def test_scale_values_refuse_a_position_off_the_scale(position: float) -> None:
    with pytest.raises(ValueError, match="'positions'"):
        sc.method_a_scale_values([position], part=1)


def test_method_a_summary_median_and_range_per_site() -> None:
    summary = sc.method_a_summary(
        {"pleasant": [5, 4, 4, 2], "calm": [3, 3, np.nan, 1]},
        part=2,
        sites=["a", "a", "b", "b"],
    )
    assert summary.sites == ("a", "b")
    assert summary.items == ("pleasant", "calm")
    np.testing.assert_array_equal(summary.medians, [[4.5, 3.0], [3.0, 1.0]])
    np.testing.assert_array_equal(summary.ranges, [[1.0, 0.0], [2.0, 0.0]])
    np.testing.assert_array_equal(summary.counts, [[2, 2], [2, 1]])
    assert not summary.medians.flags.writeable


def test_method_a_summary_takes_the_figure_columns() -> None:
    """Four columns for Figure C.2, three for Figure C.3, one for part 3."""
    four = sc.method_a_summary(np.full((3, 4), 2), part=1)
    assert four.items == sc.METHOD_A_SCALES[1].items
    three = sc.method_a_summary(np.full((3, 3), 2), part=1)
    assert three.items == sc.METHOD_A_ALTERNATIVE_PART_1.items
    single = sc.method_a_summary([5, 4, 4], part=3)
    assert single.items == (sc.METHOD_A_SCALES[3].subject,)
    assert single.medians[0, 0] == 4.0
    assert single.sites == ("all",)


def test_method_a_summary_refuses_a_column_count_the_part_has_not() -> None:
    values = np.full((3, 5), 2)
    with pytest.raises(ValueError, match="columns"):
        sc.method_a_summary(values, part=1)


def test_method_a_summary_refuses_sites_of_another_length() -> None:
    values = [1, 2, 3]
    with pytest.raises(ValueError, match="'sites'"):
        sc.method_a_summary(values, part=3, sites=["a", "b"])


def test_method_a_summary_refuses_a_value_between_boxes() -> None:
    values = [1.5, 2.0]
    with pytest.raises(ValueError, match="whole scale values"):
        sc.method_a_summary(values, part=4)


# ---------------------------------------------------------------------------
# Formulas (A.1) and (A.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("score", [1.0, 2.0, 3.0, 4.0, 5.0])
def test_equal_scores_sit_at_the_origin(score: float) -> None:
    """Every attribute at one score cancels in both formulas: P = E = 0."""
    result = sc.pleasantness_eventfulness(_neutral(2, score))
    assert result.pleasantness[0] == pytest.approx(0.0, abs=1e-12)
    assert result.eventfulness[0] == pytest.approx(0.0, abs=1e-12)
    np.testing.assert_allclose(result.respondent_pleasantness, 0.0, atol=1e-12)


def test_the_extremes_are_the_printed_range() -> None:
    """Pleasant, calm, vibrant at 5 and their opposites at 1 give 4 + sqrt(32)."""
    most = _neutral()
    for name in ("pleasant", "calm", "vibrant"):
        most[name] = [5]
    for name in ("annoying", "chaotic", "monotonous"):
        most[name] = [1]
    result = sc.pleasantness_eventfulness(most)
    assert result.pleasantness[0] == pytest.approx(_RANGE, rel=1e-12)
    assert result.pleasantness[0] == pytest.approx(
        ISO12913_3_COORDINATE_RANGE_PRINTED, abs=0.005
    )
    assert result.normalized_pleasantness[0] == pytest.approx(1.0, rel=1e-12)
    least = {name: [6 - values[0]] for name, values in most.items()}
    assert sc.pleasantness_eventfulness(least).pleasantness[0] == pytest.approx(-_RANGE)


def test_the_eventfulness_extremes() -> None:
    most = _neutral()
    for name in ("eventful", "chaotic", "vibrant"):
        most[name] = [5]
    for name in ("uneventful", "calm", "monotonous"):
        most[name] = [1]
    result = sc.pleasantness_eventfulness(most)
    assert result.eventfulness[0] == pytest.approx(_RANGE, rel=1e-12)
    assert result.normalized_eventfulness[0] == pytest.approx(1.0, rel=1e-12)
    assert sc.PLEASANTNESS_EVENTFULNESS_RANGE == pytest.approx(_RANGE, rel=1e-15)


@pytest.mark.parametrize(
    ("attribute", "angle_deg"),
    [
        ("pleasant", 0.0),
        ("vibrant", 45.0),
        ("eventful", 90.0),
        ("chaotic", 135.0),
        ("annoying", 180.0),
        ("monotonous", 225.0),
        ("uneventful", 270.0),
        ("calm", 315.0),
    ],
)
def test_one_attribute_raised_points_along_its_axis(
    attribute: str, angle_deg: float
) -> None:
    """Figure A.1: each attribute raised alone moves the point along its arrow.

    The main axes carry a weight of 1 and the diagonal ones cos 45 degrees on
    each coordinate, so the displacement is 2 along the axis in both cases.
    """
    answers = _neutral()
    answers[attribute] = [5]
    result = sc.pleasantness_eventfulness(answers)
    p, e = result.pleasantness[0], result.eventfulness[0]
    assert math.hypot(p, e) == pytest.approx(2.0, rel=1e-12)
    assert math.degrees(math.atan2(e, p)) % 360.0 == pytest.approx(angle_deg, abs=1e-9)


def test_site_coordinates_come_from_the_site_medians() -> None:
    """A.2 makes the median the central tendency; the formulas then apply."""
    answers = _isd_answers()
    result = sc.pleasantness_eventfulness(answers)
    medians = np.nanmedian(answers, axis=0)
    p, ch, v, u, ca, a, e, m = medians
    c = math.cos(math.radians(45.0))
    assert result.pleasantness[0] == pytest.approx(
        (p - a) + c * (ca - ch) + c * (v - m)
    )
    assert result.eventfulness[0] == pytest.approx(
        (e - u) + c * (ch - ca) + c * (v - m)
    )
    np.testing.assert_array_equal(result.attribute_values[0], medians)


def test_mean_central_tendency_is_the_mean_of_the_respondents() -> None:
    """With every attribute answered, the formulas being linear, the site
    point of the means is the mean of the respondents' points.
    """
    answers = _isd_answers()
    complete = answers[~np.isnan(answers).any(axis=1)]
    result = sc.pleasantness_eventfulness(complete, central_tendency="mean")
    assert result.pleasantness[0] == pytest.approx(
        float(np.mean(result.respondent_pleasantness))
    )
    assert result.eventfulness[0] == pytest.approx(
        float(np.mean(result.respondent_eventfulness))
    )


def test_a_blank_answer_parts_the_mean_point_from_the_mean_of_respondents() -> None:
    """A blank makes each attribute mean run over its own set of respondents.

    The site point is then not the mean of the respondents' points, which is
    why the docstrings state the equality only for complete answers. The ISD
    subset has two rows with a blank.
    """
    answers = _isd_answers()
    assert np.isnan(answers).any(axis=1).sum() == 2
    result = sc.pleasantness_eventfulness(answers, central_tendency="mean")
    respondents_p = float(np.nanmean(result.respondent_pleasantness))
    means = np.nanmean(answers, axis=0)
    p, ch, v, _u, ca, a, _e, m = means
    c = math.cos(math.radians(45.0))
    assert result.pleasantness[0] == pytest.approx(
        (p - a) + c * (ca - ch) + c * (v - m)
    )
    assert abs(result.pleasantness[0] - respondents_p) > 0.01


def test_a_blank_answer_leaves_the_respondent_out() -> None:
    """A blank leaves out the coordinate whose formula reads that attribute.

    Formula (A.1) does not read eventful or uneventful, so a respondent who
    left one of those blank still has a pleasantness; the count per site is
    of the respondents who answered all eight.
    """
    answers = _isd_answers()
    result = sc.pleasantness_eventfulness(answers)
    blank = np.isnan(answers).any(axis=1)
    assert result.respondent_counts[0] == int(np.sum(~blank))
    reads_p = [0, 1, 2, 4, 5, 7]  # p, ch, v, ca, a, m
    reads_e = [1, 2, 3, 4, 6, 7]  # ch, v, u, ca, e, m
    np.testing.assert_array_equal(
        np.isnan(result.respondent_pleasantness),
        np.isnan(answers[:, reads_p]).any(axis=1),
    )
    np.testing.assert_array_equal(
        np.isnan(result.respondent_eventfulness),
        np.isnan(answers[:, reads_e]).any(axis=1),
    )
    assert result.respondent_sites == ("all",) * answers.shape[0]


def test_pleasantness_eventfulness_refuses_a_missing_attribute() -> None:
    answers = _neutral()
    del answers["calm"]
    with pytest.raises(ValueError, match="eight attributes"):
        sc.pleasantness_eventfulness(answers)


def test_pleasantness_eventfulness_refuses_an_array_of_other_width() -> None:
    answers = np.full((4, 7), 3)
    with pytest.raises(ValueError, match="columns"):
        sc.pleasantness_eventfulness(answers)


def test_pleasantness_eventfulness_refuses_an_unknown_central_tendency() -> None:
    answers = _neutral()
    with pytest.raises(ValueError, match="central_tendency"):
        sc.pleasantness_eventfulness(answers, central_tendency="mode")  # type: ignore[arg-type]


def test_isd_sites_fall_in_pleasantness_as_their_level_rises() -> None:
    """Consistency, not calibration: 26 real sites, P against their LAeq and N5.

    The louder sites of the database are the less pleasant ones: the rank
    correlation of the site pleasantness with the median LAeq of the site's
    recordings is about -0.51 (p < 0.01), and with N5 about -0.55.
    """
    pleasantness, laeq, n5 = _isd_site_coordinates()
    with_level = sc.spearman_rank_correlation(pleasantness, laeq)
    with_loudness = sc.spearman_rank_correlation(pleasantness, n5)
    assert with_level.coefficient < -0.4
    assert with_level.p_value < 0.01
    assert with_loudness.coefficient < -0.4
    reference = stats.spearmanr(pleasantness, laeq)
    assert with_level.coefficient == pytest.approx(reference.statistic, rel=1e-12)
    assert with_level.p_value == pytest.approx(reference.pvalue, rel=1e-9)


def test_isd_calmest_site_is_pleasant_and_uneventful() -> None:
    """Regent's Park Japanese Garden sits in the calm quadrant of Figure A.1."""
    result = sc.pleasantness_eventfulness(_isd_answers())
    assert result.pleasantness[0] > 0.0
    assert result.eventfulness[0] < 0.0


# ---------------------------------------------------------------------------
# Correlation: Formulas (A.3), (A.4), (B.1), (B.2)
# ---------------------------------------------------------------------------


def test_spearman_without_ties_is_pearson_of_the_ranks() -> None:
    rng = np.random.default_rng(12913)
    x = rng.normal(size=25)
    y = x + rng.normal(size=25)
    result = sc.spearman_rank_correlation(x, y)
    assert result.formula == "(A.3)"
    ranks_x, ranks_y = stats.rankdata(x), stats.rankdata(y)
    assert result.coefficient == pytest.approx(
        float(np.corrcoef(ranks_x, ranks_y)[0, 1]), rel=1e-12
    )
    reference = stats.spearmanr(x, y)
    assert result.coefficient == pytest.approx(reference.statistic, rel=1e-12)
    assert result.p_value == pytest.approx(reference.pvalue, rel=1e-9)


def test_spearman_with_ties_is_formula_a4() -> None:
    """Formula (A.4) on real ordinal answers against scipy's average-rank Pearson."""
    answers = _isd_answers()
    rows = ~np.isnan(answers[:, 0]) & ~np.isnan(answers[:, 5])
    pleasant, annoying = answers[rows, 0], answers[rows, 5]
    result = sc.spearman_rank_correlation(pleasant, annoying)
    assert result.formula == "(A.4)"
    reference = stats.spearmanr(pleasant, annoying)
    assert result.coefficient == pytest.approx(reference.statistic, rel=1e-12)
    assert result.p_value == pytest.approx(reference.pvalue, rel=1e-9)
    assert result.coefficient < 0.0


def test_formula_a4_reduces_to_a3_without_ties() -> None:
    """T = U = 0 turns (A.4) into (A.3): both sides written out here."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 7.0, 5.0, 6.0])
    n = x.size
    d2 = float(np.sum((stats.rankdata(x) - stats.rankdata(y)) ** 2))
    base = (n**3 - n) / 12.0
    a4 = (2.0 * base - d2) / (2.0 * math.sqrt(base * base))
    a3 = 1.0 - 6.0 * d2 / (n * (n * n - 1))
    assert a4 == pytest.approx(a3, rel=1e-14)
    assert sc.spearman_rank_correlation(x, y).coefficient == pytest.approx(
        a3, rel=1e-14
    )


def test_a_monotone_pair_correlates_perfectly() -> None:
    result = sc.spearman_rank_correlation([1, 2, 3, 4], [10, 20, 30, 1000])
    assert result.coefficient == 1.0
    assert result.p_value == 0.0
    assert math.isinf(result.t_statistic)


def test_one_sided_probabilities_split_the_two_sided_one() -> None:
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    y = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0]
    both = sc.spearman_rank_correlation(x, y)
    greater = sc.spearman_rank_correlation(x, y, alternative="greater")
    less = sc.spearman_rank_correlation(x, y, alternative="less")
    assert greater.p_value == pytest.approx(0.5 * both.p_value, rel=1e-12)
    assert greater.p_value + less.p_value == pytest.approx(1.0, rel=1e-12)


def test_pearson_is_formulas_b1_and_b2() -> None:
    rng = np.random.default_rng(3)
    x = rng.uniform(1.0, 5.0, 20)
    y = 50.0 + 4.0 * x + rng.normal(scale=2.0, size=20)
    result = sc.pearson_correlation(x, y)
    reference = stats.pearsonr(x, y)
    assert result.formula == "(B.1)"
    assert result.coefficient == pytest.approx(reference.statistic, rel=1e-12)
    assert result.p_value == pytest.approx(reference.pvalue, rel=1e-9)
    assert result.x_ranks is None


def test_formula_b2_divides_by_n() -> None:
    """With (B.2) over n, sample standard deviations would shrink r by (n - 1)/n."""
    x = np.array([1.0, 2.0, 4.0, 5.0, 7.0])
    y = np.array([2.0, 1.5, 5.0, 4.5, 8.0])
    n = x.size
    covariance = float(np.sum((x - x.mean()) * (y - y.mean())) / n)
    r_population = covariance / (np.std(x) * np.std(y))
    r_sample_sd = covariance / (np.std(x, ddof=1) * np.std(y, ddof=1))
    assert sc.pearson_correlation(x, y).coefficient == pytest.approx(
        r_population, rel=1e-12
    )
    assert r_sample_sd == pytest.approx(r_population * (n - 1) / n, rel=1e-12)


def test_correlation_refuses_pairs_of_two_lengths() -> None:
    x, y = [1, 2, 3], [1, 2]
    with pytest.raises(ValueError, match="pair up"):
        sc.spearman_rank_correlation(x, y)


def test_correlation_refuses_two_pairs() -> None:
    x, y = [1, 2], [2, 1]
    with pytest.raises(ValueError, match="at least 3 pairs"):
        sc.pearson_correlation(x, y)


def test_correlation_refuses_a_constant_variable() -> None:
    x, y = [3, 3, 3, 3], [1, 2, 3, 4]
    with pytest.raises(ValueError, match="constant"):
        sc.spearman_rank_correlation(x, y)


def test_correlation_refuses_a_missing_value() -> None:
    x, y = [1.0, np.nan, 3.0, 4.0], [1, 2, 3, 4]
    with pytest.raises(ValueError, match="incomplete pairs"):
        sc.pearson_correlation(x, y)


def test_correlation_refuses_an_unknown_alternative() -> None:
    x, y = [1, 2, 3], [1, 3, 2]
    with pytest.raises(ValueError, match="alternative"):
        sc.spearman_rank_correlation(x, y, alternative="both")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Method B
# ---------------------------------------------------------------------------


def test_method_b_scale_values_run_one_to_five_to_one_decimal() -> None:
    np.testing.assert_array_equal(
        sc.method_b_scale_values([0.0, 0.25, 0.5, 1.0]), [1.0, 2.0, 3.0, 5.0]
    )
    assert sc.method_b_scale_values(0.62) == 3.5
    assert sc.method_b_scale_values(0.613) == 3.5


def test_method_b_scale_values_refuse_a_mark_off_the_scale() -> None:
    with pytest.raises(ValueError, match="marked_fraction"):
        sc.method_b_scale_values([1.2])


def test_method_b_summary_mean_sd_and_confidence_interval() -> None:
    loud = np.array([2.1, 3.4, 2.9, 3.8, 2.5, 3.0])
    summary = sc.method_b_summary({"How loud is it here?": loud})
    assert summary.means[0, 0] == pytest.approx(loud.mean())
    assert summary.standard_deviations[0, 0] == pytest.approx(np.std(loud, ddof=1))
    low, high = stats.t.interval(
        0.95, loud.size - 1, loc=loud.mean(), scale=stats.sem(loud)
    )
    assert summary.confidence_lower[0, 0] == pytest.approx(low, rel=1e-12)
    assert summary.confidence_upper[0, 0] == pytest.approx(high, rel=1e-12)
    assert summary.medians[0, 0] == pytest.approx(np.median(loud))
    assert summary.confidence_level == 0.95


def test_method_b_summary_columns_are_the_figure_c7_scales() -> None:
    summary = sc.method_b_summary(np.full((4, 4), 2.5), sites=["x", "x", "y", "y"])
    assert summary.items == tuple(s.question for s in sc.METHOD_B_SCALES)
    assert summary.sites == ("x", "y")
    three = sc.method_b_summary(np.full((2, 3), 2.5))
    assert len(three.items) == 3


def test_method_b_summary_leaves_one_answer_without_spread() -> None:
    summary = sc.method_b_summary([4.2])
    assert summary.means[0, 0] == pytest.approx(4.2)
    assert math.isnan(summary.standard_deviations[0, 0])
    assert math.isnan(summary.confidence_lower[0, 0])


def test_method_b_summary_refuses_a_confidence_level_of_one() -> None:
    values = [2.0, 3.0]
    with pytest.raises(ValueError, match="confidence_level"):
        sc.method_b_summary(values, confidence_level=1.0)


def test_source_ranking_median_and_range() -> None:
    ranking = sc.method_b_source_ranking(
        [["traffic", "birds"], ["birds", "traffic", "voices"], ["voices"], ["traffic"]],
        sites=["A", "A", "B", "B"],
    )
    assert ranking.sites == ("A", "B")
    assert ranking.sources[0] == "traffic"
    column = {name: j for j, name in enumerate(ranking.sources)}
    assert ranking.median_ranks[0, column["traffic"]] == 1.5
    assert ranking.rank_ranges[0, column["traffic"]] == 1.0
    assert ranking.lowest_ranks[0, column["birds"]] == 1.0
    assert ranking.highest_ranks[0, column["birds"]] == 2.0
    assert math.isnan(ranking.median_ranks[1, column["birds"]])
    assert ranking.mentions[1, column["birds"]] == 0
    np.testing.assert_array_equal(ranking.participants, [2, 2])


def test_source_ranking_refuses_more_than_eight_sources() -> None:
    rankings = [[f"source {k}" for k in range(9)]]
    with pytest.raises(ValueError, match="limits the list to 8"):
        sc.method_b_source_ranking(rankings)


def test_source_ranking_refuses_a_source_listed_twice() -> None:
    rankings = [["traffic", "traffic"]]
    with pytest.raises(ValueError, match="each source once"):
        sc.method_b_source_ranking(rankings)


def test_source_ranking_refuses_a_bare_string() -> None:
    rankings = "traffic"
    with pytest.raises(ValueError, match="'rankings'"):
        sc.method_b_source_ranking(rankings)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ISO/TS 12913-2 Annex A: the reporting record
# ---------------------------------------------------------------------------

_RESULTS = {
    "LAeq,T": 59.7,
    "LCeq,T": 66.1,
    "LAF5,T": 63.0,
    "LAF95,T": 52.4,
    "N5": 15.5,
    "N95": 7.9,
    "Nrmc": 11.2,
}


def _participants() -> sc.SoundscapeParticipants:
    return sc.SoundscapeParticipants(
        selection="visitors approached at the entrance",
        residents_or_visitors="visitors",
        lay_or_expert="lay people",
        age_and_gender_distribution="18 to 74 years, 52 % women",
        other_relevant_information="none",
    )


def _environment(**changes: object) -> sc.SoundscapeAcousticEnvironment:
    fields: dict[str, object] = {
        "environment_type": "real",
        "sound_sources": "birdsong, water, distant traffic",
        "weather_and_wind": "dry, light wind",
        "time_of_year_and_day": "June, 14:00 to 16:00",
        "measurement_points": "three points, artificial head at 1,6 m facing the pond",
        "measurement_results": _RESULTS,
        "site_description": "urban park, Japanese garden",
    }
    fields.update(changes)
    return sc.SoundscapeAcousticEnvironment(**fields)  # type: ignore[arg-type]


def _collection() -> sc.SoundscapeDataCollection:
    return sc.SoundscapeDataCollection(
        methods="Method A questionnaire on a soundwalk",
        questions="parts 1 to 4 of ISO/TS 12913-2 C.3.1, answers on paper",
        language="English, as printed in Annex C",
        instrument_copy="Appendix B",
        rating_scale_construction="five-point category scales of Figures C.2 to C.6",
    )


def test_a_complete_report_is_built() -> None:
    report = sc.SoundscapeReport(_participants(), _environment(), _collection())
    assert report.acoustic_environment.measurement_results["N5"] == 15.5
    assert isinstance(report.acoustic_environment.measurement_results, MappingProxyType)


def test_a_participants_item_left_empty_names_its_clause() -> None:
    with pytest.raises(ValueError, match=r"A\.2 b\)"):
        sc.SoundscapeParticipants(
            selection="random",
            residents_or_visitors="  ",
            lay_or_expert="lay",
            age_and_gender_distribution="adults",
            other_relevant_information="none",
        )


def test_a_missing_measurement_result_names_a3_f() -> None:
    results = {k: v for k, v in _RESULTS.items() if k != "Nrmc"}
    with pytest.raises(ValueError, match=r"A\.3 f\)"):
        _environment(measurement_results=results)


def test_a_non_numeric_result_is_refused() -> None:
    results = {**_RESULTS, "N5": "loud"}
    with pytest.raises(ValueError, match="'N5' must be finite"):
        _environment(measurement_results=results)


def test_a_recorded_environment_needs_its_reproduction() -> None:
    with pytest.raises(ValueError, match=r"A\.3 h\)"):
        _environment(environment_type="recorded")


def test_a_field_study_needs_its_site_description() -> None:
    with pytest.raises(ValueError, match=r"A\.3 g\)"):
        _environment(site_description=None)


def test_a_recorded_environment_needs_its_site_description() -> None:
    """A.3 g) asks it of "a study based on audio recordings" too."""
    with pytest.raises(ValueError, match=r"A\.3 g\)"):
        _environment(
            environment_type="recorded",
            site_description=None,
            recording_and_reproduction="artificial head, played on headphones",
        )


def test_a_virtual_environment_needs_no_site_description() -> None:
    record = _environment(
        environment_type="virtual",
        site_description=None,
        recording_and_reproduction="synthesized sources, played on headphones",
    )
    assert record.site_description is None


def test_an_unknown_environment_type_is_refused() -> None:
    with pytest.raises(ValueError, match="environment_type"):
        _environment(environment_type="imagined")


def test_data_collection_needs_a_copy_of_the_instrument() -> None:
    with pytest.raises(ValueError, match="copy of the instrument"):
        sc.SoundscapeDataCollection(
            methods="questionnaire",
            questions="Figure C.4",
            language="English",
            instrument_copy="",
        )


def test_a_report_refuses_a_part_of_the_wrong_kind() -> None:
    participants = _participants()
    collection = _collection()
    with pytest.raises(ValueError, match="acoustic_environment"):
        sc.SoundscapeReport(participants, "a park", collection)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Results and their plots
# ---------------------------------------------------------------------------


def test_published_arrays_of_results_are_read_only() -> None:
    result = sc.pleasantness_eventfulness(_isd_answers())
    for name in (
        "attribute_values",
        "pleasantness",
        "eventfulness",
        "respondent_pleasantness",
        "respondent_eventfulness",
        "respondent_counts",
    ):
        assert not getattr(result, name).flags.writeable, name
    correlation = sc.spearman_rank_correlation([1, 2, 3], [1, 3, 2])
    assert not correlation.x.flags.writeable


@pytest.mark.parametrize(
    "correlate", [sc.spearman_rank_correlation, sc.pearson_correlation]
)
def test_a_correlation_holds_its_own_copies(correlate: object) -> None:
    """A later change to the caller's arrays cannot rewrite the result."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 5.0])
    result = correlate(x, y)  # type: ignore[operator]
    assert not np.shares_memory(result.x, x)
    assert not np.shares_memory(result.y, y)
    x[0] = 100.0
    assert result.x[0] == 1.0
    assert x.flags.writeable


@pytest.mark.parametrize("part", [1, 2, 3, 4])
def test_scale_values_are_a_new_array(part: int) -> None:
    """Parts 1 and 4 keep the position as the value, in an array of its own."""
    positions = np.array([1.0, 3.0, 5.0])
    values = sc.method_a_scale_values(positions, part=part)
    assert not np.shares_memory(values, positions)
    values[0] = 4.0  # type: ignore[index]
    np.testing.assert_array_equal(positions, [1.0, 3.0, 5.0])


def test_result_shapes_are_checked_when_built() -> None:
    with pytest.raises(ValueError, match="'medians'"):
        sc.MethodASummary(
            part=2,
            items=("pleasant",),
            sites=("a",),
            medians=np.zeros((2, 1)),
            minima=np.zeros((1, 1)),
            maxima=np.zeros((1, 1)),
            ranges=np.zeros((1, 1)),
            counts=np.zeros((1, 1), dtype=np.int64),
        )


def test_the_figure_a1_plot_draws_the_eight_attributes() -> None:
    sites = [row[0] for row in ISD_LOCATION_MEDIANS]
    medians = np.array([row[3] for row in ISD_LOCATION_MEDIANS], dtype=float)
    result = sc.pleasantness_eventfulness(medians, sites=sites)
    ax = result.plot()
    labels = {t.get_text() for t in ax.texts}
    assert {"PLEASANT", "VIBRANT", "EVENTFUL", "CHAOTIC"} <= labels
    assert {"ANNOYING", "MONOTONOUS", "UNEVENTFUL", "CALM"} <= labels
    # Each site is a marker of its own, named in the legend.
    assert ax.get_legend_handles_labels()[1] == sites
    assert ax.get_xlim() == pytest.approx((-2.0, 2.0))
    assert ax.get_ylim() == pytest.approx((-1.55, 1.55))
    plt.close("all")
    ax = result.plot(normalized=False, respondents=True, language="es")
    assert "AGRADABLE" in {t.get_text() for t in ax.texts}
    assert ax.get_xlim()[1] == pytest.approx(2.0 * _RANGE)
    plt.close("all")


def _site_markers(ax: object, sites: list[str]) -> list[object]:
    return [line for line in ax.lines if line.get_label() in sites]  # type: ignore[attr-defined]


@pytest.mark.parametrize("normalized", [True, False])
def test_the_figure_a1_plot_puts_each_site_at_its_p_and_e(*, normalized: bool) -> None:
    sites = [row[0] for row in ISD_LOCATION_MEDIANS]
    medians = np.array([row[3] for row in ISD_LOCATION_MEDIANS], dtype=float)
    result = sc.pleasantness_eventfulness(medians, sites=sites)
    ax = result.plot(normalized=normalized)
    markers = _site_markers(ax, sites)
    x = np.concatenate([np.asarray(m.get_xdata(), dtype=float) for m in markers])
    y = np.concatenate([np.asarray(m.get_ydata(), dtype=float) for m in markers])
    scale = 1.0 / _RANGE if normalized else 1.0
    np.testing.assert_allclose(x, result.pleasantness * scale, rtol=1e-12)
    np.testing.assert_allclose(y, result.eventfulness * scale, rtol=1e-12)
    plt.close("all")


def test_the_figure_a1_legend_stays_on_its_own_figure() -> None:
    """The renderer's own figure is laid out, so the legend under the axes
    is not cut off by a plain savefig() or plt.show().
    """
    sites = [row[0] for row in ISD_LOCATION_MEDIANS]
    medians = np.array([row[3] for row in ISD_LOCATION_MEDIANS], dtype=float)
    ax = sc.pleasantness_eventfulness(medians, sites=sites).plot(language="es")
    figure = ax.figure
    figure.canvas.draw()
    box = ax.get_legend().get_window_extent()
    assert box.y0 >= 0.0
    assert box.x0 >= 0.0
    assert box.x1 <= figure.bbox.width
    assert box.y1 < ax.xaxis.label.get_window_extent().y0
    assert ax.title.get_window_extent().y1 <= figure.bbox.height
    plt.close("all")


def _figure_a1_axes(
    result: sc.PleasantnessEventfulness, language: str, *, own: bool
) -> Axes:
    """The renderer's own figure, or a default one the caller lays out."""
    if own:
        return result.plot(language=language)
    _fig, ax = plt.subplots()
    result.plot(ax, language=language)
    plt.tight_layout()
    return ax


@pytest.mark.parametrize(("n_sites", "own"), [(26, True), (11, False)])
def test_the_figure_a1_labels_stay_inside_the_axes(*, n_sites: int, own: bool) -> None:
    """The words written past the arrow tips never reach the frame: on the
    renderer's own figure with the 26 sites of the database under it, and on
    a default figure the caller lays out with the eleven of the guide.
    """
    sites = [row[0] for row in ISD_LOCATION_MEDIANS][:n_sites]
    medians = np.array([row[3] for row in ISD_LOCATION_MEDIANS], dtype=float)
    result = sc.pleasantness_eventfulness(medians[:n_sites], sites=sites)
    for language in ("en", "es"):
        ax = _figure_a1_axes(result, language, own=own)
        ax.figure.canvas.draw()
        frame = ax.get_window_extent()
        for text in ax.texts:
            if not text.get_text():
                continue
            box = text.get_window_extent()
            assert frame.x0 < box.x0, text.get_text()
            assert box.x1 < frame.x1, text.get_text()
        plt.close("all")


def test_the_method_a_plot_marks_the_median_over_the_range() -> None:
    summary = sc.method_a_summary(
        {"pleasant": [5, 4, 2, 1, 3], "annoying": [1, 2, 4, 5, 3]},
        part=2,
        sites=["a", "a", "b", "b", "b"],
    )
    ax = summary.plot(language="es")
    markers = _site_markers(ax, ["a", "b"])
    for k, marker in enumerate(markers):
        np.testing.assert_array_equal(marker.get_ydata(), summary.medians[k])
    for k, bars in enumerate(ax.collections):
        segments = bars.get_segments()
        np.testing.assert_array_equal([s[0][1] for s in segments], summary.minima[k])
        np.testing.assert_array_equal([s[1][1] for s in segments], summary.maxima[k])
    title = ax.get_title()
    assert title.startswith("ISO/TS 12913-3, Método A, parte 2 (mediana, recorrido)\n")
    assert title.endswith("Calidad afectiva percibida")
    plt.close("all")


def test_the_method_b_plot_marks_the_mean_within_its_interval() -> None:
    summary = sc.method_b_summary(
        np.array(
            [
                [3.9, 4.2, 2.2],
                [4.4, 3.6, 2.8],
                [2.0, 2.5, 4.1],
                [3.3, 3.1, 3.9],
                [2.9, 3.8, 4.4],
            ]
        ),
        sites=["a", "a", "b", "b", "b"],
    )
    ax = summary.plot()
    markers = _site_markers(ax, ["a", "b"])
    for k, marker in enumerate(markers):
        np.testing.assert_allclose(marker.get_ydata(), summary.means[k])
    for k, bars in enumerate(ax.collections):
        segments = bars.get_segments()
        np.testing.assert_allclose(
            [s[0][1] for s in segments], summary.confidence_lower[k]
        )
        np.testing.assert_allclose(
            [s[1][1] for s in segments], summary.confidence_upper[k]
        )
    assert ax.get_title().endswith("mean, 95 % confidence interval")
    plt.close("all")
    ax = summary.plot(language="es")
    assert ax.get_title().endswith("media, intervalo de confianza del 95 %")
    plt.close("all")


def test_the_spearman_plot_draws_the_ranks_under_its_symbol() -> None:
    x = [3.0, 1.0, 2.0, 2.0, 5.0]
    y = [10.0, 30.0, 20.0, 40.0, 50.0]
    rho = sc.spearman_rank_correlation(x, y)
    ax = rho.plot()
    (points,) = ax.lines
    np.testing.assert_array_equal(points.get_xdata(), rho.x_ranks)
    np.testing.assert_array_equal(points.get_ydata(), rho.y_ranks)
    assert ax.get_title().startswith(r"$r_\mathrm{spearman}$ = ")
    plt.close("all")
    r = sc.pearson_correlation(x, y)
    ax = r.plot()
    (points,) = ax.lines
    np.testing.assert_array_equal(points.get_xdata(), r.x)
    np.testing.assert_array_equal(points.get_ydata(), r.y)
    assert ax.get_title().startswith("Pearson $r$ = ")
    plt.close("all")


def test_the_source_ranking_plot_draws_the_median_rank_and_its_range() -> None:
    ranking = sc.method_b_source_ranking(
        [["traffic", "voices", "birds"], ["birds", "traffic"], ["voices"], ["traffic"]],
        sites=["a", "a", "b", "b"],
    )
    ax = ranking.plot()
    for k, bars in enumerate(ax.containers):
        widths = [patch.get_width() for patch in bars]
        np.testing.assert_array_equal(
            widths, np.nan_to_num(ranking.median_ranks[k], nan=0.0)
        )
    for k, spans in enumerate(ax.collections):
        segments = spans.get_segments()
        np.testing.assert_array_equal(
            [s[0][0] for s in segments], np.nan_to_num(ranking.lowest_ranks[k], nan=0.0)
        )
        np.testing.assert_array_equal(
            [s[1][0] for s in segments],
            np.nan_to_num(ranking.highest_ranks[k], nan=0.0),
        )
    plt.close("all")


def test_the_respondents_are_drawn_in_the_colour_of_their_site() -> None:
    answers = np.array(
        [
            [5, 1, 4, 2, 5, 1, 3, 2],
            [4, 2, 4, 2, 4, 2, 3, 2],
            [2, 4, 3, 3, 2, 4, 4, 3],
            [1, 5, 2, 3, 1, 5, 5, 3],
            [2, 5, 2, 2, 2, 4, 4, 2],
        ],
        dtype=float,
    )
    result = sc.pleasantness_eventfulness(
        answers, sites=["park", "park", "road", "road", "road"]
    )
    ax = result.plot(respondents=True)
    dots = [line for line in ax.lines if line.get_marker() == "."]
    sites = [line for line in ax.lines if line.get_label() in ("park", "road")]
    # One faint series per site, holding that site's respondents only.
    assert [line.get_xdata().size for line in dots] == [2, 3]
    park_p = result.respondent_pleasantness[:2] / _RANGE
    assert np.asarray(dots[0].get_xdata()) == pytest.approx(park_p)
    # A dot is a quieter shade of its site's marker, never another site's hue.
    for dot, site in zip(dots, sites, strict=True):
        dot_rgb = np.asarray(mpl.colors.to_rgb(dot.get_color()))
        own = np.asarray(mpl.colors.to_rgb(site.get_color()))
        other = [
            np.asarray(mpl.colors.to_rgb(s.get_color())) for s in sites if s is not site
        ]
        assert all(
            np.linalg.norm(dot_rgb - own) < np.linalg.norm(dot_rgb - o) for o in other
        )
    plt.close("all")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: sc.method_a_summary(np.full((3, 4), 3), part=1),
        lambda: sc.pleasantness_eventfulness(_isd_answers()),
        lambda: sc.spearman_rank_correlation([1, 2, 3, 4], [1, 3, 2, 4]),
        lambda: sc.pearson_correlation([1, 2, 3, 4], [1, 3, 2, 4]),
        lambda: sc.method_b_summary(np.full((3, 4), 3.0)),
        lambda: sc.method_b_source_ranking([["traffic", "birds"], ["birds"]]),
    ],
)
def test_every_result_plots_in_both_languages(factory: object) -> None:
    result = factory()  # type: ignore[operator]
    for language in ("en", "es"):
        fig, ax = plt.subplots()
        assert result.plot(ax, language=language) is ax
        assert ax.get_title()
        plt.close(fig)


def test_names_are_published_on_the_environment_package() -> None:
    for name in sc.__all__:
        assert getattr(environment, name) is getattr(sc, name)
