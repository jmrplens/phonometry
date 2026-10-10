#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A scalar guard refuses an array on every numpy, not on the ones that refuse it.

``float(np.array([54.0]))`` is ``54.0`` with a ``DeprecationWarning`` on numpy
2.0 to 2.3 and a ``TypeError`` from 2.4 on. A guard that left the refusal of a
per-band array to :func:`float` (or to :mod:`math`, which converts the same
way) therefore took a one-element array as a number on the oldest numpy the
package supports and refused it on the newest. ISO 354's relative humidity
was found that way, by the suite run at the dependency floors.

The tests here hold the class, on whatever numpy runs them:

* :class:`_ConvertsLikeNumpy20` is a one-element array that converts to a
  Python number the way numpy 2.0 still did, so the behaviour of the old floor
  is reproduced on the newest release and a guard that relies on the
  conversion fails here as it failed there;
* every guard that was read, and a public call into each kind of guard, is
  called with it and with a plain one-element array, after the number it
  wraps has been shown to pass, and has to answer with its own ``ValueError``;
* four structural rules read ``src`` with :mod:`ast` so that the next guard
  cannot be written the old way: no ``float()`` or ``int()`` whose
  ``TypeError`` is caught as the refusal, no private scalar guard that opens
  on a conversion without asking the rank, no ``float()`` around the value
  handed to a shared scalar guard (it converts before the guard can look),
  and no guard anywhere, public or private, that reads a parameter or a
  dataclass field through ``float()``, ``int()`` or :mod:`math` without the
  rank of that value settled in the same function.

