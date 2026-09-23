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
    plate_longitudinal_speed,
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
    measured = {
        key for key, m in HOPKINS.items() if m.basis_of("poisson_ratio") != "estimated"
    }

    assert measured == set(ref.HOPKINS_A2_MEASURED_POISSON)


def test_the_estimated_loss_factors_are_marked_as_such() -> None:
    """Twelve of them, and the rest are either measured or absent."""
    estimated = {
        key
        for key, m in HOPKINS.items()
        if m.basis_of("flexural_loss_factor") == "estimated"
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
def test_a_material_several_books_print_comes_back_several_times() -> None:
    """Choosing between published steels is the caller's call, not ours."""
    steels = solids_named("Steel")

    assert {row.table for row in steels} == {
        "hopkins-2007-table-a2",
        "cremer-2005-table-4-3",
        "bies-2017-table-c1",
        "long-2014-table-12-1",
        "norton-karczub-2003-appendix-4a",
        "norton-karczub-2003-table-6-1",
        "vigran-2008-table-3-1",
    }
    assert len(steels) > len({row.table for row in steels})


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
    for steel in (HOPKINS["steel"], CREMER["steel"]):
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


def test_the_plate_speed_sits_between_the_other_two() -> None:
    """The gap Cremer prints is bar against bulk, not bar against plate.

    The prose of this package quotes his 16 per cent, and a reader who took it
    for the bar-to-plate gap would be out by a factor of three. Pinning both
    numbers here keeps that particular slip in the suite rather than only in
    the documentation, where nothing checks it.
    """
    modulus, density, nu = 200e9, 7800.0, 0.3

    bar = beam_longitudinal_speed(modulus, density_kg_m3=density)
    plate = plate_longitudinal_speed(modulus, density_kg_m3=density, poisson_ratio=nu)
    bulk = bulk_longitudinal_speed(modulus, density_kg_m3=density, poisson_ratio=nu)

    assert plate / bar == pytest.approx(1.0 / math.sqrt(1.0 - nu**2))
    assert plate / bar - 1.0 == pytest.approx(0.048, abs=5e-4)
    assert bar < plate < bulk


def test_the_oracle_covers_every_attribution_in_the_data_file() -> None:
    """A credit the oracle does not list is a credit nothing checks.

    The parametrised test above only sees what the oracle names, so an
    attribution added to the data file and not to the oracle would ride along
    untested. This is what makes that impossible rather than unlikely.
    """
    in_catalogue = {
        (key, field) for key, row in CREMER.items() for field in row.attributed_to
    }

    assert in_catalogue == {
        (key, field) for key, field, _ in ref.CREMER_4_3_ATTRIBUTIONS
    }


@pytest.mark.parametrize("key", ref.HOPKINS_A2_ROWS_WITHOUT_A_DERIVED_SPEED)
def test_a_range_only_density_derives_no_speed_and_says_so(key: str) -> None:
    """Nothing follows from a density the page declined to collapse.

    Aircrete and brick keep the plate speed Hopkins printed and nothing else:
    the bar and bulk speeds would have to come through a modulus, and there is
    no density to work one out with. Filling them from the midpoint of the
    range would be inventing two numbers out of one the book would not give.
    """
    row = HOPKINS[key]

    assert row.plate_longitudinal_speed_m_s is not None
    assert row.bar_longitudinal_speed_m_s is None
    assert row.bulk_longitudinal_speed_m_s is None
    assert row.why_missing("bar_longitudinal_speed_m_s") == (
        "the page does not give it, and it does not follow from the cells that it does"
    )


# ---------------------------------------------------------------------------
# Mechel Table 3: a third book, and the first with a defect of its own
# ---------------------------------------------------------------------------
MECHEL = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "mechel-2008-table-3"
}


def test_the_whole_table_is_here() -> None:
    """Thirty-eight rows on the two pages, thirty-eight in the library."""
    assert len(MECHEL) == 38


