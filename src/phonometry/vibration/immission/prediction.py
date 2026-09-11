#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Predicting vibration before it is measured (DIN 4150-1:2001-06).

Part 1 of DIN 4150 is the first question of the series: before a blast is
fired, a pile driven or a line built, how much vibration will reach the
building, and how much of it will the floors feel. It gives no recipe, and
says so in its foreword; what it gives is the shape of every answer, the
handful of constants experience has fixed, and twenty-seven figures of
measured cases to show what the shapes look like in the ground. The shapes
and the constants are here.

**Propagation** (Clause 4.2). Beyond the reference distance
:math:`R_1 = a/2 + \lambda_R` of Formula (1), half the source's extent plus a
surface wavelength, the velocity amplitude decays as

.. math::

   \bar v = \bar v_1 \left(\frac{R}{R_1}\right)^{-n} \exp[-\alpha (R - R_1)]

(Formula (2)): geometric spreading with an exponent :math:`n` that Figure 1
fixes at 0, 0,5, 1 or 1,5 by whether the source is a line or a point,
harmonic or impulsive, and the wave a surface or a body wave; and material
damping with :math:`\alpha \approx 2\pi D / \lambda`, the damping ratio of the
ground over the wavelength, which for loose ground may be taken as 0,01 at
most in a preliminary estimate. Nearer than :math:`R_1` the formula does not
hold. A train is a chain of point sources and decays with an exponent
between 0,3 and 0,5.

**Into the building** (Clause 4.3). A building on the ground is a mass on a
spring with the natural frequency of Formula (3), about 15 Hz for one or two
storeys and under 8 Hz above six; the foundation passes at most
:math:`1 / (2 D_0)` of the ground's amplitude at that frequency, 2 for the
0,25 of loose ground, and a mean of 0,5 above it, or all of it on rock; a
floor amplifies by at most :math:`1 / (2 D_1)`, 10 to 25 for a concrete
floor; and the lowest horizontal natural frequency of a building of five
storeys or more is about :math:`10 / n` Hz (Formula (4)).

**Sources** (Clause 5). A blast in the far field follows
:math:`v_{\max} = k (L/L_0)^b (R/R_0)^{-m}` (Formula (5)) with the charge per
delay :math:`L` and constants from trial blasts; a falling mass follows the
same with the root of its fall energy (Formula (6)); a hall of :math:`N`
similar machines gives :math:`\chi \, v_B \sqrt{N}` at a point where
:math:`N_B` of them were measured (Formula (7)), with the correction
:math:`\chi` of Figure 3, which is printed as a nomogram and is here as the
nomogram read at a five-hundredth. Rail traffic excites at the speed over
the spacing of whatever repeats along the track, sleepers first, and its
vehicles have natural frequencies of their own.

**What is not here.** The measured cases of Annex A print their inputs and
their peaks and say themselves that they are not a basis for a prediction;
two of their figures are drawn from the formulas above with every parameter
printed, and those are the conformance rows. Two symbol lists print a
distance in millimetres, one working frequency has its sign the wrong way
and one legend swaps two line styles; all in ``docs/ERRATA.md``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_count,
    require_finite_array,
    require_non_negative,
    require_positive,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "BLASTING_RELEVANT_DISTANCE_M",
    "FLOOR_DAMPING_RATIO_RANGE",
    "FOUNDATION_TRANSFER_ABOVE_RESONANCE",
    "LOOSE_GROUND_DAMPING_RATIO",
    "LOOSE_GROUND_SYSTEM_DAMPING",
    "MACHINE_COUNT_AXIS",
    "MACHINE_COUNT_CORRECTION",
    "MACHINE_FREQUENCY_BANDS_HZ",
    "MEDIUM_SOIL_SHEAR_WAVE_SPEED_M_S",
    "RAIL_INFLUENCE_RANGE_M",
    "RAIL_SUPPORT_SPACING_M",
    "SOURCE_EXPONENTS",
    "STOREY_FORMULA_MIN_STOREYS",
    "TRACK_TRANSMITTED_BANDS_HZ",
    "TRAIN_CHAIN_EXPONENT_RANGE",
    "VEHICLE_NATURAL_FREQUENCIES_HZ",
    "attenuation_coefficient_per_m",
    "blast_peak_velocity_mm_s",
    "fall_energy_kj",
    "far_field_velocity_mm_s",
    "floor_transfer_max",
    "foundation_transfer_max",
    "geometric_exponent",
    "impact_peak_velocity_mm_s",
    "machine_count_correction",
    "machine_hall_velocity_mm_s",
    "material_damping_factor",
    "reference_distance_m",
    "soil_building_frequency_guide_hz",
    "soil_building_natural_frequency_hz",
    "storey_frequency_hz",
    "track_excitation_frequency_hz",
]

