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
name. A level or a level difference carries no ``_db``, because its head noun
already says decibels, while a decibel value under another noun keeps it and
fails bare as it did before.
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
import phonometry.environment
import phonometry.io
import phonometry.noise_control
import phonometry.room
import phonometry.signals

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


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


def test_every_public_function_is_named_for_what_it_returns() -> None:
    found, stale = cpu.unit_named_functions()
    assert found == []
    assert stale == []


def test_a_level_function_named_with_its_decibels_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A function that ends in ``_db`` or ``_hz`` again fails the rule.

    The two units a function name never carries, one function each, and one
    that keeps a unit its quantity is written in twice (``_mm_s``), which
    passes.
    """

    def plant_background_correction_db(level: float) -> float:
        return level

    def track_excitation_frequency_hz(speed_kmh: float) -> float:
        return speed_kmh

    def far_field_velocity_again_mm_s(level: float) -> float:
        return level

    added = {
        "plant_background_correction_db": plant_background_correction_db,
        "track_excitation_frequency_hz": track_excitation_frequency_hz,
        "far_field_velocity_again_mm_s": far_field_velocity_again_mm_s,
    }
    for name, function in added.items():
        monkeypatch.setattr(function, "__module__", "phonometry.signals")
        monkeypatch.setattr(phonometry.signals, name, function, raising=False)
    monkeypatch.setattr(
        phonometry.signals, "__all__", [*phonometry.signals.__all__, *added]
    )
    found, _ = cpu.unit_named_functions()
    assert sorted(entry.qualname for entry in found) == [
        "plant_background_correction_db",
        "track_excitation_frequency_hz",
    ]


def test_a_method_named_with_its_decibels_is_reported_and_a_property_is_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A method, a classmethod and a staticmethod are functions; a property is not.

    A property reads like a field, and a field keeps the unit of what it
    holds, so ``burst_level_db`` as a property passes where the same name as
    a method fails.
    """

    def margin_db(self: object) -> float:
        return 0.0

    def from_level_db(cls: type, level: float) -> float:
        return level

    def bandwidth_hz(fs: float) -> float:
        return fs

    record = phonometry.signals.ToneBurstResult
    monkeypatch.setattr(record, "margin_db", margin_db, raising=False)
    monkeypatch.setattr(
        record, "from_level_db", classmethod(from_level_db), raising=False
    )
    monkeypatch.setattr(
        record, "bandwidth_hz", staticmethod(bandwidth_hz), raising=False
    )
    monkeypatch.setattr(
        record, "burst_level_db", property(lambda self: 0.0), raising=False
    )
    found, _ = cpu.unit_named_functions()
    assert sorted(entry.qualname for entry in found) == [
        "ToneBurstResult.bandwidth_hz",
        "ToneBurstResult.from_level_db",
        "ToneBurstResult.margin_db",
    ]


