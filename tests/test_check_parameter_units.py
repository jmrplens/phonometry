#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The unit gate's two name rules: one spelling per unit, and constants with units.

``scripts/check_parameter_units.py`` holds the public names of the package to
two rules besides the one it was written for. A unit has one spelling, so a
name that ends in ``_seconds``, ``_degrees``, ``_km_h``, ``_db_s``, ``_knots``
or an ``_h`` that means hours is refused wherever it stands; and a published
constant ends in its unit, as a parameter does, when it is a single number,
whatever its name says, or a table whose name says a quantity. These tests
pin the halves that decide both, then run the two rules over the real tree,
where they have to be silent, and put an old name back, where they have to
speak.
"""

from __future__ import annotations

import pathlib
import sys
from types import MappingProxyType
from typing import NamedTuple

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_units as cpu

import phonometry.aircraft
import phonometry.building
import phonometry.signals


@pytest.mark.parametrize(
    ("name", "rejected"),
    [
        ("phase_tolerance_degrees", "_degrees"),
        ("burst_seconds", "_seconds"),
        ("speed_from_km_h", "_km_h"),
        ("decay_rate_db_s", "_db_s"),
        ("wind_speed_knots", "_knots"),
        ("curing_time_h", "_h"),
        ("PHASE_TOLERANCE_DEGREES", "_degrees"),
    ],
)
def test_a_retired_spelling_is_named(name: str, rejected: str) -> None:
    assert cpu.rejected_spelling(name) == rejected


@pytest.mark.parametrize(
    "name",
    [
        "phase_tolerance_deg",
        "burst_s",
        "speed_from_kmh",
        "decay_rate_db_per_s",
        "wind_speed_kt",
        "curing_time_hours",
        # The hour of a rate, mm/h, is the denominator of its unit.
        "rainfall_rate_mm_h",
        "width",
    ],
)
def test_the_spelling_the_tree_writes_passes(name: str) -> None:
    assert cpu.rejected_spelling(name) is None


def test_the_longer_retired_suffix_is_the_one_reported() -> None:
    """``_km_h`` ends in ``_h`` too, and the fix for it is ``_kmh``, not hours."""
    assert cpu.rejected_spelling("speed_to_km_h") == "_km_h"


class _Record(NamedTuple):
    frequency_hz: float


@pytest.mark.parametrize(
    "value",
    [
        "band-limiting",
        ("day", "evening", "night"),
        MappingProxyType({"e": "sanitary land"}),
        True,
        MappingProxyType({"a": _Record(63.0)}),
        _Record(1000.0),
    ],
)
def test_a_label_or_a_record_holds_no_bare_number(value: object) -> None:
    assert not cpu.holds_a_number(value)


@pytest.mark.parametrize(
    "value",
    [
        340.0,
        5,
        (63.0, 125.0),
        np.array([50.0, 63.0]),
        MappingProxyType({"day": (7, 19)}),
        MappingProxyType({1: 0.71}),
    ],
)
def test_a_number_anywhere_in_a_constant_is_held(value: object) -> None:
    assert cpu.holds_a_number(value)


@pytest.mark.parametrize("value", [10.0, 5, np.float64(0.775), np.array(1e-12)])
def test_a_lone_number_is_a_single_number(value: object) -> None:
    assert cpu.holds_a_single_number(value)


@pytest.mark.parametrize(
    "value",
    [True, (63.0, 125.0), np.array([50.0, 63.0]), MappingProxyType({1: 0.71})],
)
def test_a_table_or_a_truth_value_is_not(value: object) -> None:
    assert not cpu.holds_a_single_number(value)


@pytest.mark.parametrize(
    "name",
    [
        "TAPPING_IMPACT_RATE_HZ",
        "DBQPS_REFERENCE_V",
        "UNDERWATER_REFERENCE_EXPOSURE_PA2_S",
        "DEFAULT_STABILITY_MARGIN_DB",
        "ISO7235_COVERAGE_FACTOR",
        "DEFAULT_CO2_MOLE_FRACTION",
    ],
)
def test_a_lone_number_names_its_unit_or_says_it_has_none(name: str) -> None:
    assert cpu.constant_declares_its_unit(name)


@pytest.mark.parametrize(
    "name", ["TAPPING_IMPACT_RATE", "HAV_EAV_A8", "NO_TONE_AUDIBILITY"]
)
def test_a_lone_number_with_a_bare_name_does_not(name: str) -> None:
    assert not cpu.constant_declares_its_unit(name)


@pytest.mark.parametrize(
    "name",
    [
        "NOY_BANDS",
        "ROAD_REFERENCE_SPEED",
        "TAPPING_HAMMER_MASS",
        "UNIVERSAL_GAS_CONSTANT",
        "UNDERWATER_REFERENCE_PRESSURE",
        "DEFAULT_POLAR_ANGLES",
        "LOW_FREQUENCY_VOLUME_LIMIT",
    ],
)
def test_a_constant_that_names_a_quantity_is_under_the_rule(name: str) -> None:
    assert cpu.constant_names_a_quantity(name)


@pytest.mark.parametrize(
    "name",
    [
        # An adjective, not a frequency.
        "LOW_FREQUENCY_WEIGHTING",
        "FLOW_COEFFICIENT_CONSTANTS",
    ],
)
def test_a_constant_that_names_no_quantity_is_not(name: str) -> None:
    assert not cpu.constant_names_a_quantity(name)


def test_the_molar_mass_is_a_quantity_as_a_run_of_words() -> None:
    assert cpu.names_a_quantity("molecular_mass")
    assert cpu.names_a_quantity("molar_mass_kg_mol")
    assert not cpu.names_a_quantity("mass_flow")


def test_the_tree_spells_every_unit_one_way() -> None:
    found, stale = cpu.misspelled()
    assert found == []
    assert stale == []


def test_every_published_constant_says_its_unit() -> None:
    found, stale = cpu.unitless_constants()
    assert found == []
    assert stale == []


def test_a_retired_spelling_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A function that takes ``burst_seconds`` again is caught by its parameter."""

    def tone_burst_again(burst_seconds: float) -> float:
        return burst_seconds

    tone_burst_again.__module__ = "phonometry.signals"
    monkeypatch.setattr(
        phonometry.signals, "tone_burst_again", tone_burst_again, raising=False
    )
    monkeypatch.setattr(
        phonometry.signals,
        "__all__",
        [*phonometry.signals.__all__, "tone_burst_again"],
    )
    found, _ = cpu.misspelled()
    assert [(entry.qualname, entry.name, rejected) for entry, rejected in found] == [
        ("tone_burst_again", "burst_seconds", "_seconds")
    ]


