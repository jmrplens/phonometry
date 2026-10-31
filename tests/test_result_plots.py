#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The contract every one-line ``.plot()`` method on a result object has to keep.

Four promises, none of them about any single standard, which is why they are
tested together and away from the domains:

* matplotlib is a *soft* dependency. Importing phonometry and computing must
  work without it, so ``phonometry._plot.common`` may not import matplotlib at
  module scope; the AST check below allows only imports inside a function body
  or under ``if TYPE_CHECKING:``.
* When it really is missing, ``.plot()`` fails with the install command, not
  with a bare ``ModuleNotFoundError``.
* Styling kwargs reach the primary artist. Every renderer draws a fixed default
  colour and width, and a user-supplied ``linewidth=`` or ``color=`` must
  override it rather than collide with it: ``color`` in particular used to raise
  ``TypeError: got multiple values for keyword``. The table below walks every
  public renderer, line-drawn and bar-drawn alike.
* ``ax=None`` creates a figure and passing ``ax=`` composes into it, returning
  the same axes object, so a result can be drawn into a caller's subplot.

The result objects are built by ``tests/result_factories.py``; what each figure
*says* about its own standard is asserted in that domain's own test file. These
tests run on the non-interactive Agg backend.
"""

from __future__ import annotations

import ast
import builtins
import functools
import inspect
import itertools
import pathlib
import sys
import typing
from typing import TYPE_CHECKING, Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from result_factories import (
    FS,
    _acoustic_centre,
    _adjacent_neutrality,
    _adjustment_value,
    _agc_characteristic,
    _airborne_insulation,
    _airborne_prediction,
    _airborne_rating,
    _am_bins,
    _am_block,
    _am_period,
    _amplifier_frequency_response,
    _amplifier_overload,
    _assessment_velocity,
    _background_duration,
    _background_noise,
    _band_averaged_stiffness,
    _band_uncertainty,
    _binaural_indicators,
    _binned_levels,
    _calculation_verification,
    _calibration_deviation,
    _capillary_tube_impedance,
    _channel_match,
    _cnossos_road,
    _coherence_check,
    _coherent_output_spectrum,
    _comparison_budget,
    _comparison_calibration,
    _comparison_phase,
    _conformance_verification,
    _correction_budget,
    _correction_verification,
    _coupler_check,
    _coupler_frequency_response,
    _coupler_parameter_uncertainty,
    _coupler_transfer_impedance,
    _cross_spectral_density,
    _crosstalk_attenuation,
    _diffuse_absorption,
    _diffuse_field,
    _diffuser_polar_response,
    _diffusion,
    _direct_sound_subtraction,
    _directivity_factor,
    _double_hit,
    _double_wall,
    _driving_point_stiffness,
    _ear_canal_frequency_response,
    _ear_canal_microphone,
    _ecma_fluctuation_strength,
    _ecma_loudness,
    _ecma_roughness,
    _ecma_tonality,
    _effective_blocking_mass,
    _emergence,
    _envelope,
    _envelope_spectrum,
    _environmental_sensitivity_correction,
    _eq_response,
    _exp_ir,
    _exposure,
    _extended_impact_rating,
    _extended_rating,
    _field_comparison_response,
    _field_indicators,
    _field_strength_reading,
    _filter_periodic,
    _force_spectrum,
    _free_field_arrangement,
    _free_field_check,
    _free_field_correction,
    _free_field_parameter_uncertainty,
    _free_field_region,
    _frequency_response,
    _gap_width_check,
    _hard_walled_power,
    _hard_walled_room_check,
    _heat_conduction_correction,
    _heavy_impact_improvement,
    _high_frequency_power,
    _impact_insulation,
    _impact_mobility,
    _impact_prediction,
    _impact_rating,
    _impedance_pressure_ratio,
    _impedance_tube,
    _impulse_response,
    _in_situ_power,
    _induction_loop_verification,
    _instrument_agreement,
    _intensity,
    _intensity_power_negative,
    _inverse_square_law,
    _jig_diameter_correction,
    _joint_gap_series,
    _joint_gap_series_check,
    _joint_open_band_rating,
    _joint_test_element_check,
    _lab_floor_covering_improvement,
    _lab_joint_insulation,
    _lab_lining_improvement,
    _layered_absorber,
    _level_difference_quantiles,
    _lifter,
    _limiting_test_signal,
    _lining_curing_check,
    _loop_field,
    _loop_impedance,
    _loop_requirement,
    _loudspeaker,
    _low_frequency,
    _low_frequency_procedure,
    _maximum_output_current,
    _measurement_disturbance,
    _method_a_summary,
    _method_b_summary,
    _microphone,
    _miso_coherence,
    _modulation,
    _monte_carlo,
    _neck_loop_characteristics,
    _neck_loop_verification,
    _open_plan,
    _outdoor,
    _overload,
    _pass_by_measurement,
    _pass_by_uncertainty,
    _people_assessment,
    _phase_decomposition,
    _pile_strike,
    _piston_directivity,
    _plant_contour,
    _plant_sound_power,
    _pleasantness_eventfulness,
    _porous_medium,
    _position_spread,
    _predicted_receptor,
    _pressure_reciprocity,
    _programme_characteristic_voltage,
    _programme_signal_check,
    _protection_voltage,
    _quadrature_phase_error,
    _radiation_efficiency,
    _rain_generator_verification,
    _rainfall_reference_correction,
    _rainfall_sound,
    _random_incidence,
    _rated_impedance,
    _reciprocity_air_attenuation,
    _reciprocity_budget,
    _rectangular_pulse,
    _reduction_improvement_rating,
    _reference_sound_source,
    _reference_source_calibration,
    _reference_source_drift,
    _reference_track,
    _reflection_grid_check,
    _reflection_index,
    _reflection_index_uncertainty,
    _reflection_limit,
    _relevant_turbines,
    _response_decay,
    _reverb_energy,
    _reverb_power,
    _rigid_mass_calibration,
    _rise_speed,
    _rolling_stock_roughness_record,
    _rolling_stock_test,
    _room,
    _room_modes,
    _roughness_comparability,
    _round_robin_precision,
    _sel_distribution,
    _service_equipment,
    _service_equipment_background,
    _service_equipment_positions,
    _shaped_sweep,
    _single_mode_fit,
    _single_panel,
    _slit_aperture,
    _slm_periodic,
    _small_roughness_deviation,
    _sound_calibrator,
    _sound_energy,
    _sound_power,
    _sound_strength,
    _soundscape_correlation,
    _source_directionality,
    _source_location_plan,
    _source_ranking,
    _special_room_power,
    _special_room_reverberation,
    _special_room_suitability,
    _special_room_surfaces,
    _static_airflow,
    _stationary_test,
    _statistical_pass_by,
    _stepped_sine_impulse_response,
    _sti,
    _swept_sine_distortion,
    _synchronous_average,
    _time_invariance,
    _time_selective_response,
    _tone_search,
    _track_decay_rate,
    _train_passage,
    _turbine_array,
    _turbine_declaration,
    _turbine_levels,
    _turbine_levels_by_sector,
    _turbine_power,
    _turbine_surface,
    _varying_background,
    _vector_change,
    _vibration_meter_reading,
    _vibration_meter_verification,
    _wave_motion_correction,
    _wind_shear,
    _window_correction,
    _window_metrics,
    _wt_rating,
    _zwicker_stationary,
    _zwicker_time_varying,
)

import phonometry as ph
from phonometry._plot import common as _plotting

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_api_docs as gad

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from matplotlib.axes import Axes
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from phonometry.simulation import ElasticFDTDResult, FDTDResult


# --------------------------------------------------------------------------
# Soft-dependency contract: lazy import + ImportError guidance
# --------------------------------------------------------------------------
def test_plotting_module_has_no_toplevel_matplotlib_import() -> None:
    """matplotlib must be imported inside functions, never at module scope."""
    tree = ast.parse(inspect.getsource(_plotting))
    # Imports inside a function body are lazy; imports under an
    # ``if TYPE_CHECKING:`` guard never run at import time. Both are allowed;
    # a plain module-scope runtime import of matplotlib is not.
    allowed: set[ast.AST] = set()
    for node in ast.walk(tree):
        is_func = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        is_typecheck = (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        )
        if is_func or is_typecheck:
            for sub in ast.walk(node):
                allowed.add(sub)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [module, *[a.name for a in node.names]]
            if any("matplotlib" in n for n in names):
                assert node in allowed, "matplotlib imported at runtime module scope"


def test_plot_raises_helpful_error_without_matplotlib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without matplotlib, .plot() fails with an actionable message."""
    real_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> ModuleType:
        if name.startswith("matplotlib"):
            msg = "No module named 'matplotlib'"
            raise ImportError(msg)
        return real_import(name, *args, **kwargs)

    res = _zwicker_stationary()
    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ImportError, match=r'pip install "phonometry\[plot\]"'):
        res.plot()