def test_a_method_inherited_from_a_base_no_module_exports_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A published class answers to what its private base defines.

    ``AirLayer`` and seventeen other layers inherit ``plot`` from
    ``_DrawableLayer``, which no module exports; a ``_db`` method planted
    there is called on every one of them, and it is reported once, under the
    class that defines it.
    """
    from phonometry.materials.absorbers import layered

    def margin_db(self: object) -> float:
        return 0.0

    monkeypatch.setattr(layered._DrawableLayer, "margin_db", margin_db, raising=False)
    found, _ = cpu.unit_named_functions()
    assert [entry.qualname for entry in found] == ["_DrawableLayer.margin_db"]


def test_a_function_exemption_nothing_needs_is_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        cpu.FUNCTION_UNIT_EXEMPT,
        ("phonometry.noise_control.silencer_in_situ", "sound_power_level_db"),
        "a reason nobody needs",
    )
    _, stale = cpu.unit_named_functions()
    assert stale == [
        ("phonometry.noise_control.silencer_in_situ", "sound_power_level_db")
    ]


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


@pytest.mark.parametrize("name", ["assessment_period_minutes", "period_hours"])
def test_a_period_in_minutes_spells_the_minute_out(name: str) -> None:
    """The minute is ``_minutes``, spelled out as the hour is."""
    assert cpu.names_a_quantity(name, "phonometry.environment")
    assert cpu.declares_its_unit(name)


@pytest.mark.parametrize("name", ["assessment_period_min", "period_min"])
def test_a_period_that_ends_in_min_names_no_unit(name: str) -> None:
    """A trailing ``_min`` is a minimum (``f_min``, ``kij_min``), so a period
    that ends in it names no unit and the rule reports it, as it reports a
    bare one.
    """
    assert cpu.names_a_quantity(name, "phonometry.environment")
    assert not cpu.declares_its_unit(name)


def test_a_minute_under_per_is_the_denominator_of_a_rate() -> None:
    """The feet per minute of an ANP climb rate is a unit, and ``min`` alone
    is not one, so ``envelope``/``envelope_min`` is no pair.
    """
    assert cpu.declares_its_unit("rate_of_climb_ft_per_min")
    assert cpu.is_unit_tail("ft_per_min")
    assert cpu.is_unit_tail("minutes")
    assert not cpu.is_unit_tail("min")


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


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("insertion_loss_db", ""),
        ("band_levels_db", ""),
        ("sound_power_level_a_db", ""),
        ("sound_reduction_index_1000_db", ""),
        ("levels_before_db", ""),
        ("receiver_correction_after_db", ""),
        ("band_levels_at_characteristic_db", ""),
        ("linearity_levels_below_upper_db", ""),
        ("front_to_random_index_db", ""),
        ("pressure_level_difference_db", ""),
        ("spectrum_adaptation_term_50_3150_db", ""),
        ("max_spl_db", ""),
        ("l_i_fmax_0_db", ""),
        ("delta_rw_c_direct_db", ""),
        ("r_s_w_ctr_db", "phonometry.building.measurement.joint_insulation"),
        ("c_100_5000_db", "phonometry.building.measurement.joint_insulation"),
        ("level_db_at", ""),
        ("EARPHONE_ATTENUATION_DB", ""),
        ("VIBROTACTILE_HEARING_LEVELS_DB", ""),
        ("emergence_db", ""),
        ("c2_db", "phonometry.emission.reference_sound_source"),
        ("MAX_K3_DB", "phonometry.emission.workstation"),
        ("MIN_MULTI_JUNCTION_KIJ_DB", "phonometry.building.prediction"),
        ("k_ff_db", "phonometry.building.prediction.simplified_model"),
        ("tonal_adjustment_db", ""),
        ("adjustments_db", ""),
        ("isolation_db", ""),
        ("free_field_rejection_db", ""),
        ("level_shift_db", ""),
        ("level_increase_db", ""),
        ("level_excess_db", ""),
        ("l1_db", "phonometry.building.measurement.insulation"),
    ],
)
def test_a_level_or_a_level_difference_carries_no_db(name: str, module: str) -> None:
    """The head noun says decibel, so ``_db`` says it a second time."""
    assert cpu.decibel_suffix(name, module) is not None


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("tolerance_db", ""),
        ("background_margin_a_db", ""),
        ("a_weighted_limit_db", ""),
        ("expanded_uncertainty_1khz_db", ""),
        ("level_standard_deviation_db", ""),
        ("level_step_db", ""),
        ("slope_db_per_decade", ""),
        ("attenuation_db_per_m", ""),
        ("class_densities_per_db", ""),
        ("within_10_db_of_max", ""),
        ("sigma_level_db", ""),
        ("signal_to_noise_ratio_db", ""),
        ("diffuse_pressure_difference_db", ""),
        ("phase_difference_db", ""),
        ("c_db", "phonometry.underwater.bioacoustics.weighting"),
        ("r_direct_db", "phonometry.environment.propagation.ground_barriers"),
        ("MAX_K3_DB", "phonometry.vibration.machinery"),
        ("c1_db", "phonometry.underwater.propagation"),
        ("shift_db", ""),
        ("allowed_threshold_shift_db", ""),
        ("drop_db", ""),
        ("sensitivity_change_db", ""),
        ("temperature_adjustment_db", ""),
        ("l1_db", "phonometry.materials.absorbers.four_microphone"),
    ],
)
def test_a_name_whose_head_noun_does_not_say_decibel_keeps_db(
    name: str, module: str
) -> None:
    """A tolerance, a margin, a statistic, a rate or a difference of another
    quantity says nothing of decibels, so its unit stays in the name.
    """
    assert cpu.decibel_suffix(name, module) is None


@pytest.mark.parametrize(
    "name",
    [
        "insertion_loss",
        "pressure_level_difference",
        "sound_pressure_level",
        "pressure_residual_index",
        "emergence",
        "rating_adjustment",
        "free_field_rejection",
        "level_shift",
    ],
)
def test_the_head_noun_of_a_level_declares_the_decibel(name: str) -> None:
    """A level and a level difference say their unit by the noun."""
    assert cpu.declares_its_unit(name)


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("MAX_K3", "phonometry.emission.workstation"),
        ("GRADE_2_MAX_K3", "phonometry.emission.workstation"),
        ("MIN_MULTI_JUNCTION_KIJ", "phonometry.building.prediction"),
        ("c1", "phonometry.emission.sound_power"),
    ],
)
def test_the_symbol_of_a_correction_declares_the_decibel_in_its_package(
    name: str, module: str
) -> None:
    """:math:`K_3`, :math:`K_{ij}` and :math:`C_1` are corrections and an
    index in decibels where their standards print them, so the constant rule
    reads the cap on :math:`K_3` as declaring its unit there and nowhere else.
    """
    assert cpu.constant_declares_its_unit(name, module)
    assert not cpu.constant_declares_its_unit(name, "phonometry.signals")


@pytest.mark.parametrize(
    "name",
    [
        "plateau_height",
        "phase_difference",
        "pressure_loss",
        "temperature_reduction",
        "shift",
        "drop_height",
    ],
)
def test_another_head_noun_declares_nothing(name: str) -> None:
    """A height, a phase difference, a pressure loss or a temperature
    reduction does not say decibel, so a decibel value under one of those
    still needs its ``_db``.
    """
    assert not cpu.declares_its_unit(name)


def test_no_level_carries_a_unit_suffix() -> None:
    found, stale = cpu.decibel_suffixed()
    assert found == []
    assert stale == []


def test_a_level_named_with_its_decibels_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A parameter ``insertion_loss_db`` and a constant ``..._LEVEL_DB`` fail again."""

    def insertion_loss_again(insertion_loss_db: float, *, margin_db: float) -> float:
        return insertion_loss_db + margin_db

    monkeypatch.setattr(insertion_loss_again, "__module__", "phonometry.signals")
    monkeypatch.setattr(
        phonometry.signals, "insertion_loss_again", insertion_loss_again, raising=False
    )
    monkeypatch.setattr(phonometry.signals, "REFERENCE_LEVEL_DB", 94.0, raising=False)
    monkeypatch.setattr(
        phonometry.signals,
        "__all__",
        [*phonometry.signals.__all__, "insertion_loss_again", "REFERENCE_LEVEL_DB"],
    )
    found, _ = cpu.decibel_suffixed()
    assert sorted((entry.qualname, entry.name) for entry, _ in found) == [
        ("", "REFERENCE_LEVEL_DB"),
        ("insertion_loss_again", "insertion_loss_db"),
    ]


