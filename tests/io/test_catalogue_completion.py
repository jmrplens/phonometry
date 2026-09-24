#  Copyright (c) 2026. Jose Manuel Requena Plens
"""One path completes a catalogue row: ``CatalogueRow.from_printed``.

A page prints the columns its author needed, and a row built from it holds
what follows from those columns as well: a modulus from a plate speed, an
area in square metres from the page's sabins. ``from_printed`` is the one
place that works anything out, the packaged loaders build every published
row through it, and ``Cls(...)`` stays literal. These tests hold it to that:
every published row is its own printed cells completed again, a value is
never filled over a cell that says something, a figure in another unit is
converted on its digits and rounded once, the text of a derived value names
the bases of the cells it rests on when they mix, and a row is edited
through ``printed_fields`` rather than ``dataclasses.replace``.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType

import catalogue_fingerprint
import numpy as np
import pytest

import phonometry
from phonometry import building, io, materials, solids
from phonometry._internal import catalogue as private
from phonometry.materials import AbsorptionAreaSpectrum, PorousMaterial
from phonometry.solids import SolidMaterial

_SOURCE = "Example Acoustics Ltd, Panel 40 technical data sheet, Rev. 4, p. 2"

#: A square foot in square metres, and a thousand cubic feet in cubic metres,
#: both exact since the 1959 definition of the yard.
_FOOT = Fraction("0.09290304")
_PER_VOLUME = _FOOT / Fraction("28.316846592")


def _published_rows() -> list[io.CatalogueRow]:
    """Every row of every published catalogue that is a catalogue row."""
    return [
        row
        for mapping in catalogue_fingerprint.published_mappings().values()
        for row in mapping.values()
        if isinstance(row, io.CatalogueRow)
    ]


PUBLISHED_ROWS = _published_rows()


# ---------------------------------------------------------------------------
# Parity: every published row is its printed cells, completed again
# ---------------------------------------------------------------------------
def test_every_published_row_is_its_printed_cells_completed_again() -> None:
    """``from_printed(**printed_fields())`` gives every published row back.

    The loaders build through ``from_printed``, so this is the round trip the
    design calls parity: what a row says the page printed, completed again,
    is the row, the converted and the carried cells included. That the
    loaders build what they built before, but for the four last digits and
    the ninety-five texts the fingerprint lists, is the next test's to say.
    """
    assert len(PUBLISHED_ROWS) > 1900
    derived = 0
    for row in PUBLISHED_ROWS:
        cells = row.printed_fields()
        assert type(row).from_printed(**cells) == row, f"{row.table}: {row.name}"
        derived += bool(row.derived)
    assert derived == 175


def _text(value: object) -> str:
    """A dumped cell as the fingerprint writes it, so a type change shows."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_the_loaders_build_what_they_built_before_but_the_listed_cells() -> None:
    """Through ``from_printed``, every packaged row is the row it was before.

    Before is the dump the literal constructors and the private completions
    of the solids and the porous materials built, which the fingerprint
    carries through its earlier steps. The cells that differ now are exactly
    the ones its two newest steps list: four last digits of Long Table 7.1,
    and the derived texts of the nineteen Hopkins rows whose estimated
    Poisson ratio they rest on. Nothing else of any row moved.
    """
    fp = catalogue_fingerprint
    before = fp.row_contract(fp.resilient_layer_row(fp.one_row_shape(fp.baseline())))
    live = fp.dump()
    assert sorted(live) == sorted(before)
    moved = {
        (name, key, field)
        for name, rows in before.items()
        for key, row in rows.items()
        for field in set(row) | set(live[name][key])
        if _text(row.get(field)) != _text(live[name][key].get(field))
    }
    listed = {
        ("PUBLISHED_ABSORPTION_AREAS", key, field) for key, field in fp.EXACT_CONVERSION
    } | {("PUBLISHED_SOLIDS", key, "derived") for key in fp.MIXED_BASIS_ROWS}
    assert moved == listed
    assert all(set(before[name]) == set(live[name]) for name in before)


