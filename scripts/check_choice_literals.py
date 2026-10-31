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
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import functools
import importlib
import importlib.util
import inspect
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
    or None when it is not imported or its source cannot be read.
    """
    module = sys.modules.get(module_name)
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
        values = [
            element.value
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
        return tuple(values) if values and len(values) == len(node.elts) else ()
    if isinstance(node, ast.Dict):
        return tuple(
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        )
    if isinstance(node, ast.Call) and node.args:
        return strings_of(node.args[0], constants, depth + 1)
    if isinstance(node, ast.Name) and node.id in constants:
        return strings_of(constants[node.id], constants, depth + 1)
    return _picked_strings(node, constants, depth)


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

    One of the package's, or one of the module *home* the caller lives in.
    """
    target: object | None = None
    if isinstance(node.func, ast.Name):
        target = namespace.get(node.func.id)
    elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        owner = namespace.get(node.func.value.id)
        target = getattr(owner, node.func.attr, None) if owner is not None else None
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
    not what the wrapper's module does.
    """
    unwrapped = inspect.unwrap(function) if callable(function) else function
    return {
        **getattr(unwrapped, "__globals__", {}),
        **_local_imports(tree, module_name),
    }


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
    """``(module, qualname, object)`` of every public callable and record."""
    seen: set[tuple[str, str]] = set()
    for module in _public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            home = getattr(obj, "__module__", "") or ""
            if not home.startswith("phonometry"):
                continue
            for qualname, target in _exported_targets(exported, obj):
                if (home, qualname) not in seen:
                    seen.add((home, qualname))
                    yield home, qualname, target


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


def offenders() -> tuple[list[Choice], list[tuple[str, str, str]]]:
    """The closed choices typed ``str``, and the stale entries of :data:`OPEN`."""
    found: list[Choice] = []
    used: set[tuple[str, str, str]] = set()
    for choice in string_choices():
        key = (choice.module, choice.qualname, choice.name)
        if key in OPEN:
            used.add(key)
            continue
        if choice.evidence:
            found.append(choice)
    return found, [key for key in OPEN if key not in used]


def main() -> int:
    """Report every closed choice typed ``str``; the exit status says if any."""
    found, stale = offenders()
    if not (found or stale):
        print(
            "Every public choice of a fixed set of strings is typed Literal, "
            "and every string left open says why."
        )
        return 0
    if found:
        print("::error::a public choice of a fixed set is typed str")
        print(f"{len(found)} parameter(s) or field(s) take any string:")
        for choice in sorted(found):
            print(
                f"  {choice.module}.{choice.qualname}({choice.name}): "
                + "; ".join(dict.fromkeys(choice.evidence))
            )
        print(
            "  -> annotate it with the Literal of its options (a shared alias "
            "where the vocabulary recurs); a string that is open by its nature "
            "goes in OPEN of scripts/check_choice_literals.py with its reason."
        )
    for key in stale:
        print(
            f"::error::OPEN of scripts/check_choice_literals.py lists {key}, "
            "which no longer exists or no longer needs it"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
