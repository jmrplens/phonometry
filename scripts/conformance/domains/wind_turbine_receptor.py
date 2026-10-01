#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Wind turbine sound at a receptor (IEC TS 61400-11-2:2024).

**Printed tables.** Tables K.1 and K.2 are reproduced cell by cell, blanks
included; Table 7 row by row, with its fourth row read at the -10 degrees C
its frequencies belong to (see docs/ERRATA.md); Table 3, Table K.3, Tables C.1
to C.5, Table A.1 and the grid points of Figure A.1. The air attenuation of Table C.2
is checked against ISO 9613-1 twice, because it is two tables: from 125 Hz
to 200 Hz it is ISO 9613-1 at the 10 degrees C and 70 % of its caption,
evaluated at the nominal band centres (at the exact mid-band of 160 Hz,
158.5 Hz, ISO 9613-1 Table 1 prints 0.584 dB/km where the TS prints 0.59), and
from 25 Hz to 100 Hz it is the Danish statutory order's, set for 80 %, which
puts it 0.01 dB/km to 0.02 dB/km under the caption's atmosphere between
50 Hz and 100 Hz.

**Closed forms.** Equations (1) to (11), (C.1) and (J.1), the 3 dB rule of
11.7 and the selection of 9.3.2.3 on numbers worked by hand in the rows.

**The IOA reference code.** Clause 13 is the reference method of the IOA
Amplitude Modulation Working Group, and the working group published its code
with three sample series and their results. The rows reproduce the printed
results, the band sums of the sample workbook, and synthetic blocks and
periods run through the unmodified code, down to the mean and the mode of the
fundamentals it prints for the valid blocks of a rated period. On the 10 min period the TS departs
from the working group's report, and the row that shows it pins the TS.

Oracle: IEC TS 61400-11-2:2024 (Edition 1.0), the PDF page is the printed
folio plus two: Table 3 on folio 32, Table 7 on folio 45, Figure 1 on folio 54, Table A.1 and
Figure A.1 on folios 60 and 61, Tables C.1 to C.5 on folios 64 to 66, Tables
K.1 to K.3 on folios 83 to 85. IOA AMWG code v1.4
(AMWG_Deliverable_Code-1.4.PY) with its sample data; the Danish order is BEK
nr. 135 of 7 February 2019, Table 1.4.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from reference_data import wind_turbine_receptor as oracle

from phonometry import environment as env
from phonometry.environment.assessment import wind_turbine_receptor as wtr
from phonometry.environment.propagation.air_absorption import air_attenuation
from phonometry.filters import weighting_compliance

from ..registry import Outcome, count, numeric, record, register

_WT = "Wind turbine sound at a receptor (IEC TS 61400-11-2)"
_AM = "Wind turbine amplitude modulation (IEC TS 61400-11-2 clause 13)"


# ---------------------------------------------------------------------------
# Annex K
# ---------------------------------------------------------------------------
@register(
    _WT, "IEC TS 61400-11-2:2024 Table K.1", "Wind speed at 10 m from 120 m, every cell"
)
def _chk_k1() -> Outcome:
    matching = total = 0
    for alpha, row in zip(oracle.WT_K1_EXPONENTS, oracle.WT_K1_SPEEDS_10M, strict=True):
        speeds = env.power_law_wind_speed(
            np.asarray(oracle.WT_K1_SPEEDS_120M),
            height_m=10.0,
            reference_height_m=120.0,
            shear_exponent=alpha,
        )
        matching += int(np.sum(np.isclose(np.round(speeds, 1), row)))
        total += len(row)
    return count(matching, total, subject="cells of Table K.1")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table K.2",
    "Shear exponent from 10 m and 120 m, every cell and every blank",
)
def _chk_k2() -> Outcome:
    low, high = env.TYPICAL_WIND_SHEAR_EXPONENT_RANGE
    matching = total = 0
    for v10 in range(1, 16):
        for v120 in range(3, 16):
            alpha = float(
                env.wind_shear_exponent(
                    float(v120), float(v10), height_m=120.0, reference_height_m=10.0
                )
            )
            printed = oracle.WT_K2_SHEAR_EXPONENTS.get((v10, v120))
            inside = low <= alpha <= high
            total += 1
            if printed is None:
                matching += int(not inside)
            else:
                matching += int(
                    inside and math.isclose(round(alpha, 2), printed, abs_tol=1e-9)
                )
    return count(
        matching, total, subject="cells of Table K.2, the blanks outside -0.1 to 0.5"
    )


