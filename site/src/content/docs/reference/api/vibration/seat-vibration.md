---
title: "vibration.human.seat_vibration"
description: "What a seat does to the vibration under it (ISO 10326-1:2016)."
sidebar:
  label: "seat_vibration"
---

What a seat does to the vibration under it (ISO 10326-1:2016).

A driver does not sit on the floor of the machine. The seat is between them,
and whether it helps is not obvious: a suspension seat can amplify what it was
bought to attenuate, if the excitation happens to sit near its resonance. This
standard is the laboratory method that answers the question with one number.

**The SEAT factor** (10.2.2) is that number. Drive a vibration simulator with
the input spectrum the application standard prescribes, measure the
frequency-weighted r.m.s. acceleration at the seat and at the platform, and
divide:

$$
\mathrm{SEAT} = \frac{a_\mathrm{wS}}{a_\mathrm{wP}} \tag{2}
$$

Below 1 the seat is doing its job; at 1 it is a rigid plank; above 1 it is
making the ride worse. Both accelerations are the arithmetic mean of **three
consecutive runs agreeing within ± 5 %** (10.2.1), which is what
[`mean_of_test_runs`](/phonometry/reference/api/vibration/seat-vibration/#mean_of_test_runs) enforces, because a mean of runs that disagree by
more than that is not a measurement this standard recognises.

**Correcting to an intended input** (10.2.3). A simulator does not reproduce
its target spectrum exactly, so the magnitude measured on the seat is scaled
by the ratio between the input actually delivered and the input intended:

$$
a^{*}_\mathrm{wS} = \frac{a_\mathrm{wS}\, a^{*}_\mathrm{wP}}{a_\mathrm{wP}} = \mathrm{SEAT} \cdot a^{*}_\mathrm{wP} \tag{3, 4}
$$

The printed Formula (3) asterisks all four symbols and so reduces to
$a^{*}_\mathrm{wS} = a^{*}_\mathrm{wS}$; the reading above is the one
its own prose, and Formula (4) beside it, require. See `docs/ERRATA.md`.

**The damping test** (10.3) is the other half. Load the seat with an inert
mass of 75 kg ± 1 %, drive the base at the suspension's resonance frequency,
and take the ratio there:

$$
T = \frac{a_\mathrm{S}(f_\mathrm{r})}{a_\mathrm{P}(f_\mathrm{r})} \tag{5}
$$

The arithmetic is the SEAT arithmetic, and the meaning is not: SEAT is a
whole-spectrum verdict on a seat in service, and $T$ is what the seat
does at the one frequency where it does the most. Clause 11 makes them the two
acceptance values a specific application standard may set, and this standard
sets neither: it fixes the method and leaves the numbers to whoever writes for
the machine.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ACTIVE_DAMPING_TEST_MASS_KG

*Constant* (`float`).

```python
ACTIVE_DAMPING_TEST_MASS_KG = 60.0
```

## corrected_seat_acceleration

```python
corrected_seat_acceleration(
    seat_acceleration: float,
    platform_acceleration: float,
    intended_platform_acceleration: float,
) -> float
```

The seat magnitude corrected to the intended input (10.2.3).

$a^{*}_\mathrm{wS} = a_\mathrm{wS}\,a^{*}_\mathrm{wP}/a_\mathrm{wP}$,
which is Formula (4) with the SEAT factor substituted, and what the prose
of 10.2.3 asks for. The printed Formula (3) carries an asterisk on every
symbol and reduces to an identity; `docs/ERRATA.md` records it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `seat_acceleration` | The magnitude measured at the seat, $a_\mathrm{wS}$. |
| `platform_acceleration` | The input actually delivered, $a_\mathrm{wP}$. |
| `intended_platform_acceleration` | The input the test intended, $a^{*}_\mathrm{wP}$. |

**Returns:** The corrected magnitude on the seat, in the unit the accelerations were given in.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If any acceleration is not positive and finite. |

## DAMPING_TEST_MASS_KG

*Constant* (`float`).

```python
DAMPING_TEST_MASS_KG = 75.0
```

## DAMPING_TEST_MASS_TOLERANCE

*Constant* (`float`).

```python
DAMPING_TEST_MASS_TOLERANCE = 0.01
```

## mean_of_test_runs

```python
mean_of_test_runs(values: ArrayLike, *, tolerance: float = 0.05) -> float
```

The arithmetic mean of the runs of one test (10.2.1, 10.3).

The standard asks for three consecutive runs whose values lie within
± 5 % of their arithmetic mean, and records that mean. A set that does not
meet the spread is not a result to be averaged anyway, so it is refused
here rather than quietly returned.

**Parameters**

| Name | Description |
| :--- | :--- |
| `values` | The r.m.s. accelerations of the runs, in any consistent unit. Three of them, as the standard asks; a different count is accepted, since the run-in and warm-up notes in 10.2.1 leave room for discarding a reading. |
| `tolerance` | The permitted spread as a fraction of the mean; [`RUN_AGREEMENT_TOLERANCE`](/phonometry/reference/api/vibration/seat-vibration/#run_agreement_tolerance) by default. |

**Returns:** The arithmetic mean, in the unit the values were given in.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If fewer than two values are given, if any is not positive and finite, if the tolerance is not positive, or if any value lies outside the tolerance band around the mean. |

## resonance_transmissibility

```python
resonance_transmissibility(
    seat_acceleration: float,
    platform_acceleration: float,
) -> float
```

The transmissibility at resonance of Formula (5), dimensionless.

The damping test drives the base at the suspension's resonance frequency
$f_\mathrm{r}$ with the seat carrying an inert
[`DAMPING_TEST_MASS_KG`](/phonometry/reference/api/vibration/seat-vibration/#damping_test_mass_kg), and this is the ratio there. The arithmetic
matches [`seat_factor`](/phonometry/reference/api/vibration/seat-vibration/#seat_factor) and the meaning does not: this is the one
frequency the seat treats worst, not a verdict over a spectrum, and
Clause 11 makes it the acceptance value of a different test.

**Parameters**

| Name | Description |
| :--- | :--- |
| `seat_acceleration` | $a_\mathrm{S}(f_\mathrm{r})$, measured at the disc on the seat. |
| `platform_acceleration` | $a_\mathrm{P}(f_\mathrm{r})$, measured on the platform. |

**Returns:** $a_\mathrm{S}(f_\mathrm{r})/a_\mathrm{P}(f_\mathrm{r})$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If either acceleration is not positive and finite. |

## RUN_AGREEMENT_TOLERANCE

*Constant* (`float`).

```python
RUN_AGREEMENT_TOLERANCE = 0.05
```

## seat_factor

```python
seat_factor(seat_acceleration: float, platform_acceleration: float) -> float
```

The SEAT factor of Formula (2), dimensionless.

**Parameters**

| Name | Description |
| :--- | :--- |
| `seat_acceleration` | The frequency-weighted r.m.s. acceleration measured at the seat, $a_\mathrm{wS}$, in metres per second squared. |
| `platform_acceleration` | The same quantity at the platform, $a_\mathrm{wP}$. |

**Returns:** $a_\mathrm{wS}/a_\mathrm{wP}$; below 1 the seat attenuates.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If either acceleration is not positive and finite. |

## seat_transmission

```python
seat_transmission(
    seat_runs: ArrayLike,
    platform_runs: ArrayLike,
    *,
    tolerance: float = 0.05,
) -> SeatTransmissionResult
```

One simulated input vibration test, from its runs (10.2).

Each set of runs is averaged through [`mean_of_test_runs`](/phonometry/reference/api/vibration/seat-vibration/#mean_of_test_runs), so a test
whose runs do not agree within ± 5 % is refused rather than averaged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `seat_runs` | The frequency-weighted r.m.s. accelerations measured at the seat, one per run, in metres per second squared. |
| `platform_runs` | The same at the platform, one per run. |
| `tolerance` | The permitted spread of each set, as a fraction of its mean. |

**Returns:** The test, as a [`SeatTransmissionResult`](/phonometry/reference/api/vibration/seat-vibration/#seattransmissionresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For anything [`mean_of_test_runs`](/phonometry/reference/api/vibration/seat-vibration/#mean_of_test_runs) refuses, or if the two sets do not hold the same number of runs. |

## SeatTransmissionResult

```python
SeatTransmissionResult(
    seat_acceleration: float,
    platform_acceleration: float,
    seat_runs: tuple[float, ...],
    platform_runs: tuple[float, ...],
)
```

One simulated input vibration test, as the standard records it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `seat_acceleration` | The mean of the seat runs, $a_\mathrm{wS}$, in metres per second squared. |
| `platform_acceleration` | The mean of the platform runs, $a_\mathrm{wP}$. |
| `seat_runs` | The individual seat readings the mean came from. |
| `platform_runs` | The individual platform readings. |

### SeatTransmissionResult.attenuates

*property*

Whether the seat passes less vibration than it receives.

True is the whole of what it means: a SEAT factor below 1. It is not
an acceptance, because Clause 11 leaves acceptance values to the
application standard written for the machine.

### SeatTransmissionResult.corrected_acceleration()

```python
SeatTransmissionResult.corrected_acceleration(
    intended_platform_acceleration: float,
) -> float
```

The seat magnitude corrected to an intended input (10.2.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `intended_platform_acceleration` | The input the test intended, in the unit the runs were given in. |

**Returns:** The corrected magnitude on the seat.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the intended input is not positive and finite. |

### SeatTransmissionResult.plot()

```python
SeatTransmissionResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the runs, their means and the SEAT factor between them.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_seat_transmission`. |

### SeatTransmissionResult.seat_factor

*property*

The SEAT factor of Formula (2).

## TEST_RUNS

*Constant* (`int`).

```python
TEST_RUNS = 3
```

## UNITY_TRANSMISSION

*Constant* (`float`).

```python
UNITY_TRANSMISSION = 1.0
```
