#  Copyright (c) 2026. Jose Manuel Requena Plens
"""One spelling per concept across the public names of the installed package.

A census of every public dataclass field, parameter and property found the
same quantities spelled several ways: ``speed_of_sound`` in eighty places and
``sound_speed`` in seventeen, ``c`` in eight more; ``fs`` in a hundred and
sixty-five and ``sample_rate`` in three; a verdict that ``passes`` on five
results and ``passed`` on four; and ``frequency``, ``time``, ``distance`` and
``level`` naming fifty arrays while the other two hundred and twenty arrays
of the same quantities say ``frequencies``, ``times``, ``distances`` and
``levels``. Every one of those partitions grew back a name at a time, five
singular ``frequency`` arrays arriving with the auditorium results alone,
because nothing looked at the whole API. This does.

What it holds is the spelling the majority already used, and it does not
rule on compounds (``air_sound_speed``, ``band_level``): a modifier reads the
way its standard writes it, and the rule is about the bare concept. An axis
is one of those concepts: ``fs`` is the sample rate whatever its family
called it, a band axis is ``frequencies`` on every result, and ``levels``,
``times`` and ``distances`` carry no unit because their unit never changes.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from typing import TYPE_CHECKING

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator

#: A bare name that spells a concept the rest of the API spells otherwise,
#: mapped to the spelling it has to use.
_MINORITY = {
    "sound_speed": "speed_of_sound",
    "speed_of_sound_m_s": "speed_of_sound",
    "sample_rate": "fs",
    "sampling_rate": "fs",
    "samplerate": "fs",
    "freq": "frequency (one) or frequencies (an array)",
    "freqs": "frequencies",
    "passed": "passes",
    "fs_hz": "fs",
    "sample_rate_hz": "fs",
    "sampling_rate_hz": "fs",
    "sampling_frequency": "fs",
    "frequencies_hz": "frequencies",
    "band_centers": "frequencies",
    "band_centres_hz": "frequencies",
    "centre_frequencies": "frequencies",
    "center_frequencies": "frequencies",
    "band_frequencies": "frequencies",
    "bands_hz": "frequencies",
    "levels_db": "levels",
    "background_levels_db": "background_levels",
    "pressure_levels_db": "pressure_levels",
    "times_s": "times",
    "time_s": "times",
    "distances_m": "distances",
    "sound_speeds": "speeds_of_sound",
    "confidence_level": "confidence",
}

_KHZ = (
    "a formula it evaluates is printed with f in kHz (the NMFS weighting "
    "functions, the Wenz wind-noise rule of fives), so the unit is named"
)
_FEET = "the NPD tables are defined at distances in feet, and distance_ft is public"
_AIRCRAFT = (
    "aircraft holds every distance to its unit, because the ANP database "
    "prints its NPD tables in feet beside the metres the package computes in "
    "(the aircraft rule of scripts/check_parameter_units.py)"
)
#: Where a minority spelling is kept on purpose, keyed by location, each with
#: the reason. An entry that matches nothing any more fails the test too.
_MINORITY_EXEMPT = {
    "phonometry.aircraft.npd_atmosphere.NpdAtmosphereIncrement.distances_m": _FEET,
    "phonometry.aircraft.npd_atmosphere.npd_atmosphere_increment(distances_m)": _FEET,
    "phonometry.aircraft.airport_noise.NpdLevelResult.distances_m": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.event_level(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.noise_contour(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.npd_curve(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.npd_level(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.anp_fleet.AnpDatabase.__init__(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.anp_fleet.AnpNpdCurves.distances_m": _AIRCRAFT,
    "phonometry.aircraft.rotorcraft_noise.RotorcraftEventResult.distances_m": _AIRCRAFT,
    "phonometry.aircraft.rotorcraft_propagation.MeanGroundPlaneResult.distances_m": (
        _AIRCRAFT
    ),
    "phonometry.aircraft.rotorcraft_propagation.TerrainScreeningResult.distances_m": (
        _AIRCRAFT
    ),
    "phonometry.aircraft.rotorcraft_propagation.mean_ground_plane(distances_m)": (
        _AIRCRAFT
    ),
    "phonometry.aircraft.rotorcraft_propagation.terrain_screening_adjustment(distances_m)": (
        _AIRCRAFT
    ),
    "phonometry.underwater.bioacoustics.weighting.weighted_exposure(frequencies_hz)": _KHZ,
    "phonometry.underwater.sources.ambient_noise.ocean_ambient_noise(frequencies_hz)": _KHZ,
    "phonometry.vibration.structural.transfer_stiffness.BandAveragedStiffness.center_frequencies": (
        "a second axis beside nominal_frequencies: the exact centres the "
        "nominal bands were averaged at"
    ),
}

#: Symbols used as parameter names, mapped to the word the API uses. The
#: simulation package is exempt: its solvers take maps of the symbols their
#: equations are written in (``c``, ``rho``, ``c_p``, ``c_s``, ``dx``), as a
#: notation of their own.
_SYMBOLS = {"c": "speed_of_sound", "rho": "density"}
_SYMBOL_EXEMPT_PACKAGES = ("phonometry.simulation.",)
#: Parameters whose symbol is some other quantity than the one above.
_SYMBOL_EXEMPT = {
    # ASTM E2611-19 names the downstream forward amplitude C.
    "phonometry.materials.absorbers.four_microphone.face_quantities(c)",
}

#: Singular and plural of the quantities an array of is named in the plural.
_PLURALS = {
    "frequency": "frequencies",
    "time": "times",
    "distance": "distances",
    "level": "levels",
}
#: Unit suffixes a quantity name can carry; the rule reads the name without it.
_UNIT_SUFFIXES = ("_hz", "_db", "_s", "_m")

#: A ``:param`` text that says the argument holds many values: one per band,
#: a band axis, a shape, or a plural noun before the first symbol or comma.
_READS_AS_MANY = re.compile(
    r"\bper band\b|\bone value per\b|\bone-dimensional\b|\b1-D\b"
    r"|\bband axis\b|\bshape ``\(|\bin ascending (?:band )?order\b"
    r"|^[^`,.:(]*\b(?:frequencies|levels|times|distances|centres|centers)\b",
    re.IGNORECASE,
)
#: A ``:param`` text that says the argument takes one value or many.
_READS_AS_EITHER = re.compile(
    r"\bscalar or\b|\bscalar/array\b|\bany shape\b|\bbroadcast"
    r"|\bone or many\b|\bor (?:frequencies|levels|times|distances)\b|\(s\)",
    re.IGNORECASE,
)


def _kind(annotation: str) -> str:
    """``array``, ``scalar`` or ``either`` for an annotation as written.

    ``either`` is a vectorised argument, one value or many (``ArrayLike``, or
    a union with ``float``), which the rule leaves alone: its name is a matter
    of reading, not of what it holds.
    """
    text = annotation.replace(" ", "")
    parts = set(text.split("|"))
    scalar = bool(parts & {"float", "int", "complex", "SupportsFloat"})
    vector = "ArrayLike" in text
    array = bool(
        re.search(
            r"NDArray|ndarray|Sequence\[|list\[|tuple\[float,\.\.\.\]|\bReal\b|\bComplex\b",
            text,
        )
    )
    if array and not (scalar or vector):
        return "array"
    if scalar and not (array or vector):
        return "scalar"
    return "either"


def _public_modules() -> Iterator[object]:
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        yield importlib.import_module(info.name)


def _public_names() -> Iterator[tuple[str, str, str, str, str]]:
    """``(where, name, annotation, kind, text)`` for every public field and parameter.

    ``kind`` is ``field``, ``property``, ``param`` or ``varargs``; ``text`` is
    the ``:param`` text of a parameter, or ``""``.
    """
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
                yield from _parameters(key, obj)
            elif inspect.isclass(obj):
                yield from _class_names(key, obj)


def _param_text(func: object, name: str) -> str:
    """The ``:param name:`` text of *func*'s docstring, on one line."""
    match = re.search(
        rf":param {re.escape(name)}:(.*?)(?=\n\s*:(?:param|return|raises)|\Z)",
        inspect.getdoc(func) or "",
        re.DOTALL,
    )
    return " ".join(match.group(1).split()) if match else ""