# --------------------------------------------------------------------------
# Every public .plot() must accept and forward a benign styling kwarg
# --------------------------------------------------------------------------
#: ISO 4869-2 Annex A: 16 subjects over the eight octaves from 63 Hz, which
#: every hearing-protector result is built from.
_PROTECTOR_ATTENUATION = [
    [4, 8, 13, 18, 20, 30, 35, 30],
    [6, 12, 16, 21, 29, 35, 47, 35],
    [10, 16, 17, 23, 25, 32, 48, 37],
    [3, 7, 12, 18, 20, 25, 33, 30],
    [8, 10, 16, 16, 25, 27, 43, 32],
    [4, 7, 10, 15, 19, 32, 35, 31],
    [5, 5, 9, 16, 20, 25, 30, 28],
    [15, 15, 21, 26, 25, 38, 46, 38],
    [5, 6, 10, 13, 19, 22, 29, 28],
    [9, 9, 10, 19, 20, 27, 37, 31],
    [9, 16, 18, 24, 25, 35, 44, 39],
    [5, 6, 11, 12, 17, 20, 28, 28],
    [7, 10, 17, 22, 25, 35, 41, 44],
    [6, 8, 16, 18, 19, 19, 30, 33],
    [10, 12, 17, 25, 28, 33, 45, 40],
    [12, 13, 17, 27, 29, 38, 49, 41],
]

