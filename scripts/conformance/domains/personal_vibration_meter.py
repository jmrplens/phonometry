#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Personal vibration exposure meters (ISO 8041-2).

ISO 8041-2:2021 specifies the personal vibration exposure meter (PVEM), the
instrument left unattended to log a worker's exposure through a full working
day (5.1.1, folio 4), and it grades that instrument with the tables of
ISO 8041-1 wherever it can. Its 5.9 (folio 11) repeats the
saw-tooth signal burst: Table 6 (folio 12) defines the same test signal, and
Tables 7, 8 and 9 (folios 12, 13 and 14) print 228 indications a conforming
PVEM has to show, each with its tolerance beside it.

The rows here are Part 2's own, and they answer two separate questions about
those tables.

1. *Does the library reproduce the Part 2 page?* The oracle is the Part 2
   transcription in ``reference_data``, typed off the Part 2 pages. Each of
   the three tables gets one row that counts how many of its printed cells
   the library chain lands inside the tolerance Part 2 prints beside them.
   Cited ``Part 2 / Part 1``, because the same cell is printed in both.
2. *Is it the same table as Part 1's?* One implementation serves both parts
   only if it is, so each table also gets a row that holds the Part 2
   transcription cell by cell against
   :data:`phonometry.vibration.SIGNAL_BURST_RESPONSE` and
   :data:`phonometry.vibration.BURST_TOLERANCE_PERCENT`, indication and
   tolerance alike, and Table 6 gets one for the test signal. Cited
   ``Part 2 vs Part 1``, because the row compares the two documents.

Two things Part 2 prints differently have a table of their own in the library
and a row here: Table 2 (folio 8), which keeps the first two rows of the
Part 1 table and drops the running r.m.s. row because its 5.13 (folio 15)
declares it not applicable, and the maximum expanded uncertainties of
clauses 12 and 13 (folios 26 to 32 and 41).

Oracle: ISO 8041-2:2021, printed folios 8, 12, 13, 14, 23, 26 to 32, 37 and
41 (PDF pages 16, 20, 21, 22, 31, 34 to 40, 45 and 49).
"""

from __future__ import annotations

import reference_data as ref

import phonometry as ph

from ..registry import Outcome, count, numeric, record, register
from .signal_burst import _indications

_PVEM = "Personal vibration exposure meters (ISO 8041-2)"

_TOLERANCE = 5e-4

#: Fields Table 6 prints per application.
_TABLE6_FIELDS = 6

#: Each printed table of Part 2: its number, the application it grades, its
#: printed columns and its transcribed lines.
_TABLES: tuple[
    tuple[
        int,
        str,
        tuple[str, ...],
        dict[tuple[str, int | None], tuple[tuple[float, float], ...]],
    ],
    ...,
] = (
    (7, "hand-arm", ref.ISO8041_2_TABLE7_COLUMNS, ref.ISO8041_2_TABLE7),
    (8, "whole-body", ref.ISO8041_2_TABLE8_COLUMNS, ref.ISO8041_2_TABLE8),
    (
        9,
        "low-frequency-whole-body",
        ref.ISO8041_2_TABLE9_COLUMNS,
        ref.ISO8041_2_TABLE9,
    ),
)

#: How many cells each table prints, counted on the page, so that a line lost
#: from the transcription fails its row instead of shrinking the denominator.
_PRINTED_CELLS = {7: 12, 8: 192, 9: 24}


def _row_name(row: str) -> str:
    """The library's name for a printed row, the band-limiting one included."""
    return ph.vibration.BAND_LIMITING if row == "band-limiting" else row


def _cell_count(
    number: int,
    table: dict[tuple[str, int | None], tuple[tuple[float, float], ...]],
) -> int:
    """How many cells the transcription holds, checked against the page."""
    total = sum(len(cells) for cells in table.values())
    if total != _PRINTED_CELLS[number]:
        msg = (
            f"Table {number}: the Part 2 transcription holds {total} cells "
            f"where the page prints {_PRINTED_CELLS[number]}."
        )
        raise AssertionError(msg)
    return total


def _register_reproduction() -> None:
    """One row per Part 2 table: the library chain against the Part 2 page."""
    for number, application, columns, table in _TABLES:

        def _check(
            number: int = number,
            application: str = application,
            columns: tuple[str, ...] = columns,
            table: dict[
                tuple[str, int | None], tuple[tuple[float, float], ...]
            ] = table,
        ) -> Outcome:
            total = _cell_count(number, table)
            inside = 0
            for (row, cycles), cells in table.items():
                computed = _indications(application, _row_name(row), cycles)
                for column, (printed, tolerance) in zip(columns, cells, strict=True):
                    deviation = abs(computed[column] / printed - 1.0) * 100.0
                    if deviation <= tolerance:
                        inside += 1
            return count(
                inside,
                total,
                subject="printed cells",
                expected_label=f"{total} cells inside the printed tolerance",
            )

        register(
            _PVEM,
            f"ISO 8041-2:2021 Table {number} / -1:2017 Table {number}",
            f"Signal-burst response, {application}: every printed cell",
        )(_check)


