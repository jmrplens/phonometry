#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Multichannel (2-D) time signals are rejected, never silently flattened.

A raveled stereo signal concatenates the channels into one wrong series;
every single-channel analysis entry point must refuse it instead (library
audit finding).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable

_STEREO = np.zeros((2, 4800))


@pytest.mark.parametrize(
    "analyze",
    [
        ph.psychoacoustics.loudness_ecma,
        ph.psychoacoustics.tonality_ecma,
        ph.psychoacoustics.roughness_ecma,
        ph.psychoacoustics.fluctuation_strength_ecma,
        ph.psychoacoustics.loudness_moore_glasberg,
        ph.environment.sound_pressure_level_history,
        ph.environment.impulsive_sound_adjustment,
    ],
    ids=[
        "loudness_ecma",
        "tonality_ecma",
        "roughness_ecma",
        "fluctuation_strength_ecma",
        "moore_glasberg",
        "sound_pressure_level_history",
        "impulsive_sound_adjustment",
    ],
)
def test_stereo_input_is_rejected(
    analyze: Callable[[np.ndarray, float], object],
) -> None:
    """The refusal names the parameter the caller passed, ``x``."""
    with pytest.raises(ValueError, match="^'x' must be a 1-D time series"):
        analyze(_STEREO, 48000.0)
