#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Wind turbine sound at a receptor (IEC TS 61400-11-2:2024).

IEC 61400-11 measures what a turbine emits; IEC TS 61400-11-2:2024 measures
what arrives at a dwelling, where the wind that drives the turbine also stirs
the trees, the background and the propagation. This module holds its closed
forms and printed tables; the amplitude modulation of clause 13 is in
:mod:`~phonometry.environment.assessment.wind_turbine_modulation`.

**Wind speed at another height** (Annex K, IEC 61400-11:2012 Annex D). The
power law of Equation (K.1), :func:`power_law_wind_speed`, and its inverse
for the shear exponent, Equation (K.2), :func:`wind_shear_exponent`, which
Tables K.1 and K.2 tabulate for 10 m and 120 m; the logarithmic profile with
the reference roughness length :math:`z_{0\mathrm{ref}} = 0.05` m (3.31) that
9.3.2.1 uses to bring a hub-height wind speed to 10 m,
:func:`logarithmic_wind_speed`; and :func:`wind_shear_profile`, which plots
both through two measured heights. Table K.3's roughness lengths are
:data:`ROUGHNESS_LENGTHS_M`.

**Bins and their averages** (10.1, 10.3). :func:`bin_sound_levels` sorts
interval levels into 1 m/s wind speed bins and 30 degree sectors and forms, per
bin, the energy average of Equation (1) (or the arithmetic one of Equation (8)
for statistical levels), the type A uncertainty of Equation (2) or (9), the
type B one of Equations (3) and (4) and their combination, Equation (5).
:func:`turbine_sound_levels` subtracts the background per bin with Equations
(6) and (7), under the 3 dB rule of 11.7. :func:`predicted_receptor_level`
sums a prediction over the turbines with the uncertainty of Equations (10)
and (11), and :func:`sound_relevant_turbines` picks the turbines whose wind
speeds make the binning wind speed (9.3.2.3).

**Low frequency sound** (Annex C). :func:`wind_turbine_low_frequency_level`
evaluates Equation (C.1) band by band with the ground correction and air
attenuation of Table C.2 and a facade insulation such as those of Table C.3.
Table C.2's air attenuation is the Danish statutory order's, not the
ISO 9613-1 value at the 70 % humidity its caption names: from 25 Hz to
100 Hz its cells are those of the order (BEK nr. 135 of 7 February 2019,
Table 1.4), set for 10 degrees C and **80 %** relative humidity with the
Nord2000 band attenuation rates and nothing below 25 Hz, which puts them
0.01 dB/km to 0.02 dB/km under ISO 9613-1 at 70 % between 50 Hz and 100 Hz;
from 125 Hz to 200 Hz the cells are ISO 9613-1 at 10 degrees C and 70 %
evaluated at the nominal band centres. ISO 9613-1's own Table 1 is computed at
the exact mid-band frequencies and prints 0.584 dB/km at 160 Hz (158.5 Hz
exactly), where Table C.2 prints the nominal 160 Hz value 0.59; Table 7 of the
TS, in contrast, follows the exact mid-bands.

**Emergence and the rating level** (Annexes J and A). :func:`sound_emergence`
is Equation (J.1); :func:`wind_turbine_rating_level` adds the most severe of
the tonal, amplitude modulation and impulsive adjustments (A.1), with the
amplitude modulation adjustment of Figure A.1 in
:func:`amplitude_modulation_adjustment`.

