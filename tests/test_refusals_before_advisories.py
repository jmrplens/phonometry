#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A documented refusal comes first, and NumPy says nothing the library is about to say.

Under ``python -W error`` a warning raised ahead of a refusal replaces it: the
caller who wrote ``except ValueError`` met a ``FilterBankWarning``, a
``STIWarning``, a ``ValveNoiseWarning``, a ``SoundPowerWarning`` or NumPy's
``RuntimeWarning`` instead.
Each case runs with every warning an error and waits for the exception the
docstring names.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry import (
    building,
    emission,
    environment,
    filters,
    fluids,
    hearing,
    materials,
    noise_control,
    room,
    signals,
    speech,
    underwater,
    vibration,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike

    _Load = tuple[ArrayLike, ArrayLike, ArrayLike, ArrayLike]


@pytest.fixture(autouse=True)
def _every_warning_an_error() -> None:
    warnings.simplefilter("error")


def _exponential_ir(fs: int) -> np.ndarray:
    t = np.arange(fs) / fs
    return np.exp(-6.91 * t) * np.random.default_rng(7).standard_normal(fs)


def test_a_band_above_the_nyquist_frequency_is_refused_before_the_bank_warns() -> None:
    ir = _exponential_ir(8000)
    with pytest.raises(ValueError, match=r"'band'.*Nyquist"):
        room.decay_curve(ir, 8000, band=3500.0)


def test_limits_above_the_nyquist_frequency_are_refused_before_the_bank_warns() -> None:
    ir = _exponential_ir(8000)
    with pytest.raises(ValueError, match=r"'limits'.*Nyquist"):
        room.room_parameters(ir, 8000, limits=(20000.0, 22000.0))


def test_stipa_refuses_ambient_levels_without_speech_levels_before_the_length() -> None:
    short = speech.stipa_signal(48000, duration_s=5.0, seed=1234)
    with pytest.raises(ValueError, match="requires the speech octave-band levels"):
        speech.stipa(short, 48000, ambient=[40.0] * 7)  # type: ignore[call-overload]


def test_valve_stages_that_take_too_much_are_refused_before_the_series_law() -> None:
    with pytest.raises(ValueError, match="take more than the valve's differential"):
        noise_control.stage_conditions(
            inlet_pressure_pa=1.0e6,
            outlet_pressure_pa=4.0e5,
            vapor_pressure_pa=2.32e3,
            stage_coefficients=[95.0, 95.0, 95.0],
            flow_coefficient=90.0,
        )


def test_an_overflowing_comb_order_is_refused_by_the_library() -> None:
    with pytest.raises(ValueError, match="overflows the floating-point range"):
        signals.comb_filter_response(np.array([1e308]), 1e308, 3)


def test_an_infinite_transmissibility_is_refused_by_its_own_name() -> None:
    with pytest.raises(ValueError, match="'transmissibility' must contain only finite"):
        vibration.transfer_stiffness_indirect(
            np.array([np.inf + 0j, 0.05 + 0j]),
            50.0,
            frequency=np.array([10.0, 20.0]),
        )


def test_a_singular_load_pair_warns_once_and_numpy_says_nothing() -> None:
    warnings.simplefilter("error", RuntimeWarning)
    warnings.simplefilter("ignore", materials.ImpedanceTubeWarning)
    c0 = 343.24
    k = np.asarray(materials.tube_wavenumber(np.array([500.0, 1000.0]), c0))
    load = (1.0 + 0j, 0.9 + 0j, 0.8 + 0j, 0.7 + 0j)
    matrix = materials.transfer_matrix_two_load(
        load,
        load,
        thickness_m=0.05,
        wavenumber=k.real.astype(np.complex128),
        characteristic_impedance=1.204 * c0,
        l1=0.10,
        s1=0.03,
        l2=0.15,
        s2=0.03,
    )
    assert not np.all(np.isfinite(matrix.t11))


@pytest.mark.parametrize("solve", ["two-load", "one-load"])
def test_a_load_with_no_downstream_response_is_named_singular(solve: str) -> None:
    # H3 = H4 = 0 leaves no pressure and no velocity at the downstream face, so
    # the denominator and the scale it is judged against are both zero: the
    # solve is singular, not merely near it, and still says so.
    c0 = 343.24
    k = np.asarray(materials.tube_wavenumber(np.array([500.0, 1000.0]), c0))
    load = (
        np.array([1.0 + 0j, 0.9 + 0j]),
        np.array([0.8 + 0j, 0.7 + 0j]),
        np.zeros(2, dtype=np.complex128),
        np.zeros(2, dtype=np.complex128),
    )
    geometry: dict[str, Any] = {
        "thickness_m": 0.05,
        "wavenumber": k.real.astype(np.complex128),
        "characteristic_impedance": 1.204 * c0,
        "l1": 0.10,
        "s1": 0.03,
        "l2": 0.15,
        "s2": 0.03,
    }
    loads = (load, load) if solve == "two-load" else (load,)
    function = (
        materials.transfer_matrix_two_load
        if solve == "two-load"
        else materials.transfer_matrix_one_load
    )
    with pytest.warns(
        materials.ImpedanceTubeWarning,
        match=r"near-singular at 2 frequency point\(s\)",
    ):
        matrix = function(*loads, **geometry)
    assert not np.any(np.isfinite(matrix.t11))


#: Octave mid-band frequencies of the ISO 3747 cases, 125 Hz to 8 kHz.
_OCTAVES = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
#: Third-octave mid-band frequencies of the ISO 3741 cases.
_THIRDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def _in_situ(**kwargs: object) -> emission.InSituSoundPowerResult:
    """Four positions and no background: the 7.5 advisory is due on a valid call."""
    arguments: dict[str, Any] = {"frequencies": _OCTAVES, **kwargs}
    power = arguments.pop("reference_sound_power_levels", np.full(7, 93.0))
    return emission.sound_power_in_situ(
        np.full((4, 7), 80.0), np.full((4, 7), 82.0), power, **arguments
    )


@pytest.mark.parametrize(
    ("arguments", "refusal"),
    [
        ({"temperature_c": -300.0}, "'temperature_c' must be finite"),
        ({"static_pressure_kpa": 0.0}, "'static_pressure_kpa' must be finite"),
        ({"frequencies": _OCTAVES[::-1]}, "'frequencies' must be distinct"),
        ({"reference_sound_power_levels": np.full(6, 93.0)}, "one value per band"),
        ({"sigma_omc_db": -1.0}, "'sigma_omc_db' must be finite"),
        ({"coverage_factor": 0.0}, "'coverage_factor' must be positive"),
        (
            {"reference_background_levels": np.full(5, 60.0)},
            "'reference_background_levels' must carry one value per band",
        ),
        (
            {"conditions": emission.GradeConditions(directivity_range=-1.0)},
            "'directivity_range' must be finite",
        ),
    ],
)
def test_the_in_situ_determination_refuses_before_it_misses_its_background(
    arguments: dict[str, object], refusal: str
) -> None:
    with pytest.raises(ValueError, match=refusal):
        _in_situ(**arguments)


def test_the_in_situ_determination_refuses_before_it_counts_its_positions() -> None:
    with pytest.raises(ValueError, match="'temperature_c' must be finite"):
        emission.sound_power_in_situ(
            np.full((2, 7), 80.0),
            np.full((2, 7), 82.0),
            np.full(7, 93.0),
            frequencies=_OCTAVES,
            background_levels=np.full(7, 50.0),
            temperature_c=-300.0,
        )


def test_the_in_situ_energy_refuses_before_it_counts_its_events() -> None:
    with pytest.raises(ValueError, match="'integration_time' must be positive"):
        emission.sound_energy_in_situ(
            np.full((4, 7), 80.0),
            np.full((4, 7), 82.0),
            np.full(7, 93.0),
            frequencies=_OCTAVES,
            n_events=3,
            background_levels=np.full(7, 50.0),
            integration_time=-1.0,
        )


def test_the_reverberation_room_refuses_a_background_before_the_positions() -> None:
    with pytest.raises(ValueError, match="'background_levels' must match"):
        emission.sound_power_reverberation(
            np.full((4, 6), 80.0),
            np.full(6, 1.5),
            200.0,
            220.0,
            frequencies=_THIRDS,
            background_levels=np.full(5, 60.0),
        )


def test_the_comparison_refuses_a_background_without_its_bands_first() -> None:
    with pytest.raises(ValueError, match="'frequencies' are required"):
        emission.sound_power_comparison(
            np.full((4, 6), 80.0),
            np.full(6, 82.0),
            np.full(6, 90.0),
            background_levels=np.full(6, 60.0),
        )


def test_the_comparison_refuses_a_reference_background_before_any_advisory() -> None:
    with pytest.raises(ValueError, match="'reference_background_levels' must"):
        emission.sound_power_comparison(
            np.full((4, 6), 80.0),
            np.full((4, 6), 82.0),
            np.full(6, 90.0),
            frequencies=_THIRDS,
            background_levels=np.full(6, 75.0),
            reference_background_levels=np.full(5, 60.0),
        )


def test_the_reverberation_energy_refuses_a_background_without_its_interval() -> None:
    with pytest.raises(ValueError, match="'integration_time'"):
        emission.sound_energy_reverberation(
            np.full((4, 6), 80.0),
            np.full(6, 1.5),
            200.0,
            220.0,
            frequencies=_THIRDS,
            background_levels=np.full(6, 60.0),
        )


def test_the_energy_comparison_refuses_a_background_without_its_interval() -> None:
    with pytest.raises(ValueError, match="'integration_time'"):
        emission.sound_energy_comparison(
            np.full((4, 6), 80.0),
            np.full(6, 82.0),
            np.full(6, 90.0),
            frequencies=_THIRDS,
            background_levels=np.full(6, 60.0),
        )


def test_the_hard_walled_room_refuses_before_it_counts_its_microphones() -> None:
    with pytest.raises(ValueError, match="'temperature_c' must be finite"):
        emission.sound_power_hard_walled(
            np.full((1, 7), 80.0),
            np.full((1, 7), 82.0),
            np.full(7, 93.0),
            frequencies=_OCTAVES,
            background_levels=np.full(7, 50.0),
            temperature_c=-300.0,
        )


def test_the_hard_walled_energy_refuses_a_background_without_its_interval() -> None:
    with pytest.raises(ValueError, match="'integration_time'"):
        emission.sound_energy_hard_walled(
            np.full((1, 7), 80.0),
            np.full((1, 7), 82.0),
            np.full(7, 93.0),
            frequencies=_OCTAVES,
            n_events=5,
            background_levels=np.full(7, 50.0),
        )


def test_the_hard_walled_room_check_refuses_before_it_counts_orientations() -> None:
    with pytest.raises(ValueError, match="'volume' must be positive"):
        emission.check_hard_walled_room(
            np.full((4, 7), 80.0),
            frequencies=_OCTAVES,
            volume=-1.0,
            reference_box_m=(1.0, 1.0, 1.0),
        )


def test_the_hard_walled_survey_refuses_its_bands_before_it_counts_positions() -> None:
    with pytest.raises(ValueError, match="'frequencies'"):
        emission.hard_walled_source_locations(
            np.full((2, 7), 80.0), frequencies=_OCTAVES[::-1]
        )


#: Two segments whose partial powers are negative in both bands.
_REVERSED_FLOW = np.array([[-1e-3, -2e-3], [-1e-3, -2e-3]])


def test_the_precision_intensity_method_refuses_text_before_the_net_power() -> None:
    with pytest.raises(TypeError, match="'frequencies' must be numbers"):
        emission.sound_power_intensity_precision(
            _REVERSED_FLOW, np.ones(2), frequencies=["a", "b"]
        )


def test_the_discrete_point_method_refuses_before_it_counts_its_points() -> None:
    with pytest.raises(ValueError, match="'temporal_intensity' must carry one column"):
        emission.sound_power_intensity_points(
            np.abs(_REVERSED_FLOW), np.ones(2), temporal_intensity=np.ones((5, 3))
        )


def test_the_special_room_survey_refuses_its_column_before_its_positions() -> None:
    with pytest.raises(ValueError, match="'n_microphone_positions' must be one of"):
        emission.special_room_source_locations(
            np.full((3, 7), 80.0), frequencies=_OCTAVES, n_microphone_positions=7
        )


def test_the_special_room_refuses_its_a_weighted_background_first() -> None:
    with pytest.raises(ValueError, match="'a_weighted_background_levels' must be"):
        emission.sound_power_special_room(
            np.full((1, 7), 80.0),
            frequencies=_OCTAVES,
            volume=100.0,
            nominal_reverberation_time_s=1.0,
            a_weighted_levels=np.full(3, 80.0),
            a_weighted_background_levels=np.full(2, 60.0),
        )


def test_the_special_room_comparison_refuses_its_reference_power_first() -> None:
    with pytest.raises(ValueError, match="'reference_sound_power_levels' must carry"):
        emission.sound_power_special_room_comparison(
            np.full((1, 7), 80.0),
            np.full((1, 7), 82.0),
            np.full(6, 90.0),
            frequencies=_OCTAVES,
        )


@pytest.mark.parametrize(
    "arguments",
    [
        {"background_levels": np.full(2, 78.0)},
        {"room": emission.RoomEnvironment(absorption_area=1.0)},
    ],
    ids=["short-background-margin", "large-k2"],
)
def test_the_surface_method_refuses_its_bands_before_it_advises(
    arguments: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="'frequencies' length must match"):
        emission.sound_power_pressure(
            np.full((20, 2), 80.0),
            "hemisphere",
            radius=1.0,
            frequencies=[1000.0],
            **arguments,  # type: ignore[arg-type]
        )


def test_the_surface_energy_method_refuses_its_bands_before_it_advises() -> None:
    with pytest.raises(ValueError, match="'frequencies' length must match"):
        emission.sound_energy_pressure(
            np.full((20, 2), 80.0),
            "hemisphere",
            radius=1.0,
            background_levels=np.full(2, 78.0),
            integration_time=1.0,
            frequencies=[1000.0],
        )


def test_the_turbine_set_refuses_its_overhead_mask_before_the_background() -> None:
    levels = np.full(12, 90.0)
    with pytest.raises(ValueError, match="'overhead_mask' must have one entry"):
        emission.turbine_sound_power(
            levels,
            surface_area=100.0,
            background_levels=levels - 1.0,
            environmental_correction=2.0,
            overhead_mask=np.zeros(3, dtype=bool),
        )


def test_the_high_frequency_room_constant_refuses_before_the_octave() -> None:
    with pytest.raises(ValueError, match="8 alpha V / S reaches 1"):
        emission.room_constant_from_air_absorption(
            [1000.0, 20000.0],
            volume=1.0e6,
            surface_area=1.0,
            temperature_c=20.0,
            relative_humidity_percent=50.0,
        )


def test_the_high_frequency_method_refuses_its_room_constant_first() -> None:
    with pytest.raises(ValueError, match="'room_constant' must be positive"):
        emission.high_frequency_sound_power(
            np.full((4, 2), 80.0), frequencies=[1000.0, 2000.0], room_constant=-1.0
        )


def test_stipa_refuses_a_clip_shorter_than_one_period_before_its_length() -> None:
    clip = speech.stipa_signal(48000, duration_s=18.0, seed=3)[:24000]
    with pytest.raises(ValueError, match="Signal too short for STIPA"):
        speech.stipa(clip, 48000)


def test_stipa_refuses_levels_of_the_wrong_length_before_its_length() -> None:
    short = speech.stipa_signal(48000, duration_s=5.0, seed=1234)
    with pytest.raises(ValueError, match="'levels'"):
        speech.stipa(short, 48000, levels=[60.0, 60.0])


def test_air_refuses_conditions_that_cannot_hold_together_before_the_domain() -> None:
    with pytest.raises(ValueError, match="cannot hold together"):
        fluids.air(
            temperature_c=20.0,
            static_pressure_pa=1_000.0,
            relative_humidity_percent=50.0,
        )


def test_nipts_refuses_a_duration_that_is_not_finite_before_the_domain() -> None:
    with pytest.raises(ValueError, match="'exposure_duration_years' must be finite"):
        hearing.nipts(l_ex=85.0, exposure_duration_years=float("nan"))


def test_the_binaural_indicators_refuse_a_silent_recording_before_its_length() -> None:
    with pytest.raises(ValueError, match="N5/N95"):
        environment.binaural_indicators(
            np.zeros((2, 24000)), 48000, parameters="loudness"
        )


#: Two octaves, the second of which ISO 3744 Annex E has no A-weighting for.
_OFF_TABLE = [1000.0, 1234.0]
#: The one-third octaves of an ISO 6926 calibration, 125 Hz to 10 kHz.
_CALIBRATION = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 10000.0])


