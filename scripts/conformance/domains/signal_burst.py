#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Saw-tooth signal-burst response of a human-vibration meter (ISO 8041-1 5.9).

The largest printed oracle in the standard, and one it declares arithmetic:
"NOTE 1 The response to the saw-tooth signal burst is determined by digital
simulation of the filter characteristics" (folio 16). Table 6 defines the test
signal and Tables 7, 8 and 9 print the 228 indications a conforming meter must
show for a 1 m/s2 amplitude, with the tolerance beside each column.

These rows run the library chain end to end: the saw-tooth generator, the
weighting (or the band-limiting response) applied from rest, and then the
r.m.s. value, the vibration dose value, the two maximum transient vibration
values and the motion sickness dose value. Three aggregate rows count how many
of the printed cells land inside their printed tolerance; the sampled rows
report single cells against the figure on the page, at a tolerance far tighter
than the printed one, because that is what the reproduction actually achieves.

Two of the sampled cells are there because they decide a convention the tables
do not print: the continuous row of Table 7 lands on 0,565 only when it is
filled from ``t = 0``, and the linear MTVV of the ``Wk`` continuous row lands
on 0,364 only when the filtering starts from rest.

Oracle: ISO 8041-1:2017, printed folios 17, 18 and 19 (PDF pages 25, 26 and
27): Table 6 (saw-tooth signal burst test signal characteristics) and Tables 7,
8 and 9 (the responses). ISO 8041-2:2021 5.9 (folio 11) prints the same tables.
"""

from __future__ import annotations

import functools

import phonometry as ph

from ..registry import Outcome, count, numeric, register

_BURST = "Saw-tooth signal burst (ISO 8041-1 5.9)"

#: The unit of each printed column, for the report.
_UNITS = {
    "rms": "m/s2",
    "vdv": "m/s^1.75",
    "mtvv_linear": "m/s2",
    "mtvv_exponential": "m/s2",
    "msdv": "m/s^1.5",
}

#: How each printed column is headed in the table.
_COLUMNS = {
    "rms": "r.m.s. value",
    "vdv": "VDV",
    "mtvv_linear": "MTVV linear",
    "mtvv_exponential": "MTVV exponential",
    "msdv": "MSDV",
}

#: How each table is titled in the report, and how many cells it prints.
_TABLES = {
    "hand-arm": ("ISO 8041-1:2017 Table 7", 12),
    "whole-body": ("ISO 8041-1:2017 Table 8", 192),
    "low-frequency-whole-body": ("ISO 8041-1:2017 Table 9", 24),
}


@functools.cache
def _indications(application: str, row: str, cycles: int | None) -> dict[str, float]:
    """The library's indications for one printed line, computed once."""
    return ph.vibration.signal_burst_indications(application, row, cycles)


def _rows_of(application: str) -> list[tuple[str, int | None]]:
    """The printed lines of one application's table, in printed order."""
    test = ph.vibration.SAWTOOTH_BURST_TESTS[application]
    rows = [ph.vibration.BAND_LIMITING, *test.weightings]
    return [(row, cycles) for row in rows for cycles in (*test.cycle_counts, None)]


def _cells_within_tolerance(application: str) -> tuple[int, int]:
    """How many printed cells of one table the library lands inside."""
    inside = 0
    total = 0
    for row, cycles in _rows_of(application):
        printed = ph.vibration.SIGNAL_BURST_RESPONSE[application, row, cycles]
        computed = _indications(application, row, cycles)
        for quantity, expected in printed.items():
            total += 1
            tolerance = ph.vibration.BURST_TOLERANCE_PERCENT[quantity]
            if abs(computed[quantity] / expected - 1.0) * 100.0 <= tolerance:
                inside += 1
    return inside, total


def _register_tables() -> None:
    """One aggregate row per printed table."""
    for application, (standard, cells) in _TABLES.items():

        def _check(application: str = application, cells: int = cells) -> Outcome:
            inside, total = _cells_within_tolerance(application)
            return count(
                inside,
                total,
                subject="printed cells",
                expected_label=f"{cells} cells inside the printed tolerance",
            )

        register(
            _BURST,
            standard,
            f"Signal-burst response, {application}: every printed cell",
        )(_check)


