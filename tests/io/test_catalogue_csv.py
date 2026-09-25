#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A catalogue as a spreadsheet saves it: a CSV file and its JSON header.

``io.read_catalogue`` reads a ``.csv`` file with the JSON header beside it,
and ``io.write_catalogue`` writes the pair. The rows go through the same
pass as a JSON document's, so these tests hold the CSV front end to what is
its own: the dialect the header declares and nothing guessed, the closed
grammar of a cell and every refusal of it, the columns a first line may
name, each problem placed at its line and its column, the formula guard, the
byte order mark, the limits, and the round trip of every published table a
CSV file can hold, with the others refused at the pointer of what it cannot.

The manufacturer here is fictitious, as in every example of the repository.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import json
import pathlib
import pkgutil
import sys
import warnings
from collections.abc import Mapping
from typing import Any

import pytest

import phonometry
from phonometry import io, materials
from phonometry.building import ImpactInsulation
from phonometry.io import _catalogue_csv
from phonometry.materials import (
    AbsorptionAreaSpectrum,
    AbsorptionSpectrum,
    PorousMaterial,
)

_HEADER: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "ceiling-tiles",
    "row_type": "AbsorptionSpectrum",
    "about": "Octave-band Sabine coefficients a fictitious data sheet prints.",
    "provenance": {
        "kind": "datasheet",
        "document": "Example tile data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 1",
        "consulted": "2026-09-25",
        "laboratory": "Example Lab",
    },
    "basis": "measured",
    "csv": {"delimiter": ";", "decimal": ","},
}

_BANDS = (125, 250, 500, 1000, 2000, 4000)
_COLUMNS = ";".join(
    ["key", "name", "mounting", *(f"absorption_coefficient_{band}" for band in _BANDS)]
)
_TILES = (
    f"{_COLUMNS}\n"
    "e400;Example tile;E400;0,45;0,62;0,78;0,90;0,94;0,91\n"
    "a;Example tile;A;0,10;0,25;0,55;0,80;0,85;0,80\n"
)


def _header(**changes: object) -> dict[str, Any]:
    """The tile sheet's header, with *changes* made to its top level."""
    header = copy.deepcopy(_HEADER)
    header.update(changes)
    return header


