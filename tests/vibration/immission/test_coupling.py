#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the numbers of DIN 45669-2:2005-06.

The standard is procedure, and its numbers are limits rather than results, so
these hold each one to the page it is printed on and the verdicts to both
sides of every limit.
"""

from __future__ import annotations

import pytest

from phonometry.vibration import immission as im


@pytest.mark.parametrize(
    ("direction", "limit_hz"), [("vertical", 100.0), ("horizontal", 40.0)]
)
def test_a_loose_mounting_carries_the_direction_to_its_limit(
    direction: str, limit_hz: float
) -> None:
    """5.3.2.1 and 5.3.2.2: 100 Hz vertically, 40 Hz horizontally, at 3 m/s²."""
    inside = im.check_loose_mounting(3.0, limit_hz, direction=direction)
    assert inside.acceptable
    assert inside.frequency_limit_hz == limit_hz
    assert inside.peak_acceleration_limit_m_s2 == 3.0
    too_high = im.check_loose_mounting(3.0, limit_hz * 1.01, direction=direction)
    assert not too_high.acceptable
    too_strong = im.check_loose_mounting(3.01, limit_hz, direction=direction)
    assert not too_strong.acceptable


def test_a_soft_covering_has_the_same_limits_and_needs_the_spiked_device() -> None:
    """5.3.3: the limits do not change, what the transducer stands on does."""
    hard = im.check_loose_mounting(1.0, 80.0, direction="vertical")
    soft = im.check_loose_mounting(1.0, 80.0, direction="vertical", surface="soft")
    assert soft.acceptable == hard.acceptable
    assert soft.frequency_limit_hz == hard.frequency_limit_hz
    assert "spikes" in soft.device
    assert "rounded feet" in hard.device
    assert im.SPIKED_DEVICE_MASS_KG == 2.5


def test_wax_carries_a_sensitive_hard_surface_horizontally_to_80_hz() -> None:
    """Table 1, the one mounting that goes beyond the loose limit."""
    assert im.WAX_MOUNTING_HORIZONTAL_LIMIT_HZ == 80.0
    assert (
        im.WAX_MOUNTING_HORIZONTAL_LIMIT_HZ > im.LOOSE_MOUNTING_LIMITS_HZ["horizontal"]
    )


def test_table_3_by_quantity_and_class() -> None:
    """Printed folio 17: 15 and 25 for r.m.s.-based values, 20 and 35 for peaks."""
    assert im.instrument_confidence_limit_percent("rms") == 15.0
    assert im.instrument_confidence_limit_percent("rms", 2) == 25.0
    assert im.instrument_confidence_limit_percent("peak", 1) == 20.0
    assert im.instrument_confidence_limit_percent("peak", 2) == 35.0
    with pytest.raises(ValueError, match="accuracy_class"):
        im.instrument_confidence_limit_percent("rms", 3)
    with pytest.raises(ValueError, match="quantity"):
        im.instrument_confidence_limit_percent("mean", 1)


def test_the_mass_loading_ratio_and_its_limit() -> None:
    """7.2.4: a hundredth of the vibrating mass."""
    assert im.mass_loading_ratio(2.5, vibrating_mass_kg=500.0) == pytest.approx(0.005)
    assert (
        im.mass_loading_ratio(2.5, vibrating_mass_kg=500.0)
        < im.MASS_LOADING_RATIO_LIMIT
    )
    assert (
        im.mass_loading_ratio(2.5, vibrating_mass_kg=200.0)
        > im.MASS_LOADING_RATIO_LIMIT
    )
    with pytest.raises(ValueError, match="vibrating_mass_kg"):
        im.mass_loading_ratio(2.5, vibrating_mass_kg=0.0)


def test_the_placement_numbers_of_5_1_4_and_5_3_4_1() -> None:
    assert im.EMISSION_POINT_TRACK_DISTANCE_M == 8.0
    assert im.CLEARANCE_TO_DISTURBING_BODY_FACTOR == 1.5
    assert im.GROUND_COUPLING_DEVIATION_DB == 15.0


def test_bad_arguments_are_refused_by_name() -> None:
    with pytest.raises(ValueError, match="direction"):
        im.check_loose_mounting(1.0, 10.0, direction="sideways")
    with pytest.raises(ValueError, match="surface"):
        im.check_loose_mounting(1.0, 10.0, direction="vertical", surface="wet")
    with pytest.raises(ValueError, match="peak_acceleration_m_s2"):
        im.check_loose_mounting(0.0, 10.0, direction="vertical")
    with pytest.raises(ValueError, match="upper_frequency_hz"):
        im.check_loose_mounting(1.0, -10.0, direction="vertical")