_KWARG_PLOT_CASES = [
    ("zwicker", _zwicker_stationary, "line"),
    ("sti", _sti, "bar"),
    ("airborne", _airborne_rating, "line"),
    ("impact", _impact_rating, "line"),
    (
        "impact_improvement_rating",
        lambda: ph.building.ImpactImprovementSpectrum(
            name="Covering",
            source="A test",
            **{
                f"impact_improvement_{band}": 2.0 * index
                for index, band in enumerate(
                    (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000)
                    + (1250, 1600, 2000, 2500, 3150)
                )
            },
        ).rating(),
        "line",
    ),
    ("room", lambda: _room([250, 2000]), "bar"),
    ("sound_power", _sound_power, "bar"),
    ("reverb_power", _reverb_power, "bar"),
    ("in_situ_power", _in_situ_power, "bar"),
    ("hard_walled_power", _hard_walled_power, "bar"),
    ("hard_walled_room_check", _hard_walled_room_check, "bar"),
    ("source_location_plan", _source_location_plan, "bar"),
    ("special_room_power", _special_room_power, "bar"),
    ("special_room_reverberation", _special_room_reverberation, "line"),
    ("special_room_surfaces", _special_room_surfaces, "line"),
    ("special_room_suitability", _special_room_suitability, "bar"),
    ("high_frequency_power", _high_frequency_power, "bar"),
    ("inverse_square_law", _inverse_square_law, "line"),
    ("free_field_check", _free_field_check, "bar"),
    ("source_directionality", _source_directionality, "bar"),
    ("reference_source_calibration", _reference_source_calibration, "bar"),
    ("reference_sound_source", _reference_sound_source, "line"),
    ("reference_source_drift", _reference_source_drift, "bar"),
    ("turbine_surface", _turbine_surface, "line"),
    ("turbine_array", _turbine_array, "line"),
    (
        "turbine_environment",
        lambda: ph.emission.check_turbine_test_environment(
            ph.emission.turbine_environmental_correction(
                _turbine_surface().area, absorption_area=900.0
            )
        ),
        "line",
    ),
    (
        "turbine_correction",
        lambda: ph.emission.turbine_reference_source_correction(
            [95.0, 96.0], calibrated_level=93.0, machine_length_m=8.0
        ),
        "line",
    ),
    ("turbine_power", _turbine_power, "bar"),
    ("turbine_declaration", _turbine_declaration, "bar"),
    ("sound_energy", _sound_energy, "bar"),
    ("reverb_energy", _reverb_energy, "bar"),
    ("intensity_power", _intensity_power_negative, "bar"),
    ("intensity", _intensity, "line"),
    (
        "decay_curve",
        lambda: ph.room.decay_curve(_exp_ir(seconds=1.0, t60=0.6), FS),
        "line",
    ),
    (
        "facade",
        lambda: ph.building.facade_insulation(
            [70.0, 72.0, 74.0], [40.0, 41.0, 42.0], [0.5, 0.5, 0.5]
        ),
        "line",
    ),
    ("open_plan", _open_plan, "line"),
    ("outdoor", _outdoor, "line"),
    ("cnossos_road", _cnossos_road, "bar"),
    ("statistical_pass_by", _statistical_pass_by, "line"),
    ("reflection_index", _reflection_index, "line"),
    ("reflection_index_uncertainty", _reflection_index_uncertainty, "bar"),
    ("reflection_rating", lambda: _reflection_index().rating, "bar"),
    ("direct_sound_subtraction", _direct_sound_subtraction, "line"),
    ("reflection_limit", _reflection_limit, "bar"),
    ("reflection_grid_check", _reflection_grid_check, "line"),
    ("am_block", _am_block, "bar"),
    ("am_period", _am_period, "line"),
    ("am_bins", _am_bins, "line"),
    ("wind_shear", _wind_shear, "line"),
    ("binned_levels", _binned_levels, "line"),
    ("turbine_levels", _turbine_levels, "line"),
    ("turbine_levels_by_sector", _turbine_levels_by_sector, "line"),
    ("predicted_receptor", _predicted_receptor, "bar"),
    ("relevant_turbines", _relevant_turbines, "bar"),
    ("low_frequency_wind_turbine", _low_frequency, "line"),
    ("emergence", _emergence, "bar"),
    ("wind_turbine_rating", _wt_rating, "bar"),
    ("tone_search", _tone_search, "line"),
    ("roughness_spectrum", _rolling_stock_roughness_record, "line"),
    ("track_decay_rate", _track_decay_rate, "line"),
    ("pass_by_measurement", _pass_by_measurement, "line"),
    ("stationary_test", _stationary_test, "bar"),
    ("rolling_stock_test", _rolling_stock_test, "line"),
    ("rise_speed", _rise_speed, "line"),
    ("adjacent_neutrality", _adjacent_neutrality, "bar"),
    ("small_roughness_deviation", _small_roughness_deviation, "line"),
    ("roughness_comparability", _roughness_comparability, "line"),
    ("reference_track", _reference_track, "line"),
    ("pass_by_uncertainty", _pass_by_uncertainty, "bar"),
    (
        "pass_by_regression",
        lambda: _statistical_pass_by().regressions["1"],
        "line",
    ),
    ("impedance_tube", _impedance_tube, "line"),
    ("porous_medium", _porous_medium, "line"),
    ("layered_absorber", _layered_absorber, "line"),
    ("diffuse_absorption", _diffuse_absorption, "line"),
    ("monte_carlo", _monte_carlo, "bar"),
    ("exposure", _exposure, "bar"),
    ("sel_distribution", _sel_distribution, "line"),
    ("level_difference_quantiles", _level_difference_quantiles, "line"),
    ("round_robin_precision", _round_robin_precision, "bar"),
    ("calculation_verification", _calculation_verification, "line"),
    ("service_equipment", _service_equipment, "line"),
    ("service_equipment_background", _service_equipment_background, "line"),
    ("position_spread", _position_spread, "line"),
    ("service_equipment_positions", _service_equipment_positions, "line"),
    ("calibration_deviation", _calibration_deviation, "line"),
    ("background_duration", _background_duration, "line"),
    ("varying_background", _varying_background, "line"),
    ("measurement_disturbance", _measurement_disturbance, "line"),
    ("instrument_agreement", _instrument_agreement, "line"),
    ("pleasantness_eventfulness", _pleasantness_eventfulness, "line"),
    ("method_a_summary", _method_a_summary, "line"),
    ("soundscape_correlation", _soundscape_correlation, "line"),
    ("method_b_summary", _method_b_summary, "line"),
    ("source_ranking", _source_ranking, "bar"),
    ("binaural_indicators", _binaural_indicators, "bar"),
    ("directivity_factor", _directivity_factor, "line"),
    ("random_incidence", _random_incidence, "line"),
    ("diffuse_field", _diffuse_field, "line"),
    ("adjustment_value", _adjustment_value, "line"),
    ("free_field_correction", _free_field_correction, "line"),
    ("correction_budget", _correction_budget, "bar"),
    ("correction_verification", _correction_verification, "line"),
    ("comparison_calibration", _comparison_calibration, "line"),
    ("comparison_budget", _comparison_budget, "bar"),
    (
        "environmental_sensitivity_correction",
        _environmental_sensitivity_correction,
        "line",
    ),
    ("jig_diameter_correction", _jig_diameter_correction, "line"),
    ("free_field_region", _free_field_region, "line"),
    ("acoustic_center", _acoustic_centre, "line"),
    ("capillary_tube_impedance", _capillary_tube_impedance, "line"),
    ("coupler_check", _coupler_check, "bar"),
    ("coupler_parameter_uncertainty", _coupler_parameter_uncertainty, "line"),
    ("coupler_transfer_impedance", _coupler_transfer_impedance, "line"),
    ("free_field_arrangement", _free_field_arrangement, "bar"),
    ("free_field_parameter_uncertainty", _free_field_parameter_uncertainty, "line"),
    ("heat_conduction_correction", _heat_conduction_correction, "line"),
    ("pressure_reciprocity", _pressure_reciprocity, "line"),
    ("reciprocity_air_attenuation", _reciprocity_air_attenuation, "line"),
    ("reciprocity_budget", _reciprocity_budget, "line"),
    ("wave_motion_correction", _wave_motion_correction, "line"),
    ("comparison_phase", _comparison_phase, "line"),
    ("impedance_pressure_ratio", _impedance_pressure_ratio, "line"),
    ("rectangular_pulse", _rectangular_pulse, "line"),
    ("time_selective_response", _time_selective_response, "line"),
    ("stepped_sine_impulse_response", _stepped_sine_impulse_response, "line"),
    ("vibration_meter_reading", _vibration_meter_reading, "line"),
    ("vibration_meter_verification", _vibration_meter_verification, "line"),
    (
        "running_rms_decay_verification",
        lambda: ph.vibration.verify_running_rms_decay(
            0.98, integration_time=1.0, method="linear"
        ),
        "line",
    ),
    ("conformance_verification", _conformance_verification, "line"),
    (
        "sound_calibrator_requirement",
        lambda: _sound_calibrator().requirement("environmental_level"),
        "line",
    ),
    ("sound_calibrator_verification", _sound_calibrator, "bar"),
    ("filter_periodic", _filter_periodic, "line"),
    ("filter_periodic_clause", lambda: _filter_periodic().clause("13"), "line"),
    ("filter_periodic_figure_c1", lambda: _filter_periodic().clause("10.2"), "line"),
    ("slm_periodic", _slm_periodic, "line"),
    (
        "slm_periodic_requirement",
        lambda: _slm_periodic().requirement("toneburst"),
        "line",
    ),
    (
        "slm_periodic_margins",
        lambda: _slm_periodic().requirement("electrical_weighting"),
        "line",
    ),
    ("time_invariance", _time_invariance, "line"),
    ("assessment_velocity", _assessment_velocity, "line"),
    ("train_passage", _train_passage, "line"),
    ("people_assessment", _people_assessment, "bar"),
    (
        "assumed_protection",
        lambda: ph.hearing.assumed_protection_value(_PROTECTOR_ATTENUATION),
        "line",
    ),
    (
        "hml_rating",
        lambda: ph.hearing.hml_rating(_PROTECTOR_ATTENUATION),
        "line",
    ),
    ("snr_rating", lambda: ph.hearing.snr_rating(_PROTECTOR_ATTENUATION), "bar"),
    (
        "protected_level",
        lambda: ph.hearing.octave_band_protected_level(
            [75.0, 84.0, 86.0, 88.0, 97.0, 99.0, 97.0, 96.0],
            ph.hearing.assumed_protection_value(_PROTECTOR_ATTENUATION),
        ),
        "bar",
    ),
    (
        "real_ear_attenuation",
        lambda: ph.hearing.real_ear_attenuation(_PROTECTOR_ATTENUATION),
        "line",
    ),
    (
        "attenuation_difference",
        lambda: ph.hearing.assess_attenuation_difference(
            ph.hearing.real_ear_attenuation(_PROTECTOR_ATTENUATION),
            [6.0, 9.0, 14.0, 19.0, 22.0, 29.0, 30.0, 33.0],
            second_expanded_uncertainty_db=2.0,
        ),
        "bar",
    ),
    (
        "reat_sound_field",
        lambda: ph.hearing.check_reat_sound_field(
            dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 7),
            [0.0] * 7,
        ),
        "line",
    ),
    (
        "active_insertion_loss",
        lambda: ph.hearing.active_insertion_loss(
            [[20.0, 24.0, -3.0], [22.0, 23.0, -1.0], [21.0, 25.0, -2.0]],
            frequencies=[100.0, 125.0, 1000.0],
        ),
        "line",
    ),
    (
        "anr_total_attenuation",
        lambda: ph.hearing.anr_total_attenuation(
            _PROTECTOR_ATTENUATION, [[20.0] * 24] * len(_PROTECTOR_ATTENUATION)
        ),
        "line",
    ),
    (
        "anr_linearity",
        lambda: ph.hearing.assess_anr_linearity(
            [90.0, 95.0, 100.0], [[60.0, 65.0, 70.0], [60.0, 65.0, 69.0]]
        ),
        "line",
    ),
    (
        "audiometric_ambient_noise",
        lambda: ph.hearing.check_audiometric_ambient_noise(np.full(25, 10.0)),
        "line",
    ),
    (
        "ascending_method",
        lambda: ph.hearing.ascending_method_threshold(
            presentation_levels=[20, 25, 30, 20, 25, 30],
            responses=[False, False, True, False, False, True],
        ),
        "line",
    ),
    (
        "bracketing_method",
        lambda: ph.hearing.bracketing_method_threshold([30, 30, 35], [30, 35, 35]),
        "line",
    ),
    (
        "automatic_audiometry",
        lambda: ph.hearing.automatic_audiometry_threshold(
            [30, 20, 31, 21, 32, 20, 30, 19]
        ),
        "line",
    ),
    (
        "sweep_audiometry",
        lambda: ph.hearing.sweep_audiometry_threshold(
            [30.0, 20.0] * 6, reversal_frequencies=np.geomspace(500.0, 4000.0, 12)
        ),
        "line",
    ),
    (
        "retest_agreement",
        lambda: ph.hearing.check_retest_agreement(25.0, 30.0),
        "line",
    ),
    (
        "audiogram_cautions",
        lambda: ph.hearing.audiogram_cautions(
            [250.0, 500.0, 1000.0],
            air_conduction_threshold_levels=[20.0, 40.0, 45.0],
            bone_conduction_threshold_levels=[40.0, 30.0, 35.0],
        ),
        "line",
    ),
    (
        "audiometric_uncertainty",
        lambda: ph.hearing.audiometric_uncertainty(1000.0),
        "bar",
    ),
    (
        "diffuse_sound_field",
        lambda: ph.hearing.check_diffuse_sound_field(
            dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 11),
            [0.0] * 11,
        ),
        "line",
    ),
    (
        "free_sound_field",
        lambda: ph.hearing.check_free_sound_field(
            dict.fromkeys(("left", "right", "up", "down"), [0.5] * 11),
            [0.0] * 11,
            front_levels=[1.0] * 11,
            back_levels=[0.0] * 11,
            loudspeaker_distance_m=2.0,
        ),
        "line",
    ),
    (
        "earmuff_insertion_loss",
        lambda: ph.hearing.earmuff_insertion_loss(
            np.full(22, 90.0), np.full((3, 22), 70.0) + np.arange(3)[:, None]
        ),
        "line",
    ),
    (
        "insertion_loss_uncertainty",
        lambda: ph.hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY,
        "bar",
    ),
    (
        "plane_progressive_wave",
        lambda: ph.hearing.check_plane_progressive_wave([[80.0] * 22, [81.0] * 22]),
        "line",
    ),
    (
        "fixture_isolation",
        lambda: ph.hearing.verify_fixture_isolation(
            np.full(22, 120.0), np.full(22, 55.0)
        ),
        "line",
    ),
    ("static_airflow", _static_airflow, "line"),
    ("airborne_prediction", _airborne_prediction, "bar"),
    ("impact_prediction", _impact_prediction, "bar"),
    ("airborne_insulation", _airborne_insulation, "line"),
    ("impact_insulation", _impact_insulation, "line"),
    ("low_frequency_procedure", _low_frequency_procedure, "line"),
    ("laboratory_lining_improvement", _lab_lining_improvement, "line"),
    ("reduction_improvement_rating", _reduction_improvement_rating, "line"),
    ("laboratory_floor_covering_improvement", _lab_floor_covering_improvement, "line"),
    ("heavy_impact_improvement", _heavy_impact_improvement, "line"),
    ("laboratory_joint_insulation", _lab_joint_insulation, "line"),
    ("joint_open_band_rating", _joint_open_band_rating, "bar"),
    ("joint_test_element_check", _joint_test_element_check, "bar"),
    ("gap_width_check", _gap_width_check, "line"),
    ("joint_gap_series", _joint_gap_series, "line"),
    ("joint_gap_series_check", _joint_gap_series_check, "line"),
    ("lining_curing_check", _lining_curing_check, "line"),
    ("rainfall_reference_correction", _rainfall_reference_correction, "line"),
    ("rainfall_sound", _rainfall_sound, "line"),
    ("rain_generator_verification", _rain_generator_verification, "line"),
    (
        "low_frequency_element",
        lambda: ph.building.low_frequency_element_normalized_difference(
            [84.0, 86.0, 88.0],
            [70.0, 73.0, 76.0],
            measurement_area=2.0,
            n_elements=4,
            l_p=[78.0, 80.0, 82.0],
            frequencies=[50.0, 63.0, 80.0],
        ),
        "bar",
    ),
    (
        "low_frequency_intensity",
        lambda: ph.building.low_frequency_intensity_reduction(
            [84.0, 86.0, 88.0],
            [70.0, 73.0, 76.0],
            measurement_area=12.0,
            area=10.0,
            frequencies=[50.0, 63.0, 80.0],
        ),
        "bar",
    ),
    ("band_uncertainty", _band_uncertainty, "line"),
    ("band_averaged_stiffness", _band_averaged_stiffness, "line"),
    (
        "blocked_output_check",
        lambda: ph.vibration.check_blocked_output(
            frequencies=[50.0, 100.0, 200.0],
            input_acceleration_level=[100.0, 100.0, 100.0],
            output_acceleration_level=[70.0, 75.0, 60.0],
        ),
        "line",
    ),
    (
        "output_mass_check",
        lambda: ph.vibration.check_output_mass(
            frequencies=[50.0, 100.0, 200.0],
            output_mass_kg=0.1,
            output_force_level=[120.0, 120.0, 120.0],
            output_acceleration_level=[100.0, 105.0, 110.0],
        ),
        "line",
    ),
    ("effective_blocking_mass", _effective_blocking_mass, "line"),
    ("driving_point_stiffness", _driving_point_stiffness, "line"),
    ("impact_mobility", _impact_mobility, "line"),
    ("single_mode_fit", _single_mode_fit, "line"),
    ("window_correction", _window_correction, "bar"),
    ("double_hit", _double_hit, "line"),
    ("force_spectrum", _force_spectrum, "line"),
    ("coherence_check", _coherence_check, "line"),
    ("overload", _overload, "line"),
    ("response_decay", _response_decay, "line"),
    ("channel_match", _channel_match, "line"),
    (
        "driving_point_uncertainty",
        lambda: ph.vibration.driving_point_uncertainty(
            120.0, repeatability_range_db=0.6
        ),
        "bar",
    ),
    ("radiation_efficiency", _radiation_efficiency, "line"),
    ("single_panel", _single_panel, "line"),
    ("double_wall", _double_wall, "line"),
    ("slit_aperture", _slit_aperture, "line"),
    ("modulation_distortion", _modulation, "line"),
    ("field_indicators", _field_indicators, "line"),
    ("loop_field", _loop_field, "line"),
    ("loop_impedance", _loop_impedance, "line"),
    ("amplifier_frequency_response", _amplifier_frequency_response, "line"),
    ("agc_characteristic", _agc_characteristic, "line"),
    ("quadrature_phase_error", _quadrature_phase_error, "line"),
    ("neck_loop_characteristics", _neck_loop_characteristics, "line"),
    ("neck_loop_verification", _neck_loop_verification, "bar"),
    ("field_strength_reading", _field_strength_reading, "line"),
    ("background_noise", _background_noise, "line"),
    ("induction_loop_verification", _induction_loop_verification, "bar"),
    ("loop_requirement", _loop_requirement, "line"),
    ("amplifier_overload", _amplifier_overload, "line"),
    ("max_output_current", _maximum_output_current, "line"),
    ("programme_signal_check", _programme_signal_check, "line"),
    ("limiting_test_signal", _limiting_test_signal, "line"),
    ("rated_impedance", _rated_impedance, "line"),
    ("program_characteristic_voltage", _programme_characteristic_voltage, "bar"),
    ("protection_voltage", _protection_voltage, "line"),
    ("coupler_frequency_response", _coupler_frequency_response, "line"),
    ("crosstalk_attenuation", _crosstalk_attenuation, "line"),
    ("field_comparison_response", _field_comparison_response, "bar"),
    ("ear_canal_frequency_response", _ear_canal_frequency_response, "line"),
    ("ear_canal_microphone", _ear_canal_microphone, "bar"),
    (
        "flight_profile",
        lambda: ph.aircraft.load_anp_database().flight_profile(
            "A320-211",
            "departure",
            aerodrome=ph.aircraft.Aerodrome(elevation_ft=0.0),
        ),
        "line",
    ),
    (
        "attenuation_arp866a",
        lambda: ph.aircraft.attenuation_arp866a(
            [500.0, 1000.0, 2000.0], temperature_c=10.0, relative_humidity_percent=80.0
        ),
        "line",
    ),
    (
        "spectral_class",
        lambda: ph.aircraft.load_anp_database().spectral_class(103),
        "line",
    ),
    (
        "npd_atmosphere_increment",
        lambda: ph.aircraft.npd_atmosphere_increment(
            ph.aircraft.load_anp_database().spectral_class(103),
            temperature_c=10.0,
            relative_humidity_percent=80.0,
        ),
        "line",
    ),
    ("plant_contour", _plant_contour, "line"),
    ("plant_sound_power", _plant_sound_power, "bar"),
    (
        "plant_measurement_check",
        lambda: ph.emission.check_plant_measurement(
            _plant_contour(), _plant_sound_power(), measurement_time_s=90.0
        ),
        "bar",
    ),
    (
        "partial_plant_contributions",
        lambda: ph.emission.partial_plant_contributions(
            [_plant_sound_power(), _plant_sound_power()], names=["North", "South"]
        ),
        "bar",
    ),
    (
        "revised_npd_curves",
        lambda: ph.aircraft.load_anp_database().revised_npd_curves(
            "747100", "D", temperature_c=10.0, relative_humidity_percent=80.0
        ),
        "line",
    ),
    (
        "coherence",
        lambda: ph.electroacoustics.coherence(
            np.sin(np.arange(4096) / 3.0),
            np.sin(np.arange(4096) / 3.0) + np.cos(np.arange(4096) / 7.0),
            fs=1000.0,
        ),
        "line",
    ),
    (
        "octave_band_levels",
        lambda: ph.emission.octave_band_levels(
            [60.0, 62.0, 61.0], frequencies=[50.0, 63.0, 80.0]
        ),
        "bar",
    ),
    (
        "wavelength_spectrum",
        lambda: ph.environment.sources.cnossos_rail.rail_roughness(
            ph.environment.sources.cnossos_rail.RailRoughnessClass.WELL_MAINTAINED
        ),
        "line",
    ),
    (
        "one_third_octave_absorption",
        lambda: ph.materials.surfaces.one_third_octave_absorption(
            np.linspace(0.1, 0.9, 200), frequencies=np.linspace(400.0, 1200.0, 200)
        ),
        "bar",
    ),
    (
        "loudness_contour",
        lambda: ph.psychoacoustics.equal_loudness_contour(40.0),
        "line",
    ),
    (
        "background_corrected_level",
        lambda: ph.building.background_corrected_level(
            [60.0, 45.0, 33.0], [30.0, 35.0, 30.0], frequencies=[100.0, 125.0, 160.0]
        ),
        "bar",
    ),
    (
        "strong_coupling_check",
        lambda: ph.building.check_strong_coupling(
            [4.0, 2.0, 6.0], 200.0, 200.0, 100.0, 100.0
        ),
        "line",
    ),
    (
        "energy_spectral_density",
        lambda: ph.vibration.energy_spectral_density(
            np.exp(-np.arange(128) / 8.0), fs=1000.0
        ),
        "line",
    ),
]


