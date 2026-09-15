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

**Borrowed numbers.** Two clauses of ISO 11957 compute nothing of their own:
6.4 sends the background correction to ISO 3741 and clause 8 sends the single
number to ISO 717-1, which is why the printed arithmetic of those two
documents is an oracle of these two clauses. Three accredited laboratories
have published cabin measurements rated to clause 8, and Example 7-8 of Barron
carries the A-weighted sum of Annex A through a spectrum of its own. The last
group of rows is those, each naming the document its numbers come from and the
clause of ISO 11957 that makes it applicable, because neither half is the
citation on its own.

**Measured in real rooms.** Annex C of ISO 11546-2 asks whether the room an
enclosure stands in is good enough for the base standard, and nothing inside
the document answers that with a number. Two studies do. A 1996 campaign at
the National Physical Laboratory took a reference sound source through five
rooms on its site and printed the environmental correction of each three ways,
measured, from the reverberation time and from a coefficient read off the
table of room descriptions; a 2024 study at BAuA had three test engineers
assess one workroom and printed what each assessment decides about it. A
German guidance sheet adds the A-weighted level at a workstation before and
after two enclosures were built around the machine. Those rows name the room,
the page and the printed folio, and one of them records the column of the 1996
study that must not be used, because it does not follow that study's own
equation.
"""

from __future__ import annotations

import numpy as np
import reference_data as ref

import phonometry as ph
from phonometry.noise_control.enclosure_insulation import (
    ROOM_ABSORPTION_ESTIMATES,
    TEST_ENVIRONMENT_REQUIREMENTS,
)

from ..registry import Outcome, count, mask, numeric, record, register

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


#: ISO 11546-2:1995, Annex C, Table C.2, "Approximate values of the mean sound
#: absorption coefficient, alpha, for different room configurations", printed
#: folio 13 (PDF page 17), read on the printed page. Both columns are
#: transcribed, because the description is the whole of what this table says:
#: the coefficient is only its key. The same seven rows and the same wording
#: are printed in BS EN ISO 11546-2:2009, printed folio 13 (PDF page 19).
#:
#: The 2010 editions of the sound power standards print a longer table under
#: the same title and it is not this one, so it cannot stand in for it: ISO
#: 3744:2010 Table A.1 (printed folio 36) and ISO 3746:2010 Table A.1 (printed
#: folio 24) carry eight rows, adding 0,30 for a room with an absorbing ceiling
#: and bare walls, and reword two of the seven below.
_TABLE_C2: dict[float, str] = {
    0.05: (
        "Nearly empty room with smooth hard walls made of concrete, brick, "
        "plaster or tile"
    ),
    0.1: "Partly empty room; room with smooth walls",
    0.15: "Room with furniture; rectangular machinery room; rectangular industrial room",
    0.2: (
        "Irregularly shaped room with furniture; irregularly shaped machinery "
        "room or industrial room"
    ),
    0.25: (
        "Room with upholstered furniture; machinery or industrial room with a "
        "small amount of sound-absorbing material on ceiling or walls "
        "(e.g. partially absorptive ceiling)"
    ),
    0.35: "Room with sound-absorbing materials on both ceiling and walls",
    0.5: "Room with large amounts of sound-absorbing materials on ceiling and walls",
}


@register(
    _ENCLOSURES,
    "ISO 11546-2:1995 Table C.2",
    "The seven room descriptions, word for word, under the mean absorption "
    "coefficient each of them is printed against",
)
def _chk_table_c2() -> Outcome:
    matching = sum(
        1
        for alpha, description in _TABLE_C2.items()
        if ROOM_ABSORPTION_ESTIMATES.get(alpha) == description
    )
    return count(matching, len(_TABLE_C2), subject="rows of Table C.2")


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


# ---------------------------------------------------------------------------
# Oracles from outside the three standards.
#
# ISO 11546-2 prints no worked example, so the rows below take their numbers
# from five documents that measured or worked the same quantities and owe
# nothing to this library: a 1996 measurement campaign in five real rooms at
# the National Physical Laboratory, a 2024 BAuA study of one workroom, two
# textbook worked examples and a German guidance sheet on realised enclosures.
# Each row names the document, its edition, the PDF page and the printed folio.
# ---------------------------------------------------------------------------

#: Table 8 of the NPL study, printed folio 15: the area of each measurement
#: surface the reference sound source was measured over, in square metres.
#: Surfaces 1 and 2 have the same area, so every quantity computed from area
#: alone comes out the same for both, which the printed tables confirm.
_NPL_SURFACE_M2: dict[int, float] = {1: 14.1, 2: 14.1, 3: 28.2, 4: 49.6}

#: Table 9, printed folio 16: for each of the five rooms, the area of its
#: boundary surfaces, its volume, the A-weighted reverberation time and the two
#: ends of the range of mean absorption coefficients the report reads off the
#: table of room descriptions in Annex A of ISO 3744:1994 and ISO 3746:1995,
#: the editions its references 4 and 5 name. The report reproduces that table
#: as its Table 1, seven rows that are Table C.2 of ISO 11546-2 under another
#: name; the 2010 editions print a different one, as the comment on
#: ``_TABLE_C2`` says. Rooms A and E are given a single coefficient rather
#: than a range.
_NPL_ROOMS: dict[str, tuple[float, float, float, float, float]] = {
    # S_V in m2, V in m3, T (A-weighted) in s, alpha from, alpha to
    "A": (134.0, 91.5, 0.2, 0.5, 0.5),
    "B": (168.0, 116.0, 0.5, 0.1, 0.25),
    "C": (373.0, 428.0, 1.3, 0.1, 0.25),
    "D": (834.0, 1188.0, 1.0, 0.2, 0.5),
    "E": (358.0, 274.0, 2.3, 0.05, 0.05),
}

#: Tables 10 to 14, printed folios 18 to 20, ``absolute`` row: the measured
#: K_2A of each room and measurement surface, in decibels, against the 90,9 dB
#: re 1 pW the reference sound source was calibrated to under ISO 6926. This is
#: a measurement, not an evaluation of a formula, and it is the ground truth
#: the applicability rows below are judged against.
_NPL_MEASURED_K2A: dict[str, dict[int, float]] = {
    "A": {1: 0.0, 2: 0.6, 3: 1.0, 4: 1.1},
    "B": {1: 3.3, 2: 3.4, 3: 4.3},
    "C": {1: 3.4, 2: 3.5, 3: 5.1},
    "D": {1: 0.3, 2: 0.9, 3: 1.3, 4: 1.9},
    "E": {1: 5.2, 2: 5.5, 3: 7.7},
}

#: The same tables, ``reverberation (A-wt)`` row: K_2A as the authors computed
#: it from their Eq. (3), K_2 = 10 lg (1 + 4 S/A), with the room absorption of
#: their Eq. (5), A = 0,16 V/T. That is the pair ISO 3744 prints as Eq. (A.2)
#: and Eq. (A.3), and the pair ISO 11546-2 leans on through Annex C.
_NPL_REVERBERATION_K2A: dict[str, dict[int, float]] = {
    "A": {1: 2.5, 2: 2.5, 3: 4.0, 4: 5.7},
    "B": {1: 4.0, 2: 4.0, 3: 6.0},
    "C": {1: 3.2, 2: 3.2, 3: 5.0},
    "D": {1: 1.1, 2: 1.1, 3: 2.0, 4: 3.1},
    "E": {1: 5.9, 2: 5.9, 3: 8.4},
}

#: The same tables, ``estimated room absorption`` row, as the two bounds each
#: cell prints; the lower bound goes with the upper end of the absorption
#: range. These are printed values, and they are deliberately **not** used to
#: check anything here: they do not follow the report's own Eq. (3), which is
#: what :func:`_chk_npl_estimated_absorption_drops_the_factor_four` records so
#: that the exclusion is not quietly reversed later.
_NPL_ESTIMATED_K2A: dict[str, dict[int, tuple[float, float]]] = {
    "A": {1: (0.8, 0.8), 2: (0.8, 0.8), 3: (1.5, 1.5), 4: (2.4, 2.4)},
    "B": {1: (1.3, 2.6), 2: (1.3, 2.6), 3: (2.2, 4.3)},
    "C": {1: (0.6, 1.3), 2: (0.6, 1.3), 3: (1.1, 2.3)},
    "D": {1: (0.1, 0.4), 2: (0.1, 0.4), 3: (0.3, 0.7), 4: (0.1, 1.1)},
    "E": {1: (2.7, 2.7), 2: (2.7, 2.7), 3: (4.3, 4.3)},
}

#: Table 3 of the BAuA study, printed folio 186: what three test engineers of
#: different experience assessed for one and the same workroom, as mean
#: absorption coefficient and boundary surface area in square metres, followed
#: by the K_2A each assessment yields on the two reference measurement surfaces
#: the same folio defines. The table's fourth column holds column means rather
#: than a fourth assessment, so it is not a case and is not listed here.
_BAUA_ENGINEERS: dict[str, tuple[float, float, float, float]] = {
    # alpha, S_V in m2, K_2A at 0,5 m, K_2A at 1 m
    "Test Eng. 1": (0.15, 174.0, 7.1, 9.2),
    "Test Eng. 2": (0.15, 173.0, 7.1, 9.3),
    "Test Eng. 3": (0.30, 174.3, 4.9, 6.7),
}

#: Folio 186 again: the reference measurement surface for a workstation 0,5 m
#: from the machine, and for one at 1 m, in square metres.
_BAUA_SURFACES_M2: tuple[float, float] = (26.9, 48.3)

#: Table 4, printed folio 187: the equivalent absorption area each of the two
#: rooms was measured to have with a reference sound source, in square metres,
#: then the K_2A computed from it at 0,5 m, at 1 m and on the 25,1 m2
#: measurement surface the source itself stood on. Only these rows of the
#: table are used: its L_pA(in situ) cell for the former reverberation room,
#: 81,08 dB, does not fit the 97,7 m2 beside it through the author's own
#: Eq. (9), which would need 79,74 dB, so that cell is left alone.
_BAUA_DIRECT: dict[str, tuple[float, float, float, float]] = {
    # A in m2, K_2A at 0,5 m, K_2A at 1 m, K_2A on the 25,1 m2 surface
    "workroom": (55.2, 4.7, 6.5, 4.5),
    "former reverberation room": (97.7, 3.2, 4.7, 3.1),
}

#: Folio 187: the measurement surface the direct method used, in square metres,
#: printed rounded from the 2 m hemisphere the text defines.
_BAUA_DIRECT_SURFACE_M2 = 25.1

#: Example 1.13 of Peters, Smith and Hollins, printed p. 16: two machines
#: measured at one reception point in octave bands, and the attenuation of one
#: enclosure, all in decibels. The example carries its own A-weighting, the
#: ISO 3744 Annex E values rounded to whole decibels; this library uses the
#: unrounded table, and both reach the printed integer answers.
_SMITH_BANDS_HZ = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_SMITH_ATTENUATION_DB = np.array([4.0, 9.0, 15.0, 21.0, 24.0, 30.0, 27.0, 26.0])

#: The two source spectra of that example and the A-weighted attenuation the
#: answer box on printed p. 17 gives for each, in decibels.
_SMITH_MACHINES: dict[str, tuple[list[float], float]] = {
    "machine A": ([105.0, 107.0, 99.0, 94.0, 91.0, 87.0, 82.0, 79.0], 14.0),
    "machine B": ([68.0, 79.0, 82.0, 87.0, 92.0, 96.0, 89.0, 81.0], 27.0),
}

#: The two installed enclosures of the IFA guidance sheet whose A-weighted
#: level is printed both before and after, in decibels: Beispiel 1 on printed
#: folio 22, and Beispiel 3 with its level before on folio 23 and after on
#: folio 25. Its second example is left out: the level with the enclosure in
#: place is never printed there, so the only way to feed it is to subtract the
#: printed 21 dB from the printed 95 dB, which is the answer run backwards.
_IFA_ENCLOSURES: dict[str, tuple[float, float, float]] = {
    # without, with, the printed reduction, all in dB(A)
    "punching machine, Beispiel 1": (100.0, 80.0, 20.0),
    "emery machine, Beispiel 3": (104.0, 84.0, 20.0),
}


@register(
    _ENCLOSURES,
    "NPL CIRA(EXT) 009 (1996) Tables 8 to 14, PDF pp. 19 to 24, "
    "printed folios 15 to 20",
    "The environmental correction taken from a room's printed volume and "
    "A-weighted reverberation time reproduces all 17 values measured in five "
    "real rooms",
)
def _chk_npl_reverberation_k2a() -> Outcome:
    # A tenth of a decibel, not a twentieth: the study prints its answers to
    # 0,1 dB and prints the volume and the reverberation time it fed them
    # rounded as well, so the inputs carry rounding of their own.
    worst = 0.0
    matching = 0
    total = 0
    for room, printed in _NPL_REVERBERATION_K2A.items():
        _, volume_m3, time_s, _, _ = _NPL_ROOMS[room]
        for surface, want in printed.items():
            total += 1
            got = float(
                ph.emission.environmental_correction(
                    _NPL_SURFACE_M2[surface],
                    reverberation_time=time_s,
                    volume=volume_m3,
                )
            )
            if abs(got - want) <= 0.1:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of K_2A, from 1,1 dB to 8,4 dB",
        expected_label=f"17/17 (worst departure {worst:.2f} dB)",
    )


@register(
    _ENCLOSURES,
    "NPL CIRA(EXT) 009 (1996) Tables 9 to 14, PDF pp. 20 to 24, "
    "printed folios 16 to 20",
    "Annex C calls a room fit for ISO 3746 exactly where the measured "
    "environmental correction stays under the 7 dB of Table C.1, in all 17 "
    "configurations",
)
def _chk_npl_annex_c_against_the_measurement() -> Outcome:
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3746"][0]
    assert ceiling is not None
    matching = 0
    total = 0
    for room, printed in _NPL_MEASURED_K2A.items():
        room_surface_m2, _, _, _, alpha = _NPL_ROOMS[room]
        for surface, measured in printed.items():
            total += 1
            verdict = ph.noise_control.test_environment_applicability(
                base_standard="ISO 3746",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=_NPL_SURFACE_M2[surface],
            )
            matching += int(verdict.applicable is (measured <= ceiling))
    return count(
        matching,
        total,
        subject="verdicts that agree with the measurement",
        expected_label="17/17, reading the absorption at the upper end of each "
        "printed range",
    )


@register(
    _ENCLOSURES,
    "NPL CIRA(EXT) 009 (1996) Tables 9 to 14, PDF pp. 20 to 24, "
    "printed folios 16 to 20",
    "At the 2 dB ceiling ISO 3744 is given, the annex agrees with 13 of the "
    "same 17 measurements, and the four it refuses are the hemi-anechoic room "
    "the report says the table of room descriptions cannot reach",
)
def _chk_npl_annex_c_at_the_precision_ceiling() -> Outcome:
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3744"][0]
    assert ceiling is not None
    matching = 0
    differing: list[str] = []
    for room, printed in _NPL_MEASURED_K2A.items():
        room_surface_m2, _, _, _, alpha = _NPL_ROOMS[room]
        for surface, measured in printed.items():
            verdict = ph.noise_control.test_environment_applicability(
                base_standard="ISO 3744",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=_NPL_SURFACE_M2[surface],
            )
            if verdict.applicable is (measured <= ceiling):
                matching += 1
            else:
                differing.append(f"{room}{surface}")
    return numeric(
        13.0,
        float(matching),
        0.0,
        expected_label="13 of 17, the four that differ being room A, which is "
        "hemi-anechoic and so more absorbent than the 0,5 the table stops at",
        computed_label=f"{matching} of 17, differing at {', '.join(differing)}",
    )


@register(
    _ENCLOSURES,
    "NPL CIRA(EXT) 009 (1996) Tables 6 and 9, PDF pp. 15 and 20, "
    "printed folios 11 and 16",
    "Room E is printed with two different boundary areas, and only the one "
    "Table 9 pairs with the volume and the reverberation time puts the annex "
    "back on the measurement",
)
def _chk_npl_room_e_area_conflict() -> Outcome:
    measured = _NPL_MEASURED_K2A["E"]
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 3746"][0]
    assert ceiling is not None
    agreeing: dict[float, int] = {}
    for room_surface_m2 in (358.0, 258.0):
        agreeing[room_surface_m2] = sum(
            int(
                ph.noise_control.test_environment_applicability(
                    base_standard="ISO 3746",
                    mean_absorption_coefficient=_NPL_ROOMS["E"][4],
                    room_surface_area_m2=room_surface_m2,
                    measurement_surface_area_m2=_NPL_SURFACE_M2[surface],
                ).applicable
                is (value <= ceiling)
            )
            for surface, value in measured.items()
        )
    return numeric(
        3.0,
        float(agreeing[358.0]),
        0.0,
        expected_label="all three surfaces judged as measured, from the 358 m2 "
        "of Table 9",
        computed_label=f"{agreeing[358.0]} of 3 with Table 9, and "
        f"{agreeing[258.0]} of 3 with the 258 m2 Table 6 prints for the same "
        "room",
    )


@register(
    _ENCLOSURES,
    "NPL CIRA(EXT) 009 (1996) Tables 10 to 14, PDF pp. 22 to 24, "
    "printed folios 18 to 20",
    "The estimated room absorption column of the study does not follow the "
    "study's own Eq. (3): every one of its 17 cells sits more than 0,4 dB "
    "away from it, so that column is no oracle for this library",
)
def _chk_npl_estimated_absorption_drops_the_factor_four() -> Outcome:
    # The column follows 10 lg (1 + S/(alpha S_V)) instead, the factor 4
    # dropped: 10 of the 17 cells to the tenth it is printed to, the rooms C
    # and E within 0,2 dB of it, and the lower bound of room D, surface 4,
    # printed as 0,1 dB where that form gives 0,49 dB. Anyone anchoring the
    # absorption route on the column would read the library as wrong by up
    # to 4,6 dB while it is right.
    far = 0
    total = 0
    closest = float("inf")
    for room, printed in _NPL_ESTIMATED_K2A.items():
        room_surface_m2, _, _, alpha_from, alpha_to = _NPL_ROOMS[room]
        for surface, bounds in printed.items():
            total += 1
            gaps = [
                abs(
                    bound
                    - float(
                        ph.emission.environmental_correction(
                            _NPL_SURFACE_M2[surface],
                            mean_absorption_coefficient=alpha,
                            room_surface=room_surface_m2,
                        )
                    )
                )
                for bound, alpha in zip(bounds, (alpha_to, alpha_from), strict=True)
            ]
            closest = min(closest, min(gaps))
            far += int(min(gaps) > 0.4)
    return count(
        far,
        total,
        subject="printed cells Eq. (3) does not reach",
        expected_label=f"17/17 (closest approach {closest:.2f} dB)",
    )


@register(
    _ENCLOSURES,
    "Heisterkamp (2024) Table 3, PDF p. 10, printed folio 186",
    "The environmental correction from a mean absorption coefficient and a "
    "boundary area reproduces the six values three test engineers reached for "
    "one workroom",
)
def _chk_baua_estimated_environment() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for alpha, room_surface_m2, at_half_metre, at_one_metre in _BAUA_ENGINEERS.values():
        for surface_m2, want in zip(
            _BAUA_SURFACES_M2, (at_half_metre, at_one_metre), strict=True
        ):
            total += 1
            got = float(
                ph.emission.environmental_correction(
                    surface_m2,
                    mean_absorption_coefficient=alpha,
                    room_surface=room_surface_m2,
                )
            )
            if abs(got - want) <= 0.05:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of K_2A",
        expected_label=f"6/6 (worst departure {worst:.2f} dB)",
    )


@register(
    _ENCLOSURES,
    "Heisterkamp (2024) Table 3, PDF p. 10, printed folio 186",
    "Annex C puts the same workroom outside ISO 11202 on the first two "
    "assessments and inside it on the third, which is where their printed "
    "K_2A falls against the 7 dB of Table C.1",
)
def _chk_baua_applicability_verdict() -> Outcome:
    ceiling = TEST_ENVIRONMENT_REQUIREMENTS["ISO 11202"][0]
    assert ceiling is not None
    matching = 0
    total = 0
    for alpha, room_surface_m2, at_half_metre, at_one_metre in _BAUA_ENGINEERS.values():
        for surface_m2, printed in zip(
            _BAUA_SURFACES_M2, (at_half_metre, at_one_metre), strict=True
        ):
            total += 1
            verdict = ph.noise_control.test_environment_applicability(
                base_standard="ISO 11202",
                mean_absorption_coefficient=alpha,
                room_surface_area_m2=room_surface_m2,
                measurement_surface_area_m2=surface_m2,
            )
            matching += int(verdict.applicable is (printed <= ceiling))
    return count(
        matching,
        total,
        subject="verdicts that agree with the printed K_2A",
        expected_label="6/6, the tightest of them sitting 0,09 dB over the "
        "7 dB ceiling",
    )


@register(
    _ENCLOSURES,
    "Heisterkamp (2024) Table 4, PDF p. 11, printed folio 187",
    "The environmental correction taken from an absorption area measured with "
    "a reference sound source reproduces all six printed values, in two rooms "
    "and on three measurement surfaces",
)
def _chk_baua_measured_absorption_area() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    surfaces = (*_BAUA_SURFACES_M2, _BAUA_DIRECT_SURFACE_M2)
    for absorption_m2, *printed in _BAUA_DIRECT.values():
        for surface_m2, want in zip(surfaces, printed, strict=True):
            total += 1
            got = float(
                ph.emission.environmental_correction(
                    surface_m2, absorption_area=absorption_m2
                )
            )
            if abs(got - want) <= 0.05:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of K_2A",
        expected_label=f"6/6 (worst departure {worst:.2f} dB)",
    )


@register(
    _ENCLOSURES,
    "Barron (2003) Example 7-8, PDF pp. 321 and 323, printed folios 309 and 311",
    "The two A-weighted totals of that example on their own, 108,4 dBA "
    "without the enclosure and 89,8 dBA with it, which is where the "
    "weighting table shows and the difference of the two hides it",
)
def _chk_barron_a_weighted_totals() -> Outcome:
    # The rows above take the difference of these two totals, and a difference
    # hardly constrains the weighting at all: a whole decibel of error in any
    # one band moves D_pA by at most 0,07 dB, while it moves the 1 kHz share
    # of the total by 0,45 dB. The totals are the discriminating numbers, the
    # result object does not publish them, so the row reaches the helper that
    # forms them. The spectra and the printed totals are the ones the
    # Equation (3) and Equation (4) rows already read from Table 7-5.
    from phonometry.noise_control.enclosure_insulation import _a_weighted_total

    printed = {
        "without the enclosure": _BARRON_LPA_WITHOUT_DBA,
        "with the enclosure": _BARRON_LPA_WITH_DBA,
    }
    computed = {
        "without the enclosure": _a_weighted_total(
            _BARRON_LP_WITHOUT_DB, _BOOK_OCTAVES_HZ
        ),
        "with the enclosure": _a_weighted_total(_BARRON_LP_WITH_DB, _BOOK_OCTAVES_HZ),
    }
    worst = max(abs(computed[name] - value) for name, value in printed.items())
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dBA",
        expected_label="both totals within the one decimal the book prints",
        computed_label=", ".join(
            f"{name} {value:.2f} dBA" for name, value in computed.items()
        )
        + f", worst departure {worst:.3f} dB",
    )


@register(
    _ENCLOSURES,
    "Peters, Smith and Hollins, Acoustics and Noise Control 3rd ed, "
    "Example 1.13, PDF pp. 31 and 32, printed folios 16 and 17",
    "One enclosure, one measured band attenuation, two source spectra: the "
    "Annex D estimate gives 14 dBA against one machine and 27 dBA against the "
    "other, which is why the annex calls it an estimate",
)
def _chk_smith_estimate_follows_the_spectrum() -> Outcome:
    computed = {
        name: ph.noise_control.estimated_a_weighted_insulation(
            spectrum, _SMITH_ATTENUATION_DB, frequencies=_SMITH_BANDS_HZ
        )
        for name, (spectrum, _) in _SMITH_MACHINES.items()
    }
    printed = {name: want for name, (_, want) in _SMITH_MACHINES.items()}
    return record(
        printed,
        {name: float(round(value)) for name, value in computed.items()},
        unit="dBA",
        computed_label=", ".join(
            f"{name} = {value:.2f} dBA" for name, value in computed.items()
        )
        + f", a spread of {computed['machine B'] - computed['machine A']:.1f} dB",
    )


#: W. Schirmer (ed.), Technischer Laermschutz, 2nd edition, Springer 2006,
#: 10.8.1 "Akustische Dimensionierung": an enclosure 6 m by 5 m by 3 m high
#: with a 0,25 m2 exhaust opening, whose walls and roof the book prints as
#: S_K = 96 m2 - 0,25 m2 = 95,75 m2 on PDF page 323, printed folio 303, and
#: the opening fraction q = S_O/(S_K + S_O) = 2,6e-3 it prints for it on PDF
#: page 324, printed folio 304. The third edition of 2023 prints the same
#: numbers at the same clause.
_SCHIRMER_OPENING_M2 = 0.25
_SCHIRMER_WALLS_M2 = 95.75
_SCHIRMER_LEAK_RATIO = 2.6e-3


@register(
    _ENCLOSURES,
    "Schirmer (2006) 10.8.1, PDF pp. 323 and 324, printed folios 303 and 304",
    "ISO 11546-1:1995 3.16 / ISO 11546-2:1995 3.14: the leak ratio of an "
    "enclosure with a 0,25 m2 opening in 95,75 m2 of wall, taken over the "
    "interior surface with the opening counted in, against the printed "
    "q = 2,6e-3",
)
def _chk_schirmer_leak_ratio() -> Outcome:
    # Definition 3.14 of part 2 is definition 3.16 of part 1 word for word, so
    # this one row serves both parts. The book prints q to two significant
    # figures, so the tolerance is half of its last digit.
    ratio = ph.noise_control.leak_ratio(
        _SCHIRMER_OPENING_M2, _SCHIRMER_WALLS_M2 + _SCHIRMER_OPENING_M2
    )
    return numeric(
        _SCHIRMER_LEAK_RATIO,
        ratio,
        5e-5,
        places=6,
        expected_label="q = 2,6e-3 (+/-5e-5, half of the last digit printed)",
        computed_label=f"{ratio:.6f}",
    )


@register(
    _ENCLOSURES,
    "IFA-LSA 01-243 (2014) Anhang, Beispiele 1 and 3, PDF pp. 22, 23 and 25, "
    "printed folios 22, 23 and 25",
    "The A-weighted insulation of two enclosures measured where they stand, "
    "at a punching machine and at an emery machine, which pins the order of "
    "the subtraction against real installations",
)
def _chk_ifa_installed_enclosures() -> Outcome:
    computed: dict[str, float] = {}
    printed: dict[str, float] = {}
    for name, (without, with_, reduction) in _IFA_ENCLOSURES.items():
        result = ph.noise_control.sound_pressure_insulation(
            [without],
            [with_],
            a_weighted_without=without,
            a_weighted_with=with_,
            base_standard="ISO 11202",
            condition="in-situ",
            source_kind="actual",
        )
        assert result.a_weighted_insulation is not None
        computed[name] = result.a_weighted_insulation
        printed[name] = reduction
    return record(printed, computed, unit="dB")


# ---------------------------------------------------------------------------
# ISO 11957 prints no worked example, but it delegates two of its clauses to
# documents that do, and three laboratories have published cabin measurements
# rated to clause 8. The rows below are those borrowed oracles. Each names the
# document the numbers come from and the clause of ISO 11957 that makes it
# applicable, because neither half is the citation on its own.
# ---------------------------------------------------------------------------

#: The 16 one-third-octave rating bands of clause 8, in hertz.
_RATING_BANDS_HZ = np.array(
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
    ]
)

#: Clause 6.4 of ISO 11957 corrects the level inside the cabin for the
#: background "in accordance with ISO 3741". ISO 3741:2010 9.1.2 evaluates its
#: own Equation (14) at two arguments and prints the results: K_1 is held at
#: the 6 dB value at 200 Hz and below and at 6 300 Hz and above, and at the
#: 10 dB value from 250 Hz to 5 000 Hz. These three bands take one rule, then the other, then
#: the first again.
_K1_CLAMP_BANDS_HZ = np.array([100.0, 1000.0, 6300.0])

#: The margins over the background the three bands are given, in decibels. The
#: middle one is under its own 10 dB threshold, so it is the clamp itself that
#: is exercised there rather than Equation (14).
_K1_CLAMP_MARGIN_DB = np.array([6.0, 8.0, 6.0])

#: The two values ISO 3741:2010 prints on folio 20 (PDF p. 29), in decibels,
#: after Equation (14) on folio 19 (PDF p. 28):
#: "K1i shall be set to 1,26 dB (the value for dLpi = 6 dB)" and "to 0,46 dB
#: (the value for dLpi = 10 dB)".
_PRINTED_K1_DB = np.array([1.26, 0.46, 1.26])

#: A flat level to put those margins under, in decibels.
_K1_SIGNAL_DB = 80.0

#: ISO 717-1:2013 Table C.1, the two A-weighted spectra the adaptation terms
#: are formed against, in decibels, over the rating bands.
_SPECTRUM_ONE_DB = np.array(
    [-29.0, -26.0, -23.0, -21.0, -19.0, -17.0, -15.0, -13.0]
    + [-12.0, -11.0, -10.0, -9.0, -9.0, -9.0, -9.0, -9.0]
)
_SPECTRUM_TWO_DB = np.array(
    [-20.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0, -12.0]
    + [-11.0, -9.0, -8.0, -9.0, -10.0, -11.0, -13.0, -15.0]
)

#: ISO 3744:2010 Annex E, Table E.1 (PDF p. 69, printed folio 60): the
#: one-third-octave C_k over the same bands. Annex A of ISO 11957 takes the
#: spectrum unweighted and an attenuation A_i that is positive where the
#: weighting takes level away, so A_i = -C_k and the printed A-weighted
#: spectra are de-weighted with these before they are handed over.
_CK_THIRD_DB = np.array(
    [-19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2]
    + [-1.9, -0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2]
)

#: The "-10 lg sum" Table C.1 prints under each spectrum, in decibels. Both are
#: truncated rather than rounded, which the table marks with its ellipsis.
_PRINTED_SUM_TERM_DB = (28.308, 26.859)

#: SGS-CSTC Standards Technical Services, Shunde Branch, test report
#: SDHL260400706101HI of 7 May 2026, folio "Page 3 of 4": D_p of a meeting pod
#: measured in a 200 m3 reverberation room, in decibels, over the rating bands.
#: The report also prints 36,2 dB at 4 000 Hz and 36,4 dB at 5 000 Hz, which
#: the rating does not read.
_SGS_POD_DB = np.array(
    [11.0, 22.5, 24.0, 26.0, 29.3, 32.1, 28.3, 30.6]
    + [31.9, 34.9, 34.5, 33.2, 32.1, 33.7, 32.6, 33.2]
)

#: AGH University, Department of Mechanics and Vibroacoustics, report 5.5.130.
#: of August 2023, folio "Strona 10 z 10": D of an acoustic booth measured in a
#: 180,4 m3 reverberation room, in decibels, over the rating bands. The printed
#: table runs from 50 Hz to 10 kHz; the eight bands outside the rating range
#: play no part in it.
_AGH_BOOTH_DB = np.array(
    [10.0, 20.1, 14.7, 19.3, 20.6, 19.9, 23.2, 20.4]
    + [17.6, 19.1, 18.8, 20.2, 21.8, 24.4, 26.8, 28.3]
)

#: AGH University, Laboratorium Akustyki Technicznej, report 5.5.130.680 of
#: October 2017, folio "Strona 11 z 12": D_p of a telephone booth measured in
#: the same room, tabulated to whole decibels.
_EURONOVA_BOOTH_DB = np.array(
    [12.0, 18.0, 14.0, 15.0, 20.0, 25.0, 28.0, 31.0]
    + [31.0, 33.0, 34.0, 34.0, 31.0, 30.0, 32.0, 33.0]
)

#: Barron, Industrial Noise Control and Acoustics, Table 7-5 (printed folio
#: 308): the octave centres of Example 7-8, in hertz.
_BARRON_BANDS_HZ = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])

#: The same table, row "L_p^o(OB)": the level at the operator with no
#: enclosure, in decibels.
_BARRON_OPEN_DB = np.array([93.4, 98.5, 102.9, 104.6, 102.8, 95.5])

#: The same table, row "IL": the insertion loss the enclosure buys, in
#: decibels, which is the printed L_p^o(OB) less the printed L_p(OB) band for
#: band.
_BARRON_INSERTION_LOSS_DB = np.array([11.0, 13.6, 17.0, 18.8, 18.9, 24.3])

#: The two A-weighted totals the example prints, on folios 309 and 311, in
#: decibels: "L_A^o = 108.4 dBA (without the enclosure)" and "L_A = 89.8 dBA
#: (with the enclosure)". Each is printed to a tenth, so their difference
#: carries a tenth of uncertainty of its own.
_BARRON_OPEN_TOTAL_DB = 108.4
_BARRON_ENCLOSED_TOTAL_DB = 89.8


@register(
    _ENCLOSURES,
    "ISO 11957:1996 6.4 with ISO 3741:2010 9.1.2, Equation (14) and its clamps "
    "(PDF pp. 28 and 29, printed folios 19 and 20)",
    "The background correction 6.4 delegates, at the two clamp points "
    "ISO 3741 prints: 1,26 dB for a 6 dB margin and 0,46 dB for a 10 dB one",
)
def _chk_printed_k1_clamps() -> Outcome:
    levels = np.full(_K1_CLAMP_BANDS_HZ.size, _K1_SIGNAL_DB)
    correction = ph.emission.reverberation_background_correction(
        levels, levels - _K1_CLAMP_MARGIN_DB, _K1_CLAMP_BANDS_HZ
    )
    worst = float(np.max(np.abs(correction - _PRINTED_K1_DB)))
    return numeric(
        0.0,
        worst,
        0.005,
        unit="dB",
        expected_label=(
            "the printed 1,26 dB and 0,46 dB, to the two decimals folio 20 "
            "prints them at (+/-0,005 dB, half of that last digit)"
        ),
        computed_label=(
            f"worst departure {worst:.4f} dB over the three bands, which "
            "re-evaluate Equation (14) at the clamped margin instead of "
            "taking the rounded constant the clause writes"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 6.4 and 6.7 with ISO 3741:2010 9.1.2 (PDF p. 29, printed folio 20)",
    "The two clauses that spend that correction: the internal noise level at "
    "the two edges of its 6 dB to 10 dB window, and the insulation of 6.4",
)
def _chk_printed_k1_reaches_both_clauses() -> Outcome:
    # The window of 6.7 and the band thresholds of ISO 3741 share the numbers
    # 6 and 10 and are not the same rule; what is checked here is the value of
    # K_1 at those arguments, not where the window itself comes from.
    edges = [
        ph.noise_control.internal_noise_level(
            np.full(3, _K1_SIGNAL_DB), background_level=_K1_SIGNAL_DB - margin
        )
        for margin in (6.0, 10.0)
    ]
    cabin = np.full(_K1_CLAMP_BANDS_HZ.size, 60.0)
    insulation = ph.noise_control.cabin_insulation(
        np.full(_K1_CLAMP_BANDS_HZ.size, 90.0),
        cabin,
        frequencies=_K1_CLAMP_BANDS_HZ,
        method="laboratory",
        cabin_background_levels=cabin - _K1_CLAMP_MARGIN_DB,
    ).insulation
    computed = np.concatenate([np.asarray(edges), insulation])
    printed = np.array([78.74, 79.54, 31.26, 30.46, 31.26])
    worst = float(np.max(np.abs(computed - printed)))
    return numeric(
        0.0,
        worst,
        0.005,
        unit="dB",
        expected_label=(
            "80 - 1,26 and 80 - 0,46 for L_pA, and 31,26 / 30,46 / 31,26 "
            "for D_p (+/-0,005 dB, half of the last digit printed)"
        ),
        computed_label=f"worst departure {worst:.4f} dB over the five values",
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 clause 8 with ISO 717-1:2013 Annex C, Table C.1 "
    "(PDF p. 24, printed folio 16)",
    "Clause 8 is ISO 717-1 with D_p written where that standard writes R, so "
    "its printed example rates 30 (-2; -3) dB on an unfavourable sum of 31,8 dB",
)
def _chk_clause_eight_on_the_iso717_example() -> Outcome:
    printed = ref.ISO717_1_ANNEX_C_EXPECTED
    rating = ph.noise_control.weighted_cabin_insulation(ref.ISO717_1_ANNEX_C_R)
    return record(
        {
            "D_p,w": printed["rw"],
            "C": printed["c"],
            "Ctr": printed["ctr"],
            "unfavourable sum": printed["unfavourable_sum"],
        },
        {
            "D_p,w": rating.rating,
            "C": rating.c,
            "Ctr": rating.ctr,
            "unfavourable sum": round(rating.unfavourable_sum, 1),
        },
        unit="dB",
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 Annex A with ISO 717-1:2013 Annex C, Table C.1 "
    "(PDF p. 24, printed folio 16)",
    "The summation term of the Annex A estimate against the two printed "
    "sums, 28,308 dB and 26,859 dB, over sixteen bands each",
)
def _chk_annex_a_on_the_printed_sums() -> Outcome:
    # The table truncates, so the acceptance band is one-sided: a correct
    # value sits at or above each printed figure and less than 0,001 dB over
    # it, never under. The departure reported is the one nearest an edge.
    departures: list[float] = []
    for spectrum, printed in zip(
        (_SPECTRUM_ONE_DB, _SPECTRUM_TWO_DB), _PRINTED_SUM_TERM_DB, strict=True
    ):
        estimate = ph.noise_control.estimated_cabin_noise_insulation(
            spectrum - _CK_THIRD_DB,
            ref.ISO717_1_ANNEX_C_R,
            frequencies=_RATING_BANDS_HZ,
        )
        # The table prints the sum and its -10 lg, not L_A: its own spectra sit
        # within a hundredth of 0 dB, so the adaptation term needs the sum
        # alone. L_A is closed in from the same printed integers here, which is
        # why the comparison is with the estimate less that total.
        total = 10.0 * float(np.log10(np.sum(10.0 ** (0.1 * spectrum))))
        departures.append(estimate - total - printed)
    binding = min(departures, key=lambda value: min(value, 0.001 - value))
    return mask(
        expected=(
            "the printed -10 lg of the two sums, 28,308 dB and 26,859 dB. "
            "The table truncates rather than rounds, which its ellipsis says, "
            "so a correct value sits at or above each and within 0,001 dB of it"
        ),
        computed=(
            "departures "
            + " and ".join(f"{value:+.6f} dB" for value in departures)
            + " over the two spectra"
        ),
        deviation=binding,
        lower=0.0,
        upper=0.001,
        unit="dB",
        places=6,
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 clause 8 in SGS-CSTC report SDHL260400706101HI (2026), "
    "PDF p. 3, printed folio 3 of 4",
    "A meeting pod measured in a 200 m3 reverberation room and rated by the "
    "issuing laboratory at D_p,w = 32 dB",
)
def _chk_sgs_pod_rating() -> Outcome:
    # The report prints the rating and nothing else of the single-number set,
    # so C and Ctr travel here as computed values and are not anchored on it.
    rating = ph.noise_control.weighted_cabin_insulation(_SGS_POD_DB)
    return numeric(
        32.0,
        float(rating.rating),
        0.0,
        unit="dB",
        expected_label="D_p,w = 32 dB, the integer the report prints",
        computed_label=(
            f"D_p,w = {rating.rating} dB on an unfavourable sum of "
            f"{rating.unfavourable_sum:.1f} dB"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 clause 8 in AGH report 5.5.130. (2023), PDF p. 10, printed folio 10 of 10",
    "An acoustic booth measured in a 180,4 m3 reverberation room and rated "
    "by the issuing laboratory at D_p,w = 22 dB",
)
def _chk_agh_booth_rating() -> Outcome:
    rating = ph.noise_control.weighted_cabin_insulation(_AGH_BOOTH_DB)
    return numeric(
        22.0,
        float(rating.rating),
        0.0,
        unit="dB",
        expected_label="D_p,w = 22 dB, the integer the report prints",
        computed_label=(
            f"D_p,w = {rating.rating} dB on an unfavourable sum of "
            f"{rating.unfavourable_sum:.1f} dB"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 clause 8 in AGH report 5.5.130.680 (2017), PDF p. 11, "
    "printed folio 11 of 12",
    "A telephone booth whose insulation is tabulated to whole decibels, "
    "rated by the issuing laboratory at D_p,w = 30 dB",
)
def _chk_euronova_booth_rating() -> Outcome:
    # The plotted curve on the same card carries finer values than the table,
    # so the laboratory rated unrounded data. Rating the printed integers
    # reaches the same 30 dB with 9,0 dB of the 32,0 dB budget to spare, which
    # is the margin this row is worth and no more.
    rating = ph.noise_control.weighted_cabin_insulation(_EURONOVA_BOOTH_DB)
    return numeric(
        30.0,
        float(rating.rating),
        0.0,
        unit="dB",
        expected_label="D_p,w = 30 dB, the integer the report prints",
        computed_label=(
            f"D_p,w = {rating.rating} dB on an unfavourable sum of "
            f"{rating.unfavourable_sum:.1f} dB"
        ),
    )


@register(
    _ENCLOSURES,
    "ISO 11957:1996 Annex A with Barron (2003) Example 7-8, Table 7-5, "
    "PDF pp. 319 to 323, printed folios 307 to 311",
    "The A-weighted estimate over six octave bands: the two totals the "
    "example prints, 108.4 dBA and 89.8 dBA, are 18.6 dB apart",
)
def _chk_annex_a_on_barron_example() -> Outcome:
    # A machine enclosure predicted by the book's own model rather than a cabin
    # measured to ISO 11957, so what this anchors is the arithmetic of the
    # annex: the A-weighted sum with the insulation in and the one without.
    estimate = ph.noise_control.estimated_cabin_noise_insulation(
        _BARRON_OPEN_DB,
        _BARRON_INSERTION_LOSS_DB,
        frequencies=_BARRON_BANDS_HZ,
    )
    return numeric(
        _BARRON_OPEN_TOTAL_DB - _BARRON_ENCLOSED_TOTAL_DB,
        estimate,
        0.1,
        unit="dB",
        expected_label=(
            "108.4 dBA less 89.8 dBA, each printed to a tenth, so the "
            "difference carries a tenth of its own (+/-0.1 dB)"
        ),
    )


# ---------------------------------------------------------------------------
# ISO 11546-1 prints no worked example either, so the rows below take its
# arithmetic to published examples that do print one. What such an example can
# and cannot pin is worth saying once: it shares the band subtraction of
# Equations (1) and (3), the A-weighted summation of Equations (2) and (4) and
# the estimate of Annex C, because those are ordinary arithmetic on two
# spectra. It shares nothing of the measurement procedure, the applicability
# of Table 1 or the test environment, and no row below claims otherwise. Each
# names the document, the edition, the PDF page and the printed folio the
# numbers were read on.
# ---------------------------------------------------------------------------

#: The six octave bands both enclosure examples are worked in, in hertz. They
#: are exactly the mandatory octave range of clause 6.2.
_BOOK_OCTAVES_HZ = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])

#: Barron, Industrial Noise Control and Acoustics, Marcel Dekker, New York,
#: 2003 (ISBN 0-8247-0701-X), 7.6.2, Example 7-8, Table 7-5 "Solution for
#: Example 7-8" on PDF page 320, printed folio 308: a machine in a 1.80 m by
#: 1.20 m by 1.00 m plywood enclosure, with the operator 3 m away in a room 20
#: m by 20 m by 4 m. The rows are printed to 0.1 dB. The example is a
#: prediction, not an ISO 11546-1 measurement: the insertion loss is computed
#: from the sound power balance of the book's Equation (7-85), and only the
#: arithmetic that follows is shared with this standard.
_BARRON_LW_DB = np.array([103.0, 109.0, 114.0, 117.0, 113.0, 107.0])
_BARRON_LW_OUT_DB = np.array([92.0, 95.4, 97.0, 98.2, 94.2, 82.7])
_BARRON_IL_DB = np.array([11.0, 13.6, 17.0, 18.8, 18.9, 24.3])
_BARRON_LP_WITHOUT_DB = np.array([93.4, 98.5, 102.9, 104.6, 102.8, 95.5])
_BARRON_LP_WITH_DB = np.array([82.4, 84.9, 85.9, 85.8, 83.9, 71.2])

#: The two A-weighted sound pressure levels of the same example, in decibels,
#: printed in the running text rather than in the table: PDF page 321, printed
#: folio 309, "L_A = 108.4 dBA (without the enclosure)", and PDF page 323,
#: printed folio 311, "L_A = 89.8 dBA (with the enclosure)". Their difference
#: is D_pA; the book never prints it.
_BARRON_LPA_WITHOUT_DBA = 108.4
_BARRON_LPA_WITH_DBA = 89.8

#: The five bands of Table 7-5 where the sound power rows close on themselves.
#: At 2 000 Hz the table prints L_W,out = 94.2 dB while 113 - 18.9 = 94.1, and
#: the table's own L_p(OB) of 83.9 dB follows 94.1 rather than 94.2, so it is
#: the printed L_W,out that is 0.1 dB high there. The printed insertion loss is
#: the figure that is right, which is why the Equation (3) row keeps all six
#: bands and only the Equation (1) row, which reads L_W,out, drops one. This is
#: a slip in a textbook, not in a standard, so it is recorded here and not in
#: docs/ERRATA.md.
_BARRON_POWER_BANDS = np.array([True, True, True, True, False, True])

#: Harris (ed.), Noise Control Manual: Guidelines for Problem-Solving in the
#: Industrial/Commercial Acoustical Environment, Noise Control Association,
#: Van Nostrand Reinhold, 1991 (Springer softcover reprint, ISBN
#: 978-1-4757-6011-8), Appendix 3. The octave levels at the worker's station
#: before any treatment, in decibels, from Figure A3-2 on PDF page 135,
#: printed folio 125, and Figure A3-8 on PDF page 141, printed folio 131. Both
#: figures start from the same spectrum.
_HARRIS_BEFORE_DB = np.array([108.0, 103.0, 99.0, 104.0, 101.0, 85.0])

#: The four cases of the same two figures: the per-band reduction of each, in
#: decibels, against the A-weighted level the figure prints for it. Example 1
#: prints its insertion loss as one row; Example 3 prints a room adjustment and
#: a transmission loss which are added here, which is exact arithmetic on the
#: printed lines but is a construction rather than a quotation. Example 3 is a
#: personnel enclosure, nearer ISO 11957 in subject, and is kept because the
#: estimator is the same formula.
#:
#: The comparison is on the reduction, 107 dBA minus the figure's own total,
#: never on the rounded total itself: Example 1(a) prints 94 dBA where its own
#: pairwise addition lands on 94.5 and an energy sum gives 94.7, so a row
#: phrased on the rounded total would be red for a correct implementation. The
#: book adds bands pairwise from a difference table (Figure A3-1, PDF page 130,
#: printed folio 120), which costs about 0.7 dB at worst.
_HARRIS_CASES: dict[str, tuple[list[float], float]] = {
    "Example 1(a), plywood": ([13.0, 11.0, 12.0, 12.0, 13.0, 15.0], 107.0 - 94.0),
    "Example 1(b), plywood and insulation": (
        [18.0, 17.0, 23.0, 30.0, 38.0, 40.0],
        107.0 - 81.0,
    ),
    "Example 3(a), plain wall": ([16.0, 24.0, 40.0, 49.0, 50.0, 41.0], 107.0 - 77.0),
    "Example 3(b), insulated wall": (
        [24.0, 36.0, 50.0, 58.0, 61.0, 46.0],
        107.0 - 68.0,
    ),
}

#: ISO 717-1:2020, Annex C, Table C.1 "Calculation example: Measurements in
#: the specified frequency range 100 Hz to 3 150 Hz", PDF page 23, printed
#: folio 17: the sound reduction index of the example, in decibels, over the
#: sixteen one-third-octave rating bands. Clause 7.4 of ISO 11546-1 rates
#: D_W the same way with D_W in place of R, which is what lets this column be
#: read as an insertion loss spectrum.
_ISO717_TABLE_C1_DB = [
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

#: ISO 80000-1:2009, Annex B "Rounding of numbers": B.2 and B.3 Rule A with
#: both its examples on PDF page 43, printed folio 35, and Rule B with the
#: remark that Rule A is generally preferable on PDF page 44, printed folio
#: 36. Each
#: entry is a printed number over its printed rounding range, which B.1
#: defines as the interval between the integral multiples being rounded to, so
#: the quotient is what a rounding to the nearest integer is asked for.
#:
#: The two ties of Rule A at rounding range 10 are the pair that decides the
#: rule: 1 225,0 goes to 1 220 and 1 235,0 to 1 240, the even multiple in both
#: cases, where Rule B would give 1 230 and 1 240. The ties printed at
#: rounding range 0,1 are deliberately left out: 12,35 has no exact double, so
#: the tie is gone before any code sees it and the comparison would test the
#: binary representation rather than the rule.
_ISO80000_ROUNDING: tuple[tuple[str, float, int], ...] = (
    ("B.2, 12,223 at range 0,1", 12.223 / 0.1, 122),
    ("B.2, 12,251 at range 0,1", 12.251 / 0.1, 123),
    ("B.2, 12,275 at range 0,1", 12.275 / 0.1, 123),
    ("B.2, 1 223,3 at range 10", 1223.3 / 10.0, 122),
    ("B.2, 1 225,1 at range 10", 1225.1 / 10.0, 123),
    ("B.2, 1 227,5 at range 10", 1227.5 / 10.0, 123),
    ("B.3 Rule A, 1 225,0 at range 10", 1225.0 / 10.0, 122),
    ("B.3 Rule A, 1 235,0 at range 10", 1235.0 / 10.0, 124),
)

#: Suva, W. Lips, "Lärmbekämpfung durch Kapselungen", Bestellnummer 66026.d,
#: revised edition March 2010, clause 6.2.1 on PDF page 17, printed folio 15:
#: the manufacturer's octave sound power levels of a converter set, in
#: decibels, of which the guide says "Diese Werte ergeben L_WA = 104 dB".
_SUVA_OCTAVES_HZ = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_SUVA_LW_DB = np.array([91.0, 98.0, 102.0, 101.0, 99.0, 98.0, 91.0, 85.0])
_SUVA_LWA_DB = 104.0

# The same Rechenbeispiel of Schirmer's chapter 10 anchors the leak ratio of
# definition 3.16, which part 1 and part 2 word identically, and the row for it
# is registered above, _chk_schirmer_leak_ratio, under the second edition. It
# is not repeated here: the same division printed in two editions of one book
# is one oracle, not two. The third edition prints it at 10.8.1, PDF page 517,
# printed folio 499 for the geometry and PDF page 518, printed folio 500 for
# q = 2,6e-3.


@register(
    _ENCLOSURES,
    "Barron (2003) Table 7-5, PDF p. 320, printed folio 308",
    "ISO 11546-1:1995 Eq. (3): D_p band by band from the two printed sound "
    "pressure spectra, against the printed insertion loss row",
)
def _chk_barron_pressure_bands() -> Outcome:
    result = ph.noise_control.sound_pressure_insulation(
        _BARRON_LP_WITHOUT_DB,
        _BARRON_LP_WITH_DB,
        frequencies=_BOOK_OCTAVES_HZ,
        base_standard="ISO 11201",
        band_fraction=1,
    )
    departure = np.abs(result.insulation - _BARRON_IL_DB)
    worst = float(np.max(departure))
    return count(
        int(np.count_nonzero(departure <= 0.05)),
        int(_BARRON_IL_DB.size),
        subject="printed values of the insertion loss row",
        expected_label=f"6/6 (worst departure {worst:.1e} dB)",
    )


@register(
    _ENCLOSURES,
    "Barron (2003) Example 7-8, PDF pp. 321 and 323, printed folios 309 and 311",
    "ISO 11546-1:1995 Eq. (4): D_pA from the same two band spectra, against "
    "the difference of the printed 108.4 dBA and 89.8 dBA",
)
def _chk_barron_a_weighted_insulation() -> Outcome:
    result = ph.noise_control.sound_pressure_insulation(
        _BARRON_LP_WITHOUT_DB,
        _BARRON_LP_WITH_DB,
        frequencies=_BOOK_OCTAVES_HZ,
        base_standard="ISO 11201",
        band_fraction=1,
    )
    assert result.a_weighted_insulation is not None
    # Each total is printed to a tenth, so their difference is good to a tenth
    # and no more, which is the tolerance.
    return numeric(
        _BARRON_LPA_WITHOUT_DBA - _BARRON_LPA_WITH_DBA,
        result.a_weighted_insulation,
        0.1,
        unit="dB",
        places=2,
    )


@register(
    _ENCLOSURES,
    "Barron (2003) Example 7-8, PDF pp. 320 to 323, printed folios 308 to 311",
    "ISO 11546-1:1995 Annex C: the estimate formed from the unenclosed "
    "spectrum and the printed insertion loss lands on the same printed "
    "difference of A-weighted levels",
)
def _chk_barron_annex_c_estimate() -> Outcome:
    estimate = ph.noise_control.estimated_a_weighted_insulation(
        _BARRON_LP_WITHOUT_DB,
        _BARRON_IL_DB,
        frequencies=_BOOK_OCTAVES_HZ,
    )
    return numeric(
        _BARRON_LPA_WITHOUT_DBA - _BARRON_LPA_WITH_DBA,
        estimate,
        0.1,
        unit="dB",
        places=2,
    )


@register(
    _ENCLOSURES,
    "Barron (2003) Table 7-5, PDF p. 320, printed folio 308",
    "ISO 11546-1:1995 Eq. (1): D_W from the printed sound power levels with "
    "and without the enclosure, in the five bands where the table closes on "
    "itself",
)
def _chk_barron_power_bands() -> Outcome:
    keep = _BARRON_POWER_BANDS
    result = ph.noise_control.sound_power_insulation(
        _BARRON_LW_DB[keep],
        _BARRON_LW_OUT_DB[keep],
        frequencies=_BOOK_OCTAVES_HZ[keep],
        base_standard="ISO 3744",
        band_fraction=1,
    )
    departure = np.abs(result.insulation - _BARRON_IL_DB[keep])
    worst = float(np.max(departure))
    return count(
        int(np.count_nonzero(departure <= 0.05)),
        int(departure.size),
        subject="printed values of the insertion loss row",
        expected_label=f"5/5 (worst departure {worst:.1e} dB)",
    )


@register(
    _ENCLOSURES,
    "Harris (1991) Figures A3-2 and A3-8, PDF pp. 135 and 141, "
    "printed folios 125 and 131",
    "ISO 11546-1:1995 Annex C: the A-weighted reduction of four enclosure "
    "cases, within the decibel the book's own pairwise addition costs",
)
def _chk_harris_estimated_reduction() -> Outcome:
    worst = 0.0
    matching = 0
    for reduction, printed in _HARRIS_CASES.values():
        estimate = ph.noise_control.estimated_a_weighted_insulation(
            _HARRIS_BEFORE_DB,
            reduction,
            frequencies=_BOOK_OCTAVES_HZ,
        )
        departure = abs(estimate - printed)
        worst = max(worst, departure)
        matching += int(departure <= 1.0)
    return count(
        matching,
        len(_HARRIS_CASES),
        subject="printed A-weighted reductions",
        expected_label=f"4/4 (worst departure {worst:.2f} dB)",
    )


@register(
    _ENCLOSURES,
    "ISO 717-1:2020 Annex C, Table C.1, PDF p. 23, printed folio 17",
    "ISO 11546-1:1995 7.4 rates D_W the way ISO 717-1 rates R, and the "
    "printed calculation example reads through that pass-through unchanged",
)
def _chk_iso717_pass_through() -> Outcome:
    rated = ph.noise_control.weighted_insulation(
        _ISO717_TABLE_C1_DB,
        quantity="sound_power",
        band_fraction=3,
    )
    printed = {"rating": 30.0, "C": -2.0, "Ctr": -3.0, "unfavourable sum": 31.8}
    computed = {
        "rating": float(rated.rating),
        "C": float(rated.c),
        "Ctr": float(rated.ctr),
        "unfavourable sum": float(rated.unfavourable_sum),
    }
    return record(printed, computed, unit="dB")


@register(
    _ENCLOSURES,
    "ISO 80000-1:2009 Annex B, B.2 and B.3, PDF pp. 43 and 44, printed folios 35 and 36",
    "ISO 11546-1:1995 9.4 states every result rounded to the nearest integer "
    "and names no rule; the rule this rounding follows is Rule A, the even "
    "multiple, which the annex calls generally preferable",
)
def _chk_iso80000_rounding() -> Outcome:
    given = [multiple for _, multiple, _ in _ISO80000_ROUNDING]
    rounded = ph.noise_control.sound_power_insulation(
        given, [0.0] * len(given)
    ).rounded()
    printed = [want for _, _, want in _ISO80000_ROUNDING]
    matching = sum(
        int(got == want) for got, want in zip(rounded.tolist(), printed, strict=True)
    )
    return count(
        matching,
        len(printed),
        subject="printed roundings of Annex B, two of them ties",
    )


@register(
    _ENCLOSURES,
    "Suva 66026.d (2010) 6.2.1, PDF p. 17, printed folio 15",
    "ISO 11546-1:1995 Eq. (2): the A-weighted total of an octave sound power "
    "spectrum, read as the insulation against a reference that carries its "
    "energy in the 1 kHz band alone",
)
def _chk_suva_a_weighted_total() -> Outcome:
    # The A-weighting correction is zero at 1 kHz by definition, so a
    # reference whose energy sits in that band alone has an A-weighted total
    # equal to its band level. Putting that level at 0 dB makes Equation (2)
    # return the A-weighted total of the other spectrum, which is the only
    # quantity this guide prints. The remaining bands are 300 dB down, which
    # is thirty orders of magnitude below the one that carries the energy.
    reference = np.full(_SUVA_LW_DB.size, -300.0)
    reference[_SUVA_OCTAVES_HZ == 1000.0] = 0.0
    result = ph.noise_control.sound_power_insulation(
        _SUVA_LW_DB,
        reference,
        frequencies=_SUVA_OCTAVES_HZ,
        base_standard="ISO 3744",
        band_fraction=1,
    )
    assert result.a_weighted_insulation is not None
    return numeric(
        _SUVA_LWA_DB,
        result.a_weighted_insulation,
        0.5,
        unit="dB",
        places=2,
        expected_label="104 dB, the integer the guide prints",
    )