#: Figure 1 (printed page 6): the exponent :math:`n` of Formula (2) by the
#: geometry of the source (``"point"`` or ``"line"``), its character in time
#: (``"harmonic"``, stationary, or ``"impulsive"``) and the wave that
#: carries it (``"surface"`` or ``"body"``). Each of point, impulsive and
#: body adds 0,5 to the 0 of a harmonic line source on a surface wave.
SOURCE_EXPONENTS: dict[tuple[str, str, str], float] = {
    ("line", "harmonic", "surface"): 0.0,
    ("line", "harmonic", "body"): 0.5,
    ("point", "harmonic", "surface"): 0.5,
    ("line", "impulsive", "surface"): 0.5,
    ("point", "harmonic", "body"): 1.0,
    ("line", "impulsive", "body"): 1.0,
    ("point", "impulsive", "surface"): 1.0,
    ("point", "impulsive", "body"): 1.5,
}

#: The far-field exponent of a train, a chain of point sources not excited
#: in phase: between 0,3 and 0,5 (Clause 4.2).
TRAIN_CHAIN_EXPONENT_RANGE: tuple[float, float] = (0.3, 0.5)

#: The damping ratio :math:`D` a preliminary estimate may assume for loose
#: ground at most (Clause 4.2): 0,01. More has to be proven.
LOOSE_GROUND_DAMPING_RATIO: float = 0.01

#: The shear wave speed of a ground of medium stiffness (Clause 4.3), in
#: metres per second: 150 to 200.
MEDIUM_SOIL_SHEAR_WAVE_SPEED_M_S: tuple[float, float] = (150.0, 200.0)

#: The system damping :math:`D_0` of a building on loose ground that
#: Clause 4.3 lets one assume: 0,25, which caps the foundation's transfer at
#: resonance at 2.
LOOSE_GROUND_SYSTEM_DAMPING: float = 0.25

#: The mean transfer value of a foundation above the natural frequency of
#: the building on its ground (Clause 4.3): 0,5. On rock there is no
#: reduction at all.
FOUNDATION_TRANSFER_ABOVE_RESONANCE: float = 0.5

#: The damping ratio :math:`D_1` of a reinforced concrete floor (Clause
#: 4.3): between 0,02 and 0,05, so the floor amplifies by 10 to 25 at most.
FLOOR_DAMPING_RATIO_RANGE: tuple[float, float] = (0.02, 0.05)

#: The fewest storeys the storey formula of Formula (4) is meant for: 5.
STOREY_FORMULA_MIN_STOREYS: int = 5

#: How far the vibration of a blast is very rarely relevant beyond (Clause
#: 5.1.2), in metres: 1500 for quarry blasting, 400 for construction
#: blasting.
BLASTING_RELEVANT_DISTANCE_M: dict[str, float] = {
    "quarry": 1500.0,
    "construction": 400.0,
}

#: The spacing of the rail supports (Clause 5.3.2), in metres: 0,6 to 0,9.
RAIL_SUPPORT_SPACING_M: tuple[float, float] = (0.6, 0.9)

