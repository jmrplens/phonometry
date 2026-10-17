#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice reads the same everywhere it is offered.

Three choices were spelled differently from one function to the next. The
band set of a spectrum was ``band="third"`` on the panel predictions,
``bands="third-octave"`` on the ISO 717 ratings, ``band_type="third"`` on
the intensity determinations, ``bandwidth="one-third-octave"`` on the
reference sound source and ``band_fraction=3`` on the cabins, while the
filter bank, the room parameters and the intensity measurement already took
``fraction=3``. A sound field was ``"free-field"`` on the hearing threshold,
``"free_field"`` on the microphone calibrations and ``"free"`` on the
loudness models. A flat frequency weighting was ``a_weighted=False``,
``weighted=False``, ``"unweighted"`` or ``None``.

The tests here read the installed package the way a caller meets it, with
every type alias spelled out as its definition: no public choice offers a
band-set word or takes a band set as a ``str``, every public ``field`` states
its options in a ``Literal`` and offers no sound field outside free, diffuse
and pressure, no ``weighting`` offers a flat word, and no table or tuple a
choice is checked against holds one of the retired words. Where a word is
kept on purpose, the exemption names the place and says why. The calls that
refuse the retired spellings at run time are pinned as well, since a static
reading cannot see a value a function accepts inline.
"""

from __future__ import annotations

import dataclasses
import functools
import importlib
import inspect
import pathlib
import pkgutil
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from typing import Any

import pytest
from test_public_vocabulary import _public_modules

import phonometry

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_api_docs as gad  # noqa: E402

#: The words a choice used for a band set before every band set became
#: ``fraction=1`` (octaves) or ``fraction=3`` (one-third octaves).
_BAND_SET_WORDS = frozenset(
    {"third", "thirds", "third-octave", "one-third-octave", "octave", "octaves"}
)

_SII_PROCEDURE = (
    "ANSI S3.5-1997 names its four calculation procedures, and "
    "'one-third-octave' and 'octave' are two of those names: a procedure "
    "with its own band-importance table, not a band set chosen for a spectrum"
)
#: The names a band-set choice has gone by. A choice under one of them that
#: takes a ``str`` can be handed a band-set word, whatever its default.
_BAND_SET_NAMES = frozenset(
    {"band", "bands", "band_type", "band_fraction", "bandwidth", "band_set", "fraction"}
)
_STR = re.compile(r"\bstr\b")
_ISO_3745_SIGNAL = (
    "names the kind of test signal of ISO 3745 Annex A, 'discrete-frequency' "
    "or 'broadband', not a band set"
)
#: Where a band-set word is kept, keyed by location, each with the reason.
_LABEL = "a translation key: the English word the figure prints, not a choice"
_BAND_SET_EXEMPT = {
    "phonometry.emission.free_field_qualification.FreeFieldCheck.bandwidth": (
        _ISO_3745_SIGNAL
    ),
    "phonometry._plot.building._STRINGS": _LABEL,
    "phonometry._plot.speech._SII_METHOD_LABELS": _SII_PROCEDURE,
    "phonometry._report.sii._METHOD_NAMES": _SII_PROCEDURE,
    "phonometry._report.sii._TABLE_CAPTIONS": _SII_PROCEDURE,
    "phonometry.speech.sii._PROCEDURES": _SII_PROCEDURE,
    "phonometry.speech.sii.SII_METHODS": _SII_PROCEDURE,
    "phonometry.speech.sii.SIIProcedure.method": _SII_PROCEDURE,
    "phonometry.speech.sii.SIIResult.method": _SII_PROCEDURE,
    "phonometry.speech.sii.sii_procedure(method)": _SII_PROCEDURE,
    "phonometry.speech.sii.speech_intelligibility_index(method)": _SII_PROCEDURE,
}

#: The sound fields a public ``field`` may name.
_SOUND_FIELDS = frozenset({"free", "diffuse", "pressure"})
_EARDRUM = (
    "the Moore-Glasberg models take a spectrum already at the eardrum, with "
    "no outer-ear transfer applied: a point of presentation, not a sound field"
)
_CATALOGUE_COLUMN = (
    "names the catalogue column an issue was found in, not a sound field"
)
_NORMAL_INCIDENCE = (
    "Hopkins (2007) Eq. 4.99 sets m by the incident sound field, m = 8 for a "
    "diffuse field or m = 4 for a plane wave at normal incidence (PDF page 522, "
    "printed page 495): 'normal' names that plane wave, which has no "
    "free/diffuse/pressure word"
)
_QUASI_FREE = (
    "ISO 8253-2:2009 5.4 names the quasi-free sound field, a field of its own "
    "with its own tolerances beside the free field of 5.2"
)
_RECORD_FIELD = "names the record field a rate is read from, for a message"
_SIMULATION_FIELD = (
    "names a field quantity of the simulation grid, the pressure 'p' or a "
    "particle velocity 'vx' or 'vy', not a sound field"
)
#: Where a ``field`` offers another value, keyed by location, with the reason.
_FIELD_EXEMPT = {
    "phonometry.psychoacoustics.loudness.moore_glasberg._FIELDS": _EARDRUM,
    "phonometry.psychoacoustics.loudness.moore_glasberg.MooreGlasbergLoudness.field": (
        _EARDRUM
    ),
    "phonometry.psychoacoustics.loudness.moore_glasberg_time."
    "MooreGlasbergTimeVaryingLoudness.field": _EARDRUM,
    "phonometry.building.prediction.aperture_transmission._FIELD_M": (
        _NORMAL_INCIDENCE
    ),
    "phonometry.building.prediction.aperture_transmission."
    "slit_transmission_coefficient(field)": _NORMAL_INCIDENCE,
    "phonometry.hearing.sound_field_audiometry.FreeSoundFieldCheck.field": (
        _QUASI_FREE
    ),
    "phonometry.io._resolve.require_signal_rate(field)": _RECORD_FIELD,
    "phonometry.simulation.elastic_fdtd.ElasticFDTD2D.collocated(field)": (
        _SIMULATION_FIELD
    ),
    "phonometry._internal.catalogue.CatalogueError.__init__(field)": _CATALOGUE_COLUMN,
    "phonometry._internal.catalogue.CatalogueIssue.field": _CATALOGUE_COLUMN,
    "phonometry.psychoacoustics.loudness.moore_glasberg.loudness_moore_glasberg(field)": (
        _EARDRUM
    ),
    "phonometry.psychoacoustics.loudness.moore_glasberg."
    "loudness_moore_glasberg_from_spectrum(field)": _EARDRUM,
    "phonometry.psychoacoustics.loudness.moore_glasberg."
    "loudness_moore_glasberg_from_third_octave(field)": _EARDRUM,
    "phonometry.psychoacoustics.loudness.moore_glasberg_time."
    "loudness_moore_glasberg_time(field)": _EARDRUM,
}

#: A sound field as any module has written it, old spellings included: a
#: tuple or table named for a field that holds one of these is a list of
#: sound fields, and holds nothing else.
_SOUND_FIELD_WORDS = _SOUND_FIELDS | {
    "free-field",
    "free_field",
    "diffuse-field",
    "diffuse_field",
}

#: The words a weighting used for none at all before every flat weighting
#: became ``"Z"``.
_FLAT_WORDS = frozenset({"unweighted", "flat", "linear", "lin", "none", "Lin"})
_GCC = (
    "names the weighting of a generalized cross-correlation (Knapp and "
    "Carter), not a frequency weighting: 'none' is the plain correlation"
)
#: Where a ``weighting`` keeps another word, keyed by location, with the reason.
_WEIGHTING_EXEMPT = {
    "phonometry.signals._correlation.time_delay(weighting)": _GCC,
    "phonometry.signals._correlation.TimeDelayResult.weighting": _GCC,
    "phonometry._plot.vibration._STRINGS": _LABEL,
}

#: The names a weighting choice went by before every one became ``weighting``.
_WEIGHTING_FLAGS = frozenset(
    {"a_weighted", "weighted", "curve", "c_weighted", "unweighted", "flat"}
)
#: An annotation that makes a parameter or field a choice rather than values.
_CHOICE_TYPE = re.compile(r"\b(bool|str)\b|Literal\[")
_TABLE_ROW = (
    "reads the A-weighted (or A/C) single-number row of a printed table "
    "instead of its band rows: a row of the table, not a choice of curve"
)
#: Where a weighting flag keeps its name, keyed by location, with the reason.
_WEIGHTING_FLAG_EXEMPT = {
    "phonometry.emission._sound_power_intensity_points.error_factor(a_weighted)": (
        _TABLE_ROW
    ),
    "phonometry.building.measurement.survey_insulation."
    "estimate_reverberation_index(weighted)": _TABLE_ROW,
}

_LITERAL = re.compile(r"Literal\[([^\[\]]*)\]")
_QUOTED = re.compile(r"""'([^']*)'|"([^"]*)\"""")