@register(
    _WT, "IEC TS 61400-11-2:2024 Table K.3", "Roughness length of four terrains, m"
)
def _chk_k3() -> Outcome:
    return record(
        oracle.WT_K3_ROUGHNESS_LENGTHS_M, dict(env.ROUGHNESS_LENGTHS_M), unit="m"
    )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 9.3.2.1 with IEC 61400-11:2012 Equation (29)",
    "Hub-height wind speed brought back to 10 m over z0ref = 0.05 m, m/s",
)
def _chk_log_profile() -> Outcome:
    v_hub = 6.0 * math.log(120.0 / 0.05) / math.log(10.0 / 0.05)
    back = env.logarithmic_wind_speed(v_hub, height_m=10.0, reference_height_m=120.0)
    return numeric(6.0, float(back), 1e-6, unit="m/s", places=6)


# ---------------------------------------------------------------------------
# Clause 10 and 11
# ---------------------------------------------------------------------------
_LEVELS = np.array([40.0, 42.0, 41.0])
_TYPE_B = np.array([0.3, 0.4, 0.5])


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Equations (1) to (5)",
    "Combined uncertainty of an energy-averaged bin of three intervals, dB",
)
def _chk_bin_uncertainty() -> Outcome:
    binned = env.bin_sound_levels(
        _LEVELS, [5.0, 5.2, 4.8], type_b_uncertainty_db=_TYPE_B
    )
    mean = 10.0 * math.log10(float(np.mean(10.0 ** (_LEVELS / 10.0))))
    s = math.sqrt(float(np.sum((_LEVELS - mean) ** 2)) / 6.0)
    u = math.sqrt(float(np.mean(_TYPE_B**2)))
    return numeric(
        math.hypot(s, u),
        float(binned.combined_uncertainty_db[0]),
        1e-6,
        unit="dB",
        places=6,
    )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Equations (6) and (7)",
    "Turbine level and its uncertainty 5 dB over the background, dB",
)
def _chk_background() -> Outcome:
    result = env.turbine_sound_levels(
        [45.0], [40.0], total_uncertainty_db=[0.8], background_uncertainty_db=[0.6]
    )
    e_t, e_b = 10.0**4.5, 10.0**4.0
    expected = {
        "L_c": 10.0 * math.log10(e_t - e_b),
        "u_c": math.hypot(0.8 * e_t, 0.6 * e_b) / (e_t - e_b),
    }
    computed = {
        "L_c": float(result.turbine_levels_db[0]),
        "u_c": float(result.turbine_uncertainty_db[0]),
    }
    worst = max(abs(computed[k] - expected[k]) for k in expected)
    return numeric(
        0.0,
        worst,
        1e-6,
        unit="dB",
        places=6,
        computed_label=f"worst deviation {worst:.2e} dB",
    )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 11.7",
    "Turbine level of a total 2 dB over the background: the suggested 3 dB correction, dB",
)
def _chk_three_db_rule() -> Outcome:
    result = env.turbine_sound_levels([42.0], [40.0])
    return numeric(39.0, float(result.turbine_levels_db[0]), 1e-6, unit="dB", places=6)


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table 3",
    "Type B uncertainty examples: typical range and standard uncertainty, dB",
)
def _chk_table3() -> Outcome:
    published = env.TYPE_B_UNCERTAINTY_EXAMPLES_DB
    printed = oracle.WT_TABLE3_TYPE_B_DB
    names = set(published) | set(printed)
    matching = sum(
        int(
            name in published
            and name in printed
            and all(
                math.isclose(a, b, abs_tol=1e-12)
                for a, b in zip(published[name], printed[name], strict=True)
            )
        )
        for name in names
    )
    return count(matching, len(names), subject="components of Table 3")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Equations (10) and (11)",
    "Combined uncertainty of a prediction over three turbines, dB",
)
def _chk_prediction() -> Outcome:
    levels = np.array([35.0, 32.0, 28.0])
    u_w = np.array([1.0, 1.5, 2.0])
    weights = 10.0 ** (levels / 10.0)
    propagated = float(np.sum(u_w * weights) / np.sum(weights))
    expected = math.sqrt(propagated**2 + 2.0**2 + 0.5**2)
    result = env.predicted_receptor_level(levels, u_w)
    return numeric(expected, result.combined_uncertainty_db, 1e-6, unit="dB", places=6)


