#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published solids, against the page they were transcribed from.

A catalogue is only worth what its provenance is worth, so most of these tests
are about what the page said rather than what the numbers are. Table A2 marks
most of its Poisson ratios and loss factors "Estimate", prints four cells as a
range and two as an upper bound, and credits four different authors across its
rows. The library's copy has to carry all of it, because a caller who reads a
0,2 Poisson ratio as a measurement will trust it further than the book does.

The one arithmetic test is the steel row, which is also the only row the table
gives enough of to close the loop: a plate speed, a density and a Poisson
ratio, and no modulus. The inverse has to land on the modulus every handbook
prints for structural steel.
"""

from __future__ import annotations

import math

import pytest
import reference_data as ref

from phonometry.solids import (
    PUBLISHED_SOLIDS,
    SolidMaterial,
    beam_longitudinal_speed,
    bulk_longitudinal_speed,
    solids_named,
)

#: Hopkins Table A2 on its own, by the row key the page gives each material.
#: The catalogue keys every row by its table as well, because two books print
#: a steel and they are not the same steel.
HOPKINS = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "hopkins-2007-table-a2"
}
CREMER = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "cremer-2005-table-4-3"
}


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
def test_every_printed_row_is_in_the_catalogue() -> None:
    """Twenty-five rows on the page, twenty-five in the library."""
    assert len(HOPKINS) == len(ref.HOPKINS_A2_ROWS)
    assert set(HOPKINS) == {key for key, *_ in ref.HOPKINS_A2_ROWS}


@pytest.mark.parametrize(("key", "density", "nu", "eta"), ref.HOPKINS_A2_ROWS)
def test_each_row_carries_the_printed_cells(
    key: str, density: float | None, nu: float, eta: float | None
) -> None:
    """Density, Poisson ratio and loss factor, cell by cell."""
    material = HOPKINS[key]

    assert material.density_kg_m3 == density
    assert material.poisson_ratio == pytest.approx(nu)
    assert material.flexural_loss_factor == (
        None if eta is None else pytest.approx(eta)
    )


@pytest.mark.parametrize(("name", "speed", "hfc"), ref.HOPKINS_A2_PLATE_SPEED_AND_HFC)
def test_the_speed_and_hfc_columns_agree_with_the_older_oracle(
    name: str, speed: float, hfc: float
) -> None:
    """Two transcriptions of one table, made months apart, have to agree.

    The speed and ``h.f_c`` columns were transcribed once already, as the
    oracle for ``thickness_critical_frequency_product``. This is the catalogue
    read back against them, which is the cheapest check there is that the
    second pass over the same page did not slip a digit.
    """
    del name
    matches = [
        m
        for m in HOPKINS.values()
        if m.plate_longitudinal_speed_m_s == pytest.approx(speed)
        and m.thickness_critical_frequency_product_m_hz == pytest.approx(hfc)
    ]

    assert matches, f"no catalogue row with {speed} m/s and {hfc} m Hz"


# ---------------------------------------------------------------------------
# What the page says that is not a number
# ---------------------------------------------------------------------------
def test_only_four_poisson_ratios_are_measurements() -> None:
    """The other twenty-one carry the footnote that reads "Estimate"."""
    measured = {key for key, m in HOPKINS.items() if not m.is_estimate("poisson_ratio")}

    assert measured == set(ref.HOPKINS_A2_MEASURED_POISSON)


def test_the_estimated_loss_factors_are_marked_as_such() -> None:
    """Twelve of them, and the rest are either measured or absent."""
    estimated = {
        key for key, m in HOPKINS.items() if m.is_estimate("flexural_loss_factor")
    }

    assert estimated == set(ref.HOPKINS_A2_ESTIMATED_LOSS_FACTOR)


@pytest.mark.parametrize(("key", "field_name", "low", "high"), ref.HOPKINS_A2_RANGES)
def test_a_cell_printed_as_an_interval_is_kept_as_one(
    key: str, field_name: str, low: float, high: float
) -> None:
    """Five cells, and none of them becomes a midpoint the page never gave."""
    material = HOPKINS[key]

    assert material.ranges[field_name] == (low, high)


@pytest.mark.parametrize(("key", "bound"), ref.HOPKINS_A2_UPPER_BOUNDS)
def test_a_loss_factor_printed_as_a_bound_is_not_a_value(
    key: str, bound: float
) -> None:
    """Aluminium and steel say "at most", which is not the same as "is"."""
    material = HOPKINS[key]

    assert "flexural_loss_factor" in material.bounded_above
    assert material.flexural_loss_factor is None
    assert material.ranges["flexural_loss_factor"] == (0.0, bound)


@pytest.mark.parametrize(("key", "credit"), ref.HOPKINS_A2_ATTRIBUTIONS)
def test_a_row_the_book_credits_to_someone_else_says_so(key: str, credit: str) -> None:
    """Rindel, Schmitz, Heckl and the rest keep their names on their rows."""
    assert HOPKINS[key].attributed_to["row"] == credit


def test_the_steel_row_credits_two_authors_across_three_cells() -> None:
    """The one row whose columns do not share a source."""
    steel = HOPKINS["steel"]

    assert steel.attributed_to["plate_longitudinal_speed_m_s"] == "Fahy, 1985"
    assert steel.attributed_to["poisson_ratio"] == "Fahy, 1985"
    assert steel.attributed_to["flexural_loss_factor"] == "Heckl, 1981"


def test_the_orthotropic_row_says_that_it_is_orthotropic() -> None:
    """OSB's quoted speed is an effective one, and the note says so."""
    osb = HOPKINS["osb"]

    assert "orthotropic" in osb.note
    assert osb.ranges["plate_longitudinal_speed_m_s"] == (2200.0, 3500.0)


