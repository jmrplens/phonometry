← [Documentation index](README.md)

# Measurement uncertainty (GUM and Monte Carlo)

Every measurement result is incomplete without a statement of its uncertainty.
The *Guide to the Expression of Uncertainty in Measurement* gives two ways to
propagate the uncertainties of the inputs of a measurement model
$y = f(x_1, \dots, x_N)$ to the output: the **law of propagation of
uncertainty** (**ISO/IEC Guide 98-3:2008**, the GUM, clause 5) and the
**Monte Carlo method** (**ISO/IEC Guide 98-3-1:2008**, Supplement 1, clause 7).
The first combines standard uncertainties analytically through the sensitivity
coefficients; the second propagates the whole probability distributions
numerically. They agree for linear models and diverge, informatively, when the
model is non-linear or the inputs are far from Gaussian.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_uncertainty_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_uncertainty.svg" alt="From a shared measurement model y equals f of x1 to xN with its input estimates and standard uncertainties, two parallel lanes. Left, the GUM law of propagation: sensitivity coefficients c_i equal the partial derivative of f with respect to x_i, combined in quadrature so uc squared is the sum of c_i squared times u squared of x_i plus correlation terms, then the Welch-Satterthwaite effective degrees of freedom, giving the expanded uncertainty U equals k times uc with k the t-distribution coverage factor. Right, the Monte Carlo method: draw each x_i from its probability density, propagate M trials of y equals f of the sampled inputs, then sort the outputs and take the probabilistically symmetric 95 percent coverage interval from low to high fractiles" width="88%"></picture>

## 1. The law of propagation of uncertainty (GUM clause 5)

For a model $y = f(x_1, \dots, x_N)$ with uncorrelated inputs, the combined
standard uncertainty is the quadrature sum of the input contributions
$u_i(y) = |c_i|\,u(x_i)$ weighted by the sensitivity coefficients
$c_i = \partial f / \partial x_i$:

$$
u_c^2(y) = \sum_{i=1}^{N} \left(\frac{\partial f}{\partial x_i}\right)^2 u^2(x_i).
$$

`combine_uncertainty` evaluates the sensitivities by central differences, so any
callable model works — no hand-derived partials. Input quantities are described
by a `Quantity` (best estimate, standard uncertainty, PDF, degrees of freedom).
Type B evaluations from a half-width $a$ are built by `rectangular`
($a/\sqrt{3}$), `triangular` ($a/\sqrt{6}$) and `u_shaped` ($a/\sqrt{2}$)
(GUM clause 4.3).

```python
import phonometry as ph

# A-weighted level: a reading plus zero-mean calibration, instrument and
# positional corrections. The model is their sum.
quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
result = ph.combine_uncertainty(lambda a, b, c, d: a + b + c + d, quantities)

print(round(result.value, 2))                 # 74.0
print(round(result.combined_uncertainty, 3))  # 0.407 dB
print(result.contributions.round(3))          # [0.    0.115 0.173 0.35 ]
print(round(result.effective_dof, 1))         # 16.5

k, U = result.expanded(0.95)
print(round(k, 2), round(U, 2))               # 2.11 0.86  ->  Y = 74.0 ± 0.9 dB
```

The **expanded uncertainty** $U = k\,u_c$ scales the combined uncertainty by a
coverage factor $k = t_p(\nu_\text{eff})$ from the $t$-distribution at the
**effective degrees of freedom** given by the Welch–Satterthwaite formula
(Annex G.4). Here the single Type A input (9 degrees of freedom) pulls
$\nu_\text{eff}$ down to about 16, so $k = 2.11$ rather than the large-sample
1.96. Correlated inputs are handled by passing a correlation matrix; a fully
correlated sum then adds linearly instead of in quadrature.

## 2. The Monte Carlo method (Supplement 1)

When the model is non-linear or the inputs are markedly non-Gaussian, the GUM
Gaussian assumption for the output can be inaccurate. `monte_carlo` instead
draws samples of each input from its PDF, evaluates the model over all trials
and reports the mean, the standard deviation and the **probabilistically
symmetric coverage interval** (equal probability in each tail, clause 7.7).

