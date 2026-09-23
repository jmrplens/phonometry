#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the Statistical Pass-By method (ISO 11819-1:1997).

The printed oracle is Annex E, a test report worked from regression lines to
the index, and Annex D, a reference surface averaged from seven surfaces. Annex
E prints the lines and not the pass-bys, so the fit itself is held to an
independent least-squares implementation (``scipy.stats.linregress``) on
seeded data, and the chain from pass-bys to the index is run on pass-bys placed
so that their least-squares line is exactly the printed one
(``reference_data.statistical_pass_by.annex_e_pass_bys``).
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import statistical_pass_by as ref
from scipy import stats

from phonometry import environment
from phonometry.environment.sources.statistical_pass_by import (
    SPB_ANNEX_D_SURFACES_DB,
    SPB_CONFIDENCE_INTERVALS_DB,
    SPB_MINIMUM_VEHICLE_COUNTS,
    SPB_NORMALIZED_REFERENCE_DB,
    SPB_REFERENCE_SPEEDS_KMH,
    SPB_SPEED_WINDOW_STANDARD_DEVIATIONS,
    SPB_VEHICLE_CATEGORIES,
    SPB_VEHICLE_STANDARD_DEVIATIONS_DB,
    SPB_WEIGHTING_FACTORS,
    StatisticalPassByResult,
    StatisticalPassByWarning,
    normalized_reference_levels,
    pass_by_regression,
    statistical_pass_by,
    statistical_pass_by_index,
)

_CATEGORIES = ("1", "2a", "2b")


def _annex_e_rows() -> tuple[list[str], list[float], list[float]]:
    categories: list[str] = []
    speeds: list[float] = []
    levels: list[float] = []
    for category in _CATEGORIES:
        v, level = ref.annex_e_pass_bys(category)
        categories += [category] * len(v)
        speeds += v
        levels += level
    return categories, speeds, levels


@pytest.fixture(scope="module")
def annex_e() -> StatisticalPassByResult:
    """The Annex E site, uncorrected and corrected, against its reference."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", StatisticalPassByWarning)
        return statistical_pass_by(
            *_annex_e_rows(),
            road_speed_category="medium",
            corrected_vehicle_sound_levels_db=ref.ANNEX_E_CORRECTED_VEHICLE_SOUND_LEVELS_DB,
            reference_db=ref.ANNEX_E_REFERENCE_INDEX_DB,
        )


def _cloud(
    n: int,
    *,
    mean_speed_kmh: float,
    lg_spread: float,
    intercept_db: float,
    slope_db: float,
    residual_db: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Seeded pass-bys scattered about a line in ``lg v``."""
    rng = np.random.default_rng(seed)
    logs = math.log10(mean_speed_kmh) + lg_spread * rng.standard_normal(n)
    levels = intercept_db + slope_db * logs + residual_db * rng.standard_normal(n)
    return 10.0**logs, levels


# --------------------------------------------------------------------------
# The printed tables
# --------------------------------------------------------------------------
def test_table_1_reference_speeds_and_weighting_factors() -> None:
    speeds = {road: dict(row) for road, row in SPB_REFERENCE_SPEEDS_KMH.items()}
    weights = {road: dict(row) for road, row in SPB_WEIGHTING_FACTORS.items()}
    assert speeds == ref.TABLE_1_REFERENCE_SPEEDS_KMH
    assert weights == ref.TABLE_1_WEIGHTING_FACTORS


@pytest.mark.parametrize("road", ["low", "medium", "high"])
def test_table_1_weights_are_proportions(road: str) -> None:
    assert math.fsum(SPB_WEIGHTING_FACTORS[road].values()) == pytest.approx(1.0)


def test_table_2_and_the_counts_of_7_3_and_9_3() -> None:
    assert (
        dict(SPB_VEHICLE_STANDARD_DEVIATIONS_DB) == ref.TABLE_2_STANDARD_DEVIATIONS_DB
    )
    assert dict(SPB_CONFIDENCE_INTERVALS_DB) == ref.TABLE_2_CONFIDENCE_INTERVALS_DB
    assert dict(SPB_MINIMUM_VEHICLE_COUNTS) == ref.MINIMUM_VEHICLE_COUNTS
    assert (
        dict(SPB_SPEED_WINDOW_STANDARD_DEVIATIONS)
        == ref.SPEED_WINDOW_STANDARD_DEVIATIONS
    )