#: The natural frequencies of the parts of a rail vehicle, which do not
#: move with its speed (Clause 5.3.2), in hertz: the car body on its
#: secondary suspension, 1 to 3; the bogie on its primary suspension, 6 to
#: 10.
VEHICLE_NATURAL_FREQUENCIES_HZ: dict[str, tuple[float, float]] = {
    "car_body": (1.0, 3.0),
    "bogie": (6.0, 10.0),
}

#: The bands a form of track passes on preferentially (Clause 5.3.2), in
#: hertz: ballasted track 40 to 80, a tunnel with under-ballast mats 15 to
#: 40, a mass-spring system 5 to 20.
TRACK_TRANSMITTED_BANDS_HZ: dict[str, tuple[float, float]] = {
    "ballast": (40.0, 80.0),
    "under_ballast_mat": (15.0, 40.0),
    "mass_spring": (5.0, 20.0),
}

#: How far rail vibration reaches at most (Clause 5.3.2), in metres: 80,
#: further on soft layers.
RAIL_INFLUENCE_RANGE_M: float = 80.0

#: The frequencies Clause 5.4 gives for machines, in hertz: the coupled
#: rams of a counter-blow hammer 4 to 8, the horizontal pendulum of a
#: forging press on its foundation 5 to 15, a frame saw 4 to 8 with its
#: harmonics.
MACHINE_FREQUENCY_BANDS_HZ: dict[str, tuple[float, float]] = {
    "counter_blow_hammer": (4.0, 8.0),
    "forging_press_horizontal": (5.0, 15.0),
    "frame_saw": (4.0, 8.0),
}

#: Figure 3 (printed page 14): the numbers of machines :math:`N` the
#: correction :math:`\chi` of Formula (7) is read at, from 4 to 100.
MACHINE_COUNT_AXIS: tuple[int, ...] = (
    4, 5, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100,
)  # fmt: skip

#: Figure 3 (printed page 14): the correction :math:`\chi` of Formula (7)
#: along :data:`MACHINE_COUNT_AXIS`, for the six numbers :math:`N_B` the
#: figure draws a curve for. The standard prints it as a nomogram and
#: nothing else; these are the curves read off the page at the centre of
#: their stroke, to a five-hundredth. None of the six starts at
#: :math:`1/\sqrt{N_B}`, so it is an empirical family and not a rule.
MACHINE_COUNT_CORRECTION: dict[int, tuple[float, ...]] = {
    3: (
        0.551, 0.537, 0.519, 0.496, 0.471, 0.423, 0.383, 0.360, 0.336, 0.323,
        0.309, 0.300, 0.292, 0.289, 0.289, 0.289, 0.286,
    ),
    5: (
        0.455, 0.444, 0.427, 0.406, 0.386, 0.342, 0.308, 0.292, 0.276, 0.264,
        0.256, 0.245, 0.239, 0.238, 0.236, 0.234, 0.234,
    ),
    10: (
        0.365, 0.355, 0.342, 0.327, 0.308, 0.280, 0.252, 0.239, 0.225, 0.216,
        0.207, 0.200, 0.193, 0.192, 0.192, 0.191, 0.189,
    ),
    30: (
        0.292, 0.283, 0.273, 0.258, 0.243, 0.220, 0.200, 0.188, 0.176, 0.169,
        0.164, 0.157, 0.153, 0.153, 0.151, 0.150, 0.149,
    ),
    60: (
        0.242, 0.239, 0.230, 0.220, 0.207, 0.189, 0.170, 0.158, 0.148, 0.142,
        0.136, 0.130, 0.127, 0.127, 0.126, 0.125, 0.125,
    ),
    100: (
        0.189, 0.188, 0.180, 0.173, 0.161, 0.147, 0.134, 0.125, 0.117, 0.111,
        0.108, 0.100, 0.100, 0.100, 0.100, 0.100, 0.099,
    ),
}  # fmt: skip

