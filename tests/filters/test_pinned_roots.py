#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The polynomial roots the BS.468-4 prototype takes, correctly rounded.

:mod:`phonometry.filters._pinned_roots` finds every root of a polynomial with
exact coefficients and rounds each part to the nearest double. These tests
hold it to answers found another way: roots written in closed form, rounded
here by exact integer square roots and rational midpoints, so neither the
iteration nor its certificate has a part in them; the 468 network's six poles
as an arbitrary-precision library computed them; and :func:`numpy.roots`,
which the prototype used to call, within its own error.
"""

from __future__ import annotations

import ast
import inspect
import math
import random
import subprocess
import sys
import textwrap
from fractions import Fraction

import numpy as np
import pytest
import scipy.linalg

from phonometry.filters import _pinned_roots
from phonometry.filters._pinned_roots import (
    correctly_rounded_roots,
    exact_polynomial_product,
    exact_polynomial_sum,
)
from phonometry.filters.weighting import (
    _ITU_R_468_LADDER,
    _ITU_R_468_LOAD_OHM,
    _ITU_R_468_SOURCE_OHM,
    _abcd_product,
    _itu_r_468_prototype,
    _ladder_element,
)

#: The six poles of the ITU-R BS.468-4 network of Fig. 1a, in rad/s: the roots
#: of its denominator over the seven component values the table holds, each
#: part rounded to the nearest double. Computed with mpmath 1.3.0, roots
#: found to 3000 bits and each part accepted only where an interval of a
#: relative 2^-2400 around it rounds to one double.
_468_POLES = (
    ("-0x1.e9a65711e74aap+15", "0x0.0p+0"),
    ("-0x1.94becddf7a993p+14", "0x0.0p+0"),
    ("-0x1.70fe240f0b0b0p+14", "-0x1.1c37d1603bcd6p+15"),
    ("-0x1.70fe240f0b0b0p+14", "0x1.1c37d1603bcd6p+15"),
    ("-0x1.24defc9c7e130p+14", "-0x1.e7f8501a8afddp+15"),
    ("-0x1.24defc9c7e130p+14", "0x1.e7f8501a8afddp+15"),
)


def _468_denominator() -> tuple[Fraction, ...]:
    """The network's denominator, exactly, as the prototype builds it."""
    abcd = [
        [(Fraction(1),), (Fraction(_ITU_R_468_SOURCE_OHM),)],
        [(Fraction(0),), (Fraction(1),)],
    ]
    for kind, value in _ITU_R_468_LADDER:
        abcd = _abcd_product(abcd, _ladder_element(kind, value))
    load = Fraction(_ITU_R_468_LOAD_OHM)
    return exact_polynomial_sum(abcd[0][0], tuple(c / load for c in abcd[0][1]))


def _bits(roots: tuple[complex, ...] | list[complex]) -> list[tuple[str, str]]:
    """Each root as the hex of its two parts, so that equality is bit for bit."""
    return [(z.real.hex(), z.imag.hex()) for z in roots]


def test_the_468_poles_are_the_correctly_rounded_roots_of_the_network() -> None:
    """Each part of each pole is the double nearest the exact root's.

    Pinned to values an arbitrary-precision library found, so the test reads
    the same on every platform and says which doubles the prototype has; the
    pairs are exact conjugates and the two real poles have no imaginary part.
    """
    poles, _ = _itu_r_468_prototype()
    expected = [complex(float.fromhex(re), float.fromhex(im)) for re, im in _468_POLES]
    assert _bits(poles) == _bits(expected)
    assert _bits(correctly_rounded_roots(_468_denominator())) == _bits(expected)


def _ulps_apart(a: float, b: float) -> int:
    """How many doubles lie between *a* and *b*, of one sign."""
    return abs(int(np.float64(a).view(np.int64)) - int(np.float64(b).view(np.int64)))


