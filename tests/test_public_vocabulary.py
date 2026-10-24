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
import sys
import textwrap
import types
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

_SCRIPTS = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from check_parameter_units import DIMENSIONLESS

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

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
    "tone_freq": "tone_frequency",
    "ci_lower": "confidence_lower",
    "ci_upper": "confidence_upper",
    "lower_ci": "confidence_lower",
    "upper_ci": "confidence_upper",
    "band_type": "fraction",
    "band_fraction": "fraction",
    "curve": "weighting",
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
    "phonometry.aircraft.npd_atmosphere.NPDAtmosphereIncrement.distances_m": _FEET,
    "phonometry.aircraft.npd_atmosphere.npd_atmosphere_increment(distances_m)": _FEET,
    "phonometry.aircraft.airport_noise.NPDLevelResult.distances_m": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.event_level(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.noise_contour(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.npd_curve(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.airport_noise.npd_level(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.anp_fleet.ANPDatabase.__init__(distances_m)": _AIRCRAFT,
    "phonometry.aircraft.anp_fleet.ANPNPDCurves.distances_m": _AIRCRAFT,
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

    ``kind`` is ``field``, ``property``, ``param``, ``varargs`` (``*args``) or
    ``varkw`` (``**kwargs``); ``text`` is the ``:param`` text of a parameter,
    or ``""``.
    """
    for key, obj in _public_members():
        if inspect.isclass(obj):
            yield from _class_names(key, obj)
        else:
            yield from _parameters(key, obj)


def _public_members() -> Iterator[tuple[str, object]]:
    """``(where, member)`` for every public function and class, once each."""
    seen: set[str] = set()
    # The root publishes its three classes (``Signal``, ``ReportMetadata``,
    # ``PhonometryWarning``) through a lazy ``__getattr__``, so they are read
    # by name from its ``__all__``, not from its namespace.
    root = {name: getattr(phonometry, name) for name in phonometry.__all__}
    members = [root.items()] + [vars(module).items() for module in _public_modules()]
    for items in members:
        for attr, obj in items:
            if attr.startswith("_"):
                continue
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("phonometry"):
                continue
            key = f"{owner}.{getattr(obj, '__qualname__', attr)}"
            if key in seen:
                continue
            seen.add(key)
            if inspect.isfunction(obj) or inspect.isclass(obj):
                yield key, obj


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
        kind = (
            "varargs"
            if parameter.kind is parameter.VAR_POSITIONAL
            else "varkw"
            if parameter.kind is parameter.VAR_KEYWORD
            else "param"
        )
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


def _self_targets(func: object) -> Iterator[str]:
    """The public names *func* assigns on ``self`` (``self.fs = fs``)."""
    try:
        source = textwrap.dedent(inspect.getsource(func))  # type: ignore[arg-type]
    except (OSError, TypeError):  # pragma: no cover - no source to read
        return
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign | ast.AugAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            for element in target.elts if isinstance(target, ast.Tuple) else [target]:
                if (
                    isinstance(element, ast.Attribute)
                    and isinstance(element.value, ast.Name)
                    and element.value.id == "self"
                    and not element.attr.startswith("_")
                ):
                    yield element.attr


def _instance_attributes() -> Iterator[tuple[str, str]]:
    """``(where, name)`` for every public attribute a public plain class sets.

    A dataclass declares its fields, a property is a member of its class, and
    the walk above reads both. A plain class such as ``OctaveFilterBank``
    writes its public attributes in a method (``self.fs = fs``), where no
    signature, field list or member shows them, so they are read from the
    source of every method of the class and of its phonometry bases. That is
    how ``bank.freq``, ``bank.freq_d`` and ``bank.num_bands`` stayed public
    long after every field and parameter of the same quantities was spelled
    out.
    """
    seen: set[str] = set()
    for module in _public_modules():
        for attr, obj in vars(module).items():
            if attr.startswith("_") or not inspect.isclass(obj):
                continue
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("phonometry") or dataclasses.is_dataclass(obj):
                continue
            key = f"{owner}.{obj.__qualname__}"
            if key in seen:
                continue
            seen.add(key)
            names: set[str] = set()
            for klass in obj.__mro__:
                if not (getattr(klass, "__module__", "") or "").startswith(
                    "phonometry"
                ):
                    continue
                for member in vars(klass).values():
                    if inspect.isfunction(member):
                        names.update(_self_targets(member))
            yield from ((f"{key}.{name}", name) for name in sorted(names))


def test_the_attribute_walk_reads_the_plain_classes() -> None:
    """The walk sees what a plain class writes on ``self``, or it proves nothing."""
    found = {where for where, _ in _instance_attributes()}
    assert "phonometry.filters.core.OctaveFilterBank.fs" in found
    assert "phonometry.filters.weighting.WeightingFilter.high_accuracy" in found


def test_one_concept_is_spelled_one_way() -> None:
    """The minority spellings of a bare concept name are gone and stay gone."""
    names = [(where, name) for where, name, *_ in _public_names()]
    assert len(names) > 5000, "the walk found too few names to mean anything"
    names += list(_instance_attributes())
    offenders = sorted(
        f"{where}: {name!r} is spelled {_MINORITY[name]!r} everywhere else"
        for where, name in names
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
    and every minority spelling that :data:`_MINORITY` maps to it; for ``x``,
    the ``signal`` and ``signal_in`` of :data:`_SIGNAL_SPELLINGS`; for a count
    ``n_events``, the bare ``events``; and for a ``min_``/``max_`` name, the
    same name with ``minimum``/``maximum``. A message that quotes one of them
    names a parameter the caller cannot pass.
    """
    singular = {plural: one for one, plural in _PLURALS.items()}
    stem = _quantity(parameter)
    spellings: set[str] = set()
    for base in {parameter, stem}:
        for word in (base, singular.get(base, base), _PLURALS.get(base, base)):
            if word in _PLURALS or word in singular:
                spellings |= {word} | {word + suffix for suffix in _UNIT_SUFFIXES}
    retired = {**_MINORITY, **_SIGNAL_SPELLINGS, **_QUANTITY_SPELLINGS}
    spellings |= {old for old, new in retired.items() if new == parameter}
    tokens = parameter.split("_")
    if "n" in tokens[:2] and tokens[-1] != "n":
        spellings.add("_".join(t for t in tokens if t != "n"))
    if {"min", "max"} & set(tokens):
        spellings.add(
            "_".join({"min": "minimum", "max": "maximum"}.get(t, t) for t in tokens)
        )
    return spellings - {parameter}


def _named_in(node: ast.AST, constants: dict[str, str] | None = None) -> set[str]:
    """The identifiers a function body puts in front of a user.

    A quoted identifier inside any string, in the body or in a module-level
    message the body raises by name (``raise ValueError(_NO_ENERGY_MSG)``),
    and a bare identifier handed to a call next to a value
    (``require_positive_array(f, "frequency")``) or as a key of a mapping
    handed to one (``{"frequency": f.shape}``), which the validation helpers
    quote in their own messages.
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            names |= set(_QUOTED.findall(child.value))
        if isinstance(child, ast.Name) and constants and child.id in constants:
            names |= set(_QUOTED.findall(constants[child.id]))
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
        #: The module-level strings, by name: a message a function raises by
        #: the name of a constant quotes what the constant holds.
        self.constants = {
            target.id: node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

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
            own = {parameter} & _named_in(function, self.constants)
            self._exposure[key] = own | self.passed_on(function, parameter)
        return self._exposure[key]


#: The modules of the shared helpers every domain hands its values to. A
#: helper there that names the value in its message by a defaulted argument
#: (``name="signal"``) speaks for every caller that leaves the argument out.
_SHARED_HELPER_MODULES = (
    "phonometry._internal.validation",
    "phonometry._internal.utils",
    "phonometry.io._resolve",
)


@functools.cache
def _helper_name_defaults() -> dict[str, dict[str, tuple[int | None, str]]]:
    """Each shared helper's defaulted name arguments: ``{param: (position, default)}``.

    A name argument is ``name`` or one ending in ``_name``; the position is
    ``None`` for a keyword-only one.
    """
    positional = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    }
    helpers: dict[str, dict[str, tuple[int | None, str]]] = {}
    for module_name in _SHARED_HELPER_MODULES:
        module = importlib.import_module(module_name)
        for attr, obj in vars(module).items():
            if not inspect.isfunction(obj) or obj.__module__ != module_name:
                continue
            parameters = list(inspect.signature(obj).parameters.values())
            defaults = {
                p.name: (index if p.kind in positional else None, p.default)
                for index, p in enumerate(parameters)
                if (p.name == "name" or p.name.endswith("_name"))
                and isinstance(p.default, str)
            }
            if defaults:
                helpers[attr] = defaults
    return helpers


def _named_by_helper_defaults(node: ast.AST) -> set[str]:
    """The names a shared helper's message gives a value it was handed unnamed.

    A helper such as ``resolve_samples(x)`` with a defaulted ``name="signal"``
    would tell the caller of a function that takes ``x`` that its ``signal``
    is wrong.
    """
    helpers = _helper_name_defaults()
    names: set[str] = set()
    for call in ast.walk(node):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id in helpers
        ):
            continue
        passed = {keyword.arg for keyword in call.keywords}
        for parameter, (position, default) in helpers[call.func.id].items():
            if parameter in passed or (
                position is not None and position < len(call.args)
            ):
                continue
            names |= {default} if _IDENTIFIER.match(default) else set()
    return names


@pytest.mark.parametrize(
    ("parameter", "stale"),
    [
        ("n_events", "events"),
        ("min_n_records", "min_records"),
        ("max_n_arrivals", "maximum_n_arrivals"),
        ("max_level", "maximum_level"),
        ("frequencies", "frequency"),
    ],
)
def test_a_retired_spelling_of_a_parameter_is_stale(parameter: str, stale: str) -> None:
    """A message that quotes the count or min/max spelling a name left is stale."""
    assert stale in _stale_spellings(parameter)


def test_a_message_names_the_parameter_the_caller_passed() -> None:
    """No message of a public function quotes a retired spelling of its parameter.

    When a parameter is renamed, ``frequency`` to ``frequencies``, the
    messages that quote it have to follow, in the function itself and in the
    helpers it hands the value to: a caller told that ``'frequency' must be
    positive`` looks for a parameter the function no longer has. This reads
    the source of the installed package and, for each public function and
    method, follows each parameter through the functions of its module it is
    passed to, and fails on a message that names it by one of the spellings
    the vocabulary above retired. A shared helper of another module that a
    value reaches without its name argument names it by that argument's
    default, so the default is read as well.
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
                named = (
                    _named_in(function, module.constants)
                    | _named_by_helper_defaults(function)
                    | module.passed_on(function, parameter)
                )
                offenders += [
                    f"{relative.as_posix()}:{function.lineno} {qualified}({parameter}): "
                    f"a message calls it {old!r}"
                    for old in sorted(named & stale)
                ]
    assert not offenders, "\n".join(offenders)


# ---------------------------------------------------------------------------
# Acronyms are capitals, and words are spelled out.
# ---------------------------------------------------------------------------

#: The pieces of a class name: a run of capitals that is an acronym
#: (``EPNL`` in ``EPNLResult``), a capitalised word, a lower-case run and a
#: run of digits.
_SEGMENT = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z][a-z]+|[a-z]+|\d+")

#: Acronyms a class name writes in capitals even where no other public class
#: spells them yet: the standards bodies and the quantities the library
#: names. A capitalised segment that reads as one of these (``Hvac``,
#: ``Npd``, ``DbHr``) is the acronym in the wrong case.
_ACRONYMS = frozenset(
    {
        "AGC",
        "ANP",
        "ANR",
        "ANSI",
        "ARP",
        "ASTM",
        "DBHR",
        "DIN",
        "EBU",
        "ECAC",
        "EPNL",
        "FDTD",
        "FFT",
        "HML",
        "HTLAN",
        "HVAC",
        "ICAO",
        "IEC",
        "ISO",
        "MLS",
        "NIPTS",
        "NMFS",
        "NPD",
        "REAT",
        "RMS",
        "SAE",
        "SEL",
        "SII",
        "SNR",
        "SPL",
        "STI",
        "STOI",
        "THD",
        "VDI",
    }
)

#: Capitalised segments that are names, not acronyms, with the reason.
_PROPER_NAMES = {
    "Ecma": "Ecma International writes its own name so; it is not an acronym",
}


def _public_classes() -> dict[str, str]:
    """Every public class by name, mapped to where it is defined."""
    classes: dict[str, str] = {}
    for module in _public_modules():
        for attr, obj in vars(module).items():
            if attr.startswith("_") or not inspect.isclass(obj):
                continue
            owner = getattr(obj, "__module__", "") or ""
            if owner.startswith("phonometry"):
                classes[attr] = f"{owner}.{obj.__qualname__}"
    return classes


def _acronym_offenders(names: Iterable[str]) -> list[str]:
    """The class names that write an acronym as a capitalised word.

    The acronyms are the curated :data:`_ACRONYMS` and every run of capitals
    another of *names* writes (``SNR`` in ``SNRRatingResult``). A run of
    capitalised segments is held against them joined, so ``DbHrCheck`` is
    found as ``DBHR``.
    """
    names = list(names)
    known = set(_ACRONYMS)
    for name in names:
        known |= {s for s in _SEGMENT.findall(name) if len(s) > 1 and s.isupper()}
    offenders: list[str] = []
    for name in names:
        segments = _SEGMENT.findall(name)
        words = [
            s if s[:1].isupper() and s[1:].islower() and s not in _PROPER_NAMES else ""
            for s in segments
        ]
        found = {
            "".join(words[i:j])
            for i in range(len(words))
            for j in range(i + 1, len(words) + 1)
            if all(words[i:j]) and "".join(words[i:j]).upper() in known
        }
        offenders += [
            f"{name}: {word!r} is the acronym {word.upper()!r}"
            for word in sorted(found)
        ]
    return offenders


def test_an_acronym_is_written_in_capitals() -> None:
    """``HTLANResult`` beside ``HMLRatingResult``, never ``HtlanResult``.

    PEP 8 writes an acronym in a CapWords name in capitals, and most of the
    library's classes already did (``EPNLResult``, ``STIResult``,
    ``ZoomFFTResult``). A class that writes one as a word (``HvacWarning``)
    is the minority spelling. Ecma is the one exception: the organisation
    spells its own name so.
    """
    classes = _public_classes()
    assert len(classes) > 500, "the walk found too few classes to mean anything"
    offenders = [
        f"{classes[line.split(':')[0]]}: {line.split(': ', 1)[1]}"
        for line in _acronym_offenders(classes)
    ]
    assert not offenders, "\n".join(sorted(offenders))


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["HtlanResult"], ["HtlanResult: 'Htlan' is the acronym 'HTLAN'"]),
        (["DbHrCheck"], ["DbHrCheck: 'DbHr' is the acronym 'DBHR'"]),
        (["Arp866aAttenuation"], ["Arp866aAttenuation: 'Arp' is the acronym 'ARP'"]),
        # An acronym another class writes in capitals is learnt from it.
        (["QwxResult", "QWXTable"], ["QwxResult: 'Qwx' is the acronym 'QWX'"]),
        (["HTLANResult", "DBHRCheck", "ARP866AAttenuation", "EcmaLoudness"], []),
    ],
)
def test_the_acronym_rule_reads_a_class_name(
    names: list[str], expected: list[str]
) -> None:
    assert _acronym_offenders(names) == expected


