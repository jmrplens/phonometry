---
title: "noise_control.enclosure_insulation"
description: "What an enclosure is worth, measured rather than predicted (ISO 11546)."
sidebar:
  label: "enclosure_insulation"
---

What an enclosure is worth, measured rather than predicted (ISO 11546).

[`phonometry.noise_control.enclosures`](/phonometry/reference/api/noise_control/enclosures/) predicts what a box around a
machine will do from its walls and its lining. This module is the other half:
the measurement that says what the box built actually does, and the arithmetic
by which a manufacturer may declare it.

The quantity is a **difference of two runs**. Determine the machine's sound
power without the enclosure, determine it again with the enclosure in place,
and subtract band by band:

$$
D_W = L_{W,\text{without}} - L_{W,\text{with}}
$$

That is Equation (1) of both parts, and Equations (2) to (5) are the same
subtraction on the A-weighted total, on a sound pressure level at a stated
position and, in part 1, on the pair of levels the reciprocity method reads. Nothing here is a transmission loss: an insertion loss carries the
source, the room and the mounting with it, which is why the standard makes all
three reportable.

Two parts, one procedure
------------------------

**ISO 11546-1:1995** measures in a laboratory, for a **declaration**: the
manufacturer's figure, obtained under conditions the buyer can compare across
suppliers. **ISO 11546-2:1995** measures the same thing **in situ**, for an
**acceptance**: the enclosure as installed, in the room it was installed in,
with the machine it was built for. The two documents share their definitions,
their equations, their reporting rules and their artificial source word for
word; what changes is the environment, the base standard the levels come from
and, in part 2, an annex that asks whether the room is good enough at all.

