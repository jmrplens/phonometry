#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every fixed choice a public parameter or record field offers is a ``Literal``.

A choice typed ``str`` reaches the function as any string a caller types:
``weighting_filter("a")`` or ``sii_procedure("one third octave")`` is
checked, at best, when the call runs, and a type checker sees nothing wrong.
Typed ``Literal["A", "C", "Z"]``, the options are part of the signature, the
editor offers them, and ``mypy`` refuses a misspelling before anything runs.

The guard walks every public function, method and record of the imported
package and reads the source of each. A parameter annotated ``str``, or a
union with a bare ``str`` in it (``str | None``, ``str | float``,
``Literal[...] | str``), is a closed choice when the function itself says so:

* it hands the parameter to a shared validator (``require_choice``,
  ``check_language``, ``check_engine``);
* it compares the parameter with ``in`` against a collection of strings, or
  with ``==`` or ``!=`` against a string;
* it looks the parameter up in a mapping keyed by strings
  (``TABLE[name]``, ``TABLE.get(name)``) or matches it in a ``match``;
* its ``:param:`` text (``:ivar:`` for a record field) names two quoted
  options or more;
* its annotation sets the ``str`` beside an ``Enum`` (``RoadSurface | str``),
  whose members are the options the string spells.

The text is followed through what only normalises it (``str(name)``,
``name.strip().lower()``) and into the local names bound from it (``key =
name.lower()``, ``key = _normalise(name, ALIASES)``, ``key = ALIASES.get(name,
name)``), so a choice checked after it is cleaned up is still a choice.

A record field is read the same way, in the ``__post_init__`` that checks it.
A closed choice is annotated with a ``Literal`` (a shared alias where one
vocabulary recurs: ``Language``, ``ReportEngine``), and a string that is open
by its nature (a path, a label, a catalogue name a caller's catalogue can add
to) goes in :data:`OPEN` with the reason. An entry of :data:`OPEN` that names
nothing the walk finds fails, so the table cannot outlive its reasons. The
fields of a catalogue row are passed over as a class (:data:`CATALOGUE_ROW`):
the catalogue contract holds every text cell to ``str`` and refuses any other
annotation when the package is imported.

A parameter passed on untouched is followed into the function that receives
it, up to six calls deep, so ``hearing_groups(guidance)`` is a choice
because the private ``_check_guidance(guidance)`` it calls compares the text
with a set; a parameter handed to one that is already a ``Literal`` is caught
by ``mypy`` as well, since a ``str`` does not fit it. The parameter is followed
when it is handed on by keyword, by position, inside a dict spread into the
call (``f(**options)``), and into a function the body imports itself; and a
table handed on beside it (``_area_key(area_type, _ACTIVITY_LIMITS)``) is
known to the receiving function by its keys, so the helper's ``key not in
table`` is the closed set it is.

A collection of strings (``Sequence[str]``, ``tuple[str, ...]``,
``set[str]``) and the keys of a mapping are choices of the same kind: each
item is followed through a ``for`` loop, a comprehension, ``enumerate``,
``.items()`` and ``.keys()``, and a set difference with the options
(``set(sides) - _SIDES``) or a subset test (``<=``, ``issubset``) closes the
collection as a whole; a comprehension that copies each item (``{str(d)
for d in limits}``) holds the caller's strings as surely as ``set(sides)``.
The table a test reads may be written in place, held in a local, picked by a
conditional expression both of whose branches are tables, picked out of a
table of tables (``_BUDGET_TABLES[field]``, read as the keys of all of them)
or imported from another module of the package; a frozen table the source
builds with code (``MappingProxyType({**_rows(...)})``) is read off the
imported module. A record field is followed out of the ``__post_init__`` into
the helper it is handed to, and a comparison of ``<record>.<field>`` with a
string in any function of the record's module closes it as well.

An annotation is read through the type aliases of the module that writes it
(:func:`expanded`), the ones under ``if TYPE_CHECKING:`` and the imported
ones included, so ``free_sides: _FreeSides | None`` with ``_FreeSides =
Iterable[str]`` is a collection of any strings. An imported alias is spelled
out in the module that writes it, through that module's own aliases.

A string a caller writes below the top level of a collection or a mapping
(the columns of ``Mapping[int, Mapping[str, float]]``, the items of
``Sequence[Sequence[str]]``) is not followed through the code, so it is
called a choice as it stands: it is typed with its ``Literal``, or it goes
in :data:`OPEN` with the reason it is open (:func:`takes_nested_strings`).

A choice typed ``Literal`` promises one spelling of each option, and the
guard holds the code to it (rule A45, :func:`cleaned_up_choices`): a public
parameter or record field whose annotation is a ``Literal`` (an alias of one,
a union holding one, or a collection or mapping of one) fails when the code
folds its case, strips its spaces, replaces its separators, makes a text of
any value with ``str()`` or maps an alias the ``Literal`` does not list,
before it checks the text as the caller wrote it with ``require_choice`` (or
``if text not in OPTIONS: raise``). A check as written holds the text to the
``Literal`` only when the options it is held against are ones the
``Literal`` lists, so a ``require_choice``, a membership test or a subset
test against a wider set fails too; against one row of a table picked when
the code runs, it is held to the row closest to the ``Literal``. The text is
followed into every function it is handed to, six calls deep, and a record
field from its ``__post_init__`` into every function of its module that
reads it.
"""

from __future__ import annotations

import ast
import collections.abc
import dataclasses
import enum
import functools
import importlib
import importlib.util
import inspect
import pathlib
import pkgutil
import re
import sys
import textwrap
import typing
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

import phonometry
from phonometry._internal.catalogue import CatalogueRow

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
    from types import FunctionType, ModuleType

#: The members of an annotation that let any string through.
_STRING_MEMBERS = frozenset({"str", "Optional[str]"})

#: The generic collections whose items a caller writes one by one.
_COLLECTIONS = frozenset(
    {
        "AbstractSet",
        "Collection",
        "FrozenSet",
        "Iterable",
        "List",
        "MutableSequence",
        "MutableSet",
        "Sequence",
        "Set",
        "Tuple",
        "frozenset",
        "list",
        "set",
        "tuple",
    }
)

#: The generic mappings whose keys a caller writes.
_MAPPINGS = frozenset({"Dict", "Mapping", "MutableMapping", "dict"})

#: A subscripted annotation member, ``Sequence[str]`` or
#: ``collections.abc.Mapping[str, float]``, split into its origin and arguments.
_GENERIC = re.compile(r"(?:\w+\.)*(?P<origin>\w+)\[(?P<arguments>.*)\]", re.DOTALL)

#: Calls that only hold the items of a collection in another container:
#: ``set(sides)`` holds the strings ``sides`` holds.
_CONTAINERS = frozenset({"frozenset", "list", "set", "sorted", "tuple"})

#: Methods that only clean up a text: what they return is the caller's choice.
_NORMALISERS = frozenset(
    {"strip", "lstrip", "rstrip", "lower", "upper", "casefold", "replace", "title"}
)

#: Shared validators that take the value first and refuse what is not an option.
VALIDATORS = frozenset({"require_choice", "check_language", "check_engine"})

#: A quoted option in a docstring: ``"free"``, ``'free'`` or a bare ``"free"``.
_QUOTED = re.compile(
    r"``['\"]([^'\"`]+)['\"]``|(?<![\w`])['\"]([^'\"\s][^'\"]{0,40})['\"](?![\w`])"
)

_EXAMPLE = (
    "an open string: the documented values are examples of what a caller "
    "writes, not the whole set the function accepts"
)
_CATALOGUE_NAME = (
    "a row name of a published catalogue, which a caller's own catalogue "
    "extends at run time (io.Catalogue), so the set is open"
)
_CATALOGUE_KEY = (
    "a '<table>/<row>' key of a published catalogue, the key io.Catalogue "
    "gives every row; the rows are the catalogue's data files, and a caller's "
    "own row is passed as the record itself"
)
_TEXT = "free text a caller writes into a record or a fiche"
_LABEL = "a label the record prints as the page or the caller wrote it"
_NOTATION = (
    "the notation of a single number as the standard prints it (LA,eq, "
    "LC,Fmax,nT), a label"
)
_POSITION_LABEL = "the name the caller gives a measurement position, a label"
_ROW_LABEL = "the name the caller gives a row of the comparison, a label"
_COLUMNS = (
    "the columns of one row of the result, named as the record names them, not "
    "a choice a caller makes"
)
_ANP_FILE = (
    "a word as the ANP database file spells it, and a caller's own database "
    "file may spell it otherwise"
)
_GRADED = (
    "a requirement name read back from the result's own requirements, a key "
    "refused with KeyError (A44), not a choice a caller makes"
)

_PRINTED_TEXT = (
    "the words the standard prints in that row of its table, read, not chosen"
)
_CLAUSE = "the clause, table or figure the standard prints a row under, a reference"
_UNIT = "the unit or reference a value is printed with, a label for display"
_REFERENCE = "the document a row cites, as the source prints it, a reference"

#: Strings that are open on purpose, keyed by ``(module, qualified name,
#: parameter)``, each with its reason. An entry that matches nothing fails.
OPEN: dict[tuple[str, str, str], str] = {
    ("phonometry._internal.catalogue", "CatalogueIssue", "location"): (
        "where in a caller's file the problem is: a JSON pointer, a cell "
        "reference or '<Python>'"
    ),
    ("phonometry._report.metadata", "ReportMetadata", "measurement_standard"): (_TEXT),
    ("phonometry.aircraft.anp_fleet", "ANPAircraft", "engine_type"): _ANP_FILE,
    ("phonometry.aircraft.anp_fleet", "ANPDatabase.__init__", "aircraft"): (
        "the ANP aircraft rows by identifier, each keyed by the column names of "
        "the file it was read from, which a database release may extend"
    ),
    ("phonometry.aircraft.anp_fleet", "ANPDatabase.profile", "profile_id"): (
        "an identifier of the loaded ANP database, whose set depends on the file"
    ),
    ("phonometry.aircraft.anp_fleet", "SpectralClass", "class_id"): (
        "an identifier of the loaded ANP database, whose set depends on the file"
    ),
    ("phonometry.aircraft.flight_performance", "ApproachStep", "step_type"): (
        _ANP_FILE
    ),
    ("phonometry.aircraft.flight_performance", "DepartureStep", "step_type"): (
        _ANP_FILE
    ),
    ("phonometry.aircraft.flight_performance", "DepartureStep", "thrust_rating"): (
        _ANP_FILE
    ),
    (
        "phonometry.building.measurement.ratings",
        "WeightedRatingResult.report",
        "symbol",
    ): "the descriptor ISO 717-1 Tables 1 and 2 print, a label for the fiche",
    ("phonometry.building.regulation.spain", "DBHRRequirement", "quantity"): (
        "the symbol of the quantity the requirement is stated in, a label"
    ),
    (
        "phonometry.building.prediction.installed_structure_borne",
        "installed_source_prediction",
        "paths",
    ): (
        "the named terms of one transmission path, values of different kinds "
        "the function reads by name, not a choice a caller makes"
    ),
    ("phonometry.emission.sound_power_plant", "PlantRequirement", "clause"): (_LABEL),
    (
        "phonometry.environment.assessment.soundscape",
        "method_b_source_ranking",
        "rankings",
    ): (
        "the sources each participant names, compared as given; a study codes "
        "them to its own vocabulary (ISO/TS 12913-2 C.3.2.4)"
    ),
    (
        "phonometry.environment.assessment.soundscape",
        "SoundscapeAcousticEnvironment",
        "site_description",
    ): "ISO/TS 12913-2 A.3 g), the study site described in words",
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralMetric",
        "symbol",
    ): "the metric as Table D.1 prints it, a label",
    ("phonometry.environment.assessment.spain", "RegulationLimits", "index"): (
        "the noise index as the regulation prints it, a label"
    ),
    ("phonometry.filters.compliance", "FilterComplianceResult", "band_margins"): (
        _COLUMNS
    ),
    ("phonometry.filters.compliance", "FilterComplianceResult.plot", "requirement"): (
        "one of the result's own requirements, a set that depends on the "
        "filter class and the edition the result was judged against"
    ),
    (
        "phonometry.filters.compliance",
        "FilterComplianceResult.binding_margin",
        "requirement",
    ): _GRADED,
    (
        "phonometry.filters.compliance",
        "FilterComplianceResult.requirement_class",
        "requirement",
    ): _GRADED,
    ("phonometry.fluids.catalogue", "gases_named", "name"): _CATALOGUE_NAME,
    ("phonometry.materials.absorbers.carpets", "carpets_named", "name"): (
        _CATALOGUE_NAME
    ),
    ("phonometry.materials.absorbers.catalogue", "porous_materials_named", "name"): (
        _CATALOGUE_NAME
    ),
    (
        "phonometry.materials.absorbers.resistive_sheets",
        "resistive_sheets_named",
        "name",
    ): _CATALOGUE_NAME,
    (
        "phonometry.materials.diffusers.measured_scattering",
        "scattering_named",
        "name",
    ): _CATALOGUE_NAME,
    (
        "phonometry.materials.diffusers.predicted_diffusion",
        "diffusion_named",
        "name",
    ): _CATALOGUE_NAME,
    (
        "phonometry.materials.diffusers.predicted_scattering",
        "predicted_scattering_named",
        "name",
    ): _CATALOGUE_NAME,
    ("phonometry.metrology.conformance", "ConformanceVerification", "unit"): (
        "the unit of the numbers the verification holds, a label for the figure"
    ),
    (
        "phonometry.metrology.free_field_corrections",
        "UncertaintyComponentRow",
        "symbol",
    ): "the symbol or name as the table prints it, a label",
    ("phonometry.metrology.reference_values", "ReferenceValue", "quantity"): (
        "the name of the quantity as ISO 1683 prints it, a label"
    ),
    (
        "phonometry.metrology.sound_level_meter",
        "SoundLevelMeterPeriodicRequirement.failure_reason",
        "label",
    ): (
        "a label of the requirement's own 'failed' results, read back from "
        "the record as a key (A44), not a choice a caller makes"
    ),
    ("phonometry.noise_control._duct_path", "DuctElement", "code"): (
        "a worksheet code the caller chooses, a label"
    ),
    (
        "phonometry.noise_control.duct_walls",
        "duct_transmission_loss_named",
        "name",
    ): _CATALOGUE_NAME,
    ("phonometry.materials.resilient.dynamic_stiffness", "resilient_layer", "layer"): (
        _CATALOGUE_KEY
    ),
    ("phonometry.signals._correlation", "time_delay", "window"): (
        "any window scipy.signal.get_window accepts, an open set"
    ),
    ("phonometry.simulation.compute", "RunProvenance", "cuda_driver_api"): (
        "a CUDA version the GPU driver reports, open like every version number"
    ),
    ("phonometry.simulation.compute", "RunProvenance", "cuda_runtime"): (
        "a CUDA version the array library reports, open like every version number"
    ),
    ("phonometry.solids.catalogue", "solids_named", "name"): _CATALOGUE_NAME,
    (
        "phonometry.vibration.machinery.diagnostics",
        "FaultFrequencyResult",
        "source",
    ): "a description of the machine element, the plot's title",
    ("phonometry.vibration.machinery.diagnostics", "FaultLine", "name"): (
        "a short label of the line, unique within a result"
    ),
    (
        "phonometry.building.measurement.service_equipment",
        "ServiceEquipmentResult",
        "ratings",
    ): _NOTATION,
    (
        "phonometry.building.measurement.service_equipment",
        "check_instrument_agreement",
        "instrument_levels",
    ): _NOTATION,
    ("phonometry.emission.sound_power_plant", "partial_plant_contributions", "names"): (
        "the name the caller gives each part, the label of its row"
    ),
    ("phonometry.emission.turbine_noise", "TurbineMicrophoneArray", "labels"): (
        _POSITION_LABEL
    ),
    (
        "phonometry.emission.turbine_noise",
        "TurbineSoundPowerResult.plot",
        "position_labels",
    ): _POSITION_LABEL,
    (
        "phonometry.environment.assessment.soundscape",
        "SoundscapeAcousticEnvironment",
        "measurement_results",
    ): (
        "the symbols ISO/TS 12913-2 A.3 f) prints, seven required and any other "
        "result the study reports allowed, so the set is open"
    ),
    (
        "phonometry.environment.propagation.software_quality",
        "CalculationVerification",
        "labels",
    ): _ROW_LABEL,
    (
        "phonometry.environment.propagation.software_quality",
        "verify_calculation_results",
        "labels",
    ): _ROW_LABEL,
    (
        "phonometry.environment.sources._statistical_pass_by",
        "normalized_reference_levels",
        "surface_levels",
    ): (
        "a label for each surface averaged; the vehicle categories inside each "
        "are the typed choice"
    ),
    (
        "phonometry.environment.sources.rolling_stock_noise",
        "rolling_stock_test",
        "run_levels",
    ): (_POSITION_LABEL),
    (
        "phonometry.filters.weighting_compliance",
        "WeightingComplianceResult",
        "band_margins",
    ): _COLUMNS,
    (
        "phonometry.filters.weighting_compliance",
        "WeightingComplianceResult",
        "between_nominals",
    ): _COLUMNS,
    ("phonometry.io._catalogue", "Catalogue", "extras"): (
        "the caller's own x-... columns of each row, named by the caller"
    ),
    ("phonometry.io._catalogue", "Catalogue", "name"): (
        "the name the caller gives a catalogue, the table its rows are filed under"
    ),
    ("phonometry.io._catalogue", "write_catalogue", "rows"): _CATALOGUE_KEY,
    ("phonometry.io._wav", "AudioFileInfo", "container"): (
        "the container a file declares: WAV, RF64 or BW64 for the WAV family, or the "
        "format name libsndfile reports for any other, an open set"
    ),
    (
        "phonometry.metrology.free_field_corrections",
        "CorrectionUncertaintyBudget",
        "descriptors",
    ): (
        "a1 to a15 of Table I.1, then the names the laboratory gives the "
        "components its own method adds"
    ),
    ("phonometry.noise_control.enclosure_insulation", "MethodEntry", "quantities"): (
        "the symbols of the quantities a row of Table 1 gives, as it prints them"
    ),
    (
        "phonometry.building.measurement.heavy_impact",
        "HeavyImpactSourceSpec",
        "description",
    ): _PRINTED_TEXT,
    (
        "phonometry.building.measurement.service_equipment",
        "OperatingCondition",
        "clause",
    ): _CLAUSE,
    (
        "phonometry.building.measurement.service_equipment",
        "OperatingCondition",
        "conditions",
    ): _PRINTED_TEXT,
    (
        "phonometry.building.measurement.service_equipment",
        "OperatingCondition",
        "equipment",
    ): _PRINTED_TEXT,
    ("phonometry.building.regulation.spain", "DBHRRequirement", "unit"): _UNIT,
    (
        "phonometry.electroacoustics.induction_loop",
        "LoopRequirement",
        "clause",
    ): _CLAUSE,
    (
        "phonometry.electroacoustics.induction_loop",
        "OverloadTestFrequency",
        "program",
    ): _PRINTED_TEXT,
    (
        "phonometry.electroacoustics.induction_loop_components",
        "NeckLoopType",
        "description",
    ): _PRINTED_TEXT,
    (
        "phonometry.emission.sound_power_plant",
        "PlantRequirement",
        "description",
    ): _PRINTED_TEXT,
    ("phonometry.emission.sound_power_plant", "PlantRequirement", "key"): _GRADED,
    ("phonometry.emission.sound_power_plant", "PlantRequirement", "unit"): _UNIT,
    (
        "phonometry.environment.assessment.soundscape",
        "QuestionnaireScale",
        "figure",
    ): _CLAUSE,
    (
        "phonometry.environment.assessment.soundscape",
        "QuestionnaireScale",
        "instruction",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.assessment.soundscape",
        "QuestionnaireScale",
        "question",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.assessment.soundscape",
        "QuestionnaireScale",
        "subject",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralMetric",
        "method",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralMetric",
        "unit",
    ): _UNIT,
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralParameter",
        "metrics",
    ): _NOTATION,
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralParameter",
        "parameter",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.assessment.soundscape_binaural",
        "BinauralParameter",
        "reference",
    ): _REFERENCE,
    (
        "phonometry.environment.assessment.spain",
        "RegulationLimits",
        "reference",
    ): _REFERENCE,
    (
        "phonometry.environment.assessment.wind_turbine_receptor",
        "GroundImpedanceClass",
        "description",
    ): _PRINTED_TEXT,
    (
        "phonometry.environment.sources.rolling_stock_noise",
        "TrackCondition",
        "clause",
    ): _CLAUSE,
    ("phonometry.filters.periodic_tests", "PeriodicTestClause", "title"): _PRINTED_TEXT,
    (
        "phonometry.io._video",
        "VideoOptions",
        "vaapi_device",
    ): "the path of a render device on the caller's machine",
    (
        "phonometry.materials.absorbers.porous",
        "FiberResistivityFit",
        "source",
    ): _REFERENCE,
    (
        "phonometry.metrology.comparison_calibration",
        "ComparisonUncertaintyRow",
        "component",
    ): _PRINTED_TEXT,
    (
        "phonometry.metrology.comparison_calibration",
        "ReferenceCalibrationRow",
        "method",
    ): _PRINTED_TEXT,
    (
        "phonometry.metrology.comparison_calibration",
        "ReferenceCalibrationRow",
        "references",
    ): _REFERENCE,
    (
        "phonometry.metrology.free_field_corrections",
        "UncertaintyComponentRow",
        "description",
    ): _PRINTED_TEXT,
    (
        "phonometry.metrology.reciprocity_calibration",
        "ReciprocityUncertaintyRow",
        "group",
    ): _PRINTED_TEXT,
    (
        "phonometry.metrology.reference_values",
        "ReferenceValue",
        "printed",
    ): _PRINTED_TEXT,
    ("phonometry.metrology.reference_values", "ReferenceValue", "unit"): _UNIT,
    (
        "phonometry.metrology.sound_level_meter",
        "SoundLevelMeterPeriodicRequirement",
        "tables",
    ): _CLAUSE,
    (
        "phonometry.noise_control.enclosure_insulation",
        "MethodEntry",
        "base_standard",
    ): _REFERENCE,
    (
        "phonometry.noise_control.enclosure_insulation",
        "MethodEntry",
        "subclause",
    ): _CLAUSE,
    (
        "phonometry.noise_control.enclosure_insulation",
        "MethodEntry",
        "test_environment",
    ): _PRINTED_TEXT,
    ("phonometry.room.auditorium", "AuditoriumQuantity", "aspect"): _PRINTED_TEXT,
    ("phonometry.room.auditorium", "AuditoriumQuantity", "unit"): _UNIT,
    ("phonometry.room.workroom_prediction", "PredictionMethod", "rooms"): _PRINTED_TEXT,
    (
        "phonometry.underwater.bioacoustics.weighting",
        "ExposureCriteria",
        "peak_reference",
    ): _UNIT,
    (
        "phonometry.underwater.bioacoustics.weighting",
        "ExposureCriteria",
        "sel_reference",
    ): _UNIT,
    (
        "phonometry.underwater.bioacoustics.weighting",
        "WeightingParameters",
        "description",
    ): _PRINTED_TEXT,
    (
        "phonometry.underwater.propagation.weston_regimes",
        "WestonSeabed",
        "name",
    ): "the name a caller gives a seabed of their own; the two published ones are the keys of WESTON_SEABEDS",
}

#: Why a catalogue row is passed over: the catalogue contract
#: (``phonometry._internal.catalogue``) classifies every field from its
#: annotation and refuses at import anything but ``str`` for a text cell,
#: because a cell the page leaves blank is the empty string and a caller's
#: catalogue (io.Catalogue) prints the words of its own page.
CATALOGUE_ROW = (
    "a text cell of a catalogue row is str by the catalogue contract, which "
    "refuses any other annotation"
)


class Choice(NamedTuple):
    """One public string parameter or field and what says it is closed."""

    module: str
    qualname: str
    name: str
    annotation: str
    evidence: tuple[str, ...]


def _members(annotation: str) -> list[str]:
    """The members of a union annotation, split at its top-level ``|``."""
    members: list[str] = []
    depth = 0
    current: list[str] = []
    for character in annotation:
        if character in "[(":
            depth += 1
        elif character in "])":
            depth -= 1
        if character == "|" and depth == 0:
            members.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    members.append("".join(current).strip())
    return members


def takes_any_string(annotation: str) -> bool:
    """Whether an annotation lets any string through: ``str`` alone or in a union."""
    return any(member in _STRING_MEMBERS for member in _members(annotation))


def _generic(member: str) -> tuple[str, list[str]] | None:
    """The origin and the arguments of a subscripted member, or ``None``."""
    found = _GENERIC.fullmatch(member.strip())
    if found is None:
        return None
    return found["origin"], [part.strip() for part in _split(found["arguments"])]


def _split(arguments: str) -> list[str]:
    """The arguments of a subscript, split at its top-level commas."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for character in arguments:
        if character in "[(":
            depth += 1
        elif character in "])":
            depth -= 1
        if character == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(character)
    parts.append("".join(current))
    return parts


