#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Environmental noise sources: road traffic, road surfaces and wind turbines.

The CNOSSOS-EU road source of Directive 2002/49/EC Annex II 2.2 - rolling and
propulsion emission per vehicle category, the road-surface corrections and the
traffic-flow assembly - checked against the CIRCABC emission test set the
Commission publishes with the method.

The Statistical Pass-By method of ISO 11819-1 follows: the reference speeds and
weighting factors of Table 1, the expected random errors of Table 2, and the
example report of Annex E run from pass-bys to the difference from the
reference surface, with the reference surface of Annex D averaged from its
seven rows. Annex E prints its regression lines but not the pass-bys, so the
chain starts from pass-bys placed so that their least-squares line is exactly
the printed one.

The IEC 61400-11 wind-turbine quantities close the module: the apparent sound
power level referred to the rotor centre and the tonal-audibility chain, both
closed forms of the standard.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import reference_data as ref
from reference_data import statistical_pass_by as spb

import phonometry as ph

from ..registry import Outcome, count, numeric, record, register

_CNOSSOS_ROAD = "CNOSSOS-EU road source (Directive 2002/49/EC Annex II)"


def _cnossos_road_2015_inputs() -> tuple[Any, dict[str, Any]]:
    """The superseded (EU) 2015/996 Appendix F database the workbook used.

    Wrapped in ``tests/cnossos_road_oracle.py`` so this report and the test
    suite read the same database; two copies of the wrapping could drift and
    leave the two validating against different tables.
    """
    import cnossos_road_oracle as oracle

    return oracle.coefficients_2015(), oracle.surfaces_2015()


@register(
    _CNOSSOS_ROAD,
    "CIRCABC CNOSSOS-EU road emission test set",
    "Line power of the 60 committed cases of the 4 875-case published test set, 8 octave bands each, dB re 1 pW/m",
)
def _chk_cnossos_road_workbook() -> Outcome:
    """Worst per-band deviation from the published test workbook.

    The European Commission source-module test set was computed with the
    Appendix F tables of Commission Directive (EU) 2015/996, so the shipped
    equations are fed that superseded database. The workbook prints two
    decimals, hence the 0,01 dB budget.
    """
    coefficients, surfaces = _cnossos_road_2015_inputs()
    worst = 0.0
    for case in ref.cnossos_road_workbook_cases():
        traffic = [
            ph.environment.RoadTraffic(
                ph.environment.RoadVehicleCategory(c),
                float(case[f"q_{c}"]),
                float(case[f"v_{c}"]),
                studded_fraction=0.5 if c == "1" else 0.0,
            )
            for c in ("1", "2", "3", "4a", "4b")
        ]
        result = ph.environment.road_source_power(
            traffic,
            surface=surfaces[case["surface"]],
            temperature_c=float(case["temperature_c"]),
            road_slope_percent=float(case["gradient_pct"]),
            studded_months=float(case["studded_months"]),
            junction_distance=float(case["junction_distance_m"]),
            junction_type=ph.environment.JunctionType(int(case["junction_type"])),
            coefficients=coefficients,
        )
        for got, band in zip(
            result.total_line_power, ref.CNOSSOS_ROAD_BANDS, strict=True
        ):
            worst = max(worst, abs(float(got) - float(case[f"lw_{band}"])))
    return numeric(
        0.0,
        worst,
        0.01,
        unit="dB",
        places=4,
        expected_label="<= 0.01 dB on 480 published band levels (60 cases)",
    )


