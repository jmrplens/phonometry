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
[`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison) computes it, with the [`MonitorReadings`](/phonometry/reference/api/metrology/comparison-calibration/#monitorreadings)
of the monitor or without.

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
the test ([`air`](/phonometry/reference/api/fluids/air/)). Turned round,
[`reflection_free_window_s`](/phonometry/reference/api/metrology/comparison-calibration/#reflection_free_window_s) gives the longest window that keeps a
reflection of a known path outside it.

**The phase of the sensitivity** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). Both
parts carry the phase over with the modulus: IEC 61094-5 calculates "the
sensitivity (both modulus and phase) of the test microphone", and IEC
61094-8 "both the modulus and phase of the free-field sensitivity of the
microphone under test". The model of D.2 holds for the complex ratios, so
the phase follows the level term by term:

$$
\varphi_\mathrm{test} = \varphi_\mathrm{ref} + \arg R_V - \arg R_P
$$

and the interchange of Annex C cancels the phase shifts of the two channels
and of the field just as (C.3) cancels their gains,
$\varphi_\mathrm{ref} - \varphi_\mathrm{test} = \tfrac12(\Phi_\mathrm{C12} - \Phi_\mathrm{C21})$. In a free field the phases
have to be referred to the acoustic centres of the microphones (5.1 of the
second part), which 7.3 positions "at the measurement points"; in a
sequential substitution both centres go to the same point in turn, and the
pressures on the two microphones have the same phase there. The phase inputs
of a calibration travel together, as a [`SimultaneousComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneouscomparisonphase)
or a [`SequentialComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#sequentialcomparisonphase).

**Different acoustic impedances** (IEC 61094-5 7.4 and 7.5). Two microphones
of different acoustic impedance do not see the same sound pressure; neither
clause prints a model, and both ask for the effect to be assessed and taken
into the budget. [`impedance_pressure_ratio`](/phonometry/reference/api/metrology/comparison-calibration/#impedance_pressure_ratio) writes it in one form, each
microphone's equivalent volume $V_\mathrm{e}$ (IEC 61094-1 6.2.2)
against the equivalent volume $V_x$ of what it works into,

$$
R_P = \frac{V_x + V_\mathrm{e,ref}}{V_x + V_\mathrm{e,test}}
$$

for two circuits: a closed coupler, the printed Formula (3) of IEC 61094-2,
for a sequential substitution; and, for a simultaneous excitation, each
microphone behind the air between the two, a divider that is this library's
reading of the sentence of Table D.1 ("Microphone impedance") that puts them
in series, which prints no circuit.
[`ReciprocityMicrophone.complex_equivalent_volume_m3`](/phonometry/reference/api/metrology/reciprocity-coupler/#reciprocitymicrophonecomplex_equivalent_volume_m3) gives
$V_\mathrm{e}$ from the lumped parameters of IEC 61094-2 E.4.

**Time-selective processing** (IEC 61094-8 Annex B). A free field can be
simulated by keeping only the direct sound of an impulse response:
[`time_selective_response`](/phonometry/reference/api/metrology/comparison-calibration/#time_selective_response) weights the response with a time window
(B.1.3), with the "'tapered' edges" B.1.2 says it "normally has", and
transforms what is left by Formula (B.2), at any frequency. The impulse response comes from any of the methods of B.2 to B.6:
[`stepped_sine_impulse_response`](/phonometry/reference/api/metrology/comparison-calibration/#stepped_sine_impulse_response) takes a stepped-sine measurement to
the time domain by Formula (B.3), and the sweeps, the maximum length
sequences and the random noise of B.3 to B.5 are those of
`phonometry.room` and `phonometry.electroacoustics`. For the direct
impulse method of B.6, [`rectangular_pulse`](/phonometry/reference/api/metrology/comparison-calibration/#rectangular_pulse) is the pulse of Formula
(B.10) and [`rectangular_pulse_duration_s`](/phonometry/reference/api/metrology/comparison-calibration/#rectangular_pulse_duration_s) the duration whose first
spectral zero lies an order of magnitude above the frequencies of interest.

Two printed values the library does not follow
----------------------------------------------

**IEC 61094-5 D.3.** The root-sum-square of the eight components Table D.1
prints is 0,0437 dB, not the 0,040 dB D.3 states; with $k = 2$ it is
0,087 dB rather than 0,08 dB. [`comparison_uncertainty_budget`](/phonometry/reference/api/metrology/comparison-calibration/#comparison_uncertainty_budget) gives the
sum of the printed components, and the defect is in `docs/ERRATA.md`.

**IEC 61094-8 B.10.** The spectrum of Formula (B.10) is that of a rectangular
pulse of duration $2b$, although the text calls $b$ the duration.
The formula and the first zero it puts at $1/(2b)$ agree, so the library
follows them and reads $b$ as the half-duration:
[`rectangular_pulse`](/phonometry/reference/api/metrology/comparison-calibration/#rectangular_pulse) takes the whole duration $T = 2b$. The defect
is in `docs/ERRATA.md`.

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
    *,
    reference_sensitivity_phase_deg: NDArray[np.float64] | None = None,
    output_phase_differences_deg: NDArray[np.float64] | None = None,
    pressure_phase_difference_deg: NDArray[np.float64] | None = None,
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
| `reference_sensitivity_phase_deg` | $\varphi_\mathrm{ref}$, the phase of the reference microphone's sensitivity, in degrees, or `None` for a calibration of the level alone. |
| `output_phase_differences_deg` | $\arg R_V$ of each determination, one row per determination, in degrees, or `None`. |
| `pressure_phase_difference_deg` | $\arg R_P$, in degrees, or `None`. |

### ComparisonCalibration.correction_db

*property*

$\sum_j C_j$, in dB (0 without corrections).

### ComparisonCalibration.determinations

*property*

The number of determinations averaged.

### ComparisonCalibration.output_level_difference_db

*property*

$20\lg R_V$, the mean over the determinations, in dB.

### ComparisonCalibration.output_phase_difference_deg

*property*

$\arg R_V$, the mean over the determinations, in degrees, or
`None` for a calibration of the level alone.

### ComparisonCalibration.plot()

```python
ComparisonCalibration.plot(
    ax: Axes | None = None,
    *,
    quantity: str = 'level',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $L_\mathrm{test}$ and the reference's level against
frequency, with the expanded uncertainty as a band when it is known,
or the two phases.

The reference's level is $L_\mathrm{ref}$, or, in a free field
against a pressure-calibrated reference, $L_\mathrm{ref}$ plus
its free-field difference: the level the test microphone was
compared with.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `quantity` | `"level"` (default), or `"phase"` for $\varphi_\mathrm{test}$ and $\varphi_\mathrm{ref}$ of a calibration that carries them. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of the microphone under test. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown quantity, or the phase of a calibration of the level alone. |

### ComparisonCalibration.sensitivity_level_db

*property*

$L_\mathrm{test}$, in dB re 1 V/Pa.

### ComparisonCalibration.sensitivity_mv_per_pa

*property*

$M_\mathrm{test} = 10^{L_\mathrm{test}/20}$ V/Pa, in mV/Pa.

### ComparisonCalibration.sensitivity_phase_deg

*property*

$\varphi_\mathrm{test} = \varphi_\mathrm{ref} + \arg R_V - \arg R_P$, in degrees from -180° (excluded) to 180°, or `None` for a
calibration of the level alone (IEC 61094-5 5.1.1, IEC 61094-8 5.1).

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

## impedance_pressure_ratio

```python
impedance_pressure_ratio(
    frequencies_hz: ArrayLike,
    *,
    reference_equivalent_volume_m3: ArrayLike,
    test_equivalent_volume_m3: ArrayLike,
    coupling_equivalent_volume_m3: ArrayLike | None = None,
    coupling_impedance_pa_s_m3: ArrayLike | None = None,
) -> ImpedancePressureRatio
```

The ratio of the sound pressures that the different acoustic
impedances of two microphones cause (IEC 61094-5:2016 7.4 and 7.5).

"Differences in the acoustic impedance between the test and reference
microphones can cause the sound pressure at the test and reference
microphones to differ" (7.4), most where a pressure and a free-field
response microphone meet above 10 kHz (7.5). Neither clause prints a
model; both refer the effect to the uncertainty, and 7.4 to the
literature for a model. This function writes two circuits: the closed
coupler that IEC 61094-2 prints as Formula (3), and a series divider that
is this library's reading of the one sentence Table D.1 gives the
simultaneous excitation. Each microphone enters by its equivalent volume
$V_\mathrm{e} = \kappa_\mathrm{r} p_{s,\mathrm{r}}/(\mathrm{j}\omega Z_\mathrm{a})$ (IEC 61094-1 6.2.2, with $\kappa_\mathrm{r} = 1{,}40$
and $p_{s,\mathrm{r}}$ = 101,325 kPa):

* **A closed coupler, sequential substitution.** In a coupler small
  against the wavelength, the source drives the sum of the admittances of
  the gas and of every microphone in it, IEC 61094-2:2009 Formula (3),
  $1/Z = \mathrm{j}\omega\,[V/(\kappa p_s) + \sum V_\mathrm{e}/(\kappa_\mathrm{r} p_{s,\mathrm{r}})]$, so putting the test
  microphone in the place of the reference changes the pressure by
  $R_P = (V_x + V_\mathrm{e,ref})/(V_x + V_\mathrm{e,test})$, with
  $V_x$ the rest of the load: the gas volume referred to the
  reference conditions, $V \kappa_\mathrm{r} p_{s,\mathrm{r}}/(\kappa p_s)$, and the equivalent volumes of
  the source and of any monitor. A monitor that "accurately sense[s]
  changes in the sound pressure at the test/reference microphone
  position" (5.1.3) corrects for this ratio; without one it is the
  correction. Pass `coupling_equivalent_volume_m3`.
* **The air between the microphones in series, simultaneous
  excitation.** "The acoustical impedance of the microphone acts in
  series with that of the air in the space between the two microphones.
  Microphones with different acoustic impedance therefore see slightly
  different pressures when simultaneously exposed to the same pressure
  field" (Table D.1, "Microphone impedance"). The row prints no circuit;
  this library reads it as a divider, each diaphragm taking the pressure
  $p_0 Z_\mathrm{a}/(Z_\mathrm{a} + Z_x)$ of the common field
  $p_0$ behind the same series impedance $Z_x$, the reading
  in which the two microphones see the different pressures the row
  concludes they do. Written with volumes this is
  the same ratio, $V_x$ being the equivalent volume of
  $Z_x$, $\kappa_\mathrm{r} p_{s,\mathrm{r}}/(\mathrm{j}\omega Z_x)$. Pass `coupling_impedance_pa_s_m3`; the parts print no value
  for it, and Table D.1 asks for the effect to be "established
  experimentally" when the impedances differ significantly.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `reference_equivalent_volume_m3` | $V_\mathrm{e,ref}$, complex, in m³, one value or one per frequency, such as [`ReciprocityMicrophone.complex_equivalent_volume_m3`](/phonometry/reference/api/metrology/reciprocity-coupler/#reciprocitymicrophonecomplex_equivalent_volume_m3) gives it from the lumped parameters of IEC 61094-2 E.4. Its ratio to $V_\mathrm{eq}$ holds no $\kappa_\mathrm{r}$, so the volume keeps the definition $V_\mathrm{eq}$ was given in, the $\kappa_\mathrm{r} = 1{,}40$ of IEC 61094-1 for the values of its Table 3; a series impedance is turned into $V_x$ with that same 1,40. |
| `test_equivalent_volume_m3` | $V_\mathrm{e,test}$, in m³. |
| `coupling_equivalent_volume_m3` | $V_x$ of a closed coupler, in m³ at the reference conditions (Default: None). |
| `coupling_impedance_pa_s_m3` | $Z_x$, the acoustic impedance in series with each microphone, in Pa·s/m³ (Default: None; give exactly one of the two). |

**Returns:** The [`ImpedancePressureRatio`](/phonometry/reference/api/metrology/comparison-calibration/#impedancepressureratio).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, not exactly one of the two couplings, a series impedance of zero, a column that is not one finite value per frequency, or a coupling and a test microphone whose equivalent volumes cancel. |

## ImpedancePressureRatio

```python
ImpedancePressureRatio(
    frequencies_hz: NDArray[np.float64],
    ratio: NDArray[np.complex128],
    coupling: str,
    coupling_equivalent_volume_m3: NDArray[np.complex128],
)
```

The ratio of the sound pressures on the test and the reference
microphone that their different acoustic impedances cause
(IEC 61094-5:2016 7.4 and 7.5).

$$
R_P = \frac{V_x + V_\mathrm{e,ref}}{V_x + V_\mathrm{e,test}}
$$

with $V_\mathrm{e}$ the equivalent volume of each microphone and
$V_x$ that of what it works into. Its level,
`level_difference_db`, is the `pressure_level_difference_db` of a
comparison, and its phase the `pressure_phase_difference_deg`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `ratio` | $R_P$ at each frequency, complex. |
| `coupling` | `"coupler"`, a closed coupler small against the wavelength (IEC 61094-2 Formula (3)), or `"series"`, the air between the microphones in series with each, this library's reading of IEC 61094-5 Table D.1. |
| `coupling_equivalent_volume_m3` | $V_x$ at each frequency, complex, in m³. |

### ImpedancePressureRatio.level_difference_db

*property*

$20\lg\lvert R_P\rvert$, in dB: what the test microphone
hears more than the reference.

### ImpedancePressureRatio.phase_difference_deg

*property*

$\arg R_P$, in degrees.

### ImpedancePressureRatio.plot()

```python
ImpedancePressureRatio.plot(
    ax: Axes | None = None,
    *,
    quantity: str = 'level',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $20\lg\lvert R_P\rvert$ and its standard uncertainty,
or $\arg R_P$, against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `quantity` | `"level"` (default) or `"phase"`. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of $R_P$. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown quantity. |

### ImpedancePressureRatio.standard_uncertainty_db

*property*

The level difference taken as the semi-range of a rectangular
distribution, $\lvert 20\lg\lvert R_P\rvert\rvert/\sqrt{3}$, in
dB.

This is how Table D.1 of IEC 61094-5 carries the effect, a semi-range
of 0,005 dB at 2 kHz giving 0,003 dB, and how 7.5 asks for it when no
reference of similar impedance is available: "the size of the error
caused should be estimated and added to the uncertainty budget". It
is the `"impedance"` component of
[`comparison_uncertainty_budget`](/phonometry/reference/api/metrology/comparison-calibration/#comparison_uncertainty_budget); a calibration that corrects for
$R_P$ instead takes only what is left of it. The same row of
Table D.1 warns that "when microphones have significantly differing
impedances (for example WS2F microphone compared against LS2P at
frequencies above 10 kHz), the measurement uncertainty can be
considerably larger and should be established experimentally": there
this value is an estimate of the model's, not a substitute for that
experiment.

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

## MonitorReadings

```python
MonitorReadings(
    *,
    reference_level_db: ArrayLike,
    test_level_db: ArrayLike,
    reference_phase_deg: ArrayLike | None = None,
    test_phase_deg: ArrayLike | None = None,
)
```

The readings of the monitor microphone that watches the source of a
sequential calibration (IEC 61094-5:2016 5.1.3, IEC 61094-8:2012 A.2).

They travel together because they are one instrument's: the monitor is
read in the measurement of each microphone, and each microphone's output
is taken re the monitor reading taken with it, so a source that drifts
between the two measurements cancels in the quotient of the two ratios.
Its phases are read with its levels when the calibration carries the
phase. Pass one to [`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison) as `monitor`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_level_db` | $20\lg V_\mathrm{mon,1}$, the monitor's output level in the measurement of the reference, in dB, one row per determination. |
| `test_level_db` | $20\lg V_\mathrm{mon,2}$, the monitor's output level in the measurement of the test microphone, in dB. |
| `reference_phase_deg` | $\varphi_\mathrm{mon,1}$, the monitor's phase in the measurement of the reference, in degrees (Default: None). |
| `test_phase_deg` | $\varphi_\mathrm{mon,2}$, the monitor's phase in the measurement of the test microphone, in degrees (Default: None; given with the other or not at all). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for one phase without the other. |

## rectangular_pulse

```python
rectangular_pulse(
    duration_s: float,
    *,
    amplitude_v: float = 1.0,
) -> RectangularPulse
```

The rectangular pulse of the direct impulse method (IEC 61094-8:2012
B.6.1).

"A signal that approximates an idealized unit impulse (delta function)
can be directly applied to the sound source", and "in order to have a
flat spectrum in the frequency range of interest [...] the duration of
the input signal needs to be sufficiently short": its spectrum is Formula
(B.10). Give the whole duration $T$; Formula (B.10) writes it as
$2b$ (`docs/ERRATA.md`). [`rectangular_pulse_duration_s`](/phonometry/reference/api/metrology/comparison-calibration/#rectangular_pulse_duration_s)
gives the duration for an upper limit of frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `duration_s` | $T = 2b$, in s. |
| `amplitude_v` | $a$, in V (Default: 1). |

**Returns:** The [`RectangularPulse`](/phonometry/reference/api/metrology/comparison-calibration/#rectangularpulse).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a duration or an amplitude that is not positive. |

## rectangular_pulse_duration_s

```python
rectangular_pulse_duration_s(
    upper_frequency_hz: float,
    *,
    zero_ratio: float = 10.0,
) -> float
```

The duration of a rectangular pulse whose first spectral zero lies a
given factor above the frequencies of interest (IEC 61094-8:2012 B.6.1).

The first zero, $1/(2b) = 1/T$, "must be approximately an order of
magnitude higher than the upper limit of the frequency range of interest,
leading to a requirement for the duration, $b$ of just a few
microseconds":

$$
T = 2b = \frac{1}{r\, f_\mathrm{max}}
$$

with $r$ the factor, 10 by default. For 20 kHz that is 5 µs, a
half-duration $b$ of 2,5 µs, at which the spectrum has fallen by
0,14 dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `upper_frequency_hz` | $f_\mathrm{max}$, in Hz. |
| `zero_ratio` | $r$, the first zero over $f_\mathrm{max}$ (Default: 10, an order of magnitude). |

**Returns:** $T$, in s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency that is not positive or a ratio that is not above 1. |

## RectangularPulse

```python
RectangularPulse(duration_s: float, amplitude_v: float = 1.0)
```

The rectangular pulse of the direct impulse method (IEC 61094-8:2012
B.6.1, Formula (B.10)).

A pulse of amplitude $a$ lasting $T$ has the spectrum

$$
X(f) = \frac{2ab\sin(2\pi f b)}{2\pi f b}, \qquad b = T/2
$$

Formula (B.10), whose first zero is at $f = 1/(2b) = 1/T$. The
standard calls $b$ the duration; the formula and its first zero
are those of a pulse lasting $2b$ (`docs/ERRATA.md`), and the
library follows them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `duration_s` | $T = 2b$, how long the pulse lasts, in s. |
| `amplitude_v` | $a$, the voltage applied to the source, in V. |

### RectangularPulse.area_v_s

*property*

$X(0) = 2ab$, the area of the pulse, in V·s.

### RectangularPulse.first_zero_hz

*property*

$1/(2b)$, the first zero of the spectrum, in Hz (B.6.1).

### RectangularPulse.half_duration_s

*property*

$b$ of Formula (B.10), half the duration, in s.

### RectangularPulse.level_db_at()

```python
RectangularPulse.level_db_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

$20\lg\lvert X(f)/X(0)\rvert$, how far the spectrum has
fallen from its value at 0 Hz, in dB (minus infinity at a zero).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Any frequencies, in Hz. |

**Returns:** The level at each, in dB.

### RectangularPulse.plot()

```python
RectangularPulse.plot(
    ax: Axes | None = None,
    *,
    upper_frequency_hz: float | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $\lvert X(f)/X(0)\rvert$ in dB up to past its second
zero, with the first zero and, when given, the upper limit of the
frequencies of interest.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `upper_frequency_hz` | The upper limit of the frequencies of interest, in Hz, marked with the level the pulse has fallen by there (Default: None). |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the spectrum. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### RectangularPulse.spectrum_at()

```python
RectangularPulse.spectrum_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

$X(f)$ of Formula (B.10), in V·s, the transform of the pulse
centred on the time origin, where it is real.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Any frequencies, in Hz. |

**Returns:** $X(f)$ at each.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency that is not finite. |

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

## reflection_free_window_s

```python
reflection_free_window_s(
    source_distance_m: float,
    reflected_path_m: float,
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    relative_humidity_percent: float = 50.0,
) -> float
```

The longest time window that keeps a reflection outside the effective
free-field region (IEC 61094-8:2012 B.1 and B.1.3 a)).

A point on the boundary of the region of Formula (B.1) reflects along a
path of the major diameter $A = d + \tau c$, from the source to it
and on to the microphone, so a reflection whose path is $L$ stays
outside the region, and out of the window, while

$$
\tau \le \frac{L - d}{c}
$$

with $\tau$ measured from the arrival of the direct sound. B.1.3
places the window by "the relative distance between source and
microphone [...] and from the source to the walls or other reflecting
objects"; for a plane reflector the path is that of the image of the
source in it. The tapered edge the window "normally has" (B.1.2) has to
fall within this time too.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d$, the separation of the acoustic centres of the source and the microphone, in m. |
| `reflected_path_m` | $L$, the length of the shortest reflected path, from the source by the reflector to the microphone, in m. |
| `temperature_c` | The air temperature, in °C (Default: 23,0). |
| `static_pressure_kpa` | The static pressure, in kPa (Default: 101,325). |
| `relative_humidity_percent` | The relative humidity, in % (Default: 50). |

**Returns:** $(L - d)/c$, in s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a separation that is not positive, a reflected path that is not longer than the direct one, or conditions Annex F refuses. |

## sequential_comparison

```python
sequential_comparison(
    frequencies_hz: ArrayLike,
    reference_sensitivity_level_db: ArrayLike,
    reference_output_level_db: ArrayLike,
    test_output_level_db: ArrayLike,
    *,
    monitor: MonitorReadings | None = None,
    field: str = 'pressure',
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
    phase: SequentialComparisonPhase | None = None,
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

**Phase** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). With the phase of the
reference's sensitivity and the phases of the two outputs, given together
as a [`SequentialComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#sequentialcomparisonphase) and read against the monitor's
output (its phases in the [`MonitorReadings`](/phonometry/reference/api/metrology/comparison-calibration/#monitorreadings)) or against the signal
driving the source, the calibration carries the phase of the test
microphone too, the quotient of the ratios written for their phases:

$$
\arg R_V = (\varphi_\mathrm{test} - \varphi_\mathrm{mon,2}) - (\varphi_\mathrm{ref} - \varphi_\mathrm{mon,1})
$$

In a free field the phases are those at the acoustic centres of the
microphones (IEC 61094-8 5.1); with each centre placed in turn at the
same measurement point (7.3), $\arg R_P$ is 0.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `reference_sensitivity_level_db` | $L_\mathrm{ref}$, the reference microphone's sensitivity level, in dB re 1 V/Pa. |
| `reference_output_level_db` | $20\lg V_\mathrm{ref}$, the reference microphone's output level, in dB re any voltage the test microphone is read against too. |
| `test_output_level_db` | $20\lg V_\mathrm{test}$, the test microphone's output level, in dB re the same voltage. |
| `monitor` | The [`MonitorReadings`](/phonometry/reference/api/metrology/comparison-calibration/#monitorreadings) of a monitor microphone, $20\lg V_\mathrm{mon,1}$ and $20\lg V_\mathrm{mon,2}$ in the measurements of the reference and of the test microphone, with their phases when the calibration carries the phase (Default: None, no monitor). |
| `field` | `"pressure"` (IEC 61094-5, default) or `"free_field"` (IEC 61094-8). |
| `pressure_level_difference_db` | $20\lg R_P$, in dB (Default: 0). |
| `corrections_db` | Further corrections added to the level, by name, in dB (Default: none). |
| `reference_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) of the reference, added (Default: None). |
| `test_environment` | The [`EnvironmentalSensitivityCorrection`](/phonometry/reference/api/metrology/comparison-calibration/#environmentalsensitivitycorrection) of the test microphone, subtracted (Default: None). |
| `reference_free_field_difference_db` | The reference's free-field to pressure sensitivity level difference (IEC/TS 61094-7), free field only, in dB; carried in `corrections_db` as `"reference free-field difference"` (Default: None). |
| `expanded_uncertainty_db` | The expanded uncertainty ($k = 2$) of the result at each frequency, in dB (Default: None). |
| `phase` | The [`SequentialComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#sequentialcomparisonphase) of the calibration: the reference's phase, the output phases and $\arg R_P$ (Default: None, a calibration of the level alone). |

**Returns:** The [`ComparisonCalibration`](/phonometry/reference/api/metrology/comparison-calibration/#comparisoncalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown field, a free-field correction on a pressure calibration, an environmental correction made at other frequencies, readings whose numbers of determinations disagree, any column that is not one finite value per frequency, or monitor phases without the output phases. |

## SequentialComparisonPhase

```python
SequentialComparisonPhase(
    *,
    reference_sensitivity_phase_deg: ArrayLike,
    reference_output_phase_deg: ArrayLike,
    test_output_phase_deg: ArrayLike,
    pressure_phase_difference_deg: ArrayLike | None = None,
)
```

The phase inputs of a calibration by sequential excitation
(IEC 61094-5:2016 5.1.1, IEC 61094-8:2012 5.1).

They travel together because the phase of the test microphone needs all of
them at once: the phase of the reference's sensitivity it is carried over
from, and the phases of the two outputs, read against the monitor's output
or against the signal driving the source; $\arg R_P$ completes them
where the pressures on the two microphones differ in phase. The monitor's
own phases are read with its levels, in [`MonitorReadings`](/phonometry/reference/api/metrology/comparison-calibration/#monitorreadings). Pass one
to [`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison) as `phase`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_sensitivity_phase_deg` | $\varphi_\mathrm{ref}$, the phase of the reference's sensitivity, in degrees, one value or one per frequency. |
| `reference_output_phase_deg` | The phase of the reference microphone's output, in degrees, one row per determination. |
| `test_output_phase_deg` | The phase of the test microphone's output, in degrees, one row per determination. |
| `pressure_phase_difference_deg` | $\arg R_P$, in degrees (Default: None, 0). |

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
    phase: SimultaneousComparisonPhase | None = None,
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

**Phase** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). With the phase of the
reference's sensitivity and the phase readings of the two channels, given
together as a [`SimultaneousComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneouscomparisonphase), the calibration
carries the phase of the test microphone too. The phase of
each channel's reading re the other's adds up as its level does in (C.1)
and (C.2), so their difference cancels the phase shifts of the channels
and of the field:

$$
\varphi_\mathrm{ref} - \varphi_\mathrm{test} = \tfrac12\left(\Phi_\mathrm{C12} - \Phi_\mathrm{C21}\right)
$$

with the difference of the two readings taken into one turn before it is
halved, so the result is unique while the two microphones differ by less
than 90°. Without the interchange, $-\Phi_\mathrm{C12}$ is taken as
$\arg R_V$. Neither part prints this form; it is (C.3) written for
the complex ratio the sensitivity "both modulus and phase" is.

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
| `phase` | The [`SimultaneousComparisonPhase`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneouscomparisonphase) of the calibration: the reference's phase, the phase readings and $\arg R_P$ (Default: None, a calibration of the level alone). |

**Returns:** The [`ComparisonCalibration`](/phonometry/reference/api/metrology/comparison-calibration/#comparisoncalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown field, a pressure calibration without the interchange, a free-field correction on a pressure calibration, an environmental correction made at other frequencies, readings whose numbers of determinations disagree, any column that is not one finite value per frequency, or phase readings that do not follow the level readings. |

## SimultaneousComparisonPhase

```python
SimultaneousComparisonPhase(
    *,
    reference_sensitivity_phase_deg: ArrayLike,
    channel_phase_difference_deg: ArrayLike,
    interchanged_channel_phase_difference_deg: ArrayLike | None = None,
    pressure_phase_difference_deg: ArrayLike | None = None,
)
```

The phase inputs of a calibration by simultaneous excitation
(IEC 61094-5:2016 5.1.1, IEC 61094-8:2012 5.1).

They travel together because the phase of the test microphone needs all of
them at once: the phase of the reference's sensitivity it is carried over
from, and the phase readings of the two channels that carry it, given as
the level readings are; $\arg R_P$ completes them where the pressures
on the two microphones differ in phase. Pass one to
[`simultaneous_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#simultaneous_comparison) as `phase`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_sensitivity_phase_deg` | $\varphi_\mathrm{ref}$, the phase of the reference's sensitivity, in degrees, one value or one per frequency. |
| `channel_phase_difference_deg` | $\Phi_\mathrm{C12}$, the phase of channel 1's reading re channel 2's with the reference on channel 1, in degrees, one row per determination. |
| `interchanged_channel_phase_difference_deg` | $\Phi_\mathrm{C21}$, the same after the interchange, in degrees (Default: None; given exactly when the interchanged level reading is). |
| `pressure_phase_difference_deg` | $\arg R_P$, the phase of the effective sound pressure on the test microphone re that on the reference, in degrees (Default: None, 0). |

## stepped_sine_impulse_response

```python
stepped_sine_impulse_response(
    frequencies_hz: ArrayLike,
    response: ArrayLike,
) -> SteppedSineImpulseResponse
```

The impulse response of a frequency response measured at linearly
spaced frequencies (IEC 61094-8:2012 B.2, Formula (B.3)).

"When the full range frequency response can be measured, an inverse
Fourier transform, Equation B.3, can be applied to transform this response
to the time domain, where time selective processes can be applied" (B.2.1),

$$
h(t) = \int_{-\infty}^{\infty} H(f)\,\mathrm{e}^{\mathrm{j}2\pi f t}\, \mathrm{d}f
$$

computed by the inverse FFT, which needs "the frequency response to be
measured at discrete frequencies and linearly spaced frequency
increments" and a range extended to 0 Hz: "the low frequency response can
be estimated from a knowledge of the pressure sensitivities of the
microphones", and the measurement should reach "about three times the
resonance frequency of the microphones". The axis therefore starts at
0 Hz, holds $K + 1$ frequencies $k\,\Delta f$, and the
response is taken as that of a real $h(t)$: the negative frequencies
are the complex conjugates of the positive ones, and the imaginary part
of the value at 0 Hz, which a real response does not have, is dropped.
The result has $N = 2K + 1$ samples at $f_\mathrm{s} = N\,\Delta f$
and lasts $1/\Delta f$, which has to be long enough "to include"
the reflections that matter (B.2.2): 120 Hz in a small anechoic room
whose primary reflections all arrive before 8 ms, about 30 Hz in a large
one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | $k\,\Delta f$, from 0 Hz, in Hz, equally spaced. |
| `response` | $H(k\,\Delta f)$, complex, one value per frequency. |

**Returns:** The [`SteppedSineImpulseResponse`](/phonometry/reference/api/metrology/comparison-calibration/#steppedsineimpulseresponse); pass its `impulse_response` and `sample_rate_hz` to [`time_selective_response`](/phonometry/reference/api/metrology/comparison-calibration/#time_selective_response).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than two frequencies, an axis that does not start at 0 Hz or is not equally spaced, or a response that is not one finite value per frequency. |

## SteppedSineImpulseResponse

```python
SteppedSineImpulseResponse(
    frequency_step_hz: float,
    impulse_response: NDArray[np.float64],
)
```

The impulse response of a stepped-sine measurement (IEC 61094-8:2012
B.2, Formula (B.3)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequency_step_hz` | $\Delta f$, the step of the measured frequencies, in Hz. |
| `impulse_response` | $h(t)$ at $t = n/f_\mathrm{s}$, in the unit of the response per second. |

### SteppedSineImpulseResponse.duration_s

*property*

$1/\Delta f$, how long the impulse response lasts, in s:
"the length of the impulse response will be the inverse of the size
of the frequency step" (B.2.2).

### SteppedSineImpulseResponse.plot()

```python
SteppedSineImpulseResponse.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the impulse response against time.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### SteppedSineImpulseResponse.sample_rate_hz

*property*

$f_\mathrm{s} = N\,\Delta f$, in Hz.

### SteppedSineImpulseResponse.time_s

*property*

The time of each sample, in s.

## time_selective_response

```python
time_selective_response(
    impulse_response: ArrayLike,
    sample_rate_hz: float,
    *,
    window_start_s: float,
    window_end_s: float,
    window_shape: str = 'tukey',
    taper_fraction: float = 0.25,
    excitation: RectangularPulse | None = None,
) -> TimeSelectiveResponse
```

The frequency response of the direct sound alone, through a time
window (IEC 61094-8:2012 Annex B).

"An impulse response (IR) can be obtained from the measured output of the
reference microphone or device under test, which separates the direct
and reflected energy components [...] enabling the two to be separated by
applying a time window" (B.1.1); "a time-domain to frequency-domain
transformation can then be used to obtain the desired frequency
response". The window is a weighting function that is zero outside the
chosen interval (B.1.3); a rectangular one "is not recommended because it
usually leads to spectral leakage", so the default is a Tukey window, flat
in the middle with cosine-tapered edges. Its placement and duration are
the user's, by the three criteria of B.1.3: the distances from the source
to the microphone and to the reflectors (see [`reflection_free_window_s`](/phonometry/reference/api/metrology/comparison-calibration/#reflection_free_window_s)),
the supporting structure beyond the rod, and a look at the impulse
response.

The impulse response may come from any method of Annex B: a stepped sine
by [`stepped_sine_impulse_response`](/phonometry/reference/api/metrology/comparison-calibration/#stepped_sine_impulse_response), a sweep or a maximum length
sequence by [`phonometry.room.impulse_response`](/phonometry/reference/api/rooms/impulse-response/) and
[`phonometry.room.mls_impulse_response`](/phonometry/reference/api/rooms/impulse-response/#mls_impulse_response), or a direct impulse (B.6), in
which case `excitation` divides the spectrum of the pulse out. The
reference and the test microphone are windowed alike, and the levels of
their responses at the calibration frequencies go to
[`sequential_comparison`](/phonometry/reference/api/metrology/comparison-calibration/#sequential_comparison) as the two output levels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `impulse_response` | The impulse response, one value per sample, from the start of the record. |
| `sample_rate_hz` | Its sample rate, in Hz. |
| `window_start_s` | Where the window begins, in s from the start of the record: before the direct sound arrives. |
| `window_end_s` | Where it ends, in s: before the first reflection. |
| `window_shape` | `"tukey"` (default), `"hann"`, `"hamming"` or `"rectangular"`. |
| `taper_fraction` | The fraction of a Tukey window that is taper, half at each edge (Default: 0,25). |
| `excitation` | The [`RectangularPulse`](/phonometry/reference/api/metrology/comparison-calibration/#rectangularpulse) of a direct impulse measurement, divided out of the response (Default: None). |

**Returns:** The [`TimeSelectiveResponse`](/phonometry/reference/api/metrology/comparison-calibration/#timeselectiveresponse).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for what [`TimeSelectiveResponse`](/phonometry/reference/api/metrology/comparison-calibration/#timeselectiveresponse) refuses. |

## TimeSelectiveResponse

```python
TimeSelectiveResponse(
    impulse_response: NDArray[np.float64],
    sample_rate_hz: float,
    window_start_s: float,
    window_end_s: float,
    window_shape: str = 'tukey',
    taper_fraction: float = 0.25,
    excitation: RectangularPulse | None = None,
)
```

The frequency response of the direct sound alone, an impulse response
weighted with a time window and transformed (IEC 61094-8:2012 B.1.3 and
B.2).

The window keeps the samples from `window_start_s` to
`window_end_s`, counted from the start of the record, with tapered
edges, and `response_at` transforms them by Formula (B.2),
$H(f) = \int h(t)\,\mathrm{e}^{-\mathrm{j}2\pi f t}\,\mathrm{d}t$,
at any frequency. With an `excitation`, the transform is divided by
the pulse's, as a pulse that begins at the start of the record.

**Attributes**

| Name | Description |
| :--- | :--- |
| `impulse_response` | The impulse response, sampled. |
| `sample_rate_hz` | Its sample rate, in Hz. |
| `window_start_s` | Where the window begins, in s. |
| `window_end_s` | Where it ends, in s. |
| `window_shape` | `"tukey"`, `"hann"`, `"hamming"` or `"rectangular"`. |
| `taper_fraction` | The fraction of a Tukey window that is taper, half at each edge. |
| `excitation` | The [`RectangularPulse`](/phonometry/reference/api/metrology/comparison-calibration/#rectangularpulse) the response was taken with, divided out, or `None`. |

### TimeSelectiveResponse.free_field_region()

```python
TimeSelectiveResponse.free_field_region(
    source_distance_m: float,
    arrival_time_s: float,
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    relative_humidity_percent: float = 50.0,
) -> FreeFieldRegion
```

The effective free-field region of this window (B.1, Formula
(B.1)), with $\tau$ "the time from the arrival of the sound at
the microphone under test, to the end of the time window".

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_distance_m` | $d$, in m. |
| `arrival_time_s` | When the direct sound reaches the microphone, in s from the start of the record. |
| `temperature_c` | The air temperature, in °C (Default: 23,0). |
| `static_pressure_kpa` | The static pressure, in kPa (Default: 101,325). |
| `relative_humidity_percent` | The relative humidity, in % (Default: 50). |

**Returns:** The [`FreeFieldRegion`](/phonometry/reference/api/metrology/comparison-calibration/#freefieldregion).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an arrival at or after the end of the window, or what [`free_field_region`](/phonometry/reference/api/metrology/comparison-calibration/#free_field_region) refuses. |

### TimeSelectiveResponse.frequency_resolution_hz

*property*

The inverse of the window length, in Hz: the spacing of the
frequencies the window can tell apart, as B.2.2 relates the length of
an impulse response to its frequency step.

### TimeSelectiveResponse.level_db_at()

```python
TimeSelectiveResponse.level_db_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

$20\lg\lvert H(f)\rvert$, in dB re 1 of the response's unit
times a second.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |

**Returns:** The level at each, in dB.

### TimeSelectiveResponse.phase_deg_at()

```python
TimeSelectiveResponse.phase_deg_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

$\arg H(f)$, in degrees, with the time origin at the start of
the record.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |

**Returns:** The phase at each, in degrees.

### TimeSelectiveResponse.plot()

```python
TimeSelectiveResponse.plot(
    ax: Axes | None = None,
    *,
    quantity: str = 'impulse',
    frequencies_hz: ArrayLike | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the impulse response with the window over it, or the level of
$H(f)$ with and without the window.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `quantity` | `"impulse"` (default) or `"response"`. |
| `frequencies_hz` | The frequencies of the response, in Hz (Default: None, 200 from the frequency resolution to a quarter of the sample rate, or, with an `excitation`, to a tenth of the first zero of its spectrum if that is lower, B.6.1). |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the windowed curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown quantity. |

### TimeSelectiveResponse.record_response_at()

```python
TimeSelectiveResponse.record_response_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.complex128]
```

$H(f)$ of the whole record with no window, the reflections
included: what the window takes away, for comparison.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |

**Returns:** $H(f)$ at each.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing. |

### TimeSelectiveResponse.response_at()

```python
TimeSelectiveResponse.response_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.complex128]
```

$H(f)$, Formula (B.2) applied to the windowed response, at
each frequency, complex, in the unit of the response times seconds
(divided by the pulse's spectrum, in V·s, when there is one).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |

**Returns:** $H(f)$ at each.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, or, with an excitation, a frequency at or above the first zero of its spectrum. |

### TimeSelectiveResponse.time_s

*property*

The time of each sample from the start of the record, in s.

### TimeSelectiveResponse.window

*property*

The window at each sample of the record, 0 outside it.

### TimeSelectiveResponse.window_length_s

*property*

How long the window lasts, in s.

### TimeSelectiveResponse.windowed_impulse_response

*property*

The impulse response times the window.
