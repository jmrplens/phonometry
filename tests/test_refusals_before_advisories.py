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
from typing import Any

import numpy as np
import pytest

from phonometry import (
    emission,
    environment,
    fluids,
    hearing,
    materials,
    noise_control,
    room,
    signals,
    speech,
    vibration,
)


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
    c0 = 343.24
    k = np.asarray(materials.tube_wavenumber(np.array([500.0, 1000.0]), c0))
    load = (1.0 + 0j, 0.9 + 0j, 0.8 + 0j, 0.7 + 0j)
    # A RuntimeWarning of NumPy's is handed back when the block ends, and the
    # filter above raises it.
    with pytest.warns(materials.ImpedanceTubeWarning, match="near-singular") as seen:
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
    assert len(seen) == 1
    assert not np.all(np.isfinite(matrix.t11))


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