@pytest.mark.parametrize(
    ("name", "factory", "kind"),
    _KWARG_PLOT_CASES,
    ids=[c[0] for c in _KWARG_PLOT_CASES],
)
def test_every_plot_forwards_kwargs_to_primary_artist(
    name: str, factory: Callable[[], object], kind: str
) -> None:
    res = factory()
    out = res.plot(linewidth=2)
    ax = out[0] if isinstance(out, tuple) else out
    artists = ax.lines if kind == "line" else ax.patches
    assert artists, f"{name}: no primary {kind} artist drawn"
    assert any(a.get_linewidth() == 2.0 for a in artists), (
        f"{name}: linewidth kwarg not forwarded to the primary artist"
    )
    plt.close("all")

    # A user-supplied color must win over the renderer's fixed default rather
    # than raising ``TypeError: got multiple values for keyword 'color'``.
    out = res.plot(color="red")
    ax = out[0] if isinstance(out, tuple) else out
    artists = ax.lines if kind == "line" else ax.patches
    red = plt.matplotlib.colors.to_rgba("red")

    def _is_red(artist: Line2D | Patch) -> bool:
        if kind == "line":
            return plt.matplotlib.colors.to_rgba(artist.get_color()) == red
        return tuple(artist.get_facecolor()) == red

    assert any(_is_red(a) for a in artists), (
        f"{name}: color kwarg did not override the fixed default artist color"
    )
    plt.close("all")

    # And the same for `label`, which is where this went wrong for longest.
    # `color` was passed by name next to `**kwargs` once and fixed; `label`
    # was passed that way in fifty-five renderers, so a caller naming a curve
    # got `TypeError: got multiple values for keyword argument 'label'`
    # instead of a labelled curve.
    out = res.plot(label="mine")
    ax = out[0] if isinstance(out, tuple) else out
    # Through the legend, not through the artist: `ax.bar` puts the label on
    # the container it returns rather than on each rectangle, so reading
    # `ax.patches` would miss it on every bar renderer. The legend is what the
    # caller is naming the curve for anyway.
    assert "mine" in ax.get_legend_handles_labels()[1], (
        f"{name}: label kwarg did not reach the legend"
    )
    plt.close("all")

    # Matplotlib gives seven properties two names, and since 3.3 a call that
    # receives both is `TypeError: Got both 'color' and 'c', which are aliases
    # of one another`. A renderer that defaults its own colour under one
    # spelling therefore refuses every caller who wrote the other, which is
    # what 195 `setdefault` calls across 24 modules did until `style_default`
    # replaced them. The long spelling is checked above; this is the short one,
    # and it has to reach the artist rather than raise.
    # `c` is the short spelling of `color` on a Line2D only: a Rectangle has no
    # such alias, so the bar renderers are held to `lw`, which every artist
    # aliases, and the colour half of the check stays with the line renderers.
    out = res.plot(c="red", lw=2) if kind == "line" else res.plot(lw=2)
    ax = out[0] if isinstance(out, tuple) else out
    artists = ax.lines if kind == "line" else ax.patches
    assert any(a.get_linewidth() == 2.0 for a in artists), (
        f"{name}: the short spelling of linewidth did not reach the artist"
    )
    if kind == "line":
        assert any(_is_red(a) for a in artists), (
            f"{name}: the short spelling of color did not reach the artist"
        )
    plt.close("all")

    # A property no renderer thought of as the caller's: `zorder` was written
    # beside the caller's keywords, or a copy of them, in renderers across the
    # package, so a caller who stacked a curve got `TypeError: got multiple
    # values for keyword argument 'zorder'` instead of a figure.
    out = res.plot(zorder=7)
    ax = out[0] if isinstance(out, tuple) else out
    artists = ax.lines if kind == "line" else ax.patches
    assert any(a.get_zorder() == 7 for a in artists), (
        f"{name}: zorder kwarg did not reach the primary artist"
    )
    plt.close("all")