def _item(member: str) -> str | None:
    """The annotation of what a caller writes into a collection or mapping member.

    The item of ``Sequence[X]``, ``tuple[X, ...]`` or ``frozenset[X]``, and the
    key of ``Mapping[X, Y]``; ``None`` for any other member.
    """
    parsed = _generic(member)
    if parsed is None:
        return None
    origin, arguments = parsed
    if origin in _MAPPINGS and len(arguments) == 2:
        return arguments[0]
    if origin in {"tuple", "Tuple"}:
        homogeneous = len(arguments) == 2 and arguments[1] == "..."
        return arguments[0] if homogeneous else None
    if origin in _COLLECTIONS and len(arguments) == 1:
        return arguments[0]
    return None


def takes_any_strings(annotation: str) -> bool:
    """Whether an annotation lets a collection of any strings through.

    A ``Sequence[str]``, ``Iterable[str]``, ``tuple[str, ...]``, ``set[str]``
    or ``frozenset[str]``, or a ``Mapping[str, ...]`` whose keys a caller
    writes, alone or in a union: ``free_sides: str | Iterable[str]`` takes the
    choice one string at a time as surely as ``str`` takes one.
    """
    return any(_item(member) in _STRING_MEMBERS for member in _members(annotation))


def _inner(member: str) -> list[str]:
    """What a caller writes inside one collection or mapping member.

    The values of ``Mapping[X, Y]``, the item of ``Sequence[X]`` or
    ``tuple[X, ...]`` and each member of a fixed ``tuple[X, Y]``; nothing for
    any other member.
    """
    parsed = _generic(member)
    if parsed is None:
        return []
    origin, arguments = parsed
    if origin in _MAPPINGS and len(arguments) == 2:
        return [arguments[1]]
    if origin in {"tuple", "Tuple"}:
        return [argument for argument in arguments if argument != "..."]
    if origin in _COLLECTIONS and len(arguments) == 1:
        return arguments
    return []


def takes_nested_strings(annotation: str) -> bool:
    """Whether a caller writes any strings below the top level of an annotation.

    The keys of the inner mapping of ``Mapping[int, Mapping[str, float]]``,
    the items of the inner sequence of ``Sequence[Sequence[str]]``, at any
    depth. The code evidence follows a collection's items and a mapping's
    keys one level down and no further, so a string held deeper is called a
    choice without it: it takes its ``Literal``, or :data:`OPEN` says why it
    is open.
    """
    return any(
        takes_any_strings(inner) or takes_nested_strings(inner)
        for member in _members(annotation)
        for inner in _inner(member)
    )


#: What a string below the top level of an annotation is called by.
NESTED = "a string below the top level of what a caller writes, not followed"


def enum_beside(annotation: str, module: ModuleType | None) -> list[str]:
    """The evidence that a ``str`` stands beside an ``Enum`` of the options.

    ``RoadSurface | str`` takes the members or the strings they stand for: the
    string half is the same closed set, written out as text.
    """
    namespace = vars(module) if module is not None else {}
    return [
        f"a str beside the Enum {member}"
        for member in _members(annotation)
        if isinstance(namespace.get(member), type)
        and issubclass(namespace[member], enum.Enum)
    ]


def _bare(node: ast.expr) -> ast.expr:
    """*node* without the calls that only clean up a text around it."""
    while isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "str"
            and len(node.args) == 1
        ):
            node = node.args[0]
        elif isinstance(node.func, ast.Attribute) and node.func.attr in _NORMALISERS:
            node = node.func.value
        else:
            break
    return node


def _derived_from(value: ast.expr, matches: Callable[[ast.expr], bool]) -> bool:
    """Whether an assigned *value* is the target, cleaned up, resolved or held.

    The target itself through the calls that only clean it up, an alias
    lookup ``ALIASES.get(name, name)``, a private helper handed the target
    first (``_normalise(name, ALIASES, "name")``), or the strings of the
    target held in another container: ``tuple(sides)``, ``set(sides)``, a
    comprehension that copies each item (``{str(d) for d in limits}``) or
    the one-item ``(side,)`` a bare string becomes, on either branch of a
    conditional expression.
    """
    if matches(value):
        return True
    if isinstance(value, ast.Call) and value.args and matches(value.args[0]):
        name = _call_name(value)
        return name == "get" or name.startswith("_") or _holds_items(value)
    if isinstance(value, ast.Call) and _holds_items(value):
        return _derived_from(value.args[0], matches)
    if isinstance(value, ast.IfExp):
        # ``(x,) if isinstance(x, str) else tuple(x)``: one name or several.
        return _derived_from(value.body, matches) or _derived_from(
            value.orelse, matches
        )
    if isinstance(value, ast.Tuple | ast.List | ast.Set):
        return any(matches(element) for element in value.elts)
    if isinstance(value, ast.SetComp | ast.ListComp | ast.GeneratorExp):
        return _copies_items(value, matches)
    return False


def _copies_items(
    value: ast.SetComp | ast.ListComp | ast.GeneratorExp,
    matches: Callable[[ast.expr], bool],
) -> bool:
    """Whether a comprehension holds the target's items, each cleaned up.

    ``{str(direction) for direction in limits}`` or ``[s.lower() for s in
    sides]``: one loop over the target (its keys, for a mapping) whose element
    is the loop variable through the calls that only clean up a text.
    """
    if len(value.generators) != 1:
        return False
    generator = value.generators[0]
    element = _bare(value.elt)
    return (
        isinstance(generator.target, ast.Name)
        and isinstance(element, ast.Name)
        and element.id == generator.target.id
        and matches(_held(_keys_of(generator.iter)))
    )