def _sheet(
    folder: pathlib.Path,
    text: str = _TILES,
    header: Mapping[str, Any] | None = None,
    name: str = "tiles.csv",
) -> pathlib.Path:
    """A CSV file of *text* with its header beside it."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    beside = folder / f"{name}.phonometry.json"
    beside.write_text(
        json.dumps(_HEADER if header is None else header), encoding="utf-8"
    )
    return path


def _read(
    path: pathlib.Path, row_type: type[io.CatalogueRow] = AbsorptionSpectrum
) -> io.Catalogue[Any]:
    return io.read_catalogue(path, row_type=row_type)


def _issues(
    path: pathlib.Path, row_type: type[io.CatalogueRow] = AbsorptionSpectrum
) -> tuple[io.CatalogueIssue, ...]:
    """Every issue the reader finds in the sheet at *path*, which it refuses."""
    with pytest.raises(io.CatalogueError, match=r"tiles\.csv") as caught:
        _read(path, row_type)
    return caught.value.issues


def _one_cell(folder: pathlib.Path, cell: str, decimal: str = ",") -> pathlib.Path:
    """A one-row sheet whose 500 Hz cell is *cell*."""
    delimiter = ";" if decimal == "," else ","
    columns = delimiter.join(["key", "name", "absorption_coefficient_500"])
    quoted = f'"{cell}"' if delimiter in cell else cell
    header = _header(csv={"delimiter": delimiter, "decimal": decimal})
    return _sheet(folder, f"{columns}\na{delimiter}Tile{delimiter}{quoted}\n", header)


# ---------------------------------------------------------------------------
# A sheet reads into the rows a JSON document gives
# ---------------------------------------------------------------------------
def test_a_sheet_reads_into_the_rows_its_json_twin_gives(
    tmp_path: pathlib.Path,
) -> None:
    sheet = _read(_sheet(tmp_path))
    twin = copy.deepcopy(_HEADER)
    del twin["csv"]
    twin["rows"] = [
        {
            "key": "e400",
            "name": "Example tile",
            "mounting": "E400",
            **dict(
                zip(
                    (f"absorption_coefficient_{b}" for b in _BANDS),
                    (0.45, 0.62, 0.78, 0.90, 0.94, 0.91),
                    strict=True,
                )
            ),
        },
        {
            "key": "a",
            "name": "Example tile",
            "mounting": "A",
            **dict(
                zip(
                    (f"absorption_coefficient_{b}" for b in _BANDS),
                    (0.10, 0.25, 0.55, 0.80, 0.85, 0.80),
                    strict=True,
                )
            ),
        },
    ]
    json_twin = io.parse_catalogue(twin, row_type=AbsorptionSpectrum)
    assert dict(sheet) == dict(json_twin)
    assert list(sheet) == ["ceiling-tiles/e400", "ceiling-tiles/a"]
    assert sheet.name == "ceiling-tiles"
    assert sheet.about == _HEADER["about"]
    assert (
        sheet["ceiling-tiles/e400"].basis_of("absorption_coefficient_500") == "measured"
    )
    assert sheet.notes == ()


def test_the_two_files_are_hashed_as_their_bytes(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path)
    sheet = _read(path)
    header = tmp_path / "tiles.csv.phonometry.json"
    assert sheet.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert sheet.header_sha256 == hashlib.sha256(header.read_bytes()).hexdigest()


def test_a_json_document_has_no_header_hash(tmp_path: pathlib.Path) -> None:
    document = _header(rows=[{"key": "a", "name": "Tile"}])
    del document["csv"]
    path = tmp_path / "tiles.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert _read(path).header_sha256 == ""


def test_a_header_elsewhere_is_named_with_header_path(tmp_path: pathlib.Path) -> None:
    (tmp_path / "sheets").mkdir()
    path = tmp_path / "sheets" / "tiles.csv"
    path.write_text(_TILES, encoding="utf-8")
    header = tmp_path / "shared-header.json"
    header.write_text(json.dumps(_HEADER), encoding="utf-8")
    sheet = io.read_catalogue(path, row_type=AbsorptionSpectrum, header_path=header)
    assert len(sheet) == 2
    assert sheet.header_sha256 == hashlib.sha256(header.read_bytes()).hexdigest()


def test_the_extension_is_read_in_any_case(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path, name="TILES.CSV")
    assert len(_read(path)) == 2


def test_a_row_narrows_its_provenance_in_its_own_columns(
    tmp_path: pathlib.Path,
) -> None:
    text = (
        "key;name;absorption_coefficient_500;provenance.report;provenance.test_date;"
        "provenance.page;provenance.test_standard\n"
        "a;Tile;0,55;26-031;2025-11-04;3;ISO 354:2003\n"
        "b;Tile;0,60;;;;\n"
    )
    sheet = _read(_sheet(tmp_path, text))
    first, second = sheet.values()
    assert first.provenance is not None
    assert first.provenance.report == "26-031"
    assert first.provenance.test_date == "2025-11-04"
    assert first.provenance.test_standard == "ISO 354:2003"
    assert first.source == (
        "Example tile data sheet (Example Acoustics Ltd), Rev. 1, p. 3; report "
        "26-031 (Example Lab); consulted 2026-09-25"
    )
    assert second.provenance == sheet.provenance


def test_the_basis_column_is_the_row_entry_and_an_empty_cell_takes_the_document(
    tmp_path: pathlib.Path,
) -> None:
    text = "key;name;absorption_coefficient_500;basis\na;Tile;0,55;declared\nb;Tile;0,60;\n"
    first, second = _read(_sheet(tmp_path, text)).values()
    assert first.basis == {"row": "declared"}
    assert second.basis == {"row": "measured"}


def test_a_column_of_your_own_is_kept_as_text(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500;x-code;x-price\na;Tile;0,55;T-1;12,50\n"
    sheet = _read(_sheet(tmp_path, text))
    assert sheet.extras == {"ceiling-tiles/a": {"x-code": "T-1", "x-price": "12,50"}}


def test_a_byte_order_mark_is_read_past(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path)
    path.write_text(_TILES, encoding="utf-8-sig")
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert list(_read(path)) == ["ceiling-tiles/e400", "ceiling-tiles/a"]


def test_blank_lines_and_lines_of_empty_cells_are_not_rows(
    tmp_path: pathlib.Path,
) -> None:
    text = _TILES.replace("\na;", "\n\n;;;;;;;;\na;") + "\n;;;;;;;;\n"
    assert len(_read(_sheet(tmp_path, text))) == 2


def test_a_quoted_cell_holds_the_delimiter_and_a_line_break(
    tmp_path: pathlib.Path,
) -> None:
    text = 'key;name;note;absorption_coefficient_500\na;"Tile; white";"Two\r\nlines";0,55\n'
    row = _read(_sheet(tmp_path, text))["ceiling-tiles/a"]
    assert row.name == "Tile; white"
    assert row.note == "Two\nlines"


# ---------------------------------------------------------------------------
# The grammar of a cell
# ---------------------------------------------------------------------------
_B = "absorption_coefficient_500"


@pytest.mark.parametrize(
    ("cell", "decimal", "expected"),
    [
        ("0,85", ",", {"value": 0.85}),
        ("0.85", ".", {"value": 0.85}),
        ("  0,85  ", ",", {"value": 0.85}),
        ("+0,85", ",", {"value": 0.85}),
        ("\u22120,5", ",", {"value": -0.5}),
        ("-0.5", ".", {"value": -0.5}),
        ("1e-1", ".", {"value": 0.1}),
        ("1", ",", {"value": 1}),
        ("~0,85", ",", {"value": 0.85, "approximate": True}),
        ("<=0,5", ",", {"ranges": (None, 0.5), "bounded_above": True}),
        ("\u22640,5", ",", {"ranges": (None, 0.5), "bounded_above": True}),
        ("<0.5", ".", {"ranges": (None, 0.5), "bounded_above": True}),
        (">=0,5", ",", {"ranges": (0.5, None), "bounded_below": True}),
        ("\u22650,5", ",", {"ranges": (0.5, None), "bounded_below": True}),
        ("> 0.5", ".", {"ranges": (0.5, None), "bounded_below": True}),
        ("0,30..0,50", ",", {"ranges": (0.3, 0.5)}),
        ("-0.5 .. 0.5", ".", {"ranges": (-0.5, 0.5)}),
        ("~0,30..0,50", ",", {"ranges": (0.3, 0.5), "approximate": True}),
        ("0,85\u00b10,05", ",", {"value": 0.85, "uncertainty": 0.05}),
        ("0.85+/-0.05", ".", {"value": 0.85, "uncertainty": 0.05}),
        ("0,85 \u00b1 0,05", ",", {"value": 0.85, "uncertainty": 0.05}),
        (
            "~0,85\u00b10,05",
            ",",
            {"value": 0.85, "uncertainty": 0.05, "approximate": True},
        ),
        ("[n.m.]", ",", {"unquantified": "n.m."}),
        ("[see note 3]", ",", {"unquantified": "see note 3"}),
        ("", ",", {}),
    ],
)
def test_a_cell_says_one_thing(
    tmp_path: pathlib.Path, cell: str, decimal: str, expected: dict[str, object]
) -> None:
    row = _read(_one_cell(tmp_path, cell, decimal))["ceiling-tiles/a"]
    assert row.absorption_coefficient_500 == expected.get("value")
    assert type(row.absorption_coefficient_500) is type(expected.get("value"))
    assert row.ranges.get(_B) == expected.get("ranges")
    assert row.uncertainty.get(_B) == expected.get("uncertainty")
    assert row.unquantified.get(_B) == expected.get("unquantified")
    assert (_B in row.approximate) is expected.get("approximate", False)
    assert (_B in row.bounded_above) is expected.get("bounded_above", False)
    assert (_B in row.bounded_below) is expected.get("bounded_below", False)


def test_the_design_example_of_a_corrupt_glyph(tmp_path: pathlib.Path) -> None:
    """A text where a number goes is refused, never read as a word, a NaN or 0."""
    (issue,) = _issues(_one_cell(tmp_path, "0.^G", "."))
    assert str(issue) == (
        "tiles.csv, line 2, column C (absorption_coefficient_500), row 'a': '0.^G' "
        "is not a number; if the datasheet prints this text where the number "
        "would be, write it as [0.^G]"
    )
    assert issue.field == _B
    assert issue.row_key == "a"


@pytest.mark.parametrize(
    ("cell", "decimal", "said"),
    [
        ("1.000", ",", '\'1.000\' is ambiguous: the header declares "decimal": ","'),
        ("1,000", ".", '\'1,000\' is ambiguous: the header declares "decimal": "."'),
        ("0,85", ".", "'0,85' writes a decimal comma"),
        ("0.85", ",", "'0.85' writes a decimal point"),
        ("1 000", ",", "separates thousands with a space"),
        ("1\u202f000", ",", "separates thousands with a space"),
        ("~<=0,5", ",", "is an approximate bound, which a CSV cell does not write"),
        ("<=0,5\u00b10,1", ",", "is a bound with a plus-or-minus"),
        ("0,3..0,5\u00b10,1", ",", "is a range with a plus-or-minus"),
        ("true", ",", "'true' is a flag, and the column holds numbers"),
        ("[]", ",", "'[]' holds no word"),
        ("[AFr5", ",", "'[AFr5' opens a bracket it does not close"),
        ("NaN", ",", "'NaN' is not a finite number"),
        ("-inf", ",", "'-inf' is not a finite number"),
        (
            "0,30/0,35",
            ",",
            "holds several numbers; a list of readings with no single value is written only in a JSON catalogue",
        ),
        ("0.30, 0.35", ".", "holds several numbers"),
        ("n.m.", ",", "write it as [n.m.]"),
        ("12 dB", ",", "'12 dB' is not a number"),
    ],
)
def test_a_cell_the_grammar_does_not_read_is_refused_where_it_is(
    tmp_path: pathlib.Path, cell: str, decimal: str, said: str
) -> None:
    path = _one_cell(tmp_path, cell, decimal)
    cells = [issue for issue in _issues(path) if issue.file == "tiles.csv"]
    (issue,) = cells
    assert issue.location == "line 2, column C (absorption_coefficient_500)"
    assert said in issue.message


def test_every_problem_of_every_cell_is_raised_at_once(tmp_path: pathlib.Path) -> None:
    text = f"{_COLUMNS}\ne400;Tile;E400;0.^G;0,62;x;0,90;0,94;0,91\na;Tile;A;0,1;[;0,55;0,80;true;0,80\n"
    issues = _issues(_sheet(tmp_path, text))
    assert [(issue.location.split(" (")[0], issue.row_key) for issue in issues] == [
        ("line 2, column D", "e400"),
        ("line 2, column F", "e400"),
        ("line 3, column E", "a"),
        ("line 3, column H", "a"),
    ]


def test_a_refused_sheet_builds_no_row(tmp_path: pathlib.Path) -> None:
    text = (
        f"{_COLUMNS}\ne400;Tile;E400;0,45;0,62;0,78;0,90;0,94;0,91\na;Tile;A;x;;;;;\n"
    )
    with pytest.raises(io.CatalogueError, match="1 problem, and no row was read"):
        _read(_sheet(tmp_path, text))


@pytest.mark.parametrize("word", ["true", "false", "TRUE", "False"])
def test_a_flag_is_true_or_false_in_any_case(tmp_path: pathlib.Path, word: str) -> None:
    header = _header(row_type="ImpactInsulation")
    text = f"key;name;has_section_drawing\na;Floor;{word}\n"
    row = _read(_sheet(tmp_path, text, header), ImpactInsulation)["ceiling-tiles/a"]
    assert row.has_section_drawing is (word.lower() == "true")


@pytest.mark.parametrize("word", ["1", "0", "s\u00ed", "x", "yes"])
def test_a_flag_is_nothing_else(tmp_path: pathlib.Path, word: str) -> None:
    header = _header(row_type="ImpactInsulation")
    path = _sheet(tmp_path, f"key;name;has_section_drawing\na;Floor;{word}\n", header)
    (issue,) = _issues(path, ImpactInsulation)
    assert issue.location == "line 2, column C (has_section_drawing)"
    assert f"{word!r} is not a flag: a flag is true or false" in issue.message


def test_an_empty_flag_is_the_default(tmp_path: pathlib.Path) -> None:
    header = _header(row_type="ImpactInsulation")
    path = _sheet(tmp_path, "key;name;has_section_drawing\na;Floor;\n", header)
    assert _read(path, ImpactInsulation)["ceiling-tiles/a"].has_section_drawing is False


def test_a_figure_in_another_unit_is_converted_on_its_digits(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(row_type="PorousMaterial", basis="declared")
    text = (
        "key;name;flow_resistivity_kpa_s_m2;flow_resistivity_pa_s_m2;thickness_cm\n"
        "declared;Core;>=5;;\n"
        "lab;Core;12,50;;4\n"
        "own;Core;;12500;\n"
    )
    sheet = _read(_sheet(tmp_path, text, header), PorousMaterial)
    declared, lab, own = sheet.values()
    assert declared.ranges == {"flow_resistivity_pa_s_m2": (5000.0, None)}
    assert declared.converted["flow_resistivity_pa_s_m2"] == ("5", "kPa s/m2")
    assert lab.flow_resistivity_pa_s_m2 == 12500.0
    assert lab.converted["flow_resistivity_pa_s_m2"] == ("12.50", "kPa s/m2")
    assert lab.thickness_mm == 40
    assert own.flow_resistivity_pa_s_m2 == 12500
    assert own.converted == {}


def test_one_cell_filled_under_two_units_is_refused(tmp_path: pathlib.Path) -> None:
    header = _header(row_type="PorousMaterial")
    text = "key;name;thickness_mm;thickness_cm\na;Core;40;4\n"
    (issue,) = _issues(_sheet(tmp_path, text, header), PorousMaterial)
    assert issue.location.startswith("line 2, column ")
    assert "given twice" in issue.message


def test_the_row_contract_is_placed_at_the_cell_it_breaks(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(row_type="PorousMaterial")
    text = "key;name;porosity;frame_density_kg_m3;tortuosity\na;Core;0,95;-5;1\nb;Core;0,9..0,8;;\n"
    issues = _issues(_sheet(tmp_path, text, header), PorousMaterial)
    assert [(issue.location, issue.field) for issue in issues] == [
        ("line 2, column D (frame_density_kg_m3)", "frame_density_kg_m3"),
        ("line 3, column C (porosity)", "porosity"),
    ]


def test_a_missing_name_is_placed_at_its_column(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500\na;;0,55\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2, column B (name)"
    assert "needs 'name'" in issue.message


def test_a_row_without_a_key_is_placed_on_its_line(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500\n;Tile;0,55\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2"
    assert "needs a key of its own" in issue.message


def test_a_key_written_twice_is_placed_at_the_second(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500\na;Tile;0,55\na;Tile;0,60\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 3, column A (key)"
    assert "'a' is the key of row 0 too" in issue.message


def test_a_bad_word_in_the_basis_column_is_placed_there(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500;basis\na;Tile;0,55;guessed\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2, column D (basis)"
    assert "'guessed'" in issue.message


def test_a_problem_in_a_provenance_column_is_placed_there(
    tmp_path: pathlib.Path,
) -> None:
    text = "key;name;absorption_coefficient_500;provenance.report\na;Tile;0,55;26\u2066-031\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2, column D (provenance.report)"
    assert "U+2066" in issue.message


def test_a_control_character_in_a_cell_is_placed_there(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500\na;Tile\u202e;0,55\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2, column B (name)"
    assert "U+202E" in issue.message


def test_a_measured_row_without_a_report_is_noted_on_its_line(
    tmp_path: pathlib.Path,
) -> None:
    header = _header()
    header["provenance"] = {**_HEADER["provenance"], "laboratory": ""}
    path = _sheet(tmp_path, header=header)
    with pytest.warns(io.CatalogueWarning, match="2 notes"):
        sheet = _read(path)
    assert [(note.file, note.location) for note in sheet.notes] == [
        ("tiles.csv", "line 2"),
        ("tiles.csv", "line 3"),
    ]


# ---------------------------------------------------------------------------
# The first line
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("column", "said"),
    [
        ("absorption_coefficent_500", "did you mean 'absorption_coefficient_500'?"),
        ("provenance.reprot", "did you mean 'provenance.report'?"),
        ("kye", "no field 'kye' on AbsorptionSpectrum"),
        ("derived", "derived is what the library works out"),
        ("table", "the catalogue's name is the table of every row it holds"),
        ("estimated", "an estimate is a basis"),
        ("approximate", "a CSV writes an approximate value in its own cell, as ~0.85"),
        ("ranges", "and a bound as <=30 or >=5"),
        ("bounded_above", "an upper bound in its own cell, as <=30"),
        ("uncertainty", "a plus-or-minus in its own cell"),
        ("unquantified", "between brackets, as [AFr5]"),
        ("reported", "reported is written only in a JSON catalogue"),
        ("misprinted", "misprinted is written only in a JSON catalogue"),
        ("not_derivable", "not_derivable is written only in a JSON catalogue"),
        ("carried", "carried is written only in a JSON catalogue"),
        ("converted", "names a column for the unit instead"),
        ("attributed_to", "attributed_to is written only in a JSON catalogue"),
        (
            "basis.absorption_coefficient_500",
            "a basis for one cell is written only in a JSON",
        ),
        (
            "provenance.field_test_standards",
            "field_test_standards is written only in a JSON",
        ),
        ("provenance", "a row narrows its provenance in the columns provenance.page"),
        ("x-", "'x-' is not a column name"),
        ("x-a b", "'x-a b' is not a column name"),
        ("", "has no name"),
        ("na\u202eme", "a mark that reorders text"),
    ],
)
def test_a_column_the_reader_does_not_take_is_refused_on_the_first_line(
    tmp_path: pathlib.Path, column: str, said: str
) -> None:
    text = f"key;name;absorption_coefficient_250;{column}\na;Tile;0,55;1\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.file == "tiles.csv"
    assert issue.location == "line 1, column D"
    assert said in issue.message


def test_a_column_named_twice_is_refused_at_the_second(tmp_path: pathlib.Path) -> None:
    text = "key;name;absorption_coefficient_500;absorption_coefficient_500\na;Tile;0,55;0,60\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 1, column D"
    assert "as column C is; a column is named once" in issue.message


def test_a_sheet_needs_a_key_column(tmp_path: pathlib.Path) -> None:
    (issue,) = _issues(_sheet(tmp_path, "name;absorption_coefficient_500\nTile;0,55\n"))
    assert issue.location == "line 1"
    assert "names no 'key' column" in issue.message


def test_a_sheet_needs_a_column_for_every_field_a_row_needs(
    tmp_path: pathlib.Path,
) -> None:
    (issue,) = _issues(_sheet(tmp_path, "key;absorption_coefficient_500\na;0,55\n"))
    assert issue.location == "line 1"
    assert "names no column that holds 'name'" in issue.message


def test_a_refused_column_hides_no_problem_in_another(tmp_path: pathlib.Path) -> None:
    text = (
        "key;name;absorption_coefficent_500;absorption_coefficient_250\na;Tile;0,55;x\n"
    )
    issues = _issues(_sheet(tmp_path, text))
    assert [issue.location for issue in issues] == [
        "line 1, column C",
        "line 2, column D (absorption_coefficient_250)",
    ]


def test_columns_past_z_are_lettered_as_a_spreadsheet_does() -> None:
    letters = [
        _catalogue_csv._letters(index) for index in (0, 25, 26, 51, 52, 701, 702)
    ]
    assert letters == ["A", "Z", "AA", "AZ", "BA", "ZZ", "AAA"]


# ---------------------------------------------------------------------------
# The lines
# ---------------------------------------------------------------------------
def test_a_line_with_another_number_of_cells_is_refused(tmp_path: pathlib.Path) -> None:
    text = f"{_COLUMNS}\ne400;Tile;E400;0,45;0,62;0,78\n"
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2"
    assert "holds 6 cells, and the first line names 9 columns" in issue.message


def test_an_empty_file_is_refused(tmp_path: pathlib.Path) -> None:
    (issue,) = _issues(_sheet(tmp_path, ""))
    assert issue.location == "line 1"
    assert "the file is empty" in issue.message


def test_a_first_line_and_no_row_is_refused(tmp_path: pathlib.Path) -> None:
    (issue,) = _issues(_sheet(tmp_path, f"{_COLUMNS}\n\n"))
    assert "no row follows" in issue.message


def test_a_quote_left_open_is_refused_on_its_line(tmp_path: pathlib.Path) -> None:
    text = f'{_COLUMNS}\ne400;"Tile"x;E400;0,45;0,62;0,78;0,90;0,94;0,91\n'
    (issue,) = _issues(_sheet(tmp_path, text))
    assert issue.location == "line 2"
    assert "cannot be split into cells" in issue.message


def test_more_rows_than_a_catalogue_holds_are_refused(tmp_path: pathlib.Path) -> None:
    text = "key;name\n" + "".join(f"k{index};Tile\n" for index in range(50_001))
    (issue,) = _issues(_sheet(tmp_path, text))
    assert "heads 50001 rows, and a catalogue holds at most 50000" in issue.message


# ---------------------------------------------------------------------------
# The header and its dialect
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("dialect", "where", "said"),
    [
        ({"delimiter": "|", "decimal": ","}, "/csv/delimiter", "is '|'"),
        ({"delimiter": ";", "decimal": ";"}, "/csv/decimal", "is ';'"),
        ({"delimiter": ";"}, "/csv", "needs 'decimal'"),
        ({"decimal": ","}, "/csv", "needs 'delimiter'"),
        (
            {"delimiter": ",", "decimal": ","},
            "/csv",
            "a decimal comma needs another delimiter",
        ),
        (
            {"delimiter": ";", "decimal": ",", "quote": "'"},
            "/csv/quote",
            "the dialect has no 'quote'",
        ),
        ([";", ","], "/csv", "not an object"),
    ],
)
def test_a_dialect_the_reader_does_not_take_is_refused_in_the_header(
    tmp_path: pathlib.Path, dialect: object, where: str, said: str
) -> None:
    issues = _issues(_sheet(tmp_path, header=_header(csv=dialect)))
    located = [issue for issue in issues if issue.location == where]
    assert located, [str(issue) for issue in issues]
    assert located[0].file == "tiles.csv.phonometry.json"
    assert said in located[0].message


def test_a_header_declares_its_dialect(tmp_path: pathlib.Path) -> None:
    header = _header()
    del header["csv"]
    (issue,) = _issues(_sheet(tmp_path, header=header))
    assert (issue.file, issue.location) == ("tiles.csv.phonometry.json", "")
    assert "declares no dialect" in issue.message


def test_a_header_holds_no_rows(tmp_path: pathlib.Path) -> None:
    header = _header(rows=[{"key": "b", "name": "Tile"}])
    (issue,) = _issues(_sheet(tmp_path, header=header))
    assert (issue.file, issue.location) == ("tiles.csv.phonometry.json", "/rows")


def test_a_problem_of_the_header_is_placed_in_the_header(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(row_type="PorousMaterial", schema_version=2)
    issues = _issues(_sheet(tmp_path, header=header))
    assert [(issue.file, issue.location) for issue in issues] == [
        ("tiles.csv.phonometry.json", "/schema_version"),
    ]
    header = _header(row_type="PorousMaterial")
    header["provenance"] = {**_HEADER["provenance"], "kind": "brochure"}
    issues = _issues(_sheet(tmp_path, header=header))
    assert {(issue.file, issue.location) for issue in issues} == {
        ("tiles.csv.phonometry.json", "/row_type"),
        ("tiles.csv.phonometry.json", "/provenance/kind"),
    }


def test_the_header_problems_come_before_the_cells(tmp_path: pathlib.Path) -> None:
    header = _header(about="")
    text = f"{_COLUMNS}\ne400;Tile;E400;x;0,62;0,78;0,90;0,94;0,91\n"
    issues = _issues(_sheet(tmp_path, text, header))
    assert [issue.file for issue in issues] == [
        "tiles.csv.phonometry.json",
        "tiles.csv",
    ]


def test_every_number_with_the_other_decimal_mark_proposes_it(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(csv={"delimiter": ";", "decimal": "."})
    issues = _issues(_sheet(tmp_path, header=header))
    head = issues[0]
    assert (head.file, head.location) == ("tiles.csv.phonometry.json", "/csv/decimal")
    assert 'declare "decimal": ","' in head.message
    assert len(issues) == 1 + 2 * 6


def test_one_number_with_the_other_mark_proposes_nothing(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(csv={"delimiter": ";", "decimal": "."})
    text = "key;name;absorption_coefficient_250;absorption_coefficient_500\na;Tile;0.25;0,55\n"
    (issue,) = _issues(_sheet(tmp_path, text, header))
    assert issue.location == "line 2, column D (absorption_coefficient_500)"


def test_a_first_line_that_splits_at_another_delimiter_proposes_it(
    tmp_path: pathlib.Path,
) -> None:
    header = _header(csv={"delimiter": ",", "decimal": "."})
    (issue,) = _issues(_sheet(tmp_path, header=header))
    assert (issue.file, issue.location) == (
        "tiles.csv.phonometry.json",
        "/csv/delimiter",
    )
    assert 'splits into 9 at ";"; declare "delimiter": ";"' in issue.message


def test_a_tab_is_a_delimiter(tmp_path: pathlib.Path) -> None:
    header = _header(csv={"delimiter": "\t", "decimal": ","})
    path = _sheet(tmp_path, _TILES.replace(";", "\t"), header)
    assert len(_read(path)) == 2


def test_a_missing_header_is_named(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "tiles.csv"
    path.write_text(_TILES, encoding="utf-8")
    with pytest.raises(FileNotFoundError, match=r"tiles\.csv\.phonometry\.json"):
        _read(path)


def test_a_calibration_sidecar_is_not_a_header(tmp_path: pathlib.Path) -> None:
    sidecar = {
        "schema": "phonometry-calibration",
        "schema_version": 1,
        "calibration_factor": 1.0,
    }
    path = _sheet(tmp_path, header=sidecar)
    with pytest.raises(
        io.CatalogueError, match="is the calibration sidecar of an audio file"
    ):
        _read(path)


def test_a_header_that_is_not_json_is_refused(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path)
    (tmp_path / "tiles.csv.phonometry.json").write_text("{", encoding="utf-8")
    with pytest.raises(
        io.CatalogueError, match=r"tiles\.csv\.phonometry\.json, line 1"
    ):
        _read(path)


def test_the_class_the_header_names_is_never_imported(tmp_path: pathlib.Path) -> None:
    header = _header(row_type="os.system")
    text = f"{_COLUMNS};x-module\ne400;Tile;E400;0,45;0,62;0,78;0,90;0,94;0,91;subprocess\n"
    before = set(sys.modules)
    (issue,) = _issues(_sheet(tmp_path, text, header))
    assert set(sys.modules) == before
    assert issue.location == "/row_type"


# ---------------------------------------------------------------------------
# Encodings and limits
# ---------------------------------------------------------------------------
def test_a_sheet_that_is_not_utf8_is_refused(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path)
    path.write_bytes(_TILES.replace("Example", "Ejemplo t\u00e9cnico").encode("cp1252"))
    with pytest.raises(io.CatalogueError, match="save it as CSV UTF-8"):
        _read(path)


def test_a_header_that_is_not_utf8_is_refused(tmp_path: pathlib.Path) -> None:
    path = _sheet(tmp_path)
    beside = tmp_path / "tiles.csv.phonometry.json"
    beside.write_bytes(
        json.dumps(_header(about="Caf\u00e9"), ensure_ascii=False).encode("latin-1")
    )
    with pytest.raises(
        io.CatalogueError, match="tiles.csv.phonometry.json: is not UTF-8"
    ):
        _read(path)


def test_a_sheet_past_sixteen_mebibytes_is_refused_before_it_is_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _sheet(tmp_path)
    with path.open("wb") as handle:
        handle.truncate(16 * 1024 * 1024 + 1)

    def never(self: pathlib.Path) -> bytes:
        raise AssertionError(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", never)
    with pytest.raises(io.CatalogueError, match="tiles.csv: is 16777217 bytes"):
        _read(path)


def test_a_header_past_sixty_four_kibibytes_is_refused_before_it_is_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _sheet(tmp_path, header=_header(about="x" * 70_000))

    def never(self: pathlib.Path) -> bytes:
        raise AssertionError(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", never)
    with pytest.raises(io.CatalogueError, match="at most 65536 bytes"):
        _read(path)


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
def _mine(tmp_path: pathlib.Path) -> io.Catalogue[AbsorptionSpectrum]:
    """The tile sheet, read from a folder of its own under *tmp_path*."""
    folder = tmp_path / "in"
    folder.mkdir()
    return _read(_sheet(folder))


def _document(**row: object) -> dict[str, Any]:
    """A JSON document of the tile sheet's header with one row of *row*."""
    document = _header(rows=[{"key": "a", "name": "Tile", **row}])
    del document["csv"]
    del document["basis"]
    return document


