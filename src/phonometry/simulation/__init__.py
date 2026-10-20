#  Copyright (c) 2026. Jose Manuel Requena Plens
"""simulation domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .compute import (
    Compute,
    ComputeDeviceError,
    ComputeFallbackWarning,
    ComputeImportError,
    RunProvenance,
    use,
)
from .elastic_fdtd import (
    AIR,
    ALUMINUM,
    CONCRETE,
    STEEL,
    WATER,
    ElasticBoundaries,
    ElasticFDTD2D,
    ElasticFDTDResult,
    ElasticRecording,
    ExplosionSource,
    ForceSource,
    Material,
    elastic_fdtd_simulation,
    scholte_speed,
)
from .fdtd import (
    FDTD2D,
    ContourProbe,
    CWSource,
    FDTDResult,
    GaussianPulse,
    PlaneWaveSource,
    SignalSource,
    fdtd_simulation,
)
from .ntff import SIMULATION_AIR, ContourPhasors, far_field_from_contour

__all__ = [
    "AIR",
    "SIMULATION_AIR",
    "ALUMINUM",
    "CONCRETE",
    "FDTD2D",
    "STEEL",
    "WATER",
    "CWSource",
    "Compute",
    "ComputeDeviceError",
    "ComputeFallbackWarning",
    "ComputeImportError",
    "ContourPhasors",
    "ContourProbe",
    "ElasticBoundaries",
    "ElasticFDTD2D",
    "ElasticFDTDResult",
    "ElasticRecording",
    "ExplosionSource",
    "FDTDResult",
    "ForceSource",
    "GaussianPulse",
    "Material",
    "PlaneWaveSource",
    "RunProvenance",
    "SignalSource",
    "elastic_fdtd_simulation",
    "far_field_from_contour",
    "fdtd_simulation",
    "scholte_speed",
    "use",
]
