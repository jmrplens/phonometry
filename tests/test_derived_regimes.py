#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A result reads its regime from the values it holds.

Each result here used to store the regime or the classification its function
reached beside the values it was reached from: the over-critical hammer of
Hopkins Eq. (3.95), the turbulent or cavitating valve of IEC 60534-8-4 5.1,
the five regimes of IEC 60534-8-3 5.2, the screened section of the NORAH2
guidance, the peaks and the kept reversals of ISO 8253-1, the interpolated
rows of IEC 61094-2 Table C.3, the prime of ISO 11957, the identified tone of
IEC 61400-11, the correction of ISO 10140-1 J.1, the background rule of
IEC TS 61400-11-2, Weston's regimes and the fractional-delay alignment of a
synchronous average. Each is now a read-only property: none can be handed to
the constructor, and a result built by hand reads it from its own values. The
numbers a regime selects are held to it, so a result built by hand cannot
carry one regime beside the values of another. ISO 10848 is the odd one: its
band set stays a field, a statement the caller makes, which
:func:`~phonometry.building.vibration_reduction_index` no longer fills.
"""

from __future__ import annotations

import dataclasses
import math
import warnings

import numpy as np
import pytest

from phonometry import (
    aircraft,
    building,
    environment,
    hearing,
    materials,
    metrology,
    noise_control,
    signals,
    underwater,
)

_BANDS = np.array([100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0])


# --- Hopkins Eq. (3.95): over-critical when K m >= 4 Zdp^2 ----------------------


def _tapping(stiffness: float, impedance: float) -> building.TappingForceResult:
    return building.tapping_force_spectrum(_BANDS, stiffness, impedance, mass=0.5)


def test_the_hammer_regime_is_no_constructor_field() -> None:
    fields = dataclasses.asdict(_tapping(1.0e6, 3.0e4))
    with pytest.raises(TypeError, match="over_critical"):
        building.TappingForceResult(**fields, over_critical=True)


def test_critical_damping_itself_is_over_critical() -> None:
    # K m = 4 Zdp^2 exactly: 8e6 x 0,5 = 4 x 1000^2. Hopkins prints the
    # over-critical case with >=, so the boundary is no rebound.
    assert _tapping(8.0e6, 1000.0).over_critical is True
    assert _tapping(8.0e6, 1000.001).over_critical is False


def test_the_hammer_regime_is_read_from_k_zdp_and_m() -> None:
    assert _tapping(1.0e6, 3.0e4).over_critical is False
    assert _tapping(1.0e6, 100.0).over_critical is True
    heavy = building.tapping_force_spectrum(_BANDS, 1.0e6, 3.0e4, mass=1.0e4)
    assert heavy.over_critical is True
    assert dataclasses.replace(heavy).over_critical is True


def test_a_tapping_result_cannot_keep_the_cut_off_of_another_regime() -> None:
    # Eq. (3.102) gives 225 Hz under-critical; at Zdp = 100 the regime is
    # over-critical, where Eq. (3.101) gives 32,5 Hz.
    soft = _tapping(1.0e6, 3.0e4)
    with pytest.raises(ValueError, match="cut_off_frequency"):
        dataclasses.replace(soft, impedance=100.0)


def test_a_tapping_result_cannot_keep_the_spectrum_of_another_regime() -> None:
    soft = _tapping(1.0e6, 3.0e4)
    hard = _tapping(1.0e6, 100.0)
    with pytest.raises(ValueError, match="peak_force"):
        dataclasses.replace(soft, peak_force=hard.peak_force)


def test_a_tapping_power_input_is_the_mean_square_force_over_zdp() -> None:
    soft = _tapping(1.0e6, 3.0e4)
    doubled = np.asarray(soft.power_input) * 2.0
    with pytest.raises(ValueError, match="power_input"):
        dataclasses.replace(soft, power_input=doubled)


def test_a_tapping_result_needs_a_positive_hammer_mass() -> None:
    soft = _tapping(1.0e6, 3.0e4)
    with pytest.raises(ValueError, match="mass_kg"):
        dataclasses.replace(soft, mass_kg=0.0)


# --- IEC 60534-8-4 5.1: cavitating when dp exceeds x_Fzp1 (p1 - pv) --------------


def _liquid(outlet_pressure_pa: float) -> noise_control.HydrodynamicValveNoise:
    return noise_control.valve_hydrodynamic_noise(
        noise_control.LiquidStream(
            mass_flow=30.0,
            inlet_pressure_pa=10.0e5,
            outlet_pressure_pa=outlet_pressure_pa,
            vapour_pressure_pa=0.0317e5,
            density=997.0,
            speed_of_sound=1400.0,
        ),
        noise_control.LiquidTrim(
            flow_coefficient=90.0,
            style_modifier=0.42,
            pressure_recovery=0.92,
            incipient_ratio=0.25,
            power_ratio=0.25,
            valve_diameter_m=0.1,
            seat_diameter_m=0.08,
        ),
        noise_control.LiquidPipe(
            internal_diameter_m=0.1071, wall_thickness=0.0036, density=7800.0
        ),
    )


def _at_differential(
    point: noise_control.HydrodynamicValveNoise, differential: float
) -> dict[str, float]:
    """The differential and the x_F of Equation (1) that goes with it."""
    span = point.inlet_pressure_pa - point.vapour_pressure_pa
    return {"differential": differential, "pressure_ratio": differential / span}


def test_the_valve_regime_follows_its_pressures() -> None:
    assert _liquid(8.5e5).regime == "turbulent"
    assert _liquid(6.5e5).regime == "cavitating"


def test_a_differential_on_the_threshold_is_turbulent() -> None:
    # 5.1 prints "lower than" for turbulent and "exceeds" for cavitating; on
    # the threshold Equation (9) gives nought, so the point is turbulent.
    turbulent = _liquid(8.5e5)
    threshold = turbulent.corrected_ratio * (
        turbulent.inlet_pressure_pa - turbulent.vapour_pressure_pa
    )
    on_it = dataclasses.replace(turbulent, **_at_differential(turbulent, threshold))
    assert on_it.regime == "turbulent"


def test_a_turbulent_point_cannot_carry_cavitation_fields() -> None:
    turbulent = _liquid(8.5e5)
    with pytest.raises(ValueError, match="cavitation_efficiency"):
        dataclasses.replace(turbulent, cavitation_efficiency=1.0e-6)


def test_a_turbulent_point_cannot_carry_a_cavitation_transmission_loss() -> None:
    turbulent = _liquid(8.5e5)
    with pytest.raises(ValueError, match="cavitation_transmission_loss"):
        dataclasses.replace(turbulent, cavitation_transmission_loss=1.0)


def test_a_point_past_the_threshold_needs_its_cavitation_fields() -> None:
    turbulent = _liquid(8.5e5)
    threshold = turbulent.corrected_ratio * (
        turbulent.inlet_pressure_pa - turbulent.vapour_pressure_pa
    )
    past = _at_differential(turbulent, math.nextafter(threshold, math.inf))
    with pytest.raises(ValueError, match="cavitation_efficiency"):
        dataclasses.replace(turbulent, **past)


def test_a_valve_result_needs_the_liquid_below_its_inlet_pressure() -> None:
    turbulent = _liquid(8.5e5)
    with pytest.raises(ValueError, match="vapour_pressure_pa"):
        dataclasses.replace(turbulent, vapour_pressure_pa=11.0e5)


def test_the_pressure_ratio_is_equation_1_of_the_pressures() -> None:
    # x_F = 0,9 is past x_Fzp1 = 0,2345 while the pressures say 0,15.
    turbulent = _liquid(8.5e5)
    with pytest.raises(ValueError, match="pressure_ratio"):
        dataclasses.replace(turbulent, pressure_ratio=0.9)


def test_the_corrected_threshold_is_equation_3c_of_x_fz_and_p1() -> None:
    # x_Fz = 0,9 moves the threshold to 0,844 at 10 bar, where 3,5 bar of
    # differential is turbulent.
    cavitating = _liquid(6.5e5)
    with pytest.raises(ValueError, match="corrected_ratio"):
        dataclasses.replace(cavitating, incipient_ratio=0.9)


def test_a_valve_result_stops_below_flashing() -> None:
    # 5.1 calls a point cavitating only while x_F is not greater than 1, and
    # Equation (9) has no value at 1 itself.
    cavitating = _liquid(6.5e5)
    span = cavitating.inlet_pressure_pa - cavitating.vapour_pressure_pa
    flashing = _at_differential(cavitating, span)
    with pytest.raises(ValueError, match="flashes"):
        dataclasses.replace(cavitating, **flashing)


# --- IEC 60534-8-3 5.2: five regimes, each closed at the top ----------------------


def _gas(outlet_pressure_pa: float) -> noise_control.AerodynamicValveNoise:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.ValveNoiseWarning)
        return noise_control.valve_aerodynamic_noise(
            noise_control.GasStream(
                mass_flow=2.22,
                inlet_pressure_pa=1.0e6,
                outlet_pressure_pa=outlet_pressure_pa,
                inlet_density=5.3,
                inlet_temperature_k=450.0,
                specific_heat_ratio=1.22,
                molecular_mass=19.8,
            ),
            noise_control.ValveTrim(
                flow_coefficient=90.0,
                style_modifier=noise_control.valve_style_modifier(0.00137, 0.181, 6),
                pressure_recovery=0.792 / 0.984,
                outlet_diameter_m=0.1,
                efficiency_correction=-3.8,
                strouhal_number=0.2,
            ),
            noise_control.DownstreamPipe(
                internal_diameter_m=0.2031, wall_thickness=0.008, density=8000.0
            ),
        )


def test_the_gas_regime_is_no_constructor_field() -> None:
    subsonic = _gas(7.2e5)
    with pytest.raises(TypeError, match="regime"):
        dataclasses.replace(subsonic, regime=2)


@pytest.mark.parametrize(
    ("outlet_pressure_pa", "regime"),
    [(7.2e5, 1), (6.0e5, 2), (4.0e5, 4), (0.5e5, 5)],
)
def test_the_gas_regime_is_read_from_the_ratio_and_the_boundaries(
    outlet_pressure_pa: float, regime: int
) -> None:
    point = _gas(outlet_pressure_pa)
    assert point.regime == regime
    assert point.regime == noise_control.flow_regime(
        point.pressure_ratio, point.boundaries
    )


def test_each_gas_regime_is_closed_at_the_top() -> None:
    boundaries = _gas(7.2e5).boundaries
    edge = boundaries.critical
    assert noise_control.flow_regime(edge, boundaries) == 1
    assert noise_control.flow_regime(math.nextafter(edge, math.inf), boundaries) == 2


def test_a_gas_result_refuses_a_ratio_no_regime_holds() -> None:
    subsonic = _gas(7.2e5)
    with pytest.raises(ValueError, match="pressure_ratio"):
        dataclasses.replace(subsonic, pressure_ratio=1.0)


def test_a_gas_result_cannot_keep_the_mach_number_of_another_regime() -> None:
    # x = 0,6 is regime IV, whose jet Mach number is 1,45; regime I kept 0,99.
    subsonic = _gas(7.2e5)
    with pytest.raises(ValueError, match="mach"):
        dataclasses.replace(subsonic, pressure_ratio=0.6)


def test_a_gas_result_cannot_keep_the_efficiency_of_another_regime() -> None:
    subsonic = _gas(7.2e5)
    shock = _gas(4.0e5)
    with pytest.raises(ValueError, match="acoustical_efficiency"):
        dataclasses.replace(subsonic, acoustical_efficiency=shock.acoustical_efficiency)


def test_the_gas_boundaries_are_those_of_the_gas_and_the_trim() -> None:
    subsonic = _gas(7.2e5)
    with pytest.raises(ValueError, match=r"boundaries\.vena_contracta"):
        dataclasses.replace(subsonic, specific_heat_ratio=1.4)


# --- NORAH2 guidance Appendix D: terrain above the line of sight screens -----------


def _section(peak_m: float) -> aircraft.TerrainScreeningResult:
    distances = np.linspace(0.0, 1000.0, 41)
    heights = peak_m * np.exp(-(((distances - 500.0) / 120.0) ** 2))
    return aircraft.terrain_screening_adjustment(
        _BANDS, (0.0, 10.0), (1000.0, 1.5), distances, heights
    )


def _ridge() -> aircraft.TerrainScreeningResult:
    return aircraft.terrain_screening_adjustment(
        _BANDS, (0.0, 10.0), (1000.0, 1.5), [0.0, 500.0, 1000.0], [0.0, 30.0, 0.0]
    )


def test_the_section_regime_follows_its_terrain() -> None:
    assert _section(2.0).screened is False
    assert _section(25.0).screened is True


def test_terrain_on_the_line_of_sight_does_not_screen() -> None:
    # Only points strictly above the line of sight are obstacles.
    result = aircraft.terrain_screening_adjustment(
        _BANDS, (0.0, 0.0), (100.0, 10.0), [0.0, 50.0, 100.0], [0.0, 5.0, 0.0]
    )
    assert result.screened is False


def test_a_screening_section_needs_its_diffracting_path() -> None:
    clear = _section(2.0)
    heights = np.asarray(clear.heights).copy()
    heights[20] = 40.0
    with pytest.raises(ValueError, match="path_difference"):
        dataclasses.replace(clear, heights=heights)


def test_the_diffracting_edges_are_the_rubber_bands() -> None:
    ridge = _ridge()
    moved = np.array([[400.0, 30.0]])
    with pytest.raises(ValueError, match="diffraction_points"):
        dataclasses.replace(ridge, diffraction_points=moved)


def test_a_section_runs_from_the_source_to_the_receiver() -> None:
    # The rubber band runs from the source to the receiver; terrain past the
    # receiver is no obstacle, and the function crops it away.
    ridge = _ridge()
    with pytest.raises(ValueError, match="distances"):
        dataclasses.replace(
            ridge, distances=[0.0, 500.0, 1200.0, 1300.0], heights=[0.0, 0.0, 30.0, 0.0]
        )


def test_a_section_starts_at_the_source() -> None:
    # A source 100 m before the section would leave a 50 m crest at the first
    # vertex out of the line-of-sight test.
    clear = _section(2.0)
    heights = np.asarray(clear.heights).copy()
    heights[0] = 50.0
    with pytest.raises(ValueError, match="distances"):
        dataclasses.replace(clear, source=(-100.0, 10.0), heights=heights)


@pytest.mark.parametrize(
    "source", [(1000.0, 10.0), (1200.0, 10.0), (float("nan"), 10.0), (0.0, math.inf)]
)
def test_a_section_result_needs_a_finite_source_before_its_receiver(
    source: tuple[float, float],
) -> None:
    clear = _section(2.0)
    with pytest.raises(ValueError, match="'source'"):
        dataclasses.replace(clear, source=source)


# --- ISO 10848: the band set is stated, or read from the spacing --------------------


def test_the_measured_index_leaves_the_band_set_to_the_frequencies() -> None:
    result = building.vibration_reduction_index(
        np.full(16, 10.0),
        4.0,
        10.0,
        12.0,
        frequencies=np.array([100.0 * 2.0 ** (k / 3.0) for k in range(16)]),
    )
    assert result.band_type is None
    octaves = dataclasses.replace(
        result,
        frequencies=np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]),
        k_ij=np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
    )
    # 125 Hz to 1000 Hz, the octave range of Annex A.
    assert octaves.single_number == pytest.approx(2.5)


# --- ISO 8253-1 6.3.5 and 7.5: peaks, valleys and the reversals kept ----------------


def test_the_reversal_kinds_are_no_constructor_fields() -> None:
    fields = dataclasses.asdict(
        hearing.automatic_audiometry_threshold([40.0, 30.0, 42.0, 31.0, 41.0, 32.0])
    )
    with pytest.raises(TypeError, match="is_peak"):
        hearing.AutomaticThresholdResult(**fields, is_peak=np.ones(6, dtype=bool))


def test_the_reversals_kept_are_read_from_the_levels() -> None:
    # 6.3.5 a): an excursion of 3 dB or less loses both its reversals.
    result = hearing.automatic_audiometry_threshold(
        [40.0, 30.0, 42.0, 31.0, 41.0, 32.0]
    )
    narrowed = hearing.automatic_audiometry_threshold(
        [40.0, 30.0, 42.0, 39.0, 41.0, 32.0, 43.0, 31.0]
    )
    assert result.retained.tolist() == [False, True, True, True, True, True]
    assert narrowed.retained.tolist() == [False, True, False, False] + [
        False,
        True,
        True,
        True,
    ]
    assert narrowed.is_peak.tolist() == [True, False] * 4
    assert narrowed.peaks_db.tolist() == [43.0]


def test_an_automatic_threshold_is_held_to_its_reversals() -> None:
    result = hearing.automatic_audiometry_threshold(
        [40.0, 30.0, 42.0, 31.0, 41.0, 32.0]
    )
    other = np.array([40.0, 30.0, 42.0, 31.0, 41.0, 33.0])
    with pytest.raises(ValueError, match="mean_db"):
        dataclasses.replace(result, reversal_levels_db=other)


def test_a_tracing_that_keeps_no_peak_is_refused() -> None:
    result = hearing.automatic_audiometry_threshold(
        [40.0, 30.0, 42.0, 31.0, 41.0, 32.0]
    )
    narrowed = np.array([40.0, 30.0, 42.0, 39.0, 41.0, 32.0])
    with pytest.raises(ValueError, match="no peak or no valley"):
        dataclasses.replace(result, reversal_levels_db=narrowed)


def test_a_tracing_that_does_not_alternate_is_refused() -> None:
    result = hearing.automatic_audiometry_threshold([40.0, 30.0, 42.0, 31.0])
    stepped = np.array([40.0, 30.0, 20.0, 31.0])
    with pytest.raises(ValueError, match="'reversal_levels_db' must alternate"):
        dataclasses.replace(result, reversal_levels_db=stepped)


def test_the_sweep_peaks_are_read_from_the_levels() -> None:
    frequencies = np.geomspace(500.0, 4000.0, 8)
    levels = np.array([30.0, 40.0, 31.0, 41.0, 32.0, 42.0, 31.0, 40.0])
    result = hearing.sweep_audiometry_threshold(frequencies, levels)
    assert result.is_peak.tolist() == [False, True] * 4


def test_a_sweep_threshold_is_held_to_its_reversals() -> None:
    frequencies = np.geomspace(500.0, 4000.0, 8)
    levels = np.array([30.0, 40.0, 31.0, 41.0, 32.0, 42.0, 31.0, 40.0])
    result = hearing.sweep_audiometry_threshold(frequencies, levels)
    with pytest.raises(ValueError, match="mean_db"):
        dataclasses.replace(result, reversal_levels_db=levels + 1.0)


# --- IEC 61094-2 Table C.3: read from a row or interpolated -------------------------


def test_the_interpolated_rows_are_read_from_the_frequencies() -> None:
    result = metrology.large_volume_wave_motion_correction([800.0, 1100.0, 2000.0])
    assert result.interpolated.tolist() == [False, True, False]
    hydrogen = metrology.large_volume_wave_motion_correction(
        [800.0, 1100.0, 2000.0], speed_of_sound_ratio=2.0
    )
    assert hydrogen.interpolated.tolist() == [False, False, False]


def test_a_correction_beyond_the_last_row_is_refused() -> None:
    result = metrology.large_volume_wave_motion_correction([800.0, 1100.0, 2000.0])
    with pytest.raises(ValueError, match="2500"):
        dataclasses.replace(result, speed_of_sound_ratio=0.5)


def test_a_correction_of_another_gas_is_refused() -> None:
    result = metrology.large_volume_wave_motion_correction([800.0, 1100.0, 2000.0])
    with pytest.raises(ValueError, match="correction_db"):
        dataclasses.replace(result, speed_of_sound_ratio=2.0)


# --- ISO 11957 3.6: the prime says the measurement was in situ ----------------------


def _laboratory_cabin() -> noise_control.CabinInsulationResult:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.CabinInsulationWarning)
        return noise_control.cabin_insulation(
            np.full(_BANDS.size, 80.0), np.full(_BANDS.size, 50.0), frequencies=_BANDS
        )


def test_the_prime_is_read_from_the_method() -> None:
    laboratory = _laboratory_cabin()
    assert laboratory.apparent is False
    in_situ = dataclasses.replace(laboratory, method="in-situ-loudspeaker")
    assert in_situ.apparent is True
    assert in_situ.symbol == "D'_p"


def test_a_cabin_result_refuses_an_unknown_method() -> None:
    laboratory = _laboratory_cabin()
    with pytest.raises(ValueError, match="method"):
        dataclasses.replace(laboratory, method="guessed")


def test_only_the_actual_noise_method_carries_an_a_weighted_insulation() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.CabinInsulationWarning)
        actual = noise_control.cabin_insulation(
            np.full(_BANDS.size, 80.0),
            np.full(_BANDS.size, 50.0),
            frequencies=_BANDS,
            method="in-situ-actual-noise",
            a_weighted_room_level=85.0,
            a_weighted_cabin_level=55.0,
        )
    with pytest.raises(ValueError, match="a_weighted_insulation"):
        dataclasses.replace(actual, method="laboratory")


# --- IEC 61400-11 9.5.4: an identified tone is read from the spectrum --------------


def _tonal(amplitude_db: float) -> environment.WindTurbineTonalityResult:
    frequencies = np.arange(400.0, 601.0, 1.0)
    levels = np.full(frequencies.size, 30.0)
    levels[100] += amplitude_db
    return environment.wind_turbine_tonality(levels, frequencies)


def test_the_identified_tone_is_read_from_the_levels() -> None:
    tonal = _tonal(15.0)
    assert tonal.has_identified_tone is True
    flat = environment.wind_turbine_tonality(
        np.full(tonal.frequencies.size, 30.0), tonal.frequencies, tone_frequency=500.0
    )
    assert flat.has_identified_tone is False
    assert flat.is_audible is False


def test_a_tonality_result_cannot_keep_the_numbers_of_another_spectrum() -> None:
    tonal = _tonal(15.0)
    flat = np.full(tonal.frequencies.size, 30.0)
    with pytest.raises(ValueError, match="tone_level"):
        dataclasses.replace(tonal, levels=flat)


@pytest.mark.parametrize("candidate_hz", [700.0, 501.3])
def test_a_tonality_result_needs_its_candidate_on_a_line(candidate_hz: float) -> None:
    tonal = _tonal(15.0)
    with pytest.raises(ValueError, match="candidate_frequency_hz"):
        dataclasses.replace(tonal, candidate_frequency_hz=candidate_hz)


def test_a_tonality_candidate_below_20_hz_is_refused() -> None:
    frequencies = np.arange(10.0, 301.0, 1.0)
    levels = np.full(frequencies.size, 30.0)
    levels[90] += 15.0
    low = environment.wind_turbine_tonality(levels, frequencies)
    with pytest.raises(ValueError, match="candidate_frequency_hz"):
        dataclasses.replace(low, candidate_frequency_hz=15.0)


# --- IEC TS 61400-11-2 11.7: the background rule of each bin ------------------------


@pytest.mark.parametrize(
    ("background_db", "regime"),
    [
        (37.0, environment.BackgroundCorrectionRegime.LOGARITHMIC),
        (37.1, environment.BackgroundCorrectionRegime.THREE_DB),
        (40.0, environment.BackgroundCorrectionRegime.THREE_DB),
        (40.1, environment.BackgroundCorrectionRegime.UNDETERMINED),
    ],
)
def test_the_background_rule_is_read_from_the_levels(
    background_db: float, regime: environment.BackgroundCorrectionRegime
) -> None:
    # "at least 3 dB" and "0 dB to 3 dB" are both inclusive.
    result = environment.turbine_sound_levels([40.0], [background_db])
    assert result.regimes == (regime,)
    assert dataclasses.replace(result).regimes == (regime,)


def test_a_level_difference_is_the_total_less_the_background() -> None:
    result = environment.turbine_sound_levels([40.0], [37.0])
    with pytest.raises(ValueError, match="level_differences_db"):
        dataclasses.replace(result, level_differences_db=np.array([-0.1]))


def test_a_turbine_level_follows_the_rule_of_its_bin() -> None:
    # A louder background leaves the level undetermined, not the logarithmic
    # subtraction kept from 37 dB.
    result = environment.turbine_sound_levels([40.0], [37.0])
    louder = {
        "background_levels_db": np.array([45.0]),
        "level_differences_db": np.array([-5.0]),
    }
    with pytest.raises(ValueError, match="turbine_levels_db"):
        dataclasses.replace(result, **louder)


def test_an_undetermined_bin_carries_no_uncertainty() -> None:
    result = environment.turbine_sound_levels([40.0], [41.0])
    with pytest.raises(ValueError, match="turbine_uncertainty_db"):
        dataclasses.replace(result, turbine_uncertainty_db=np.array([0.5]))


# --- Ainslie (2010) 9.3: Weston's regimes, each from its own boundary --------------


def test_each_weston_regime_holds_from_its_own_boundary() -> None:
    bounds = underwater.weston_regime_boundaries(250.0, 50.0)
    edges = [
        bounds.spherical_to_cylindrical,
        bounds.cylindrical_to_mode_stripping,
        bounds.mode_stripping_to_single_mode,
    ]
    result = underwater.weston_propagation_loss(edges, 250.0, 50.0)
    assert result.regime.tolist() == ["cylindrical", "mode-stripping", "single-mode"]
    laws = (result.cylindrical, result.mode_stripping, result.single_mode)
    in_force = [float(law[k]) for k, law in enumerate(laws)]
    assert np.asarray(result.propagation_loss).tolist() == in_force


def test_the_weston_regime_is_read_from_the_range() -> None:
    result = underwater.weston_propagation_loss(
        np.geomspace(10.0, 1.0e5, 40), 250.0, 50.0
    )
    assert result.regime[0] == "spherical"
    assert dataclasses.replace(result).regime[0] == "spherical"


def test_a_weston_loss_is_the_law_of_the_regime_in_force() -> None:
    # Moving the first range onto the cylindrical boundary leaves the
    # spherical loss of 10 m beside a cylindrical label.
    result = underwater.weston_propagation_loss(
        np.geomspace(10.0, 1.0e5, 40), 250.0, 50.0
    )
    ranges = np.asarray(result.range_m).copy()
    ranges[0] = result.boundaries.spherical_to_cylindrical
    with pytest.raises(ValueError, match="propagation_loss"):
        dataclasses.replace(result, range_m=ranges)


# --- McFadden (1987): a period between samples is interpolated --------------------


def _averaged(period_s: float) -> signals.SynchronousAverageResult:
    fs = 1000.0
    t = np.arange(4000) / fs
    return signals.time_synchronous_average(
        np.sin(2.0 * np.pi * t / period_s), fs, period_s=period_s
    )


def test_the_alignment_is_no_constructor_field() -> None:
    whole = _averaged(0.05)
    with pytest.raises(TypeError, match="interpolated"):
        dataclasses.replace(whole, interpolated=True)


def test_the_alignment_is_read_from_the_rate_and_the_period() -> None:
    assert _averaged(0.05).interpolated is False
    assert _averaged(0.0505).interpolated is True


def test_an_average_keeps_the_period_grid_of_its_rate() -> None:
    whole = _averaged(0.05)
    with pytest.raises(ValueError, match="samples_per_period"):
        dataclasses.replace(whole, period_s=0.06)


# --- Jimenez et al. (2017): a converged design reached perfect absorption ----------


def test_a_converged_design_reached_perfect_absorption() -> None:
    resonator = materials.HelmholtzResonator(0.01, 0.01, 0.05, 0.02)
    with pytest.raises(ValueError, match="absorption"):
        materials.CriticalCouplingResult(
            target_frequency=300.0,
            angle_rad=0.0,
            resonator=resonator,
            slit_height=1.0e-3,
            absorption=0.2,
            normalized_impedance=3.0 + 0.0j,
            converged=True,
        )
