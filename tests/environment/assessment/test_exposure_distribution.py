#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for :mod:`phonometry.environment.assessment.exposure_distribution` (ISO 13474:2009).

The oracle is Annex A of the standard, the TOW launcher heard at 3 020 m:
Table A.3 feeds Table A.4 digit by digit, and Figure A.3 prints the long-term
levels and five exceedance levels of the spread distribution. The integrals
the module evaluates in closed form (Equations (22), (24) and (A.4)) are
checked against numerical quadrature of the expressions as the standard
prints them, which shares no code with the closed forms.
"""

from __future__ import annotations

import dataclasses
import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import (
    ISO13474_ANNEX_A_DAY_FRACTION,
    ISO13474_ANNEX_A_NIGHT_FRACTION,
    ISO13474_ANNEX_A_PRINTED_SHIFT_DB,
    ISO13474_ANNEX_A_SIGMA_DB,
    ISO13474_ANNEX_A_SUBCLASSES,
    ISO13474_FIGURE_A3_EXCEEDANCE_DB,
    ISO13474_FIGURE_A3_LOWER_LIMIT_DB,
    ISO13474_FIGURE_A3_LT1_DB,
    ISO13474_FIGURE_A3_LT2_DB,
    ISO13474_TABLE_A3,
    ISO13474_TABLE_A4,
)
from scipy import integrate, optimize

from phonometry import environment
from phonometry.environment.assessment import exposure_distribution as sd

_LEVELS = np.array([row[1] for row in ISO13474_TABLE_A3])
_DAY = np.array([row[2] for row in ISO13474_TABLE_A3])
_NIGHT = np.array([row[3] for row in ISO13474_TABLE_A3])
_PRINTED_PERIOD = np.array([row[4] for row in ISO13474_TABLE_A3])
#: The 07:00 to 19:00 probabilities at full precision, as the annex forms them.
_PERIOD = (
    ISO13474_ANNEX_A_DAY_FRACTION * _DAY + ISO13474_ANNEX_A_NIGHT_FRACTION * _NIGHT
)


def _annex_a(probabilities: np.ndarray = _PERIOD) -> sd.SelDistribution:
    return sd.sel_distribution(
        _LEVELS,
        probabilities,
        sigma_db=ISO13474_ANNEX_A_SIGMA_DB,
        subclasses=ISO13474_ANNEX_A_SUBCLASSES,
    )


def _annex_a_one_subclass() -> sd.SelDistribution:
    return sd.sel_distribution(
        _LEVELS, _PERIOD, sigma_db=ISO13474_ANNEX_A_SIGMA_DB, subclasses=1
    )


def _column(index: int) -> np.ndarray:
    return np.array([row[index] for row in ISO13474_TABLE_A4])


# ---------------------------------------------------------------------------
# Annex A: Table A.3 to Table A.4
# ---------------------------------------------------------------------------
def test_period_column_of_table_a3_is_the_80_20_average() -> None:
    """The printed 07:00 to 19:00 column is 0,8 day + 0,2 night, rounded."""
    np.testing.assert_array_equal(np.round(_PERIOD, 4), _PRINTED_PERIOD)


def test_table_a4_levels_probabilities_and_boundaries() -> None:
    dist = _annex_a()
    np.testing.assert_array_equal(dist.levels_db, _column(1))
    np.testing.assert_array_equal(np.round(dist.probabilities, 4), _column(2))
    np.testing.assert_array_equal(np.round(dist.lower_bounds_db, 2), _column(3))
    np.testing.assert_array_equal(np.round(dist.upper_bounds_db, 2), _column(4))


def test_table_a4_densities_digit_by_digit() -> None:
    """All 27 printed densities, including 1,2399 and 0,0170.

    Both are what the full-precision probability gives and not what the
    rounded column beside them gives (0,1860 / 0,15 = 1,2400 and
    0,0042 / 0,25 = 0,0168), which is how the annex was computed.
    """
    dist = _annex_a()
    np.testing.assert_array_equal(np.round(dist.class_densities_per_db, 4), _column(5))


def test_equal_levels_keep_their_classes_in_input_order() -> None:
    """The two 30,8 dB classes are n = 8 then n = 20, as Table A.4 orders them."""
    dist = _annex_a()
    # Flat indices are the Table A.3 row numbers minus one.
    assert dist.replicas[2] == (7,)
    assert dist.replicas[3] == (19,)
    assert dist.replicas[6] == (8,)
    assert dist.replicas[7] == (9,)
    assert dist.upper_bounds_db[2] == pytest.approx(30.8)
    assert dist.lower_bounds_db[3] == pytest.approx(30.8)


# ---------------------------------------------------------------------------
# Annex A: the long-term levels and Figure A.3
# ---------------------------------------------------------------------------
def test_lt1_is_equation_7() -> None:
    dist = _annex_a()
    lt1 = sd.long_term_sel(_LEVELS, _PERIOD)
    assert lt1 == pytest.approx(dist.long_term_level_db, abs=1e-12)
    assert lt1 == pytest.approx(
        10.0 * math.log10(np.sum(_PERIOD * 10 ** (0.1 * _LEVELS)))
    )
    assert round(lt1, 1) == ISO13474_FIGURE_A3_LT1_DB


def test_lt2_matches_quadrature_of_equation_a4() -> None:
    dist = _annex_a()
    energy, _ = integrate.quad(
        lambda x: float(dist.density(x)) * 10.0 ** (0.1 * x),
        -60.0,
        160.0,
        limit=400,
        epsabs=0.0,
        epsrel=1e-12,
    )
    assert dist.distribution_long_term_level_db == pytest.approx(
        10.0 * math.log10(energy), abs=1e-9
    )
    assert round(dist.distribution_long_term_level_db, 1) == ISO13474_FIGURE_A3_LT2_DB


def test_lt2_with_one_subclass_is_the_energy_mean_of_the_class_centres() -> None:
    """With N_sub = 1 each subclass sits at the centre of its class.

    The shift of Equation (22) preserves the energy of every subclass, so what
    separates LT2 from LT1 is where the subclass centres sit and nothing else.
    With one subclass per class that centre is half-way between the printed
    boundaries of Table A.4, which gives the expected value without the
    library's subclass arithmetic.
    """
    dist = _annex_a_one_subclass()
    order = np.argsort(_LEVELS, kind="stable")
    centres = 0.5 * (_column(3) + _column(4))
    expected = 10.0 * math.log10(
        float(np.sum(_PERIOD[order] * 10.0 ** (0.1 * centres)))
    )
    assert dist.distribution_long_term_level_db == pytest.approx(expected, abs=1e-9)


def test_lt2_sits_below_lt1_in_the_annex_example() -> None:
    """Spread over their widths, the classes lose energy against their levels."""
    dist = _annex_a()
    assert dist.distribution_long_term_level_db < dist.long_term_level_db


def test_fifty_percent_level_matches_figure_a3() -> None:
    dist = _annex_a()
    assert round(dist.exceedance_level(50.0), 1) == ISO13474_FIGURE_A3_EXCEEDANCE_DB[50]


def test_figure_a3_levels_other_than_l50_are_not_the_roots_of_equation_25() -> None:
    """Equation (25) gives 21,6 / 40,5 / 43,0 / 47,5 dB; the figure prints higher.

    The roots are checked against a bracketing root search on the quadrature
    of the density, which shares no code with ``exceedance_level``. The
    printed 21,7 / 40,6 / 43,2 / 48,0 dB are the erratum in docs/ERRATA.md,
    whichever of the two probability columns feeds the distribution.
    """
    percents = (95.0, 10.0, 5.0, 1.0)
    for probabilities in (_PERIOD, _PRINTED_PERIOD):
        dist = _annex_a(probabilities)
        total = float(np.sum(probabilities))
        roots = []
        for percent in percents:
            target = percent / 100.0

            def tail(
                x: float,
                target: float = target,
                d: sd.SelDistribution = dist,
                whole: float = total,
            ) -> float:
                below, _ = integrate.quad(
                    lambda t: float(d.density(t)), -60.0, x, limit=400, epsabs=1e-14
                )
                return whole - below - target

            roots.append(optimize.brentq(tail, 10.0, 60.0, xtol=1e-9))
        np.testing.assert_allclose(dist.exceedance_level(percents), roots, atol=1e-6)
        np.testing.assert_array_equal(np.round(roots, 1), [21.6, 40.5, 43.0, 47.5])
        printed = [ISO13474_FIGURE_A3_EXCEEDANCE_DB[int(p)] for p in percents]
        assert np.all(np.asarray(printed) - np.asarray(roots) > 0.05)


def _accumulated_from_the_drawn_start(
    dist: sd.SelDistribution, percent: float
) -> float:
    """The level where 1 - (P(L > 15) - P(L > x)) falls to the percentage."""
    floor = float(dist.exceedance(ISO13474_FIGURE_A3_LOWER_LIMIT_DB))
    return float(
        optimize.brentq(
            lambda x: 1.0 - (floor - float(dist.exceedance(x))) - percent / 100.0,
            ISO13474_FIGURE_A3_LOWER_LIMIT_DB + 1e-6,
            80.0,
            xtol=1e-10,
        )
    )


def test_the_15_db_reading_matches_figure_a3_only_with_the_rounded_column() -> None:
    """What the errata entry says of the hypothesis, and where it stops.

    Accumulated from 15 dB, where the drawn curve of Figure A.3 begins (its
    axis starts at 10 dB), the curve reproduces all five printed levels when
    fed the 07:00 to 19:00 column of Table A.3 as printed, which sums to
    1,0004. Fed the full-precision probabilities that reproduce Table A.4, it
    gives 48,05 dB for L1, which would print 48,1 dB. With the printed column
    the reading adds about 0,17 % to every exceedance: the 0,21 % below 15 dB
    less the 0,04 % by which the column exceeds one.
    """
    rounded = _annex_a(_PRINTED_PERIOD)
    for percent, printed in ISO13474_FIGURE_A3_EXCEEDANCE_DB.items():
        level = _accumulated_from_the_drawn_start(rounded, percent)
        assert level == pytest.approx(printed, abs=0.05), percent
    below = float(np.sum(_PRINTED_PERIOD)) - float(
        rounded.exceedance(ISO13474_FIGURE_A3_LOWER_LIMIT_DB)
    )
    offset = 1.0 - float(rounded.exceedance(ISO13474_FIGURE_A3_LOWER_LIMIT_DB))
    assert round(100.0 * below, 2) == pytest.approx(0.21)
    assert round(100.0 * offset, 2) == pytest.approx(0.17)
    full = _accumulated_from_the_drawn_start(_annex_a(), 1.0)
    assert full == pytest.approx(48.0549, abs=1e-4)
    assert round(full, 1) == pytest.approx(48.1)


def test_printed_level_shift_is_not_equation_22_at_5_db() -> None:
    """1,04 dB is Equation (22) at sigma = 3 dB; the annex spreads with 5 dB.

    LT2 printed as 37,0 dB needs the 2,878 dB of Equation (22): with 1,04 dB
    every level of the distribution moves up by 1,84 dB and LT2 reads 38,8 dB.
    """
    assert round(sd.turbulence_level_shift(3.0), 2) == ISO13474_ANNEX_A_PRINTED_SHIFT_DB
    shift = sd.turbulence_level_shift(ISO13474_ANNEX_A_SIGMA_DB)
    assert shift == pytest.approx(2.878231366, abs=1e-9)
    dist = _annex_a()
    with_printed_shift = dist.distribution_long_term_level_db + (
        shift - ISO13474_ANNEX_A_PRINTED_SHIFT_DB
    )
    assert round(with_printed_shift, 1) == pytest.approx(38.8)


def test_figure_a2_peak_sits_where_the_printed_curve_peaks() -> None:
    """The crest of Figure A.2, to what the page resolves.

    Read off the drawn curve (folio 35), the crest is flat to its line width
    from about 30,2 dB to 30,8 dB and sits at 0,0607/dB, a height the page
    gives to a few units in the fifth decimal. The check holds the computed
    peak to that span and that height, and no closer.
    """
    dist = _annex_a()
    x = np.linspace(25.0, 36.0, 11001)
    density = np.asarray(dist.density(x))
    assert x[np.argmax(density)] == pytest.approx(30.5, abs=0.3)
    assert float(density.max()) == pytest.approx(0.0607, abs=5e-4)


# ---------------------------------------------------------------------------
# The closed forms against quadrature of the printed expressions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sigma", [0.5, 3.0, 5.0, 8.0])
def test_turbulence_level_shift_is_the_integral_of_equation_22(sigma: float) -> None:
    # 10^(0.1 x) exp(-x^2 / 2 sigma^2), with the two exponents added so the
    # factors cannot overflow apart; nothing of the integrand is left beyond
    # 40 standard deviations of its peak.
    ln10 = math.log(10.0)

    def integrand(x: float) -> float:
        return math.exp(0.1 * ln10 * x - (x * x) / (2.0 * sigma * sigma))

    peak = 0.1 * ln10 * sigma * sigma
    integral, _ = integrate.quad(
        integrand,
        peak - 40.0 * sigma,
        peak + 40.0 * sigma,
        points=[peak],
        limit=200,
        epsabs=0.0,
        epsrel=1e-13,
    )
    expected = 10.0 * math.log10(integral / (sigma * math.sqrt(2.0 * math.pi)))
    assert sd.turbulence_level_shift(sigma) == pytest.approx(expected, abs=1e-10)


def test_each_subclass_keeps_its_energy_after_the_shift() -> None:
    """The reason for Equation (22): the spread subclass averages to its centre."""
    dist = sd.sel_distribution([40.0, 50.0], [0.5, 0.5], sigma_db=4.0, subclasses=1)
    mean = float(dist.subclass_centres_db[0, 0])
    shift = dist.level_shift_db

    def integrand(x: float) -> float:
        z = (x - (mean - shift)) / 4.0
        return math.exp(-0.5 * z * z + 0.1 * math.log(10.0) * (x - mean)) / (
            4.0 * math.sqrt(2.0 * math.pi)
        )

    energy, _ = integrate.quad(
        integrand,
        mean - 200.0,
        mean + 200.0,
        points=[mean],
        limit=200,
        epsabs=0.0,
        epsrel=1e-13,
    )
    # The integrand carries 10^(-0.1 mean), so the energy is 1 at the centre.
    assert 10.0 * math.log10(energy) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("x", [10.0, 25.0, 31.4, 40.0, 50.0])
def test_exceedance_is_the_integral_of_the_density(x: float) -> None:
    dist = _annex_a()
    tail, _ = integrate.quad(
        lambda t: float(dist.density(t)), x, 160.0, limit=400, epsabs=1e-14
    )
    assert float(dist.exceedance(x)) == pytest.approx(tail, abs=1e-11)


def test_density_integrates_to_the_total_probability() -> None:
    dist = _annex_a()
    total, _ = integrate.quad(
        lambda t: float(dist.density(t)), -60.0, 160.0, limit=400, epsabs=1e-14
    )
    assert total == pytest.approx(float(np.sum(_PERIOD)), abs=1e-11)
    assert float(dist.exceedance(-1000.0)) == pytest.approx(float(np.sum(_PERIOD)))
    assert float(dist.exceedance(1000.0)) == 0.0


def test_exceedance_level_inverts_the_exceedance() -> None:
    dist = _annex_a()
    percents = np.array([99.0, 95.0, 50.0, 10.0, 5.0, 1.0, 0.01])
    levels = dist.exceedance_level(percents)
    assert levels.shape == percents.shape
    np.testing.assert_allclose(dist.exceedance(levels), percents / 100.0, atol=1e-12)
    assert np.all(np.diff(levels) > 0.0)


def test_class_density_is_a_step_function_of_the_classes() -> None:
    dist = _annex_a()
    centres = 0.5 * (dist.lower_bounds_db + dist.upper_bounds_db)
    np.testing.assert_allclose(dist.class_density(centres), dist.class_densities_per_db)
    assert dist.class_density(20.0) == 0.0
    assert dist.class_density(60.0) == 0.0
    # At a shared boundary Equation (15) defines neither neighbour.
    assert dist.class_density(float(dist.lower_bounds_db[5])) == 0.0
    area = np.sum(
        dist.class_densities_per_db * (dist.upper_bounds_db - dist.lower_bounds_db)
    )
    assert area == pytest.approx(float(np.sum(_PERIOD)))


def test_subclass_centres_follow_equation_18() -> None:
    dist = sd.sel_distribution([40.0, 44.0], [0.25, 0.75], subclasses=4)
    # Classes [38, 42] and [42, 46]: b = 1 dB, centres at g_L + (j - 1/2) b.
    np.testing.assert_allclose(
        dist.subclass_centres_db,
        [[38.5, 39.5, 40.5, 41.5], [42.5, 43.5, 44.5, 45.5]],
    )
    np.testing.assert_allclose(dist.class_densities_per_db, [0.25 / 4.0, 0.75 / 4.0])


def test_sigma_and_subclasses_default_to_the_annex() -> None:
    dist = sd.sel_distribution([40.0, 44.0], [0.5, 0.5])
    assert dist.sigma_db == 5.0
    assert dist.subclasses == 10
    assert dist.subclass_centres_db.shape == (2, 10)


def test_result_arrays_are_read_only() -> None:
    dist = _annex_a()
    arrays = {
        field.name: getattr(dist, field.name)
        for field in dataclasses.fields(dist)
        if isinstance(getattr(dist, field.name), np.ndarray)
    }
    assert set(arrays) == {
        "levels_db",
        "probabilities",
        "lower_bounds_db",
        "upper_bounds_db",
        "class_densities_per_db",
        "subclass_centres_db",
    }
    writable = [name for name, array in arrays.items() if array.flags.writeable]
    assert writable == []
    with pytest.raises(ValueError, match="read-only"):
        dist.subclass_centres_db[0, 0] = 0.0


# ---------------------------------------------------------------------------
# Equal levels: when a class would have no width
# ---------------------------------------------------------------------------
def test_three_equal_levels_are_combined_into_one_class() -> None:
    """Clause 5: the middle of three equal levels has no width."""
    dist = sd.sel_distribution(
        [40.0, 42.0, 42.0, 42.0, 45.0], [0.1, 0.2, 0.3, 0.1, 0.3]
    )
    np.testing.assert_allclose(dist.levels_db, [40.0, 42.0, 45.0])
    np.testing.assert_allclose(dist.probabilities, [0.1, 0.6, 0.3])
    np.testing.assert_allclose(dist.lower_bounds_db, [39.0, 41.0, 43.5])
    np.testing.assert_allclose(dist.upper_bounds_db, [41.0, 43.5, 46.5])
    assert dist.replicas == ((0,), (1, 2, 3), (4,))


def test_two_equal_levels_at_an_end_are_combined() -> None:
    """Equations (12) and (13) leave the end class of a pair with no width."""
    low = sd.sel_distribution([40.0, 40.0, 44.0], [0.3, 0.3, 0.4])
    np.testing.assert_allclose(low.levels_db, [40.0, 44.0])
    np.testing.assert_allclose(low.probabilities, [0.6, 0.4])
    high = sd.sel_distribution([40.0, 44.0, 44.0], [0.4, 0.3, 0.3])
    np.testing.assert_allclose(high.levels_db, [40.0, 44.0])
    np.testing.assert_allclose(high.lower_bounds_db, [38.0, 42.0])
    np.testing.assert_allclose(high.upper_bounds_db, [42.0, 46.0])


def test_two_equal_interior_levels_keep_two_classes() -> None:
    dist = sd.sel_distribution([40.0, 42.0, 42.0, 45.0], [0.1, 0.2, 0.3, 0.4])
    np.testing.assert_allclose(dist.levels_db, [40.0, 42.0, 42.0, 45.0])
    np.testing.assert_allclose(dist.lower_bounds_db, [39.0, 41.0, 42.0, 43.5])
    np.testing.assert_allclose(dist.upper_bounds_db, [41.0, 42.0, 43.5, 46.5])


# ---------------------------------------------------------------------------
# Equations (5), (7), (8) and (14)
# ---------------------------------------------------------------------------
def test_replica_probabilities_is_the_outer_product() -> None:
    p = sd.replica_probabilities([0.25, 0.75], [0.1, 0.3, 0.6])
    np.testing.assert_allclose(p, [[0.025, 0.075, 0.15], [0.075, 0.225, 0.45]])
    assert p.sum() == pytest.approx(1.0)


def test_grid_and_flat_inputs_give_the_same_distribution() -> None:
    levels = np.array([[40.0, 43.0, 47.0], [38.0, 41.0, 45.0]])
    probs = sd.replica_probabilities([0.6, 0.4], [0.5, 0.3, 0.2])
    grid = sd.sel_distribution(levels, probs)
    flat = sd.sel_distribution(levels.ravel(), probs.ravel())
    np.testing.assert_array_equal(grid.levels_db, flat.levels_db)
    np.testing.assert_array_equal(
        grid.class_densities_per_db, flat.class_densities_per_db
    )
    assert grid.replicas == flat.replicas
    # Row-major: replica (k, l) sits at flat index k * N_exc + l; (1, 0) is 38 dB.
    assert grid.replicas[0] == (3,)
    assert sd.long_term_sel(levels, probs) == pytest.approx(
        sd.long_term_sel(levels.ravel(), probs.ravel())
    )


def test_rating_level_adds_k_inside_the_sum() -> None:
    levels = [40.0, 43.0, 47.0]
    probs = [0.5, 0.3, 0.2]
    k = 12.0
    expected = 10.0 * math.log10(
        sum(p * 10 ** (0.1 * (lv + k)) for lv, p in zip(levels, probs, strict=True))
    )
    assert sd.long_term_sel(levels, probs, rating_adjustment_db=k) == pytest.approx(
        expected
    )
    assert sd.long_term_sel(levels, probs) == pytest.approx(expected - k)


def test_frequency_weighted_sel_is_the_energy_sum_of_equation_5() -> None:
    bands = [115.0, 119.0, 134.0, 135.0, 134.0, 136.0, 133.0, 126.0]
    a_weighting = [-39.4, -26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0]
    expected = 10.0 * math.log10(
        sum(10 ** (0.1 * (lv + w)) for lv, w in zip(bands, a_weighting, strict=True))
    )
    assert sd.frequency_weighted_sel(bands, a_weighting) == pytest.approx(
        expected, abs=1e-12
    )


def test_frequency_weighted_sel_keeps_the_leading_axes() -> None:
    spectra = np.array([[[60.0, 70.0], [50.0, 50.0]], [[80.0, 80.0], [0.0, -10.0]]])
    out = sd.frequency_weighted_sel(spectra, [0.0, -3.0])
    assert isinstance(out, np.ndarray)
    assert out.shape == (2, 2)
    assert out[1, 0] == pytest.approx(10.0 * math.log10(10**8 + 10**7.7))


def test_frequency_weighted_sel_does_not_overflow() -> None:
    assert sd.frequency_weighted_sel([4000.0, 4000.0], 0.0) == pytest.approx(
        4000.0 + 10.0 * math.log10(2.0)
    )


def test_names_are_exported_from_the_environment_domain() -> None:
    for name in sd.__all__:
        assert getattr(environment, name) is getattr(sd, name)


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------
def test_refuses_shapes_that_differ() -> None:
    levels = [40.0, 42.0, 44.0]
    probs = [0.5, 0.5]
    with pytest.raises(ValueError, match="same shape"):
        sd.sel_distribution(levels, probs)


def test_refuses_a_negative_probability() -> None:
    probs = [1.2, -0.2]
    with pytest.raises(ValueError, match="negative probability"):
        sd.sel_distribution([40.0, 44.0], probs)


def test_refuses_probabilities_that_do_not_sum_to_one() -> None:
    percent = [50.0, 50.0]
    with pytest.raises(ValueError, match="sum to one"):
        sd.long_term_sel([40.0, 44.0], percent)


@pytest.mark.parametrize("total", [0.98, 1.02])
def test_refuses_a_set_of_classes_two_percent_from_one(total: float) -> None:
    """A class left out, or one counted twice, is refused and not renormalised."""
    probs = _PERIOD * (total / float(np.sum(_PERIOD)))
    with pytest.raises(ValueError, match="sum to one"):
        sd.sel_distribution(_LEVELS, probs)


@pytest.mark.parametrize("total", [0.995, 1.0004, 1.005])
def test_accepts_probabilities_rounded_to_a_printed_table(total: float) -> None:
    """Table A.3 prints a 07:00 to 19:00 column that sums to 1,000 4."""
    probs = _PERIOD * (total / float(np.sum(_PERIOD)))
    dist = sd.sel_distribution(_LEVELS, probs)
    assert float(np.sum(dist.probabilities)) == pytest.approx(total)


def test_accepts_the_printed_period_column_of_table_a3() -> None:
    assert float(np.sum(_PRINTED_PERIOD)) == pytest.approx(1.0004, abs=1e-12)
    level = sd.long_term_sel(_LEVELS, _PRINTED_PERIOD)
    assert round(float(level), 1) == ISO13474_FIGURE_A3_LT1_DB


def test_refuses_a_single_distinct_level() -> None:
    levels = [42.0, 42.0]
    with pytest.raises(ValueError, match="two distinct levels"):
        sd.sel_distribution(levels, [0.5, 0.5])


def test_refuses_a_non_finite_level() -> None:
    levels = [40.0, float("nan")]
    with pytest.raises(ValueError, match="'levels_db' must contain only finite"):
        sd.sel_distribution(levels, [0.5, 0.5])


def test_refuses_a_complex_level() -> None:
    levels = np.array([40.0 + 1j, 44.0])
    with pytest.raises(ValueError, match="'levels_db' must be real"):
        sd.long_term_sel(levels, [0.5, 0.5])


def test_refuses_an_empty_input() -> None:
    empty: list[float] = []
    with pytest.raises(ValueError, match="'levels_db' must not be empty"):
        sd.long_term_sel(empty, empty)


@pytest.mark.parametrize("sigma", [0.0, -5.0, float("inf")])
def test_refuses_a_non_positive_sigma(sigma: float) -> None:
    with pytest.raises(ValueError, match="'sigma_db' must be positive"):
        sd.turbulence_level_shift(sigma)


def test_refuses_zero_subclasses() -> None:
    with pytest.raises(ValueError, match="'subclasses' must be a whole number"):
        sd.sel_distribution([40.0, 44.0], [0.5, 0.5], subclasses=0)


def test_refuses_a_non_finite_rating_adjustment() -> None:
    with pytest.raises(ValueError, match="'rating_adjustment_db' must be finite"):
        sd.long_term_sel([40.0, 44.0], [0.5, 0.5], rating_adjustment_db=float("nan"))


@pytest.mark.parametrize("percent", [0.0, 100.0, -1.0, float("nan")])
def test_refuses_a_percentage_out_of_range(percent: float) -> None:
    dist = sd.sel_distribution([40.0, 44.0], [0.5, 0.5])
    with pytest.raises(ValueError, match="'percent' must lie strictly between"):
        dist.exceedance_level(percent)


def test_refuses_a_two_dimensional_class_probability() -> None:
    grid = [[0.5, 0.5]]
    with pytest.raises(
        ValueError, match="'absorption_probabilities' must be one-dimensional"
    ):
        sd.replica_probabilities(grid, [1.0])


def test_refuses_weighting_that_does_not_broadcast() -> None:
    weighting = [0.0, 1.0, 2.0]
    with pytest.raises(ValueError, match="'weighting_db' must broadcast"):
        sd.frequency_weighted_sel([60.0, 70.0], weighting)


def test_refuses_all_zero_probabilities_in_the_energy_mean() -> None:
    levels = np.array([40.0, 44.0])
    weights = np.zeros(2)
    with pytest.raises(ValueError, match="at least one replica"):
        sd._energy_mean_db(levels, weights)


def _fields(**overrides: object) -> dict[str, object]:
    dist = sd.sel_distribution([40.0, 44.0], [0.5, 0.5], subclasses=2)
    fields = {name: getattr(dist, name) for name in dist.__dataclass_fields__}
    fields.update(overrides)
    return fields


def test_result_refuses_columns_of_different_length() -> None:
    fields = _fields(probabilities=np.array([1.0]))
    with pytest.raises(ValueError, match="per-class columns"):
        sd.SelDistribution(**fields)  # type: ignore[arg-type]


def test_result_refuses_subclass_centres_of_the_wrong_shape() -> None:
    fields = _fields(subclass_centres_db=np.zeros((2, 3)))
    with pytest.raises(ValueError, match="'subclass_centres_db' must have one row"):
        sd.SelDistribution(**fields)  # type: ignore[arg-type]


def test_result_refuses_a_class_of_no_width() -> None:
    fields = _fields(upper_bounds_db=np.array([42.0, 42.0]))
    with pytest.raises(ValueError, match="positive width"):
        sd.SelDistribution(**fields)  # type: ignore[arg-type]


def test_result_refuses_a_non_finite_column() -> None:
    fields = _fields(class_densities_per_db=np.array([np.nan, 0.1]))
    with pytest.raises(
        ValueError, match="'class_densities_per_db' must contain only finite"
    ):
        sd.SelDistribution(**fields)  # type: ignore[arg-type]


def test_result_refuses_replicas_that_miss_a_class() -> None:
    fields = _fields(replicas=((0,),))
    with pytest.raises(ValueError, match="'replicas' must name"):
        sd.SelDistribution(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# What the three views draw
# ---------------------------------------------------------------------------
def test_classes_view_draws_the_step_density_over_the_boundaries() -> None:
    dist = _annex_a()
    ax = dist.plot(view="classes")
    (steps,) = ax.patches
    values, edges, _ = steps.get_data()
    np.testing.assert_allclose(values, dist.class_densities_per_db)
    np.testing.assert_allclose(edges[:-1], dist.lower_bounds_db)
    assert edges[-1] == pytest.approx(dist.upper_bounds_db[-1])
    plt.close("all")


def test_density_view_draws_the_continuous_density_and_lt2() -> None:
    dist = _annex_a()
    ax = dist.plot()
    curve, marker = ax.lines
    np.testing.assert_allclose(curve.get_ydata(), dist.density(curve.get_xdata()))
    assert marker.get_xdata()[0] == pytest.approx(dist.distribution_long_term_level_db)
    assert marker.get_label() == "LT2 (long-term level) 37.0 dB"
    plt.close("all")


def test_exceedance_view_marks_the_five_figure_a3_levels() -> None:
    dist = _annex_a()
    ax = dist.plot(view="exceedance", language="es")
    curve, *points, marker = ax.lines
    np.testing.assert_allclose(curve.get_ydata(), dist.exceedance(curve.get_xdata()))
    assert len(points) == 5
    levels = [float(p.get_xdata()[0]) for p in points]
    np.testing.assert_allclose(
        levels, dist.exceedance_level([95.0, 50.0, 10.0, 5.0, 1.0])
    )
    np.testing.assert_allclose(
        [float(p.get_ydata()[0]) for p in points], [0.95, 0.5, 0.1, 0.05, 0.01]
    )
    assert "31,5 dB" in points[1].get_label()
    assert marker.get_label() == "LT2 (nivel a largo plazo) 37,0 dB"
    assert ax.get_xlabel().startswith("Nivel de exposición sonora")
    plt.close("all")


def test_plot_forwards_style_and_composes_into_given_axes() -> None:
    dist = _annex_a()
    _, given = plt.subplots()
    ax = dist.plot(given, view="exceedance", c="k", linewidth=3.0)
    assert ax is given
    assert ax.lines[0].get_linewidth() == pytest.approx(3.0)
    plt.close("all")


def test_plot_refuses_an_unknown_view() -> None:
    dist = _annex_a()
    with pytest.raises(ValueError, match="Unknown view 'cdf'"):
        dist.plot(view="cdf")
