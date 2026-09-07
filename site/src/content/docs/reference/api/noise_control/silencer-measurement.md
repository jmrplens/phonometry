---
title: "noise_control.silencer_measurement"
description: "Insertion loss of a ducted silencer, measured by substitution."
sidebar:
  label: "silencer_measurement"
---

Insertion loss of a ducted silencer, measured by substitution.

Everything a silencer model computes comes from geometry. The figure a
supplier publishes does not: it is an **insertion loss measured by
substitution**, and this module is the arithmetic of that measurement.

Two standards share the method and differ only in how much rigour they ask
of the laboratory:

* **ISO 7235:2003** (published in Europe as EN ISO 7235:2009) is the full
  procedure, with a modal filter between the source and the test object, a
  qualified receiving side, and a stated measurement uncertainty. It covers
  silencers, air-terminal units and other duct elements, with and without
  flow.
* **ISO 11691:1995** (EN ISO 11691:2009) is the survey-grade laboratory
  method without flow, for silencers up to a design velocity of 15 m/s. It
  is six printed pages and carries two equations.

The measurement is the same subtraction in both. Run the rig once with a
plain **substitution duct** in place of the silencer, run it again with the
silencer installed, and take the difference band by band:

$$
D_\mathrm{i} = L_{W\mathrm{II}} - L_{W\mathrm{I}}
$$

