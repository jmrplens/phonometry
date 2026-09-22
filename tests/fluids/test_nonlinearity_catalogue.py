#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Rossing's four tables of B/A, against a second reading of their pages.

The oracle in :mod:`tests.reference_data.wave4_fluids` holds each cell as the
page prints it, plus-or-minus, minus sign and brackets included. These tests
read every value back out of :data:`phonometry.fluids.PUBLISHED_NONLINEARITY`
and pin what the page says around it: which paper each number comes from, the
uncertainty where one is printed, the pressure only where a table prints one,
the two cells of Table 8.2 that print a rule, and the one line of Table 8.3 the
page prints twice.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry import fluids
from phonometry.fluids import (
    PUBLISHED_NONLINEARITY,
    NonlinearityParameter,
    nonlinearity_named,
)

T81 = "rossing-2014-table-8-1"
T82 = "rossing-2014-table-8-2"
T83 = "rossing-2014-table-8-3"
T84 = "rossing-2014-table-8-4"
KELVIN = (303.15, 313.15, 323.15, 333.15, 343.15, 353.15, 363.15, 373.15)
GROUPS = ("Liquid metals", "Liquid gases", "Other substances")


def _rows(table: str) -> list[NonlinearityParameter]:
    return [row for row in PUBLISHED_NONLINEARITY.values() if row.table == table]


def _number(cell: str) -> float:
    return float(cell.replace("−", "-").replace(" ", ""))


def _value(cell: str) -> tuple[float, float | None]:
    """The printed B/A and the plus-or-minus beside it, if any."""
    if "±" in cell:
        value, spread = cell.split("±")
        return _number(value), _number(spread)
    return _number(cell), None


def _check(row: NonlinearityParameter, cell: str, reference: str) -> None:
    value, spread = _value(cell)
    assert row.b_over_a == value
    if spread is None:
        assert "b_over_a" not in row.uncertainty
    else:
        assert row.uncertainty == {"b_over_a": spread}
    assert row.attributed_to["b_over_a"].endswith(f" {reference}")


# ---------------------------------------------------------------------------
# Every printed value, read back
# ---------------------------------------------------------------------------
def test_table_8_1_holds_every_measurement_with_its_year_and_paper() -> None:
    rows = _rows(T81)
    assert len(rows) == len(ref.ROSSING_8_1) == 18
    for row, (temperature, (value, year, reference)) in zip(
        rows, ref.ROSSING_8_1, strict=True
    ):
        assert row.name == "Water"
        assert row.temperature_c == _number(temperature)
        assert row.year == int(year)
        assert row.static_pressure_pa is None
        _check(row, value, reference)


def test_table_8_2_is_one_row_per_printed_cell_and_none_for_a_rule() -> None:
    rows = {(row.static_pressure_pa, row.temperature_c): row for row in _rows(T82)}
    rules = 0
    for pressure, cells in ref.ROSSING_8_2:
        for kelvin, cell in zip(KELVIN, cells, strict=True):
            key = (_number(pressure) * 1e6, round(kelvin - 273.15, 9))
            if cell == "–":
                rules += 1
                assert key not in rows
                continue
            _check(rows[key], cell, "[8.65]")
    assert rules == 2
    assert len(rows) == 8 * 8 - rules


def test_the_two_tables_of_water_agree_where_they_print_the_same_paper() -> None:
    """Table 8.1's [8.65] rows are Table 8.2's 0.1 MPa row, cell for cell."""
    atmospheric = {
        row.temperature_c: row.b_over_a
        for row in _rows(T81)
        if row.attributed_to["b_over_a"].endswith("[8.65]")
    }
    low_pressure = {
        row.temperature_c: row.b_over_a
        for row in _rows(T82)
        if row.static_pressure_pa == pytest.approx(0.1e6)
    }
    assert atmospheric == low_pressure
    assert sorted(atmospheric) == [30, 40, 50, 60, 70, 80]


