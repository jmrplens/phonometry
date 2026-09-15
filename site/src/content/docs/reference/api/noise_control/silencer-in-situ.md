---
title: "noise_control.silencer_in_situ"
description: "What a silencer does where it was installed (ISO 11820:1996)."
sidebar:
  label: "silencer_in_situ"
---

What a silencer does where it was installed (ISO 11820:1996).

[`phonometry.noise_control.silencer_measurement`](/phonometry/reference/api/noise_control/silencer-measurement/) is the laboratory
measurement a catalogue figure comes from: a qualified rig, a substitution
duct, a stated uncertainty. This is the other one. The silencer is in the
plant, the plant is running, and the question is what the thing is doing
there.

Clause 1.1 puts the relationship between the two in one sentence: results
obtained here **cannot be compared** with performance data obtained from
laboratory measurements to ISO 7235. The reason is in the Introduction: what
is measured in situ carries the flanking transmission, the regenerated flow
noise and the operating conditions with it, and the standard treats all three
as properties of the silencer in that installation rather than as errors to be
removed. A number from this module and a number from a data sheet are two
different quantities, and this library keeps them in two different modules so
that they cannot be added by accident.

Two quantities, twenty installations
------------------------------------

**Transmission loss** $D_{ts}$ compares the sound power reaching the
silencer with the sound power leaving it, Equation (4). **Insertion loss**
$D_{is}$ compares the plant without the silencer with the plant with it,
Equation (8), and it is the only choice for a blowdown silencer, which does
not exist as a duct element to measure through.

Neither is a bare subtraction of levels. Each starts as a sound pressure level
difference, Equation (1) or (3), and becomes a loss by adding the area ratio
of the two measurement surfaces and the difference of the two field
corrections:

$$
D_{ts} = D_{tps} + 10 \lg \frac{S_2}{S_1} + K_2 - K_1
$$

