#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Eleven insulation tables against a second reading of their pages.

Seven tables of Harris 3e Chapter 31 and Rossing's Table 11.4 reach the
transmission loss catalogue; Tables 19.2 to 19.4 of Harris (1977) reach the
impact catalogue. The oracle in :mod:`tests.reference_data.wave4_building`
holds each cell as the page prints it, and these tests read every one of them
back out of the catalogue. They also pin the shape each table was given: a
column is a variant, a blank cell is no row, the window table is turned, a
door pair serves no surface density, and a floor printed twice is told apart
by its load.
"""

from __future__ import annotations

import math
import re

import pytest
import reference_data as ref

from phonometry.building import (
    PUBLISHED_IMPACT_INSULATION,
    PUBLISHED_TRANSMISSION_LOSS,
    TRANSMISSION_LOSS_BANDS_HZ,
    ImpactInsulation,
    TransmissionLossSpectrum,
)

STC = "sound_transmission_class"

#: One technical atmosphere, the kg/cm2 the 1977 page prints its load in.
TECHNICAL_ATMOSPHERE_PA = 98066.5


def _num(cell: str) -> float:
    """A printed number, with the decimal comma the Spanish pages use."""
    return float(cell.replace(",", "."))


def _table(name: str) -> list[TransmissionLossSpectrum]:
    """The rows of one transmission loss table, in catalogue order."""
    return [row for row in PUBLISHED_TRANSMISSION_LOSS.values() if row.table == name]


def _impact(name: str) -> list[ImpactInsulation]:
    """The rows of one impact table, in catalogue order."""
    return [row for row in PUBLISHED_IMPACT_INSULATION.values() if row.table == name]


# ---------------------------------------------------------------------------
# How many rows each table became
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("table", "count"),
    [
        ("harris-1995-table-31-2", 42),
        ("harris-1995-table-31-3", 10),
        ("harris-1995-table-31-5", 21),
        ("harris-1995-table-31-6", 14),
        ("harris-1995-table-31-7", 5),
        ("harris-1995-table-31-8", 27),
        ("harris-1995-table-31-9", 10),
        ("rossing-2014-table-11-4", 23),
    ],
)
def test_each_table_became_one_row_per_printed_rating(table: str, count: int) -> None:
    """A column is a row, so a table's size is the number of cells it rates."""
    rows = _table(table)
    assert len(rows) == count
    assert all(row.sound_transmission_class is not None for row in rows)


@pytest.mark.parametrize(
    ("table", "oracle"),
    [
        ("harris-1977-table-19-2", ref.HARRIS_1977_19_2),
        ("harris-1977-table-19-3", ref.HARRIS_1977_19_3),
        ("harris-1977-table-19-4", ref.HARRIS_1977_19_4),
    ],
)
def test_each_impact_table_is_one_row_per_printed_row(
    table: str, oracle: tuple[tuple[str, tuple[str, ...]], ...]
) -> None:
    rows = _impact(table)
    assert [row.name for row in rows] == [label for label, _ in oracle]


# ---------------------------------------------------------------------------
# Every printed cell, read back
# ---------------------------------------------------------------------------
def test_table_31_2_holds_every_cell_under_the_column_it_was_printed_in() -> None:
    columns = [
        ("Sin cámara de absorción", "1/1"),
        ("Sin cámara de absorción", "1/2"),
        ("Sin cámara de absorción", "2/2"),
        ("Con cámara de absorción", "1/1"),
        ("Con cámara de absorción", "1/2"),
        ("Con cámara de absorción", "2/2"),
    ]
    rows = {(row.name, row.variant): row for row in _table("harris-1995-table-31-2")}
    for label, cells in ref.HARRIS_31_2:
        for (cavity, layers), cell in zip(columns, cells, strict=True):
            row = rows[label, f"{cavity}, capas de escayola {layers}"]
            assert row.sound_transmission_class == _num(cell)


