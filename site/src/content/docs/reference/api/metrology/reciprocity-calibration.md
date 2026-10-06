---
title: "metrology.reciprocity_calibration"
description: "Primary calibration of laboratory standard microphones by reciprocity: the sensitivities that come out of three pair measurements, and the uncertainty budget that goes with them (IEC 61094-2:2009 clause 5.7 and clause 7, IEC 61094-3:2016 clause 5.7 and clause 7)."
sidebar:
  label: "reciprocity_calibration"
---

Primary calibration of laboratory standard microphones by reciprocity: the
sensitivities that come out of three pair measurements, and the uncertainty
budget that goes with them (IEC 61094-2:2009 clause 5.7 and clause 7, IEC
61094-3:2016 clause 5.7 and clause 7).

A reciprocity calibration needs no reference microphone. Two microphones are
coupled acoustically, one drives and the other receives, and the electrical
transfer impedance $Z_\mathrm{e,12} = U_2/i_1$ that is measured is the
product of their two sensitivities times the acoustic transfer impedance of
whatever couples them, which is computed:

$$
M_1 M_2 = \frac{Z_\mathrm{e,12}}{Z_\mathrm{a,12}}
$$

In a coupler (IEC 61094-2) $Z_\mathrm{a,12}$ is the acoustic impedance
of the enclosed gas, worked out in
[`reciprocity_coupler`](/phonometry/reference/api/metrology/reciprocity-coupler/); in a free field (IEC
61094-3) it is that of a spherical wave between the two acoustic centres,
worked out in [`reciprocity_free_field`](/phonometry/reference/api/metrology/reciprocity-free-field/). Either way
three pairs taken from three microphones give three products, and each
sensitivity follows from them alone:

$$
M_1 = \left(\frac{P_{12}\,P_{31}}{P_{23}}\right)^{1/2}, \qquad M_2 = \frac{P_{12}}{M_1}, \qquad M_3 = \frac{P_{31}}{M_1}
$$

which is Formula (7) of IEC 61094-2 and Formula (8) of IEC 61094-3. With two
microphones and an auxiliary sound source, the ratio $r_{12} = M_1/M_2$ measured against the source replaces the third pair (Formula (8) of
the first part, Formula (9) of the second): $M_1 = (r_{12}\,P_{12})^{1/2}$.

**The sign of a square root.** Reciprocity fixes the products, and a product
does not change when every sensitivity changes sign together, so no
measurement of this kind can tell $M$ from $-M$. Both parts ask
for the phase to be referred to the full four-quadrant range, 0 to
$2\pi$ (5.7.1 of each: a NOTE in IEC 61094-2, the running text in IEC
61094-3); the library takes the square root on
the branch that is continuous in frequency and has a non-negative real part at
the lowest frequency, then fixes the other two microphones by the products, so
that the three are consistent with every product at every frequency. The
modulus does not depend on the choice.

**Uncertainty.** Both parts list the components of a calibration in their
Table 1 ([`IEC61094_2_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_2_table_1), [`IEC61094_3_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_3_table_1)) and ask for
each as a standard uncertainty as a function of frequency, in linear or
logarithmic form (7.5 of the first part, 7.8 of the second).
[`reciprocity_uncertainty_budget`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocity_uncertainty_budget) combines them in quadrature at each
frequency and multiplies by the coverage factor: $k = 2$ in IEC 61094-2
7.5, and the factor for a 95 % coverage probability in IEC 61094-3 7.8, which
is 2 for a combination dominated by many comparable components. The
components the acoustic transfer impedance contributes are found, as both
parts describe, by "repeating a calculation while the various components are
changed one at a time by their associated uncertainty":
[`coupler_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_parameter_uncertainty) and
[`free_field_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_parameter_uncertainty) do that.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## IEC61094_2_TABLE_1

*Constant* (`mapping`).

## IEC61094_3_TABLE_1

*Constant* (`mapping`).

## reciprocity_uncertainty_budget

```python
reciprocity_uncertainty_budget(
    frequencies_hz: ArrayLike,
    standard_uncertainties_db: Mapping[str, ArrayLike],
    *,
    field: str = 'pressure',
    additional_components_db: Mapping[str, ArrayLike] | None = None,
    coverage_factor: float = 2.0,
) -> ReciprocityUncertaintyBudget
```

The uncertainty budget of a reciprocity calibration (IEC 61094-2:2009
7.5, IEC 61094-3:2016 7.8).