#: Abbreviations the library spells out, mapped to the word it uses.
_SPELLED_OUT = {
    "mic": "microphone",
    "mics": "microphones",
    "lab": "laboratory",
    "std": "standard_deviation",
    "freq": "frequency",
    "freqs": "frequencies",
    "ref": "reference",
    "refs": "references",
    "anim": "animation",
    "anims": "animations",
}

#: ``minimum`` and ``maximum`` written as the library writes them, by kind.
_MIN_MAX = {"minimum": "min", "maximum": "max"}
#: The unit that says a ``max`` names a level: ``max_db`` is the maximum level.
_LEVEL_UNITS = frozenset({"db"})
_LMAX_RULE = "the maximum level Lmax is spelled 'max_level'"

_COUNT_RULE = "a count is n_<plural>, as in n_points"
#: Words that begin with ``num`` and are no abbreviation of a count.
_WORDS_FROM_NUM = ("number", "numer", "numpy")
_R_S_MAX = (
    "R_s,max of ISO 10140-1 Annex J, the symbol's own subscript: the largest "
    "sound reduction index the arrangement can show, a limit, not Lmax"
)
#: ``ci`` as a word of a public name: a confidence bound is spelled out.
_CI_RULE = "a confidence bound is 'confidence_lower'/'confidence_upper', never 'ci'"
_C_I = (
    "C_I, the impact sound spectrum adaptation term of ISO 717-2 (C_I, "
    "C_I,50-2500, C_I,Delta, C_I,r), the symbol's own name: no confidence "
    "interval"
)
#: Where a spelling the rules below refuse is kept on purpose, keyed by
#: location, each with the reason. An entry that matches nothing fails.
_SPELLING_EXEMPT = {
    "phonometry.building.measurement.joint_insulation.LaboratoryJointInsulationResult.r_s_max": _R_S_MAX,
    "phonometry.building.measurement.joint_insulation.laboratory_joint_insulation(r_s_max)": _R_S_MAX,
    "phonometry.building.measurement.ratings.ImpactRatingResult.ci": _C_I,
    "phonometry.building.measurement.ratings.ExtendedImpactRatingResult.ci": _C_I,
    "phonometry.building.measurement.ratings.ExtendedImpactRatingResult.ci_50_2500": _C_I,
    "phonometry.building.measurement.ratings.ImpactImprovementRatingResult.ci_delta": _C_I,
    "phonometry.building.measurement.ratings.ImpactImprovementRatingResult.ci_r": _C_I,
    "phonometry.building.measurement.floor_covering_improvement.FloorCoveringImprovementResult.ci_delta": _C_I,
    "phonometry.building.measurement.laboratory_improvement.LaboratoryFloorCoveringImprovementResult.ci_delta": _C_I,
}


def _min_max_spelling(token: str, kind: str) -> str:
    """``min``/``max`` in the case a name of *kind* writes it."""
    short = _MIN_MAX[token]
    if kind == "constant":
        return short.upper()
    return short.capitalize() if kind == "class" else short


