#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A solid's catalogue row as a medium of the elastic simulation.

Wherever the elastic FDTD takes a :class:`Material` it takes a solid's row
too, published or read from a catalogue file, and reads three of its cells:
the bulk longitudinal speed, the transverse speed and the density. The risk
the tests hold is the one the solver's own banner warns about, a plate or a
bar speed taken for the bulk speed it integrates, which would put an eleven
per cent error behind a citation. The oracle for the speeds is the closed
forms of an isotropic solid, ``c_P = sqrt(E (1 - nu) / (rho (1 + nu)
(1 - 2 nu)))`` and ``c_S = sqrt(E / (2 rho (1 + nu)))``, applied to the
modulus, Poisson ratio and density Bies Table C.1 prints for mild steel,
written here as the page prints them rather than read back from the row.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import io, materials, solids
from phonometry.simulation.elastic_fdtd import (
    STEEL,
    WATER,
    ElasticFDTD2D,
    Material,
    scholte_speed,
)
from phonometry.solids import PUBLISHED_SOLIDS

#: Mild steel as Bies Table C.1 prints it, the row the STEEL constant cites.
BIES_STEEL = PUBLISHED_SOLIDS["bies-2017-table-c1/steel_mild"]

#: What Bies 5e Table C.1 prints for "Steel (mild)", PDF page 747 (printed
#: p. 718): a Young's modulus of 207 x 10^9 N/m2, a density of 7850 kg/m3 and
#: a Poisson's ratio of 0.30.
PRINTED_E_PA, PRINTED_RHO_KG_M3, PRINTED_NU = 207e9, 7850.0, 0.30


def _bulk(e: float, nu: float, rho: float) -> float:
    return math.sqrt(e * (1.0 - nu) / (rho * (1.0 + nu) * (1.0 - 2.0 * nu)))


def _shear(e: float, nu: float, rho: float) -> float:
    return math.sqrt(e / (2.0 * rho * (1.0 + nu)))


def _solid(**cells: float) -> solids.SolidMaterial:
    """A row of a table of my own, built through the completion."""
    return solids.SolidMaterial.from_printed(
        name="Example alloy", source="A test of the elastic simulation", **cells
    )


def test_a_row_gives_the_bulk_speeds_of_its_printed_constants() -> None:
    e, nu, rho = PRINTED_E_PA, PRINTED_NU, PRINTED_RHO_KG_M3
    assert (
        BIES_STEEL.printed("youngs_modulus_pa"),
        BIES_STEEL.printed("poisson_ratio"),
        BIES_STEEL.printed("density_kg_m3"),
    ) == (e, nu, rho)
    # The two speeds the solver reads, against the closed forms of the page's
    # three numbers: 5957.96 and 3184.66 m/s.
    c_p, c_s = _bulk(e, nu, rho), _shear(e, nu, rho)
    assert BIES_STEEL.printed("bulk_longitudinal_speed_m_s") == pytest.approx(
        c_p, rel=1e-12
    )
    assert BIES_STEEL.printed("transverse_speed_m_s") == pytest.approx(c_s, rel=1e-12)
    fluid = WATER
    by_row = scholte_speed(fluid, BIES_STEEL)
    by_material = scholte_speed(fluid, Material(c_p=c_p, c_s=c_s, rho=rho))
    assert by_row == pytest.approx(by_material, rel=1e-12)
    # The STEEL constant is the same row, rounded to 0.1 m/s.
    assert (STEEL.c_p, STEEL.c_s) == pytest.approx((c_p, c_s), abs=0.05)
    assert by_row == pytest.approx(scholte_speed(fluid, STEEL), rel=1e-5)


def test_the_plate_speed_is_never_what_the_solver_reads() -> None:
    """A row holding only its plate speed and density is refused, not read."""
    plate_only = solids.SolidMaterial(
        name="Example plate",
        source="A test of the elastic simulation",
        density_kg_m3=7800.0,
        plate_longitudinal_speed_m_s=5200.0,
        bar_longitudinal_speed_m_s=5000.0,
        longitudinal_speed_m_s=5100.0,
        transverse_speed_m_s=3100.0,
    )
    with pytest.raises(
        ValueError,
        match=r"'Example plate' has no bulk_longitudinal_speed_m_s, which "
        r"'the elastic FDTD' needs: the page does not give it",
    ):
        scholte_speed(WATER, plate_only)


