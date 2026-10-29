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
import importlib.util
import inspect
import pathlib
import sys
import textwrap
import typing
from collections.abc import Callable, Iterable, Mapping
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
    from collections.abc import Sequence

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


def test_an_imported_alias_is_read_where_it_is_written(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``NamesOrNone = _Names | None`` imported alone names the ``_Names`` of
    its own module, which the importing module does not hold; read where it is
    written, it takes any strings all the same.
    """
    sources = {
        "_alias_home": (
            "from collections.abc import Iterable\n\n"
            "_Names = Iterable[str]\n"
            "NamesOrNone = _Names | None\n"
        ),
        "_alias_user": (
            "from ._alias_home import NamesOrNone\n\n\n"
            "def pick(names: NamesOrNone = None) -> None:\n"
            "    del names\n"
        ),
    }
    for stem, text in sources.items():
        path = tmp_path / f"{stem}.py"
        path.write_text(text, encoding="utf-8")
        name = f"phonometry.{stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    read = ccl.expanded("NamesOrNone", "phonometry._alias_user")
    assert read == "Iterable[str] | None"
    assert ccl.takes_any_strings(read)


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


def test_a_string_below_the_top_level_is_read_as_it_stands() -> None:
    """The columns of each row, or the items of each list, are not followed.

    ``verify_signal_burst_response(measured)`` read the columns of each burst
    length against the printed ones while the annotation let any string in;
    a key one level down is called a choice by its annotation alone.
    """
    assert ccl.takes_nested_strings("Mapping[int, Mapping[str, float]]")
    assert ccl.takes_nested_strings("Sequence[Sequence[str]]")
    assert ccl.takes_nested_strings("tuple[Mapping[str, Any], ...] | None")
    assert ccl.takes_nested_strings("Mapping[int, tuple[Sequence[str], float]]")
    assert not ccl.takes_nested_strings("Mapping[str, float]")
    assert not ccl.takes_nested_strings("Mapping[int, str]")
    assert not ccl.takes_nested_strings(
        "Mapping[int, Mapping[Literal['rms', 'vdv'], float]]"
    )


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


def test_a_class_written_into_between_two_methods_is_still_read_whole() -> None:
    """The methods of a class are read off its namespace as it was at the start.

    Reading a class's annotations on Python 3.14 stores them in its namespace,
    and what the walk does with one method may read them before the next; a
    namespace that grows while its methods are handed out must neither stop
    the walk nor change it.
    """

    class _Grows:
        def first(self, mode: str) -> str:
            return mode

        def second(self, mode: str) -> str:
            return mode

    names = []
    for name, _ in ccl._public_methods(_Grows):
        names.append(name)
        setattr(_Grows, f"added_after_{name}", lambda self: None)
    assert names == ["first", "second"]


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
        (
            comparison.SharedComparisonComponent,
            set(comparison.IEC61094_5_TABLE_D1) & set(comparison.IEC61094_8_TABLE_2),
        ),
        (reciprocity.PressureReciprocityComponent, reciprocity.IEC61094_2_TABLE_1),
        (reciprocity.FreeFieldReciprocityComponent, reciprocity.IEC61094_3_TABLE_1),
        (
            reciprocity.ReciprocityComponent,
            {*reciprocity.IEC61094_2_TABLE_1, *reciprocity.IEC61094_3_TABLE_1},
        ),
        (
            reciprocity.SharedReciprocityComponent,
            set(reciprocity.IEC61094_2_TABLE_1) & set(reciprocity.IEC61094_3_TABLE_1),
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


# --------------------------------------------------------------------------
# One spelling (rule A45): a choice typed Literal is checked as written.

#: The options of the synthetic choices below.
_Pace = Literal["fast", "slow"]
_PACES: tuple[_Pace, ...] = ("fast", "slow")


def _folded_before_the_check(mode: _Pace) -> str:
    key = mode.strip().lower()
    return require_choice(key, "mode", _PACES)


def _checked_before_the_fold(mode: _Pace) -> str:
    named = require_choice(mode, "mode", _PACES)
    return named.upper()


def _refused_before_the_fold(mode: _Pace) -> str:
    if mode not in _PACES:
        raise ValueError(mode)
    return mode.title()


def _made_a_text(mode: _Pace) -> str:
    return require_choice(
        str(mode),
        "mode",
        _PACES,
    )


def _lowered(text: str) -> str:
    return text.lower()


def _folded_by_a_helper(mode: _Pace) -> str:
    return require_choice(_lowered(mode), "mode", _PACES)


def _checks(text: object) -> _Pace:
    return require_choice(text, "mode", _PACES)


def _checked_by_a_helper(mode: _Pace) -> str:
    _checks(mode)
    return mode.casefold()


def _folded_after_a_private_helper(mode: _Pace) -> bool:
    return _resolve(mode).upper() == "FAST"


#: Spellings no option lists, mapped to one.
_UNLISTED_ALIASES = {"quick": "fast"}

#: A spelling the Literal lists on purpose, mapped to the option it stands for.
_LISTED_ALIASES = {"slow": "fast"}


def _maps_an_unlisted_alias(mode: _Pace) -> str:
    key = _UNLISTED_ALIASES.get(mode, mode)
    return require_choice(key, "mode", _PACES)


def _maps_a_listed_alias(mode: _Pace) -> str:
    key = _LISTED_ALIASES.get(mode, mode)
    return require_choice(key, "mode", _PACES)


def _items_folded(sides: Sequence[_Side]) -> set[str]:
    return {side.lower() for side in sides if side.lower() in ("left", "right")}


def _keys_checked_as_a_whole(levels: Mapping[_Side, float]) -> set[str]:
    extra = set(levels) - {"left", "right"}
    if extra:
        raise ValueError(sorted(extra))
    return {str(side) for side in levels}


def _cleaned(
    function: object, name: str, *, options: tuple[str, ...], collection: bool = False
) -> list[str]:
    reading = ccl._received(
        function,
        name,
        options=frozenset(options),
        collection=collection,
        depth=0,
    )
    return ccl._cleans_up_first(reading)


def test_a_clean_up_before_the_check_is_refused() -> None:
    """``mode.strip().lower()`` ahead of ``require_choice`` lets ``" FAST "`` in."""
    assert _cleaned(_folded_before_the_check, "mode", options=_PACES) == [
        ".lower()",
        ".strip()",
    ]


def test_a_check_as_written_before_the_clean_up_passes() -> None:
    """A clean-up after the text is checked as written accepts nothing more."""
    assert _cleaned(_checked_before_the_fold, "mode", options=_PACES) == []
    assert _cleaned(_refused_before_the_fold, "mode", options=_PACES) == []


def test_a_text_made_of_any_value_is_a_clean_up() -> None:
    """``str(mode)`` takes ``2`` for ``"2"``, on a line of its own or not."""
    assert _cleaned(_made_a_text, "mode", options=_PACES) == ["str()"]


def test_a_clean_up_in_a_helper_is_followed() -> None:
    """The helper folds the text it is handed before anyone checks it."""
    assert _cleaned(_folded_by_a_helper, "mode", options=_PACES) == [
        "handed to _lowered(text), .lower()"
    ]


def test_a_check_in_a_helper_is_a_check_where_it_is_called() -> None:
    """A helper that checks the text first checks it for its caller."""
    assert _cleaned(_checked_by_a_helper, "mode", options=_PACES) == []


def test_a_clean_up_of_what_a_private_helper_hands_back_is_one() -> None:
    """``_resolve(mode).upper()`` folds the text the helper hands back."""
    assert _cleaned(_folded_after_a_private_helper, "mode", options=_PACES) == [
        ".upper()"
    ]


def test_an_alias_the_literal_does_not_list_is_refused() -> None:
    """``ALIASES.get(mode, mode)`` with a key no option spells takes it in;
    a map of spellings the ``Literal`` lists on purpose accepts nothing more.
    """
    assert _cleaned(_maps_an_unlisted_alias, "mode", options=_PACES) == [
        "an alias map .get(text, text)"
    ]
    assert _cleaned(_maps_a_listed_alias, "mode", options=_PACES) == []


def test_the_items_of_a_collection_are_read_one_by_one() -> None:
    """Each item folded before its check is a clean-up; a leftover refused as
    a whole (``set(levels) - OPTIONS``) is a check of every key as written.
    """
    sides = ("left", "right")
    assert _cleaned(_items_folded, "sides", options=sides, collection=True) == [
        ".lower()"
    ]
    assert (
        _cleaned(_keys_checked_as_a_whole, "levels", options=sides, collection=True)
        == []
    )


@dataclass(frozen=True)
class _Checked:
    """A record that checks its choice as written when it is built."""

    pace: _Pace

    def __post_init__(self) -> None:
        require_choice(self.pace, "pace", _PACES)


@dataclass(frozen=True)
class _Unchecked:
    """A record that leaves its choice to whoever reads it."""

    stride: _Pace


def _reads_checked(record: _Checked) -> bool:
    return record.pace.lower() == "fast"


def _reads_unchecked(record: _Unchecked) -> bool:
    return record.stride.lower() == "fast"


def test_a_record_field_is_read_where_its_module_uses_it() -> None:
    """A field checked when the record is built may be cleaned up later; one
    that is not is cleaned up by the module that reads it.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    options = frozenset(_PACES)
    checked = ccl._field_spelling(
        _Checked, "pace", constants, options=options, collection=False
    )
    unchecked = ccl._field_spelling(
        _Unchecked, "stride", constants, options=options, collection=False
    )
    assert checked == []
    assert unchecked == [".lower() in _reads_unchecked()"]


def test_every_literal_choice_is_checked_as_written() -> None:
    """The package passes: no public choice typed ``Literal`` is cleaned up
    before its check, here or in a function it is handed to (rule A45).
    """
    assert list(ccl.cleaned_up_choices()) == []


#: Two route names, bound to constants a table is keyed by.
_PER_LEAF = "per_leaf"
_TOGETHER = "together"
_ROUTES = {_PER_LEAF: 40.0, _TOGETHER: 50.0}


def _route(quantity: str) -> float:
    if quantity not in _ROUTES:
        raise ValueError(quantity)
    return _ROUTES[quantity]


def test_a_table_keyed_by_named_constants_holds_their_strings() -> None:
    """``{_DNT_A: ...}`` is keyed by the text ``_DNT_A`` is bound to, so a
    ``str`` checked against it is a closed choice like one checked against
    ``{"DnT,A": ...}``.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    assert ccl.strings_of(ast.Name(id="_ROUTES"), constants) == ("per_leaf", "together")
    found = ccl.code_evidence(_tree(_route), ccl._the_name("quantity"), constants)
    assert found == ["'in' a set of strings", "a lookup by key"]


class _Pacer:
    """A class whose public method hands its choice to a method of its own."""

    def pace(self, mode: _Pace) -> bool:
        return self._matches(mode)

    def _matches(self, mode: str) -> bool:
        return mode.lower() in _PACES


@dataclass(frozen=True)
class _Holder:
    """A record whose public method hands its choice to an object it holds."""

    pacer: _Pacer

    def pace(self, mode: _Pace) -> bool:
        return self.pacer.pace(mode)


def test_a_clean_up_in_a_method_of_its_own_class_is_followed() -> None:
    """``self._matches(mode)`` and ``self.pacer.pace(mode)`` are followed
    into the method they call, through the class and through the annotation
    of the field that holds the object.
    """
    assert _cleaned(_Pacer.pace, "mode", options=_PACES) == [
        "handed to _Pacer._matches(mode), .lower()"
    ]
    assert _cleaned(_Holder.pace, "mode", options=_PACES) == [
        "handed to _Pacer.pace(mode), handed to _Pacer._matches(mode), .lower()"
    ]


#: The options of a check that also takes a spelling of its own.
_QUICK = {"quick": "fast"}


def _checked_against_more(mode: _Pace) -> str:
    named = require_choice(mode, "mode", (*_PACES, *_QUICK))
    return _QUICK.get(named, named)


def test_a_check_against_options_the_literal_does_not_list_is_refused() -> None:
    """``require_choice(mode, "mode", (*_PACES, *_QUICK))`` reads the text as
    written and still takes ``"quick"``, which no option spells.
    """
    constants = ccl._module_constants(sys.modules[__name__])
    starred = ast.parse("(*_PACES, *_QUICK)", mode="eval").body
    assert ccl.strings_of(starred, constants) == ("fast", "slow", "quick")
    assert _cleaned(_checked_against_more, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]
    assert _cleaned(_checked_before_the_fold, "mode", options=_PACES) == []


def _refused_against_more(mode: _Pace) -> str:
    if mode not in ("fast", "slow", "quick"):
        raise ValueError(mode)
    return mode.lower()


def _sides_held_to_more(sides: Sequence[_Side]) -> set[str]:
    if not set(sides) <= {"left", "right", "top"}:
        raise ValueError(sides)
    return {side.upper() for side in sides}


def _keys_held_to_more(levels: Mapping[_Side, float]) -> set[str]:
    extra = set(levels) - {"left", "right", "top"}
    if extra:
        raise ValueError(sorted(extra))
    return {side.upper() for side in levels}


def test_a_membership_test_against_options_the_literal_does_not_list_is_refused() -> (
    None
):
    """``if mode not in ("fast", "slow", "quick"): raise`` reads the text as
    written and still takes ``"quick"``; so do a subset test and a leftover
    refused as a whole against a set wider than the ``Literal``.
    """
    sides = ("left", "right")
    assert _cleaned(_refused_against_more, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]
    assert _cleaned(_sides_held_to_more, "sides", options=sides, collection=True) == [
        "options wider than the Literal ('top',)"
    ]
    assert _cleaned(_keys_held_to_more, "levels", options=sides, collection=True) == [
        "options wider than the Literal ('top',)"
    ]
    assert _cleaned(_refused_before_the_fold, "mode", options=_PACES) == []
    assert (
        _cleaned(_keys_checked_as_a_whole, "levels", options=sides, collection=True)
        == []
    )


#: The options of two kinds of record, one row each, as a shared helper picks
#: the row of the record it is handed.
_ROWS_BY_KIND = {"pace": ("fast", "slow"), "gait": ("walk", "run")}

#: The same table, with a row for the pace that also takes a spelling of its own.
_WIDER_ROWS = {"pace": ("fast", "slow", "quick"), "gait": ("walk", "run")}


def _refused_against_a_picked_row(mode: _Pace, kind: str) -> str:
    paces = _ROWS_BY_KIND[kind]
    if mode not in paces:
        raise ValueError(mode)
    return mode.lower()


def _refused_against_a_wider_row(mode: _Pace, kind: str) -> str:
    if mode not in _WIDER_ROWS[kind]:
        raise ValueError(mode)
    return mode.lower()


def test_a_check_against_a_row_picked_at_run_time_is_held_to_the_closest_row() -> None:
    """``_ROWS_BY_KIND[kind]`` is one row of the table, and the row of the
    ``Literal``'s own options takes nothing more; a table none of whose rows
    is the ``Literal``'s alone lets through what the closest row adds.
    """
    assert _cleaned(_refused_against_a_picked_row, "mode", options=_PACES) == []
    assert _cleaned(_refused_against_a_wider_row, "mode", options=_PACES) == [
        "options wider than the Literal ('quick',)"
    ]


def test_an_escape_in_a_literal_option_is_the_character_it_spells() -> None:
    """An escape written in a ``Literal`` option is the character it spells,
    a tab and not a backslash and a ``t``, so ``write_catalogue``'s tab
    delimiter is one of the options its check holds it to.
    """
    assert ccl._literal_options('Literal[",", ";", "\\t"]') == {",", ";", "\t"}


class _PrivateBase:
    """A base the package would not export, with a public method."""

    def paced(self, mode: _Pace) -> bool:
        return mode.upper() == "FAST"


class _Exported(_PrivateBase):
    """A class that inherits ``paced`` and defines nothing of its own."""


class _Overriding(_PrivateBase):
    """A class that defines ``paced`` again, so it inherits nothing."""

    def paced(self, mode: _Pace) -> bool:
        return require_choice(mode, "mode", _PACES) == "fast"


def test_a_public_method_inherited_from_a_private_base_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``paced`` is a public method of ``_Exported``, defined on its base:
    it is read, under the base, and its clean-up fails; a method the class
    defines again is its own.
    """
    monkeypatch.setattr(_PrivateBase, "__module__", "phonometry.synthetic")
    inherited = list(ccl._inherited_methods(_Exported))
    overridden = list(ccl._inherited_methods(_Overriding))
    assert inherited == [(_PrivateBase, "paced", _PrivateBase.paced)]
    assert overridden == []
    assert _cleaned(_PrivateBase.paced, "mode", options=_PACES) == [".upper()"]


def test_a_method_the_package_inherits_from_a_private_base_is_read_once() -> None:
    """``plot`` of the six layers of ``materials.absorbers.layered`` is
    defined on ``_DrawableLayer``: the walk reads it once, under that base.
    """
    plots = [
        (home, qualname)
        for home, qualname, _ in ccl._targets()
        if qualname.endswith("_DrawableLayer.plot")
    ]
    assert plots == [("phonometry.materials.absorbers.layered", "_DrawableLayer.plot")]


def _never_checked(mode: _Pace) -> bool:
    return mode == "fast"


def _checked_with_not_in(mode: _Pace) -> _Pace:
    if mode not in _PACES:
        raise ValueError(mode)
    return mode


def _checked_beside_another(mode: _Pace, *, strict: bool) -> _Pace:
    if strict:
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_behind_its_own_test(mode: _Pace | None) -> _Pace | None:
    if mode is not None:
        require_choice(mode, "mode", _PACES)
    return mode


def _verdict_of(
    function: Callable[..., object],
    name: str,
    *,
    collection: bool = False,
    options: Iterable[str] = (),
) -> str | None:
    return ccl._verdict(
        ccl._checks_of(
            function,
            name,
            field=False,
            collection=collection,
            depth=0,
            options=frozenset(options),
        )
    )


def test_a_choice_is_checked_by_a_shared_validator_on_every_path() -> None:
    """``require_choice`` where the function starts passes; a check only
    beside another argument, a ``not in`` that refuses a number with
    ``ValueError`` and no check at all each fail with their own verdict.
    """
    assert _verdict_of(_validated, "mode") is None
    assert _verdict_of(_checked_behind_its_own_test, "mode") is None
    assert _verdict_of(_checked_beside_another, "mode") == (
        "checked on some paths only, so a misspelling passes on the others"
    )
    assert _verdict_of(_checked_with_not_in, "mode") == (
        "checked with ``not in``, so a value that is not a text is refused "
        "with ValueError instead of TypeError"
    )
    assert _verdict_of(_never_checked, "mode") == (
        "never checked, so a misspelling passes"
    )


def _checked_after_an_early_return(mode: _Pace, *, quick: bool) -> _Pace:
    if quick:
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _column_of(mode: _Pace, *, quick: bool) -> int:
    if quick:
        return 0
    require_choice(mode, "mode", _PACES)
    return 1


def _checked_after_a_helper_returns_early(mode: _Pace, *, quick: bool) -> int:
    return _column_of(mode, quick=quick)


def _checked_after_its_own_early_return(mode: _Pace | None) -> _Pace | None:
    if mode is None:
        return None
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_before_an_early_return(mode: _Pace, *, quick: bool) -> _Pace:
    require_choice(mode, "mode", _PACES)
    if quick:
        return "fast"
    return mode


def _checked_after_a_yield(mode: _Pace) -> typing.Iterator[_Pace]:
    yield "fast"
    yield require_choice(mode, "mode", _PACES)


def _items_skipped_before_the_check(paces: Sequence[_Pace], *, skip: bool) -> None:
    for pace in paces:
        if skip:
            continue
        require_choice(pace, "paces", _PACES)


def _items_checked_after_an_inner_loop(paces: Sequence[_Pace]) -> None:
    for pace in paces:
        for _ in range(2):
            if pace:
                break
        require_choice(pace, "paces", _PACES)


def test_a_return_before_the_check_leaves_a_path_unchecked() -> None:
    """A ``return`` that runs before the check, in the function or in a
    helper the choice is handed to, ends the paths that take it with the
    choice unchecked, and so does a ``continue`` of the loop that checks each
    item; one behind a test of the choice itself, one after the check, a
    ``yield`` and a ``break`` of an inner loop leave none.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    assert _verdict_of(_checked_after_an_early_return, "mode") == some_paths
    assert _verdict_of(_checked_after_a_helper_returns_early, "mode") == some_paths
    assert (
        _verdict_of(_items_skipped_before_the_check, "paces", collection=True)
        == some_paths
    )
    assert _verdict_of(_checked_after_its_own_early_return, "mode") is None
    assert _verdict_of(_checked_before_an_early_return, "mode") is None
    assert _verdict_of(_checked_after_a_yield, "mode") is None
    assert (
        _verdict_of(_items_checked_after_an_inner_loop, "paces", collection=True)
        is None
    )


def _checked_behind_a_test_of_its_text(mode: str) -> str:
    if mode == "fast":
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_behind_a_test_of_its_form_and_more(
    mode: _Pace | None, *, strict: bool
) -> _Pace | None:
    if strict and mode is not None:
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_misspelling_returns(mode: str) -> str:
    if mode == "typo":
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_an_empty_text_returns(mode: str) -> str:
    if not mode:
        return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_text_matched_returns(mode: str) -> str:
    match mode:
        case "typo":
            return "fast"
    require_choice(mode, "mode", _PACES)
    return mode


def _checked_after_a_listed_option_returns(mode: _Pace) -> int:
    if mode == "fast":
        return 0
    require_choice(mode, "mode", ("slow",))
    return 1


def _checked_but_for_a_listed_option(mode: _Pace) -> _Pace:
    if mode != "fast":
        require_choice(mode, "mode", _PACES)
    return mode


def _checked_in_the_else_of_a_listed_option(mode: _Pace) -> int:
    if mode == "fast":
        column = 0
    else:
        column = 1
        require_choice(mode, "mode", _PACES)
    return column


def _checked_after_listed_options_return(mode: _Pace) -> int:
    if mode in ("fast", "slow"):
        return 0
    require_choice(mode, "mode", _PACES)
    return 1


def _checked_after_none_is_matched(mode: _Pace | None) -> _Pace | None:
    match mode:
        case None:
            return None
    require_choice(mode, "mode", _PACES)
    return mode


def _items_checked_after_an_empty_collection_returns(paces: Sequence[_Pace]) -> None:
    if not paces:
        return
    for pace in paces:
        require_choice(pace, "paces", _PACES)


def test_only_a_test_of_its_form_or_of_a_listed_option_keeps_every_path() -> None:
    """A check behind a test of the text, or one a misspelling can return
    before, leaves a misspelling unchecked on the other path: ``if mode ==
    "fast": require_choice(...)``, ``if mode == "typo": return``, ``if not
    mode: return`` (an empty text is not an option), ``case "typo": return``
    and ``if strict and mode is not None`` (a test that asks something
    besides the form). A test of the form (``is None``, the emptiness of a
    collection, ``case None``) keeps every path, and so does one that skips
    the check only for an option the ``Literal`` lists (``if method ==
    "vdi2081": return ...``), in either branch.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    paces = frozenset(_PACES)
    for leaky in (
        _checked_behind_a_test_of_its_text,
        _checked_behind_a_test_of_its_form_and_more,
        _checked_after_a_misspelling_returns,
        _checked_after_an_empty_text_returns,
        _checked_after_a_text_matched_returns,
    ):
        assert _verdict_of(leaky, "mode", options=paces) == some_paths, leaky
    for tight in (
        _checked_after_a_listed_option_returns,
        _checked_but_for_a_listed_option,
        _checked_in_the_else_of_a_listed_option,
        _checked_after_listed_options_return,
        _checked_after_none_is_matched,
    ):
        assert _verdict_of(tight, "mode", options=paces) is None, tight
    assert (
        _verdict_of(
            _items_checked_after_an_empty_collection_returns,
            "paces",
            collection=True,
            options=paces,
        )
        is None
    )
    # An option is known only from the Literal: without it, the return
    # before the check is a path a misspelling could take.
    assert _verdict_of(_checked_after_a_listed_option_returns, "mode") == some_paths


def _rows_once_each(paces: Sequence[_Pace]) -> tuple[_Pace, ...]:
    rows = tuple(dict.fromkeys(paces))
    for row in rows:
        require_choice(row, "paces", _PACES)
    return rows


def _one_or_several_paces(paces: _Pace | Sequence[_Pace]) -> list[_Pace]:
    chosen = (paces,) if isinstance(paces, str) else tuple(paces)
    return [require_choice(pace, "paces", _PACES) for pace in chosen]


def _keys_of_a_copy(levels: Mapping[_Pace, float]) -> None:
    given: Mapping[_Pace, float] = dict(levels.items())
    for key in given:
        require_choice(key, "levels", _PACES)


def _a_copy_left_unchecked(levels: Mapping[_Pace, float]) -> None:
    given = dict(levels.items())
    if not given:
        raise ValueError(levels)


def test_a_check_of_a_copy_of_the_items_is_a_check_of_the_items() -> None:
    """``tuple(dict.fromkeys(x))``, ``(x,) if isinstance(x, str) else
    tuple(x)`` and ``dict(x.items())`` hold the caller's items, so a check
    of each item of the copy checks each item of the choice; a copy nobody
    checks leaves the choice unchecked.
    """
    assert _verdict_of(_rows_once_each, "paces", collection=True) is None
    assert _verdict_of(_one_or_several_paces, "paces", collection=True) is None
    assert _verdict_of(_keys_of_a_copy, "levels", collection=True) is None
    assert _verdict_of(_a_copy_left_unchecked, "levels", collection=True) == (
        "never checked, so a misspelling passes"
    )


@dataclass(frozen=True)
class _Strides:
    """A record that checks each of its choices when it is built."""

    paces: tuple[_Pace, ...]

    def __post_init__(self) -> None:
        for pace in self.paces:
            require_choice(pace, "paces", _PACES)

    @classmethod
    def of(cls, paces: Sequence[_Pace]) -> _Strides:
        return cls(paces=tuple(paces))


def test_a_choice_handed_to_the_record_a_classmethod_builds_is_checked_there() -> None:
    """``cls(paces=tuple(paces))`` is followed into the record's
    ``__post_init__``, where each item is checked.
    """
    assert _verdict_of(_Strides.of, "paces", collection=True) is None


@dataclass(frozen=True)
class _CheckedPaceLimits:
    """A record that checks each key of its limits when it is built."""

    limits: Mapping[_Pace, float]

    def __post_init__(self) -> None:
        for pace in self.limits:
            require_choice(pace, "limits", _PACES)


@dataclass(frozen=True)
class _UncheckedPaceLimits:
    """A record that keeps its limits as they come."""

    limits: Mapping[_Pace, float]


def _limits_rebuilt(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items()}
    )


