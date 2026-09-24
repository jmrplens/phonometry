#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every catalogue row checks itself when it is built, whoever builds it.

``CatalogueRow.__post_init__`` holds a row to eleven rules, the same for a
packaged row, a row a reader builds from a file and a row a caller writes by
hand. Each test below builds a row that breaks one rule and watches it be
refused with :class:`~phonometry.io.CatalogueError`, naming the row and the
field; the last ones sweep every published row through the same constructor
and classify every field of every row class.

These are the probes that were accepted before the contract existed: a
density of -5, a ``NaN`` Poisson ratio, a modulus of ``"abc"``, a range on a
field the class does not have, ``Carpet(approximate=[...])`` keeping a list,
and a value served beside the ``misprinted`` hedge that says it is not.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
import typing
from fractions import Fraction
from types import MappingProxyType

import numpy as np
import pytest

from phonometry import io
from phonometry.building import ImpactInsulation, TransmissionLossSpectrum
from phonometry.environment.propagation import GroundSurface
from phonometry.fluids import Gas, NonlinearityParameter
from phonometry.materials import (
    AbsorptionSpectrum,
    Carpet,
    PorousMaterial,
    ResistiveSheet,
)
from phonometry.noise_control import DuctWallSpectrum
from phonometry.solids import DampingTreatment, SolidMaterial

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import catalogue_fingerprint  # noqa: E402
import check_frozen_constants as cfc  # noqa: E402

_SOURCE = "Example Acoustics Ltd, Panel 40 technical data sheet, Rev. 4, p. 2"


def _row(cls: type[io.CatalogueRow], **cells: object) -> io.CatalogueRow:
    """A row of *cls* named and cited, with *cells* on top."""
    return cls(name="Panel 40 core", source=_SOURCE, **cells)


# ---------------------------------------------------------------------------
# Rule 1: a name and a source
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("cells", "missing"),
    [
        ({"name": "", "source": _SOURCE}, "no name"),
        ({"name": "Panel 40 core", "source": "   "}, "no source"),
    ],
)
def test_a_row_without_a_name_or_a_source_is_refused(
    cells: dict[str, str], missing: str
) -> None:
    with pytest.raises(io.CatalogueError, match=missing):
        SolidMaterial(**cells)


def test_a_name_that_is_not_text_is_refused() -> None:
    with pytest.raises(io.CatalogueError, match="name holds 7, which is not text"):
        SolidMaterial(name=7, source=_SOURCE)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "cells",
    [
        {"misprinted": {"porosity": ""}},
        {"not_derivable": {"porosity": "   "}},
        {"unquantified": {"porosity": ""}},
        {"derived": {"porosity": ""}},
        {"porosity": 0.9, "carried": {"porosity": " "}},
        {"attributed_to": {"row": ""}},
        {"thickness_mm": 40.0, "converted": {"thickness_mm": ("", "cm")}},
        {"thickness_mm": 40.0, "converted": {"thickness_mm": ("4", "")}},
    ],
    ids=[
        "misprinted",
        "not_derivable",
        "unquantified",
        "derived",
        "carried",
        "attributed_to",
        "converted-figure",
        "converted-unit",
    ],
)
def test_a_hedge_whose_text_is_empty_is_refused(cells: dict[str, object]) -> None:
    """An empty ``misprinted`` answered ``why_missing`` with ``""`` and hid it."""
    ((hedge, entry),) = ((k, v) for k, v in cells.items() if isinstance(v, dict))
    ((key, _),) = entry.items()
    with pytest.raises(io.CatalogueError, match=f"{hedge} holds no text for {key!r}"):
        _row(PorousMaterial, **cells)


def test_a_hedge_a_subclass_adds_holds_text_too() -> None:
    with pytest.raises(io.CatalogueError, match="borrowed holds no text"):
        _row(SolidMaterial, loss_factor=0.01, borrowed={"loss_factor": ""})


