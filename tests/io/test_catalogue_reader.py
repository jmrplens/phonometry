#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A catalogue file of your own, read into the rows every catalogue hands out.

``io.read_catalogue`` and ``io.parse_catalogue`` read one table: a header
with the document's provenance, and rows whose cells are named as the fields
of the row class the caller passes. These tests read the example of the
design (a data sheet with a declared bound in kPa s/m2 and a laboratory
characterisation on another page), and then break every rule the reader
holds a document to, one at a time, watching each refusal name the file, the
place as a JSON pointer, the row and the field. A document with several
problems is refused once, with all of them.

The manufacturer here is fictitious, as in every example of the repository.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import pathlib
import pkgutil
import sys
import warnings
from collections.abc import Mapping
from typing import Any

import numpy as np
import pytest

import phonometry
from phonometry import fluids, io, materials, solids
from phonometry.building import ImpactInsulation
from phonometry.materials import AbsorptionAreaSpectrum, PorousMaterial

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from check_frozen_constants import mutable_parts  # noqa: E402

_DATASHEET: dict[str, Any] = {
    "kind": "datasheet",
    "document": "Panel 40 technical data sheet",
    "publisher": "Example Acoustics Ltd",
    "version": "Rev. 4",
    "issued": "2026-03",
    "consulted": "2026-09-23",
    "page": "2",
}

_PANEL_40: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "panel-40",
    "row_type": "PorousMaterial",
    "about": (
        "Core of the Panel 40 absorber as its data sheet gives it. Page 2 "
        "declares the airflow resistivity class under CE marking; page 3 "
        "quotes the laboratory characterisation of a 40 mm specimen."
    ),
    "provenance": _DATASHEET,
    "basis": "declared",
    "rows": [
        {
            "key": "core-declared",
            "name": "Panel 40 core",
            "variant": "as declared",
            "thickness_mm": 40,
            "frame_density_kg_m3": 40,
            "ranges": {"flow_resistivity_kpa_s_m2": [5, None]},
            "bounded_below": ["flow_resistivity_kpa_s_m2"],
            "note": "the sheet prints the designation code AFr5",
            "x-product-code": "P40-C",
        },
        {
            "key": "core-lab",
            "name": "Panel 40 core",
            "variant": "40 mm specimen",
            "provenance": {
                "page": "3",
                "printed_table": "Table 2",
                "laboratory": "Example Lab",
                "accreditation": "ENAC 000/LE000",
                "report": "26-014",
                "test_date": "2025-11-04",
                "test_standard": "ISO 9053-1:2018",
            },
            "basis": {
                "row": "measured",
                "youngs_modulus_pa": "calculated",
                "poisson_ratio": "estimated",
            },
            "flow_resistivity_pa_s_m2": 12500,
            "uncertainty": {"flow_resistivity_pa_s_m2": 900},
            "porosity": 0.97,
            "tortuosity": 1.02,
            "approximate": ["tortuosity"],
            "viscous_length_um": 95,
            "thermal_length_um": 190,
            "frame_density_kg_m3": 40,
            "thickness_mm": 40,
            "youngs_modulus_pa": 140000,
            "poisson_ratio": 0.0,
            "unquantified": {"structural_loss_factor": "n.m."},
            "x-product-code": "P40-C",
        },
    ],
}


def _panel() -> dict[str, Any]:
    """A fresh copy of the design's example document."""
    return copy.deepcopy(_PANEL_40)


def _read(document: object) -> io.Catalogue[PorousMaterial]:
    """The example document, or a broken copy of it, read as porous rows."""
    return io.parse_catalogue(
        document,  # type: ignore[arg-type]
        row_type=PorousMaterial,
        label="panel-40.json",
    )


def _issues(document: object) -> tuple[io.CatalogueIssue, ...]:
    """Every issue the reader finds in *document*, which it must refuse."""
    with pytest.raises(io.CatalogueError, match="panel-40.json") as caught:
        _read(document)
    return caught.value.issues


# ---------------------------------------------------------------------------
# The example of the design
# ---------------------------------------------------------------------------
def test_the_example_reads_into_porous_rows_keyed_by_the_catalogue() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mine = _read(_panel())
    assert isinstance(mine, io.Catalogue)
    assert list(mine) == ["panel-40/core-declared", "panel-40/core-lab"]
    assert mine.name == "panel-40"
    assert mine.row_type is PorousMaterial
    assert all(row.table == "panel-40" for row in mine.values())
    assert mine.notes == ()
    assert mine.schema_version == 1


def test_a_declared_bound_in_kilopascals_is_held_as_a_bound_in_pascals() -> None:
    declared = _read(_panel())["panel-40/core-declared"]
    assert declared.flow_resistivity_pa_s_m2 is None
    assert declared.ranges == {"flow_resistivity_pa_s_m2": (5000.0, None)}
    assert declared.bounded_below == frozenset({"flow_resistivity_pa_s_m2"})
    assert declared.converted == {"flow_resistivity_pa_s_m2": ("5", "kPa s/m2")}
    assert not declared.is_derived("flow_resistivity_pa_s_m2")


def test_the_refusal_quotes_the_datasheet_figure_before_the_converted_one() -> None:
    declared = _read(_panel())["panel-40/core-declared"]
    expected = (
        "'Panel 40 core' has no flow_resistivity_pa_s_m2, which 'the caller' "
        "needs: the datasheet prints a lower bound of 5 kPa s/m2 (5000 Pa s/m2) "
        "and no value (Panel 40 technical data sheet (Example Acoustics Ltd), "
        "Rev. 4, p. 2; consulted 2026-09-23)."
    )
    with pytest.raises(ValueError, match="flow_resistivity_pa_s_m2") as caught:
        declared.printed("flow_resistivity_pa_s_m2")
    assert str(caught.value) == expected


