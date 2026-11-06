#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every warning of the library is reported at the caller's line, whatever the route.

Python shows a warning at the file and line it is attributed to, a filter by
module reads that file, and the ``default`` action keys its memory of what it
has shown on that line. Each case below provokes one published warning through
a public call made from this file, and every warning the call emits has to name
this file: a ``stacklevel`` counted for one route left 33 of the library's
warnings on a library line, among them every filter bank at 44.1 kHz
(``filters/core.py:698``), the room-volume advisory of the absorption
measurement, the atmospheric absorption reached from the rotorcraft and the
high-frequency sound power routes, a lossy file read or converted, and a
reverberation room measured at too few positions.

The cases hold the routes of those warnings that a short public call reaches
from here, and one public call for most published classes. The routes that
need a flight procedure, a broadcast meter's tone bursts, a metadiffuser, a
power plant contour, a resilient layer, a transfer-stiffness fiche or a
barrier measurement have no case here yet, nor the classes only such a set-up
reaches.
"""

from __future__ import annotations

import inspect
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest

import phonometry
from phonometry import (
    aircraft,
    building,
    emission,
    environment,
    filters,
    fluids,
    hearing,
    io,
    materials,
    metrology,
    noise_control,
    psychoacoustics,
    room,
    signals,
    speech,
    vibration,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_FS = 48000


def _third_octaves() -> np.ndarray:
    return np.array(
        [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600]
        + [2000, 2500, 3150, 4000, 5000],
        dtype=float,
    )


def _absorption_small_room() -> None:
    bands = _third_octaves()
    materials.measure_sound_absorption(
        frequencies=bands,
        t_empty=np.full(bands.size, 9.0),
        t_specimen=np.full(bands.size, 5.0),
        volume=100.0,
        area=10.8,
        temperature_c=20.0,
    )


def _absorption_sample_area() -> None:
    materials.absorption_coefficient(5.0, 3.0, 200.0, 8.0)


def _absorption_temperature() -> None:
    materials.absorption_area(3.0, 200.0, temperature_c=5.0)


def _airflow_static_velocity() -> None:
    velocity = np.array([0.5e-3, 5.0e-3, 20.0e-3])
    materials.static_airflow_resistance(velocity, 12000.0 * velocity, 0.008)


def _airflow_alternating_margin() -> None:
    materials.alternating_airflow_resistance(
        60.0,
        80.0,
        piston_stroke_specimen=14.0e-3,
        piston_stroke_termination=1.4e-3,
        frequency=2.0,
        cavity_volume=1.0e-3,
        background_level=55.0,
    )


def _airflow_alternating_validity() -> None:
    materials.alternating_airflow_resistance(
        70.0,
        70.0,
        piston_stroke_specimen=2.0e-3,
        piston_stroke_termination=1.0e-3,
        frequency=2.0,
        cavity_volume=1.0e-3,
    )


def _impedance_tube_range() -> None:
    c0 = 343.24
    impedance = 1.204 * c0
    f_lower, f_upper = materials.plane_wave_frequency_range(0.03, c0, diameter_m=0.05)
    f = np.array([f_lower * 0.5, 1000.0, f_upper * 1.5])
    k0 = np.asarray(materials.tube_wavenumber(f, c0))
    x1, x2 = 0.12, 0.09
    reflection = 0.3 + 0.1j
    h12 = (np.exp(1j * k0 * x2) + reflection * np.exp(-1j * k0 * x2)) / (
        np.exp(1j * k0 * x1) + reflection * np.exp(-1j * k0 * x1)
    )
    materials.two_microphone_impedance(
        h12,
        frequency=f,
        spacing_m=0.03,
        x1=x1,
        speed_of_sound=c0,
        characteristic_impedance=impedance,
        diameter_m=0.05,
    )


def _impedance_tube_two_load() -> None:
    c0 = 343.24
    f = np.array([500.0, 1000.0])
    k = np.asarray(materials.tube_wavenumber(f, c0)).real.astype(np.complex128)
    load = (1.0 + 0j, 0.9 + 0j, 0.8 + 0j, 0.7 + 0j)
    materials.transfer_matrix_two_load(
        load,
        load,
        thickness_m=0.05,
        wavenumber=k,
        characteristic_impedance=1.204 * c0,
        l1=0.10,
        s1=0.03,
        l2=0.15,
        s2=0.03,
    )


def _dynamic_stiffness_unresolved() -> None:
    materials.floating_floor_resonance(
        25.0,
        200.0,
        100.0,
        airflow_resistivity_kpa_s_m2=5.0,
        thickness_m=0.02,
        porosity=0.9,
    )


def _dynamic_stiffness_disregarded() -> None:
    materials.installed_dynamic_stiffness(
        0.7, airflow_resistivity_kpa_s_m2=5.0, gas_stiffness_n_m3=0.07
    )


def _porous_through_ground() -> None:
    environment.ground_effect(
        np.linspace(200.0, 2000.0, 40), 1.0, 1.0, 10.0, flow_resistivity_pa_s_m2=2e5
    )


def _road_absorption() -> None:
    materials.check_spot_frequency_range([200.0, 500.0, 2000.0])


def _scattering() -> None:
    values = dict.fromkeys(materials.BASE_PLATE_BANDS_HZ, 0.0)
    values[100] = 0.06
    materials.check_base_plate_scattering(values)


def _suspended_ceiling() -> None:
    materials.check_ceiling_specimen(
        area=10.8, depth_mm=200.0, fixture_density_kg_m2=8.0
    )


def _filter_bank_limits() -> None:
    x = np.random.default_rng(42).standard_normal(1000)
    # Limits no other test asks for: the design cache would otherwise hold a
    # bank another test designed first.
    filters.octave_filter(x, 1000, limits=[11.0, 997.0])


def _filter_bank_class() -> None:
    filters.OctaveFilterBank(1000, limits=[10.0, 1000.0])


def _filter_bank_detrend() -> None:
    bank = filters.OctaveFilterBank(
        _FS,
        design=filters.FilterDesign(resample=False),
        block_processing=filters.BlockProcessing(stateful=True),
    )
    bank.filter(np.ones(_FS // 10), detrend=True)


def _atmospheric_absorption() -> None:
    environment.atmospheric_absorption(
        1000.0, temperature_c=-30.0, relative_humidity_percent=50.0
    )


def _fluid_assumption() -> None:
    fluids.ideal_gas(
        temperature_c=20.0, heat_capacity_ratio=1.4, molar_mass_kg_mol=0.029
    )


def _fluid_domain() -> None:
    fluids.air(
        temperature_c=60.0,
        static_pressure_pa=101_325.0,
        relative_humidity_percent=50.0,
    )


def _fluid_through_reciprocity() -> None:
    microphone = metrology.ReciprocityMicrophone(
        equivalent_volume_m3=144e-9,
        resonance_frequency_hz=8200.0,
        loss_factor=1.05,
        front_cavity_volume_m3=0.534e-6,
        front_cavity_depth_m=1.95e-3,
        front_cavity_diameter_m=18.6e-3,
    )
    metrology.check_coupler(
        np.array([250.0, 1000.0]),
        metrology.PlaneWaveCoupler(
            length_m=7.5e-3,
            diameter_m=18.6e-3,
            capillary=metrology.CapillaryTube(
                length_m=0.05, radius_m=1.0 / 6000.0, n_tubes=2
            ),
        ),
        (microphone, microphone, microphone),
        temperature_c=30.0,
        static_pressure_pa=101325.0,
        relative_humidity_percent=50.0,
    )


def _sound_power_reverberation() -> None:
    levels = np.array([[70.0], [80.0], [72.0], [78.0], [71.0], [79.0]])
    emission.sound_power_comparison(levels, np.array([70.0]), np.array([90.0]))


def _sound_power_background() -> None:
    emission.sound_energy_pressure(
        np.full((10, 1), 84.0),
        "hemisphere",
        radius=1.0,
        background_levels=np.full(1, 70.0),
        integration_time=10.0,
    )


def _environmental_measurement() -> None:
    environment.residual_sound_correction(32.2, 29.2)


def _road_device() -> None:
    environment.sound_reflection_rating(np.full(18, 1.2))


def _barrier_in_situ() -> None:
    environment.reference_microphone_height_m(6.0, source_to_barrier_m=1.0)


def _impulse_prominence() -> None:
    environment.impulse_prominence([5.0], [40.0])


def _software_quality() -> None:
    environment.uniform_sample_indices(2001, 20)


def _wind_turbine() -> None:
    frequencies = np.arange(460.0, 542.0, 2.0)
    levels = np.full(frequencies.size, 30.0)
    levels[int(np.argmin(np.abs(frequencies - 500.0)))] = 60.0
    environment.wind_turbine_tonality(
        levels, frequencies=frequencies, tone_frequency=500.0
    )


def _noise_criterion() -> None:
    path = noise_control.duct_path(
        frequencies=[63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0],
        # No 31.5 Hz band: the RC rating says it reads from 31.5 Hz up.
        source_level=[90.0, 86.0, 82.0, 79.0, 77.0, 75.0, 71.0, 61.0],
        elements=[noise_control.DuctElement(label="Silencer", attenuation=50.0)],
        room_effect=6.0,
        criterion="RC",
        target=35.0,
    )
    assert path.rating is not None


def _hvac() -> None:
    noise_control.fan_sound_power(
        2.0, fan_static_pressure_pa=500.0, relative_efficiency_percent=0.8
    )


def _screen_in_situ() -> None:
    noise_control.impulse_mean_level([80.0, 84.0, 82.0])


def _silencer_in_situ() -> None:
    noise_control.measurement_distance_downstream_m(0.25, 0.36)


def _enclosure() -> None:
    noise_control.enclosure_sound_power_insulation(
        [90.0, 90.0], [79.4, 79.6], frequencies=[500.0, 1000.0]
    )


def _plane_wave() -> None:
    noise_control.expansion_chamber([50.0, 100.0, 2000.0], 0.3, 0.02, 0.002)


def _laboratory_insulation() -> None:
    building.background_correction([32.2], [26.2])


def _building_prediction() -> None:
    building.weighted_lining_improvement(160.0, 62.0)


def _low_frequency() -> None:
    building.corner_level([[56.0, 58.0, 54.0], [55.0, 60.0, 53.0], [54.0, 57.0, 56.0]])


def _noise_induced_hearing_loss() -> None:
    hearing.nipts(90.0, 60.0, 0.5)


def _occupational_exposure() -> None:
    hearing.job_based_exposure(
        [88.0, 86.0, 89.0, 86.0, 91.0], 8.0, n_workers=18, sample_duration_hours=0.5
    )


def _auditorium() -> None:
    t = np.arange(int(0.1 * _FS)) / _FS
    room_ir = np.exp(-6.91 * t / 2.0) * np.random.default_rng(1).standard_normal(t.size)
    reference = np.zeros(int(0.05 * _FS))
    reference[10] = 1.0
    room.sound_strength(room_ir, reference, _FS, limits=None)


def _spatial_decay() -> None:
    room.check_background_margin([80.0, 70.0, 66.0], 60.0)


def _tone_burst() -> None:
    signals.tone_burst(_FS, 997.0, 10)


def _human_vibration() -> None:
    x = np.zeros(200)
    x[0] = 10.0
    vibration.crest_factor(x)


def _building_damage() -> None:
    vibration.story_fundamental_frequency(3)


def _calibration() -> None:
    t = np.arange(_FS) / _FS
    tone = (1.0 + 0.05 * np.sin(2 * np.pi * 4 * t)) * np.sin(2 * np.pi * 1000 * t)
    metrology.sensitivity(tone, fs=_FS)


def _sphere_division() -> None:
    metrology.directivity_factor(np.zeros((2, 24)))


def _tonality() -> None:
    t = np.arange(_FS) / _FS
    rng = np.random.default_rng(3)
    x = 0.2 * np.sin(2 * np.pi * 89.1 * t) + 0.002 * rng.standard_normal(t.size)
    psychoacoustics.tone_to_noise_ratio(x, _FS, tone_frequency=89.1)


def _sti() -> None:
    speech.stipa(speech.stipa_signal(_FS, duration_s=5.0, seed=1234), _FS)


def _clipping(tmp_path: Path) -> None:
    io.write(
        tmp_path / "hot.wav", np.array([0.5, 1.5, -2.0, -0.25]), _FS, subtype="PCM_16"
    )


def _clipping_through_convert(tmp_path: Path) -> None:
    x = np.zeros(1000)
    x[::100] = 1.5
    source = tmp_path / "hot.wav"
    io.write(source, x, _FS, subtype="DOUBLE")
    io.convert(source, tmp_path / "narrow.wav", subtype="PCM_16", block_size=100)


def _noise_induced_hearing_loss_through_htlan() -> None:
    hearing.htlan(60, "male", 90.0, 60.0, 0.5)


def _uncertainty() -> None:
    inputs = [
        metrology.Quantity(value=5.0, uncertainty=0.01),
        metrology.Quantity(value=0.02, uncertainty=1e-4),
        metrology.Quantity(value=1.0, uncertainty=0.01),
    ]
    metrology.uncertainty_propagation(lambda v, i, _p: v / i, inputs)


def _impulsive_sound() -> None:
    t = np.arange(2 * _FS) / _FS
    environment.impulsive_sound_adjustment(np.sin(2 * np.pi * 1000.0 * t), _FS)


def _silencer_measurement() -> None:
    noise_control.substitution_area_ratio(0.05, 0.1)


def _fluid_assumption_through_catalogue() -> None:
    fluids.PUBLISHED_GASES["bies-2017-table-c2/methane"].ideal_state(temperature_c=20.0)


def _sound_power_few_positions() -> None:
    levels = np.full((4, 6), 80.0)
    emission.sound_power_comparison(levels, np.full(6, 82.0), np.full(6, 90.0))


def _lossy_read(tmp_path: Path) -> None:
    import soundfile as sf

    path = tmp_path / "note.mp3"
    sf.write(str(path), 0.4 * np.sin(2 * np.pi * 1000 * np.arange(_FS // 2) / _FS), _FS)
    io.read(path)


def _lossy_convert(tmp_path: Path) -> None:
    import soundfile as sf

    source = tmp_path / "note.mp3"
    sf.write(
        str(source), 0.3 * np.sin(2 * np.pi * 997 * np.arange(_FS // 4) / _FS), _FS
    )
    io.convert(source, tmp_path / "expanded.wav")


def _atmospheric_absorption_through_rotorcraft() -> None:
    aircraft.atmospheric_adjustment([12500.0], 1060.0)


def _atmospheric_absorption_through_emission() -> None:
    emission.room_constant_from_air_absorption(
        [12500.0],
        volume=200.0,
        surface_area=220.0,
        temperature_c=-30.0,
        relative_humidity_percent=50.0,
    )


def _cabin_insulation() -> None:
    noise_control.cabin_insulation(
        [88.0, 88.0], [70.0, 68.0], frequencies=[500.0, 1000.0]
    )


def _statistical_pass_by() -> None:
    environment.pass_by_regression(
        [50.0, 80.0, 128.0],
        [70.0, 76.0, 81.0],
        vehicle_category="1",
        road_speed_category="medium",
    )


def _soundscape() -> None:
    noise = 0.01 * np.random.default_rng(5).standard_normal((2, _FS // 2))
    environment.binaural_indicators(noise, _FS, parameters="sound_pressure_level")


def _impulse_response() -> None:
    from scipy import signal

    b, a = signal.butter(2, 0.01)
    pair = room.golay_pair(6)
    responses = [
        signal.lfilter(b, a, np.tile(code, 3))[2 * code.size :] for code in pair
    ]
    room.golay_impulse_response(responses[0], responses[1], pair)


def _transfer_stiffness_unblocked() -> None:
    sweep = np.arange(1.0, 400.0, 0.2)
    force = np.full(sweep.size, 1.0e6 + 0j) * 1.0e-6
    accel = -((2.0 * np.pi * sweep) ** 2) * 1.0e-6 * np.ones(sweep.size)
    output = accel * 1.0e-3
    output[sweep > 300.0] = accel[sweep > 300.0] * 0.2
    vibration.driving_point_stiffness(
        frequencies=sweep,
        input_force_n=force,
        input_acceleration_m_s2=accel,
        output_acceleration_m_s2=output,
    )


#: Each case, by the published warning it provokes. A case that takes
#: ``tmp_path`` is handed one.
_CASES: dict[str, tuple[type[Warning], Callable[..., None]]] = {
    "absorption-small-room": (materials.AbsorptionWarning, _absorption_small_room),
    "absorption-sample-area": (materials.AbsorptionWarning, _absorption_sample_area),
    "absorption-temperature": (materials.AbsorptionWarning, _absorption_temperature),
    "airflow-static": (materials.AirflowResistanceWarning, _airflow_static_velocity),
    "airflow-margin": (materials.AirflowResistanceWarning, _airflow_alternating_margin),
    "airflow-validity": (
        materials.AirflowResistanceWarning,
        _airflow_alternating_validity,
    ),
    "impedance-tube-range": (materials.ImpedanceTubeWarning, _impedance_tube_range),
    "impedance-tube-two-load": (
        materials.ImpedanceTubeWarning,
        _impedance_tube_two_load,
    ),
    "dynamic-stiffness-unresolved": (
        materials.DynamicStiffnessWarning,
        _dynamic_stiffness_unresolved,
    ),
    "dynamic-stiffness-disregarded": (
        materials.DynamicStiffnessWarning,
        _dynamic_stiffness_disregarded,
    ),
    "porous-through-ground": (materials.PorousAbsorberWarning, _porous_through_ground),
    "road-absorption": (materials.RoadAbsorptionWarning, _road_absorption),
    "scattering": (materials.ScatteringDiffusionWarning, _scattering),
    "suspended-ceiling": (materials.SuspendedCeilingWarning, _suspended_ceiling),
    "filter-bank-octave-filter": (filters.FilterBankWarning, _filter_bank_limits),
    "filter-bank-class": (filters.FilterBankWarning, _filter_bank_class),
    "filter-bank-detrend": (filters.FilterBankWarning, _filter_bank_detrend),
    "atmospheric-absorption": (
        environment.AtmosphericAbsorptionWarning,
        _atmospheric_absorption,
    ),
    "fluid-assumption": (fluids.FluidAssumptionWarning, _fluid_assumption),
    "fluid-domain": (fluids.FluidWarning, _fluid_domain),
    "fluid-through-reciprocity": (fluids.FluidWarning, _fluid_through_reciprocity),
    "sound-power-reverberation": (
        emission.SoundPowerWarning,
        _sound_power_reverberation,
    ),
    "sound-power-background": (emission.SoundPowerWarning, _sound_power_background),
    "environmental-measurement": (
        environment.EnvironmentalMeasurementWarning,
        _environmental_measurement,
    ),
    "road-device": (environment.RoadDeviceWarning, _road_device),
    "barrier-in-situ": (environment.BarrierInSituWarning, _barrier_in_situ),
    "impulse-prominence": (environment.ImpulseProminenceWarning, _impulse_prominence),
    "software-quality": (environment.SoftwareQualityWarning, _software_quality),
    "wind-turbine": (environment.WindTurbineNoiseWarning, _wind_turbine),
    "noise-criterion": (room.NoiseCriterionWarning, _noise_criterion),
    "hvac": (noise_control.HVACWarning, _hvac),
    "screen-in-situ": (noise_control.ScreenInSituWarning, _screen_in_situ),
    "silencer-in-situ": (noise_control.SilencerInSituWarning, _silencer_in_situ),
    "enclosure": (noise_control.EnclosureInsulationWarning, _enclosure),
    "plane-wave": (noise_control.PlaneWaveWarning, _plane_wave),
    "laboratory-insulation": (
        building.LaboratoryInsulationWarning,
        _laboratory_insulation,
    ),
    "building-prediction": (building.BuildingPredictionWarning, _building_prediction),
    "low-frequency": (building.LowFrequencyWarning, _low_frequency),
    "noise-induced-hearing-loss": (
        hearing.NoiseInducedHearingLossWarning,
        _noise_induced_hearing_loss,
    ),
    "occupational-exposure": (
        hearing.OccupationalExposureWarning,
        _occupational_exposure,
    ),
    "auditorium": (room.AuditoriumWarning, _auditorium),
    "spatial-decay": (room.SpatialDecayWarning, _spatial_decay),
    "tone-burst": (signals.ToneBurstWarning, _tone_burst),
    "human-vibration": (vibration.HumanVibrationWarning, _human_vibration),
    "building-damage": (vibration.BuildingDamageWarning, _building_damage),
    "calibration": (metrology.CalibrationWarning, _calibration),
    "sphere-division": (metrology.SphereDivisionWarning, _sphere_division),
    "tonality": (psychoacoustics.TonalityWarning, _tonality),
    "sti": (speech.STIWarning, _sti),
    "noise-induced-hearing-loss-through-htlan": (
        hearing.NoiseInducedHearingLossWarning,
        _noise_induced_hearing_loss_through_htlan,
    ),
    "uncertainty": (metrology.UncertaintyWarning, _uncertainty),
    "impulsive-sound": (environment.ImpulsiveSoundWarning, _impulsive_sound),
    "silencer-measurement": (
        noise_control.SilencerMeasurementWarning,
        _silencer_measurement,
    ),
    "fluid-assumption-through-catalogue": (
        fluids.FluidAssumptionWarning,
        _fluid_assumption_through_catalogue,
    ),
    "clipping": (io.ClippingWarning, _clipping),
    "clipping-through-convert": (io.ClippingWarning, _clipping_through_convert),
    "sound-power-few-positions": (
        emission.SoundPowerWarning,
        _sound_power_few_positions,
    ),
    "lossy-read": (io.LossyCompressionWarning, _lossy_read),
    "lossy-convert": (io.LossyCompressionWarning, _lossy_convert),
    "atmospheric-absorption-through-rotorcraft": (
        environment.AtmosphericAbsorptionWarning,
        _atmospheric_absorption_through_rotorcraft,
    ),
    "atmospheric-absorption-through-emission": (
        environment.AtmosphericAbsorptionWarning,
        _atmospheric_absorption_through_emission,
    ),
    "cabin-insulation": (noise_control.CabinInsulationWarning, _cabin_insulation),
    "statistical-pass-by": (
        environment.StatisticalPassByWarning,
        _statistical_pass_by,
    ),
    "soundscape": (environment.SoundscapeWarning, _soundscape),
    "impulse-response": (room.ImpulseResponseWarning, _impulse_response),
    "transfer-stiffness-unblocked": (
        vibration.TransferStiffnessWarning,
        _transfer_stiffness_unblocked,
    ),
}


@pytest.mark.parametrize("case", sorted(_CASES))
def test_a_warning_names_the_line_that_made_the_call(case: str, tmp_path: Path) -> None:
    category, call = _CASES[case]
    arguments = (
        {"tmp_path": tmp_path}
        if "tmp_path" in inspect.signature(call).parameters
        else {}
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        call(**arguments)
    emitted = [
        w for w in caught if issubclass(w.category, phonometry.PhonometryWarning)
    ]
    assert any(issubclass(w.category, category) for w in emitted), (
        f"{case} emitted no {category.__name__}: "
        f"{[w.category.__name__ for w in caught]}"
    )
    elsewhere = [
        f"{w.category.__name__} at {w.filename}:{w.lineno}"
        for w in emitted
        if w.filename != __file__
    ]
    assert not elsewhere, f"{case}: " + "; ".join(elsewhere)
