---
title: "vibration.immission.coupling"
description: "Mounting the transducer, and what the meter may be wrong by (DIN 45669-2:2005-06)."
sidebar:
  label: "coupling"
---

Mounting the transducer, and what the meter may be wrong by (DIN 45669-2:2005-06).

DIN 45669-2 is the procedure the DIN 45669-1 meter is used with: where the
transducers go, how they are coupled to the floor or the ground, how long a
measurement runs and what keeps a disturbance out of it. Nearly all of that
is judgement written down, and the little that is a number is here, because a
number a measurement is planned by belongs where the plan is checked.

**Loose mounting** (5.3.2 and 5.3.3). A transducer set down without fastening
walks or lifts off when the vibration is strong, and a coupling that is not
force-locked resonates against the surface. The clause fixes both limits: a
loose transducer measures without falsification up to 100 Hz vertically and
40 Hz horizontally, provided the peak acceleration in every direction stays at
or below 3 m/s². On a hard surface it may stand on its own or on the device
with rounded feet of Figure 1 b); on a soft covering it has to stand on the
device with hardened steel spikes of Figure 1 a), about 2,5 kg together with
the transducer, pressed and tapped through the covering. Above those limits
the transducer is glued, screwed or plastered on, and on a sensitive hard
surface such as tiles or parquet adhesive wax carries the horizontal
component to 80 Hz.

**Mass loading** (7.2.4). The mass coupled to the object, transducer and
device together, should be at most a hundredth of the mass the object
vibrates with; a heavier transducer is a disturbance of kind $s_3$.

**The instrument's share of the error** (8.1, Table 3). A meter that meets
every single requirement of DIN 45669-1 may still be wrong on one displayed
quantity, and Table 3 says by how much at a high confidence level: 15 % on an
r.m.s.-based value and 20 % on a peak for class 1, 25 % and 35 % for class 2.
The classes are the accuracy classes of the 1995 edition of Part 1; the 2010
edition dropped the distinction, so a meter of today is graded by the one set
of tolerances and the table's class 1 column is the one that applies to it.

**What is not here.** Measurement positions, directions, durations and the
list of disturbances are text, and so is the coupling to the ground, where
5.3.4.1 warns that the coupling alone can move the reading by up to 15 dB.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_loose_mounting

```python
check_loose_mounting(
    peak_acceleration_m_s2: float,
    upper_frequency_hz: float,
    *,
    direction: str,
    surface: str = 'hard',
) -> MountingCheck
```

May the transducer be set down without fastening? (5.3.2 and 5.3.3)

Loose mounting carries a vertical measurement to 100 Hz and a horizontal
one to 40 Hz, provided the peak acceleration in every direction stays at
or below 3 m/s². Above either limit the transducer is glued, screwed or
plastered on. The limits are the same on a hard surface and on a soft
covering; what differs is what the transducer stands on, which the result
names.

**Parameters**

| Name | Description |
| :--- | :--- |
| `peak_acceleration_m_s2` | The largest peak acceleration expected in any direction, in metres per second squared. |
| `upper_frequency_hz` | The highest frequency the measurement has to carry, in hertz. |
| `direction` | `"vertical"` or `"horizontal"`. |
| `surface` | `"hard"` (default: masonry, a raw slab, a hard floor) or `"soft"` (a carpet or any elastic floor covering). |

