#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A filter object types a Signal in as a Signal out, and an array as an array.

``filters.weighting_filter``, ``filters.parametric_eq`` and
``filters.time_weighting`` were overloaded on their input: a ``Signal`` gives
a ``Signal`` (a ``TimeWeightedEnvelope`` for the time weighting) and an array
gives an array. Their reusable forms, ``WeightingFilter.filter``,
``ParametricEQ.filter`` and ``TimeWeighting.process``, return the same thing
on the same terms but said ``Signal | ndarray`` for either input, so
``y: NDArray[np.float64] = wf.filter(x)`` was a type error in mypy and pyright
for a call that cannot return a Signal. Each method now has the heads of its
function, and this file holds the two forms to the same types: CI type checks
every file in this directory alongside ``src`` and ``scripts``, so a head that
goes fails the build. ``scripts/check_return_overloads.py`` holds every
function of the package that returns a record or an array to the same rule.
"""

from __future__ import annotations

from typing import assert_type

import numpy as np
from numpy.typing import NDArray

from phonometry import filters, io

_FS = 48000.0
_SAMPLES: NDArray[np.float64] = np.random.default_rng(3).standard_normal(4800)
_TAKE = io.Signal(_SAMPLES, _FS)
_SECTION = filters.EQSection(filter_type="peaking", f0=1000.0, gain_db=6.0, q=1.0)


def test_a_weighting_filter_types_each_input_as_its_function_does() -> None:
    """The object and the function give a Signal a Signal and an array an array."""
    weighting = filters.WeightingFilter(_FS, "A")
    weighted_take = assert_type(weighting.filter(_TAKE), io.Signal)
    weighted: NDArray[np.float64] = assert_type(
        weighting.filter(_SAMPLES), NDArray[np.float64]
    )
    assert_type(filters.weighting_filter(_TAKE), io.Signal)
    assert_type(filters.weighting_filter(_SAMPLES, _FS), NDArray[np.float64])
    assert isinstance(weighted_take, io.Signal)
    assert not isinstance(weighted, io.Signal)
    np.testing.assert_array_equal(
        weighted, filters.weighting_filter(_SAMPLES, _FS, "A")
    )


def test_a_parametric_eq_types_each_input_as_its_function_does() -> None:
    """The cascade and its function agree, input for input."""
    cascade = filters.ParametricEQ(_FS, _SECTION)
    equalized_take = assert_type(cascade.filter(_TAKE), io.Signal)
    equalized: NDArray[np.float64] = assert_type(
        cascade.filter(_SAMPLES), NDArray[np.float64]
    )
    assert_type(filters.parametric_eq(_TAKE, sections=_SECTION), io.Signal)
    assert_type(
        filters.parametric_eq(_SAMPLES, _FS, sections=_SECTION), NDArray[np.float64]
    )
    assert isinstance(equalized_take, io.Signal)
    assert not isinstance(equalized, io.Signal)


def test_a_time_weighting_types_each_block_as_its_function_does() -> None:
    """A Signal block gives the envelope record, an array block a bare array."""
    envelope = assert_type(
        filters.TimeWeighting(_FS, "fast").process(_TAKE),
        filters.TimeWeightedEnvelope,
    )
    mean_square: NDArray[np.float64] = assert_type(
        filters.TimeWeighting(_FS, "fast").process(_SAMPLES), NDArray[np.float64]
    )
    assert_type(filters.time_weighting(_TAKE), filters.TimeWeightedEnvelope)
    assert_type(filters.time_weighting(_SAMPLES, _FS), NDArray[np.float64])
    assert isinstance(envelope, filters.TimeWeightedEnvelope)
    assert not isinstance(mean_square, filters.TimeWeightedEnvelope)