def _keys_of(node: ast.expr) -> ast.expr:
    """*node* without a ``.keys()`` that only reads a mapping's keys."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "keys"
        and not node.args
        and not node.keywords
    ):
        return node.func.value
    return node


def _holds_items(node: ast.Call) -> bool:
    """Whether a call only holds the items of its one argument.

    ``set(x)``, ``tuple(x)``, ``sorted(x)`` and ``dict.fromkeys(x)``, which
    keeps the strings of ``x`` as its keys, in their order, once each.
    """
    if len(node.args) != 1 or node.keywords:
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id in _CONTAINERS
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "fromkeys"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "dict"
    )


def _held(node: ast.expr) -> ast.expr:
    """*node* without a call that only holds its items: ``set(x)`` is ``x``."""
    while isinstance(node, ast.Call) and _holds_items(node):
        node = node.args[0]
    return node


def _following(
    tree: ast.AST, is_target: Callable[[ast.expr], bool]
) -> Callable[[ast.expr], bool]:
    """*is_target* widened to the cleaned-up text and the locals bound from it."""
    names: set[str] = set()

    def matches(node: ast.expr) -> bool:
        node = _bare(node)
        return is_target(node) or (isinstance(node, ast.Name) and node.id in names)

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                bound, value = node.targets[0].id, node.value
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None
            ):
                bound, value = node.target.id, node.value
            else:
                continue
            if bound not in names and _derived_from(value, matches):
                names.add(bound)
                changed = True
    return matches


def _module_constants(module: ModuleType | None) -> dict[str, ast.expr]:
    """The module-level assignments of *module*, by name, as expressions.

    A constant the module imports from another module of the package
    (``from .fdtd import _SIDES``) is the expression it is assigned there.
    """
    if module is None:
        return {}
    return dict(_constants_of(module.__name__))


#: How many imports deep a module's constants are followed.
_IMPORT_DEPTH = 3


def _assigned(node: ast.stmt) -> list[tuple[str, ast.expr]]:
    """The names a module-level assignment binds, each with its value.

    ``X = ...``, ``X: T = ...`` and the ``type X = ...`` of an alias.
    """
    if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
        return [(node.name.id, node.value)]
    if isinstance(node, ast.Assign):
        return [
            (target.id, node.value)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return [(node.target.id, node.value)]
    return []


def _import_source(node: ast.ImportFrom, package: str) -> str | None:
    """The module of the package a ``from ... import`` reads, or None for one
    outside the package or a relative import that resolves to nothing.
    """
    try:
        source = importlib.util.resolve_name(
            "." * node.level + (node.module or ""), package
        )
    except ValueError:
        return None
    return source if source.startswith("phonometry") else None


def _parsed_module(module_name: str) -> tuple[ModuleType, ast.Module, str] | None:
    """The imported module *module_name*, its parsed source and its package,
    or None when it cannot be imported or its source cannot be read.

    A module of the package imported only under ``TYPE_CHECKING`` is not
    loaded yet: it is imported here, or the readers cached on this keep it
    empty whatever runs later.
    """
    module = sys.modules.get(module_name)
    if module is None and module_name.startswith("phonometry"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            module = None
    if module is None:
        return None
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError, SyntaxError):
        return None
    return module, tree, module.__package__ or module_name.rpartition(".")[0]


def _imported_constants(
    node: ast.ImportFrom, package: str, depth: int
) -> list[tuple[str, ast.expr]]:
    """The constants a ``from ... import`` of the package brings in, by the
    name the importing module gives them.
    """
    source = _import_source(node, package)
    if source is None:
        return []
    imported = _constants_of(source, depth + 1)
    return [
        (alias.asname or alias.name, imported[alias.name])
        for alias in node.names
        if alias.name in imported
    ]


def _module_statements(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    """The statements of a module body, those of its top-level ``if`` blocks
    included: an alias or an import under ``if TYPE_CHECKING:`` is the
    module's as surely as one written at the top.
    """
    for node in body:
        if isinstance(node, ast.If):
            yield from _module_statements(node.body)
            yield from _module_statements(node.orelse)
        else:
            yield node


@functools.cache
def _constants_of(module_name: str, depth: int = 0) -> MappingProxyType[str, ast.expr]:
    parsed = _parsed_module(module_name)
    if parsed is None:
        return MappingProxyType({})
    module, tree, package = parsed
    found: dict[str, ast.expr] = {}
    for node in _module_statements(tree.body):
        if isinstance(node, ast.ImportFrom):
            if depth < _IMPORT_DEPTH:
                for name, value in _imported_constants(node, package, depth):
                    found.setdefault(name, value)
            continue
        found.update(_assigned(node))
    _read_frozen_tables(found, vars(module))
    return MappingProxyType(found)


def _read_frozen_tables(
    found: dict[str, ast.expr], namespace: dict[str, object]
) -> None:
    """Replace each constant of *found* the source builds with code by its value.

    Only a constant whose expression holds no strings :func:`strings_of` can
    read, and only when the running module holds a frozen table under its name
    (:func:`_runtime_table`).
    """
    for name, value in list(found.items()):
        if strings_of(value, found):
            continue
        held = _runtime_table(namespace.get(name))
        if held is not None:
            found[name] = held


#: How many tables deep a table of tables is spelled out from its value.
_TABLE_DEPTH = 2


def _runtime_table(value: object, depth: int = 0) -> ast.expr | None:
    """A frozen table of strings the source builds with code, as its value reads.

    ``MappingProxyType({**_rows(...)})`` names its keys only when it runs; a
    published table is frozen (a ``MappingProxyType``, a ``tuple`` or a
    ``frozenset``), so its keys or items are read off the imported module and
    spelled as the display that would hold them. A mutable ``dict`` is left
    alone: a cache or a registry fills one as the program runs.
    """
    if depth > _TABLE_DEPTH:
        return None
    if (
        isinstance(value, MappingProxyType)
        and value
        and all(isinstance(key, str) for key in value)
    ):
        return ast.Dict(
            keys=[ast.Constant(value=key) for key in value],
            values=[
                _runtime_table(item, depth + 1) or ast.Constant(value=None)
                for item in value.values()
            ],
        )
    if (
        isinstance(value, tuple | frozenset)
        and value
        and all(isinstance(item, str) for item in value)
    ):
        items = sorted(value) if isinstance(value, frozenset) else list(value)
        return ast.Tuple(
            elts=[ast.Constant(value=item) for item in items], ctx=ast.Load()
        )
    return None


#: How many names, calls and subscripts deep a set of strings is resolved.
_STRINGS_DEPTH = 6


def strings_of(
    node: ast.expr | None, constants: Mapping[str, ast.expr], depth: int = 0
) -> tuple[str, ...]:
    """The string options an expression holds, or ``()`` when it holds none.

    A tuple, list or set of string constants, the string keys of a dict, a
    call wrapping one of those (``frozenset(...)``, ``MappingProxyType(...)``),
    a name bound to one of those (a module constant, or a local the caller
    adds to *constants*), a conditional expression both of whose branches
    hold one (``_SIDES if strict else ("top",)``), and one table of a table of
    tables (``_TABLES[kind]``), read as the keys any of its tables holds.
    """
    if node is None or depth > _STRINGS_DEPTH:
        return ()
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return _display_strings(node.elts, constants, depth)
    if isinstance(node, ast.Dict):
        return tuple(
            text for key in node.keys if (text := _key_text(key, constants)) is not None
        )
    if isinstance(node, ast.Call) and node.args:
        return strings_of(node.args[0], constants, depth + 1)
    if isinstance(node, ast.Name) and node.id in constants:
        return strings_of(constants[node.id], constants, depth + 1)
    return _picked_strings(node, constants, depth)


def _display_strings(
    elements: list[ast.expr], constants: Mapping[str, ast.expr], depth: int
) -> tuple[str, ...]:
    """The strings a tuple, list or set display holds, or ``()``.

    Each item is a string written in place or a starred set of strings
    (``(*_SINGLE, *_ALIASES)`` holds the items of one and the keys of the
    other); one item of another kind makes the display no set of strings.
    """
    values: list[str] = []
    for element in elements:
        if isinstance(element, ast.Constant) and isinstance(element.value, str):
            values.append(element.value)
            continue
        held = (
            strings_of(element.value, constants, depth + 1)
            if isinstance(element, ast.Starred)
            else ()
        )
        if not held:
            return ()
        values.extend(held)
    return tuple(values)


def _key_text(key: ast.expr | None, constants: Mapping[str, ast.expr]) -> str | None:
    """The string a dict display key holds: written in place, or a module
    constant bound to one (``{_DNT_A: ...}`` with ``_DNT_A = "DnT,A"``).
    """
    if isinstance(key, ast.Name) and key.id in constants:
        key = constants[key.id]
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        return key.value
    return None


def _picked_strings(
    node: ast.expr, constants: Mapping[str, ast.expr], depth: int
) -> tuple[str, ...]:
    """The strings of a table picked when the code runs, or ``()``.

    One branch of a conditional expression both of whose branches hold
    strings, or one table of a table of tables (:func:`_keys_of_tables`).
    """
    if isinstance(node, ast.IfExp):
        body = strings_of(node.body, constants, depth + 1)
        orelse = strings_of(node.orelse, constants, depth + 1)
        return tuple(dict.fromkeys(body + orelse)) if body and orelse else ()
    if isinstance(node, ast.Subscript):
        return _keys_of_tables(node.value, constants, depth + 1)
    return ()


def _dict_display(
    node: ast.expr, constants: Mapping[str, ast.expr], depth: int
) -> ast.Dict | None:
    """The dict display a name or a wrapping call stands for, or ``None``."""
    while depth <= _STRINGS_DEPTH:
        if isinstance(node, ast.Dict):
            return node
        if isinstance(node, ast.Name) and node.id in constants:
            node = constants[node.id]
        elif isinstance(node, ast.Call) and node.args:
            node = node.args[0]
        else:
            return None
        depth += 1
    return None


def _keys_of_tables(
    node: ast.expr, constants: Mapping[str, ast.expr], depth: int
) -> tuple[str, ...]:
    """The keys of the tables a table of tables holds, all of them together.

    ``_BUDGET_TABLES[field]`` is one of the tables ``_BUDGET_TABLES`` maps to,
    so a key is closed when every one of them holds strings; the union is the
    set a caller may pick from, whichever table is picked.
    """
    table = _dict_display(node, constants, depth)
    if table is None or not table.values:
        return ()
    keys: list[str] = []
    for value in table.values:
        held = strings_of(value, constants, depth + 1)
        if not held:
            return ()
        keys.extend(held)
    return tuple(dict.fromkeys(keys))


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


#: The set methods that keep what is not, or say whether all is, in a set of
#: strings: ``set(sides).difference(SIDES)``, ``set(sides).issubset(SIDES)``.
_SET_TESTS = frozenset({"difference", "issubset"})

_SUBSET = "a subset of a set of strings"


def _set_call_evidence(
    node: ast.Call,
    is_target: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
) -> list[str]:
    """What a set method call says of the target's strings."""
    if not (isinstance(node.func, ast.Attribute) and node.args):
        return []
    owner, argument = node.func.value, node.args[0]
    if (
        node.func.attr in _SET_TESTS
        and is_target(_held(owner))
        and strings_of(argument, constants)
    ):
        return [_SUBSET]
    if (
        node.func.attr == "issuperset"
        and strings_of(owner, constants)
        and is_target(_held(argument))
    ):
        return [_SUBSET]
    return []


def _text_evidence(
    operator: ast.cmpop, right: ast.expr, constants: dict[str, ast.expr]
) -> list[str]:
    """What ``target <operator> right`` says of the target's text."""
    if isinstance(operator, ast.In | ast.NotIn) and strings_of(right, constants):
        return ["'in' a set of strings"]
    # An empty text is no option: ``label == ""`` asks whether one was
    # written at all.
    if (
        isinstance(operator, ast.Eq | ast.NotEq)
        and isinstance(right, ast.Constant)
        and isinstance(right.value, str)
        and right.value
    ):
        return [f"== {right.value!r}"]
    return []


def _subset_evidence(
    left: ast.expr,
    operator: ast.cmpop,
    right: ast.expr,
    is_target: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
) -> bool:
    """Whether ``left <operator> right`` tests the target's strings as a
    subset of a set of strings (``set(sides) <= SIDES``).
    """
    if isinstance(operator, ast.LtE | ast.Lt):
        return is_target(_held(left)) and bool(strings_of(right, constants))
    if isinstance(operator, ast.GtE | ast.Gt):
        return bool(strings_of(left, constants)) and is_target(_held(right))
    return False


def _looked_for(
    left: ast.expr,
    operator: ast.cmpop,
    right: ast.expr,
    is_target: Callable[[ast.expr], bool],
) -> list[str]:
    """``"top" in sides``: one string looked for among the target's items."""
    if (
        isinstance(operator, ast.In | ast.NotIn)
        and isinstance(left, ast.Constant)
        and isinstance(left.value, str)
        and is_target(right)
    ):
        return [f"{left.value!r} 'in' it"]
    return []


def _comparison_evidence(
    node: ast.Compare,
    is_target: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
    *,
    collection: bool,
) -> list[str]:
    """What one comparison says of the target, pair by pair."""
    found: list[str] = []
    left = node.left
    for operator, right in zip(node.ops, node.comparators, strict=True):
        if is_target(left):
            found.extend(_text_evidence(operator, right, constants))
        if _subset_evidence(left, operator, right, is_target, constants):
            found.append(_SUBSET)
        if collection:
            found.extend(_looked_for(left, operator, right, is_target))
        left = right
    return found


