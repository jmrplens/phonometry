---
title: "metrology.comparison_calibration"
description: "Calibration of a measurement microphone by comparison with a reference microphone (IEC 61094-5:2016, pressure; IEC 61094-8:2012, free field)."
sidebar:
  label: "comparison_calibration"
---

Calibration of a measurement microphone by comparison with a reference
microphone (IEC 61094-5:2016, pressure; IEC 61094-8:2012, free field).

A working standard microphone is not calibrated by reciprocity. It is put
beside, or in place of, a reference microphone whose sensitivity is already
known, both are exposed to the same sound pressure, and the ratio of their
open-circuit output voltages carries the reference's sensitivity over to it.
IEC 61094-5 does this in a pressure field, in a coupler or a jig; IEC 61094-8
does it in a free field, in an anechoic room or behind a time window. Annex D
of the first part writes the model once for both:

$$
M_\mathrm{test} = M_\mathrm{ref}\,\frac{R_V}{R_P}
$$

where $R_V$ is the ratio of the output voltages of the test and
reference microphones and $R_P$ that of the effective sound pressures
acting on them, reduced to unity by the procedure and the corrections. In
sensitivity levels, the form every function here computes,

$$
L_\mathrm{test} = L_\mathrm{ref} + 20\lg R_V - 20\lg R_P + \sum_j C_j
$$

with $C_j$ the corrections the part asks for.

**Simultaneous excitation** (IEC 61094-5 5.1.2 and Annex C, IEC 61094-8 5.3).
Both microphones sit in the field at once, each on its own measuring channel.
The level reading difference between the channels, reference on channel 1, is
Formula (C.1); after the microphones are interchanged it is Formula (C.2); and
their difference cancels the gains of the two channels and the asymmetry of
the field, Formula (C.3):

$$
L_\mathrm{ref} - L_\mathrm{test} = \tfrac12\left(L_\mathrm{C12} - L_\mathrm{C21}\right)
$$

IEC 61094-5 requires the interchange in a coupler or a jig ("shall be used",
5.1.2); [`simultaneous_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneous_comparison) refuses a pressure calibration without
it. IEC 61094-8 does not, and without it the channel difference is taken as
read.

**Sequential excitation** (IEC 61094-5 5.1.3 and Annex B, IEC 61094-8 5.2 and
Annex A). The microphones take the same place in turn. Either the exchange
does not change the sound pressure significantly, or any change is detected
and corrected, for example with a monitor microphone near the source: the
ratio of each microphone's output to the monitor's, and the quotient of the
two ratios, is the output ratio corrected for the drift (IEC 61094-8 A.2).
[`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison) computes it, with the monitor or without.

