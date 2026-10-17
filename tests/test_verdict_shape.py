#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A verdict is spelled ``passes``, refuses a truth value, and has a judging verb.

Four rules, each read off the public API rather than off a list of names, so a
verdict added tomorrow is held to them too:

a. **No public name reads as a test.** pytest collects every function whose
   name starts with ``test`` and every class whose name starts with ``Test``
   from a module it imports, so ``from phonometry.noise_control import *`` in
   a user's test file used to collect ``test_environment_applicability`` and
   fail on a fixture it never asked for.
b. **A judgement carries its verb.** A public function, or a public method
   of a published class, that answers with a ``bool``, a tuple of them, a
   boolean array or a verdict record is named ``verify_`` (an instrument),
   ``assess_`` (a measured situation) or ``check_`` (the setup a method
   needs), as CONTRIBUTING sets out; and each of those returns a record, or
   ``None`` when the answer is only a warning. Two regime predicates stay,
   because CONTRIBUTING keeps a verb for a predicate: they say which procedure
   a clause selects, not whether anything passed. A method that tests
   membership or provenance, looks up one requirement of a verdict by its
   clause, or says how a value is reported answers no pass or fail either,
   and is keyed by location with its reason.
c. **A verdict refuses to stand in for a bool.** Every class a judging
   function returns, and every public class with a scalar ``passes``, defines
   a ``__bool__`` that raises ``TypeError``: ``if result:`` on a record is
   always true, so it would pass every failure. The rule is read from the
   source of the ``__bool__`` the class inherits, and then by calling it.
d. **One spelling for the overall flag.** The pass/fail of a verdict is
   ``passes``; ``complies``, ``satisfied``, ``all_satisfied``,
   ``acceptable`` and ``applicable`` are gone. A flag that is not a pass/fail
   stays under its own name, keyed here with the reason.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
import functools
import importlib
import inspect
import pkgutil
import re
import textwrap
import types
import typing
import warnings
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from numpy.typing import NDArray

import phonometry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: The prefixes of a judgement (CONTRIBUTING, "The three verbs of a judgement").
VERBS = ("verify_", "assess_", "check_")

#: Public callables that return a ``bool`` and keep a name without a judging
#: verb, keyed by location, each with its reason.
REGIME_PREDICATES = {
    "phonometry.building.measurement.low_frequency.low_frequency_procedure_applies": (
        "a regime predicate: ISO 16283-1 and -2 select the low-frequency "
        "procedure by the room volume; nothing is judged to pass or fail"
    ),
    "phonometry.psychoacoustics.quality._tone_audibility.resolve_tones_separately": (
        "a regime predicate: ISO/PAS 20065 Step 3 decides whether two tones in "
        "one critical band are rated apart or together; nothing passes or fails"
    ),
}

#: Public methods that return a ``bool`` or a verdict and keep a name without
#: a judging verb, keyed by location, each with its reason.
PREDICATE_METHODS = {
    "phonometry._internal.catalogue.CatalogueRow.is_approximate": (
        "provenance: whether the page printed a cell with a tilde; nothing is judged"
    ),
    "phonometry._internal.catalogue.CatalogueRow.is_derived": (
        "provenance: whether the library computed a cell the page did not print"
    ),
    "phonometry._report.metadata.ReportMetadata.is_empty": (
        "a container predicate: whether any report field was filled in"
    ),
    "phonometry.metrology.sound_calibrator.CalibratorTableRow.contains": (
        "membership: whether a frequency falls in the range of a printed row"
    ),
    "phonometry.metrology.sound_level_meter.MaxUncertaintyRow.contains": (
        "membership: whether a frequency falls in the range of a printed row"
    ),
    "phonometry.building.measurement.service_equipment.ServiceEquipmentResult.upper_limit": (
        "how to report: ISO 16032 Clause 9 asks whether a weighted value is an "
        "upper limit, which is not a pass or fail of the measurement"
    ),
    "phonometry.electroacoustics.induction_loop.InductionLoopVerification.requirement": (
        "an accessor: the requirement of a verdict already judged, looked up by "
        "its clause"
    ),
    "phonometry.metrology.sound_calibrator.SoundCalibratorVerification.requirement": (
        "an accessor: the requirement of a verdict already judged, looked up by "
        "its clause"
    ),
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicVerification.requirement": (
        "an accessor: the requirement of a verdict already judged, looked up by "
        "its clause"
    ),
    "phonometry.filters.periodic_tests.FilterPeriodicVerification.clause": (
        "an accessor: the test of a verdict already judged, looked up by its clause"
    ),
}