def _register_identity() -> None:
    """One row per Part 2 table: the same cells as the Part 1 table."""
    for number, application, columns, table in _TABLES:

        def _check(
            number: int = number,
            application: str = application,
            columns: tuple[str, ...] = columns,
            table: dict[
                tuple[str, int | None], tuple[tuple[float, float], ...]
            ] = table,
        ) -> Outcome:
            total = _cell_count(number, table)
            same = 0
            for (row, cycles), cells in table.items():
                part_1 = ph.vibration.SIGNAL_BURST_RESPONSE[
                    application, _row_name(row), cycles
                ]
                for column, (printed, tolerance) in zip(columns, cells, strict=True):
                    # Exact comparison of two transcriptions of the same
                    # printed decimal, which parse to the same float: a Part 2
                    # cell one digit off would be a different number, and a
                    # tolerance would hide it.
                    tolerance_1 = ph.vibration.BURST_TOLERANCE_PERCENT[column]
                    if part_1[column] == printed and tolerance_1 == tolerance:
                        same += 1
            return count(
                same,
                total,
                subject="cells",
                expected_label=(
                    f"{total} cells, indication and tolerance, as ISO 8041-1 "
                    "prints them"
                ),
            )

        register(
            _PVEM,
            f"ISO 8041-2:2021 Table {number} vs -1:2017 Table {number}",
            f"Printed cells identical to Part 1, {application}",
        )(_check)


_register_reproduction()
_register_identity()


@register(
    _PVEM,
    "ISO 8041-2:2021 Table 6 vs -1:2017 Table 6",
    "Saw-tooth test signal identical to Part 1, 18 fields",
)
def _chk_table_6() -> Outcome:
    """The six fields Table 6 prints per application, against Part 1's.

    Weightings, angular frequency, start time, burst lengths, repeat time and
    duration: the burst tables can only be the same if the signal is.
    """
    same = 0
    total = 0
    # Walk the library's applications, not the transcription's: an application
    # the transcription lost then counts as six fields that differ instead of
    # leaving the tally to pass on the ones that remain.
    for application, test in ph.vibration.SAWTOOTH_BURST_TESTS.items():
        printed = ref.ISO8041_2_TABLE6.get(application)
        if printed is None:
            total += _TABLE6_FIELDS
            continue
        library = (
            test.weightings,
            test.angular_frequency_rad_s,
            test.start_time_s,
            test.cycle_counts,
            test.repeat_time_s,
            test.duration_s,
        )
        for part_2, part_1 in zip(printed, library, strict=True):
            total += 1
            if part_2 == part_1:
                same += 1
    # And an application the page prints that the library lacks counts too.
    unmatched = set(ref.ISO8041_2_TABLE6) - set(ph.vibration.SAWTOOTH_BURST_TESTS)
    total += _TABLE6_FIELDS * len(unmatched)
    return count(same, total, subject="fields")


@register(
    _PVEM,
    "ISO 8041-2:2021 Table 2",
    "Tolerances of indication of a PVEM, 2 rows, %",
)
def _chk_table_2() -> Outcome:
    """The two rows Part 2 prints, and not the running r.m.s. row.

    The first row carries one tolerance per application. The names on both
    sides have to agree, so a running r.m.s. key in the library table would
    stop the report rather than pass unnoticed: 5.13 (folio 15) reads "Not
    applicable for PVEM".
    """
    printed = {
        "indication": ref.ISO8041_2_TABLE2_INDICATION_PERCENT,
        "low-frequency indication": (
            ref.ISO8041_2_TABLE2_LOW_FREQUENCY_INDICATION_PERCENT
        ),
        "weighting consistency": ref.ISO8041_2_TABLE2_WEIGHTING_CONSISTENCY_PERCENT,
    }
    return record(
        printed,
        dict(ph.vibration.PVEM_INDICATION_TOLERANCES_PERCENT),
        unit="%",
    )


@register(
    _PVEM,
    "ISO 8041-2:2021 12.11",
    "Maximum expanded uncertainties of the frequency-response tests, %",
)
def _chk_frequency_response_uncertainties() -> Outcome:
    """12.11.2 (folio 29) 4,5 %, 12.11.3 (folio 30) 3 %, 12.11.4 (folio 31) 5 %."""
    clauses = ("12.11.2", "12.11.3", "12.11.4")
    printed = {
        clause: ref.ISO8041_2_MAX_EXPANDED_UNCERTAINTY_PERCENT[clause]
        for clause in clauses
    }
    computed = {
        clause: ph.vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT[clause]
        for clause in clauses
    }
    return record(printed, computed, unit="%")


@register(
    _PVEM,
    "ISO 8041-2:2021 Clauses 12 and 13",
    "Maximum expanded uncertainties of measurement, 11 figures over 10 clauses, %",
)
def _chk_all_uncertainties() -> Outcome:
    """Every clause of Part 2 that prints a figure, and no other.

    12.7 (folio 26), 12.10.1 (folio 27), 12.10.2 on both ranges (folio 28),
    the three frequency-response clauses (folios 29 to 31), 12.13 (folio 31),
    12.14 and 12.18 (folio 32) and 13.9 (folio 41).
    """
    return record(
        dict(ref.ISO8041_2_MAX_EXPANDED_UNCERTAINTY_PERCENT),
        dict(ph.vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT),
        unit="%",
    )


@register(
    _PVEM,
    "ISO 8041-2:2021 12.1 and 13.1",
    "Coverage factor of the expanded uncertainty",
)
def _chk_coverage_factor() -> Outcome:
    """12.1 prints "no less than 2" (folio 23) and 13.1 ``k = 2`` (folio 37).

    The factor is a stated integer, not a measured value, so it is compared
    with no tolerance at all.
    """
    return numeric(
        ref.ISO8041_2_COVERAGE_FACTOR,
        ph.vibration.ISO8041_COVERAGE_FACTOR,
        0.0,
        places=0,
        unit="",
    )