@pytest.mark.parametrize(("key", "rho", "modulus", "product"), ref.MECHEL_3_SCALAR_ROWS)
def test_each_mechel_row_carries_the_printed_cells(
    key: str, rho: float, modulus: float, product: float
) -> None:
    """The three columns this library reads, for the rows printed as values."""
    material = MECHEL[key]

    assert material.density_kg_m3 == rho
    assert material.youngs_modulus_pa == modulus
    assert material.thickness_critical_frequency_product_m_hz == product


@pytest.mark.parametrize(("key", "low", "high"), ref.MECHEL_3_DENSITY_RANGES)
def test_a_mechel_density_printed_as_a_range_stays_one(
    key: str, low: float, high: float
) -> None:
    assert MECHEL[key].density_kg_m3 is None
    assert MECHEL[key].ranges["density_kg_m3"] == (low, high)


def test_a_page_that_does_not_say_which_loss_factor_gets_the_unqualified_one() -> None:
    """Mechel prints one column headed "Loss fact." and nothing else.

    Putting it in ``flexural_loss_factor`` would be reading a measurement
    method off a column heading that does not give one.
    """
    steel = MECHEL["steel"]

    assert steel.loss_factor == 1e-4
    assert steel.flexural_loss_factor is None
    assert steel.longitudinal_loss_factor is None


def test_no_mechel_row_invents_a_poisson_ratio() -> None:
    """The page prints none, so neither the plate nor the bulk speed follows.

    A Poisson ratio of 0,3 would reproduce the table nicely and would be a
    number Mechel did not give. The bar speed does follow, from the modulus
    and the density, and that is as far as a row goes.
    """
    assert all(row.poisson_ratio is None for row in MECHEL.values())
    assert all(row.plate_longitudinal_speed_m_s is None for row in MECHEL.values())
    assert all(row.bulk_longitudinal_speed_m_s is None for row in MECHEL.values())
    assert MECHEL["steel"].bar_longitudinal_speed_m_s == pytest.approx(5064.0, abs=1.0)


# ---------------------------------------------------------------------------
# The errata entry for Mechel Table 3 rests on these two
# ---------------------------------------------------------------------------
def _band(row: SolidMaterial, field: str) -> tuple[float, float]:
    """A field as ``(low, high)``, whether the page printed a value or a range."""
    if field in row.ranges:
        return row.ranges[field]
    value = getattr(row, field)
    assert value is not None, field
    return value, value


def _wall_impedance_band(key: str) -> tuple[float, float]:
    """``Z_m`` from Mechel Eq. (11) on the row's own printed cells.

    The density and the ``h f_c`` come from the catalogue and only ``Z_m``
    from the oracle, because the claim is about two printed columns agreeing
    with each other and not about a transcription agreeing with itself.
    """
    row = MECHEL[key]
    rho = _band(row, "density_kg_m3")
    product = _band(row, "thickness_critical_frequency_product_m_hz")
    z0 = ref.MECHEL_REFERENCE_IMPEDANCE_N_S_M3
    return rho[0] * product[0] / z0, rho[1] * product[1] / z0


@pytest.mark.parametrize(
    ("key", "low", "high"),
    [row for row in ref.MECHEL_3_PRINTED_WALL_IMPEDANCE if row[0] != "pvc_30_softener"],
)
def test_the_printed_wall_impedance_follows_from_the_books_own_equation(
    key: str, low: float, high: float
) -> None:
    """Eq. (11) reproduces the column, which is what makes the one gap a defect.

    Without this, the disagreement of a single row could be a mistake in the
    transcription or in the equation as it was read. Thirty-seven rows over
    four decades of ``Z_m`` say it is neither.
    """
    computed_low, computed_high = _wall_impedance_band(key)
    tolerance = ref.MECHEL_3_WALL_IMPEDANCE_TOLERANCE

    assert computed_low == pytest.approx(low, rel=tolerance)
    assert computed_high == pytest.approx(high, rel=tolerance)


