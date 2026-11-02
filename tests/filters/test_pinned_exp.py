#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pinned ``exp`` and ``pow`` return glibc's own bits.

``_pinned_exp`` exists so the weighting fit takes its exponentials and powers
from no platform at all, and that is only worth having if it moves no shipped
coefficient: the routines it spells are glibc's (ARM's optimized-routines, in
the variant compiled for a fused multiply-add unit), so on a machine whose C
library is that routine the two must agree bit for bit. These tests pin a
deterministic slice of the validation that established it, the inputs one
actual design evaluates, and the exact fused multiply-add emulation every
fused site of the C routines goes through.
"""

from __future__ import annotations

import math
import sys

import numpy as np
import pytest
from libm_identity import on_the_pinned_libm

from phonometry.filters import _weighting_design
from phonometry.filters._pinned_exp import (
    _fused_multiply_add,
    _round_to_odd_sum,
    pinned_exp,
    pinned_pow,
)
from phonometry.filters.weighting import _analog_weighting_zpk, _fit_band


def _exp_reference(values: np.ndarray) -> np.ndarray:
    def one(value: float) -> float:
        try:
            return math.exp(value)
        except OverflowError:
            return math.inf

    return np.fromiter(map(one, values.tolist()), np.float64, values.size)


def _pow_reference(base: np.ndarray, exponent: np.ndarray) -> np.ndarray:
    def one(x: float, y: float) -> float:
        try:
            return math.pow(x, y)
        except OverflowError:
            return math.inf

    return np.fromiter(
        map(one, base.tolist(), exponent.tolist()), np.float64, base.size
    )


def _mismatches(mine: np.ndarray, reference: np.ndarray) -> np.ndarray:
    return np.asarray(mine.view(np.uint64) != reference.view(np.uint64))


def _probe() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A deterministic canary over both routines' main paths."""
    rng = np.random.default_rng(12345)
    x = rng.uniform(-700.0, 700.0, 4096)
    base = np.exp(rng.uniform(-40.0, 40.0, 4096))
    exponent = rng.uniform(-8.0, 8.0, 4096)
    return x, base, exponent


@on_the_pinned_libm
def test_exp_bits_match_over_the_whole_domain() -> None:
    """Every regime: the fast path, the scaled edges near overflow and underflow, tiny."""
    rng = np.random.default_rng(0)
    x = np.concatenate(
        [
            rng.uniform(-745.0, 710.0, 100_000),
            rng.uniform(-30.0, 120.0, 100_000),
            rng.uniform(-1.0, 1.0, 50_000) * 2.0 ** -rng.integers(0, 60, 50_000),
        ]
    )
    assert not _mismatches(pinned_exp(x), _exp_reference(x)).any()


@on_the_pinned_libm
def test_pow_bits_match_over_the_bases_and_exponents_the_design_uses() -> None:
    """Powers of ten, powers of one, small integer powers, and wide random draws."""
    rng = np.random.default_rng(1)
    n = 50_000
    base = np.concatenate(
        [
            np.exp(rng.uniform(-700.0, 700.0, n)),
            np.full(n, 10.0),
            rng.uniform(1e-14, 200.0, n),
            rng.uniform(1.0, 1e6, n),
        ]
    )
    exponent = np.concatenate(
        [
            rng.uniform(-1.0, 1.0, n),
            rng.uniform(-6.0, 8.0, n),
            np.full(n, 1.0),
            np.full(n, 2.0),
        ]
    )
    assert not _mismatches(
        pinned_pow(base, exponent), _pow_reference(base, exponent)
    ).any()


