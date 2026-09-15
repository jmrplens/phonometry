#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Workroom acoustics: ISO 14257, ISO 11690-3 and EN 16487.

The three documents answer three questions about the same room. ISO 14257
measures how the sound falls off across it and derives two descriptors from
that curve; ISO 11690-3 says which prediction method may be used to compute the
same curve before the room exists, and what one machine adds at its own
workstation once it does; EN 16487 fixes the test arrangement for the
suspended ceiling that is the usual way of changing the answer.

**The oracle is Annex C of ISO 14257.** A measurement in a 83 m by 32 m by 11 m
shipyard hall with eleven microphone positions from 2 m to 48 m, printed all
the way through: the source power, its free-field-over-a-reflecting-plane
curve, the levels measured in the room, the two distribution curves and four
tables of results. The rows below take the printed inputs and check the printed
outputs, including the one place where the annex is not consistent with itself.
"""

from __future__ import annotations

import numpy as np

import phonometry as ph
from phonometry.materials.absorbers.suspended_ceilings import (
    CEILING_UNCERTAINTY,
    EN16487_COVERAGE_FACTOR,
)
from phonometry.room.spatial_decay import DECADE_TO_DOUBLING, PINK_NOISE_WEIGHTS_DB

from ..registry import Outcome, count, numeric, record, register

_WORKROOM = "Spatial sound decay and prediction in workrooms"

#: Table C.1: the eleven microphone positions, in metres.
_DISTANCES_M = np.array([2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 48], dtype=float)

#: Table C.2: the sound power level of the source used for the test, in
#: decibels, by nominal octave centre in hertz.
_SOURCE_POWER_DB = {
    125: 97.6,
    250: 98.6,
    500: 102.2,
    1000: 110.8,
    2000: 111.2,
    4000: 107.4,
}

#: Table C.4: the levels measured in the workroom, in decibels.
_ROOM_LEVELS_DB = {
    125: [85.7, 82.5, 80.8, 78.3, 77.1, 75.4, 73.7, 71.3, 70.4, 67.3, 65.7],
    250: [84.9, 81.9, 79.6, 77.8, 77.9, 74.3, 72.1, 70.3, 69.8, 65.0, 63.5],
    500: [89.8, 85.7, 83.6, 81.8, 80.5, 78.8, 76.8, 76.3, 72.0, 70.5, 69.1],
    1000: [98.9, 95.1, 93.0, 92.0, 91.0, 87.9, 85.8, 83.5, 81.5, 77.0, 75.6],
    2000: [99.7, 96.0, 93.5, 92.2, 91.0, 89.6, 86.6, 85.0, 81.1, 79.4, 76.7],
    4000: [93.8, 91.2, 88.3, 86.8, 85.7, 84.3, 80.4, 78.1, 74.9, 72.5, 70.5],
}

#: Table C.3: the same source in a free field over a reflecting plane, in
#: decibels, which Annex B takes back out of the measurement.
_FREE_FIELD_LEVELS_DB = {
    125: [83.4, 79.8, 76.9, 74.9, 73.2, 70.7, 67.3, 65.1, 61.5, 59.1, 55.6],
    250: [84.8, 80.9, 78.8, 76.4, 75.1, 72.5, 69.1, 66.6, 62.8, 60.5, 56.5],
    500: [89.7, 85.5, 83.2, 81.4, 80.0, 77.5, 74.1, 71.2, 67.4, 65.3, 60.4],
    1000: [98.8, 94.7, 92.3, 90.3, 88.7, 86.1, 82.6, 79.8, 75.7, 73.7, 67.8],
    2000: [99.2, 94.8, 92.2, 90.1, 88.6, 85.9, 82.6, 80.1, 75.3, 73.4, 65.7],
    4000: [92.8, 90.2, 87.3, 85.0, 83.2, 80.4, 76.8, 75.2, 71.0, 68.0, 57.3],
}

#: Table C.6: the curve after the Annex B correction, in decibels.
_CORRECTED_DB = {
    125: [-11.8, -14.9, -16.5, -19.0, -20.1, -21.9, -23.7, -26.2, -27.1, -30.2, -31.9],
    250: [-13.9, -16.5, -19.2, -20.7, -20.7, -24.3, -26.5, -28.3, -28.7, -33.6, -35.0],
    500: [-13.9, -17.3, -19.6, -21.4, -22.8, -24.4, -26.1, -26.2, -30.4, -32.0, -33.1],
    1000: [-13.8, -16.9, -19.1, -19.8, -20.6, -23.8, -25.6, -27.7, -29.4, -34.2, -34.9],
    2000: [-13.3, -16.1, -18.4, -19.5, -20.7, -21.9, -25.0, -26.5, -30.0, -31.9, -34.0],
    4000: [-13.1, -16.4, -19.0, -20.3, -21.3, -22.7, -26.5, -29.2, -32.2, -34.4, -35.8],
}

#: Table C.7: the printed decay rate, in decibels per distance doubling.
_PRINTED_DECAY_DB = {
    "near": {125: 5.2, 250: 5.2, 500: 5.7, 1000: 4.6, 2000: 4.8, 4000: 5.5},
    "middle": {125: 3.7, 250: 4.0, 500: 3.5, 1000: 4.4, 2000: 4.5, 4000: 5.4},
    "far": {125: 4.6, 250: 6.0, 500: 2.6, 1000: 5.2, 2000: 4.0, 4000: 3.6},
}

#: Table C.9: the printed excess of sound pressure level, in decibels.
_PRINTED_EXCESS_DB = {
    "near": {125: 5.6, 250: 3.8, 500: 4.3, 1000: 5.2, 2000: 5.4, 4000: 4.0},
    "middle": {125: 8.1, 250: 6.3, 500: 6.9, 1000: 7.3, 2000: 7.8, 4000: 5.6},
    "far": {125: 11.5, 250: 8.6, 500: 9.8, 1000: 8.3, 2000: 9.4, 4000: 6.6},
}

#: The ranges the annex evaluates over, in metres.
_RANGES_M = {"near": (2.0, 5.0), "middle": (5.0, 24.0), "far": (24.0, 48.0)}


def _raw(band: int) -> np.ndarray:
    return ph.room.sound_distribution_value(
        _ROOM_LEVELS_DB[band], _SOURCE_POWER_DB[band]
    )


def _corrected(band: int) -> np.ndarray:
    measured = ph.room.sound_distribution_value(
        _FREE_FIELD_LEVELS_DB[band], _SOURCE_POWER_DB[band]
    )
    return ph.room.corrected_distribution_value(
        _raw(band), measured, _DISTANCES_M, source_height_m=0.0
    )


def _keep(region: str) -> np.ndarray:
    low, high = _RANGES_M[region]
    return (_DISTANCES_M >= low) & (_DISTANCES_M <= high)


@register(
    _WORKROOM,
    "ISO 14257:2001 Eq. (2)",
    "The free-field reference curve falls 6 dB per distance doubling and "
    "passes 11 dB under the source power at 1 m",
)
def _chk_reference_curve() -> Outcome:
    ref = ph.room.reference_distribution_value([1.0, 2.0, 4.0])
    return record(
        {"at 1 m": -11.0, "per doubling": 6.02},
        {
            "at 1 m": round(float(ref[0]), 4),
            "per doubling": round(float(ref[0] - ref[1]), 2),
        },
        unit="dB",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex C, Table C.6 EXAMPLE",
    "The Annex B correction reproduces all 66 printed values of the "
    "corrected distribution curve",
)
def _chk_table_c6() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for band, printed in _CORRECTED_DB.items():
        got = _corrected(band)
        for value, want in zip(got.tolist(), printed, strict=True):
            total += 1
            if abs(value - want) <= 0.1:
                matching += 1
            worst = max(worst, abs(value - want))
    return count(
        matching,
        total,
        subject="printed values within the rounding of the table",
        expected_label=f"66/66 (worst departure {worst:.2f} dB)",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex C, Table C.6 last column",
    "The A-weighted pink-noise normalisation of Eq. (4) reproduces the "
    "eleven printed values",
)
def _chk_table_c6_normalized() -> Outcome:
    printed = [
        -13.4,
        -16.5,
        -18.9,
        -20.0,
        -21.1,
        -22.8,
        -25.7,
        -27.5,
        -30.4,
        -33.1,
        -34.6,
    ]
    corrected = {band: _corrected(band) for band in _SOURCE_POWER_DB}
    got = [
        ph.room.normalized_distribution_value(
            [corrected[band][i] for band in _SOURCE_POWER_DB]
        )
        for i in range(_DISTANCES_M.size)
    ]
    worst = max(abs(a - b) for a, b in zip(got, printed, strict=True))
    return numeric(
        0.0,
        worst,
        0.1,
        unit="dB",
        expected_label="every value within the printed rounding",
        computed_label=f"worst departure {worst:.2f} dB over 11 positions",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Eq. (5) / Annex C, Table C.7 EXAMPLE",
    "The rate of spatial decay reproduces all 18 printed values, in three "
    "distance ranges and six octave bands",
)
def _chk_table_c7() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for region, row in _PRINTED_DECAY_DB.items():
        keep = _keep(region)
        for band, want in row.items():
            total += 1
            got = ph.room.spatial_decay_rate(_corrected(band)[keep], _DISTANCES_M[keep])
            if abs(got - want) <= 0.06:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of DL2 within the rounding of the table",
        expected_label=f"18/18 (worst departure {worst:.2f} dB)",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Eqs. (6) and (7) / Annex C, Table C.9 EXAMPLE",
    "The excess of sound pressure level reproduces all 18 printed values "
    "from the uncorrected curve of Table C.5",
)
def _chk_table_c9() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for region, row in _PRINTED_EXCESS_DB.items():
        keep = _keep(region)
        for band, want in row.items():
            total += 1
            got = ph.room.mean_level_excess(_raw(band)[keep], _DISTANCES_M[keep])
            if abs(got - want) <= 0.07:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of DLf within the rounding of the table",
        expected_label=f"18/18 (worst departure {worst:.2f} dB)",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex C (C.1 against Tables C.7 and C.9)",
    "The annex applies its own Annex B correction to DL2 and not to DLf, "
    "which the two tables disagree about by more than a decibel",
)
def _chk_annex_c_is_inconsistent() -> Outcome:
    swapped = 0
    for region, row in _PRINTED_DECAY_DB.items():
        keep = _keep(region)
        for band, want in row.items():
            got = ph.room.spatial_decay_rate(_raw(band)[keep], _DISTANCES_M[keep])
            swapped += int(abs(got - want) > 0.06)
    for region, row in _PRINTED_EXCESS_DB.items():
        keep = _keep(region)
        for band, want in row.items():
            got = ph.room.mean_level_excess(_corrected(band)[keep], _DISTANCES_M[keep])
            swapped += int(abs(got - want) > 0.07)
    return numeric(
        28.0,
        float(swapped),
        0.0,
        expected_label=(
            "28 of the 36 printed results leave the rounding of their own "
            "table when the other table's curve is used"
        ),
        computed_label=f"{swapped} of 36, 14 in each table",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Eq. (5) against Eq. (8)",
    "The factor Eq. (5) prints, 0,3, is the logarithm of two rounded, which "
    "Eq. (8) prints in full one page later",
)
def _chk_printed_factor() -> Outcome:
    return numeric(
        float(np.log10(2.0)),
        DECADE_TO_DOUBLING,
        0.002,
        expected_label="lg 2 = 0,301 03",
        computed_label="the printed 0,3, which is 0,34 % smaller",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Table 1",
    "The A-weighted pink-noise spectrum weights the six octave bands the "
    "way Table 1 prints them",
)
def _chk_table_one() -> Outcome:
    printed = {
        "125 Hz": -16.1,
        "250 Hz": -8.6,
        "500 Hz": -3.2,
        "1 kHz": 0.0,
        "2 kHz": 1.2,
        "4 kHz": 1.0,
    }
    computed = dict(zip(printed, PINK_NOISE_WEIGHTS_DB.values(), strict=True))
    return record(printed, computed, unit="dB")


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex B, Eq. (B.4)",
    "A source with its acoustical centre on the floor radiates into a half "
    "space, which is 3 dB over the free field",
)
def _chk_floor_reflection() -> Outcome:
    free = ph.room.reference_distribution_value([4.0])[0]
    floor = ph.room.floor_reference_value([4.0], source_height_m=0.0)[0]
    return numeric(
        3.0,
        float(floor - free),
        0.02,
        unit="dB",
        expected_label="the 3 dB Eq. (B.4) prints",
    )


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex C, Table C.2 EXAMPLE",
    "The level increase at a machine's own workstation is the ISO 3744 "
    "environmental correction, which reproduces seven of the eight rows",
)
def _chk_annex_c_of_11690() -> Outcome:
    printed = {
        "M1": (105.0, 79.0, 9.5),
        "M2": (98.0, 81.0, 3.0),
        "M3": (107.0, 87.0, 5.0),
        "M4": (94.0, 82.0, 1.0),
        "M5": (102.0, 84.0, 4.0),
        "M6": (96.0, 82.0, 2.0),
        "M7": (101.0, 84.0, 3.0),
    }
    worst = 0.0
    matching = 0
    for power, emission, want in printed.values():
        got = ph.room.workstation_level_increase(
            sound_power_level_db=power,
            emission_level_db=emission,
            absorption_area_m2=195.0,
        )
        if abs(got - want) <= 0.45:
            matching += 1
        worst = max(worst, abs(got - want))
    return count(
        matching,
        len(printed),
        subject="rows within the half decibel the diagram is drawn to",
        expected_label=f"7/7 (worst departure {worst:.2f} dB)",
    )


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex C, Figure C.1 (the eighth machine)",
    "M8 needs more increase than the diagram can show, and the table "
    "prints the edge of the diagram instead",
)
def _chk_m8_off_the_chart() -> Outcome:
    got = ph.room.workstation_level_increase(
        sound_power_level_db=107.0, emission_level_db=78.0, absorption_area_m2=195.0
    )
    return numeric(
        12.4,
        got,
        0.1,
        unit="dB",
        expected_label="12,4 dB, against the 10 dB the table prints and the "
        "10 dB the diagram ends at",
    )


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Table E.1",
    "Each category of prediction method admits the levels of detail "
    "Table E.1 lists and refuses the rest",
)
def _chk_table_e1() -> Outcome:
    cases = {
        "1 with a level-1 room": ("1", 1, 1, 1, True),
        "1 with a level-4 room": ("1", 4, 1, 1, False),
        "2a as Annex D uses it": ("2a", 2, 1, 1, True),
        "2a with level-3 fittings": ("2a", 1, 3, 1, False),
        "2c with everything": ("2c", 4, 4, 3, True),
    }
    matching = 0
    for category, room_detail, fitting, source, want in cases.values():
        verdict = ph.room.detail_is_sufficient(
            category,
            room_detail=room_detail,
            fitting_detail=fitting,
            source_detail=source,
        )
        matching += int(verdict.satisfied is want)
    return count(matching, len(cases), subject="combinations judged as printed")


@register(
    _WORKROOM,
    "ISO 11690-3:1998 4.3 against ISO 14257 Annex C",
    "The middle-range decay of the worked example falls inside the 2 dB to "
    "5 dB the guidance says to expect",
)
def _chk_typical_range() -> Outcome:
    low, high = ph.room.typical_decay_range("middle")
    keep = _keep("middle")
    inside = 0
    for band in _SOURCE_POWER_DB:
        got = ph.room.spatial_decay_rate(_corrected(band)[keep], _DISTANCES_M[keep])
        above = low is None or got >= low
        below = high is None or got <= high
        inside += int(above and below)
    return numeric(
        5.0,
        float(inside),
        0.0,
        expected_label=(
            "five of the six octave bands, the 4 kHz one running 0,4 dB over "
            "the 5 dB top of the range 4.3 leads one to expect"
        ),
        computed_label=f"{inside} of 6 inside 2 dB to 5 dB",
    )


@register(
    _WORKROOM,
    "EN 16487:2014 Table 1",
    "The reproducibility uncertainty of the absorption coefficient is the "
    "printed spectrum, and a coverage factor of 2,8 over its standard deviation",
)
def _chk_en16487_table_one() -> Outcome:
    printed = {
        "125 Hz": 0.23,
        "250 Hz": 0.23,
        "500 Hz": 0.11,
        "1 kHz": 0.10,
        "2 kHz": 0.10,
        "4 kHz": 0.13,
    }
    computed = dict(
        zip(printed, ph.materials.reproducibility_uncertainty().tolist(), strict=True)
    )
    return record(printed, computed)


@register(
    _WORKROOM,
    "EN 16487:2014 Table 1 NOTE",
    "The printed uncertainty is a reproducibility standard deviation times "
    "the coverage factor of 2,8 that ISO 5725-6 applies",
)
def _chk_en16487_coverage() -> Outcome:
    sigma = CEILING_UNCERTAINTY[1000.0] / EN16487_COVERAGE_FACTOR
    return numeric(
        CEILING_UNCERTAINTY[1000.0],
        EN16487_COVERAGE_FACTOR * sigma,
        1e-12,
        expected_label="0,10 at 1 kHz, which is 2,8 times 0,0357",
    )


@register(
    _WORKROOM,
    "EN 16487:2014 4.2.1",
    "The air-absorption correction is four room volumes of attenuation "
    "difference spread over the specimen",
)
def _chk_air_correction() -> Outcome:
    got = ph.materials.air_absorption_correction(
        volume_m3=200.0,
        specimen_area_m2=10.8,
        attenuation_with=[0.0120],
        attenuation_empty=[0.0100],
    )
    return numeric(
        4.0 * 200.0 * 0.002 / 10.8,
        float(got[0]),
        1e-9,
        expected_label="4V(m2 - m1)/S with V = 200 m3, S = 10,80 m2",
    )