def _limits_rebuilt_unchecked(limits: Mapping[_Pace, float]) -> _UncheckedPaceLimits:
    return _UncheckedPaceLimits(
        limits={pace: abs(value) for pace, value in limits.items()}
    )


def test_a_dict_comprehension_that_keeps_the_keys_hands_them_on() -> None:
    """``{pace: float(value) for pace, value in limits.items()}`` gives each
    key a new value and keeps the key, so the record that checks its keys
    checks the caller's; a record that checks nothing leaves them unchecked.
    """
    assert _verdict_of(_limits_rebuilt, "limits", collection=True) is None
    assert _verdict_of(_limits_rebuilt_unchecked, "limits", collection=True) == (
        "never checked, so a misspelling passes"
    )


def _limits_kept_if_listed(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if pace in _PACES}
    )


def _limits_kept_if_set(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if value}
    )


def _limits_kept_if_set_then_checked(limits: Mapping[_Pace, float]) -> None:
    kept = {pace: value for pace, value in limits.items() if value}
    for key in kept:
        require_choice(key, "limits", _PACES)


def _limits_kept_but_one_option(limits: Mapping[_Pace, float]) -> _CheckedPaceLimits:
    return _CheckedPaceLimits(
        limits={pace: float(value) for pace, value in limits.items() if pace != "fast"}
    )