def _spelling_problems(name: str, *, kind: str, annotation: str = "") -> list[str]:
    """What a public name spells the way the library does not.

    *kind* is ``param``, ``field``, ``property``, ``constant``, ``function``,
    ``class`` or ``module``. Every name is held to the spelled-out words, to
    ``n_<plural>`` and to ``min``/``max``: ``minimum`` and ``maximum`` appear
    in no public name, whatever it is. The count rule and the maximum-level
    rule read the names that hold a value (parameters, fields, properties and
    constants).
    """
    tokens = (
        [s.lower() for s in _SEGMENT.findall(name)]
        if kind == "class"
        else name.lower().split("_")
    )
    problems = [
        f"{token!r} is spelled {_SPELLED_OUT[token]!r}"
        for token in tokens
        if token in _SPELLED_OUT
    ]
    if any(
        token.startswith("num") and not token.startswith(_WORDS_FROM_NUM)
        for token in tokens
    ):
        problems.append(_COUNT_RULE)
    problems += [
        f"{token!r} is spelled {_min_max_spelling(token, kind)!r}"
        for token in tokens
        if token in _MIN_MAX
    ]
    if "ci" in tokens:
        problems.append(_CI_RULE)
    if kind in {"class", "function", "module"}:
        return problems
    if (
        kind != "constant"
        and tokens[-1] == "count"
        and annotation.replace(" ", "") not in {"bool", "bool|None"}
    ):
        problems.append(_COUNT_RULE)
    problems += [
        _LMAX_RULE
        for token, following in zip(tokens, tokens[1:], strict=False)
        if token == "max" and following in _LEVEL_UNITS
    ]
    return problems


def _module_names() -> Iterator[tuple[str, str, str]]:
    """``(where, name, kind)`` for every name a public module lists in ``__all__``."""
    for module in _public_modules():
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name)
            kind = (
                "class"
                if inspect.isclass(obj)
                else "function"
                if callable(obj)
                else "module"
                if inspect.ismodule(obj)
                else "constant"
            )
            if kind != "module":
                yield f"{module.__name__}.{name}", name, kind


def test_words_are_spelled_out() -> None:
    """``microphone``, ``laboratory``, ``standard_deviation``, ``n_points``, ``max_``.

    One spelling per word across the library: ``mic``, ``lab``, ``std`` and
    ``freq`` are spelled out, a count is ``n_<plural>`` (never ``num_points``,
    ``point_count`` or ``numtaps``), and ``minimum`` and ``maximum`` are
    written ``min`` and ``max`` in every public name, ``MIN``/``MAX`` in a
    constant and ``Min``/``Max`` in a class, as numpy, SciPy, scikit-learn
    and Matplotlib write them (``max_iter``, ``min_samples_leaf``,
    ``vmax``) and as the standards write the maximum and minimum levels
    Lmax and Lmin. ``ref`` is written ``reference``, so the level of a
    reference sound source is ``reference_levels``; the acronyms SPL, SEL, SNR
    and RMS stay, as terms of art, like Lmax. A maximum in decibels is the maximum level, ``max_level``,
    never a bare ``max_db``. A confidence bound is ``confidence_lower`` or
    ``confidence_upper``, so ``ci`` is a word of no public name, the ISO 717-2
    adaptation term C_I aside. The attributes a plain class writes on
    ``self`` are held to the same words as the fields of a dataclass. An
    animation is ``animation``, never ``anim``.
    """
    offenders: list[str] = []
    seen: set[str] = set()
    for where, name, annotation, kind, _ in _public_names():
        if kind == "varargs" or where in seen:
            continue
        seen.add(where)
        if where in _SPELLING_EXEMPT:
            continue
        offenders += [
            f"{where}: {problem}"
            for problem in _spelling_problems(name, kind=kind, annotation=annotation)
        ]
    for where, name, kind in _module_names():
        if where in seen or where in _SPELLING_EXEMPT:
            continue
        seen.add(where)
        offenders += [
            f"{where}: {problem}" for problem in _spelling_problems(name, kind=kind)
        ]
    for where, name in _instance_attributes():
        if where in seen or where in _SPELLING_EXEMPT:
            continue
        seen.add(where)
        offenders += [
            f"{where}: {problem}" for problem in _spelling_problems(name, kind="field")
        ]
    for module in _public_modules():
        path = module.__name__  # type: ignore[attr-defined]
        leaf = path.rsplit(".", 1)[-1]
        offenders += [
            f"{path}: {problem}" for problem in _spelling_problems(leaf, kind="module")
        ]
    assert not offenders, "\n".join(sorted(set(offenders)))


#: Row keys a spelling rule does not apply to, each with its reason. Empty:
#: the two ends of the summation of IEC 61260-1 5.16 across a band are
#: ``summation_difference_lower`` and ``summation_difference_upper``, which
#: no rule refuses.
_ROW_KEY_EXEMPT: dict[tuple[str, str], str] = {}


def test_the_row_keys_of_a_verdict_are_spelled_out() -> None:
    """A key of the per-band rows a verifier returns is held to the same words.

    The rows of ``FilterComplianceResult``, ``WeightingComplianceResult`` and
    ``IntensityInstrumentComplianceResult`` are dictionaries, so no signature
    or field list shows their keys, and ``band["freq"]`` stayed in all three
    after every attribute of the same quantity was spelled ``frequency``.
    They are read from a verdict of each kind.
    """
    from phonometry import emission, filters

    limits = emission.residual_index_limits("probe")
    frequencies, class1 = limits.frequencies, limits.class_1
    verdicts = {
        "FilterComplianceResult": filters.verify_filter_class(
            filters.OctaveFilterBank(48000, fraction=1, limits=[500, 2000]),
            n_points=1024,
        ),
        "WeightingComplianceResult": filters.verify_weighting_class(
            filters.WeightingFilter(48000, "A"), n_sweep_points=256
        ),
        "IntensityInstrumentComplianceResult": emission.verify_intensity_class(
            class1 + 1.0, frequencies=frequencies, device="probe"
        ),
    }
    offenders: list[str] = []
    seen: set[tuple[str, str]] = set()
    for owner, verdict in verdicts.items():
        rows = list(verdict.bands)
        between = getattr(verdict, "between_nominals", None)
        if between is not None:
            rows.append(between)
        assert rows, f"{owner} returned no rows to read"
        for key in sorted({key for row in rows for key in row}):
            seen.add((owner, key))
            if (owner, key) in _ROW_KEY_EXEMPT:
                continue
            offenders += [
                f"{owner} row key {key!r}: {problem}"
                for problem in _spelling_problems(key, kind="field")
            ]
    offenders += [
        f"{owner} row key {key!r} is exempt but no longer exists"
        for owner, key in sorted(set(_ROW_KEY_EXEMPT) - seen)
    ]
    assert not offenders, "\n".join(offenders)


def test_every_kept_spelling_still_exists() -> None:
    """An exemption from the spelling rules that names nothing is a stale one."""
    found = (
        {where for where, *_ in _public_names()}
        | {where for where, *_ in _module_names()}
        | {where for where, _ in _instance_attributes()}
    )
    stale = sorted(set(_SPELLING_EXEMPT) - found)
    assert not stale, "\n".join(stale)


@pytest.mark.parametrize(
    ("name", "kind", "annotation", "expected"),
    [
        ("mic_calibration_factor", "function", "", ["'mic' is spelled 'microphone'"]),
        ("LabInsulationWarning", "class", "", ["'lab' is spelled 'laboratory'"]),
        ("lab_insulation", "module", "", ["'lab' is spelled 'laboratory'"]),
        ("delay_std", "field", "float", ["'std' is spelled 'standard_deviation'"]),
        ("freq_d", "field", "", ["'freq' is spelled 'frequency'"]),
        ("nominal_freq", "field", "", ["'freq' is spelled 'frequency'"]),
        ("band_freqs", "param", "ArrayLike", ["'freqs' is spelled 'frequencies'"]),
        ("lower_edges", "field", "", []),
        ("num_points", "param", "int", [_COUNT_RULE]),
        ("numtaps", "param", "int | None", [_COUNT_RULE]),
        ("point_count", "param", "int", [_COUNT_RULE]),
        ("count", "field", "int", [_COUNT_RULE]),
        ("meets_min_count", "property", "bool", []),
        ("number", "field", "int", []),
        (
            "MINIMUM_MICROPHONE_DISTANCE_M",
            "constant",
            "",
            ["'minimum' is spelled 'MIN'"],
        ),
        (
            "maximum_qualified_radius_m",
            "property",
            "float",
            ["'maximum' is spelled 'max'"],
        ),
        ("max_levels", "param", "ArrayLike", []),
        ("max_level", "field", "float", []),
        ("min_level", "param", "float", []),
        # The maximum and minimum levels Lmax and Lmin are min/max too.
        ("maximum_levels", "param", "ArrayLike", ["'maximum' is spelled 'max'"]),
        ("minimum_level", "param", "float", ["'minimum' is spelled 'min'"]),
        # A maximum given in decibels is the maximum level, however short.
        ("background_max_db", "field", "NDArray", [_LMAX_RULE]),
        ("background_max_level", "param", "ArrayLike", []),
        # The smallest of an attenuation is an extreme, not a level.
        ("min_db", "property", "float", []),
        # A term of art is no exception, nor a noun after a preposition.
        ("minimum_phase_response", "field", "NDArray", ["'minimum' is spelled 'min'"]),
        ("TAKT_MAXIMUM_FACTOR", "constant", "", ["'maximum' is spelled 'MAX'"]),
        ("exceeds_maximum", "property", "bool", ["'maximum' is spelled 'max'"]),
        ("limit_at_max", "field", "bool", []),
        # A function, a class and a module are held to the same spelling.
        (
            "standardized_maximum_impact_level",
            "function",
            "",
            ["'maximum' is spelled 'max'"],
        ),
        ("floor_transfer_max", "function", "", []),
        ("junction_min_vibration_reduction", "function", "", []),
        ("MaxUncertaintyRow", "class", "", []),
        ("MaximumUncertaintyRow", "class", "", ["'maximum' is spelled 'Max'"]),
        ("minimum_phase", "module", "", ["'minimum' is spelled 'min'"]),
        # A confidence bound is spelled out, in every form it could take.
        ("ci_lower", "field", "NDArray", [_CI_RULE]),
        ("ci_low", "field", "NDArray", [_CI_RULE]),
        ("ci_lower_db", "param", "ArrayLike", [_CI_RULE]),
        ("lower_ci_95", "field", "float", [_CI_RULE]),
        ("ci_width", "property", "float", [_CI_RULE]),
        ("CiBounds", "class", "", [_CI_RULE]),
        ("confidence_lower", "field", "NDArray", []),
        # A word that holds the letters is not the word.
        ("acoustic_impedance", "field", "NDArray", []),
    ],
)
def test_the_spelling_rules_read_a_name(
    name: str, kind: str, annotation: str, expected: list[str]
) -> None:
    assert _spelling_problems(name, kind=kind, annotation=annotation) == expected