def _plateau(
    plateau_height: float, phase_difference: float, pressure_loss: float
) -> float:
    return plateau_height + phase_difference + pressure_loss


def _plateau_db(
    plateau_height_db: float, phase_difference_db: float, insertion_loss: float
) -> float:
    return plateau_height_db + phase_difference_db + insertion_loss


def test_a_decibel_value_under_another_head_noun_still_needs_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dropping ``_db`` is only for a level or a level difference.

    A plateau height in decibels, a phase difference and a pressure loss
    named bare are reported as quantities without their unit, as they were
    before the level rule; with ``_db`` they pass both rules, and a bare
    ``insertion_loss`` passes the unit rule because its noun says decibel.
    """
    monkeypatch.setattr(_plateau, "__module__", "phonometry.building.stub")
    monkeypatch.setattr(_plateau_db, "__module__", "phonometry.building.stub")
    stub = types.ModuleType("phonometry.stub")
    stub.__all__ = ["plateau", "plateau_db"]  # type: ignore[attr-defined]
    stub.plateau = _plateau  # type: ignore[attr-defined]
    stub.plateau_db = _plateau_db  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield "phonometry.stub", stub

    monkeypatch.setattr(cpu, "public_modules", modules)
    unnamed, _, _ = cpu.offenders()
    assert {(p.qualname, p.name) for p in unnamed} == {
        ("plateau", "plateau_height"),
        ("plateau", "phase_difference"),
        ("plateau", "pressure_loss"),
    }
    found, _ = cpu.decibel_suffixed()
    assert found == []


def test_a_level_exemption_nothing_needs_is_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = ("phonometry.signals", "nothing_here", "level_db")
    monkeypatch.setitem(cpu.LEVEL_SUFFIX_EXEMPT, key, "a reason for nothing")
    _, stale = cpu.decibel_suffixed()
    assert key in stale


def test_the_notebook_table_reads_a_level_the_way_the_rule_does() -> None:
    """The table shows dB for exactly the names the rule reads as a level.

    The two disagree only where a difference noun follows another quantity
    (a pressure loss, a sound pressure insulation), which the rule leaves to
    the unit rule and the table never meets bare on a field.
    """
    from phonometry._internal import display

    disagreements = {
        (entry.module, entry.name)
        for entry in cpu.public_names()
        if entry.name not in display._NAMED_UNITS
        and not display._suffix_unit(entry.name)
        and display.says_decibels(entry.name, entry.module)
        != cpu.decibel_head(entry.name, entry.module)
    }
    assert all(cpu.names_a_quantity(name, module) for module, name in disagreements)


def _attenuation(
    frequencies: np.ndarray, height: float, speed_of_sound: float = 343.0
) -> float:
    return height + speed_of_sound


def _calibrated(x: np.ndarray, calibration_factor: float | None = None) -> float:
    return 0.0 if calibration_factor is None else calibration_factor


def _medium(speed_of_sound: float = 343.0) -> float:
    return speed_of_sound


def _ground(distance: float, *, ground_source: float = 0.0) -> float:
    return distance + ground_source


def _seabed(density: float, water_density: float = 1000.0) -> float:
    return density / water_density


def test_a_condition_is_written_by_name_whatever_its_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The speed of sound and a calibration factor carry no unit to catch, so
    the unit half of the rule never saw them: both are reported when a caller
    can still pass them by position. The first parameter is the subject of
    the call and stays where it is, and a keyword-only ground factor passes.
    """
    for function in (_attenuation, _calibrated, _medium, _ground, _seabed):
        monkeypatch.setattr(function, "__module__", "phonometry.environment.stub")
    stub = types.ModuleType("phonometry.stub")
    stub.__all__ = ["attenuation", "calibrated", "medium", "ground", "seabed"]  # type: ignore[attr-defined]
    stub.attenuation = _attenuation  # type: ignore[attr-defined]
    stub.calibrated = _calibrated  # type: ignore[attr-defined]
    stub.medium = _medium  # type: ignore[attr-defined]
    stub.ground = _ground  # type: ignore[attr-defined]
    stub.seabed = _seabed  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield "phonometry.stub", stub

    monkeypatch.setattr(cpu, "public_modules", modules)
    _, loose, _ = cpu.offenders()
    assert sorted((p.qualname, p.name) for p in loose) == [
        ("attenuation", "speed_of_sound"),
        ("calibrated", "calibration_factor"),
        ("seabed", "water_density"),
    ]