def test_table_2_intervals_are_about_two_standard_errors() -> None:
    """The printed intervals follow from their NOTE's vehicle counts, roughly.

    1,96 standard deviations over the root of 100 cars rounds to the printed
    0,3 dB. Over the root of 40 heavy vehicles it gives 0,62 dB where 0,7 dB
    is printed: 9.6 reports the findings of research rather than this
    arithmetic, so the heavy intervals are only held to be the next tenth up.
    """
    car = 1.96 * SPB_VEHICLE_STANDARD_DEVIATIONS_DB["1"] / math.sqrt(100)
    heavy = 1.96 * SPB_VEHICLE_STANDARD_DEVIATIONS_DB["2a"] / math.sqrt(40)
    assert round(car, 1) == SPB_CONFIDENCE_INTERVALS_DB["1"]
    assert heavy < SPB_CONFIDENCE_INTERVALS_DB["2a"] < heavy + 0.1


def test_annex_d_surfaces_and_their_average() -> None:
    assert {k: dict(v) for k, v in SPB_ANNEX_D_SURFACES_DB.items()} == (
        ref.ANNEX_D_SURFACES_DB
    )
    assert dict(SPB_NORMALIZED_REFERENCE_DB) == ref.ANNEX_D_AVERAGE_DB
    averaged = normalized_reference_levels(SPB_ANNEX_D_SURFACES_DB)
    assert {k: round(v, 1) for k, v in averaged.items()} == ref.ANNEX_D_AVERAGE_DB


def test_annex_d_does_not_decide_between_means() -> None:
    """The energetic mean prints the same row, so the page cannot tell them apart."""
    levels = np.array(
        [[row[k] for k in _CATEGORIES] for row in ref.ANNEX_D_SURFACES_DB.values()]
    )
    energetic = 10.0 * np.log10(np.mean(10.0 ** (levels / 10.0), axis=0))
    assert [round(float(v), 1) for v in energetic] == list(
        ref.ANNEX_D_AVERAGE_DB.values()
    )


@pytest.mark.parametrize(
    ("table", "key"),
    [
        (SPB_REFERENCE_SPEEDS_KMH, "medium"),
        (SPB_REFERENCE_SPEEDS_KMH["medium"], "1"),
        (SPB_WEIGHTING_FACTORS["high"], "2b"),
        (SPB_MINIMUM_VEHICLE_COUNTS, "2"),
        (SPB_ANNEX_D_SURFACES_DB["A1"], "1"),
        (SPB_NORMALIZED_REFERENCE_DB, "2a"),
    ],
)
def test_published_tables_refuse_writes(table: dict, key: str) -> None:
    with pytest.raises(TypeError, match="does not support item assignment"):
        table[key] = 0.0


def test_result_arrays_refuse_writes(annex_e: StatisticalPassByResult) -> None:
    speeds = annex_e.regressions["1"].speeds_kmh
    with pytest.raises(ValueError, match="read-only"):
        speeds[0] = 1.0


# --------------------------------------------------------------------------
# Annex E, end to end
# --------------------------------------------------------------------------
def test_annex_e_lines_are_recovered(annex_e: StatisticalPassByResult) -> None:
    for category, regression in annex_e.regressions.items():
        assert regression.vehicle_count == ref.ANNEX_E_VEHICLE_COUNTS[category]
        assert regression.intercept_db == pytest.approx(
            ref.ANNEX_E_INTERCEPTS_DB[category], abs=1e-9
        )
        assert regression.slope_db_per_decade == pytest.approx(
            ref.ANNEX_E_SLOPES_DB[category], abs=1e-9
        )
        assert regression.mean_speed_kmh == pytest.approx(
            ref.ANNEX_E_MEAN_SPEEDS_KMH[category]
        )
        assert regression.correlation == pytest.approx(
            ref.ANNEX_E_CORRELATIONS[category]
        )
        assert regression.residual_standard_deviation_db == pytest.approx(
            ref.ANNEX_E_RESIDUAL_STANDARD_DEVIATIONS_DB[category]
        )
        # The line passes through the mean level printed beside it.
        assert (
            round(regression.mean_level_db, 1) == (ref.ANNEX_E_MEAN_LEVELS_DB[category])
        )
    assert annex_e.heavy_vehicle_count == ref.ANNEX_E_HEAVY_VEHICLE_COUNT