# ---------------------------------------------------------------------------
# A count says it is a count.
# ---------------------------------------------------------------------------

#: The annotations, as written, of a value that holds a whole number.
_INT_ANNOTATIONS = frozenset({"int", "int|None", "None|int", "Optional[int]"})
#: Units of time a duration is written in. The name before the unit says the
#: quantity (``duration_s``, ``duration_days``, ``period_hours``); a name that
#: is the unit alone (``seconds``, ``years``) says none, whatever it holds: a
#: number, a tuple of the durations of several periods or an array.
_TIME_UNITS = frozenset({"seconds", "minutes", "hours", "days", "years"})
#: Words that end in ``s`` and are no plural: the sample rate.
_NOT_PLURAL = frozenset({"fs"})
#: Words after which a name is a qualifier of the noun before them.
_PREPOSITIONS = frozenset({"at", "of", "in", "for", "to", "by", "from", "on", "with"})
_N_RULE = "a count is n_<plural>"
_DURATION_RULE = "a duration names its quantity before its unit"
_SAMPLES = "a length counted in samples: the unit is the sample, as in delay_samples"
#: Where an ``int`` named in the plural is no count, keyed by location, each
#: with the reason. An entry that matches nothing fails the test too.
_DECIMALS = (
    "the number of decimals a value is rounded to, as numpy's round(decimals=): "
    "a precision, not a tally of things"
)
_COUNT_EXEMPT = {
    "phonometry.building.regulation.spain.DBHRRequirement.decimals": _DECIMALS,
    "phonometry._internal.boundary.round_half_away_from_zero(decimals)": _DECIMALS,
    "phonometry._internal.boundary.round_half_even(decimals)": _DECIMALS,
    "phonometry._internal.boundary.round_half_up(decimals)": _DECIMALS,
    "phonometry.environment.assessment.soundscape.SoundscapeCorrelation.degrees_of_freedom": (
        "the degrees of freedom of the t test, the statistic's own name"
    ),
    "phonometry.signals._cepstrum.EchoDetectionResult.delay_samples": _SAMPLES,
    "phonometry.signals._cepstrum.CepstrumResult.linear_phase_samples": _SAMPLES,
    "phonometry.signals._test_signals.ToneBurstResult.burst_samples": _SAMPLES,
    "phonometry.signals._test_signals.ToneBurstResult.period_samples": _SAMPLES,
    "phonometry.simulation.elastic_fdtd.ElasticBoundaries.absorbing_layer_cells": (
        "the thickness of the absorbing layer counted in grid cells: the unit "
        "is the cell, as the sample is of delay_samples"
    ),
    "phonometry.simulation.fdtd.FDTDBoundaries.absorbing_layer_cells": (
        "the thickness of the absorbing layer counted in grid cells: the unit "
        "is the cell, as the sample is of delay_samples"
    ),
}


def _is_plural(word: str) -> bool:
    """Whether *word* reads as an English plural (``positions``, not ``axis``)."""
    return (
        word.endswith("s")
        and not word.endswith(("ss", "us", "is"))
        and word not in _NOT_PLURAL
    )


def _count_problems(name: str, annotation: str) -> list[str]:
    """Why a value named *name* does not say it is a count or a duration.

    The head noun of a name is its last word, read before a preposition
    (``responses_at_threshold``) and before a trailing participle
    (``positions_used``). An ``int`` whose head noun is a plural holds how
    many of them there are, and is ``n_<plural>``, behind a ``min_``/``max_``
    when it is a limit (``min_n_records``). A rate (``points_per_bandwidth``)
    is not a count, and a duration is read by its unit whatever its type:
    ``duration_days`` is a duration, ``seconds`` or ``years`` alone says no
    quantity, and neither does ``hours`` holding the durations of three
    periods.
    """
    text = annotation.replace(" ", "").replace("<class'int'>", "int")
    whole = text in _INT_ANNOTATIONS
    tokens = name.lower().split("_")
    if tokens[0] in {"min", "max"}:
        tokens = tokens[1:]
    if not tokens or tokens[0] == "n" or "per" in tokens:
        return []
    for index, token in enumerate(tokens):
        if token in _PREPOSITIONS:
            tokens = tokens[:index]
            break
    while len(tokens) > 1 and tokens[-1].endswith("ed"):
        tokens = tokens[:-1]
    if not tokens:
        return []
    if tokens[-1] in _TIME_UNITS:
        return [_DURATION_RULE] if len(tokens) == 1 else []
    if not whole:
        return []
    return [_N_RULE] if _is_plural(tokens[-1]) else []


def test_a_count_is_n_plural() -> None:
    """``n_events``, ``n_turns``, ``n_subjects``: a count says it is one.

    A parameter, a field or a property that holds a whole number of things
    is ``n_<plural>``, the spelling ``n_samples``, ``n_points`` and
    ``n_harmonics`` already had, so ``events=3`` cannot be read as the events
    themselves. A class or a grade (``filter_class``), an axis, a number of
    decimals and a length counted in samples are not counts, and a duration
    in a unit follows the unit rule (``exposure_duration_years``).
    """
    offenders = sorted(
        f"{where}: {problem}"
        for where, name, annotation, kind, _ in _public_names()
        if kind in {"param", "field", "property"} and where not in _COUNT_EXEMPT
        for problem in _count_problems(name, annotation)
    )
    assert not offenders, "\n".join(offenders)


def test_every_kept_count_spelling_still_exists() -> None:
    """An exemption from the count rule that names nothing is a stale one."""
    found = {where for where, *_ in _public_names()}
    stale = sorted(set(_COUNT_EXEMPT) - found)
    assert not stale, "\n".join(stale)


@pytest.mark.parametrize(
    ("name", "annotation", "expected"),
    [
        ("events", "int | None", [_N_RULE]),
        ("microphone_positions", "int", [_N_RULE]),
        ("min_records", "int", [_N_RULE]),
        ("max_arrivals", "int", [_N_RULE]),
        ("responses_at_threshold", "int", [_N_RULE]),
        ("positions_used", "int", [_N_RULE]),
        ("years", "int", [_DURATION_RULE]),
        ("years", "float", [_DURATION_RULE]),
        # A duration is read by its unit whatever it holds.
        ("seconds", "float", [_DURATION_RULE]),
        ("seconds", "int", [_DURATION_RULE]),
        ("minutes", "float | None", [_DURATION_RULE]),
        ("hours", "tuple[float, float, float]", [_DURATION_RULE]),
        ("days", "ArrayLike", [_DURATION_RULE]),
        ("duration_s", "float", []),
        ("period_hours", "tuple[float, float]", []),
        ("seconds_per_decade", "tuple[float, ...]", []),
        ("at_least", "int", []),
        ("n_events", "int | None", []),
        ("min_n_records", "int", []),
        ("max_n_arrivals", "int", []),
        ("exposure_duration_years", "int", []),
        ("duration_days", "int", []),
        ("year_days", "int", []),
        ("points_per_bandwidth", "int", []),
        ("filter_class", "int", []),
        ("axis", "int | None", []),
        ("fs", "int", []),
        # Only a whole number is a count: an array of positions is not one.
        ("positions", "NDArray[np.float64]", []),
        ("events", "float", []),
    ],
)
def test_the_count_rule_reads_a_name(
    name: str, annotation: str, expected: list[str]
) -> None:
    assert _count_problems(name, annotation) == expected