def test_table_31_3_holds_both_weights_of_every_thickness() -> None:
    rows = {
        (row.name, row.thickness_mm): row for row in _table("harris-1995-table-31-3")
    }
    for label, (light_kg, light_stc, normal_kg, normal_stc) in ref.HARRIS_31_3:
        thickness = _num(label)
        light = rows["Pared de bloques de peso ligero", thickness]
        normal = rows["Pared de bloques de peso normal", thickness]
        assert (light.block_mass_kg, light.sound_transmission_class) == (
            _num(light_kg),
            _num(light_stc),
        )
        assert (normal.block_mass_kg, normal.sound_transmission_class) == (
            _num(normal_kg),
            _num(normal_stc),
        )
        # A mass per block is not a mass per square metre.
        assert light.surface_density_kg_m2 is None
        assert normal.surface_density_kg_m2 is None


def test_table_31_5_has_a_row_for_every_printed_cell_and_none_for_a_blank() -> None:
    columns = [
        "Sin fibra de vidrio, un lado",
        "Sin fibra de vidrio, ambos lados",
        "Con fibra de vidrio, un lado",
        "Con fibra de vidrio, ambos lados",
    ]
    rows = {(row.name, row.variant): row for row in _table("harris-1995-table-31-5")}
    blanks = 0
    for label, cells in ref.HARRIS_31_5:
        for column, cell in zip(columns, cells, strict=True):
            if cell:
                assert rows[label, column].sound_transmission_class == _num(cell)
            else:
                blanks += 1
                assert (label, column) not in rows
    assert blanks == 7
    assert len(rows) == 4 * len(ref.HARRIS_31_5) - blanks


def test_table_31_6_rates_each_door_unsealed_and_sealed() -> None:
    rows = {(row.name, row.variant): row for row in _table("harris-1995-table-31-6")}
    for label, (mass, unsealed, sealed) in ref.HARRIS_31_6:
        loose = rows[label, "Sin sellar"]
        tight = rows[label, "Bien selladas"]
        assert loose.sound_transmission_class == _num(unsealed)
        assert tight.sound_transmission_class == _num(sealed)
        for row in (loose, tight):
            if mass.endswith(" each"):
                assert row.surface_density_kg_m2 is None
                assert row.unquantified == {"surface_density_kg_m2": mass}
                assert mass in row.why_missing("surface_density_kg_m2")
            else:
                assert row.surface_density_kg_m2 == _num(mass)


def test_sealing_a_door_never_lowers_its_rating() -> None:
    """Not a claim of this library: a check the transcription kept the columns."""
    rows = _table("harris-1995-table-31-6")
    by_name: dict[str, dict[str, float | None]] = {}
    for row in rows:
        by_name.setdefault(row.name, {})[row.variant] = row.sound_transmission_class
    for ratings in by_name.values():
        assert ratings["Bien selladas"] >= ratings["Sin sellar"]  # type: ignore[operator]


def test_table_31_7_holds_the_kilograms_and_the_thickness_of_the_heading() -> None:
    rows = {row.name: row for row in _table("harris-1995-table-31-7")}
    for label, (kg, _lb, stc) in ref.HARRIS_31_7:
        row = rows[label]
        assert row.surface_density_kg_m2 == _num(kg)
        assert row.sound_transmission_class == _num(stc)
        assert row.thickness_mm == 45


def test_the_two_weight_columns_of_table_31_7_are_one_quantity() -> None:
    """The criterion the errata registry holds Chapter 32 to, applied here.

    The imperial half is the measurement and the SI half its translation; a
    pair is sound when the SI half is the conversion rounded or truncated to
    the precision it is printed to. All five pairs of this table pass, which
    is why the catalogue holds the kg/m2 column and registers nothing.
    """
    lb_ft2_in_kg_m2 = 0.45359237 / 0.3048**2
    for _label, (kg, lb, _stc) in ref.HARRIS_31_7:
        converted = _num(lb) * lb_ft2_in_kg_m2
        assert _num(kg) in {round(converted), math.floor(converted)}