**Corrections.** IEC 61094-8 7.6 always corrects the reference's sensitivity
to the environmental conditions of the test. IEC 61094-5 6.6 does so when the
two microphones are different models; for two of the same model it allows the
result to be referred instead to the conditions at which the reference's
calibration is valid. Both parts allow the result to be referred to the
reference conditions of clause 4 (23,0 °C, 101,325 kPa, 50 %) when reliable
correction data are available.
[`environmental_sensitivity_correction`](/phonometry/reference/api/metrology/comparison-calibration/#environmental_sensitivity_correction) writes that correction to first
order from the coefficients of the microphone, in the units IEC 61094-2
Annex D gives them. [`jig_diameter_correction`](/phonometry/reference/api/metrology/comparison-calibration/#jig_diameter_correction) returns the corrections of
IEC 61094-5 Table A.1 for a type WS3 microphone calibrated against an LS2aP in
the jig of Figure A.4. A free-field calibration against a reference calibrated
in a pressure field takes the reference's free-field to pressure sensitivity
level difference of IEC/TS 61094-7 (IEC 61094-8 Table 1 and 8.2).

**Uncertainty.** [`comparison_uncertainty_budget`](/phonometry/reference/api/metrology/comparison-calibration/#comparison_uncertainty_budget) combines, on
[`combine_uncertainty`](/phonometry/reference/api/metrology/uncertainty/#combine_uncertainty), the components of IEC
61094-5 Table D.1 or IEC 61094-8 Table 2, each with a sensitivity of 1 in the
level model above, and multiplies the combined standard uncertainty by the
coverage factor $k = 2$ both parts report with (IEC 61094-5 7.9 and D.2,
IEC 61094-8 8.8). The expanded uncertainty is then passed to the calibration,
which draws it as a band.

**The effective free-field region** (IEC 61094-8 B.1).
[`free_field_region`](/phonometry/reference/api/metrology/comparison-calibration/#free_field_region) gives the prolate spheroid inside which a time
window of length $\tau$ simulates a free field, with the source and the
microphone at its foci and the major diameter

$$
A = d + \tau c
$$

at the speed of sound $c$ of IEC 61094-2 Annex F for the conditions of
the test ([`air`](/phonometry/reference/api/fluids/air/)).

Two printed values the library does not follow
----------------------------------------------

**IEC 61094-5 D.3.** The root-sum-square of the eight components Table D.1
prints is 0,0437 dB, not the 0,040 dB D.3 states; with $k = 2$ it is
0,087 dB rather than 0,08 dB. [`comparison_uncertainty_budget`](/phonometry/reference/api/metrology/comparison-calibration/#comparison_uncertainty_budget) gives the
sum of the printed components, and the defect is in `docs/ERRATA.md`.

**IEC 61094-8 B.10.** The spectrum of Formula (B.10) is that of a rectangular
pulse of duration $2b$, although the text calls $b$ the duration;
the library does not implement the direct impulse method of B.6, which the
standard itself calls largely superseded, and the defect is in
`docs/ERRATA.md`.

The IEC 61183 diffuse-field comparison of clause 5
([`diffuse_field_sensitivity`](/phonometry/reference/api/metrology/random-incidence/#diffuse_field_sensitivity)) is the same
sequential comparison without a monitor, and computes its level difference and
its sensitivity level through this module.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## comparison_uncertainty_budget

```python
comparison_uncertainty_budget(
    standard_uncertainties_db: Mapping[str, float | Quantity],
    *,
    frequency_hz: float,
    field: str = 'pressure',
    additional_components: Sequence[Quantity] = (),
    coverage_factor: float = 2.0,
) -> ComparisonUncertaintyBudget
```

The uncertainty budget of a comparison calibration at one frequency
(IEC 61094-5:2016 Annex D; IEC 61094-8:2012 8.8 and Table 2).

Each component is given as a standard uncertainty in dB, the column
Table D.1 prints, or as a [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) whose
standard uncertainty it takes: `metrology.rectangular(0, 0.03)` for a
semi-range of 0,03 dB, say. They are keyed by the names of
[`IEC61094_5_TABLE_D1`](/phonometry/reference/api/metrology/comparison-calibration/#iec61094_5_table_d1) for a pressure calibration and of
[`IEC61094_8_TABLE_2`](/phonometry/reference/api/metrology/comparison-calibration/#iec61094_8_table_2) for a free-field one; neither table is
exhaustive (D.1, 8.1), so a component may be left out and
`additional_components` adds the ones a set-up needs, such as the
diameter correction of a WS3 microphone in the jig (Table D.1, special
cases). The combination is [`combine_uncertainty`](/phonometry/reference/api/metrology/uncertainty/#combine_uncertainty)
on the level model, every component with a sensitivity of 1, which is the
root-sum-square of D.3; the expanded uncertainty is $k = 2$ times
it, the coverage factor 7.9 and D.2 of the first part and 8.8 of the
second report with.

With the eight components of Table D.1 at 2 kHz the combined standard
uncertainty is 0,0437 dB and the expanded one 0,087 dB. D.3 prints
0,040 dB and 0,08 dB, which are not the root-sum-square of its own
components (an erratum; see `docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `standard_uncertainties_db` | The components, keyed by name, each a standard uncertainty in dB or a [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity). |
| `frequency_hz` | The frequency the budget is for, in Hz. |
| `field` | `"pressure"` (Table D.1, default) or `"free_field"` (Table 2). |
| `additional_components` | Further components, as named [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) objects (Default: none). |
| `coverage_factor` | $k$ (Default: 2). |

**Returns:** The [`ComparisonUncertaintyBudget`](/phonometry/reference/api/metrology/comparison-calibration/#comparisonuncertaintybudget).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a key that is not a component of the field's table, an additional component without a name or with the name of another component, no component at all, or a value that is negative or not finite. |

## ComparisonCalibration

```python
ComparisonCalibration(
    frequencies_hz: NDArray[np.float64],
    reference_sensitivity_level_db: NDArray[np.float64],
    output_level_differences_db: NDArray[np.float64],
    pressure_level_difference_db: NDArray[np.float64],
    corrections_db: Mapping[str, NDArray[np.float64]],
    field: str,
    excitation: str,
    expanded_uncertainty_db: NDArray[np.float64] | None = None,
)
```

The sensitivity level of a microphone calibrated by comparison
(IEC 61094-5:2016 D.2 for a pressure field, IEC 61094-8:2012 for a free
field).

$$
L_\mathrm{test} = L_\mathrm{ref} + 20\lg R_V - 20\lg R_P + \sum_j C_j
$$

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `reference_sensitivity_level_db` | $L_\mathrm{ref}$, the reference microphone's sensitivity level as calibrated, in dB re 1 V/Pa. |
| `output_level_differences_db` | $20\lg R_V$ of each determination, one row per determination, in dB: the output of the test microphone re that of the reference. |
| `pressure_level_difference_db` | $20\lg R_P$, the effective sound pressure on the test microphone re that on the reference, in dB. |
| `corrections_db` | The corrections $C_j$ added to the level, by name, each in dB at every frequency. |
| `field` | `"pressure"` (IEC 61094-5) or `"free_field"` (IEC 61094-8). |
| `excitation` | `"simultaneous"` or `"sequential"`. |
| `expanded_uncertainty_db` | The expanded uncertainty ($k = 2$) of the sensitivity level at each frequency, in dB, or `None`. |

### ComparisonCalibration.correction_db

*property*

$\sum_j C_j$, in dB (0 without corrections).

### ComparisonCalibration.determinations

*property*

The number of determinations averaged.

### ComparisonCalibration.output_level_difference_db

*property*

$20\lg R_V$, the mean over the determinations, in dB.

### ComparisonCalibration.plot()

```python
ComparisonCalibration.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $L_\mathrm{test}$ and the reference's level against
frequency, with the expanded uncertainty as a band when it is known.

The reference's level is $L_\mathrm{ref}$, or, in a free field
against a pressure-calibrated reference, $L_\mathrm{ref}$ plus
its free-field difference: the level the test microphone was
compared with.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the $L_\mathrm{test}$ curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### ComparisonCalibration.sensitivity_level_db

*property*

$L_\mathrm{test}$, in dB re 1 V/Pa.

### ComparisonCalibration.sensitivity_mv_per_pa

*property*

$M_\mathrm{test} = 10^{L_\mathrm{test}/20}$ V/Pa, in mV/Pa.

### ComparisonCalibration.standard

*property*

The designation the calibration follows.

## ComparisonUncertaintyBudget

```python
ComparisonUncertaintyBudget(
    frequency_hz: float,
    field: str,
    names: tuple[str, ...],
    components: tuple[str, ...],
    standard_uncertainties_db: NDArray[np.float64],
    uncertainty: UncertaintyResult,
    coverage_factor: float = 2.0,
)
```

The uncertainty budget of a comparison calibration at one frequency
(IEC 61094-5:2016 Annex D, IEC 61094-8:2012 8.8).

Every component is a standard uncertainty in dB and enters the level model
with a sensitivity of 1, so the combined standard uncertainty is their
root-sum-square (D.3), and the expanded uncertainty is $k = 2$
times it (7.9 of the first part, 8.8 of the second).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | The frequency, in Hz. |
| `field` | `"pressure"` (Table D.1) or `"free_field"` (Table 2). |
| `names` | The key of each component, then the names of any additional ones. |
| `components` | The component as the table prints it, or the name of an additional one. |
| `standard_uncertainties_db` | $u_i$, in dB. |
| `uncertainty` | The [`UncertaintyResult`](/phonometry/reference/api/metrology/uncertainty/#uncertaintyresult) of the combination, which has to be the combination of `standard_uncertainties_db`. |
| `coverage_factor` | $k$, 2 by both parts. |

### ComparisonUncertaintyBudget.combined_uncertainty_db

*property*

$u_\mathrm{c}$, the combined standard uncertainty, in dB.

### ComparisonUncertaintyBudget.expanded_uncertainty_db

*property*

$U = k\,u_\mathrm{c}$, in dB.

### ComparisonUncertaintyBudget.linear_combined_uncertainty_db

*property*

$u_\mathrm{c}$ combined in linear form, in dB.

Each component converted to a relative uncertainty,
$r_i = 10^{u_i/20} - 1$, combined in quadrature and converted
back, $20\lg(1 + r_\mathrm{c})$: the "strict calculation" D.3
mentions and 8.8 prefers. For components of a few hundredths of a
decibel it differs from `combined_uncertainty_db` in the fourth
decimal at most, which is why both parts accept the logarithmic form.

### ComparisonUncertaintyBudget.plot()

```python
ComparisonUncertaintyBudget.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the standard uncertainty of each component, with
$u_\mathrm{c}$, $k$ and $U$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `barh`. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### ComparisonUncertaintyBudget.standard

*property*

The designation whose table the budget follows.

## ComparisonUncertaintyRow

```python
ComparisonUncertaintyRow(
    component: str,
    subclauses: tuple[str, ...] = (),
    stated_db: float | None = None,
    divisor: float | None = None,
    standard_uncertainty_db: float | None = None,
)
```

One row of the uncertainty table of IEC 61094-5 (Table D.1) or
IEC 61094-8 (Table 2).

Table D.1 is a worked example at 2 kHz: seven of its eight rows state a
value, the distribution it is read with and the standard uncertainty that
follows; the repeatability row prints its standard uncertainty alone.
Table 2 lists the typical components with the subclause that discusses
each and prints no value.

**Attributes**

| Name | Description |
| :--- | :--- |
| `component` | The component as the table prints it. |
| `subclauses` | The subclauses the table refers the component to (Table 2); empty for Table D.1, which prints none. |
| `stated_db` | The value the row's text states, in dB: a semi-range or an expanded uncertainty with $k = 2$, as `divisor` says; `None` for the repeatability of Table D.1, whose text states none, and for Table 2. |
| `divisor` | What turns `stated_db` into a standard uncertainty: $\sqrt{3}$ for the semi-range of a rectangular distribution, 2 for an expanded uncertainty with $k = 2$; `None` where `stated_db` is. |
| `standard_uncertainty_db` | The standard uncertainty the table prints, in dB; `None` for Table 2. |

## environmental_sensitivity_correction

```python
environmental_sensitivity_correction(
    frequencies_hz: ArrayLike,
    *,
    static_pressure_kpa: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_coefficient_db_per_kpa: ArrayLike,
    temperature_coefficient_db_per_k: ArrayLike,
    humidity_coefficient_db_per_percent: ArrayLike = 0.0,
    reference_static_pressure_kpa: float = 101.325,
    reference_temperature_c: float = 23.0,
    reference_relative_humidity_percent: float = 50.0,
) -> EnvironmentalSensitivityCorrection
```

The correction of a sensitivity level from one set of environmental
conditions to another (IEC 61094-5 6.6, IEC 61094-8 7.6).

IEC 61094-8 7.6 asks for the reference microphone's sensitivity to be
corrected to the conditions of the test in every case. IEC 61094-5 6.6
asks for it when the two microphones are different models, and for two of
the same model allows the result to be referred instead to the conditions
at which the reference's calibration is valid. Both allow the result to be
referred to the reference conditions of clause 4 when reliable correction
data are available; neither prints a formula. This is the first-order
one, a coefficient times a deviation for each of the three conditions,

$$
C_\mathrm{env} = \delta_p\,(p_s - p_{s,0}) + \delta_t\,(t - t_0) + \delta_H\,(H - H_0)
$$

with the coefficients in the units IEC 61094-2:2009 Annex D gives them:
dB/kPa for the static pressure, dB/K for the temperature. Annex D of that
part puts the low-frequency static pressure coefficient of LS1P
microphones between -0,01 dB/kPa and -0,02 dB/kPa and of LS2P between
-0,003 dB/kPa and -0,008 dB/kPa, the temperature coefficient within
±0,005 dB/K, and all three vary with frequency and from one microphone to
another, so they are the microphone's own and are required here. 6.5.3 of
the same part observes no influence of humidity on a laboratory standard
microphone, hence the default of 0 for its coefficient.

The reference conditions default to clause 4 of IEC 61094-5 and IEC
61094-8, 101,325 kPa, 23,0 °C and 50 %. The correction adds to a level
known at the reference conditions to give it at the conditions of the
test; [`simultaneous_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneous_comparison) and [`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison)
add it to the reference microphone's level (`reference_environment=`)
or subtract it from the result (`test_environment=`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `static_pressure_kpa` | $p_s$, the static pressure the level is wanted at, in kPa. |
| `temperature_c` | $t$, in °C. |
| `relative_humidity_percent` | $H$, in %. |
| `static_pressure_coefficient_db_per_kpa` | $\delta_p$, in dB/kPa, one value or one per frequency. |
| `temperature_coefficient_db_per_k` | $\delta_t$, in dB/K. |
| `humidity_coefficient_db_per_percent` | $\delta_H$, in dB per percentage point (Default: 0). |
| `reference_static_pressure_kpa` | $p_{s,0}$, where the level is known, in kPa (Default: 101,325). |
| `reference_temperature_c` | $t_0$, in °C (Default: 23,0). |
| `reference_relative_humidity_percent` | $H_0$, in % (Default: 50). |

**Returns:** The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, a pressure that is not positive, a temperature that is not finite or not above absolute zero, a relative humidity outside 0 % to 100 %, a coefficient that is not finite, or a coefficient column that is not one value per frequency. |

## EnvironmentalSensitivityCorrection

```python
EnvironmentalSensitivityCorrection(
    frequencies_hz: NDArray[np.float64],
    static_pressure_kpa: float,
    temperature_c: float,
    relative_humidity_percent: float,
    reference_static_pressure_kpa: float,
    reference_temperature_c: float,
    reference_relative_humidity_percent: float,
    static_pressure_coefficient_db_per_kpa: NDArray[np.float64],
    temperature_coefficient_db_per_k: NDArray[np.float64],
    humidity_coefficient_db_per_percent: NDArray[np.float64],
)
```

The change of a microphone's sensitivity level between two sets of
environmental conditions, to first order in each.

$$
C_\mathrm{env} = \delta_p\,(p_s - p_{s,0}) + \delta_t\,(t - t_0) + \delta_H\,(H - H_0)
$$

with the static pressure coefficient $\delta_p$ in dB/kPa, the
temperature coefficient $\delta_t$ in dB/K and the humidity
coefficient $\delta_H$ in dB per percentage point, each one value
or one per frequency. Added to a sensitivity level valid at
$(p_{s,0}, t_0, H_0)$, it gives the level at $(p_s, t, H)$.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `static_pressure_kpa` | $p_s$, where the level is wanted, in kPa. |
| `temperature_c` | $t$, in °C. |
| `relative_humidity_percent` | $H$, in %. |
| `reference_static_pressure_kpa` | $p_{s,0}$, where the level is known, in kPa. |
| `reference_temperature_c` | $t_0$, in °C. |
| `reference_relative_humidity_percent` | $H_0$, in %. |
| `static_pressure_coefficient_db_per_kpa` | $\delta_p$ at each frequency, in dB/kPa. |
| `temperature_coefficient_db_per_k` | $\delta_t$, in dB/K. |
| `humidity_coefficient_db_per_percent` | $\delta_H$, in dB/%. |

### EnvironmentalSensitivityCorrection.correction_db

*property*

$C_\mathrm{env}$, the sum of the three terms, in dB.

### EnvironmentalSensitivityCorrection.humidity_term_db

*property*

$\delta_H\,(H - H_0)$, in dB.

### EnvironmentalSensitivityCorrection.plot()

```python
EnvironmentalSensitivityCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $C_\mathrm{env}$ and its three terms against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the $C_\mathrm{env}$ curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### EnvironmentalSensitivityCorrection.static_pressure_term_db

*property*

$\delta_p\,(p_s - p_{s,0})$, in dB.

### EnvironmentalSensitivityCorrection.temperature_term_db

*property*

$\delta_t\,(t - t_0)$, in dB.

## free_field_region

```python
free_field_region(
    source_distance_m: float,
    window_time_s: float,
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    relative_humidity_percent: float = 50.0,
) -> FreeFieldRegion
```

The effective free-field region of a time window (IEC 61094-8:2012
B.1).

Formula (B.1), $A = d + \tau c$, with $c$ "the speed of sound
at the prevailing environmental conditions", which is taken from the
IEC 61094-2:2009 Annex F air of [`air`](/phonometry/reference/api/fluids/air/). The
conditions default to the reference conditions of clause 4, 23,0 °C,
101,325 kPa and 50 %.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d$, the separation of the acoustic centres of the source and the microphone, in m. |
| `window_time_s` | $\tau$, from the arrival of the sound at the microphone to the end of the time window, in s. |
| `temperature_c` | The air temperature, in °C (Default: 23,0). |
| `static_pressure_kpa` | The static pressure, in kPa (Default: 101,325). |
| `relative_humidity_percent` | The relative humidity, in % (Default: 50). |

**Returns:** The [`FreeFieldRegion`](/phonometry/reference/api/metrology/comparison-calibration/#freefieldregion).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a separation or window that is not positive, or conditions Annex F refuses. |

## FreeFieldRegion

```python
FreeFieldRegion(
    source_distance_m: float,
    window_time_s: float,
    speed_of_sound: float,
)
```

The effective free-field region of a time-selective calibration
(IEC 61094-8:2012 B.1, Formula (B.1) and Figure B.1).

A prolate spheroid generated by an ellipse with the acoustic centres of
the source and of the microphone at its foci, $d$ apart, and the
major diameter $A = d + \tau c$. A reflection from any point on its
surface arrives $\tau$ after the direct sound, at the end of the
window; the device measured is inside, and any reflecting surface or
obstacle has to be outside.

**Attributes**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d$, the source to receiver separation, in m. |
| `window_time_s` | $\tau$, from the arrival of the sound at the microphone to the end of the window, in s. |
| `speed_of_sound` | $c$ at the conditions of the test, in m/s. |

### FreeFieldRegion.major_axis_m

*property*

$A = d + \tau c$, Formula (B.1), in m.

### FreeFieldRegion.plot()

```python
FreeFieldRegion.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the region in a plane through the axis, as Figure B.1 draws it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the boundary of the region. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### FreeFieldRegion.rod_clearance_m

*property*

$(A - d)/2 = \tau c/2$, how far the region reaches behind the
microphone along the axis, in m: the mounting rod "should be
sufficiently long so that the end opposite to the microphone is
completely outside" it (B.1).

### FreeFieldRegion.semi_minor_axis_m

*property*

$b = \sqrt{(A/2)^2 - (d/2)^2}$, the radius of the region at
mid-way between the source and the microphone, in m: the clearance a
surface parallel to the axis needs to be outside it.

## IEC61094_5_TABLE_A1

*Constant* (`mapping`).

```python
IEC61094_5_TABLE_A1 = {1000.0: -0.004, 1250.0: -0.006, 1600.0: -0.009, 2000.0: -0.015, 2500.0: -0.023, 3150.0: -0.036, 4000.0: -0.059, 5000.0: -0.092, 6300.0: -0.146, 8000.0: -0.235, 10000.0: -0.367, 12500.0: -0.572, 16000.0: -0.933, 20000.0: -1.443}
```

## IEC61094_5_TABLE_D1

*Constant* (`mapping`).

```python
IEC61094_5_TABLE_D1 = {'reference': ComparisonUncertaintyRow(component='Sensitivity of reference microphone', subclauses=(), stated_db=0.05, divisor=2.0, standard_uncertainty_db=0.025), 'capacitance': ComparisonUncertaintyRow(component='Microphone capacitance', subclauses=(), stated_db=0.01, divisor=1.7320508075688772, standard_uncertainty_db=0.006), 'non_linearity': ComparisonUncertaintyRow(component='Non-linearity', subclauses=(), stated_db=0.03, divisor=1.7320508075688772, standard_uncertainty_db=0.017), 'impedance': ComparisonUncertaintyRow(component='Microphone impedance', subclauses=(), stated_db=0.005, divisor=1.7320508075688772, standard_uncertainty_db=0.003), 'polarizing_voltage': ComparisonUncertaintyRow(component='Polarising voltage', subclauses=(), stated_db=0.008681549586371858, divisor=1.7320508075688772, standard_uncertainty_db=0.005), 'repeatability': ComparisonUncertaintyRow(component='Repeatability', subclauses=(), stated_db=None, divisor=None, standard_uncertainty_db=0.025), 'drift': ComparisonUncertaintyRow(component='Drift in reference microphone sensitivity since last calibration', subclauses=(), stated_db=0.03, divisor=1.7320508075688772, standard_uncertainty_db=0.017), 'rounding': ComparisonUncertaintyRow(component='Rounding of reported results', subclauses=(), stated_db=0.005, divisor=1.7320508075688772, standard_uncertainty_db=0.003)}
```

## IEC61094_8_TABLE_1

*Constant* (`mapping`).

```python
IEC61094_8_TABLE_1 = {'primary_free_field': ReferenceCalibrationRow(microphone_types='LS', method='Primary free-field calibration', references=('IEC 61094-3',), expanded_uncertainty_1khz_db=0.25, expanded_uncertainty_10khz_db=0.1), 'primary_pressure': ReferenceCalibrationRow(microphone_types='LS', method='Primary pressure calibration with the addition of a free-field to pressure sensitivity level difference', references=('IEC 61094-2', 'IEC/TS 61094-7'), expanded_uncertainty_1khz_db=0.12, expanded_uncertainty_10khz_db=0.4), 'secondary_pressure': ReferenceCalibrationRow(microphone_types='LS', method='Secondary pressure calibration with the addition of a free-field to pressure sensitivity level difference', references=('IEC 61094-5', 'IEC/TS 61094-7'), expanded_uncertainty_1khz_db=0.15, expanded_uncertainty_10khz_db=0.5), 'secondary_free_field': ReferenceCalibrationRow(microphone_types='LS and WS', method='Secondary free-field calibration', references=('IEC 61094-8',), expanded_uncertainty_1khz_db=0.2, expanded_uncertainty_10khz_db=0.5), 'electrostatic_actuator': ReferenceCalibrationRow(microphone_types='LS and WS', method='Electrostatic actuator calibration with the addition of a free-field to actuator response level difference', references=('IEC 61094-6',), expanded_uncertainty_1khz_db=0.3, expanded_uncertainty_10khz_db=0.6)}
```

## IEC61094_8_TABLE_2

*Constant* (`mapping`).

## jig_diameter_correction

```python
jig_diameter_correction(
    frequencies_hz: ArrayLike | None = None,
) -> JigDiameterCorrection
```

The corrections of IEC 61094-5:2016 Table A.1 for a type WS3 microphone
against a type LS2aP reference in the jig of Figure A.4.

The table gives them at the preferred one-third-octave frequencies from
1 kHz, -0,004 dB, to 20 kHz, -1,443 dB, calculated for a radially
symmetrical field and the 0,5 mm diaphragm separation of Figure A.4, "the
only one for which the corrections specified in Table A.1 are valid". A
frequency within 2 % of a row, such as an exact base-ten one-third-octave
frequency, reads as that row. Pass `.correction_db` to the comparison as
one of its `corrections_db` and `.standard_uncertainty_db` to the
budget as an additional component.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies of the table, in Hz, increasing (Default: None, the 14 rows). |

**Returns:** The [`JigDiameterCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#jigdiametercorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency the table does not print. |

## JigDiameterCorrection

```python
JigDiameterCorrection(
    frequencies_hz: NDArray[np.float64],
    correction_db: NDArray[np.float64],
)
```

The corrections of IEC 61094-5 Table A.1 at the frequencies asked for.

Added to the sensitivity level of a type WS3 microphone calibrated against
a type LS2aP reference in the jig of Figure A.4, they account for the
radial sensitivity of the two diaphragms and for the smaller one of the
test microphone. Their expanded uncertainty is 10 % of their value
(A.2 and the NOTE to Table A.1), a component of the budget of Table D.1.
None of the three places that give the 10 % states its coverage factor;
the library reads it as $k = 2$, the factor 7.9 and D.2 report every
expanded uncertainty with.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies of the table asked for, in Hz. |
| `correction_db` | The correction at each, in dB. |

### JigDiameterCorrection.expanded_uncertainty_db

*property*

The expanded uncertainty of each correction, one tenth of its
magnitude, in dB (read as $k = 2$, 7.9 and D.2).

### JigDiameterCorrection.plot()

```python
JigDiameterCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the corrections with their expanded uncertainty.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the correction curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### JigDiameterCorrection.standard_uncertainty_db

*property*

The standard uncertainty of each correction, the expanded one over
$k = 2$ (a reading of 7.9 and D.2, since the 10 % comes without
a coverage factor), in dB: the special-case component of Table D.1.

## ReferenceCalibrationRow

```python
ReferenceCalibrationRow(
    microphone_types: str,
    method: str,
    references: tuple[str, ...],
    expanded_uncertainty_1khz_db: float,
    expanded_uncertainty_10khz_db: float,
)
```

One row of IEC 61094-8:2012 Table 1: a way the reference microphone's
free-field sensitivity can be known, and the expanded uncertainty
($k = 2$) it typically carries.

**Attributes**

| Name | Description |
| :--- | :--- |
| `microphone_types` | The reference microphone types the row is for, `"LS"` or `"LS and WS"`. |
| `method` | The calibration method as the table prints it. |
| `references` | The documents that define it. |
| `expanded_uncertainty_1khz_db` | The typical expanded uncertainty at 1 kHz, in dB. |
| `expanded_uncertainty_10khz_db` | The same at 10 kHz, in dB. |

## sequential_comparison

```python
sequential_comparison(
    frequencies_hz: ArrayLike,
    reference_sensitivity_level_db: ArrayLike,
    reference_output_level_db: ArrayLike,
    test_output_level_db: ArrayLike,
    *,
    reference_monitor_level_db: ArrayLike | None = None,
    test_monitor_level_db: ArrayLike | None = None,
    field: str = 'pressure',
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ComparisonCalibration
```

Calibration by comparison with the microphones put in the field in
turn (IEC 61094-5:2016 5.1.3 and Annex B; IEC 61094-8:2012 5.2 and
Annex A).

The reference and the test microphone take the same place one after the
other. Either the exchange does not change the sound pressure
significantly, or any change is detected and corrected (IEC 61094-5
5.1.3, IEC 61094-8 5.2), for example with a monitor microphone near the
source: the ratio of each microphone's output to the monitor's output,
and the quotient of the two ratios, "gives the ratio of the microphone
under test output voltage to the reference microphone output voltage,
corrected for any variation in the sound pressure generated by the
source" (IEC 61094-8 A.2). With $V_\mathrm{ref}$ and
$V_\mathrm{mon,1}$ the outputs of the reference and the monitor in
the first measurement, and $V_\mathrm{test}$ and
$V_\mathrm{mon,2}$ those of the second,

$$
20\lg R_V = 20\lg\frac{V_\mathrm{test}}{V_\mathrm{mon,2}} - 20\lg\frac{V_\mathrm{ref}}{V_\mathrm{mon,1}}
$$

and without a monitor $20\lg(V_\mathrm{test}/V_\mathrm{ref})$,
the plain difference of the two output levels. The sensitivity level of
the test microphone then follows by D.2.

Each reading may be one value per frequency or a matrix of one row per
determination; the calibration averages the determinations.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `reference_sensitivity_level_db` | $L_\mathrm{ref}$, the reference microphone's sensitivity level, in dB re 1 V/Pa. |
| `reference_output_level_db` | $20\lg V_\mathrm{ref}$, the reference microphone's output level, in dB re any voltage the test microphone is read against too. |
| `test_output_level_db` | $20\lg V_\mathrm{test}$, the test microphone's output level, in dB re the same voltage. |
| `reference_monitor_level_db` | $20\lg V_\mathrm{mon,1}$, the monitor's output level in the measurement of the reference, in dB (Default: None, no monitor). |
| `test_monitor_level_db` | $20\lg V_\mathrm{mon,2}$, the monitor's output level in the measurement of the test microphone, in dB (Default: None; given with the other or not at all). |
| `field` | `"pressure"` (IEC 61094-5, default) or `"free_field"` (IEC 61094-8). |
| `pressure_level_difference_db` | $20\lg R_P$, in dB (Default: 0). |
| `corrections_db` | Further corrections added to the level, by name, in dB (Default: none). |
| `reference_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) of the reference, added (Default: None). |
| `test_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) of the test microphone, subtracted (Default: None). |
| `reference_free_field_difference_db` | The reference's free-field to pressure sensitivity level difference (IEC/TS 61094-7), free field only, in dB; carried in `corrections_db` as `"reference free-field difference"` (Default: None). |
| `expanded_uncertainty_db` | The expanded uncertainty ($k = 2$) of the result at each frequency, in dB (Default: None). |

**Returns:** The [`ComparisonCalibration`](/phonometry/reference/api/metrology/comparison-calibration/#comparisoncalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown field, one monitor reading without the other, a free-field correction on a pressure calibration, an environmental correction made at other frequencies, readings whose numbers of determinations disagree, or any column that is not one finite value per frequency. |

## simultaneous_comparison

```python
simultaneous_comparison(
    frequencies_hz: ArrayLike,
    reference_sensitivity_level_db: ArrayLike,
    channel_difference_db: ArrayLike,
    interchanged_channel_difference_db: ArrayLike | None = None,
    *,
    field: str = 'pressure',
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ComparisonCalibration
```

Calibration by comparison with both microphones in the field at once
(IEC 61094-5:2016 5.1.2 and Annex C; IEC 61094-8:2012 5.3).

Each microphone is read on its own measuring channel. With the reference
on channel 1, the level reading difference between the channels is
Formula (C.1),

$$
L_\mathrm{C12} = (L_1 + L_\mathrm{m1} + L_\mathrm{d1} + L_\mathrm{WA}) - (L_2 + L_\mathrm{m2} + L_\mathrm{d1} + L_\mathrm{WB})
$$

and after the microphones are interchanged, in the coupler ports and on
the preamplifiers, it is Formula (C.2). Their difference leaves the two
sensitivity levels alone, whatever the gains of the channels and the
asymmetry of the field, Formula (C.3):

$$
L_\mathrm{ref} - L_\mathrm{test} = \tfrac12\left(L_\mathrm{C12} - L_\mathrm{C21}\right)
$$

so $20\lg R_V = -\tfrac12(L_\mathrm{C12} - L_\mathrm{C21})$, and the
sensitivity level of the test microphone follows by D.2. A pressure
calibration requires the interchange ("the microphones shall be
interchanged, and the measurement repeated", 5.1.2). A free-field one does
not (5.3 relies on a symmetrical field instead); without it, the channel
difference is taken as $-20\lg R_V$, which assumes channels of equal
gain.

Each reading may be one value per frequency or a matrix of one row per
determination (the three repeats of D.2, say); the calibration averages
the determinations.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `reference_sensitivity_level_db` | $L_\mathrm{ref}$, the reference microphone's sensitivity level, in dB re 1 V/Pa, one value or one per frequency. For a free-field calibration it is the reference's free-field level, or its pressure level with `reference_free_field_difference_db`. |
| `channel_difference_db` | $L_\mathrm{C12}$, the reading of channel 1 less that of channel 2 with the reference on channel 1, in dB. |
| `interchanged_channel_difference_db` | $L_\mathrm{C21}$, the same difference after the interchange, the test microphone on channel 1, in dB (Default: None; required for `field="pressure"`). |
| `field` | `"pressure"` (IEC 61094-5, default) or `"free_field"` (IEC 61094-8). |
| `pressure_level_difference_db` | $20\lg R_P$, the effective sound pressure on the test microphone re that on the reference, in dB (Default: 0, the ratio reduced to unity). |
| `corrections_db` | Further corrections added to the level, by name, in dB, such as `jig_diameter_correction(f).correction_db` (Default: none). |
| `reference_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) that takes the reference's level from the conditions of its calibration to those of the test, added (Default: None). |
| `test_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) of the test microphone from the reference conditions to those of the test, subtracted to refer the result to the reference conditions (Default: None, the result is at the conditions of the test). |
| `reference_free_field_difference_db` | The reference's free-field to pressure sensitivity level difference (IEC/TS 61094-7), added to a pressure-calibrated reference in a free-field calibration only, in dB; the result carries it in `corrections_db` as `"reference free-field difference"` (Default: None). |
| `expanded_uncertainty_db` | The expanded uncertainty ($k = 2$) of the result at each frequency, in dB, as [`comparison_uncertainty_budget`](/phonometry/reference/api/metrology/comparison-calibration/#comparison_uncertainty_budget) gives it (Default: None). |

**Returns:** The [`ComparisonCalibration`](/phonometry/reference/api/metrology/comparison-calibration/#comparisoncalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown field, a pressure calibration without the interchange, a free-field correction on a pressure calibration, an environmental correction made at other frequencies, readings whose numbers of determinations disagree, or any column that is not one finite value per frequency. |
