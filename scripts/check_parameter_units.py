#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public parameter that names a quantity without saying which unit
it is in.

A number the caller types is where a unit is lost, and the loss is silent: a
static pressure of 101 325 handed to a function that wants kilopascals is a
thousand times the atmosphere, and every result downstream is still a float.
No guard can catch that by magnitude, because both readings are legitimate
values of the same quantity elsewhere in this library, so the unit has to be
in the name, where the caller writes it and where a reader of the call site
can see it.

The rule is one line: a public parameter whose name says one of the quantities
this tree has written in two units (:data:`QUANTITIES` and
:data:`WORD_QUANTITIES`) ends either in a unit (:data:`UNITS`) or in a suffix
that says the quantity carries no unit of its own (:data:`DIMENSIONLESS`, which
covers the decibel levels, the ratios and the indicators). Anything else keeps
its unit in the docstring, which is not where the mistake is made.

The surface is the one a caller reaches: every name in the ``__all__`` of every
public module, the public methods and properties of the classes among them, and
the fields a dataclass turns into keyword arguments. That is why this walks the
imported package rather than the source tree: :class:`ReportMetadata` is
published from the root and defined in a private module, and a scan by file
path would never see it.

The second half of the rule is where the name has to appear: a parameter under
the rule that carries a default is keyword-only, so the number cannot be
written as a bare positional argument with the name nowhere on the line.

:data:`EXEMPT` is the escape hatch for the first half and :data:`POSITIONAL`
for the second, both keyed by module, qualified name and parameter, and each
entry carries the reason it is one.
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
#: (kPa against Pa), by 273 (degrees Celsius against kelvin) or by 57 (degrees
#: against radians). A quantity earns its place here by having had two units
#: competing for one name in this tree, which is what makes the mistake
#: silent; the ones that only ever had one unit are not listed, because a
#: suffix there would restate the convention rather than resolve anything.
#:
#: ``pressure``, ``temperature`` and ``humid`` are matched anywhere in a name.
#: The geometric ones are matched as whole words inside it, so ``critical_angle``
#: and ``duct_diameter`` are held to the rule and ``triangles`` is not.
QUANTITIES = ("pressure", "temperature", "humid")

#: Matched as a word of the name, split on underscores.
WORD_QUANTITIES = frozenset(
    {"diameter", "angle", "angles", "period", "periods", "gradient"}
)

#: The unit suffixes the tree uses. Every one of them is already in the
#: published API. ``_ft`` is here because a pressure altitude is a length: the
#: quantity a name says is not always the quantity it holds, and the unit still
#: has to be on it.
UNITS = (
    "_kpa",
    "_pa",
    "_inhg",
    "_percent",
    "_c",
    "_k",
    "_ft",
    "_mm",
    "_m",
    "_rad",
    "_deg",
    "_sr",
    "_s",
    "_per_s",
    "_np_per_rad",
    "_min",
    "_hours",
)

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
    # An evaluation period is not a length of time here: it is which of the
    # three the assessment is about, or the assessments themselves.
    (
        "phonometry.environment.assessment.spain",
        "PeriodAssessment",
        "period",
    ): 'the label "day", "evening" or "night", not a duration',
    (
        "phonometry.environment.assessment.spain",
        "ActivityAssessment",
        "periods",
    ): "the per-period assessments themselves, one result object each",
    (
        "phonometry.environment.assessment.rating",
        "composite_rating_level",
        "periods",
    ): "(level, hours, adjustment) triples; each carries its own unit",
    # Counts and waveforms built on the word, not quantities in its unit.
    (
        "phonometry.signals.synchronous_average",
        "SynchronousAverageResult",
        "period_waveform",
    ): "the averaged waveform itself, in the unit of the record it came from",
    (
        "phonometry.signals.synchronous_average",
        "SynchronousAverageResult",
        "samples_per_period",
    ): "a count of samples, which is what the name already says",
    (
        "phonometry.signals.test_signals",
        "ToneBurstResult",
        "period_samples",
    ): "a count of samples, which is what the name already says",
    # The bearing formulae use the two diameters as a ratio d/D, so the unit
    # cancels and the docstring asks only that both be the same one.
    (
        "phonometry.vibration.machinery.diagnostics",
        "bearing_fault_frequencies",
        "element_diameter",
    ): "d of the ratio d/D; any unit, as long as it matches pitch_diameter",
    (
        "phonometry.vibration.machinery.diagnostics",
        "bearing_fault_frequencies",
        "pitch_diameter",
    ): "D of the ratio d/D; any unit, as long as it matches element_diameter",
}


