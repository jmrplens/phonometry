#  Copyright (c) 2026. Jose Manuel Requena Plens
"""materials.resilient subdomain of phonometry: resilient layers under floating floors and linings."""

from __future__ import annotations

from .dynamic_stiffness import (
    PUBLISHED_RESILIENT_LAYERS,
    DynamicStiffnessResult,
    DynamicStiffnessWarning,
    ResilientLayer,
    apparent_dynamic_stiffness,
    enclosed_gas_stiffness,
    floating_floor_resonance,
    installed_dynamic_stiffness,
    natural_frequency,
    resilient_layer,
)

__all__ = [
    "PUBLISHED_RESILIENT_LAYERS",
    "DynamicStiffnessResult",
    "DynamicStiffnessWarning",
    "ResilientLayer",
    "apparent_dynamic_stiffness",
    "enclosed_gas_stiffness",
    "floating_floor_resonance",
    "installed_dynamic_stiffness",
    "natural_frequency",
    "resilient_layer",
]