def test_a_sheet_is_written_as_a_csv_file_and_its_header(
    tmp_path: pathlib.Path,
) -> None:
    mine = _mine(tmp_path)
    path = tmp_path / "out.csv"
    written = io.write_catalogue(mine, path, delimiter=";", decimal=",")
    header = tmp_path / "out.csv.phonometry.json"
    assert written == (path, header)
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert raw.count(b"\r\n") == 3
    document = json.loads(header.read_text(encoding="utf-8"))
    assert document["csv"] == {"delimiter": ";", "decimal": ","}
    assert "rows" not in document
    assert document["catalogue"] == "ceiling-tiles"
    back = _read(path)
    assert dict(back) == dict(mine)
    assert back.extras == mine.extras


def test_the_columns_follow_the_row_class_then_the_basis_and_the_provenance(
    tmp_path: pathlib.Path,
) -> None:
    mine = _mine(tmp_path)
    path = tmp_path / "out.csv"
    io.write_catalogue(mine, path, delimiter=";", decimal=",")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == ";".join(
        [
            "key",
            "name",
            *(f"absorption_coefficient_{band}" for band in _BANDS),
            "mounting",
            "basis",
        ]
    )
    assert lines[1] == "e400;Example tile;0,45;0,62;0,78;0,9;0,94;0,91;E400;measured"