# ---------------------------------------------------------------------------
# Rule 2: every field holds what its annotation says
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), -float("inf"), "abc", "0,97", True, 10**400],
    ids=["nan", "inf", "-inf", "text", "comma", "bool", "huge"],
)
def test_a_numeric_cell_holds_a_finite_number(value: object) -> None:
    with pytest.raises(io.CatalogueError, match=r"poisson_ratio holds .* finite"):
        _row(SolidMaterial, poisson_ratio=value)


def test_an_empty_numeric_cell_holds_none() -> None:
    assert _row(SolidMaterial, poisson_ratio=None).poisson_ratio is None


@pytest.mark.parametrize(
    "value",
    [7800, 7800.0, np.float64(7800.0), Fraction(7800)],
    ids=lambda value: type(value).__name__,
)
def test_a_numeric_cell_takes_any_finite_real_as_it_is(value: object) -> None:
    """An integer stays an integer: the page printed 7800, not 7800.0."""
    assert _row(SolidMaterial, density_kg_m3=value).density_kg_m3 is value


def test_the_probe_the_contract_was_written_for_is_refused() -> None:
    """Density -5, Poisson ratio NaN, modulus "abc": the first named is the type."""
    cells: dict[str, object] = {
        "density_kg_m3": -5.0,
        "youngs_modulus_pa": "abc",
        "poisson_ratio": float("nan"),
    }
    with pytest.raises(io.CatalogueError, match=r"^'Panel 40 core': youngs_modulus"):
        _row(SolidMaterial, **cells)


@pytest.mark.parametrize("value", [1990.5, True, "1990"])
def test_a_whole_number_field_takes_a_whole_number(value: object) -> None:
    with pytest.raises(io.CatalogueError, match=r"year holds .* whole number"):
        _row(NonlinearityParameter, year=value)


def test_a_whole_number_field_takes_one() -> None:
    assert _row(NonlinearityParameter, year=1990).year == 1990


@pytest.mark.parametrize("value", [1, 0, "yes", None])
def test_a_flag_field_takes_true_or_false_and_nothing_else(value: object) -> None:
    with pytest.raises(io.CatalogueError, match=r"has_section_drawing holds .* True"):
        _row(ImpactInsulation, has_section_drawing=value)


@pytest.mark.parametrize("value", [5, None, 0.5])
def test_a_text_field_takes_text(value: object) -> None:
    with pytest.raises(io.CatalogueError, match=r"mounting holds .* which is not text"):
        _row(AbsorptionSpectrum, mounting=value)


def test_a_refused_value_is_quoted_short() -> None:
    """A message quotes a cell, not a page of it."""
    with pytest.raises(io.CatalogueError, match="poisson_ratio holds") as caught:
        _row(SolidMaterial, poisson_ratio="x" * 500)
    assert len(str(caught.value)) < 200


# ---------------------------------------------------------------------------
# Rules 3 and 4: sets and mappings are frozen from their annotations
# ---------------------------------------------------------------------------
def test_a_set_written_as_a_list_is_held_as_a_frozenset() -> None:
    """``Carpet(approximate=[...])`` used to keep the list it was given."""
    row = _row(Carpet, pile_height_mm=6.0, approximate=["pile_height_mm"])
    assert row.approximate == frozenset({"pile_height_mm"})
    assert isinstance(row.approximate, frozenset)


def test_a_solid_bound_below_is_frozen_like_every_other_set() -> None:
    """The solids once froze their sets from a list that left this one out."""
    row = _row(
        SolidMaterial,
        ranges={"density_kg_m3": [400.0, None]},
        bounded_below=["density_kg_m3"],
    )
    assert isinstance(row.bounded_below, frozenset)
    assert row.ranges["density_kg_m3"] == (400.0, None)


def test_a_set_written_as_one_name_is_refused() -> None:
    """``frozenset("porosity")`` would be a set of nine letters."""
    with pytest.raises(io.CatalogueError, match="approximate holds 'porosity'"):
        _row(PorousMaterial, porosity=0.9, approximate="porosity")


