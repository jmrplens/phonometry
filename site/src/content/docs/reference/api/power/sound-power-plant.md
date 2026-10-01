---
title: "emission.sound_power_plant"
description: "Sound power levels of multisource industrial plants for the evaluation of sound pressure levels in the environment: ISO 8297:1994, engineering method (grade 2)."
sidebar:
  label: "sound_power_plant"
---

Sound power levels of multisource industrial plants for the evaluation of
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
distances $d_i$ from each position to the nearest point of the plant
perimeter (9.1.2.2),

$$
\bar{d} = \frac{1}{N} \sum_{i=1}^{N} d_i ,
$$

shall exceed $0{,}05\sqrt{S_\mathrm{p}}$ or 5 m, whichever is the
greater, and shall not exceed $0{,}5\sqrt{S_\mathrm{p}}$ or 35 m,
whichever is the lesser, $S_\mathrm{p}$ being the plant area; the plant
area shall be seen from any point of the contour inside an aspect angle of at
most 180°; and adjacent positions shall be at most $2\bar{d}$ apart.
The microphone height (9.3) is

$$
h = H + 0{,}025\sqrt{S_\mathrm{m}} \quad \text{or 5 m, whichever is the greater,}
$$

with $S_\mathrm{m}$ the area the contour encloses and $H$ the
characteristic height of the plant, the mean height of its $n$ sources
(9.2 c), $H = \frac{1}{n}\sum_k h_k$.

Clause 10 then computes, band by band, the energy average of the levels
$L_{pi}$ at the $N$ positions (10.1),

$$
\overline{L_p} = 10 \lg\left[\frac{1}{N} \sum_{i=1}^{N} 10^{0{,}1 L_{pi}} \right] \ \mathrm{dB},
$$

replaces any level more than 5 dB above that average by
$\overline{L_p} + 5$ dB and averages again into
$\overline{L_p^*}$ when a contour further out is not practicable (10.2,
10.3), and adds four terms (10.4 to 10.8):

$$
L_W = \overline{L_p} + \Delta L_\mathrm{S} + \Delta L_\mathrm{F} + \Delta L_\mathrm{M} + \Delta L_\alpha ,
$$

$$
\Delta L_\mathrm{S} = 10 \lg\frac{2 S_\mathrm{m} + h l}{S_0}\ \mathrm{dB}, \qquad \Delta L_\mathrm{F} = \lg\frac{\bar{d}}{4\sqrt{S_\mathrm{p}}}\ \mathrm{dB},
$$

$$
\Delta L_\mathrm{M} = 3\left(1 - \frac{\theta}{90}\right) \mathrm{dB}, \qquad \Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}\ \mathrm{dB},
$$

with $l$ the length of the contour, $S_0 = 1$ m², $\theta$
the angle at which a directional microphone has lost 3 dB
($\Delta L_\mathrm{M} = 0$ for an omnidirectional one) and
$\alpha$ the attenuation coefficient of the air. The area term is the
measurement surface of ISO 3744: for a circular contour round a point source
on the ground, $2 S_\mathrm{m}$ is the hemisphere $2\pi r^2$ over
it and $h l$ the band of wall of height $h$ round it. The
proximity term has no factor 10: NOTE 11 says it lies between −0,9 dB and
−1,9 dB when 9.1 is met, and $\lg(0{,}5/4) = -0{,}903$ and
$\lg(0{,}05/4) = -1{,}903$ are its two ends. The A-weighted level of
10.9 is $L_{W\mathrm{A}} = 10 \lg \sum_j 10^{0{,}1(L_{Wj} + C_j)}$ dB,
with the octave-band $C_j$ of ISO 3744:2010 Annex E that every other
sound power method of this library uses.