What a rule cannot see is a guard that only compares its parameter and a
conversion in another function it hands the value to; the ISO 9613-1
humidity was one, and is held by the public calls instead.
"""

from __future__ import annotations

import ast
import importlib
import types
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import (
    aircraft,
    building,
    emission,
    environment,
    hearing,
    materials,
    noise_control,
    psychoacoustics,
    room,
    underwater,
    vibration,
)
from phonometry._internal import validation
from phonometry.filters import OctaveFilterBank

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

SRC = Path(__file__).resolve().parent.parent / "src" / "phonometry"

#: The helpers that ask a value for its rank before reading it as a number.
_RANK_HELPERS = frozenset({"is_scalar", "require_real", "require_scalar"})

#: The shared scalar guards of :mod:`phonometry._internal.validation`, which
#: check the rank themselves and so must receive the caller's value as it is.
_SHARED_GUARDS = frozenset(
    {
        "require_positive",
        "require_finite",
        "require_non_negative",
        "require_above_absolute_zero",
        "require_fraction",
    }
)

#: The conversions that read a value as one number.
#: (``np.isfinite`` is not one: it answers an array with an array, on every
#: numpy, and the helpers that call it on their first argument take arrays.)
_CONVERSIONS = frozenset({"float", "int", "math.isfinite", "math.isnan"})


class _ConvertsLikeNumpy20(np.ndarray):
    """A one-element array that converts to a Python number, as numpy 2.0 did.

    numpy 2.4 refuses ``float()`` and ``int()`` of an array with any axis;
    2.0 to 2.3 return its one element. Overriding the two conversions brings
    the old behaviour to whichever numpy runs the suite, so a guard that
    relies on the conversion to refuse an array is caught on every install.
    """

    def __float__(self) -> float:
        return float(self.view(np.ndarray).reshape(-1)[0])

    def __int__(self) -> int:
        return int(self.view(np.ndarray).reshape(-1)[0])


def _lenient(value: float) -> np.ndarray:
    return np.asarray([value]).view(_ConvertsLikeNumpy20)


def _one_element_arrays(value: float) -> list[np.ndarray]:
    """The plain one-element array, and the one that converts like numpy 2.0."""
    return [np.asarray([value]), _lenient(value)]


_ARRAY_IDS = ["numpy-array", "converts-like-numpy-2.0"]

#: The two ways of wrapping a guard's probe in one axis, by the ids above.
_WRAPS: list[Callable[[float], np.ndarray]] = [
    lambda value: np.asarray([value]),
    _lenient,
]


def test_the_stand_in_converts_the_way_numpy_2_0_did() -> None:
    lenient = _lenient(54.0)
    assert float(lenient) == pytest.approx(54.0)
    assert int(_lenient(3)) == 3
    assert np.ndim(lenient) == 1


# ---------------------------------------------------------------------------
# The helpers themselves
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value", [3.0, 3, np.float64(3.0), np.int64(3), np.asarray(3.0), "3", None]
)
def test_a_value_without_axes_is_a_scalar(value: object) -> None:
    assert validation.is_scalar(value)


@pytest.mark.parametrize(
    "value",
    [np.asarray([3.0]), _lenient(3.0), [3.0], (3.0, 4.0), [[1.0], [2.0, 3.0]]],
    ids=["array", "lenient", "list", "tuple", "ragged"],
)
def test_anything_with_an_axis_is_not(value: object) -> None:
    assert not validation.is_scalar(value)


@pytest.mark.parametrize("value", _one_element_arrays(54.0), ids=_ARRAY_IDS)
def test_require_real_refuses_an_array_with_its_own_message(value: np.ndarray) -> None:
    with pytest.raises(ValueError, match="'humidity' is wrong"):
        validation.require_real(value, "'humidity' is wrong")


@pytest.mark.parametrize("value", ["fifty", object(), 10**400])
def test_require_real_renames_what_float_refuses(value: object) -> None:
    with pytest.raises(ValueError, match="'x' is wrong"):
        validation.require_real(value, "'x' is wrong")


@pytest.mark.parametrize(
    "guard", sorted(_SHARED_GUARDS), ids=lambda name: name.removeprefix("require_")
)
@pytest.mark.parametrize("value", _one_element_arrays(0.5), ids=_ARRAY_IDS)
def test_every_shared_scalar_guard_refuses_an_array(
    guard: str, value: np.ndarray
) -> None:
    check: Callable[[object, str], float] = getattr(validation, guard)
    with pytest.raises(ValueError, match="'probe' must be one number"):
        check(value, "probe")


@pytest.mark.parametrize(
    "guard", sorted(_SHARED_GUARDS), ids=lambda name: name.removeprefix("require_")
)
def test_every_shared_scalar_guard_takes_what_float_takes(guard: str) -> None:
    """A numeric string reached the guards through ``float()`` before they
    asked the rank, and still does.
    """
    check: Callable[[object, str], float] = getattr(validation, guard)
    assert check("0.5", "probe") == pytest.approx(0.5)


@pytest.mark.parametrize(
    "guard", sorted(_SHARED_GUARDS), ids=lambda name: name.removeprefix("require_")
)
@pytest.mark.parametrize(
    "value", ["fifty", None, object()], ids=["word", "none", "object"]
)
def test_every_shared_scalar_guard_names_what_float_refuses(
    guard: str, value: object
) -> None:
    check: Callable[[object, str], float] = getattr(validation, guard)
    with pytest.raises(ValueError, match="'probe' must be a number"):
        check(value, "probe")


# ---------------------------------------------------------------------------
# Through the public interface
# ---------------------------------------------------------------------------

_FREQS = np.array([100.0, 125.0, 160.0])
_T = np.array([2.0, 2.1, 2.2])


@pytest.mark.parametrize("humidity", _one_element_arrays(54.0), ids=_ARRAY_IDS)
def test_iso354_humidity_refuses_an_array(humidity: np.ndarray) -> None:
    with pytest.raises(ValueError, match="'relative_humidity_percent'"):
        materials.measure_sound_absorption(
            _FREQS,
            _T,
            _T - 0.5,
            volume=200.0,
            area=10.8,
            relative_humidity_percent=humidity,
        )


@pytest.mark.parametrize("start_band", _one_element_arrays(2), ids=_ARRAY_IDS)
def test_icao_start_band_refuses_an_array(start_band: np.ndarray) -> None:
    spl = np.full(24, 60.0)
    with pytest.raises(ValueError, match="'start_band'"):
        aircraft.tone_correction(spl, start_band=start_band)


@pytest.mark.parametrize("lowest", _one_element_arrays(12.0), ids=_ARRAY_IDS)
def test_a_filter_bank_limit_refuses_an_array(lowest: np.ndarray) -> None:
    limits = [lowest, 20_000.0]
    with pytest.raises(ValueError, match="two frequencies"):
        OctaveFilterBank(48_000, limits=limits)


@pytest.mark.parametrize("level", _one_element_arrays(120.0), ids=_ARRAY_IDS)
def test_an_underwater_level_refuses_an_array(level: np.ndarray) -> None:
    with pytest.raises(ValueError, match="'level'"):
        underwater.underwater_to_in_air_spl(level)


# ---------------------------------------------------------------------------
# Every guard that was read, called directly
# ---------------------------------------------------------------------------


def _helper(module: str, name: str) -> Callable[..., object]:
    found: Callable[..., object] = getattr(
        importlib.import_module(f"phonometry.{module}"), name
    )
    return found


#: Guards of the shape ``guard(value, name)``.
_NAMED_GUARDS: list[tuple[str, str]] = [
    ("building.measurement.flanking_transmission", "_positive"),
    ("building.measurement.intensity_insulation", "_positive_area"),
    ("building.measurement.survey_insulation", "_positive"),
    ("building.prediction.simplified_model", "_check_finite"),
    ("building.regulation.spain", "_finite"),
    ("building.regulation.spain", "_positive"),
    ("electroacoustics.distortion", "_positive"),
    ("electroacoustics.swept_sine", "_positive"),
    ("emission.sound_power_in_duct", "_as_scalar"),
    ("environment.assessment.measurement", "_positive"),
    ("environment.assessment.measurement", "_finite"),
    ("environment.assessment.spain", "_finite"),
    ("environment.assessment.spain", "_positive"),
    ("environment.sources.cnossos_rail", "_finite"),
    ("environment.sources.cnossos_road", "_finite"),
    ("environment.sources.wind_turbine", "_positive"),
    ("fluids.water", "_positive"),
    ("fluids.water", "_finite"),
    ("materials.diffusers.design", "_positive_scalar"),
    ("materials.diffusers.reverberation_room_scattering", "_positive_scalar"),
    ("metrology.comparison_calibration", "_relative_humidity"),
    ("metrology.sound_level_meter", "_scalar"),
    ("noise_control.valves_hydrodynamic", "_require_count"),
    ("psychoacoustics.quality.annoyance", "_nonnegative"),
    ("psychoacoustics.quality.tone_audibility", "_positive"),
    ("psychoacoustics.quality.tone_audibility", "_finite"),
    ("signals.spectra", "_positive"),
    ("underwater.acoustics", "_positive"),
    ("underwater.acoustics", "_finite"),
    ("underwater.propagation.closed_form", "_positive"),
    ("underwater.sonar_equation", "_finite"),
    ("vibration.human.instrumentation", "_checked_uncertainty"),
    ("vibration.machinery.diagnostics", "_require_count"),
]


@pytest.mark.parametrize(
    ("module", "name"), _NAMED_GUARDS, ids=[f"{m}.{n}" for m, n in _NAMED_GUARDS]
)
@pytest.mark.parametrize("wrap", _WRAPS, ids=_ARRAY_IDS)
def test_every_named_guard_refuses_an_array(
    module: str, name: str, wrap: Callable[[float], np.ndarray]
) -> None:
    guard = _helper(module, name)
    # The number itself passes, so the array can only be refused for its rank.
    guard(3.0, "probe")
    value = wrap(3.0)
    with pytest.raises(ValueError, match="'probe'"):
        guard(value, "probe")


#: Guards with a signature of their own: the call, and the name it refuses.
_OWN_SIGNATURES: list[tuple[str, str, Callable[[object], tuple[object, ...]], str]] = [
    ("electroacoustics.distortion", "_validate_notch_q", lambda v: (v,), "notch_q"),
    (
        "electroacoustics.headphones",
        "_impedances",
        lambda v: (v, 0.0),
        "rated_impedance",
    ),
    (
        "electroacoustics.headphones",
        "_impedances",
        lambda v: (32.0, v),
        "rated_source_impedance",
    ),
    (
        "electroacoustics.swept_sine",
        "_harmonic_window",
        lambda v: (v, np.array([0.0, 4096.0]), 2),
        "ir_length",
    ),
    (
        "emission.free_field_qualification",
        "_band_index",
        lambda v: (v,),
        "frequencies_hz",
    ),
    (
        "emission.free_field_qualification",
        "_checked_plane",
        lambda v: (v, None),
        "reflecting_plane",
    ),
    ("emission.intensity_compliance", "_spacing_offset", lambda v: (v,), "spacing"),
    (
        "emission.sound_power",
        "_static_pressure_at_altitude",
        lambda v: (v,),
        "altitude",
    ),
    (
        "emission.sound_power_hard_walled",
        "_check_uncertainty_inputs",
        lambda v: (v, 2.0),
        "sigma_omc_db",
    ),
    (
        "emission.sound_power_in_situ",
        "_checked_sigma_omc",
        lambda v: (v, 2.0),
        "sigma_omc",
    ),
    (
        "emission.sound_power_intensity_points",
        "_nominal_band",
        lambda v: (v, "octave"),
        "frequencies",
    ),
    (
        "emission.sound_power_reverberation",
        "_room_inputs",
        lambda v: (v, 120.0, 20.0, 101.325),
        "volume",
    ),
    (
        "environment.assessment.spain",
        "_validate_annual_inputs",
        lambda v: (None, v, 50.0),
        "year_days",
    ),
    (
        "environment.assessment.spain",
        "_validate_annual_inputs",
        lambda v: (v, 365, 50.0),
        "operating_days",
    ),
    (
        "materials.absorbers.biot",
        "_require_poisson_ratio",
        lambda v: (v,),
        "poisson_ratio",
    ),
    (
        "materials.absorbers.sound_absorption",
        "_resolve_speed",
        lambda v: (20.0, v),
        "speed_of_sound",
    ),
    (
        "materials.absorbers.sound_absorption",
        "_resolve_speed",
        lambda v: (v, None),
        "temperature_c",
    ),
    ("materials.diffusers.design", "_prime_generator", lambda v: (v,), "prime"),
    (
        "metrology.free_field_corrections",
        "_repeatability_dof",
        lambda v: (v,),
        "repeatability_dof",
    ),
    (
        "psychoacoustics.quality.tonality_ecma",
        "_band_range",
        lambda v: (v, None),
        "f_low",
    ),
    (
        "psychoacoustics.quality.tone_audibility",
        "_require_line_spacing",
        lambda v: (v,),
        "line_spacing",
    ),
    ("signals.phase", "_validate_oversample", lambda v: (v,), "oversample"),
    ("signals.spectra", "_validate_confidence", lambda v: (v,), "confidence"),
    ("vibration.human.exposure", "_positive_fs", lambda v: (v,), "fs"),
    (
        "vibration.structural.impact_mobility",
        "_pair",
        lambda v: ((v, 100.0), "band_hz"),
        "band_hz",
    ),
    (
        "building.measurement.intensity_insulation",
        "_validated_element_count",
        lambda v: (v,),
        "elements",
    ),
    (
        "building.measurement.low_frequency",
        "_require_volume_triggers",
        lambda v: (v, "volume"),
        "volume",
    ),
    ("filters.core", "_resolve_limits", lambda v: ([v, 20_000.0],), "limits"),
    ("_report.iso10848", "_part_designation", lambda v: (v,), "part"),
]


#: The number each guard takes, by the parameter it refuses, where 3.0 is
#: outside the range it accepts or warns about: a probe refused for its value
#: would be refused whether or not the rank is asked, and could not tell a
#: guard that asks it from one that does not.
_OWN_PROBES: dict[str, float] = {
    "ir_length": 4096,
    "frequencies_hz": 100.0,
    "reflecting_plane": 0.5,
    "frequencies": 1000.0,
    "poisson_ratio": 0.3,
    "temperature_c": 20.0,
    "f_low": 100.0,
    "confidence": 0.95,
}


@pytest.mark.parametrize(
    ("module", "name", "arguments", "refused"),
    _OWN_SIGNATURES,
    ids=[f"{m}.{n}:{r}" for m, n, _, r in _OWN_SIGNATURES],
)
@pytest.mark.parametrize("wrap", _WRAPS, ids=_ARRAY_IDS)
def test_every_guard_with_its_own_signature_refuses_an_array(
    module: str,
    name: str,
    arguments: Callable[[object], tuple[object, ...]],
    refused: str,
    wrap: Callable[[float], np.ndarray],
) -> None:
    guard = _helper(module, name)
    probe = _OWN_PROBES.get(refused, 3.0)
    # The number itself passes, so the array can only be refused for its rank.
    guard(*arguments(probe))
    args = arguments(wrap(probe))
    with pytest.raises(ValueError, match=refused):
        guard(*args)


@pytest.mark.parametrize("value", _one_element_arrays(100.0), ids=_ARRAY_IDS)
def test_a_frequency_pair_member_refuses_an_array(value: np.ndarray) -> None:
    owner = types.SimpleNamespace(band=(value, 2000.0))
    guard = _helper("electroacoustics.loudspeaker", "_require_frequency_pair")
    with pytest.raises(ValueError, match="'band'"):
        guard(owner, "band")


@pytest.mark.parametrize("value", _one_element_arrays(100.0), ids=_ARRAY_IDS)
def test_an_envelope_band_edge_refuses_an_array(value: np.ndarray) -> None:
    guard = _helper("signals.envelope", "_bandpass_pre_filter")
    record = np.zeros(4096)
    with pytest.raises(ValueError, match="'band'"):
        guard(record, 48_000.0, (value, 1000.0))


@pytest.mark.parametrize("value", _one_element_arrays(100.0), ids=_ARRAY_IDS)
def test_a_pile_strike_limit_refuses_an_array(value: np.ndarray) -> None:
    rng = np.random.default_rng(1)
    pressure = rng.standard_normal(4800)
    with pytest.raises(ValueError, match="'limits'"):
        underwater.strike_sel_spectrum(pressure, 48_000.0, limits=(value, 10_000.0))


#: Public calls whose guard read the parameter through ``float()`` or
#: :mod:`math` without its rank: each took a one-element array on numpy 2.0.2,
#: the floor, and refused it on 2.4 and later with an anonymous ``TypeError``.
#: (call, the number it takes, the parameter it names when refused)
_PUBLIC_CALLS: list[tuple[str, Callable[[object], object], float, str]] = [
    (
        "materials.absorption_class",
        lambda v: materials.absorption_class(v),
        0.8,
        "alpha_w",
    ),
    (
        "emission.reference_atmosphere_correction",
        lambda v: emission.reference_atmosphere_correction(
            v, static_pressure_kpa=101.3
        ),
        20.0,
        "temperature_c",
    ),
    (
        "room.minimum_reliable_reverberation_time",
        lambda v: room.minimum_reliable_reverberation_time(100.0, detector_time=v),
        0.1,
        "detector_time",
    ),
    (
        "vibration.machinery.is_significant_change",
        lambda v: vibration.machinery.is_significant_change(v, 4.5),
        3.0,
        "change",
    ),
    (
        "noise_control.blade_passing_frequency",
        lambda v: noise_control.blade_passing_frequency(1450.0, v),
        12,
        "blades",
    ),
    (
        "building.low_frequency_procedure_applies",
        lambda v: building.low_frequency_procedure_applies(v),
        30.0,
        "volume",
    ),
    (
        "aircraft.sae_band_attenuation",
        lambda v: aircraft.sae_band_attenuation(
            [100.0, 1000.0, 4000.0], 100.0, relative_humidity_percent=v
        ),
        54.0,
        "relative_humidity_percent",
    ),
    (
        "environment.atmospheric_absorption",
        lambda v: environment.atmospheric_absorption(
            100.0, relative_humidity_percent=v
        ),
        54.0,
        "relative_humidity_percent",
    ),
    (
        "aircraft.lateral_attenuation",
        lambda v: aircraft.lateral_attenuation(v, 500.0),
        10.0,
        "elevation_deg",
    ),
    (
        "psychoacoustics.fluctuation_strength_am_noise",
        lambda v: psychoacoustics.fluctuation_strength_am_noise(60.0, v, 4.0),
        1.0,
        "modulation_factor",
    ),
    (
        "hearing.audiometric_uncertainty",
        lambda v: hearing.audiometric_uncertainty(v),
        1000.0,
        "frequency",
    ),
]


@pytest.mark.parametrize(
    ("call", "probe", "refused"),
    [entry[1:] for entry in _PUBLIC_CALLS],
    ids=[entry[0] for entry in _PUBLIC_CALLS],
)
@pytest.mark.parametrize("wrap", _WRAPS, ids=_ARRAY_IDS)
def test_a_public_guard_refuses_an_array(
    call: Callable[[object], object],
    probe: float,
    refused: str,
    wrap: Callable[[float], np.ndarray],
) -> None:
    # The number itself passes, so the array can only be refused for its rank.
    call(probe)
    value = wrap(probe)
    with pytest.raises(ValueError, match=f"'{refused}' must be one number"):
        call(value)


@pytest.mark.parametrize("value", _one_element_arrays(55.0), ids=_ARRAY_IDS)
def test_a_soundscape_result_refuses_an_array(value: np.ndarray) -> None:
    from phonometry.environment.assessment import soundscape as sc

    results: dict[str, object] = dict.fromkeys(
        ("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T", "N5", "N95", "Nrmc"), 50.0
    )
    results["LAeq,T"] = value
    fields: dict[str, object] = {
        "environment_type": "real",
        "sound_sources": "traffic",
        "weather_and_wind": "dry",
        "time_of_year_and_day": "June, noon",
        "measurement_points": "one point",
        "measurement_results": results,
        "site_description": "street",
    }
    with pytest.raises(ValueError, match="'LAeq,T'"):
        sc.SoundscapeAcousticEnvironment(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The structural rules
# ---------------------------------------------------------------------------


def _called_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return ast.unparse(func)
    return ""


def _functions(tree: ast.AST) -> Iterator[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _asks_the_rank(function: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call)
        and _called_name(node).rsplit(".", 1)[-1] in _RANK_HELPERS
        for node in ast.walk(function)
    )


def _catches_type_error(handler: ast.ExceptHandler) -> bool:
    caught = handler.type
    if caught is None:
        return True
    names = caught.elts if isinstance(caught, ast.Tuple) else [caught]
    return any(
        isinstance(name, ast.Name)
        and name.id in {"TypeError", "Exception", "BaseException"}
        for name in names
    )


def renaming_guards(source: str) -> list[str]:
    """Each ``float()``/``int()`` whose ``TypeError`` a guard catches as its refusal.

    Allowed only in a function that asks the rank too, because only the rank
    refuses a one-element array on numpy 2.0 to 2.3.
    """
    found: list[str] = []
    for function in _functions(ast.parse(source)):
        if _asks_the_rank(function):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Try) or not any(
                _catches_type_error(handler) for handler in node.handlers
            ):
                continue
            found += [
                f"{function.name}:{call.lineno}"
                for statement in node.body
                for call in ast.walk(statement)
                if isinstance(call, ast.Call) and _called_name(call) in {"float", "int"}
            ]
    return found


def _first_statement(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.stmt | None:
    """The first statement after the docstring and any ``msg = ...`` line."""
    for statement in function.body:
        if isinstance(statement, ast.Expr) and isinstance(
            statement.value, ast.Constant
        ):
            continue
        if isinstance(statement, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id == "msg"
            for target in statement.targets
        ):
            continue
        return statement
    return None


def scalar_guards_without_rank(source: str) -> list[str]:
    """Private guards that open by reading their value as one number, unasked.

    A private function that raises, and whose first statement converts its
    first parameter, is a scalar guard; it has to ask the rank (or test the
    type with :func:`isinstance`, which no array passes) before converting.
    """
    found: list[str] = []
    for function in _functions(ast.parse(source)):
        if not function.name.startswith("_") or function.name.startswith("__"):
            continue
        params = [
            arg.arg
            for arg in function.args.posonlyargs + function.args.args
            if arg.arg not in {"self", "cls"}
        ]
        first = _first_statement(function)
        # A conversion inside a try is the renaming rule's to judge.
        if not params or first is None or isinstance(first, ast.Try):
            continue
        if not any(isinstance(node, ast.Raise) for node in ast.walk(function)):
            continue
        read = first.test if isinstance(first, ast.If) else first
        converts = any(
            isinstance(node, ast.Call)
            and _called_name(node) in _CONVERSIONS
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == params[0]
            for node in ast.walk(read)
        )
        typed = any(
            isinstance(node, ast.Call)
            and _called_name(node) == "isinstance"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == params[0]
            for node in ast.walk(function)
        )
        if converts and not typed and not _asks_the_rank(function):
            found.append(f"{function.name}:{function.lineno}")
    return found


def converted_before_the_guard(source: str) -> list[str]:
    """Each shared scalar guard handed ``float(x)`` instead of ``x``.

    The conversion runs first and turns a one-element array into a number on
    numpy 2.0 to 2.3, so the guard's own rank check never sees the array.
    """
    return [
        f"{_called_name(node)}:{node.lineno}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and _called_name(node) in _SHARED_GUARDS
        and node.args
        and isinstance(node.args[0], ast.Call)
        and _called_name(node.args[0]) == "float"
    ]


#: The calls that settle a value's rank for the guard that reads it: the rank
#: helpers, the shared scalar guards built on them, and ``require_count``, which
#: takes nothing but an ``int`` or a ``float``.
_ASKS_THE_RANK_OF = _RANK_HELPERS | _SHARED_GUARDS | {"require_count"}

#: The conversions a guard reads a parameter through.
_GUARD_CONVERSIONS = _CONVERSIONS | {"math.isinf"}

#: Type names that no array is an instance of. ``isinstance(x, bool)`` is not
#: among them on purpose: it refuses an ``int`` posing as a count and lets an
#: array through to the conversion that follows it.
_NUMBER_TYPES = frozenset(
    {"int", "float", "integer", "floating", "number", "Real", "Integral", "Number"}
)


def _subjects(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Callable[[ast.AST], str | None]:
    """What a guard in *function* can be guarding: a parameter, or a field.

    In ``__post_init__`` the caller's values are the dataclass fields, read as
    ``self.<field>``; everywhere else they are the parameters.
    """
    arguments = function.args
    params = {
        arg.arg
        for arg in arguments.posonlyargs + arguments.args + arguments.kwonlyargs
        if arg.arg not in {"self", "cls"}
    }
    fields = function.name == "__post_init__"

    def subject(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name) and node.id in params:
            return node.id
        if (
            fields
            and isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        ):
            return ast.unparse(node)
        return None

    return subject


def _rank_settled(
    function: ast.FunctionDef | ast.AsyncFunctionDef, subject: str
) -> bool:
    """Whether *function* asks *subject* its rank, or its number type."""
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if ast.unparse(node.args[0]) != subject:
            continue
        called = _called_name(node).rsplit(".", 1)[-1]
        if called in _ASKS_THE_RANK_OF:
            return True
        if called == "isinstance" and len(node.args) > 1:
            named = {
                part.id if isinstance(part, ast.Name) else part.attr
                for part in ast.walk(node.args[1])
                if isinstance(part, (ast.Name, ast.Attribute))
            }
            if named & _NUMBER_TYPES:
                return True
    return False


def _raises(statements: list[ast.stmt]) -> bool:
    return any(
        isinstance(node, ast.Raise)
        for statement in statements
        for node in ast.walk(statement)
    )


def _converted(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    subject: Callable[[ast.AST], str | None],
) -> tuple[dict[str, str], set[str]]:
    """The names bound to ``float(x)``/``int(x)``, and every ``x`` so converted."""
    bound: dict[str, str] = {}
    converted: set[str] = set()
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Call)
            and _called_name(node) in {"float", "int"}
            and node.args
            and (read := subject(node.args[0])) is not None
        ):
            converted.add(read)
        target = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        value = getattr(node, "value", None)
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Call)
            and _called_name(value) in {"float", "int"}
            and value.args
            and (read := subject(value.args[0])) is not None
        ):
            bound[target.id] = read
    return bound, converted


def _compared(part: ast.AST, subject: Callable[[ast.AST], str | None]) -> list[str]:
    """What a comparison in a guard's test orders (``is`` and ``in`` do not)."""
    if not isinstance(part, ast.Compare) or any(
        isinstance(op, (ast.Is, ast.IsNot, ast.In, ast.NotIn)) for op in part.ops
    ):
        return []
    return [
        read
        for operand in (part.left, *part.comparators)
        if (read := subject(operand)) is not None
    ]