def test_the_document_basis_is_the_row_entry_of_a_row_without_one() -> None:
    mine = _read(_panel())
    assert mine["panel-40/core-declared"].basis == {"row": "declared"}
    lab = mine["panel-40/core-lab"]
    assert lab.basis_of("flow_resistivity_pa_s_m2") == "measured"
    assert lab.basis_of("poisson_ratio") == "estimated"


def test_a_row_narrows_the_provenance_and_its_source_says_so() -> None:
    mine = _read(_panel())
    lab = mine["panel-40/core-lab"]
    assert lab.provenance is not None
    assert lab.provenance.page == "3"
    assert lab.provenance.report == "26-014"
    assert lab.provenance.document == "Panel 40 technical data sheet"
    assert lab.source == (
        "Panel 40 technical data sheet (Example Acoustics Ltd), Rev. 4, p. 3, "
        "Table 2; report 26-014 (Example Lab); consulted 2026-09-23"
    )
    assert mine.provenance.page == "2"
    assert mine["panel-40/core-declared"].provenance == mine.provenance


def test_the_shear_modulus_is_derived_and_names_the_bases_it_rests_on() -> None:
    lab = _read(_panel())["panel-40/core-lab"]
    assert lab.is_derived("shear_modulus_pa")
    assert "(calculated)" in lab.derived["shear_modulus_pa"]
    assert "(estimated)" in lab.derived["shear_modulus_pa"]


def test_the_rows_work_where_a_packaged_row_does() -> None:
    lab = _read(_panel())["panel-40/core-lab"]
    medium = lab.medium(np.geomspace(100, 5000, 8))
    assert medium.characteristic_impedance.shape == (8,)
    assert lab.viscous_length_um == 95
    assert lab.printed("porosity") == 0.97


def test_a_row_with_no_value_for_a_cell_a_consumer_needs_is_refused_by_it() -> None:
    declared = _read(_panel())["panel-40/core-declared"]
    frequencies = np.geomspace(100, 5000, 8)
    with pytest.raises(ValueError, match="flow_resistivity_pa_s_m2") as caught:
        declared.medium(frequencies)
    assert "the datasheet prints a lower bound of 5 kPa s/m2" in str(caught.value)


def test_a_column_of_your_own_is_kept_as_text_beside_the_row() -> None:
    mine = _read(_panel())
    assert mine.extras == {
        "panel-40/core-declared": {"x-product-code": "P40-C"},
        "panel-40/core-lab": {"x-product-code": "P40-C"},
    }


def test_a_number_in_a_column_of_your_own_keeps_its_digits() -> None:
    document = _panel()
    document["rows"][0]["x-edge"] = 1.50
    text = json.dumps(document).replace('"x-edge": 1.5', '"x-edge": 1.50')
    mine = _read(text)
    assert mine.extras["panel-40/core-declared"]["x-edge"] == "1.50"


def test_the_text_is_read_from_its_digits_and_hashed() -> None:
    text = json.dumps(_panel())
    mine = _read(text)
    assert mine.file_sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert _read(_panel()).file_sha256 == ""


