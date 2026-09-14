#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Measured insulation of enclosures and cabins (ISO 11546-1/-2, ISO 11957).

None of the three documents prints a worked numeric example, so the rows here
are the oracles they do offer, and each says which kind it is.

**Printed tables.** Table C.1 and Table C.2 of ISO 11546-2 are reproduced cell
by cell, and so are the applicability rows of Table 1 of both parts and the
printed thresholds of ISO 11957.

**Closed form.** Figure C.1 of ISO 11546-2 is a curve the annex asks the
reader to read off by eye. Solving the environmental correction of ISO 3744
for the room gives ``S_V/S = 4/((10^(K2/10) - 1) alpha)``, and the row checks
that the ratio this returns puts
:func:`phonometry.emission.environmental_correction` back on the Table C.1
limit exactly, at every absorption coefficient of Table C.2.

**Algebraic identity.** The estimated A-weighted insulation of Annex C of
part 1, Annex D of part 2 and Annex A of ISO 11957 reduces to the difference
of the A-weighted totals of the assumed spectrum with and without the
insulation. The rows check that identity, which is what pins the sign of the
A-weighting term the annexes print as an attenuation.
"""

from __future__ import annotations

import numpy as np

import phonometry as ph
from phonometry.noise_control.enclosure_insulation import (
    ROOM_ABSORPTION_ESTIMATES,
    TEST_ENVIRONMENT_REQUIREMENTS,
)

from ..registry import Outcome, count, numeric, record, register

_ENCLOSURES = "Enclosure and cabin insulation"

#: A one-third-octave spectrum over the range clause 6.2 requires.
_BANDS = np.array(
    [
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
        5000.0,
    ]
)

#: A machine spectrum to put the annex formulas on, in decibels.
_SOURCE = np.linspace(95.0, 80.0, _BANDS.size)


@register(
    _ENCLOSURES,
    "ISO 11546-1:1995 Eq. (1) / ISO 11546-2:1995 Eq. (1)",
    "D_W is the difference of the two sound power determinations, "
    "and a level shift common to both leaves it alone",
)
def _chk_sound_power_insulation_is_a_difference() -> Outcome:
    with_enclosure = _SOURCE - np.linspace(10.0, 30.0, _BANDS.size)
    plain = ph.noise_control.sound_power_insulation(
        _SOURCE, with_enclosure, frequencies=_BANDS
    )
    shifted = ph.noise_control.sound_power_insulation(
        _SOURCE + 7.5, with_enclosure + 7.5, frequencies=_BANDS
    )
    worst = float(np.max(np.abs(plain.insulation - shifted.insulation)))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB over 18 bands",
    )


@register(
    _ENCLOSURES,
    "ISO 11546-1:1995 Annex C / ISO 11546-2:1995 Annex D",
    "D_WA,e of the annex equals the difference of the two A-weighted totals "
    "computed from the same assumed spectrum",
)
def _chk_estimated_insulation_identity() -> Outcome:
    insulation = np.linspace(5.0, 35.0, _BANDS.size)
    estimate = ph.noise_control.estimated_a_weighted_insulation(
        _SOURCE, insulation, frequencies=_BANDS
    )
    res = ph.noise_control.sound_power_insulation(
        _SOURCE, _SOURCE - insulation, frequencies=_BANDS
    )
    assert res.a_weighted_insulation is not None
    return numeric(res.a_weighted_insulation, estimate, 1e-9, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11546-1:1995 Annex C / ISO 11546-2:1995 Annex D",
    "An enclosure of no insulation at all estimates exactly 0 dB, "
    "which is the sign test of the A-weighting term A_i",
)
def _chk_estimated_insulation_zero() -> Outcome:
    estimate = ph.noise_control.estimated_a_weighted_insulation(
        _SOURCE, np.zeros(_BANDS.size), frequencies=_BANDS
    )
    return numeric(0.0, estimate, 1e-12, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11546-2:1995 Figure C.1",
    "The area ratio S_V/S the closed form returns puts K_2 back on the "
    "Table C.1 limit, at every absorption coefficient of Table C.2",
)
def _chk_figure_c1_closed_form() -> Outcome:
    surface = 14.1
    limit = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3744"][0]
    assert limit is not None
    worst = 0.0
    for alpha in ROOM_ABSORPTION_ESTIMATES:
        verdict = ph.noise_control.test_environment_applicability(
            base_standard="ISO 3744",
            mean_absorption_coefficient=alpha,
            room_surface_area_m2=surface,
            measurement_surface_area_m2=surface,
        )
        assert verdict.required_area_ratio is not None
        k2 = float(
            ph.emission.environmental_correction(
                surface,
                mean_absorption_coefficient=alpha,
                room_surface=verdict.required_area_ratio * surface,
            )
        )
        worst = max(worst, abs(k2 - limit))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="dB",
        computed_label=f"max deviation {worst:.2e} dB over the 7 rows of Table C.2",
    )


@register(
    _ENCLOSURES,
    "ISO 11546-2:1995 Table C.1",
    "Environmental correction ceiling K_2 and background margin dL of the nine columns",
)
def _chk_table_c1() -> Outcome:
    printed = {
        "ISO 3743-1 dL": 6.0,
        "ISO 3744 K2": 2.0,
        "ISO 3744 dL": 6.0,
        "ISO 3746 K2": 7.0,
        "ISO 3746 dL": 3.0,
        "ISO 3747 dL": 3.0,
        "ISO 11201 K2": 2.0,
        "ISO 11201 dL": 6.0,
        "ISO 11202 K2": 7.0,
        "ISO 11202 dL": 3.0,
        "ISO 11204 K2": 7.0,
        "ISO 11204 dL": 6.0,
    }
    computed: dict[str, float] = {}
    for name, (ceiling, margin) in TEST_ENVIRONMENT_REQUIREMENTS.items():
        if ceiling is not None:
            computed[f"{name} K2"] = ceiling
        if margin is not None:
            computed[f"{name} dL"] = margin
    return record(printed, computed, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11546-2:1995 Table C.2",
    "The seven mean absorption coefficients of the room descriptions",
)
def _chk_table_c2() -> Outcome:
    printed = (0.05, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5)
    matching = sum(
        1
        for alpha in printed
        if alpha in ROOM_ABSORPTION_ESTIMATES and ROOM_ABSORPTION_ESTIMATES[alpha]
    )
    return count(matching, len(printed), subject="rows of Table C.2")


@register(
    _ENCLOSURES,
    "ISO 11546-2:1995 Table 1",
    "The survey methods give an A-weighted value only, so no band "
    "quantity may be declared from them",
)
def _chk_table_one_band_values() -> Outcome:
    rows = {
        entry.base_standard: entry
        for entry in ph.noise_control.applicable_methods(condition="in-situ")
    }
    printed = {"ISO 3744": 1.0, "ISO 3746": 0.0, "ISO 11202": 0.0, "ISO 11204": 1.0}
    computed = {name: float(rows[name].band_values) for name in printed}
    return record(
        printed,
        computed,
        label="ISO 3744 bands, ISO 3746 none, ISO 11202 none, ISO 11204 bands",
        computed_label=", ".join(
            f"{name} {'bands' if value else 'none'}" for name, value in computed.items()
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11546-1:1995 Table 1",
    "The laboratory table carries no survey-grade row, and its footnote 2 "
    "excludes the grade 3 variant of ISO 9614-1 and ISO 11204",
)
def _chk_table_one_laboratory_rows() -> Outcome:
    laboratory = ph.noise_control.applicable_methods(condition="laboratory")
    names = {entry.base_standard for entry in laboratory}
    marked = {
        entry.base_standard for entry in laboratory if entry.survey_grade_excluded
    }
    absent = {"ISO 3746", "ISO 3747", "ISO 11202"}.isdisjoint(names)
    present = {"ISO 3741", "ISO 3742", "ISO 3743-2"} <= names
    agrees = absent and present and marked == {"ISO 9614-1", "ISO 11204"}
    return count(
        3 if agrees else 0,
        3,
        subject="readings of Table 1",
        expected_label="no survey row, the three reverberation rows, footnote 2 on two",
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 Eq. (1) and Eq. (2)",
    "D_p and D'_p are the same subtraction, and only the method decides "
    "whether the answer carries the prime",
)
def _chk_cabin_equations_agree() -> Outcome:
    room = np.linspace(88.0, 80.0, _BANDS.size)
    cabin = room - np.linspace(10.0, 38.0, _BANDS.size)
    laboratory = ph.noise_control.cabin_insulation(
        room, cabin, frequencies=_BANDS, method="laboratory"
    )
    in_situ = ph.noise_control.cabin_insulation(
        room, cabin, frequencies=_BANDS, method="in-situ-loudspeaker"
    )
    worst = float(np.max(np.abs(laboratory.insulation - in_situ.insulation)))
    symbols = laboratory.symbol == "D_p" and in_situ.symbol == "D'_p"
    return numeric(
        0.0,
        worst if symbols else 1.0,
        1e-12,
        unit="dB",
        computed_label=(
            f"max absolute difference {worst:.3f} dB, "
            f"{laboratory.symbol} and {in_situ.symbol}"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 Annex A",
    "D_pA,e of the annex equals the difference of the two A-weighted totals, "
    "the same identity as the enclosure annexes",
)
def _chk_cabin_estimate_identity() -> Outcome:
    insulation = np.linspace(8.0, 40.0, _BANDS.size)
    cabin = ph.noise_control.estimated_cabin_noise_insulation(
        _SOURCE, insulation, frequencies=_BANDS
    )
    enclosure = ph.noise_control.estimated_a_weighted_insulation(
        _SOURCE, insulation, frequencies=_BANDS
    )
    return numeric(enclosure, cabin, 1e-12, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11957:1996 6.2",
    "Cabin clearance: half a wavelength at 100 Hz is 1,715 m at 343 m/s, "
    "and the 50 Hz to 80 Hz range takes a flat 2 m",
)
def _chk_cabin_clearance() -> Outcome:
    printed = {"100 Hz": 1.715, "80 Hz": 2.0, "63 Hz": 2.0, "50 Hz": 2.0}
    computed = {
        f"{frequency:g} Hz": ph.noise_control.minimum_cabin_clearance_m(frequency)
        for frequency in (100.0, 80.0, 63.0, 50.0)
    }
    return record(printed, computed, unit="m")


@register(
    _ENCLOSURES,
    "ISO 11957:1996 6.4 and 7.2.1",
    "Source-spectrum flatness: 6 dB in the 125 Hz octave, 5 dB in the "
    "250 Hz octave and 4 dB above",
)
def _chk_band_flatness_limits() -> Outcome:
    levels = np.array([80.0, 80.0, 80.0, 70.0, 70.0, 70.0, 60.0, 60.0, 60.0])
    frequencies = np.array(
        [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0]
    )
    check = ph.noise_control.check_band_flatness(levels, frequencies=frequencies)
    printed = {"125 Hz": 6.0, "250 Hz": 5.0, "500 Hz": 4.0}
    computed = {
        f"{centre:g} Hz": float(limit)
        for centre, limit in zip(
            check.octave_centres_hz.tolist(), check.limit_db.tolist(), strict=True
        )
    }
    return record(printed, computed, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11957:1996 7.2.1",
    "Source positions: at least the largest deviation of D'_p between any "
    "two positions in octave bands, three at least and six at most",
)
def _chk_source_position_criterion() -> Outcome:
    base = np.full(6, 30.0)
    spread = np.vstack([base, base + 4.5, base - 5.0])
    verdict = ph.noise_control.check_source_positions(spread)
    return numeric(
        6.0,
        float(verdict.required_positions),
        0.0,
        unit="",
        expected_label="6 positions for a 9,5 dB spread, capped at six",
        computed_label=(
            f"{verdict.required_positions} positions for "
            f"{verdict.max_octave_spread_db:.1f} dB"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 6.7",
    "The internal noise level is corrected for the background only while "
    "the margin lies between 6 dB and 10 dB",
)
def _chk_internal_noise_window() -> Outcome:
    inside = ph.noise_control.internal_noise_level(
        [60.0, 60.0, 60.0], background_level=52.0
    )
    outside = ph.noise_control.internal_noise_level(
        [60.0, 60.0, 60.0], background_level=45.0
    )
    printed = {"margin 8 dB": 60.0 + 10.0 * float(np.log10(1.0 - 10.0**-0.8))}
    printed["margin 15 dB"] = 60.0
    computed = {"margin 8 dB": inside, "margin 15 dB": outside}
    return record(printed, computed, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 11957:1996 clause 10",
    "The stated uncertainty needs a room at least 20 times the volume of "
    "the cabin, and the loudspeaker method in situ adds about 2 dB",
)
def _chk_uncertainty_conditions() -> Outcome:
    laboratory = ph.noise_control.uncertainty_conditions(
        room_volume_m3=300.0, cabin_volume_m3=15.0
    )
    loudspeaker = ph.noise_control.uncertainty_conditions(
        room_volume_m3=300.0,
        cabin_volume_m3=15.0,
        method="in-situ-loudspeaker",
    )
    printed = {"volume ratio": 20.0, "excess deviation": 2.0}
    computed = {
        "volume ratio": laboratory.volume_ratio,
        "excess deviation": float(loudspeaker.excess_standard_deviation_db or 0.0),
    }
    return record(printed, computed)
