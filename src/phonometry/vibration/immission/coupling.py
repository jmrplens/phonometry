#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Mounting the transducer, and what the meter may be wrong by (DIN 45669-2:2005-06).

DIN 45669-2 is the procedure the DIN 45669-1 meter is used with: where the
transducers go, how they are coupled to the floor or the ground, how long a
measurement runs and what keeps a disturbance out of it. Nearly all of that
is judgement written down, and the little that is a number is here, because a
number a measurement is planned by belongs where the plan is checked.

**Loose mounting** (5.3.2 and 5.3.3). A transducer set down without fastening
walks or lifts off when the vibration is strong, and a coupling that is not
force-locked resonates against the surface. The clause fixes both limits: a
loose transducer measures without falsification up to 100 Hz vertically and
40 Hz horizontally, provided the peak acceleration in every direction stays at
or below 3 m/s². On a hard surface it may stand on its own or on the device
with rounded feet of Figure 1 b); on a soft covering it has to stand on the
device with hardened steel spikes of Figure 1 a), about 2,5 kg together with
the transducer, pressed and tapped through the covering. Above those limits
the transducer is glued, screwed or plastered on, and on a sensitive hard
surface such as tiles or parquet adhesive wax carries the horizontal
component to 80 Hz.

**Mass loading** (7.2.4). The mass coupled to the object, transducer and
device together, should be at most a hundredth of the mass the object
vibrates with; a heavier transducer is a disturbance of kind :math:`s_3`.

**The instrument's share of the error** (8.1, Table 3). A meter that meets
every single requirement of DIN 45669-1 may still be wrong on one displayed
quantity, and Table 3 says by how much at a high confidence level: 15 % on an
r.m.s.-based value and 20 % on a peak for class 1, 25 % and 35 % for class 2.
The classes are the accuracy classes of the 1995 edition of Part 1; the 2010
edition dropped the distinction, so a meter of today is graded by the one set
of tolerances and the table's class 1 column is the one that applies to it.

**What is not here.** Measurement positions, directions, durations and the
list of disturbances are text, and so is the coupling to the ground, where
5.3.4.1 warns that the coupling alone can move the reading by up to 15 dB.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..._internal.validation import require_choice, require_positive

__all__ = [
    "CLEARANCE_TO_DISTURBING_BODY_FACTOR",
    "EMISSION_POINT_TRACK_DISTANCE_M",
    "GROUND_COUPLING_DEVIATION_DB",
    "INSTRUMENT_CONFIDENCE_LIMITS_PERCENT",
    "LOOSE_MOUNTING_LIMITS_HZ",
    "LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2",
    "MASS_LOADING_RATIO_LIMIT",
    "SPIKED_DEVICE_MASS_KG",
    "WAX_MOUNTING_HORIZONTAL_LIMIT_HZ",
    "MountingCheck",
    "check_loose_mounting",
    "instrument_confidence_limit_percent",
    "mass_loading_ratio",
]

#: The frequency up to which a transducer set down without fastening measures
#: without falsification, in hertz, by measuring direction (5.3.2.1, 5.3.2.2,
#: 5.3.3.1, 5.3.3.2): 100 Hz vertically, 40 Hz horizontally, on a hard surface
#: and on a soft covering alike.
LOOSE_MOUNTING_LIMITS_HZ: dict[str, float] = {"vertical": 100.0, "horizontal": 40.0}

#: The peak acceleration, in metres per second squared, up to which a loose
#: transducer neither lifts off nor walks (5.3.2.1): 3 m/s² in every direction.
LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2: float = 3.0

#: The frequency, in hertz, up to which adhesive wax carries the horizontal
#: component on a sensitive hard surface such as tiles, parquet or a lacquered
#: screed (Table 1).
WAX_MOUNTING_HORIZONTAL_LIMIT_HZ: float = 80.0

#: The mass of the spiked coupling device of Figure 1 a) together with the
#: transducer it carries, in kilograms, about (5.3.3.1).
SPIKED_DEVICE_MASS_KG: float = 2.5

#: The most of the object's vibrating mass that the transducer and its device
#: may add to it (7.2.4): a hundredth.
MASS_LOADING_RATIO_LIMIT: float = 0.01

#: Table 3: the confidence limits of the meter's own error on one displayed
#: quantity, in per cent, as ``(class 1, class 2)``, for a value based on an
#: r.m.s. and for a peak. The 2010 edition of DIN 45669-1 no longer
#: distinguishes the two classes.
INSTRUMENT_CONFIDENCE_LIMITS_PERCENT: dict[str, tuple[float, float]] = {
    "rms": (15.0, 25.0),
    "peak": (20.0, 35.0),
}

#: How far the coupling of a transducer to the ground alone may move the
#: reading, in decibels (5.3.4.1), which the clause glosses as a factor of 5 in
#: amplitude.
GROUND_COUPLING_DEVIATION_DB: float = 15.0

#: The distance from the nearest track 5.1.4 gives as an example for the
#: reference point of a railway emission measurement, in metres.
EMISSION_POINT_TRACK_DISTANCE_M: float = 8.0

#: How far a ground measurement point keeps from a body that disturbs the wave
#: field, as a multiple of the body's largest dimension (5.1.4): at least 1,5.
CLEARANCE_TO_DISTURBING_BODY_FACTOR: float = 1.5

