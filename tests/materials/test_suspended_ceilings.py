#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the suspended-ceiling test code (EN 16487:2014).

The standard prints no worked example. Its oracles are the numbers it fixes:
the specimen geometry of 4.1.1, the air-absorption cap of 4.2.1, and Table 1,
the reproducibility of the round robin behind it.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from phonometry import materials
from phonometry.materials.absorbers.suspended_ceilings import (
    AIR_CORRECTION_LIMIT,
    CEILING_UNCERTAINTY,
    EN16487_COVERAGE_FACTOR,
    MAX_DEFLECTION_MM,
    MIN_FIXTURE_DENSITY_KG_M2,
    MIN_RELATIVE_HUMIDITY_PERCENT,
    MIN_ROOM_EDGE_ANGLE_DEG,
    MOUNTING_TYPES,
    SUBSTRUCTURE_LIMITS_MM,
    TARGET_SPECIMEN_AREA_M2,
    TEST_OBJECT_SIZE_M,
    TYPE_E_DEPTH_MM,
    WEIGHTED_UNCERTAINTY,
    SuspendedCeilingWarning,
)


def test_the_table_one_figures_are_the_printed_ones() -> None:
    assert CEILING_UNCERTAINTY == {
        125.0: 0.23,
        250.0: 0.23,
        500.0: 0.11,
        1000.0: 0.10,
        2000.0: 0.10,
        4000.0: 0.13,
    }
    assert WEIGHTED_UNCERTAINTY == 0.08
    assert EN16487_COVERAGE_FACTOR == 2.8


def test_the_uncertainty_falls_with_frequency_until_four_kilohertz() -> None:
    got = materials.reproducibility_uncertainty()
    assert got.tolist() == [0.23, 0.23, 0.11, 0.10, 0.10, 0.13]
    assert got[0] > got[3]
    assert got[-1] > got[-2]


def test_one_band_can_be_asked_for_by_frequency() -> None:
    assert materials.reproducibility_uncertainty([500.0]).tolist() == [0.11]


def test_a_band_table_one_does_not_print_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 1"):
        materials.reproducibility_uncertainty([63.0])


def test_the_uncertainty_is_a_coverage_factor_over_a_standard_deviation() -> None:
    """The note under Table 1: ISO 5725-6 with a coverage factor of 2,8."""
    sigma = CEILING_UNCERTAINTY[1000.0] / EN16487_COVERAGE_FACTOR
    assert sigma == pytest.approx(0.0357, abs=1e-4)


def test_the_air_correction_is_four_volumes_over_the_area() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        got = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.01],
            attenuation_empty=[0.008],
        )
    assert got[0] == pytest.approx(4.0 * 200.0 * 0.002 / 10.8)


def test_a_dry_room_can_pass_the_cap_the_clause_sets() -> None:
    """A difference of 1e-4 per metre in a 200 m3 room is 0,0074, well under."""
    got = materials.air_absorption_correction(
        volume_m3=200.0,
        specimen_area_m2=10.8,
        attenuation_with=[0.0101],
        attenuation_empty=[0.0100],
    )
    assert abs(got[0]) < AIR_CORRECTION_LIMIT


def test_the_correction_is_zero_when_the_air_did_not_change() -> None:
    got = materials.air_absorption_correction(
        volume_m3=200.0,
        specimen_area_m2=10.8,
        attenuation_with=[0.01, 0.02],
        attenuation_empty=[0.01, 0.02],
    )
    assert np.allclose(got, 0.0)


def test_mismatched_attenuation_spectra_are_refused() -> None:
    with pytest.raises(ValueError, match="band for band"):
        materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.01, 0.02],
            attenuation_empty=[0.01],
        )


def test_the_printed_geometry_is_the_printed_geometry() -> None:
    assert TARGET_SPECIMEN_AREA_M2 == 10.80
    assert TEST_OBJECT_SIZE_M == (0.6, 0.6)
    assert MIN_ROOM_EDGE_ANGLE_DEG == 10.0
    assert MIN_FIXTURE_DENSITY_KG_M2 == 20.0
    assert TYPE_E_DEPTH_MM == 200.0
    assert MAX_DEFLECTION_MM == 5.0
    assert SUBSTRUCTURE_LIMITS_MM == (30.0, 50.0)
    assert MIN_RELATIVE_HUMIDITY_PERCENT == 50.0