def test_annex_e_vehicle_sound_levels(annex_e: StatisticalPassByResult) -> None:
    assert dict(annex_e.reported_vehicle_sound_levels_db) == (
        ref.ANNEX_E_VEHICLE_SOUND_LEVELS_DB
    )
    assert annex_e.vehicle_sound_levels_db["1"] == pytest.approx(78.5456, abs=1e-4)
    assert annex_e.vehicle_sound_levels_db["2a"] == pytest.approx(81.1140, abs=1e-4)
    assert annex_e.vehicle_sound_levels_db["2b"] == pytest.approx(83.8379, abs=1e-4)


def test_annex_e_index_is_the_index_of_the_printed_levels() -> None:
    """79,9 dB is what the three levels give as printed, to one decimal."""
    index = statistical_pass_by_index(
        ref.ANNEX_E_VEHICLE_SOUND_LEVELS_DB, road_speed_category="medium"
    )
    assert index == pytest.approx(79.9464, abs=1e-4)
    assert round(index, 1) == ref.ANNEX_E_INDEX_DB


def test_clause_chain_reports_80_0(annex_e: StatisticalPassByResult) -> None:
    """Unrounded levels, as 9.2 has them calculated, give 80,0 dB, not 79,9."""
    assert annex_e.index_db == pytest.approx(79.9852, abs=1e-4)
    assert annex_e.reported_index_db == pytest.approx(80.0)
    two_decimals = {k: round(v, 2) for k, v in annex_e.vehicle_sound_levels_db.items()}
    literal = statistical_pass_by_index(two_decimals, road_speed_category="medium")
    assert literal == pytest.approx(79.9877, abs=1e-4)
    assert round(literal, 1) == pytest.approx(80.0)


def test_annex_e_corrected_index_and_difference(
    annex_e: StatisticalPassByResult,
) -> None:
    assert annex_e.corrected_index_db == pytest.approx(80.1210, abs=1e-4)
    assert annex_e.reported_corrected_index_db == ref.ANNEX_E_CORRECTED_INDEX_DB
    assert annex_e.corrected_difference_db is not None
    assert round(annex_e.corrected_difference_db, 1) == ref.ANNEX_E_DIFFERENCE_DB
    assert annex_e.difference_db == pytest.approx(
        annex_e.index_db - ref.ANNEX_E_REFERENCE_INDEX_DB
    )


def test_annex_e_meets_7_3_and_9_3(annex_e: StatisticalPassByResult) -> None:
    assert annex_e.meets_minimum_counts
    assert annex_e.reference_speeds_in_window


def test_annex_d_reference_index_is_not_the_annex_e_one() -> None:
    """The seven-surface reference of Annex D indexes to 78,9 dB, not 77,3 dB."""
    index = statistical_pass_by_index(
        SPB_NORMALIZED_REFERENCE_DB, road_speed_category="medium"
    )
    assert index == pytest.approx(78.9219, abs=1e-4)


def test_reference_as_levels_is_indexed_with_the_same_weights() -> None:
    result = statistical_pass_by(
        *_annex_e_rows(),
        road_speed_category="medium",
        reference_db=SPB_NORMALIZED_REFERENCE_DB,
    )
    assert result.reference_index_db == pytest.approx(78.9219, abs=1e-4)
    assert result.corrected_difference_db is None