def test_a_dict_comprehension_that_drops_keys_hands_on_only_the_kept_ones() -> None:
    """A filter drops the keys it fails for before any check sees them, so a
    misspelling the filter drops passes unchecked, handed on or held in a
    local: ``if pace in _PACES`` drops it silently and ``if value`` drops any
    key whose value is zero. A filter that drops only an option the
    ``Literal`` lists (``if pace != "fast"``) drops no misspelling.
    """
    never = "never checked, so a misspelling passes"
    assert _verdict_of(_limits_kept_if_listed, "limits", collection=True) == never
    assert _verdict_of(_limits_kept_if_set, "limits", collection=True) == never
    assert (
        _verdict_of(_limits_kept_if_set_then_checked, "limits", collection=True)
        == never
    )
    assert (
        _verdict_of(
            _limits_kept_but_one_option, "limits", collection=True, options=_PACES
        )
        is None
    )


def _paces_checked_in_a_comprehension(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces]


def _paces_checked_where_a_filter_holds(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces if pace]


def _paces_checked_but_one_option(paces: Sequence[_Pace]) -> list[_Pace]:
    return [require_choice(pace, "paces", _PACES) for pace in paces if pace != "fast"]


def _pace_checked_per_step(pace: _Pace, steps: int) -> list[_Pace]:
    return [require_choice(pace, "pace", _PACES) for _ in range(steps)]


