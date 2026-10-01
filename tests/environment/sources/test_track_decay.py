#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tests for the track decay rate of EN 15461:2008+A1:2010.

EN 15461 prints no measured example. The oracle is its own Annex A: a
response that decays as :math:`A(0)\,e^{-\beta x}` has the rate
:math:`20 \lg e^{\beta} = 8{,}686\,\beta` dB/m, and on any grid Formula 1 is
:math:`4{,}343` over the sum of :math:`e^{-2\beta x_n}\,\Delta x_n` with the
intervals of A.2, which a uniform grid turns into a geometric series with a
closed sum. The grid itself is Figure 2, whose 29 points are pinned here.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import environment
from phonometry.environment.sources.track_decay import (
    TRACK_DECAY_EXCITATION_INDICES,
    TrackDecayRate,
    track_decay_excitation_positions,
    track_decay_rate,
)

_NEPER_DB = 20.0 * math.log10(math.e)

#: How a grid that does not start at 0 m and increase is refused.
_GRID_ORDER = "'distances_m' must start at the accelerometer, 0 m, and increase"


def test_the_grid_is_the_29_points_of_figure_2() -> None:
    """Quarter bays to 2,5, half bays to 4, whole bays to 8, then 10 to 66."""
    assert len(TRACK_DECAY_EXCITATION_INDICES) == 29
    assert TRACK_DECAY_EXCITATION_INDICES[:11] == tuple(0.25 * n for n in range(11))
    assert TRACK_DECAY_EXCITATION_INDICES[11:18] == (3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0)
    assert TRACK_DECAY_EXCITATION_INDICES[18:] == (
        10.0, 12.0, 16.0, 20.0, 24.0, 30.0, 36.0, 42.0, 48.0, 54.0, 66.0,
    )  # fmt: skip


def test_the_grid_scales_with_the_sleeper_spacing() -> None:
    """6.7: 0,6 m bays when the rail has no discrete supports, 39,6 m at bay 66."""
    positions = track_decay_excitation_positions()
    assert positions[-1] == pytest.approx(39.6)
    np.testing.assert_allclose(
        track_decay_excitation_positions(sleeper_spacing_m=0.65),
        np.asarray(TRACK_DECAY_EXCITATION_INDICES) * 0.65,
    )


def test_formula_1_on_a_uniform_grid_is_a_geometric_series() -> None:
    """4,343 / (dx/2 + dx*sum q**n + dx*q**N), q = exp(-2 beta dx), to rounding."""
    beta = 0.3
    dx = 0.25
    count = 80
    distances = dx * np.arange(count + 1)
    response = np.exp(-beta * distances)[:, None]
    rate = track_decay_rate(response, frequencies_hz=[1000.0], distances_m=distances)
    q = math.exp(-2.0 * beta * dx)
    series = dx / 2.0 + dx * sum(q**n for n in range(1, count)) + dx * q**count
    assert rate.decay_rates_db_per_m[0] == pytest.approx(4.343 / series, rel=1e-12)


def test_a_dense_grid_recovers_the_exponential_rate() -> None:
    """A.1: the rate of A(0) exp(-beta x) is 8,686 beta dB/m."""
    distances = np.arange(0.0, 150.0, 1.0e-3)
    beta = 0.23
    rate = track_decay_rate(
        np.exp(-beta * distances)[:, None],
        frequencies_hz=[500.0],
        distances_m=distances,
    )
    assert rate.decay_rates_db_per_m[0] == pytest.approx(_NEPER_DB * beta, rel=2e-4)


def test_mobility_and_accelerance_give_the_same_rate() -> None:
    """Only the ratio to the direct response enters, so a factor per band cancels."""
    positions = track_decay_excitation_positions()
    frequencies = np.array([250.0, 1000.0, 4000.0])
    betas = np.array([0.5, 0.1, 0.2])
    mobility = np.exp(-np.outer(positions, betas))
    accelerance = mobility * (2.0 * np.pi * frequencies)
    one = track_decay_rate(mobility, frequencies_hz=frequencies)
    two = track_decay_rate(accelerance, frequencies_hz=frequencies)
    np.testing.assert_allclose(
        one.decay_rates_db_per_m, two.decay_rates_db_per_m, rtol=1e-12
    )


