#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The spelling gate: identifiers, and the values a caller types, in American English.

``scripts/check_identifier_spelling.py`` walks the installed package, so its
own run only says the tree is clean today. These tests fix what it must
catch and what it must leave alone. A name is read word by word, so
``AcousticCentre`` is caught and ``SlitResonator`` is not a ``litre``; the
nouns ``analysis`` and ``organism`` are not the verbs ``analyse`` and
``organise``; ``catalogue`` is the one British form the library keeps. The
walk reaches a function's parameter, a ``Literal`` choice, a default, an enum
value and a key of a published table, each shown here by putting a British
form back; and an exemption that outlives the value it excuses is reported,
because it would excuse the next one to take the spelling.
"""

from __future__ import annotations

import enum
import inspect
import pathlib
import sys
import types
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_identifier_spelling as spelling
import check_parameter_units as walk

import phonometry.environment
import phonometry.signals

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.mark.parametrize(
    ("name", "words"),
    [
        ("AcousticCentre", ["acoustic", "centre"]),
        ("STORY_FREQUENCY_MIN_STORIES", ["story", "frequency", "min", "stories"]),
        ("EQFilter", ["eq", "filter"]),
        ("thickness1_m", ["thickness", "1", "m"]),
        (
            "optimised brushed down concrete",
            ["optimised", "brushed", "down", "concrete"],
        ),
    ],
)
def test_a_name_breaks_into_its_words(name: str, words: list[str]) -> None:
    assert spelling.words(name) == words


@pytest.mark.parametrize(
    ("name", "british"),
    [
        ("acoustic_centre", "centre"),
        ("AcousticCentre", "centre"),
        ("centred_interval", "centre"),
        ("SIMULATED_PROGRAMME_SPECTRUM", "programme"),
        ("normalised_difference", "normalis"),
        ("FibreResistivityFit", "fibre"),
        ("storeys", "storey"),
        ("water_vapour_mole_fraction", "vapour"),
        ("MODELLING_UNCERTAINTY_DB", "modell"),
        ("behaviour_observation", "behaviour"),
        ("neighbour_difference_db", "neighbour"),
        ("unfavourable_sum", "favour"),
        ("colour_map", "colour"),
        ("urbanisation", "urbanis"),
        ("draught", "draught"),
        ("collected_volume_litres", "litre"),
        ("distance_millimetres", "metre"),
        ("ALUMINIUM", "aluminium"),
        ("OPTIMISED_BRUSHED_DOWN_CONCRETE", "optimis"),
        ("analyse_band", "analys"),
        ("realised_level", "realis"),
        ("organised_by", "organis"),
        ("equaliser_gain", "equaliser"),
        ("tyre_noise", "tyre"),
        ("aeroplane", "aeroplane"),
        ("analogue_output", "analogue"),
        ("centring", "centre"),
        ("cancelled_modes", "cancell"),
        ("channelled_flow", "channell"),
        ("practised", "practis"),
        ("aerofoil_noise", "aerofoil"),
        ("kerbside", "kerb"),
        ("louvre_loss", "louvre"),
        ("insitu_absorption_coefficient", "insitu"),
        ("InsituAbsorptionResult", "insitu"),
    ],
)
def test_a_british_form_is_named(name: str, british: str) -> None:
    assert british in [stem.british for stem in spelling.british_forms(name)]


@pytest.mark.parametrize(
    "name",
    [
        "acoustic_center",
        "center_frequency",
        "story_fundamental_frequency",
        "program_signal",
        "fiber_diameter_um",
        # Words of their own in both spellings.
        "harmonic_analysis",
        "analyses",
        "realistic_room",
        "organism",
        "optimism",
        "programmed_level",
        "programmer",
        # The letters run across two words, or inside another word.
        "SlitResonatorAbsorberResult",
        "polystyrene",
        # The one British form the library keeps.
        "read_catalogue",
        "CatalogueError",
        "catalogues",
        "in_situ_absorption_coefficient",
        "InSituAbsorptionResult",
    ],
)
def test_the_american_spelling_passes(name: str) -> None:
    assert spelling.british_forms(name) == []


@pytest.mark.parametrize(
    ("name", "american"),
    [
        # Any -ise verb, and its -isation, not only the ones a list names.
        ("synthesised_signal", "synthesized"),
        ("harmonised_standard", "harmonized"),
        ("recognised", "recognized"),
        ("vectorise", "vectorize"),
        ("acoustically_neutralised", "neutralized"),
        ("prioritising", "prioritizing"),
        ("visualisation", "visualization"),
        ("criticise", "criticize"),
        # Any -yse verb.
        ("paralysed", "paralyzed"),
        ("catalyser", "catalyzer"),
        # Any -our noun.
        ("honour", "honor"),
        ("honourable", "honorable"),
        ("flavourless", "flavorless"),
        ("armoured", "armored"),
        # Any -tre and -bre noun.
        ("THEATRE", "theater"),
        ("theatres", "theaters"),
        ("spectre_level", "specter"),
        ("lustred", "lustered"),
        ("calibre", "caliber"),
        ("sabres", "sabers"),
    ],
)
def test_a_british_ending_is_caught_in_any_word(name: str, american: str) -> None:
    """A family of words is caught by its ending, and the fix spells the word."""
    assert american in [stem.american for stem in spelling.british_forms(name)]


@pytest.mark.parametrize(
    "name",
    [
        # American words of the -ise shape.
        "noise",
        "denoised",
        "harmonoise",
        "pairwise",
        "rise_time",
        "rising",
        "raised",
        "imprecise",
        "exercise",
        "unsupervised",
        "advertising",
        "uncompromising",
        "improvisation",
        "premises",
        "crises",
        "miser",
        "disable",
        "surmised",
        # The plural of an -is noun is no -ise verb.
        "metropolises",
        "trellises",
        # American words of the -our, -tre and -bre shapes.
        "contour",
        "contoured",
        "hours",
        "pouring",
        "detour",
        "glamour",
        "pompadour",
        "hatred",
        "timbre",
        "inbred",
        # Two l in American English too, and words that only end in the letters.
        "cancellation",
        "initially",
        "totally",
        "signally",
        "string",
        "isentropic",
        "visible",
        "revision",
        "diagrammed",
        "dialogue",
        "greyhound",
    ],
)
def test_an_american_word_of_a_british_shape_passes(name: str) -> None:
    assert spelling.british_forms(name) == []


def test_a_word_a_stem_names_is_not_reported_twice() -> None:
    """``centres`` is the stem ``centre``, not also the ``-tre`` shape."""
    assert [stem.british for stem in spelling.british_forms("centres")] == ["centre"]


def test_the_tree_spells_every_identifier_the_american_way() -> None:
    found, stale = spelling.misspelled()
    assert found == []
    assert stale == []


def _published(
    monkeypatch: pytest.MonkeyPatch, module: object, name: str, obj: object
) -> None:
    """Publish ``obj`` as ``name`` from ``module`` for one test."""
    monkeypatch.setattr(module, name, obj, raising=False)
    monkeypatch.setattr(module, "__all__", [*module.__all__, name])  # type: ignore[attr-defined]


def _reported(
    found: list[tuple[spelling.Finding, list[spelling.Stem]]],
) -> set[tuple[str, str, str]]:
    return {(entry.qualname, entry.name, entry.kind) for entry, _ in found}


def test_a_british_parameter_put_back_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A function that takes ``centre_frequency`` again is caught by its parameter."""

    def band_again(centre_frequency: float) -> float:
        return centre_frequency

    band_again.__module__ = "phonometry.signals"
    _published(monkeypatch, phonometry.signals, "band_again", band_again)
    found, _ = spelling.misspelled()
    assert _reported(found) == {("band_again", "centre_frequency", "name")}


