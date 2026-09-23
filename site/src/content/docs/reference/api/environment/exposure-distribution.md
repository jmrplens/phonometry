---
title: "environment.assessment.exposure_distribution"
description: "How often a blast is how loud: the distribution of its sound exposure level (ISO 13474:2009, clauses 4 and 5)."
sidebar:
  label: "exposure_distribution"
---

How often a blast is how loud: the distribution of its sound exposure level
(ISO 13474:2009, clauses 4 and 5).

A blast, a shot or a detonation a few kilometres away is heard at a level that
changes from one event to the next by ten decibels and more, because the
weather between source and receiver changes. ISO 13474 does not predict one
level; it describes the weather as a set of **replica atmospheres**, each one
a combination of an atmospheric-absorption class `k` and an
excess-attenuation class `l` with its probability of occurrence, computes
the frequency-weighted single-event sound exposure level `L_E,w,k,l` for
each, and turns that list into a statistical distribution. This module is that
statistical core. The propagation that produces each `L_E,w,k,l` (clause 6),
the classification of the weather (clause 7) and the probability of each class
from meteorological data (clause 8) are the caller's input.

The chain, in the order the standard writes it:

* the frequency-weighted level of each replica from its band levels,
  Equation (5), [`frequency_weighted_sel`](/phonometry/reference/api/environment/exposure-distribution/#frequency_weighted_sel);
* the joint probability of the two classes, Equation (14),
  [`replica_probabilities`](/phonometry/reference/api/environment/exposure-distribution/#replica_probabilities);
* the long-term average of the single-event level, Equation (7), and the
  rating level that adds the adjustment `K` for highly impulsive sound,
  Equation (8), [`long_term_sel`](/phonometry/reference/api/environment/exposure-distribution/#long_term_sel);
* the levels placed in increasing order as `M` classes with contiguous
  boundaries half-way between consecutive levels and the density of each
  class, Equations (10) to (16);
* each class split into `N_sub` subclasses, Equations (17) to (20), and each
  subclass replaced by a normal distribution of standard deviation
  $\sigma$ (5 dB is the value the standard says is typically used) whose
  mean is shifted down by

  $$
  \Delta\mu = 10\lg\left[\frac{1}{\sigma\sqrt{2\pi}} \int_{-\infty}^{\infty} 10^{0{,}1x}\, \mathrm{e}^{-x^{2}/(2\sigma^{2})}\,\mathrm{d}x\right] = \frac{\sigma^{2}\ln 10}{20}~\text{dB} \tag{22}
  $$

  so that the energetic mean of the subclass stays where it was, Equations
  (21) to (23), [`turbulence_level_shift`](/phonometry/reference/api/environment/exposure-distribution/#turbulence_level_shift);
* from the continuous density $\rho^{*}(x)$, the probability that the
  level exceeds `x`, Equation (24), and the `n`-percent exceedance level,
  Equation (25), and the long-term level computed a second time from the
  distribution, Equation (A.4) of Annex A.

[`sel_distribution`](/phonometry/reference/api/environment/exposure-distribution/#sel_distribution) does the last three steps and returns a
[`SelDistribution`](/phonometry/reference/api/environment/exposure-distribution/#seldistribution), whose `.plot()` draws the class density, the
continuous density or the exceedance curve.

Two readings the text leaves to the implementer
-----------------------------------------------

**Equal levels.** Equation (11) puts a boundary half-way between consecutive
levels, so two equal levels share a boundary at that level and each keeps a
class of non-zero width on its own side; Annex A does exactly that with its
two classes at 30,8 dB and its two at 31,8 dB, and so does this module. The
standard names one case, three consecutive equal levels, whose middle class
then has no width and no defined density, and for it says "classes with the
same level shall be combined". A run of two equal levels at either end of the
list leaves a class of no width in the same way, through Equation (12) or
(13); the standard does not mention it, and this module reads it as the same
case. Every run of equal levels that would leave a class of no width is
therefore combined into one class carrying the sum of their probabilities;
every other run is left as the standard writes it.

**The integrals.** Equations (22), (24) and (A.4) are integrals of Gaussian
functions and are evaluated here in closed form, not by quadrature: the shift
is $\sigma^{2}\ln 10/20$, the exceedance is a sum of Gaussian tail
probabilities, and $\int\rho^{*}(x)\,10^{0{,}1x}\,\mathrm{d}x$ is a sum of
lognormal means. There is no integration range to choose and no truncation to
account for.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## frequency_weighted_sel

```python
frequency_weighted_sel(
    band_levels_db: ArrayLike,
    weighting_db: ArrayLike,
) -> float | NDArray[np.float64]
```

Frequency-weighted sound exposure level from band levels (Equation (5)).

$$
L_{E,\mathrm{w}} = 10\lg\sum_{j=N_\mathrm{min}}^{N_\mathrm{max}} 10^{0{,}1\left[L_E(j) + \mathrm{w}(j)\right]}~\text{dB}
$$

The standard prefers one-third-octave bands and requires every band from
1 Hz (index 0) to 10 kHz (index 40) whose weighted level is within 20 dB of
the largest weighted band level. Which bands those are depends on the
spectrum, so the function sums every band it is given: passing the whole
range from 1 Hz to 10 kHz always meets the requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_levels_db` | Band sound exposure levels $L_E(j)$, in dB, along the last axis. Leading axes are kept, so an array of shape `(N_atm, N_exc, n_bands)` of the replica atmospheres returns their `(N_atm, N_exc)` weighted levels at once. |
| `weighting_db` | The frequency weighting $\mathrm{w}(j)$ of each band, in dB (A-weighting, C-weighting or any other), broadcast against `band_levels_db`. |

**Returns:** $L_{E,\mathrm{w}}$ in dB, a float for a single spectrum.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty or non-finite input, or shapes that do not broadcast. |

## long_term_sel

```python
long_term_sel(
    levels_db: ArrayLike,
    probabilities: ArrayLike,
    *,
    rating_adjustment_db: float = 0.0,
) -> float
```

Long-term average single-event sound exposure level (Equations (7), (8)).

$$
\langle L_{E,\mathrm{w}}\rangle_\mathrm{LT} = 10\lg\left[ \sum_{k=1}^{N_\mathrm{atm}}\sum_{l=1}^{N_\mathrm{exc}} \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}\, 10^{0{,}1 L_{E,\mathrm{w},k,l}}\right]~\text{dB} \tag{7}
$$

With the rating level adjustment `K` for highly impulsive sound of
ISO 1996-1 inside the sum, the same expression is the long-term average
single-event sound exposure **rating** level
$\langle L_\mathrm{r}\rangle_\mathrm{LT}$ of Equation (8), the
quantity the standard offers to ISO 1996-1 as the frequency-weighted and
adjusted single-event level. `K` is one constant for the source, so
Equation (8) is Equation (7) plus `K`.

Annex A calls this value `LT1` and computes it with a single
atmospheric-absorption class of probability 1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{E,\mathrm{w},k,l}$ of each replica atmosphere, in dB, any shape (`(N_atm, N_exc)` or already flattened). |
| `probabilities` | The probability of each replica, the same shape as `levels_db` (see [`replica_probabilities`](/phonometry/reference/api/environment/exposure-distribution/#replica_probabilities)). |
| `rating_adjustment_db` | `K`, in dB; 0 dB (the default) gives Equation (7). |

**Returns:** The long-term average level, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the shapes differ, a probability is negative, the probabilities do not sum to one, every probability is zero, or a value is not finite. |

## replica_probabilities

```python
replica_probabilities(
    absorption_probabilities: ArrayLike,
    excess_attenuation_probabilities: ArrayLike,
) -> NDArray[np.float64]
```

Probability of occurrence of each replica atmosphere (Equation (14)).

$$
\wp_m = \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}
$$

The two classifications are taken as independent (clause 4.5, NOTE 1 to
Equation (6)), so the probability of the replica `(k, l)` is the product
of the probability of its atmospheric-absorption class and that of its
excess-attenuation class.

**Parameters**

| Name | Description |
| :--- | :--- |
| `absorption_probabilities` | $\wp_{\mathrm{atm},k}$, one per atmospheric-absorption class. Annex A uses a single class of probability 1. |
| `excess_attenuation_probabilities` | $\wp_{\mathrm{exc},l}$, one per excess-attenuation class. |

**Returns:** An array of shape `(N_atm, N_exc)`, row `k` and column `l`, the shape [`sel_distribution`](/phonometry/reference/api/environment/exposure-distribution/#sel_distribution) and [`long_term_sel`](/phonometry/reference/api/environment/exposure-distribution/#long_term_sel) read `levels_db` in.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty, multi-dimensional, non-finite or negative input. |

## sel_distribution

```python
sel_distribution(
    levels_db: ArrayLike,
    probabilities: ArrayLike,
    *,
    sigma_db: float = 5.0,
    subclasses: int = 10,
) -> SelDistribution
```

Statistical distribution of the single-event sound exposure level
(ISO 13474:2009, clause 5).

The levels of the replica atmospheres are placed in increasing order
(Equation (10)); boundaries between consecutive classes lie half-way
between their levels (Equation (11)) and the two outer boundaries mirror
the nearest inner one about the end level (Equations (12), (13)); each
class has the constant density $\rho_m = \wp_m/(g_{\mathrm{U},m} - g_{\mathrm{L},m})$ (Equation (15)). Each class is then divided into
`subclasses` equal subclasses of width $b_m$ centred at
$\mu_{m,j} = g_{\mathrm{L},m} + (j - \tfrac12)b_m$ (Equations (17),
(18)), and each subclass is replaced by a normal distribution of standard
deviation `sigma_db` and weight $b_m\rho_m$, centred at
$\mu_{m,j} - \Delta\mu$ (Equations (21) to (23)).

Equal levels keep their own classes unless that leaves a class of no
width, in which case the run is combined (see the module documentation).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{E,\mathrm{w},k,l}$ of each replica atmosphere, in dB, any shape; a `(N_atm, N_exc)` array is read row by row. |
| `probabilities` | The probability of occurrence of each replica, the same shape as `levels_db`, summing to one (see [`replica_probabilities`](/phonometry/reference/api/environment/exposure-distribution/#replica_probabilities)). |
| `sigma_db` | Standard deviation of the spread due to turbulence, in dB; 5 dB by default, the value clause 5 says is typically used. |
| `subclasses` | $N_\mathrm{sub}$, the subclasses per class; 10 by default, the number Annex A uses. The standard fixes none. |

**Returns:** The distribution.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the shapes differ, a value is not finite, a probability is negative, the probabilities do not sum to one, every probability is zero, fewer than two distinct levels remain once equal levels are combined, `sigma_db` is not positive, or `subclasses` is not a whole number of at least one. |

## SelDistribution

```python
SelDistribution(
    levels_db: NDArray[np.float64],
    probabilities: NDArray[np.float64],
    lower_bounds_db: NDArray[np.float64],
    upper_bounds_db: NDArray[np.float64],
    class_densities_per_db: NDArray[np.float64],
    subclass_centres_db: NDArray[np.float64],
    sigma_db: float,
    level_shift_db: float,
    subclasses: int,
    long_term_level_db: float,
    distribution_long_term_level_db: float,
    replicas: tuple[tuple[int, ...], ...],
)
```

The statistical distribution of a single-event sound exposure level
(ISO 13474:2009, clause 5).

The replica atmospheres, sorted by level, are the `M` classes of
Equations (10) to (16); each class is split into `subclasses` equal
subclasses (Equations (17) to (20)) and each subclass is replaced by a
normal distribution of standard deviation `sigma_db` centred
`level_shift_db` below the subclass centre (Equations (21) to (23)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{E,\mathrm{w},m}$ of the `M` classes, in increasing order, in dB. |
| `probabilities` | $\wp_m$ of each class (Equation (14)). |
| `lower_bounds_db` | $g_{\mathrm{L},m}$, in dB (Equations (11), (12)). |
| `upper_bounds_db` | $g_{\mathrm{U},m}$, in dB (Equations (11), (13)). |
| `class_densities_per_db` | $\rho_m$, the constant density of each class, in 1/dB (Equation (15)). |
| `subclass_centres_db` | $\mu_{m,j}$, shape `(M, subclasses)`, in dB (Equation (18)). |
| `sigma_db` | $\sigma$ of the turbulent spread, in dB. |
| `level_shift_db` | $\Delta\mu$, in dB (Equation (22)). |
| `subclasses` | $N_\mathrm{sub}$, the subclasses per class. |
| `long_term_level_db` | $\langle L_{E,\mathrm{w}}\rangle_\mathrm{LT}$ from the classes, Equation (7); Annex A's `LT1`. |
| `distribution_long_term_level_db` | the same average taken over the continuous distribution, Equation (A.4); Annex A's `LT2`. It differs from `long_term_level_db` only by the spreading of each class over its width, since $\Delta\mu$ preserves the energy of each subclass. |
| `replicas` | For each class, the flat indices of the replica atmospheres it holds, in the row-major order the input was given in; a class holds more than one only where equal levels were combined. |

### SelDistribution.class_density()

```python
SelDistribution.class_density(
    x_db: ArrayLike,
) -> float | NDArray[np.float64]
```

The class density $\rho(x)$ before the turbulent spread
(Equations (15), (16)), in 1/dB.

A step function, constant inside each class and zero outside the
classes; at a boundary itself, where Equation (15) defines neither
neighbour, it is zero.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x_db` | Level or levels `x`, in dB. |

**Returns:** $\rho(x)$, a float for a scalar `x`.

### SelDistribution.density()

```python
SelDistribution.density(x_db: ArrayLike) -> float | NDArray[np.float64]
```

The continuous density $\rho^{*}(x)$ (Equations (21), (23)), in 1/dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x_db` | Level or levels `x`, in dB. |

**Returns:** $\rho^{*}(x)$, a float for a scalar `x`.

### SelDistribution.exceedance()

```python
SelDistribution.exceedance(x_db: ArrayLike) -> float | NDArray[np.float64]
```

Probability that the level exceeds `x` (Equation (24)).

$$
\mathrm{P_r}(L_{E,\mathrm{w}} > x) = \int_x^{\infty} \rho^{*}(x')\,\mathrm{d}x'
$$

evaluated exactly as a sum of Gaussian upper-tail probabilities. It
tends to the sum of the probabilities of the classes, one, as `x`
falls.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x_db` | Level or levels `x`, in dB. |

**Returns:** The probability, a float for a scalar `x`.

### SelDistribution.exceedance_level()

```python
SelDistribution.exceedance_level(
    percent: ArrayLike,
) -> float | NDArray[np.float64]
```

The `n`-percent exceedance level $L_{E,\mathrm{w},n}$ (Equation (25)).

The level exceeded with probability `n / 100`: the root of
$\mathrm{P_r}(L_{E,\mathrm{w}} > x) = n/100$, found to 10⁻¹⁰ dB.
`exceedance_level(95)` is the level exceeded by 95 % of the events,
the lowest of the usual set; `exceedance_level(1)` the highest.

**Parameters**

| Name | Description |
| :--- | :--- |
| `percent` | `n`, in per cent, strictly between 0 and 100 times the total probability of the classes. |

**Returns:** The level, in dB, a float for a scalar `percent`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a percentage outside that range. |

### SelDistribution.plot()

```python
SelDistribution.plot(
    ax: Axes | None = None,
    *,
    view: str = 'density',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the distribution, as its class density, density or exceedance.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `view` | `"density"` (default) draws the continuous density $\rho^{*}(x)$ with the long-term level of Equation (A.4) marked, the curve of Annex A Figure A.2; `"classes"` draws the step density $\rho(x)$ of the classes before the turbulent spread, Figure A.1; `"exceedance"` draws $\mathrm{P_r}(L_{E,\mathrm{w}} > x)$ with the 95, 50, 10, 5 and 1 per cent exceedance levels marked, Figure A.3. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the primary artist. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `view` is not one of the three names above. |

## turbulence_level_shift

```python
turbulence_level_shift(sigma_db: float) -> float
```

Shift of the mean of each Gaussian subclass, $\Delta\mu$ (Equation (22)).

The shift that keeps the energetically averaged level of a subclass at its
centre once the subclass is spread by a normal distribution of standard
deviation $\sigma$. The integral of Equation (22) is the mean of a
lognormal variable and has the closed form

$$
\Delta\mu = \frac{\sigma^{2}\ln 10}{20}~\text{dB},
$$

2,878 dB for the 5 dB the standard says is typically used.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sigma_db` | The standard deviation $\sigma$ of the turbulent spread, in dB. |

**Returns:** $\Delta\mu$, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite `sigma_db`. |
