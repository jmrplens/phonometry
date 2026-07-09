#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Shared input-validation helpers (private).

Seeded by the library audit: modules used to hand-roll the same checks with
diverging NaN semantics and error-message styles. New code should validate
through these helpers; existing modules migrate as they are touched.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


def require_positive(value: float, name: str) -> float:
    """Require a positive finite number (rejects NaN).

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises ValueError: for NaN or a non-positive value.
    """
    if math.isnan(value) or value <= 0.0:
        raise ValueError(f"'{name}' must be positive.")
    return float(value)


def require_non_negative(value: float, name: str) -> float:
    """Require a non-negative finite number (rejects NaN).

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises ValueError: for NaN or a negative value.
    """
    if math.isnan(value) or value < 0.0:
        raise ValueError(f"'{name}' must be non-negative.")
    return float(value)


def require_fraction(value: float, name: str) -> float:
    """Require a fraction in ``[0, 1)`` (rejects NaN).

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :return: The validated value as a ``float``.
    :raises ValueError: for NaN or a value outside ``[0, 1)``.
    """
    if math.isnan(value) or value < 0.0 or value >= 1.0:
        raise ValueError(f"'{name}' must be in the range [0, 1).")
    return float(value)


def require_choice(value: str, name: str, options: tuple[str, ...]) -> str:
    """Require *value* to be one of *options*.

    :param value: The value to validate.
    :param name: Parameter name used in the error message.
    :param options: The accepted values.
    :return: The validated value.
    :raises ValueError: for a value not in *options*.
    """
    if value not in options:
        raise ValueError(f"'{name}' must be one of {options}; got {value!r}.")
    return value


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
