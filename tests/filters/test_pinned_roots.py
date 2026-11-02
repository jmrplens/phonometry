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
#: the integer square root, the neighbour of a double and infinity.
_EXACT_MATH = frozenset({"inf", "isqrt", "nextafter"})


def test_the_root_finder_reaches_no_numerical_library() -> None:
    """Read off the source: no numpy, SciPy or LAPACK, and of ``math`` only exact steps.

    The roots are the same doubles everywhere because nothing between the
    exact coefficients and the one rounding at the end is a library's
    arithmetic: Python's integers and fractions are exact, ``math.isqrt``
    is an integer function and ``math.nextafter`` the neighbouring double.
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
    from_math = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "math"
    }
    assert from_math <= _EXACT_MATH, sorted(from_math - _EXACT_MATH)