@pytest.mark.parametrize(
    ("cells", "fragment"),
    [
        ({"ranges": {"porosity": [0.1, 0.2, 0.3]}}, r"ranges\['porosity'\] holds"),
        ({"ranges": {"porosity": 0.5}}, r"ranges\['porosity'\] holds 0.5"),
        ({"ranges": [("porosity", (0.1, 0.2))]}, "which is not a mapping"),
        ({"converted": {"thickness_mm": "40 mm"}}, r"converted\['thickness_mm'\]"),
        ({"unquantified": {"tortuosity": 3}}, r"unquantified\['tortuosity'\] holds 3"),
        ({"basis": {5: "measured"}}, "basis key holds 5"),
    ],
)
def test_a_hedge_of_the_wrong_shape_is_refused(
    cells: dict[str, object], fragment: str
) -> None:
    with pytest.raises(io.CatalogueError, match=fragment):
        _row(PorousMaterial, thickness_mm=40.0, **cells)


def test_a_row_built_by_hand_is_immutable_all_the_way_down() -> None:
    """Lists and dicts go in; nothing the caller can edit comes out."""
    ranges = {"flow_resistivity_pa_s_m2": [5000.0, 9000.0]}
    row = _row(
        PorousMaterial,
        porosity=0.97,
        ranges=ranges,
        reported={"viscous_length_um": [96.0, [200.0, 450.0]]},
        approximate=["porosity"],
        converted={"flow_resistivity_pa_s_m2": ["5", "kPa s/m2"]},
        attributed_to={"row": "Example Lab"},
    )
    assert list(cfc.mutable_parts(row, "row")) == []
    ranges["flow_resistivity_pa_s_m2"][0] = 1.0
    assert row.ranges["flow_resistivity_pa_s_m2"] == (5000.0, 9000.0)


def test_a_mapping_a_subclass_adds_is_frozen_too() -> None:
    """``SolidMaterial.borrowed`` is frozen by the same rule as the shared ones."""
    row = _row(SolidMaterial, loss_factor=0.01, borrowed={"loss_factor": "steel"})
    assert isinstance(row.borrowed, MappingProxyType)
    with pytest.raises(TypeError):
        row.borrowed["loss_factor"] = "iron"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Rule 5: every hedge names a field of the row
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "hedge",
    [
        "approximate",
        "ranges",
        "bounded_above",
        "reported",
        "unquantified",
        "uncertainty",
        "not_derivable",
        "converted",
        "basis",
        "derived",
        "carried",
        "misprinted",
        "attributed_to",
    ],
)
def test_a_hedge_on_a_field_the_class_does_not_have_is_refused(hedge: str) -> None:
    """``PorousMaterial(ranges={"no_such_field": ...})`` used to be accepted."""
    entry: object = {
        "approximate": ["no_such_field"],
        "bounded_above": ["no_such_field"],
        "ranges": {"no_such_field": (1.0, 2.0)},
        "reported": {"no_such_field": (1.0,)},
        "uncertainty": {"no_such_field": 1.0},
        "converted": {"no_such_field": ("1", "kPa")},
    }.get(hedge, {"no_such_field": "why"})
    cells = {hedge: entry}
    with pytest.raises(io.CatalogueError, match=f"{hedge} names 'no_such_field'"):
        _row(PorousMaterial, **cells)


@pytest.mark.parametrize(
    "hedge",
    ["approximate", "ranges", "unquantified", "uncertainty", "converted"],
)
def test_a_hedge_on_a_number_does_not_name_a_text_field(hedge: str) -> None:
    entry: object = {
        "approximate": ["mounting"],
        "ranges": {"mounting": (1.0, 2.0)},
        "uncertainty": {"mounting": 1.0},
        "converted": {"mounting": ("1", "m")},
    }.get(hedge, {"mounting": "A"})
    cells = {hedge: entry, "mounting": "A"}
    with pytest.raises(io.CatalogueError, match="which is not a numeric field"):
        _row(AbsorptionSpectrum, **cells)