def _events_reverberation() -> object:
    return emission.sound_energy_reverberation(
        np.full((4, 6), 80.0),
        np.full(6, 1.5),
        200.0,
        220.0,
        frequencies=_THIRDS,
        n_events=3,
        background_levels=np.full(6, 60.0),
    )


def _events_comparison() -> object:
    return emission.sound_energy_comparison(
        np.full((4, 6), 80.0),
        np.full(6, 82.0),
        np.full(6, 90.0),
        frequencies=_THIRDS,
        n_events=3,
        background_levels=np.full(6, 60.0),
    )


def _events_hard_walled(**arguments: Any) -> object:
    return emission.sound_energy_hard_walled(
        np.full((1, 7), 80.0),
        np.full((1, 7), 82.0),
        np.full(7, 93.0),
        frequencies=_OCTAVES,
        n_events=3,
        **arguments,
    )


def _events_surface(**arguments: Any) -> object:
    return emission.sound_energy_pressure(
        np.full((20, 2), 80.0), "hemisphere", n_events=3, **arguments
    )


def _two_segments(**arguments: Any) -> object:
    return emission.sound_power_intensity(
        np.full((2, 3), 1e-3), np.ones(2), **arguments
    )


def _anechoic_margin(**arguments: Any) -> object:
    return emission.sound_power_anechoic(
        np.full((20, 2), 80.0),
        "sphere",
        radius=1.0,
        background_levels=np.full((20, 2), 79.0),
        frequencies=[1000.0, 2000.0],
        **arguments,
    )