def test_a_file_is_read_and_hashed_as_its_bytes(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "panel-40.JSON"
    raw = ("\ufeff" + json.dumps(_panel())).encode("utf-8")
    path.write_bytes(raw)
    mine = io.read_catalogue(path, row_type=PorousMaterial)
    assert mine.file_sha256 == hashlib.sha256(raw).hexdigest()
    assert len(mine) == 2


def test_a_catalogue_is_frozen_all_the_way_down() -> None:
    mine = _read(_panel())
    assert list(mutable_parts(mine, "mine")) == []
    for item in ("rows", "extras", "conventions", "notes", "provenance"):
        assert list(mutable_parts(getattr(mine, item), item)) == [], item
    with pytest.raises(AttributeError, match="'name'"):
        mine.name = "other"  # type: ignore[misc]


def test_a_catalogue_equals_a_mapping_of_the_same_rows() -> None:
    mine = _read(_panel())
    assert mine == dict(mine)
    assert _read(_panel()) == mine
    assert repr(mine) == (
        "Catalogue(name='panel-40', row_type=PorousMaterial, rows=2, notes=0)"
    )


# ---------------------------------------------------------------------------
# Joining with the published catalogues
# ---------------------------------------------------------------------------
def test_a_published_catalogue_joins_yours_without_sharing_a_key() -> None:
    mine = _read(_panel())
    joined = materials.PUBLISHED_POROUS | mine
    assert len(joined) == len(materials.PUBLISHED_POROUS) + 2
    assert joined["panel-40/core-lab"] is mine["panel-40/core-lab"]
    both = mine | materials.PUBLISHED_POROUS
    assert list(both)[:2] == list(mine)


def test_a_key_in_both_catalogues_is_refused_at_every_join() -> None:
    mine = _read(_panel())
    joined = materials.PUBLISHED_POROUS | mine
    with pytest.raises(io.CatalogueError, match="panel-40/core-lab"):
        _ = joined | mine


def test_a_join_is_read_only() -> None:
    joined = materials.PUBLISHED_POROUS | _read(_panel())
    with pytest.raises(TypeError, match="item assignment"):
        joined["panel-40/other"] = None  # type: ignore[index]


def test_a_join_with_what_is_not_a_mapping_is_not_one() -> None:
    mine = _read(_panel())
    with pytest.raises(TypeError, match="unsupported operand"):
        _ = mine | 3  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Notes: kept, never acted on
# ---------------------------------------------------------------------------
def test_a_measured_row_without_a_report_or_laboratory_is_noted() -> None:
    document = _panel()
    del document["rows"][1]["provenance"]
    with pytest.warns(io.CatalogueWarning, match="1 note"):
        mine = _read(document)
    (note,) = mine.notes
    assert note.severity == "note"
    assert note.row_key == "core-lab"
    assert note.location == "/rows/1"
    assert "neither a report nor a laboratory" in note.message


@pytest.mark.parametrize("named", ["report", "laboratory"])
def test_a_measured_row_that_names_a_report_or_a_laboratory_is_not_noted(
    named: str,
) -> None:
    document = _panel()
    narrowed = document["rows"][1]["provenance"]
    for key in ("report", "laboratory", "accreditation"):
        if key != named:
            del narrowed[key]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _read(document).notes == ()


def test_a_sentence_where_a_word_goes_is_noted_and_kept() -> None:
    document = _panel()
    sentence = "not measured, because the sample was too thin to test"
    document["rows"][1]["unquantified"] = {"structural_loss_factor": sentence}
    with pytest.warns(io.CatalogueWarning, match="structural_loss_factor"):
        mine = _read(document)
    assert mine["panel-40/core-lab"].unquantified["structural_loss_factor"] == sentence
    assert mine.notes[0].field == "structural_loss_factor"


def test_an_alias_and_a_column_of_your_own_are_not_notes() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _read(_panel()).notes == ()


def test_a_row_class_notes_what_only_it_can_judge() -> None:
    """The reader asks every row for the notes its own class writes."""
    import dataclasses

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Noted(PorousMaterial):
        def _catalogue_notes(self) -> tuple[str, ...]:
            return ("the printed rating does not follow from the bands",)

    document = _panel()
    document["row_type"] = "Noted"
    with pytest.warns(io.CatalogueWarning, match="2 notes"):
        mine = io.parse_catalogue(document, row_type=Noted)
    assert [note.message for note in mine.notes] == [
        "the printed rating does not follow from the bands"
    ] * 2


# ---------------------------------------------------------------------------
# One refusal with every issue in it
# ---------------------------------------------------------------------------
def test_every_problem_of_a_document_is_raised_at_once() -> None:
    document = _panel()
    document["rows"][0]["porosity"] = "0,97"
    document["rows"][1]["tortuosity"] = True
    document["rows"][1]["x-bad"] = [1, 2]
    issues = _issues(document)
    assert [issue.location for issue in issues] == [
        "/rows/0/porosity",
        "/rows/1/tortuosity",
        "/rows/1/x-bad",
    ]
    assert issues[0].row_key == "core-declared"
    assert issues[0].field == "porosity"
    assert str(issues[0]) == (
        "panel-40.json: /rows/0/porosity (row 'core-declared'): expected a "
        "number, got the text '0,97'; JSON numbers use a decimal point"
    )


def test_the_message_counts_the_issues_and_lists_the_first_twenty() -> None:
    document = _panel()
    document["rows"] = [
        {"key": f"row-{index}", "name": "Panel", "porosity": "x"} for index in range(25)
    ]
    with pytest.raises(io.CatalogueError, match="25 problems") as caught:
        _read(document)
    assert len(caught.value.issues) == 25
    assert "and 5 more" in str(caught.value)


def test_a_refused_document_builds_no_row() -> None:
    document = _panel()
    document["rows"][1]["porosity"] = 1.5
    (issue,) = _issues(document)
    assert issue.location == "/rows/1/porosity"
    assert "porosity is a fraction from 0 to 1" in issue.message


def test_the_contract_of_a_clean_row_is_reported_beside_the_problems_of_another() -> (
    None
):
    """A fixed file meets no problem the refusal did not already name."""
    document = _panel()
    document["rows"][0]["porosity"] = "0,97"
    document["rows"][1]["frame_density_kg_m3"] = -40
    issues = _issues(document)
    assert [issue.location for issue in issues] == [
        "/rows/0/porosity",
        "/rows/1/frame_density_kg_m3",
    ]
    assert "never negative" in issues[1].message


def test_a_row_provenance_that_fails_hides_no_other_row() -> None:
    document = _panel()
    document["rows"][0]["frame_density_kg_m3"] = -40
    document["rows"][1]["provenance"]["test_date"] = 5
    issues = _issues(document)
    assert [issue.location for issue in issues] == [
        "/rows/0/frame_density_kg_m3",
        "/rows/1/provenance/test_date",
    ]


def test_a_document_key_that_fails_hides_no_row() -> None:
    document = _broken("/about", "")
    document["rows"][1]["frame_density_kg_m3"] = -40
    issues = _issues(document)
    assert [issue.location for issue in issues] == [
        "/about",
        "/rows/1/frame_density_kg_m3",
    ]


def test_a_row_standard_narrows_the_document_standards_field_by_field() -> None:
    document = _panel()
    document["provenance"]["field_test_standards"] = {
        "structural_loss_factor": "ISO 4664-1"
    }
    document["rows"][1]["provenance"]["field_test_standards"] = {"porosity": "ISO 4590"}
    mine = _read(document)
    lab = mine["panel-40/core-lab"].provenance
    assert lab is not None
    assert lab.field_test_standards == {
        "structural_loss_factor": "ISO 4664-1",
        "porosity": "ISO 4590",
    }
    assert lab.test_standard_of("structural_loss_factor") == "ISO 4664-1"
    assert lab.test_standard_of("porosity") == "ISO 4590"
    assert lab.test_standard_of("tortuosity") == "ISO 9053-1:2018"
    declared = mine["panel-40/core-declared"].provenance
    assert declared is not None
    assert declared.field_test_standards == {"structural_loss_factor": "ISO 4664-1"}


@pytest.mark.parametrize(
    ("row_type", "written", "message"),
    [
        (
            materials.ResilientLayer,
            "dynamic_stiffness_mn_per_m3",
            "'mn_per_m3' is not a unit this reader converts; write "
            "dynamic_stiffness_n_m3 (N/m3) or dynamic_stiffness_mn_m3 (MN/m3)",
        ),
        (
            PorousMaterial,
            "fibre_diameter_distribution_paramter",
            "no field 'fibre_diameter_distribution_paramter' on PorousMaterial; "
            "did you mean 'fibre_diameter_distribution_parameter'?",
        ),
        (
            solids.SolidMaterial,
            "longitudinal_speed_bar_m_s",
            "no field 'longitudinal_speed_bar_m_s' on SolidMaterial; did you mean "
            "'longitudinal_speed_m_s'?",
        ),
        (
            PorousMaterial,
            "thickness_average",
            "no field 'thickness_average' on PorousMaterial",
        ),
    ],
)
def test_a_wrong_unit_is_told_apart_from_a_misspelt_field(
    row_type: type[io.CatalogueRow], written: str, message: str
) -> None:
    """The message about units is kept for a name that differs in its unit alone."""
    document = _document(row_type.__name__, {"key": "a", "name": "A", written: 1.0})
    with pytest.raises(io.CatalogueError, match=written) as caught:
        io.parse_catalogue(document, row_type=row_type, label="mine.json")
    (issue,) = caught.value.issues
    assert issue.location == f"/rows/0/{written}"
    assert issue.message == message


def test_a_figure_under_another_unit_keeps_the_digits_the_file_writes() -> None:
    """The record of a converted figure quotes it as printed, never as a float."""
    document = _panel()
    row = document["rows"][1]
    del row["flow_resistivity_pa_s_m2"], row["uncertainty"], row["thickness_mm"]
    row["flow_resistivity_kpa_s_m2"] = 12.5
    row["thickness_cm"] = 4
    text = json.dumps(document)
    for written, printed in (
        ('"flow_resistivity_kpa_s_m2": 12.5,', '"flow_resistivity_kpa_s_m2": 12.50,'),
        ('"thickness_cm": 4}', '"thickness_cm": 4e0}'),
        (
            '"flow_resistivity_kpa_s_m2": [5, null]',
            '"flow_resistivity_kpa_s_m2": [5.00, null]',
        ),
    ):
        assert text.count(written) == 1, written
        text = text.replace(written, printed)
    mine = _read(text)
    lab = mine["panel-40/core-lab"]
    assert lab.converted == {
        "flow_resistivity_pa_s_m2": ("12.50", "kPa s/m2"),
        "thickness_mm": ("4e0", "cm"),
    }
    assert lab.flow_resistivity_pa_s_m2 == 12500.0
    assert lab.thickness_mm == 40.0
    declared = mine["panel-40/core-declared"]
    assert declared.converted["flow_resistivity_pa_s_m2"] == ("5.00", "kPa s/m2")
    assert declared.why_missing("flow_resistivity_pa_s_m2").startswith(
        "the datasheet prints a lower bound of 5.00 kPa s/m2 (5000 Pa s/m2)"
    )


def _broken(path: str, value: object) -> dict[str, Any]:
    """The example with the member at *path* set to *value*, or removed."""
    document = _panel()
    *parents, last = path.strip("/").split("/")
    node: Any = document
    for part in parents:
        node = node[int(part)] if isinstance(node, list) else node[part]
    if value is _REMOVE:
        del node[int(last) if isinstance(node, list) else last]
    elif isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value
    return document


_REMOVE = object()


@pytest.mark.parametrize(
    ("path", "value", "location", "fragment"),
    [
        # the header
        ("/schema", "phonometry-calibration", "/schema", "not 'phonometry-catalogue'"),
        ("/schema_version", 2, "/schema_version", "upgrade phonometry"),
        ("/schema_version", True, "/schema_version", "not a whole number"),
        ("/schema_version", 1.5, "/schema_version", "not a whole number"),
        ("/schema_version", 0, "/schema_version", "the first version is 1"),
        ("/row_type", "SolidMaterial", "/row_type", "row_type=PorousMaterial"),
        ("/about", "", "/about", "is empty"),
        ("/basis", "estimate", "/basis", "not one of measured"),
        ("/conventions", "a legend", "/conventions", "not a list of texts"),
        ("/csv", {"delimiter": ";"}, "/csv", "only the header beside a CSV file"),
        ("/rows", [], "/rows", "at least one"),
        ("/about", _REMOVE, "", "needs a top-level 'about'"),
        # the name
        ("/catalogue", "acme-2026-rev4", "/catalogue", "'acme-rev4-2026'"),
        ("/catalogue", "Panel 40", "/catalogue", "not a catalogue name"),
        ("/catalogue", "en-12354-1-2017-annex-c", "/catalogue", "packaged table"),
        # the provenance
        ("/provenance/kind", "brochure", "/provenance/kind", "not one of datasheet"),
        ("/provenance/consulted", "23/09/2026", "/provenance/consulted", "YYYY-MM-DD"),
        ("/provenance/consulted", "2026-02-30", "/provenance/consulted", "YYYY-MM-DD"),
        ("/provenance/issued", "March 2026", "/provenance/issued", "YYYY-MM"),
        ("/provenance/sha256", "abc", "/provenance/sha256", "not a SHA-256"),
        ("/provenance/version", _REMOVE, "/provenance", "write null"),
        ("/provenance/version", "", "/provenance/version", "or None"),
        ("/provenance/source", "x", "/provenance/source", "has no 'source'"),
        ("/provenance/document", "", "/provenance/document", "names its document"),
        # the rows and their keys
        ("/rows/0/key", "core/declared", "/rows/0/key", "no '/'"),
        ("/rows/0/key", "core declared", "/rows/0/key", "no '/', ':' or space"),
        ("/rows/0/key", "core:declared", "/rows/0/key", "no '/', ':' or space"),
        ("/rows/0/key", "core-lab", "/rows/1/key", "the key of row 0 too"),
        ("/rows/0/key", _REMOVE, "/rows/0", "a key of its own"),
        ("/rows/0/name", _REMOVE, "/rows/0", "needs 'name'"),
        ("/rows/0/name", "", "/rows/0/name", "has no name"),
        ("/rows/0", "a row", "/rows/0", "a row is a JSON object"),
        # cells
        ("/rows/1/porosity", "0,97", "/rows/1/porosity", "decimal point"),
        ("/rows/1/porosity", True, "/rows/1/porosity", "true, which is a flag"),
        ("/rows/1/porosity", [0.97], "/rows/1/porosity", "got a list"),
        ("/rows/1/porosityy", 0.97, "/rows/1/porosityy", "did you mean 'porosity'"),
        (
            "/rows/1/thickness_inch",
            1.5,
            "/rows/1/thickness_inch",
            "'inch' is not a unit",
        ),
        (
            "/rows/1/derived",
            {"porosity": "x"},
            "/rows/1/derived",
            "cells the page prints",
        ),
        (
            "/rows/1/estimated",
            ["porosity"],
            "/rows/1/estimated",
            "an estimate is a basis",
        ),
        ("/rows/1/table", "other", "/rows/1/table", "catalogue's name"),
        ("/rows/1/source", "other", "/rows/1/source", "composed from the provenance"),
        ("/rows/1/x-code", {"a": 1}, "/rows/1/x-code", "holds text or a number"),
        ("/rows/1/x-code", True, "/rows/1/x-code", "holds text or a number"),
        ("/rows/1/x-", "P40", "/rows/1/x-", "not a column name"),
        # hedges
        (
            "/rows/1/approximate",
            ["tortuosityy"],
            "/rows/1/approximate/0",
            "did you mean",
        ),
        (
            "/rows/1/approximate",
            "tortuosity",
            "/rows/1/approximate",
            "not a list of fields",
        ),
        ("/rows/1/ranges", {"porosity": [0.9]}, "/rows/1/ranges/porosity", "two ends"),
        (
            "/rows/1/ranges",
            {"porosity": ["a", 1]},
            "/rows/1/ranges/porosity/0",
            "expected a number",
        ),
        (
            "/rows/1/reported",
            {"tortuosity": []},
            "/rows/1/reported/tortuosity",
            "at least one",
        ),
        (
            "/rows/1/basis",
            {"row": "guessed"},
            "/rows/1/basis/row",
            "not one of measured",
        ),
        (
            "/rows/1/basis",
            {"name": "measured"},
            "/rows/1/basis/name",
            "cannot be named here",
        ),
        (
            "/rows/1/converted",
            {"porosity": ["97"]},
            "/rows/1/converted/porosity",
            "two texts",
        ),
        (
            "/rows/1/unquantified",
            {"porosity": 3},
            "/rows/1/unquantified/porosity",
            "expected text",
        ),
        (
            "/rows/1/uncertainty",
            {"porosity": "0.01"},
            "/rows/1/uncertainty/porosity",
            "expected a number",
        ),
        # the row contract, found in the pass and located
        (
            "/rows/1/misprinted",
            {"porosity": "the page prints 9.7"},
            "/rows/1/porosity",
            "misprinted says",
        ),
        (
            "/rows/1/bounded_above",
            ["porosity"],
            "/rows/1/bounded_above",
            "has no range",
        ),
        (
            "/rows/1/converted",
            {"shear_modulus_pa": ["1", "psi"]},
            "/rows/1/converted/shear_modulus_pa",
            "holds nothing",
        ),
        (
            "/rows/1/carried",
            {"shear_modulus_pa": "the row above"},
            "/rows/1/carried/shear_modulus_pa",
            "holds nothing",
        ),
        (
            "/rows/0/bounded_below",
            ["thickness_mm"],
            "/rows/0/bounded_below",
            "has no range",
        ),
        (
            "/rows/0/ranges",
            {"flow_resistivity_kpa_s_m2": [None, 5]},
            "/rows/0/ranges/flow_resistivity_kpa_s_m2",
            "missing an end the page prints",
        ),
        (
            "/rows/1/frame_density_kg_m3",
            -40,
            "/rows/1/frame_density_kg_m3",
            "never negative",
        ),
        # the row's provenance
        (
            "/rows/1/provenance/document",
            "Other",
            "/rows/1/provenance/document",
            "another catalogue file",
        ),
        (
            "/rows/1/provenance/kind",
            "test_report",
            "/rows/1/provenance/kind",
            "another catalogue file",
        ),
        (
            "/rows/1/provenance/pages",
            "3",
            "/rows/1/provenance/pages",
            "did you mean 'page'",
        ),
        (
            "/rows/1/provenance/field_test_standards",
            {"porosityy": "ISO 4638"},
            "/rows/1/provenance/field_test_standards/porosityy",
            "did you mean",
        ),
    ],
)
def test_a_document_that_breaks_a_rule_is_refused_where_it_breaks_it(
    path: str, value: object, location: str, fragment: str
) -> None:
    document = _broken(path, value)
    issues = _issues(document)
    located = [issue for issue in issues if issue.location == location]
    assert located, [str(issue) for issue in issues]
    assert any(fragment in issue.message for issue in located), [
        issue.message for issue in located
    ]
    assert all(issue.file == "panel-40.json" for issue in issues)
    assert all(issue.severity == "error" for issue in issues)


# ---------------------------------------------------------------------------
# What only text can hold
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "location", "fragment"),
    [
        ('{"schema": NaN}', "/schema", "NaN is not JSON"),
        ('{"schema": "a", "schema": "b"}', "/", "names 'schema' twice"),
        ("{", "line 1, column 2", "this is not JSON"),
        ("[1, 2]", "", "one JSON object"),
    ],
)
def test_text_that_is_not_strict_json_is_refused(
    text: str, location: str, fragment: str
) -> None:
    issues = _issues(text)
    assert any(
        issue.location == location and fragment in issue.message for issue in issues
    ), [str(issue) for issue in issues]


