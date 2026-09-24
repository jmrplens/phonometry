#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A catalogue written to a file reads back into the same rows.

``io.write_catalogue`` writes what ``io.read_catalogue`` reads: the cells
each row's page prints, never a value this library derived, and a value
converted from another unit in that unit when it reads back to the same
float. The test that carries the layer is the round trip of every published
table: each one is written, read back and compared field for field with the
rows it came from, the type of every value included, so every row class and
every hedge the packaged data uses goes through the reader.
"""

from __future__ import annotations

import dataclasses
import datetime
import importlib
import json
import os
import pathlib
import pkgutil
import re
from collections.abc import Mapping
from typing import Any

import pytest

import phonometry
from phonometry import fluids, io, materials, solids
from phonometry.materials import AbsorptionAreaSpectrum, PorousMaterial


def _published_tables() -> list[tuple[str, str, dict[str, io.CatalogueRow]]]:
    """Every table of every published mapping of rows, one entry each."""
    found: list[tuple[str, str, dict[str, io.CatalogueRow]]] = []
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if not (name.startswith("PUBLISHED_") and isinstance(value, Mapping)):
                continue
            tables: dict[str, dict[str, io.CatalogueRow]] = {}
            for key, row in value.items():
                if isinstance(row, io.CatalogueRow):
                    tables.setdefault(row.table, {})[key] = row
            found += [(name, table, rows) for table, rows in sorted(tables.items())]
    return found


TABLES = _published_tables()

#: The fields that name where a row was read from, which a file of yours
#: says in its own way: the catalogue's name and the provenance.
_WHERE_FROM = frozenset({"table", "provenance"})


def test_every_published_table_is_found() -> None:
    """Every packaged data file with rows, two of them split in two mappings."""
    assert len({table for _, table, _ in TABLES}) >= 80
    assert len(TABLES) >= 82


@pytest.mark.parametrize(
    ("mapping", "table", "rows"),
    TABLES,
    ids=[f"{mapping}-{table}" for mapping, table, _ in TABLES],
)
def test_every_published_table_reads_back_field_for_field(
    tmp_path: pathlib.Path,
    mapping: str,
    table: str,
    rows: dict[str, io.CatalogueRow],
) -> None:
    path = tmp_path / f"{table}.json"
    catalogue = "copy-of-" + mapping.lower().replace("_", "-")
    io.write_catalogue(rows, path, catalogue=catalogue)
    row_type = type(next(iter(rows.values())))
    back = io.read_catalogue(path, row_type=row_type)
    assert [key.partition("/")[2] for key in back] == [
        key.rpartition("/")[2] for key in rows
    ]
    for (key, row), again in zip(rows.items(), back.values(), strict=True):
        for item in dataclasses.fields(row):
            if item.name in _WHERE_FROM:
                continue
            held, read = getattr(row, item.name), getattr(again, item.name)
            assert read == held, (key, item.name)
            assert type(read) is type(held), (key, item.name)
        assert again.table == catalogue
        assert again.provenance is not None
        assert again.provenance.kind == "publication"
        assert again.source == row.source
    assert back.notes == ()


def test_the_legends_of_a_table_travel_with_it(tmp_path: pathlib.Path) -> None:
    from phonometry import noise_control

    rows = {
        key: row
        for key, row in noise_control.PUBLISHED_DUCT_TRANSMISSION_LOSS.items()
        if row.table == "ashrae-2019-tables-29-to-34"
    }
    path = tmp_path / "ducts.json"
    io.write_catalogue(rows, path, catalogue="ducts")
    back = io.read_catalogue(path, row_type=noise_control.DuctWallSpectrum)
    assert len(back.conventions) >= 2
    assert back.conventions[0].startswith("Table 32 note")
    assert back.about.startswith(
        json.loads(path.read_text(encoding="utf-8"))["about"][:40]
    )


def test_a_table_is_exported_as_a_publication_consulted_today(
    tmp_path: pathlib.Path,
) -> None:
    rows = _hopkins_a2()
    path = tmp_path / "plantilla.json"
    written = io.write_catalogue(rows, path, catalogue="plantilla-a2")
    assert written == (path,)
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema"] == "phonometry-catalogue"
    assert document["schema_version"] == 1
    assert document["row_type"] == "SolidMaterial"
    provenance = document["provenance"]
    assert provenance["kind"] == "publication"
    assert provenance["version"] is None
    assert provenance["document"] == next(iter(rows.values())).source
    today = datetime.datetime.now(tz=datetime.UTC).date()
    consulted = datetime.date.fromisoformat(provenance["consulted"])
    assert abs((consulted - today).days) <= 1
    assert all("derived" not in row for row in document["rows"])
    assert document["phonometry_version"] == phonometry.__version__


def test_a_provenance_passed_in_makes_the_file_the_same_every_day(
    tmp_path: pathlib.Path,
) -> None:
    rows = _hopkins_a2()
    source = next(iter(rows.values())).source
    fixed = io.Provenance(
        kind="publication", document=source, version=None, consulted="2026-09-23"
    )
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    io.write_catalogue(rows, first, catalogue="plantilla-a2", provenance=fixed)
    io.write_catalogue(rows, second, catalogue="plantilla-a2", provenance=fixed)
    assert first.read_bytes() == second.read_bytes()


def test_a_value_the_page_prints_in_sabins_is_written_in_sabins(
    tmp_path: pathlib.Path,
) -> None:
    rows = dict(materials.PUBLISHED_ABSORPTION_AREAS)
    rows = {key: row for key, row in rows.items() if row.table == "long-2014-table-7-1"}
    path = tmp_path / "areas.json"
    io.write_catalogue(rows, path, catalogue="areas")
    document = json.loads(path.read_text(encoding="utf-8"))
    musician = next(row for row in document["rows"] if "absorption_area_500_ft2" in row)
    assert "absorption_area_500_m2" not in musician
    assert "converted" not in musician
    assert re.search(r'"absorption_area_500_ft2": 11\.5\b', path.read_text("utf-8"))


def test_a_value_in_a_unit_no_family_holds_keeps_its_record(
    tmp_path: pathlib.Path,
) -> None:
    rows = {
        key: row
        for key, row in solids.PUBLISHED_DAMPING.items()
        if row.table == "ver-beranek-2006-table-14-1"
    }
    path = tmp_path / "damping.json"
    io.write_catalogue(rows, path, catalogue="damping")
    first = json.loads(path.read_text(encoding="utf-8"))["rows"][0]
    assert first["converted"]["youngs_modulus_max_pa"] == ["3e5", "psi"]
    assert first["youngs_modulus_max_pa"] == 2068427190.0


# ---------------------------------------------------------------------------
# A catalogue of your own
# ---------------------------------------------------------------------------
_MINE: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "panel-40",
    "row_type": "PorousMaterial",
    "about": "Core of the Panel 40 absorber as its data sheet gives it.",
    "provenance": {
        "kind": "datasheet",
        "document": "Panel 40 technical data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 4",
        "consulted": "2026-09-23",
        "page": "2",
        "field_test_standards": {"flow_resistivity_kpa_s_m2": "EN 29053"},
    },
    "basis": "declared",
    "conventions": ["Values at 23 °C"],
    "rows": [
        {
            "key": "core-declared",
            "name": "Panel 40 core",
            "thickness_cm": 4,
            "ranges": {"flow_resistivity_kpa_s_m2": [5, None]},
            "bounded_below": ["flow_resistivity_kpa_s_m2"],
            "x-product-code": "P40-C",
        },
        {
            "key": "core-lab",
            "name": "Panel 40 core",
            "provenance": {
                "page": "3",
                "laboratory": "Example Lab",
                "report": "26-014",
            },
            "basis": {"row": "measured"},
            "flow_resistivity_kpa_s_m2": 12.5,
            "uncertainty": {"flow_resistivity_kpa_s_m2": 0.9},
            "reported": {"tortuosity": [1.02, [1.0, 1.05]]},
            "x-edge": 24,
        },
    ],
}


def _mine() -> io.Catalogue[PorousMaterial]:
    return io.parse_catalogue(json.dumps(_MINE), row_type=PorousMaterial)


def test_a_catalogue_of_your_own_reads_back_as_itself(tmp_path: pathlib.Path) -> None:
    mine = _mine()
    path = tmp_path / "mine.json"
    io.write_catalogue(mine, path)
    back = io.read_catalogue(path, row_type=PorousMaterial)
    assert back == mine
    assert back.extras == mine.extras
    assert back.conventions == mine.conventions
    assert back.provenance == mine.provenance
    for key in mine:
        assert back[key].provenance == mine[key].provenance


def test_a_converted_cell_is_written_in_the_unit_it_was_read_in(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "mine.json"
    io.write_catalogue(_mine(), path)
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    assert rows[0]["thickness_cm"] == 4
    assert rows[0]["ranges"] == {"flow_resistivity_kpa_s_m2": [5, None]}
    assert rows[1]["flow_resistivity_kpa_s_m2"] == 12.5
    assert rows[1]["uncertainty"] == {"flow_resistivity_kpa_s_m2": 0.9}
    assert all("converted" not in row for row in rows)
    assert rows[1]["provenance"] == {
        "page": "3",
        "laboratory": "Example Lab",
        "report": "26-014",
    }
    assert rows[1]["x-edge"] == "24"


def test_a_row_of_your_own_filtered_out_of_a_catalogue_writes_alone(
    tmp_path: pathlib.Path,
) -> None:
    mine = _mine()
    lab = {key: row for key, row in mine.items() if key.endswith("lab")}
    path = tmp_path / "lab.json"
    io.write_catalogue(lab, path, about="The laboratory page alone.")
    back = io.read_catalogue(path, row_type=PorousMaterial)
    assert back["panel-40/core-lab"] == mine["panel-40/core-lab"]
    assert back.provenance.report == "26-014"


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------
def _hopkins_a2() -> dict[str, io.CatalogueRow]:
    return {
        key: row
        for key, row in solids.PUBLISHED_SOLIDS.items()
        if row.table == "hopkins-2007-table-a2"
    }


def test_a_mapping_of_several_tables_shows_the_filter(tmp_path: pathlib.Path) -> None:
    rows = dict(solids.PUBLISHED_SOLIDS)
    with pytest.raises(io.CatalogueError, match=r"r\.table =="):
        io.write_catalogue(rows, tmp_path / "all.json", catalogue="all-solids")


def test_a_table_of_the_library_needs_a_name_of_your_own(
    tmp_path: pathlib.Path,
) -> None:
    rows = _hopkins_a2()
    with pytest.raises(TypeError, match="catalogue= is required"):
        io.write_catalogue(rows, tmp_path / "a2.json")


def test_a_reserved_name_is_refused_with_a_free_one(tmp_path: pathlib.Path) -> None:
    rows = _hopkins_a2()
    with pytest.raises(io.CatalogueError, match="'hopkins-table-a2-2007'"):
        io.write_catalogue(
            rows, tmp_path / "a2.json", catalogue="hopkins-2007-table-a2"
        )


def test_the_fluid_states_are_not_rows(tmp_path: pathlib.Path) -> None:
    rows = fluids.PUBLISHED_FLUIDS
    with pytest.raises(TypeError, match="Fluid states"):
        io.write_catalogue(rows, tmp_path / "fluids.json", catalogue="fluids")  # type: ignore[arg-type]


def test_rows_of_two_classes_are_refused(tmp_path: pathlib.Path) -> None:
    rows = {
        **dict(list(materials.PUBLISHED_POROUS.items())[:1]),
        **dict(list(materials.PUBLISHED_CARPETS.items())[:1]),
    }
    with pytest.raises(TypeError, match="rows of one class"):
        io.write_catalogue(rows, tmp_path / "mixed.json", catalogue="mixed")


def test_no_rows_is_nothing_to_write(tmp_path: pathlib.Path) -> None:
    with pytest.raises(io.CatalogueError, match="nothing to write"):
        io.write_catalogue({}, tmp_path / "empty.json", catalogue="empty")


def test_a_file_is_never_replaced_unless_asked(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "mine.json"
    path.write_text("keep", encoding="utf-8")
    mine = _mine()
    with pytest.raises(FileExistsError, match="overwrite=True"):
        io.write_catalogue(mine, path)
    assert path.read_text(encoding="utf-8") == "keep"
    io.write_catalogue(mine, path, overwrite=True)
    assert io.read_catalogue(path, row_type=PorousMaterial) == mine


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symbolic links here")
def test_a_symbolic_link_is_never_written_through(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "elsewhere.json"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    mine = _mine()
    with pytest.raises(FileExistsError, match="symbolic link"):
        io.write_catalogue(mine, link, overwrite=True)
    assert target.read_text(encoding="utf-8") == "keep"


def test_a_write_leaves_no_file_but_its_own(tmp_path: pathlib.Path) -> None:
    io.write_catalogue(_mine(), tmp_path / "mine.json")
    assert [path.name for path in tmp_path.iterdir()] == ["mine.json"]


def test_a_failed_write_leaves_nothing_behind(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(self: pathlib.Path, target: pathlib.Path) -> None:
        raise OSError(self, target)

    monkeypatch.setattr(pathlib.Path, "replace", refuse)
    mine = _mine()
    with pytest.raises(OSError, match="tmp"):
        io.write_catalogue(mine, tmp_path / "mine.json")
    assert list(tmp_path.iterdir()) == []


def test_a_file_is_named_json(tmp_path: pathlib.Path) -> None:
    mine = _mine()
    with pytest.raises(ValueError, match="ends in .json"):
        io.write_catalogue(mine, tmp_path / "mine.csv")


def test_a_key_a_file_cannot_hold_is_refused(tmp_path: pathlib.Path) -> None:
    rows = {"mine/core lab": _mine()["panel-40/core-lab"]}
    with pytest.raises(io.CatalogueError, match="'core lab'"):
        io.write_catalogue(rows, tmp_path / "mine.json", about="A row.")


def test_rows_of_two_documents_are_refused(tmp_path: pathlib.Path) -> None:
    mine = _mine()
    other = dataclasses.replace(
        mine["panel-40/core-lab"],
        provenance=dataclasses.replace(
            mine.provenance, document="Panel 50 technical data sheet"
        ),
    )
    rows = {"panel-40/a": mine["panel-40/core-declared"], "panel-40/b": other}
    with pytest.raises(io.CatalogueError, match="one document"):
        io.write_catalogue(rows, tmp_path / "two.json", about="Two sheets.")


def test_an_area_per_volume_keeps_what_it_is_per(tmp_path: pathlib.Path) -> None:
    rows = {
        key: row
        for key, row in materials.PUBLISHED_ABSORPTION_AREAS.items()
        if row.per not in ("", "person")
    }
    assert rows
    path = tmp_path / "air.json"
    io.write_catalogue(rows, path, catalogue="air")
    back = io.read_catalogue(path, row_type=AbsorptionAreaSpectrum)
    for key, row in rows.items():
        assert back[f"air/{key.rpartition('/')[2]}"].per == row.per
