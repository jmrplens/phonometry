#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the seat vibration of ISO 10326-1:2016.

Anchored on the printed clauses: the SEAT factor of Formula (2), the
correction to an intended input of 10.2.3 (whose printed Formula (3) is an
identity and is recorded in the errata), the transmissibility at resonance of
Formula (5), the ± 5 % agreement three consecutive runs have to keep (10.2.1
and 10.3), and the test masses of 10.3 and 9.5.1.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from phonometry import vibration
from phonometry.vibration.human import seat_vibration as st

if TYPE_CHECKING:
    from collections.abc import Callable

# Three runs at the platform and three at the seat, agreeing well inside the
# ± 5 % the standard allows.
PLATFORM_RUNS = (1.02, 1.00, 0.99)
SEAT_RUNS = (0.72, 0.70, 0.71)


def test_the_seat_factor_is_the_ratio_of_formula_2() -> None:
    assert st.seat_factor(0.7, 1.0) == pytest.approx(0.7)
    assert st.seat_factor(1.4, 1.0) == pytest.approx(1.4)


def test_a_seat_factor_of_one_is_a_plank() -> None:
    """The number the standard's two verdicts turn on."""
    assert st.seat_factor(0.9, 0.9) == pytest.approx(st.UNITY_TRANSMISSION)


def test_the_correction_of_10_2_3_is_formula_4_with_2_substituted() -> None:
    """The printed Formula (3) is an identity; this is what it meant.

    ``a*_wS = a_wS a*_wP / a_wP``, which is Formula (4) with the SEAT factor
    of Formula (2) substituted into it. Both routes have to give the same
    number, which is the argument the errata entry rests on.
    """
    seat, platform, intended = 0.70, 1.00, 1.10
    corrected = st.corrected_seat_acceleration(seat, platform, intended)
    assert corrected == pytest.approx(seat * intended / platform)
    assert corrected == pytest.approx(st.seat_factor(seat, platform) * intended)


def test_the_correction_does_nothing_when_the_input_was_delivered() -> None:
    """A simulator that hit its target leaves the seat magnitude alone."""
    got = st.corrected_seat_acceleration(0.70, 1.00, 1.00)
    assert got == pytest.approx(0.70)


def test_the_transmissibility_at_resonance_of_formula_5() -> None:
    """Same arithmetic as the SEAT factor, different test and different meaning."""
    assert st.resonance_transmissibility(2.4, 1.2) == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("func", "kwargs"),
    [
        (st.seat_factor, {"seat_acceleration": 0.0, "platform_acceleration": 1.0}),
        (st.seat_factor, {"seat_acceleration": 1.0, "platform_acceleration": -1.0}),
        (
            st.resonance_transmissibility,
            {"seat_acceleration": math.nan, "platform_acceleration": 1.0},
        ),
    ],
)
def test_an_acceleration_that_is_not_one_is_refused(
    func: Callable[..., float], kwargs: dict
) -> None:
    with pytest.raises(ValueError, match=r"acceleration"):
        func(**kwargs)


def test_the_correction_refuses_an_intended_input_that_is_not_one() -> None:
    with pytest.raises(ValueError, match=r"intended_platform_acceleration"):
        st.corrected_seat_acceleration(0.7, 1.0, 0.0)


def test_the_mean_of_three_agreeing_runs() -> None:
    assert st.mean_of_test_runs(PLATFORM_RUNS) == pytest.approx(
        sum(PLATFORM_RUNS) / 3.0
    )


def test_runs_that_disagree_by_more_than_five_percent_are_refused() -> None:
    """10.2.1 asks for three runs within ± 5 % of their mean, and means it."""
    with pytest.raises(ValueError, match=r"more than the 5 % this test allows"):
        st.mean_of_test_runs([1.0, 1.2, 1.0])


def test_the_five_percent_band_is_inclusive_at_its_edge() -> None:
    """A run exactly on the limit is inside it, which is what "within" says.

    The case is written to land on the edge in floating point, not near it:
    1,05 against a mean of 1 comes out 5,000000000000004 % away, and refusing
    that would refuse the standard's own edge for a representation error.
    """
    mean = 1.0
    edge = [mean * (1.0 - st.RUN_AGREEMENT_TOLERANCE), mean, mean * 1.05]
    assert st.mean_of_test_runs(edge) == pytest.approx(mean)


def test_a_hair_outside_the_band_is_still_outside_it() -> None:
    """The slack that keeps the edge in is not a widening of the band."""
    with pytest.raises(ValueError, match=r"more than the 5 %"):
        st.mean_of_test_runs([0.95, 1.0, 1.0501])


def test_the_tolerance_can_be_tightened() -> None:
    with pytest.raises(ValueError, match=r"more than the 1 % this test allows"):
        st.mean_of_test_runs([1.0, 1.03, 1.0], tolerance=0.01)


def test_one_run_has_no_spread_to_check() -> None:
    with pytest.raises(ValueError, match=r"at least two runs"):
        st.mean_of_test_runs([1.0])


@pytest.mark.parametrize("bad", [[0.0, 1.0, 1.0], [1.0, math.inf, 1.0]])
def test_a_run_that_is_not_an_acceleration_is_refused(bad: list) -> None:
    with pytest.raises(ValueError, match=r"'values' must be positive and finite"):
        st.mean_of_test_runs(bad)


def test_the_test_masses_are_the_printed_ones() -> None:
    """10.3 loads 75 kg ± 1 %; 9.5.1 allows 60 kg for active damping."""
    assert st.DAMPING_TEST_MASS_KG == pytest.approx(75.0)
    assert st.DAMPING_TEST_MASS_TOLERANCE == pytest.approx(0.01)
    assert st.ACTIVE_DAMPING_TEST_MASS_KG == pytest.approx(60.0)
    assert st.TEST_RUNS == 3


def test_the_test_bundles_the_runs_and_their_verdict() -> None:
    got = st.seat_transmission(SEAT_RUNS, PLATFORM_RUNS)
    assert got.platform_acceleration == pytest.approx(sum(PLATFORM_RUNS) / 3.0)
    assert got.seat_acceleration == pytest.approx(sum(SEAT_RUNS) / 3.0)
    assert got.seat_factor == pytest.approx(
        got.seat_acceleration / got.platform_acceleration
    )
    assert got.attenuates
    assert got.seat_runs == pytest.approx(SEAT_RUNS)


def test_a_seat_that_makes_the_ride_worse_does_not_attenuate() -> None:
    got = st.seat_transmission([1.30, 1.28, 1.29], PLATFORM_RUNS)
    assert not got.attenuates
    assert got.seat_factor > 1.0


def test_the_test_corrects_to_an_intended_input() -> None:
    got = st.seat_transmission(SEAT_RUNS, PLATFORM_RUNS)
    assert got.corrected_acceleration(1.10) == pytest.approx(1.10 * got.seat_factor)


def test_the_two_sides_are_measured_in_the_same_runs() -> None:
    with pytest.raises(ValueError, match=r"measured in the same runs"):
        st.seat_transmission([0.7, 0.71], PLATFORM_RUNS)


def test_a_test_whose_runs_disagree_is_refused_whole() -> None:
    with pytest.raises(ValueError, match=r"more than the 5 %"):
        st.seat_transmission([0.7, 0.9, 0.7], PLATFORM_RUNS)


def test_the_names_are_exported_from_the_domain() -> None:
    assert vibration.seat_factor(0.7, 1.0) == pytest.approx(0.7)
    assert vibration.DAMPING_TEST_MASS_KG == pytest.approx(75.0)
    assert vibration.RUN_AGREEMENT_TOLERANCE == pytest.approx(0.05)
