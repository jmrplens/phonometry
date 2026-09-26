#  Copyright (c) 2026. Jose Manuel Requena Plens
"""An ISO 12354 homogeneous element built from a solid's catalogue row.

``HomogeneousElement.from_solid`` works out the two numbers Annex B builds a
homogeneous element from, the mass per unit area ``m' = rho t`` and the
critical frequency ``fc = co**2 / (1.8 cL t)`` (ISO 12354-1:2017, the symbols
of Formula (B.2), PDF page 32, printed folio 26), with ``cL`` the
quasi-longitudinal phase velocity of Table B.3 (PDF page 37, folio 31), which
is a row's plate speed. The oracle is the worked example of
Annex L, whose element block (PDF page 84, folio 78) prints the density and
the velocity of each of its three constructions beside the results, rounded
to one decimal. Table B.3 prints the same two numbers for concrete and for
calcium-silicate blocks, and 400 to 800 kg/m³ for autoclaved aerated
concrete, of which Annex L takes 600. 220 mm of concrete at 2 200 kg/m³ and
3 800 m/s is 484 kg/m² and 76,8 Hz; 365 mm of autoclaved aerated concrete at
600 kg/m³ and 1 900 m/s is 219 kg/m² and 92,6 Hz; 200 mm of calcium-silicate
blocks at 1 800 kg/m³ and 2 500 m/s is 360 kg/m² and 128,4 Hz, all with
``co`` = 340 m/s. Its footnote says the calculation used the unrounded
values, which is what this method gives, so the in-situ indices of
Table L.3 follow from the rows to the tolerance the detailed model is held to.
"""

from __future__ import annotations

import iso12354_building
import numpy as np
import pytest
import reference_data as ref

from phonometry import building, io, materials, solids

#: The one-third-octave bands of the Annex L tables.
BANDS = np.asarray(ref.ISO12354_ANNEX_L_BANDS, dtype=np.float64)

#: The density and the quasi-longitudinal phase velocity of the three
#: materials of ISO 12354-1:2017 Annex L, as its element block prints them
#: (PDF page 84, folio 78). Table B.3 (PDF page 37, folio 31) prints the same
#: pairs, except that it gives autoclaved aerated concrete blocks a density
#: of 400 to 800 kg/m³, of which Annex L takes 600.
ANNEX_L_MATERIALS = {
    "Concrete": (2200.0, 3800.0),
    "Autoclaved aerated concrete blocks": (600.0, 1900.0),
    "Calcium-silicate blocks": (1800.0, 2500.0),
}

#: The Annex L element each row makes, with its thickness in metres.
ELEMENTS = {
    "floor": ("Concrete", 0.22),
    "ext1": ("Autoclaved aerated concrete blocks", 0.365),
    "ext2": ("Autoclaved aerated concrete blocks", 0.365),
    "int1": ("Calcium-silicate blocks", 0.2),
    "int2": ("Calcium-silicate blocks", 0.2),
}


def _row(material: str) -> solids.SolidMaterial:
    density, speed = ANNEX_L_MATERIALS[material]
    return solids.SolidMaterial.from_printed(
        name=material,
        source="ISO 12354-1:2017 Annex L, PDF page 84 (printed p. 78)",
        density_kg_m3=density,
        plate_longitudinal_speed_m_s=speed,
    )


def _element(label: str) -> building.HomogeneousElement:
    material, thickness = ELEMENTS[label]
    area, length1, length2, *_, eta_int, _, _, _ = ref.ISO12354_ANNEX_L_ELEMENTS[label]
    return building.HomogeneousElement.from_solid(
        _row(material),
        thickness_m=thickness,
        internal_loss_factor=eta_int,
        area_m2=area,
        length1_m=length1,
        length2_m=length2,
        perimeter_absorption_m=iso12354_building.perimeter_sums()[label],
        label=label,
    )


@pytest.mark.parametrize(
    ("label", "mass", "fc"),
    [("floor", 484.0, 76.8), ("ext1", 219.0, 92.6), ("int1", 360.0, 128.4)],
)
def test_the_annex_l_elements_follow_from_their_rows(
    label: str, mass: float, fc: float
) -> None:
    element = _element(label)
    assert element.mass_per_area == pytest.approx(mass, rel=1e-12)
    assert round(element.critical_frequency, 1) == fc
    material, _ = ELEMENTS[label]
    assert (element.density, element.longitudinal_velocity) == ANNEX_L_MATERIALS[
        material
    ]


@pytest.mark.parametrize("label", sorted(ref.ISO12354_ANNEX_L3_R_SITU))
def test_the_rows_reproduce_the_in_situ_indices_of_table_l3(label: str) -> None:
    situ = building.in_situ_element(_element(label), BANDS)
    assert situ.sound_reduction_index == pytest.approx(
        ref.ISO12354_ANNEX_L3_R_SITU[label], abs=0.1
    )


def test_the_critical_frequency_is_the_one_the_measurement_module_works_out() -> None:
    element = _element("floor")
    assert element.critical_frequency == building.critical_frequency(
        3800.0, 0.22, speed_of_sound=340.0
    )


def test_the_air_sets_the_critical_frequency() -> None:
    faster = building.HomogeneousElement.from_solid(
        _row("Concrete"),
        thickness_m=0.22,
        internal_loss_factor=0.005,
        area_m2=20.0,
        length1_m=5.0,
        length2_m=4.0,
        fluid=materials.PUBLISHED_AIR,
    )
    ratio = faster.critical_frequency / _element("floor").critical_frequency
    assert ratio == pytest.approx((materials.PUBLISHED_AIR.speed_of_sound / 340.0) ** 2)