def test_the_one_row_that_does_not_is_the_one_the_errata_names() -> None:
    """Mechel prints 1220 where his own Eq. (11) gives 145 for that row."""
    key, printed, expected = ref.MECHEL_3_WALL_IMPEDANCE_DEFECT
    low, high = _wall_impedance_band(key)

    assert low == pytest.approx(expected, abs=0.1)
    assert low == pytest.approx(high)
    assert printed / low == pytest.approx(8.4, abs=0.05)


@pytest.mark.parametrize(
    ("hopkins_key", "mechel_key", "hopkins_product", "mechel_product"),
    ref.MECHEL_AND_HOPKINS_SHARED_PRODUCT,
)
def test_two_books_agree_on_the_one_column_they_share_outright(
    hopkins_key: str,
    mechel_key: str,
    hopkins_product: float,
    mechel_product: float,
) -> None:
    """``h f_c`` needs no conversion, no Poisson ratio and no speed of sound.

    It is the cheapest cross-check there is between two books, and the reason
    both pages are worth holding: the steel rows agree to the digit, and the
    aluminium rows to six per cent.
    """
    assert HOPKINS[hopkins_key].thickness_critical_frequency_product_m_hz == (
        hopkins_product
    )
    assert MECHEL[mechel_key].thickness_critical_frequency_product_m_hz == (
        mechel_product
    )
    assert mechel_product / hopkins_product == pytest.approx(1.0, abs=0.06)


def test_the_impedance_oracle_covers_every_row_in_the_table() -> None:
    """A row the oracle does not list is a row nothing checks.

    The same hole opened twice: first in Cremer's attributions and then here,
    where the row missing from the oracle was the very one whose disagreement
    sets the tolerance. A parametrised test over an oracle checks the oracle,
    not the table, unless something holds the two together.
    """
    assert set(MECHEL) == {key for key, *_ in ref.MECHEL_3_PRINTED_WALL_IMPEDANCE}


# ---------------------------------------------------------------------------
# Bies Table C.1: a fourth book, and the one that prints the conversions
# ---------------------------------------------------------------------------
BIES = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "bies-2017-table-c1"
}


def test_the_three_fluids_of_the_page_are_not_in_a_solids_catalogue() -> None:
    """The table opens with air, fresh water and sea water. They are not solids.

    Their Poisson ratio of 0,5 is the page saying so: the closing note calls it
    effectively zero for liquids and gases and the 0,5 is the incompressible
    limit, which is a statement about a fluid and not about a solid.
    """
    assert [key for key in BIES if "water" in key or "air" in key] == []


@pytest.mark.parametrize(
    ("key", "modulus", "rho", "speed", "internal", "in_situ"), ref.BIES_C1_SPOT_ROWS
)
def test_each_bies_row_carries_the_printed_cells(
    key: str,
    modulus: float,
    rho: float,
    speed: float,
    internal: float,
    in_situ: float,
) -> None:
    """One row from each of the five groups the page prints in bold."""
    material = BIES[key]

    assert material.youngs_modulus_pa == modulus
    assert material.density_kg_m3 == rho
    assert material.bar_longitudinal_speed_m_s == speed
    assert material.loss_factor == internal
    assert material.in_situ_loss_factor == in_situ


def test_the_loss_factor_column_is_two_quantities_and_not_an_interval() -> None:
    """Footnote a says which end is which, so neither end is a bound on the other.

    Reading "0.0001-0.01" for steel as an interval of the internal loss factor
    would be a factor of a hundred, and it is the single most expensive way to
    misread this table. The low end is the material welded into an enclosure
    and the high end a panel installed in a building.
    """
    assert ref.BIES_C1_LOSS_FACTOR_IS_TWO_QUANTITIES
    steel = BIES["steel_mild"]

    assert steel.loss_factor == 0.0001
    assert steel.in_situ_loss_factor == 0.01
    assert "loss_factor" not in steel.ranges
    assert "in_situ_loss_factor" not in steel.ranges


