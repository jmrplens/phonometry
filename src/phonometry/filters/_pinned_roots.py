#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Roots of a polynomial with exact coefficients, each part correctly rounded.

The ITU-R BS.468-4 prototype's six poles are the roots of the denominator of
its network, and :func:`numpy.roots` finds roots as the eigenvalues of the
companion matrix, through LAPACK's Hessenberg QR iteration. That iteration is
a library's arithmetic: its rotations and its deflation test are sums of
products the BLAS and the compiler are free to order and to fuse, and the
OpenBLAS numpy ships for 64-bit ARM returns other last bits for these six
poles than the x86-64 build does, which reached every 468 design. The
polynomial products that build the denominator from the network went through
the BLAS as well.

Here the denominator is built with exact rational arithmetic
(:func:`exact_polynomial_product`, :func:`exact_polynomial_sum`), so it is the
network's own polynomial over the component values, with no rounding at all,
and :func:`correctly_rounded_roots` returns each root with its real and its
imaginary part the double nearest the exact root's. That answer has one
definition and no platform in it, and it is found with nothing but Python
integers and fractions, whose arithmetic is exact, one correctly rounded
integer division per part and the two doubles beside its result, which
:func:`math.nextafter` returns exactly as IEEE 754 defines them.

The method is a simultaneous iteration followed by a certificate. Aberth's
iteration (Aberth, Math. Comp. 27, 1973; Ehrlich, Comm. ACM 10, 1967) moves
all the approximations together from points on a circle: each takes Newton's
step damped by the pull of all the others, which keeps two of them from
settling on one root, and is rounded onto a binary grid that follows its own
magnitude, so that the fractions stay short and roots of very different
sizes are held to the same relative precision. Each pass after the first
doubles the grid's bits, which is Ziv's loop again, and ends with a
certificate that needs no assumption about the iteration: for any point
:math:`x` of a polynomial of degree :math:`n`, the disk of radius
:math:`n\,|p(x)/p'(x)|` about :math:`x` holds a root, since
:math:`|p'(x)/p(x)| = |\sum_k 1/(x - r_k)| \le n / \min_k |x - r_k|`.
When the :math:`n` disks are pairwise disjoint, each holds exactly one root
and every root is simple. A disk about a point's real part, widened by its
imaginary part, holds the same root; if it meets no other disk it holds that
root alone, and since it is symmetric about the axis it holds the root's
conjugate too, so the root is real. Every other disk has to lie wholly above
or below the axis. When both ends of each disk's extent in each coordinate
lie strictly between the midpoints around one double, decided in exact
rational arithmetic, that double is the coordinate's correctly rounded
value, and the pass returns; otherwise the next pass refines the grid. A
multiple root is never separated, and the finest grid refuses it.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "correctly_rounded_roots",
    "exact_polynomial_product",
    "exact_polynomial_sum",
]

#: A polynomial as its exact coefficients, the highest power first.
Polynomial = tuple[Fraction, ...]

#: A complex number as its exact real and imaginary parts.
_Complex = tuple[Fraction, Fraction]

#: Bits below each approximation's leading bit the first sweeps keep; each
#: pass after them doubles it.
_FIRST_BITS = 64
_LAST_BITS = 4096

#: Steps of the simultaneous iteration at most. It converges in a few dozen
#: on the polynomials it is given; the cap only bounds a search that would
#: not, and the certificate refuses what it leaves unresolved.
_ABERTH_STEPS = 400

#: Sweeps of the iteration per pass. Each pass doubles the grid's bits and
#: each sweep near a simple root at least doubles the correct ones, so two
#: sweeps keep the approximations at the grid's resolution.
_PASS_SWEEPS = 2

#: Guard bits of the upper bound on a disk's radius beyond the radius itself.
_RADIUS_GUARD = 64


def _power_of_two(exponent: int) -> Fraction:
    """``2 ** exponent`` as an exact fraction, for either sign of *exponent*."""
    if exponent >= 0:
        return Fraction(1 << exponent)
    return Fraction(1, 1 << -exponent)