def guards_without_rank(source: str) -> list[str]:
    """Every guard that reads a caller's value as one number without its rank.

    A guard is an ``if`` whose body raises. It reads a parameter (a field, in
    ``__post_init__``) as one number when its test converts it with
    :func:`float`, :func:`int` or :mod:`math`, when it tests a name bound to
    such a conversion (``value = float(volume)`` and then ``if value <= 0.0``),
    or when it compares the parameter that the function converts elsewhere
    (``if fs <= 0: raise`` and then ``float(fs)``). Each one, public or
    private, needs the rank of what it reads settled in the same function, by
    a rank helper, a shared scalar guard or an :func:`isinstance` against a
    number type, or it accepts a one-element array on numpy 2.0 to 2.3 and
    refuses it anonymously from 2.4 on.
    """
    found: list[str] = []
    for function in _functions(ast.parse(source)):
        subject = _subjects(function)
        bound, converted = _converted(function, subject)
        reads: dict[str, int] = {}
        for node in ast.walk(function):
            if not isinstance(node, ast.If) or not _raises(node.body):
                continue
            for part in ast.walk(node.test):
                read = None
                if (
                    isinstance(part, ast.Call)
                    and _called_name(part) in _GUARD_CONVERSIONS
                    and part.args
                ):
                    read = subject(part.args[0])
                elif isinstance(part, ast.Name) and part.id in bound:
                    read = bound[part.id]
                if read is not None:
                    reads.setdefault(read, part.lineno)
                for ordered in _compared(part, subject):
                    if ordered in converted:
                        reads.setdefault(ordered, part.lineno)
        found += [
            f"{function.name}({read}):{line}"
            for read, line in sorted(reads.items())
            if not _rank_settled(function, read)
        ]
    return found