#: The spellings of an overall pass/fail that ``passes`` replaced.
RETIRED_FLAGS = ("complies", "satisfied", "all_satisfied", "acceptable", "applicable")

#: Flags a public record keeps under its own name, keyed by
#: ``(module.class, flag)``, each with its reason. They are read like the
#: retired spellings, so the vocabulary below lists them all and a new one
#: has to be argued here.
KEPT_FLAGS = {
    (
        "phonometry.vibration.structural.building_damage.DamageAssessment",
        "within_guideline",
    ): (
        "DIN 4150-3 5.1: exceeding a guideline value is not a failure, so the "
        "record says where the value sits, not whether it passed"
    ),
    (
        "phonometry.vibration.immission.vibration_meter.AssessmentVelocity",
        "within_guideline",
    ): ("DIN 4150-3 5.1, as DamageAssessment: a guideline, not a limit"),
    ("phonometry.emission.turbine_noise.TurbineSoundPowerResult", "conforms"): (
        "a magnitude result with a flag: the sound power is the answer, and the "
        "flag says whether the bins reach the coverage IEC 61400-11 asks for"
    ),
    ("phonometry.vibration.machinery.evaluation.OperationalChange", "significant"): (
        "ISO 20816-1 Annex D: a significant change is a reason to look, not a "
        "failure, like AttenuationDifferenceResult.significant"
    ),
}

#: Every name that reads as an overall flag of a verdict.
FLAG_VOCABULARY = (*RETIRED_FLAGS, "within_guideline", "conforms", "significant")

_RETURN_TEXT = re.compile(
    r":returns?:\s*(.*?)(?=\n\s*:(?:param|returns?|raises|rtype)\b|\Z)", re.DOTALL
)
_BOOLEAN_RETURN = re.compile(
    r"^(?:a\s+)?(?:boolean\b|``true``|true\b|whether\b)|\bboolean (?:array|mask)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Walking the public API
# --------------------------------------------------------------------------- #
def _public_modules() -> Iterator[types.ModuleType]:
    yield phonometry
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        yield importlib.import_module(info.name)


@functools.cache
def _published() -> dict[int, tuple[str, str, Any]]:
    """``id(obj) -> (published name, owner location, obj)`` for every public name."""
    found: dict[int, tuple[str, str, Any]] = {}
    for module in _public_modules():
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name)
            owner = getattr(obj, "__module__", "") or ""
            if not owner.startswith("phonometry"):
                continue
            location = f"{owner}.{getattr(obj, '__qualname__', name)}"
            found.setdefault(id(obj), (f"{module.__name__}.{name}", location, obj))
    return found


def _functions() -> list[tuple[str, str, Callable[..., Any]]]:
    return sorted(
        (where, location, obj)
        for where, location, obj in _published().values()
        if inspect.isfunction(obj)
    )


def _classes() -> list[tuple[str, str, type]]:
    return sorted(
        (where, location, obj)
        for where, location, obj in _published().values()
        if inspect.isclass(obj)
    )


@functools.cache
def _methods() -> list[tuple[str, str, Callable[..., Any]]]:
    """``(name, location, function)`` for every public method a published class defines.

    Properties are fields of the record, not callables, and are left to rule
    d; what a class inherits is read where it is defined.
    """
    found = []
    for _, _, cls in _classes():
        for name, member in vars(cls).items():
            if name.startswith("_"):
                continue
            func = (
                member.__func__
                if isinstance(member, (staticmethod, classmethod))
                else member
            )
            if inspect.isfunction(func):
                location = f"{cls.__module__}.{cls.__qualname__}.{name}"
                found.append((name, location, func))
    return sorted(found, key=lambda item: item[1])


class _Namespace(dict[str, Any]):
    """A module's globals, with the names it imports only for type checking."""

    def __missing__(self, key: str) -> object:
        if hasattr(builtins, key):
            return getattr(builtins, key)
        return _class_by_name().get(key, Any)