def exact_polynomial_product(left: Polynomial, right: Polynomial) -> Polynomial:
    """The product of two polynomials, exactly.

    :param left: Coefficients, the highest power first.
    :param right: Coefficients, the highest power first.
    :return: The product's coefficients, the highest power first.
    """
    product = [Fraction(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            product[i + j] += a * b
    return tuple(product)


def exact_polynomial_sum(left: Polynomial, right: Polynomial) -> Polynomial:
    """The sum of two polynomials, exactly, aligned at their constant terms.

    :param left: Coefficients, the highest power first.
    :param right: Coefficients, the highest power first.
    :return: The sum's coefficients, the highest power first.
    """
    width = max(len(left), len(right))
    padded_left = (Fraction(0),) * (width - len(left)) + tuple(left)
    padded_right = (Fraction(0),) * (width - len(right)) + tuple(right)
    return tuple(a + b for a, b in zip(padded_left, padded_right, strict=True))


def _product(a: _Complex, b: _Complex) -> _Complex:
    """``a * b`` of two exact complex numbers."""
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def _quotient(a: _Complex, b: _Complex) -> _Complex:
    """``a / b`` of two exact complex numbers, *b* not zero."""
    norm = b[0] * b[0] + b[1] * b[1]
    return (
        (a[0] * b[0] + a[1] * b[1]) / norm,
        (a[1] * b[0] - a[0] * b[1]) / norm,
    )


def _value_and_slope(
    coefficients: Polynomial, x: _Complex
) -> tuple[_Complex, _Complex]:
    """``p(x)`` and ``p'(x)`` by Horner's rule, exactly."""
    value: _Complex = (Fraction(0), Fraction(0))
    slope: _Complex = (Fraction(0), Fraction(0))
    for coefficient in coefficients:
        slope = _product(slope, x)
        slope = (slope[0] + value[0], slope[1] + value[1])
        value = _product(value, x)
        value = (value[0] + coefficient, value[1])
    return value, slope


def _exponent(value: Fraction) -> int:
    """``floor(log2 |value|)`` or one less, read off bit lengths; *value* not zero."""
    return value.numerator.bit_length() - value.denominator.bit_length()


def _on_grid(x: _Complex, bits: int) -> _Complex:
    """*x* rounded part by part to *bits* bits below its larger part's leading bit.

    The grid follows the point's own magnitude, so roots of very different
    sizes are all held to the same relative precision. A point at the origin
    stays there.
    """
    larger = max(abs(x[0]), abs(x[1]))
    if not larger:
        return x
    scale = _power_of_two(bits - _exponent(larger))
    return Fraction(round(x[0] * scale)) / scale, Fraction(round(x[1] * scale)) / scale


def _magnitude2(x: _Complex) -> Fraction:
    """``|x|**2``, exactly."""
    return x[0] * x[0] + x[1] * x[1]


def _starts(coefficients: Polynomial) -> list[_Complex]:
    r"""Distinct starting points on a circle, none mirrored in the real axis.

    The radius is a power of two near the geometric mean of the roots'
    magnitudes, :math:`|a_n / a_0|^{1/n}`, read off bit lengths. The points
    are :math:`((1 - t^2), 2t) / (1 + t^2)` on the unit circle for rational
    :math:`t` spread over both signs and shifted off the symmetric values, so
    that no two are conjugate and none is real, which a polynomial with real
    coefficients would otherwise keep conjugate or real for good.
    """
    degree = len(coefficients) - 1
    constant = abs(coefficients[-1]) or Fraction(1)
    radius = _power_of_two(_exponent(constant / abs(coefficients[0])) // degree)
    points = []
    for k in range(degree):
        t = Fraction(2 * k + 1 - degree, degree) * Fraction(3, 2) + Fraction(1, 7)
        denominator = 1 + t * t
        points.append(
            (radius * (1 - t * t) / denominator, radius * 2 * t / denominator)
        )
    return points


def _aberth_sweep(coefficients: Polynomial, points: list[_Complex], bits: int) -> bool:
    """One sweep of Aberth's iteration in place; whether every correction was small.

    Each point moves by Newton's correction damped by the pull of all the
    others, which keeps two approximations from settling on one root, and is
    rounded onto its grid. A correction is small when it is under sixteen
    units of that grid.
    """
    settled = True
    one: _Complex = (Fraction(1), Fraction(0))
    for i, x in enumerate(points):
        value, slope = _value_and_slope(coefficients, x)
        if not (slope[0] or slope[1]):
            settled = False
            continue
        newton = _quotient(value, slope)
        repulsion: _Complex = (Fraction(0), Fraction(0))
        for j, other in enumerate(points):
            if j != i:
                term = _quotient(one, (x[0] - other[0], x[1] - other[1]))
                repulsion = (repulsion[0] + term[0], repulsion[1] + term[1])
        damping = _product(newton, repulsion)
        correction = _quotient(newton, (1 - damping[0], -damping[1]))
        points[i] = _on_grid((x[0] - correction[0], x[1] - correction[1]), bits)
        unit = _power_of_two(2 * (4 - bits)) * _magnitude2(points[i])
        settled = settled and _magnitude2(correction) <= unit
    return settled


def _aberth(coefficients: Polynomial) -> list[_Complex]:
    """All the roots, to the first grid's resolution, by Aberth's iteration."""
    points = [_on_grid(x, _FIRST_BITS) for x in _starts(coefficients)]
    for _ in range(_ABERTH_STEPS):
        if _aberth_sweep(coefficients, points, _FIRST_BITS):
            break
    return points


def _radius_above(coefficients: Polynomial, x: _Complex) -> Fraction:
    r"""An upper bound on :math:`n\,|p(x)/p'(x)|`, the radius of a disk that holds a root.

    The square is exact; its root is bounded above by an integer square root
    with :data:`_RADIUS_GUARD` bits beyond the radius.
    """
    value, slope = _value_and_slope(coefficients, x)
    degree = len(coefficients) - 1
    below = _magnitude2(slope)
    if not below:
        return Fraction(-1)
    square = degree * degree * _magnitude2(value) / below
    if not square:
        return square
    shift = 1 << _RADIUS_GUARD
    scaled = square.numerator * square.denominator * shift * shift
    return Fraction(math.isqrt(scaled) + 1, square.denominator * shift)


def _disjoint(centres: list[_Complex], radii: list[Fraction]) -> bool:
    """Whether every disk has a radius and no two disks meet."""
    if any(radius < 0 for radius in radii):
        return False
    for i, (a, ra) in enumerate(zip(centres, radii, strict=True)):
        for b, rb in zip(centres[i + 1 :], radii[i + 1 :], strict=True):
            reach = ra + rb
            if _magnitude2((a[0] - b[0], a[1] - b[1])) <= reach * reach:
                return False
    return True


def _rounded(low: Fraction, high: Fraction) -> float | None:
    """The double every point of ``[low, high]`` rounds to, or ``None``.

    Integer true division in Python is correctly rounded, so *low* rounds to
    ``nearest``. Every point of the interval rounds to it when the whole
    interval lies strictly between the midpoints ``nearest`` shares with its
    two neighbours, which is decided in exact rational arithmetic; an
    interval that reaches either midpoint asks for a finer grid. A single
    point, an exact root, rounds as the division rounds it.
    """
    nearest = low.numerator / low.denominator
    if low == high:
        return nearest
    exact = Fraction(nearest)
    below = (exact + Fraction(math.nextafter(nearest, -math.inf))) / 2
    above = (exact + Fraction(math.nextafter(nearest, math.inf))) / 2
    return nearest if below < low and high < above else None


def _alone_on_the_axis(
    index: int, points: list[_Complex], radii: list[Fraction]
) -> Fraction | None:
    """The radius of a disk on the real axis that holds the root of *index* alone, or ``None``.

    The disk about the point's real part, widened by its imaginary part,
    holds the root the point's own disk holds. If it meets no other disk it
    holds that root alone, and since it is symmetric about the axis it holds
    the root's conjugate too, so the root is real.
    """
    centre = (points[index][0], Fraction(0))
    widened = radii[index] + abs(points[index][1])
    for other, (x, radius) in enumerate(zip(points, radii, strict=True)):
        reach = widened + radius
        apart = _magnitude2((centre[0] - x[0], centre[1] - x[1]))
        if other != index and apart <= reach * reach:
            return None
    return widened


def _certified_root(
    coefficients: Polynomial, index: int, points: list[_Complex], radii: list[Fraction]
) -> list[complex] | None:
    """The rounded root of one disk: a real root, a conjugate pair, nothing, or ``None``.

    A real root comes back alone; the disk above the axis reports its root
    and that root's conjugate, so the disk below reports nothing. ``None``
    is a disk that does not yet decide: one that straddles the axis without
    being alone on it, or whose extent reaches a rounding boundary.
    """
    x, radius = points[index], radii[index]
    widened = _alone_on_the_axis(index, points, radii)
    if widened is not None:
        # The point's real part is the widened disk's centre, so a disk about
        # it no wider holds the same root; on the axis the iteration can land
        # on the root itself, which a root on a rounding boundary needs.
        on_axis = _radius_above(coefficients, (x[0], Fraction(0)))
        if 0 <= on_axis < widened:
            widened = on_axis
        part = _rounded(x[0] - widened, x[0] + widened)
        return None if part is None else [complex(part, 0.0)]
    if -x[1] > radius:
        return []
    if x[1] <= radius:
        return None
    re = _rounded(x[0] - radius, x[0] + radius)
    im = _rounded(x[1] - radius, x[1] + radius)
    if re is None or im is None:
        return None
    return [complex(re, im), complex(re, -im)]


def _certified(
    coefficients: Polynomial, points: list[_Complex]
) -> list[complex] | None:
    """Every root rounded, if the disks about *points* certify them all, else ``None``."""
    radii = [_radius_above(coefficients, x) for x in points]
    if not _disjoint(points, radii):
        return None
    roots: list[complex] = []
    for index in range(len(points)):
        found = _certified_root(coefficients, index, points, radii)
        if found is None:
            return None
        roots += found
    return roots


def _exact_coefficients(coefficients: Sequence[Fraction | int]) -> Polynomial:
    """*coefficients* as fractions, refused unless a polynomial of degree one or more."""
    if any(
        isinstance(c, bool) or not isinstance(c, (Fraction, int)) for c in coefficients
    ):
        msg = "'coefficients' must be exact: Fraction or int."
        raise TypeError(msg)
    exact = tuple(Fraction(c) for c in coefficients)
    if len(exact) <= 1 or not exact[0]:
        msg = "'coefficients' must be a polynomial of degree one or more."
        raise ValueError(msg)
    return exact


def correctly_rounded_roots(
    coefficients: Sequence[Fraction | int],
) -> tuple[complex, ...]:
    """Every root of a real polynomial, each part the double nearest the exact root's.

    :param coefficients: The polynomial's exact coefficients, the highest
        power first, the first not zero. Its roots must be simple.
    :return: The roots, sorted by real part and then by imaginary part; a
        complex pair is a pair of exact conjugates and a real root has an
        imaginary part of ``0.0``.
    :raises TypeError: if a coefficient is not a :class:`~fractions.Fraction`
        or an ``int``.
    :raises ValueError: if the polynomial is a constant.
    :raises ArithmeticError: if the roots are not resolved by the finest grid,
        as a multiple root never is.
    """
    exact = _exact_coefficients(coefficients)
    points = _aberth(exact)
    bits = _FIRST_BITS
    while bits < _LAST_BITS:
        bits *= 2
        for _ in range(_PASS_SWEEPS):
            _aberth_sweep(exact, points, bits)
        roots = _certified(exact, points)
        if roots is not None:
            return tuple(sorted(roots, key=lambda z: (z.real, z.imag)))
    msg = "the roots were not resolved; a multiple root never is."
    raise ArithmeticError(msg)
