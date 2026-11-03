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
integer division per part, the two doubles beside its result, which
:func:`math.nextafter` returns exactly as IEEE 754 defines them, and the
addition of ``+0.0`` that makes a zero positive.

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
value. An extent that reaches a midpoint asks whether the coordinate is that
midpoint exactly: on the line through it the polynomial is
:math:`A(t) + \mathrm{i}\,B(t)` for real :math:`t`, and the disk's one root,
which is simple, lies on the line where the greatest common divisor of
:math:`A` and :math:`B` changes sign across the line's chord through the
disk, which exact arithmetic decides too; such a coordinate rounds to even.
When neither decides, the next pass refines the grid.
Two approximations of two close real roots can settle on the vertical line
through the roots' midpoint, where every correction is purely imaginary and
the grid holds the real part exactly, so a pass that does not decide moves
each point off it by a small step of its own before the next. The step is
deterministic and the certificate, not the path, decides the answer, so it
changes no result.

A root at zero is read off the coefficients, which end in a zero, and is
divided out before the iteration, which would approach it ever more closely
without its relative grid ever deciding. Every part that rounds to zero is
``+0.0``, whichever side of zero the exact part lies; a part at or beyond
:math:`2^{1024} - 2^{970}`, which round to nearest takes to infinity, raises
:class:`OverflowError`. A multiple root is never separated: at zero it is
refused at once, and elsewhere the finest grid refuses it.
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

#: Sweeps of the iteration per pass at most. Each pass doubles the grid's
#: bits and each sweep near a simple root at least doubles the correct ones,
#: so two sweeps settle a pass where the roots are apart; a cluster of close
#: roots takes more, and a multiple root, which never settles, takes them
#: all before the finest grid refuses it.
_PASS_STEPS = 16

#: Guard bits of the bounds on a square root beyond the root itself.
_RADIUS_GUARD = 64

#: The rounding boundary past the largest double, half way between it and
#: :math:`2^{1024}`: round to nearest takes every value from here on to
#: infinity, and a tie here too, since the largest double's last bit is odd.
_OVERFLOW = Fraction(2**1024 - 2**970)

#: The offset that shifts the starting points off the symmetric values: the
#: reciprocal of a prime, so that no two starts are conjugate and none is
#: real for every degree below three times it (:func:`_starts`).
_START_OFFSET = Fraction(1, 1009)


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
    :math:`t_k = \tfrac{3}{2}(2k + 1 - n)/n + 1/q`, spread over both signs and
    shifted off the symmetric values by :data:`_START_OFFSET`, :math:`1/q`
    with :math:`q = 1009` a prime, so that no two are conjugate and none is
    real, which a polynomial with real coefficients would otherwise keep
    conjugate or real for good. Two points are conjugate where
    :math:`t_j = -t_k` and a point is real where :math:`t_k = 0`; either asks
    :math:`3q\,m = -2n` for an integer :math:`m`, so for every degree
    :math:`n` below :math:`3q = 3027` neither happens.
    """
    degree = len(coefficients) - 1
    constant = abs(coefficients[-1]) or Fraction(1)
    radius = _power_of_two(_exponent(constant / abs(coefficients[0])) // degree)
    points = []
    for k in range(degree):
        t = Fraction(2 * k + 1 - degree, degree) * Fraction(3, 2) + _START_OFFSET
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
    units of that grid. A point that has landed on another is first moved
    off it (:func:`_apart`), and where the damping cancels Newton's step
    exactly the step is taken undamped.
    """
    settled = True
    one: _Complex = (Fraction(1), Fraction(0))
    for i in range(len(points)):
        x = _apart(points, i, bits)
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
        undamped = (1 - damping[0], -damping[1])
        correction = _quotient(newton, undamped) if any(undamped) else newton
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


def _square_root_below(square: Fraction) -> Fraction:
    """A lower bound on the square root of *square*, :data:`_RADIUS_GUARD` bits within it.

    ``sqrt(a / b)`` is ``sqrt(a b) / b``, and the integer square root of
    ``a b 4^g`` over ``b 2^g`` is below it by less than ``2^-g`` of it.
    """
    shift = 1 << _RADIUS_GUARD
    scaled = square.numerator * square.denominator * shift * shift
    return Fraction(math.isqrt(scaled), square.denominator * shift)


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
    unit = Fraction(1, square.denominator << _RADIUS_GUARD)
    return _square_root_below(square) + unit


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