@dataclasses.dataclass(frozen=True)
class _Choice:
    """One public parameter or field, as a caller meets it."""

    where: str
    name: str
    #: The annotation with every unpublished alias spelled out.
    annotation: str
    #: The default, or ``inspect.Parameter.empty``.
    default: Any


def _literal_values(annotation: str) -> set[str]:
    """Every string a ``Literal[...]`` in *annotation* offers."""
    values: set[str] = set()
    for body in _LITERAL.findall(annotation):
        for single, double in _QUOTED.findall(body):
            values.add(single or double)
    return values


def _expanded(annotation: object, module: str) -> str:
    text = annotation if isinstance(annotation, str) else str(annotation)
    return gad.expand_unpublished_aliases(text, module)


def _signature_choices(
    where: str, func: Callable[..., object], module: str
) -> Iterator[_Choice]:
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):  # pragma: no cover - builtins
        return
    for parameter in signature.parameters.values():
        if parameter.name in {"self", "cls"}:
            continue
        yield _Choice(
            f"{where}({parameter.name})",
            parameter.name,
            _expanded(parameter.annotation, module),
            parameter.default,
        )


def _class_choices(where: str, cls: type, module: str) -> Iterator[_Choice]:
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            default = (
                field.default
                if field.default is not dataclasses.MISSING
                else inspect.Parameter.empty
            )
            yield _Choice(
                f"{where}.{field.name}",
                field.name,
                _expanded(field.type, module),
                default,
            )
    elif "__init__" in vars(cls):
        yield from _signature_choices(
            f"{where}.__init__", vars(cls)["__init__"], module
        )
    for name, member in vars(cls).items():
        if name.startswith("_"):
            continue
        if isinstance(member, staticmethod | classmethod):
            yield from _signature_choices(f"{where}.{name}", member.__func__, module)
        elif inspect.isfunction(member):
            yield from _signature_choices(f"{where}.{name}", member, module)


