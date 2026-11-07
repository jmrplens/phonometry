#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A text where an array of numbers goes is refused by a type checker too.

numpy's ``ArrayLike`` admits any ``str`` and any ``bytes``, so
``signals.leq("not a signal")`` type-checked, in mypy and in pyright, and only
the call refused it. Every public parameter that takes numbers takes the
package's ``NumericArrayLike`` instead, which is ``ArrayLike`` without its
texts, and so does every alias that stands for such a parameter: the
``Signal`` or an array of a signal input, values by band, the rows of a
curve, and the last head of a function overloaded on the shape of its input.
Each refused call below runs to the ``TypeError`` the library raises and
carries the code mypy refuses it with; CI type checks every file in this
directory with unused ignores reported, so a refusal that goes fails the
build. The calls without an ignore are the forms of numbers the parameters
keep taking. ``scripts/check_parameter_annotations.py`` holds every public
parameter, overload head, declared constructor and record field to the rule.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import building, emission, environment, filters, io, room, signals

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import ArrayLike, NDArray

_FS = 48000.0
_NOISE: NDArray[np.float64] = np.random.default_rng(7).standard_normal(4800)
_SINGLE: NDArray[np.float32] = _NOISE.astype(np.float32)
_TWO_CHANNELS: NDArray[np.float64] = np.vstack((_NOISE, _NOISE))
_TAKE = io.Signal(_NOISE, _FS)
_TEXT = "must be numbers, not text"


def test_a_signal_input_refuses_a_text_and_takes_numbers() -> None:
    """A recording is a Signal or an array of numbers, never a text."""
    with pytest.raises(TypeError, match=_TEXT):
        signals.leq("not a signal")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=_TEXT):
        signals.leq(b"not a signal")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=_TEXT):
        filters.octave_filter("not a signal", _FS)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=_TEXT):
        emission.sound_intensity(
            "not a signal",  # type: ignore[arg-type]
            _NOISE,
            _FS,
            spacing_m=0.012,
        )
    for numbers in (_NOISE, _SINGLE, _TWO_CHANNELS, _TAKE, [0.1, -0.2, 0.3]):
        signals.leq(numbers)
    signals.leq([[0.1, -0.2], [0.3, 0.4]])
    signals.leq((0.1, -0.2, 0.3))


def _typed_as_numbers(rows: Sequence[float], one: float) -> None:
    """Code of a caller's own that says numbers hands them over."""
    signals.leq(rows)
    signals.leq(_NOISE)
    room.room_constant(100.0, one)


def _typed_as_array_like(levels: ArrayLike) -> None:
    """``ArrayLike`` says a text may be there, so it is no array of numbers."""
    signals.leq(levels)  # type: ignore[arg-type]


def test_code_of_your_own_hands_over_numbers_and_not_numpy_array_like() -> None:
    """A parameter typed as numbers passes, and one typed ``ArrayLike`` does not.

    A type checker cannot let a value that may be a text through to a
    parameter that refuses one; an ``NDArray``, a ``Sequence[float]`` or a
    ``float`` says numbers. The values are parameters of the caller's own
    functions, as they are in code that hands them on: a variable assigned in
    the same scope is narrowed to what it was given, which pyright reads as a
    list of numbers whatever its annotation says.
    """
    _typed_as_numbers([0.1, -0.2, 0.3], 0.2)
    _typed_as_array_like([0.1, -0.2, 0.3])


def test_a_number_or_an_array_refuses_a_text_on_its_last_head() -> None:
    """A function overloaded on the shape of its input refuses a text on every head."""
    with pytest.raises(TypeError, match="'mean_absorption' must be numbers"):
        room.room_constant(100.0, "0.2")  # type: ignore[type-var]
    room.room_constant(100.0, 0.2)
    room.room_constant(100.0, [0.2, 0.3])
    room.room_constant(100.0, np.array([0.2, 0.3]))


def test_values_by_band_refuse_a_text() -> None:
    """Values by band are a mapping of band to value or an array of numbers."""
    with pytest.raises(TypeError, match=_TEXT):
        building.weighted_rating("45 47 50 52 55")  # type: ignore[arg-type]


def test_a_record_field_of_numbers_refuses_a_text() -> None:
    """A record built by a caller takes the numbers of its field, not a text."""
    with pytest.raises(TypeError, match=_TEXT):
        environment.SourceEmission(sound_power_level="90")  # type: ignore[arg-type]
    environment.SourceEmission(sound_power_level=[90.0] * 8)