def _double(value: Fraction) -> float:
    r"""The double nearest *value*, a zero always ``+0.0``.

    Integer true division in Python is correctly rounded, ties to even, and
    adding ``+0.0`` turns a ``-0.0`` positive and leaves every other double
    as it is.

    :raises OverflowError: if *value* lies at or beyond
        :math:`\pm(2^{1024} - 2^{970})`, which round to nearest takes to
        infinity.
    """
    if abs(value) >= _OVERFLOW:
        msg = (
            "a root has a part at or beyond 2**1024 - 2**970, which round to "
            "nearest takes to infinity."
        )
        raise OverflowError(msg)
    return value.numerator / value.denominator + 0.0


def _boundary(nearest: float, towards: float) -> Fraction:
    """The rounding boundary between the double *nearest* and its neighbour towards *towards*.

    It is the midpoint of the two, exactly; past the largest double the
    neighbour is infinite, and the boundary is :data:`_OVERFLOW`.
    """
    neighbour = math.nextafter(nearest, towards)
    if not math.isfinite(neighbour):
        return _OVERFLOW if towards > 0 else -_OVERFLOW
    return (Fraction(nearest) + Fraction(neighbour)) / 2


def _rounded(low: Fraction, high: Fraction) -> float | None:
    """The double every point of ``[low, high]`` rounds to, or ``None``.

    *low* rounds to ``nearest``, and every point of the interval rounds to it
    when the whole interval lies strictly between the boundaries ``nearest``
    shares with its two neighbours, which is decided in exact rational
    arithmetic; an interval that reaches either boundary, the threshold of
    overflow among them, does not decide. A single point, an exact root,
    rounds as the division rounds it.

    :raises OverflowError: if the whole interval lies at or beyond the
        threshold of overflow.
    """
    if low <= -_OVERFLOW < high or low < _OVERFLOW <= high:
        return None
    nearest = _double(low)
    if low == high:
        return nearest
    below, above = _boundary(nearest, -math.inf), _boundary(nearest, math.inf)
    return nearest if below < low and high < above else None


def _boundary_within(low: Fraction, high: Fraction) -> Fraction | None:
    """A rounding boundary that ``[low, high]`` reaches, or ``None``.

    The threshold of overflow if the interval reaches it, else a midpoint
    beside the double *low* rounds to. Called where :func:`_rounded` did not
    decide, so the interval lies within the thresholds when it reaches
    neither.
    """
    for threshold in (-_OVERFLOW, _OVERFLOW):
        if low <= threshold <= high:
            return threshold
    nearest = _double(low)
    for towards in (math.inf, -math.inf):
        boundary = _boundary(nearest, towards)
        if low <= boundary <= high:
            return boundary
    return None


def _trimmed(polynomial: list[Fraction]) -> list[Fraction]:
    """*polynomial* without its leading zero coefficients."""
    start = 0
    while start < len(polynomial) and not polynomial[start]:
        start += 1
    return polynomial[start:]


def _remainder(dividend: list[Fraction], divisor: list[Fraction]) -> list[Fraction]:
    """The remainder of dividing *dividend* by *divisor*, exactly; *divisor* trimmed."""
    remainder = list(dividend)
    while len(remainder) >= len(divisor):
        ratio = remainder[0] / divisor[0]
        for k, coefficient in enumerate(divisor):
            remainder[k] -= ratio * coefficient
        remainder.pop(0)
        remainder = _trimmed(remainder)
    return remainder