def _item_names(tree: ast.AST, is_target: Callable[[ast.expr], bool]) -> set[str]:
    """The names a loop or a comprehension binds to each item of the target.

    ``for side in sides``, ``[f for f in fields]``, ``for i, side in
    enumerate(sides)`` and, for a mapping, the key of ``for key, value in
    levels.items()`` or ``for key in levels.keys()``.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
            continue
        source, bound = node.iter, node.target
        position = 0
        if (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr in {"items", "keys"}
            and not source.args
        ):
            source = source.func.value
        elif (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Name)
            and source.func.id == "enumerate"
            and source.args
        ):
            source, position = source.args[0], 1
        if not is_target(_held(source)):
            continue
        if isinstance(bound, ast.Tuple) and len(bound.elts) > position:
            bound = bound.elts[position]
        if isinstance(bound, ast.Name):
            names.add(bound.id)
    return names


def _local_tables(
    tree: ast.AST, constants: Mapping[str, ast.expr]
) -> dict[str, ast.expr]:
    """The locals of *tree* bound to a set of strings, by name.

    ``table = _BUDGET_TABLES[field]``, ``table = _SIDES if strict else
    ("top",)`` or ``options = tuple(_SIDES)``: a test against the local is a
    test against the strings it holds (:func:`strings_of`).
    """
    found: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        for name, value in _assigned(node):
            if strings_of(value, {**constants, **found}):
                found.setdefault(name, value)
    return found


def code_evidence(
    tree: ast.AST,
    is_target: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
    *,
    collection: bool = False,
) -> list[str]:
    """What in *tree* treats the target as one of a fixed set of strings.

    A *collection* of strings is one when what is left of it once a set of
    strings is taken away is refused (``set(sides) - set(SIDES)``), when it
    is tested as a subset of one (``set(sides) <= SIDES``,
    ``.issubset(SIDES)``), or when one string is looked for in it
    (``"top" in sides``). The set of strings may be held in a local of
    *tree* (:func:`_local_tables`) as well as written in place.
    """
    found: list[str] = []
    constants = {**constants, **_local_tables(tree, constants)}
    is_target = _following(tree, is_target)
    items = _item_names(tree, is_target) if collection else set()
    if items:
        found.extend(
            f"each item {evidence}"
            for evidence in code_evidence(
                tree,
                lambda node: isinstance(node, ast.Name) and node.id in items,
                constants,
            )
        )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if node.args and is_target(node.args[0]) and name in VALIDATORS:
                found.append(f"{name}()")
            if (
                name == "get"
                and isinstance(node.func, ast.Attribute)
                and node.args
                and is_target(node.args[0])
                and strings_of(node.func.value, constants)
            ):
                found.append("a lookup by key")
            found.extend(_set_call_evidence(node, is_target, constants))
        elif isinstance(node, ast.Compare):
            found.extend(
                _comparison_evidence(node, is_target, constants, collection=collection)
            )
        elif (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Sub)
            and is_target(_held(node.left))
            and strings_of(node.right, constants)
        ):
            found.append("a set difference with a set of strings")
        elif (
            isinstance(node, ast.Subscript)
            and is_target(node.slice)
            and strings_of(node.value, constants)
        ):
            found.append("a lookup by key")
        elif isinstance(node, ast.Match) and is_target(node.subject):
            found.append("a match on strings")
    return found


#: How many calls deep a parameter passed on untouched is followed.
_PASS_DEPTH = 6


def _local_imports(tree: ast.AST, module_name: str) -> dict[str, object]:
    """The names a function body imports itself, resolved to their objects."""
    module = sys.modules.get(module_name)
    package = getattr(module, "__package__", None) or module_name.rpartition(".")[0]
    found: dict[str, object] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        source = "." * node.level + (node.module or "")
        try:
            imported = importlib.import_module(
                importlib.util.resolve_name(source, package)
            )
        except (ImportError, ValueError):
            continue
        for alias in node.names:
            found[alias.asname or alias.name] = getattr(imported, alias.name, None)
    return found


def _spread_dicts(tree: ast.AST) -> dict[str, dict[str, ast.expr]]:
    """The dicts of keyword arguments a body builds to spread into a call."""
    found: dict[str, dict[str, ast.expr]] = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            continue
        value = node.value
        entries: dict[str, ast.expr] = {}
        if isinstance(value, ast.Dict):
            entries = {
                key.value: item
                for key, item in zip(value.keys, value.values, strict=True)
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
        elif isinstance(value, ast.Call) and _is_dict_call(value):
            entries = {
                keyword.arg: keyword.value
                for keyword in value.keywords
                if keyword.arg is not None
            }
        if entries:
            found[node.targets[0].id] = entries
    return found


def _is_dict_call(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
    )


def _callee(
    node: ast.Call, namespace: dict[str, object], home: str = "phonometry"
) -> FunctionType | None:
    """The function a call names, looked up in *namespace*.

    One of the package's, or one of the module *home* the caller lives in. A
    method reaches its own class through ``self`` and ``cls``
    (:func:`_namespace`), and an object it holds through the annotation of
    the field (``self.database.event_level(...)``).
    """
    target: object | None = None
    function = node.func
    if isinstance(function, ast.Name):
        target = namespace.get(function.id)
    elif isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
        owner = namespace.get(function.value.id)
        target = getattr(owner, function.attr, None) if owner is not None else None
    elif (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Attribute)
        and isinstance(function.value.value, ast.Name)
        and function.value.value.id == "self"
    ):
        holder = namespace.get("self")
        held = (
            _held_class(holder, function.value.attr)
            if inspect.isclass(holder)
            else None
        )
        target = getattr(held, function.attr, None) if held is not None else None
    target = getattr(target, "__func__", target)
    if inspect.isclass(target):
        target = vars(target).get("__init__")
    if inspect.isfunction(target) and (
        target.__module__.startswith("phonometry") or target.__module__ == home
    ):
        return target
    return None


def _arguments(
    node: ast.Call, callee: FunctionType, spread: dict[str, dict[str, ast.expr]]
) -> dict[str, ast.expr]:
    """What a call hands each parameter of *callee*, by the parameter's name.

    By position, by keyword, and from a dict of keywords the body built and
    spreads into the call (``f(**options)``).
    """
    try:
        parameters = list(inspect.signature(callee).parameters)
    except (TypeError, ValueError):
        return {}
    if parameters and parameters[0] in {"self", "cls"}:
        parameters = parameters[1:]
    handed: dict[str, ast.expr] = {}
    for index, argument in enumerate(node.args):
        if isinstance(argument, ast.Starred) or index >= len(parameters):
            break
        handed[parameters[index]] = argument
    for keyword in node.keywords:
        if keyword.arg is not None:
            handed[keyword.arg] = keyword.value
        elif isinstance(keyword.value, ast.Name):
            handed.update(
                (key, value)
                for key, value in spread.get(keyword.value.id, {}).items()
                if key in parameters
            )
    return handed


def _bound_tables(
    handed: dict[str, ast.expr], constants: dict[str, ast.expr]
) -> dict[str, ast.expr]:
    """The parameters a call hands a collection of strings, as that collection.

    ``_area_key(area_type, _ACTIVITY_LIMITS)`` hands ``table`` the keys of the
    caller's table, so the helper's ``key not in table`` is a closed set.
    """
    bound: dict[str, ast.expr] = {}
    for parameter, argument in handed.items():
        options = strings_of(argument, constants)
        if options:
            bound[parameter] = ast.Tuple(
                elts=[ast.Constant(value=option) for option in options],
                ctx=ast.Load(),
            )
    return bound


@functools.cache
def _literal_aliases() -> frozenset[str]:
    """Every name a phonometry module binds to a ``Literal`` alias."""
    names: set[str] = set()
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith("phonometry") or module is None:
            continue
        for name, value in vars(module).items():
            if typing.get_origin(value) is typing.Literal:
                names.add(name)
    return frozenset(names)


def _is_literal(annotation: str) -> bool:
    """Whether a parameter annotation, as written, is a ``Literal`` choice.

    Alone, in a union, or as what a collection holds (``Sequence[Field]``)
    and a mapping is keyed by.
    """
    for part in _members(annotation):
        if part.startswith("Literal[") or part in _literal_aliases():
            return True
        item = _item(part)
        if item is not None and _is_literal(item):
            return True
    return False


def _namespace(function: object, tree: ast.AST, module_name: str) -> dict[str, object]:
    """The names *function* can call: its module's, and those it imports itself.

    A wrapped function (a record's ``__post_init__`` is wrapped where the
    record takes ownership of its arrays) names what its own module imports,
    not what the wrapper's module does. A method also names its own class as
    ``self`` and ``cls``, so ``self._range_mask(weighting)`` is followed into
    the method it calls.
    """
    unwrapped = inspect.unwrap(function) if callable(function) else function
    names: dict[str, object] = {
        **getattr(unwrapped, "__globals__", {}),
        **_local_imports(tree, module_name),
    }
    owner = _owning_class(unwrapped, module_name)
    if owner is not None:
        names["self"] = owner
        names["cls"] = owner
    return names


def _owning_class(function: object, module_name: str) -> type | None:
    """The class *function* is defined in, read off its ``__qualname__``."""
    path = (getattr(function, "__qualname__", "") or "").split(".")[:-1]
    if not path or "<locals>" in path:
        return None
    owner: object = sys.modules.get(module_name)
    for part in path:
        owner = getattr(owner, part, None)
    return owner if inspect.isclass(owner) else None


def _held_class(owner: type, attribute: str) -> type | None:
    """The class the field *attribute* of *owner* is annotated with.

    ``database: ANPDatabase`` makes ``self.database.event_level`` the method
    of :class:`ANPDatabase`. An annotation written as text (``from
    __future__ import annotations``) is read in the module that wrote it; a
    union holding one class is that class.
    """
    for base in owner.__mro__:
        hint = inspect.get_annotations(base).get(attribute)
        if hint is None:
            continue
        if isinstance(hint, str):
            namespace = vars(sys.modules[base.__module__])
            candidates = [namespace.get(part.strip()) for part in hint.split("|")]
        else:
            candidates = [hint, *typing.get_args(hint)]
        classes = [
            candidate
            for candidate in candidates
            if inspect.isclass(candidate) and candidate is not type(None)
        ]
        return classes[0] if len(classes) == 1 else None
    return None


def _checks_received(
    callee: Callable[..., object],
    received: str,
    constants: dict[str, ast.expr],
    *,
    collection: bool,
) -> bool:
    """Whether *callee* types its parameter *received* ``Literal`` or checks
    it against a fixed set of strings itself.
    """
    annotation = expanded(
        str(inspect.signature(callee).parameters[received].annotation),
        callee.__module__,
    )
    if _is_literal(annotation):
        return True
    tree = _parsed(callee)
    return tree is not None and bool(
        code_evidence(tree, _the_name(received), constants, collection=collection)
    )


# PLR0913: the recursion carries what it has followed so far.
def passed_on_evidence(  # noqa: PLR0913
    function: object,
    name: str,
    depth: int = 0,
    seen: frozenset[str] = frozenset(),
    constants: dict[str, ast.expr] | None = None,
    *,
    target: Callable[[ast.expr], bool] | None = None,
    collection: bool = False,
) -> list[str]:
    """What a function that receives parameter *name* untouched says of it.

    Follows the parameter into each phonometry function it is handed to, and
    reports the first one that checks it against a fixed set of strings or
    already types it ``Literal``. *constants* are the names the function
    knows as collections of strings: its module's, and the tables its caller
    handed it. *target* reads the value in *function* some other way than by
    the parameter's name: ``self.<field>`` in a ``__post_init__`` that hands a
    record field to a helper. *collection* says the value is a collection of
    strings, whose items are the choice.
    """
    if depth >= _PASS_DEPTH:
        return []
    tree = _parsed(function)
    if tree is None:
        return []
    module_name = getattr(function, "__module__", "") or ""
    if constants is None:
        constants = _module_constants(sys.modules.get(module_name))
    namespace = _namespace(function, tree, module_name)
    matches = _following(tree, target or _the_name(name))
    spread = _spread_dicts(tree)
    known = {**constants, **_local_tables(tree, constants)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = _callee(node, namespace, module_name)
        if callee is None:
            continue
        handed = _arguments(node, callee, spread)
        received = next(
            (parameter for parameter, value in handed.items() if matches(value)),
            None,
        )
        key = f"{getattr(callee, '__qualname__', '')}.{received}"
        if received is None or key in seen:
            continue
        callee_constants = {
            **_module_constants(sys.modules.get(callee.__module__)),
            **_bound_tables(handed, known),
        }
        label = f"handed to {callee.__qualname__}({received})"
        if _checks_received(callee, received, callee_constants, collection=collection):
            return [label]
        deeper = passed_on_evidence(
            callee,
            received,
            depth + 1,
            seen | {key},
            callee_constants,
            collection=collection,
        )
        if deeper:
            return [f"{label}, {deeper[0]}"]
    return []


def documented_options(doc: str | None, name: str) -> tuple[str, ...]:
    """The quoted options the ``:param:`` or ``:ivar:`` text of *name* lists."""
    entry = re.search(
        rf":(?:param|ivar)\s+{re.escape(name)}:(.*?)(?=\n\s*:[a-z]+[\s:]|\Z)",
        inspect.cleandoc(doc or ""),
        re.DOTALL,
    )
    if entry is None:
        return ()
    options = [a or b for a, b in _QUOTED.findall(entry.group(1))]
    return tuple(dict.fromkeys(options))


def _public_modules() -> Iterator[ModuleType]:
    yield phonometry
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        yield importlib.import_module(info.name)


def _public_methods(cls: type) -> Iterator[tuple[str, object]]:
    """``(name, function)`` of every public method of *cls*, ``__init__``
    included, a class or static method by the function it wraps.

    A catalogue row's constructor takes its cells, which the catalogue
    contract holds to str (:data:`CATALOGUE_ROW`), so it is passed over.

    The namespace is read once, before the first method is handed out: what
    the caller does with a method may write into it, as reading the class's
    annotations does on Python 3.14 (``__annotate_func__`` and
    ``__annotations_cache__``), and a live view would then fail with
    ``RuntimeError: dictionary changed size during iteration``.
    """
    row = issubclass(cls, CatalogueRow)
    for attribute, member in tuple(vars(cls).items()):
        if attribute == "__init__" and row:
            continue
        if attribute.startswith("_") and attribute != "__init__":
            continue
        function = (
            member.__func__
            if isinstance(member, classmethod | staticmethod)
            else member
        )
        if inspect.isfunction(function):
            yield attribute, function


def _exported_targets(exported: str, obj: object) -> Iterator[tuple[str, object]]:
    """``(qualname, object)`` of what one exported name puts under the rule:
    a function, or a record and the public methods of a class.
    """
    if inspect.isfunction(obj):
        yield exported, obj
        return
    if not inspect.isclass(obj):
        return
    if dataclasses.is_dataclass(obj):
        yield exported, obj
    for attribute, function in _public_methods(obj):
        yield f"{exported}.{attribute}", function


def _targets() -> Iterator[tuple[str, str, object]]:
    """``(module, qualname, object)`` of every public callable and record.

    A public method a public class inherits from a base the package does not
    export (``plot`` of the layers of :mod:`~phonometry.materials.absorbers.layered`,
    defined on a private ``_DrawableLayer``) is a public method of each of
    them; it is read once, under the base that defines it.
    """
    seen: set[tuple[str, str]] = set()
    walked: set[int] = set()
    classes: dict[type, None] = {}
    for module in _public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            home = getattr(obj, "__module__", "") or ""
            if not home.startswith("phonometry"):
                continue
            if inspect.isclass(obj):
                classes[obj] = None
            for qualname, target in _exported_targets(exported, obj):
                if (home, qualname) not in seen:
                    seen.add((home, qualname))
                    walked.add(id(target))
                    yield home, qualname, target
    for cls in classes:
        for base, attribute, function in _inherited_methods(cls):
            if id(function) not in walked:
                walked.add(id(function))
                yield base.__module__, f"{base.__qualname__}.{attribute}", function


def _inherited_methods(cls: type) -> Iterator[tuple[type, str, object]]:
    """``(base, name, function)`` of every public method *cls* inherits from
    a base of the package, and does not define again itself.
    """
    row = issubclass(cls, CatalogueRow)
    for base in cls.__mro__[1:]:
        if not base.__module__.startswith("phonometry"):
            continue
        for attribute, function in _public_methods(base):
            if attribute == "__init__" and row:
                continue
            resolved = inspect.getattr_static(cls, attribute, None)
            if getattr(resolved, "__func__", resolved) is function:
                yield base, attribute, function


def _parsed(obj: object) -> ast.AST | None:
    try:
        return ast.parse(textwrap.dedent(inspect.getsource(obj)))  # type: ignore[arg-type]
    except (OSError, TypeError, SyntaxError):
        return None


def _annotation(value: object) -> str:
    return value if isinstance(value, str) else getattr(value, "__name__", str(value))


#: A quoted string inside an annotation (``Literal['top', 'left']``), whose
#: words are options, never names.
_QUOTED_TEXT = re.compile(r"""('[^']*'|"[^"]*")""")

#: A bare name in an annotation, not the attribute part of a dotted one.
_ANNOTATION_NAME = re.compile(r"(?<![\w.])[A-Za-z_]\w*")

#: How many aliases deep an annotation is spelled out.
_ALIAS_DEPTH = 4


def _reads_as_type(node: ast.expr) -> bool:
    """Whether a module-level value is a type alias's definition.

    A subscripted type (``Iterable[str]``, ``Literal[...]``), a union of
    types (``str | Iterable[str]``) or ``str`` itself.
    """
    if isinstance(node, ast.Subscript):
        return isinstance(node.value, ast.Name | ast.Attribute)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return all(
            _reads_as_type(side)
            or isinstance(side, ast.Name | ast.Attribute)
            or (isinstance(side, ast.Constant) and side.value is None)
            for side in (node.left, node.right)
        )
    return isinstance(node, ast.Name) and node.id == "str"


@functools.cache
def _imports_of(module_name: str) -> MappingProxyType[str, tuple[str, str]]:
    """What *module_name* imports from the package, by the name it gives each:
    the module imported from and the name there.

    A name the module also assigns is its own, as :func:`_constants_of` reads
    it, and is left out.
    """
    parsed = _parsed_module(module_name)
    if parsed is None:
        return MappingProxyType({})
    _, tree, package = parsed
    imports: dict[str, tuple[str, str]] = {}
    assigned: set[str] = set()
    for node in _module_statements(tree.body):
        if not isinstance(node, ast.ImportFrom):
            assigned.update(name for name, _ in _assigned(node))
            continue
        source = _import_source(node, package)
        if source is None:
            continue
        for alias in node.names:
            imports.setdefault(alias.asname or alias.name, (source, alias.name))
    return MappingProxyType(
        {name: where for name, where in imports.items() if name not in assigned}
    )


@functools.cache
def _type_aliases(module_name: str) -> MappingProxyType[str, tuple[str, str]]:
    """The type aliases *module_name* defines or imports, each with the module
    that writes it and its definition there.

    An imported alias is read where it is written: ``B = A | None`` imported
    alone names the ``A`` of its own module, which the importing module may
    not hold.
    """
    imports = _imports_of(module_name)
    aliases: dict[str, tuple[str, str]] = {}
    for name, value in _constants_of(module_name).items():
        if not _reads_as_type(value):
            continue
        where = imports.get(name)
        home = _type_aliases(where[0]).get(where[1]) if where else None
        aliases[name] = home or (module_name, ast.unparse(value))
    return MappingProxyType(aliases)


def expanded(annotation: str, module_name: str, depth: int = 0) -> str:
    """*annotation* with every type alias of its module spelled out.

    ``free_sides: _FreeSides | None`` with ``_FreeSides = Iterable[str]`` in
    the module takes any strings as surely as ``Iterable[str] | None``: the
    guard reads what the alias stands for, not its name. A ``Literal`` alias
    becomes its ``Literal[...]``, which stays a closed choice. An alias
    imported from another module of the package is spelled out there, through
    the aliases of that module.
    """
    if depth > _ALIAS_DEPTH:
        return annotation
    aliases = _type_aliases(module_name)

    def substitute(match: re.Match[str]) -> str:
        name = match.group(0)
        if name not in aliases:
            return name
        home, definition = aliases[name]
        # No parentheses: a union is read the same inside a union or a
        # subscript, and a member in parentheses would hide its own members.
        return expanded(definition, home, depth + 1)

    pieces = _QUOTED_TEXT.split(annotation)
    # Odd indices are the quoted strings the split kept; they stay as written.
    return "".join(
        piece if index % 2 else _ANNOTATION_NAME.sub(substitute, piece)
        for index, piece in enumerate(pieces)
    )


def _field_module(record: type, name: str) -> str:
    """The module that annotates field *name* of *record*, where its aliases live."""
    for owner in record.__mro__:
        if name in inspect.get_annotations(owner):
            return owner.__module__
    return record.__module__


def _field_of_self(name: str) -> Callable[[ast.expr], bool]:
    """A predicate for ``self.<name>``, the way a ``__post_init__`` reads a field."""

    def matches(node: ast.expr) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == name
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        )

    return matches


def _the_name(name: str) -> Callable[[ast.expr], bool]:
    """A predicate for the bare name of a parameter."""

    def matches(node: ast.expr) -> bool:
        return isinstance(node, ast.Name) and node.id == name

    return matches


def _field_read(name: str, *, own: bool) -> Callable[[ast.expr], bool]:
    """A predicate for ``<expr>.<name>``, a field read off a record.

    In a method of the record's own class (*own*) ``self.<name>`` is the
    field too; in another class's method it is that class's attribute, which
    only shares the name.
    """

    def matches(node: ast.expr) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == name
            and (
                own
                or not (isinstance(node.value, ast.Name) and node.value.id == "self")
            )
        )

    return matches


@functools.cache
def _module_functions(
    module_name: str,
) -> tuple[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef], ...]:
    """Every function and method *module_name* defines, with its class.

    Nested functions are included, each paired with the class whose body
    holds it, or the empty string at module level.
    """
    module = sys.modules.get(module_name)
    if module is None:
        return ()
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError, SyntaxError):
        return ()
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []

    def visit(node: ast.AST, owner: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, child.name)
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                found.append((owner, child))
                visit(child, owner)
            else:
                visit(child, owner)

    visit(tree, "")
    return tuple(found)


@functools.cache
def _attribute_readers(
    module_name: str,
) -> dict[str, tuple[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef], ...]]:
    """The functions of a module that read each attribute name, by the name."""
    readers: dict[str, list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]] = {}
    for owner, function in _module_functions(module_name):
        for attribute in {
            node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute)
        }:
            readers.setdefault(attribute, []).append((owner, function))
    return {attribute: tuple(found) for attribute, found in readers.items()}


def _functions_reading(
    module_name: str, name: str
) -> tuple[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef], ...]:
    """The functions of a module that read ``<expr>.<name>``, with their class."""
    return _attribute_readers(module_name).get(name, ())


def compared_in_module(
    record: type,
    name: str,
    constants: dict[str, ast.expr],
    *,
    collection: bool = False,
) -> list[str]:
    """What the record's module says of a field it reads as ``<expr>.<name>``.

    A field the record does not check when it is built is often checked where
    it is used: ``source.direction not in _SIDE_TRAVEL`` in the function that
    places a plane wave. Each function of the module the record is defined in
    is read on its own, so a local bound from the field in one function is not
    taken for another's, and ``self.<name>`` counts only in the record's own
    methods.
    """
    found: list[str] = []
    for owner, function in _functions_reading(record.__module__, name):
        is_field = _field_read(name, own=owner == record.__name__)
        found.extend(
            f"{evidence} in {function.name}()"
            for evidence in code_evidence(
                function, is_field, constants, collection=collection
            )
        )
    return list(dict.fromkeys(found))


def _field_evidence(
    record: type,
    name: str,
    constants: dict[str, ast.expr],
    *,
    collection: bool,
) -> list[str]:
    """What the code says of record field *name*, where the record is built or used.

    The ``__post_init__`` that checks it, the helper that ``__post_init__``
    hands ``self.<name>`` to (followed as a parameter is), and the functions of
    the record's module that compare ``<expr>.<name>`` with strings.
    """
    check = vars(record).get("__post_init__")
    tree = _parsed(check) if check is not None else None
    if tree is not None:
        evidence = code_evidence(
            tree, _field_of_self(name), constants, collection=collection
        )
        if evidence:
            return evidence
        evidence = passed_on_evidence(
            check,
            name,
            target=_field_of_self(name),
            collection=collection,
        )
        if evidence:
            return evidence
    return compared_in_module(record, name, constants, collection=collection)


