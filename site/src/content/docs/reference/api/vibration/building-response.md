---
title: "vibration.structural.building_response"
description: "Predicting the fundamental frequency and damping of a building (ISO 4866)."
sidebar:
  label: "building_response"
---

Predicting the fundamental frequency and damping of a building (ISO 4866).

A vibration measurement on a building is read against the building's own
response, and that response starts with one number: the lowest natural
frequency of the fundamental translation mode. Measure it when you can, says
ISO 4866; Annex D is what to do when you cannot, because the excitation is too
weak, the damping too high or the subcomponents too loud to separate.

The annex offers four empirical predictors and is candid about all of them.
The simplest is the storey count, $f = 10/n$ hertz, the same rule
DIN 4150-3 prints in its 6.4 and this library already publishes as
[`storey_fundamental_frequency`](/phonometry/reference/api/vibration/building-damage/#storey_fundamental_frequency).
The other three are the forms the period $T$ takes in national codes,
each with a coefficient the codes disagree about:

$$
T = k_1 h \qquad T = \frac{k_2 h}{\sqrt{b}} \qquad T = \frac{k_3 h}{\sqrt{b}} \sqrt{\frac{h}{h + b}}
$$

with $h$ the height and $b$ the width parallel to the force, both
in metres. The coefficients range over 0,014 to 0,03, over 0,087 to 0,109 and
over 0,06 to 0,08 respectively, so the choice of code moves the answer by more
than a factor of two in the first form alone.

Fitting one curve to measurements instead of to codes, D.3 quotes
$f = 46/h$ hertz ($T = 0{,}022\,h$ seconds) from a sample of 163
rectangular-plan buildings, and prints the fit with the data around it: errors
of **± 50 %** are not uncommon, and the annex says that is typical of what an
empirical formula can do. It also says something worth repeating, since it is
the opposite of what a reader expects: computer models correlate *worse* with
measured frequencies than $46/h$ does, because the model is only as good
as its idea of what the building is made of.

Damping (D.4) has no predictor at all. Measured values between **0,5 %** and
**2,1 %** of critical are what the annex reports for buildings where
soil-structure interaction was negligible, and the two orthogonal translation
modes of one building can differ widely. Damping is partly a function of how
the building was put together, so anticipate large errors.

Everything here is an estimate with a stated error, which is the only honest
way to use it: as the answer to "is the excitation anywhere near the
building's own frequency", not as a frequency to design against.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## BuildingFrequencyEstimate

```python
BuildingFrequencyEstimate(
    frequency_hz: float,
    period_s: float,
    model: str,
    coefficient: float | None,
    height_m: float | None,
)
```

One predicted fundamental frequency, with the error it carries.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | The predicted fundamental frequency. |
| `period_s` | The same prediction as a period. |
| `model` | Which of [`PERIOD_MODELS`](/phonometry/reference/api/vibration/building-response/#period_models) produced it. |
| `coefficient` | The code coefficient used, or `None` for the storey model, which has none. |
| `height_m` | The height it was computed from, where the model uses one. |

### BuildingFrequencyEstimate.bounds_hz

*property*

The ± 50 % band of D.3 around `frequency_hz`.

### BuildingFrequencyEstimate.plot()

```python
BuildingFrequencyEstimate.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw Figure D.1 with this estimate on it.

The `f = 46/h` line against height on logarithmic axes, the ± 50 %
band around it, and this estimate as a point.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_building_frequency`. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the estimate came from the storey model, which has no height to place a point at. |

## DAMPING_RATIO_RANGE

*Constant* (`tuple`).

```python
DAMPING_RATIO_RANGE = (0.005, 0.021)
```

## empirical_frequency_bounds

```python
empirical_frequency_bounds(frequency_hz: float) -> tuple[float, float]
```

The ± 50 % band D.3 puts around an empirical prediction, in hertz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | A predicted fundamental frequency, in hertz. |

**Returns:** `(lower, upper)`, the band the annex says is not uncommon.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the frequency is not positive and finite. |

## EMPIRICAL_FREQUENCY_TOLERANCE

*Constant* (`float`).

```python
EMPIRICAL_FREQUENCY_TOLERANCE = 0.5
```

## estimate_fundamental_frequency

```python
estimate_fundamental_frequency(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> BuildingFrequencyEstimate
```

One prediction, bundled with the coefficient and the error band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `model` | One of [`PERIOD_MODELS`](/phonometry/reference/api/vibration/building-response/#period_models). |
| `storeys` | Number of storeys `n`, for the storey model. |
| `height_m` | Height `h` above the base, in metres. |
| `width_m` | Width `b` parallel to the force, in metres. |
| `coefficient` | The code coefficient, or `None` for the midpoint. |

**Returns:** The prediction, as a [`BuildingFrequencyEstimate`](/phonometry/reference/api/vibration/building-response/#buildingfrequencyestimate).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For anything [`fundamental_period`](/phonometry/reference/api/vibration/building-response/#fundamental_period) refuses. |

## fundamental_frequency

```python
fundamental_frequency(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> float
```

The reciprocal of [`fundamental_period`](/phonometry/reference/api/vibration/building-response/#fundamental_period), in hertz.

Arguments and errors are that function's; this exists because the annex
states two of its four predictors as frequencies and two as periods, and a
reader should not have to remember which.

**Parameters**

| Name | Description |
| :--- | :--- |
| `model` | One of [`PERIOD_MODELS`](/phonometry/reference/api/vibration/building-response/#period_models). |
| `storeys` | Number of storeys `n`, for the storey model. |
| `height_m` | Height `h` above the base, in metres. |
| `width_m` | Width `b` parallel to the force, in metres. |
| `coefficient` | The code coefficient, or `None` for the midpoint. |

**Returns:** The fundamental frequency, in hertz.

## fundamental_period

```python
fundamental_period(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> float
```

The fundamental translation period of a building, in seconds (D.2).

Four predictors, and which arguments are needed depends on which:

* `"storeys"` needs *storeys*: $T = 0{,}1\,n$.
* `"height"` needs *height_m*: $T = k_1 h$.
* `"height_width"` needs both and *width_m*: $T = k_2 h/\sqrt{b}$.
* `"slenderness"` needs both:
  $T = (k_3 h/\sqrt{b})\sqrt{h/(h+b)}$.

The coefficient defaults to the midpoint of the range D.2 prints for that
form, since the annex gives a range and no way to choose inside it; state
*coefficient* to use the value of a particular code.

**Parameters**

| Name | Description |
| :--- | :--- |
| `model` | One of [`PERIOD_MODELS`](/phonometry/reference/api/vibration/building-response/#period_models). |
| `storeys` | Number of storeys `n`, for the storey model. |
| `height_m` | Height `h` above the base, in metres. |
| `width_m` | Width `b` parallel to the force, in metres. |
| `coefficient` | The code coefficient, or `None` for the midpoint of [`PERIOD_COEFFICIENT_RANGES`](/phonometry/reference/api/vibration/building-response/#period_coefficient_ranges). Not accepted by the storey model, which has no coefficient to choose. |

**Returns:** The fundamental period, in seconds.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the model is not one of the four, if an argument the model needs is missing or not positive, or if a coefficient is given for the storey model. |

## HEIGHT_FREQUENCY_CONSTANT_HZ_M

*Constant* (`float`).

```python
HEIGHT_FREQUENCY_CONSTANT_HZ_M = 46.0
```

## height_fundamental_frequency

```python
height_fundamental_frequency(height: ArrayLike) -> np.ndarray | float
```

The `f = 46/h` fit of D.3, in hertz.

Fitted to 163 rectangular-plan buildings rather than taken from a code,
which is why it is here on its own: D.3 also reports that computed
frequencies correlate with measurement *worse* than this line does.

**Parameters**

| Name | Description |
| :--- | :--- |
| `height` | Height `h` above the base, in metres (scalar or array). |

**Returns:** The predicted fundamental frequency, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a height is not positive and finite. |

## HEIGHT_PERIOD_COEFFICIENT_S_PER_M

*Constant* (`float`).

```python
HEIGHT_PERIOD_COEFFICIENT_S_PER_M = 0.022
```

## PERIOD_COEFFICIENT_RANGES

*Constant* (`dict`).

```python
PERIOD_COEFFICIENT_RANGES = {'height': (0.014, 0.03), 'height_width': (0.087, 0.109), 'slenderness': (0.06, 0.08)}
```

## PERIOD_MODELS

*Constant* (`tuple`).

```python
PERIOD_MODELS = ('storeys', 'height', 'height_width', 'slenderness')
```

## STOREY_PERIOD_COEFFICIENT_S

*Constant* (`float`).

```python
STOREY_PERIOD_COEFFICIENT_S = 0.1
```
