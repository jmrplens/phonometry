#  Copyright (c) 2026. Jose Manuel Requena Plens

"""Real result objects, built through the public API, for the plot tests.

Every ``.plot()`` in the library draws a result object, and a result object is
only honest if a real computation produced it: a hand-filled dataclass would let
a renderer agree with a field the standard never puts there. So each factory
below runs the public entry point on a small, deterministic input and hands back
the result it returns, which is what the plot contract in
``tests/test_result_plots.py`` and the per-domain content assertions both draw.

Two of them build the dataclass directly, and say why in their docstrings: the
wide-band ``IntensityResult`` needs centres two decades apart to exercise the
log-axis bar widths, and the invalid-band ``RoomAcousticsResult`` needs exactly
one band flagged on every decay-time series. Everything else goes through the
same call a user would write.

The tests tree is on ``sys.path`` (``pythonpath = ["tests"]`` in pyproject), so
this module is imported as ``result_factories`` next to ``reference_data``,
``golden_data`` and ``oracle_data``.
"""

from __future__ import annotations

import numpy as np
import pytest

import phonometry as ph

FS = 48000
RNG = np.random.default_rng(20260707)


def _exp_ir(seconds: float = 0.8, t60: float = 0.5) -> np.ndarray:
    t = np.arange(int(seconds * FS)) / FS
    decay = np.exp(-3.0 * np.log(10.0) / t60 * t)
    return decay * RNG.standard_normal(t.size)


def _zwicker_stationary() -> ph.psychoacoustics.ZwickerLoudness:
    return ph.psychoacoustics.loudness_zwicker_from_spectrum(np.full(28, 40.0))


def _sti() -> ph.speech.STIResult:
    sig = ph.speech.stipa_signal(fs=FS, seconds=16.0, seed=3)
    return ph.speech.stipa(sig, FS)


def _airborne_rating() -> ph.building.WeightedRatingResult:
    measured = np.array(
        [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58],
        dtype=float,
    )
    return ph.building.weighted_rating(measured)


def _impact_rating() -> ph.building.ImpactRatingResult:
    measured = np.array(
        [60, 61, 62, 63, 64, 65, 63, 61, 60, 58, 56, 53, 50, 47, 44, 41],
        dtype=float,
    )
    return ph.building.weighted_impact_rating(measured)


def _room(limits: list[float] | None) -> ph.room.RoomAcousticsResult:
    return ph.room.room_parameters(_exp_ir(), FS, limits=limits)


def _sound_power() -> ph.emission.SoundPowerResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    r = 2.0
    s = 2.0 * np.pi * r**2
    lw_bands = np.array([90.0, 92.0, 95.0, 93.0])
    levels = np.tile(lw_bands - 10.0 * np.log10(s), (10, 1))
    return ph.emission.sound_power_pressure(
        levels, "hemisphere", radius=r, frequencies=freqs
    )


def _reverb_power() -> ph.emission.ReverberationSoundPowerResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    t60 = np.array([1.6, 1.5, 1.4, 1.1])
    lp = np.tile(np.array([80.0, 82.0, 84.0, 81.0]), (6, 1))
    return ph.emission.sound_power_reverberation(lp, t60, 200.0, 220.0, freqs)


def _sound_energy() -> ph.emission.SoundEnergyResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    r = 2.0
    s = 2.0 * np.pi * r**2
    lj_bands = np.array([100.0, 102.0, 105.0, 103.0])
    levels = np.tile(lj_bands - 10.0 * np.log10(s), (10, 1))
    return ph.emission.sound_energy_pressure(
        levels, "hemisphere", radius=r, frequencies=freqs
    )


def _reverb_energy() -> ph.emission.ReverberationSoundEnergyResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    t60 = np.array([1.6, 1.5, 1.4, 1.1])
    le = np.tile(np.array([90.0, 92.0, 94.0, 91.0]), (6, 1))
    return ph.emission.sound_energy_reverberation(le, t60, 200.0, 220.0, freqs)


def _intensity_power_negative() -> ph.emission.SoundPowerIntensityResult:
    areas = np.array([0.5, 0.5, 0.5, 0.5])
    # band 0 positive net, band 1 all-negative net (external source).
    intensity = np.column_stack([np.full(4, 5.0e-4), np.full(4, -5.0e-5)])
    freqs = np.array([500.0, 1000.0])
    with pytest.warns(ph.emission.SoundPowerWarning):
        return ph.emission.sound_power_intensity(intensity, areas, frequencies=freqs)


def _intensity() -> ph.emission.IntensityResult:
    p1 = RNG.standard_normal(FS)
    p2 = np.roll(p1, 1)
    return ph.emission.sound_intensity(
        p1, p2, FS, spacing=0.012, fraction=3, limits=[125, 4000]
    )


def _open_plan() -> ph.room.OpenPlanResult:
    positions = np.array([2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0])
    spl = 57.0 - 7.0 * np.log2(positions / 4.0)
    sti = np.clip(0.9 - 0.055 * positions, 0.0, 1.0)
    return ph.room.open_plan_metrics(positions, spl, sti)


def _outdoor() -> ph.environment.OutdoorAttenuation:
    bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
    barrier = ph.environment.Barrier(source_to_edge=101.0, edge_to_receiver=101.0)
    return ph.environment.outdoor_propagation_attenuation(
        200.0,
        1.5,
        1.5,
        frequencies=bands,
        ground_source=1.0,
        ground_middle=1.0,
        ground_receiver=1.0,
        barrier=barrier,
        temperature_c=15.0,
        relative_humidity_percent=70.0,
    )


def _cnossos_road() -> ph.environment.RoadEmissionResult:
    return ph.environment.road_source_power(
        [
            ph.environment.RoadTraffic(
                ph.environment.RoadVehicleCategory.LIGHT, 1200.0, 50.0
            ),
            ph.environment.RoadTraffic(
                ph.environment.RoadVehicleCategory.HEAVY, 45.0, 50.0
            ),
        ],
        surface=ph.environment.RoadSurface.THIN_LAYER_A,
        temperature_c=12.0,
        road_slope_percent=3.0,
    )


def _reflection_index() -> ph.environment.ReflectionIndexResult:
    """EN 1793-5 Table B.1: twelve grid positions in front of a 4 m barrier."""
    from reference_data import barrier_reflection as br

    return ph.environment.reflection_index_from_positions(
        np.asarray(br.TABLE_B1_POSITIONS).T
    )


def _reflection_records() -> tuple[np.ndarray, np.ndarray]:
    """In-front and free-field records of microphone 5 before a half reflector."""
    samples = 2048
    t = np.arange(samples) / FS

    def pulse(at_s: float, amplitude: float) -> np.ndarray:
        dt = t - at_s
        return (
            amplitude
            * np.exp(-0.5 * (dt / 0.05e-3) ** 2)
            * np.cos(2 * np.pi * 3000.0 * dt)
        )

    direct, reflected = 1.25 / 343.0, 1.75 / 343.0
    free = pulse(0.004 + direct, 0.8)
    front = pulse(0.004 + direct, 0.8) + 0.5 * pulse(0.004 + reflected, 1.0 / 1.75)
    return front, free


def _direct_sound_subtraction() -> ph.environment.DirectSoundSubtraction:
    """EN 1793-5 5.5.4 on microphone 5 in front of a half reflector."""
    front, free = _reflection_records()
    return ph.environment.subtract_direct_sound(front, free, FS)


def _reflection_limit() -> ph.environment.ReflectionFrequencyLimit:
    """EN 1793-5 5.5.7 for a 3,5 m barrier, the case of 5.8."""
    return ph.environment.reflection_low_frequency_limit(3.5, speed_of_sound=343.0)


def _reflection_grid_check() -> ph.environment.ReflectionGridCheck:
    """EN 1793-5 5.6.2.6 with microphone 7 out by 30 mm."""
    from reference_data import barrier_reflection as br

    distances = np.array([dk for _, dk in br.TABLE_3])
    distances[6] += 0.030
    return ph.environment.check_reflection_grid_position(
        distances / 343.0, speed_of_sound=343.0
    )


def _statistical_pass_by() -> ph.environment.StatisticalPassByResult:
    """The ISO 11819-1 method on the pass-bys whose lines Annex E prints."""
    from reference_data import statistical_pass_by as spb

    categories: list[str] = []
    speeds: list[float] = []
    levels: list[float] = []
    for category in ph.environment.SPB_VEHICLE_CATEGORIES:
        v, level = spb.annex_e_pass_bys(category)
        categories += [category] * len(v)
        speeds += v
        levels += level
    return ph.environment.statistical_pass_by(
        categories, speeds, levels, road_speed_category="medium"
    )