def test_formula_2_floor_and_the_suitable_bands() -> None:
    """DR_min = 4,343/x_max; a rate below twice it is unsuitable (clause 7)."""
    positions = track_decay_excitation_positions()
    rates_db = np.array([0.1, 1.0])
    rate = track_decay_rate(
        np.exp(-np.outer(positions, rates_db / _NEPER_DB)),
        frequencies_hz=[1000.0, 2000.0],
    )
    assert rate.minimum_measurable_db_per_m == pytest.approx(4.343 / 39.6)
    np.testing.assert_array_equal(rate.suitable, [False, True])


def test_the_far_field_drop_is_judged_against_10_db() -> None:
    """6.7: the farthest response must be 10 dB below the direct one in every band."""
    positions = track_decay_excitation_positions()
    rates_db = np.array([0.3, 1.0])
    rate = track_decay_rate(
        np.exp(-np.outer(positions, rates_db / _NEPER_DB)),
        frequencies_hz=[1000.0, 2000.0],
    )
    drops = rate.far_field_drops_db
    assert drops is not None
    np.testing.assert_allclose(drops, rates_db * 39.6)
    assert rate.far_field_sufficient is True
    shallow = track_decay_rate(
        np.exp(-np.outer(positions, [0.2 / _NEPER_DB])), frequencies_hz=[1000.0]
    )
    assert shallow.far_field_sufficient is False


def test_a_rate_of_exactly_twice_the_floor_is_suitable() -> None:
    """Clause 7: a band is unsuitable when DR_min is greater than half its rate.

    On the Figure 2 grid, rates of 1,95, 2 and 2,05 times DR_min are
    unsuitable, suitable and suitable.
    """
    positions = track_decay_excitation_positions()
    floor = 4.343 / positions[-1]
    rates = TrackDecayRate(
        "vertical",
        [250.0, 315.0, 400.0],
        [1.95 * floor, 2.0 * floor, 2.05 * floor],
        distances_m=positions,
        responses=np.ones((positions.size, 3)),
    )
    assert rates.minimum_measurable_db_per_m == floor
    np.testing.assert_array_equal(rates.suitable, [False, True, True])


@pytest.mark.parametrize(("drop_db", "sufficient"), [(9.8, False), (10.2, True)])
def test_a_far_field_drop_of_10_db_is_the_boundary(
    drop_db: float, *, sufficient: bool
) -> None:
    """6.7: a response 9,8 dB down at the farthest position is short, 10,2 dB down is not."""
    positions = track_decay_excitation_positions()
    rate = track_decay_rate(
        np.exp(-np.outer(positions, [drop_db / positions[-1] / _NEPER_DB])),
        frequencies_hz=[1000.0],
    )
    drops = rate.far_field_drops_db
    assert drops is not None
    np.testing.assert_allclose(drops, [drop_db])
    assert rate.far_field_sufficient is sufficient


@pytest.mark.parametrize(
    ("direct_db", "farthest_db"), [(20.5, 10.5), (14.0, 4.0), (6.6, -3.4)]
)
def test_a_far_field_drop_of_exactly_10_db_is_sufficient(
    direct_db: float, farthest_db: float
) -> None:
    """6.7 asks for at least 10 dB, and levels 10,0 dB apart are exactly that.

    Carried to magnitudes and back, each of these pairs comes out a few units
    in the last place under 10 dB; the verdict must not hang on them.
    """
    levels_db = np.array([[direct_db], [direct_db - 5.0], [farthest_db]])
    rate = track_decay_rate(
        10.0 ** (levels_db / 20.0), frequencies_hz=[1000.0], distances_m=[0.0, 0.6, 1.2]
    )
    drops = rate.far_field_drops_db
    assert drops is not None
    assert drops[0] == pytest.approx(10.0, abs=1e-12)
    assert rate.far_field_sufficient is True