_GEOMETRIES = ("point", "line")
_CHARACTERS = ("harmonic", "impulsive")
_WAVES = ("surface", "body")
#: Storeys up to which a building on medium ground answers at about 15 Hz,
#: and up to which at 8 to 12 Hz (Clause 4.3).
_LOW_RISE_STOREYS = 2
_MID_RISE_STOREYS = 6
_LOW_RISE_HZ = (15.0, 15.0)
_MID_RISE_HZ = (8.0, 12.0)
#: Two storeys are printed in both ranges of the clause: the union.
_TWO_STOREY_HZ = (8.0, 15.0)
_HIGH_RISE_HZ = (0.0, 8.0)
#: The reference charge and distance of Formula (5) and the reference energy
#: of Formula (6): 1 kg, 1 m and 1 kJ.
_REFERENCE_CHARGE_KG = 1.0
_REFERENCE_DISTANCE_M = 1.0
_REFERENCE_ENERGY_KJ = 1.0
#: The energy in a fall: a weight in kilonewtons through a height in metres
#: is that many kilojoules.
_KJ_PER_KN_M = 1.0


def geometric_exponent(*, geometry: str, character: str, wave: str) -> float:
    """The exponent :math:`n` of Formula (2) for a source and a wave, Figure 1.

    :param geometry: ``"point"`` or ``"line"``.
    :param character: ``"harmonic"`` (stationary) or ``"impulsive"``.
    :param wave: ``"surface"`` or ``"body"``.
    :return: :math:`n`: 0, 0,5, 1 or 1,5.
    :raises ValueError: For an unknown geometry, character or wave.
    """
    key = (
        require_choice(str(geometry), "geometry", _GEOMETRIES),
        require_choice(str(character), "character", _CHARACTERS),
        require_choice(str(wave), "wave", _WAVES),
    )
    return SOURCE_EXPONENTS[key]


def reference_distance_m(
    source_extent_m: float, *, rayleigh_wavelength_m: float
) -> float:
    r"""The distance the far field begins at, Formula (1).

    :math:`R_1 = a/2 + \lambda_R`: half the extent of the source along the
    direction of propagation plus a wavelength of the surface wave. Nearer
    than it Formula (2) does not hold.

    :param source_extent_m: :math:`a`, in metres, not negative.
    :param rayleigh_wavelength_m: :math:`\lambda_R`, in metres.
    :return: :math:`R_1`, in metres.
    :raises ValueError: For a negative extent or a non-positive wavelength.
    """
    extent = require_non_negative(source_extent_m, "source_extent_m")
    wavelength = require_positive(rayleigh_wavelength_m, "rayleigh_wavelength_m")
    return extent / 2.0 + wavelength


def attenuation_coefficient_per_m(
    damping_ratio: float, *, wavelength_m: float
) -> float:
    r"""The material damping of the ground, :math:`\alpha` of Formula (2).

    :math:`\alpha \approx 2\pi D / \lambda` with :math:`\lambda = c / f` the
    wavelength that matters. Figure A.19 prints 0,005 for a damping ratio of
    0,01 and a wavelength of 12,5 m.

    :param damping_ratio: :math:`D`, not negative; 0,01 at most for loose
        ground in a preliminary estimate.
    :param wavelength_m: :math:`\lambda`, in metres.
    :return: :math:`\alpha`, in reciprocal metres.
    :raises ValueError: For a negative damping ratio or a non-positive
        wavelength.
    """
    damping = require_non_negative(damping_ratio, "damping_ratio")
    wavelength = require_positive(wavelength_m, "wavelength_m")
    return 2.0 * math.pi * damping / wavelength