@register(
    _CNOSSOS_ROAD,
    "Directive (EU) 2021/1226 Annex pt (19)(a), Table F-1",
    "Rolling and propulsion coefficients, 5 categories x 4 rows x 8 bands",
)
def _chk_cnossos_road_table_f1() -> Outcome:
    bad = 0
    for category, expected in ref.CNOSSOS_ROAD_TABLE_F1.items():
        pairs = (
            (
                ph.environment.ROAD_COEFFICIENTS.rolling_a[category],
                expected["AR"],
            ),
            (
                ph.environment.ROAD_COEFFICIENTS.rolling_b[category],
                expected["BR"],
            ),
            (
                ph.environment.ROAD_COEFFICIENTS.propulsion_a[category],
                expected["AP"],
            ),
            (
                ph.environment.ROAD_COEFFICIENTS.propulsion_b[category],
                expected["BP"],
            ),
        )
        bad += sum(
            1 for got, want in pairs for a, b in zip(got, want, strict=True) if a != b
        )
    return count(
        160 - bad,
        160,
        subject="coefficients",
        expected_label="160 coefficients identical",
    )


@register(
    _CNOSSOS_ROAD,
    "Directive (EU) 2021/1226 Annex pt (19)(b), Table F-4",
    "Road-surface coefficients, 15 surfaces x 5 categories x (8 alpha + beta)",
)
def _chk_cnossos_road_table_f4() -> Outcome:
    bad = 0
    for surface in ph.environment.RoadSurface:
        row = ph.environment.road_surface_coefficients(surface)
        expected = ref.CNOSSOS_ROAD_TABLE_F4[surface.value]
        for category in ("1", "2", "3", "4a", "4b"):
            key = category if category in expected else "4a/4b"
            bad += sum(
                1
                for a, b in zip(row.alpha[category], expected[key][0], strict=True)
                if a != b
            )
            bad += int(row.beta[category] != expected[key][1])
    return count(
        675 - bad,
        675,
        subject="stored coefficients",
        expected_label="675 stored coefficients identical",
    )


@register(
    _CNOSSOS_ROAD,
    "Directive (EU) 2015/996 Appendix F, Tables F-2 and F-3",
    "Studded-tyre and junction coefficients, unchanged since 2015",
)
def _chk_cnossos_road_tables_f2_f3() -> Outcome:
    bad = sum(
        1
        for got, want in (
            (
                ph.environment.ROAD_COEFFICIENTS.studded_a,
                ref.CNOSSOS_ROAD_TABLE_F2["ai"],
            ),
            (
                ph.environment.ROAD_COEFFICIENTS.studded_b,
                ref.CNOSSOS_ROAD_TABLE_F2["bi"],
            ),
        )
        for a, b in zip(got, want, strict=True)
        if a != b
    )
    for category, expected in ref.CNOSSOS_ROAD_TABLE_F3.items():
        bad += int(
            ph.environment.ROAD_COEFFICIENTS.junction_c[category]
            != (expected[1], expected[2])
        )
    return count(
        36 - bad,
        36,
        subject="coefficients",
        expected_label="36 coefficients identical",
    )


@register(
    _CNOSSOS_ROAD,
    "Directive (EU) 2015/996 Annex II 2.2.4 / 2.2.11",
    "Sound power at v_ref = 70 km/h under reference conditions, dB re 1 pW",
)
def _chk_cnossos_road_reference_conditions() -> Outcome:
    """At the reference conditions every correction vanishes identically, so
    the rolling and propulsion powers are the Table F-1 coefficients A_R, A_P.
    """
    worst = 0.0
    for category in ("1", "2", "3", "4a", "4b"):
        rolling = ph.environment.road_rolling_noise(category, 70.0)
        propulsion = ph.environment.road_propulsion_noise(category, 70.0)
        for got, want in (
            (rolling, ph.environment.ROAD_COEFFICIENTS.rolling_a[category]),
            (
                propulsion,
                ph.environment.ROAD_COEFFICIENTS.propulsion_a[category],
            ),
        ):
            worst = max(
                worst, max(abs(float(a) - b) for a, b in zip(got, want, strict=True))
            )
    return numeric(
        0.0,
        worst,
        0.0,
        unit="dB",
        places=6,
        expected_label="exactly A_R,i,m and A_P,i,m",
    )


