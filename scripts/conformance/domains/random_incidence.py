#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Random-incidence and diffuse-field sensitivity of a sound level meter.

IEC 61183:1994 prints no worked calibration, but Annex A prints the numbers
its free-field method is built from: the adjustment factors of Formulas (A.1)
and (A.2) for 10° steps in two planes (Table A.1), the size of the largest
element that division leaves (A.1.7), and the directions of a division of the
sphere into 38 elements of equal area (note to A.1.8). Annex B prints the
directivity factor and the diffuse-to-pressure difference of the reference
microphone the diffuse-field routes of Formulas (10) and (11) default to
(Table B.1). The rows below reproduce each of those from the library, and add
the invariant every weighting of the sphere has to keep: its factors sum to
one, so an omnidirectional instrument has a directivity factor of one.

Oracle: BS EN 61183:1995, the English text of EN 61183:1994, which is
IEC 1183:1994 unchanged: A.1.6 on printed folio 8 (PDF page 12), A.1.7 on
folio 9 (PDF page 13), Table A.1 and the note to A.1.8 on folio 10 (PDF page
14), Table B.1 on folio 14 (PDF page 18).

One printed defect sits in this oracle and is recorded in ``docs/ERRATA.md``:
the note to A.1.8 lists 77,9° and 282,1° where the symmetry of its own list,
and the equal-area construction, give 77,8° and 282,2°. The row on that list
checks the other 18 and names the two.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import metrology

from ..registry import Outcome, count, numeric, register

_IEC61183 = "Random-incidence and diffuse-field sensitivity (IEC 61183)"

_STEP = ref.IEC61183_TABLE_A1_STEP_DEG


def _printed_factor_by_angle() -> dict[int, float]:
    return {angle: k for angles, k in ref.IEC61183_TABLE_A1 for angle in angles}


@register(
    _IEC61183,
    "IEC 61183:1994 Formulas (A.1), (A.2), Table A.1",
    "Adjustment factors K(phi) of all 36 angles, 10° steps in two planes",
)
def _chk_table_a1() -> Outcome:
    """Every angle of a plane rounds to the five decimals its row prints.

    Table A.1 prints ten values, one for each group of angles that lie on the
    same ring; the row checks the factor of each of the 36 angles against the
    value of its group, from 0,00095 at the poles to 0,02179 at 90°.
    """
    factors = metrology.adjustment_factors(_STEP)
    printed = _printed_factor_by_angle()
    matching = sum(
        1
        for angle, value in printed.items()
        if math.isclose(round(float(factors[round(angle / _STEP)]), 5), value)
    )
    return count(matching, len(printed), subject="angles of Table A.1")


@register(
    _IEC61183,
    "IEC 61183:1994 A.6 NOTE 2, Table A.1",
    "Four planes at 45° take half the factors of Table A.1",
)
def _chk_four_planes() -> Outcome:
    """Twice each four-plane factor rounds to the value Table A.1 prints."""
    factors = metrology.adjustment_factors(_STEP, planes=4)
    printed = _printed_factor_by_angle()
    matching = sum(
        1
        for angle, value in printed.items()
        if math.isclose(round(2.0 * float(factors[round(angle / _STEP)]), 5), value)
    )
    return count(matching, len(printed), subject="halved factors of Table A.1")


@register(
    _IEC61183,
    "IEC 61183:1994 A.1.7",
    "Largest of the 70 elements of 10° steps in two planes, about 2,2 % of the sphere",
)
def _chk_largest_element() -> Outcome:
    """The element at 90°, K(90°) = 2,179 %, and below the 3 % of A.1.6."""
    largest = 100.0 * metrology.largest_element_fraction(_STEP)
    return numeric(ref.IEC61183_A17_LARGEST_PERCENT, largest, 0.05, unit="%", places=3)