def _parameters(where: str, func: object) -> Iterator[tuple[str, str, str, str, str]]:
    try:
        signature = inspect.signature(func)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - builtins
        return
    for parameter in signature.parameters.values():
        if parameter.name in {"self", "cls"}:
            continue
        kind = "varargs" if parameter.kind is parameter.VAR_POSITIONAL else "param"
        yield (
            f"{where}({parameter.name})",
            parameter.name,
            str(parameter.annotation),
            kind,
            _param_text(func, parameter.name),
        )


def _class_names(where: str, cls: type) -> Iterator[tuple[str, str, str, str, str]]:
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            yield f"{where}.{field.name}", field.name, str(field.type), "field", ""
    elif issubclass(cls, tuple) and hasattr(cls, "_fields"):
        # A named tuple: its fields are neither dataclass fields nor an
        # ``__init__`` of its own, and its accessors are not properties.
        annotations = getattr(cls, "__annotations__", {})
        for name in cls._fields:
            yield f"{where}.{name}", name, str(annotations.get(name, "")), "field", ""
    elif "__init__" in vars(cls):
        yield from _parameters(f"{where}.__init__", vars(cls)["__init__"])
    for name, member in vars(cls).items():
        if name.startswith("_"):
            continue
        getter = (
            member.fget
            if isinstance(member, property)
            else member.func
            if isinstance(member, functools.cached_property)
            else None
        )
        if getter is not None:
            annotation = str(getter.__annotations__.get("return", ""))
            yield f"{where}.{name}", name, annotation, "property", ""
        elif isinstance(member, staticmethod | classmethod):
            yield from _parameters(f"{where}.{name}", member.__func__)
        elif inspect.isfunction(member):
            yield from _parameters(f"{where}.{name}", member)