Which areas those are is not a matter of taste. Figure 1 enumerates twenty
installations, sixteen for transmission and four for insertion, by what stands
on each side of the silencer, and clause 9.1.3 gives each of them its own rule
for $S_1$ and $S_2$: a measurement surface in the duct, a quarter
or a half of the silencer intake, a quarter of the room absorption, or a
surface enveloping the open end. [`installation_case`](/phonometry/reference/api/noise_control/silencer-in-situ/#installation_case) is that figure and
those rules as data, so that a measurement says which case it is and the areas
follow.

The corrections that are not a correction
-----------------------------------------

Clause 4 corrects for background noise from a **printed table**, not from the
usual logarithmic subtraction, and the two do not agree: at a margin of 5 dB
the table takes off 2 dB where the formula takes off 1,7, and at 8 dB it takes
off 1 where the formula takes off 0,7. [`silencer_background_correction_db`](/phonometry/reference/api/noise_control/silencer-in-situ/#silencer_background_correction_db)
implements the table as printed, and says so.

Where the extraneous sound can be measured on its own, 9.1.1 and 9.1.2 offer
the energy route of Equations (17) and (18) instead, and cap it: **the maximum
correction is 3 dB**. A measurement that needs more than that does not yield
the quantity at all, and the clause says what may be stated instead, which is
an inequality. [`extraneous_corrected_mean_level_db`](/phonometry/reference/api/noise_control/silencer-in-situ/#extraneous_corrected_mean_level_db) returns whether the
cap was reached so that a capped value cannot be reported as a determination.

Clause 9.1.5 is the one prohibition worth reading twice: converting
one-third-octave data to octave data is permissible **for measured sound
pressure levels only, but not for level differences**.
[`octave_levels_from_third_octave_db`](/phonometry/reference/api/noise_control/silencer-in-situ/#octave_levels_from_third_octave_db) does the permitted conversion, and
the docstring names the function in this library that does the forbidden one
for a different standard.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## DOWNSTREAM_DISTANCE_COEFFICIENTS

*Constant* (`tuple`).

```python
DOWNSTREAM_DISTANCE_COEFFICIENTS = (12.0, 10.0)
```

## extraneous_corrected_mean_level_db

```python
extraneous_corrected_mean_level_db(
    levels_db: ArrayLike,
    extraneous_levels_db: ArrayLike,
) -> tuple[float, bool]
```

The mean level with the extraneous sound taken off, Equations (17) and (18).

$$
\overline{L_p} = 10 \lg \left[\frac{1}{N} \sum_j \left(10^{0,1 L_{pj}} - 10^{0,1 L_{ej}}\right)\right]
$$

The energy route 9.1.1 and 9.1.2 offer instead of Table 1, for the case
where the sources the silencer works on can be switched off and the
extraneous sound measured at the same positions.

The clause caps it: **the maximum correction is 3 dB**. Past that the
quantity is not determined, and what may be stated instead is the
inequality of clause 4. The second return value says whether the cap was
reached, so that a capped number cannot be written down as a
determination.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The levels with everything running, in decibels. |
| `extraneous_levels_db` | The extraneous levels at the same positions, in decibels. |

**Returns:** The corrected mean level in decibels, and whether the correction reached the cap.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match point for point, or an extraneous level at or above the level it is subtracted from. |

## flow_velocity_m_s

```python
flow_velocity_m_s(
    velocity_pressure_pa: ArrayLike,
    density_kg_m3: float,
) -> NDArray[np.float64]
```

The flow velocity a velocity pressure stands for, Equation (28).

$w = \sqrt{2 p_v / \rho}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_pressure_pa` | $p_v$, in pascals. |
| `density_kg_m3` | $\rho$, in kilograms per cubic metre. |

**Returns:** $w$, in metres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive density or a negative velocity pressure. |

## gas_density_kg_m3

```python
gas_density_kg_m3(
    *,
    temperature_c: float,
    molar_mass_kg_kmol: float | None = None,
    ambient_pressure_pa: float = 100000.0,
) -> float
```

The density of the gas, Equation (29).

$$
\rho = \frac{M \, p_{\text{amb}}}{R \, (273 + \theta)}
$$

with $R$ the universal gas constant, printed as 8 314,4 N m per
kmol K, and $M$ the molar mass. The standard adds that
$R/M = 287$ N m per kg K for air, and that is what is used when no
molar mass is given.

[`phonometry.noise_control.normal_air_density`](/phonometry/reference/api/noise_control/silencer-measurement/#normal_air_density) computes the same
quantity for ISO 7235, from a gauge pressure and with that standard's own
two constants; this one takes the absolute ambient pressure the way
Equation (29) prints it and admits any gas through its molar mass.

**Parameters**

| Name | Description |
| :--- | :--- |
| `temperature_c` | $\theta$, in degrees Celsius. |
| `molar_mass_kg_kmol` | $M$, in kilograms per kilomole. Omit it for air. |
| `ambient_pressure_pa` | $p_{\text{amb}}$, in pascals. |

**Returns:** $\rho$, in kilograms per cubic metre.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a temperature that is not finite or at or below the absolute zero the equation uses, or a non-positive pressure or molar mass. |

## in_situ_insertion_loss

```python
in_situ_insertion_loss(
    levels_without_db: ArrayLike,
    levels_with_db: ArrayLike,
    *,
    area_without_m2: float,
    area_with_m2: float,
    frequencies: ArrayLike | None = None,
    field_correction_difference_db: float = 0.0,
    case: int | None = None,
) -> SilencerInSituResult
```

The insertion loss of a silencer in place, Equation (21).

$$
D_{is} = \overline{L_{pII}} - \overline{L_{pI}} + 10 \lg \frac{S_{II}}{S_I} + K_{II} - K_I
$$

The same shape as Equation (19) with the two runs in place of the two
sides. NOTE 5 of 3.4 says that in most cases the two areas are equal and
the two field corrections nearly so, and then both terms fall out and the
loss is the level difference; the arguments are still explicit, because
"in most cases" is not "always" and cases 17 and 19 of Figure 1 are where
it fails.

A blowdown silencer can only be measured this way: there is no duct to
measure through.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_without_db` | $\overline{L_{pII}}$ per band, in decibels. |
| `levels_with_db` | $\overline{L_{pI}}$ per band, in decibels. |
| `area_without_m2` | $S_{II}$, in square metres. |
| `area_with_m2` | $S_I$, in square metres. |
| `frequencies` | Nominal band centres, in hertz. |
| `field_correction_difference_db` | $K_{II} - K_I$, in decibels. |
| `case` | The installation of Figure 1, 17 to 20, carried into the result. |

**Returns:** The loss, as a [`SilencerInSituResult`](/phonometry/reference/api/noise_control/silencer-in-situ/#silencerinsituresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, a non-positive area or band centre, a field correction that is not finite, or a case that is not an insertion one. |

## in_situ_transmission_loss

```python
in_situ_transmission_loss(
    source_levels_db: ArrayLike,
    receiver_levels_db: ArrayLike,
    *,
    source_area_m2: float,
    receiver_area_m2: float,
    frequencies: ArrayLike | None = None,
    field_correction_difference_db: float = 0.0,
    case: int | None = None,
) -> SilencerInSituResult
```

The transmission loss of a silencer in place, Equation (19).

$$
D_{ts} = D_{tps} + 10 \lg \frac{S_2}{S_1} + K_2 - K_1
$$

The level difference of Equation (1), the ratio of the two measurement
areas, and the difference of the two field corrections.
[`installation_case`](/phonometry/reference/api/noise_control/silencer-in-situ/#installation_case) says which areas the installation calls for;
[`temperature_field_correction_db`](/phonometry/reference/api/noise_control/silencer-in-situ/#temperature_field_correction_db) is the correction difference two
temperatures make.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_levels_db` | $\overline{L_{p2}}$ per band, in decibels. |
| `receiver_levels_db` | $\overline{L_{p1}}$ per band, in decibels. |
| `source_area_m2` | $S_2$, in square metres. |
| `receiver_area_m2` | $S_1$, in square metres. |
| `frequencies` | Nominal band centres, in hertz. |
| `field_correction_difference_db` | $K_2 - K_1$, in decibels. |
| `case` | The installation of Figure 1, 1 to 16, carried into the result. |

**Returns:** The loss, as a [`SilencerInSituResult`](/phonometry/reference/api/noise_control/silencer-in-situ/#silencerinsituresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, a non-positive area or band centre, a field correction that is not finite, or a case that is not a transmission one. |

## insertion_level_difference_db

```python
insertion_level_difference_db(
    levels_without_db: ArrayLike,
    levels_with_db: ArrayLike,
) -> NDArray[np.float64]
```

The level difference the silencer made, Equation (3).

$D_{ips} = L_{pII} - L_{pI}$, the level before the silencer was
installed less the level after. Here II is *without* and I is *with*,
which is again the opposite of the reading order, so the arguments say
which run they are.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_without_db` | $L_{pII}$ per band, in decibels. |
| `levels_with_db` | $L_{pI}$ per band, in decibels. |

**Returns:** $D_{ips}$ per band, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match band for band. |

## installation_case

```python
installation_case(number: int) -> InstallationCase
```

One installation of Figure 1, with the area rules clause 9 gives it.

The figure is a matrix: the source side may be a duct, a room with a
diffuse field, a room with a non-diffuse field or an open space, and so
may the receiver side, which is sixteen transmission cases. The four
insertion cases are keyed by the receiver side alone, because the source
side is not part of what is measured.

**Parameters**

| Name | Description |
| :--- | :--- |
| `number` | The case number Figure 1 prints, 1 to 20. |

**Returns:** The case, as an [`InstallationCase`](/phonometry/reference/api/noise_control/silencer-in-situ/#installationcase).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a number outside the figure. |

## INSTALLATION_CASES

*Constant* (`dict`).

## InstallationCase

```python
InstallationCase(
    number: int,
    source_side: str,
    receiver_side: str,
    quantity: str,
    source_area_rule: str,
    receiver_area_rule: str,
)
```

One of the twenty installations of Figure 1, with its area rules.

**Attributes**

| Name | Description |
| :--- | :--- |
| `number` | The case number Figure 1 prints, 1 to 20. |
| `source_side` | What stands on the source side: `"duct"`, `"diffuse_room"`, `"non_diffuse_room"`, `"open_space"`, or `"any"` for the four insertion cases, whose source side is not part of the case. |
| `receiver_side` | The same for the receiver side. |
| `quantity` | `"transmission"` for cases 1 to 16, `"insertion"` for 17 to 20. |
| `source_area_rule` | How 9.1.3 or 9.1.4 says to read $S_2$, the source side of a transmission case, or $S_{II}$, the run without the silencer of an insertion one, in the clause's own words. |
| `receiver_area_rule` | The same for $S_1$ or $S_I$. |

## ISO11820_AIR_GAS_CONSTANT

*Constant* (`float`).

```python
ISO11820_AIR_GAS_CONSTANT = 287.0
```

## ISO11820_AMBIENT_PRESSURE_PA

*Constant* (`float`).

```python
ISO11820_AMBIENT_PRESSURE_PA = 100000.0
```

## ISO11820_BACKGROUND_CORRECTIONS_DB

*Constant* (`dict`).

```python
ISO11820_BACKGROUND_CORRECTIONS_DB = {3: 3.0, 4: 2.0, 5: 2.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
```

## ISO11820_GAS_CONSTANT

*Constant* (`float`).

```python
ISO11820_GAS_CONSTANT = 8314.4
```

## ISO11820_MINIMUM_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO11820_MINIMUM_BACKGROUND_MARGIN_DB = 3.0
```

## ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB = 10.0
```

## ISO11820_OCTAVE_BAND_EXTENDED_RANGE_HZ

*Constant* (`tuple`).

```python
ISO11820_OCTAVE_BAND_EXTENDED_RANGE_HZ = (31.5, 8000.0)
```

## ISO11820_OCTAVE_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
ISO11820_OCTAVE_BAND_RANGE_HZ = (63.0, 4000.0)
```

## ISO11820_SOUND_SPEED_M_S

*Constant* (`float`).

```python
ISO11820_SOUND_SPEED_M_S = 340.0
```

## ISO11820_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ

*Constant* (`tuple`).

```python
ISO11820_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ = (25.0, 10000.0)
```

## ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ = (50.0, 5000.0)
```

## MAXIMUM_EXTRANEOUS_CORRECTION_DB

*Constant* (`float`).

```python
MAXIMUM_EXTRANEOUS_CORRECTION_DB = 3.0
```

## mean_sound_pressure_level_db

```python
mean_sound_pressure_level_db(levels_db: ArrayLike) -> float
```

The mean level over the measuring points, Equation (2).

$$
\overline{L_p} = 10 \lg \left(\frac{1}{N} \sum_j 10^{0,1 L_{pj}}\right)
$$

An energy mean, which is what every clause of the standard means by "mean
sound pressure level".

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The levels at the measuring points, in decibels. |

**Returns:** $\overline{L_p}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty or non-finite set of levels. |

## measurement_distance_downstream_m

```python
measurement_distance_downstream_m(
    downstream_area_m2: float,
    free_area_m2: float,
) -> float
```

How far downstream the measurement surface stands, Equation (16).

$d_d = 12 \sqrt{S_d} - 10 \sqrt{S_f}$, with $S_f$ the free
cross-sectional area of the silencer, which NOTE 18 warns is not the same
thing as its total intake cross-section.

The expression can return zero or less for a silencer whose free area is a
large fraction of the duct it sits in. 8.3.1 has its own escape for that,
which is agreement between the parties on the distances, and the case is
reported rather than returned as a distance nobody can stand at.

**Parameters**

| Name | Description |
| :--- | :--- |
| `downstream_area_m2` | $S_d$, in square metres. |
| `free_area_m2` | $S_f$, in square metres. |

**Returns:** $d_d$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area. |

## measurement_distance_upstream_m

```python
measurement_distance_upstream_m(upstream_area_m2: float) -> float
```

How far upstream the measurement surface stands, Equation (15).

$d_u = 1,5 \sqrt{4 S_u / \pi}$, which is one and a half equivalent
diameters of the upstream measurement cross-section.

**Parameters**

| Name | Description |
| :--- | :--- |
| `upstream_area_m2` | $S_u$, in square metres. |

**Returns:** $d_u$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area. |

## octave_levels_from_third_octave_db

```python
octave_levels_from_third_octave_db(
    levels_db: ArrayLike,
) -> NDArray[np.float64]
```

One-third-octave levels folded into octaves, 9.1.5.

The energy sum of each consecutive group of three. Clause 9.1.5 permits
this conversion **for measured sound pressure levels only, but not for
level differences**, and that sentence is the whole of the clause.

The prohibition is worth stating twice, because this library does perform
the forbidden operation for a different standard:
[`phonometry.noise_control.octave_insertion_loss`](/phonometry/reference/api/noise_control/silencer-measurement/#octave_insertion_loss) folds a
one-third-octave insertion loss into octaves, which is Equation (2) of
ISO 11691 and is exactly what ISO 11820 forbids. The two are not
interchangeable: one is a fold of a measured level, the other a fold of a
difference, and ISO 11820 wants the levels folded on each side and the
difference taken afterwards.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | One-third-octave levels, in decibels, a multiple of three bands in ascending order. |

**Returns:** The octave levels, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a count that is not a multiple of three. |

## reverberant_surface_area_m2

```python
reverberant_surface_area_m2(
    volume_m3: float,
    reverberation_time_s: ArrayLike,
    *,
    speed_of_sound: float = 340.0,
) -> NDArray[np.float64]
```

A quarter of the room absorption, as an area, Equations (6), (10) and (12).

$$
S = \frac{6 \ln 10 \; V}{c \, T}
$$

The three equations are the same expression written three times, for the
receiver room of the transmission measurement and for the room with and
without the silencer of the insertion one. It is a quarter of the Sabine
equivalent absorption area, which is what turns a reverberant level into a
sound power.

The standard prints $c = 340$ m/s "at room temperature"; that value
is the default here and a measurement at another temperature should say
so.

**Parameters**

| Name | Description |
| :--- | :--- |
| `volume_m3` | The room volume, in cubic metres. |
| `reverberation_time_s` | The reverberation time per band, in seconds. |
| `speed_of_sound` | The speed of sound, in metres per second. |

**Returns:** The area, in square metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive volume, time or speed. |

## SABINE_AREA_COEFFICIENT

*Constant* (`float`).

```python
SABINE_AREA_COEFFICIENT = 13.815510557964275
```

## silencer_background_correction_db

```python
silencer_background_correction_db(
    level_difference_db: ArrayLike,
) -> NDArray[np.float64]
```

The background correction of Table 1, in decibels to subtract.

The table is printed stepped and integer-indexed, and it is **not** the
logarithmic subtraction $-10 \lg(1 - 10^{-0,1 \Delta L})$ that most
emission standards use: at a margin of 5 dB it takes off 2 dB where the
formula takes off 1,7, and at 8 dB it takes off 1 where the formula takes
off 0,7. It is implemented as printed.

The table gives no row between its integers. A difference that falls
between two rows is read at the lower one, which is the larger correction
and therefore the lower source level; the standard does not decide this,
and the choice is stated here rather than smoothed away. Above
[`ISO11820_NEGLIGIBLE_BACKGROUND_MARGIN_DB`](/phonometry/reference/api/noise_control/silencer-in-situ/#iso11820_negligible_background_margin_db) there is no row to read
at all: 10 dB is the last one the table prints, and anything over it takes
nothing off, so 10,5 dB is corrected by zero rather than by the 0,5 dB of
the 10 dB row.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference_db` | The difference between the level measured with the source running and the background level alone, in decibels. |

**Returns:** The correction to subtract, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a margin under [`ISO11820_MINIMUM_BACKGROUND_MARGIN_DB`](/phonometry/reference/api/noise_control/silencer-in-situ/#iso11820_minimum_background_margin_db), which Table 1 calls invalid. |

## silencer_flow_velocity_m_s

```python
silencer_flow_velocity_m_s(
    upstream_mean_velocity_m_s: float,
    *,
    upstream_area_m2: float,
    free_area_m2: float,
) -> float
```

The mean velocity inside the silencer, Equation (31).

$\overline{w_f} = (S_u / S_f) \, \overline{w_u}$, the upstream mean
velocity scaled by how much the silencer narrows the passage. It is the
velocity the regenerated noise of the installation answers to, which is
why 9.2 asks for it rather than for the duct velocity.

**Parameters**

| Name | Description |
| :--- | :--- |
| `upstream_mean_velocity_m_s` | $\overline{w_u}$, in metres per second, the arithmetic mean of Equation (30). |
| `upstream_area_m2` | $S_u$, in square metres. |
| `free_area_m2` | $S_f$, the free cross-section, in square metres. |

**Returns:** $\overline{w_f}$, in metres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area. |

## SilencerInSituResult

```python
SilencerInSituResult(
    frequencies: NDArray[np.float64] | None,
    level_difference_db: NDArray[np.float64],
    area_term_db: float,
    field_correction_difference_db: float,
    loss_db: NDArray[np.float64],
    quantity: str,
    case: InstallationCase | None,
)
```

A silencer measured where it stands, ISO 11820 Equation (19) or (21).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal band centres, in hertz, or `None`. |
| `level_difference_db` | $D_{tps}$ or $D_{ips}$, the sound pressure level difference the loss is built on, per band. |
| `area_term_db` | $10 \lg(S_2/S_1)$ or $10 \lg(S_{II}/S_I)$, in decibels. |
| `field_correction_difference_db` | $K_2 - K_1$ or $K_{II} - K_I$, in decibels. |
| `loss_db` | $D_{ts}$ or $D_{is}$ per band, in decibels. |
| `quantity` | `"transmission"` or `"insertion"`. |
| `case` | The installation of Figure 1 the measurement was made in, or `None` where the caller did not name one. |

### SilencerInSituResult.plot()

```python
SilencerInSituResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the level difference and the loss it becomes.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.noise_control.plot_silencer_in_situ`. |

**Returns:** The `Axes`.

### SilencerInSituResult.symbol

*property*

The symbol clause 11 reports this as, `"D_ts"` or `"D_is"`.

## SilencerInSituWarning

The measurement is outside a condition ISO 11820 states.

## sound_power_level_db

```python
sound_power_level_db(
    mean_level_db: ArrayLike,
    *,
    area_m2: ArrayLike,
    field_correction_db: ArrayLike = 0.0,
) -> NDArray[np.float64]
```

A mean level read as a sound power, Equations (5), (7), (9) and (11).

$$
L_W = \overline{L_p} + 10 \lg \frac{S}{S_0} + K, \qquad S_0 = 1\ \text{m}^2
$$

The four equations differ only in which side of the silencer and which run
they belong to. $S$ is whichever area the case calls for, from
[`installation_case`](/phonometry/reference/api/noise_control/silencer-in-situ/#installation_case), and $K$ the field correction of Annex A,
which NOTE 4 expects to stay under
[`TYPICAL_FIELD_CORRECTION_LIMIT_DB`](/phonometry/reference/api/noise_control/silencer-in-situ/#typical_field_correction_limit_db) in absolute value once the areas
have been chosen as 3.3 and 3.4 define them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `mean_level_db` | $\overline{L_p}$ per band, in decibels. |
| `area_m2` | $S$, in square metres. |
| `field_correction_db` | $K$, in decibels. |

**Returns:** $L_W$ per band, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area or mismatched shapes. |

## static_pressure_difference_pa

```python
static_pressure_difference_pa(
    total_pressure_loss_pa: float,
    *,
    volume_flow_m3_s: float,
    density_kg_m3: float,
    upstream_area_m2: float,
    downstream_area_m2: float,
) -> float
```

The static pressure difference behind a change of area, Equation (14).

$$
\Delta p_S = \Delta p_T - \frac{\rho \, q_V^2}{2} \left(\frac{1}{S_u^2} - \frac{1}{S_d^2}\right)
$$

For a silencer whose inlet and outlet areas differ, where the gas
temperature does not vary markedly. With equal areas the bracket vanishes
and the two pressure differences are the same number, which is what 3.5
says in words.

**Parameters**

| Name | Description |
| :--- | :--- |
| `total_pressure_loss_pa` | $\Delta p_T$, in pascals. |
| `volume_flow_m3_s` | $q_V$, in cubic metres per second. |
| `density_kg_m3` | $\rho$, in kilograms per cubic metre. |
| `upstream_area_m2` | $S_u$, in square metres. |
| `downstream_area_m2` | $S_d$, in square metres. |

**Returns:** $\Delta p_S$, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a value that is not finite, or a non-positive density or area. |

## temperature_field_correction_db

```python
temperature_field_correction_db(
    *,
    receiver_temperature_c: float,
    source_temperature_c: float,
) -> float
```

The field correction difference two temperatures make, Equations (20) and (22).

$$
K_2 - K_1 = 5 \lg \frac{273 + \theta_1}{273 + \theta_2}
$$

Unless Annex A gives a reason to say otherwise, the field corrections
account for markedly different temperatures on the two sides and for
nothing else. The standard explains the term by the speed of sound alone,
and that is where the ratio comes out upside down: the factor from squared
pressure to power is the characteristic impedance, and at one ambient
pressure the standard's own Equation (29) makes the density fall as
$1/T$ while $c$ rises as $\sqrt{T}$, so
$\rho c$ falls as $T^{-1/2}$ and the correction rises with
temperature. The printed form is returned unchanged, because a reader
holding ISO 11820 has to find the standard's own number; the defect is
registered in `docs/ERRATA.md` under "ISO 11820:1996, Equations (20) and
(22)".

The same expression is Equation (22) with the two runs of an insertion
measurement in place of the two sides: there $\theta_I$ is the
temperature with the silencer and $\theta_{II}$ without, and the
correction it returns is $K_{II} - K_I$. Pass the with-silencer
temperature as the receiver one and the without-silencer temperature as
the source one, which is the ordering the two equations share.

The standard writes 273 rather than 273,15, and that is what is used.

**Parameters**

| Name | Description |
| :--- | :--- |
| `receiver_temperature_c` | $\theta_1$ on the receiver side, or $\theta_I$ with the silencer, in degrees Celsius. |
| `source_temperature_c` | $\theta_2$ on the source side, or $\theta_{II}$ without the silencer, in degrees Celsius. |

**Returns:** $K_2 - K_1$ or $K_{II} - K_I$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a temperature that is not finite or at or below the absolute zero the equation uses. |

## total_pressure_loss_pa

```python
total_pressure_loss_pa(
    upstream_total_pressure_pa: float,
    downstream_total_pressure_pa: float,
) -> float
```

The total pressure loss of the silencer, Equation (13).

$\Delta p_T = \overline{p_{Tu}} - \overline{p_{Td}}$, the mean total
pressure upstream less the mean total pressure downstream, each of them
the arithmetic mean of Equations (23) and (25). Where the inlet and outlet
areas are equal and neither temperature nor density changes much, this is
also the static pressure difference.

**Parameters**

| Name | Description |
| :--- | :--- |
| `upstream_total_pressure_pa` | $\overline{p_{Tu}}$, in pascals, as a difference from the ambient pressure. |
| `downstream_total_pressure_pa` | $\overline{p_{Td}}$, in pascals, on the same basis. |

**Returns:** $\Delta p_T$, in pascals.

## transmission_level_difference_db

```python
transmission_level_difference_db(
    source_levels_db: ArrayLike,
    receiver_levels_db: ArrayLike,
) -> NDArray[np.float64]
```

The level difference across the silencer, Equation (1).

$D_{tps} = \overline{L_{p2}} - \overline{L_{p1}}$, the mean level on
the source side less the mean level on the receiver side. The arguments
are named for the side rather than for the subscript, because 1 is the
receiver and 2 the source, which is the opposite of the order most readers
expect.

NOTE 2 of 3.1: this is not a result of its own but the step Equation (19)
turns into a transmission loss.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_levels_db` | $\overline{L_{p2}}$ per band, in decibels. |
| `receiver_levels_db` | $\overline{L_{p1}}$ per band, in decibels. |

**Returns:** $D_{tps}$ per band, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match band for band. |

## TYPICAL_FIELD_CORRECTION_LIMIT_DB

*Constant* (`float`).

```python
TYPICAL_FIELD_CORRECTION_LIMIT_DB = 3.0
```

## UPSTREAM_DISTANCE_DIAMETERS

*Constant* (`float`).

```python
UPSTREAM_DISTANCE_DIAMETERS = 1.5
```

## velocity_pressure_pa

```python
velocity_pressure_pa(
    total_pressure_pa: ArrayLike,
    static_pressure_pa: ArrayLike,
) -> NDArray[np.float64]
```

The velocity pressure, Equation (27).

$p_v = p_T - p_S$, the total pressure less the static pressure, both
reported as differences from the ambient atmospheric pressure as 8.3.2
asks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `total_pressure_pa` | $p_T$, in pascals. |
| `static_pressure_pa` | $p_S$, in pascals. |

**Returns:** $p_v$, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match. |

## VELOCITY_UNIFORMITY_TOLERANCE_PERCENT

*Constant* (`float`).

```python
VELOCITY_UNIFORMITY_TOLERANCE_PERCENT = 10.0
```