def test_printed_fields_leaves_out_what_this_library_derived() -> None:
    steel = solids.PUBLISHED_SOLIDS["hopkins-2007-table-a2/steel"]
    cells = steel.printed_fields()
    assert "derived" not in cells
    assert steel.derived
    for name in steel.derived:
        assert name not in cells
    assert cells["plate_longitudinal_speed_m_s"] == steel.plate_longitudinal_speed_m_s
    assert cells["table"] == "hopkins-2007-table-a2"
    assert cells["name"] == steel.name
    assert cells["source"] == steel.source


def test_printed_fields_keeps_what_the_page_gives_in_another_unit_or_row() -> None:
    """A converted value and a carried one are the page's, and stay."""
    musician = materials.PUBLISHED_ABSORPTION_AREAS[
        "long-2014-table-7-1/musician_per_person_with_instrument"
    ]
    cells = musician.printed_fields()
    assert cells["absorption_area_500_m2"] == musician.absorption_area_500_m2
    assert cells["converted"] == musician.converted
    sheet = next(
        row for row in materials.PUBLISHED_FLOW_RESISTANCE.values() if row.carried
    )
    assert sheet.printed_fields()["carried"] == sheet.carried


def test_printed_fields_leaves_out_the_fields_that_hold_nothing() -> None:
    """An empty hedge, an empty text and a quantity the page left out."""
    row = SolidMaterial(name="Panel 40 core", source=_SOURCE, density_kg_m3=40.0)
    assert row.printed_fields() == {
        "name": "Panel 40 core",
        "source": _SOURCE,
        "density_kg_m3": 40.0,
    }


def test_printed_fields_keeps_a_flag_that_is_false() -> None:
    """``False`` is an answer the page gives, not a cell it left empty."""
    floor = next(
        row
        for row in building.PUBLISHED_IMPACT_INSULATION.values()
        if row.has_section_drawing is False
    )
    assert floor.printed_fields()["has_section_drawing"] is False


def test_printed_fields_keeps_a_text_left_empty_whose_default_says_something() -> None:
    """An area per nothing stated is not an area per person.

    ``per`` defaults to a person, so a row that leaves it empty has said
    something other than the default, and building it again without the
    empty text would make it an area per person without anyone noticing.
    """
    row = AbsorptionAreaSpectrum.from_printed(
        name="Chair", source=_SOURCE, per="", absorption_area_500_m2=0.4
    )
    cells = row.printed_fields()
    assert cells["per"] == ""
    again = AbsorptionAreaSpectrum.from_printed(**cells)
    assert again.per == ""
    assert again == row


def test_printed_fields_leaves_out_a_derived_the_caller_passed_literally() -> None:
    """A ``derived`` given to ``Cls(...)`` is the caller's, and is not printed.

    It goes with its value, like every derived one, so building again gives
    back what the class works out from the printed cells, which here is
    nothing.
    """
    row = SolidMaterial(
        name="Panel 40 core",
        source=_SOURCE,
        youngs_modulus_pa=1.0e9,
        derived={"youngs_modulus_pa": "the caller's own estimate"},
    )
    assert row.is_derived("youngs_modulus_pa")
    assert row.printed_fields() == {"name": "Panel 40 core", "source": _SOURCE}
    assert SolidMaterial.from_printed(**row.printed_fields()).youngs_modulus_pa is None


def test_printed_fields_is_a_new_dictionary_of_frozen_values() -> None:
    row = solids.PUBLISHED_SOLIDS["hopkins-2007-table-a2/aircrete"]
    first = row.printed_fields()
    first["density_kg_m3"] = 1.0
    assert "density_kg_m3" not in row.printed_fields()
    assert isinstance(row.printed_fields()["ranges"], MappingProxyType)
    assert isinstance(row.printed_fields()["basis"], MappingProxyType)


# ---------------------------------------------------------------------------
# The constructor stays literal; from_printed completes
# ---------------------------------------------------------------------------
_PLATE_CELLS = {
    "name": "Panel 40 core",
    "source": _SOURCE,
    "density_kg_m3": 2000.0,
    "plate_longitudinal_speed_m_s": 3000.0,
    "poisson_ratio": 0.2,
}


