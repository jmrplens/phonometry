#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``Signal.pipe`` gives a type checker what the function it calls returns.

``pipe(func, *args, **kwargs)`` is typed by the function it is handed: the
arguments after it are checked against that function's own, after the
Signal it takes first, and the result is the function's return. An
overloaded function of the library picks the head the Signal matches, so a
chain keeps its types to the end. ``tests/io/test_io_signal_structure.py``
holds the runtime; this file holds the types, and only because CI type
checks every file in this directory alongside ``src`` and ``scripts``.

The arguments are held by the calls a checker refuses: each carries the
``type: ignore`` of the error it raises, and mypy, which reports an ignore
that silences nothing, fails the day ``pipe`` stops checking them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

import numpy as np
import pytest
from numpy.typing import NDArray

from phonometry import filters, io, signals

_TAKE = io.Signal(np.zeros((2, 4800)), 48000.0, calibration_factor=2.0)


def test_a_function_of_the_library_keeps_its_return() -> None:
    """A Signal in gives the Signal head, and a chain carries it on."""
    assert_type(_TAKE.pipe(filters.weighting_filter), io.Signal)
    assert_type(_TAKE.pipe(filters.weighting_filter, weighting="C"), io.Signal)
    assert_type(
        _TAKE.pipe(filters.time_weighting, mode="slow"), filters.TimeWeightedEnvelope
    )
    assert_type(
        _TAKE.pick(0).pipe(filters.weighting_filter).crop(0.0, 0.05).pipe(signals.leq),
        float | NDArray[np.float64],
    )


def test_a_lambda_returns_what_it_computes() -> None:
    """Any callable taking the Signal first: its return is the chain's end."""
    assert_type(_TAKE.pipe(lambda take, k: take.n_samples * k, 2), int)


def test_a_choice_its_function_refuses_is_refused_by_that_function() -> None:
    """A spelling the function does not take is refused by a checker, and by the function."""
    with pytest.raises(ValueError, match="'weighting' must be one of"):
        _TAKE.pipe(filters.weighting_filter, weighting="Q")  # type: ignore[arg-type]


if TYPE_CHECKING:
    # Checked and never run: a keyword the function does not take, and more
    # positional arguments than it has.
    _TAKE.pipe(filters.weighting_filter, weightin="A")  # type: ignore[arg-type]
    _TAKE.pipe(signals.leq, 1.0, 2.0, 3.0, 4.0, 5.0)  # type: ignore[arg-type, call-arg]
