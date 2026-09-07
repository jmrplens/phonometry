#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the guideline values of DIN 4150-3:1999-02.

Anchored on the printed tables: Table 1 (short-term, three building classes,
three foundation frequency bands and the topmost floor plane), Table 2
(buried pipelines by material), Table 3 (long-term, topmost floor plane), and
the three rules that travel with them: the 20 mm/s of 5.2 for floors, the
doubling of row 1 for massive engineering structures (5.1), and the halving
of Table 2 for long-term vibration (6.3).

Between the printed frequencies the guideline is read off Bild 1, which joins
the corner values by straight lines on a linear frequency axis; the midpoints
tested here are read from that figure and not from any other source.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import vibration
from phonometry.vibration.structural import building_damage as bd

# Table 1, foundation columns: (class, frequency Hz, guideline mm/s), taken at
# the frequencies the table prints its corner values at.
TABLE_1_CORNERS = [
    ("commercial", 1.0, 20.0),
    ("commercial", 10.0, 20.0),
    ("commercial", 50.0, 40.0),
    ("commercial", 100.0, 50.0),
    ("residential", 1.0, 5.0),
    ("residential", 10.0, 5.0),
    ("residential", 50.0, 15.0),
    ("residential", 100.0, 20.0),
    ("sensitive", 1.0, 3.0),
    ("sensitive", 10.0, 3.0),
    ("sensitive", 50.0, 8.0),
    ("sensitive", 100.0, 10.0),
]


@pytest.mark.parametrize(("cls", "freq", "expected"), TABLE_1_CORNERS)
def test_table_1_foundation_corners(cls: str, freq: float, expected: float) -> None:
    """Every printed corner value of Table 1 comes back unchanged."""
    assert bd.guideline_velocity(cls, freq) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("cls", "expected"),
    [("commercial", 40.0), ("residential", 15.0), ("sensitive", 8.0)],
)
def test_table_1_top_floor_is_one_number(cls: str, expected: float) -> None:
    """The last column of Table 1 holds at every frequency, so none is asked for."""
    assert bd.guideline_velocity(cls, location="top_floor") == pytest.approx(expected)


@pytest.mark.parametrize(
    ("cls", "expected"),
    [("commercial", 10.0), ("residential", 5.0), ("sensitive", 2.5)],
)
def test_table_3_long_term(cls: str, expected: float) -> None:
    """Table 3: one value per class in the topmost floor plane."""
    got = bd.guideline_velocity(cls, location="top_floor", duration="long_term")
    assert got == pytest.approx(expected)


@pytest.mark.parametrize(
    ("material", "expected"),
    [
        ("welded_steel", 100.0),
        ("concrete_or_flanged_metal", 80.0),
        ("masonry_or_plastic", 50.0),
    ],
)
def test_table_2_pipelines(material: str, expected: float) -> None:
    """Table 2, and 6.3 halving it for long-term vibration."""
    assert bd.pipeline_guideline_velocity(material) == pytest.approx(expected)
    got = bd.pipeline_guideline_velocity(material, duration="long_term")
    assert got == pytest.approx(0.5 * expected)


def test_the_band_between_corners_is_the_straight_line_of_bild_1() -> None:
    """Bild 1 joins the corners by straight lines on a linear frequency axis.

    Table 1 prints a band as a range, "5 bis 15" for a dwelling between 10 Hz
    and 50 Hz, and the range alone would leave the value at 30 Hz undecided.
    Bild 1 decides it: halfway across the band in frequency is halfway up it
    in velocity, which puts a dwelling at 10 mm/s and not at 5 or 15.
    """
    assert bd.guideline_velocity("residential", 30.0) == pytest.approx(10.0)
    assert bd.guideline_velocity("commercial", 30.0) == pytest.approx(30.0)
    assert bd.guideline_velocity("sensitive", 75.0) == pytest.approx(9.0)
    # A quarter of the way into the 10 Hz to 50 Hz band of row 1.
    assert bd.guideline_velocity("commercial", 20.0) == pytest.approx(25.0)


def test_below_10_hz_and_above_100_hz_are_flat() -> None:
    """The first band is constant, and 5.1 lets 100 Hz stand for anything faster."""
    assert bd.guideline_velocity("residential", 1.0) == pytest.approx(5.0)
    assert bd.guideline_velocity("residential", 4.0) == pytest.approx(5.0)
    assert bd.guideline_velocity("residential", 250.0) == pytest.approx(20.0)


