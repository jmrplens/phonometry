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

import copy
import dataclasses
import datetime
import errno
import importlib
import json
import os
import pathlib
import pkgutil
import re
import stat
import sys
from collections.abc import Mapping
from typing import Any

import pytest

import phonometry
from phonometry import fluids, io, materials, solids
from phonometry._internal import json_input
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
    path = tmp_path / "template.json"
    written = io.write_catalogue(rows, path, catalogue="template-a2")
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
    io.write_catalogue(rows, first, catalogue="template-a2", provenance=fixed)
    io.write_catalogue(rows, second, catalogue="template-a2", provenance=fixed)
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


def test_a_figure_that_does_not_read_back_is_written_in_the_field_unit(
    tmp_path: pathlib.Path,
) -> None:
    """A record that does not convert to the value held never replaces it."""
    row = PorousMaterial(
        name="Panel 40 core",
        source="Panel 40 technical data sheet",
        flow_resistivity_pa_s_m2=12480.0,
        converted={"flow_resistivity_pa_s_m2": ("12.5", "kPa s/m2")},
    )
    path = tmp_path / "mine.json"
    io.write_catalogue(
        {"mine/core": row}, path, catalogue="mine", about="A row built in Python."
    )
    written = json.loads(path.read_text(encoding="utf-8"))["rows"][0]
    assert written["flow_resistivity_pa_s_m2"] == 12480.0
    assert "flow_resistivity_kpa_s_m2" not in written
    assert written["converted"] == {"flow_resistivity_pa_s_m2": ["12.5", "kPa s/m2"]}
    back = io.read_catalogue(path, row_type=PorousMaterial)["mine/core"]
    assert back.flow_resistivity_pa_s_m2 == 12480.0
    assert back.converted == row.converted


def test_a_record_too_far_from_one_to_convert_is_kept_as_a_record(
    tmp_path: pathlib.Path,
) -> None:
    """Reading 1e-999999999 exactly would take minutes; it is not tried."""
    row = PorousMaterial(
        name="Panel 40 core",
        source="Panel 40 technical data sheet",
        thickness_mm=40.0,
        converted={"thickness_mm": ("1e-999999999", "cm")},
    )
    path = tmp_path / "mine.json"
    io.write_catalogue(
        {"mine/core": row}, path, catalogue="mine", about="A row built in Python."
    )
    written = json.loads(path.read_text(encoding="utf-8"))["rows"][0]
    assert written["thickness_mm"] == 40.0
    assert "thickness_cm" not in written
    assert written["converted"] == {"thickness_mm": ["1e-999999999", "cm"]}


def test_a_plus_or_minus_is_written_in_the_unit_it_reads_back_in(
    tmp_path: pathlib.Path,
) -> None:
    """4.2 Pa s/m2 is 0.0042 kPa s/m2, whose float reads back as 4.200000000000001."""
    document = copy.deepcopy(_MINE)
    document["rows"][1]["uncertainty"] = {"flow_resistivity_kpa_s_m2": 0.0042}
    mine = io.parse_catalogue(json.dumps(document), row_type=PorousMaterial)
    lab = mine["panel-40/core-lab"]
    assert lab.uncertainty == {"flow_resistivity_pa_s_m2": 4.2}
    path = tmp_path / "mine.json"
    io.write_catalogue(mine, path)
    written = json.loads(path.read_text(encoding="utf-8"))["rows"][1]
    assert written["flow_resistivity_pa_s_m2"] == 12500.0
    assert written["uncertainty"] == {"flow_resistivity_pa_s_m2": 4.2}
    assert written["converted"] == {"flow_resistivity_pa_s_m2": ["12.5", "kPa s/m2"]}
    back = io.read_catalogue(path, row_type=PorousMaterial)
    assert back == mine
    assert back["panel-40/core-lab"].uncertainty == {"flow_resistivity_pa_s_m2": 4.2}


def test_the_standard_of_one_field_is_written_where_the_rows_differ(
    tmp_path: pathlib.Path,
) -> None:
    document = copy.deepcopy(_MINE)
    document["rows"][1]["provenance"]["field_test_standards"] = {
        "tortuosity": "ISO 9053-1:2018"
    }
    mine = io.parse_catalogue(json.dumps(document), row_type=PorousMaterial)
    path = tmp_path / "mine.json"
    io.write_catalogue(mine, path)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["provenance"]["field_test_standards"] == {
        "flow_resistivity_pa_s_m2": "EN 29053"
    }
    assert written["rows"][1]["provenance"]["field_test_standards"] == {
        "tortuosity": "ISO 9053-1:2018"
    }
    assert "provenance" not in written["rows"][0]
    back = io.read_catalogue(path, row_type=PorousMaterial)
    for key in mine:
        assert back[key].provenance == mine[key].provenance


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
    with pytest.raises(
        io.CatalogueError, match="a catalogue with no rows says nothing"
    ):
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