def test_a_measured_rate_of_exactly_twice_the_floor_is_suitable() -> None:
    """Clause 7 on measured responses: exactly twice DR_min is not less than twice.

    Positions 0, 0,5 m and 1,4 m stand for 0,25 m, 0,7 m and 0,9 m of rail
    (A.2), so magnitudes 1, 0,75 and 0,25 sum to 0,25 + 0,5625 x 0,7 +
    0,0625 x 0,9 = 0,7 m, half of x_max, and the rate is exactly twice the
    floor; binary arithmetic lands it a few units in the last place under.
    """
    rate = track_decay_rate(
        [[1.0], [0.75], [0.25]], frequencies_hz=[1000.0], distances_m=[0.0, 0.5, 1.4]
    )
    floor = rate.minimum_measurable_db_per_m
    assert floor is not None
    assert rate.decay_rates_db_per_m[0] == pytest.approx(2.0 * floor, rel=1e-12)
    np.testing.assert_array_equal(rate.suitable, [True])


def test_rates_from_a_report_carry_no_grid() -> None:
    """A TrackDecayRate built from printed rates has no floor and no drop to judge."""
    rates = TrackDecayRate("lateral", [250.0, 315.0], [2.5, 1.9])
    assert rates.minimum_measurable_db_per_m is None
    assert rates.far_field_sufficient is None
    assert rates.suitable.all()
    assert rates.rate_at(315.0) == pytest.approx(1.9)


def test_a_missing_band_is_a_key_error() -> None:
    """rate_at names the band it could not find."""
    rates = TrackDecayRate("vertical", [250.0], [2.5])
    with pytest.raises(KeyError, match="no band at 400 Hz"):
        rates.rate_at(400.0)


def test_an_unknown_direction_is_refused() -> None:
    """6.6 measures the vertical and the lateral responses only."""
    with pytest.raises(ValueError, match="'direction' must be one of"):
        TrackDecayRate("longitudinal", [250.0], [2.5])


@pytest.mark.parametrize(
    "frequencies_hz",
    [[250.0, 250.0, 315.0], [315.0, 250.0, 400.0], [250.0, 251.0, 315.0]],
    ids=["repeated", "decreasing", "same band"],
)
def test_the_bands_are_distinct_and_increasing(frequencies_hz: list[float]) -> None:
    """A band given twice would let the verdict read one rate and rate_at the other."""
    with pytest.raises(
        ValueError, match="'frequencies_hz' must name distinct one-third octave bands"
    ):
        TrackDecayRate("vertical", frequencies_hz, [0.1, 3.0, 3.0])


def test_measured_rates_need_distinct_bands_too() -> None:
    """The same check holds for rates computed from responses."""
    responses = np.ones((29, 2))
    with pytest.raises(
        ValueError, match="'frequencies_hz' must name distinct one-third octave bands"
    ):
        track_decay_rate(responses, frequencies_hz=[250.0, 250.0])


def test_the_grid_starts_at_the_accelerometer() -> None:
    """The direct response is at 0 m, and the positions increase."""
    responses = np.ones((2, 1))
    with pytest.raises(
        ValueError, match="'distances_m' must start at the accelerometer"
    ):
        track_decay_rate(responses, frequencies_hz=[1000.0], distances_m=[0.1, 0.5])


def test_one_row_per_position() -> None:
    """The responses and the grid agree on the number of positions."""
    responses = np.ones((3, 1))
    with pytest.raises(ValueError, match="'responses' has 3 rows for 29 positions"):
        track_decay_rate(responses, frequencies_hz=[1000.0])


def test_responses_are_positive_magnitudes() -> None:
    """A level in decibels is not a magnitude."""
    levels = -np.ones((29, 1))
    with pytest.raises(ValueError, match="'responses' are magnitudes"):
        track_decay_rate(levels, frequencies_hz=[1000.0])