def test_every_row_names_the_page_it_came_from() -> None:
    """The whole point of a published catalogue."""
    assert all("Table A2" in m.source for m in HOPKINS.values())
    assert all("635-636" in m.source for m in HOPKINS.values())


# ---------------------------------------------------------------------------
# What a row is for
# ---------------------------------------------------------------------------
def test_the_steel_row_closes_back_to_the_handbook_modulus() -> None:
    """Table A2 prints no modulus, which is why the inverse exists."""
    low, high = ref.STRUCTURAL_STEEL_YOUNGS_MODULUS_BAND_PA
    steel = HOPKINS["steel"]

    modulus = steel.youngs_modulus_pa

    assert modulus is not None
    assert modulus > low
    assert modulus < high
    assert steel.is_derived("youngs_modulus_pa")


def test_a_derived_modulus_says_which_cells_it_came_from() -> None:
    """A computed number stored as if it had been read is a lie about a page."""
    assert (
        HOPKINS["steel"].derived["youngs_modulus_pa"]
        == "from the plate speed, the density and the Poisson ratio"
    )


def test_a_row_whose_density_is_a_range_has_no_modulus_and_says_why() -> None:
    """Choosing a density inside the range is the caller's call, not ours.

    Hopkins prints 400 to 800 kg/m3 for aircrete because that is what is
    known about it. Deriving a modulus from the midpoint would be handing back
    a number the page deliberately did not give.
    """
    aircrete = HOPKINS["aircrete"]

    assert aircrete.youngs_modulus_pa is None
    assert aircrete.why_missing("density_kg_m3") == (
        "the page prints 400 to 800 and no value"
    )


def test_a_field_that_is_not_missing_has_no_reason_to_be() -> None:
    """``why_missing`` answers about a hole, and there is no hole here."""
    assert HOPKINS["steel"].why_missing("density_kg_m3") == ""


def test_why_missing_refuses_a_field_this_class_does_not_have() -> None:
    """A misspelt name must not answer as if the cell were empty."""
    with pytest.raises(AttributeError):
        HOPKINS["steel"].why_missing("densty_kg_m3")


def test_the_table_itself_cannot_be_edited() -> None:
    """The annotation says ``Mapping``; the object has to mean it.

    A row that cannot be edited is only half of it. A plain ``dict`` behind a
    ``Mapping`` annotation still lets a caller add a material the page never
    printed, or replace one, and every later reader of the catalogue would
    have no way to tell.
    """
    with pytest.raises(TypeError):
        PUBLISHED_SOLIDS["unobtainium"] = HOPKINS["steel"]  # type: ignore[index]