def test_a_conforming_arrangement_passes() -> None:
    check = materials.check_ceiling_specimen(
        area_m2=10.8,
        depth_mm=200.0,
        deflection_mm=3.0,
        substructure_width_mm=25.0,
        substructure_height_mm=45.0,
    )
    assert check.satisfied is True
    assert check.ce_marking_depth is True
    assert check.area_error_m2 == pytest.approx(0.0)


def test_a_sagging_ceiling_fails_the_deflection_rule() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.1.1.2.3.5"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, deflection_mm=8.0
        )
    assert check.deflection_ok is False
    assert check.satisfied is False


def test_a_deep_substructure_fails_its_own_rule() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="substructure"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, substructure_height_mm=70.0
        )
    assert check.substructure_ok is False


def test_a_light_mounting_fixture_fails() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.1.1.1.6"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, fixture_density_kg_m2=8.0
        )
    assert check.fixture_ok is False


def test_another_depth_is_allowed_but_is_not_the_ce_marking_one() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="CE marking"):
        check = materials.check_ceiling_specimen(area_m2=10.8, depth_mm=400.0)
    assert check.satisfied is True
    assert check.ce_marking_depth is False


def test_the_ce_marking_depth_belongs_to_the_type_e_mounting_alone() -> None:
    """4.1.1.2.3.1 fixes 200 mm for type E, so type A cannot reach it."""
    check = materials.check_ceiling_specimen(
        area_m2=10.8, mounting="A", depth_mm=TYPE_E_DEPTH_MM
    )
    assert check.ce_marking_depth is False
    assert check.satisfied is True


def test_a_type_e_arrangement_without_a_depth_is_refused() -> None:
    with pytest.raises(ValueError, match="depth_mm"):
        materials.check_ceiling_specimen(area_m2=10.8)


def test_the_four_mountings_are_the_admitted_ones() -> None:
    assert sorted(MOUNTING_TYPES) == ["A", "B", "E", "J"]
    assert "air space" in materials.mounting_type("E")
    assert "3 mm" in materials.mounting_type("B")


def test_an_unknown_mounting_letter_is_refused() -> None:
    with pytest.raises(ValueError, match="mounting"):
        materials.check_ceiling_specimen(area_m2=10.8, mounting="Z", depth_mm=200.0)


@pytest.mark.parametrize(
    "field",
    [
        "deflection_mm",
        "substructure_width_mm",
        "substructure_height_mm",
        "fixture_density_kg_m2",
    ],
)
def test_a_negative_geometry_is_refused_rather_than_judged(field: str) -> None:
    """An upper bound alone would let a negative length pass as conforming."""
    with pytest.raises(ValueError, match=field):
        materials.check_ceiling_specimen(area_m2=10.8, depth_mm=200.0, **{field: -1.0})


@pytest.mark.parametrize("value", [float("-inf"), float("inf"), float("nan")])
def test_a_non_finite_geometry_is_refused(value: float) -> None:
    with pytest.raises(ValueError, match="deflection_mm"):
        materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, deflection_mm=value
        )


def test_an_area_away_from_the_target_is_reported_and_not_warned_about() -> None:
    # 4.1.1.1.1 asks for an area "as close to 10,80 m2 as possible", which is a
    # target and not a tolerance: the difference is reported, and nothing in the
    # clause makes one number of it a failure.
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        check = materials.check_ceiling_specimen(area_m2=9.6, depth_mm=200.0)
    assert check.area_error_m2 == pytest.approx(-1.2)
    assert check.satisfied is True


def test_an_air_correction_over_the_cap_is_warned_about() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        correction = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.0005, 0.0230],
            attenuation_empty=[0.0004, 0.0210],
        )
    assert float(correction[-1]) > materials.AIR_CORRECTION_LIMIT


def test_a_correction_inside_the_cap_is_silent() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        correction = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.0011, 0.0035],
            attenuation_empty=[0.0010, 0.0030],
        )
    assert float(max(correction)) < materials.AIR_CORRECTION_LIMIT
