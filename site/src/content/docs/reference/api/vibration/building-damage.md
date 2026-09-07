---
title: "vibration.structural.building_damage"
description: "Effects of vibration on structures (DIN 4150-3:1999-02)."
sidebar:
  label: "building_damage"
---

Effects of vibration on structures (DIN 4150-3:1999-02).

A pile driver, a passing tram or a blast puts vibration into the ground, and
the question the neighbours ask is whether the building will crack. DIN 4150-3
answers it the way an engineering practice can afford to: not with a stress
calculation, but with **guideline values** (*Anhaltswerte*) for one measured
quantity, the peak particle velocity, drawn from a large body of measurements
on real buildings. Keep under them and damage of the kind the standard defines
has not been observed; exceed them and it does not follow that damage occurs,
only that the cheap check no longer settles the question and Clauses 4.2 to
4.4 have to be done properly.

**What is measured** (5.1). At the foundation, the largest of the three
components $v_x$, $v_y$, $v_z$ of the particle velocity, as
a peak, each treated on its own; the standard calls it
$|v_i|_\mathrm{max}$ and then writes it $v_i$. In the topmost
floor plane, the larger of the two horizontal components, measured at the
outside wall, which is the building's horizontal answer to the foundation
excitation rather than a new excitation.

**Short-term vibration** (Clause 5) is vibration that does not occur often
enough for resonance to build up in the structure. Table 1 gives its
guideline values by building class, and at the foundation they depend on
frequency: a building tolerates a fast wiggle better than a slow one, so the
value rises from 1 Hz to 100 Hz. Between the printed frequencies the
guideline is read off Bild 1, which joins the corner values by straight lines
on a linear frequency axis; above 100 Hz the 100 Hz value may be used. In the
topmost floor plane one value covers all frequencies.

**Long-term vibration** (Clause 6, *Dauererschütterungen*) is the opposite
case: often enough for the structure to respond at its own frequencies. Table
3 drops to a single value per class in the topmost floor plane, roughly a
quarter of the short-term one, and prints no frequency dependence at all.

**Buried pipelines** (5.3) are judged on their own Table 2 by pipe material,
measured on the pipe, and long-term vibration halves those values (6.3).

Three sizing rules travel with the tables and are here because a reader who
has the tables needs them in the same breath:

* Ceilings and floors (5.2) are separately covered by a vertical
  $v_z \leq 20$ mm/s at the point of largest vibration, usually mid-span.
* Massive engineering structures such as reinforced-concrete abutments and
  block foundations may take twice the row 1 values of Table 1 (5.1).
* The lowest horizontal natural frequency of a building of five storeys or
  more is roughly $f_i \approx 10/n$ with $n$ the storey count
  (6.4), which is the estimate that tells you whether the topmost floor plane
  will be excited at all.

Clause 6.2 turns a measured velocity into a bending stress for a beam or a
one-way slab vibrating in one mode, which is the bridge from this guideline
check to the stress calculation of 4.2:

$$
\hat{\sigma}_\mathrm{max} = 1{,}73 \left(E_\mathrm{dyn} \, \varrho \, \frac{G_\mathrm{ges}}{G_\mathrm{balken}}\right)^{0,5} k_n \, \hat{v}_\mathrm{max} \tag{1}
$$

The guideline values are not limits in the legal sense and not an acceptance
specification. They are where experience says the question stops being worth
asking.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## assess_building_vibration

```python
assess_building_vibration(
    velocity_mm_s: float,
    *,
    building_class: BuildingClass | str,
    frequency_hz: float | None = None,
    location: MeasurementLocation | str = 'foundation',
    duration: VibrationDuration | str = 'short_term',
    massive_structure: bool = False,
) -> DamageAssessment
```