@pytest.mark.parametrize(
    ("distances_m", "message"),
    [
        ([0.0, -1.0], _GRID_ORDER),
        ([0.0, 0.6, 0.6], _GRID_ORDER),
        ([0.1, 0.6], _GRID_ORDER),
        ([0.0], "'distances_m' needs at least the direct position and one more"),
        (
            [[0.0, 0.6]],
            "'distances_m' must be one-dimensional, one distance per position",
        ),
        ([0.0, math.nan], "'distances_m' must be finite"),
        ([0.0, math.inf], "'distances_m' must be finite"),
    ],
    ids=["backwards", "repeated", "off-zero", "one", "two-dimensional", "nan", "inf"],
)
def test_a_rate_built_directly_needs_the_grid_of_6_7(
    distances_m: list[float], message: str
) -> None:
    """6.7, Figure 2 and A.2: the direct position at 0 m, then strictly farther ones.

    The constructor refuses what track_decay_rate refuses, so a grid that runs
    backwards cannot make the floor of Formula 2 or the far-field drop pass.
    """
    responses = np.ones((np.asarray(distances_m).size, 1))
    with pytest.raises(ValueError, match=f"^{message}\\.$"):
        TrackDecayRate(
            "vertical", [250.0], [2.5], distances_m=distances_m, responses=responses
        )


@pytest.mark.parametrize(
    "direct", [0.0, -1.0, math.nan, math.inf], ids=["zero", "negative", "nan", "inf"]
)
def test_a_rate_built_directly_needs_positive_finite_magnitudes(direct: float) -> None:
    """Formula 1 divides by the direct response, and a level in decibels is not a magnitude."""
    responses = np.array([[direct], [0.1]])
    with pytest.raises(ValueError, match="'responses' are magnitudes"):
        TrackDecayRate(
            "vertical", [250.0], [2.5], distances_m=[0.0, 0.6], responses=responses
        )


def test_a_rate_built_directly_needs_one_row_per_position() -> None:
    """The constructor counts the rows against the grid, as track_decay_rate does."""
    responses = np.ones((3, 1))
    with pytest.raises(ValueError, match="'responses' has 3 rows for 2 positions"):
        TrackDecayRate(
            "vertical", [250.0], [2.5], distances_m=[0.0, 0.6], responses=responses
        )


def test_a_rate_built_directly_on_a_valid_grid_is_judged() -> None:
    """A grid the constructor accepts gives the floor of Formula 2 and the drop of 6.7."""
    rates = TrackDecayRate(
        "vertical",
        [250.0],
        [2.5],
        distances_m=[0.0, 0.6, 1.2],
        responses=[1.0, 0.5, 0.25],
    )
    assert rates.responses is not None
    assert rates.responses.shape == (3, 1)
    assert rates.minimum_measurable_db_per_m == pytest.approx(4.343 / 1.2)
    assert rates.far_field_sufficient is True


def test_the_arrays_are_read_only() -> None:
    """A result never hands out a writable array."""
    rate = track_decay_rate(np.ones((29, 1)), frequencies_hz=[1000.0])
    with pytest.raises(ValueError, match="assignment destination is read-only"):
        rate.decay_rates_db_per_m[0] = 1.0


def test_the_plot_is_logarithmic_between_the_limits_of_9_2() -> None:
    """EN 15461 9.2: 0,01 dB/m to 100 dB/m, with the lower limit drawn."""
    rates = TrackDecayRate("vertical", [250.0, 315.0, 400.0], [2.5, 2.4, 7.0])
    ax = rates.plot(
        limit_db_per_m=environment.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["vertical"]
    )
    assert ax.get_yscale() == "log"
    assert ax.get_ylim() == pytest.approx((0.01, 100.0))
    assert [line.get_label() for line in ax.get_lines()] == ["Measured", "Lower limit"]
    plt.close(ax.figure)