def test_numpy_finds_the_468_poles_within_its_own_error() -> None:
    r"""What the prototype took from :func:`numpy.roots` is these poles, to numpy's error.

    numpy takes the roots as the eigenvalues of the balanced companion
    matrix, through LAPACK, which is backward stable: each eigenvalue it
    returns is within :math:`n \varepsilon \lVert B \rVert_2 \kappa` of an
    exact one, :math:`\kappa` its condition number, and the coefficients it
    is handed are the exact ones rounded to doubles, which moves each root by
    :math:`\sum_k |\delta a_k| |r|^{n-k} / |p'(r)|` more. The poles here
    are within that of numpy's, at a small fraction of it, on whatever
    platform runs this; and numpy's answer is not the correctly rounded one,
    which is why the two parted in their last bits.
    """
    exact = _468_denominator()
    monic = [c / exact[0] for c in exact]
    doubles = np.array([float(c) for c in monic])
    degree = len(doubles) - 1
    ours = np.array(_itu_r_468_prototype()[0])
    theirs = np.roots(doubles)
    companion = np.diag(np.ones(degree - 1), -1)
    companion[0, :] = -doubles[1:]
    balanced, _ = scipy.linalg.matrix_balance(companion, permute=False)
    values, left, right = scipy.linalg.eig(balanced, left=True, right=True)
    slope = np.polyval(np.polyder(doubles), ours)
    eps = float(np.finfo(np.float64).eps)
    worst = 0.0
    for root, derivative in zip(ours, slope, strict=True):
        found = theirs[np.argmin(np.abs(theirs - root))]
        i = int(np.argmin(np.abs(values - root)))
        kappa = (
            np.linalg.norm(left[:, i])
            * np.linalg.norm(right[:, i])
            / abs(np.vdot(left[:, i], right[:, i]))
        )
        backward = degree * eps * np.linalg.norm(balanced, 2) * kappa
        rounding = sum(
            abs(float(monic[k] - Fraction(doubles[k]))) * abs(root) ** (degree - k)
            for k in range(degree + 1)
        ) / abs(derivative)
        worst = max(worst, abs(found - root) / (backward + rounding))
    assert worst < 1.0, f"numpy is {worst:.3f} of its own error bound away"


def _rounded(low: Fraction, high: Fraction) -> float | None:
    """The double all of ``[low, high]`` rounds to, or ``None``: decided exactly."""
    nearest = low.numerator / low.denominator
    exact = Fraction(nearest)
    below = (exact + Fraction(math.nextafter(nearest, -math.inf))) / 2
    above = (exact + Fraction(math.nextafter(nearest, math.inf))) / 2
    return nearest if below < low and high < above else None


def _nearest_double(centre: Fraction, square: Fraction, sign: int) -> float:
    """The double nearest ``centre + sign * sqrt(square)``, by integer square roots.

    The square root is enclosed between ``isqrt(square 4^m) / 2^m`` and one
    unit more, and ``m`` grows until the enclosure rounds to one double.
    """
    for bits in (128, 256, 512, 1024, 2048):
        scale = 1 << bits
        floor = Fraction(math.isqrt(math.floor(square * scale * scale)), scale)
        ends = sorted(
            (centre + sign * floor, centre + sign * (floor + Fraction(1, scale)))
        )
        found = _rounded(*ends)
        if found is not None:
            return found
    msg = "the closed form did not decide at 2048 bits"
    raise AssertionError(msg)


def _random_rational(rng: random.Random) -> Fraction:
    """A rational of either sign, scaled anywhere from 2^-20 to 2^20."""
    value = Fraction(rng.randint(-(10**6), 10**6), rng.randint(1, 10**6))
    return value * Fraction(2) ** rng.randint(-20, 20)


def _factor(rng: random.Random) -> tuple[tuple[Fraction, ...], list[complex]]:
    """A random factor and its roots, correctly rounded from their closed form.

    A linear factor, a quadratic with a conjugate pair, or a quadratic with
    two real roots, ``x^2 + b x + c``, its roots ``-b/2 +/- sqrt(b^2/4 - c)``.
    """
    kind = rng.choice(("linear", "complex", "real"))
    if kind == "linear":
        root = _random_rational(rng)
        return (Fraction(1), -root), [complex(root.numerator / root.denominator)]
    centre = _random_rational(rng)
    spread = abs(_random_rational(rng)) + Fraction(1, 10**9)
    if kind == "complex":
        square = spread * spread * Fraction(rng.randint(2, 97), rng.randint(2, 97))
        re = centre.numerator / centre.denominator
        im = _nearest_double(Fraction(0), square, 1)
        polynomial = (Fraction(1), -2 * centre, centre * centre + square)
        return polynomial, [complex(re, im), complex(re, -im)]
    square = spread * spread * Fraction(rng.randint(2, 97), rng.randint(2, 97))
    roots = [complex(_nearest_double(centre, square, s)) for s in (-1, 1)]
    return (Fraction(1), -2 * centre, centre * centre - square), roots