#: The sampled cells: application, row, burst length, column, the figure on the
#: page and the relative tolerance the row is judged at.
_SAMPLED: tuple[tuple[str, str, int | None, str, float, float], ...] = (
    ("hand-arm", "band-limiting", 1, "rms", 0.0448, 5e-3),
    ("hand-arm", "band-limiting", None, "rms", 0.565, 5e-3),
    ("hand-arm", "Wh", 16, "rms", 0.0309, 5e-3),
    ("whole-body", "band-limiting", None, "rms", 0.546, 5e-3),
    ("whole-body", "Wb", 4, "rms", 0.0614, 5e-3),
    ("whole-body", "Wk", 1, "vdv", 0.323, 5e-3),
    ("whole-body", "Wk", 16, "mtvv_exponential", 0.289, 5e-3),
    ("whole-body", "Wk", None, "mtvv_linear", 0.364, 5e-3),
    ("low-frequency-whole-body", "band-limiting", None, "msdv", 21.51, 1e-2),
    ("low-frequency-whole-body", "Wf", 1, "rms", 0.0197, 5e-3),
)


def _register_sampled() -> None:
    """One row per sampled printed cell."""
    for application, row, cycles, quantity, printed, tolerance in _SAMPLED:
        standard = _TABLES[application][0]
        if cycles is None:
            length = "continuous"
        else:
            length = f"{cycles} cycle" if cycles == 1 else f"{cycles} cycles"
        column = _COLUMNS[quantity]

        def _check(
            application: str = application,
            row: str = row,
            cycles: int | None = cycles,
            quantity: str = quantity,
            printed: float = printed,
            tolerance: float = tolerance,
        ) -> Outcome:
            computed = _indications(application, row, cycles)[quantity]
            return numeric(
                printed,
                computed,
                tolerance,
                unit=_UNITS[quantity],
                places=5,
                rel=True,
            )

        register(
            _BURST,
            standard,
            f"{row}, {length}, {column}, {_UNITS[quantity]}",
        )(_check)


_register_tables()
_register_sampled()


@register(
    _BURST,
    "ISO 8041-1:2017 Table 6",
    "Saw-tooth frequency of the whole-body burst, Hz",
)
def _chk_whole_body_frequency() -> Outcome:
    """100 rad/s, printed beside it as 15,915 Hz."""
    return numeric(
        15.915,
        ph.vibration.SAWTOOTH_BURST_TESTS["whole-body"].frequency_hz,
        1e-4,
        unit="Hz",
        places=4,
        rel=True,
    )


@register(
    _BURST,
    "ISO 8041-1:2017 Table 6",
    "Saw-tooth frequency of the hand-arm burst, Hz",
)
def _chk_hand_arm_frequency() -> Outcome:
    """500 rad/s, printed beside it as 79,58 Hz."""
    return numeric(
        79.58,
        ph.vibration.SAWTOOTH_BURST_TESTS["hand-arm"].frequency_hz,
        1e-4,
        unit="Hz",
        places=4,
        rel=True,
    )


@register(
    _BURST,
    "ISO 8041-1:2017 Table 6",
    "Saw-tooth frequency of the low-frequency whole-body burst, Hz",
)
def _chk_low_frequency_frequency() -> Outcome:
    """2,5 rad/s, printed beside it as 0,3979 Hz."""
    return numeric(
        0.3979,
        ph.vibration.SAWTOOTH_BURST_TESTS["low-frequency-whole-body"].frequency_hz,
        1e-4,
        unit="Hz",
        places=4,
        rel=True,
    )


@register(
    _BURST,
    "ISO 8041-1:2017 12.13",
    "Largest fall time of the whole-body saw-tooth generator, s",
)
def _chk_fall_time() -> Outcome:
    """The 1/(5 f2) of 12.13, which is 2 ms for the 100 Hz upper corner."""
    return numeric(
        2e-3,
        ph.vibration.SAWTOOTH_BURST_TESTS["whole-body"].max_fall_time_s,
        1e-6,
        unit="s",
        places=6,
    )
