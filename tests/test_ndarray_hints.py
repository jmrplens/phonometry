#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tests that read an annotation of an array read it on every NumPy.

``numpy.typing.NDArray`` changed form in NumPy 2.5, and the census of number
returns, the record display test and the verdict shape test, which asked
whether an annotation's origin was ``np.ndarray``, read every array at the
dependency floors and none at the pins. These cases run in both jobs, so the
reading :mod:`ndarray_hints` gives is the same in each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from ndarray_hints import ndarray_of, ndarray_scalar
from numpy.typing import NDArray

from phonometry._internal.types import Real

if TYPE_CHECKING:
    from collections.abc import Callable

type _Mask = NDArray[np.bool_]
type _Masks[T: np.generic] = list[NDArray[T]]
#: Its value names what only a type checker imports, which no run can evaluate.
type _Unknown = Callable[[], NDArray[np.bool_]]


@pytest.mark.parametrize(
    ("hint", "scalar"),
    [
        (NDArray[np.bool_], np.bool_),
        (NDArray[np.complex128], np.complex128),
        (NDArray[np.floating[Any]], np.floating[Any]),
        (np.ndarray[tuple[int], np.dtype[np.int64]], np.int64),
        (Real, np.float64),
        (_Mask, np.bool_),
    ],
)
def test_an_array_is_read_with_its_scalar(hint: object, scalar: object) -> None:
    """numpy's alias, the package's and a ``type`` statement name their array."""
    assert ndarray_of(hint) is not None
    assert ndarray_scalar(hint) == scalar


def test_a_bare_array_names_no_scalar() -> None:
    assert ndarray_of(np.ndarray) is np.ndarray
    assert ndarray_scalar(np.ndarray) is None


@pytest.mark.parametrize(
    "hint",
    [
        float,
        complex,
        list[float],
        float | NDArray[np.float64],
        _Masks[np.bool_],
        _Unknown,
        None,
    ],
)
def test_what_is_no_array_alone_names_none(hint: object) -> None:
    """A union, a list of arrays and an alias that cannot be read name no array."""
    assert ndarray_of(hint) is None
    assert ndarray_scalar(hint) is None
