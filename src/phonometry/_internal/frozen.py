#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Read-only arrays for the tables the library publishes (private).

A module-level array is shared by every caller that imports it, so an
in-place operation on it (``OCTAVE_BANDS *= 2``, or a function that writes
into the array it was handed) changes the table for the rest of the process,
silently. Every published array is therefore built through :func:`read_only`,
the array counterpart of wrapping a published dictionary in
:class:`types.MappingProxyType`.
"""

from __future__ import annotations

import numpy as np


def read_only[A: np.ndarray](array: A) -> A:
    """Return *array* with its ``writeable`` flag cleared.

    The array is not copied: the flag is cleared on the object itself, so the
    caller hands over a freshly built array and keeps no writeable reference
    to it.

    :param array: A newly built array that is about to be published.
    :return: The same array, which now refuses any write.
    """
    array.flags.writeable = False
    return array