```python
import phonometry as ph

quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
mc = ph.monte_carlo(lambda a, b, c, d: a + b + c + d, quantities,
                    trials=1_000_000, coverage=0.95, seed=1)

print(round(mc.value, 2))                 # 74.0
print(round(mc.standard_uncertainty, 3))  # 0.407 dB  (matches uc above)
print([round(x, 2) for x in mc.interval]) # [73.2, 74.8]
```

For this near-linear model the Monte Carlo standard uncertainty reproduces the
GUM $u_c$ to three digits and the 95 % interval matches $Y \pm U$. The two
methods are validated against the Guides' own worked examples: the additive
model of four unit inputs gives $u_c = 2.0$ (Supplement 1 clause 9.2), and four
rectangular inputs give a Monte Carlo interval of $[-3.88,\, 3.88]$
(Supplement 1 clause 9.2.3).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/uncertainty_budget_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/uncertainty_budget.png" alt="Two panels for the A-weighted level example. Left, the GUM uncertainty budget: a horizontal bar chart of the contribution of each input to the combined uncertainty — Reading contributes nothing, Calibration and Instrument the rectangular corrections, and the Position Type A term the most — with a dashed line marking the combined uncertainty uc of 0.407 dB. Right, the Monte Carlo output distribution as a histogram, overlaid with the GUM Gaussian of the same mean and standard deviation, and the shaded 95 percent coverage interval; the title reads Y equals 74.00 dB, U equals 0.86 dB, k equals 2.11" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
model = lambda a, b, c, d: a + b + c + d
result = ph.combine_uncertainty(model, quantities)
mc = ph.monte_carlo(model, quantities, trials=1_000_000, coverage=0.95, seed=1,
                    keep_samples=True)
k, U = result.expanded(0.95)

# One line per panel — the budget bars, and the Monte Carlo histogram with
# its coverage interval (the committed figure also overlays the GUM Gaussian):
result.plot()
mc.plot()
plt.show()

# By hand, both panels — budget bars and the Monte Carlo output distribution:
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4))
ax1.barh(result.names, result.contributions)
ax1.axvline(result.combined_uncertainty, ls="--",
            label=f"$u_c$ = {result.combined_uncertainty:.3f} dB")
ax1.invert_yaxis(); ax1.legend()

rng = np.random.default_rng(1)
samples = model(np.full(200_000, 74.0),
                rng.uniform(-0.20, 0.20, 200_000),
                rng.uniform(-0.30, 0.30, 200_000),
                rng.normal(0.0, 0.35, 200_000))
ax2.hist(samples, bins=120, density=True, alpha=0.35, label="Monte Carlo")
ax2.axvspan(*mc.interval, alpha=0.12, label="95 % coverage interval")
ax2.set_title(f"Y = {result.value:.2f} dB,  U = {U:.2f} dB (k = {k:.2f})")
ax2.legend()
plt.show()
```

</details>

The `UncertaintyResult` carries the `value`, `combined_uncertainty`, the
`sensitivities`, the per-input `contributions` and the `effective_dof`; its
`.plot()` draws the budget and `.expanded(coverage)` returns the pair
$(k, U)$. The `MonteCarloResult` carries the `value`, `standard_uncertainty`,
the coverage `interval` and its `coverage`; with `keep_samples=True` it also
retains the output `samples`, and its `.plot()` draws the output histogram
with the coverage interval marked (the right panel above). The building-acoustics uncertainty
of ISO 12999-1 — which combines reproducibility terms for a single-number
rating — is a separate, domain-specific budget.

---

**Standards.** ISO/IEC Guide 98-3:2008, *Uncertainty of measurement — Part 3:
Guide to the expression of uncertainty in measurement (GUM:1995)* — the law of
propagation of uncertainty (clause 5), Type B evaluation (clause 4.3), the
expanded uncertainty and coverage factor (clause 6, Annex G) and the
Welch–Satterthwaite effective degrees of freedom (Annex G.4). ISO/IEC
Guide 98-3-1:2008, *Supplement 1 — Propagation of distributions using a Monte
Carlo method* — the numerical propagation and the probabilistically symmetric
coverage interval (clause 7).
