#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Read-only arrays for the tables and the results the library publishes (private).

A module-level array is shared by every caller that imports it, so an
in-place operation on it (``OCTAVE_BANDS *= 2``, or a function that writes
into the array it was handed) changes the table for the rest of the process,
silently. Every published array is therefore built through :func:`read_only`,
the array counterpart of wrapping a published dictionary in
:class:`types.MappingProxyType`.

A result has the opposite exposure. ``np.asarray`` hands back the caller's own
array when it is already of the asked type, so a result that keeps what it
was given shares memory with the caller, and changing the caller's array
afterwards changes the result. An array a result keeps from its arguments is
therefore a copy of its own, made through :func:`read_only_copy`;
``scripts/check_array_aliasing.py`` holds the package to it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, DTypeLike, NDArray


def read_only[A: np.ndarray](array: A) -> A:
    """Return *array* with its ``writeable`` flag cleared.

    The array is not copied: the flag is cleared on the object itself, so the
    caller hands over a freshly built array and keeps no writeable reference
    to it. The array still owns its data, so a caller who sets the flag back
    on can write again; what this stops is the accident, an in-place operation
    nobody meant to aim at a shared table.

    Never hand it an array that came in as an argument: it would clear the
    flag on the caller's own array. :func:`read_only_copy` is for those.

    :param array: A newly built array that is about to be published.
    :return: The same array, which now refuses in-place writes.
    """
    array.flags.writeable = False
    return array


@overload
def read_only_copy(array: None, dtype: DTypeLike | None = None) -> None: ...


@overload
def read_only_copy(
    array: ArrayLike, dtype: DTypeLike | None = None
) -> NDArray[Any]: ...


def read_only_copy(
    array: ArrayLike | None, dtype: DTypeLike | None = None
) -> NDArray[Any] | None:
    """A copy of *array* that refuses in-place writes, for a result to keep.

    The copy is the result's own, so nothing the caller does to the array it
    passed reaches the result, and the flag is cleared on the copy, never on
    the caller's array. ``None``, an optional field left out, stays ``None``.

    :param array: The array, or anything ``np.array`` reads as one, that a
        result keeps from its arguments.
    :param dtype: The type to copy into; the array's own when omitted.
    :return: A new read-only array, or ``None``.
    """
    if array is None:
        return None
    return read_only(np.array(array, dtype=dtype))
