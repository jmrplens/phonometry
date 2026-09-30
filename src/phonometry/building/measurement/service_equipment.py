#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound from service equipment and activities in buildings, engineering method.

This is the **engineering method** of ISO 16032 for the sound pressure level a
building's own equipment makes in a room: taps, showers, baths and water
closets, ventilation, heating and cooling, lifts, rubbish chutes, boilers and
pumps, car-park doors and, new in the revision, *activities*, the sources whose
operation nobody on site controls (a restaurant's coolers, amplified music next
door, a sports hall). It is the method a dispute over a noisy installation ends
in; the survey method for the same quantities is ISO 10052
(:func:`~phonometry.building.survey_service_equipment_level`).

**Which text.** The implementation follows the draft of the second edition,
ISO/DIS 16032:2023, in its German publication E DIN EN ISO 16032:2023-05
(prEN ISO 16032:2023, German and English text). The draft is the only text of
the revision the library holds, so everything implemented here follows it,
and it is cited as a draft; clause numbers are those of the draft. What changed from the withdrawn
ISO 16032:2004 is said where it matters below and in the guide.

**Where it applies (Clause 1).** The method is meant for rooms of about
300 m³ or less, in dwellings, hotels, schools, offices and hospitals. It is not
meant for large auditoriums and concert halls, nor for a source so far from the
building that the weather changes the propagation, although the operating
conditions of Annex B can still be used there. Nothing in the library checks
the volume.

**The procedure.** The linear band spectrum is recorded together with the A-
or C-weighted level (a *multispectral* recording, Clause 6), in one of three
quantities of Table 1: the maximum level with time weighting S or F, taken at
the moment the weighted level peaks, or the equivalent continuous level over
a stated integration time. It is measured at three microphone positions, one
in the loudest corner of the room (7.2) and two in the reverberant field
(7.3). When the three A-weighted readings differ by more than 3,0 dB the
corner is measured again together with two new room positions, and a third
time with two more if the spread of the six still reaches 6,0 dB (7.4.1,
:func:`check_position_spread`). Every reading enters the band average of
Formula (1), rounded to one decimal (7.5):

.. math::

    L = 10 \lg \left[ \frac{1}{n} \sum_{i=1}^{n} 10^{0,1 L_i} \right]
    \ \mathrm{dB}

A sound source in the room itself, a ventilation outlet for example, gets one
additional position of its own (7.9,
:func:`additional_microphone_position`), whose reading is reported separately,
never standardized and never averaged with the others.

**Background (Clause 9).** With the background band level :math:`L_2` and the
measured one :math:`L_1`, the difference :math:`\Delta L = L_1 - L_2` decides:
at 10 dB or more nothing is corrected; from 4 dB to 10 dB the band is corrected
with Formulae (7) to (9),

.. math::

    L = L_1 - K, \qquad
    K = -10 \lg \left[ 1 - 10^{-0,1 \Delta L} \right] \ \mathrm{dB}

and below 4 dB the correction is held at the 2,2 dB that a 4 dB difference
gives, the band is reported as influenced by the background and the result is
an upper limit of the equipment level
(:func:`service_equipment_background_correction`).

**Standardization and normalization (4.8, 7.7).** If a regulation asks for it,
the corrected bands are referred to a reference reverberation time
:math:`T_0` (0,5 s unless another value is specified) or to a reference
absorption area :math:`A_0 = 10` m², Formulae (5) and (6):

.. math::

    L_\mathrm{nT} = L - 10 \lg \frac{T}{T_0}\ \mathrm{dB}, \qquad
    L_\mathrm{n} = L - 10 \lg \frac{A_0\,T}{0,16\,V}\ \mathrm{dB}

Only the one-third-octave bands 50 Hz to 5 000 Hz (octave bands 63 Hz to
4 000 Hz) are standardized or normalized, because the reverberation time of the
bands outside cannot be measured reliably; those bands still enter the
weighted sums, unstandardized, and the report has to say so.

**Weighted values (4.3, 4.4, 7.8).** The A- and C-weighted single numbers are
energy sums of the corrected bands plus the Annex A corrections, rounded to
whole decibels. The A-weighted value uses either the restricted range 50 Hz to
5 000 Hz or the extended range 25 Hz to 10 000 Hz; the C-weighted value uses
the extended range. The single numbers are named as Table 1 names them, for
example :math:`L_\mathrm{A,Smax,nT}` or :math:`L_\mathrm{C,eq}`. 4.2 also
admits "a specific frequency range" for the bands, and the form of Annex C has
a box for it, but 7.8 forms the weighted values over the two ranges above
only, and so does the library: a band set that does not cover the chosen
range is refused.

**Precision (Clause 10).** Table 2 gives the reproducibility standard deviation
of a room-average band level, 1,9 dB at the lowest bands down to 1,0 dB from
800 Hz up, and 0,8 dB and 1,2 dB for the A- and C-weighted values of a steady,
flat sound at least 10 dB above the background. A result carries them as
:attr:`ServiceEquipmentResult.reproducibility_db` and
:attr:`ServiceEquipmentResult.weighted_reproducibility_db`; the draft states no
coverage factor, so no expanded uncertainty is formed.

**Operating conditions (Annex B).** How each kind of equipment is to be run
while it is measured, and for how long the equivalent level is integrated, is
the data of :data:`SERVICE_EQUIPMENT_OPERATING_CONDITIONS`, including the
activity sources of B.10.

**Printed defects.** Table A.1 prints a C-weighting of 0 dB for every
one-third-octave band from 1 600 Hz to 10 000 Hz and of -5 dB at 25 Hz. Its
own octave column gives -0,2 dB at 2 000 Hz, -0,8 dB at 4 000 Hz and -3,0 dB
at 8 000 Hz, and IEC 61672-1, which Clause 4 cites for the weightings, gives
-0,1 dB to -4,4 dB from 1 600 Hz up and -4,4 dB at 25 Hz. The library uses the
IEC 61672-1 values in those cells. The cells, and the other defects of the
draft this module meets (a background correction sent to the reverberation
clause, the corner procedure sent to Clause 6, and a position ladder with no
rule at exactly 6,0 dB and 9,0 dB nor for three readings 6,0 dB or more
apart), are registered in ``docs/ERRATA.md``.

**No numeric oracle.** The draft prints no worked example. The conformance of
this module rests on closed forms and on the numbers the draft prints: the
2,2 dB of a 4 dB background difference, Table A.1 and Table 2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal

import numpy as np

from ..._internal.levels_math import energy_mean
from ..._internal.validation import (
    _as_float64,
    require_choice,
    require_count,
    require_positive,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "SERVICE_EQUIPMENT_OPERATING_CONDITIONS",
    "SERVICE_EQUIPMENT_REPRODUCIBILITY",
    "SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY",
    "SERVICE_EQUIPMENT_WEIGHTING",
    "OperatingCondition",
    "PositionSpreadCheck",
    "ServiceEquipmentBackgroundResult",
    "ServiceEquipmentPositionCheck",
    "ServiceEquipmentResult",
    "additional_microphone_position",
    "check_position_spread",
    "check_service_equipment_positions",
    "loudest_corner",
    "service_equipment_background_correction",
    "service_equipment_level",
]

# ---------------------------------------------------------------------------
# Printed tables
# ---------------------------------------------------------------------------

#: One-third-octave band centres of the extended range of 4.2, 25 Hz to
#: 10 000 Hz, in Hz.
_THIRD_OCTAVE_BANDS: Final = (
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
)

#: Octave band centres of 4.2, 31,5 Hz to 8 000 Hz, in Hz.
_OCTAVE_BANDS: Final = (31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)

#: The A-weighting column of Table A.1 in the one-third-octave bands, in dB,
#: 25 Hz to 10 000 Hz. Every cell agrees with IEC 61672-1:2013 Table 3.
_A_THIRD: Final = (
    -44.7,
    -39.4,
    -34.6,
    -30.2,
    -26.2,
    -22.5,
    -19.1,
    -16.1,
    -13.4,
    -10.9,
    -8.6,
    -6.6,
    -4.8,
    -3.2,
    -1.9,
    -0.8,
    0.0,
    0.6,
    1.0,
    1.2,
    1.3,
    1.2,
    1.0,
    0.5,
    -0.1,
    -1.1,
    -2.5,
)

#: The C-weighting of the one-third-octave bands, in dB, 25 Hz to 10 000 Hz.
#: The cells from 31,5 Hz to 1 250 Hz are Table A.1 as printed. The 25 Hz cell
#: and the nine from 1 600 Hz to 10 000 Hz are IEC 61672-1:2013 Table 3: the
#: draft prints -5 dB at 25 Hz and 0 dB from 1 600 Hz up, which its own octave
#: column contradicts at 2 000, 4 000 and 8 000 Hz (``docs/ERRATA.md``).
_C_THIRD: Final = (
    -4.4,
    -3.0,
    -2.0,
    -1.3,
    -0.8,
    -0.5,
    -0.3,
    -0.2,
    -0.1,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    -0.1,
    -0.2,
    -0.3,
    -0.5,
    -0.8,
    -1.3,
    -2.0,
    -3.0,
    -4.4,
)

#: The octave columns of Table A.1, in dB, 31,5 Hz to 8 000 Hz (the table
#: labels the first band "31"). Both columns are as printed.
_A_OCTAVE: Final = (-39.4, -26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1)
_C_OCTAVE: Final = (-3.0, -0.8, -0.2, 0.0, 0.0, 0.0, -0.2, -0.8, -3.0)

