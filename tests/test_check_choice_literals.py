#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that holds every fixed choice of the public API to a ``Literal``.

``scripts/check_choice_literals.py`` reads each public string parameter and
field and calls it a closed choice when the function itself treats it as one:
it hands it to a shared validator, compares it with a set of strings, looks it
up by key, documents two quoted options or more, or passes it on untouched to
a function that does one of those. A closed choice typed ``str`` fails, and a
string that is open by its nature goes in ``OPEN`` with its reason. These
tests pin each way a choice is recognised, the hatch, and the package itself,
and that every vocabulary typed ``Literal`` offers exactly what its table
holds.
"""

from __future__ import annotations

import ast
import enum
import inspect
import pathlib
import sys
import textwrap
import typing
from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_choice_literals as ccl

from phonometry._internal.frozen import OwnsArrays
from phonometry._internal.validation import require_choice
from phonometry.filters.weighting import time_weighting

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import pytest


def _tree(function: object) -> ast.AST:
    return ast.parse(textwrap.dedent(inspect.getsource(function)))  # type: ignore[arg-type]


def _compared(mode: str) -> str:
    if mode not in ("fast", "slow"):
        raise ValueError(mode)
    return mode


def _equal(mode: str) -> bool:
    return mode == "fast"


def _validated(mode: str) -> str:
    return require_choice(mode, "mode", ("fast", "slow"))


def _passed_on(x: list[float], mode: str) -> object:
    return time_weighting(x, 48000, mode=mode)  # type: ignore[arg-type]


def _free(label: str) -> str:
    return label.upper()


#: A table a caller hands a helper beside the text it checks.
_SIDE_TABLE = {"left": 1, "right": 2}


class _Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


def _normalised(mode: str) -> bool:
    return str(mode).strip().lower() in ("fast", "slow")


def _resolve(text: str) -> str:
    return text


def _derived(mode: str) -> int:
    key = _resolve(mode)
    if key not in ("fast", "slow"):
        raise ValueError(key)
    return 0


def _check_against(name: str, table: dict[str, int]) -> int:
    key = name.lower()
    if key not in table:
        raise ValueError(name)
    return table[key]


def _hands_a_table(side: str) -> int:
    return _check_against(side, _SIDE_TABLE)


def _spreads(x: list[float], mode: str) -> object:
    options = {"mode": mode}
    return time_weighting(x, 48000, **options)  # type: ignore[arg-type]


def _imports_inside(x: list[float], mode: str) -> object:
    from phonometry.filters.weighting import time_weighting as weigh

    return weigh(x, 48000, mode=mode)  # type: ignore[arg-type]


def _documented(mode: str) -> None:
    """Take a mode.

    :param mode: ``"fast"`` or ``"slow"``.
    """


#: The sides a collection of strings is checked against, below.
_SIDES = ("left", "right", "top", "bottom")


def _set_difference(sides: Sequence[str]) -> None:
    unknown = set(sides) - set(_SIDES)
    if unknown:
        raise ValueError(sorted(unknown))


def _subset(sides: Sequence[str]) -> bool:
    return set(sides) <= set(_SIDES)


def _issubset(sides: Sequence[str]) -> bool:
    return set(sides).issubset(_SIDES)


def _issuperset(sides: Sequence[str]) -> bool:
    return set(_SIDES).issuperset(sides)


def _one_or_several(sides: str | Iterable[str]) -> tuple[str, ...]:
    named = (sides,) if isinstance(sides, str) else tuple(sides)
    if set(named) - set(_SIDES):
        raise ValueError(named)
    return named


def _once_each(sides: Sequence[str]) -> tuple[str, ...]:
    rows = tuple(dict.fromkeys(sides))
    for side in rows:
        if side not in _SIDES:
            raise ValueError(side)
    return rows


def _item_by_item(levels: dict[str, float]) -> None:
    for side, level in levels.items():
        if side not in _SIDES or level < 0.0:
            raise ValueError(side)


def _held_table(sides: Sequence[str]) -> None:
    table = _SIDES
    if set(sides) - set(table):
        raise ValueError(sides)


def _picked_table(sides: Sequence[str], *, strict: bool) -> None:
    table = _SIDES if strict else ("top", "bottom")
    if set(sides) - set(table):
        raise ValueError(sides)


#: A table of tables, one picked by the caller's kind.
_TABLES = {"plan": _SIDES, "section": ("up", "down")}


def _one_of_the_tables(levels: dict[str, float], kind: str) -> None:
    table = _TABLES[kind]
    unknown = [key for key in levels if key not in table]
    if unknown:
        raise ValueError(unknown)


#: A frozen table the source builds with code, whose keys only the running
#: module holds.
_BUILT = MappingProxyType(dict.fromkeys(name.lower() for name in ("North", "South")))


def _built_table(sides: Sequence[str]) -> None:
    if set(sides) - set(_BUILT):
        raise ValueError(sides)


def _a_set_copy(limits: Mapping[str, float]) -> None:
    given = {str(direction) for direction in limits}
    if given - set(_SIDES):
        raise ValueError(sorted(given))


def _a_list_copy(sides: Sequence[str]) -> None:
    names = [side.strip().lower() for side in sides]
    if set(names) - set(_SIDES):
        raise ValueError(names)


#: An alias that hides a collection of any strings behind a name.
_FreeSides = Iterable[str]

#: An alias of the options, which stays a closed choice once spelled out.
_Side = Literal["left", "right"]


def _one_looked_for(sides: Sequence[str]) -> bool:
    return "top" in sides


def _a_label(labels: Sequence[str]) -> bool:
    return any(label == "" for label in labels)


def _check_travel(travel: str) -> None:
    if travel not in ("up", "down"):
        raise ValueError(travel)


@dataclass(frozen=True)
class _Wave(OwnsArrays):
    """A record whose field a helper checks, its __post_init__ wrapped."""

    travel: str

    def __post_init__(self) -> None:
        _check_travel(self.travel)


@dataclass(frozen=True)
class _Source:
    """A record whose field the module checks where it is used."""

    direction: str


def _place(source: _Source) -> int:
    if source.direction not in ("down", "up"):
        raise ValueError(source.direction)
    return 0


class _Elsewhere:
    """Another class's attribute of the same name is not the record's field."""

    label = "x"

    def title(self) -> bool:
        return self.label == "probes"


@dataclass(frozen=True)
class _Labelled:
    label: str


def test_a_collection_of_strings_is_read_as_a_choice() -> None:
    """A collection of ``str``, alone or in a union, or a mapping keyed by
    ``str``, takes the choice one string at a time; a typed item does not.
    """
    for annotation in (
        "Sequence[str]",
        "str | Iterable[str] | None",
        "tuple[str, ...]",
        "frozenset[str]",
        "collections.abc.Sequence[str]",
        "Mapping[str, float] | None",
        "dict[str, tuple[NDArray[np.float64], NDArray[np.float64]]]",
    ):
        assert ccl.takes_any_strings(annotation), annotation
    for annotation in (
        "tuple[str, str]",
        "Sequence[Side]",
        "Mapping[int, str]",
        "list[float]",
        "str",
    ):
        assert not ccl.takes_any_strings(annotation), annotation


def test_a_literal_inside_a_collection_is_a_literal() -> None:
    """Handing a collection to a parameter of Literal items is a choice."""
    assert ccl._is_literal("Sequence[Literal['a', 'b']]")
    assert ccl._is_literal("Mapping[Literal['a'], float] | None")
    assert not ccl._is_literal("Sequence[str]")


def test_a_set_difference_or_subset_against_strings_is_a_choice() -> None:
    """What is left once the options are taken away is refused, or the
    collection is tested as a subset of them: either way its strings are a
    closed set.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function in (_set_difference, _subset, _issubset, _issuperset):
        found = ccl.code_evidence(
            _tree(function), ccl._the_name("sides"), constants, collection=True
        )
        assert found, function.__name__