def test_table_31_8_is_turned_so_that_a_row_is_a_window() -> None:
    headings = [
        "Cristal único",
        "Cristal doble, 3 mm y 3 mm",
        "Cristal doble, 6 mm y 6 mm",
        "Cristal doble, 6 mm y L-7 mm",
    ]
    rows = {(row.name, row.variant): row for row in _table("harris-1995-table-31-8")}
    printed = 0
    for rating, cells in ref.HARRIS_31_8:
        for heading, cell in zip(headings, cells, strict=True):
            if not cell:
                continue
            printed += 1
            row = rows[heading, cell.replace("†", "")]
            assert row.sound_transmission_class == _num(rating)
    assert printed == len(rows) == 27


def test_a_single_pane_holds_its_thickness_and_a_double_one_its_gap_only() -> None:
    for row in _table("harris-1995-table-31-8"):
        if row.name != "Cristal único":
            assert row.thickness_mm is None
            assert "air gap" in row.note
        elif row.variant == "3 mm, 4 mm":
            assert row.thickness_mm is None
            assert row.reported == {"thickness_mm": (3.0, 4.0)}
        else:
            assert row.thickness_mm == float(re.sub(r"[^0-9.]", "", row.variant))


def test_a_laminated_pane_says_so() -> None:
    laminated = [
        row for row in _table("harris-1995-table-31-8") if row.variant.startswith("L-")
    ]
    assert {row.variant for row in laminated} == {"L-20 mm", "L-12 mm", "L-6 mm"}
    assert all("laminated" in row.note for row in laminated)


def test_table_31_9_holds_floor_ceiling_and_group_as_printed() -> None:
    rows = {
        row.name + "|" + row.variant: row for row in _table("harris-1995-table-31-9")
    }
    keyed = {
        key.rsplit("/", 1)[1]: row
        for key, row in PUBLISHED_TRANSMISSION_LOSS.items()
        if row.table == "harris-1995-table-31-9"
    }
    for number, (group, floor, ceiling, stc) in ref.HARRIS_31_9:
        row = keyed[number]
        assert (row.group, row.name, row.variant) == (group, floor, ceiling)
        assert row.sound_transmission_class == _num(stc)
    assert len(rows) == len(ref.HARRIS_31_9)


def test_every_floor_printed_as_the_same_as_another_names_it() -> None:
    table = "harris-1995-table-31-9"
    referring = {
        key.rsplit("/", 1)[1]: row.refers_to_row
        for key, row in PUBLISHED_TRANSMISSION_LOSS.items()
        if row.table == table and row.refers_to_row
    }
    assert referring == {"5": "4", "7": "6", "9": "8", "10": "8"}
    for number, target in referring.items():
        assert (
            f"Igual que {target}"
            in PUBLISHED_TRANSMISSION_LOSS[f"{table}/{number}"].name
        )
        assert f"{table}/{target}" in PUBLISHED_TRANSMISSION_LOSS


def test_rossing_11_4_holds_six_bands_and_a_rating_per_row() -> None:
    bands = (125, 250, 500, 1000, 2000, 4000)
    rows = {row.name: row for row in _table("rossing-2014-table-11-4")}
    assert list(rows) == [label for label, _ in ref.ROSSING_11_4]
    for label, cells in ref.ROSSING_11_4:
        row = rows[label]
        assert [row.transmission_loss_db(band) for band in bands] == [
            _num(cell) for cell in cells[:6]
        ]
        assert row.sound_transmission_class == _num(cells[6])
        assert row.transmission_loss_63_db is None
        assert row.transmission_loss_8000_db is None


@pytest.mark.parametrize(
    ("fragment", "inches"),
    [
        ("8 inch thick concrete masonry units", 8),
        ("4 inch thick brick wall", 4),
        ("Single-paned 1/8 inch thick glass", 1 / 8),
        ("1/2 inch thick laminated glass", 1 / 2),
        ("Hollow wooden door, 1 3/4 inch thick", 1.75),
        ("8 inch thick concrete slab floor", 8),
    ],
)
def test_a_printed_overall_thickness_is_held_at_25_4_mm_to_the_inch(
    fragment: str, inches: float
) -> None:
    (row,) = (row for row in _table("rossing-2014-table-11-4") if row.name == fragment)
    assert row.thickness_mm == pytest.approx(inches * 25.4, abs=1e-9)