def test_a_classmethod_parameter_is_held_to_the_spelling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An alternative constructor is walked like ``__init__``.

    A classmethod or a staticmethod sits in the class dictionary as a
    descriptor, not a function, so it is the function it wraps that has to be
    read.
    """

    def from_burst(cls: type, burst_seconds: float) -> float:
        return burst_seconds

    def from_gap(gap_seconds: float) -> float:
        return gap_seconds

    record = phonometry.signals.ToneBurstResult
    monkeypatch.setattr(record, "from_burst", classmethod(from_burst), raising=False)
    monkeypatch.setattr(record, "from_gap", staticmethod(from_gap), raising=False)
    found, _ = cpu.misspelled()
    assert sorted((entry.name, rejected) for entry, rejected in found) == [
        ("burst_seconds", "_seconds"),
        ("gap_seconds", "_seconds"),
    ]


def test_a_constant_without_its_unit_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``NOY_BANDS`` published again beside ``NOY_BANDS_HZ`` fails the rule."""
    monkeypatch.setattr(
        phonometry.aircraft,
        "NOY_BANDS",
        tuple(phonometry.aircraft.NOY_BANDS_HZ),
        raising=False,
    )
    monkeypatch.setattr(
        phonometry.aircraft,
        "__all__",
        [*phonometry.aircraft.__all__, "NOY_BANDS"],
    )
    found, _ = cpu.unitless_constants()
    assert [entry.name for entry in found] == ["NOY_BANDS"]


def test_a_lone_number_without_its_unit_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``TAPPING_IMPACT_RATE`` needs no quantity word to be under the rule.

    A rate names no quantity the table rule knows, and 10.0 on its own could
    be hertz, impacts a minute or a count: a single number is held to its
    unit whatever its name says.
    """
    monkeypatch.setattr(
        phonometry.building,
        "TAPPING_IMPACT_RATE",
        float(phonometry.building.TAPPING_IMPACT_RATE_HZ),
        raising=False,
    )
    monkeypatch.setattr(
        phonometry.building,
        "__all__",
        [*phonometry.building.__all__, "TAPPING_IMPACT_RATE"],
    )
    found, _ = cpu.unitless_constants()
    assert [entry.name for entry in found] == ["TAPPING_IMPACT_RATE"]


def test_an_exemption_a_name_no_longer_needs_is_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An exemption kept for a name that now says its unit is reported."""
    monkeypatch.setitem(
        cpu.CONSTANT_EXEMPT,
        ("phonometry.building.prediction.resilient_layers", "TAPPING_IMPACT_RATE_HZ"),
        "a reason nobody needs",
    )
    _, stale = cpu.unitless_constants()
    assert stale == [
        ("phonometry.building.prediction.resilient_layers", "TAPPING_IMPACT_RATE_HZ")
    ]