@functools.cache
def _choices() -> tuple[_Choice, ...]:
    """Every public parameter and field, with its aliases spelled out."""
    return tuple(_walk_choices())


def _walk_choices() -> Iterator[_Choice]:
    seen: set[str] = set()
    for module in _public_modules():
        for attr, obj in vars(module).items():
            if attr.startswith("_"):
                continue
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("phonometry"):
                continue
            key = f"{owner}.{getattr(obj, '__qualname__', attr)}"
            if key in seen:
                continue
            seen.add(key)
            if inspect.isfunction(obj):
                yield from _signature_choices(key, obj, owner)
            elif inspect.isclass(obj):
                yield from _class_choices(key, obj, owner)


@functools.cache
def _module_values() -> tuple[tuple[str, object], ...]:
    """``(where, value)`` of every module-level tuple and mapping, once each.

    Private modules and private names included: a choice is checked against
    the tuple ``require_choice`` reads it from and looked up in the table
    keyed by it, so those are where a band-set word or a stray field name
    survives longest. A value re-exported by a package is keyed by the
    deepest module that holds it, the one that writes it.
    """
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        importlib.import_module(info.name)
    places: dict[int, tuple[str, object]] = {}
    for module_name, module in sorted(sys.modules.items()):
        if not module_name.startswith("phonometry"):
            continue
        for attr, value in list(vars(module).items()):
            if attr.startswith("__") or not isinstance(value, tuple | Mapping):
                continue
            if isinstance(value, type):
                continue
            where = f"{module_name}.{attr}"
            known = places.get(id(value))
            if known is None or len(where) > len(known[0]):
                places[id(value)] = (where, value)
    return tuple(sorted(places.values(), key=lambda item: item[0]))


