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
from reference_data import enclosure_cabin_insulation as enclosure
from reference_data import spatial_decay as spatial
from reference_data import workroom_prediction as prediction

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

#: The printed tables of ISO 14257 Annex C, ISO 11690-3 Annexes B and C and the
#: documents that stand beside them are in ``tests/reference_data/``
#: ``spatial_decay.py``, ``workroom_prediction.py`` and
#: ``enclosure_cabin_insulation.py``, each with its folio and page, and the
#: test suite reads them there too.

#: Table C.1: the eleven microphone positions, as an array to select from.
_DISTANCES_M = np.array(spatial.ANNEX_C_DISTANCES_M, dtype=float)


def _raw(band: int) -> np.ndarray:
    return ph.room.sound_distribution_value(
        spatial.ANNEX_C_ROOM_LEVELS_DB[band], spatial.ANNEX_C_SOURCE_POWER_DB[band]
    )


def _corrected(band: int) -> np.ndarray:
    measured = ph.room.sound_distribution_value(
        spatial.ANNEX_C_FREE_FIELD_LEVELS_DB[band],
        spatial.ANNEX_C_SOURCE_POWER_DB[band],
    )
    return ph.room.corrected_distribution_value(
        _raw(band), measured, _DISTANCES_M, source_height_m=0.0
    )


def _keep(region: str) -> np.ndarray:
    low, high = spatial.ANNEX_C_RANGES_M[region]
    return np.asarray((_DISTANCES_M >= low) & (_DISTANCES_M <= high), dtype=bool)


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
    for band, printed in spatial.ANNEX_C_TABLE_C6_DB.items():
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
    "The A-weighted pink-noise normalisation of Eq. (4), with the printed "
    "6,2 dB, reproduces the eleven printed values to within 0,1 dB",
)
def _chk_table_c6_normalized() -> Outcome:
    # 0,1 dB and not the printed 0,05: the 6,2 dB Eq. (4) prints is the
    # A-weighting curve's energy sum rounded to one decimal, the six weights
    # Table 1 prints, rounded on their own, sum to 6,2515 dB, and the annex was
    # normalised exactly, so the printed constant returns every value 0,05 dB
    # high on top of the rounding. The next row holds the split; the errata
    # records it.
    printed = spatial.ANNEX_C_TABLE_C6_NORMALIZED_DB
    corrected = {band: _corrected(band) for band in spatial.ANNEX_C_SOURCE_POWER_DB}
    got = [
        ph.room.normalized_distribution_value(
            [corrected[band][i] for band in spatial.ANNEX_C_SOURCE_POWER_DB]
        )
        for i in range(_DISTANCES_M.size)
    ]
    departures = [a - b for a, b in zip(got, printed, strict=True)]
    worst = max(abs(d) for d in departures)
    high = sum(d > 0.05 for d in departures)
    return numeric(
        0.0,
        worst,
        0.1,
        unit="dB",
        expected_label=(
            "every value within 0,1 dB: the printed 6,2 dB is 0,05 dB short of "
            "the sum of the printed Table 1 weights, which is what the annex "
            "normalised with, so a cell can come out one unit high in the last "
            "place and never low"
        ),
        computed_label=(
            f"worst departure {worst:.2f} dB over 11 positions, {high} of them "
            "beyond the printed rounding and all of those high"
        ),
    )


#: How many of the fourteen Annex C values the printed 6,2 dB of Eq. (4) puts
#: outside their rounding, every one of them a tenth high. Recorded, not derived:
#: it is the finding the row publishes, so a change in it has to fail the row.
_PRINTED_OFFSET_CELLS_OUTSIDE = 9