def string_choices() -> Iterator[Choice]:
    """Every public string parameter or field, with what says it is closed."""
    for home, qualname, obj in _targets():
        constants = _module_constants(sys.modules.get(home))
        if inspect.isclass(obj):
            if issubclass(obj, CatalogueRow):
                continue
            for field in dataclasses.fields(obj):  # type: ignore[arg-type]
                annotation = _annotation(field.type)
                read = expanded(annotation, _field_module(obj, field.name))
                collection = takes_any_strings(read)
                nested = takes_nested_strings(read)
                if not (collection or nested or takes_any_string(read)):
                    continue
                name = field.name
                evidence = (
                    _field_evidence(obj, name, constants, collection=collection)
                    if collection or takes_any_string(read)
                    else []
                )
                if nested:
                    evidence.append(NESTED)
                options = documented_options(obj.__doc__, name)
                if len(options) >= 2:
                    evidence.append("documented options " + ", ".join(options[:6]))
                evidence.extend(enum_beside(annotation, sys.modules.get(home)))
                yield Choice(home, qualname, name, annotation, tuple(evidence))
            continue
        try:
            signature = inspect.signature(obj)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        tree = _parsed(obj)
        for parameter in signature.parameters.values():
            if parameter.name in {"self", "cls"}:
                continue
            annotation = _annotation(parameter.annotation)
            read = expanded(annotation, home)
            collection = takes_any_strings(read)
            # A constructor the dataclass machinery writes has no source; the
            # record's own field is the one read for a nested string.
            nested = tree is not None and takes_nested_strings(read)
            if not (collection or nested or takes_any_string(read)):
                continue
            name = parameter.name
            evidence = []
            if collection or takes_any_string(read):
                if tree is not None:
                    evidence = code_evidence(
                        tree, _the_name(name), constants, collection=collection
                    )
                if not evidence:
                    evidence = passed_on_evidence(obj, name, collection=collection)
            if nested:
                evidence.append(NESTED)
            options = documented_options(getattr(obj, "__doc__", None), name)
            if len(options) >= 2:
                evidence.append("documented options " + ", ".join(options[:6]))
            evidence.extend(enum_beside(annotation, sys.modules.get(home)))
            yield Choice(home, qualname, name, annotation, tuple(evidence))


#: How many calls deep a ``Literal`` choice is followed into the functions it
#: is handed to, looking for a clean-up before its check.
_SPELLING_DEPTH = 6


class _Reading(NamedTuple):
    """How one function reads a choice: where it cleans the text up, and
    where it checks the text as the caller wrote it.

    *folds* pairs where each clean-up starts with what it does; *checks*
    holds where each check of the text as written ends. Positions are
    ``(line, column)`` in the function's own source.
    """

    folds: tuple[tuple[tuple[int, int], str], ...]
    checks: tuple[tuple[int, int], ...]


def _start(node: ast.AST) -> tuple[int, int]:
    """Where *node* starts, ``(line, column)``."""
    line: int = getattr(node, "lineno", 0)
    column: int = getattr(node, "col_offset", 0)
    return line, column


def _end(node: ast.AST) -> tuple[int, int]:
    """Where *node* ends, ``(line, column)``, or where it starts if unknown."""
    line: int | None = getattr(node, "end_lineno", None)
    column: int | None = getattr(node, "end_col_offset", None)
    if line is None or column is None:
        return _start(node)
    return line, column


def _cleaned_up(
    node: ast.Call,
    matches: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
    options: frozenset[str],
) -> str | None:
    """What a call does to the caller's text, when it cleans it up or maps it.

    A method that only cleans up a text (``mode.lower()``,
    ``str(mode).strip()``, ``_require_str(mode).upper()`` on what a private
    helper hands back), ``str(mode)``, which makes a text of any value (``2``
    for ``"2"``), and an alias map that hands back what it does not know
    (``ALIASES.get(mode, mode)``). An alias map whose every key is one of the
    *options* the ``Literal`` lists on purpose (``{"J_LFC": "J_LF"}``) maps a
    spelling the caller was offered, and accepts nothing more.
    """
    function = node.func
    if (
        isinstance(function, ast.Attribute)
        and function.attr in _NORMALISERS
        and _derived_from(function.value, matches)
    ):
        return f".{function.attr}()"
    if (
        isinstance(function, ast.Name)
        and function.id == "str"
        and len(node.args) == 1
        and matches(node.args[0])
    ):
        return "str()"
    if (
        isinstance(function, ast.Attribute)
        and function.attr == "get"
        and len(node.args) == 2
        and all(matches(argument) for argument in node.args)
    ):
        keys = strings_of(function.value, constants)
        if keys and set(keys) <= options:
            return None
        return "an alias map .get(text, text)"
    return None


def _raises(body: list[ast.stmt]) -> bool:
    return any(
        isinstance(node, ast.Raise)
        for statement in body
        for node in ast.walk(statement)
    )


def _unlisted_items(
    tree: ast.AST, is_raw: Callable[[ast.expr], bool], constants: dict[str, ast.expr]
) -> dict[str, ast.expr]:
    """The locals bound to what a collection holds beyond a set of strings,
    each with the options it is taken against.

    ``extra = set(levels) - set(OPTIONS)`` or ``set(levels).difference(OPTIONS)``:
    a collection whose leftover is refused is checked as written, as a whole.
    """
    names: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        against: ast.expr | None = None
        if (
            isinstance(value, ast.BinOp)
            and isinstance(value.op, ast.Sub)
            and is_raw(_held(value.left))
        ):
            against = value.right
        elif (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "difference"
            and bool(value.args)
            and is_raw(_held(value.func.value))
        ):
            against = value.args[0]
        if against is not None and strings_of(against, constants):
            names.update(
                (target.id, against)
                for target in node.targets
                if isinstance(target, ast.Name)
            )
    return names


class _Refusal(NamedTuple):
    """A test that refuses the text as written: where it starts and ends, and
    the options it lets through.
    """

    start: tuple[int, int]
    end: tuple[int, int]
    against: ast.expr


def _refused_unless_listed(
    node: ast.If,
    is_raw: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
    unlisted: dict[str, ast.expr],
) -> list[_Refusal]:
    """The tests of *node* that refuse the text as written.

    ``if text not in OPTIONS: raise ...``; for a collection, ``if not
    set(levels) <= OPTIONS: raise ...`` or ``if extra: raise ...`` with
    ``extra`` bound to what it holds beyond the options (:func:`_unlisted_items`).
    Each comes with the options it is held against, which the caller holds
    to the ``Literal`` (:func:`_wider_than_the_literal`).
    """
    if not _raises(node.body):
        return []
    found: list[_Refusal] = []
    for part in ast.walk(node.test):
        if isinstance(part, ast.Name) and part.id in unlisted:
            found.append(
                _Refusal(_start(node.test), _end(node.test), unlisted[part.id])
            )
        if not isinstance(part, ast.Compare):
            continue
        left, operator, right = part.left, part.ops[0], part.comparators[0]
        if is_raw(left) and isinstance(operator, ast.NotIn):
            if strings_of(right, constants):
                found.append(_Refusal(_start(part), _end(part), right))
        elif _subset_evidence(left, operator, right, is_raw, constants):
            options = right if isinstance(operator, ast.LtE | ast.Lt) else left
            found.append(_Refusal(_start(part), _end(part), options))
    return found


def _strings_picked(
    node: ast.expr | None, constants: Mapping[str, ast.expr]
) -> list[tuple[str, ...]]:
    """Each set of strings *node* may hold when the code runs.

    One set for a set written out (:func:`strings_of`); one per branch of a
    conditional expression, and one per table of a table of tables picked by
    a key the code works out (``_FIELD_QUANTITIES[type(result)]``), where
    :func:`strings_of` reads them all together.
    """
    for _ in range(_STRINGS_DEPTH):
        if isinstance(node, ast.Name) and node.id in constants:
            node = constants[node.id]
        elif isinstance(node, ast.Call) and node.args:
            node = node.args[0]
        else:
            break
    if isinstance(node, ast.IfExp):
        branches = [
            *_strings_picked(node.body, constants),
            *_strings_picked(node.orelse, constants),
        ]
        if branches:
            return branches
    if isinstance(node, ast.Subscript):
        table = _dict_display(node.value, constants, 0)
        rows = [strings_of(value, constants) for value in table.values] if table else []
        if rows and all(rows):
            return rows
    held = strings_of(node, constants)
    return [held] if held else []


def _wider_than_the_literal(
    against: ast.expr | None,
    constants: Mapping[str, ast.expr],
    options: frozenset[str],
) -> tuple[str, ...]:
    """The strings a check of the text as written lets through that the
    ``Literal``'s *options* do not list, none when the options are unknown.

    A check against one of several sets picked when the code runs
    (:func:`_strings_picked`) lets through what the closest of them holds
    beyond the options: none, when one of them lists only options.
    """
    if not options:
        return ()
    extras = [
        tuple(sorted(set(held) - options))
        for held in _strings_picked(against, constants)
    ]
    return min(extras, key=len, default=())


def _cleans_up_first(reading: _Reading) -> list[str]:
    """The clean-ups a reading makes before its first check of the text as
    written, or all of them when it never checks the text as written.
    """
    first = min(reading.checks, default=None)
    return list(
        dict.fromkeys(
            label
            for start, label in sorted(reading.folds)
            if first is None or start < first
        )
    )


class _Reader(NamedTuple):
    """What one function's reading of a choice needs, carried down its calls."""

    is_raw: Callable[[ast.expr], bool]
    matches: Callable[[ast.expr], bool]
    namespace: dict[str, object]
    module_name: str
    constants: dict[str, ast.expr]
    spread: dict[str, dict[str, ast.expr]]
    options: frozenset[str]
    collection: bool
    depth: int


# PLR0913: the recursion carries what it has followed so far.
def _spelling(  # noqa: PLR0913
    tree: ast.AST,
    target: Callable[[ast.expr], bool],
    namespace: dict[str, object],
    module_name: str,
    constants: dict[str, ast.expr],
    *,
    options: frozenset[str],
    collection: bool,
    depth: int,
) -> _Reading:
    """How *tree* reads the choice *target* picks out, among *options*.

    The text as the caller wrote it is the target itself and, for a
    collection, each of its items; a clean-up is read off the text as written
    and off the locals bound from it (:func:`_following`). A function the
    text is handed to is followed: a clean-up inside it, before its own check,
    is a clean-up where the call is made, and a check inside it, before any
    clean-up, is a check where the call ends.
    """
    constants = {**constants, **_local_tables(tree, constants)}
    items = _item_names(tree, target) if collection else set()

    def is_raw(node: ast.expr) -> bool:
        return target(node) or (isinstance(node, ast.Name) and node.id in items)

    reader = _Reader(
        is_raw=is_raw,
        matches=_following(tree, is_raw),
        namespace=namespace,
        module_name=module_name,
        constants=constants,
        spread=_spread_dicts(tree),
        options=options,
        collection=collection,
        depth=depth,
    )
    unlisted = _unlisted_items(tree, is_raw, constants) if collection else {}
    folds: list[tuple[tuple[int, int], str]] = []
    checks: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            for refusal in _refused_unless_listed(node, is_raw, constants, unlisted):
                checks.append(refusal.end)
                wider = _wider_than_the_literal(refusal.against, constants, options)
                if wider:
                    label = f"options wider than the Literal {wider}"
                    folds.append((refusal.start, label))
        elif isinstance(node, ast.Call):
            _read_call(node, reader, folds, checks)
    return _Reading(tuple(folds), tuple(checks))


def _read_call(
    node: ast.Call,
    reader: _Reader,
    folds: list[tuple[tuple[int, int], str]],
    checks: list[tuple[int, int]],
) -> None:
    """Add what one call does to the choice: a clean-up, a check as written,
    or either of those inside a function the choice is handed to.
    """
    label = _cleaned_up(node, reader.matches, reader.constants, reader.options)
    if label is not None:
        folds.append((_start(node), label))
    if node.args and reader.is_raw(node.args[0]) and _call_name(node) in VALIDATORS:
        checks.append(_end(node))
        wider = _beyond_the_literal(node, reader)
        if wider:
            folds.append((_start(node), f"options wider than the Literal {wider}"))
    callee = _callee(node, reader.namespace, reader.module_name)
    if callee is not None and reader.depth < _SPELLING_DEPTH:
        _read_handed_on(node, callee, reader, folds, checks)


def _beyond_the_literal(node: ast.Call, reader: _Reader) -> tuple[str, ...]:
    """The options a check of the text as written takes that the ``Literal``
    does not list.

    ``require_choice(text, "quantity", (*_SINGLE, *_ALIASES))`` reads the text
    as the caller wrote it, and still takes an alias of the table's own that
    no option spells: the check holds the text to the ``Literal`` only when
    its options are among the ones the ``Literal`` lists. A membership or
    subset test is held the same way (:func:`_refused_unless_listed`).
    """
    argument = node.args[2] if len(node.args) > 2 else None
    for keyword in node.keywords:
        if keyword.arg == "options":
            argument = keyword.value
    return _wider_than_the_literal(argument, reader.constants, reader.options)


def _read_handed_on(
    node: ast.Call,
    callee: FunctionType,
    reader: _Reader,
    folds: list[tuple[tuple[int, int], str]],
    checks: list[tuple[int, int]],
) -> None:
    """Add what *callee* does with the choice a call hands it."""
    for parameter, value in _arguments(node, callee, reader.spread).items():
        if not reader.matches(value):
            continue
        inner = _received(
            callee,
            parameter,
            options=reader.options,
            collection=reader.collection,
            depth=reader.depth + 1,
        )
        first = _cleans_up_first(inner)
        if first:
            label = f"handed to {callee.__qualname__}({parameter}), {first[0]}"
            folds.append((_start(node), label))
        elif inner.checks and reader.is_raw(value):
            checks.append(_end(node))


@functools.cache
def _received(
    function: Callable[..., object],
    name: str,
    *,
    options: frozenset[str],
    collection: bool,
    depth: int,
) -> _Reading:
    """How *function* reads the choice among *options* it receives as
    parameter *name*.
    """
    tree = _parsed(function)
    if tree is None:
        return _Reading((), ())
    module_name = getattr(function, "__module__", "") or ""
    return _spelling(
        tree,
        _the_name(name),
        _namespace(function, tree, module_name),
        module_name,
        _module_constants(sys.modules.get(module_name)),
        options=options,
        collection=collection,
        depth=depth,
    )


def _literal_options(annotation: str) -> frozenset[str]:
    """The options the ``Literal`` of an annotation, read through its
    aliases (:func:`expanded`), lists: every quoted text in it, read as the
    string it spells, so an escape written in the annotation is the
    character it stands for (a tab, not a backslash and a ``t``).
    """
    return frozenset(_spelled(text) for text in _QUOTED_TEXT.findall(annotation))


def _spelled(quoted: str) -> str:
    """The string a quoted text of an annotation spells, escapes read."""
    try:
        text = ast.literal_eval(quoted)
    except (SyntaxError, ValueError):
        return quoted[1:-1]
    return text if isinstance(text, str) else quoted[1:-1]


def _literal_shape(annotation: str) -> tuple[bool, bool]:
    """Whether an annotation is a ``Literal`` choice, and whether its
    ``Literal`` is what a collection holds or a mapping is keyed by.
    """
    collection = any(
        (item := _item(member)) is not None and _is_literal(item)
        for member in _members(annotation)
    )
    return _is_literal(annotation), collection


def _post_init(record: type) -> Callable[..., object] | None:
    """The ``__post_init__`` a record runs, its own or the nearest base's."""
    for owner in record.__mro__:
        check = vars(owner).get("__post_init__")
        if check is not None:
            unwrapped: Callable[..., object] = inspect.unwrap(check)
            return unwrapped
    return None


def _field_spelling(
    record: type,
    name: str,
    constants: dict[str, ast.expr],
    *,
    options: frozenset[str],
    collection: bool,
) -> list[str]:
    """The clean-ups the code makes of record field *name* before its check.

    A field the record's ``__post_init__`` checks as written is closed when
    the record is built, so a later clean-up accepts nothing more. A field it
    does not check is read wherever its module reads ``<expr>.<name>``.
    """
    check = _post_init(record)
    tree = _parsed(check) if check is not None else None
    if check is not None and tree is not None:
        module_name = check.__module__
        reading = _spelling(
            tree,
            _field_of_self(name),
            _namespace(check, tree, module_name),
            module_name,
            _module_constants(sys.modules.get(module_name)),
            options=options,
            collection=collection,
            depth=0,
        )
        first = _cleans_up_first(reading)
        if first or reading.checks:
            return first
    module = sys.modules.get(record.__module__)
    namespace = dict(vars(module)) if module is not None else {}
    found: list[str] = []
    for owner, function in _functions_reading(record.__module__, name):
        reading = _spelling(
            function,
            _field_read(name, own=owner == record.__name__),
            namespace,
            record.__module__,
            constants,
            options=options,
            collection=collection,
            depth=0,
        )
        found.extend(
            f"{label} in {function.name}()" for label in _cleans_up_first(reading)
        )
    return list(dict.fromkeys(found))