def _am_block() -> ph.environment.ModulationBlock:
    """The IOA sample series of 100 Hz to 400 Hz (IEC TS 61400-11-2, 13.6.2.3)."""
    from reference_data import wind_turbine_receptor as wt

    return ph.environment.amplitude_modulation_block(
        np.asarray(wt.IOA_SAMPLE_SERIES_TENTHS_DB[2][:100]) / 10.0,
        modulation_frequency_range_hz=(0.4, 0.9),
    )


def _am_period() -> ph.environment.ModulationPeriod:
    """A 10 min period of 36 valid 10 s blocks (IEC TS 61400-11-2, 13.6.3)."""
    from reference_data import wind_turbine_receptor as wt

    indices = wt.IOA_PERIOD_CASES[0][1]
    series = np.concatenate([wt.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in indices])
    return ph.environment.amplitude_modulation_period(
        series / 10.0, modulation_frequency_range_hz=wt.IOA_PERIOD_RANGE_HZ
    )


def _am_bins() -> ph.environment.BinnedModulation:
    """Ten 10 min ratings in three bands, binned (IEC TS 61400-11-2, 13.6.4)."""
    ratings = np.array(
        [
            [2.0, 4.0, 1.0],
            [0.0, 6.5, 3.5],
            [5.0, 1.0, 9.5],
            [3.0, 3.0, 0.0],
            [7.0, 2.0, 2.0],
        ]
        * 2
    )
    speeds = np.array([4.6, 5.4, 5.5, 7.0, 7.4, 6.1, 6.2, 8.0, 3.2, 4.0])
    return ph.environment.bin_amplitude_modulation(ratings, speeds)


def _wind_shear() -> ph.environment.WindShearProfile:
    return ph.environment.wind_shear_profile(5.0, 9.0, upper_height_m=120.0)


def _binned_levels() -> ph.environment.BinnedSoundLevels:
    speeds = np.linspace(3.0, 9.0, 40)
    levels = 30.0 + 1.5 * speeds + np.sin(7.0 * speeds)
    return ph.environment.bin_sound_levels(levels, speeds, type_b_uncertainty_db=0.4)


def _turbine_levels() -> ph.environment.TurbineSoundLevels:
    return ph.environment.turbine_sound_levels(
        [38.0, 40.0, 42.0, 43.0],
        [33.0, 36.0, 40.0, 41.0],
        total_uncertainty_db=0.8,
        background_uncertainty_db=0.6,
        wind_speeds_m_s=[4.0, 5.0, 6.0, 7.0],
    )


def _turbine_levels_by_sector() -> ph.environment.TurbineSoundLevels:
    speeds, directions = [4.0, 5.0, 6.0, 4.0, 5.0, 6.0], [0.0] * 3 + [90.0] * 3
    total = ph.environment.bin_sound_levels(
        [38.0, 40.0, 42.0, 36.0, 39.0, 41.0], speeds, directions
    )
    background = ph.environment.bin_sound_levels(
        [33.0, 36.0, 40.0, 30.0, 32.0, 35.0], speeds, directions
    )
    return total.background_corrected(background)


def _predicted_receptor() -> ph.environment.PredictedReceptorLevel:
    return ph.environment.predicted_receptor_level([35.0, 32.0, 28.0, 20.0], 1.5)


def _relevant_turbines() -> ph.environment.SoundRelevantTurbines:
    return ph.environment.sound_relevant_turbines([35.0, 33.0, 32.0, 25.0, 20.0, 18.0])


def _low_frequency() -> ph.environment.LowFrequencyLevel:
    return ph.environment.wind_turbine_low_frequency_level(
        np.full(14, 100.0),
        distance_m=600.0,
        hub_height_m=120.0,
        facade_insulation_db=ph.environment.LOW_FREQUENCY_FACADE_INSULATION_DB[
            "Denmark brick or similar"
        ],
    )


def _emergence() -> ph.environment.SoundEmergence:
    return ph.environment.sound_emergence(
        [40.0, 42.0, 45.0], [36.0, 38.0, 41.0], wind_speeds_m_s=[5.0, 6.0, 7.0]
    )


def _wt_rating() -> ph.environment.WindTurbineRatingLevel:
    return ph.environment.wind_turbine_rating_level(
        40.0, tonal_adjustment_db=2.0, amplitude_modulation_adjustment_db=3.5
    )


def _tone_search() -> ph.environment.ToneSearchLimit:
    return ph.environment.upper_tone_search_frequency(
        600.0, temperature_c=10.0, relative_humidity_percent=50.0
    )


def _rolling_stock_roughness(
    offset_db: float = -1.0,
) -> ph.environment.AcousticRoughnessSpectrum:
    """A roughness spectrum held 1 dB under the ISO 3095 Figure 2 limit."""
    limit = ph.environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    wavelengths = sorted(limit, reverse=True)
    return ph.environment.AcousticRoughnessSpectrum(
        wavelengths, [limit[w] + offset_db for w in wavelengths]
    )


def _rolling_stock_roughness_record() -> ph.environment.AcousticRoughnessSpectrum:
    """EN 15610 Method A on a 3 m record of two sinusoids and a little noise."""
    x = np.arange(0.0, 3.0, 1.0e-3)
    record = 2.0 * np.cos(2.0 * np.pi * 25.0 * x) + 0.5 * np.cos(
        2.0 * np.pi * 125.0 * x
    )
    record += 0.05 * RNG.standard_normal(x.size)
    return ph.environment.acoustic_roughness_spectrum(record, sample_spacing_m=1.0e-3)


def _track_decay_rate() -> ph.environment.TrackDecayRate:
    """EN 15461 Formula 1 on exponential responses 20 % above the vertical limit."""
    limit = ph.environment.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["vertical"]
    rates = np.array(list(limit.values())) * 1.2
    positions = ph.environment.track_decay_excitation_positions()
    return ph.environment.track_decay_rate(
        np.exp(-np.outer(positions, rates / 8.686)), frequencies_hz=list(limit)
    )


def _pass_by_measurement() -> ph.environment.PassByMeasurement:
    """ISO 3095 6.6.3 on a 1 kHz tone swelling through a 10 s record."""
    t = np.arange(int(10.0 * FS)) / FS
    swell = np.exp(-(((t - 5.0) / 1.5) ** 2)) + 1.0e-3
    return ph.environment.pass_by_measurement(
        np.sin(2.0 * np.pi * 1000.0 * t) * swell, FS, start_s=4.0, end_s=6.0
    )


def _stationary_test() -> ph.environment.StationaryTestResult:
    """ISO 3095 5.8.1 on three sets of four positions, one of them an end."""
    return ph.environment.stationary_test(
        [[60.0, 62.0, 61.0, 65.0], [60.5, 62.0, 61.0, 64.0], [61.0, 62.5, 61.0, 64.5]],
        [4.0, 4.0, 4.0, ph.environment.STATIONARY_END_POSITION_LENGTH_M],
    )


def _rolling_stock_test() -> ph.environment.RollingStockTestResult:
    """ISO 3095 6.7.1 on three runs at each side."""
    return ph.environment.rolling_stock_test(
        {"left": [80.2, 80.9, 81.4], "right": [81.6, 82.4, 81.9]}
    )


def _rise_speed() -> ph.environment.RiseSpeedResult:
    """ISO 3095 Annex A on a history with one 12 dB ramp."""
    times = np.arange(0.0, 2.0, 0.01)
    levels = np.full(times.size, 60.0)
    levels[50:71] = 60.0 + 0.6 * np.arange(21)
    levels[71:] = 72.0
    return ph.environment.impulsiveness_rise_speed(times, levels)


def _adjacent_neutrality() -> ph.environment.AdjacentVehicleNeutrality:
    """ISO 3095 6.3.4 on levels 1,9 dB apart."""
    return ph.environment.check_adjacent_vehicle_neutrality(83.0, 81.1)


def _small_roughness_deviation() -> ph.environment.SmallRoughnessDeviation:
    """ISO 3095 Annex C with the 4 cm band 2 dB over the limit at 80 km/h."""
    base = _rolling_stock_roughness()
    levels = np.array(base.levels_db)
    levels[base.bands.index(14)] += 3.0
    roughness = ph.environment.AcousticRoughnessSpectrum(base.wavelengths_m, levels)
    frequencies = [
        100.0,
        125.0,
        160.0,
        200.0,
        250.0,
        315.0,
        400.0,
        500.0,
        630.0,
        800.0,
        1000.0,
        1250.0,
        1600.0,
        2000.0,
        2500.0,
        3150.0,
        4000.0,
    ]
    noise = 70.0 + 5.0 * np.sin(np.linspace(0.0, 3.0, len(frequencies)))
    return ph.environment.check_small_roughness_deviations(
        roughness, noise, frequencies_hz=frequencies, speed_kmh=80.0
    )


