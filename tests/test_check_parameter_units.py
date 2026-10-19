#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The unit gate: a unit in the name, one spelling per unit, constants with units.

``scripts/check_parameter_units.py`` walks the installed package, so its own
run only says the tree is clean today. These tests fix what it must catch. A
distance is held to the rule inside ``phonometry.aircraft`` and nowhere else,
because only there do feet compete with metres; a numbered ``thickness1`` is
the word ``thickness`` like any other; and a plural is the word it is the
plural of. A unit has one spelling, so a name that ends in ``_seconds``,
``_degrees``, ``_km_h``, ``_db_s``, ``_knots`` or an ``_h`` that means hours
is refused wherever it stands; and a published constant ends in its unit, as
a parameter does, when it is a single number, whatever its name says, or a
table whose name says a quantity. The tests pin the halves that decide these
rules, run them over the real tree, where they have to be silent, and put an
old name back, where they have to speak. They also fix that the one
exemption of a length word still names a parameter that exists, since an
exemption that outlives its parameter would excuse the next one to take the
name.
"""

from __future__ import annotations

import functools
import inspect
import pathlib
import sys
import types
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_units as cpu

import phonometry.aircraft
import phonometry.building
import phonometry.signals

if TYPE_CHECKING:
    from collections.abc import Iterator


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

    monkeypatch.setattr(tone_burst_again, "__module__", "phonometry.signals")
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


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("distances", "phonometry.aircraft"),
        ("distances", "phonometry.aircraft.airport_noise"),
        ("query_distances", "phonometry.aircraft.airport_noise"),
        ("distance", "phonometry.aircraft.rotorcraft_propagation"),
    ],
    ids=["aircraft", "aircraft-submodule", "aircraft-compound", "aircraft-singular"],
)
def test_distance_is_held_to_the_rule_inside_aircraft(name: str, module: str) -> None:
    assert cpu.names_a_quantity(name, module)


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("distances", "phonometry.environment.propagation"),
        ("distance", "phonometry.aircraftx"),
        ("distances", ""),
    ],
    ids=["elsewhere", "sibling-prefix", "no-module"],
)
def test_distance_is_not_held_to_the_rule_outside_aircraft(
    name: str, module: str
) -> None:
    assert not cpu.names_a_quantity(name, module)


@pytest.mark.parametrize(
    "name",
    [
        "thickness",
        "thickness1",
        "thickness2",
        "plate_thickness",
        "layer_thicknesses",
        "spacing",
        "spacings",
        "line_spacing",
        "height",
        "heights",
        "source_height2",
        "diameters",
        "gradients",
    ],
)
def test_a_length_word_is_held_to_the_rule_everywhere(name: str) -> None:
    assert cpu.names_a_quantity(name, "phonometry.materials")


@pytest.mark.parametrize("name", ["triangles", "weights", "spacer", "f1", "n_layers"])
def test_a_name_that_only_contains_the_letters_is_not(name: str) -> None:
    assert not cpu.names_a_quantity(name, "phonometry.materials")


def _npd(distances_m: float, distance: float, *, level_db: float = 0.0) -> float:
    return distances_m + distance + level_db


def _junction(distances: float, thickness1: float, spacing_m: float = 0.05) -> float:
    return distances + thickness1 + spacing_m


def test_the_walk_reports_what_the_rule_holds(monkeypatch: pytest.MonkeyPatch) -> None:
    """An aircraft ``distance`` and a numbered ``thickness1`` are reported bare,
    a ``spacing_m`` with a default that stays positional is reported loose, and
    a ``distances`` outside aircraft is not reported at all.
    """
    monkeypatch.setattr(_npd, "__module__", "phonometry.aircraft.stub")
    monkeypatch.setattr(_junction, "__module__", "phonometry.vibration.stub")
    stub = types.ModuleType("phonometry.stub")
    stub.__all__ = ["npd", "junction"]  # type: ignore[attr-defined]
    stub.npd = _npd  # type: ignore[attr-defined]
    stub.junction = _junction  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield "phonometry.stub", stub

    monkeypatch.setattr(cpu, "public_modules", modules)
    unnamed, loose, _ = cpu.offenders()
    assert {(p.qualname, p.name) for p in unnamed} == {
        ("npd", "distance"),
        ("junction", "thickness1"),
    }
    assert {(p.qualname, p.name) for p in loose} == {("junction", "spacing_m")}


def test_the_source_line_selector_is_exempt_and_still_exists() -> None:
    """``vertical_directivity(height=)`` picks source line 1 or 2; its exemption
    has to keep pointing at a parameter that is really there.
    """
    from phonometry.environment.sources import cnossos_rail

    key = (
        "phonometry.environment.sources.cnossos_rail",
        "vertical_directivity",
        "height",
    )
    assert key in cpu.EXEMPT
    assert cnossos_rail.vertical_directivity.__module__ == key[0]
    assert cpu.names_a_quantity(key[2], key[0])
    assert key[2] in inspect.signature(cnossos_rail.vertical_directivity).parameters


@pytest.mark.parametrize(
    "name",
    [
        "speed",
        "speed_range",
        "minimum_speed",
        "reference_speed",
        "rotational_speed",
        "airspeed",
        "airspeeds",
        "ground_speed",
        "phase",
        "excess_phase",
        "phase_std",
    ],
)
def test_a_vehicle_speed_and_a_phase_are_held_to_the_rule(name: str) -> None:
    assert cpu.names_a_quantity(name, "phonometry.environment")


@pytest.mark.parametrize(
    "name",
    [
        "speed_of_sound",
        "speeds_of_sound",
        "seabed_sound_speed",
        "sound_speed_ratio",
        "wave_speed1",
        "shear_wave_speed",
        "phaser",
    ],
)
def test_the_speed_of_sound_is_not_a_vehicle_speed(name: str) -> None:
    assert not cpu.names_a_quantity(name, "phonometry.environment")


def _stub(**params: str) -> list[cpu.Parameter]:
    """One stub parameter per name, documented as given, in one subpackage."""
    return [
        cpu.Parameter("phonometry.stub.module", "stub", name, "stub.py:1", doc=doc)
        for name, doc in params.items()
    ]


def test_a_rate_per_distance_must_say_so_in_its_name() -> None:
    """An absorption documented in dB/km under ``_coefficient`` is reported."""
    found, _ = cpu.misnamed_rates(
        _stub(
            absorption_coefficient="The absorption coefficient alpha, in dB/km.",
            air_attenuation="Air power-attenuation coefficient m (1/m).",
            attenuation_empty="m_1 per band, in reciprocal metres.",
            tube_attenuation="The attenuation constant, in nepers per metre.",
        )
    )
    assert sorted(p.name for p in found) == [
        "absorption_coefficient",
        "air_attenuation",
        "attenuation_empty",
        "tube_attenuation",
    ]


def test_a_coefficient_documented_per_distance_is_a_rate() -> None:
    """A bare ``coefficient`` in dB/m says neither absorption nor attenuation,
    and is the alpha of ISO 9613-1 all the same; a pure one is left alone.
    """
    found, _ = cpu.misnamed_rates(
        _stub(
            coefficient="Pure-tone attenuation coefficient alpha per band, in dB/m.",
            coefficient_db_per_m="The attenuation coefficient alpha, in dB/m.",
            scattering_coefficient="The scattering coefficient s, dimensionless.",
        )
    )
    assert [p.name for p in found] == ["coefficient"]


def test_a_rate_that_names_its_distance_and_a_pure_alpha_pass() -> None:
    found, _ = cpu.misnamed_rates(
        _stub(
            absorption_db_per_km="The absorption coefficient alpha, in dB/km.",
            attenuation_db_per_m="alpha, in decibels per metre.",
            air_attenuation_per_m="Air power-attenuation coefficient m (1/m).",
            attenuation_np_per_m="The attenuation constant, in Np/m.",
            absorption_coefficient="The sound absorption coefficient, dimensionless.",
            attenuation_db="The attenuation over the path, in dB.",
        )
    )
    assert found == []


def test_the_pressure_of_the_medium_has_one_stem() -> None:
    """Every other word for the ambient pressure is refused, and so is
    ``atmospheric_pressure_`` outside the signatures that carry a stream
    pressure beside it.
    """
    found, _ = cpu.ambient_pressure_names(
        _stub(
            barometric_pressure_pa="",
            ambient_pressure_pa="",
            atmospheric_pressure_kpa="",
            absolute_pressure_pa="",
            static_pressure_kpa="",
            static_pressure_pa="",
            static_gauge_pressure_pa="",
            reference_static_pressure_kpa="",
        )
    )
    assert sorted(e.name for e in found if e.module == "phonometry.stub.module") == [
        "absolute_pressure_pa",
        "ambient_pressure_pa",
        "atmospheric_pressure_kpa",
        "barometric_pressure_pa",
    ]


def test_the_atmosphere_beside_a_stream_is_admitted_where_listed() -> None:
    key = (
        "phonometry.noise_control.valves",
        "pipe_transmission_loss",
        "atmospheric_pressure_pa",
    )
    admitted = cpu.Parameter(key[0], key[1], key[2], "valves.py:1")
    elsewhere = cpu.Parameter(key[0], "pipe_wall_impedance", key[2], "valves.py:2")
    found, _ = cpu.ambient_pressure_names([admitted, elsewhere])
    assert [(e.qualname, e.name) for e in found if e.module == key[0]] == [
        ("pipe_wall_impedance", "atmospheric_pressure_pa")
    ]


def test_a_name_public_both_bare_and_with_its_unit_is_reported() -> None:
    """``volume`` and ``volume_m3`` in one subpackage are one quantity spelled
    two ways; the same pair across two subpackages is not reported here.
    """
    params = [
        cpu.Parameter("phonometry.stub.a", "room", "volume", "a.py:1"),
        cpu.Parameter("phonometry.stub.b", "turbine", "volume_m3", "b.py:1"),
        cpu.Parameter("phonometry.other.c", "box", "area", "c.py:1"),
        cpu.Parameter("phonometry.elsewhere.d", "cell", "area_m2", "d.py:1"),
    ]
    found, _ = cpu.bare_and_suffixed(params)
    assert [(package, bare, unit) for package, bare, unit, *_ in found] == [
        ("phonometry.stub", "volume", "volume_m3")
    ]


@pytest.mark.parametrize(
    ("bare", "suffixed"),
    [
        ("rated_impedance", "rated_impedance_ohm"),
        ("duration", "duration_ms"),
        ("density", "density_kg_m3"),
        ("flow_resistivity", "flow_resistivity_pa_s_m2"),
        ("stiffness", "stiffness_n_per_m"),
        ("coefficient", "coefficient_db_per_100m"),
        ("force", "force_n"),
    ],
)
def test_a_pair_is_found_whatever_unit_ends_it(bare: str, suffixed: str) -> None:
    """An electrical unit, a millisecond, a compound unit or a single-letter
    newton each pair a name with its bare spelling; ``density_kg_m3`` is not
    read as a ``density_kg`` in cubic metres.
    """
    params = [
        cpu.Parameter("phonometry.stub.a", "record", bare, "a.py:1"),
        cpu.Parameter("phonometry.stub.b", "function", suffixed, "b.py:1"),
    ]
    found, _ = cpu.bare_and_suffixed(params)
    assert [(b, u) for _, b, u, *_ in found] == [(bare, suffixed)]


@pytest.mark.parametrize(
    "tail",
    ["ohm", "kg_m3", "pa_s_m2", "n_per_m", "db_per_100m", "m3_s", "n", "a", "w"],
)
def test_a_unit_tail_is_read_as_a_unit(tail: str) -> None:
    assert cpu.is_unit_tail(tail)


@pytest.mark.parametrize(
    "tail",
    ["db", "j", "i", "s_db", "per", "m_per", "db_m", "kg_db_per_m", "ratio"],
)
def test_a_level_a_subscript_or_a_word_is_not_a_unit_tail(tail: str) -> None:
    """A level's ``_db``, the ``j`` of an element and a dangling ``per`` are
    not units, so ``r``/``r_s_db`` or ``area``/``area_j`` is no pair.
    """
    assert not cpu.is_unit_tail(tail)


def test_a_pair_exemption_nothing_needs_is_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        cpu.PAIR_EXEMPT, ("phonometry.stub", "volume", "volume_m3"), "no reason"
    )
    params = [cpu.Parameter("phonometry.stub.a", "room", "volume", "a.py:1")]
    _, stale = cpu.bare_and_suffixed(params)
    assert ("phonometry.stub", "volume", "volume_m3") in stale


class _Mobility:
    """A stub result whose phase is a property, documented in radians."""

    @property
    def phase(self) -> np.ndarray:
        """Mobility phase, in radians."""
        return np.zeros(1)


class _CachedMobility:
    """A stub result whose phase is computed once, documented in radians."""

    @functools.cached_property
    def phase(self) -> np.ndarray:
        """Mobility phase, in radians."""
        return np.zeros(1)


@pytest.mark.parametrize("result", [_Mobility, _CachedMobility])
def test_a_property_is_walked_like_a_field(
    result: type, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``phase`` read off a result, a property or a cached one, is held to
    the rule as a field would be.
    """
    monkeypatch.setattr(result, "__module__", "phonometry.vibration.stub")
    stub = types.ModuleType("phonometry.stub")
    stub.__all__ = ["Mobility"]  # type: ignore[attr-defined]
    stub.Mobility = result  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield "phonometry.stub", stub

    monkeypatch.setattr(cpu, "public_modules", modules)
    unnamed, _, _ = cpu.offenders()
    assert [(p.qualname, p.name) for p in unnamed] == [("Mobility", "phase")]


def test_the_tree_holds_every_closing_rule() -> None:
    parameters = list(cpu.public_parameters())
    assert cpu.misnamed_rates(parameters) == ([], [])
    assert cpu.ambient_pressure_names(parameters) == ([], [])
    assert cpu.bare_and_suffixed(parameters) == ([], [])
