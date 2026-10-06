#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Verdicts at a printed limit that do not hang on the last bits of a float (private).

A standard prints its limits in decimal and says in words which side of them
the limit itself falls on: a margin "of 6 dB or more", a spread that "does not
exceed" 1,5 dB, a ratio "limited to 0,99". The quantity judged against such a
limit is computed, the difference of two readings, the mean of three, the
ratio of two areas, and in binary a difference that is 6,0 dB in decimal comes
out 5,999 999 999 999 996 as often as 6,000 000 000 000 004. Which of the two
depends on the readings, on the order of a sum and on the machine, so a verdict
read straight off the comparison turns on the last bit, and so does a half
rounded to the nearest whole number.

The quantity is therefore settled first: rounded to nine decimal places, a
nanodecibel, a nanometre or a billionth of a ratio. That is far below any
digit a standard prints or an instrument reads, and far above the binary error
of a decimal quantity of ordinary size, so a value that is on the limit in
decimal is on it after settling, on either side of it only when it truly is.
The settled value only decides the verdict; the result keeps the computed one.

A quantity too large for nine decimals to sit above its last bit (a stiffness
of :math:`10^{8}` N/m³, say) is compared as its ratio to the limit instead, which
is of order one, and one too small for nine decimals to see (a sound power in
watts) as its ratio to the whole it is part of (:func:`settled_ratio`). A
signed sum judged against zero is one of these: its whole is the sum of the
magnitudes of its terms. A degenerate fit, a slope of :math:`10^{-18}` from data that do
not change, is not a boundary of this kind and is judged by a named physical
threshold in the module that fits it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

#: Decimal places a computed quantity is settled to before it is compared with
#: a printed limit or rounded at a half: a nanodecibel, far below any printed
#: digit, far above the binary error of a decimal quantity of ordinary size.
SETTLED_DECIMALS = 9


def settled(value: ArrayLike) -> NDArray[np.float64]:
    """``value`` rounded to nine decimal places, for judging it against a limit.

    :param value: The computed quantity, any shape.
    :return: The settled values as a float array (a 0-d array for a scalar).
    """
    return np.round(np.asarray(value, dtype=np.float64), SETTLED_DECIMALS)


def settled_ratio(part: ArrayLike, whole: ArrayLike) -> NDArray[np.float64]:
    """``part / whole`` settled, for judging a quantity on its own scale.

    A quantity whose size is the caller's, a sound power in watts or an
    intensity in watts per square metre, cannot be settled to nine decimals
    of its unit: a power of :math:`10^{-6}` W would settle to nothing. Its
    ratio to a whole of the same kind is of order one and can. The whole is
    the sum of the magnitudes when the part is a signed sum, so a sum that is
    zero in decimal, 0,3 - 0,1 - 0,2 W, and comes out a few units in the last
    place of its terms either side of zero in binary settles to zero, and a
    sum that is the half of a total in decimal settles to 0,5.

    :param part: The quantity judged, any shape.
    :param whole: What it is a share of, broadcastable with ``part``.
    :return: The settled ratio; zero where the whole is zero, since a part of
        nothing is nothing, and NaN where either is NaN, so that a NaN answers
        every comparison False as it did before it was settled.
    """
    numerator = np.asarray(part, dtype=np.float64)
    denominator = np.asarray(whole, dtype=np.float64)
    shape = np.broadcast_shapes(numerator.shape, denominator.shape)
    ratio = np.divide(
        numerator,
        denominator,
        out=np.zeros(shape, dtype=np.float64),
        where=np.isnan(numerator) | np.isnan(denominator) | (np.abs(denominator) > 0.0),
    )
    return settled(ratio)


def settled_net_share(terms: ArrayLike, axis: int | None = None) -> NDArray[np.float64]:
    """The signed sum of ``terms`` as a settled share of their magnitudes.

    The sign of an algebraic sum, a net sound power or a mean normal
    intensity, is what a standard judges against zero, and the sum of more
    than two decimal terms that cancel in decimal is a few units in the last
    place of its terms either side of zero in binary. Settled as a share of
    the sum of the magnitudes it is zero, and it is positive or negative only
    when the terms do not cancel to nine decimals of their own size.

    :param terms: The signed terms.
    :param axis: The axis summed over; ``None`` sums them all.
    :return: The settled share, in [-1, 1]; zero where every term is zero.
    """
    values = np.asarray(terms, dtype=np.float64)
    return settled_ratio(np.sum(values, axis=axis), np.sum(np.abs(values), axis=axis))


def round_half_up(value: ArrayLike, decimals: int = 0) -> NDArray[np.float64]:
    """Round to ``decimals`` places with halves upwards (2,5 to 3, -2,5 to -2).

    The scaled value is settled before the half is judged, so 20,4 - 14,9 dB,
    5,499 999 999 999 998 in binary, rounds to 6 as the 5,5 dB it is.

    :param value: The value or values to round.
    :param decimals: The decimal places kept.
    :return: The rounded values as a float array.
    """
    scale = 10.0**decimals
    scaled = settled(np.asarray(value, dtype=np.float64) * scale)
    return np.asarray(np.floor(scaled + 0.5) / scale, dtype=np.float64)


def round_half_away_from_zero(
    value: ArrayLike, decimals: int = 0
) -> NDArray[np.float64]:
    """Round to ``decimals`` places with halves away from zero (-2,5 to -3).

    :param value: The value or values to round.
    :param decimals: The decimal places kept.
    :return: The rounded values as a float array.
    """
    scale = 10.0**decimals
    scaled = settled(np.asarray(value, dtype=np.float64) * scale)
    return np.asarray(np.sign(scaled) * np.floor(np.abs(scaled) + 0.5) / scale)


def round_half_even(value: ArrayLike, decimals: int = 0) -> NDArray[np.float64]:
    """Round to ``decimals`` places with halves to the even neighbour.

    Rule A of ISO 80000-1:2009 Annex B: 2,5 to 2 and 3,5 to 4. The scaled
    value is settled before the half is judged, so 32,3 - 20,8 dB,
    11,499 999 999 999 996 in binary, rounds to 12 as the 11,5 dB it is.

    :param value: The value or values to round.
    :param decimals: The decimal places kept.
    :return: The rounded values as a float array.
    """
    scale = 10.0**decimals
    scaled = settled(np.asarray(value, dtype=np.float64) * scale)
    return np.asarray(np.rint(scaled) / scale, dtype=np.float64)