def test_the_strings_held_in_a_local_are_followed() -> None:
    """``(x,)``, ``tuple(x)`` and ``dict.fromkeys(x)`` hold the caller's strings."""
    constants = ccl._module_constants(sys.modules[__name__])
    for function in (_one_or_several, _once_each):
        found = ccl.code_evidence(
            _tree(function), ccl._the_name("sides"), constants, collection=True
        )
        assert found, function.__name__


def test_a_table_held_in_a_local_is_the_table_written_in_place() -> None:
    """``table = _SIDES``, a table picked by a conditional expression and one
    table of a table of tables are the sets of strings they hold.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function, name in (
        (_held_table, "sides"),
        (_picked_table, "sides"),
        (_one_of_the_tables, "levels"),
    ):
        found = ccl.code_evidence(
            _tree(function), ccl._the_name(name), constants, collection=True
        )
        assert found, function.__name__


def test_a_table_of_tables_holds_the_keys_of_all_its_tables() -> None:
    """Whichever table is picked, a key of any of them is an option."""
    constants = ccl._module_constants(sys.modules[__name__])
    picked = ast.parse("_TABLES[kind]", mode="eval").body
    assert set(ccl.strings_of(picked, constants)) == {*_SIDES, "up", "down"}
    # A table of numbers is no set of strings.
    assert (
        ccl.strings_of(ast.parse("_SIDE_TABLE[k]", mode="eval").body, constants) == ()
    )


def test_a_frozen_table_built_with_code_is_read_off_the_module() -> None:
    """The keys of a table the source builds when it runs come from the module."""
    constants = ccl._module_constants(sys.modules[__name__])
    assert set(ccl.strings_of(ast.Name(id="_BUILT"), constants)) == {"north", "south"}
    found = ccl.code_evidence(
        _tree(_built_table), ccl._the_name("sides"), constants, collection=True
    )
    assert found == ["a set difference with a set of strings"]


def test_a_comprehension_that_copies_the_items_is_followed() -> None:
    """``{str(d) for d in limits}`` and ``[s.lower() for s in sides]`` hold the
    caller's strings, so a set difference on the copy closes the original.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    for function, name in ((_a_set_copy, "limits"), (_a_list_copy, "sides")):
        found = ccl.code_evidence(
            _tree(function), ccl._the_name(name), constants, collection=True
        )
        assert "a set difference with a set of strings" in found, function.__name__