@register(
    _WORKROOM,
    "ISO 14257:2001 Eq. (4) against Annex C, Table C.6 last column and Table "
    "C.10 (ISO 14257:2001, PDF page 10, printed folio 4; BS EN ISO 14257:2001, "
    "PDF page 14, printed folio 4)",
    "The 6,2 dB Eq. (4) prints is the A-weighting curve's energy sum rounded, "
    "the six weights Table 1 prints sum to 6,2515 dB, and the annex was "
    "normalised exactly: Eq. (3) under the Table 1 weights lands all fourteen "
    "printed values inside their rounding where the printed constant lands "
    "nine of them one unit high",
)
def _chk_equation_four_offset_against_annex_c() -> Outcome:
    # Eq. (3) with the Table 1 weights as the machine spectrum is Eq. (4) with
    # the sum of those weights in place of the printed 6,2 dB. Both readings run
    # over the unrounded Annex B chain from the printed Tables C.2 to C.4, and
    # the count of cells outside +/-0,05 dB is taken for each: the sum must
    # land none outside, and the printed constant must land some, every one of
    # them high.
    weights = [
        PINK_NOISE_WEIGHTS_DB[float(band)] for band in spatial.ANNEX_C_SOURCE_POWER_DB
    ]
    corrected = {band: _corrected(band) for band in spatial.ANNEX_C_SOURCE_POWER_DB}
    raw = {band: _raw(band) for band in spatial.ANNEX_C_SOURCE_POWER_DB}

    def _both(curve: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        rows = [
            [curve[band][i] for band in spatial.ANNEX_C_SOURCE_POWER_DB]
            for i in range(_DISTANCES_M.size)
        ]
        by_sum = np.array(
            [ph.room.spectrum_distribution_value(row, weights) for row in rows]
        )
        by_print = np.array(
            [ph.room.normalized_distribution_value(row) for row in rows]
        )
        return by_sum, by_print

    by_sum, by_print = _both(corrected)
    dep_sum = (by_sum - np.asarray(spatial.ANNEX_C_TABLE_C6_NORMALIZED_DB)).tolist()
    dep_print = (by_print - np.asarray(spatial.ANNEX_C_TABLE_C6_NORMALIZED_DB)).tolist()
    raw_by_sum, raw_by_print = _both(raw)
    for region, want in spatial.ANNEX_C_TABLE_C10_DB.items():
        keep = _keep(region)
        dep_sum.append(
            ph.room.mean_level_excess(raw_by_sum[keep], _DISTANCES_M[keep]) - want
        )
        dep_print.append(
            ph.room.mean_level_excess(raw_by_print[keep], _DISTANCES_M[keep]) - want
        )
    cells = len(dep_sum)
    outside_sum = sum(abs(d) > 0.05 for d in dep_sum)
    outside_print = sum(abs(d) > 0.05 for d in dep_print)
    low_print = sum(d < 0.0 for d in dep_print)
    past_one_unit = sum(d > 0.15 for d in dep_print)
    # Every claim the row states is judged, not only the first: the sum lands no
    # cell outside the rounding, the printed constant lands the recorded number
    # of them outside, none of its departures is low, and none reaches a second
    # unit of the tenth. A verdict on the sum alone would go on passing the day
    # the printed constant agreed with the annex, while the row still said not.
    violations = (
        outside_sum
        + abs(outside_print - _PRINTED_OFFSET_CELLS_OUTSIDE)
        + low_print
        + past_one_unit
    )
    return numeric(
        0.0,
        float(violations),
        0.0,
        expected_label=(
            f"0 of {cells} outside the printed rounding with the Table 1 sum, "
            f"against {_PRINTED_OFFSET_CELLS_OUTSIDE} of {cells} with the printed "
            f"6,2 dB, every one of the {cells} high and none by a second unit"
        ),
        computed_label=(
            f"{outside_sum} of {cells} with the sum (worst "
            f"{max(abs(d) for d in dep_sum):.3f} dB, both signs); "
            f"{outside_print} of {cells} with 6,2 dB (worst "
            f"{max(abs(d) for d in dep_print):.3f} dB, {low_print} low, "
            f"{past_one_unit} past one unit)"
        ),
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
    for region, row in spatial.ANNEX_C_TABLE_C7_DB.items():
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
    for region, row in spatial.ANNEX_C_TABLE_C9_DB.items():
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
    for region, row in spatial.ANNEX_C_TABLE_C7_DB.items():
        keep = _keep(region)
        for band, want in row.items():
            got = ph.room.spatial_decay_rate(_raw(band)[keep], _DISTANCES_M[keep])
            swapped += int(abs(got - want) > 0.06)
    for region, row in spatial.ANNEX_C_TABLE_C9_DB.items():
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
        expected_label="lg 2 = 0,301 03",
        computed_label="the printed 0,3, which is 0,34 % smaller",
    )


@register(
    _WORKROOM,
    "ISO 14257:2001 Table 1",
    "The A-weighted pink-noise spectrum weights the six octave bands the "
    "way Table 1 prints them",
)
def _chk_table_one() -> Outcome:
    labels = ("125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz")
    printed = dict(
        zip(labels, spatial.TABLE_1_PINK_NOISE_WEIGHTS_DB.values(), strict=True)
    )
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
    declared = spatial.ANNEX_C_SOURCE_DECLARATION_DB
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
        ph.room.normalized_distribution_value(
            list(spatial.ANNEX_C_SOURCE_POWER_DB.values())
        )
        + NORMALIZED_OFFSET_DB
    )
    return numeric(
        spatial.ANNEX_C_SOURCE_POWER_A_WEIGHTED_DB, float(total), 0.05, unit="dB"
    )


