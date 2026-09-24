---
title: "metrology.free_field_corrections"
description: "Corrections that bring a sound level meter to its free-field response (IEC 62585:2012)."
sidebar:
  label: "free_field_corrections"
---

Corrections that bring a sound level meter to its free-field response
(IEC 62585:2012).

A periodic test of a sound level meter by IEC 61672-3 drives its microphone
with a sound calibrator, a comparison coupler or an electrostatic actuator,
none of which is the plane progressive wave the meter is specified for. The
test needs, at each frequency, the correction that turns what the meter
indicates on that source into what it would indicate in a free field of the
same sound pressure level, and the manufacturer has to state it. IEC 62585
gives the methods for finding those corrections and the uncertainty they may
carry.

**The adjustment value, Annex A.** The manufacturer adjusts the meter's
sensitivity to minimise the averaged deviation of its free-field response from
the incident level over the whole frequency range, then applies the
recommended calibrator and reads $L_4$. The adjustment value quoted in
the manual is $\Delta L = L_1 - L_4$, $L_1$ being the level stated
for the calibrator. [`adjustment_value`](/phonometry/reference/api/metrology/free-field-corrections/#adjustment_value) makes the fit and returns an
[`AdjustmentValue`](/phonometry/reference/api/metrology/free-field-corrections/#adjustmentvalue).

**The corrections, Annexes D, E and F.** Each compares the meter with a
laboratory standard microphone of type LS2P, in a free field and on the
source, and adds the free-field correction of that microphone, which comes
from IEC/TS 61094-7 and is an input here:

$$
C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3}) - (L_\mathrm{ind2} - L_\mathrm{ind4}) - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}) + (L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}) + C_\mathrm{FF,RM} \tag{D.7}
$$