def _calibration_margin(**arguments: Any) -> object:
    return emission.reference_source_calibration(
        np.full((20, 8), 80.0),
        frequencies=_CALIBRATION,
        arrangement="paths",
        background_levels=np.full((20, 8), 79.0),
        **arguments,
    )


#: A call whose arguments meet an advisory and a refusal both, the advisory
#: computed first, and the refusal it must raise.
_ADVISED_THEN_REFUSED: dict[str, tuple[Callable[[], object], str]] = {
    "energy-reverberation-events": (_events_reverberation, "'integration_time'"),
    "energy-comparison-events": (_events_comparison, "'integration_time'"),
    "energy-hard-walled-events-interval": (
        lambda: _events_hard_walled(background_levels=np.full(7, 50.0)),
        "'integration_time'",
    ),
    "energy-hard-walled-events-temperature": (
        lambda: _events_hard_walled(temperature_c=-300.0),
        "'temperature_c' must be finite",
    ),
    "energy-surface-events-radius": (
        lambda: _events_surface(radius=-1.0),
        "A positive 'radius' is required",
    ),
    "energy-surface-events-bands": (
        lambda: _events_surface(radius=1.0, frequencies=[1000.0]),
        "'frequencies' length must match",
    ),
    "energy-surface-margin-a-weighting": (
        lambda: emission.sound_energy_pressure(
            np.full((20, 2), 80.0),
            "hemisphere",
            radius=1.0,
            background_levels=np.full(2, 78.0),
            integration_time=1.0,
            frequencies=_OFF_TABLE,
        ),
        "No ISO 3744 Annex E A-weighting value for 1234 Hz",
    ),
    "surface-margin-a-weighting": (
        lambda: emission.sound_power_pressure(
            np.full((20, 2), 80.0),
            "hemisphere",
            radius=1.0,
            background_levels=np.full(2, 78.0),
            frequencies=_OFF_TABLE,
        ),
        "No ISO 3744 Annex E A-weighting value for 1234 Hz",
    ),
    "intensity-segments-second-sweep": (
        lambda: _two_segments(normal_intensity_2=np.ones((5, 5))),
        "'normal_intensity_2' must have shape",
    ),
    "intensity-segments-pressure-levels": (
        lambda: _two_segments(pressure_levels=np.ones((5, 5))),
        "'pressure_levels' must have shape",
    ),
    "in-duct-positions-velocity": (
        lambda: emission.sound_power_in_duct(
            np.full((2, 5), 90.0),
            frequencies=[1000.0, 2000.0, 4000.0, 8000.0, 12500.0],
            duct_diameter_m=0.5,
            flow_velocity=50.0,
        ),
        "'flow_velocity' must satisfy",
    ),
    "anechoic-margin-temperature": (
        lambda: _anechoic_margin(temperature_c=-300.0),
        "'temperature_c' must be above",
    ),
    "anechoic-margin-areas": (
        lambda: _anechoic_margin(areas=np.ones(3)),
        "'areas' must have one value per microphone position",
    ),
    "anechoic-margin-coverage": (
        lambda: _anechoic_margin(coverage_factor=0.0),
        "'coverage_factor' must be positive",
    ),
    "calibration-margin-c2": (
        lambda: _calibration_margin(c2=np.nan),
        "'c2' must be finite",
    ),
    "calibration-margin-max-levels": (
        lambda: _calibration_margin(max_levels=np.full((3, 3), 80.0)),
        "'max_levels' must have the shape of 'levels'",
    ),
    "room-constant-atmosphere": (
        lambda: emission.room_constant_from_air_absorption(
            [10000.0, 20000.0],
            volume=1.0e6,
            surface_area=1.0,
            temperature_c=-30.0,
            relative_humidity_percent=50.0,
        ),
        "8 alpha V / S reaches 1",
    ),
}


