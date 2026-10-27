---
title: "building.measurement.uncertainty"
description: "Measurement uncertainty in building acoustics (ISO 12999-1:2020)."
sidebar:
  label: "uncertainty"
---

Measurement uncertainty in building acoustics (ISO 12999-1:2020).

This module supplies the **measurement uncertainty** of the sound-insulation
quantities produced by the field/lab/prediction modules
([`phonometry.building.measurement.insulation`](/phonometry/reference/api/building/insulation/), [`phonometry.building.measurement.laboratory_insulation`](/phonometry/reference/api/building/laboratory-insulation/),
[`phonometry.building.prediction.simplified_model`](/phonometry/reference/api/building/simplified-model/)). ISO 12999-1 does not re-measure anything;
it tabulates *standard uncertainties* `u` derived from inter-laboratory tests
(ISO 5725) and prescribes how to expand and combine them.

**Three measurement situations (Clause 5.2)** fix which standard deviation is the
standard uncertainty `u`:

- **A**: laboratory characterisation (ISO 10140); `u` = reproducibility `σR`.
- **B**: same location, different teams; `u` = in-situ `σsitu`.
- **C**: same location, same operator/equipment repeated; `u` = repeatability `σr`.

**Tabulated standard uncertainties** (one-third-octave and single-number):

- Airborne `R`/`R'`/`Dn`/`DnT`: Table 2 (bands) and Table 3 (ratings).
- Impact `Ln`/`L'n`/`L'nT`: Table 4 (bands, situations B/C only) and Table 5
  (ratings). ISO 12999-1:2020 Table 4 has **no 500 Hz band** (the 2014 edition did).
- Reduction of impact noise by floor coverings `ΔL`/`ΔLw`: Table 6 (bands) and
  Table 7 (rating), situation A only.
- Upper 95 % limit of airborne reproducibility `σR95`: Annex D Tables D.1/D.2
  (situation A; informative). In ISO 12999-1:2014 these were extra columns of
  Tables 2/3.
- Maximum repeatability standard deviation for lab self-verification: Table 1.

**Expansion (Clause 8).** $U = k\,u$ (Formula 2) with the coverage
factor `k` of
Table 8 (a minimum of $k = 1$ is enforced). Declaring conformity with a
requirement uses the **one-sided** factor (Formulae 4/5); reporting a two-sided
interval $Y = y \pm U$ (Formula 3) uses the two-sided factor.

**Combination.** Uncorrelated quadrature $u_\mathrm{c} = \sqrt{\sum u_i^2}$
(Formula C.2);
prediction input uncertainty (Formula A.1); model/reality combination (Formula A.2);
reduction by `m` independent measurements $u/\sqrt{m}$ (Formula A.7);
and the
uncorrelated single-number combination of Annex B (Formula B.2).

