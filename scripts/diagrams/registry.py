#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every diagram the documentation embeds, under the name it embeds it by.

``DIAGRAMS`` is the catalogue: it maps the base file name of a diagram to
the builder that draws it, the title printed across the top and the canvas
height it needs. It is the only place that knows the whole set, which is
what makes it the place to look when a guide shows a diagram and the
question is where it comes from; the domain modules only know how to draw.
``generate_all`` walks the catalogue and writes the four variants of each
entry into ``output_dir``.
"""

from __future__ import annotations

from pathlib import Path

from .aircraft import (
    _d_aircraft_certification,
    _d_aircraft_noise_station,
    _d_anp_records,
    _d_doc29_segment_geometry,
    _d_rotorcraft_certification,
    _d_rotorcraft_hemisphere,
)
from .buildings import (
    _d_db_hr_requirements,
    _d_decay_range,
    _d_directivity_factor,
    _d_en12354_6_takeoff,
    _d_enclosed_space_absorption,
    _d_facade_setup,
    _d_flanking,
    _d_heavy_impact_sources,
    _d_impact,
    _d_installed_paths,
    _d_insulation_lab,
    _d_insulation_setup,
    _d_intensity_insulation,
    _d_ir_measurement,
    _d_iso717_rating_chain,
    _d_iso12354_annexl,
    _d_iso12999,
    _d_iso16251_mockup,
    _d_junction_catalogue,
    _d_low_frequency_corners,
    _d_open_plan,
    _d_open_plan_setup,
    _d_panel_insulation,
    _d_reception_plate,
    _d_reception_plate_rigs,
    _d_resilient_buildups,
    _d_reverberation_prediction,
    _d_room_image_sources,
    _d_room_measurement,
    _d_room_measurement_section,
    _d_room_noise,
    _d_room_noise_setup,
    _d_room_second_microphone,
    _d_source_qualification,
    _d_survey_sweep,
    _d_sweep_budget,
    _d_workroom_path,
)
from .canvas import _write
from .devices import (
    _d_box_array,
    _d_distortion_bench,
    _d_duct_path,
    _d_enclosure_cabin_measurement,
    _d_in_duct_rig,
    _d_intensity_scan,
    _d_loudspeaker_freefield,
    _d_loudspeaker_polar,
    _d_machine_enclosure,
    _d_methods,
    _d_microphone_references,
    _d_noise_control,
    _d_noise_declaration_chain,
    _d_open_end_solid_angles,
    _d_pp_probe,
    _d_precision_anechoic,
    _d_program_loudness,
    _d_quasi_peak_test,
    _d_radiation_factor,
    _d_residual_intensity_check,
    _d_reverberation_power,
    _d_room_to_room,
    _d_screen_in_situ,
    _d_silencer_in_situ,
    _d_silencer_iso7235,
    _d_sound_power_in_situ,
    _d_surfaces,
    _d_sweep_bench,
    _d_swept_sine,
    _d_valve_noise_place,
    _d_vdi2081_sheet,
    _d_vibration_sound_power,
    _d_workstation_microphone,
)
from .environment import (
    _d_atmospheric_refraction,
    _d_barrier_four_paths,
    _d_barrier_in_situ,
    _d_cnossos_rail,
    _d_cnossos_road,
    _d_env_positions,
    _d_ground_barrier,
    _d_ground_reflection,
    _d_ground_regions,
    _d_impulse_prominence,
    _d_outdoor,
    _d_rd1367_chain,
    _d_statistical_pass_by_site,
    _d_wind_turbine,
    _d_wind_turbine_board,
)
from .fluids import _d_humid_air_chain
from .materials import (
    _d_airflow,
    _d_astm_tube,
    _d_diffusion_goniometer,
    _d_dynamic_stiffness_rig,
    _d_impedance_tube,
    _d_insitu_subtraction,
    _d_iso354_room,
    _d_iso11654,
    _d_metadiffuser_chain,
    _d_porous_layer,
    _d_scattering_reverb,
    _d_slit_absorber_chain,
    _d_spot_tube,
    _d_standing_wave_tube,
    _d_suspended_ceiling_specimen,
)
from .perception import (
    _d_dosimeter,
    _d_emission_positions,
    _d_hearing_protector_chain,
    _d_hearing_threshold,
    _d_loudness_capture,
    _d_mg_capture_routes,
    _d_nihl,
    _d_objective_intelligibility,
    _d_psychoacoustic_annoyance,
    _d_slm_workstation,
    _d_sound_quality,
    _d_soundfield_audiometry,
    _d_speech_intelligibility,
    _d_sti_chain,
    _d_sti_setup,
    _d_stoi_bench,
    _d_tone_audibility,
    _d_tone_audibility_acquisition,
    _d_zwicker,
)
from .signals import (
    _d_bank_dataflow,
    _d_block_processing,
    _d_calibration_chain,
    _d_calibration_coupling,
    _d_calibration_dataflow,
    _d_cepstrum_echoes,
    _d_correlation_delay,
    _d_data_qualification,
    _d_echo_geometry,
    _d_equal_loudness_weighting,
    _d_filter_class_check,
    _d_infrasound_chain,
    _d_levels_from_a_record,
    _d_miso_coherence,
    _d_miso_setup,
    _d_multichannel,
    _d_multichannel_capture,
    _d_multirate,
    _d_signal_chain,
    _d_slm_chain,
    _d_slm_pipeline,
    _d_spectral_analysis,
    _d_synchronous_averaging,
    _d_system_measurement,
    _d_test_signals,
    _d_time_frequency,
    _d_time_weighting,
    _d_tsa_setup,
    _d_uncertainty,
    _d_uncertainty_sources,
    _d_verification_regimes,
)
from .simulation import (
    _d_elastic_fluid_solid,
    _d_fdtd,
    _d_immersed_plate_tl,
    _d_ntff_contour,
)
from .underwater import (
    _d_hydrophone_deployment,
    _d_marine_mammal_exposure,
    _d_pile_driving_deployment,
    _d_sofar_channel,
    _d_sonar_equation,
    _d_underwater_waveguide,
)
from .vibration import (
    _d_building_frequency_predictors,
    _d_fault_kinematics,
    _d_hand_arm_vibration,
    _d_human_vibration,
    _d_iso2631_5_setup,
    _d_junction_rig,
    _d_machine_diagnostics,
    _d_machine_vibration_positions,
    _d_meter_verification_bench,
    _d_mobility_rig,
    _d_multiple_shock,
    _d_people_in_buildings,
    _d_power_injection_rig,
    _d_railway_cross_section,
    _d_railway_monitoring,
    _d_railway_prediction_chain,
    _d_seat_test_rig,
    _d_structural_damage_points,
    _d_transfer_stiffness_rig,
    _d_vibration_meter_coupling,
    _d_vibration_prediction_path,
)

DIAGRAMS = {
    "diagram_calibration_setup": (
        _d_calibration_chain,
        "Calibration chain: from calibrator to physical units",
        560,
    ),
    "diagram_calibration_coupling": (
        _d_calibration_coupling,
        "Coupling the calibrator (IEC 60942:2017)",
        580,
    ),
    "diagram_env_measurement": (
        _d_env_positions,
        "Environmental noise measurement positions (ISO 1996-2)",
        560,
    ),
    "diagram_tonality_positions": (
        _d_emission_positions,
        "Emission measurement positions (ECMA-74)",
        560,
    ),
    "diagram_signal_chain": (_d_signal_chain, "phonometry processing chain", 400),
    "diagram_multirate": (
        _d_multirate,
        "Multirate decimation in the octave filter bank",
        560,
    ),
    "diagram_pp_probe": (_d_pp_probe, "Two-microphone (p-p) intensity probe", 460),
    "diagram_sti_chain": (_d_sti_chain, "STI measurement chain (IEC 60268-16)", 400),
    "diagram_insulation_setup": (
        _d_insulation_setup,
        "Airborne sound insulation setup (ISO 16283-1)",
        600,
    ),
    "diagram_ir_measurement": (
        _d_ir_measurement,
        "Impulse-response measurement chain (ISO 18233)",
        440,
    ),
    "diagram_sound_power_surfaces": (
        _d_surfaces,
        "ISO 3744 / 3746 sound power measurement surfaces",
        640,
    ),
    "diagram_impact_setup": (
        _d_impact,
        "ISO 16283-2 impact sound insulation setup",
        600,
    ),
    "diagram_facade_setup": (
        _d_facade_setup,
        "Facade sound insulation setup (ISO 16283-3)",
        700,
    ),
    "diagram_iso717_rating_chain": (
        _d_iso717_rating_chain,
        "How a band spectrum becomes one number (ISO 717-1, ISO 717-2)",
        816,
    ),
    "diagram_heavy_impact_sources": (
        _d_heavy_impact_sources,
        "Standard heavy and soft impact sources (ISO 16283-2, JIS A 1418-2)",
        680,
    ),
    "diagram_survey_sweep": (
        _d_survey_sweep,
        "The ISO 10052 survey sweep (Clauses 6.2 and 6.3)",
        560,
    ),
    "diagram_low_frequency_corners": (
        _d_low_frequency_corners,
        "How a room under 25 m³ is measured at 50, 63 and 80 Hz (ISO 16283)",
        870,
    ),
    "diagram_db_hr_requirements": (
        _d_db_hr_requirements,
        "Where each DB-HR requirement applies (CTE DB-HR)",
        860,
    ),
    "sound_power_methods": (_d_methods, "Sound power methods compared", 944),
    "diagram_noise_declaration_chain": (
        _d_noise_declaration_chain,
        "Declaring and verifying a sound power level (ISO 4871)",
        736,
    ),
    "diagram_flanking_paths": (
        _d_flanking,
        "Direct and flanking transmission paths (EN 12354)",
        640,
    ),
    "diagram_outdoor_geometry": (
        _d_outdoor,
        "ISO 9613-2 source–barrier–receiver geometry",
        560,
    ),
    "diagram_impedance_tube": (
        _d_impedance_tube,
        "Impedance tube: two-microphone method (ISO 10534-2)",
        520,
    ),
    "diagram_astm_tube": (
        _d_astm_tube,
        "Four-microphone transmission-loss tube (ASTM E2611)",
        560,
    ),
    "diagram_airflow_resistance": (
        _d_airflow,
        "Airflow resistance: static and alternating methods (ISO 9053-1/-2)",
        660,
    ),
    "diagram_iso354_room": (
        _d_iso354_room,
        "Reverberation-room sound absorption (ISO 354)",
        730,
    ),
    "diagram_suspended_ceiling_specimen": (
        _d_suspended_ceiling_specimen,
        "How a suspended ceiling is mounted for the test (EN 16487)",
        860,
    ),
    "diagram_standing_wave_tube": (
        _d_standing_wave_tube,
        "Standing-wave-ratio tube: probe traverse and the minima (ISO 10534-1)",
        680,
    ),
    "diagram_scattering_reverb": (
        _d_scattering_reverb,
        "Random-incidence scattering in a reverberation room (ISO 17497-1)",
        560,
    ),
    "diagram_diffusion_goniometer": (
        _d_diffusion_goniometer,
        "Free-field diffusion goniometer (ISO 17497-2)",
        580,
    ),
    "diagram_metadiffuser_chain": (
        _d_metadiffuser_chain,
        "How a metadiffuser is predicted, from wells to diffusion",
        924,
    ),
    "diagram_insitu_subtraction": (
        _d_insitu_subtraction,
        "In-situ road absorption: subtraction technique (ISO 13472-1)",
        560,
    ),
    "diagram_spot_tube": (
        _d_spot_tube,
        "In-situ road absorption: spot method (ISO 13472-2)",
        540,
    ),
    "diagram_precision_anechoic": (
        _d_precision_anechoic,
        "Precision sound power in an anechoic room (ISO 3745)",
        600,
    ),
    "diagram_intensity_scan": (
        _d_intensity_scan,
        "Precision sound intensity scanning (ISO 9614-3)",
        600,
    ),
    "diagram_reverberation_power": (
        _d_reverberation_power,
        "ISO 3741 reverberation test room",
        600,
    ),
    "diagram_sound_power_in_situ": (
        _d_sound_power_in_situ,
        "How sound power is measured in situ (ISO 3747)",
        744,
    ),
    "diagram_box_array": (
        _d_box_array,
        "ISO 3744 parallelepiped measurement surface",
        580,
    ),
    "diagram_radiation_factor": (
        _d_radiation_factor,
        "Determining the radiation factor (ISO/TS 7849-2)",
        540,
    ),
    "diagram_residual_intensity_check": (
        _d_residual_intensity_check,
        "Residual-intensity test and the before-use probe check",
        570,
    ),
    "diagram_human_vibration": (
        _d_human_vibration,
        "Whole-body vibration measurement chain (ISO 2631-1 / ISO 8041-1)",
        580,
    ),
    "diagram_hand_arm_vibration": (
        _d_hand_arm_vibration,
        "Hand-transmitted vibration: where the accelerometer goes",
        660,
    ),
    "diagram_meter_verification_bench": (
        _d_meter_verification_bench,
        "Pattern evaluation of a human-vibration meter (ISO 8041-1)",
        1054,
    ),
    "diagram_speech_intelligibility": (
        _d_speech_intelligibility,
        "Speech Intelligibility Index computation flow (ANSI S3.5-1997)",
        600,
    ),
    "diagram_room_second_microphone": (
        _d_room_second_microphone,
        "What ISO 3382-1 asks for beyond one omnidirectional microphone",
        574,
    ),
    "diagram_room_measurement": (
        _d_room_measurement,
        "Room-acoustics measurement setup (ISO 3382-1 / ISO 3382-2)",
        620,
    ),
    "diagram_room_measurement_section": (
        _d_room_measurement_section,
        "The measuring chain in section (ISO 3382-1 clauses 4.2 and 4.3)",
        600,
    ),
    "diagram_source_qualification": (
        _d_source_qualification,
        "How the source qualifies, and where it stands in the hall (ISO 3382-1)",
        716,
    ),
    "diagram_room_noise": (
        _d_room_noise,
        "Room-noise rating methods (ANSI/ASA S12.2-2019): NC and RC Mark II",
        580,
    ),
    "diagram_room_noise_setup": (
        _d_room_noise_setup,
        "Measuring the rated spectrum (ANSI/ASA S12.2-2019, clause 5.2.5)",
        600,
    ),
    "diagram_sweep_budget": (
        _d_sweep_budget,
        "Dimensioning the excitation for a room with T = 1.2 s (ISO 18233)",
        560,
    ),
    "diagram_hearing_threshold": (
        _d_hearing_threshold,
        "Hearing-threshold model (ISO 7029 age distribution, ISO 389-7 zero)",
        600,
    ),
    "diagram_soundfield_audiometry": (
        _d_soundfield_audiometry,
        "Sound-field audiometry and the ISO 389-7 reference zero",
        580,
    ),
    "diagram_slm_workstation_iso9612": (
        _d_slm_workstation,
        "Sound level meter at a workstation (ISO 9612, Clause 12.4)",
        580,
    ),
    "diagram_sti_setup": (
        _d_sti_setup,
        "Setting up an STI measurement (IEC 60268-16, clause 7)",
        580,
    ),
    "diagram_stoi_bench": (
        _d_stoi_bench,
        "Capturing a STOI pair through a real device",
        545,
    ),
    "diagram_uncertainty": (
        _d_uncertainty,
        "Uncertainty: GUM propagation vs Monte Carlo (Guide 98-3)",
        540,
    ),
    "diagram_uncertainty_sources": (
        _d_uncertainty_sources,
        "Where an acoustic budget's terms come from",
        580,
    ),
    "diagram_multichannel_capture": (
        _d_multichannel_capture,
        "Capturing an array: one clock, locked gains, a written row map",
        580,
    ),
    "diagram_infrasound_chain": (
        _d_infrasound_chain,
        "Measuring infrasound: the chain that must deliver 0,25 Hz",
        580,
    ),
    "diagram_nihl": (
        _d_nihl,
        "Noise-induced hearing loss (ISO 1999): NIPTS and HTLAN",
        470,
    ),
    "diagram_hearing_protector_chain": (
        _d_hearing_protector_chain,
        "From sixteen subjects to the effective A-weighted level (ISO 4869-2)",
        910,
    ),
    "diagram_ntacou112": (
        _d_impulse_prominence,
        "Impulsive-sound prominence and LAeq adjustment (NT ACOU 112)",
        520,
    ),
    "diagram_iso2631_5": (
        _d_multiple_shock,
        "Multiple-shock spinal-response dose and injury risk (ISO 2631-5)",
        580,
    ),
    "diagram_iso2631_5_setup": (
        _d_iso2631_5_setup,
        "Getting the record (ISO 2631-5, clauses 5.1.2 and 5.1.4)",
        600,
    ),
    "diagram_seat_test_rig": (
        _d_seat_test_rig,
        "How a seat is tested on a vibration simulator (ISO 10326-1)",
        790,
    ),
    "diagram_en12354_6": (
        _d_enclosed_space_absorption,
        "Absorption area and reverberation time of a room (EN 12354-6)",
        410,
    ),
    "diagram_en12354_6_takeoff": (
        _d_en12354_6_takeoff,
        "Room take-off: one room, three input lists (EN 12354-6)",
        580,
    ),
    "diagram_decay_range": (
        _d_decay_range,
        "The decay-range budget of one band (ISO 3382)",
        520,
    ),
    "diagram_directivity_factor": (
        _d_directivity_factor,
        "Directivity factor Q: four mountings, four critical distances",
        410,
    ),
    "diagram_time_weighting": (
        _d_time_weighting,
        "Exponential-detector chain of the time weightings (IEC 61672-1)",
        460,
    ),
    "diagram_levels_from_a_record": (
        _d_levels_from_a_record,
        "Every level one calibrated record yields (IEC 61672-1, IEC 61252)",
        760,
    ),
    "diagram_block_processing": (
        _d_block_processing,
        "Block processing: carrying the filter state versus resetting it",
        510,
    ),
    "diagram_multichannel": (
        _d_multichannel,
        "Array-shape flow through a per-channel operation",
        410,
    ),
    "diagram_open_plan": (
        _d_open_plan,
        "Open-plan office spatial decay of speech (ISO 3382-3)",
        500,
    ),
    "diagram_workroom_path": (
        _d_workroom_path,
        "How a workroom is measured, path and points (ISO 14257)",
        710,
    ),
    "diagram_open_plan_setup": (
        _d_open_plan_setup,
        "Where the ISO 3382-3 measurement line goes (clauses 5.1 and 5.2)",
        780,
    ),
    "diagram_iso12999": (
        _d_iso12999,
        "Measurement uncertainty from tables to expanded U (ISO 12999-1)",
        500,
    ),
    "diagram_iso11654": (
        _d_iso11654,
        "Single-number sound-absorption rating (ISO 11654)",
        520,
    ),
    "diagram_zwicker": (_d_zwicker, "Zwicker loudness model chain (ISO 532-1)", 490),
    "diagram_loudness_capture": (
        _d_loudness_capture,
        "Where the microphone goes for a loudness measurement (ISO 532-1)",
        650,
    ),
    "diagram_equal_loudness_weighting": (
        _d_equal_loudness_weighting,
        "Why A-weighting: an equal-loudness contour, inverted (ISO 226)",
        560,
    ),
    "diagram_loudspeaker_freefield": (
        _d_loudspeaker_freefield,
        "Loudspeaker free-field sensitivity measurement (IEC 60268-5)",
        600,
    ),
    "diagram_loudspeaker_polar": (
        _d_loudspeaker_polar,
        "Polar directional response measurement (IEC 60268-5 clause 23)",
        600,
    ),
    "diagram_microphone_references": (
        _d_microphone_references,
        ("The three fields a microphone sensitivity is defined in (IEC 60268-4)"),
        590,
    ),
    "diagram_distortion_bench": (
        _d_distortion_bench,
        "The IEC 60268-3 distortion bench and its operating point",
        590,
    ),
    "diagram_dosimeter_iso9612": (
        _d_dosimeter,
        "Occupational noise exposure measurement (ISO 9612)",
        640,
    ),
    "diagram_dynamic_stiffness_rig": (
        _d_dynamic_stiffness_rig,
        "Dynamic-stiffness resonance rig (EN 29052-1)",
        880,
    ),
    "diagram_mobility_rig": (
        _d_mobility_rig,
        "Mechanical-mobility measurement on a beam (ISO 7626)",
        860,
    ),
    "diagram_transfer_stiffness_rig": (
        _d_transfer_stiffness_rig,
        "Dynamic transfer stiffness: direct and indirect methods (ISO 10846)",
        1110,
    ),
    "diagram_reception_plate": (
        _d_reception_plate,
        "Reception-plate measurement of structure-borne power (EN 15657)",
        560,
    ),
    "diagram_reception_plate_rigs": (
        _d_reception_plate_rigs,
        "EN 15657 low- and high-mobility reception plates",
        600,
    ),
    "diagram_iso16251_mockup": (
        _d_iso16251_mockup,
        "ISO 16251-1 small floor mock-up for floor-covering improvement",
        600,
    ),
    "diagram_iso12354_annexl": (
        _d_iso12354_annexl,
        "ISO 12354-1 Annex L worked building: elements, junctions, paths",
        616,
    ),
    "diagram_resilient_buildups": (
        _d_resilient_buildups,
        "Resilient layers in section: floating floor, mounts, wall lining",
        500,
    ),
    "diagram_junction_catalogue": (
        _d_junction_catalogue,
        "EN 12354-1 Annex E junction types, path branches and the mass ratio",
        686,
    ),
    "diagram_installed_paths": (
        _d_installed_paths,
        "Installed structure-borne sound paths (EN 12354-5)",
        620,
    ),
    "diagram_wind_turbine_iec61400": (
        _d_wind_turbine,
        "Wind-turbine noise measurement geometry (IEC 61400-11)",
        640,
    ),
    "diagram_ground_reflection": (
        _d_ground_reflection,
        "Ground reflection: direct ray, image source and path difference",
        560,
    ),
    "diagram_fdtd": (
        _d_fdtd,
        "2D acoustic FDTD wave simulation (staggered leapfrog)",
        500,
    ),
    "diagram_ntff_contour": (
        _d_ntff_contour,
        "Near-to-far-field capture: contour, clearances and angle convention",
        800,
    ),
    "diagram_elastic_fluid_solid": (
        _d_elastic_fluid_solid,
        "A fluid-solid contact at three incidences, and where it sits on the grid",
        720,
    ),
    "diagram_immersed_plate_tl": (
        _d_immersed_plate_tl,
        "Immersed-plate transmission: the strip, the probes and the time gate",
        660,
    ),
    "diagram_slm_chain": (
        _d_slm_chain,
        "Sound level meter measurement chain (IEC 61672-1)",
        560,
    ),
    "diagram_insulation_lab": (
        _d_insulation_lab,
        "Laboratory sound insulation suite (ISO 10140)",
        600,
    ),
    "diagram_intensity_insulation": (
        _d_intensity_insulation,
        "How sound insulation is measured by intensity (ISO 15186)",
        904,
    ),
    "diagram_junction_rig": (
        _d_junction_rig,
        "Junction vibration measurement on L- and T-junctions (ISO 10848)",
        620,
    ),
    "diagram_power_injection_rig": (
        _d_power_injection_rig,
        "Power injection: coupling loss factors from measured energies",
        670,
    ),
    "diagram_fault_kinematics": (
        _d_fault_kinematics,
        "Where the fault frequencies come from: bearing, gear pair, ducted fan",
        790,
    ),
    "diagram_machine_diagnostics": (
        _d_machine_diagnostics,
        "Condition monitoring on a motor-gearbox train (Norton Section 8.4)",
        600,
    ),
    "diagram_machine_vibration_positions": (
        _d_machine_vibration_positions,
        "Where machine vibration is measured (ISO 20816-1)",
        700,
    ),
    "diagram_building_frequency_predictors": (
        _d_building_frequency_predictors,
        "What a building's own frequency is predicted from (ISO 4866 Annex D)",
        790,
    ),
    "diagram_vibration_prediction_path": (
        _d_vibration_prediction_path,
        "The path a vibration prediction follows (DIN 4150-1)",
        880,
    ),
    "diagram_railway_prediction_chain": (
        _d_railway_prediction_chain,
        "A railway prediction, track to floor (E DIN 45672-3)",
        758,
    ),
    "diagram_structural_damage_points": (
        _d_structural_damage_points,
        "Where a building is measured for vibration damage (DIN 4150-3)",
        850,
    ),
    "diagram_railway_monitoring": (
        _d_railway_monitoring,
        "How railway vibration is measured in a building (E DIN 4150-2)",
        890,
    ),
    "diagram_people_in_buildings": (
        _d_people_in_buildings,
        "How vibration in a dwelling is measured and judged (DIN 4150-2)",
        880,
    ),
    "diagram_vibration_meter_coupling": (
        _d_vibration_meter_coupling,
        "Where DIN 45669-2 puts the transducer, and how it is coupled",
        836,
    ),
    "diagram_railway_cross_section": (
        _d_railway_cross_section,
        "Where vibration next to a railway is measured (DIN 45672-1, DIN 45672-2)",
        960,
    ),
    "diagram_vibration_sound_power": (
        _d_vibration_sound_power,
        "Sound power from surface vibration (ISO/TS 7849)",
        580,
    ),
    "diagram_hydrophone_deployment": (
        _d_hydrophone_deployment,
        "Ship radiated-noise measurement geometry (ISO 17208-1)",
        640,
    ),
    "diagram_sofar_channel": (
        _d_sofar_channel,
        "The SOFAR channel: a deep-ocean sound waveguide",
        620,
    ),
    "diagram_pile_driving": (
        _d_pile_driving_deployment,
        "Percussive pile-driving survey geometry (ISO 18406)",
        670,
    ),
    "diagram_sonar_equation": (
        _d_sonar_equation,
        "Sonar equation geometry: passive and active (ISO 18405)",
        660,
    ),
    "diagram_underwater_waveguide": (
        _d_underwater_waveguide,
        "The range-independent waveguide the four solvers share",
        606,
    ),
    "diagram_marine_mammal_exposure": (
        _d_marine_mammal_exposure,
        "Marine-mammal exposure: measured here, assessed there",
        620,
    ),
    "diagram_atmospheric_refraction": (
        _d_atmospheric_refraction,
        "Atmospheric refraction: downwind multipath and the upwind shadow",
        620,
    ),
    "diagram_aircraft_certification": (
        _d_aircraft_certification,
        "Aircraft noise certification points (ICAO Annex 16, Chapter 3)",
        640,
    ),
    "diagram_rotorcraft_certification": (
        _d_rotorcraft_certification,
        "Helicopter overflight noise certification (ICAO Annex 16, Chapter 8)",
        620,
    ),
    "diagram_aircraft_noise_station": (
        _d_aircraft_noise_station,
        "A noise certification measurement station (ICAO Annex 16, App. 2)",
        750,
    ),
    "diagram_doc29_segment": (
        _d_doc29_segment_geometry,
        "Flight-path segment geometry (ECAC Doc 29, Chapter 4)",
        710,
    ),
    "diagram_anp_records": (
        _d_anp_records,
        "From an ANP aircraft record to an event level (ECAC Doc 29)",
        866,
    ),
    "diagram_rotorcraft_hemisphere": (
        _d_rotorcraft_hemisphere,
        "The rotorcraft noise hemisphere and its angles (ECAC Doc 32)",
        686,
    ),
    "diagram_swept_sine": (
        _d_swept_sine,
        "Swept-sine distortion: deconvolution and harmonic pre-arrivals",
        620,
    ),
    "diagram_sweep_bench": (
        _d_sweep_bench,
        "Playing and recording a sweep: the two benches and the time budget",
        620,
    ),
    "diagram_system_measurement": (
        _d_system_measurement,
        "Two-channel FRF measurement: the H1 estimator and coherence",
        560,
    ),
    "diagram_test_signals": (
        _d_test_signals,
        "The test-signal family at a glance",
        640,
    ),
    "diagram_spectral_analysis": (
        _d_spectral_analysis,
        "The Welch PSD pipeline: segment, taper, average (Bendat & Piersol)",
        600,
    ),
    "diagram_miso_coherence": (
        _d_miso_coherence,
        "MISO coherence: from correlated sources to per-source contributions",
        540,
    ),
    "diagram_miso_setup": (
        _d_miso_setup,
        "Instrumenting a MISO measurement: one reference per source",
        580,
    ),
    "diagram_time_frequency": (
        _d_time_frequency,
        "The time-frequency trade-off: two tilings of the same record",
        560,
    ),
    "diagram_cepstrum_echoes": (
        _d_cepstrum_echoes,
        "The cepstrum chain: an echo becomes a quefrency spike",
        560,
    ),
    "diagram_echo_geometry": (
        _d_echo_geometry,
        "Where the quefrency comes from: the geometry of one reflection",
        600,
    ),
    "diagram_synchronous_averaging": (
        _d_synchronous_averaging,
        "Time synchronous averaging: trigger, slice, average",
        580,
    ),
    "diagram_tsa_setup": (
        _d_tsa_setup,
        "Instrumenting a synchronous average: tacho and accelerometer",
        600,
    ),
    "diagram_correlation_delay": (
        _d_correlation_delay,
        "Time-delay estimation: two microphones and one correlation peak",
        640,
    ),
    "diagram_data_qualification": (
        _d_data_qualification,
        ("Data qualification: the stationarity decision (Bendat & Piersol 10.3)"),
        620,
    ),
    "diagram_sound_quality": (
        _d_sound_quality,
        "Sound quality beyond loudness: four calibrated sensations",
        500,
    ),
    "diagram_mg_capture_routes": (
        _d_mg_capture_routes,
        "Which recording maps to which arguments (ISO 532-2 clause 7.2)",
        690,
    ),
    "diagram_tone_audibility_acquisition": (
        _d_tone_audibility_acquisition,
        "The spectra an ISO/PAS 20065 assessment is built on",
        620,
    ),
    "diagram_tone_audibility": (
        _d_tone_audibility,
        "Tone audibility: from spectrum to penalty (ISO/PAS 20065)",
        580,
    ),
    "diagram_psychoacoustic_annoyance": (
        _d_psychoacoustic_annoyance,
        "Psychoacoustic annoyance: four sensations, one scalar",
        520,
    ),
    "diagram_objective_intelligibility": (
        _d_objective_intelligibility,
        "STOI and ESTOI: correlating clean against degraded speech",
        600,
    ),
    "diagram_program_loudness": (
        _d_program_loudness,
        "Programme loudness: the BS.1770 / R 128 metering chain",
        670,
    ),
    "diagram_quasi_peak_test": (
        _d_quasi_peak_test,
        "How a quasi-peak meter is tested (ITU-R BS.468-4)",
        900,
    ),
    "diagram_reverberation_prediction": (
        _d_reverberation_prediction,
        "Predicting the reverberation time: Sabine against Eyring",
        600,
    ),
    "diagram_panel_insulation": (
        _d_panel_insulation,
        "Panel between rooms: mass law and the coincidence dip",
        540,
    ),
    "diagram_porous_layer": (
        _d_porous_layer,
        "Porous absorber on a rigid wall: microstructure to absorption",
        590,
    ),
    "diagram_slit_absorber_chain": (
        _d_slit_absorber_chain,
        "The slit panel as a chain of transfer matrices",
        900,
    ),
    "diagram_ground_barrier": (
        _d_ground_barrier,
        "Barrier diffraction over ground: the Fresnel number at work",
        510,
    ),
    "diagram_ground_regions": (
        _d_ground_regions,
        "ISO 9613-2 ground regions and the ground factor G",
        640,
    ),
    "diagram_barrier_four_paths": (
        _d_barrier_four_paths,
        "The four diffracted paths of a barrier on finite-impedance ground",
        596,
    ),
    "diagram_cnossos_road": (
        _d_cnossos_road,
        "CNOSSOS-EU road source line geometry",
        580,
    ),
    "diagram_cnossos_rail": (
        _d_cnossos_rail,
        "CNOSSOS-EU railway source lines and directivity angles",
        700,
    ),
    "diagram_statistical_pass_by_site": (
        _d_statistical_pass_by_site,
        "ISO 11819-1 pass-by site: the microphone and the test section",
        596,
    ),
    "diagram_wind_turbine_board": (
        _d_wind_turbine_board,
        "IEC 61400-11 ground-board microphone mounting",
        600,
    ),
    "diagram_rd1367_chain": (
        _d_rd1367_chain,
        "RD 1367/2007: from a noise phase to the three acceptance criteria",
        580,
    ),
    "diagram_room_image_sources": (
        _d_room_image_sources,
        "Image-source lattice in plan: first reflections of a 7 × 5 m room",
        665,
    ),
    "diagram_noise_control": (
        _d_noise_control,
        "Noise control at the source, along the path and at the receiver",
        625,
    ),
    "diagram_machine_enclosure": (
        _d_machine_enclosure,
        "Machine enclosure in section: what IL = R − C really depends on",
        660,
    ),
    "diagram_room_to_room": (
        _d_room_to_room,
        "Plant room to operator room: every symbol of the balance, in section",
        586,
    ),
    "diagram_enclosure_cabin_measurement": (
        _d_enclosure_cabin_measurement,
        "How an enclosure and a cabin are measured (ISO 11546, ISO 11957)",
        560,
    ),
    "diagram_silencer_iso7235": (
        _d_silencer_iso7235,
        "How a silencer is measured: the ISO 7235 substitution method",
        710,
    ),
    "diagram_silencer_in_situ": (
        _d_silencer_in_situ,
        "How a silencer is measured where it stands (ISO 11820)",
        610,
    ),
    "diagram_screen_in_situ": (
        _d_screen_in_situ,
        "How a removable screen is measured where it stands (ISO 11821)",
        656,
    ),
    "diagram_barrier_in_situ": (
        _d_barrier_in_situ,
        "How an outdoor barrier is measured once it is built (ISO 10847)",
        750,
    ),
    "diagram_open_end_solid_angles": (
        _d_open_end_solid_angles,
        "How a duct end is mounted, and what it keeps in (ISO 7235 Table B.1)",
        470,
    ),
    "diagram_duct_path": (
        _d_duct_path,
        "Long's Table 14.9 installation: every row of the sheet as a place",
        566,
    ),
    "diagram_workstation_microphone": (
        _d_workstation_microphone,
        "Where the microphone goes at a work station (ISO 11201 Clause 9)",
        600,
    ),
    "diagram_in_duct_rig": (
        _d_in_duct_rig,
        "How a fan is measured in its duct (ISO 5136)",
        800,
    ),
    "diagram_valve_noise_place": (
        _d_valve_noise_place,
        "Where control valve noise is made, and where it is quoted",
        502,
    ),
    "diagram_vdi2081_sheet": (
        _d_vdi2081_sheet,
        "The VDI 2081 worked sheet as a place, and where each number comes from",
        596,
    ),
    "diagram_slm_pipeline": (
        _d_slm_pipeline,
        "The sound level meter pipeline: one function per stage",
        672,
    ),
    "diagram_calibration_dataflow": (
        _d_calibration_dataflow,
        "Calibration data flow: one factor, every level function",
        616,
    ),
    "diagram_bank_dataflow": (
        _d_bank_dataflow,
        "Inside a band: the decimation decision and the biquad cascade",
        680,
    ),
    "diagram_filter_class_check": (
        _d_filter_class_check,
        "How a band is graded against Table 1 (IEC 61260-1)",
        796,
    ),
    "diagram_verification_regimes": (
        _d_verification_regimes,
        "Specification, pattern evaluation, periodic test (IEC 61672, IEC 61260)",
        974,
    ),
    "diagram_humid_air_chain": (
        _d_humid_air_chain,
        "Humid air from four inputs, step by step (IEC 61094-2 Annex F)",
        938,
    ),
}


def generate_all(output_dir: str = ".github/images") -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for name, (builder, title, height) in DIAGRAMS.items():
        _write(output_dir, name, builder, title, height)