def test_a_layer_thickness_is_not_taken_for_the_construction() -> None:
    """ "1/2 inch drywall on wooden studs" is the drywall, not the wall."""
    for row in _table("rossing-2014-table-11-4"):
        if "drywall" in row.name or "air gap" in row.name:
            assert row.thickness_mm is None


def test_the_open_plan_partition_keeps_the_name_the_page_prints() -> None:
    (row,) = (row for row in _table("rossing-2014-table-11-4") if "office" in row.name)
    assert row.name == "Open-plane office partition"
    assert "ERRATA" in row.note


# ---------------------------------------------------------------------------
# A rating with no spectrum refuses every band
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "table",
    [f"harris-1995-table-31-{n}" for n in (2, 3, 5, 6, 7, 8, 9)],
)
def test_a_table_that_prints_only_a_rating_refuses_every_band(table: str) -> None:
    row = _table(table)[0]
    for band in TRANSMISSION_LOSS_BANDS_HZ:
        with pytest.raises(ValueError, match=r"has no transmission_loss_\d+_db"):
            row.transmission_loss_db(band)


# ---------------------------------------------------------------------------
# Harris (1977): a third impact quantity, in decibels
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("table", "oracle"),
    [
        ("harris-1977-table-19-2", ref.HARRIS_1977_19_2),
        ("harris-1977-table-19-3", ref.HARRIS_1977_19_3),
    ],
)
def test_each_finish_holds_the_improvement_the_page_prints(
    table: str, oracle: tuple[tuple[str, tuple[str, ...]], ...]
) -> None:
    for row, (_label, (value,)) in zip(_impact(table), oracle, strict=True):
        if "-" in value:
            low, high = value.split("-")
            assert row.impact_sound_improvement_db is None
            assert row.ranges == {
                "impact_sound_improvement_db": (_num(low), _num(high))
            }
        else:
            assert row.impact_sound_improvement_db == _num(value)


def test_each_timber_floor_holds_its_improvement_and_its_load() -> None:
    rows = _impact("harris-1977-table-19-4")
    for row, (_label, (load, value)) in zip(rows, ref.HARRIS_1977_19_4, strict=True):
        assert row.impact_sound_improvement_db == _num(value)
        assert row.added_load_pa == pytest.approx(
            _num(load) * TECHNICAL_ATMOSPHERE_PA, rel=1e-12
        )


def test_the_floor_printed_twice_is_two_rows_told_apart_by_the_load() -> None:
    name = "Suelo de parquet (sin listones) sobre cubierta de lana de vidrio de 18 mm"
    twice = [row for row in _impact("harris-1977-table-19-4") if row.name == name]
    assert len(twice) == 2
    unloaded, loaded = twice
    assert (unloaded.added_load_pa, unloaded.impact_sound_improvement_db) == (0, 27)
    assert loaded.added_load_pa == pytest.approx(82375.86)
    assert loaded.impact_sound_improvement_db == 22
    assert unloaded.variant != loaded.variant


def test_the_1977_rows_carry_no_rating_and_the_rating_rows_no_decibels() -> None:
    for row in PUBLISHED_IMPACT_INSULATION.values():
        if row.table.startswith("harris-1977-"):
            assert row.impact_insulation_class is None
            assert row.impact_insulation_class_improvement is None
        else:
            assert row.impact_sound_improvement_db is None
            assert row.added_load_pa is None


def test_table_19_2_cites_the_page_it_is_printed_on() -> None:
    """The running text calls it on the next page; the table is on this one."""
    (source,) = {row.source for row in _impact("harris-1977-table-19-2")}
    assert source == "Harris (1977) Table 19.2, PDF page 742 (printed p. 729)"
