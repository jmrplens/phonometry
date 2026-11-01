#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""``sin``, ``tan``, ``atan`` and ``hypot``, correctly rounded, in exact integer arithmetic.

:mod:`phonometry.filters._weighting_design` takes a sine twice per design (the
read-back that sets the shipped gain), a tangent three times (the band edges
and the anchor, through the bilinear warp), an arctangent at each of the 257
points of its frequency grid (the warped grid mapped back to the frequencies
the target curve is read at) and, for the curves whose prototype has complex
poles or zeros, the magnitude of each of them, which Python takes through the
C library's ``hypot``. Taken from the C library, each is whatever the platform
ships, and the platforms round a fraction of inputs differently.

Here each is the *correctly rounded* value: the double nearest the exact
mathematical result. That answer has one definition and no platform in it, and
it is computed with nothing but Python integers, whose arithmetic is exact, and
one final correctly rounded integer division. The method is Ziv's: the
function is evaluated in fixed point at ``P`` bits with a rigorous bound on the
error, and if both ends of the interval that bound draws round to the same
double, that double is the answer; if they do not, ``P`` doubles and the
evaluation runs again. No input can loop forever, because the sine, tangent or
arctangent of a non-zero double is never exactly half way between two doubles.

Why correctly rounded rather than a transcription of the C library's own
routines: glibc's ``sin``, ``tan`` and ``atan`` are the IBM Accurate
Mathematical Library, and they and its ``hypot`` are LGPL-2.1-or-later, which
this MIT package does not take in. For the sine, the tangent and the magnitude
the correctly rounded value is also glibc's wherever the weighting design
reaches: over the 133 designs of the corpus (70 distinct sines, 105 tangents
and 67 magnitudes) glibc is correctly rounded on every one, so the shipped
Linux coefficients did not move. For the arctangent it is not: glibc rounds 19
of the 15 866 distinct arctangents those designs evaluate to the other
neighbour, those 19 reach 32 of the designs, and pinning the arctangent here
moved six of those designs on Linux by their last bits. Away from the corpus
the agreement is the C library's accuracy, not a guarantee:
``tests/filters/test_pinned_trig.py`` holds the agreement on the inputs a
design evaluates, measures it on draws across the domain, and checks the
arctangent against exact rational bounds that evaluate no arctangent.