@register(
    _CNOSSOS_ROAD,
    "Directive (EU) 2021/1226 Annex pt (8)(b)",
    "Octave-band A-weighting AWC_f,i prescribed by 2.5.5, dB",
)
def _chk_cnossos_a_weighting() -> Outcome:
    bad = sum(
        1
        for a, b in zip(
            ph.environment.CNOSSOS_A_WEIGHTING,
            ref.CNOSSOS_A_WEIGHTING_TABLE,
            strict=True,
        )
        if a != b
    )
    return count(
        8 - bad,
        8,
        subject="values",
        expected_label="8 values identical",
    )


# ===========================================================================
# Wind-turbine noise (IEC 61400-11)
# ===========================================================================
_WIND_TURBINE = "Wind-turbine noise (IEC 61400-11)"


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formula 30",
    "Critical bandwidth about a 500 Hz tone, Hz",
)
def _chk_wt_critical_bandwidth() -> Outcome:
    from phonometry.environment.sources.wind_turbine import critical_bandwidth

    expected = 25.0 + 75.0 * (1.0 + 1.4 * (500.0 / 1000.0) ** 2) ** 0.69
    return numeric(expected, critical_bandwidth(500.0), 1e-6, unit="Hz", places=3)


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formula 26",
    "Apparent sound power level of a single band, dB re 1 pW",
)
def _chk_wt_apparent_power() -> Outcome:
    r1 = 150.0
    expected = 100.0 - 6.0 + 10.0 * math.log10(4.0 * math.pi * r1**2)
    return numeric(
        expected,
        ph.environment.apparent_sound_power_level([100.0], r1),
        1e-4,
        unit="dB",
        places=4,
    )


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formulae 31-34",
    "Tonal audibility of a synthetic clean tone, dB",
)
def _chk_wt_tonal_audibility() -> Outcome:
    df = 2.0
    freqs = np.arange(440.0, 560.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[int(np.argmin(np.abs(freqs - 500.0)))] = 60.0
    res = ph.environment.wind_turbine_tonality(levels, freqs)
    return numeric(16.38, res.tonal_audibility, 6e-2, unit="dB", places=2)


# ===========================================================================
# Road surfaces: the Statistical Pass-By method (ISO 11819-1)
# ===========================================================================
_ROAD_SURFACE = "Road-surface influence on traffic noise (ISO 11819-1)"

#: The Annex E site: a medium-speed road, cars at 80 km/h and heavy vehicles
#: at 70 km/h.
_SPB_ROAD = spb.ANNEX_E_ROAD_SPEED_CATEGORY


def _given(value: float | None) -> float:
    """A value the call was given the inputs for, which cannot be missing."""
    if value is None:
        msg = "the corrected levels were passed, so the corrected value exists."
        raise ValueError(msg)
    return value


def _spb_annex_e(**options: Any) -> ph.environment.StatisticalPassByResult:
    """The method run on pass-bys whose lines are the Annex E ones."""
    categories: list[str] = []
    speeds: list[float] = []
    levels: list[float] = []
    for category in ph.environment.SPB_VEHICLE_CATEGORIES:
        v, level = spb.annex_e_pass_bys(category)
        categories += [category] * len(v)
        speeds += v
        levels += level
    return ph.environment.statistical_pass_by(
        categories, speeds, levels, road_speed_category=_SPB_ROAD, **options
    )


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 Table 1",
    "Reference speeds and weighting factors, 3 road speed categories x 3 "
    "vehicle categories x 2",
)
def _chk_spb_table_1() -> Outcome:
    printed = [
        (spb.TABLE_1_REFERENCE_SPEEDS_KMH, ph.environment.SPB_REFERENCE_SPEEDS_KMH),
        (spb.TABLE_1_WEIGHTING_FACTORS, ph.environment.SPB_WEIGHTING_FACTORS),
    ]
    cells = [
        (float(table[road][category]), float(published[road][category]))
        for table, published in printed
        for road in table
        for category in table[road]
    ]
    matching = sum(1 for want, got in cells if math.isclose(want, got, abs_tol=0.0))
    return count(matching, len(cells), subject="printed cells")


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 Table 2",
    "Expected random errors: standard deviation of individual vehicles and "
    "95 % confidence interval around L_veh, 3 vehicle categories, dB",
)
def _chk_spb_table_2() -> Outcome:
    printed = {
        **{f"s {k}": v for k, v in spb.TABLE_2_STANDARD_DEVIATIONS_DB.items()},
        **{f"CI {k}": v for k, v in spb.TABLE_2_CONFIDENCE_INTERVALS_DB.items()},
    }
    published = {
        **{
            f"s {k}": v
            for k, v in ph.environment.SPB_VEHICLE_STANDARD_DEVIATIONS_DB.items()
        },
        **{f"CI {k}": v for k, v in ph.environment.SPB_CONFIDENCE_INTERVALS_DB.items()},
    }
    return record(printed, published, unit="dB")


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 Annex E, regression data",
    "L_veh of cars, dual-axle and multi-axle heavy vehicles at 80 and 70 km/h, "
    "from pass-bys on the printed regression lines, reported to one decimal, dB",
)
def _chk_spb_annex_e_vehicle_levels() -> Outcome:
    result = _spb_annex_e()
    return record(
        spb.ANNEX_E_VEHICLE_SOUND_LEVELS_DB,
        dict(result.reported_vehicle_sound_levels_db),
        unit="dB",
    )


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 9.5 and Annex E",
    "SPBI not corrected for temperature, from the three L_veh as Annex E "
    "prints them (78,5, 81,1 and 83,8 dB), dB",
)
def _chk_spb_annex_e_index() -> Outcome:
    result = _spb_annex_e()
    index = ph.environment.statistical_pass_by_index(
        result.reported_vehicle_sound_levels_db, road_speed_category=_SPB_ROAD
    )
    return numeric(spb.ANNEX_E_INDEX_DB, index, 0.05, unit="dB", places=3)


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 9.5 and Annex E",
    "SPBI corrected for temperature, from the corrected L_veh Annex E prints, dB",
)
def _chk_spb_annex_e_corrected_index() -> Outcome:
    result = _spb_annex_e(
        corrected_vehicle_sound_levels_db=spb.ANNEX_E_CORRECTED_VEHICLE_SOUND_LEVELS_DB
    )
    return numeric(
        spb.ANNEX_E_CORRECTED_INDEX_DB,
        _given(result.corrected_index_db),
        0.05,
        unit="dB",
        places=3,
    )


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 clause 10 and Annex E",
    "Difference of the temperature-corrected SPBI from the 77,3 dB of the "
    "reference surface, dB",
)
def _chk_spb_annex_e_difference() -> Outcome:
    result = _spb_annex_e(
        corrected_vehicle_sound_levels_db=spb.ANNEX_E_CORRECTED_VEHICLE_SOUND_LEVELS_DB,
        reference_db=spb.ANNEX_E_REFERENCE_INDEX_DB,
    )
    return numeric(
        spb.ANNEX_E_DIFFERENCE_DB,
        _given(result.corrected_difference_db),
        0.05,
        unit="dB",
        places=3,
    )


@register(
    _ROAD_SURFACE,
    "ISO 11819-1:1997 10.2 and Annex D",
    "L_veh of the normalized reference surface for the medium speed range, "
    "the average of the seven surfaces printed, to one decimal, dB",
)
def _chk_spb_annex_d_reference() -> Outcome:
    averaged = ph.environment.normalized_reference_levels(spb.ANNEX_D_SURFACES_DB)
    return record(
        spb.ANNEX_D_AVERAGE_DB,
        {key: round(value, 1) for key, value in averaged.items()},
        unit="dB",
    )