def test_the_constructor_works_nothing_out() -> None:
    row = SolidMaterial(**_PLATE_CELLS)
    assert row.youngs_modulus_pa is None
    assert row.bar_longitudinal_speed_m_s is None
    assert not row.derived


def test_from_printed_fills_what_follows_and_marks_it() -> None:
    row = SolidMaterial.from_printed(**_PLATE_CELLS)
    expected = solids.youngs_modulus_from_plate_speed(
        3000.0, density_kg_m3=2000.0, poisson_ratio=0.2
    )
    assert row.youngs_modulus_pa == expected
    assert row.derived["youngs_modulus_pa"] == (
        "from the plate speed, the density and the Poisson ratio"
    )
    assert set(row.derived) == {
        "youngs_modulus_pa",
        "shear_modulus_pa",
        "bar_longitudinal_speed_m_s",
        "bulk_longitudinal_speed_m_s",
        "transverse_speed_m_s",
        "thickness_critical_frequency_product_m_hz",
    }
    assert not row.is_derived("plate_longitudinal_speed_m_s")


def test_a_row_the_class_completes_nothing_of_is_the_literal_row() -> None:
    cells = {"name": "Panel 40", "source": _SOURCE, "absorption_coefficient_500": 0.8}
    row = materials.AbsorptionSpectrum.from_printed(**cells)
    assert row == materials.AbsorptionSpectrum(**cells)


def test_changing_a_cell_through_printed_fields_completes_it_again() -> None:
    """The documented edit: a new density moves the modulus that follows from it.

    ``dataclasses.replace`` copies the derived modulus as it was, beside a
    density it no longer follows from, which is why it is not the way.
    """
    steel = solids.PUBLISHED_SOLIDS["hopkins-2007-table-a2/steel"]
    cells = steel.printed_fields()
    cells["density_kg_m3"] = 7000.0
    edited = SolidMaterial.from_printed(**cells)
    assert edited.youngs_modulus_pa == solids.youngs_modulus_from_plate_speed(
        steel.plate_longitudinal_speed_m_s,
        density_kg_m3=7000.0,
        poisson_ratio=steel.poisson_ratio,
    )
    assert edited.youngs_modulus_pa != steel.youngs_modulus_pa

    stale = dataclasses.replace(steel, density_kg_m3=7000.0)
    assert stale.youngs_modulus_pa == steel.youngs_modulus_pa


def test_a_derived_passed_in_is_refused() -> None:
    cells = {**_PLATE_CELLS, "derived": {"youngs_modulus_pa": "guessed"}}
    with pytest.raises(io.CatalogueError, match="derived is what from_printed"):
        SolidMaterial.from_printed(**cells)


def test_every_cell_is_checked_before_any_arithmetic_reads_it() -> None:
    """A text where a density goes is the contract's refusal, not a crash."""
    cells = {**_PLATE_CELLS, "density_kg_m3": "2000"}
    with pytest.raises(io.CatalogueError, match="density_kg_m3"):
        SolidMaterial.from_printed(**cells)


def test_a_name_no_field_carries_is_refused_as_unknown() -> None:
    cells = {**_PLATE_CELLS, "densty_kg_m3": 2000.0}
    with pytest.raises(TypeError, match="densty_kg_m3"):
        SolidMaterial.from_printed(**cells)


@pytest.mark.parametrize(
    ("hedge", "entry"),
    [
        ("ranges", {"youngs_modulus_pa": (1.0e9, 2.0e9)}),
        ("reported", {"youngs_modulus_pa": (1.0e9, 2.0e9)}),
        ("unquantified", {"youngs_modulus_pa": "varies"}),
        ("not_derivable", {"youngs_modulus_pa": "an effective panel modulus"}),
        ("misprinted", {"youngs_modulus_pa": "the page prints 3 GPa, twice"}),
    ],
)
def test_nothing_is_filled_over_a_cell_the_row_says_something_about(
    hedge: str, entry: dict[str, object]
) -> None:
    row = SolidMaterial.from_printed(**_PLATE_CELLS, **{hedge: entry})
    assert row.youngs_modulus_pa is None
    assert not row.is_derived("youngs_modulus_pa")


