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
way its standard writes it, and the rule is about the bare concept.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
import re
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


def _public_names() -> Iterator[tuple[str, str, str, str]]:
    """``(where, name, annotation, kind)`` for every public field and parameter.

    ``kind`` is ``field``, ``property``, ``param`` or ``varargs``.
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


def _parameters(where: str, func: object) -> Iterator[tuple[str, str, str, str]]:
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
        )


def _class_names(where: str, cls: type) -> Iterator[tuple[str, str, str, str]]:
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            yield f"{where}.{field.name}", field.name, str(field.type), "field"
    elif "__init__" in vars(cls):
        yield from _parameters(f"{where}.__init__", vars(cls)["__init__"])
    for name, member in vars(cls).items():
        if name.startswith("_"):
            continue
        if isinstance(member, property) and member.fget is not None:
            annotation = str(member.fget.__annotations__.get("return", ""))
            yield f"{where}.{name}", name, annotation, "property"
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
        for where, name, _, _ in names
        if name in _MINORITY
    )
    assert not offenders, "\n".join(offenders)


def test_a_symbol_is_not_a_parameter_name_outside_the_solvers() -> None:
    """``c`` and ``rho`` are ``speed_of_sound`` and ``density`` by name."""
    offenders = sorted(
        f"{where}: {name!r} is {_SYMBOLS[name]!r} everywhere else"
        for where, name, _, kind in _public_names()
        if kind == "param"
        and name in _SYMBOLS
        and not where.startswith(_SYMBOL_EXEMPT_PACKAGES)
        and where not in _SYMBOL_EXEMPT
    )
    assert not offenders, "\n".join(offenders)


def test_an_array_of_a_quantity_is_named_in_the_plural() -> None:
    """``frequencies`` holds many, ``frequency`` one; the same for three more.

    Only an annotation that admits an array and nothing else is held to the
    plural, and only one that admits a number and nothing else to the
    singular: a vectorised argument that takes either is named for reading.
    """
    singular = {plural: one for one, plural in _PLURALS.items()}
    offenders: list[str] = []
    for where, name, annotation, kind in _public_names():
        shape = _kind(annotation)
        if name in _PLURALS and shape == "array":
            offenders.append(
                f"{where}: an array named {name!r}; use {_PLURALS[name]!r}"
            )
        elif name in singular and shape == "scalar" and kind != "varargs":
            offenders.append(
                f"{where}: one value named {name!r}; use {singular[name]!r}"
            )
    assert not offenders, "\n".join(sorted(offenders))
