#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Trigonometric oracles that owe nothing to the routines they check.

A double ``r`` is the correctly rounded value of a function at ``x`` exactly
when the exact value lies strictly between the midpoints ``r`` shares with
its two neighbours. For the arctangent of ``x > 0`` that is a question about
the tangent of two rational numbers, since the tangent increases on
:math:`(-\pi/2, \pi/2)`: is :math:`\tan(\mathrm{low}) < x < \tan(\mathrm{high})`?
For the sine and the tangent of ``x`` it is a question about the exact value
itself, enclosed after an exact reduction by a rational enclosure of
:math:`\pi`. Each sine, cosine and tangent is enclosed by the Taylor partial
sums of the sine and cosine and the Lagrange bound on what they leave out, in
exact :class:`fractions.Fraction` arithmetic, and the enclosure is widened
until it decides. No trigonometric function is evaluated anywhere, so
neither the routine under test nor the C library has a say in the verdict;
the sine, tangent and arctangent of a non-zero rational are never a
midpoint, so the widening always ends.
"""

from __future__ import annotations

import math
from fractions import Fraction

__all__ = [
    "correctly_rounded_arctangent",
    "is_correctly_rounded_arctangent",
    "is_correctly_rounded_sine",
    "is_correctly_rounded_tangent",
]

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
    midpoints bracket :math:`\pi/2`, where the cosine changes sign. An
    answer of magnitude 2 or more is refused before anything is enclosed:
    no arctangent reaches it, the sign of the cosine places a midpoint short
    of :math:`\pi/2` only below 2 (it is positive again one period up), and
    the enclosures of :func:`_cosine_is_positive` never decide far out.
    """
    if math.isnan(x):
        return math.isnan(r)
    same_sign = (math.copysign(1.0, x) > 0) is (math.copysign(1.0, r) > 0)
    if not x:
        return same_sign and not r
    if not same_sign or not r or not math.isfinite(r):
        return False
    x, r = math.fabs(x), math.fabs(r)
    if r >= 2.0:
        # No arctangent reaches 2, and the enclosures below hold only short of
        # it: one period up the cosine is positive again, and far out they
        # never decide.
        return False
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


#: Bits of the first enclosure of :math:`\pi`; doubled with the terms.
_FIRST_PI_BITS = 128


def _arctangent_of_reciprocal(n: int, bits: int) -> tuple[Fraction, Fraction]:
    """An enclosure of ``atan(1/n)``, ``n >= 2``, at least *bits* bits wide.

    The series alternates with terms that shrink, so each partial sum lies on
    the other side of the limit from the one before, within the next term.
    """
    total = Fraction(0)
    k = 0
    while True:
        term = Fraction(1, (2 * k + 1) * n ** (2 * k + 1))
        if term < Fraction(1, 1 << bits):
            return (total - term, total) if k % 2 else (total, total + term)
        total += term if k % 2 == 0 else -term
        k += 1


def _pi_enclosure(bits: int) -> tuple[Fraction, Fraction]:
    r"""``(low, high)`` around :math:`\pi` by Machin's formula, 16 atan(1/5) - 4 atan(1/239)."""
    fifth_low, fifth_high = _arctangent_of_reciprocal(5, bits)
    far_low, far_high = _arctangent_of_reciprocal(239, bits)
    return 16 * fifth_low - 4 * far_high, 16 * fifth_high - 4 * far_low