@register(
    _WT,
    "IEC TS 61400-11-2:2024 9.3.2.3",
    "Sound relevant turbines of six at 35, 33, 32, 25, 20 and 18 dB",
)
def _chk_relevant() -> Outcome:
    result = env.sound_relevant_turbines([35.0, 33.0, 32.0, 25.0, 20.0, 18.0])
    expected = {f"turbine {i + 1}": float(i < 3) for i in range(6)}
    computed = {f"turbine {i + 1}": float(result.relevant[i]) for i in range(6)}
    return record(
        expected,
        computed,
        label="the three loudest (the other three drop the total by 0.3 dB)",
        computed_label=", ".join(str(i + 1) for i in result.indices),
    )


# ---------------------------------------------------------------------------
# Annex C
# ---------------------------------------------------------------------------
def _iso_9613_1_db_per_km(humidity: float) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return 1000.0 * np.asarray(
            air_attenuation(
                np.asarray(oracle.WT_C_BANDS_HZ),
                temperature_c=10.0,
                relative_humidity_percent=humidity,
            )
        )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table C.1",
    "Impedance classes A to H: flow resistivity, Nordtest classes and ground",
)
def _chk_table_c1() -> Outcome:
    published = env.LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES
    printed = oracle.WT_C1_IMPEDANCE_CLASSES
    letters = set(published) | set(printed)
    matching = 0
    for letter in letters:
        row = published.get(letter)
        if row is None or letter not in printed:
            continue
        sigma, nordtest, text = printed[letter]
        matching += int(
            math.isclose(row.flow_resistivity_kpa_s_m2, sigma)
            and len(row.nordtest_classes_kpa_s_m2) == len(nordtest)
            and all(
                math.isclose(a, b)
                for a, b in zip(row.nordtest_classes_kpa_s_m2, nordtest, strict=True)
            )
            and row.description == text
        )
    return count(matching, len(letters), subject="classes of Table C.1")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Tables C.2, C.3 and C.5",
    "Ground correction, air attenuation, facade insulation and the Swedish curve",
)
def _chk_c_tables() -> Outcome:
    pairs: list[tuple[object, tuple[float, ...]]] = [
        (env.LOW_FREQUENCY_GROUND_CORRECTION_DB, oracle.WT_C2_GROUND_DB),
        (env.LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM, oracle.WT_C2_ALPHA_DB_PER_KM),
        *(
            (env.LOW_FREQUENCY_FACADE_INSULATION_DB[name], row)
            for name, row in oracle.WT_C3_FACADE_DB.items()
        ),
        (tuple(env.SWEDISH_LOW_FREQUENCY_LIMITS_DB.values()), oracle.WT_C5_SWEDEN_DB),
    ]
    matching = sum(
        int(np.sum(np.isclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float))))
        for a, b in pairs
    )
    total = sum(len(b) for _, b in pairs)
    return count(matching, total, subject="cells of Tables C.2, C.3 and C.5")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table C.2 with ISO 9613-1",
    "Air attenuation at 125 Hz to 200 Hz: ISO 9613-1 at 10 degrees C and 70 % "
    "at the nominal band centres",
)
def _chk_c2_iso_70() -> Outcome:
    alpha = np.round(_iso_9613_1_db_per_km(70.0)[11:], 2)
    matching = int(np.sum(np.isclose(alpha, oracle.WT_C2_ALPHA_DB_PER_KM[11:])))
    return count(matching, 3, subject="cells of Table C.2 to 0.01 dB/km")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table C.2 with ISO 9613-1 and BEK nr. 135:2019 Table 1.4",
    "Air attenuation at 50 Hz to 100 Hz under ISO 9613-1 at 70 %, dB/km",
)
def _chk_c2_gap() -> Outcome:
    printed = np.asarray(oracle.WT_C2_ALPHA_DB_PER_KM)
    gap = np.round(_iso_9613_1_db_per_km(70.0)[7:11], 2) - printed[7:11]
    names = ("50 Hz", "63 Hz", "80 Hz", "100 Hz")
    return record(
        dict(zip(names, (0.01, 0.01, 0.02, 0.02), strict=True)),
        {n: round(float(g), 2) for n, g in zip(names, gap, strict=True)},
        unit="dB/km",
        label="0.01, 0.01, 0.02, 0.02 dB/km: the cells are the Danish order's, at 80 %",
    )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table C.2 with BEK nr. 135:2019 Table 1.4",
    "Air attenuation at 25 Hz to 100 Hz within 0.01 dB/km of ISO 9613-1 at 80 %",
)
def _chk_c2_iso_80() -> Outcome:
    printed = np.asarray(oracle.WT_C2_ALPHA_DB_PER_KM)
    at_80 = np.round(_iso_9613_1_db_per_km(80.0)[4:11], 2)
    same_as_order = bool(
        np.allclose(printed[:11], oracle.DK_BEK135_ALPHA_DB_PER_KM[:11])
    )
    matching = (
        int(np.sum(np.abs(at_80 - printed[4:11]) <= 0.01 + 1e-12))
        if same_as_order
        else 0
    )
    return count(matching, 7, subject="cells of Table C.2, the Danish order's cells")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table C.4",
    "A-weighting row, 10 Hz to 200 Hz, against IEC 61672-1:2013 Table 3",
)
def _chk_c4_a_weighting() -> Outcome:
    table = {row[0]: row[1] for row in weighting_compliance._WEIGHTING_TABLE3}
    matching = sum(
        int(
            math.isclose(wtr._A_WEIGHTING_DB[f], value, abs_tol=1e-9)
            and math.isclose(table[f], value, abs_tol=1e-9)
        )
        for f, value in zip(
            oracle.WT_C_BANDS_HZ, oracle.WT_C4_A_WEIGHTING_DB, strict=True
        )
    )
    return count(matching, len(oracle.WT_C_BANDS_HZ), subject="bands of Table C.4")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Equation (C.1)",
    "Indoor A-weighted 63 Hz level of 95 dB at 500 m from a 100 m hub, dB",
)
def _chk_c1() -> Outcome:
    slant = math.hypot(500.0, 100.0)
    expected = (
        95.0
        - 26.2
        - 10.0 * math.log10(slant**2)
        - 11.0
        + 4.3
        - 0.11 * slant / 1000.0
        - 16.6
    )
    result = env.wind_turbine_low_frequency_level(
        [95.0],
        distance_m=500.0,
        hub_height_m=100.0,
        frequencies_hz=[63.0],
        facade_insulation_db=[16.6],
    )
    indoor = result.indoor_levels_db
    computed = math.nan if indoor is None else float(indoor[0])
    return numeric(expected, computed, 1e-6, unit="dB", places=6)


