---
title: "emission.turbine_noise"
description: "Airborne noise of a steam turbine set and its driven machinery: IEC 61063:1991 (EN 61063:1996)."
sidebar:
  label: "turbine_noise"
---

Airborne noise of a steam turbine set and its driven machinery:
IEC 61063:1991 (EN 61063:1996).

IEC 61063 is a noise test code. It takes the survey method of ISO 3746 and
fixes, for one family of machines, what that method leaves open: the shape of
the measurement surface around a turbine, generator and exciter standing on
their operating floor, the microphone positions on it, how the background and
the room are corrected, and what the report says. The text read here is the
English one of BS EN 61063:1996, which reproduces IEC 1063:1991 without
modification; every clause, table and figure below was read on the printed
page, cited as PDF page and printed folio.

**The measurement surface** (clause 7.1, printed folio 7, PDF page 13). The
turbine set is enclosed by several *reference boxes* in juxtaposition, one per
part (turbine casings, gear, generator, exciter), terminating on the
reflecting plane. The measurement surface is made of right parallelepipeds
parallel to them at the measurement distance $d = 1$ m, and its area is
Equation (1),

$$
S = 2\,h_\mathrm{max}\,b_\mathrm{max} + \sum_{i=1}^{Z} l_i\,(2 h_i + b_i) \tag{Eq. 1}
$$