def far_field_velocity_mm_s(
    reference_velocity_mm_s: float,
    distance_m: ArrayLike,
    *,
    reference_distance_m: float,
    exponent: float,
    attenuation_per_m: float = 0.0,
) -> NDArray[np.float64]:
    r"""The velocity amplitude at a distance in the far field, Formula (2).

    :math:`\bar v = \bar v_1 (R / R_1)^{-n} \exp[-\alpha (R - R_1)]`: the
    amplitude at the reference distance, spread with the exponent of Figure
    1 and damped with :math:`\alpha`. Figure A.19 draws it for 0,44 mm/s at
    13 m with :math:`\alpha` = 0,005 for the three exponents 0, 0,5 and 1.

    :param reference_velocity_mm_s: :math:`\bar v_1`, at :math:`R_1`, in
        millimetres per second.
    :param distance_m: :math:`R`, in metres, one or many, none nearer than
        :math:`R_1`.
    :param reference_distance_m: :math:`R_1`, in metres.
    :param exponent: :math:`n`, from :func:`geometric_exponent`.
    :param attenuation_per_m: :math:`\alpha`, from
        :func:`attenuation_coefficient_per_m`; 0 (default) for no material
        damping.
    :return: :math:`\bar v`, one per distance, in millimetres per second.
    :raises ValueError: For a negative amplitude, exponent or attenuation, a
        non-positive reference distance, or a distance in the near field.
    """
    amplitude = require_non_negative(reference_velocity_mm_s, "reference_velocity_mm_s")
    distances = require_finite_array(distance_m, "distance_m")
    reference = require_positive(reference_distance_m, "reference_distance_m")
    if np.any(distances < reference):
        msg = (
            f"Formula (2) holds in the far field only; a distance under R_1 = "
            f"{reference:g} m needs its own investigation (Clause 4.2)."
        )
        raise ValueError(msg)
    power = require_non_negative(exponent, "exponent")
    alpha = require_non_negative(attenuation_per_m, "attenuation_per_m")
    spread = (distances / reference) ** (-power)
    damped = np.exp(-alpha * (distances - reference))
    return np.asarray(amplitude * spread * damped, dtype=np.float64)


def material_damping_factor(
    distance_m: ArrayLike,
    *,
    damping_ratio: float,
    frequency_hz: float,
    wave_speed_m_s: float,
) -> NDArray[np.float64]:
    r"""The share the ground absorbs over a distance, Figure 2.

    :math:`\exp[-2\pi D f (R - R_1) / c]`, the damping factor of Formula (2)
    alone, which Figure 2 draws for a damping ratio of 0,01 and a wave speed
    of 200 m/s from 10 Hz to 50 Hz: at 100 m the ground has taken 27 % of
    the amplitude at 10 Hz and 79 % at 50 Hz.

    :param distance_m: :math:`R - R_1`, in metres, one or many, not negative.
    :param damping_ratio: :math:`D`, not negative.
    :param frequency_hz: :math:`f`, in hertz.
    :param wave_speed_m_s: :math:`c`, in metres per second.
    :return: The factor, one per distance, between 0 and 1.
    :raises ValueError: For a negative distance or damping ratio, or a
        non-positive frequency or wave speed.
    """
    distances = require_finite_array(distance_m, "distance_m")
    if np.any(distances < 0.0):
        msg = "'distance_m' must not be negative."
        raise ValueError(msg)
    wavelength = require_positive(wave_speed_m_s, "wave_speed_m_s") / require_positive(
        frequency_hz, "frequency_hz"
    )
    alpha = attenuation_coefficient_per_m(damping_ratio, wavelength_m=wavelength)
    return np.asarray(np.exp(-alpha * distances), dtype=np.float64)


def soil_building_natural_frequency_hz(
    stiffness_n_per_m: float, *, mass_kg: float
) -> float:
    r"""The natural frequency of a building on its ground, Formula (3).

    :math:`f_B = \frac{1}{2\pi}\sqrt{k_B / m_B}`: the ground as a spring under
    the mass of the building that moves in phase, for the vertical direction
    and predominantly harmonic vibration in the lower frequency range.

    :param stiffness_n_per_m: :math:`k_B`, the spring stiffness of the
        ground, in newtons per metre.
    :param mass_kg: :math:`m_B`, in kilograms.
    :return: :math:`f_B`, in hertz.
    :raises ValueError: For a non-positive stiffness or mass.
    """
    stiffness = require_positive(stiffness_n_per_m, "stiffness_n_per_m")
    mass = require_positive(mass_kg, "mass_kg")
    return math.sqrt(stiffness / mass) / (2.0 * math.pi)