def test_no_loss_factor_the_row_holds_is_ever_read() -> None:
    """Four loss factors on the row, and the element takes the one it is given."""
    row = solids.SolidMaterial.from_printed(
        name="Concrete",
        source="A test of the detailed model",
        density_kg_m3=2200.0,
        plate_longitudinal_speed_m_s=3800.0,
        loss_factor=0.02,
        flexural_loss_factor=0.03,
        longitudinal_loss_factor=0.04,
        in_situ_loss_factor=0.05,
    )
    element = building.HomogeneousElement.from_solid(
        row,
        thickness_m=0.22,
        internal_loss_factor=0.005,
        area_m2=20.0,
        length1_m=5.0,
        length2_m=4.0,
    )
    assert element.internal_loss_factor == 0.005
    assert element.label == "Concrete"


def test_the_loss_factor_has_no_default() -> None:
    concrete = _row("Concrete")
    with pytest.raises(TypeError, match="internal_loss_factor"):
        building.HomogeneousElement.from_solid(  # type: ignore[call-arg]
            concrete,
            thickness_m=0.22,
            area_m2=20.0,
            length1_m=5.0,
            length2_m=4.0,
        )


def test_a_plate_speed_worked_out_from_the_constants_is_taken() -> None:
    """A page that prints E, nu and rho has printed the plate speed too."""
    row = solids.PUBLISHED_SOLIDS["bies-2017-table-c1/concrete_high_strength"]
    assert row.is_derived("plate_longitudinal_speed_m_s")
    element = building.HomogeneousElement.from_solid(
        row,
        thickness_m=0.2,
        internal_loss_factor=0.005,
        area_m2=10.0,
        length1_m=3.0,
        length2_m=3.33,
    )
    assert element.longitudinal_velocity == row.plate_longitudinal_speed_m_s
    assert element.mass_per_area == pytest.approx(0.2 * 2400.0)


def test_a_density_the_page_prints_as_a_range_is_refused() -> None:
    aircrete = solids.PUBLISHED_SOLIDS["hopkins-2007-table-a2/aircrete"]
    with pytest.raises(
        ValueError,
        match=r"has no density_kg_m3, which 'HomogeneousElement.from_solid' needs: "
        r"the page prints \d+ to \d+ and no value",
    ):
        building.HomogeneousElement.from_solid(
            aircrete,
            thickness_m=0.1,
            internal_loss_factor=0.0125,
            area_m2=10.0,
            length1_m=3.0,
            length2_m=3.33,
        )


def test_a_row_of_another_class_is_a_type_error() -> None:
    wood = next(iter(solids.PUBLISHED_ORTHOTROPIC_WOOD.values()))
    with pytest.raises(TypeError, match="got OrthotropicWood"):
        building.HomogeneousElement.from_solid(  # type: ignore[arg-type]
            wood,
            thickness_m=0.02,
            internal_loss_factor=0.01,
            area_m2=10.0,
            length1_m=3.0,
            length2_m=3.33,
        )


@pytest.mark.parametrize(
    ("name", "value"), [("thickness_m", 0.0), ("internal_loss_factor", -0.01)]
)
def test_a_thickness_or_loss_factor_that_is_not_positive_is_refused(
    name: str, value: float
) -> None:
    arguments = {
        "thickness_m": 0.22,
        "internal_loss_factor": 0.005,
        "area_m2": 20.0,
        "length1_m": 5.0,
        "length2_m": 4.0,
        name: value,
    }
    row = _row("Concrete")
    with pytest.raises(ValueError, match=name):
        building.HomogeneousElement.from_solid(row, **arguments)


def test_a_wall_of_your_own_goes_into_the_detailed_model() -> None:
    walls = io.parse_catalogue(
        {
            "schema": "phonometry-catalogue",
            "schema_version": 1,
            "catalogue": "blocks",
            "row_type": "SolidMaterial",
            "about": "A fictitious block's density and plate speed, as its data sheet prints them.",
            "provenance": {
                "kind": "datasheet",
                "document": "Example block data sheet",
                "version": "Rev. 3",
                "consulted": "2026-09-25",
            },
            "basis": "declared",
            "rows": [
                {
                    "key": "block",
                    "name": "Example block",
                    "density_kg_m3": 1800,
                    "plate_longitudinal_speed_m_s": 2500,
                },
                {"key": "light", "name": "Example light block", "density_kg_m3": 600},
            ],
        },
        row_type=solids.SolidMaterial,
    )
    element = building.HomogeneousElement.from_solid(
        walls["blocks/block"],
        thickness_m=0.2,
        internal_loss_factor=0.01,
        area_m2=13.75,
        length1_m=5.0,
        length2_m=2.75,
    )
    assert round(element.critical_frequency, 1) == 128.4
    light = walls["blocks/light"]
    with pytest.raises(
        ValueError,
        match=r"'Example light block' has no plate_longitudinal_speed_m_s, which "
        r"'HomogeneousElement.from_solid' needs: the datasheet does not give it",
    ):
        building.HomogeneousElement.from_solid(
            light,
            thickness_m=0.2,
            internal_loss_factor=0.01,
            area_m2=13.75,
            length1_m=5.0,
            length2_m=2.75,
        )