def test_the_hedges_that_may_name_text_do() -> None:
    """Harris misprints a name and gives three descriptions by reference."""
    row = _row(
        ImpactInsulation,
        refers_to_row="31",
        misprinted={"name": "the page prints the name misspelt; ERRATA"},
        carried={"refers_to_row": "the row above"},
        derived={"name": "from the heading"},
        basis={"row": "measured", "impact_insulation_class": "declared"},
        attributed_to={"table": "Harris (1995)", "row": "a lab"},
    )
    assert row.basis_of("name") == "measured"
    assert row.basis_of("impact_insulation_class") == "declared"


@pytest.mark.parametrize(
    ("hedge", "key"),
    [
        ("basis", "name"),
        ("attributed_to", "refers_to_row"),
        ("misprinted", "source"),
        ("carried", "table"),
        ("derived", "has_section_drawing"),
    ],
)
def test_a_hedge_does_not_name_what_is_not_a_cell_it_may_hold(
    hedge: str, key: str
) -> None:
    """A basis or a credit is for a number or the row; a citation is no cell."""
    cells: dict[str, object] = {hedge: {key: "measured"}, "refers_to_row": "31"}
    with pytest.raises(io.CatalogueError, match=f"{hedge} names '{key}'"):
        _row(ImpactInsulation, **cells)


def test_basis_takes_the_row_and_not_the_table() -> None:
    with pytest.raises(io.CatalogueError, match="basis names 'table'"):
        _row(SolidMaterial, basis={"table": "measured"})


def test_borrowed_names_a_numeric_field_of_the_solid() -> None:
    with pytest.raises(io.CatalogueError, match="borrowed names 'no_such_field'"):
        _row(SolidMaterial, borrowed={"no_such_field": "steel"})


# ---------------------------------------------------------------------------
# Rule 6: a bound bounds a range
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("hedge", ["bounded_above", "bounded_below"])
def test_a_bound_on_a_field_with_no_range_is_refused(hedge: str) -> None:
    cells: dict[str, object] = {
        hedge: ["flow_resistivity_pa_s_m2"],
        "flow_resistivity_pa_s_m2": 5000.0,
    }
    with pytest.raises(io.CatalogueError, match=f"{hedge} names .* which has no range"):
        _row(PorousMaterial, **cells)


# ---------------------------------------------------------------------------
# Rule 7: a range is finite, ordered and has the end it printed
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pair", "fragment"),
    [
        ((float("nan"), 2.0), r"ranges\['tortuosity'\]\[0\] holds nan"),
        ((1.0, float("inf")), r"ranges\['tortuosity'\]\[1\] holds inf"),
        ((3.0, 1.5), "runs from 3.0 down to 1.5"),
        ((1.0, None), "missing an end"),
    ],
)
def test_a_range_that_is_not_one_is_refused(
    pair: tuple[float | None, float | None], fragment: str
) -> None:
    with pytest.raises(io.CatalogueError, match=fragment):
        _row(PorousMaterial, ranges={"tortuosity": pair})


def test_a_reading_interval_that_runs_backwards_is_refused() -> None:
    """A ``(low, high)`` among the readings is an interval like any other."""
    with pytest.raises(io.CatalogueError, match="viscous_length_um' runs from 5.0 d"):
        _row(PorousMaterial, reported={"viscous_length_um": (96.0, (5.0, 2.0))})


def test_a_range_of_one_point_is_a_range() -> None:
    row = _row(PorousMaterial, ranges={"tortuosity": (1.5, 1.5)})
    assert row.ranges["tortuosity"] == (1.5, 1.5)


# ---------------------------------------------------------------------------
# Rule 8: readings are finite, an uncertainty is not below zero
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("entries", "fragment"),
    [
        ((25.0, float("nan")), r"reported\['viscous_length_um'\]\[1\] holds nan"),
        ((25.0, (200.0, "450")), r"\[1\]\[1\] holds '450'"),
        ((25.0, (200.0,)), r"\[1\] holds \(200.0,\), which is not a list of 2"),
    ],
)
def test_a_reading_that_is_not_a_finite_number_is_refused(
    entries: tuple[object, ...], fragment: str
) -> None:
    with pytest.raises(io.CatalogueError, match=fragment):
        _row(PorousMaterial, reported={"viscous_length_um": entries})