def test_a_nan_inside_a_row_is_refused_by_its_pointer() -> None:
    text = json.dumps(_panel()).replace('"porosity": 0.97', '"porosity": Infinity')
    issues = _issues(text)
    messages = [
        issue.message for issue in issues if issue.location == "/rows/1/porosity"
    ]
    assert "Infinity is not JSON and not a number any page prints" in messages
    assert "expected a number, got Infinity, which is not a finite number" in messages


@pytest.mark.parametrize(
    ("value", "said"),
    [(None, "null"), (3, "the number 3"), (["a"], "a list"), ({}, "an object")],
)
def test_a_text_field_says_what_it_got_instead(value: object, said: str) -> None:
    (issue,) = _issues(_broken("/rows/1/variant", value))
    assert issue.location == "/rows/1/variant"
    assert issue.row_key == "core-lab"
    assert issue.message == f"expected text, got {said}"


def test_a_name_written_twice_in_a_row_is_refused() -> None:
    text = json.dumps(_panel()).replace(
        '"porosity": 0.97', '"porosity": 0.97, "porosity": 0.5'
    )
    issues = _issues(text)
    assert any(
        issue.location == "/rows/1" and "'porosity' twice" in issue.message
        for issue in issues
    )


def test_a_nan_from_a_mapping_is_refused_as_it_is_from_text() -> None:
    document = _broken("/rows/1/porosity", float("nan"))
    issues = _issues(document)
    assert issues[0].location == "/rows/1/porosity"
    assert "not a finite number" in issues[0].message


