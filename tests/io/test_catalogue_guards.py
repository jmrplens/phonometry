#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Guards that keep the catalogue reader closed over what the package adds.

Three classes of mistake would slip past the reader's own tests the day they
are made: a new row class the reader cannot read, from a JSON document or
from a CSV file; a new kind of field the CSV front end would refuse as an
unknown column; and a new packaged table whose name a caller's catalogue
could already hold. Each guard below walks what the package publishes rather
than a list, so the class is closed.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import pathlib
import pkgutil
import re

import pytest

import phonometry
from phonometry import io
from phonometry._internal import catalogue as private
from phonometry.io import _catalogue, _catalogue_csv


def _published_row_classes() -> list[type[io.CatalogueRow]]:
    """Every row class a public package exports, the bases included."""
    found: dict[str, type[io.CatalogueRow]] = {}
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if inspect.isclass(value) and issubclass(value, io.CatalogueRow):
                found[value.__qualname__] = value
    return [found[name] for name in sorted(found)]


ROW_CLASSES = _published_row_classes()


def test_the_walk_finds_the_row_classes() -> None:
    names = {cls.__name__ for cls in ROW_CLASSES}
    assert {"CatalogueRow", "BandedRow", "PorousMaterial", "SolidMaterial"} <= names
    assert len(ROW_CLASSES) >= 22


def _one_row(cls: type[io.CatalogueRow]) -> dict[str, object]:
    """A row of *cls* that fills its first numeric field, if it has one."""
    row: dict[str, object] = {"key": "a", "name": "Specimen A"}
    kinds = private.field_kinds(cls)
    numeric = sorted(
        name for name, kind in kinds.items() if kind in ("number", "whole")
    )
    if numeric:
        row[numeric[0]] = 1 if kinds[numeric[0]] == "whole" else 0.5
    return row


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_published_row_class_is_read_from_a_one_row_document(
    cls: type[io.CatalogueRow], tmp_path: pathlib.Path
) -> None:
    """Guard (a): no row class the package publishes escapes the reader.

    Read from a file, so the text, its printed digits and the row class go
    through the whole path a caller's file takes.
    """
    row = _one_row(cls)
    document = {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "guard",
        "row_type": cls.__name__,
        "about": "One row, to show the reader reads the class.",
        "provenance": {
            "kind": "other",
            "document": "A test of the reader",
            "version": None,
            "consulted": "2026-09-23",
        },
        "rows": [row],
    }
    path = tmp_path / "guard.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    catalogue = io.read_catalogue(path, row_type=cls)
    read = catalogue["guard/a"]
    assert type(read) is cls
    for name, value in row.items():
        if name != "key":
            assert getattr(read, name) == value


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_published_row_class_is_read_from_a_one_row_sheet(
    cls: type[io.CatalogueRow], tmp_path: pathlib.Path
) -> None:
    """Guard (a), for a CSV file: no row class escapes the CSV front end."""
    row = _one_row(cls)
    header = {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "guard",
        "row_type": cls.__name__,
        "about": "One row, to show the CSV reader reads the class.",
        "provenance": {
            "kind": "other",
            "document": "A test of the reader",
            "version": None,
            "consulted": "2026-09-25",
        },
        "csv": {"delimiter": ";", "decimal": ","},
    }
    path = tmp_path / "guard.csv"
    cells = [str(value).replace(".", ",") for value in row.values()]
    path.write_text(f"{';'.join(row)}\n{';'.join(cells)}\n", encoding="utf-8")
    (tmp_path / "guard.csv.phonometry.json").write_text(
        json.dumps(header), encoding="utf-8"
    )
    read = io.read_catalogue(path, row_type=cls)["guard/a"]
    assert type(read) is cls
    for name, value in row.items():
        if name != "key":
            assert getattr(read, name) == value


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_field_is_a_csv_column_or_is_sent_where_it_is_written(
    cls: type[io.CatalogueRow],
) -> None:
    """Every field of every row class is a column, or its refusal says where it goes.

    A field is a column of the sheet, a mark written in the cell itself, a
    form only a JSON document writes, or one the library writes; never a
    name the sheet refuses as unknown, which is what a new kind of field
    the CSV front end does not know would come out as.
    """
    reader = _catalogue._Reader(cls, _catalogue._Issues("guard"))
    for item in dataclasses.fields(cls):
        role, _, problem = _catalogue_csv._Sheet.role(item.name, reader)
        assert role or problem, item.name
        assert not problem.startswith("no field"), (item.name, problem)
        assert "did you mean" not in problem, (item.name, problem)


def _data_files() -> list[pathlib.Path]:
    root = pathlib.Path(phonometry.__file__).parent
    return sorted(root.glob("**/data/*.json"))


def test_every_packaged_table_has_a_name_no_catalogue_of_yours_can_take() -> None:
    """Guard (c): every packaged table's name is of the reserved form.

    A caller's catalogue can never be named like one, so a key of theirs and
    a key of a packaged table never meet, today or after an update adds a
    table, and checking it reads no packaged table.
    """
    files = _data_files()
    assert len(files) >= 80
    free = [path.name for path in files if not _catalogue._RESERVED.match(path.stem)]
    assert free == []


def test_the_reserved_form_is_wide_enough_for_a_standard() -> None:
    """A table of a standard's annex is reserved like a book's table."""
    reserved = _catalogue._RESERVED
    for name in (
        "en-12354-1-2017-annex-c",
        "iso-354-2003-table-1",
        "acme-2026-rev4",
        "cox-2017-table-c3",
    ):
        assert reserved.match(name), name
    for name in ("panel-40", "panel-40-alpha", "iso-3382-2-lab", "acme-rev4-2026"):
        assert not reserved.match(name), name


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_field_of_every_row_class_has_a_kind(cls: type[io.CatalogueRow]) -> None:
    """Guard (d): each field is a number, a flag, text, a set, a mapping or the provenance."""
    kinds = private.field_kinds(cls)
    assert set(kinds) == {item.name for item in dataclasses.fields(cls)}
    assert set(kinds.values()) <= {
        "number",
        "whole",
        "flag",
        "text",
        "set",
        "mapping",
        "provenance",
    }
    assert kinds["provenance"] == "provenance"


def test_a_catalogue_name_is_the_documented_pattern() -> None:
    assert re.fullmatch(_catalogue._NAME.pattern, "panel-40")
    assert not re.fullmatch(_catalogue._NAME.pattern, "Panel-40")
    assert not re.fullmatch(_catalogue._NAME.pattern, "x" * 65)