def _roughness_comparability() -> ph.environment.RoughnessComparability:
    """ISO 3095 Annex E between two tracks 3 dB apart in three bands."""
    one = _rolling_stock_roughness(-2.0)
    levels = np.array(one.levels_db)
    levels[8:11] += 3.0
    two = ph.environment.AcousticRoughnessSpectrum(one.wavelengths_m, levels)
    frequencies = [250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0]
    noise = np.full(len(frequencies), 75.0)
    return ph.environment.roughness_comparability(
        one, two, noise, noise + 1.0, frequencies_hz=frequencies, speed_kmh=100.0
    )


def _reference_track() -> ph.environment.ReferenceTrackCheck:
    """ISO 3095 6.2 on roughness under Figure 2 and rates over Figure 3."""
    limits = ph.environment.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M
    rates = [
        ph.environment.TrackDecayRate(
            d, list(limits[d]), [1.1 * v for v in limits[d].values()]
        )
        for d in ("vertical", "lateral")
    ]
    return ph.environment.check_reference_track(
        [_rolling_stock_roughness(), _rolling_stock_roughness(-1.5)],
        rates,
        speed_kmh=160.0,
    )


def _pass_by_uncertainty() -> ph.environment.PassByUncertainty:
    """ISO 3095 Annex G, three inputs of Table G.1."""
    return ph.environment.pass_by_uncertainty(
        55.0,
        [
            ph.metrology.Quantity(0.0, 0.46, name="level linearity"),
            ph.metrology.Quantity(0.0, 0.35, name="tripod"),
            ph.metrology.Quantity(0.515, 0.30, name="ground level"),
        ],
    )


def _porous_medium() -> ph.materials.PorousMediumResult:
    f = np.linspace(400.0, 4000.0, 40)
    return ph.materials.miki(f, 20000.0)


def _layered_absorber() -> ph.materials.LayeredAbsorberResult:
    f = np.linspace(400.0, 4000.0, 40)
    med = ph.materials.miki(f, 20000.0)
    return ph.materials.layered_absorber(f, [ph.materials.PorousLayer(0.05, med)])


def _diffuse_absorption() -> ph.materials.DiffuseFieldAbsorptionResult:
    f = np.linspace(400.0, 4000.0, 8)
    med = ph.materials.miki(f, 20000.0)
    return ph.materials.diffuse_field_absorption(
        f, [ph.materials.PorousLayer(0.05, med)], quadrature_points=16
    )


def _impedance_tube() -> ph.materials.ImpedanceTubeResult:
    f = np.linspace(200.0, 1600.0, 60)
    r_true = 0.6 * np.exp(-f / 1200.0) * np.exp(0.8j)
    k = 2.0 * np.pi * f / 343.2
    s, x1 = 0.05, 0.12
    phase = np.exp(2j * k * x1)
    h12 = (np.exp(-1j * k * s) + r_true * phase * np.exp(1j * k * s)) / (
        1.0 + r_true * phase
    )
    return ph.materials.two_microphone_impedance(
        h12,
        frequency=f,
        spacing=s,
        x1=x1,
        speed_of_sound=343.2,
        characteristic_impedance=407.0,
    )


_MC_QUANTITIES = (
    ph.metrology.Quantity(74.0, 0.0, name="Reading"),
    ph.metrology.rectangular(0.0, 0.20, name="Calibration"),
    ph.metrology.Quantity(0.0, 0.35, dof=9, name="Position"),
)


def _monte_carlo() -> ph.metrology.MonteCarloResult:
    return ph.metrology.monte_carlo(
        lambda a, b, c: a + b + c,
        _MC_QUANTITIES,
        trials=2000,
        seed=7,
        keep_samples=True,
    )


def _exposure() -> ph.hearing.ExposureResult:
    tasks = [
        ph.hearing.Task((86.4, 86.7, 87.0), 2.0, label="grinding"),
        ph.hearing.Task((80.1, 80.9, 80.5), 3.0, label="welding"),
        ph.hearing.Task((75.0, 74.6, 74.9), 3.0, label="assembly"),
    ]
    return ph.hearing.task_based_exposure(tasks)


def _sel_distribution() -> ph.environment.SelDistribution:
    """Five replica levels of a distant blast and their probabilities (ISO 13474)."""
    return ph.environment.sel_distribution(
        [30.0, 33.0, 36.0, 41.0, 45.0], [0.3, 0.3, 0.2, 0.15, 0.05]
    )


def _level_difference_quantiles() -> ph.environment.LevelDifferenceQuantiles:
    """The 25 level differences of the ISO 17534-1 C.4 example."""
    from reference_data import software_quality

    return ph.environment.level_difference_quantiles(
        software_quality.ISO17534_1_EXAMPLE_DIFFERENCES_DB
    )


def _round_robin_precision() -> ph.environment.RoundRobinPrecision:
    """Thirty receivers calculated by three programs (ISO 17534-1 4.5.2)."""
    base = np.linspace(45.0, 65.0, 30)[:, None]
    spread = np.linspace(0.1, 1.5, 30)[:, None]
    return ph.environment.round_robin_precision(
        base + spread * np.array([-1.0, 0.25, 0.75])
    )


def _calculation_verification() -> ph.environment.CalculationVerification:
    """Three rows of a TRC form, the last outside its limits (ISO 17534-1 B.2)."""
    return ph.environment.verify_calculation_results(
        [13.7, 19.5, 21.2],
        [13.65, 19.45, 21.05],
        [13.75, 19.55, 21.15],
        labels=["63 Hz", "125 Hz", "250 Hz"],
    )


def _service_equipment() -> ph.building.ServiceEquipmentResult:
    """A ventilation outlet heard in a bedroom, 25 Hz to 10 kHz (ISO/DIS 16032)."""
    freqs = np.array(list(ph.building.SERVICE_EQUIPMENT_WEIGHTING["third"]["A"]))
    shape = 48.0 - 0.6 * np.arange(freqs.size)
    readings = shape + np.array([[0.4], [-0.3], [0.8]])
    background = shape - 12.0
    background[[1, 24]] = shape[[1, 24]] - 3.0
    t = np.full(freqs.size, 0.6)
    return ph.building.service_equipment_level(
        readings,
        freqs,
        quantity="eq",
        background_db=background,
        reverberation_time_s=t,
        volume_m3=32.0,
    )


def _service_equipment_background() -> ph.building.ServiceEquipmentBackgroundResult:
    """Three octave bands, one of them held at 2,2 dB (ISO/DIS 16032 Clause 9)."""
    return ph.building.service_equipment_background_correction(
        [52.0, 48.0, 41.0], [38.0, 42.0, 39.0], frequencies_hz=[125.0, 250.0, 500.0]
    )


def _position_spread() -> ph.building.PositionSpreadCheck:
    """Six A-weighted readings of 7.4.1 that settle on the second stage."""
    return ph.building.check_position_spread([36.2, 33.0, 34.1, 35.8, 32.4, 34.6])


def _service_equipment_positions() -> ph.building.ServiceEquipmentPositionCheck:
    """A 4,2 m by 3,4 m bedroom with a supply outlet near the ceiling."""
    return ph.building.check_service_equipment_positions(
        (4.2, 3.4, 2.5),
        (0.5, 0.5, 0.5),
        [(2.1, 1.9, 1.3), (3.4, 0.8, 1.6)],
        source_positions_m=[(4.0, 3.2, 2.3)],
    )


def _soundscape_answers() -> tuple[np.ndarray, list[str]]:
    """Twelve Method A part 2 answers at three sites (ISO/TS 12913-3 A.3)."""
    answers = np.array(
        [
            [5, 1, 4, 3, 5, 1, 3, 2],
            [4, 2, 4, 3, 4, 1, 3, 2],
            [5, 1, 3, 4, 5, 1, 2, 2],
            [4, 2, 3, 3, 4, 2, 3, 2],
            [2, 4, 4, 1, 2, 4, 5, 2],
            [3, 4, 5, 2, 2, 3, 5, 1],
            [2, 5, 4, 1, 1, 4, 5, 2],
            [3, 4, 4, 2, 2, 3, 4, 2],
            [2, 3, 1, 4, 2, 3, 1, 5],
            [2, 2, 2, 4, 3, 3, 2, 4],
            [3, 2, 1, 5, 3, 2, 1, 4],
            [2, 3, 2, 4, 2, 3, 2, 5],
        ],
        dtype=float,
    )
    sites = ["garden"] * 4 + ["market"] * 4 + ["car park"] * 4
    return answers, sites


def _pleasantness_eventfulness() -> ph.environment.PleasantnessEventfulness:
    answers, sites = _soundscape_answers()
    return ph.environment.pleasantness_eventfulness(answers, sites=sites)


