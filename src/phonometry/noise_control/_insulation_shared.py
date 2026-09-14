#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What ISO 11546 and ISO 11957 print in the same words.

The two documents were drafted together and share more than a subject. Their
definitions of the leak ratio and the seal ratio are word for word the same,
they ask for the same band range in the same two sentences, and both hand their
single-number rating to ISO 717-1 with their own quantity written where that
standard writes :math:`R`. Writing any of that twice would let the two copies
drift, so it is written once here and imported by both public modules.

Nothing in this module is a quantity of its own: the public names it defines
are re-exported by :mod:`phonometry.noise_control.enclosure_insulation` and
:mod:`phonometry.noise_control.cabin_insulation`, which is where a reader looks
for them.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np

from .._internal.validation import require_choice, require_positive

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.typing import NDArray

    from .._internal.warnings import PhonometryWarning

__all__ = [
    "MANDATORY_BAND_RANGE_HZ",
    "PREFERRED_BAND_RANGE_HZ",
    "leak_ratio",
    "seal_ratio",
]

#: The band range both standards require, by band fraction: 100 Hz to 5 kHz in
#: one-third octaves, 125 Hz to 4 kHz in octaves. ISO 11546 states it in 6.2,
#: ISO 11957 in 6.4 and again in 7.4.
MANDATORY_BAND_RANGE_HZ: dict[int, tuple[float, float]] = {
    3: (100.0, 5000.0),
    1: (125.0, 4000.0),
}

#: The range both standards would rather have, by band fraction, from the note
#: that follows the requirement in each.
PREFERRED_BAND_RANGE_HZ: dict[int, tuple[float, float]] = {
    3: (50.0, 10000.0),
    1: (63.0, 8000.0),
}

#: The bands ISO 717-1 reads, by band fraction.
_RATING_BANDS: dict[int, tuple[float, ...]] = {
    3: (
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
    ),
    1: (125.0, 250.0, 500.0, 1000.0, 2000.0),
}

#: The band fraction of a one-third-octave spectrum.
_THIRD_OCTAVE = 3


def _band_fraction(value: int) -> int:
    """The band fraction, checked against the two the standards allow."""
    return int(require_choice(str(value), "band_fraction", ("1", "3")))


def _check_band_range(
    frequencies: NDArray[np.float64] | None,
    band_fraction: int,
    *,
    standard: str,
    category: type[PhonometryWarning],
    stacklevel: int = 4,
) -> None:
    """Warn when the bands given do not cover what the standard requires."""
    if frequencies is None or frequencies.size == 0:
        return
    low, high = MANDATORY_BAND_RANGE_HZ[band_fraction]
    lowest = float(np.min(frequencies))
    highest = float(np.max(frequencies))
    if lowest > low or highest < high:
        msg = (
            f"{standard} requires the bands from {low:g} Hz to {high:g} Hz; the "
            f"spectrum runs from {lowest:g} Hz to {highest:g} Hz."
        )
        warnings.warn(msg, category, stacklevel=stacklevel)


def _rating_bands(band_fraction: int) -> tuple[NDArray[np.float64], str]:
    """The ISO 717-1 rating bands and the name the rating machinery knows them by."""
    bands = np.asarray(_RATING_BANDS[band_fraction], dtype=np.float64)
    name = "third-octave" if band_fraction == _THIRD_OCTAVE else "octave"
    return bands, name


def _require_rating_bands(
    values: NDArray[np.float64], bands: NDArray[np.float64]
) -> None:
    """Refuse a spectrum that is not the rating bands themselves."""
    if values.size != bands.size:
        msg = (
            f"The ISO 717-1 rating reads {bands.size} bands "
            f"({bands[0]:g} Hz to {bands[-1]:g} Hz); got {values.size} values. "
            "Trim the spectrum to those bands before rating it."
        )
        raise ValueError(msg)


def leak_ratio(opening_area_m2: float, interior_surface_area_m2: float) -> float:
    r"""How open an enclosure or a cabin is.

    :math:`\theta = S_O / S_E`, the area of the openings over the area of the
    interior surface: definition 3.16 of ISO 11546-1, 3.14 of ISO 11546-2 and
    3.14 of ISO 11957, in the same words in all three. What they do with it
    differs: clause 4 of ISO 11546 only prefers a value under 2 %, while clause
    1 of ISO 11957 makes the same 2 % a condition of applicability.

    An opening fitted with an effective silencer does not count as one.

    :param opening_area_m2: The total area of the openings, in square metres.
    :param interior_surface_area_m2: The interior surface area, openings
        included, in square metres.
    :return: The ratio, dimensionless.
    :raises ValueError: For a non-positive area.
    """
    openings = require_positive(opening_area_m2, "opening_area_m2")
    interior = require_positive(interior_surface_area_m2, "interior_surface_area_m2")
    return openings / interior


def seal_ratio(leak: float) -> float:
    r"""The reciprocal of the leak ratio.

    :math:`\psi = 1/\theta`, from NOTE 5 to definition 3.16 of ISO 11546-1 and
    NOTE 3 to definition 3.14 of ISO 11957. Both print the two because a
    catalogue quotes whichever reads better.

    :param leak: The leak ratio :math:`\theta`, dimensionless and positive.
    :return: :math:`\psi`, dimensionless.
    :raises ValueError: For a non-positive ratio.
    """
    return 1.0 / require_positive(leak, "leak")