@on_the_pinned_libm
def test_pow_of_a_subnormal_base_matches() -> None:
    """A base below the normal range is rescaled by 2**52 first, as the C routine does."""
    rng = np.random.default_rng(4)
    n = 20_000
    base = rng.integers(1, 1 << 52, n).astype(np.float64) * 2.0**-1074
    exponent = np.concatenate(
        [rng.uniform(0.001, 1.0, n // 2), rng.uniform(-0.2, -0.001, n // 2)]
    )
    assert not _mismatches(
        pinned_pow(base, exponent), _pow_reference(base, exponent)
    ).any()


@on_the_pinned_libm
def test_every_exp_and_pow_input_of_a_real_design_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The agreement holds on the inputs the fit actually produces.

    A spy captures every array the A weighting at 48 kHz hands its
    exponential and its power, and each is replayed through :mod:`math`: the
    fit's own universe of inputs, not a synthetic distribution.
    """
    exps: list[np.ndarray] = []
    pows: list[tuple[np.ndarray, np.ndarray]] = []
    original_exp = _weighting_design._scalar_exp
    original_pow = pinned_pow

    def exp_spy(values: np.ndarray) -> np.ndarray:
        exps.append(np.asarray(values, dtype=np.float64).reshape(-1).copy())
        return original_exp(values)

    def pow_spy(base: object, exponent: object) -> np.ndarray:
        x, y = np.broadcast_arrays(
            np.asarray(base, dtype=np.float64), np.asarray(exponent, dtype=np.float64)
        )
        pows.append((x.reshape(-1).copy(), y.reshape(-1).copy()))
        return original_pow(base, exponent)  # type: ignore[arg-type]

    monkeypatch.setattr(_weighting_design, "_scalar_exp", exp_spy)
    monkeypatch.setattr(_weighting_design, "pinned_pow", pow_spy)
    _weighting_design._exponentials.cache_clear()
    zeros, poles, _ = _analog_weighting_zpk("A")
    _weighting_design.design_sos(
        zeros, poles, 48000.0, _fit_band("A", 48000), 4, 1000.0, n_origin_zeros=4
    )
    assert exps, "the design evaluated no exponential"
    assert pows, "the design evaluated no power"
    x = np.unique(np.concatenate(exps))
    assert not _mismatches(pinned_exp(x), _exp_reference(x)).any()
    base = np.concatenate([b for b, _ in pows])
    exponent = np.concatenate([e for _, e in pows])
    assert not _mismatches(
        pinned_pow(base, exponent), _pow_reference(base, exponent)
    ).any()


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="math.fma, the reference, is new in Python 3.13"
)
def test_fused_multiply_add_is_correctly_rounded() -> None:
    """The emulation behind every fused site, against the C library's ``fma``.

    The near-cancelling draws are where a double rounding would show: the
    product and the addend nearly annihilate, so the answer is made of the
    product's low half, and an emulation that rounded twice would miss it.
    The wide draws cover exponent gaps up to two hundred binades.
    """
    rng = np.random.default_rng(3)
    n = 200_000
    a = rng.uniform(-1.0, 1.0, n) * 2.0 ** rng.integers(-60, 60, n)
    b = rng.uniform(-1.0, 1.0, n) * 2.0 ** rng.integers(-60, 60, n)
    near = -(a * b) * (1.0 + rng.uniform(-1e-15, 1e-15, n))
    wide = rng.uniform(-1.0, 1.0, n) * 2.0 ** rng.integers(-120, 120, n)
    for c in (near, wide):
        reference = np.fromiter(
            map(math.fma, a.tolist(), b.tolist(), c.tolist()), np.float64, n
        )
        assert not _mismatches(_fused_multiply_add(a, b, c), reference).any()


def test_round_to_odd_leaves_exact_sums_and_odd_results() -> None:
    """Rounding to odd: an exact sum is kept, an inexact one lands on an odd significand."""
    exact = _round_to_odd_sum(np.array([1.0, 0.5]), np.array([2.0, 0.25]))
    np.testing.assert_array_equal(exact, [3.0, 0.75])
    inexact = _round_to_odd_sum(
        np.array([1.0, 1.0, -1.0]), np.array([2.0**-60, -(2.0**-60), 2.0**-60])
    )
    bits = inexact.view(np.uint64)
    np.testing.assert_array_equal(bits & np.uint64(1), [1, 1, 1])
    np.testing.assert_array_equal(
        inexact,
        [np.nextafter(1.0, 2.0), np.nextafter(1.0, 0.0), np.nextafter(-1.0, 0.0)],
    )


def test_specials_follow_the_c_routines() -> None:
    """``exp`` of the infinities and of NaN; overflow and underflow; the identities of ``pow``."""
    out = pinned_exp(np.array([-np.inf, np.inf, np.nan, 710.0, -746.0, 0.0, -0.0]))
    np.testing.assert_array_equal(out[:2], [0.0, np.inf])
    assert math.isnan(out[2])
    np.testing.assert_array_equal(out[3:], [np.inf, 0.0, 1.0, 1.0])
    np.testing.assert_array_equal(
        pinned_pow(np.array([1.0, 3.0, 2.0, 10.0]), np.array([123.0, 0.0, 1.0, 2.0])),
        [1.0, 1.0, 2.0, 100.0],
    )
    assert pinned_pow(2.0, 1e20)[()] == np.inf
    assert pinned_pow(0.5, 1e20)[()] == 0.0


def test_a_result_that_vanishes_below_the_subnormals_is_positive_zero() -> None:
    """Past the subnormal range the C routines return ``+0.0``, not ``-0.0``.

    The scale of such a result carries an exponent pushed out of range, and
    its sign is read only after ``2^1022`` is added back, as the C routine
    reads it; reading the unshifted bits gave ``-0.0`` for these inputs.
    """
    vanished = pinned_exp(np.array([float.fromhex("-0x1.f7230f248753bp+9")]))
    assert vanished.view(np.uint64)[0] == 0
    vanished = pinned_pow(
        np.array([float.fromhex("0x1.61a6a897d43fep-775")]),
        np.array([float.fromhex("0x1.d2cb91367e7ecp+0")]),
    )
    assert vanished.view(np.uint64)[0] == 0


@pytest.mark.parametrize(
    ("base", "exponent"), [(0.0, 2.0), (-2.0, 2.0), (np.inf, 1.0), (2.0, np.nan)]
)
def test_pow_refuses_what_the_design_never_asks(base: float, exponent: float) -> None:
    """A base that is not positive and finite, or an exponent that is not finite."""
    with pytest.raises(ValueError, match="positive finite base and a finite exponent"):
        pinned_pow(base, exponent)


def test_shape_and_empty_are_preserved() -> None:
    """The elementwise contract: any shape in, the same shape out."""
    square = np.array([[0.5, 1.5], [2.5, 3.5]])
    assert pinned_exp(square).shape == (2, 2)
    assert pinned_exp(np.empty(0)).shape == (0,)
    assert pinned_pow(square, 2.0).shape == (2, 2)
    assert pinned_pow(np.empty(0), 2.0).shape == (0,)
    np.testing.assert_array_equal(
        pinned_exp(square).reshape(-1), pinned_exp(square.reshape(-1))
    )


def _ordered(values: np.ndarray) -> np.ndarray:
    as_int = values.view(np.int64)
    return np.where(as_int < 0, -(as_int & 0x7FFFFFFFFFFFFFFF), as_int)


def test_within_one_ulp_of_the_local_libm_everywhere() -> None:
    """On any platform, the pinned routines and the local libm stay adjacent.

    Every C library rounds ``exp`` and ``pow`` to within about half an ulp of
    the true value, so wherever two of them disagree the answers are
    floating-point neighbours. This is the portable half of the contract.
    """
    x, base, exponent = _probe()
    gap_exp = np.abs(_ordered(pinned_exp(x)) - _ordered(_exp_reference(x)))
    gap_pow = np.abs(
        _ordered(pinned_pow(base, exponent)) - _ordered(_pow_reference(base, exponent))
    )
    assert int(gap_exp.max()) <= 1
    assert int(gap_pow.max()) <= 1


@pytest.mark.parametrize(
    "value",
    [np.array([1.0 + 2.0j]), ["0.5"], [bytearray(b"1")]],
    ids=["complex", "text", "bytes"],
)
def test_exp_and_pow_refuse_what_holds_no_real_number_by_name(value: object) -> None:
    """A complex value, a text or a bytearray is refused, not read as numbers.

    ``np.asarray(value, dtype=np.float64)`` kept a complex value's real part,
    parsed a text and read a bytearray as the codes of its characters.
    """
    with pytest.raises(TypeError, match="'values'"):
        pinned_exp(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'base'"):
        pinned_pow(value, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'exponent'"):
        pinned_pow(2.0, value)  # type: ignore[arg-type]