def _method_a_summary() -> ph.environment.MethodASummary:
    answers, sites = _soundscape_answers()
    return ph.environment.method_a_summary(answers, part=2, sites=sites)


def _soundscape_correlation() -> ph.environment.SoundscapeCorrelation:
    """Site pleasantness against site LAeq, five sites (ISO/TS 12913-3 A.4)."""
    return ph.environment.spearman_rank_correlation(
        [6.1, 4.8, 1.2, -2.5, -4.0], [52.0, 55.5, 61.0, 66.5, 70.0]
    )


def _method_b_summary() -> ph.environment.MethodBSummary:
    ratings = np.array(
        [
            [2.1, 1.4, 4.2, 4.0],
            [2.6, 1.9, 3.8, 3.5],
            [3.9, 3.6, 2.4, 2.2],
            [4.3, 3.1, 2.0, 1.6],
        ]
    )
    return ph.environment.method_b_summary(
        ratings, sites=["park", "park", "road", "road"]
    )


def _source_ranking() -> ph.environment.SourceRanking:
    return ph.environment.method_b_source_ranking(
        [
            ["birds", "water", "voices"],
            ["water", "birds"],
            ["traffic", "voices"],
            ["traffic"],
        ],
        sites=["park", "park", "road", "road"],
    )


def _binaural_indicators() -> ph.environment.BinauralIndicators:
    """One second of noise at two ears, the right 4 dB down (ISO/TS 12913-3 D.2)."""
    import warnings

    left = 0.1 * np.random.default_rng(12913).standard_normal(FS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ph.environment.SoundscapeWarning)
        return ph.environment.binaural_indicators(
            np.vstack([left, 10.0 ** (-4.0 / 20.0) * left]),
            FS,
            parameters="sound_pressure_level",
        )


def _directivity_factor() -> ph.metrology.DirectivityFactor:
    """Two planes of 10° readings round a mildly directional meter (IEC 61183)."""
    phi = np.radians(np.arange(36) * 10.0)
    horizontal = 94.0 + 20.0 * np.log10(0.6 + 0.4 * np.cos(phi))
    vertical = 94.0 + 20.0 * np.log10(0.7 + 0.3 * np.cos(phi))
    return ph.metrology.directivity_factor(np.vstack((horizontal, vertical)))


def _random_incidence() -> ph.metrology.RandomIncidenceSensitivity:
    """G_F and 10 lg gamma of a meter at four bands (IEC 61183 Formula (1))."""
    return ph.metrology.random_incidence_sensitivity(
        [1000.0, 2000.0, 4000.0, 8000.0],
        [0.1, 0.0, -0.3, -0.9],
        [0.05, 0.2, 0.85, 2.45],
    )


def _diffuse_field() -> ph.metrology.DiffuseFieldSensitivity:
    """A meter compared with a pressure-calibrated reference (IEC 61183 (11))."""
    return ph.metrology.diffuse_field_sensitivity(
        [1000.0, 2000.0, 4000.0, 8000.0],
        [80.2, 80.4, 80.1, 79.0],
        [80.0, 80.0, 80.0, 80.0],
        reference_pressure_level_db=-26.0,
    )


def _adjustment_value() -> ph.metrology.AdjustmentValue:
    """A meter's free-field response fitted to its tolerances (IEC 62585 A)."""
    return ph.metrology.adjustment_value(
        [125.0, 1000.0, 8000.0],
        [94.2, 94.1, 93.4],
        94.3,
        calibrator_level_db=94.0,
        tolerance_db=[1.0, 0.7, 1.5],
    )


def _free_field_correction() -> ph.metrology.FreeFieldCorrection:
    """Three microphones on a calibrator (IEC 62585 Formula (D.7))."""
    return ph.metrology.sound_calibrator_correction(
        [1000.0, 4000.0, 8000.0],
        [[94.0, 93.6, 92.9], [94.0, 93.65, 93.0], [94.0, 93.55, 92.85]],
        [94.08, 94.95, 96.6],
        [94.0, 93.1, 91.6],
        [94.0, 94.1, 94.2],
        reference_free_field_correction_db=[0.08, 0.85, 2.4],
    )


def _correction_budget() -> ph.metrology.CorrectionUncertaintyBudget:
    """The budget of IEC 62585 Table I.2, at 1 kHz."""
    values = dict.fromkeys(("a1", "a2", "a3", "a4", "a14"), 0.005)
    values.update(
        a5=0.05, a6=0.0, a7=0.06, a8=0.025, a9=0.025, a10=0.029,
        a11=0.013, a12=0.013, a13=0.0, a15=0.03,
    )  # fmt: skip
    return ph.metrology.correction_uncertainty_budget(
        values, repeatability_dof=2, frequency_hz=1000.0
    )


def _correction_verification() -> ph.metrology.CorrectionUncertaintyVerification:
    """Expanded uncertainties against the maxima of IEC 62585 clause 12."""
    return ph.metrology.verify_correction_uncertainty(
        [1000.0, 4000.0, 8000.0, 16000.0],
        [0.12, 0.2, 0.3, 0.55],
        clause=12,
        correction_range_db=[0.02, 0.05, 0.1, 0.2],
    )


def _static_airflow() -> ph.materials.StaticAirflowResult:
    u = np.array([0.2e-3, 0.4e-3, 0.6e-3, 0.8e-3, 1.0e-3])
    dp = 30000.0 * u + 4.0e6 * u**2
    return ph.materials.static_airflow_resistance(u, dp, area=0.01, thickness=0.05)


def _airborne_prediction() -> ph.building.AirbornePredictionResult:
    paths = []
    for name, rw, k_ff, k_side, lf in (
        ("floor", 49.0, 12.4, 8.9, 4.5),
        ("facade", 42.0, 12.6, 6.7, 2.55),
    ):
        ff, df, fd = ph.building.flanking_element(
            label=name,
            r_flanking=rw,
            r_separating=57.0,
            k_ff=k_ff,
            k_fd=k_side,
            k_df=k_side,
            separating_area=11.5,
            coupling_length=lf,
        )
        paths.extend((ff, df, fd))
    return ph.building.predicted_airborne_insulation(
        r_direct=57.0, flanking_paths=paths
    )


def _impact_prediction() -> ph.building.ImpactPredictionResult:
    return ph.building.predicted_impact_insulation(
        ln_w_eq=78.0, delta_l_w=17.0, k_correction=2.0
    )


def _airborne_insulation() -> ph.building.AirborneInsulationResult:
    return ph.building.airborne_insulation(
        [70.0, 72.0, 74.0],
        [40.0, 41.0, 42.0],
        [0.5, 0.5, 0.5],
        area=10.0,
        volume=50.0,
    )


def _impact_insulation() -> ph.building.ImpactInsulationResult:
    return ph.building.impact_insulation(
        [60.0, 61.0, 62.0], [0.5, 0.5, 0.5], volume=50.0
    )


#: The 16 ISO 717 rating bands and the two above them, 100 Hz to 5000 Hz.
_LAB_BANDS = [
    *(100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0),
    *(800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0),
]


def _lab_lining_improvement() -> ph.building.LabLiningImprovementResult:
    """A lining 2 dB to 19 dB better, on the heavy standard wall (ISO 10140-1 G)."""
    without = np.linspace(40.0, 65.0, 18)
    return ph.building.lab_lining_improvement(
        without, without + np.linspace(2.0, 19.0, 18), _LAB_BANDS
    )


def _reduction_improvement_rating() -> ph.building.ReductionImprovementRating:
    """The ISO 717-1 Annex D rating of that lining."""
    rating = _lab_lining_improvement().rating
    assert rating is not None
    return rating


def _lab_floor_covering_improvement() -> ph.building.LabFloorCoveringImprovementResult:
    """A covering on the lightweight reference floor No 3 (ISO 10140-1 H)."""
    bare = np.full(18, 75.0)
    return ph.building.lab_floor_covering_improvement(
        bare,
        bare - np.linspace(1.0, 30.0, 18),
        _LAB_BANDS,
        reference_floor="lightweight_3",
    )


def _heavy_impact_improvement() -> ph.building.HeavyImpactImprovementResult:
    """The rubber-ball improvement of ISO 10140-1 H.6.1 in four octaves."""
    return ph.building.heavy_impact_improvement(
        [80.0, 75.0, 70.0, 65.0], [78.0, 70.0, 62.0, 55.0], [63, 125, 250, 500]
    )


def _lining_curing_check() -> ph.building.LiningCuringCheck:
    """The G.4 example: measurements within 1 d, 3 d after construction."""
    return ph.building.check_lining_curing(3.0, 1.0)