# --------------------------------------------------------------------------
# One signature for every .plot(): ax first, everything else by name
# --------------------------------------------------------------------------
def _public_plot_methods() -> dict[str, Callable[..., object]]:
    """Every ``plot`` a caller can reach on a class the package publishes.

    Walks the imported package rather than the source, so a class published
    from a private module (``io._signal.Signal``) counts under the public name
    that reaches it, and a ``plot`` inherited from a phonometry base class is
    held to the rule on every subclass that exposes it.
    """
    import importlib
    import pkgutil

    found: dict[str, Callable[..., object]] = {}
    for info in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if name.startswith("_") or not inspect.isclass(obj):
                continue
            if not obj.__module__.startswith("phonometry"):
                continue
            try:
                method = inspect.getattr_static(obj, "plot")
            except AttributeError:
                continue
            if isinstance(method, staticmethod | classmethod):
                method = method.__func__
            if inspect.isfunction(method):
                found.setdefault(f"{obj.__module__}.{obj.__qualname__}", method)
    return found


#: The parameter kinds a call can fill by position.
_BY_POSITION = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.VAR_POSITIONAL,
)


def test_every_plot_takes_ax_first_and_the_rest_by_name() -> None:
    """``result.plot(ax)`` draws into ``ax``, on every result in the library.

    Two shapes broke it. Three results put a choice before the axes
    (``plot(quantity, ax)``, ``plot(frequency, characteristic_impedance,
    ax)``), so the call every other result accepts raised or, worse, bound the
    axes to a frequency vector. Six took ``language`` by position, so
    ``plot(ax, "es")`` worked on those six and nowhere else. The rule is the
    one every other result keeps: the axes first, and every other
    argument, ``language`` included, keyword-only. Eight results that hand
    the drawing to another took ``language`` only through ``**kwargs``, so
    their signatures hid it: every plot names it.
    """
    methods = _public_plot_methods()
    assert len(methods) > 200, "the walk found too few plot methods to mean anything"
    offenders: list[str] = []
    for owner, method in sorted(methods.items()):
        parameters = list(inspect.signature(method).parameters.values())[1:]
        if not parameters or parameters[0].name != "ax":
            first = parameters[0].name if parameters else None
            offenders.append(f"{owner}.plot: first parameter is {first!r}, not 'ax'")
            continue
        offenders.extend(
            f"{owner}.plot: {parameter.name!r} can be passed by position"
            for parameter in parameters[1:]
            if parameter.kind in _BY_POSITION and parameter.name != "language"
        )
        language = next((p for p in parameters if p.name == "language"), None)
        if language is None:
            offenders.append(f"{owner}.plot: takes no 'language'")
        elif language.kind is not inspect.Parameter.KEYWORD_ONLY:
            offenders.append(f"{owner}.plot: 'language' is not keyword-only")
    assert not offenders, "\n".join(offenders)


def _public_plot_helpers() -> dict[str, Callable[..., object]]:
    """Every ``plot_*`` function a public module publishes in its ``__all__``."""
    import importlib
    import pkgutil

    found: dict[str, Callable[..., object]] = {}
    for info in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if name.startswith("plot_") and inspect.isfunction(obj):
                found.setdefault(name, obj)
    return found


def test_every_plot_helper_takes_its_axes_and_language_by_name() -> None:
    """``plot_x(data, *, ax=None, ..., language="en", **kwargs)`` on every helper.

    The helpers drew from three shapes. Seventeen took the axes by position
    after their data (``plot_plate_geometry(0.8, 0.6, ax)``), six took it first and
    every dimension by name (``plot_barrier_geometry(ax, source_height_m=...)``),
    and one took it by name only, so a caller had to know which helper was
    which before passing the axes the same way twice. A geometry helper whose
    first number is a dimension and whose second is the axes also turns a
    forgotten argument into an axes bound to a length. Now the data a helper
    draws is positional, and the axes, the language and the style keywords are
    written by name on all of them.
    """
    helpers = _public_plot_helpers()
    assert len(helpers) >= 24, "the walk found too few plot helpers to mean anything"
    offenders: list[str] = []
    for name, helper in sorted(helpers.items()):
        parameters = inspect.signature(helper).parameters
        for wanted in ("ax", "language"):
            parameter = parameters.get(wanted)
            if parameter is None:
                offenders.append(f"{name}: takes no {wanted!r}")
            elif parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
                offenders.append(f"{name}: {wanted!r} can be passed by position")
        var_keyword = next(
            (
                p.name
                for p in parameters.values()
                if p.kind is inspect.Parameter.VAR_KEYWORD
            ),
            None,
        )
        if var_keyword is None:
            offenders.append(f"{name}: forwards no style keywords (**kwargs)")
        elif not _reads_in_body(helper, var_keyword):
            offenders.append(f"{name}: takes **{var_keyword} and never reads it")
    assert not offenders, "\n".join(offenders)