def test_an_alias_is_read_as_what_it_stands_for() -> None:
    """A collection of strings behind an alias takes any strings; an alias of
    the options stays a ``Literal``, and a quoted option is never a name.
    """
    read = ccl.expanded("_FreeSides | None", __name__)
    assert read == "Iterable[str] | None"
    assert ccl.takes_any_strings(read)
    assert ccl._is_literal(ccl.expanded("Sequence[_Side]", __name__))
    assert ccl.expanded("Literal['_FreeSides']", __name__) == "Literal['_FreeSides']"


def test_a_table_imported_from_a_sibling_module_is_followed() -> None:
    """``from .fdtd import _SIDES`` gives the elastic engine the acoustic one's
    sides, read where they are written, and a set difference with them closes
    a collection of sides.
    """
    from phonometry.simulation import elastic_fdtd

    constants = ccl._constants_of(elastic_fdtd.__name__)
    assert set(ccl.strings_of(ast.Name(id="_SIDES"), constants)) == {
        "left",
        "right",
        "top",
        "bottom",
    }
    tree = ast.parse("def f(sides):\n    return set(sides) - set(_SIDES)\n")
    found = ccl.code_evidence(
        tree, ccl._the_name("sides"), dict(constants), collection=True
    )
    assert found == ["a set difference with a set of strings"]


