#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 1683:2015 reference values: the table, and the constants that point at it.

The oracle is the printed page, UNE-EN ISO 1683:2016 (which adopts ISO
1683:2015 unchanged), PDF pages 8 and 9, printed folios 8 and 9: Table 1 for
sounds in gases, Table 2 for sounds in liquids and Table 3 for the vibratory
quantities, with the 50 nm/s of note b of Table 3. Each value below is written
here from the page, in the prefixed unit it is printed in, and converted, so a
table that stored 20 µPa as ``2e-6`` would fail rather than agree with itself.
"""

from __future__ import annotations

import dataclasses
import types

import pytest

from phonometry import emission, metrology, underwater, vibration
from phonometry.building.measurement import structure_borne_power
from phonometry.environment.assessment import impulsive_sound

_MICRO = 1e-6
_NANO = 1e-9
_PICO = 1e-12

#: (medium, key) -> (printed number, SI factor of its prefix, unit, table).
_PRINTED: dict[tuple[str, str], tuple[float, float, str, str]] = {
    ("gas", "sound_pressure"): (20.0, _MICRO, "Pa", "Table 1"),
    ("gas", "sound_exposure"): (400.0, _PICO, "Pa²·s", "Table 1"),
    ("gas", "sound_power"): (1.0, _PICO, "W", "Table 1"),
    ("gas", "sound_energy"): (1.0, _PICO, "J", "Table 1"),
    ("gas", "sound_intensity"): (1.0, _PICO, "W/m²", "Table 1"),
    ("liquid", "sound_pressure"): (1.0, _MICRO, "Pa", "Table 2"),
    ("liquid", "sound_exposure"): (1.0, _PICO, "Pa²·s", "Table 2"),
    ("liquid", "sound_power"): (1.0, _PICO, "W", "Table 2"),
    ("liquid", "sound_energy"): (1.0, _PICO, "J", "Table 2"),
    ("liquid", "sound_intensity"): (1.0, _PICO, "W/m²", "Table 2"),
    ("liquid", "particle_displacement"): (1.0, _PICO, "m", "Table 2"),
    ("liquid", "particle_velocity"): (1.0, _NANO, "m/s", "Table 2"),
    ("liquid", "particle_acceleration"): (1.0, _MICRO, "m/s²", "Table 2"),
    ("liquid", "distance"): (1.0, 1.0, "m", "Table 2"),
    ("solid", "displacement"): (1.0, _PICO, "m", "Table 3"),
    ("solid", "velocity"): (1.0, _NANO, "m/s", "Table 3"),
    ("solid", "acceleration"): (1.0, _MICRO, "m/s²", "Table 3"),
    ("solid", "force"): (1.0, _MICRO, "N", "Table 3"),
    ("solid", "velocity_alternative"): (50.0, _NANO, "m/s", "Table 3, note b"),
}

_TABLE = metrology.ISO1683_REFERENCE_VALUES


def test_the_table_holds_exactly_the_printed_rows() -> None:
    """Five rows in Table 1, nine in Table 2, four and the alternative in 3."""
    rows = {(medium, key) for medium, block in _TABLE.items() for key in block}
    assert rows == set(_PRINTED)


@pytest.mark.parametrize(("medium", "key"), sorted(_PRINTED))
def test_each_value_is_the_printed_one(medium: str, key: str) -> None:
    """The value in SI, the unit it is in, and the table it is printed in."""
    number, prefix, unit, table = _PRINTED[medium, key]
    row = _TABLE[medium][key]
    assert row.value == pytest.approx(number * prefix, rel=1e-15)
    assert row.unit == unit
    assert row.table == table
    assert row.medium == medium


def test_the_gas_exposure_is_the_pressure_squared_over_a_second() -> None:
    """(20 µPa)² s: the two rows of Table 1 agree with each other."""
    pressure = _TABLE["gas"]["sound_pressure"].value
    exposure = _TABLE["gas"]["sound_exposure"].value
    assert exposure == pytest.approx(pressure**2, rel=1e-15)


def test_the_table_cannot_be_changed_in_place() -> None:
    """A published table is shared by the process, so it refuses writes."""
    assert isinstance(_TABLE, types.MappingProxyType)
    assert all(isinstance(block, types.MappingProxyType) for block in _TABLE.values())
    row = _TABLE["gas"]["sound_pressure"]
    with pytest.raises(dataclasses.FrozenInstanceError, match="value"):
        row.value = 1.0  # type: ignore[misc]


def test_the_printed_strings_carry_the_prefix() -> None:
    """The micro sign is the one extracted text loses; the table keeps it."""
    assert _TABLE["gas"]["sound_pressure"].printed == "20 µPa"
    assert _TABLE["solid"]["force"].printed == "1 µN"
    assert _TABLE["solid"]["velocity_alternative"].printed == "50 nm/s"


def test_note_b_of_table_2_is_the_air_to_water_offset() -> None:
    """A level re 1 µPa is 10 lg(20²/1²) ≈ 26,0 dB above the same level re 20 µPa."""
    assert underwater.in_air_to_underwater_spl(0.0) == pytest.approx(26.0, abs=0.05)


@pytest.mark.parametrize(
    ("constant", "medium", "key"),
    [
        (underwater.UNDERWATER_REFERENCE_PRESSURE, "liquid", "sound_pressure"),
        (underwater.UNDERWATER_REFERENCE_EXPOSURE, "liquid", "sound_exposure"),
        (vibration.REFERENCE_ACCELERATION, "solid", "acceleration"),
        (impulsive_sound.REFERENCE_PRESSURE, "gas", "sound_pressure"),
        (structure_borne_power.REFERENCE_VELOCITY, "solid", "velocity"),
        (structure_borne_power.REFERENCE_SOUND_POWER, "gas", "sound_power"),
        (structure_borne_power.REFERENCE_FORCE, "solid", "force"),
    ],
)
def test_the_published_constants_are_the_table_values(
    constant: float, medium: str, key: str
) -> None:
    """The constants that existed before the table now read it."""
    assert constant == _TABLE[medium][key].value


def test_the_structure_borne_references_that_differ_keep_their_value() -> None:
    """ISO/TS 7849 and ISO 9611 count from 50 nm/s, the note b alternative."""
    alternative = _TABLE["solid"]["velocity_alternative"].value
    assert emission.REFERENCE_VELOCITY == alternative
    assert structure_borne_power.FREE_VELOCITY_REFERENCE == alternative
