#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A figure written in another unit of the same kind, converted on its digits.

A data sheet prints a flow resistivity in kPa s/m2, a thickness in
centimetres, a modulus in N/mm2, and a row holds the unit its field is named
for. A catalogue file names the figure after the field with the unit it is
in (``flow_resistivity_kpa_s_m2``), and :meth:`CatalogueRow.from_printed`
converts it with the exact factor, rounds once, and records the page's figure
and unit in ``converted``. The unit may be written wherever the field is
named: as a value, and as the key of a hedge, whose numbers are converted
with it. These tests hold the families to that, and to the suffixes they must
never take (a specific flow resistance in Pa s/m, a rate per metre).
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from typing import Any

import pytest

from phonometry import io
from phonometry._internal import catalogue as private
from phonometry.environment.propagation import GroundSurface
from phonometry.fluids import NonlinearityParameter
from phonometry.materials import (
    AbsorptionAreaSpectrum,
    PorousMaterial,
    ResilientLayer,
    ResistiveSheet,
)
from phonometry.solids import DampingMaterial, SolidMaterial

_SOURCE = "Panel 40 technical data sheet (Example Acoustics Ltd), Rev. 4"


def _built(cls: type[io.CatalogueRow], **cells: Any) -> Any:  # noqa: ANN401 - the row of the class asked for
    return cls.from_printed(name="Panel 40 core", source=_SOURCE, **cells)


# ---------------------------------------------------------------------------
# The families
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("cls", "written", "figure", "field", "value", "unit"),
    [
        (PorousMaterial, "thickness_m", 0.04, "thickness_mm", 40.0, "m"),
        (PorousMaterial, "thickness_cm", 4, "thickness_mm", 40.0, "cm"),
        (PorousMaterial, "viscous_length_mm", 0.095, "viscous_length_um", 95.0, "mm"),
        (
            PorousMaterial,
            "flow_resistivity_kpa_s_m2",
            12.5,
            "flow_resistivity_pa_s_m2",
            12500.0,
            "kPa s/m2",
        ),
        (
            PorousMaterial,
            "frame_density_g_cm3",
            0.04,
            "frame_density_kg_m3",
            40.0,
            "g/cm3",
        ),
        (
            PorousMaterial,
            "youngs_modulus_kpa",
            140,
            "youngs_modulus_pa",
            140000.0,
            "kPa",
        ),
        (
            SolidMaterial,
            "youngs_modulus_gpa",
            0.067,
            "youngs_modulus_pa",
            67000000.0,
            "GPa",
        ),
        (
            SolidMaterial,
            "youngs_modulus_mpa",
            70,
            "youngs_modulus_pa",
            70000000.0,
            "MPa",
        ),
        (
            SolidMaterial,
            "youngs_modulus_n_mm2",
            70,
            "youngs_modulus_pa",
            70000000.0,
            "N/mm2",
        ),
        (
            ResistiveSheet,
            "surface_density_kg_m2",
            0.3,
            "surface_density_g_m2",
            300.0,
            "kg/m2",
        ),
        (ResistiveSheet, "mass_per_area_g_m2", 300, "mass_per_area_kg_m2", 0.3, "g/m2"),
        (
            ResilientLayer,
            "dynamic_stiffness_mn_m3",
            9,
            "dynamic_stiffness_n_m3",
            9e6,
            "MN/m3",
        ),
        (NonlinearityParameter, "temperature_k", 293.15, "temperature_c", 20.0, "K"),
        (
            NonlinearityParameter,
            "static_pressure_kpa",
            101.325,
            "static_pressure_pa",
            101325.0,
            "kPa",
        ),
    ],
)
def test_a_figure_in_another_unit_of_the_family_fills_its_field(
    cls: type[io.CatalogueRow],
    written: str,
    figure: object,
    field: str,
    value: float,
    unit: str,
) -> None:
    row = _built(cls, **{written: figure})
    assert getattr(row, field) == value
    assert row.converted[field] == (
        repr(figure) if isinstance(figure, float) else str(figure),
        unit,
    )
    assert not row.is_derived(field)


def test_a_figure_converts_on_its_digits_and_rounds_once() -> None:
    """0.067 GPa is 67 000 000 Pa exactly, where the float product is not."""
    row = _built(SolidMaterial, youngs_modulus_gpa=private.PrintedNumber("0.067"))
    assert row.youngs_modulus_pa == 67000000.0
    assert 0.067 * 1e9 != 67000000.0
    assert row.converted["youngs_modulus_pa"] == ("0.067", "GPa")


def test_the_printed_digits_are_kept_as_written() -> None:
    row = _built(
        PorousMaterial, flow_resistivity_kpa_s_m2=private.PrintedNumber("12.50")
    )
    assert row.converted["flow_resistivity_pa_s_m2"] == ("12.50", "kPa s/m2")


