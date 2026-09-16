#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Spatial sound distribution curves in workrooms (ISO 14257:2001).

A workroom is not a reverberation room and it is not a free field. Put a known
source in it, walk away from it with a meter, and the level falls off somewhere
between the 6 dB per distance doubling of a free field and the nothing at all
of a perfectly diffuse room. That curve is what this standard measures, and the
two numbers it derives from it are what a room is judged by:

* :math:`\mathrm{DL}_2`, the **rate of spatial decay per distance doubling**,
  which says how much quieter it gets by walking away, and
* :math:`\mathrm{DL}_\mathrm{f}`, the **excess of sound pressure level**, which
  says how much louder the room is than a free field would have been.

The quantity everything is built on is the sound distribution value, the level
at a point less the sound power level of the source that produced it, so that
the curve belongs to the room and not to the source:

.. math::

   D_j(r) = L_{pj}(r) - L_{Wj} \tag{1}

The reference curve is the same quantity in a free field, which is the inverse
square law written as a level:

.. math::

   D_\mathrm{ref}(r) = 10 \lg \frac{r_0^2}{4 \pi r^2}
                     = 20 \lg \frac{r_0}{r} - 11 \tag{2}

with :math:`r_0` = 1 m. The two derived quantities are a least-squares slope
over a range of positions,

.. math::

   \mathrm{DL}_2 = -0,3 \,
   \frac{z \sum D_i \lg(r_i/r_0) - \sum D_i \sum \lg(r_i/r_0)}
        {z \sum [\lg(r_i/r_0)]^2 - [\sum \lg(r_i/r_0)]^2} \tag{5}

with :math:`z = m - n + 1`, and the difference from the reference curve,

.. math::

   \mathrm{DL}_\mathrm{f} = D - D_\mathrm{ref} \tag{6}

averaged over a distance range by Equation (7) or read off the regression line
at one conventional distance by Equation (8).

**The 0,3 of Equation (5).** The slope of a least-squares fit of :math:`D`
against :math:`\lg r` is a rate per decade; a doubling is :math:`\lg 2` of a
decade, which is 0,301 03. The clause prints 0,3, and that is what
:data:`DECADE_TO_DOUBLING` carries, because the printed constant is what
reproduces the printed results. Equation (8) prints :math:`\lg 2` in full a page
later, so the two are not the same number in the same document; the difference
is 0,3 % of a slope and the errata registry records it.

**Two spectra.** A curve measured in octave bands can be collapsed onto the
spectrum of a real machine by Equation (3), or onto the A-weighted pink noise of
Table 1 by Equation (4), which is what a room gets judged by when nobody knows
yet what will be installed in it.

**The 6,2 of Equation (4).** The constant is the energy sum of the
A-weighting curve over the six octaves, 6,23 dB, printed to one decimal, and it
is there so that a flat curve comes back unchanged. Table 1 prints the same
curve to one decimal weight by weight, and the six printed weights sum to
6,251 5 dB, so the printed equation returns a flat curve 0,05 dB high.
:data:`NORMALIZED_OFFSET_DB` carries the printed 6,2 on the same rule as the
0,3 above: four printings print it and a reader checking against the page will
use it. Annex C was normalised exactly: its normalized column and its
Table C.10 land inside the printed rounding under Equation (3) with the Table 1
weights and one unit high in the last place under the printed constant, so
every value this module normalizes stands 0,05 dB above the annex. The errata
registry records it. Equation (3) with the Table 1 weights as the machine
spectrum is Equation (4) normalised exactly, for whoever needs the annex's
reading.

**Annex B.** In a room whose own excess is small, what the measurement sees is
partly the source's own directivity and the reflection off the floor rather than
the room. The annex corrects for that with a reference curve measured for that
source in a free field over a reflecting plane, Equation (B.1), against the
theoretical floor-reflected curve of Equations (B.2) to (B.4).

Read from BS EN ISO 14257:2001, which endorses ISO 14257:2001 without
modification.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.validation import (
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ADJACENT_BAND_LIMIT_DB",
    "DECADE_TO_DOUBLING",
    "EVALUATION_DISTANCES_M",
    "FREE_FIELD_OFFSET_DB",
    "ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB",
    "ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB",
    "ISO14257_REFERENCE_DISTANCE_M",
    "MAX_DIRECTIVITY_INDEX_DB",
    "MIN_SOURCE_TO_WALL_M",
    "NEAR_REGION_START_M",
    "NORMALIZED_OFFSET_DB",
    "OMNIDIRECTIONAL_RAMP_HZ",
    "OMNIDIRECTIONAL_TOLERANCE_DB",
    "PINK_NOISE_WEIGHTS_DB",
    "PREFERRED_MIDDLE_LIMIT_M",
    "SOURCE_ON_FLOOR_HEIGHT_M",
    "SPATIAL_DECAY_BANDS_HZ",
    "STABILITY_TOLERANCE_DB",
    "TYPICAL_FAR_LIMIT_M",
    "TYPICAL_NEAR_LIMIT_M",
    "BackgroundMarginCheck",
    "SpatialDecayResult",
    "SpatialDecayWarning",
    "check_background_margin",
    "corrected_distribution_value",
    "distance_region",
    "floor_reference_value",
    "level_excess",
    "level_excess_at",
    "mean_level_excess",
    "normalized_distribution_value",
    "omnidirectionality_tolerance_db",
    "reference_distribution_value",
    "sound_distribution_value",
    "spatial_decay_curve",
    "spatial_decay_rate",
    "spectrum_distribution_value",
]


class SpatialDecayWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 14257 states."""


#: 4.2.1: the reference distance of Equation (2), in metres.
ISO14257_REFERENCE_DISTANCE_M: float = 1.0

#: 4.2.1: the 11 dB Equation (2) prints for ``10 lg(4 pi)``, which is 10,99.
FREE_FIELD_OFFSET_DB: float = 11.0

#: 6.3: the factor Equation (5) prints in front of the least-squares slope. A
#: slope against ``lg r`` is a rate per decade and a doubling is ``lg 2`` of
#: one, which is 0,301 03; the clause prints 0,3 and that is what is used, so
#: that the results are the printed ones. Equation (8) prints ``lg 2`` itself
#: (see the errata).
DECADE_TO_DOUBLING: float = 0.3

#: Table 1: the A-weighted pink-noise spectrum of 4.2.3, in decibels, by
#: nominal octave centre frequency in hertz.
PINK_NOISE_WEIGHTS_DB: dict[float, float] = {
    125.0: -16.1,
    250.0: -8.6,
    500.0: -3.2,
    1000.0: 0.0,
    2000.0: 1.2,
    4000.0: 1.0,
}

#: The six octave bands Table 1 covers, in hertz.
SPATIAL_DECAY_BANDS_HZ: tuple[float, ...] = tuple(PINK_NOISE_WEIGHTS_DB)

#: 4.2.3: the constant Equation (4) takes off the energy sum, in decibels. It
#: is the energy sum of the A-weighting curve over the six octaves, 6,23 dB,
#: printed to one decimal; the six weights Table 1 prints, rounded on their
#: own, sum to 6,251 5 dB, so the printed equation returns a flat curve
#: 0,05 dB high. Kept as printed, like the 11 of Equation (2) and the 0,3 of
#: Equation (5): a result is what the printed equation gives. Annex C was
#: normalised exactly, which leaves every printed normalized value 0,05 dB
#: below what this constant returns (see the errata);
#: :func:`spectrum_distribution_value` with the Table 1 weights is Equation (4)
#: normalised exactly.
NORMALIZED_OFFSET_DB: float = 6.2

#: 6.2: the near region starts here, in metres.
NEAR_REGION_START_M: float = 1.0

#: 6.2: the typical boundaries between the near, middle and far regions, in
#: metres. Other values may be used and are then reported.
TYPICAL_NEAR_LIMIT_M: float = 5.0
TYPICAL_FAR_LIMIT_M: float = 16.0

#: 6.2: how far into the middle region the clause would rather reach, in
#: metres.
PREFERRED_MIDDLE_LIMIT_M: float = 24.0

#: 6.4.3: the conventional distance each region is read at, in metres.
EVALUATION_DISTANCES_M: dict[str, float] = {
    "near": 4.0,
    "middle": 10.0,
    "far": 30.0,
}

#: 5.1.3: the acoustical centre stands at least this far from any wall or
#: reflecting object other than the floor, in metres.
MIN_SOURCE_TO_WALL_M: float = 3.0

#: 5.1.3: a source counts as close to the floor at or below this height, in
#: metres.
SOURCE_ON_FLOOR_HEIGHT_M: float = 0.5

#: 5.1.4: the source shall be this far over the background in every band and
#: at every distance, in decibels; between this and
#: :data:`ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB` an ISO 3744 correction is made, and
#: below it the point is not measured.
ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB: float = 10.0
ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB: float = 6.0

#: A.1: the largest absolute directivity index the source may show in any
#: one-third-octave band from 100 Hz to 5 kHz, in decibels.
MAX_DIRECTIVITY_INDEX_DB: float = 8.0

#: A.1: the band of uniform omnidirectional radiation, in decibels, at the two
#: ends of the ramp, and the one-third-octave centres the ramp runs between,
#: in hertz. Below the first the tolerance is the lower value and above the
#: second it is the upper one.
OMNIDIRECTIONAL_TOLERANCE_DB: tuple[float, float] = (2.0, 8.0)
OMNIDIRECTIONAL_RAMP_HZ: tuple[float, float] = (630.0, 1000.0)

#: A.2: the largest step allowed between adjacent one-third-octave bands of the
#: source's sound power, in decibels.
ADJACENT_BAND_LIMIT_DB: float = 8.0

#: A.1: the nominal one-third-octave centres of the range the source is
#: qualified over, in hertz.
_THIRD_OCTAVE_CENTRES_HZ: tuple[float, ...] = (
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

#: The regions clause 6.2 names, plus the whole path as one.
_REGIONS: tuple[str, ...] = ("near", "middle", "far", "whole")

#: The fewest positions a regression or a trapezoidal mean can be taken over.
_MIN_REGRESSION_POINTS = 2

#: Every curve of clause 6 is read position by position, so a value without a
#: distance is a curve with a hole in it rather than a shorter curve.
_MISMATCH_MSG = (
    "'distribution_values_db' and 'distances_m' must match position for position."
)

#: A.4: the repeatability tolerance on the source's sound power, in decibels,
#: keyed by the one-third-octave range it applies to, in hertz.
STABILITY_TOLERANCE_DB: dict[tuple[float, float], float] = {
    (100.0, 160.0): 1.0,
    (200.0, 5000.0): 0.5,
}


@dataclass(frozen=True)
class BackgroundMarginCheck:
    """Whether the levels clear the background by what 5.1.4 asks.

    :param margins_db: The level of the source less the background at each
        position and band given, in decibels, in the shape they came in.
    :param needs_correction: True where the margin is under
        :data:`ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB` and over
        :data:`ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB`, which is the window where the
        clause asks for the ISO 3744 background correction.
    :param unusable: True where the margin is at or under
        :data:`ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB`, which the clause offers no
        correction for.
    :param satisfied: True when every margin clears
        :data:`ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB`, which is the only case that needs
        nothing done to it.
    """

    margins_db: NDArray[np.float64]
    needs_correction: NDArray[np.bool_]
    unusable: NDArray[np.bool_]
    satisfied: bool


def check_background_margin(
    levels_db: ArrayLike, background_levels_db: ArrayLike
) -> BackgroundMarginCheck:
    """Does the source stand clear of the background? 5.1.4.

    The clause asks for 10 dB at every position and in every octave band the
    curve is measured over. Between 10 dB and 6 dB it asks for the background
    correction of ISO 3744 (:func:`phonometry.emission.background_correction`)
    before the levels are used; at 6 dB or less it asks for neither, because
    there is no longer a source level to correct towards.

    The verdict is returned rather than applied: correcting the levels here
    would change a measured number behind the caller's back, and the correction
    the clause names belongs to the standard that prints it. A margin under
    10 dB anywhere also emits :class:`SpatialDecayWarning`, so a curve computed
    from levels nobody checked says so on the way past.

    One octave band at a time, as every other function of clause 6 takes its
    positions: the clause asks the same 10 dB of every band, and a curve is
    read band by band.

    :param levels_db: :math:`L_p` with the test source running, in decibels,
        one value per measured position of one octave band.
    :param background_levels_db: The background at the same positions, in
        decibels, as a scalar or one value per position.
    :return: The verdict, as a :class:`BackgroundMarginCheck`.
    :raises ValueError: For inputs that are not finite or do not match position
        for position.
    """
    levels = require_finite_array(levels_db, "levels_db")
    background = require_finite_array(background_levels_db, "background_levels_db")
    if background.size not in (1, levels.size):
        msg = (
            "'background_levels_db' must be a scalar or match 'levels_db' "
            "position for position."
        )
        raise ValueError(msg)
    margins = np.asarray(levels - background, dtype=np.float64)
    unusable = margins <= ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB
    needs_correction = (
        margins < ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB
    ) & ~unusable
    satisfied = not bool(np.any(margins < ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB))
    if not satisfied:
        worst = float(np.min(margins))
        detail = (
            f"{int(np.count_nonzero(unusable))} of them at or under "
            f"{ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB:g} dB, which 5.1.4 offers no "
            "correction for"
            if bool(np.any(unusable))
            else (
                "which 5.1.4 asks the ISO 3744 background correction for "
                "before the levels are used"
            )
        )
        warnings.warn(
            f"ISO 14257 5.1.4 asks for {ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB:g} dB over the "
            f"background at every position and in every octave band; "
            f"{int(np.count_nonzero(margins < ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB))} of "
            f"{margins.size} clear less than that and the worst is "
            f"{worst:.1f} dB, {detail}.",
            SpatialDecayWarning,
            stacklevel=2,
        )
    return BackgroundMarginCheck(
        margins_db=margins,
        needs_correction=needs_correction,
        unusable=unusable,
        satisfied=satisfied,
    )


@dataclass(frozen=True)
class SpatialDecayResult:
    r"""A spatial sound distribution curve and what clause 6 reads off it.

    :param distances_m: The distance of each microphone position from the
        acoustical centre of the source, in metres.
    :param distribution_values_db: :math:`D` at each position, in decibels.
    :param reference_values_db: :math:`D_\mathrm{ref}` at each position, in
        decibels.
    :param level_excess_db: :math:`\mathrm{DL}_\mathrm{f}` at each position,
        in decibels.
    :param decay_rate_db: :math:`\mathrm{DL}_2` over the range, in decibels
        per distance doubling.
    :param mean_excess_db: :math:`\mathrm{DL}_\mathrm{f}(r_n, r_m)` over the
        range, in decibels.
    :param region: ``"near"``, ``"middle"``, ``"far"`` or ``"whole"``.
    :param band_hz: The nominal octave centre the curve belongs to, in hertz,
        or ``None`` for a curve that stands for a spectrum.
    """

    distances_m: NDArray[np.float64]
    distribution_values_db: NDArray[np.float64]
    reference_values_db: NDArray[np.float64]
    level_excess_db: NDArray[np.float64]
    decay_rate_db: float
    mean_excess_db: float
    region: str
    band_hz: float | None = None

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes:
        """Draw the curve, the free-field reference and the fitted slope.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param kwargs: Passed to the renderer, including ``language``.
        :return: The axes drawn on.
        """
        from .._i18n import check_language
        from .._plot.room import plot_spatial_decay

        check_language(kwargs.get("language", "en"))
        return plot_spatial_decay(self, ax=ax, **kwargs)


def sound_distribution_value(
    levels_db: ArrayLike, sound_power_levels_db: ArrayLike
) -> NDArray[np.float64]:
    r"""The sound distribution value of a measured point, Equation (1).

    .. math::

       D_j(r) = L_{pj}(r) - L_{Wj}

    Subtracting the source's own sound power is what makes the curve a property
    of the room: run the test again with a louder source and every value comes
    back the same.

    :param levels_db: :math:`L_{pj}(r)` at each position, in decibels.
    :param sound_power_levels_db: :math:`L_{Wj}` of the source, in decibels,
        as a scalar or one value per position.
    :return: :math:`D_j(r)`, in decibels.
    :raises ValueError: For inputs that are not finite or do not broadcast.
    """
    levels = require_finite_array(levels_db, "levels_db")
    power = require_finite_array(sound_power_levels_db, "sound_power_levels_db")
    if power.size not in (1, levels.size):
        msg = (
            "'sound_power_levels_db' must be a scalar or match 'levels_db' "
            "position for position."
        )
        raise ValueError(msg)
    return np.asarray(levels - power, dtype=np.float64)


def reference_distribution_value(distances_m: ArrayLike) -> NDArray[np.float64]:
    r"""The free-field reference curve, Equation (2).

    .. math::

       D_\mathrm{ref}(r) = 10 \lg \frac{r_0^2}{4 \pi r^2}
                         = 20 \lg \frac{r_0}{r} - 11 \ \text{dB}

    The clause prints both forms and they are the same number to within the
    rounding of the 11: :math:`10 \lg 4\pi` is 10,99. The printed 11 is what is
    used here, because it is the curve the standard draws in its own figures.

    :param distances_m: :math:`r` at each position, in metres.
    :return: :math:`D_\mathrm{ref}(r)`, in decibels.
    :raises ValueError: For a distance that is not strictly positive.
    """
    radii = require_positive_array(distances_m, "distances_m")
    return np.asarray(
        20.0 * np.log10(ISO14257_REFERENCE_DISTANCE_M / radii) - FREE_FIELD_OFFSET_DB,
        dtype=np.float64,
    )


def floor_reference_value(
    distances_m: ArrayLike,
    *,
    source_height_m: float = 0.0,
    path_height_m: float | None = None,
) -> NDArray[np.float64]:
    r"""The reference curve over a reflecting plane, Equations (B.2) to (B.4).

    .. math::

       D_\mathrm{floor,ref}(r) = D_\mathrm{ref}(r)
       + 10 \lg\left(1 + \frac{r^2}{r^2 + 4 h_S h_P}\right) \ \text{dB}

    With the microphone path at the source height the product becomes
    :math:`4 h_S^2`, which is Equation (B.3); with the source on the floor the
    whole bracket becomes 2 and the correction is the 3 dB of Equation (B.4),
    the free field folded into a half space.

    :param distances_m: :math:`r` at each position, in metres.
    :param source_height_m: :math:`h_S`, in metres; zero for a source on the
        floor.
    :param path_height_m: :math:`h_P`, in metres; omit it for a path at the
        source height.
    :return: :math:`D_\mathrm{floor,ref}(r)`, in decibels.
    :raises ValueError: For a distance that is not strictly positive or a
        negative height.
    """
    radii = require_positive_array(distances_m, "distances_m")
    source = require_finite(source_height_m, "source_height_m")
    if source < 0.0:
        msg = "'source_height_m' must be zero or positive."
        raise ValueError(msg)
    path = (
        source
        if path_height_m is None
        else require_finite(path_height_m, "path_height_m")
    )
    if path < 0.0:
        msg = "'path_height_m' must be zero or positive."
        raise ValueError(msg)
    squared = radii**2
    bracket = 1.0 + squared / (squared + 4.0 * source * path)
    return reference_distribution_value(radii) + 10.0 * np.log10(bracket)


def corrected_distribution_value(
    distribution_values_db: ArrayLike,
    measured_reference_db: ArrayLike,
    distances_m: ArrayLike,
    *,
    source_height_m: float = 0.0,
    path_height_m: float | None = None,
) -> NDArray[np.float64]:
    r"""The Annex B correction for the source's own curve, Equation (B.1).

    .. math::

       D_{\mathrm{corr}\,j}(r) = 10 \lg\left[
       10^{D_j(r)/10} - 10^{D_{\mathrm{meas,ref}\,j}(r)/10}
       + 10^{D_\mathrm{floor,ref}(r)/10}\right] \ \text{dB}

    What the annex does is swap one reference curve for another: it takes the
    source's measured free-field-over-a-reflecting-plane curve out of the
    measurement and puts the theoretical one back, so that what is left is the
    room. It matters where the room's own excess is small, which is where the
    source's directivity and the floor reflection are a large part of what the
    meter saw.

    :param distribution_values_db: :math:`D_j(r)` in the room, in decibels.
    :param measured_reference_db: :math:`D_{\mathrm{meas,ref}\,j}(r)` measured
        for this source over a reflecting plane, in decibels.
    :param distances_m: :math:`r` at each position, in metres.
    :param source_height_m: :math:`h_S`, in metres.
    :param path_height_m: :math:`h_P`, in metres.
    :return: :math:`D_{\mathrm{corr}\,j}(r)`, in decibels.
    :raises ValueError: For inputs that do not match position for position, or
        a correction that leaves no energy at all.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    measured = require_finite_array(measured_reference_db, "measured_reference_db")
    radii = require_positive_array(distances_m, "distances_m")
    if values.shape != measured.shape or values.shape != radii.shape:
        msg = (
            "'distribution_values_db', 'measured_reference_db' and "
            "'distances_m' must match position for position."
        )
        raise ValueError(msg)
    floor = floor_reference_value(
        radii, source_height_m=source_height_m, path_height_m=path_height_m
    )
    energy = (
        10.0 ** (values / 10.0) - 10.0 ** (measured / 10.0) + 10.0 ** (floor / 10.0)
    )
    if np.any(energy <= 0.0):
        msg = (
            "Equation (B.1) takes the measured reference curve out of the "
            "measurement, and here it takes out more than there was: the "
            "reference curve cannot be louder than the room measurement at "
            "the same position."
        )
        raise ValueError(msg)
    return np.asarray(10.0 * np.log10(energy), dtype=np.float64)