def test_a_number_too_large_for_a_float_is_refused() -> None:
    text = json.dumps(_panel()).replace('"porosity": 0.97', '"porosity": 1e400')
    issues = _issues(text)
    assert "not a finite number" in issues[0].message


@pytest.mark.parametrize("character", ["\x00", "\x1b", "\r", "\u202e", "\u2066"])
def test_a_control_character_or_a_reordering_mark_is_refused(character: str) -> None:
    document = _broken("/rows/1/note", f"Panel{character}40")
    issues = _issues(document)
    assert issues[0].location == "/rows/1/note"
    assert f"U+{ord(character):04X}" in issues[0].message


def test_a_tab_and_a_line_feed_are_text() -> None:
    document = _broken("/rows/1/note", "first line\n\tsecond line")
    assert _read(document)["panel-40/core-lab"].note == "first line\n\tsecond line"


def test_a_name_is_read_in_its_composed_form() -> None:
    """The same word, composed or decomposed, is one name to the searches."""
    decomposed = "Lana de roca co\u0301ncava"
    document = _broken("/rows/1/name", decomposed)
    row = _read(document)["panel-40/core-lab"]
    assert row.name == "Lana de roca cóncava"


def test_a_text_past_its_length_is_refused() -> None:
    document = _broken("/rows/1/variant", "x" * 2001)
    issues = _issues(document)
    assert "at most 2000" in issues[0].message


