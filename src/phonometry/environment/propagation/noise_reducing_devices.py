#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Single-number ratings of noise reducing devices (EN 1793, EN 16272).

A barrier beside a road is not judged band by band. It is judged by single
numbers, and each is the same operation on a spectrum nobody measures on
site: the normalised traffic noise spectrum of **EN 1793-3:1997**, eighteen
one-third octave bands from 100 Hz to 5 kHz carrying relative A-weighted
levels :math:`L_i` that stand for what a road sounds like at the roadside.

A barrier beside a railway is judged the same way and by a different
spectrum. **EN 16272-3-1:2012** prints the normalised railway noise spectrum
over the same eighteen bands, and its Clauses 5 and 6 are the two formulas
below with that table in place of the other one: rolling noise puts its
weight higher up, so the railway spectrum is flat within one decibel from
1,25 kHz to 2,5 kHz where the road one has already begun to fall away.
The railway parts carry no category ladder; their annexes are guidance
notes, and a rating there is the number and nothing more.

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

* **EN 1793-5:2016** rates the sound reflection measured in place, the
  index :math:`RI` of
  :mod:`~phonometry.environment.propagation.barrier_reflection`, on the same
  spectrum but from the lowest band the size of the sample makes reliable
  (Clause 5.8, Formula (12)):

  .. math::

     DL_{RI} = -10 \lg\left[
     \frac{\sum_{i=m}^{18} RI_i\, 10^{0.1 L_i}}
          {\sum_{i=m}^{18} 10^{0.1 L_i}} \right]

  The clause copies the 0,99 limit on the ratio from EN 1793-1, so a device
  reflecting more than it receives in the weighted sum rates 0,04 dB.

All three are reported rounded to the nearest integer (EN 1793-1 Clause 6.1,
EN 1793-2 Clause 7.1, EN 1793-5 Clause 5.11). The first two have a normative
category ladder in their Annex A: A1 to A5 for absorption, B1 to B4 for
insulation, with A0 and B0 reserved for "not determined". The categories are
read off the reported integer, which is why the ladders have no gaps between
their steps. EN 1793-5 prints no ladder.

Absorption and insulation answer different questions and are not
comparable. A device can be a perfect reflector and still keep the noise out
(high :math:`DL_R`, low :math:`DL_\alpha`); a device can be highly absorptive
and let sound through (the other way round). The declaration carries both.
:math:`DL_{RI}` answers the first question again, in the direct sound field
beside the road rather than the diffuse field of a reverberation room, so it
does not convert into :math:`DL_\alpha` either.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import OwnsArrays
from ..._internal.validation import require_finite_array, require_positive

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

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

#: EN 16272-3-1:2012, Table 1. The normalised railway noise spectrum, over
#: the same eighteen bands as the road one: relative A-weighted one-third
#: octave band levels, in dB, flat within a decibel from 1,25 kHz to 2,5 kHz.
NORMALISED_RAILWAY_NOISE_SPECTRUM_DB: tuple[float, ...] = (
    -27.0,
    -25.0,
    -23.0,
    -21.0,
    -19.0,
    -17.0,
    -15.0,
    -13.0,
    -12.0,
    -11.0,
    -10.0,
    -9.0,
    -9.0,
    -9.0,
    -9.0,
    -10.0,
    -13.0,
    -17.0,
)

#: The two spectra a device can be rated against, by the standard that
#: prints each: ``"road"`` is EN 1793-3 and ``"railway"`` is EN 16272-3-1.
SPECTRA: Mapping[str, tuple[float, ...]] = MappingProxyType(
    {
        "road": NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB,
        "railway": NORMALISED_RAILWAY_NOISE_SPECTRUM_DB,
    }
)

#: EN 1793-1:2012, Clause 5 and EN 16272-3-1:2012, Clause 5. The ceiling both
#: standards put on the weighted absorption ratio, so that a measured
#: coefficient above one cannot leave the logarithm without an argument.
ABSORPTION_RATIO_LIMIT = 0.99

#: Slack on the 0,99 limit of the weighted ratio, so a ratio that is 0,99 in
#: decimal is on the limit whichever way the last bits of the weighted mean
#: fall. EN 1793-1 Clause 5 and EN 16272-3-1 Clause 5 limit a ratio that
#: reaches 0,99, so the slack widens that inclusive bound downwards: absorption
#: coefficients that weigh to 0,99 in decimal can come out
#: 0,989 999 999 999 999 8 in binary. EN 1793-5 Clause 5.8 limits a ratio that exceeds 0,99, so
#: there it lifts the bound: every index read as 0,99 from 500 Hz weighs to two
#: units in the last place above 0,99. A millionth of a millionth is far below
#: the two decimals a coefficient or an index is reported to.
_RATIO_SLACK = 1e-12

