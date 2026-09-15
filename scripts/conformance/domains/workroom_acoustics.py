#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Workroom acoustics: ISO 14257 and ISO 11690-3.

The two documents answer two questions about the same room. ISO 14257
measures how the sound falls off across it and derives two descriptors from
that curve; ISO 11690-3 says which prediction method may be used to compute the
same curve before the room exists, and what one machine adds at its own
workstation once it does. The usual way of changing the answer, a suspended
absorbing ceiling, is measured to EN 16487, which has a section of its own.

**The oracle is Annex C of ISO 14257.** A measurement in a 83 m by 32 m by 11 m
shipyard hall with eleven microphone positions from 2 m to 48 m, printed all
the way through: the source power, its free-field-over-a-reflecting-plane
curve, the levels measured in the room, the two distribution curves and four
tables of results. The rows below take the printed inputs and check the printed
outputs, including the two places where the annex is not consistent with itself:
Tables C.7 and C.9 disagree about which curve they were computed from, and
Tables C.11 and C.12 cannot be got out of Equation (8) at all. That second one
is not a misprint. The BS and the AENOR printings carry the same digits.

**Annex C is not the only witness.** It is printed in the document that defines
the method, so it cannot say whether the method was read right. Three published
sources can. A Swiss national-institute guide prints a 21 position curve
measured in a workroom and the 42 descriptors its own analysis program read off
it, and it never names ISO 14257: it takes the two quantities from VDI 3760 and
EN ISO 11690-1, so reproducing its figures is a cross-family check rather than a
restatement. A German guidance sheet prints four levels at four distances and
the decay rate its own specialised formula gives for them, and one cell of its
result table does not survive the comparison. A BAuA research report prints the
fitting density an independent VDI 3760 tool computed for surveyed workrooms,
four of which are read here.

