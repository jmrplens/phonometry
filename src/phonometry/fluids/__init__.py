#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The media sound travels through: humid air by IEC 61094-2 Annex F, sea water,
ideal gases, and the fluid states and nonlinearity parameters books print.

Each state is computed from the conditions that were measured rather than
assumed, or read from the page that prints it. Every other package may import
this one without an architecture edge, the way they import
:mod:`phonometry.filters`, :mod:`phonometry.signals` and
:mod:`phonometry.metrology`: a medium is not a domain of application but
something every domain needs, and eleven identical edges would record nothing.

What lives here is the *physics* of a fluid. A simplified formula a measurement
standard prints inside its own procedure stays in that standard's module, where
its clause can be cited beside it, and a constant frozen by a conformance row
never moves at all. Those three are different things, and keeping them apart is
what lets better physics reach a caller without any measurement silently
ceasing to reproduce the standard it claims.
"""

from __future__ import annotations

from ._air import (
    DEFAULT_CO2_MOLE_FRACTION,
    DEFAULT_RELATIVE_HUMIDITY_PERCENT,
    DEFAULT_STATIC_PRESSURE_PA,
    air,
)
from ._state import (
    Fluid,
    FluidAssumptionWarning,
    FluidPropertyUnavailableError,
    FluidWarning,
    characteristic_impedance,
)
from .catalogue import (
    PUBLISHED_FLUIDS,
    PUBLISHED_GASES,
    Gas,
    gases_named,
)
from .gas import (
    IDEAL_GAS_VALIDITY,
    MOLAR_GAS_CONSTANT_J_MOL_K,
    ideal_gas,
)
from .nonlinearity import (
    PUBLISHED_NONLINEARITY,
    NonlinearityParameter,
    nonlinearity_named,
)
from .water import (
    depth_to_absolute_pressure_pa,
    depth_to_gauge_pressure_mpa,
    sea_water,
    sea_water_density,
    sea_water_sound_speed,
)

__all__ = [
    "DEFAULT_CO2_MOLE_FRACTION",
    "DEFAULT_RELATIVE_HUMIDITY_PERCENT",
    "DEFAULT_STATIC_PRESSURE_PA",
    "IDEAL_GAS_VALIDITY",
    "MOLAR_GAS_CONSTANT_J_MOL_K",
    "PUBLISHED_FLUIDS",
    "PUBLISHED_GASES",
    "PUBLISHED_NONLINEARITY",
    "Fluid",
    "FluidAssumptionWarning",
    "FluidPropertyUnavailableError",
    "FluidWarning",
    "Gas",
    "NonlinearityParameter",
    "air",
    "characteristic_impedance",
    "gases_named",
    "ideal_gas",
    "nonlinearity_named",
    "depth_to_absolute_pressure_pa",
    "depth_to_gauge_pressure_mpa",
    "sea_water",
    "sea_water_density",
    "sea_water_sound_speed",
]
