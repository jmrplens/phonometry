#  Copyright (c) 2026. Jose M. Requena-Plens
"""room domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .enclosed_space_absorption import (
    ReverberationResult,
    air_absorption_area,
    enclosed_space_reverberation,
    equivalent_absorption_area,
    hard_object_absorption,
    object_fraction,
    reverberation_time,
)
from .open_plan import OpenPlanResult, open_plan_metrics
from .reverberation_prediction import (
    ReverberationModelResult,
    arau_puchades_reverberation_time,
    eyring_reverberation_time,
    fitzroy_reverberation_time,
    mean_absorption,
    millington_sette_reverberation_time,
    reverberation_time_models,
    sabine_reverberation_time,
)
from .room_acoustics import (
    DecayCurve,
    RoomAcousticsResult,
    decay_curve,
    room_parameters,
)
from .room_ir import (
    ImpulseResponseResult,
    ImpulseResponseWarning,
    impulse_response,
    inverse_filter,
    mls_impulse_response,
    mls_signal,
    sweep_signal,
)
from .room_noise import (
    NCResult,
    RCResult,
    nc_curve,
    noise_criterion,
    rc_curve,
    room_criterion,
)

__all__ = [
    "DecayCurve",
    "ImpulseResponseResult",
    "ImpulseResponseWarning",
    "NCResult",
    "OpenPlanResult",
    "RCResult",
    "ReverberationModelResult",
    "ReverberationResult",
    "RoomAcousticsResult",
    "air_absorption_area",
    "arau_puchades_reverberation_time",
    "decay_curve",
    "enclosed_space_reverberation",
    "equivalent_absorption_area",
    "eyring_reverberation_time",
    "fitzroy_reverberation_time",
    "hard_object_absorption",
    "impulse_response",
    "inverse_filter",
    "mean_absorption",
    "millington_sette_reverberation_time",
    "mls_impulse_response",
    "mls_signal",
    "nc_curve",
    "noise_criterion",
    "object_fraction",
    "open_plan_metrics",
    "rc_curve",
    "reverberation_time",
    "reverberation_time_models",
    "room_criterion",
    "room_parameters",
    "sabine_reverberation_time",
    "sweep_signal",
]