# ---------------------------------------------------------------------------
# Equation (8), which the annex prints results for that it does not produce
# ---------------------------------------------------------------------------


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
    for region, row in spatial.ANNEX_C_TABLE_C11_DB.items():
        keep = _keep(region)
        distance = EVALUATION_DISTANCES_M[region]
        for band, want in row.items():
            got = ph.room.level_excess_at(
                np.asarray(spatial.ANNEX_C_TABLE_C5_DB[band])[keep],
                _DISTANCES_M[keep],
                distance,
            )
            outside += int(abs(got - want) > 0.05)
            low, high = min(low, got - want), max(high, got - want)
    normalized = np.asarray(spatial.ANNEX_C_TABLE_C6_NORMALIZED_DB)
    for region, want in spatial.ANNEX_C_TABLE_C12_DB.items():
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


def _suva_range(column: str, region: str) -> tuple[np.ndarray, np.ndarray]:
    """One printed column over one printed range, as values and distances."""
    index = spatial.SUVA_COLUMNS.index(column)
    low, high = spatial.SUVA_RANGES_M[region]
    radii = [radius for radius in spatial.SUVA_CURVE_DB if low <= radius <= high]
    values = [spatial.SUVA_CURVE_DB[radius][index] for radius in radii]
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
    for region, printed in spatial.SUVA_DECAY_DB.items():
        for column, want in zip(spatial.SUVA_COLUMNS, printed, strict=True):
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
    for region, printed in spatial.SUVA_EXCESS_DB.items():
        for column, want in zip(spatial.SUVA_COLUMNS, printed, strict=True):
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
        for region, printed in spatial.SUVA_EXCESS_DB.items()
        for column, want in zip(spatial.SUVA_COLUMNS, printed, strict=True)
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
    for radius in spatial.SUVA_RADII_M:
        region = ph.room.distance_region(float(radius))
        admitted = [
            name
            for name, (low, high) in spatial.SUVA_RANGES_M.items()
            if low <= radius <= high
        ]
        matching += int(region in admitted)
    return count(
        matching,
        len(spatial.SUVA_RADII_M),
        subject="radii put in a range the printed bounds admit",
    )


