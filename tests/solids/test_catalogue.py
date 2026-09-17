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

import pytest
import reference_data as ref

from phonometry.solids import PUBLISHED_SOLIDS, SolidMaterial


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
def test_every_printed_row_is_in_the_catalogue() -> None:
    """Twenty-five rows on the page, twenty-five in the library."""
    assert len(PUBLISHED_SOLIDS) == len(ref.HOPKINS_A2_ROWS)
    assert set(PUBLISHED_SOLIDS) == {key for key, *_ in ref.HOPKINS_A2_ROWS}


@pytest.mark.parametrize(("key", "density", "nu", "eta"), ref.HOPKINS_A2_ROWS)
def test_each_row_carries_the_printed_cells(
    key: str, density: float | None, nu: float, eta: float | None
) -> None:
    """Density, Poisson ratio and loss factor, cell by cell."""
    material = PUBLISHED_SOLIDS[key]

    assert material.density_kg_m3 == density
    assert material.poisson_ratio == pytest.approx(nu)
    assert material.loss_factor == (None if eta is None else pytest.approx(eta))


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
        for m in PUBLISHED_SOLIDS.values()
        if m.longitudinal_speed_m_s == pytest.approx(speed)
        and m.thickness_critical_frequency_product_m_hz == pytest.approx(hfc)
    ]

    assert matches, f"no catalogue row with {speed} m/s and {hfc} m Hz"


# ---------------------------------------------------------------------------
# What the page says that is not a number
# ---------------------------------------------------------------------------
def test_only_four_poisson_ratios_are_measurements() -> None:
    """The other twenty-one carry the footnote that reads "Estimate"."""
    measured = {
        key for key, m in PUBLISHED_SOLIDS.items() if not m.is_estimate("poisson_ratio")
    }

    assert measured == set(ref.HOPKINS_A2_MEASURED_POISSON)


def test_the_estimated_loss_factors_are_marked_as_such() -> None:
    """Twelve of them, and the rest are either measured or absent."""
    estimated = {
        key for key, m in PUBLISHED_SOLIDS.items() if m.is_estimate("loss_factor")
    }

    assert estimated == set(ref.HOPKINS_A2_ESTIMATED_LOSS_FACTOR)


@pytest.mark.parametrize(("key", "field_name", "low", "high"), ref.HOPKINS_A2_RANGES)
def test_a_cell_printed_as_an_interval_is_kept_as_one(
    key: str, field_name: str, low: float, high: float
) -> None:
    """Five cells, and none of them becomes a midpoint the page never gave."""
    material = PUBLISHED_SOLIDS[key]

    assert material.ranges[field_name] == (low, high)


@pytest.mark.parametrize(("key", "bound"), ref.HOPKINS_A2_UPPER_BOUNDS)
def test_a_loss_factor_printed_as_a_bound_is_not_a_value(
    key: str, bound: float
) -> None:
    """Aluminium and steel say "at most", which is not the same as "is"."""
    material = PUBLISHED_SOLIDS[key]

    assert "loss_factor" in material.bounded_above
    assert material.loss_factor is None
    assert material.ranges["loss_factor"] == (0.0, bound)


@pytest.mark.parametrize(("key", "credit"), ref.HOPKINS_A2_ATTRIBUTIONS)
def test_a_row_the_book_credits_to_someone_else_says_so(key: str, credit: str) -> None:
    """Rindel, Schmitz, Heckl and the rest keep their names on their rows."""
    assert PUBLISHED_SOLIDS[key].attributed_to["row"] == credit


def test_the_steel_row_credits_two_authors_across_three_cells() -> None:
    """The one row whose columns do not share a source."""
    steel = PUBLISHED_SOLIDS["steel"]

    assert steel.attributed_to["longitudinal_speed_m_s"] == "Fahy, 1985"
    assert steel.attributed_to["poisson_ratio"] == "Fahy, 1985"
    assert steel.attributed_to["loss_factor"] == "Heckl, 1981"


def test_the_orthotropic_row_says_that_it_is_orthotropic() -> None:
    """OSB's quoted speed is an effective one, and the note says so."""
    osb = PUBLISHED_SOLIDS["osb"]

    assert "orthotropic" in osb.note
    assert osb.ranges["longitudinal_speed_m_s"] == (2200.0, 3500.0)


def test_every_row_names_the_page_it_came_from() -> None:
    """The whole point of a published catalogue."""
    assert all("Table A2" in m.source for m in PUBLISHED_SOLIDS.values())
    assert all("635-636" in m.source for m in PUBLISHED_SOLIDS.values())


# ---------------------------------------------------------------------------
# What a row is for
# ---------------------------------------------------------------------------
def test_the_steel_row_closes_back_to_the_handbook_modulus() -> None:
    """Table A2 prints no modulus, which is why the inverse exists."""
    low, high = ref.STRUCTURAL_STEEL_YOUNGS_MODULUS_BAND_PA

    modulus = PUBLISHED_SOLIDS["steel"].youngs_modulus_pa()

    assert modulus > low
    assert modulus < high


def test_a_row_whose_density_is_a_range_refuses_to_give_a_modulus() -> None:
    """Choosing a density inside the range is the caller's call, not ours.

    Hopkins prints 400 to 800 kg/m3 for aircrete because that is what is
    known about it. Returning a modulus for the midpoint would be handing back
    a number the page deliberately did not give.
    """
    with pytest.raises(ValueError, match="400 to 800"):
        PUBLISHED_SOLIDS["aircrete"].youngs_modulus_pa()


def test_the_table_itself_cannot_be_edited() -> None:
    """The annotation says ``Mapping``; the object has to mean it.

    A row that cannot be edited is only half of it. A plain ``dict`` behind a
    ``Mapping`` annotation still lets a caller add a material the page never
    printed, or replace one, and every later reader of the catalogue would
    have no way to tell.
    """
    with pytest.raises(TypeError):
        PUBLISHED_SOLIDS["unobtainium"] = PUBLISHED_SOLIDS["steel"]  # type: ignore[index]


def test_the_mappings_inside_a_row_cannot_be_edited() -> None:
    """``frozen=True`` stops a rebind, not a write through a field.

    The row is shared by every caller, so a ``ranges`` or an ``attributed_to``
    that one of them can rewrite in place is provenance that cannot be
    trusted, however frozen the row around it looks.
    """
    row = PUBLISHED_SOLIDS["steel"]
    with pytest.raises(TypeError):
        row.attributed_to["loss_factor"] = "nobody"  # type: ignore[index]
    with pytest.raises(TypeError):
        row.ranges["loss_factor"] = (0.0, 1.0)  # type: ignore[index]
    assert row.attributed_to["loss_factor"] == "Heckl, 1981"


def test_every_row_is_a_solid_material() -> None:
    """What the next test proves about the class, it proves about every row."""
    assert all(isinstance(row, SolidMaterial) for row in PUBLISHED_SOLIDS.values())


def test_a_row_cannot_be_edited() -> None:
    """A shared table that a caller can edit is a bug waiting to happen.

    The row built here is this test's own, not one out of the catalogue: the
    assignment is refused either way, but reaching into shared state to prove
    it is a habit worth not having in a suite this size.
    """
    row = SolidMaterial(
        name="Steel",
        source="Hopkins (2007) Table A2, PDF page 635 (printed p. 607)",
        longitudinal_speed_m_s=5270.0,
        poisson_ratio=0.28,
        thickness_critical_frequency_product_m_hz=12.3,
        density_kg_m3=7800.0,
    )
    with pytest.raises(AttributeError):
        row.density_kg_m3 = 1.0  # type: ignore[misc]