def test_nothing_is_filled_over_a_printed_value() -> None:
    row = SolidMaterial.from_printed(**_PLATE_CELLS, youngs_modulus_pa=1.5e10)
    assert row.youngs_modulus_pa == 1.5e10
    assert not row.is_derived("youngs_modulus_pa")


def test_a_hedged_poisson_ratio_completes_no_porous_modulus() -> None:
    """Porous rows derive nothing from a Poisson ratio the page hedges."""
    row = PorousMaterial.from_printed(
        name="Panel 40 core",
        source=_SOURCE,
        youngs_modulus_pa=140000.0,
        poisson_ratio=0.3,
        ranges={"poisson_ratio": (0.2, 0.4)},
    )
    assert row.shear_modulus_pa is None


def test_the_poisson_ratio_follows_from_the_modulus_and_the_shear_modulus() -> None:
    """``nu = E / (2 G) - 1``: 200 GPa and 79 GPa give 200/158 - 1 = 21/79."""
    row = SolidMaterial.from_printed(
        name="Panel 40 core",
        source=_SOURCE,
        youngs_modulus_pa=2.0e11,
        shear_modulus_pa=7.9e10,
    )
    assert row.poisson_ratio == pytest.approx(21 / 79, rel=1e-14)
    assert row.is_derived("poisson_ratio")
    assert row.derived["poisson_ratio"] == "from the modulus and the shear modulus"


_NO_ISOTROPIC_SOLID = {
    "name": "Panel 40 core",
    "source": _SOURCE,
    "youngs_modulus_pa": 1.0e9,
    "shear_modulus_pa": 1.0e8,
}


@pytest.mark.parametrize("density", [None, 1000.0], ids=["alone", "with a density"])
def test_two_moduli_no_isotropic_solid_has_are_refused(density: float | None) -> None:
    """1 GPa and 0.1 GPa give a Poisson ratio of 4, which is no material's.

    Without a density nothing downstream would read it, and it would be
    stored as derived; with one, the plate speed would refuse it with a
    ``ValueError`` about a cell the caller never gave. Both are the row's
    refusal now, naming the two printed cells.
    """
    cells = {**_NO_ISOTROPIC_SOLID, "density_kg_m3": density}
    with pytest.raises(io.CatalogueError, match="poisson_ratio cannot be worked out"):
        SolidMaterial.from_printed(**cells)


def test_the_refusal_names_the_printed_cells_and_their_values() -> None:
    with pytest.raises(io.CatalogueError) as refusal:
        SolidMaterial.from_printed(**_NO_ISOTROPIC_SOLID)
    text = str(refusal.value)
    assert "youngs_modulus_pa = 1000000000.0" in text
    assert "shear_modulus_pa = 100000000.0" in text
    assert "not_derivable" in text


def test_not_derivable_keeps_the_arithmetic_from_running() -> None:
    """A row that says the two moduli do not give a ratio loads, without one."""
    row = SolidMaterial.from_printed(
        **_NO_ISOTROPIC_SOLID,
        density_kg_m3=1000.0,
        not_derivable={"poisson_ratio": "the two moduli are for different axes"},
    )
    assert row.poisson_ratio is None
    assert set(row.derived) == {"bar_longitudinal_speed_m_s", "transverse_speed_m_s"}


def test_a_printed_poisson_ratio_the_arithmetic_refuses_is_the_rows_refusal() -> None:
    """0.7 gives a plate speed and no bulk speed, and the row says which."""
    cells = {
        "name": "Panel 40 core",
        "source": _SOURCE,
        "youngs_modulus_pa": 2.0e10,
        "density_kg_m3": 2000.0,
        "poisson_ratio": 0.7,
    }
    with pytest.raises(
        io.CatalogueError, match="bulk_longitudinal_speed_m_s cannot be worked out"
    ):
        SolidMaterial.from_printed(**cells)