def soil_building_frequency_guide_hz(storeys: int) -> tuple[float, float]:
    """The natural frequency Clause 4.3 gives a building on medium ground.

    About 15 Hz for one or two storeys, 8 Hz to 12 Hz for two to six, under
    8 Hz above six, for a ground with a shear wave speed of 150 m/s to
    200 m/s. The clause prints two storeys in both ranges, so a two-storey
    building gets the union, 8 Hz to 15 Hz.

    :param storeys: The number of storeys, at least one.
    :return: ``(low, high)`` in hertz; the low bound is 0 above six storeys
        and both are 15 for a single storey.
    :raises ValueError: For fewer than one storey or a count that is not
        whole.
    """
    count = require_count(storeys, "storeys")
    if count < _LOW_RISE_STOREYS:
        return _LOW_RISE_HZ
    if count == _LOW_RISE_STOREYS:
        return _TWO_STOREY_HZ
    if count <= _MID_RISE_STOREYS:
        return _MID_RISE_HZ
    return _HIGH_RISE_HZ


def foundation_transfer_max(
    system_damping_ratio: float = LOOSE_GROUND_SYSTEM_DAMPING,
) -> float:
    r"""The most a foundation passes at the building's resonance, Clause 4.3.

    :math:`V_F = 1 / (2 D_0)` with the system damping of the building on its
    ground, 0,25 for loose ground, which gives 2. Above the resonance a
    mean of :data:`FOUNDATION_TRANSFER_ABOVE_RESONANCE` may be assumed, and
    on rock there is no reduction.

    :param system_damping_ratio: :math:`D_0`, positive; 0,25 by default.
    :return: :math:`V_F`.
    :raises ValueError: For a non-positive damping ratio.
    """
    return 1.0 / (2.0 * require_positive(system_damping_ratio, "system_damping_ratio"))


def floor_transfer_max(floor_damping_ratio: float) -> float:
    r"""The most a floor amplifies at its resonance, Clause 4.3.

    :math:`V_D = 1 / (2 D_1)`, from the foundation through the walls to the
    floor, for a building excited in phase over its whole footprint by
    predominantly harmonic vibration: 25 for a concrete floor with a damping
    ratio of 0,02 and 10 for one with 0,05. Short spans, partitions and a
    foundation on loose ground raise the damping.

    :param floor_damping_ratio: :math:`D_1`, positive.
    :return: :math:`V_D`.
    :raises ValueError: For a non-positive damping ratio.
    """
    return 1.0 / (2.0 * require_positive(floor_damping_ratio, "floor_damping_ratio"))


def storey_frequency_hz(storeys: int) -> float:
    r"""The lowest horizontal natural frequency of a building, Formula (4).

    :math:`f_1 \approx 10 / n` Hz for a building of :math:`n` storeys, meant
    for five and more, where a tall slender building meets a low excitation
    frequency.

    :param storeys: :math:`n`, at least five.
    :return: :math:`f_1`, in hertz.
    :raises ValueError: For fewer than five storeys.
    """
    count = require_count(storeys, "storeys")
    if count < STOREY_FORMULA_MIN_STOREYS:
        msg = f"the storey formula is for {STOREY_FORMULA_MIN_STOREYS} storeys and more, got {count}."
        raise ValueError(msg)
    return 10.0 / count