def test_one_concept_is_spelled_one_way() -> None:
    """The minority spellings of a bare concept name are gone and stay gone."""
    names = list(_public_names())
    assert len(names) > 5000, "the walk found too few names to mean anything"
    offenders = sorted(
        f"{where}: {name!r} is spelled {_MINORITY[name]!r} everywhere else"
        for where, name, *_ in names
        if name in _MINORITY and where not in _MINORITY_EXEMPT
    )
    assert not offenders, "\n".join(offenders)


def test_every_kept_minority_spelling_still_exists() -> None:
    """An exemption that names nothing any more is a stale one."""
    found = {where for where, name, *_ in _public_names() if name in _MINORITY}
    stale = sorted(set(_MINORITY_EXEMPT) - found)
    assert not stale, "\n".join(stale)


def test_a_symbol_is_not_a_parameter_name_outside_the_solvers() -> None:
    """``c`` and ``rho`` are ``speed_of_sound`` and ``density`` by name."""
    offenders = sorted(
        f"{where}: {name!r} is {_SYMBOLS[name]!r} everywhere else"
        for where, name, _, kind, _ in _public_names()
        if kind == "param"
        and name in _SYMBOLS
        and not where.startswith(_SYMBOL_EXEMPT_PACKAGES)
        and where not in _SYMBOL_EXEMPT
    )
    assert not offenders, "\n".join(offenders)


def _quantity(name: str) -> str:
    """*name* without the unit suffix a quantity can carry."""
    for suffix in _UNIT_SUFFIXES:
        stem = name.removesuffix(suffix)
        if stem != name and (stem in _PLURALS or stem in _PLURALS.values()):
            return stem
    return name


def _holds_many(annotation: str, kind: str, text: str) -> bool:
    """Whether a name holds an array: by its annotation, or by its ``:param`` text.

    A vectorised argument (``ArrayLike``, or a union with ``float``) holds
    many when its text says so (one value per band, a band axis, a plural
    noun) and does not also say it takes a single value.
    """
    shape = _kind(annotation)
    if shape == "array":
        return True
    return (
        shape == "either"
        and kind == "param"
        and bool(_READS_AS_MANY.search(text))
        and not _READS_AS_EITHER.search(text)
    )


def _admits_an_array(annotation: str) -> bool:
    """Whether an annotation as written lets an array through."""
    return bool(re.search(r"ArrayLike|NDArray|ndarray|Sequence\[|list\[", annotation))


