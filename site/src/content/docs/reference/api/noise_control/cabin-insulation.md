---
title: "noise_control.cabin_insulation"
description: "What a cabin keeps out, measured in the room it stands in (ISO 11957)."
sidebar:
  label: "cabin_insulation"
---

What a cabin keeps out, measured in the room it stands in (ISO 11957).

An enclosure keeps noise in; a **cabin** keeps it out. ISO 11957:1996 measures
the second, and it measures it as one subtraction: put the cabin in a sound
field, measure the level in the room and the level inside the empty cabin, and
take the difference band by band.

$$
D_p = (L_p)_{\text{room}} - (L_p)_{\text{cabin}}
$$

That is Equation (1) in the laboratory. Equation (2) is the same arithmetic
**in situ**, where the room need not be diffuse, and the answer carries a prime
to say so: $D'_p$. Equation (3) is the A-weighted difference
$D'_{pA}$, and the standard defines it only for the third of its three
methods, the one that drives the room with the noise that is actually there.
There is no unprimed $D_{pA}$ in this document, and
[`cabin_insulation`](/phonometry/reference/api/noise_control/cabin-insulation/#cabin_insulation) refuses to compute one.

The three methods
-----------------

* **laboratory**, clause 6, in a reverberation room to ISO 3741, with at least
  two loudspeaker positions;
* **in situ with a loudspeaker**, 7.2.1, in any room at all, where the number
  of source positions is not fixed in advance but read off the spread of the
  answer itself ([`check_source_positions`](/phonometry/reference/api/noise_control/cabin-insulation/#check_source_positions));
* **in situ with the actual noise**, 7.2.2, where the machinery of the
  workplace is the source, which is the only method that yields
  $D'_{pA}$.

Only results from the same method may be compared, which is why the method is
a field of [`CabinInsulationResult`](/phonometry/reference/api/noise_control/cabin-insulation/#cabininsulationresult) and not a remark in a docstring.

What is here and what is not
----------------------------

Every equation of clauses 6 to 9 is implemented, plus the numeric acceptance
rules the clauses state: the source-position criterion of 7.2.1, the flatness
of the driving spectrum of 6.4, the clearance of 6.2, the background margins,
and the volume ratio clause 10 attaches its uncertainty to. The single-number
rating of clause 8 is handed to [`phonometry.building.weighted_rating`](/phonometry/reference/api/building/ratings/#weighted_rating),
which is ISO 717-1 with $D_p$ written where that standard writes
$R$, and the background correction is handed to
[`phonometry.emission.reverberation_background_correction`](/phonometry/reference/api/power/sound-power-reverberation/#reverberation_background_correction), which is the
ISO 3741 the clauses point at.

The leak ratio of definition 3.14 and the seal ratio of its note are printed
word for word as in ISO 11546, so they are imported from
[`phonometry.noise_control.enclosure_insulation`](/phonometry/reference/api/noise_control/enclosure-insulation/) rather than written twice.
The scope is tighter here: ISO 11546 only prefers a leak ratio under 2 %, while
clause 1 of ISO 11957 makes it a condition of applicability.

Instrumentation, mounting, the ten operations of every movable part and the
report template are procedure, and procedure is not arithmetic. The one piece
of clause 11 that computes is the rounding of 11.4 e), which is
[`CabinInsulationResult.rounded`](/phonometry/reference/api/noise_control/cabin-insulation/#cabininsulationresultrounded).

The document prints no worked example, so the tests are anchored on the
algebraic identities of the subtraction, on the printed thresholds, and on the
identity that makes [`estimated_cabin_noise_insulation`](/phonometry/reference/api/noise_control/cabin-insulation/#estimated_cabin_noise_insulation) agree with its own
inputs.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## BAND_FLATNESS_LIMIT_DB

*Constant* (`dict`).

```python
BAND_FLATNESS_LIMIT_DB = {125.0: 6.0, 250.0: 5.0}
```

## BandFlatnessCheck

```python
BandFlatnessCheck(
    octave_centres_hz: NDArray[np.float64],
    spread_db: NDArray[np.float64],
    limit_db: NDArray[np.float64],
    satisfied: NDArray[np.bool_],
)
```

How flat the driving spectrum is inside each octave, 6.4 and 7.2.1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `octave_centres_hz` | The octave centre frequencies read, in hertz. |
| `spread_db` | The difference between the loudest and the quietest of the three one-third-octave bands in each, in decibels. |
| `limit_db` | What 6.4 allows in each, in decibels, and `nan` in the octaves below 125 Hz, for which the clause prints no limit. |
| `satisfied` | Whether each octave meets its limit. An octave with no printed limit is reported as satisfied. |

### BandFlatnessCheck.all_satisfied

*property*

Whether every octave with a printed limit meets it.

## cabin_insulation

```python
cabin_insulation(
    room_levels: ArrayLike,
    cabin_levels: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    method: CabinMethod = 'laboratory',
    band_fraction: int = 3,
    room_background_levels: ArrayLike | None = None,
    cabin_background_levels: ArrayLike | None = None,
    a_weighted_room_level: float | None = None,
    a_weighted_cabin_level: float | None = None,
    internal_noise_level: float | None = None,
) -> CabinInsulationResult
```

Sound pressure insulation of a cabin, Equations (1), (2) and (3).

One function for the three equations, because the three are the same
subtraction and what separates them is the method, not the arithmetic:

$$
D_p = (L_p)_{\text{room}} - (L_p)_{\text{cabin}}
$$

in the laboratory, the same in situ under the name $D'_p$, and the
A-weighted difference $D'_{pA} = (L_{pA})_{\text{room}} - (L_{pA})_{\text{cabin}}$ when the source is the noise of the workplace.
Definition 3.7 ties that last one to the actual-noise method alone, so an
A-weighted pair given under another method is refused rather than quietly
renamed.

Where a background spectrum is supplied it is taken off first, by the
ISO 3741 correction 6.4 asks for, and a margin under
[`MIN_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/noise_control/cabin-insulation/#min_signal_to_background_db) is reported.

**Parameters**

| Name | Description |
| :--- | :--- |
| `room_levels` | $(L_p)_{\text{room}}$ per band, in decibels. |
| `cabin_levels` | $(L_p)_{\text{cabin}}$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `method` | `"laboratory"` (default), `"in-situ-loudspeaker"` or `"in-situ-actual-noise"`. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |
| `room_background_levels` | Background in the room per band, in decibels, for the correction of 7.2.2. |
| `cabin_background_levels` | Background inside the cabin per band, in decibels, for the correction of 6.4. |
| `a_weighted_room_level` | $(L_{pA})_{\text{room}}$, in decibels. |
| `a_weighted_cabin_level` | $(L_{pA})_{\text{cabin}}$, in decibels. |
| `internal_noise_level` | $L_{pA}$ of 6.7, in decibels, carried into the result because 11.4 reports it beside the insulation. |

**Returns:** The insulation, as a [`CabinInsulationResult`](/phonometry/reference/api/noise_control/cabin-insulation/#cabininsulationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, an unknown method or band fraction, or an A-weighted pair under a method that does not define one. |

## CabinInsulationResult

```python
CabinInsulationResult(
    frequencies: NDArray[np.float64] | None,
    room_levels: NDArray[np.float64],
    cabin_levels: NDArray[np.float64],
    insulation: NDArray[np.float64],
    apparent: bool,
    a_weighted_insulation: float | None,
    internal_noise_level: float | None,
    method: str,
    band_fraction: int,
)
```

The sound pressure insulation of a cabin, band by band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal band centre frequencies, in hertz, or `None` when the levels were given without them. |
| `room_levels` | $(L_p)_{\text{room}}$, in decibels, after any background correction. |
| `cabin_levels` | $(L_p)_{\text{cabin}}$, in decibels, after any background correction. |
| `insulation` | $D_p$ or $D'_p$ per band, in decibels. |
| `apparent` | Whether the answer carries the prime of 3.6, which it does for both in-situ methods. |
| `a_weighted_insulation` | $D'_{pA}$ of Equation (3), in decibels, or `None`. Defined only for the actual-noise method. |
| `internal_noise_level` | $L_{pA}$ of 6.7, in decibels, or `None` when the cabin has no integral source. |
| `method` | `"laboratory"`, `"in-situ-loudspeaker"` or `"in-situ-actual-noise"`. |
| `band_fraction` | 3 for one-third octaves, 1 for octaves. |

### CabinInsulationResult.plot()

```python
CabinInsulationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two levels and the difference between them.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.noise_control.plot_cabin_insulation`. |

**Returns:** The `Axes`.

### CabinInsulationResult.rounded()

```python
CabinInsulationResult.rounded() -> NDArray[np.int_]
```

The band values as 11.4 e) reports them, to the nearest decibel.

### CabinInsulationResult.symbol

*property*

The symbol clause 12 reports this as, `"D_p"` or `"D'_p"`.

## CabinInsulationWarning

The measurement is outside a condition ISO 11957 states.

## CabinUncertainty

```python
CabinUncertainty(
    method: str,
    volume_ratio: float,
    ratio_satisfied: bool,
    stateable: bool,
    stated_band_range_hz: tuple[float, float] | None,
    increased_uncertainty_band_range_hz: tuple[float, float] | None,
    excess_standard_deviation_db: float | None,
)
```

What clause 10 will and will not say about a measurement.

**Attributes**

| Name | Description |
| :--- | :--- |
| `method` | The method the statement is about. |
| `volume_ratio` | $V_{\text{room}} / V_{\text{cabin}}$. |
| `ratio_satisfied` | Whether that ratio reaches [`MIN_ROOM_TO_CABIN_VOLUME_RATIO`](/phonometry/reference/api/noise_control/cabin-insulation/#min_room_to_cabin_volume_ratio). |
| `stateable` | Whether clause 10 offers any figure at all. It does not for the actual-noise method, which it sends to ISO 4871 instead. |
| `stated_band_range_hz` | The range the statement covers, in hertz, or `None` when nothing is stateable. |
| `increased_uncertainty_band_range_hz` | The range where a larger uncertainty is expected, in hertz, or `None`. |
| `excess_standard_deviation_db` | What this method adds to the standard deviation of the laboratory one, in decibels, or `None`. |

## check_band_flatness

```python
check_band_flatness(
    third_octave_levels: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> BandFlatnessCheck
```

Is the driving spectrum flat enough inside each octave? 6.4 and 7.2.1.

An octave-band measurement only means what the standard says it means if
the sound that produced it was spread evenly across the octave. The clause
puts a number on that: the three one-third-octave levels inside one octave
shall not differ by more than 6 dB in the octave of 125 Hz, 5 dB in the one
of 250 Hz and 4 dB in the bands of higher frequencies. Nothing is printed
for the octaves below 125 Hz, so nothing is claimed for them here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `third_octave_levels` | The one-third-octave levels of the sound in the room, in decibels. |
| `frequencies` | Their nominal centre frequencies, in hertz. |

**Returns:** One row per octave, as a [`BandFlatnessCheck`](/phonometry/reference/api/noise_control/cabin-insulation/#bandflatnesscheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match, a frequency that names no one-third-octave band, a band given twice, or an octave that is not covered by its three bands. |

## check_source_positions

```python
check_source_positions(
    insulation_by_position: ArrayLike,
) -> SourcePositionCheck
```

Were there enough loudspeaker positions? 7.2.1.

The only acceptance criterion in the document that is read off the answer
rather than fixed in advance: the number of source positions shall be at
least the largest difference, in decibels, between the $D'_p$ of any
two positions, **in octave bands**. Three positions to begin with, six at
most, and a spread past six goes in the report.

The clause says octave bands, and it says so because the spread of a
one-third-octave answer is the wider one. A one-third-octave measurement is
therefore folded to octaves at the level, by energy-summing the room and
the cabin spectra, before the difference is formed; folding the difference
itself is not the same number, so this function takes the octave-band
$D'_p$ already formed and does not pretend to do that conversion.

**Parameters**

| Name | Description |
| :--- | :--- |
| `insulation_by_position` | $D'_p$ in octave bands, one row per source position and one column per band, in decibels. |

**Returns:** The verdict, as a [`SourcePositionCheck`](/phonometry/reference/api/noise_control/cabin-insulation/#sourcepositioncheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For fewer than [`MIN_SOURCE_POSITIONS_IN_SITU`](/phonometry/reference/api/noise_control/cabin-insulation/#min_source_positions_in_situ) positions, or an array that is not rectangular. |

## DEFAULT_BAND_FLATNESS_LIMIT_DB

*Constant* (`float`).

```python
DEFAULT_BAND_FLATNESS_LIMIT_DB = 4.0
```

## estimated_cabin_noise_insulation

```python
estimated_cabin_noise_insulation(
    spectrum_levels: ArrayLike,
    insulation: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> float
```

What a cabin is worth against a stated spectrum, Annex A.

Both formulas of the annex, which differ only in whether $D_p$ or
$D'_p$ is substituted:

$$
D_{pA,e} = L_A - 10 \lg \sum_i 10^{0,1 (L_i - A_i - D_{pi})}
$$

with $L_A = 10 \lg \sum_i 10^{0,1 (L_i - A_i)}$ the A-weighted total
of the assumed spectrum. The sign of $A_i$ is the trap: the annex
prints an attenuation, positive where the weighting takes level away, while
this library's band corrections are the correction itself, so
$A_i = -C_k$. Both terms are built here from the same table, so the
total and the sum cannot disagree, and an insulation of zero returns
exactly zero.

The annex assumes a diffuse field and says so; in situ it will usually not
be, and nothing here is corrected for flanking through the floor.

**Parameters**

| Name | Description |
| :--- | :--- |
| `spectrum_levels` | $L_i$, the assumed noise spectrum per band, in decibels. |
| `insulation` | $D_{pi}$ or $D'_{pi}$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |

**Returns:** $D_{pA,e}$ or $D'_{pA,e}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match band for band. |

## IN_SITU_EXCESS_STANDARD_DEVIATION_DB

*Constant* (`float`).

```python
IN_SITU_EXCESS_STANDARD_DEVIATION_DB = 2.0
```

## INCREASED_UNCERTAINTY_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
INCREASED_UNCERTAINTY_BAND_RANGE_HZ = (50.0, 200.0)
```

## INTERNAL_NOISE_CENTRE_HEIGHT_M

*Constant* (`float`).

```python
INTERNAL_NOISE_CENTRE_HEIGHT_M = 1.55
```

## INTERNAL_NOISE_CENTRE_TOLERANCE_M

*Constant* (`float`).

```python
INTERNAL_NOISE_CENTRE_TOLERANCE_M = 0.075
```

## INTERNAL_NOISE_CORRECTION_WINDOW_DB

*Constant* (`tuple`).

```python
INTERNAL_NOISE_CORRECTION_WINDOW_DB = (6.0, 10.0)
```

## internal_noise_level

```python
internal_noise_level(
    levels: ArrayLike,
    *,
    background_level: float | None = None,
) -> float
```

The noise a cabin makes on its own, $L_{pA}$ of 6.7.

The A-weighted levels measured at the three positions on the 0,3 m sphere,
or over the inclined circular path, averaged on a mean-square basis with
the external sources switched off.

The background rule of 6.7 is not the one of 6.4. The margin over the
background must reach [`MIN_SIGNAL_TO_BACKGROUND_DB`](/phonometry/reference/api/noise_control/cabin-insulation/#min_signal_to_background_db), and the
correction is made **only** while the margin stays inside
[`INTERNAL_NOISE_CORRECTION_WINDOW_DB`](/phonometry/reference/api/noise_control/cabin-insulation/#internal_noise_correction_window_db): past the top of that window
the correction is under a tenth of a decibel and the clause does not ask
for it. The correction itself is the $K_1$ of ISO 3741,
$-10 \lg (1 - 10^{-0,1 \Delta L})$, applied to the A-weighted total
rather than band by band, which is what makes it a separate line here from
[`phonometry.emission.reverberation_background_correction`](/phonometry/reference/api/power/sound-power-reverberation/#reverberation_background_correction).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | The A-weighted levels at the microphone positions, in decibels. |
| `background_level` | The A-weighted background inside the cabin with the integral sources switched off, in decibels. |

**Returns:** $L_{pA}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty or non-finite set of levels. |

## LOW_BAND_CLEARANCE_M

*Constant* (`float`).

```python
LOW_BAND_CLEARANCE_M = 2.0
```

## LOW_BAND_CLEARANCE_RANGE_HZ

*Constant* (`tuple`).

```python
LOW_BAND_CLEARANCE_RANGE_HZ = (50.0, 80.0)
```

## MAX_LEAK_RATIO

*Constant* (`float`).

```python
MAX_LEAK_RATIO = 0.02
```

## MAX_MICROPHONE_TO_CABIN_M

*Constant* (`float`).

```python
MAX_MICROPHONE_TO_CABIN_M = 5.0
```

## MAX_SOURCE_POSITIONS_IN_SITU

*Constant* (`int`).

```python
MAX_SOURCE_POSITIONS_IN_SITU = 6
```

## MIN_FIXED_MICROPHONE_POSITIONS

*Constant* (`int`).

```python
MIN_FIXED_MICROPHONE_POSITIONS = 6
```

## MIN_LOUDSPEAKER_POSITIONS

*Constant* (`int`).

```python
MIN_LOUDSPEAKER_POSITIONS = 2
```

## MIN_LOUDSPEAKER_SEPARATION_M

*Constant* (`float`).

```python
MIN_LOUDSPEAKER_SEPARATION_M = 3.0
```

## MIN_MICROPHONE_HEIGHT_M

*Constant* (`float`).

```python
MIN_MICROPHONE_HEIGHT_M = 1.0
```

## MIN_ROOM_TO_CABIN_VOLUME_RATIO

*Constant* (`float`).

```python
MIN_ROOM_TO_CABIN_VOLUME_RATIO = 20.0
```

## MIN_SIGNAL_TO_BACKGROUND_DB

*Constant* (`float`).

```python
MIN_SIGNAL_TO_BACKGROUND_DB = 6.0
```

## MIN_SOURCE_POSITIONS_IN_SITU

*Constant* (`int`).

```python
MIN_SOURCE_POSITIONS_IN_SITU = 3
```

## MIN_SOURCE_TO_CABIN_M

*Constant* (`float`).

```python
MIN_SOURCE_TO_CABIN_M = 2.0
```

## MIN_SOURCE_TO_MICROPHONE_IN_SITU_M

*Constant* (`float`).

```python
MIN_SOURCE_TO_MICROPHONE_IN_SITU_M = 3.0
```

## MIN_SOURCE_TO_MICROPHONE_M

*Constant* (`float`).

```python
MIN_SOURCE_TO_MICROPHONE_M = 2.0
```

## minimum_cabin_clearance_m

```python
minimum_cabin_clearance_m(
    lowest_band_frequency_hz: float,
    *,
    speed_of_sound: float = 343.0,
) -> float
```

How far the cabin stands from the room, 6.2.

Half a wavelength at the centre of the lowest band of interest, between the
cabin and the walls, the ceiling and any diffusing element alike. Below
100 Hz the clause stops computing and fixes a flat
[`LOW_BAND_CLEARANCE_M`](/phonometry/reference/api/noise_control/cabin-insulation/#low_band_clearance_m), which at 50 Hz is less than the half
wavelength the rule above it would have asked for: the low-frequency
sentence relaxes the requirement rather than tightening it, and it is
written here exactly as printed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `lowest_band_frequency_hz` | The centre frequency of the lowest band of interest, in hertz. |
| `speed_of_sound` | Speed of sound in the room, in metres per second. |

**Returns:** The least clearance, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency or speed. |

## OPERATOR_PATH_INCLINATION_DEG

*Constant* (`float`).

```python
OPERATOR_PATH_INCLINATION_DEG = 45.0
```

## OPERATOR_SPHERE_RADIUS_M

*Constant* (`float`).

```python
OPERATOR_SPHERE_RADIUS_M = 0.3
```

## PREFERRED_SIGNAL_TO_BACKGROUND_DB

*Constant* (`float`).

```python
PREFERRED_SIGNAL_TO_BACKGROUND_DB = 12.0
```

## SourcePositionCheck

```python
SourcePositionCheck(
    positions_used: int,
    max_octave_spread_db: float,
    required_positions: int,
    satisfied: bool,
    exceeds_maximum: bool,
)
```

Whether enough loudspeaker positions were used, 7.2.1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `positions_used` | $N$, the number of source positions measured. |
| `max_octave_spread_db` | The largest difference in $D'_p$ between any two positions, over the octave bands, in decibels. |
| `required_positions` | The fewest positions that spread calls for, never below [`MIN_SOURCE_POSITIONS_IN_SITU`](/phonometry/reference/api/noise_control/cabin-insulation/#min_source_positions_in_situ). |
| `satisfied` | Whether `positions_used` reaches that number. |
| `exceeds_maximum` | Whether the spread runs past [`MAX_SOURCE_POSITIONS_IN_SITU`](/phonometry/reference/api/noise_control/cabin-insulation/#max_source_positions_in_situ), which 7.2.1 says shall be stated in the report. |

## STATED_UNCERTAINTY_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
STATED_UNCERTAINTY_BAND_RANGE_HZ = (250.0, 10000.0)
```

## uncertainty_conditions

```python
uncertainty_conditions(
    *,
    room_volume_m3: float,
    cabin_volume_m3: float,
    method: CabinMethod = 'laboratory',
) -> CabinUncertainty
```

What clause 10 is willing to say about this measurement.

In the laboratory the uncertainty of ISO 3741 carries over from 250 Hz to
10 kHz, but only while the room is at least
[`MIN_ROOM_TO_CABIN_VOLUME_RATIO`](/phonometry/reference/api/noise_control/cabin-insulation/#min_room_to_cabin_volume_ratio) times the volume of the cabin; below
that ratio, and from 50 Hz to 200 Hz in any case, a larger uncertainty is
expected. The loudspeaker method in situ adds about
[`IN_SITU_EXCESS_STANDARD_DEVIATION_DB`](/phonometry/reference/api/noise_control/cabin-insulation/#in_situ_excess_standard_deviation_db) to the standard deviation. For
the actual-noise method the clause states nothing at all and sends a
declared value to ISO 4871.

**Parameters**

| Name | Description |
| :--- | :--- |
| `room_volume_m3` | $V_{\text{room}}$, in cubic metres. |
| `cabin_volume_m3` | $V_{\text{cabin}}$, in cubic metres. |
| `method` | `"laboratory"` (default), `"in-situ-loudspeaker"` or `"in-situ-actual-noise"`. |

**Returns:** The statement, as a [`CabinUncertainty`](/phonometry/reference/api/noise_control/cabin-insulation/#cabinuncertainty).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive volume or an unknown method. |

## WALL_CLEARANCE_FACTOR

*Constant* (`float`).

```python
WALL_CLEARANCE_FACTOR = 0.5
```

## weighted_cabin_insulation

```python
weighted_cabin_insulation(
    insulation: ArrayLike,
    *,
    apparent: bool = False,
    band_fraction: int = 3,
) -> WeightedCabinInsulation
```

The single-number rating of a cabin, clause 8.

ISO 717-1 with $D_p$ or $D'_p$ written where that standard
writes the sound reduction index: the reference curve, the shift and the
adaptation terms come from [`phonometry.building.weighted_rating`](/phonometry/reference/api/building/ratings/#weighted_rating), and
what is done here is the trim to the rating bands and the prime.

Clause 4 calls this the preferred single number and then warns against
reading too much into it, because what a cabin is worth depends on the
spectrum it stands in. [`estimated_cabin_noise_insulation`](/phonometry/reference/api/noise_control/cabin-insulation/#estimated_cabin_noise_insulation) is the
answer to that objection.

**Parameters**

| Name | Description |
| :--- | :--- |
| `insulation` | $D_p$ or $D'_p$ over the 16 one-third-octave rating bands or the 5 octave ones, in decibels. |
| `apparent` | Whether the spectrum is the in-situ one, which decides whether the rating is $D_{p,w}$ or $D'_{p,w}$. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The rating, as a [`WeightedCabinInsulation`](/phonometry/reference/api/noise_control/cabin-insulation/#weightedcabininsulation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spectrum that is not the rating bands. |

## WeightedCabinInsulation

```python
WeightedCabinInsulation(
    rating: int,
    c: int,
    ctr: int,
    unfavourable_sum: float,
    band_centres_hz: NDArray[np.float64],
    apparent: bool,
)
```

The single-number rating of a cabin, clause 8 by way of ISO 717-1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | $D_{p,w}$ or $D'_{p,w}$, in decibels. |
| `c` | The spectrum adaptation term $C$, in decibels. |
| `ctr` | The spectrum adaptation term $C_{tr}$, in decibels. |
| `unfavourable_sum` | The sum of unfavourable deviations at the shift the rating was read at, in decibels. |
| `band_centres_hz` | The bands the rating was read over, in hertz. |
| `apparent` | Whether the rating carries the prime of 3.9. |
