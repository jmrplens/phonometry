#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A data sheet's absorption and insulation rows, read from a file of one's own.

The notes a reader keeps beside the catalogue are the class's to write: a
practical coefficient off the steps of ISO 11654 or above its cap, a printed
rating the bands do not give. They are noted once, when the file is read,
and never change a cell; an alias or an ``x-`` column is a documented use
and notes nothing.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from phonometry import building, io, materials

if TYPE_CHECKING:
    import pathlib

_HEADER: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "panel-40-alpha",
    "row_type": "PracticalAbsorptionSpectrum",
    "about": "Practical absorption of Panel 40 as its data sheet prints it.",
    "provenance": {
        "kind": "datasheet",
        "document": "Panel 40 technical data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 4",
        "consulted": "2026-09-25",
        "laboratory": "Example Lab",
        "report": "26-015",
        "test_standard": "ISO 354:2003",
    },
    "basis": "measured",
    "csv": {"delimiter": ";", "decimal": ","},
}

_BANDS = ";".join(
    f"practical_absorption_coefficient_{band}"
    for band in (125, 250, 500, 1000, 2000, 4000)
)
_SHEET = (
    f"key;name;mounting;construction_depth_mm;{_BANDS};"
    "weighted_absorption_coefficient;shape_indicator;absorption_class;x-edge\n"
    "e200;Panel 40;E-200;200;0,40;0,70;0,95;1,00;0,95;0,90;0,95;;A;A24\n"
    "a;Panel 40;A;;[n.m.];0,25;0,70;1,05;1,00;0,95;0,60;MH;C;A24\n"
)


