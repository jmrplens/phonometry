---
title: "hearing.noise_induced_hearing_loss"
description: "Public API of phonometry.hearing.noise_induced_hearing_loss (auto-generated)."
sidebar:
  label: "noise_induced_hearing_loss"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Estimation of noise-induced hearing loss (ISO 1999:2013).

Implements the noise-induced permanent threshold shift (NIPTS) of a
noise-exposed population and its combination with the age-related threshold
into the hearing threshold level associated with age and noise (HTLAN), over
the six audiometric frequencies 500 Hz to 6000 Hz.

The median NIPTS for exposure durations of 10 to 40 years is
`N50 = [u + v*lg(t/t0)] * (L_EX,8h - L0)**2` (clause 6.3.1, Formula 2, with
the values `u, v, L0` of Table 1), extrapolated below 10 years by Formula 3.
The statistical distribution about the median is two half-Gaussians whose
spreads `du` (worse than the median) and `dl` (better) follow Formulae 6/7
with the coefficients of Table 3; a population fractile is
`N50 + z * spread` with `z` the standard-normal quantile (clause 6.3.2,
Formulae 4/5, Table 2), clamped at zero. The HTLAN combines the age component
`H` (HTLA, database A = ISO 7029) with the noise component `N` by
`H' = H + N - H*N/120` (clause 6.1, Formula 1).

## htlan

```python
htlan(
    age: float,
    sex: Literal['male', 'female'],
    l_ex: float,
    years: float,
    fractile: float = 0.5,
    frequencies: ArrayLike | None = None,
) -> HtlanResult
```

Hearing threshold level associated with age and noise (clause 6.1).

Combines the age component `H` (HTLA from database A, i.e. ISO 7029, at
the same population fractile) with the noise component `N` (the NIPTS at
that fractile) by Formula (1): `H' = H + N - H*N/120`. The formula applies
to corresponding percentage values, so the same `fractile` drives both
components.

**Parameters**

| Name | Description |
| :--- | :--- |
| `age` | Listener age, in years (at least 18, the ISO 7029 lower limit). |
| `sex` | `"male"` or `"female"`. |
| `l_ex` | Noise exposure level normalized to 8 h, `L_EX,8h`, in dB. |
| `years` | Exposure duration, in years. |
| `fractile` | Population fractile in (0, 1) applied to both components. |
| `frequencies` | Optional subset of the audiometric frequencies, in hertz; `None` uses all six (500 Hz - 6000 Hz). |

**Returns:** An [`HtlanResult`](/phonometry/reference/api/hearing/noise-induced-hearing-loss/#htlanresult) with `htla`, `nipts`, `threshold` and `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an age below 18, an unknown sex, a non-positive duration, a fractile outside (0, 1), or an unknown frequency. |

## HtlanResult

```python
HtlanResult(
    age: float,
    sex: str,
    l_ex: float,
    years: float,
    fractile: float,
    frequencies: np.ndarray,
    htla: np.ndarray,
    nipts: np.ndarray,
    threshold: np.ndarray,
)
```

Hearing threshold level associated with age and noise (clause 6.1).

All arrays are in dB and aligned with `NIPTS_FREQUENCIES`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `age` | Listener age, in years. |
| `sex` | `"male"` or `"female"`. |
| `l_ex` | Noise exposure level normalized to 8 h, in dB. |
| `years` | Exposure duration, in years. |
| `fractile` | Population fractile (0-1) applied to both components. |
| `frequencies` | Audiometric frequencies, in hertz. |
| `htla` | Age component `H` (HTLA, database A = ISO 7029). |
| `nipts` | Noise component `N` (NIPTS at `fractile`). |
| `threshold` | Combined HTLAN `H' = H + N - H*N/120`. |

### HtlanResult.plot()

```python
HtlanResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the age, noise and combined threshold components over frequency.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## nipts

```python
nipts(
    l_ex: float,
    years: float,
    fractile: float = 0.5,
    frequencies: ArrayLike | None = None,
) -> NiptsResult
```

Noise-induced permanent threshold shift (ISO 1999:2013, clause 6.3).

Returns, per audiometric frequency, the median NIPTS `N50` (Formula 2,
extrapolated below 10 years by Formula 3), the upper/lower spreads
`du`/`dl` (Formulae 6/7) and the NIPTS at the requested population
`fractile` (Formulae 4/5): `N50 + z * spread` where `z` is the
standard-normal quantile of `fractile` and the spread is the upper one for
`z >= 0` (worse than the median) or the lower one otherwise, clamped at
zero.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_ex` | Noise exposure level normalized to a nominal 8 h working day, `L_EX,8h`, in dB. |
| `years` | Exposure duration, in years (> 0; the standard establishes 10-40 years and extrapolates 1-10 years by Formula 3, below 1 year the result is a further extrapolation). |
| `fractile` | Population fractile in the open interval (0, 1); `0.5` gives the median. The reliable range of the standard is 0.05-0.95. |
| `frequencies` | Optional subset of the audiometric frequencies, in hertz; `None` uses all six (500 Hz - 6000 Hz). |

**Returns:** A [`NiptsResult`](/phonometry/reference/api/hearing/noise-induced-hearing-loss/#niptsresult) with the distribution and `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive duration, a fractile outside (0, 1), or an unknown frequency. |

## NiptsResult

```python
NiptsResult(
    l_ex: float,
    years: float,
    fractile: float,
    frequencies: np.ndarray,
    median: np.ndarray,
    value: np.ndarray,
    spread_upper: np.ndarray,
    spread_lower: np.ndarray,
)
```

Noise-induced permanent threshold shift (ISO 1999:2013, clause 6.3).

All arrays are in dB and aligned with `NIPTS_FREQUENCIES`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `l_ex` | Noise exposure level normalized to 8 h, `L_EX,8h`, in dB. |
| `years` | Exposure duration, in years. |
| `fractile` | Population fractile of `value` (0-1); the fraction of the population with a smaller shift, so `0.9` is the most-susceptible 10 %. |
| `frequencies` | Audiometric frequencies, in hertz. |
| `median` | Median NIPTS `N50` (Formula 2/3). |
| `value` | NIPTS at `fractile` (Formula 4/5), clamped at zero. |
| `spread_upper` | Upper half-Gaussian spread `du` (Formula 6). |
| `spread_lower` | Lower half-Gaussian spread `dl` (Formula 7). |

### NiptsResult.plot()

```python
NiptsResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the NIPTS spectrum with the fractile band over frequency.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.