Where the machine cannot be run, both parts substitute a source for it, and
the substitution is what the choice in [`applicable_methods`](/phonometry/reference/api/noise_control/enclosure-insulation/#applicable_methods) is about:

* an **actual** source, the machine itself, which is the normal case;
* the **reciprocity** method of part 1, 7.2, which puts the enclosure in a
  diffuse field and measures inside it, giving $D_{pr}$;
* an **artificial** source, the tapping machine of Annex A on its undamped
  steel plate, used at several positions inside the enclosure.

Clause 1 draws the scope around the first of those: the part applies without
restriction to a free-standing enclosure smaller than
[`UNRESTRICTED_ENCLOSURE_VOLUME_M3`](/phonometry/reference/api/noise_control/enclosure-insulation/#unrestricted_enclosure_volume_m3), and a larger one may still be
measured **with its actual source**, provided the base standard's own limit on
volume is met.

What this module computes, and what it refuses to
-------------------------------------------------

Every equation of clauses 6 and 7 is here, with the weighted rating of
ISO 717-1 delegated to [`phonometry.building.weighted_rating`](/phonometry/reference/api/building/ratings/#weighted_rating) rather than
re-derived, and the A-weighted estimate of the annexes written so that it
cannot disagree with its own inputs: [`estimated_a_weighted_insulation`](/phonometry/reference/api/noise_control/enclosure-insulation/#estimated_a_weighted_insulation)
reduces algebraically to the difference of the two A-weighted totals computed
from the same assumed spectrum, which is the only exact oracle either part
offers.

Annex A is a hardware drawing and Annex B an illustration; their numbers are
constants here and nothing more. Clause 5 is instrumentation, clause 8 hands
its uncertainty to the base standard and to ISO 4871, and clauses 9 and 10 are
a report. The one piece of clause 9 that computes is the rounding of
9.4, which is [`EnclosureInsulationResult.rounded`](/phonometry/reference/api/noise_control/enclosure-insulation/#enclosureinsulationresultrounded).

Neither part prints a worked example, so the tests are anchored where the
documents allow: the algebraic identities of the subtraction, the closed form
behind Figure C.1 of part 2, which is cross-checked against
[`phonometry.emission.environmental_correction`](/phonometry/reference/api/power/sound-power/#environmental_correction), and the printed
thresholds and tables.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## applicable_methods

```python
applicable_methods(
    *,
    condition: EnclosureCondition = 'laboratory',
    source_kind: SourceKind = 'actual',
) -> tuple[MethodEntry, ...]
```

The rows of Table 1 open to a given condition and source.

Reading the table is what stops a declaration claiming more than its
method can give: a survey-grade determination hands back an A-weighted
number and nothing per band, so $D_W$ cannot be declared from it,
and the reciprocity method exists only in the laboratory.

**Parameters**

| Name | Description |
| :--- | :--- |
| `condition` | `"laboratory"` (default) or `"in-situ"`. |
| `source_kind` | `"actual"` (default), `"reciprocity"` or `"artificial"`. |

**Returns:** The rows, as [`MethodEntry`](/phonometry/reference/api/noise_control/enclosure-insulation/#methodentry) values.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown condition or source kind, or a combination the standard does not have. |

## ARTIFICIAL_SOURCE_DROP_MM

*Constant* (`float`).

```python
ARTIFICIAL_SOURCE_DROP_MM = 40.0
```

## ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB

*Constant* (`float`).

```python
ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB = 110.0
```

## artificial_source_insulation

```python
artificial_source_insulation(
    level_without_by_position: ArrayLike,
    level_with_by_position: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    quantity: str = 'sound_power',
    condition: EnclosureCondition = 'laboratory',
    band_fraction: int = 3,
) -> EnclosureInsulationResult
```

Insertion loss with the tapping source of Annex A, 7.3 of part 1 and 7.2 of part 2.

The plate is dropped at each of several positions, the band difference is
formed at each, and the positions are averaged **arithmetically**: "express
the final result as the arithmetic mean value of the results for the
different source positions" is the clause's own sentence, and it is not the
energy mean used almost everywhere else in this library, so it is written
out here rather than borrowed.

The clause sends the levels to Equation (1) or to Equation (3) depending on
which determination was made, so the method yields $D_W$ or
$D_p$ and 9.4 e) reports whichever it was. That is `quantity`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_without_by_position` | Levels without the enclosure, one row per source position, in decibels. |
| `level_with_by_position` | The same with the enclosure, row for row, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `quantity` | `"sound_power"` (default) for Equation (1), or `"sound_pressure"` for Equation (3). |
| `condition` | `"laboratory"` for part 1, `"in-situ"` for part 2. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The averaged insertion loss, as an [`EnclosureInsulationResult`](/phonometry/reference/api/noise_control/enclosure-insulation/#enclosureinsulationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For arrays that are not two-dimensional and matched, fewer than two source positions, or an unknown quantity. |

## ARTIFICIAL_SOURCE_LEAK_RATIO_ADVISORY

*Constant* (`float`).

```python
ARTIFICIAL_SOURCE_LEAK_RATIO_ADVISORY = 0.02
```

## ARTIFICIAL_SOURCE_MAX_FILL_RATIO

*Constant* (`float`).

```python
ARTIFICIAL_SOURCE_MAX_FILL_RATIO = 0.25
```

## ARTIFICIAL_SOURCE_PLATE_MM

*Constant* (`tuple`).

```python
ARTIFICIAL_SOURCE_PLATE_MM = (4.0, 800.0, 300.0)
```

## ARTIFICIAL_SOURCE_STANDOFF_MM

*Constant* (`float`).

```python
ARTIFICIAL_SOURCE_STANDOFF_MM = 60.0
```

## EnclosureInsulationResult

```python
EnclosureInsulationResult(
    frequencies: NDArray[np.float64] | None,
    level_without: NDArray[np.float64],
    level_with: NDArray[np.float64],
    insulation: NDArray[np.float64],
    quantity: str,
    a_weighted_insulation: float | None,
    condition: str,
    source_kind: str,
    base_standard: str,
    band_fraction: int,
)
```

The insertion loss of an enclosure, band by band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal band centre frequencies, in hertz, or `None` when the levels were given without them. |
| `level_without` | The level measured without the enclosure, in decibels. |
| `level_with` | The level measured with it, in decibels. |
| `insulation` | $D_W$, $D_p$ or $D_{pr}$ per band, in decibels. |
| `quantity` | What was subtracted: `"sound_power"`, `"sound_pressure"` or `"reciprocity"`. |
| `a_weighted_insulation` | $D_{WA}$ or $D_{pA}$ of Equation (2) or (4), in decibels, or `None` when no band centres were given and no A-weighted pair was supplied. For the two standards of Table 1 that determine an A-weighted value alone, a single pair of levels is that value, and it is carried here. |
| `condition` | `"laboratory"` (part 1) or `"in-situ"` (part 2). |
| `source_kind` | `"actual"`, `"reciprocity"` or `"artificial"`. |
| `base_standard` | The standard the levels were determined by. |
| `band_fraction` | 3 for one-third octaves, 1 for octaves. |

### EnclosureInsulationResult.plot()

```python
EnclosureInsulationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two runs and the difference between them.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.noise_control.plot_enclosure_insulation`. |

**Returns:** The `Axes`.

### EnclosureInsulationResult.rounded()

```python
EnclosureInsulationResult.rounded() -> NDArray[np.int_]
```

The band values as clause 9.4 reports them, to the nearest decibel.

## EnclosureInsulationWarning

The measurement is outside a condition ISO 11546 states.

## estimated_a_weighted_insulation

```python
estimated_a_weighted_insulation(
    spectrum_levels: ArrayLike,
    insulation: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> float
```

The A-weighted insulation an enclosure would give a stated spectrum.

Annex C of part 1 and Annex D of part 2, the same formula:

$$
D_{WA,e} = L_A - 10 \lg \sum_i 10^{0,1 (L_i - A_i - D_i)}
$$

where $L_i$ is the assumed source spectrum, $A_i$ the
A-weighting of the band and $D_i$ the measured insulation. The sign
of $A_i$ is the trap: the standard prints an attenuation, positive
where the weighting takes level away, while this library's band
corrections are the correction itself, so $A_i = -C_k$. Both terms
are formed here from the same table, so the total and the sum cannot
disagree, and with $D_i = 0$ the answer is exactly zero.

The same formula serves $D_W$ (giving $D_{WA,e}$),
$D_p$ and $D_{pr}$; which one it is, is the caller's.

**Parameters**

| Name | Description |
| :--- | :--- |
| `spectrum_levels` | The assumed source spectrum $L_i$ per band, in decibels. |
| `insulation` | The measured insulation $D_i$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |

**Returns:** $D_{WA,e}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For inputs that do not match band for band. |

## fill_ratio

```python
fill_ratio(source_volume_m3: float, interior_volume_m3: float) -> float
```

How much of the enclosure the source fills, 3.15 of part 1 and 3.13 of part 2.

$\phi = V_S / V_E$. The artificial source of Annex A is
representative only up to
[`ARTIFICIAL_SOURCE_MAX_FILL_RATIO`](/phonometry/reference/api/noise_control/enclosure-insulation/#artificial_source_max_fill_ratio); past that it is changing the
interior field it is supposed to be measuring through.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_volume_m3` | The volume of the source, in cubic metres. |
| `interior_volume_m3` | The interior volume of the enclosure, in cubic metres. |

**Returns:** The ratio, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive volume. |

## leak_ratio

```python
leak_ratio(opening_area_m2: float, interior_surface_area_m2: float) -> float
```

How open an enclosure or a cabin is.

$\theta = S_O / S_E$, the area of the openings over the area of the
interior surface: definition 3.16 of ISO 11546-1, 3.14 of ISO 11546-2 and
3.14 of ISO 11957, in the same words in all three. What they do with it
differs: clause 4 of ISO 11546 only prefers a value under 2 %, while clause
1 of ISO 11957 makes the same 2 % a condition of applicability.

An opening fitted with an effective silencer does not count as one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `opening_area_m2` | The total area of the openings, in square metres. |
| `interior_surface_area_m2` | The interior surface area, openings included, in square metres. |

**Returns:** The ratio, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area. |

## MANDATORY_BAND_RANGE_HZ

*Constant* (`mapping`).

```python
MANDATORY_BAND_RANGE_HZ = {3: (100.0, 5000.0), 1: (125.0, 4000.0)}
```

## MethodEntry

```python
MethodEntry(
    base_standard: str,
    test_environment: str,
    quantities: tuple[str, ...],
    subclause: str,
    band_values: bool,
    survey_grade_excluded: bool = False,
)
```

One row of Table 1: a way of measuring and what it yields.

**Attributes**

| Name | Description |
| :--- | :--- |
| `base_standard` | The standard the levels come from. |
| `test_environment` | The environment the row names for it, as printed. |
| `quantities` | The symbols the row can give, such as `("D_W", "D_WA")`. |
| `subclause` | The subclause of ISO 11546 that describes it. |
| `band_values` | Whether the row gives values per band, or only the A-weighted number. |
| `survey_grade_excluded` | Whether footnote 2 of Table 1 of part 1 marks the row, which excludes the survey-grade variant of that standard. Part 2 carries no such footnote. |

## PREFERRED_BAND_RANGE_HZ

*Constant* (`mapping`).

```python
PREFERRED_BAND_RANGE_HZ = {3: (50.0, 10000.0), 1: (63.0, 8000.0)}
```

## reciprocity_insulation

```python
reciprocity_insulation(
    external_levels: ArrayLike,
    internal_levels: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    band_fraction: int = 3,
) -> EnclosureInsulationResult
```

Insertion loss measured from the outside in, Equation (5) of part 1.

$D_{pr} = \overline{L_{p,\text{ext}}} - \overline{L_{p,\text{int}}}$:
the enclosure is put in a diffuse field, the field is measured around it
and again inside it, and the difference is the insulation the enclosure
would give a source within it. The method belongs to the laboratory, and it
is the one case where the enclosure is measured without any source inside
at all.

**Parameters**

| Name | Description |
| :--- | :--- |
| `external_levels` | The averaged level in the field outside, per band, in decibels. |
| `internal_levels` | The averaged level inside the enclosure standing in that field, per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The insertion loss, as an [`EnclosureInsulationResult`](/phonometry/reference/api/noise_control/enclosure-insulation/#enclosureinsulationresult) whose quantity is `"reciprocity"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, non-finite values or an unknown band fraction. |

## ROOM_ABSORPTION_ESTIMATES

*Constant* (`mapping`).

```python
ROOM_ABSORPTION_ESTIMATES = {0.05: 'Nearly empty room with smooth hard walls made of concrete, brick, plaster or tile', 0.1: 'Partly empty room; room with smooth walls', 0.15: 'Room with furniture; rectangular machinery room; rectangular industrial room', 0.2: 'Irregularly shaped room with furniture; irregularly shaped machinery room or industrial room', 0.25: 'Room with upholstered furniture; machinery or industrial room with a small amount of sound-absorbing material on ceiling or walls (e.g. partially absorptive ceiling)', 0.35: 'Room with sound-absorbing materials on both ceiling and walls', 0.5: 'Room with large amounts of sound-absorbing materials on ceiling and walls'}
```

## seal_ratio

```python
seal_ratio(leak: float) -> float
```

The reciprocal of the leak ratio.

$\psi = 1/\theta$, from NOTE 5 to definition 3.16 of ISO 11546-1 and
NOTE 3 to definition 3.14 of ISO 11957. Both print the two because a
catalogue quotes whichever reads better.

**Parameters**

| Name | Description |
| :--- | :--- |
| `leak` | The leak ratio $\theta$, dimensionless and positive. |

**Returns:** $\psi$, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive ratio. |

## sound_power_insulation

```python
sound_power_insulation(
    level_without: ArrayLike,
    level_with: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    a_weighted_without: float | None = None,
    a_weighted_with: float | None = None,
    base_standard: str = 'ISO 3744',
    condition: EnclosureCondition = 'laboratory',
    source_kind: SourceKind = 'actual',
    band_fraction: int = 3,
) -> EnclosureInsulationResult
```

Insertion loss from two sound power determinations, Equations (1) and (2).

$D_W = L_{W,\text{without}} - L_{W,\text{with}}$ band by band, and
$D_{WA}$ the same difference of the A-weighted totals. Where the
A-weighted pair is not supplied it is computed from the band spectra with
the ISO 3744 Annex E table, which is what the note to clause 6.2 prefers.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_without` | Sound power levels of the machine without the enclosure, in decibels. |
| `level_with` | The same with the enclosure in place, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `a_weighted_without` | $L_{WA}$ without the enclosure, in decibels, when it was measured rather than computed. |
| `a_weighted_with` | The same with the enclosure, in decibels. |
| `base_standard` | The standard the sound power came from, as Table 1 lists them. |
| `condition` | `"laboratory"` for part 1, `"in-situ"` for part 2. |
| `source_kind` | `"actual"`, `"reciprocity"` or `"artificial"`. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The insertion loss, as an [`EnclosureInsulationResult`](/phonometry/reference/api/noise_control/enclosure-insulation/#enclosureinsulationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, non-finite values, half an A-weighted pair, an unknown condition, source kind or band fraction, or a combination of condition and source kind Table 1 does not have. |

## sound_pressure_insulation

```python
sound_pressure_insulation(
    level_without: ArrayLike,
    level_with: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    a_weighted_without: float | None = None,
    a_weighted_with: float | None = None,
    base_standard: str = 'ISO 11201',
    condition: EnclosureCondition = 'laboratory',
    source_kind: SourceKind = 'actual',
    band_fraction: int = 3,
) -> EnclosureInsulationResult
```

Insertion loss from two sound pressure levels, Equations (3) and (4).

$D_p = L_{p,\text{without}} - L_{p,\text{with}}$ at one stated
position, with the same microphone positions in both runs, and
$D_{pA}$ the difference of the A-weighted values. The position is
part of the answer: the standard requires it in the report, because an
insertion loss at the operator's ear and one a metre from the panel are
different numbers about the same enclosure.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_without` | Sound pressure levels without the enclosure, in decibels. |
| `level_with` | The same with the enclosure, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `a_weighted_without` | $L_{pA}$ without the enclosure, in decibels, when it was measured rather than computed. |
| `a_weighted_with` | The same with the enclosure, in decibels. |
| `base_standard` | The standard the pressure levels came from. |
| `condition` | `"laboratory"` for part 1, `"in-situ"` for part 2. |
| `source_kind` | `"actual"`, `"reciprocity"` or `"artificial"`. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The insertion loss, as an [`EnclosureInsulationResult`](/phonometry/reference/api/noise_control/enclosure-insulation/#enclosureinsulationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra that do not match, non-finite values, half an A-weighted pair, an unknown condition, source kind or band fraction, or a combination of condition and source kind Table 1 does not have. |

## source_position_clearance_m

```python
source_position_clearance_m(shortest_inner_dimension_m: float) -> float
```

How far the artificial source stands from a wall, 7.3 of part 1 and 7.2 of part 2.

$0,2\,d$ with $d$ the shortest interior dimension of the
enclosure, so that the plate is never against a panel it is meant to
excite through the air. Both parts print the same sentence, and both add
that the source is used in two orientations 90 degrees apart where the
enclosure has room for them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `shortest_inner_dimension_m` | $d$, in metres. |

**Returns:** The least distance to any wall, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive dimension. |

## SOURCE_WALL_CLEARANCE_FACTOR

*Constant* (`float`).

```python
SOURCE_WALL_CLEARANCE_FACTOR = 0.2
```

## test_environment_applicability

```python
test_environment_applicability(
    *,
    base_standard: str,
    mean_absorption_coefficient: float,
    room_surface_area_m2: float,
    measurement_surface_area_m2: float,
) -> TestEnvironmentApplicability
```

Is this room good enough for that base standard? Annex C of part 2.

Annex C asks the question the other way round from the emission
standards: not what the environmental correction of this room is, but how
much room a method needs. With
$K_2 = 10 \lg (1 + 4 S / (\alpha S_V))$ held at the limit Table C.1
sets, the ratio the room must reach is

$$
\frac{S_V}{S} = \frac{4}{(10^{K_2/10} - 1)\,\alpha}
$$

which is Figure C.1 in closed form, the curve the annex asks the reader to
read off by eye. Take $\alpha$ from
[`ROOM_ABSORPTION_ESTIMATES`](/phonometry/reference/api/noise_control/enclosure-insulation/#room_absorption_estimates) when nobody measured it.

A standard that works by comparison with a reference sound source, ISO
3743-1 and ISO 3747, states no $K_2$ requirement at all; for those
the answer carries the background margin and nothing else, and
`applicable` is decided by the margin alone, which this function does
not see. It is reported as `True` there, with
`required_area_ratio` at `None`, so that the caller reads the table
rather than a number the annex does not give.

**Parameters**

| Name | Description |
| :--- | :--- |
| `base_standard` | One of the columns of Table C.1, as [`TEST_ENVIRONMENT_REQUIREMENTS`](/phonometry/reference/api/noise_control/enclosure-insulation/#test_environment_requirements) keys them. |
| `mean_absorption_coefficient` | $\alpha$ of the room, dimensionless. |
| `room_surface_area_m2` | $S_V$, the total area of the room's boundary surfaces, in square metres. |
| `measurement_surface_area_m2` | $S$, the area of the measurement surface around the source, in square metres. |

**Returns:** The verdict, as a [`TestEnvironmentApplicability`](/phonometry/reference/api/noise_control/enclosure-insulation/#testenvironmentapplicability).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown standard, a coefficient outside `(0, 1]` or a non-positive area. |

## TEST_ENVIRONMENT_REQUIREMENTS

*Constant* (`mapping`).

```python
TEST_ENVIRONMENT_REQUIREMENTS = {'ISO 3743-1': (None, 6.0), 'ISO 3744': (2.0, 6.0), 'ISO 3746': (7.0, 3.0), 'ISO 3747': (None, 3.0), 'ISO 9614-1': (None, None), 'ISO 9614-2': (None, None), 'ISO 11201': (2.0, 6.0), 'ISO 11202': (7.0, 3.0), 'ISO 11204': (7.0, 6.0)}
```

## TestEnvironmentApplicability

```python
TestEnvironmentApplicability(
    base_standard: str,
    environmental_correction_limit_db: float | None,
    background_margin_limit_db: float | None,
    required_area_ratio: float | None,
    actual_area_ratio: float,
    applicable: bool,
    mean_absorption_coefficient: float,
)
```

Whether a room is good enough for a base standard, Annex C of part 2.

**Attributes**

| Name | Description |
| :--- | :--- |
| `base_standard` | The standard asked about. |
| `environmental_correction_limit_db` | The largest $K_2$ Table C.1 allows it, in decibels, or `None` where the standard states none. |
| `background_margin_limit_db` | The smallest margin over the background Table C.1 asks of it, in decibels, or `None` where the table states none. |
| `required_area_ratio` | The smallest $S_V/S$ that meets the $K_2$ limit at this absorption coefficient. |
| `actual_area_ratio` | The $S_V/S$ of the room and the measurement surface given. |
| `applicable` | Whether the room meets the limit. |
| `mean_absorption_coefficient` | The $\alpha$ the answer was read at. |

## UNRESTRICTED_ENCLOSURE_VOLUME_M3

*Constant* (`float`).

```python
UNRESTRICTED_ENCLOSURE_VOLUME_M3 = 2.0
```

## weighted_insulation

```python
weighted_insulation(
    insulation: ArrayLike,
    *,
    quantity: str = 'sound_power',
    band_fraction: int = 3,
) -> WeightedEnclosureInsulation
```

The single-number rating of an insertion loss, 7.4 of part 1 and 7.3 of part 2.

Both parts say the same thing: rate the spectrum by ISO 717-1, putting
$D_W$ or $D_{pr}$ where that standard writes $R$. The
reference curve, the shift and the adaptation terms come from
[`phonometry.building.weighted_rating`](/phonometry/reference/api/building/ratings/#weighted_rating), which has its own conformance
rows; what is done here is the trim to the rating bands.

**Parameters**

| Name | Description |
| :--- | :--- |
| `insulation` | The insertion loss per band, in decibels, over exactly the 16 one-third-octave rating bands of 100 Hz to 3,15 kHz or the 5 octave ones of 125 Hz to 2 kHz; a wider spectrum is refused rather than trimmed, because which bands it holds is the caller's to say. |
| `quantity` | `"sound_power"` (default) or `"reciprocity"`. |
| `band_fraction` | 3 for one-third octaves (default), 1 for octaves. |

**Returns:** The rating, as a [`WeightedEnclosureInsulation`](/phonometry/reference/api/noise_control/enclosure-insulation/#weightedenclosureinsulation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spectrum that does not carry the rating bands. |

## WeightedEnclosureInsulation

```python
WeightedEnclosureInsulation(
    rating: int,
    c: int,
    ctr: int,
    unfavourable_sum: float,
    band_centres_hz: NDArray[np.float64],
    quantity: str,
)
```

The single-number rating of an insertion loss spectrum, ISO 717-1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | $D_{W,w}$ or $D_{pr,w}$, in decibels. |
| `c` | The spectrum adaptation term $C$, in decibels. |
| `ctr` | The spectrum adaptation term $C_{tr}$, in decibels. |
| `unfavourable_sum` | The sum of unfavourable deviations the shift left, in decibels. |
| `band_centres_hz` | The bands the rating was read over, in hertz. |
| `quantity` | What was rated, `"sound_power"` or `"reciprocity"`. |