@pytest.mark.parametrize(
    "cells",
    [
        {"reported": {"viscous_length_um": ()}},
        {
            "reported": {"viscous_length_um": ()},
            "carried": {"viscous_length_um": "the row above"},
        },
    ],
    ids=["alone", "behind-carried"],
)
def test_a_list_of_readings_with_nothing_in_it_is_refused(
    cells: dict[str, object],
) -> None:
    """``why_missing`` read "the page lists  and no single value" for it."""
    with pytest.raises(io.CatalogueError, match="reported lists nothing for 'visc"):
        _row(PorousMaterial, **cells)


@pytest.mark.parametrize(
    ("spread", "fragment"),
    [(-92.0, "never below zero"), (float("inf"), "holds inf")],
)
def test_an_uncertainty_below_zero_or_infinite_is_refused(
    spread: float, fragment: str
) -> None:
    cells: dict[str, object] = {
        "flow_resistivity_pa_s_m2": 540.0,
        "uncertainty": {"flow_resistivity_pa_s_m2": spread},
    }
    with pytest.raises(io.CatalogueError, match=fragment):
        _row(PorousMaterial, **cells)


def test_an_uncertainty_of_zero_is_one() -> None:
    row = _row(
        PorousMaterial,
        flow_resistivity_pa_s_m2=540.0,
        uncertainty={"flow_resistivity_pa_s_m2": 0.0},
    )
    assert row.uncertainty["flow_resistivity_pa_s_m2"] == 0.0


# ---------------------------------------------------------------------------
# Rule 9: a hedge that says there is no value, and one that says there is
# ---------------------------------------------------------------------------
_BAND = "absorption_coefficient_500"


@pytest.mark.parametrize(
    "hedge",
    [
        {"misprinted": {_BAND: "the page prints 5.0; ERRATA"}},
        {"unquantified": {_BAND: "n.m."}},
        {"not_derivable": {_BAND: "the cells it would need are ranges"}},
        {"reported": {_BAND: (0.4, 0.6)}},
    ],
    ids=["misprinted", "unquantified", "not_derivable", "reported"],
)
def test_a_value_beside_a_hedge_that_says_there_is_none_is_refused(
    hedge: dict[str, object],
) -> None:
    """``AbsorptionSpectrum(..., misprinted=...)`` served the value it disowned."""
    with pytest.raises(io.CatalogueError, match=f"{_BAND} holds 0.5, and"):
        _row(AbsorptionSpectrum, **{_BAND: 0.5}, **hedge)


@pytest.mark.parametrize(
    "cells",
    [
        {"converted": {"flow_resistivity_pa_s_m2": ("5", "kPa s/m2")}},
        {"carried": {"flow_resistivity_pa_s_m2": "the row above"}},
    ],
    ids=["converted", "carried"],
)
def test_a_conversion_or_a_carried_cell_with_nothing_behind_it_is_refused(
    cells: dict[str, object],
) -> None:
    with pytest.raises(io.CatalogueError, match="which holds nothing"):
        _row(PorousMaterial, **cells)


def test_a_carried_text_field_that_is_empty_is_refused() -> None:
    with pytest.raises(io.CatalogueError, match="carried names 'refers_to_row'"):
        _row(ImpactInsulation, carried={"refers_to_row": "the row above"})


@pytest.mark.parametrize(
    "cells",
    [
        {
            "converted": {"flow_resistivity_pa_s_m2": ("5", "kPa s/m2")},
            "ranges": {"flow_resistivity_pa_s_m2": (5000.0, None)},
            "bounded_below": {"flow_resistivity_pa_s_m2"},
        },
        {
            "carried": {"viscous_length_um": "the row above"},
            "reported": {"viscous_length_um": (96.0, 120.0)},
        },
        {"converted": {"thickness_mm": ("4", "cm")}, "thickness_mm": 40.0},
    ],
    ids=["converted-bound", "carried-list", "converted-value"],
)
def test_a_conversion_or_a_carried_cell_holds_a_value_a_range_or_a_list(
    cells: dict[str, object],
) -> None:
    assert _row(PorousMaterial, **cells).name == "Panel 40 core"