def _point_sin_cos(
    y: Fraction, terms: int
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    """``(sin low, sin high, cos low, cos high)`` at the rational *y*, ``|y| < 2``."""
    if not y:
        return Fraction(0), Fraction(0), Fraction(1), Fraction(1)
    sine, cosine, slack = _sin_cos_enclosure(abs(y), terms)
    if y < 0:
        sine = -sine
    return sine - slack, sine + slack, cosine - slack, cosine + slack


def _reduced(x: float, bits: int) -> tuple[int, Fraction, Fraction, Fraction]:
    r"""``(k, low, high, half pi)``: ``x - k pi`` lies in ``[low, high]``, within :math:`\pi/2`."""
    pi_low, pi_high = _pi_enclosure(bits)
    exact = Fraction(x)
    k = round(exact / pi_low)
    ends = (exact - k * pi_low, exact - k * pi_high)
    return k, min(ends), max(ends), pi_low / 2


def _verdict(r: float, low: Fraction, high: Fraction) -> bool | None:
    """Whether ``r`` is the double nearest a value enclosed in ``[low, high]``, or ``None``."""
    below = (Fraction(r) + Fraction(math.nextafter(r, -math.inf))) / 2
    above = (Fraction(r) + Fraction(math.nextafter(r, math.inf))) / 2
    if below < low and high < above:
        return True
    if high <= below or low >= above:
        return False
    return None


def _decide(x: float, r: float, enclose: object) -> bool:
    """Widen *enclose* until it decides whether ``r`` is correctly rounded at ``x``."""
    if math.isnan(x) or math.isinf(x):
        return math.isnan(r)
    if not x:
        same_sign = (math.copysign(1.0, x) > 0) is (math.copysign(1.0, r) > 0)
        return same_sign and not r
    if not math.isfinite(r):
        return False
    bits, terms = _FIRST_PI_BITS, 2 * _FIRST_TERMS
    while True:
        bounds = enclose(x, bits, terms)  # type: ignore[operator]
        verdict = None if bounds is None else _verdict(r, *bounds)
        if verdict is not None:
            return verdict
        bits, terms = 2 * bits, 2 * terms


def _sine_bounds(x: float, bits: int, terms: int) -> tuple[Fraction, Fraction] | None:
    """An enclosure of ``sin x``, or ``None`` where the reduction straddles a crest."""
    k, low, high, half_pi = _reduced(x, bits)
    if low <= -half_pi or high >= half_pi:
        return None
    # The sine increases on (-pi/2, pi/2): its least value is at the low end.
    least, _, _, _ = _point_sin_cos(low, terms)
    _, most, _, _ = _point_sin_cos(high, terms)
    return (-most, -least) if k % 2 else (least, most)


def _tangent_bound(y: Fraction, terms: int, *, upper: bool) -> Fraction | None:
    """The upper or lower bound of ``tan y`` at a rational inside (-pi/2, pi/2)."""
    sine_low, sine_high, cosine_low, cosine_high = _point_sin_cos(y, terms)
    if cosine_low <= 0:
        return None
    if upper:
        return sine_high / (cosine_low if sine_high >= 0 else cosine_high)
    return sine_low / (cosine_high if sine_low >= 0 else cosine_low)


def _tangent_bounds(
    x: float, bits: int, terms: int
) -> tuple[Fraction, Fraction] | None:
    """An enclosure of ``tan x``, or ``None`` where it cannot yet be told from a pole."""
    _, low, high, half_pi = _reduced(x, bits)
    if low <= -half_pi or high >= half_pi:
        return None
    # The tangent increases on (-pi/2, pi/2) and has period pi.
    least = _tangent_bound(low, terms, upper=False)
    most = _tangent_bound(high, terms, upper=True)
    if least is None or most is None:
        return None
    return least, most


def is_correctly_rounded_sine(x: float, r: float) -> bool:
    """Whether ``r`` is the double nearest ``sin x``, decided exactly.

    A signed zero must come back with its sign, and a NaN or an infinity
    as a NaN.
    """
    return _decide(x, r, _sine_bounds)


def is_correctly_rounded_tangent(x: float, r: float) -> bool:
    """Whether ``r`` is the double nearest ``tan x``, decided exactly.

    A signed zero must come back with its sign, and a NaN or an infinity
    as a NaN.
    """
    return _decide(x, r, _tangent_bounds)
