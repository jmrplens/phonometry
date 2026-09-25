#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every ``*_named`` lookup searches the catalogue it is given.

Each published catalogue has a lookup by name, and each takes
``catalogue=``: the rows to search in place of its own ``PUBLISHED_*``. A
caller's catalogue read from a file, the published one joined with it by
``|``, or any mapping of key to row goes there, and the lookup keeps its own
way of matching a name, answers every match in the order the mapping holds
them, and never picks one. A row of another class in the mapping is refused
by its key rather than skipped, because a skipped row would be missing from
the answer under the very name asked for.

The table below names every lookup with the catalogue it searches by
default, and a guard walks what the packages publish, so a new lookup that
does not take ``catalogue=``, or that the table does not list, fails here.

The manufacturer here is fictitious, as in every example of the repository.
"""

from __future__ import annotations

import collections.abc
import dataclasses
import importlib
import inspect
import pkgutil
import typing
from collections.abc import Callable, Mapping
from typing import Any

import pytest

import phonometry
from phonometry import (
    building,
    environment,
    fluids,
    io,
    materials,
    noise_control,
    solids,
)

type Lookup = Callable[..., tuple[io.CatalogueRow, ...]]

#: Every lookup, with the published catalogue it searches by default.
LOOKUPS: dict[str, tuple[Lookup, Mapping[str, io.CatalogueRow]]] = {
    "transmission_loss_named": (
        building.transmission_loss_named,
        building.PUBLISHED_TRANSMISSION_LOSS,
    ),
    "impact_insulation_named": (
        building.impact_insulation_named,
        building.PUBLISHED_IMPACT_INSULATION,
    ),
    "ground_surfaces_named": (
        environment.ground_surfaces_named,
        environment.PUBLISHED_GROUND,
    ),
    "gases_named": (fluids.gases_named, fluids.PUBLISHED_GASES),
    "nonlinearity_named": (fluids.nonlinearity_named, fluids.PUBLISHED_NONLINEARITY),
    "carpets_named": (materials.carpets_named, materials.PUBLISHED_CARPETS),
    "porous_materials_named": (
        materials.porous_materials_named,
        materials.PUBLISHED_POROUS,
    ),
    "absorption_named": (materials.absorption_named, materials.PUBLISHED_ABSORPTION),
    "resistive_sheet_named": (
        materials.resistive_sheet_named,
        materials.PUBLISHED_FLOW_RESISTANCE,
    ),
    "scattering_named": (materials.scattering_named, materials.PUBLISHED_SCATTERING),
    "diffusion_named": (materials.diffusion_named, materials.PUBLISHED_DIFFUSION),
    "predicted_scattering_named": (
        materials.predicted_scattering_named,
        materials.PUBLISHED_PREDICTED_SCATTERING,
    ),
    "resilient_moduli_named": (
        materials.resilient_moduli_named,
        materials.PUBLISHED_RESILIENT_MODULI,
    ),
    "duct_wall_named": (
        noise_control.duct_wall_named,
        noise_control.PUBLISHED_DUCT_TRANSMISSION_LOSS,
    ),
    "solids_named": (solids.solids_named, solids.PUBLISHED_SOLIDS),
    "damping_named": (solids.damping_named, solids.PUBLISHED_DAMPING),
    "damping_treatments_named": (
        solids.damping_treatments_named,
        solids.PUBLISHED_DAMPING_TREATMENTS,
    ),
    "solid_nonlinearity_named": (
        solids.solid_nonlinearity_named,
        solids.PUBLISHED_SOLID_NONLINEARITY,
    ),
    "orthotropic_wood_named": (
        solids.orthotropic_wood_named,
        solids.PUBLISHED_ORTHOTROPIC_WOOD,
    ),
    "plateau_material_named": (
        solids.plateau_material_named,
        solids.PUBLISHED_PLATEAU_DATA,
    ),
}

NAMES = sorted(LOOKUPS)


def _row_type(lookup: Lookup) -> type[io.CatalogueRow] | None:
    """The row class a function answers a tuple of, or ``None``."""
    hints = typing.get_type_hints(lookup, localns={"Mapping": collections.abc.Mapping})
    returned = hints.get("return")
    if typing.get_origin(returned) is not tuple:
        return None
    args = typing.get_args(returned)
    if (
        len(args) == 2
        and args[1] is Ellipsis
        and inspect.isclass(args[0])
        and issubclass(args[0], io.CatalogueRow)
    ):
        return args[0]
    return None


def _published_lookups() -> dict[str, Lookup]:
    """Every public function named ``*_named`` that answers a tuple of rows."""
    found: dict[str, Lookup] = {}
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if (
                name.endswith("_named")
                and inspect.isfunction(value)
                and _row_type(value) is not None
            ):
                found[name] = value
    return found


def _first(published: Mapping[str, io.CatalogueRow]) -> io.CatalogueRow:
    return next(iter(published.values()))


def _stranger(row_type: type[io.CatalogueRow]) -> io.CatalogueRow:
    """A published row of a class that is not *row_type*."""
    for candidate in (
        _first(solids.PUBLISHED_SOLIDS),
        _first(materials.PUBLISHED_POROUS),
    ):
        if not isinstance(candidate, row_type):
            return candidate
    raise AssertionError(row_type)  # pragma: no cover


# ---------------------------------------------------------------------------
# Guard (b): every lookup takes catalogue=, and the table lists every lookup
# ---------------------------------------------------------------------------
def test_every_lookup_the_packages_publish_takes_a_catalogue() -> None:
    """Guard (b): ``catalogue`` is keyword-only and ``None`` by default."""
    published = _published_lookups()
    assert len(published) >= 20
    for name, lookup in published.items():
        parameter = inspect.signature(lookup).parameters.get("catalogue")
        assert parameter is not None, name
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, name
        assert parameter.default is None, name


def test_the_table_here_lists_every_lookup_the_packages_publish() -> None:
    """A lookup the packages add has to join the behaviour tests below."""
    published = _published_lookups()
    assert set(published) == set(LOOKUPS)
    for name, (lookup, _) in LOOKUPS.items():
        assert published[name] is lookup, name


@pytest.mark.parametrize("name", NAMES)
def test_the_published_catalogue_of_the_table_holds_the_lookup_s_rows(
    name: str,
) -> None:
    lookup, published = LOOKUPS[name]
    row_type = _row_type(lookup)
    assert row_type is not None
    assert len(published) > 0
    assert all(type(row) is row_type for row in published.values())


# ---------------------------------------------------------------------------
# What a lookup searches
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", NAMES)
def test_without_a_catalogue_a_lookup_searches_its_published_one(name: str) -> None:
    lookup, published = LOOKUPS[name]
    row = _first(published)
    found = lookup(row.name)
    assert found[0] is row
    assert found == lookup(row.name, catalogue=published)
    assert found == lookup(row.name, catalogue=None)


@pytest.mark.parametrize("name", NAMES)
def test_a_lookup_searches_only_the_catalogue_it_is_given(name: str) -> None:
    lookup, published = LOOKUPS[name]
    row = _first(published)
    assert lookup(row.name, catalogue={"mine/one": row}) == (row,)
    assert lookup(row.name, catalogue={}) == ()


@pytest.mark.parametrize("name", NAMES)
def test_a_lookup_answers_every_match_in_the_order_the_catalogue_holds_them(
    name: str,
) -> None:
    lookup, published = LOOKUPS[name]
    row = _first(published)
    twin = dataclasses.replace(row, variant="a second printing")
    found = lookup(row.name, catalogue={"mine/b": twin, "mine/a": row})
    assert found == (twin, row)
    assert found[0] is twin


@pytest.mark.parametrize("name", NAMES)
def test_a_row_of_another_class_is_refused_by_its_key(name: str) -> None:
    lookup, published = LOOKUPS[name]
    row_type = _row_type(lookup)
    assert row_type is not None
    stranger = _stranger(row_type)
    catalogue = {"mine/one": _first(published), "mine/stranger": stranger}
    expected = (
        f"catalogue= holds a row of class {type(stranger).__name__} under "
        f"'mine/stranger', and {name} reads {row_type.__name__} rows"
    )
    with pytest.raises(TypeError, match=expected):
        lookup("anything", catalogue=catalogue)


@pytest.mark.parametrize("name", NAMES)
def test_a_catalogue_that_is_not_a_mapping_is_refused(name: str) -> None:
    lookup, published = LOOKUPS[name]
    rows = [_first(published)]
    expected = f"{name} takes catalogue= as a mapping of key to row, .*; got list$"
    with pytest.raises(TypeError, match=expected):
        lookup("anything", catalogue=rows)


# ---------------------------------------------------------------------------
# With a catalogue of your own
# ---------------------------------------------------------------------------
_EXAMPLE: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "example-foams",
    "row_type": "PorousMaterial",
    "about": "Two foams from a fictitious data sheet, typed from its page 2.",
    "provenance": {
        "kind": "datasheet",
        "document": "Example foam data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 2",
        "consulted": "2026-09-25",
        "page": "2",
    },
    "basis": "declared",
    "rows": [
        {"key": "grey", "name": "Foam", "variant": "grey", "porosity": 0.98},
        {
            "key": "black",
            "name": "Foam",
            "variant": "black",
            "flow_resistivity_kpa_s_m2": 9.5,
        },
    ],
}


def _mine() -> io.Catalogue[materials.PorousMaterial]:
    return io.parse_catalogue(_EXAMPLE, row_type=materials.PorousMaterial)


def test_a_catalogue_read_from_a_document_is_searched_by_the_same_rule() -> None:
    mine = _mine()
    found = materials.porous_materials_named("foam", catalogue=mine)
    assert [row.variant for row in found] == ["grey", "black"]
    assert found[1].flow_resistivity_pa_s_m2 == 9500.0
    assert found[1].provenance is not None
    assert materials.porous_materials_named("Foam 2", catalogue=mine) == ()


def test_the_published_catalogue_and_yours_are_searched_as_one() -> None:
    mine = _mine()
    published = materials.porous_materials_named("Foam")
    both = materials.porous_materials_named(
        "Foam", catalogue=materials.PUBLISHED_POROUS | mine
    )
    assert both == (*published, *mine.values())
    reversed_join = materials.porous_materials_named(
        "Foam", catalogue=mine | materials.PUBLISHED_POROUS
    )
    assert reversed_join == (*mine.values(), *published)


def test_a_catalogue_of_another_row_class_is_refused_by_its_first_key() -> None:
    mine = _mine()
    expected = (
        "catalogue= holds a row of class PorousMaterial under "
        "'example-foams/grey', and solids_named reads SolidMaterial rows"
    )
    with pytest.raises(TypeError, match=expected):
        solids.solids_named("Foam", catalogue=mine)  # type: ignore[arg-type]


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Batched(materials.PorousMaterial):
    """A caller's own porous row, with a column the library does not have."""

    batch: str = ""


def test_a_row_of_a_subclass_of_your_own_is_searched_like_any_other() -> None:
    row = _Batched.from_printed(
        name="Foam",
        source="Example foam data sheet, Rev. 2, p. 2",
        porosity=0.97,
        batch="26-07",
    )
    found = materials.porous_materials_named("foam", catalogue={"mine/foam": row})
    assert found == (row,)
    assert found[0].batch == "26-07"


def test_a_lookup_leaves_the_catalogue_it_is_given_as_it_was() -> None:
    mine = _mine()
    rows = dict(mine)
    materials.porous_materials_named("Foam", catalogue=mine)
    assert dict(mine) == rows
    assert list(mine) == ["example-foams/grey", "example-foams/black"]
