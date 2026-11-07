#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The ITU-R BS.468-4 weighting network, rebuilt from its seven components.

The poles and gain of the passive network of Fig. 1a, which the ``'468'``
curve of :func:`phonometry.filters.weighting_filter` discretises and
:func:`phonometry.electroacoustics.weighting_bs468` evaluates in closed form.
Both read the one prototype here, so the digital design and the analog
response cannot drift apart.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

import numpy as np

from .pinned_complex import _shifted_to, complex_product
from .pinned_roots import (
    Polynomial,
    correctly_rounded_roots,
    exact_polynomial_product,
    exact_polynomial_sum,
)
from .pinned_trig import pinned_hypot

__all__ = ["itu_r_468_prototype"]


#: Source resistance of ITU-R BS.468-4 Fig. 1a, in series with the generator.
SOURCE_OHM = 600.0
#: Load the Fig. 1a response is taken across: the amplifier input, drawn in
#: the figure as ``Z = 600 ohm``.
LOAD_OHM = 600.0
#: The seven reactive elements of ITU-R BS.468-4 Fig. 1a, "Weighting network,
#: simple form" (printed p. 1), in ladder order left to right. Kinds are
#: ``"shunt_c"`` (capacitor to ground, admittance ``s C``), ``"series_l"``
#: (inductor in the series arm, impedance ``s L``) and ``"series_c"`` (the one
#: capacitor in the series arm, impedance ``1 / (s C)``). Values in SI units;
#: the figure prints nF and mH.
LADDER: tuple[tuple[str, float], ...] = (
    ("shunt_c", 13.85e-9),
    ("series_l", 12.88e-3),
    ("shunt_c", 26.82e-9),
    ("series_c", 33.06e-9),
    ("shunt_c", 9.21e-9),
    ("series_l", 26.49e-3),
    ("shunt_c", 31.47e-9),
)


#: A two-port's ABCD matrix ``[[A, B], [C, D]]``, each entry a polynomial in
#: ``s`` held as its exact coefficients, the highest power first.
_TwoPort = list[list[Polynomial]]


def _abcd_product(left: _TwoPort, right: _TwoPort) -> _TwoPort:
    """Product of two 2x2 ABCD matrices whose entries are polynomials in ``s``.

    The chain rule of two-port theory is an ordinary matrix product over the
    polynomial ring, so the ladder's transfer function comes out as
    polynomials, with no per-frequency evaluation; and over exact rational
    coefficients it comes out with no rounding either, where ``numpy``'s
    ``polymul`` hands each product to the BLAS.

    :param left: The upstream two-port, as ``[[A, B], [C, D]]``.
    :param right: The downstream two-port, in the same form.
    :return: The cascade ``left @ right``.
    """
    return [
        [
            exact_polynomial_sum(
                exact_polynomial_product(left[row][0], right[0][col]),
                exact_polynomial_product(left[row][1], right[1][col]),
            )
            for col in (0, 1)
        ]
        for row in (0, 1)
    ]


def _ladder_element(kind: str, value: float) -> _TwoPort:
    """The ABCD matrix of one element of the Fig. 1a ladder, exactly.

    The component values are read as the doubles the table holds, each an
    exact rational number.
    """
    one, zero, s = (Fraction(1),), (Fraction(0),), (Fraction(1), Fraction(0))
    exact = Fraction(value)
    if kind == "shunt_c":
        return [[one, zero], [(exact, Fraction(0)), one]]
    if kind == "series_l":
        return [[one, (exact, Fraction(0))], [zero, one]]
    # "series_c": s * [[1, 1 / (s C)], [0, 1]], the scaling the prototype's
    # docstring describes.
    return [[s, (1 / exact,)], [zero, s]]


@lru_cache(maxsize=1)
def itu_r_468_prototype() -> tuple[tuple[complex, ...], float]:
    r"""Poles and gain of the ITU-R BS.468-4 weighting network.

    Clause 1 of the Recommendation makes the passive network of Fig. 1a the
    primitive: "The nominal response curve of the weighting network is given
    in Fig. 1b which is the theoretical response of the passive network shown
    in Fig. 1a. Table 1 gives the values of this response at various
    frequencies." So the nominal curve is defined at every frequency, and the
    21 rows of Table 1 are that curve sampled and rounded to 0.1 dB, not the
    definition. The network is rebuilt here from the seven printed component
    values by a polynomial ABCD chain, rather than stored as precomputed
    roots, so a reader can check the constants against the figure.

    Chaining the ladder scaled by ``s`` clears the series capacitor's
    ``1 / (s C)`` entry, which is the whole of the algebra: the scaling comes
    back as the numerator of

    .. math::

       H(s) = \frac{K\,s}{s^6 + a_5 s^5 + \dots + a_0},

    one zero at the origin because that series capacitor blocks dc, and six
    poles because ``C2``, ``C3`` and ``C4`` form a capacitive loop whose
    third state is dependent (seven reactive elements, order six). The
    coefficients are exact: the chain runs in rational arithmetic over the
    component values, so the denominator is the network's own polynomial,
    and the poles are its roots with each part correctly rounded
    (:func:`~phonometry._internal.pinned_roots.correctly_rounded_roots`), the
    same doubles on every platform. ``numpy.roots`` takes them as
    eigenvalues through LAPACK, which is a library's arithmetic and gave
    other last bits on 64-bit ARM; its answers lie within its own error of
    these. The resulting curve reproduces all 21 rows of Table 1 to
    0.0503 dB maximum and 0.0264 dB rms, which is the 0.05 dB rounding
    quantum of the printed table (the 100 Hz row overshoots it by
    0.0002 dB, a rounding tie the four-significant-figure component values
    cannot resolve).

    :return: The six poles in rad/s, sorted for reproducibility, and the
        gain ``K`` that puts the response at 0 dB at the 1 kHz reference
        frequency Table 1 prints as its zero row.
    """
    abcd: _TwoPort = [
        [(Fraction(1),), (Fraction(SOURCE_OHM),)],
        [(Fraction(0),), (Fraction(1),)],
    ]
    for kind, value in LADDER:
        abcd = _abcd_product(abcd, _ladder_element(kind, value))

    # Loading the two-port: V_out / V_in = 1 / (A + B / R_load), times the s
    # the series capacitor's matrix was scaled by.
    load = Fraction(LOAD_OHM)
    denominator = exact_polynomial_sum(abcd[0][0], tuple(c / load for c in abcd[0][1]))
    poles = correctly_rounded_roots(denominator)
    w_ref = 2.0 * np.pi * 1000.0
    # prod(j w_ref - poles), spelled in real arithmetic by complex_product
    # because numpy's own complex product is fused on some builds.
    at_reference = complex_product(_shifted_to(w_ref, np.array(poles)))
    gain = pinned_hypot(*at_reference) / w_ref
    return poles, gain