def test_table_8_3_names_every_row_the_page_leaves_blank() -> None:
    rows = _rows(T83)
    name = ""
    expected = []
    for label, cells in ref.ROSSING_8_3:
        name = label or name
        expected.append((name, cells))
    # The page prints one line twice; the catalogue holds it once.
    deduplicated = [
        entry for i, entry in enumerate(expected) if entry not in expected[:i]
    ]
    assert len(deduplicated) == len(expected) - 1 == len(rows) == 61
    for row, (substance, (temperature, value, reference)) in zip(
        rows, deduplicated, strict=True
    ):
        assert row.name == substance
        assert row.temperature_c == _number(temperature)
        _check(row, value, reference)


def test_the_line_printed_twice_is_one_row_that_says_so() -> None:
    printed = [cells for label, cells in ref.ROSSING_8_3 if label == "1-Pentanol"]
    assert printed == [("20", "10", "[8.68]"), ("20", "10", "[8.68]")]
    (pentanol,) = nonlinearity_named("1-pentanol")
    assert "twice" in pentanol.note
    assert "ERRATA" in pentanol.note


def test_table_8_4_files_every_row_under_the_heading_it_is_printed_under() -> None:
    rows = _rows(T84)
    group = ""
    expected = []
    for label, cells in ref.ROSSING_8_4:
        if label in GROUPS:
            assert cells == ("", "", "")
            group = label
            continue
        expected.append((group, label, cells))
    assert len(rows) == len(expected) == 23
    name = ""
    for row, (heading, label, (temperature, value, reference)) in zip(
        rows, expected, strict=True
    ):
        name = label or name
        assert (row.group, row.name) == (heading, name)
        assert row.temperature_c == _number(temperature)
        _check(row, value, reference)


def test_a_liquefied_gas_is_held_at_the_negative_temperature_printed() -> None:
    (helium,) = nonlinearity_named("helium")
    assert helium.temperature_c == pytest.approx(-271.38)
    assert helium.b_over_a == 4.5


# ---------------------------------------------------------------------------
# What surrounds the number
# ---------------------------------------------------------------------------
def test_every_value_names_the_paper_it_comes_from() -> None:
    for row in PUBLISHED_NONLINEARITY.values():
        credit = row.attributed_to["b_over_a"]
        assert credit.endswith("]")
        # The reference list is spelled out, not left as a bracketed number.
        assert len(credit) > 40


def test_only_the_pressure_table_holds_a_pressure() -> None:
    for row in PUBLISHED_NONLINEARITY.values():
        if row.table == T82:
            assert row.static_pressure_pa is not None
        else:
            assert row.static_pressure_pa is None


def test_only_table_8_1_holds_a_year() -> None:
    for row in PUBLISHED_NONLINEARITY.values():
        assert (row.year is not None) == (row.table == T81)


def test_every_row_cites_its_own_page() -> None:
    pages = {row.table: row.source for row in PUBLISHED_NONLINEARITY.values()}
    assert pages == {
        T81: "Rossing (2014) Table 8.1, PDF page 284 (printed p. 268)",
        T82: "Rossing (2014) Table 8.2, PDF page 284 (printed p. 268)",
        T83: "Rossing (2014) Table 8.3, PDF page 285 (printed p. 269)",
        T84: "Rossing (2014) Table 8.4, PDF page 285 (printed p. 269)",
    }


def test_the_lookup_matches_a_fragment_and_ignores_case() -> None:
    water = nonlinearity_named("WATER")
    assert {row.table for row in water} == {T81, T82, T84}
    assert len(water) == 18 + 62 + 1
    assert nonlinearity_named("unobtainium") == ()


def test_the_catalogue_is_reachable_and_cannot_be_written_to() -> None:
    assert fluids.PUBLISHED_NONLINEARITY is PUBLISHED_NONLINEARITY
    with pytest.raises(TypeError):
        PUBLISHED_NONLINEARITY["x/y"] = NonlinearityParameter(  # type: ignore[index]
            name="x", source="nowhere"
        )
