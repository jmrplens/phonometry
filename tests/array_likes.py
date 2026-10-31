#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Objects of the caller's that numpy reads as the very memory they hold.

A column of a data frame or a labelled array does it through ``__array__``:
``np.asarray`` of it is the caller's own array, not a copy, so a record that
sealed what ``np.asarray`` gave it sealed the caller's array. The three
columns differ in how they answer ``copy``, the keyword NumPy 2 passes to
``__array__``: one honours it, one is older than it and takes no such
keyword, and one takes it and ignores it. An object can also publish its
memory through ``__array_interface__`` (on its class, or set on itself, as
some libraries do) or ``__array_struct__``, or through the buffer protocol,
as a ``memoryview`` does: ``np.asarray`` of any of them is a new array over
the caller's memory, and a record that kept the object kept that memory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import DTypeLike


class Column:
    """An array-like that copies only when a copy is asked for."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __array__(
        self, dtype: DTypeLike | None = None, *, copy: bool | None = None
    ) -> np.ndarray:
        """The array it holds, or a copy of it when one is asked for."""
        if copy:
            return np.array(self.array, dtype=dtype)
        return np.asarray(self.array, dtype=dtype)


class OldStyleColumn:
    """An array-like written before NumPy 2, whose ``__array__`` takes no ``copy``."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __array__(self, dtype: DTypeLike | None = None) -> np.ndarray:
        """The array it holds, whatever NumPy asks."""
        return np.asarray(self.array, dtype=dtype)


class CarelessColumn:
    """An array-like that takes ``copy`` and hands back the array it holds anyway."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __array__(
        self, dtype: DTypeLike | None = None, *, copy: bool | None = None
    ) -> np.ndarray:
        """The array it holds, a copy asked for or not."""
        del copy
        return np.asarray(self.array, dtype=dtype)


class Interface:
    """An object that publishes the memory of the array it holds."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    @property
    def __array_interface__(self) -> dict[str, Any]:
        """The interface of the array it holds, its memory included."""
        return self.array.__array_interface__


class OwnInterface:
    """An object that sets the interface of the array it holds on itself."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array
        self.__array_interface__ = array.__array_interface__


class Struct:
    """An object that publishes the memory of the array it holds as a C struct."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    @property
    def __array_struct__(self) -> object:
        """The C-level interface of the array it holds."""
        return self.array.__array_struct__


#: Every kind, by the name a test case is given.
ARRAY_LIKES: dict[str, Callable[[np.ndarray], object]] = {
    "a column that honours copy": Column,
    "a column older than copy": OldStyleColumn,
    "a column that ignores copy": CarelessColumn,
    "an array interface": Interface,
    "an array interface set on the object": OwnInterface,
    "an array struct": Struct,
    "a memoryview": memoryview,
}