Clause/table numbers refer to ISO 12999-1:2020(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## assess_requirement_conformity

```python
assess_requirement_conformity(
    rating: float,
    expanded_uncertainty_db: float,
    required_rating: float,
    *,
    bound: Literal['minimum', 'maximum'],
) -> RequirementConformity
```

Does a measured value meet a requirement beyond its uncertainty? (Clause 8).

The expanded uncertainty is worked with the one-sided coverage factor of
Table 8 ([`insulation_coverage_factor`](/phonometry/reference/api/building/uncertainty/#insulation_coverage_factor) with `one_sided=True`) and
then taken off the best estimate for a minimum,
$y - U > Y_\mathrm{required}$ (Formula (5)), or added to it for a
maximum, $y + U < Y_\mathrm{required}$ (Formula (4)): an apparent
sound reduction index `R'w` provably above its minimum, a normalized
impact level `L'n,w` provably below its maximum.

**Parameters**

| Name | Description |
| :--- | :--- |
| `rating` | The best estimate $y$, in dB. |
| `expanded_uncertainty_db` | $U$, one-sided, in dB. |
| `required_rating` | $Y_\mathrm{required}$, in dB. |
| `bound` | `"minimum"` (Formula (5)) or `"maximum"` (Formula (4)). |

**Returns:** The verdict, as a [`RequirementConformity`](/phonometry/reference/api/building/uncertainty/#requirementconformity).

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | For a `rating`, `expanded_uncertainty_db` or `required_rating` that is not one number, or a `bound` that is not a text. |
| ValueError | For an unknown `bound`, a value that is not finite or a negative uncertainty. |

## band_uncertainty

```python
band_uncertainty(
    measurand: Literal['airborne', 'impact', 'impact_reduction'],
    situation: Literal['A', 'B', 'C'],
    *,
    upper_limit: bool = False,
) -> BandUncertainty
```

The one-third-octave standard uncertainties for a measurand.

Airborne (Table 2) offers situations A/B/C; impact (Table 4) only B/C; the
reduction `ΔL` (Table 6) only A. `upper_limit=True` selects the `σR95`
upper limit for airborne, situation A (Annex D Table D.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `measurand` | `"airborne"`, `"impact"` or `"impact_reduction"`. |
| `situation` | Measurement situation `"A"`, `"B"` or `"C"` (Clause 5.2). |
| `upper_limit` | Select the `σR95` upper limit (airborne, situation A). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Unknown measurand, or a situation not tabulated for it. |
| TypeError | if `measurand` is not a text. |

## BandUncertainty

```python
BandUncertainty(
    measurand: Literal['airborne', 'impact', 'impact_reduction'],
    situation: Literal['A', 'B', 'C'],
    frequencies: tuple[float, ...],
    uncertainties: tuple[float, ...],
    *,
    upper_limit: bool = False,
)
```

One-third-octave-band standard uncertainties (ISO 12999-1 Tables 2/4/6/D.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `measurand` | `"airborne"`, `"impact"` or `"impact_reduction"`. |
| `situation` | Measurement situation `"A"`, `"B"` or `"C"` (Clause 5.2). |
| `frequencies` | Band centre frequencies, in Hz. |
| `uncertainties` | Standard uncertainty `u` per band, in dB. |
| `upper_limit` | `True` for the `σR95` upper limit (Annex D Table D.1). |

### BandUncertainty.plot()

```python
BandUncertainty.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the per-band standard uncertainty spectrum.

Requires matplotlib (`pip install "phonometry[plot]"`); returns the
`Axes`.

## COVERAGE_FACTORS

*Constant* (`mapping`).

```python
COVERAGE_FACTORS = {(0.68, False): 1.0, (0.8, False): 1.28, (0.9, False): 1.65, (0.95, False): 1.96, (0.99, False): 2.58, (0.999, False): 3.29, (0.84, True): 1.0, (0.9, True): 1.28, (0.95, True): 1.65, (0.975, True): 1.96, (0.995, True): 2.58, (0.9995, True): 3.29}
```

## insulation_coverage_factor

```python
insulation_coverage_factor(
    coverage: float = 0.95,
    *,
    one_sided: bool = False,
) -> float
```

The coverage factor `k` for a coverage probability (Table 8).

**Parameters**

| Name | Description |
| :--- | :--- |
| `coverage` | Coverage probability as a fraction. Two-sided values are `0.68, 0.80, 0.90, 0.95, 0.99, 0.999`; one-sided values are `0.84, 0.90, 0.95, 0.975, 0.995, 0.9995`. |
| `one_sided` | Use the one-sided column (conformity checks, Formulae 4/5). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Coverage probability not tabulated in Table 8. |
| TypeError | if `coverage` is not a single number. |

## insulation_expanded_uncertainty

```python
insulation_expanded_uncertainty(
    u: float,
    coverage: float = 0.95,
    *,
    one_sided: bool = False,
) -> float
```

The expanded uncertainty $U = k\,u$ (Formula 2, Clause 8).

The coverage factor `k` is taken from Table 8 for the requested coverage
probability; a minimum of $k = 1$ is enforced (Clause 8).

**Parameters**

| Name | Description |
| :--- | :--- |
| `u` | Standard uncertainty `u`, in dB (must be non-negative). |
| `coverage` | Coverage probability as a fraction (see [`insulation_coverage_factor`](/phonometry/reference/api/building/uncertainty/#insulation_coverage_factor)). |
| `one_sided` | Use the one-sided coverage factor (conformity checks). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Negative `u` or an untabulated coverage probability. |
| TypeError | if `u` is not a single number. |

## max_repeatability_standard_deviation

```python
max_repeatability_standard_deviation() -> BandUncertainty
```

Table 1: the maximum repeatability standard deviation per band (Clause 5.8).

A laboratory verifies its own procedure when the repeatability standard
deviation of `nx` repeated measurements stays below these values.

## prediction_input_uncertainty

```python
prediction_input_uncertainty(
    sigma_reproducibility: float,
    sigma_product: float,
    n: int | np.integer[Any],
) -> float
```

The prediction input uncertainty `u_input` (Formula A.1).

$$
u_{\mathrm{input}} = \sqrt{\frac{\sigma_\mathrm{R}^2 + \sigma_{\mathrm{product}}^2}{n} + \sigma_{\mathrm{product}}^2}
$$

combines the
reproducibility standard deviation with the product-homogeneity scatter over
`n` measurements of nominally identical specimens.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sigma_reproducibility` | Reproducibility standard deviation `σR`, in dB. |
| `sigma_product` | Product-homogeneity standard deviation `σ_product`, in dB. |
| `n` | Number of measurements of the product ($n \ge 1$). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | A non-integer or non-positive `n`, or a negative standard deviation. |
| TypeError | if `sigma_product` or `sigma_reproducibility` is not a single number, or `n` is a flag, a text or an array where a count goes. |

## reduce_by_independent_measurements

```python
reduce_by_independent_measurements(u: float, m: int) -> float
```

Reduce a standard uncertainty by `m` independent measurements (Formula A.7).

$u_{\mathrm{reduced}} = u / \sqrt{m}$: measurements by different
persons with different
equipment lower the in-situ uncertainty.

**Parameters**

| Name | Description |
| :--- | :--- |
| `u` | Standard uncertainty of a single measurement, in dB (non-negative). |
| `m` | Number of independent measurements ($m \ge 1$). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Non-positive `m` or negative `u`. |
| TypeError | if `m` or `u` is not a single number. |

## RequirementConformity

```python
RequirementConformity(
    rating: float,
    expanded_uncertainty_db: float,
    required_rating: float,
    *,
    bound: Literal['minimum', 'maximum'],
)
```

A measured value against a requirement, with its uncertainty (Clause 8).

ISO 12999-1:2020 Clause 8 declares conformity only when the whole one-sided
interval clears the requirement: $y - U > Y_\mathrm{required}$ for a
minimum (Formula (5)) and $y + U < Y_\mathrm{required}$ for a maximum
(Formula (4)). Both are strict, so a value that clears the requirement by
exactly $U$ does not conform. The margin and the verdict are read
from the three values and the side, so they are not fields: a record cannot
be built to conform with a value the clause refuses.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | The best estimate $y$, in dB. |
| `expanded_uncertainty_db` | $U$, worked with the one-sided coverage factor, in dB. |
| `required_rating` | $Y_\mathrm{required}$, in dB. |
| `bound` | `"minimum"` when the requirement is a value to exceed (an apparent sound reduction index `R'w`) or `"maximum"` when it is one to stay under (a normalized impact level `L'n,w`). |

### RequirementConformity.margin_db

*property*

How far the uncertain interval clears the requirement, in dB.

$y - U - Y_\mathrm{required}$ for a minimum and
$Y_\mathrm{required} - (y + U)$ for a maximum: positive when the
value conforms. Settled, so a value exactly $U$ from the
requirement in decimal gives a margin of zero whichever way the last
bits of the subtraction fall.

### RequirementConformity.passes

*property*

The verdict: the margin is positive, Formula (5) or (4) holds.

## single_number_uncertainty

```python
single_number_uncertainty(
    quantity: Literal['r_w', 'r_w+c_50_3150', 'r_w+c_50_5000', 'r_w+c_100_3150', 'r_w+c_100_5000', 'r_w+ctr_50_3150', 'r_w+ctr_50_5000', 'r_w+ctr_100_3150', 'r_w+ctr_100_5000', 'ln_w', 'ln_w+ci', 'delta_lw', 'rprime_w', 'r_prime_w', 'dn_w', 'dnw', 'dnt_w', 'dntw', 'lprime_n_w', 'lnprime_w', 'lnt_w', 'lprime_nt_w', 'delta_l_w'],
    situation: Literal['A', 'B', 'C'],
    *,
    upper_limit: bool = False,
) -> float
```

The tabulated single-number standard uncertainty `u`, in dB.

Descriptors (case-insensitive, with aliases) cover the ISO 717 ratings:
`"r_w"` (also `rprime_w`/`dn_w`/`dnt_w`) and its spectrum-adaptation
variants `"r_w+c_50_5000"` etc. (Table 3); `"ln_w"`/`"ln_w+ci"` (Table 5);
`"delta_lw"` (Table 7). `upper_limit=True` selects the situation-A `σR95`
(Annex D Table D.2), defined for airborne descriptors only.

:::note
For the impact descriptors (`"ln_w"`/`"ln_w+ci"`, Table 5) the
situation-A value is an *estimate*: no reproducibility results are
available for impact sound insulation (Table 5, footnote a).
:::

**Parameters**

| Name | Description |
| :--- | :--- |
| `quantity` | Rating descriptor (see above). |
| `situation` | Measurement situation `"A"`, `"B"` or `"C"` (Clause 5.2). |
| `upper_limit` | Select the `σR95` upper limit (airborne, situation A). |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Unknown descriptor, an untabulated situation, or an `upper_limit` request outside airborne/situation A. |

## single_number_uncertainty_uncorrelated

```python
single_number_uncertainty_uncorrelated(
    band_uncertainties: ArrayLike,
    reference_differences: ArrayLike,
) -> float
```

Uncorrelated single-number uncertainty from band uncertainties (Formula B.2).

$$
u(R_\mathrm{w}{+}C) = \sqrt{\sum_i (w_i \, u_i)^2}
$$

with energy weights

$$
w_i = \frac{10^{(L_i - R_i)/10}}{\sum_j 10^{(L_j - R_j)/10}}
$$

derived from the
reference spectrum. This is the *no-correlation* estimate of Annex B; the
fully correlated bound (Formulae B.3-B.6) instead re-runs the ISO 717 rating
and is not reproduced here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_uncertainties` | Per-band standard uncertainties `u_i`, in dB. |
| `reference_differences` | Per-band $L_i - R_i$ (reference-spectrum level minus measured band value), in dB. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | Mismatched shapes, empty input, or negative `u_i`. |

## uncertain_value

```python
uncertain_value(
    value: float,
    quantity: Literal['r_w', 'r_w+c_50_3150', 'r_w+c_50_5000', 'r_w+c_100_3150', 'r_w+c_100_5000', 'r_w+ctr_50_3150', 'r_w+ctr_50_5000', 'r_w+ctr_100_3150', 'r_w+ctr_100_5000', 'ln_w', 'ln_w+ci', 'delta_lw', 'rprime_w', 'r_prime_w', 'dn_w', 'dnw', 'dnt_w', 'dntw', 'lprime_n_w', 'lnprime_w', 'lnt_w', 'lprime_nt_w', 'delta_l_w'],
    situation: Literal['A', 'B', 'C'],
    *,
    coverage: float = 0.95,
    one_sided: bool = False,
    upper_limit: bool = False,
) -> UncertainValue
```

Attach the ISO 12999-1 expanded uncertainty to a single-number rating.

Convenience wrapper combining [`single_number_uncertainty`](/phonometry/reference/api/building/uncertainty/#single_number_uncertainty),
[`insulation_coverage_factor`](/phonometry/reference/api/building/uncertainty/#insulation_coverage_factor) and [`insulation_expanded_uncertainty`](/phonometry/reference/api/building/uncertainty/#insulation_expanded_uncertainty) into an
[`UncertainValue`](/phonometry/reference/api/building/uncertainty/#uncertainvalue) ($y \pm U$) without modifying the rating
dataclasses. For conformity checks pass `one_sided=True` and read
[`UncertainValue.lower`](/phonometry/reference/api/building/uncertainty/#uncertainvaluelower) / [`UncertainValue.upper`](/phonometry/reference/api/building/uncertainty/#uncertainvalueupper) (Formulae 4/5).

**Parameters**

| Name | Description |
| :--- | :--- |
| `value` | Best estimate `y` (e.g. `Rw` in dB). |
| `quantity` | Rating descriptor (see [`single_number_uncertainty`](/phonometry/reference/api/building/uncertainty/#single_number_uncertainty)). |
| `situation` | Measurement situation `"A"`, `"B"` or `"C"` (Clause 5.2). |
| `coverage` | Coverage probability as a fraction. |
| `one_sided` | Use the one-sided coverage factor. |
| `upper_limit` | Use the `σR95` upper limit (airborne, situation A). |

## UncertainValue

```python
UncertainValue(
    value: float,
    standard_uncertainty: float,
    coverage_factor: float,
    expanded_uncertainty: float,
    coverage: float,
    *,
    one_sided: bool,
)
```

A best estimate with its ISO 12999-1 expanded uncertainty (Clause 8).

**Attributes**

| Name | Description |
| :--- | :--- |
| `value` | Best estimate `y` (e.g. a weighted rating), in dB. |
| `standard_uncertainty` | Standard uncertainty `u`, in dB. |
| `coverage_factor` | Coverage factor `k` (Table 8). |
| `expanded_uncertainty` | $U = k\,u$, in dB. |
| `coverage` | The coverage probability of `expanded_uncertainty`, as a fraction (e.g. `0.95`). |
| `one_sided` | `True` for a one-sided interval (conformity checks). |

### UncertainValue.lower

*property*

Lower interval bound $y - U$ (Formula 3/5).

### UncertainValue.upper

*property*

Upper interval bound $y + U$ (Formula 3/4).