def spectrum_distribution_value(
    distribution_values_db: ArrayLike, machine_power_levels_db: ArrayLike
) -> float:
    r"""The curve collapsed onto one machine's spectrum, Equation (3).

    .. math::

       D_S(r) = 10 \lg \frac{\sum_j 10^{(D_j(r) + L_{W\mathrm{mach}\,j})/10}}
                            {\sum_j 10^{L_{W\mathrm{mach}\,j}/10}} \ \text{dB}

    The octave-band curve says what the room does to each band; this says what
    the room does to one particular machine, which is the number a layout
    decision is made on.

    :param distribution_values_db: :math:`D_j(r)` in each band, in decibels.
    :param machine_power_levels_db: :math:`L_{W\mathrm{mach}\,j}` of the
        machine in the same bands, in decibels.
    :return: :math:`D_S(r)`, in decibels.
    :raises ValueError: For inputs that do not match band for band.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    power = require_finite_array(machine_power_levels_db, "machine_power_levels_db")
    if values.shape != power.shape:
        msg = (
            "'distribution_values_db' and 'machine_power_levels_db' must "
            "match band for band."
        )
        raise ValueError(msg)
    numerator = float(np.sum(10.0 ** ((values + power) / 10.0)))
    denominator = float(np.sum(10.0 ** (power / 10.0)))
    return 10.0 * math.log10(numerator / denominator)


def normalized_distribution_value(
    distribution_values_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> float:
    r"""The curve collapsed onto A-weighted pink noise, Equation (4).

    .. math::

       D_\mathrm{Norm} = 10 \lg \sum_j 10^{(D_j + P_j)/10} \ \text{dB}
                       - 6,2 \ \text{dB}

    with :math:`P_j` from Table 1. It is Equation (3) with one spectrum fixed,
    and 4.2.3 says why that spectrum is a normalisation and not an average
    industrial machine: the spectra met in practice are too varied for any
    average to mean anything.

    The 6,2 dB is the energy sum of the A-weighting curve printed to one
    decimal, and the six printed weights of Table 1 sum to 6,251 5 dB, so the
    printed equation returns a flat curve 0,05 dB high. It is used as printed:
    the result is what a hand evaluation of the printed equation gives, which
    is 0,05 dB above Annex C, normalised exactly (see the errata registry). For
    the exact normalisation, which returns a flat curve unchanged, call
    :func:`spectrum_distribution_value` with the values of
    :data:`PINK_NOISE_WEIGHTS_DB` as the machine spectrum.

    :param distribution_values_db: :math:`D_j` in each band, in decibels, in
        the order of :data:`SPATIAL_DECAY_BANDS_HZ` unless ``frequencies``
        says otherwise.
    :param frequencies: The nominal octave centres the values belong to, in
        hertz.
    :return: :math:`D_\mathrm{Norm}`, in decibels.
    :raises ValueError: For a count that is not the six bands of Table 1, or a
        frequency the table does not name.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    if frequencies is None:
        bands = np.asarray(SPATIAL_DECAY_BANDS_HZ, dtype=np.float64)
    else:
        bands = require_positive_array(frequencies, "frequencies")
    if values.shape != bands.shape:
        msg = (
            "Table 1 of ISO 14257 normalises over its six octave bands; got "
            f"{values.size} value(s) against {bands.size} band(s)."
        )
        raise ValueError(msg)
    weights = []
    matched = []
    for band in bands.tolist():
        match = [
            centre
            for centre in PINK_NOISE_WEIGHTS_DB
            if math.isclose(band, centre, rel_tol=1e-3)
        ]
        if not match:
            msg = (
                f"{band:g} Hz is not one of the octave bands Table 1 of "
                "ISO 14257 names."
            )
            raise ValueError(msg)
        matched.append(match[0])
        weights.append(PINK_NOISE_WEIGHTS_DB[match[0]])
    # Counting the bands is not enough: six values that repeat 125 Hz and leave
    # 4 kHz out would weigh one band twice and another not at all, and the sum
    # of Equation (4) is over the six once each, in whatever order they come.
    if sorted(matched) != sorted(PINK_NOISE_WEIGHTS_DB):
        printed = ", ".join(f"{centre:g}" for centre in sorted(PINK_NOISE_WEIGHTS_DB))
        msg = (
            "Equation (4) normalises over each of the six octave bands of "
            f"Table 1 of ISO 14257 once: {printed} Hz, in any order."
        )
        raise ValueError(msg)
    weighted = values + np.asarray(weights, dtype=np.float64)
    total = float(np.sum(10.0 ** (weighted / 10.0)))
    return 10.0 * math.log10(total) - NORMALIZED_OFFSET_DB


