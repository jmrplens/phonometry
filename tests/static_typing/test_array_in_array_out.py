#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A function of a number or an array of them returns, for mypy too, what it was handed.

An array in, an array out: a number gives a ``float``, a sequence or an array
an array, and an argument whose shape a type checker cannot know (an
``ArrayLike``, a nested list) the union. The heads take their arguments as
type parameters bounded by the three forms, because mypy reads an argument
whose type holds an ``Any`` (the shape of every ``NDArray[np.float64]`` does)
as matching every head it fits and returns ``Any`` unless those heads agree
on its type; with a bound, each head is inferred to the argument's own type
and the first one stands. ``tests/test_scalar_or_array_returns.py`` holds the
runtime to the heads; this file holds the heads, for one function of each
shape, and it only holds them because CI type checks every file in this
directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, assert_type

import numpy as np
from numpy.typing import NDArray

from phonometry import emission, fluids, room, vibration

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

_ARRAY: NDArray[np.float64] = np.array([0.2, 0.3])
_ANY_SHAPE: np.ndarray[tuple[Any, ...], np.dtype[np.float64]] = np.array([0.2, 0.3])
_ARRAY_LIKE: ArrayLike = 0.2
_ZONES = vibration.ZoneBoundaries(a_b=1.0, b_c=2.0, c_d=3.0)


def test_numbers_read_as_a_float() -> None:
    """A Python number, a numpy one or a mean of an array is one value."""
    assert_type(room.room_constant(100.0, 0.2), float)
    assert_type(room.schroeder_frequency(1, 100.0), float)
    assert_type(room.room_constant(100.0, np.float32(0.2)), float)
    assert_type(room.schroeder_frequency(np.int64(1), 100.0), float)
    assert_type(room.room_constant(100.0, np.mean(_ARRAY)), float)


def test_arrays_read_as_an_array() -> None:
    """A list, an array of any shape and a zero-dimensional array are arrays."""
    assert_type(room.room_constant(100.0, [0.2, 0.3]), NDArray[np.float64])
    assert_type(room.room_constant(100.0, _ARRAY), NDArray[np.float64])
    assert_type(room.room_constant(100.0, _ANY_SHAPE), NDArray[np.float64])
    assert_type(room.room_constant(100.0, np.array(0.2)), NDArray[np.float64])


def test_what_mypy_cannot_shape_reads_as_the_union() -> None:
    """An ``ArrayLike`` or a nested list may be either."""
    assert_type(room.room_constant(100.0, _ARRAY_LIKE), float | NDArray[np.float64])
    assert_type(room.room_constant(100.0, [[0.2, 0.3]]), float | NDArray[np.float64])


def test_the_first_array_among_several_arguments_decides() -> None:
    """Numbers everywhere give a float; one array anywhere gives an array."""
    assert_type(room.critical_distance(50.0, directivity=2.0), float)
    assert_type(room.critical_distance(_ARRAY, directivity=2.0), NDArray[np.float64])
    assert_type(room.critical_distance(50.0, directivity=_ARRAY), NDArray[np.float64])
    assert_type(
        room.critical_distance(absorption_area=[50.0, 60.0]), NDArray[np.float64]
    )
    assert_type(
        fluids.sea_water_sound_speed(10.0, 35.0, [10.0, 100.0]), NDArray[np.float64]
    )
    assert_type(
        emission.emission_sound_pressure_level(80.0, local_correction=_ARRAY),
        NDArray[np.float64],
    )


def test_a_grade_is_a_letter_or_an_array_of_them() -> None:
    """The zone graders follow the same rule with a ``Literal`` for one grade."""
    assert_type(vibration.evaluation_zone(2.5, _ZONES), Literal["A", "B", "C", "D"])
    zones = vibration.evaluation_zone(_ARRAY, _ZONES)
    assert_type(zones, NDArray[np.str_])


def test_the_functions_keyed_on_another_argument() -> None:
    """``axis`` and a missing ``frequency`` decide what the heads say."""
    levels = np.array([[60.0, 62.0], [61.0, 63.0]])
    assert_type(vibration.passage_average_level(levels), float)
    assert_type(vibration.passage_average_level(levels, axis=0), NDArray[np.float64])
    assert_type(
        vibration.guideline_velocity("residential", location="top_floor"), float
    )