where $\mathrm{I}$ is the series with the test object and
$\mathrm{II}$ the series with the substitution duct. ISO 11691 writes
the same thing as $D = L_{p1} - L_{p2}$ with the substitution duct
first, and ISO 7235 6.3 adds the reverberation-time term
$10 \lg(T_2 / T_1)$ when the receiving room's absorption moved between
the two series. [`substitution_insertion_loss`](/phonometry/reference/api/noise_control/silencer-measurement/#substitution_insertion_loss) is all three.

What the subtraction is **not** is a transmission loss. It is measured
against a particular substitution duct in a particular rig, so it carries
the rig with it: the flanking path along the duct walls sets a **limiting
insertion loss** the facility cannot measure past, and the receiving side
decides how much of the sound the microphones see at all. A catalogue
figure is a claim about the arrangement as much as about the device, which
is why ISO 7235 makes the arrangement reportable.

The rest of the module is the bookkeeping that goes with the subtraction:

* [`octave_insertion_loss`](/phonometry/reference/api/noise_control/silencer-measurement/#octave_insertion_loss) folds three one-third-octave values into
  the octave that contains them, which ISO 11691 does on the transmitted
  energy rather than on the decibels;
* [`microphone_spread_limit`](/phonometry/reference/api/noise_control/silencer-measurement/#microphone_spread_limit) and
  [`microphone_positions_required`](/phonometry/reference/api/noise_control/silencer-measurement/#microphone_positions_required) are ISO 7235 Table 6, the rule that
  sends a test duct from three microphone positions to five;
* [`survey_reproducibility`](/phonometry/reference/api/noise_control/silencer-measurement/#survey_reproducibility), [`measurement_reproducibility`](/phonometry/reference/api/noise_control/silencer-measurement/#measurement_reproducibility) and
  [`measurement_expanded_uncertainty`](/phonometry/reference/api/noise_control/silencer-measurement/#measurement_expanded_uncertainty) are the two standards' own answers to how
  repeatable any of this is.

The plane-wave modelling this measurement is compared against lives in
[`phonometry.noise_control.silencers`](/phonometry/reference/api/noise_control/silencers/), and the cut-on frequency above
which a duct stops carrying plane waves alone is in
[`phonometry.noise_control.duct_modes`](/phonometry/reference/api/noise_control/duct-modes/).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ISO11691_REPRODUCIBILITY

*Constant* (`tuple`).

```python
ISO11691_REPRODUCIBILITY = ((1250.0, 2.0), (10000.0, 3.0))
```

## ISO7235_COVERAGE_FACTOR

*Constant* (`float`).

```python
ISO7235_COVERAGE_FACTOR = 2.0
```

## ISO7235_REPRODUCIBILITY

*Constant* (`dict`).

```python
ISO7235_REPRODUCIBILITY = {'insertion_loss': ((100.0, 1.5), (500.0, 1.0), (1250.0, 2.0), (10000.0, 3.0)), 'transmission_loss': ((100.0, 3.0), (500.0, 3.0), (1250.0, 3.0), (10000.0, 3.0)), 'intensity': ((100.0, 3.0), (500.0, 1.5), (1250.0, 1.0), (5000.0, 1.0))}
```

## ISO7235_SPREAD_LIMITS

*Constant* (`tuple`).

```python
ISO7235_SPREAD_LIMITS = ((50.0, 10.0), (63.0, 10.0), (80.0, 8.0), (100.0, 8.0), (125.0, 7.0), (160.0, 6.0))
```

## measurement_expanded_uncertainty

```python
measurement_expanded_uncertainty(
    frequency: float,
    *,
    quantity: str = 'insertion_loss',
) -> float
```

ISO 7235 7.9: twice the reproducibility, for 95 % coverage.

Unless the laboratory knows better, the expanded uncertainty it records
is twice the standard deviation of Table 7. That puts a measured
insertion loss of 25 dB at 250 Hz within 2 dB of the truth and the same
figure at 4 kHz within 6.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | The one-third-octave band centre, in Hz. |
| `quantity` | The column of Table 7, as in [`measurement_reproducibility`](/phonometry/reference/api/noise_control/silencer-measurement/#measurement_reproducibility). |

**Returns:** The expanded uncertainty, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As [`measurement_reproducibility`](/phonometry/reference/api/noise_control/silencer-measurement/#measurement_reproducibility). |

## measurement_reproducibility

```python
measurement_reproducibility(
    frequency: float,
    *,
    quantity: str = 'insertion_loss',
) -> float
```

ISO 7235 Table 7: the reproducibility standard deviation.

The three columns do not agree with one another, and that is the useful
part. Insertion loss is measured best in the middle of the range, 1 dB
from 125 to 500 Hz, and worst at the top, 3 dB above 1,6 kHz. The
sound-intensity route runs the other way, 3 dB at the bottom and 1 dB in
the top two ranges. Transmission loss is a flat 3 dB everywhere, which is
the mark of an estimate rather than a measurement: 7.9 says only the
insertion-loss column came from tests, on 1 m long parallel-baffle
silencers, and that the other two rest on experience.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | The one-third-octave band centre, in Hz. |
| `quantity` | `"insertion_loss"`, `"transmission_loss"` or `"intensity"`, choosing the column. |

**Returns:** $\sigma_R$, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the frequency is not positive and finite, if it is above the range the column covers, or if the quantity is not one of the three the table prints. |

## microphone_positions_required

```python
microphone_positions_required(levels: ArrayLike, frequency: float) -> int
```

ISO 7235 6.2.1: three microphone positions, or five.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | The band levels measured at the three key positions, in dB. Exactly three are expected, because the rule is about whether three were enough. |
| `frequency` | The one-third-octave band centre, in Hz. |

**Returns:** `3` if the three positions agree closely enough for the band, `5` if the standard asks for two more.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite, if there are not three of them, or if the frequency is not positive and finite. |

## microphone_spread_limit

```python
microphone_spread_limit(frequency: float) -> float
```

ISO 7235 Table 6: how far three positions may disagree.

A spatial average in a test duct is taken from at least three microphone
positions equally spaced on a line across the duct. If the highest and
the lowest of the three differ by more than the limit of Table 6, three
positions are not enough to describe the field and five shall be used.

The limit falls with frequency, from 10 dB at 50 and 63 Hz to 6 dB from
160 Hz upwards, because a duct at low frequency has a standing-wave
pattern the three points sample badly and at high frequency does not.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | The one-third-octave band centre, in Hz. |

**Returns:** The largest tolerated difference between the three positions, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the frequency is not positive and finite. |

## octave_insertion_loss

```python
octave_insertion_loss(insertion_loss: ArrayLike) -> NDArray[np.float64]
```

ISO 11691 Equation (2): three one-third octaves into their octave.

$$
D_\mathrm{oct} = -10 \lg\left[\frac{1}{3}\left( 10^{-D_1/10} + 10^{-D_2/10} + 10^{-D_3/10} \right)\right]\ \text{dB}
$$

The average is taken on what the silencer *lets through*, not on the
decibels, and the two are not the same thing. A silencer that gives 30,
30 and 5 dB across an octave gives 9,8 dB over the octave, not 21,7: the
band that leaks decides the answer, because it is the one carrying nearly
all of the transmitted energy. That is the whole reason the standard
writes the equation out rather than letting a reader average the numbers.

ISO 11691 states the assumption it rests on: the sound pressure levels of
the three one-third octaves are taken to be equal in the series run with
the substitution duct, so their energies can be weighted equally here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `insertion_loss` | One-third-octave insertion losses in dB, in ascending frequency order, a multiple of three of them. Each consecutive group of three is one octave. |

**Returns:** $D_\mathrm{oct}$, in dB, a third as many values.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a value is not finite, if the array is empty, or if it does not hold a multiple of three bands. |

## SilencerMeasurementWarning

A substitution measurement is outside the range its method covers.

Raised when a test arrangement falls outside a limit the standard writes
down but does not make an error: an area ratio outside the 0,6 to 1,7 of
ISO 11691 4.5, or a band outside the 50 Hz to 10 kHz both standards
measure over. The arithmetic still runs, because a laboratory may report
such a value as long as it says so.

## substitution_area_ratio

```python
substitution_area_ratio(duct_area: float, element_area: float) -> float
```

ISO 11691 4.5: the test duct against the silencer it feeds.

The survey method wants the test ducts to be close in cross section to
what they connect to. Outside the range of 0,6 to 1,7 the ducts are no
longer standing in for the installation the silencer will see, and the
reflections at the two joints stop being negligible; inside it,
transition elements may be fitted.

**Parameters**

| Name | Description |
| :--- | :--- |
| `duct_area` | The cross-sectional area of the test duct, in m². |
| `element_area` | The cross-sectional area of the silencer or of the substitution duct, in m². |

**Returns:** The ratio of the two areas, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an area is not positive and finite. |

**Warns**

| Warning | When |
| :--- | :--- |
| SilencerMeasurementWarning | If the ratio is outside 0,6 to 1,7. |

## substitution_insertion_loss

```python
substitution_insertion_loss(
    substitution_level: ArrayLike,
    object_level: ArrayLike,
    *,
    reverberation_times: tuple[ArrayLike, ArrayLike] | None = None,
) -> NDArray[np.float64]
```

The insertion loss of the two test series, band by band.

$$
D_\mathrm{i} = L_{W\mathrm{II}} - L_{W\mathrm{I}} \quad\text{and}\quad D_\mathrm{i} = \overline{L_{p1}} - \overline{L_{p2}} + 10 \lg \frac{T_2}{T_1}\ \text{dB}
$$

Both printings are the same subtraction: the level measured **without**
the test object minus the level measured **with** it. ISO 7235 numbers
the series so that $\mathrm{I}$ carries the test object and
$\mathrm{II}$ the substitution duct (Equation (1)); ISO 11691
numbers them the other way, $L_{p1}$ for the substitution duct and
$L_{p2}$ for the silencer (Equation (1) of that standard). The
argument names here follow what was in the duct rather than either
numbering, so neither convention can be entered backwards without the
sign of the answer saying so.

The optional reverberation times are ISO 7235 6.3: if the receiving
room's absorption moved between the two series, the level difference is
not yet the insertion loss and $10 \lg(T_2 / T_1)$ puts it right,
with $T_2$ the time measured with the test object installed. When
the test object sits outside the room, 6.3 allows $T_2 = T_1$, and
then the term is zero and the pair can be left out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `substitution_level` | The band levels of the series run with the substitution duct in place of the test object, in dB. |
| `object_level` | The band levels of the series run with the test object installed, in dB. |
| `reverberation_times` | Optionally `(T_1, T_2)` in s, the reverberation times of the substitution series and of the test-object series, for the correction of 6.3. One value stands for every band. |

**Returns:** $D_\mathrm{i}$, in dB, one value per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a level is not finite, if the arguments do not all carry the same number of bands, or if a reverberation time is not positive and finite. |

## SURVEY_AREA_RATIO_RANGE

*Constant* (`tuple`).

```python
SURVEY_AREA_RATIO_RANGE = (0.6, 1.7)
```

## SURVEY_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
SURVEY_BAND_RANGE_HZ = (50.0, 10000.0)
```

## SURVEY_DIAMETER_RANGE_M

*Constant* (`tuple`).

```python
SURVEY_DIAMETER_RANGE_M = (0.08, 2.0)
```

## SURVEY_MAX_VELOCITY_M_S

*Constant* (`float`).

```python
SURVEY_MAX_VELOCITY_M_S = 15.0
```

## survey_reproducibility

```python
survey_reproducibility(frequency: float) -> float
```

ISO 11691 Table 1: the survey method's own reproducibility.

Two decibels up to the 1,25 kHz one-third octave and three above it.
ISO 11691 makes no claim of its own beyond that: it says outright that
exact information on the precision cannot be given, that interlaboratory
tests would be needed for a real `sigma_R`, and that this estimate is
what makes it a survey standard.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | The one-third-octave band centre, in Hz. |

**Returns:** $\sigma_R$, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the frequency is not positive and finite, or above the 10 kHz the table stops at. |