def _regression(
    values: NDArray[np.float64], radii: NDArray[np.float64]
) -> tuple[float, float]:
    """The least-squares slope and the mean of ``lg(r/r0)``, per decade."""
    logs = np.log10(radii / ISO14257_REFERENCE_DISTANCE_M)
    count = float(values.size)
    numerator = count * float(np.sum(values * logs)) - float(np.sum(values)) * float(
        np.sum(logs)
    )
    denominator = count * float(np.sum(logs**2)) - float(np.sum(logs)) ** 2
    if denominator <= 0.0:
        msg = (
            "The regression of Equation (5) needs at least two distinct "
            "distances; every position given is at the same distance."
        )
        raise ValueError(msg)
    return numerator / denominator, float(np.mean(logs))


def spatial_decay_rate(
    distribution_values_db: ArrayLike, distances_m: ArrayLike
) -> float:
    r"""The rate of spatial decay per distance doubling, Equation (5).

    .. math::

       \mathrm{DL}_2 = -0,3 \,
       \frac{z \sum D_i \lg(r_i/r_0) - \sum D_i \sum \lg(r_i/r_0)}
            {z \sum [\lg(r_i/r_0)]^2 - [\sum \lg(r_i/r_0)]^2} \ \text{dB}

    A free field gives 6 dB, a perfectly diffuse room gives 0, and a real
    workroom sits between them: 4,6 dB in the middle range of the Annex C
    example, which is a large and moderately fitted shipyard hall.

    The sign is the way round a reader expects: the regression slope is
    negative, so a room that gets quieter with distance returns a positive
    number of decibels per doubling.

    :param distribution_values_db: :math:`D_i` at the positions of the range,
        in decibels.
    :param distances_m: :math:`r_i` at the same positions, in metres.
    :return: :math:`\mathrm{DL}_2`, in decibels per distance doubling.
    :raises ValueError: For inputs that do not match position for position,
        fewer than two positions, or positions that are all at one distance.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    radii = require_positive_array(distances_m, "distances_m")
    if values.shape != radii.shape:
        raise ValueError(_MISMATCH_MSG)
    if values.size < _MIN_REGRESSION_POINTS:
        msg = (
            "Equation (5) is a regression over a range of distances; it needs "
            f"at least {_MIN_REGRESSION_POINTS} positions, got {values.size}."
        )
        raise ValueError(msg)
    slope, _mean_log = _regression(values, radii)
    if values.size == _MIN_REGRESSION_POINTS:
        # After the regression, not before: two positions at one distance are
        # refused by it, and an advisory about a fit that cannot be made would
        # be noise in front of the error that says so.
        #
        # Two positions define a line, so the fit has nothing left over to
        # describe: the answer is the slope between those two points and a
        # position that was misread carries straight into it. The recommended
        # distributions of 5.3.2 put many more than two in a region, and the
        # clause calls the count they give a minimum.
        warnings.warn(
            "Equation (5) over two positions is the line through them, not a "
            "regression with anything to spare: the rate returned is the slope "
            "between the two and no position can be checked against the rest. "
            "5.3.2 of ISO 14257 calls the positions of its recommended "
            "distributions a minimum number.",
            SpatialDecayWarning,
            stacklevel=2,
        )
    return -DECADE_TO_DOUBLING * slope


def level_excess(
    distribution_values_db: ArrayLike, distances_m: ArrayLike
) -> NDArray[np.float64]:
    r"""The excess over a free field at each position, Equation (6).

    .. math::

       \mathrm{DL}_\mathrm{f} = D - D_\mathrm{ref}

    :param distribution_values_db: :math:`D` at each position, in decibels.
    :param distances_m: :math:`r` at each position, in metres.
    :return: :math:`\mathrm{DL}_\mathrm{f}` at each position, in decibels.
    :raises ValueError: For inputs that do not match position for position.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    radii = require_positive_array(distances_m, "distances_m")
    if values.shape != radii.shape:
        raise ValueError(_MISMATCH_MSG)
    return np.asarray(values - reference_distribution_value(radii), dtype=np.float64)