def _rainfall_reference_correction() -> ph.building.RainfallReferenceCorrection:
    """A reference pane 1 dB to 3 dB above Table I.1 (ISO 10140-5 Annex I)."""
    return ph.building.rainfall_reference_correction(
        np.linspace(46.0, 48.0, 18), np.linspace(0.18, 0.035, 18)
    )


def _rainfall_sound() -> ph.building.RainfallSoundResult:
    """A rooflight under heavy rain, normalized (ISO 10140-1 Annex K)."""
    return ph.building.rainfall_sound(
        np.linspace(48.0, 60.0, 18),
        np.linspace(1.9, 0.85, 18),
        _LAB_BANDS,
        volume_m3=62.0,
        excited_area_m2=1.875,
        reference_correction=_rainfall_reference_correction(),
    )


def _rain_generator_verification() -> ph.building.RainGeneratorVerification:
    """A heavy-rain tank at 41 mm/h with its drops measured (ISO 10140-5 H.1)."""
    return ph.building.verify_rain_generator(
        41.0, drop_diameters_mm=np.linspace(4.2, 5.8, 20)
    )


def _low_frequency_procedure() -> ph.building.LowFrequencyResult:
    """The ISO 16283 corner procedure in a 18 m3 receiving room."""
    return ph.building.apply_low_frequency_procedure(
        [50.0, 52.0, 49.0],
        [50.0, 63.0, 80.0],
        ph.building.LowFrequencyProcedure(
            volume=18.0,
            corner_levels=[
                [56.0, 58.0, 54.0],
                [55.0, 60.0, 53.0],
                [54.0, 57.0, 56.0],
                [53.0, 56.0, 55.0],
            ],
            reverberation_63_octave=0.72,
        ),
        reverberation_time=[0.60, 0.55, 0.50],
    )


def _band_uncertainty() -> ph.building.BandUncertainty:
    return ph.building.band_uncertainty("airborne", "B")


def _intensity_wide() -> ph.emission.IntensityResult:
    """IntensityResult with band centres spanning two decades (100 Hz-10 kHz)
    so the log-axis bar-width scaling can be checked at the extremes.
    """
    freqs = np.array([100.0, 1000.0, 10000.0])
    n = freqs.size
    # 1 uW/m^2 is 60 dB re 1 pW/m^2 exactly, the level the bands and the
    # broadband total both carry here.
    return ph.emission.IntensityResult(
        frequencies=freqs,
        intensity=np.full(n, 1.0e-6),
        intensity_level=np.full(n, 60.0),
        pressure_level=np.full(n, 62.0),
        pressure_intensity_index=np.full(n, 2.0),
        direction=np.ones(n),
        bias_correction=np.ones(n),
        total_intensity=1.0e-6,
        total_intensity_level=60.0,
        total_pressure_level=62.0,
        total_pressure_intensity_index=2.0,
        total_direction=1,
        max_valid_frequency=5000.0,
    )


_ANNEX_C2_R = [
    20.4,
    16.3,
    17.7,
    22.6,
    22.4,
    22.7,
    24.8,
    26.6,
    28.0,
    30.5,
    31.8,
    32.5,
    33.4,
    33.0,
    31.0,
    25.5,
]
_ANNEX_C2_FREQS = [
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
]


def _extended_rating() -> ph.building.ExtendedWeightedRatingResult:
    return ph.building.weighted_rating_extended(
        [18.7, 19.2, 20.0, *_ANNEX_C2_R, 26.8, 29.2], _ANNEX_C2_FREQS
    )


def _extended_impact_rating() -> ph.building.ExtendedImpactRatingResult:
    li = [
        55.0,
        57.0,
        59.0,
        62.1,
        63.2,
        63.5,
        66.2,
        68.5,
        70.0,
        71.7,
        73.1,
        73.8,
        73.5,
        73.8,
        73.3,
        73.1,
        73.0,
        72.4,
        71.2,
    ]
    freqs = [
        50,
        63,
        80,
        100,
        125,
        160,
        200,
        250,
        315,
        400,
        500,
        630,
        800,
        1000,
        1250,
        1600,
        2000,
        2500,
        3150,
    ]
    return ph.building.weighted_impact_rating_extended(li, freqs)


_PANEL_BANDS = np.array(
    [
        100,
        125,
        160,
        200,
        250,
        315,
        400,
        500,
        630,
        800,
        1000,
        1250,
        1600,
        2000,
        2500,
        3150,
    ],
    dtype=float,
)


def _band_averaged_stiffness() -> ph.vibration.BandAveragedStiffness:
    """Twenty lines in each third-octave band from 100 Hz to 2 kHz, of a Kelvin-Voigt element."""
    f = np.geomspace(89.2, 2238.0, 280)
    return ph.vibration.band_averaged_stiffness(f, 1.0e6 + 1j * 2.0 * np.pi * f * 80.0)


def _effective_blocking_mass() -> ph.vibration.EffectiveBlockingMass:
    """A 20 kg block whose effective mass leaves 1 dB at f3, about 1048 Hz."""
    f = np.geomspace(20.0, 5000.0, 200)
    m_eff = 20.0 * (1.0 + (f / 3000.0) ** 2)
    ones = np.ones(f.size, dtype=complex)
    return ph.vibration.effective_blocking_mass(
        f, m_eff * ones, ones, ones, blocking_mass_kg=20.0
    )


def _driving_point_stiffness() -> ph.vibration.DrivingPointStiffnessResult:
    """A 1 MN/m spring under a 2 kg force distribution plate: f_UL near 52 Hz."""
    f = np.arange(1.0, 200.0, 0.2)
    w = 2.0 * np.pi * f
    k11 = 1.0e6 - w**2 * 2.0
    return ph.vibration.driving_point_stiffness(f, k11 * 1.0e-6, -(w**2) * 1.0e-6)


def _impact_records() -> tuple[np.ndarray, np.ndarray]:
    """Five impacts on a 2 kg, 40 Hz, 0.5 % resonator, sampled at 4096 Hz.

    A Gaussian force pulse and the resonator's acceleration, built by a
    convolution long enough that the decay never wraps round the record.
    """
    fs, n = 4096, 4096
    t = np.arange(n) / fs
    force = 100.0 * np.exp(-((t - 0.005) ** 2) / (2.0 * 5e-4**2))
    omega = 2.0 * np.pi * 40.0
    impulse = (np.exp(-0.005 * omega * t) * np.sin(omega * t)) / (2.0 * omega)
    displacement = np.convolve(force, impulse)[:n] / fs
    acceleration = np.gradient(np.gradient(displacement, 1.0 / fs), 1.0 / fs)
    rows = np.arange(1.0, 1.5, 0.1)[:, np.newaxis]
    return force * rows, acceleration * rows + 1e-3 * RNG.standard_normal((5, n))


def _impact_mobility() -> ph.vibration.ImpactMobilityResult:
    force, response = _impact_records()
    return ph.vibration.impact_mobility(
        force,
        response,
        4096.0,
        exponential_decay_rate_per_s=20.0,
        force_window_s=0.02,
        frequency_range_hz=(1.0, 800.0),
    )


def _single_mode_fit() -> ph.vibration.SingleModeFitResult:
    return _impact_mobility().fit_mode((30.0, 50.0))


def _window_correction() -> ph.vibration.ExponentialWindowCorrection:
    return ph.vibration.exponential_window_correction(
        [40.0, 125.0], [0.03, 0.02], exponential_decay_rate_per_s=5.0
    )


def _double_hit() -> ph.vibration.DoubleHitCheck:
    force, _ = _impact_records()
    return ph.vibration.check_double_hit(
        force[0] + 0.6 * np.roll(force[0], 245), 4096.0
    )


def _force_spectrum() -> ph.vibration.ForceSpectrumCheck:
    force, _ = _impact_records()
    return ph.vibration.check_force_spectrum(
        force[0], 4096.0, frequency_range_hz=(0.0, 400.0), max_drop_db=10.0
    )


def _coherence_check() -> ph.vibration.CoherenceCheck:
    return ph.vibration.check_coherence(
        _impact_mobility(), frequency_range_hz=(10.0, 400.0), exclude_hz=[(60.0, 80.0)]
    )


def _overload() -> ph.vibration.OverloadCheck:
    _, response = _impact_records()
    return ph.vibration.check_overload(response[0], 4096.0, full_scale=40.0)


def _response_decay() -> ph.vibration.ResponseDecayCheck:
    _, response = _impact_records()
    return ph.vibration.check_response_decay(response[0], 4096.0, start_s=0.02)


def _channel_match() -> ph.vibration.ChannelMatchVerification:
    f = np.geomspace(10.0, 1000.0, 60)
    return ph.vibration.verify_channel_match(
        f,
        1.0 + 0.03 * np.exp(-f / 300.0) * np.exp(0.02j),
        frequency_range_hz=(10.0, 1000.0),
    )