def test_the_internal_end_lands_where_the_other_books_put_it() -> None:
    """Which is the evidence that the two ends are what footnote a says.

    Cremer measures steel's flexural loss factor between 0,2 and 3 times
    10^-4 and Mechel prints 1 times 10^-4. Bies' low end is 1 times 10^-4 and
    his high end a hundred times that, which is a mounting and not a material.
    """
    assert BIES["steel_mild"].loss_factor == MECHEL["steel"].loss_factor
    low, high = CREMER["steel"].ranges["flexural_loss_factor"]

    assert low <= BIES["steel_mild"].loss_factor <= high


@pytest.mark.parametrize("key", [row[0] for row in ref.BIES_C1_SPOT_ROWS])
def test_the_printed_speed_is_the_bar_speed(key: str) -> None:
    """The page calls column 4 "Speed of sound for a 1-D solid"."""
    material = BIES[key]
    assert material.youngs_modulus_pa is not None
    assert material.density_kg_m3 is not None

    closed_form = math.sqrt(material.youngs_modulus_pa / material.density_kg_m3)

    assert material.bar_longitudinal_speed_m_s == pytest.approx(
        closed_form, rel=ref.BIES_C1_SPEED_TOLERANCE
    )
    assert not material.is_derived("bar_longitudinal_speed_m_s")


@pytest.mark.parametrize(("key", "printed", "closed_form"), ref.BIES_C1_SPEED_DEFECTS)
def test_three_rows_do_not_follow_from_their_own_two_columns(
    key: str, printed: float, closed_form: float
) -> None:
    """The page says the column was calculated from the modulus and the density.

    For eighty-four of the eighty-seven rows that print both as single values
    it reproduces inside three per cent. These three do not, which is what
    makes them misprints rather than a looser method, and each says so in its
    own note.
    """
    material = BIES[key]
    assert material.youngs_modulus_pa is not None
    assert material.density_kg_m3 is not None

    assert material.bar_longitudinal_speed_m_s == printed
    assert math.sqrt(
        material.youngs_modulus_pa / material.density_kg_m3
    ) == pytest.approx(closed_form, abs=1.0)
    assert "docs/ERRATA.md" in material.note


def test_the_rest_of_the_table_reproduces_to_three_per_cent() -> None:
    """Without this, three disagreeing rows could be three of many."""
    off = []
    for key, row in BIES.items():
        speed = row.bar_longitudinal_speed_m_s
        modulus, rho = row.youngs_modulus_pa, row.density_kg_m3
        if speed is None or modulus is None or rho is None:
            continue
        if key in {defect[0] for defect in ref.BIES_C1_SPEED_DEFECTS}:
            continue
        off.append(abs(speed / math.sqrt(modulus / rho) - 1))

    assert len(off) == 84
    assert max(off) <= ref.BIES_C1_SPEED_TOLERANCE
    assert sum(1 for value in off if value <= 0.01) >= 79


def test_the_closing_note_of_the_table_is_an_oracle_for_four_conversions() -> None:
    """Printed page 721 gives all three speeds and the Poisson ratio at once.

    No other page in the catalogue does, and until now none of the four had
    this book behind it: the speeds were anchored on Hopkins, Cremer and
    Norton & Karczub, and ``nu = E/(2G) - 1`` on nothing printed at all.
    """
    modulus, density, nu = ref.BIES_CLOSING_NOTE_CASE

    bar = beam_longitudinal_speed(modulus, density_kg_m3=density)
    plate = plate_longitudinal_speed(modulus, density_kg_m3=density, poisson_ratio=nu)
    bulk = bulk_longitudinal_speed(modulus, density_kg_m3=density, poisson_ratio=nu)
    shear = modulus / (2.0 * (1.0 + nu))

    assert bar == pytest.approx(math.sqrt(modulus / density))
    assert plate == pytest.approx(math.sqrt(modulus / (density * (1.0 - nu**2))))
    assert bulk == pytest.approx(
        math.sqrt(modulus * (1.0 - nu) / (density * (1.0 + nu) * (1.0 - 2.0 * nu)))
    )
    assert modulus / (2.0 * shear) - 1.0 == pytest.approx(nu)


