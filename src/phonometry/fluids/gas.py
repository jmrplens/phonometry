#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""An ideal gas from the two numbers a gas table prints.

A table of gases prints a ratio of specific heats and a molar mass, and those
two close the ideal-gas state completely:

.. math::

   c = \sqrt{\frac{\gamma R T}{M}}
   \qquad
   \rho = \frac{p\,M}{R\,T}

so a caller who has a gas that is not air or water can still have a
:class:`~phonometry.fluids.Fluid` for it, computed rather than typed.

How far the closure goes
------------------------
Hopkins (2007) Table A1, PDF page 634 (printed p. 607), prints both columns
for six gases at 20 degC and 1,013e5 Pa, as its own footnote states. Against
it, the speeds land within 0,5 m/s for all six and the densities within
0,002 kg/m3 for the four light ones. Carbon dioxide comes out 0,7 % light and
sulphur hexafluoride 2 % light.

That shortfall is not an error in the arithmetic, it is the compressibility
factor: a real gas has ``rho = p M / (Z R T)``, so the ideal density is ``Z``
times the real one and the fraction missing is ``1 - Z``. It grows with the
molecule, and SF6, a heavy one whose attraction is not negligible at room
conditions, is exactly the gas a demonstration reaches for. The model says so
in :data:`IDEAL_GAS_VALIDITY` rather than pretending otherwise.

What it does not give
---------------------
Viscosity, thermal conductivity and the Prandtl number are transport
properties. Nothing in the ideal-gas closure determines them, so the returned
fluid does not carry them and reading one raises
:class:`~phonometry.fluids.FluidPropertyUnavailable` naming the model, which is
what every other fluid here does with a quantity its model did not fix.
"""

from __future__ import annotations

import math
import warnings

from ._state import Fluid, FluidAssumptionWarning
from .air import DEFAULT_STATIC_PRESSURE_PA

__all__ = [
    "IDEAL_GAS_VALIDITY",
    "MOLAR_GAS_CONSTANT",
    "ideal_gas",
]

#: The molar gas constant ``R``, in J/(mol K). Exact since the 2019 revision of
#: the SI fixed the Boltzmann and Avogadro constants.
MOLAR_GAS_CONSTANT = 8.31446261815324

#: What the ideal-gas closure is worth, stated so a caller can read it off the
#: fluid it gets back.
IDEAL_GAS_VALIDITY = (
    "ideal gas: exact for a dilute gas and within about 1 % of a printed table "
    "for the light gases at room conditions. The density comes out light by "
    "1 - Z, the compressibility factor's distance from unity, and that grows "
    "with the molecule: carbon dioxide is 0,7 % light and sulphur hexafluoride "
    "2 % against Hopkins Table A1, where the speeds still land within 0,5 m/s."
)

#: Celsius-to-kelvin offset, in kelvin.
_ABSOLUTE_ZERO_C_OFFSET = 273.15


def _warn_assumed_pressure(static_pressure_pa: float) -> None:
    """Announce the one condition this model will assume if it is not given."""
    msg = (
        f"static pressure assumed to be {static_pressure_pa:.0f} Pa, one "
        "standard atmosphere, because none was supplied. Density is "
        "proportional to it, so a measurement at 950 hPa is 6 % lighter than "
        "this. Pass static_pressure_pa to silence this."
    )
    warnings.warn(msg, FluidAssumptionWarning, stacklevel=3)


def ideal_gas(
    *,
    temperature_c: float,
    heat_capacity_ratio: float,
    molar_mass_kg_mol: float,
    static_pressure_pa: float | None = None,
) -> Fluid:
    r"""A gas at one state, from its ratio of specific heats and molar mass.

    :math:`c = \sqrt{\gamma R T / M}` and :math:`\rho = p M / (R T)`, the two
    ideal-gas relations, which is all a table that prints ``gamma`` and ``M``
    supports. See the module docstring for how far that goes and what it leaves
    out.

    :param temperature_c: Temperature ``t``, in degrees Celsius (above
        absolute zero).
    :param heat_capacity_ratio: Ratio of specific heats ``gamma`` (> 1). It is
        1,67 for a monatomic gas, about 1,4 for a diatomic one and lower for a
        polyatomic one, and it is above 1 for every gas, because ``gamma`` is
        ``c_p/c_v`` and ``c_p - c_v`` is the gas constant.
    :param molar_mass_kg_mol: Molar mass ``M``, in kg/mol (> 0). The tables
        print kg/mol, so 0,028 95 for dry air and not 28,95.
    :param static_pressure_pa: Static pressure ``p``, in pascals (> 0). When
        omitted, one standard atmosphere is assumed and a
        :class:`~phonometry.fluids.FluidAssumptionWarning` says so, because the
        density is proportional to it.
    :return: The :class:`~phonometry.fluids.Fluid` at that state, carrying a
        density, a speed of sound and the ratio of specific heats it was given.
    :raises ValueError: for a non-positive input or a temperature at or below
        absolute zero.
    """
    from .._internal.validation import require_above_absolute_zero, require_positive

    temperature = require_above_absolute_zero(temperature_c, "temperature_c")
    gamma = require_positive(heat_capacity_ratio, "heat_capacity_ratio")
    if gamma <= 1.0:
        msg = (
            f"'heat_capacity_ratio' must be greater than 1, not {gamma:g}: it is "
            "c_p/c_v, and c_p - c_v is the specific gas constant, which is "
            "positive"
        )
        raise ValueError(msg)
    molar_mass = require_positive(molar_mass_kg_mol, "molar_mass_kg_mol")
    if static_pressure_pa is None:
        pressure = DEFAULT_STATIC_PRESSURE_PA
        _warn_assumed_pressure(pressure)
    else:
        pressure = require_positive(static_pressure_pa, "static_pressure_pa")

    kelvin = temperature + _ABSOLUTE_ZERO_C_OFFSET
    speed = math.sqrt(gamma * MOLAR_GAS_CONSTANT * kelvin / molar_mass)
    density = pressure * molar_mass / (MOLAR_GAS_CONSTANT * kelvin)
    return Fluid(
        temperature_c=float(temperature),
        static_pressure_pa=float(pressure),
        composition={"molar_mass_kg_mol": float(molar_mass)},
        model="ideal gas",
        validity=IDEAL_GAS_VALIDITY,
        properties={
            "density": density,
            "speed_of_sound": speed,
            "heat_capacity_ratio": float(gamma),
        },
    )
