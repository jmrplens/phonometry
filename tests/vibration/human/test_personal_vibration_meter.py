#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the personal vibration exposure meter of ISO 8041-2:2021.

Part 2 grades a PVEM with the tables of Part 1 wherever it can, and the claim
this file pins is that "wherever it can" is true to the digit. The oracle is
the Part 2 transcription in ``reference_data``, typed off the Part 2 pages
rather than copied from the Part 1 tables the library holds: Table 6 (folio
12), the 228 indications and 228 tolerances of Tables 7 to 9 (folios 12 to
14), Table 2 (folio 8) and the maximum expanded uncertainties of clauses 12
and 13 (folios 26 to 32 and 41).

Two things are Part 2's own and are published as tables of their own: its
Table 2, which drops the running r.m.s. row, and its list of uncertainty
clauses, which is shorter than Part 1's.
"""

from __future__ import annotations

import pytest
from reference_data import (
    ISO8041_2_COVERAGE_FACTOR,
    ISO8041_2_MAX_EXPANDED_UNCERTAINTY_PERCENT,
    ISO8041_2_TABLE2_INDICATION_PERCENT,
    ISO8041_2_TABLE2_LOW_FREQUENCY_INDICATION_PERCENT,
    ISO8041_2_TABLE2_ROWS,
    ISO8041_2_TABLE2_WEIGHTING_CONSISTENCY_PERCENT,
    ISO8041_2_TABLE6,
    ISO8041_2_TABLE7,
    ISO8041_2_TABLE7_COLUMNS,
    ISO8041_2_TABLE8,
    ISO8041_2_TABLE8_COLUMNS,
    ISO8041_2_TABLE9,
    ISO8041_2_TABLE9_COLUMNS,
)

from phonometry import vibration

#: The three printed tables of Part 2, each with the application whose Part 1
#: table it has to match.
PART_2_TABLES = (
    ("hand-arm", ISO8041_2_TABLE7_COLUMNS, ISO8041_2_TABLE7),
    ("whole-body", ISO8041_2_TABLE8_COLUMNS, ISO8041_2_TABLE8),
    ("low-frequency-whole-body", ISO8041_2_TABLE9_COLUMNS, ISO8041_2_TABLE9),
)


def _row_name(row: str) -> str:
    """The library's name for a printed row, ``Band limiting`` included."""
    return vibration.BAND_LIMITING if row == "band-limiting" else row


# ---------------------------------------------------------------------------
# Table 6 and Tables 7 to 9: the same signal and the same 228 cells.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("application", "printed"), ISO8041_2_TABLE6.items())
def test_the_part_2_test_signal_is_the_part_1_test_signal(
    application: str,
    printed: tuple[tuple[str, ...], float, float, tuple[int, ...], float, float],
) -> None:
    """Table 6 of Part 2 (folio 12), field by field against Part 1's."""
    weightings, omega, start, cycles, repeat, duration = printed
    test = vibration.SAWTOOTH_BURST_TESTS[application]
    assert test.weightings == weightings
    assert test.angular_frequency_rad_s == pytest.approx(omega)
    assert test.start_time_s == pytest.approx(start)
    assert test.cycle_counts == cycles
    assert test.repeat_time_s == pytest.approx(repeat)
    assert test.duration_s == pytest.approx(duration)


def test_the_part_2_tables_print_72_lines_and_228_cells() -> None:
    """The Part 2 transcription is the whole of Tables 7 to 9, not a sample."""
    lines = sum(len(table) for _, _, table in PART_2_TABLES)
    cells = sum(len(cells) for _, _, table in PART_2_TABLES for cells in table.values())
    assert (lines, cells) == (72, 228)


@pytest.mark.parametrize(("application", "columns", "table"), PART_2_TABLES)
def test_every_part_2_indication_is_the_part_1_indication(
    application: str,
    columns: tuple[str, ...],
    table: dict[tuple[str, int | None], tuple[tuple[float, float], ...]],
) -> None:
    """Cell by cell: each Part 2 indication equals the Part 1 cell exactly.

    Exact equality, because both sides are the decimal the page prints: a
    Part 2 cell that differed in its last printed digit would be a different
    number, and this is where it would show.
    """
    for (row, cycles), cells in table.items():
        library = vibration.SIGNAL_BURST_RESPONSE[application, _row_name(row), cycles]
        assert tuple(library) == columns
        printed = tuple(value for value, _ in cells)
        assert tuple(library.values()) == printed, (row, cycles)


@pytest.mark.parametrize(("application", "columns", "table"), PART_2_TABLES)
def test_every_part_2_tolerance_is_the_part_1_tolerance(
    application: str,
    columns: tuple[str, ...],
    table: dict[tuple[str, int | None], tuple[tuple[float, float], ...]],
) -> None:
    """And the tolerance printed beside each cell, 10 % or 12 % for the VDV."""
    for (row, cycles), cells in table.items():
        for column, (_, tolerance) in zip(columns, cells, strict=True):
            assert vibration.BURST_TOLERANCE_PERCENT[column] == pytest.approx(
                tolerance
            ), (application, row, cycles, column)