#: IFA-LSA 01-234, Tab. 4.4: the four positions of the path, as an array.
_IFA_DISTANCES_M = np.array(spatial.IFA_LSA_01_234_DISTANCES_M)


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
    for band, want in spatial.IFA_LSA_01_234_DECAY_DB.items():
        got = ph.room.spatial_decay_rate(
            spatial.IFA_LSA_01_234_LEVELS_DB[band], _IFA_DISTANCES_M
        )
        if abs(got - want) <= 0.05:
            matching += 1
        worst = max(worst, abs(got - want))
    return count(
        matching,
        len(spatial.IFA_LSA_01_234_DECAY_DB),
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
    levels = spatial.IFA_LSA_01_234_LEVELS_DB[2000]
    printed_level = ph.room.spatial_decay_rate(levels, _IFA_DISTANCES_M)
    implied = list(levels)
    implied[2] = implied[1] - spatial.IFA_LSA_01_234_DIFFERENCES_DB["Lp2 - Lp3"][2]
    implied_level = ph.room.spatial_decay_rate(implied, _IFA_DISTANCES_M)
    want = spatial.IFA_LSA_01_234_DECAY_DB[2000]
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
    for (*_, volume), _, surface, want in spatial.PROBST_ROOMS.values():
        got = ph.room.fitting_density(surface_area_m2=surface, volume_m3=volume)
        if abs(got - want) <= 0.0005:
            matching += 1
        worst = max(worst, abs(got - want))
    return count(
        matching,
        len(spatial.PROBST_ROOMS),
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
    printed = prediction.ANNEX_C_MACHINES_DB
    worst = 0.0
    matching = 0
    for power, emission, want, _ in printed.values():
        got = ph.room.workstation_level_increase(
            sound_power_level_db=power,
            emission_level_db=emission,
            absorption_area_m2=prediction.ANNEX_C_ABSORPTION_M2,
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
    power, emission, _, _ = prediction.ANNEX_C_M8_DB
    got = ph.room.workstation_level_increase(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=prediction.ANNEX_C_ABSORPTION_M2,
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
    for band in spatial.ANNEX_C_SOURCE_POWER_DB:
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

#: C.1 (printed folio 18) reads the emission sound pressure level of a machine
#: as a free-field value measured with the machine on a reflecting floor, and
#: that half space is what the direct term of Annex B radiates into.
_B_DIRECTIVITY = 2.0

#: Tables B.4 and B.7 (printed folios 17 and 18), the four machines, by name.
_B_M1: _Machine = prediction.ANNEX_B_MACHINES["M1"]
_B_M2: _Machine = prediction.ANNEX_B_MACHINES["M2"]
_B_M3: _Machine = prediction.ANNEX_B_MACHINES["M3"]
_B_M4: _Machine = prediction.ANNEX_B_MACHINES["M4"]

#: The departure of the one cell of Table B.9 the model does not bring inside
#: the half step of its printed tenth: beside the new machine with the first
#: choice, 89,337 dB against a printed 89,4 dB. The annex prints no
#: contribution that would locate the difference, so it is recorded here as it
#: is and not attributed to anything.
_B_CASE_B_EXCEPTION_DB = -0.063


def _distance_m(source: tuple[float, ...], station: tuple[float, ...]) -> float:
    """How far one printed position is from another, in metres."""
    return float(np.linalg.norm(np.subtract(source, station)))


def _annex_b_absorption_m2() -> float:
    """``A`` of the workroom, from the dimensions and the coefficient printed."""
    length, width, height = prediction.ANNEX_B_ROOM_M
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
            [(area, prediction.ANNEX_B_MEAN_ABSORPTION) for area in faces]
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
        # Table B.5 prints the 50 dB of background against the label W1, and the
        # label is the half of that table this annex gets right: Figure B.1 puts
        # W1 beside M2, and the levels of Table B.6 come back there. So the
        # background is heard beside M2 and not in the far corner, which is
        # where the label W2 belongs. It is worth 0,004 dB either way, and both
        # readings round to the printed tenth; this one is the one that agrees
        # with the rest of the row.
        "beside M2": _annex_b_level(
            prediction.ANNEX_B_BESIDE_M2,
            (_B_M1, _B_M2),
            background_db=prediction.ANNEX_B_BACKGROUND_DB,
        ),
        "far corner": _annex_b_level(prediction.ANNEX_B_FAR_CORNER, (_B_M1, _B_M2)),
    }


def _annex_b_case_b(new_machine: _Machine) -> dict[str, float]:
    """The three levels of case B for one of the two machines on offer."""
    machines = (_B_M1, _B_M2, new_machine)
    return {
        "beside M2": _annex_b_level(
            prediction.ANNEX_B_BESIDE_M2,
            machines,
            background_db=prediction.ANNEX_B_BACKGROUND_DB,
        ),
        "far corner": _annex_b_level(prediction.ANNEX_B_FAR_CORNER, machines),
        "beside the new machine": _annex_b_level(
            prediction.ANNEX_B_BESIDE_THE_NEW_MACHINE, machines
        ),
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
    return record(prediction.ANNEX_B_PRINTED_CASE_A_DB, computed, unit="dB")


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
    for machine, row in zip(
        (_B_M3, _B_M4), prediction.ANNEX_B_PRINTED_CASE_B_DB.values(), strict=True
    ):
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
            f"{total}/{total}: all but one within the 0,05 dB half step of "
            f"the printed tenth (worst {worst:.3f} dB), and the cell beside the "
            f"new machine with the first choice at its recorded "
            f"{_B_CASE_B_EXCEPTION_DB:+.3f} dB (computed {exception:+.4f} dB)"
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
    printed = {
        "before": prediction.ANNEX_B_PRINTED_CASE_A_DB,
        **prediction.ANNEX_B_PRINTED_CASE_B_DB,
    }
    # Figure B.1 draws W1 immediately above M2 and W2 alone in the far corner,
    # which is how the cells of Tables B.6 and B.9 are keyed above; Tables B.5
    # and B.8 tabulate coordinates for the same two labels the other way round.
    as_drawn = {"W1": "beside M2", "W2": "far corner"}
    as_tabulated = {"W1": "far corner", "W2": "beside M2"}
    # Both readings are counted: each printed cell has to come back at the
    # position the figure draws and has to miss at the one the tables give.
    reproduced = 0
    rejected = 0
    misses = []
    for column, row in printed.items():
        for label, position in as_drawn.items():
            want = row[position]
            reproduced += int(abs(computed[column][position] - want) <= 0.1)
            miss = abs(computed[column][as_tabulated[label]] - want)
            misses.append(miss)
            rejected += int(miss > 0.1)
    cells = len(printed) * 2
    return count(
        reproduced + rejected,
        2 * cells,
        subject=(
            f"readings of the {cells} printed cells, reproduced at the "
            "positions Figure B.1 draws and rejected at the positions Tables "
            "B.5 and B.8 tabulate"
        ),
        expected_label=(
            f"{2 * cells}/{2 * cells}: the {cells} cells within 0,1 dB at the "
            f"positions Figure B.1 draws, and the same {cells} more than 0,1 dB "
            f"out at the positions Tables B.5 and B.8 tabulate (nearest "
            f"{min(misses):.3f} dB, farthest {max(misses):.3f} dB)"
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
    machines = prediction.ANNEX_C_MACHINES_DB
    declared = {
        name: (power, emission) for name, (power, emission, _, _) in machines.items()
    }
    printed = {name: level for name, (_, _, _, level) in machines.items()}
    computed = {
        name: float(
            round(
                ph.room.workstation_level(
                    sound_power_level_db=power,
                    emission_level_db=emission,
                    absorption_area_m2=prediction.ANNEX_C_ABSORPTION_M2,
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

#: IFA-LSA 01-234, Tab. 4.2 (printed folio 14): the volume and the boundary area
#: the same page works out of the dimensions of the hall it prints.
_IFA_LENGTH_M, _IFA_BREADTH_M, _IFA_HEIGHT_M = prediction.IFA_LSA_01_234_HALL_M
_IFA_VOLUME_M3 = _IFA_LENGTH_M * _IFA_BREADTH_M * _IFA_HEIGHT_M
_IFA_SURFACE_M2 = 2.0 * (
    _IFA_BREADTH_M * _IFA_LENGTH_M
    + _IFA_HEIGHT_M * _IFA_LENGTH_M
    + _IFA_HEIGHT_M * _IFA_BREADTH_M
)


def _ifa_absorption_area_m2() -> list[float]:
    """``A`` of the hall, band by band, from the times the sheet measured."""
    return [
        float(area)
        for area in np.asarray(
            ph.room.sabine_absorption_area(
                _IFA_VOLUME_M3,
                prediction.IFA_LSA_01_234_REVERBERATION_S,
                speed_of_sound=prediction.IFA_LSA_01_234_SPEED_M_S,
            )
        ).tolist()
    ]


@register(
    _WORKROOM,
    "IFA-LSA 01-234 (2020) Tab. 4.2 (printed folio 14, PDF p. 14)",
    "The equivalent absorption area of a 6 000 m3 production hall, from the "
    "reverberation times measured in it",
)
def _chk_ifa_absorption_area() -> Outcome:
    labels = ("500 Hz", "1 kHz", "2 kHz", "4 kHz")
    printed = dict(zip(labels, prediction.IFA_LSA_01_234_PRINTED_AREA_M2, strict=True))
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
    "over the 2 200 m2 of boundary the sheet works out from its dimensions",
)
def _chk_ifa_mean_absorption() -> Outcome:
    labels = ("500 Hz", "1 kHz", "2 kHz", "4 kHz")
    printed = dict(
        zip(labels, prediction.IFA_LSA_01_234_PRINTED_ABSORPTION, strict=True)
    )
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
        list(prediction.VER_BERANEK_TABLE_7_4_BEFORE_DB)
    )
    after = ph.room.total_workstation_level(
        list(prediction.VER_BERANEK_TABLE_7_4_AFTER_DB)
    )
    total_before, total_after = prediction.VER_BERANEK_TABLE_7_4_TOTALS_DB
    printed = {
        "before treatment": total_before,
        "after treatment": total_after,
        "the benefit": prediction.VER_BERANEK_TREATMENT_BENEFIT_DB,
    }
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


@register(
    _WORKROOM,
    "Barron (2003) Example 7-8 and Table 7-5 (printed folios 307 to 309, PDF "
    "pp. 319 to 321)",
    "The level at the operator in six octave bands, with the direct term as "
    "the statement and the worked line write it, Q/(4 pi r^2)",
)
def _chk_barron_example_7_8() -> Outcome:
    labels = ("125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz")
    printed = dict(zip(labels, enclosure.BARRON_TABLE_7_5_LP_WITHOUT_DB, strict=True))
    levels = np.asarray(
        ph.room.steady_state_spl(
            enclosure.BARRON_TABLE_7_5_LW_DB,
            enclosure.BARRON_EXAMPLE_7_8_OPERATOR_DISTANCE_M,
            enclosure.BARRON_TABLE_7_5_ROOM_CONSTANT_M2,
            directivity=1.0,
        )
    )
    computed = dict(
        zip(
            printed,
            (
                round(level + prediction.BARRON_IMPEDANCE_TERM_DB, 1)
                for level in levels.tolist()
            ),
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
    surface = enclosure.BARRON_EXAMPLE_7_8_SURFACE_M2
    implied = float(ph.room.room_constant(surface, 0.041))
    printed_absorption = float(
        ph.room.room_constant(surface, enclosure.BARRON_TABLE_7_5_ABSORPTION_AT_2_KHZ)
    )
    return numeric(
        enclosure.BARRON_TABLE_7_5_ROOM_CONSTANT_M2[4],
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
    room_constant = float(
        ph.room.room_constant(
            prediction.BARRON_EXAMPLE_7_6_SOURCE_SURFACE_M2,
            prediction.BARRON_EXAMPLE_7_6_SOURCE_ABSORPTION,
        )
    )
    level = (
        float(
            ph.room.steady_state_spl(
                prediction.BARRON_EXAMPLE_7_6_POWER_LEVEL_DB,
                prediction.BARRON_EXAMPLE_7_6_SOURCE_DISTANCE_M,
                room_constant,
                directivity=prediction.BARRON_EXAMPLE_7_6_DIRECTIVITY,
            )
        )
        + prediction.BARRON_IMPEDANCE_TERM_DB
    )
    return numeric(
        prediction.BARRON_EXAMPLE_7_6_SOURCE_ROOM_LEVEL_DB,
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