def test_the_mappings_inside_a_row_cannot_be_edited() -> None:
    """``frozen=True`` stops a rebind, not a write through a field.

    The row is shared by every caller, so a ``ranges`` or an ``attributed_to``
    that one of them can rewrite in place is provenance that cannot be
    trusted, however frozen the row around it looks.
    """
    row = HOPKINS["steel"]
    with pytest.raises(TypeError):
        row.attributed_to["flexural_loss_factor"] = "nobody"  # type: ignore[index]
    with pytest.raises(TypeError):
        row.ranges["flexural_loss_factor"] = (0.0, 1.0)  # type: ignore[index]
    assert row.attributed_to["flexural_loss_factor"] == "Heckl, 1981"


def test_every_row_is_a_solid_material() -> None:
    """What the next test proves about the class, it proves about every row."""
    assert all(isinstance(row, SolidMaterial) for row in HOPKINS.values())


def test_a_row_cannot_be_edited() -> None:
    """A shared table that a caller can edit is a bug waiting to happen.

    The row built here is this test's own, not one out of the catalogue: the
    assignment is refused either way, but reaching into shared state to prove
    it is a habit worth not having in a suite this size.
    """
    row = SolidMaterial(
        name="Steel",
        source="Hopkins (2007) Table A2, PDF page 635 (printed p. 607)",
        plate_longitudinal_speed_m_s=5270.0,
        poisson_ratio=0.28,
        thickness_critical_frequency_product_m_hz=12.3,
        density_kg_m3=7800.0,
    )
    with pytest.raises(AttributeError):
        row.density_kg_m3 = 1.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Cremer Table 4.3: a second book, and the first that checks itself
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("key", "rho", "modulus", "shear", "nu", "bar", "transverse"),
    ref.CREMER_4_3_ROWS,
)
def test_each_cremer_row_carries_the_printed_cells(
    key: str,
    rho: float,
    modulus: float,
    shear: float,
    nu: float,
    bar: float,
    transverse: float,
) -> None:
    """Six columns, cell by cell, as PDF page 201 prints them."""
    metal = CREMER[key]

    assert metal.density_kg_m3 == rho
    assert metal.youngs_modulus_pa == modulus
    assert metal.shear_modulus_pa == shear
    assert metal.poisson_ratio == nu
    assert metal.bar_longitudinal_speed_m_s == bar
    assert metal.transverse_speed_m_s == transverse


@pytest.mark.parametrize("key", [row[0] for row in ref.CREMER_4_3_ROWS])
def test_no_cremer_column_is_derived(key: str) -> None:
    """The page prints all six, so nothing here may be computed.

    This is the test that would catch a derivation quietly overwriting a
    printed cell, which would turn the table's own cross-check into a
    tautology: the point of this row is that six numbers were measured and
    three relations tie them together.
    """
    printed = (
        "density_kg_m3",
        "youngs_modulus_pa",
        "shear_modulus_pa",
        "poisson_ratio",
        "bar_longitudinal_speed_m_s",
        "transverse_speed_m_s",
    )

    assert [f for f in printed if CREMER[key].is_derived(f)] == []


@pytest.mark.parametrize(
    ("key", "rho", "modulus", "shear", "nu", "bar", "transverse"),
    ref.CREMER_4_3_ROWS,
)
def test_the_cremer_row_agrees_with_the_three_relations_that_tie_it(
    key: str,
    rho: float,
    modulus: float,
    shear: float,
    nu: float,
    bar: float,
    transverse: float,
) -> None:
    """The table prints E, G, nu and both speeds, so each row over-determines
    itself.

    No other table in this catalogue does. It is the only place where a
    transcription error shows up as physics rather than as a number that looks
    plausible, which is why it is worth having twice: once as data and once as
    this.
    """
    del key
    tolerance = ref.CREMER_4_3_CONSISTENCY_TOLERANCE

    assert shear == pytest.approx(modulus / (2.0 * (1.0 + nu)), rel=tolerance)
    assert bar == pytest.approx(math.sqrt(modulus / rho), rel=tolerance)
    assert transverse == pytest.approx(math.sqrt(shear / rho), rel=tolerance)