def cleaned_up_choices() -> Iterator[Choice]:
    """Every public ``Literal`` choice the code cleans up before it checks it.

    A parameter or a record field typed with a ``Literal`` of its options (an
    alias of one, a union holding one, or a collection or mapping of one)
    promises one spelling of each option. The code that reads it must check
    the text as the caller wrote it (``require_choice``, ``check_language``,
    ``check_engine``, or ``if text not in OPTIONS: raise``) before it folds
    the case, strips the spaces, makes a text of another value with
    ``str()`` or maps an alias it does not list (``ALIASES.get(text,
    text)``), in its own body or in a function it hands the text to, and the
    check must hold no option the ``Literal`` does not list; otherwise ``"a"``
    passes for ``"A"`` when the call runs while a type checker refuses it.
    A method is followed into the methods of its own class it calls
    (``self._range_mask(weighting)``) and into those of an object it holds
    (``self.database.event_level(...)``). This is rule A45.
    """
    for home, qualname, obj in _targets():
        if inspect.isclass(obj):
            if not issubclass(obj, CatalogueRow):
                yield from _cleaned_up_fields(home, qualname, obj)
        else:
            yield from _cleaned_up_parameters(home, qualname, obj)


def _cleaned_up_fields(home: str, qualname: str, record: type) -> Iterator[Choice]:
    """The ``Literal`` fields of a public record its code cleans up first."""
    constants = _module_constants(sys.modules.get(home))
    for field in dataclasses.fields(record):
        annotation = _annotation(field.type)
        read = expanded(annotation, _field_module(record, field.name))
        literal, collection = _literal_shape(read)
        if not literal:
            continue
        evidence = _field_spelling(
            record,
            field.name,
            constants,
            options=_literal_options(read),
            collection=collection,
        )
        if evidence:
            yield Choice(home, qualname, field.name, annotation, tuple(evidence))


def _cleaned_up_parameters(
    home: str, qualname: str, function: object
) -> Iterator[Choice]:
    """The ``Literal`` parameters of a public function its code cleans up first."""
    if not callable(function) or _parsed(function) is None:
        return
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return
    for parameter in signature.parameters.values():
        annotation = _annotation(parameter.annotation)
        read = expanded(annotation, home)
        literal, collection = _literal_shape(read)
        if not literal:
            continue
        reading = _received(
            function,
            parameter.name,
            options=_literal_options(read),
            collection=collection,
            depth=0,
        )
        evidence = _cleans_up_first(reading)
        if evidence:
            yield Choice(home, qualname, parameter.name, annotation, tuple(evidence))


# ---------------------------------------------------------------------------
# A vocabulary written down twice: a table keyed by text, a record field of
# text, and a choice that is not checked on every path
# ---------------------------------------------------------------------------

#: The script whose ``_COVERED`` names the files the GPU parity lock holds.
GPU_PARITY_SCRIPT = pathlib.Path(__file__).resolve().parent / "gpu_parity.py"

#: Why the modules of those files are exempt as a whole.
GPU_PARITY_REASON = (
    "GPU-parity batch: an edit to a file scripts/gpu_parity.py fingerprints "
    "invalidates gpu-parity.lock, so the choices of those files are typed and "
    "checked in one batch of their own, with the GPU run that records the "
    "lock again"
)


def gpu_parity_modules(
    script: pathlib.Path = GPU_PARITY_SCRIPT,
) -> MappingProxyType[str, str]:
    """The package modules the GPU parity lock holds, each with the reason.

    Read from ``_COVERED`` in the source of *script*, so the exemption follows
    the files the lock fingerprints and cannot drift from them; each entry is
    a path joined onto the repository root with ``/``, and the ones under
    ``src/`` are modules of the package.
    """
    if not script.is_file():
        return MappingProxyType({})
    tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    paths: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_COVERED"
            for target in node.targets
        ):
            paths = [
                element.right.value
                for element in getattr(node.value, "elts", [])
                if isinstance(element, ast.BinOp)
                and isinstance(element.right, ast.Constant)
                and isinstance(element.right.value, str)
            ]
    modules: dict[str, str] = {}
    for path in paths:
        parts = pathlib.PurePosixPath(path).with_suffix("").parts
        if parts[:1] == ("src",) and len(parts) > 1:
            modules[".".join(parts[1:])] = GPU_PARITY_REASON
    return MappingProxyType(modules)


#: The modules of the files the GPU parity lock holds, keyed by module.
GPU_PARITY = gpu_parity_modules()

#: A published table keyed by text, or a tuple of texts, whose keys equal a
#: vocabulary of the package by coincidence, keyed by ``(module, name)``, with
#: the reason. An entry that matches nothing fails.
OPEN_TABLES: dict[tuple[str, str], str] = {
    ("phonometry.environment.assessment.soundscape", "METHOD_A_SCALES[...].items"): (
        "the rows a scale of ISO/TS 12913-2 rates, as the figure prints them: "
        "sound sources described in prose for part 1, the eight attributes "
        "for part 2, two kinds of row in one field"
    ),
}

_MAPPING_ORIGINS = frozenset({"Mapping", "MappingProxyType", "dict", "MutableMapping"})
#: The annotations of a collection that type its items with one argument, as
#: a published tuple or frozenset may be annotated.
_ITEM_ORIGINS = frozenset(
    {
        "AbstractSet",
        "Collection",
        "Container",
        "FrozenSet",
        "Iterable",
        "Reversible",
        "Sequence",
        "Set",
        "frozenset",
    }
)


def _package(module_name: str) -> str:
    """The top-level package of a module: ``building`` for
    ``phonometry.building.measurement.ratings``.
    """
    parts = module_name.split(".")
    return parts[1] if len(parts) > 1 else parts[0]


@functools.cache
def _vocabularies() -> tuple[tuple[str, str, frozenset[str]], ...]:
    """Every vocabulary of text the package writes: ``(module, name, options)``.

    The ``Literal`` aliases of each module, and every ``Literal`` of texts an
    annotation spells in place (named ``Literal@<line>``), so a table keyed by
    the options of an inline ``Literal`` is found as surely as one keyed by an
    alias.
    """
    found: list[tuple[str, str, frozenset[str]]] = []
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith("phonometry") or module is None:
            continue
        for name, value in vars(module).items():
            if typing.get_origin(value) is typing.Literal:
                options = typing.get_args(value)
                if options and all(isinstance(option, str) for option in options):
                    found.append((module_name, name, frozenset(options)))
        try:
            tree = ast.parse(inspect.getsource(module))
        except (OSError, TypeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Subscript)
                and (
                    (isinstance(node.value, ast.Name) and node.value.id == "Literal")
                    or (
                        isinstance(node.value, ast.Attribute)
                        and node.value.attr == "Literal"
                    )
                )
            ):
                continue
            elements = (
                node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            )
            if elements and all(
                isinstance(element, ast.Constant) and isinstance(element.value, str)
                for element in elements
            ):
                written = frozenset(
                    element.value
                    for element in elements
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                )
                found.append((module_name, f"Literal@{node.lineno}", written))
    return tuple(found)


def _vocabulary_of(texts: frozenset[str], module_name: str) -> str | None:
    """The vocabulary *texts* spell, read where a table of *module_name* is.

    Equal to a vocabulary of the same top-level package, or a part of at least
    two options of one its own module writes.
    """
    package = _package(module_name)
    for home, name, options in _vocabularies():
        if options == texts and _package(home) == package:
            return f"the options of {home}.{name}"
    # One text is no vocabulary: a part has to hold two options at least.
    if len(texts) >= 2:  # noqa: PLR2004
        for home, name, options in _vocabularies():
            if home == module_name and texts < options:
                return f"part of the options of {home}.{name}"
    return None


#: The qualifiers an annotation of a constant may wrap its type in, which say
#: nothing of what the type holds: ``Final[Mapping[str, float]]`` is keyed by
#: any text as surely as ``Mapping[str, float]``.
_QUALIFIERS = frozenset({"Annotated", "ClassVar", "Final"})


def _annotation_node(
    annotation: object, module_name: str | None = None
) -> ast.expr | None:
    """*annotation* parsed, with the aliases of *module_name* spelled out
    (``_Table = Mapping[str, float]`` reads as what it stands for) and the
    qualifiers around it taken off.
    """
    if annotation is None:
        return None
    text = annotation if isinstance(annotation, str) else _annotation(annotation)
    if module_name is not None:
        text = expanded(text, module_name)
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return None
    return _unqualified(node)


def _unqualified(node: ast.expr) -> ast.expr:
    """*node* without the ``Final``, ``ClassVar`` or ``Annotated`` around it."""
    while isinstance(node, ast.Subscript):
        origin = node.value
        name = (
            origin.attr
            if isinstance(origin, ast.Attribute)
            else getattr(origin, "id", "")
        )
        if name not in _QUALIFIERS:
            break
        inner = node.slice
        node = inner.elts[0] if isinstance(inner, ast.Tuple) and inner.elts else inner
    return node


def _origin_and_arguments(node: ast.expr | None) -> tuple[str, list[ast.expr]]:
    if node is None:
        return "", []
    node = _unqualified(node)
    if not isinstance(node, ast.Subscript):
        return "", []
    origin = node.value
    name = (
        origin.attr if isinstance(origin, ast.Attribute) else getattr(origin, "id", "")
    )
    arguments = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
    return name, list(arguments)


def _takes_text(node: ast.expr | None, module_name: str) -> bool:
    """Whether a key or item annotation lets any text through (or is absent)."""
    if node is None:
        return True
    return takes_any_string(expanded(ast.unparse(node), module_name))


def _item_types(
    origin: str, arguments: list[ast.expr], count: int
) -> list[ast.expr | None] | None:
    """The annotation of each of *count* items of a tuple or a frozenset.

    ``tuple[X, ...]`` and ``Sequence[X]`` give every item ``X``; ``tuple[X,
    Y]`` gives each item its own; no annotation, or one that says nothing of
    the items, gives none (any text, as a type checker reads it). ``None``
    for an annotation of a different length, which is not this value's.
    """
    if origin in {"tuple", "Tuple"}:
        if (
            len(arguments) == 2  # noqa: PLR2004
            and isinstance(arguments[1], ast.Constant)
            and arguments[1].value is Ellipsis
        ):
            return [arguments[0]] * count
        return list(arguments) if len(arguments) == count else None
    if origin in _ITEM_ORIGINS and len(arguments) == 1:
        return [arguments[0]] * count
    return [None] * count


def _texts_by_position(
    rows: list[tuple[object, ...]],
    types: list[ast.expr | None] | None,
    module_name: str,
    path: str,
) -> Iterator[tuple[str, frozenset[str]]]:
    """The texts each position of a set of tuples holds where its annotation
    lets any text in: each part of a key ``("group_1", "rigid")`` typed
    ``tuple[str, str]`` is a vocabulary of its own.
    """
    if types is None:
        return
    for index, held in enumerate(types):
        texts = [row[index] for row in rows]
        if all(isinstance(text, str) for text in texts) and _takes_text(
            held, module_name
        ):
            yield f"{path}<{index}>", frozenset(str(text) for text in texts)


def _keyed_by_text(
    value: object, annotation: ast.expr | None, module_name: str, path: str, depth: int
) -> Iterator[tuple[str, frozenset[str]]]:
    """Each key set or item set of a published value its annotation lets any
    text into, at any depth.

    The keys of a mapping, each part of a mapping's tuple keys, the items of
    a tuple or a frozenset, the parts of its tuple items, and the same in each
    field of a record the value holds, read through the record's own
    annotations. An annotation that does not say what a key or an item is
    (none, ``Any``, or one the guard cannot read) lets any text in, as it does
    for a type checker.
    """
    if depth > _TABLE_DEPTH + 2:
        return
    origin, arguments = _origin_and_arguments(annotation)
    if isinstance(value, collections.abc.Mapping):
        mapping = origin in _MAPPING_ORIGINS
        key_type = arguments[0] if mapping and arguments else None
        value_type = arguments[1] if mapping and len(arguments) > 1 else None
        keys = list(value)
        if keys and all(isinstance(key, str) for key in keys):
            if _takes_text(key_type, module_name):
                yield path, frozenset(keys)
        elif keys and all(isinstance(key, tuple) for key in keys):
            widths = {len(key) for key in keys}
            if len(widths) == 1:
                key_origin, key_arguments = _origin_and_arguments(key_type)
                yield from _texts_by_position(
                    keys,
                    _item_types(key_origin, key_arguments, widths.pop()),
                    module_name,
                    f"{path}[key]",
                )
        seen: set[int] = set()
        for held in value.values():
            if id(held) not in seen:
                seen.add(id(held))
                yield from _keyed_by_text(
                    held, value_type, module_name, f"{path}[...]", depth + 1
                )
    elif isinstance(value, tuple | frozenset):
        items = list(value)
        types = _item_types(origin, arguments, len(items))
        if items and all(isinstance(item, str) for item in items):
            if types is not None and any(
                _takes_text(held, module_name) for held in types
            ):
                yield path, frozenset(items)
        elif items and all(isinstance(item, tuple) for item in items):
            widths = {len(item) for item in items}
            item_type = types[0] if types else None
            if len(widths) == 1 and (types is None or len(set(map(id, types))) == 1):
                row_origin, row_arguments = _origin_and_arguments(item_type)
                yield from _texts_by_position(
                    items,
                    _item_types(row_origin, row_arguments, widths.pop()),
                    module_name,
                    f"{path}[...]",
                )
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        record = type(value)
        for field in dataclasses.fields(record):
            home = _field_module(record, field.name)
            yield from _keyed_by_text(
                getattr(value, field.name, None),
                _annotation_node(field.type, home),
                home,
                f"{path}.{field.name}",
                depth + 1,
            )


def _home_of_constant(
    module: ModuleType, name: str, value: object
) -> tuple[str, object]:
    """The module that annotates a published constant, and its annotation."""
    holders: list[str] = []
    for module_name, other in list(sys.modules.items()):
        if not module_name.startswith("phonometry") or other is None:
            continue
        if getattr(other, name, None) is not value:
            continue
        annotations = getattr(other, "__annotations__", {}) or {}
        if name in annotations:
            return module_name, annotations[name]
        holders.append(module_name)
    holders.sort(key=lambda held: -held.count("."))
    return (holders[0] if holders else module.__name__), None


def vocabulary_tables() -> Iterator[Choice]:
    """Every published table keyed by text whose keys are a vocabulary.

    A published ``Mapping[str, ...]``, ``tuple[str, ...]`` or ``frozenset[str]``
    (or one with no annotation, which a type checker reads as keyed by any
    text), at any depth of the table, whose keys or items are the options of
    a ``Literal`` of its top-level package, or part of a ``Literal`` of its own
    module, is the vocabulary written twice: a caller indexing it with a
    misspelling meets a ``KeyError`` when the call runs, where a table keyed
    by the ``Literal`` is refused by ``mypy``. This is rule A21.
    """
    seen: set[tuple[str, str]] = set()
    for module in _public_modules():
        for name in getattr(module, "__all__", ()):
            value = getattr(module, name, None)
            if not (
                isinstance(value, collections.abc.Mapping | tuple | frozenset)
                or (dataclasses.is_dataclass(value) and not isinstance(value, type))
            ):
                continue
            home, annotation = _home_of_constant(module, name, value)
            if (home, name) in seen or home in GPU_PARITY:
                continue
            seen.add((home, name))
            for path, texts in _keyed_by_text(
                value, _annotation_node(annotation, home), home, "", 0
            ):
                vocabulary = _vocabulary_of(texts, home)
                if vocabulary is not None:
                    yield Choice(
                        home,
                        f"{name}{path}",
                        "keys",
                        str(annotation),
                        (f"its keys are {vocabulary}",),
                    )


@functools.cache
def _construction_sites() -> MappingProxyType[
    str, tuple[tuple[str, ast.AST | None, ast.Call], ...]
]:
    """Every call in the package by the name it calls: ``(module, function, call)``.

    *function* is the function the call is written in, or ``None`` at module
    level, so an argument is read where it is written.
    """
    sites: dict[str, list[tuple[str, ast.AST | None, ast.Call]]] = {}
    root = pathlib.Path(phonometry.__file__).parent
    for path in sorted(root.rglob("*.py")):
        parts = list(path.relative_to(root.parent).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_name = ".".join(parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))

        def visit(
            node: ast.AST, function: ast.AST | None, module_name: str = module_name
        ) -> None:
            for child in ast.iter_child_nodes(node):
                inner = (
                    child
                    if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                    else function
                )
                if isinstance(child, ast.Call):
                    called = child.func
                    name = (
                        called.id
                        if isinstance(called, ast.Name)
                        else called.attr
                        if isinstance(called, ast.Attribute)
                        else None
                    )
                    if name is not None:
                        sites.setdefault(name, []).append(
                            (module_name, function, child)
                        )
                visit(child, inner)

        visit(tree, None)
    return MappingProxyType({name: tuple(found) for name, found in sites.items()})