# ---------------------------------------------------------------------------
# A duration says its unit.
# ---------------------------------------------------------------------------

#: The words that make a name a duration, whatever else it says.
_DURATION_WORDS = frozenset({"duration", "durations"})
#: The endings a duration is written in: the second and the millisecond, and
#: the minute, the hour, the day and the year spelled out, as
#: ``duration_s``, ``duration_ms``, ``assessment_period_minutes``,
#: ``duration_hours``, ``duration_days`` and ``exposure_duration_years``
#: write them.
_DURATION_UNITS = ("_s", "_ms", "_minutes", "_hours", "_days", "_years")
_DURATION_UNIT_RULE = "a duration ends in its time unit, as in duration_s"
#: The endings that say a name with the word holds no length of time, so it
#: needs no unit of time: the suffixes ``scripts/check_parameter_units.py``
#: reads as unitless (the decibels of a ``duration_correction``, a ratio, an
#: index), less ``_uncertainty``. The uncertainty of a duration is a length
#: of time in the unit of the duration, as ``u1b`` of ISO 9612 (Eq C.7) is
#: in hours, so it ends in its unit (``sweep_duration_uncertainty_s``).
_DURATION_UNITLESS = tuple(
    suffix for suffix in DIMENSIONLESS if suffix != "_uncertainty"
)
#: Where a duration keeps a name without its unit, keyed by location, each
#: with the reason. An entry that names nothing, or names a duration the
#: rule no longer reports, fails the test too.
_DURATION_EXEMPT = {
    "phonometry.environment.assessment.impulsive_sound.rating_level(durations)": (
        "the durations of the sub-intervals in any time unit, read beside a "
        "reference_time in the same unit: the rating level of ISO/PAS 1996-3 "
        "clause 8 uses only their ratio, so no unit is assumed and none can "
        "be lost"
    ),
    "phonometry.building.measurement.service_equipment.check_background_duration": (
        "a verb, not a duration: it holds the durations_s of the background "
        "measurements of ISO/DIS 16032 7.6 to approximately 30 s and returns "
        "a BackgroundDurationCheck"
    ),
}


def _module_namespace(where: str) -> Mapping[str, object]:
    """The namespace of the module a location of the walk is defined in.

    A location is the module's path followed by a qualified name and, for a
    parameter, the parameter in brackets, so the module is the longest
    leading run of the dotted path that is an imported module.
    """
    parts = where.split("(", 1)[0].split(".")
    for end in range(len(parts), 0, -1):
        module = sys.modules.get(".".join(parts[:end]))
        if module is not None:
            return vars(module)
    return {}


def _is_choice(node: ast.expr, namespace: Mapping[str, object]) -> bool:
    """Whether one member of an annotation is a ``Literal`` or names one."""
    if isinstance(node, ast.Subscript):
        head = node.value
        name = head.attr if isinstance(head, ast.Attribute) else getattr(head, "id", "")
        return name == "Literal"
    if isinstance(node, ast.Name):
        value = namespace.get(node.id)
        value = getattr(value, "__value__", value)  # a ``type X = ...`` alias
        return typing.get_origin(value) is typing.Literal
    return False


def _is_choice_or_flag(annotation: str, namespace: Mapping[str, object]) -> bool:
    """Whether the annotation is a ``Literal`` choice or a ``bool``, or ``None``.

    The annotation is the text the walk reads, so an alias such as
    ``VibrationDuration`` is looked up in the namespace of the module that
    wrote it, and a class a module without postponed annotations shows as
    ``<class 'bool'>`` is read by its name.
    """
    text = re.sub(r"<class '([\w.]+)'>", r"\1", annotation)
    try:
        tree = ast.parse(text, mode="eval").body
    except SyntaxError:
        return False
    members: list[ast.expr] = []
    pending = [tree]
    while pending:
        node = pending.pop()
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            pending.extend((node.left, node.right))
        elif not (isinstance(node, ast.Constant) and node.value is None):
            members.append(node)
    return bool(members) and all(
        (isinstance(node, ast.Name) and node.id == "bool")
        or _is_choice(node, namespace)
        for node in members
    )


def _duration_problems(
    name: str, annotation: str, namespace: Mapping[str, object] | None = None
) -> list[str]:
    """Why a value named *name* that is a duration does not say its unit.

    A name is a duration when one of its words is ``duration`` or
    ``durations``. It ends in a unit of time (:data:`_DURATION_UNITS`) or in a
    suffix that says the value holds no length of time
    (:data:`_DURATION_UNITLESS`), as the decibels of a
    ``duration_correction``. The uncertainty of a duration is not one of
    them: the ``u1b`` of ISO 9612 (Eq C.7) is in hours, so it is written
    ``duration_uncertainty_hours``. A choice among labels
    (``duration: Literal["short_term", "long_term"]``) and a switch
    (``include_duration_uncertainty: bool``) hold no length of time and are
    outside the rule.
    """
    lowered = name.lower()
    if _DURATION_WORDS.isdisjoint(lowered.split("_")):
        return []
    if lowered.endswith(_DURATION_UNITS) or lowered.endswith(_DURATION_UNITLESS):
        return []
    if _is_choice_or_flag(annotation, namespace or {}):
        return []
    return [_DURATION_UNIT_RULE]


def _returns(function: object) -> str:
    """The text of the return annotation of *function*, or ``""``."""
    return str(getattr(function, "__annotations__", {}).get("return", ""))


def _exported_names(
    modules: Iterable[types.ModuleType],
) -> Iterator[tuple[str, str, str]]:
    """``(where, name, annotation)`` for every function and constant *modules* list.

    A function is read by the name its module lists in ``__all__``, where it
    is defined and with the annotation of what it returns, so a predicate
    that returns a ``bool`` reads as a switch. A constant is read in lower
    case (``TAKT_DURATION_S`` as ``takt_duration_s``) with the type of its
    value, once, where the first module that lists it publishes it.
    """
    seen: set[tuple[str, int]] = set()
    for module in modules:
        for name in getattr(module, "__all__", ()):
            value = getattr(module, name)
            if inspect.isclass(value) or inspect.ismodule(value):
                continue
            if (name, id(value)) in seen:
                continue
            seen.add((name, id(value)))
            if callable(value):
                owner = getattr(value, "__module__", None) or module.__name__
                where = f"{owner}.{getattr(value, '__qualname__', name)}"
                yield where, name, _returns(value)
            else:
                where = f"{module.__name__}.{name}"
                yield where, name.lower(), type(value).__name__


def _method_names(
    members: Iterable[tuple[str, object]],
) -> Iterator[tuple[str, str, str]]:
    """``(where, name, annotation)`` for every public method of a class in *members*.

    A method, a static method and a class method are read by name, with the
    annotation of what they return; a property is read with the fields.
    """
    for where, member in members:
        if not inspect.isclass(member):
            continue
        for name, attribute in vars(member).items():
            function = (
                attribute.__func__
                if isinstance(attribute, staticmethod | classmethod)
                else attribute
            )
            if not name.startswith("_") and inspect.isfunction(function):
                yield f"{where}.{name}", name, _returns(function)


def _named_durations() -> Iterator[tuple[str, str, str]]:
    """``(where, name, annotation)`` for every public name the duration rule reads.

    A parameter, a field and a property; a function, a method, a static
    method and a class method; and a constant.
    """
    for where, name, annotation, kind, _ in _public_names():
        if kind in {"param", "field", "property"}:
            yield where, name, annotation
    yield from _exported_names(_public_modules())
    yield from _method_names(_public_members())


def _duration_offenders(
    names: Iterable[tuple[str, str, str]],
) -> dict[str, list[str]]:
    """Every duration among *names* the rule reports, by location, exemptions included."""
    return {
        where: problems
        for where, name, annotation in names
        if (problems := _duration_problems(name, annotation, _module_namespace(where)))
    }


def test_a_duration_ends_in_its_unit() -> None:
    """``duration_s``, ``duration_hours``, ``exposure_duration_years``.

    A parameter, a field, a property, a function, a method or a constant
    whose name says it is a duration ends in the unit of time it holds or
    returns, so ``segment_duration`` cannot be read in seconds by one caller
    and in milliseconds by the next: the name is where the unit is written,
    beside the ``duration_ms`` of a toneburst, the ``duration_hours`` of a
    working day, ``rectangular_pulse_duration_s`` and ``TAKT_DURATION_S``.
    The count rule above refuses a unit alone (``seconds``); this one
    refuses a duration without one.
    """
    offenders = sorted(
        f"{where}: {problem}"
        for where, problems in _duration_offenders(_named_durations()).items()
        if where not in _DURATION_EXEMPT
        for problem in problems
    )
    assert not offenders, "\n".join(offenders)


def test_every_kept_duration_spelling_is_still_one() -> None:
    """An exemption from the duration rule that excuses nothing is a stale one."""
    stale = sorted(set(_DURATION_EXEMPT) - set(_duration_offenders(_named_durations())))
    assert not stale, "\n".join(stale)


_ALIASES = {
    "VibrationDuration": typing.Literal["short_term", "long_term"],
    "Threshold": float,
}