def test_the_library_passes_a_part_2_row_against_the_part_2_page() -> None:
    """The reproduction, judged against the Part 2 cells of one whole row.

    Every cell of the Wk row of Table 8 (folio 13), four columns by six burst
    lengths, from the library chain and graded against the tolerances the
    Part 2 page prints beside them.
    """
    for cycles in (1, 2, 4, 8, 16, None):
        got = vibration.signal_burst_indications("whole-body", "Wk", cycles, fs=5_000.0)
        cells = ISO8041_2_TABLE8["Wk", cycles]
        for column, (printed, tolerance) in zip(
            ISO8041_2_TABLE8_COLUMNS, cells, strict=True
        ):
            deviation = abs(got[column] / printed - 1.0) * 100.0
            assert deviation <= tolerance, (cycles, column, deviation)


# ---------------------------------------------------------------------------
# Table 2 of Part 2: two rows, no running r.m.s.
# ---------------------------------------------------------------------------
def test_the_pvem_table_2_is_the_part_2_page() -> None:
    """4 %, 5 % for low-frequency whole-body vibration, and 3 %."""
    assert vibration.PVEM_INDICATION_TOLERANCES_PERCENT == pytest.approx(
        {
            "indication": ISO8041_2_TABLE2_INDICATION_PERCENT,
            "low-frequency indication": (
                ISO8041_2_TABLE2_LOW_FREQUENCY_INDICATION_PERCENT
            ),
            "weighting consistency": ISO8041_2_TABLE2_WEIGHTING_CONSISTENCY_PERCENT,
        }
    )


def test_the_pvem_table_2_has_no_running_rms_row() -> None:
    """Part 2 prints two rows, and 5.13 makes the running r.m.s. inapplicable.

    The first row carries one tolerance per application, which is why two
    rows publish three keys; none of them is the 2 % running r.m.s. row of
    Part 1.
    """
    rows = {
        "indication": 1,
        "low-frequency indication": 1,
        "weighting consistency": 2,
    }
    assert set(vibration.PVEM_INDICATION_TOLERANCES_PERCENT) == set(rows)
    assert max(rows.values()) == ISO8041_2_TABLE2_ROWS
    assert vibration.RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT not in (
        vibration.PVEM_INDICATION_TOLERANCES_PERCENT.values()
    )


def test_the_pvem_table_2_repeats_the_first_two_rows_of_part_1() -> None:
    """The numbers Part 1 publishes for the same two rows."""
    table = vibration.PVEM_INDICATION_TOLERANCES_PERCENT
    assert table["indication"] == pytest.approx(
        vibration.indication_tolerance_percent("Wk")
    )
    assert table["low-frequency indication"] == pytest.approx(
        vibration.indication_tolerance_percent("Wf")
    )
    assert table["weighting consistency"] == pytest.approx(
        vibration.WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT
    )


# ---------------------------------------------------------------------------
# The maximum expanded uncertainties of clauses 12 and 13 of Part 2.
# ---------------------------------------------------------------------------
def test_the_pvem_uncertainties_are_the_part_2_page() -> None:
    """Every clause Part 2 prints a figure for, and no other."""
    assert vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT == pytest.approx(
        ISO8041_2_MAX_EXPANDED_UNCERTAINTY_PERCENT
    )


def test_the_three_frequency_response_clauses() -> None:
    """12.11.2 permits 4,5 %, 12.11.3 3 % and 12.11.4 5 % (folios 29 to 31)."""
    table = vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT
    assert table["12.11.2"] == pytest.approx(4.5)
    assert table["12.11.3"] == pytest.approx(3.0)
    assert table["12.11.4"] == pytest.approx(5.0)


def test_a_clause_both_parts_print_carries_the_same_figure() -> None:
    """Where the clause numbers coincide, so do the figures; 13.9 does not.

    13.9 of Part 2 is periodic verification (5 %), the counterpart of 14.9 of
    Part 1; 13.9 of Part 1 is the indication test of a one-off instrument
    (2 %), a clause Part 2 does not have. The same number names two different
    tests, which is why each part has a table of its own.
    """
    part_1 = vibration.MAX_EXPANDED_UNCERTAINTY_PERCENT
    part_2 = vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT
    shared = [clause for clause in part_2 if clause.startswith("12.")]
    assert len(shared) == 10
    for clause in shared:
        assert part_2[clause] == pytest.approx(part_1[clause]), clause
    assert part_2["13.9"] == pytest.approx(part_1["14.9"])
    assert part_2["13.9"] != pytest.approx(part_1["13.9"])


def test_the_coverage_factor_is_the_part_2_one() -> None:
    """12.1 prints "no less than 2" and 13.1 prints ``k = 2`` in Part 2 too."""
    assert vibration.ISO8041_COVERAGE_FACTOR == pytest.approx(ISO8041_2_COVERAGE_FACTOR)


@pytest.mark.parametrize(
    "table",
    [
        vibration.PVEM_INDICATION_TOLERANCES_PERCENT,
        vibration.PVEM_MAX_EXPANDED_UNCERTAINTY_PERCENT,
    ],
)
def test_the_pvem_tables_are_read_only(table: dict[str, float]) -> None:
    """A published table cannot be edited by the code that reads it."""
    with pytest.raises(TypeError, match="does not support item assignment"):
        table["12.7"] = 0.0