def test_reference_index_may_be_any_real_number() -> None:
    """A numpy integer is an index, not a mapping of levels."""
    result = statistical_pass_by(
        *_annex_e_rows(), road_speed_category="medium", reference_db=np.int64(77)
    )
    assert result.reference_index_db == pytest.approx(77.0)
    assert result.difference_db == pytest.approx(result.index_db - 77.0)


def test_no_reference_leaves_the_differences_out() -> None:
    result = statistical_pass_by(*_annex_e_rows(), road_speed_category="medium")
    assert result.difference_db is None
    assert result.corrected_index_db is None
    assert result.reported_corrected_index_db is None


# --------------------------------------------------------------------------
# The regression against an independent least-squares fit
# --------------------------------------------------------------------------
def test_regression_matches_linregress() -> None:
    speeds, levels = _cloud(
        150,
        mean_speed_kmh=84.0,
        lg_spread=0.06,
        intercept_db=18.0,
        slope_db=32.0,
        residual_db=1.4,
        seed=1,
    )
    regression = pass_by_regression(
        speeds, levels, vehicle_category="1", road_speed_category="medium"
    )
    fit = stats.linregress(np.log10(speeds), levels)
    assert regression.slope_db_per_decade == pytest.approx(fit.slope, rel=1e-12)
    assert regression.intercept_db == pytest.approx(fit.intercept, rel=1e-12)
    assert regression.correlation == pytest.approx(fit.rvalue, rel=1e-12)
    residuals = levels - (fit.intercept + fit.slope * np.log10(speeds))
    assert regression.residual_standard_deviation_db == pytest.approx(
        math.sqrt(float(np.sum(residuals**2)) / (speeds.size - 2)), rel=1e-12
    )
    assert regression.level_standard_deviation_db == pytest.approx(
        float(np.std(levels, ddof=1)), rel=1e-12
    )
    assert regression.lg_speed_standard_deviation == pytest.approx(
        float(np.std(np.log10(speeds), ddof=1)), rel=1e-12
    )


def test_confidence_interval_is_the_line_interval_at_the_reference_speed() -> None:
    """Refitted about the reference speed, the intercept error is the line's there."""
    speeds, levels = _cloud(
        40,
        mean_speed_kmh=76.0,
        lg_spread=0.05,
        intercept_db=46.0,
        slope_db=19.0,
        residual_db=2.0,
        seed=2,
    )
    regression = pass_by_regression(
        speeds, levels, vehicle_category="2a", road_speed_category="medium"
    )
    shifted = stats.linregress(np.log10(speeds / 70.0), levels)
    quantile = stats.t.ppf(0.975, speeds.size - 2)
    assert regression.confidence_interval_db == pytest.approx(
        quantile * shifted.intercept_stderr, rel=1e-10
    )
    assert regression.vehicle_sound_level_db == pytest.approx(
        shifted.intercept, rel=1e-12
    )


@pytest.mark.filterwarnings("ignore::phonometry.environment.StatisticalPassByWarning")
def test_mean_speed_is_converted_from_the_logarithm() -> None:
    regression = pass_by_regression(
        [50.0, 80.0, 128.0],
        [70.0, 76.0, 81.0],
        vehicle_category="1",
        road_speed_category="medium",
    )
    assert regression.mean_speed_kmh == pytest.approx(80.0)


def test_index_interval_combines_the_three_by_sensitivity(
    annex_e: StatisticalPassByResult,
) -> None:
    step = 1e-6
    combined = 0.0
    for category in _CATEGORIES:
        levels = dict(annex_e.vehicle_sound_levels_db)
        levels[category] += step
        derivative = (
            statistical_pass_by_index(levels, road_speed_category="medium")
            - annex_e.index_db
        ) / step
        combined += (
            derivative * annex_e.regressions[category].confidence_interval_db
        ) ** 2
    assert annex_e.index_confidence_interval_db == pytest.approx(
        math.sqrt(combined), rel=1e-5
    )


# --------------------------------------------------------------------------
# The index
# --------------------------------------------------------------------------
def test_index_formula_of_9_5() -> None:
    levels = {"1": 76.0, "2a": 82.0, "2b": 85.0}
    expected = 10.0 * math.log10(
        0.700 * 10.0**7.6
        + 0.075 * (110.0 / 85.0) * 10.0**8.2
        + 0.225 * (110.0 / 85.0) * 10.0**8.5
    )
    assert statistical_pass_by_index(
        levels, road_speed_category="high"
    ) == pytest.approx(expected, rel=1e-14)