def test_a_sweep_of_figures_converts_exactly_where_floats_do_not() -> None:
    kilo = Fraction(1000)
    figures = [f"{whole}.{part:03d}" for whole in range(3) for part in range(1000)]
    exact = [private.convert_figure(figure, kilo) for figure in figures]
    assert exact == [float(Fraction(figure) * kilo) for figure in figures]
    assert any(
        float(figure) * 1000.0 != value
        for figure, value in zip(figures, exact, strict=True)
    )


def test_kelvin_moves_by_its_offset_and_its_uncertainty_does_not() -> None:
    row = _built(
        NonlinearityParameter,
        temperature_k=private.PrintedNumber("293.15"),
        uncertainty={"temperature_k": 0.5},
    )
    assert row.temperature_c == 20.0
    assert row.uncertainty == {"temperature_c": 0.5}


def test_the_ends_of_a_range_and_the_readings_of_a_list_convert_with_the_offset() -> (
    None
):
    ranged = _built(
        DampingMaterial, ranges={"peak_temperature_at_10_hz_k": [263.15, 283.15]}
    )
    # the offset is applied to the decimal figure, so the result is exact
    assert ranged.ranges["peak_temperature_at_10_hz_c"] == (-10.0, 10.0)
    assert ranged.converted["peak_temperature_at_10_hz_c"] == ("263.15 to 283.15", "K")
    listed = _built(
        DampingMaterial,
        reported={"peak_temperature_at_10_hz_k": [273.15, [283.15, 293.15]]},
    )
    assert listed.reported["peak_temperature_at_10_hz_c"] == (0.0, (10.0, 20.0))
    assert listed.converted["peak_temperature_at_10_hz_c"] == (
        "273.15, 283.15 to 293.15",
        "K",
    )


def test_a_bound_records_the_end_the_page_prints() -> None:
    row = _built(
        ResilientLayer,
        ranges={"dynamic_stiffness_mn_m3": [None, 9]},
        bounded_above=["dynamic_stiffness_mn_m3"],
    )
    assert row.ranges == {"dynamic_stiffness_n_m3": (None, 9e6)}
    assert row.bounded_above == frozenset({"dynamic_stiffness_n_m3"})
    assert row.converted == {"dynamic_stiffness_n_m3": ("9", "MN/m3")}
    assert row.why_missing("dynamic_stiffness_n_m3") == (
        "the page prints an upper bound of 9 MN/m3 (9000000 N/m3) and no value"
    )


def test_a_converted_interval_and_list_quote_the_page_first() -> None:
    ranged = _built(PorousMaterial, ranges={"flow_resistivity_kpa_s_m2": [5, 10]})
    assert ranged.why_missing("flow_resistivity_pa_s_m2") == (
        "the page prints 5 to 10 kPa s/m2 (5000 to 10000 Pa s/m2) and no value"
    )
    listed = _built(PorousMaterial, reported={"flow_resistivity_kpa_s_m2": [5, 7]})
    assert listed.why_missing("flow_resistivity_pa_s_m2") == (
        "the page lists 5, 7 kPa s/m2 (5000, 7000 Pa s/m2) and no single value"
    )


def test_a_hedge_that_holds_no_number_may_name_either_unit() -> None:
    row = _built(
        PorousMaterial,
        flow_resistivity_kpa_s_m2=12.5,
        approximate=["flow_resistivity_pa_s_m2"],
        basis={"flow_resistivity_kpa_s_m2": "measured"},
    )
    assert row.approximate == frozenset({"flow_resistivity_pa_s_m2"})
    assert row.basis_of("flow_resistivity_pa_s_m2") == "measured"


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------
def test_the_numbers_of_one_cell_are_written_in_one_unit() -> None:
    cells = {
        "flow_resistivity_kpa_s_m2": 12.5,
        "uncertainty": {"flow_resistivity_pa_s_m2": 900},
    }
    with pytest.raises(
        io.CatalogueError, match="numbers of flow_resistivity_pa_s_m2 are written"
    ):
        _built(PorousMaterial, **cells)


def test_a_cell_given_under_its_own_name_and_an_alias_is_refused() -> None:
    cells = {"thickness_mm": 40, "thickness_cm": 4}
    with pytest.raises(io.CatalogueError, match="one cell, given twice"):
        _built(PorousMaterial, **cells)


def test_a_hedge_that_names_one_cell_twice_is_refused() -> None:
    cells = {"approximate": ["thickness_mm", "thickness_cm"]}
    with pytest.raises(io.CatalogueError, match="approximate names thickness_mm twice"):
        _built(PorousMaterial, **cells)


