#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pinned ``sin``, ``tan`` and ``hypot`` are correctly rounded.

``_pinned_trig`` answers with the double nearest the exact value, which has
one definition and no platform in it. These tests hold it to that on inputs
where glibc itself is not correctly rounded (the values were computed at 400
bits with an independent arbitrary-precision library), check ``hypot`` against
exact rational arithmetic, and pin the property the weighting design relies
on: on every sine, tangent and magnitude a design evaluates, glibc is
correctly rounded too, so the pinned routines return the C library's own bits
there and the shipped Linux coefficients do not move.
"""

from __future__ import annotations

import math
import platform
from fractions import Fraction

import numpy as np
import pytest

from phonometry.filters import _weighting_design
from phonometry.filters._pinned_trig import pinned_hypot, pinned_sin, pinned_tan
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


@pytest.mark.parametrize(
    ("function", "cases"), [(pinned_sin, _SIN_HARD), (pinned_tan, _TAN_HARD)]
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

    This is why switching to correctly rounded routines moved no shipped
    Linux coefficient: on these inputs glibc's ``sin``, ``tan`` and ``hypot``
    (the last through Python's complex ``abs``) return the nearest double.
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
    gap_sin = np.abs(_ordered(pinned_sin(x)) - _ordered(np.sin(x)))
    gap_tan = np.abs(_ordered(pinned_tan(t)) - _ordered(np.tan(t)))
    assert int(gap_sin.max()) <= 1
    assert int(gap_tan.max()) <= 1


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
