#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The resistive facings, against a second reading of the two pages.

The catalogue and the oracle in :mod:`tests.reference_data.resistive_sheets`
were transcribed from the rendered pages by two readers who never saw each
other's work, and compared cell by cell before either was kept. These tests
keep that comparison alive, and add the things the transcription cannot say by
itself: that a column a page prints twice restates one value, which is what
identifies the two places where it does not; that the flow resistance of a
woven mesh rises as the weave closes; that the mass of a wire cloth follows
from its wire and its mesh; and that the eight cells TABLE 8.7 leaves blank
carry down the value of their own block and no other.
"""

from __future__ import annotations

import math

import pytest
import reference_data as ref

from phonometry import materials
from phonometry.materials.absorbers import (
    PUBLISHED_FLOW_RESISTANCE,
    PUBLISHED_POROUS,
    ResistiveSheet,
    resistive_sheet_named,
)

#: The three files this catalogue is read from, one per printed table, as the
#: keys spell them.
TABLE_8_5 = "ver-beranek-2006-table-8-5"
TABLE_8_6 = "ver-beranek-2006-table-8-6"
TABLE_8_7 = "ver-beranek-2006-table-8-7"
TABLES = (TABLE_8_5, TABLE_8_6, TABLE_8_7)

#: Kilograms per square metre in one pound per square foot, and grams per
#: square metre in one ounce per square yard, both exact by the definitions of
#: the pound, the ounce, the foot and the yard. Nothing on these pages is
#: converted by this library; these are what the pages' own two printings of
#: one quantity have to satisfy.
KG_M2_PER_LB_FT2 = 0.45359237 / 0.09290304
G_M2_PER_OZ_YD2 = 28.349523125 / 0.83612736
UM_PER_MIL = 25.4
MM_PER_INCH = 25.4
CM_PER_INCH = 2.54

#: How wide the two printings of one quantity may sit apart. The pages round
#: to two digits, and one of them rounds 0.3277 down to 0.32, which is 2.4 per
#: cent: a tighter window would be a test of the book's rounding rather than
#: of its arithmetic.
ROUNDING = 0.05

#: Density of the steel of a wire cloth, in kg/m3. Not from the page: the page
#: never says what the wire is made of, and the mass column is what says it.
STEEL_DENSITY_KG_M3 = 7800.0

#: How the oracle's SI columns map onto the fields of the row class. The US
#: customary half of each pair is checked against its SI twin instead, because
#: this catalogue does not hold it.
FIELDS_8_5 = {
    "Wires/cm": "wires_per_cm",
    "µm (10−6 m)": "wire_diameter_um",
    "kg/m2": "mass_per_area_kg_m2",
    "N · s/m3": "specific_flow_resistance_pa_s_m",
    "ρ0c0": "normalized_flow_resistance",
}
FIELDS_8_7 = {
    "ρ0c0": "normalized_flow_resistance",
    "N · s/m3": "specific_flow_resistance_pa_s_m",
    "NLF 500/20": "nonlinearity_factor",
    "mm": "thickness_mm",
    "kg/m2": "mass_per_area_kg_m2",
}


def _row(name: str) -> ResistiveSheet:
    return resistive_sheet_named(name)[0]


def _of(table: str) -> tuple[ResistiveSheet, ...]:
    return tuple(
        row for row in PUBLISHED_FLOW_RESISTANCE.values() if row.table == table
    )


def _cells(columns: tuple[str, ...], values: tuple[str, ...]) -> dict[str, str]:
    return dict(zip(columns, values, strict=True))


def _block_head(name: str, column: str) -> tuple[str, str]:
    """The row a blank cell of TABLE 8.7 inherits from, and what it prints.

    Read off the oracle rather than off the catalogue, so that a row carrying
    the value of the wrong block is a failure and not a tautology: the page
    prints the two resistance columns once per block, and the block a row
    belongs to is settled by the last printed cell above it.
    """
    head = printed = ""
    for row_name, values in ref.VER_BERANEK_8_7:
        cell = _cells(ref.VER_BERANEK_8_7_COLUMNS, values)[column]
        if cell:
            head, printed = row_name, cell
        if row_name == name:
            return head, printed
    raise AssertionError(name)


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_three_tables() -> None:
    assert len(PUBLISHED_FLOW_RESISTANCE) == 29
    assert len(ref.VER_BERANEK_8_5) == len(_of(TABLE_8_5)) == 5
    assert len(ref.VER_BERANEK_8_6) == len(_of(TABLE_8_6)) == 13
    assert len(ref.VER_BERANEK_8_7) == len(_of(TABLE_8_7)) == 11


def test_the_rows_are_in_the_order_the_pages_print_them() -> None:
    printed = [
        name
        for table in (ref.VER_BERANEK_8_5, ref.VER_BERANEK_8_6, ref.VER_BERANEK_8_7)
        for name, _values in table
    ]
    assert [row.name for row in PUBLISHED_FLOW_RESISTANCE.values()] == printed


@pytest.mark.parametrize(
    ("name", "values"),
    ref.VER_BERANEK_8_5,
    ids=[name for name, _v in ref.VER_BERANEK_8_5],
)
def test_every_wire_mesh_cell_is_the_printed_one(
    name: str, values: tuple[str, ...]
) -> None:
    """Cell by cell against the second reading, in the page's own SI columns."""
    row = _row(name)
    cells = _cells(ref.VER_BERANEK_8_5_COLUMNS, values)
    for column, field in FIELDS_8_5.items():
        held = getattr(row, field)
        assert held == pytest.approx(float(cells[column])), f"{name}.{field}"