def _radiation_efficiency() -> ph.vibration.RadiationEfficiencyResult:
    bp = ph.vibration.plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = ph.vibration.coincidence_frequency(2500.0 * 0.006, bp)
    return ph.vibration.radiation_efficiency(_PANEL_BANDS, 1.5, 1.25, fc)


def _single_panel() -> ph.building.SoundReductionResult:
    bp = ph.vibration.plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = ph.vibration.coincidence_frequency(15.0, bp)
    return ph.building.single_panel_transmission_loss(
        _PANEL_BANDS, 15.0, critical_frequency=fc, loss_factor=0.024
    )


def _double_wall() -> ph.building.SoundReductionResult:
    return ph.building.double_wall_transmission_loss(_PANEL_BANDS, 12.0, 12.0, 0.1)


def _slit_aperture() -> ph.building.ApertureTransmissionResult:
    return ph.building.slit_transmission_coefficient(_PANEL_BANDS, 0.002, 0.1)


def _modulation() -> ph.electroacoustics.ModulationDistortionResult:
    t = np.arange(FS) / FS
    x = (
        np.sin(2 * np.pi * 250.0 * t)
        + 0.25 * np.sin(2 * np.pi * 8000.0 * t)
        + 0.02 * np.sin(2 * np.pi * 8250.0 * t)
        + 0.02 * np.sin(2 * np.pi * 7750.0 * t)
    )
    return ph.electroacoustics.modulation_distortion(x, FS, f_low=250.0, f_high=8000.0)


def _field_indicators() -> ph.emission.FieldIndicators:
    rng = np.random.default_rng(9614)
    lp = 74.0 + rng.normal(0.0, 0.8, (8, 4))
    i_n = 1.0e-5 * (1.0 + rng.normal(0.0, 0.2, (8, 4)))
    return ph.emission.field_indicators(lp, i_n, [125.0, 250.0, 500.0, 1000.0])


def _room_with_one_invalid_band() -> ph.room.RoomAcousticsResult:
    """A RoomAcousticsResult whose middle band is flagged invalid on every
    decay-time series (built directly so the test is deterministic).
    """
    freq = np.array([250.0, 500.0, 1000.0])
    ones = np.ones(3)
    valid = np.array([True, False, True])  # 500 Hz band invalid
    return ph.room.RoomAcousticsResult(
        frequencies=freq,
        edt=ones.copy(),
        t20=ones.copy(),
        t30=ones.copy(),
        c50=np.zeros(3),
        c80=np.zeros(3),
        d50=np.zeros(3),
        ts=np.zeros(3),
        dynamic_range=np.array([60.0, 5.0, 60.0]),
        edt_valid=valid.copy(),
        t20_valid=valid.copy(),
        t30_valid=valid.copy(),
        curvature=np.zeros(3),
    )


def _transfer_matrix() -> tuple[ph.materials.TransferMatrix, np.ndarray, float]:
    f = np.linspace(200.0, 1600.0, 40)
    rho_c = 407.0
    k = 2.0 * np.pi * f / 343.2
    tm = ph.materials.air_layer_transfer_matrix(k, 0.05, rho_c)
    return tm, f, rho_c


def _high_frequency_power() -> ph.emission.HighFrequencySoundPowerResult:
    """ISO 9295 direct method over the three thirds of the 16 kHz octave."""
    freqs = np.array([12500.0, 16000.0, 20000.0])
    room = ph.emission.room_constant_from_air_absorption(
        freqs,
        volume_m3=200.0,
        surface_area_m2=210.0,
        temperature_c=23.0,
        relative_humidity_percent=50.0,
    )
    orientations = np.array(
        [
            [62.0, 60.0, 55.0],
            [63.0, 61.0, 56.0],
            [61.5, 60.5, 54.0],
            [62.5, 59.5, 55.5],
        ]
    )
    return ph.emission.high_frequency_sound_power(
        orientations, frequencies_hz=freqs, room_constant_m2=room
    )


_FREE_FIELD_DIRECTIONS = (
    (1.0, 1.0, 1.0),
    (1.0, 1.0, 0.3),
    (0.0, 1.0, 0.5),
    (1.0, 0.0, 0.2),
    (-1.0, 0.5, 0.6),
    (0.3, -1.0, 0.8),
)
_FREE_FIELD_TARGETS: tuple[tuple[str, ...], ...] = (
    ("trihedral corner",),
    ("dihedral corner",),
    ("boundary centre",),
    ("closest boundary",),
    ("unique features",),
    (),
)


def _inverse_square_law() -> ph.emission.InverseSquareLawResult:
    """ISO 26101 deviations: six traverses, one wall reflection at 1 kHz."""
    freqs = ph.emission.qualification_frequencies_hz()
    d = np.arange(0.30, 3.0001, 0.02)
    traverses = []
    for index, direction in enumerate(_FREE_FIELD_DIRECTIONS):
        level = 90.0 - 20.0 * np.log10(d)
        grid = np.repeat(level[:, None], freqs.size, axis=1)
        grid[:, 4] += 0.5 * (index + 1) / 6.0 * np.sin(2.0 * np.pi * d / 0.343)
        traverses.append(
            ph.emission.MicrophoneTraverse.along(
                direction,
                d,
                grid,
                background_levels_db=np.full(freqs.size, 30.0),
                name=f"path {index + 1}",
                targets=_FREE_FIELD_TARGETS[index],
            )
        )
    return ph.emission.inverse_square_law_deviations(
        traverses, frequencies_hz=freqs, room="hemi-anechoic"
    )


def _source_directionality() -> ph.emission.SourceDirectionalityResult:
    """ISO 26101 Annex B: 32 positions, a gentle lobe growing with frequency."""
    freqs = ph.emission.qualification_frequencies_hz()
    positions = ph.emission.directionality_positions("hemi-anechoic")
    lobe = positions[:, 0] / 1.5
    levels = 80.0 + np.outer(lobe, np.linspace(0.3, 2.0, freqs.size))
    return ph.emission.verify_source_directionality(
        levels, frequencies_hz=freqs, room="hemi-anechoic"
    )


def _free_field_check() -> ph.emission.FreeFieldCheck:
    """ISO 3745 Annex A as amended, measured out to 2 m."""
    return ph.emission.check_free_field(
        _inverse_square_law(),
        bandwidth="discrete-frequency",
        source_directionality=_source_directionality(),
        measurement_radius_m=2.0,
        reflecting_plane_absorption_coefficient=0.03,
        reflecting_plane_margin_m=1.2,
        paths_in_working_area=True,
    )


_RSS_THIRDS = np.array(
    [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
     2500, 3150, 4000, 5000, 6300, 8000, 10000],
    dtype=float,
)  # fmt: skip


def _reference_source_calibration() -> ph.emission.ReferenceSourceCalibration:
    """ISO 6926 clause 8 over the 20 fixed positions of a 2 m hemisphere."""
    shape = 78.0 + 2.0 * np.sin(np.linspace(0.0, np.pi, _RSS_THIRDS.size))
    levels = shape[None, :] + np.linspace(-1.0, 1.0, 20)[:, None]
    return ph.emission.reference_source_calibration(
        levels, frequencies_hz=_RSS_THIRDS, arrangement="fixed"
    )


def _reference_sound_source() -> ph.emission.ReferenceSoundSourceVerdict:
    """ISO 6926 clause 5 with three repeated sound power levels."""
    calibration = _reference_source_calibration()
    repeated = calibration.sound_power_level_db[None, :] + np.array(
        [[0.08], [-0.05], [0.02]]
    )
    return ph.emission.verify_reference_sound_source(
        calibration, repeated_levels_db=repeated, supply_variation_db=0.15
    )


def _reference_source_drift() -> ph.emission.ReferenceSourceDriftResult:
    """ISO 6926 5.6.3: two checks six months apart, one band drifted."""
    reference = 80.0 + np.zeros(_RSS_THIRDS.size)
    latest = reference + np.linspace(-0.2, 0.3, _RSS_THIRDS.size)
    latest[12] += 0.5
    return ph.emission.verify_reference_source_drift(
        reference, latest, frequencies_hz=_RSS_THIRDS
    )


def _in_situ_power() -> ph.emission.InSituSoundPowerResult:
    """ISO 3747 in situ comparison at four positions, one band an upper bound."""
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    st = np.array(
        [
            [83.4, 85.0, 84.2, 81.0],
            [82.8, 84.6, 83.9, 80.4],
            [84.0, 85.9, 85.0, 81.9],
            [83.1, 85.3, 84.5, 81.3],
        ]
    )
    rss = np.array(
        [
            [81.9, 83.7, 84.9, 84.8],
            [81.2, 83.1, 84.3, 84.1],
            [82.6, 84.4, 85.5, 85.4],
            [82.1, 83.9, 85.0, 85.0],
        ]
    )
    background = np.array([70.0, 72.0, 71.0, 78.0])  # 2 kHz margin below 6 dB
    return ph.emission.sound_power_in_situ(
        st, rss, np.array([90.5, 92.5, 93.8, 94.0]), freqs, background_levels=background
    )


