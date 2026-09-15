#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for workroom noise prediction (ISO 11690-3:1998).

The oracle is Annex C: eight machines with their two declared emission values
in a room of 195 m2, with the level increase at each machine's own workstation
read off Figure C.1 and tabulated in Table C.2. Seven of the eight rows fall
inside the diagram and the library reproduces them within the half decibel the
diagram is drawn to; the eighth runs off the top of it.
"""

from __future__ import annotations

import pytest

from phonometry import room
from phonometry.room.workroom_prediction import (
    FITTING_DETAIL_LEVELS,
    PREDICTION_METHODS,
    ROOM_DETAIL_LEVELS,
    SOURCE_DETAIL_LEVELS,
)

#: Table C.1 and Table C.2: the machines, and what the annex reads for them.
ANNEX_C = {
    "M1": (105.0, 79.0, 9.5, 89.0),
    "M2": (98.0, 81.0, 3.0, 84.0),
    "M3": (107.0, 87.0, 5.0, 92.0),
    "M4": (94.0, 82.0, 1.0, 83.0),
    "M5": (102.0, 84.0, 4.0, 88.0),
    "M6": (96.0, 82.0, 2.0, 84.0),
    "M7": (101.0, 84.0, 3.0, 87.0),
}

#: C.2.2: the absorption area of the example room, in square metres.
ANNEX_C_ABSORPTION_M2 = 195.0


@pytest.mark.parametrize("machine", sorted(ANNEX_C))
def test_the_increase_reproduces_table_c2(machine: str) -> None:
    power, emission, printed_increase, printed_level = ANNEX_C[machine]
    increase = room.workstation_level_increase(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=ANNEX_C_ABSORPTION_M2,
    )
    level = room.workstation_level(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=ANNEX_C_ABSORPTION_M2,
    )
    assert increase == pytest.approx(printed_increase, abs=0.45)
    assert level == pytest.approx(printed_level, abs=0.45)


def test_the_eighth_machine_runs_off_the_top_of_figure_c1() -> None:
    """Table C.2 prints the edge of the diagram for M8 (see the errata)."""
    increase = room.workstation_level_increase(
        sound_power_level_db=107.0,
        emission_level_db=78.0,
        absorption_area_m2=ANNEX_C_ABSORPTION_M2,
    )
    assert increase == pytest.approx(12.4, abs=0.1)
    assert increase > 10.0


def test_a_bigger_room_adds_less() -> None:
    small = room.workstation_level_increase(
        sound_power_level_db=100.0, emission_level_db=80.0, absorption_area_m2=50.0
    )
    large = room.workstation_level_increase(
        sound_power_level_db=100.0, emission_level_db=80.0, absorption_area_m2=5000.0
    )
    assert small > large
    assert large == pytest.approx(0.3, abs=0.1)


def test_an_emission_level_above_the_power_level_is_refused() -> None:
    with pytest.raises(ValueError, match="no surface at all"):
        room.workstation_level_increase(
            sound_power_level_db=90.0, emission_level_db=95.0, absorption_area_m2=200.0
        )


def test_the_contributions_add_on_an_energy_basis() -> None:
    total = room.total_workstation_level([80.0, 80.0])
    assert total == pytest.approx(83.0103, abs=1e-3)


def test_the_background_counts_as_one_more_contribution() -> None:
    with_background = room.total_workstation_level([80.0], existing_level_db=80.0)
    assert with_background == pytest.approx(83.0103, abs=1e-3)


def test_the_fitting_density_is_the_surface_over_four_volumes() -> None:
    assert room.fitting_density(400.0, 1000.0) == pytest.approx(0.1)


def test_the_four_categories_are_the_printed_ones() -> None:
    assert sorted(PREDICTION_METHODS) == ["1", "2a", "2b", "2c"]
    assert room.prediction_method("1").family == "diffuse field"
    assert room.prediction_method("2c").family == "geometrical"
    assert len(ROOM_DETAIL_LEVELS) == 4
    assert len(FITTING_DETAIL_LEVELS) == 4
    assert len(SOURCE_DETAIL_LEVELS) == 3


def test_an_unknown_category_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 4"):
        room.prediction_method("3")


def test_the_diffuse_field_method_asks_for_the_least() -> None:
    verdict = room.detail_is_sufficient(
        "1", room_detail=1, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is True


def test_a_room_described_too_coarsely_for_ray_tracing_is_reported() -> None:
    verdict = room.detail_is_sufficient(
        "1", room_detail=4, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is False
    assert verdict.room_ok is False
    assert verdict.fittings_ok is True


def test_the_annex_d_example_matches_table_d1() -> None:
    """D.1 picks category 2a with room 2, fittings 1 and source 1."""
    verdict = room.detail_is_sufficient(
        "2a", room_detail=2, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is True


def test_a_level_no_table_prints_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 3"):
        room.detail_is_sufficient(
            "2a", room_detail=1, fitting_detail=1, source_detail=4
        )


def test_the_typical_ranges_are_the_printed_ones() -> None:
    assert room.typical_decay_range("near") == (5.0, 6.0)
    assert room.typical_decay_range("middle") == (2.0, 5.0)
    assert room.typical_decay_range("far") == (6.0, None)
    assert room.typical_excess_range("middle") == (2.0, 10.0)


def test_an_unknown_region_is_refused() -> None:
    with pytest.raises(ValueError, match="4.3"):
        room.typical_decay_range("close")