@pytest.mark.parametrize(
    ("name", "values"),
    ref.VER_BERANEK_8_6,
    ids=[name for name, _v in ref.VER_BERANEK_8_6],
)
def test_every_glass_cloth_cell_is_the_printed_one(
    name: str, values: tuple[str, ...]
) -> None:
    """The surface density, the weave, the one number and the one bound.

    The surface density is held in grammes per square metre, which is the unit
    this table prints it in and not the kilogramme per square metre of the
    other two, so it is checked against the column that fills it.
    """
    row = _row(name)
    cells = _cells(ref.VER_BERANEK_8_6_COLUMNS, values)
    printed = cells["Flow Resistance, mks rayls (N · s/m3)"]
    if printed.startswith("<"):
        assert row.specific_flow_resistance_pa_s_m is None
        low, high = row.ranges["specific_flow_resistance_pa_s_m"]
        assert (low, high) == (0.0, float(printed.lstrip("<")))
        assert "specific_flow_resistance_pa_s_m" in row.bounded_above
    else:
        assert row.specific_flow_resistance_pa_s_m == pytest.approx(float(printed))
    assert row.surface_density_g_m2 == pytest.approx(float(cells["g/m2"]))
    assert row.mass_per_area_kg_m2 is None
    assert row.weave_construction == cells["Construction, Ends × Picks"]
    assert row.name == cells["Cloth Number"]


@pytest.mark.parametrize(
    ("name", "values"),
    ref.VER_BERANEK_8_7,
    ids=[name for name, _v in ref.VER_BERANEK_8_7],
)
def test_every_sintered_cell_is_the_printed_one_or_the_one_carried_down(
    name: str, values: tuple[str, ...]
) -> None:
    """A blank cell of the flow-resistance block is not empty in the row.

    The page prints the two resistance columns once per block and leaves them
    blank beneath, so a reading that stopped at the printed cell would hand
    back a row with no flow resistance at all for eight of the eleven sheets.
    What is checked here is not only that such a cell was filled: it is that
    it was filled with the value of its own block, from the row the sentence
    in ``carried`` names. Those eight values are the only numbers this
    catalogue holds that no reader read off their own cell.
    """
    row = _row(name)
    cells = _cells(ref.VER_BERANEK_8_7_COLUMNS, values)
    for column, field in FIELDS_8_7.items():
        printed = cells[column]
        if printed == "":
            head, carried = _block_head(name, column)
            assert field in row.carried, f"{name}.{field} lost its block value"
            assert not row.is_derived(field), f"{name}.{field}"
            assert getattr(row, field) == pytest.approx(float(carried)), (
                f"{name}.{field} carries the value of another block"
            )
            reason = row.carried[field]
            assert f"from the {head} row" in reason, f"{name}.{field}"
            assert f"prints {carried} " in reason, f"{name}.{field}"
            continue
        assert getattr(row, field) == pytest.approx(float(printed)), f"{name}.{field}"
    assert row.name == cells["Designation"]