# ---------------------------------------------------------------------------
# The derived text names the bases when they mix
# ---------------------------------------------------------------------------
def test_the_derived_text_names_the_bases_of_the_cells_it_rests_on() -> None:
    """A calculated modulus and an estimated Poisson ratio give a shear modulus."""
    row = PorousMaterial.from_printed(
        name="Panel 40 core",
        source=_SOURCE,
        youngs_modulus_pa=140000.0,
        poisson_ratio=0.0,
        structural_loss_factor=0.1,
        basis={
            "row": "measured",
            "youngs_modulus_pa": "calculated",
            "poisson_ratio": "estimated",
        },
    )
    assert row.shear_modulus_pa == 70000.0
    assert row.derived["shear_modulus_pa"] == (
        "from the Young's modulus and the Poisson ratio; it rests on "
        "youngs_modulus_pa (calculated) and poisson_ratio (estimated)"
    )


def test_one_basis_for_every_cell_names_none() -> None:
    measured = PorousMaterial.from_printed(
        name="Panel 40 core",
        source=_SOURCE,
        youngs_modulus_pa=140000.0,
        poisson_ratio=0.0,
        basis={"row": "measured"},
    )
    assert measured.derived["shear_modulus_pa"] == (
        "from the Young's modulus and the Poisson ratio"
    )
    unstated = SolidMaterial.from_printed(**_PLATE_CELLS)
    assert ";" not in "".join(unstated.derived.values())


def test_a_value_rests_on_the_cells_of_the_values_it_was_worked_out_from() -> None:
    """A bar speed from a derived modulus rests on that modulus's estimate."""
    row = SolidMaterial.from_printed(
        **_PLATE_CELLS, basis={"poisson_ratio": "estimated"}
    )
    clause = (
        "; it rests on poisson_ratio (estimated) and on "
        "plate_longitudinal_speed_m_s and density_kg_m3, whose basis the source "
        "does not state"
    )
    assert row.derived["bar_longitudinal_speed_m_s"] == (
        f"from the modulus and the density{clause}"
    )
    assert row.derived["transverse_speed_m_s"] == (
        f"from the shear modulus and the density{clause}"
    )


def test_the_hopkins_estimates_are_named_in_every_value_they_feed() -> None:
    board = solids.PUBLISHED_SOLIDS["hopkins-2007-table-a2/plasterboard_natural_gypsum"]
    assert board.basis_of("poisson_ratio") == "estimated"
    for text in board.derived.values():
        assert text.endswith(catalogue_fingerprint.MIXED_BASIS_CLAUSE[2:])


_E = "youngs_modulus_pa"
_G = "shear_modulus_pa"
_NU = "poisson_ratio"
_RHO = "density_kg_m3"
_PLATE = "plate_longitudinal_speed_m_s"
_BAR = "bar_longitudinal_speed_m_s"
_ELASTIC = {_E: 2.0e10, _RHO: 2000.0, _NU: 0.2}

#: Every place a completion fills a value: the class, the cells printed, the
#: field filled and the printed cells it rests on, in the order the text
#: names them. Worked out by hand from the formulas each site applies.
_FILL_SITES = {
    "modulus from the plate speed": (
        SolidMaterial,
        {_PLATE: 3000.0, _RHO: 2000.0, _NU: 0.2},
        _E,
        (_PLATE, _RHO, _NU),
    ),
    "modulus from the bar speed": (
        SolidMaterial,
        {_BAR: 3000.0, _RHO: 2000.0},
        _E,
        (_BAR, _RHO),
    ),
    "Poisson ratio from the two moduli": (
        SolidMaterial,
        {_E: 2.0e11, _G: 7.9e10},
        _NU,
        (_E, _G),
    ),
    "shear modulus from the modulus": (
        SolidMaterial,
        {_E: 2.0e10, _NU: 0.2},
        _G,
        (_E, _NU),
    ),
    "bar speed": (SolidMaterial, {_E: 2.0e10, _RHO: 2000.0}, _BAR, (_E, _RHO)),
    "plate speed": (SolidMaterial, _ELASTIC, _PLATE, (_E, _RHO, _NU)),
    "bulk speed": (
        SolidMaterial,
        _ELASTIC,
        "bulk_longitudinal_speed_m_s",
        (_E, _RHO, _NU),
    ),
    "transverse speed": (
        SolidMaterial,
        {_G: 8.0e9, _RHO: 2000.0},
        "transverse_speed_m_s",
        (_G, _RHO),
    ),
    "h f_c from a derived plate speed": (
        SolidMaterial,
        _ELASTIC,
        "thickness_critical_frequency_product_m_hz",
        (_E, _RHO, _NU),
    ),
    "porous shear modulus": (
        PorousMaterial,
        {_E: 140000.0, _NU: 0.3},
        _G,
        (_E, _NU),
    ),
    "porous modulus": (PorousMaterial, {_G: 50000.0, _NU: 0.3}, _E, (_G, _NU)),
}


