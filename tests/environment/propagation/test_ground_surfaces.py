#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the published ground surfaces (``environment.propagation``).

Every outdoor model in this package asks the ground how resistive it is, and
the answer comes off a page rather than out of an instrument. What these tests
hold to account is the reading of those pages: that a number that appears in
two books comes out the same, that a cell the page did not print as a number
is not one here, and that the eight classes the propagation models define are
the eight the models in this library already use.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry.aircraft.rotorcraft_propagation import _FLOW_RESISTIVITY
from phonometry.environment.propagation import (
    PUBLISHED_GROUND,
    GroundSurface,
    ground_surfaces_named,
)

#: The tables this catalogue reads, and how many rows each page prints.
_TABLES = {
    "bies-2017-table-5-1": 34,
    "bies-2017-table-5-2": 8,
    "cox-2017-table-6-7": 63,
}


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
def test_every_table_holds_the_rows_its_page_prints() -> None:
    """Row counts per table, so a dropped row cannot pass unnoticed."""
    counted: dict[str, int] = {}
    for row in PUBLISHED_GROUND.values():
        counted[row.table] = counted.get(row.table, 0) + 1

    assert counted == _TABLES


def test_every_row_cites_a_document_a_page_and_a_folio() -> None:
    """Read the citations the way the provenance gate reads them."""
    for key, row in PUBLISHED_GROUND.items():
        assert row.source.startswith(("Bies 5e ", "Cox & D'Antonio 3e ")), key
        assert "PDF page" in row.source, key
        assert "printed p" in row.source, key


def test_every_row_is_named_and_keyed_by_its_table() -> None:
    for key, row in PUBLISHED_GROUND.items():
        assert row.name, key
        assert key == f"{row.table}/{key.split('/', 1)[1]}"


# ---------------------------------------------------------------------------
# What two books say about the same ground
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("bies", "cox", "printed"), ref.EMBLETON_SHARED_GROUND)
def test_the_two_books_agree_where_they_share_a_source(
    bies: str, cox: str, printed: object
) -> None:
    """Bies and Cox both take these seven surfaces from Embleton (1983).

    Bies prints kPa s/m2 and Cox prints rayl/m, so a pair that matches has
    matched through a conversion as well as through two readings of two
    different pages.
    """
    from_bies = PUBLISHED_GROUND[f"bies-2017-table-5-1/{bies}"]
    from_cox = PUBLISHED_GROUND[f"cox-2017-table-6-7/{cox}"]

    held = [
        row.ranges.get("flow_resistivity_pa_s_m2") or row.flow_resistivity_pa_s_m2
        for row in (from_bies, from_cox)
    ]

    assert held[0] == pytest.approx(printed, rel=1e-12)
    assert held[1] == pytest.approx(printed, rel=1e-12)


# ---------------------------------------------------------------------------
# The eight classes the propagation models define
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("key", "letter", "resistivity", "iso_g", "nmpb_g"), ref.BIES_GROUND_CLASSES
)
def test_each_ground_class_carries_its_letter_and_its_two_factors(
    key: str, letter: str, resistivity: float, iso_g: float, nmpb_g: float
) -> None:
    """The class table is not measured ground: it is what the models define."""
    row = PUBLISHED_GROUND[f"bies-2017-table-5-2/{key}"]

    assert row.harmonoise_class == letter
    assert row.flow_resistivity_pa_s_m2 == pytest.approx(resistivity, rel=1e-12)
    assert row.iso_9613_ground_factor == pytest.approx(iso_g, rel=1e-12)
    assert row.nmpb_ground_factor == pytest.approx(nmpb_g, rel=1e-12)


def test_the_two_ground_factors_differ_for_two_of_the_eight_classes() -> None:
    """Which is the reason to carry both rather than one.

    ISO 9613-2 admits only hard ground and porous ground; NMPB-2008 grades the
    two classes in between at 0,7 and 0,3.
    """
    classes = {
        row.harmonoise_class: row
        for row in PUBLISHED_GROUND.values()
        if row.harmonoise_class
    }

    differing = {
        letter
        for letter, row in classes.items()
        if row.iso_9613_ground_factor != row.nmpb_ground_factor
    }

    assert differing == {"E", "F"}