#: A- and C-weighting corrections of **ISO/DIS 16032:2023 Annex A, Table A.1**
#: (E DIN EN ISO 16032:2023-05, printed p. 12 of the English text), in dB.
#: Keyed by band width (``"third"``, 25 Hz to 10 000 Hz, or ``"octave"``,
#: 31,5 Hz to 8 000 Hz), then by weighting (``"A"`` or ``"C"``), then by the
#: nominal band centre in Hz. The one-third-octave C-weighting at 25 Hz and from
#: 1 600 Hz to 10 000 Hz is the IEC 61672-1:2013 value where the draft prints a
#: defect; every other cell is the print.
SERVICE_EQUIPMENT_WEIGHTING: Mapping[str, Mapping[str, Mapping[float, float]]] = (
    MappingProxyType(
        {
            "third": MappingProxyType(
                {
                    "A": MappingProxyType(
                        dict(zip(_THIRD_OCTAVE_BANDS, _A_THIRD, strict=True))
                    ),
                    "C": MappingProxyType(
                        dict(zip(_THIRD_OCTAVE_BANDS, _C_THIRD, strict=True))
                    ),
                }
            ),
            "octave": MappingProxyType(
                {
                    "A": MappingProxyType(
                        dict(zip(_OCTAVE_BANDS, _A_OCTAVE, strict=True))
                    ),
                    "C": MappingProxyType(
                        dict(zip(_OCTAVE_BANDS, _C_OCTAVE, strict=True))
                    ),
                }
            ),
        }
    )
)


#: The lowest band of the last one-third-octave row of Table 2, which prints
#: "800 to 10 000", in Hz.
_TABLE2_LAST_ROW_FROM_HZ = 800.0

#: The one-third-octave rows of Table 2 as printed: each group of band
#: centres, in Hz, with its reproducibility standard deviation, in dB.
_TABLE2_THIRD_ROWS: Final = (
    ((25.0, 31.5, 40.0), 1.9),
    ((50.0, 63.0, 80.0), 1.9),
    ((100.0, 125.0, 160.0), 1.9),
    ((200.0, 250.0, 315.0), 1.5),
    ((400.0, 500.0, 630.0), 1.2),
    (tuple(f for f in _THIRD_OCTAVE_BANDS if f >= _TABLE2_LAST_ROW_FROM_HZ), 1.0),
)


#: Reproducibility standard deviation of a room-average band level,
#: **ISO/DIS 16032:2023 Clause 10, Table 2** (printed p. 10), in dB. Keyed by
#: band width, then by the nominal band centre in Hz: 1,9 dB from 25 Hz to
#: 160 Hz (octaves 31,5 Hz to 125 Hz), 1,5 dB from 200 Hz to 315 Hz (250 Hz),
#: 1,2 dB from 400 Hz to 630 Hz (500 Hz) and 1,0 dB from 800 Hz to 10 000 Hz
#: (1 000 Hz to 8 000 Hz). The values are estimated from a limited number of
#: measurements of sources constant in time; a fluctuating source increases the
#: uncertainty, maximum levels most of all.
SERVICE_EQUIPMENT_REPRODUCIBILITY: Mapping[str, Mapping[float, float]] = (
    MappingProxyType(
        {
            "third": MappingProxyType(
                {f: sigma for centres, sigma in _TABLE2_THIRD_ROWS for f in centres}
            ),
            "octave": MappingProxyType(
                {31.5: 1.9, 63.0: 1.9, 125.0: 1.9, 250.0: 1.5, 500.0: 1.2}
                | dict.fromkeys((1000.0, 2000.0, 4000.0, 8000.0), 1.0)
            ),
        }
    )
)

#: Reproducibility standard deviation of the A- and C-weighted single numbers,
#: **ISO/DIS 16032:2023 Table 2** (printed p. 10), in dB: 0,8 dB and 1,2 dB.
#: Footnote a limits both to a constant sound with a relatively flat spectrum
#: from 25 Hz to 10 000 Hz, at least 10 dB above the background.
SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY: Mapping[str, float] = MappingProxyType(
    {"A": 0.8, "C": 1.2}
)


@dataclass(frozen=True)
class OperatingCondition:
    """How one kind of equipment is run while it is measured (Annex B).

    Annex B is normative, but B.1.1 lets national requirements and regulations
    override it, and equipment it does not list is measured by the principles
    of the document with the chosen conditions reported in detail.

    :ivar clause: The clause of Annex B, e.g. ``"B.2.6"``.
    :ivar equipment: What the entry covers, in words.
    :ivar maximum_level: Whether the entry defines a cycle for the maximum
        level ``Lmax``.
    :ivar equivalent_level: Whether the entry defines the equivalent level
        ``Leq``; a rubbish chute is measured as a maximum level only.
    :ivar conditions: The operating conditions, in words.
    :ivar maximum_cycle: The operating cycle for ``Lmax``, or ``None``.
    :ivar equivalent_cycle: What the ``Leq`` integration time covers, or
        ``None``.
    :ivar nominal_integration_time_s: The integration time the entry gives in
        seconds when it is a fixed duration (about 30 s), or ``None`` when it
        is the length of a cycle.
    :ivar parameters: The other numbers the entry prints, keyed by a name that
        carries the unit (``"tube_length_m"``) or says it is a count.
    """

    clause: str
    equipment: str
    maximum_level: bool
    equivalent_level: bool
    conditions: str
    maximum_cycle: str | None
    equivalent_cycle: str | None
    nominal_integration_time_s: float | None
    parameters: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """Freeze the parameters, which a caller may hand over as a ``dict``."""
        if not isinstance(self.parameters, MappingProxyType):
            object.__setattr__(
                self, "parameters", MappingProxyType(dict(self.parameters))
            )


#: The integration time Annex B gives for steady operation, in seconds: "about
#: 30 s" (B.1.2, B.2.2, B.3, B.4), and the shortest averaging time where no
#: operating cycle can be defined (B.1.3).
_ABOUT_30_S = 30.0
#: The same steady-operation cycle in words: the ``Leq`` cycle of ventilation,
#: heating and cooling (B.3, B.4) and the ``Lmax`` cycle of cooling (B.4).
_ABOUT_30_S_CYCLE = "about 30 s"

#: The mixers of B.2.2 that are run through the temperature range: one
#: dual-function control, independent flow and temperature controls, or a
#: thermostatic valve. A mixer with independent hot and cold taps is not.
_TEMPERATURE_MIXERS = (
    "a single-lever mixer (one control for flow and temperature), a mixer "
    "with independent flow and temperature controls or a thermostatic valve"
)