# ---------------------------------------------------------------------------
# What the two printings of one quantity say about each other
# ---------------------------------------------------------------------------
def test_the_page_restates_three_wire_mesh_columns_in_the_other_units() -> None:
    """Three of the four quantities of TABLE 8.5 are printed in two systems of
    units, and both printings agree.

    The fourth pair is the flow resistance, printed in N s/m3 and again as a
    multiple of rho0 c0, which is not a restatement in other units and is what
    :meth:`ResistiveSheet.reference_impedance_pa_s_m` reads instead.

    Which is the whole argument of the erratum: on four of the five rows the
    mass in pounds per square foot is the mass in kilogrammes per square metre
    converted, and on the fifth it is ten times it. A test that only compared
    the catalogue against a second reader would pass with the defect in place,
    because both readers read the same wrong digits.
    """
    off = []
    for name, values in ref.VER_BERANEK_8_5:
        cells = _cells(ref.VER_BERANEK_8_5_COLUMNS, values)
        pairs = (
            (float(cells["Wires/cm"]), float(cells["Wires/in."]) / CM_PER_INCH),
            (
                float(cells["µm (10−6 m)"]),
                float(cells["mils (10−3 in.)"]) * UM_PER_MIL,
            ),
            (
                float(cells["kg/m2"]),
                float(cells["lb/ft2"]) * KG_M2_PER_LB_FT2,
            ),
        )
        off += [name for si, customary in pairs if abs(si / customary - 1.0) > ROUNDING]
    assert off == ["80"]


def test_the_misprinted_pound_cell_is_recorded_beside_the_mass_that_is_served() -> None:
    """The defective cell is the restatement, so the SI cell is still served.

    A catalogue that blanked the kilogramme cell as well would be refusing a
    number the page prints, that the column above it fits and that the weave
    of the mesh predicts. What the row refuses to do is pass the pound cell on
    in silence, and the note is where it says so: a ``misprinted`` hedge would
    have been keyed to a field that holds a number, where nothing reads it
    back, and the cell it belongs to is one this catalogue does not hold.
    """
    row = _row("80")
    assert row.mass_per_area_kg_m2 == pytest.approx(0.31)
    assert "0.63 lb/ft2" in row.note
    assert "ERRATA" in row.note
    assert not row.misprinted
    assert [r.name for r in _of(TABLE_8_5) if r.note] == ["80"]
    assert not any(row.misprinted for row in PUBLISHED_FLOW_RESISTANCE.values())


def test_the_glass_cloth_surface_density_is_one_wrong_factor_on_every_row() -> None:
    """Thirteen rows, thirteen disagreements, all the same size.

    An ounce per square yard is 33.906 grams per square metre to three
    decimals, and the table
    behaves as though it were about 30.5, which is what tells a systematic
    conversion apart from a scatter of slips. The page does not say which of
    the two columns carries the factor, so the row holds the one the page
    prints in SI and its note carries the other; if a later reader ever
    repairs one of the two columns, this is the test that will say so.
    """
    for name, values in ref.VER_BERANEK_8_6:
        cells = _cells(ref.VER_BERANEK_8_6_COLUMNS, values)
        factor = float(cells["g/m2"]) / float(cells["oz/yd2"])
        assert 30.0 < factor < 31.0, name
        assert factor < G_M2_PER_OZ_YD2 * (1.0 - ROUNDING), name
        row = _row(name)
        assert row.surface_density_g_m2 == pytest.approx(float(cells["g/m2"]))
        assert f"{cells['oz/yd2']} oz/yd2" in row.note, name
        assert "ERRATA" in row.note, name


def test_the_page_restates_the_sintered_thickness_and_mass_as_well() -> None:
    """The other table that restates a thickness and a mass, and it is
    consistent.

    Run beside the wire mesh test, this is what makes the single exception
    there an exception rather than the accuracy the book works to.
    """
    for name, values in ref.VER_BERANEK_8_7:
        cells = _cells(ref.VER_BERANEK_8_7_COLUMNS, values)
        assert float(cells["mm"]) / (
            float(cells["in."]) * MM_PER_INCH
        ) == pytest.approx(1.0, abs=ROUNDING), name
        assert float(cells["kg/m2"]) / (
            float(cells["lb/ft2"]) * KG_M2_PER_LB_FT2
        ) == pytest.approx(1.0, abs=ROUNDING), name