def mean_level_excess(
    distribution_values_db: ArrayLike, distances_m: ArrayLike
) -> float:
    r"""The excess averaged over a distance range, Equation (7).

    .. math::

       \mathrm{DL}_\mathrm{f}(r_n, r_m) =
       \frac{\sum_{i=n+1}^{m}
             \left[(\mathrm{DL}_{\mathrm{f}i} + \mathrm{DL}_{\mathrm{f}i-1})
             \lg(r_i/r_{i-1})\right]}
            {2 \lg(r_m/r_n)} \ \text{dB}

    It is the trapezoidal mean of the excess against the logarithm of the
    distance, which is the axis the curve is drawn on, so a position twice as
    far weighs the same as one twice as near rather than twice as much.

    :param distribution_values_db: :math:`D` at the positions of the range, in
        decibels.
    :param distances_m: :math:`r` at the same positions, in metres, in
        increasing order.
    :return: :math:`\mathrm{DL}_\mathrm{f}(r_n, r_m)`, in decibels.
    :raises ValueError: For inputs that do not match, fewer than two
        positions, or distances that do not increase.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    radii = require_positive_array(distances_m, "distances_m")
    if values.shape != radii.shape:
        raise ValueError(_MISMATCH_MSG)
    if values.size < _MIN_REGRESSION_POINTS:
        msg = (
            "Equation (7) averages between positions; it needs at least "
            f"{_MIN_REGRESSION_POINTS}, got {values.size}."
        )
        raise ValueError(msg)
    if np.any(np.diff(radii) <= 0.0):
        msg = "'distances_m' must increase from one position to the next."
        raise ValueError(msg)
    excess = level_excess(values, radii)
    steps = np.log10(radii[1:] / radii[:-1])
    total = float(np.sum((excess[1:] + excess[:-1]) * steps))
    return total / (2.0 * math.log10(radii[-1] / radii[0]))


def level_excess_at(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
    distance_m: float,
) -> float:
    r"""The excess read off the regression line at one distance, Equation (8).

    .. math::

       \mathrm{DL}'_{\mathrm{f}r} = \left(\sum_{i=n}^{m} \frac{D_i}{z}\right)
       + 20 \lg \frac{r}{r_0}
       + \frac{\mathrm{DL}_2(r_n, r_m)}{\lg 2}
         \left[\left(\sum_{i=n}^{m} \frac{\lg(r_i/r_0)}{z}\right)
               - \lg \frac{r}{r_0}\right] + 11 \ \text{dB}

    This is the height of the fitted line over the free-field line at a
    conventional distance: 4 m for the near region, 10 m for the middle one and
    30 m for the far one (:data:`EVALUATION_DISTANCES_M`). Unlike Equation (7)
    it does not average the measured points, it reads the line, so a single
    outlying position moves it much less.

    Note that the clause divides by :math:`\lg 2` in full here while Equation
    (5) multiplies by the rounded 0,3; the two constants differ by 0,3 % and
    the errata registry records it.

    :param distribution_values_db: :math:`D_i` at the positions of the range,
        in decibels.
    :param distances_m: :math:`r_i` at the same positions, in metres.
    :param distance_m: :math:`r`, the distance to read at, in metres.
    :return: :math:`\mathrm{DL}'_{\mathrm{f}r}`, in decibels.
    :raises ValueError: For inputs that do not match, fewer than two
        positions, or a non-positive distance.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    radii = require_positive_array(distances_m, "distances_m")
    target = require_positive(distance_m, "distance_m")
    if values.shape != radii.shape:
        raise ValueError(_MISMATCH_MSG)
    nearest, farthest = float(np.min(radii)), float(np.max(radii))
    if not nearest <= target <= farthest:
        # Equation (8) reads the fitted line, and outside the range it was
        # fitted over it is reading a line nothing measured holds up. The far
        # region is where this happens: its conventional distance is 30 m and
        # 6.2 recommends the path reach 24 m, so a path that stops there
        # answers the far region by extrapolation or not at all.
        warnings.warn(
            f"Equation (8) reads the regression line at {target:g} m, outside "
            f"the {nearest:g} m to {farthest:g} m the positions given cover, "
            "so the value is an extrapolation of the fit rather than a "
            "reading of the measurement.",
            SpatialDecayWarning,
            stacklevel=2,
        )
    decay = spatial_decay_rate(values, radii)
    log_target = math.log10(target / ISO14257_REFERENCE_DISTANCE_M)
    mean_value = float(np.mean(values))
    mean_log = float(np.mean(np.log10(radii / ISO14257_REFERENCE_DISTANCE_M)))
    return (
        mean_value
        + 20.0 * log_target
        + decay / math.log10(2.0) * (mean_log - log_target)
        + FREE_FIELD_OFFSET_DB
    )