def test_each_item_and_each_key_is_read() -> None:
    """A loop over the items, or over the keys of ``.items()``, checks each."""
    constants = ccl._module_constants(sys.modules[__name__])
    found = ccl.code_evidence(
        _tree(_item_by_item), ccl._the_name("levels"), constants, collection=True
    )
    assert "each item 'in' a set of strings" in found


def test_one_string_looked_for_in_a_collection_is_a_choice() -> None:
    """``"top" in sides`` names one option, as ``side == "top"`` does."""
    found = ccl.code_evidence(
        _tree(_one_looked_for), ccl._the_name("sides"), {}, collection=True
    )
    assert found == ["'top' 'in' it"]


def test_an_empty_text_is_no_option() -> None:
    """``label == ""`` asks whether a label was written, not which."""
    found = ccl.code_evidence(
        _tree(_a_label), ccl._the_name("labels"), {}, collection=True
    )
    assert found == []


def test_a_field_handed_to_a_helper_is_followed() -> None:
    """``__post_init__`` hands ``self.<field>`` to a helper that checks it, and
    the wrapper a record's ``__post_init__`` gets does not hide the helper.
    """
    assert hasattr(vars(_Wave)["__post_init__"], "__wrapped__")
    found = ccl._field_evidence(_Wave, "travel", {}, collection=False)
    assert found == ["handed to _check_travel(travel)"]


def test_a_field_compared_where_it_is_used_is_a_choice() -> None:
    """A field the record does not check is checked by the function that
    reads it; ``self.<name>`` of another class only shares the name.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    found = ccl.compared_in_module(_Source, "direction", constants)
    assert found == ["'in' a set of strings in _place()"]
    assert ccl.compared_in_module(_Labelled, "label", constants) == []


def test_a_catalogue_row_constructor_is_passed_over() -> None:
    """A catalogue row takes its cells as text by the catalogue contract."""
    from phonometry._internal.catalogue import CatalogueRow

    for home, qualname, _ in ccl._targets():
        owner = qualname.partition(".")[0]
        cls = getattr(sys.modules[home], owner, None)
        if qualname.endswith(".__init__") and isinstance(cls, type):
            assert not issubclass(cls, CatalogueRow), qualname


def test_a_membership_test_against_strings_is_a_choice() -> None:
    """``mode not in ("fast", "slow")`` is the commonest closed choice."""
    found = ccl.code_evidence(_tree(_compared), ccl._the_name("mode"), {})
    assert "'in' a set of strings" in found


def test_an_equality_with_a_string_is_a_choice() -> None:
    """``mode == "fast"`` names one option, so the set is closed."""
    found = ccl.code_evidence(_tree(_equal), ccl._the_name("mode"), {})
    assert "== 'fast'" in found


def test_a_shared_validator_is_a_choice() -> None:
    """``require_choice`` refuses anything but its options."""
    found = ccl.code_evidence(_tree(_validated), ccl._the_name("mode"), {})
    assert "require_choice()" in found


def test_a_parameter_passed_on_to_a_literal_is_a_choice() -> None:
    """Handing the text to a ``Literal`` parameter makes it the same choice."""
    found = ccl.passed_on_evidence(_passed_on, "mode")
    assert found == ["handed to time_weighting(mode)"]


def test_a_str_inside_a_union_is_read_as_a_choice() -> None:
    """``str | float`` lets any string through as surely as ``str`` alone.

    So does the ``Literal[...] | str`` the guide forbids, while a ``str``
    nested inside another type (``Mapping[str, float]``) is not the choice.
    """
    assert ccl.takes_any_string("str | float | np.ndarray | None")
    assert ccl.takes_any_string("Literal['zero', 'first'] | str")
    assert ccl.takes_any_string("Optional[str]")
    assert not ccl.takes_any_string("Literal['zero', 'first'] | float | None")
    assert not ccl.takes_any_string("Mapping[str, float] | None")


def test_a_text_cleaned_up_before_the_check_is_a_choice() -> None:
    """``str(mode).strip().lower() in (...)`` checks the caller's choice."""
    found = ccl.code_evidence(_tree(_normalised), ccl._the_name("mode"), {})
    assert "'in' a set of strings" in found