@pytest.mark.parametrize(
    ("name", "annotation", "expected"),
    [
        ("duration", "float", [_DURATION_UNIT_RULE]),
        ("segment_duration", "float", [_DURATION_UNIT_RULE]),
        ("durations", "ArrayLike", [_DURATION_UNIT_RULE]),
        ("duration_range", "tuple[float, float] | None", [_DURATION_UNIT_RULE]),
        # ``_samples`` is a count of samples, not a unit of time.
        ("duration_samples", "tuple[float, ...] | None", [_DURATION_UNIT_RULE]),
        ("duration", "Threshold", [_DURATION_UNIT_RULE]),
        ("duration", "VibrationDuration | float", [_DURATION_UNIT_RULE]),
        ("duration_s", "float", []),
        ("durations_s", "ArrayLike", []),
        ("duration_ms", "float", []),
        ("assessment_duration_minutes", "float", []),
        ("duration_range_hours", "tuple[float, float] | None", []),
        ("duration_days", "int", []),
        ("exposure_duration_years", "int", []),
        ("sweep_duration_uncertainty_s", "float", []),
        ("duration_correction", "float", []),
        ("duration_ratio", "float", []),
        # The uncertainty of a duration is a length of time.
        ("duration_uncertainty", "float", [_DURATION_UNIT_RULE]),
        ("duration_uncertainty_hours", "float", []),
        ("include_duration_uncertainty", "bool", []),
        ("duration", "VibrationDuration", []),
        ("duration", "VibrationDuration | None", []),
        ("duration", "Literal['short_term', 'long_term']", []),
        ("duration", "bool", []),
        ("duration", "<class 'bool'>", []),
        ("duration", "<class 'float'>", [_DURATION_UNIT_RULE]),
        # A name without the word is the count rule's or no rule's.
        ("reference_time", "float", []),
        ("period", "float", []),
    ],
)
def test_the_duration_rule_reads_a_name(
    name: str, annotation: str, expected: list[str]
) -> None:
    assert _duration_problems(name, annotation, _ALIASES) == expected


def test_the_duration_rule_reads_a_function_a_method_and_a_constant() -> None:
    """A function, a method or a constant named for a duration says its unit too.

    The walk reads the name a module lists in ``__all__`` and the methods of
    a class, beside the parameters, fields and properties: a function
    ``strike_duration`` that returns seconds, a method ``rise_duration``, a
    static or class method and a constant ``DEFAULT_PULSE_DURATION`` are
    refused, the same names with their unit pass, and so does a predicate
    that returns a ``bool``.
    """

    def strike_duration(x: float) -> float:
        return x

    def strike_duration_s(x: float) -> float:
        return x

    def is_long_duration(x: float) -> bool:
        return x > 1.0

    class PileStrike:
        def rise_duration(self) -> float:
            return 0.0

        def rise_duration_ms(self) -> float:
            return 0.0

        @staticmethod
        def tail_duration() -> float:
            return 0.0

        @classmethod
        def decay_duration(cls) -> float:
            return 0.0

        def has_duration(self) -> bool:
            return True

    module = types.ModuleType("probe")
    exported = {
        "strike_duration": strike_duration,
        "strike_duration_s": strike_duration_s,
        "is_long_duration": is_long_duration,
        "PileStrike": PileStrike,
        "DEFAULT_PULSE_DURATION": 0.1,
        "TAKT_DURATION_S": 0.125,
        "SHORT_DURATION_ENABLED": True,
    }
    vars(module).update(exported, __all__=list(exported))
    names = [
        *_exported_names([module, module]),
        *_method_names([("probe.PileStrike", PileStrike)]),
    ]
    offenders = _duration_offenders(names)
    assert sorted(where.rsplit(".", 1)[-1] for where in offenders) == [
        "DEFAULT_PULSE_DURATION",
        "decay_duration",
        "rise_duration",
        "strike_duration",
        "tail_duration",
    ]
    assert len(names) == 11, "a name read twice, or one not read"


#: A parameter that names the time signal in a spelling the API retired.
_SIGNAL_SPELLINGS = {"signal": "x", "signal_in": "x"}

#: The spellings a signal of one quantity, a generic record and a reference
#: value had before they said their unit or their word whole.
_QUANTITY_SPELLINGS = {
    "pressure": "pressure_pa",
    "force": "force_n",
    "acceleration": "acceleration_m_s2",
    "record": "x",
    "levels_ref": "reference_levels",
    "background_levels_ref": "reference_background_levels",
    "lw_ref": "reference_sound_power_levels",
    "ref_signal": "reference_signal",
}


def test_the_time_signal_is_x() -> None:
    """A function that reads a time signal takes it as ``x``, first.

    The signal-processing core always did (``octave_filter(x, fs)``,
    ``sel(x, fs)``), and thirty functions in psychoacoustics,
    electroacoustics, environment, vibration and room called it ``signal``
    or ``signal_in`` instead. A record field that holds an output signal
    (``EnvelopeResult.signal``) is not a parameter and keeps its name.
    """
    offenders = sorted(
        f"{where}: the time signal is {_SIGNAL_SPELLINGS[name]!r}"
        for where, name, _, kind, _ in _public_names()
        if kind == "param" and name in _SIGNAL_SPELLINGS
    )
    assert not offenders, "\n".join(offenders)


#: A time signal named for the quantity it holds, without its unit.
_BARE_SIGNAL_QUANTITIES = frozenset(
    {
        "pressure",
        "pressures",
        "force",
        "forces",
        "acceleration",
        "accelerations",
        "velocity",
        "velocities",
        "displacement",
        "displacements",
        "voltage",
        "current",
        "record",
        "records",
    }
)
_SIGNAL_TYPES = re.compile(r"\bSignal(?:Input)?\b")
#: The word a signal of no particular quantity was called before it was ``x``.
_RECORD_WORDS = frozenset({"record", "records"})


def test_a_signal_named_for_its_quantity_carries_its_unit() -> None:
    """``x`` for the generic signal; ``pressure_pa``, ``force_n``, ``acceleration_m_s2``.

    A time signal that is one physical quantity is named for it with its
    unit, as ``velocity_mm_s`` is in the DIN 4150 and DIN 45669 functions:
    the underwater levels read a pressure in pascals, the multiple-shock
    model an acceleration in m/s², an impact hammer a force in newtons.
    A record in any unit is the generic signal, ``x``. The rule reads every
    public parameter and field typed as a signal (``Signal``, ``SignalInput``),
    and every one named ``record`` whatever its type: a result that keeps the
    samples it judged as a bare array (``OverloadCheck.x``) is held to the
    same name as the parameter they came in by.
    """
    offenders = sorted(
        f"{where}: a signal of one quantity is named with its unit "
        "(pressure_pa, force_n, acceleration_m_s2), a generic one is 'x'"
        for where, name, annotation, kind, _ in _public_names()
        if kind in {"param", "field"}
        and name in _BARE_SIGNAL_QUANTITIES
        and (_SIGNAL_TYPES.search(annotation) or name in _RECORD_WORDS)
    )
    assert not offenders, "\n".join(offenders)


def test_no_record_unpacks_like_a_tuple() -> None:
    """A record is read by name: ``curve.times``, never ``times, levels = curve``.

    ``DecayCurve`` and ``LevelHistory`` kept an ``__iter__`` so that the
    ``(times, levels)`` pair they replaced still unpacked; a line that swapped
    the two names still ran. A public record (a dataclass) defines no
    ``__iter__``, so unpacking one raises ``TypeError``. A mapping of rows
    iterates its keys, as a ``dict`` does: that is a collection, not a record.
    """
    import collections.abc

    offenders: list[str] = []
    seen: set[str] = set()
    for module in _public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported)
            if not (inspect.isclass(obj) and dataclasses.is_dataclass(obj)):
                continue
            key = f"{obj.__module__}.{obj.__qualname__}"
            if key in seen or issubclass(obj, collections.abc.Mapping):
                continue
            seen.add(key)
            for klass in obj.__mro__:
                if (getattr(klass, "__module__", "") or "").startswith(
                    "phonometry"
                ) and "__iter__" in vars(klass):
                    offenders.append(f"{key}: defines __iter__ in {klass.__qualname__}")
                    break
    assert not offenders, "\n".join(sorted(offenders))


# --------------------------------------------------------------------------- #
# A standard's designation is in a name only where it distinguishes, one form
# --------------------------------------------------------------------------- #
#: The bodies whose documents a public name may carry, by their number. ASTM
#: numbers begin with a letter (``E2611``), so they read ``astm_e2611``; every
#: other body is joined to its number (``iso10534``, ``IEC61094_2``, ``BS468``,
#: ``ARP866A``, ``AIR1845``), and a part number follows an underscore.
_DESIGNATION = re.compile(
    r"(?:iso|iec|en|din|bs|vdi|arp|air|ansi|ecma)\d+[a-z]?(?:_\d+)?|astm_e\d+",
    re.IGNORECASE,
)
#: A body written apart from its number, a series spelled out after it, or an
#: ASTM body without its number: ``EN_12354``, ``iso_9613``, ``itu_r_468``,
#: ``SAE_AIR1845``, ``air_density_astm``.
_SPLIT_DESIGNATION = re.compile(
    r"(?:^|_)(?:iso|iec|en|din|bs|vdi|arp|ansi|ecma|itu_r|sae)_\d"
    r"|(?:^|_)sae_(?:air|arp)\d"
    r"|(?:^|_)astm(?!_e\d)(?:_|$)",
    re.IGNORECASE,
)

