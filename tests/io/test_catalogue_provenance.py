#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which document a row was read from, and how a refusal names it.

A packaged row cites a page, and ``why_missing`` says "the page". A row read
from a data sheet carries a :class:`~phonometry.io.Provenance`, and the same
sentence names the data sheet: "the datasheet prints an upper bound of ...".
These tests hold the provenance to its fields, and hold every packaged
row's sentences to what they were before the provenance existed, byte for
byte, against a copy of the code that wrote them.
"""

from __future__ import annotations

import dataclasses
import importlib
import pkgutil
from collections.abc import Mapping

import pytest

import phonometry
from phonometry import io
from phonometry._internal import catalogue as private
from phonometry.materials import PorousMaterial, ResilientLayer

_DATASHEET = io.Provenance(
    kind="datasheet",
    document="Panel 40 technical data sheet",
    publisher="Example Acoustics Ltd",
    version="Rev. 4",
    consulted="2026-09-23",
    page="2",
)


def test_the_kinds_are_the_seven_a_document_can_be() -> None:
    assert io.PROVENANCE_KINDS == (
        "datasheet",
        "declaration_of_performance",
        "test_report",
        "measurement",
        "calculation",
        "publication",
        "other",
    )


@pytest.mark.parametrize(
    ("kind", "noun"),
    [
        ("datasheet", "the datasheet"),
        ("declaration_of_performance", "the declaration of performance"),
        ("test_report", "the test report"),
        ("measurement", "the measurement record"),
        ("calculation", "the calculation note"),
        ("publication", "the source"),
        ("other", "the source"),
    ],
)
def test_a_refusal_names_the_document_by_its_kind(kind: str, noun: str) -> None:
    provenance = dataclasses.replace(_DATASHEET, kind=kind)
    assert provenance.noun == noun
    layer = ResilientLayer(
        name="Floor mat",
        source=provenance.cited(),
        provenance=provenance,
        ranges={"dynamic_stiffness_n_m3": (None, 9e6)},
        bounded_above=frozenset({"dynamic_stiffness_n_m3"}),
    )
    assert layer.why_missing("dynamic_stiffness_n_m3") == (
        f"{noun} prints an upper bound of 9e+06 and no value"
    )
    assert layer.why_missing("density_kg_m3").startswith(f"{noun} does not give it")


def test_a_row_without_a_provenance_says_the_page() -> None:
    layer = ResilientLayer(name="Floor mat", source="Hopkins (2007) Table A3")
    assert layer.provenance is None
    assert layer.why_missing("density_kg_m3").startswith("the page does not give it")


def test_the_citation_is_composed_from_the_document() -> None:
    assert _DATASHEET.cited() == (
        "Panel 40 technical data sheet (Example Acoustics Ltd), Rev. 4, p. 2; "
        "consulted 2026-09-23"
    )
    report = io.Provenance(
        kind="test_report",
        document="Sound absorption test",
        version=None,
        consulted="2026-09-23",
        printed_table="Table 2",
        report="26-014",
        laboratory="Example Lab",
    )
    assert report.cited() == (
        "Sound absorption test, no version printed, Table 2; report 26-014 "
        "(Example Lab); consulted 2026-09-23"
    )
    book = io.Provenance(
        kind="publication",
        document="Cox & D'Antonio 3e Table 6.7, PDF page 257 (printed p. 200)",
        version=None,
        consulted="2026-09-23",
    )
    assert book.cited() == book.document


def test_a_field_takes_its_own_standard_over_the_documents() -> None:
    provenance = dataclasses.replace(
        _DATASHEET,
        test_standard="EN 29052-1",
        field_test_standards={"structural_loss_factor": "ISO 4664-1"},
    )
    assert provenance.test_standard_of("structural_loss_factor") == "ISO 4664-1"
    assert provenance.test_standard_of("porosity") == "EN 29052-1"
    assert isinstance(provenance.field_test_standards, Mapping)
    with pytest.raises(TypeError, match="does not support item assignment"):
        provenance.field_test_standards["porosity"] = "x"  # type: ignore[index]


def test_a_provenance_is_frozen_and_not_hashable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError, match="page"):
        _DATASHEET.page = "3"  # type: ignore[misc]
    with pytest.raises(TypeError, match="Provenance"):
        hash(_DATASHEET)


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"kind": "brochure"}, "not one of datasheet"),
        ({"document": " "}, "names its document"),
        ({"version": ""}, "or None"),
        ({"consulted": "2026-9-23"}, "YYYY-MM-DD"),
        ({"consulted": "2026-02-29"}, "YYYY-MM-DD"),
        ({"issued": "2026-13"}, "YYYY-MM"),
        ({"issued": "spring 2026"}, "YYYY-MM"),
        ({"sha256": "0" * 63}, "SHA-256"),
        ({"page": 2}, "not text"),
        ({"field_test_standards": {"porosity": ""}}, "standard as text"),
        ({"field_test_standards": ["porosity"]}, "not a mapping"),
    ],
)
def test_a_provenance_that_does_not_hold_together_is_refused(
    change: dict[str, object], fragment: str
) -> None:
    fields = {
        item.name: getattr(_DATASHEET, item.name)
        for item in dataclasses.fields(_DATASHEET)
    }
    fields.update(change)
    with pytest.raises(io.CatalogueError, match=fragment):
        io.Provenance(**fields)  # type: ignore[arg-type]


def test_the_dates_a_document_prints_are_taken_at_their_precision() -> None:
    for issued in ("2026", "2026-03", "2026-03-31"):
        assert dataclasses.replace(_DATASHEET, issued=issued).issued == issued


def test_a_standard_for_a_field_the_row_does_not_have_is_refused() -> None:
    provenance = dataclasses.replace(
        _DATASHEET, field_test_standards={"porosityy": "ISO 15901-1"}
    )
    with pytest.raises(io.CatalogueError, match="porosityy"):
        PorousMaterial(name="Core", source="x", provenance=provenance)


def test_a_provenance_field_holds_a_provenance() -> None:
    with pytest.raises(io.CatalogueError, match="not a Provenance"):
        PorousMaterial(name="Core", source="x", provenance="Rev. 4")  # type: ignore[arg-type]


def test_a_row_error_in_python_carries_one_issue_at_python() -> None:
    with pytest.raises(io.CatalogueError, match="porosity") as caught:
        PorousMaterial(name="Core", source="x", porosity=1.5)
    (issue,) = caught.value.issues
    assert issue.location == "<Python>"
    assert issue.field == "porosity"
    assert issue.severity == "error"
    assert "a porosity is a fraction" in issue.message


# ---------------------------------------------------------------------------
# Every packaged sentence is what it was
# ---------------------------------------------------------------------------
def _why_missing_before(row: io.CatalogueRow, field_name: str) -> str:
    """``CatalogueRow.why_missing`` as it stood before a row had a provenance.

    A verbatim copy of the method at commit ``d075da188``, kept as the oracle:
    every packaged row carries no provenance, and its sentences must not move
    by a byte now that the method names the document by its kind and quotes
    a converted figure first.
    """
    if getattr(row, field_name) is not None:
        return ""
    if field_name in row.misprinted:
        return row.misprinted[field_name]
    if field_name in row.unquantified:
        return (
            f"the page prints “{row.unquantified[field_name]}” "
            f"where the number would be"
        )
    if field_name in row.not_derivable:
        return row.not_derivable[field_name]
    if field_name in row.ranges:
        low, high = row.ranges[field_name]
        if high is not None and field_name in row.bounded_above:
            return f"the page prints an upper bound of {high:g} and no value"
        if low is not None and field_name in row.bounded_below:
            return f"the page prints a lower bound of {low:g} and no value"
        if low is not None and high is not None:
            return f"the page prints {low:g} to {high:g} and no value"
    if field_name in row.reported:
        listed = ", ".join(
            f"{entry[0]:g} to {entry[1]:g}"
            if isinstance(entry, tuple)
            else f"{entry:g}"
            for entry in row.reported[field_name]
        )
        return f"the page lists {listed} and no single value"
    return (
        "the page does not give it, and it does not follow from the cells that it does"
    )


def _published_rows() -> list[io.CatalogueRow]:
    rows: list[io.CatalogueRow] = []
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if name.startswith("PUBLISHED_") and isinstance(value, Mapping):
                rows += [
                    row for row in value.values() if isinstance(row, io.CatalogueRow)
                ]
    return rows


def test_every_packaged_sentence_is_byte_for_byte_what_it_was() -> None:
    cells = 0
    for row in _published_rows():
        assert row.provenance is None
        for field_name in private._shape(type(row)).numeric:
            if getattr(row, field_name) is None:
                cells += 1
                assert row.why_missing(field_name) == _why_missing_before(
                    row, field_name
                ), (row.table, row.name, field_name)
    assert cells >= 9000