def test_a_local_bound_from_the_text_is_followed() -> None:
    """``key = _resolve(mode)`` and then ``key not in (...)`` is the same check."""
    found = ccl.code_evidence(_tree(_derived), ccl._the_name("mode"), {})
    assert "'in' a set of strings" in found


def test_a_table_handed_on_beside_the_text_closes_the_helper() -> None:
    """The helper's ``key not in table`` is closed by the caller's table."""
    found = ccl.passed_on_evidence(_hands_a_table, "side")
    assert found == ["handed to _check_against(name)"]


def test_a_parameter_spread_from_a_dict_is_followed() -> None:
    """``f(**options)`` hands each key of the dict to the parameter it names."""
    found = ccl.passed_on_evidence(_spreads, "mode")
    assert found == ["handed to time_weighting(mode)"]


def test_a_function_the_body_imports_is_followed() -> None:
    """A call to a name the body imports itself reaches the library function."""
    found = ccl.passed_on_evidence(_imports_inside, "mode")
    assert found == ["handed to time_weighting(mode)"]


def test_a_str_beside_an_enum_is_a_choice() -> None:
    """``_Colour | str`` takes the members or the strings they stand for."""
    module = sys.modules[__name__]
    assert ccl.enum_beside("_Colour | str", module) == ["a str beside the Enum _Colour"]
    assert ccl.enum_beside("float | str", module) == []


def test_a_free_text_is_not_a_choice() -> None:
    """A label that is only transformed is open text, and nothing is reported."""
    assert ccl.code_evidence(_tree(_free), ccl._the_name("label"), {}) == []
    assert ccl.passed_on_evidence(_free, "label") == []


def test_two_quoted_options_in_the_docstring_are_a_choice() -> None:
    """The documented options count even when the body checks nothing."""
    assert ccl.documented_options(_documented.__doc__, "mode") == ("fast", "slow")