_TABLE = "a printed table number, which belongs to its document"
_INSTANCE = (
    "the one published instance of a record a caller builds with other "
    "values: the designation names the document that fixes these"
)
_SIBLINGS = (
    "the package offers the same quantity by more than one document, and the "
    "designation is what tells them apart"
)
_FAMILY = (
    "a constant of a module whose constants keep their designation, because "
    "one of them would otherwise share a name with another standard's"
)
_OWNER = (
    "without it the name would be another package's public name, and one "
    "public name has one owner"
)
#: Every public name that keeps a designation, keyed by ``module.name`` of the
#: package that publishes it, with the reason. A designation anywhere else is
#: dropped: the module the name lives in already says which standard it
#: follows. An entry that matches nothing fails.
_DESIGNATION_KEPT: dict[str, str] = {
    **dict.fromkeys(
        (
            "phonometry.metrology.IEC61094_2_TABLE_1",
            "phonometry.metrology.IEC61094_2_TABLE_C1",
            "phonometry.metrology.IEC61094_2_TABLE_C2",
            "phonometry.metrology.IEC61094_2_TABLE_C3",
            "phonometry.metrology.IEC61094_3_TABLE_1",
            "phonometry.metrology.IEC61094_5_TABLE_A1",
            "phonometry.metrology.IEC61094_5_TABLE_D1",
            "phonometry.metrology.IEC61094_8_TABLE_1",
            "phonometry.metrology.IEC61094_8_TABLE_2",
            "phonometry.metrology.IEC61183_TABLE_B1",
            "phonometry.metrology.IEC61672_TABLE_4",
            "phonometry.metrology.IEC61672_TABLE_5",
            "phonometry.metrology.IEC61672_TABLE_B1",
            "phonometry.metrology.IEC62585_TABLE_I1",
        ),
        _TABLE,
    ),
    "phonometry.broadcast.BS468_BALLISTICS": _INSTANCE,
    "phonometry.building.EN12354_AIR": _INSTANCE,
    **dict.fromkeys(
        (
            "phonometry.aircraft.AIR1845_ATTENUATION_DB_PER_100M",
            "phonometry.aircraft.ARP866AAttenuation",
            "phonometry.aircraft.attenuation_arp866a",
            "phonometry.aircraft.band_attenuation_arp5534",
            "phonometry.materials.ISO13472_SPEED_OF_SOUND_M_S",
            "phonometry.materials.air_density_iso10534",
            "phonometry.materials.speed_of_sound_iso10534",
            "phonometry.materials.air_density_astm_e2611",
            "phonometry.materials.speed_of_sound_astm_e2611",
            "phonometry.materials.plane_wave_frequency_range_astm_e2611",
            "phonometry.materials.speed_of_sound_iso17497",
            "phonometry.electroacoustics.weighting_bs468",
            "phonometry.environment.GroundSurface.iso9613_ground_factor",
            "phonometry.emission.FreeFieldCheck.iso26101_spacing_met",
        ),
        _SIBLINGS,
    ),
    **dict.fromkeys(
        (
            "phonometry.environment.ISO10847_MIN_BACKGROUND_MARGIN_DB",
            "phonometry.materials.EN16487_COVERAGE_FACTOR",
            "phonometry.vibration.ISO8041_COVERAGE_FACTOR",
            "phonometry.room.ISO14257_MIN_BACKGROUND_MARGIN_DB",
            "phonometry.room.ISO14257_REFERENCE_DISTANCE_M",
            "phonometry.noise_control.ISO7235_COVERAGE_FACTOR",
        ),
        _OWNER,
    ),
    **dict.fromkeys(
        (
            "phonometry.environment.ISO10847_BACKGROUND_CORRECTIONS",
            "phonometry.environment.ISO10847_OCTAVE_BAND_EXTENDED_RANGE_HZ",
            "phonometry.environment.ISO10847_OCTAVE_BAND_RANGE_HZ",
            "phonometry.environment.ISO10847_PREFERRED_BACKGROUND_MARGIN_DB",
            "phonometry.environment.ISO10847_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ",
            "phonometry.environment.ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ",
            "phonometry.room.ISO14257_PREFERRED_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.IEC60534_MOLAR_GAS_CONSTANT_J_KMOL_K",
            "phonometry.noise_control.ISO11691_REPRODUCIBILITY",
            "phonometry.noise_control.ISO11820_AIR_GAS_CONSTANT_J_KG_K",
            "phonometry.noise_control.ISO11820_ATMOSPHERIC_PRESSURE_PA",
            "phonometry.noise_control.ISO11820_BACKGROUND_CORRECTIONS",
            "phonometry.noise_control.ISO11820_MIN_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO11820_MOLAR_GAS_CONSTANT_J_KMOL_K",
            "phonometry.noise_control.ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO11820_OCTAVE_BAND_EXTENDED_RANGE_HZ",
            "phonometry.noise_control.ISO11820_OCTAVE_BAND_RANGE_HZ",
            "phonometry.noise_control.ISO11820_SPEED_OF_SOUND_M_S",
            "phonometry.noise_control.ISO11820_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ",
            "phonometry.noise_control.ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ",
            "phonometry.noise_control.ISO11821_BAND_RANGE_HZ",
            "phonometry.noise_control.ISO11821_MIN_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO11821_PREFERRED_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO11957_MIN_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO11957_PREFERRED_BACKGROUND_MARGIN_DB",
            "phonometry.noise_control.ISO7235_ABSOLUTE_ZERO_OFFSET_K",
            "phonometry.noise_control.ISO7235_AIR_GAS_CONSTANT_J_KG_K",
            "phonometry.noise_control.ISO7235_REPRODUCIBILITY",
            "phonometry.noise_control.ISO7235_SPREAD_LIMITS",
        ),
        _FAMILY,
    ),
}


def _designated_names() -> Iterator[tuple[str, str, str]]:
    """``(key, name, kind)`` of every public name that holds a designation.

    The key is the package that publishes the name, then the name, and for a
    field or a property the class between them: where a caller reads it.
    """
    for package_name in phonometry.__all__:
        package = getattr(phonometry, package_name)
        if not inspect.ismodule(package):
            continue
        for name in getattr(package, "__all__", ()):
            obj = getattr(package, name)
            kind = (
                "class"
                if inspect.isclass(obj)
                else "function"
                if callable(obj)
                else "module"
                if inspect.ismodule(obj)
                else "constant"
            )
            if kind == "module":
                continue
            key = f"{package.__name__}.{name}"
            if _DESIGNATION.search(name) or _SPLIT_DESIGNATION.search(name):
                yield key, name, kind
            if kind != "class":
                continue
            members = (
                [field.name for field in dataclasses.fields(obj)]
                if (dataclasses.is_dataclass(obj))
                else []
            )
            members += [
                attribute
                for attribute, member in vars(obj).items()
                if not attribute.startswith("_")
                and isinstance(member, (property, functools.cached_property))
            ]
            for member in members:
                if _DESIGNATION.search(member) or _SPLIT_DESIGNATION.search(member):
                    yield f"{key}.{member}", member, "field"


def _designation_problems(name: str, kind: str) -> list[str]:
    """How a name that holds a designation writes it the library's way not."""
    problems: list[str] = []
    if _SPLIT_DESIGNATION.search(name):
        problems.append(
            "a designation joins its body to its number (EN12354, iso9613, "
            "BS468, AIR1845), with a part number after an underscore"
        )
        return problems
    found = _DESIGNATION.search(name)
    if found is None:  # pragma: no cover - the walk yields only designated names
        return problems
    if kind == "function" and found.end() != len(name):
        problems.append(
            "a function carries its designation last (air_density_iso10534)"
        )
    if kind != "function" and found.start() != 0:
        problems.append(
            "a constant, a class or a field carries its designation first "
            "(EN12354_AIR, ARP866AAttenuation)"
        )
    return problems


def test_a_standard_designation_is_written_one_way_and_only_where_it_distinguishes() -> (
    None
):
    """``EN12354_AIR``, ``air_density_iso10534``: one form, and only where it tells.

    Where the module a name lives in already says which standard it follows,
    the designation is dropped (``metrology.REFERENCE_VALUES``, not
    ``ISO1683_REFERENCE_VALUES``). Where it tells two things apart, it stays,
    written one way: the body joined to its number, a part after an
    underscore, first in a constant, a class or a field and last in a
    function. :data:`_DESIGNATION_KEPT` names every one that stays and why.
    """
    offenders: list[str] = []
    found: set[str] = set()
    for key, name, kind in _designated_names():
        found.add(key)
        offenders += [
            f"{key}: {problem}" for problem in _designation_problems(name, kind)
        ]
        if key not in _DESIGNATION_KEPT:
            offenders.append(
                f"{key}: the module already says which standard this follows; "
                "drop the designation, or list the name in _DESIGNATION_KEPT "
                "with what it tells apart"
            )
    stale = sorted(set(_DESIGNATION_KEPT) - found)
    offenders += [f"{key}: listed in _DESIGNATION_KEPT and not found" for key in stale]
    assert not offenders, "\n".join(sorted(offenders))


