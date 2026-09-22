---
title: "noise_control.screen_in_situ"
description: "What a screen on the shop floor is worth (ISO 11821:1997)."
sidebar:
  label: "screen_in_situ"
---

What a screen on the shop floor is worth (ISO 11821:1997).

A **removable screen** is a panel or a flexible curtain put between a machine
and the people near it, breaking the line of sight and nothing more. It is the
cheapest thing in noise control and the hardest to quote a number for, because
what it is worth depends on the room it stands in as much as on the screen.

ISO 11821 measures that number where the screen stands. The quantity is an
insertion loss, the difference between the level at a position with the screen
removed and the level at the same position with it in place:

$$
D_p = L_{p1} - L_{p2}
$$

Clause 5.8 prints that without an equation number, and the whole of the
standard is arranging for those two levels to be comparable.

What it is not for
------------------

The Introduction draws three lines. A screen in an open-plan office is
ISO 10053; an outdoor community-noise barrier is ISO 10847, which is
[`phonometry.environment.propagation.barrier_in_situ`](/phonometry/reference/api/environment/barrier-in-situ/); and this method is
not a qualification of a screen as a product but a measurement of one
installation. Indoors the room decides a large part of the answer, so two
screens may only be compared where the test conditions were the same.

Within its own scope it wants a screen at least 1,5 m high and 1,5 m long, and
outdoors it stops at 25 m from the screen.

One number or several
---------------------

Where the screen protects a defined operator position, 5.5.1 puts three
microphones on a sphere of 0,3 m radius around the head and the answer is one
number. Where it shields an area, 5.5.2 puts them along a line perpendicular
to the screen at a quarter, a half, once and twice the screen height, never
closer than 1 m, and the answer is a range: NOTE 2 says the smallest
attenuation will be found at the most remote position and the largest at the
nearest, which is why the Introduction asks for the maximum and the minimum
rather than a mean.

The two guards worth knowing
----------------------------