def test_the_curve_is_monotonic_across_the_printed_range() -> None:
    """A building takes more of a fast wiggle than a slow one, at every class."""
    f = np.linspace(1.0, 100.0, 400)
    for cls in bd.BUILDING_CLASSES:
        v = np.asarray(bd.guideline_velocity(cls, f))
        assert np.all(np.diff(v) >= -1e-12)


def test_an_array_of_frequencies_comes_back_as_an_array() -> None:
    got = bd.guideline_velocity("commercial", [1.0, 10.0, 50.0, 100.0])
    assert isinstance(got, np.ndarray)
    assert got == pytest.approx([20.0, 20.0, 40.0, 50.0])


def test_massive_structures_take_twice_row_1() -> None:
    """5.1: massive engineering structures may double the row 1 values."""
    plain = bd.guideline_velocity("commercial", 50.0)
    doubled = bd.guideline_velocity("commercial", 50.0, massive_structure=True)
    assert doubled == pytest.approx(2.0 * plain)
    assert doubled == pytest.approx(80.0)


def test_the_doubling_is_written_for_row_1_alone() -> None:
    with pytest.raises(ValueError, match=r"applies to the commercial row"):
        bd.guideline_velocity("residential", 50.0, massive_structure=True)


def test_the_doubling_does_not_reach_table_3() -> None:
    """Row 1 of Table 1 is a row of Table 1, and Table 3 is another table.

    Clause 5.1 is a sentence of Clause 5, which is short-term vibration, and
    it names Table 1. Clause 6 prints Table 3 and says nothing about raising
    it for a massive structure, so the allowance stops here rather than being
    carried over by analogy.
    """
    with pytest.raises(ValueError, match=r"Table 3 carries no such allowance"):
        bd.guideline_velocity(
            "commercial",
            location="top_floor",
            duration="long_term",
            massive_structure=True,
        )
    plain = bd.guideline_velocity(
        "commercial", location="top_floor", duration="long_term"
    )
    assert plain == pytest.approx(10.0)


def test_the_doubling_does_reach_the_topmost_floor_plane() -> None:
    """5.1 names row 1, and the topmost floor plane is a column of that row."""
    got = bd.guideline_velocity(
        "commercial", location="top_floor", massive_structure=True
    )
    assert got == pytest.approx(80.0)


def test_table_3_has_no_foundation_column() -> None:
    with pytest.raises(ValueError, match=r"topmost floor plane only"):
        bd.guideline_velocity("residential", 10.0, duration="long_term")


def test_the_short_term_foundation_case_needs_a_frequency() -> None:
    with pytest.raises(ValueError, match=r"'frequency' is required"):
        bd.guideline_velocity("residential")


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"building_class": "palace"}, r"'building_class' must be one of"),
        ({"building_class": "residential", "location": "roof"}, r"'location' must be"),
        ({"building_class": "residential", "duration": "often"}, r"'duration' must be"),
    ],
)
def test_a_name_outside_its_choices_is_refused(kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        bd.guideline_velocity(frequency=10.0, **kwargs)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.inf, math.nan])
def test_a_frequency_that_is_not_a_frequency_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match=r"'frequency' must be positive and finite"):
        bd.guideline_velocity("residential", bad)


def test_floor_and_massive_constants_are_the_printed_ones() -> None:
    """5.2 and 5.1, as numbers rather than prose."""
    assert bd.FLOOR_VERTICAL_MM_S == pytest.approx(20.0)
    assert bd.MASSIVE_STRUCTURE_FACTOR == pytest.approx(2.0)
    assert bd.PIPELINE_LONG_TERM_FACTOR == pytest.approx(0.5)


def test_the_storey_estimate_of_6_4() -> None:
    """``f_i ~ 10 / n``, offered from about five storeys up."""
    assert bd.storey_fundamental_frequency(5) == pytest.approx(2.0)
    assert bd.storey_fundamental_frequency(8) == pytest.approx(1.25)
    assert bd.STOREY_FREQUENCY_MIN_STOREYS == 5


@pytest.mark.parametrize("bad", [0, -3])
def test_a_building_with_no_storeys_is_refused(bad: int) -> None:
    with pytest.raises(ValueError, match=r"'storeys' must be at least 1"):
        bd.storey_fundamental_frequency(bad)


def test_a_fractional_storey_count_is_refused() -> None:
    with pytest.raises(ValueError, match=r"'storeys' must be an integer"):
        bd.storey_fundamental_frequency(4.5)  # type: ignore[arg-type]


