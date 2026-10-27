#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A public parameter the body converts takes, for mypy too, what it converts.

``np.asarray`` takes a list of integers, a tuple, an integer array and a
nested list, and so does every function that hands its argument to it; a
parameter annotated ``list[float]`` or ``NDArray[np.float64]`` refused them
for mypy while the call ran, and ``list`` refused a list of a narrower type
besides (a ``list[AirLayer]`` is no ``list[Layer]``). These calls run, and
CI type checks every file in this directory alongside ``src`` and
``scripts``, so each one holds an annotation to what its body takes.
``scripts/check_parameter_annotations.py`` holds every public parameter to
the rule; this file holds the forms a caller writes.
"""

from __future__ import annotations

from typing import assert_type

import numpy as np
from numpy.typing import NDArray

from phonometry import aircraft, broadcast, filters, materials

#: Two channels of samples, ``[channels, samples]``, as a nested list.
_TWO_CHANNELS = [[0.1, -0.2, 0.3, -0.1] * 100, [0.05, 0.1, -0.1, 0.0] * 100]


def test_a_nested_list_is_a_multichannel_signal() -> None:
    """The ``[channels, samples]`` list ``true_peak_level`` documents."""
    levels = broadcast.true_peak_level(_TWO_CHANNELS, fs=48000.0)
    assert_type(levels, float | NDArray[np.float64])
    assert np.shape(levels) == (2,)


def test_integers_and_nested_lists_reach_a_table() -> None:
    """A list of integers is no ``list[float]`` to mypy; ``ArrayLike`` takes it."""
    powers = [1000, 2000]
    distances_m = [200, 400, 800]
    levels = [[90, 85, 80], [92, 87, 82]]
    out = aircraft.npd_level(powers, distances_m, levels, 1500.0, (300, 600))
    assert_type(out, NDArray[np.float64])
    assert out.shape == (2,)


def test_an_integer_array_and_a_list_of_integers_are_signals() -> None:
    """The array head of an overloaded filter takes any array-like."""
    weighted = filters.weighting_filter([0, 1, 0, -1] * 1000, 48000)
    assert_type(weighted, np.ndarray)
    counted = filters.weighting_filter(np.zeros(4000, dtype=np.int64), 48000)
    assert_type(counted, np.ndarray)


def test_a_list_of_one_kind_of_layer_is_a_sequence_of_layers() -> None:
    """A ``list[AirLayer]`` is no ``list[Layer]``, and is a ``Sequence[Layer]``."""
    layers: list[materials.AirLayer] = [materials.AirLayer(thickness_m=0.05)]
    result = materials.layered_absorber((250, 500, 1000), layers)
    assert_type(result, materials.LayeredAbsorberResult)