def _says_neither(annotation: str, kind: str, text: str) -> bool:
    """A vectorised parameter whose ``:param`` text does not say what it holds.

    The text is the only witness the rule has for a parameter that admits a
    number as well as an array, so a singular one has to say, in so many
    words, that it takes one value or many (``scalar or array``). A phrasing
    the rule cannot read (``Frequency vector``, ``the band centres``) is not
    taken on trust either way: it is a finding until the text says which.
    """
    return (
        kind == "param"
        and _kind(annotation) == "either"
        and _admits_an_array(annotation)
        and not _READS_AS_EITHER.search(text)
    )


def _plural_of(name: str, stem: str) -> str:
    """The plural spelling to suggest, the one :data:`_MINORITY` also accepts."""
    plural = _PLURALS[stem] + name.removeprefix(stem)
    return _MINORITY.get(plural, plural)


def test_an_array_of_a_quantity_is_named_in_the_plural() -> None:
    """``frequencies`` holds many, ``frequency`` one; the same for three more.

    An annotation that admits an array and nothing else is held to the
    plural, and so is a vectorised argument whose ``:param`` text says it
    holds one value per band; one that admits a number and nothing else is
    held to the singular. A vectorised argument that takes either keeps a
    singular name, and its text has to say that it takes either: one whose
    text says neither is a finding, so that an array named in the singular
    cannot pass by being described in words the rule does not read. A unit
    suffix does not change the rule: ``frequency_hz`` holding a band axis is
    an array named in the singular.
    """
    singular = {plural: one for one, plural in _PLURALS.items()}
    offenders: list[str] = []
    for where, name, annotation, kind, text in _public_names():
        stem = _quantity(name)
        if stem in _PLURALS and _holds_many(annotation, kind, text):
            offenders.append(
                f"{where}: an array named {name!r}; use {_plural_of(name, stem)!r}"
            )
        elif stem in _PLURALS and _says_neither(annotation, kind, text):
            offenders.append(
                f"{where}: {name!r} admits an array and its :param text does not "
                f"say whether it takes one value or many; say '(scalar or array)' "
                f"if a number works, or name it {_plural_of(name, stem)!r}"
            )
        elif stem in singular and _kind(annotation) == "scalar" and kind != "varargs":
            offenders.append(
                f"{where}: one value named {name!r}; use {singular[stem]!r}"
            )
    assert not offenders, "\n".join(sorted(offenders))


# ---------------------------------------------------------------------------
# A message names the parameter the caller passed.
# ---------------------------------------------------------------------------

#: A quoted identifier in the text of a message: ``'frequencies' must be``.
_QUOTED = re.compile(r"'([A-Za-z_][A-Za-z0-9_]*)'")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _stale_spellings(parameter: str) -> set[str]:
    """The other spellings of *parameter* the vocabulary has retired.

    For ``frequencies``: ``frequency``, ``frequencies_hz``, ``frequency_hz``
    and every minority spelling that :data:`_MINORITY` maps to it. A message
    that quotes one of them names a parameter the caller cannot pass.
    """
    singular = {plural: one for one, plural in _PLURALS.items()}
    stem = _quantity(parameter)
    spellings: set[str] = set()
    for base in {parameter, stem}:
        for word in (base, singular.get(base, base), _PLURALS.get(base, base)):
            if word in _PLURALS or word in singular:
                spellings |= {word} | {word + suffix for suffix in _UNIT_SUFFIXES}
    spellings |= {old for old, new in _MINORITY.items() if new == parameter}
    return spellings - {parameter}


