#  Copyright (c) 2026. Jose Manuel Requena Plens
"""numpy's complex product and quotient, spelled in real arithmetic.

numpy multiplies and divides complex arrays in loops of plain C that a
compiler may contract into multiply-adds, which numpy built with clang does on
every 64-bit ARM and on x86-64 from AVX2 on, and numpy built with GCC does not:
the same product moved by its last bit between platforms. These are numpy's
steps in numpy's order, each a separately rounded Python ``float`` operation,
so the answer is the unfused one everywhere. The weighting design of
:mod:`phonometry.filters` and the ITU-R BS.468-4 prototype
(:mod:`phonometry._internal.itu_r_468`) take their complex arithmetic from
here.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

__all__ = ["complex_product", "complex_quotient"]


def _shifted_to(w_ref: float, roots: np.ndarray) -> list[tuple[float, float]]:
    """``j w_ref - r`` for each root, as ``(real, imaginary)``, formed as numpy forms it."""
    return [(0.0 - root.real, w_ref - root.imag) for root in roots.tolist()]


def complex_product(factors: list[tuple[float, float]]) -> tuple[float, float]:
    r"""``numpy.prod`` of complex numbers, in real arithmetic, one rounding per operation.

    numpy multiplies a complex array left to right, each step
    :math:`(a_r b_r - a_i b_i) + \mathrm{j}(a_r b_i + a_i b_r)`, and the loop
    it runs a product through is plain C a compiler may contract: numpy built
    with clang fuses each of those into a multiply-add wherever the processor
    has one, on every 64-bit ARM and on x86-64 from AVX2 on, and numpy built
    with GCC does not. The product a design took through it moved by its last
    bit between Linux and the macOS and Windows builds, and so did the A
    weighting at 48 kHz. These are numpy's steps in the order numpy takes
    them, each a separately rounded Python ``float`` operation, which no
    compiler contracts, so the answer is the unfused one everywhere.

    :param factors: The complex numbers as ``(real, imaginary)`` pairs.
    :return: Their product as a pair, ``(1.0, 0.0)`` for none.
    """
    if not factors:
        return 1.0, 0.0
    real, imaginary = factors[0]
    for factor_real, factor_imaginary in factors[1:]:
        real, imaginary = (
            real * factor_real - imaginary * factor_imaginary,
            real * factor_imaginary + imaginary * factor_real,
        )
    return real, imaginary


def complex_quotient(
    numerator: tuple[float, float], denominator: tuple[float, float]
) -> tuple[float, float]:
    """numpy's complex division, Smith's algorithm, in real arithmetic.

    The same steps numpy's loop takes, in the same order, each rounded once,
    for the reason :func:`complex_product` gives: numpy's loop is C that clang
    contracts into multiply-adds. The denominator is never zero here, since
    every root the design maps lies in the closed left half plane and is
    taken away from a positive ``2 fs``.

    :param numerator: ``(real, imaginary)``.
    :param denominator: ``(real, imaginary)``, not zero.
    :return: The quotient as a pair.
    """
    real, imaginary = numerator
    below_real, below_imaginary = denominator
    if math.fabs(below_real) >= math.fabs(below_imaginary):
        ratio = below_imaginary / below_real
        scale = 1.0 / (below_real + below_imaginary * ratio)
        return (real + imaginary * ratio) * scale, (imaginary - real * ratio) * scale
    ratio = below_real / below_imaginary
    scale = 1.0 / (below_imaginary + below_real * ratio)
    return (real * ratio + imaginary) * scale, (imaginary * ratio - real) * scale
