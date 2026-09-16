#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The three longitudinal wave speeds of a solid, and the printed column.

A solid carries a different longitudinal wave in a beam, in a plate and in an
unbounded medium, and the whole point of this module is that the three are
named apart. So the tests are about telling them apart: the order they come in,
the round trip through each inverse, the ratios the formulas demand, and the
one column a book prints that can settle whether the constant is right.

That column is ``h.f_c`` in Hopkins Table A2. Twenty-five materials, one
constant, and a heading that states the speed of sound it was computed for, so
the rounded 1.8 of ISO 12354-1 and the exact ``2 pi / sqrt(12)`` cannot both
pass.
"""

from __future__ import annotations

import math

import pytest
import reference_data as ref

from phonometry import solids
from phonometry.vibration import coincidence_frequency

_STEEL_DENSITY, _STEEL_POISSON, _STEEL_PLATE_SPEED, _STEEL_HFC = ref.HOPKINS_A2_STEEL


def _steel_modulus() -> float:
    """Young's modulus of the Table A2 steel, from its own printed row."""
    return solids.youngs_modulus_from_plate_speed(
        _STEEL_PLATE_SPEED,
        density_kg_m3=_STEEL_DENSITY,
        poisson_ratio=_STEEL_POISSON,
    )


# ---------------------------------------------------------------------------
# Telling the three apart
# ---------------------------------------------------------------------------
def test_the_three_speeds_come_in_the_order_the_constraint_implies() -> None:
    """More constraint is more stiffness: beam, then plate, then unbounded."""
    modulus = _steel_modulus()
    beam = solids.beam_longitudinal_speed(modulus, density_kg_m3=_STEEL_DENSITY)
    plate = solids.plate_longitudinal_speed(
        modulus, density_kg_m3=_STEEL_DENSITY, poisson_ratio=_STEEL_POISSON
    )
    bulk = solids.bulk_longitudinal_speed(
        modulus, density_kg_m3=_STEEL_DENSITY, poisson_ratio=_STEEL_POISSON
    )

    assert beam < plate < bulk


def test_the_plate_stiffens_the_beam_by_exactly_one_minus_nu_squared() -> None:
    """The only thing between Eq. 2.20 and Eq. 2.21."""
    modulus = _steel_modulus()
    beam = solids.beam_longitudinal_speed(modulus, density_kg_m3=_STEEL_DENSITY)
    plate = solids.plate_longitudinal_speed(
        modulus, density_kg_m3=_STEEL_DENSITY, poisson_ratio=_STEEL_POISSON
    )

    assert plate / beam == pytest.approx(1.0 / math.sqrt(1.0 - _STEEL_POISSON**2))


def test_a_material_that_cannot_contract_sideways_has_one_speed() -> None:
    """At ``nu = 0`` there is nothing to distinguish the three."""
    beam = solids.beam_longitudinal_speed(2.0e11, density_kg_m3=7800.0)
    plate = solids.plate_longitudinal_speed(
        2.0e11, density_kg_m3=7800.0, poisson_ratio=0.0
    )
    bulk = solids.bulk_longitudinal_speed(
        2.0e11, density_kg_m3=7800.0, poisson_ratio=0.0
    )

    assert plate == pytest.approx(beam)
    assert bulk == pytest.approx(beam)


# ---------------------------------------------------------------------------
# The inverses
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("poisson_ratio", [0.0, 0.2, 0.28, 0.34, 0.45])
def test_every_speed_returns_the_modulus_it_was_made_from(
    poisson_ratio: float,
) -> None:
    """A catalogue is built out of these round trips, so they have to close."""
    modulus, density = 1.7e10, 2300.0
    beam = solids.beam_longitudinal_speed(modulus, density_kg_m3=density)
    plate = solids.plate_longitudinal_speed(
        modulus, density_kg_m3=density, poisson_ratio=poisson_ratio
    )
    bulk = solids.bulk_longitudinal_speed(
        modulus, density_kg_m3=density, poisson_ratio=poisson_ratio
    )

    assert solids.youngs_modulus_from_beam_speed(
        beam, density_kg_m3=density
    ) == pytest.approx(modulus)
    assert solids.youngs_modulus_from_plate_speed(
        plate, density_kg_m3=density, poisson_ratio=poisson_ratio
    ) == pytest.approx(modulus)
    assert solids.youngs_modulus_from_bulk_speed(
        bulk, density_kg_m3=density, poisson_ratio=poisson_ratio
    ) == pytest.approx(modulus)