def test_all_the_weight_on_cars_gives_the_car_level() -> None:
    index = statistical_pass_by_index(
        {"1": 77.3, "2a": 82.0, "2b": 85.0},
        road_speed_category="low",
        weighting_factors={"1": 1.0, "2a": 0.0, "2b": 0.0},
    )
    assert index == pytest.approx(77.3, rel=1e-14)


@pytest.mark.filterwarnings("ignore::phonometry.environment.StatisticalPassByWarning")
def test_reported_levels_round_half_up() -> None:
    """A level on the half is reported up, as 9.2 rounds; Python's round() does not."""
    regression = pass_by_regression(
        [60.0, 80.0, 100.0],
        [78.25, 78.25, 78.25],
        vehicle_category="1",
        road_speed_category="medium",
    )
    assert regression.vehicle_sound_level_db == pytest.approx(78.25)
    assert regression.reported_vehicle_sound_level_db == pytest.approx(78.3)
    assert round(regression.vehicle_sound_level_db, 1) == pytest.approx(78.2)


# --------------------------------------------------------------------------
# 7.3 and 9.3, as warnings
# --------------------------------------------------------------------------
def test_reference_speed_outside_the_window_warns() -> None:
    speeds, levels = _cloud(
        120,
        mean_speed_kmh=115.0,
        lg_spread=0.02,
        intercept_db=17.0,
        slope_db=32.0,
        residual_db=1.0,
        seed=3,
    )
    with pytest.warns(StatisticalPassByWarning, match="9.3"):
        regression = pass_by_regression(
            speeds, levels, vehicle_category="1", road_speed_category="medium"
        )
    assert not regression.reference_speed_in_window
    low, high = regression.speed_window_kmh
    assert low > 80.0
    assert high > low


def test_too_few_vehicles_of_a_category_warns() -> None:
    speeds, levels = _cloud(
        20,
        mean_speed_kmh=80.0,
        lg_spread=0.05,
        intercept_db=17.0,
        slope_db=32.0,
        residual_db=1.0,
        seed=4,
    )
    with pytest.warns(StatisticalPassByWarning, match="7.3"):
        regression = pass_by_regression(
            speeds, levels, vehicle_category="1", road_speed_category="medium"
        )
    assert not regression.meets_minimum_count


def test_too_few_heavy_vehicles_together_warns() -> None:
    rows: tuple[list[str], list[float], list[float]] = ([], [], [])
    for category, n, seed in (("1", 100, 5), ("2a", 30, 6), ("2b", 30, 7)):
        speeds, levels = _cloud(
            n,
            mean_speed_kmh=75.0,
            lg_spread=0.06,
            intercept_db=40.0,
            slope_db=22.0,
            residual_db=1.5,
            seed=seed,
        )
        rows[0].extend([category] * n)
        rows[1].extend(speeds.tolist())
        rows[2].extend(levels.tolist())
    with pytest.warns(StatisticalPassByWarning, match="heavy vehicles"):
        result = statistical_pass_by(*rows, road_speed_category="medium")
    assert result.heavy_vehicle_count == 60
    assert not result.meets_minimum_counts


# --------------------------------------------------------------------------
# What is refused
# --------------------------------------------------------------------------
def test_a_category_the_method_does_not_use_is_refused() -> None:
    categories, speeds, levels = _annex_e_rows()
    categories[0] = "1b"
    with pytest.raises(ValueError, match="clause 4"):
        statistical_pass_by(categories, speeds, levels, road_speed_category="medium")


def test_an_unknown_road_speed_category_is_refused() -> None:
    with pytest.raises(ValueError, match="road_speed_category"):
        statistical_pass_by_index(
            ref.ANNEX_E_VEHICLE_SOUND_LEVELS_DB, road_speed_category="urban"
        )