for a multi-frequency sound calibrator ([`sound_calibrator_correction`](/phonometry/reference/api/metrology/free-field-corrections/#sound_calibrator_correction)),
Formula (E.6) for a comparison coupler ([`comparison_coupler_correction`](/phonometry/reference/api/metrology/free-field-corrections/#comparison_coupler_correction)),
and Formula (F.13), normalised to the calibration check frequency, for an
electrostatic actuator ([`electrostatic_actuator_correction`](/phonometry/reference/api/metrology/free-field-corrections/#electrostatic_actuator_correction)). All three
return a [`FreeFieldCorrection`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrection), which averages the determinations of
the combinations clause 7 asks for and keeps their range.

**The uncertainty, Annex I and clauses 9 to 14.**
[`correction_uncertainty_budget`](/phonometry/reference/api/metrology/free-field-corrections/#correction_uncertainty_budget) builds the budget of Table I.1 on
[`combine_uncertainty`](/phonometry/reference/api/metrology/uncertainty/#combine_uncertainty): its 15 components, each
divided by the divisor its distribution sets, and the effective degrees of
freedom by Welch-Satterthwaite, which choose the coverage factor for a level of
confidence of 95 %. [`verify_correction_uncertainty`](/phonometry/reference/api/metrology/free-field-corrections/#verify_correction_uncertainty) judges the expanded
uncertainty at each frequency against the maximum permitted by the clause the
correction belongs to, [`maximum_expanded_uncertainty`](/phonometry/reference/api/metrology/free-field-corrections/#maximum_expanded_uncertainty), and for clauses
12 to 14 the range of the corrections over the microphones against the same
maximum.

**The exact frequencies, Annex H.** The corrections are reported at exact
base-ten frequencies, [`exact_frequencies`](/phonometry/reference/api/metrology/free-field-corrections/#exact_frequencies).

Three readings the text leaves to the implementer
-------------------------------------------------

**The fit of Annex A.** The text asks for the sensitivity that minimises "the
averaged deviation" of the free-field response, with the tolerance limits of
IEC 61672-1, which vary with frequency, "taken into account", and prints no
formula. [`adjustment_value`](/phonometry/reference/api/metrology/free-field-corrections/#adjustment_value) takes the least-squares reading: the
sensitivity adjustment $s$ minimises $\sum_i w_i (d_i + s)^2$,
$d_i$ the deviation at frequency $i$ and $w_i = 1/t_i^2$
for a tolerance $t_i$, so a frequency with a tight tolerance pulls the
fit harder than one with a loose one, and a frequency without a tolerance
($t_i = \infty$) does not pull it at all. Without tolerances every
frequency weighs the same and $s$ is minus the mean deviation.

**The labels of Annex E.** Figure E.1, the list of symbols under (E.6) and the
descriptors a3 and a4 of Table I.1 all define $L_\mathrm{ind3a}$ as the
reading of the reference microphone in the coupler and $L_\mathrm{ind3b}$
as that of the meter, with $L_{p,\mathrm{P1}}$ at the reference and
$L_{p,\mathrm{P2}}$ at the meter. Equations (E.4) to (E.6) are written
the other way round, as (D.5) to (D.7) are for a calibrator, and with the
figure's definitions they do not follow from (E.1) to (E.3B): they come out
$2(\Delta L_\mathrm{P,SLM} - \Delta L_\mathrm{P,RM})$ away from the
correction. [`comparison_coupler_correction`](/phonometry/reference/api/metrology/free-field-corrections/#comparison_coupler_correction) names its inputs by what
each reading is of, so neither labelling reaches it, and the defect is in
`docs/ERRATA.md`.

**The coverage factor of Table I.2.** The budget at 1 kHz reproduces the
printed combined standard uncertainty, 0,0590 dB, and effective degrees of
freedom, 29,98, but prints $k = 2{,}11$, the Student factor for about 17
degrees of freedom. For 29,98 it is 2,04, and the expanded uncertainty
0,120 dB rather than the 0,124 dB the table prints to its guard digit. The
budget here gives 2,04, and the defect is in `docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## adjustment_value

```python
adjustment_value(
    frequencies_hz: ArrayLike,
    free_field_indicated_level_db: ArrayLike,
    calibrator_reading_db: float,
    *,
    calibrator_level_db: float,
    incident_level_db: ArrayLike | None = None,
    tolerance_db: ArrayLike | None = None,
    pressure_indicated_level_db: ArrayLike | None = None,
    check_frequency_hz: float = 1000.0,
) -> AdjustmentValue
```

The adjustment value at the calibration check frequency
(IEC 62585:2012, Annex A).

The free-field response of the meter is measured "with where possible a
measured level equal to the stated level for the recommended sound
calibrator", the sensitivity is adjusted "to minimise the averaged
deviation" of the indication from the incident level over the frequency
range, and the adjusted meter is then exposed to the calibrator:

$$
s = -\frac{\sum_i w_i d_i}{\sum_i w_i}, \qquad \Delta L = L_1 - (L_4' + s)
$$

with $d_i$ the indication less the incident level at each
frequency, $w_i = 1/t_i^2$ for a tolerance $t_i$ (or equal
weights), and $L_4'$ the indication on the calibrator at the
sensitivity the free-field readings were taken at. The least-squares
weighting is this module's reading of a text that prints no formula (see
the module notes). Where the achievable free-field level differs from
$L_1$, `incident_level_db` carries it, which is the allowance the
text asks for.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies of the free-field response, in Hz, increasing, the calibration check frequency among them. |
| `free_field_indicated_level_db` | What the meter indicates in the free field at each frequency, in dB, before the adjustment. |
| `calibrator_reading_db` | $L_4'$, what the meter indicates on the recommended calibrator at the same sensitivity, in dB. |
| `calibrator_level_db` | $L_1$, the level stated for the calibrator at the calibration check frequency, in dB. |
| `incident_level_db` | The incident free-field level at each frequency, in dB, one value or one per frequency (Default: None, the calibrator's $L_1$ at every frequency). |
| `tolerance_db` | The tolerance the deviation is judged against at each frequency, in dB, such as the narrower side of the IEC 61672-1 acceptance limits for the class; one value or one per frequency, and infinite where a frequency should not pull the fit (Default: None, equal weights). |
| `pressure_indicated_level_db` | What the meter indicates in a pressure field of level $L_1$ at each frequency, in dB, before the adjustment, for the pressure-to-free-field correction and $L_3$ (Default: None). |
| `check_frequency_hz` | $f_\mathrm{R}$, in Hz (Default: 1000). |

**Returns:** The [`AdjustmentValue`](/phonometry/reference/api/metrology/free-field-corrections/#adjustmentvalue).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for columns that do not hold one value per frequency, a value that is not finite, a tolerance that is not positive or finite nowhere, or a check frequency that is not among the frequencies. |

## AdjustmentValue

```python
AdjustmentValue(
    frequencies_hz: NDArray[np.float64],
    free_field_deviation_db: NDArray[np.float64],
    calibrator_level_db: float,
    calibrator_reading_db: float,
    check_frequency_hz: float = 1000.0,
    tolerance_db: NDArray[np.float64] | None = None,
    pressure_deviation_db: NDArray[np.float64] | None = None,
)
```

The adjustment value at the calibration check frequency
(IEC 62585:2012, Annex A).

The free-field response of the meter before its sensitivity is adjusted,
the tolerances the fit weighs it with, and what the meter indicates on its
sound calibrator at that same sensitivity. The fit and everything that
follows from it are derived from those, so a result cannot state an
adjustment its own readings do not give. Figure A.1 names the levels at
the calibration check frequency $f_\mathrm{R}$: $L_1$ the
level stated for the calibrator, $L_2$ the indication in a free
field at that level, $L_3$ the indication in a pressure field at
that level, $L_4$ the indication on the calibrator, all after the
adjustment. The manual states $\Delta L = L_1 - L_4$ as a fixed
number, without an uncertainty (clause 8).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | the frequencies of the free-field response, in Hz. |
| `free_field_deviation_db` | $d$, the indication in the free field less the incident level at each frequency, before the adjustment, in dB. |
| `calibrator_level_db` | $L_1$, the level stated for the sound calibrator, in dB. |
| `calibrator_reading_db` | $L_4'$, what the meter indicates on the calibrator before the adjustment, at the sensitivity the free-field readings were taken at, in dB. |
| `check_frequency_hz` | $f_\mathrm{R}$, the calibration check frequency, in Hz: one of `frequencies_hz`. |
| `tolerance_db` | $t$ at each frequency, in dB, infinite where a frequency does not pull the fit; `None` for equal weights. |
| `pressure_deviation_db` | the indication in a pressure field of level $L_1$ less $L_1$ at each frequency, before the adjustment, in dB; `None` when the pressure response was not given. |

### AdjustmentValue.adjusted_deviation_db

*property*

The deviation of the free-field response after the adjustment,
$d + s$, in dB: curve (2) less curve (1) of Figure A.1.

### AdjustmentValue.adjustment_db

*property*

$\Delta L = L_1 - L_4$, in dB: the value the manual states,
added to the indication on the calibrator to obtain its stated level.

### AdjustmentValue.calibrator_indicated_level_db

*property*

$L_4 = L_4' + s$, what the adjusted meter indicates on the
calibrator, in dB.

### AdjustmentValue.check_frequency_offset_db

*property*

$L_2 - L_1$, in dB: the deliberate "offset" NOTE 1 of clause
8 allows at the calibration check frequency, which the fit over the
whole range leaves in the free-field response there.

### AdjustmentValue.free_field_indicated_level_db

*property*

$L_2$, the indication in a free field at $L_1$ and the
calibration check frequency, after the adjustment, in dB.

### AdjustmentValue.plot()

```python
AdjustmentValue.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the free-field deviation before and after the adjustment,
with the tolerances it was weighed against.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the adjusted-response curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### AdjustmentValue.pressure_indicated_level_db

*property*

$L_3$, the indication in a pressure field at $L_1$ and
the calibration check frequency, after the adjustment, in dB; `None`
without the pressure response. $L_3 - L_4$ is what the loading
of the calibrator by the microphone makes of it (NOTE to Figure A.1).

### AdjustmentValue.pressure_to_free_field_correction_db

*property*

The pressure-to-free-field correction of the meter at each
frequency, in dB: the free-field level (1) less the indication in the
pressure field (3), after the adjustment. `None` without the pressure
response.

### AdjustmentValue.sensitivity_adjustment_db

*property*

$s = -\sum_i w_i d_i$, the change of sensitivity the fit
makes, in dB: added to every indication.

### AdjustmentValue.weights

*property*

The weight of each frequency in the fit, $1/t_i^2$
normalised to sum to one; equal without tolerances.

## comparison_coupler_correction

```python
comparison_coupler_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_coupler_level_db: ArrayLike,
    reference_coupler_level_db: ArrayLike,
    *,
    reference_free_field_correction_db: ArrayLike,
    free_field_level_difference_db: ArrayLike = 0.0,
    coupler_level_difference_db: ArrayLike = 0.0,
) -> FreeFieldCorrection
```

Free-field corrections for use with a comparison coupler
(IEC 62585:2012, Annex E, Formula (E.6)).

$$
C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3b}) - (L_\mathrm{ind2} - L_\mathrm{ind3a}) - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}) + (L_{p,\mathrm{P2}} - L_{p,\mathrm{P1}}) + C_\mathrm{FF,RM}
$$

with the symbols of Figure E.1: the meter in a free progressive field
(measurement 1), a type LS2P reference microphone in its place (2), and
both face to face in the two openings of the coupler (3), the reference
reading $L_\mathrm{ind3a}$ at $L_{p,\mathrm{P1}}$ and the meter
$L_\mathrm{ind3b}$ at $L_{p,\mathrm{P2}}$. Formula (E.6) as
printed exchanges the two readings in the coupler (see the module notes);
the inputs here are named by what each reading is of, so the result is
the meter's free-field response relative to its response in the coupler
either way.

Each reading may be one value per frequency or a matrix of one row per
determination; E.2 step 5 asks for three microphones at least, and the
correction is their mean.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `slm_free_field_level_db` | $L_\mathrm{ind1}$, the meter in the free field, in dB. |
| `reference_free_field_level_db` | $L_\mathrm{ind2}$, the reference microphone in the same field, in dB. |
| `slm_coupler_level_db` | the meter in the coupler, in dB ($L_\mathrm{ind3b}$ of Figure E.1). |
| `reference_coupler_level_db` | the reference microphone in the coupler, in dB ($L_\mathrm{ind3a}$ of Figure E.1). |
| `reference_free_field_correction_db` | $C_\mathrm{FF,RM}$ from IEC/TS 61094-7, in dB, one per frequency or one for all. |
| `free_field_level_difference_db` | $L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}$, the free-field level during measurement 1 less that during measurement 2, in dB (Default: 0; NOTE 2). |
| `coupler_level_difference_db` | the sound pressure level at the meter less that at the reference in the coupler, in dB (Default: 0). |

**Returns:** The [`FreeFieldCorrection`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | as [`sound_calibrator_correction`](/phonometry/reference/api/metrology/free-field-corrections/#sound_calibrator_correction). |

## correction_uncertainty_budget

```python
correction_uncertainty_budget(
    values_db: Mapping[str, float],
    *,
    repeatability_dof: float,
    frequency_hz: float,
    correction_db: float = 0.0,
    static_pressure_kpa: float | None = None,
    additional_components: Sequence[Quantity] = (),
    coverage: float = 0.95,
) -> CorrectionUncertaintyBudget
```

The uncertainty budget of a correction with the 15 components of Table
I.1 (IEC 62585:2012, Annex I).

Each component is given as Table I.2 prints it in its "Value" column: the
half-width of a rectangular distribution for most, the expanded
uncertainty ($k = 2$) from IEC/TS 61094-7 for the free-field
correction of the reference microphone (a7), and the standard uncertainty
from repeated measurements for the repeatability (a15). The divisors of
Table I.1, $\sqrt{3}$, 2 and 1, turn them into standard
uncertainties; the combination is
[`combine_uncertainty`](/phonometry/reference/api/metrology/uncertainty/#combine_uncertainty) on Formula (E.6), every
component a correction with a sensitivity of $\pm 1$; the effective
degrees of freedom are Welch-Satterthwaite's, with only the repeatability
finite; and the coverage factor is the Student factor for them at a level
of confidence of 95 % (clause 5).

Table I.2 at 1 kHz gives $u_\mathrm{c} = 0{,}0590$ dB and
$\nu_\mathrm{eff} = 29{,}98$, so $k = 2{,}04$ and
$U = 0{,}12$ dB (the table prints $k = 2{,}11$, an erratum;
see the module notes); Table I.3 at 8 kHz gives $u_\mathrm{c} = 0{,}140$ dB, $k = 2{,}00$ and $U = 0{,}28$ dB.

Table I.1 is written for the comparison coupler of Annex E. The budget of
a calibrator (Annex D) has the same 15 components with the readings on the
calibrator in place of those in the coupler; one of an actuator (Annex F)
adds its own, which `additional_components` carries.

**Parameters**

| Name | Description |
| :--- | :--- |
| `values_db` | The value of each of the 15 components, in dB, keyed by the descriptor of Table I.1, `"a1"` to `"a15"`. A component taken as negligible is given as 0, as Table I.2 gives a6 and a13. |
| `repeatability_dof` | The degrees of freedom of the repeatability (a15), from the number of repeat measurements: 2 in Tables I.2 and I.3. |
| `frequency_hz` | The frequency, in Hz, which sets the clause 6 component and the maximum the budget is judged against. |
| `correction_db` | The correction the budget is for, in dB (Default: 0). |
| `static_pressure_kpa` | The static pressure the measurements were made at, in kPa (Default: None). Below 97 kPa clause 6 adds a component of expanded uncertainty 0,15 dB up to 3 kHz and 0,25 dB above ($k = 2$); outside 80 kPa to 105 kPa it refuses. |
| `additional_components` | Further components the laboratory's own method needs, as [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) objects of estimate 0 and sensitivity 1, named (Default: none). |
| `coverage` | The level of confidence (Default: 0,95, clause 5). |

**Returns:** The [`CorrectionUncertaintyBudget`](/phonometry/reference/api/metrology/free-field-corrections/#correctionuncertaintybudget).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a set of components that is not the 15 of Table I.1, a value that is negative or not finite, degrees of freedom that are not positive, or a static pressure outside clause 6. |

## CorrectionUncertaintyBudget

```python
CorrectionUncertaintyBudget(
    frequency_hz: float,
    descriptors: tuple[str, ...],
    symbols: tuple[str, ...],
    values_db: NDArray[np.float64],
    divisors: NDArray[np.float64],
    dofs: NDArray[np.float64],
    uncertainty: UncertaintyResult,
    coverage: float = 0.95,
)
```

The uncertainty budget of a correction at one frequency
(IEC 62585:2012, Annex I, Tables I.1 to I.3).

One entry per component, in the order of Table I.1 and then any
component the laboratory adds: the value the budget states, the divisor
that turns it into a standard uncertainty $u_i$, and its degrees of
freedom. The combination is the law of propagation of the GUM, with every
component entering Formula (E.6) with a sensitivity of $\pm 1$, and
the coverage factor the Student factor for the Welch-Satterthwaite
effective degrees of freedom at the stated level of confidence.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | the frequency, in Hz. |
| `descriptors` | `"a1"` to `"a15"`, then `"static pressure"` when clause 6 adds it, then the names of any further components. |
| `symbols` | the symbol or name of each component. |
| `values_db` | the value each component is stated as, in dB: a half-width, an expanded uncertainty or a standard uncertainty, as its divisor says. |
| `divisors` | the divisor of each component. |
| `dofs` | the degrees of freedom of each component (`inf` for a Type B estimate). |
| `uncertainty` | the [`UncertaintyResult`](/phonometry/reference/api/metrology/uncertainty/#uncertaintyresult) of the combination. |
| `coverage` | the level of confidence, 0,95 by clause 5. |

### CorrectionUncertaintyBudget.combined_uncertainty_db

*property*

$u(C_\mathrm{FF,SLM})$, the combined standard uncertainty,
in dB.

### CorrectionUncertaintyBudget.correction_db

*property*

The correction the budget is for, in dB (0 when not given).

### CorrectionUncertaintyBudget.coverage_factor

*property*

$k$, the Student factor for the effective degrees of freedom
at `coverage`.

### CorrectionUncertaintyBudget.effective_dof

*property*

The Welch-Satterthwaite effective degrees of freedom,
$u_\mathrm{c}^4 / \sum_i u_i^4/\nu_i$.

### CorrectionUncertaintyBudget.expanded_uncertainty_db

*property*

$U = k\,u_\mathrm{c}$, in dB.

### CorrectionUncertaintyBudget.plot()

```python
CorrectionUncertaintyBudget.plot(
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

### CorrectionUncertaintyBudget.standard_uncertainties_db

*property*

$u_i$, each value over its divisor, in dB.

## CorrectionUncertaintyVerification

```python
CorrectionUncertaintyVerification(
    clause: int,
    frequencies_hz: NDArray[np.float64],
    expanded_uncertainty_db: NDArray[np.float64],
    maximum_uncertainty_db: NDArray[np.float64],
    correction_db: NDArray[np.float64] | None = None,
    coverage_factor: NDArray[np.float64] | None = None,
    correction_range_db: NDArray[np.float64] | None = None,
)
```

The expanded uncertainties of a set of corrections against the maxima
of their clause (IEC 62585:2012, clauses 5 and 9 to 14).

Clause 5: "If the actual expanded uncertainty of measurement exceeds any
of the maximum permitted values, the measurement shall not be used to
evaluate the corrections provided in the instruction manual." Clauses 12
to 14 add a second requirement on the microphone: when the range of the
corrections measured with three microphones exceeds the maximum permitted
expanded uncertainty at a frequency, the microphone is unsuitable for the
source unless more samples show otherwise. Both are "shall not exceed", so
a value equal to its maximum passes.

**Attributes**

| Name | Description |
| :--- | :--- |
| `clause` | the clause, 9 to 14. |
| `frequencies_hz` | the frequencies, in Hz. |
| `expanded_uncertainty_db` | the actual expanded uncertainty at each frequency, in dB. |
| `maximum_uncertainty_db` | the maximum permitted at each frequency, in dB. |
| `correction_db` | the corrections, in dB, which the documentation of clause 15 states with their uncertainty; `None` if not given. |
| `coverage_factor` | the coverage factor of each expanded uncertainty, which clause 15 asks to be stated; `None` if not given. |
| `correction_range_db` | the range of the corrections over the microphones at each frequency, in dB (clauses 12 to 14); `None` if not given. |

### CorrectionUncertaintyVerification.failing_frequencies_hz

*property*

The frequencies where either requirement fails, in Hz.

### CorrectionUncertaintyVerification.margin_db

*property*

The maximum less the expanded uncertainty at each frequency, in dB:
negative where it fails.

### CorrectionUncertaintyVerification.passes

*property*

Whether every expanded uncertainty, and every range when given, is
within the maximum of the clause.

True says the measurement may be used for the corrections in the
manual and, for clauses 12 to 14 with a range, that the microphone is
suitable for the source. It says nothing of whether the corrections
conform to IEC 61672-1, which clause 15 p) asks separately.

### CorrectionUncertaintyVerification.plot()

```python
CorrectionUncertaintyVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the expanded uncertainty and the range against the maximum of
the clause.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the expanded-uncertainty curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### CorrectionUncertaintyVerification.range_passes

*property*

Whether the range of the corrections is within the maximum,
frequency by frequency; `None` when no range was given.

### CorrectionUncertaintyVerification.report()

```python
CorrectionUncertaintyVerification.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the documentation of clause 15 n) and o) to a PDF.

One page: the standard-basis line, an optional metadata header, the
table of the corrections with their expanded uncertainty, coverage
factor, maximum and verdict at each frequency beside the plot, and
the boxed statement of whether the uncertainties are within the
maximum permitted values.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata); `None` produces a bare fiche. |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | Accepted for a uniform signature; it has no effect. |
| `language` | Fiche language: `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"`. |
| ImportError | If reportlab is not installed (`pip install phonometry[report]`), or matplotlib is missing for the embedded figure (`pip install phonometry[plot]`). |

### CorrectionUncertaintyVerification.subject

*property*

What the clause corrects for, in the words of its title.

### CorrectionUncertaintyVerification.uncertainty_passes

*property*

Whether the expanded uncertainty is within the maximum, frequency
by frequency.

## electrostatic_actuator_correction

```python
electrostatic_actuator_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_actuator_level_db: ArrayLike,
    *,
    reference_sensitivity_level_db: ArrayLike,
    reference_channel_gain_db: ArrayLike = 0.0,
    actuator_level_db: ArrayLike = 0.0,
    free_field_level_difference_db: ArrayLike = 0.0,
    check_frequency_hz: float = 1000.0,
) -> FreeFieldCorrection
```

Free-field corrections, normalised to the calibration check frequency,
for use with an electrostatic actuator (IEC 62585:2012, Annex F,
Formula (F.13)).

$$
C_\mathrm{N,FF,SLM} = R_\mathrm{N,ind1} - R_\mathrm{N,ind2} - (R_\mathrm{N,p,F1} - R_\mathrm{N,p,F2}) + S_\mathrm{N,RM} + G_\mathrm{N,RC} - (R_\mathrm{N,ind3} - R_\mathrm{N,EA})
$$

every term $X_\mathrm{N} = X(f) - X(f_0)$ normalised to the
calibration check frequency $f_0$ (Formulas (F.5) to (F.12)). Three
measurements (Figure F.1): the meter in a free progressive field (1), a
type LS2P reference microphone of known free-field sensitivity in its
place (2), and the actuator on the meter (3). An actuator is not an
absolute source (NOTE 4 to 3.4), so the correction is relative to
$f_0$, where it is zero, and the absolute response there comes from
a sound calibrator (NOTE 2 of F.2).

Each reading may be one value per frequency or a matrix of one row per
determination; F.2 step 5 averages the combinations of microphone and
actuator clause 7 asks for.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing, $f_0$ among them. |
| `slm_free_field_level_db` | $L_\mathrm{ind1}(f)$, the meter in the free field, in dB. |
| `reference_free_field_level_db` | $L_\mathrm{ind2}(f)$, the reference channel in the same field, in dB. |
| `slm_actuator_level_db` | $L_\mathrm{ind3}(f)$, the meter on the actuator, in dB. |
| `reference_sensitivity_level_db` | $S_\mathrm{RM}(f)$, the free-field (open-circuit) sensitivity level of the reference microphone, in dB re 1 V/Pa, one per frequency. |
| `reference_channel_gain_db` | $G_\mathrm{RC}(f)$, the gain of the reference channel, in dB (Default: 0, a flat channel). Its frequency response has to be known; its absolute gain does not. |
| `actuator_level_db` | $L_\mathrm{EA}(f)$, the level the actuator simulates, in dB (Default: 0 at every frequency: the same at $f$ and $f_0$ for a drive voltage independent of frequency, NOTE 4). |
| `free_field_level_difference_db` | $L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}$ at each frequency, in dB (Default: 0; NOTE 3). |
| `check_frequency_hz` | $f_0$, in Hz (Default: 1000). |

**Returns:** The [`FreeFieldCorrection`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrection), zero at $f_0$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | as [`sound_calibrator_correction`](/phonometry/reference/api/metrology/free-field-corrections/#sound_calibrator_correction), or for an $f_0$ that is not among the frequencies. |

## exact_frequencies

```python
exact_frequencies(
    lowest_hz: float,
    highest_hz: float,
    *,
    fraction: int = 12,
) -> NDArray[np.float64]
```

The exact base-ten frequencies between two limits (IEC 62585:2012,
Annex H, Formula (H.1)).

$$
f_x = f_\mathrm{r}\, 10^{3x/(10b)}
$$

for every integer $x$, with $f_\mathrm{r} = 1000$ Hz and the
step-width designator $b$. Annex H gives it for $b = 12$,
one-twelfth-octave steps, whose decade from 1 kHz to 10 kHz Table H.1
prints to seven significant digits; they are the band edges of
one-twelfth-octave filters, so 1 kHz and every one-third-octave midband
frequency are among them. Clauses 10 and 12 to 14 and Annexes B and C
report the corrections at these exact frequencies rather than at the
nominal ones. $b = 1$ gives the exact octave midband frequencies
clause 10 measures a microphone at, and $b = 3$ the one-third-octave
ones.

**Parameters**

| Name | Description |
| :--- | :--- |
| `lowest_hz` | The lowest frequency wanted, in Hz. |
| `highest_hz` | The highest frequency wanted, in Hz, not below `lowest_hz`. |
| `fraction` | The step-width designator $b$ (Default: 12). |

**Returns:** Every exact frequency from `lowest_hz` to `highest_hz` inclusive, in Hz, increasing and read-only. It may be empty when the range is narrower than a step.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a limit that is not positive and finite, limits in the wrong order, or a designator that is not a whole number of at least one. |

## FreeFieldCorrection

```python
FreeFieldCorrection(
    frequencies_hz: NDArray[np.float64],
    corrections_db: NDArray[np.float64],
    reference_correction_db: NDArray[np.float64],
    source: str,
    check_frequency_hz: float | None = None,
)
```

The corrections that bring a meter on a source to its free-field
response (IEC 62585:2012, Formulas (D.7), (E.6) and (F.13)).

One row of `corrections_db` per determination, one combination of
microphone and source, and one column per frequency. The correction the
manual states is their mean at each frequency (D.2 step 6, E.2 step 5,
F.2 step 5); clauses 12 to 14 judge the range over the microphones
against the maximum permitted expanded uncertainty.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | the frequencies, in Hz. |
| `corrections_db` | $C_\mathrm{FF,SLM}$, or $C_\mathrm{N,FF,SLM}$ for an actuator, of each determination, in dB, shape `(determinations, frequencies)`. |
| `reference_correction_db` | what the reference microphone contributes at each frequency, in dB: $C_\mathrm{FF,RM}$ for a calibrator or a coupler, $S_\mathrm{N,RM} + G_\mathrm{N,RC}$ for an actuator. |
| `source` | `"sound_calibrator"` (Annex D), `"comparison_coupler"` (Annex E) or `"electrostatic_actuator"` (Annex F). |
| `check_frequency_hz` | the normalisation frequency $f_0$ of an actuator's corrections, in Hz; `None` for the other two sources, whose corrections are absolute. |

### FreeFieldCorrection.clause

*property*

The clause whose maximum uncertainty the correction is judged
against: 12, 13 or 14.

### FreeFieldCorrection.correction_db

*property*

The mean correction over the determinations at each frequency, in
dB: the value the manual states.

### FreeFieldCorrection.determinations

*property*

The number of determinations averaged.

### FreeFieldCorrection.formula

*property*

The formula applied: `"D.7"`, `"E.6"` or `"F.13"`.

### FreeFieldCorrection.plot()

```python
FreeFieldCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the correction against frequency, with every determination
and the range between them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mean-correction curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### FreeFieldCorrection.range_db

*property*

The range of the determinations at each frequency, largest less
smallest, in dB; zero for a single determination.

## IEC62585_TABLE_I1

*Constant* (`mapping`).

## maximum_expanded_uncertainty

```python
maximum_expanded_uncertainty(
    frequencies_hz: ArrayLike,
    *,
    clause: int,
) -> NDArray[np.float64]
```

The maximum permitted expanded uncertainty of a correction
(IEC 62585:2012, clauses 9 to 14).

====== ========================================== =========================
Clause Correction for                             Maximum, dB
====== ========================================== =========================
9      reflections from the case, diffraction     0,25 to 4 kHz; 0,35 above
10     the microphone's non-uniform response      0,25 from 63 Hz to 4 kHz;
                                                  0,35 to 8 kHz; 0,45 above
11     windscreens and similar accessories        0,20 to 4 kHz; 0,30 above
12-14  a calibrator, a coupler, an actuator       0,25 to 4 kHz; 0,35 below
                                                  10 kHz; 0,50 from 10 kHz
====== ========================================== =========================

"To 4 kHz" includes 4 kHz; 10 kHz is in the band "at and above 10 kHz".
Clauses 10 and 11 exclude the reproducibility component of the samples of
microphone or accessory. A frequency within 2 % of a boundary is read as
it, so the exact base-ten frequencies of Annex H fall where their nominal
ones do.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `clause` | The clause, 9 to 14. |

**Returns:** The maximum at each frequency, in dB, read-only.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for another clause, a frequency that is not positive and finite, or, for clause 10, a frequency below 63 Hz. |

## sound_calibrator_correction

```python
sound_calibrator_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_calibrator_level_db: ArrayLike,
    reference_calibrator_level_db: ArrayLike,
    *,
    reference_free_field_correction_db: ArrayLike,
    free_field_level_difference_db: ArrayLike = 0.0,
    calibrator_level_difference_db: ArrayLike = 0.0,
) -> FreeFieldCorrection
```

Free-field corrections for use with a multi-frequency sound calibrator
(IEC 62585:2012, Annex D, Formula (D.7)).

$$
C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3}) - (L_\mathrm{ind2} - L_\mathrm{ind4}) - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}) + (L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}) + C_\mathrm{FF,RM}
$$

Four measurements (Figure D.1): the meter in a free progressive field
(1), a type LS2P reference microphone in its place in the same field (2),
the calibrator on the meter (3) and the same calibrator on the reference
(4). Neither the meter nor the calibrator has to be calibrated absolutely:
the result is the meter's free-field response relative to its response on
the calibrator, carried over from the reference microphone's known
free-field correction.

Each reading may be one value per frequency or a matrix of one row per
determination; D.2 step 6 asks for at least nine, three microphones on
three calibrators, and the correction is their mean.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `slm_free_field_level_db` | $L_\mathrm{ind1}$, the meter in the free field, in dB. |
| `reference_free_field_level_db` | $L_\mathrm{ind2}$, the reference microphone in the same field, in dB. |
| `slm_calibrator_level_db` | $L_\mathrm{ind3}$, the meter on the calibrator, in dB. |
| `reference_calibrator_level_db` | $L_\mathrm{ind4}$, the reference microphone on the calibrator, in dB. |
| `reference_free_field_correction_db` | $C_\mathrm{FF,RM}$, the free-field correction of the reference microphone from IEC/TS 61094-7, in dB, one per frequency or one for all. |
| `free_field_level_difference_db` | $L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}$, the free-field level during measurement 1 less that during measurement 2, from a monitor microphone, in dB (Default: 0, a stable source; NOTE 2). |
| `calibrator_level_difference_db` | $L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}$, the calibrator's level on the meter less that on the reference, in dB (Default: 0, a stable calibrator; NOTE 3). |

**Returns:** The [`FreeFieldCorrection`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a reading that is not finite, a column count that is not the number of frequencies, or readings with different numbers of determinations. |

## UncertaintyComponentRow

```python
UncertaintyComponentRow(
    symbol: str,
    description: str,
    distribution: str,
    divisor: float,
)
```

One row of IEC 62585:2012 Table I.1, the likely components of the
uncertainty of a correction measured with a comparison coupler (Annex E).

**Attributes**

| Name | Description |
| :--- | :--- |
| `symbol` | The symbol or name the table prints, such as `"L_ind1"` or `"Gain of SLM"`. |
| `description` | The description and source of the component. |
| `distribution` | `"rectangular"` or `"normal"`. |
| `divisor` | What turns the value the budget states into a standard uncertainty: $\sqrt{3}$ for a rectangular half-width, 2 for a normal expanded uncertainty with $k = 2$, 1 for a normal standard uncertainty from a statistical evaluation. |

## verify_correction_uncertainty

```python
verify_correction_uncertainty(
    frequencies_hz: ArrayLike,
    expanded_uncertainty_db: ArrayLike,
    *,
    clause: int,
    correction_db: ArrayLike | None = None,
    coverage_factor: ArrayLike | None = None,
    correction_range_db: ArrayLike | None = None,
) -> CorrectionUncertaintyVerification
```

Verify the expanded uncertainties of a set of corrections against the
maxima of their clause (IEC 62585:2012, clauses 5 and 9 to 14).

The actual expanded uncertainty at each frequency, at a level of
confidence of 95 % with the coverage factor stated (clause 5), has not to
exceed [`maximum_expanded_uncertainty`](/phonometry/reference/api/metrology/free-field-corrections/#maximum_expanded_uncertainty) of the clause; for a
calibrator, a coupler or an actuator (clauses 12 to 14) the range of the
corrections over three microphones has not to exceed it either. A
[`FreeFieldCorrection`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrection) knows its clause, [`clause`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrectionclause),
and its range, [`range_db`](/phonometry/reference/api/metrology/free-field-corrections/#freefieldcorrectionrange_db); a
[`CorrectionUncertaintyBudget`](/phonometry/reference/api/metrology/free-field-corrections/#correctionuncertaintybudget) per frequency gives the expanded
uncertainty and the coverage factor.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `expanded_uncertainty_db` | The actual expanded uncertainty at each frequency, in dB, one value or one per frequency. |
| `clause` | The clause the corrections belong to: 9 (case and diffraction), 10 (microphone response), 11 (windscreens and accessories), 12 (sound calibrator), 13 (comparison coupler) or 14 (electrostatic actuator). |
| `correction_db` | The corrections, in dB, for the documentation of clause 15 (Default: None). |
| `coverage_factor` | The coverage factor of each expanded uncertainty, for the same documentation (Default: None). |
| `correction_range_db` | The range of the corrections over the microphones at each frequency, in dB, clauses 12 to 14 only (Default: None, not judged). |

**Returns:** The [`CorrectionUncertaintyVerification`](/phonometry/reference/api/metrology/free-field-corrections/#correctionuncertaintyverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown clause, columns that do not hold one value per frequency, a negative uncertainty or range, a range for clauses 9 to 11, or a frequency below 63 Hz for clause 10. |
