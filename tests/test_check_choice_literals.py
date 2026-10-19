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
from typing import TYPE_CHECKING

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_choice_literals as ccl

from phonometry._internal.validation import require_choice
from phonometry.filters.weighting import time_weighting

if TYPE_CHECKING:
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
    from phonometry.building.measurement import survey_insulation, uncertainty
    from phonometry.building.prediction import panel_transmission
    from phonometry.environment.sources import cnossos_rail, cnossos_road
    from phonometry.materials.absorbers import porous, suspended_ceilings
    from phonometry.noise_control import enclosure_insulation
    from phonometry.underwater.bioacoustics import audiograms
    from phonometry.underwater.bioacoustics import weighting as hearing
    from phonometry.underwater.sources import ship_traffic_noise
    from phonometry.vibration.human import exposure, signal_burst
    from phonometry.vibration.immission import coupling, train_categories

    rooms = {key for row in survey_insulation._TABLE3.values() for key in row}
    groups = {key for table in hearing._PARAMETERS.values() for key in table}
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