def test_a_speed_the_page_does_not_say_is_which_is_refused() -> None:
    long_row = next(
        row
        for row in PUBLISHED_SOLIDS.values()
        if row.table == "long-2014-table-12-1" and row.longitudinal_speed_m_s
    )
    assert long_row.bulk_longitudinal_speed_m_s is None
    with pytest.raises(ValueError, match="which 'the elastic FDTD' needs"):
        ElasticFDTD2D.from_regions((8, 8), 0.01, background=long_row)


def test_a_range_the_page_prints_is_refused_in_its_terms() -> None:
    aircrete = PUBLISHED_SOLIDS["hopkins-2007-table-a2/aircrete"]
    assert "density_kg_m3" in aircrete.ranges
    with pytest.raises(
        ValueError, match=r"'Aircrete/.* has no bulk_longitudinal_speed_m_s"
    ):
        scholte_speed(WATER, aircrete)


def test_a_row_of_a_class_without_the_three_cells_is_a_type_error() -> None:
    porous = next(iter(materials.PUBLISHED_POROUS.values()))
    with pytest.raises(
        TypeError,
        match=r"solid is a PorousMaterial row, which has no "
        r"bulk_longitudinal_speed_m_s or transverse_speed_m_s or density_kg_m3",
    ):
        scholte_speed(WATER, porous)


def test_speeds_no_isotropic_solid_has_are_refused_naming_the_row() -> None:
    auxetic = _solid(
        density_kg_m3=1000.0,
        bulk_longitudinal_speed_m_s=1000.0,
        transverse_speed_m_s=900.0,
    )
    with pytest.raises(
        ValueError,
        match=r"solid: 'Example alloy' \(A test of the elastic simulation\) is "
        r"not a medium this solver takes: c_p\*\*2 must be at least",
    ):
        scholte_speed(WATER, auxetic)


def test_a_row_paints_a_region_as_its_material_does() -> None:
    material = Material(
        c_p=BIES_STEEL.bulk_longitudinal_speed_m_s,
        c_s=BIES_STEEL.transverse_speed_m_s,
        rho=BIES_STEEL.density_kg_m3,
    )
    lower = (slice(6, None), slice(None))
    by_row = ElasticFDTD2D.from_regions(
        (12, 10), 0.002, background=WATER, regions=[(lower, BIES_STEEL)]
    )
    by_material = ElasticFDTD2D.from_regions(
        (12, 10), 0.002, background=WATER, regions=[(lower, material)]
    )
    assert by_row.dt == by_material.dt
    for name in ("c_p", "c_s", "rho", "mu", "lam"):
        np.testing.assert_array_equal(getattr(by_row, name), getattr(by_material, name))
    assert by_row.c_s[0, 0] == 0.0
    assert by_row.c_p[-1, 0] == BIES_STEEL.bulk_longitudinal_speed_m_s


def test_a_solid_of_your_own_goes_in_through_its_completion() -> None:
    """A file row printing E, nu and rho holds the bulk speeds the page implies."""
    catalogue = io.parse_catalogue(
        {
            "schema": "phonometry-catalogue",
            "schema_version": 1,
            "catalogue": "alloys",
            "row_type": "SolidMaterial",
            "about": "Elastic constants of a fictitious alloy, as its data sheet prints them.",
            "provenance": {
                "kind": "datasheet",
                "document": "Example alloy data sheet",
                "version": "Rev. 1",
                "consulted": "2026-09-25",
            },
            "rows": [
                {
                    "key": "a",
                    "name": "Example alloy",
                    "youngs_modulus_gpa": 70,
                    "poisson_ratio": 0.33,
                    "density_kg_m3": 2700,
                }
            ],
        },
        row_type=solids.SolidMaterial,
    )
    row = catalogue["alloys/a"]
    assert row.is_derived("bulk_longitudinal_speed_m_s")
    speed = scholte_speed(WATER, row)
    want = scholte_speed(
        WATER,
        Material(
            c_p=_bulk(70e9, 0.33, 2700.0), c_s=_shear(70e9, 0.33, 2700.0), rho=2700.0
        ),
    )
    assert speed == pytest.approx(want, rel=1e-12)