#: The refusal of a file at ``mine.json`` written without ``overwrite``.
_KEPT = r"mine\.json exists; pass overwrite=True to replace it$"


def _made_while_written(monkeypatch: pytest.MonkeyPatch, path: pathlib.Path) -> None:
    """Have another program make a file at *path* while the new one is written.

    The writer looks at the name before it writes a byte; the file is made
    after that, once the new file's bytes are on the disk, and before the
    new file is put at the name.
    """
    fsync = os.fsync

    def and_theirs(fd: int) -> None:
        fsync(fd)
        path.write_text("theirs", encoding="utf-8")

    monkeypatch.setattr(os, "fsync", and_theirs)


def _kept_alone(tmp_path: pathlib.Path) -> None:
    """The other program's file is at the name, and the new file nowhere."""
    assert (tmp_path / "mine.json").read_text(encoding="utf-8") == "theirs"
    assert [path.name for path in tmp_path.iterdir()] == ["mine.json"]


def test_a_file_made_at_the_name_while_it_is_written_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The name is refused in the step that puts the new file there.

    Looked at only before the file was written, the name was then renamed
    over, and a file another program had made there was replaced without a
    word.
    """
    path = tmp_path / "mine.json"
    _made_while_written(monkeypatch, path)
    mine = _mine()
    with pytest.raises(FileExistsError, match=_KEPT):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    _kept_alone(tmp_path)
    path.unlink()
    io.write_catalogue(_mine(), path)
    assert io.read_catalogue(path, row_type=PorousMaterial) == _mine()
    assert [item.name for item in tmp_path.iterdir()] == ["mine.json"]


def _no_hard_links(monkeypatch: pytest.MonkeyPatch) -> None:
    """The file system of FAT, say, on POSIX: it makes no hard link."""

    def refuse(*_: object, **__: object) -> None:
        raise PermissionError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(json_input, "_WINDOWS", False)
    monkeypatch.setattr(os, "link", refuse)


def test_without_hard_links_a_file_made_before_the_name_is_taken_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file system that makes no hard link, such as FAT, still writes.

    The name is taken by an empty file of the writer's own and the new file
    renamed over it; a file made at the name before is kept and refused.
    """
    _no_hard_links(monkeypatch)
    path = tmp_path / "mine.json"
    io.write_catalogue(_mine(), path)
    assert io.read_catalogue(path, row_type=PorousMaterial) == _mine()
    assert [item.name for item in tmp_path.iterdir()] == ["mine.json"]
    path.unlink()
    _made_while_written(monkeypatch, path)
    mine = _mine()
    with pytest.raises(FileExistsError, match=_KEPT):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    _kept_alone(tmp_path)


