#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public parameter that names a pressure, a temperature or a humidity
without saying which unit it is in.

A number the caller types is where a unit is lost, and the loss is silent: a
static pressure of 101 325 handed to a function that wants kilopascals is a
thousand times the atmosphere, and every result downstream is still a float.
No guard can catch that by magnitude, because both readings are legitimate
values of the same quantity elsewhere in this library, so the unit has to be
in the name, where the caller writes it and where a reader of the call site
can see it.

The rule is one line: a public parameter whose name says pressure, temperature
or humidity ends either in a unit (:data:`UNITS`) or in a suffix that says the
quantity carries no unit of its own (:data:`DIMENSIONLESS`, which covers the
decibel levels, the ratios and the indicators). Anything else keeps its unit
in the docstring, which is not where the mistake is made.

The surface is the one a caller reaches: every name in the ``__all__`` of every
public module, the public methods and properties of the classes among them, and
the fields a dataclass turns into keyword arguments. That is why this walks the
imported package rather than the source tree: :class:`ReportMetadata` is
published from the root and defined in a private module, and a scan by file
path would never see it.

:data:`EXEMPT` is the escape hatch, keyed by module, qualified name and
parameter, and each entry carries the reason it is one.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import pathlib
import pkgutil
import sys
from typing import TYPE_CHECKING, NamedTuple

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The quantities whose unit a caller can get wrong by a factor of a thousand
#: (kPa against Pa) or by 273 (degrees Celsius against kelvin).
QUANTITIES = ("pressure", "temperature", "humid")

#: The unit suffixes the tree uses. Every one of them is already in the
#: published API. ``_ft`` is here because a pressure altitude is a length: the
#: quantity a name says is not always the quantity it holds, and the unit still
#: has to be on it.
UNITS = ("_kpa", "_pa", "_inhg", "_percent", "_c", "_k", "_ft")

#: Suffixes that say the quantity has no unit of its own: a level is in
#: decibels and names its reference elsewhere, a ratio and an index are pure
#: numbers, a correction is the decibels one of them adds, and an indicator is
#: the difference of two levels that the ISO 9614 family names in decibels.
DIMENSIONLESS = (
    "_level",
    "_levels",
    "_index",
    "_indices",
    "_indicator",
    "_ratio",
    "_recovery",
    "_uncertainty",
    "_coefficient",
    "_correction",
    "_db",
    "_db_per_m",
)

#: Parameters that name a pressure and stay bare, with the reason. The one
#: shape that qualifies is an acoustic pressure: a waveform or a field, always
#: in pascals, and often a :class:`~phonometry.io.Signal` whose calibration
#: says so itself. There is no second unit anyone passes it in, so a suffix
#: would restate the type rather than resolve an ambiguity.
_ACOUSTIC = "acoustic pressure, always in pascals; a Signal carries its own calibration"
EXEMPT: dict[tuple[str, str, str], str] = {
    ("phonometry.underwater.acoustics", "sound_pressure_level", "pressure"): _ACOUSTIC,
    ("phonometry.underwater.acoustics", "sound_exposure_level", "pressure"): _ACOUSTIC,
    (
        "phonometry.underwater.acoustics",
        "peak_sound_pressure_level",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "single_strike_sel",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "strike_sel_spectrum",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "pile_strike_metrics",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "PileStrikeResult",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.propagation.numerical",
        "GaussianBeamResult",
        "pressure",
    ): _ACOUSTIC,
    ("phonometry.simulation.ntff", "ContourPhasors", "pressure"): _ACOUSTIC,
    ("phonometry.simulation.fdtd", "FDTDResult", "pressures"): _ACOUSTIC,
}


class Parameter(NamedTuple):
    """One public parameter, and where a reader finds it."""

    module: str
    qualname: str
    name: str
    where: str


def _is_public(name: str) -> bool:
    """Whether a module part, a definition or a parameter is public."""
    return not name.startswith("_")


def public_modules() -> Iterator[tuple[str, ModuleType]]:
    """Every module a caller can import by a public path, imported."""
    yield "phonometry", phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not all(_is_public(part) for part in found.name.split(".")):
            continue
        try:
            yield found.name, importlib.import_module(found.name)
        except ImportError:  # pragma: no cover - an optional backend
            continue


def _where(obj: object) -> str:
    """``path:line`` of a definition, or an empty string when it has none."""
    try:
        path = inspect.getsourcefile(obj)  # type: ignore[arg-type]
        line = inspect.getsourcelines(obj)[1]  # type: ignore[arg-type]
    except (OSError, TypeError):
        return ""
    if path is None:
        return ""
    return f"{pathlib.Path(path).resolve().relative_to(ROOT)}:{line}"


def _members(name: str, obj: object) -> Iterator[tuple[str, object]]:
    """One callable per name a caller can call: the object and its methods."""
    yield name, obj
    if not inspect.isclass(obj):
        return
    for attribute, member in vars(obj).items():
        if not _is_public(attribute):
            continue
        if isinstance(member, property) and member.fget is not None:
            yield f"{name}.{attribute}", member.fget
        elif inspect.isfunction(member):
            yield f"{name}.{attribute}", member


def public_parameters() -> Iterator[Parameter]:
    """Every parameter a caller can name in a call to the published API."""
    seen: set[tuple[str, str, str]] = set()
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if not callable(obj):
                continue
            for qualname, target in _members(exported, obj):
                if not callable(target):
                    continue
                try:
                    signature = inspect.signature(target)
                except (TypeError, ValueError):
                    continue
                home = getattr(target, "__module__", module_name)
                for parameter in signature.parameters:
                    if parameter in {"self", "cls"}:
                        continue
                    key = (home, qualname, parameter)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield Parameter(home, qualname, parameter, _where(target))


def names_a_quantity(name: str) -> bool:
    """Whether the parameter name says pressure, temperature or humidity."""
    return any(quantity in name.lower() for quantity in QUANTITIES)


def declares_its_unit(name: str) -> bool:
    """Whether the name ends in a unit or says it carries none."""
    lowered = name.lower()
    return lowered.endswith(UNITS) or lowered.endswith(DIMENSIONLESS)


def offenders() -> tuple[list[Parameter], list[tuple[str, str, str]]]:
    """The parameters that keep their unit off the name, and the stale exemptions."""
    found: list[Parameter] = []
    used: set[tuple[str, str, str]] = set()
    for parameter in public_parameters():
        if not names_a_quantity(parameter.name):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in EXEMPT:
            used.add(key)
        elif not declares_its_unit(parameter.name):
            found.append(parameter)
    stale = [key for key in EXEMPT if key not in used]
    return found, stale


def main() -> int:
    """Report every public parameter whose name hides its unit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    found, stale = offenders()
    if not found and not stale:
        print(
            "Every public pressure, temperature and humidity parameter names its unit."
        )
        return 0
    if found:
        print("::error::a public parameter names a quantity without its unit")
        print(f"{len(found)} parameter(s) keep the unit out of the name:")
        for parameter in sorted(found):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> end the name in one of "
            + ", ".join(UNITS)
            + ", or, if the quantity carries no unit, in one of "
            + ", ".join(DIMENSIONLESS)
            + "; an acoustic waveform goes in EXEMPT at the top of "
            "scripts/check_parameter_units.py with its reason."
        )
    for key in stale:
        print(f"::error::EXEMPT lists {key}, which no longer exists")
    return 1


if __name__ == "__main__":
    sys.exit(main())