def distance_region(
    distance_m: float,
    *,
    near_limit_m: float = TYPICAL_NEAR_LIMIT_M,
    far_limit_m: float = TYPICAL_FAR_LIMIT_M,
) -> str:
    """Which of the three regions of 6.2 a distance falls in.

    The near region runs from 1 m to :math:`d_1`, the middle from :math:`d_1`
    to :math:`d_2` and the far one from :math:`d_2` out. The typical
    boundaries are 5 m and 16 m; other values may be used and are then
    recorded and reported, which is why they are arguments here.

    :param distance_m: The distance from the acoustical centre, in metres.
    :param near_limit_m: :math:`d_1`, in metres.
    :param far_limit_m: :math:`d_2`, in metres.
    :return: ``"near"``, ``"middle"`` or ``"far"``.
    :raises ValueError: For a non-positive distance, boundaries that do not
        increase, a near boundary inside the first metre, which would leave the
        near region empty, or a distance inside that first metre, which the
        clause does not evaluate.
    """
    radius = require_positive(distance_m, "distance_m")
    near = require_positive(near_limit_m, "near_limit_m")
    far = require_positive(far_limit_m, "far_limit_m")
    if far <= near:
        msg = "'far_limit_m' must be greater than 'near_limit_m'."
        raise ValueError(msg)
    if near < NEAR_REGION_START_M:
        # The near region is the stretch from 1 m to d1, so a d1 under 1 m is
        # not a narrow near region: it is none at all, and the first position
        # the clause evaluates would come back as middle.
        msg = (
            f"The near region of 6.2 runs from {NEAR_REGION_START_M:g} m to "
            f"'near_limit_m', so it cannot end at {near:g} m."
        )
        raise ValueError(msg)
    if radius < NEAR_REGION_START_M:
        msg = (
            f"6.2 of ISO 14257 starts the near region at "
            f"{NEAR_REGION_START_M:g} m; got {radius:g} m."
        )
        raise ValueError(msg)
    if radius <= near:
        return "near"
    if radius <= far:
        return "middle"
    return "far"