@functools.cache
def _class_by_name() -> dict[str, type]:
    return {obj.__name__: obj for _, _, obj in _classes()}


def _resolve(annotation: object, owner: object) -> object:
    """The object an annotation names, read in the namespace of *owner*."""
    if not isinstance(annotation, str):
        return annotation
    namespace = _Namespace(vars(inspect.getmodule(owner)))
    namespace.setdefault("np", np)
    namespace.setdefault("NDArray", NDArray)
    try:
        return eval(annotation, {}, namespace)  # noqa: S307 - annotations of our own source
    except (NameError, TypeError, SyntaxError):  # pragma: no cover - reported below
        return annotation


def _return_of(func: Callable[..., Any]) -> object:
    return _resolve(inspect.signature(func).return_annotation, func)


def _members(hint: object) -> tuple[object, ...]:
    """The alternatives of a union, or the hint itself, with ``None`` as its type."""
    if isinstance(hint, types.UnionType) or typing.get_origin(hint) is typing.Union:
        return typing.get_args(hint)
    return (type(None),) if hint is None else (hint,)


def _is_boolean_array(hint: object) -> bool:
    if typing.get_origin(hint) is not np.ndarray:
        return False
    args = typing.get_args(hint)
    dtype = typing.get_args(args[-1]) if args else ()
    return bool(dtype) and dtype[0] is np.bool_


def _raising_bool(cls: type) -> bool:
    """Whether the ``__bool__`` *cls* inherits raises ``TypeError``."""
    for klass in cls.__mro__:
        method = vars(klass).get("__bool__")
        if method is None:
            continue
        if not inspect.isfunction(method):
            return False
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and node.exc is not None:
                exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                if isinstance(exc, ast.Name) and exc.id == "TypeError":
                    return True
        return False
    return False


def _flag_annotation(cls: type, name: str) -> object | None:
    """The annotation of the field or property *name* of *cls*, if it has one."""
    member = inspect.getattr_static(cls, name, None)
    if isinstance(member, property) and member.fget is not None:
        return _resolve(member.fget.__annotations__.get("return"), member.fget)
    if isinstance(member, functools.cached_property):
        return _resolve(member.func.__annotations__.get("return"), member.func)
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            if field.name == name:
                return _resolve(field.type, cls)
    return None


def _has_scalar_passes(cls: type) -> bool:
    return _flag_annotation(cls, "passes") in (bool, bool | None)


def _is_verdict(hint: object) -> bool:
    """A class that carries a pass/fail: ``passes``, or a spelling it replaced."""
    return inspect.isclass(hint) and any(
        _flag_annotation(hint, flag) is not None for flag in ("passes", *RETIRED_FLAGS)
    )


def _judges(func: Callable[..., Any]) -> str | None:
    """What makes *func* a judgement, or ``None`` when it returns a magnitude."""
    hint = _return_of(func)
    for member in _members(hint):
        if member is bool:
            return "returns a bool"
        if typing.get_origin(member) is tuple and bool in typing.get_args(member):
            return f"returns {member}"
        if _is_boolean_array(member):
            return "returns a boolean array"
        if _is_verdict(member):
            return f"returns the verdict {member.__name__}"  # type: ignore[union-attr]
    match = _RETURN_TEXT.search(inspect.getdoc(func) or "")
    if match and _BOOLEAN_RETURN.search(" ".join(match.group(1).split())):
        return "documents a boolean return"
    return None


def _verb_returns() -> list[tuple[str, type]]:
    """``(where, class)`` for every class a judging function or method returns."""
    callables = [(where, func) for where, _, func in _functions()]
    callables += [(location, func) for _, location, func in _methods()]
    returned = []
    for where, func in callables:
        if where.rsplit(".", 1)[1].startswith(VERBS):
            returned.extend(
                (where, member)
                for member in _members(_return_of(func))
                if inspect.isclass(member) and member is not type(None)
            )
    return returned


