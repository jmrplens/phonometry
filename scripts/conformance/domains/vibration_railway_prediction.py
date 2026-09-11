#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Railway vibration predicted from third-octave spectra (E DIN 45672-3:2023-02).

The draft prediction method for railways works one example through its
chain in Annex C: Table C.1 prints the emission spectrum of a tram at a
building's foundation, the transmission for the difference in distance, the
transfer to a concrete floor, and the sum of Formula (1) band by band; the
sum level over the bands, and from it the clock maximum r.m.s. of Formula
(9), the KB_Fmax of Formula (10) and the peak velocity of Formula (12). Its
Table 2 prints the KB weighting of DIN 45669-1 as a table, and its Annex A
six tables of level differences into and inside a building, read off their
pages cell by cell.

The rows compare with the printed values at the decimals they are printed
with. Three rows of Table C.1 are a tenth off the sum of their printed
terms, which is what rounding the terms after summing does, and the row
carries that tenth. The example feeds Formula (9) the unweighted sum of all
19 bands, so the chain is held to that; and its assessment severities of
Formula (11), printed as 0,11 and 0,05, do not follow from any printed
input, so those rows compare with what the formula gives for the printed
inputs and the entry is in ``docs/ERRATA.md``.

Oracle: E DIN 45672-3:2023-02, Table 2 on printed page 22, Tables A.1 to
A.6 on printed pages 24 to 29, Table C.1 and the results on printed page 34,
and the assessment on printed page 35.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

import numpy as np

import phonometry as ph

from ..registry import Outcome, numeric, register

if TYPE_CHECKING:
    from collections.abc import Callable

_PREDICTION = (
    "Railway vibration predicted from third-octave spectra (E DIN 45672-3:2023-02)"
)
_EDITION = "E DIN 45672-3:2023-02"

#: Half a unit in the last printed place.
_TENTH_DB = 0.05
_TWO_DECIMALS = 0.005
_THREE_DECIMALS = 0.0005

#: Table C.1 (printed page 34): the three terms and the printed sum, for the
#: bands a row is built on.
_TABLE_C1 = {
    4.0: (26.0, 0.9, 1.9, 28.9),
    20.0: (57.0, 1.3, 17.3, 75.6),
    63.0: (60.0, 2.2, -0.8, 61.4),
    250.0: (28.0, 2.4, -9.6, 20.8),
}
_PRINTED_LEVELS = (
    28.9, 30.2, 41.0, 58.6, 62.1, 65.1, 68.8, 75.6, 69.4, 65.0, 55.7, 55.5, 61.4,
    58.3, 48.1, 43.1, 41.6, 27.7, 20.8,
)  # fmt: skip

#: Table 2 (printed page 22): the cells a row is built on.
_TABLE_2 = {4.0: -4.7, 8.0: -1.7, 20.0: -0.3, 63.0: 0.0}

#: Annex A: a cell of each table, as (label, expected, getter).
_ANNEX_A: dict[str, tuple[float, Callable[[], float]]] = {
    "Table A.1, concrete floor at 8 Hz, the band at 8 Hz": (
        15.0,
        lambda: ph.vibration.ground_to_floor_transfer_db(
            "concrete", floor_natural_frequency_hz=8.0
        )[3],
    ),
    "Table A.1, concrete floor at 20 Hz, the band at 20 Hz": (
        13.12,
        lambda: ph.vibration.ground_to_floor_transfer_db(
            "concrete", floor_natural_frequency_hz=20.0
        )[7],
    ),
    "Table A.2, timber floor at 8 Hz, the band at 4 Hz": (
        5.14,
        lambda: ph.vibration.ground_to_floor_transfer_db(
            "timber", floor_natural_frequency_hz=8.0
        )[0],
    ),
    "Table A.3, ground to a basement, the mean at 31,5 Hz": (
        -9.3,
        lambda: ph.vibration.ground_to_foundation_transfer_db("basement")[9],
    ),
    "Table A.4, ground to a ground floor, the mean at 12,5 Hz": (
        -1.9,
        lambda: ph.vibration.ground_to_foundation_transfer_db("ground_floor")[5],
    ),
    "Table A.5, foundation to a concrete floor, the mean at its natural frequency": (
        17.26,
        lambda: ph.vibration.foundation_to_floor_transfer_db(
            [20.0], floor="concrete", floor_natural_frequency_hz=20.0
        )[0],
    ),
    "Table A.6, foundation to a timber floor, the mean at its natural frequency": (
        21.93,
        lambda: ph.vibration.foundation_to_floor_transfer_db(
            [20.0], floor="timber", floor_natural_frequency_hz=20.0
        )[0],
    ),
}