def test_the_two_exceptions_the_packaged_data_needs_are_kept() -> None:
    """A value beside its range (Hopkins A2), a ``~`` on a range (Cox)."""
    row = _row(
        SolidMaterial,
        density_kg_m3=600.0,
        ranges={"density_kg_m3": (400.0, 800.0), "poisson_ratio": (0.2, 0.3)},
        approximate={"poisson_ratio"},
    )
    assert row.density_kg_m3 == 600.0


# ---------------------------------------------------------------------------
# Rule 10: the basis vocabulary, one implementation
# ---------------------------------------------------------------------------
def test_a_basis_outside_the_vocabulary_is_refused_on_any_field() -> None:
    with pytest.raises(io.CatalogueError, match="the basis of 'poisson_ratio' is"):
        _row(SolidMaterial, basis={"poisson_ratio": "Estimate"})


# ---------------------------------------------------------------------------
# Rule 11: physical limits by unit, never by size
# ---------------------------------------------------------------------------
#: The suffixes the contract bounds below by zero, as the maintainer approved
#: them, and the three whose quantities can be negative.
_NOT_NEGATIVE = (
    "_kg_m3",
    "_kg_m2",
    "_kg",
    "_kg_mol",
    "_m_s",
    "_pa",
    "_pa_s_m2",
    "_pa_s_m",
    "_n_m3",
    "_mm",
    "_um",
    "_m",
    "_m2",
    "_m_hz",
    "_per_cm",
)
_SIGNED = ("_c", "_per_m", "_db", "_percent", "_ratio")

#: A row with one field per suffix above, as a caller's subclass would be.
_EveryUnit = typing.cast(
    "type[io.CatalogueRow]",
    dataclasses.make_dataclass(
        "EveryUnit",
        [
            (f"quantity{suffix}", float | None, dataclasses.field(default=None))
            for suffix in _NOT_NEGATIVE + _SIGNED
        ],
        bases=(io.CatalogueRow,),
        frozen=True,
        kw_only=True,
    ),
)


@pytest.mark.parametrize("suffix", _NOT_NEGATIVE)
@pytest.mark.parametrize(
    "where",
    ["value", "range", "reading"],
)
def test_a_quantity_whose_unit_cannot_be_negative_is_refused_below_zero(
    suffix: str, where: str
) -> None:
    name = f"quantity{suffix}"
    cells: dict[str, object] = {
        "value": {name: -1.0},
        "range": {"ranges": {name: (-1.0, 2.0)}},
        "reading": {"reported": {name: (2.0, (-1.0, 3.0))}},
    }[where]
    with pytest.raises(io.CatalogueError, match="is never negative"):
        _row(_EveryUnit, **cells)


@pytest.mark.parametrize("suffix", _NOT_NEGATIVE + _SIGNED)
def test_zero_is_not_negative(suffix: str) -> None:
    row = _row(_EveryUnit, **{f"quantity{suffix}": 0.0})
    assert getattr(row, f"quantity{suffix}") == 0.0


@pytest.mark.parametrize("suffix", _SIGNED)
def test_a_quantity_that_can_be_negative_is_not_bounded(suffix: str) -> None:
    """A Celsius temperature, a porosity decay, a level: all signed, all kept."""
    row = _row(_EveryUnit, **{f"quantity{suffix}": -1.0e6})
    assert getattr(row, f"quantity{suffix}") == -1.0e6


def test_the_longest_suffix_decides() -> None:
    """``_per_m`` ends in ``_m`` and is a rate that Cox prints negative."""
    row = _row(GroundSurface, porosity_decay_rate_per_m=-270.0)
    assert row.porosity_decay_rate_per_m == -270.0


def test_the_first_probe_is_refused_for_its_density() -> None:
    with pytest.raises(io.CatalogueError, match=r"density_kg_m3 is -5.0, and a qua"):
        _row(SolidMaterial, density_kg_m3=-5.0)