def _common_divisor(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    """A greatest common divisor of two real polynomials, by Euclid's algorithm, exactly."""
    a, b = _trimmed(a), _trimmed(b)
    while b:
        a, b = b, _remainder(a, b)
    return a


def _real_value(polynomial: list[Fraction], t: Fraction) -> Fraction:
    """A real polynomial at *t*, by Horner's rule, exactly."""
    value = Fraction(0)
    for coefficient in polynomial:
        value = value * t + coefficient
    return value


def _on_the_line(
    coefficients: Polynomial, axis: int, value: Fraction
) -> tuple[list[Fraction], list[Fraction]]:
    r"""*p* on the line where coordinate *axis* is *value*, as :math:`A(t) + \mathrm{i}\,B(t)`.

    :math:`t` is the other coordinate: the point is :math:`v + \mathrm{i}t`
    on the line of real part :math:`v` (*axis* 0) and :math:`t + \mathrm{i}v`
    on the line of imaginary part :math:`v` (*axis* 1). The polynomial is
    shifted to the line's origin by repeated synthetic division, which gives
    the coefficients of :math:`p(c + w)` in :math:`w` exactly, and on the
    line of real part :math:`v` the power :math:`w^k` is
    :math:`\mathrm{i}^k t^k`.
    """
    origin: _Complex = (value, Fraction(0)) if axis == 0 else (Fraction(0), value)
    shifted: list[_Complex] = [(c, Fraction(0)) for c in coefficients]
    degree = len(shifted) - 1
    for last in range(degree, 0, -1):
        for j in range(1, last + 1):
            step = _product(origin, shifted[j - 1])
            shifted[j] = (shifted[j][0] + step[0], shifted[j][1] + step[1])
    if axis == 0:
        for position in range(len(shifted)):
            for _ in range((degree - position) % 4):
                shifted[position] = (-shifted[position][1], shifted[position][0])
    return [c[0] for c in shifted], [c[1] for c in shifted]


def _on_line(
    coefficients: Polynomial,
    centre: _Complex,
    radius: Fraction,
    axis: int,
    value: Fraction,
) -> bool:
    r"""Whether the one root in the disk has coordinate *axis* exactly *value*.

    The disk about *centre* holds one root of *p*, a simple one. On the line
    where coordinate *axis* is *value*, :math:`p = A(t) + \mathrm{i}\,B(t)`,
    so the roots of *p* on the line are the real roots of
    :math:`g = \gcd(A, B)`, each as simple in :math:`g` as in *p*. The line
    meets the disk in a chord of half-length
    :math:`h = \sqrt{r^2 - (v - c)^2}` about the centre's other coordinate;
    :math:`g` has at most one root on an interval inside the chord, a simple
    one, so it has one exactly where its values at the interval's ends differ
    in sign or vanish. The half-length is bounded below by an integer square
    root, so the interval lies inside the chord; a root on the line beyond it
    is found by a later pass, whose disk is smaller.
    """
    offset = value - centre[axis]
    half = _square_root_below(radius * radius - offset * offset)
    along = centre[1 - axis]
    divisor = _common_divisor(*_on_the_line(coefficients, axis, value))
    ends = _real_value(divisor, along - half) * _real_value(divisor, along + half)
    return ends <= 0


def _decided(
    coefficients: Polynomial, centre: _Complex, radius: Fraction, axis: int
) -> float | None:
    """The correctly rounded coordinate *axis* of the one root in the disk, or ``None``.

    The extent's ends round alike (:func:`_rounded`), or the extent reaches a
    rounding boundary the coordinate is exactly (:func:`_on_line`), which
    rounds to even; otherwise the disk does not decide yet.
    """
    low, high = centre[axis] - radius, centre[axis] + radius
    part = _rounded(low, high)
    if part is not None:
        return part
    boundary = _boundary_within(low, high)
    if boundary is None or not _on_line(coefficients, centre, radius, axis, boundary):
        return None
    return _double(boundary)


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
    being alone on it, or whose extent reaches a rounding boundary the
    coordinate is not exactly. The conjugate's imaginary part is
    ``0.0 - im``, so that a part that rounds to zero is ``+0.0`` on both.
    """
    x, radius = points[index], radii[index]
    widened = _alone_on_the_axis(index, points, radii)
    if widened is not None:
        # The point's real part is the widened disk's centre, so a disk about
        # it no wider holds the same root; on the axis the iteration can land
        # on the root itself, which then decides at once.
        on_axis = _radius_above(coefficients, (x[0], Fraction(0)))
        if 0 <= on_axis < widened:
            widened = on_axis
        part = _decided(coefficients, (x[0], Fraction(0)), widened, 0)
        return None if part is None else [complex(part, 0.0)]
    if -x[1] > radius:
        return []
    if x[1] <= radius:
        return None
    re = _decided(coefficients, x, radius, 0)
    im = _decided(coefficients, x, radius, 1)
    if re is None or im is None:
        return None
    return [complex(re, im), complex(re, 0.0 - im)]


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


def _settle(coefficients: Polynomial, points: list[_Complex], bits: int) -> None:
    """Sweep on the grid of *bits* until every correction is small, :data:`_PASS_STEPS` times at most."""
    for _ in range(_PASS_STEPS):
        if _aberth_sweep(coefficients, points, bits):
            return


def _nudge(points: list[_Complex], bits: int) -> None:
    """Move each point off any line of symmetry it has settled on, by a step of its own.

    Two approximations of two close real roots can settle on the vertical
    line through the roots' midpoint: there the iteration's corrections are
    purely imaginary and the grid holds the real part exactly, so they never
    reach the axis. A step of a relative ``2**(-bits/2)``, a different
    multiple of ``1 + 2i`` for each point, takes them off it.
    """
    for index, x in enumerate(points):
        points[index] = _shifted(x, index, -(bits // 2), bits)


def _shifted(x: _Complex, index: int, exponent: int, bits: int) -> _Complex:
    """*x* moved by a relative ``2**exponent`` times ``(index + 1)(1 + 2i)``, onto its grid."""
    scale = max(abs(x[0]), abs(x[1])) or Fraction(1)
    shift = _power_of_two(exponent) * scale * (index + 1)
    return _on_grid((x[0] + shift, x[1] + 2 * shift), bits)


def _apart(points: list[_Complex], index: int, bits: int) -> _Complex:
    """The point of *index*, moved a few hundred units of its grid off any other it has landed on.

    Two approximations of a cluster the grid cannot yet resolve can round to
    the same point, where the pull between them has no direction; the step
    differs from point to point, so they part.
    """
    x = points[index]
    if any(other == x for j, other in enumerate(points) if j != index):
        x = _shifted(x, index, 8 - bits, bits)
    return x


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


def _iterated_roots(exact: Polynomial) -> list[complex]:
    """Every root of *exact*, none at zero, by the iteration and its certificate.

    :raises ArithmeticError: if the roots are not resolved at the finest grid.
    """
    points = _aberth(exact)
    bits = _FIRST_BITS
    while bits < _LAST_BITS:
        bits *= 2
        _settle(exact, points, bits)
        roots = _certified(exact, points)
        if roots is not None:
            return roots
        _nudge(points, bits)
    msg = (
        f"the roots were not resolved at {_LAST_BITS} bits; a multiple root "
        "never is, nor a cluster of roots the iteration has not parted by then."
    )
    raise ArithmeticError(msg)


def correctly_rounded_roots(
    coefficients: Sequence[Fraction | int],
) -> tuple[complex, ...]:
    """Every root of a real polynomial, each part the double nearest the exact root's.

    A root at zero is found exactly from the coefficients, whose last one is
    then zero, and divided out before the iteration.

    :param coefficients: The polynomial's exact coefficients, the highest
        power first, the first not zero. Its roots must be simple.
    :return: The roots, sorted by real part and then by imaginary part; a
        complex pair is a pair of conjugates, a real root has an imaginary
        part of ``0.0``, and every part that rounds to zero is ``+0.0``,
        whichever side of zero the exact part lies.
    :raises TypeError: if a coefficient is not a :class:`~fractions.Fraction`
        or an ``int``.
    :raises ValueError: if the polynomial is a constant.
    :raises OverflowError: if a part of a root lies at or beyond
        ``2**1024 - 2**970``, which round to nearest takes to infinity.
    :raises ArithmeticError: if zero is a multiple root, which the
        coefficients show, or if the roots are not resolved at 4096 bits, as a
        multiple root never is, nor a cluster of roots the iteration has not
        parted by then.
    """
    exact = _exact_coefficients(coefficients)
    kept = len(exact)
    while not exact[kept - 1]:
        kept -= 1
    at_zero = len(exact) - kept
    if at_zero > 1:
        msg = f"zero is a root {at_zero} times over; a multiple root is refused."
        raise ArithmeticError(msg)
    roots = _iterated_roots(exact[:kept]) if kept > 1 else []
    roots += [complex(0.0, 0.0)] * at_zero
    return tuple(sorted(roots, key=lambda z: (z.real, z.imag)))
