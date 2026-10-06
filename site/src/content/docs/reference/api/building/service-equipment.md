---
title: "building.measurement.service_equipment"
description: "Sound from service equipment and activities in buildings, engineering method."
sidebar:
  label: "service_equipment"
---

Sound from service equipment and activities in buildings, engineering method.

This is the **engineering method** of ISO 16032 for the sound pressure level a
building's own equipment makes in a room: taps, showers, baths and water
closets, ventilation, heating and cooling, lifts, rubbish chutes, boilers and
pumps, car-park doors and, new in the revision, *activities*, the sources whose
operation nobody on site controls (a restaurant's coolers, amplified music next
door, a sports hall). It is the method a dispute over a noisy installation ends
in; the survey method for the same quantities is ISO 10052
([`survey_service_equipment_level`](/phonometry/reference/api/building/survey-insulation/#survey_service_equipment_level)).

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
[`check_position_spread`](/phonometry/reference/api/building/service-equipment/#check_position_spread)). Every reading enters the band average of
Formula (1), rounded to one decimal (7.5):

$$
L = 10 \lg \left[ \frac{1}{n} \sum_{i=1}^{n} 10^{0,1 L_i} \right] \ \mathrm{dB}
$$

A sound source in the room itself, a ventilation outlet for example, gets one
additional position of its own (7.9,
[`additional_microphone_position`](/phonometry/reference/api/building/service-equipment/#additional_microphone_position)), whose reading is reported separately,
never standardized and never averaged with the others.

**Background (Clause 9).** With the background band level $L_2$ and the
measured one $L_1$, the difference $\Delta L = L_1 - L_2$ decides:
at 10 dB or more nothing is corrected; from 4 dB to 10 dB the band is corrected
with Formulae (7) to (9),

$$
L = L_1 - K, \qquad K = -10 \lg \left[ 1 - 10^{-0,1 \Delta L} \right] \ \mathrm{dB}
$$

and below 4 dB the correction is held at the 2,2 dB that a 4 dB difference
gives, the band is reported as influenced by the background and the result is
an upper limit of the equipment level
([`service_equipment_background_correction`](/phonometry/reference/api/building/service-equipment/#service_equipment_background_correction)).

**Standardization and normalization (4.8, 7.7).** If a regulation asks for it,
the corrected bands are referred to a reference reverberation time
$T_0$ (0,5 s unless another value is specified) or to a reference
absorption area $A_0 = 10$ m², Formulae (5) and (6):

$$
L_\mathrm{nT} = L - 10 \lg \frac{T}{T_0}\ \mathrm{dB}, \qquad L_\mathrm{n} = L - 10 \lg \frac{A_0\,T}{0,16\,V}\ \mathrm{dB}
$$

Only the one-third-octave bands 50 Hz to 5 000 Hz (octave bands 63 Hz to
4 000 Hz) are standardized or normalized, because the reverberation time of the
bands outside cannot be measured reliably; those bands still enter the
weighted sums, unstandardized, and the report has to say so.

**Weighted values (4.3, 4.4, 7.8).** The A- and C-weighted single numbers are
energy sums of the corrected bands plus the Annex A corrections, rounded to
whole decibels. The A-weighted value uses either the restricted range 50 Hz to
5 000 Hz or the extended range 25 Hz to 10 000 Hz; the C-weighted value uses
the extended range. The single numbers are named as Table 1 names them, for
example $L_\mathrm{A,Smax,nT}$ or $L_\mathrm{C,eq}$. 4.2 also
admits "a specific frequency range" for the bands, and the form of Annex C has
a box for it, but 7.8 forms the weighted values over the two ranges above
only, and so does the library: a band set that does not cover the chosen
range is refused.

**Precision (Clause 10).** Table 2 gives the reproducibility standard deviation
of a room-average band level, 1,9 dB at the lowest bands down to 1,0 dB from
800 Hz up, and 0,8 dB and 1,2 dB for the A- and C-weighted values of a steady,
flat sound at least 10 dB above the background. A result carries them as
[`ServiceEquipmentResult.reproducibility_db`](/phonometry/reference/api/building/service-equipment/#serviceequipmentresult) and
[`ServiceEquipmentResult.weighted_reproducibility_db`](/phonometry/reference/api/building/service-equipment/#serviceequipmentresultweighted_reproducibility_db); the draft states no
coverage factor, so no expanded uncertainty is formed.

**On-site checks.** The draft also sets numbers the operator meets while
measuring, and each is a verdict here. The corner microphone keeps at least
0,2 m from any obstacle (7.2), judged from the distance measured on site by
[`check_service_equipment_positions`](/phonometry/reference/api/building/service-equipment/#check_service_equipment_positions). A calibration that deviates from
previous calibrations by more than 0,5 dB takes the equipment out of use
(Clause 5, [`verify_calibration_deviation`](/phonometry/reference/api/building/service-equipment/#verify_calibration_deviation)). The background is measured
over approximately 30 s (7.6, [`check_background_duration`](/phonometry/reference/api/building/service-equipment/#check_background_duration), which
reports each departure from 30 s and judges it against the tolerance the
operator names, because the draft prints none). Where
the background varies in time, its maximum watched for 10 min to 15 min at the
corner and 10 dB or more below the equipment lets the result stand without
correction (NOTE to Clause 9, [`check_varying_background`](/phonometry/reference/api/building/service-equipment/#check_varying_background)). A maximum
less than 5 dB above the equivalent level in the middle of the frequency range
says a period was not disturbed by doors or footsteps (Clause 9,
[`check_measurement_disturbance`](/phonometry/reference/api/building/service-equipment/#check_measurement_disturbance)), and calculated single numbers more
than 2 dB from the instrument's reading send the calculation back for a check
(NOTE to 7.8, [`check_instrument_agreement`](/phonometry/reference/api/building/service-equipment/#check_instrument_agreement)).

**Operating conditions (Annex B).** How each kind of equipment is to be run
while it is measured, and for how long the equivalent level is integrated, is
the data of [`SERVICE_EQUIPMENT_OPERATING_CONDITIONS`](/phonometry/reference/api/building/service-equipment/#service_equipment_operating_conditions), including the
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
apart), are registered in `docs/ERRATA.md`.

**No numeric oracle.** The draft prints no worked example. The conformance of
this module rests on closed forms and on the numbers the draft prints: the
2,2 dB of a 4 dB background difference, Table A.1, Table 2, and the limits of
the on-site checks met exactly and missed.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## additional_microphone_position

```python
additional_microphone_position(
    room_dimensions_m: ArrayLike,
    source_position_m: ArrayLike,
    *,
    mounting: _Mounting,
) -> np.ndarray
```

The extra position for a sound source in the room (ISO/DIS 16032:2023 7.9).

A source in the room itself, a ventilation outlet in a wall or in the
ceiling for example, gets one additional microphone position of its own:
1 m in front of a wall source at 1,5 m above the floor, or 1,5 m above the
floor directly below a ceiling source. The reading there is reported
separately, is neither standardized nor normalized, and is not averaged
with positions 1, 2 and 3: pass it to [`service_equipment_level`](/phonometry/reference/api/building/service-equipment/#service_equipment_level) on
its own, without a reverberation time.

Coordinates are those of [`check_service_equipment_positions`](/phonometry/reference/api/building/service-equipment/#check_service_equipment_positions): a
rectangular room with one corner at the origin, `x` along the length,
`y` along the width and `z` the height above the floor. A wall source
belongs to the wall it is nearest to, and the position is 1 m from the
source along that wall's inward normal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `room_dimensions_m` | Length, width and height of the room, in m. |
| `source_position_m` | The source as `(x, y, z)`, in m. |
| `mounting` | `"wall"` or `"ceiling"`. |

**Returns:** The position `(x, y, z)`, in m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a dimension is not positive, the source lies outside the room, or the position would. |

## BackgroundDurationCheck

```python
BackgroundDurationCheck(durations_s: np.ndarray, tolerance_s: float)
```

Whether each background was measured over approximately 30 s (7.6).

**Attributes**

| Name | Description |
| :--- | :--- |
| `durations_s` | The time over which each background equivalent level was measured, in s. |
| `tolerance_s` | The departure from 30 s, either way, that the operator accepts as "approximately", in s. The draft prints none. |

### BackgroundDurationCheck.departures_s

*property*

How far each duration departs from 30 s, in s.

**Returns:** The duration less 30 s, one per background measurement.

### BackgroundDurationCheck.largest_departure_s

*property*

The largest departure from 30 s, either way, in s.

**Returns:** The largest absolute value of `departures_s`.

### BackgroundDurationCheck.nominal_duration_s

*property*

The 30 s of 7.6, fixed by the draft.

**Returns:** The nominal background measurement time, in s.

### BackgroundDurationCheck.passes

*property*

Whether every background was measured over approximately 30 s.

"Approximately" is the operator's `tolerance_s`, not a number
of the draft.

**Returns:** `True` when no duration departs from 30 s by more than `tolerance_s`.

### BackgroundDurationCheck.plot()

```python
BackgroundDurationCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each duration against the 30 s of 7.6 and the tolerance accepted.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of the durations. |

**Returns:** The axes.

### BackgroundDurationCheck.within_tolerance

*property*

Per background, whether it departs from 30 s by no more than the tolerance.

A departure of exactly `tolerance_s` is within it.

**Returns:** One boolean per background measurement.

## CalibrationDeviationResult

```python
CalibrationDeviationResult(
    levels_db: np.ndarray,
    previous_levels_db: np.ndarray,
    deviations_db: np.ndarray,
)
```

Whether the instrumentation may be used, by its calibrations (Clause 5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `levels_db` | The calibrator readings of this measurement in the order they were taken, at the beginning and at the end, in dB. |
| `previous_levels_db` | The readings of earlier calibrations of the same instrumentation with the same calibrator, in dB; empty when none were given. |
| `deviations_db` | Per reading of `levels_db`, the largest absolute difference from every calibration taken before it, the earlier ones and the readings of this measurement already taken, in dB; `nan` for a first reading with nothing before it. |

### CalibrationDeviationResult.largest_deviation_db

*property*

The largest deviation of a reading from the calibrations before it.

**Returns:** The largest of `deviations_db`, in dB.

### CalibrationDeviationResult.limit_db

*property*

The 0,5 dB of Clause 5, fixed by the draft.

**Returns:** The largest deviation that still lets the equipment be used, in dB.

### CalibrationDeviationResult.passes

*property*

Whether no reading deviates from an earlier one by more than 0,5 dB.

**Returns:** `True` when the equipment may be used; `False` takes it out of use until the reason is clarified and the sensitivity put right (Clause 5).

### CalibrationDeviationResult.plot()

```python
CalibrationDeviationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each reading against the window the earlier calibrations leave it.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of this measurement's readings. |

**Returns:** The axes.

## check_background_duration

```python
check_background_duration(
    durations_s: ArrayLike,
    *,
    tolerance_s: float,
) -> BackgroundDurationCheck
```

Was the background measured over approximately 30 s (ISO/DIS 16032:2023 7.6)?

"The background sound pressure level shall be determined in frequency
bands as the equivalent continuous sound pressure levels over a period of
approximately 30 s just before or after each set of measurements. The same
microphone positions as used for the service equipment sound pressure
level measurements shall be used."

The draft writes approximately and prints no tolerance, so the library
sets none: the operator names the departure from 30 s, either way, that
their report accepts as approximate, and each duration is held to it. A
departure of exactly the tolerance is within it, and `tolerance_s=0`
holds every background to 30 s exactly. Each departure is reported
([`BackgroundDurationCheck.departures_s`](/phonometry/reference/api/building/service-equipment/#backgrounddurationcheckdepartures_s)) whatever the verdict.
Whether the background was taken just before or after each set, and at
the same positions, is not a number and is left to the operator.

**Parameters**

| Name | Description |
| :--- | :--- |
| `durations_s` | The measurement time of each background equivalent level, one per position or per set, in s. |
| `tolerance_s` | The departure from 30 s, either way, accepted as "approximately", in s. Required: the draft prints none. |

**Returns:** [`BackgroundDurationCheck`](/phonometry/reference/api/building/service-equipment/#backgrounddurationcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a duration is not a positive, finite number, or the tolerance is not one finite number of 0 s or more. |

## check_instrument_agreement

```python
check_instrument_agreement(
    result: ServiceEquipmentResult,
    instrument_levels_db: Mapping[str, ArrayLike],
) -> InstrumentAgreementCheck
```

Does the calculation agree with the instrument (NOTE to ISO/DIS 16032:2023 7.8)?

"It can be useful to compare the corrected and calculated A- and
C-weighted results with the values registered directly by the
instrument. If the difference is more than 2 dB, the calculations should
be checked for possible explanations." The NOTE is new in the revision.
The calculated value is the single number of the result as 7.8 rounds
it, and a difference of exactly 2 dB is not "more than 2 dB".

The instrument registers the level as measured, so a single number
corrected for the background, or standardized, may differ from it for
those reasons alone: the NOTE asks for an explanation, not a fault. Name
the single number each instrument value is compared with; `"LA,eq"`
against the A-weighted equivalent level the meter showed is the plain
case.

**Parameters**

| Name | Description |
| :--- | :--- |
| `result` | The [`ServiceEquipmentResult`](/phonometry/reference/api/building/service-equipment/#serviceequipmentresult) whose single numbers are compared. |
| `instrument_levels_db` | The instrument's value for each single number compared, keyed by its notation in `result.ratings` (`"LA,eq"`, `"LC,Fmax"`...), in dB: one value, or the reading at each position, which is energy-averaged by Formula (1). |

**Returns:** [`InstrumentAgreementCheck`](/phonometry/reference/api/building/service-equipment/#instrumentagreementcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | If `result` is not a [`ServiceEquipmentResult`](/phonometry/reference/api/building/service-equipment/#serviceequipmentresult). |
| ValueError | If `instrument_levels_db` is empty, names a single number the result does not carry, or holds a level that is not finite. |

## check_measurement_disturbance

```python
check_measurement_disturbance(
    maximum_levels_db: ArrayLike,
    equivalent_levels_db: ArrayLike,
) -> MeasurementDisturbanceCheck
```

Was a measurement period disturbed (ISO/DIS 16032:2023 Clause 9)?

"A simple check on-site is to compare the maximum level to the equivalent
level in the middle of the frequency range during each measurement
period, for many stable sources this difference should be less than 5 dB
to indicate that the measurement has not been disturbed by closing doors,
footfall noise etcetera." The check is the paragraph's, new in the
revision: it holds for many stable sources, not for a source whose own
level varies, and the draft does not name the band beyond "the middle of
the frequency range", which the operator chooses. A difference of exactly
5 dB is not "less than 5 dB" and marks the period.

**Parameters**

| Name | Description |
| :--- | :--- |
| `maximum_levels_db` | The maximum level of a band in the middle of the frequency range, one per measurement period, in dB. |
| `equivalent_levels_db` | The equivalent level of the same band over the same period, one per period, in dB. |

**Returns:** [`MeasurementDisturbanceCheck`](/phonometry/reference/api/building/service-equipment/#measurementdisturbancecheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite or the two counts differ. |

## check_position_spread

```python
check_position_spread(levels_db: ArrayLike) -> PositionSpreadCheck
```

Are the positions measured so far enough (ISO/DIS 16032:2023 7.4.1)?

The A-weighted levels read directly from the instrument, without any
correction, decide how many positions are measured. With three readings
(corner, 2, 3) a spread up to and including 3,0 dB lets the corrections
proceed; otherwise the corner is measured again with two new room
positions (4 and 5), and the six must differ by less than 6,0 dB, then
once more (corner, 6 and 7) and the nine by less than 9,0 dB. 7.4.2
applies the same steps to a maximum level, with the sound exposure level
$L_\mathrm{AE}$ allowed in its place for short events.

The draft interrupts the session when the difference "is larger than
9,0 dB and is related to unpredictable time domain variations whereas the
readings in the corner position confirm the sound source is stable": the
reasons are investigated before a new series, and no reading of the
interrupted one is used. Levels alone cannot say what a difference is
related to, so the check answers `"interrupt"` whenever no further stage
can pass and leaves those two conditions to the operator: a spread still
9,0 dB or more after nine readings, and a spread that already reaches
9,0 dB after three or six, since more readings can only widen it. The
third paragraph of 7.4.1 sends to positions 6 and 7 only a difference
"less than 9,0 dB".

The draft states no rule at a spread of exactly 6,0 dB after six readings
or 9,0 dB after nine, nor for three readings 6,0 dB or more apart. The
ladder is read as a sequence: a stage that does not pass goes to the next
while a later one can still pass, and a spread at a limit does not pass it
(`docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The 3, 6 or 9 A-weighted levels in the order of 7.4.1: `[corner, 2, 3]`, then `[corner, 4, 5]` and `[corner, 6, 7]` appended, in dB. |

**Returns:** [`PositionSpreadCheck`](/phonometry/reference/api/building/service-equipment/#positionspreadcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If there are not 3, 6 or 9 finite levels. |

## check_service_equipment_positions

```python
check_service_equipment_positions(
    room_dimensions_m: ArrayLike,
    corner_position_m: ArrayLike,
    room_positions_m: ArrayLike,
    *,
    source_positions_m: ArrayLike | None = None,
    small_room: bool = False,
    corner_obstacle_distance_m: ArrayLike | None = None,
) -> ServiceEquipmentPositionCheck
```

Are the microphone positions far enough apart (ISO/DIS 16032:2023 7.2, 7.3)?

The corner position is preferably 0,5 m from the two walls and the floor,
raised to 1,0 m or 1,5 m where furniture is in the way, and at least
0,2 m from any obstacle. The reverberant-field positions keep at least
1,0 m from each other and from the corner (1,5 m preferred), 1,5 m from
any sound source in the room, 0,50 m from every room surface (0,30 m in a
small room where 0,50 m cannot be met) and a height from 0,5 m to 2,0 m.
Pass the positions of one stage of 7.4.1 at a time: positions 4 and 5
keep the distances of 7.3 like 2 and 3.

The verdict holds the corner position to its height of 0,5 m to 1,5 m and
the reverberant-field positions to every distance and height of 7.3. The
two preferences, 0,5 m from the walls of the corner and 1,5 m between
positions, are reported beside it and do not decide it
([`preferred_corner_wall_distance`](/phonometry/reference/api/building/service-equipment/#serviceequipmentpositioncheckpreferred_corner_wall_distance),
[`preferred_separation`](/phonometry/reference/api/building/service-equipment/#serviceequipmentpositioncheckpreferred_separation)).

A room outline cannot show furniture, so the 0,2 m that 7.2 asks between
the corner microphone and any obstacle is judged from the distance
measured on site, when it is given: "The microphone position shall be at
least 0,2 m away from any obstacle", inclusive. The draft states it in the
clause on the corner position and nowhere for the reverberant-field
positions, whose 0,50 m from the room surfaces 7.3 sets instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `room_dimensions_m` | Length, width and height of a rectangular room, in m. |
| `corner_position_m` | Position 1 as `(x, y, z)`, in m. |
| `room_positions_m` | The reverberant-field positions, one `(x, y, z)` per row, in m. |
| `source_positions_m` | Sound sources in the room (outlets, radiators), one `(x, y, z)` per row, in m; `None` or an empty list for none. |
| `small_room` | Whether the room is too small for 0,50 m from the surfaces, so 0,30 m applies. |
| `corner_obstacle_distance_m` | The distance from the corner microphone to the nearest obstacle, or one distance per obstacle near it, in m, measured on site; `None` (default) leaves the 0,2 m of 7.2 unjudged. |

**Returns:** [`ServiceEquipmentPositionCheck`](/phonometry/reference/api/building/service-equipment/#serviceequipmentpositioncheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a dimension is not positive, a coordinate is not a finite real number, no room position is given, a position lies outside the room, `small_room` is not `True` or `False`, or an obstacle distance is not a finite distance of 0 m or more. |

## check_varying_background

```python
check_varying_background(
    background_maximum_db: ArrayLike,
    equipment_levels_db: ArrayLike,
    *,
    observation_time_s: float,
    frequencies_hz: ArrayLike | None = None,
) -> VaryingBackgroundCheck
```

Can the result stand without correction (NOTE to ISO/DIS 16032:2023 Clause 9)?

Clause 9 corrects the bands for a background roughly constant in time,
and its NOTE says that for a background varying in time, road traffic for
example, "a reliable correction cannot be made. However, the maximum sound
pressure levels of the background noise could be determined over a period
of 10 min to 15 min in the corner microphone position. If the maximum
level is 10 dB or more below the service equipment sound pressure level
the result can be regarded valid without correction." The NOTE also
suggests checking "the validity in all relevant octave-bands", words kept
from the 2004 edition, which measured in octaves: the margin is judged in
every band given, one-third octaves or octaves, and a single weighted
value is one band.

Both ends of the 10 min to 15 min are included, and so is a margin of
exactly 10 dB ("10 dB or more"). The 2004 edition took the maximum "in one
of the microphone positions"; the draft names the corner.

**Parameters**

| Name | Description |
| :--- | :--- |
| `background_maximum_db` | The maximum level of the background over the observation period, at the corner position, per band, in dB. |
| `equipment_levels_db` | The service equipment sound pressure level in the same bands, in dB. |
| `observation_time_s` | How long the background maximum was watched for, in s. |
| `frequencies_hz` | Band centres in Hz, kept for the plot only. |

**Returns:** [`VaryingBackgroundCheck`](/phonometry/reference/api/building/service-equipment/#varyingbackgroundcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite, the shapes differ, or the observation time is not one positive number. |

## InstrumentAgreementCheck

```python
InstrumentAgreementCheck(
    calculated_db: Mapping[str, float],
    instrument_db: Mapping[str, float],
)
```

Whether the calculated single numbers agree with the instrument (7.8).

**Attributes**

| Name | Description |
| :--- | :--- |
| `calculated_db` | The single numbers of the result compared, as 7.8 rounds them, keyed by their Table 1 notation (`"LA,eq"`...), in dB. |
| `instrument_db` | The value the instrument registered for each, in dB; the energy average when several readings were given. |

### InstrumentAgreementCheck.differences_db

*property*

The calculated value less the instrument's, per single number, in dB.

**Returns:** Keyed like `calculated_db`.

### InstrumentAgreementCheck.disagreeing

*property*

The single numbers more than 2 dB from the instrument.

**Returns:** Their notations, in the order of `calculated_db`.

### InstrumentAgreementCheck.limit_db

*property*

The 2 dB of the NOTE to 7.8, fixed by the draft.

**Returns:** The largest difference, either way, that agrees, in dB.

### InstrumentAgreementCheck.passes

*property*

Whether every calculated value is within 2 dB of the instrument.

**Returns:** `True` when no single number calls for a second look at the calculation.

### InstrumentAgreementCheck.plot()

```python
InstrumentAgreementCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each calculated-less-instrument difference against 2 dB.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of the differences. |

**Returns:** The axes.

## loudest_corner

```python
loudest_corner(
    c_weighted_levels_db: ArrayLike,
    *,
    excluded: Sequence[int] = (),
) -> int
```

The corner that becomes microphone position 1 (ISO/DIS 16032:2023 7.2).

Position 1 is the corner with the highest C-weighted level, measured
directly (a hand-held integrating meter will do: no band calculation, no
reverberation or background correction) as the maximum level with time
weighting S or F or as the equivalent level, under the chosen operating
conditions or any steady condition that finds the loudest corner. A corner
whose level is dominated by direct sound from a source in the room, a
ventilation outlet for example, is left out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `c_weighted_levels_db` | One C-weighted level per corner, in dB. |
| `excluded` | Indices of the corners dominated by direct sound, counted from 0 in the order of `c_weighted_levels_db`. |

**Returns:** The index of the loudest corner left, counted from 0; the first of a tie.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite, `excluded` is not a sequence of whole numbers, an index is out of range, or every corner is excluded. |

## MeasurementDisturbanceCheck

```python
MeasurementDisturbanceCheck(
    maximum_levels_db: np.ndarray,
    equivalent_levels_db: np.ndarray,
)
```

Whether each measurement period was free of disturbances (Clause 9).

**Attributes**

| Name | Description |
| :--- | :--- |
| `maximum_levels_db` | The maximum level in the middle of the frequency range, one per measurement period, in dB. |
| `equivalent_levels_db` | The equivalent level in the same band, one per period, in dB. |

### MeasurementDisturbanceCheck.differences_db

*property*

The maximum less the equivalent level of each period, in dB.

**Returns:** One difference per measurement period.

### MeasurementDisturbanceCheck.disturbed_periods

*property*

The periods whose difference reaches 5 dB, counted from 0.

**Returns:** Their indices, in the order given.

### MeasurementDisturbanceCheck.limit_db

*property*

The 5 dB of Clause 9, fixed by the draft.

**Returns:** The difference a period must stay under, in dB.

### MeasurementDisturbanceCheck.passes

*property*

Whether no period shows a disturbance.

**Returns:** `True` when every period's maximum lies less than 5 dB above its equivalent level.

### MeasurementDisturbanceCheck.plot()

```python
MeasurementDisturbanceCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each period's maximum-to-equivalent difference against 5 dB.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of the differences. |

**Returns:** The axes.

### MeasurementDisturbanceCheck.undisturbed

*property*

Per period, whether the difference is less than 5 dB.

A difference of exactly 5,0 dB is not "less than 5 dB".

**Returns:** One boolean per measurement period.

## OperatingCondition

```python
OperatingCondition(
    clause: str,
    equipment: str,
    maximum_level: bool,
    equivalent_level: bool,
    conditions: str,
    maximum_cycle: str | None,
    equivalent_cycle: str | None,
    nominal_integration_time_s: float | None,
    parameters: Mapping[str, float] = ...,
)
```

How one kind of equipment is run while it is measured (Annex B).

Annex B is normative, but B.1.1 lets national requirements and regulations
override it, and equipment it does not list is measured by the principles
of the document with the chosen conditions reported in detail.

**Attributes**

| Name | Description |
| :--- | :--- |
| `clause` | The clause of Annex B, e.g. `"B.2.6"`. |
| `equipment` | What the entry covers, in words. |
| `maximum_level` | Whether the entry defines a cycle for the maximum level `Lmax`. |
| `equivalent_level` | Whether the entry defines the equivalent level `Leq`; a rubbish chute is measured as a maximum level only. |
| `conditions` | The operating conditions, in words. |
| `maximum_cycle` | The operating cycle for `Lmax`, or `None`. |
| `equivalent_cycle` | What the `Leq` integration time covers, or `None`. |
| `nominal_integration_time_s` | The integration time the entry gives in seconds when it is a fixed duration (about 30 s), or `None` when it is the length of a cycle. |
| `parameters` | The other numbers the entry prints, keyed by a name that carries the unit (`"tube_length_m"`) or says it is a count. |

## PositionSpreadCheck

```python
PositionSpreadCheck(
    levels_db: np.ndarray,
    stage: int,
    spread_db: float,
    limit_db: float,
    action: Literal['proceed', 'add_positions', 'interrupt'],
    next_positions: tuple[int, ...],
    corner_standard_deviation_db: float | None,
)
```

Whether the readings so far are enough to average (7.4.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `levels_db` | The A-weighted levels read directly from the instrument, uncorrected, in the order of 7.4.1: corner, position 2, position 3, then (corner, 4, 5) and (corner, 6, 7) for each further stage, in dB. |
| `stage` | 1, 2 or 3: how many sets of three readings there are. |
| `spread_db` | The difference between the highest and lowest reading, in dB. |
| `limit_db` | The spread this stage allows: 3,0 dB (inclusive), 6,0 dB or 9,0 dB (strict). |
| `action` | `"proceed"` to the corrections of 7.5 to 7.7, `"add_positions"` for the corner again and two new room positions, or `"interrupt"` when no further stage can pass: after nine readings, or sooner when the spread already reaches 9,0 dB. |
| `next_positions` | The room positions to add, `(4, 5)` or `(6, 7)`, or `()`. |
| `corner_standard_deviation_db` | Sample standard deviation of the corner readings, in dB, which 7.4.1 takes as representative of the room average when a statistical value (a 5 % value, the n-th highest) is wanted; `None` with a single corner reading. |

### PositionSpreadCheck.passes

*property*

Whether the readings may be averaged as they are.

**Returns:** `True` when `action` is `"proceed"`.

### PositionSpreadCheck.plot()

```python
PositionSpreadCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the readings against the spread the stage allows.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of the room positions. |

**Returns:** The axes.

## service_equipment_background_correction

```python
service_equipment_background_correction(
    levels_db: ArrayLike,
    background_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike | None = None,
) -> ServiceEquipmentBackgroundResult
```

Correct band levels for the background (ISO/DIS 16032:2023 Clause 9).

With $\Delta L = L_1 - L_2$ the band is left as it is at 10 dB or
more, corrected with $K = -10 \lg(1 - 10^{-0,1 \Delta L})$ from 4 dB
to 10 dB (Formulae (7) to (9)), and below 4 dB the correction is held at
2,2 dB, the value a 4 dB difference gives. Such a band is influenced by the
background, which the report has to state, and for a comparison with a
limit the result is an upper limit of the equipment level. A background at
or above the measured level is the same case: held at 2,2 dB rather than
left undefined.

The method assumes a background roughly constant in time. Where it is not,
the NOTE to Clause 9 suggests the maximum level of the background over 10
to 15 minutes at the corner position instead: if it is 10 dB or more below
the equipment, the result stands without correction
([`check_varying_background`](/phonometry/reference/api/building/service-equipment/#check_varying_background)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | Measured band levels $L_1$, background included, in dB. |
| `background_db` | Background band levels $L_2$, in dB, the same shape. |
| `frequencies_hz` | Band centres in Hz, kept for the plot only. |

**Returns:** [`ServiceEquipmentBackgroundResult`](/phonometry/reference/api/building/service-equipment/#serviceequipmentbackgroundresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite or the shapes differ. |

## service_equipment_level

```python
service_equipment_level(
    levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    quantity: _Quantity,
    band: _Band = 'third',
    background_db: ArrayLike | None = None,
    reverberation_time_s: ArrayLike | None = None,
    volume_m3: float | None = None,
    reference_reverberation_time_s: float = 0.5,
    a_weighting_range: _Range = 'restricted',
) -> ServiceEquipmentResult
```

Sound pressure level of service equipment in a room (ISO/DIS 16032:2023).

The chain of Clauses 6 and 7: the band levels of every reading are
energy-averaged by Formula (1) and rounded to one decimal (7.5), corrected
for the background by Clause 9, standardized by Formula (5) or normalized
by Formula (6) where a reverberation time is given (7.7, 50 Hz to 5 000 Hz
only), and summed into the A- and C-weighted single numbers of Table 1 with
the Annex A corrections, rounded to whole decibels (7.8).

The readings are the linear band spectra of the measurements of 7.4:
positions 1, 2 and 3 at least, with the corner reading repeated in each
further stage that [`check_position_spread`](/phonometry/reference/api/building/service-equipment/#check_position_spread) asks for. Take them at the
instant the A- or C-weighted level peaks for a maximum level (Clause 6), or
over the integration time of Annex B for an equivalent level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | Band levels of each reading, shape `(readings, bands)` (one-dimensional for a single reading), in dB. |
| `frequencies_hz` | Nominal band centres, in Hz, increasing: the one-third-octave bands of 25 Hz to 10 000 Hz or the octave bands of 31,5 Hz to 8 000 Hz, as `band` says. |
| `quantity` | The Table 1 quantity measured: `"Smax"`, `"Fmax"` or `"eq"`. It names the single numbers and nothing else. |
| `band` | `"third"` (default) or `"octave"`. 6 asks for the weighted values from one-third-octave bands; octave results are optional. |
| `background_db` | Background band levels, in dB, one per band or one row per microphone position (energy-averaged over the positions, as the 2004 edition says in so many words and the draft leaves implicit). |
| `reverberation_time_s` | Reverberation time of each band, in s, measured by ISO 3382-2 (Clause 8). Only the bands of the standardization range are read; the others may be `nan`. |
| `volume_m3` | Room volume, in m³, for the normalized levels. |
| `reference_reverberation_time_s` | $T_0$ of Formula (5), in s (0,5 s unless a regulation specifies another value). |
| `a_weighting_range` | `"restricted"` (default: 50 Hz to 5 000 Hz, octave 63 Hz to 4 000 Hz) or `"extended"` (25 Hz to 10 000 Hz, octave 31,5 Hz to 8 000 Hz) for the A-weighted values; the report must say which. The C-weighted values always use the extended range. |

**Returns:** [`ServiceEquipmentResult`](/phonometry/reference/api/building/service-equipment/#serviceequipmentresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a centre is not a nominal band, the bands do not cover the A-weighting range, the shapes disagree, a level is not a finite real number, a reverberation time in the standardization range is not positive, `volume_m3` or `reference_reverberation_time_s` is not one positive number, or `volume_m3` is given without a reverberation time. |

## SERVICE_EQUIPMENT_OPERATING_CONDITIONS

*Constant* (`mapping`).

## SERVICE_EQUIPMENT_REPRODUCIBILITY

*Constant* (`mapping`).

```python
SERVICE_EQUIPMENT_REPRODUCIBILITY = {'third': {25.0: 1.9, 31.5: 1.9, 40.0: 1.9, 50.0: 1.9, 63.0: 1.9, 80.0: 1.9, 100.0: 1.9, 125.0: 1.9, 160.0: 1.9, 200.0: 1.5, 250.0: 1.5, 315.0: 1.5, 400.0: 1.2, 500.0: 1.2, 630.0: 1.2, 800.0: 1.0, 1000.0: 1.0, 1250.0: 1.0, 1600.0: 1.0, 2000.0: 1.0, 2500.0: 1.0, 3150.0: 1.0, 4000.0: 1.0, 5000.0: 1.0, 6300.0: 1.0, 8000.0: 1.0, 10000.0: 1.0}, 'octave': {31.5: 1.9, 63.0: 1.9, 125.0: 1.9, 250.0: 1.5, 500.0: 1.2, 1000.0: 1.0, 2000.0: 1.0, 4000.0: 1.0, 8000.0: 1.0}}
```

## SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY

*Constant* (`mapping`).

```python
SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY = {'A': 0.8, 'C': 1.2}
```

## SERVICE_EQUIPMENT_WEIGHTING

*Constant* (`mapping`).

```python
SERVICE_EQUIPMENT_WEIGHTING = {'third': {'A': {25.0: -44.7, 31.5: -39.4, 40.0: -34.6, 50.0: -30.2, 63.0: -26.2, 80.0: -22.5, 100.0: -19.1, 125.0: -16.1, 160.0: -13.4, 200.0: -10.9, 250.0: -8.6, 315.0: -6.6, 400.0: -4.8, 500.0: -3.2, 630.0: -1.9, 800.0: -0.8, 1000.0: 0.0, 1250.0: 0.6, 1600.0: 1.0, 2000.0: 1.2, 2500.0: 1.3, 3150.0: 1.2, 4000.0: 1.0, 5000.0: 0.5, 6300.0: -0.1, 8000.0: -1.1, 10000.0: -2.5}, 'C': {25.0: -4.4, 31.5: -3.0, 40.0: -2.0, 50.0: -1.3, 63.0: -0.8, 80.0: -0.5, 100.0: -0.3, 125.0: -0.2, 160.0: -0.1, 200.0: 0.0, 250.0: 0.0, 315.0: 0.0, 400.0: 0.0, 500.0: 0.0, 630.0: 0.0, 800.0: 0.0, 1000.0: 0.0, 1250.0: 0.0, 1600.0: -0.1, 2000.0: -0.2, 2500.0: -0.3, 3150.0: -0.5, 4000.0: -0.8, 5000.0: -1.3, 6300.0: -2.0, 8000.0: -3.0, 10000.0: -4.4}}, 'octave': {'A': {31.5: -39.4, 63.0: -26.2, 125.0: -16.1, 250.0: -8.6, 500.0: -3.2, 1000.0: 0.0, 2000.0: 1.2, 4000.0: 1.0, 8000.0: -1.1}, 'C': {31.5: -3.0, 63.0: -0.8, 125.0: -0.2, 250.0: 0.0, 500.0: 0.0, 1000.0: 0.0, 2000.0: -0.2, 4000.0: -0.8, 8000.0: -3.0}}}
```

## ServiceEquipmentBackgroundResult

```python
ServiceEquipmentBackgroundResult(
    measured_db: np.ndarray,
    background_db: np.ndarray,
    difference_db: np.ndarray,
    correction_db: np.ndarray,
    corrected_db: np.ndarray,
    regime: tuple[str, ...],
    frequencies_hz: np.ndarray | None = None,
)
```

Band levels corrected for the background by Clause 9.

**Attributes**

| Name | Description |
| :--- | :--- |
| `measured_db` | The measured band levels $L_1$, background included, in dB. |
| `background_db` | The background band levels $L_2$, in dB. |
| `difference_db` | $\Delta L = L_1 - L_2$ per band, in dB (Formula (9)). |
| `correction_db` | The correction $K$ per band, in dB: 0 at 10 dB or more, Formula (8) from 4 dB, and 2,2 dB below 4 dB. |
| `corrected_db` | $L = L_1 - K$ per band, in dB (Formula (7)). |
| `regime` | Per band, `"none"` (no correction), `"corrected"` (Formula (8)) or `"limited"` (held at 2,2 dB: the band is an upper limit of the equipment level). |
| `frequencies_hz` | The band centres, in Hz, or `None` when not given. |

### ServiceEquipmentBackgroundResult.influenced

*property*

Whether any band is influenced by the background (Clause 9).

**Returns:** `True` when at least one band was held at 2,2 dB, which the report has to state.

### ServiceEquipmentBackgroundResult.limited

*property*

Per band, whether the background held the correction at 2,2 dB.

**Returns:** One boolean per band; `True` marks an upper limit.

### ServiceEquipmentBackgroundResult.plot()

```python
ServiceEquipmentBackgroundResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot measured, background and corrected band levels.

Bands held at 2,2 dB are marked as upper limits. Requires matplotlib
(`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the corrected-level curve. |

**Returns:** The axes.

## ServiceEquipmentPositionCheck

```python
ServiceEquipmentPositionCheck(
    room_dimensions_m: np.ndarray,
    corner_position_m: np.ndarray,
    room_positions_m: np.ndarray,
    source_positions_m: np.ndarray,
    small_room: bool,
    separation_m: float,
    surface_distance_m: float,
    source_distance_m: float | None,
    heights_m: np.ndarray,
    corner_height_m: float,
    corner_wall_distances_m: tuple[float, float],
    separation_ok: bool,
    surface_ok: bool,
    source_ok: bool,
    height_ok: bool,
    corner_height_ok: bool,
    corner_obstacle_distance_m: float | None = None,
    corner_obstacle_ok: bool | None = None,
)
```

Whether the positions keep the corner height of 7.2 and the distances of 7.3.

Positions are coordinates in metres in a rectangular room with one corner
at the origin: `x` along the length, `y` along the width and `z` the
height above the floor.

**Attributes**

| Name | Description |
| :--- | :--- |
| `room_dimensions_m` | Length, width and height of the room, in m. |
| `corner_position_m` | Position 1, in m. |
| `room_positions_m` | The reverberant-field positions, shape `(k, 3)`, in m. |
| `source_positions_m` | Sound sources in the room, shape `(m, 3)`, in m (empty when none were given). |
| `small_room` | Whether the small-room surface distance of 7.3 applies. |
| `separation_m` | The shortest distance between any two positions, corner included, in m. |
| `surface_distance_m` | The shortest distance from a room position to a wall, the floor or the ceiling, in m. |
| `source_distance_m` | The shortest distance from a room position to a source, in m, or `None` without sources. |
| `heights_m` | The heights of the room positions, in m. |
| `corner_height_m` | The height of the corner position, in m. |
| `corner_wall_distances_m` | The corner position's distances to the two walls nearest to it, in m; 7.2 prefers 0,5 m (`preferred_corner_wall_distance`, advisory). |
| `separation_ok` | At least 1,0 m between positions. |
| `surface_ok` | At least 0,50 m (0,30 m in a small room) from every surface. |
| `source_ok` | At least 1,5 m from every source. |
| `height_ok` | Every room position from 0,5 m to 2,0 m high. |
| `corner_height_ok` | The corner position from 0,5 m to 1,5 m high. |
| `corner_obstacle_distance_m` | The distance from the corner microphone to the nearest obstacle, as measured on site, in m; `None` when it was not given. |
| `corner_obstacle_ok` | At least 0,2 m from any obstacle (7.2); `None` when the distance was not given, and then not judged. |

### ServiceEquipmentPositionCheck.passes

*property*

Whether the distances and heights of 7.3 and the corner of 7.2 hold.

The corner position enters through its height and, when its distance
to the nearest obstacle was given, through the 0,2 m that 7.2 asks of
it. The 0,5 m from its walls is a preference
(`preferred_corner_wall_distance`), like the 1,5 m between
positions (`preferred_separation`).

**Returns:** `True` when the five requirements hold, and the sixth, the obstacle distance, holds or was not given.

### ServiceEquipmentPositionCheck.plot()

```python
ServiceEquipmentPositionCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the room in plan with the positions and their clearances.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the markers of the room positions. |

**Returns:** The axes.

### ServiceEquipmentPositionCheck.preferred_corner_wall_distance

*property*

Whether position 1 is 0,5 m from both walls of its corner, as 7.2 prefers.

7.2 places the corner microphone "preferably" 0,5 m from the walls and
the floor, and where furniture is in the way raises only its height,
which `corner_height_ok` judges. The draft gives the wall
distance no tolerance and no lower or upper bound, so a corner position
elsewhere is a departure the operator reports rather than a failure.

**Returns:** `True` when both `corner_wall_distances_m` are 0,5 m; advisory, not part of `passes`.

### ServiceEquipmentPositionCheck.preferred_separation

*property*

Whether the positions are 1,5 m apart, the distance 7.3 prefers.

**Returns:** `True` at 1,5 m or more; advisory, not part of `passes`.

### ServiceEquipmentPositionCheck.source_limit_m

*property*

The distance 7.3 asks between a room position and a source, in m.

**Returns:** 1,5 m.

### ServiceEquipmentPositionCheck.surface_limit_m

*property*

The surface distance 7.3 asks of this room, in m.

**Returns:** 0,30 m in a small room, 0,50 m otherwise.

## ServiceEquipmentResult

```python
ServiceEquipmentResult(
    frequencies_hz: np.ndarray,
    band: str,
    quantity: str,
    a_weighting_range: str,
    readings_db: np.ndarray,
    average_db: np.ndarray,
    background: ServiceEquipmentBackgroundResult | None,
    corrected_db: np.ndarray,
    standardizable: np.ndarray,
    standardized_db: np.ndarray | None,
    normalized_db: np.ndarray | None,
    ratings: Mapping[str, int],
    unrounded_ratings: Mapping[str, float],
    reproducibility_db: np.ndarray,
)
```

Service-equipment sound pressure level, engineering method.

Produced by [`service_equipment_level`](/phonometry/reference/api/building/service-equipment/#service_equipment_level). Every band array runs over
`frequencies_hz`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal band centres, in Hz. |
| `band` | `"third"` or `"octave"`. |
| `quantity` | The Table 1 quantity: `"Smax"`, `"Fmax"` or `"eq"`. |
| `a_weighting_range` | `"restricted"` (50 Hz to 5 000 Hz; octave 63 Hz to 4 000 Hz) or `"extended"` (25 Hz to 10 000 Hz; octave 31,5 Hz to 8 000 Hz), the range the A-weighted values were summed over. |
| `readings_db` | The band levels of every reading, shape `(readings, bands)`, in dB. |
| `average_db` | Formula (1) over the readings, rounded to one decimal (7.5), in dB. |
| `background` | The Clause 9 correction, or `None` when no background was given. |
| `corrected_db` | The average corrected for the background, in dB (the average itself when there is no background). |
| `standardizable` | Per band, whether 7.7 lets it be standardized or normalized (50 Hz to 5 000 Hz; octave 63 Hz to 4 000 Hz). |
| `standardized_db` | $L_\mathrm{nT}$ per band (Formula (5)), in dB, or `None` without a reverberation time. Bands outside the range are the corrected level, unstandardized. |
| `normalized_db` | $L_\mathrm{n}$ per band (Formula (6)), in dB, or `None` without a reverberation time and a volume. |
| `ratings` | The weighted single numbers of Table 1, rounded to whole decibels (7.8), keyed by their notation: `"LA,eq"`, `"LA,Smax,nT"`, `"LC,Fmax,n"` and so on. The C-weighted ones are present only when the bands cover the extended range. |
| `unrounded_ratings` | The same single numbers before rounding, in dB. |
| `reproducibility_db` | The Table 2 standard deviation of each band, in dB. |

### ServiceEquipmentResult.plot()

```python
ServiceEquipmentResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band spectrum through each step of the method.

The average, the background, the corrected level and, when formed, the
standardized one, with the bands the background limits marked and the
A-weighted single numbers in the title. Requires matplotlib
(`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of the final band levels. |

**Returns:** The axes.

### ServiceEquipmentResult.reading_count

*property*

The number of readings averaged by Formula (1).

**Returns:** The number of rows of `readings_db`.

### ServiceEquipmentResult.unstandardized_bands_hz

*property*

The bands that enter the weighted values without standardization.

7.7 keeps 25, 31,5, 40, 6 300, 8 000 and 10 000 Hz (octaves 31,5 Hz and
8 000 Hz) out of the standardization and normalization, and asks the
report to mention them whenever they contribute to a weighted value.

**Returns:** The centres, in Hz, of the bands inside a weighted range that were left unstandardized; empty when nothing was standardized.

### ServiceEquipmentResult.upper_limit()

```python
ServiceEquipmentResult.upper_limit(weighting: str) -> bool
```

Whether a weighted value is an upper limit because of the background.

A band the background held at 2,2 dB (Clause 9) that lies in the range
of the weighted sum makes that sum an upper limit, and Clause 9 asks the
report to say whether the A- and the C-weighted value are influenced.

**Parameters**

| Name | Description |
| :--- | :--- |
| `weighting` | `"A"` or `"C"`. |

**Returns:** `True` when a band of the range was held at 2,2 dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a weighting other than A or C. |

### ServiceEquipmentResult.weighted_reproducibility_db

*property*

The Table 2 standard deviation of each single number, in dB.

0,8 dB for every A-weighted value of `ratings` and 1,2 dB for
every C-weighted one. Footnote a of Table 2 limits both to a constant
sound with a relatively flat spectrum from 25 Hz to 10 000 Hz, at least
10 dB above the background; a fluctuating source, a maximum level most
of all, is more uncertain, and the draft states no coverage factor.

**Returns:** The reproducibility standard deviation keyed like `ratings` (`"LA,eq"`, `"LC,Fmax,nT"`...).

## VaryingBackgroundCheck

```python
VaryingBackgroundCheck(
    background_maximum_db: np.ndarray,
    equipment_levels_db: np.ndarray,
    observation_time_s: float,
    frequencies_hz: np.ndarray | None = None,
)
```

Whether a result stands without correction for a varying background.

The route the NOTE to Clause 9 offers when the background varies in time.

**Attributes**

| Name | Description |
| :--- | :--- |
| `background_maximum_db` | The maximum level of the background over the observation period at the corner position, per band (or one weighted value), in dB. |
| `equipment_levels_db` | The service equipment sound pressure level, the same bands, in dB. |
| `observation_time_s` | How long the background maximum was watched for, in s. |
| `frequencies_hz` | The band centres, in Hz, or `None` when not given. |

### VaryingBackgroundCheck.limit_db

*property*

The 10 dB of the NOTE to Clause 9, fixed by the draft.

**Returns:** How far below the equipment the background maximum must lie, at least, in dB.

### VaryingBackgroundCheck.margin_db

*property*

How far the background maximum lies below the equipment, per band.

**Returns:** The equipment level less the background maximum, in dB.

### VaryingBackgroundCheck.margin_ok

*property*

Per band, whether the background maximum is 10 dB or more below.

**Returns:** One boolean per band.

### VaryingBackgroundCheck.observation_ok

*property*

Whether the background maximum was watched for 10 min to 15 min.

**Returns:** `True` from 600 s to 900 s, both included.

### VaryingBackgroundCheck.passes

*property*

Whether the result can be regarded valid without correction.

**Returns:** `True` when the background maximum, watched for 10 min to 15 min, lies 10 dB or more below the equipment in every band.

### VaryingBackgroundCheck.plot()

```python
VaryingBackgroundCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the equipment level against the background maximum, per band.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of the equipment level. |

**Returns:** The axes.

## verify_calibration_deviation

```python
verify_calibration_deviation(
    calibration_levels_db: ArrayLike,
    *,
    previous_levels_db: ArrayLike | None = None,
) -> CalibrationDeviationResult
```

Has the sensitivity moved more than 0,5 dB (ISO/DIS 16032:2023 Clause 5)?

"At the beginning and at the end of the measurements, verify the
sensitivity of the instrumentation with a sound calibrator class 1
according to IEC 60942. If the calibration measurement deviates from
previous calibrations by more than 0,5 dB, do not use this equipment until
the reason for this deviation has been clarified and appropriate actions
have been taken." Each reading of this measurement is held to every
calibration before it: the earlier calibrations given, and for the
reading at the end, the one at the beginning as well. A deviation of
exactly 0,5 dB is not "more than" it and passes. The 2004 edition asked
for the two calibrations without a limit; the 0,5 dB is new in the
revision.

The readings are compared as levels, so they must come from the same
calibrator at the same stated level; readings taken at different stated
levels are passed instead as each one's departure from its stated level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `calibration_levels_db` | The calibrator readings of this measurement in the order taken, the one at the beginning and the one at the end, in dB. One reading alone is judged against `previous_levels_db`, which lets the beginning be checked before measuring. |
| `previous_levels_db` | Readings of earlier calibrations of the same instrumentation, in dB; `None` (default) to compare the end with the beginning only. |

**Returns:** [`CalibrationDeviationResult`](/phonometry/reference/api/building/service-equipment/#calibrationdeviationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a reading is not a finite level, or there is nothing to compare: one reading and no earlier calibration. |