def test_a_british_value_a_caller_types_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Literal choice and a default are values the caller writes, like a name."""

    def period_again(
        model: Literal["storeys", "height"] = "height", location: str = "centre"
    ) -> str:
        return f"{model}{location}"

    period_again.__module__ = "phonometry.signals"
    _published(monkeypatch, phonometry.signals, "period_again", period_again)
    found, _ = spelling.misspelled()
    assert _reported(found) == {
        ("period_again(model)", "storeys", "Literal value"),
        ("period_again(location)", "centre", "default value"),
    }


def test_an_enum_value_and_a_table_key_are_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An enum's member and value, and a key of a published table."""

    class Surface(enum.Enum):
        OPTIMISED = "optimised"

    Surface.__module__ = "phonometry.environment"
    _published(monkeypatch, phonometry.environment, "Surface", Surface)
    table = MappingProxyType({"acoustic_centres": 1.0, "cox-2017/wood_fibre": 2.0})
    _published(monkeypatch, phonometry.environment, "SPELLING_TABLE", table)
    found, _ = spelling.misspelled()
    assert _reported(found) == {
        ("Surface", "OPTIMISED", "name"),
        ("Surface.OPTIMISED", "optimised", "enum value"),
        ("SPELLING_TABLE", "acoustic_centres", "table key"),
    }