def test_a_published_table_is_a_template_in_the_default_dialect(
    tmp_path: pathlib.Path,
) -> None:
    allard = {
        key: row
        for key, row in materials.PUBLISHED_POROUS.items()
        if row.table == "allard-2009-table-13-1"
    }
    path = tmp_path / "template.csv"
    io.write_catalogue(allard, path, catalogue="template-allard")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0].split(",")[:3] == ["key", "name", "note"]
    assert lines[1].startswith("foam,Foam,")
    header = json.loads((tmp_path / "template.csv.phonometry.json").read_text("utf-8"))
    assert header["csv"] == {"delimiter": ",", "decimal": "."}
    assert header["provenance"]["kind"] == "publication"


_FORMULAS = (
    "=SUM(A1)",
    "+1",
    "-x",
    "@me",
    "\tx",
    "'=x",
    "''-x",
    "'s-Hertogenbosch",
    "'",
    "a'b",
)


def test_a_text_a_spreadsheet_would_run_is_written_after_an_apostrophe(
    tmp_path: pathlib.Path,
) -> None:
    document = _header(
        rows=[
            {"key": f"k{index}", "name": text, "note": text, f"x-{index}": text}
            for index, text in enumerate(_FORMULAS)
        ]
    )
    del document["csv"]
    mine = io.parse_catalogue(document, row_type=AbsorptionSpectrum)
    path = tmp_path / "formulas.csv"
    io.write_catalogue(mine, path)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    names = [line.split(",")[1] for line in lines[1:]]
    assert names == [
        "'=SUM(A1)",
        "'+1",
        "'-x",
        "'@me",
        "'\tx",
        "''=x",
        "'''-x",
        "'s-Hertogenbosch",
        "'",
        "a'b",
    ]
    back = _read(path)
    assert [row.name for row in back.values()] == list(_FORMULAS)
    assert [row.note for row in back.values()] == list(_FORMULAS)
    assert back.extras == mine.extras


