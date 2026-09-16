---
title: "room.spatial_decay"
description: "Spatial sound distribution curves in workrooms (ISO 14257:2001)."
sidebar:
  label: "spatial_decay"
---

Spatial sound distribution curves in workrooms (ISO 14257:2001).

A workroom is not a reverberation room and it is not a free field. Put a known
source in it, walk away from it with a meter, and the level falls off somewhere
between the 6 dB per distance doubling of a free field and the nothing at all
of a perfectly diffuse room. That curve is what this standard measures, and the
two numbers it derives from it are what a room is judged by:

* $\mathrm{DL}_2$, the **rate of spatial decay per distance doubling**,
  which says how much quieter it gets by walking away, and
* $\mathrm{DL}_\mathrm{f}$, the **excess of sound pressure level**, which
  says how much louder the room is than a free field would have been.

The quantity everything is built on is the sound distribution value, the level
at a point less the sound power level of the source that produced it, so that
the curve belongs to the room and not to the source:

$$
D_j(r) = L_{pj}(r) - L_{Wj} \tag{1}
$$

The reference curve is the same quantity in a free field, which is the inverse
square law written as a level:

$$
D_\mathrm{ref}(r) = 10 \lg \frac{r_0^2}{4 \pi r^2} = 20 \lg \frac{r_0}{r} - 11 \tag{2}
$$

with $r_0$ = 1 m. The two derived quantities are a least-squares slope
over a range of positions,

$$
\mathrm{DL}_2 = -0,3 \, \frac{z \sum D_i \lg(r_i/r_0) - \sum D_i \sum \lg(r_i/r_0)} {z \sum [\lg(r_i/r_0)]^2 - [\sum \lg(r_i/r_0)]^2} \tag{5}
$$

with $z = m - n + 1$, and the difference from the reference curve,

$$
\mathrm{DL}_\mathrm{f} = D - D_\mathrm{ref} \tag{6}
$$

averaged over a distance range by Equation (7) or read off the regression line
at one conventional distance by Equation (8).

