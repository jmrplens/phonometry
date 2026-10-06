← [Documentation index](../../README.md)

# Service-Equipment and Activity Noise (ISO 16032)

A neighbour's toilet flushing at night, a lift motor behind a bedroom wall, a
ventilation outlet that hums, or the bar downstairs: the number a building
regulation puts on them comes from ISO 16032, the **engineering method** for
the sound pressure level that service equipment makes in a room. Its revision
widens the scope from installed equipment to **activities**, sources in or
near the building whose operation nobody on site controls, such as sports
facilities, pubs and amplified music.

The library implements the revision from its draft, **ISO/DIS 16032:2023**,
published in Germany as E DIN EN ISO 16032:2023-05. The published second
edition is not available to the project; the draft is the only text of the
revision there is, so everything the library implements follows it, and it
is cited as a draft, with
its own clause numbers. The withdrawn 2004 edition is used only to say what
changed. The survey method for the same quantities is
[ISO 10052](insulation-survey.md), and the
prediction of the structure-borne part of equipment noise is
[EN 12354-5](../design/installed-structure-borne.md).

**Where it applies.** Clause 1 intends the method for rooms of about 300 m³
or less, in dwellings, hotels, schools, offices and hospitals. It is not meant
for large auditoriums and concert halls, nor for a source so far from the
building that the weather changes how the sound gets there, although the
operating conditions of Annex B can still be used in such cases.

## What the method measures

The linear band spectrum is recorded together with the A- or C-weighted level
(a *multispectral* recording, Clause 6) in one of three quantities: the
**maximum level** with time weighting S or F, read at the instant the
weighted level peaks, or the **equivalent continuous level** over an
integration time. The single numbers are then computed from the bands, never
read off the meter, and Table 1 names them:

| | A-weighted | C-weighted |
| :--- | :--- | :--- |
| Maximum, time weighting S | $L_\mathrm{A,Smax}$, $L_\mathrm{A,Smax,nT}$, $L_\mathrm{A,Smax,n}$ | $L_\mathrm{C,Smax}$, $L_\mathrm{C,Smax,nT}$, $L_\mathrm{C,Smax,n}$ |
| Maximum, time weighting F | $L_\mathrm{A,Fmax}$, $L_\mathrm{A,Fmax,nT}$, $L_\mathrm{A,Fmax,n}$ | $L_\mathrm{C,Fmax}$, $L_\mathrm{C,Fmax,nT}$, $L_\mathrm{C,Fmax,n}$ |
| Equivalent continuous | $L_\mathrm{A,eq}$, $L_\mathrm{A,eq,nT}$, $L_\mathrm{A,eq,n}$ | $L_\mathrm{C,eq}$, $L_\mathrm{C,eq,nT}$, $L_\mathrm{C,eq,n}$ |

The draft is explicit that these are not interchangeable: only results
obtained with the same method are compared, and a result compared with a
legal requirement has to be the quantity the requirement names. The library
keys every single number by exactly this notation.

## Where the microphones go (7.2 and 7.3)

**Position 1 is a corner.** The corner with the highest C-weighted level is
found first, by the maximum level with S or F or by the equivalent level,
under the chosen operating conditions or any steady condition that finds the
loudest corner. A hand-held integrating meter will do: no band calculation,
no correction. The microphone goes preferably 0.5 m from the two walls and
the floor, raised to 1.0 m or 1.5 m where furniture is in the way, and at
least 0.2 m from any obstacle. A corner dominated by direct sound from a
source in the room, a ventilation outlet for example, is left out of the
search.

**Positions 2 and 3 are in the reverberant field.** They keep preferably
1.5 m, and at least 1.0 m, from each other and from the corner position;
1.5 m from any sound source in the room; 0.50 m from every room surface
(0.30 m in a small room where that cannot be met); and a height from 0.5 m to
2.0 m.

`loudest_corner` picks position 1 from the corner readings, and
`check_service_equipment_positions` holds a set of positions in a rectangular
room to the distances and heights of 7.3, and the corner to its height of
0.5 m to 1.5 m. The two preferences, the corner 0.5 m from its walls and the
positions 1.5 m apart, are reported as `preferred_corner_wall_distance` and
`preferred_separation` and do not decide `passes`:

```python
import numpy as np
from phonometry import building

# The loudest corner of four, C-weighted and read directly.
corner = building.loudest_corner([47.8, 49.3, 51.6, 50.2])
print(corner)                   # 2: the third corner, counted from 0

# A 4.2 m x 3.4 m x 2.5 m bedroom next to the bathroom.
positions = building.check_service_equipment_positions(
    (4.2, 3.4, 2.5),                            # length, width, height [m]
    (3.7, 2.9, 0.5),                            # position 1, in that corner
    [(1.4, 1.9, 1.2), (3.1, 0.8, 1.5)],         # positions 2 and 3
    source_positions_m=[(0.6, 3.0, 2.5)],       # a supply outlet in the ceiling
)
print(positions.passes, round(positions.separation_m, 2))   # True 2.05
print(positions.preferred_corner_wall_distance)             # True: 0.5 m from both walls
positions.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_positions_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_positions.svg" alt="Plan of a 4.2 by 3.4 metre bedroom. A shaded rectangle with a dashed edge, half a metre inside the walls, marks the zone the surface clearance leaves to the reverberant-field positions. The corner position, numbered 1, sits in the upper right corner, half a metre from both walls; positions 2 and 3 sit inside the shaded zone, more than 2 metres apart. A supply outlet in the ceiling near the upper left corner is joined to position 2, the nearest, by a dotted line labelled 1.88 metres, the distance in three dimensions. The second line of the title reads that the requirements are met." width="90%"></picture>

*The plan cannot show a distance in three dimensions: the outlet is in the
ceiling and position 2 is 1.2 m high, so the two are 1.88 m apart although
they look closer. The figure joins each source to its nearest position and
writes the true distance on the line.*

A room outline cannot show furniture, so the 0.2 m that 7.2 asks between the
corner microphone and any obstacle is judged from the distance measured on
site. Pass it as `corner_obstacle_distance_m`, one value or one per obstacle
near the microphone: the nearest decides `corner_obstacle_ok`, which then
enters `passes`, and 0.2 m itself is "at least 0.2 m". Left out, it is not
judged. The choice of corner stays with the person placing the microphone.

```python
positions = building.check_service_equipment_positions(
    (4.2, 3.4, 2.5), (3.7, 2.9, 0.5), [(1.4, 1.9, 1.2), (3.1, 0.8, 1.5)],
    source_positions_m=[(0.6, 3.0, 2.5)],
    corner_obstacle_distance_m=[0.35, 0.25],    # a wardrobe and a radiator [m]
)
print(positions.corner_obstacle_distance_m, positions.passes)   # 0.25 True
```

**A source in the room gets a position of its own (7.9).** Where a source
stands in the room itself, a ventilation outlet in the wall or in the ceiling
for example, one additional position is measured for each: 1 m in front of a
wall source at 1.5 m above the floor, or 1.5 m above the floor directly below
a ceiling source. Its result is reported separately, never standardized or
normalized, and not averaged with positions 1, 2 and 3.
`additional_microphone_position` places it in the same coordinates:

```python
extra = building.additional_microphone_position(
    (4.2, 3.4, 2.5), (0.6, 3.0, 2.5), mounting="ceiling")
print(extra)                                    # [0.6 3.  1.5]
```

## How many positions (7.4.1)

The A-weighted readings of positions 1, 2 and 3, as the instrument shows them
without any correction, decide whether three are enough. If they are within
3.0 dB of each other the corrections follow. Otherwise the corner is measured
again with two new room positions, 4 and 5, and the six have to be less than
6.0 dB apart; failing that, the corner once more with positions 6 and 7, and
the nine less than 9.0 dB apart. A difference larger than 9.0 dB that comes
from unpredictable variations in time, while the corner readings show a
steady source, interrupts the session: the cause is investigated before a new
series, and no reading of the interrupted one is used. The same ladder
applies to a maximum level (7.4.2), where the sound exposure level
$L_\mathrm{AE}$ may stand in for short events.

`check_position_spread` takes the readings in that order (corner, 2, 3, then
corner, 4, 5 and corner, 6, 7) and says what comes next:

```python
first = building.check_position_spread([34.1, 31.2, 35.6])
print(first.action, first.next_positions)       # add_positions (4, 5)

second = building.check_position_spread([34.1, 31.2, 35.6, 33.9, 32.4, 34.8])
print(second.action, round(second.corner_standard_deviation_db, 2))  # proceed 0.14
second.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_position_spread_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_position_spread.svg" alt="Six A-weighted readings in the order of 7.4.1: the corner at 34.1 dB, positions 2 and 3 at 31.2 and 35.6 dB, the corner again at 33.9 dB and positions 4 and 5 at 32.4 and 34.8 dB. A shaded band 6 dB tall starting at the lowest reading holds all six. The title gives the spread, 4.4 dB, and the verdict, proceed." width="80%"></picture>

*The first three readings are 4.4 dB apart, past the 3.0 dB of the first
stage; with positions 4 and 5 the six are still 4.4 dB apart, under the
6.0 dB the second stage allows, so the method proceeds with all six. The
corner, measured twice, is the reading 7.4.1 uses when a statistical value is
wanted: the standard deviation of the corner readings is taken as
representative of the room average.*

The draft leaves two boundaries without a rule: six readings exactly 6.0 dB
apart, and nine exactly 9.0 dB apart, are neither "less than" nor "exceeding"
the limit. The library reads the ladder as a sequence, so a spread at a limit
does not pass it. Positions 6 and 7 answer only a difference under 9.0 dB,
and more readings can only widen the spread, so three or six readings already
9.0 dB apart or more get `"interrupt"` at once: no later stage can pass.
Whether the difference comes from the time variation or from the source is
for the person measuring to judge, since the levels alone cannot say. The
gaps are in the
[errata registry](../../ERRATA.md).

## From readings to a single number

Clause 6 fixes the order: average, correct for the background, standardize or
normalize if a regulation asks for it, then weight.

**The band average (Formula (1), 7.5).** Every reading enters the energy
average, the repeated corner readings included, and the band levels are
rounded to one decimal:

$$
L = 10 \lg \left[ \frac{1}{n} \sum_{i=1}^{n} 10^{0.1 L_i} \right]\ \mathrm{dB}
$$

**The background (Clause 9).** The background is measured as the equivalent
level over about 30 s just before or after each set of measurements, at the
same positions (7.6; the [checks on site](#checks-on-site) hold the time to
30 s within the tolerance you accept, and offer the route for a background
that varies). With
$\Delta L = L_1 - L_2$ between the measured band and the background band,
nothing is corrected at 10 dB or more; from 4 dB to 10 dB the band is
corrected by Formulae (7) to (9),

$$
L = L_1 - K, \qquad K = -10 \lg \left[ 1 - 10^{-0.1 \Delta L} \right]\ \mathrm{dB}
$$

and below 4 dB the correction is held at the 2.2 dB a 4 dB margin gives. Such
a band is influenced by the background: the report has to say so, and for a
comparison with a limit the result is an upper limit of the equipment level.
`service_equipment_background_correction` applies the clause on its own:

```python
k = building.service_equipment_background_correction(
    [40.0, 40.0, 40.0], [28.0, 34.0, 38.0])
print(np.round(k.correction_db, 2), k.regime)
# [0.   1.26 2.2 ] ('none', 'corrected', 'limited')
```

**Standardization and normalization (4.8, 7.7).** If required, the corrected
bands are referred to a reference reverberation time $T_0$, 0.5 s unless
another value is specified, or to a reference absorption area
$A_0 = 10$ m² (Formulae (5) and (6)):

$$
L_\mathrm{nT} = L - 10 \lg \frac{T}{T_0}\ \mathrm{dB}, \qquad
L_\mathrm{n} = L - 10 \lg \frac{A_0\,T}{0.16\,V}\ \mathrm{dB}
$$

The reverberation time is measured by ISO 3382-2 in the one-third-octave
bands 50 Hz to 5000 Hz (octave bands 63 Hz to 4000 Hz), preferably by the
impulse response method at least from 50 Hz to 315 Hz (Clause 8). Only those
bands are standardized: 25, 31.5, 40, 6300, 8000 and 10 000 Hz enter the
weighted sums unstandardized, and the report mentions it whenever they
contribute. The draft also advises against standardizing an unfurnished room
with one highly absorbing surface, where late reflections between the other,
parallel surfaces lengthen the reverberation time and the correction goes
wrong.

**The weighted values (4.3, 4.4, 7.8).** The A- and C-weighted single numbers
are energy sums of the corrected bands plus the Annex A corrections, rounded
to whole decibels:

$$
L_\mathrm{A} = 10 \lg \sum_{i} 10^{0.1 (L_i + A_i)}\ \mathrm{dB}, \qquad
L_\mathrm{C} = 10 \lg \sum_{i} 10^{0.1 (L_i + C_i)}\ \mathrm{dB}
$$

The A-weighted value is summed over the restricted range 50 Hz to 5000 Hz or
the extended range 25 Hz to 10 000 Hz, and the C-weighted value over the
extended range; the report names the range. The draft's NOTE to 7.8 suggests
comparing the result with the weighted level the instrument showed: more
than 2 dB apart, the calculation deserves a second look, and
`check_instrument_agreement` makes the comparison (see
[checks on site](#checks-on-site)).

`service_equipment_level` runs the whole chain. Here a water closet is flushed
and refilled (Annex B.2.6) and heard in the bedroom next door, three readings
from 25 Hz to 10 kHz:

```python
freqs = np.array(list(building.SERVICE_EQUIPMENT_WEIGHTING["third"]["A"]))
spectrum = np.array([29.5, 31.0, 33.2, 35.4, 37.1, 38.6, 40.2, 41.5, 42.3,
                     42.8, 42.6, 41.9, 40.8, 39.4, 37.9, 36.2, 34.6, 33.1,
                     31.4, 29.8, 28.1, 26.5, 24.6, 22.9, 21.0, 19.4, 17.6])
readings = spectrum + np.array([[0.6], [-0.9], [0.4]])   # positions 1, 2, 3
background = np.array([28.0, 28.4, 29.6, 27.2, 25.1, 23.0, 21.2, 19.6, 18.1,
                       16.9, 15.8, 14.9, 14.1, 13.4, 12.8, 12.3, 11.9, 11.6,
                       11.4, 11.3, 11.2, 11.2, 11.3, 11.5, 11.8, 12.2, 12.7])
t = np.array([np.nan, np.nan, np.nan, 0.82, 0.78, 0.74, 0.70, 0.66, 0.63,
              0.60, 0.58, 0.56, 0.55, 0.54, 0.53, 0.52, 0.51, 0.50, 0.49,
              0.48, 0.47, 0.46, 0.45, 0.44, np.nan, np.nan, np.nan])
res = building.service_equipment_level(
    readings, freqs, quantity="eq",
    background_db=background, reverberation_time_s=t, volume_m3=35.7,
)
print(res.ratings["LA,eq"], res.ratings["LA,eq,nT"], res.ratings["LC,eq,nT"])
# 45 45 51
print(res.upper_limit("A"), res.upper_limit("C"))  # False True
print(res.unstandardized_bands_hz)
# (25.0, 31.5, 40.0, 6300.0, 8000.0, 10000.0)
res.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_level_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_level.svg" alt="The one-third-octave spectrum of a water closet heard in a bedroom, 25 Hz to 10 kHz. The average of the three readings peaks near 43 dB at 200 Hz and falls to about 18 dB at 10 kHz. The background, dotted, lies 1.6 to 3.7 dB under the average at 25, 31.5 and 40 Hz, 8.3 dB under it at 50 Hz, more than 11 dB under it from 63 Hz to 5 kHz, and 5 to 9 dB under it from 6.3 to 10 kHz. The curve corrected for the background meets the average from 63 Hz to 5 kHz; it lies 2.2 dB under it in the three lowest bands, 0.7 dB under it at 50 Hz and 0.5 to 1.7 dB under it from 6.3 to 10 kHz. The standardized curve runs up to 2.8 dB below the average at low frequencies, where the room is live, and up to 0.6 dB above it near 5 kHz. Grey bands mark 25 to 40 Hz and 6.3 to 10 kHz as not standardized, and orange triangles mark the three lowest bands as upper limits. The title gives L A,eq,nT = 45 dB." width="94%"></picture>

*The three lowest bands sit within 4 dB of the background, so their
correction is held at 2.2 dB and they are upper limits. They lie in the
C-weighted range, which makes $L_\mathrm{C,eq}$ an upper limit, and outside
the restricted A-weighted range, which leaves $L_\mathrm{A,eq}$ unaffected.
At 50 Hz and from 6.3 kHz up the background is 5 dB to 9 dB below, and
Formula (8) takes 0.5 dB to 1.7 dB off those bands.
The standardization lowers the bands where the room is more reverberant than
0.5 s and raises those where it is less, and leaves the six grey bands as
they are.*

### `service_equipment_level` parameters

| Parameter | Type | Units | Default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `levels_db` | array | dB | required | Band levels of every reading, `(readings, bands)`; one row for a single reading |
| `frequencies_hz` | array | Hz | required | Nominal centres, increasing: one-third octaves 25 Hz to 10 kHz or octaves 31.5 Hz to 8 kHz |
| `quantity` | str | | required | `"Smax"`, `"Fmax"` or `"eq"`, the Table 1 quantity; it names the single numbers |
| `band` | str | | `"third"` | `"third"` or `"octave"`; Clause 6 asks for one-third octaves, octaves are optional |
| `background_db` | array | dB | `None` | One level per band, or one row per position, energy-averaged |
| `reverberation_time_s` | array | s | `None` | Per band; only 50 Hz to 5 kHz (octaves 63 Hz to 4 kHz) is read, the rest may be `nan` |
| `volume_m3` | float | m³ | `None` | Room volume for the normalized levels; needs the reverberation time |
| `reference_reverberation_time_s` | float | s | `0.5` | $T_0$ of Formula (5) |
| `a_weighting_range` | str | | `"restricted"` | `"restricted"` (50 Hz to 5 kHz; octaves 63 Hz to 4 kHz) or `"extended"` (25 Hz to 10 kHz; octaves 31.5 Hz to 8 kHz) |

The result carries `average_db`, `background` (the Clause 9 correction),
`corrected_db`, `standardized_db`, `normalized_db`, `standardizable`,
`ratings` and `unrounded_ratings` keyed by Table 1, `upper_limit("A")` and
`upper_limit("C")`, `unstandardized_bands_hz`, `reproducibility_db` and
`weighted_reproducibility_db`. The C-weighted values are formed only when the
bands cover the extended range.

For the octave counterpart of the restricted A-weighting range the draft
gives no range of its own; the library uses 63 Hz to 4000 Hz, the octave
range the draft pairs with 50 Hz to 5000 Hz for the standardization.

## Checks on site

Beside the method, the draft sets numbers for the measurement itself: how far
the calibration may drift, how long the background is measured, when a
varying background still lets the result stand, when a period was disturbed,
and how far the calculation may stand from the meter. Each check below
returns a verdict with `passes` (and refuses to be read as `True` or `False`
itself) and a `.plot()`.

### The calibration (Clause 5)

At the beginning and at the end of the measurements the sensitivity of the
instrumentation is verified with a class 1 sound calibrator (IEC 60942). A
calibration that deviates from previous calibrations by more than 0.5 dB
takes the equipment out of use until the reason is clarified and the
sensitivity put right. The limit is new in the revision: the 2004 edition
asked for the two calibrations and set no number.
`verify_calibration_deviation` holds each reading to every calibration
before it, the earlier ones given and, for the end, the beginning as well; a
deviation of exactly 0.5 dB is not "more than 0.5 dB" and passes. The
readings are compared as levels, so they come from the same calibrator at the
same stated level.

```python
cal = building.verify_calibration_deviation(
    [94.0, 94.2],                       # beginning and end of this measurement [dB]
    previous_levels_db=[93.9, 94.0],    # earlier calibrations of the instrumentation [dB]
)
print(np.round(cal.deviations_db, 2), cal.passes)   # [0.1 0.3] True
cal.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_calibration_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_calibration.svg" alt="Four calibrator readings in order: two earlier calibrations at 93.9 and 94.0 dB, then this measurement's beginning at 94.0 dB and end at 94.2 dB. Over the beginning and the end a shaded band from 93.5 to 94.4 dB marks where a reading stays within 0.5 dB of every calibration before it; both readings lie inside it, labelled 0.10 dB and 0.30 dB. The title gives the largest deviation, 0.30 dB, and says the equipment may be used." width="80%"></picture>

*The band over each reading of this measurement is where it would stay within
0.5 dB of every calibration before it. The end, 94.2 dB, is 0.3 dB from the
earliest calibration and 0.2 dB from the beginning, so the equipment may be
used.*

### The background measurement (7.6)

The background is the equivalent level in bands over approximately 30 s just
before or after each set of measurements, at the same microphone positions.
The draft prints no tolerance for "approximately", so the library sets none:
`check_background_duration` asks for the departure from 30 s, either way,
that your report accepts as approximate (`tolerance_s`, a required keyword),
holds each time to it, and reports every departure whatever the verdict. A
departure of exactly the tolerance is within it, and `tolerance_s=0.0` holds
each time to 30 s exactly. Whether the background was taken just before or
after each set, and at the same positions, is not a number and stays with the
operator.

```python
duration = building.check_background_duration(
    [30.0, 31.0, 30.0, 26.5],   # measurement time of each background [s]
    tolerance_s=2.0,            # what the report accepts as "approximately" [s]
)
print(duration.departures_s, duration.within_tolerance, duration.passes)
# [ 0.   1.   0.  -3.5] [ True  True  True False] False
duration.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_background_duration_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_background_duration.svg" alt="Four background measurement times against a dashed line at 30 s and a shaded band from 28 to 32 s, the 2 s accepted either way. The first three, at 30, 31 and 30 s, lie inside the band; the fourth, at 26.5 s, lies under it and is ringed in orange as beyond the tolerance. The title gives the largest departure, 3.5 s, beyond the 2 s accepted." width="80%"></picture>

*With 2 s accepted either way, the first three backgrounds are approximately
30 s and the fourth, 3.5 s short, is not. Every departure goes in the report,
and the tolerance written beside them is what decides.*

### A background that varies (NOTE to Clause 9)

The correction of Clause 9 assumes a background roughly constant in time.
Where it is not, road traffic for example, a reliable correction cannot be
made, and the NOTE to Clause 9 offers another route: watch the maximum level
of the background for 10 min to 15 min at the corner position; if it lies
10 dB or more below the equipment, the result can be regarded valid without
correction. The NOTE asks to check "the validity in all relevant
octave-bands", words kept from the 2004 edition, which measured in octaves;
`check_varying_background` judges the margin in every band it is given,
one-third octaves or octaves. Both ends of the period are included, and so is
a margin of exactly 10 dB. The 2004 edition watched "one of the microphone
positions"; the draft names the corner.

```python
octaves = [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]
varying = building.check_varying_background(
    [36.5, 35.0, 31.0, 27.5, 24.0, 21.0, 17.5],   # background maximum over 12 min [dB]
    [44.0, 46.5, 43.0, 39.5, 36.0, 32.5, 28.0],   # the equipment, same bands [dB]
    observation_time_s=720.0,
    frequencies_hz=octaves,
)
print(varying.margin_ok, varying.passes)
# [False  True  True  True  True  True  True] False
varying.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_varying_background_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_varying_background.svg" alt="Octave bands from 63 Hz to 4 kHz. The equipment level, solid with square markers, falls from 46.5 dB at 125 Hz to 28 dB at 4 kHz. A dashed line runs 10 dB under it. The background maximum, dotted, lies under the dashed line from 125 Hz up, but at 63 Hz it reaches 36.5 dB, above the dashed line at 34 dB, and an orange triangle marks that band as less than 10 dB below. The title reads not valid without correction, watched for 12 min." width="80%"></picture>

*The traffic peaks reach 36.5 dB at 63 Hz, only 7.5 dB under the equipment,
so that band is short of the 10 dB the NOTE asks and the result cannot stand
without correction there; from 125 Hz up the margin is 10.5 dB to 12 dB.*

### Disturbed periods (Clause 9)

"A simple check on-site" closes Clause 9: compare the maximum level with the
equivalent level in the middle of the frequency range during each
measurement period. For many stable sources the difference should be less
than 5 dB; a larger one says the period was disturbed, by a closing door or
footfall for example. The check is new in the revision. It holds for stable
sources, not for one whose own level varies, and the draft names the band
only as "the middle of the frequency range", so the operator chooses it. A
difference of exactly 5 dB is not less than 5 dB and marks the period.

```python
periods = building.check_measurement_disturbance(
    [41.6, 42.0, 48.9, 41.3, 41.8, 42.2],   # maximum of a mid-range band, per period [dB]
    [39.0, 39.4, 41.1, 38.9, 39.2, 39.6],   # equivalent level, same band and periods [dB]
)
print(np.round(periods.differences_db, 1), periods.disturbed_periods)
# [2.6 2.6 7.8 2.4 2.6 2.6] (2,)
periods.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_disturbance_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_disturbance.svg" alt="Six measurement periods with the maximum level less the equivalent level of each: 2.6, 2.6, 7.8, 2.4, 2.6 and 2.6 dB. A dashed line at 5 dB bounds a shaded region above it labelled disturbed; only the third period lies in it. The title reads disturbed periods: 3." width="80%"></picture>

*In five periods the maximum sits 2.4 dB to 2.6 dB above the equivalent
level; in the third it sits 7.8 dB above, and that period was disturbed.
`disturbed_periods` counts from 0, the figure from 1.*

### The calculation against the instrument (NOTE to 7.8)

The NOTE to 7.8 suggests comparing the corrected and calculated A- and
C-weighted results with the values the instrument registered: more than
2 dB apart, the calculations should be checked for possible explanations. The
NOTE is new in the revision. `check_instrument_agreement` takes the result and
the instrument's value for each single number, keyed by its Table 1 notation;
a reading at each position is energy-averaged by Formula (1). The calculated
value is the single number as 7.8 rounds it, and exactly 2 dB agrees. A
background correction or a standardization can account for a difference by
itself, which is the kind of explanation the NOTE asks for.

```python
agreement = building.check_instrument_agreement(
    res, {"LA,eq": [46.0, 44.5, 45.8], "LC,eq": [52.3, 50.8, 52.1]})
print({k: round(v, 1) for k, v in agreement.differences_db.items()}, agreement.passes)
# {'LA,eq': -0.5, 'LC,eq': 0.2} True
agreement.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_instrument_agreement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/service_equipment_instrument_agreement.svg" alt="The calculated less the instrument's value for two single numbers, L A,eq and L C,eq, against a shaded band from minus 2 to plus 2 dB. L A,eq sits at minus 0.5 dB and L C,eq at plus 0.2 dB, both inside the band. The title says the calculation agrees." width="80%"></picture>

*The meter read 44.5 dB to 46.0 dB A-weighted and 50.8 dB to 52.3 dB
C-weighted at the three positions of the water closet example. Their energy
averages lie 0.5 dB above the calculated $L_\mathrm{A,eq}$ = 45 dB and 0.2 dB
below $L_\mathrm{C,eq}$ = 52 dB, well inside 2 dB.*

## Operating conditions (Annex B)

How the equipment runs while it is measured decides the number as much as the
microphones do. Annex B is normative, but national requirements and
regulations take precedence (B.1.1), and equipment it does not list is
measured by its principles with the chosen conditions reported in detail.
`SERVICE_EQUIPMENT_OPERATING_CONDITIONS` holds each entry as data:

| Key | Clause | Maximum level | Equivalent level |
| :--- | :--- | :--- | :--- |
| `water_tap` | B.2.2 | a single tap: open fully, wait, close; a hot and cold mixer: hot tap open, then cold, closed in the same order; single-lever, flow and temperature, and thermostatic mixers: through the temperature range | about 30 s at the loudest setting; for single-lever, flow and temperature, and thermostatic mixers the highest of the average, hot and cold settings |
| `shower_cabin` | B.2.3 | as a tap | as a tap |
| `bath` | B.2.4 | as a tap, and the shower; without a wall fixture the shower is held about 1.5 m above the tub bottom | as a tap |
| `filling_emptying` | B.2.5 | filling, then emptying | the filling period and the emptying period, half full |
| `water_closet` | B.2.6 | a full flushing and refilling cycle | the same cycle |
| `mechanical_ventilation` | B.3 | about 30 s at the loudest setting | about 30 s |
| `heating` / `cooling` | B.4 | start from cold, full load, each appliance / about 30 s | about 30 s |
| `lift` | B.5 | 1 or 2 persons, up to five floors each way, at least three repetitions | the same cycle |
| `rubbish_chute` | B.6 | two PVC tubes, 0.1 m long, 50 mm across, 0.7 kg/m | not measured |
| `auxiliary_equipment` | B.7 | start, operate, stop; or a full automatic cycle | the cycle |
| `car_park_door` | B.8 | opening and closing | a full cycle |
| `other_equipment` | B.9 | the cycle of normal use | the cycle |
| `unknown_source` | B.10 | | several 30 s periods in the loudest hour of normal operation |

B.10 is the new part. An activity, a restaurant's coolers or live music next
door, is measured in normal operation, automatic controls suspended where
needed, over several 30 s periods within the hour the level is expected to be
highest, leaving out downtime and minor irregular events. Where the sound is
too irregular for the corner search, the acoustically most reflective corner
becomes position 1, and the report says so. Where no operating cycle can be
defined at all, the equivalent level is averaged until it is stable, and not
for less than 30 s (B.1.3).

```python
wc = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["water_closet"]
print(wc.clause, wc.equivalent_cycle)
# B.2.6 a full flushing and refilling cycle
chute = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["rubbish_chute"]
print(chute.equivalent_level, chute.parameters["tube_length_m"])   # False 0.1
```

## Precision (Clause 10)

Table 2 estimates the reproducibility standard deviation of a room-average
band level from a limited number of measurements of steady sources:

| One-third-octave bands | Octave bands | $\sigma_\mathrm{R}$ |
| :--- | :--- | :--- |
| 25 Hz to 160 Hz | 31.5 Hz to 125 Hz | 1.9 dB |
| 200 Hz to 315 Hz | 250 Hz | 1.5 dB |
| 400 Hz to 630 Hz | 500 Hz | 1.2 dB |
| 800 Hz to 10 000 Hz | 1000 Hz to 8000 Hz | 1.0 dB |
| A-weighted | | 0.8 dB |
| C-weighted | | 1.2 dB |

The two weighted values hold for a steady sound with a relatively flat
spectrum from 25 Hz to 10 kHz, at least 10 dB above the background. A source
that fluctuates raises the uncertainty, the maximum levels most of all. The
result carries the band values as `reproducibility_db` and the value of each
single number, keyed like `ratings`, as `weighted_reproducibility_db`; the
tables are `SERVICE_EQUIPMENT_REPRODUCIBILITY` and
`SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY`. The draft states no coverage
factor, so the library does not form an expanded uncertainty.

```python
print(dict(res.weighted_reproducibility_db))
# {'LA,eq': 0.8, 'LC,eq': 1.2, 'LA,eq,nT': 0.8, 'LC,eq,nT': 1.2, 'LA,eq,n': 0.8, 'LC,eq,n': 1.2}
```

## What the revision changes

Against the withdrawn ISO 16032:2004, the draft:

- widens the scope from installed service equipment to activities and
  unknown sources in or near the building (B.10);
- measures in one-third-octave bands, octaves being optional, where 2004
  measured in octaves only;
- sets the number of positions by the spread ladder of 7.4.1, where 2004 took
  two corner readings and measured each position as many times as the
  difference between them in whole decibels;
- standardizes 50 Hz to 5000 Hz (octaves 63 Hz to 4000 Hz) only;
- sums the A-weighted value over 50 Hz to 5000 Hz or 25 Hz to 10 000 Hz, where
  2004 used octaves 63 Hz to 8000 Hz (31.5 Hz to 8000 Hz for C);
- relaxes the reverberant-field positions: 1.0 m apart at least (2004 asked
  1.5 m), 0.50 m from surfaces (0.75 m) and up to 2.0 m high (1.5 m);
- raises the low-frequency reproducibility of Table 2 from 1.5 dB to 1.9 dB
  and the C-weighted one from 1.1 dB to 1.2 dB;
- takes the equipment out of use when a calibration deviates from previous
  calibrations by more than 0.5 dB, where 2004 asked for the calibrations and
  set no limit;
- adds two on-site checks, a maximum less than 5 dB above the equivalent
  level in each period and calculated results within 2 dB of the instrument;
- watches the maximum of a varying background at the corner position, where
  2004 used any one of the positions.

## Verifying it without a worked example

The draft prints no worked example, so the conformance rows stand on what it
does print and on closed forms. Printed: the 2.2 dB a 4 dB background margin
gives (Clause 9), the 36 A-weighting cells of Table A.1, its C-weighting cells
with the ten misprinted ones taken from IEC 61672-1, and the 38 cells of
Table 2. Closed forms: the band average of three readings, a reverberation
time of $2T_0$ lowering exactly 50 Hz to 5000 Hz (octaves 63 Hz to 4000 Hz)
by $10\lg 2$, an equivalent absorption area of 16 m² normalized to
$A_0 = 10$ m² gaining
$10\lg 1.6 = 2.04$ dB, the A- and C-weighted sums of a flat spectrum and
their rounding half up to whole decibels, the thresholds of Clause 9 met by
levels given to 0.1 dB, the thresholds of 7.4.1 at their boundaries, every
distance and height limit of 7.3, and the corner height and preferred wall
distance of 7.2, met exactly and missed by 0.01 m, and the positions 7.9
places in front of a wall source and below a ceiling one. The checks on site
stand on the limits the draft prints, each met exactly and missed: the 0.2 m
from an obstacle, the 0.5 dB calibration deviation, the 10 min to 15 min and
the 10 dB of a varying background, the 5 dB between the maximum and the
equivalent level, and the 2 dB between calculation and instrument, with the
instrument above the calculation and below it. A difference of decimal
readings that lands a hair off its limit in binary, 40.3 dB over 30.3 dB for
the 10 dB for instance, still reads as the limit. Since the draft prints no
tolerance for its 30 s, the background row gives its own (0 s, 0.3 s and
1 s) and holds 30 s to each, met exactly and missed above and below.

## Quick answers

### Why does the C-weighted value differ from Table A.1 as printed?

Because the table misprints it. The draft's one-third-octave C-weighting
column reads 0 dB in every band from 1600 Hz to 10 000 Hz and −5 dB at 25 Hz,
which contradicts its own octave column (−0.2, −0.8 and −3.0 dB at 2, 4 and
8 kHz) and IEC 61672-1 (−0.1 dB to −4.4 dB from 1600 Hz up, −4.4 dB at
25 Hz). The library uses the IEC 61672-1 values in those ten cells, from
Table 3 of IEC 61672-1:2013, which the
[frequency weighting](../../signals/levels/weighting.md) implements;
read as printed, a flat spectrum would sum 0.4 dB higher. The defect is in the
[errata registry](../../ERRATA.md).

### Are the 25 Hz and 10 kHz bands standardized?

No. 7.7 standardizes and normalizes only 50 Hz to 5000 Hz, because the
reverberation time outside cannot be measured reliably. The outer bands enter
the weighted sums as corrected, and `unstandardized_bands_hz` lists the ones
that do, for the report.

### Can I use it for the bar downstairs?

Yes: that is what B.10 adds. Run the activity normally, measure several 30 s
periods in its loudest hour, and treat each set of three positions exactly as
for a service equipment. Where the sound is too irregular to find the loudest
corner, use the most reflective one and report the deviation.

### Does a background measured over 28 s pass?

Only if the tolerance you give allows it. 7.6 asks for "approximately 30 s"
and prints no tolerance, so `check_background_duration` asks you for one
(`tolerance_s`) rather than decide how much "approximately" allows: with 2 s
accepted, 28 s passes; with 1 s, it does not. Either way the 2 s departure is
reported, the tolerance goes in the report beside it, and nothing else in the
method changes.

### Is the result an upper limit?

When a band of the weighted range was within 4 dB of the background, yes:
`upper_limit("A")` and `upper_limit("C")` say which single number is, and the
report has to state it.

## References

- **E DIN EN ISO 16032:2023-05**, *Acoustics — Measurement of sound pressure level from service equipment or activities in buildings — Engineering method (draft international standard)*. The draft ISO/DIS 16032:2023 of the second edition (prEN ISO 16032:2023) in its German publication, German and English text, and cited as a draft. Every clause number on this page is the draft's. Six printed defects are in the errata registry, the C-weighting of Table A.1 among them.
- **ISO 16032:2004**, *Acoustics — Measurement of sound pressure level from service equipment in buildings — Engineering method*. The first edition, which the draft revises and which is withdrawn. Read in BS EN ISO 16032:2004 for what changed: octave bands only, a position count set by two corner readings, and no activity sources.
- **ISO 10052:2021**, *Acoustics — Field measurements of airborne and impact sound insulation and of service equipment sound — Survey method* (https://www.iso.org/standard/76560.html). The survey method for the same quantities: three A- or C-weighted readings, no band analysis, and the reverberation index in place of a measured reverberation time.

## Standards

**Covered.** The engineering method of ISO/DIS 16032:2023, the draft of the second edition
of ISO 16032, read in E DIN EN ISO 16032:2023-05: the Table 1 quantities, the
corner search of 7.2 and the distances of 7.3 for a rectangular room, the
position ladder of 7.4.1 with the corner standard deviation, the additional
position of 7.9 for a source in the room, the band average
of Formula (1) rounded to 0.1 dB, the background correction of Clause 9 held
at 2.2 dB, standardization and normalization by Formulae (5) and (6) over
50 Hz to 5000 Hz, the A- and C-weighted sums of Formulae (2) and (3) over the
ranges of 7.8 rounded to whole decibels, Table A.1 (with the misprinted
C-weighting cells from IEC 61672-1), Table 2, and the operating conditions of
Annex B as data, the activities of B.10 included. The checks on site: the
0.2 m from obstacles of 7.2 from a measured distance, the 0.5 dB calibration
deviation of Clause 5, the 30 s background of 7.6 against the tolerance the
operator gives, the 10 min to 15 min
maximum of a varying background and its 10 dB margin (NOTE to Clause 9), the
5 dB between the maximum and the equivalent level of Clause 9, and the 2 dB
comparison with the instrument of the NOTE to 7.8.

**Not covered.** The draft is not the published standard: where ISO 16032:2024 differs, this
page follows the draft. The library does not record the multispectral time
trace or find the instant of the maximum: it takes the band levels at that
instant as given. The checks on site judge numbers the operator measures
and passes in; they do not decide what is not a number: which corner is the
loudest, whether the background was taken just before or after each set and
at the same positions, which band is "the middle of the frequency range", or
whether a source is stable enough for the 5 dB check. "Approximately 30 s"
has no tolerance in the draft, so the library sets none: the operator names
the one the report accepts. Nothing checks the room volume of about 300 m³ or
less that Clause 1
intends the method for. The "specific frequency range" that 4.2 admits
beside the two ranges, and that the form of Annex C has a box for, is not
offered: 7.8 forms the weighted values over the restricted or the extended
range only, and a band set that does not cover the chosen range is refused.
No `.report()` fiche is produced: the building fiches are drawn around an
ISO 717 reference curve that this method does not have. There is no printed
worked example, so no row reproduces one.

## See also

- [Sound Insulation Survey Method (ISO 10052)](insulation-survey.md):
  the survey method for the same service-equipment quantities.
- [Installed structure-borne sound (EN 12354-5)](../design/installed-structure-borne.md):
  predicting the structure-borne part of the same noise before the building
  exists.
- [Room acoustic parameters (ISO 3382-1/2)](../rooms/room-acoustics.md): the ISO 3382-2
  reverberation times the standardization needs.
- [Frequency Weighting (A, C, Z)](../../signals/levels/weighting.md): the
  IEC 61672-1 A- and C-weightings, whose Table 3 gives the ten C-weighting
  cells the draft misprints.
- [Errata found in published sources](../../ERRATA.md): the six
  defects of the draft this method meets.
- API reference:
  [`building.measurement.service_equipment`](https://jmrplens.github.io/phonometry/reference/api/building/service-equipment/).
