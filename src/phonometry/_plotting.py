#  Copyright (c) 2026. Jose M. Requena-Plens
"""Deprecated location of the plot renderers (moved to ``phonometry._plot``).

Kept as a silent re-export for one deprecation cycle (removed in 4.0):
result ``.plot()`` call sites are being retargeted per domain during the
3.2 package reorganization, and external users of this private module keep
working unchanged."""

from __future__ import annotations

from ._plot.materials import plot_absorption_uncertainty as plot_absorption_uncertainty
from ._plot.hearing import plot_age_threshold as plot_age_threshold
from ._plot.building import plot_airborne_insulation as plot_airborne_insulation
from ._plot.building import plot_airborne_prediction as plot_airborne_prediction
from ._plot.aircraft import plot_aircraft_band_attenuation as plot_aircraft_band_attenuation
from ._plot.underwater import plot_ambient_noise as plot_ambient_noise
from ._plot.building import plot_band_uncertainty as plot_band_uncertainty
from ._plot.underwater import plot_bottom_loss as plot_bottom_loss
from ._plot.vibration import plot_daily_exposure as plot_daily_exposure
from ._plot.room import plot_decay_curve as plot_decay_curve
from ._plot.materials import plot_diffusion_polar as plot_diffusion_polar
from ._plot.materials import plot_dynamic_stiffness as plot_dynamic_stiffness
from ._plot.psychoacoustics import plot_ecma_loudness as plot_ecma_loudness
from ._plot.psychoacoustics import plot_ecma_roughness as plot_ecma_roughness
from ._plot.psychoacoustics import plot_ecma_tonality as plot_ecma_tonality
from ._plot.room import plot_enclosed_space_absorption as plot_enclosed_space_absorption
from ._plot.aircraft import plot_epnl as plot_epnl
from ._plot.room import plot_excitation as plot_excitation
from ._plot.building import plot_facade_insulation as plot_facade_insulation
from ._plot.building import plot_facade_prediction as plot_facade_prediction
from ._plot.simulation import plot_fdtd_probes as plot_fdtd_probes
from ._plot.simulation import plot_fdtd_snapshot as plot_fdtd_snapshot
from ._plot.building import plot_floor_covering_improvement as plot_floor_covering_improvement
from ._plot.psychoacoustics import plot_fluctuation_strength as plot_fluctuation_strength
from ._plot.aircraft import plot_flyover as plot_flyover
from ._plot.electroacoustics import plot_frequency_response as plot_frequency_response
from ._plot.electroacoustics import plot_harmonic_distortion as plot_harmonic_distortion
from ._plot.hearing import plot_htlan as plot_htlan
from ._plot.building import plot_impact_insulation as plot_impact_insulation
from ._plot.building import plot_impact_prediction as plot_impact_prediction
from ._plot.building import plot_impact_rating as plot_impact_rating
from ._plot.materials import plot_impedance_tube as plot_impedance_tube
from ._plot.environmental import plot_impulse_prominence as plot_impulse_prominence
from ._plot.room import plot_impulse_response as plot_impulse_response
from ._plot.materials import plot_insitu_absorption as plot_insitu_absorption
from ._plot.building import plot_installed_structure_borne as plot_installed_structure_borne
from ._plot.emission import plot_intensity as plot_intensity
from ._plot.vibration import plot_mobility as plot_mobility
from ._plot.metrology import plot_monte_carlo as plot_monte_carlo
from ._plot.psychoacoustics import plot_moore_glasberg_loudness as plot_moore_glasberg_loudness
from ._plot.psychoacoustics import plot_moore_glasberg_time_loudness as plot_moore_glasberg_time_loudness
from ._plot.vibration import plot_multiple_shock as plot_multiple_shock
from ._plot.hearing import plot_nipts as plot_nipts
from ._plot.aircraft import plot_noise_contour as plot_noise_contour
from ._plot.room import plot_noise_criterion as plot_noise_criterion
from ._plot.underwater import plot_normal_modes as plot_normal_modes
from ._plot.aircraft import plot_npd_level as plot_npd_level
from ._plot.hearing import plot_occupational_exposure as plot_occupational_exposure
from ._plot.room import plot_open_plan as plot_open_plan
from ._plot.environmental import plot_outdoor_attenuation as plot_outdoor_attenuation
from ._plot.underwater import plot_parabolic_equation as plot_parabolic_equation
from ._plot.underwater import plot_pile_strike as plot_pile_strike
from ._plot.psychoacoustics import plot_psychoacoustic_annoyance as plot_psychoacoustic_annoyance
from ._plot.building import plot_radiated_power as plot_radiated_power
from ._plot.underwater import plot_ray_trace as plot_ray_trace
from ._plot.room import plot_reverberation_models as plot_reverberation_models
from ._plot.room import plot_room_acoustics as plot_room_acoustics
from ._plot.room import plot_room_criterion as plot_room_criterion
from ._plot.aircraft import plot_rotorcraft_hemisphere as plot_rotorcraft_hemisphere
from ._plot.materials import plot_scattering_coefficient as plot_scattering_coefficient
from ._plot.underwater import plot_ship_source_level as plot_ship_source_level
from ._plot.underwater import plot_ship_traffic_spectrum as plot_ship_traffic_spectrum
from ._plot.hearing import plot_sii as plot_sii
from ._plot.underwater import plot_sonar_equation as plot_sonar_equation
from ._plot.emission import plot_sound_power as plot_sound_power
from ._plot.underwater import plot_sound_speed_profile as plot_sound_speed_profile
from ._plot.materials import plot_static_airflow as plot_static_airflow
from ._plot.hearing import plot_sti as plot_sti
from ._plot.building import plot_structure_borne_power as plot_structure_borne_power
from ._plot.environmental import plot_tonal_adjustment as plot_tonal_adjustment
from ._plot.psychoacoustics import plot_tone_audibility as plot_tone_audibility
from ._plot.vibration import plot_transfer_stiffness as plot_transfer_stiffness
from ._plot.underwater import plot_transmission_loss as plot_transmission_loss
from ._plot.metrology import plot_uncertainty_budget as plot_uncertainty_budget
from ._plot.building import plot_vibration_reduction as plot_vibration_reduction
from ._plot.emission import plot_vibration_sound_power as plot_vibration_sound_power
from ._plot.vibration import plot_vibration_weighting as plot_vibration_weighting
from ._plot.materials import plot_weighted_absorption as plot_weighted_absorption
from ._plot.building import plot_weighted_rating as plot_weighted_rating
from ._plot.vibration import plot_weighted_spectrum as plot_weighted_spectrum
from ._plot.environmental import plot_wind_turbine_tonality as plot_wind_turbine_tonality
from ._plot.psychoacoustics import plot_zwicker_loudness as plot_zwicker_loudness