**ISO 11690-3 works an example of its own**, in Annex B: one workroom twice
over, first as two machines are installed in it and then as a third is chosen
between the two models on offer. It is printed to a tenth of a decibel, and its
workstation labels contradict its own results, so the rows that use it anchor on
the printed positions and never on the labels. Where neither document prints an
example, three published ones stand in: a German data sheet for the step from a
measured reverberation time to an absorption area, Ver & Beranek for the energy
addition at a workstation with nine machines around it, and Barron for the
direct-plus-reverberant field a category 1 method computes each contribution
with.
"""

from __future__ import annotations

import numpy as np

import phonometry as ph
from phonometry.room.spatial_decay import (
    ADJACENT_BAND_LIMIT_DB,
    DECADE_TO_DOUBLING,
    EVALUATION_DISTANCES_M,
    FREE_FIELD_OFFSET_DB,
    MAX_DIRECTIVITY_INDEX_DB,
    NORMALIZED_OFFSET_DB,
    OMNIDIRECTIONAL_RAMP_HZ,
    OMNIDIRECTIONAL_TOLERANCE_DB,
    PINK_NOISE_WEIGHTS_DB,
    STABILITY_TOLERANCE_DB,
)

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

#: Table C.6, last column: the same curve collapsed onto A-weighted pink
#: noise by Eq. (4), in decibels.
_CORRECTED_NORMALIZED_DB = [
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
    printed = _CORRECTED_NORMALIZED_DB
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


# ---------------------------------------------------------------------------
# Annex A and the source that was qualified against it
# ---------------------------------------------------------------------------


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex A (PDF pages 24 and 25, printed folios 14 and 15)",
    "The limits a test source is qualified against are the ones the normative "
    "annex prints",
)
def _chk_annex_a_limits() -> Outcome:
    printed = {
        "max |DI|, dB": 8.0,
        "DI tolerance to 630 Hz, dB": 2.0,
        "DI tolerance from 1 kHz, dB": 8.0,
        "ramp starts, Hz": 630.0,
        "ramp ends, Hz": 1000.0,
        "adjacent band step, dB": 8.0,
        "Lw stability 100 Hz to 160 Hz, dB": 1.0,
        "Lw stability 200 Hz to 5 kHz, dB": 0.5,
    }
    computed = {
        "max |DI|, dB": MAX_DIRECTIVITY_INDEX_DB,
        "DI tolerance to 630 Hz, dB": OMNIDIRECTIONAL_TOLERANCE_DB[0],
        "DI tolerance from 1 kHz, dB": OMNIDIRECTIONAL_TOLERANCE_DB[1],
        "ramp starts, Hz": OMNIDIRECTIONAL_RAMP_HZ[0],
        "ramp ends, Hz": OMNIDIRECTIONAL_RAMP_HZ[1],
        "adjacent band step, dB": ADJACENT_BAND_LIMIT_DB,
        "Lw stability 100 Hz to 160 Hz, dB": STABILITY_TOLERANCE_DB[(100.0, 160.0)],
        "Lw stability 200 Hz to 5 kHz, dB": STABILITY_TOLERANCE_DB[(200.0, 5000.0)],
    }
    return record(printed, computed)


@register(
    _WORKROOM,
    "ISO 14257:2001 C.3 (PDF page 29, printed folio 19)",
    "The source the annex declares as qualified is inside both limits it is "
    "declared against",
)
def _chk_annex_c_source_qualifies() -> Outcome:
    # The annex prints "maximum directivity index: 4,4 dB; maximum sound power
    # level difference of adjacent one-third-octave bands: 6,5 dB ... OK". It
    # prints no band for the directivity index, so it cannot say anything about
    # the ramp of A.1, only about the 8 dB cap.
    declared = {"directivity index": 4.4, "adjacent band step": 6.5}
    limits = {
        "directivity index": MAX_DIRECTIVITY_INDEX_DB,
        "adjacent band step": ADJACENT_BAND_LIMIT_DB,
    }
    inside = sum(int(value <= limits[name]) for name, value in declared.items())
    return count(
        inside,
        len(declared),
        subject="declared characteristics inside their limit",
        expected_label="2/2, the closer of the two 1,5 dB under the 8 dB cap",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex C, Table C.2 last column (PDF page 28, printed folio 18)",
    "The A-weighted sound power level of the test source is the energy sum of "
    "its six printed octave bands under the Table 1 weights",
)
def _chk_table_c2_a_weighted() -> Outcome:
    # Equation (4) is that energy sum less 6,2 dB, so adding the offset back
    # leaves the plain A-weighted total the last column of the table prints.
    # This is the one printed number of Annex C that the Table C.6 chain never
    # touches, so it checks the weights and the summation on their own.
    total = (
        ph.room.normalized_distribution_value(list(_SOURCE_POWER_DB.values()))
        + NORMALIZED_OFFSET_DB
    )
    return numeric(115.7, float(total), 0.05, unit="dB")


# ---------------------------------------------------------------------------
# Equation (8), which the annex prints results for that it does not produce
# ---------------------------------------------------------------------------

#: Table C.11: the excess read off the fitted line at the conventional distance
#: of each region, in decibels, by nominal octave centre in hertz.
_PRINTED_EXCESS_AT_DB = {
    "near": {125: 6.2, 250: 4.0, 500: 4.4, 1000: 5.2, 2000: 5.3, 4000: 3.9},
    "middle": {125: 7.8, 250: 5.4, 500: 6.4, 1000: 6.9, 2000: 7.7, 4000: 5.8},
    "far": {125: 10.6, 250: 7.4, 500: 9.3, 1000: 7.2, 2000: 9.2, 4000: 6.1},
}

#: Table C.12: the same three figures for A-weighted pink noise, in decibels.
_PRINTED_EXCESS_AT_NORMALIZED_DB = {"near": 4.8, "middle": 6.8, "far": 8.0}

#: Table C.5 on printed folio 21 (PDF page 31): the uncorrected curve
#: D = L_p - L_W as printed, in decibels, by nominal octave centre in hertz.
#: The excess family of the annex, Table C.9, is computed on this curve and not
#: on the corrected one, so it is the curve Equation (8) is read over here.
_PRINTED_D_TABLE_C5 = {
    125: [-11.9, -15.1, -16.8, -19.3, -20.5, -22.2, -23.9, -26.3, -27.2, -30.3, -31.9],
    250: [-13.7, -16.7, -19.0, -20.8, -20.7, -24.3, -26.5, -28.3, -28.8, -33.6, -35.1],
    500: [-12.4, -16.5, -18.6, -20.4, -21.7, -23.4, -25.4, -25.9, -30.2, -31.7, -33.1],
    1000: [-11.9, -15.7, -17.8, -18.8, -19.8, -22.9, -25.0, -27.3, -29.3, -33.8, -35.2],
    2000: [-11.5, -15.2, -17.7, -19.0, -20.2, -21.6, -24.6, -26.2, -30.1, -31.8, -34.5],
    4000: [-13.6, -16.2, -19.1, -20.6, -21.7, -23.1, -27.0, -29.3, -32.5, -34.9, -36.9],
}


@register(
    _WORKROOM,
    "ISO 14257:2001 Annex C, Tables C.11 and C.12 (BS EN ISO 14257:2001, PDF "
    "page 34, printed folio 24; UNE-EN ISO 14257:2002, PDF page 30, printed "
    "folio 30)",
    "Equation (8) over the printed curves does not give the printed tables, "
    "and two printings print the same numbers, so the annex is inconsistent "
    "here rather than mis-set",
)
def _chk_equation_eight_leaves_table_c11() -> Outcome:
    # Both inputs are printed curves, so the count and the spread are the
    # annex's own and do not move with the Annex B correction of this library:
    # Table C.11 is read over the printed D of Table C.5, the basis of the
    # errata entry and of the excess of Table C.9, and Table C.12 over the one
    # printed A-weighted curve there is, the last column of Table C.6.
    outside = 0
    low = high = 0.0
    for region, row in _PRINTED_EXCESS_AT_DB.items():
        keep = _keep(region)
        distance = EVALUATION_DISTANCES_M[region]
        for band, want in row.items():
            got = ph.room.level_excess_at(
                np.asarray(_PRINTED_D_TABLE_C5[band])[keep],
                _DISTANCES_M[keep],
                distance,
            )
            outside += int(abs(got - want) > 0.05)
            low, high = min(low, got - want), max(high, got - want)
    normalized = np.asarray(_CORRECTED_NORMALIZED_DB)
    for region, want in _PRINTED_EXCESS_AT_NORMALIZED_DB.items():
        keep = _keep(region)
        got = ph.room.level_excess_at(
            normalized[keep], _DISTANCES_M[keep], EVALUATION_DISTANCES_M[region]
        )
        outside += int(abs(got - want) > 0.05)
        low, high = min(low, got - want), max(high, got - want)
    return numeric(
        18.0,
        float(outside),
        0.0,
        expected_label=(
            "18 of the 21 printed results leave the rounding of their own "
            "table: 15 of the 18 of Table C.11 over Table C.5, up to 1,55 dB, "
            "and the 3 of Table C.12 over the last column of Table C.6. The "
            "two printings of the standard agree digit for digit, so neither "
            "is a misprint of the other"
        ),
        computed_label=(
            f"{outside} of 21, departures from {low:+.2f} dB to {high:+.2f} dB "
            f"with no systematic sign"
        ),
    )


# ---------------------------------------------------------------------------
# Two more workrooms, measured and worked by somebody else
# ---------------------------------------------------------------------------
#
# Annex C is one room, and the annex is the document that defines the method,
# so it cannot be a witness that the method was read right. These two can. A
# Swiss national-institute guide prints a 21 position curve and the 42
# descriptors its own analysis program read off it, and a German guidance sheet
# prints four levels at four distances and the decay rate its own printed
# formula gives for them. Neither cites this library and neither could: the
# first is dated 2006 and the second 2020, and the first never names ISO 14257
# at all, deriving the two descriptors from VDI 3760 and EN ISO 11690-1.
#
# The documents, as the rows cite them by reference and year:
#
# * Suva 66008.f is W. Lips, "Acoustique des locaux industriels. Informations
#   pour projeteurs, architectes et ingenieurs", Suva, 8th revised edition,
#   August 2006.
# * IFA-LSA 01-234 is Laermschutz-Arbeitsblatt IFA-LSA 01-234, "Raumakustik in
#   industriellen Arbeitsraeumen", IFA and DGUV, 2. aktualisierte Ausgabe,
#   April 2020.
# * Probst (2006) is W. Probst, "Gestaltung laermarmer Fertigungsstaetten in
#   metallverarbeitenden Betrieben", BAuA Schriftenreihe Forschung Fb 1083,
#   Dortmund/Berlin/Dresden 2006, whose PDF page numbers equal its folios.

#: Suva 66008.f, Tableau 2 and the Figure 7 summary: the seven columns both
#: tables are printed in. The last is the total the instrument printed rather
#: than Equation (4) over the other six: collapsing the six with the Table 1
#: weights runs 0,02 dB to 0,57 dB above it, so the total is carried here as a
#: seventh measured column and never computed.
_SUVA_COLUMNS = ("125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "total")

#: Suva 66008.f, Tableau 2: the sound distribution curve, printed as "SAK en
#: dB", which is D = Lp - Lw of Equation (1), in decibels. One entry per
#: printed row: the distance in metres against the seven columns above.
_SUVA_CURVE_DB: dict[float, tuple[float, ...]] = {
    1.0: (-9.9, -10.2, -8.0, -10.5, -8.1, -9.1, -8.9),
    2.0: (-15.0, -11.7, -13.1, -15.0, -12.2, -11.3, -13.0),
    3.0: (-21.7, -12.1, -15.0, -16.2, -12.6, -14.0, -14.2),
    4.0: (-19.2, -14.6, -15.4, -16.3, -13.3, -15.1, -14.9),
    5.0: (-19.4, -15.9, -15.9, -17.9, -13.8, -15.3, -15.6),
    6.0: (-20.5, -16.1, -14.9, -17.8, -14.1, -16.0, -15.6),
    7.0: (-20.0, -15.3, -16.4, -18.3, -15.3, -16.1, -16.4),
    8.0: (-19.5, -16.4, -17.3, -19.1, -15.5, -16.7, -17.0),
    9.0: (-20.3, -15.3, -18.2, -19.6, -15.8, -16.9, -17.4),
    10.0: (-22.1, -17.4, -18.1, -19.7, -16.0, -17.0, -17.6),
    12.0: (-21.0, -16.3, -18.9, -19.9, -16.7, -18.3, -18.2),
    14.0: (-23.3, -18.1, -19.7, -20.5, -16.3, -18.3, -18.4),
    16.0: (-23.1, -18.0, -20.4, -20.3, -17.4, -19.0, -19.0),
    18.0: (-22.4, -19.2, -18.6, -20.6, -16.9, -19.3, -18.7),
    20.0: (-22.3, -17.8, -21.5, -22.7, -18.4, -20.5, -20.3),
    24.0: (-24.5, -21.4, -21.6, -23.6, -19.2, -21.6, -21.2),
    28.0: (-25.0, -20.3, -21.3, -24.2, -19.7, -22.6, -21.5),
    32.0: (-24.7, -22.6, -23.7, -24.4, -20.7, -23.4, -22.7),
    36.0: (-24.9, -22.9, -22.7, -24.7, -21.5, -23.9, -23.0),
    40.0: (-26.4, -24.4, -23.0, -25.5, -21.1, -24.4, -23.2),
    48.0: (-26.5, -25.1, -24.7, -25.7, -22.3, -25.3, -24.2),
}

#: Suva 66008.f, the summary inside Figure 7: the decay rate its own program
#: read off that curve, in decibels per distance doubling. The rows are
#: labelled "pres", "moyen" and "loin" on the page.
_SUVA_DECAY_DB: dict[str, tuple[float, ...]] = {
    "near": (4.5, 2.3, 3.4, 3.0, 2.4, 2.9, 2.8),
    "middle": (2.2, 1.4, 3.1, 1.7, 2.0, 2.2, 2.1),
    "far": (2.6, 4.7, 2.9, 3.4, 3.4, 4.1, 3.5),
}

#: The same summary: the excess of sound pressure level, in decibels.
_SUVA_EXCESS_DB: dict[str, tuple[float, ...]] = {
    "near": (1.7, 5.8, 5.0, 3.3, 6.3, 5.7, 5.1),
    "middle": (9.0, 13.5, 12.4, 10.8, 14.4, 13.0, 12.8),
    "far": (15.4, 18.5, 17.9, 16.1, 20.1, 17.5, 18.2),
}

#: Suva 66008.f, 2.6.2: the three distance ranges, printed with both bounds,
#: in metres. The path stops at 48 m, so the far range is evaluated over 16 m
#: to 48 m.
_SUVA_RANGES_M = {"near": (1.0, 5.0), "middle": (5.0, 16.0), "far": (16.0, 64.0)}

#: Suva 66008.f, 2.6.3: the radii the same page tells a surveyor to stand at,
#: in metres.
_SUVA_RADII_M = (
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0, 16.0, 18.0,
    20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 48.0, 56.0, 64.0,
)  # fmt: skip


def _suva_range(column: str, region: str) -> tuple[np.ndarray, np.ndarray]:
    """One printed column over one printed range, as values and distances."""
    index = _SUVA_COLUMNS.index(column)
    low, high = _SUVA_RANGES_M[region]
    radii = [radius for radius in _SUVA_CURVE_DB if low <= radius <= high]
    values = [_SUVA_CURVE_DB[radius][index] for radius in radii]
    return np.array(values, dtype=float), np.array(radii, dtype=float)


@register(
    _WORKROOM,
    "Suva 66008.f (2006) Tableau 2 and Figure 7 (PDF page 13, printed page 11)",
    "Equation (5) reproduces the 21 decay rates a Swiss workroom survey "
    "prints, in three distance ranges and seven columns",
)
def _chk_suva_decay() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for region, printed in _SUVA_DECAY_DB.items():
        for column, want in zip(_SUVA_COLUMNS, printed, strict=True):
            total += 1
            got = ph.room.spatial_decay_rate(*_suva_range(column, region))
            if abs(got - want) <= 0.06:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of DL2 reproduced within 0,06 dB",
        expected_label=f"21/21 (worst departure {worst:.3f} dB)",
    )


@register(
    _WORKROOM,
    "Suva 66008.f (2006) Tableau 2 and Figure 7 (PDF page 13, printed page 11)",
    "Equations (6) and (7) reproduce the 21 printed values of the excess over "
    "a free field from the same measured curve",
)
def _chk_suva_excess() -> Outcome:
    worst = 0.0
    matching = 0
    total = 0
    for region, printed in _SUVA_EXCESS_DB.items():
        for column, want in zip(_SUVA_COLUMNS, printed, strict=True):
            total += 1
            got = ph.room.mean_level_excess(*_suva_range(column, region))
            if abs(got - want) <= 0.05:
                matching += 1
            worst = max(worst, abs(got - want))
    return count(
        matching,
        total,
        subject="printed values of DLf within the rounding of the summary",
        expected_label=f"21/21 (worst departure {worst:.3f} dB)",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Eq. (2) against Suva 66008.f (2006) Figure 7 (PDF page 13, "
    "printed page 11)",
    "The free-field reference the survey measured its excess against, "
    "recovered from its 21 printed values, is the whole sphere",
)
def _chk_suva_reference_offset() -> Outcome:
    # A wrong reference offset shifts every DLf by the same constant, so the
    # mean of the 21 residuals says which offset the other program used. It is
    # not the 8 dB of a hemisphere and not an Annex B floor correction.
    residuals = [
        ph.room.mean_level_excess(*_suva_range(column, region)) - want
        for region, printed in _SUVA_EXCESS_DB.items()
        for column, want in zip(_SUVA_COLUMNS, printed, strict=True)
    ]
    implied = FREE_FIELD_OFFSET_DB - float(np.mean(residuals))
    return numeric(
        float(10.0 * np.log10(4.0 * np.pi)),
        implied,
        0.02,
        unit="dB",
        expected_label="10 lg(4 pi) = 10,992 dB, which Eq. (2) prints as 11 dB",
        computed_label=f"{implied:.3f} dB, from the mean of the 21 residuals",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 6.2 against Suva 66008.f (2006) 2.6.2 and 2.6.3 (PDF page "
    "11, printed page 9)",
    "The three distance ranges hold every one of the 23 measurement radii the "
    "same page lists",
)
def _chk_suva_regions() -> Outcome:
    # 6.2 writes the regions as "from 1 m to d1", "from d1 to d2" and "from
    # d2", and the survey prints them as closed intervals, so 5 m and 16 m are
    # each named by two ranges and neither document says which one owns them.
    # The row therefore asks that every radius land in a range that admits it,
    # which is all either page pins.
    matching = 0
    for radius in _SUVA_RADII_M:
        region = ph.room.distance_region(float(radius))
        admitted = [
            name
            for name, (low, high) in _SUVA_RANGES_M.items()
            if low <= radius <= high
        ]
        matching += int(region in admitted)
    return count(
        matching,
        len(_SUVA_RADII_M),
        subject="radii put in a range the printed bounds admit",
    )


#: IFA-LSA 01-234, Tab. 4.4: the four positions of the path, in metres, which
#: are the distances the German technical rules for noise at work ask for.
_IFA_DISTANCES_M = np.array([0.75, 1.50, 3.00, 6.00])

#: IFA-LSA 01-234, Tab. 4.4: the sound pressure levels measured there, in
#: decibels. They are bare Lp rather than D = Lp - Lw, which Equation (5) does
#: not mind, because a constant offset cancels in a least-squares slope; the
#: sheet applies its own printed formula to the same bare levels for the same
#: reason.
_IFA_LEVELS_DB = {
    "500 Hz": [79.2, 74.4, 70.2, 67.1],
    "1 kHz": [81.9, 77.1, 73.0, 69.8],
    "2 kHz": [80.4, 75.3, 71.0, 67.4],
    "4 kHz": [84.3, 78.5, 73.2, 69.3],
}

#: IFA-LSA 01-234, Tab. 4.5: the decay rate the sheet prints for each band, in
#: decibels per distance doubling.
_IFA_DECAY_DB = {"500 Hz": 4.0, "1 kHz": 4.0, "2 kHz": 4.3, "4 kHz": 5.0}


@register(
    _WORKROOM,
    "IFA-LSA 01-234 (2020) Tab. 4.4 and Tab. 4.5 (PDF pages 17 and 18, "
    "printed folios 17 and 18)",
    "Equation (5) reproduces the decay rate a German guidance sheet prints "
    "for four octave bands measured at four distances",
)
def _chk_ifa_decay() -> Outcome:
    worst = 0.0
    matching = 0
    for band, want in _IFA_DECAY_DB.items():
        got = ph.room.spatial_decay_rate(_IFA_LEVELS_DB[band], _IFA_DISTANCES_M)
        if abs(got - want) <= 0.05:
            matching += 1
        worst = max(worst, abs(got - want))
    return count(
        matching,
        len(_IFA_DECAY_DB),
        subject="printed values of DL2 within the rounding of the table",
        expected_label=f"4/4 (worst departure {worst:.3f} dB)",
    )


@register(
    _WORKROOM,
    "IFA-LSA 01-234 (2020) Tab. 4.4 against Tab. 4.5 (PDF pages 17 and 18, "
    "printed folios 17 and 18)",
    "The 2 kHz level difference the result table prints, 4,7 dB, is not the "
    "one its own decay rate was computed from",
)
def _chk_ifa_defective_difference() -> Outcome:
    # Tab. 4.4 prints 75,3 dB and 71,0 dB at the second and third positions, a
    # difference of 4,3 dB; Tab. 4.5 prints that difference as 4,7 dB. The
    # regression says which of the two cells is right: only the printed level
    # gives the printed decay rate.
    printed_level = ph.room.spatial_decay_rate(
        _IFA_LEVELS_DB["2 kHz"], _IFA_DISTANCES_M
    )
    implied = list(_IFA_LEVELS_DB["2 kHz"])
    implied[2] = implied[1] - 4.7
    implied_level = ph.room.spatial_decay_rate(implied, _IFA_DISTANCES_M)
    want = _IFA_DECAY_DB["2 kHz"]
    agreeing = int(abs(printed_level - want) <= 0.05) + int(
        abs(implied_level - want) > 0.05
    )
    return count(
        agreeing,
        2,
        subject="readings the printed decay rate settles",
        expected_label=(
            "the printed level gives the printed 4,3 dB and the level the "
            "printed difference would need gives 4,4 dB"
        ),
    )


#: Probst, BAuA Fb 1083, Anh. 1: the volume of the room and the cumulative
#: fitting surface each of four surveyed workrooms prints, in cubic and square
#: metres, against the density printed under them, in reciprocal metres. These
#: four rooms are plain boxes whose printed volume is the product of their
#: printed dimensions; other tables in the annex carry a footnote on a
#: dimension and a volume that is not that product, and are left out.
_PROBST_FITTINGS = {
    "Tab. 3, folio 79": (1260.0, 321.9, 0.064),
    "Tab. 6, folio 82": (1848.0, 140.0, 0.019),
    "Tab. 13, folio 93": (2760.0, 160.0, 0.014),
    "Tab. 22, folio 105": (693.0, 54.0, 0.019),
}


@register(
    _WORKROOM,
    "Probst (2006) Anh. 1 Tabs. 3, 6, 13 and 22 (PDF pages and printed folios "
    "79, 82, 93 and 105)",
    "The fitting density of NOTE 3 of 6.2.2 reproduces the four values an "
    "independent VDI 3760 tool printed for surveyed workrooms",
)
def _chk_probst_fitting_density() -> Outcome:
    # The tables print three decimals, so half a unit in the last place is what
    # reproducing one means. That is two significant figures at these
    # magnitudes, which pins the form of the quotient and the factor 4 rather
    # than a tight tolerance.
    worst = 0.0
    matching = 0
    for volume, surface, want in _PROBST_FITTINGS.values():
        got = ph.room.fitting_density(surface_area_m2=surface, volume_m3=volume)
        if abs(got - want) <= 0.0005:
            matching += 1
        worst = max(worst, abs(got - want))
    return count(
        matching,
        len(_PROBST_FITTINGS),
        subject="printed densities within half of their last printed figure",
        expected_label=f"4/4 (worst departure {worst:.5f} 1/m)",
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


# --- Annex B of ISO 11690-3, the example the standard works itself ----------

#: A machine of Annex B: sound power level and emission sound pressure level in
#: decibels, position in metres, and the workstation it is the machine of, if
#: it has one.
_Machine = tuple[
    float, float, tuple[float, float, float], tuple[float, float, float] | None
]

#: Tables B.2 and B.3 (printed folio 16): the box-shaped workroom, in metres,
#: and the one mean absorption coefficient every surface of it is given.
_B_ROOM_M = (20.0, 15.0, 7.0)
_B_MEAN_ABSORPTION = 0.15

#: C.1 (printed folio 18) reads the emission sound pressure level of a machine
#: as a free-field value measured with the machine on a reflecting floor, and
#: that half space is what the direct term of Annex B radiates into.
_B_DIRECTIVITY = 2.0

#: Tables B.5 and B.8 (printed folio 18): the three workstation positions, in
#: metres. They are named here by where they stand and not by the labels the
#: annex prints, because those labels contradict its own results.
_B_BESIDE_M2 = (17.0, 4.0, 1.6)
_B_FAR_CORNER = (3.0, 12.0, 1.6)
_B_BESIDE_THE_NEW_MACHINE = (3.0, 4.0, 1.6)

#: Tables B.4 and B.7 (printed folios 17 and 18). The emission level of M1 is
#: printed in brackets and the footnote of both tables says a bracketed value
#: is not used in the calculation; M1 is the machine of no workstation, so
#: nothing here reads it.
_B_M1: _Machine = (95.0, 80.0, (10.0, 3.0, 1.0), None)
_B_M2: _Machine = (90.0, 77.0, (17.0, 3.0, 1.0), _B_BESIDE_M2)
_B_M3: _Machine = (100.0, 87.0, (3.0, 3.0, 1.0), _B_BESIDE_THE_NEW_MACHINE)
_B_M4: _Machine = (95.0, 82.0, (3.0, 3.0, 1.0), _B_BESIDE_THE_NEW_MACHINE)

#: Table B.5: what the existing workstation already hears, in decibels.
_B_BACKGROUND_DB = 50.0

#: Table B.6 (printed folio 18), the "after" column of case A, and the "before"
#: column of Table B.9, in decibels, by position.
_B_PRINTED_CASE_A = {"beside M2": 82.1, "far corner": 80.3}

#: The departure of the one cell of Table B.9 the model does not bring inside
#: the half step of its printed tenth: beside the new machine with the first
#: choice, 89,337 dB against a printed 89,4 dB. The annex prints no
#: contribution that would locate the difference, so it is recorded here as it
#: is and not attributed to anything.
_B_CASE_B_EXCEPTION_DB = -0.063

#: Table B.9 (printed folio 18), the two "after" columns, in decibels, by
#: position.
_B_PRINTED_CASE_B = {
    "first choice, M3 at 100 dB": {
        "beside M2": 86.2,
        "far corner": 85.7,
        "beside the new machine": 89.4,
    },
    "second choice, M4 at 95 dB": {
        "beside M2": 83.8,
        "far corner": 82.8,
        "beside the new machine": 85.4,
    },
}


def _distance_m(source: tuple[float, ...], station: tuple[float, ...]) -> float:
    """How far one printed position is from another, in metres."""
    return float(np.linalg.norm(np.subtract(source, station)))


def _annex_b_absorption_m2() -> float:
    """``A`` of the workroom, from the dimensions and the coefficient printed."""
    length, width, height = _B_ROOM_M
    faces = (
        length * width,
        length * width,
        length * height,
        length * height,
        width * height,
        width * height,
    )
    return float(
        ph.room.equivalent_absorption_area(
            [(area, _B_MEAN_ABSORPTION) for area in faces]
        )
    )


def _annex_b_level(
    station: tuple[float, float, float],
    machines: tuple[_Machine, ...],
    *,
    background_db: float | None = None,
) -> float:
    """What Annex B hears at one position once *machines* are running.

    Each machine contributes what the spatial sound distribution curve of the
    room gives at the distance between it and the station, except at the
    workstation the machine is the machine of, where Annex C gives it from the
    two declared emission values instead. The contributions add on an energy
    basis, and so does whatever the station already heard.
    """
    absorption = _annex_b_absorption_m2()
    parts = []
    for power, emission, position, own_station in machines:
        if own_station == station:
            parts.append(
                ph.room.workstation_level(
                    sound_power_level_db=power,
                    emission_level_db=emission,
                    absorption_area_m2=absorption,
                )
            )
        else:
            parts.append(
                float(
                    ph.room.steady_state_spl(
                        power,
                        _distance_m(position, station),
                        absorption_area=absorption,
                        directivity=_B_DIRECTIVITY,
                    )
                )
            )
    return ph.room.total_workstation_level(parts, existing_level_db=background_db)


def _annex_b_case_a() -> dict[str, float]:
    """The two levels of case A, by position."""
    return {
        "beside M2": _annex_b_level(_B_BESIDE_M2, (_B_M1, _B_M2)),
        "far corner": _annex_b_level(
            _B_FAR_CORNER, (_B_M1, _B_M2), background_db=_B_BACKGROUND_DB
        ),
    }


def _annex_b_case_b(new_machine: _Machine) -> dict[str, float]:
    """The three levels of case B for one of the two machines on offer."""
    machines = (_B_M1, _B_M2, new_machine)
    return {
        "beside M2": _annex_b_level(_B_BESIDE_M2, machines),
        "far corner": _annex_b_level(
            _B_FAR_CORNER, machines, background_db=_B_BACKGROUND_DB
        ),
        "beside the new machine": _annex_b_level(_B_BESIDE_THE_NEW_MACHINE, machines),
    }


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex B, Tables B.2 to B.6 EXAMPLE (BS EN printing, "
    "printed folios 16 to 18, PDF pp. 26 to 28)",
    "Case A: what the two workstations hear once the two new machines are "
    "installed, at the positions the annex prints",
)
def _chk_annex_b_case_a() -> Outcome:
    computed = {where: round(level, 1) for where, level in _annex_b_case_a().items()}
    return record(_B_PRINTED_CASE_A, computed, unit="dB")


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex B, Tables B.7 to B.9 EXAMPLE (BS EN printing, "
    "printed folio 18, PDF p. 28)",
    "Case B: the six levels printed for the two machines on offer, at the "
    "three workstation positions",
)
def _chk_annex_b_case_b() -> Outcome:
    worst = 0.0
    exception = 0.0
    matching = 0
    total = 0
    for machine, row in zip((_B_M3, _B_M4), _B_PRINTED_CASE_B.values(), strict=True):
        computed = _annex_b_case_b(machine)
        for where, want in row.items():
            total += 1
            departure = computed[where] - want
            if (machine, where) == (_B_M3, "beside the new machine"):
                # The one cell outside the half step, pinned at its own
                # departure rather than widening the tolerance of all six.
                exception = departure
                matching += int(abs(departure - _B_CASE_B_EXCEPTION_DB) <= 0.001)
            else:
                worst = max(worst, abs(departure))
                matching += int(abs(departure) <= 0.05)
    return count(
        matching,
        total,
        subject="printed levels of Table B.9",
        expected_label=(
            f"6/6: five within the 0,05 dB half step of the printed tenth "
            f"(worst {worst:.3f} dB), and the cell beside the new machine with "
            f"the first choice at its recorded {_B_CASE_B_EXCEPTION_DB:+.3f} dB "
            f"(computed {exception:+.4f} dB)"
        ),
    )


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex B, Figure B.1 against Tables B.5 and B.8 (BS EN "
    "printing, printed folios 16 and 18)",
    "The results of Annex B belong to the positions Figure B.1 draws, and "
    "not to the ones the two workstation tables put the same labels on",
)
def _chk_annex_b_labels() -> Outcome:
    computed = {
        "before": _annex_b_case_a(),
        "first choice, M3 at 100 dB": _annex_b_case_b(_B_M3),
        "second choice, M4 at 95 dB": _annex_b_case_b(_B_M4),
    }
    printed = {"before": _B_PRINTED_CASE_A, **_B_PRINTED_CASE_B}
    # Figure B.1 draws W1 immediately above M2 and W2 alone in the far corner,
    # which is how the cells of Tables B.6 and B.9 are keyed above; Tables B.5
    # and B.8 tabulate coordinates for the same two labels the other way round.
    as_drawn = {"W1": "beside M2", "W2": "far corner"}
    as_tabulated = {"W1": "far corner", "W2": "beside M2"}
    drawn = 0
    tabulated = 0
    for column, row in printed.items():
        for label, position in as_drawn.items():
            want = row[position]
            drawn += int(abs(computed[column][position] - want) <= 0.1)
            tabulated += int(abs(computed[column][as_tabulated[label]] - want) <= 0.1)
    return count(
        drawn,
        len(printed) * 2,
        subject="printed cells reproduced at the position Figure B.1 draws",
        expected_label=(
            f"6/6, against {tabulated}/6 at the positions Tables B.5 and B.8 "
            "tabulate, which are between 0,5 dB and 1,8 dB out"
        ),
    )


@register(
    _WORKROOM,
    "ISO 11690-3:1998 Annex C, Table C.2 last column EXAMPLE (BS EN "
    "printing, printed folio 20, PDF p. 30)",
    "The level at a machine's own workstation rounds to the printed integer "
    "for all seven machines the diagram of Figure C.1 can show",
)
def _chk_annex_c_level_of_11690() -> Outcome:
    # Table C.1 (printed folio 19), as sound power level and emission level in
    # decibels, against the L'pA of Table C.2. The eighth machine is the one
    # the diagram cannot show, and the Figure C.1 row of this domain has it.
    declared = {
        "M1": (105.0, 79.0),
        "M2": (98.0, 81.0),
        "M3": (107.0, 87.0),
        "M4": (94.0, 82.0),
        "M5": (102.0, 84.0),
        "M6": (96.0, 82.0),
        "M7": (101.0, 84.0),
    }
    printed = {
        "M1": 89.0,
        "M2": 84.0,
        "M3": 92.0,
        "M4": 83.0,
        "M5": 88.0,
        "M6": 84.0,
        "M7": 87.0,
    }
    computed = {
        name: float(
            round(
                ph.room.workstation_level(
                    sound_power_level_db=power,
                    emission_level_db=emission,
                    absorption_area_m2=195.0,
                )
            )
        )
        for name, (power, emission) in declared.items()
    }
    return record(printed, computed, unit="dB")


@register(
    _WORKROOM,
    "ISO 11690-3:1998 4.3 (BS EN printing, printed folios 2 and 3, PDF pp. 12 and 13)",
    "The bounds the clause prints for the two descriptors, region by region, "
    "with the five it leaves open left open",
)
def _chk_clause_43_ranges() -> Outcome:
    printed: dict[str, tuple[float | None, float | None]] = {
        "DL2 near": (5.0, 6.0),
        "DL2 middle": (2.0, 5.0),
        "DL2 far": (6.0, None),
        "DLf near": (None, None),
        "DLf middle": (2.0, 10.0),
        "DLf far": (None, None),
    }
    reader = {"DL2": ph.room.typical_decay_range, "DLf": ph.room.typical_excess_range}
    matching = 0
    for name, bounds in printed.items():
        descriptor, region = name.split()
        matching += sum(
            got == want
            for got, want in zip(reader[descriptor](region), bounds, strict=True)
        )
    return count(
        matching,
        2 * len(printed),
        subject="bounds of 4.3, the five the clause prints no number for included",
    )


# --- The worked examples that stand in where a standard prints none ---------

#: IFA-LSA 01-234, Tab. 4.2 (printed folio 14): two-measurement means of T20 in
#: a production hall, in seconds, by octave centre.
_IFA_REVERBERATION_S = (3.5, 3.8, 3.3, 2.5)

#: The same page prints "V = 30 . 20 . 10 m3 = 6000 m3" and
#: "S = 2 . 20 . 30 m2 + 2 . 10 . 30 m2 + 2 . 10 . 20 m2 = 2200 m2".
_IFA_VOLUME_M3 = 30.0 * 20.0 * 10.0
_IFA_SURFACE_M2 = 2.0 * (20.0 * 30.0 + 10.0 * 30.0 + 10.0 * 20.0)

#: Eq. (4.1) of the same sheet is printed with the 0,163 form of the Sabine
#: constant, which is 24 ln 10 / c at c = 339 m/s; the library defaults to
#: 343 m/s, which is the 0,161 form and about 1 % of absorption area away.
_IFA_SPEED_M_S = 339.0


def _ifa_absorption_area_m2() -> list[float]:
    """``A`` of the hall, band by band, from the times the sheet measured."""
    return [
        float(area)
        for area in np.asarray(
            ph.room.sabine_absorption_area(
                _IFA_VOLUME_M3, _IFA_REVERBERATION_S, speed_of_sound=_IFA_SPEED_M_S
            )
        ).tolist()
    ]


@register(
    _WORKROOM,
    "IFA-LSA 01-234 (2020) Tab. 4.2 (printed folio 14, PDF p. 14)",
    "The equivalent absorption area of a 6 000 m3 production hall, from the "
    "reverberation times measured in it",
)
def _chk_ifa_absorption_area() -> Outcome:
    printed = {"500 Hz": 279.0, "1 kHz": 257.0, "2 kHz": 296.0, "4 kHz": 391.0}
    computed = dict(
        zip(
            printed,
            (float(round(area)) for area in _ifa_absorption_area_m2()),
            strict=True,
        )
    )
    return record(printed, computed, unit="m²")


@register(
    _WORKROOM,
    "IFA-LSA 01-234 (2020) Tab. 4.2 (printed folio 14, PDF p. 14)",
    "The mean absorption coefficient of the same hall, which is that area "
    "over the 2 200 m2 of boundary the sheet works out from its dimensions",
)
def _chk_ifa_mean_absorption() -> Outcome:
    printed = {"500 Hz": 0.13, "1 kHz": 0.12, "2 kHz": 0.13, "4 kHz": 0.18}
    computed = dict(
        zip(
            printed,
            (round(area / _IFA_SURFACE_M2, 2) for area in _ifa_absorption_area_m2()),
            strict=True,
        )
    )
    return record(printed, computed)


@register(
    _WORKROOM,
    "Ver & Beranek 2e, Table 7.4 and the text before it (printed folios 199 "
    "and 200, PDF pp. 203 and 204)",
    "Nine machines around one assembly bench add on a power basis to the two "
    "printed totals, and to the benefit of treating the ceiling",
)
def _chk_energy_addition_at_a_workstation() -> Outcome:
    # I. L. Ver and L. L. Beranek (eds.), Noise and Vibration Control
    # Engineering, 2nd edition, Wiley, 2006. Table 7.4 on printed folio 200
    # prints the nine contributions and the two totals; the 3,7 dB benefit is
    # printed in the text on folio 199, as the difference of those two totals.
    before = ph.room.total_workstation_level(
        [70.7, 79.1, 71.1, 75.6, 64.2, 69.1, 69.6, 67.6, 69.0]
    )
    after = ph.room.total_workstation_level(
        [65.3, 74.8, 67.5, 73.5, 60.0, 65.5, 65.6, 63.8, 63.2]
    )
    printed = {"before treatment": 82.4, "after treatment": 78.7, "the benefit": 3.7}
    computed = {
        "before treatment": before,
        "after treatment": after,
        "the benefit": before - after,
    }
    worst = max(abs(computed[name] - want) for name, want in printed.items())
    matching = sum(abs(computed[name] - want) <= 0.06 for name, want in printed.items())
    return count(
        matching,
        len(printed),
        subject="printed totals and the benefit printed beside them",
        expected_label=(
            f"3/3 (worst departure {worst:.2f} dB, on the total before "
            "treatment: the nine contributions are themselves printed to "
            "0,1 dB, so their sum can only be recovered to half a step)"
        ),
    )


# --- Barron (2003), the direct-plus-reverberant field of a category 1 method -

#: Example 7-8 and Table 7-5 (printed folios 307 and 308): a production machine
#: in a 20 m by 20 m by 4 m room of 1 120 m2 of boundary, with the operator 3 m
#: away and a directivity factor of unity. The sound power level and the room
#: constant are printed by octave band; the room constant is the column to
#: feed, because the absorption coefficient printed at 2 kHz does not give it.
_BARRON_SURFACE_M2 = 1120.0
_BARRON_DISTANCE_M = 3.0
_BARRON_POWER_DB = (103.0, 109.0, 114.0, 117.0, 113.0, 107.0)
_BARRON_ROOM_CONSTANT_M2 = (40.62, 51.55, 60.19, 84.30, 47.88, 66.44)

#: Eqs. (7-18) and (7-73) carry 10 lg(rho c / 400) as the literal +0,1 dB the
#: book rounds it to, and the worked lines add exactly that.
_BARRON_IMPEDANCE_TERM_DB = 0.1


@register(
    _WORKROOM,
    "Barron (2003) Example 7-8 and Table 7-5 (printed folios 307 to 309, PDF "
    "pp. 319 to 321)",
    "The level at the operator in six octave bands, with the direct term as "
    "the statement and the worked line write it, Q/(4 pi r^2)",
)
def _chk_barron_example_7_8() -> Outcome:
    printed = {
        "125 Hz": 93.4,
        "250 Hz": 98.5,
        "500 Hz": 102.9,
        "1 kHz": 104.6,
        "2 kHz": 102.8,
        "4 kHz": 95.5,
    }
    levels = np.asarray(
        ph.room.steady_state_spl(
            _BARRON_POWER_DB,
            _BARRON_DISTANCE_M,
            _BARRON_ROOM_CONSTANT_M2,
            directivity=1.0,
        )
    )
    computed = dict(
        zip(
            printed,
            (round(level + _BARRON_IMPEDANCE_TERM_DB, 1) for level in levels.tolist()),
            strict=True,
        )
    )
    return record(printed, computed, unit="dB")


@register(
    _WORKROOM,
    "Barron (2003) Table 7-5 against itself (printed folio 308, PDF p. 320)",
    "The room constant printed at 2 kHz is the one a mean absorption of "
    "0,041 gives, and not the 0,043 the row above it prints",
)
def _chk_barron_table_7_5_absorption_row() -> Outcome:
    implied = float(ph.room.room_constant(_BARRON_SURFACE_M2, 0.041))
    printed_absorption = float(ph.room.room_constant(_BARRON_SURFACE_M2, 0.043))
    return numeric(
        47.88,
        implied,
        0.005,
        unit="m²",
        expected_label="the 47,88 m2 Table 7-5 prints at 2 kHz",
        computed_label=(
            f"{implied:.2f} m2 from a mean absorption of 0,041, against the "
            f"{printed_absorption:.2f} m2 the printed 0,043 gives"
        ),
    )


@register(
    _WORKROOM,
    "Barron (2003) Example 7-6 (printed folio 298, PDF p. 310)",
    "The level in a paper mill refiner room, from the room constant the "
    "example works out and a directivity factor of 2",
)
def _chk_barron_example_7_6() -> Outcome:
    room_constant = float(ph.room.room_constant(900.0, 0.05))
    level = (
        float(ph.room.steady_state_spl(105.0, 4.0, room_constant, directivity=2.0))
        + _BARRON_IMPEDANCE_TERM_DB
    )
    return numeric(
        94.8,
        level,
        0.06,
        unit="dB",
        places=2,
        expected_label="the 94,8 dB the example prints, for a room constant of 47,37 m2",
        computed_label=(
            f"{level:.2f} dB, from the {room_constant:.2f} m2 the library "
            "returns for (0,05)(900)/(1 - 0,05)"
        ),
    )