@pytest.mark.parametrize(
    ("site", "estimated"),
    [
        (site, cell)
        for site, (_, _, _, rests_on) in _FILL_SITES.items()
        for cell in rests_on
    ],
)
def test_every_fill_names_each_printed_cell_it_rests_on(
    site: str, estimated: str
) -> None:
    """One estimated input at a time, at every fill: the text names it.

    A fill that left one of its inputs out would leave that input's basis out
    of the text, and a value resting on an estimate would read as a figure
    of one kind.
    """
    cls, printed, filled, rests_on = _FILL_SITES[site]
    row = cls.from_printed(
        name="Panel 40 core",
        source=_SOURCE,
        basis={estimated: "estimated"},
        **printed,
    )
    others = " and ".join(cell for cell in rests_on if cell != estimated)
    assert row.derived[filled].endswith(
        f"; it rests on {estimated} (estimated) and on {others}, whose basis "
        "the source does not state"
    )


# ---------------------------------------------------------------------------
# A figure in another unit is converted on its digits and rounded once
# ---------------------------------------------------------------------------
def test_an_exact_conversion_rounds_once() -> None:
    """0.067 GPa is 67 000 000 Pa, which the float product misses."""
    giga = Fraction(10**9)
    assert private.convert_figure("0.067", giga) == 67000000.0
    assert 0.067 * 1e9 != 67000000.0


def test_the_float_product_misses_where_the_exact_one_does_not() -> None:
    """Of the figures a page prints to three decimals, some are inexact."""
    figures = [
        f"{whole}.{thousandths:03d}"
        for whole in range(20)
        for thousandths in range(1000)
    ]
    exact = [private.convert_figure(figure, _FOOT) for figure in figures]
    assert exact == [float(Fraction(Decimal(figure)) * _FOOT) for figure in figures]
    inexact = sum(
        float(figure) * float(_FOOT) != value
        for figure, value in zip(figures, exact, strict=True)
    )
    assert inexact > 0


def test_sabins_are_read_as_square_metres_and_the_figure_is_kept() -> None:
    row = AbsorptionAreaSpectrum.from_printed(
        name="Musician", source=_SOURCE, absorption_area_500_ft2=11.5
    )
    assert row.absorption_area_500_m2 == 1.06838496
    assert row.converted == {"absorption_area_500_m2": ("11.5", "sabins")}
    assert not row.is_derived("absorption_area_500_m2")
    assert not hasattr(row, "absorption_area_500_ft2")


@pytest.mark.parametrize(
    ("figure", "written"),
    [(Decimal("11.5"), "11.5"), (4, "4"), (np.float64(8.5), "8.5")],
)
def test_the_figure_is_kept_in_its_own_digits(figure: object, written: str) -> None:
    row = AbsorptionAreaSpectrum.from_printed(
        name="Musician", source=_SOURCE, absorption_area_125_ft2=figure
    )
    assert row.converted["absorption_area_125_m2"] == (written, "sabins")
    assert row.absorption_area_125_m2 == float(Fraction(written) * _FOOT)