def test_a_cell_the_row_can_say_why_is_empty_is_never_filled_by_arithmetic() -> None:
    """The honeycomb rows print a modulus and a density and no speed.

    The arithmetic would run: 1,31 GPa over 72 kg/m3 gives 4 265 m/s. The page
    leaves the cell blank because a one-dimensional speed does not mean
    anything in a honeycomb, and its modulus and density are effective ones,
    so the number would be arithmetic standing in for a quantity that does not
    exist.
    """
    panels = [row for key, row in BIES.items() if key.startswith("aluminum_honeycomb")]

    assert len(panels) == 4
    for panel in panels:
        assert panel.youngs_modulus_pa is not None
        assert panel.density_kg_m3 is not None
        assert panel.bar_longitudinal_speed_m_s is None
        # The page prints nothing in that cell, so the row holds nothing in it
        # either; why a honeycomb has no one-dimensional speed is what the row
        # note is for.
        assert "bar_longitudinal_speed_m_s" not in panel.unquantified
        assert "honeycomb" in panel.note


def test_no_row_anywhere_is_both_derived_and_printed_as_a_range() -> None:
    """A field cannot be a number this library worked out and an interval the
    page gave.

    Bies prints a modulus of 18 to 30 GPa for normal concrete with a speed
    beside it, and the modulus worked back out of that speed used to sit next
    to the interval contradicting it.
    """
    clashes = [
        (key, field)
        for key, row in PUBLISHED_SOLIDS.items()
        for field in row.derived
        if field in row.ranges
    ]

    assert clashes == []


@pytest.mark.parametrize(("table", "size"), ref.SOLID_TABLE_SIZES)
def test_every_table_holds_the_rows_its_page_prints(table: str, size: int) -> None:
    """A row that goes missing must fail something.

    Nothing else here would notice. The parametrised tests only check the rows
    they name, and the statistical ones only the rows that reach them: of the
    hundred and five Bies rows, eighty-four reach the speed comparison, three
    the defect list and four the honeycomb test, so fourteen were covered by
    nothing at all.
    """
    assert sum(1 for row in PUBLISHED_SOLIDS.values() if row.table == table) == size


def test_the_catalogue_is_the_sum_of_its_tables() -> None:
    """And no table is in the catalogue that the oracle does not know about."""
    assert len(PUBLISHED_SOLIDS) == sum(size for _, size in ref.SOLID_TABLE_SIZES)
    assert {row.table for row in PUBLISHED_SOLIDS.values()} == {
        table for table, _ in ref.SOLID_TABLE_SIZES
    }


# ---------------------------------------------------------------------------
# Long Table 12.1 and Arau Table 4.1: two pages that qualify nothing
# ---------------------------------------------------------------------------
LONG = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "long-2014-table-12-1"
}
ARAU = {
    key.split("/", 1)[1]: row
    for key, row in PUBLISHED_SOLIDS.items()
    if row.table == "arau-1999-table-4-1"
}


def test_long_holds_its_speed_unqualified() -> None:
    """The column is headed "Speed of Longitudinal Waves" and nothing else.

    The page prints no modulus and no Poisson ratio, so there is nothing on it
    that could say which of the three waves it is. Putting 5050 m/s in
    ``bar_longitudinal_speed_m_s`` would be a guess with a decimal point on it,
    and it would then be compared against columns that were read rather than
    guessed.
    """
    steel = LONG["steel"]

    assert steel.longitudinal_speed_m_s == ref.LONG_STEEL_SPEED_M_S
    assert steel.bar_longitudinal_speed_m_s is None
    assert steel.plate_longitudinal_speed_m_s is None
    assert steel.bulk_longitudinal_speed_m_s is None