Each component is the standard uncertainty of the sensitivity level it
causes, in dB, one value or one per frequency, keyed by the names of the
field's Table 1 ([`IEC61094_2_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_2_table_1), [`IEC61094_3_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_3_table_1)).
Neither table is exhaustive ("Not all of the components may be relevant in
a given calibration setup"), so a component may be left out and
`additional_components_db` adds others. The components that come from
the acoustic transfer impedance are what
[`coupler_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_parameter_uncertainty) and
[`free_field_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_parameter_uncertainty) return,
keyed the same way.

The combination is the root-sum-square at each frequency; the expanded
uncertainty is $k$ times it, with $k = 2$ as IEC 61094-2 7.5
states. IEC 61094-3 7.8 asks for the factor of a 95 % coverage
probability, which is 2 for a budget of many comparable components; a
caller whose budget is dominated by one component with few degrees of
freedom passes its own.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `standard_uncertainties_db` | The components, keyed by name, each a standard uncertainty in dB, one value or one per frequency. |
| `field` | `"pressure"` (default) or `"free_field"`. |
| `additional_components_db` | Further components, by name, in the same form (Default: none). |
| `coverage_factor` | $k$ (Default: 2). |

**Returns:** The [`ReciprocityUncertaintyBudget`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocityuncertaintybudget).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a key that is not in the field's Table 1, an additional component with the name of another, no component at all, or a value that is negative or not finite. |

## ReciprocityCalibration

```python
ReciprocityCalibration(
    frequencies_hz: NDArray[np.float64],
    sensitivity_v_per_pa: NDArray[np.complex128],
    products_v2_per_pa2: NDArray[np.complex128],
    field: str,
    method: str,
    corrections_db: Mapping[str, NDArray[np.float64]],
    expanded_uncertainty_db: NDArray[np.float64] | None = None,
)
```

The complex sensitivities of microphones calibrated by reciprocity
(IEC 61094-2:2009 5.7 in a coupler, IEC 61094-3:2016 5.7 in a free field).

Built by [`pressure_reciprocity`](/phonometry/reference/api/metrology/reciprocity-coupler/#pressure_reciprocity),
[`pressure_reciprocity_pair`](/phonometry/reference/api/metrology/reciprocity-coupler/#pressure_reciprocity_pair),
[`free_field_reciprocity`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_reciprocity) and
[`free_field_reciprocity_pair`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_reciprocity_pair).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `sensitivity_v_per_pa` | The complex sensitivity of each microphone, one row per microphone, in V/Pa: the pressure sensitivity $M_\mathrm{p}$ in a coupler, the free-field sensitivity $M_\mathrm{f}$ in a free field. |
| `products_v2_per_pa2` | The product of the two sensitivities of each pair, one row per pair (12, 23, 31 in the three-microphone method, 12 alone with an auxiliary source), in V²/Pa². |
| `field` | `"pressure"` (IEC 61094-2) or `"free_field"` (IEC 61094-3). |
| `method` | `"three_microphones"` or `"auxiliary_source"`. |
| `corrections_db` | Corrections added to every microphone's sensitivity level, by name, in dB at each frequency: the wave-motion correction of IEC 61094-2 Table C.3 for a large-volume coupler, say. |
| `expanded_uncertainty_db` | The expanded uncertainty of the sensitivity level at each frequency, in dB, or `None`. |

### ReciprocityCalibration.correction_db

*property*

$\sum_j C_j$, the corrections added to every level, in dB.

### ReciprocityCalibration.microphones

*property*

The number of microphones calibrated: 3, or 2 with a source.

### ReciprocityCalibration.phase_deg

*property*

The phase of each sensitivity, in degrees from 0 to 360 (5.7.1 of
both parts: a NOTE in IEC 61094-2, the running text in IEC 61094-3).

### ReciprocityCalibration.plot()

```python
ReciprocityCalibration.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the sensitivity level of each microphone against frequency,
with the expanded uncertainty as a band when it is known.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of the first microphone. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### ReciprocityCalibration.sensitivity_level_db

*property*

$20\lg(|M|/1\,\mathrm{V/Pa}) + \sum_j C_j$, one row per
microphone, in dB re 1 V/Pa.

### ReciprocityCalibration.sensitivity_mv_per_pa

*property*

The modulus of each sensitivity with the corrections, in mV/Pa.

### ReciprocityCalibration.standard

*property*

The designation the calibration follows.

## ReciprocityUncertaintyBudget

```python
ReciprocityUncertaintyBudget(
    frequencies_hz: NDArray[np.float64],
    field: str,
    names: tuple[str, ...],
    components: tuple[str, ...],
    standard_uncertainties_db: NDArray[np.float64],
    coverage_factor: float = 2.0,
)
```

The uncertainty budget of a reciprocity calibration as a function of
frequency (IEC 61094-2:2009 7.5 and Table 1, IEC 61094-3:2016 7.8 and
Table 1).

Every component is a standard uncertainty of the sensitivity level in dB at
each frequency; they are combined in quadrature and multiplied by the
coverage factor.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `field` | `"pressure"` (IEC 61094-2) or `"free_field"` (IEC 61094-3). |
| `names` | The key of each component, those of the field's Table 1 in its order, then any additional ones. |
| `components` | The component as the table prints it, or the name of an additional one. |
| `standard_uncertainties_db` | $u_i(f)$, one row per component, in dB. |
| `coverage_factor` | $k$. |

### ReciprocityUncertaintyBudget.combined_uncertainty_db

*property*

$u_\mathrm{c}(f) = (\sum_i u_i^2)^{1/2}$, in dB.

### ReciprocityUncertaintyBudget.expanded_uncertainty_db

*property*

$U(f) = k\,u_\mathrm{c}(f)$, in dB.

### ReciprocityUncertaintyBudget.linear_combined_uncertainty_db

*property*

$u_\mathrm{c}$ combined in linear form, in dB.

Each component converted to a relative uncertainty
$r_i = 10^{u_i/20} - 1$, combined in quadrature and converted
back by $20\lg(1 + r_\mathrm{c})$: the linear form 7.5 of the first
part and 7.8 of the second prefer, while accepting the logarithmic one
"as the values are very small".

### ReciprocityUncertaintyBudget.plot()

```python
ReciprocityUncertaintyBudget.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each standard uncertainty and the expanded uncertainty against
frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the expanded-uncertainty curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### ReciprocityUncertaintyBudget.standard

*property*

The designation whose Table 1 the budget follows.

## ReciprocityUncertaintyRow

```python
ReciprocityUncertaintyRow(
    component: str,
    group: str,
    subclauses: tuple[str, ...] = (),
)
```

One row of Table 1 of IEC 61094-2:2009 or IEC 61094-3:2016,
"Uncertainty components".

**Attributes**

| Name | Description |
| :--- | :--- |
| `component` | The measured quantity as the table prints it. |
| `group` | The heading the table lists it under. |
| `subclauses` | The subclauses or annexes the table refers it to; empty where the table prints none. |