def test_a_stale_open_entry_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exemption that names nothing the walk finds cannot outlive its reason."""
    key = ("phonometry.nowhere", "gone", "mode")
    monkeypatch.setitem(ccl.OPEN, key, "a reason that no longer applies")
    found, stale = ccl.offenders()
    assert found == []
    assert stale == [key]


def test_every_public_choice_of_the_package_is_a_literal() -> None:
    """The package passes: no closed choice is typed ``str``, no entry is stale."""
    found, stale = ccl.offenders()
    assert found == []
    assert stale == []


def _closed(pairs: list[tuple[object, object]]) -> list[tuple[object, object]]:
    """The pairs whose two sides differ, with the alias read as a set."""
    return [
        (alias, options)
        for alias, options in pairs
        if set(typing.get_args(alias)) != set(options)  # type: ignore[call-overload]
    ]


def test_every_vocabulary_offers_what_its_table_holds() -> None:
    """A ``Literal`` and the table that answers it name the same options.

    The alias is what a type checker holds the caller to and the table is
    what the function reads, so an option in one and not the other is either
    refused by the checker and accepted when the call runs, or the reverse.
    """
    from phonometry._internal import catalogue
    from phonometry.aircraft import measurement_system
    from phonometry.building.measurement import survey_insulation, uncertainty
    from phonometry.building.prediction import panel_transmission
    from phonometry.electroacoustics import headphones
    from phonometry.emission import free_field_qualification
    from phonometry.environment.assessment import soundscape, soundscape_binaural
    from phonometry.environment.sources import (
        cnossos_rail,
        cnossos_road,
        rolling_stock_noise,
        track_decay,
    )
    from phonometry.hearing import sound_field_audiometry
    from phonometry.materials.absorbers import porous, suspended_ceilings
    from phonometry.metrology import (
        comparison_calibration,
        free_field_corrections,
        reciprocity_calibration,
        sound_level_meter,
    )
    from phonometry.noise_control import (
        _duct_path,
        duct_modes,
        enclosure_insulation,
        silencers,
    )
    from phonometry.underwater.bioacoustics import audiograms
    from phonometry.underwater.bioacoustics import weighting as hearing
    from phonometry.underwater.sources import ship_traffic_noise
    from phonometry.vibration.human import exposure, signal_burst
    from phonometry.vibration.immission import coupling, train_categories

    rooms = {key for row in survey_insulation._TABLE3.values() for key in row}
    # A duct section's dimensions are spread into plane_wave_limit as its
    # keywords; the flow and the speed of sound are not dimensions.
    dimensions = set(inspect.signature(duct_modes.plane_wave_limit).parameters) - {
        "flow_velocity",
        "speed_of_sound",
    }
    groups = {key for table in hearing._PARAMETERS.values() for key in table}
    # The base standards of Table 1 of ISO 11546, by the quantity each row
    # gives: a sound power (D_W...) or a sound pressure level (D_p, D_pA).
    methods = [row for rows in enclosure_insulation._METHODS.values() for row in rows]
    power = {
        row.base_standard
        for row in methods
        if any(q.startswith("D_W") for q in row.quantities)
    }
    pressure = {
        row.base_standard
        for row in methods
        if any(q in {"D_p", "D_pA"} for q in row.quantities)
    }
    comparison = comparison_calibration
    reciprocity = reciprocity_calibration
    pairs: list[tuple[object, object]] = [
        (exposure.WeightingName, exposure._WEIGHTINGS),
        (signal_burst.BurstApplication, signal_burst.SAWTOOTH_BURST_TESTS),
        (train_categories.TrainKind, train_categories.TRAIN_KINDS),
        (coupling.DisplayedQuantity, coupling.INSTRUMENT_CONFIDENCE_LIMITS_PERCENT),
        (audiograms.AudiogramGroup, audiograms._AUDIOGRAM_ORIGINAL),
        (hearing.HearingGroup, groups),
        (ship_traffic_noise.VesselClass, ship_traffic_noise._VESSEL_CLASSES),
        (
            uncertainty.SingleNumberQuantity,
            set(uncertainty._SINGLE) | set(uncertainty._ALIASES),
        ),
        (survey_insulation.SurveyRoom, rooms),
        (panel_transmission.PlateauMaterialName, panel_transmission.PLATEAU_MATERIALS),
        (porous.DelanyBazleyPreset, porous.DELANY_BAZLEY_COEFFICIENTS),
        (suspended_ceilings.MountingLetter, suspended_ceilings.MOUNTING_TYPES),
        (
            enclosure_insulation.TestEnvironmentStandard,
            enclosure_insulation.TEST_ENVIRONMENT_REQUIREMENTS,
        ),
        (
            cnossos_road.RoadVehicleCode,
            [member.value for member in cnossos_road.RoadVehicleCategory],
        ),
        (
            cnossos_road.RoadSurfaceName,
            [member.value for member in cnossos_road.RoadSurface],
        ),
        (cnossos_rail.BrakeCode, [member.value for member in cnossos_rail.BrakeType]),
        (
            cnossos_rail.RailRoughnessCode,
            [member.value for member in cnossos_rail.RailRoughnessClass],
        ),
        (
            cnossos_rail.TrackTransferCode,
            [member.value for member in cnossos_rail.TrackTransferClass],
        ),
        (
            cnossos_rail.TractionVehicleName,
            [member.value for member in cnossos_rail.TractionVehicle],
        ),
        (
            cnossos_rail.BridgeTypeName,
            [member.value for member in cnossos_rail.BridgeType],
        ),
        (catalogue.ProvenanceKind, catalogue.PROVENANCE_KINDS),
        (measurement_system.LinearityRange, measurement_system._LINEARITY_LIMITS),
        (headphones.TransducerPrinciple, headphones.TRANSDUCER_PRINCIPLES),
        (headphones.EarphoneType, headphones.EARPHONE_TYPES),
        (headphones.AcousticCoupling, headphones.ACOUSTIC_COUPLINGS),
        (headphones.BackRadiation, headphones.BACK_RADIATIONS),
        (free_field_qualification.PathTarget, free_field_qualification._PATH_TARGETS),
        (
            soundscape.AffectiveQuality,
            soundscape.PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES,
        ),
        (soundscape_binaural.BinauralRow, soundscape_binaural.BINAURAL_PARAMETERS),
        (
            sound_field_audiometry.SoundFieldPosition,
            sound_field_audiometry._DIFFUSE_POSITIONS,
        ),
        (
            sound_field_audiometry.LateralPosition,
            sound_field_audiometry._LATERAL_POSITIONS,
        ),
        (
            free_field_corrections.TableI1Descriptor,
            free_field_corrections.IEC62585_TABLE_I1,
        ),
        (sound_level_meter.MeterWeighting, sound_level_meter._WEIGHTINGS),
        (sound_level_meter.WeightingVersusA, sound_level_meter._WEIGHTINGS_VS_A),
        (sound_level_meter.DisplayVersusF, sound_level_meter._TIME_WEIGHTINGS_VS_F),
        (sound_level_meter.ToneburstResponse, sound_level_meter._TONEBURST_KEYS),
        (sound_level_meter.RangeReading, sound_level_meter._RANGE_READINGS),
        (sound_level_meter.SlmRequirement, sound_level_meter.SLM_PERIODIC_REQUIREMENTS),
        (sound_level_meter.SlmClause, set(sound_level_meter._CLAUSES.values())),
        (silencers.SilencerDimension, silencers._GEOMETRY_KEYS),
        (_duct_path.DuctSectionDimension, dimensions),
        (signal_burst.BurstQuantity, signal_burst.BURST_TOLERANCE_PERCENT),
        (comparison.PressureComparisonComponent, comparison.IEC61094_5_TABLE_D1),
        (comparison.FreeFieldComparisonComponent, comparison.IEC61094_8_TABLE_2),
        (
            comparison.ComparisonComponent,
            {*comparison.IEC61094_5_TABLE_D1, *comparison.IEC61094_8_TABLE_2},
        ),
        (reciprocity.PressureReciprocityComponent, reciprocity.IEC61094_2_TABLE_1),
        (reciprocity.FreeFieldReciprocityComponent, reciprocity.IEC61094_3_TABLE_1),
        (
            reciprocity.ReciprocityComponent,
            {*reciprocity.IEC61094_2_TABLE_1, *reciprocity.IEC61094_3_TABLE_1},
        ),
        (enclosure_insulation.SoundPowerStandard, power),
        (enclosure_insulation.SoundPressureStandard, pressure),
        (track_decay.Direction, track_decay.TRACK_DECAY_DIRECTIONS),
        (
            track_decay.Direction,
            rolling_stock_noise.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M,
        ),
    ]
    assert _closed(pairs) == []


def test_an_area_type_is_one_every_limit_table_prints() -> None:
    """RD 1367 area ``f`` has no row in Tables A, A1, A2 or B1, so it is no option.

    Each option, a letter or an alias, resolves to a row of all four tables.
    """
    from phonometry.environment.assessment import spain

    tables = (
        spain._OUTDOOR_OBJECTIVES,
        spain._INFRASTRUCTURE_LIMITS,
        spain._MAX_INFRASTRUCTURE_LIMITS,
        spain._ACTIVITY_LIMITS,
    )
    resolved = {spain._AREA_ALIASES.get(o, o) for o in typing.get_args(spain.AreaType)}
    assert all(resolved == set(table) for table in tables)