def test_a_document_nested_past_six_levels_is_refused() -> None:
    document = _broken("/rows/1/reported", {"tortuosity": [[[1.0, 1.1]]]})
    issues = _issues(document)
    assert any("nests at most 6" in issue.message for issue in issues)


def test_a_document_nested_past_what_a_reader_follows_is_refused() -> None:
    text = "[" * 100_000 + "]" * 100_000
    (issue,) = _issues(text)
    assert "nests deeper than a reader follows" in issue.message


def test_a_file_past_sixteen_mebibytes_is_refused_before_it_is_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "huge.json"
    with path.open("wb") as handle:
        handle.truncate(16 * 1024 * 1024 + 1)

    def never(self: pathlib.Path) -> bytes:
        raise AssertionError(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", never)
    with pytest.raises(io.CatalogueError, match="huge.json: is 16777217 bytes"):
        io.read_catalogue(path, row_type=PorousMaterial)


def test_text_past_sixteen_mebibytes_is_refused_before_it_is_decoded() -> None:
    text = json.dumps(_panel()) + " " * (16 * 1024 * 1024)
    with pytest.raises(io.CatalogueError, match="panel-40.json: is 1677"):
        _read(text)


def test_text_that_is_not_utf8_is_refused(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "latin.json"
    path.write_bytes(json.dumps(_panel()).replace("Panel", "Panél").encode("latin-1"))
    with pytest.raises(io.CatalogueError, match="save it as UTF-8"):
        io.read_catalogue(path, row_type=PorousMaterial)


def test_more_rows_than_a_catalogue_holds_are_refused() -> None:
    document = _panel()
    document["rows"] = [{"key": "a", "name": "A"}] * 50_001
    issues = _issues(document)
    assert "at most 50000" in issues[0].message


# ---------------------------------------------------------------------------
# The call itself
# ---------------------------------------------------------------------------
def test_a_fluid_is_not_a_row_type() -> None:
    document = _panel()
    with pytest.raises(TypeError, match="Gas.ideal_state"):
        io.parse_catalogue(document, row_type=fluids.Fluid)  # type: ignore[type-var]


def test_a_row_type_must_be_a_row_class() -> None:
    document = _panel()
    with pytest.raises(TypeError, match="row_type is <class 'dict'>"):
        io.parse_catalogue(document, row_type=dict)  # type: ignore[type-var]


def test_a_document_must_be_text_or_a_mapping() -> None:
    with pytest.raises(TypeError, match="parse_catalogue reads"):
        io.parse_catalogue(b"{}", row_type=PorousMaterial)  # type: ignore[arg-type]


def test_a_file_must_be_named_json_or_csv(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "panel-40.txt"
    with pytest.raises(ValueError, match=r"'panel-40\.txt' ends in neither"):
        io.read_catalogue(path, row_type=PorousMaterial)


def test_a_json_document_takes_no_header_path(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "panel-40.json"
    with pytest.raises(ValueError, match="header_path is the header of a CSV file"):
        io.read_catalogue(path, row_type=PorousMaterial, header_path="h.json")


def test_an_os_error_passes_untouched(tmp_path: pathlib.Path) -> None:
    with pytest.raises(FileNotFoundError, match=r"missing\.json"):
        io.read_catalogue(tmp_path / "missing.json", row_type=PorousMaterial)


def test_the_class_the_file_names_is_never_imported() -> None:
    document = _panel()
    document["row_type"] = "os.system"
    document["rows"][0]["x-module"] = "subprocess"
    before = set(sys.modules)
    issues = _issues(document)
    assert set(sys.modules) == before
    assert issues[0].location == "/row_type"


def _published_catalogues() -> dict[tuple[str, str], Any]:
    """Every PUBLISHED_* mapping of every public package, by package and name."""
    found: dict[tuple[str, str], Any] = {}
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if name.startswith("PUBLISHED_") and isinstance(value, Mapping):
                found[module.name, name] = value
    return found


def test_reading_leaves_every_published_catalogue_as_it_was(
    tmp_path: pathlib.Path,
) -> None:
    published = {
        where: (value, dict(value)) for where, value in _published_catalogues().items()
    }
    assert len(published) >= 20
    path = tmp_path / "panel-40.json"
    path.write_text(json.dumps(_panel()), encoding="utf-8")
    listing = sorted(tmp_path.iterdir())
    io.read_catalogue(path, row_type=PorousMaterial)
    _read(_panel())
    _ = materials.PUBLISHED_POROUS | _read(_panel())
    assert sorted(tmp_path.iterdir()) == listing
    for (package, name), (value, copy_before) in published.items():
        assert getattr(importlib.import_module(f"phonometry.{package}"), name) is value
        assert dict(value) == copy_before


# ---------------------------------------------------------------------------
# Other row classes
# ---------------------------------------------------------------------------
def _document(row_type: str, *rows: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "mine",
        "row_type": row_type,
        "about": "A table of my own.",
        "provenance": {
            "kind": "measurement",
            "document": "Laboratory notebook 7",
            "version": None,
            "consulted": "2026-09-23",
            "laboratory": "Example Lab",
        },
        "rows": list(rows),
    }


def test_a_flag_is_true_or_false_and_nothing_else() -> None:
    good = _document(
        "ImpactInsulation", {"key": "a", "name": "Floor", "has_section_drawing": True}
    )
    row = io.parse_catalogue(good, row_type=ImpactInsulation)["mine/a"]
    assert row.has_section_drawing is True
    bad = _document(
        "ImpactInsulation", {"key": "a", "name": "Floor", "has_section_drawing": 1}
    )
    with pytest.raises(
        io.CatalogueError, match="has_section_drawing .*: expected true or false"
    ):
        io.parse_catalogue(bad, row_type=ImpactInsulation)


def test_a_whole_number_field_takes_a_whole_number() -> None:
    bad = _document("NonlinearityParameter", {"key": "a", "name": "Water", "year": 1.5})
    with pytest.raises(io.CatalogueError, match="year .*: expected a whole number"):
        io.parse_catalogue(bad, row_type=fluids.NonlinearityParameter)


def test_sabins_per_thousand_cubic_feet_need_what_they_are_per() -> None:
    bad = _document(
        "AbsorptionAreaSpectrum",
        {"key": "air", "name": "Air", "absorption_area_2000_ft2_per_1000_ft3": 2.3},
    )
    with pytest.raises(
        io.CatalogueError, match="needs per written beside it"
    ) as caught:
        io.parse_catalogue(bad, row_type=AbsorptionAreaSpectrum)
    assert caught.value.issues[0].location == (
        "/rows/0/absorption_area_2000_ft2_per_1000_ft3"
    )


def test_a_name_two_fields_could_take_is_refused_where_it_is_written() -> None:
    import dataclasses

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Board(io.CatalogueRow):
        thickness_mm: float | None = None
        thickness_m: float | None = None

    document = _document("Board", {"key": "a", "name": "Board", "thickness_cm": 4})
    with pytest.raises(io.CatalogueError, match="'thickness_cm' could be") as caught:
        io.parse_catalogue(document, row_type=Board)
    (issue,) = caught.value.issues
    assert issue.location == "/rows/0/thickness_cm"
    assert "'thickness_m' or 'thickness_mm'" in issue.message


# ---------------------------------------------------------------------------
# A row read from a file where a packaged row goes
# ---------------------------------------------------------------------------
def test_a_gas_of_your_own_closes_its_state() -> None:
    document = _document(
        "Gas",
        {
            "key": "n2",
            "name": "Nitrogen",
            "molar_mass_kg_mol": 0.028,
            "heat_capacity_ratio": 1.4,
        },
        {
            "key": "x",
            "name": "Gas X",
            "molar_mass_kg_mol": 0.03,
            "unquantified": {"heat_capacity_ratio": "n.a."},
        },
    )
    gases = io.parse_catalogue(document, row_type=fluids.Gas)
    state = gases["mine/n2"].ideal_state(
        temperature_c=20.0, static_pressure_pa=101325.0
    )
    # c = sqrt(gamma R T / M), R the molar gas constant of the 2019 SI
    molar_gas_constant = 6.02214076e23 * 1.380649e-23
    expected = math.sqrt(1.4 * molar_gas_constant * 293.15 / 0.028)
    assert state.speed_of_sound == pytest.approx(expected, rel=1e-12)
    unknown = gases["mine/x"]
    with pytest.raises(ValueError, match="heat_capacity_ratio") as caught:
        unknown.ideal_state(temperature_c=20.0, static_pressure_pa=101325.0)
    assert "the measurement record prints “n.a.” where the number would be" in str(
        caught.value
    )


def test_a_spectrum_of_your_own_is_rated_as_a_packaged_one() -> None:
    bands = (250, 500, 1000, 2000, 4000)
    measured = dict(zip(bands, (0.55, 0.9, 1.0, 0.95, 0.9), strict=True))
    cells = {
        f"absorption_coefficient_{band}": value for band, value in measured.items()
    }
    document = _document(
        "AbsorptionSpectrum",
        {"key": "p40", "name": "Panel 40", **cells},
        {
            "key": "p50",
            "name": "Panel 50",
            **{name: value for name, value in cells.items() if "4000" not in name},
            "unquantified": {"absorption_coefficient_4000": "n.m."},
        },
    )
    spectra = io.parse_catalogue(document, row_type=materials.AbsorptionSpectrum)
    panel = spectra["mine/p40"]
    assert panel.spectrum() == measured
    at = list(bands)
    rating = materials.weighted_absorption(panel.values_at(at))
    assert rating.alpha_w == pytest.approx(0.85)
    assert rating.absorption_class == "B"
    other = spectra["mine/p50"]
    with pytest.raises(ValueError, match="absorption_coefficient_4000") as caught:
        other.values_at(at)
    assert "prints “n.m.” where the number would be" in str(caught.value)


def test_a_resilient_layer_of_your_own_carries_a_floor() -> None:
    document = _document(
        "ResilientLayer",
        {"key": "a", "name": "Underlay A", "dynamic_stiffness_mn_m3": 9},
        {
            "key": "b",
            "name": "Underlay B",
            "ranges": {"dynamic_stiffness_mn_m3": [None, 9]},
            "bounded_above": ["dynamic_stiffness_mn_m3"],
        },
    )
    layers = io.parse_catalogue(document, row_type=materials.ResilientLayer)
    layer = materials.resilient_layer(layers["mine/a"])
    assert layer is layers["mine/a"]
    # f0 = (1/2 pi) sqrt(s'/m'), EN 29052-1 Formula 2
    assert layer.natural_frequency(100.0) == pytest.approx(
        math.sqrt(9e6 / 100.0) / (2 * math.pi), rel=1e-12
    )
    bound = materials.resilient_layer(layers["mine/b"])
    with pytest.raises(ValueError, match="dynamic_stiffness_n_m3") as caught:
        bound.natural_frequency(100.0)
    assert "prints an upper bound of 9 MN/m3 (9000000 N/m3) and no value" in str(
        caught.value
    )


def test_a_row_of_a_measurement_names_its_laboratory_in_the_source() -> None:
    document = _document(
        "SolidMaterial", {"key": "a", "name": "Board", "density_kg_m3": 860}
    )
    row = io.parse_catalogue(document, row_type=solids.SolidMaterial)["mine/a"]
    assert row.source == (
        "Laboratory notebook 7, no version printed; laboratory Example Lab; "
        "consulted 2026-09-23"
    )
    assert row.provenance is not None
    assert row.provenance.noun == "the measurement record"