# ---------------------------------------------------------------------------
# Annexes J and A, Table 7
# ---------------------------------------------------------------------------
@register(
    _WT,
    "IEC TS 61400-11-2:2024 Equation (J.1)",
    "Emergence of a 44.5 dB ambient over 41 dB, dB",
)
def _chk_emergence() -> Outcome:
    result = env.sound_emergence([44.5], [41.0])
    return numeric(3.5, float(result.emergence_db[0]), 1e-6, unit="dB", places=6)


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Figure A.1",
    "Amplitude modulation adjustment at the grid points the curve meets",
)
def _chk_figure_a1() -> Outcome:
    matching = sum(
        int(
            math.isclose(
                float(env.amplitude_modulation_adjustment(depth)), k, abs_tol=1e-12
            )
        )
        for depth, k in oracle.WT_FIGURE_A1_POINTS_DB
    )
    return count(
        matching, len(oracle.WT_FIGURE_A1_POINTS_DB), subject="points of Figure A.1"
    )


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table A.1 and A.2",
    "Tonal adjustment at each limit of the mean audibility, both step sizes",
)
def _chk_table_a1() -> Outcome:
    checks = [
        env.tonal_adjustment_from_mean_audibility(upper) == k
        for upper, k in oracle.WT_TABLE_A1
    ]
    checks.append(env.tonal_adjustment_from_mean_audibility(12.01) == 6)  # noqa: PLR2004
    checks += [
        env.tonal_adjustment_from_mean_audibility(upper, coarse=True) == k
        for upper, k in oracle.WT_A2_COARSE
    ]
    checks.append(env.tonal_adjustment_from_mean_audibility(9.01, coarse=True) == 6)  # noqa: PLR2004
    return count(sum(checks), len(checks), subject="limits of Table A.1 and A.2")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 A.1",
    "Rating level with the most severe adjustment alone, dB",
)
def _chk_rating() -> Outcome:
    result = env.wind_turbine_rating_level(
        40.0,
        tonal_adjustment_db=2.0,
        amplitude_modulation_adjustment_db=4.0,
        impulsive_adjustment_db=1.8,
    )
    return numeric(44.0, result.rating_level_db, 1e-6, unit="dB", places=6)