**The air absorption.** Table 3 prints $\alpha$ per octave band at
15 °C and 70 %, "taken from ISO 3891", and asks for the values at the
measured temperature and humidity when the weather differs markedly. With no
weather given, [`plant_air_absorption_db_per_m`](/phonometry/reference/api/power/sound-power-plant/#plant_air_absorption_db_per_m-1) returns Table 3 as
printed; with a temperature and a humidity it evaluates the attenuation
coefficient of ISO 3891:1978 Annex A (SAE ARP 866A) at the one-third-octave
band centred on each octave, through the transcription
[`phonometry.aircraft.atmospheric_absorption.arp866a_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866a_attenuation) that
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
$\Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}$: passing 15 °C
and 70 % gives $0{,}0074\sqrt{S_\mathrm{m}}$ dB more at 8 kHz than
omitting the weather, 1,4 dB for a measurement area of 36 800 m². The
weather is therefore for the case 10.7 names, a weather that differs
markedly from 15 °C and 70 %; at or near those conditions Table 3 is the
reading the standard gives.

**What is judged and what is computed.** [`plant_measurement_contour`](/phonometry/reference/api/power/sound-power-plant/#plant_measurement_contour)
lays the positions on a contour given as a polygon round the plant polygon
and measures everything 9.1 and 9.2 ask for; [`plant_sound_power`](/phonometry/reference/api/power/sound-power-plant/#plant_sound_power) runs
clause 10 on the levels read there; [`check_plant_measurement`](/phonometry/reference/api/power/sound-power-plant/#check_plant_measurement) holds
the arrangement and the readings against the requirements of clauses 1.2,
6, 7.1, 9.1, 9.3, 9.5 and 10.2 and returns one verdict. Table 2 corrects the
levels for background noise and Table 1 states the uncertainty of the
method, which depends on $\bar{d}/\sqrt{S_\mathrm{p}}$ alone.
Clause 0.2 b) uses the method to find the contribution of particular parts
of a plant, and [`partial_plant_contributions`](/phonometry/reference/api/power/sound-power-plant/#partial_plant_contributions) combines the sound power
of parts measured on their own contours into the whole and each part's share
of it.

Source: ISO 8297:1994, read in the identical British adoption BS ISO
8297:1994 (clauses 0 to 12, Tables 1 to 3, Figure 1).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_plant_measurement

```python
check_plant_measurement(
    contour: PlantMeasurementContour,
    sound_power: PlantSoundPowerResult | None = None,
    *,
    measurement_time_s: float | ArrayLike | None = None,
    leq_range_db: float | ArrayLike | None = None,
) -> PlantMeasurementCheck
```

May clause 10 be applied to this measurement? ISO 8297 1.2, 6, 7.1, 9 and 10.2.

From the contour alone: the largest dimension of the plant area between
16 m and approximately 320 m (1.2); the average measurement distance
inside the window of 9.1.1 a); the plant area seen from every point of
the contour inside 180° (9.1.1 b); adjacent positions at most
$2\bar{d}$ apart (9.1.1 c); no more than 10 % of the positions
omitted (9.1.2.4); and the microphone at least 5 m high (9.3). With the
determination as well: the directional microphone's 3 dB angle above 30°
in every band (7.1), the background at least 6 dB below every level
(6 b), and the seven octave bands from 63 Hz to 4 kHz measured
(9.5.1 a). With the measurement times: at least 1 min at each position
(9.5.1). With the range of the integrated readings: an
$L_{\mathrm{eq},T}$ that "does not fluctuate by more than
± 0,5 dB" at each position (9.5.3), a range of at most 1 dB.

Four rows are advisory: the standard lets them go unmet provided the
report says so, so they do not decide [`PlantMeasurementCheck.passes`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcheckpasses).
The first is the height of 9.3 itself. 9.3 prescribes a height, not a
lower bound, so the row holds when the microphones stand at
$H + 0{,}025\sqrt{S_\mathrm{m}}$ (or 5 m) to within the ±5 % to
which 9.2 reads $H$ and $S_\mathrm{m}$ off the plan, and a
microphone lower (placed "as high as possible above the minimum height of
5 m" where the height cannot be reached) or higher than that is listed in
[`PlantMeasurementCheck.deviations`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcheckdeviations). The others are the background
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

**Parameters**

| Name | Description |
| :--- | :--- |
| `contour` | The contour, from [`plant_measurement_contour`](/phonometry/reference/api/power/sound-power-plant/#plant_measurement_contour). |
| `sound_power` | The determination made on it, or `None` to judge the arrangement alone. Its geometry must be the contour's. |
| `measurement_time_s` | The measurement time at each position, in seconds, one value or one per measured position; `None` to leave 9.5.1 unjudged. |
| `leq_range_db` | With an integrating instrument, the range (highest less lowest) over which the $L_{\mathrm{eq},T}$ reading still moved when it was taken, in decibels: one value, or one per measured position (or per position and band); `None` to leave 9.5.3 unjudged. A sound level meter's reading is judged by [`plant_steady_reading_db`](/phonometry/reference/api/power/sound-power-plant/#plant_steady_reading_db) instead (9.5.2). |

**Returns:** A [`PlantMeasurementCheck`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a determination whose geometry or number of positions is not the contour's, a non-positive time, or a negative range. |

## partial_plant_contributions

```python
partial_plant_contributions(
    parts: Sequence[PlantSoundPowerResult],
    *,
    names: Sequence[str] | None = None,
) -> PartialPlantContributions
```

Put together the parts of a plant measured on their own contours (0.2 b).

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

**Parameters**

| Name | Description |
| :--- | :--- |
| `parts` | The determinations of the parts, all over the same bands. |
| `names` | A name per part, or `None` for "Part 1", "Part 2", ... |

**Returns:** A [`PartialPlantContributions`](/phonometry/reference/api/power/sound-power-plant/#partialplantcontributions).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no parts, parts over different bands, or a name count that does not match. |

## PartialPlantContributions

```python
PartialPlantContributions(
    names: tuple[str, ...],
    frequencies_hz: NDArray[np.float64],
    part_levels_db: NDArray[np.float64],
)
```

The sound power of a plant put together from parts measured on their
own contours, and each part's share of it (0.2 b, c).

**Attributes**

| Name | Description |
| :--- | :--- |
| `names` | A name per part. |
| `frequencies_hz` | Nominal octave-band centres, in Hz. |
| `part_levels_db` | $L_W$ of each part, `(parts, bands)`, in dB re 1 pW. |

### PartialPlantContributions.a_weighted_contribution_db

*property*

Each part's $L_{W\mathrm{A}}$ less the total, in decibels.

### PartialPlantContributions.a_weighted_part_levels_db

*property*

$L_{W\mathrm{A}}$ of each part over the bands of 10.9, in dB re 1 pW.

### PartialPlantContributions.a_weighted_total_db

*property*

$L_{W\mathrm{A}}$ of the parts together, in dB re 1 pW.

### PartialPlantContributions.contribution_db

*property*

Each part's $L_W$ less the total, per band, in decibels (at most 0).

### PartialPlantContributions.plot()

```python
PartialPlantContributions.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each part's $L_W$ and their total, band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the total's bars. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### PartialPlantContributions.total_level_db

*property*

$L_W$ of the parts together, per band, in dB re 1 pW.

## PLANT_AIR_ABSORPTION_DB_PER_M

*Constant* (`mapping`).

```python
PLANT_AIR_ABSORPTION_DB_PER_M = {31.5: 0.0, 63.0: 0.0, 125.0: 0.0, 250.0: 0.001, 500.0: 0.002, 1000.0: 0.005, 2000.0: 0.01, 4000.0: 0.026, 8000.0: 0.046}
```

## plant_air_absorption_db_per_m

```python
plant_air_absorption_db_per_m(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float | None = None,
    relative_humidity_percent: float | None = None,
) -> NDArray[np.float64]
```

The attenuation coefficient of the air $\alpha$ of 10.7, in dB/m.

With no weather, Table 3 as printed, valid at 15 °C and 70 %. With the
temperature and relative humidity at the time of the measurement, which
Table 3 asks for when they "differ markedly" from those, the coefficient
of ISO 3891:1978 Annex A (SAE ARP 866A) that Table 3 was taken from,
evaluated at the one-third-octave band centred on each octave by
[`phonometry.aircraft.atmospheric_absorption.arp866a_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866a_attenuation)
(the parabolic reading of its Table 1 that reproduces ISO 3891 Table 10)
and turned from dB/100 m into dB/m. ISO 3891 gives no evaluation frequency
below 50 Hz, so the 31,5 Hz band keeps the 0 of Table 3.

The two do not meet at 15 °C and 70 %: the formula gives 0,000 59 dB/m
at 125 Hz, 0,025 05 dB/m at 4 kHz and 0,061 dB/m at 8 kHz where Table 3
prints 0, 0,026 and 0,046, and ISO 3891 Table 9 itself prints 0,1, 2,5
and 6,1 dB/100 m there. The other rows agree to the printed digit. In
the sound power the 8 kHz row is a step of
$0{,}5 \times 0{,}0148\sqrt{S_\mathrm{m}} \approx 0{,}0074\sqrt{S_\mathrm{m}}$ dB between omitting the weather and
passing 15 °C and 70 %, 1,4 dB over 36 800 m². Pass the weather only
when it differs markedly from 15 °C and 70 %, as Table 3 asks; the
standard sets no number for "markedly".

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal octave-band centres, 31,5 Hz to 8 kHz. |
| `temperature_c` | Air temperature at the measurement, in °C, or `None` for Table 3. |
| `relative_humidity_percent` | Relative humidity at the measurement, in percent (0 to 100), or `None` for Table 3. |

**Returns:** $\alpha$ per band, in dB/m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band outside the method, only one of the two weather values, or a humidity outside 0 % to 100 %. |

## PLANT_BACKGROUND_CORRECTION_DB

*Constant* (`mapping`).

```python
PLANT_BACKGROUND_CORRECTION_DB = {6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
```

## plant_background_correction_db

```python
plant_background_correction_db(
    level_difference_db: ArrayLike,
) -> float | NDArray[np.float64]
```

The background correction of Table 2, to subtract from the level measured.

The table is printed in whole decibels: 1 dB for a difference of 6, 7 or
8 dB, 0,5 dB for 9 or 10 dB, 0 above 10 dB, and "Measurement invalid"
below 6 dB. A difference between two rows is rounded to the nearest whole
decibel, a half going up; the two ends are compared as printed, so 5,9 dB
is invalid and 10,2 dB takes no correction. The difference is first
settled to nine decimals, so 20,4 - 14,4 dB, 5,999 999 999 999 998 in
binary, is the 6 dB it is, and 64,1 - 55,6 dB the 8,5 dB that rounds up.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference_db` | The level with the plant operating less the background level alone, in decibels: one value or an array. |

**Returns:** The correction, in decibels, a `float` for one difference and an array of the same shape otherwise.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-finite difference or one below 6 dB, which the table calls an invalid measurement. |

## plant_characteristic_height_m

```python
plant_characteristic_height_m(
    source_heights_m: ArrayLike,
    *,
    low_source_count: int = 0,
) -> float
```

The characteristic height of the plant $H$, 9.2 c) and NOTE 7.

The mean height of the midpoints of the noise sources, derived from the
equipment lists and the elevation drawings,
$H = \frac{1}{n}\sum_{k=1}^{n} h_k$. NOTE 7 lets a plant with ten or
more sources lower than 2 m count them approximately (to ±10 %) and take
each at 1 m: pass those sources as `low_source_count` and leave them out
of `source_heights_m`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_heights_m` | $h_k$, the height of the midpoint of each source not counted by NOTE 7, in metres. May be empty when every source is. |
| `low_source_count` | How many sources lower than 2 m NOTE 7 takes at 1 m; 0, or at least 10. |

**Returns:** $H$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a negative or non-finite height, a count from 1 to 9, or no sources at all. |

## plant_mean_distance_limits_m

```python
plant_mean_distance_limits_m(plant_area_m2: float) -> tuple[float, float]
```

The window of 9.1.1 a) for the average measurement distance $\bar{d}$.

$\bar{d}$ shall exceed $0{,}05\sqrt{S_\mathrm{p}}$ or 5 m,
whichever is the greater, and shall not exceed
$0{,}5\sqrt{S_\mathrm{p}}$ or 35 m, whichever is the lesser. The
lower bound is strict, so the window is empty at or below
$S_\mathrm{p} = 100$ m² and at or above $490\,000$ m²,
where no contour meets the clause.

**Parameters**

| Name | Description |
| :--- | :--- |
| `plant_area_m2` | $S_\mathrm{p}$, in square metres. |

**Returns:** `(lower, upper)` in metres: $\bar{d}$ must be above the first and at most the second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive area. |

## plant_measurement_contour

```python
plant_measurement_contour(
    plant_outline_m: ArrayLike,
    contour_m: ArrayLike,
    *,
    characteristic_height_m: float,
    position_count: int | None = None,
    omitted_positions: Sequence[int] = (),
) -> PlantMeasurementContour
```

Lay the measurement positions on a contour round the plant area, 9.1.

The positions are spaced equally along the contour from its first vertex.
With no `position_count`, the layout is the smallest that meets 9.1.1 c),
$D_\mathrm{m} = l/N \le 2\bar{d}$, with $\bar{d}$ taken over
that same layout, from three positions up. A layout of your own is given
as `position_count`, and the positions that could not be measured, a
river or a building in the way (9.1.2.4), as `omitted_positions`.

The contour is not required to meet 9.1.1 here: a first contour drawn on
the plan and found wanting is how the procedure starts (9.1.2.3, NOTE 6).
[`check_plant_measurement`](/phonometry/reference/api/power/sound-power-plant/#check_plant_measurement) says whether it does.

**Parameters**

| Name | Description |
| :--- | :--- |
| `plant_outline_m` | Vertices of the plant area, in metres. |
| `contour_m` | Vertices of the measurement contour round it, in metres. |
| `characteristic_height_m` | $H$, in metres, from [`plant_characteristic_height_m`](/phonometry/reference/api/power/sound-power-plant/#plant_characteristic_height_m). |
| `position_count` | Positions in the layout, or `None` for the fewest 9.1.1 c) allows. |
| `omitted_positions` | Indices into the layout of positions not measured; needs `position_count`, since the indices refer to it. |

**Returns:** A [`PlantMeasurementContour`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcontour).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for polygons that do not form a contour round the plant area, or omitted positions without a layout to refer to. |

## PLANT_METHOD_UNCERTAINTY_DB

*Constant* (`mapping`).

```python
PLANT_METHOD_UNCERTAINTY_DB = {0.05: (-3.5, 3.0), 0.1: (-2.5, 2.5), 0.2: (-2.5, 2.0), 0.5: (-2.0, 1.5)}
```

## plant_method_uncertainty_db

```python
plant_method_uncertainty_db(distance_ratio: float) -> tuple[float, float]
```

The uncertainty inherent in the method, Table 1: a 95 % confidence
interval for one determination, as `(lower, upper)` in decibels.

Table 1 prints four rows of $\bar{d}/\sqrt{S_\mathrm{p}}$ and says
nothing of the ratios between them. The interval narrows as the ratio
grows, so a ratio between two rows takes the row at or below it, the
wider of the two; nothing narrower than a printed row is claimed. The
range of the table, 0,05 to 0,5, is the range 9.1.1 a) allows.

NOTE 1 adds that where the background corrections of 9.5.4 cannot be
applied, the uncertainty may be greater than the table's.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_ratio` | $\bar{d}/\sqrt{S_\mathrm{p}}$. |

**Returns:** `(lower, upper)`, for example `(-3.5, 3.0)` at 0,05.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a ratio outside 0,05 to 0,5. |

## plant_microphone_height_m

```python
plant_microphone_height_m(
    characteristic_height_m: float,
    measurement_area_m2: float,
) -> float
```

The microphone height of 9.3: $h = H + 0{,}025\sqrt{S_\mathrm{m}}$
or 5 m, whichever is the greater.

Where this height cannot be reached for practical reasons, 9.3 asks for
the microphone as high as possible above 5 m and for the fact to be
reported; [`check_plant_measurement`](/phonometry/reference/api/power/sound-power-plant/#check_plant_measurement) reports it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `characteristic_height_m` | $H$, in metres. |
| `measurement_area_m2` | $S_\mathrm{m}$, the area the contour encloses, in square metres. |

**Returns:** $h$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a negative height or a non-positive area. |

## plant_sound_power

```python
plant_sound_power(
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
) -> PlantSoundPowerResult
```

The octave-band and A-weighted sound power level of a plant, clause 10.

Steps 1 to 9 of clause 10 on the levels read round the contour. With a
background given, every level is first corrected by Table 2 (9.5.4). The
levels are energy-averaged per band (step 1); where one exceeds the
average by more than 5 dB, 10.2 asks for a contour further from the
plant, and where that is not practicable replaces each such level by the
average plus 5 dB and averages again (steps 2 and 3), which is done here
with a [`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning), the result recording which levels were
replaced. Steps 4 to 7 add the area, proximity, microphone and air
absorption terms, step 8 sums them into $L_W$ and step 9 into
$L_{W\mathrm{A}}$; the module docstring writes them out.

The geometry is the one 9.2 measures on the plot plan, to within ±5 %;
[`PlantMeasurementContour.sound_power`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcontoursound_power) supplies it from polygons.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{pi}$, one row per position and one column per octave band, in dB re 20 µPa. |
| `frequencies_hz` | Nominal octave-band centres of the columns, 31,5 Hz to 8 kHz. |
| `measurement_area_m2` | $S_\mathrm{m}$, in square metres. |
| `contour_length_m` | $l$, in metres. |
| `microphone_height_m` | $h$, the height the microphones stood at, in metres. |
| `mean_distance_m` | $\bar{d}$, in metres. |
| `plant_area_m2` | $S_\mathrm{p}$, in square metres. |
| `background_levels_db` | The background alone at each position and band, in decibels, or `None` where the plant could not be stopped. |
| `directional_microphone_angle_deg` | $\theta$, the angle at which a directional microphone has lost 3 dB, in degrees, one value or one per band; `None` (default) for an omnidirectional microphone. |
| `temperature_c` | Air temperature at the measurement, in °C, or `None` for Table 3 at 15 °C. Pass it, with the humidity, only when the weather differs markedly from 15 °C and 70 %: the formula does not return Table 3 at those conditions, and passing them gives $0{,}0074\sqrt{S_\mathrm{m}}$ dB more at 8 kHz than omitting them (see [`plant_air_absorption_db_per_m`](/phonometry/reference/api/power/sound-power-plant/#plant_air_absorption_db_per_m-1)). |
| `relative_humidity_percent` | Relative humidity at the measurement, in percent, or `None` for Table 3 at 70 %. |

**Returns:** A [`PlantSoundPowerResult`](/phonometry/reference/api/power/sound-power-plant/#plantsoundpowerresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that do not match the bands, a background less than 6 dB below a level, a non-positive geometry, a microphone angle outside (0°, 90°], or half a weather. |

## plant_steady_reading_db

```python
plant_steady_reading_db(maximum_db: float, minimum_db: float) -> float
```

The level read on a sound level meter from a steady noise, 9.5.2.

With time weighting S, a needle that swings over less than 5 dB marks
the noise as steady for the standard, and the level is the arithmetic
mean of the maximum and the minimum over the observation. A wider swing
makes the noise non-steady, and 9.5.2 then asks for an integrating
instrument instead (9.5.3), whose steady $L_{\mathrm{eq},T}$ is
the level used; `leq_range_db` of [`check_plant_measurement`](/phonometry/reference/api/power/sound-power-plant/#check_plant_measurement)
judges that one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `maximum_db` | The highest level read, in decibels. |
| `minimum_db` | The lowest level read, in decibels. |

**Returns:** The level, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a minimum above the maximum, or a swing of 5 dB or more, the swing settled to nine decimals first, so 64,1 - 59,1 dB, 4,999 999 999 999 993 in binary, is the 5 dB it is. |

## PlantMeasurementCheck

```python
PlantMeasurementCheck(requirements: tuple[PlantRequirement, ...])
```

The arrangement and the readings of an ISO 8297 measurement against the
requirements of the standard.

**Attributes**

| Name | Description |
| :--- | :--- |
| `requirements` | One [`PlantRequirement`](/phonometry/reference/api/power/sound-power-plant/#plantrequirement) per requirement that could be evaluated, in the order of the clauses. |

### PlantMeasurementCheck.deviations

*property*

The advisory requirements that do not hold, which the report states.

### PlantMeasurementCheck.failures

*property*

The requirements that are not advisory and do not hold.

### PlantMeasurementCheck.passes

*property*

Whether every requirement that is not advisory holds.

True says the contour, the positions, the microphones and the readings
meet what ISO 8297 requires of them; the advisory rows that do not
hold (`deviations`) still go in the report.

### PlantMeasurementCheck.plot()

```python
PlantMeasurementCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot how far each requirement is inside or outside its limit.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### PlantMeasurementCheck.requirement()

```python
PlantMeasurementCheck.requirement(key: str) -> PlantRequirement
```

The requirement with this key.

**Parameters**

| Name | Description |
| :--- | :--- |
| `key` | Its [`PlantRequirement.key`](/phonometry/reference/api/power/sound-power-plant/#plantrequirement). |

**Returns:** The requirement.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | for a key this check does not carry. |

## PlantMeasurementContour

```python
PlantMeasurementContour(
    plant_outline_m: NDArray[np.float64],
    contour_m: NDArray[np.float64],
    characteristic_height_m: float,
    position_count: int,
    omitted_positions: tuple[int, ...] = (),
)
```

A measurement contour round a plant area on the plot plan, clauses 9.1 to 9.4.

The plant area and the contour are polygons in metres, in any consistent
plane coordinates; the contour encloses the plant and does not touch it.
The layout is `position_count` positions spaced equally along the
contour from its first vertex (9.1.2.4, $D_\mathrm{m} = l/N$), of
which those listed in `omitted_positions` could not be measured; every
quantity below is taken over the positions that were.

**Attributes**

| Name | Description |
| :--- | :--- |
| `plant_outline_m` | Vertices of the plant area, `(n, 2)`, in metres. |
| `contour_m` | Vertices of the measurement contour, `(n, 2)`, in metres. |
| `characteristic_height_m` | $H$, in metres (9.2 c). |
| `position_count` | Positions in the equidistant layout. |
| `omitted_positions` | Indices into the layout of the positions left out (9.1.2.4), in increasing order. |

### PlantMeasurementContour.contour_length_m

*property*

$l$, the length of the contour, in metres (9.2 a).

### PlantMeasurementContour.distance_ratio

*property*

$\bar{d}/\sqrt{S_\mathrm{p}}$, the argument of Table 1.

### PlantMeasurementContour.largest_plant_dimension_m

*property*

The largest horizontal dimension of the plant area, in metres (1.2).

### PlantMeasurementContour.layout_positions_m

*property*

Every position of the equidistant layout, omitted ones included,
`(position_count, 2)`, in metres.

### PlantMeasurementContour.mean_distance_limits_m

*property*

The window of 9.1.1 a) for this plant area, in metres.

### PlantMeasurementContour.mean_distance_m

*property*

$\bar{d}$, the average measurement distance, in metres (9.1.2.2).

### PlantMeasurementContour.measurement_area_m2

*property*

$S_\mathrm{m}$, the total area the contour encloses, plant
included, in square metres (3.4).

### PlantMeasurementContour.minimum_receiver_distance_m

*property*

The distance from the plant centre beyond which 0.2 a) lets the
result stand for a point source: 1,5 times the largest dimension, in
metres.

### PlantMeasurementContour.nearest_perimeter_points_m

*property*

The point of the plant perimeter nearest each measured position,
`(N, 2)`, in metres: the other end of each $d_i$.

### PlantMeasurementContour.omitted_percent

*property*

The share of the layout left out, in percent (9.1.2.4).

### PlantMeasurementContour.plant_area_m2

*property*

$S_\mathrm{p}$, the plant area, in square metres (3.3).

### PlantMeasurementContour.plant_centre_m

*property*

The geometrical centre of the plant area, where 0.2 a) places the
point source that stands for the plant, in metres.

### PlantMeasurementContour.plot()

```python
PlantMeasurementContour.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the plan: plant area, contour, positions and their microphone
directions, in the manner of Figure 1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the position markers. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### PlantMeasurementContour.position_spacing_m

*property*

$D_\mathrm{m}$, the distance between adjacent positions of the
layout along the contour, in metres (3.6).

### PlantMeasurementContour.prescribed_microphone_height_m

*property*

$h$ of 9.3 for this contour and plant, in metres.

### PlantMeasurementContour.sound_power()

```python
PlantMeasurementContour.sound_power(
    levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    microphone_height_m: float | None = None,
    background_levels_db: ArrayLike | None = None,
    directional_microphone_angle_deg: float | ArrayLike | None = None,
    temperature_c: float | None = None,
    relative_humidity_percent: float | None = None,
) -> PlantSoundPowerResult
```

Run clause 10 on the levels read at the measured positions of this contour.

[`plant_sound_power`](/phonometry/reference/api/power/sound-power-plant/#plant_sound_power) with the geometry of the contour; see there.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | One row per measured position, in the order of `positions_m`, one column per octave band, in decibels. |
| `frequencies_hz` | The octave-band centres of the columns, in Hz. |
| `microphone_height_m` | The height the microphones stood at, in metres; `None` for the height 9.3 prescribes. |
| `background_levels_db` | The background alone, same shape, or `None`. |
| `directional_microphone_angle_deg` | The 3 dB angle of a directional microphone, one or one per band, or `None`. |
| `temperature_c` | Air temperature at the measurement, in °C, or `None` for Table 3. |
| `relative_humidity_percent` | Relative humidity at the measurement, in percent, or `None` for Table 3. |

**Returns:** A [`PlantSoundPowerResult`](/phonometry/reference/api/power/sound-power-plant/#plantsoundpowerresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a number of rows that is not the number of measured positions, or any error of [`plant_sound_power`](/phonometry/reference/api/power/sound-power-plant/#plant_sound_power). |

## PlantRequirement

```python
PlantRequirement(
    key: str,
    clause: str,
    description: str,
    value: float,
    comparison: str,
    limit: float,
    unit: str,
    holds: bool,
    advisory: bool = False,
    tolerance: float = 0.0,
)
```

One requirement of ISO 8297 held against the measurement.

**Attributes**

| Name | Description |
| :--- | :--- |
| `key` | A stable identifier, such as `"mean_distance_min"`. |
| `clause` | The clause that sets it, such as `"9.1.1 a)"`; the omitted positions also name the item of clause 12 that reports them, `"9.1.2.4, 12 n)"`. |
| `description` | What is compared, in English. |
| `value` | The measured value, in `unit`. |
| `comparison` | How the value must stand to the limit: `">"`, `">="`, `"<="`, or `"="` for a value prescribed to within `tolerance` of the limit. |
| `limit` | The limit, in `unit`. |
| `unit` | The unit of the value and the limit, `""` for a count. |
| `holds` | Whether the requirement is met. |
| `advisory` | `True` where the standard allows the requirement to go unmet provided the report says so (the microphone height of 9.3, the preferred background margin of 6 b), the contour average of 10.2, the "approximately 320 m" of 1.2); such a requirement does not decide [`PlantMeasurementCheck.passes`](/phonometry/reference/api/power/sound-power-plant/#plantmeasurementcheckpasses). |
| `tolerance` | For `"="`, how far the value may stand from the limit, in `unit`; 0 for the other comparisons. |

### PlantRequirement.margin

*property*

How far the value is inside the limit, as a fraction of the limit:
positive where it holds by the comparison, negative where it does not.
For `"="` it is the room left inside the tolerance.

## PlantSoundPowerResult

```python
PlantSoundPowerResult(
    frequencies_hz: NDArray[np.float64],
    measured_levels_db: NDArray[np.float64],
    background_levels_db: NDArray[np.float64] | None,
    measurement_area_m2: float,
    contour_length_m: float,
    microphone_height_m: float,
    mean_distance_m: float,
    plant_area_m2: float,
    *,
    directional_microphone_angle_deg: NDArray[np.float64] | None = None,
    temperature_c: float | None = None,
    relative_humidity_percent: float | None = None,
)
```

The sound power level of a plant for the evaluation of levels in the
environment, clause 10 of ISO 8297.

The fields are the readings and the geometry the calculation was made
from; every step of clause 10 is derived from them on request, so a
result cannot carry a level that disagrees with its own inputs.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal octave-band centres, in Hz. |
| `measured_levels_db` | The levels read at the $N$ positions with the plant operating, `(N, bands)`, in dB re 20 µPa. |
| `background_levels_db` | The background alone at the same positions, or `None` when it could not be measured (9.5.4). |
| `measurement_area_m2` | $S_\mathrm{m}$, in square metres. |
| `contour_length_m` | $l$, in metres. |
| `microphone_height_m` | $h$, the height the microphones stood at, in metres. |
| `mean_distance_m` | $\bar{d}$, in metres. |
| `plant_area_m2` | $S_\mathrm{p}$, in square metres. |
| `directional_microphone_angle_deg` | $\theta$ per band, or `None` for an omnidirectional microphone. |
| `temperature_c` | Air temperature for the air absorption, in °C, or `None` for Table 3. |
| `relative_humidity_percent` | Relative humidity for the air absorption, in percent, or `None` for Table 3. |

### PlantSoundPowerResult.a_weighted_bands_hz

*property*

The bands summed into $L_{W\mathrm{A}}$: those the octave table
of ISO 3744:2010 Annex E weights, 63 Hz to 8 kHz. A 31,5 Hz band, which
NOTE 8 makes optional, is left out.

### PlantSoundPowerResult.a_weighted_sound_power_level_db

*property*

$L_{W\mathrm{A}} = 10 \lg \sum_j 10^{0{,}1(L_{Wj} + C_j)}$, in
dB re 1 pW (10.9).

### PlantSoundPowerResult.air_absorption_db_per_m

*property*

$\alpha$ per band, in dB/m (10.7, Table 3).

### PlantSoundPowerResult.air_absorption_term_db

*property*

$\Delta L_\alpha = 0{,}5\,\alpha\sqrt{S_\mathrm{m}}$ per
band, in decibels (10.7).

### PlantSoundPowerResult.area_term_db

*property*

$\Delta L_\mathrm{S} = 10 \lg[(2S_\mathrm{m} + hl)/S_0]$, in
decibels (10.4).

### PlantSoundPowerResult.background_correction_db

*property*

The Table 2 correction subtracted at each position and band, in
decibels; `None` with no background.

### PlantSoundPowerResult.background_margin_db

*property*

The level with the plant operating less the background, per position
and band, in decibels; `None` with no background.

### PlantSoundPowerResult.capped

*property*

Per position and band, whether $L_{pi}$ exceeds
$\overline{L_p}$ by more than 5 dB and was replaced (10.2).

The excess is settled to nine decimals first: a level 5 dB above the
energy mean comes out of the arithmetic a unit or two of the last
place of the levels either side of 5, which side depending on the
machine, and is not replaced.

### PlantSoundPowerResult.corrected_mean_level_db

*property*

$\overline{L_p^*}$ of 10.3, the average after replacing each
capped level by $\overline{L_p} + 5$ dB; equal to
$\overline{L_p}$ in a band with nothing capped.

### PlantSoundPowerResult.distance_ratio

*property*

$\bar{d}/\sqrt{S_\mathrm{p}}$, the argument of Table 1.

### PlantSoundPowerResult.levels_db

*property*

$L_{pi}$, the levels corrected for the background (9.5.4),
`(N, bands)`, in decibels.

### PlantSoundPowerResult.mean_level_db

*property*

$\overline{L_p}$, the energy average round the contour, per band
(10.1), in decibels.

### PlantSoundPowerResult.microphone_term_db

*property*

$\Delta L_\mathrm{M} = 3(1 - \theta/90)$ per band, 0 for an
omnidirectional microphone, in decibels (10.6).

### PlantSoundPowerResult.near_field_term_db

*property*

$\Delta L_\mathrm{F} = \lg[\bar{d}/(4\sqrt{S_\mathrm{p}})]$,
in decibels (10.5).

### PlantSoundPowerResult.plot()

```python
PlantSoundPowerResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the octave-band $L_W$ beside the contour average it was
built from, with $L_{W\mathrm{A}}$ in the title.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band bars. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### PlantSoundPowerResult.sound_power_level_db

*property*

$L_W$ per octave band, in dB re 1 pW (10.8).

### PlantSoundPowerResult.steps_2_3_applied

*property*

Whether 10.2 and 10.3 changed anything: then
$\overline{L_p^*}$ replaces $\overline{L_p}$ in 10.8.

### PlantSoundPowerResult.uncertainty_db

*property*

The 95 % interval of Table 1 as `(lower, upper)` in decibels, or
`None` where the distance ratio is outside the table (and outside
9.1.1 a).