def test_a_published_choice_list_and_a_spaced_key_are_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A tuple or frozenset of choices, and a key written as words, are typed
    by the caller like a Literal choice; a catalogue's row key is not.
    """
    _published(monkeypatch, phonometry.environment, "LOCATIONS", ("centre", "edge"))
    _published(
        monkeypatch, phonometry.environment, "SIDES", frozenset({"centre", "edge"})
    )
    table = MappingProxyType(
        {"boundary centre": 1.0, "wall-centre": 2.0, "cox-2017/wood fibre": 3.0}
    )
    _published(monkeypatch, phonometry.environment, "TARGETS", table)
    found, _ = spelling.misspelled()
    assert _reported(found) == {
        ("LOCATIONS", "centre", "constant item"),
        ("SIDES", "centre", "constant item"),
        ("TARGETS", "boundary centre", "table key"),
        ("TARGETS", "wall-centre", "table key"),
    }


def test_a_constant_that_is_not_a_tuple_of_strings_holds_no_items() -> None:
    assert spelling.constant_items((1.0, "centre")) == ()
    assert spelling.constant_items(()) == ()
    assert spelling.constant_items("centre") == ()
    assert spelling.constant_items(frozenset({"b", "a"})) == ("a", "b")


def test_a_module_path_is_held_to_the_spelling(monkeypatch: pytest.MonkeyPatch) -> None:
    """A public module named ``programme_signal`` is reported by its path."""
    stub = types.ModuleType("phonometry.electroacoustics.programme_signal")
    stub.__all__ = []  # type: ignore[attr-defined]

    def modules() -> Iterator[tuple[str, types.ModuleType]]:
        yield stub.__name__, stub

    monkeypatch.setattr(walk, "public_modules", modules)
    found, _ = spelling.misspelled()
    assert _reported(found) == {("", stub.__name__, "module")}


def test_an_exemption_nothing_needs_is_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exemption kept for a value that is gone, and a sanctioned word nobody
    writes, are both reported.
    """
    key = ("phonometry.environment", "Gone.MEMBER", "colour")
    monkeypatch.setitem(spelling.EXEMPT, key, "a reason nobody needs")
    monkeypatch.setitem(spelling.SANCTIONED, "dialogue", "a word nobody writes")
    found, stale = spelling.misspelled()
    assert found == []
    assert stale == [key, "dialogue"]


def test_the_printed_surface_keeps_its_print_and_its_member_does_not() -> None:
    """The CNOSSOS exemption still names the member and the value it excuses."""
    from phonometry.environment.sources import cnossos_road

    key = (
        "phonometry.environment.sources.cnossos_road",
        "RoadSurface.OPTIMIZED_BRUSHED_DOWN_CONCRETE",
        "optimised brushed down concrete",
    )
    assert key in spelling.EXEMPT
    member = cnossos_road.RoadSurface.OPTIMIZED_BRUSHED_DOWN_CONCRETE
    assert member.value == key[2]
    assert spelling.british_forms(member.name) == []


def test_the_walk_reads_a_parameter_of_every_kind() -> None:
    """The slots of a class are its constructor's parameters and its fields."""
    from phonometry.vibration.structural import building_response

    slots = {
        (slot.qualname, slot.name)
        for slot in spelling._slots(
            "fundamental_period", building_response.fundamental_period
        )
    }
    assert ("fundamental_period", "n_stories") in slots
    params = inspect.signature(building_response.fundamental_period).parameters
    namespace = spelling._namespace(building_response.fundamental_period)
    assert "stories" in set(
        spelling.literal_values(params["model"].annotation, namespace)
    )
