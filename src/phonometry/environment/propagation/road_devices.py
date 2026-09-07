#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Single-number ratings of road traffic noise reducing devices (EN 1793).

A barrier beside a road is not judged band by band. It is judged by two
numbers, and both are the same operation on a spectrum nobody measures on
site: the normalised traffic noise spectrum of **EN 1793-3:1997**, eighteen
one-third octave bands from 100 Hz to 5 kHz carrying relative A-weighted
levels :math:`L_i` that stand for what a road sounds like at the roadside.

* **EN 1793-1:2012** rates absorption. What matters to the neighbour is the
  energy the device sends back across the road, so the rating is what is
  *not* absorbed, in decibels (Clause 5):

  .. math::

     DL_\alpha = -10 \lg\left| 1 -
     \frac{\sum_{i=1}^{18} \alpha_{\mathrm{S}i}\, 10^{0.1 L_i}}
          {\sum_{i=1}^{18} 10^{0.1 L_i}} \right|

  A measured :math:`\alpha_\mathrm{S}` can exceed one band by band, which
  can push the weighted ratio past 1 and leave the logarithm without an
  argument. The clause says so and fixes it: the ratio is limited to 0,99.

* **EN 1793-2:2012** rates airborne insulation with the same weighting
  (Clause 5.2), on the transmitted energy rather than the absorbed:

  .. math::

     DL_R = -10 \lg\left|
     \frac{\sum_{i=1}^{18} 10^{0.1 L_i}\, 10^{-0.1 R_i}}
          {\sum_{i=1}^{18} 10^{0.1 L_i}} \right|

Both are reported rounded to the nearest integer (EN 1793-1 Clause 6.1,
EN 1793-2 Clause 7.1), and both have a normative category ladder in their
Annex A: A1 to A5 for absorption, B1 to B4 for insulation, with A0 and B0
reserved for "not determined". The categories are read off the reported
integer, which is why the ladders have no gaps between their steps.

The two ratings answer different questions and are not comparable. A device
can be a perfect reflector and still keep the noise out (high :math:`DL_R`,
low :math:`DL_\alpha`); a device can be highly absorptive and let sound
through (the other way round). The declaration carries both.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import require_finite_array

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: EN 1793-3:1997, Table 1. The eighteen one-third octave bands the
#: normalised traffic noise spectrum is printed for, in Hz.
TRAFFIC_NOISE_BANDS_HZ: tuple[float, ...] = (
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
)

#: EN 1793-3:1997, Table 1. The normalised traffic noise spectrum itself:
#: relative A-weighted one-third octave band levels, in dB, peaking at
#: 1 kHz and falling by twelve decibels at either end of the range.
NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB: tuple[float, ...] = (
    -20.0,
    -20.0,
    -18.0,
    -16.0,
    -15.0,
    -14.0,
    -13.0,
    -12.0,
    -11.0,
    -9.0,
    -8.0,
    -9.0,
    -10.0,
    -11.0,
    -13.0,
    -15.0,
    -16.0,
    -18.0,
)

#: EN 1793-1:2012, Clause 5. The ceiling the standard puts on the weighted
#: absorption ratio, so that a measured coefficient above one cannot leave
#: the logarithm without an argument.
ABSORPTION_RATIO_LIMIT = 0.99

#: EN 1793-1:2012, Table A.1. Categories of absorptive performance, read
#: off the reported integer: each pair is the inclusive range of that
#: category, open at either end for A1 and A5.
ABSORPTION_CATEGORIES: tuple[tuple[str, int, int], ...] = (
    ("A1", -(2**31), 3),
    ("A2", 4, 7),
    ("A3", 8, 11),
    ("A4", 12, 15),
    ("A5", 16, 2**31),
)

#: EN 1793-2:2012, Table A.1. Categories of airborne sound insulation, on
#: the same reading.
INSULATION_CATEGORIES: tuple[tuple[str, int, int], ...] = (
    ("B1", -(2**31), 14),
    ("B2", 15, 24),
    ("B3", 25, 34),
    ("B4", 35, 2**31),
)


class RoadDeviceWarning(UserWarning):
    """Raised when a rating is computed on data the standard bounds."""


