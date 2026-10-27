---
title: "metrology.uncertainty"
description: "Measurement uncertainty by the GUM and its Monte Carlo supplement."
sidebar:
  label: "uncertainty"
---

Measurement uncertainty by the GUM and its Monte Carlo supplement.

Implements the two propagation methods of the *Guide to the Expression of
Uncertainty in Measurement*:

* the **law of propagation of uncertainty** (ISO/IEC Guide 98-3:2008, clause 5)
  - the combined standard uncertainty of a measurement model
  $y = f(x_1, \ldots, x_N)$
  from the input standard uncertainties and sensitivity coefficients, with
  optional input correlations, the effective degrees of freedom
  (Welch-Satterthwaite, Annex G.4) and the expanded uncertainty
  $U = k u_\mathrm{c}$ with a coverage factor from the t-distribution
  (clause 6);
* the **Monte Carlo method** (ISO/IEC Guide 98-3-1:2008, Supplement 1) - the
  numerical propagation of the input probability density functions, giving the
  estimate, its standard uncertainty and a probabilistically symmetric coverage
  interval (clause 7.7).

Input quantities are described by [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity); [`rectangular`](/phonometry/reference/api/metrology/uncertainty/#rectangular),
[`triangular`](/phonometry/reference/api/metrology/uncertainty/#triangular) and [`u_shaped`](/phonometry/reference/api/metrology/uncertainty/#u_shaped) build Type B quantities from a
half-width (clause 4.3).

Scope notes: [`monte_carlo`](/phonometry/reference/api/metrology/uncertainty/#monte_carlo) runs a **fixed** number of trials and reports
the probabilistically symmetric interval only -- the adaptive procedure of
Supplement 1 clause 7.9 and the shortest coverage interval of 5.3.4 are not
implemented; its inputs are sampled independently (the multivariate-Gaussian
path of 6.4.8 for non-independent quantities is not implemented -- use
[`uncertainty_propagation`](/phonometry/reference/api/metrology/uncertainty/#uncertainty_propagation) with `correlation` for correlated budgets).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## combined_standard_uncertainty

```python
combined_standard_uncertainty(
    contributions: Sequence[float | Sequence[float] | NDArray[Any]] | NDArray[Any],
) -> float
```

Combined standard uncertainty of independent contributions, root-sum-square.

$u_\mathrm{c} = \sqrt{\sum_j (c_j u_j)^2}$: the law of
propagation of uncertainty for uncorrelated input quantities
(ISO/IEC Guide 98-3:2008, 5.1.2, Equation (10), written with
$c_j u(x_j)$ as in 5.1.3), the same sum ISO 1996-2:2017 prints as
Formula (2) for an environmental noise level and ISO 12999-1:2020 as
Formula (C.2) for building acoustics, where Formula (A.2) adds the
model-to-reality term to a predicted value the same way. Every domain
that adds independent contributions in quadrature calls this one
function; [`uncertainty_propagation`](/phonometry/reference/api/metrology/uncertainty/#uncertainty_propagation) is the full budget, with
sensitivity coefficients from a model, correlations and degrees of
freedom.

**Parameters**

| Name | Description |
| :--- | :--- |
| `contributions` | Either the products $c_j u_j$, one per contribution, in the unit of the result (decibels for a level), or `(u_j, c_j)` pairs whose product is formed here (each a tuple, a list or an array of the two), with `u_j` non-negative; the two may be mixed, and an array of pairs is read row by row. Independent inputs are assumed, so there is no covariance term. |

**Returns:** $u_\mathrm{c}$, in the unit of the contributions.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `contributions` is empty, holds a value that is not finite, a pair that is not `(uncertainty, sensitivity)`, or a pair whose uncertainty is negative. |

## coverage_factor

```python
coverage_factor(coverage: float = 0.95, dof: float = inf) -> float
```

Coverage factor `k` from the t-distribution (GUM clause 6, Annex G).

**Parameters**

| Name | Description |
| :--- | :--- |
| `coverage` | Coverage probability in (0, 1). |
| `dof` | Effective degrees of freedom; `inf` gives the normal quantile. |

**Returns:** The two-sided coverage factor $k = t_p(\text{dof})$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a coverage outside (0, 1). |
| TypeError | if `coverage` or `dof` is not a single number. |

## ExpandedUncertainty

```python
ExpandedUncertainty(coverage_factor: float, expanded_uncertainty: float)
```

An expanded uncertainty and the coverage factor it was formed with.

What [`UncertaintyResult.expanded`](/phonometry/reference/api/metrology/uncertainty/#uncertaintyresultexpanded) returns: `k` and
$U = k u_\mathrm{c}$, named, where a `(k, U)` tuple used to be
unpacked by position (GUM clause 6, Annex G).

**Attributes**

| Name | Description |
| :--- | :--- |
| `coverage_factor` | The coverage factor `k`. |
| `expanded_uncertainty` | $U = k u_\mathrm{c}$, in the unit of the measurand. |

## monte_carlo

```python
monte_carlo(
    model: Callable[..., ArrayLike],
    quantities: Sequence[Quantity],
    n_trials: int = 1000000,
    coverage: float = 0.95,
    seed: int | None = None,
    *,
    keep_samples: bool = False,
) -> MonteCarloResult
```

Propagate uncertainty by the Monte Carlo method (Supplement 1).

Draws `n_trials` samples of each input from its PDF, evaluates the model and
reports the sample mean, the sample standard deviation and the
probabilistically symmetric coverage interval (clause 7.7).

The inputs are sampled **independently**: the Supplement's
multivariate-Gaussian path for non-independent quantities (6.4.8) is not
implemented (use [`uncertainty_propagation`](/phonometry/reference/api/metrology/uncertainty/#uncertainty_propagation) with `correlation` for a
correlated budget). The number of trials is fixed (the adaptive procedure
of clause 7.9 is not implemented) and the reported interval is the
probabilistically symmetric one (not the 5.3.4 shortest interval).

**Parameters**

| Name | Description |
| :--- | :--- |
| `model` | The measurement function $f(x_1, \ldots, x_N)$ returning `y`; it must accept array arguments (vectorised over the trials). |
| `quantities` | The input [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) objects, in argument order. |
| `n_trials` | Number of Monte Carlo trials `M` (at least 2; the sample standard deviation needs two values). |
| `coverage` | Coverage probability of the reported interval. |
| `seed` | Optional seed for the random generator (reproducibility). |
| `keep_samples` | Retain the raw output sample on the result (one float per trial) so [`MonteCarloResult.plot`](/phonometry/reference/api/metrology/uncertainty/#montecarloresultplot) can draw the output-distribution histogram. |

**Returns:** A [`MonteCarloResult`](/phonometry/reference/api/metrology/uncertainty/#montecarloresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no inputs, fewer than 2 trials or bad coverage, or when the model returns a non-finite output for any trial. |
| TypeError | if `coverage` or `n_trials` is not a single number. |

## MonteCarloResult

```python
MonteCarloResult(
    value: float,
    standard_uncertainty: float,
    interval: tuple[float, float],
    coverage: float,
    n_trials: int,
    samples: np.ndarray | None = None,
)
```

Result of the Monte Carlo method (Guide 98-3-1, Supplement 1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `value` | Estimate `y` (the sample mean of the output). |
| `standard_uncertainty` | $u(y)$ (the sample standard deviation). |
| `interval` | Probabilistically symmetric coverage interval `(low, high)` (clause 7.7). |
| `coverage` | The coverage probability of `interval`. |
| `n_trials` | Number of Monte Carlo trials. |
| `samples` | The raw model-output sample (one value per trial), kept only when [`monte_carlo`](/phonometry/reference/api/metrology/uncertainty/#monte_carlo) is called with `keep_samples=True` (it feeds the output-distribution histogram of `plot`). |

### MonteCarloResult.plot()

```python
MonteCarloResult.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the output histogram with the coverage interval marked.

Needs the raw output sample, so call `monte_carlo(...,
keep_samples=True)`. Requires matplotlib
(`pip install "phonometry[plot]"`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `language` | Label language, `"en"` (default) or `"es"`. |

## Quantity

```python
Quantity(
    *,
    value: float,
    uncertainty: float,
    distribution: Literal['gaussian', 'rectangular', 'triangular', 'u-shaped'] = 'gaussian',
    dof: float = inf,
    name: str = '',
)
```

An input quantity of a measurement model (GUM clause 4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `value` | Best estimate $x_i$ of the input quantity. |
| `uncertainty` | Standard uncertainty $u(x_i)$ (>= 0). |
| `distribution` | PDF used by the Monte Carlo method: `"gaussian"`, `"rectangular"`, `"triangular"` or `"u-shaped"`. |
| `dof` | Degrees of freedom of `uncertainty` (`inf` for Type B). |
| `name` | Optional label used in the uncertainty budget and its plot. |

## rectangular

```python
rectangular(value: float, half_width: float, name: str = '') -> Quantity
```

Type B quantity with a rectangular PDF of half-width `a` (GUM 4.3.7).

The standard uncertainty is $a / \sqrt{3}$.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `half_width` or `value` is not a single number. |

## triangular

```python
triangular(value: float, half_width: float, name: str = '') -> Quantity
```

Type B quantity with a triangular PDF of half-width `a` (GUM 4.3.9).

The standard uncertainty is $a / \sqrt{6}$.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `half_width` or `value` is not a single number. |

## u_shaped

```python
u_shaped(value: float, half_width: float, name: str = '') -> Quantity
```

Type B quantity with a U-shaped (arcsine) PDF of half-width `a`.

The standard uncertainty is $a / \sqrt{2}$.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `half_width` or `value` is not a single number. |

## uncertainty_propagation

```python
uncertainty_propagation(
    model: Callable[..., float | np.floating[Any] | np.integer[Any]],
    quantities: Sequence[Quantity],
    correlation: ArrayLike | None = None,
) -> UncertaintyResult
```

Combined standard uncertainty by the GUM law of propagation (clause 5).

**Parameters**

| Name | Description |
| :--- | :--- |
| `model` | The measurement function $f(x_1, \ldots, x_N)$ returning `y`. |
| `quantities` | The input [`Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) objects, in the order the model takes its arguments. |
| `correlation` | Optional `N x N` correlation matrix $r_{ij}$ between the inputs; `None` treats them as uncorrelated. With a non-identity matrix and finite input dof the effective degrees of freedom are `NaN` (undefined; the GUM defines no correlated fallback -- Welch-Satterthwaite holds for independent inputs only) and an [`UncertaintyWarning`](/phonometry/reference/api/metrology/uncertainty/#uncertaintywarning) is issued when finite input dof would otherwise have been propagated. |

**Returns:** An [`UncertaintyResult`](/phonometry/reference/api/metrology/uncertainty/#uncertaintyresult) with $u_\mathrm{c}(y)$, the sensitivity coefficients, the contributions and the effective degrees of freedom.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no inputs, a malformed correlation matrix, or a model that is not finite at the estimates or one evaluation step either side of them. |

## UncertaintyResult

```python
UncertaintyResult(
    value: float,
    combined_uncertainty: float,
    sensitivities: np.ndarray,
    contributions: np.ndarray,
    effective_dof: float,
    names: tuple[str, ...] = (),
)
```

Result of the GUM law of propagation of uncertainty (Guide 98-3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `value` | The output estimate $y = f(x_1, \ldots, x_N)$. |
| `combined_uncertainty` | Combined standard uncertainty $u_\mathrm{c}(y)$. |
| `sensitivities` | Sensitivity coefficients $c_i = \partial f/\partial x_i$. |
| `contributions` | Per-input contributions $\lvert c_i \rvert u(x_i)$ to $u_\mathrm{c}(y)$. |
| `effective_dof` | Welch-Satterthwaite effective degrees of freedom (Annex G.4, defined for independent inputs). For a correlated budget with finite input dof it is `NaN` (undefined: the GUM has no correlated form and `expanded()` then needs an explicit factor); with all-infinite input dof it is `inf` (normal-distribution coverage factor), since the GUM defines no correlated Welch-Satterthwaite form. |
| `names` | Input labels aligned with the arrays above. |

### UncertaintyResult.expanded()

```python
UncertaintyResult.expanded(
    coverage: float = 0.95,
    *,
    coverage_factor_override: float | None = None,
) -> ExpandedUncertainty
```

Coverage factor `k` and expanded uncertainty $U = k u_\mathrm{c}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `coverage` | Coverage probability in (0, 1); `0.95` by default. |
| `coverage_factor_override` | Explicit `k`. Required for a correlated budget with finite input degrees of freedom, where the GUM defines no effective-dof formula (`effective_dof` is NaN). |

**Returns:** The coverage factor `k` and `U`, as an [`ExpandedUncertainty`](/phonometry/reference/api/metrology/uncertainty/#expandeduncertainty) (GUM clause 6, Annex G).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the effective dof are undefined and no explicit coverage factor is given. |

### UncertaintyResult.plot()

```python
UncertaintyResult.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the uncertainty budget (per-input contributions).

Requires matplotlib (`pip install "phonometry[plot]"`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `language` | Label language, `"en"` (default) or `"es"`. |

## UncertaintyWarning

A GUM propagation fell back outside its nominal assumptions.