#: Conditions that keep their positional slot, with the reason. The bar is a
#: signature the caller cannot reach any other way, not a call site that would
#: be tedious to update.
POSITIONAL: dict[tuple[str, str, str], str] = {
    (
        "phonometry.metrology.calibration",
        "sensitivity",
        "reference_pressure_pa",
    ): (
        "the positional form is part of the Signal overload contract of this "
        "function, so it moves with that contract and not with a sweep of the "
        "ambient conditions"
    ),
}


class Parameter(NamedTuple):
    """One public parameter, and where a reader finds it."""

    module: str
    qualname: str
    name: str
    where: str
    positional_with_default: bool = False
    #: The annotation as written, so a sibling guard can read the type off it
    #: without walking the API a second time.
    annotation: str = ""
    #: ``True`` when a caller can still pass this one by position.
    positional: bool = False


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
                params = list(signature.parameters.values())
                for position, parameter in enumerate(params):
                    if parameter.name in {"self", "cls"}:
                        continue
                    key = (home, qualname, parameter.name)
                    if key in seen:
                        continue
                    seen.add(key)
                    # The second half of the rule: a condition that carries a
                    # default and is not what the call is about should be
                    # written by name. Three bare numbers in a row is the
                    # order nobody remembers.
                    loose = (
                        position > 0
                        and parameter.default is not inspect.Parameter.empty
                        and parameter.kind is parameter.POSITIONAL_OR_KEYWORD
                    )
                    annotation = parameter.annotation
                    declared = (
                        "" if annotation is inspect.Parameter.empty else str(annotation)
                    )
                    yield Parameter(
                        home,
                        qualname,
                        parameter.name,
                        _where(target),
                        loose,
                        declared,
                        parameter.kind is parameter.POSITIONAL_OR_KEYWORD,
                    )


def names_a_quantity(name: str) -> bool:
    """Whether the parameter name says one of the quantities under the rule."""
    lowered = name.lower()
    if set(lowered.split("_")) & WORD_QUANTITIES:
        return True
    return any(quantity in lowered for quantity in QUANTITIES)


def declares_its_unit(name: str) -> bool:
    """Whether the name ends in a unit or says it carries none."""
    lowered = name.lower()
    return lowered.endswith(UNITS) or lowered.endswith(DIMENSIONLESS)


def offenders() -> tuple[list[Parameter], list[Parameter], list[tuple[str, str, str]]]:
    """The unnamed units, the ones a caller can still pass by position, and stale keys."""
    unnamed: list[Parameter] = []
    loose: list[Parameter] = []
    used: set[tuple[str, str, str]] = set()
    for parameter in public_parameters():
        if not names_a_quantity(parameter.name):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in EXEMPT or key in POSITIONAL:
            used.add(key)
            if key in POSITIONAL and not declares_its_unit(parameter.name):
                unnamed.append(parameter)
            continue
        if not declares_its_unit(parameter.name):
            unnamed.append(parameter)
        # Only the dimensional half: a level, a ratio or an index carries no
        # unit to get wrong, so nothing is lost by passing one by position.
        if parameter.positional_with_default and parameter.name.lower().endswith(UNITS):
            loose.append(parameter)
    stale = [k for k in (*EXEMPT, *POSITIONAL) if k not in used]
    return unnamed, loose, stale


def main() -> int:
    """Report every public parameter whose name hides its unit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    unnamed, loose, stale = offenders()
    if not unnamed and not loose and not stale:
        print("Every public parameter under the rule names its unit and asks for it.")
        return 0
    if unnamed:
        print("::error::a public parameter names a quantity without its unit")
        print(f"{len(unnamed)} parameter(s) keep the unit out of the name:")
        for parameter in sorted(unnamed):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> end the name in one of "
            + ", ".join(UNITS)
            + ", or, if the quantity carries no unit, in one of "
            + ", ".join(DIMENSIONLESS)
            + "; an acoustic waveform goes in EXEMPT at the top of "
            "scripts/check_parameter_units.py with its reason."
        )
    if loose:
        print("::error::a public condition can still be passed as a bare number")
        print(f"{len(loose)} parameter(s) carry a default and stay positional:")
        for parameter in sorted(loose):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> put a bare '*' before it in the signature, or KW_ONLY before "
            "the field, so the unit in the name is written at the call site; "
            "a signature that has to keep its positional form goes in "
            "POSITIONAL with the reason."
        )
    for key in stale:
        print(f"::error::EXEMPT or POSITIONAL lists {key}, which no longer exists")
    return 1


if __name__ == "__main__":
    sys.exit(main())
