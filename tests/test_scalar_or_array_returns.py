#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A function of a number or an array of them returns what its overloads say.

An array in, an array out: such a function returns a Python ``float`` (a
string, for a grade) only when every argument that decides the shape of the
result is a number, and an array as soon as one of them is a sequence or a
numpy array, a zero-dimensional array included. Its ``typing.overload``
heads say the same to a type checker, and these tests hold the runtime to
them, call by call:

* every public function whose heads tell a single value from an array has a
  case here, so a new one cannot ship without its runtime being checked;
* with numbers, Python or numpy ones, it returns a ``float``, compared with
  ``type(r) is float`` so that a ``numpy.float64`` (which is a ``float``
  subclass) does not pass for one;
* with each deciding argument in turn given as a list, it returns an array,
  and as a zero-dimensional array it returns a zero-dimensional array, each
  holding the value the numbers gave.

The functions keyed on another argument (``axis``, ``limits``, ``weighted``,
a missing ``frequency``) have a test of their own below.
"""

from __future__ import annotations

import ast
import functools
import importlib
import inspect
import pathlib
import sys
import types
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

import phonometry
from phonometry import (
    aircraft,
    broadcast,
    building,
    electroacoustics,
    emission,
    environment,
    fluids,
    hearing,
    materials,
    metrology,
    noise_control,
    psychoacoustics,
    room,
    signals,
    simulation,
    underwater,
    vibration,
)

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_return_overloads as cro

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from numpy.typing import NDArray

_ZONES = vibration.ZoneBoundaries(a_b=1.0, b_c=2.0, c_d=3.0)


@dataclass(frozen=True)
class Case:
    """One call of a function of a number or an array of them.

    :ivar function: The public function or method, as a caller reaches it.
    :ivar arguments: Keyword arguments that make a valid call, every deciding
        one a Python number.
    :ivar deciding: The arguments whose shape the result follows.
    :ivar single: What the function returns for numbers: ``float``,
        ``complex`` for a complex result, or ``str`` for a grade.
    :ivar together: Whether the deciding arguments take one shape between
        them (one value per band each) rather than broadcasting, so that a
        sequence is given to all of them at once.
    :ivar increasing: Whether the deciding argument is an axis that must
        increase (a frequency axis), so that a sequence of it holds the
        number and its double rather than the number twice.
    :ivar label: Tells two cases of one function apart.
    """

    function: Callable[..., object]
    arguments: Mapping[str, Any]
    deciding: tuple[str, ...]
    single: type = float
    together: bool = False
    increasing: bool = False
    label: str = field(default="")

    @property
    def name(self) -> str:
        """The qualified name of the function, which the cases are keyed by."""
        target = inspect.unwrap(self.function)
        return f"{target.__module__}.{target.__qualname__}"

    def call(self, **changed: object) -> object:
        """Call the function with *changed* in place of the case's arguments."""
        return self.function(**{**self.arguments, **changed})