def test_without_hard_links_no_file_is_made_at_the_name_once_it_is_taken(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another program making its file just before the rename finds the name taken.

    Looked at again just before the rename, the name was free, and a file
    made there in that instant was then replaced without a word.
    """
    _no_hard_links(monkeypatch)
    path = tmp_path / "mine.json"
    replace = pathlib.Path.replace
    made: list[str] = []

    def theirs_first(self: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
        try:
            handle = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            pass
        else:
            os.write(handle, b"theirs")
            os.close(handle)
            made.append(os.fspath(target))
        return replace(self, target)

    monkeypatch.setattr(pathlib.Path, "replace", theirs_first)
    io.write_catalogue(_mine(), path)
    monkeypatch.undo()
    assert made == []
    assert io.read_catalogue(path, row_type=PorousMaterial) == _mine()
    assert [item.name for item in tmp_path.iterdir()] == ["mine.json"]


def test_without_hard_links_a_failed_rename_leaves_nothing_behind(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither the empty file that took the name nor the new file stays."""
    _no_hard_links(monkeypatch)

    def refuse(self: pathlib.Path, target: pathlib.Path) -> None:
        raise OSError(errno.EIO, "Input/output error", str(target))

    monkeypatch.setattr(pathlib.Path, "replace", refuse)
    mine = _mine()
    with pytest.raises(OSError, match="Input/output error"):
        io.write_catalogue(mine, tmp_path / "mine.json")
    assert list(tmp_path.iterdir()) == []


def test_without_hard_links_a_file_renamed_over_the_taken_name_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After a failure, only the writer's own empty file is removed.

    Another program that renamed its file over the empty one keeps it, and
    the new file is removed.
    """
    _no_hard_links(monkeypatch)
    path = tmp_path / "mine.json"
    theirs = tmp_path / "theirs.json"
    replace = pathlib.Path.replace

    def theirs_then_fail(self: pathlib.Path, target: pathlib.Path) -> None:
        theirs.write_text("theirs", encoding="utf-8")
        replace(theirs, target)
        raise OSError(errno.EIO, "Input/output error", str(target))

    monkeypatch.setattr(pathlib.Path, "replace", theirs_then_fail)
    mine = _mine()
    with pytest.raises(OSError, match="Input/output error"):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    _kept_alone(tmp_path)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="the reserving fallback runs on POSIX, whose O_EXCL never follows a "
    "link; Windows renames, and follows a link on open",
)
def test_without_hard_links_a_link_made_at_the_name_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symbolic link that names nothing takes the name as a file does."""
    _no_hard_links(monkeypatch)
    path = tmp_path / "mine.json"
    fsync = os.fsync

    def and_a_link(fd: int) -> None:
        fsync(fd)
        path.symlink_to(tmp_path / "nowhere.json")

    try:
        (tmp_path / "probe").symlink_to(tmp_path / "nowhere.json")
    except OSError:
        pytest.skip("this system does not let the test make a symbolic link")
    (tmp_path / "probe").unlink()
    monkeypatch.setattr(os, "fsync", and_a_link)
    mine = _mine()
    with pytest.raises(FileExistsError, match=_KEPT):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    assert path.is_symlink()
    assert [item.name for item in tmp_path.iterdir()] == ["mine.json"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows's own rename")
def test_on_windows_a_link_made_at_the_name_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows's rename refuses a symbolic link that names nothing, as a file."""
    path = tmp_path / "mine.json"
    fsync = os.fsync

    def and_a_link(fd: int) -> None:
        fsync(fd)
        path.symlink_to(tmp_path / "nowhere.json")

    try:
        (tmp_path / "probe").symlink_to(tmp_path / "nowhere.json")
    except OSError:
        pytest.skip("this system does not let the test make a symbolic link")
    (tmp_path / "probe").unlink()
    monkeypatch.setattr(os, "fsync", and_a_link)
    mine = _mine()
    with pytest.raises(FileExistsError, match=_KEPT):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    assert path.is_symlink()
    assert [item.name for item in tmp_path.iterdir()] == ["mine.json"]


def test_on_windows_the_rename_refuses_a_file_made_at_the_name(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows's rename refuses a name that holds a file, as it renames."""
    rename = os.rename

    def windows_rename(source: str, target: str) -> None:
        if os.path.lexists(target):
            message = "Cannot create a file when that file already exists"
            raise FileExistsError(errno.EEXIST, message, str(target))
        rename(source, target)

    monkeypatch.setattr(json_input, "_WINDOWS", True)
    monkeypatch.setattr(os, "rename", windows_rename)
    path = tmp_path / "mine.json"
    _made_while_written(monkeypatch, path)
    mine = _mine()
    with pytest.raises(FileExistsError, match=_KEPT):
        io.write_catalogue(mine, path)
    monkeypatch.undo()
    _kept_alone(tmp_path)


def test_a_symbolic_link_is_never_written_through(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "elsewhere.json"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("this system does not let the test make a symbolic link")
    mine = _mine()
    with pytest.raises(FileExistsError, match="symbolic link"):
        io.write_catalogue(mine, link, overwrite=True)
    assert target.read_text(encoding="utf-8") == "keep"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX names are bytes")
def test_a_refusal_to_overwrite_prints_a_name_that_is_not_utf8(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / os.fsdecode(b"\xff-mine.json")
    try:
        path.write_text("keep", encoding="utf-8")
    except (OSError, UnicodeEncodeError):
        pytest.skip("this file system takes only names that are text")
    rows = _mine()
    with pytest.raises(FileExistsError) as caught:
        io.write_catalogue(rows, path)
    assert "\\udcff-mine.json exists" in str(caught.value)
    str(caught.value).encode("utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_a_file_written_over_keeps_its_permission_bits(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "mine.json"
    rows = _mine()
    io.write_catalogue(rows, path)
    path.chmod(0o640)
    io.write_catalogue(rows, path, overwrite=True)
    assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_a_read_only_file_written_over_stays_read_only(tmp_path: pathlib.Path) -> None:
    """On POSIX by its bits, and on Windows by the read-only flag it keeps."""
    path = tmp_path / "mine.json"
    rows = _mine()
    io.write_catalogue(rows, path)
    path.chmod(stat.S_IREAD)
    io.write_catalogue(rows, path, overwrite=True)
    assert not path.stat().st_mode & stat.S_IWRITE
    assert sorted(item.name for item in tmp_path.iterdir()) == ["mine.json"]
    assert io.read_catalogue(path, row_type=PorousMaterial).keys() == rows.keys()
    path.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_a_write_leaves_no_file_but_its_own(tmp_path: pathlib.Path) -> None:
    io.write_catalogue(_mine(), tmp_path / "mine.json")
    assert [path.name for path in tmp_path.iterdir()] == ["mine.json"]


@pytest.mark.parametrize("overwrite", [False, True])
def test_a_failed_write_leaves_nothing_behind(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, *, overwrite: bool
) -> None:
    """Whichever step puts the new file at the name fails, on every system."""

    def refuse(self: pathlib.Path, target: pathlib.Path) -> None:
        raise OSError(self, target)

    monkeypatch.setattr(pathlib.Path, "replace", refuse)
    monkeypatch.setattr(pathlib.Path, "rename", refuse)
    monkeypatch.setattr(os, "link", refuse)
    mine = _mine()
    with pytest.raises(OSError, match=r"\.mine\.json\.[0-9a-f]{16}\.tmp"):
        io.write_catalogue(mine, tmp_path / "mine.json", overwrite=overwrite)
    assert list(tmp_path.iterdir()) == []


def test_a_file_is_named_json_or_csv(tmp_path: pathlib.Path) -> None:
    mine = _mine()
    with pytest.raises(ValueError, match=r"'mine\.xlsx' ends in neither"):
        io.write_catalogue(mine, tmp_path / "mine.xlsx")


def test_a_json_document_takes_no_dialect(tmp_path: pathlib.Path) -> None:
    mine = _mine()
    with pytest.raises(ValueError, match="delimiter= and decimal= declare"):
        io.write_catalogue(mine, tmp_path / "mine.json", delimiter=";")
    assert list(tmp_path.iterdir()) == []


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
    with pytest.raises(io.CatalogueError, match="not all read from one document"):
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


# ---------------------------------------------------------------------------
# Nothing the reader refuses for its size is ever written
# ---------------------------------------------------------------------------
#: The one document every row below is read from.
_FOAMS: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "foams",
    "row_type": "PorousMaterial",
    "about": "Foams of a fictitious data sheet.",
    "provenance": {
        "kind": "datasheet",
        "document": "Example foam data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 2",
        "consulted": "2026-09-30",
    },
    "rows": [{"key": "f0", "name": "Foam", "porosity": 0.9}],
}


def _foams(count: int = 1, **first: object) -> dict[str, io.CatalogueRow]:
    """*count* rows of the foam sheet, built in Python, the first with *first*.

    Built in Python, so that a text the reader would refuse can be held.
    """
    row = io.parse_catalogue(_FOAMS, row_type=PorousMaterial)["foams/f0"]
    rows: dict[str, io.CatalogueRow] = {
        f"foams/f{index}": dataclasses.replace(row, variant=f"batch {index}")
        for index in range(count)
    }
    rows["foams/f0"] = dataclasses.replace(rows["foams/f0"], **first)
    return rows


def _write(
    rows: Mapping[str, io.CatalogueRow],
    path: pathlib.Path,
    about: str = "Foams.",
    *,
    overwrite: bool = False,
) -> None:
    io.write_catalogue(rows, path, catalogue="foams", about=about, overwrite=overwrite)


def _refused_past_the_edge(
    tmp_path: pathlib.Path,
    suffix: str,
    good: tuple[Mapping[str, io.CatalogueRow], str],
    past: tuple[Mapping[str, io.CatalogueRow], str],
) -> io.CatalogueIssue:
    """*good* written and read back, *past* refused over it, the files kept.

    :return: The one issue *past* is refused with.
    """
    path = tmp_path / f"mine.{suffix}"
    _write(good[0], path, good[1])
    back = io.read_catalogue(path, row_type=PorousMaterial)
    assert list(back.values()) == list(good[0].values())
    kept = {item.name: item.read_bytes() for item in tmp_path.iterdir()}
    with pytest.raises(io.CatalogueError) as caught:
        _write(past[0], path, past[1], overwrite=True)
    assert {item.name: item.read_bytes() for item in tmp_path.iterdir()} == kept
    (issue,) = caught.value.issues
    return issue


def _fewer_rows(monkeypatch: pytest.MonkeyPatch, most: int) -> None:
    """The most rows a catalogue holds, lowered, for the JSON and the CSV reader."""
    from phonometry.io import _catalogue, _catalogue_csv

    monkeypatch.setattr(_catalogue, "_MAX_ROWS", most)
    monkeypatch.setattr(_catalogue_csv, "_MAX_ROWS", most)


@pytest.mark.parametrize(
    ("suffix", "where", "said"),
    [
        ("json", "/rows", "holds 4 rows, and a catalogue holds at most 3"),
        ("csv", "line 1", "heads 4 rows, and a catalogue holds at most 3"),
    ],
    ids=["json", "csv"],
)
def test_no_more_rows_are_written_than_a_reader_takes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
    where: str,
    said: str,
) -> None:
    """At the limit the file is written and read back; past it, nothing is.

    The writer wrote any number of rows, and a file of more than the reader
    takes replaced a good one with a file no reader reads.
    """
    _fewer_rows(monkeypatch, 3)
    issue = _refused_past_the_edge(
        tmp_path, suffix, (_foams(3), "Foams."), (_foams(4), "Foams.")
    )
    assert (issue.file, issue.location, issue.message) == (
        f"mine.{suffix}",
        where,
        said,
    )


def _bytes_of(
    written: tuple[Mapping[str, io.CatalogueRow], str],
    suffix: str,
    folder: pathlib.Path,
) -> list[int]:
    """The size of each file *written* makes, the CSV file first, in *folder*."""
    folder.mkdir()
    paths = io.write_catalogue(
        written[0], folder / f"size.{suffix}", catalogue="foams", about=written[1]
    )
    return [path.stat().st_size for path in paths]


@pytest.mark.parametrize(
    ("suffix", "limit", "held_as", "grown"),
    [
        ("json", "_MAX_BYTES", "a catalogue file", "variant"),
        ("csv", "_MAX_BYTES", "a catalogue file", "variant"),
        ("csv", "_MAX_HEADER", "the header of a catalogue CSV", "about"),
    ],
    ids=["json-file", "csv-file", "csv-header"],
)
def test_no_file_is_written_past_the_bytes_a_reader_takes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
    limit: str,
    held_as: str,
    grown: str,
) -> None:
    """A file of exactly the limit is written and read back; one byte more is not."""
    from phonometry.io import _catalogue, _catalogue_csv

    good = (_foams(), "Foams.")
    past = (
        (_foams(variant="batch 0+"), "Foams.")
        if grown == "variant"
        else (_foams(), "Foams!.")
    )
    sizes = _bytes_of(good, suffix, tmp_path / "good")
    size = sizes[-1] if limit == "_MAX_HEADER" else sizes[0]
    assert _bytes_of(past, suffix, tmp_path / "past") != sizes
    module = _catalogue_csv if limit == "_MAX_HEADER" else _catalogue
    monkeypatch.setattr(module, limit, size)
    folder = tmp_path / "edge"
    folder.mkdir()
    issue = _refused_past_the_edge(folder, suffix, good, past)
    name = f"mine.{suffix}" + (".phonometry.json" if limit == "_MAX_HEADER" else "")
    assert (issue.file, issue.location) == (name, "")
    assert issue.message.startswith(
        f"is {size + 1} bytes, and {held_as} is at most {size} bytes"
    )


@pytest.mark.parametrize("suffix", ["json", "csv"])
@pytest.mark.parametrize(
    ("field_name", "limit"),
    [("variant", 2_000), ("note", 20_000)],
    ids=["text", "prose"],
)
def test_no_text_is_written_longer_than_a_reader_takes(
    tmp_path: pathlib.Path, suffix: str, field_name: str, limit: int
) -> None:
    """A text of the longest a reader takes is written and read back; one more is not.

    The writer wrote a text of any length from a row built in Python, and
    the reader then refused the file.
    """
    from phonometry.io import _catalogue

    assert limit == (
        _catalogue._MAX_PROSE if field_name == "note" else _catalogue._MAX_TEXT
    )
    good = (_foams(**{field_name: "x" * limit}), "Foams.")
    past = (_foams(**{field_name: "x" * (limit + 1)}), "Foams.")
    issue = _refused_past_the_edge(tmp_path, suffix, good, past)
    if suffix == "json":
        assert (issue.file, issue.location) == ("mine.json", f"/rows/0/{field_name}")
    else:
        assert issue.file == "mine.csv"
        assert issue.location.startswith("line 2, column ")
    assert issue.message == (
        f"holds {limit + 1} characters, and a text here holds at most {limit}"
    )