# --------------------------------------------------------------------------- #
# a. No public name reads as a test
# --------------------------------------------------------------------------- #
def test_no_public_name_is_collected_by_pytest() -> None:
    offenders = sorted(
        where
        for where, _, _ in _published().values()
        if where.rsplit(".", 1)[1].startswith(("test", "Test"))
    )
    assert not offenders, (
        "pytest collects these from a user's test module; name them for what "
        "they answer:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------- #
# b. A judgement carries its verb, and a verb returns a record
# --------------------------------------------------------------------------- #
def test_every_judgement_is_named_with_its_verb() -> None:
    offenders = []
    for where, location, func in _functions():
        if where.rsplit(".", 1)[1].startswith(VERBS) or location in REGIME_PREDICATES:
            continue
        reason = _judges(func)
        if reason is not None:
            offenders.append(f"{where}: {reason}")
    assert not offenders, (
        "a public function that answers pass or fail is named verify_, assess_ "
        "or check_ and returns a record:\n" + "\n".join(offenders)
    )


def test_every_judging_verb_returns_a_record() -> None:
    offenders = []
    for where, _, func in _functions():
        if not where.rsplit(".", 1)[1].startswith(VERBS):
            continue
        hint = _return_of(func)
        if not all(
            member is type(None) or dataclasses.is_dataclass(member)
            for member in _members(hint)
        ):
            offenders.append(f"{where} -> {hint}")
    assert not offenders, (
        "a judgement carries its reasons: a record, or None for a warning "
        "only:\n" + "\n".join(offenders)
    )


def test_every_judging_method_is_named_with_its_verb() -> None:
    offenders = []
    for name, location, func in _methods():
        if name.startswith(VERBS) or location in PREDICATE_METHODS:
            continue
        reason = _judges(func)
        if reason is not None:
            offenders.append(f"{location}: {reason}")
    assert not offenders, (
        "a public method that answers pass or fail is named verify_, assess_ "
        "or check_ and returns a record; a predicate that judges nothing is "
        "argued in PREDICATE_METHODS:\n" + "\n".join(offenders)
    )


def test_every_judging_method_returns_a_record() -> None:
    offenders = []
    for name, location, func in _methods():
        if not name.startswith(VERBS):
            continue
        hint = _return_of(func)
        if not all(
            member is type(None) or dataclasses.is_dataclass(member)
            for member in _members(hint)
        ):
            offenders.append(f"{location} -> {hint}")
    assert not offenders, (
        "a judgement carries its reasons: a record, or None for a warning "
        "only:\n" + "\n".join(offenders)
    )


def test_every_exempt_method_still_exists() -> None:
    locations = {location for _, location, _ in _methods()}
    assert set(PREDICATE_METHODS) <= locations, sorted(
        set(PREDICATE_METHODS) - locations
    )


def test_every_regime_predicate_is_still_published() -> None:
    locations = {location for _, location, _ in _functions()}
    assert set(REGIME_PREDICATES) <= locations, sorted(
        set(REGIME_PREDICATES) - locations
    )


# --------------------------------------------------------------------------- #
# c. A verdict refuses to stand in for a bool
# --------------------------------------------------------------------------- #
def _verdict_classes() -> set[type]:
    """Every class a judging function returns, and every one with a ``passes``."""
    return {cls for _, cls in _verb_returns()} | {
        cls for _, _, cls in _classes() if _has_scalar_passes(cls)
    }


def test_every_verdict_refuses_a_truth_value() -> None:
    offenders = sorted(
        f"{cls.__module__}.{cls.__qualname__}"
        for cls in _verdict_classes()
        if not _raising_bool(cls)
    )
    assert not offenders, (
        "these have no __bool__ that raises TypeError, so `if result:` is always "
        "true:\n" + "\n".join(offenders)
    )


def test_a_built_verdict_refuses_a_truth_value() -> None:
    """``bool(result)`` raises on every verdict the result factories build."""
    import result_factories

    held = _verdict_classes()
    checked = []
    for name, factory in list(vars(result_factories).items()):
        if not (
            inspect.isfunction(factory)
            and factory.__module__ == result_factories.__name__
            and name.startswith("_")
        ):
            continue
        parameters = inspect.signature(factory).parameters.values()
        if any(p.default is p.empty and p.kind != p.VAR_KEYWORD for p in parameters):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = factory()
        if type(result) not in held:
            continue
        with pytest.raises(TypeError, match="has no truth value"):
            bool(result)
        checked.append(type(result).__name__)
    assert checked


# --------------------------------------------------------------------------- #
# d. One spelling for the overall flag
# --------------------------------------------------------------------------- #
def test_the_overall_flag_is_spelled_passes() -> None:
    offenders = []
    for _, location, cls in _classes():
        for flag in FLAG_VOCABULARY:
            annotation = _flag_annotation(cls, flag)
            if annotation is None:
                continue
            if flag not in RETIRED_FLAGS and annotation not in (bool, bool | None):
                continue  # a per-band mask under a kept name is not an overall flag
            if (location, flag) in KEPT_FLAGS:
                continue
            offenders.append(f"{location}.{flag}")
    assert not offenders, (
        "the pass/fail of a verdict is `passes`; a flag that is not one is "
        "argued in KEPT_FLAGS:\n" + "\n".join(sorted(offenders))
    )


def test_every_kept_flag_still_exists() -> None:
    by_location = {location: cls for _, location, cls in _classes()}
    missing = [
        f"{location}.{flag}"
        for location, flag in KEPT_FLAGS
        if location not in by_location
        or _flag_annotation(by_location[location], flag) is None
    ]
    assert not missing, missing


def _qualname(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


@pytest.mark.parametrize(
    "cls", sorted(_verdict_classes(), key=_qualname), ids=_qualname
)
def test_the_bool_of_every_verdict_raises(cls: type) -> None:
    """Each class's own ``__bool__``, called on a bare instance, refuses."""
    bare = object.__new__(cls)
    with pytest.raises(TypeError, match="has no truth value"):
        bool(bare)


def _railway_change() -> object:
    from phonometry import vibration

    return vibration.assess_railway_change(
        kb_fmax_before=0.3,
        kb_fmax_after=0.3,
        kb_ftr_before=0.05,
        kb_ftr_after=0.05,
        guide=vibration.railway_guide_values("residential"),
    )


def _activity() -> object:
    from phonometry import environment

    phases = {
        "day": [
            environment.NoisePhase(2.0, 0.0),
            environment.NoisePhase(6.0, 50.0, kt=6.0, kf=3.0),
            environment.NoisePhase(4.0, 48.0, kt=3.0, kf=3.0),
        ]
    }
    return environment.assess_activity(
        phases, environment.activity_limits("a"), operating_days=303
    )


def _db_hr() -> object:
    from phonometry import building

    facade = building.db_hr_facade_requirement(62.0, "residential", "bedrooms")
    return building.assess_db_hr([(33.0, facade)])


def _band_flatness() -> object:
    from phonometry import noise_control

    return noise_control.check_band_flatness(
        [80.0, 80.0, 80.0, 70.0, 70.0, 70.0],
        frequencies=[100.0, 125.0, 160.0, 200.0, 250.0, 315.0],
    )


def _intensity_class() -> object:
    from phonometry import emission

    frequencies, class1, _ = emission.residual_index_limits("probe")
    return emission.verify_intensity_class(
        class1 + 1.0, frequencies=frequencies, device="probe"
    )


#: Real instances of the verdicts and judging results this module holds,
#: each built through the public call a user would write.
_BUILT: dict[str, Callable[[], object]] = {
    "AircraftSystemComplianceResult": lambda: (
        phonometry.aircraft.verify_aircraft_noise_system(
            directional={4000.0: {30: 0.4, 60: 0.9, 90: 1.9, 120: 2.4, 150: 2.4}}
        )
    ),
    "ActivityAssessment": _activity,
    "PeriodAssessment": lambda: _activity().periods[0],  # type: ignore[attr-defined]
    "BandFlatnessCheck": _band_flatness,
    "BackgroundMarginCheck": lambda: phonometry.room.check_background_margin(
        [80.0, 75.0], [70.0, 60.0]
    ),
    "BackgroundNoiseAssessment": lambda: (
        phonometry.electroacoustics.assess_background_noise([-40.0, -38.0])
    ),
    "BasePlateScatteringCheck": lambda: (
        phonometry.materials.check_base_plate_scattering([0.02] * 18)
    ),
    "CeilingSpecimenCheck": lambda: phonometry.materials.check_ceiling_specimen(
        area=10.8, depth_mm=200.0, deflection_mm=3.0
    ),
    "DBHRAssessment": _db_hr,
    "DBHRCheck": lambda: _db_hr().checks[0],  # type: ignore[attr-defined]
    "DamageAssessment": lambda: phonometry.vibration.assess_building_vibration(
        3.0, building_class="commercial", frequency_hz=50.0
    ),
    "EnclosureTestEnvironmentCheck": lambda: (
        phonometry.noise_control.check_enclosure_test_environment(
            base_standard="ISO 3744",
            mean_absorption_coefficient=0.3,
            room_surface_area_m2=400.0,
            measurement_surface_area_m2=20.0,
        )
    ),
    "FieldStationarityCheck": lambda: phonometry.emission.field_indicators(
        np.full(4, 80.0), np.full(4, 1.0e-5), temporal_intensity=np.full(10, 1.0e-5)
    ).check_field_stationarity(),
    "FilterComplianceResult": lambda: phonometry.filters.verify_filter_class(
        phonometry.filters.OctaveFilterBank(
            fs=48000, fraction=1, order=6, limits=[125, 4000]
        )
    ),
    "FixtureIsolationVerification": lambda: phonometry.hearing.verify_fixture_isolation(
        np.full(22, 120.0), np.full(22, 60.0)
    ),
    "IntensityInstrumentComplianceResult": _intensity_class,
    "LimpFrameCheck": lambda: phonometry.materials.check_limp_frame(20.0e3),
    "MountingCheck": lambda: phonometry.vibration.check_loose_mounting(
        3.0, 50.0, direction="vertical"
    ),
    "OperationalChange": lambda: phonometry.vibration.assess_operational_change(
        0.8, 2.8
    ),
    "PeopleAssessment": lambda: phonometry.vibration.assess_people_in_buildings(
        0.1, phonometry.vibration.guide_values("residential")
    ),
    "PerceptibleDifference": lambda: phonometry.room.assess_perceptible_difference(
        "C80", 0.0, 2.0
    ),
    "PredictionDetailCheck": lambda: phonometry.room.check_prediction_detail(
        "1", room_detail=3, fitting_detail=1, source_detail=1
    ),
    "QuasiPeakDynamicsResult": lambda: phonometry.broadcast.verify_quasi_peak_dynamics(
        48000.0
    ),
    "RailwayChange": _railway_change,
    "RequirementConformity": lambda: phonometry.building.assess_requirement_conformity(
        52.0, 1.5, 50.0, bound="minimum"
    ),
    "ShortDistanceCheck": lambda: phonometry.environment.check_short_distance(
        source_height_m=0.5,
        receiver_height_m=1.5,
        barrier_height_m=3.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=20.0,
    ),
    "SourcePositionCheck": lambda: phonometry.noise_control.check_source_positions(
        np.vstack([np.linspace(20.0, 40.0, 8) + shift for shift in (0.0, 1.0, -1.0)])
    ),
    "StrongCouplingCheck": lambda: phonometry.building.check_strong_coupling(
        [4.0, 2.0], 20.0, 20.0, 100.0, 100.0
    ),
    "TonalAssessmentResult": lambda: phonometry.environment.assess_tonal_audibility(
        54.1, 45.2, 430.0
    ),
    "TonalSurveyAssessment": lambda: phonometry.environment.assess_tonal_survey(
        [40.0, 60.0, 40.0], frequencies=[100.0, 125.0, 160.0]
    ),
    "ToneAudibilityResult": lambda: phonometry.psychoacoustics.assess_tones(
        [40.0], [50.0], 2.7, tone_frequencies=[200.0]
    ),
    "WeightingComplianceResult": lambda: phonometry.filters.verify_weighting_class(
        phonometry.filters.WeightingFilter(48000, "B")
    ),
    "WeightingVerification": lambda: phonometry.vibration.verify_weighting(
        "Wk", [1.0, 1.0, 1.0], frequencies=[4.0, 8.0, 16.0]
    ),
}


@pytest.mark.parametrize("name", sorted(_BUILT))
def test_a_real_verdict_refuses_a_truth_value(name: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = _BUILT[name]()
    assert type(result).__name__ == name
    with pytest.raises(TypeError, match="has no truth value"):
        bool(result)