@dataclass(frozen=True)
class RoadDeviceRating:
    """One single-number rating of a road traffic noise reducing device.

    :ivar rating: The rating before rounding, in dB. ``DLα`` (EN 1793-1) or
        ``DL_R`` (EN 1793-2), depending on ``quantity``.
    :ivar reported: The same rating rounded to the nearest integer, which is
        what a test report carries and what the category is read off.
    :ivar category: The Annex A category of the reported value, ``"A1"`` to
        ``"A5"`` for absorption or ``"B1"`` to ``"B4"`` for insulation.
    :ivar quantity: ``"absorption"`` or ``"insulation"``.
    :ivar bands_hz: The eighteen band centre frequencies, in Hz.
    :ivar values: The per-band input the rating was weighted from: the sound
        absorption coefficients, or the sound reduction indices in dB.
    :ivar weights: The normalised traffic noise spectrum, in dB.
    """

    rating: float
    reported: int
    category: str
    quantity: str
    bands_hz: NDArray[np.float64]
    values: NDArray[np.float64]
    weights: NDArray[np.float64]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the per-band input against the spectrum that weights it.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_road_device_rating

        return plot_road_device_rating(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _round_half_up(value: float) -> int:
    """Round to an integer, halves upward.

    Both parts say only "rounded to the nearest integer", which leaves the
    half undecided; the family it belongs to (ISO 717-2:2020 Annex D) reads
    the half upward, and so does this.
    """
    return int(np.floor(value + 0.5))


def _weighted(
    values: ArrayLike, name: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The band values and the spectrum weights, checked against each other."""
    band_values = require_finite_array(values, name)
    if band_values.size != len(TRAFFIC_NOISE_BANDS_HZ):
        msg = (
            f"{name} must cover the {len(TRAFFIC_NOISE_BANDS_HZ)} one-third "
            f"octave bands of EN 1793-3 from 100 Hz to 5 kHz; got "
            f"{band_values.size}"
        )
        raise ValueError(msg)
    return band_values, np.asarray(NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB, dtype=float)


def _category(reported: int, ladder: tuple[tuple[str, int, int], ...]) -> str:
    """The Annex A category the reported integer falls in."""
    for name, low, high in ladder:
        if low <= reported <= high:
            return name
    msg = f"no category covers {reported} dB"  # pragma: no cover - ladders are total
    raise ValueError(msg)


def sound_absorption_rating(absorption_coefficients: ArrayLike) -> RoadDeviceRating:
    r"""``DLα``, the EN 1793-1 single-number rating of sound absorption.

    :param absorption_coefficients: :math:`\alpha_\mathrm{S}` in the
        eighteen one-third octave bands of :data:`TRAFFIC_NOISE_BANDS_HZ`.
    :return: The rating, its reported integer and its Annex A category.
    :raises ValueError: If the input does not cover the eighteen bands, or
        is not finite.
    :warns RoadDeviceWarning: If the weighted ratio reaches the 0,99 limit
        of Clause 5, which means the rating is the limit and not the data.
    """
    alpha, weights = _weighted(absorption_coefficients, "absorption_coefficients")
    energy = 10.0 ** (0.1 * weights)
    ratio = float(np.sum(alpha * energy) / np.sum(energy))
    if ratio >= ABSORPTION_RATIO_LIMIT:
        msg = (
            "the weighted absorption ratio reached the "
            f"{ABSORPTION_RATIO_LIMIT} limit of EN 1793-1 Clause 5, so the "
            f"rating is that limit rather than the measurement; the ratio "
            f"was {ratio!r}"
        )
        warnings.warn(msg, RoadDeviceWarning, stacklevel=2)
        ratio = ABSORPTION_RATIO_LIMIT
    rating = -10.0 * float(np.log10(abs(1.0 - ratio)))
    reported = _round_half_up(rating)
    return RoadDeviceRating(
        rating=rating,
        reported=reported,
        category=_category(reported, ABSORPTION_CATEGORIES),
        quantity="absorption",
        bands_hz=np.asarray(TRAFFIC_NOISE_BANDS_HZ, dtype=float),
        values=alpha,
        weights=weights,
    )


def airborne_insulation_rating(sound_reduction_index_db: ArrayLike) -> RoadDeviceRating:
    r"""``DL_R``, the EN 1793-2 single-number rating of airborne insulation.

    :param sound_reduction_index_db: :math:`R` in decibels, in the eighteen
        one-third octave bands of :data:`TRAFFIC_NOISE_BANDS_HZ`.
    :return: The rating, its reported integer and its Annex A category.
    :raises ValueError: If the input does not cover the eighteen bands, or
        is not finite.
    """
    reduction, weights = _weighted(sound_reduction_index_db, "sound_reduction_index_db")
    energy = 10.0 ** (0.1 * weights)
    transmitted = float(np.sum(energy * 10.0 ** (-0.1 * reduction)) / np.sum(energy))
    rating = -10.0 * float(np.log10(abs(transmitted)))
    reported = _round_half_up(rating)
    return RoadDeviceRating(
        rating=rating,
        reported=reported,
        category=_category(reported, INSULATION_CATEGORIES),
        quantity="insulation",
        bands_hz=np.asarray(TRAFFIC_NOISE_BANDS_HZ, dtype=float),
        values=reduction,
        weights=weights,
    )
