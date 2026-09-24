#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The row every published catalogue hands out, as ``phonometry.io`` publishes it.

Every ``PUBLISHED_*`` table of every package is a mapping of rows built on
one base, and a caller holding a row has to be able to name its type, catch
what its constructor raises, and ask the same questions of any row whatever
package it came from. These tests hold the base to that: it is published
from one place, every row class built on it has the same shape (frozen,
keyword-only, no ``__slots__``), and the three hedges that say how a served
number relates to the page (``basis``, ``converted``, ``carried``) answer the
same way on every row.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
from types import MappingProxyType

import pytest

import phonometry
from phonometry import io
from phonometry._internal import catalogue as private


def _row_classes() -> list[type[io.CatalogueRow]]:
    """Every row class the public packages define on the shared base."""
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.ispkg and not module.name.startswith("_"):
            importlib.import_module(f"phonometry.{module.name}")
    found: list[type[io.CatalogueRow]] = []
    pending = [io.CatalogueRow]
    while pending:
        cls = pending.pop()
        for subclass in cls.__subclasses__():
            if subclass.__module__.startswith("phonometry."):
                found.append(subclass)
                pending.append(subclass)
    return sorted(found, key=lambda cls: cls.__qualname__)


ROW_CLASSES = _row_classes()


def test_the_row_types_are_published_from_io() -> None:
    """Seven names, one owner, and the same objects the catalogues are built on."""
    for name in (
        "CatalogueRow",
        "BandedRow",
        "CatalogueError",
        "CatalogueIssue",
        "Provenance",
        "CATALOGUE_BASES",
        "PROVENANCE_KINDS",
    ):
        assert name in io.__all__, name
        assert getattr(io, name) is getattr(private, name), name


def test_the_catalogue_file_names_are_published_from_io() -> None:
    """The reader, the writer, what they return and what they warn with.

    ``CatalogueWarning`` is defined in a private module, which the test that
    every warning is published does not walk, so it is named here.
    """
    from phonometry.io import _catalogue

    for name in (
        "Catalogue",
        "CatalogueWarning",
        "read_catalogue",
        "parse_catalogue",
        "write_catalogue",
    ):
        assert name in io.__all__, name
        assert getattr(io, name) is getattr(_catalogue, name), name
    assert issubclass(io.CatalogueWarning, phonometry.PhonometryWarning)
    assert "CATALOGUE_SCHEMA" not in io.__all__
    assert "CATALOGUE_SCHEMA_VERSION" not in io.__all__


def test_the_bases_are_the_five_a_source_can_claim() -> None:
    assert io.CATALOGUE_BASES == (
        "measured",
        "declared",
        "calculated",
        "estimated",
        "extended",
    )
    assert isinstance(io.CATALOGUE_BASES, tuple)


def test_a_catalogue_error_is_a_value_error() -> None:
    """The data is wrong, not the call, and a caller may catch either."""
    assert issubclass(io.CatalogueError, ValueError)


def test_every_published_row_class_is_found() -> None:
    """The walk sees the twenty row classes the packages publish today."""
    names = {cls.__name__ for cls in ROW_CLASSES}
    assert {
        "SolidMaterial",
        "OrthotropicWood",
        "PlateauMaterial",
        "DampingMaterial",
        "DampingTreatment",
        "SolidNonlinearity",
        "NonlinearityParameter",
        "Carpet",
        "ResilientMaterial",
        "ResilientLayer",
        "PorousMaterial",
    } <= names
    assert len(ROW_CLASSES) >= 20


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_row_class_is_frozen_and_keyword_only(cls: type) -> None:
    """A row is built by naming its cells, never by their position.

    ``OrthotropicWood`` and ``PlateauMaterial`` took their own fields by
    position, seven and three of them, while every other row took none, so
    the same call read two ways depending on the class.
    """
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen  # type: ignore[attr-defined]
    positional = [
        parameter.name
        for parameter in inspect.signature(cls).parameters.values()
        if parameter.kind is not inspect.Parameter.KEYWORD_ONLY
    ]
    assert positional == []


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_no_row_class_is_slotted(cls: type) -> None:
    """A slotted dataclass breaks a zero-argument ``super()`` inside it.

    ``slots=True`` builds a new class, and the ``__class__`` cell of a method
    that calls ``super()`` still points at the old one, so on the Python 3.13
    releases that predate the fix (3.13.5 is one) a ``__post_init__`` that
    defers to the base raises ``TypeError`` when the row is built. The
    project admits every 3.13 release. Seven row classes carried it; none
    may.
    """
    assert "__slots__" not in vars(cls)


