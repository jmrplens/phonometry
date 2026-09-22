#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a published constant that a caller can change in place.

A module-level table is shared by every caller in the process. If it is a
``dict``, ``PUBLISHED_RESILIENT_LAYERS["cork"] = ...`` replaces a printed row
for everybody who reads it afterwards; if it is a writeable array,
``OCTAVE_BANDS *= 2`` moves every band of every function that defaults to it.
Neither raises, and neither is visible at the place where the wrong number is
finally read. An annotation saying ``Mapping`` does not help: the type checker
reads it, the interpreter does not, and a ``dict`` behind it stays editable.

The rule: every value a caller reaches by a public name of a public module is
immutable all the way down. A dictionary is published as a
:class:`types.MappingProxyType`, a sequence as a tuple, a set as a frozenset,
and an array through ``phonometry._internal.frozen.read_only``. The walk goes
into the values of a mapping, the items of a tuple or frozenset and the fields
of a dataclass instance, because a proxy around a dictionary of dictionaries
still hands out the inner ones, and a frozen dataclass still holds whatever
mutable container it was built with. A dataclass instance that is not frozen
is itself an offence: its fields can be rebound.

This walks the imported package rather than the source tree for the same
reason ``check_parameter_units.py`` does: what a caller reaches is decided by
imports and re-exports, and a constant built by a function call only shows
its type once it exists.

:data:`EXEMPT` is the escape hatch, keyed by module and name, and each entry
carries the reason it is one.
"""

from __future__ import annotations

import argparse
import dataclasses
import enum
import importlib
import inspect
import pkgutil
import sys
import types
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from typing import TYPE_CHECKING, NamedTuple

import numpy as np

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator

#: Published names that may stay mutable, keyed by ``(module, name)``, each
#: with the reason. Empty: nothing published needs to be edited in place.
EXEMPT: dict[tuple[str, str], str] = {}

#: The containers a caller can change in place. The abstract classes catch the
#: builtins and their relatives alike (``UserDict``, ``ChainMap``, ``deque``).
_MUTABLE = (
    MutableMapping,
    MutableSequence,
    MutableSet,
    bytearray,
    types.SimpleNamespace,
)


class Offence(NamedTuple):
    """One mutable object reachable from a published name."""

    module: str
    name: str
    path: str
    kind: str


def _is_public(name: str) -> bool:
    """Whether a module part or a name is public."""
    return not name.startswith("_")


def public_modules() -> Iterator[tuple[str, types.ModuleType]]:
    """Every module a caller can import by a public path, imported."""
    yield "phonometry", phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not all(_is_public(part) for part in found.name.split(".")):
            continue
        try:
            yield found.name, importlib.import_module(found.name)
        except ImportError:  # pragma: no cover - an optional backend
            continue


def published(module: types.ModuleType) -> Iterator[tuple[str, object]]:
    """``(name, value)`` for every public value *module* hands a caller.

    The names are those bound in the module and those its ``__all__`` lists,
    so a name served by a module-level ``__getattr__`` is read too.
    """
    names = set(vars(module)) | set(getattr(module, "__all__", ()))
    for name in sorted(names):
        if not _is_public(name):
            continue
        try:
            value = getattr(module, name)
        except AttributeError:
            continue
        if _is_value(value):
            yield name, value


def _is_value(obj: object) -> bool:
    """Whether *obj* is data a caller reads, not code or a namespace."""
    return not (
        inspect.ismodule(obj)
        or inspect.isclass(obj)
        or inspect.isroutine(obj)
        or isinstance(obj, (property, staticmethod, classmethod))
    )


def mutable_parts(value: object, path: str) -> Iterator[tuple[str, str]]:
    """``(path, kind)`` for every part of *value* that can be changed in place.

    :param value: The published object.
    :param path: How a caller spells it, extended as the walk goes down.
    """
    seen: set[int] = set()

    def walk(obj: object, where: str) -> Iterator[tuple[str, str]]:
        if id(obj) in seen or isinstance(obj, (str, bytes, enum.Enum)):
            return
        seen.add(id(obj))
        if isinstance(obj, np.ndarray):
            if obj.flags.writeable:
                yield where, "writeable ndarray"
            return
        is_record = dataclasses.is_dataclass(obj) and not isinstance(obj, type)
        if isinstance(obj, _MUTABLE):
            yield where, type(obj).__name__
        elif is_record and not type(obj).__dataclass_params__.frozen:  # type: ignore[attr-defined]
            yield where, f"{type(obj).__name__} (dataclass, not frozen)"
        if isinstance(obj, Mapping):
            for key, item in obj.items():
                yield from walk(item, f"{where}[{key!r}]")
        elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, range):
            for index, item in enumerate(obj):
                yield from walk(item, f"{where}[{index}]")
        elif is_record:
            for field in dataclasses.fields(obj):  # type: ignore[arg-type]
                yield from walk(getattr(obj, field.name), f"{where}.{field.name}")

    yield from walk(value, path)


def offenders(
    modules: Iterator[tuple[str, types.ModuleType]] | None = None,
    exempt: Mapping[tuple[str, str], str] = EXEMPT,
) -> tuple[list[Offence], list[tuple[str, str]]]:
    """Every mutable part of a published value, and every stale exemption.

    One object published under several names (a table and the package that
    re-exports it) is reported once, under the first name the walk meets, and
    an exemption covers the object under every name it goes by.

    :param modules: ``(dotted name, module)`` pairs to inspect; the public
        modules of the installed package when omitted.
    :param exempt: The escape hatch, keyed by ``(module, name)``.
    :return: The offences, and the exemptions that no longer excuse anything:
        the name is gone, or what it holds can no longer be changed.
    """
    entries = [
        (module_name, name, value)
        for module_name, module in (
            modules if modules is not None else public_modules()
        )
        for name, value in published(module)
    ]
    by_key = {(module_name, name): value for module_name, name, value in entries}
    excused = {id(by_key[key]) for key in exempt if key in by_key}
    stale = sorted(
        key
        for key in exempt
        if key not in by_key or not any(mutable_parts(by_key[key], key[1]))
    )
    found: list[Offence] = []
    reported: set[int] = set()
    for module_name, name, value in entries:
        if id(value) in excused or id(value) in reported:
            continue
        parts = list(mutable_parts(value, name))
        if parts:
            reported.add(id(value))
        found.extend(Offence(module_name, name, path, kind) for path, kind in parts)
    return found, stale


def main() -> int:
    """Report every published value a caller can change in place."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    found, stale = offenders()
    if not found and not stale:
        print("Every published constant is immutable all the way down.")
        return 0
    if found:
        print("::error::a published constant can be changed in place")
        print(f"{len(found)} mutable part(s) reachable from a public name:")
        for offence in sorted(found):
            print(f"  {offence.module}: {offence.path}  <- {offence.kind}")
        print(
            "  -> publish a dict as types.MappingProxyType (inner ones too), a "
            "list as a tuple, a set as a frozenset, and an array through "
            "phonometry._internal.frozen.read_only; a value that has to stay "
            "editable goes in EXEMPT at the top of "
            "scripts/check_frozen_constants.py with its reason."
        )
    for key in stale:
        print(
            f"::error::EXEMPT lists {key}, which is no longer published or no "
            "longer mutable"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
