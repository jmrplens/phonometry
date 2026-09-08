---
title: "vibration.human.instrumentation"
description: "Type-testing a human-vibration meter against ISO 8041-1:2017."
sidebar:
  label: "instrumentation"
---

Type-testing a human-vibration meter against ISO 8041-1:2017.

A sound level meter can be given a class: IEC 61672-1 prints design goals and
tolerance limits, and [`verify_weighting_class`](/phonometry/reference/api/filters/weighting-compliance/#verify_weighting_class)
turns a measured response into a verdict against them. A human-vibration
meter is checked the same way and by the same kind of table, and this module
is that check.

**What the standard grades.** ISO 8041-1 defines the nine frequency
weightings ([`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names)) as exact transfer
functions, and then says how far a real instrument may sit from them. The
allowance is not one number: it is a band that widens away from the middle of
the working range, keyed to four transition frequencies per weighting
(Table 4) and four tolerance regions between them (Table 5). Inside the
central region the magnitude may differ by `+12 %` / `−11 %`; in the two
skirts by `+26 %` / `−21 %`; beyond the outermost pair the standard stops
constraining the response from below altogether, which is what `−100 %`
means in the printed table.

**What it does not grade.** A verdict here is about the *frequency weighting*,
which is one clause of a standard that also covers indication, linearity,
overload, temperature, humidity and electromagnetic susceptibility. Passing
this check is a necessary condition for conformity, never a certificate of
it: the rest are laboratory tests on hardware, not arithmetic.

**Tolerances are on the factor, not on the decibel.** The standard writes its
limits as percentages of the weighting factor, and this module keeps them
that way. `+26 %` is `+2,0 dB` to two decimals, but the percentage is
what the page prints and what the acceptance test in Annex B is written in.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## CENTRAL_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
CENTRAL_TOLERANCE_PERCENT = (12.0, -11.0, 6.0)
```

## INDICATION_TOLERANCE_PERCENT

*Constant* (`float`).

```python
INDICATION_TOLERANCE_PERCENT = 4.0
```

## indication_tolerance_percent

```python
indication_tolerance_percent(name: str) -> float
```

The Table 2 indication tolerance at the reference frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |

**Returns:** The permitted deviation of the indication, in per cent.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine. |

## LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT

*Constant* (`float`).

```python
LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT = 5.0
```

## LOW_FREQUENCY_WEIGHTING

*Constant* (`str`).

```python
LOW_FREQUENCY_WEIGHTING = 'Wf'
```

## phase_tolerance_degrees

```python
phase_tolerance_degrees(
    name: str,
    frequencies: ArrayLike,
) -> NDArray[np.float64]
```

The Table 5 characteristic phase-deviation band, region by region.

Footnote a of the table limits this to instruments that provide a
measurement parameter not based on r.m.s. values, which is why it is a
separate function rather than a third array beside the magnitudes: an
r.m.s.-only meter is not graded on phase at all.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | Frequencies at which the band is wanted, in hertz. |

**Returns:** The permitted deviation, in degrees, infinite in the two tails.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As for [`weighting_tolerance_percent`](/phonometry/reference/api/vibration/instrumentation/#weighting_tolerance_percent). |

## REFERENCE_ACCELERATION_M_S2

*Constant* (`dict`).

```python
REFERENCE_ACCELERATION_M_S2 = {'Wb': 1.0, 'Wc': 1.0, 'Wd': 1.0, 'We': 1.0, 'Wf': 0.1, 'Wh': 10.0, 'Wj': 1.0, 'Wk': 1.0, 'Wm': 1.0}
```

## REFERENCE_FREQUENCY_HZ

*Constant* (`dict`).

```python
REFERENCE_FREQUENCY_HZ = {'Wb': 15.915494309189533, 'Wc': 15.915494309189533, 'Wd': 15.915494309189533, 'We': 15.915494309189533, 'Wf': 0.3978873577297384, 'Wh': 79.57747154594767, 'Wj': 15.915494309189533, 'Wk': 15.915494309189533, 'Wm': 15.915494309189533}
```

## reference_indication

```python
reference_indication(name: str) -> float
```

The weighted indication a conforming meter shows at the reference.

Table 1 pairs each application with a reference frequency and a reference
r.m.s. acceleration, and the weightings are not unity there, so the
expected indication is the product of the two.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |

**Returns:** The weighted acceleration, in metres per second squared.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine. |

## SKIRT_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
SKIRT_TOLERANCE_PERCENT = (26.0, -21.0, 12.0)
```

## TAIL_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
TAIL_TOLERANCE_PERCENT = (26.0, -100.0, inf)
```

## TRANSITION_FREQUENCIES_HZ

*Constant* (`dict`).

```python
TRANSITION_FREQUENCIES_HZ = {'Wb': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wc': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wd': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'We': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wf': (0.05011872336272722, 0.12589254117941673, 0.3981071705534972, 1.0), 'Wh': (3.9810717055349722, 10.0, 794.3282347242813, 1995.2623149688789), 'Wj': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wk': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wm': (0.5011872336272722, 1.2589254117941673, 63.09573444801933, 158.48931924611142)}
```

## UNCONSTRAINED_BELOW

*Constant* (`float`).

```python
UNCONSTRAINED_BELOW = -100.0
```

## verify_weighting

```python
verify_weighting(
    name: str,
    frequencies: ArrayLike,
    measured_factors: ArrayLike,
) -> WeightingVerification
```

Check a measured weighting response against ISO 8041-1 Tables 4 and 5.

The acceptance test is the one Annex B is written in: the deviation
`(measured / design - 1) * 100` at each frequency has to sit between the
lower and upper limits of the region that frequency falls in.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | The frequencies the response was measured at, in hertz. |
| `measured_factors` | The measured weighting factors, linear and not in decibels, one per frequency. |

**Returns:** The verdict, as a [`WeightingVerification`](/phonometry/reference/api/vibration/instrumentation/#weightingverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine, if the two arrays do not have the same shape, if a frequency is not positive and finite, or if a measured factor is negative or not finite. |

## weighting_tolerance_percent

```python
weighting_tolerance_percent(
    name: str,
    frequencies: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

The Table 5 band around a weighting, region by region.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | Frequencies at which the band is wanted, in hertz. |

**Returns:** `(upper, lower)` percentages, elementwise. `lower` is [`UNCONSTRAINED_BELOW`](/phonometry/reference/api/vibration/instrumentation/#unconstrained_below) outside the two outer transition frequencies, where the standard sets no lower limit at all.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine, or a frequency is not positive and finite. |

## WeightingVerification

```python
WeightingVerification(
    weighting: str,
    frequencies_hz: NDArray[np.float64],
    measured: NDArray[np.float64],
    design: NDArray[np.float64],
    deviation_percent: NDArray[np.float64],
    within_tolerance: NDArray[np.bool_],
)
```

One measured weighting response against its ISO 8041-1 tolerances.

**Attributes**

| Name | Description |
| :--- | :--- |
| `weighting` | The weighting the response was measured for. |
| `frequencies_hz` | The frequencies it was measured at. |
| `measured` | The measured weighting factors, as supplied. |
| `design` | The design-goal factors of ISO 8041-1 Table 3 at the same frequencies. |
| `deviation_percent` | `(measured / design - 1) * 100` elementwise, which is the quantity the standard's acceptance test is written in. |
| `within_tolerance` | Whether each frequency is inside its band. |

### WeightingVerification.failing_frequencies_hz

*property*

The frequencies whose deviation falls outside the band.

### WeightingVerification.passes

*property*

Whether every measured frequency sits inside its band.

True says the frequency weighting meets ISO 8041-1, and nothing more:
the indication, linearity, overload and environmental tests of the
same standard are hardware measurements this cannot stand in for.

### WeightingVerification.plot()

```python
WeightingVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the measured response inside the tolerance band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_weighting_verification`. |

### WeightingVerification.worst_deviation_percent

*property*

The largest deviation in magnitude, signed as it was measured.