def test_rows_that_do_not_match_are_refused() -> None:
    categories, speeds, levels = _annex_e_rows()
    with pytest.raises(ValueError, match="one value per pass-by"):
        statistical_pass_by(
            categories, speeds[:-1], levels, road_speed_category="medium"
        )


def test_a_category_with_too_few_pass_bys_is_refused() -> None:
    with pytest.raises(ValueError, match="at least 3 pass-bys"):
        pass_by_regression(
            [70.0, 80.0], [75.0, 77.0], vehicle_category="1", road_speed_category="low"
        )


def test_pass_bys_all_at_one_speed_are_refused() -> None:
    with pytest.raises(ValueError, match="same speed"):
        pass_by_regression(
            [80.0, 80.0, 80.0],
            [75.0, 76.0, 77.0],
            vehicle_category="1",
            road_speed_category="low",
        )


def test_a_speed_that_is_not_positive_is_refused() -> None:
    with pytest.raises(ValueError, match="speeds_kmh"):
        pass_by_regression(
            [0.0, 80.0, 90.0],
            [75.0, 76.0, 77.0],
            vehicle_category="1",
            road_speed_category="low",
        )


def test_a_missing_level_is_refused() -> None:
    with pytest.raises(ValueError, match="one value for each"):
        statistical_pass_by_index({"1": 78.0, "2a": 81.0}, road_speed_category="low")


def test_weights_that_are_not_proportions_are_refused() -> None:
    with pytest.raises(ValueError, match="add up"):
        statistical_pass_by_index(
            ref.ANNEX_E_VEHICLE_SOUND_LEVELS_DB,
            road_speed_category="medium",
            weighting_factors={"1": 0.8, "2a": 0.1, "2b": 0.2},
        )


def test_negative_weights_are_refused() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        statistical_pass_by_index(
            ref.ANNEX_E_VEHICLE_SOUND_LEVELS_DB,
            road_speed_category="medium",
            weighting_factors={"1": 1.1, "2a": 0.0, "2b": -0.1},
        )


def test_normalized_reference_needs_a_surface() -> None:
    with pytest.raises(ValueError, match="at least one surface"):
        normalized_reference_levels({})


# --------------------------------------------------------------------------
# The figures
# --------------------------------------------------------------------------
def test_plot_draws_three_lines_and_the_index(
    annex_e: StatisticalPassByResult,
) -> None:
    ax = annex_e.plot()
    labels = ax.get_legend_handles_labels()[1]
    assert len(labels) == 3
    assert "78.5 dB" in labels[0]
    assert "SPBI = 80.0 dB" in ax.get_title()
    assert ax.get_xscale() == "log"
    plt.close("all")


def test_plot_speaks_spanish(annex_e: StatisticalPassByResult) -> None:
    ax = annex_e.plot(language="es")
    labels = ax.get_legend_handles_labels()[1]
    assert labels[0].startswith("Turismos (1)")
    assert "78,5 dB" in labels[0]
    assert "80,0 dB" in ax.get_title()
    assert ax.get_xlabel() == "Velocidad del vehículo [km/h]"
    plt.close("all")


def test_regression_plot_draws_the_window_and_the_level(
    annex_e: StatisticalPassByResult,
) -> None:
    regression = annex_e.regressions["2b"]
    ax = regression.plot()
    labels = ax.get_legend_handles_labels()[1]
    assert any("Pass-bys ($n$ = 53)" in label for label in labels)
    assert any("83.8 dB" in label for label in labels)
    low, high = regression.speed_window_kmh
    window = ax.patches[0].get_bbox()
    assert window.x0 == pytest.approx(low)
    assert window.x1 == pytest.approx(high)
    plt.close("all")


def test_public_names_reach_the_environment_namespace() -> None:
    for name in (
        "statistical_pass_by",
        "statistical_pass_by_index",
        "pass_by_regression",
        "normalized_reference_levels",
        "SPB_REFERENCE_SPEEDS_KMH",
    ):
        assert hasattr(environment, name)
    assert environment.SPB_VEHICLE_CATEGORIES == SPB_VEHICLE_CATEGORIES