Clause 5.7 corrects for the background with the ordinary energy subtraction,
not with a table, and it draws two hard lines: under 6 dB "the environmental
conditions are not acceptable", and over 10 dB there is nothing to correct.
[`background_corrected_level_db`](/phonometry/reference/api/noise_control/screen-in-situ/#background_corrected_level_db) refuses the first and skips the second.

Clause 5.9 is the other: the A-weighted attenuation $D_{pA}$ **shall not
be determined when an artificial sound source is used**, because an A-weighted
number belongs to the spectrum that produced it and a loudspeaker's spectrum is
not the machine's. [`screen_attenuation`](/phonometry/reference/api/noise_control/screen-in-situ/#screen_attenuation) refuses it rather than compute a
number the standard forbids.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## background_corrected_level_db

```python
background_corrected_level_db(
    levels_db: ArrayLike,
    background_levels_db: ArrayLike,
) -> NDArray[np.float64]
```

The level with the background taken off, clause 5.7.

$$
L_p = 10 \lg \left(10^{L_{ps}/10} - 10^{L_{pb}/10}\right)
$$

The plain energy subtraction, applied band by band at each measurement
position. Where ISO 11820 corrects from a stepped table, this standard
prints the formula and boxes it.

Clause 5.7 draws the window itself. A margin over 10 dB needs no
correction and the level is returned unchanged. A margin under 6 dB means
"the environmental conditions are not acceptable", which is a refusal and
not a warning: the background it names includes wind-generated noise, so
the remedy is to wait for a quieter day rather than to correct harder.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The level with the sources on, per band, in decibels. |
| `background_levels_db` | The level with them off, per band, in decibels. |

**Returns:** The corrected level per band, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match band for band, or a margin under [`ISO11821_MINIMUM_BACKGROUND_MARGIN_DB`](/phonometry/reference/api/noise_control/screen-in-situ/#iso11821_minimum_background_margin_db). |

## BACKGROUND_CORRECTION_WINDOW_DB

*Constant* (`tuple`).

```python
BACKGROUND_CORRECTION_WINDOW_DB = (6.0, 10.0)
```

## DIRECTIVITY_CIRCLE_RADIUS_M

*Constant* (`float`).

```python
DIRECTIVITY_CIRCLE_RADIUS_M = 1.5
```

## directivity_index_db

```python
directivity_index_db(levels_db: ArrayLike) -> NDArray[np.float64]
```

The directivity index of a source, definition 3.10.

$DI_i = L_{360} - L_{30,i}$, where $L_{360}$ is the
logarithmic mean of the levels at twelve positions evenly spaced on a
horizontal circle of about 1,5 m radius around the source, and
$L_{30,i}$ the level at one of them.

The sign is the way round to notice. Written as the mean less the
position, the index is **positive where the position is quieter than the
mean**, which is the opposite of the directivity index of the emission
standards. Clause 5.2.2 then reads naturally: an artificial source
qualifies while no position falls more than
[`DIRECTIVITY_INDEX_LIMIT_DB`](/phonometry/reference/api/noise_control/screen-in-situ/#directivity_index_limit_db) below the mean, which is a bound on how
much of a shadow the source casts on itself.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The levels at the twelve positions, in decibels. |

**Returns:** $DI_i$ at each position, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a count that is not [`DIRECTIVITY_POSITIONS`](/phonometry/reference/api/noise_control/screen-in-situ/#directivity_positions). |

## DIRECTIVITY_INDEX_LIMIT_DB

*Constant* (`float`).

```python
DIRECTIVITY_INDEX_LIMIT_DB = 8.0
```

## DIRECTIVITY_POSITIONS

*Constant* (`int`).

```python
DIRECTIVITY_POSITIONS = 12
```

## ENGINEERING_STANDARD_DEVIATION_DB

*Constant* (`float`).

```python
ENGINEERING_STANDARD_DEVIATION_DB = 2.0
```

## IMPULSE_INVALID_DEVIATION_DB

*Constant* (`float`).

```python
IMPULSE_INVALID_DEVIATION_DB = 5.0
```

## impulse_mean_level_db

```python
impulse_mean_level_db(repeat_levels_db: ArrayLike) -> float
```

The level of an impulsive measurement, 5.6.2.1.

A single-impulse source is measured at least three times with the S time
weighting, and the level is the **arithmetic** mean of the repeats, not
the energy mean: the clause says "arithmetic mean values" and means it.

The spread decides whether the set counts. Past
[`IMPULSE_REPEAT_DEVIATION_DB`](/phonometry/reference/api/noise_control/screen-in-situ/#impulse_repeat_deviation_db) the clause asks for three more
repeats, which is reported here; past
[`IMPULSE_INVALID_DEVIATION_DB`](/phonometry/reference/api/noise_control/screen-in-situ/#impulse_invalid_deviation_db) the measurement is invalid, which is
refused.

**Parameters**

| Name | Description |
| :--- | :--- |
| `repeat_levels_db` | The levels of the repeats, in decibels. |

**Returns:** The arithmetic mean, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For fewer than [`IMPULSE_REPEATS`](/phonometry/reference/api/noise_control/screen-in-situ/#impulse_repeats) repeats or a spread past [`IMPULSE_INVALID_DEVIATION_DB`](/phonometry/reference/api/noise_control/screen-in-situ/#impulse_invalid_deviation_db). |

## IMPULSE_REPEAT_DEVIATION_DB

*Constant* (`float`).

```python
IMPULSE_REPEAT_DEVIATION_DB = 3.0
```

## IMPULSE_REPEATS

*Constant* (`int`).

```python
IMPULSE_REPEATS = 3
```

## ISO11821_BAND_RANGE_HZ

*Constant* (`mapping`).

```python
ISO11821_BAND_RANGE_HZ = {3: (100.0, 5000.0), 1: (125.0, 4000.0)}
```

## ISO11821_MINIMUM_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO11821_MINIMUM_BACKGROUND_MARGIN_DB = 6.0
```

## ISO11821_PREFERRED_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO11821_PREFERRED_BACKGROUND_MARGIN_DB = 10.0
```

## microphone_distances_m

```python
microphone_distances_m(screen_height_m: float) -> NDArray[np.float64]
```

Where the microphones stand in front of a screen, 5.5.2.

A quarter, a half, once and twice the screen height, along a line
perpendicular to the screen, and never closer than
[`MINIMUM_MICROPHONE_DISTANCE_M`](/phonometry/reference/api/noise_control/screen-in-situ/#minimum_microphone_distance_m). Under 4 m the quarter-height
position falls inside that floor and is pushed out to it; at 2 m and under
the half-height one is pushed out too, and then the two nearest positions
coincide. The clause keeps the floor rather than the factor, so the
returned distances may repeat, and that is the printed rule rather than an
oversight here.

NOTE 2 of 5.5.2 says what the spread of the answers means: the smallest
attenuation will be found at the most remote position and the largest at
the nearest, which is why the Introduction asks for both rather than for
an average.

**Parameters**

| Name | Description |
| :--- | :--- |
| `screen_height_m` | The screen height, in metres. |

**Returns:** The four distances from the screen, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive height. |

## MINIMUM_MICROPHONE_DISTANCE_M

*Constant* (`float`).

```python
MINIMUM_MICROPHONE_DISTANCE_M = 1.0
```

## MINIMUM_SCREEN_DIMENSION_M

*Constant* (`float`).

```python
MINIMUM_SCREEN_DIMENSION_M = 1.5
```

## OPERATOR_HEIGHT_M

*Constant* (`float`).

```python
OPERATOR_HEIGHT_M = 1.55
```

## OPERATOR_HEIGHT_TOLERANCE_M

*Constant* (`float`).

```python
OPERATOR_HEIGHT_TOLERANCE_M = 0.075
```

## OUTDOOR_RANGE_M

*Constant* (`float`).

```python
OUTDOOR_RANGE_M = 25.0
```

## screen_attenuation

```python
screen_attenuation(
    unscreened_levels_db: ArrayLike,
    screened_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    source_kind: SourceKind = 'actual',
    a_weighted_unscreened_level_db: float | None = None,
    a_weighted_screened_level_db: float | None = None,
    distance_m: float | None = None,
) -> ScreenInSituResult
```

The in-situ attenuation of a screen, clauses 5.8 and 5.9.

$D_p = L_{p1} - L_{p2}$, the unscreened level less the screened one
at the same position, band by band. Clause 5.8 adds the condition that
makes the subtraction mean anything: either both levels are time-averaged,
or both are arithmetic means of several $L_{S\text{max}}$ values.
The two kinds are not mixed, and [`impulse_mean_level_db`](/phonometry/reference/api/noise_control/screen-in-situ/#impulse_mean_level_db) is the
second of them.

$D_{pA} = L_{pA1} - L_{pA2}$ is clause 5.9, and it carries the
standard's one flat prohibition: it **shall not be determined when an
artificial sound source is used**. An A-weighted number belongs to the
spectrum that produced it, and a loudspeaker's spectrum is not the
machine's, so the pair is refused rather than computed under
`source_kind="artificial"`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `unscreened_levels_db` | $L_{p1}$ per band, in decibels. |
| `screened_levels_db` | $L_{p2}$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `source_kind` | `"actual"` (default) or `"artificial"`. |
| `a_weighted_unscreened_level_db` | $L_{pA1}$, in decibels. |
| `a_weighted_screened_level_db` | $L_{pA2}$, in decibels. |
| `distance_m` | How far this position stands from the screen, in metres, carried into the result because 5.5.2 reports the spread over the line rather than one number. |

**Returns:** The attenuation, as a [`ScreenInSituResult`](/phonometry/reference/api/noise_control/screen-in-situ/#screeninsituresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, a band centre or a distance that is not strictly positive, an unknown source kind, half an A-weighted pair, or an A-weighted pair with an artificial source. |

## SCREEN_DISTANCE_FACTORS

*Constant* (`tuple`).

```python
SCREEN_DISTANCE_FACTORS = (0.25, 0.5, 1.0, 2.0)
```

## ScreenInSituResult

```python
ScreenInSituResult(
    frequencies: NDArray[np.float64] | None,
    unscreened_levels_db: NDArray[np.float64],
    screened_levels_db: NDArray[np.float64],
    attenuation_db: NDArray[np.float64],
    a_weighted_attenuation_db: float | None,
    source_kind: str,
    distance_m: float | None,
)
```

The in-situ attenuation of a removable screen, ISO 11821 clause 5.8.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal band centres, in hertz, or `None`. |
| `unscreened_levels_db` | $L_{p1}$, the level with the screen removed, per band. |
| `screened_levels_db` | $L_{p2}$, the level with it in place, per band. |
| `attenuation_db` | $D_p$ per band, in decibels. |
| `a_weighted_attenuation_db` | $D_{pA}$, in decibels, or `None`. Clause 5.9 allows it only with the actual source. |
| `source_kind` | `"actual"` or `"artificial"`. |
| `distance_m` | How far the position stands from the screen, in metres, or `None`. |

### ScreenInSituResult.plot()

```python
ScreenInSituResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two levels and the attenuation between them.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.noise_control.plot_screen_in_situ`. |

**Returns:** The `Axes`.

### ScreenInSituResult.rounded()

```python
ScreenInSituResult.rounded() -> NDArray[np.int_]
```

The band values as 7.4 c) reports them, to the nearest integer.

`attenuation_db` keeps the unrounded difference. A tie goes to
the even decibel, Rule A of ISO 80000-1:2009 Annex B, as in the other
in-situ standards of this library.

### ScreenInSituResult.rounded_a_weighted()

```python
ScreenInSituResult.rounded_a_weighted() -> int | None
```

$D_{pA}$ as 7.4 c) reports it, to the nearest integer.

The clause gives the A-weighted attenuation the same rounding as the
band values. `None` where no A-weighted pair was given.

## ScreenInSituWarning

The measurement is outside a condition ISO 11821 states.