def test_a_check_in_a_comprehension_runs_only_where_its_clauses_let_it() -> None:
    """A check in the element of a comprehension runs once for each item its
    filters keep, so a filter that drops a text the ``Literal`` does not list
    (``if pace`` drops ``""``) leaves it unchecked, as a ``continue`` would; a
    comprehension over something else than the choice runs it only when that
    holds an item, as a ``for`` loop does. A comprehension over the choice
    itself, and a filter that drops only a listed option, leave none.
    """
    some_paths = "checked on some paths only, so a misspelling passes on the others"
    assert (
        _verdict_of(_paces_checked_in_a_comprehension, "paces", collection=True) is None
    )
    assert (
        _verdict_of(
            _paces_checked_where_a_filter_holds,
            "paces",
            collection=True,
            options=_PACES,
        )
        == some_paths
    )
    assert (
        _verdict_of(
            _paces_checked_but_one_option, "paces", collection=True, options=_PACES
        )
        is None
    )
    assert _verdict_of(_pace_checked_per_step, "pace") == some_paths


_TERMINATIONS = (
    "Literal['fast', 'slow'] | Mapping[Literal['left', 'right'], "
    "Literal['fast', 'slow'] | float]"
)
_TWO_SIDES = ("left", "right")


@dataclass(frozen=True)
class _Terminations:
    """A record that checks a single pace, each side and each pace it maps to."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _KeysUnchecked:
    """A record that checks its single pace and the paces it maps to, not the sides."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for value in self.sides.values():
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _ValuesUnchecked:
    """A record that checks its single pace and its sides, not the paces they map to."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side in self.sides:
                require_choice(side, "sides", _TWO_SIDES)
        else:
            require_choice(self.sides, "sides", _PACES)


@dataclass(frozen=True)
class _SingleUnchecked:
    """A record that checks every side and pace of a mapping, and no single pace."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)