def omnidirectionality_tolerance_db(frequency_hz: float) -> float:
    """The directivity band a qualifying source stays inside, A.1.

    The clause states the tolerance in three pieces: ``+/- 2`` dB in the
    one-third-octave bands from 100 Hz to 630 Hz, a linear increase to
    ``+/- 8`` dB between 630 Hz and 1 kHz, and ``+/- 8`` dB from 1 kHz to
    5 kHz. The increase is taken here across the three one-third-octave bands
    that span it, so 800 Hz is the midpoint at 5 dB; the clause says "linearly"
    without saying linear in what, and the band index is the only reading on
    which the two endpoints land on printed bands.

    :param frequency_hz: The one-third-octave centre, in hertz.
    :return: The largest absolute directivity index allowed, in decibels.
    :raises ValueError: For a non-positive frequency.
    """
    centre = require_positive(frequency_hz, "frequency_hz")
    low_db, high_db = OMNIDIRECTIONAL_TOLERANCE_DB
    low_hz, high_hz = OMNIDIRECTIONAL_RAMP_HZ
    index = _third_octave_index(centre)
    low_index = _third_octave_index(low_hz)
    high_index = _third_octave_index(high_hz)
    if index <= low_index:
        return low_db
    if index >= high_index:
        return high_db
    fraction = (index - low_index) / (high_index - low_index)
    return low_db + fraction * (high_db - low_db)