def test_a_number_is_not_guarded_as_a_formula(tmp_path: pathlib.Path) -> None:
    mine = io.parse_catalogue(_document(**{_B: -0.5}), row_type=AbsorptionSpectrum)
    path = tmp_path / "signed.csv"
    io.write_catalogue(mine, path)
    assert path.read_text(encoding="utf-8-sig").splitlines()[1].endswith(",-0.5")


@pytest.mark.parametrize(
    ("row", "where", "said"),
    [
        (
            {"reported": {_B: [0.3, 0.35]}},
            "/rows/0/reported/absorption_coefficient_500",
            "reported is written only in a JSON catalogue",
        ),
        (
            {"misprinted": {_B: "the page prints 5.5"}},
            "/rows/0/misprinted/absorption_coefficient_500",
            "misprinted is written only",
        ),
        (
            {_B: 0.5, "carried": {_B: "from the row above"}},
            "/rows/0/carried/absorption_coefficient_500",
            "carried is written only",
        ),
        (
            {_B: 0.5, "attributed_to": {"row": "Example Lab"}},
            "/rows/0/attributed_to/row",
            "attributed_to is written only",
        ),
        (
            {_B: 0.5, "basis": {_B: "estimated"}},
            "/rows/0/basis/absorption_coefficient_500",
            "a basis for one cell",
        ),
        (
            {_B: 0.5, "converted": {_B: ["0.5", "sabins"]}},
            "/rows/0/converted/absorption_coefficient_500",
            "converted is written only",
        ),
        (
            {"ranges": {_B: [0.3, 0.5]}, "bounded_above": [_B]},
            "/rows/0/ranges/absorption_coefficient_500",
            "a bound with its other end printed",
        ),
        (
            {_B: 0.4, "ranges": {_B: [0.3, 0.5]}},
            "/rows/0/ranges/absorption_coefficient_500",
            "a value beside a range",
        ),
        (
            {
                "ranges": {_B: [None, 0.5]},
                "bounded_above": [_B],
                "uncertainty": {_B: 0.1},
            },
            "/rows/0/uncertainty/absorption_coefficient_500",
            "a plus-or-minus on a range or a bound",
        ),
        (
            {"ranges": {_B: [None, 0.5]}, "bounded_above": [_B], "approximate": [_B]},
            "/rows/0/approximate/0",
            "an approximate bound",
        ),
        (
            {_B: 0.5, "provenance": {"field_test_standards": {_B: "ISO 354:2003"}}},
            "/rows/0/provenance/field_test_standards",
            "field_test_standards is written only",
        ),
    ],
)
def test_what_a_cell_cannot_hold_is_refused_at_its_pointer(
    tmp_path: pathlib.Path, row: dict[str, object], where: str, said: str
) -> None:
    mine = io.parse_catalogue(_document(**row), row_type=AbsorptionSpectrum)
    path = tmp_path / "out.csv"
    with pytest.raises(io.CatalogueError, match="a CSV file cannot hold") as caught:
        io.write_catalogue(mine, path)
    (issue,) = caught.value.issues
    assert (issue.file, issue.location, issue.row_key) == ("out.csv", where, "a")
    assert said in issue.message
    assert list(tmp_path.iterdir()) == []