@register(
    _IEC61183,
    "IEC 61183:1994 Formula (A.3), Table A.1",
    "The 72 factors of two planes sum to one with the poles in both sums",
)
def _chk_factor_sum() -> Outcome:
    """Each plane's pole factor covers half its cap, so both enter.

    Counted once, as a reading of the paragraph under (A.3) would have it,
    the sum is 0,998097 and every 10 lg gamma comes out 0,008 dB high.
    """
    total = 2.0 * float(np.sum(metrology.adjustment_factors(_STEP)))
    return numeric(1.0, total, 1e-12, places=6)


@register(
    _IEC61183,
    "IEC 61183:1994 Formulas (A.3), (1)",
    "An omnidirectional instrument has 10 lg gamma = 0 dB, so G_RI = G_F",
)
def _chk_omnidirectional() -> Outcome:
    """72 equal readings at 10° steps in two planes."""
    result = metrology.directivity_factor(np.full((2, 36), 94.0))
    return numeric(0.0, result.directivity_index_db, 1e-9, unit="dB", places=6)


@register(
    _IEC61183,
    "IEC 61183:1994 note to A.1.8",
    "Directions of the 38 equal-area elements, to the 0,1° printed",
)
def _chk_equal_area_angles() -> Outcome:
    """The 20 printed angles of the horizontal plane, less the two errata.

    Each direction halves its element's area in polar angle. The note prints
    77,9° and 282,1°, which break the list's symmetry about 90°; the
    construction gives 77,85° and 282,15° (``docs/ERRATA.md``).
    """
    horizontal, _ = metrology.equal_area_incidence_angles()
    printed = ref.IEC61183_EQUAL_AREA_HORIZONTAL_DEG
    errata = ref.IEC61183_EQUAL_AREA_ERRATA_DEG
    checked = [
        (float(computed), value)
        for computed, value in zip(horizontal, printed, strict=True)
        if value not in errata
    ]
    matching = sum(
        1 for computed, value in checked if math.isclose(round(computed, 1), value)
    )
    return count(
        matching,
        len(checked),
        subject="printed angles other than 77,9° and 282,1°",
    )


@register(
    _IEC61183,
    "IEC 61183:1994 note to A.1.8, Formula (A.5)",
    "Each of the 38 equal-area elements is 2,6 % of the sphere",
)
def _chk_equal_area_element() -> Outcome:
    """The weight of every reading of Formula (A.5), 1/38."""
    result = metrology.equal_area_directivity_factor(
        np.full(20, 90.0), np.full(18, 90.0)
    )
    return numeric(
        ref.IEC61183_EQUAL_AREA_ELEMENT_PERCENT,
        100.0 * result.largest_element,
        0.05,
        unit="%",
        places=3,
    )


@register(
    _IEC61183,
    "IEC 61183:1994 Formulas (10), (11), Table B.1",
    "Reference corrections of an LS2aP/LS2F microphone at the 30 preferred frequencies",
)
def _chk_table_b1_defaults() -> Outcome:
    """What the diffuse-field routes take from Table B.1 when not told.

    Formula (10) subtracts 10 lg gamma_ref and Formula (11) adds Delta_DP; with
    every other term zero, the diffuse-field level is the table's own cell.
    The row printed "25 to 800" is checked at each preferred frequency it
    covers.
    """
    frequencies = np.array(sorted(metrology.IEC61183_TABLE_B1))
    zero = np.zeros(frequencies.size)
    free_field = metrology.diffuse_field_sensitivity(
        frequencies, zero, zero, reference_free_field_level_db=0.0
    )
    pressure = metrology.diffuse_field_sensitivity(
        frequencies, zero, zero, reference_pressure_level_db=0.0
    )
    matching = 0
    for index, frequency in enumerate(frequencies):
        row = next(
            row
            for row in ref.IEC61183_TABLE_B1_PRINTED
            if row[1] <= frequency <= row[2]
        )
        matching += math.isclose(
            -free_field.diffuse_field_level_db[index], row[3], abs_tol=1e-12
        )
        matching += math.isclose(
            pressure.diffuse_field_level_db[index], row[4], abs_tol=1e-12
        )
    return count(matching, 2 * frequencies.size, subject="cells of Table B.1")