def _cases() -> tuple[Case, ...]:
    modes = room.room_modes(
        (7.0, 5.0, 3.0), max_frequency=120.0, reverberation_time=0.8
    )
    shear = environment.wind_shear_profile(5.0, 9.0, upper_height_m=120.0)
    sel = environment.sel_distribution(
        [30.0, 33.0, 36.0, 41.0, 45.0], [0.3, 0.3, 0.2, 0.15, 0.05]
    )
    box = (7.0, 5.0, 3.0)
    impedance = electroacoustics.loop_impedance(2.0, 1.0e-4)
    record = np.zeros(4800)
    record[288] = 96000.0
    record[624] = 0.3 * 96000.0
    windowed = metrology.time_selective_response(
        record, 96000.0, window_start_s=0.0025, window_end_s=0.006
    )
    microphone = metrology.ReciprocityMicrophone(
        equivalent_volume_m3=144e-9,
        resonance_frequency_hz=8200.0,
        loss_factor=1.0,
        front_cavity_volume_m3=0.534e-6,
        front_cavity_depth_m=1.95e-3,
        front_cavity_diameter_m=18.6e-3,
    )
    mode = vibration.SingleModeFitResult(
        frequencies=np.array([30.0, 40.0, 50.0]),
        frf=np.array([1.0e-3 + 0.0j, 2.0e-3 + 1.0e-3j, 1.0e-3 + 0.0j]),
        pole_rad_s=complex(-5.0, 2.0 * np.pi * 40.0),
        residue=complex(0.0, -1.0e-2),
        direct_term=0.0j,
    )
    contour = simulation.ContourPhasors(
        frequency=500.0,
        positions=np.array([[0.1, 0.0], [0.0, 0.1], [-0.1, 0.0], [0.0, -0.1]]),
        normals=np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]]),
        pressure=np.array([1.0 + 0.0j, 1.0j, -1.0 + 0.0j, -1.0j]),
        normal_velocity=np.array([1.0e-3 + 0.0j, 1.0e-3j, -1.0e-3 + 0.0j, -1.0e-3j]),
        segment=0.157,
    )
    sdof = {"frequency": 10.0, "mass": 1.0, "stiffness": 1.0e4, "damping": 5.0}
    beam = {"frequency": 100.0, "bending_stiffness": 1.0e3, "mass_per_length": 10.0}
    amplifier = electroacoustics.amplifier_frequency_response(
        frequencies=[50.0, 100.0, 1000.0, 8000.0],
        output_current_a=[1.0, 1.9, 2.0, 1.5],
    )
    resonator = materials.HelmholtzResonator(
        neck_length_m=0.01, neck_side_m=0.01, cavity_length_m=0.05, cavity_side_m=0.05
    )
    plane = aircraft.mean_ground_plane([0.0, 100.0, 200.0], [0.0, 1.0, 3.0])
    profile = environment.linear_sound_speed_profile(0.1)
    pulse = metrology.RectangularPulse(duration_s=1.0e-3, amplitude_v=1.0)
    thirds = np.array(
        [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
         2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000],
        dtype=float,
    )  # fmt: skip
    calibration = emission.reference_source_calibration(
        78.0 + np.linspace(-1.0, 1.0, 20)[:, None] + np.zeros(thirds.size),
        frequencies=thirds,
        arrangement="fixed",
    )
    return (
        Case(
            broadcast.channel_weight,
            {"azimuth": 90.0, "elevation": 10.0},
            ("azimuth", "elevation"),
        ),
        Case(electroacoustics.piston_resistance, {"x": 1.0}, ("x",)),
        Case(electroacoustics.piston_reactance, {"x": 1.0}, ("x",)),
        Case(
            electroacoustics.piston_directivity,
            {"ka": 2.0, "theta": 0.3},
            ("ka", "theta"),
        ),
        Case(
            electroacoustics.field_strength_level,
            {"field_strength_a_per_m": 0.1},
            ("field_strength_a_per_m",),
        ),
        Case(electroacoustics.field_strength, {"level": -12.0}, ("level",)),
        Case(
            electroacoustics.magnetic_flux_density,
            {"field_strength_a_per_m": 0.4},
            ("field_strength_a_per_m",),
        ),
        Case(electroacoustics.telecoil_response, {"angle_deg": 45.0}, ("angle_deg",)),
        Case(impedance.at, {"frequency_hz": 1000.0}, ("frequency_hz",)),
        Case(
            impedance.drive_voltage,
            {"current_a": 3.0, "frequency_hz": 1000.0},
            ("frequency_hz",),
        ),
        Case(
            emission.plant_background_correction,
            {"level_difference": 8.0},
            ("level_difference",),
        ),
        Case(emission.local_environmental_correction, {"ratio": 0.5}, ("ratio",)),
        Case(emission.precision_uncertainty, {"sigma_r0": 0.5}, ("sigma_r0",)),
        Case(
            emission.turbine_background_correction,
            {"level_difference": 8.0},
            ("level_difference",),
        ),
        Case(
            emission.environmental_ratio_from_absorption,
            {
                "absorption_area": 50.0,
                "measurement_surface_m2": 20.0,
                "directivity_index": 1.0,
            },
            ("absorption_area", "directivity_index"),
        ),
        Case(
            emission.environmental_ratio_from_k2,
            {"environmental_correction": 1.0, "directivity_index": 1.0},
            ("environmental_correction", "directivity_index"),
        ),
        Case(
            emission.emission_sound_pressure_level,
            {
                "measured_level": 80.0,
                "background_correction": 0.5,
                "local_correction": 1.0,
            },
            ("measured_level", "background_correction", "local_correction"),
        ),
        Case(
            emission.excess_sound_pressure_level,
            {"level": 80.0, "reference_sound_power_levels": 90.0, "distance": 2.0},
            ("level", "reference_sound_power_levels", "distance"),
        ),
        Case(
            emission.environmental_correction,
            {"surface_area": 20.0, "absorption_area": 50.0},
            ("absorption_area",),
            label="absorption area",
        ),
        Case(
            emission.environmental_correction,
            {"surface_area": 20.0, "reverberation_time": 1.0, "volume": 100.0},
            ("reverberation_time",),
            label="reverberation time",
        ),
        Case(
            emission.environmental_correction,
            {
                "surface_area": 20.0,
                "mean_absorption_coefficient": 0.3,
                "room_surface": 150.0,
            },
            ("mean_absorption_coefficient",),
            label="mean absorption",
        ),
        Case(
            environment.method_a_scale_values,
            {"positions": 2.0, "part": 1},
            ("positions",),
        ),
        Case(
            environment.method_b_scale_values,
            {"marked_fraction": 0.5},
            ("marked_fraction",),
        ),
        Case(
            environment.amplitude_modulation_adjustment,
            {"modulation_depth_db": 4.0},
            ("modulation_depth_db",),
        ),
        Case(
            environment.logarithmic_wind_speed,
            {"reference_speed_m_s": 5.0, "height_m": 100.0, "reference_height_m": 10.0},
            ("reference_speed_m_s",),
        ),
        Case(
            environment.power_law_wind_speed,
            {
                "reference_speed_m_s": 5.0,
                "height_m": 100.0,
                "reference_height_m": 10.0,
                "shear_exponent": 0.2,
            },
            ("reference_speed_m_s", "shear_exponent"),
        ),
        Case(
            environment.wind_shear_exponent,
            {
                "speed_m_s": 7.0,
                "reference_speed_m_s": 5.0,
                "height_m": 100.0,
                "reference_height_m": 10.0,
            },
            ("speed_m_s", "reference_speed_m_s"),
        ),
        Case(
            environment.background_level_increase,
            {"measured_level": 70.0, "background_level": 60.0},
            ("measured_level", "background_level"),
            together=True,
        ),
        Case(
            environment.predicted_prominence,
            {"onset_rate": 1000.0, "level_difference": 30.0},
            ("onset_rate", "level_difference"),
        ),
        Case(environment.impulse_adjustment, {"prominence": 10.0}, ("prominence",)),
        Case(shear.speed_at, {"height_m": 80.0}, ("height_m",)),
        Case(sel.class_density, {"levels": 35.0}, ("levels",)),
        Case(sel.density, {"levels": 35.0}, ("levels",)),
        Case(sel.exceedance, {"levels": 35.0}, ("levels",)),
        Case(sel.exceedance_level, {"percent": 10.0}, ("percent",)),
        Case(
            fluids.sea_water_sound_speed,
            {"temperature_c": 10.0, "salinity_psu": 35.0, "depth_m": 100.0},
            ("temperature_c", "salinity_psu", "depth_m"),
        ),
        Case(
            hearing.min_significant_difference,
            {"expanded_uncertainty_db": 2.0},
            ("expanded_uncertainty_db",),
        ),
        Case(
            materials.apparent_dynamic_stiffness,
            {"resonant_frequency_hz": 50.0, "total_mass_per_area_kg_m2": 8.0},
            ("resonant_frequency_hz",),
        ),
        Case(
            materials.enclosed_gas_stiffness,
            {"thickness_m": 0.02, "porosity": 0.9},
            ("thickness_m",),
        ),
        Case(
            materials.natural_frequency,
            {"dynamic_stiffness_n_m3": 1.0e7, "mass_per_area_kg_m2": 100.0},
            ("dynamic_stiffness_n_m3",),
        ),
        Case(
            noise_control.plenum_attenuation,
            {
                "exit_area": 0.5,
                "line_of_sight": 2.0,
                "wall_area": 20.0,
                "mean_absorption": 0.3,
            },
            ("mean_absorption",),
        ),
        Case(
            noise_control.room_effect,
            {"distance": 2.0, "room_constant": 50.0, "directivity": 2.0},
            ("room_constant", "directivity"),
            label="room constant",
        ),
        Case(
            noise_control.room_effect,
            {"distance": 2.0, "absorption_area": 50.0, "directivity": 2.0},
            ("absorption_area", "directivity"),
            label="absorption area",
        ),
        Case(psychoacoustics.erb_bandwidth, {"frequency": 1000.0}, ("frequency",)),
        Case(psychoacoustics.cam_from_frequency, {"frequency": 1000.0}, ("frequency",)),
        Case(psychoacoustics.frequency_from_cam, {"cam": 15.0}, ("cam",)),
        Case(modes.density, {"frequency": 100.0}, ("frequency",)),
        Case(
            room.absorption_per_table,
            {"distance": 1.0, "speech_to_noise": 3.0},
            ("distance",),
        ),
        Case(room.air_absorption_area, {"m": 0.001, "volume": 100.0}, ("m",)),
        Case(
            room.critical_distance,
            {"room_constant": 50.0, "directivity": 2.0},
            ("room_constant", "directivity"),
            label="room constant",
        ),
        Case(
            room.critical_distance,
            {"absorption_area": 50.0, "directivity": 2.0},
            ("absorption_area", "directivity"),
            label="absorption area",
        ),
        Case(
            room.crowd_noise_level,
            {"talkers": 10.0, "absorption_area": 50.0},
            ("talkers", "absorption_area"),
        ),
        Case(room.filter_bandwidth, {"center": 1000.0}, ("center",)),
        Case(
            room.free_field_reference_level,
            {"level": 80.0, "distance": 10.0},
            ("level",),
        ),
        Case(room.hard_object_absorption, {"object_volume": 0.65}, ("object_volume",)),
        Case(room.min_receiver_positions, {"seats": 800.0}, ("seats",)),
        Case(
            room.min_reliable_reverberation_time, {"bandwidth": 100.0}, ("bandwidth",)
        ),
        Case(room.reflection_density, {"time": 0.1, "volume": 100.0}, ("time",)),
        Case(
            room.reverberation_room_reference_level,
            {"reverberation_room_level": 80.0, "absorption_area": 20.0},
            ("reverberation_room_level", "absorption_area"),
        ),
        Case(
            room.reverberation_time,
            {"absorption_area": 20.0, "volume": 100.0},
            ("absorption_area",),
        ),
        Case(
            room.room_constant,
            {"surface_area": 100.0, "mean_absorption": 0.2},
            ("mean_absorption",),
        ),
        Case(
            room.room_modal_density,
            {"dimensions": box, "frequency": 100.0},
            ("frequency",),
        ),
        Case(
            room.room_mode_count,
            {"dimensions": box, "frequency": 100.0},
            ("frequency",),
        ),
        Case(
            room.sabine_absorption_area,
            {"volume": 100.0, "reverberation_time": 1.0},
            ("reverberation_time",),
        ),
        Case(
            room.schroeder_frequency,
            {"reverberation_time": 1.0, "volume": 100.0},
            ("reverberation_time",),
        ),
        Case(
            room.sound_strength_from_power,
            {"pressure_level": 80.0, "power_level": 90.0},
            ("pressure_level", "power_level"),
        ),
        Case(room.speech_direct_level, {"distance": 1.0}, ("distance",)),
        Case(
            room.speech_to_noise_ratio,
            {"distance": 1.0, "absorption_per_table": 5.0},
            ("distance", "absorption_per_table"),
        ),
        Case(
            vibration.allowable_velocity,
            {
                "frequency": 50.0,
                "constant_velocity_mm_s": 4.5,
                "corner_low_hz": 10.0,
                "corner_high_hz": 1000.0,
            },
            ("frequency",),
        ),
        Case(
            vibration.gear_housing_velocity_limit,
            {"frequency": 50.0, "rating": 4.5},
            ("frequency",),
        ),
        Case(
            vibration.gear_shaft_displacement_limit,
            {"frequency": 50.0, "rating": 100.0},
            ("frequency",),
        ),
        Case(
            vibration.bending_stress,
            {
                "peak_velocity_m_s": 0.01,
                "dynamic_modulus_pa": 3.0e10,
                "density": 2400.0,
            },
            ("peak_velocity_m_s",),
        ),
        Case(
            vibration.guideline_velocity,
            {"building_class": "residential", "frequency": 20.0},
            ("frequency",),
        ),
        Case(vibration.height_fundamental_frequency, {"height_m": 30.0}, ("height_m",)),
        Case(vibration.injury_probability, {"risk": 0.5}, ("risk",)),
        Case(vibration.ultimate_strength, {"age": 40.0}, ("age",)),
        Case(
            vibration.evaluation_zone,
            {"magnitude": 2.5, "boundaries": _ZONES},
            ("magnitude",),
            single=str,
        ),
        Case(
            vibration.industrial_machine_zone,
            {
                "group": "group_1",
                "support": "rigid",
                "displacement_um": 40.0,
                "velocity_mm_s": 2.0,
            },
            ("displacement_um", "velocity_mm_s"),
            single=str,
        ),
        Case(amplifier.at, {"frequency_hz": 200.0}, ("frequency_hz",)),
        Case(building.reverberation_index, {"t": 0.8}, ("t",)),
        Case(
            building.surface_pressure_intensity_indicator,
            {"lp": 70.0, "l_in": 65.0},
            ("lp", "l_in"),
            together=True,
        ),
        Case(
            building.background_correction,
            {"signal_and_background": 60.0, "background": 40.0},
            ("signal_and_background", "background"),
            together=True,
        ),
        Case(
            building.low_frequency_level,
            {"level": 40.0, "corner": 45.0},
            ("level", "corner"),
            together=True,
        ),
        Case(
            building.structure_borne_power_level,
            {
                "velocity_level": 60.0,
                "mass_per_area": 200.0,
                "area": 10.0,
                "loss_factor": 0.02,
                "frequency": 500.0,
            },
            ("velocity_level", "loss_factor", "frequency"),
        ),
        Case(
            building.equivalent_blocked_force_level,
            {"power_level": 80.0, "plate_mobility": 1.0e-5},
            ("power_level", "plate_mobility"),
        ),
        Case(
            building.characteristic_reception_plate_power,
            {"blocked_force_level": 70.0},
            ("blocked_force_level",),
        ),
        Case(
            building.equivalent_free_velocity_level,
            {"power_level": 80.0, "plate_mobility": 1.0e-3},
            ("power_level", "plate_mobility"),
        ),
        Case(
            building.source_mobility_from_levels,
            {"free_velocity_level": 90.0, "blocked_force_level": 70.0},
            ("free_velocity_level", "blocked_force_level"),
        ),
        Case(
            building.coupling_term,
            {
                "source_mobility": 1.0e-4,
                "receiver_mobility": 1.0e-5,
                "transfer_mobility": 1.0e-6,
            },
            ("source_mobility", "receiver_mobility", "transfer_mobility"),
        ),
        Case(
            building.coupling_term_force_source,
            {"source_mobility": 1.0e-4, "receiver_mobility": 1.0e-5},
            ("source_mobility", "receiver_mobility"),
        ),
        Case(
            building.coupling_term_velocity_source,
            {"source_mobility": 1.0e-4, "receiver_impedance": 1.0e5},
            ("source_mobility", "receiver_impedance"),
        ),
        Case(
            building.installed_power_from_reception_plate,
            {"reception_plate_level": 80.0, "receiver_mobility": 1.0e-5},
            ("reception_plate_level", "receiver_mobility"),
        ),
        Case(
            building.installed_structure_borne_power_level,
            {"characteristic_power_level": 80.0, "coupling_term": -5.0},
            ("characteristic_power_level", "coupling_term"),
        ),
        Case(
            building.structure_borne_pressure_level_path,
            {
                "installed_power_level": 80.0,
                "adjustment_term": -5.0,
                "flanking_reduction_index": 50.0,
                "element_area": 10.0,
            },
            ("installed_power_level", "adjustment_term", "flanking_reduction_index"),
        ),
        Case(
            building.structure_to_airborne_adjustment,
            {
                "frequency": 500.0,
                "critical_frequency": 100.0,
                "mass_per_area": 200.0,
                "radiation_factor": 1.0,
            },
            ("frequency", "radiation_factor"),
        ),
        Case(
            building.tapping_machine_characteristic_power_level,
            {"force_level": 80.0, "frequency": 500.0},
            ("force_level", "frequency"),
        ),
        Case(
            building.tapping_machine_coupling_term,
            {"receiver_mobility": 1.0e-5, "frequency": 500.0},
            ("receiver_mobility", "frequency"),
        ),
        Case(
            building.tapping_machine_force_level_estimate,
            {"frequency": 500.0},
            ("frequency",),
        ),
        Case(building.transmission_loss_from_coefficient, {"tau": 0.01}, ("tau",)),
        Case(
            building.mass_law_transmission_loss,
            {"frequency": 500.0, "mass_per_area": 10.0},
            ("frequency",),
        ),
        Case(
            building.force_pulse,
            {"time": 1.0e-3, "contact_stiffness": 1.0e7, "impedance": 1.0e4},
            ("time",),
        ),
        Case(vibration.transfer_stiffness_level, {"stiffness": 2.0}, ("stiffness",)),
        Case(vibration.loss_factor, {"stiffness": 2.0}, ("stiffness",)),
        Case(
            vibration.random_error_percent,
            {"coherence": 0.8, "n_averages": 10},
            ("coherence",),
        ),
        Case(
            vibration.corner_transmission_coefficient,
            {"angle_rad": 0.3, "chi": 1.0, "psi": 1.0},
            ("angle_rad",),
        ),
        Case(
            vibration.straight_transmission_coefficient,
            {"angle_rad": 0.3, "chi": 1.0, "psi": 1.0},
            ("angle_rad",),
        ),
        Case(
            vibration.coupling_loss_factor,
            {
                "transmission_coefficient": 0.1,
                "group_velocity": 100.0,
                "junction_length": 4.0,
                "plate_area": 10.0,
                "frequency": 500.0,
            },
            ("transmission_coefficient", "frequency"),
        ),
        Case(
            vibration.point_connection_coupling_loss_factor,
            {
                "frequency": 500.0,
                "n_connections": 4,
                "thickness1_m": 0.1,
                "thickness2_m": 0.1,
                "surface_density1": 200.0,
                "surface_density2": 200.0,
                "wave_speed1": 3000.0,
                "wave_speed2": 3000.0,
                "plate_area1": 10.0,
            },
            ("frequency",),
        ),
        Case(
            vibration.wave_vibration_reduction_index,
            {"transmission_coefficient": 0.1, "critical_frequency_receiver": 100.0},
            ("transmission_coefficient",),
        ),
        Case(emission.normal_intensity_from_levels, {"levels": 80.0}, ("levels",)),
        Case(
            emission.reverberation_parameter,
            {"frequencies": 1000.0, "volume": 70.0},
            ("frequencies",),
        ),
        Case(
            emission.special_room_background_correction,
            {"levels": 70.0, "background_levels": 62.0},
            ("levels", "background_levels"),
        ),
        Case(
            emission.phase_mismatch_from_residual_index,
            {"residual_index": 10.0, "spacing_m": 0.012, "frequency": 1000.0},
            ("residual_index", "frequency"),
        ),
        Case(
            emission.residual_index_from_phase_mismatch,
            {"phase_mismatch_deg": 0.3, "spacing_m": 0.012, "frequency": 1000.0},
            ("phase_mismatch_deg", "frequency"),
        ),
        Case(
            emission.background_noise_correction,
            {"source_levels": 70.0, "background_levels": 60.0},
            ("source_levels", "background_levels"),
            together=True,
        ),
        Case(
            emission.air_absorption_np_per_m,
            {
                "frequencies": 16000.0,
                "temperature_c": 20.0,
                "relative_humidity_percent": 50.0,
            },
            ("frequencies",),
        ),
        Case(
            emission.free_field_absorption_correction,
            {
                "frequencies": 16000.0,
                "radius": 3.0,
                "temperature_c": 20.0,
                "relative_humidity_percent": 50.0,
            },
            ("frequencies",),
        ),
        Case(
            emission.free_field_absorption_correction,
            {
                "frequencies": 16000.0,
                "radius": 1.0,
                "temperature_c": 20.0,
                "relative_humidity_percent": 50.0,
            },
            ("frequencies",),
            label="no correction within 2 m",
        ),
        Case(emission.velocity_level, {"velocity": 1.0e-3}, ("velocity",)),
        Case(
            emission.velocity_level_from_acceleration,
            {"peak_acceleration": 1.0, "frequency": 100.0},
            ("peak_acceleration", "frequency"),
        ),
        Case(
            emission.radiation_factor,
            {"sound_power": 1.0e-3, "area": 2.0, "mean_square_velocity": 1.0e-6},
            ("sound_power", "mean_square_velocity"),
        ),
        Case(
            emission.radiated_sound_power_level,
            {"velocity_level": 90.0, "area": 2.0, "radiation_factor": 0.5},
            ("velocity_level", "radiation_factor"),
        ),
        Case(environment.air_attenuation, {"frequencies": 1000.0}, ("frequencies",)),
        Case(
            environment.air_power_attenuation_per_m,
            {"frequencies": 1000.0},
            ("frequencies",),
        ),
        Case(
            hearing.age_and_noise_threshold,
            {"htla": 10.0, "nipts_value": 5.0},
            ("htla", "nipts_value"),
        ),
        Case(
            materials.power_attenuation_from_alpha,
            {"attenuation_db_per_m": 0.005},
            ("attenuation_db_per_m",),
        ),
        Case(materials.absorption_area, {"t60": 2.0, "volume": 200.0}, ("t60",)),
        Case(
            materials.absorption_coefficient,
            {"t1": 4.0, "t2": 2.0, "volume": 200.0, "sample_area": 11.0},
            ("t1", "t2"),
        ),
        Case(
            signals.comb_filter_response,
            {"frequencies": 10.3, "period_s": 0.1, "n_averages": 8},
            ("frequencies",),
        ),
        Case(
            vibration.beam_bending_wave_speed,
            {"frequency": 100.0, "bending_stiffness": 1.0e4, "mass_per_length": 10.0},
            ("frequency",),
        ),
        Case(
            vibration.plate_bending_wave_speed,
            {"frequency": 100.0, "bending_stiffness": 1.0e4, "mass_per_area": 10.0},
            ("frequency",),
        ),
        Case(
            vibration.injected_power,
            {"force_n": 1.0, "mobility": 1.0e-4},
            ("force_n", "mobility"),
        ),
        # The complex form: a Python complex for numbers.
        Case(
            electroacoustics.program_signal_filter,
            {"frequencies": 1000.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            metrology.microphone_acoustic_impedance,
            {
                "electrical_admittance_s": 1.0e-6,
                "blocked_impedance_ohm": 1.0e5,
                "pressure_sensitivity_v_per_pa": 0.05,
            },
            (
                "electrical_admittance_s",
                "blocked_impedance_ohm",
                "pressure_sensitivity_v_per_pa",
            ),
            single=complex,
        ),
        Case(
            metrology.temperature_transfer_function,
            {"length_to_diameter_ratio": 0.5, "x": 10.0},
            ("x",),
            single=complex,
        ),
        Case(
            metrology.temperature_transfer_function,
            {"length_to_diameter_ratio": 0.5, "x": 10.0, "method": "approximation"},
            ("x",),
            single=complex,
            label="approximation",
        ),
        Case(
            metrology.air_gap_series_impedance_pa_s_m3,
            {"frequencies": 1000.0, "gap_length_m": 2.0e-3, "gap_radius_m": 6.35e-3},
            ("frequencies",),
            single=complex,
            increasing=True,
        ),
        Case(
            metrology.free_field_transfer_impedance,
            {
                "sensitivity_1_v_per_pa": 0.05,
                "sensitivity_2_v_per_pa": 0.05,
                "frequencies": 1000.0,
                "diaphragm_distance_m": 0.2,
                "temperature_c": 23.0,
                "static_pressure_pa": 101325.0,
                "relative_humidity_percent": 50.0,
            },
            ("frequencies",),
            single=complex,
            increasing=True,
        ),
        Case(
            windowed.response_at,
            {"frequencies": 1000.0},
            ("frequencies",),
            single=complex,
            increasing=True,
        ),
        Case(
            windowed.record_response_at,
            {"frequencies": 1000.0},
            ("frequencies",),
            single=complex,
            increasing=True,
        ),
        Case(
            microphone.acoustic_impedance_pa_s_m3,
            {"frequencies": 1000.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            microphone.complex_equivalent_volume_m3,
            {"frequencies": 1000.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            simulation.far_field_from_contour,
            {"contour": contour, "angles_deg": 30.0},
            ("angles_deg",),
            single=complex,
        ),
        Case(
            underwater.reflection_coefficient,
            {
                "grazing_angle_deg": 30.0,
                "rho1": 1025.0,
                "c1": 1500.0,
                "rho2": 1800.0,
                "c2": 1700.0,
            },
            ("grazing_angle_deg",),
            single=complex,
        ),
        Case(
            vibration.seat_to_spine_transfer,
            {"frequencies": 5.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            vibration.band_limitation_response,
            {"frequencies": 10.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            vibration.kb_weighting_response,
            {"frequencies": 10.0},
            ("frequencies",),
            single=complex,
        ),
        Case(
            vibration.convert_frf,
            {
                "value": 1.0e-4,
                "source": "receptance",
                "target": "mobility",
                "frequency": 100.0,
            },
            ("value", "frequency"),
            single=complex,
        ),
        Case(vibration.sdof_receptance, sdof, ("frequency",), single=complex),
        Case(vibration.sdof_mobility, sdof, ("frequency",), single=complex),
        Case(vibration.sdof_accelerance, sdof, ("frequency",), single=complex),
        Case(vibration.base_transmissibility, sdof, ("frequency",), single=complex),
        Case(vibration.infinite_beam_impedance, beam, ("frequency",), single=complex),
        Case(vibration.infinite_beam_mobility, beam, ("frequency",), single=complex),
        Case(
            vibration.infinite_beam_moment_mobility,
            beam,
            ("frequency",),
            single=complex,
        ),
        Case(
            vibration.blocking_force_ratio,
            {"driving_point_stiffness": 2.0e6, "termination_stiffness": 1.0e7},
            ("driving_point_stiffness", "termination_stiffness"),
            single=complex,
        ),
        Case(
            vibration.transfer_stiffness_direct,
            {"blocking_force": 10.0, "input_displacement": 1.0e-5},
            ("blocking_force", "input_displacement"),
            single=complex,
        ),
        Case(
            vibration.transfer_stiffness_indirect,
            {
                "transmissibility": 0.05,
                "blocking_mass": 50.0,
                "frequency": 100.0,
                "flange_mass": 1.0,
            },
            ("transmissibility", "frequency"),
            single=complex,
        ),
        Case(mode.fitted_frf, {"frequencies": 40.0}, ("frequencies",), single=complex),
        Case(
            mode.corrected_frf, {"frequencies": 40.0}, ("frequencies",), single=complex
        ),
        Case(
            mode.corrected_mobility,
            {"frequencies": 40.0},
            ("frequencies",),
            single=complex,
        ),
        # A validator that makes a number one-dimensional: a float all the same.
        Case(
            building.bare_floor_impact_level,
            {
                "frequencies": 500.0,
                "mass_per_area": 1.0,
                "structural_reverberation_time": 1.0,
                "radiation_factor": 1.0,
            },
            ("frequencies",),
        ),
        Case(
            building.bending_radiation_factor,
            {
                "frequencies": 500.0,
                "critical_frequency": 500.0,
                "length1": 1.0,
                "length2": 1.0,
            },
            ("frequencies",),
        ),
        Case(
            building.calculated_sound_reduction_index,
            {
                "frequencies": 500.0,
                "mass_per_area": 1.0,
                "critical_frequency": 500.0,
                "total_loss_factor": 1.0,
                "radiation_factor": 1.0,
                "forced_radiation_factor": 1.0,
            },
            ("frequencies",),
        ),
        Case(
            building.direct_impact_level,
            {"delta_l": 0.0, "delta_l_ceiling": 0.0, "floor_level": 1.0},
            ("floor_level", "delta_l", "delta_l_ceiling"),
        ),
        Case(
            building.direct_reduction_index,
            {"delta_r_source": 0.0, "delta_r_receiving": 0.0, "separating_index": 1.0},
            ("separating_index", "delta_r_source", "delta_r_receiving"),
        ),
        Case(
            building.flanking_impact_level_from_flanking_level,
            {
                "normalized_flanking_impact_level": 1.0,
                "area": 1.0,
                "laboratory_area": 1.0,
                "coupling_length": 1.0,
                "laboratory_coupling_length": 1.0,
            },
            ("normalized_flanking_impact_level",),
        ),
        Case(
            building.flanking_reduction_index_from_flanking_level,
            {
                "flanking_level_difference": 1.0,
                "separating_area": 1.0,
                "coupling_length": 1.0,
                "laboratory_coupling_length": 1.0,
            },
            ("flanking_level_difference",),
        ),
        Case(
            building.floating_floor_improvement,
            {"frequencies": 500.0, "resonance_frequency": 500.0},
            ("frequencies",),
        ),
        Case(
            building.forced_radiation_factor,
            {"frequencies": 500.0, "length1": 1.0, "length2": 1.0},
            ("frequencies",),
        ),
        Case(
            building.in_situ_equivalent_absorption_length,
            {"frequencies": 500.0, "area": 1.0, "situ_reverberation_time": 1.0},
            ("frequencies",),
        ),
        Case(
            building.in_situ_impact_level,
            {
                "impact_level": 1.0,
                "situ_reverberation_time": 1.0,
                "laboratory_reverberation_time": 1.0,
            },
            (
                "impact_level",
                "situ_reverberation_time",
                "laboratory_reverberation_time",
            ),
        ),
        Case(
            building.in_situ_reduction_index,
            {
                "sound_reduction_index": 1.0,
                "situ_reverberation_time": 1.0,
                "laboratory_reverberation_time": 1.0,
            },
            (
                "sound_reduction_index",
                "situ_reverberation_time",
                "laboratory_reverberation_time",
            ),
        ),
        Case(
            building.in_situ_total_loss_factor,
            {
                "frequencies": 500.0,
                "internal_loss_factor": 1.0,
                "mass_per_area": 1.0,
                "area": 1.0,
                "critical_frequency": 500.0,
                "radiation_factor": 1.0,
                "perimeter_absorption": 1.0,
            },
            ("frequencies",),
        ),
        Case(
            building.in_situ_velocity_level_difference,
            {
                "vibration_reduction_index": 1.0,
                "coupling_length": 1.0,
                "absorption_length_i": 1.0,
                "absorption_length_j": 1.0,
            },
            ("absorption_length_i", "absorption_length_j"),
        ),
        Case(
            building.laboratory_total_loss_factor,
            {"frequencies": 500.0, "mass_per_area": 1.0},
            ("frequencies",),
        ),
        Case(
            building.reciprocity_impact_level,
            {"sound_reduction_index": 1.0, "frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            building.resonant_sound_reduction_index,
            {
                "sound_reduction_index": 1.0,
                "frequencies": 500.0,
                "critical_frequency": 500.0,
            },
            ("frequencies",),
        ),
        Case(
            building.structural_reverberation_time,
            {"total_loss_factor": 1.0, "frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            electroacoustics.band_limit_response,
            {"frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            vibration.phase_tolerance_deg,
            {"name": "Wb", "frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            materials.apply_microphone_calibration,
            {"h12_uncorrected": 0.5, "calibration_factor": 1.1},
            ("h12_uncorrected", "calibration_factor"),
            single=complex,
        ),
        Case(
            materials.microphone_calibration_factor,
            {"h12_config1": 0.5, "h12_config2": 0.4},
            ("h12_config1", "h12_config2"),
            single=complex,
        ),
        Case(
            materials.normalized_surface_admittance,
            {"reflection": 0.5},
            ("reflection",),
            single=complex,
        ),
        Case(
            materials.normalized_surface_impedance,
            {"reflection": 0.5},
            ("reflection",),
            single=complex,
        ),
        Case(
            materials.reflection_factor,
            {"h12": 0.5, "spacing_m": 0.05, "x1": 0.1, "wavenumber": 18.3},
            ("h12", "wavenumber"),
            single=complex,
        ),
        Case(
            materials.surface_impedance,
            {"reflection": 0.5, "characteristic_impedance": 413.0},
            ("reflection",),
            single=complex,
        ),
        Case(
            materials.tube_wavenumber,
            {"frequency": 500.0, "speed_of_sound": 343.0},
            ("frequency",),
            single=complex,
        ),
        Case(
            materials.standing_wave_normalized_impedance,
            {"swr": 2.0, "first_min_distance": 0.1, "wavelength": 0.686},
            ("swr", "first_min_distance", "wavelength"),
            single=complex,
        ),
        Case(
            materials.standing_wave_reflection,
            {"swr": 2.0, "first_min_distance": 0.1, "wavelength": 0.686},
            ("swr", "first_min_distance", "wavelength"),
            single=complex,
        ),
        Case(
            materials.membrane_impedance,
            {"frequency": 500.0, "surface_density": 1.0},
            ("frequency",),
            single=complex,
        ),
        Case(
            materials.perforated_plate_impedance,
            {
                "frequency": 500.0,
                "thickness_m": 0.001,
                "hole_radius": 0.002,
                "open_area": 0.05,
            },
            ("frequency",),
            single=complex,
        ),
        Case(
            materials.microperforated_plate_impedance,
            {
                "frequency": 500.0,
                "thickness_m": 0.0005,
                "hole_radius": 0.0002,
                "open_area": 0.01,
            },
            ("frequency",),
            single=complex,
        ),
        Case(
            materials.helmholtz_resonator_impedance,
            {"frequency": 500.0, "resonator": resonator},
            ("frequency",),
            single=complex,
        ),
        Case(
            noise_control.helmholtz_impedance,
            {
                "frequencies": 500.0,
                "neck_area": 1.0e-4,
                "neck_length": 0.01,
                "cavity_volume": 1.0e-3,
            },
            ("frequencies",),
            single=complex,
        ),
        Case(
            noise_control.quarter_wave_impedance,
            {"frequencies": 500.0, "length": 0.5, "area": 1.0e-2},
            ("frequencies",),
            single=complex,
        ),
        Case(
            environment.spherical_reflection_coefficient,
            {
                "normalized_impedance": 5.0 + 3.0j,
                "source_height_m": 1.0,
                "receiver_height_m": 1.5,
                "distance": 10.0,
                "frequencies": 500.0,
            },
            ("frequencies",),
            single=complex,
        ),
        Case(
            materials.absorption_from_reflection,
            {"reflection": 0.5},
            ("reflection",),
        ),
        Case(
            materials.absorption_reference_corrected,
            {"road_reflection": 0.5, "reference_reflection": 0.9},
            ("road_reflection", "reference_reflection"),
        ),
        Case(
            materials.air_density_astm_e2611,
            {"temperature_c": 20.0, "static_pressure_kpa": 101.325},
            ("temperature_c", "static_pressure_kpa"),
        ),
        Case(
            materials.air_density_iso10534,
            {"temperature_c": 20.0, "static_pressure_kpa": 101.325},
            ("temperature_c", "static_pressure_kpa"),
        ),
        Case(
            materials.in_situ_absorption_from_reflection,
            {"reflection": 0.5},
            ("reflection",),
        ),
        Case(
            materials.normalized_diffusion_coefficient,
            {"d_theta": 0.6, "d_theta_reference": 0.3},
            ("d_theta", "d_theta_reference"),
        ),
        Case(
            materials.scattering_coefficient,
            {"alpha_spec": 0.6, "alpha_s": 0.3},
            ("alpha_spec", "alpha_s"),
        ),
        Case(
            materials.speed_of_sound_astm_e2611,
            {"temperature_c": 20.0},
            ("temperature_c",),
        ),
        Case(
            materials.speed_of_sound_iso10534,
            {"temperature_c": 20.0},
            ("temperature_c",),
        ),
        Case(
            materials.speed_of_sound_iso17497,
            {"temperature_c": 20.0},
            ("temperature_c",),
        ),
        Case(
            materials.standing_wave_absorption,
            {"swr": 2.0},
            ("swr",),
        ),
        Case(
            materials.standing_wave_ratio_from_level,
            {"level_difference": 6.0},
            ("level_difference",),
        ),
        Case(
            materials.standing_wave_reflection_magnitude,
            {"swr": 2.0},
            ("swr",),
        ),
        Case(
            materials.statistical_absorption,
            {"normalized_impedance": 2.0},
            ("normalized_impedance",),
        ),
        Case(
            materials.tube_attenuation_constant,
            {"frequency": 500.0, "speed_of_sound": 343.0, "diameter_m": 0.1},
            ("frequency",),
        ),
        Case(
            environment.kurze_anderson_attenuation,
            {"fresnel_number": 1.0},
            ("fresnel_number",),
        ),
        Case(
            plane.height,
            {"distance_m": 50.0},
            ("distance_m",),
        ),
        Case(
            profile.speed_at,
            {"height_m": 10.0},
            ("height_m",),
        ),
        # A validator that makes a number one-dimensional, the rest of the class.
        Case(
            aircraft.atmospheric_adjustment,
            {"frequencies": 1000.0, "distance_m": 120.0},
            ("frequencies",),
        ),
        Case(
            aircraft.diffraction_attenuation,
            {"frequencies": 1000.0, "path_difference": 0.5, "edge_height_m": 5.0},
            ("frequencies",),
        ),
        Case(
            aircraft.ground_effect_adjustment,
            {
                "frequencies": 1000.0,
                "source_height_m": 30.0,
                "receiver_height_m": 1.2,
                "horizontal_distance_m": 150.0,
            },
            ("frequencies",),
        ),
        Case(building.acceleration_level, {"acceleration": 0.01}, ("acceleration",)),
        Case(
            building.band_mode_count,
            {"frequencies": 500.0, "area": 10.0, "critical_frequency": 100.0},
            ("frequencies",),
        ),
        Case(
            building.direction_averaged_level_difference,
            {"dv_ij": 12.0, "dv_ji": 14.0},
            ("dv_ij", "dv_ji"),
            together=True,
        ),
        Case(
            building.equivalent_absorption_length,
            {"area": 10.0, "structural_reverberation_time": 0.2, "frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            building.fast_reverberation_correction,
            {"reverberation_time": 1.2},
            ("reverberation_time",),
        ),
        Case(
            building.modal_overlap_factor,
            {
                "area": 10.0,
                "critical_frequency": 100.0,
                "structural_reverberation_time": 0.2,
            },
            ("structural_reverberation_time",),
        ),
        Case(
            building.normalized_ceiling_attenuation,
            {"level_source": 80.0, "level_receiving": 45.0, "absorption_area": 12.0},
            ("level_source", "level_receiving", "absorption_area"),
            together=True,
        ),
        Case(
            building.partition_referenced_reduction_index,
            {"reduction_index": 40.0, "room_height_m": 2.7, "room_length": 5.0},
            ("reduction_index",),
        ),
        Case(
            building.plate_loss_factor,
            {"reverberation_time": 0.2, "frequency": 500.0},
            ("frequency",),
        ),
        Case(
            building.resilient_mount_improvement,
            {
                "frequencies": 500.0,
                "impedance": 10000.0,
                "mass_per_area": 20.0,
                "loss_factor": 0.02,
                "mount_stiffness": 100000.0,
                "mount_density": 4.0,
            },
            ("frequencies", "loss_factor"),
        ),
        Case(
            building.short_pulse_mean_square_force,
            {"frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            building.total_loss_factor,
            {"structural_reverberation_time": 0.2, "frequencies": 500.0},
            ("frequencies",),
        ),
        Case(
            building.velocity_level_difference,
            {"source_level": 90.0, "receive_level": 78.0},
            ("source_level", "receive_level"),
            together=True,
        ),
        Case(
            electroacoustics.weighting_bs468, {"frequencies": 1000.0}, ("frequencies",)
        ),
        Case(
            hearing.reat_expanded_uncertainty,
            {"frequencies": 500.0, "protector": "earplug"},
            ("frequencies",),
        ),
        Case(pulse.level_at, {"frequencies": 100.0}, ("frequencies",)),
        Case(pulse.spectrum_at, {"frequencies": 100.0}, ("frequencies",)),
        Case(
            calibration.sound_power_level_at, {"frequencies": 500.0}, ("frequencies",)
        ),
        Case(
            emission.directionality_tolerance,
            {"frequencies": 500.0, "room": "anechoic"},
            ("frequencies",),
        ),
        Case(
            emission.in_duct_reproducibility, {"frequencies": 500.0}, ("frequencies",)
        ),
        Case(
            emission.inverse_square_law_tolerance,
            {"frequencies": 500.0, "room": "anechoic"},
            ("frequencies",),
        ),
        Case(
            emission.min_analyzer_bandwidth,
            {
                "tone_frequency_hz": 12000.0,
                "microphone_speed_m_s": 0.5,
                "speed_of_sound": 343.0,
            },
            ("tone_frequency_hz",),
        ),
        Case(
            emission.plant_air_absorption_db_per_m,
            {"frequencies": 1000.0},
            ("frequencies",),
            increasing=True,
        ),
        Case(
            emission.reverberation_background_correction,
            {"levels": 70.0, "background_levels": 60.0, "frequencies": 500.0},
            ("levels", "background_levels", "frequencies"),
            together=True,
        ),
        Case(
            emission.room_absorption_coefficient,
            {"reverberation_time": 1.5, "volume": 200.0, "surface_area": 220.0},
            ("reverberation_time",),
        ),
        Case(
            emission.room_constant_from_air_absorption,
            {
                "frequencies": 10000.0,
                "volume": 200.0,
                "surface_area": 220.0,
                "temperature_c": 20.0,
                "relative_humidity_percent": 50.0,
            },
            ("frequencies",),
        ),
        Case(
            emission.room_constant_from_reverberation_time,
            {"reverberation_time": 1.5, "volume": 200.0, "surface_area": 220.0},
            ("reverberation_time",),
        ),
    )


CASES = _cases()

#: Functions of four or more arguments that broadcast, which keep the union
#: on a function without heads (EXEMPT in scripts/check_return_overloads.py)
#: and follow the rule at run time all the same: the same calls as the cases.
UNHEADED = (
    Case(
        building.flanking_impact_level,
        {
            "delta_l": 0.0,
            "delta_r_j": 0.0,
            "floor_level": 1.0,
            "index_i": 1.0,
            "index_j": 1.0,
            "velocity_level_difference": 1.0,
            "area_i": 1.0,
            "area_j": 1.0,
        },
        (
            "floor_level",
            "index_i",
            "index_j",
            "velocity_level_difference",
            "delta_l",
            "delta_r_j",
        ),
    ),
    Case(
        building.flanking_impact_level_from_normalized_difference,
        {
            "delta_l": 0.0,
            "delta_r_j": 0.0,
            "floor_level": 1.0,
            "index_i": 1.0,
            "index_j": 1.0,
            "normalized_velocity_level_difference": 1.0,
            "area_i": 1.0,
            "coupling_length": 1.0,
        },
        (
            "floor_level",
            "index_i",
            "index_j",
            "normalized_velocity_level_difference",
            "delta_l",
            "delta_r_j",
        ),
    ),
    Case(
        building.flanking_reduction_index,
        {
            "delta_r_i": 0.0,
            "delta_r_j": 0.0,
            "index_i": 1.0,
            "index_j": 1.0,
            "velocity_level_difference": 1.0,
            "separating_area": 1.0,
            "area_i": 1.0,
            "area_j": 1.0,
        },
        ("index_i", "index_j", "velocity_level_difference", "delta_r_i", "delta_r_j"),
    ),
    Case(
        building.flanking_reduction_index_from_normalized_difference,
        {
            "delta_r_i": 0.0,
            "delta_r_j": 0.0,
            "index_i": 1.0,
            "index_j": 1.0,
            "normalized_velocity_level_difference": 1.0,
            "separating_area": 1.0,
            "coupling_length": 1.0,
        },
        (
            "index_i",
            "index_j",
            "normalized_velocity_level_difference",
            "delta_r_i",
            "delta_r_j",
        ),
    ),
    Case(
        materials.absorption_coefficient_uncertainty,
        {
            "volume": 200.0,
            "area": 10.0,
            "speed_of_sound": 343.0,
            "t_a": 5.0,
            "u_a": 0.05,
            "t_b": 4.0,
            "u_b": 0.05,
        },
        ("speed_of_sound", "t_a", "u_a", "t_b", "u_b"),
    ),
    Case(
        materials.base_plate_scattering,
        {
            "volume": 200.0,
            "area": 10.0,
            "c1": 343.0,
            "t1": 5.0,
            "c3": 343.0,
            "t3": 4.9,
            "m1": 0.0,
            "m3": 0.0,
        },
        ("c1", "t1", "c3", "t3", "m1", "m3"),
    ),
    Case(
        materials.random_incidence_absorption,
        {
            "volume": 200.0,
            "area": 10.0,
            "c1": 343.0,
            "t1": 5.0,
            "c2": 343.0,
            "t2": 4.0,
            "m1": 0.0,
            "m2": 0.0,
        },
        ("c1", "t1", "c2", "t2", "m1", "m2"),
    ),
    Case(
        materials.specular_absorption_coefficient,
        {
            "volume": 200.0,
            "area": 10.0,
            "c3": 343.0,
            "t3": 4.9,
            "c4": 343.0,
            "t4": 3.9,
            "m3": 0.0,
            "m4": 0.0,
        },
        ("c3", "t3", "c4", "t4", "m3", "m4"),
    ),
    Case(
        building.vibration_reduction_index_from_flanking,
        {
            "normalized_flanking_level_difference": 60.0,
            "reduction_index_i": 50.0,
            "reduction_index_j": 48.0,
            "junction_length": 4.0,
            "area_i": 10.0,
            "area_j": 12.0,
            "absorption_length_i": 3.0,
            "absorption_length_j": 3.5,
        },
        (
            "normalized_flanking_level_difference",
            "reduction_index_i",
            "reduction_index_j",
            "absorption_length_i",
            "absorption_length_j",
        ),
        together=True,
    ),
)

#: The functions keyed on another argument than the shape of their input,
#: each held by a test of its own below.
_KEYED = frozenset(
    {
        "phonometry.room.auditorium.sound_pressure_exposure_level",
        "phonometry.vibration.immission.railway.passage_average_level",
        "phonometry.building.measurement.survey_insulation.estimate_reverberation_index",
    }
)


def _ids(case: Case) -> str:
    return (
        f"{case.name.rpartition('.')[2]} ({case.label})"
        if case.label
        else case.name.rpartition(".")[2]
    )


def _public_callables() -> Iterator[Callable[..., object]]:
    """Every public function and method of the package, once each."""
    seen: set[int] = set()
    for package in phonometry.__all__:
        module = getattr(phonometry, package)
        if not isinstance(module, types.ModuleType):
            continue
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            members: list[object] = [obj]
            if inspect.isclass(obj):
                members = [
                    member
                    for member_name, member in vars(obj).items()
                    if not member_name.startswith("_")
                ]
            for member in members:
                function = member.fget if isinstance(member, property) else member
                if inspect.isfunction(function) and id(function) not in seen:
                    seen.add(id(function))
                    yield function


@functools.cache
def _source() -> cro.Package:
    """The package as the gate reads it: every head, its aliases expanded."""
    return cro.Package(ast_scan.python_files([], cro.SOURCE), cro.SOURCE)


def _tells_a_value_from_an_array(function: Callable[..., object]) -> bool:
    """Whether the heads of *function* return a single value alone and an array alone.

    Read from the source by the gate's own reader, so a head that spells the
    array or the value through an alias (``Real``, ``Grade``) or as a numpy
    scalar is classified as the gate classifies it.
    """
    package = _source()
    read = package.functions.get(f"{function.__module__}.{function.__qualname__}")
    return read is not None and cro.tells_a_value_from_an_array(package, read)


@pytest.mark.whole_tree
def test_every_function_of_a_number_or_an_array_has_a_case() -> None:
    """A new overloaded function cannot ship without its runtime being called."""
    named = {case.name for case in CASES} | _KEYED
    found = {
        f"{function.__module__}.{function.__qualname__}"
        for function in _public_callables()
        if _tells_a_value_from_an_array(function)
    }
    assert found - named == set(), "overloaded with no case here"
    assert named - found == set(), "a case for a function the heads do not split"


@pytest.mark.parametrize("case", CASES + UNHEADED, ids=_ids)
def test_numbers_give_a_single_value(case: Case) -> None:
    """Python numbers in, a Python ``float`` (or a grade) out, not a numpy scalar."""
    result = case.call()
    assert type(result) is case.single


@pytest.mark.parametrize("case", CASES + UNHEADED, ids=_ids)
@pytest.mark.parametrize("kind", [np.float64, np.float32])
def test_numpy_numbers_give_a_single_value(case: Case, kind: type[np.floating]) -> None:
    """A numpy number is a number: it gives what a Python one gives."""
    changed = {name: kind(case.arguments[name]) for name in case.deciding}
    assert type(case.call(**changed)) is case.single


#: How far a complex value of an array may sit from the value a number gives,
#: relative to it: numpy divides complex numbers in another order in the loop
#: over an array than in the one over a single number, and the two differ in
#: the last bits. A number keeps the bits it always had.
_COMPLEX_ROUNDING = 4 * np.finfo(np.float64).eps


def _same_values(result: object, expected: list[object], single: type) -> None:
    if single is complex:
        np.testing.assert_allclose(
            np.asarray(result), expected, rtol=_COMPLEX_ROUNDING, atol=0.0
        )
    else:
        np.testing.assert_array_equal(np.asarray(result), expected)


@pytest.mark.parametrize("case", CASES + UNHEADED, ids=_ids)
def test_a_sequence_gives_an_array(case: Case) -> None:
    """Each deciding argument given as a list makes the result an array."""
    expected = case.call()
    groups = [case.deciding] if case.together else [(name,) for name in case.deciding]
    for names in groups:
        if case.increasing:
            listed = {
                name: [case.arguments[name], 2.0 * case.arguments[name]]
                for name in names
            }
            doubled = case.call(**{name: 2.0 * case.arguments[name] for name in names})
            values = [expected, doubled]
        else:
            listed = {
                name: [case.arguments[name], case.arguments[name]] for name in names
            }
            values = [expected, expected]
        result = case.call(**listed)
        assert isinstance(result, np.ndarray), names
        assert result.shape == (2,), names
        _same_values(result, values, case.single)


@pytest.mark.parametrize("case", CASES + UNHEADED, ids=_ids)
def test_a_zero_dimensional_array_gives_one(case: Case) -> None:
    """An array in, an array out, even with nothing to broadcast."""
    expected = case.call()
    for name in case.deciding:
        result = case.call(**{name: np.asarray(case.arguments[name])})
        assert isinstance(result, np.ndarray), name
        assert result.ndim == 0, name
        assert result[()] == expected, name


def test_the_unheaded_functions_are_exempt_with_their_reason() -> None:
    """A function of four or more broadcast arguments keeps its union by name.

    The heads that say which argument first holds an array would number more
    than the union says, so the check of return overloads lists each of them
    with that reason; the cases above hold their runtime to the rule.
    """
    exempt = {qualname for _path, qualname in cro.EXEMPT}
    missing = [
        case.name for case in UNHEADED if case.name.rsplit(".", 1)[-1] not in exempt
    ]
    assert not missing


def test_the_exposure_level_is_keyed_on_limits() -> None:
    """``limits=None`` reads the broadband response, one number; bands give one each."""
    rng = np.random.default_rng(1)
    ir = rng.standard_normal(4800) * np.exp(-np.arange(4800) / 600.0)
    broadband = room.sound_pressure_exposure_level(ir, 48000, limits=None)
    banded = room.sound_pressure_exposure_level(ir, 48000)
    assert type(broadband) is float
    assert isinstance(banded, np.ndarray)
    assert banded.ndim == 1


def test_the_passage_average_is_keyed_on_axis() -> None:
    """Without ``axis`` every level is averaged to one; with one, an array is left."""
    levels = np.array([[60.0, 62.0], [61.0, 63.0]])
    assert type(vibration.passage_average_level(levels)) is float
    per_band = vibration.passage_average_level(levels, axis=0)
    assert isinstance(per_band, np.ndarray)
    assert per_band.shape == (2,)
    # One dimension averaged over its axis leaves a zero-dimensional array, as
    # the head for a given axis says, not a float.
    reduced = vibration.passage_average_level([60.0, 70.0], axis=0)
    assert isinstance(reduced, np.ndarray)
    assert reduced.ndim == 0


def test_only_the_route_k2_reads_decides_its_shape() -> None:
    """``absorption_area`` wins over the pairs, and ``T`` over ``alpha``.

    The input of a route that is not read never reaches the result, so an
    array handed to it leaves the number the route read gave.
    """
    by_area = emission.environmental_correction(20.0, absorption_area=50.0)
    unread_t = emission.environmental_correction(
        20.0, absorption_area=50.0, reverberation_time=[1.0, 2.0], volume=100.0
    )
    assert type(unread_t) is float
    assert unread_t == by_area
    by_t = emission.environmental_correction(20.0, reverberation_time=1.0, volume=100.0)
    unread_alpha = emission.environmental_correction(
        20.0,
        reverberation_time=1.0,
        volume=100.0,
        mean_absorption_coefficient=[0.2, 0.3],
        room_surface=150.0,
    )
    assert type(unread_alpha) is float
    assert unread_alpha == by_t
    per_band = emission.environmental_correction(
        20.0, absorption_area=[50.0, 60.0], reverberation_time=1.0, volume=100.0
    )
    assert isinstance(per_band, np.ndarray)
    assert per_band.shape == (2,)


def test_the_reverberation_index_is_keyed_on_weighted() -> None:
    """The weighted index is one number, the unweighted one a band each."""
    assert (
        type(building.estimate_reverberation_index(30.0, "furnished", weighted=True))
        is float
    )
    bands = building.estimate_reverberation_index(30.0, "furnished")
    assert isinstance(bands, np.ndarray)


def test_the_reverberation_time_uncertainty_is_one_number() -> None:
    """The measurements are one axis, which it reduces to one ``float``."""
    times = [8.05, 7.94, 8.12, 7.88, 8.03, 7.98]
    assert type(materials.reverberation_time_uncertainty(times)) is float
    assert type(materials.reverberation_time_uncertainty(np.array(times))) is float


def test_the_mean_single_event_level_is_keyed_on_n_events() -> None:
    """Events one at a time reduce their axis; one reading of several keeps its shape."""
    one_by_one = emission.mean_single_event_level([89.0, 91.0, 90.0, 90.5, 89.5])
    assert type(one_by_one) is float
    per_band = emission.mean_single_event_level(np.full((5, 3), 97.0))
    assert isinstance(per_band, np.ndarray)
    assert per_band.shape == (3,)
    assert type(emission.mean_single_event_level(97.0, n_events=5)) is float
    zero_d = emission.mean_single_event_level(np.asarray(97.0), n_events=5)
    assert isinstance(zero_d, np.ndarray)
    assert zero_d.ndim == 0
    listed = emission.mean_single_event_level([97.0, 96.0], n_events=5)
    assert isinstance(listed, np.ndarray)
    assert listed.shape == (2,)


def test_a_guideline_without_a_frequency_is_one_number() -> None:
    """The floors and the long-term table read no frequency, and print one value."""
    top = vibration.guideline_velocity("residential", location="top_floor")
    assert type(top) is float


def test_a_validator_s_one_element_array_is_read_as_the_number_it_holds() -> None:
    """A one-element list is a sequence, and gives a one-element array back."""
    single = emission.local_environmental_correction(0.5)
    listed = emission.local_environmental_correction([0.5])
    assert type(single) is float
    assert isinstance(listed, np.ndarray)
    assert listed.shape == (1,)
    assert listed[0] == single


def test_the_piston_functions_return_a_python_float() -> None:
    """They returned ``numpy.float64`` through ``out[()]``; a number gives a ``float`` now."""
    for function in (
        electroacoustics.piston_resistance,
        electroacoustics.piston_reactance,
    ):
        assert type(function(1.0)) is float
    assert type(electroacoustics.piston_directivity(2.0, 0.3)) is float


def _stationary(f1: float | NDArray[np.float64]) -> object:
    return emission.FieldStationarityCheck(f1).stationary


def _workstation_correction(margin: float | NDArray[np.float64]) -> object:
    return emission.WorkstationBackgroundCorrection(margin).correction


@pytest.mark.parametrize(
    ("read", "number", "single"),
    [(_stationary, 0.3, bool), (_workstation_correction, 8.0, float)],
    ids=[
        "FieldStationarityCheck.stationary",
        "WorkstationBackgroundCorrection.correction",
    ],
)
def test_the_two_properties_follow_the_field_they_read(
    read: Callable[[float | NDArray[np.float64]], object], number: float, single: type
) -> None:
    """A property has no argument to overload on: the field it reads decides its form."""
    expected = read(number)
    assert type(expected) is single
    assert type(read(np.float64(number))) is single
    listed = read(np.array([number, number]))
    assert isinstance(listed, np.ndarray)
    assert listed.shape == (2,)
    zero = read(np.asarray(number))
    assert isinstance(zero, np.ndarray)
    assert zero.ndim == 0
    assert zero[()] == expected


def test_the_helper_refuses_a_result_its_like_does_not_shape() -> None:
    """An argument left out of ``like`` that does shape the result fails loudly."""
    from phonometry._internal.types import as_float_or_array

    with pytest.raises(ValueError, match="missing from 'like'"):
        as_float_or_array(np.array([1.0, 2.0]), like=(1.0,))


def test_the_modules_of_the_cases_import() -> None:
    """Each case names a function its module still defines."""
    for case in CASES + UNHEADED:
        module = importlib.import_module(inspect.unwrap(case.function).__module__)
        assert module is not None


#: The shortest run of words a return description may not say twice: five
#: words of 25 characters or more. A formula left behind beside the sentence
#: that took its place (``:math:`A_{\text{air}} = 4 m V (1 - \psi)`, m2``) is
#: a run of five words that short, and no return description of the package
#: repeats one on purpose.
_REPEATED_WORDS = 5
_REPEATED_CHARACTERS = 25


def _repeated_phrase(text: str, span: int = _REPEATED_WORDS) -> str | None:
    """A run of ``span`` words, :data:`_REPEATED_CHARACTERS` long or more, said twice."""
    words = text.split()
    first: dict[str, int] = {}
    for start in range(len(words) - span + 1):
        phrase = " ".join(words[start : start + span])
        if len(phrase) < _REPEATED_CHARACTERS:
            continue
        if phrase in first and start - first[phrase] >= span:
            return phrase
        first.setdefault(phrase, start)
    return None


def _return_blocks(source: str) -> list[tuple[int, str]]:
    """``(line, text)`` of every ``:return:`` field of every docstring in ``source``."""
    blocks: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
        ):
            continue
        doc = ast.get_docstring(node, clean=False)
        if not doc:
            continue
        lines = doc.split("\n")
        for index, line in enumerate(lines):
            if not line.strip().startswith((":return:", ":returns:")):
                continue
            indent = len(line) - len(line.lstrip())
            body = [line.strip()]
            for following in lines[index + 1 :]:
                if not following.strip():
                    break
                if len(following) - len(following.lstrip()) <= indent:
                    break
                body.append(following.strip())
            blocks.append((getattr(node, "lineno", 1), " ".join(body)))
    return blocks


@pytest.mark.whole_tree
def test_a_return_description_says_its_rule_once() -> None:
    """A ``:return:`` field states what the function returns once.

    Rewriting a return to state the array rule left the old sentence behind
    it in four places (``room.mean_absorption``,
    ``vibration.injury_probability``, and the reverberation time and the air
    absorption area of ``room.enclosed_space_absorption``), so their
    reference pages gave the formula and the rule twice in two wordings.
    """
    package = pathlib.Path(phonometry.__file__).parent
    repeated = []
    for path in sorted(package.rglob("*.py")):
        for line, text in _return_blocks(path.read_text(encoding="utf-8")):
            phrase = _repeated_phrase(text)
            if phrase is not None:
                repeated.append(f"{path.relative_to(package)}:{line}: {phrase!r}")
    assert not repeated, "\n".join(repeated)
