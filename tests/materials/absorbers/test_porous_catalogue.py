#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published porous specimens, against the pages they were read from.

A catalogue is only worth what its provenance is worth, so most of these tests
are about what the page said rather than what the numbers are. Allard and
Atalla print their parameter tables in whatever units the chapter needed:
millimetres in one, metres in another, micrometres everywhere else; a complex
shear modulus in N/cm2 here and a Young's modulus in pascals there; and one
row that prints the word "model" in three cells because the quantity is
frequency dependent. All of it has to survive into the library, because a
caller who reads a 0,12 as micrometres is out by a factor of a thousand and
nothing downstream will tell them.

The printed digits live once, in ``tests/reference_data``, with every
conversion written into the literal. These assertions are what makes the two
representations one copy.
"""

from __future__ import annotations

import inspect
import pathlib
import re

import numpy as np
import pytest
import reference_data as ref

import phonometry
from phonometry.materials.absorbers import (
    PUBLISHED_POROUS,
    PorousMaterial,
    delany_bazley,
    johnson_champoux_allard,
    miki,
    porous_materials_named,
)

#: How ``check_published_sources`` splits a citation that names several pages:
#: after a closing parenthesis, because the spelling for a page with no folio
#: reads "(no printed folio; between folios A and B)" and a bare "; " would cut
#: it in half.
_CITATION_JOINER = re.compile(r"(?<=\)); ")

#: The rows the oracle holds, by key, for the per-row tests.
_ORACLE = dict(ref.ALLARD_POROUS_ROWS)


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
def test_every_row_of_every_table_is_in_the_oracle() -> None:
    """Both directions: no row unchecked, no oracle entry without a row."""
    assert set(PUBLISHED_POROUS) == set(_ORACLE)


@pytest.mark.parametrize(("key", "printed"), ref.ALLARD_POROUS_ROWS)
def test_each_row_carries_the_printed_cells(
    key: str, printed: dict[str, float]
) -> None:
    """Every cell of every row, against a second reading of the same page.

    The oracle writes each conversion into its literal, so a value that
    matches here matches the printed digit **and** the factor: Table 9.1's
    ``0.12`` millimetres is 120 micrometres or the transcription is wrong.
    """
    row = PUBLISHED_POROUS[key]
    for field, value in printed.items():
        assert getattr(row, field) == pytest.approx(value, rel=1e-12), field


@pytest.mark.parametrize("key", list(_ORACLE))
def test_no_row_holds_a_cell_its_page_does_not_print(key: str) -> None:
    """The other direction: a quantity absent from the oracle is ``None``.

    A test that only checks the cells the oracle lists would pass a row that
    had grown a tortuosity nobody printed, which is the failure mode a
    parameter catalogue has to be proof against.
    """
    row = PUBLISHED_POROUS[key]
    printed = _ORACLE[key]
    quantities = [
        name
        for name, annotation in PorousMaterial.__annotations__.items()
        if "float" in str(annotation)
    ]
    for field in quantities:
        if field in printed or row.is_derived(field):
            continue
        assert getattr(row, field) is None, field


def test_every_table_holds_the_rows_its_page_prints() -> None:
    """Row counts per table, so a dropped row cannot pass unnoticed."""
    counted: dict[str, int] = {}
    for row in PUBLISHED_POROUS.values():
        counted[row.table] = counted.get(row.table, 0) + 1
    assert counted == {
        "allard-2009-table-6-1": 1,
        "allard-2009-table-7-1": 2,
        "allard-2009-table-8-1": 2,
        "allard-2009-table-9-1": 2,
        "allard-2009-table-10-1": 2,
        "allard-2009-table-11-2": 1,
        "allard-2009-table-11-3": 2,
        "allard-2009-table-11-4": 4,
        "allard-2009-table-11-5": 3,
        "allard-2009-table-11-6": 1,
        "allard-2009-table-11-7": 3,
        "allard-2009-table-11-8": 1,
        "allard-2009-table-11-9": 1,
        "allard-2009-table-12-1": 1,
        "allard-2009-table-12-2": 1,
        "allard-2009-table-12-4": 1,
        "allard-2009-table-12-5": 2,
        "allard-2009-table-13-1": 1,
        "allard-2009-table-13-2": 1,
    }


def test_every_row_cites_a_document_a_page_and_a_folio() -> None:
    """Read the citations the way the provenance gate reads them."""
    for key, row in PUBLISHED_POROUS.items():
        for citation in _CITATION_JOINER.split(row.source):
            assert citation.startswith("Allard & Atalla 2e "), key
            assert "PDF page " in citation, key
            assert "(printed p. " in citation, key


def test_the_one_specimen_that_takes_two_pages_names_both() -> None:
    """Table 6.1 prints no characteristic length and Sect. 6.5.4 does.

    A fibre diameter of 12 um gives, through the book's Eqs. (5.29) and
    (5.30), the two lengths the equivalent fluid needs, and they are on the
    facing folio rather than in the table. The row would be citing a page that
    does not carry half its cells if the citation named the table alone.
    """
    row = PUBLISHED_POROUS["allard-2009-table-6-1/domisol_coffrage"]
    assert "Table 6.1, PDF page 133 (printed p. 124)" in row.source
    assert "Sect. 6.5.4, PDF page 132 (printed p. 123)" in row.source
    assert row.viscous_length_um / 1e6 == pytest.approx(
        ref.ALLARD_SECT_6_5_4_VISCOUS_LENGTH_M, rel=1e-12
    )
    assert row.thermal_length_um / 1e6 == pytest.approx(
        ref.ALLARD_SECT_6_5_4_THERMAL_LENGTH_M, rel=1e-12
    )


# ---------------------------------------------------------------------------
# What the pages say about each other
# ---------------------------------------------------------------------------
def test_the_two_pages_that_print_the_glass_wool_describe_one_specimen() -> None:
    """Folio 275 repeats folio 124, and its ``E`` is folio 124's ``N``.

    Table 11.8 prints a Young's modulus and a Poisson ratio where Table 6.1
    prints a complex shear modulus. ``N = E/(2(1 + nu))`` with the printed
    loss factor as the imaginary part reproduces the Table 6.1 cell, which is
    what licenses reading the two tables as one material, and is also the one
    arithmetic check available on a page that prints no wave speed.
    """
    table_6_1 = PUBLISHED_POROUS["allard-2009-table-6-1/domisol_coffrage"]
    table_11_8 = PUBLISHED_POROUS["allard-2009-table-11-8/glass_wool"]
    for field in (
        "porosity",
        "tortuosity",
        "flow_resistivity_pa_s_m2",
        "frame_density_kg_m3",
        "viscous_length_um",
        "thermal_length_um",
        "poisson_ratio",
        "structural_loss_factor",
    ):
        assert getattr(table_6_1, field) == getattr(table_11_8, field), field
    assert table_6_1.frame_constants() == table_11_8.frame_constants()


def test_the_thermal_length_of_the_glass_wool_is_the_one_both_pages_print() -> None:
    """110 and not 112, which is what ``Lambda' = 2 Lambda`` would give.

    Sect. 6.5.4 rounds 1,12e-4 m to 1,1e-4 in its own print, and Table 11.8
    prints 110 um independently. Two pages agreeing on the rounded value is
    what settles it; deriving the length from the viscous one would put a
    number in the catalogue that neither page has.
    """
    row = PUBLISHED_POROUS["allard-2009-table-6-1/domisol_coffrage"]
    assert row.thermal_length_um == 110.0
    assert row.thermal_length_um != 2.0 * row.viscous_length_um
    assert not row.is_derived("thermal_length_um")


@pytest.mark.parametrize(
    "keys",
    [
        (
            "allard-2009-table-11-5/foam_3",
            "allard-2009-table-12-1/foam_1",
            "allard-2009-table-12-4/limp_foam",
            "allard-2009-table-12-5/foam",
        ),
        ("allard-2009-table-11-7/carpet_1", "allard-2009-table-11-7/carpet_2"),
    ],
)
def test_one_specimen_printed_on_several_pages_agrees_with_itself(
    keys: tuple[str, ...],
) -> None:
    """The book reuses a foam across four chapters, and the cells match.

    This is the cheapest check there is on a transcription made table by
    table: the same five numbers had to be read four times, off four pages,
    and a slipped digit shows up here without any page having to be read
    again. The elastic constants are not compared, because two of the four
    pages print none: the limp examples do not need them.
    """
    rows = [PUBLISHED_POROUS[key] for key in keys]
    for field in (
        "porosity",
        "flow_resistivity_pa_s_m2",
        "tortuosity",
        "viscous_length_um",
        "thermal_length_um",
        "frame_density_kg_m3",
    ):
        values = {getattr(row, field) for row in rows}
        assert len(values) == 1, (field, values)


def test_the_two_directions_of_the_anisotropic_glass_wool_are_two_rows() -> None:
    """Table 10.1 prints one material with two flow resistivities.

    The equivalent-fluid models here are isotropic and take one of each, so a
    row that held both would have to invent a rule for which one the model
    gets. Two rows, each a direction, leaves the choice with the caller and
    the page's own word, ``variant``, saying what it is.
    """
    x = PUBLISHED_POROUS["allard-2009-table-10-1/glass_wool_x"]
    z = PUBLISHED_POROUS["allard-2009-table-10-1/glass_wool_z"]
    assert x.name == z.name
    assert (x.variant, z.variant) == ("direction x", "direction z")
    assert (x.flow_resistivity_pa_s_m2, z.flow_resistivity_pa_s_m2) == (4000.0, 8000.0)
    assert (x.viscous_length_um, z.viscous_length_um) == (200.0, 140.0)
    assert x.thermal_length_um == z.thermal_length_um


# ---------------------------------------------------------------------------
# The hedges the pages print
# ---------------------------------------------------------------------------
def test_a_cell_that_prints_a_word_keeps_the_word() -> None:
    """Table 11.5 prints "model" in three cells of its screen row.

    The prose on the facing folio explains why: the screen's lengths were
    derived from its measured flow resistance and its tortuosity taken as a
    frequency-dependent expression, so no single number stands for either. A
    float there would be a tortuosity nobody published.
    """
    row = PUBLISHED_POROUS["allard-2009-table-11-5/screen_2"]
    for field in ("tortuosity", "viscous_length_um", "thermal_length_um"):
        assert getattr(row, field) is None, field
        assert row.why_missing(field) == "model", field


def test_a_thickness_the_page_calls_variable_is_not_a_number() -> None:
    """Table 12.1 sweeps the foam thickness and prints the word."""
    row = PUBLISHED_POROUS["allard-2009-table-12-1/foam_1"]
    assert row.thickness_mm is None
    assert row.why_missing("thickness_mm") == "variable"


def test_a_cell_the_page_leaves_empty_says_so_differently() -> None:
    """An empty cell and a cell holding a word are two different answers."""
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    assert row.youngs_modulus_pa is None
    assert row.why_missing("youngs_modulus_pa") == (
        "the page does not give it, and it does not follow from the cells that it does"
    )


# ---------------------------------------------------------------------------
# What the library derives, and what it refuses to
# ---------------------------------------------------------------------------
def test_the_modulus_that_follows_from_the_other_two_is_marked_derived() -> None:
    """A page prints ``N`` or ``E``; the catalogue answers both, and says so."""
    printed_shear = PUBLISHED_POROUS["allard-2009-table-8-1/material_1"]
    assert printed_shear.is_derived("youngs_modulus_pa")
    assert not printed_shear.is_derived("shear_modulus_pa")
    assert printed_shear.youngs_modulus_pa == pytest.approx(
        2.0 * 75.0e3 * (1.0 + 0.3), rel=1e-12
    )

    printed_young = PUBLISHED_POROUS["allard-2009-table-11-6/foam"]
    assert printed_young.is_derived("shear_modulus_pa")
    assert not printed_young.is_derived("youngs_modulus_pa")
    assert printed_young.shear_modulus_pa == pytest.approx(
        294.0e3 / (2.0 * (1.0 + 0.2)), rel=1e-12
    )


def test_nothing_is_derived_without_a_poisson_ratio() -> None:
    """Two constants are three only when the third is printed.

    Table 11.5's felt prints neither modulus and no Poisson ratio, and a
    catalogue that reached for a nominal 0,3 would be publishing a modulus the
    book does not have.
    """
    row = PUBLISHED_POROUS["allard-2009-table-11-5/felt_1"]
    assert row.poisson_ratio is None
    assert row.youngs_modulus_pa is None
    assert row.shear_modulus_pa is None
    assert not row.derived


def test_the_complex_shear_modulus_is_rebuilt_from_the_two_stored_fields() -> None:
    """``N(1 + j eta)`` goes in as two reals and comes back as one complex."""
    row = PUBLISHED_POROUS["allard-2009-table-8-1/material_2"]
    shear, poisson = row.frame_constants()
    assert shear == pytest.approx(complex(80.0e3, 12.0e3), rel=1e-12)
    assert poisson == 0.44


def test_frame_constants_refuses_a_specimen_published_without_them() -> None:
    """Table 11.2 prints no elastic constants, and the object says so."""
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    with pytest.raises(ValueError, match=r"published without frame elastic"):
        row.frame_constants()


def test_a_row_whose_page_prints_no_loss_factor_is_not_given_one() -> None:
    """Table 11.3's foam prints ``eta_s``; Table 12.4's limp foam does not.

    ``frame_constants`` reads a missing loss factor as zero, which is the
    lossless frame, not a guess at a typical value. The field stays ``None``
    so a caller can tell the two apart.
    """
    row = PUBLISHED_POROUS["allard-2009-table-12-4/limp_foam"]
    assert row.structural_loss_factor is None


# ---------------------------------------------------------------------------
# medium()
# ---------------------------------------------------------------------------
def test_medium_is_the_model_called_with_the_stored_parameters() -> None:
    """``medium()`` converts the lengths and dispatches, and does no more."""
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    f = np.array([125.0, 500.0, 2000.0])
    direct = johnson_champoux_allard(
        f,
        row.flow_resistivity_pa_s_m2,
        porosity=row.porosity,
        tortuosity=row.tortuosity,
        viscous_length=row.viscous_length_um / 1e6,
        thermal_length=row.thermal_length_um / 1e6,
    )
    np.testing.assert_array_equal(
        row.medium(f).characteristic_impedance,
        direct.characteristic_impedance,
    )


@pytest.mark.filterwarnings("ignore::phonometry.PhonometryWarning")
def test_medium_dispatches_to_the_one_parameter_models() -> None:
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    f = np.array([500.0])
    assert row.medium(f, model="miki").model == "miki"
    assert row.medium(f, model="delany_bazley").model == "delany_bazley[delany_bazley]"


def test_medium_rejects_an_unknown_model() -> None:
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    with pytest.raises(ValueError, match=r"'model' must be one of"):
        row.medium(np.array([500.0]), model="biot")


def test_medium_refuses_a_row_whose_page_left_the_parameter_out() -> None:
    """And the refusal says which cell, what the page had there, and where.

    The screen of Table 11.5 has a flow resistivity and three cells that read
    "model", so the one-parameter models work on it and the five-parameter one
    cannot. Failing here beats a ``TypeError`` about ``None`` four frames down
    inside the model.
    """
    row = PUBLISHED_POROUS["allard-2009-table-11-5/screen_2"]
    f = np.array([500.0])
    with pytest.raises(ValueError, match=r"has no tortuosity.*model.*Table 11\.5"):
        row.medium(f)
    with pytest.warns(phonometry.PhonometryWarning):
        assert row.medium(f, model="miki").model == "miki"


def test_a_row_with_no_flow_resistivity_refuses_every_model() -> None:
    """Every model in this package starts from ``sigma``.

    No row of these nineteen tables is missing one, so this asserts the
    refusal on a row built for the purpose rather than on the catalogue.
    """
    row = PorousMaterial(name="Nothing", source="nowhere", porosity=0.98)
    for model in ("johnson_champoux_allard", "delany_bazley", "miki"):
        with pytest.raises(ValueError, match=r"has no flow_resistivity_pa_s_m2"):
            row.medium(np.array([500.0]), model=model)


# ---------------------------------------------------------------------------
# The lookup
# ---------------------------------------------------------------------------
def test_a_name_several_tables_print_comes_back_several_times() -> None:
    """Five pages print a "Foam" and they are five different foams."""
    foams = porous_materials_named("Foam")
    assert len(foams) == 5
    assert len({row.flow_resistivity_pa_s_m2 for row in foams}) > 1
    assert [row.table for row in foams] == sorted({row.table for row in foams})


def test_the_lookup_ignores_case_and_answers_nothing_for_an_unknown_name() -> None:
    assert porous_materials_named("foam") == porous_materials_named("Foam")
    assert porous_materials_named("granite") == ()


# ---------------------------------------------------------------------------
# The catalogue as an object
# ---------------------------------------------------------------------------
def test_the_table_itself_cannot_be_edited() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"] = PorousMaterial(  # type: ignore[index]
            name="x", source="y"
        )


def test_the_mappings_inside_a_row_cannot_be_edited() -> None:
    """``frozen=True`` protects the fields, not what they point at."""
    row = PUBLISHED_POROUS["allard-2009-table-11-5/screen_2"]
    with pytest.raises(TypeError):
        row.unquantified["tortuosity"] = "1.0"  # type: ignore[index]
    with pytest.raises(TypeError):
        row.derived["youngs_modulus_pa"] = "guessed"  # type: ignore[index]


def test_a_row_cannot_be_edited() -> None:
    row = PUBLISHED_POROUS["allard-2009-table-11-2/soft_fibrous"]
    with pytest.raises(AttributeError):
        row.porosity = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# The removal policy
# ---------------------------------------------------------------------------
def test_no_model_defaults_to_a_published_specimen() -> None:
    """Withdrawing the catalogue costs no capability.

    Every model keeps its parameters as explicit arguments, so nothing in the
    library reads these tables and deleting them would break no call that does
    not name one.
    """
    for function in (johnson_champoux_allard, delany_bazley, miki):
        defaults = [
            parameter.default
            for parameter in inspect.signature(function).parameters.values()
            if parameter.default is not inspect.Parameter.empty
        ]
        assert not any(isinstance(default, PorousMaterial) for default in defaults), (
            function.__name__
        )


def test_nothing_in_the_library_reads_the_published_tables() -> None:
    """No module of ``src`` reads the catalogue except where it is defined."""
    root = pathlib.Path(phonometry.__file__).parent
    readers = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if "PUBLISHED_POROUS" in path.read_text(encoding="utf-8")
    ]
    assert sorted(readers) == [
        "materials/__init__.py",
        "materials/absorbers/__init__.py",
        "materials/absorbers/catalogue.py",
    ]


@pytest.mark.parametrize(
    ("hedge", "cell"),
    [
        ("ranges", {"youngs_modulus_pa": [1.0e5, 3.0e5]}),
        ("unquantified", {"youngs_modulus_pa": "varies with temperature"}),
        ("reported", {"youngs_modulus_pa": [1.0e5, 3.0e5]}),
    ],
)
def test_arithmetic_never_fills_a_cell_the_row_can_speak_for(
    hedge: str, cell: dict[str, object]
) -> None:
    """A modulus the page printed as an interval is not a missing modulus.

    Deriving a scalar from the other two constants would put it beside the
    interval contradicting it: the field would say one number and the row
    would say the book gave none. No table in this catalogue prints a modulus
    that way yet, so this is asserted on a row built for it.
    """
    from phonometry.materials.absorbers.catalogue import _complete

    filled = _complete(
        {
            "name": "Hedged",
            "shear_modulus_pa": 1.0e5,
            "poisson_ratio": 0.3,
            hedge: cell,
        }
    )
    assert "youngs_modulus_pa" not in filled
    assert not filled.get("derived")
