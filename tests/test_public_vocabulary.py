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

import pytest

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

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
    retired = {**_MINORITY, **_SIGNAL_SPELLINGS}
    spellings |= {old for old, new in retired.items() if new == parameter}
    tokens = parameter.split("_")
    if "n" in tokens[:2] and tokens[-1] != "n":
        spellings.add("_".join(t for t in tokens if t != "n"))
    if {"min", "max"} & set(tokens):
        spellings.add(
            "_".join({"min": "minimum", "max": "maximum"}.get(t, t) for t in tokens)
        )
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

    ``require_1d_signal(x)`` with a defaulted ``name="signal"`` tells the
    caller of a function that takes ``x`` that its ``signal`` is wrong.
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
                    _named_in(function)
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

    One spelling per word across the library: ``mic``, ``lab`` and ``std``
    are spelled out, a count is ``n_<plural>`` (never ``num_points``,
    ``point_count`` or ``numtaps``), and ``minimum`` and ``maximum`` are
    written ``min`` and ``max`` in every public name, ``MIN``/``MAX`` in a
    constant and ``Min``/``Max`` in a class, as numpy, SciPy, scikit-learn
    and Matplotlib write them (``max_iter``, ``min_samples_leaf``,
    ``vmax``) and as the standards write the maximum and minimum levels
    Lmax and Lmin. A maximum in decibels is the maximum level, ``max_level``,
    never a bare ``max_db``. A confidence bound is ``confidence_lower`` or
    ``confidence_upper``, so ``ci`` is a word of no public name, the ISO 717-2
    adaptation term C_I aside.
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
    for module in _public_modules():
        path = module.__name__  # type: ignore[attr-defined]
        leaf = path.rsplit(".", 1)[-1]
        offenders += [
            f"{path}: {problem}" for problem in _spelling_problems(leaf, kind="module")
        ]
    assert not offenders, "\n".join(sorted(set(offenders)))


def test_every_kept_spelling_still_exists() -> None:
    """An exemption from the spelling rules that names nothing is a stale one."""
    found = {where for where, *_ in _public_names()} | {
        where for where, *_ in _module_names()
    }
    stale = sorted(set(_SPELLING_EXEMPT) - found)
    assert not stale, "\n".join(stale)


@pytest.mark.parametrize(
    ("name", "kind", "annotation", "expected"),
    [
        ("mic_calibration_factor", "function", "", ["'mic' is spelled 'microphone'"]),
        ("LabInsulationWarning", "class", "", ["'lab' is spelled 'laboratory'"]),
        ("lab_insulation", "module", "", ["'lab' is spelled 'laboratory'"]),
        ("delay_std", "field", "float", ["'std' is spelled 'standard_deviation'"]),
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
    "phonometry.signals.test_signals.ToneBurstResult.burst_samples": _SAMPLES,
    "phonometry.signals.test_signals.ToneBurstResult.period_samples": _SAMPLES,
    "phonometry.simulation.elastic_fdtd.ElasticBoundaries.absorbing_layer_cells": (
        "the thickness of the absorbing layer counted in grid cells: the unit "
        "is the cell, as the sample is of delay_samples"
    ),
    "phonometry.simulation.fdtd.fdtd_simulation(absorbing_layer_cells)": (
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


#: A parameter that names the time signal in a spelling the API retired.
_SIGNAL_SPELLINGS = {"signal": "x", "signal_in": "x"}


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
