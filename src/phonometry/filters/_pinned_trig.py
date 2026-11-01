#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""``sin``, ``tan`` and ``hypot``, correctly rounded, in exact integer arithmetic.

:mod:`phonometry.filters._weighting_design` takes a sine twice per design (the
read-back that sets the shipped gain), a tangent three times (the band edges
and the anchor, through the bilinear warp) and, for the curves whose prototype
has complex poles or zeros, the magnitude of each of them, which Python takes
through the C library's ``hypot``. Taken from the C library, each is whatever
the platform ships, and the platforms round a fraction of inputs differently.

Here each is the *correctly rounded* value: the double nearest the exact
mathematical result. That answer has one definition and no platform in it, and
it is computed with nothing but Python integers, whose arithmetic is exact, and
one final correctly rounded integer division. The method is Ziv's: the
function is evaluated in fixed point at ``P`` bits with a rigorous bound on the
error, and if both ends of the interval that bound draws round to the same
double, that double is the answer; if they do not, ``P`` doubles and the
evaluation runs again. No input can loop forever, because a sine or tangent of
a non-zero double is never exactly half way between two doubles.

Why correctly rounded rather than a transcription of the C library's own
routine: glibc's ``sin`` and ``tan`` (the IBM Accurate Mathematical Library) and
its ``hypot`` are correctly rounded on every input the weighting design feeds
them, measured over the 133 designs of the corpus (70 distinct sines, 105
tangents and 67 magnitudes, every one the correctly rounded value), so the
correctly rounded routine returns the C library's own bits wherever the design
reaches it, and the shipped Linux coefficients do not move. Away from the
corpus the agreement is the C library's accuracy, not a guarantee:
``tests/filters/test_pinned_trig.py`` holds the agreement on the inputs a design
evaluates and measures it on draws across the domain.

The domain is what the design needs and a margin: ``|x| < 1024`` for the
trigonometric functions (the design never passes more than :math:`\pi`) and
finite arguments for ``hypot``. Anything outside it is refused rather than
answered by a branch nobody has checked.
"""

from __future__ import annotations

import math

import numpy as np

__all__ = ["pinned_hypot", "pinned_sin", "pinned_tan"]

#: Bits of :math:`\pi` kept in fixed point. The reduction uses it to the
#: working precision plus the bits a multiple of :math:`\pi/2` below ``1024``
#: can cancel, and the Ziv loop stops well short of it.
_PI_BITS = 1600

#: Guard bits the argument reduction carries beyond the working precision.
_REDUCTION_GUARD = 96

#: Working precision of the first Ziv pass, and the most any pass may use.
_FIRST_PRECISION = 96
_LAST_PRECISION = 1200

#: Largest argument the trigonometric functions accept.
_TRIG_LIMIT = 1024.0


def _arctan_reciprocal(n: int, scale: int) -> int:
    """``atan(1/n) * 2**scale``, truncated, with an error under one unit per term."""
    one = 1 << scale
    term = one // n
    total = term
    n2 = n * n
    k = 1
    sign = -1
    while term:
        term //= n2
        k += 2
        total += sign * (term // k)
        sign = -sign
    return total


def _pi_fixed(bits: int) -> int:
    r""":math:`\pi \cdot 2^{bits}` by Machin's formula, within one unit."""
    guard = 32
    scale = bits + guard
    value = 4 * (4 * _arctan_reciprocal(5, scale) - _arctan_reciprocal(239, scale))
    return value >> guard


_PI = _pi_fixed(_PI_BITS)


def _round_fixed(value: int, error: int, scale: int) -> float | None:
    """The double ``value / 2**scale`` rounds to, if the error bound cannot move it.

    Integer true division in Python is correctly rounded, so both ends of the
    interval are rounded exactly; equal ends mean every point inside rounds
    to the same double.

    :param value: The fixed-point approximation.
    :param error: A bound on its distance from the exact result, in units.
    :param scale: The binary point.
    :return: The correctly rounded double, or ``None`` if the bound straddles
        a rounding boundary.
    """
    denominator = 1 << scale
    low = (value - error) / denominator
    high = (value + error) / denominator
    return low if low == high else None


def _fixed_argument(x: float, scale: int) -> int:
    """``x * 2**scale`` as an integer, exact whenever the scale reaches x's last bit."""
    numerator, denominator = x.as_integer_ratio()
    shift = scale - (denominator.bit_length() - 1)
    if shift >= 0:
        return numerator << shift
    return numerator >> -shift


def _reduce(x: float, scale: int) -> tuple[int, int]:
    """``x - k pi/2`` in fixed point at ``scale`` bits, and ``k``.

    :return: ``(r, k)``; ``r`` is within two units of the exact remainder.
    """
    wide = scale + _REDUCTION_GUARD
    argument = _fixed_argument(x, wide)
    half_pi = _PI >> (_PI_BITS - wide + 1)
    quadrant = (2 * argument + half_pi) // (2 * half_pi)
    remainder = argument - quadrant * half_pi
    return remainder >> _REDUCTION_GUARD, quadrant