@pytest.mark.parametrize("seed", range(60))
def test_every_root_is_the_double_nearest_its_closed_form(seed: int) -> None:
    """Polynomials of random factors, their roots rounded from closed forms.

    The factors are linear, quadratics with a conjugate pair and quadratics
    with two real irrational roots, their coefficients rational and their
    scales spread over twelve decades, multiplied out exactly; each root's
    parts are rounded here from ``-b/2`` and ``sqrt(|b^2/4 - c|)`` by integer
    square roots, a method the routine does not use.
    """
    rng = random.Random(seed)
    polynomial: tuple[Fraction, ...] = (Fraction(1),)
    expected: list[complex] = []
    for _ in range(rng.randint(1, 4)):
        factor, roots = _factor(rng)
        polynomial = exact_polynomial_product(polynomial, factor)
        expected += roots
    expected.sort(key=lambda z: (z.real, z.imag))
    assert _bits(correctly_rounded_roots(polynomial)) == _bits(expected)


def test_a_root_on_a_rounding_boundary_rounds_to_even() -> None:
    """A root exactly half way between two doubles takes the even one.

    ``1 + 2^-53`` lies half way between 1 and the next double, and
    ``1 + 3 * 2^-53`` half way between that one and the one after: the first
    rounds down to 1 and the second up, each to the neighbour with the even
    last bit, as round to nearest has it. No interval about such a root ever
    decides, so the root has to be found exactly.
    """
    low, high = Fraction(1) + Fraction(1, 2**53), Fraction(1) + Fraction(3, 2**53)
    roots = correctly_rounded_roots(
        exact_polynomial_product((Fraction(1), -low), (Fraction(1), Fraction(-3)))
    )
    assert _bits(roots) == _bits([complex(1.0), complex(3.0)])
    (root,) = correctly_rounded_roots((Fraction(1), -high))
    assert root.real.hex() == "0x1.0000000000002p+0"


def test_roots_at_the_origin_and_on_the_axes_come_back_exact() -> None:
    """``x^3 + x`` and ``x^2 - 3x + 2``: exact roots, signed zeros positive."""
    assert _bits(correctly_rounded_roots([1, 0, 1, 0])) == _bits(
        [complex(0.0, -1.0), complex(0.0, 0.0), complex(0.0, 1.0)]
    )
    assert _bits(correctly_rounded_roots([1, -3, 2])) == _bits([1 + 0j, 2 + 0j])


#: The root finder run in a child, so that a polynomial it never finishes
#: fails in bounded time on every platform: ``SIGALRM`` does not exist on
#: Windows, the suite's own limit waits fifteen minutes, and a thread cannot
#: be stopped while its fractions grow.
_CHILD = textwrap.dedent(
    """
    import sys
    from fractions import Fraction
    from phonometry.filters._pinned_roots import correctly_rounded_roots
    coefficients = [Fraction(c) for c in sys.argv[1:]]
    try:
        roots = correctly_rounded_roots(coefficients)
    except ArithmeticError as error:
        print(type(error).__name__, error)
    else:
        print(" ".join(f"{z.real.hex()},{z.imag.hex()}" for z in roots))
    """
)


def _printed(roots: list[complex]) -> str:
    """*roots* as the child prints them."""
    return " ".join(f"{z.real.hex()},{z.imag.hex()}" for z in roots)