def blast_peak_velocity_mm_s(
    charge_kg: float,
    distance_m: ArrayLike,
    *,
    coefficient_mm_s: float,
    charge_exponent: float,
    distance_exponent: float,
) -> NDArray[np.float64]:
    r"""The peak velocity of a blast in the far field, Formula (5).

    :math:`v_{\max} = k (L/L_0)^b (R/R_0)^{-m}` with the charge per delay
    :math:`L` against 1 kg, the distance :math:`R` against 1 m, and the
    constants :math:`k`, :math:`b` and :math:`m` from trial blasts or
    comparable cases in ground, method and distance, with allowance for
    scatter. The standard prints no values for them. Its symbol list prints
    the distance in millimetres, which the reference metre says is a slip.

    :param charge_kg: :math:`L`, in kilograms per delay.
    :param distance_m: :math:`R`, in metres, one or many.
    :param coefficient_mm_s: :math:`k`, in millimetres per second.
    :param charge_exponent: :math:`b`.
    :param distance_exponent: :math:`m`.
    :return: :math:`v_{\max}`, one per distance, in millimetres per second.
    :raises ValueError: For a non-positive charge, distance or coefficient,
        or a negative exponent.
    """
    charge = require_positive(charge_kg, "charge_kg")
    distances = _distances(distance_m)
    factor = require_positive(coefficient_mm_s, "coefficient_mm_s")
    charge_power = require_non_negative(charge_exponent, "charge_exponent")
    distance_power = require_non_negative(distance_exponent, "distance_exponent")
    return np.asarray(
        factor
        * (charge / _REFERENCE_CHARGE_KG) ** charge_power
        * (distances / _REFERENCE_DISTANCE_M) ** (-distance_power),
        dtype=np.float64,
    )


def _distances(distance_m: ArrayLike) -> NDArray[np.float64]:
    distances = require_finite_array(distance_m, "distance_m")
    if np.any(distances <= 0.0):
        msg = "'distance_m' must be positive."
        raise ValueError(msg)
    return distances


def fall_energy_kj(weight_kn: float, *, drop_height_m: float) -> float:
    r"""The energy of a falling mass, :math:`E = G h` of Clause 5.1.3.

    A weight in kilonewtons through a height in metres is that many
    kilojoules, the unit Formula (6) wants.

    :param weight_kn: :math:`G`, in kilonewtons.
    :param drop_height_m: :math:`h`, in metres.
    :return: :math:`E`, in kilojoules.
    :raises ValueError: For a non-positive weight or height.
    """
    weight = require_positive(weight_kn, "weight_kn")
    height = require_positive(drop_height_m, "drop_height_m")
    return _KJ_PER_KN_M * weight * height


def impact_peak_velocity_mm_s(
    fall_energy_kj: float,
    distance_m: ArrayLike,
    *,
    coefficient_mm_s: float,
    distance_exponent: float,
) -> NDArray[np.float64]:
    r"""The peak velocity of a falling mass, Formula (6).

    :math:`v_{\max} = k (E/E_0)^{0{,}5} (R/R_0)^{-m}` with the fall energy
    :math:`E` against 1 kJ, the distance against 1 m, and :math:`k` and
    :math:`m` from comparable cases. The blast that fells a chimney is
    usually the smaller source; the impact is this one.

    :param fall_energy_kj: :math:`E`, in kilojoules, from
        :func:`fall_energy_kj`.
    :param distance_m: :math:`R`, in metres, one or many.
    :param coefficient_mm_s: :math:`k`, in millimetres per second.
    :param distance_exponent: :math:`m`.
    :return: :math:`v_{\max}`, one per distance, in millimetres per second.
    :raises ValueError: For a non-positive energy, distance or coefficient,
        or a negative exponent.
    """
    energy = require_positive(fall_energy_kj, "fall_energy_kj")
    distances = _distances(distance_m)
    factor = require_positive(coefficient_mm_s, "coefficient_mm_s")
    distance_power = require_non_negative(distance_exponent, "distance_exponent")
    return np.asarray(
        factor
        * math.sqrt(energy / _REFERENCE_ENERGY_KJ)
        * (distances / _REFERENCE_DISTANCE_M) ** (-distance_power),
        dtype=np.float64,
    )