@pytest.mark.parametrize(
    ("call", "refusal"),
    list(_ADVISED_THEN_REFUSED.values()),
    ids=list(_ADVISED_THEN_REFUSED),
)
def test_an_emission_refusal_found_after_an_advisory_still_comes_first(
    call: Callable[[], object], refusal: str
) -> None:
    """The advisory a helper, a correction or a composed function raises waits.

    Each call computes an advisory before the step that refuses: the count of
    events or segments in the helper that reduces them, the background margin
    of a correction the A-weighted total follows, the K1 margin of
    :func:`~phonometry.emission.sound_power_anechoic` that a calibration
    composes, the atmosphere of the air absorption a room constant composes.
    """
    with pytest.raises(ValueError, match=refusal):
        call()


def _tube_wavenumbers(*frequencies: float) -> np.ndarray:
    """Real air wavenumbers at 343.24 m/s, as the four-microphone cases use them."""
    k = materials.tube_wavenumber(np.array(frequencies), 343.24)
    return np.asarray(k).real.astype(np.complex128)


#: 6 kHz lies above the ASTM E2611-19 plane-wave range of a 0.1 m tube with
#: 30 mm microphone spacings, so a solve given ``diameter_m`` advises on it.
_TUBE_GEOMETRY: dict[str, Any] = {
    "l1": 0.10,
    "s1": 0.03,
    "l2": 0.15,
    "s2": 0.03,
    "thickness_m": 0.05,
    "characteristic_impedance": 1.204 * 343.24,
}
_H = np.array([1.0 + 0j, 0.9 + 0j, 0.5 + 0j])
_LOAD = (_H, 0.8 * _H, 0.5 * _H, 0.4 * _H)


