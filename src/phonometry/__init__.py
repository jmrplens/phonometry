#  Copyright (c) 2020. Jose M. Requena-Plens
"""
Octave-Band and Fractional Octave-Band filter for signals in the time domain.
Implementation according to ANSI s1.11-2004 and IEC 61260-1-2014.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple, overload, Literal

import numpy as np

from .calibration import CalibrationWarning, calculate_sensitivity
from .environmental import composite_rating_level, lden, ldn
from .compliance import verify_filter_class
from .core import OctaveFilterBank
from .frequencies import getansifrequencies, normalizedfreq
from .intensity import (
    FieldIndicators,
    IntensityResult,
    dynamic_capability_index,
    field_indicators,
    sound_intensity,
)
from .levels import laeq, lc_peak, leq, lex_8h, ln_levels, sel, sound_exposure
from .loudness import ZwickerLoudness, loudness_zwicker, loudness_zwicker_from_spectrum
from .loudness_ecma import EcmaLoudness, loudness_ecma
from .loudness_moore_glasberg import (
    MooreGlasbergLoudness,
    loudness_moore_glasberg,
    loudness_moore_glasberg_from_spectrum,
    loudness_moore_glasberg_from_third_octave,
)
from .loudness_moore_glasberg_time import (
    MooreGlasbergTimeVaryingLoudness,
    loudness_moore_glasberg_time,
)
from .loudness_contours import equal_loudness_contour, hearing_threshold, loudness_level
from .sharpness import sharpness_din, sharpness_din_from_specific
from .sti import STIResult, sti_from_impulse_response, stipa, stipa_signal
from .tonality_ecma import EcmaTonality, tonality_ecma
from .roughness_ecma import EcmaRoughness, roughness_ecma
from .tonality import ToneAssessment, prominence_ratio, tone_to_noise_ratio
from .parametric_filters import (
    TimeWeighting,
    WeightingFilter,
    linkwitz_riley,
    time_weighting,
    weighting_filter,
)
from .insulation import (
    AirborneInsulationResult,
    FacadeInsulationResult,
    ImpactInsulationResult,
    ImpactRatingResult,
    WeightedRatingResult,
    airborne_insulation,
    energy_average_level,
    facade_insulation,
    impact_insulation,
    weighted_impact_rating,
    weighted_rating,
)
from .lab_insulation import (
    LabAirborneInsulationResult,
    LabImpactInsulationResult,
    LabInsulationWarning,
    background_correction,
    lab_airborne_insulation,
    lab_impact_insulation,
)
from .open_plan import OpenPlanResult, open_plan_metrics
from .sound_power import (
    MeteorologicalCorrection,
    PrecisionCriteria,
    PrecisionFieldIndicators,
    PrecisionIntensityResult,
    PrecisionSoundPowerResult,
    SoundPowerResult,
    SoundPowerWarning,
    background_noise_correction,
    environmental_correction,
    measurement_positions,
    meteorological_corrections,
    precision_background_correction,
    precision_field_indicators,
    precision_positions,
    precision_qualification,
    precision_uncertainty,
    sound_power_anechoic,
    sound_power_intensity_precision,
    sound_power_pressure,
)
from .sound_power_reverberation import (
    ReverberationSoundPowerResult,
    sound_power_comparison,
    sound_power_reverberation,
)
from .sound_power_intensity import (
    SoundPowerIntensityResult,
    sound_power_intensity,
)
from .scattering_diffusion import (
    BASE_PLATE_BANDS_HZ,
    BASE_PLATE_MAX_SCATTERING,
    TWO_DIMENSIONAL_SOURCE_WEIGHTS,
    DiffusionResult,
    ScatteringDiffusionWarning,
    ScatteringResult,
    ScatteringUncertainty,
    absorption_coefficient_uncertainty,
    air_attenuation_coefficient,
    area_factors,
    base_plate_scattering,
    check_base_plate_scattering,
    directional_diffusion,
    directional_diffusion_coefficient,
    normalized_diffusion_coefficient,
    random_incidence_absorption,
    random_incidence_diffusion,
    reverberation_time_uncertainty,
    scattering_coefficient,
    scattering_coefficient_spectrum,
    scattering_coefficient_uncertainty,
    specular_absorption_coefficient,
    speed_of_sound,
)
from .road_absorption import (
    DEFAULT_MIC_HEIGHT,
    DEFAULT_SOURCE_HEIGHT,
    DEFAULT_SPEED_OF_SOUND,
    PART1_FREQUENCY_RANGE,
    SPOT_FREQUENCY_RANGE,
    SPOT_NARROW_BAND_RANGE,
    InsituAbsorptionResult,
    RoadAbsorptionWarning,
    absorption_reference_corrected,
    adrienne_window,
    check_spot_frequency_range,
    geometric_spreading_factor,
    geometric_spreading_factor_angle,
    insitu_absorption_coefficient,
    insitu_absorption_from_reflection,
    insitu_absorption_spectrum,
    insitu_reflection_factor,
    max_sampled_area_radius,
    msa_major_axis,
    one_third_octave_absorption,
    power_reflection_coefficient,
    reflected_path_delay,
    spot_internal_loss_correction,
    spot_microphone_spacing_bounds,
    spot_tube_upper_frequency,
)
from .human_vibration import (
    HAV_EAV_A8,
    HAV_ELV_A8,
    REFERENCE_ACCELERATION,
    REFERENCE_DURATION_S,
    WBV_EAV_A8,
    WBV_EAV_VDV,
    WBV_ELV_A8,
    WBV_ELV_VDV,
    WEIGHTING_NAMES,
    DailyVibrationExposure,
    ExposureAssessment,
    HumanVibrationWarning,
    WeightedSpectrum,
    WeightingResponse,
    apply_weighting,
    combine_partial_exposures,
    crest_factor,
    daily_exposure,
    daily_vibration_exposure,
    energy_equivalent_acceleration,
    exposure_assessment,
    frequency_weighting,
    hav_daily_exposure,
    hav_vwf_lifetime_years,
    motion_sickness_dose_value,
    mtvv,
    partial_exposure,
    running_rms,
    vibration_dose_value,
    vibration_total_value,
    weighted_acceleration,
    weighting_factors,
)
from .room_acoustics import (
    DecayCurve,
    RoomAcousticsResult,
    decay_curve,
    room_parameters,
)
from .sound_absorption import (
    AbsorptionWarning,
    absorption_area,
    absorption_coefficient,
    attenuation_from_alpha,
)
from .air_absorption import (
    AtmosphericAbsorptionWarning,
    air_attenuation,
    air_attenuation_m,
)
from .impedance_tube import (
    ImpedanceTubeResult,
    ImpedanceTubeWarning,
    TransferMatrix,
    absorption_from_reflection,
    air_density_astm,
    air_density_iso,
    air_layer_transfer_matrix,
    apply_mic_calibration,
    characteristic_impedance,
    face_quantities,
    mic_calibration_factor,
    normalized_surface_admittance,
    normalized_surface_impedance,
    plane_wave_frequency_range,
    reflection_factor,
    speed_of_sound_astm,
    speed_of_sound_iso,
    standing_wave_absorption,
    standing_wave_normalized_impedance,
    standing_wave_ratio_from_level,
    standing_wave_reflection,
    standing_wave_reflection_magnitude,
    surface_impedance,
    transfer_matrix_one_load,
    transfer_matrix_two_load,
    tube_attenuation_constant,
    tube_wavenumber,
    two_microphone_impedance,
    wave_decomposition,
)
from .airflow_resistance import (
    AirflowResistanceWarning,
    StaticAirflowResult,
    airflow_resistance,
    airflow_resistivity,
    alternating_airflow_resistance,
    effective_kappa,
    linear_airflow_velocity,
    piston_volume_flow_rate,
    specific_airflow_resistance,
    static_airflow_resistance,
    thermal_boundary_layer_thickness,
)
from .absorption_rating import (
    AbsorptionRatingResult,
    OCTAVE_BANDS_HZ,
    REFERENCE_CURVE,
    THIRD_OCTAVE_BANDS_HZ,
    absorption_class,
    practical_absorption_coefficient,
    weighted_absorption,
)
from .outdoor_propagation import (
    DEFAULT_FREQUENCIES,
    Barrier,
    OutdoorAttenuation,
    atmospheric_absorption,
    barrier_attenuation,
    directivity_omega,
    geometric_divergence,
    ground_attenuation,
    ground_attenuation_alternative,
    meteorological_correction,
    outdoor_propagation_attenuation,
    predicted_receiver_level,
)
from .room_ir import (
    impulse_response,
    inverse_filter,
    mls_impulse_response,
    mls_signal,
    sweep_signal,
)
from .building_prediction import (
    AirbornePredictionResult,
    FlankingPath,
    ImpactPredictionResult,
    PathContribution,
    combine_linings,
    equivalent_impact_level,
    flanking_element,
    flanking_path,
    impact_flanking_correction,
    junction_min_vibration_reduction,
    junction_vibration_reduction,
    predicted_airborne_insulation,
    predicted_impact_insulation,
    standardized_impact_level,
)
from .building_uncertainty import (
    COVERAGE_FACTORS,
    BandUncertainty,
    UncertainValue,
    band_uncertainty,
    combine_uncertainties,
    coverage_factor,
    expanded_uncertainty,
    maximum_repeatability_standard_deviation,
    prediction_input_uncertainty,
    reduce_by_independent_measurements,
    satisfies_lower_requirement,
    satisfies_upper_requirement,
    single_number_uncertainty,
    single_number_uncertainty_uncorrelated,
    uncertain_value,
)
from .occupational_exposure import (
    COVERAGE_FACTOR,
    INSTRUMENT_U2,
    ExposureResult,
    ExposureWarning,
    Task,
    TaskContribution,
    full_day_exposure,
    job_based_exposure,
    minimum_cumulative_duration_hours,
    table_c4_contribution,
    task_based_exposure,
)
from ._version import __version__

# Public methods
__all__ = [
    "__version__",
    "octavefilter",
    "getansifrequencies",
    "normalizedfreq",
    "OctaveFilterBank",
    "WeightingFilter",
    "weighting_filter",
    "time_weighting",
    "TimeWeighting",
    "linkwitz_riley",
    "calculate_sensitivity",
    "leq",
    "laeq",
    "ln_levels",
    "lc_peak",
    "sel",
    "sound_exposure",
    "lex_8h",
    "loudness_zwicker",
    "loudness_zwicker_from_spectrum",
    "ZwickerLoudness",
    "loudness_ecma",
    "EcmaLoudness",
    "loudness_moore_glasberg",
    "loudness_moore_glasberg_from_spectrum",
    "loudness_moore_glasberg_from_third_octave",
    "MooreGlasbergLoudness",
    "loudness_moore_glasberg_time",
    "MooreGlasbergTimeVaryingLoudness",
    "tonality_ecma",
    "EcmaTonality",
    "roughness_ecma",
    "EcmaRoughness",
    "sharpness_din",
    "sharpness_din_from_specific",
    "equal_loudness_contour",
    "loudness_level",
    "hearing_threshold",
    "tone_to_noise_ratio",
    "prominence_ratio",
    "ToneAssessment",
    "sound_intensity",
    "IntensityResult",
    "field_indicators",
    "FieldIndicators",
    "dynamic_capability_index",
    "sti_from_impulse_response",
    "stipa",
    "stipa_signal",
    "STIResult",
    "sweep_signal",
    "inverse_filter",
    "impulse_response",
    "mls_signal",
    "mls_impulse_response",
    "room_parameters",
    "decay_curve",
    "DecayCurve",
    "RoomAcousticsResult",
    "absorption_area",
    "absorption_coefficient",
    "attenuation_from_alpha",
    "AbsorptionWarning",
    "air_attenuation",
    "air_attenuation_m",
    "AtmosphericAbsorptionWarning",
    # Impedance tube (ISO 10534-1/-2, ASTM E2611)
    "ImpedanceTubeResult",
    "ImpedanceTubeWarning",
    "TransferMatrix",
    "absorption_from_reflection",
    "air_density_astm",
    "air_density_iso",
    "air_layer_transfer_matrix",
    "apply_mic_calibration",
    "characteristic_impedance",
    "face_quantities",
    "mic_calibration_factor",
    "normalized_surface_admittance",
    "normalized_surface_impedance",
    "plane_wave_frequency_range",
    "reflection_factor",
    "speed_of_sound_astm",
    "speed_of_sound_iso",
    "standing_wave_absorption",
    "standing_wave_normalized_impedance",
    "standing_wave_ratio_from_level",
    "standing_wave_reflection",
    "standing_wave_reflection_magnitude",
    "surface_impedance",
    "transfer_matrix_one_load",
    "transfer_matrix_two_load",
    "tube_attenuation_constant",
    "tube_wavenumber",
    "two_microphone_impedance",
    "wave_decomposition",
    # Airflow resistance (ISO 9053-1/-2)
    "AirflowResistanceWarning",
    "StaticAirflowResult",
    "airflow_resistance",
    "airflow_resistivity",
    "alternating_airflow_resistance",
    "effective_kappa",
    "linear_airflow_velocity",
    "piston_volume_flow_rate",
    "specific_airflow_resistance",
    "static_airflow_resistance",
    "thermal_boundary_layer_thickness",
    # Absorption rating (ISO 11654)
    "AbsorptionRatingResult",
    "OCTAVE_BANDS_HZ",
    "REFERENCE_CURVE",
    "THIRD_OCTAVE_BANDS_HZ",
    "absorption_class",
    "practical_absorption_coefficient",
    "weighted_absorption",
    "DEFAULT_FREQUENCIES",
    "Barrier",
    "OutdoorAttenuation",
    "atmospheric_absorption",
    "barrier_attenuation",
    "directivity_omega",
    "geometric_divergence",
    "ground_attenuation",
    "ground_attenuation_alternative",
    "meteorological_correction",
    "outdoor_propagation_attenuation",
    "predicted_receiver_level",
    "open_plan_metrics",
    "OpenPlanResult",
    "sound_power_pressure",
    "measurement_positions",
    "background_noise_correction",
    "environmental_correction",
    "SoundPowerResult",
    "SoundPowerWarning",
    "sound_power_reverberation",
    "sound_power_comparison",
    "ReverberationSoundPowerResult",
    "sound_power_intensity",
    "SoundPowerIntensityResult",
    # ISO 3745 / ISO 9614-3 precision sound power
    "sound_power_anechoic",
    "PrecisionSoundPowerResult",
    "precision_positions",
    "precision_background_correction",
    "meteorological_corrections",
    "MeteorologicalCorrection",
    "precision_uncertainty",
    "sound_power_intensity_precision",
    "PrecisionIntensityResult",
    "precision_field_indicators",
    "PrecisionFieldIndicators",
    "precision_qualification",
    "PrecisionCriteria",
    # ISO 17497-1/-2 scattering & diffusion
    "speed_of_sound",
    "air_attenuation_coefficient",
    "random_incidence_absorption",
    "specular_absorption_coefficient",
    "scattering_coefficient",
    "scattering_coefficient_spectrum",
    "ScatteringResult",
    "base_plate_scattering",
    "BASE_PLATE_BANDS_HZ",
    "BASE_PLATE_MAX_SCATTERING",
    "check_base_plate_scattering",
    "reverberation_time_uncertainty",
    "absorption_coefficient_uncertainty",
    "scattering_coefficient_uncertainty",
    "ScatteringUncertainty",
    "directional_diffusion",
    "directional_diffusion_coefficient",
    "DiffusionResult",
    "normalized_diffusion_coefficient",
    "area_factors",
    "random_incidence_diffusion",
    "TWO_DIMENSIONAL_SOURCE_WEIGHTS",
    "ScatteringDiffusionWarning",
    # ISO 13472-1/-2 in-situ road-surface absorption
    "adrienne_window",
    "geometric_spreading_factor",
    "geometric_spreading_factor_angle",
    "reflected_path_delay",
    "insitu_reflection_factor",
    "insitu_absorption_from_reflection",
    "power_reflection_coefficient",
    "insitu_absorption_coefficient",
    "insitu_absorption_spectrum",
    "InsituAbsorptionResult",
    "absorption_reference_corrected",
    "one_third_octave_absorption",
    "max_sampled_area_radius",
    "msa_major_axis",
    "spot_tube_upper_frequency",
    "spot_microphone_spacing_bounds",
    "check_spot_frequency_range",
    "spot_internal_loss_correction",
    "DEFAULT_SOURCE_HEIGHT",
    "DEFAULT_MIC_HEIGHT",
    "DEFAULT_SPEED_OF_SOUND",
    "PART1_FREQUENCY_RANGE",
    "SPOT_FREQUENCY_RANGE",
    "SPOT_NARROW_BAND_RANGE",
    "RoadAbsorptionWarning",
    # ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC human vibration
    "frequency_weighting",
    "weighting_factors",
    "apply_weighting",
    "WeightingResponse",
    "WEIGHTING_NAMES",
    "weighted_acceleration",
    "WeightedSpectrum",
    "running_rms",
    "mtvv",
    "vibration_dose_value",
    "motion_sickness_dose_value",
    "crest_factor",
    "vibration_total_value",
    "daily_exposure",
    "partial_exposure",
    "combine_partial_exposures",
    "hav_daily_exposure",
    "energy_equivalent_acceleration",
    "hav_vwf_lifetime_years",
    "exposure_assessment",
    "ExposureAssessment",
    "daily_vibration_exposure",
    "DailyVibrationExposure",
    "HumanVibrationWarning",
    "REFERENCE_ACCELERATION",
    "REFERENCE_DURATION_S",
    "HAV_EAV_A8",
    "HAV_ELV_A8",
    "WBV_EAV_A8",
    "WBV_ELV_A8",
    "WBV_EAV_VDV",
    "WBV_ELV_VDV",
    "airborne_insulation",
    "AirborneInsulationResult",
    "impact_insulation",
    "ImpactInsulationResult",
    "weighted_rating",
    "WeightedRatingResult",
    "weighted_impact_rating",
    "ImpactRatingResult",
    "facade_insulation",
    "FacadeInsulationResult",
    "energy_average_level",
    "lab_airborne_insulation",
    "LabAirborneInsulationResult",
    "lab_impact_insulation",
    "LabImpactInsulationResult",
    "background_correction",
    "LabInsulationWarning",
    "lden",
    "ldn",
    "composite_rating_level",
    "CalibrationWarning",
    "verify_filter_class",
    "predicted_airborne_insulation",
    "AirbornePredictionResult",
    "predicted_impact_insulation",
    "ImpactPredictionResult",
    "junction_vibration_reduction",
    "junction_min_vibration_reduction",
    "flanking_path",
    "flanking_element",
    "FlankingPath",
    "PathContribution",
    "combine_linings",
    "equivalent_impact_level",
    "impact_flanking_correction",
    "standardized_impact_level",
    "band_uncertainty",
    "single_number_uncertainty",
    "single_number_uncertainty_uncorrelated",
    "maximum_repeatability_standard_deviation",
    "coverage_factor",
    "expanded_uncertainty",
    "uncertain_value",
    "combine_uncertainties",
    "prediction_input_uncertainty",
    "reduce_by_independent_measurements",
    "satisfies_lower_requirement",
    "satisfies_upper_requirement",
    "BandUncertainty",
    "UncertainValue",
    "COVERAGE_FACTORS",
    "task_based_exposure",
    "job_based_exposure",
    "full_day_exposure",
    "minimum_cumulative_duration_hours",
    "table_c4_contribution",
    "Task",
    "TaskContribution",
    "ExposureResult",
    "ExposureWarning",
    "COVERAGE_FACTOR",
    "INSTRUMENT_U2",
]


@lru_cache(maxsize=32)
def _cached_filter_bank(
    fs: int,
    fraction: float,
    order: int,
    limits: Tuple[float, ...] | None,
    filter_type: str,
    ripple: float,
    attenuation: float,
    calibration_factor: float,
    dbfs: bool,
) -> OctaveFilterBank:
    """Design (or reuse) a stateless filter bank for octavefilter()."""
    return OctaveFilterBank(
        fs=fs,
        fraction=fraction,
        order=order,
        limits=list(limits) if limits is not None else None,
        filter_type=filter_type,
        ripple=ripple,
        attenuation=attenuation,
        calibration_factor=calibration_factor,
        dbfs=dbfs,
    )


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[False] = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[False] = False,
) -> Tuple[np.ndarray, List[float]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[True] = True,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[False] = False,
) -> Tuple[np.ndarray, List[float], List[np.ndarray]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[False] = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[True] = ...,
) -> Tuple[np.ndarray, List[str]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[True] = True,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[True] = ...,
) -> Tuple[np.ndarray, List[str], List[np.ndarray]]: ...


def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: bool = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: bool = False,
) -> Tuple[np.ndarray, List[float]] | Tuple[np.ndarray, List[str]] | Tuple[np.ndarray, List[float], List[np.ndarray]] | Tuple[np.ndarray, List[str], List[np.ndarray]]:
    """
    Filter a signal with octave or fractional octave filter bank.

    This method uses a filter bank with Second-Order Sections (SOS) coefficients.
    To obtain the correct coefficients, automatic subsampling is applied to the
    signal in each filtered band.

    Multichannel support: If x is 2D (channels, samples), each channel is filtered.

    :param x: Input signal (1D array or 2D array [channels, samples]).
    :type x: Union[List[float], np.ndarray]
    :param fs: Sample rate in Hz.
    :type fs: int
    :param fraction: Bandwidth 'b'. Examples: 1/3-octave b=3, 1-octave b=1, 2/3-octave b=1.5. Default: 1.
    :type fraction: float
    :param order: Order of the filter. Default: 6.
    :type order: int
    :param limits: Minimum and maximum limit frequencies [f_min, f_max]. Default [12, 20000].
    :type limits: Optional[List[float]]
    :param show: If True, plot and show the filter response.
    :type show: bool
    :param sigbands: If True, also return the signal in the time domain divided into bands.
    :type sigbands: bool
    :param plot_file: Path to save the filter response plot.
    :type plot_file: Optional[str]
    :param detrend: If True, remove DC offset before filtering. Default: True.
    :type detrend: bool
    :param filter_type: Type of filter ('butter', 'cheby1', 'cheby2', 'ellip', 'bessel').
        Default: 'butter' (the only type that meets IEC 61260-1 class 1 with the
        default parameters).
    :param ripple: Passband ripple in dB (for cheby1, ellip). Default: 0.1.
    :param attenuation: Stopband attenuation in dB (for cheby2, ellip). Default: 72.0.
        For ``cheby2`` scipy pins the deep-stopband floor at exactly this value,
        so it must be >= 70 dB to clear the IEC 61260-1 class 1 limit (matches
        :class:`OctaveFilterBank`).
    :param calibration_factor: Calibration factor for SPL calculation. Default: 1.0.
    :param dbfs: If True, return results in dBFS. Default: False.
    :param mode: 'rms' or 'peak'. Default: 'rms'.
    :param nominal: If True, return IEC 61260-1 nominal frequency labels (List[str]) instead of exact floats.
    :return: A tuple containing (SPL_array, Frequencies_list) or (SPL_array, Frequencies_list, signals).
        When *nominal=True*, the frequency list contains ``List[str]`` labels instead of floats.
    :rtype: Union[Tuple[np.ndarray, List[float]], Tuple[np.ndarray, List[str]],
        Tuple[np.ndarray, List[float], List[np.ndarray]],
        Tuple[np.ndarray, List[str], List[np.ndarray]]]
    """
    
    if show or plot_file:
        # Plotting has side effects: bypass the cache.
        filter_bank = OctaveFilterBank(
            fs=fs,
            fraction=fraction,
            order=order,
            limits=limits,
            filter_type=filter_type,
            ripple=ripple,
            attenuation=attenuation,
            show=show,
            plot_file=plot_file,
            calibration_factor=calibration_factor,
            dbfs=dbfs,
        )
    else:
        # The bank is immutable in non-stateful mode: reuse the design.
        # Pass limits through as-is (tuple for hashability); the bank
        # constructor is the single place that validates them and owns
        # the default when None.
        limits_key = tuple(map(float, limits)) if limits is not None else None
        filter_bank = _cached_filter_bank(
            fs, fraction, order, limits_key, filter_type,
            ripple, attenuation, calibration_factor, dbfs,
        )

    return filter_bank.filter(x, sigbands=sigbands, mode=mode, detrend=detrend, nominal=nominal)  # type: ignore[call-overload,no-any-return]