def _named_in(node: ast.AST) -> set[str]:
    """The identifiers a function body puts in front of a user.

    A quoted identifier inside any string, and a bare identifier handed to a
    call next to a value (``require_positive_array(f, "frequency")``) or as a
    key of a mapping handed to one (``{"frequency": f.shape}``), which the
    validation helpers quote in their own messages.
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            names |= set(_QUOTED.findall(child.value))
        if not isinstance(child, ast.Call):
            continue
        arguments = [*child.args, *(keyword.value for keyword in child.keywords)]
        if not any(
            isinstance(argument, ast.Name | ast.Attribute | ast.Subscript | ast.Call)
            for argument in arguments
        ):
            continue
        for argument in arguments:
            keys = argument.keys if isinstance(argument, ast.Dict) else [argument]
            names |= {
                key.value
                for key in keys
                if isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and _IDENTIFIER.match(key.value)
            }
    return names


def _parameter_names(function: ast.FunctionDef) -> list[str]:
    arguments = function.args
    every = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    return [argument.arg for argument in every if argument.arg not in {"self", "cls"}]


def _carriers(function: ast.FunctionDef) -> dict[str, str]:
    """Local name to the parameter it holds, for one-parameter assignments.

    A local the parameter was validated into under its own name
    (``f = require_positive_array(frequencies, "frequencies")``) is left out:
    a check further down sees a value that has already passed it.
    """
    carriers = {name: name for name in _parameter_names(function)}
    validated: set[str] = set()
    for node in ast.walk(function):
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            continue
        sources = {
            carriers[name.id]
            for name in ast.walk(node.value)
            if isinstance(name, ast.Name) and name.id in carriers
        }
        if len(sources) != 1:
            continue
        parameter = sources.pop()
        target = node.targets[0].id
        carriers.setdefault(target, parameter)
        for call in ast.walk(node.value):
            if not isinstance(call, ast.Call):
                continue
            arguments = [*call.args, *(keyword.value for keyword in call.keywords)]
            carries = any(
                isinstance(a, ast.Name) and carriers.get(a.id) == parameter
                for a in arguments
            )
            if carries and any(
                isinstance(a, ast.Constant) and a.value == parameter for a in arguments
            ):
                validated.add(target)
    return {name: held for name, held in carriers.items() if name not in validated}


class _Module:
    """The functions of one source module and the names their messages use."""

    def __init__(self, tree: ast.Module) -> None:
        self.functions = {
            node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        self.callables: list[tuple[str, ast.FunctionDef]] = [
            (name, node) for name, node in self.functions.items()
        ]
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.callables += [
                    (f"{node.name}.{child.name}", child)
                    for child in node.body
                    if isinstance(child, ast.FunctionDef)
                ]
        self._exposure: dict[tuple[str, str], set[str]] = {}

    def passed_on(self, function: ast.FunctionDef, parameter: str) -> set[str]:
        """The names *parameter* reaches a message under, in the functions it is passed to."""
        carriers = _carriers(function)
        names: set[str] = set()
        for call in ast.walk(function):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id in self.functions
                and self.functions[call.func.id] is not function
            ):
                continue
            callee = call.func.id
            bound = list(
                zip(_parameter_names(self.functions[callee]), call.args, strict=False)
            )
            bound += [(k.arg, k.value) for k in call.keywords if k.arg is not None]
            for slot, value in bound:
                if isinstance(value, ast.Name) and carriers.get(value.id) == parameter:
                    names |= self.exposure(callee, slot)
        return names

    def exposure(self, name: str, parameter: str) -> set[str]:
        """The names a message of function *name* gives its *parameter*."""
        key = (name, parameter)
        if key not in self._exposure:
            self._exposure[key] = set()  # a recursive call adds nothing new
            function = self.functions[name]
            own = {parameter} & _named_in(function)
            self._exposure[key] = own | self.passed_on(function, parameter)
        return self._exposure[key]


def test_a_message_names_the_parameter_the_caller_passed() -> None:
    """No message of a public function quotes a retired spelling of its parameter.

    When a parameter is renamed, ``frequency`` to ``frequencies``, the
    messages that quote it have to follow, in the function itself and in the
    helpers it hands the value to: a caller told that ``'frequency' must be
    positive`` looks for a parameter the function no longer has. This reads
    the source of the installed package and, for each public function and
    method, follows each parameter through the functions of its module it is
    passed to, and fails on a message that names it by one of the spellings
    the vocabulary above retired.
    """
    root = Path(phonometry.__file__).parent
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root.parent).with_suffix("")
        if any(part.startswith("_") for part in relative.parts[1:]):
            continue
        module = _Module(ast.parse(path.read_text(encoding="utf-8")))
        for qualified, function in module.callables:
            if any(part.startswith("_") for part in qualified.split(".")):
                continue
            parameters = _parameter_names(function)
            for parameter in parameters:
                stale = _stale_spellings(parameter) - set(parameters)
                named = _named_in(function) | module.passed_on(function, parameter)
                offenders += [
                    f"{relative.as_posix()}:{function.lineno} {qualified}({parameter}): "
                    f"a message calls it {old!r}"
                    for old in sorted(named & stale)
                ]
    assert not offenders, "\n".join(offenders)
