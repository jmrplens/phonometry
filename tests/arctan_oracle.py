#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""An arctangent oracle that owes nothing to the routine it checks.

A double ``r`` is the correctly rounded arctangent of ``x > 0`` exactly when
:math:`\arctan x` lies strictly between the midpoints ``r`` shares with its
two neighbours, and since the tangent increases on :math:`(-\pi/2, \pi/2)`
that is a question about the tangent of two rational numbers: is
:math:`\tan(\mathrm{low}) < x < \tan(\mathrm{high})`? Each tangent is
enclosed by the Taylor partial sums of its sine and cosine and the Lagrange
bound on what they leave out, in exact :class:`fractions.Fraction`
arithmetic, and the enclosure is widened until it decides. No arctangent is
evaluated anywhere, so neither the routine under test nor the C library has a
say in the verdict; the arctangent of a non-zero rational is never a
midpoint, so the widening always ends.
"""

from __future__ import annotations

import math
from fractions import Fraction

__all__ = ["correctly_rounded_arctangent", "is_correctly_rounded_arctangent"]

#: Terms of each series in the first enclosure; doubled until it decides.
_FIRST_TERMS = 8


def _sin_cos_enclosure(m: Fraction, terms: int) -> tuple[Fraction, Fraction, Fraction]:
    """Partial sums of ``sin m`` and ``cos m``, and a bound on what either leaves out.

    The sums run to degree ``2 * terms - 1``. By Lagrange's remainder each
    misses its function by at most :math:`m^{2n} / (2n)!` with ``n = terms``,
    every derivative of the sine and the cosine being at most one, for
    ``0 < m <= 2 * terms``.
    """
    sine = Fraction(0)
    cosine = Fraction(0)
    power = Fraction(1)
    for j in range(2 * terms):
        sign = 1 if j % 4 in (0, 1) else -1
        if j % 2:
            sine += sign * power
        else:
            cosine += sign * power
        power = power * m / (j + 1)
    return sine, cosine, power


def _cosine_is_positive(m: Fraction) -> bool:
    r"""Whether ``cos m > 0``, for ``0 < m < 2``: whether ``m`` is short of :math:`\pi/2`."""
    terms = _FIRST_TERMS
    while True:
        _, cosine, slack = _sin_cos_enclosure(m, terms)
        if cosine - slack > 0:
            return True
        if cosine + slack < 0:
            return False
        terms *= 2


def _arctangent_below(x: Fraction, m: Fraction) -> bool:
    r"""Whether :math:`\arctan x < m`, for ``x > 0`` and ``0 < m < 2``."""
    if not _cosine_is_positive(m):
        # m is at or past pi/2, which no arctangent reaches.
        return True
    terms = _FIRST_TERMS
    while True:
        sine, cosine, slack = _sin_cos_enclosure(m, terms)
        if cosine - slack > 0:
            if x * (cosine + slack) < sine - slack:
                return True
            if x * (cosine - slack) > sine + slack:
                return False
        terms *= 2


def _midpoints(r: float) -> tuple[Fraction, Fraction]:
    """The midpoints between a positive double and its two neighbours, exactly."""
    low = (Fraction(r) + Fraction(math.nextafter(r, 0.0))) / 2
    high = (Fraction(r) + Fraction(math.nextafter(r, math.inf))) / 2
    return low, high


def is_correctly_rounded_arctangent(x: float, r: float) -> bool:
    r"""Whether ``r`` is the double nearest :math:`\arctan x`, decided exactly.

    A signed zero must come back with its sign, a NaN as a NaN, and an
    infinity as the double nearest :math:`\pm\pi/2`, the one whose
    midpoints bracket :math:`\pi/2`, where the cosine changes sign.
    """
    if math.isnan(x):
        return math.isnan(r)
    same_sign = (math.copysign(1.0, x) > 0) is (math.copysign(1.0, r) > 0)
    if not x:
        return same_sign and not r
    if not same_sign or not r or not math.isfinite(r):
        return False
    x, r = math.fabs(x), math.fabs(r)
    low, high = _midpoints(r)
    if math.isinf(x):
        return _cosine_is_positive(low) and not _cosine_is_positive(high)
    exact = Fraction(x)
    return not _arctangent_below(exact, low) and _arctangent_below(exact, high)


def correctly_rounded_arctangent(x: float) -> float:
    r"""The double nearest :math:`\arctan x`, found from the C library's answer.

    The C library's arctangent is within an ulp or two everywhere, so it is a
    start; each step asks the rational oracle which side of the start the
    exact value lies and moves one double that way, until the oracle accepts.
    """
    candidate = math.atan(x)
    if is_correctly_rounded_arctangent(x, candidate):
        return candidate
    magnitude, sign = math.fabs(x), math.copysign(1.0, x)
    r = math.fabs(candidate)
    exact = Fraction(magnitude)
    while not is_correctly_rounded_arctangent(magnitude, r):
        low, _ = _midpoints(r)
        if _arctangent_below(exact, low):
            r = math.nextafter(r, 0.0)
        else:
            r = math.nextafter(r, math.inf)
    return math.copysign(r, sign)