def _search_khz(distance: float, temperature: float, humidity: float) -> float:
    found = env.upper_tone_search_frequency(
        distance, temperature_c=temperature, relative_humidity_percent=humidity
    ).upper_frequency_hz
    # Table 7 prints the nominal 3 150 Hz band as 3,2 kHz.
    return 3.2 if math.isclose(found, 3150.0) else found / 1000.0


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table 7",
    "Upper tone search frequency, the four rows printed at their own atmosphere",
)
def _chk_table7() -> Outcome:
    matching = total = 0
    for index, (temperature, humidity, row) in enumerate(oracle.WT_TABLE7_ROWS):
        if index == oracle.WT_TABLE7_MISPRINTED_ROW:
            continue
        for distance, khz in zip(oracle.WT_TABLE7_DISTANCES_M, row, strict=True):
            matching += int(
                math.isclose(_search_khz(distance, temperature, humidity), khz)
            )
            total += 1
    return count(matching, total, subject="cells of Table 7")


@register(
    _WT,
    "IEC TS 61400-11-2:2024 Table 7, fourth row",
    "The row printed at 10 degrees C and 80 %, reproduced at -10 degrees C",
)
def _chk_table7_misprint() -> Outcome:
    _, humidity, row = oracle.WT_TABLE7_ROWS[oracle.WT_TABLE7_MISPRINTED_ROW]
    matching = sum(
        int(math.isclose(_search_khz(d, -10.0, humidity), khz))
        for d, khz in zip(oracle.WT_TABLE7_DISTANCES_M, row, strict=True)
    )
    return count(matching, len(row), subject="cells of the fourth row at -10 degrees C")


# ---------------------------------------------------------------------------
# Clause 13: the IOA reference code
# ---------------------------------------------------------------------------
def _sample_block(band: int) -> env.ModulationBlock:
    series = np.asarray(oracle.IOA_SAMPLE_SERIES_TENTHS_DB[band][:100]) / 10.0
    return env.amplitude_modulation_block(
        series, modulation_frequency_range_hz=(0.4, 0.9)
    )


def _sample_row(band: int) -> Outcome:
    prominence, frequency, depth = oracle.IOA_SAMPLE_RESULTS[band]
    block = _sample_block(band)
    computed = {
        "prominence": round(block.prominence or math.nan, 2),
        "f0": round(block.fundamental_frequency_hz or math.nan, 2),
        "AM": round(block.modulation_depth_db or math.nan, 2),
    }
    return record(
        {"prominence": prominence, "f0": frequency, "AM": depth},
        computed,
        label=f"{prominence:.2f}, {frequency:.2f} Hz, {depth:.2f} dB",
        computed_label=f"{computed['prominence']:.2f}, {computed['f0']:.2f} Hz, {computed['AM']:.2f} dB",
    )


@register(
    _AM,
    "IOA AMWG reference code v1.4, sample Sample-50_200Hz",
    "Prominence, fundamental modulation frequency and 10 s AM of band 1",
)
def _chk_sample_1() -> Outcome:
    return _sample_row(1)


@register(
    _AM,
    "IOA AMWG reference code v1.4, sample Sample-100_400Hz",
    "Prominence, fundamental modulation frequency and 10 s AM of band 2",
)
def _chk_sample_2() -> Outcome:
    return _sample_row(2)


@register(
    _AM,
    "IOA AMWG reference code v1.4, sample Sample-200_800Hz",
    "Prominence, fundamental modulation frequency and 10 s AM of band 3",
)
def _chk_sample_3() -> Outcome:
    return _sample_row(3)


@register(
    _AM,
    "IOA AMWG sample band filtering workbook",
    "A-weighted sums of seven one-third-octave bands, rounded to 0.1 dB",
)
def _chk_band_sums() -> Outcome:
    levels = np.asarray(oracle.IOA_BAND_EXAMPLE_UNWEIGHTED_TENTHS_DB) / 10.0
    matching = total = 0
    for band in (1, 2, 3):
        summed = env.amplitude_modulation_band_levels(
            levels, oracle.IOA_BAND_EXAMPLE_FREQUENCIES_HZ, band=band, weighting="Z"
        )
        tenths = np.rint(summed * 10.0).astype(int)
        matching += int(
            np.sum(tenths == np.asarray(oracle.IOA_SAMPLE_SERIES_TENTHS_DB[band]))
        )
        total += tenths.size
    return count(
        matching, total, subject="sums of the three bands, one per 100 ms sample"
    )