# ---------------------------------------------------------------------------
# What the physics of a woven cloth requires
# ---------------------------------------------------------------------------
def test_the_mass_of_a_wire_cloth_follows_from_its_wire_and_its_mesh() -> None:
    """A square weave of n wires per centimetre and diameter d weighs
    ``2 n rho pi d^2 / 4`` per unit area, and all five rows agree with it.

    Three columns are involved, so a digit dropped or transposed in any of
    them breaks it, which no comparison of two readings of the same page can
    do. It also settles the erratum from the other side: the row whose pound
    cell is misprinted is the row whose kilogramme cell this predicts to
    within three per cent, so the kilogramme cell is the one to keep.
    """
    for row in _of(TABLE_8_5):
        wires_per_m = row.wires_per_cm * 100.0
        diameter_m = row.wire_diameter_um * 1e-6
        area = math.pi * diameter_m**2 / 4.0
        woven = 2.0 * wires_per_m * STEEL_DENSITY_KG_M3 * area
        assert row.mass_per_area_kg_m2 == pytest.approx(woven, rel=0.06), row.name


def test_the_flow_resistance_of_a_mesh_rises_as_the_weave_closes() -> None:
    """More wires per centimetre, less open area, more resistance.

    The table is printed in order of mesh, so a transposed pair of rows would
    show up here and nowhere else in this file.
    """
    rows = _of(TABLE_8_5)
    counts = [row.wires_per_cm for row in rows]
    resistances = [row.specific_flow_resistance_pa_s_m for row in rows]
    assert counts == sorted(counts)
    assert resistances == sorted(resistances)
    assert [row.wire_diameter_um for row in rows] == sorted(
        (row.wire_diameter_um for row in rows), reverse=True
    )


def test_the_two_tables_do_not_normalize_by_the_same_impedance() -> None:
    """Each table divides by one impedance, and the two are not the same one.

    The sintered sheets are printed against 400 Pa s/m, give or take the
    rounding of the one block that divides to 397.7, and the wire meshes
    against something between 407 and 421: a thing about the book that no
    single row says and that a caller comparing the two normalized columns
    needs to know. It is also a check on four columns at once: any of them
    mistranscribed would move a row off its table's own constant.
    """
    meshes = [row.reference_impedance_pa_s_m() for row in _of(TABLE_8_5)]
    sintered = [row.reference_impedance_pa_s_m() for row in _of(TABLE_8_7)]
    assert all(405.0 < value < 425.0 for value in meshes)
    assert all(395.0 < value < 405.0 for value in sintered)
    assert min(meshes) > max(sintered)


def test_a_row_with_one_printed_resistance_column_refuses_the_impedance() -> None:
    row = _row("1044")
    with pytest.raises(ValueError, match="normalized_flow_resistance"):
        row.reference_impedance_pa_s_m()


# ---------------------------------------------------------------------------
# What the pages credit, and what they leave open
# ---------------------------------------------------------------------------
def test_the_cloth_table_credits_a_row_and_the_sintered_table_a_table() -> None:
    """One credit per row on one page, one credit over eleven rows on the other.

    TABLE 8.6 names a maker per row, by a code its footnote b resolves, so the
    credit belongs to the row. TABLE 8.7 names the Brunswick Corporation once,
    in its title and in its footnote a, over every row of the table and not
    beside any of them, so the credit belongs to the table and is keyed that
    way. TABLE 8.5 credits nobody, and saying so is the third of the point.
    """
    for row in _of(TABLE_8_6):
        assert set(row.attributed_to) == {"row"}, row.name
        assert row.name in row.attributed_to["row"], row.name
    credited = {row.attributed_to["table"] for row in _of(TABLE_8_7)}
    assert len(credited) == 1
    assert "Brunswick Corporation" in credited.pop()
    assert all(set(row.attributed_to) == {"table"} for row in _of(TABLE_8_7))
    assert all(not row.attributed_to for row in _of(TABLE_8_5))