def _advised_one_load(load: _Load = _LOAD, **arguments: Any) -> object:
    return materials.transfer_matrix_one_load(
        load,
        **{
            **_TUBE_GEOMETRY,
            "wavenumber": _tube_wavenumbers(500.0, 1000.0, 6000.0),
            "diameter_m": 0.1,
            **arguments,
        },
    )


def _singular(solve: str, **arguments: Any) -> object:
    """A solve whose loads leave the downstream face without pressure or velocity."""
    load = (
        np.array([1.0 + 0j, 0.9 + 0j]),
        np.array([0.8 + 0j, 0.7 + 0j]),
        np.zeros(2, dtype=np.complex128),
        np.zeros(2, dtype=np.complex128),
    )
    geometry = {
        **_TUBE_GEOMETRY,
        "wavenumber": _tube_wavenumbers(500.0, 1000.0),
        **arguments,
    }
    if solve == "two-load":
        return materials.transfer_matrix_two_load(load, load, **geometry)
    return materials.transfer_matrix_one_load(load, **geometry)


#: Two bands of the four-microphone load, and their wavenumbers at 0 Hz and
#: above: at 0 Hz the wave decomposition divides by sin(0).
_LOW = (_H[:2], 0.8 * _H[:2], 0.5 * _H[:2], 0.4 * _H[:2])
_AT_ZERO_HZ = np.array([0.0 + 0j, 2.0 + 0j])


def _one_load_at_zero_hz(**arguments: Any) -> object:
    return materials.transfer_matrix_one_load(
        _LOW, **{**_TUBE_GEOMETRY, "wavenumber": _AT_ZERO_HZ, **arguments}
    )


def _two_load_at_zero_hz(load_b: _Load) -> object:
    return materials.transfer_matrix_two_load(
        _LOW, load_b, **_TUBE_GEOMETRY, wavenumber=_AT_ZERO_HZ
    )


def _two_microphone(h12: ArrayLike, frequency: ArrayLike, **arguments: Any) -> object:
    return materials.two_microphone_impedance(
        h12,
        **{
            "frequency": frequency,
            "spacing_m": 0.05,
            "x1": 0.1,
            "speed_of_sound": 343.24,
            "characteristic_impedance": 413.0,
            **arguments,
        },
    )


def _reflection_pole() -> np.ndarray:
    """``H12`` equal to the reflected-wave transfer function at both bands."""
    k0 = np.asarray(materials.tube_wavenumber(np.array([500.0, 1000.0]), 343.24))
    return np.asarray(np.exp(1j * k0 * 0.05))


_TEXT_FREQUENCIES = ["a", "b"]

#: An impedance-tube call that meets an advisory, or a NumPy warning, and a
#: refusal both, the warning computed first, and the refusal it must raise.
_TUBE_ADVISED_THEN_REFUSED: dict[
    str, tuple[Callable[[], object], type[Exception], str]
] = {
    "two-load-singular-frequencies": (
        lambda: _singular("two-load", frequencies=_TEXT_FREQUENCIES),
        TypeError,
        "'frequencies' must be numbers",
    ),
    "one-load-singular-frequencies": (
        lambda: _singular("one-load", frequencies=_TEXT_FREQUENCIES),
        TypeError,
        "'frequencies' must be numbers",
    ),
    "two-load-near-singular-frequencies": (
        lambda: materials.transfer_matrix_two_load(
            (1.0 + 0j, 0.9 + 0j, 0.8 + 0j, 0.7 + 0j),
            (1.0 + 0j, 0.9 + 0j, 0.8 + 0j, 0.7 + 0j),
            **_TUBE_GEOMETRY,
            wavenumber=_tube_wavenumbers(500.0, 1000.0),
            frequencies=_TEXT_FREQUENCIES,
        ),
        TypeError,
        "'frequencies' must be numbers",
    ),
    "one-load-plane-wave-load": (
        lambda: _advised_one_load(_LOAD[:3]),  # type: ignore[arg-type]
        ValueError,
        "'load' must be the four transfer functions",
    ),
    "one-load-plane-wave-thickness": (
        lambda: _advised_one_load(thickness_m=-0.05),
        ValueError,
        "'thickness_m' must be positive",
    ),
    "one-load-plane-wave-impedance": (
        lambda: _advised_one_load(characteristic_impedance=-1.0),
        ValueError,
        "'characteristic_impedance' must be positive",
    ),
    "one-load-plane-wave-frequencies": (
        lambda: _advised_one_load(frequencies=["a", "b", "c"]),
        TypeError,
        "'frequencies' must be numbers",
    ),
    "two-load-plane-wave-load-b": (
        lambda: materials.transfer_matrix_two_load(
            _LOAD,
            _LOAD[:2],  # type: ignore[arg-type]
            **_TUBE_GEOMETRY,
            wavenumber=_tube_wavenumbers(500.0, 1000.0, 6000.0),
            diameter_m=0.1,
        ),
        ValueError,
        "'load_b' must be the four transfer functions",
    ),
    "decomposition-plane-wave-text": (
        lambda: materials.wave_decomposition(
            "a",
            _H,
            _H,
            _H,
            l1=0.10,
            s1=0.03,
            l2=0.15,
            s2=0.03,
            wavenumber=_tube_wavenumbers(500.0, 1000.0, 6000.0),
            diameter_m=0.1,
        ),
        TypeError,
        "'h1' must be numbers, not text",
    ),
    "two-microphone-plane-wave-impedance": (
        lambda: _two_microphone(
            _H,
            [50.0, 500.0, 6000.0],
            characteristic_impedance=-413.0,
            diameter_m=0.1,
        ),
        ValueError,
        "'characteristic_impedance' must be positive",
    ),
    "one-load-zero-wavenumber-frequencies": (
        lambda: _one_load_at_zero_hz(frequencies=_TEXT_FREQUENCIES),
        TypeError,
        "'frequencies' must be numbers",
    ),
    "one-load-zero-wavenumber-thickness": (
        lambda: _one_load_at_zero_hz(thickness_m=-0.05),
        ValueError,
        "'thickness_m' must be positive",
    ),
    "two-load-zero-wavenumber-load-b": (
        lambda: _two_load_at_zero_hz(_LOW[:2]),  # type: ignore[arg-type]
        ValueError,
        "'load_b' must be the four transfer functions",
    ),
    "two-load-zero-wavenumber-text": (
        lambda: _two_load_at_zero_hz((_H[:2], _H[:2], _H[:2], ["x", "y"])),
        TypeError,
        "'load_b' must be numbers, not text",
    ),
    "two-microphone-reflection-pole-impedance": (
        lambda: _two_microphone(
            _reflection_pole(), [500.0, 1000.0], characteristic_impedance=-413.0
        ),
        ValueError,
        "'characteristic_impedance' must be positive",
    ),
    "two-microphone-reflection-pole": (
        lambda: _two_microphone(_reflection_pole(), [500.0, 1000.0]),
        ValueError,
        "'reflection' must contain only finite values",
    ),
}