#: How far, as a natural logarithm, a requested band may sit from a printed
#: centre and still name it: a hundredth, well inside the third of an
#: octave (0,23) that separates two centres.
_BAND_MATCH = 0.01

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
class RoadDeviceRating(OwnsArrays):
    """One single-number rating of a road traffic noise reducing device.

    :ivar rating: The rating before rounding, in dB. ``DLα`` (EN 1793-1),
        ``DL_R`` (EN 1793-2) or ``DL_RI`` (EN 1793-5), depending on
        ``quantity``.
    :ivar reported: The same rating rounded to the nearest integer, which is
        what a test report carries and what the category is read off.
    :ivar category: The Annex A category of the reported value, ``"A1"`` to
        ``"A5"`` for absorption or ``"B1"`` to ``"B4"`` for insulation, or
        ``None`` for a railway rating and for reflection, whose standards
        print no ladder.
    :ivar quantity: ``"absorption"``, ``"insulation"`` or ``"reflection"``.
    :ivar spectrum: ``"road"`` (EN 1793-3) or ``"railway"`` (EN 16272-3-1).
    :ivar bands_hz: The eighteen band centre frequencies, in Hz.
    :ivar values: The per-band input the rating was weighted from: the sound
        absorption coefficients, the sound reduction indices in dB, or the
        sound reflection indices (``nan`` allowed below ``lowest_band_hz``).
    :ivar weights: The normalised traffic noise spectrum, in dB.
    :ivar lowest_band_hz: The lowest band the rating sums from: 100 Hz for
        ``DLα`` and ``DL_R``, which sum all eighteen, and the lowest reliable
        band :math:`m` for ``DL_RI``.
    """

    rating: float
    reported: int
    category: str | None
    quantity: str
    spectrum: str
    bands_hz: NDArray[np.float64]
    values: NDArray[np.float64]
    weights: NDArray[np.float64]
    lowest_band_hz: float = TRAFFIC_NOISE_BANDS_HZ[0]

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
    values: ArrayLike, name: str, spectrum: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The band values and the spectrum weights, checked against each other."""
    if spectrum not in SPECTRA:
        msg = f"spectrum must be one of {tuple(SPECTRA)}; got {spectrum!r}"
        raise ValueError(msg)
    band_values = require_finite_array(values, name)
    if band_values.size != len(TRAFFIC_NOISE_BANDS_HZ):
        msg = (
            f"{name} must cover the {len(TRAFFIC_NOISE_BANDS_HZ)} one-third "
            f"octave bands from 100 Hz to 5 kHz; got {band_values.size}"
        )
        raise ValueError(msg)
    return band_values, np.asarray(SPECTRA[spectrum], dtype=float)


def _category(reported: int, ladder: tuple[tuple[str, int, int], ...]) -> str:
    """The Annex A category the reported integer falls in."""
    for name, low, high in ladder:
        if low <= reported <= high:
            return name
    msg = f"no category covers {reported} dB"  # pragma: no cover - ladders are total
    raise ValueError(msg)


def sound_absorption_rating(
    absorption_coefficients: ArrayLike, *, spectrum: str = "road"
) -> RoadDeviceRating:
    r"""``DLα``, the single-number rating of sound absorption.

    EN 1793-1:2012 Clause 5 for a road device, EN 16272-3-1:2012 Clause 5
    for a railway one: the same formula over the same eighteen bands, with
    the spectrum of the matching part in the weights. Only the road parts
    print a category ladder, so a railway rating carries none.

    :param absorption_coefficients: :math:`\alpha_\mathrm{S}` in the
        eighteen one-third octave bands of :data:`TRAFFIC_NOISE_BANDS_HZ`.
    :param spectrum: ``"road"`` (EN 1793-3, the default) or ``"railway"``
        (EN 16272-3-1).
    :return: The rating, its reported integer and, for a road device, its
        Annex A category.
    :raises ValueError: If the input does not cover the eighteen bands, is
        not finite, or the spectrum is not one of the two.
    :warns RoadDeviceWarning: If the weighted ratio reaches the 0,99 limit
        both standards put on it, which means the rating is the limit and
        not the data.
    """
    alpha, weights = _weighted(
        absorption_coefficients, "absorption_coefficients", spectrum
    )
    energy = 10.0 ** (0.1 * weights)
    ratio = float(np.sum(alpha * energy) / np.sum(energy))
    if ratio >= ABSORPTION_RATIO_LIMIT - _RATIO_SLACK:
        clause = "EN 1793-1" if spectrum == "road" else "EN 16272-3-1"
        msg = (
            "the weighted absorption ratio reached the "
            f"{ABSORPTION_RATIO_LIMIT} limit of {clause} Clause 5, so the "
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
        category=(
            _category(reported, ABSORPTION_CATEGORIES) if spectrum == "road" else None
        ),
        quantity="absorption",
        spectrum=spectrum,
        bands_hz=np.asarray(TRAFFIC_NOISE_BANDS_HZ, dtype=float),
        values=alpha,
        weights=weights,
    )


def airborne_insulation_rating(
    sound_reduction_index_db: ArrayLike, *, spectrum: str = "road"
) -> RoadDeviceRating:
    r"""``DL_R``, the single-number rating of airborne sound insulation.

    EN 1793-2:2012 Clause 5.2 for a road device, EN 16272-3-1:2012 Clause 6
    for a railway one, on the same weighting as the absorption rating above.

    :param sound_reduction_index_db: :math:`R` in decibels, in the eighteen
        one-third octave bands of :data:`TRAFFIC_NOISE_BANDS_HZ`.
    :param spectrum: ``"road"`` (EN 1793-3, the default) or ``"railway"``
        (EN 16272-3-1).
    :return: The rating, its reported integer and, for a road device, its
        Annex A category.
    :raises ValueError: If the input does not cover the eighteen bands, is
        not finite, or the spectrum is not one of the two.
    """
    reduction, weights = _weighted(
        sound_reduction_index_db, "sound_reduction_index_db", spectrum
    )
    energy = 10.0 ** (0.1 * weights)
    transmitted = float(np.sum(energy * 10.0 ** (-0.1 * reduction)) / np.sum(energy))
    rating = -10.0 * float(np.log10(abs(transmitted)))
    reported = _round_half_up(rating)
    return RoadDeviceRating(
        rating=rating,
        reported=reported,
        category=(
            _category(reported, INSULATION_CATEGORIES) if spectrum == "road" else None
        ),
        quantity="insulation",
        spectrum=spectrum,
        bands_hz=np.asarray(TRAFFIC_NOISE_BANDS_HZ, dtype=float),
        values=reduction,
        weights=weights,
    )


def sound_reflection_rating(
    reflection_indices: ArrayLike, *, lowest_band_hz: float = 200.0
) -> RoadDeviceRating:
    r"""``DL_RI``, the single-number rating of sound reflection.

    EN 1793-5:2016 Clause 5.8, Formula (12): the sound reflection index
    weighted by the normalised traffic noise spectrum of EN 1793-3, summed
    from the lowest reliable band :math:`m` to 5 kHz. For the qualification
    sample of 4 m by 4 m that band is 200 Hz (5.5.7), the default; a smaller
    device starts higher and the report names the range, for example
    ``DL_RI (400 - 5 000 Hz)`` for a 3,5 m barrier. Annex B's example rates
    7,68 dB before rounding on the two-decimal averages of Table B.1
    (7,65 dB on its particular values), reported as 8 dB. EN 1793-5 prints no
    category ladder.

    :param reflection_indices: :math:`RI` in the eighteen one-third octave
        bands of :data:`TRAFFIC_NOISE_BANDS_HZ`; a band below
        ``lowest_band_hz`` may be ``nan``.
    :param lowest_band_hz: The centre of the lowest reliable band, one of the
        eighteen.
    :return: The rating and its reported integer, category ``None``.
    :raises ValueError: If there are not eighteen values, a band from
        ``lowest_band_hz`` up is not a finite non-negative number, the band is
        not positive or not one of the eighteen, or the weighted ratio is
        zero.
    :warns RoadDeviceWarning: If the weighted ratio exceeds the maximum of
        0,99 Clause 5.8 limits it to; a ratio of 0,99 itself is not limited.
    """
    values = np.atleast_1d(np.asarray(reflection_indices, dtype=float))
    bands = np.asarray(TRAFFIC_NOISE_BANDS_HZ, dtype=float)
    if values.ndim != 1 or values.size != bands.size:
        msg = (
            f"reflection_indices must cover the {bands.size} one-third octave "
            f"bands from 100 Hz to 5 kHz; got {values.size}"
        )
        raise ValueError(msg)
    lowest = require_positive(lowest_band_hz, "lowest_band_hz")
    first = int(np.argmin(np.abs(np.log(bands / lowest))))
    if abs(math.log(bands[first] / lowest)) > _BAND_MATCH:
        msg = (
            f"lowest_band_hz must be one of the band centres {TRAFFIC_NOISE_BANDS_HZ}; "
            f"got {lowest_band_hz!r}"
        )
        raise ValueError(msg)
    used = values[first:]
    if not np.all(np.isfinite(used)) or np.any(used < 0.0):
        msg = (
            f"reflection_indices must be finite and non-negative from the "
            f"{bands[first]:g} Hz band upward"
        )
        raise ValueError(msg)
    weights = np.asarray(SPECTRA["road"], dtype=float)
    energy = 10.0 ** (0.1 * weights[first:])
    ratio = float(np.sum(used * energy) / np.sum(energy))
    if ratio > ABSORPTION_RATIO_LIMIT + _RATIO_SLACK:
        msg = (
            "the weighted reflection ratio exceeded the "
            f"{ABSORPTION_RATIO_LIMIT} limit of EN 1793-5 Clause 5.8, so the "
            f"rating is that limit rather than the measurement; the ratio was "
            f"{ratio!r}"
        )
        warnings.warn(msg, RoadDeviceWarning, stacklevel=2)
        ratio = ABSORPTION_RATIO_LIMIT
    if ratio <= 0.0:
        msg = "the weighted reflection ratio is zero, so DL_RI has no finite value"
        raise ValueError(msg)
    rating = -10.0 * math.log10(ratio)
    return RoadDeviceRating(
        rating=rating,
        reported=_round_half_up(rating),
        category=None,
        quantity="reflection",
        spectrum="road",
        bands_hz=bands,
        values=values,
        weights=weights,
        lowest_band_hz=float(bands[first]),
    )