def _reads_in_body(function: Callable[..., object], name: str) -> bool:
    """Whether the body of ``function`` reads the local ``name``.

    A helper that declares ``**kwargs`` and never touches it accepts every
    style keyword and draws nothing with it, so the signature alone does not
    prove the keywords are forwarded.
    """
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    definition = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == function.__name__
    )
    return any(
        isinstance(node, ast.Name)
        and node.id == name
        and isinstance(node.ctx, ast.Load)
        for statement in definition.body
        for node in ast.walk(statement)
    )


# --------------------------------------------------------------------------
# Common contract: ax=None creates a figure; passing ax composes
# --------------------------------------------------------------------------
def test_single_axes_plots_accept_external_ax() -> None:
    for res in (
        _zwicker_stationary(),
        _sti(),
        _airborne_rating(),
        _extended_rating(),
        _extended_impact_rating(),
        _sound_power(),
        _sound_energy(),
        _reverb_energy(),
        _open_plan(),
        _outdoor(),
        _cnossos_road(),
        _statistical_pass_by(),
        _statistical_pass_by().regressions["2a"],
        _reflection_index(),
        _reflection_index_uncertainty(),
        _direct_sound_subtraction(),
        _reflection_limit(),
        _reflection_grid_check(),
        _am_block(),
        _am_period(),
        _am_bins(),
        _wind_shear(),
        _binned_levels(),
        _turbine_levels(),
        _turbine_levels_by_sector(),
        _predicted_receptor(),
        _relevant_turbines(),
        _low_frequency(),
        _emergence(),
        _wt_rating(),
        _tone_search(),
        _adjacent_neutrality(),
        _pass_by_measurement(),
        _pass_by_uncertainty(),
        _reference_track(),
        _rise_speed(),
        _rolling_stock_roughness_record(),
        _rolling_stock_test(),
        _roughness_comparability(),
        _small_roughness_deviation(),
        _stationary_test(),
        _track_decay_rate(),
        _impedance_tube(),
        _porous_medium(),
        _layered_absorber(),
        _diffuse_absorption(),
        _monte_carlo(),
        _exposure(),
        _sel_distribution(),
        _level_difference_quantiles(),
        _round_robin_precision(),
        _calculation_verification(),
        _service_equipment(),
        _service_equipment_background(),
        _position_spread(),
        _service_equipment_positions(),
        _calibration_deviation(),
        _background_duration(),
        _varying_background(),
        _measurement_disturbance(),
        _instrument_agreement(),
        _pleasantness_eventfulness(),
        _method_a_summary(),
        _soundscape_correlation(),
        _method_b_summary(),
        _source_ranking(),
        _binaural_indicators(),
        _random_incidence(),
        _diffuse_field(),
        _adjustment_value(),
        _free_field_correction(),
        _correction_budget(),
        _correction_verification(),
        ph.hearing.check_audiometric_ambient_noise(np.full(25, 10.0)),
        ph.hearing.bracketing_method_threshold([30, 30, 35], [30, 35, 35]),
        ph.hearing.check_retest_agreement(25.0, 30.0),
        ph.hearing.audiogram_cautions(
            [250.0, 500.0], air_conduction_threshold_levels=[20.0, 45.0]
        ),
        ph.hearing.audiometric_uncertainty(1000.0),
        ph.hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY,
        ph.hearing.verify_fixture_isolation(np.full(22, 120.0), np.full(22, 55.0)),
        _comparison_calibration(),
        _comparison_budget(),
        _environmental_sensitivity_correction(),
        _jig_diameter_correction(),
        _free_field_region(),
        _acoustic_centre(),
        _capillary_tube_impedance(),
        _coupler_check(),
        _coupler_parameter_uncertainty(),
        _coupler_transfer_impedance(),
        _free_field_arrangement(),
        _free_field_parameter_uncertainty(),
        _heat_conduction_correction(),
        _pressure_reciprocity(),
        _reciprocity_air_attenuation(),
        _reciprocity_budget(),
        _wave_motion_correction(),
        _comparison_phase(),
        _impedance_pressure_ratio(),
        _rectangular_pulse(),
        _time_selective_response(),
        _stepped_sine_impulse_response(),
        _static_airflow(),
        _airborne_prediction(),
        _impact_prediction(),
        _airborne_insulation(),
        _impact_insulation(),
        _low_frequency_procedure(),
        _lab_lining_improvement(),
        _reduction_improvement_rating(),
        _lab_floor_covering_improvement(),
        _heavy_impact_improvement(),
        _lab_joint_insulation(),
        _joint_open_band_rating(),
        _joint_test_element_check(),
        _gap_width_check(),
        _joint_gap_series(),
        _joint_gap_series_check(),
        _lining_curing_check(),
        _rainfall_reference_correction(),
        _rainfall_sound(),
        _rain_generator_verification(),
        _band_uncertainty(),
        _impact_mobility(),
        _single_mode_fit(),
        _window_correction(),
        _double_hit(),
        _force_spectrum(),
        _coherence_check(),
        _overload(),
        _response_decay(),
        _channel_match(),
        ph.vibration.verify_running_rms_decay(
            4.7, integration_time=1.0, method="exponential"
        ),
        _conformance_verification(),
        _sound_calibrator(),
        _sound_calibrator().requirement("level"),
        _filter_periodic(),
        _filter_periodic().clause("13"),
        _slm_periodic(),
        _slm_periodic().requirement("toneburst"),
        _slm_periodic().requirement("electrical_weighting"),
        _time_invariance(),
        _turbine_surface(),
        _turbine_array(),
        _turbine_power(),
        _turbine_declaration(),
        _plant_contour(),
        _plant_sound_power(),
        ph.emission.check_plant_measurement(_plant_contour()),
        ph.aircraft.load_anp_database().flight_profile(
            "A320-211", "departure", aerodrome=ph.aircraft.Aerodrome(elevation_ft=0.0)
        ),
    ):
        fig, ax = plt.subplots()
        out = res.plot(ax=ax)
        assert out is ax
        plt.close(fig)


def test_no_renderer_defaults_a_label_on_the_shared_kwargs_inside_a_loop() -> None:
    """One `setdefault` in a loop names every curve after the first one.

    `dict.setdefault` mutates, so a renderer that draws several named curves
    has to take a copy per curve. Doing it once on `kwargs` sets the first
    label and then finds it already there on every later pass, which is not a
    crash and not a test failure anywhere else: the figure simply comes out
    with one legend entry repeated, and the only thing that noticed was a
    committed report preview drifting by 693 pixels.

    This is a structural check because the behavioural one cannot be written
    once: what "several named curves" means differs per renderer, while the
    shape that produces the bug is the same everywhere.
    """
    import ast
    import pathlib

    root = (
        pathlib.Path(__file__).resolve().parent.parent / "src" / "phonometry" / "_plot"
    )
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.For | ast.While | ast.AsyncFor):
                continue
            offenders.extend(
                f"{path.name}:{child.lineno}"
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "setdefault"
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "kwargs"
                and child.args
                and isinstance(child.args[0], ast.Constant)
                and child.args[0].value == "label"
            )
    assert not offenders, (
        "a label default on the shared kwargs inside a loop names every curve "
        f"after the first one: {offenders}. Take a copy per iteration."
    )


def _obstacle_domain() -> object:
    from phonometry.simulation import FDTD2D

    mask = np.zeros((20, 20), dtype=bool)
    mask[8:12, 8:12] = True
    return FDTD2D(343.0, 0.05, shape=(20, 20), obstacle_mask=mask)


def _open_domain() -> object:
    """A domain with no obstacle, whose figure still sits on the grid."""
    from phonometry.simulation import FDTD2D

    return FDTD2D(343.0, 0.05, shape=(20, 20))