@dataclass(frozen=True)
class _KeysSkipAPace:
    """A record that skips a key spelt as a pace before it checks the sides."""

    sides: _Pace | Mapping[_Side, _Pace | float]

    def __post_init__(self) -> None:
        if isinstance(self.sides, Mapping):
            for side, value in self.sides.items():
                if side in {"fast", "slow"}:
                    continue
                require_choice(side, "sides", _TWO_SIDES)
                if isinstance(value, str):
                    require_choice(value, "sides", _PACES)
        else:
            require_choice(self.sides, "sides", _PACES)


def test_every_part_of_a_choice_of_several_parts_is_checked() -> None:
    """``Pace | Mapping[Side, Pace | float]`` takes a pace as one value, a side
    as each key and a pace as each value: a check of one part says nothing of
    the others, so a record passes only when each part reaches a check, the
    single name, the keys and the values each on every path. Each part is
    read against the options of its own ``Literal``: a key skipped because it
    is spelt as a pace is a misspelt side, not an option of the keys.
    """
    paces, sides = frozenset(_PACES), frozenset(_TWO_SIDES)
    assert ccl._branches(_TERMINATIONS) == {
        ccl._WHOLE: paces,
        ccl._ITEMS: sides,
        ccl._VALUES: paces,
    }
    assert ccl._branches("Literal['fast', 'slow'] | float") == {ccl._WHOLE: paces}

    def verdict(record: type) -> str | None:
        check = ccl._post_init(record)
        assert check is not None
        return ccl._part_verdict(check, "sides", _TERMINATIONS, field=True)

    assert verdict(_Terminations) is None
    assert verdict(_KeysUnchecked) == (
        "each item or key: never checked, so a misspelling passes"
    )
    assert verdict(_ValuesUnchecked) == (
        "each value: never checked, so a misspelling passes"
    )
    assert verdict(_SingleUnchecked) == (
        "the choice itself: never checked, so a misspelling passes"
    )
    skipped = verdict(_KeysSkipAPace)
    assert skipped is not None
    assert skipped.startswith("each item or key: ")
    # The rule before parts: one check anywhere was enough for all three.
    for record in (_KeysUnchecked, _ValuesUnchecked, _SingleUnchecked):
        check = ccl._post_init(record)
        assert check is not None
        assert (
            ccl._verdict(
                ccl._checks_of(check, "sides", field=True, collection=True, depth=0)
            )
            is None
        )