def _criterion(levels: np.ndarray, frequencies: np.ndarray | None = None) -> float:
    return 0.0


def _criterion_by_name(
    levels: np.ndarray, *, frequencies: np.ndarray | None = None
) -> float:
    return 0.0


def _wavenumber(frequencies: np.ndarray, speed_of_sound: float) -> float:
    return speed_of_sound


def _single_frequency(levels: np.ndarray, frequency: float) -> float:
    return frequency


def _tones(tone_frequencies: np.ndarray, tone_levels: np.ndarray) -> float:
    return 0.0


def _modes(damping_ratio: np.ndarray, damped_natural_frequency_hz: np.ndarray) -> float:
    return 0.0


class _Contour:
    """A stub record whose method takes its axis beside the levels."""

    def sound_power(self, levels: np.ndarray, frequencies: np.ndarray) -> float:
        return 0.0


def test_a_frequency_axis_beside_its_values_is_written_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two arrays of one length bind either way round without a complaint, so
    an axis beside the values it labels has to be named, and so has an array
    whose name ends in a frequency word (``tone_frequencies`` beside the tone
    levels, a natural frequency per mode beside the damping of each mode). An
    axis that is the only array, an axis already behind the ``*`` and a single
    frequency typed as a number pass; a method is held to the rule as a
    function is.
    """
    for function in (
        _criterion,
        _criterion_by_name,
        _wavenumber,
        _single_frequency,
        _tones,
        _modes,
    ):
        monkeypatch.setattr(function, "__module__", "phonometry.room.stub")
    monkeypatch.setattr(_Contour, "__module__", "phonometry.room.stub")
    stub = types.ModuleType("phonometry.stub")
    stub.__all__ = [  # type: ignore[attr-defined]
        "criterion",
        "criterion_by_name",
        "wavenumber",
        "single_frequency",
        "tones",
        "modes",
        "Contour",
    ]
    stub.criterion = _criterion  # type: ignore[attr-defined]
    stub.criterion_by_name = _criterion_by_name  # type: ignore[attr-defined]
    stub.wavenumber = _wavenumber  # type: ignore[attr-defined]
    stub.single_frequency = _single_frequency  # type: ignore[attr-defined]
    stub.tones = _tones  # type: ignore[attr-defined]
    stub.modes = _modes  # type: ignore[attr-defined]
    stub.Contour = _Contour  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield "phonometry.stub", stub

    monkeypatch.setattr(cpu, "public_modules", modules)
    found, stale = cpu.positional_frequency_axes()
    assert sorted((entry.qualname, axis, values) for entry, axis, values in found) == [
        ("_Contour.sound_power", "frequencies", ("levels",)),
        ("criterion", "frequencies", ("levels",)),
        ("modes", "damped_natural_frequency_hz", ("damping_ratio",)),
        ("tones", "tone_frequencies", ("tone_levels",)),
    ]
    assert stale == []


def test_a_frequency_axis_exemption_nothing_needs_is_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = ("phonometry.room.stub", "criterion_gone")
    monkeypatch.setitem(cpu.FREQUENCY_AXIS_EXEMPT, key, "a reason")
    _, stale = cpu.positional_frequency_axes()
    assert key in stale


def test_the_tree_writes_every_frequency_axis_by_name() -> None:
    assert cpu.positional_frequency_axes() == ([], [])


@pytest.mark.parametrize(
    "annotation",
    [
        "ArrayLike",
        "NDArray[np.float64] | list[float]",
        "Sequence[float] | np.ndarray",
        "tuple[float, ...]",
    ],
)
def test_an_array_of_numbers_is_read_off_the_annotation(annotation: str) -> None:
    assert cpu.holds_an_array(annotation)


@pytest.mark.parametrize(
    "annotation",
    [
        "float",
        "tuple[float, float]",
        "Sequence[Layer] | Layer",
        inspect.Parameter.empty,
    ],
)
def test_a_number_a_pair_or_a_sequence_of_records_is_not(annotation: object) -> None:
    assert not cpu.holds_an_array(annotation)


def test_every_condition_on_the_tree_is_written_by_name() -> None:
    _, loose, _ = cpu.offenders()
    assert loose == []


_OCTAVES = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (phonometry.io.Signal, (np.zeros(4), 8000, 1.0)),
        (phonometry.noise_control.LiquidPipe, (0.1, 0.005, 7800.0, 5000.0)),
        (phonometry.environment.ground_attenuation, (200.0, 2.0, 2.0, _OCTAVES)),
        (phonometry.signals.sound_exposure, (np.zeros(8), 8, 8.0)),
        (phonometry.room.noise_criterion, (np.full(8, 40.0), _OCTAVES)),
        (phonometry.underwater.FluidSeabed, (1800.0, 1700.0, 1025.0)),
        (phonometry.psychoacoustics.assess_tones, ([200.0], [40.0], [50.0], 2.7)),
    ],
)
def test_a_condition_or_an_axis_passed_by_position_is_refused(
    function: Callable[..., object], args: tuple[object, ...]
) -> None:
    """The keyword rule holds at the call, not only in the guard's walk: a
    condition or a frequency axis written by position raises instead of
    binding to the next parameter.
    """
    with pytest.raises(TypeError, match=rf"{function.__name__}.*takes .*positional"):
        function(*args)