def test_bending_stress_is_formula_1() -> None:
    """Formula (1) of 6.2, term by term.

    Concrete at ``E_dyn`` = 30 GPa and 2400 kg/m3, a beam carrying nothing
    else, first mode: the square root is 1,73 times the characteristic
    impedance of the material, so the stress is linear in the velocity and
    the system dimensions never appear.
    """
    e_dyn, rho = 3.0e10, 2400.0
    sigma = bd.bending_stress(0.01, dynamic_modulus_pa=e_dyn, density_kg_m3=rho)
    assert sigma == pytest.approx(1.73 * math.sqrt(e_dyn * rho) * 0.01)


def test_bending_stress_scales_with_the_load_and_the_mode() -> None:
    kw = {"dynamic_modulus_pa": 3.0e10, "density_kg_m3": 2400.0}
    base = bd.bending_stress(0.01, **kw)
    assert bd.bending_stress(0.01, load_ratio=4.0, **kw) == pytest.approx(2.0 * base)
    assert bd.bending_stress(0.01, mode_factor=1.3, **kw) == pytest.approx(1.3 * base)
    assert bd.bending_stress(0.02, **kw) == pytest.approx(2.0 * base)


def test_bending_stress_takes_an_array_of_velocities() -> None:
    kw = {"dynamic_modulus_pa": 3.0e10, "density_kg_m3": 2400.0}
    got = bd.bending_stress([0.0, 0.01, 0.02], **kw)
    assert isinstance(got, np.ndarray)
    assert got[0] == pytest.approx(0.0)
    assert got[2] == pytest.approx(2.0 * got[1])


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"dynamic_modulus_pa": 0.0}, r"'dynamic_modulus_pa'"),
        ({"density_kg_m3": -1.0}, r"'density_kg_m3'"),
        ({"load_ratio": 0.0}, r"'load_ratio'"),
        ({"mode_factor": math.nan}, r"'mode_factor'"),
    ],
)
def test_bending_stress_refuses_an_impossible_material(
    kwargs: dict, match: str
) -> None:
    full = {"dynamic_modulus_pa": 3.0e10, "density_kg_m3": 2400.0, **kwargs}
    with pytest.raises(ValueError, match=match):
        bd.bending_stress(0.01, **full)


def test_bending_stress_refuses_a_negative_velocity() -> None:
    kw = {"dynamic_modulus_pa": 3.0e10, "density_kg_m3": 2400.0}
    with pytest.raises(ValueError, match=r"'peak_velocity_m_s' must be non-negative"):
        bd.bending_stress(-0.01, **kw)


def test_the_assessment_carries_the_comparison() -> None:
    got = bd.assess_building_vibration(
        4.0, building_class="residential", frequency_hz=30.0
    )
    assert got.guideline_mm_s == pytest.approx(10.0)
    assert got.ratio == pytest.approx(0.4)
    assert got.within_guideline


def test_the_guideline_itself_is_within_the_guideline() -> None:
    """The comparison of 5.1 is "keep to", so the value itself passes."""
    got = bd.assess_building_vibration(
        15.0, building_class="residential", location="top_floor"
    )
    assert got.frequency_hz is None
    assert got.within_guideline
    over = bd.assess_building_vibration(
        15.1, building_class="residential", location="top_floor"
    )
    assert not over.within_guideline
    assert over.ratio > 1.0


@pytest.mark.parametrize("bad", [0.0, -2.0, math.nan])
def test_the_assessment_refuses_a_velocity_that_is_not_one(bad: float) -> None:
    with pytest.raises(ValueError, match=r"'velocity_mm_s'"):
        bd.assess_building_vibration(
            bad, building_class="residential", frequency_hz=10.0
        )


def test_the_curve_helper_returns_the_four_corners() -> None:
    freq, values = bd.foundation_guideline_curve("sensitive")
    assert freq == pytest.approx([1.0, 10.0, 50.0, 100.0])
    assert values == pytest.approx([3.0, 3.0, 8.0, 10.0])


def test_the_curve_helper_samples_where_it_is_asked_to() -> None:
    freq, values = bd.foundation_guideline_curve("residential", [30.0])
    assert freq == pytest.approx([30.0])
    assert values == pytest.approx([10.0])


def test_the_names_are_exported_from_the_domain() -> None:
    """The module is reached through ``phonometry.vibration`` like its siblings."""
    assert vibration.guideline_velocity("residential", 10.0) == pytest.approx(5.0)
    assert vibration.PIPELINE_MM_S["welded_steel"] == pytest.approx(100.0)
    assert vibration.BUILDING_CLASSES == bd.BUILDING_CLASSES