@pytest.mark.parametrize(
    ("cls", "cells", "fragment"),
    [
        (PorousMaterial, {"porosity": 1.2}, "a porosity is a fraction"),
        (PorousMaterial, {"porosity": -0.1}, "a porosity is a fraction"),
        (
            PorousMaterial,
            {"ranges": {"porosity": (0.5, 1.5)}},
            "range of porosity is 1.5",
        ),
        (PorousMaterial, {"shot_content_percent": 101.0}, "share of a whole"),
        (PorousMaterial, {"binder_content_percent": -1.0}, "share of a whole"),
        (DampingTreatment, {"adhered_area_percent": 120.0}, "share of a whole"),
        (Gas, {"molar_mass_kg_mol": -0.029}, "ends in _kg_mol is never negative"),
        (TransmissionLossSpectrum, {"block_mass_kg": -1.0}, "ends in _kg is never"),
        (DuctWallSpectrum, {"duct_length_m": -3.0}, "ends in _m is never negative"),
        (
            ResistiveSheet,
            {"surface_density_g_m2": -1.0},
            "whose name ends in _m2 is never negative",
        ),
    ],
)
def test_a_packaged_row_class_is_held_to_its_limits(
    cls: type[io.CatalogueRow], cells: dict[str, object], fragment: str
) -> None:
    with pytest.raises(io.CatalogueError, match=fragment):
        _row(cls, **cells)


@pytest.mark.parametrize(
    ("cls", "cells"),
    [
        (GroundSurface, {"water_content_percent": 150.0}),
        (DampingTreatment, {"temperature_c": -40.0}),
        (DuctWallSpectrum, {"transmission_loss_63_db": -3.0}),
        (NonlinearityParameter, {"b_over_a": -1.0}),
        (PorousMaterial, {"porosity": 1.0}),
    ],
)
def test_what_the_rule_leaves_unbounded_stays_unbounded(
    cls: type[io.CatalogueRow], cells: dict[str, object]
) -> None:
    """A water content on a dry basis passes 100; a level can be negative."""
    row = _row(cls, **cells)
    ((field, value),) = cells.items()
    assert getattr(row, field) == value


# ---------------------------------------------------------------------------
# Classification: a caller's subclass the contract cannot check
# ---------------------------------------------------------------------------
def _subclass(annotation: object, name: str = "reading") -> type[io.CatalogueRow]:
    """A caller's subclass with one field of *annotation*, empty by default."""
    default = (
        dataclasses.field(default_factory=dict)
        if isinstance(annotation, str) and annotation.startswith("Mapping")
        else dataclasses.field(default=None)
    )
    return typing.cast(
        "type[io.CatalogueRow]",
        dataclasses.make_dataclass(
            "UserRow",
            [(name, annotation, default)],
            bases=(io.CatalogueRow,),
            frozen=True,
            kw_only=True,
        ),
    )


@pytest.mark.parametrize(
    "annotation",
    [
        list[float],
        dict[str, float],
        float | str,
        float | int | None,
        str | None,
        tuple[float, ...],
        set[str],
        frozenset[int],
        typing.Any,
        bytes,
        float,
        int,
        "Undeclared | None",
        "float |",
    ],
    ids=str,
)
def test_an_annotation_the_contract_cannot_check_raises_type_error(
    annotation: object,
) -> None:
    """A field nobody checks would reach every caller unchecked."""
    cls = _subclass(annotation)
    with pytest.raises(TypeError, match=r"UserRow"):
        cls(name="x", source="y")


def test_a_bare_number_is_refused_because_every_cell_may_be_missing() -> None:
    """A ``float`` field could not say the page left its cell empty."""
    cls = _subclass(float)
    with pytest.raises(TypeError, match="never a bare float or int"):
        cls(name="x", source="y", reading=1.5)


def test_optional_float_is_checked_as_the_number_it_is() -> None:
    """``Optional[float]`` resolves to ``float | None``, and is checked as one.

    From Python 3.14 the two spellings are one object, so the contract could
    not tell them apart if it wanted to; what it refuses is an annotation it
    has no check for.
    """
    cls = _subclass(typing.Optional[float])  # noqa: UP045 - the spelling under test
    assert cls(name="x", source="y", reading=1.5).reading == 1.5
    with pytest.raises(io.CatalogueError, match="reading holds nan"):
        cls(name="x", source="y", reading=float("nan"))