def test_an_empty_text_whose_default_says_something_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """An empty cell reads as the default, so "per nothing" cannot be one."""
    document = _document(absorption_area_500_m2=0.5, per="")
    document["row_type"] = "AbsorptionAreaSpectrum"
    mine = io.parse_catalogue(document, row_type=AbsorptionAreaSpectrum)
    assert mine["ceiling-tiles/a"].per == ""
    path = tmp_path / "areas.csv"
    with pytest.raises(io.CatalogueError, match="a CSV file cannot hold") as caught:
        io.write_catalogue(mine, path)
    (issue,) = caught.value.issues
    assert issue.location == "/rows/0/per"
    assert "empty where its default is 'person'" in issue.message


@pytest.mark.parametrize(
    ("delimiter", "decimal", "said"),
    [
        ("|", ".", "delimiter='|'"),
        (";", ";", "decimal=';'"),
        (",", ",", "a decimal comma needs another delimiter"),
    ],
)
def test_a_dialect_a_csv_file_does_not_take_is_refused_before_writing(
    tmp_path: pathlib.Path, delimiter: str, decimal: str, said: str
) -> None:
    mine = _mine(tmp_path)
    target = tmp_path / "out.csv"
    with pytest.raises(ValueError, match=said):
        io.write_catalogue(mine, target, delimiter=delimiter, decimal=decimal)
    assert not target.exists()