def _strings_in(value: object, depth: int = 0) -> Iterator[str]:
    """The strings a published tuple holds, or a published table is keyed by."""
    if depth > 4:  # noqa: PLR2004
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _strings_in(item, depth + 1)
    elif isinstance(value, tuple | frozenset):
        for item in value:
            if isinstance(item, str):
                yield item


def test_no_choice_offers_a_band_set_by_name() -> None:
    """A band set is ``fraction=1`` or ``fraction=3``, everywhere.

    A choice that offers ``"third"``, ``"third-octave"`` or
    ``"one-third-octave"`` in a ``Literal``, or defaults to one of them (or
    to ``"octave"``), is the split this closed. So is a choice named for a
    band set that takes a ``str``, whose words a ``Literal`` does not show:
    ``bands: str | None`` checked against a tuple inside the function.
    """
    offenders = []
    for choice in _choices():
        if choice.where in _BAND_SET_EXEMPT:
            continue
        offered = _literal_values(choice.annotation) & _BAND_SET_WORDS
        if offered:
            offenders.append(f"{choice.where}: offers {sorted(offered)}")
        if isinstance(choice.default, str) and choice.default in _BAND_SET_WORDS:
            offenders.append(f"{choice.where}: defaults to {choice.default!r}")
        if choice.name in _BAND_SET_NAMES and _STR.search(choice.annotation):
            offenders.append(
                f"{choice.where}: takes the band set as {choice.annotation!r}"
            )
    assert not offenders, "\n".join(sorted(offenders))


def test_no_table_or_tuple_holds_a_band_set_word() -> None:
    """A table read by band set is keyed by the ``fraction`` a caller passes.

    That holds for the published tables and for the private tuples and
    tables a choice is checked against, which is where the old words would
    come back first.
    """
    offenders = sorted(
        f"{where}: {word!r}"
        for where, value in _module_values()
        if where not in _BAND_SET_EXEMPT
        for word in set(_strings_in(value)) & _BAND_SET_WORDS
    )
    assert not offenders, "\n".join(offenders)


def test_a_sound_field_is_free_diffuse_or_pressure() -> None:
    """A public ``field`` names a sound field one way: free, diffuse or pressure.

    Its options are a ``Literal``, so they can be read here: a ``field``
    typed ``str`` could offer any word behind a tuple inside the function.
    A tuple or table named for a field that holds a sound field holds only
    sound fields, written the one way.
    """
    offenders = []
    for choice in _choices():
        if choice.name != "field" or choice.where in _FIELD_EXEMPT:
            continue
        offered = _literal_values(choice.annotation)
        if not offered:
            offenders.append(
                f"{choice.where}: typed {choice.annotation!r}, with no Literal "
                "to read its options from"
            )
        stray = offered - _SOUND_FIELDS
        if stray:
            offenders.append(f"{choice.where}: offers {sorted(stray)}")
        if isinstance(choice.default, str) and choice.default not in _SOUND_FIELDS:
            offenders.append(f"{choice.where}: defaults to {choice.default!r}")
    for where, value in _module_values():
        if "FIELD" not in where.rpartition(".")[2].upper() or where in _FIELD_EXEMPT:
            continue
        words = set(_strings_in(value))
        if not words & _SOUND_FIELD_WORDS:
            continue
        stray = words - _SOUND_FIELDS
        if stray:
            offenders.append(f"{where}: holds {sorted(stray)}")
    assert not offenders, "\n".join(sorted(offenders))


def test_a_flat_weighting_is_z() -> None:
    """Leaving a signal unweighted is ``weighting="Z"`` wherever it is offered.

    On the sound-level weightings that is the Z-weighting of IEC 61672-1;
    elsewhere it is whatever the standard leaves unweighted, such as the band
    limitation alone of the DIN 45669-1 vibration meter. A ``weighting`` that
    offers ``"unweighted"``, ``"flat"`` or ``"linear"``, or defaults to
    ``None`` for no weighting, is the split this closed, and so is a tuple or
    table named for a weighting that holds one of those words, or any that
    holds ``"unweighted"``: those are what a ``weighting`` is checked against.
    """
    offenders = []
    for choice in _choices():
        if choice.name != "weighting" or choice.where in _WEIGHTING_EXEMPT:
            continue
        flat = _literal_values(choice.annotation) & _FLAT_WORDS
        if flat:
            offenders.append(f"{choice.where}: offers {sorted(flat)}")
        if choice.default is None or choice.default in _FLAT_WORDS:
            offenders.append(f"{choice.where}: defaults to {choice.default!r}")
    for where, value in _module_values():
        if where in _WEIGHTING_EXEMPT:
            continue
        words = set(_strings_in(value))
        named = "WEIGHTING" in where.rpartition(".")[2].upper()
        flat = words & (_FLAT_WORDS if named else {"unweighted"})
        if flat:
            offenders.append(f"{where}: holds {sorted(flat)}")
    assert not offenders, "\n".join(sorted(offenders))