**The upper tone search frequency** (12.5.2.4, Table 7).
:func:`upper_tone_search_frequency` finds the lowest one-third-octave band that
ISO 9613-1 attenuates by at least 20 dB over the distance to the nearest
turbine.
"""

from __future__ import annotations

import math
from dataclasses import KW_ONLY, dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.display import RichDisplay
from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.levels_math import energy_mean, energy_sum
from ..._internal.validation import (
    require_finite,
    require_finite_array,
    require_finite_matrix,
    require_positive,
    require_ranks,
    require_same_length,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM",
    "LOW_FREQUENCY_BANDS_HZ",
    "LOW_FREQUENCY_FACADE_INSULATION_DB",
    "LOW_FREQUENCY_GROUND_CORRECTION_DB",
    "LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES",
    "MODELLING_UNCERTAINTY_DB",
    "PREDICTION_MODEL_UNCERTAINTY_DB",
    "REFERENCE_ROUGHNESS_LENGTH_M",
    "ROUGHNESS_LENGTHS_M",
    "SWEDISH_LOW_FREQUENCY_LIMITS_DB",
    "TONE_SEARCH_BANDS_HZ",
    "TYPE_B_UNCERTAINTY_EXAMPLES_DB",
    "TYPICAL_WIND_SHEAR_EXPONENT_RANGE",
    "BackgroundCorrectionRegime",
    "BinnedSoundLevels",
    "GroundImpedanceClass",
    "LowFrequencyLevel",
    "PredictedReceptorLevel",
    "SoundEmergence",
    "SoundRelevantTurbines",
    "ToneSearchLimit",
    "TurbineSoundLevels",
    "WindShearProfile",
    "WindTurbineRatingLevel",
    "amplitude_modulation_adjustment",
    "bin_sound_levels",
    "logarithmic_wind_speed",
    "power_law_wind_speed",
    "predicted_receptor_level",
    "sound_emergence",
    "sound_relevant_turbines",
    "turbine_sound_levels",
    "upper_tone_search_frequency",
    "wind_shear_exponent",
    "wind_shear_profile",
    "wind_turbine_low_frequency_level",
    "wind_turbine_rating_level",
]

# ---------------------------------------------------------------------------
# Published tables and constants
# ---------------------------------------------------------------------------

#: Reference roughness length :math:`z_{0\mathrm{ref}}` for converting wind
#: speeds between heights with the logarithmic profile, in m (3.31).
REFERENCE_ROUGHNESS_LENGTH_M: float = 0.05

#: Roughness length of four kinds of terrain, in m (Table K.3, the same as
#: IEC 61400-11:2012 Table D.1). A crude estimate, the TS warns, valid only
#: for cloudy conditions and long-term averages.
ROUGHNESS_LENGTHS_M: Mapping[str, float] = MappingProxyType(
    {
        "Water, snow or sand surfaces": 0.0001,
        "Open, flat land, mown grass, bare soil": 0.01,
        "Farmland with some vegetation": 0.05,
        "Suburbs, towns, forests, many trees and bushes": 0.3,
    }
)

#: The typical range of the wind shear exponent, from very unstable (-0.1) to
#: very stable (0.5) stratification; Table K.2 leaves out the values outside it
#: (K.4.3).
TYPICAL_WIND_SHEAR_EXPONENT_RANGE: tuple[float, float] = (-0.1, 0.5)

#: Examples of type B uncertainty components of a measurement period, in dB,
#: each as ``(typical range, standard uncertainty)`` (Table 3). Equation (3)
#: combines the standard uncertainties in quadrature.
TYPE_B_UNCERTAINTY_EXAMPLES_DB: Mapping[str, tuple[float, float]] = MappingProxyType(
    {
        "calibration": (0.3, 0.2),
        "instrument": (0.5, 0.3),
        "measurement position": (0.5, 0.3),
        "wind screen insertion loss": (0.3, 0.2),
    }
)

#: Standard uncertainty of the prediction model, in dB, expected for both
#: ISO 9613-2 and Nord2000 downwind up to 3 km to 5 km (10.3.4, NOTE).
PREDICTION_MODEL_UNCERTAINTY_DB: float = 2.0

#: Uncertainty contribution of the propagation modelling, in dB (10.3.4).
MODELLING_UNCERTAINTY_DB: float = 0.5

#: Nominal one-third-octave centre frequencies of Annex C, 10 Hz to 200 Hz.
LOW_FREQUENCY_BANDS_HZ: NDArray[np.float64] = read_only(
    np.array(
        [
            10.0,
            12.5,
            16.0,
            20.0,
            25.0,
            31.5,
            40.0,
            50.0,
            63.0,
            80.0,
            100.0,
            125.0,
            160.0,
            200.0,
        ]
    )
)

#: Low frequency ground correction :math:`\Delta L_\mathrm{g,LF}` for onshore
#: turbines over ground of impedance class D, in dB, at
#: :data:`LOW_FREQUENCY_BANDS_HZ` (Table C.2).
LOW_FREQUENCY_GROUND_CORRECTION_DB: NDArray[np.float64] = read_only(
    np.array([6.0, 6.0, 5.8, 5.6, 5.4, 5.2, 5.0, 4.7, 4.3, 3.7, 3.0, 1.8, 0.0, 0.0])
)

#: Air attenuation coefficient :math:`\alpha` of Table C.2, in dB/km, at
#: :data:`LOW_FREQUENCY_BANDS_HZ`, as printed. The caption says 10 degrees C
#: and 70 % relative humidity; the cells from 25 Hz to 100 Hz are those of
#: the Danish statutory order on wind turbine noise at 10 degrees C and 80 %
#: (Nord2000 band rates, zero below 25 Hz), and the cells from 125 Hz to
#: 200 Hz are ISO 9613-1 at 10 degrees C and 70 % at the nominal band centres
#: (at the exact mid-band of 160 Hz ISO 9613-1 gives 0.58, not 0.59).
LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM: NDArray[np.float64] = read_only(
    np.array(
        [0.0, 0.0, 0.0, 0.0, 0.02, 0.03, 0.05, 0.07, 0.11, 0.17, 0.26, 0.41, 0.59, 0.80]
    )
)

#: Examples of facade sound insulation :math:`\Delta L_\sigma`, in dB, at
#: :data:`LOW_FREQUENCY_BANDS_HZ` (Table C.3), given at a 67 % confidence
#: level for typical northern European facades. The lightweight row is the
#: one the Danish order gives for summer-house areas.
LOW_FREQUENCY_FACADE_INSULATION_DB: Mapping[str, NDArray[np.float64]] = (
    MappingProxyType(
        {
            "Denmark brick or similar": read_only(
                np.array(
                    [
                        4.9,
                        5.9,
                        4.6,
                        6.6,
                        8.4,
                        10.8,
                        11.4,
                        13.0,
                        16.6,
                        19.7,
                        21.2,
                        20.2,
                        21.2,
                        21.0,
                    ]
                )
            ),
            "Denmark lightweight": read_only(
                np.array(
                    [
                        6.8,
                        3.9,
                        0.4,
                        -0.2,
                        4.8,
                        6.2,
                        8.4,
                        10.5,
                        11.9,
                        11.9,
                        16.0,
                        17.5,
                        17.9,
                        17.0,
                    ]
                )
            ),
        }
    )
)

#: The Swedish criterion curve of Table C.5: Z-weighted sound pressure level
#: in each one-third-octave band from 31.5 Hz to 200 Hz, in dB, keyed by the
#: nominal centre frequency in Hz.
SWEDISH_LOW_FREQUENCY_LIMITS_DB: Mapping[float, float] = MappingProxyType(
    {
        31.5: 56.0,
        40.0: 49.0,
        50.0: 43.0,
        63.0: 42.0,
        80.0: 40.0,
        100.0: 38.0,
        125.0: 36.0,
        160.0: 34.0,
        200.0: 32.0,
    }
)


@dataclass(frozen=True)
class GroundImpedanceClass(RichDisplay):
    """One impedance class of Table C.1.

    :ivar flow_resistivity_kpa_s_m2: Representative flow resistivity, in
        kPa s/m².
    :ivar nordtest_classes_kpa_s_m2: The Nordtest flow resistivity classes the
        class covers, in kPa s/m² (empty where the table prints a dash).
    :ivar description: The ground the class describes.
    """

    flow_resistivity_kpa_s_m2: float
    nordtest_classes_kpa_s_m2: tuple[float, ...]
    description: str


#: The ground impedance classes of Table C.1, keyed by their letter. The
#: ground correction of Table C.2 is for class D.
LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES: Mapping[str, GroundImpedanceClass] = (
    MappingProxyType(
        {
            "A": GroundImpedanceClass(
                12.5, (10.0, 15.0), "Very soft (snow, moss like)"
            ),
            "B": GroundImpedanceClass(
                32.0,
                (25.0, 40.0),
                "Soft forest floor (short dense heatherlike or thick moss)",
            ),
            "C": GroundImpedanceClass(
                80.0,
                (63.0, 100.0),
                "Uncompacted loose ground (turf, grass, loose soil)",
            ),
            "D": GroundImpedanceClass(
                200.0,
                (160.0, 250.0),
                "Normal uncompacted ground (forest floor, pasture field)",
            ),
            "E": GroundImpedanceClass(
                500.0,
                (400.0, 630.0),
                "Compacted field and gravel (compacted lawns, park area)",
            ),
            "F": GroundImpedanceClass(
                2000.0,
                (2000.0,),
                "Compacted dense ground (gravel road, parking lot, ISO 10844)",
            ),
            "G": GroundImpedanceClass(
                20000.0, (), "Hard surface (most normal asphalt, concrete)"
            ),
            "H": GroundImpedanceClass(
                200000.0,
                (),
                "Very hard and dense surfaces (dense asphalt, concrete, water)",
            ),
        }
    )
)

#: Nominal one-third-octave centre frequencies over which the upper tone
#: search frequency is looked for, 50 Hz to 10 kHz (12.5.2.4, the range of
#: ISO 9613-1).
TONE_SEARCH_BANDS_HZ: NDArray[np.float64] = read_only(
    np.array(
        [
            50.0,
            63.0,
            80.0,
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
            6300.0,
            8000.0,
            10000.0,
        ]
    )
)

#: Frequency weighting A at the nominal one-third-octave centres from 10 Hz to
#: 10 kHz, in dB (IEC 61672-1:2013 Table 3). Table C.4 prints the 10 Hz to
#: 200 Hz values; the amplitude modulation bands use 50 Hz to 6.3 kHz.
_A_WEIGHTING_DB: Mapping[float, float] = MappingProxyType(
    {
        10.0: -70.4,
        12.5: -63.4,
        16.0: -56.7,
        20.0: -50.5,
        25.0: -44.7,
        31.5: -39.4,
        40.0: -34.6,
        50.0: -30.2,
        63.0: -26.2,
        80.0: -22.5,
        100.0: -19.1,
        125.0: -16.1,
        160.0: -13.4,
        200.0: -10.9,
        250.0: -8.6,
        315.0: -6.6,
        400.0: -4.8,
        500.0: -3.2,
        630.0: -1.9,
        800.0: -0.8,
        1000.0: 0.0,
        1250.0: 0.6,
        1600.0: 1.0,
        2000.0: 1.2,
        2500.0: 1.3,
        3150.0: 1.2,
        4000.0: 1.0,
        5000.0: 0.5,
        6300.0: -0.1,
        8000.0: -1.1,
        10000.0: -2.5,
    }
)

#: Level difference below which a bin is not background corrected by
#: logarithmic subtraction, in dB, and the correction then suggested (11.7).
_BACKGROUND_MARGIN_DB = 3.0
#: Drop of the predicted total, in dB, that stops the exclusion of the
#: quietest turbines (9.3.2.3).
_RELEVANCE_DROP_DB = 1.0
#: A limit reached through floating-point arithmetic is on the limit: a bin
#: whose total is 3 dB over its background in decimal, 33.3 dB over 30.3 dB,
#: is 2.9999999999999964 dB over it in binary, and the energy means of 10.3 and
#: the energy sums of 9.3.2.3 land a few units in the last place either side of
#: a whole decibel just as often. A nanodecibel is far below any digit the TS
#: prints or a meter reads.
_BOUNDARY_SLACK_DB = 1e-9

#: How far, in dB, a column of a result built by hand may be from what its
#: levels give: rounding, not a tolerance of the method.
_FIELD_SLACK_DB = 1e-9

#: The distance correction term of Equation (C.1), 10 lg(4 pi) as printed.
_DISTANCE_TERM_DB = 11.0
#: Attenuation over the source-receiver distance that sets the upper tone
#: search frequency, in dB (12.5.2.4).
_TONE_SEARCH_ATTENUATION_DB = 20.0
#: Figure A.1: no adjustment below this depth, in dB ...
_AM_ONSET_DB = 3.0
#: ... the adjustment there, in dB ...
_AM_ONSET_ADJUSTMENT_DB = 3.0
#: ... and the depth, in dB, from which it stays at its maximum ...
_AM_SATURATION_DB = 10.0
#: ... of this many dB.
_AM_MAXIMUM_ADJUSTMENT_DB = 5.0
#: Relative tolerance matching a supplied band centre to a nominal one.
_NOMINAL_MATCH = 0.01
#: Full circle, in degrees.
_FULL_TURN_DEG = 360.0


def _nominal_lookup(
    frequencies: NDArray[np.float64],
    table: Mapping[float, float] | tuple[NDArray[np.float64], NDArray[np.float64]],
    name: str,
) -> NDArray[np.float64]:
    """Values of a table at the supplied nominal centre frequencies."""
    if isinstance(table, tuple):
        keys, values = table
        lookup = dict(zip(keys.tolist(), values.tolist(), strict=True))
    else:
        lookup = dict(table)
    out = np.empty(frequencies.size)
    for i, f in enumerate(frequencies):
        match = [k for k in lookup if abs(k - f) <= _NOMINAL_MATCH * k]
        if len(match) != 1:
            msg = f"{name} has no value at {f:g} Hz; supply the values explicitly."
            raise ValueError(msg)
        out[i] = lookup[match[0]]
    return out


# ---------------------------------------------------------------------------
# Wind speed at another height (Annex K; IEC 61400-11:2012 Annex D)
# ---------------------------------------------------------------------------
def power_law_wind_speed(
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
    shear_exponent: ArrayLike,
) -> NDArray[np.float64] | float:
    r"""Wind speed at another height by the power law (Equation (K.1)).

    :math:`V_z = V_{z,\mathrm{ref}} \, (z/z_\mathrm{ref})^{\alpha}`, the
    profile of IEC 61400-11:2012 D.3 that Table K.1 evaluates for 120 m and
    10 m.

    :param reference_speed_m_s: Wind speed at the reference height, in m/s.
    :param height_m: Height of the wanted wind speed, in m.
    :param reference_height_m: Height of the known wind speed, in m.
    :param shear_exponent: The wind shear exponent :math:`\alpha`.
    :return: The wind speed at ``height_m``, in m/s; a ``float`` for scalar
        inputs.
    :raises ValueError: If a height is not positive, a speed is negative or a
        value is not finite.
    """
    z = require_positive(height_m, "height_m")
    z_ref = require_positive(reference_height_m, "reference_height_m")
    speed = np.asarray(reference_speed_m_s, dtype=np.float64)
    alpha = np.asarray(shear_exponent, dtype=np.float64)
    if not (np.all(np.isfinite(speed)) and np.all(np.isfinite(alpha))):
        msg = "'reference_speed_m_s' and 'shear_exponent' must be finite."
        raise ValueError(msg)
    if np.any(speed < 0.0):
        msg = "'reference_speed_m_s' must not be negative."
        raise ValueError(msg)
    out = speed * (z / z_ref) ** alpha
    return float(out) if out.ndim == 0 else np.asarray(out, dtype=np.float64)


def wind_shear_exponent(
    speed_m_s: ArrayLike,
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
) -> NDArray[np.float64] | float:
    r"""Wind shear exponent from two wind speeds (Equation (K.2)).

    :math:`\alpha = \ln(V_z/V_{z,\mathrm{ref}}) / \ln(z/z_\mathrm{ref})`; with
    :math:`z = 120` m and :math:`z_\mathrm{ref} = 10` m this is Table K.2.
    Values outside :data:`TYPICAL_WIND_SHEAR_EXPONENT_RANGE` are returned as
    computed; Table K.2 leaves them blank.

    :param speed_m_s: Wind speed at ``height_m``, in m/s.
    :param reference_speed_m_s: Wind speed at ``reference_height_m``, in m/s.
    :param height_m: The higher (or other) height, in m.
    :param reference_height_m: The reference height, in m.
    :return: The shear exponent; a ``float`` for scalar inputs.
    :raises ValueError: If a speed or height is not positive, or the two
        heights are the same.
    """
    z = require_positive(height_m, "height_m")
    z_ref = require_positive(reference_height_m, "reference_height_m")
    if math.isclose(z, z_ref):
        msg = "'height_m' and 'reference_height_m' must differ."
        raise ValueError(msg)
    upper = np.asarray(speed_m_s, dtype=np.float64)
    lower = np.asarray(reference_speed_m_s, dtype=np.float64)
    if not (np.all(np.isfinite(upper)) and np.all(np.isfinite(lower))):
        msg = "The wind speeds must be finite."
        raise ValueError(msg)
    if np.any(upper <= 0.0) or np.any(lower <= 0.0):
        msg = "The wind speeds must be positive for their ratio to have a logarithm."
        raise ValueError(msg)
    out = np.log(upper / lower) / math.log(z / z_ref)
    return float(out) if out.ndim == 0 else np.asarray(out, dtype=np.float64)


def logarithmic_wind_speed(
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
    roughness_length_m: float = REFERENCE_ROUGHNESS_LENGTH_M,
) -> NDArray[np.float64] | float:
    r"""Wind speed at another height by the logarithmic profile.

    :math:`V_z = V_{z,\mathrm{ref}} \ln(z/z_0) / \ln(z_\mathrm{ref}/z_0)`
    (IEC 61400-11:2012 Equation (D.1)). With the default reference roughness
    length :math:`z_{0\mathrm{ref}} = 0.05` m (3.31), a hub-height wind speed
    brought to 10 m is the binning wind speed :math:`V_\mathrm{bin}` of
    9.3.2.1 (IEC 61400-11:2012 Equation (29) solved for :math:`V_{10}`).

    :param reference_speed_m_s: Wind speed at the reference height, in m/s.
    :param height_m: Height of the wanted wind speed, in m.
    :param reference_height_m: Height of the known wind speed, in m.
    :param roughness_length_m: Roughness length :math:`z_0`, in m.
    :return: The wind speed at ``height_m``, in m/s; a ``float`` for scalar
        inputs.
    :raises ValueError: If a height or the roughness length is not positive,
        a height does not exceed the roughness length, or a speed is negative.
    """
    z = require_positive(height_m, "height_m")
    z_ref = require_positive(reference_height_m, "reference_height_m")
    z0 = require_positive(roughness_length_m, "roughness_length_m")
    if z <= z0 or z_ref <= z0:
        msg = "Both heights must exceed the roughness length."
        raise ValueError(msg)
    speed = np.asarray(reference_speed_m_s, dtype=np.float64)
    if not np.all(np.isfinite(speed)) or np.any(speed < 0.0):
        msg = "'reference_speed_m_s' must be finite and not negative."
        raise ValueError(msg)
    out = speed * math.log(z / z0) / math.log(z_ref / z0)
    return float(out) if out.ndim == 0 else np.asarray(out, dtype=np.float64)


@dataclass(frozen=True)
class WindShearProfile(RichDisplay):
    r"""A wind profile through two measured heights (Annex K).

    :ivar heights_m: The two measurement heights, lower first, in m.
    :ivar speeds_m_s: The wind speeds measured there, in m/s.
    :ivar shear_exponent: The power-law exponent :math:`\alpha` through the
        two points (Equation (K.2)).
    """

    heights_m: tuple[float, float]
    speeds_m_s: tuple[float, float]
    shear_exponent: float

    @property
    def typical(self) -> bool:
        r"""Whether :math:`\alpha` lies in the typical range (K.4.3).

        The range is :data:`TYPICAL_WIND_SHEAR_EXPONENT_RANGE`, bounds included.
        """
        low_alpha, high_alpha = TYPICAL_WIND_SHEAR_EXPONENT_RANGE
        return low_alpha <= self.shear_exponent <= high_alpha

    def speed_at(self, height_m: ArrayLike) -> NDArray[np.float64] | float:
        """The power-law wind speed at ``height_m`` (Equation (K.1)), in m/s."""
        heights = np.asarray(height_m, dtype=np.float64)
        if not np.all(np.isfinite(heights)) or np.any(heights <= 0.0):
            msg = "'height_m' must be finite and positive."
            raise ValueError(msg)
        out = self.speeds_m_s[0] * (heights / self.heights_m[0]) ** self.shear_exponent
        return float(out) if out.ndim == 0 else np.asarray(out, dtype=np.float64)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the power-law profile through the two measured points.

        The logarithmic profile with the reference roughness length through
        the lower point is drawn for comparison, as the binning wind speed of
        9.3.2.1 assumes it.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the power-law profile.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_wind_shear_profile

        return plot_wind_shear_profile(
            self, ax=ax, language=check_language(language), **kwargs
        )


def wind_shear_profile(
    lower_speed_m_s: float,
    upper_speed_m_s: float,
    *,
    lower_height_m: float = 10.0,
    upper_height_m: float,
) -> WindShearProfile:
    """The power-law wind profile through two measured wind speeds (K.4.3).

    The wind shear is typically found from a wind speed at 10 m and one at
    hub height (K.4.3); :attr:`WindShearProfile.speed_at` then gives the wind
    speed at any height by Equation (K.1).

    :param lower_speed_m_s: Wind speed at ``lower_height_m``, in m/s.
    :param upper_speed_m_s: Wind speed at ``upper_height_m``, in m/s.
    :param lower_height_m: The lower measurement height, in m (10 m by
        default).
    :param upper_height_m: The upper measurement height, in m (typically the
        hub height).
    :return: A :class:`WindShearProfile`.
    :raises ValueError: If a speed or height is not positive or the upper
        height is not above the lower one.
    """
    low_z = require_positive(lower_height_m, "lower_height_m")
    high_z = require_positive(upper_height_m, "upper_height_m")
    if high_z <= low_z:
        msg = "'upper_height_m' must be above 'lower_height_m'."
        raise ValueError(msg)
    alpha = float(
        wind_shear_exponent(
            upper_speed_m_s,
            lower_speed_m_s,
            height_m=high_z,
            reference_height_m=low_z,
        )
    )
    return WindShearProfile(
        heights_m=(low_z, high_z),
        speeds_m_s=(float(lower_speed_m_s), float(upper_speed_m_s)),
        shear_exponent=alpha,
    )


# ---------------------------------------------------------------------------
# Bins, averages and uncertainty (10.1, 10.3, 11.7)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Bins:
    """The bin of each data point, as integer indices, and the bin widths.

    ``keys[i]`` is ``(sector, speed)``: the index of the direction sector
    (0 without directions) and of the wind speed class, so that grouping
    never compares floats. :meth:`centres` turns a key into the sector centre
    in degrees and the wind speed class centre in m/s.
    """

    keys: tuple[tuple[int, int], ...]
    speeds_m_s: NDArray[np.float64]
    by_direction: bool
    bin_width_m_s: float
    sector_width_deg: float

    def centres(self, key: tuple[int, int]) -> tuple[float, float]:
        """Sector centre (degrees) and wind speed class centre (m/s) of a key."""
        return key[0] * self.sector_width_deg, key[1] * self.bin_width_m_s

    def members(self, key: tuple[int, int]) -> NDArray[np.bool_]:
        """Which data points fall in the bin ``key``."""
        return np.array([k == key for k in self.keys], dtype=np.bool_)


def _bin_keys(
    wind_speeds_m_s: ArrayLike,
    wind_directions_deg: ArrayLike | None,
    *,
    count: int,
    bin_width_m_s: float,
    sector_width_deg: float,
) -> _Bins:
    """The wind speed class and direction sector of each data point.

    Wind speed bins are ``bin_width_m_s`` wide and centred on its multiples
    (0.5 m/s to 1.5 m/s is bin 1 for 1 m/s bins); direction sectors are
    ``sector_width_deg`` wide and the first is centred on north (345 degrees
    to 15 degrees for 30 degree sectors).
    """
    speeds = require_finite_array(wind_speeds_m_s, "wind_speeds_m_s")
    if speeds.size != count:
        msg = f"'wind_speeds_m_s' must hold one value per data point ({count})."
        raise ValueError(msg)
    if np.any(speeds < 0.0):
        msg = "'wind_speeds_m_s' must not be negative."
        raise ValueError(msg)
    width = require_positive(bin_width_m_s, "bin_width_m_s")
    speed_index = np.floor(speeds / width + 0.5).astype(np.int64)
    sector = require_positive(sector_width_deg, "sector_width_deg")
    sectors = _FULL_TURN_DEG / sector
    if not math.isclose(sectors, round(sectors)):
        msg = f"'sector_width_deg' must divide 360 degrees; got {sector:g}."
        raise ValueError(msg)
    if wind_directions_deg is None:
        sector_index = np.zeros(count, dtype=np.int64)
    else:
        directions = require_finite_array(wind_directions_deg, "wind_directions_deg")
        if directions.size != count:
            msg = f"'wind_directions_deg' must hold one value per data point ({count})."
            raise ValueError(msg)
        shifted = np.mod(directions + sector / 2.0, _FULL_TURN_DEG)
        sector_index = np.mod(np.floor(shifted / sector), round(sectors)).astype(
            np.int64
        )
    keys = tuple(
        (int(a), int(b)) for a, b in zip(sector_index, speed_index, strict=True)
    )
    return _Bins(
        keys=keys,
        speeds_m_s=speeds,
        by_direction=wind_directions_deg is not None,
        bin_width_m_s=width,
        sector_width_deg=sector,
    )


def _type_a_arithmetic(
    values: NDArray[np.float64], *, mean: float | None = None
) -> float:
    """Equations (2) and (9): the spread about the bin average over N(N-1).

    ``mean`` is the bin average the deviations are taken from: the energy
    average of Equation (1) for Equation (2), the arithmetic mean of Equation
    (8) (the default) for Equation (9). NaN for a bin of one value, whose
    spread the equation cannot give.
    """
    n = values.size
    if n < 2:  # noqa: PLR2004
        return math.nan
    centre = float(np.mean(values)) if mean is None else mean
    return math.sqrt(float(np.sum((values - centre) ** 2)) / (n * (n - 1)))


class _Averaging(StrEnum):
    """How the levels of a bin are averaged (10.3.2, 10.3.3)."""

    ENERGY = "energy"
    ARITHMETIC = "arithmetic"


@dataclass(frozen=True)
class BinnedSoundLevels(OwnsArrays):
    """Interval levels averaged per wind speed bin and sector (10.1, 10.3).

    One row per occupied bin, sorted by sector and then wind speed.

    :ivar wind_speeds_m_s: Centre of each bin's wind speed class, in m/s.
    :ivar wind_directions_deg: Centre of each bin's direction sector, in
        degrees, or ``None`` when binned by wind speed alone.
    :ivar counts: Number of intervals :math:`N` in each bin.
    :ivar mean_levels_db: The bin average, Equation (1) (energy) or
        Equation (8) (arithmetic), in dB.
    :ivar type_a_uncertainty_db: Equation (2) or (9), in dB; NaN for a bin of
        one interval, whose spread the equation cannot give.
    :ivar type_b_uncertainty_db: Equation (4), in dB.
    :ivar combined_uncertainty_db: Equation (5), in dB; NaN where the type A
        part is.
    :ivar averaging: ``"energy"`` or ``"arithmetic"``.
    :ivar interval_levels_db: The interval levels binned, in dB.
    :ivar interval_wind_speeds_m_s: Their wind speeds, in m/s.
    :ivar bin_width_m_s: Width of the wind speed bins, in m/s.
    :ivar sector_width_deg: Width of the direction sectors, in degrees (also
        kept when binned by wind speed alone).
    """

    wind_speeds_m_s: NDArray[np.float64]
    wind_directions_deg: NDArray[np.float64] | None
    counts: NDArray[np.int64]
    mean_levels_db: NDArray[np.float64]
    type_a_uncertainty_db: NDArray[np.float64]
    type_b_uncertainty_db: NDArray[np.float64]
    combined_uncertainty_db: NDArray[np.float64]
    _: KW_ONLY
    averaging: str
    interval_levels_db: NDArray[np.float64]
    interval_wind_speeds_m_s: NDArray[np.float64]
    bin_width_m_s: float
    sector_width_deg: float

    def _keys(self) -> list[tuple[int, int]]:
        """The integer (sector, wind speed class) index of each bin.

        The centres are whole multiples of the widths, so dividing and
        rounding recovers the indices the binning used, and bins are paired
        on integers, never on float centres.
        """
        speeds = np.rint(self.wind_speeds_m_s / self.bin_width_m_s).astype(np.int64)
        sectors = (
            np.zeros(speeds.size, dtype=np.int64)
            if self.wind_directions_deg is None
            else np.rint(self.wind_directions_deg / self.sector_width_deg).astype(
                np.int64
            )
        )
        return [(int(d), int(v)) for d, v in zip(sectors, speeds, strict=True)]

    def background_corrected(self, background: BinnedSoundLevels) -> TurbineSoundLevels:
        """Correct these total levels for a background binned the same way (11.7).

        The bins the two share are corrected by :func:`turbine_sound_levels`
        with their combined uncertainties; a bin of either without a partner
        in the other is left out.

        :param background: The background (turbines off) levels, binned with
            the same wind speed classes and sectors.
        :return: A :class:`TurbineSoundLevels` over the shared bins, with
            their sector centres when binned by direction.
        :raises ValueError: If the two share no bin, one is binned by
            direction and the other is not, or their bin or sector widths
            differ.
        """
        if (self.wind_directions_deg is None) != (
            background.wind_directions_deg is None
        ):
            msg = "Bin the total and the background the same way, both by direction or neither."
            raise ValueError(msg)
        same_width = math.isclose(self.bin_width_m_s, background.bin_width_m_s)
        same_sector = self.wind_directions_deg is None or math.isclose(
            self.sector_width_deg, background.sector_width_deg
        )
        if not (same_width and same_sector):
            msg = (
                "Bin the total and the background with the same widths; got "
                f"{self.bin_width_m_s:g} m/s and {self.sector_width_deg:g} degrees "
                f"against {background.bin_width_m_s:g} m/s and "
                f"{background.sector_width_deg:g} degrees."
            )
            raise ValueError(msg)
        mine = {key: i for i, key in enumerate(self._keys())}
        theirs = {key: i for i, key in enumerate(background._keys())}
        shared = sorted(set(mine) & set(theirs))
        if not shared:
            msg = "The total and the background levels share no bin."
            raise ValueError(msg)
        rows = [mine[k] for k in shared]
        other = [theirs[k] for k in shared]
        return turbine_sound_levels(
            self.mean_levels_db[rows],
            background.mean_levels_db[other],
            total_uncertainty_db=self.combined_uncertainty_db[rows],
            background_uncertainty_db=background.combined_uncertainty_db[other],
            wind_speeds_m_s=self.wind_speeds_m_s[rows],
            wind_directions_deg=(
                None
                if self.wind_directions_deg is None
                else self.wind_directions_deg[rows]
            ),
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the intervals against wind speed and the bin averages over them.

        The scatter of interval levels against the binning wind speed is what
        11.9 asks to be reported; the bin averages carry their combined
        uncertainty as error bars.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bin averages.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_binned_sound_levels

        return plot_binned_sound_levels(
            self, ax=ax, language=check_language(language), **kwargs
        )


def bin_sound_levels(
    levels_db: ArrayLike,
    wind_speeds_m_s: ArrayLike,
    wind_directions_deg: ArrayLike | None = None,
    *,
    averaging: str = "energy",
    type_b_uncertainty_db: ArrayLike = 0.0,
    bin_width_m_s: float = 1.0,
    sector_width_deg: float = 30.0,
) -> BinnedSoundLevels:
    r"""Average interval levels per wind speed bin and sector (10.1, 10.3).

    Each interval (typically 10 s to 10 min) goes into the wind speed bin of
    its binning wind speed, ``bin_width_m_s`` wide and centred on its
    multiples, and, with directions, into the ``sector_width_deg`` sector
    whose first member is centred on north. Per bin:

    * the average, Equation (1)
      :math:`\overline{L}_k = 10 \lg(\frac{1}{N}\sum 10^{L_{j,k}/10})` for
      equivalent levels, or Equation (8), the arithmetic mean, for
      statistical levels such as :math:`L_{90}` (10.3.2 NOTE);
    * the type A uncertainty, Equation (2) (or (9)),
      :math:`s = \sqrt{\sum (L_{j,k} - \overline{L}_k)^2 / (N(N-1))}`;
    * the type B uncertainty, Equation (4), the root mean square of the
      per-interval type B uncertainties of Equation (3);
    * their combination, Equation (5), :math:`\sqrt{s^2 + u^2}`.

    :param levels_db: The interval levels, in dB.
    :param wind_speeds_m_s: The binning wind speed of each interval, in m/s.
    :param wind_directions_deg: Optional wind direction of each interval, in
        degrees from north.
    :param averaging: ``"energy"`` (Equation (1), for ``LAeq``) or
        ``"arithmetic"`` (Equation (8), for statistical levels).
    :param type_b_uncertainty_db: Combined type B standard uncertainty of each
        interval, Equation (3), in dB: one value for all or one per interval.
        Combine the components in quadrature, for example those of
        :data:`TYPE_B_UNCERTAINTY_EXAMPLES_DB`.
    :param bin_width_m_s: Width of the wind speed bins, in m/s (1 m/s by
        default, 10.1).
    :param sector_width_deg: Width of the direction sectors, in degrees (30
        by default, 10.1); it must divide 360.
    :return: A :class:`BinnedSoundLevels`.
    :raises ValueError: If the inputs disagree in length, a value is not
        finite, a wind speed or an uncertainty is negative, or ``averaging``
        is unknown.
    """
    known = tuple(member.value for member in _Averaging)
    if averaging not in known:
        msg = f"'averaging' must be one of {known}; got {averaging!r}."
        raise ValueError(msg)
    mode = _Averaging(averaging)
    levels = require_finite_array(levels_db, "levels_db")
    type_b = np.broadcast_to(
        np.asarray(type_b_uncertainty_db, dtype=np.float64), levels.shape
    ).astype(np.float64)
    if not np.all(np.isfinite(type_b)) or np.any(type_b < 0.0):
        msg = "'type_b_uncertainty_db' must be finite and not negative."
        raise ValueError(msg)
    bins = _bin_keys(
        wind_speeds_m_s,
        wind_directions_deg,
        count=levels.size,
        bin_width_m_s=bin_width_m_s,
        sector_width_deg=sector_width_deg,
    )
    occupied = sorted(set(bins.keys))
    n = len(occupied)
    counts = np.zeros(n, dtype=np.int64)
    means = np.zeros(n)
    type_a = np.zeros(n)
    u_b = np.zeros(n)
    for row, key in enumerate(occupied):
        members = bins.members(key)
        values = levels[members]
        counts[row] = values.size
        mean = (
            energy_mean(values) if mode is _Averaging.ENERGY else float(np.mean(values))
        )
        means[row] = mean
        type_a[row] = _type_a_arithmetic(values, mean=mean)
        u_b[row] = math.sqrt(float(np.mean(type_b[members] ** 2)))
    combined = np.sqrt(type_a**2 + u_b**2)
    centres = [bins.centres(key) for key in occupied]
    return BinnedSoundLevels(
        wind_speeds_m_s=np.array([c[1] for c in centres]),
        wind_directions_deg=(
            np.array([c[0] for c in centres]) if bins.by_direction else None
        ),
        counts=read_only(counts),
        mean_levels_db=read_only(means),
        type_a_uncertainty_db=read_only(type_a),
        type_b_uncertainty_db=read_only(u_b),
        combined_uncertainty_db=read_only(combined),
        averaging=mode.value,
        interval_levels_db=levels,
        interval_wind_speeds_m_s=bins.speeds_m_s,
        bin_width_m_s=bins.bin_width_m_s,
        sector_width_deg=bins.sector_width_deg,
    )


class BackgroundCorrectionRegime(StrEnum):
    """Which rule of 11.7 a bin's background correction followed.

    ``LOGARITHMIC``: the total is at least 3 dB above the background, and the
    background is subtracted (Equation (6)). ``THREE_DB``: the total is at
    least 0 dB but less than 3 dB above it, and the suggested 3 dB correction
    is applied.
    ``UNDETERMINED``: the background is above the total, and the turbine
    level cannot be determined (11.6.4).
    """

    LOGARITHMIC = "logarithmic"
    THREE_DB = "three_db"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class TurbineSoundLevels(OwnsArrays):
    """Background-corrected wind turbine levels per bin (10.3.2, 11.7).

    :ivar total_levels_db: The total (turbines on) bin levels, in dB.
    :ivar background_levels_db: The background (turbines off) bin levels.
    :ivar level_differences_db: Total minus background, in dB.
    :ivar turbine_levels_db: The turbine level :math:`L_{c,k}`, in dB:
        Equation (6) where the difference is at least 3 dB, the total minus
        3 dB where it is at least 0 dB but less than 3 dB, NaN where it is
        negative.
    :ivar turbine_uncertainty_db: Its standard uncertainty, in dB: Equation
        (7) for the logarithmic subtraction, the total's own uncertainty for
        the fixed 3 dB correction (a constant offset), NaN where undetermined.
    :ivar wind_speeds_m_s: The bins' wind speeds, in m/s, when known.
    :ivar wind_directions_deg: Centre of each bin's direction sector, in
        degrees, when binned by direction; ``None`` otherwise. Two bins of one
        wind speed class in different sectors are told apart by it.

    Which rule of 11.7 each bin followed (:attr:`regimes`) is read from the
    total and the background levels, so it is not a field.
    """

    total_levels_db: NDArray[np.float64]
    background_levels_db: NDArray[np.float64]
    level_differences_db: NDArray[np.float64]
    turbine_levels_db: NDArray[np.float64]
    turbine_uncertainty_db: NDArray[np.float64]
    _: KW_ONLY
    wind_speeds_m_s: NDArray[np.float64] | None
    wind_directions_deg: NDArray[np.float64] | None

    def __post_init__(self) -> None:
        """Reject a bin whose difference or turbine level is of another rule.

        The rule of 11.7 each bin follows is read from its total and its
        background level, so the difference beside them has to be theirs, and
        the turbine level the one that rule gives: Equation (6), the total
        less 3 dB, or NaN where the background is louder. Its uncertainty is
        NaN wherever the level is; elsewhere it comes from the uncertainties
        of the total and the background, which the result does not keep.

        :raises ValueError: if the columns disagree in rank or length, the
            difference is not the total less the background, the turbine
            level is not the one the rule of its bin gives, or an undetermined
            bin carries an uncertainty.
        """
        require_ranks(
            self,
            total_levels_db=1,
            background_levels_db=1,
            level_differences_db=1,
            turbine_levels_db=1,
            turbine_uncertainty_db=1,
        )
        require_same_length(
            self,
            "total_levels_db",
            "background_levels_db",
            "level_differences_db",
            "turbine_levels_db",
            "turbine_uncertainty_db",
            axis="bin",
        )
        total = np.asarray(self.total_levels_db, dtype=np.float64)
        background = np.asarray(self.background_levels_db, dtype=np.float64)
        levels = _turbine_levels(total, background)
        for name, expected, rule in (
            (
                "level_differences_db",
                total - background,
                "the total less the background",
            ),
            (
                "turbine_levels_db",
                levels,
                "the level the rule of 11.7 of each bin gives",
            ),
        ):
            if not np.allclose(
                getattr(self, name),
                expected,
                rtol=0.0,
                atol=_FIELD_SLACK_DB,
                equal_nan=True,
            ):
                msg = f"TurbineSoundLevels: '{name}' must be {rule}."
                raise ValueError(msg)
        uncertainty = np.asarray(self.turbine_uncertainty_db, dtype=np.float64)
        if not np.all(np.isnan(uncertainty[np.isnan(levels)])):
            msg = (
                "TurbineSoundLevels: 'turbine_uncertainty_db' must be NaN in a "
                "bin whose turbine level cannot be determined (11.6.4)."
            )
            raise ValueError(msg)

    @property
    def regimes(self) -> tuple[BackgroundCorrectionRegime, ...]:
        """The :class:`BackgroundCorrectionRegime` of each bin (11.7).

        Read from :attr:`total_levels_db` and :attr:`background_levels_db`:
        the logarithmic subtraction where the total is at least 3 dB above the
        background, the 3 dB correction where it is at least 0 dB but less
        than 3 dB above, and undetermined where the background is louder. A
        difference within a nanodecibel of 3 dB or of 0 dB is on that limit.
        """
        difference = np.asarray(self.total_levels_db) - np.asarray(
            self.background_levels_db
        )
        return tuple(_correction_regime(float(delta)) for delta in difference)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot total, background and turbine levels per bin.

        Binned by direction, each sector is drawn apart, in its own colour:
        the turbine level solid, the total dashed and the background dotted.
        The twelve 30° sectors of 10.1 take twelve colours; narrower sectors
        past the twelfth take them again, in the same order.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the turbine level line (one per sector).
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_turbine_sound_levels

        return plot_turbine_sound_levels(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _correction_regime(delta: float) -> BackgroundCorrectionRegime:
    """The rule of 11.7 a bin whose total is ``delta`` dB above its background follows.

    11.7 prints both rules to 3 dB inclusive: the logarithmic subtraction for
    a total "at least 3 dB" above the background and the 3 dB correction for
    one "between 0 dB to 3 dB" above it. Its own "less than 3 dB", in the
    sentence before the two rules and in NOTE 1, leaves 3 dB itself to the
    subtraction, so the correction runs from 0 dB, included, to 3 dB,
    excluded. A difference of two energy means reaches a limit only to within
    rounding, so a difference within a nanodecibel of a limit is on it.
    """
    if delta >= _BACKGROUND_MARGIN_DB - _BOUNDARY_SLACK_DB:
        return BackgroundCorrectionRegime.LOGARITHMIC
    if delta >= -_BOUNDARY_SLACK_DB:
        return BackgroundCorrectionRegime.THREE_DB
    return BackgroundCorrectionRegime.UNDETERMINED


def _turbine_levels(
    total: NDArray[np.float64], background: NDArray[np.float64]
) -> NDArray[np.float64]:
    """The turbine level of each bin by the rule of 11.7 its difference selects.

    Equation (6) where the total is at least 3 dB above the background, the
    total less 3 dB where it is at least 0 dB but less than 3 dB above, NaN
    where it is below.
    """
    e_t = 10.0 ** (total / 10.0)
    e_b = 10.0 ** (background / 10.0)
    corrected = np.full(total.shape, np.nan)
    for i, delta in enumerate(total - background):
        regime = _correction_regime(float(delta))
        if regime is BackgroundCorrectionRegime.LOGARITHMIC:
            corrected[i] = 10.0 * math.log10(e_t[i] - e_b[i])
        elif regime is BackgroundCorrectionRegime.THREE_DB:
            corrected[i] = total[i] - _BACKGROUND_MARGIN_DB
    return corrected


def turbine_sound_levels(
    total_levels_db: ArrayLike,
    background_levels_db: ArrayLike,
    *,
    total_uncertainty_db: ArrayLike = 0.0,
    background_uncertainty_db: ArrayLike = 0.0,
    wind_speeds_m_s: ArrayLike | None = None,
    wind_directions_deg: ArrayLike | None = None,
) -> TurbineSoundLevels:
    r"""Subtract the background from the total, bin by bin (10.3.2, 11.7).

    Where the bin-averaged total is at least 3 dB above the background, the
    turbine level is the logarithmic subtraction of Equation (6),
    :math:`L_{c,k} = 10 \lg(10^{L_{T,k}/10} - 10^{L_{B,k}/10})`, with the
    uncertainty of Equation (7). Where it is at least 0 dB but less than 3 dB
    above, 11.7 suggests a 3 dB correction instead, and a regulatory excess
    cannot then be found (11.7 NOTE 1). Where the background is louder than
    the total, no turbine level can be determined (11.6.4) and the bin is NaN.
    A difference within a nanodecibel of 3 dB or of 0 dB is on that limit, so
    the rounding of two energy means cannot move a bin from one rule to the
    other.

    :param total_levels_db: Bin levels with the turbines operating, in dB.
    :param background_levels_db: Bin levels with the turbines off, in dB.
    :param total_uncertainty_db: Combined standard uncertainty of each total
        level, Equation (5), in dB; NaN for a bin of one interval, whose
        uncertainty Equation (2) cannot give.
    :param background_uncertainty_db: That of each background level, in dB.
    :param wind_speeds_m_s: Optional wind speed of each bin, in m/s, for the
        plot.
    :param wind_directions_deg: Optional centre of each bin's direction
        sector, in degrees, for bins classified by direction as well (10.1);
        the plot draws each sector apart.
    :return: A :class:`TurbineSoundLevels`.
    :raises ValueError: If the inputs disagree in length or are not finite,
        or an uncertainty is infinite or negative.
    """
    total = require_finite_array(total_levels_db, "total_levels_db")
    background = require_finite_array(background_levels_db, "background_levels_db")
    if total.size != background.size:
        msg = "'total_levels_db' and 'background_levels_db' must pair bin by bin."
        raise ValueError(msg)
    u_t = np.broadcast_to(
        np.asarray(total_uncertainty_db, dtype=np.float64), total.shape
    )
    u_b = np.broadcast_to(
        np.asarray(background_uncertainty_db, dtype=np.float64), total.shape
    )
    for name, u in (("total_uncertainty_db", u_t), ("background_uncertainty_db", u_b)):
        # NaN is the uncertainty of a bin of one interval (Equation (2) needs
        # two); anything else must be a finite, non-negative standard
        # uncertainty.
        given = u[~np.isnan(u)]
        if not np.all(np.isfinite(given)) or np.any(given < 0.0):
            msg = (
                f"'{name}' must be finite and not negative, or NaN for a bin "
                "of one interval."
            )
            raise ValueError(msg)
    difference = total - background
    e_t = 10.0 ** (total / 10.0)
    e_b = 10.0 ** (background / 10.0)
    corrected = _turbine_levels(total, background)
    uncertainty = np.full(total.shape, np.nan)
    for i, delta in enumerate(difference):
        regime = _correction_regime(float(delta))
        if regime is BackgroundCorrectionRegime.LOGARITHMIC:
            uncertainty[i] = math.hypot(u_t[i] * e_t[i], u_b[i] * e_b[i]) / (
                e_t[i] - e_b[i]
            )
        elif regime is BackgroundCorrectionRegime.THREE_DB:
            uncertainty[i] = u_t[i]
    return TurbineSoundLevels(
        total_levels_db=total,
        background_levels_db=background,
        level_differences_db=read_only(difference),
        turbine_levels_db=read_only(corrected),
        turbine_uncertainty_db=read_only(uncertainty),
        wind_speeds_m_s=_optional_per_bin(
            wind_speeds_m_s, total.size, "wind_speeds_m_s"
        ),
        wind_directions_deg=_optional_per_bin(
            wind_directions_deg, total.size, "wind_directions_deg"
        ),
    )


def _optional_per_bin(
    values: ArrayLike | None, bins: int, name: str
) -> NDArray[np.float64] | None:
    """A finite array with one value per bin, or ``None`` if not given."""
    if values is None:
        return None
    out = require_finite_array(values, name)
    if out.size != bins:
        msg = f"'{name}' must hold one value per bin."
        raise ValueError(msg)
    return out


@dataclass(frozen=True)
class PredictedReceptorLevel(OwnsArrays):
    """A predicted receptor level and its uncertainty (10.3.4).

    :ivar turbine_levels_db: The predicted level from each turbine, in dB.
    :ivar sound_power_uncertainty_db: The sound power level uncertainty of
        each turbine, in dB.
    :ivar level_db: The energy sum of the turbines' levels, in dB.
    :ivar propagated_uncertainty_db: Equation (10), the level-weighted mean of
        the turbines' sound power uncertainties, in dB.
    :ivar combined_uncertainty_db: Equation (11), in dB.
    :ivar prediction_model_uncertainty_db: The model's uncertainty used, in dB.
    :ivar modelling_uncertainty_db: The modelling uncertainty used, in dB.
    """

    turbine_levels_db: NDArray[np.float64]
    sound_power_uncertainty_db: NDArray[np.float64]
    level_db: float
    propagated_uncertainty_db: float
    combined_uncertainty_db: float
    _: KW_ONLY
    prediction_model_uncertainty_db: float
    modelling_uncertainty_db: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each turbine's contribution and the total with its uncertainty.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the turbine bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_predicted_receptor_level

        return plot_predicted_receptor_level(
            self, ax=ax, language=check_language(language), **kwargs
        )


def predicted_receptor_level(
    turbine_levels_db: ArrayLike,
    sound_power_uncertainty_db: ArrayLike,
    *,
    prediction_model_uncertainty_db: float = PREDICTION_MODEL_UNCERTAINTY_DB,
    modelling_uncertainty_db: float = MODELLING_UNCERTAINTY_DB,
) -> PredictedReceptorLevel:
    r"""Sum a prediction over the turbines, with its uncertainty (10.3.4).

    The receptor level is the energy sum of the turbines' predicted levels.
    Equation (10) carries each turbine's sound power level uncertainty to it
    weighted by the turbine's share of the energy,

    .. math::

       u_{L_{\mathrm{A},k}} = \frac{\sum_i u_{L_{W\mathrm{A}},i,k} \,
       10^{L_{p\mathrm{A},i,k}/10}}{\sum_i 10^{L_{p\mathrm{A},i,k}/10}}

    (a linear, fully correlated combination), and Equation (11) adds the
    prediction model and the modelling in quadrature.

    :param turbine_levels_db: Predicted level at the receptor from each
        turbine, in dB.
    :param sound_power_uncertainty_db: Uncertainty of each turbine's sound
        power level, from IEC 61400-11, in dB (one value for all or one each).
    :param prediction_model_uncertainty_db: Standard uncertainty of the
        prediction model, in dB (2 dB by default, 10.3.4 NOTE).
    :param modelling_uncertainty_db: Uncertainty of the propagation
        modelling, in dB (0.5 dB by default).
    :return: A :class:`PredictedReceptorLevel`.
    :raises ValueError: If a value is not finite or an uncertainty is
        negative.
    """
    levels = require_finite_array(turbine_levels_db, "turbine_levels_db")
    u_w = np.broadcast_to(
        np.asarray(sound_power_uncertainty_db, dtype=np.float64), levels.shape
    )
    if not np.all(np.isfinite(u_w)) or np.any(u_w < 0.0):
        msg = "'sound_power_uncertainty_db' must be finite and not negative."
        raise ValueError(msg)
    u_model = require_finite(
        prediction_model_uncertainty_db, "prediction_model_uncertainty_db"
    )
    u_modelling = require_finite(modelling_uncertainty_db, "modelling_uncertainty_db")
    if u_model < 0.0 or u_modelling < 0.0:
        msg = "The model and modelling uncertainties must not be negative."
        raise ValueError(msg)
    weights = 10.0 ** (levels / 10.0)
    propagated = float(np.sum(u_w * weights) / np.sum(weights))
    return PredictedReceptorLevel(
        turbine_levels_db=levels,
        sound_power_uncertainty_db=u_w,
        level_db=energy_sum(levels),
        propagated_uncertainty_db=propagated,
        combined_uncertainty_db=math.sqrt(propagated**2 + u_model**2 + u_modelling**2),
        prediction_model_uncertainty_db=u_model,
        modelling_uncertainty_db=u_modelling,
    )


@dataclass(frozen=True)
class SoundRelevantTurbines(OwnsArrays):
    """The turbines that set the binning wind speed at a receptor (9.3.2.3).

    Which turbines are relevant is read from the predicted levels and the
    1.0 dB of 9.3.2.3, so it is not a field.

    :ivar predicted_levels_db: Each turbine's predicted level at the
        receptor, in dB, in the order given.
    """

    predicted_levels_db: NDArray[np.float64]

    @property
    def relevant(self) -> NDArray[np.bool_]:
        """Whether each turbine is sound relevant.

        The quietest is left out, and the next quietest after it, for as long
        as the total of those that remain has dropped by no more than 1.0 dB
        from the total of all ("reduced by more than 1,0 dB", 9.3.2.3: 1.0 dB
        itself is not more, and a drop within a nanodecibel of it is 1.0 dB).
        """
        levels = np.asarray(self.predicted_levels_db, dtype=np.float64)
        total = energy_sum(levels)
        relevant = np.ones(levels.size, dtype=np.bool_)
        for index in np.argsort(levels, kind="stable")[:-1]:
            trial = relevant.copy()
            trial[index] = False
            if (
                total - energy_sum(levels[trial])
                > _RELEVANCE_DROP_DB + _BOUNDARY_SLACK_DB
            ):
                break
            relevant = trial
        return relevant

    @property
    def total_level_db(self) -> float:
        """The predicted level of all turbines, in dB."""
        return energy_sum(self.predicted_levels_db)

    @property
    def relevant_level_db(self) -> float:
        """The predicted level of the relevant ones, in dB."""
        return energy_sum(np.asarray(self.predicted_levels_db)[self.relevant])

    @property
    def indices(self) -> tuple[int, ...]:
        """Positions of the sound relevant turbines, loudest first."""
        order = np.argsort(-self.predicted_levels_db, kind="stable")
        return tuple(int(i) for i in order if self.relevant[i])

    def binning_wind_speed_m_s(self, turbine_wind_speeds_m_s: ArrayLike) -> float:
        """The binning wind speed: the arithmetic mean over the relevant turbines.

        :param turbine_wind_speeds_m_s: The wind speed derived from each
            turbine (power curve or nacelle, recalculated to 10 m), in m/s,
            in the order of :attr:`predicted_levels_db`.
        :return: The mean of the relevant turbines' wind speeds, in m/s.
        :raises ValueError: If the speeds are not one per turbine or not
            finite.
        """
        speeds = require_finite_array(
            turbine_wind_speeds_m_s, "turbine_wind_speeds_m_s"
        )
        if speeds.size != self.predicted_levels_db.size:
            msg = "'turbine_wind_speeds_m_s' must hold one value per turbine."
            raise ValueError(msg)
        return float(np.mean(speeds[self.relevant]))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the turbines' levels, loudest first, the relevant ones marked.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the turbine bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_sound_relevant_turbines

        return plot_sound_relevant_turbines(
            self, ax=ax, language=check_language(language), **kwargs
        )


def sound_relevant_turbines(predicted_levels_db: ArrayLike) -> SoundRelevantTurbines:
    """Select the sound relevant turbines of a wind farm (9.3.2.3).

    The turbines are sorted by their predicted contribution at the receptor.
    The quietest is left out of the prediction, and the next quietest after
    it, for as long as the total of those that remain has dropped by no more
    than 1.0 dB from the total of all; the turbine whose exclusion would drop
    it by more is kept, with every louder one. Typically two or three
    turbines remain. A drop within a nanodecibel of 1.0 dB is a drop of
    1.0 dB, not more, so the rounding of the energy sums cannot keep a
    turbine the TS leaves out.

    :param predicted_levels_db: Each turbine's predicted level at the
        receptor, in dB.
    :return: A :class:`SoundRelevantTurbines`.
    :raises ValueError: If the levels are empty or not finite.
    """
    levels = require_finite_array(predicted_levels_db, "predicted_levels_db")
    return SoundRelevantTurbines(predicted_levels_db=levels)


# ---------------------------------------------------------------------------
# Low frequency sound (Annex C)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LowFrequencyLevel(OwnsArrays):
    r"""Low frequency sound at a receptor by Equation (C.1) (Annex C).

    Arrays with a turbine axis have one row per turbine and one column per
    band; the band arrays are summed over the turbines.

    :ivar frequencies_hz: The one-third-octave centres, in Hz.
    :ivar sound_power_levels_db: The turbines' band sound power levels.
    :ivar a_weighting_db: The A-weighting added to each band (zero when the
        result is unweighted).
    :ivar distance_terms_db: :math:`10 \lg(l^2 + h^2)` of each turbine, in dB.
    :ivar ground_correction_db: :math:`\Delta L_\mathrm{g,LF}` per band.
    :ivar air_attenuation_db: :math:`\Delta L_\mathrm{a}` per turbine and band.
    :ivar facade_insulation_db: :math:`\Delta L_\sigma` per band, or ``None``
        for an outdoor result.
    :ivar outdoor_levels_db: Outdoor band levels summed over the turbines.
    :ivar indoor_levels_db: Indoor band levels, or ``None``.
    :ivar outdoor_level_db: Energy sum of the outdoor bands, in dB.
    :ivar indoor_level_db: Energy sum of the indoor bands, or ``None``.
    :ivar a_weighted: Whether the levels are A-weighted.
    """

    frequencies_hz: NDArray[np.float64]
    sound_power_levels_db: NDArray[np.float64]
    a_weighting_db: NDArray[np.float64]
    distance_terms_db: NDArray[np.float64]
    ground_correction_db: NDArray[np.float64]
    air_attenuation_db: NDArray[np.float64]
    facade_insulation_db: NDArray[np.float64] | None
    outdoor_levels_db: NDArray[np.float64]
    indoor_levels_db: NDArray[np.float64] | None
    outdoor_level_db: float
    indoor_level_db: float | None
    _: KW_ONLY
    a_weighted: bool

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the outdoor and indoor band levels.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the outdoor levels.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_low_frequency_level

        return plot_low_frequency_level(
            self, ax=ax, language=check_language(language), **kwargs
        )


def wind_turbine_low_frequency_level(
    sound_power_levels_db: ArrayLike,
    *,
    distance_m: ArrayLike,
    hub_height_m: ArrayLike,
    frequencies_hz: ArrayLike = LOW_FREQUENCY_BANDS_HZ,
    ground_correction_db: ArrayLike | None = None,
    air_attenuation_db_per_km: ArrayLike | None = None,
    facade_insulation_db: ArrayLike | None = None,
    a_weighted: bool = True,
) -> LowFrequencyLevel:
    r"""Low frequency sound level at a receptor (Annex C, Equation (C.1)).

    .. math::

       L_{p,\mathrm{LF}} = L_{W,\mathrm{LF}} - 10 \lg(l^2 + h^2) - 11~\mathrm{dB}
       + \Delta L_\mathrm{g,LF} - \Delta L_\mathrm{a} - \Delta L_\sigma
       \tag{C.1}

    band by band, with :math:`\Delta L_\mathrm{a} = \alpha \sqrt{l^2 + h^2}`
    (the distance in km for :math:`\alpha` in dB/km) and 11 dB the
    :math:`10 \lg(4\pi)` of the text, taken as printed. The contributions of
    the relevant turbines are summed energetically per band, and the
    equivalent level is the energy sum of the bands (C.3, C.5); the Danish
    criterion of C.6.1 sums 10 Hz to 160 Hz, so pass those bands for it.

    :param sound_power_levels_db: Band sound power levels from IEC 61400-11,
        in dB: one row per turbine, or one row for a single turbine.
    :param distance_m: Horizontal distance :math:`l` from each tower to the
        receptor, in m.
    :param hub_height_m: Hub height :math:`h` of each turbine, in m.
    :param frequencies_hz: Nominal centre of each column, in Hz (10 Hz to
        200 Hz by default, :data:`LOW_FREQUENCY_BANDS_HZ`).
    :param ground_correction_db: :math:`\Delta L_\mathrm{g,LF}` per band;
        ``None`` for Table C.2 (onshore, impedance class D).
    :param air_attenuation_db_per_km: :math:`\alpha` per band, in dB/km,
        zero or positive (the ISO 9613-1 absorption coefficient, C.2);
        ``None`` for Table C.2, as printed (see
        :data:`LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM`).
    :param facade_insulation_db: :math:`\Delta L_\sigma` per band, for an
        indoor level (for instance a row of
        :data:`LOW_FREQUENCY_FACADE_INSULATION_DB`); ``None`` for the outdoor
        level alone.
    :param a_weighted: Add the A-weighting of Table C.4 (IEC 61672-1) to each
        band (the default), or give unweighted levels.
    :return: A :class:`LowFrequencyLevel`.
    :raises ValueError: If the shapes disagree, a distance or height is not
        positive, an air attenuation coefficient is negative, a default table
        has no value at a supplied band, or ``a_weighted`` is not a boolean.
    """
    if not isinstance(a_weighted, (bool, np.bool_)):
        msg = (
            f"'a_weighted' must be True or False; got {a_weighted!r}. A string "
            "such as 'False' is truthy and would add the A-weighting."
        )
        raise ValueError(msg)
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    power = require_finite_matrix(sound_power_levels_db, "sound_power_levels_db")
    if power.shape[1] != freqs.size:
        msg = (
            "'sound_power_levels_db' must hold one row per turbine and one "
            f"column per band ({freqs.size}); got {power.shape[1]} columns."
        )
        raise ValueError(msg)
    turbines = power.shape[0]
    distances = np.broadcast_to(np.asarray(distance_m, dtype=np.float64), (turbines,))
    heights = np.broadcast_to(np.asarray(hub_height_m, dtype=np.float64), (turbines,))
    for name, values in (("distance_m", distances), ("hub_height_m", heights)):
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            msg = f"'{name}' must be finite and positive."
            raise ValueError(msg)
    table_bands = (LOW_FREQUENCY_BANDS_HZ, LOW_FREQUENCY_GROUND_CORRECTION_DB)
    ground = (
        _nominal_lookup(freqs, table_bands, "Table C.2")
        if ground_correction_db is None
        else _per_band(ground_correction_db, freqs.size, "ground_correction_db")
    )
    alpha = (
        _nominal_lookup(
            freqs,
            (LOW_FREQUENCY_BANDS_HZ, LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM),
            "Table C.2",
        )
        if air_attenuation_db_per_km is None
        else _per_band(
            air_attenuation_db_per_km,
            freqs.size,
            "air_attenuation_db_per_km",
            non_negative=True,
        )
    )
    facade = (
        None
        if facade_insulation_db is None
        else _per_band(facade_insulation_db, freqs.size, "facade_insulation_db")
    )
    weighting = (
        _nominal_lookup(freqs, _A_WEIGHTING_DB, "The A-weighting of IEC 61672-1")
        if a_weighted
        else np.zeros(freqs.size)
    )
    slant_m = np.hypot(distances, heights)
    distance_terms = 10.0 * np.log10(slant_m**2)
    air = alpha[np.newaxis, :] * slant_m[:, np.newaxis] / 1000.0
    outdoor_per_turbine = (
        power
        + weighting
        - distance_terms[:, np.newaxis]
        - _DISTANCE_TERM_DB
        + ground
        - air
    )
    outdoor = np.asarray(energy_sum(outdoor_per_turbine, axis=0), dtype=np.float64)
    indoor = None if facade is None else outdoor - facade
    return LowFrequencyLevel(
        frequencies_hz=freqs,
        sound_power_levels_db=power,
        a_weighting_db=read_only(weighting),
        distance_terms_db=read_only(distance_terms),
        ground_correction_db=ground,
        air_attenuation_db=read_only(air),
        facade_insulation_db=facade,
        outdoor_levels_db=read_only(outdoor),
        indoor_levels_db=None if indoor is None else read_only(indoor),
        outdoor_level_db=energy_sum(outdoor),
        indoor_level_db=None if indoor is None else energy_sum(indoor),
        a_weighted=bool(a_weighted),
    )


def _per_band(
    values: ArrayLike, bands: int, name: str, *, non_negative: bool = False
) -> NDArray[np.float64]:
    r"""A finite per-band array of the right length.

    ``non_negative`` refuses a negative value: the air absorption coefficient
    of Equation (C.1) is one (ISO 9613-1, C.2), and a negative one would turn
    :math:`\Delta L_\mathrm{a}` into a gain. The ground and facade terms may
    be negative (Table C.3 prints -0,2 dB).
    """
    out = require_finite_array(values, name)
    if out.size != bands:
        msg = f"'{name}' must hold one value per band ({bands}); got {out.size}."
        raise ValueError(msg)
    if non_negative and np.any(out < 0.0):
        msg = f"'{name}' must not be negative; got {float(np.min(out)):g}."
        raise ValueError(msg)
    return out


# ---------------------------------------------------------------------------
# Emergence (Annex J) and the rating level (Annex A)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SoundEmergence(OwnsArrays):
    r"""The emergence criterion per wind speed class (Annex J, Equation (J.1)).

    :ivar ambient_levels_db: The ambient sound criterion per class, in dB.
    :ivar background_levels_db: The background sound criterion per class.
    :ivar emergence_db: :math:`E(j) = L_\mathrm{Amb}(j) - L_\mathrm{Res}(j)`.
    :ivar wind_speeds_m_s: The wind speed classes, in m/s, when given.
    """

    ambient_levels_db: NDArray[np.float64]
    background_levels_db: NDArray[np.float64]
    emergence_db: NDArray[np.float64]
    _: KW_ONLY
    wind_speeds_m_s: NDArray[np.float64] | None

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the emergence of each wind speed class.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the emergence bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_sound_emergence

        return plot_sound_emergence(
            self, ax=ax, language=check_language(language), **kwargs
        )


def sound_emergence(
    ambient_levels_db: ArrayLike,
    background_levels_db: ArrayLike,
    *,
    wind_speeds_m_s: ArrayLike | None = None,
) -> SoundEmergence:
    r"""The emergence criterion of each wind speed class (Equation (J.1)).

    :math:`E(j) = L_\mathrm{Amb}(j) - L_\mathrm{R\acute{e}s}(j)`, the
    difference of the ambient sound criterion (turbines operating) and the
    background sound criterion (turbines stopped) for each complete wind speed
    class, the criterion of French regulation. The TS warns it is not to be
    confused with limits on the difference between the turbine sound and the
    background.

    :param ambient_levels_db: The ambient sound criterion of each class, in dB.
    :param background_levels_db: The background sound criterion of each class.
    :param wind_speeds_m_s: Optional wind speed of each class, in m/s.
    :return: A :class:`SoundEmergence`.
    :raises ValueError: If the inputs disagree in length or are not finite.
    """
    ambient = require_finite_array(ambient_levels_db, "ambient_levels_db")
    background = require_finite_array(background_levels_db, "background_levels_db")
    if ambient.size != background.size:
        msg = "'ambient_levels_db' and 'background_levels_db' must pair class by class."
        raise ValueError(msg)
    speeds = None
    if wind_speeds_m_s is not None:
        speeds = require_finite_array(wind_speeds_m_s, "wind_speeds_m_s")
        if speeds.size != ambient.size:
            msg = "'wind_speeds_m_s' must hold one value per class."
            raise ValueError(msg)
    return SoundEmergence(
        ambient_levels_db=ambient,
        background_levels_db=background,
        emergence_db=read_only(ambient - background),
        wind_speeds_m_s=speeds,
    )


def amplitude_modulation_adjustment(
    modulation_depth_db: ArrayLike,
) -> NDArray[np.float64] | float:
    r"""The amplitude modulation adjustment of Figure A.1, in dB.

    The example adjustment of A.3: none below a modulation depth of 3 dB,
    3 dB at 3 dB, rising linearly to 5 dB at 10 dB and 5 dB above it. The
    figure is drawn to 12 dB; the 5 dB is kept beyond. The depth is the
    reconstructed time-series modulation depth of clause 13 (the AM rating of
    :func:`~phonometry.environment.assessment.wind_turbine_modulation.amplitude_modulation_period`).

    :param modulation_depth_db: The modulation depth, in dB.
    :return: The adjustment :math:`K_\mathrm{am}`, in dB; a ``float`` for a
        scalar depth.
    :raises ValueError: If a depth is negative or not finite.
    """
    depth = np.asarray(modulation_depth_db, dtype=np.float64)
    if not np.all(np.isfinite(depth)) or np.any(depth < 0.0):
        msg = "'modulation_depth_db' must be finite and not negative."
        raise ValueError(msg)
    slope = (_AM_MAXIMUM_ADJUSTMENT_DB - _AM_ONSET_ADJUSTMENT_DB) / (
        _AM_SATURATION_DB - _AM_ONSET_DB
    )
    rising = _AM_ONSET_ADJUSTMENT_DB + slope * (depth - _AM_ONSET_DB)
    out = np.where(
        depth < _AM_ONSET_DB, 0.0, np.minimum(rising, _AM_MAXIMUM_ADJUSTMENT_DB)
    )
    return float(out) if out.ndim == 0 else np.asarray(out, dtype=np.float64)


@dataclass(frozen=True)
class WindTurbineRatingLevel(RichDisplay):
    r"""The rating level of wind turbine sound (Annex A, A.1).

    :ivar equivalent_level_db: The equivalent continuous level
        :math:`L_\mathrm{eq}`, in dB.
    :ivar adjustments_db: The three candidate adjustments, keyed
        ``"tonal"``, ``"amplitude_modulation"`` and ``"impulsive"``, in dB.
    :ivar governing: The adjustment applied, the most severe of the three, or
        ``None`` when all three are zero.
    :ivar rating_level_db: :math:`L_\mathrm{r} = L_\mathrm{eq} + K`, in dB.
    """

    equivalent_level_db: float
    adjustments_db: Mapping[str, float]
    governing: str | None
    rating_level_db: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the three candidate adjustments with the governing one marked.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the adjustment bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_wind_turbine_rating_level

        return plot_wind_turbine_rating_level(
            self, ax=ax, language=check_language(language), **kwargs
        )


def wind_turbine_rating_level(
    equivalent_level_db: float,
    *,
    tonal_adjustment_db: float = 0.0,
    amplitude_modulation_adjustment_db: float = 0.0,
    impulsive_adjustment_db: float = 0.0,
) -> WindTurbineRatingLevel:
    r"""Rating level of wind turbine sound (Annex A, A.1).

    :math:`L_\mathrm{r} = L_\mathrm{eq} + K` with :math:`K` the most severe of
    the tonal adjustment :math:`K_\mathrm{T}`, the amplitude modulation
    adjustment :math:`K_\mathrm{am}` and the impulsive adjustment
    :math:`K_\mathrm{I}`: only one type is applied at a time. Local regulation
    usually defines the adjustments; the TS's examples are Table A.1 for
    :math:`K_\mathrm{T}`
    (:func:`~phonometry.environment.assessment.measurement.tonal_adjustment_from_mean_audibility`,
    ISO 1996-2:2017 Table J.1, with its 3 dB-step variant), Figure A.1 for
    :math:`K_\mathrm{am}` (:func:`amplitude_modulation_adjustment`) and
    ISO/PAS 1996-3 for :math:`K_\mathrm{I}`
    (:func:`~phonometry.environment.assessment.impulsive_sound.impulse_adjustment`).

    :param equivalent_level_db: The equivalent continuous level, in dB.
    :param tonal_adjustment_db: :math:`K_\mathrm{T}`, in dB.
    :param amplitude_modulation_adjustment_db: :math:`K_\mathrm{am}`, in dB.
    :param impulsive_adjustment_db: :math:`K_\mathrm{I}`, in dB.
    :return: A :class:`WindTurbineRatingLevel`.
    :raises ValueError: If a value is not finite or an adjustment is negative.
    """
    leq = require_finite(equivalent_level_db, "equivalent_level_db")
    adjustments = {
        "tonal": require_finite(tonal_adjustment_db, "tonal_adjustment_db"),
        "amplitude_modulation": require_finite(
            amplitude_modulation_adjustment_db, "amplitude_modulation_adjustment_db"
        ),
        "impulsive": require_finite(impulsive_adjustment_db, "impulsive_adjustment_db"),
    }
    if any(value < 0.0 for value in adjustments.values()):
        msg = "The adjustments must not be negative."
        raise ValueError(msg)
    governing = max(adjustments, key=lambda name: adjustments[name])
    applied = adjustments[governing]
    return WindTurbineRatingLevel(
        equivalent_level_db=leq,
        adjustments_db=MappingProxyType(adjustments),
        governing=governing if applied > 0.0 else None,
        rating_level_db=leq + applied,
    )


# ---------------------------------------------------------------------------
# Upper tone search frequency (12.5.2.4, Table 7)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ToneSearchLimit(OwnsArrays):
    """The upper frequency of the tonal search range (12.5.2.4).

    :ivar distance_m: Distance from the nearest turbine, in m.
    :ivar frequencies_hz: The nominal one-third-octave centres searched.
    :ivar attenuation_db: ISO 9613-1 attenuation of each band over the
        distance, at the exact mid-band frequency, in dB.
    :ivar upper_frequency_hz: The nominal centre of the lowest band
        attenuated by at least 20 dB, or 10 kHz when none is.
    :ivar temperature_c: Air temperature, in degrees C.
    :ivar relative_humidity_percent: Relative humidity, in %.
    :ivar atmospheric_pressure_kpa: Atmospheric pressure, in kPa.
    """

    distance_m: float
    frequencies_hz: NDArray[np.float64]
    attenuation_db: NDArray[np.float64]
    upper_frequency_hz: float
    _: KW_ONLY
    temperature_c: float
    relative_humidity_percent: float
    atmospheric_pressure_kpa: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the band attenuation over the distance and the 20 dB line.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the attenuation curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_tone_search_limit

        return plot_tone_search_limit(
            self, ax=ax, language=check_language(language), **kwargs
        )


def upper_tone_search_frequency(
    distance_m: float,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
) -> ToneSearchLimit:
    """Upper frequency of the search for tones at a receptor (12.5.2.4).

    Tones in a one-third-octave band that ISO 9613-1 attenuates by at least
    20 dB over the distance to the nearest turbine are typically of no concern
    to its neighbours, and every higher band is attenuated more; the lowest
    such band sets the top of the search range. The attenuation is evaluated
    at the exact mid-band frequency of each band (ISO 9613-1), which
    reproduces the printed rows of Table 7; the search stops at 10 kHz, the
    top of ISO 9613-1, when no band reaches 20 dB.

    :param distance_m: Distance from the source to the receiver, in m.
    :param temperature_c: Air temperature, in degrees C.
    :param relative_humidity_percent: Relative humidity, in %.
    :param atmospheric_pressure_kpa: Atmospheric pressure, in kPa.
    :return: A :class:`ToneSearchLimit`.
    :raises ValueError: If the distance is not positive or the atmosphere is
        outside what ISO 9613-1 accepts.
    """
    from ..propagation.air_absorption import air_attenuation

    distance = require_positive(distance_m, "distance_m")
    alpha = np.asarray(
        air_attenuation(
            TONE_SEARCH_BANDS_HZ,
            temperature_c=temperature_c,
            relative_humidity_percent=relative_humidity_percent,
            atmospheric_pressure_kpa=atmospheric_pressure_kpa,
            exact_midband=True,
        ),
        dtype=np.float64,
    )
    attenuation = alpha * distance
    reached = np.nonzero(attenuation >= _TONE_SEARCH_ATTENUATION_DB)[0]
    upper = (
        float(TONE_SEARCH_BANDS_HZ[reached[0]])
        if reached.size
        else float(TONE_SEARCH_BANDS_HZ[-1])
    )
    return ToneSearchLimit(
        distance_m=distance,
        frequencies_hz=TONE_SEARCH_BANDS_HZ,
        attenuation_db=read_only(attenuation),
        upper_frequency_hz=upper,
        temperature_c=float(temperature_c),
        relative_humidity_percent=float(relative_humidity_percent),
        atmospheric_pressure_kpa=float(atmospheric_pressure_kpa),
    )