#: The operating conditions and cycles of **ISO/DIS 16032:2023 Annex B**
#: (printed pp. 13 to 19), keyed by equipment: ``"water_tap"``,
#: ``"shower_cabin"``, ``"bath"``, ``"filling_emptying"``, ``"water_closet"``,
#: ``"mechanical_ventilation"``, ``"heating"``, ``"cooling"``, ``"lift"``,
#: ``"rubbish_chute"``, ``"auxiliary_equipment"``, ``"car_park_door"``,
#: ``"other_equipment"`` and ``"unknown_source"``, the activities and
#: unmonitored sources of B.10 that the revision adds. Each value is an
#: :class:`OperatingCondition`; the text is a summary of the clause, not a
#: quotation.
SERVICE_EQUIPMENT_OPERATING_CONDITIONS: Mapping[str, OperatingCondition] = (
    MappingProxyType(
        {
            "water_tap": OperatingCondition(
                clause="B.2.2",
                equipment="water tap or valve",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "stop cocks fully open (or their position reported); a movable "
                    "outlet placed as close to the middle of the sink as it goes; "
                    "measured in the surrounding rooms, not the room of the installation"
                ),
                maximum_cycle=(
                    "a tap with one inlet: open fully, wait a few seconds, close; a "
                    "mixer with independent hot and cold taps: open the hot tap "
                    "fully, open the cold tap, wait a few seconds, close the hot tap, "
                    f"then the cold one; {_TEMPERATURE_MIXERS}: open fully at the "
                    "average temperature, lower the temperature to the minimum, raise "
                    "it to the maximum and close"
                ),
                equivalent_cycle=(
                    "the tap (both taps of a hot and cold mixer) fixed in the "
                    f"position of the highest level; for {_TEMPERATURE_MIXERS} that "
                    "position is found at the average temperature and the hot- and "
                    "cold-water settings are checked too, the highest of the three "
                    "levels being the result"
                ),
                nominal_integration_time_s=_ABOUT_30_S,
                parameters={"temperature_mixer_settings": 3.0},
            ),
            "shower_cabin": OperatingCondition(
                clause="B.2.3",
                equipment="shower cabin",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "shower in the wall fixture at its highest position, directed at "
                    "the floor of the cabin; the water drained off soundlessly when the "
                    "valves are to be measured alone"
                ),
                maximum_cycle="as for a water tap (B.2.2)",
                equivalent_cycle="as for a water tap (B.2.2)",
                nominal_integration_time_s=_ABOUT_30_S,
            ),
            "bath": OperatingCondition(
                clause="B.2.4",
                equipment="bath (tub)",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "filling nozzle and shower treated as separate functions; without a "
                    "wall fixture the shower is held about 1,5 m above the bottom of the "
                    "tub; the bath empties while it is measured"
                ),
                maximum_cycle="as for a water tap (B.2.2) and, with a shower, B.2.3",
                equivalent_cycle="as for a water tap (B.2.2) and, with a shower, B.2.3",
                nominal_integration_time_s=_ABOUT_30_S,
                parameters={"shower_height_m": 1.5},
            ),
            "filling_emptying": OperatingCondition(
                clause="B.2.5",
                equipment="filling and emptying a sink or bath",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "plug closed and the vessel filled to half its maximum level with "
                    "hot and cold water mixed equally, taps fully open; then the plug "
                    "is opened and the emptying measured on its own"
                ),
                maximum_cycle="the filling period, then the emptying period",
                equivalent_cycle="the filling period and the emptying period",
                nominal_integration_time_s=None,
                parameters={"fill_fraction": 0.5},
            ),
            "water_closet": OperatingCondition(
                clause="B.2.6",
                equipment="water closet",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "flushing valves and cisterns operated to the end stop; a cistern "
                    "is measured from the supply valve fully open until it has closed"
                ),
                maximum_cycle="a full flushing and refilling cycle",
                equivalent_cycle="a full flushing and refilling cycle",
                nominal_integration_time_s=None,
            ),
            "mechanical_ventilation": OperatingCondition(
                clause="B.3",
                equipment="mechanical ventilation, vents and cooker hoods",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "manually operated systems at the setting of the highest level, "
                    "normally maximum speed or the fully open vent, after checking the "
                    "air flow is correctly adjusted"
                ),
                maximum_cycle="continuous operation over about 30 s",
                equivalent_cycle=_ABOUT_30_S_CYCLE,
                nominal_integration_time_s=_ABOUT_30_S,
            ),
            "heating": OperatingCondition(
                clause="B.4",
                equipment="heating: boilers, burners and radiators",
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "burner at full load with circulation pump, fan and fuel pump "
                    "running (maximum normal water and air flow); a radiator at the "
                    "thermostat setting of the highest constant level"
                ),
                maximum_cycle=(
                    "start from cold, run at full load, open and close each appliance "
                    "slowly, stop"
                ),
                equivalent_cycle=_ABOUT_30_S_CYCLE,
                nominal_integration_time_s=_ABOUT_30_S,
            ),
            "cooling": OperatingCondition(
                clause="B.4",
                equipment="cooling",
                maximum_level=True,
                equivalent_level=True,
                conditions="set to the position of the highest level",
                maximum_cycle=_ABOUT_30_S_CYCLE,
                equivalent_cycle=_ABOUT_30_S_CYCLE,
                nominal_integration_time_s=_ABOUT_30_S,
            ),
            "lift": OperatingCondition(
                clause="B.5",
                equipment="lift",
                maximum_level=True,
                equivalent_level=True,
                conditions="loaded with 1 or 2 persons; the load and number reported",
                maximum_cycle=(
                    "from the lowest level (at most five floors below the measurement "
                    "floor), stopping and working the door at each level, to the top "
                    "(at most five floors above), then straight back; repeated at least "
                    "three times with the microphone at different positions"
                ),
                equivalent_cycle="the same repeated cycle",
                nominal_integration_time_s=None,
                parameters={
                    "persons_min": 1.0,
                    "persons_max": 2.0,
                    "floors_below": 5.0,
                    "floors_above": 5.0,
                    "repetitions_min": 3.0,
                },
            ),
            "rubbish_chute": OperatingCondition(
                clause="B.6",
                equipment="rubbish chute",
                maximum_level=True,
                equivalent_level=False,
                conditions="the chute clear of waste",
                maximum_cycle=(
                    "two test objects dispatched together from the top storey: open-"
                    "ended unplasticized PVC tubes (or a material like it)"
                ),
                equivalent_cycle=None,
                nominal_integration_time_s=None,
                parameters={
                    "objects": 2.0,
                    "tube_length_m": 0.1,
                    "outer_diameter_m": 0.050,
                    "wall_thickness_m": 0.003,
                    "mass_per_length_kg_m": 0.7,
                },
            ),
            "auxiliary_equipment": OperatingCondition(
                clause="B.7",
                equipment="boilers, blowers, pumps and other auxiliary equipment",
                maximum_level=True,
                equivalent_level=True,
                conditions="run continuously under normal, loaded conditions",
                maximum_cycle=(
                    "start, operate, stop for a manually and electrically controlled "
                    "appliance; a full cycle, start and stop included, for automatic ones"
                ),
                equivalent_cycle="the duration of the operating cycle",
                nominal_integration_time_s=None,
            ),
            "car_park_door": OperatingCondition(
                clause="B.8",
                equipment="motor-driven car park door",
                maximum_level=True,
                equivalent_level=True,
                conditions="normal operation",
                maximum_cycle="opening and closing the door",
                equivalent_cycle="a full cycle of opening and closing the door",
                nominal_integration_time_s=None,
            ),
            "other_equipment": OperatingCondition(
                clause="B.9",
                equipment="other building service equipment",
                maximum_level=True,
                equivalent_level=True,
                conditions="the conditions of normal use",
                maximum_cycle="the operating cycle of normal use",
                equivalent_cycle="the duration of the operating cycle",
                nominal_integration_time_s=None,
            ),
            "unknown_source": OperatingCondition(
                clause="B.10",
                equipment=(
                    "activities and sources that cannot be monitored or controlled, "
                    "in or near the building (music, restaurants, sports facilities)"
                ),
                maximum_level=True,
                equivalent_level=True,
                conditions=(
                    "every source of the activity in its normal operation, automatic "
                    "controls suspended where needed; where the corner search is "
                    "impossible the acoustically most reflective corner is position 1, "
                    "reported as a deviation"
                ),
                maximum_cycle=None,
                equivalent_cycle=(
                    "several periods of 30 s while the source is in normal operation, "
                    "within the hour the level is expected to be highest, downtime and "
                    "minor irregular events left out"
                ),
                nominal_integration_time_s=_ABOUT_30_S,
                parameters={"period_s": 30.0, "assessment_window_s": 3600.0},
            ),
        }
    )
)

# ---------------------------------------------------------------------------
# Constants of the method
# ---------------------------------------------------------------------------

#: Reference reverberation time ``T0`` of Formula (5), 0,5 s unless another
#: value is specified.
_T0 = 0.5
#: Reference equivalent absorption area ``A0`` of Formula (6), 10 m².
_A0 = 10.0
#: Sabine constant of Formula (6), in s/m.
_SABINE = 0.16

#: Background thresholds of Clause 9, in dB: no correction at 10 dB or more,
#: Formulae (7) to (9) from 4 dB, and below 4 dB the correction held at 2,2 dB.
_NO_CORRECTION_DB = 10.0
_LIMIT_DIFFERENCE_DB = 4.0
_LIMITED_CORRECTION_DB = 2.2

#: Standardization range of 7.7 and 8: one-third-octave 50 Hz to 5 000 Hz,
#: octave 63 Hz to 4 000 Hz (Hz, inclusive).
_STANDARDIZATION_RANGE: Final = MappingProxyType(
    {"third": (50.0, 5000.0), "octave": (63.0, 4000.0)}
)

#: Frequency ranges of the weighted values (4.2, 7.8), in Hz, inclusive. The
#: octave counterpart of the restricted range is the 63 Hz to 4 000 Hz the
#: draft pairs with 50 Hz to 5 000 Hz for the standardization; the extended
#: octave range is the 31,5 Hz to 8 000 Hz of 4.2.
_WEIGHTING_RANGES: Final = MappingProxyType(
    {
        "third": MappingProxyType(
            {"restricted": (50.0, 5000.0), "extended": (25.0, 10000.0)}
        ),
        "octave": MappingProxyType(
            {"restricted": (63.0, 4000.0), "extended": (31.5, 8000.0)}
        ),
    }
)

#: Relative tolerance for matching a given band centre to a nominal one: the
#: exact base-ten centre of the 31,5 Hz band is 31,62 Hz.
_NOMINAL_TOLERANCE = 0.02

#: The A-weighted spread limits of 7.4.1, in dB, after three, six and nine
#: readings. The first is inclusive ("equal to, or less than 3,0 dB"), the other
#: two strict ("less than 6,0 dB", "less than 9,0 dB").
_SPREAD_LIMITS: Final = (3.0, 6.0, 9.0)
#: Readings per stage of 7.4.1: the corner again and two new room positions.
_READINGS_PER_STAGE = 3
#: Rank of an input with one row per microphone position (or per point).
_PER_POSITION_RANK = 2
#: Coordinates of a position: x, y and z.
_COORDINATES = 3
#: Values that convert to a float without being a number: flags and text.
_NOT_A_NUMBER_TYPES = (bool, np.bool_, str, bytes)
#: Floating-point slack on a difference of decimal readings compared with a
#: limit the draft prints, in dB or m: a spread of 35,1 - 32,1 is
#: 3,000 000 000 000 004 in binary and must still read as 3,0, and a
#: background 20,4 - 10,4 below the equipment is 9,999 999 999 999 998
#: and must still read as 10.
_LIMIT_SLACK = 1e-9

#: Decimals a scaled level is cut to before it is rounded half up: far below
#: any level a meter reads, far above the binary error of a decimal level.
_BINARY_SLACK_DECIMALS = 9

#: Position distances of 7.2 and 7.3, in metres.
_MIN_SEPARATION_M = 1.0
_PREFERRED_SEPARATION_M = 1.5
_MIN_SOURCE_DISTANCE_M = 1.5
_MIN_SURFACE_DISTANCE_M = 0.50
_MIN_SURFACE_DISTANCE_SMALL_ROOM_M = 0.30
_MIN_HEIGHT_M = 0.5
_MAX_HEIGHT_M = 2.0
_CORNER_HEIGHT_RANGE_M: Final = (0.5, 1.5)
_CORNER_WALL_DISTANCE_M = 0.5
#: The additional position of 7.9 for a source in the room: 1 m in front of a
#: wall source, and 1,5 m above the floor for a wall or a ceiling source, in m.
_ADDITIONAL_WALL_DISTANCE_M = 1.0
_ADDITIONAL_HEIGHT_M = 1.5