**The 0,3 of Equation (5).** The slope of a least-squares fit of $D$
against $\lg r$ is a rate per decade; a doubling is $\lg 2$ of a
decade, which is 0,301 03. The clause prints 0,3, and that is what
[`DECADE_TO_DOUBLING`](/phonometry/reference/api/rooms/spatial-decay/#decade_to_doubling) carries, because the printed constant is what
reproduces the printed results. Equation (8) prints $\lg 2$ in full a page
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
[`NORMALIZED_OFFSET_DB`](/phonometry/reference/api/rooms/spatial-decay/#normalized_offset_db) carries the printed 6,2 on the same rule as the
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

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ADJACENT_BAND_LIMIT_DB

*Constant* (`float`).

```python
ADJACENT_BAND_LIMIT_DB = 8.0
```

## BackgroundMarginCheck

```python
BackgroundMarginCheck(
    margins_db: NDArray[np.float64],
    needs_correction: NDArray[np.bool_],
    unusable: NDArray[np.bool_],
    satisfied: bool,
)
```

Whether the levels clear the background by what 5.1.4 asks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `margins_db` | The level of the source less the background at each position and band given, in decibels, in the shape they came in. |
| `needs_correction` | True where the margin is under [`ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/rooms/spatial-decay/#iso14257_preferred_signal_to_background_db) and over [`ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/rooms/spatial-decay/#iso14257_min_signal_to_background_db), which is the window where the clause asks for the ISO 3744 background correction. |
| `unusable` | True where the margin is at or under [`ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/rooms/spatial-decay/#iso14257_min_signal_to_background_db), which the clause offers no correction for. |
| `satisfied` | True when every margin clears [`ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/rooms/spatial-decay/#iso14257_preferred_signal_to_background_db), which is the only case that needs nothing done to it. |

## check_background_margin

```python
check_background_margin(
    levels_db: ArrayLike,
    background_levels_db: ArrayLike,
) -> BackgroundMarginCheck
```

Does the source stand clear of the background? 5.1.4.

The clause asks for 10 dB at every position and in every octave band the
curve is measured over. Between 10 dB and 6 dB it asks for the background
correction of ISO 3744 ([`phonometry.emission.background_correction`](/phonometry/reference/api/building/lab-insulation/#background_correction))
before the levels are used; at 6 dB or less it asks for neither, because
there is no longer a source level to correct towards.

The verdict is returned rather than applied: correcting the levels here
would change a measured number behind the caller's back, and the correction
the clause names belongs to the standard that prints it. A margin under
10 dB anywhere also emits [`SpatialDecayWarning`](/phonometry/reference/api/rooms/spatial-decay/#spatialdecaywarning), so a curve computed
from levels nobody checked says so on the way past.

One octave band at a time, as every other function of clause 6 takes its
positions: the clause asks the same 10 dB of every band, and a curve is
read band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_p$ with the test source running, in decibels, one value per measured position of one octave band. |
| `background_levels_db` | The background at the same positions, in decibels, as a scalar or one value per position. |

**Returns:** The verdict, as a [`BackgroundMarginCheck`](/phonometry/reference/api/rooms/spatial-decay/#backgroundmargincheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that are not finite or do not match position for position. |

## corrected_distribution_value

```python
corrected_distribution_value(
    distribution_values_db: ArrayLike,
    measured_reference_db: ArrayLike,
    distances_m: ArrayLike,
    *,
    source_height_m: float = 0.0,
    path_height_m: float | None = None,
) -> NDArray[np.float64]
```

The Annex B correction for the source's own curve, Equation (B.1).

$$
D_{\mathrm{corr}\,j}(r) = 10 \lg\left[ 10^{D_j(r)/10} - 10^{D_{\mathrm{meas,ref}\,j}(r)/10} + 10^{D_\mathrm{floor,ref}(r)/10}\right] \ \text{dB}
$$

What the annex does is swap one reference curve for another: it takes the
source's measured free-field-over-a-reflecting-plane curve out of the
measurement and puts the theoretical one back, so that what is left is the
room. It matters where the room's own excess is small, which is where the
source's directivity and the floor reflection are a large part of what the
meter saw.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D_j(r)$ in the room, in decibels. |
| `measured_reference_db` | $D_{\mathrm{meas,ref}\,j}(r)$ measured for this source over a reflecting plane, in decibels. |
| `distances_m` | $r$ at each position, in metres. |
| `source_height_m` | $h_S$, in metres. |
| `path_height_m` | $h_P$, in metres. |

**Returns:** $D_{\mathrm{corr}\,j}(r)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match position for position, or a correction that leaves no energy at all. |

## DECADE_TO_DOUBLING

*Constant* (`float`).

```python
DECADE_TO_DOUBLING = 0.3
```

## distance_region

```python
distance_region(
    distance_m: float,
    *,
    near_limit_m: float = 5.0,
    far_limit_m: float = 16.0,
) -> str
```

Which of the three regions of 6.2 a distance falls in.

The near region runs from 1 m to $d_1$, the middle from $d_1$
to $d_2$ and the far one from $d_2$ out. The typical
boundaries are 5 m and 16 m; other values may be used and are then
recorded and reported, which is why they are arguments here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | The distance from the acoustical centre, in metres. |
| `near_limit_m` | $d_1$, in metres. |
| `far_limit_m` | $d_2$, in metres. |

**Returns:** `"near"`, `"middle"` or `"far"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive distance, boundaries that do not increase, a near boundary inside the first metre, which would leave the near region empty, or a distance inside that first metre, which the clause does not evaluate. |

## EVALUATION_DISTANCES_M

*Constant* (`dict`).

```python
EVALUATION_DISTANCES_M = {'near': 4.0, 'middle': 10.0, 'far': 30.0}
```

## floor_reference_value

```python
floor_reference_value(
    distances_m: ArrayLike,
    *,
    source_height_m: float = 0.0,
    path_height_m: float | None = None,
) -> NDArray[np.float64]
```

The reference curve over a reflecting plane, Equations (B.2) to (B.4).

$$
D_\mathrm{floor,ref}(r) = D_\mathrm{ref}(r) + 10 \lg\left(1 + \frac{r^2}{r^2 + 4 h_S h_P}\right) \ \text{dB}
$$

With the microphone path at the source height the product becomes
$4 h_S^2$, which is Equation (B.3); with the source on the floor the
whole bracket becomes 2 and the correction is the 3 dB of Equation (B.4),
the free field folded into a half space.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distances_m` | $r$ at each position, in metres. |
| `source_height_m` | $h_S$, in metres; zero for a source on the floor. |
| `path_height_m` | $h_P$, in metres; omit it for a path at the source height. |

**Returns:** $D_\mathrm{floor,ref}(r)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a distance that is not strictly positive or a negative height. |

## FREE_FIELD_OFFSET_DB

*Constant* (`float`).

```python
FREE_FIELD_OFFSET_DB = 11.0
```

## ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB

*Constant* (`float`).

```python
ISO14257_MIN_SIGNAL_TO_BACKGROUND_DB = 6.0
```

## ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB

*Constant* (`float`).

```python
ISO14257_PREFERRED_SIGNAL_TO_BACKGROUND_DB = 10.0
```

## ISO14257_REFERENCE_DISTANCE_M

*Constant* (`float`).

```python
ISO14257_REFERENCE_DISTANCE_M = 1.0
```

## level_excess

```python
level_excess(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
) -> NDArray[np.float64]
```

The excess over a free field at each position, Equation (6).

$$
\mathrm{DL}_\mathrm{f} = D - D_\mathrm{ref}
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D$ at each position, in decibels. |
| `distances_m` | $r$ at each position, in metres. |

**Returns:** $\mathrm{DL}_\mathrm{f}$ at each position, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match position for position. |

## level_excess_at

```python
level_excess_at(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
    distance_m: float,
) -> float
```

The excess read off the regression line at one distance, Equation (8).

$$
\mathrm{DL}'_{\mathrm{f}r} = \left(\sum_{i=n}^{m} \frac{D_i}{z}\right) + 20 \lg \frac{r}{r_0} + \frac{\mathrm{DL}_2(r_n, r_m)}{\lg 2} \left[\left(\sum_{i=n}^{m} \frac{\lg(r_i/r_0)}{z}\right) - \lg \frac{r}{r_0}\right] + 11 \ \text{dB}
$$

This is the height of the fitted line over the free-field line at a
conventional distance: 4 m for the near region, 10 m for the middle one and
30 m for the far one ([`EVALUATION_DISTANCES_M`](/phonometry/reference/api/rooms/spatial-decay/#evaluation_distances_m)). Unlike Equation (7)
it does not average the measured points, it reads the line, so a single
outlying position moves it much less.

Note that the clause divides by $\lg 2$ in full here while Equation
(5) multiplies by the rounded 0,3; the two constants differ by 0,3 % and
the errata registry records it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D_i$ at the positions of the range, in decibels. |
| `distances_m` | $r_i$ at the same positions, in metres. |
| `distance_m` | $r$, the distance to read at, in metres. |

**Returns:** $\mathrm{DL}'_{\mathrm{f}r}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match, fewer than two positions, or a non-positive distance. |

## MAX_DIRECTIVITY_INDEX_DB

*Constant* (`float`).

```python
MAX_DIRECTIVITY_INDEX_DB = 8.0
```

## mean_level_excess

```python
mean_level_excess(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
) -> float
```

The excess averaged over a distance range, Equation (7).

$$
\mathrm{DL}_\mathrm{f}(r_n, r_m) = \frac{\sum_{i=n+1}^{m} \left[(\mathrm{DL}_{\mathrm{f}i} + \mathrm{DL}_{\mathrm{f}i-1}) \lg(r_i/r_{i-1})\right]} {2 \lg(r_m/r_n)} \ \text{dB}
$$

It is the trapezoidal mean of the excess against the logarithm of the
distance, which is the axis the curve is drawn on, so a position twice as
far weighs the same as one twice as near rather than twice as much.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D$ at the positions of the range, in decibels. |
| `distances_m` | $r$ at the same positions, in metres, in increasing order. |

**Returns:** $\mathrm{DL}_\mathrm{f}(r_n, r_m)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match, fewer than two positions, or distances that do not increase. |

## MIN_SOURCE_TO_WALL_M

*Constant* (`float`).

```python
MIN_SOURCE_TO_WALL_M = 3.0
```

## NEAR_REGION_START_M

*Constant* (`float`).

```python
NEAR_REGION_START_M = 1.0
```

## normalized_distribution_value

```python
normalized_distribution_value(
    distribution_values_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> float
```

The curve collapsed onto A-weighted pink noise, Equation (4).

$$
D_\mathrm{Norm} = 10 \lg \sum_j 10^{(D_j + P_j)/10} \ \text{dB} - 6,2 \ \text{dB}
$$

with $P_j$ from Table 1. It is Equation (3) with one spectrum fixed,
and 4.2.3 says why that spectrum is a normalisation and not an average
industrial machine: the spectra met in practice are too varied for any
average to mean anything.

The 6,2 dB is the energy sum of the A-weighting curve printed to one
decimal, and the six printed weights of Table 1 sum to 6,251 5 dB, so the
printed equation returns a flat curve 0,05 dB high. It is used as printed:
the result is what a hand evaluation of the printed equation gives, which
is 0,05 dB above Annex C, normalised exactly (see the errata registry). For
the exact normalisation, which returns a flat curve unchanged, call
[`spectrum_distribution_value`](/phonometry/reference/api/rooms/spatial-decay/#spectrum_distribution_value) with the values of
[`PINK_NOISE_WEIGHTS_DB`](/phonometry/reference/api/rooms/spatial-decay/#pink_noise_weights_db) as the machine spectrum.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D_j$ in each band, in decibels, in the order of [`SPATIAL_DECAY_BANDS_HZ`](/phonometry/reference/api/rooms/spatial-decay/#spatial_decay_bands_hz) unless `frequencies` says otherwise. |
| `frequencies` | The nominal octave centres the values belong to, in hertz. |

**Returns:** $D_\mathrm{Norm}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a count that is not the six bands of Table 1, or a frequency the table does not name. |

## NORMALIZED_OFFSET_DB

*Constant* (`float`).

```python
NORMALIZED_OFFSET_DB = 6.2
```

## OMNIDIRECTIONAL_RAMP_HZ

*Constant* (`tuple`).

```python
OMNIDIRECTIONAL_RAMP_HZ = (630.0, 1000.0)
```

## OMNIDIRECTIONAL_TOLERANCE_DB

*Constant* (`tuple`).

```python
OMNIDIRECTIONAL_TOLERANCE_DB = (2.0, 8.0)
```

## omnidirectionality_tolerance_db

```python
omnidirectionality_tolerance_db(frequency_hz: float) -> float
```

The directivity band a qualifying source stays inside, A.1.

The clause states the tolerance in three pieces: `+/- 2` dB in the
one-third-octave bands from 100 Hz to 630 Hz, a linear increase to
`+/- 8` dB between 630 Hz and 1 kHz, and `+/- 8` dB from 1 kHz to
5 kHz. The increase is taken here across the three one-third-octave bands
that span it, so 800 Hz is the midpoint at 5 dB; the clause says "linearly"
without saying linear in what, and the band index is the only reading on
which the two endpoints land on printed bands.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | The one-third-octave centre, in hertz. |

**Returns:** The largest absolute directivity index allowed, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency. |

## PINK_NOISE_WEIGHTS_DB

*Constant* (`dict`).

```python
PINK_NOISE_WEIGHTS_DB = {125.0: -16.1, 250.0: -8.6, 500.0: -3.2, 1000.0: 0.0, 2000.0: 1.2, 4000.0: 1.0}
```

## PREFERRED_MIDDLE_LIMIT_M

*Constant* (`float`).

```python
PREFERRED_MIDDLE_LIMIT_M = 24.0
```

## reference_distribution_value

```python
reference_distribution_value(distances_m: ArrayLike) -> NDArray[np.float64]
```

The free-field reference curve, Equation (2).

$$
D_\mathrm{ref}(r) = 10 \lg \frac{r_0^2}{4 \pi r^2} = 20 \lg \frac{r_0}{r} - 11 \ \text{dB}
$$

The clause prints both forms and they are the same number to within the
rounding of the 11: $10 \lg 4\pi$ is 10,99. The printed 11 is what is
used here, because it is the curve the standard draws in its own figures.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distances_m` | $r$ at each position, in metres. |

**Returns:** $D_\mathrm{ref}(r)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a distance that is not strictly positive. |

## sound_distribution_value

```python
sound_distribution_value(
    levels_db: ArrayLike,
    sound_power_levels_db: ArrayLike,
) -> NDArray[np.float64]
```

The sound distribution value of a measured point, Equation (1).

$$
D_j(r) = L_{pj}(r) - L_{Wj}
$$

Subtracting the source's own sound power is what makes the curve a property
of the room: run the test again with a louder source and every value comes
back the same.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{pj}(r)$ at each position, in decibels. |
| `sound_power_levels_db` | $L_{Wj}$ of the source, in decibels, as a scalar or one value per position. |

**Returns:** $D_j(r)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that are not finite or do not broadcast. |

## SOURCE_ON_FLOOR_HEIGHT_M

*Constant* (`float`).

```python
SOURCE_ON_FLOOR_HEIGHT_M = 0.5
```

## SPATIAL_DECAY_BANDS_HZ

*Constant* (`tuple`).

```python
SPATIAL_DECAY_BANDS_HZ = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
```

## spatial_decay_curve

```python
spatial_decay_curve(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
    *,
    near_limit_m: float = 5.0,
    far_limit_m: float = 16.0,
    region: str = 'middle',
    band_hz: float | None = None,
) -> SpatialDecayResult
```

The curve of one region with its two descriptors, clause 6.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D$ at every measured position, in decibels, over the whole path. |
| `distances_m` | $r$ at the same positions, in metres, in increasing order. |
| `near_limit_m` | $d_1$ of 6.2, in metres. |
| `far_limit_m` | $d_2$ of 6.2, in metres. |
| `region` | `"near"`, `"middle"`, `"far"` or `"whole"`. |
| `band_hz` | The octave centre the curve belongs to, in hertz. |

**Returns:** The curve and its descriptors, as a [`SpatialDecayResult`](/phonometry/reference/api/rooms/spatial-decay/#spatialdecayresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown region, inputs that do not match, or a region holding fewer than two measured positions. |

## spatial_decay_rate

```python
spatial_decay_rate(
    distribution_values_db: ArrayLike,
    distances_m: ArrayLike,
) -> float
```

The rate of spatial decay per distance doubling, Equation (5).

$$
\mathrm{DL}_2 = -0,3 \, \frac{z \sum D_i \lg(r_i/r_0) - \sum D_i \sum \lg(r_i/r_0)} {z \sum [\lg(r_i/r_0)]^2 - [\sum \lg(r_i/r_0)]^2} \ \text{dB}
$$

A free field gives 6 dB, a perfectly diffuse room gives 0, and a real
workroom sits between them: 4,6 dB in the middle range of the Annex C
example, which is a large and moderately fitted shipyard hall.

The sign is the way round a reader expects: the regression slope is
negative, so a room that gets quieter with distance returns a positive
number of decibels per doubling.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D_i$ at the positions of the range, in decibels. |
| `distances_m` | $r_i$ at the same positions, in metres. |

**Returns:** $\mathrm{DL}_2$, in decibels per distance doubling.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match position for position, fewer than two positions, or positions that are all at one distance. |

## SpatialDecayResult

```python
SpatialDecayResult(
    distances_m: NDArray[np.float64],
    distribution_values_db: NDArray[np.float64],
    reference_values_db: NDArray[np.float64],
    level_excess_db: NDArray[np.float64],
    decay_rate_db: float,
    mean_excess_db: float,
    region: str,
    band_hz: float | None = None,
)
```

A spatial sound distribution curve and what clause 6 reads off it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distances_m` | The distance of each microphone position from the acoustical centre of the source, in metres. |
| `distribution_values_db` | $D$ at each position, in decibels. |
| `reference_values_db` | $D_\mathrm{ref}$ at each position, in decibels. |
| `level_excess_db` | $\mathrm{DL}_\mathrm{f}$ at each position, in decibels. |
| `decay_rate_db` | $\mathrm{DL}_2$ over the range, in decibels per distance doubling. |
| `mean_excess_db` | $\mathrm{DL}_\mathrm{f}(r_n, r_m)$ over the range, in decibels. |
| `region` | `"near"`, `"middle"`, `"far"` or `"whole"`. |
| `band_hz` | The nominal octave centre the curve belongs to, in hertz, or `None` for a curve that stands for a spectrum. |

### SpatialDecayResult.plot()

```python
SpatialDecayResult.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Draw the curve, the free-field reference and the fitted slope.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `kwargs` | Passed to the renderer, including `language`. |

**Returns:** The axes drawn on.

## SpatialDecayWarning

The measurement is outside a condition ISO 14257 states.

## spectrum_distribution_value

```python
spectrum_distribution_value(
    distribution_values_db: ArrayLike,
    machine_power_levels_db: ArrayLike,
) -> float
```

The curve collapsed onto one machine's spectrum, Equation (3).

$$
D_S(r) = 10 \lg \frac{\sum_j 10^{(D_j(r) + L_{W\mathrm{mach}\,j})/10}} {\sum_j 10^{L_{W\mathrm{mach}\,j}/10}} \ \text{dB}
$$

The octave-band curve says what the room does to each band; this says what
the room does to one particular machine, which is the number a layout
decision is made on.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distribution_values_db` | $D_j(r)$ in each band, in decibels. |
| `machine_power_levels_db` | $L_{W\mathrm{mach}\,j}$ of the machine in the same bands, in decibels. |

**Returns:** $D_S(r)$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match band for band. |

## STABILITY_TOLERANCE_DB

*Constant* (`dict`).

```python
STABILITY_TOLERANCE_DB = {(100.0, 160.0): 1.0, (200.0, 5000.0): 0.5}
```

## TYPICAL_FAR_LIMIT_M

*Constant* (`float`).

```python
TYPICAL_FAR_LIMIT_M = 16.0
```

## TYPICAL_NEAR_LIMIT_M

*Constant* (`float`).

```python
TYPICAL_NEAR_LIMIT_M = 5.0
```