@pytest.mark.parametrize(("key", "variant"), ref.CREMER_4_3_VARIANTS)
def test_a_specimen_the_page_distinguishes_is_its_own_row(
    key: str, variant: str
) -> None:
    """Lead and copper print two specimens under one name.

    They share every column but the flexural loss factor, and the Remarks
    column is the only thing that says which is which. Collapsing them would
    lose a factor of fifty on the lead.
    """
    assert CREMER[key].variant == variant


def test_the_two_leads_differ_only_in_the_loss_factor() -> None:
    """A variant is a specimen, not a different material."""
    pure = CREMER["lead_chemically_pure"]
    antimonial = CREMER["lead_antimonial"]

    assert pure.density_kg_m3 == antimonial.density_kg_m3
    assert pure.youngs_modulus_pa == antimonial.youngs_modulus_pa
    assert (
        pure.ranges["flexural_loss_factor"] != antimonial.ranges["flexural_loss_factor"]
    )


def test_a_cell_the_page_prints_with_a_tilde_is_marked_approximate() -> None:
    """Not an estimate and not an interval: a number rounded on purpose."""
    assert CREMER["gold"].is_approximate("flexural_loss_factor")
    assert not CREMER["steel"].is_approximate("flexural_loss_factor")


def test_a_loss_factor_printed_as_a_bound_is_a_bound_here_too() -> None:
    """Brass, nickel and silver print ``<`` in the longitudinal column."""
    for key, high in (("brass", 1e-3), ("nickel", 1e-3), ("silver", 3e-3)):
        metal = CREMER[key]
        assert "longitudinal_loss_factor" in metal.bounded_above
        assert metal.longitudinal_loss_factor is None
        assert metal.ranges["longitudinal_loss_factor"] == (0.0, high)


@pytest.mark.parametrize(("key", "field", "credit"), ref.CREMER_4_3_ATTRIBUTIONS)
def test_a_bracketed_reference_is_resolved_to_its_authors(
    key: str, field: str, credit: str
) -> None:
    """``[4.19]`` is not a citation until someone opens the reference list."""
    assert CREMER[key].attributed_to[field] == credit


# ---------------------------------------------------------------------------
# Two books, one material
# ---------------------------------------------------------------------------
def test_a_material_both_books_print_comes_back_twice() -> None:
    """Choosing between two published steels is the caller's call."""
    steels = solids_named("Steel")

    assert {row.table for row in steels} == {
        "hopkins-2007-table-a2",
        "cremer-2005-table-4-3",
    }


def test_the_lookup_ignores_case_and_answers_nothing_for_an_unknown_name() -> None:
    assert len(solids_named("steel")) == len(solids_named("STEEL"))
    assert solids_named("unobtainium") == ()


def test_both_books_reach_the_same_three_speeds_for_their_own_steel() -> None:
    """Every row carries all three waves, whichever one its page printed.

    Hopkins prints a plate speed and Cremer a bar speed, and the other two
    follow from the row's own cells. Without that, comparing the books means
    comparing a plate speed with a bar speed, which differ by five per cent in
    steel and would read as a disagreement between the books rather than
    between two waves.
    """
    for steel in solids_named("Steel"):
        assert steel.bar_longitudinal_speed_m_s is not None
        assert steel.plate_longitudinal_speed_m_s is not None
        assert steel.bulk_longitudinal_speed_m_s is not None


def test_the_gap_cremer_prints_between_bar_and_bulk_comes_out_of_the_functions() -> (
    None
):
    """Cremer states 16 per cent at ``nu = 0.3``, under Eq. (3.32).

    It is an oracle the library did not have: ``bulk_longitudinal_speed`` was
    anchored on Norton & Karczub Eq. (1.225), and this reaches the same place
    from a different book by a different route.
    """
    modulus, density, nu = 200e9, 7800.0, 0.3

    bar = beam_longitudinal_speed(modulus, density_kg_m3=density)
    bulk = bulk_longitudinal_speed(modulus, density_kg_m3=density, poisson_ratio=nu)

    assert bulk / bar - 1.0 == pytest.approx(ref.CREMER_BAR_TO_BULK_AT_NU_0_3, abs=5e-4)