with $l_i$, $b_i$ and $h_i$ the length, width and height of
the $i$-th of the $Z$ parallelepipeds, dimensioned on the
measurement surface as Figure 2 draws them. The sum is the tops and the long
sides; $2 h_\mathrm{max} b_\mathrm{max}$ stands for every transverse
face, the two ends and the steps between neighbouring boxes. It is exact when
each cross-section contains the next one out towards both ends, as in both
drawings of Figure 2, and [`TurbineMeasurementSurface.enveloping_area_m2`](/phonometry/reference/api/power/turbine-noise/#turbinemeasurementsurfaceenveloping_area_m2)
gives the exact area of the stepped surface for the case it is not.

**The microphone positions** (clause 7.2, Figure 2). Five *key* positions are
prescribed: 1 and 5 at the centres of the two ends, 2 and 4 on the two long
sides and 3 overhead, the last three in the plane between the turbine and the
driven machinery. *Additional* positions follow at equal distances from the
key positions, close enough that "there is at least one measurement section
at each casing" (7.2.2): round the sides from 1 through 2, 5 and 4, and over
the set from 1 up the front end, across the top through 3 and down the rear
end to 5, as the plan and the elevation of Figure 2 draw them. Each of the two
paths is divided on its own, so the stations round the sides and those
overhead need not stand in the same transverse sections, as the drawings of
Figure 2 happen to put them; the text asks only for equal distances. The
overhead positions may be left out when a preliminary investigation shows
they move the sound power level by no more than 1,0 dB (NOTE of 7.2.2).

**The background correction** (clause 8.1, Table 2, printed folio 8, PDF page
14) is a stepped table applied at each microphone position, not the
closed form $-10 \lg(1 - 10^{-0.1 \Delta L})$ of ISO 3746:2010
Equation (12), which is applied to the surface-averaged level:

====================  ==============
Difference, dB        Correction, dB
====================  ==============
3                     3
4                     2
5                     2
6                     1
7                     1
8                     1
9                     0,5
10                    0,5
> 10                  0,0
====================  ==============

The background shall be at least 3 dB below the level with the source
operating (4.2); below that no valid measurement can be made, and the result
is only an indication of the upper limit (NOTE of 4.2).

**The environmental correction** $K$ (clause 8.2, Annex A). Figure A.3
(printed folio 12, PDF page 18) prints the curve and its formula,

$$
K = 10 \lg\left[1 + \frac{4}{A/S}\right] \tag{Figure A.3}
$$

with the equivalent absorption area $A = 0{,}16\,V/T$ of the room from
its reverberation time (A.3.1); A.3.2 obtains $K = L_W - L_{Wr}$ from a
calibrated reference sound source instead. $K$ shall not exceed 7 dB
(8.3 and A.3.3), which A.3.3 restates as $A/S \ge 1$.

**The surface sound pressure level and the sound power level** (clauses 8.3
and 8.4, printed folio 9, PDF page 15):

$$
\overline{L_{p\mathrm{A}}} = 10 \lg\left[\frac{1}{N} \sum_{i=1}^{N} 10^{0.1 L_{p\mathrm{A}i}}\right] - K \tag{Eq. 2}
$$

$$
L_{W\mathrm{A}} = \overline{L_{p\mathrm{A}}} + 10 \lg\frac{S}{S_0}, \qquad S_0 = 1\ \mathrm{m}^2 \tag{Eq. 3}
$$

**The report** (clauses 9 and 10, printed folios 9 and 10). The sound power
level is recorded rounded to the nearest whole decibel (9.4 g), and the report
states that it was obtained in full conformity with the standard and is
expressed in decibels above 1 pW, with at least the six items of clause 10.
The standard deviations of Table 1 (printed folio 4, PDF page 10), 5 dB for a
source with prominent discrete tones and 4 dB for a broadband one, are the
uncertainty the survey method tends to stay within.

The standard prints no worked example. Every function here is anchored in the
closed forms above and in the numbers the standard fixes: the nine cells of
Table 2, the two of Table 1, the 1 m of 7.1, the 7 dB of A.3.3, the 6 m/s of
4.3, the 3 dB of 4.2, the 1,0 dB of 7.2.2 and the 5 dB and 0,7 dB of the NOTE
of 8.3.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_turbine_test_environment

```python
check_turbine_test_environment(
    correction: TurbineEnvironmentalCorrection | None = None,
    *,
    environmental_correction_db: float | None = None,
    wind_speed_m_s: float | None = None,
) -> TurbineTestEnvironmentCheck
```

Is the test environment good enough for the standard (A.3.3, 4.3)?

A room qualifies when its environmental correction does not exceed 7 dB,
"K ≤ 7" (A.3.3), which the clause restates as $A/S \ge 1$; the two
agree to the whole decibel (the formula of Figure A.3 gives
$10 \lg 5 = 6{,}99$ dB at $A/S = 1$). Outdoors, and in very
large or open workspaces, $K$ is taken as zero (A.4), and
measurements outdoors need a wind speed below 6 m/s, with a windscreen
above 1 m/s (4.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `correction` | The environmental correction, from [`turbine_environmental_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_environmental_correction) or [`turbine_reference_source_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_reference_source_correction); or give `environmental_correction_db` instead. |
| `environmental_correction_db` | $K$ in dB, when it was found some other way, `0.0` outdoors (A.4). |
| `wind_speed_m_s` | The wind speed for a measurement outdoors, in metres per second; `None` indoors. |

**Returns:** The conditions and the verdict.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | unless exactly one of `correction` and `environmental_correction_db` is given, for a non-finite correction or for a negative wind speed. |

## turbine_background_correction

```python
turbine_background_correction(
    level_difference_db: ArrayLike,
) -> float | np.ndarray
```

Correction for background noise of Table 2 (clause 8.1).

The correction to subtract from the level measured with the source
operating, read from the stepped Table 2 of IEC 61063 at the difference
between that level and the background level alone: 3 dB at a difference
of 3 dB, 2 dB at 4 and 5 dB, 1 dB at 6 to 8 dB, 0,5 dB at 9 and 10 dB and
0,0 dB above 10 dB.

The last row is read first, on the difference as measured: any difference
above 10 dB is "> 10" and takes no correction, 10,2 dB as much as 11 dB.
Between 3 and 10 dB the table is indexed in whole decibels, so the
difference is rounded to the nearest one (halves upwards) before it is
read; 9,5 dB up to 10 dB takes the 0,5 dB of the row 10. That is how the
library reads the stepped table of ISO/TS 7849-1, whose open row is also
judged before the rounding. Table 2 prints nothing below 3 dB, the
criterion of 4.2, where "a valid measurement of the machine under test
cannot be made": there the 3 dB of the first row is returned. The level
it leaves is still an upper limit, because the exact correction for a
smaller difference is larger, which is how the NOTE of 4.2 lets such a
result be used, and it is the value ISO 3746:2010 8.3.3 prints for the
same case. [`turbine_sound_power`](/phonometry/reference/api/power/turbine-noise/#turbine_sound_power) marks such a determination as an
upper limit.

This is not the $K_{1\mathrm{A}} = -10 \lg(1 - 10^{-0.1 \Delta L})$
of ISO 3746:2010 Equation (12). The steps depart from it by a few tenths
of a decibel either way, and they are applied position by position rather
than to the surface-averaged level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference_db` | The level with the source operating less the background level, at each position, in dB (scalar or 1-D array). |

**Returns:** The correction to subtract, in dB: a `float` for a scalar, an array for an array.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a difference is not finite. |

## turbine_environmental_correction

```python
turbine_environmental_correction(
    surface_area_m2: float,
    *,
    absorption_area_m2: float | None = None,
    volume_m3: float | None = None,
    reverberation_time_s: float | None = None,
) -> TurbineEnvironmentalCorrection
```

Environmental correction $K$ from the room absorption (A.3.1).

Figure A.3 prints the curve and its formula,

$$
K = 10 \lg\left[1 + \frac{4}{A/S}\right],
$$

with $A$ the equivalent sound absorption area of the room, either
given or from its reverberation time, $A = 0{,}16\,V/T$ (A.3.1),
and $S$ the area of the measurement surface from Equation (1). It is
the $K_2$ of ISO 3744 and ISO 3746. The result is not refused above
the 7 dB the standard allows; [`check_turbine_test_environment`](/phonometry/reference/api/power/turbine-noise/#check_turbine_test_environment) is
the judgement, and [`turbine_sound_power`](/phonometry/reference/api/power/turbine-noise/#turbine_sound_power) warns.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface_area_m2` | $S$, in square metres. |
| `absorption_area_m2` | $A$, in square metres; or give `volume_m3` and `reverberation_time_s` instead. |
| `volume_m3` | $V$ of the test room, in cubic metres. |
| `reverberation_time_s` | $T$ of the test room with A-weighting on the receiving system, in seconds. |

**Returns:** The correction and the room data it came from.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | unless exactly one of the two routes to $A$ is given whole, or for a non-positive input. |

## turbine_measurement_surface

```python
turbine_measurement_surface(
    reference_boxes: Sequence[TurbineReferenceBox],
) -> TurbineMeasurementSurface
```

Measurement surface of a turbine set and its area $S$ (Equation (1)).

The parallelepipeds of the measurement surface are the reference boxes
spaced out by the measurement distance $d = 1$ m (7.1): each is
$2d$ wider and $d$ taller than its box, and the first and the
last are $d$ longer, at the two ends of the set. Then

$$
S = 2\,h_\mathrm{max}\,b_\mathrm{max} + \sum_{i=1}^{Z} l_i\,(2 h_i + b_i).
$$

A single box gives the enveloping parallelepiped of ISO 3746,
$l b + 2 l h + 2 b h$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_boxes` | The reference boxes in order along the shaft, from the turbine end (Figure 2): one [`TurbineReferenceBox`](/phonometry/reference/api/power/turbine-noise/#turbinereferencebox) per part. |

**Returns:** The surface, its parallelepipeds and its area.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if no box is given or an entry is not a [`TurbineReferenceBox`](/phonometry/reference/api/power/turbine-noise/#turbinereferencebox). |

## turbine_microphone_positions

```python
turbine_microphone_positions(
    surface: TurbineMeasurementSurface,
    *,
    microphone_height_m: float,
    spacing_m: float,
    turbine_boxes: int = 1,
    include_overhead: bool = True,
) -> TurbineMicrophoneArray
```

Key and additional microphone positions on the measurement surface (7.2).

The five key positions follow Figure 2. Position 1 is the centre of the
front end and 5 the centre of the rear end; 2 and 4 are on the two long
sides and 3 is overhead, all three in the plane between the turbine and
the driven machinery, at the outer corner of the wider (or taller) of the
two parallelepipeds that meet there, as both drawings of Figure 2 place
them. A set in a single box has that plane at mid-length.

The additional positions are "arranged at equal distances" beginning at the
key positions (7.2.2). They lie on two paths. One runs round the sides at
the microphone height, 1 to 2, 2 to 5, 5 to 4 and 4 to 1, as the plans of
Figure 2 draw it. The other, the overhead line, runs in the vertical plane
of the shaft from 1 up the front end, across the top and its steps to 3,
and on to the rear end and down it to 5, as the elevations draw it with a
position on the front end above key position 1. Each run between two key
positions is divided into the fewest equal intervals no longer than
`spacing_m`, and a position stands at each division. The two paths are
divided each on its own, so their stations need not line up in the
transverse sections the drawings of Figure 2 show; 7.2.2 asks only for
equal distances. The distance has to be short enough to put "at least one
measurement section at each casing"; the library judges it per
parallelepiped, and when a spacing leaves one with no position on its
long sides a [`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning) is emitted
and [`TurbineMicrophoneArray.every_box_sampled`](/phonometry/reference/api/power/turbine-noise/#turbinemicrophonearrayevery_box_sampled) is `False`.

Figure 2 draws the positions round the sides on one horizontal row
without dimensioning its height, so the height is the caller's, and it has
to lie on the sides of every parallelepiped.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface` | The measurement surface, from [`turbine_measurement_surface`](/phonometry/reference/api/power/turbine-noise/#turbine_measurement_surface). |
| `microphone_height_m` | Height of the row round the sides, in metres, above the reflecting plane and no higher than the lowest parallelepiped. |
| `spacing_m` | The largest distance between neighbouring positions along the path, in metres. |
| `turbine_boxes` | How many reference boxes, from the front, enclose the turbine (1 for Figure 2 a, 2 for Figure 2 b, where the HP and IP casings share one box and the LP turbine has its own). Ignored for a set in a single box. |
| `include_overhead` | `False` leaves the overhead line out, key position 3 with it, as the NOTE of 7.2.2 allows once a preliminary investigation has shown the overhead positions move the sound power level by no more than 1,0 dB (see [`TurbineSoundPowerResult.overhead_effect_db`](/phonometry/reference/api/power/turbine-noise/#turbinesoundpowerresultoverhead_effect_db)). |

**Returns:** The positions, their labels and the overhead mask.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a height outside the sides, a non-positive spacing, or a `turbine_boxes` that leaves no driven machinery. |

## turbine_noise_declaration

```python
turbine_noise_declaration(
    determinations: Mapping[str, TurbineSoundPowerResult],
    *,
    turbine: str,
    noise_control: str,
    measured_at: str,
    tonal: bool,
) -> TurbineNoiseDeclaration
```

The minimum report of clause 10 for one or more operating conditions.

Clause 10 asks the report to state that the A-weighted sound power level
"has been obtained in full conformity with the procedures of this
standard" and is expressed in decibels above 1 pW, and to give at least:
a) the turbine, with its noise control screens and enclosures; b) the
operating conditions; c) the A-weighted levels at each position, corrected
for the background; d) the A-weighted surface sound pressure level(s);
e) the A-weighted sound power level(s); f) the date and time of the
measurements. 6.2 suggests repeating the measurement under every typical
sustained load, 25 %, 50 %, 75 % and 100 % of the rated load, to find the
noisiest, so a report may carry several conditions. The report keeps each
sound power level as determined, finds the noisiest condition on it, and
rounds it to the nearest whole decibel where it is reported (9.4 g).

A determination that is not in full conformity (an upper limit, or a
$K$ above 7 dB) cannot carry the statement, and is refused.

**Parameters**

| Name | Description |
| :--- | :--- |
| `determinations` | One [`TurbineSoundPowerResult`](/phonometry/reference/api/power/turbine-noise/#turbinesoundpowerresult) per operating condition, keyed by its description (`"100 % rated load"`). |
| `turbine` | Description of the turbine set, clause 10 a). |
| `noise_control` | The noise control screens and enclosures fitted, or `"none"`, clause 10 a). |
| `measured_at` | Date and time of the measurements, clause 10 f). |
| `tonal` | Whether the sound contains prominent discrete tones (Table 1). |

**Returns:** The report.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no determination, a determination that does not conform, or an empty description. |

## turbine_reference_source_correction

```python
turbine_reference_source_correction(
    sound_power_levels_db: ArrayLike,
    *,
    calibrated_level_db: float,
    machine_length_m: float,
) -> TurbineEnvironmentalCorrection
```

Environmental correction $K = L_W - L_{Wr}$ from a reference source (A.3.2).

$L_{Wr}$ is the calibrated sound power level of the reference sound
source, determined in a free field over a reflecting plane
($K = 0$), and $L_W$ the sound power level the same source
shows in the test room by the survey method of ISO 3746 with $K$
taken as zero, on a measurement surface 1 m from it. By the NOTE of A.3.2,
$L_W$ is the mean of two determinations, the source standing in the
middle of each longitudinal side of the turbine set; a machine longer than
10 m takes two more, with the source at each end. The NOTE says "mean
value" and does not say which mean; the library takes the arithmetic mean
of the determinations.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_power_levels_db` | The determinations of $L_W$, in dB: two for a machine up to 10 m long, four above. |
| `calibrated_level_db` | $L_{Wr}$, in dB re 1 pW. |
| `machine_length_m` | Length of the machine under test, in metres, which sets how many determinations are needed. |

**Returns:** The correction and the determinations it came from.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for the wrong number of determinations or a non-finite level. |

## turbine_sound_power

```python
turbine_sound_power(
    pressure_levels_db: ArrayLike,
    *,
    surface_area_m2: float,
    background_levels_db: ArrayLike | None,
    environmental_correction_db: float,
    overhead_mask: ArrayLike | None = None,
) -> TurbineSoundPowerResult
```

Surface sound pressure level and sound power level of a turbine set (8.1 to 8.4).

Each position's level is first corrected for the background by Table 2
(8.1, [`turbine_background_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_background_correction)); the corrected levels are
energy-averaged and the environmental correction subtracted, Equation (2),

$$
\overline{L_{p\mathrm{A}}} = 10 \lg\left[\frac{1}{N} \sum_{i=1}^{N} 10^{0.1 L_{p\mathrm{A}i}}\right] - K,
$$

and the surface term closes it, Equation (3),
$L_{W\mathrm{A}} = \overline{L_{p\mathrm{A}}} + 10 \lg(S/S_0)$.

A background less than 3 dB below at any position makes the result an
upper limit (4.2) and a $K$ above 7 dB puts the room outside the
standard (8.3); both emit a [`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning)
and leave [`TurbineSoundPowerResult.conforms`](/phonometry/reference/api/power/turbine-noise/#turbinesoundpowerresultconforms) `False`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `pressure_levels_db` | $L_{p\mathrm{A}i}$ with the turbine set operating, one per position, in dB re 20 µPa: at least the four key positions that remain once the overhead one is deleted. |
| `surface_area_m2` | $S$, from [`turbine_measurement_surface`](/phonometry/reference/api/power/turbine-noise/#turbine_measurement_surface), in square metres. |
| `background_levels_db` | The A-weighted background level at each position, in dB. It is often impossible to measure with the turbine stopped, and NOTE 1 of 8.1 allows it to be evaluated by computation instead. `None` states that no background was determined, and no correction is applied. |
| `environmental_correction_db` | $K$, in dB: from [`turbine_environmental_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_environmental_correction) or [`turbine_reference_source_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_reference_source_correction), or `0.0` outdoors (A.4). |
| `overhead_mask` | Which positions are overhead ([`TurbineMicrophoneArray.overhead_mask`](/phonometry/reference/api/power/turbine-noise/#turbinemicrophonearray)), for the effect of deleting them (NOTE of 7.2.2); `None` if not needed. |

**Returns:** The per-position levels, the surface level and the sound power level.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than four positions, arrays of different lengths or non-finite values. |

## TurbineEnvironmentalCorrection

```python
TurbineEnvironmentalCorrection(
    environmental_correction_db: float,
    method: Literal['absorption', 'reference source'],
    surface_area_m2: float | None = None,
    absorption_area_m2: float | None = None,
    reference_levels_db: np.ndarray | None = None,
    calibrated_level_db: float | None = None,
)
```

The environmental correction `K` of a test room (clause 8.2, Annex A).

Built by [`turbine_environmental_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_environmental_correction) (A.3.1, Figure A.3) or
by [`turbine_reference_source_correction`](/phonometry/reference/api/power/turbine-noise/#turbine_reference_source_correction) (A.3.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `environmental_correction_db` | $K$, in dB. |
| `method` | `"absorption"` (A.3.1) or `"reference source"` (A.3.2). |
| `surface_area_m2` | $S$ (A.3.1), in square metres, or `None`. |
| `absorption_area_m2` | $A$ (A.3.1), in square metres, or `None`. |
| `reference_levels_db` | The determinations of the reference source's sound power level $L_W$ (A.3.2), in dB, or `None`. |
| `calibrated_level_db` | $L_{Wr}$ (A.3.2), in dB, or `None`. |

### TurbineEnvironmentalCorrection.plot()

```python
TurbineEnvironmentalCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw Figure A.3 with this room on it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of Figure A.3. |

**Returns:** The axes.

### TurbineEnvironmentalCorrection.ratio

*property*

$A/S$, the abscissa of Figure A.3, or `None` (A.3.2).

## TurbineMeasurementSurface

```python
TurbineMeasurementSurface(
    reference_boxes: tuple[TurbineReferenceBox, ...],
    lengths_m: np.ndarray,
    widths_m: np.ndarray,
    heights_m: np.ndarray,
    area_m2: float,
    measurement_distance_m: float = 1.0,
)
```

The measurement surface of a turbine set and its area (clause 7.1).

Built by [`turbine_measurement_surface`](/phonometry/reference/api/power/turbine-noise/#turbine_measurement_surface). The parallelepipeds are the
reference boxes grown by the measurement distance on every side except the
floor: 1 m wider on each side, 1 m taller, and 1 m longer at each end of
the set.

**Attributes**

| Name | Description |
| :--- | :--- |
| `reference_boxes` | The reference boxes, in order along the shaft. |
| `lengths_m` | $l_i$ of each parallelepiped of the measurement surface, in metres. |
| `widths_m` | $b_i$, in metres. |
| `heights_m` | $h_i$, in metres. |
| `area_m2` | $S$ of Equation (1), in square metres. |
| `measurement_distance_m` | $d$, 1 m (7.1). |

### TurbineMeasurementSurface.enveloping_area_m2

*property*

The exact area of the stepped surface, in square metres.

The tops, the long sides and the two ends of the parallelepipeds, and
at each step the part of either cross-section the other does not
cover. Equation (1) counts every transverse face together as
$2 h_\mathrm{max} b_\mathrm{max}$, which is exactly their area
when the cross-sections shrink from one largest section towards both
ends, each containing the next, as in both drawings of Figure 2.
Otherwise it can err either way: it counts too much when the tallest
and the widest parallelepipeds are different ones, and too little when
a small section stands between two large ones.

**Returns:** The area of the surface as drawn, in square metres.

### TurbineMeasurementSurface.max_height_m

*property*

$h_\mathrm{max}$ of Equation (1), in metres.

### TurbineMeasurementSurface.max_width_m

*property*

$b_\mathrm{max}$ of Equation (1), in metres.

### TurbineMeasurementSurface.plot()

```python
TurbineMeasurementSurface.plot(
    ax: Axes | None = None,
    *,
    view: Literal['plan', 'elevation'] = 'plan',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the reference boxes and the measurement surface around them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `view` | `"plan"` (default), seen from above, or `"elevation"`, seen from the side. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the outline of the measurement surface. |

**Returns:** The axes.

### TurbineMeasurementSurface.x_edges_m

*property*

Where each parallelepiped starts and ends along the shaft, in metres.

**Returns:** `Z + 1` abscissae from the front end of the measurement surface (0) to its rear end.

## TurbineMicrophoneArray

```python
TurbineMicrophoneArray(
    surface: TurbineMeasurementSurface,
    positions_m: np.ndarray,
    labels: tuple[str, ...],
    overhead_mask: np.ndarray,
    microphone_height_m: float,
    spacing_m: float,
    turbine_boxes: int,
    positions_per_box: tuple[int, ...],
)
```

The key and additional microphone positions of Figure 2 (clause 7.2).

Built by [`turbine_microphone_positions`](/phonometry/reference/api/power/turbine-noise/#turbine_microphone_positions). Coordinates are in metres:
`x` along the shaft from the front end of the measurement surface, `y`
across it from the shaft line (key position 2 on the positive side) and
`z` above the reflecting plane. The positions run once round the surface
at the microphone height, from key position 1 through 2, 5 and 4 back
towards 1, and then along the overhead line in the vertical plane of the
shaft: up the front end above key position 1, across the top through 3
and down the rear end towards 5.

**Attributes**

| Name | Description |
| :--- | :--- |
| `surface` | The measurement surface the positions lie on. |
| `positions_m` | One row `(x, y, z)` per position, in metres. |
| `labels` | `"1"` to `"5"` for the key positions, `""` for the additional ones. |
| `overhead_mask` | Which positions are on the overhead line, the ends above the row round the sides and the top of the surface. |
| `microphone_height_m` | Height of the positions round the sides, in metres. |
| `spacing_m` | The largest distance allowed between neighbours, in metres. |
| `turbine_boxes` | How many of the reference boxes enclose the turbine; key positions 2, 3 and 4 stand in the plane that follows them. |
| `positions_per_box` | Positions on one long side within the length of each parallelepiped (the other side mirrors them). |

### TurbineMicrophoneArray.count

*property*

Number of positions, key and additional, overhead included.

### TurbineMicrophoneArray.every_box_sampled

*property*

Whether every parallelepiped has a position on its long sides (7.2.2).

7.2.2 asks for "at least one measurement section at each casing". The
library knows the reference boxes, not the casings inside them, so it
judges each parallelepiped: where one box holds several casings (the
HP and IP turbines of Figure 2 b), whether each of them is reached is
read from `positions_m`.

### TurbineMicrophoneArray.key_mask

*property*

Which positions are the five key positions of Figure 2.

### TurbineMicrophoneArray.plot()

```python
TurbineMicrophoneArray.plot(
    ax: Axes | None = None,
    *,
    view: Literal['plan', 'elevation'] = 'plan',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the positions on the measurement surface, as Figure 2 does.

Key positions are crosses with their number, additional ones circles.
In elevation only the near side is drawn, the side of key position 4
as in both elevations of Figure 2, with the overhead line.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `view` | `"plan"` (default) or `"elevation"`. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the outline of the measurement surface. |

**Returns:** The axes.

## TurbineNoiseDeclaration

```python
TurbineNoiseDeclaration(
    turbine: str,
    noise_control: str,
    measured_at: str,
    tonal: bool,
    operating_conditions: tuple[str, ...],
    position_levels_db: tuple[np.ndarray, ...],
    surface_pressure_levels_db: tuple[float, ...],
    sound_power_levels_db: tuple[float, ...],
)
```

The minimum report of clause 10, one row per operating condition.

Built by [`turbine_noise_declaration`](/phonometry/reference/api/power/turbine-noise/#turbine_noise_declaration).

**Attributes**

| Name | Description |
| :--- | :--- |
| `turbine` | Description of the turbine set under test, clause 10 a). |
| `noise_control` | The noise control screens and enclosures fitted, clause 10 a) (and 1.1.5). |
| `measured_at` | Date and time of the measurements, clause 10 f). |
| `tonal` | Whether the sound contains prominent discrete tones, which selects the row of Table 1. |
| `operating_conditions` | The operating conditions, clause 10 b). |
| `position_levels_db` | The A-weighted levels at each position, corrected for the background, per condition, clause 10 c). |
| `surface_pressure_levels_db` | The A-weighted surface sound pressure level per condition, clause 10 d), in dB re 20 µPa. |
| `sound_power_levels_db` | The A-weighted sound power level per condition as determined by Equation (3), in dB re 1 pW; clause 10 e) reports it as `reported_sound_power_levels_db`. |

### TurbineNoiseDeclaration.loudest_condition

*property*

The operating condition with the highest sound power level (6.2).

Found on the levels before the rounding of 9.4 g, so two conditions
that report the same whole decibel are still told apart; on an exact
tie it is the first condition listed.

### TurbineNoiseDeclaration.plot()

```python
TurbineNoiseDeclaration.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the sound power level of each operating condition.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars. |

**Returns:** The axes.

### TurbineNoiseDeclaration.reported_sound_power_levels_db

*property*

The sound power levels rounded to the nearest whole decibel (9.4 g).

What clause 10 e) reports, in dB re 1 pW, one per operating condition.

### TurbineNoiseDeclaration.standard_deviation_db

*property*

The standard deviation of Table 1 for this kind of sound, in dB.

5 dB for a source with prominent discrete tones, 4 dB for a
broadband one: the uncertainty measurements to the survey method tend
to stay within (1.2).

### TurbineNoiseDeclaration.statement

*property*

The statement clause 10 requires the report to contain.

## TurbineReferenceBox

```python
TurbineReferenceBox(
    length_m: float,
    width_m: float,
    height_m: float,
    label: str = '',
)
```

One reference box of a turbine set (clause 7.1).

The smallest rectangular box that just encloses one part of the set, its
lagging and any noise control screen or enclosure included, and
terminates on the reflecting plane (3.5 and 7.1). The boxes of a set stand
in juxtaposition along its shaft, in the order they are passed, each
centred on the shaft line. A set whose boxes are flush on one long side
and step only on the other, as Figure 2 a draws it, is modelled as if
every box were centred: Equation (1) does not change, but beside a
narrower box the positions of each long side stand half the difference in
width across from where the drawing puts them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `length_m` | Length along the shaft, in metres. |
| `width_m` | Width across the shaft, in metres. |
| `height_m` | Height above the reflecting plane, in metres. |
| `label` | What the box encloses, for the figure (`"LP turbine"`). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a dimension is not a positive finite number. |

## TurbineSoundPowerResult

```python
TurbineSoundPowerResult(
    pressure_levels_db: np.ndarray,
    background_levels_db: np.ndarray | None,
    background_corrections_db: np.ndarray,
    corrected_levels_db: np.ndarray,
    environmental_correction_db: float,
    surface_area_m2: float,
    surface_pressure_level_db: float,
    sound_power_level_db: float,
    overhead_mask: np.ndarray | None = None,
)
```

A-weighted surface sound pressure level and sound power level (8.3, 8.4).

Built by [`turbine_sound_power`](/phonometry/reference/api/power/turbine-noise/#turbine_sound_power).

**Attributes**

| Name | Description |
| :--- | :--- |
| `pressure_levels_db` | $L_{p\mathrm{A}i}$ measured with the turbine set operating, one per position, in dB re 20 µPa. |
| `background_levels_db` | The background level at each position, in dB, or `None` when it was not determined. |
| `background_corrections_db` | The correction of Table 2 at each position, in dB (zero where no background was given). |
| `corrected_levels_db` | The levels after 8.1, in dB. |
| `environmental_correction_db` | $K$, in dB. |
| `surface_area_m2` | $S$, in square metres. |
| `surface_pressure_level_db` | $\overline{L_{p\mathrm{A}}}$ of Equation (2), $K$ subtracted, in dB re 20 µPa. |
| `sound_power_level_db` | $L_{W\mathrm{A}}$ of Equation (3), in dB re 1 pW. |
| `overhead_mask` | Which positions are overhead, or `None`. |

### TurbineSoundPowerResult.arithmetic_mean_allowed

*property*

Whether the range of the position levels is within 5 dB (NOTE of 8.3).

### TurbineSoundPowerResult.arithmetic_mean_db

*property*

The plain average of the corrected position levels, $K$ subtracted.

The NOTE of 8.3 allows it in place of Equation (2) when
`level_range_db` does not exceed 5 dB, and says it "should not
differ by more than 0,7 dB" from Equation (2). It is never above the
energy average, and within a 5 dB range it trails it by at most
0,707 dB (two levels 5 dB apart, the louder at 41 % of the positions),
the NOTE's 0,7 dB to its one decimal.

### TurbineSoundPowerResult.conforms

*property*

Whether the determination is in full conformity with the standard.

Every background at least 3 dB below (4.2) and $K$ within 7 dB
(8.3). Only such a determination can carry the statement of clause 10.

### TurbineSoundPowerResult.level_differences_db

*property*

The level with the source operating less the background, per position.

### TurbineSoundPowerResult.level_range_db

*property*

The range of the corrected position levels, in dB.

### TurbineSoundPowerResult.limited_positions

*property*

Per position, whether its background was less than 3 dB below (4.2).

**Returns:** One boolean per position, `True` where the position makes the determination an upper limit, or `None` without a background.

### TurbineSoundPowerResult.overhead_effect_db

*property*

How much the overhead positions move $L_{W\mathrm{A}}$, in dB.

The sound power level from every position less the one without the
overhead positions, on the same surface. The NOTE of 7.2.2 lets the
overhead positions be deleted when this is within 1,0 dB. `None`
without an overhead mask, or when every position or none is overhead.

### TurbineSoundPowerResult.overhead_may_be_deleted

*property*

Whether the overhead positions move the level by no more than 1,0 dB.

### TurbineSoundPowerResult.plot()

```python
TurbineSoundPowerResult.plot(
    ax: Axes | None = None,
    *,
    position_labels: Sequence[str] | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the corrected level at each position with the surface level.

The bars stand in the order the levels were given. Pass the
[`TurbineMicrophoneArray.labels`](/phonometry/reference/api/power/turbine-noise/#turbinemicrophonearray) of the array they were measured
on and the axis names the key positions as Figure 2 numbers them;
without them it counts the bars from 1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `position_labels` | One label per position, `"1"` to `"5"` for the key positions and `""` for the others, or `None`. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars of the corrected levels. |

**Returns:** The axes.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `position_labels` does not have one entry per position. |

### TurbineSoundPowerResult.reported_sound_power_level_db

*property*

$L_{W\mathrm{A}}$ rounded to the nearest whole decibel (9.4 g).

### TurbineSoundPowerResult.upper_limit

*property*

Whether a position's background was less than 3 dB below (4.2).

Then no valid measurement could be made, and the result is only an
indication of the upper limit of the sound power level.

## TurbineTestEnvironmentCheck

```python
TurbineTestEnvironmentCheck(
    environmental_correction_db: float,
    ratio: float | None,
    wind_speed_m_s: float | None = None,
)
```

Whether the test environment qualifies for IEC 61063 (A.3.3, 4.3).

Built by [`check_turbine_test_environment`](/phonometry/reference/api/power/turbine-noise/#check_turbine_test_environment). The verdicts are read
from the correction and the wind speed against the 7 dB, 6 m/s and
1 m/s the standard prints, so they are not fields.

**Attributes**

| Name | Description |
| :--- | :--- |
| `environmental_correction_db` | $K$, in dB. |
| `ratio` | $A/S$, when the correction came from the room absorption, else `None`. |
| `wind_speed_m_s` | The wind speed outdoors, in m/s, or `None`. |

### TurbineTestEnvironmentCheck.correction_ok

*property*

$K \le 7$ dB (A.3.3).

### TurbineTestEnvironmentCheck.passes

*property*

The verdict: the environment qualifies for measurements to the standard.

### TurbineTestEnvironmentCheck.plot()

```python
TurbineTestEnvironmentCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw Figure A.3 with the 7 dB limit and this environment on it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of Figure A.3. |

**Returns:** The axes.

### TurbineTestEnvironmentCheck.wind_ok

*property*

The wind speed is below 6 m/s (4.3), or `None` indoors.

### TurbineTestEnvironmentCheck.windscreen_advised

*property*

The wind is above 1 m/s, where 4.3 asks for a windscreen.