_DIRECTIONS = tuple(LOOSE_MOUNTING_LIMITS_HZ)
_SURFACES = ("hard", "soft")
_QUANTITIES = tuple(INSTRUMENT_CONFIDENCE_LIMITS_PERCENT)
_CLASSES = (1, 2)

#: What a loose transducer stands on, by surface (5.3.2.1, 5.3.3.1).
_DEVICES = {
    "hard": "the transducer alone, or the device with rounded feet of Figure 1 b)",
    "soft": (
        "the device with hardened steel spikes of Figure 1 a), about 2,5 kg with "
        "the transducer, pressed and tapped through the covering"
    ),
}


@dataclass(frozen=True)
class MountingCheck:
    """Whether a transducer may be set down without fastening (5.3.2, 5.3.3).

    :ivar acceptable: ``True`` when both the peak acceleration and the highest
        frequency of interest are within what a loose mounting carries.
    :ivar frequency_limit_hz: The frequency the direction allows a loose
        mounting up to, in hertz.
    :ivar peak_acceleration_limit_m_s2: The 3 m/s² of 5.3.2.1.
    :ivar direction: ``"vertical"`` or ``"horizontal"``.
    :ivar surface: ``"hard"`` or ``"soft"``.
    :ivar device: What the transducer has to stand on for the verdict to hold.
    """

    acceptable: bool
    frequency_limit_hz: float
    peak_acceleration_limit_m_s2: float
    direction: str
    surface: str
    device: str


def check_loose_mounting(
    peak_acceleration_m_s2: float,
    upper_frequency_hz: float,
    *,
    direction: str,
    surface: str = "hard",
) -> MountingCheck:
    """May the transducer be set down without fastening? (5.3.2 and 5.3.3)

    Loose mounting carries a vertical measurement to 100 Hz and a horizontal
    one to 40 Hz, provided the peak acceleration in every direction stays at
    or below 3 m/s². Above either limit the transducer is glued, screwed or
    plastered on. The limits are the same on a hard surface and on a soft
    covering; what differs is what the transducer stands on, which the result
    names.

    :param peak_acceleration_m_s2: The largest peak acceleration expected in
        any direction, in metres per second squared.
    :param upper_frequency_hz: The highest frequency the measurement has to
        carry, in hertz.
    :param direction: ``"vertical"`` or ``"horizontal"``.
    :param surface: ``"hard"`` (default: masonry, a raw slab, a hard floor) or
        ``"soft"`` (a carpet or any elastic floor covering).
    :return: The verdict and the limits it was read against, as a
        :class:`MountingCheck`.
    :raises ValueError: For a non-positive acceleration or frequency, or an
        unknown direction or surface.
    """
    peak = require_positive(peak_acceleration_m_s2, "peak_acceleration_m_s2")
    upper = require_positive(upper_frequency_hz, "upper_frequency_hz")
    which = require_choice(str(direction), "direction", _DIRECTIONS)
    where = require_choice(str(surface), "surface", _SURFACES)
    limit = LOOSE_MOUNTING_LIMITS_HZ[which]
    return MountingCheck(
        acceptable=peak <= LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2 and upper <= limit,
        frequency_limit_hz=limit,
        peak_acceleration_limit_m_s2=LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2,
        direction=which,
        surface=where,
        device=_DEVICES[where],
    )


def instrument_confidence_limit_percent(
    quantity: str, accuracy_class: int = 1
) -> float:
    """The confidence limit of the meter's own error on one quantity (Table 3).

    :param quantity: ``"rms"`` for a value based on an r.m.s., such as
        ``KB_F`` or ``KB_FTm``, or ``"peak"`` for a peak value.
    :param accuracy_class: 1 (default) or 2, the classes of the 1995 edition
        of DIN 45669-1. The 2010 edition grades every meter by one set of
        tolerances, so class 1 is the column that applies to a meter of today.
    :return: The limit, in per cent of the displayed value.
    :raises ValueError: For an unknown quantity or class.
    """
    which = require_choice(str(quantity), "quantity", _QUANTITIES)
    if accuracy_class not in _CLASSES:
        msg = f"'accuracy_class' must be 1 or 2; got {accuracy_class!r}."
        raise ValueError(msg)
    return INSTRUMENT_CONFIDENCE_LIMITS_PERCENT[which][_CLASSES.index(accuracy_class)]


def mass_loading_ratio(coupled_mass_kg: float, *, vibrating_mass_kg: float) -> float:
    """The mass the transducer adds to the object, as a fraction (7.2.4).

    The transducer and its coupling device together should add at most
    :data:`MASS_LOADING_RATIO_LIMIT` of the mass the object vibrates with,
    which for a floor is the mass of the slab that moves at the highest
    frequency of the signal, not the mass of the building. Where that cannot
    be estimated, 7.2.4 says to add a second, uncoupled mass of the same order
    beside the transducer and see whether the reading moves.

    :param coupled_mass_kg: The transducer and its device, in kilograms.
    :param vibrating_mass_kg: The mass of the object that vibrates with it, in
        kilograms.
    :return: The ratio of the two, dimensionless; compare it with
        :data:`MASS_LOADING_RATIO_LIMIT`.
    :raises ValueError: For a non-positive mass.
    """
    coupled = require_positive(coupled_mass_kg, "coupled_mass_kg")
    vibrating = require_positive(vibrating_mass_kg, "vibrating_mass_kg")
    return coupled / vibrating