_RULES: dict[str, Callable[[str], list[str]]] = {
    "renaming": renaming_guards,
    "private": scalar_guards_without_rank,
    "converted": converted_before_the_guard,
    "unasked": guards_without_rank,
}


def _offences(rule: Callable[[str], list[str]]) -> list[str]:
    return [
        f"{path.relative_to(SRC).as_posix()}:{where}"
        for path in sorted(SRC.rglob("*.py"))
        for where in rule(path.read_text(encoding="utf-8"))
    ]


@pytest.mark.parametrize("rule", list(_RULES), ids=list(_RULES))
def test_no_guard_in_the_tree_leaves_the_rank_to_numpy(rule: str) -> None:
    assert _offences(_RULES[rule]) == []


_PLANTED = {
    "renaming": """
def _humidity(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError("'humidity' must be a number") from None
""",
    "private": """
def _positive(value, name):
    scalar = float(value)
    if scalar <= 0.0:
        raise ValueError(name)
    return scalar
""",
    "converted": """
def volume(v):
    return require_positive(float(v), "volume")
""",
    "unasked": """
def absorption_class(alpha_w):
    if not math.isfinite(alpha_w) or not 0.0 <= alpha_w <= 1.0:
        raise ValueError("'alpha_w' must be in [0, 1]")
    return "A" if alpha_w >= 0.9 else "B"

def low_frequency_procedure_applies(volume):
    value = float(volume)
    if value <= 0.0:
        raise ValueError("'volume' must be positive")
    return value < 25.0

class Rating:
    def __post_init__(self):
        if not math.isfinite(self.alpha_w):
            raise ValueError("'alpha_w' must be finite")

def counted(n):
    if isinstance(n, bool) or int(n) != n:
        raise ValueError("'n' must be a whole number")
    return int(n)

def resampled(fs):
    if fs <= 0.0:
        raise ValueError("'fs' must be positive")
    return float(fs) / 2.0
""",
}

