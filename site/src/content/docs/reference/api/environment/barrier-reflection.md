---
title: "environment.propagation.barrier_reflection"
description: "What a noise barrier sends back across the road, measured where it stands (EN 1793-5:2016)."
sidebar:
  label: "barrier_reflection"
---

What a noise barrier sends back across the road, measured where it stands (EN 1793-5:2016).

EN 1793-1 rates the absorption of a barrier in a reverberation room, on a
sample lying on the floor and a sound field arriving from every direction.
Beside a road the sound arrives from one side, the product is standing up,
and it is not the sample that was tested. EN 1793-5 measures the same property
in place, with a loudspeaker and nine microphones in front of the device, and
calls it the **sound reflection index** $RI$: the energy the device
reflects in each one-third octave band, as a fraction of what arrives.

The measurement
---------------

A loudspeaker stands $d_S$ = 1,50 m in front of the reference plane of
the device, at half its height. A vertical 3 x 3 grid of microphones, 0,40 m
apart, stands between them with its centre 0,25 m from the plane, so 1,25 m
from the loudspeaker. Each microphone records two impulse responses: one in
front of the device, and one in free field with the loudspeaker and the grid
turned away from everything, the ground included.

In front of the device the direct sound and the reflection overlap in the
first milliseconds. The free-field record *is* the direct sound, so it is
aligned onto the other record to a fiftieth of a sample, scaled to its peak and
subtracted (5.5.4, [`subtract_direct_sound`](/phonometry/reference/api/environment/barrier-reflection/#subtract_direct_sound)). What is left is the
reflection, and what cannot be removed is measured by the reduction factor
$R_{sub}$ of Formula (6).

The two components are then cut out with the **Adrienne temporal window**
(5.5.5, [`adrienne_reflection_window`](/phonometry/reference/api/environment/barrier-reflection/#adrienne_reflection_window)): a 0,5 ms left half of a
four-term Blackman-Harris window, a flat part, and a right half whose length is
3/7 of the flat part. The marker point where the flat part begins is placed
0,2 ms before the peak of each component (5.5.6).

The index
---------

Formula (1) averages, over the microphones, the ratio of the reflected to the
incident energy in each band, with three corrections; the gain factor divides
here, as the library computes it (see below):

$$
RI_j = \frac{1}{n_j} \sum_{k=1}^{n_j} \frac{\int_{\Delta f_j} |F[h_{r,k}(t)\, w_{r,k}(t)]|^2\, df} {\int_{\Delta f_j} |F[h_{i,k}(t)\, w_{i,k}(t)]|^2\, df} \, C_{geo,k}\, C_{dir,k}(\Delta f_j)\, /\, C_{gain,k}(\Delta f_g)
$$

* $C_{geo,k} = (d_{r,k}/d_{i,k})^2$ puts back the spherical spreading of
  the longer reflected path (Formula (2), Table 2).
* $C_{dir,k}$ puts back the loudspeaker directivity: the reflection left
  the loudspeaker at another angle than the direct sound (Formula (3),
  [`source_directivity_corrections`](/phonometry/reference/api/environment/barrier-reflection/#source_directivity_corrections)).
* $C_{gain,k}$ takes out a change of amplifier or microphone gain
  between the free-field and the in-front configurations (Formula (4)).

The last correction is a **division** here. Formula (1) prints it as a
multiplier, but Formula (4) defines it as the in-front incident energy over
the free-field one, which is the gain change itself; multiplying by it would
square the change rather than remove it. docs/ERRATA.md records the case.

In the bands of 100 Hz, 125 Hz and 160 Hz the average is over microphones 1 to
6 with the 7,9 ms window; from 200 Hz over all nine with the 6,0 ms window
(5.5.5). A device measured at several grid positions averages every
microphone of every position (5.6.2.3); Annex B reports the positions one by
one and their mean, which [`reflection_index_from_positions`](/phonometry/reference/api/environment/barrier-reflection/#reflection_index_from_positions) recomputes.

The single number
-----------------

$DL_{RI}$ weights $RI$ with the normalised traffic noise spectrum
of EN 1793-3 from the lowest reliable band upward (Formula (12)); it lives
with the other EN 1793 ratings as
[`sound_reflection_rating`](/phonometry/reference/api/environment/noise-reducing-devices/#sound_reflection_rating).

The low frequency limit
-----------------------

The window has to end before the ground reflection on the source side and the
waves diffracted by the edges of the device arrive, so a smaller device allows
a shorter window and a higher low frequency limit (5.5.7). The standard gives
the limit as three curves (Figure 14) without the formula behind them.
[`reflection_low_frequency_limit`](/phonometry/reference/api/environment/barrier-reflection/#reflection_low_frequency_limit) computes it by the construction of the
method's authors (Garai and Guidorzi, J. Acoust. Soc. Am. 108 (2000) 1054,
section III.D): the window ends where the first unwanted component arrives,
and its low frequency limit is the first notch of its spectrum
([`adrienne_low_frequency_limit_hz`](/phonometry/reference/api/environment/barrier-reflection/#adrienne_low_frequency_limit_hz), 162,5 Hz for 7,9 ms, which the
paper gives as about 160 Hz). Against the curves read off Figure 14 it
follows microphone 5 within 5 % from 2,75 m up (5,5 % below at 2,5 m). At
microphone 2 it comes out about 3 % to 10 % above the printed curve, set by
the top edge; at microphone 8 it is a third below the curve at 2,5 m, 6 %
below at 4,5 m and 3 % or less from 6 m up. The two outer curves
imply microphone heights the grid does not have, and could not be rebuilt.
The guide shows the comparison, and the lowest reliable band is left to the
caller.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ADRIENNE_CALIBRATION_LENGTH_S

*Constant* (`float`).

```python
ADRIENNE_CALIBRATION_LENGTH_S = 0.0013
```

## adrienne_low_frequency_limit_hz

```python
adrienne_low_frequency_limit_hz(window_length_s: float) -> float
```

The first notch in the spectrum of an Adrienne window, in hertz.

Garai and Guidorzi (J. Acoust. Soc. Am. 108 (2000) 1054, section III.D.4)
take the first notch of the window's magnitude spectrum, the end of its
main lobe, as the low frequency limit of a measurement made through it,
and give about 160 Hz for the 7,9 ms window. EN 1793-5 states the limit
only as the curves of Figure 14, without saying how they were drawn; this
is the indicator of the method's authors. The transform of the continuous
window is evaluated in closed form and the notch is located to a
millihertz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `window_length_s` | Total length $T_{W,ADR}$, in seconds. |

**Returns:** The frequency of the first minimum of the magnitude spectrum, in hertz: 162,5 Hz for 7,9 ms and 216,5 Hz for 6,0 ms.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the length does not exceed the 0,5 ms leading edge. |

## adrienne_reflection_window

```python
adrienne_reflection_window(
    fs: float,
    window_length_s: float = 0.0079,
) -> NDArray[np.float64]
```

The Adrienne temporal window of EN 1793-5, 5.5.5.

A left half of a four-term Blackman-Harris window 0,5 ms long, a flat part,
and a right half of a Blackman-Harris window; the flat part and the
trailing edge share the rest of the length 7 to 3. The 7,9 ms standard
window has a 5,18 ms flat part and a 2,22 ms trailing edge; the 6,0 ms one
3,85 ms and 1,65 ms.

The edges are Formula (7) sampled as printed: the leading edge is the
first half of a Blackman-Harris window twice its length, taken at
`0, 1/fs, ...` up to the sample before it reaches 1, which is the marker
point; the trailing edge is the second half of one twice its length, from
the sample after the flat part down to its last sample. The ISO 13472-1
window of
[`adrienne_window`](/phonometry/reference/api/materials/road-absorption/#adrienne_window)
is left free by its standard and rescales its halves instead; this one is
the formula EN 1793-5 prints.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `window_length_s` | Total length $T_{W,ADR}$, in seconds. |

**Returns:** The window, one sample per `1 / fs`; its marker point, where the flat part begins, is sample `round(0.5e-3 * fs)`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `fs` is not positive, the length does not exceed the 0,5 ms leading edge, or the flat part is shorter than a sample. |

## ADRIENNE_SHORT_LENGTH_S

*Constant* (`float`).

```python
ADRIENNE_SHORT_LENGTH_S = 0.006
```

## ADRIENNE_STANDARD_LENGTH_S

*Constant* (`float`).

```python
ADRIENNE_STANDARD_LENGTH_S = 0.0079
```

## BarrierReflectionWarning

A reflection measurement the standard flags as suspect.

Raised when the reduction factor of the subtraction falls below 10 dB
(5.5.4), when the gain factor departs from 1 by more than 20 % (5.5.1),
and when the sample rate is below the 44 kHz of 5.5.2.

## check_reflection_grid_position

```python
check_reflection_grid_position(
    time_delays_s: ArrayLike,
    *,
    speed_of_sound: float,
    check: Literal['relative', 'grid'] = 'grid',
) -> ReflectionGridCheck
```

Check the loudspeaker and grid positions with a reflecting plate.

5.6.2.5 (`check="relative"`): with a plate 0,25 m behind microphone 5,
the delays $\Delta t_{k5}$ between the direct sound at microphone
$k$ and at microphone 5 give $\Delta d_{k5} = c\,\Delta t_{k5}$ (Formula (10)); microphone 5 does not take part. 5.6.2.6
(`check="grid"`): with the plate on the reference plane, the delays
$\Delta t_k$ between the direct and the reflected sound at each
microphone give $\Delta d_k = c\,\Delta t_k$ (Formula (11)). Either
way the set-up is correct when every path difference is within
$\pm 25$ mm of Table 3.

**Parameters**

| Name | Description |
| :--- | :--- |
| `time_delays_s` | The nine delays, microphone 1 first, in seconds; for the relative check the fifth is ignored. |
| `speed_of_sound` | Speed of sound at the air temperature, in metres per second. |
| `check` | `"relative"` or `"grid"`. |

**Returns:** The [`ReflectionGridCheck`](/phonometry/reference/api/environment/barrier-reflection/#reflectiongridcheck) verdict.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If there are not nine finite delays, the speed is not positive or the check is unknown. |

## DirectSoundSubtraction

```python
DirectSoundSubtraction(
    in_front: Signal | NDArray[np.float64],
    aligned_free_field: Signal | NDArray[np.float64],
    residual: Signal | NDArray[np.float64],
    fs: float,
    peak_index: int,
    shift_samples: float,
    amplitude_factor: float,
    reduction_db: float,
)
```

The direct sound taken out of an impulse response, 5.5.4.

**Attributes**

| Name | Description |
| :--- | :--- |
| `in_front` | The impulse response measured in front of the device. |
| `aligned_free_field` | The free-field impulse response after the shift and the amplitude adjustment of steps 2 to 5, the one that was subtracted. NOTE 1: it serves the subtraction only; the index is computed from the original free-field record. |
| `residual` | What is left, the reflected component (step 6). |
| `fs` | Sample rate, in hertz. |
| `peak_index` | The sample of the first and main peak of the in-front record, the direct sound. |
| `shift_samples` | The shift applied to the free-field record, in samples, positive for a delay: a whole number of the 1/50 sample moving steps, within the +/- 2 samples 5.5.4 allows. |
| `amplitude_factor` | The factor that made the two main peaks equal. |
| `reduction_db` | $R_{sub}$, Formula (6): the energy of the free-field record within 0,5 ms of the peak over that of the residual in the same interval, in decibels. Below 10 dB the subtraction is not perfect; `inf` when nothing is left at all. |

The three records come back in the type they arrived as: a
[`Signal`](/phonometry/reference/api/io/io/#signal) when the record was one (in pascals and
carrying `calibration_factor=1.0` when it was calibrated), a bare array
otherwise.

### DirectSoundSubtraction.plot()

```python
DirectSoundSubtraction.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the record, the aligned direct sound and what is left.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the residual `Axes.plot` call. |

**Returns:** The `Axes`.

## geometric_divergence_corrections

```python
geometric_divergence_corrections(
    *,
    source_distance_m: float = 1.5,
    microphone_distance_m: float = 0.25,
    grid_spacing_m: float = 0.4,
) -> NDArray[np.float64]
```

$C_{geo,k} = (d_{r,k}/d_{i,k})^2$, Formula (2).

The reflection travels further than the direct sound and spreads over a
larger sphere; this puts that energy back. At microphone 5 it is
$(1{,}75/1{,}25)^2 = 1{,}96$; Table 2 prints all nine to two
decimals ([`REFLECTION_GRID_DISTANCES`](/phonometry/reference/api/environment/barrier-reflection/#reflection_grid_distances)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d_S$, loudspeaker to reference plane, m. |
| `microphone_distance_m` | $d_M$, grid to reference plane, m. |
| `grid_spacing_m` | $s$, microphone spacing, m. |

**Returns:** A read-only array of the nine corrections, microphone 1 first.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As [`reflection_grid_paths_m`](/phonometry/reference/api/environment/barrier-reflection/#reflection_grid_paths_m). |

## REFLECTION_GRID_DISTANCES

*Constant* (`mapping`).

```python
REFLECTION_GRID_DISTANCES = {1: (1.37, 1.84, 1.8), 2: (1.31, 1.8, 1.87), 3: (1.37, 1.84, 1.8), 4: (1.31, 1.8, 1.87), 5: (1.25, 1.75, 1.96), 6: (1.31, 1.8, 1.87), 7: (1.37, 1.84, 1.8), 8: (1.31, 1.8, 1.87), 9: (1.37, 1.84, 1.8)}
```

## reflection_grid_paths_m

```python
reflection_grid_paths_m(
    *,
    source_distance_m: float = 1.5,
    microphone_distance_m: float = 0.25,
    grid_spacing_m: float = 0.4,
) -> NDArray[np.float64]
```

The direct and the specular path to each microphone (Table 2).

$d_{i,k}$ runs from the centre of the loudspeaker front panel to
microphone $k$; $d_{r,k}$ runs from the same point to the
reference plane and back to the microphone by specular reflection, which
is the distance from the image of the loudspeaker in the plane. With the
geometry of the standard these are the values Table 2 prints to two
decimals (1,25 m and 1,75 m at microphone 5).

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d_S$, loudspeaker to reference plane, m. |
| `microphone_distance_m` | $d_M$, grid to reference plane, m. |
| `grid_spacing_m` | $s$, microphone spacing, m. |

**Returns:** A read-only `(9, 2)` array: column 0 is $d_{i,k}$ and column 1 is $d_{r,k}$, rows in microphone order 1 to 9.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a distance is not positive or the grid does not stand between the loudspeaker and the plane. |

## REFLECTION_GRID_SPACING_M

*Constant* (`float`).

```python
REFLECTION_GRID_SPACING_M = 0.4
```

## reflection_index

```python
reflection_index(
    in_front_irs: SignalInput | Sequence[SignalInput],
    free_field_irs: SignalInput | Sequence[SignalInput],
    fs: float | None = None,
    *,
    speed_of_sound: float,
    window_length_s: float | ArrayLike = 0.006,
    low_band_window_length_s: float | ArrayLike = 0.0079,
    low_band_microphones: Sequence[int] = (1, 2, 3, 4, 5, 6),
    directivity_corrections: ArrayLike | None = None,
    lowest_band_hz: float = 200.0,
) -> ReflectionIndexResult
```

The sound reflection index $RI_j$, Formula (1).

For every microphone of every grid position: the direct sound is
subtracted ([`subtract_direct_sound`](/phonometry/reference/api/environment/barrier-reflection/#subtract_direct_sound)); the free-field record is
windowed on its own peak and the residual on the specular arrival of the
reflection, both with the marker point 0,2 ms before the peak (5.5.6);
the band energies of the two are divided and corrected by
$C_{geo,k}$, $C_{dir,k}$ and $C_{gain,k}$. The
reflection's peak is placed by geometry, the direct peak plus
$(d_{r,k} - d_{i,k})/c$, which is what 5.5.6 prefers and what makes
the reference plane the conventional reflection plane of a non-flat
device.

The gain factor is Formula (4), with the 1,3 ms window over the bands of
500 Hz to 2 kHz, and it **divides**: Formula (1) prints it as a
multiplier, which with Formula (4) would square a gain change instead of
removing it (docs/ERRATA.md). 5.5.1 allows setting it to 1 when it is
within 5 % of 1; the value computed is always used here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `in_front_irs` | Impulse responses in front of the device, `(9, N)` for one grid position or `(positions, 9, N)`, microphones in the order of Figure 3.b. A nine-channel [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) is one grid position, and a sequence of them (or of `(9, N)` arrays) one per position; a Signal's calibration is applied. |
| `free_field_irs` | The free-field impulse responses of the same microphones, in the same form and shape. |
| `fs` | Sample rate, in hertz. Required when every record is a bare array; a Signal supplies it, and a Signal that disagrees with it or with another Signal is refused rather than arbitrated. |
| `speed_of_sound` | Speed of sound at the air temperature of the test (5.5.6, 5.7.3), in metres per second; it places the reflected window, and the standard asks for its temperature-dependent value. |
| `window_length_s` | $T_{W,ADR}$ from the 200 Hz band upward, one length or nine (one per microphone); 6,0 ms by 5.5.5. |
| `low_band_window_length_s` | $T_{W,ADR}$ of the 100 Hz to 160 Hz bands; 7,9 ms by 5.5.5. |
| `low_band_microphones` | The microphones averaged below 200 Hz; 1 to 6 by 5.5.5. |
| `directivity_corrections` | $C_{dir,k}(\Delta f_j)$ as a `(9, 18)` array ([`source_directivity_corrections`](/phonometry/reference/api/environment/barrier-reflection/#source_directivity_corrections)), or `None` for none, which is what a report states as "none". |
| `lowest_band_hz` | The lowest reliable band, where $DL_{RI}$ starts; 200 Hz for the qualification sample of 5.3. |

**Returns:** The [`ReflectionIndexResult`](/phonometry/reference/api/environment/barrier-reflection/#reflectionindexresult), with `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the records are not shaped as above, the rate is missing or disagrees, a window does not fit its record, or a parameter is out of range. |

**Warns**

| Warning | When |
| :--- | :--- |
| BarrierReflectionWarning | For an $R_{sub}$ below 10 dB, a gain factor more than 20 % from 1, or a sample rate below 44 kHz. |

## reflection_index_from_positions

```python
reflection_index_from_positions(
    position_values: ArrayLike,
    *,
    lowest_band_hz: float = 200.0,
) -> ReflectionIndexResult
```

Combine the index of several grid positions into the declared one.

Each row is one grid position's $RI$ in the eighteen bands, the
"particular values" of Table B.1; the declared index is their mean, band
by band, which is the overall average 5.6.2.3 asks for when every position
contributes the same microphones. A band a position did not measure may
be `nan`; it is left out of that band's mean.

**Parameters**

| Name | Description |
| :--- | :--- |
| `position_values` | `(positions, 18)` or `(18,)` indices. |
| `lowest_band_hz` | The lowest reliable band for $DL_{RI}$, one of the eighteen centres; 200 Hz is the qualification sample of 5.3. |

**Returns:** The [`ReflectionIndexResult`](/phonometry/reference/api/environment/barrier-reflection/#reflectionindexresult) (without microphone detail).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a row does not have eighteen values, a value is negative or infinite, or a band from `lowest_band_hz` has no value. |

## REFLECTION_INDEX_PRECISION

*Constant* (`mapping`).

## REFLECTION_LOW_BAND_MICROPHONES

*Constant* (`tuple`).

```python
REFLECTION_LOW_BAND_MICROPHONES = (1, 2, 3, 4, 5, 6)
```

## reflection_low_frequency_limit

```python
reflection_low_frequency_limit(
    device_height_m: float,
    *,
    speed_of_sound: float,
    device_length_m: float | None = None,
    source_height_m: float | None = None,
) -> ReflectionFrequencyLimit
```

The low frequency limit of each microphone for a device's size, 5.5.7.

The reflected window has to end before the sound reflected by the ground on
the source side and the sound diffracted by the edges of the device reach
the microphone. With the loudspeaker at $h_S$ (half the height by
default, 3.11) the ground reflection comes from the image of the
loudspeaker below the ground; the edge diffraction takes the shortest path
over the top edge, and over each side edge of a sample of the given
length centred on the grid. The window's marker is 0,2 ms before the
reflection and its tail is taken to end 0,2 ms before the unwanted
component, as its own marker would sit, so the flat part and the trailing
edge together last exactly the delay between the two; the limit is the
first notch of that window's spectrum.

This is the construction of Garai and Guidorzi (J. Acoust. Soc. Am. 108
(2000) 1054, section III.D), not a formula of EN 1793-5, which prints the
result only as Figure 14. At microphone 5 of a 4 m device it gives
167 Hz, where 5.5.7 reads about 170 Hz; the guide compares all three
curves.

**Parameters**

| Name | Description |
| :--- | :--- |
| `device_height_m` | $h_B$, in metres. |
| `speed_of_sound` | Speed of sound at the air temperature of the test, in metres per second. |
| `device_length_m` | The length of the sample, in metres, to include its two side edges; `None` considers the ground and the top edge, which is the case 5.5.7 treats for a device longer than it is high. |
| `source_height_m` | $h_S$, in metres; `None` for $h_B/2$. 3.11 allows 2 m above a 4 m device. |

**Returns:** The [`ReflectionFrequencyLimit`](/phonometry/reference/api/environment/barrier-reflection/#reflectionfrequencylimit), with `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a dimension is not positive, the grid does not fit between the ground and the top edge, the sample is narrower than the grid, or at some microphone the ground reflection or an edge arrives no later than the reflection itself (a device below about 1,7 m). |

## REFLECTION_MICROPHONE_DISTANCE_M

*Constant* (`float`).

```python
REFLECTION_MICROPHONE_DISTANCE_M = 0.25
```

## REFLECTION_PATH_DIFFERENCES_M

*Constant* (`mapping`).

```python
REFLECTION_PATH_DIFFERENCES_M = {1: (0.122, 0.467), 2: (0.062, 0.483), 3: (0.122, 0.467), 4: (0.062, 0.483), 5: (0.0, 0.5), 6: (0.062, 0.483), 7: (0.122, 0.467), 8: (0.062, 0.483), 9: (0.122, 0.467)}
```

## REFLECTION_PATH_TOLERANCE_M

*Constant* (`float`).

```python
REFLECTION_PATH_TOLERANCE_M = 0.025
```

## REFLECTION_RATING_PRECISION_DB

*Constant* (`mapping`).

```python
REFLECTION_RATING_PRECISION_DB = {'repeatability': (0.53, 0.44, 0.62), 'reproducibility': (0.68, 0.54, 0.81)}
```

## reflection_sampled_area_radius_m

```python
reflection_sampled_area_radius_m(
    window_length_s: float = 0.0079,
    *,
    speed_of_sound: float,
) -> float
```

The radius $r$ of the maximum sampled area, Formula (8).

The circle on the reference plane, centred at the point of incidence,
within which a reflecting object would still fall inside the reflected
window. It is the ISO 13472-1 construction with the loudspeaker 1,50 m and
the microphone 0,25 m from the plane, and it reuses
[`max_sampled_area_radius`](/phonometry/reference/api/materials/road-absorption/#max_sampled_area_radius).
NOTE 1 of 5.6.1 gives 1,96 m for the 7,9 ms window at 340 m/s.

**Parameters**

| Name | Description |
| :--- | :--- |
| `window_length_s` | $T_{W,ADR}$ of the reflected component, s. |
| `speed_of_sound` | Speed of sound at the air temperature of the test (5.7.3), in metres per second. |

**Returns:** The radius, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the window length or the speed is not positive. |

## REFLECTION_SOURCE_DISTANCE_M

*Constant* (`float`).

```python
REFLECTION_SOURCE_DISTANCE_M = 1.5
```

## ReflectionFrequencyLimit

```python
ReflectionFrequencyLimit(
    device_height_m: float,
    device_length_m: float | None,
    source_height_m: float,
    window_length_s: NDArray[np.float64],
    low_frequency_limit_hz: NDArray[np.float64],
    limiting_component: tuple[str, ...],
)
```

How far down a device of a given size can be measured, 5.5.7.

**Attributes**

| Name | Description |
| :--- | :--- |
| `device_height_m` | $h_B$, the height of the device. |
| `device_length_m` | The length of the sample, or `None` when its side edges were not considered. |
| `source_height_m` | $h_S$, the height of the loudspeaker and of microphone 5. |
| `window_length_s` | Per microphone, the longest Adrienne window whose tail ends before the first unwanted component: the flat part and the trailing edge last as long as the delay between the reflection and that component, plus the 0,5 ms leading edge. |
| `low_frequency_limit_hz` | Per microphone, the first notch of that window's spectrum ([`adrienne_low_frequency_limit_hz`](/phonometry/reference/api/environment/barrier-reflection/#adrienne_low_frequency_limit_hz)). |
| `limiting_component` | Per microphone, `"ground"` for the ground reflection on the source side, `"top edge"` or `"side edge"` for a diffraction by an edge of the device. |

### ReflectionFrequencyLimit.plot()

```python
ReflectionFrequencyLimit.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the limit at each microphone and what sets it.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the `Axes.bar` call. |

**Returns:** The `Axes`.

## ReflectionGridCheck

```python
ReflectionGridCheck(check: str, path_differences_m: NDArray[np.float64])
```

The position check of 5.6.2.5 or 5.6.2.6, against Table 3.

The nominal path differences and the tolerance are Table 3's, so they are
read from the check and are not fields: a check cannot be built, or
rewritten with `dataclasses.replace`, against other nominal values
or another tolerance.

**Attributes**

| Name | Description |
| :--- | :--- |
| `check` | `"relative"` (5.6.2.5, the loudspeaker against the grid, $\Delta d_{k5}$) or `"grid"` (5.6.2.6, the grid against the reference plane, $\Delta d_k$). |
| `path_differences_m` | $c\,\Delta t$, Formula (10) or (11), per microphone, microphone 1 first, in metres; microphone 5 does not take part in the relative check. |

### ReflectionGridCheck.deviations_m

*property*

Measured minus nominal, in metres.

**Returns:** One deviation per microphone; zero for microphone 5 in the relative check, which does not take part in it.

### ReflectionGridCheck.nominal_m

*property*

The nominal values of Table 3 for this check, in metres.

**Returns:** $\Delta d_{k5}$ for the relative check, $\Delta d_k$ for the grid check, microphone 1 first.

### ReflectionGridCheck.passes

*property*

Whether every microphone is within tolerance, so the set-up is correct.

**Returns:** `True` when step 8 finds the position correct.

### ReflectionGridCheck.plot()

```python
ReflectionGridCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each microphone's deviation against the 25 mm tolerance.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the deviation `Axes.plot` call. |

**Returns:** The `Axes`.

### ReflectionGridCheck.within

*property*

Per microphone, whether the deviation is within $\pm\varepsilon_k$.

**Returns:** `True` where the deviation is within the 25 mm of Table 3 ([`REFLECTION_PATH_TOLERANCE_M`](/phonometry/reference/api/environment/barrier-reflection/#reflection_path_tolerance_m)).

## ReflectionIndexResult

```python
ReflectionIndexResult(
    bands_hz: NDArray[np.float64],
    reflection_index: NDArray[np.float64],
    position_values: NDArray[np.float64],
    lowest_band_hz: float,
    rating: RoadDeviceRating,
    microphone_values: NDArray[np.float64] | None = None,
    gain_corrections: NDArray[np.float64] | None = None,
    subtraction_reductions_db: NDArray[np.float64] | None = None,
)
```

The sound reflection index of a device, per one-third octave band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `bands_hz` | The eighteen band centres, 100 Hz to 5 kHz. |
| `reflection_index` | $RI_j$, the average over every microphone of every grid position (5.6.2.3); `nan` in a band nothing measured. |
| `position_values` | `(positions, 18)`: the average of each grid position, the "particular values" of Table B.1. |
| `lowest_band_hz` | The lowest reliable band, where the single number starts (the $m$ of Formula (12)). |
| `rating` | $DL_{RI}$ over the bands from `lowest_band_hz`, a [`RoadDeviceRating`](/phonometry/reference/api/environment/noise-reducing-devices/#roaddevicerating). |
| `microphone_values` | `(positions, 9, 18)`: the index of each microphone, `nan` where 5.5.5 leaves it out (microphones 7 to 9 below 200 Hz by default); `None` for a result built from position values. |
| `gain_corrections` | `(positions, 9)`: $C_{gain,k}$ of Formula (4), or `None`. |
| `subtraction_reductions_db` | `(positions, 9)`: $R_{sub}$ of each subtraction, in decibels, or `None`. |

### ReflectionIndexResult.expanded_uncertainty()

```python
ReflectionIndexResult.expanded_uncertainty(
    *,
    estimate: Literal['median', 'low', 'high'] = 'high',
    coverage_factor: float = 1.96,
) -> tuple[NDArray[np.float64], float]
```

Expanded uncertainty from the reproducibility of Table A.1 (A.2).

$U_j = k_p\, s_{R,j}$, with $s_R$ taken as the combined
standard uncertainty. Annex B.5 takes the high column and
$k_p$ = 1,96 for 95 % coverage, which is the default.

**Parameters**

| Name | Description |
| :--- | :--- |
| `estimate` | The column of Table A.1, `"median"`, `"low"` or `"high"`. |
| `coverage_factor` | $k_p$. |

**Returns:** The eighteen $U_j$ and the $U$ of $DL_{RI}$ in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | On an unknown column or a non-positive factor. |

### ReflectionIndexResult.plot()

```python
ReflectionIndexResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the index per band, each grid position and the rating.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the average `Axes.plot` call. |

**Returns:** The `Axes`.

## source_directivity_corrections

```python
source_directivity_corrections(
    microphone_irs: SignalInput,
    specular_irs: SignalInput,
    fs: float | None = None,
    *,
    window_length_s: float | ArrayLike = 0.006,
    low_band_window_length_s: float | ArrayLike = 0.0079,
) -> NDArray[np.float64]
```

$C_{dir,k}(\Delta f_j)$, Formula (3).

The direct sound reaches microphone $k$ at the angle
$\alpha_k$ from the loudspeaker axis, and the reflection leaves the
loudspeaker at another angle $\beta_k$, towards its specular point.
Both are measured once per loudspeaker in free field, at the same distance
$d_{i,k}$: one at the microphone position, one on the specular path.
The correction is the ratio of their windowed band energies, each window
placed on its own record's peak (5.5.6).

**Parameters**

| Name | Description |
| :--- | :--- |
| `microphone_irs` | `(9, N)` free-field impulse responses at the nine microphone positions (angle $\alpha_k$). Accepts a nine-channel [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal), whose calibration is applied. |
| `specular_irs` | `(9, N)` free-field impulse responses at the nine points on the specular paths (angle $\beta_k$); same treatment. |
| `fs` | Sample rate, in hertz. Required when both sets are bare arrays; either may be a Signal and supply it, and two Signals recorded at different rates are refused rather than arbitrated. |
| `window_length_s` | Window from the 200 Hz band upward, one length or nine, in seconds. |
| `low_band_window_length_s` | Window of the 100 Hz to 160 Hz bands, one length or nine, in seconds. |

**Returns:** A read-only `(9, 18)` array, microphones by the bands of [`TRAFFIC_NOISE_BANDS_HZ`](/phonometry/reference/api/environment/noise-reducing-devices/#traffic_noise_bands_hz), to pass as `directivity_corrections` to [`reflection_index`](/phonometry/reference/api/environment/barrier-reflection/#reflection_index).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the records are not `(9, N)`, finite and equal in shape, the rate is missing, disagrees or is not positive, or a window does not fit its record. |

## subtract_direct_sound

```python
subtract_direct_sound(
    in_front_ir: SignalInput,
    free_field_ir: SignalInput,
    fs: float | None = None,
) -> DirectSoundSubtraction
```

Remove the direct sound from an impulse response, 5.5.4.

The free-field record is the direct sound alone, measured with the same
geometry. It is shifted in steps of a fiftieth of a sample, within two
samples either way, by a phase ramp over its own transform (steps a and
b); the shift that minimises the squared difference over 50 samples
around the main peak of the in-front record is kept; the shifted record
is scaled so the two main peaks are equal; and it is subtracted. The
reduction factor $R_{sub}$ of Formula (6) measures what is left of
the direct sound.

**Parameters**

| Name | Description |
| :--- | :--- |
| `in_front_ir` | The impulse response in front of the device. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal), whose calibration is applied to the samples, so the records come back in pascals, and as Signals. |
| `free_field_ir` | The free-field impulse response of the same microphone, same length and sample rate; same treatment. |
| `fs` | Sample rate, in hertz. Required when both records are bare arrays; either may be a Signal and supply it, and two Signals recorded at different rates are refused rather than arbitrated. |

**Returns:** The [`DirectSoundSubtraction`](/phonometry/reference/api/environment/barrier-reflection/#directsoundsubtraction), with `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the records are not one-dimensional, finite and of equal length, or the rate is missing or not positive. |

**Warns**

| Warning | When |
| :--- | :--- |
| BarrierReflectionWarning | If $R_{sub}$ is below 10 dB or the sample rate below 44 kHz. |