def test_the_measurement_conditions_the_pages_print_reach_their_rows() -> None:
    """Two conditions on three pages, and neither is left in the prose.

    The resistance of a facing follows the viscosity of the air, so the air
    temperature TABLE 8.7 prints in its column spanner is not decoration; and
    a surface density averaged over a large sample is not a measurement of the
    sample in hand. Both are printed once, over a whole table, and both are on
    every row of the table they cover.
    """
    assert all("70°F" in row.note for row in _of(TABLE_8_7))
    assert all("Averaged over a large sample" in row.note for row in _of(TABLE_8_6))


def test_the_only_bound_on_the_pages_is_not_served_as_a_value() -> None:
    row = _row("1562")
    assert row.specific_flow_resistance_pa_s_m is None
    assert "upper bound of 5" in row.why_missing("specific_flow_resistance_pa_s_m")
    with pytest.raises(ValueError, match="upper bound"):
        row.printed("specific_flow_resistance_pa_s_m")


def test_the_carried_down_cells_name_the_row_they_came_from() -> None:
    """Eight rows inherit, and each of them says which row it inherited from."""
    carried = [
        row
        for row in _of(TABLE_8_7)
        if "specific_flow_resistance_pa_s_m" in row.carried
    ]
    assert len(carried) == 8
    heads = {
        row.carried["specific_flow_resistance_pa_s_m"].split(" row")[0]
        for row in carried
    }
    assert heads == {
        "carried down the blank cells of TABLE 8.7 from the FM 125",
        "carried down the blank cells of TABLE 8.7 from the FM 122",
    }
    assert all(
        row.specific_flow_resistance_pa_s_m is not None for row in _of(TABLE_8_7)
    )


# ---------------------------------------------------------------------------
# The shape of the catalogue
# ---------------------------------------------------------------------------
def test_a_resistance_is_not_a_resistivity() -> None:
    """The two catalogues hold two quantities and share no field name.

    A facing of 24.6 Pa s/m and a bulk absorber of 24.6 Pa s/m2 differ by a
    thickness, and the only thing standing between them is that the two row
    classes spell their quantity differently. A rename that collapsed them
    would pass every other test in this file.
    """
    sheet = _row("80")
    porous = next(iter(PUBLISHED_POROUS.values()))
    assert hasattr(sheet, "specific_flow_resistance_pa_s_m")
    assert not hasattr(sheet, "flow_resistivity_pa_s_m2")
    assert hasattr(porous, "flow_resistivity_pa_s_m2")
    assert not hasattr(porous, "specific_flow_resistance_pa_s_m")


def test_the_lookup_matches_a_whole_name_only() -> None:
    assert len(resistive_sheet_named("12")) == 1
    assert resistive_sheet_named("12")[0].table == TABLE_8_5
    assert resistive_sheet_named("fm 122") == resistive_sheet_named("FM 122")
    assert resistive_sheet_named("FM") == ()


def test_the_catalogue_is_reachable_from_the_package() -> None:
    assert materials.PUBLISHED_FLOW_RESISTANCE is PUBLISHED_FLOW_RESISTANCE
    assert all(
        key.startswith(f"{row.table}/") and row.table in TABLES
        for key, row in PUBLISHED_FLOW_RESISTANCE.items()
    )


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_FLOW_RESISTANCE["x/y"] = ResistiveSheet(name="x", source="nowhere")  # type: ignore[index]


def test_every_row_says_which_printed_table_it_came_from() -> None:
    """One file per printed table, so a key and a citation name one table.

    The three tables print one quantity between them and were read from one
    pair of facing pages, which is what a single file would have been an
    argument for; what it would have cost is this. A row of TABLE 8.6 would
    have carried a citation naming three tables and two pages, two of which
    are not where it was read, and its key would have named a file rather
    than a table.
    """
    for table, printed, folio in (
        (TABLE_8_5, "TABLE 8.5", "printed p. 262"),
        (TABLE_8_6, "TABLE 8.6", "printed p. 263"),
        (TABLE_8_7, "TABLE 8.7", "printed p. 263"),
    ):
        rows = _of(table)
        assert rows, table
        for row in rows:
            assert row.source.count("PDF page") == 1, row.name
            assert printed in row.source, row.name
            assert folio in row.source, row.name
    assert {row.source for row in PUBLISHED_FLOW_RESISTANCE.values()} == {
        _of(table)[0].source for table in TABLES
    }
