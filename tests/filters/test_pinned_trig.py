#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pinned ``sin``, ``tan``, ``atan`` and ``hypot`` are correctly rounded.

``_pinned_trig`` answers with the double nearest the exact value, which has
one definition and no platform in it. These tests hold it to that on inputs
where glibc itself is not correctly rounded (the values were computed at 400
bits with an independent arbitrary-precision library), check ``hypot`` against
exact rational arithmetic and ``atan`` against exact rational bounds on the
tangent (:mod:`arctan_oracle`), and pin what the weighting design relies on:
on every sine, tangent and magnitude a design evaluates, glibc is correctly
rounded too, so the pinned routines return the C library's own bits there,
while on 19 of the arctangents the checked designs evaluate it is not, and
the pinned arctangent returns the correctly rounded value glibc misses.
"""

from __future__ import annotations

import math
import platform
from fractions import Fraction

import numpy as np
import pytest
from arctan_oracle import is_correctly_rounded_arctangent

from phonometry.filters import _weighting_design
from phonometry.filters._pinned_trig import (
    _atan_scalar,
    _hypot_scalar,
    _sin_scalar,
    _tan_scalar,
    pinned_atan,
    pinned_hypot,
    pinned_sin,
    pinned_tan,
)
from phonometry.filters.weighting import _analog_weighting_zpk, _fit_band

#: ``(x, correctly rounded sin x)``, both as hex, at inputs where glibc 2.41's
#: ``sin`` returns the other neighbour. Computed with mpmath at 400 bits.
_SIN_HARD = (
    ("0x1.78a5850a3243dp+1", "0x1.94f354ac3acddp-3"),
    ("0x1.99d18df77b2e8p-2", "0x1.8ef73797d6b13p-2"),
    ("0x1.73b2feb9dde36p+1", "0x1.e23943f5b7f9dp-3"),
    ("0x1.4f47f1f779176p+1", "0x1.fec47d4ab5323p-2"),
    ("0x1.75ea5de97d775p+1", "0x1.bfb07d49d16a5p-3"),
    ("0x1.3c7152ee2cf7bp+1", "0x1.3db29a4bd78d3p-1"),
)

#: The same for ``tan``.
_TAN_HARD = (
    ("0x1.3761284791f86p-4", "0x1.37fb11e5695f0p-4"),
    ("0x1.3b7651f309c7dp-2", "0x1.45d6013848a35p-2"),
    ("0x1.d3dd8fef43cfep-3", "0x1.dc2da25b0223fp-3"),
    ("0x1.14f313643e1dap-4", "0x1.155f51542b1f9p-4"),
    ("0x1.c6fafb9ca5c1ap-4", "0x1.c8dc679793ca3p-4"),
    ("0x1.5a8a145ac19bep+0", "0x1.221ca163b3181p+2"),
)

#: The same for ``atan``: the 19 arguments, of the 15 866 distinct
#: arctangents the 133 checked designs evaluate, where glibc 2.41 returns the
#: other neighbour. They sit in 32 of those designs, among them the A
#: weighting at 44.1, 88.2 and 192 kHz. Computed with mpmath at 200 bits and
#: confirmed by the rational oracle below.
_ATAN_HARD = (
    ("0x1.60aff2484240ap-5", "0x1.6078397c2cb21p-5"),
    ("0x1.dd26c956129b0p-5", "0x1.dc9cee428ee82p-5"),
    ("0x1.328064d380af0p-4", "0x1.31ee6e71d6703p-4"),
    ("0x1.3f5134354fd6ep-4", "0x1.3eac3400112f8p-4"),
    ("0x1.5f84d220159d3p-4", "0x1.5ea8ddfaa6f25p-4"),
    ("0x1.9de5e3912fda6p-4", "0x1.9c7f70399289dp-4"),
    ("0x1.cc20c46f97aa0p-4", "0x1.ca34fee0931a1p-4"),
    ("0x1.e6b911d2fddd8p-4", "0x1.e4738555922d2p-4"),
    ("0x1.0a3caa408f675p-3", "0x1.08c0923d5e28cp-3"),
    ("0x1.2e3f6d08d3e77p-3", "0x1.2c14e5f9117dfp-3"),
    ("0x1.8a65676624071p-3", "0x1.85a0571b63c81p-3"),
    ("0x1.8dbad746a7863p-3", "0x1.88d7026f30806p-3"),
    ("0x1.79188b5fc199bp-2", "0x1.69509aae96ecep-2"),
    ("0x1.a688c27d4947ep-2", "0x1.90bd6bf20d841p-2"),
    ("0x1.7dd642ffa1b91p+0", "0x1.f5daa4c1179edp-1"),
    ("0x1.2959b07fef209p+1", "0x1.2a0fc004d6f46p+0"),
    ("0x1.d49cfea0a4b3cp+1", "0x1.4ddd0daf9bdbfp+0"),
    ("0x1.52ee09006238fp+3", "0x1.7a066d12d0885p+0"),
    ("0x1.6709e8bb1537ap+4", "0x1.86b9212253b43p+0"),
)


@pytest.mark.parametrize(
    ("function", "cases"),
    [(pinned_sin, _SIN_HARD), (pinned_tan, _TAN_HARD), (pinned_atan, _ATAN_HARD)],
)
def test_correctly_rounded_where_glibc_is_not(
    function: object, cases: tuple[tuple[str, str], ...]
) -> None:
    """The nearest double, on inputs the C library rounds the other way."""
    x = np.array([float.fromhex(value) for value, _ in cases])
    expected = np.array([float.fromhex(value) for _, value in cases])
    got = function(x)  # type: ignore[operator]
    np.testing.assert_array_equal(got.view(np.uint64), expected.view(np.uint64))


def test_hypot_is_the_exact_square_root_rounded_once() -> None:
    """Checked in rational arithmetic: the exact value lies within half an ulp.

    For a correctly rounded ``r`` the exact :math:`x^2 + y^2` lies between the
    squares of the two midpoints around ``r``; that comparison is exact in
    :class:`fractions.Fraction`, so it is an oracle owing nothing to the
    routine under test.
    """
    rng = np.random.default_rng(11)
    xs = rng.uniform(-1.0, 1.0, 2000) * 2.0 ** rng.integers(-40, 40, 2000)
    ys = rng.uniform(-1.0, 1.0, 2000) * 2.0 ** rng.integers(-40, 40, 2000)
    for x, y in zip(xs.tolist(), ys.tolist(), strict=True):
        r = pinned_hypot(x, y)
        exact = Fraction(x) ** 2 + Fraction(y) ** 2
        below = (Fraction(r) + Fraction(math.nextafter(r, 0.0))) / 2
        above = (Fraction(r) + Fraction(math.nextafter(r, math.inf))) / 2
        assert below * below <= exact <= above * above, (x, y)
    assert pinned_hypot(3.0, 4.0) == 5.0
    assert pinned_hypot(0.0, -0.0) == 0.0


#: The classes random bit patterns all but never draw, each one pattern in
#: 2 048, so 150 of them hold none: the signed zeros, subnormals at both ends
#: and in the middle of their range, the infinities and NaN.
_ARCTANGENT_SPECIALS = (
    0.0,
    -0.0,
    float.fromhex("0x0.0000000000001p-1022"),
    -float.fromhex("0x0.8000000000001p-1022"),
    float.fromhex("0x0.fffffffffffffp-1022"),
    math.inf,
    -math.inf,
    math.nan,
)


def _arctangent_draws() -> list[float]:
    r"""Doubles from the whole line: random bit patterns, a log-uniform band, the rest.

    Random bit patterns reach every exponent alike; the band from
    :math:`2^{-62}` to :math:`2^{62}` holds every argument whose arctangent is
    neither the argument itself nor the double nearest :math:`\pi/2`, where
    the routine does its real work; and the classes the patterns all but
    never draw, :data:`_ARCTANGENT_SPECIALS`, are added by hand.
    """
    rng = np.random.default_rng(29)
    patterns = rng.integers(0, 2**64, 150, dtype=np.uint64).view(np.float64)
    mantissas = rng.integers(0, 2**52, 250, dtype=np.uint64)
    exponents = (rng.integers(-62, 62, 250) + 1023).astype(np.uint64)
    signs = rng.integers(0, 2, 250, dtype=np.uint64)
    band = ((signs << np.uint64(63)) | (exponents << np.uint64(52)) | mantissas).view(
        np.float64
    )
    return [*patterns.tolist(), *band.tolist(), *_ARCTANGENT_SPECIALS]


def _neighbours(r: float) -> tuple[float, float]:
    """The doubles on either side of ``r``."""
    return math.nextafter(r, -math.inf), math.nextafter(r, math.inf)


def test_arctangent_is_correctly_rounded_by_rational_bounds() -> None:
    """Every answer lies within half an ulp, decided with no arctangent evaluated.

    :mod:`arctan_oracle` brackets the exact value between the midpoints around
    the answer through the tangent of each midpoint, enclosed in exact
    rational arithmetic, so the verdict owes nothing to the routine under test
    or to the C library. The oracle is shown to refuse as well: the doubles on
    both sides of every answer but a NaN's, and of each hard case's answer
    above, which takes in glibc's own answer there whichever side it falls on
    (below on 8 of the 19, above on the other 11).
    """
    for x in _arctangent_draws():
        answer = _atan_scalar(x)
        assert is_correctly_rounded_arctangent(x, answer), x.hex()
        if not math.isnan(x):
            for neighbour in _neighbours(answer):
                assert not is_correctly_rounded_arctangent(x, neighbour), x.hex()
    for argument, expected in _ATAN_HARD:
        x = float.fromhex(argument)
        assert is_correctly_rounded_arctangent(x, float.fromhex(expected))
        for neighbour in _neighbours(float.fromhex(expected)):
            assert not is_correctly_rounded_arctangent(x, neighbour), argument


@pytest.mark.parametrize(
    ("x", "r"),
    [(1.0, math.pi / 4 + 2 * math.pi), (0.5, 6.746832916180392), (1.0, 1e300)],
    ids=["pi-over-4-a-period-up", "atan-of-a-half-a-period-up", "far-out"],
)
def test_the_oracle_refuses_what_no_arctangent_reaches(x: float, r: float) -> None:
    r"""An answer a period away, or far out, is refused, and at once.

    The sign of the cosine that places a midpoint short of :math:`\pi/2`
    is positive again one period up, so the double nearest
    :math:`\pi/4 + 2\pi` passed for the arctangent of one, and that nearest
    :math:`\arctan(1/2) + 2\pi` for the arctangent of a half; and for an
    answer of 1e300 the enclosures never decided, so a broken routine would
    have hung the test instead of failing it.
    """
    assert not is_correctly_rounded_arctangent(x, r)
    assert not is_correctly_rounded_arctangent(-x, -r)


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ("0x0.0p+0", "0x0.0p+0"),
        ("-0x0.0p+0", "-0x0.0p+0"),
        ("inf", "0x1.921fb54442d18p+0"),
        ("-inf", "-0x1.921fb54442d18p+0"),
        ("0x0.0000000000001p-1022", "0x0.0000000000001p-1022"),
        ("-0x1.0000000000000p-1022", "-0x1.0000000000000p-1022"),
        ("0x1.fffffffffffffp-29", "0x1.fffffffffffffp-29"),
        ("0x1.0000000000000p-26", "0x1.fffffffffffffp-27"),
        ("0x1.0000000000000p+0", "0x1.921fb54442d18p-1"),
        ("0x1.0000000000000p+52", "0x1.921fb54442d17p+0"),
        ("0x1.0000000000000p+54", "0x1.921fb54442d18p+0"),
        ("0x1.fffffffffffffp+1023", "0x1.921fb54442d18p+0"),
    ],
)
def test_arctangent_edges(argument: str, expected: str) -> None:
    r"""Signed zeros keep their sign, the ends of the line give the nearest pi/2.

    Below :math:`2^{-28}` the arctangent rounds to its argument, subnormals
    included, while :math:`2^{-26}` is a power of two whose cubic term
    already reaches the narrower ulp below it; far out the answer is the
    double nearest :math:`\pi/2`, which is ``math.pi / 2``, and short of
    about :math:`5.8 \times 10^{15}` it is the double below.
    """
    x = float.fromhex(argument)
    got = pinned_atan(x)[()]
    assert np.float64(got).view(np.uint64) == np.float64(float.fromhex(expected)).view(
        np.uint64
    )
    assert is_correctly_rounded_arctangent(x, got)
    assert float.fromhex("0x1.921fb54442d18p+0") == math.pi / 2


def test_arctangent_of_a_nan_is_a_nan() -> None:
    """A NaN is handed back, as the C library hands it back."""
    assert math.isnan(pinned_atan(math.nan)[()])


def test_arctangent_is_odd() -> None:
    """``atan(-x)`` is ``-atan(x)``, bit for bit, on every draw."""
    draws = np.array(_arctangent_draws())
    np.testing.assert_array_equal(
        pinned_atan(-draws).view(np.uint64), (-pinned_atan(draws)).view(np.uint64)
    )


def _design_inputs(
    curve: str, fs: int
) -> tuple[list[float], list[float], list[complex]]:
    """The tangent, sine and complex-root arguments one design evaluates."""
    tangents: list[float] = []
    sines: list[float] = []
    roots: list[complex] = []
    original_tan = _weighting_design._scalar_tan
    original_sin = pinned_sin
    original_factors = _weighting_design._stable_factors

    def tan_spy(values: np.ndarray) -> np.ndarray:
        tangents.extend(np.asarray(values, dtype=np.float64).reshape(-1).tolist())
        return original_tan(values)

    def sin_spy(values: np.ndarray) -> np.ndarray:
        sines.extend(np.asarray(values, dtype=np.float64).reshape(-1).tolist())
        return original_sin(values)

    def factors_spy(values: np.ndarray) -> object:
        roots.extend(complex(v) for v in np.asarray(values).reshape(-1))
        return original_factors(values)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(_weighting_design, "_scalar_tan", tan_spy)
        patch.setattr(_weighting_design, "pinned_sin", sin_spy)
        patch.setattr(_weighting_design, "_stable_factors", factors_spy)
        zeros, poles, _ = _analog_weighting_zpk(curve)
        _weighting_design.design_sos(
            zeros,
            poles,
            float(fs),
            _fit_band(curve, fs),
            3 if curve == "D" else 4,
            1000.0,
        )
    return tangents, sines, roots


@pytest.mark.skipif(
    platform.libc_ver()[0] != "glibc",
    reason="the claim is about glibc: that it is correctly rounded on these inputs",
)
@pytest.mark.parametrize(("curve", "fs"), [("A", 48000), ("D", 44100)])
def test_glibc_agrees_on_every_input_a_design_evaluates(curve: str, fs: int) -> None:
    """Where the design reaches, the C library's own answer is the correctly rounded one.

    This is why the correctly rounded sine, tangent and magnitude moved no
    shipped Linux coefficient: on these inputs glibc's ``sin``, ``tan`` and
    ``hypot`` (the last through Python's complex ``abs``) return the nearest
    double. The arctangent is the one that did move some, through the inputs
    of :data:`_ATAN_HARD`.
    """
    tangents, sines, roots = _design_inputs(curve, fs)
    assert tangents
    assert sines
    np.testing.assert_array_equal(
        pinned_tan(np.array(tangents)), [math.tan(t) for t in tangents]
    )
    np.testing.assert_array_equal(
        pinned_sin(np.array(sines)), [math.sin(s) for s in sines]
    )
    for root in roots:
        assert pinned_hypot(root.real, root.imag) == abs(root)


def _ordered(values: np.ndarray) -> np.ndarray:
    as_int = values.view(np.int64)
    return np.where(as_int < 0, -(as_int & 0x7FFFFFFFFFFFFFFF), as_int)


def test_within_one_ulp_of_the_local_libm_everywhere() -> None:
    """On any platform, the correctly rounded value and the local libm stay adjacent."""
    rng = np.random.default_rng(5)
    x = np.concatenate(
        [rng.uniform(0.0, math.pi, 4000), rng.uniform(-1000.0, 1000.0, 1000)]
    )
    t = rng.uniform(-1.55, 1.55, 4000)
    a = rng.uniform(-1.0, 1.0, 4000) * 2.0 ** rng.integers(-30, 60, 4000)
    gap_sin = np.abs(_ordered(pinned_sin(x)) - _ordered(np.sin(x)))
    gap_tan = np.abs(_ordered(pinned_tan(t)) - _ordered(np.tan(t)))
    local_atan = np.array([math.atan(v) for v in a.tolist()])
    gap_atan = np.abs(_ordered(pinned_atan(a)) - _ordered(local_atan))
    assert int(gap_sin.max()) <= 1
    assert int(gap_tan.max()) <= 1
    assert int(gap_atan.max()) <= 1


def test_tiny_and_signed_arguments() -> None:
    """Below the cubic term the sine and the tangent are the argument itself, signs kept."""
    tiny = np.array([2.0**-40, -(2.0**-40), 5e-324, -0.0, 0.0])
    np.testing.assert_array_equal(
        pinned_sin(tiny).view(np.uint64), tiny.view(np.uint64)
    )
    np.testing.assert_array_equal(
        pinned_tan(tiny).view(np.uint64), tiny.view(np.uint64)
    )
    assert pinned_sin(-1.0)[()] == -pinned_sin(1.0)[()]
    assert pinned_tan(-1.0)[()] == -pinned_tan(1.0)[()]


@pytest.mark.parametrize("value", [1024.0, -1e6, np.inf, np.nan])
def test_trigonometry_refuses_arguments_outside_its_domain(value: float) -> None:
    """``|x| < 1024``: the design passes at most pi, and nothing past it is guessed at."""
    with pytest.raises(ValueError, match=r"\|x\| < 1024"):
        pinned_sin(value)
    with pytest.raises(ValueError, match=r"\|x\| < 1024"):
        pinned_tan(value)


def test_hypot_refuses_infinities() -> None:
    """The design never asks for the magnitude of an infinite root."""
    with pytest.raises(ValueError, match="finite arguments"):
        pinned_hypot(np.inf, 1.0)


@pytest.mark.parametrize(
    "value",
    ["3", True, 3, np.float32(3.0), 3 + 0j],
    ids=["text", "flag", "integer", "single", "complex"],
)
def test_hypot_refuses_anything_but_a_python_float_by_name(value: object) -> None:
    """A text, a flag, an integer, a narrower float or a complex is refused.

    Each argument used to go through :func:`float` first, so ``'3'`` read as
    3.0 and ``True`` as 1.0; the refusal names the argument, as the
    elementwise routines name theirs.
    """
    with pytest.raises(TypeError, match="'x' must be a Python float"):
        pinned_hypot(value, 4.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'y' must be a Python float"):
        pinned_hypot(4.0, value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [1, np.float32(0.5), True])
def test_the_scalar_routines_take_a_python_float_and_nothing_else(
    value: object,
) -> None:
    """Each routine settles what it was handed before it reads it as a number.

    The elementwise functions always hand over a Python float (``tolist`` of
    a float64 array), and :func:`pinned_hypot` refuses anything else by name
    before it hands its arguments on, so this refusal only fences the private
    routines: an integer or a single-precision value would otherwise be read
    at a precision nobody chose.
    """
    with pytest.raises(TypeError, match="Python float"):
        _sin_scalar(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Python float"):
        _tan_scalar(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Python float"):
        _atan_scalar(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Python floats"):
        _hypot_scalar(value, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Python floats"):
        _hypot_scalar(1.0, value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [np.array([1.0 + 2.0j]), ["0.5"], [bytearray(b"1")]],
    ids=["complex", "text", "bytes"],
)
def test_sin_tan_and_atan_refuse_what_holds_no_real_number_by_name(
    value: object,
) -> None:
    """A complex value, a text or a bytearray is refused, not read as numbers."""
    with pytest.raises(TypeError, match="'values'"):
        pinned_sin(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'values'"):
        pinned_tan(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'values'"):
        pinned_atan(value)  # type: ignore[arg-type]