_ANSWERED = {
    "renaming": """
def _humidity(value):
    return require_real(value, "'humidity' must be a number")
""",
    "private": """
def _positive(value, name):
    require_scalar(value, name)
    scalar = float(value)
    if scalar <= 0.0:
        raise ValueError(name)
    return scalar
""",
    "converted": """
def volume(v):
    return require_positive(v, "volume")
""",
    "unasked": """
def absorption_class(alpha_w):
    require_scalar(alpha_w, "alpha_w")
    if not math.isfinite(alpha_w) or not 0.0 <= alpha_w <= 1.0:
        raise ValueError("'alpha_w' must be in [0, 1]")
    return "A" if alpha_w >= 0.9 else "B"

def low_frequency_procedure_applies(volume):
    value = require_positive(volume, "volume")
    if value <= 0.0:
        raise ValueError("'volume' must be positive")
    return value < 25.0

class Rating:
    def __post_init__(self):
        require_scalar(self.alpha_w, "alpha_w")
        if not math.isfinite(self.alpha_w):
            raise ValueError("'alpha_w' must be finite")

def counted(n):
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
        raise ValueError("'n' must be a whole number")
    if int(n) != n:
        raise ValueError("'n' must be a whole number")
    return int(n)

def resampled(fs):
    fs = require_positive(fs, "fs")
    if fs <= 0.0:
        raise ValueError("'fs' must be positive")
    return float(fs) / 2.0
""",
}


@pytest.mark.parametrize("rule", list(_RULES), ids=list(_RULES))
def test_each_rule_finds_the_shape_it_exists_for(rule: str) -> None:
    assert _RULES[rule](_PLANTED[rule]) != []
    assert _RULES[rule](_ANSWERED[rule]) == []


def test_the_unasked_rule_finds_every_shape_of_the_guard() -> None:
    """An inline test, a bound conversion, a field, a bool-only isinstance, and
    a comparison of a value the function converts afterwards.
    """
    found = guards_without_rank(_PLANTED["unasked"])
    assert sorted(where.split(":")[0] for where in found) == [
        "__post_init__(self.alpha_w)",
        "absorption_class(alpha_w)",
        "counted(n)",
        "low_frequency_procedure_applies(volume)",
        "resampled(fs)",
    ]