def _write_sheet(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "panel-40-alpha.csv"
    path.write_text(_SHEET, encoding="utf-8")
    (tmp_path / "panel-40-alpha.csv.phonometry.json").write_text(
        json.dumps(_HEADER), encoding="utf-8"
    )
    return path


def _read_sheet(tmp_path: pathlib.Path) -> io.Catalogue[Any]:
    path = _write_sheet(tmp_path)
    with pytest.warns(io.CatalogueWarning, match="3 notes"):
        return io.read_catalogue(path, row_type=materials.PracticalAbsorptionSpectrum)


def test_the_guides_sheet_is_read_with_its_cells_as_printed(
    tmp_path: pathlib.Path,
) -> None:
    catalogue = _read_sheet(tmp_path)
    e200 = catalogue["panel-40-alpha/e200"]
    a = catalogue["panel-40-alpha/a"]
    assert e200.construction_depth_mm == 200.0
    assert e200.mounting == "E-200"
    assert a.practical_absorption_coefficient_1000 == 1.05
    assert a.unquantified == {"practical_absorption_coefficient_125": "n.m."}
    assert a.shape_indicator == "MH"
    assert catalogue.extras["panel-40-alpha/a"] == {"x-edge": "A24"}
    assert e200.rating().rating_label == "0.95"
    assert a.rating().rating_label == "0.55(MH)"


def test_the_guides_sheet_notes_the_cap_and_the_rating_that_disagrees(
    tmp_path: pathlib.Path,
) -> None:
    notes = _read_sheet(tmp_path).notes
    assert [note.row_key for note in notes] == ["a", "a", "a"]
    assert all(note.severity == "note" for note in notes)
    assert all(note.location == "line 3" for note in notes)
    messages = [note.message for note in notes]
    assert "at 1000 Hz is printed as 1.05, above the 1.00" in messages[0]
    assert "printed as 0.60 and the bands give 0.55" in messages[1]
    assert "printed as 'C' and the bands give 'D'" in messages[2]


def test_a_sheet_whose_ratings_follow_notes_nothing(tmp_path: pathlib.Path) -> None:
    sheet = _SHEET.replace("1,05;1,00;0,95;0,60;MH;C", "1,00;1,00;0,95;0,55;MH;D")
    path = _write_sheet(tmp_path)
    path.write_text(sheet, encoding="utf-8")
    catalogue = io.read_catalogue(path, row_type=materials.PracticalAbsorptionSpectrum)
    assert catalogue.notes == ()


def _document(row_type: str, row: dict[str, Any]) -> dict[str, Any]:
    header = {k: v for k, v in _HEADER.items() if k != "csv"}
    return {**header, "catalogue": "lab-report", "row_type": row_type, "rows": [row]}


def test_an_alias_and_an_x_column_note_nothing() -> None:
    document = _document(
        "PracticalAbsorptionSpectrum",
        {
            "key": "p",
            "name": "Panel",
            "thickness_cm": 4,
            "practical_absorption_coefficient_500": 0.85,
            "x-code": "P40",
        },
    )
    catalogue = io.parse_catalogue(
        document, row_type=materials.PracticalAbsorptionSpectrum
    )
    assert catalogue.notes == ()
    assert catalogue["lab-report/p"].thickness_mm == 40.0


def test_an_off_grid_practical_coefficient_is_noted_on_its_digits() -> None:
    document = _document(
        "PracticalAbsorptionSpectrum",
        {"key": "p", "name": "Panel", "practical_absorption_coefficient_500": 0.83},
    )
    with pytest.warns(io.CatalogueWarning, match="off the steps of 0.05"):
        catalogue = io.parse_catalogue(
            document, row_type=materials.PracticalAbsorptionSpectrum
        )
    (note,) = catalogue.notes
    assert note.location == "/rows/0"
    assert catalogue["lab-report/p"].practical_absorption_coefficient_500 == 0.83


def test_a_one_third_octave_report_is_read_and_turned_into_practical() -> None:
    thirds = dict(
        zip(
            (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000),
            (0.12, 0.15, 0.17, 0.21, 0.31, 0.51, 0.54, 0.80, 0.93, 1.05, 1.10),
            strict=True,
        )
    )
    row: dict[str, Any] = {"key": "t", "name": "Panel"}
    row |= {f"absorption_coefficient_{band}": value for band, value in thirds.items()}
    document = _document("ThirdOctaveAbsorptionSpectrum", row)
    catalogue = io.parse_catalogue(
        document, row_type=materials.ThirdOctaveAbsorptionSpectrum
    )
    practical = catalogue["lab-report/t"].practical()
    assert practical.spectrum() == pytest.approx({125: 0.15, 250: 0.35, 500: 0.75})
    assert practical.provenance == catalogue.provenance
    assert "does not follow" in practical.why_missing(
        "practical_absorption_coefficient_1000"
    )


def test_a_sound_reduction_report_notes_a_printed_rw_that_does_not_follow() -> None:
    import reference_data as ref

    bands = (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250)
    bands += (1600, 2000, 2500, 3150)
    row: dict[str, Any] = {
        "key": "w",
        "name": "Wall",
        "weighted_sound_reduction_index_db": 31,
    }
    row |= {
        f"sound_reduction_index_{band}_db": value
        for band, value in zip(bands, ref.ISO717_1_ANNEX_C_R, strict=True)
    }
    document = _document("SoundReductionSpectrum", row)
    with pytest.warns(io.CatalogueWarning, match="Rw is printed as 31"):
        catalogue = io.parse_catalogue(
            document, row_type=building.SoundReductionSpectrum
        )
    assert catalogue["lab-report/w"].rating().rating == 30
    assert catalogue["lab-report/w"].weighted_sound_reduction_index_db == 31.0


def test_an_impact_report_holds_a_declared_bound_and_rates_nothing_it_lacks() -> None:
    document = _document(
        "ImpactImprovementSpectrum",
        {
            "key": "m",
            "name": "Floor mat",
            "ranges": {"weighted_impact_improvement_db": [26, None]},
            "bounded_below": ["weighted_impact_improvement_db"],
            "basis": {"row": "declared"},
        },
    )
    catalogue = io.parse_catalogue(
        document, row_type=building.ImpactImprovementSpectrum
    )
    row = catalogue["lab-report/m"]
    assert catalogue.notes == ()
    assert row.why_missing("weighted_impact_improvement_db") == (
        "the datasheet prints a lower bound of 26 and no value"
    )
    with pytest.raises(ValueError, match="impact_improvement_100_db"):
        row.rating()


@pytest.mark.parametrize(
    "row_type",
    [
        materials.PracticalAbsorptionSpectrum,
        materials.ThirdOctaveAbsorptionSpectrum,
        building.SoundReductionSpectrum,
        building.ImpactImprovementSpectrum,
    ],
    ids=lambda cls: cls.__name__,
)
@pytest.mark.parametrize("suffix", [".json", ".csv"])
def test_every_fiche_type_is_written_and_read_back(
    row_type: type[io.CatalogueRow], suffix: str, tmp_path: pathlib.Path
) -> None:
    band = next(name for name, kind in _numbers(row_type) if "_1000" in name)
    row = row_type(
        name="Specimen",
        source="A test",
        table="own-sheet",
        **{band: 0.5},
        approximate={band},
        basis={"row": "measured"},
        note="as printed",
    )
    provenance = io.Provenance(
        kind="test_report",
        document="Report 1",
        version=None,
        consulted="2026-09-25",
        laboratory="Example Lab",
    )
    paths = io.write_catalogue(
        {"own-sheet/s": row},
        tmp_path / f"own{suffix}",
        catalogue="own-sheet",
        about="One specimen of a laboratory report.",
        provenance=provenance,
    )
    back = io.read_catalogue(paths[0], row_type=row_type)["own-sheet/s"]
    assert getattr(back, band) == 0.5
    assert back.approximate == frozenset({band})
    assert back.note == "as printed"


def _numbers(row_type: type[io.CatalogueRow]) -> list[tuple[str, str]]:
    from phonometry._internal import catalogue as private

    return sorted(
        (name, kind)
        for name, kind in private.field_kinds(row_type).items()
        if kind == "number"
    )
