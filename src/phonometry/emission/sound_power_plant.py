#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound power levels of multisource industrial plants for the evaluation of
sound pressure levels in the environment: ISO 8297:1994, engineering method
(grade 2).

A petrochemical complex, a quarry or a crushing plant is too large for any
enveloping surface of ISO 3744, and too full of sources for any one of them
to be measured alone. ISO 8297 treats the whole plant as one source. A closed
path, the **measurement contour**, is drawn round the plant area on the plot
plan; microphones stand on it at equal spacing, raised to a height that grows
with the area the contour encloses, and point horizontally at the plant; the
octave-band levels they read are averaged, and a few corrections turn the
average into the sound power the plant radiates towards its neighbours, the
number a prediction model needs at a distance of at least 1,5 times the
largest dimension of the plant area (clause 0.2 a).

The contour (clause 9.1.1) has three requirements. The average of the
distances :math:`d_i` from each position to the nearest point of the plant
perimeter (9.1.2.2),

.. math::

   \bar{d} = \frac{1}{N} \sum_{i=1}^{N} d_i ,

shall exceed :math:`0{,}05\sqrt{S_\mathrm{p}}` or 5 m, whichever is the
greater, and shall not exceed :math:`0{,}5\sqrt{S_\mathrm{p}}` or 35 m,
whichever is the lesser, :math:`S_\mathrm{p}` being the plant area; the plant
area shall be seen from any point of the contour inside an aspect angle of at
most 180°; and adjacent positions shall be at most :math:`2\bar{d}` apart.
The microphone height (9.3) is

.. math::

   h = H + 0{,}025\sqrt{S_\mathrm{m}} \quad \text{or 5 m, whichever is the
   greater,}

with :math:`S_\mathrm{m}` the area the contour encloses and :math:`H` the
characteristic height of the plant, the mean height of its :math:`n` sources
(9.2 c), :math:`H = \frac{1}{n}\sum_k h_k`.

Clause 10 then computes, band by band, the energy average of the levels
:math:`L_{pi}` at the :math:`N` positions (10.1),

.. math::

   \overline{L_p} = 10 \lg\left[\frac{1}{N} \sum_{i=1}^{N} 10^{0{,}1 L_{pi}}
   \right] \ \mathrm{dB},

replaces any level more than 5 dB above that average by
:math:`\overline{L_p} + 5` dB and averages again into
:math:`\overline{L_p^*}` when a contour further out is not practicable (10.2,
10.3), and adds four terms (10.4 to 10.8):

.. math::

   L_W = \overline{L_p} + \Delta L_\mathrm{S} + \Delta L_\mathrm{F}
   + \Delta L_\mathrm{M} + \Delta L_\alpha ,

.. math::

   \Delta L_\mathrm{S} = 10 \lg\frac{2 S_\mathrm{m} + h l}{S_0}\ \mathrm{dB},
   \qquad
   \Delta L_\mathrm{F} = \lg\frac{\bar{d}}{4\sqrt{S_\mathrm{p}}}\ \mathrm{dB},

.. math::

   \Delta L_\mathrm{M} = 3\left(1 - \frac{\theta}{90}\right) \mathrm{dB},
   \qquad
   \Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}\ \mathrm{dB},

with :math:`l` the length of the contour, :math:`S_0 = 1` m², :math:`\theta`
the angle at which a directional microphone has lost 3 dB
(:math:`\Delta L_\mathrm{M} = 0` for an omnidirectional one) and
:math:`\alpha` the attenuation coefficient of the air. The area term is the
measurement surface of ISO 3744: for a circular contour round a point source
on the ground, :math:`2 S_\mathrm{m}` is the hemisphere :math:`2\pi r^2` over
it and :math:`h l` the band of wall of height :math:`h` round it. The
proximity term has no factor 10: NOTE 11 says it lies between −0,9 dB and
−1,9 dB when 9.1 is met, and :math:`\lg(0{,}5/4) = -0{,}903` and
:math:`\lg(0{,}05/4) = -1{,}903` are its two ends. The A-weighted level of
10.9 is :math:`L_{W\mathrm{A}} = 10 \lg \sum_j 10^{0{,}1(L_{Wj} + C_j)}` dB,
with the octave-band :math:`C_j` of ISO 3744:2010 Annex E that every other
sound power method of this library uses.

**The air absorption.** Table 3 prints :math:`\alpha` per octave band at
15 °C and 70 %, "taken from ISO 3891", and asks for the values at the
measured temperature and humidity when the weather differs markedly. With no
weather given, :func:`plant_air_absorption_db_per_m` returns Table 3 as
printed; with a temperature and a humidity it evaluates the attenuation
coefficient of ISO 3891:1978 Annex A (SAE ARP 866A) at the one-third-octave
band centred on each octave, through the transcription
:func:`phonometry.aircraft.atmospheric_absorption.arp866a_attenuation` that
the ECAC Doc 29 Appendix D implementation reads; there is no second copy of
it here. ISO 3891 gives no evaluation frequency below 50 Hz, so the 31,5 Hz
band keeps the 0 of Table 3 in any weather. At 15 °C and 70 % the formula
agrees with Table 3 to its printed digit at 63 Hz and from 250 Hz to 2 kHz,
and not at 125 Hz (0,000 59 dB/m against 0), 4 kHz (0,025 05 against 0,026)
or 8 kHz (0,061 against 0,046): ISO 3891 Table 9 prints 0,1, 2,5 and
6,1 dB/100 m in those bands at those conditions, and ISO 8297 does not say
how it drew its octave values from the one-third-octave data of ISO 3891, so
Table 3 is kept as printed and the difference is recorded, not corrected.
The difference reaches the sound power through
:math:`\Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}`: passing 15 °C
and 70 % gives :math:`0{,}0074\sqrt{S_\mathrm{m}}` dB more at 8 kHz than
omitting the weather, 1,4 dB for a measurement area of 36 800 m². The
weather is therefore for the case 10.7 names, a weather that differs
markedly from 15 °C and 70 %; at or near those conditions Table 3 is the
reading the standard gives.

**What is judged and what is computed.** :func:`plant_measurement_contour`
lays the positions on a contour given as a polygon round the plant polygon
and measures everything 9.1 and 9.2 ask for; :func:`plant_sound_power` runs
clause 10 on the levels read there; :func:`check_plant_measurement` holds
the arrangement and the readings against the requirements of clauses 1.2,
6, 7.1, 9.1, 9.3, 9.5 and 10.2 and returns one verdict. Table 2 corrects the
levels for background noise and Table 1 states the uncertainty of the
method, which depends on :math:`\bar{d}/\sqrt{S_\mathrm{p}}` alone.
Clause 0.2 b) uses the method to find the contribution of particular parts
of a plant, and :func:`partial_plant_contributions` combines the sound power
of parts measured on their own contours into the whole and each part's share
of it.

Source: ISO 8297:1994, read in the identical British adoption BS ISO
8297:1994 (clauses 0 to 12, Tables 1 to 3, Figure 1).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.boundary import settled
from .._internal.frozen import OwnsArrays, read_only
from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import (
    is_at_most,
    require_count,
    require_finite,
    require_finite_matrix,
    require_positive,
    require_ranks,
    require_same_length,
)
from ._shared import (
    _CK_OCTAVE,
    _S0,
    SoundPowerWarning,
    _a_weighting_corrections,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "PLANT_AIR_ABSORPTION_DB_PER_M",
    "PLANT_BACKGROUND_CORRECTION_DB",
    "PLANT_METHOD_UNCERTAINTY_DB",
    "PartialPlantContributions",
    "PlantMeasurementCheck",
    "PlantMeasurementContour",
    "PlantRequirement",
    "PlantSoundPowerResult",
    "check_plant_measurement",
    "partial_plant_contributions",
    "plant_air_absorption_db_per_m",
    "plant_background_correction_db",
    "plant_characteristic_height_m",
    "plant_mean_distance_limits_m",
    "plant_measurement_contour",
    "plant_method_uncertainty_db",
    "plant_microphone_height_m",
    "plant_sound_power",
    "plant_steady_reading_db",
]

# --------------------------------------------------------------------------- #
# The printed tables
# --------------------------------------------------------------------------- #

#: Table 3: the attenuation coefficient of the air :math:`\alpha`, in dB/m,
#: per octave band, "valid at a temperature of 15 °C and an average relative
#: humidity of 70 %" and "taken from ISO 3891" (BS ISO 8297:1994, PDF page 15,
#: printed p. 7). The first row is printed "31"; it is the 31,5 Hz octave of
#: ISO 266 that 7.2 and NOTE 8 name, and is keyed so here.
PLANT_AIR_ABSORPTION_DB_PER_M: Mapping[float, float] = MappingProxyType(
    {
        31.5: 0.0,
        63.0: 0.0,
        125.0: 0.0,
        250.0: 0.001,
        500.0: 0.002,
        1000.0: 0.005,
        2000.0: 0.01,
        4000.0: 0.026,
        8000.0: 0.046,
    }
)

#: Table 1: the uncertainty inherent in the method, a 95 % confidence interval
#: for one determination, keyed by :math:`\bar{d}/\sqrt{S_\mathrm{p}}` and
#: given as (lower, upper) in decibels (PDF page 10, printed p. 2). It covers
#: the spatial variation of the levels round the contour that an uneven
#: spread of sources causes, not a change of the emission over time.
PLANT_METHOD_UNCERTAINTY_DB: Mapping[float, tuple[float, float]] = MappingProxyType(
    {
        0.05: (-3.5, 3.0),
        0.1: (-2.5, 2.5),
        0.2: (-2.5, 2.0),
        0.5: (-2.0, 1.5),
    }
)