def _third_octave_index(frequency_hz: float) -> int:
    """Where a nominal one-third-octave centre sits in the A.1 range."""
    for index, centre in enumerate(_THIRD_OCTAVE_CENTRES_HZ):
        if math.isclose(frequency_hz, centre, rel_tol=1e-3):
            return index
    msg = (
        f"{frequency_hz:g} Hz is not one of the nominal one-third-octave "
        "centres A.1 of ISO 14257 states its requirement over, 100 Hz to "
        "5 kHz."
    )
    raise ValueError(msg)


def spatial_decay_curve(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
    *,
    near_limit_m: float = TYPICAL_NEAR_LIMIT_M,
    far_limit_m: float = TYPICAL_FAR_LIMIT_M,
    region: str = "middle",
    band_hz: float | None = None,
) -> SpatialDecayResult:
    """The curve of one region with its two descriptors, clause 6.

    :param distribution_values_db: :math:`D` at every measured position, in
        decibels, over the whole path.
    :param distances_m: :math:`r` at the same positions, in metres, in
        increasing order.
    :param near_limit_m: :math:`d_1` of 6.2, in metres.
    :param far_limit_m: :math:`d_2` of 6.2, in metres.
    :param region: ``"near"``, ``"middle"``, ``"far"`` or ``"whole"``.
    :param band_hz: The octave centre the curve belongs to, in hertz.
    :return: The curve and its descriptors, as a :class:`SpatialDecayResult`.
    :raises ValueError: For an unknown region, inputs that do not match, or a
        region holding fewer than two measured positions.
    """
    values = require_finite_array(distribution_values_db, "distribution_values_db")
    radii = require_positive_array(distances_m, "distances_m")
    if values.shape != radii.shape:
        raise ValueError(_MISMATCH_MSG)
    if region not in _REGIONS:
        msg = f"'region' must be one of {_REGIONS}; got {region!r}."
        raise ValueError(msg)
    if region == "whole":
        keep = np.ones(radii.shape, dtype=np.bool_)
    else:
        keep = np.asarray(
            [
                distance_region(
                    float(radius), near_limit_m=near_limit_m, far_limit_m=far_limit_m
                )
                == region
                for radius in radii.tolist()
            ],
            dtype=np.bool_,
        )
        # 6.2 draws the regions closed at both ends, so the position that
        # bounds two of them belongs to both regressions.
        if region == "middle":
            keep |= np.isclose(radii, near_limit_m)
        elif region == "far":
            keep |= np.isclose(radii, far_limit_m)
    if int(np.count_nonzero(keep)) < _MIN_REGRESSION_POINTS:
        msg = (
            f"The {region} region holds {int(np.count_nonzero(keep))} of the "
            f"{radii.size} positions given, and clause 6 needs at least "
            f"{_MIN_REGRESSION_POINTS} to describe one."
        )
        raise ValueError(msg)
    chosen, chosen_radii = values[keep], radii[keep]
    return SpatialDecayResult(
        distances_m=chosen_radii,
        distribution_values_db=chosen,
        reference_values_db=reference_distribution_value(chosen_radii),
        level_excess_db=level_excess(chosen, chosen_radii),
        decay_rate_db=spatial_decay_rate(chosen, chosen_radii),
        mean_excess_db=mean_level_excess(chosen, chosen_radii),
        region=region,
        band_hz=None if band_hz is None else require_positive(band_hz, "band_hz"),
    )