def test_what_long_would_be_if_it_were_a_plate_speed() -> None:
    """Which is the measurement behind calling the unqualified field a hint.

    Long's steel is below every plate speed the other tables hold, so it is
    almost certainly not one. Almost is why the field is unqualified.
    """
    plate_speeds = [
        row.plate_longitudinal_speed_m_s
        for row in PUBLISHED_SOLIDS.values()
        if row.name.lower().startswith("steel")
        and row.plate_longitudinal_speed_m_s is not None
    ]

    assert plate_speeds
    assert ref.LONG_STEEL_SPEED_M_S < min(plate_speeds)


def test_the_dotted_cells_keep_the_dots() -> None:
    """Nine rows print a row of dots where a speed would be.

    The cell keeps what the page printed, and the sentence about why there is
    no number is composed around it, so a reader of the row and a reader of
    the published table both see the page.
    """
    dotted = [
        key
        for key, row in LONG.items()
        if row.unquantified.get("longitudinal_speed_m_s") == ref.LONG_DOTTED_SPEED_CELL
    ]

    assert len(dotted) == ref.LONG_ROWS_WITHOUT_A_SPEED
    assert LONG[dotted[0]].why_missing("longitudinal_speed_m_s") == (
        f"the page prints \u201c{ref.LONG_DOTTED_SPEED_CELL}\u201d where the number would be"
    )


def test_a_cell_that_holds_words_instead_of_a_number() -> None:
    """One row's loss factor is the sentence "Varies with frequency"."""
    key, words = ref.LONG_UNQUANTIFIED_LOSS_FACTOR

    assert LONG[key].loss_factor is None
    assert LONG[key].unquantified["loss_factor"] == words
    assert LONG[key].why_missing("loss_factor") == (
        f"the page prints \u201c{words}\u201d where the number would be"
    )


def test_a_table_the_book_credits_whole_is_credited_whole() -> None:
    """Long prints the table under "(Beranek and Ver, 1992)"."""
    assert all(
        row.attributed_to == {"table": "Beranek and Ver, 1992"} for row in LONG.values()
    )


@pytest.mark.parametrize(("key", "printed_hz", "product"), ref.ARAU_4_1_PRODUCTS)
def test_arau_prints_the_frequency_of_a_one_centimetre_plate(
    key: str, printed_hz: float, product: float
) -> None:
    """So the product held here is that frequency times 0,01 m.

    A change of unit rather than a derivation, which is why it is not in
    ``derived``: the page gives the same quantity Hopkins does, per centimetre
    instead of per metre.
    """
    assert ARAU[key].thickness_critical_frequency_product_m_hz == product
    assert product == pytest.approx(printed_hz * 0.01)
    assert not ARAU[key].is_derived("thickness_critical_frequency_product_m_hz")


@pytest.mark.parametrize(
    ("arau_key", "hopkins_key", "arau_product", "hopkins_product"),
    ref.ARAU_AGAINST_HOPKINS,
)
def test_arau_against_hopkins_on_the_one_column_they_share(
    arau_key: str, hopkins_key: str, arau_product: float, hopkins_product: float
) -> None:
    """Three agree inside four per cent and the steel is nineteen apart.

    Nothing on Arau's page can settle the steel, because he prints no modulus
    and no speed, so this is a disagreement between books and not a defect of
    either. It is pinned here so the gap is a number somebody chose to keep
    rather than something nobody looked at.
    """
    assert ARAU[arau_key].thickness_critical_frequency_product_m_hz == arau_product
    assert (
        HOPKINS[hopkins_key].thickness_critical_frequency_product_m_hz
        == hopkins_product
    )
    gap = abs(arau_product / hopkins_product - 1)

    if arau_key == "acero":
        assert gap == pytest.approx(0.187, abs=0.002)
    else:
        assert gap == pytest.approx(0.0, abs=0.041)


def test_a_page_that_prints_one_material_twice_gets_two_rows() -> None:
    """Arau's glass carries one damping factor monolithic and another laminated."""
    assert ARAU["vidrio_monolitico"].loss_factor == 0.002
    assert ARAU["vidrio_laminar"].loss_factor == 0.02
    assert ARAU["vidrio_monolitico"].name == ARAU["vidrio_laminar"].name