def test_the_steel_of_table_a2_has_the_modulus_a_structural_steel_has() -> None:
    """The inverse on a printed row, against what steel is known to be."""
    low, high = ref.STRUCTURAL_STEEL_YOUNGS_MODULUS_BAND_PA

    assert low < _steel_modulus() < high


# ---------------------------------------------------------------------------
# The printed column
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("material", "plate_speed", "printed"), ref.HOPKINS_A2_PLATE_SPEED_AND_HFC
)
def test_every_row_of_table_a2_reproduces_its_own_h_fc(
    material: str, plate_speed: float, printed: float
) -> None:
    """Twenty-five materials against the column, at the printed precision."""
    got = solids.thickness_critical_frequency_product(
        plate_speed, speed_of_sound_m_s=ref.HOPKINS_A2_SPEED_OF_SOUND_M_S
    )

    assert got == pytest.approx(printed, abs=0.05), material


def test_the_rounded_iso_constant_would_miss_the_printed_column() -> None:
    """Why the exact ``2 pi / sqrt(12)`` is the one written down here."""
    rounded = ref.HOPKINS_A2_SPEED_OF_SOUND_M_S**2 / (1.8 * _STEEL_PLATE_SPEED)

    assert abs(rounded - _STEEL_HFC) > 0.05
    assert solids.thickness_critical_frequency_product(
        _STEEL_PLATE_SPEED
    ) == pytest.approx(_STEEL_HFC, abs=0.05)


def test_the_product_is_the_coincidence_frequency_times_the_thickness() -> None:
    """The same quantity the plate side of the library already computes."""
    thickness = 0.012
    modulus = _steel_modulus()
    mass_per_area = _STEEL_DENSITY * thickness
    bending = modulus * thickness**3 / (12.0 * (1.0 - _STEEL_POISSON**2))

    expected = coincidence_frequency(mass_per_area, bending) * thickness

    assert solids.thickness_critical_frequency_product(
        _STEEL_PLATE_SPEED
    ) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# What the formulas refuse
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("poisson_ratio", [1.0, -1.0, 1.5])
def test_a_plate_refuses_a_ratio_that_would_divide_by_zero(
    poisson_ratio: float,
) -> None:
    """``1 - nu**2`` has to stay positive."""
    with pytest.raises(ValueError, match="poisson_ratio must lie between -1 and 1"):
        solids.plate_longitudinal_speed(
            2.0e11, density_kg_m3=7800.0, poisson_ratio=poisson_ratio
        )


@pytest.mark.parametrize("poisson_ratio", [0.5, 0.6, -1.0])
def test_an_unbounded_solid_refuses_an_incompressible_material(
    poisson_ratio: float,
) -> None:
    """At ``nu = 0.5`` there is no pure longitudinal wave to have a speed."""
    with pytest.raises(ValueError, match="poisson_ratio must lie between -1 and 0.5"):
        solids.bulk_longitudinal_speed(
            2.0e11, density_kg_m3=7800.0, poisson_ratio=poisson_ratio
        )


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_a_speed_needs_a_positive_modulus_and_density(bad: float) -> None:
    """The house precondition, on both arguments of the simplest of the three."""
    with pytest.raises(ValueError, match="youngs_modulus_pa"):
        solids.beam_longitudinal_speed(bad, density_kg_m3=7800.0)
    with pytest.raises(ValueError, match="density_kg_m3"):
        solids.beam_longitudinal_speed(2.0e11, density_kg_m3=bad)