Compare one measured peak velocity with its guideline value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured peak velocity, in millimetres per second; see [`DamageAssessment`](/phonometry/reference/api/vibration/building-damage/#damageassessment) for which component it is. |
| `building_class` | One of [`BUILDING_CLASSES`](/phonometry/reference/api/vibration/building-damage/#building_classes). |
| `frequency_hz` | Frequency of the dominant component, in hertz. Required for the short-term foundation case. |
| `location` | `"foundation"` (default) or `"top_floor"`. |
| `duration` | `"short_term"` (default) or `"long_term"`. |
| `massive_structure` | See [`guideline_velocity`](/phonometry/reference/api/vibration/building-damage/#guideline_velocity). |

**Returns:** The comparison, as a [`DamageAssessment`](/phonometry/reference/api/vibration/building-damage/#damageassessment).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the velocity is not positive and finite, or for any reason [`guideline_velocity`](/phonometry/reference/api/vibration/building-damage/#guideline_velocity) raises. |

## bending_stress

```python
bending_stress(
    peak_velocity_m_s: ArrayLike,
    *,
    dynamic_modulus_pa: float,
    density_kg_m3: float,
    load_ratio: float = 1.0,
    mode_factor: float = 1.0,
) -> np.ndarray | float
```

Peak bending stress from a peak velocity, Formula (1) of 6.2.

For a beam or a one-way slab of full rectangular section, constant
stiffness and uniform mass, vibrating in one mode, the peak bending
stress follows from the peak velocity alone:

$$
\hat{\sigma}_\mathrm{max} = 1{,}73 \left(E_\mathrm{dyn} \, \varrho \, \frac{G_\mathrm{ges}}{G_\mathrm{balken}}\right)^{0,5} k_n \, \hat{v}_\mathrm{max}
$$

The system dimensions do not enter, which is the point of the formula: a
velocity measured where the amplitude is largest is enough. The mode
factor $k_n$ lies between 1 and 1,3 in the technically important
cases, so it moves the answer by less than a third.

**Parameters**

| Name | Description |
| :--- | :--- |
| `peak_velocity_m_s` | Peak velocity over the beam length, in metres per second (scalar or array). Note the unit: the guideline tables are in millimetres per second and this formula is not. |
| `dynamic_modulus_pa` | Dynamic modulus of elasticity $E_\mathrm{dyn}$, in pascals. |
| `density_kg_m3` | Material density $\varrho$, in kilograms per cubic metre. |
| `load_ratio` | The load coefficient $G_\mathrm{ges}/G_\mathrm{balken}$, the beam's own weight plus any uniformly distributed load it carries over its own weight. 1 for a beam carrying nothing else. |
| `mode_factor` | The mode coefficient $k_n$, dimensionless. |

**Returns:** The peak bending stress, in pascals; a float unless the velocity was an array.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a material property, the load ratio or the mode factor is not positive and finite, or a velocity is negative. |

## BENDING_STRESS_CONSTANT

*Constant* (`float`).

```python
BENDING_STRESS_CONSTANT = 1.73
```

## BUILDING_CLASSES

*Constant* (`tuple`).

```python
BUILDING_CLASSES = ('commercial', 'residential', 'sensitive')
```

## DamageAssessment

```python
DamageAssessment(
    velocity_mm_s: float,
    guideline_mm_s: float,
    building_class: str,
    location: str,
    duration: str,
    frequency_hz: float | None,
)
```

One measured velocity against the guideline value it is judged by.

**Attributes**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured peak velocity, in millimetres per second: the largest of the three components at the foundation, or the larger of the two horizontal components in the topmost floor plane. |
| `guideline_mm_s` | The guideline value it is compared with. |
| `building_class` | The row of Table 1 or Table 3 that was used. |
| `location` | Where the velocity was measured. |
| `duration` | Which clause the guideline came from. |
| `frequency_hz` | The frequency the guideline was read at, or `None` where the guideline does not depend on frequency. |

### DamageAssessment.plot()

```python
DamageAssessment.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw Bild 1 with this measurement on it.

The three foundation curves of Table 1 against frequency, and the
measured velocity as a point, so the margin is read rather than
computed.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_damage_assessment`. |

### DamageAssessment.ratio

*property*

The measured velocity as a fraction of the guideline value.

### DamageAssessment.within_guideline

*property*

Whether the measured velocity keeps to the guideline value.

True is the whole of what the standard promises: damage of the kind
4.5 defines has not, in the experience the tables are drawn from, been
observed. False is not the converse, and 5.1 says so: exceeding a
guideline value does not mean damage occurs, it means the question
has to be answered by 4.2 to 4.4 instead.

## FLOOR_VERTICAL_MM_S

*Constant* (`float`).

```python
FLOOR_VERTICAL_MM_S = 20.0
```

## FOUNDATION_FREQUENCIES_HZ

*Constant* (`tuple`).

```python
FOUNDATION_FREQUENCIES_HZ = (1.0, 10.0, 50.0, 100.0)
```

## foundation_guideline_curve

```python
foundation_guideline_curve(
    building_class: BuildingClass | str,
    frequency: ArrayLike | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

Bild 1 as two arrays: frequency and guideline velocity.

The corner points of Table 1 by default, which is the polyline Bild 1
draws; pass *frequency* to sample the same polyline elsewhere.

**Parameters**

| Name | Description |
| :--- | :--- |
| `building_class` | One of [`BUILDING_CLASSES`](/phonometry/reference/api/vibration/building-damage/#building_classes). |
| `frequency` | Frequencies to sample at, in hertz, or `None` for the four corners of Table 1. |

**Returns:** `(frequency_hz, guideline_mm_s)`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the class is not one of the three, or a frequency is not positive and finite. |

## guideline_velocity

```python
guideline_velocity(
    building_class: BuildingClass | str,
    frequency: ArrayLike | None = None,
    *,
    location: MeasurementLocation | str = 'foundation',
    duration: VibrationDuration | str = 'short_term',
    massive_structure: bool = False,
) -> np.ndarray | float
```

The guideline peak velocity of Table 1 or Table 3, in mm/s.

At the foundation for short-term vibration the guideline is a function of
frequency, read off Bild 1: constant below 10 Hz, then two straight
segments joining the corner values of Table 1 on a linear frequency axis,
and constant again above 100 Hz, since 5.1 allows the 100 Hz value to be
used for anything faster. Everywhere else Table 1 and Table 3 print one
number for all frequencies, and *frequency* is then not needed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `building_class` | One of [`BUILDING_CLASSES`](/phonometry/reference/api/vibration/building-damage/#building_classes). |
| `frequency` | Frequency of the dominant component, in hertz (scalar or array). Required for the short-term foundation case and ignored otherwise. |
| `location` | `"foundation"` (default) or `"top_floor"`. |
| `duration` | `"short_term"` (Table 1, default) or `"long_term"` (Table 3). |
| `massive_structure` | Raise the row 1 values by [`MASSIVE_STRUCTURE_FACTOR`](/phonometry/reference/api/vibration/building-damage/#massive_structure_factor), which is the most 5.1 allows a massive engineering structure. Only the commercial row is raised; the allowance is written for that row alone. |

**Returns:** The guideline peak velocity, in millimetres per second; a float unless *frequency* was an array.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a name is not one of its choices, if the short-term foundation case is asked for without a frequency, if a frequency is not positive and finite, or if *massive_structure* is asked for outside the commercial row. |

## LONG_TERM_TOP_FLOOR_MM_S

*Constant* (`dict`).

```python
LONG_TERM_TOP_FLOOR_MM_S = {'commercial': 10.0, 'residential': 5.0, 'sensitive': 2.5}
```

## MASSIVE_STRUCTURE_FACTOR

*Constant* (`float`).

```python
MASSIVE_STRUCTURE_FACTOR = 2.0
```

## pipeline_guideline_velocity

```python
pipeline_guideline_velocity(
    material: PipelineMaterial | str,
    *,
    duration: VibrationDuration | str = 'short_term',
) -> float
```

The guideline peak velocity on a buried pipeline (Table 2), in mm/s.

Measured on the pipe itself; a substitute measurement at the ground
surface above it only estimates the value (5.3, D.1). Long-term vibration
halves the table, which is what 6.3 allows without further evidence.

**Parameters**

| Name | Description |
| :--- | :--- |
| `material` | One of [`PIPELINE_MATERIALS`](/phonometry/reference/api/vibration/building-damage/#pipeline_materials). |
| `duration` | `"short_term"` (default) or `"long_term"`. |

**Returns:** The guideline peak velocity, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a name is not one of its choices. |

## PIPELINE_LONG_TERM_FACTOR

*Constant* (`float`).

```python
PIPELINE_LONG_TERM_FACTOR = 0.5
```

## PIPELINE_MATERIALS

*Constant* (`tuple`).

```python
PIPELINE_MATERIALS = ('welded_steel', 'concrete_or_flanged_metal', 'masonry_or_plastic')
```

## PIPELINE_MM_S

*Constant* (`dict`).

```python
PIPELINE_MM_S = {'welded_steel': 100.0, 'concrete_or_flanged_metal': 80.0, 'masonry_or_plastic': 50.0}
```

## SHORT_TERM_FOUNDATION_MM_S

*Constant* (`dict`).

```python
SHORT_TERM_FOUNDATION_MM_S = {'commercial': (20.0, 20.0, 40.0, 50.0), 'residential': (5.0, 5.0, 15.0, 20.0), 'sensitive': (3.0, 3.0, 8.0, 10.0)}
```

## SHORT_TERM_TOP_FLOOR_MM_S

*Constant* (`dict`).

```python
SHORT_TERM_TOP_FLOOR_MM_S = {'commercial': 40.0, 'residential': 15.0, 'sensitive': 8.0}
```

## STOREY_FREQUENCY_MIN_STOREYS

*Constant* (`int`).

```python
STOREY_FREQUENCY_MIN_STOREYS = 5
```

## STOREY_FREQUENCY_NUMERATOR_HZ

*Constant* (`float`).

```python
STOREY_FREQUENCY_NUMERATOR_HZ = 10.0
```

## storey_fundamental_frequency

```python
storey_fundamental_frequency(storeys: int) -> float
```

The rough lowest horizontal natural frequency of a building (6.4).

`f_i ~ 10 / n`, offered for buildings from about five storeys up. It is
a rough estimate and the standard says so; its use is to tell whether the
excitation is anywhere near the frequency at which the topmost floor
plane will answer.

**Parameters**

| Name | Description |
| :--- | :--- |
| `storeys` | The number of storeys `n`. |

**Returns:** The estimated lowest horizontal natural frequency, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the storey count is not a positive integer. |