def test_a_plus_or_minus_alone_in_another_unit_is_refused() -> None:
    """Converted says which figure the page printed, and there is none here."""
    cells = {"uncertainty": {"flow_resistivity_kpa_s_m2": 0.9}}
    with pytest.raises(io.CatalogueError, match="no value, range or list"):
        _built(PorousMaterial, **cells)


def test_converted_written_beside_an_alias_figure_is_refused() -> None:
    cells = {
        "ranges": {"flow_resistivity_kpa_s_m2": [5, None]},
        "bounded_below": ["flow_resistivity_kpa_s_m2"],
        "converted": {"flow_resistivity_pa_s_m2": ["5", "kPa s/m2"]},
    }
    with pytest.raises(
        io.CatalogueError, match="converted is given for flow_resistivity_pa_s_m2"
    ):
        _built(PorousMaterial, **cells)


@pytest.mark.parametrize(
    ("cls", "written"),
    [
        # Pa s/m is a specific flow resistance, not a length in metres
        (ResistiveSheet, "specific_flow_resistance_pa_s_mm"),
        # a decay rate per metre is not a length either
        (GroundSurface, "porosity_decay_rate_per_mm"),
        # nor is a count of wires per centimetre
        (ResistiveSheet, "wires_per_mm"),
        # a unit no family holds
        (PorousMaterial, "thickness_inch"),
    ],
)
def test_a_compound_unit_is_never_read_as_a_family_member(
    cls: type[io.CatalogueRow], written: str
) -> None:
    assert written not in private.spellings(cls).aliases
    with pytest.raises(TypeError, match=written):
        _built(cls, **{written: 1.0})


def test_a_name_two_fields_could_take_is_refused() -> None:
    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Board(io.CatalogueRow):
        thickness_mm: float | None = None
        thickness_m: float | None = None

    assert private.spellings(Board).ambiguous["thickness_cm"] == (
        "thickness_m",
        "thickness_mm",
    )
    with pytest.raises(
        io.CatalogueError, match="could be thickness_m and thickness_mm"
    ):
        Board.from_printed(name="Board", source=_SOURCE, thickness_cm=4)


def test_a_field_name_is_never_converted() -> None:
    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Board(io.CatalogueRow):
        thickness_mm: float | None = None
        thickness_m: float | None = None

    row = Board.from_printed(name="Board", source=_SOURCE, thickness_m=0.04)
    assert row.thickness_m == 0.04
    assert row.thickness_mm is None
    assert row.converted == {}


# ---------------------------------------------------------------------------
# A field of a class of your own
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True, kw_only=True)
class _Mount(io.CatalogueRow):
    """A row class of a caller's own, with fields in compound units."""

    dynamic_stiffness_n_m: float | None = None
    mass_per_length_kg_m: float | None = None
    thermal_conductivity_w_m_k: float | None = None
    specific_heat_j_kg_k: float | None = None
    temperature_rise_c: float | None = None
    wall_thickness_mm: float | None = None


@pytest.mark.parametrize(
    "field",
    [
        # N/m: its metre divides, and a figure in N/mm is a thousand times more
        "dynamic_stiffness_n_m",
        # kg/m
        "mass_per_length_kg_m",
        # W/(m K): its kelvin divides and takes no offset
        "thermal_conductivity_w_m_k",
        # J/(kg K)
        "specific_heat_j_kg_k",
        # a difference of two temperatures moves by the factor alone
        "temperature_rise_c",
    ],
)
def test_a_field_of_your_own_in_a_compound_unit_takes_no_other_unit(
    field: str,
) -> None:
    names = private.spellings(_Mount)
    assert [
        written for written, (target, _) in names.aliases.items() if target == field
    ] == []
    assert field not in names.units


def test_a_field_of_your_own_in_a_plain_unit_takes_its_family() -> None:
    row = _Mount.from_printed(name="Mount", source=_SOURCE, wall_thickness_cm=4)
    assert row.wall_thickness_mm == 40.0
    assert row.converted == {"wall_thickness_mm": ("4", "cm")}


def test_a_figure_in_a_unit_your_field_does_not_take_is_refused() -> None:
    """150 N/mm is 150 000 N/m, and read as millimetres it would be 0.15."""
    cells = {"dynamic_stiffness_n_mm": 150}
    with pytest.raises(TypeError, match="dynamic_stiffness_n_mm"):
        _Mount.from_printed(name="Mount", source=_SOURCE, **cells)


def test_a_field_a_subclass_adds_takes_none_of_its_base_class_units() -> None:
    """The sabins of a table set in feet are for the bands that table prints."""

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Loud(AbsorptionAreaSpectrum):
        intensity_w_m2: float | None = None

    names = private.spellings(Loud)
    assert "intensity_w_ft2" not in names.aliases
    assert names.aliases["absorption_area_500_ft2"][0] == "absorption_area_500_m2"