def _one_pace_read_by_letter(paces: _Pace | Sequence[_Pace]) -> tuple[_Pace, ...]:
    given = paces if isinstance(paces, str) else paces
    return tuple(require_choice(pace, "paces", _PACES) for pace in given)


def test_a_single_choice_wrapped_as_one_item_is_checked_with_the_items() -> None:
    """``(paces,) if isinstance(paces, str) else paces`` holds a single pace as
    the one item the loop checks; read letter by letter it is not checked as
    the pace it is.
    """
    annotation = "Literal['fast', 'slow'] | Sequence[Literal['fast', 'slow']]"
    assert (
        ccl._part_verdict(_one_or_several_paces, "paces", annotation, field=False)
        is None
    )
    assert (
        ccl._part_verdict(_one_pace_read_by_letter, "paces", annotation, field=False)
        == "the choice itself: never checked, so a misspelling passes"
    )


def test_a_stale_unchecked_entry_fails_and_a_needed_one_does_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An entry of ``UNCHECKED`` the walk still finds is kept; one it no
    longer finds is stale. The walk hands back every unchecked choice, the
    exempt ones too, so a needed entry is never mistaken for a stale one.
    """
    needed = ("phonometry.synthetic", "_never_checked", "mode")
    gone = ("phonometry.nowhere", "gone", "mode")
    monkeypatch.setitem(ccl.UNCHECKED, needed, "a reason that still applies")
    monkeypatch.setitem(ccl.UNCHECKED, gone, "a reason that no longer applies")
    walk = [ccl.Choice(*needed, "_Pace", ("never checked",))]
    stale = ccl._stale_unchecked(walk)
    assert needed not in stale
    assert gone in stale


def test_every_literal_choice_is_checked_on_every_path() -> None:
    """The package passes: every public ``Literal`` choice and every one a
    record a caller builds holds reaches a shared validator on every path,
    and no entry of ``UNCHECKED`` is stale (rule A45).
    """
    every = list(ccl.unchecked_choices())
    assert [
        choice
        for choice in every
        if (choice.module, choice.qualname, choice.name) not in ccl.UNCHECKED
    ] == []
    assert ccl._stale_unchecked(every) == []


#: A table of this module keyed by the options of ``_Pace`` but typed ``str``.
_PACE_LIMITS_TEXT: dict[str, float] = {"fast": 0.125, "slow": 1.0}
#: The same table keyed by the vocabulary.
_PACE_LIMITS: dict[_Pace, float] = {"fast": 0.125, "slow": 1.0}


def test_a_table_keyed_by_any_text_whose_keys_are_a_vocabulary_is_found() -> None:
    """A ``dict[str, ...]`` whose keys are the options of a ``Literal`` of its
    module is the vocabulary written twice; keyed by the ``Literal`` it is not.
    """
    text = list(
        ccl._keyed_by_text(
            _PACE_LIMITS_TEXT,
            ccl._annotation_node("dict[str, float]"),
            __name__,
            "",
            0,
        )
    )
    typed = list(
        ccl._keyed_by_text(
            _PACE_LIMITS,
            ccl._annotation_node("dict[_Pace, float]"),
            __name__,
            "",
            0,
        )
    )
    assert text == [("", frozenset({"fast", "slow"}))]
    assert typed == []


#: A table annotation spelled through an alias of this module.
_PaceTable = dict[str, float]


@dataclass(frozen=True)
class _PaceLimits:
    """A published record whose table field is keyed by any text."""

    limits: dict[str, float]


def _found(value: object, annotation: str | None) -> list[tuple[str, frozenset[str]]]:
    return list(
        ccl._keyed_by_text(
            value, ccl._annotation_node(annotation, __name__), __name__, "", 0
        )
    )


def test_a_table_is_read_through_its_alias_and_its_qualifier() -> None:
    """An alias of the module, ``Final`` around the type and a ``Sequence``
    of texts let any text in as surely as ``dict[str, ...]`` written out.
    """
    paces = frozenset({"fast", "slow"})
    assert _found(_PACE_LIMITS_TEXT, "_PaceTable") == [("", paces)]
    assert _found(_PACE_LIMITS_TEXT, "Final[dict[str, float]]") == [("", paces)]
    assert _found(_PACE_LIMITS, "Final[dict[_Pace, float]]") == []
    assert _found(_PACES, "Sequence[str]") == [("", paces)]
    assert _found(_PACES, "Final[tuple[str, ...]]") == [("", paces)]
    assert _found(_PACES, "Sequence[_Pace]") == []
    # An annotation that says nothing of the keys lets any text in.
    assert _found(_PACE_LIMITS_TEXT, "Any") == [("", paces)]


def test_each_part_of_a_tuple_key_and_each_field_of_a_record_is_read() -> None:
    """The parts of a key ``("fast", "dry")`` are a vocabulary each, and a
    published record's table fields are read through the record's own
    annotations.
    """
    table = {("fast", "dry"): 1.0, ("slow", "wet"): 2.0}
    assert _found(table, "dict[tuple[str, str], float]") == [
        ("[key]<0>", frozenset({"fast", "slow"})),
        ("[key]<1>", frozenset({"dry", "wet"})),
    ]
    assert _found(table, "dict[tuple[_Pace, str], float]") == [
        ("[key]<1>", frozenset({"dry", "wet"}))
    ]
    assert _found(_PaceLimits(limits=dict(_PACE_LIMITS_TEXT)), None) == [
        (".limits", frozenset({"fast", "slow"}))
    ]


def _pace_of(*, quick: bool) -> _Pace:
    return "fast" if quick else "slow"


def _pace_and_count(*, quick: bool) -> tuple[_Pace, int]:
    return _pace_of(quick=quick), 1


def _text_of(*, quick: bool) -> str:
    return "fast" if quick else "any text"


@dataclass(frozen=True)
class _Stride:
    """A record whose field is typed with the vocabulary."""

    pace: _Pace


def _filled_from_returns(*, quick: bool) -> tuple[object, ...]:
    def _stride() -> _Stride:
        return _Stride(pace=_pace_of(quick=quick))

    unpacked, _count = _pace_and_count(quick=quick)
    stride = _stride()
    return (_pace_of(quick=quick), unpacked, stride.pace, _text_of(quick=quick))


def test_a_value_handed_back_by_a_function_typed_with_a_literal_is_closed() -> None:
    """Guard (c) reads what fills a record field back to where it is written:
    a call to a function annotated to return a ``Literal``, an item unpacked
    from a ``tuple[...]`` such a helper returns, and a field of the record a
    nested function returns are the vocabulary; a function annotated ``str``
    hands back any text.
    """
    tree = _tree(_filled_from_returns)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_filled_from_returns"
    )
    returned = next(
        node.value for node in ast.walk(function) if isinstance(node, ast.Return)
    )
    assert isinstance(returned, ast.Tuple)
    sources = [ccl._source(item, function, __name__, 0) for item in returned.elts]
    paces = frozenset({"fast", "slow"})
    assert sources[:3] == [ccl._Source("literal", paces)] * 3
    assert sources[3] == ccl._OPEN_SOURCE


def test_a_stale_open_table_entry_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exemption for a table the walk no longer flags cannot outlive its reason."""
    key = ("phonometry.nowhere", "GONE")
    monkeypatch.setitem(ccl.OPEN_TABLES, key, "a reason that no longer applies")
    needed = ("phonometry.synthetic", "TABLE")
    monkeypatch.setitem(ccl.OPEN_TABLES, needed, "a reason that still applies")
    walk = [ccl.Choice(*needed, "keys", "dict[str, float]", ("its keys",))]
    stale = ccl._stale_tables(walk)
    assert key in stale
    assert needed not in stale


def test_every_published_table_of_a_vocabulary_is_keyed_by_it() -> None:
    """The package passes: no published table keyed by any text holds the
    options of a vocabulary, and no entry of ``OPEN_TABLES`` is stale (rule A21).
    """
    tables = list(ccl.vocabulary_tables())
    assert [
        table
        for table in tables
        if (table.module, table.qualname) not in ccl.OPEN_TABLES
    ] == []
    assert ccl._stale_tables(tables) == []