def _chk_table_c1(band_hz: float) -> Outcome:
    emission, ground, floor, printed = _TABLE_C1[band_hz]
    computed = float(
        ph.vibration.predict_floor_spectrum(
            [emission], ground_db=ground, floor_db=floor
        )[0]
    )
    # Rounding the terms after summing leaves the print a tenth off in three rows.
    return numeric(printed, computed, 0.1 + 1e-9, unit="dB", places=2)


@register(
    _PREDICTION, f"{_EDITION} Annex C, Table C.1", "Sum level of the 19 printed bands"
)
def _chk_sum_level() -> Outcome:
    return numeric(
        78.1,
        ph.vibration.band_sum_level(_PRINTED_LEVELS),
        _TENTH_DB,
        unit="dB",
        places=2,
    )


@register(
    _PREDICTION,
    f"{_EDITION} Annex C, C.3",
    "KB_FTm,Zug from 78,1 dB by Formula (9), c_T1 = 1",
)
def _chk_kb_ftm() -> Outcome:
    return numeric(0.4, ph.vibration.takt_maximum_kb([78.1]), 0.05, places=4)


@register(
    _PREDICTION, f"{_EDITION} Annex C, C.3", "KB_Fmax,Zug by Formula (10), 1,5 times it"
)
def _chk_kb_fmax() -> Outcome:
    computed = ph.vibration.TRAIN_KB_FMAX_FACTOR * ph.vibration.takt_maximum_kb([78.1])
    return numeric(0.6, computed, 0.05, places=4)


@register(
    _PREDICTION, f"{_EDITION} Annex C, C.3", "v_max by Formula (12), 3 times that, mm/s"
)
def _chk_peak_velocity() -> Outcome:
    kb_fmax = ph.vibration.TRAIN_KB_FMAX_FACTOR * ph.vibration.takt_maximum_kb([78.1])
    return numeric(
        1.81,
        ph.vibration.peak_velocity_from_kb_mm_s(kb_fmax),
        _TWO_DECIMALS,
        unit="mm/s",
        places=3,
    )


@register(
    _PREDICTION,
    f"{_EDITION} Annex C, C.3",
    "KB_FTr of the day by Formula (11), 200 trams at 0,7 (the print's 0,11 puts "
    "alpha under the root once, not squared)",
)
def _chk_kb_ftr_day() -> Outcome:
    computed = ph.vibration.train_assessment_severity([0.4], [200], alpha=0.7)
    return numeric(0.090, computed, _THREE_DECIMALS, places=4)


@register(
    _PREDICTION,
    f"{_EDITION} Annex C, C.3",
    "KB_FTr of the night by Formula (11), 20 trams at 0,7 (the print's 0,05 puts "
    "alpha under the root once, not squared)",
)
def _chk_kb_ftr_night() -> Outcome:
    computed = ph.vibration.train_assessment_severity(
        [0.4], [20], alpha=0.7, time_of_day="night"
    )
    return numeric(0.040, computed, _THREE_DECIMALS, places=4)


def _chk_table_2(band_hz: float) -> Outcome:
    computed = float(ph.vibration.kb_weighted_levels_db([0.0], [band_hz])[0])
    return numeric(_TABLE_2[band_hz], computed, 1e-9, unit="dB", places=1)


def _chk_annex_a(label: str) -> Outcome:
    expected, getter = _ANNEX_A[label]
    return numeric(expected, float(np.asarray(getter())), 1e-9, unit="dB", places=2)


def _register_rows() -> None:
    for band in _TABLE_C1:
        register(
            _PREDICTION,
            f"{_EDITION} Annex C, Table C.1",
            f"L_v at {band:g} Hz by Formula (1)",
        )(functools.partial(_chk_table_c1, band))
    for band in _TABLE_2:
        register(_PREDICTION, f"{_EDITION} Table 2", f"KB weighting at {band:g} Hz")(
            functools.partial(_chk_table_2, band)
        )
    for label in _ANNEX_A:
        register(_PREDICTION, f"{_EDITION} Annex A", label)(
            functools.partial(_chk_annex_a, label)
        )


_register_rows()