def _sin_cos(r: int, scale: int) -> tuple[int, int, int]:
    """Fixed-point ``sin r`` and ``cos r`` for ``|r| <= pi/4``, and their error bound.

    Taylor series, each term derived from the last by one multiplication, one
    shift and one division, each of which truncates by less than one unit; the
    series stops when a term vanishes, and what it leaves out is smaller than
    the first term it did not add.

    :return: ``(sin, cos, error)`` with the error in units of ``2**-scale``.
    """
    square = (r * r) >> scale
    sine = term = r
    k = 1
    while term:
        term = -((term * square) >> scale) // ((2 * k) * (2 * k + 1))
        sine += term
        k += 1
    terms = k
    cosine = term = 1 << scale
    k = 1
    while term:
        term = -((term * square) >> scale) // ((2 * k - 1) * (2 * k))
        cosine += term
        k += 1
    return sine, cosine, 4 * max(terms, k) + 8


def _check_trig_argument(x: float) -> None:
    """Refuse anything but a finite double inside the domain the routines are proved on."""
    if not isinstance(x, float):
        message = f"pinned trigonometry takes a Python float; got {type(x).__name__}."
        raise TypeError(message)
    if not (math.isfinite(x) and -_TRIG_LIMIT < x < _TRIG_LIMIT):
        message = f"pinned trigonometry takes |x| < {_TRIG_LIMIT:g}; got {x!r}."
        raise ValueError(message)


def _sin_scalar(x: float) -> float:
    """``sin(x)`` correctly rounded, by Ziv's loop."""
    _check_trig_argument(x)
    if not x:
        return x
    precision = _FIRST_PRECISION
    while precision <= _LAST_PRECISION:
        scale = precision + max(0, -math.frexp(x)[1])
        r, quadrant = _reduce(x, scale)
        sine, cosine, error = _sin_cos(r, scale)
        value = (sine, cosine, -sine, -cosine)[quadrant % 4]
        rounded = _round_fixed(value, error, scale)
        if rounded is not None:
            return rounded
        precision *= 2
    message = f"pinned sin could not round {x!r} within {_LAST_PRECISION} bits."
    raise ArithmeticError(message)


def _tan_scalar(x: float) -> float:
    """``tan(x)`` correctly rounded, by Ziv's loop over a fixed-point quotient."""
    _check_trig_argument(x)
    if not x:
        return x
    precision = _FIRST_PRECISION
    while precision <= _LAST_PRECISION:
        scale = precision + max(0, -math.frexp(x)[1])
        r, quadrant = _reduce(x, scale)
        sine, cosine, error = _sin_cos(r, scale)
        top, bottom = (sine, cosine) if quadrant % 2 == 0 else (-cosine, sine)
        if abs(bottom) > error:
            quotient = (top << scale) // bottom
            bound = ((error << scale) + abs(quotient) * error) // (
                abs(bottom) - error
            ) + 2
            rounded = _round_fixed(quotient, bound, scale)
            if rounded is not None:
                return rounded
        precision *= 2
    message = f"pinned tan could not round {x!r} within {_LAST_PRECISION} bits."
    raise ArithmeticError(message)


def _hypot_scalar(x: float, y: float) -> float:
    """``sqrt(x*x + y*y)`` correctly rounded: the sum is exact in integers.

    The exact square root is bracketed by an integer square root with at least
    64 significant bits, and the last bit of the bracket records whether the
    root was exact, so the one rounding that follows is the correct one.
    """
    if not (isinstance(x, float) and isinstance(y, float)):
        message = (
            "pinned hypot takes two Python floats; got "
            f"({type(x).__name__}, {type(y).__name__})."
        )
        raise TypeError(message)
    if not (math.isfinite(x) and math.isfinite(y)):
        message = f"pinned hypot takes finite arguments; got ({x!r}, {y!r})."
        raise ValueError(message)
    nx, dx = math.fabs(x).as_integer_ratio()
    ny, dy = math.fabs(y).as_integer_ratio()
    total = nx * nx * dy * dy + ny * ny * dx * dx
    if total == 0:
        return 0.0
    exponent = (dx * dy).bit_length() - 1
    shift = max(0, (130 - total.bit_length()) // 2 + 1)
    scaled = total << (2 * shift)
    root = math.isqrt(scaled)
    inexact = root * root != scaled
    return (2 * root + inexact) / (1 << (exponent + shift + 1))


def _elementwise(function: object, values: np.ndarray | float) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    flat = array.reshape(-1).tolist()
    out = np.fromiter((function(v) for v in flat), np.float64, len(flat))  # type: ignore[operator]
    return out.reshape(array.shape)


def pinned_sin(values: np.ndarray | float) -> np.ndarray:
    """``sin`` elementwise, correctly rounded, the same bits on every machine.

    :param values: Real values with ``|x| < 1024``.
    :return: The sine, elementwise, in the same shape.
    :raises ValueError: If a value is not finite or ``|x| >= 1024``.
    """
    return _elementwise(_sin_scalar, values)


def pinned_tan(values: np.ndarray | float) -> np.ndarray:
    """``tan`` elementwise, correctly rounded, the same bits on every machine.

    :param values: Real values with ``|x| < 1024``.
    :return: The tangent, elementwise, in the same shape.
    :raises ValueError: If a value is not finite or ``|x| >= 1024``.
    """
    return _elementwise(_tan_scalar, values)


def pinned_hypot(x: float, y: float) -> float:
    r"""``hypot(x, y)``, correctly rounded, the same bits on every machine.

    :param x: A finite real value.
    :param y: A finite real value.
    :return: :math:`\sqrt{x^2 + y^2}` rounded once.
    :raises ValueError: If either argument is not finite.
    """
    return _hypot_scalar(float(x), float(y))