@pytest.mark.parametrize(
    ("call", "refused", "refusal"),
    list(_TUBE_ADVISED_THEN_REFUSED.values()),
    ids=list(_TUBE_ADVISED_THEN_REFUSED),
)
def test_an_impedance_tube_refusal_found_after_a_warning_still_comes_first(
    call: Callable[[], object], refused: type[Exception], refusal: str
) -> None:
    """The plane-wave advisory, the singular solve and NumPy's division wait.

    Each call meets a warning before the step that refuses: the plane-wave
    range of a tube given its diameter, the denominator of a solve whose
    downstream face is silent, the division by ``sin(k s)`` at 0 Hz or by
    ``H_R - H12`` where the two meet. Every argument is checked before any of
    them, and the advisories come once the result stands.
    """
    with pytest.raises(refused, match=refusal):
        call()


#: Three corners where ISO 16283 asks for four, so the low-frequency
#: procedure advises, over the five bands of an ISO 16283 field measurement.
_THREE_CORNERS = np.array([[55.0, 60.0, 50.0], [56.0, 58.0, 52.0], [50.0, 54.0, 56.0]])
_FIELD_BANDS = [50.0, 63.0, 80.0, 100.0, 125.0]
_FIELD_L1 = np.array([80.0, 82.0, 79.0, 75.0, 74.0])
_FIELD_L2 = np.array([50.0, 52.0, 49.0, 45.0, 44.0])
_FIELD_T2 = np.array([0.60, 0.55, 0.50, 0.45, 0.40])


def _three_corner_procedure(
    t63: float | None = 0.7,
) -> building.LowFrequencyProcedure:
    return building.LowFrequencyProcedure(
        volume=18.0, corner_levels=_THREE_CORNERS, reverberation_63_octave=t63
    )


def _facade_with_three_corners(**arguments: Any) -> object:
    return building.facade_insulation(
        _FIELD_L1,
        _FIELD_L2,
        _FIELD_T2,
        **{
            "area": 10.0,
            "volume": 18.0,
            "surface_level": _FIELD_L1,
            "frequencies": _FIELD_BANDS,
            "low_frequency": _three_corner_procedure(),
            **arguments,
        },
    )


#: The one-third-octave bands of ISO 11957 and a room and cabin spectrum.
_CABIN_BANDS = np.array(
    [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0]
    + [800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0]
)
_ROOM_LEVELS = np.linspace(88.0, 80.0, _CABIN_BANDS.size)
_CABIN_LEVELS = _ROOM_LEVELS - np.linspace(10.0, 38.0, _CABIN_BANDS.size)
_DUCT_OCTAVES = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])


def _decaying_ir(samples: int, seed: int = 7) -> np.ndarray:
    """An exponentially decaying noise response sampled at 8 kHz."""
    t = np.arange(samples) / 8000.0
    rng = np.random.default_rng(seed)
    return np.exp(-6.91 * t / 0.5) * rng.standard_normal(samples)


#: Band limits whose two top octaves sit above fs / 2 at 8 kHz, so the bank
#: advises that it drops them.
_PAST_NYQUIST = (500.0, 8000.0)


#: Limits whose top bands an 8 kHz rate cannot hold, so the bank names them.
_OCTAVES_PAST_8_KHZ = (12.0, 20000.0)


def _impulse(samples: int) -> np.ndarray:
    """One unit impulse a little way into a record of *samples* samples."""
    record = np.zeros(samples)
    record[64] = 1.0
    return record


#: Nine microphones of one grid position, recorded below the 44 kHz floor of
#: EN 1793-5 5.5.2, and the same nine one sample shorter.
_GRID = np.tile(_impulse(2048), (9, 1))
_SHORT_GRID = _GRID[:, :-1]
_LOW_RATE = 32000.0

#: Two band spectra of ISO 11546 that stop short of its required bands.
_BOX_WITHOUT = [90.0, 90.0]
_BOX_WITH = [80.0, 80.0]


#: A force record with a second impact a quarter second after the first, and
#: a response, both one second long at 1024 Hz, so the DFT bins are 1 Hz apart.
_IMPACT_FS = 1024.0
_PULSE = np.exp(-0.5 * ((np.arange(1024) / _IMPACT_FS - 0.01) / 0.001) ** 2)
_DOUBLE_IMPACT = _PULSE + 0.6 * np.roll(_PULSE, 245)

#: A sound speed profile whose gradient breaks at 100 m, where the source sits.
_KINKED_DEPTHS = np.array([0.0, 100.0, 300.0, 1000.0])
_KINKED_SPEEDS = np.array([1500.0, 1510.0, 1488.0, 1512.0])


def _beams_from_the_kink(
    fan: underwater.BeamFan, ranges_m: np.ndarray | None = None
) -> object:
    """Gaussian beams launched from the profile's break, 1 km out."""
    return underwater.gaussian_beams(
        200.0,
        _KINKED_DEPTHS,
        _KINKED_SPEEDS,
        source_depth=100.0,
        max_range=1000.0,
        ranges_m=ranges_m,
        n_depth_points=2,
        fan=fan,
        range_step=100.0,
    )


