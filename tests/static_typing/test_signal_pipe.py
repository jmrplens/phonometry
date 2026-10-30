#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``Signal.pipe`` gives a type checker what the function it calls returns.

``pipe(func, *args, **kwargs)`` is typed by the function it is handed: the
arguments after it are checked against that function's own, after the
Signal it takes first, and the result is the function's return. An
overloaded function of the library picks the head the Signal matches, so a
chain keeps its types to the end. ``tests/io/test_io_signal_structure.py``
holds the runtime; this file holds the types, and only because CI type
checks every file in this directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

from typing import assert_type

import numpy as np
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