def _reference_source_level_by_word() -> object:
    from result_factories import _reference_source_calibration

    calibration = _reference_source_calibration()
    return calibration.sound_power_level_at([125.0], fraction="octave")  # type: ignore[arg-type]


_FIELD_REFUSED = r"'field' must be one of \('pressure', 'free'\); got 'free_field'"
_FRACTION_REFUSED = r"'fraction' must be 1 \(octave\) or 3 \(one-third octave\)"

#: Each retired spelling, passed where it used to be read, and the refusal it
#: meets now. A function that took the old word back inline, past every
#: annotation and tuple the static rules read, fails here.
_RETIRED_SPELLINGS: list[tuple[str, Callable[[], object], type[Exception], str]] = [
    (
        "vibration meter 'unweighted'",
        lambda: phonometry.vibration.verify_vibration_meter(
            [8.0, 16.0, 31.5],
            [1.0, 1.0, 1.0],
            weighting="unweighted",  # type: ignore[arg-type]
        ),
        ValueError,
        r"'weighting' must be one of \('kb', 'Z'\); got 'unweighted'",
    ),
    (
        "hearing threshold 'free-field'",
        lambda: phonometry.hearing.reference_threshold("free-field"),  # type: ignore[arg-type]
        ValueError,
        r"'field' must be one of \('free', 'diffuse'\); got 'free-field'",
    ),
    (
        "hearing threshold 'diffuse-field'",
        lambda: phonometry.hearing.reference_threshold("diffuse-field"),  # type: ignore[arg-type]
        ValueError,
        r"'field' must be one of \('free', 'diffuse'\); got 'diffuse-field'",
    ),
    (
        "sequential comparison 'free_field'",
        lambda: phonometry.metrology.sequential_comparison(
            [1000.0],
            [-26.0],
            [90.0],
            [89.0],
            field="free_field",  # type: ignore[arg-type]
        ),
        ValueError,
        _FIELD_REFUSED,
    ),
    (
        "simultaneous comparison 'free_field'",
        lambda: phonometry.metrology.simultaneous_comparison(
            [1000.0],
            [-26.0],
            [0.1],
            [0.1],
            field="free_field",  # type: ignore[arg-type]
        ),
        ValueError,
        _FIELD_REFUSED,
    ),
    (
        "comparison budget 'free_field'",
        lambda: phonometry.metrology.comparison_uncertainty_budget(
            {},
            frequency_hz=1000.0,
            field="free_field",  # type: ignore[arg-type]
        ),
        ValueError,
        _FIELD_REFUSED,
    ),
    (
        "reciprocity budget 'free_field'",
        lambda: phonometry.metrology.reciprocity_uncertainty_budget(
            [1000.0],
            {},
            field="free_field",  # type: ignore[arg-type]
        ),
        ValueError,
        _FIELD_REFUSED,
    ),
    (
        "ISO 717 rating 'third-octave'",
        lambda: phonometry.building.weighted_rating(
            [50.0] * 16,
            fraction="third-octave",  # type: ignore[arg-type]
        ),
        ValueError,
        _FRACTION_REFUSED,
    ),
    (
        "mass law 'third'",
        lambda: phonometry.building.mass_law_transmission_loss(
            [500.0],
            10.0,
            fraction="third",  # type: ignore[arg-type]
        ),
        ValueError,
        _FRACTION_REFUSED,
    ),
    (
        "reference source 'octave'",
        _reference_source_level_by_word,
        ValueError,
        _FRACTION_REFUSED,
    ),
    (
        "weighting filter curve=",
        lambda: phonometry.filters.weighting_filter(
            [0.0] * 480,
            48000,
            curve="A",  # type: ignore[call-arg]
        ),
        TypeError,
        r"unexpected keyword argument 'curve'",
    ),
    (
        "quasi-peak meter weighted=",
        lambda: phonometry.broadcast.quasi_peak_meter(
            [0.0] * 480,
            48000,
            weighted=False,  # type: ignore[call-arg]
        ),
        TypeError,
        r"unexpected keyword argument 'weighted'",
    ),
    (
        "intensity band_type=",
        lambda: phonometry.emission.sound_power_intensity(
            [[1.0, 1.0, 1.0]],
            [1.0],
            band_type="third",  # type: ignore[call-arg]
        ),
        TypeError,
        r"unexpected keyword argument 'band_type'",
    ),
]