def test_a_header_already_there_keeps_the_sheet_from_being_written(
    tmp_path: pathlib.Path,
) -> None:
    mine = _mine(tmp_path)
    header = tmp_path / "out.csv.phonometry.json"
    header.write_text("{}", encoding="utf-8")
    target = tmp_path / "out.csv"
    with pytest.raises(FileExistsError, match="overwrite=True"):
        io.write_catalogue(mine, target)
    assert not target.exists()
    assert header.read_text(encoding="utf-8") == "{}"


def test_a_symbolic_link_at_the_header_is_never_written_through(
    tmp_path: pathlib.Path,
) -> None:
    mine = _mine(tmp_path)
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}", encoding="utf-8")
    (tmp_path / "out.csv.phonometry.json").symlink_to(elsewhere)
    target = tmp_path / "out.csv"
    with pytest.raises(FileExistsError, match="symbolic link"):
        io.write_catalogue(mine, target, overwrite=True)
    assert elsewhere.read_text(encoding="utf-8") == "{}"
    assert not target.exists()


def test_overwrite_replaces_both_files(tmp_path: pathlib.Path) -> None:
    mine = _mine(tmp_path)
    target = tmp_path / "out.csv"
    io.write_catalogue(mine, target)
    io.write_catalogue(mine, target, delimiter="\t", overwrite=True)
    assert "\t" in target.read_text(encoding="utf-8-sig").splitlines()[0]
    assert dict(_read(target)) == dict(mine)


