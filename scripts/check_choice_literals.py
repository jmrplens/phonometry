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
from typing import TYPE_CHECKING, NamedTuple

import phonometry
from phonometry._internal.catalogue import CatalogueRow

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import FunctionType, ModuleType

#: The members of an annotation that let any string through.
_STRING_MEMBERS = frozenset({"str", "Optional[str]"})

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
    ("phonometry.emission.sound_power_plant", "PlantRequirement", "clause"): (_LABEL),
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
    ("phonometry.solids.catalogue", "solids_named", "name"): _CATALOGUE_NAME,
    (
        "phonometry.vibration.machinery.diagnostics",
        "FaultFrequencyResult",
        "source",
    ): "a description of the machine element, the plot's title",
    ("phonometry.vibration.machinery.diagnostics", "FaultLine", "name"): (
        "a short label of the line, unique within a result"
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
    """Whether an assigned *value* is the target, cleaned up or resolved.

    The target itself through the calls that only clean it up, an alias
    lookup ``ALIASES.get(name, name)``, or a private helper handed the target
    first (``_normalise(name, ALIASES, "name")``).
    """
    if matches(value):
        return True
    if isinstance(value, ast.Call) and value.args and matches(value.args[0]):
        name = _call_name(value)
        return name == "get" or name.startswith("_")
    return False


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
    """The module-level assignments of *module*, by name, as expressions."""
    if module is None:
        return {}
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError, SyntaxError):
        return {}
    found: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.value is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
        ):
            found[node.target.id] = node.value
    return found


def strings_of(
    node: ast.expr | None, constants: dict[str, ast.expr], depth: int = 0
) -> tuple[str, ...]:
    """The string options an expression holds, or ``()`` when it holds none.

    A tuple, list or set of string constants, the string keys of a dict, a
    call wrapping one of those (``frozenset(...)``, ``MappingProxyType(...)``)
    and a module constant bound to one of those.
    """
    if node is None or depth > 4:
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
    return ()


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def code_evidence(
    tree: ast.AST,
    is_target: Callable[[ast.expr], bool],
    constants: dict[str, ast.expr],
) -> list[str]:
    """What in *tree* treats the target as one of a fixed set of strings."""
    found: list[str] = []
    is_target = _following(tree, is_target)
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
        elif isinstance(node, ast.Compare) and is_target(node.left):
            for operator, right in zip(node.ops, node.comparators, strict=True):
                if isinstance(operator, ast.In | ast.NotIn) and strings_of(
                    right, constants
                ):
                    found.append("'in' a set of strings")
                if (
                    isinstance(operator, ast.Eq | ast.NotEq)
                    and isinstance(right, ast.Constant)
                    and isinstance(right.value, str)
                ):
                    found.append(f"== {right.value!r}")
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
    """Whether a parameter annotation, as written, is a ``Literal`` choice."""
    parts = [part.strip() for part in annotation.split("|")]
    return any(
        part.startswith("Literal[") or part in _literal_aliases() for part in parts
    )


def passed_on_evidence(
    function: object,
    name: str,
    depth: int = 0,
    seen: frozenset[str] = frozenset(),
    constants: dict[str, ast.expr] | None = None,
) -> list[str]:
    """What a function that receives parameter *name* untouched says of it.

    Follows the parameter into each phonometry function it is handed to, and
    reports the first one that checks it against a fixed set of strings or
    already types it ``Literal``. *constants* are the names the function
    knows as collections of strings: its module's, and the tables its caller
    handed it.
    """
    if depth >= _PASS_DEPTH:
        return []
    tree = _parsed(function)
    if tree is None:
        return []
    module_name = getattr(function, "__module__", "") or ""
    if constants is None:
        constants = _module_constants(sys.modules.get(module_name))
    namespace = {
        **getattr(function, "__globals__", {}),
        **_local_imports(tree, module_name),
    }
    matches = _following(tree, _the_name(name))
    spread = _spread_dicts(tree)
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
        annotation = str(inspect.signature(callee).parameters[received].annotation)
        callee_constants = {
            **_module_constants(sys.modules.get(callee.__module__)),
            **_bound_tables(handed, constants),
        }
        callee_tree = _parsed(callee)
        found = (
            code_evidence(callee_tree, _the_name(received), callee_constants)
            if callee_tree is not None
            else []
        )
        label = f"handed to {callee.__qualname__}({received})"
        if found or _is_literal(annotation):
            return [label]
        deeper = passed_on_evidence(
            callee, received, depth + 1, seen | {key}, callee_constants
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


def _targets() -> Iterator[tuple[str, str, object]]:
    """``(module, qualname, object)`` of every public callable and record."""
    seen: set[tuple[str, str]] = set()
    for module in _public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            home = getattr(obj, "__module__", "") or ""
            if not home.startswith("phonometry"):
                continue
            if inspect.isclass(obj):
                if (home, exported) not in seen and dataclasses.is_dataclass(obj):
                    seen.add((home, exported))
                    yield home, exported, obj
                for attribute, member in vars(obj).items():
                    if attribute.startswith("_") and attribute != "__init__":
                        continue
                    function = (
                        member.__func__
                        if isinstance(member, classmethod | staticmethod)
                        else member
                    )
                    if inspect.isfunction(function):
                        key = (home, f"{exported}.{attribute}")
                        if key not in seen:
                            seen.add(key)
                            yield home, f"{exported}.{attribute}", function
            elif inspect.isfunction(obj) and (home, exported) not in seen:
                seen.add((home, exported))
                yield home, exported, obj


def _parsed(obj: object) -> ast.AST | None:
    try:
        return ast.parse(textwrap.dedent(inspect.getsource(obj)))  # type: ignore[arg-type]
    except (OSError, TypeError, SyntaxError):
        return None


def _annotation(value: object) -> str:
    return value if isinstance(value, str) else getattr(value, "__name__", str(value))


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


def string_choices() -> Iterator[Choice]:
    """Every public string parameter or field, with what says it is closed."""
    for home, qualname, obj in _targets():
        constants = _module_constants(sys.modules.get(home))
        if inspect.isclass(obj):
            if issubclass(obj, CatalogueRow):
                continue
            check = vars(obj).get("__post_init__")
            tree = _parsed(check) if check is not None else None
            for field in dataclasses.fields(obj):  # type: ignore[arg-type]
                annotation = _annotation(field.type)
                if not takes_any_string(annotation):
                    continue
                name = field.name
                evidence = (
                    code_evidence(tree, _field_of_self(name), constants)
                    if tree is not None
                    else []
                )
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
            if not takes_any_string(annotation):
                continue
            name = parameter.name
            evidence = (
                code_evidence(tree, _the_name(name), constants)
                if tree is not None
                else []
            )
            if not evidence:
                evidence = passed_on_evidence(obj, name)
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