@pytest.mark.parametrize(
    ("call", "error", "match"),
    [case[1:] for case in _RETIRED_SPELLINGS],
    ids=[case[0] for case in _RETIRED_SPELLINGS],
)
def test_a_retired_spelling_is_refused(
    call: Callable[[], object], error: type[Exception], match: str
) -> None:
    """No function takes an old word back at run time."""
    with pytest.raises(error, match=match):
        call()


def test_a_weighting_is_chosen_by_weighting() -> None:
    """A frequency weighting is ``weighting=``, never a flag or a ``curve``.

    ``a_weighted=True``, ``weighted=False`` and ``curve="A"`` each chose a
    weighting under a name of their own. A parameter or field under one of
    those names that takes a flag or a word is a choice of curve, and fails
    here unless it picks something else, such as a row of a printed table.
    """
    offenders = sorted(
        f"{choice.where}: chooses a weighting as {choice.annotation!r}"
        for choice in _choices()
        if choice.name in _WEIGHTING_FLAGS
        and choice.where not in _WEIGHTING_FLAG_EXEMPT
        and _CHOICE_TYPE.search(choice.annotation)
    )
    assert not offenders, "\n".join(offenders)


@pytest.mark.parametrize(
    "exemptions",
    [_BAND_SET_EXEMPT, _FIELD_EXEMPT, _WEIGHTING_EXEMPT, _WEIGHTING_FLAG_EXEMPT],
    ids=["band_set", "field", "weighting", "weighting_flag"],
)
def test_every_exemption_still_names_something(exemptions: dict[str, str]) -> None:
    """An exemption whose place is gone is a stale one."""
    places = {choice.where for choice in _choices()} | {
        where for where, _ in _module_values()
    }
    stale = sorted(set(exemptions) - places)
    assert not stale, "\n".join(stale)


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        ("Literal['third', 'octave']", {"third", "octave"}),
        ('Literal["free", "diffuse"] | None', {"free", "diffuse"}),
        ("int | None", set()),
        ("Literal[1, 3]", set()),
    ],
)
def test_the_literal_reader_reads_the_strings_offered(
    annotation: str, expected: set[str]
) -> None:
    assert _literal_values(annotation) == expected


def test_an_alias_is_read_as_its_definition() -> None:
    """The guard sees through an alias the module imports to type a choice."""
    text = _expanded("BandFraction | None", "phonometry.building.measurement.ratings")
    assert "Literal[1, 3]" in text
    module = importlib.import_module("phonometry.vibration.structural.building_damage")
    assert _literal_values(_expanded("BuildingClass", module.__name__)) == {
        "commercial",
        "residential",
        "sensitive",
    }


@pytest.mark.parametrize("value", [1, 3])
def test_a_band_fraction_is_one_or_three(value: int) -> None:
    from phonometry._internal.validation import require_band_fraction

    assert require_band_fraction(value, "fraction") == value


@pytest.mark.parametrize("value", [True, 3.0, "third", 2, 24, None])
def test_anything_else_is_refused_as_a_band_set(value: object) -> None:
    """A flag, a measured number or a word is not read as a band set."""
    from phonometry._internal.validation import require_band_fraction

    with pytest.raises(ValueError, match="'fraction' must be 1 .octave. or 3"):
        require_band_fraction(value, "fraction")


def test_the_walk_reaches_the_package() -> None:
    assert sum(1 for _ in _choices()) > 5000  # noqa: PLR2004
    assert phonometry.__name__ == "phonometry"