#: Table 2: the correction, in decibels, subtracted from the level measured
#: with the plant operating, keyed by the difference in whole decibels between
#: that level and the background alone (PDF page 14, printed p. 6). Below
#: 6 dB the table says "Measurement invalid", above 10 dB the correction is 0.
PLANT_BACKGROUND_CORRECTION_DB: Mapping[int, float] = MappingProxyType(
    {6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
)

# --------------------------------------------------------------------------- #
# The numbers of the clauses
# --------------------------------------------------------------------------- #

#: Octave bands of the method: 63 Hz to 4 kHz are measured (9.5.1 a), 31,5 Hz
#: and 8 kHz may be added (NOTE 8), nominal centres of ISO 266 (7.2).
_OCTAVE_BANDS_HZ = (31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)
#: The bands 9.5.1 a) requires, 63 Hz to 4 kHz.
_REQUIRED_BANDS_HZ = (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
#: Relative tolerance within which a frequency names a nominal octave centre:
#: wide enough for the exact base-ten and base-two centres (7 943 Hz, 31,25 Hz),
#: far narrower than the factor of two between octaves.
_BAND_TOLERANCE = 0.03
#: The lowest band ISO 3891 Table 2 evaluates, in hertz; the 31,5 Hz octave
#: lies below it.
_ISO3891_LOWEST_BAND_HZ = 50.0
#: Bounds of 9.1.1 a) on the average measurement distance: factors of
#: :math:`\sqrt{S_\mathrm{p}}` and lengths in metres.
_MIN_DISTANCE_RATIO = 0.05
_MIN_MEAN_DISTANCE_M = 5.0
_MAX_DISTANCE_RATIO = 0.5
_MAX_MEAN_DISTANCE_M = 35.0
#: 9.1.1 b): the largest aspect angle, in degrees.
_MAX_ASPECT_ANGLE_DEG = 180.0
#: 9.1.1 c): adjacent positions at most this many average distances apart.
_SPACING_PER_MEAN_DISTANCE = 2.0
#: 9.1.2.4: the largest share of omitted positions, in percent.
_MAX_OMITTED_PERCENT = 10.0
#: 9.3: the height term per root of the measurement area, and the lowest height.
_HEIGHT_PER_ROOT_AREA = 0.025
_MIN_MICROPHONE_HEIGHT_M = 5.0
#: 9.2: l, Sm and H are read off the plan "with an accuracy better than
#: ± 5 %". The height of 9.3 is built from H and the root of Sm, so it is
#: known to that fraction of itself and no better.
_PLAN_ACCURACY = 0.05
#: NOTE 7: sources below this height, ten or more of them, may be taken at
#: 1 m.
_LOW_SOURCE_HEIGHT_M = 2.0
_LOW_SOURCE_ASSUMED_HEIGHT_M = 1.0
_LOW_SOURCE_MIN_COUNT = 10
#: 1.2: the largest horizontal dimension of the plant area, from 16 m to
#: "approximately 320 m".
_MIN_PLANT_DIMENSION_M = 16.0
_MAX_PLANT_DIMENSION_M = 320.0
#: 0.2 a): the prediction treats the plant as a point source at its centre
#: from this many times its largest dimension outwards.
_RECEIVER_DISTANCE_FACTOR = 1.5
#: 7.1: the 3 dB angle of a directional microphone shall exceed 30°; 10.6
#: writes its correction against 90°.
_MIN_DIRECTIONAL_ANGLE_DEG = 30.0
_MICROPHONE_TERM_DB = 3.0
_RIGHT_ANGLE_DEG = 90.0
#: 10.2: a level more than this far above the contour average is replaced.
_EXCESS_LIMIT_DB = 5.0
#: 10.5: the factor on the root of the plant area in the proximity term.
_NEAR_FIELD_FACTOR = 4.0
#: 10.7: the factor on the root of the measurement area in the air term.
_AIR_TERM_FACTOR = 0.5
#: 6 b) and Table 2: the background at least 6 dB and preferably more than
#: 10 dB below the level measured.
_MIN_BACKGROUND_MARGIN_DB = 6.0
_PREFERRED_BACKGROUND_MARGIN_DB = 10.0
#: 9.5.1: at least 1 min in any octave band.
_MIN_MEASUREMENT_TIME_S = 60.0
#: 9.5.2: a sound level meter's needle swinging less than this is steady.
_STEADY_RANGE_DB = 5.0
#: 9.5.3: the integrated reading L_eq,T used is one that "does not fluctuate by
#: more than ± 0,5 dB", a range of at most 1 dB.
_INTEGRATED_RANGE_DB = 1.0

# The limits of 6 b), Table 2, 9.5.2, 9.5.3 and 10.2 are held against levels
# worked from decimal readings, a difference or an energy mean, which binary
# arithmetic leaves a few units of the last place off their decimal value:
# 20,4 - 14,4 dB is 5,999 999 999 999 998 and is still the 6 dB of Table 2's
# first row. Each such level is settled to nine decimals (``settled``, shared
# by every verdict at a printed limit) before it meets its limit, so the verdict does
# not hang on the last binary digit of the machine that worked it out.

#: The fewest vertices of a polygon.
_MIN_VERTICES = 3
#: The fewest positions a contour layout starts from.
_MIN_POSITIONS = 3
#: Points at which a stretch of contour inside the convex hull of the plant
#: is sampled for the aspect angle it reports.
_INSIDE_SAMPLES = 17
#: Relative tolerance of the geometric predicates, scaled by the size of the
#: drawing.
_GEOMETRY_TOLERANCE = 1e-9
#: A 2-D point is a pair.
_POINT_SIZE = 2
#: Nominal octave-band centres of the A-weighting table this method sums over.
_A_WEIGHTED_BANDS_HZ = tuple(float(f) for f in _CK_OCTAVE)


# --------------------------------------------------------------------------- #
# Small validators
# --------------------------------------------------------------------------- #


def _octave_bands(
    frequencies_hz: ArrayLike, name: str = "frequencies_hz"
) -> np.ndarray:
    """Nominal octave centres for the frequencies given, in increasing order.

    :raises ValueError: for a frequency that names no octave band of the
        method, a band named twice, or bands out of order.
    """
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if freqs.ndim != 1 or freqs.size == 0 or not np.all(np.isfinite(freqs)):
        msg = f"'{name}' must be a non-empty 1-D array of finite frequencies."
        raise ValueError(msg)
    nominal = np.empty_like(freqs)
    for i, f in enumerate(freqs.tolist()):
        match = [
            band
            for band in _OCTAVE_BANDS_HZ
            if math.isclose(f, band, rel_tol=_BAND_TOLERANCE)
        ]
        if not match:
            msg = (
                f"'{name}' must name octave bands from 31.5 Hz to 8 kHz "
                f"(ISO 8297 7.2, 9.5.1 and NOTE 8); got {f:g} Hz."
            )
            raise ValueError(msg)
        nominal[i] = match[0]
    if np.any(np.diff(nominal) <= 0.0):
        msg = f"'{name}' must name each octave band once, in increasing order."
        raise ValueError(msg)
    return nominal


def _weather(
    temperature_c: float | None, relative_humidity_percent: float | None
) -> tuple[float | None, float | None]:
    """The measured weather, both or neither.

    :raises ValueError: when only one of the two is given.
    """
    if (temperature_c is None) != (relative_humidity_percent is None):
        msg = (
            "'temperature_c' and 'relative_humidity_percent' go together: give "
            "both for the air absorption of the weather at the measurement, or "
            "neither for Table 3 at 15 °C and 70 %."
        )
        raise ValueError(msg)
    if temperature_c is None or relative_humidity_percent is None:
        return None, None
    return (
        require_finite(temperature_c, "temperature_c"),
        require_finite(relative_humidity_percent, "relative_humidity_percent"),
    )


def _directional_angles(
    angle_deg: float | ArrayLike | None, bands: int
) -> np.ndarray | None:
    """The 3 dB angle of a directional microphone per band, or ``None``.

    :raises ValueError: for an angle that is not in (0°, 90°].
    """
    if angle_deg is None:
        return None
    theta = np.atleast_1d(np.asarray(angle_deg, dtype=np.float64))
    if theta.size == 1:
        theta = np.full(bands, float(theta[0]))
    if theta.ndim != 1 or theta.size != bands or not np.all(np.isfinite(theta)):
        msg = (
            "'directional_microphone_angle_deg' must be one angle, or one per "
            f"octave band ({bands})."
        )
        raise ValueError(msg)
    if np.any(theta <= 0.0) or np.any(theta > _RIGHT_ANGLE_DEG):
        msg = (
            "'directional_microphone_angle_deg' must lie in (0°, 90°]: 10.6 "
            "writes the correction of a directional microphone against 90°, and "
            "past it the formula turns negative where an omnidirectional "
            "microphone takes 0 dB; pass None for an omnidirectional one."
        )
        raise ValueError(msg)
    return theta


# --------------------------------------------------------------------------- #
# Clause by clause
# --------------------------------------------------------------------------- #


def plant_characteristic_height_m(
    source_heights_m: ArrayLike, *, low_source_count: int = 0
) -> float:
    r"""The characteristic height of the plant :math:`H`, 9.2 c) and NOTE 7.

    The mean height of the midpoints of the noise sources, derived from the
    equipment lists and the elevation drawings,
    :math:`H = \frac{1}{n}\sum_{k=1}^{n} h_k`. NOTE 7 lets a plant with ten or
    more sources lower than 2 m count them approximately (to ±10 %) and take
    each at 1 m: pass those sources as ``low_source_count`` and leave them out
    of ``source_heights_m``.

    :param source_heights_m: :math:`h_k`, the height of the midpoint of each
        source not counted by NOTE 7, in metres. May be empty when every
        source is.
    :param low_source_count: How many sources lower than 2 m NOTE 7 takes at
        1 m; 0, or at least 10.
    :return: :math:`H`, in metres.
    :raises ValueError: for a negative or non-finite height, a count from 1 to
        9, or no sources at all.
    """
    heights = np.atleast_1d(np.asarray(source_heights_m, dtype=np.float64))
    if heights.ndim != 1 or not np.all(np.isfinite(heights)) or np.any(heights < 0.0):
        msg = "'source_heights_m' must be a 1-D sequence of finite heights >= 0 m."
        raise ValueError(msg)
    low = require_count(low_source_count, "low_source_count", minimum=0)
    if 0 < low < _LOW_SOURCE_MIN_COUNT:
        msg = (
            f"NOTE 7 of ISO 8297 applies to {_LOW_SOURCE_MIN_COUNT} or more "
            f"sources lower than {_LOW_SOURCE_HEIGHT_M:g} m; got {low}. Give "
            "fewer low sources their heights in 'source_heights_m'."
        )
        raise ValueError(msg)
    count = heights.size + low
    if count == 0:
        msg = "The plant needs at least one noise source for its characteristic height."
        raise ValueError(msg)
    return float((np.sum(heights) + low * _LOW_SOURCE_ASSUMED_HEIGHT_M) / count)


def plant_microphone_height_m(
    characteristic_height_m: float, measurement_area_m2: float
) -> float:
    r"""The microphone height of 9.3: :math:`h = H + 0{,}025\sqrt{S_\mathrm{m}}`
    or 5 m, whichever is the greater.

    Where this height cannot be reached for practical reasons, 9.3 asks for
    the microphone as high as possible above 5 m and for the fact to be
    reported; :func:`check_plant_measurement` reports it.

    :param characteristic_height_m: :math:`H`, in metres.
    :param measurement_area_m2: :math:`S_\mathrm{m}`, the area the contour
        encloses, in square metres.
    :return: :math:`h`, in metres.
    :raises ValueError: for a negative height or a non-positive area.
    """
    height = require_finite(characteristic_height_m, "characteristic_height_m")
    if height < 0.0:
        msg = "'characteristic_height_m' must be >= 0 m."
        raise ValueError(msg)
    area = require_positive(measurement_area_m2, "measurement_area_m2")
    return max(
        height + _HEIGHT_PER_ROOT_AREA * math.sqrt(area), _MIN_MICROPHONE_HEIGHT_M
    )


def plant_mean_distance_limits_m(plant_area_m2: float) -> tuple[float, float]:
    r"""The window of 9.1.1 a) for the average measurement distance :math:`\bar{d}`.

    :math:`\bar{d}` shall exceed :math:`0{,}05\sqrt{S_\mathrm{p}}` or 5 m,
    whichever is the greater, and shall not exceed
    :math:`0{,}5\sqrt{S_\mathrm{p}}` or 35 m, whichever is the lesser. The
    lower bound is strict, so the window is empty at or below
    :math:`S_\mathrm{p} = 100` m² and at or above :math:`490\,000` m²,
    where no contour meets the clause.

    :param plant_area_m2: :math:`S_\mathrm{p}`, in square metres.
    :return: ``(lower, upper)`` in metres: :math:`\bar{d}` must be above the
        first and at most the second.
    :raises ValueError: for a non-positive area.
    """
    root = math.sqrt(require_positive(plant_area_m2, "plant_area_m2"))
    return (
        max(_MIN_DISTANCE_RATIO * root, _MIN_MEAN_DISTANCE_M),
        min(_MAX_DISTANCE_RATIO * root, _MAX_MEAN_DISTANCE_M),
    )


def plant_background_correction_db(
    level_difference_db: ArrayLike,
) -> float | NDArray[np.float64]:
    r"""The background correction of Table 2, to subtract from the level measured.

    The table is printed in whole decibels: 1 dB for a difference of 6, 7 or
    8 dB, 0,5 dB for 9 or 10 dB, 0 above 10 dB, and "Measurement invalid"
    below 6 dB. A difference between two rows is rounded to the nearest whole
    decibel, a half going up; the two ends are compared as printed, so 5,9 dB
    is invalid and 10,2 dB takes no correction. The difference is first
    settled to nine decimals, so 20,4 - 14,4 dB, 5,999 999 999 999 998 in
    binary, is the 6 dB it is, and 64,1 - 55,6 dB the 8,5 dB that rounds up.

    :param level_difference_db: The level with the plant operating less the
        background level alone, in decibels: one value or an array.
    :return: The correction, in decibels, a ``float`` for one difference and an
        array of the same shape otherwise.
    :raises ValueError: for a non-finite difference or one below 6 dB, which
        the table calls an invalid measurement.
    """
    raw = np.asarray(level_difference_db, dtype=np.float64)
    if not np.all(np.isfinite(raw)):
        msg = "'level_difference_db' must be finite."
        raise ValueError(msg)
    diff = settled(raw)
    invalid = diff < _MIN_BACKGROUND_MARGIN_DB
    if np.any(invalid):
        msg = (
            "ISO 8297 Table 2 calls a measurement invalid where the level with "
            f"the plant operating is less than {_MIN_BACKGROUND_MARGIN_DB:g} dB "
            f"above the background; got {np.min(diff):.2f} dB."
        )
        raise ValueError(msg)
    rows = np.floor(np.minimum(diff, _PREFERRED_BACKGROUND_MARGIN_DB) + 0.5).astype(int)
    table = np.vectorize(PLANT_BACKGROUND_CORRECTION_DB.__getitem__, otypes=[float])
    correction = np.where(diff > _PREFERRED_BACKGROUND_MARGIN_DB, 0.0, table(rows))
    if correction.ndim == 0:
        return float(correction)
    return np.asarray(correction, dtype=np.float64)


def plant_air_absorption_db_per_m(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float | None = None,
    relative_humidity_percent: float | None = None,
) -> NDArray[np.float64]:
    r"""The attenuation coefficient of the air :math:`\alpha` of 10.7, in dB/m.

    With no weather, Table 3 as printed, valid at 15 °C and 70 %. With the
    temperature and relative humidity at the time of the measurement, which
    Table 3 asks for when they "differ markedly" from those, the coefficient
    of ISO 3891:1978 Annex A (SAE ARP 866A) that Table 3 was taken from,
    evaluated at the one-third-octave band centred on each octave by
    :func:`phonometry.aircraft.atmospheric_absorption.arp866a_attenuation`
    (the parabolic reading of its Table 1 that reproduces ISO 3891 Table 10)
    and turned from dB/100 m into dB/m. ISO 3891 gives no evaluation frequency
    below 50 Hz, so the 31,5 Hz band keeps the 0 of Table 3.

    The two do not meet at 15 °C and 70 %: the formula gives 0,000 59 dB/m
    at 125 Hz, 0,025 05 dB/m at 4 kHz and 0,061 dB/m at 8 kHz where Table 3
    prints 0, 0,026 and 0,046, and ISO 3891 Table 9 itself prints 0,1, 2,5
    and 6,1 dB/100 m there. The other rows agree to the printed digit. In
    the sound power the 8 kHz row is a step of
    :math:`0{,}5 \times 0{,}0148\sqrt{S_\mathrm{m}} \approx
    0{,}0074\sqrt{S_\mathrm{m}}` dB between omitting the weather and
    passing 15 °C and 70 %, 1,4 dB over 36 800 m². Pass the weather only
    when it differs markedly from 15 °C and 70 %, as Table 3 asks; the
    standard sets no number for "markedly".

    :param frequencies_hz: Nominal octave-band centres, 31,5 Hz to 8 kHz.
    :param temperature_c: Air temperature at the measurement, in °C, or
        ``None`` for Table 3.
    :param relative_humidity_percent: Relative humidity at the measurement, in
        percent (0 to 100), or ``None`` for Table 3.
    :return: :math:`\alpha` per band, in dB/m.
    :raises ValueError: for a band outside the method, only one of the two
        weather values, or a humidity outside 0 % to 100 %.
    """
    bands = _octave_bands(frequencies_hz)
    theta, humidity = _weather(temperature_c, relative_humidity_percent)
    if theta is None or humidity is None:
        return np.array(
            [PLANT_AIR_ABSORPTION_DB_PER_M[float(b)] for b in bands], dtype=np.float64
        )
    from ..aircraft.atmospheric_absorption import arp866a_attenuation

    alpha = np.zeros_like(bands)
    covered = bands >= _ISO3891_LOWEST_BAND_HZ
    if np.any(covered):
        arp = arp866a_attenuation(
            bands[covered], temperature_c=theta, relative_humidity_percent=humidity
        )
        alpha[covered] = arp.coefficient_db_per_100m / 100.0
    return alpha


def plant_method_uncertainty_db(distance_ratio: float) -> tuple[float, float]:
    r"""The uncertainty inherent in the method, Table 1: a 95 % confidence
    interval for one determination, as ``(lower, upper)`` in decibels.

    Table 1 prints four rows of :math:`\bar{d}/\sqrt{S_\mathrm{p}}` and says
    nothing of the ratios between them. The interval narrows as the ratio
    grows, so a ratio between two rows takes the row at or below it, the
    wider of the two; nothing narrower than a printed row is claimed. The
    range of the table, 0,05 to 0,5, is the range 9.1.1 a) allows.

    NOTE 1 adds that where the background corrections of 9.5.4 cannot be
    applied, the uncertainty may be greater than the table's.

    :param distance_ratio: :math:`\bar{d}/\sqrt{S_\mathrm{p}}`.
    :return: ``(lower, upper)``, for example ``(-3.5, 3.0)`` at 0,05.
    :raises ValueError: for a ratio outside 0,05 to 0,5.
    """
    ratio = require_positive(distance_ratio, "distance_ratio")
    rows = sorted(PLANT_METHOD_UNCERTAINTY_DB)
    below = [
        row for row in rows if row <= ratio or math.isclose(row, ratio, rel_tol=1e-9)
    ]
    above_top = ratio > rows[-1] and not math.isclose(ratio, rows[-1], rel_tol=1e-9)
    if not below or above_top:
        msg = (
            f"ISO 8297 Table 1 covers d/sqrt(Sp) from {rows[0]:g} to {rows[-1]:g}; "
            f"got {ratio:.4g}."
        )
        raise ValueError(msg)
    return PLANT_METHOD_UNCERTAINTY_DB[below[-1]]


def plant_steady_reading_db(maximum_db: float, minimum_db: float) -> float:
    r"""The level read on a sound level meter from a steady noise, 9.5.2.

    With time weighting S, a needle that swings over less than 5 dB marks
    the noise as steady for the standard, and the level is the arithmetic
    mean of the maximum and the minimum over the observation. A wider swing
    makes the noise non-steady, and 9.5.2 then asks for an integrating
    instrument instead (9.5.3), whose steady :math:`L_{\mathrm{eq},T}` is
    the level used; ``leq_range_db`` of :func:`check_plant_measurement`
    judges that one.

    :param maximum_db: The highest level read, in decibels.
    :param minimum_db: The lowest level read, in decibels.
    :return: The level, in decibels.
    :raises ValueError: for a minimum above the maximum, or a swing of 5 dB or
        more, the swing settled to nine decimals first, so 64,1 - 59,1 dB,
        4,999 999 999 999 993 in binary, is the 5 dB it is.
    """
    top = require_finite(maximum_db, "maximum_db")
    bottom = require_finite(minimum_db, "minimum_db")
    if bottom > top:
        msg = "'minimum_db' must not exceed 'maximum_db'."
        raise ValueError(msg)
    swing = float(settled(top - bottom))
    if swing >= _STEADY_RANGE_DB:
        msg = (
            f"The needle swings over {swing:.1f} dB; ISO 8297 9.5.2 calls "
            f"a noise steady only below {_STEADY_RANGE_DB:g} dB and asks for an "
            "integrating instrument otherwise (9.5.3)."
        )
        raise ValueError(msg)
    return 0.5 * (top + bottom)


# --------------------------------------------------------------------------- #
# Plane geometry of the plot plan
# --------------------------------------------------------------------------- #


def _polygon(vertices: ArrayLike, name: str) -> np.ndarray:
    """A simple polygon as an ``(n, 2)`` array, the closing vertex dropped.

    :raises ValueError: for fewer than three vertices, a non-finite
        coordinate, a zero area or edges that cross.
    """
    arr = _vertex_array(vertices, name)
    scale = float(np.max(np.ptp(arr, axis=0)))
    # The vertices are finite, so the scale is never NaN: a non-positive scale
    # is the one degenerate outline the comparison has to catch.
    if scale <= 0.0 or abs(_signed_area(arr)) <= _GEOMETRY_TOLERANCE * scale**2:
        msg = f"'{name}' must enclose an area."
        raise ValueError(msg)
    _require_simple(arr, scale, name)
    return arr


def _vertex_array(vertices: ArrayLike, name: str) -> np.ndarray:
    """The vertices as an ``(n, 2)`` array of at least three, the closing
    vertex dropped.

    :raises ValueError: for a shape other than ``(n, 2)``, a non-finite
        coordinate, or fewer than three distinct vertices.
    """
    arr = np.asarray(vertices, dtype=np.float64)
    if (
        arr.ndim != _POINT_SIZE
        or arr.shape[1] != _POINT_SIZE
        or not np.all(np.isfinite(arr))
    ):
        msg = f"'{name}' must be a sequence of finite (x, y) vertices in metres."
        raise ValueError(msg)
    if arr.shape[0] > _MIN_VERTICES and np.allclose(arr[0], arr[-1]):
        arr = arr[:-1]
    if arr.shape[0] < _MIN_VERTICES:
        msg = f"'{name}' must have at least {_MIN_VERTICES} distinct vertices."
        raise ValueError(msg)
    return arr


def _require_simple(polygon: np.ndarray, scale: float, name: str) -> None:
    """Reject a polygon two of whose edges that are not neighbours touch.

    Each edge is held against every later edge but the next one, and the
    first edge also spares the last, its neighbour across the closing vertex.

    :raises ValueError: naming the first pair of edges that cross.
    """
    starts, ends = _edges(polygon)
    count = polygon.shape[0]
    for i in range(count):
        stop = count - 1 if i == 0 else count
        for j in range(i + 2, stop):
            if _segments_touch(starts[i], ends[i], starts[j], ends[j], scale):
                msg = f"'{name}' must be a simple polygon; edges {i} and {j} cross."
                raise ValueError(msg)


def _signed_area(vertices: np.ndarray) -> float:
    """Shoelace area, positive for counter-clockwise vertices."""
    x, y = vertices[:, 0], vertices[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _edges(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Start and end of each edge of a closed polygon."""
    return vertices, np.roll(vertices, -1, axis=0)


def _cross(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """z component of the cross product of 2-D vectors (broadcasting)."""
    return np.asarray(u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0])


def _segments_touch(
    p1: np.ndarray, p2: np.ndarray, q1: np.ndarray, q2: np.ndarray, scale: float
) -> bool:
    """Whether two closed segments share a point, within the drawing tolerance."""
    tol = _GEOMETRY_TOLERANCE * scale
    d1 = float(_cross(q2 - q1, p1 - q1))
    d2 = float(_cross(q2 - q1, p2 - q1))
    d3 = float(_cross(p2 - p1, q1 - p1))
    d4 = float(_cross(p2 - p1, q2 - p1))
    if ((d1 > tol and d2 < -tol) or (d1 < -tol and d2 > tol)) and (
        (d3 > tol and d4 < -tol) or (d3 < -tol and d4 > tol)
    ):
        return True
    return bool(
        np.min(_point_segment_distance(np.array([p1, p2]), q1[None], q2[None])) <= tol
        or np.min(_point_segment_distance(np.array([q1, q2]), p1[None], p2[None]))
        <= tol
    )


def _point_segment_distance(
    points: np.ndarray, starts: np.ndarray, ends: np.ndarray
) -> np.ndarray:
    """Distance from each point to each segment, shape ``(points, segments)``."""
    d = ends - starts
    length2 = np.sum(d * d, axis=1)
    rel = points[:, None, :] - starts[None, :, :]
    t = np.clip(np.sum(rel * d[None], axis=2) / length2[None], 0.0, 1.0)
    nearest = starts[None] + t[..., None] * d[None]
    return np.asarray(np.hypot(*(points[:, None, :] - nearest).T).T, dtype=np.float64)


def _inside(points: np.ndarray, polygon: np.ndarray) -> np.ndarray:
    """Even-odd test of each point against a polygon (boundary undecided)."""
    x, y = points[:, 0][:, None], points[:, 1][:, None]
    xi, yi = polygon[:, 0][None], polygon[:, 1][None]
    xj, yj = np.roll(polygon[:, 0], 1)[None], np.roll(polygon[:, 1], 1)[None]
    straddles = (yi > y) != (yj > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        x_cross = xi + (y - yi) * (xj - xi) / (yj - yi)
    crossings = np.sum(straddles & (x < x_cross), axis=1)
    return np.asarray(crossings % 2 == 1)


def _convex_hull(points: np.ndarray) -> np.ndarray:
    """Counter-clockwise convex hull (Andrew's monotone chain)."""
    pts = sorted({(float(p[0]), float(p[1])) for p in points})

    def chain(seq: list[tuple[float, float]]) -> list[tuple[float, float]]:
        out: list[tuple[float, float]] = []
        for p in seq:
            while (
                len(out) >= _POINT_SIZE
                and (
                    (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                    - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])
                )
                <= 0.0
            ):
                out.pop()
            out.append(p)
        return out

    lower = chain(pts)
    upper = chain(pts[::-1])
    return np.asarray(lower[:-1] + upper[:-1], dtype=np.float64)


def _stretch_inside_hull(
    a: np.ndarray, b: np.ndarray, hull: np.ndarray, tol: float
) -> tuple[float, float] | None:
    """The part of segment ``ab`` strictly inside a convex hull, as the
    parameters ``(t_low, t_high)`` of ``a + t (b - a)``.

    Cyrus-Beck clipping against the open hull shrunk by ``tol``: ``None``
    when the segment only touches or misses it.
    """
    starts, ends = _edges(hull)
    t_low, t_high = 0.0, 1.0
    direction = b - a
    for h0, h1 in zip(starts, ends, strict=True):
        edge = h1 - h0
        normal = np.array([-edge[1], edge[0]]) / float(np.hypot(*edge))
        offset = float(normal @ (a - h0)) - tol
        rate = float(normal @ direction)
        if abs(rate) <= _GEOMETRY_TOLERANCE * max(1.0, float(np.hypot(*direction))):
            if offset <= 0.0:
                return None
            continue
        t = -offset / rate
        if rate > 0.0:
            t_low = max(t_low, t)
        else:
            t_high = min(t_high, t)
        if t_low >= t_high:
            return None
    return t_low, t_high


def _largest_pair_angle_deg(a: np.ndarray, b: np.ndarray, hull: np.ndarray) -> float:
    r"""The largest angle two vertices of a convex hull subtend at any point
    of segment ``ab``, in degrees.

    From a point outside a convex polygon, the polygon fills the angle between
    the two vertices its tangents touch, which is the largest angle any pair
    of its vertices subtends there; so the largest aspect angle along a stretch
    of contour outside the hull is the largest, over the pairs, of the largest
    angle each pair subtends along it. For one pair :math:`V_i V_j` that is
    Regiomontanus's problem: on either side of the point :math:`X` where the
    line of the segment crosses the line :math:`V_i V_j`, the angle grows from
    zero to its greatest where a circle through :math:`V_i` and :math:`V_j`
    touches the line, at :math:`|XT|^2 = |XV_i|\,|XV_j|`, and falls away
    beyond it (at the foot of the perpendicular from the midpoint of
    :math:`V_i V_j` when the two lines are parallel). The largest on the
    segment is therefore at one of its ends or at one of those points, and
    every pair is evaluated there at once.
    """
    first, second = np.triu_indices(hull.shape[0], k=1)
    vi, vj = hull[first], hull[second]
    direction = b - a
    length2 = float(direction @ direction)
    chord = vj - vi
    rate = _cross(chord, direction[None])
    parallel = np.abs(rate) <= _GEOMETRY_TOLERANCE * np.hypot(
        chord[:, 0], chord[:, 1]
    ) * math.sqrt(length2)
    t_middle = ((0.5 * (vi + vj) - a[None]) @ direction) / length2
    # A parallel pair divides by zero here; its tangent point is t_middle.
    with np.errstate(divide="ignore", invalid="ignore"):
        t_cross = _cross(chord, vi - a[None]) / rate
        cross_point = a[None] + t_cross[:, None] * direction[None]
        reach = np.sqrt(
            np.hypot(*(cross_point - vi).T) * np.hypot(*(cross_point - vj).T)
        ) / math.sqrt(length2)
        ts = np.stack(
            [
                np.where(parallel, t_middle, t_cross + reach),
                np.where(parallel, t_middle, t_cross - reach),
                np.zeros_like(t_middle),
                np.ones_like(t_middle),
            ],
            axis=1,
        )
    ts = np.clip(np.nan_to_num(ts, nan=0.0), 0.0, 1.0)
    points = a[None, None] + ts[..., None] * direction[None, None]
    to_i = vi[:, None] - points
    to_j = vj[:, None] - points
    angles = np.arctan2(np.abs(_cross(to_i, to_j)), np.sum(to_i * to_j, axis=-1))
    return math.degrees(float(np.max(angles)))


def _ray_hits(
    origin: np.ndarray, direction: np.ndarray, starts: np.ndarray, ends: np.ndarray
) -> bool:
    """Whether a ray from ``origin`` meets any of the segments."""
    d = ends - starts
    denom = _cross(direction[None], d)
    rel = starts - origin[None]
    with np.errstate(divide="ignore", invalid="ignore"):
        s = _cross(rel, d) / denom
        t = _cross(rel, direction[None]) / denom
    hits = (np.abs(denom) > 0.0) & (s > 0.0) & (t >= 0.0) & (t <= 1.0)
    return bool(np.any(hits))


def _aspect_angle_deg(point: np.ndarray, polygon: np.ndarray) -> float:
    """The angle a polygon subtends at a point outside it, in degrees.

    The directions to the vertices, sorted, cut the circle into gaps; a gap
    no ray of which meets an edge is a direction the plant is not seen in,
    and the aspect angle is the full turn less those gaps. It exceeds 180°
    exactly when the point lies inside the convex hull of the polygon.
    """
    rel = polygon - point[None]
    angles = np.sort(np.arctan2(rel[:, 1], rel[:, 0]))
    gaps = np.diff(np.append(angles, angles[0] + 2.0 * np.pi))
    starts, ends = _edges(polygon)
    unseen = 0.0
    for start, gap in zip(angles.tolist(), gaps.tolist(), strict=True):
        if gap <= _GEOMETRY_TOLERANCE:
            continue
        middle = start + 0.5 * gap
        direction = np.array([math.cos(middle), math.sin(middle)])
        if not _ray_hits(point, direction, starts, ends):
            unseen += gap
    return math.degrees(2.0 * math.pi - unseen)


def _walk(contour: np.ndarray, count: int) -> tuple[np.ndarray, np.ndarray]:
    """``count`` equidistant points along a closed contour from its first
    vertex, and the unit normal at each pointing into the contour.

    A point that falls on a vertex takes the mean of the normals of the two
    edges that meet there.
    """
    starts, ends = _edges(contour)
    seg = ends - starts
    lengths = np.hypot(seg[:, 0], seg[:, 1])
    total = float(np.sum(lengths))
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    inward = 1.0 if _signed_area(contour) > 0.0 else -1.0
    normals = inward * np.stack([-seg[:, 1], seg[:, 0]], axis=1) / lengths[:, None]
    tol = _GEOMETRY_TOLERANCE * total
    points = np.empty((count, _POINT_SIZE))
    directions = np.empty((count, _POINT_SIZE))
    for k in range(count):
        s = total * k / count
        edge = min(
            int(np.searchsorted(cumulative, s, side="right")) - 1, lengths.size - 1
        )
        along = s - cumulative[edge]
        points[k] = starts[edge] + seg[edge] * (along / lengths[edge])
        normal = normals[edge]
        if along <= tol:
            normal = normal + normals[edge - 1]
            normal = normal / float(np.hypot(*normal))
        directions[k] = normal
    return points, directions


# --------------------------------------------------------------------------- #
# The measurement contour
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlantMeasurementContour(OwnsArrays):
    r"""A measurement contour round a plant area on the plot plan, clauses 9.1 to 9.4.

    The plant area and the contour are polygons in metres, in any consistent
    plane coordinates; the contour encloses the plant and does not touch it.
    The layout is ``position_count`` positions spaced equally along the
    contour from its first vertex (9.1.2.4, :math:`D_\mathrm{m} = l/N`), of
    which those listed in ``omitted_positions`` could not be measured; every
    quantity below is taken over the positions that were.

    :ivar plant_outline_m: Vertices of the plant area, ``(n, 2)``, in metres.
    :ivar contour_m: Vertices of the measurement contour, ``(n, 2)``, in
        metres.
    :ivar characteristic_height_m: :math:`H`, in metres (9.2 c).
    :ivar position_count: Positions in the equidistant layout.
    :ivar omitted_positions: Indices into the layout of the positions left out
        (9.1.2.4), in increasing order.
    """

    plant_outline_m: NDArray[np.float64]
    contour_m: NDArray[np.float64]
    characteristic_height_m: float
    position_count: int
    omitted_positions: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """Reject a contour that is not a closed path round the plant area.

        Every quantity of the method is measured between these two polygons,
        so the checks are made where they are built: each is a simple
        polygon, every vertex of the plant area lies inside the contour, and
        no edge of the one touches an edge of the other. The layout needs at
        least three positions and at least one of them measured.

        :raises ValueError: for either polygon malformed, a contour that does
            not enclose the plant area or touches it, a negative height, or a
            layout that leaves nothing to measure.
        """
        # The record's own copies of the caller's arrays, made before this
        # hook runs, sealed: every derived quantity is read from these, and
        # some are cached, so they must not change afterwards.
        plant = read_only(np.asarray(_polygon(self.plant_outline_m, "plant_outline_m")))
        contour = read_only(np.asarray(_polygon(self.contour_m, "contour_m")))
        object.__setattr__(self, "plant_outline_m", plant)
        object.__setattr__(self, "contour_m", contour)
        height = require_finite(self.characteristic_height_m, "characteristic_height_m")
        if height < 0.0:
            msg = "'characteristic_height_m' must be >= 0 m."
            raise ValueError(msg)
        count = require_count(
            self.position_count, "position_count", minimum=_MIN_POSITIONS
        )
        omitted = tuple(
            require_count(i, "omitted_positions", minimum=0)
            for i in self.omitted_positions
        )
        if list(omitted) != sorted(set(omitted)) or any(i >= count for i in omitted):
            msg = (
                "'omitted_positions' must list distinct indices into the layout "
                f"of {count} positions, in increasing order."
            )
            raise ValueError(msg)
        if len(omitted) >= count:
            msg = "'omitted_positions' leaves no position to measure."
            raise ValueError(msg)
        object.__setattr__(self, "omitted_positions", omitted)
        if not np.all(_inside(plant, contour)):
            msg = "'contour_m' must enclose every vertex of 'plant_outline_m'."
            raise ValueError(msg)
        scale = float(np.max(np.ptp(contour, axis=0)))
        p_starts, p_ends = _edges(plant)
        c_starts, c_ends = _edges(contour)
        for i in range(plant.shape[0]):
            for j in range(contour.shape[0]):
                if _segments_touch(
                    p_starts[i], p_ends[i], c_starts[j], c_ends[j], scale
                ):
                    msg = (
                        "'contour_m' must not touch 'plant_outline_m': the "
                        "measurement distance of 9.1.2.2 is then zero."
                    )
                    raise ValueError(msg)

    @cached_property
    def _layout(self) -> tuple[np.ndarray, np.ndarray]:
        """Every position of the layout and its inward normal."""
        points, normals = _walk(self.contour_m, self.position_count)
        return read_only(points), read_only(normals)

    @cached_property
    def measured(self) -> NDArray[np.bool_]:
        """Per layout position, whether it was measured (not omitted)."""
        mask = np.ones(self.position_count, dtype=bool)
        mask[list(self.omitted_positions)] = False
        return read_only(mask)

    @property
    def layout_positions_m(self) -> NDArray[np.float64]:
        """Every position of the equidistant layout, omitted ones included,
        ``(position_count, 2)``, in metres.
        """
        return np.array(self._layout[0], dtype=np.float64)

    @cached_property
    def positions_m(self) -> NDArray[np.float64]:
        """The measured positions, ``(N, 2)``, in metres."""
        return read_only(np.array(self._layout[0][self.measured], dtype=np.float64))

    @cached_property
    def microphone_directions(self) -> NDArray[np.float64]:
        """Unit vectors of the microphone reference direction at each measured
        position: horizontal, at 90° to the contour, towards the plant (9.4).
        """
        return read_only(np.array(self._layout[1][self.measured], dtype=np.float64))

    @cached_property
    def distances_m(self) -> NDArray[np.float64]:
        """:math:`d_i`, from each measured position to the nearest point of the
        plant perimeter, in metres (3.5, 9.1.2.2).
        """
        starts, ends = _edges(self.plant_outline_m)
        return read_only(
            np.min(_point_segment_distance(self.positions_m, starts, ends), axis=1)
        )

    @property
    def nearest_perimeter_points_m(self) -> NDArray[np.float64]:
        """The point of the plant perimeter nearest each measured position,
        ``(N, 2)``, in metres: the other end of each :math:`d_i`.
        """
        starts, ends = _edges(self.plant_outline_m)
        seg = ends - starts
        rel = self.positions_m[:, None, :] - starts[None]
        t = np.clip(
            np.sum(rel * seg[None], axis=2) / np.sum(seg * seg, axis=1), 0.0, 1.0
        )
        candidates = starts[None] + t[..., None] * seg[None]
        gaps = np.hypot(*(self.positions_m[:, None, :] - candidates).T).T
        pick = np.argmin(gaps, axis=1)
        return np.asarray(candidates[np.arange(pick.size), pick], dtype=np.float64)

    @cached_property
    def aspect_angles_deg(self) -> NDArray[np.float64]:
        r""":math:`\phi` at each measured position, the angle the plant area
        subtends there, in degrees (9.1.1 b).
        """
        return read_only(
            np.array(
                [_aspect_angle_deg(p, self.plant_outline_m) for p in self.positions_m],
                dtype=np.float64,
            )
        )

    @cached_property
    def enters_convex_hull(self) -> bool:
        """Whether any stretch of the contour runs inside the convex hull of the
        plant area, where the aspect angle exceeds 180° and 9.1.1 b) fails.
        """
        hull = _convex_hull(self.plant_outline_m)
        tol = _GEOMETRY_TOLERANCE * float(np.max(np.ptp(self.contour_m, axis=0)))
        starts, ends = _edges(self.contour_m)
        return any(
            _stretch_inside_hull(a, b, hull, tol) is not None
            for a, b in zip(starts, ends, strict=True)
        )

    @cached_property
    def largest_aspect_angle_deg(self) -> float:
        """The largest aspect angle on the contour, in degrees.

        9.1.1 b) asks it of *any point* of the contour, not only of the
        positions. Along the contour outside the convex hull of the plant
        area the maximum is found exactly: on each edge it lies at an end or
        where a circle through two vertices of the hull touches the edge.
        Where the contour runs inside the hull (:attr:`enters_convex_hull`),
        the angle there exceeds 180°, and the value is the largest found at
        the positions, the vertices and 17 points spread along each stretch
        inside: above 180°, which is what fails the clause, but a lower bound
        of the maximum there rather than the maximum itself.
        """
        plant = self.plant_outline_m
        hull = _convex_hull(plant)
        tol = _GEOMETRY_TOLERANCE * float(np.max(np.ptp(self.contour_m, axis=0)))
        candidates = [*self.positions_m, *self.contour_m]
        largest = 0.0
        starts, ends = _edges(self.contour_m)
        for a, b in zip(starts, ends, strict=True):
            largest = max(largest, _largest_pair_angle_deg(a, b, hull))
            stretch = _stretch_inside_hull(a, b, hull, tol)
            if stretch is not None:
                inside = np.linspace(*stretch, _INSIDE_SAMPLES + 2)[1:-1]
                candidates.extend(a + t * (b - a) for t in inside)
        return max(largest, *(_aspect_angle_deg(p, plant) for p in candidates))

    @property
    def plant_area_m2(self) -> float:
        r""":math:`S_\mathrm{p}`, the plant area, in square metres (3.3)."""
        return abs(_signed_area(self.plant_outline_m))

    @property
    def measurement_area_m2(self) -> float:
        r""":math:`S_\mathrm{m}`, the total area the contour encloses, plant
        included, in square metres (3.4).
        """
        return abs(_signed_area(self.contour_m))

    @property
    def contour_length_m(self) -> float:
        """:math:`l`, the length of the contour, in metres (9.2 a)."""
        starts, ends = _edges(self.contour_m)
        return float(np.sum(np.hypot(*(ends - starts).T)))

    @property
    def position_spacing_m(self) -> float:
        r""":math:`D_\mathrm{m}`, the distance between adjacent positions of the
        layout along the contour, in metres (3.6).
        """
        return self.contour_length_m / self.position_count

    @property
    def mean_distance_m(self) -> float:
        r""":math:`\bar{d}`, the average measurement distance, in metres (9.1.2.2)."""
        return float(np.mean(self.distances_m))

    @property
    def distance_ratio(self) -> float:
        r""":math:`\bar{d}/\sqrt{S_\mathrm{p}}`, the argument of Table 1."""
        return self.mean_distance_m / math.sqrt(self.plant_area_m2)

    @property
    def omitted_percent(self) -> float:
        """The share of the layout left out, in percent (9.1.2.4)."""
        return 100.0 * len(self.omitted_positions) / self.position_count

    @property
    def largest_plant_dimension_m(self) -> float:
        """The largest horizontal dimension of the plant area, in metres (1.2)."""
        rel = self.plant_outline_m[:, None, :] - self.plant_outline_m[None, :, :]
        return float(np.max(np.hypot(rel[..., 0], rel[..., 1])))

    @property
    def plant_centre_m(self) -> NDArray[np.float64]:
        """The geometrical centre of the plant area, where 0.2 a) places the
        point source that stands for the plant, in metres.
        """
        v = self.plant_outline_m
        cross = v[:, 0] * np.roll(v[:, 1], -1) - np.roll(v[:, 0], -1) * v[:, 1]
        area = 0.5 * float(np.sum(cross))
        cx = float(np.sum((v[:, 0] + np.roll(v[:, 0], -1)) * cross)) / (6.0 * area)
        cy = float(np.sum((v[:, 1] + np.roll(v[:, 1], -1)) * cross)) / (6.0 * area)
        return np.array([cx, cy])

    @property
    def minimum_receiver_distance_m(self) -> float:
        """The distance from the plant centre beyond which 0.2 a) lets the
        result stand for a point source: 1,5 times the largest dimension, in
        metres.
        """
        return _RECEIVER_DISTANCE_FACTOR * self.largest_plant_dimension_m

    @property
    def prescribed_microphone_height_m(self) -> float:
        """:math:`h` of 9.3 for this contour and plant, in metres."""
        return plant_microphone_height_m(
            self.characteristic_height_m, self.measurement_area_m2
        )

    @property
    def mean_distance_limits_m(self) -> tuple[float, float]:
        """The window of 9.1.1 a) for this plant area, in metres."""
        return plant_mean_distance_limits_m(self.plant_area_m2)

    def sound_power(
        self,
        levels_db: ArrayLike,
        frequencies_hz: ArrayLike,
        *,
        microphone_height_m: float | None = None,
        background_levels_db: ArrayLike | None = None,
        directional_microphone_angle_deg: float | ArrayLike | None = None,
        temperature_c: float | None = None,
        relative_humidity_percent: float | None = None,
    ) -> PlantSoundPowerResult:
        """Run clause 10 on the levels read at the measured positions of this contour.

        :func:`plant_sound_power` with the geometry of the contour; see there.

        :param levels_db: One row per measured position, in the order of
            :attr:`positions_m`, one column per octave band, in decibels.
        :param frequencies_hz: The octave-band centres of the columns, in Hz.
        :param microphone_height_m: The height the microphones stood at, in
            metres; ``None`` for the height 9.3 prescribes.
        :param background_levels_db: The background alone, same shape, or
            ``None``.
        :param directional_microphone_angle_deg: The 3 dB angle of a
            directional microphone, one or one per band, or ``None``.
        :param temperature_c: Air temperature at the measurement, in °C, or
            ``None`` for Table 3.
        :param relative_humidity_percent: Relative humidity at the measurement,
            in percent, or ``None`` for Table 3.
        :return: A :class:`PlantSoundPowerResult`.
        :raises ValueError: for a number of rows that is not the number of
            measured positions, or any error of :func:`plant_sound_power`.
        """
        levels = require_finite_matrix(levels_db, "levels_db")
        if levels.shape[0] != self.positions_m.shape[0]:
            msg = (
                f"'levels_db' has {levels.shape[0]} rows for "
                f"{self.positions_m.shape[0]} measured positions."
            )
            raise ValueError(msg)
        height = (
            self.prescribed_microphone_height_m
            if microphone_height_m is None
            else microphone_height_m
        )
        return plant_sound_power(
            levels,
            frequencies_hz,
            measurement_area_m2=self.measurement_area_m2,
            contour_length_m=self.contour_length_m,
            microphone_height_m=height,
            mean_distance_m=self.mean_distance_m,
            plant_area_m2=self.plant_area_m2,
            background_levels_db=background_levels_db,
            directional_microphone_angle_deg=directional_microphone_angle_deg,
            temperature_c=temperature_c,
            relative_humidity_percent=relative_humidity_percent,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the plan: plant area, contour, positions and their microphone
        directions, in the manner of Figure 1.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the position markers.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.emission_plant import plot_plant_contour

        return plot_plant_contour(
            self, ax=ax, language=check_language(language), **kwargs
        )


def plant_measurement_contour(
    plant_outline_m: ArrayLike,
    contour_m: ArrayLike,
    *,
    characteristic_height_m: float,
    position_count: int | None = None,
    omitted_positions: Sequence[int] = (),
) -> PlantMeasurementContour:
    r"""Lay the measurement positions on a contour round the plant area, 9.1.

    The positions are spaced equally along the contour from its first vertex.
    With no ``position_count``, the layout is the smallest that meets 9.1.1 c),
    :math:`D_\mathrm{m} = l/N \le 2\bar{d}`, with :math:`\bar{d}` taken over
    that same layout, from three positions up. A layout of your own is given
    as ``position_count``, and the positions that could not be measured, a
    river or a building in the way (9.1.2.4), as ``omitted_positions``.

    The contour is not required to meet 9.1.1 here: a first contour drawn on
    the plan and found wanting is how the procedure starts (9.1.2.3, NOTE 6).
    :func:`check_plant_measurement` says whether it does.

    :param plant_outline_m: Vertices of the plant area, in metres.
    :param contour_m: Vertices of the measurement contour round it, in metres.
    :param characteristic_height_m: :math:`H`, in metres, from
        :func:`plant_characteristic_height_m`.
    :param position_count: Positions in the layout, or ``None`` for the
        fewest 9.1.1 c) allows.
    :param omitted_positions: Indices into the layout of positions not
        measured; needs ``position_count``, since the indices refer to it.
    :return: A :class:`PlantMeasurementContour`.
    :raises ValueError: for polygons that do not form a contour round the plant
        area, or omitted positions without a layout to refer to.
    """
    omitted = tuple(omitted_positions)
    if position_count is not None:
        return PlantMeasurementContour(
            np.asarray(plant_outline_m, dtype=np.float64),
            np.asarray(contour_m, dtype=np.float64),
            characteristic_height_m,
            position_count,
            omitted,
        )
    if omitted:
        msg = "'omitted_positions' index a layout; give its 'position_count' with them."
        raise ValueError(msg)
    first = PlantMeasurementContour(
        np.asarray(plant_outline_m, dtype=np.float64),
        np.asarray(contour_m, dtype=np.float64),
        characteristic_height_m,
        _MIN_POSITIONS,
    )
    # d_i is never below the smallest distance between the two outlines, so
    # a spacing of twice that meets 9.1.1 c) whatever the layout.
    p_starts, p_ends = _edges(first.plant_outline_m)
    c_starts, c_ends = _edges(first.contour_m)
    gap = min(
        float(np.min(_point_segment_distance(first.contour_m, p_starts, p_ends))),
        float(np.min(_point_segment_distance(first.plant_outline_m, c_starts, c_ends))),
    )
    ceiling = max(_MIN_POSITIONS, math.ceil(first.contour_length_m / (2.0 * gap)))
    # Nor is d_i ever above the distance to any one plant vertex, which along a
    # contour edge is largest at an end of it: no layout below l / (2 reach)
    # can meet 9.1.1 c), so the search starts there rather than at three.
    reach = min(
        float(np.max(np.hypot(*(first.contour_m - vertex).T)))
        for vertex in first.plant_outline_m
    )
    floor = max(_MIN_POSITIONS, math.ceil(first.contour_length_m / (2.0 * reach)))
    for count in range(min(floor, ceiling), ceiling + 1):
        layout = PlantMeasurementContour(
            first.plant_outline_m, first.contour_m, characteristic_height_m, count
        )
        # Judged settled, as the 9.1.1 c) row of the report judges it.
        excess = layout.position_spacing_m - (
            _SPACING_PER_MEAN_DISTANCE * layout.mean_distance_m
        )
        if is_at_most(float(settled(excess)), 0.0):
            return layout
    return PlantMeasurementContour(
        first.plant_outline_m, first.contour_m, characteristic_height_m, ceiling
    )


# --------------------------------------------------------------------------- #
# Clause 10: the sound power level
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlantSoundPowerResult(OwnsArrays):
    r"""The sound power level of a plant for the evaluation of levels in the
    environment, clause 10 of ISO 8297.

    The fields are the readings and the geometry the calculation was made
    from; every step of clause 10 is derived from them on request, so a
    result cannot carry a level that disagrees with its own inputs.

    :ivar frequencies_hz: Nominal octave-band centres, in Hz.
    :ivar measured_levels_db: The levels read at the :math:`N` positions with
        the plant operating, ``(N, bands)``, in dB re 20 µPa.
    :ivar background_levels_db: The background alone at the same positions,
        or ``None`` when it could not be measured (9.5.4).
    :ivar measurement_area_m2: :math:`S_\mathrm{m}`, in square metres.
    :ivar contour_length_m: :math:`l`, in metres.
    :ivar microphone_height_m: :math:`h`, the height the microphones stood
        at, in metres.
    :ivar mean_distance_m: :math:`\bar{d}`, in metres.
    :ivar plant_area_m2: :math:`S_\mathrm{p}`, in square metres.
    :ivar directional_microphone_angle_deg: :math:`\theta` per band, or
        ``None`` for an omnidirectional microphone.
    :ivar temperature_c: Air temperature for the air absorption, in °C, or
        ``None`` for Table 3.
    :ivar relative_humidity_percent: Relative humidity for the air absorption,
        in percent, or ``None`` for Table 3.
    """

    frequencies_hz: NDArray[np.float64]
    measured_levels_db: NDArray[np.float64]
    background_levels_db: NDArray[np.float64] | None
    measurement_area_m2: float
    contour_length_m: float
    microphone_height_m: float
    mean_distance_m: float
    plant_area_m2: float
    _: KW_ONLY
    directional_microphone_angle_deg: NDArray[np.float64] | None = None
    temperature_c: float | None = None
    relative_humidity_percent: float | None = None

    def __post_init__(self) -> None:
        """Reject readings that clause 10 cannot turn into a sound power.

        The bands must be octaves of the method and include at least one the
        A-weighting of 10.9 reads; the levels and the background run one row
        per position and one column per band; the geometry is positive; the
        background, where given, stands at least 6 dB below every level,
        since Table 2 has no correction below that; and the weather is given
        whole or not at all.

        :raises ValueError: for any of the above.
        """
        bands = read_only(_octave_bands(self.frequencies_hz))
        object.__setattr__(self, "frequencies_hz", bands)
        # The record's own copies, sealed: every step of clause 10 is derived
        # from these on request, so a later write to the caller's array must
        # not reach them.
        levels = read_only(
            np.asarray(
                require_finite_matrix(self.measured_levels_db, "measured_levels_db")
            )
        )
        if levels.shape[1] != bands.size:
            msg = (
                f"'measured_levels_db' has {levels.shape[1]} columns for "
                f"{bands.size} octave bands."
            )
            raise ValueError(msg)
        object.__setattr__(self, "measured_levels_db", levels)
        if not any(float(b) in _A_WEIGHTED_BANDS_HZ for b in bands):
            msg = (
                "The bands must include at least one from 63 Hz to 8 kHz, which "
                "the A-weighting of 10.9 reads."
            )
            raise ValueError(msg)
        if self.background_levels_db is not None:
            background = read_only(
                np.asarray(
                    require_finite_matrix(
                        self.background_levels_db, "background_levels_db"
                    )
                )
            )
            if background.shape != levels.shape:
                msg = (
                    "'background_levels_db' must match 'measured_levels_db', one "
                    "row per position and one column per band."
                )
                raise ValueError(msg)
            plant_background_correction_db(levels - background)
            object.__setattr__(self, "background_levels_db", background)
        for name in (
            "measurement_area_m2",
            "contour_length_m",
            "microphone_height_m",
            "mean_distance_m",
            "plant_area_m2",
        ):
            object.__setattr__(self, name, require_positive(getattr(self, name), name))
        angles = _directional_angles(self.directional_microphone_angle_deg, bands.size)
        object.__setattr__(
            self,
            "directional_microphone_angle_deg",
            None if angles is None else read_only(np.asarray(angles)),
        )
        theta, humidity = _weather(self.temperature_c, self.relative_humidity_percent)
        object.__setattr__(self, "temperature_c", theta)
        object.__setattr__(self, "relative_humidity_percent", humidity)

    @property
    def background_margin_db(self) -> NDArray[np.float64] | None:
        """The level with the plant operating less the background, per position
        and band, in decibels; ``None`` with no background.
        """
        if self.background_levels_db is None:
            return None
        return np.asarray(
            self.measured_levels_db - self.background_levels_db, dtype=np.float64
        )

    @property
    def background_correction_db(self) -> NDArray[np.float64] | None:
        """The Table 2 correction subtracted at each position and band, in
        decibels; ``None`` with no background.
        """
        margin = self.background_margin_db
        if margin is None:
            return None
        return np.asarray(plant_background_correction_db(margin), dtype=np.float64)

    @property
    def levels_db(self) -> NDArray[np.float64]:
        """:math:`L_{pi}`, the levels corrected for the background (9.5.4),
        ``(N, bands)``, in decibels.
        """
        correction = self.background_correction_db
        if correction is None:
            return np.array(self.measured_levels_db, dtype=np.float64)
        return np.asarray(self.measured_levels_db - correction, dtype=np.float64)

    @property
    def mean_level_db(self) -> NDArray[np.float64]:
        r""":math:`\overline{L_p}`, the energy average round the contour, per band
        (10.1), in decibels.
        """
        return energy_mean(self.levels_db, axis=0)

    @property
    def capped(self) -> NDArray[np.bool_]:
        r"""Per position and band, whether :math:`L_{pi}` exceeds
        :math:`\overline{L_p}` by more than 5 dB and was replaced (10.2).

        The excess is settled to nine decimals first: a level 5 dB above the
        energy mean comes out of the arithmetic a unit or two of the last
        place of the levels either side of 5, which side depending on the
        machine, and is not replaced.
        """
        excess = settled(self.levels_db - self.mean_level_db)
        return np.asarray(excess > _EXCESS_LIMIT_DB, dtype=bool)

    @property
    def steps_2_3_applied(self) -> bool:
        r"""Whether 10.2 and 10.3 changed anything: then
        :math:`\overline{L_p^*}` replaces :math:`\overline{L_p}` in 10.8.
        """
        return bool(np.any(self.capped))

    @property
    def corrected_mean_level_db(self) -> NDArray[np.float64]:
        r""":math:`\overline{L_p^*}` of 10.3, the average after replacing each
        capped level by :math:`\overline{L_p} + 5` dB; equal to
        :math:`\overline{L_p}` in a band with nothing capped.
        """
        cap = self.mean_level_db + _EXCESS_LIMIT_DB
        return energy_mean(np.where(self.capped, cap, self.levels_db), axis=0)

    @property
    def area_term_db(self) -> float:
        r""":math:`\Delta L_\mathrm{S} = 10 \lg[(2S_\mathrm{m} + hl)/S_0]`, in
        decibels (10.4).
        """
        surface = (
            2.0 * self.measurement_area_m2
            + self.microphone_height_m * self.contour_length_m
        )
        return 10.0 * math.log10(surface / _S0)

    @property
    def near_field_term_db(self) -> float:
        r""":math:`\Delta L_\mathrm{F} = \lg[\bar{d}/(4\sqrt{S_\mathrm{p}})]`,
        in decibels (10.5).
        """
        return math.log10(
            self.mean_distance_m / (_NEAR_FIELD_FACTOR * math.sqrt(self.plant_area_m2))
        )

    @property
    def microphone_term_db(self) -> NDArray[np.float64]:
        r""":math:`\Delta L_\mathrm{M} = 3(1 - \theta/90)` per band, 0 for an
        omnidirectional microphone, in decibels (10.6).
        """
        theta = self.directional_microphone_angle_deg
        if theta is None:
            return np.zeros(self.frequencies_hz.size)
        return np.asarray(
            _MICROPHONE_TERM_DB * (1.0 - theta / _RIGHT_ANGLE_DEG), dtype=np.float64
        )

    @cached_property
    def _alpha(self) -> NDArray[np.float64]:
        r""":math:`\alpha` per band, evaluated once."""
        return read_only(
            plant_air_absorption_db_per_m(
                self.frequencies_hz,
                temperature_c=self.temperature_c,
                relative_humidity_percent=self.relative_humidity_percent,
            )
        )

    @property
    def air_absorption_db_per_m(self) -> NDArray[np.float64]:
        r""":math:`\alpha` per band, in dB/m (10.7, Table 3)."""
        return np.array(self._alpha, dtype=np.float64)

    @property
    def air_absorption_term_db(self) -> NDArray[np.float64]:
        r""":math:`\Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}` per
        band, in decibels (10.7).
        """
        return np.asarray(
            _AIR_TERM_FACTOR
            * self.air_absorption_db_per_m
            * math.sqrt(self.measurement_area_m2),
            dtype=np.float64,
        )

    @property
    def sound_power_level_db(self) -> NDArray[np.float64]:
        """:math:`L_W` per octave band, in dB re 1 pW (10.8)."""
        return np.asarray(
            self.corrected_mean_level_db
            + self.area_term_db
            + self.near_field_term_db
            + self.microphone_term_db
            + self.air_absorption_term_db,
            dtype=np.float64,
        )

    @property
    def a_weighted_bands_hz(self) -> NDArray[np.float64]:
        r"""The bands summed into :math:`L_{W\mathrm{A}}`: those the octave table
        of ISO 3744:2010 Annex E weights, 63 Hz to 8 kHz. A 31,5 Hz band, which
        NOTE 8 makes optional, is left out.
        """
        keep = np.isin(self.frequencies_hz, _A_WEIGHTED_BANDS_HZ)
        return np.array(self.frequencies_hz[keep], dtype=np.float64)

    @property
    def a_weighted_sound_power_level_db(self) -> float:
        r""":math:`L_{W\mathrm{A}} = 10 \lg \sum_j 10^{0{,}1(L_{Wj} + C_j)}`, in
        dB re 1 pW (10.9).
        """
        keep = np.isin(self.frequencies_hz, _A_WEIGHTED_BANDS_HZ)
        bands = self.frequencies_hz[keep]
        return energy_sum(
            self.sound_power_level_db[keep] + _a_weighting_corrections(bands)
        )

    @property
    def distance_ratio(self) -> float:
        r""":math:`\bar{d}/\sqrt{S_\mathrm{p}}`, the argument of Table 1."""
        return self.mean_distance_m / math.sqrt(self.plant_area_m2)

    @property
    def uncertainty_db(self) -> tuple[float, float] | None:
        """The 95 % interval of Table 1 as ``(lower, upper)`` in decibels, or
        ``None`` where the distance ratio is outside the table (and outside
        9.1.1 a).
        """
        try:
            return plant_method_uncertainty_db(self.distance_ratio)
        except ValueError:
            return None

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the octave-band :math:`L_W` beside the contour average it was
        built from, with :math:`L_{W\mathrm{A}}` in the title.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band bars.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.emission_plant import plot_plant_sound_power

        return plot_plant_sound_power(
            self, ax=ax, language=check_language(language), **kwargs
        )


def plant_sound_power(
    levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    measurement_area_m2: float,
    contour_length_m: float,
    microphone_height_m: float,
    mean_distance_m: float,
    plant_area_m2: float,
    background_levels_db: ArrayLike | None = None,
    directional_microphone_angle_deg: float | ArrayLike | None = None,
    temperature_c: float | None = None,
    relative_humidity_percent: float | None = None,
) -> PlantSoundPowerResult:
    r"""The octave-band and A-weighted sound power level of a plant, clause 10.

    Steps 1 to 9 of clause 10 on the levels read round the contour. With a
    background given, every level is first corrected by Table 2 (9.5.4). The
    levels are energy-averaged per band (step 1); where one exceeds the
    average by more than 5 dB, 10.2 asks for a contour further from the
    plant, and where that is not practicable replaces each such level by the
    average plus 5 dB and averages again (steps 2 and 3), which is done here
    with a :class:`SoundPowerWarning`, the result recording which levels were
    replaced. Steps 4 to 7 add the area, proximity, microphone and air
    absorption terms, step 8 sums them into :math:`L_W` and step 9 into
    :math:`L_{W\mathrm{A}}`; the module docstring writes them out.

    The geometry is the one 9.2 measures on the plot plan, to within ±5 %;
    :meth:`PlantMeasurementContour.sound_power` supplies it from polygons.

    :param levels_db: :math:`L_{pi}`, one row per position and one column per
        octave band, in dB re 20 µPa.
    :param frequencies_hz: Nominal octave-band centres of the columns, 31,5 Hz
        to 8 kHz.
    :param measurement_area_m2: :math:`S_\mathrm{m}`, in square metres.
    :param contour_length_m: :math:`l`, in metres.
    :param microphone_height_m: :math:`h`, the height the microphones stood at,
        in metres.
    :param mean_distance_m: :math:`\bar{d}`, in metres.
    :param plant_area_m2: :math:`S_\mathrm{p}`, in square metres.
    :param background_levels_db: The background alone at each position and
        band, in decibels, or ``None`` where the plant could not be stopped.
    :param directional_microphone_angle_deg: :math:`\theta`, the angle at which
        a directional microphone has lost 3 dB, in degrees, one value or one
        per band; ``None`` (default) for an omnidirectional microphone.
    :param temperature_c: Air temperature at the measurement, in °C, or
        ``None`` for Table 3 at 15 °C. Pass it, with the humidity, only when
        the weather differs markedly from 15 °C and 70 %: the formula does not
        return Table 3 at those conditions, and passing them gives
        :math:`0{,}0074\sqrt{S_\mathrm{m}}` dB more at 8 kHz than omitting
        them (see :func:`plant_air_absorption_db_per_m`).
    :param relative_humidity_percent: Relative humidity at the measurement, in
        percent, or ``None`` for Table 3 at 70 %.
    :return: A :class:`PlantSoundPowerResult`.
    :raises ValueError: for levels that do not match the bands, a background
        less than 6 dB below a level, a non-positive geometry, a microphone
        angle outside (0°, 90°], or half a weather.
    """
    result = PlantSoundPowerResult(
        frequencies_hz=np.asarray(frequencies_hz, dtype=np.float64),
        measured_levels_db=require_finite_matrix(levels_db, "levels_db"),
        background_levels_db=(
            None
            if background_levels_db is None
            else require_finite_matrix(background_levels_db, "background_levels_db")
        ),
        measurement_area_m2=measurement_area_m2,
        contour_length_m=contour_length_m,
        microphone_height_m=microphone_height_m,
        mean_distance_m=mean_distance_m,
        plant_area_m2=plant_area_m2,
        directional_microphone_angle_deg=(
            None
            if directional_microphone_angle_deg is None
            else np.asarray(directional_microphone_angle_deg, dtype=np.float64)
        ),
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
    )
    if result.steps_2_3_applied:
        rows, cols = np.nonzero(result.capped)
        cells = ", ".join(
            f"position {r} at {result.frequencies_hz[c]:g} Hz"
            for r, c in zip(rows.tolist(), cols.tolist(), strict=True)
        )
        msg = (
            f"ISO 8297 10.2: a level exceeds the contour average by more than "
            f"{_EXCESS_LIMIT_DB:g} dB ({cells}). The clause asks for a contour "
            "further from the plant; where that is not practicable it replaces "
            "those levels by the average plus 5 dB, as done here (10.3)."
        )
        warnings.warn(msg, SoundPowerWarning, stacklevel=2)
    return result


# --------------------------------------------------------------------------- #
# The verdict
# --------------------------------------------------------------------------- #

#: The comparisons a requirement can make of its value with its limit; "="
#: holds within the requirement's tolerance.
_COMPARISONS = (">", ">=", "<=", "=")


@dataclass(frozen=True)
class PlantRequirement:
    """One requirement of ISO 8297 held against the measurement.

    :ivar key: A stable identifier, such as ``"mean_distance_min"``.
    :ivar clause: The clause that sets it, such as ``"9.1.1 a)"``; the
        omitted positions also name the item of clause 12 that reports them,
        ``"9.1.2.4, 12 n)"``.
    :ivar description: What is compared, in English.
    :ivar value: The measured value, in :attr:`unit`.
    :ivar comparison: How the value must stand to the limit: ``">"``,
        ``">="``, ``"<="``, or ``"="`` for a value prescribed to within
        :attr:`tolerance` of the limit.
    :ivar limit: The limit, in :attr:`unit`.
    :ivar unit: The unit of the value and the limit, ``""`` for a count.
    :ivar holds: Whether the requirement is met.
    :ivar advisory: ``True`` where the standard allows the requirement to go
        unmet provided the report says so (the microphone height of 9.3, the
        preferred background margin of 6 b), the contour average of 10.2, the
        "approximately 320 m" of 1.2); such a requirement does not decide
        :attr:`PlantMeasurementCheck.passes`.
    :ivar tolerance: For ``"="``, how far the value may stand from the limit,
        in :attr:`unit`; 0 for the other comparisons.
    """

    key: str
    clause: str
    description: str
    value: float
    comparison: str
    limit: float
    unit: str
    holds: bool
    advisory: bool = False
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        """Reject a comparison the verdict cannot draw.

        :raises ValueError: for a comparison outside ``">"``, ``">="``,
            ``"<="`` and ``"="``, or a negative tolerance.
        """
        if self.comparison not in _COMPARISONS:
            msg = (
                f"'comparison' must be one of {_COMPARISONS}; got {self.comparison!r}."
            )
            raise ValueError(msg)
        if math.isnan(self.tolerance) or self.tolerance < 0.0:
            msg = f"'tolerance' must be >= 0; got {self.tolerance!r}."
            raise ValueError(msg)

    @property
    def margin(self) -> float:
        """How far the value is inside the limit, as a fraction of the limit:
        positive where it holds by the comparison, negative where it does not.
        For ``"="`` it is the room left inside the tolerance.
        """
        scale = abs(self.limit) if abs(self.limit) > 0.0 else 1.0
        if self.comparison == "=":
            return (self.tolerance - abs(self.value - self.limit)) / scale
        sign = -1.0 if self.comparison == "<=" else 1.0
        return sign * (self.value - self.limit) / scale


def _row(
    key: str,
    clause: str,
    description: str,
    value: float,
    comparison: str,
    limit: float,
    unit: str,
    *,
    advisory: bool = False,
    holds: bool | None = None,
    tolerance: float = 0.0,
) -> PlantRequirement:
    """A requirement row, its verdict computed from the comparison unless given."""
    if holds is None:
        # Judged on the settled difference: a spacing of 10,2 m worked from a
        # contour of 163,2 m in 16 positions is twice a mean distance of 5,1 m
        # whichever way the last bits of either fall.
        margin = float(settled(value - limit))
        if comparison == ">":
            holds = margin > 0.0
        elif comparison == ">=":
            holds = margin >= 0.0
        elif comparison == "=":
            holds = is_at_most(float(settled(abs(value - limit) - tolerance)), 0.0)
        else:
            holds = is_at_most(margin, 0.0)
    return PlantRequirement(
        key=key,
        clause=clause,
        description=description,
        value=float(value),
        comparison=comparison,
        limit=float(limit),
        unit=unit,
        holds=bool(holds),
        advisory=advisory,
        tolerance=float(tolerance),
    )


@dataclass(frozen=True)
class PlantMeasurementCheck:
    """The arrangement and the readings of an ISO 8297 measurement against the
    requirements of the standard.

    :ivar requirements: One :class:`PlantRequirement` per requirement that
        could be evaluated, in the order of the clauses.
    """

    requirements: tuple[PlantRequirement, ...]

    @property
    def passes(self) -> bool:
        """Whether every requirement that is not advisory holds.

        True says the contour, the positions, the microphones and the readings
        meet what ISO 8297 requires of them; the advisory rows that do not
        hold (:attr:`deviations`) still go in the report.
        """
        return all(r.holds for r in self.requirements if not r.advisory)

    @property
    def failures(self) -> tuple[PlantRequirement, ...]:
        """The requirements that are not advisory and do not hold."""
        return tuple(r for r in self.requirements if not r.advisory and not r.holds)

    @property
    def deviations(self) -> tuple[PlantRequirement, ...]:
        """The advisory requirements that do not hold, which the report states."""
        return tuple(r for r in self.requirements if r.advisory and not r.holds)

    def requirement(self, key: str) -> PlantRequirement:
        """The requirement with this key.

        :param key: Its :attr:`PlantRequirement.key`.
        :return: The requirement.
        :raises KeyError: for a key this check does not carry.
        """
        for r in self.requirements:
            if r.key == key:
                return r
        raise KeyError(key)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        An object is always true, so ``if check_plant_measurement(...):`` would
        pass every measurement. The verdict is :attr:`passes`.

        :raises TypeError: Always.
        """
        msg = (
            "a PlantMeasurementCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot how far each requirement is inside or outside its limit.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.emission_plant import plot_plant_measurement_check

        return plot_plant_measurement_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _geometry_rows(
    contour: PlantMeasurementContour, height_m: float
) -> list[PlantRequirement]:
    """The rows of 1.2, 9.1.1, 9.1.2.4 and 9.3, which the plan decides."""
    lower, upper = contour.mean_distance_limits_m
    dimension = contour.largest_plant_dimension_m
    aspect = contour.largest_aspect_angle_deg
    enters = contour.enters_convex_hull
    prescribed = contour.prescribed_microphone_height_m
    return [
        _row("plant_dimension_min", "1.2", "largest dimension of the plant area",
             dimension, ">=", _MIN_PLANT_DIMENSION_M, "m"),
        _row("plant_dimension_max", "1.2",
             "largest dimension of the plant area (approximately)",
             dimension, "<=", _MAX_PLANT_DIMENSION_M, "m", advisory=True),
        _row("mean_distance_min", "9.1.1 a)", "average measurement distance",
             contour.mean_distance_m, ">", lower, "m"),
        _row("mean_distance_max", "9.1.1 a)", "average measurement distance",
             contour.mean_distance_m, "<=", upper, "m"),
        _row("aspect_angle", "9.1.1 b)", "largest aspect angle on the contour",
             aspect, "<=", _MAX_ASPECT_ANGLE_DEG, "deg", holds=not enters),
        _row("position_spacing", "9.1.1 c)", "distance between measurement positions",
             contour.position_spacing_m, "<=",
             _SPACING_PER_MEAN_DISTANCE * contour.mean_distance_m, "m"),
        _row("omitted_positions", "9.1.2.4, 12 n)", "omitted measurement positions",
             contour.omitted_percent, "<=", _MAX_OMITTED_PERCENT, "%"),
        _row("microphone_height_min", "9.3", "microphone height",
             height_m, ">=", _MIN_MICROPHONE_HEIGHT_M, "m"),
        _row("microphone_height", "9.3",
             "microphone height at the prescribed, to the ±5 % of 9.2",
             height_m, "=", prescribed, "m", advisory=True,
             tolerance=_PLAN_ACCURACY * prescribed),
    ]  # fmt: skip


def _reading_rows(result: PlantSoundPowerResult) -> list[PlantRequirement]:
    """The rows of 6 b), 7.1, 9.5.1 a) and 10.2, which the readings decide."""
    rows: list[PlantRequirement] = []
    theta = result.directional_microphone_angle_deg
    if theta is not None:
        rows.append(
            _row("directional_microphone", "7.1",
                 "3 dB angle of the directional microphone",
                 float(np.min(theta)), ">", _MIN_DIRECTIONAL_ANGLE_DEG, "deg")
        )  # fmt: skip
    margin = result.background_margin_db
    if margin is not None:
        worst = float(settled(np.min(margin)))
        rows.append(
            _row("background_margin", "6 b)", "margin over the background noise",
                 worst, ">=", _MIN_BACKGROUND_MARGIN_DB, "dB")
        )  # fmt: skip
        rows.append(
            _row("background_margin_preferred", "6 b)",
                 "margin over the background noise (preferred)",
                 worst, ">", _PREFERRED_BACKGROUND_MARGIN_DB, "dB", advisory=True)
        )  # fmt: skip
    present = sum(1 for band in _REQUIRED_BANDS_HZ if band in result.frequencies_hz)
    rows.append(
        _row("octave_bands", "9.5.1 a)", "octave bands from 63 Hz to 4 kHz measured",
             present, ">=", len(_REQUIRED_BANDS_HZ), "")
    )  # fmt: skip
    excess = float(settled(np.max(result.levels_db - result.mean_level_db)))
    rows.append(
        _row("level_excess", "10.2", "largest level above the contour average",
             excess, "<=", _EXCESS_LIMIT_DB, "dB", advisory=True)
    )  # fmt: skip
    return rows


def check_plant_measurement(
    contour: PlantMeasurementContour,
    sound_power: PlantSoundPowerResult | None = None,
    *,
    measurement_time_s: float | ArrayLike | None = None,
    leq_range_db: float | ArrayLike | None = None,
) -> PlantMeasurementCheck:
    r"""May clause 10 be applied to this measurement? ISO 8297 1.2, 6, 7.1, 9 and 10.2.

    From the contour alone: the largest dimension of the plant area between
    16 m and approximately 320 m (1.2); the average measurement distance
    inside the window of 9.1.1 a); the plant area seen from every point of
    the contour inside 180° (9.1.1 b); adjacent positions at most
    :math:`2\bar{d}` apart (9.1.1 c); no more than 10 % of the positions
    omitted (9.1.2.4); and the microphone at least 5 m high (9.3). With the
    determination as well: the directional microphone's 3 dB angle above 30°
    in every band (7.1), the background at least 6 dB below every level
    (6 b), and the seven octave bands from 63 Hz to 4 kHz measured
    (9.5.1 a). With the measurement times: at least 1 min at each position
    (9.5.1). With the range of the integrated readings: an
    :math:`L_{\mathrm{eq},T}` that "does not fluctuate by more than
    ± 0,5 dB" at each position (9.5.3), a range of at most 1 dB.

    Four rows are advisory: the standard lets them go unmet provided the
    report says so, so they do not decide :attr:`PlantMeasurementCheck.passes`.
    The first is the height of 9.3 itself. 9.3 prescribes a height, not a
    lower bound, so the row holds when the microphones stand at
    :math:`H + 0{,}025\sqrt{S_\mathrm{m}}` (or 5 m) to within the ±5 % to
    which 9.2 reads :math:`H` and :math:`S_\mathrm{m}` off the plan, and a
    microphone lower (placed "as high as possible above the minimum height of
    5 m" where the height cannot be reached) or higher than that is listed in
    :attr:`PlantMeasurementCheck.deviations`. The others are the background
    "preferably more than 10 dB" below (6 b), a level more than 5 dB above
    the contour average, which 10.2 answers with a new contour or with steps
    2 and 3, and the upper end of 1.2, which the standard gives as
    approximate.

    The background margin, the level above the contour average and the range
    of the integrated reading are settled to nine decimals before they meet
    their limits, so a difference of decimal readings is judged as the
    decimal it is: a background 64,4 - 54,4 dB below, 10,000 000 000 000 007
    in binary, is the 10 dB that 6 b) does not prefer.

    Some printed numbers are left to the measurement team and not judged
    here, by choice rather than because they cannot be computed: the ±5 %
    and ±30 % to which 9.2 and 9.1.1 a) ask the plan to be read, the
    calibration intervals of 7.3, and the reflecting surfaces and the wind
    of clause 6 a) and c), which the standard states without a number.

    :param contour: The contour, from :func:`plant_measurement_contour`.
    :param sound_power: The determination made on it, or ``None`` to judge
        the arrangement alone. Its geometry must be the contour's.
    :param measurement_time_s: The measurement time at each position, in
        seconds, one value or one per measured position; ``None`` to leave
        9.5.1 unjudged.
    :param leq_range_db: With an integrating instrument, the range (highest
        less lowest) over which the :math:`L_{\mathrm{eq},T}` reading still
        moved when it was taken, in decibels: one value, or one per measured
        position (or per position and band); ``None`` to leave 9.5.3
        unjudged. A sound level meter's reading is judged by
        :func:`plant_steady_reading_db` instead (9.5.2).
    :return: A :class:`PlantMeasurementCheck`.
    :raises ValueError: for a determination whose geometry or number of
        positions is not the contour's, a non-positive time, or a negative
        range.
    """
    height = contour.prescribed_microphone_height_m
    if sound_power is not None:
        _require_same_geometry(contour, sound_power)
        height = sound_power.microphone_height_m
    rows = _geometry_rows(contour, height)
    if sound_power is not None:
        rows.extend(_reading_rows(sound_power))
    if measurement_time_s is not None:
        rows.append(_measurement_time_row(measurement_time_s))
    if leq_range_db is not None:
        rows.append(_integrated_reading_row(leq_range_db))
    return PlantMeasurementCheck(requirements=tuple(rows))


def _require_same_geometry(
    contour: PlantMeasurementContour, sound_power: PlantSoundPowerResult
) -> None:
    """Reject a determination made on another contour than this one.

    :raises ValueError: for a determination whose areas, lengths, mean
        distance or number of positions are not the contour's.
    """
    pairs = (
        ("measurement_area_m2", contour.measurement_area_m2),
        ("contour_length_m", contour.contour_length_m),
        ("mean_distance_m", contour.mean_distance_m),
        ("plant_area_m2", contour.plant_area_m2),
    )
    for name, expected in pairs:
        if not math.isclose(getattr(sound_power, name), expected, rel_tol=1e-9):
            msg = (
                f"'sound_power' was computed with another '{name}' than the contour's."
            )
            raise ValueError(msg)
    if sound_power.measured_levels_db.shape[0] != contour.positions_m.shape[0]:
        msg = "'sound_power' has another number of positions than the contour."
        raise ValueError(msg)


def _measurement_time_row(measurement_time_s: float | ArrayLike) -> PlantRequirement:
    """The row of 9.5.1: the shortest measurement time against one minute.

    :raises ValueError: for a time that is not positive and finite.
    """
    times = np.atleast_1d(np.asarray(measurement_time_s, dtype=np.float64))
    if not np.all(np.isfinite(times)) or np.any(times <= 0.0):
        msg = "'measurement_time_s' must be positive and finite."
        raise ValueError(msg)
    return _row("measurement_time", "9.5.1", "measurement time interval",
                float(np.min(times)), ">=", _MIN_MEASUREMENT_TIME_S, "s")  # fmt: skip


def _integrated_reading_row(leq_range_db: float | ArrayLike) -> PlantRequirement:
    """The row of 9.5.3: the widest range of an integrated reading against 1 dB.

    :raises ValueError: for a range that is negative or not finite.
    """
    spread = np.atleast_1d(np.asarray(leq_range_db, dtype=np.float64))
    if not np.all(np.isfinite(spread)) or np.any(spread < 0.0):
        msg = "'leq_range_db' must be finite and >= 0 dB."
        raise ValueError(msg)
    return _row("integrated_reading", "9.5.3",
                "range of the integrated reading L_eq,T (±0,5 dB)",
                float(settled(np.max(spread))), "<=", _INTEGRATED_RANGE_DB,
                "dB")  # fmt: skip


# --------------------------------------------------------------------------- #
# Particular parts of a plant (0.2 b)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PartialPlantContributions(OwnsArrays):
    """The sound power of a plant put together from parts measured on their
    own contours, and each part's share of it (0.2 b, c).

    :ivar names: A name per part.
    :ivar frequencies_hz: Nominal octave-band centres, in Hz.
    :ivar part_levels_db: :math:`L_W` of each part, ``(parts, bands)``, in
        dB re 1 pW.
    """

    names: tuple[str, ...]
    frequencies_hz: NDArray[np.float64]
    part_levels_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Reject parts whose spectra do not run over the same bands.

        :raises ValueError: for a name count, a band count or a level matrix
            that disagree, or bands outside the method.
        """
        bands = read_only(_octave_bands(self.frequencies_hz))
        object.__setattr__(self, "frequencies_hz", bands)
        levels = read_only(
            np.asarray(require_finite_matrix(self.part_levels_db, "part_levels_db"))
        )
        object.__setattr__(self, "part_levels_db", levels)
        object.__setattr__(self, "names", tuple(str(n) for n in self.names))
        require_ranks(self, frequencies_hz=1, part_levels_db=2)
        require_same_length(self, "frequencies_hz", ("part_levels_db", 1))
        if len(self.names) != levels.shape[0]:
            msg = (
                f"PartialPlantContributions: {len(self.names)} names for "
                f"{levels.shape[0]} parts."
            )
            raise ValueError(msg)

    @property
    def total_level_db(self) -> NDArray[np.float64]:
        """:math:`L_W` of the parts together, per band, in dB re 1 pW."""
        return energy_sum(self.part_levels_db, axis=0)

    @property
    def contribution_db(self) -> NDArray[np.float64]:
        """Each part's :math:`L_W` less the total, per band, in decibels (at most 0)."""
        return np.asarray(self.part_levels_db - self.total_level_db, dtype=np.float64)

    @property
    def a_weighted_part_levels_db(self) -> NDArray[np.float64]:
        r""":math:`L_{W\mathrm{A}}` of each part over the bands of 10.9, in dB re 1 pW."""
        keep = np.isin(self.frequencies_hz, _A_WEIGHTED_BANDS_HZ)
        ck = _a_weighting_corrections(self.frequencies_hz[keep])
        return energy_sum(self.part_levels_db[:, keep] + ck, axis=1)

    @property
    def a_weighted_total_db(self) -> float:
        r""":math:`L_{W\mathrm{A}}` of the parts together, in dB re 1 pW."""
        return energy_sum(self.a_weighted_part_levels_db)

    @property
    def a_weighted_contribution_db(self) -> NDArray[np.float64]:
        r"""Each part's :math:`L_{W\mathrm{A}}` less the total, in decibels."""
        return np.asarray(
            self.a_weighted_part_levels_db - self.a_weighted_total_db, dtype=np.float64
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each part's :math:`L_W` and their total, band by band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the total's bars.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.emission_plant import plot_partial_plant_contributions

        return plot_partial_plant_contributions(
            self, ax=ax, language=check_language(language), **kwargs
        )


def partial_plant_contributions(
    parts: Sequence[PlantSoundPowerResult], *, names: Sequence[str] | None = None
) -> PartialPlantContributions:
    """Put together the parts of a plant measured on their own contours (0.2 b).

    ISO 8297 is written for a whole plant, and 0.2 b) and c) also use it on
    particular parts of an industrial area, to find each part's contribution
    and to compare component installations. The parts, each measured round
    its own contour and not overlapping, radiate incoherently, so the power
    of the whole is the energy sum of theirs band by band, and each part's
    contribution is its level less that sum. NOTE 2 is the caveat: the sound
    power of a plant measured round one contour may differ from the sum of
    the powers of its sources, so this sum is not the same determination as
    the whole plant measured at once. Sources raised well above the plant
    (clause 11) are determined by other standards and reported beside the
    plant (item m) of clause 12); they are not summed in here.

    :param parts: The determinations of the parts, all over the same bands.
    :param names: A name per part, or ``None`` for "Part 1", "Part 2", ...
    :return: A :class:`PartialPlantContributions`.
    :raises ValueError: for no parts, parts over different bands, or a name
        count that does not match.
    """
    if not parts:
        msg = "'parts' must hold at least one determination."
        raise ValueError(msg)
    bands = parts[0].frequencies_hz
    for part in parts[1:]:
        if part.frequencies_hz.shape != bands.shape or not np.array_equal(
            part.frequencies_hz, bands
        ):
            msg = "Every part must be determined over the same octave bands."
            raise ValueError(msg)
    labels = (
        tuple(f"Part {i + 1}" for i in range(len(parts)))
        if names is None
        else tuple(names)
    )
    return PartialPlantContributions(
        names=labels,
        frequencies_hz=np.asarray(bands, dtype=np.float64),
        part_levels_db=np.stack([p.sound_power_level_db for p in parts]),
    )