@register(
    _AM,
    "IOA AMWG reference code v1.4, synthetic 10 s blocks",
    "Status, prominence, fundamental and depth of nine designed blocks",
)
def _chk_synthetic_blocks() -> Outcome:
    matching = 0
    for (
        _,
        frequency_range,
        values,
        prominence,
        frequency,
        depth,
    ) in oracle.IOA_BLOCK_CASES:
        block = env.amplitude_modulation_block(
            np.asarray(values) / 10.0, modulation_frequency_range_hz=frequency_range
        )
        if depth > 0.0:
            ok = (
                block.valid
                and math.isclose(block.prominence or 0.0, prominence, rel_tol=1e-10)
                and math.isclose(
                    block.fundamental_frequency_hz or 0.0, frequency, abs_tol=1e-9
                )
                and math.isclose(block.modulation_depth_db or 0.0, depth, abs_tol=1e-10)
            )
        elif prominence > 0.0:
            ok = (
                block.status is env.ModulationBlockStatus.LOW_PROMINENCE
                and math.isclose(block.prominence or 0.0, prominence, rel_tol=1e-10)
            )
        else:
            ok = block.status is env.ModulationBlockStatus.NO_PEAK
        matching += int(ok)
    return count(matching, len(oracle.IOA_BLOCK_CASES), subject="blocks")


def _period(index: int) -> env.ModulationPeriod:
    indices = oracle.IOA_PERIOD_CASES[index][1]
    series = (
        np.concatenate([oracle.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in indices]) / 10.0
    )
    return env.amplitude_modulation_period(
        series, modulation_frequency_range_hz=oracle.IOA_PERIOD_RANGE_HZ
    )


@register(
    _AM,
    "IOA AMWG reference code v1.4, 10 min rating",
    "90th percentile of 36 valid 10 s blocks, dB",
)
def _chk_period_36() -> Outcome:
    rating = oracle.IOA_PERIOD_CASES[0][3]
    return numeric(rating or math.nan, _period(0).rating_db, 1e-6, unit="dB", places=6)


@register(
    _AM,
    "IOA AMWG reference code v1.4 with IEC TS 61400-11-2:2024 13.6.2.2",
    "A period of exactly 30 valid blocks is rated, dB",
)
def _chk_period_30() -> Outcome:
    rating = oracle.IOA_PERIOD_CASES[1][3]
    return numeric(rating or math.nan, _period(1).rating_db, 1e-6, unit="dB", places=6)


@register(
    _AM,
    "IEC TS 61400-11-2:2024 13.6.3 (the IOA code discards the period)",
    "A period of 29 valid blocks is rated 0 dB and kept, dB",
)
def _chk_period_29() -> Outcome:
    period = _period(2)
    return record(
        {"valid blocks": float(oracle.IOA_PERIOD_CASES[2][2]), "rating": 0.0},
        {"valid blocks": float(period.valid_blocks), "rating": period.rating_db},
        label="29 valid blocks, rated 0 dB (the AMWG report discards it)",
        computed_label=f"{period.valid_blocks} valid blocks, rated {period.rating_db:g} dB",
    )


@register(
    _AM,
    "IOA AMWG reference code v1.4 with IEC TS 61400-11-2:2024 13.6.3",
    "Mean and mode fundamental of a rated period, 20 of 36 valid blocks at 0.7 Hz",
)
def _chk_period_frequencies() -> Outcome:
    indices, _, _, mean, mode = oracle.IOA_PERIOD_FREQUENCY_CASE
    series = (
        np.concatenate([oracle.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in indices]) / 10.0
    )
    period = env.amplitude_modulation_period(
        series, modulation_frequency_range_hz=oracle.IOA_PERIOD_RANGE_HZ
    )
    got_mean = period.mean_modulation_frequency_hz
    got_mode = period.mode_modulation_frequency_hz
    worst = (
        math.inf
        if got_mean is None or got_mode is None
        else max(abs(got_mean - mean), abs(got_mode - mode))
    )
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="Hz",
        places=9,
        expected_label=f"mean {mean:.4f} Hz, mode {mode:.2f} Hz",
        computed_label=(
            "not rated"
            if got_mean is None or got_mode is None
            else f"mean {got_mean:.4f} Hz, mode {got_mode:.2f} Hz"
        ),
    )