**Returns:** The verdict and the limits it was read against, as a [`MountingCheck`](/phonometry/reference/api/vibration/coupling/#mountingcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative acceleration, a non-positive frequency, or an unknown direction or surface. |

## CLEARANCE_TO_DISTURBING_BODY_FACTOR

*Constant* (`float`).

```python
CLEARANCE_TO_DISTURBING_BODY_FACTOR = 1.5
```

## EMISSION_POINT_TRACK_DISTANCE_M

*Constant* (`float`).

```python
EMISSION_POINT_TRACK_DISTANCE_M = 8.0
```

## GROUND_COUPLING_DEVIATION_DB

*Constant* (`float`).

```python
GROUND_COUPLING_DEVIATION_DB = 15.0
```

## instrument_confidence_limit_percent

```python
instrument_confidence_limit_percent(
    quantity: str,
    accuracy_class: int = 1,
) -> float
```

The confidence limit of the meter's own error on one quantity (Table 3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `quantity` | `"rms"` for a value based on an r.m.s., such as `KB_F` or `KB_FTm`, or `"peak"` for a peak value. |
| `accuracy_class` | 1 (default) or 2, the classes of the 1995 edition of DIN 45669-1. The 2010 edition grades every meter by one set of tolerances, so class 1 is the column that applies to a meter of today. |

**Returns:** The limit, in per cent of the displayed value.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown quantity or class. |

## INSTRUMENT_CONFIDENCE_LIMITS_PERCENT

*Constant* (`dict`).

```python
INSTRUMENT_CONFIDENCE_LIMITS_PERCENT = {'rms': (15.0, 25.0), 'peak': (20.0, 35.0)}
```

## LOOSE_MOUNTING_LIMITS_HZ

*Constant* (`dict`).

```python
LOOSE_MOUNTING_LIMITS_HZ = {'vertical': 100.0, 'horizontal': 40.0}
```

## LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2

*Constant* (`float`).

```python
LOOSE_MOUNTING_PEAK_ACCELERATION_M_S2 = 3.0
```

## mass_loading_ratio

```python
mass_loading_ratio(
    coupled_mass_kg: float,
    *,
    vibrating_mass_kg: float,
) -> float
```

The mass the transducer adds to the object, as a fraction (7.2.4).

The transducer and its coupling device together should add at most
[`MASS_LOADING_RATIO_LIMIT`](/phonometry/reference/api/vibration/coupling/#mass_loading_ratio_limit) of the mass the object vibrates with,
which for a floor is the mass of the slab that moves at the highest
frequency of the signal, not the mass of the building. Where that cannot
be estimated, 7.2.4 says to add a second, uncoupled mass of the same order
beside the transducer and see whether the reading moves.

**Parameters**

| Name | Description |
| :--- | :--- |
| `coupled_mass_kg` | The transducer and its device, in kilograms. |
| `vibrating_mass_kg` | The mass of the object that vibrates with it, in kilograms. |

**Returns:** The ratio of the two, dimensionless; compare it with [`MASS_LOADING_RATIO_LIMIT`](/phonometry/reference/api/vibration/coupling/#mass_loading_ratio_limit).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive mass. |

## MASS_LOADING_RATIO_LIMIT

*Constant* (`float`).

```python
MASS_LOADING_RATIO_LIMIT = 0.01
```

## MountingCheck

```python
MountingCheck(
    acceptable: bool,
    frequency_limit_hz: float,
    peak_acceleration_limit_m_s2: float,
    direction: str,
    surface: str,
    device: str,
)
```

Whether a transducer may be set down without fastening (5.3.2, 5.3.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `acceptable` | `True` when both the peak acceleration and the highest frequency of interest are within what a loose mounting carries. |
| `frequency_limit_hz` | The frequency the direction allows a loose mounting up to, in hertz. |
| `peak_acceleration_limit_m_s2` | The 3 m/s² of 5.3.2.1. |
| `direction` | `"vertical"` or `"horizontal"`. |
| `surface` | `"hard"` or `"soft"`. |
| `device` | What the transducer has to stand on for the verdict to hold. |

## SPIKED_DEVICE_MASS_KG

*Constant* (`float`).

```python
SPIKED_DEVICE_MASS_KG = 2.5
```

## WAX_MOUNTING_HORIZONTAL_LIMIT_HZ

*Constant* (`float`).

```python
WAX_MOUNTING_HORIZONTAL_LIMIT_HZ = 80.0
```
