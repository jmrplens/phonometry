---
title: "filters.time_invariance"
description: "The exponential-sweep test of a band filter: time-invariant operation."
sidebar:
  label: "time_invariance"
---

The exponential-sweep test of a band filter: time-invariant operation.

IEC 61260-1:2014 5.14 asks a set of filters that claims time-invariant
operation to pass a test a transfer function cannot: driven by a
constant-amplitude sinusoid whose frequency rises at an exponential rate, each
filter's time-averaged output shall stay within $\pm 0.4$ dB (class 1)
or $\pm 0.6$ dB (class 2) of the level Formula (17) predicts,

$$
L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[ \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\, \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right]\ \mathrm{dB},
$$

for a sweep of one decade in 2 s to 5 s (5.14.3). Annex G derives it: the time
average of the swept output is the effective bandwidth over the sweep rate, so
a filter whose effective bandwidth is the reference one ($B_\mathrm{e} = B_\mathrm{r}$) reads exactly $L_\mathrm{c}$ (G.2.8). IEC 61260-2:2016
7.4 is the pattern-evaluation test and IEC 61260-3:2016 10.3 uses the same
sweep to measure the effective bandwidth deviation of a time-invariant filter
in a periodic test.

This module has three things for it:

* [`swept_band_level`](/phonometry/reference/api/filters/time-invariance/#swept_band_level), Formula (17) itself, which IEC 61260-2 and -3
  Annex B work through to $L_\mathrm{c} = 107.97$ dB;
* [`swept_level_uncertainty`](/phonometry/reference/api/filters/time-invariance/#swept_level_uncertainty), the standard uncertainty of that level
  from the uncertainties of the sweep (Annex A of IEC 61260-2 and -3,
  Formula (A.2)); the annexes print $u = 0.057$ dB for their example,
  which this reproduces, while the printed Formula (A.2) drops the square on
  the coefficient of its frequency terms (see the errata registry);
* [`verify_time_invariance`](/phonometry/reference/api/filters/time-invariance/#verify_time_invariance), the test run on an
  [`OctaveFilterBank`](/phonometry/reference/api/filters/core/#octavefilterbank): the sweep of Formulas (A.3)
  and (A.4) goes through every band exactly as the bank filters a signal, the
  polyphase decimation of a multirate bank included, so it tests what the
  transfer functions alone cannot.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## swept_band_level

```python
swept_band_level(
    input_level_db: float,
    *,
    fraction: float,
    sweep_duration_s: float,
    averaging_time_s: float,
    start_frequency_hz: float,
    end_frequency_hz: float,
    reference_attenuation_db: float = 0.0,
) -> float
```

IEC 61260-1:2014 Formula (17): the time-averaged output of a sweep.

$$
L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[ \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\, \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right]
$$

with $\lg(f_2/f_1) = 3/(10b)$ for a base-ten filter of bandwidth
designator $1/b$ (NOTE 1 to 5.14.2): the level an exponential sweep
of constant amplitude leaves, averaged over $T_\mathrm{avg}$, at the
output of a filter whose relative attenuation is zero in its pass band and
infinite outside it (NOTE 2). The deviation of a measured output from it
is what 5.14.3 and IEC 61260-3:2016 10.3.6 grade.

**Parameters**

| Name | Description |
| :--- | :--- |
| `input_level_db` | $L_\mathrm{in}$, the level of the sweep. |
| `fraction` | The bandwidth designator denominator `b`. |
| `sweep_duration_s` | $T_\mathrm{sweep}$, the time from the start frequency to the end frequency. |
| `averaging_time_s` | $T_\mathrm{avg}$, the averaging time of the output level. |
| `start_frequency_hz` | $f_\mathrm{start}$. |
| `end_frequency_hz` | $f_\mathrm{end}$, above the start. |
| `reference_attenuation_db` | $A_\mathrm{ref}$, the reference attenuation of 5.9 (0 dB by default). |

**Returns:** $L_\mathrm{c}$ in the unit of `input_level_db`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive bandwidth designator, duration, averaging time or frequency, or an end frequency not above the start. |

## swept_level_uncertainty

```python
swept_level_uncertainty(
    *,
    input_level_uncertainty_db: float,
    sweep_duration_s: float,
    sweep_duration_uncertainty_s: float,
    averaging_time_s: float,
    averaging_time_uncertainty_s: float,
    start_frequency_hz: float,
    start_frequency_uncertainty_hz: float,
    end_frequency_hz: float,
    end_frequency_uncertainty_hz: float,
    display_resolution_db: float = 0.0,
) -> float
```

The standard uncertainty of [`swept_band_level`](/phonometry/reference/api/filters/time-invariance/#swept_band_level), from the sweep.

Annex A of IEC 61260-2:2016 and of IEC 61260-3:2016 propagates the
standard uncertainties of the input level, the sweep time, the averaging
time and the two end frequencies through Formula (17) (A.1):

$$
u_{L_\mathrm{c}}^2 = u_{L_\mathrm{in}}^2 + \left(\frac{10}{\ln 10}\right)^2 \left[ \left(\frac{u_{T_\mathrm{sweep}}}{T_\mathrm{sweep}}\right)^2 + \left(\frac{u_{T_\mathrm{avg}}}{T_\mathrm{avg}}\right)^2\right] + \left(\frac{10}{\ln(f_\mathrm{end}/f_\mathrm{start})\,\ln 10} \right)^2 \left[ \left(\frac{u_{f_\mathrm{end}}}{f_\mathrm{end}}\right)^2 + \left(\frac{u_{f_\mathrm{start}}}{f_\mathrm{start}}\right)^2\right]
$$

Formula (A.2) as printed in both parts leaves the square off the
coefficient of the frequency terms; the square is what the derivative of
Formula (17) gives, and it is the only reading that reproduces the
annexes' own example (A.3.5): $u_{L_\mathrm{c}} \approx 0.057$ dB and
an expanded uncertainty of 0.115 dB, where the printed form gives
0.075 dB. See the errata registry.

A reading taken from a display adds its resolution as a rectangular
distribution of half-width half the resolution (IEC 61260-3:2016 5.2):
`display_resolution_db=0.1` turns the example's 0.115 dB into the
0.128 dB of A.3.5.

**Parameters**

| Name | Description |
| :--- | :--- |
| `input_level_uncertainty_db` | $u_{L_\mathrm{in}}$, standard. |
| `sweep_duration_s` | $T_\mathrm{sweep}$. |
| `sweep_duration_uncertainty_s` | Its standard uncertainty. |
| `averaging_time_s` | $T_\mathrm{avg}$. |
| `averaging_time_uncertainty_s` | Its standard uncertainty. |
| `start_frequency_hz` | $f_\mathrm{start}$. |
| `start_frequency_uncertainty_hz` | Its standard uncertainty. |
| `end_frequency_hz` | $f_\mathrm{end}$, above the start. |
| `end_frequency_uncertainty_hz` | Its standard uncertainty. |
| `display_resolution_db` | The resolution of the display the output level is read from, 0 when it is not read from one. |

**Returns:** $u_{L_\mathrm{c}}$, the standard uncertainty in dB; the annexes expand it with a coverage factor of 2.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a negative uncertainty or resolution, a non-positive duration or frequency, or an end frequency not above the start. |

## TimeInvarianceResult

```python
TimeInvarianceResult(
    band_frequencies: np.ndarray,
    fraction: float,
    fs: float,
    seconds_per_decade: tuple[float, ...],
    start_frequency_hz: float,
    end_frequency_hz: float,
    sweep_durations_s: tuple[float, ...],
    averaging_times_s: tuple[float, ...],
    output_levels_db: np.ndarray,
    expected_levels_db: np.ndarray,
)
```

The time-invariance verdict of a filter bank, IEC 61260-1:2014 5.14.

What [`verify_time_invariance`](/phonometry/reference/api/filters/time-invariance/#verify_time_invariance) returns. For every sweep rate and
every band it holds the time-averaged output level of the bank driven by
an exponential sweep and the level Formula (17) predicts for it,

$$
L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[ \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\, \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right],
$$

whose difference 5.14.3 bounds by $\pm 0.4$ dB for class 1 and
$\pm 0.6$ dB for class 2. The levels are in decibels relative to
the level of the input sweep, whose effective value is 1 (IEC 61260-2
Formula (A.4)), so $L_\mathrm{in} = 0$ dB.

**Attributes**

| Name | Description |
| :--- | :--- |
| `band_frequencies` | The exact mid-band frequencies, Hz. |
| `fraction` | The bandwidth designator denominator `b`. |
| `fs` | The bank's sampling rate, Hz. |
| `seconds_per_decade` | The sweep rates, one decade in so many seconds. |
| `start_frequency_hz` | $f_\mathrm{start}$ of every sweep. |
| `end_frequency_hz` | $f_\mathrm{end}$ of every sweep. |
| `sweep_durations_s` | $T_\mathrm{sweep}$, one per rate. |
| `averaging_times_s` | $T_\mathrm{avg}$, one per rate: the sweep and the silence after it during which the slowest band's output dies away. |
| `output_levels_db` | The measured time-averaged output level $L_\mathrm{out}$, shape `(rates, bands)`. |
| `expected_levels_db` | $L_\mathrm{c}$ of Formula (17), same shape. |

### TimeInvarianceResult.band_classes

*property*

The strictest class each band meets at every sweep rate.

### TimeInvarianceResult.deviations_db

*property*

$L_\mathrm{out} - L_\mathrm{c}$, shape `(rates, bands)`.

### TimeInvarianceResult.overall_class

*property*

The strictest class every band meets, `None` if one meets none.

### TimeInvarianceResult.plot()

```python
TimeInvarianceResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot every band's deviation from Formula (17), one line per rate.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.filters.plot_time_invariance`. |

### TimeInvarianceResult.worst_deviation_db

*property*

The deviation of largest magnitude, signed, over bands and rates.

## verify_time_invariance

```python
verify_time_invariance(
    bank: OctaveFilterBank,
    *,
    seconds_per_decade: tuple[float, ...] = (2.0, 5.0),
) -> TimeInvarianceResult
```

Test the time-invariant operation of a bank, IEC 61260-1:2014 5.14.

The swept-frequency test of IEC 61260-2:2016 7.4, run on the bank itself:
an exponential sweep of effective value 1 (Formulas (A.3) and (A.4))
goes through every band exactly as [`OctaveFilterBank.filter`](/phonometry/reference/api/filters/core/#octavefilterbankfilter)
processes it, the polyphase decimation of a multirate bank included, and
each band's time-averaged output is compared with the level
$L_\mathrm{c}$ of Formula (17). A bank whose bands do what their
transfer functions say reads, band by band, its effective bandwidth
deviation (Annex G, G.2.8); decimation that folds energy back into a
band, or state that is not carried from one sample to the next, reads as
more.

* The sweep starts one decade below the frequency at which the lowest
  band's relative attenuation reaches 55 dB below its lower band edge,
  and ends one decade above the matching point of the highest band, or
  at the Nyquist frequency if that comes first (7.4.2 asks for "at
  least" 55 dB; the extra decade keeps the start transient of the sweep
  out of the lowest band).
* The averaging runs from the start of the sweep until the slowest
  band's impulse response has lost all but $10^{-9}$ of its energy
  after the sweep ends (7.4.4).
* The reference attenuation is each band's attenuation at its exact
  mid-band frequency, as [`verify_filter_class`](/phonometry/reference/api/filters/compliance/#verify_filter_class) takes it.

A time-invariant design is an optional claim: 5.14.4 has the instruction
manual state the bandwidths and frequency ranges it applies to, and the
verdict here is for the bank as configured.

**Parameters**

| Name | Description |
| :--- | :--- |
| `bank` | The filter bank; its designed sections and decimation factors are run, and a stateful bank's carried state is left alone. |
| `seconds_per_decade` | The sweep rates to run, one decade in so many seconds, each within the 2 s to 5 s for which 5.14.3 sets its limits. The default runs both ends of that range. |

**Returns:** A [`TimeInvarianceResult`](/phonometry/reference/api/filters/time-invariance/#timeinvarianceresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no sweep rate, a rate outside 2 s to 5 s per decade, or a bank with no bands. |