def track_excitation_frequency_hz(
    train_speed_m_s: float, *, spacing_m: float, harmonics: int = 1
) -> NDArray[np.float64]:
    r"""The frequencies a repeating feature of the track excites, Clause 5.3.2.

    :math:`f_A = v_Z / d` and its multiples, for the spacing :math:`d` of
    whatever repeats along the track or the wheel: the sleepers, the axles,
    the bogies, a flat spot once per turn of the wheel. The natural
    frequencies of the vehicle itself do not move with the speed.

    :param train_speed_m_s: :math:`v_Z`, in metres per second.
    :param spacing_m: :math:`d`, in metres.
    :param harmonics: How many multiples to return, the fundamental first.
    :return: :math:`f_A` and its multiples, in hertz.
    :raises ValueError: For a non-positive speed or spacing, or fewer than
        one harmonic.
    """
    speed = require_positive(train_speed_m_s, "train_speed_m_s")
    spacing = require_positive(spacing_m, "spacing_m")
    count = require_count(harmonics, "harmonics")
    return np.asarray(speed / spacing * np.arange(1, count + 1), dtype=np.float64)


def machine_count_correction(
    machine_count: ArrayLike, *, reference_count: int
) -> NDArray[np.float64]:
    r"""The correction :math:`\chi` of Formula (7), Figure 3.

    The figure draws :math:`\chi` against the number of machines running,
    from 4 to 100, for measurements made with 3, 5, 10, 30, 60 or 100 of
    them, and prints no closed form; the curve is read off the page at a
    five-hundredth and interpolated linearly between the readings.

    :param machine_count: :math:`N`, from 4 to 100, one or many.
    :param reference_count: :math:`N_B`, one of the six curves.
    :return: :math:`\chi`, one per count.
    :raises ValueError: For a count outside the figure or a reference the
        figure has no curve for.
    """
    counts = require_finite_array(machine_count, "machine_count")
    grid = np.asarray(MACHINE_COUNT_AXIS, dtype=np.float64)
    if reference_count not in MACHINE_COUNT_CORRECTION:
        msg = (
            f"Figure 3 draws chi for N_B in {sorted(MACHINE_COUNT_CORRECTION)}, "
            f"got {reference_count!r}."
        )
        raise ValueError(msg)
    if np.any(counts < grid[0]) or np.any(counts > grid[-1]):
        msg = f"Figure 3 runs from {grid[0]:g} to {grid[-1]:g} machines."
        raise ValueError(msg)
    curve = MACHINE_COUNT_CORRECTION[reference_count]
    return np.asarray(np.interp(counts, grid, curve), dtype=np.float64)


def machine_hall_velocity_mm_s(
    reference_velocity_mm_s: float, machine_count: ArrayLike, *, reference_count: int
) -> NDArray[np.float64]:
    r"""The peak velocity outside a hall of similar machines, Formula (7).

    :math:`v_N = \chi \, v_B \sqrt{N}`: the velocity measured at the point
    with :math:`N_B` machines running, scaled to :math:`N` of them with the
    correction of Figure 3. Figure A.18 draws it for 0,44 mm/s measured with
    three machines and finds the measurements on the curve up to about
    sixty, the nearest group; beyond that the added groups are further off.

    :param reference_velocity_mm_s: :math:`v_B`, in millimetres per second.
    :param machine_count: :math:`N`, from 4 to 100, one or many.
    :param reference_count: :math:`N_B`, one of 3, 5, 10, 30, 60 or 100.
    :return: :math:`v_N`, one per count, in millimetres per second.
    :raises ValueError: For a negative velocity, or a count or reference
        outside Figure 3.
    """
    velocity = require_non_negative(reference_velocity_mm_s, "reference_velocity_mm_s")
    counts = require_finite_array(machine_count, "machine_count")
    chi = machine_count_correction(counts, reference_count=reference_count)
    return np.asarray(chi * velocity * np.sqrt(counts), dtype=np.float64)