_Band = Literal["third", "octave"]
_Quantity = Literal["Smax", "Fmax", "eq"]
_Range = Literal["restricted", "extended"]
_Mounting = Literal["wall", "ceiling"]
_QUANTITIES: Final = ("Smax", "Fmax", "eq")
_BANDS: Final = ("third", "octave")
_RANGES: Final = ("restricted", "extended")
_MOUNTINGS: Final = ("wall", "ceiling")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _round_half_up_array(values: ArrayLike, decimals: int) -> np.ndarray:
    """Round halves upward, not to even as :func:`round` would.

    7.5 rounds the band average to one decimal and 7.8 the weighted values to
    whole decibels without naming a rule for the half; the half is taken
    upward, the rule of ISO 717-1 and ISO 717-2 that the same laboratories
    apply to the same spectra. The scaled value is first cut to nine decimals,
    so a level that is a half in decimal but comes out a hair under it in
    binary still rounds up: three readings of 40,65 dB average to
    40,649 999 999 999 99 by Formula (1), and 7.5 makes it 40,7 dB.
    """
    scale = 10.0**decimals
    scaled = np.round(
        np.asarray(values, dtype=np.float64) * scale, _BINARY_SLACK_DECIMALS
    )
    return np.floor(scaled + 0.5) / scale


def _round_half_up(value: float, decimals: int = 0) -> float:
    """Scalar form of :func:`_round_half_up_array`."""
    return float(_round_half_up_array(value, decimals))


def _nominal_bands(frequencies_hz: ArrayLike, band: str) -> np.ndarray:
    """Match each given centre to the nominal band of 4.2 it stands for."""
    table = np.asarray(_THIRD_OCTAVE_BANDS if band == "third" else _OCTAVE_BANDS)
    freqs = np.atleast_1d(_as_float64(frequencies_hz, "frequencies_hz"))
    if freqs.ndim != 1 or freqs.size == 0 or not np.all(np.isfinite(freqs)):
        msg = "'frequencies_hz' must be a non-empty one-dimensional list of finite centres."
        raise ValueError(msg)
    nominal = np.empty_like(freqs)
    for i, f in enumerate(freqs):
        j = int(np.argmin(np.abs(table - f)))
        if not math.isclose(f, float(table[j]), rel_tol=_NOMINAL_TOLERANCE):
            low, high = table[0], table[-1]
            msg = (
                f"{f:g} Hz is not a nominal {band}-band centre of ISO/DIS 16032 4.2 "
                f"({low:g} Hz to {high:g} Hz)."
            )
            raise ValueError(msg)
        nominal[i] = table[j]
    if np.any(np.diff(nominal) <= 0.0):
        msg = "'frequencies_hz' must name each band once, in increasing order."
        raise ValueError(msg)
    return nominal