def _snapshot_plot(result: FDTDResult | ElasticFDTDResult) -> object:
    """*result* with its snapshot plot as its ``plot``, for a row of the table below."""
    import functools
    import types

    return types.SimpleNamespace(plot=functools.partial(result.plot, kind="snapshot"))


def _acoustic_snapshots() -> object:
    from phonometry.simulation import (
        FDTDRecording,
        FDTDRun,
        GaussianPulse,
        fdtd_simulation,
    )

    run = FDTDRun(
        c=343.0,
        dx=9.0e-3,
        duration_s=1.0e-3,
        shape=(20, 24),
        sources=[GaussianPulse(ix=7, iy=5, half_width_s=1.0e-4)],
        recording=FDTDRecording(snapshot_every=10),
    )
    return _snapshot_plot(fdtd_simulation(run))


def _elastic_snapshots() -> object:
    from phonometry.simulation import (
        ElasticRecording,
        ElasticRun,
        ExplosionSource,
        elastic_fdtd_simulation,
    )

    def pulse(t: float) -> float:
        return float(np.exp(-(((t - 2e-5) / 5e-6) ** 2)))

    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=1e-4,
        rho=2500.0,
        shape=(20, 21),
        sources=[ExplosionSource(ix=10, iy=9, waveform=pulse)],
        recording=ElasticRecording(snapshot_every=4),
    )
    return _snapshot_plot(elastic_fdtd_simulation(run))


@pytest.mark.parametrize(
    ("factory", "draw", "keyword", "value"),
    [
        (_round_robin_precision, "plot", "width", 0.1),
        (_round_robin_precision, "plot", "align", "center"),
        (_programme_characteristic_voltage, "plot", "bottom", 0.0),
        (_binned_levels, "plot", "yerr", 0.0),
        (_filter_periodic, "plot", "yerr", 0.0),
        (lambda: _filter_periodic().clause("13"), "plot", "yerr", 0.0),
        (_slm_periodic, "plot", "yerr", 0.0),
        (
            lambda: _slm_periodic().requirement("electrical_weighting"),
            "plot",
            "yerr",
            0.0,
        ),
        (_obstacle_domain, "plot_geometry", "extent", (0.0, 1.0, 1.0, 0.0)),
        (_obstacle_domain, "plot_geometry", "origin", "lower"),
        (_open_domain, "plot_geometry", "extent", (0.0, 1.0, 1.0, 0.0)),
        (_open_domain, "plot_geometry", "origin", "lower"),
        (_acoustic_snapshots, "plot", "color_limit", 0.5),
        (_elastic_snapshots, "plot", "color_limit", 0.5),
    ],
)
def test_a_keyword_the_renderer_computes_from_the_data_is_refused(
    factory: Callable[[], object], draw: str, keyword: str, value: object
) -> None:
    """The caller's style wins over the renderer's, its data does not.

    A bar baseline measured from a floor, the error bars of a mean, the bins
    of a histogram, the extent of a field and the colour limit of a single
    snapshot, whose scale is its own field's, drawn from the caller would put
    the data where it was not measured, so the renderer names and refuses
    them instead of drawing the caller's numbers over its own.
    """
    method = getattr(factory(), draw)
    with pytest.raises(TypeError, match=f"{keyword} cannot be overridden"):
        method(**{keyword: value})
    plt.close("all")


# --------------------------------------------------------------------------
# A plot returns the type its signature promises for the axes it was handed
# --------------------------------------------------------------------------
#: A built result for every public result whose ``.plot()`` returns what an
#: argument decides (overloaded on ``ax``, or on a ``view`` or a ``quantity``
#: that chooses a polar axes) or always returns a polar axes, keyed as
#: :func:`_public_plot_methods` keys it.
_DECIDED_PLOT_RESULTS: dict[str, Callable[[], Any]] = {
    "phonometry.electroacoustics.frequency_response.FrequencyResponseResult": (
        _frequency_response
    ),
    "phonometry.electroacoustics.loudspeaker.LoudspeakerCharacteristics": (
        _loudspeaker
    ),
    "phonometry.electroacoustics.microphone.MicrophoneCharacteristics": _microphone,
    "phonometry.electroacoustics.piston.PistonDirectivity": _piston_directivity,
    "phonometry.electroacoustics.swept_sine.SweptSineDistortionResult": (
        _swept_sine_distortion
    ),
    "phonometry.filters.equalizer.EQResponseResult": _eq_response,
    "phonometry.materials.diffusers.design.DiffuserPolarResponse": (
        _diffuser_polar_response
    ),
    "phonometry.materials.diffusers.scattering_diffusion.DiffusionResult": _diffusion,
    "phonometry.metrology.random_incidence.DirectivityFactor": _directivity_factor,
    "phonometry.psychoacoustics.loudness.ecma.EcmaLoudness": _ecma_loudness,
    "phonometry.psychoacoustics.loudness.zwicker.ZwickerLoudness": (
        _zwicker_time_varying
    ),
    "phonometry.psychoacoustics.quality._fluctuation_strength_ecma.EcmaFluctuationStrength": (
        _ecma_fluctuation_strength
    ),
    "phonometry.psychoacoustics.quality._roughness_ecma.EcmaRoughness": (
        _ecma_roughness
    ),
    "phonometry.psychoacoustics.quality._tonality_ecma.EcmaTonality": _ecma_tonality,
    "phonometry.room._impulse_response.ImpulseResponseResult": _impulse_response,
    "phonometry.room._impulse_response.ShapedSweepResult": _shaped_sweep,
    "phonometry.room.acoustics.RoomAcousticsResult": lambda: _room([250, 2000]),
    "phonometry.room.auditorium.SoundStrengthResult": _sound_strength,
    "phonometry.room.modes.RoomModesResult": _room_modes,
    "phonometry.signals._cepstrum.LifterResult": _lifter,
    "phonometry.signals._envelope.EnvelopeResult": _envelope,
    "phonometry.signals._envelope.EnvelopeSpectrumResult": _envelope_spectrum,
    "phonometry.signals.miso.MISOCoherenceResult": _miso_coherence,
    "phonometry.signals.phase.PhaseDecompositionResult": _phase_decomposition,
    "phonometry.signals.spectra.CoherentOutputSpectrumResult": (
        _coherent_output_spectrum
    ),
    "phonometry.signals.spectra.CrossSpectralDensityResult": _cross_spectral_density,
    "phonometry.signals.synchronous_average.SynchronousAverageResult": (
        _synchronous_average
    ),
    "phonometry.signals.windows.WindowMetricsResult": _window_metrics,
    "phonometry.underwater.sources.pile_driving_noise.PileStrikeResult": _pile_strike,
    "phonometry.vibration.machinery.evaluation.VectorChangeResult": _vector_change,
    "phonometry.vibration.structural._impact_mobility.ChannelMatchVerification": (
        _channel_match
    ),
    "phonometry.vibration.structural._impact_mobility.DoubleHitCheck": _double_hit,
    "phonometry.vibration.structural._impact_mobility.ImpactMobilityResult": (
        _impact_mobility
    ),
    "phonometry.vibration.structural.mechanical_mobility.RigidMassCalibrationResult": (
        _rigid_mass_calibration
    ),
}

#: The public ``plot_`` helpers whose return an argument decides, each called
#: on a small input of its own with the keywords the test chooses.
_DECIDED_PLOT_HELPERS: dict[str, Callable[..., object]] = {
    "plot_excitation": lambda **kwargs: ph.room.plot_excitation(
        ph.room.sweep_signal(FS, 100.0, 4000.0, 0.1), FS, **kwargs
    ),
}

#: What a head's return annotation promises, read off its text as the API
#: reference prints it (an alias such as ``TwoPanels`` spelled out): one axes,
#: a polar one, a column of ``n`` axes, or one or two as the data decide.
_A_COLUMN = "tuple[Axes"


def _promised(head: Callable[..., object]) -> str:
    """The return annotation of ``head``, its unpublished aliases spelled out."""
    written = str(inspect.signature(head).return_annotation)
    return gad.expand_unpublished_aliases(written, head.__module__)


def _decided(function: Callable[..., object]) -> bool:
    """Whether an argument decides what a plot returns, or it returns a polar axes.

    Overloads whose heads all return the same type (the "both or neither"
    heads of a geometry helper) decide nothing about the return.
    """
    returns = {_promised(head) for head in typing.get_overloads(function)}
    return len(returns) > 1 or "PolarAxes" in _promised(function)