#: How deep a value is followed back to where it is written: through locals,
#: the callers of a private helper and the fields of the records it is read
#: off.
_SOURCE_DEPTH = 4


class _Source(NamedTuple):
    """What a value is made of: fixed texts, a ``Literal``, or something open."""

    kind: str  # "texts", "literal", "none" or "open"
    texts: frozenset[str]


_OPEN_SOURCE = _Source("open", frozenset())


def _merged(sources: list[_Source]) -> _Source:
    texts: set[str] = set()
    kinds: set[str] = set()
    for source in sources:
        if source.kind == "open":
            return _OPEN_SOURCE
        if source.kind != "none":
            kinds.add(source.kind)
            texts |= source.texts
    if not kinds:
        return _Source("none", frozenset())
    return _Source("literal" if "literal" in kinds else "texts", frozenset(texts))


def _module_object(module_name: str) -> ModuleType | None:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def _parameters_of(function: ast.AST) -> list[ast.arg]:
    if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
        return []
    arguments = function.args
    return [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]


@functools.cache
def _resolved(name: str, module_name: str) -> object:
    """What *name* stands for in *module_name*: an object the module binds,
    or one it imports only under ``TYPE_CHECKING`` (``None`` when neither).
    """
    module = _module_object(module_name)
    found = getattr(module, name, None)
    if found is not None or module is None:
        return found
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError, SyntaxError):
        return None
    package = module.__package__ or module_name.rpartition(".")[0]
    for node in _module_statements(tree.body):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if (alias.asname or alias.name) != name:
                continue
            try:
                source = importlib.util.resolve_name(
                    "." * node.level + (node.module or ""), package
                )
                return getattr(importlib.import_module(source), alias.name, None)
            except (ImportError, ValueError):
                return None
    return None


def _returned(
    call: ast.Call, function: ast.AST | None, module_name: str
) -> tuple[str, str] | None:
    """The return annotation of what *call* calls, with the module it is read
    in: a function nested in *function*, or one *module_name* binds or
    imports. ``None`` when the callee is not found or says nothing.
    """
    if not isinstance(call.func, ast.Name):
        return None
    name = call.func.id
    if function is not None:
        for node in ast.walk(function):
            if (
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node is not function
                and node.name == name
            ):
                returns = node.returns
                return None if returns is None else (ast.unparse(returns), module_name)
    called = _resolved(name, module_name)
    if not callable(called) or inspect.isclass(called):
        return None
    called = inspect.unwrap(called)
    if not inspect.isfunction(called):
        return None
    returned = inspect.get_annotations(called).get("return")
    if returned is None:
        return None
    return _annotation(returned), called.__module__


def _closed_options(annotation: str, module_name: str) -> frozenset[str]:
    """The options of an annotation each member of which is a ``Literal`` of
    texts or ``None``; empty when a member lets another value through.
    """
    read = expanded(annotation, module_name)
    members = _members(read)
    if not all(member == "None" or member.startswith("Literal[") for member in members):
        return frozenset()
    return _literal_options(read)


def _unpacked_source(
    value: ast.expr,
    index: int,
    width: int,
    function: ast.AST | None,
    module_name: str,
    depth: int,
) -> _Source:
    """What the item *index* of a *width*-tuple unpacked from *value* is made of.

    ``key, alpha = _resolve(...)`` reads the item of the callee's
    ``tuple[...]`` return annotation; ``a, b = "x", y`` the item written.
    """
    if isinstance(value, ast.Tuple) and len(value.elts) == width:
        return _source(value.elts[index], function, module_name, depth + 1)
    if isinstance(value, ast.Call):
        returned = _returned(value, function, module_name)
        if returned is not None:
            parsed = _generic(expanded(*returned))
            if (
                parsed is not None
                and parsed[0] in {"tuple", "Tuple"}
                and len(parsed[1]) == width
            ):
                options = _closed_options(parsed[1][index], returned[1])
                if options:
                    return _Source("literal", options)
    return _OPEN_SOURCE


def _literal_annotation(
    annotation: ast.expr | None, module_name: str
) -> frozenset[str]:
    if annotation is None:
        return frozenset()
    read = expanded(ast.unparse(annotation), module_name)
    return _literal_options(read) if _is_literal(read) else frozenset()


def _source(
    expression: ast.expr, function: ast.AST | None, module_name: str, depth: int
) -> _Source:
    """What *expression*, written in *function* of *module_name*, is made of."""
    if depth > _SOURCE_DEPTH:
        return _OPEN_SOURCE
    if isinstance(expression, ast.Constant):
        if isinstance(expression.value, str):
            return _Source("texts", frozenset({expression.value}))
        return (
            _Source("none", frozenset()) if expression.value is None else _OPEN_SOURCE
        )
    if isinstance(expression, ast.IfExp):
        return _merged(
            [
                _source(expression.body, function, module_name, depth + 1),
                _source(expression.orelse, function, module_name, depth + 1),
            ]
        )
    if isinstance(expression, ast.Call) and _call_name(expression) in VALIDATORS:
        return _Source("literal", frozenset())
    if isinstance(expression, ast.Call):
        # What a function annotated to return a Literal hands back.
        returned = _returned(expression, function, module_name)
        options = _closed_options(*returned) if returned is not None else frozenset()
        return _Source("literal", options) if options else _OPEN_SOURCE
    if isinstance(expression, ast.Name):
        return _name_source(expression.id, function, module_name, depth)
    if isinstance(expression, ast.Attribute):
        return _attribute_source(expression, function, module_name)
    if isinstance(expression, ast.Subscript) and isinstance(expression.value, ast.Name):
        table = getattr(_module_object(module_name), expression.value.id, None)
        if (
            isinstance(table, collections.abc.Mapping)
            and table
            and all(isinstance(held, str) for held in table.values())
        ):
            return _Source("texts", frozenset(table.values()))
    return _OPEN_SOURCE


def _name_source(
    name: str, function: ast.AST | None, module_name: str, depth: int
) -> _Source:
    if function is None:
        value = getattr(_module_object(module_name), name, None)
        return (
            _Source("texts", frozenset({value}))
            if isinstance(value, str)
            else _OPEN_SOURCE
        )
    for parameter in _parameters_of(function):
        if parameter.arg != name:
            continue
        options = _literal_annotation(parameter.annotation, module_name)
        if options:
            return _Source("literal", options)
        if (
            isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef)
            and function.name.startswith("_")
            and not function.name.startswith("__")
        ):
            return _callers_source(function, name, module_name, depth)
        return _OPEN_SOURCE
    found: list[_Source] = []
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            found.append(_source(node.value, function, module_name, depth + 1))
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Tuple)
        ):
            names = node.targets[0].elts
            for index, bound in enumerate(names):
                if isinstance(bound, ast.Name) and bound.id == name:
                    found.append(
                        _unpacked_source(
                            node.value, index, len(names), function, module_name, depth
                        )
                    )
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            options = _literal_annotation(node.annotation, module_name)
            if options:
                found.append(_Source("literal", options))
            elif node.value is not None:
                found.append(_source(node.value, function, module_name, depth + 1))
        elif (
            isinstance(node, ast.For | ast.comprehension)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            held = node.iter
            found.append(
                _merged(
                    [
                        _source(item, function, module_name, depth + 1)
                        for item in held.elts
                    ]
                )
                if isinstance(held, ast.Tuple | ast.List | ast.Set)
                else _OPEN_SOURCE
            )
    if found:
        return _merged(found)
    value = getattr(_module_object(module_name), name, None)
    return (
        _Source("texts", frozenset({value})) if isinstance(value, str) else _OPEN_SOURCE
    )


def _callers_source(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    module_name: str,
    depth: int,
) -> _Source:
    """What every caller of a private helper hands its parameter *name*."""
    defined = getattr(_module_object(module_name), function.name, None)
    positional = [
        argument.arg for argument in (*function.args.posonlyargs, *function.args.args)
    ]
    if positional and positional[0] in {"self", "cls"}:
        positional = positional[1:]
    found: list[_Source] = []
    for caller_module, caller, call in _construction_sites().get(function.name, ()):
        if getattr(_module_object(caller_module), function.name, None) is not defined:
            continue
        handed: ast.expr | None = None
        for keyword in call.keywords:
            if keyword.arg is None:
                return _OPEN_SOURCE
            if keyword.arg == name:
                handed = keyword.value
        if handed is None and name in positional:
            index = positional.index(name)
            if index < len(call.args) and not any(
                isinstance(argument, ast.Starred) for argument in call.args[: index + 1]
            ):
                handed = call.args[index]
        if handed is None:
            return _OPEN_SOURCE
        found.append(_source(handed, caller, caller_module, depth + 1))
    return _merged(found) if found else _OPEN_SOURCE


def _field_options(record: object, name: str) -> frozenset[str]:
    if not (inspect.isclass(record) and dataclasses.is_dataclass(record)):
        return frozenset()
    for field in dataclasses.fields(record):
        if field.name == name:
            read = expanded(_annotation(field.type), _field_module(record, name))
            return _literal_options(read) if _is_literal(read) else frozenset()
    return frozenset()


def _attribute_source(
    expression: ast.Attribute, function: ast.AST | None, module_name: str
) -> _Source:
    """A field read off a record whose class types it with a ``Literal``.

    ``self.<field>`` in a method of the record's class, a parameter annotated
    with the record, or a local bound to what a function annotated to return
    it hands back (a function of the module, one it imports, or one nested in
    the function the field is read in). A record class imported only under
    ``TYPE_CHECKING`` is found where it is imported from.
    """
    module = _module_object(module_name)
    holder = expression.value
    if not isinstance(holder, ast.Name) or function is None or module is None:
        return _OPEN_SOURCE
    candidates: list[object] = [
        _resolved(ast.unparse(parameter.annotation).strip("'\""), module_name)
        for parameter in _parameters_of(function)
        if parameter.arg == holder.id and parameter.annotation is not None
    ]
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == holder.id
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
        ):
            called = getattr(module, _call_name(node.value), None)
            if inspect.isclass(called):
                candidates.append(called)
                continue
            returned = _returned(node.value, function, module_name)
            if returned is not None:
                candidates.append(_resolved(returned[0].strip("'\""), returned[1]))
    for candidate in candidates:
        options = _field_options(candidate, expression.attr)
        if options:
            return _Source("literal", options)
    return _OPEN_SOURCE


def _argument_for(
    call: ast.Call, field: dataclasses.Field[object], positional: list[str]
) -> ast.expr | None | str:
    """What a call to a record's constructor hands *field*: the expression,
    ``None`` when the field keeps its default, or ``"**"`` when a spread of
    keywords may.
    """
    for keyword in call.keywords:
        if keyword.arg == field.name:
            return keyword.value
        if keyword.arg is None:
            return "**"
    if field.name in positional:
        index = positional.index(field.name)
        if any(
            isinstance(argument, ast.Starred) for argument in call.args[: index + 1]
        ):
            return "**"
        if index < len(call.args):
            return call.args[index]
    return None


def constant_fields() -> Iterator[Choice]:
    """Every public record field of text that the package fills from fixed texts.

    A field annotated ``str`` (or ``tuple[str, ...]``) that every call to its
    record's constructor in the package fills with a string constant, a
    ``Literal``-typed value, or a choice from a fixed set of them, is a closed
    vocabulary typed open: a reader of the record cannot tell the four kinds
    of a silencer from free text. Each value is followed back through locals,
    the callers of a private helper and the fields of the records it is read
    off. A field no call fills, or one call fills from an open text, is not
    held to it. This is rule A21 for a record.
    """
    for home, qualname, target in _targets():
        if home in GPU_PARITY or not inspect.isclass(target):
            continue
        if not dataclasses.is_dataclass(target) or issubclass(target, CatalogueRow):
            continue
        record: type = target
        fields = dataclasses.fields(record)
        positional = [
            field.name for field in fields if field.init and not field.kw_only
        ]
        for field in fields:
            read = expanded(_annotation(field.type), _field_module(record, field.name))
            collection = takes_any_strings(read)
            if not (collection or takes_any_string(read)):
                continue
            if (home, qualname, field.name) in OPEN:
                continue
            sources: list[_Source] = []
            for module_name, function, call in _construction_sites().get(
                record.__name__, ()
            ):
                if (
                    getattr(_module_object(module_name), record.__name__, None)
                    is not record
                ):
                    continue
                handed = _argument_for(call, field, positional)
                if handed == "**":
                    sources.append(_OPEN_SOURCE)
                elif handed is None:
                    default = field.default
                    sources.append(
                        _Source("texts", frozenset({default}))
                        if isinstance(default, str)
                        else _Source("none", frozenset())
                        if default is None
                        else _OPEN_SOURCE
                    )
                elif collection and isinstance(handed, ast.Tuple | ast.List):
                    sources.append(
                        _merged(
                            [
                                _source(item, function, module_name, 0)
                                for item in handed.elts
                            ]
                        )
                    )
                elif isinstance(handed, ast.expr):
                    sources.append(_source(handed, function, module_name, 0))
            built = _merged(sources) if sources else _OPEN_SOURCE
            if built.kind in {"texts", "literal"}:
                spelled = ", ".join(repr(text) for text in sorted(built.texts)[:6])
                yield Choice(
                    home,
                    qualname,
                    field.name,
                    _annotation(field.type),
                    (
                        f"every one of the {len(sources)} constructions in the "
                        f"package fills it with {spelled or 'a checked choice'}",
                    ),
                )


#: The statements a check of a choice may sit inside without leaving a path on
#: which the choice goes unchecked: a test that is about the choice itself
#: (``if text is not None``, ``if isinstance(text, str)``, ``for item in
#: texts``) runs the check whenever the choice is there to check.


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }


def _mentions(node: ast.AST, is_raw: Callable[[ast.expr], bool]) -> bool:
    return any(isinstance(part, ast.expr) and is_raw(part) for part in ast.walk(node))


def _branches_away(
    holder: ast.AST, child: ast.AST, is_raw: Callable[[ast.expr], bool]
) -> bool:
    """Whether *holder* runs *child* on some paths only, for a reason that is
    not the choice itself.
    """
    if isinstance(holder, ast.If | ast.IfExp) and child is not holder.test:
        return not _mentions(holder.test, is_raw)
    if isinstance(holder, ast.While):
        return child is not holder.test
    if isinstance(holder, ast.BoolOp) and child in holder.values:
        before = holder.values[: holder.values.index(child)]
        return bool(before) and not any(_mentions(value, is_raw) for value in before)
    if isinstance(holder, ast.For | ast.AsyncFor) and child is not holder.iter:
        return not _mentions(holder.iter, is_raw)
    if isinstance(holder, ast.Try):
        return child in holder.orelse
    return isinstance(
        holder,
        ast.ExceptHandler
        | ast.match_case
        | ast.Lambda
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.comprehension,
    )


def _on_some_path_only(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    is_raw: Callable[[ast.expr], bool],
    root: ast.AST,
) -> bool:
    """Whether *node* runs on some paths through *root* and not on others,
    for a reason that is not the choice itself.
    """
    child, holder = node, parents.get(node)
    while holder is not None and holder is not root:
        if _branches_away(holder, child, is_raw):
            return True
        child, holder = holder, parents.get(holder)
    return False


#: The statements that open a scope of their own: a ``return`` inside one
#: ends a path of that scope, not of the function around it.
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_LOOPS = (ast.For, ast.AsyncFor, ast.While)


def _block_before(holder: ast.AST, child: ast.AST) -> list[ast.stmt]:
    """The statements of *holder*'s block that run before *child* in it."""
    for field in ("body", "orelse", "finalbody", "handlers", "cases"):
        block = getattr(holder, field, None)
        if isinstance(block, list) and child in block:
            return block[: block.index(child)]
    return []


def _own_nodes(statement: ast.AST) -> Iterator[ast.AST]:
    """The nodes of *statement*, nested scopes left out."""
    pending = [statement]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(
            child
            for child in ast.iter_child_nodes(node)
            if not isinstance(child, _SCOPES)
        )


def _behind_a_test_of(
    node: ast.AST,
    statement: ast.AST,
    parents: dict[ast.AST, ast.AST],
    is_raw: Callable[[ast.expr], bool],
) -> bool:
    """Whether *node*, inside *statement*, runs only behind a test of the
    choice itself (``if text is None: return``).
    """
    child, holder = node, parents.get(node)
    while holder is not None:
        if (
            isinstance(holder, ast.If | ast.IfExp | ast.While)
            and child is not holder.test
            and _mentions(holder.test, is_raw)
        ) or (
            isinstance(holder, ast.Match)
            and child is not holder.subject
            and _mentions(holder.subject, is_raw)
        ):
            return True
        if holder is statement:
            return False
        child, holder = holder, parents.get(holder)
    return False


