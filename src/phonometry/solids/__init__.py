#  Copyright (c) 2026. Jose Manuel Requena Plens
"""solids domain of phonometry (see module docstrings).

The elastic constants of a solid and the wave speeds that follow from them.
Like :mod:`phonometry.fluids`, this is not a domain of application but
something the domains need: twenty-one public parameters across
:mod:`phonometry.building`, :mod:`phonometry.vibration` and
:mod:`phonometry.materials` ask for a Young's modulus or a Poisson ratio, and
until now every conversion between a modulus and a wave speed was done in the
caller's head.

What lives here is the *physics* of a solid. A simplified relation a
measurement standard prints inside its own procedure stays in that standard's
module, where its clause can be cited beside it, exactly as for fluids.
"""

from __future__ import annotations

from .catalogue import PUBLISHED_SOLIDS, SolidMaterial, solids_named
from .damping import PUBLISHED_DAMPING, DampingMaterial, damping_named
from .damping_treatments import (
    PUBLISHED_DAMPING_TREATMENTS,
    DampingTreatment,
    damping_treatments_named,
)
from .elastic import (
    DEFAULT_SPEED_OF_SOUND_M_S,
    beam_longitudinal_speed,
    bulk_longitudinal_speed,
    plate_longitudinal_speed,
    thickness_critical_frequency_product,
    youngs_modulus_from_beam_speed,
    youngs_modulus_from_bulk_speed,
    youngs_modulus_from_plate_speed,
)
from .nonlinearity import (
    PUBLISHED_SOLID_NONLINEARITY,
    SolidNonlinearity,
    solid_nonlinearity_named,
)
from .orthotropic_wood import (
    PUBLISHED_ORTHOTROPIC_WOOD,
    OrthotropicWood,
    orthotropic_wood_named,
)
from .plateau import PUBLISHED_PLATEAU_DATA, PlateauMaterial, plateau_material_named

__all__ = [
    "PUBLISHED_SOLID_NONLINEARITY",
    "SolidNonlinearity",
    "solid_nonlinearity_named",
    "PUBLISHED_DAMPING_TREATMENTS",
    "DampingTreatment",
    "damping_treatments_named",
    "DEFAULT_SPEED_OF_SOUND_M_S",
    "PUBLISHED_DAMPING",
    "PUBLISHED_SOLIDS",
    "DampingMaterial",
    "SolidMaterial",
    "beam_longitudinal_speed",
    "bulk_longitudinal_speed",
    "PUBLISHED_ORTHOTROPIC_WOOD",
    "PUBLISHED_PLATEAU_DATA",
    "OrthotropicWood",
    "PlateauMaterial",
    "orthotropic_wood_named",
    "plateau_material_named",
    "damping_named",
    "plate_longitudinal_speed",
    "solids_named",
    "thickness_critical_frequency_product",
    "youngs_modulus_from_beam_speed",
    "youngs_modulus_from_bulk_speed",
    "youngs_modulus_from_plate_speed",
]