#: Octave bands and levels the ISO 3743 factories share.
_ISO3743_FREQS = np.array([250.0, 500.0, 1000.0, 2000.0])
_ISO3743_ST = np.array(
    [
        [83.4, 85.0, 84.2, 81.0],
        [82.8, 84.6, 83.9, 80.4],
        [84.0, 85.9, 85.0, 81.9],
    ]
)
_ISO3743_RSS = np.array(
    [
        [81.9, 83.7, 84.9, 84.8],
        [81.2, 83.1, 84.3, 84.1],
        [82.6, 84.4, 85.5, 85.4],
    ]
)


def _hard_walled_power() -> ph.emission.HardWalledSoundPowerResult:
    """ISO 3743-1 comparison at three positions, one band an upper bound."""
    background = np.array([66.0, 67.0, 66.0, 79.0])  # 2 kHz margin below 6 dB
    with pytest.warns(ph.emission.SoundPowerWarning, match="below 6 dB"):
        return ph.emission.sound_power_hard_walled(
            _ISO3743_ST, _ISO3743_RSS, np.array([90.5, 92.5, 93.8, 94.0]),
            _ISO3743_FREQS, background_levels=background, sigma_omc_db=1.0,
        )  # fmt: skip


def _hard_walled_room_check() -> ph.emission.HardWalledRoomCheck:
    """ISO 3743-1 4.4 with the 1 kHz spread over its Table 3 limit."""
    spread = np.array([1.8, 1.2, 1.9, 1.0])
    orientations = 80.0 + np.linspace(0.0, 1.0, 8)[:, None] * spread[None, :]
    return ph.emission.check_hard_walled_room(
        orientations, _ISO3743_FREQS, volume_m3=60.0, reference_box_m=[0.6, 0.5, 0.4]
    )


def _source_location_plan() -> ph.emission.SourceLocationPlan:
    """ISO 3743-2 Table 3 for six positions, with the A-weighted row."""
    survey = np.array(
        [
            [70.0, 71.0, 72.0, 70.5],
            [72.5, 69.0, 72.4, 71.0],
            [70.4, 73.0, 71.8, 70.2],
            [72.8, 70.0, 72.2, 71.4],
            [71.0, 68.5, 72.0, 70.9],
            [71.6, 72.2, 71.9, 70.6],
        ]
    )
    return ph.emission.special_room_source_locations(
        survey, _ISO3743_FREQS, a_weighted_levels=[80.0, 81.5, 79.8, 80.9, 80.2, 81.0]
    )


def _special_room_power() -> ph.emission.SpecialRoomSoundPowerResult:
    """ISO 3743-2 direct method in a 70 m3 room, Tnom = 0,73 s."""
    return ph.emission.sound_power_special_room(
        _ISO3743_ST, _ISO3743_FREQS, volume_m3=70.0, nominal_reverberation_time_s=0.73,
        background_levels=np.array([66.0, 67.0, 66.0, 60.0]), sigma_omc_db=1.0,
    )  # fmt: skip


def _special_room_reverberation() -> ph.emission.SpecialRoomReverberationCheck:
    """ISO 3743-2 6.3 on one-third octaves, one band pushed out of the limits."""
    thirds = np.array(
        [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0,
         1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0]
    )  # fmt: skip
    t = 0.7 * ph.emission.reverberation_parameter(thirds, 70.0)
    t[4] *= 1.25
    return ph.emission.check_special_room_reverberation(
        t, thirds, volume_m3=70.0, nominal_reverberation_time_s=0.7
    )


def _special_room_surfaces() -> ph.emission.SpecialRoomSurfaceCheck:
    """ISO 3743-2 6.4, five surfaces around a mean of 0,15."""
    walls = 0.15 * np.array([1.0, 1.2, 0.8, 1.1, 0.9])[:, None] * np.ones((1, 4))
    return ph.emission.check_special_room_surfaces(walls, [0.03] * 4, _ISO3743_FREQS)


def _special_room_suitability() -> ph.emission.SpecialRoomSuitabilityCheck:
    """ISO 3743-2 6.7, the 2 kHz difference beyond Table 1."""
    calibrated = np.array([90.5, 92.5, 93.8, 94.0])
    return ph.emission.check_special_room_suitability(
        calibrated + np.array([1.0, -2.0, 0.5, 3.4]), calibrated, _ISO3743_FREQS
    )


def _turbine_surface() -> ph.emission.TurbineMeasurementSurface:
    """IEC 61063: a turbine box and a generator box, as Figure 2 a draws them."""
    return ph.emission.turbine_measurement_surface(
        [
            ph.emission.TurbineReferenceBox(5.0, 3.0, 3.0, "turbine"),
            ph.emission.TurbineReferenceBox(6.0, 2.5, 2.5, "generator"),
        ]
    )


def _turbine_array() -> ph.emission.TurbineMicrophoneArray:
    """IEC 61063 key and additional positions every 2 m around that set."""
    return ph.emission.turbine_microphone_positions(
        _turbine_surface(), microphone_height_m=1.2, spacing_m=2.0
    )


def _turbine_power() -> ph.emission.TurbineSoundPowerResult:
    """IEC 61063 determination at the positions above, one overhead."""
    levels = np.array([88.0, 90.5, 91.0, 89.0, 92.5, 90.0])
    return ph.emission.turbine_sound_power(
        levels,
        surface_area_m2=_turbine_surface().area_m2,
        background_levels_db=levels - np.array([9.0, 12.0, 6.0, 15.0, 4.0, 11.0]),
        environmental_correction_db=1.8,
        overhead_mask=np.array([False, False, False, False, True, False]),
    )


def _turbine_declaration() -> ph.emission.TurbineNoiseDeclaration:
    """IEC 61063 report of the determination above at two loads."""
    return ph.emission.turbine_noise_declaration(
        {"50 %": _turbine_power(), "100 %": _turbine_power()},
        turbine="Two-box set",
        noise_control="none",
        measured_at="2026-09-25 10:00",
        tonal=False,
    )


def _immission_record(fs_hz: float = 2048.0) -> np.ndarray:
    """A two-second burst of ground vibration inside a quiet 70 s record.

    Long enough for two whole 30 s clock intervals, so the clock maxima and
    their r.m.s. are real rather than empty, and shaped so the meter has
    something to hold a maximum of.
    """
    t = np.arange(int(70.0 * fs_hz)) / fs_hz
    record = np.zeros_like(t)
    burst = (t > 20.0) & (t < 22.0)
    record[burst] = (
        4.0 * np.sin(2.0 * np.pi * 24.0 * t[burst]) * np.hanning(int(burst.sum()))
    )
    return record


def _vibration_meter_reading() -> object:
    """DIN 45669-1 5.1.6: what a meter displays for that record."""
    from phonometry.vibration.immission import measure_vibration_immission

    return measure_vibration_immission(_immission_record(), 2048.0)


def _vibration_meter_verification() -> object:
    """DIN 45669-1 Tables 2 and 3: a meter 2 % high everywhere but one point."""
    from phonometry.vibration.immission import (
        kb_weighting_response,
        verify_vibration_meter,
    )

    freqs = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0, 80.0])
    measured = np.abs(kb_weighting_response(freqs)) * 1.02
    measured[5] *= 1.15  # 31,5 Hz, outside the 10 % of the central band
    return verify_vibration_meter(freqs, measured)


def _assessment_velocity() -> object:
    """DIN 45669-1 Annex E: the same record judged for a dwelling."""
    from phonometry.vibration.immission import assess_short_term_vibration

    return assess_short_term_vibration(
        _immission_record(), 2048.0, building_class="residential"
    )


def _people_assessment() -> object:
    """DIN 4150-2 Clause 6.2: two hammers in a commercial area, decided on A_r."""
    from phonometry.vibration.immission import (
        assess_people_in_buildings,
        assessment_vibration_severity,
        guide_values,
    )

    kb_ftr = assessment_vibration_severity([0.16, 0.39], [6 * 3600.0, 1.5 * 3600.0])
    return assess_people_in_buildings(0.47, guide_values("commercial"), kb_ftr=kb_ftr)