def test_a_unit_no_family_holds_is_spelled_beside_its_converted_figure() -> None:
    row = AbsorptionAreaSpectrum.from_printed(
        name="Seat",
        source=_SOURCE,
        per="seat",
        ranges={"absorption_area_500_ft2": [5, 10]},
    )
    assert row.why_missing("absorption_area_500_m2") == (
        "the page prints 5 to 10 sabins (0.4645152 to 0.9290304 m2) and no value"
    )


# ---------------------------------------------------------------------------
# The guard that closes the class: every published field's unit
# ---------------------------------------------------------------------------
def _row_classes() -> list[type[io.CatalogueRow]]:
    import importlib
    import pkgutil

    import phonometry

    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.ispkg and not module.name.startswith("_"):
            importlib.import_module(f"phonometry.{module.name}")
    found: list[type[io.CatalogueRow]] = []
    pending: list[type[io.CatalogueRow]] = [io.CatalogueRow]
    while pending:
        cls = pending.pop()
        for subclass in cls.__subclasses__():
            if subclass.__module__.startswith("phonometry."):
                found.append(subclass)
                pending.append(subclass)
    return found


#: Every published numeric field whose name ends in a unit of a family, by
#: family. A field added with a name that ends in a family's suffix lands
#: here, and has to be read: a compound unit ending in one (Pa s/m, per
#: metre) is listed in the module's compound units instead, or it would be
#: scaled as a length.
_FAMILY_FIELDS: dict[str, frozenset[str]] = {
    "density": frozenset(
        {"density_kg_m3", "frame_density_kg_m3", "layer_density_kg_m3"}
    ),
    "flow resistivity": frozenset({"flow_resistivity_pa_s_m2"}),
    "length": frozenset(
        {
            "construction_depth_mm",
            "diameter_mm",
            "duct_length_m",
            "fibre_diameter_um",
            "first_side_mm",
            "pile_height_mm",
            "second_side_mm",
            "thermal_length_um",
            "thickness_mm",
            "viscous_length_um",
            "wire_diameter_um",
        }
    ),
    "mass per area": frozenset(
        {
            "mass_per_area_kg_m2",
            "pile_weight_kg_m2",
            "surface_density_g_m2",
            "surface_density_kg_m2",
            "surface_density_per_mm_kg_m2",
        }
    ),
    "pressure": frozenset(
        {
            "added_load_pa",
            "dynamic_youngs_modulus_pa",
            "loss_modulus_max_pa",
            "plate_stiffness_d1_pa",
            "plate_stiffness_d2_pa",
            "plate_stiffness_d3_pa",
            "plate_stiffness_d4_pa",
            "shear_modulus_pa",
            "static_load_pa",
            "static_pressure_pa",
            "youngs_modulus_max_pa",
            "youngs_modulus_min_pa",
            "youngs_modulus_pa",
            "youngs_modulus_transition_pa",
        }
    ),
    "stiffness per area": frozenset(
        {"apparent_dynamic_stiffness_n_m3", "dynamic_stiffness_n_m3"}
    ),
    "temperature": frozenset(
        {
            "peak_temperature_at_1000_hz_c",
            "peak_temperature_at_100_hz_c",
            "peak_temperature_at_10_hz_c",
            "temperature_c",
        }
    ),
}


def test_every_published_field_in_a_family_is_one_the_families_were_read_for() -> None:
    found: dict[str, set[str]] = {}
    for cls in _row_classes():
        units = private.spellings(cls).units
        for name in private._shape(cls).numeric:
            unit = private._UNITS.get(private.unit_suffix(name))
            if unit is not None:
                assert units.get(name) == unit.spelling, (cls.__name__, name)
                found.setdefault(unit.family, set()).add(name)
    assert {family: frozenset(names) for family, names in found.items()} == (
        _FAMILY_FIELDS
    )


def test_every_field_that_takes_another_unit_spells_its_own() -> None:
    """A refusal quotes the page's figure and then the row's, in its unit."""
    for cls in _row_classes():
        names = private.spellings(cls)
        filled = {target for target, _ in names.aliases.values()}
        assert sorted(name for name in filled if not names.units.get(name)) == [], (
            cls.__name__
        )


def test_the_compound_units_are_found_before_the_family_inside_them() -> None:
    assert private.unit_suffix("specific_flow_resistance_pa_s_m") == "_pa_s_m"
    assert private.unit_suffix("porosity_decay_rate_per_m") == "_per_m"
    assert private.unit_suffix("wires_per_cm") == "_per_cm"
    assert private.unit_suffix("dynamic_stiffness_mn_m3") == "_mn_m3"
    assert private.unit_suffix("flow_resistivity_kpa_s_m2") == "_kpa_s_m2"
    assert private.unit_suffix("porosity") == ""