@pytest.mark.parametrize(
    ("name", "kind", "expected"),
    [
        ("EN_12354_AIR", "constant", 1),
        ("iso_9613_ground_factor", "field", 1),
        ("itu_r_468_weighting", "function", 1),
        ("SAE_AIR1845_ATTENUATION_DB_PER_100M", "constant", 1),
        ("arp866a_attenuation", "function", 1),
        ("air_density_astm", "function", 1),
        ("COVERAGE_FACTOR_EN16487", "constant", 1),
        ("EN12354_AIR", "constant", 0),
        ("air_density_iso10534", "function", 0),
        ("plane_wave_frequency_range_astm_e2611", "function", 0),
        ("IEC61094_2_TABLE_C1", "constant", 0),
        ("ARP866AAttenuation", "class", 0),
    ],
)
def test_the_designation_rule_reads_a_name(name: str, kind: str, expected: int) -> None:
    assert len(_designation_problems(name, kind)) == expected


# --------------------------------------------------------------------------- #
# The two ends of a range come lower first
# --------------------------------------------------------------------------- #
#: The words that name the two ends of a range, upper word first.
_RANGE_ENDS = (("upper", "lower"), ("max", "min"), ("high", "low"))
_SPREADS = (
    "the spreads of the upper and the lower half of a distribution about its "
    "median, two parameters of one curve, not the two ends of a range"
)
#: Pairs kept upper first on purpose, keyed by location and the upper name,
#: each with its reason. An entry that matches nothing fails.
_RANGE_ORDER_EXEMPT: dict[str, str] = {
    "phonometry.hearing.hearing_protectors.HMLRatingResult.high": (
        "H, M and L of ISO 4869-2 are an ordered set the standard prints in "
        "that order, not the two ends of a range"
    ),
    "phonometry.hearing.hearing_protectors.HMLRatingResult.subject_high": (
        "the per-subject H, M and L, printed in the order of the rating"
    ),
    "phonometry.hearing.threshold.AgeThresholdResult.spread_upper": _SPREADS,
    "phonometry.hearing.noise_induced_hearing_loss.NIPTSResult.spread_upper": (
        _SPREADS
    ),
}


def _upper_before_lower(names: list[str]) -> list[tuple[str, str]]:
    """The ``(upper, lower)`` twins of *names* in which the upper comes first."""
    position = {name: index for index, name in enumerate(names)}
    found: list[tuple[str, str]] = []
    for name in names:
        words = name.split("_")
        for upper, lower in _RANGE_ENDS:
            if upper not in words:
                continue
            twin = "_".join(lower if word == upper else word for word in words)
            if position.get(twin, -1) > position[name]:
                found.append((name, twin))
    return found


def _ordered_members() -> Iterator[tuple[str, list[str]]]:
    """``(where, names)``: every public signature and record field list, in order."""
    seen: set[str] = set()
    for module in _public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported)
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("phonometry"):
                continue
            key = f"{owner}.{exported}"
            if key in seen:
                continue
            seen.add(key)
            if inspect.isclass(obj):
                if dataclasses.is_dataclass(obj):
                    yield key, [field.name for field in dataclasses.fields(obj)]
                for attribute, member in vars(obj).items():
                    if inspect.isfunction(member) and not attribute.startswith("_"):
                        yield (
                            f"{key}.{attribute}",
                            list(inspect.signature(member).parameters),
                        )
            elif inspect.isfunction(obj):
                yield key, list(inspect.signature(obj).parameters)


def test_the_two_ends_of_a_range_come_lower_first() -> None:
    """``plant_steady_reading(min_level, max_level)``, ``lower_`` before ``upper_``.

    The filter and weighting masks came ``(lower, upper)`` while the vibration
    tolerances came ``(upper, lower)``, and both arrays have the same shape, so
    a swap is silent. Every signature and every record field list puts the
    lower end first: ``lower`` before ``upper``, ``min`` before ``max``,
    ``low`` before ``high``.
    """
    offenders: list[str] = []
    found: set[str] = set()
    for where, names in _ordered_members():
        for upper, lower in _upper_before_lower(names):
            location = f"{where}.{upper}"
            found.add(location)
            if location not in _RANGE_ORDER_EXEMPT:
                offenders.append(f"{where}: {upper!r} comes before {lower!r}")
    offenders += [
        f"{location}: listed in _RANGE_ORDER_EXEMPT and not found"
        for location in sorted(set(_RANGE_ORDER_EXEMPT) - found)
    ]
    assert not offenders, "\n".join(sorted(offenders))


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["max_level", "min_level"], [("max_level", "min_level")]),
        (
            ["upper_tolerance_db", "lower_tolerance_db"],
            [("upper_tolerance_db", "lower_tolerance_db")],
        ),
        (["min_level", "max_level"], []),
        (["x", "fs", "high_hz"], []),
    ],
)
def test_the_range_order_rule_reads_a_list(
    names: list[str], expected: list[tuple[str, str]]
) -> None:
    assert _upper_before_lower(names) == expected


# ---------------------------------------------------------------------------
# A count's name stays out of the prose that says the plain noun
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent

#: A count parameter written where the sentence wants its noun: "the number
#: of n_planes", "Biquad n_sections". Renaming ``planes`` to ``n_planes`` with a
#: word-boundary pattern rewrites the noun in every sentence around it too.
_COUNT_AS_NOUN = re.compile(r"[A-Za-z]\s+(n_[a-z_]*[a-z]s)\b(?!\s*=)")

#: Spans that hold code or mathematics, where an identifier is what is meant,
#: and the field name a docstring opens a line with (``:param n_planes:``).
_CODE_SPANS = re.compile(
    r":math:`[^`]*`|``[^`]*``|`[^`]*`|\$[^$]*\$|^:\w+(?:\s+[\w.]+)?:"
)


def _prose_lines(text: str, *, docstring: bool) -> Iterator[str]:
    """The lines of ``text`` a reader reads as sentences, code spans removed.

    Fenced and displayed blocks (Markdown fences, ``$$``, ``.. math::`` and
    doctest lines) are skipped; inline code and inline mathematics are cut out.
    """
    fenced = False
    math_indent: int | None = None
    for line in text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if math_indent is not None and (not stripped or indent > math_indent):
            continue
        math_indent = None
        if stripped.startswith("$$") and stripped.count("$$") > 1:
            continue  # A display formula opened and closed on its own line.
        if stripped.startswith(("```", "$$")):
            fenced = not fenced
            continue
        if fenced or stripped.startswith(">>>"):
            continue
        if docstring and stripped.startswith(".. math::"):
            math_indent = indent
            continue
        yield _CODE_SPANS.sub(" ", stripped)


def _docstrings() -> Iterator[tuple[str, str]]:
    for path in sorted((_ROOT / "src" / "phonometry").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ) and (doc := ast.get_docstring(node, clean=True)):
                yield str(path.relative_to(_ROOT)), doc


#: The API pages generated from the docstrings, which the docstring half of the
#: test reads at their source. ``docs/reference/api/index.md`` is written by
#: hand and read with the guides.
_GENERATED_API = _ROOT / "site" / "src" / "content" / "docs" / "reference" / "api"


def _pages() -> Iterator[tuple[str, str]]:
    roots = (_ROOT / "docs", _ROOT / "site" / "src" / "content" / "docs")
    for root in roots:
        for path in sorted([*root.rglob("*.md"), *root.rglob("*.mdx")]):
            if _GENERATED_API not in path.parents:
                yield str(path.relative_to(_ROOT)), path.read_text(encoding="utf-8")


def count_names_written_as_nouns(text: str, *, docstring: bool) -> list[str]:
    """Every count parameter ``text`` writes where its sentence wants the noun."""
    return [
        match.group(1)
        for line in _prose_lines(text, docstring=docstring)
        for match in _COUNT_AS_NOUN.finditer(line)
    ]


def test_the_rule_tells_a_count_named_in_prose_from_one_used_as_a_noun() -> None:
    text = (
        "Measurements in ``n_planes`` n_planes through the reference.\n"
        ":param n_planes: The number of n_planes (Default: 2).\n"
        "Biquad n_sections, i.e. half the degree.\n"
        "Pass ``n_planes`` planes; the shape is (7, n_bands).\n"
        "```python\nr = f(x, n_axles=4)  # four n_axles\n```\n"
        "$$N = n_\\mathrm{a}$$\nThe number of n_axles per vehicle.\n"
        ".. math::\n\n    f(n_x, n_y) = n_points\n\nThe number of planes.\n"
    )
    assert count_names_written_as_nouns(text, docstring=True) == [
        "n_planes",
        "n_planes",
        "n_sections",
        "n_axles",
    ]


def test_a_count_name_never_stands_in_for_its_noun_in_prose() -> None:
    """The rename to ``n_<plural>`` stops at the identifier.

    "The number of n_planes" and "Number of n_axles per vehicle" are what a
    word-boundary rename of ``planes`` and ``axles`` leaves in the sentences
    around the parameter; the docstrings and the guides say the noun.
    """
    found = [
        f"{where}: {name}"
        for where, text, docstring in (
            *((w, t, True) for w, t in _docstrings()),
            *((w, t, False) for w, t in _pages()),
        )
        for name in count_names_written_as_nouns(text, docstring=docstring)
    ]
    assert found == []