@functools.cache
def _decided_methods() -> dict[str, Callable[..., object]]:
    """Every public ``plot`` whose return an argument decides, or that is polar."""
    return {
        owner: method
        for owner, method in _public_plot_methods().items()
        if _decided(method)
    }


def _decided_helpers() -> dict[str, Callable[..., object]]:
    """Every public ``plot_`` helper whose return an argument decides."""
    return {
        name: helper
        for name, helper in _public_plot_helpers().items()
        if _decided(helper)
    }


def _literal_values(annotation: object, module: str) -> tuple[str, ...] | None:
    """The options of a ``Literal`` annotation, or of an alias the module defines."""
    if not isinstance(annotation, str):
        return None
    node = ast.parse(annotation, mode="eval").body
    if isinstance(node, ast.Name):
        alias = getattr(sys.modules[module], node.id, None)
        if typing.get_origin(alias) is typing.Literal:
            return tuple(str(value) for value in typing.get_args(alias))
        return None
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Literal"
    ):
        items = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        return tuple(str(ast.literal_eval(item)) for item in items)
    return None


def _calls(head: Callable[..., object]) -> list[tuple[dict[str, object], str | None]]:
    """Every call a head admits: each axes it takes, and each option of its choices.

    The second item names the axes handed in (``"polar"`` or ``"cartesian"``),
    or is ``None`` when the head takes none and the plot makes its own.
    """
    parameters = inspect.signature(head).parameters
    axes = str(parameters["ax"].annotation)
    handed: list[str | None] = []
    if "None" in axes:
        handed.append(None)
    if "PolarAxes" in axes:
        handed.append("polar")
    elif "Axes" in axes:
        handed.append("cartesian")
    choices = [
        [(name, value) for value in values]
        for name, parameter in parameters.items()
        if (values := _literal_values(parameter.annotation, head.__module__))
        and name != "language"
    ]
    return [
        (dict(picked), projection)
        for projection in handed
        for picked in itertools.product(*choices)
    ]


def _fresh_axes(projection: str) -> Axes:
    _fig, ax = plt.subplots(
        subplot_kw={"projection": "polar"} if projection == "polar" else None
    )
    return ax


def _check_return(out: object, promised: str, given: Axes | None, where: str) -> None:
    """``out`` is what the head's return annotation ``promised`` says it is."""
    from matplotlib.axes import Axes as MplAxes

    if promised.startswith(_A_COLUMN):
        panels = promised.count("Axes")
        assert given is None, f"{where}: a column of axes for a given axes"
        assert isinstance(out, tuple), f"{where}: {type(out).__name__}, not a tuple"
        assert len(out) == panels, f"{where}: {len(out)} axes, not {panels}"
        assert all(isinstance(ax, MplAxes) for ax in out), where
        assert len({id(ax) for ax in out}) == panels, f"{where}: an axes twice"
        return
    if promised == "Axes | tuple[Axes, Axes]":
        if isinstance(out, tuple):
            assert given is None, f"{where}: a column of axes for a given axes"
            assert len(out) == 2, where
            return
        assert isinstance(out, MplAxes), where
    else:
        assert promised in {"Axes", "PolarAxes"}, f"{where}: unread {promised!r}"
        assert isinstance(out, MplAxes), f"{where}: {type(out).__name__}, not Axes"
        polar = out.name == "polar"
        assert polar == (promised == "PolarAxes"), (
            f"{where}: {out.name} axes where the head promises {promised}"
        )
    if given is not None:
        assert out is given, f"{where}: not the axes it was handed"


def _honours_its_heads(
    draw: Callable[..., object], function: Callable[..., object], name: str
) -> None:
    """Every head of ``function`` holds for every call it admits on ``draw``."""
    heads = typing.get_overloads(function) or [function]
    for head in heads:
        promised = _promised(head)
        for keywords, projection in _calls(head):
            given = None if projection is None else _fresh_axes(projection)
            arguments = dict(keywords) if given is None else {**keywords, "ax": given}
            out = draw(**arguments)
            _check_return(out, promised, given, f"{name}({arguments})")
            plt.close("all")


def _choices_covered(function: Callable[..., object], name: str) -> None:
    """Each option of a choice the heads split is taken by exactly one head.

    A choice every head takes whole (``kind`` of the excitation plot) is no
    split; one the heads divide (``view``, ``quantity``) has to be divided
    without a gap and without an option two heads claim.
    """
    heads = typing.get_overloads(function)
    for parameter, spelled in inspect.signature(function).parameters.items():
        options = _literal_values(spelled.annotation, function.__module__)
        if parameter == "language" or options is None:
            continue
        per_head = [
            _literal_values(
                inspect.signature(head).parameters[parameter].annotation,
                head.__module__,
            )
            or ()
            for head in heads
        ]
        if all(sorted(taken) == sorted(options) for taken in per_head):
            continue
        taken = sorted(value for values in per_head for value in values)
        if taken != sorted(options):
            msg = f"{name}: the heads take {taken} of {parameter} {sorted(options)}"
            raise AssertionError(msg)


def test_every_decided_plot_has_a_built_result() -> None:
    """A new plot whose return an argument decides gets a result here, or fails.

    The contract below can only hold a plot to its signature when it has a
    result to draw, so the table of results and the plots the walk finds are
    the same set.
    """
    assert set(_decided_methods()) == set(_DECIDED_PLOT_RESULTS)
    assert set(_decided_helpers()) == set(_DECIDED_PLOT_HELPERS)


@pytest.mark.parametrize("owner", sorted(_DECIDED_PLOT_RESULTS))
def test_a_plot_returns_what_its_signature_promises(owner: str) -> None:
    """Without ``ax`` a column of axes, with one that axes, polar where promised.

    A multi-panel ``.plot()`` returned an ndarray of axes without ``ax`` and
    the axes it was given with one, and its annotation said only "one or the
    other", so a typed caller narrowed a value the call had already decided.
    Each overload head now says which, and this calls every head as it is
    written: with no axes, with an axes of the projection it takes, and with
    each option of a ``view`` or ``quantity`` it splits on. The runtime value
    has to be what that head returns: a tuple of exactly its axes, the very
    axes it was handed, or a polar axes exactly where it says ``PolarAxes``.
    """
    method = _decided_methods()[owner]
    result = _DECIDED_PLOT_RESULTS[owner]()
    _choices_covered(method, owner)
    _honours_its_heads(result.plot, method, owner)


@pytest.mark.parametrize("name", sorted(_DECIDED_PLOT_HELPERS))
def test_a_plot_helper_returns_what_its_signature_promises(name: str) -> None:
    helper = _decided_helpers()[name]
    _choices_covered(helper, name)
    _honours_its_heads(_DECIDED_PLOT_HELPERS[name], helper, name)


@pytest.mark.parametrize(
    ("owner", "keywords"),
    [
        ("phonometry.electroacoustics.piston.PistonDirectivity", {}),
        ("phonometry.materials.diffusers.design.DiffuserPolarResponse", {}),
        ("phonometry.vibration.machinery.evaluation.VectorChangeResult", {}),
        ("phonometry.metrology.random_incidence.DirectivityFactor", {}),
        (
            "phonometry.electroacoustics.loudspeaker.LoudspeakerCharacteristics",
            {"quantity": "directivity"},
        ),
        (
            "phonometry.electroacoustics.microphone.MicrophoneCharacteristics",
            {"quantity": "directivity"},
        ),
    ],
)
def test_a_plot_that_draws_on_a_polar_axes_refuses_a_cartesian_one(
    owner: str, keywords: dict[str, str]
) -> None:
    """The heads say PolarAxes for these; a cartesian axes is refused by name.

    The predicted diffuser response took any axes and failed on the first
    polar setter with an ``AttributeError``; it now refuses as the other polar
    plots do, before it draws.
    """
    result = _DECIDED_PLOT_RESULTS[owner]()
    _fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="'ax' must be a polar axes"):
        result.plot(ax, **keywords)
    plt.close("all")


def test_the_diffusion_fiche_refuses_a_cartesian_axes() -> None:
    from phonometry._plot.materials import plot_diffusion_polar_report

    result = _diffusion()
    _fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="'ax' must be a polar axes"):
        plot_diffusion_polar_report(result, ax)  # type: ignore[arg-type]
    plt.close("all")
