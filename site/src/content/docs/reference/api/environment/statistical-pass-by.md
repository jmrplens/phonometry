---
title: "environment.sources.statistical_pass_by"
description: "What a road surface adds to the noise of the traffic on it (ISO 11819-1:1997)."
sidebar:
  label: "statistical_pass_by"
---

What a road surface adds to the noise of the traffic on it (ISO 11819-1:1997).

A road surface is not a source, but it changes how loud every tyre on it is,
and the Statistical Pass-By (SPB) method is how that change is measured. A
microphone stands 7,5 m from the centre of the lane and 1,2 m above it, and for
each vehicle that passes on its own, the maximum A-weighted level with time
weighting F and the speed are written down, together with the vehicle's
category: cars (1), dual-axle heavy vehicles (2a) or multi-axle heavy vehicles
(2b). Other vehicles are not used (clause 4).

**9.1 and 9.2, the vehicle sound level.** For each category the levels are
regressed on the logarithm of the speed by least squares,

$$
L_{\mathrm{AFmax}} = a + b \lg \frac{v}{1\ \mathrm{km/h}},
$$

and the ordinate of that line at the reference speed of Table 1 is the vehicle
sound level $L_\mathrm{veh}$ of the category ([`pass_by_regression`](/phonometry/reference/api/environment/statistical-pass-by/#pass_by_regression)).
The reference speed depends on the road speed category of 3.3 (low, medium,
high) and is the same for the two heavy categories.

**9.5, the index.** The three vehicle sound levels are added on an energy basis,
each weighted by the proportion $W_x$ of its category in a standard mix
and the heavy ones by the ratio of the car reference speed to their own:

$$
\mathrm{SPBI} = 10 \lg \left[ W_1 \, 10^{L_1/10} + W_{2a} \frac{v_1}{v_{2a}} 10^{L_{2a}/10} + W_{2b} \frac{v_1}{v_{2b}} 10^{L_{2b}/10} \right]
$$

([`statistical_pass_by_index`](/phonometry/reference/api/environment/statistical-pass-by/#statistical_pass_by_index)). The index is for comparing surfaces, not
for predicting a traffic noise level (9.5 NOTE), and the comparison clause 10
has in mind is a difference from a reference surface, of which Annex D gives an
example built from seven Swedish surfaces ([`normalized_reference_levels`](/phonometry/reference/api/environment/statistical-pass-by/#normalized_reference_levels),
[`SPB_NORMALIZED_REFERENCE_DB`](/phonometry/reference/api/environment/statistical-pass-by/#spb_normalized_reference_db)).

**The rounding chain.** 9.2 ends "All levels shall be calculated to two decimal
places and rounded to one decimal place." This module carries every level at
full precision, which is at least the two decimal places the clause asks for,
feeds the index with those unrounded vehicle sound levels, and rounds once, to
one decimal, only what is reported (the `reported_` properties, rounded half
up). The example of Annex E does something else: its index of 79,9 dB is the
index of the three vehicle sound levels *as printed* to one decimal (78,5,
81,1 and 83,8 dB give 79,946 dB). From the regression coefficients it prints,
carried without intermediate rounding, the same three levels are 78,546,
81,114 and 83,838 dB and the index is 79,985 dB, which reports as 80,0 dB. The
two readings differ by 0,04 dB, enough to move the printed digit, and
[`statistical_pass_by_index`](/phonometry/reference/api/environment/statistical-pass-by/#statistical_pass_by_index) handed the printed one-decimal levels
reproduces the example exactly, which is also what 9.5 describes when it says
the mandatory reporting of every $L_\mathrm{veh}$ lets others compute
the index for their own weighting factors.

**9.3 and 7.3, as warnings.** The regression is only used to normalize to the
reference speed if that speed lies within one standard deviation of the
measured mean speed for the heavy vehicles and one and a half for the cars. The
mean and the standard deviation are those of $\lg v$, the variable the
line is fitted in; the speed printed in Annex E is marked "converted from the
logarithm of speed", and the mean it prints is $10^{\overline{\lg v}}$.
For surface classification, 7.3 asks for at least 100 cars, 30 vehicles of each
heavy category and 80 heavy vehicles in all. Both conditions are judged, kept
on the result and, when they fail, emitted as
[`StatisticalPassByWarning`](/phonometry/reference/api/environment/statistical-pass-by/#statisticalpassbywarning) rather than raised: a before-and-after study
(6.6) is still an SPB measurement.

**9.4, temperature.** The vehicle sound levels should be corrected to an air
temperature of 20 °C, and the standard says a suitable method is under
consideration. None is implemented here: temperature-corrected levels are an
input (`corrected_vehicle_sound_levels_db`), and the index is then computed
for both, which is what clause 13 asks to be reported.

**9.6, the random errors.** Table 2 gives the spread expected of individual
vehicles about $L_\mathrm{veh}$ and the 95 % confidence interval that
spread leaves on it for 100 cars and 40 heavy vehicles of each type
([`SPB_VEHICLE_STANDARD_DEVIATIONS_DB`](/phonometry/reference/api/environment/statistical-pass-by/#spb_vehicle_standard_deviations_db), [`SPB_CONFIDENCE_INTERVALS_DB`](/phonometry/reference/api/environment/statistical-pass-by/#spb_confidence_intervals_db)).
A regression also returns the confidence interval of its own line at the
reference speed, from the Student distribution with $n - 2$ degrees of
freedom, and the result combines the three into an interval on the index with
the sensitivity of the index to each level. The standard says the index error
"will be a combination of these errors according to the chosen weighting
factors" and gives no formula; the combination here assumes the three
categories independent.

Read from BS EN ISO 11819-1:2001, which is identical to ISO 11819-1:1997 (its
national foreword).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## normalized_reference_levels

```python
normalized_reference_levels(
    surface_levels_db: Mapping[str, Mapping[str, float]],
) -> Mapping[str, float]
```

The vehicle sound levels of a normalized reference surface, 10.2 and Annex D.

The normalized reference case is a fictitious surface whose
$L_\mathrm{veh}$ are set by convention, "for instance ... the
average results of a great number of SPB measurements" on dense asphalt
surfaces. Annex D builds one from seven surfaces
([`SPB_ANNEX_D_SURFACES_DB`](/phonometry/reference/api/environment/statistical-pass-by/#spb_annex_d_surfaces_db)) and prints the average of each column,
which is what this returns: the arithmetic mean, category by category.

The energetic mean would print the same row there (76,4, 81,0 and 84,0 dB
either way), so the page does not decide between the two; the arithmetic
mean is the plain reading of "average" for levels that are already
averages.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface_levels_db` | The vehicle sound levels of each surface, in decibels, as a mapping from a surface label to a mapping keyed `"1"`, `"2a"` and `"2b"`. |

**Returns:** The mean level of each category, in decibels, unrounded.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For no surfaces, or a surface without exactly the three categories. |

## pass_by_regression

```python
pass_by_regression(
    speeds_kmh: ArrayLike,
    max_levels_db: ArrayLike,
    *,
    vehicle_category: str,
    road_speed_category: str,
) -> PassByRegression
```

Fit the level of one vehicle category against the logarithm of speed, 9.1 and 9.2.

The maximum A-weighted levels are regressed on
$\lg(v / 1\ \mathrm{km/h})$ by least squares, and the ordinate of the
line at the Table 1 reference speed is the vehicle sound level
$L_\mathrm{veh}$ of the category
([`PassByRegression.vehicle_sound_level_db`](/phonometry/reference/api/environment/statistical-pass-by/#passbyregressionvehicle_sound_level_db)).

Two conditions are judged on the way and emitted as
[`StatisticalPassByWarning`](/phonometry/reference/api/environment/statistical-pass-by/#statisticalpassbywarning) when they fail: the 7.3 minimum number of
vehicles of the category for surface classification, and the 9.3 window the
reference speed has to lie in for the line to be used at it. Both verdicts
stay on the result.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speeds_kmh` | The speed of each pass-by, in km/h, measured as the vehicle midpoint passes the microphone (8.4). |
| `max_levels_db` | The maximum A-weighted sound pressure level of each pass-by, time weighting F, in decibels, in the same order. |
| `vehicle_category` | `"1"` (cars), `"2a"` (dual-axle heavy vehicles) or `"2b"` (multi-axle heavy vehicles). |
| `road_speed_category` | `"low"`, `"medium"` or `"high"` (3.3), which picks the reference speed. |

**Returns:** The line and its statistics, as a [`PassByRegression`](/phonometry/reference/api/environment/statistical-pass-by/#passbyregression).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown category, a speed that is not positive, a level that is not finite, inputs that do not match pass-by for pass-by, fewer than three pass-bys, or pass-bys all at one speed. |

## PassByRegression

```python
PassByRegression(
    vehicle_category: str,
    road_speed_category: str,
    speeds_kmh: NDArray[np.float64],
    max_levels_db: NDArray[np.float64],
    reference_speed_kmh: float,
    intercept_db: float,
    slope_db_per_decade: float,
    correlation: float,
    level_standard_deviation_db: float,
    residual_standard_deviation_db: float,
    lg_speed_standard_deviation: float,
)
```

The regression line of one vehicle category and what 9.2 reads off it.

The line is $L = a + b \lg(v / 1\ \mathrm{km/h})$, fitted by least
squares to the pass-bys of one category (9.1). Everything clause 13 item 29
asks to be reported about it is here: the slope and the intercept, the mean
and the standard deviation of the speeds and the standard deviation of the
residuals.

**Parameters**

| Name | Description |
| :--- | :--- |
| `vehicle_category` | `"1"`, `"2a"` or `"2b"`. |
| `road_speed_category` | `"low"`, `"medium"` or `"high"`. |
| `speeds_kmh` | The measured speed of each pass-by, in km/h, read-only. |
| `max_levels_db` | The maximum A-weighted level of each pass-by, time weighting F, in decibels, read-only. |
| `reference_speed_kmh` | The Table 1 reference speed of the category, in km/h. |
| `intercept_db` | $a$, the ordinate of the line at 1 km/h, in decibels. |
| `slope_db_per_decade` | $b$, in decibels per decade of speed. |
| `correlation` | The correlation coefficient of level and $\lg v$. |
| `level_standard_deviation_db` | The standard deviation of the measured levels, in decibels. |
| `residual_standard_deviation_db` | The standard deviation of the levels about the line, $\sqrt{\sum e_i^2 / (n - 2)}$, in decibels: the spread with the speed effect removed that Table 2 describes. |
| `lg_speed_standard_deviation` | The standard deviation of $\lg(v / 1\ \mathrm{km/h})$, in decades. |

### PassByRegression.confidence_interval_db

*property*

Half-width of the 95 % confidence interval of the line at the reference speed.

$$
t_{0,975;\,n-2} \, s_e \sqrt{\frac{1}{n} + \frac{(\lg v_\mathrm{ref} - \overline{\lg v})^2}{\sum (\lg v_i - \overline{\lg v})^2}}
$$

the textbook interval of a least-squares line, in decibels. It is the
measured counterpart of the 0,3 dB and 0,7 dB Table 2 expects, and it
widens as the reference speed moves away from the mean speed.

### PassByRegression.mean_level_db

*property*

The mean of the measured levels, in decibels.

### PassByRegression.mean_speed_kmh

*property*

The mean speed $10^{\overline{\lg v}}$, in km/h.

The mean of the variable the line is fitted in, converted back, as
Annex E prints it ("value converted from the logarithm of speed"). The
line passes through it at `mean_level_db`.

### PassByRegression.meets_minimum_count

*property*

Whether the category has the vehicles 7.3 asks for classification.

### PassByRegression.plot()

```python
PassByRegression.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the pass-bys, the fitted line, the 9.3 window and $L_\mathrm{veh}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the fitted line. |

**Returns:** The axes drawn on.

### PassByRegression.reference_speed_in_window

*property*

Whether the reference speed lies inside `speed_window_kmh` (9.3).

### PassByRegression.reported_vehicle_sound_level_db

*property*

$L_\mathrm{veh}$ rounded to one decimal, as 9.2 has it reported.

### PassByRegression.speed_window_kmh

*property*

The speeds the reference speed must lie between, 9.3, in km/h.

$10^{\overline{\lg v} \pm k s}$ with $s$ the standard
deviation of $\lg v$ and $k$ 1,5 for cars and 1 for heavy
vehicles ([`SPB_SPEED_WINDOW_STANDARD_DEVIATIONS`](/phonometry/reference/api/environment/statistical-pass-by/#spb_speed_window_standard_deviations)).

### PassByRegression.vehicle_count

*property*

How many pass-bys the line was fitted through.

### PassByRegression.vehicle_sound_level_db

*property*

$L_\mathrm{veh}$, the line at the reference speed, unrounded (9.2).

## SPB_ANNEX_D_SURFACES_DB

*Constant* (`mapping`).

```python
SPB_ANNEX_D_SURFACES_DB = {'A1': {'1': 76.6, '2a': 81.1, '2b': 84.1}, 'A2': {'1': 75.9, '2a': 80.0, '2b': 83.0}, 'A3': {'1': 76.4, '2a': 81.8, '2b': 84.0}, 'A4': {'1': 77.2, '2a': 81.5, '2b': 84.9}, 'B1': {'1': 76.1, '2a': 81.0, '2b': 84.4}, 'B2': {'1': 76.4, '2a': 80.4, '2b': 83.3}, 'B3': {'1': 76.4, '2a': 81.0, '2b': 84.1}}
```

## SPB_CONFIDENCE_INTERVALS_DB

*Constant* (`mapping`).

```python
SPB_CONFIDENCE_INTERVALS_DB = {'1': 0.3, '2a': 0.7, '2b': 0.7}
```

## SPB_MINIMUM_VEHICLE_COUNTS

*Constant* (`mapping`).

```python
SPB_MINIMUM_VEHICLE_COUNTS = {'1': 100, '2a': 30, '2b': 30, '2': 80}
```

## SPB_NORMALIZED_REFERENCE_DB

*Constant* (`mapping`).

```python
SPB_NORMALIZED_REFERENCE_DB = {'1': 76.4, '2a': 81.0, '2b': 84.0}
```

## SPB_REFERENCE_AIR_TEMPERATURE_C

*Constant* (`float`).

```python
SPB_REFERENCE_AIR_TEMPERATURE_C = 20.0
```

## SPB_REFERENCE_SPEEDS_KMH

*Constant* (`mapping`).

```python
SPB_REFERENCE_SPEEDS_KMH = {'low': {'1': 50.0, '2a': 50.0, '2b': 50.0}, 'medium': {'1': 80.0, '2a': 70.0, '2b': 70.0}, 'high': {'1': 110.0, '2a': 85.0, '2b': 85.0}}
```

## SPB_ROAD_SPEED_CATEGORIES

*Constant* (`tuple`).

```python
SPB_ROAD_SPEED_CATEGORIES = ('low', 'medium', 'high')
```

## SPB_SPEED_WINDOW_STANDARD_DEVIATIONS

*Constant* (`mapping`).

```python
SPB_SPEED_WINDOW_STANDARD_DEVIATIONS = {'1': 1.5, '2a': 1.0, '2b': 1.0}
```

## SPB_VEHICLE_CATEGORIES

*Constant* (`tuple`).

```python
SPB_VEHICLE_CATEGORIES = ('1', '2a', '2b')
```

## SPB_VEHICLE_STANDARD_DEVIATIONS_DB

*Constant* (`mapping`).

```python
SPB_VEHICLE_STANDARD_DEVIATIONS_DB = {'1': 1.5, '2a': 2.0, '2b': 2.0}
```

## SPB_WEIGHTING_FACTORS

*Constant* (`mapping`).

```python
SPB_WEIGHTING_FACTORS = {'low': {'1': 0.9, '2a': 0.075, '2b': 0.025}, 'medium': {'1': 0.8, '2a': 0.1, '2b': 0.1}, 'high': {'1': 0.7, '2a': 0.075, '2b': 0.225}}
```

## statistical_pass_by

```python
statistical_pass_by(
    vehicle_categories: ArrayLike,
    speeds_kmh: ArrayLike,
    max_levels_db: ArrayLike,
    *,
    road_speed_category: str,
    corrected_vehicle_sound_levels_db: Mapping[str, float] | None = None,
    reference_db: float | Mapping[str, float] | None = None,
    weighting_factors: Mapping[str, float] | None = None,
) -> StatisticalPassByResult
```

The Statistical Pass-By method of ISO 11819-1 from a list of pass-bys.

One row per vehicle that passed on its own: its category, its speed and its
maximum A-weighted level. The rows are split by category, a line is fitted
through each ([`pass_by_regression`](/phonometry/reference/api/environment/statistical-pass-by/#pass_by_regression)), each line is read at its Table 1
reference speed, and the three vehicle sound levels are combined into the
index ([`statistical_pass_by_index`](/phonometry/reference/api/environment/statistical-pass-by/#statistical_pass_by_index)) at full precision. The rounding to
one decimal of 9.2 is left to the `reported_` properties of the result.

The 7.3 counts (the two heavy categories together included) and the 9.3
speed windows are judged, kept on the result and emitted as
[`StatisticalPassByWarning`](/phonometry/reference/api/environment/statistical-pass-by/#statisticalpassbywarning) when they fail.

**Parameters**

| Name | Description |
| :--- | :--- |
| `vehicle_categories` | The category of each pass-by, `"1"`, `"2a"` or `"2b"`. |
| `speeds_kmh` | The speed of each pass-by, in km/h. |
| `max_levels_db` | The maximum A-weighted level of each pass-by, time weighting F, in decibels. |
| `road_speed_category` | `"low"`, `"medium"` or `"high"` (3.3). |
| `corrected_vehicle_sound_levels_db` | Vehicle sound levels corrected to [`SPB_REFERENCE_AIR_TEMPERATURE_C`](/phonometry/reference/api/environment/statistical-pass-by/#spb_reference_air_temperature_c) by a method of the caller's choosing, keyed by category, for which the index is also computed. 9.4 gives no method. To correct each pass-by instead, which 9.4 prefers, correct `max_levels_db` and call this again. |
| `reference_db` | The reference surface of clause 10: either its SPBI in decibels, or its three vehicle sound levels keyed by category (for instance [`SPB_NORMALIZED_REFERENCE_DB`](/phonometry/reference/api/environment/statistical-pass-by/#spb_normalized_reference_db)), whose index is then computed with the same weighting factors. |
| `weighting_factors` | Other proportions of the three categories (9.5); Table 1 when omitted. |

**Returns:** The regressions, the levels and the index, as a [`StatisticalPassByResult`](/phonometry/reference/api/environment/statistical-pass-by/#statisticalpassbyresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a category the method does not use, rows that do not match, a category with fewer than three pass-bys or all at one speed, or invalid weighting factors or levels. |

## statistical_pass_by_index

```python
statistical_pass_by_index(
    vehicle_sound_levels_db: Mapping[str, float],
    *,
    road_speed_category: str,
    weighting_factors: Mapping[str, float] | None = None,
) -> float
```

The Statistical Pass-By Index of three vehicle sound levels, 9.5.

$$
\mathrm{SPBI} = 10 \lg \left[ W_1 \, 10^{L_1/10} + W_{2a} \frac{v_1}{v_{2a}} 10^{L_{2a}/10} + W_{2b} \frac{v_1}{v_{2b}} 10^{L_{2b}/10} \right]
$$

with the reference speeds and the weighting factors of Table 1 for the road
speed category. The heavy terms carry the ratio of the car reference speed
to their own because the index stands for the equivalent level of a flow in
which the cars pass faster than the lorries: a vehicle that goes slower is
heard for longer.

Whatever levels are handed in are used as they are. Handed the three levels
a report prints to one decimal, this is the index a third party computes
from a report, which 9.5 anticipates, and the chain the example of Annex E
uses; [`statistical_pass_by`](/phonometry/reference/api/environment/statistical-pass-by/#statistical_pass_by) feeds it the unrounded levels instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `vehicle_sound_levels_db` | $L_\mathrm{veh}$ of cars, dual-axle and multi-axle heavy vehicles, in decibels, keyed `"1"`, `"2a"` and `"2b"`. |
| `road_speed_category` | `"low"`, `"medium"` or `"high"` (3.3), which picks the reference speeds and the weighting factors of Table 1. |
| `weighting_factors` | Other proportions of the three categories, keyed the same way, for the nationally adapted calculations 9.5 allows (the report then has to state them). They must add up to 1. Table 1 when omitted. |

**Returns:** The index, in decibels, unrounded.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a road speed category the standard does not define, a level missing, unknown or not finite, or weighting factors that are negative or do not add up to 1. |

## StatisticalPassByResult

```python
StatisticalPassByResult(
    road_speed_category: str,
    regressions: Mapping[str, PassByRegression],
    weighting_factors: Mapping[str, float],
    vehicle_sound_levels_db: Mapping[str, float],
    index_db: float,
    corrected_vehicle_sound_levels_db: Mapping[str, float] | None = None,
    corrected_index_db: float | None = None,
    reference_index_db: float | None = None,
)
```

The vehicle sound levels and the index of one road surface (ISO 11819-1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `road_speed_category` | `"low"`, `"medium"` or `"high"`. |
| `regressions` | The [`PassByRegression`](/phonometry/reference/api/environment/statistical-pass-by/#passbyregression) of each vehicle category, keyed `"1"`, `"2a"` and `"2b"`. |
| `weighting_factors` | The $W_x$ the index was computed with. |
| `vehicle_sound_levels_db` | $L_\mathrm{veh}$ of each category, uncorrected for temperature and unrounded, in decibels. |
| `index_db` | The SPBI of those levels, unrounded, in decibels. |
| `corrected_vehicle_sound_levels_db` | The temperature-corrected levels the caller supplied (9.4), or `None`. |
| `corrected_index_db` | The SPBI of the corrected levels, or `None`. |
| `reference_index_db` | The SPBI of the reference surface (clause 10), or `None` when no reference was given. |

### StatisticalPassByResult.corrected_difference_db

*property*

The temperature-corrected SPBI less the reference one, or `None`.

### StatisticalPassByResult.difference_db

*property*

The SPBI less that of the reference surface, in decibels, or `None`.

Positive for a surface louder than the reference. Unrounded; 9.5 names
this difference as the usual way the index is presented.

### StatisticalPassByResult.heavy_vehicle_count

*property*

Dual-axle and multi-axle heavy vehicles together, as 7.3 counts them.

### StatisticalPassByResult.index_confidence_interval_db

*property*

Half-width of the 95 % interval the three line intervals leave on the index.

$$
\sqrt{\sum_x \left( c_x \, \Delta_x \right)^2}, \qquad c_x = \frac{\partial \mathrm{SPBI}}{\partial L_x} = \frac{W'_x \, 10^{L_x/10}}{\sum_y W'_y \, 10^{L_y/10}}
$$

with $W'_x$ the weighting factor times the speed ratio of 9.5 and
$\Delta_x$ each category's
[`PassByRegression.confidence_interval_db`](/phonometry/reference/api/environment/statistical-pass-by/#passbyregressionconfidence_interval_db). The three categories
are measured on different vehicles and are taken as independent.

### StatisticalPassByResult.meets_minimum_counts

*property*

Whether every count of 7.3 is met, the heavy vehicles together included.

### StatisticalPassByResult.plot()

```python
StatisticalPassByResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the three clouds of pass-bys, their lines and $L_\mathrm{veh}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the three fitted lines. |

**Returns:** The axes drawn on.

### StatisticalPassByResult.reference_speeds_in_window

*property*

Whether every reference speed lies inside its 9.3 window.

### StatisticalPassByResult.reference_speeds_kmh

*property*

The Table 1 reference speeds the levels are normalized to, in km/h.

### StatisticalPassByResult.reported_corrected_index_db

*property*

The temperature-corrected SPBI rounded to one decimal, or `None`.

### StatisticalPassByResult.reported_index_db

*property*

The SPBI rounded to one decimal (9.2).

### StatisticalPassByResult.reported_vehicle_sound_levels_db

*property*

$L_\mathrm{veh}$ of each category rounded to one decimal (9.2).

## StatisticalPassByWarning

A pass-by data set falls short of a condition ISO 11819-1 states.