def test_a_mapping_a_caller_subclass_adds_is_frozen_and_checked() -> None:
    """``Mapping`` resolves although the test module never imports it."""
    cls = _subclass("Mapping[str, int]", name="counts")
    row = cls(name="x", source="y", counts={"a": 1})
    assert isinstance(row.counts, MappingProxyType)
    with pytest.raises(io.CatalogueError, match=r"counts\['b'\] holds 'two'"):
        cls(name="x", source="y", counts={"b": "two"})


# ---------------------------------------------------------------------------
# Every published row passes, and rebuilds to itself
# ---------------------------------------------------------------------------
def _published_rows() -> list[io.CatalogueRow]:
    return [
        row
        for mapping in catalogue_fingerprint.published_mappings().values()
        for row in mapping.values()
        if isinstance(row, io.CatalogueRow)
    ]


def test_every_published_row_rebuilds_to_itself_through_the_contract() -> None:
    """The packaged rows met the contract at import; a rebuild changes nothing.

    Built again from its own fields, every row passes every rule a second time
    and comes out equal, so freezing an already frozen row is a no-op and no
    packaged cell sits outside a limit.
    """
    rows = _published_rows()
    assert len(rows) > 1900
    for row in rows:
        cells = {item.name: getattr(row, item.name) for item in dataclasses.fields(row)}
        assert type(row)(**cells) == row, f"{row.table}: {row.name}"


#: The six porosities Cox Table 6.7 prints in per cent, with what each prints.
_COX_PER_CENT = {
    "mineral_layer_beneath_mixed_deciduous_forest": "36.5",
    "humus_on_pine_forest_floor": "58.1",
    "pine_forest_litter": "38.9",
    "grass_root_layer_in_loamy_sand": "48 ± 4",
    "loamy_sand": "37.5",
    "bare_sandy_plain": "26.9",
}


def test_the_six_percent_porosities_of_cox_are_held_as_misprinted() -> None:
    """Cox Table 6.7 prints six porosities in per cent in a column of fractions.

    A porosity of 36.5 is not one, and the page does not say it is a per
    cent, so the six cells are empty and ``misprinted`` quotes what the page
    prints. Every other porosity the catalogue holds is a fraction.
    """
    from phonometry.environment.propagation import PUBLISHED_GROUND

    held = {
        key: row
        for key, row in PUBLISHED_GROUND.items()
        if "porosity" in row.misprinted
    }
    assert sorted(held) == sorted(f"cox-2017-table-6-7/{key}" for key in _COX_PER_CENT)
    for row in held.values():
        assert row.porosity is None
        assert "porosity" not in row.uncertainty
    fractions = [row.porosity for row in PUBLISHED_GROUND.values() if row.porosity]
    assert fractions
    assert all(0.0 < value <= 1.0 for value in fractions)


@pytest.mark.parametrize(("key", "figure"), _COX_PER_CENT.items())
def test_why_a_per_cent_porosity_is_missing_quotes_the_page(
    key: str, figure: str
) -> None:
    """The answer is what the page prints, not that it printed nothing."""
    from phonometry.environment.propagation import PUBLISHED_GROUND

    row = PUBLISHED_GROUND[f"cox-2017-table-6-7/{key}"]
    why = row.why_missing("porosity")
    assert why.startswith(f"the page prints “{figure}” in its Porosity column")
    assert "docs/ERRATA.md" in why
    with pytest.raises(ValueError, match=f"prints “{figure}”"):
        row.printed("porosity")


def test_a_porosity_the_page_leaves_empty_still_says_so() -> None:
    """Tall crops prints a dash, which is a different answer from the six."""
    from phonometry.environment.propagation import PUBLISHED_GROUND

    row = PUBLISHED_GROUND["cox-2017-table-6-7/tall_crops"]
    assert row.why_missing("porosity") == (
        "the page does not give it, and it does not follow from the cells that it does"
    )