def _train_passage() -> object:
    """DIN 45672-2: a twelve-second passage with two tones and some noise."""
    from phonometry.vibration.immission import evaluate_train_passage

    fs = 2048
    t = np.arange(12 * fs) / fs
    envelope = np.clip((t - 2.0) / 2.0, 0.0, 1.0) * np.clip((10.0 - t) / 2.0, 0.0, 1.0)
    rng = np.random.default_rng(4)
    record = envelope * (
        0.3 * np.sin(2.0 * np.pi * 40.0 * t)
        + 0.1 * np.sin(2.0 * np.pi * 63.0 * t)
        + 0.03 * rng.standard_normal(t.size)
    )
    return evaluate_train_passage(record, fs, t2_s=(3.0, 9.0))


def _sound_calibrator() -> ph.metrology.SoundCalibratorVerification:
    """IEC 60942:2017: a class 1 calibrator at 1 kHz, one environmental reading out."""
    record = ph.metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.12,
        level_uncertainty_db=0.10,
        frequency_deviation_percent=-0.1,
        frequency_uncertainty_percent=0.05,
        distortion_percent=0.8,
        distortion_uncertainty_percent=0.3,
        environmental_level_deviation_db=[0.10, 0.30],
        environmental_level_uncertainty_db=0.12,
    )
    return ph.metrology.verify_sound_calibrator(
        "1", record, nominal_frequency_hz=1000.0
    )


def _conformance_verification() -> ph.metrology.ConformanceVerification:
    """IEC 61672-1:2013 Table C.1 example 6: -0,5 dB against +1,0; -1,2 dB."""
    return ph.metrology.verify_conformance(
        -0.5, uncertainty=0.3, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5
    )


def _slm_periodic() -> ph.metrology.SoundLevelMeterPeriodicVerification:
    """IEC 61672-3:2013: a class 2 meter with A, F and S, one toneburst out."""
    record = ph.metrology.SoundLevelMeterPeriodicMeasurements(
        acoustic_weighting_deviations_db=[0.3, -1.2],
        acoustic_weighting_uncertainties_db=[0.3, 0.5],
        electrical_weighting_deviations_db={
            "A": [0.1, 0.0, 0.0, 0.0, 0.0, 0.0, -0.2, -0.6]
        },
        electrical_weighting_uncertainties_db={"A": [0.2] * 8},
        time_weighting_at_1khz_deviations_db={"S": 0.05},
        time_weighting_at_1khz_uncertainties_db={"S": 0.12},
        linearity_deviations_db=[0.0, 0.2, -0.3],
        linearity_uncertainties_db=[0.2, 0.2, 0.2],
        toneburst_responses_db={"F": [-1.1, -18.3, -32.4], "S": [-7.5, -27.8]},
        toneburst_uncertainties_db={"F": [0.2] * 3, "S": [0.2] * 2},
        high_level_stability_db=0.05,
        high_level_stability_uncertainty_db=0.12,
    )
    return ph.metrology.verify_sound_level_meter_periodic(2, record)


def _filter_periodic() -> ph.filters.FilterPeriodicVerification:
    """IEC 61260-3:2016: a class 1 one-third-octave filter, every clause graded."""
    row = [75.0, 62.0, 45.0, 20.0, 0.8, 0.3, 0.1, 0.0, 0.1, 0.2, 0.7, 19.0, 44.0, 63.0]
    row_u = [0.4, 0.4, 0.4, 0.25, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.25]
    record = ph.filters.FilterPeriodicMeasurements(
        midband_attenuations_db=[0.1, -0.2, 0.05],
        midband_uncertainties_db=[0.15, 0.15, 0.25],
        linearity_deviations_db=[0.1, 0.2, 0.3],
        linearity_levels_below_upper_db=[0.0, 20.0, 45.0],
        linearity_uncertainties_db=[0.1, 0.1, 0.2],
        relative_attenuations_db=[[*row, 76.0]],
        relative_attenuation_uncertainties_db=[[*row_u, 0.4, 0.4, 0.4]],
    )
    return ph.filters.verify_filter_periodic(1, record, fraction=3)


def _time_invariance() -> ph.filters.TimeInvarianceResult:
    """IEC 61260-1:2014 5.14: a small octave bank swept at 5 s per decade."""
    bank = ph.filters.OctaveFilterBank(48000, fraction=1, order=6, limits=[500, 2000])
    return ph.filters.verify_time_invariance(bank, seconds_per_decade=(5.0,))


def _loop_field() -> ph.electroacoustics.LoopField:
    """A 10 m by 15 m loop, its field across the short side at 1,2 m."""
    return ph.electroacoustics.rectangular_loop_field(
        4.0, 15.0, 10.0, 0.0, np.linspace(-7.0, 7.0, 57), 1.2
    )


def _loop_impedance() -> ph.electroacoustics.LoopImpedance:
    """IEC 62489-1:2010 Table B.1: the typical place of worship, 0,69 ohm and 109 uH."""
    return ph.electroacoustics.loop_impedance(0.69, 109e-6)


def _amplifier_frequency_response() -> ph.electroacoustics.AmplifierFrequencyResponse:
    """A loop amplifier rolling off below 100 Hz and above 5 kHz."""
    return ph.electroacoustics.amplifier_frequency_response(
        [50.0, 100.0, 1000.0, 5000.0, 8000.0], [0.8, 0.97, 1.0, 0.95, 0.7]
    )


def _agc_characteristic() -> ph.electroacoustics.AgcCharacteristic:
    """An automatic gain control like the one of IEC 62489-1:2010 Figure A.1."""
    return ph.electroacoustics.agc_characteristic(
        [-60.0, -50.0, -40.0, -30.0, -20.0, -10.0, 0.0],
        [-33.0, -23.0, -13.0, -3.0, 0.0, 0.0, 0.0],
    )


def _quadrature_phase_error() -> ph.electroacoustics.QuadraturePhaseError:
    """A quadrature network drifting to 85 degrees at 5 kHz."""
    return ph.electroacoustics.quadrature_phase_error(
        [100.0, 1000.0, 2000.0, 5000.0], [92.0, 90.0, 88.0, 85.0]
    )


def _neck_loop_characteristics() -> ph.electroacoustics.NeckLoopCharacteristics:
    """A passive neck loop on the jig of IEC 62489-1:2010+A1:2014 Annex E."""
    return ph.electroacoustics.neck_loop_characteristics(
        [100.0, 200.0, 1000.0, 5000.0, 8000.0],
        [-6.0, -2.0, 0.5, -1.0, -5.0],
        [31.0, 31.5, 32.0, 36.0, 42.0],
        input_voltage_v=1.0,
    )


def _neck_loop_verification() -> ph.electroacoustics.NeckLoopVerification:
    """A type 1 neck loop of the draft Amendment 2."""
    return ph.electroacoustics.verify_neck_loop(32.4, 0.94)


def _field_strength_reading() -> ph.electroacoustics.FieldStrengthReading:
    """Half a second of a 1 kHz sine at 400 mA/m on the true-RMS meter."""
    t = np.arange(FS // 2) / FS
    return ph.electroacoustics.field_strength_meter(
        0.4 * np.sqrt(2.0) * np.sin(2.0 * np.pi * 1000.0 * t), FS
    )


def _background_noise() -> ph.electroacoustics.BackgroundNoiseAssessment:
    """IEC 60118-4:2014 7.2: five points, the noisiest at -35 dB."""
    return ph.electroacoustics.assess_background_noise(
        [-52.0, -48.0, -35.0, -44.0, -50.0]
    )


def _induction_loop_verification() -> ph.electroacoustics.InductionLoopVerification:
    """IEC 60118-4:2014: four points, the response and the noise with the system on."""
    return ph.electroacoustics.verify_induction_loop_system(
        [0.5, -1.0, 2.0, -2.5],
        frequencies_hz=[100.0, 1000.0, 5000.0],
        response_db=[[-1.0, 0.0, -2.5], [0.0, 0.0, -3.4]],
        background_noise_levels_db=[-50.0, -49.0, -48.0, -51.0],
        system_noise_levels_db=[-48.0, -47.5, -47.0, -48.0],
    )


def _loop_requirement() -> ph.electroacoustics.LoopRequirement:
    """The frequency response requirement of that verdict."""
    return _induction_loop_verification().requirement("frequency_response")


def _amplifier_overload() -> ph.electroacoustics.AmplifierOverloadVerification:
    """IEC 60118-4:2014/A1:2017 10.3: the place of worship of Table B.1 on 3 A."""
    return ph.electroacoustics.verify_amplifier_overload(3.0, _loop_impedance(), 6.0)


def _maximum_output_current() -> ph.electroacoustics.MaximumOutputCurrent:
    """IEC 62489-1:2010 5.4.7: five steps of level into 0,5 ohm, rated at 1 % THD."""
    return ph.electroacoustics.maximum_output_current(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [0.1, 0.2, 0.5, 1.5, 3.0],
        load_resistance_ohm=0.5,
        rated_thd_percent=1.0,
    )