def test_sabins_per_thousand_cubic_feet_need_what_they_are_per() -> None:
    row = AbsorptionAreaSpectrum.from_printed(
        name="Air",
        source=_SOURCE,
        per="cubic metre of air",
        absorption_area_2000_ft2_per_1000_ft3=2.3,
    )
    assert row.absorption_area_2000_m2 == 0.007545931758530184
    assert row.absorption_area_2000_m2 == float(Fraction("2.3") * _PER_VOLUME)
    assert row.converted["absorption_area_2000_m2"] == ("2.3", "sabins per 1000 ft3")
    with pytest.raises(io.CatalogueError, match="needs per written beside it"):
        AbsorptionAreaSpectrum.from_printed(
            name="Air", source=_SOURCE, absorption_area_2000_ft2_per_1000_ft3=2.3
        )


def test_a_cell_given_under_two_names_is_refused() -> None:
    cells = {
        "name": "Musician",
        "source": _SOURCE,
        "absorption_area_500_ft2": 11.5,
        "absorption_area_500_m2": 1.07,
    }
    with pytest.raises(io.CatalogueError, match="are one cell, given twice"):
        AbsorptionAreaSpectrum.from_printed(**cells)


def test_a_figure_left_empty_still_speaks_for_its_cell() -> None:
    """An empty figure under one alias and a figure under another are two answers."""
    cells = {
        "name": "Musician",
        "source": _SOURCE,
        "per": "seat",
        "absorption_area_500_ft2": None,
        "absorption_area_500_ft2_per_1000_ft3": 2.0,
    }
    with pytest.raises(io.CatalogueError, match="are one cell, given twice"):
        AbsorptionAreaSpectrum.from_printed(**cells)


@pytest.mark.parametrize("figure", [float("nan"), True, "11,5", Decimal("Infinity")])
def test_a_figure_that_is_not_a_finite_number_is_refused(figure: object) -> None:
    cells = {"name": "Musician", "source": _SOURCE, "absorption_area_500_ft2": figure}
    with pytest.raises(io.CatalogueError, match="absorption_area_500_ft2"):
        AbsorptionAreaSpectrum.from_printed(**cells)


def test_a_figure_the_page_leaves_empty_stays_empty() -> None:
    row = AbsorptionAreaSpectrum.from_printed(
        name="Musician", source=_SOURCE, absorption_area_500_ft2=None
    )
    assert row.absorption_area_500_m2 is None
    assert not row.converted


def test_the_constructor_takes_no_alias() -> None:
    """``Cls(...)`` is literal, and a figure in sabins is not one of its fields."""
    cells = {"name": "Musician", "source": _SOURCE, "absorption_area_500_ft2": 11.5}
    with pytest.raises(TypeError, match="absorption_area_500_ft2"):
        AbsorptionAreaSpectrum(**cells)


# ---------------------------------------------------------------------------
# Every packaged loader builds through the one path
# ---------------------------------------------------------------------------
def _loader_calls() -> list[tuple[str, ast.Call]]:
    """Every call in the package that builds a row from a data file's cells.

    A loader passes the citation of the file as ``source=`` and splats the
    row's cells, and nothing else in the package does both, so the pair finds
    every loader, however it names its function or its row.
    """
    root = pathlib.Path(phonometry.__file__).parent
    found: list[tuple[str, ast.Call]] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                names = {keyword.arg for keyword in node.keywords}
                if None in names and "source" in names:
                    found.append((path.relative_to(root).as_posix(), node))
    return found


def test_every_packaged_loader_builds_its_rows_through_from_printed() -> None:
    """No loader builds a row literally, so none can skip the completion.

    Twenty-two calls in twenty-one modules: every catalogue loader, with the
    absorption one building two classes from one file.
    """
    calls = _loader_calls()
    assert len(calls) == 22
    literal = [
        f"{where}:{call.lineno}"
        for where, call in calls
        if not (
            isinstance(call.func, ast.Attribute) and call.func.attr == "from_printed"
        )
    ]
    assert literal == []


def test_the_absorption_loader_still_chooses_the_row_type() -> None:
    """``_is_area`` is the loader's, because it picks between two classes."""
    from phonometry.materials.absorbers import measured

    assert measured._is_area({"absorption_area_125_ft2": 4.0})
    assert not measured._is_area({"absorption_coefficient_125": 0.4})
    assert not hasattr(measured, "_metric")
