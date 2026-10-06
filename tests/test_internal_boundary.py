#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The settling and the half rounding every verdict at a printed limit uses.

The pairs below are decimal readings whose difference is exactly the value on
the right in decimal and a few units in the last place off it in binary, on
one side or the other. Which side is not asserted anywhere: a test that
pinned the sign of a residual would pin one machine's arithmetic. What is
asserted is that the settled value, and the rounding of a half, are the
decimal ones whichever side the subtraction lands on.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry._internal.boundary import (
    SETTLED_DECIMALS,
    round_half_away_from_zero,
    round_half_even,
    round_half_up,
    settled,
    settled_net_share,
    settled_ratio,
)


@pytest.mark.parametrize(
    ("first", "second", "difference"),
    [
        (32.3, 26.3, 6.0),
        (32.2, 26.2, 6.0),
        (35.3, 20.3, 15.0),
        (35.2, 20.2, 15.0),
        (0.35, 0.28, 0.07),
    ],
)
def test_a_decimal_difference_settles_on_its_decimal_value(
    first: float, second: float, difference: float
) -> None:
    assert float(settled(first - second)) == difference


def test_settling_keeps_nine_decimals() -> None:
    assert SETTLED_DECIMALS == 9
    assert float(settled(1.000_000_001_4)) == 1.000_000_001
    assert float(settled(1.000_000_000_4)) == 1.0


def test_settling_keeps_the_shape() -> None:
    values = np.array([[32.3 - 26.3, 32.2 - 26.2], [1.0, 2.0]])
    got = settled(values)
    assert got.shape == (2, 2)
    np.testing.assert_array_equal(got, [[6.0, 6.0], [1.0, 2.0]])


@pytest.mark.parametrize(
    ("value", "decimals", "expected"),
    [
        (64.1 - 3.6, 0, 61.0),  # 60,5 in decimal
        (128.2 - 45.7, 0, 83.0),  # 82,5 in decimal
        (2.5, 0, 3.0),
        (-2.5, 0, -2.0),
        (1.005 * 100.0, 0, 101.0),  # 100,5 in decimal
        (40.65, 1, 40.7),
        (52.35, 1, 52.4),
    ],
)
def test_round_half_up_rounds_a_decimal_half_upwards(
    value: float, decimals: int, expected: float
) -> None:
    assert float(round_half_up(value, decimals)) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (64.1 - 3.6, 61.0),
        (-(64.1 - 3.6), -61.0),
        (-20.455 * 100.0, -2046.0),
        (2.4, 2.0),
        (-2.4, -2.0),
        (0.0, 0.0),
    ],
)
def test_round_half_away_from_zero_rounds_a_decimal_half_outwards(
    value: float, expected: float
) -> None:
    assert float(round_half_away_from_zero(value)) == expected


def test_round_half_away_from_zero_keeps_decimals() -> None:
    got = round_half_away_from_zero(np.array([0.25, -0.25, 0.35]), 1)
    np.testing.assert_allclose(got, [0.3, -0.3, 0.4], atol=1e-12)


@pytest.mark.parametrize(
    "terms",
    [
        [0.3, -0.1, -0.2],  # sums a few units in the last place under zero
        [0.1, 0.2, -0.3],  # and over it
        [0.9, 0.5, -0.5, 0.2, -0.6, -0.8, -0.5, 0.6, -0.3, 0.5],
    ],
)
def test_terms_that_cancel_in_decimal_have_a_settled_net_share_of_zero(
    terms: list[float],
) -> None:
    assert abs(float(settled_net_share(terms))) <= 0.0


def test_the_net_share_keeps_its_sign_and_its_axis() -> None:
    terms = np.array([[1.0e-6, -1.0e-6], [3.0e-6, -1.0e-6]])
    np.testing.assert_allclose(settled_net_share(terms, axis=0), [1.0, -1.0])
    assert float(settled_net_share([2.0e-9, -1.0e-9])) == pytest.approx(1.0 / 3.0)


def test_a_share_of_a_power_in_watts_settles_on_its_own_scale() -> None:
    # A half of 1,28e-5 W is 0,5 settled, which nine decimals of a watt
    # could not tell from nothing.
    assert float(settled_ratio(3.5e-6 + 2.9e-6, 1.28e-5)) == 0.5
    assert float(settled_ratio(1.0, 0.0)) == 0.0
    assert np.isnan(settled_ratio(np.nan, 1.0))
    assert np.isnan(settled_ratio(1.0, np.nan))
    # A NaN part stays NaN over a zero whole too: a 0 there would answer
    # "<= 0" True where NaN answers every comparison False.
    assert np.isnan(settled_ratio(np.nan, 0.0))
    np.testing.assert_array_equal(
        np.isnan(settled_ratio([np.nan, 1.0], [0.0, 0.0])), [True, False]
    )


@pytest.mark.parametrize(
    ("value", "decimals", "expected"),
    [
        (30.9 - 15.4, 0, 16.0),  # 15,5 in decimal, under it in binary
        (30.1 - 15.6, 0, 14.0),  # 14,5 in decimal, over it in binary
        (2.5, 0, 2.0),
        (3.5, 0, 4.0),
        (-2.5, 0, -2.0),
        (2.4, 0, 2.0),
        (0.25, 1, 0.2),
        (0.35, 1, 0.4),
    ],
)
def test_round_half_even_sends_a_decimal_half_to_the_even_neighbour(
    value: float, decimals: int, expected: float
) -> None:
    assert float(round_half_even(value, decimals)) == pytest.approx(expected, abs=1e-12)