def _in_range(nominal: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    """Which nominal bands lie within an inclusive frequency range."""
    low, high = bounds
    return (nominal >= low * (1.0 - _NOMINAL_TOLERANCE)) & (
        nominal <= high * (1.0 + _NOMINAL_TOLERANCE)
    )


def _covers(nominal: np.ndarray, band: str, bounds: tuple[float, float]) -> bool:
    """Whether every nominal band of a range is among the given ones."""
    table = np.asarray(_THIRD_OCTAVE_BANDS if band == "third" else _OCTAVE_BANDS)
    needed = table[_in_range(table, bounds)]
    return bool(np.all(np.isin(needed, nominal)))


def _weighted_sum(
    levels: np.ndarray, corrections: np.ndarray, mask: np.ndarray
) -> float:
    """Formula (2) or (3): the energy sum of the weighted bands in the range."""
    return float(
        10.0 * np.log10(np.sum(10.0 ** (0.1 * (levels[mask] + corrections[mask]))))
    )


def _as_levels(value: ArrayLike, name: str) -> np.ndarray:
    """A finite float array of levels, or a ``ValueError`` naming the input."""
    arr = _as_float64(value, name)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        msg = f"'{name}' must hold finite levels in dB."
        raise ValueError(msg)
    return arr


def _positive_number(value: ArrayLike, name: str) -> float:
    """One positive, finite, real number, or a ``ValueError`` naming it.

    A string, a flag, a complex number or an array of numbers is refused
    rather than converted, whether it comes bare or wrapped in a 0-d array of
    any dtype: ``float("50")`` and ``float(True)`` would each give a volume,
    and so would ``np.array("50")``, ``np.array(True)`` and
    ``np.array(True, dtype=object)``; a one-element array would reach
    :func:`float` only to raise an anonymous ``TypeError``, and a ragged list
    fails in numpy before any guard could name it.
    """
    msg = f"'{name}' must be one positive number."
    try:
        arr = np.asarray(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(msg) from exc
    # The element itself decides, so a flag or a text inside an object array
    # is refused like a bare one.
    if arr.ndim != 0 or isinstance(arr.item(), _NOT_A_NUMBER_TYPES):
        raise ValueError(msg)
    return require_positive(float(_as_float64(value, name)), name)


def _room(room_dimensions_m: ArrayLike) -> np.ndarray:
    """The length, width and height of a rectangular room, or a ``ValueError``."""
    dims = _as_float64(room_dimensions_m, "room_dimensions_m")
    if dims.shape != (3,) or not np.all(np.isfinite(dims)) or np.any(dims <= 0.0):
        msg = "'room_dimensions_m' must be the positive length, width and height of the room."
        raise ValueError(msg)
    return dims


def _refuse_truth_value(owner: str) -> str:
    """The message of a verdict that refuses to be read as a ``bool``."""
    return f"a {owner} has no truth value; read its '.passes' for the verdict"


# ---------------------------------------------------------------------------
# Background correction (Clause 9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceEquipmentBackgroundResult:
    r"""Band levels corrected for the background by Clause 9.

    :ivar measured_db: The measured band levels :math:`L_1`, background
        included, in dB.
    :ivar background_db: The background band levels :math:`L_2`, in dB.
    :ivar difference_db: :math:`\Delta L = L_1 - L_2` per band, in dB
        (Formula (9)).
    :ivar correction_db: The correction :math:`K` per band, in dB: 0 at 10 dB or
        more, Formula (8) from 4 dB, and 2,2 dB below 4 dB.
    :ivar corrected_db: :math:`L = L_1 - K` per band, in dB (Formula (7)).
    :ivar regime: Per band, ``"none"`` (no correction), ``"corrected"``
        (Formula (8)) or ``"limited"`` (held at 2,2 dB: the band is an upper
        limit of the equipment level).
    :ivar frequencies_hz: The band centres, in Hz, or ``None`` when not given.
    """

    measured_db: np.ndarray
    background_db: np.ndarray
    difference_db: np.ndarray
    correction_db: np.ndarray
    corrected_db: np.ndarray
    regime: tuple[str, ...]
    frequencies_hz: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Reject a correction whose band arrays disagree in length.

        :raises ValueError: if the arrays or the regimes do not share one band
            count.
        """
        n = np.asarray(self.measured_db).shape
        arrays = (
            self.background_db,
            self.difference_db,
            self.correction_db,
            self.corrected_db,
        )
        if any(np.asarray(a).shape != n for a in arrays) or len(self.regime) != n[0]:
            msg = "ServiceEquipmentBackgroundResult: every band quantity needs one value per band."
            raise ValueError(msg)
        if (
            self.frequencies_hz is not None
            and np.asarray(self.frequencies_hz).shape != n
        ):
            msg = "ServiceEquipmentBackgroundResult: 'frequencies_hz' needs one centre per band."
            raise ValueError(msg)

    @property
    def limited(self) -> np.ndarray:
        """Per band, whether the background held the correction at 2,2 dB.

        :return: One boolean per band; ``True`` marks an upper limit.
        """
        return np.asarray([r == "limited" for r in self.regime], dtype=bool)

    @property
    def influenced(self) -> bool:
        """Whether any band is influenced by the background (Clause 9).

        :return: ``True`` when at least one band was held at 2,2 dB, which the
            report has to state.
        """
        return bool(np.any(self.limited))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot measured, background and corrected band levels.

        Bands held at 2,2 dB are marked as upper limits. Requires matplotlib
        (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the corrected-level curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_service_equipment_background

        return plot_service_equipment_background(
            self, ax=ax, language=check_language(language), **kwargs
        )


def service_equipment_background_correction(
    levels_db: ArrayLike,
    background_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike | None = None,
) -> ServiceEquipmentBackgroundResult:
    r"""Correct band levels for the background (ISO/DIS 16032:2023 Clause 9).

    With :math:`\Delta L = L_1 - L_2` the band is left as it is at 10 dB or
    more, corrected with :math:`K = -10 \lg(1 - 10^{-0,1 \Delta L})` from 4 dB
    to 10 dB (Formulae (7) to (9)), and below 4 dB the correction is held at
    2,2 dB, the value a 4 dB difference gives. Such a band is influenced by the
    background, which the report has to state, and for a comparison with a
    limit the result is an upper limit of the equipment level. A background at
    or above the measured level is the same case: held at 2,2 dB rather than
    left undefined.

    The method assumes a background roughly constant in time. Where it is not,
    the NOTE to Clause 9 suggests the maximum level of the background over 10
    to 15 minutes at the corner position instead: if it is 10 dB or more below
    the equipment, the result stands without correction.

    :param levels_db: Measured band levels :math:`L_1`, background included,
        in dB.
    :param background_db: Background band levels :math:`L_2`, in dB, the same
        shape.
    :param frequencies_hz: Band centres in Hz, kept for the plot only.
    :return: :class:`ServiceEquipmentBackgroundResult`.
    :raises ValueError: If a level is not finite or the shapes differ.
    """
    measured = np.atleast_1d(_as_levels(levels_db, "levels_db"))
    background = np.atleast_1d(_as_levels(background_db, "background_db"))
    if measured.ndim != 1 or background.shape != measured.shape:
        msg = "'levels_db' and 'background_db' must be one level per band, the same length."
        raise ValueError(msg)
    freqs = None
    if frequencies_hz is not None:
        freqs = _as_float64(frequencies_hz, "frequencies_hz")
        if freqs.shape != measured.shape or not np.all(np.isfinite(freqs)):
            msg = "'frequencies_hz' must give one finite centre per band."
            raise ValueError(msg)
    difference = measured - background
    # The thresholds are read with the slack of a decimal difference: 20,4 dB
    # over 10,4 dB is a 10 dB margin to Clause 9 and a hair under it in binary.
    uncorrected = difference >= _NO_CORRECTION_DB - _LIMIT_SLACK
    corrected_regime = ~uncorrected & (
        difference >= _LIMIT_DIFFERENCE_DB - _LIMIT_SLACK
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        formula = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * difference))
    correction = np.where(
        uncorrected,
        0.0,
        np.where(corrected_regime, formula, _LIMITED_CORRECTION_DB),
    )
    regime = tuple(
        "none" if none else "corrected" if formed else "limited"
        for none, formed in zip(uncorrected, corrected_regime, strict=True)
    )
    return ServiceEquipmentBackgroundResult(
        measured_db=measured.copy(),
        background_db=background.copy(),
        difference_db=difference,
        correction_db=np.asarray(correction, dtype=np.float64),
        corrected_db=measured - correction,
        regime=regime,
        frequencies_hz=freqs,
    )


# ---------------------------------------------------------------------------
# The result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceEquipmentResult:
    r"""Service-equipment sound pressure level, engineering method.

    Produced by :func:`service_equipment_level`. Every band array runs over
    :attr:`frequencies_hz`.

    :ivar frequencies_hz: Nominal band centres, in Hz.
    :ivar band: ``"third"`` or ``"octave"``.
    :ivar quantity: The Table 1 quantity: ``"Smax"``, ``"Fmax"`` or ``"eq"``.
    :ivar a_weighting_range: ``"restricted"`` (50 Hz to 5 000 Hz; octave
        63 Hz to 4 000 Hz) or ``"extended"`` (25 Hz to 10 000 Hz; octave
        31,5 Hz to 8 000 Hz), the range the A-weighted values were summed over.
    :ivar readings_db: The band levels of every reading, shape
        ``(readings, bands)``, in dB.
    :ivar average_db: Formula (1) over the readings, rounded to one decimal
        (7.5), in dB.
    :ivar background: The Clause 9 correction, or ``None`` when no background
        was given.
    :ivar corrected_db: The average corrected for the background, in dB (the
        average itself when there is no background).
    :ivar standardizable: Per band, whether 7.7 lets it be standardized or
        normalized (50 Hz to 5 000 Hz; octave 63 Hz to 4 000 Hz).
    :ivar standardized_db: :math:`L_\mathrm{nT}` per band (Formula (5)), in dB,
        or ``None`` without a reverberation time. Bands outside the range are
        the corrected level, unstandardized.
    :ivar normalized_db: :math:`L_\mathrm{n}` per band (Formula (6)), in dB, or
        ``None`` without a reverberation time and a volume.
    :ivar ratings: The weighted single numbers of Table 1, rounded to whole
        decibels (7.8), keyed by their notation: ``"LA,eq"``,
        ``"LA,Smax,nT"``, ``"LC,Fmax,n"`` and so on. The C-weighted ones are
        present only when the bands cover the extended range.
    :ivar unrounded_ratings: The same single numbers before rounding, in dB.
    :ivar reproducibility_db: The Table 2 standard deviation of each band, in
        dB.
    """

    frequencies_hz: np.ndarray
    band: str
    quantity: str
    a_weighting_range: str
    readings_db: np.ndarray
    average_db: np.ndarray
    background: ServiceEquipmentBackgroundResult | None
    corrected_db: np.ndarray
    standardizable: np.ndarray
    standardized_db: np.ndarray | None
    normalized_db: np.ndarray | None
    ratings: Mapping[str, int]
    unrounded_ratings: Mapping[str, float]
    reproducibility_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject a result whose band arrays do not share one band set.

        :raises ValueError: if a band array differs in length from
            :attr:`frequencies_hz` or the readings are not two-dimensional.
        """
        shape = np.asarray(self.frequencies_hz).shape
        bands = [
            self.average_db,
            self.corrected_db,
            self.standardizable,
            self.reproducibility_db,
        ]
        bands += [
            a for a in (self.standardized_db, self.normalized_db) if a is not None
        ]
        if any(np.asarray(a).shape != shape for a in bands):
            msg = (
                "ServiceEquipmentResult: every band quantity needs one value per band."
            )
            raise ValueError(msg)
        readings = np.asarray(self.readings_db)
        if readings.ndim != _PER_POSITION_RANK or readings.shape[1:] != shape:
            msg = "ServiceEquipmentResult: 'readings_db' must be (readings, bands)."
            raise ValueError(msg)

    @property
    def reading_count(self) -> int:
        """The number of readings averaged by Formula (1).

        :return: The number of rows of :attr:`readings_db`.
        """
        return int(np.asarray(self.readings_db).shape[0])

    def _range_mask(self, weighting: str) -> np.ndarray:
        """The bands a weighted value of this result was summed over."""
        key = self.a_weighting_range if weighting == "A" else "extended"
        return _in_range(
            np.asarray(self.frequencies_hz), _WEIGHTING_RANGES[self.band][key]
        )

    def upper_limit(self, weighting: str) -> bool:
        """Whether a weighted value is an upper limit because of the background.

        A band the background held at 2,2 dB (Clause 9) that lies in the range
        of the weighted sum makes that sum an upper limit, and Clause 9 asks the
        report to say whether the A- and the C-weighted value are influenced.

        :param weighting: ``"A"`` or ``"C"``.
        :return: ``True`` when a band of the range was held at 2,2 dB.
        :raises ValueError: for a weighting other than A or C.
        """
        require_choice(weighting, "weighting", ("A", "C"))
        if self.background is None:
            return False
        return bool(np.any(self.background.limited & self._range_mask(weighting)))

    @property
    def unstandardized_bands_hz(self) -> tuple[float, ...]:
        """The bands that enter the weighted values without standardization.

        7.7 keeps 25, 31,5, 40, 6 300, 8 000 and 10 000 Hz (octaves 31,5 Hz and
        8 000 Hz) out of the standardization and normalization, and asks the
        report to mention them whenever they contribute to a weighted value.

        :return: The centres, in Hz, of the bands inside a weighted range that
            were left unstandardized; empty when nothing was standardized.
        """
        if self.standardized_db is None:
            return ()
        used = self._range_mask("A")
        if any(k.startswith("LC") for k in self.ratings):
            used = used | self._range_mask("C")
        freqs = np.asarray(self.frequencies_hz)
        return tuple(float(f) for f in freqs[used & ~np.asarray(self.standardizable)])

    @property
    def weighted_reproducibility_db(self) -> Mapping[str, float]:
        """The Table 2 standard deviation of each single number, in dB.

        0,8 dB for every A-weighted value of :attr:`ratings` and 1,2 dB for
        every C-weighted one. Footnote a of Table 2 limits both to a constant
        sound with a relatively flat spectrum from 25 Hz to 10 000 Hz, at least
        10 dB above the background; a fluctuating source, a maximum level most
        of all, is more uncertain, and the draft states no coverage factor.

        :return: The reproducibility standard deviation keyed like
            :attr:`ratings` (``"LA,eq"``, ``"LC,Fmax,nT"``...).
        """
        return MappingProxyType(
            {
                key: SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY[key[1]]
                for key in self.ratings
            }
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the band spectrum through each step of the method.

        The average, the background, the corrected level and, when formed, the
        standardized one, with the bands the background limits marked and the
        A-weighted single numbers in the title. Requires matplotlib
        (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of the final band levels.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_service_equipment_level

        return plot_service_equipment_level(
            self, ax=ax, language=check_language(language), **kwargs
        )


def service_equipment_level(
    levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    quantity: _Quantity,
    band: _Band = "third",
    background_db: ArrayLike | None = None,
    reverberation_time_s: ArrayLike | None = None,
    volume_m3: float | None = None,
    reference_reverberation_time_s: float = _T0,
    a_weighting_range: _Range = "restricted",
) -> ServiceEquipmentResult:
    r"""Sound pressure level of service equipment in a room (ISO/DIS 16032:2023).

    The chain of Clauses 6 and 7: the band levels of every reading are
    energy-averaged by Formula (1) and rounded to one decimal (7.5), corrected
    for the background by Clause 9, standardized by Formula (5) or normalized
    by Formula (6) where a reverberation time is given (7.7, 50 Hz to 5 000 Hz
    only), and summed into the A- and C-weighted single numbers of Table 1 with
    the Annex A corrections, rounded to whole decibels (7.8).

    The readings are the linear band spectra of the measurements of 7.4:
    positions 1, 2 and 3 at least, with the corner reading repeated in each
    further stage that :func:`check_position_spread` asks for. Take them at the
    instant the A- or C-weighted level peaks for a maximum level (Clause 6), or
    over the integration time of Annex B for an equivalent level.

    :param levels_db: Band levels of each reading, shape ``(readings, bands)``
        (one-dimensional for a single reading), in dB.
    :param frequencies_hz: Nominal band centres, in Hz, increasing: the
        one-third-octave bands of 25 Hz to 10 000 Hz or the octave bands of
        31,5 Hz to 8 000 Hz, as ``band`` says.
    :param quantity: The Table 1 quantity measured: ``"Smax"``, ``"Fmax"`` or
        ``"eq"``. It names the single numbers and nothing else.
    :param band: ``"third"`` (default) or ``"octave"``. 6 asks for the weighted
        values from one-third-octave bands; octave results are optional.
    :param background_db: Background band levels, in dB, one per band or one
        row per microphone position (energy-averaged over the positions, as the
        2004 edition says in so many words and the draft leaves implicit).
    :param reverberation_time_s: Reverberation time of each band, in s,
        measured by ISO 3382-2 (Clause 8). Only the bands of the
        standardization range are read; the others may be ``nan``.
    :param volume_m3: Room volume, in m³, for the normalized levels.
    :param reference_reverberation_time_s: :math:`T_0` of Formula (5), in s
        (0,5 s unless a regulation specifies another value).
    :param a_weighting_range: ``"restricted"`` (default: 50 Hz to 5 000 Hz,
        octave 63 Hz to 4 000 Hz) or ``"extended"`` (25 Hz to 10 000 Hz,
        octave 31,5 Hz to 8 000 Hz) for the A-weighted values; the report must
        say which. The C-weighted values always use the extended range.
    :return: :class:`ServiceEquipmentResult`.
    :raises ValueError: If a centre is not a nominal band, the bands do not
        cover the A-weighting range, the shapes disagree, a level is not a
        finite real number, a reverberation time in the standardization range
        is not positive, ``volume_m3`` or ``reference_reverberation_time_s``
        is not one positive number, or ``volume_m3`` is given without a
        reverberation time.
    """
    require_choice(quantity, "quantity", _QUANTITIES)
    require_choice(band, "band", _BANDS)
    require_choice(a_weighting_range, "a_weighting_range", _RANGES)
    # T0 is read only with a reverberation time, and checked on every call.
    t0 = _positive_number(
        reference_reverberation_time_s, "reference_reverberation_time_s"
    )
    nominal = _nominal_bands(frequencies_hz, band)
    readings = _as_levels(levels_db, "levels_db")
    if readings.ndim == 1:
        readings = readings[np.newaxis, :]
    if readings.ndim != _PER_POSITION_RANK or readings.shape[1] != nominal.size:
        msg = "'levels_db' must be (readings, bands) with one column per band of 'frequencies_hz'."
        raise ValueError(msg)

    a_mask = _in_range(nominal, _WEIGHTING_RANGES[band][a_weighting_range])
    if not _covers(nominal, band, _WEIGHTING_RANGES[band][a_weighting_range]):
        low, high = _WEIGHTING_RANGES[band][a_weighting_range]
        msg = (
            f"The {a_weighting_range} A-weighting range needs every {band} band from "
            f"{low:g} Hz to {high:g} Hz (ISO/DIS 16032 7.8)."
        )
        raise ValueError(msg)
    c_bounds = _WEIGHTING_RANGES[band]["extended"]
    c_mask = _in_range(nominal, c_bounds) if _covers(nominal, band, c_bounds) else None

    average = _round_half_up_array(energy_mean(readings, axis=0), 1)

    background = None
    corrected = average.copy()
    if background_db is not None:
        bg = _as_levels(background_db, "background_db")
        if bg.ndim == _PER_POSITION_RANK:
            bg = energy_mean(bg, axis=0)
        background = service_equipment_background_correction(
            average, bg, frequencies_hz=nominal
        )
        corrected = background.corrected_db.copy()

    standardizable = _in_range(nominal, _STANDARDIZATION_RANGE[band])
    standardized, normalized = _standardize(
        corrected,
        standardizable,
        reverberation_time_s=reverberation_time_s,
        volume_m3=volume_m3,
        t0=t0,
    )

    weights = SERVICE_EQUIPMENT_WEIGHTING[band]
    a_corr = np.asarray([weights["A"][float(f)] for f in nominal])
    c_corr = np.asarray([weights["C"][float(f)] for f in nominal])
    unrounded: dict[str, float] = {}
    variants = (("", corrected), (",nT", standardized), (",n", normalized))
    for suffix, levels in variants:
        if levels is None:
            continue
        unrounded[f"LA,{quantity}{suffix}"] = _weighted_sum(levels, a_corr, a_mask)
        if c_mask is not None:
            unrounded[f"LC,{quantity}{suffix}"] = _weighted_sum(levels, c_corr, c_mask)
    ratings = {k: int(_round_half_up(v)) for k, v in unrounded.items()}

    reproducibility = np.asarray(
        [SERVICE_EQUIPMENT_REPRODUCIBILITY[band][float(f)] for f in nominal]
    )
    return ServiceEquipmentResult(
        frequencies_hz=nominal,
        band=band,
        quantity=quantity,
        a_weighting_range=a_weighting_range,
        readings_db=readings.copy(),
        average_db=average,
        background=background,
        corrected_db=corrected,
        standardizable=standardizable,
        standardized_db=standardized,
        normalized_db=normalized,
        ratings=MappingProxyType(ratings),
        unrounded_ratings=MappingProxyType(unrounded),
        reproducibility_db=reproducibility,
    )


def _standardize(
    corrected: np.ndarray,
    standardizable: np.ndarray,
    *,
    reverberation_time_s: ArrayLike | None,
    volume_m3: float | None,
    t0: float,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Formulae (5) and (6) over the standardization range of 7.7.

    ``t0`` is :math:`T_0` in s, already checked by the caller.
    """
    if reverberation_time_s is None:
        if volume_m3 is not None:
            msg = "'volume_m3' normalizes through Formula (6), which also needs 'reverberation_time_s'."
            raise ValueError(msg)
        return None, None
    t = np.atleast_1d(_as_float64(reverberation_time_s, "reverberation_time_s"))
    if t.shape != corrected.shape:
        msg = "'reverberation_time_s' must give one value per band."
        raise ValueError(msg)
    used = t[standardizable]
    if not (np.all(np.isfinite(used)) and np.all(used > 0.0)):
        msg = (
            "'reverberation_time_s' must be positive in every band from 50 Hz to "
            "5 000 Hz (octave 63 Hz to 4 000 Hz) the result is standardized in."
        )
        raise ValueError(msg)
    safe_t = np.where(standardizable, t, t0)
    standardized = corrected - np.where(
        standardizable, 10.0 * np.log10(safe_t / t0), 0.0
    )
    if volume_m3 is None:
        return standardized, None
    v = _positive_number(volume_m3, "volume_m3")
    normalized = corrected - np.where(
        standardizable, 10.0 * np.log10(_A0 * safe_t / (_SABINE * v)), 0.0
    )
    return standardized, normalized


# ---------------------------------------------------------------------------
# How many positions (7.4.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PositionSpreadCheck:
    r"""Whether the readings so far are enough to average (7.4.1).

    :ivar levels_db: The A-weighted levels read directly from the instrument,
        uncorrected, in the order of 7.4.1: corner, position 2, position 3,
        then (corner, 4, 5) and (corner, 6, 7) for each further stage, in dB.
    :ivar stage: 1, 2 or 3: how many sets of three readings there are.
    :ivar spread_db: The difference between the highest and lowest reading, in
        dB.
    :ivar limit_db: The spread this stage allows: 3,0 dB (inclusive), 6,0 dB or
        9,0 dB (strict).
    :ivar action: ``"proceed"`` to the corrections of 7.5 to 7.7,
        ``"add_positions"`` for the corner again and two new room positions, or
        ``"interrupt"`` when no further stage can pass: after nine readings, or
        sooner when the spread already reaches 9,0 dB.
    :ivar next_positions: The room positions to add, ``(4, 5)`` or ``(6, 7)``,
        or ``()``.
    :ivar corner_standard_deviation_db: Sample standard deviation of the corner
        readings, in dB, which 7.4.1 takes as representative of the room
        average when a statistical value (a 5 % value, the n-th highest) is
        wanted; ``None`` with a single corner reading.
    """

    levels_db: np.ndarray
    stage: int
    spread_db: float
    limit_db: float
    action: Literal["proceed", "add_positions", "interrupt"]
    next_positions: tuple[int, ...]
    corner_standard_deviation_db: float | None

    def __post_init__(self) -> None:
        """Reject a check whose readings do not make a whole number of stages.

        :raises ValueError: if the level count is not 3, 6 or 9 or disagrees
            with :attr:`stage`.
        """
        n = np.asarray(self.levels_db).size
        if n != _READINGS_PER_STAGE * self.stage or self.stage not in (1, 2, 3):
            msg = "PositionSpreadCheck: 'levels_db' must hold 3, 6 or 9 readings, three per stage."
            raise ValueError(msg)

    @property
    def passes(self) -> bool:
        """Whether the readings may be averaged as they are.

        :return: ``True`` when :attr:`action` is ``"proceed"``.
        """
        return self.action == "proceed"

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        raise TypeError(_refuse_truth_value("PositionSpreadCheck"))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the readings against the spread the stage allows.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the markers of the room positions.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_position_spread

        return plot_position_spread(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_position_spread(levels_db: ArrayLike) -> PositionSpreadCheck:
    r"""Are the positions measured so far enough (ISO/DIS 16032:2023 7.4.1)?

    The A-weighted levels read directly from the instrument, without any
    correction, decide how many positions are measured. With three readings
    (corner, 2, 3) a spread up to and including 3,0 dB lets the corrections
    proceed; otherwise the corner is measured again with two new room
    positions (4 and 5), and the six must differ by less than 6,0 dB, then
    once more (corner, 6 and 7) and the nine by less than 9,0 dB. 7.4.2
    applies the same steps to a maximum level, with the sound exposure level
    :math:`L_\mathrm{AE}` allowed in its place for short events.

    The draft interrupts the session when the difference "is larger than
    9,0 dB and is related to unpredictable time domain variations whereas the
    readings in the corner position confirm the sound source is stable": the
    reasons are investigated before a new series, and no reading of the
    interrupted one is used. Levels alone cannot say what a difference is
    related to, so the check answers ``"interrupt"`` whenever no further stage
    can pass and leaves those two conditions to the operator: a spread still
    9,0 dB or more after nine readings, and a spread that already reaches
    9,0 dB after three or six, since more readings can only widen it. The
    third paragraph of 7.4.1 sends to positions 6 and 7 only a difference
    "less than 9,0 dB".

    The draft states no rule at a spread of exactly 6,0 dB after six readings
    or 9,0 dB after nine, nor for three readings 6,0 dB or more apart. The
    ladder is read as a sequence: a stage that does not pass goes to the next
    while a later one can still pass, and a spread at a limit does not pass it
    (``docs/ERRATA.md``).

    :param levels_db: The 3, 6 or 9 A-weighted levels in the order of 7.4.1:
        ``[corner, 2, 3]``, then ``[corner, 4, 5]`` and ``[corner, 6, 7]``
        appended, in dB.
    :return: :class:`PositionSpreadCheck`.
    :raises ValueError: If there are not 3, 6 or 9 finite levels.
    """
    levels = np.atleast_1d(_as_levels(levels_db, "levels_db"))
    if levels.ndim != 1 or levels.size not in (3, 6, 9):
        msg = "'levels_db' must hold 3, 6 or 9 readings: [corner, 2, 3] and each later stage."
        raise ValueError(msg)
    stage = levels.size // _READINGS_PER_STAGE
    limit = _SPREAD_LIMITS[stage - 1]
    spread = float(np.max(levels) - np.min(levels))
    within = (
        spread <= limit + _LIMIT_SLACK if stage == 1 else spread < limit - _LIMIT_SLACK
    )
    # A spread can only widen as readings are added, and the last stage
    # needs it under 9,0 dB: once it reaches that, no stage is left to pass.
    reachable = spread < _SPREAD_LIMITS[-1] - _LIMIT_SLACK
    action: Literal["proceed", "add_positions", "interrupt"]
    following: tuple[int, ...]
    if within:
        action, following = "proceed", ()
    elif stage < len(_SPREAD_LIMITS) and reachable:
        action, following = "add_positions", (2 * stage + 2, 2 * stage + 3)
    else:
        action, following = "interrupt", ()
    corners = levels[::_READINGS_PER_STAGE]
    corner_sd = float(np.std(corners, ddof=1)) if corners.size > 1 else None
    return PositionSpreadCheck(
        levels_db=levels.copy(),
        stage=stage,
        spread_db=spread,
        limit_db=limit,
        action=action,
        next_positions=following,
        corner_standard_deviation_db=corner_sd,
    )


# ---------------------------------------------------------------------------
# Where the positions are (7.2, 7.3)
# ---------------------------------------------------------------------------


def loudest_corner(
    c_weighted_levels_db: ArrayLike, *, excluded: Sequence[int] = ()
) -> int:
    """The corner that becomes microphone position 1 (ISO/DIS 16032:2023 7.2).

    Position 1 is the corner with the highest C-weighted level, measured
    directly (a hand-held integrating meter will do: no band calculation, no
    reverberation or background correction) as the maximum level with time
    weighting S or F or as the equivalent level, under the chosen operating
    conditions or any steady condition that finds the loudest corner. A corner
    whose level is dominated by direct sound from a source in the room, a
    ventilation outlet for example, is left out.

    :param c_weighted_levels_db: One C-weighted level per corner, in dB.
    :param excluded: Indices of the corners dominated by direct sound, counted
        from 0 in the order of ``c_weighted_levels_db``.
    :return: The index of the loudest corner left, counted from 0; the first of
        a tie.
    :raises ValueError: If a level is not finite, ``excluded`` is not a
        sequence of whole numbers, an index is out of range, or every corner
        is excluded.
    """
    levels = np.atleast_1d(_as_levels(c_weighted_levels_db, "c_weighted_levels_db"))
    if levels.ndim != 1:
        msg = "'c_weighted_levels_db' must give one level per corner."
        raise ValueError(msg)
    msg = "'excluded' must be a sequence of corner indices, such as [1]."
    try:
        rank = np.ndim(excluded)
    except (TypeError, ValueError) as exc:  # a ragged nesting of lists
        raise ValueError(msg) from exc
    if isinstance(excluded, (str, bytes)) or rank != 1:
        raise ValueError(msg)
    left = np.ones(levels.size, dtype=bool)
    for value in excluded:
        # A bool, a string or 1,7 is not the number of a corner: int() would
        # read each of them as one and leave that corner out without a word.
        index = require_count(value, "excluded", minimum=0)
        if index >= levels.size:
            msg = f"Corner index {index} is out of range for {levels.size} corners."
            raise ValueError(msg)
        left[index] = False
    if not np.any(left):
        msg = "Every corner is excluded; 7.2 leaves no corner to measure in."
        raise ValueError(msg)
    candidates = np.where(left, levels, -np.inf)
    return int(np.argmax(candidates))


@dataclass(frozen=True)
class ServiceEquipmentPositionCheck:
    """Whether the positions keep the corner height of 7.2 and the distances of 7.3.

    Positions are coordinates in metres in a rectangular room with one corner
    at the origin: ``x`` along the length, ``y`` along the width and ``z`` the
    height above the floor.

    :ivar room_dimensions_m: Length, width and height of the room, in m.
    :ivar corner_position_m: Position 1, in m.
    :ivar room_positions_m: The reverberant-field positions, shape ``(k, 3)``,
        in m.
    :ivar source_positions_m: Sound sources in the room, shape ``(m, 3)``, in
        m (empty when none were given).
    :ivar small_room: Whether the small-room surface distance of 7.3 applies.
    :ivar separation_m: The shortest distance between any two positions,
        corner included, in m.
    :ivar surface_distance_m: The shortest distance from a room position to a
        wall, the floor or the ceiling, in m.
    :ivar source_distance_m: The shortest distance from a room position to a
        source, in m, or ``None`` without sources.
    :ivar heights_m: The heights of the room positions, in m.
    :ivar corner_height_m: The height of the corner position, in m.
    :ivar corner_wall_distances_m: The corner position's distances to the two
        walls nearest to it, in m; 7.2 prefers 0,5 m
        (:attr:`preferred_corner_wall_distance`, advisory).
    :ivar separation_ok: At least 1,0 m between positions.
    :ivar surface_ok: At least 0,50 m (0,30 m in a small room) from every
        surface.
    :ivar source_ok: At least 1,5 m from every source.
    :ivar height_ok: Every room position from 0,5 m to 2,0 m high.
    :ivar corner_height_ok: The corner position from 0,5 m to 1,5 m high.
    """

    room_dimensions_m: np.ndarray
    corner_position_m: np.ndarray
    room_positions_m: np.ndarray
    source_positions_m: np.ndarray
    small_room: bool
    separation_m: float
    surface_distance_m: float
    source_distance_m: float | None
    heights_m: np.ndarray
    corner_height_m: float
    corner_wall_distances_m: tuple[float, float]
    separation_ok: bool
    surface_ok: bool
    source_ok: bool
    height_ok: bool
    corner_height_ok: bool

    @property
    def surface_limit_m(self) -> float:
        """The surface distance 7.3 asks of this room, in m.

        :return: 0,30 m in a small room, 0,50 m otherwise.
        """
        return (
            _MIN_SURFACE_DISTANCE_SMALL_ROOM_M
            if self.small_room
            else _MIN_SURFACE_DISTANCE_M
        )

    @property
    def source_limit_m(self) -> float:
        """The distance 7.3 asks between a room position and a source, in m.

        :return: 1,5 m.
        """
        return _MIN_SOURCE_DISTANCE_M

    @property
    def preferred_separation(self) -> bool:
        """Whether the positions are 1,5 m apart, the distance 7.3 prefers.

        :return: ``True`` at 1,5 m or more; advisory, not part of
            :attr:`passes`.
        """
        return self.separation_m >= _PREFERRED_SEPARATION_M - _LIMIT_SLACK

    @property
    def preferred_corner_wall_distance(self) -> bool:
        """Whether position 1 is 0,5 m from both walls of its corner, as 7.2 prefers.

        7.2 places the corner microphone "preferably" 0,5 m from the walls and
        the floor, and where furniture is in the way raises only its height,
        which :attr:`corner_height_ok` judges. The draft gives the wall
        distance no tolerance and no lower or upper bound, so a corner position
        elsewhere is a departure the operator reports rather than a failure.

        :return: ``True`` when both :attr:`corner_wall_distances_m` are 0,5 m;
            advisory, not part of :attr:`passes`.
        """
        return all(
            abs(d - _CORNER_WALL_DISTANCE_M) <= _LIMIT_SLACK
            for d in self.corner_wall_distances_m
        )

    @property
    def passes(self) -> bool:
        """Whether the distances and heights of 7.3 and the corner height of 7.2 hold.

        The corner position enters through its height alone: the 0,5 m from
        its walls is a preference (:attr:`preferred_corner_wall_distance`),
        like the 1,5 m between positions (:attr:`preferred_separation`), and
        the 0,2 m from any obstacle that 7.2 also asks is not judged.

        :return: ``True`` when all five requirements hold.
        """
        return all(
            (
                self.separation_ok,
                self.surface_ok,
                self.source_ok,
                self.height_ok,
                self.corner_height_ok,
            )
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        raise TypeError(_refuse_truth_value("ServiceEquipmentPositionCheck"))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the room in plan with the positions and their clearances.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the markers of the room positions.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_service_equipment_positions

        return plot_service_equipment_positions(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _points(value: ArrayLike, name: str) -> np.ndarray:
    """An ``(n, 3)`` array of finite coordinates, or a ``ValueError``.

    An empty list is no position at all, the same as an empty ``(0, 3)``
    array, so ``[]`` for the sources means none and ``[]`` for the room
    positions meets the refusal of a missing position by name.
    """
    arr = _as_float64(value, name)
    if arr.ndim == 1 and arr.size == 0:
        arr = arr.reshape(0, _COORDINATES)
    elif arr.ndim == 1:
        arr = arr[np.newaxis, :]
    if (
        arr.ndim != _PER_POSITION_RANK
        or arr.shape[1] != _COORDINATES
        or not np.all(np.isfinite(arr))
    ):
        msg = f"'{name}' must be finite (x, y, z) coordinates in metres."
        raise ValueError(msg)
    return arr


def check_service_equipment_positions(
    room_dimensions_m: ArrayLike,
    corner_position_m: ArrayLike,
    room_positions_m: ArrayLike,
    *,
    source_positions_m: ArrayLike | None = None,
    small_room: bool = False,
) -> ServiceEquipmentPositionCheck:
    """Are the microphone positions far enough apart (ISO/DIS 16032:2023 7.2, 7.3)?

    The corner position is preferably 0,5 m from the two walls and the floor,
    raised to 1,0 m or 1,5 m where furniture is in the way. The reverberant-
    field positions keep at least 1,0 m from each other and from the corner
    (1,5 m preferred), 1,5 m from any sound source in the room, 0,50 m from
    every room surface (0,30 m in a small room where 0,50 m cannot be met) and
    a height from 0,5 m to 2,0 m. Pass the positions of one stage of 7.4.1 at
    a time: positions 4 and 5 keep the distances of 7.3 like 2 and 3.

    The verdict holds the corner position to its height of 0,5 m to 1,5 m and
    the reverberant-field positions to every distance and height of 7.3. The
    two preferences, 0,5 m from the walls of the corner and 1,5 m between
    positions, are reported beside it and do not decide it
    (:attr:`~ServiceEquipmentPositionCheck.preferred_corner_wall_distance`,
    :attr:`~ServiceEquipmentPositionCheck.preferred_separation`).

    The draft also asks 0,2 m between the corner microphone and any obstacle,
    which a room outline cannot show and this check does not judge.

    :param room_dimensions_m: Length, width and height of a rectangular room,
        in m.
    :param corner_position_m: Position 1 as ``(x, y, z)``, in m.
    :param room_positions_m: The reverberant-field positions, one ``(x, y, z)``
        per row, in m.
    :param source_positions_m: Sound sources in the room (outlets, radiators),
        one ``(x, y, z)`` per row, in m; ``None`` or an empty list for none.
    :param small_room: Whether the room is too small for 0,50 m from the
        surfaces, so 0,30 m applies.
    :return: :class:`ServiceEquipmentPositionCheck`.
    :raises ValueError: If a dimension is not positive, a coordinate is not a
        finite real number, no room position is given, a position lies
        outside the room, or ``small_room`` is not ``True`` or ``False``.
    """
    dims = _room(room_dimensions_m)
    if not isinstance(small_room, (bool, np.bool_)):
        # 'no' and 0.3 are truthy: read as flags they would each switch the
        # surface distance to the small-room 0,30 m.
        msg = f"'small_room' must be True or False, got {small_room!r}."
        raise ValueError(msg)
    corner = _points(corner_position_m, "corner_position_m")
    if corner.shape[0] != 1:
        msg = "'corner_position_m' must be one (x, y, z) position."
        raise ValueError(msg)
    rooms = _points(room_positions_m, "room_positions_m")
    if rooms.shape[0] == 0:
        msg = "'room_positions_m' must give at least one reverberant-field position."
        raise ValueError(msg)
    sources = (
        np.empty((0, 3))
        if source_positions_m is None
        else _points(source_positions_m, "source_positions_m")
    )
    for name, pts in (
        ("corner_position_m", corner),
        ("room_positions_m", rooms),
        ("source_positions_m", sources),
    ):
        if np.any(pts < 0.0) or np.any(pts > dims):
            msg = f"'{name}' has a position outside the room."
            raise ValueError(msg)

    everything = np.vstack((corner, rooms))
    gaps = np.linalg.norm(
        everything[:, np.newaxis, :] - everything[np.newaxis, :, :], axis=-1
    )
    separation = float(np.min(gaps[np.triu_indices(everything.shape[0], k=1)]))
    surface = float(np.min(np.minimum(rooms, dims - rooms)))
    source_distance = None
    if sources.shape[0] > 0:
        to_source = np.linalg.norm(
            rooms[:, np.newaxis, :] - sources[np.newaxis, :, :], axis=-1
        )
        source_distance = float(np.min(to_source))
    heights = rooms[:, 2].copy()
    c = corner[0]
    walls = np.minimum(c[:2], dims[:2] - c[:2])
    surface_limit = (
        _MIN_SURFACE_DISTANCE_SMALL_ROOM_M if small_room else _MIN_SURFACE_DISTANCE_M
    )
    slack = _LIMIT_SLACK
    return ServiceEquipmentPositionCheck(
        room_dimensions_m=dims.copy(),
        corner_position_m=c.copy(),
        room_positions_m=rooms.copy(),
        source_positions_m=sources.copy(),
        small_room=bool(small_room),
        separation_m=separation,
        surface_distance_m=surface,
        source_distance_m=source_distance,
        heights_m=heights,
        corner_height_m=float(c[2]),
        corner_wall_distances_m=(float(walls[0]), float(walls[1])),
        separation_ok=separation >= _MIN_SEPARATION_M - slack,
        surface_ok=surface >= surface_limit - slack,
        source_ok=source_distance is None
        or source_distance >= _MIN_SOURCE_DISTANCE_M - slack,
        height_ok=bool(
            np.all(
                (heights >= _MIN_HEIGHT_M - slack) & (heights <= _MAX_HEIGHT_M + slack)
            )
        ),
        corner_height_ok=(
            _CORNER_HEIGHT_RANGE_M[0] - slack
            <= float(c[2])
            <= _CORNER_HEIGHT_RANGE_M[1] + slack
        ),
    )


def additional_microphone_position(
    room_dimensions_m: ArrayLike,
    source_position_m: ArrayLike,
    *,
    mounting: _Mounting,
) -> np.ndarray:
    """The extra position for a sound source in the room (ISO/DIS 16032:2023 7.9).

    A source in the room itself, a ventilation outlet in a wall or in the
    ceiling for example, gets one additional microphone position of its own:
    1 m in front of a wall source at 1,5 m above the floor, or 1,5 m above the
    floor directly below a ceiling source. The reading there is reported
    separately, is neither standardized nor normalized, and is not averaged
    with positions 1, 2 and 3: pass it to :func:`service_equipment_level` on
    its own, without a reverberation time.

    Coordinates are those of :func:`check_service_equipment_positions`: a
    rectangular room with one corner at the origin, ``x`` along the length,
    ``y`` along the width and ``z`` the height above the floor. A wall source
    belongs to the wall it is nearest to, and the position is 1 m from the
    source along that wall's inward normal.

    :param room_dimensions_m: Length, width and height of the room, in m.
    :param source_position_m: The source as ``(x, y, z)``, in m.
    :param mounting: ``"wall"`` or ``"ceiling"``.
    :return: The position ``(x, y, z)``, in m.
    :raises ValueError: If a dimension is not positive, the source lies
        outside the room, or the position would.
    """
    require_choice(mounting, "mounting", _MOUNTINGS)
    dims = _room(room_dimensions_m)
    source = _points(source_position_m, "source_position_m")
    if source.shape[0] != 1:
        msg = "'source_position_m' must be one (x, y, z) position."
        raise ValueError(msg)
    s = source[0]
    if np.any(s < 0.0) or np.any(s > dims):
        msg = "'source_position_m' is outside the room."
        raise ValueError(msg)
    position = np.array([s[0], s[1], _ADDITIONAL_HEIGHT_M])
    if mounting == "wall":
        # The four walls as (axis, inward direction, distance from the source).
        walls = (
            (0, 1.0, s[0]),
            (0, -1.0, dims[0] - s[0]),
            (1, 1.0, s[1]),
            (1, -1.0, dims[1] - s[1]),
        )
        axis, direction, _ = min(walls, key=lambda wall: wall[2])
        position[axis] = s[axis] + direction * _ADDITIONAL_WALL_DISTANCE_M
    if np.any(position < 0.0) or np.any(position > dims):
        msg = (
            "The position 7.9 asks for falls outside the room: it needs 1.5 m of "
            "height and, for a wall source, 1 m of floor in front of the source."
        )
        raise ValueError(msg)
    return position