@pytest.mark.parametrize("cls", ROW_CLASSES, ids=lambda cls: cls.__name__)
def test_every_field_of_every_row_class_is_classified(cls: type) -> None:
    """Number, flag, text, set or mapping: no field escapes the row contract.

    ``typing.get_type_hints`` could not resolve these classes on its own,
    because the modules import ``Mapping`` for the type checker only; the
    contract supplies it, so every field is classified by its resolved type
    and never by the text of its annotation.
    """
    shape = private._shape(cls)
    names = [item.name for item in dataclasses.fields(cls)]
    assert [name for name, _ in shape.checks] == names
    frozen = set(names) - shape.values
    assert {"approximate", "bounded_above", "ranges", "basis", "carried"} <= frozen
    assert shape.texts >= {"name", "source", "table", "variant", "group", "note"}
    assert not shape.numeric & shape.texts
    assert shape.numeric <= shape.values


def test_a_flag_is_a_kind_of_its_own() -> None:
    """``has_section_drawing`` is neither a number nor a text."""
    from phonometry.building import ImpactInsulation
    from phonometry.fluids import NonlinearityParameter

    shape = private._shape(ImpactInsulation)
    assert "has_section_drawing" in shape.values - shape.numeric - shape.texts
    assert "year" in private._shape(NonlinearityParameter).numeric


@pytest.mark.parametrize("word", ["estimate", "Measured", ""])
def test_a_basis_outside_the_five_words_is_refused(word: str) -> None:
    """A misspelt estimate would otherwise reach the page as a printed number."""
    fields = {"name": "Panel core", "source": "a datasheet", "basis": {"row": word}}

    with pytest.raises(io.CatalogueError, match="the basis of 'row' is"):
        io.CatalogueRow(**fields)  # type: ignore[arg-type]


def test_basis_answers_for_the_field_then_the_row_then_not_at_all() -> None:
    from phonometry.solids import SolidMaterial

    row = SolidMaterial(
        name="Panel core",
        source="a datasheet",
        basis={"row": "measured", "poisson_ratio": "estimated"},
    )
    assert row.basis_of("poisson_ratio") == "estimated"
    assert row.basis_of("density_kg_m3") == "measured"
    assert SolidMaterial(name="x", source="y").basis_of("density_kg_m3") == ""


def test_a_converted_or_carried_value_is_not_derived() -> None:
    """The number is the page's in both cases; the library computed nothing."""
    from phonometry.solids import SolidMaterial

    row = SolidMaterial(
        name="x",
        source="y",
        density_kg_m3=1150.0,
        youngs_modulus_pa=2.0e6,
        poisson_ratio=0.45,
        converted={"youngs_modulus_pa": ("290", "psi")},
        carried={"density_kg_m3": "carried down from the row above"},
        derived={"poisson_ratio": "from the other cells"},
    )
    assert not row.is_derived("youngs_modulus_pa")
    assert not row.is_derived("density_kg_m3")
    assert row.is_derived("poisson_ratio")


def test_the_three_new_hedges_are_frozen_mappings() -> None:
    from phonometry.materials import PorousMaterial

    row = PorousMaterial(
        name="x",
        source="y",
        thickness_mm=40.0,
        ranges={"flow_resistivity_pa_s_m2": (5000.0, None)},
        bounded_below=["flow_resistivity_pa_s_m2"],
        basis={"row": "declared"},
        converted={"flow_resistivity_pa_s_m2": ["5", "kPa s/m2"]},
        carried={"thickness_mm": "from the row above"},
    )
    for mapping in (row.basis, row.converted, row.carried):
        assert isinstance(mapping, MappingProxyType)
    assert row.converted["flow_resistivity_pa_s_m2"] == ("5", "kPa s/m2")
    assert row.bounded_below == frozenset({"flow_resistivity_pa_s_m2"})


@pytest.mark.parametrize("gone", ["estimated", "is_estimate", "is_estimated"])
def test_the_estimate_has_one_spelling(gone: str) -> None:
    """The solids and the woods each spelled it their own way; now ``basis``."""
    from phonometry.solids import OrthotropicWood, SolidMaterial

    for cls in (SolidMaterial, OrthotropicWood):
        assert not hasattr(cls, gone), f"{cls.__name__}.{gone}"
    assert "estimated" not in {
        field.name for field in dataclasses.fields(SolidMaterial)
    }