# ---------------------------------------------------------------------------
# Every published table
# ---------------------------------------------------------------------------
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


def _write_sheet(
    rows: dict[str, io.CatalogueRow],
    path: pathlib.Path,
    delimiter: str = ",",
    decimal: str = ".",
) -> io.CatalogueError | None:
    """Write *rows* to a sheet at *path*, or the refusal of what it cannot hold."""
    try:
        io.write_catalogue(
            rows, path, catalogue="copy", delimiter=delimiter, decimal=decimal
        )
    except io.CatalogueError as error:
        return error
    return None


@pytest.mark.parametrize(
    ("mapping", "table", "rows"),
    TABLES,
    ids=[f"{mapping}-{table}" for mapping, table, _ in TABLES],
)
@pytest.mark.parametrize(("delimiter", "decimal"), [(",", "."), (";", ",")])
def test_every_published_table_reads_back_or_is_refused_at_its_pointers(
    tmp_path: pathlib.Path,
    mapping: str,
    table: str,
    rows: dict[str, io.CatalogueRow],
    delimiter: str,
    decimal: str,
) -> None:
    del mapping
    path = tmp_path / f"{table}.csv"
    refusal = _write_sheet(rows, path, delimiter=delimiter, decimal=decimal)
    if refusal is not None:
        assert refusal.issues
        assert all(issue.location.startswith("/rows/") for issue in refusal.issues)
        assert all("JSON" in issue.message for issue in refusal.issues)
        assert list(tmp_path.iterdir()) == []
        return
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        back = io.read_catalogue(path, row_type=type(next(iter(rows.values()))))
    assert [key.partition("/")[2] for key in back] == [
        key.rpartition("/")[2] for key in rows
    ]
    for (key, row), again in zip(rows.items(), back.values(), strict=True):
        for item in dataclasses.fields(row):
            if item.name in ("table", "provenance"):
                continue
            held, read = getattr(row, item.name), getattr(again, item.name)
            assert read == held, (key, item.name)
            assert type(read) is type(held), (key, item.name)
        assert again.source == row.source


def test_most_published_tables_go_into_a_sheet(tmp_path: pathlib.Path) -> None:
    """A floor under how many packaged tables a CSV file holds whole.

    The others print what one cell cannot say (a credit, several readings,
    a figure in a unit no family holds), which the test above holds to a
    refusal at its pointer.
    """
    whole = [
        table
        for index, (_, table, rows) in enumerate(TABLES)
        if _write_sheet(rows, tmp_path / f"{index}.csv") is None
    ]
    assert len(whole) >= 40


def test_a_published_table_is_the_same_rows_from_either_file(
    tmp_path: pathlib.Path,
) -> None:
    rows = {
        key: row
        for key, row in materials.PUBLISHED_ABSORPTION.items()
        if row.table == "arau-1999-table-6-1"
    }
    assert rows
    sheet, document = tmp_path / "t.csv", tmp_path / "t.json"
    fixed = io.Provenance(
        kind="publication", document="A book", version=None, consulted="2026-09-25"
    )
    io.write_catalogue(rows, sheet, catalogue="t", provenance=fixed)
    io.write_catalogue(rows, document, catalogue="t", provenance=fixed)
    assert dict(_read(sheet)) == dict(_read(document))


def test_the_areas_in_sabins_travel_in_their_own_column(tmp_path: pathlib.Path) -> None:
    rows = {
        key: row
        for key, row in materials.PUBLISHED_ABSORPTION_AREAS.items()
        if row.table == "long-2014-table-7-1"
    }
    assert any(row.converted for row in rows.values())
    path = tmp_path / "areas.csv"
    io.write_catalogue(rows, path, catalogue="areas")
    first = path.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "_ft2" in first
    back = _read(path, AbsorptionAreaSpectrum)
    for key, row in rows.items():
        again = back[f"areas/{key.rpartition('/')[2]}"]
        assert again.converted == row.converted
        assert again.per == row.per