def test_the_rotorcraft_model_and_the_book_print_the_same_eight_numbers() -> None:
    """A fourth reading of the same table, from the other side of the tree.

    The rotorcraft model carries its own copy because it implements ECAC
    Doc 32, which prints the table itself, and a module cites the document it
    implements. That two documents print the same eight numbers is worth a
    test rather than a shared constant.
    """
    from_book = {
        row.harmonoise_class: row.flow_resistivity_pa_s_m2
        for row in PUBLISHED_GROUND.values()
        if row.harmonoise_class
    }

    assert from_book == pytest.approx(_FLOW_RESISTIVITY, rel=1e-12)


# ---------------------------------------------------------------------------
# The cells that are not a number
# ---------------------------------------------------------------------------
def test_the_cell_printed_with_two_decimal_points_is_not_a_number() -> None:
    """Cox's heath row prints ``1.7.3 x 10^5``, which nobody can read.

    Guessing at 1,73 or 1,7 would be inventing a resistivity, so the cell
    keeps what the page printed and the row says the number is missing.
    """
    row = PUBLISHED_GROUND["cox-2017-table-6-7/heath_line_1_marked_b"]

    assert row.flow_resistivity_pa_s_m2 is None
    assert "1.7.3" in row.unquantified["flow_resistivity_pa_s_m2"]
    assert row.why_missing("flow_resistivity_pa_s_m2").startswith("the page prints")


def test_an_uncertainty_the_page_prints_is_kept_beside_its_value() -> None:
    """Cox prints ``(540 +/- 92) x 10^3`` and two rows where it swamps the value."""
    row = PUBLISHED_GROUND["cox-2017-table-6-7/humus_on_pine_forest_floor"]

    assert row.flow_resistivity_pa_s_m2 == pytest.approx(230_000.0, rel=1e-12)
    assert row.uncertainty["flow_resistivity_pa_s_m2"] == pytest.approx(
        220_000.0, rel=1e-12
    )


def test_one_surface_fitted_three_ways_is_three_rows() -> None:
    """The fit is part of the quantity, so it is part of the row.

    An effective flow resistivity is whatever makes one model reproduce a
    measurement, so the same grass fitted with three models is three numbers
    and averaging them would average three different quantities.
    """
    lawns = [
        row
        for key, row in PUBLISHED_GROUND.items()
        if key.startswith("cox-2017-table-6-7/lawn")
    ]

    assert len(lawns) >= 2
    assert len({row.variant for row in lawns}) == len(lawns)
    for row in lawns:
        assert row.variant


def test_a_negative_porosity_decay_is_kept_negative() -> None:
    """Nine of Cox's rows print one, and a sign is a reading like any other."""
    negatives = [
        row
        for row in PUBLISHED_GROUND.values()
        if (row.porosity_decay_rate_per_m or 0.0) < 0.0
    ]

    assert negatives


def test_a_row_answers_none_where_its_page_printed_nothing() -> None:
    """Bies prints no porosity at all, and a row of his says so."""
    row = PUBLISHED_GROUND["bies-2017-table-5-1/sugar_snow"]

    assert row.porosity is None
    assert row.why_missing("porosity") == (
        "the page does not give it, and it does not follow from the cells that it does"
    )


# ---------------------------------------------------------------------------
# Looking a surface up
# ---------------------------------------------------------------------------
def test_a_name_answers_with_every_book_that_prints_it() -> None:
    rows = ground_surfaces_named("Sugar snow")

    assert len(rows) == 2
    assert {row.table for row in rows} == {
        "bies-2017-table-5-1",
        "cox-2017-table-6-7",
    }


def test_a_name_no_page_prints_answers_with_nothing() -> None:
    assert ground_surfaces_named("Lunar regolith") == ()


def test_a_row_is_frozen_and_so_are_the_mappings_it_holds() -> None:
    """The catalogue is one object shared by every caller."""
    row = PUBLISHED_GROUND["cox-2017-table-6-7/heath_line_1_marked_b"]

    with pytest.raises(AttributeError):
        row.name = "edited"  # type: ignore[misc]
    with pytest.raises(TypeError):
        row.unquantified["flow_resistivity_pa_s_m2"] = "edited"  # type: ignore[index]


def test_the_catalogue_holds_ground_surfaces() -> None:
    assert all(isinstance(row, GroundSurface) for row in PUBLISHED_GROUND.values())