The domain is what the design needs and a margin: ``|x| < 1024`` for the sine
and the tangent (the design never passes more than :math:`\pi`) and finite
arguments for ``hypot``; anything outside it is refused rather than answered
by a branch nobody has checked. The arctangent takes the whole line of
doubles, signed zeros, subnormals, infinities and NaN included, and is proved
on all of it.
"""

from __future__ import annotations

import math

import numpy as np

from .._internal.validation import real_array

__all__ = ["pinned_atan", "pinned_hypot", "pinned_sin", "pinned_tan"]

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

#: Guard bits the arctangent carries beyond the working precision, so that its
#: truncations, a few hundred at most, add up to a fraction of one unit.
_ARCTAN_GUARD = 32

#: Half-angle steps the arctangent takes before its series: each halves the
#: angle, so an argument at most one reaches the series under
#: :math:`\tan(\pi/16) < 0.2`, where each term gains more than four bits.
_HALF_ANGLE_STEPS = 2

#: The double nearest :math:`\pi/2`, the arctangent of an infinite argument:
#: the fixed-point :math:`\pi` halved and rounded once by an exact integer
#: division, which is ``math.pi / 2``.
_HALF_PI_DOUBLE = _PI / (1 << (_PI_BITS + 1))


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


def _atan_fixed(magnitude: float, scale: int) -> tuple[int, int]:
    r"""``atan(magnitude) * 2**scale`` for a finite ``magnitude > 0``, and an error bound.

    An argument above one is inverted, :math:`\arctan x = \pi/2 - \arctan(1/x)`;
    :data:`_HALF_ANGLE_STEPS` half-angle steps,
    :math:`\arctan t = 2 \arctan\bigl(t / (1 + \sqrt{1 + t^2})\bigr)`, bring the
    argument under :math:`\tan(\pi/16) < 0.2`; and the alternating series
    :math:`t - t^3/3 + t^5/5 - \dots` runs until a term vanishes. The work is
    done at :data:`_ARCTAN_GUARD` bits beyond ``scale``, where each integer
    step truncates by less than one unit: the reciprocal by one, each
    half-angle step by one (and halves what it inherits), each of the ``k``
    terms by under one and a half, the series it stops by one and a quarter,
    and the fixed-point :math:`\pi/2` by two. Four times that, the factor the
    half angles take back, stays under ``8 * (k + 4)`` units, and the final
    shift to ``scale`` adds one more.

    :param magnitude: A finite double above zero.
    :param scale: The binary point of the result.
    :return: ``(value, error)``, the error in units of ``2**-scale``.
    """
    wide = scale + _ARCTAN_GUARD
    one = 1 << wide
    t = _fixed_argument(magnitude, wide)
    invert = t > one
    if invert:
        t = (one << wide) // t
    for _ in range(_HALF_ANGLE_STEPS):
        t = (t << wide) // (one + math.isqrt(one * one + t * t))
    square = (t * t) >> wide
    power = total = t
    k = 0
    while power:
        power = (power * square) >> wide
        k += 1
        term = power // (2 * k + 1)
        total += -term if k % 2 else term
    value = total << _HALF_ANGLE_STEPS
    if invert:
        value = (_PI >> (_PI_BITS - wide + 1)) - value
    return value >> _ARCTAN_GUARD, ((8 * (k + 4)) >> _ARCTAN_GUARD) + 2


def _atan_scalar(x: float) -> float:
    r"""``atan(x)`` correctly rounded, by Ziv's loop, over the whole line of doubles.

    A signed zero and a NaN come back as they were handed, an infinity as the
    double nearest :math:`\pm\pi/2`; every other double is evaluated by
    :func:`_atan_fixed` at a scale that keeps ``precision`` significant bits
    however small the argument, subnormals included. The arctangent of a
    non-zero double is never half way between two doubles, so the loop ends.
    """
    if not isinstance(x, float):
        message = f"pinned arctangent takes a Python float; got {type(x).__name__}."
        raise TypeError(message)
    if math.isnan(x) or not x:
        return x
    if math.isinf(x):
        return math.copysign(_HALF_PI_DOUBLE, x)
    magnitude = math.fabs(x)
    precision = _FIRST_PRECISION
    while precision <= _LAST_PRECISION:
        scale = precision + max(0, -math.frexp(magnitude)[1])
        value, error = _atan_fixed(magnitude, scale)
        rounded = _round_fixed(value, error, scale)
        if rounded is not None:
            return math.copysign(rounded, x)
        precision *= 2
    message = f"pinned atan could not round {x!r} within {_LAST_PRECISION} bits."
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
    array = real_array(values, "values")
    flat = array.reshape(-1).tolist()
    out = np.fromiter((function(v) for v in flat), np.float64, len(flat))  # type: ignore[operator]
    return out.reshape(array.shape)


def pinned_sin(values: np.ndarray | float) -> np.ndarray:
    """``sin`` elementwise, correctly rounded, the same bits on every machine.

    :param values: Real values with ``|x| < 1024``.
    :return: The sine, elementwise, in the same shape.
    :raises ValueError: If a value is not finite or ``|x| >= 1024``.
    :raises TypeError: if ``values`` holds a text or a value that is not a real number.
    """
    return _elementwise(_sin_scalar, values)


def pinned_tan(values: np.ndarray | float) -> np.ndarray:
    """``tan`` elementwise, correctly rounded, the same bits on every machine.

    :param values: Real values with ``|x| < 1024``.
    :return: The tangent, elementwise, in the same shape.
    :raises ValueError: If a value is not finite or ``|x| >= 1024``.
    :raises TypeError: if ``values`` holds a text or a value that is not a real number.
    """
    return _elementwise(_tan_scalar, values)


def pinned_atan(values: np.ndarray | float) -> np.ndarray:
    """``atan`` elementwise, correctly rounded, the same bits on every machine.

    :param values: Real values; signed zeros, infinities and NaN included.
    :return: The arctangent, elementwise, in the same shape.
    :raises TypeError: if ``values`` holds a text or a value that is not a real number.
    """
    return _elementwise(_atan_scalar, values)


def pinned_hypot(x: float, y: float) -> float:
    r"""``hypot(x, y)``, correctly rounded, the same bits on every machine.

    Each argument is a Python float, as the real and imaginary parts of a
    Python complex are: anything else is refused by name rather than handed
    to :func:`float`, which would read a text as the number it spells and a
    flag as one.

    :param x: A finite Python float.
    :param y: A finite Python float.
    :return: :math:`\sqrt{x^2 + y^2}` rounded once.
    :raises TypeError: If ``x`` or ``y`` is not a Python float.
    :raises ValueError: If either argument is not finite.
    """
    for name, value in (("x", x), ("y", y)):
        if not isinstance(value, float):
            message = f"'{name}' must be a Python float; got {type(value).__name__}."
            raise TypeError(message)
    return _hypot_scalar(x, y)