#: A call of another domain that meets an advisory and a refusal both, the
#: advisory computed first, the exception it must raise and its message.
_ADVISED_THEN_REFUSED_ELSEWHERE: dict[
    str, tuple[Callable[[], object], type[Exception], str]
] = {
    "absorption-small-room-reverberation": (
        lambda: materials.absorption_coefficient(-1.0, 1.0, 120.0, 11.0),
        ValueError,
        "'t1' must be positive",
    ),
    "absorption-climate-second-temperature": (
        lambda: materials.absorption_coefficient(
            2.0, 1.0, 200.0, 11.0, temperature1_c=35.0, temperature2_c=-300.0
        ),
        ValueError,
        "'temperature2_c' must be finite and above",
    ),
    "absorption-measurement-climate-reverberation": (
        lambda: materials.measure_sound_absorption(
            [-1.0, 2.0],
            [1.0, 1.0],
            frequencies=[100.0, 125.0],
            volume=200.0,
            area=11.0,
            temperature_c=35.0,
        ),
        ValueError,
        "'t_empty' must be positive",
    ),
    "alternating-airflow-validity-background": (
        lambda: materials.alternating_airflow_resistance(
            80.0,
            70.0,
            piston_stroke_specimen=1e-3,
            piston_stroke_termination=1e-3,
            frequency=1.0,
            cavity_volume=1e-3,
            background_level="x",  # type: ignore[arg-type]
        ),
        TypeError,
        "'background_level' must be one number",
    ),
    "floating-floor-gas-floor-mass": (
        lambda: materials.floating_floor_resonance(
            30.0,
            200.0,
            -1.0,
            airflow_resistivity_kpa_s_m2=5.0,
            thickness_m=0.02,
            porosity=0.9,
        ),
        ValueError,
        "'floor_mass_per_area_kg_m2' must be positive",
    ),
    "low-frequency-corners-reverberation": (
        lambda: building.apply_low_frequency_procedure(
            _FIELD_L2,
            frequencies=_FIELD_BANDS,
            procedure=_three_corner_procedure(t63=None),
            reverberation_time=_FIELD_T2,
            room="receiving",
        ),
        ValueError,
        "needs the 63 Hz octave reverberation time",
    ),
    "airborne-source-corners-receiver-volume": (
        lambda: building.airborne_insulation(
            _FIELD_L1,
            _FIELD_L2,
            _FIELD_T2,
            area=10.0,
            volume=20.0,
            frequencies=_FIELD_BANDS,
            source_low_frequency=_three_corner_procedure(t63=None),
            receiver_low_frequency=_three_corner_procedure(),
        ),
        ValueError,
        "'volume' is 20",
    ),
    "airborne-source-corners-receiver-reverberation": (
        lambda: building.airborne_insulation(
            _FIELD_L1,
            _FIELD_L2,
            _FIELD_T2,
            area=10.0,
            volume=18.0,
            frequencies=_FIELD_BANDS,
            source_low_frequency=_three_corner_procedure(t63=None),
            receiver_low_frequency=_three_corner_procedure(t63=None),
        ),
        ValueError,
        "needs the 63 Hz octave reverberation time",
    ),
    "facade-corners-area": (
        lambda: _facade_with_three_corners(area=-1.0),
        ValueError,
        "'area' must be positive",
    ),
    "lining-resonance-glued-area": (
        lambda: building.lining_improvement(
            10.0, system="mineral_wool", glued_area=150.0
        ),
        ValueError,
        "'glued_area' is a percentage and cannot exceed 100",
    ),
    "cabin-background-margin-a-weighted-pair": (
        lambda: noise_control.cabin_insulation(
            _ROOM_LEVELS,
            _CABIN_LEVELS,
            frequencies=_CABIN_BANDS,
            cabin_background_levels=_CABIN_LEVELS - 2.0,
            method="in-situ-actual-noise",
            a_weighted_room_level=86.4,
        ),
        ValueError,
        "give both 'a_weighted_room_level' and 'a_weighted_cabin_level'",
    ),
    "duct-path-plane-wave-element": (
        lambda: noise_control.duct_path(
            np.full(8, 80.0),
            ["silencer"],  # type: ignore[list-item]
            frequencies=_DUCT_OCTAVES,
            section={"width_m": 0.9144, "height_m": 0.6096},
            flow_velocity=8.0,
        ),
        TypeError,
        "'elements' must hold DuctElement entries",
    ),
    "stage-support-dropped-bands-short-response": (
        lambda: room.stage_support(_decaying_ir(400), fs=8000, limits=_PAST_NYQUIST),
        ValueError,
        "integrates to 0.1 s",
    ),
    "early-lateral-dropped-bands-short-response": (
        lambda: room.early_lateral_energy_fraction(
            _decaying_ir(400), _decaying_ir(400, 8), fs=8000, limits=_PAST_NYQUIST
        ),
        ValueError,
        "integrates to 0.08 s",
    ),
    "late-lateral-dropped-bands-reference": (
        lambda: room.late_lateral_sound_level(
            _decaying_ir(16000),
            _decaying_ir(16000, 8),
            fs=8000,
            limits=_PAST_NYQUIST,
            reference_level=[1.0, 2.0],
        ),
        ValueError,
        "'reference_level' has shape",
    ),
    "strength-dropped-bands-reference": (
        lambda: room.sound_strength(
            _decaying_ir(16000),
            fs=8000,
            limits=_PAST_NYQUIST,
            reference_level=[1.0, 2.0],
        ),
        ValueError,
        "'reference_level' has shape",
    ),
    "nipts-domain-frequency": (
        lambda: hearing.nipts(110.0, 10.0, 0.5, frequencies=[123.0]),
        ValueError,
        "not an ISO 1999 audiometric frequency",
    ),
    "htlan-domain-empty-frequencies": (
        lambda: hearing.htlan(80.0, "male", 95.0, 60.0, 0.5, frequencies=[]),
        ValueError,
        "must carry at least one audiometric frequency",
    ),
    "full-day-spread-instrument": (
        lambda: hearing.full_day_exposure(
            [80.0, 85.0, 90.0],
            8.0,
            instrument="bogus",  # type: ignore[arg-type]
        ),
        ValueError,
        "'instrument' must be one of",
    ),
    "atmospheric-attenuation-temperature-distance": (
        lambda: environment.atmospheric_attenuation(
            [1000.0], temperature_c=60.0, distance=-1.0
        ),
        ValueError,
        "'distance' must be a finite, non-negative number",
    ),
    "outdoor-attenuation-temperature-ground": (
        lambda: environment.outdoor_propagation_attenuation(
            100.0, 1.0, 1.5, temperature_c=60.0, ground_source=2.0
        ),
        ValueError,
        "'ground_source' must be within",
    ),
    "impulsive-adjustment-no-onset-laeq": (
        lambda: environment.impulsive_sound_adjustment(
            0.1 * np.sin(2.0 * np.pi * 1000.0 * np.arange(16000) / 8000.0),
            8000.0,
            laeq="x",  # type: ignore[arg-type]
        ),
        TypeError,
        "'laeq' must be one number",
    ),
    "facade-corners-surface-level": (
        lambda: _facade_with_three_corners(surface_level=_FIELD_L1[:3]),
        ValueError,
        "'surface_level' \\(3,\\), 'l2' \\(5,\\) must all have the same shape",
    ),
    "octave-filter-dropped-bands-empty-signal": (
        lambda: filters.octave_filter(np.array([]), 8000, limits=_OCTAVES_PAST_8_KHZ),
        ValueError,
        "'x' must contain at least one sample",
    ),
    "octave-filter-dropped-bands-text-signal": (
        lambda: filters.octave_filter("abc", 8000, limits=_OCTAVES_PAST_8_KHZ),
        TypeError,
        "'x' must be numbers, not text",
    ),
    "filter-bank-dropped-bands-design": (
        lambda: filters.OctaveFilterBank(
            fs=8000,
            fraction=3,
            limits=_OCTAVES_PAST_8_KHZ,
            design=filters.FilterDesign(filter_type="cheby2", attenuation=2.0),
        ),
        ValueError,
        "cheby2 'attenuation' must be greater than",
    ),
    "enclosure-band-range-a-weighted-pair": (
        lambda: noise_control.enclosure_sound_power_insulation(
            _BOX_WITHOUT,
            _BOX_WITH,
            frequencies=[500.0, 1000.0],
            a_weighted_without=99.0,
        ),
        ValueError,
        "give both 'a_weighted_without' and 'a_weighted_with'",
    ),
    "enclosure-band-range-infinite-a-weighted": (
        lambda: noise_control.enclosure_sound_power_insulation(
            _BOX_WITHOUT,
            _BOX_WITH,
            frequencies=[500.0, 1000.0],
            a_weighted_without=99.0,
            a_weighted_with=np.inf,
        ),
        ValueError,
        "'a_weighted_with'",
    ),
    "direct-sound-rate-record-length": (
        lambda: environment.subtract_direct_sound(
            _impulse(2048), _impulse(2047), _LOW_RATE
        ),
        ValueError,
        "'in_front_ir' and 'free_field_ir' must have the same length",
    ),
    "directivity-rate-record-shape": (
        lambda: environment.source_directivity_corrections(
            _GRID, _SHORT_GRID, _LOW_RATE
        ),
        ValueError,
        "'microphone_irs' and 'specular_irs' must have the same shape",
    ),
    "reflection-index-rate-record-shape": (
        lambda: environment.reflection_index(
            _GRID, _SHORT_GRID, _LOW_RATE, speed_of_sound=343.0
        ),
        ValueError,
        "'in_front_irs' and 'free_field_irs' must have the same shape",
    ),
    "impact-masked-impact-frequency-range": (
        lambda: vibration.impact_mobility(
            _DOUBLE_IMPACT,
            _PULSE,
            _IMPACT_FS,
            force_window_s=0.02,
            frequency_range_hz=(10.2, 10.8),
        ),
        ValueError,
        "holds no DFT bin",
    ),
    "beams-kink-ranges": (
        lambda: _beams_from_the_kink(
            underwater.BeamFan(max_angle_deg=30.0, n_beams=9), np.array([-1.0])
        ),
        ValueError,
        "'ranges_m' must be finite, non-negative and non-empty",
    ),
    "beams-kink-fan": (
        lambda: _beams_from_the_kink(underwater.BeamFan(max_angle_deg=95.0, n_beams=9)),
        ValueError,
        "'max_angle_deg' must lie in",
    ),
    "transfer-stiffness-inequality-shapes": (
        lambda: vibration.transfer_stiffness_indirect(
            [0.5, 0.05], 10.0, frequency=[100.0, 200.0, 300.0]
        ),
        ValueError,
        "'frequency' and 'transmissibility' must have the same shape",
    ),
    "transfer-stiffness-result-inequality-shapes": (
        lambda: vibration.indirect_transfer_stiffness_result(
            [0.5, 0.05], 10.0, frequencies=[100.0, 200.0, 300.0]
        ),
        ValueError,
        "'frequencies' and 'transmissibility' must have the same shape",
    ),
}


@pytest.mark.parametrize(
    ("call", "refused", "refusal"),
    list(_ADVISED_THEN_REFUSED_ELSEWHERE.values()),
    ids=list(_ADVISED_THEN_REFUSED_ELSEWHERE),
)
def test_a_refusal_found_after_an_advisory_still_comes_first(
    call: Callable[[], object], refused: type[Exception], refusal: str
) -> None:
    """Each call advises before a step that refuses, and the refusal is met.

    The advisory comes from a helper or a public function the call composes
    (the room volume, the climate of one measurement of two, the gas term of
    a resilient layer, the validity of an airflow reading), or it was simply
    written ahead of the last checks; every argument is now checked first, or
    the call holds its advisories until its result stands.
    """
    with pytest.raises(refused, match=refusal):
        call()
