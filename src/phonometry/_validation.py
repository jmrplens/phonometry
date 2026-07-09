#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Shared input-validation helpers (private).

Seeded by the library audit: modules used to hand-roll the same checks with
diverging NaN semantics and error-message styles. New code should validate
through these helpers; existing modules migrate as they are touched.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def require_1d_signal(x: ArrayLike, name: str = "signal") -> np.ndarray:
    """Coerce *x* to a float64 array and require a 1-D time series.

    Multichannel input is rejected rather than silently flattened (a raveled
    2-D signal concatenates the channels into one wrong series).

    :param x: The input signal.
    :param name: Parameter name used in the error message.
    :return: The validated ``float64`` array.
    :raises ValueError: for a non-1-D input.
    """
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"{name} must be a 1-D time series; got shape {arr.shape}. "
            "Process multichannel signals one channel at a time."
        )
    return arr