def _ends_a_path(
    node: ast.AST,
    statement: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    """Whether *node*, inside *statement*, leaves the code after *statement*:
    a ``return`` of the function, or a ``continue`` or ``break`` of a loop
    *statement* sits in (one of a loop inside *statement* stays in it).
    """
    if isinstance(node, ast.Return):
        return True
    if not isinstance(node, ast.Continue | ast.Break):
        return False
    child: ast.AST = node
    holder = parents.get(node)
    while holder is not None:
        if isinstance(holder, _LOOPS) and child not in holder.orelse:
            return False
        if holder is statement:
            return True
        child, holder = holder, parents.get(holder)
    return True


def _left_before(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    is_raw: Callable[[ast.expr], bool],
    root: ast.AST,
    checked: Callable[[ast.AST], bool],
) -> bool:
    """Whether a path through *root* can leave it before *node* runs, for a
    reason that is not the choice itself.

    A ``return`` in a statement before *node*, in *node*'s block or any block
    around it, ends the paths that take it; so does a ``continue`` or a
    ``break`` of a loop *node* sits in. One behind a test of the choice
    (``if text is None: return``), or one a check of the choice runs before
    (*checked*), leaves no choice unchecked.
    """
    child, holder = node, parents.get(node)
    while holder is not None and child is not root:
        for statement in _block_before(holder, child):
            for inner in _own_nodes(statement):
                if (
                    _ends_a_path(inner, statement, parents)
                    and not _behind_a_test_of(inner, statement, parents, is_raw)
                    and not checked(inner)
                ):
                    return True
        child, holder = holder, parents.get(holder)
    return False


class _Check(NamedTuple):
    """One check a choice reaches: whether every path runs it, and whether it
    refuses a value that is not a text with ``TypeError`` (a shared validator)
    or only an unknown text, with ``ValueError`` (``if text not in OPTIONS``).
    """

    every_path: bool
    validator: bool


def _keeps_keys(value: ast.expr, target: Callable[[ast.expr], bool]) -> bool:
    """Whether *value* is a dict comprehension that keeps the target's keys.

    ``{side: float_keyed(row) for side, row in limits.items()}`` or ``{side:
    0.0 for side in limits}`` maps each key of ``limits`` to a new value and
    keeps the key as the caller wrote it.
    """
    if not isinstance(value, ast.DictComp) or len(value.generators) != 1:
        return False
    loop = value.generators[0]
    source = loop.iter
    bound = loop.target
    if (
        isinstance(source, ast.Call)
        and isinstance(source.func, ast.Attribute)
        and source.func.attr == "items"
        and not source.args
    ):
        source = source.func.value
        if not (isinstance(bound, ast.Tuple) and len(bound.elts) == 2):
            return False
        bound = bound.elts[0]
    return (
        isinstance(bound, ast.Name)
        and isinstance(value.key, ast.Name)
        and value.key.id == bound.id
        and target(_held(source))
    )


def _carries(value: ast.expr, target: Callable[[ast.expr], bool]) -> bool:
    """Whether *value* holds the target's items: the target itself, a call
    that only holds its items (``tuple(x)``), the one-item tuple ``(x,)``
    that wraps a single choice of a choice-or-sequence parameter, or a dict
    comprehension that keeps its keys (:func:`_keeps_keys`).
    """
    value = _held(value)
    if _keeps_keys(value, target):
        return True
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "dict"
        and len(value.args) == 1
        and not value.keywords
    ):
        # dict(levels) or dict(levels.items()): the same keys.
        source = value.args[0]
        if (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "items"
            and not source.args
        ):
            source = source.func.value
        return target(_held(source))
    return target(value) or (
        isinstance(value, ast.Tuple) and len(value.elts) == 1 and target(value.elts[0])
    )


def _with_copies(
    tree: ast.AST, target: Callable[[ast.expr], bool]
) -> Callable[[ast.expr], bool]:
    """*target* widened to the locals bound to a copy of its items.

    ``rows = tuple(dict.fromkeys(parameters))`` or ``efforts = (effort,) if
    isinstance(effort, str) else tuple(effort)``: a check of each item of
    the local is a check of each item of the target.
    """
    copies: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            bound, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            bound, value = node.target, node.value
        else:
            continue
        if not isinstance(bound, ast.Name):
            continue
        branches = (
            [value.body, value.orelse] if isinstance(value, ast.IfExp) else [value]
        )
        if all(_carries(branch, target) for branch in branches):
            copies.add(bound.id)

    def matches(node: ast.expr) -> bool:
        return target(node) or (isinstance(node, ast.Name) and node.id in copies)

    return matches


def _record_constructor(callee: Callable[..., object]) -> type | None:
    """The record a dataclass ``__init__`` builds, so a choice handed to it is
    read in the record's ``__post_init__``.
    """
    qualname = getattr(callee, "__qualname__", "")
    if not qualname.endswith(".__init__"):
        return None
    owner = sys.modules.get(getattr(callee, "__module__", ""))
    for part in qualname.split(".")[:-1]:
        owner = getattr(owner, part, None)
    return owner if inspect.isclass(owner) and dataclasses.is_dataclass(owner) else None


@functools.cache
def _checks_of(
    function: Callable[..., object],
    name: str,
    *,
    field: bool,
    collection: bool,
    depth: int,
) -> tuple[_Check, ...]:
    """The checks a choice reaches in *function*, received as parameter (or,
    with *field*, read as ``self.<name>``) *name*.
    """
    tree = _parsed(function)
    if tree is None:
        return ()
    module_name = getattr(function, "__module__", "") or ""
    namespace = _namespace(function, tree, module_name)
    spread = _spread_dicts(tree)
    target = _with_copies(tree, _field_of_self(name) if field else _the_name(name))
    items = _item_names(tree, target) if collection else set()

    def is_raw(node: ast.expr) -> bool:
        return target(node) or (isinstance(node, ast.Name) and node.id in items)

    root = tree.body[0] if isinstance(tree, ast.Module) and tree.body else tree
    parents = _parents(tree)
    # Each place the choice meets a check, with the checks it meets there.
    sites: list[tuple[ast.AST, tuple[_Check, ...]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _raises(node.body):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and is_raw(test.left)
                and isinstance(test.ops[0], ast.NotIn)
            ):
                sites.append((node, (_Check(every_path=True, validator=False),)))
        if not isinstance(node, ast.Call):
            continue
        if node.args and is_raw(node.args[0]) and _call_name(node) in VALIDATORS:
            sites.append((node, (_Check(every_path=True, validator=True),)))
            continue
        callee = _callee(node, namespace, module_name)
        if callee is None or depth >= _SPELLING_DEPTH:
            continue
        inner: list[_Check] = []
        if field and _reads_own_field(node, callee, namespace):
            inner.extend(
                _checks_of(
                    callee, name, field=True, collection=collection, depth=depth + 1
                )
            )
        record = _record_constructor(callee)
        for parameter, handed in _arguments(node, callee, spread).items():
            value = _held(handed)
            keys_kept = _keeps_keys(value, target)
            if not (is_raw(value) or keys_kept):
                continue
            if record is not None:
                check = _post_init(record)
                if check is not None:
                    inner.extend(
                        _checks_of(
                            check,
                            parameter,
                            field=True,
                            collection=collection and (target(value) or keys_kept),
                            depth=depth + 1,
                        )
                    )
            else:
                inner.extend(
                    _checks_of(
                        callee,
                        parameter,
                        field=False,
                        collection=collection and (target(value) or keys_kept),
                        depth=depth + 1,
                    )
                )
        if inner:
            sites.append((node, tuple(inner)))
    validated = [
        node
        for node, checks in sites
        if any(check.validator and check.every_path for check in checks)
    ]

    def checked(leaving: ast.AST) -> bool:
        """Whether a check of the choice runs before *leaving* on its path."""
        return any(
            _contains(leaving, node) or _runs_before(node, leaving, parents, is_raw)
            for node in validated
        )

    found: list[_Check] = []
    for node, checks in sites:
        here = not (
            _on_some_path_only(node, parents, is_raw, root)
            or _left_before(node, parents, is_raw, root, checked)
        )
        found.extend(
            _Check(here and check.every_path, check.validator) for check in checks
        )
    return tuple(found)


def _contains(outer: ast.AST, node: ast.AST) -> bool:
    return any(part is node for part in ast.walk(outer))


def _runs_before(
    node: ast.AST,
    later: ast.AST,
    parents: dict[ast.AST, ast.AST],
    is_raw: Callable[[ast.expr], bool],
) -> bool:
    """Whether *node* runs on every path that reaches *later*: it sits, on
    every path through its statement, in a statement before *later*'s, in
    *later*'s block or a block around it.
    """
    child, holder = later, parents.get(later)
    while holder is not None and not isinstance(child, _SCOPES):
        for statement in _block_before(holder, child):
            if _contains(statement, node) and not _on_some_path_only(
                node, parents, is_raw, holder
            ):
                return True
        child, holder = holder, parents.get(holder)
    return False


def _reads_own_field(
    node: ast.Call, callee: Callable[..., object], namespace: dict[str, object]
) -> bool:
    """Whether a call is ``self.<method>(...)`` of the record's own class, whose
    body reads the record's fields as ``self.<field>`` too.
    """
    called = node.func
    owner = namespace.get("self")
    return (
        isinstance(called, ast.Attribute)
        and isinstance(called.value, ast.Name)
        and called.value.id == "self"
        and inspect.isclass(owner)
        and getattr(inspect.getattr_static(owner, called.attr, None), "__func__", None)
        in {callee, None}
        and callable(inspect.getattr_static(owner, called.attr, None))
    )


def _verdict(checks: tuple[_Check, ...]) -> str | None:
    """What is wrong with how a choice is checked, or ``None``."""
    if any(check.validator and check.every_path for check in checks):
        return None
    if any(check.validator for check in checks):
        return "checked on some paths only, so a misspelling passes on the others"
    if checks:
        return (
            "checked with ``not in``, so a value that is not a text is refused "
            "with ValueError instead of TypeError"
        )
    return "never checked, so a misspelling passes"


#: Choices a function or a record leaves unchecked on purpose, keyed by
#: ``(module, qualified name, parameter)``, with the reason. An entry that
#: matches nothing fails.
UNCHECKED: dict[tuple[str, str, str], str] = {
    ("phonometry._internal.catalogue", "Provenance", "kind"): (
        "a field of a catalogue's provenance: the catalogue contract refuses a "
        "field it cannot read, of any type, with the CatalogueError that names "
        "the field and where the file holds it"
    ),
}


@functools.cache
def _input_records() -> frozenset[type]:
    """The public records a caller builds: one a public function takes, or one
    such a record holds, as the parameter-units guard reads them.
    """
    # A sibling guard, imported where it is needed so this one runs alone.
    import check_parameter_units  # noqa: PLC0415

    taken = check_parameter_units._taken_as_arguments()
    return frozenset(
        record
        for name, record in check_parameter_units._public_records().items()
        if (record.__module__, record.__qualname__)
        not in check_parameter_units.RECORD_AXIS_EXEMPT
        and re.search(rf"\b{re.escape(name)}\b", taken)
    )


def unchecked_choices() -> Iterator[Choice]:
    """Every public ``Literal`` choice a caller can pass unchecked.

    A parameter typed with a ``Literal`` of texts, and a field of a record a
    caller builds, must reach a shared validator (``require_choice``,
    ``check_language``, ``check_engine``) on every path, in the function, in
    one it is handed to or in the ``__post_init__`` of the record it is handed
    to: a choice compared with ``==`` takes a misspelling down the ``else``
    branch, one checked only beside another argument passes a misspelling when
    that argument is absent, and one checked with ``if text not in OPTIONS``
    refuses a number with ``ValueError``. A check behind a test of the choice
    itself (``if text is not None``, ``if isinstance(text, str)``) runs
    whenever there is a choice to check. This is rule A45.
    """
    inputs = _input_records()
    for home, qualname, obj in _targets():
        if home in GPU_PARITY:
            continue
        if inspect.isclass(obj):
            if (
                not dataclasses.is_dataclass(obj)
                or issubclass(obj, CatalogueRow)
                or obj not in inputs
            ):
                continue
            check = _post_init(obj)
            for field in dataclasses.fields(obj):
                read = expanded(_annotation(field.type), _field_module(obj, field.name))
                literal, collection = _literal_shape(read)
                if not (literal and _literal_options(read)):
                    continue
                checks = (
                    _checks_of(
                        check, field.name, field=True, collection=collection, depth=0
                    )
                    if check is not None
                    else ()
                )
                verdict = _verdict(checks)
                if verdict is not None:
                    yield Choice(
                        home, qualname, field.name, _annotation(field.type), (verdict,)
                    )
            continue
        if not callable(obj) or _parsed(obj) is None:
            continue
        try:
            signature = inspect.signature(obj)
        except (TypeError, ValueError):
            continue
        for parameter in signature.parameters.values():
            read = expanded(_annotation(parameter.annotation), home)
            literal, collection = _literal_shape(read)
            if not (literal and _literal_options(read)):
                continue
            verdict = _verdict(
                _checks_of(
                    obj, parameter.name, field=False, collection=collection, depth=0
                )
            )
            if verdict is not None:
                yield Choice(
                    home,
                    qualname,
                    parameter.name,
                    _annotation(parameter.annotation),
                    (verdict,),
                )


def offenders() -> tuple[list[Choice], list[tuple[str, str, str]]]:
    """The closed choices typed ``str``, and the stale entries of :data:`OPEN`.

    A closed choice is one the code treats as one (:func:`string_choices`) or
    a record field the package fills only from fixed texts
    (:func:`constant_fields`).
    """
    found: dict[tuple[str, str, str], Choice] = {}
    used: set[tuple[str, str, str]] = set()
    for choice in string_choices():
        key = (choice.module, choice.qualname, choice.name)
        if key in OPEN:
            used.add(key)
            continue
        if choice.evidence:
            found[key] = choice
    for choice in constant_fields():
        found.setdefault((choice.module, choice.qualname, choice.name), choice)
    return list(found.values()), [key for key in OPEN if key not in used]


def _stale_tables(tables: list[Choice]) -> list[tuple[str, str]]:
    """The entries of :data:`OPEN_TABLES` no table of the walk needs."""
    flagged = {(choice.module, choice.qualname) for choice in tables}
    return [key for key in OPEN_TABLES if key not in flagged]


def _stale_unchecked(unchecked: list[Choice]) -> list[tuple[str, str, str]]:
    """The entries of :data:`UNCHECKED` no choice of the walk needs."""
    flagged = {(choice.module, choice.qualname, choice.name) for choice in unchecked}
    return [key for key in UNCHECKED if key not in flagged]


def _report(title: str, choices: list[Choice], advice: str) -> None:
    print(f"::error::{title}")
    for choice in sorted(choices):
        print(
            f"  {choice.module}.{choice.qualname}({choice.name}): "
            + "; ".join(dict.fromkeys(choice.evidence))
        )
    print(f"  -> {advice}")


def main() -> int:
    """Report every closed choice typed ``str``, every ``Literal`` choice
    cleaned up before its check or not checked on every path, and every
    published table keyed by text that is a vocabulary; the exit status says
    if any.
    """
    found, stale = offenders()
    cleaned = sorted(cleaned_up_choices())
    tables = [
        choice
        for choice in vocabulary_tables()
        if (choice.module, choice.qualname) not in OPEN_TABLES
    ]
    every_unchecked = list(unchecked_choices())
    unchecked = [
        choice
        for choice in every_unchecked
        if (choice.module, choice.qualname, choice.name) not in UNCHECKED
    ]
    stale_tables = _stale_tables(list(vocabulary_tables()))
    stale_unchecked = _stale_unchecked(every_unchecked)
    if not (
        found
        or stale
        or cleaned
        or tables
        or unchecked
        or stale_tables
        or stale_unchecked
    ):
        print(
            "Every public choice of a fixed set of strings is typed Literal, "
            "every string left open says why, every Literal choice is checked "
            "as the caller wrote it on every path, and every published table "
            "of a vocabulary is keyed by it."
        )
        return 0
    if cleaned:
        _report(
            "a Literal choice takes a spelling its Literal does not list",
            cleaned,
            "check the text as written (require_choice) against the options "
            "the Literal lists, before any clean-up, and drop the folding: the "
            "Literal lists the one spelling of each option (rule A45).",
        )
    if unchecked:
        _report(
            "a Literal choice is not checked on every path",
            unchecked,
            "hand it to require_choice where the function starts (in "
            "__post_init__ for a record a caller builds), so a misspelling is "
            "a ValueError and a value that is not a text a TypeError on every "
            "path (rule A45).",
        )
    if tables:
        _report(
            "a published table of a vocabulary is keyed by any text",
            tables,
            "key it by the Literal of its vocabulary (one of its own module "
            "when none fits); a table whose keys match a vocabulary by "
            "coincidence goes in OPEN_TABLES with its reason (rule A21).",
        )
    if found:
        _report(
            "a public choice of a fixed set is typed str",
            found,
            "annotate it with the Literal of its options (a shared alias where "
            "the vocabulary recurs); a string that is open by its nature goes "
            "in OPEN of scripts/check_choice_literals.py with its reason.",
        )
    for key in stale:
        print(
            f"::error::OPEN of scripts/check_choice_literals.py lists {key}, "
            "which no longer exists or no longer needs it"
        )
    for table_key in stale_tables:
        print(
            f"::error::OPEN_TABLES of scripts/check_choice_literals.py lists "
            f"{table_key}, which no longer matches a vocabulary"
        )
    for choice_key in stale_unchecked:
        print(
            f"::error::UNCHECKED of scripts/check_choice_literals.py lists "
            f"{choice_key}, which is now checked or no longer exists"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
