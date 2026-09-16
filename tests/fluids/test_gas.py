#  Copyright (c) 2026. Jose Manuel Requena Plens
"""An ideal gas, and the printed table that says how far the closure goes.

Hopkins Table A1 prints four columns for six gases: the ratio of specific heats
and the molar mass, which is what :func:`phonometry.fluids.ideal_gas` takes, and
the phase velocity and density at stated conditions, which is what it returns.
That makes the table an oracle and a ruler at once, because the two rows it
fails are the interesting ones: carbon dioxide and sulphur hexafluoride miss
their printed density by 0,7 and 2,1 per cent, which is the compressibility
factor and not an error in the arithmetic.

So these tests pin both halves: that the closure reproduces the table where it
is meant to, and that it misses it by the stated amount where it is not, which
is what keeps the docstring honest.
"""

from __future__ import annotations

import warnings

import pytest
import reference_data as ref

from phonometry import fluids
from phonometry.fluids import FluidAssumptionWarning, FluidPropertyUnavailable


def _at_table_conditions(gamma: float, molar_mass: float) -> fluids.Fluid:
    """A gas at the temperature and pressure the footnote of Table A1 states."""
    return fluids.ideal_gas(
        temperature_c=ref.HOPKINS_A1_TEMPERATURE_C,
        heat_capacity_ratio=gamma,
        molar_mass_kg_mol=molar_mass,
        static_pressure_pa=ref.HOPKINS_A1_STATIC_PRESSURE_PA,
    )


# ---------------------------------------------------------------------------
# The printed table
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("gas", "gamma", "molar_mass", "printed_speed", "printed_density"),
    ref.HOPKINS_A1_GASES,
)
def test_every_gas_of_table_a1_reproduces_its_printed_speed(
    gas: str,
    gamma: float,
    molar_mass: float,
    printed_speed: float,
    printed_density: float,
) -> None:
    """The speed is where the closure holds for all six, heavy ones included."""
    del printed_density
    got = _at_table_conditions(gamma, molar_mass).speed_of_sound

    assert got == pytest.approx(printed_speed, abs=0.5), gas


@pytest.mark.parametrize(
    ("gas", "gamma", "molar_mass", "printed_speed", "printed_density"),
    ref.HOPKINS_A1_GASES,
)
def test_the_light_gases_reproduce_their_printed_density(
    gas: str,
    gamma: float,
    molar_mass: float,
    printed_speed: float,
    printed_density: float,
) -> None:
    """Four of the six, to two parts in a thousand."""
    del printed_speed
    if gas not in ref.HOPKINS_A1_IDEAL_DENSITY_GASES:
        pytest.skip(f"{gas} is one of the two the closure is measured against")
    got = _at_table_conditions(gamma, molar_mass).density

    assert got == pytest.approx(printed_density, rel=0.002), gas


@pytest.mark.parametrize("gas", sorted(ref.HOPKINS_A1_COMPRESSIBILITY_GAP))
def test_the_heavy_molecules_miss_by_the_amount_the_model_states(gas: str) -> None:
    """The docstring claims 0,7 % and 2 %; this is what holds it to that."""
    row = next(r for r in ref.HOPKINS_A1_GASES if r[0] == gas)
    _, gamma, molar_mass, _, printed_density = row
    got = _at_table_conditions(gamma, molar_mass).density
    gap = (printed_density - got) / printed_density

    assert gap == pytest.approx(ref.HOPKINS_A1_COMPRESSIBILITY_GAP[gas], abs=0.002)
    assert gap > 0.0, "the ideal gas is the lighter one, always"


# ---------------------------------------------------------------------------
# What the fluid carries, and what it refuses
# ---------------------------------------------------------------------------
def test_the_fluid_says_which_model_made_it_and_what_that_is_worth() -> None:
    """A result that cannot say where its numbers came from is not one."""
    gas = _at_table_conditions(1.4, 0.029)

    assert gas.model == "ideal gas"
    assert "compressibility factor" in gas.validity


def test_a_transport_property_is_refused_rather_than_invented() -> None:
    """Nothing in the closure determines a viscosity, so nothing returns one."""
    gas = _at_table_conditions(1.4, 0.029)

    with pytest.raises(FluidPropertyUnavailable, match="ideal gas"):
        _ = gas.viscosity


def test_the_ratio_it_was_given_comes_back() -> None:
    """It is the one property the caller supplied, so it is carried, not lost."""
    assert _at_table_conditions(1.67, 0.04).heat_capacity_ratio == pytest.approx(1.67)


def test_an_assumed_pressure_is_announced() -> None:
    """Density is proportional to it, so assuming it silently would be wrong."""
    with pytest.warns(FluidAssumptionWarning, match="static pressure assumed"):
        fluids.ideal_gas(
            temperature_c=20.0, heat_capacity_ratio=1.4, molar_mass_kg_mol=0.029
        )


def test_a_supplied_pressure_is_silent() -> None:
    """Passing every condition leaves nothing to announce."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fluids.ideal_gas(
            temperature_c=20.0,
            heat_capacity_ratio=1.4,
            molar_mass_kg_mol=0.029,
            static_pressure_pa=101325.0,
        )


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_the_two_gas_properties_have_to_be_positive(bad: float) -> None:
    """A ratio or a molar mass of zero is not a gas."""
    with pytest.raises(ValueError, match="heat_capacity_ratio"):
        fluids.ideal_gas(
            temperature_c=20.0,
            heat_capacity_ratio=bad,
            molar_mass_kg_mol=0.029,
            static_pressure_pa=101325.0,
        )
    with pytest.raises(ValueError, match="molar_mass_kg_mol"):
        fluids.ideal_gas(
            temperature_c=20.0,
            heat_capacity_ratio=1.4,
            molar_mass_kg_mol=bad,
            static_pressure_pa=101325.0,
        )


def test_a_temperature_at_absolute_zero_is_refused() -> None:
    """The closure divides by the absolute temperature."""
    with pytest.raises(ValueError, match="temperature_c"):
        fluids.ideal_gas(
            temperature_c=-273.15,
            heat_capacity_ratio=1.4,
            molar_mass_kg_mol=0.029,
            static_pressure_pa=101325.0,
        )