def _roots_in_a_child(coefficients: list[Fraction]) -> str:
    """What the root finder prints for *coefficients*, in a child given a minute.

    A child that does not return within the minute fails the test with
    ``subprocess.TimeoutExpired``, whose command line carries the coefficients.
    """
    # Fixed argv, no shell, no user input
    finished = subprocess.run(
        [sys.executable, "-c", _CHILD, *(str(c) for c in coefficients)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return finished.stdout.strip()


def test_a_child_past_its_minute_fails_with_the_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A root finder that never returns fails the test with the timeout itself.

    ``subprocess.run`` raises ``TimeoutExpired`` naming the command, which
    carries the coefficients, and the minute it waited; the helper lets it
    through rather than catching it to fail the test by hand.
    """

    def overrun(command: list[str], **options: object) -> object:
        raise subprocess.TimeoutExpired(command, 60)

    monkeypatch.setattr(subprocess, "run", overrun)
    coefficients = [Fraction(1), Fraction(-1, 3)]
    with pytest.raises(subprocess.TimeoutExpired, match=r"'-1/3'.*60 seconds"):
        _roots_in_a_child(coefficients)


def test_a_root_at_zero_is_read_off_the_coefficients() -> None:
    """``x^3 - 2x``, ``x (x - 1/3)`` and ``3x``: the root at zero is exact.

    A polynomial whose constant term is zero has a root at zero, and the
    iteration, whose grid follows each point's own magnitude, approached it
    ever more closely without its disk ever deciding: the root finder never
    returned on the first two. The root is now read off the coefficients,
    divided out and returned as ``+0.0``; the others are rounded here from
    their closed forms.
    """
    root2 = [_nearest_double(Fraction(0), Fraction(2), sign) for sign in (-1, 1)]
    expected = [complex(root2[0]), complex(0.0), complex(root2[1])]
    cubic = [Fraction(1), Fraction(0), Fraction(-2), Fraction(0)]
    assert _roots_in_a_child(cubic) == _printed(expected)
    third = [complex(0.0), complex(_double(Fraction(1, 3)))]
    assert _roots_in_a_child([Fraction(1), Fraction(-1, 3), Fraction(0)]) == (
        _printed(third)
    )
    assert _bits(correctly_rounded_roots([3, 0])) == _bits([complex(0.0)])


def test_zero_as_a_multiple_root_is_refused_at_once() -> None:
    """``x^2 (x - 1)`` ends in two zeros, so zero is a double root, refused as such.

    It was refused before only after every grid had failed, with the
    message of a root the iteration could not resolve; it is refused now
    before the iteration starts, so it is run here and not in a child.
    """
    polynomial = [Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
    with pytest.raises(ArithmeticError, match="zero is a root 2 times over"):
        correctly_rounded_roots(polynomial)


def _conjugate_pair(re: Fraction, im: Fraction) -> tuple[Fraction, ...]:
    """``(x - re)^2 + im^2``, whose roots are ``re +/- i im``."""
    return (Fraction(1), -2 * re, re * re + im * im)


@pytest.mark.parametrize("apart", [40, 52, 60, 100])
def test_close_roots_are_told_apart(apart: int) -> None:
    """Roots ``2**-apart`` apart come back each on its own, rounded on its own.

    Two approximations of two close real roots can settle on the vertical
    line through their midpoint, where every correction is imaginary and the
    grid holds the real part exactly; the root finder used to refuse such a
    pair from ``2**-40`` apart down, and a pair of conjugate pairs from
    ``2**-100``. ``1 + 2**-40`` and ``1 + 2**-52`` are doubles of their own;
    ``1 + 2**-60`` and ``1 + 2**-100`` round to 1, so the two roots come
    back as the same double.
    """
    near = 1 + Fraction(1, 2**apart)
    rounded = near.numerator / near.denominator
    reals = correctly_rounded_roots(
        exact_polynomial_product((Fraction(1), Fraction(-1)), (Fraction(1), -near))
    )
    assert _bits(reals) == _bits([complex(1.0), complex(rounded)])
    pairs = correctly_rounded_roots(
        exact_polynomial_product(
            _conjugate_pair(Fraction(1), Fraction(1)),
            _conjugate_pair(near, Fraction(1)),
        )
    )
    expected = [complex(1.0, -1.0), complex(rounded, -1.0)]
    expected += [complex(1.0, 1.0), complex(rounded, 1.0)]
    assert _bits(pairs) == _bits(sorted(expected, key=lambda z: (z.real, z.imag)))


#: The root finder's helpers as it ships them, which :class:`_Path` wraps.
_VALUE_AND_SLOPE = _pinned_roots._value_and_slope
_RADIUS_ABOVE = _pinned_roots._radius_above
_SHIFTED = _pinned_roots._shifted
_CERTIFIED_ROOT = _pinned_roots._certified_root
_BOUNDARY_WITHIN = _pinned_roots._boundary_within


class _Path:
    """The edge cases the root finder meets on one polynomial, counted by wrapping its helpers."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.zero_slopes = 0
        self.no_radius = 0
        self.parted = 0
        self.decided_on_the_axis = 0
        self.waited_across_the_axis = 0
        self.at_the_threshold = 0
        module = _pinned_roots
        value_and_slope, radius_above = _VALUE_AND_SLOPE, _RADIUS_ABOVE
        shifted, certified_root = _SHIFTED, _CERTIFIED_ROOT
        boundary_within = _BOUNDARY_WITHIN

        def counted_value_and_slope(
            coefficients: tuple[Fraction, ...], x: tuple[Fraction, Fraction]
        ) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
            value, slope = value_and_slope(coefficients, x)
            self.zero_slopes += not any(slope)
            return value, slope

        def counted_radius_above(
            coefficients: tuple[Fraction, ...], x: tuple[Fraction, Fraction]
        ) -> Fraction:
            radius = radius_above(coefficients, x)
            self.no_radius += radius < 0
            return radius

        def counted_shifted(
            x: tuple[Fraction, Fraction], index: int, exponent: int, bits: int
        ) -> tuple[Fraction, Fraction]:
            self.parted += exponent == 8 - bits
            return shifted(x, index, exponent, bits)

        def counted_certified_root(
            coefficients: tuple[Fraction, ...],
            index: int,
            points: list[tuple[Fraction, Fraction]],
            radii: list[Fraction],
        ) -> list[complex] | None:
            x, radius = points[index], radii[index]
            widened = module._alone_on_the_axis(index, points, radii)
            if widened is not None:
                on_axis = radius_above(coefficients, (x[0], Fraction(0)))
                self.decided_on_the_axis += 0 <= on_axis < widened
            else:
                self.waited_across_the_axis += -radius <= x[1] <= radius
            return certified_root(coefficients, index, points, radii)

        def counted_boundary_within(low: Fraction, high: Fraction) -> Fraction | None:
            boundary = boundary_within(low, high)
            self.at_the_threshold += boundary in {module._OVERFLOW, -module._OVERFLOW}
            return boundary

        monkeypatch.setattr(module, "_value_and_slope", counted_value_and_slope)
        monkeypatch.setattr(module, "_radius_above", counted_radius_above)
        monkeypatch.setattr(module, "_shifted", counted_shifted)
        monkeypatch.setattr(module, "_certified_root", counted_certified_root)
        monkeypatch.setattr(module, "_boundary_within", counted_boundary_within)


def _close_reals(a: Fraction, b: Fraction) -> tuple[Fraction, ...]:
    """``(x - a)(x - b)``."""
    return exact_polynomial_product((Fraction(1), -a), (Fraction(1), -b))


def test_the_iteration_meets_its_edge_cases_on_close_real_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three pairs of real roots a few dozen bits apart, each through one edge of the search.

    ``-5`` and ``-5 + 2**-54``: the derivative of a quadratic vanishes
    midway between its roots, an approximation lands there exactly, where
    Newton's step has no value and the disk no radius, so the sweep leaves
    it and the certificate waits for the next pass; two approximations land
    on one point on the way and are parted. ``2`` and ``2 + 2**-77``: an
    approximation alone on the axis decides on the radius at its real part,
    which is smaller. ``-2`` and ``-2 + 2**-77``: a disk across the axis that
    is not alone on it waits for the next pass. Each pair rounds to one
    double twice, and the counts show each edge was met, so that the test
    keeps holding them when the search changes.
    """
    path = _Path(monkeypatch)
    roots = correctly_rounded_roots(_close_reals(Fraction(-5), -5 + Fraction(1, 2**54)))
    assert _bits(roots) == _bits([complex(-5.0), complex(-5.0)])
    assert path.zero_slopes > 0
    assert path.no_radius > 0
    assert path.parted > 0
    path = _Path(monkeypatch)
    roots = correctly_rounded_roots(_close_reals(Fraction(2), 2 + Fraction(1, 2**77)))
    assert _bits(roots) == _bits([complex(2.0), complex(2.0)])
    assert path.decided_on_the_axis > 0
    path = _Path(monkeypatch)
    roots = correctly_rounded_roots(_close_reals(Fraction(-2), -2 + Fraction(1, 2**77)))
    assert _bits(roots) == _bits([complex(-2.0), complex(-2.0)])
    assert path.waited_across_the_axis > 0


def test_a_disk_across_the_threshold_of_overflow_waits_for_the_next_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``x^2 - (t^2 - 1)`` and ``x^2 - (t^2 + 1)``, ``t`` the threshold ``2^1024 - 2^970``.

    Their roots lie a hair inside and outside the threshold of overflow. The
    first disks reach across it, which decides nothing, and the search waits
    until a disk lies on one side: the roots inside round to the largest
    double and its negative, those outside are refused with ``OverflowError``.
    """
    threshold = Fraction(2**1024 - 2**970)
    largest = _double(Fraction(_LARGEST))
    path = _Path(monkeypatch)
    roots = correctly_rounded_roots((Fraction(1), Fraction(0), -(threshold**2 - 1)))
    assert _bits(roots) == _bits([complex(-largest), complex(largest)])
    assert path.at_the_threshold > 0
    path = _Path(monkeypatch)
    outside = (Fraction(1), Fraction(0), -(threshold**2 + 1))
    with pytest.raises(OverflowError, match=r"2\*\*1024 - 2\*\*970"):
        correctly_rounded_roots(outside)
    assert path.at_the_threshold > 0


def test_the_grid_keeps_the_origin_and_a_lone_point_reaches_no_boundary() -> None:
    """Two contracts of the search's helpers that no polynomial reaches on its own.

    A point at the origin stays there on every grid, its scale having no
    exponent to read; and a single point that is not a midpoint between two
    doubles reaches no rounding boundary, which the certificate only asks of
    an interval that has reached one.
    """
    origin = (Fraction(0), Fraction(0))
    assert _pinned_roots._on_grid(origin, 64) == origin
    assert _pinned_roots._boundary_within(Fraction(1), Fraction(1)) is None


def _double(value: Fraction) -> float:
    """The double nearest *value*, by Python's correctly rounded integer division."""
    return value.numerator / value.denominator


def test_two_conjugate_pairs_2_to_the_minus_92_apart_come_back_rounded() -> None:
    """Two conjugate pairs ``0.886 * 2**-92`` apart, and a real root beside them.

    With the starting points of the time, two approximations of the upper
    pair rounded to the same point on the first grid, where the pull between
    them divides by zero, and the root finder raised ``ZeroDivisionError``.
    From the shifted starting points they no longer meet there; where two
    approximations do land on one point, they are parted first
    (:func:`test_the_iteration_meets_its_edge_cases_on_close_real_roots`).
    The pairs' parts round to the same doubles.
    """
    centre, height = Fraction(-48185, 542566), Fraction(138853, 148271)
    shifted = centre + Fraction(886, 1000) / 2**92
    real = Fraction(96787, 781363)
    polynomial = exact_polynomial_product(
        exact_polynomial_product(
            _conjugate_pair(centre, height), _conjugate_pair(shifted, height)
        ),
        (Fraction(1), -real),
    )
    expected = [complex(_double(real))]
    for re in (centre, shifted):
        expected += [complex(_double(re), s * _double(height)) for s in (-1, 1)]
    roots = correctly_rounded_roots(polynomial)
    assert _bits(roots) == _bits(sorted(expected, key=lambda z: (z.real, z.imag)))


@pytest.mark.parametrize(
    ("half_units", "expected"),
    [(1, "0x1.0000000000000p+0"), (3, "0x1.0000000000002p+0")],
)
def test_a_complex_root_whose_real_part_is_a_tie_rounds_to_even(
    half_units: int, expected: str
) -> None:
    """``(x - a)^2 + 2``, ``a = 1 + k 2^-53`` half way between two doubles.

    No disk about the real part ever lies on one side of the midpoint, and
    the iteration cannot land on the root, whose imaginary part is
    irrational; the root finder refused these two simple roots as if they
    were a multiple one. The real part is now decided exactly on the line
    through the midpoint, and rounds to even.
    """
    a = 1 + Fraction(half_units, 2**53)
    roots = correctly_rounded_roots((Fraction(1), -2 * a, a * a + 2))
    im = _nearest_double(Fraction(0), Fraction(2), 1)
    re = float.fromhex(expected)
    assert _bits(roots) == _bits([complex(re, -im), complex(re, im)])


def test_a_complex_root_whose_imaginary_part_is_a_tie_rounds_to_even() -> None:
    """``(x^2 + 2 + b^2)^2 - 8 x^2``, whose roots are ``+/-sqrt(2) +/- i b``.

    ``b = 1 + 2^-53`` lies half way between 1 and the next double, and the
    real parts are irrational, so no disk about an imaginary part decides
    and the root finder refused the quartic; each imaginary part is now
    decided exactly on the line through the midpoint and rounds to 1.
    """
    b = 1 + Fraction(1, 2**53)
    square = exact_polynomial_product(
        (Fraction(1), Fraction(0), 2 + b * b), (Fraction(1), Fraction(0), 2 + b * b)
    )
    quartic = exact_polynomial_sum(square, (Fraction(-8), Fraction(0), Fraction(0)))
    root2 = [_nearest_double(Fraction(0), Fraction(2), sign) for sign in (-1, 1)]
    expected = [complex(re, s) for re in root2 for s in (-1.0, 1.0)]
    assert _bits(correctly_rounded_roots(quartic)) == _bits(expected)


def test_every_part_that_rounds_to_zero_is_positive_zero() -> None:
    """``x^2 + 2``, ``(x^2 + 2)(x - 1)``, ``x + 2^-1100`` and ``x^2 + 2^-2200``.

    The real parts of the first two are exactly zero, and the extent about
    them reached both sides and rounded its lower end to ``-0.0``; the root
    of the third, ``-2^-1100``, rounds to ``-0.0`` as a division does; and
    the conjugate of the fourth's pair, ``+/-i 2^-1100``, took a negated
    zero. Every part that rounds to zero is now ``+0.0``.
    """
    root2 = _nearest_double(Fraction(0), Fraction(2), 1)
    pair = [complex(0.0, -root2), complex(0.0, root2)]
    quadratic = (Fraction(1), Fraction(0), Fraction(2))
    cases = [
        (quadratic, pair),
        (exact_polynomial_product(quadratic, (Fraction(1), Fraction(-1))), [
            *pair, complex(1.0)
        ]),
        ((Fraction(1), Fraction(1, 2**1100)), [complex(0.0)]),
        ((Fraction(1), Fraction(0), Fraction(1, 2**2200)), [complex(0.0)] * 2),
    ]  # fmt: skip
    for polynomial, expected in cases:
        assert _bits(correctly_rounded_roots(polynomial)) == _bits(expected)


def test_no_two_starting_points_are_conjugate_and_none_is_real() -> None:
    """For every degree from 2 to 200, as the starting points' docstring says.

    The iteration keeps two conjugate points conjugate and a real point real
    on a polynomial with real coefficients, so neither may start that way.
    The offset off the symmetric values was 1/7, which gave conjugate starts
    at every multiple of 21 and a real one at the odd multiples.
    """
    failing = []
    for degree in range(2, 201):
        monic = (Fraction(1),) + (Fraction(0),) * (degree - 1) + (Fraction(1),)
        points = _pinned_roots._starts(monic)
        mirrored = {(re, -im) for re, im in points}
        if any(not im for _, im in points) or mirrored & set(points):
            failing.append(degree)
    assert failing == []


#: The largest double, ``2**1024 - 2**971``.
_LARGEST = 2**1024 - 2**971


@pytest.mark.parametrize(
    "root", [2**1100, -(2**1100), 2**1024 - 2**970], ids=["above", "below", "tie"]
)
def test_a_root_round_to_nearest_takes_to_infinity_is_refused(root: int) -> None:
    """``2^1100``, its negative and ``2^1024 - 2^970``, the tie above the largest double.

    They raised ``OverflowError`` from the division, with a message about an
    integer quotient; the refusal now names the threshold.
    """
    with pytest.raises(OverflowError, match=r"2\*\*1024 - 2\*\*970"):
        correctly_rounded_roots([1, -root])


def test_a_root_that_rounds_to_the_largest_double_comes_back_as_it() -> None:
    """``x^2 - (r^2 + 1)``, ``r`` 2^950 below the largest double, and ``x - r``.

    The irrational roots round to the largest double and its negative. The
    rounding boundary above the largest double was taken as the midpoint
    with its neighbour, which is infinite and has no exact value, so the
    root finder raised ``OverflowError``; it is ``2^1024 - 2^970``.
    """
    r = Fraction(_LARGEST - 2**950)
    largest = _double(Fraction(_LARGEST))
    roots = correctly_rounded_roots((Fraction(1), Fraction(0), -(r * r + 1)))
    assert _bits(roots) == _bits([complex(-largest), complex(largest)])
    assert _bits(correctly_rounded_roots((Fraction(1), -r))) == _bits(
        [complex(largest)]
    )


def test_a_multiple_root_is_refused() -> None:
    """``(x - 1)^2`` has no two disjoint disks to separate, at any grid."""
    with pytest.raises(ArithmeticError, match="multiple root"):
        correctly_rounded_roots([1, -2, 1])


@pytest.mark.parametrize(
    ("coefficients", "error", "match"),
    [
        ([1.0, -2.0], TypeError, "must be exact"),
        ([True, 1], TypeError, "must be exact"),
        ([3], ValueError, "degree one or more"),
        ([0, 1, 2], ValueError, "degree one or more"),
    ],
    ids=["floats", "flag", "constant", "leading-zero"],
)
def test_what_is_not_an_exact_polynomial_is_refused(
    coefficients: list[object], error: type[Exception], match: str
) -> None:
    """Floats would bring their own rounding in; a constant has no roots."""
    with pytest.raises(error, match=match):
        correctly_rounded_roots(coefficients)  # type: ignore[arg-type]


def test_the_polynomial_arithmetic_is_exact() -> None:
    """``(x + 1/3)(x - 2/7) = x^2 + x/21 - 2/21`` and sums align at the constant."""
    product = exact_polynomial_product(
        (Fraction(1), Fraction(1, 3)), (Fraction(1), Fraction(-2, 7))
    )
    assert product == (Fraction(1), Fraction(1, 21), Fraction(-2, 21))
    assert exact_polynomial_sum(
        (Fraction(1), Fraction(0), Fraction(5)), (Fraction(2),)
    ) == (
        Fraction(1),
        Fraction(0),
        Fraction(7),
    )


#: What the root finder may import: exact rational arithmetic, typing, and
#: :mod:`math`, of which it may read only the operations below.
_EXACT_IMPORTS = frozenset(
    {"__future__", "collections.abc", "fractions", "math", "typing"}
)

#: The names of :mod:`math` whose answers IEEE 754 or integer arithmetic fix:
#: the integer square root, the neighbour of a double, whether a double is
#: finite, and infinity.
_EXACT_MATH = frozenset({"inf", "isfinite", "isqrt", "nextafter"})


def test_the_root_finder_reaches_no_numerical_library() -> None:
    """Read off the source: no numpy, SciPy or LAPACK, and of ``math`` only exact steps.

    The roots are the same doubles everywhere because nothing between the
    exact coefficients and the one rounding at the end is a library's
    arithmetic: Python's integers and fractions are exact, ``math.isqrt``
    is an integer function, ``math.nextafter`` the neighbouring double and
    ``math.isfinite`` a test of the exponent's bits.
    A ``numpy`` call or a ``math`` transcendental slipped in would answer
    with the platform's bits again.
    """
    tree = ast.parse(inspect.getsource(_pinned_roots))
    imported = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }  # fmt: skip
    assert imported <= _EXACT_IMPORTS, sorted(imported - _EXACT_IMPORTS)
    assert _inexact_math(tree) == []


def _inexact_math(tree: ast.AST) -> list[str]:
    """Each reading of :mod:`math` in *tree* that is not one of its exact steps.

    ``math.name`` for a name outside :data:`_EXACT_MATH`, and an import that
    binds :mod:`math`, or one of its routines, where that check cannot read
    it: ``import math as m`` and ``from math import exp`` would hand
    ``m.exp`` and a bare ``exp`` to the C library unseen.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "math"
            and node.attr not in _EXACT_MATH
        ):
            found.append(f"{node.lineno}: math.{node.attr}")
        elif isinstance(node, ast.Import):
            found.extend(
                f"{node.lineno}: import math as {alias.asname}"
                for alias in node.names
                if alias.name == "math" and alias.asname not in {None, "math"}
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "math":
            found.extend(
                f"{node.lineno}: from math import {alias.name}"
                for alias in node.names
                if alias.name not in _EXACT_MATH
            )
    return sorted(found)


def test_the_root_finder_check_sees_math_under_another_name() -> None:
    """``math`` read through an attribute, renamed, or by a routine's bare name."""
    source = textwrap.dedent(
        """
        import math
        import math as m
        from math import exp, isqrt
        from math import *
        def f(x):
            return math.isqrt(x), math.nextafter(x, 0.0), math.log(x), m.exp(x)
        """
    )
    assert _inexact_math(ast.parse(source)) == [
        "3: import math as m",
        "4: from math import exp",
        "5: from math import *",
        "7: math.log",
    ]
