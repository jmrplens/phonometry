---
title: "vibration.structural.impact_mobility"
description: "Mechanical mobility measured by impact excitation (ISO 7626-5:2019)."
sidebar:
  label: "impact_mobility"
---

Mechanical mobility measured by impact excitation (ISO 7626-5:2019).

ISO 7626-5 measures the same frequency-response functions as ISO 7626-2, but
excites the structure with a hammer or another impactor that is not attached
to it. Each record holds one impact and the free decay it leaves behind, and
that shape is what the part is about: the force occupies a small fraction of
the record, so the noise around it matters (8.5.1); the response may not have
died away by the end of the record, so the spectrum leaks (8.3, 8.5.2); a
second impact inside the record cuts notches into the force spectrum (6.4);
and the averaging runs over impacts rather than over segments of one long
record (8.6). This module holds those pieces and reuses the FRF machinery of
`.mechanical_mobility` for the rest.

**Spectra.** The records are sampled at `fs` and transformed with the
discrete Fourier transform scaled by the sampling interval,
$X(f_k) = \Delta t \sum_n x_n e^{-j 2\pi k n / N}$, which for a transient
wholly inside the record samples its continuous Fourier transform (8.3). The
force energy spectral density is $G_{FF} = 2 \lvert F(f) \rvert^2$, in
N²·s/Hz: the power spectral density of 3.3, $2 \lvert F \rvert^2 / T$,
multiplied by the record length as 3.4 prescribes.

**Averaging (8.6).** Over $n$ impacts at one point the estimate is the
averaged cross-spectrum of response and force divided by the averaged
auto-spectrum of the force,

$$
H = \frac{\sum_i X_i F_i^{*}}{\sum_i \lvert F_i \rvert^2}, \qquad \gamma^2 = \frac{\lvert \sum_i X_i F_i^{*} \rvert^2} {\sum_i \lvert F_i \rvert^2 \sum_i \lvert X_i \rvert^2}
$$

with the ordinary coherence $\gamma^2$ of 9.1 beside it. The FRF comes
out in the kind of the response channel (accelerance, mobility or dynamic
compliance) and is converted to mobility with [`.convert_frf`](/phonometry/reference/api/vibration/mechanical-mobility/#convert_frf).

**Windows (8.5).** The *force window* has unity gain over the part of the
record that holds the force pulse and its filter response and sets the rest to
exactly zero (8.5.1). The *exponential window*
$w(t) = e^{-a t}$ starts at unity and adds a known decay to the data
(8.3 a), 8.5.2). Applied to force and response alike, it replaces every pole
$s_r$ of the impulse response by $s_r - a$ (Annex A, Formula
(A.2)), so a mode appears more damped than it is, and Formula (A.3) takes the
added damping away again:

$$
\zeta_r = \hat{\zeta}_r - \frac{a}{\omega_r}
$$

with $\hat\zeta_r$ the damping ratio estimated from the windowed data and
$\omega_r$ the damped natural frequency in rad/s. The corrected mobility
is synthesized from the corrected modes, and for a lightly damped, well
separated mode the measured peak is multiplied by
$\hat\zeta_r / \zeta_r$. Annex A leaves the damping estimator open;
[`single_mode_fit`](/phonometry/reference/api/vibration/impact-mobility/#single_mode_fit) is the one this library offers, a rational-fraction
fit of one mode over a band.

Formula (A.3) is the first-order form of the pole shift the annex states in
words. The synthesis here moves the pole itself, which is exact, and the
correction reports both: [`ExponentialWindowCorrection.damping_ratio`](/phonometry/reference/api/vibration/impact-mobility/#exponentialwindowcorrectiondamping_ratio) is
(A.3) as printed and [`ExponentialWindowCorrection.exact_damping_ratio`](/phonometry/reference/api/vibration/impact-mobility/#exponentialwindowcorrectionexact_damping_ratio)
is the damping of the shifted pole; they differ by about
$(\hat\zeta_r^3 - \zeta_r^3)/2$.

**Records.** Every function that takes a record takes a bare array with its
sample rate, or a [`Signal`](/phonometry/reference/api/io/io/#signal), which brings its own rate
(an explicit `fs` that disagrees is refused). A calibration factor the
Signal carries is deliberately not applied: the records of this part are
forces in newtons and motions in m/s², m/s or m, not pressures. The checks
hand the samples they judged back as bare arrays, in the unit they arrived
in.

**Checks.** Every record check returns a verdict object with `passes`:
[`check_double_hit`](/phonometry/reference/api/vibration/impact-mobility/#check_double_hit) (6.4), [`check_force_spectrum`](/phonometry/reference/api/vibration/impact-mobility/#check_force_spectrum) (6.2, 6.3),
[`check_overload`](/phonometry/reference/api/vibration/impact-mobility/#check_overload) (8.4), [`check_response_decay`](/phonometry/reference/api/vibration/impact-mobility/#check_response_decay) (8.3, 8.5.2) and
[`check_coherence`](/phonometry/reference/api/vibration/impact-mobility/#check_coherence) (9.1); [`verify_channel_match`](/phonometry/reference/api/vibration/impact-mobility/#verify_channel_match) judges the
channel-to-channel match of the analyser (8.1). The operational calibration of
7.2 is the rigid-mass check of ISO 7626-2:2015, 7.5.2, which 7.2 calls
essentially the same procedure: [`.rigid_mass_calibration_check`](/phonometry/reference/api/vibration/mechanical-mobility/#rigid_mass_calibration_check).

The part prints no worked example, so the implementation is anchored in closed
form: a single-degree-of-freedom structure struck by a smooth pulse gives its
mobility back from the averaged estimate, and its damping and mobility back
after exponential windowing and the Annex A correction.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## CHANNEL_MAGNITUDE_TOLERANCE

*Constant* (`float`).

```python
CHANNEL_MAGNITUDE_TOLERANCE = 0.05
```

## CHANNEL_PHASE_TOLERANCE_DEG

*Constant* (`float`).

```python
CHANNEL_PHASE_TOLERANCE_DEG = 5.0
```

## ChannelMatchVerification

```python
ChannelMatchVerification(frequencies: np.ndarray, response: np.ndarray)
```

Do two analyser channels match in gain and phase? (8.1)

The channel-to-channel match of the filters and the analyser is checked by
connecting one broad-band signal to both channels and measuring the
frequency response between them: its magnitude should equal unity within
+/- 5 % over the frequency range of interest and its phase zero within
+/- 5 degrees (8.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies in the range of interest, in hertz. |
| `response` | Complex frequency response between the channels. |

### ChannelMatchVerification.magnitude_deviation

*property*

Relative deviation of the magnitude from unity, `|H| - 1`.

### ChannelMatchVerification.magnitude_within

*property*

Per frequency, whether the magnitude is within +/- 5 % of unity.

The magnitude is compared with the bounds `1 - 0,05` and
`1 + 0,05` themselves, so a response of exactly 0,95 or 1,05 is
within them.

### ChannelMatchVerification.passes

*property*

Whether both requirements hold at every frequency.

### ChannelMatchVerification.phase_deg

*property*

Phase of the response, in degrees.

### ChannelMatchVerification.phase_within

*property*

Per frequency, whether the phase is within +/- 5 degrees of zero.

### ChannelMatchVerification.plot()

```python
ChannelMatchVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes | np.ndarray
```

Plot the magnitude and phase deviations against their tolerances.

With no `ax` a two-panel figure is drawn; with `ax` only the
magnitude deviation.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the magnitude-deviation curve. |

**Returns:** The axes, or the two-axes array.

## check_coherence

```python
check_coherence(
    result: ImpactMobilityResult,
    *,
    frequency_range_hz: tuple[float, float],
    exclude_hz: Sequence[tuple[float, float]] = (),
    minimum_coherence: float = 0.9,
    minimum_records: int = 5,
) -> CoherenceCheck
```

Is the averaged estimate's coherence high over the range of interest? (9.1)

The check passes when the coherence exceeds `minimum_coherence` (0,9,
what 9.1 calls high) at every frequency of the range that is not excluded,
and at least `minimum_records` impacts were averaged (five, the lower end
of the five to ten 9.1 says a high coherence needs). A single impact has a
coherence of 1 by construction and fails the second condition.

8.6 finds three to five impacts usually enough to verify data quality in a
low-noise environment; the coherence estimate itself, 9.1 adds, needs five
to ten records to be trusted. Averaging five impacts satisfies both, and a
lower `minimum_records` states that fewer were judged enough.

**Parameters**

| Name | Description |
| :--- | :--- |
| `result` | The averaged estimate, from [`impact_mobility`](/phonometry/reference/api/vibration/impact-mobility/#impact_mobility). |
| `frequency_range_hz` | `(f_low, f_high)`, in hertz. |
| `exclude_hz` | Bands `(f_low, f_high)` to leave out of the verdict, such as anti-resonances (9.1, NOTE 1) (Default: none). |
| `minimum_coherence` | The coherence to exceed (Default: 0.9). |
| `minimum_records` | The fewest impacts to accept, a whole number of at least 1 (Default: 5). |

**Returns:** A [`CoherenceCheck`](/phonometry/reference/api/vibration/impact-mobility/#coherencecheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an invalid range, exclusion or limit, a `minimum_records` that is not a whole number of at least 1, or exclusions that leave no frequency of the range to judge. |

## check_double_hit

```python
check_double_hit(
    force: SignalInput,
    fs: float | None = None,
    *,
    threshold_ratio: float = 0.1,
) -> DoubleHitCheck
```

Does the force record hold one impact, or a double hit? (6.4)

An impact is a run of samples whose force exceeds `threshold_ratio`
times the largest force in the record, in the direction of that largest
force; the check passes when there is exactly one. Run it on the
unwindowed, and preferably unfiltered, force: 6.4 recommends watching the
unfiltered signal so the anti-aliasing filter does not hide a secondary
impact in the ringing of the primary one, and forbids using a force window
to remove one.

The threshold is this library's, not the part's, which only says that a
small second impact shows as a slight ripple and that moderate dips may be
tolerated. At the default of 0,1 an undetected second pulse of the same
shape as the first ripples the force spectrum by at most
$20 \log_{10}(1{,}1/0{,}9) = 1{,}74$ dB peak to notch
([`DoubleHitCheck.ripple_db`](/phonometry/reference/api/vibration/impact-mobility/#doublehitcheckripple_db)). A softer, longer rebound, the usual
hammer bounce, carries more of the low-frequency spectrum than its peak
says: it can stay under the threshold and still ripple the spectrum by
several decibels. That is why 6.4 finds multiple impacts most easily in
the frequency domain, which [`check_force_spectrum`](/phonometry/reference/api/vibration/impact-mobility/#check_force_spectrum) reads.

A filtered record has a limit of its own. When the spectrum of the pulse
reaches the cut-off of the anti-aliasing filter, the ringing the filter
leaves after the pulse can itself rise above the threshold, most of all
with a steep elliptic or Chebyshev filter, and a single impact then reads
as several. The unfiltered force avoids both effects.

**Parameters**

| Name | Description |
| :--- | :--- |
| `force` | One force record, 1-D, in N. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) for its rate; a calibration factor it carries is deliberately not applied, because this record is a force in newtons and not a pressure. |
| `fs` | Sample rate, in Hz. Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises instead of silently winning. |
| `threshold_ratio` | Fraction of the largest force an excursion must exceed to count as an impact, in (0, 1) (Default: 0.1). |

**Returns:** A [`DoubleHitCheck`](/phonometry/reference/api/vibration/impact-mobility/#doublehitcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a record that is not 1-D and finite, a non-positive sample rate, a threshold outside (0, 1), or a record with no force in it. |

## check_force_spectrum

```python
check_force_spectrum(
    force: SignalInput,
    fs: float | None = None,
    *,
    frequency_range_hz: tuple[float, float],
    max_drop_db: float,
) -> ForceSpectrumCheck
```

Is the force spectrum flat enough across the frequency range of interest?

Computes the energy spectral density of one force record (3.3, 3.4) and
reads how far it falls between its highest and lowest value inside the
range. The check passes when that fall is at most `max_drop_db`. The part
gives no number for it, so the caller states the one their practice uses;
the share of force energy above the range, which 6.3 asks to keep small, is
reported beside it as [`ForceSpectrumCheck.energy_fraction_above`](/phonometry/reference/api/vibration/impact-mobility/#forcespectrumcheckenergy_fraction_above).

**Parameters**

| Name | Description |
| :--- | :--- |
| `force` | One force record, 1-D, in N (windowed or not, as it will be processed). Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) for its rate; a calibration factor it carries is deliberately not applied, because this record is a force in newtons and not a pressure. |
| `fs` | Sample rate, in Hz. Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises instead of silently winning. |
| `frequency_range_hz` | `(f_low, f_high)`, the frequency range of interest, in hertz. |
| `max_drop_db` | The largest fall across the range to accept, in dB. |

**Returns:** A [`ForceSpectrumCheck`](/phonometry/reference/api/vibration/impact-mobility/#forcespectrumcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an invalid record, sample rate, range or limit. |

## check_overload

```python
check_overload(
    record: SignalInput,
    fs: float | None = None,
    *,
    full_scale: float,
) -> OverloadCheck
```

Did one channel of the record stay below its full scale? (8.4)

**Parameters**

| Name | Description |
| :--- | :--- |
| `record` | One record, 1-D, in any unit. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) for its rate; a calibration factor it carries is deliberately not applied, so the samples stay in the unit the channel recorded them in, the unit of its full scale. |
| `fs` | Sample rate, in Hz. Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises instead of silently winning. |
| `full_scale` | The manufacturer's maximum for linear operation, in the unit of the record. |

**Returns:** An [`OverloadCheck`](/phonometry/reference/api/vibration/impact-mobility/#overloadcheck), which passes when every sample stays strictly below the full scale.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an invalid record, sample rate or full scale. |

## check_response_decay

```python
check_response_decay(
    response: SignalInput,
    fs: float | None = None,
    *,
    exponential_window: bool = False,
    segment_s: float | None = None,
    start_s: float = 0.0,
    force: SignalInput | None = None,
) -> ResponseDecayCheck
```

Has the response decayed enough by the end of the record? (8.3, 8.5.2)

Without an exponential window the response should end at about 1 % of its
highest peak (8.3, 8.5.2); with one, its natural decay should reach 25 % or
less, the general guideline of 8.5.2. The level at the end is read at the
last sample and compared with the figure to a whole per cent, so any
level below 1,5 % passes "about 1 %" (see [`ResponseDecayCheck`](/phonometry/reference/api/vibration/impact-mobility/#responsedecaycheck)).
8.3 calls the 1 % a compromise, and the check is one-sided: it asks
whether the response has decayed far enough, not whether it decayed too
far. Pass the response as recorded, before any window.

**Parameters**

| Name | Description |
| :--- | :--- |
| `response` | One response record, 1-D, in any unit. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) for its rate; a calibration factor it carries is deliberately not applied, because this record is a motion and not a pressure. |
| `fs` | Sample rate, in Hz. Required when the records are bare arrays; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value, or a force Signal, that disagrees with it raises instead of silently winning. |
| `exponential_window` | Whether the record is to be processed with an exponential window (Default: `False`). |
| `segment_s` | Length of the segments the levels are read over, in seconds; make it at least one period of the lowest mode (Default: `None`, one tenth of the record). |
| `start_s` | Time from which the highest peak is sought, in seconds (Default: 0, the whole record, as the clause reads). |
| `force` | The force record of the same impact, same length (Default: `None`). When given, the highest peak is sought only after the force pulse, where the force has fallen back to 1 % of its peak, so a driving-point acceleration is judged on its free decay and not on the impact it follows (the mass line). The later of this and `start_s` is used. A Signal likewise, its factor not applied. |

**Returns:** A [`ResponseDecayCheck`](/phonometry/reference/api/vibration/impact-mobility/#responsedecaycheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an invalid record, sample rate, segment or start, a response that is zero at every sample or at every sample from the start on (a dead channel has measured nothing, so it has not decayed either), or a force record of another length, without force or whose pulse does not end inside the record. |

## COHERENCE_RECORDS

*Constant* (`int`).

```python
COHERENCE_RECORDS = 5
```

## CoherenceCheck

```python
CoherenceCheck(
    frequencies: np.ndarray,
    coherence: np.ndarray,
    judged: np.ndarray,
    *,
    impacts: int,
    minimum_coherence: float = 0.9,
    minimum_records: int = 5,
)
```

Is the coherence high, over enough impacts to trust it? (9.1)

The coherence expresses how linearly the response follows the force at
each frequency; a value below 1 flags possible poor data (9.1). The clause
calls a coherence above 0,9 high, and says only a few records, five to
ten, are then needed for high statistical confidence in its estimate.
NOTE 1 adds that low coherence at an anti-resonance is not generally a
concern: the response is near the noise floor there. Such frequencies can
be excluded from the judgement.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies in the range of interest, in hertz. |
| `coherence` | Ordinary coherence $\gamma^2$ at each. |
| `judged` | Per frequency, whether it enters the verdict (`False` where excluded as an anti-resonance). |
| `impacts` | Number of impacts averaged. |
| `minimum_coherence` | The coherence each judged frequency must exceed. |
| `minimum_records` | The fewest impacts the check accepts. |

### CoherenceCheck.enough_records

*property*

Whether enough impacts were averaged for the coherence to be trusted.

### CoherenceCheck.high

*property*

Per frequency, whether the coherence exceeds the minimum.

### CoherenceCheck.passes

*property*

Whether every judged frequency is high and the records are enough.

### CoherenceCheck.plot()

```python
CoherenceCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the coherence against its minimum, excluded frequencies shaded.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the coherence curve. |

**Returns:** The axes.

### CoherenceCheck.random_error_percent

*property*

Normalized random error of the FRF magnitude, in percent (ISO 7626-2 Annex A).

NaN where the coherence is zero.

## DoubleHitCheck

```python
DoubleHitCheck(
    force: np.ndarray,
    fs: float,
    impact_indices: np.ndarray,
    *,
    threshold_ratio: float,
)
```

Was there more than one impact in the force record? (ISO 7626-5, 6.4)

If more than a single impact occurs within the record, the Fourier
transforms of the pulses tend to cancel at certain frequencies and cut
sharp notches into the force spectrum (Figure 5), where the low
signal-to-noise ratio spoils the mobility. For two pulses of the same
shape, the second $r$ times the first and $\tau$ later, the
spectrum is the single pulse's times $1 + r e^{-j\omega\tau}$: it
ripples with a period of $1/\tau$ in frequency between
$1 + r$ and $1 - r$, so the notches are deep only when the
second impact is about as strong as the first. That is why 6.4 says a small
second impact shows as a slight ripple, and why moderate dips "may normally
be tolerated".

**Attributes**

| Name | Description |
| :--- | :--- |
| `force` | The force record judged, in N, as a bare array (a [`Signal`](/phonometry/reference/api/io/io/#signal) passed in is read without its calibration factor, and its samples are what is kept). |
| `fs` | Its sample rate, in Hz. |
| `impact_indices` | Sample index of the peak of every impact found, in time order; the first entry is not necessarily the largest. |
| `threshold_ratio` | The fraction of the largest peak an excursion had to exceed to count as an impact. |

### DoubleHitCheck.delay_s

*property*

Time from the primary impact to the largest secondary one, in s.

`None` for a single impact.

### DoubleHitCheck.impact_peaks

*property*

Force at the peak of every impact, in N.

### DoubleHitCheck.impact_times_s

*property*

Time of the peak of every impact, in seconds.

### DoubleHitCheck.impacts

*property*

How many impacts the record holds.

### DoubleHitCheck.notch_spacing_hz

*property*

Spacing of the notches the two largest impacts cut, $1/\tau$.

`None` for a single impact.

### DoubleHitCheck.passes

*property*

Whether the record holds a single impact.

### DoubleHitCheck.plot()

```python
DoubleHitCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes | np.ndarray
```

Plot the force record with its impacts, and its energy spectral density.

With no `ax` a two-panel figure is drawn: the time history with every
impact marked, and the energy spectral density with the notches the two
largest impacts cut (Figure 5). With `ax` only the time history is
drawn on it.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the force curve. |

**Returns:** The axes, or the two-axes array.

### DoubleHitCheck.ripple_db

*property*

Peak-to-notch ripple of the force spectrum, in dB.

$20 \log_{10}[(1 + r)/(1 - r)]$ for a secondary impact `r`
times the primary one, the same shape and the only other; 0 dB for a
single impact and infinite for two equal ones, whose notches go to
zero.

### DoubleHitCheck.secondary_ratio

*property*

Largest secondary peak over the primary one (0 for a single impact).

### DoubleHitCheck.times

*property*

Time of every sample of the record, in seconds.

## energy_spectral_density

```python
energy_spectral_density(
    record: SignalInput,
    fs: float | None = None,
) -> tuple[np.ndarray, np.ndarray]
```

One-sided energy spectral density of a transient record (3.3, 3.4).

$G = 2 \lvert X(f) \rvert^2$, with $X(f)$ the discrete Fourier
transform scaled by the sampling interval: the power spectral density of
3.3, $2 \lvert X \rvert^2 / T$, multiplied by the record length
$T$ as 3.4 prescribes for a transient wholly inside the record. For a
force in newtons the unit is N²·s/Hz, the unit of Figures 3, 4, 5, 7 and 8.
The DC bin and, for an even record, the Nyquist bin are not doubled.

**Parameters**

| Name | Description |
| :--- | :--- |
| `record` | One record, 1-D. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal) for its rate; a calibration factor it carries is not applied. |
| `fs` | Sample rate, in Hz. Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises instead of silently winning. |

**Returns:** `(frequencies, esd)`: the DFT bin frequencies from 0 Hz to the Nyquist frequency, in hertz, and the density at each, in the record's unit squared times s/Hz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a record that is not 1-D and finite, or a non-positive sample rate. |

## exponential_decay_rate

```python
exponential_decay_rate(
    n_samples: int,
    fs: float,
    *,
    final_value: float,
) -> float
```

The decay rate of an exponential window that ends the record at a value.

8.5.2 describes an exponential window by the value it decays to at the end
of the record: Figure 10 uses one that decays to 5 % of its initial value.
The end of the record is its last sample, at $(N-1)/f_s$, so
$a = -\ln(w_\mathrm{end}) f_s / (N - 1)$ and
`exponential_window(n_samples, fs, decay_rate_per_s=a)[-1]` is
`final_value`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `n_samples` | Record length `N`, in samples. |
| `fs` | Sample rate, in Hz. |
| `final_value` | Window value at the last sample, in (0, 1] (dimensionless; 0.05 for the window of Figure 10). |

**Returns:** The decay rate `a`, in 1/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than 16 samples, a non-positive sample rate or a final value outside (0, 1]. |

## exponential_window

```python
exponential_window(
    n_samples: int,
    fs: float,
    *,
    decay_rate_per_s: float,
) -> np.ndarray
```

The exponential window of 8.5.2: $w(t) = e^{-a t}$.

The window has an initial value of unity at the start of the record and
decreases exponentially towards its end, adding a known amount of
artificial decay to the data (8.3 a), 8.5.2). Applied to force and response
alike it moves every pole of the impulse response by `-a` (Annex A,
Formula (A.2)); [`exponential_window_correction`](/phonometry/reference/api/vibration/impact-mobility/#exponential_window_correction) takes the added
damping away again.

**Parameters**

| Name | Description |
| :--- | :--- |
| `n_samples` | Record length `N`, in samples. |
| `fs` | Sample rate, in Hz. |
| `decay_rate_per_s` | Decay rate `a`, in 1/s (>= 0; 0 is no window). [`exponential_decay_rate`](/phonometry/reference/api/vibration/impact-mobility/#exponential_decay_rate) finds the rate that ends the record at a stated value. |

**Returns:** The window, one value per sample, $e^{-a n / f_s}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than 16 samples, a non-positive sample rate or a negative decay rate. |

## exponential_window_correction

```python
exponential_window_correction(
    damped_natural_frequency_hz: ArrayLike,
    apparent_damping_ratio: ArrayLike,
    *,
    exponential_decay_rate_per_s: float,
) -> ExponentialWindowCorrection
```

Remove an exponential window's damping from estimated modes (Formula (A.3)).

$\zeta_r = \hat\zeta_r - a/\omega_r$ for each mode, with
$\omega_r = 2\pi f_r$ the damped natural frequency. Estimate
$\hat\zeta_r$ from the windowed data with any curve fitter (Annex A
leaves the method open; [`single_mode_fit`](/phonometry/reference/api/vibration/impact-mobility/#single_mode_fit) is one).

**Parameters**

| Name | Description |
| :--- | :--- |
| `damped_natural_frequency_hz` | Damped natural frequency of each mode, in hertz (scalar or 1-D). |
| `apparent_damping_ratio` | Damping ratio estimated from the windowed data, per mode, in (0, 1). |
| `exponential_decay_rate_per_s` | Decay rate `a` of the window, in 1/s. |

**Returns:** An [`ExponentialWindowCorrection`](/phonometry/reference/api/vibration/impact-mobility/#exponentialwindowcorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for mismatched or invalid inputs, or a window whose damping reaches a mode's apparent damping. |

## ExponentialWindowCorrection

```python
ExponentialWindowCorrection(
    damped_natural_frequency_hz: np.ndarray,
    apparent_damping_ratio: np.ndarray,
    *,
    exponential_decay_rate_per_s: float,
)
```

The damping an exponential window added, taken away (Annex A).

Formula (A.3), $\zeta_r = \hat\zeta_r - a/\omega_r$, per mode, with
$\hat\zeta_r$ the damping ratio estimated from the windowed data,
$a$ the window's decay rate and $\omega_r$ the damped natural
frequency in rad/s. For a lightly damped, well separated mode the measured
peak is multiplied by $\hat\zeta_r / \zeta_r$ to give the true one.

**Attributes**

| Name | Description |
| :--- | :--- |
| `damped_natural_frequency_hz` | Damped natural frequency of each mode, $\omega_r / 2\pi$, in hertz. |
| `apparent_damping_ratio` | Damping ratio of each mode estimated from the windowed data, $\hat\zeta_r$. |
| `exponential_decay_rate_per_s` | The window's decay rate `a`, in 1/s. |

### ExponentialWindowCorrection.damping_ratio

*property*

True damping ratio of each mode, Formula (A.3): $\hat\zeta_r - a/\omega_r$.

### ExponentialWindowCorrection.exact_damping_ratio

*property*

Damping ratio of the pole moved back by `a`, of which (A.3) is the first order.

The window replaces the pole $s_r = -\sigma_r + j\omega_r$ by
$s_r - a$ (Annex A, after Formula (A.2)), so the decay rate of
the windowed mode is $\hat\sigma_r = \sigma_r + a$ at the same
damped frequency. From $\hat\sigma_r = \hat\zeta_r \omega_r / \sqrt{1 - \hat\zeta_r^2}$, the true ratio is
$\sigma_r / \sqrt{\sigma_r^2 + \omega_r^2}$ with
$\sigma_r = \hat\sigma_r - a$. It and (A.3) differ by about
$(\hat\zeta_r^3 - \zeta_r^3)/2$.

### ExponentialWindowCorrection.peak_correction_factor

*property*

Factor on the measured peak of each mode, $\hat\zeta_r / \zeta_r$.

### ExponentialWindowCorrection.plot()

```python
ExponentialWindowCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each mode's apparent damping split into the true and the window's part.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars of the true damping. |

**Returns:** The axes.

### ExponentialWindowCorrection.window_damping_ratio

*property*

The damping the window added to each mode, $a/\omega_r$.

## force_window

```python
force_window(
    n_samples: int,
    fs: float,
    *,
    width_s: float,
    start_s: float = 0.0,
    taper_s: float = 0.0,
) -> np.ndarray
```

The force window of 8.5.1: unity over the pulse, exactly zero elsewhere.

The window has unity gain for the part of the record that holds the force
signal, including the filter response, and sets the remaining samples to
exactly zero before Fourier processing. It removes broad-band noise from
the force auto-spectrum without distortion as long as none of the force
data is attenuated (8.5.1, Figure 7). A rectangular window spreads periodic
noise and DC offset over a wide band (Figure 8), and 8.5.1 notes that a
smooth transition between zero and one narrows that spread: `taper_s`
adds a half-cosine ramp of that length on each side of the unity part,
outside it, so the pulse itself is never attenuated. The shape of the ramp
is this library's choice; the part does not prescribe one.

Never use a force window to cut a second impact out of the record (6.4):
the response still carries it. [`check_double_hit`](/phonometry/reference/api/vibration/impact-mobility/#check_double_hit) finds one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `n_samples` | Record length `N`, in samples. |
| `fs` | Sample rate, in Hz. |
| `width_s` | Length of the unity part, in seconds (> 0). Sample `n` is inside it when `start_s <= n / fs < start_s + width_s`. |
| `start_s` | Where the unity part begins, in seconds (Default: 0, the beginning of the record, which keeps the pre-trigger data of 8.2). |
| `taper_s` | Length of each half-cosine ramp, in seconds (Default: 0, a rectangular window). |

**Returns:** The window, one value per sample.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than 16 samples, a non-positive sample rate or width, a negative start or taper, or a window, its falling ramp included, that is still open at the last sample of the record, at $(N - 1)/f_s$. |

## ForceSpectrumCheck

```python
ForceSpectrumCheck(
    frequencies: np.ndarray,
    energy_spectral_density: np.ndarray,
    *,
    frequency_range_hz: tuple[float, float],
    max_drop_db: float,
)
```

Does the force spectrum cover the frequency range of interest? (6.2, 6.3)

The spectrum of a force pulse is a main lobe at low frequency followed by
side lobes that fall rapidly, with a usable bandwidth inversely
proportional to the pulse duration (6.2). The tip stiffness and the
impactor mass set that bandwidth (6.3), and a double hit cuts notches into
it (6.4). The check reads how far the energy spectral density falls across
the frequency range of interest, from its highest to its lowest value
there, against a limit the caller states: the part prints none.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies above 0 Hz, in hertz. |
| `energy_spectral_density` | One-sided force energy spectral density, in N²·s/Hz (3.4). |
| `frequency_range_hz` | The frequency range of interest (3.2), in hertz. |
| `max_drop_db` | The largest fall across the range the check accepts, in dB. |

### ForceSpectrumCheck.drop_db

*property*

How far the density falls across the range, highest to lowest, in dB.

### ForceSpectrumCheck.energy_fraction_above

*property*

Share of the force energy above the range of interest (6.3).

### ForceSpectrumCheck.in_range

*property*

Per frequency, whether it lies in the frequency range of interest.

### ForceSpectrumCheck.level_db

*property*

The density in dB re its highest value inside the range.

### ForceSpectrumCheck.passes

*property*

Whether the density falls no further than the limit across the range.

### ForceSpectrumCheck.plot()

```python
ForceSpectrumCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the force energy spectral density against the range and the limit.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the density curve. |

**Returns:** The axes.

## HIGH_COHERENCE

*Constant* (`float`).

```python
HIGH_COHERENCE = 0.9
```

## impact_mobility

```python
impact_mobility(
    force: SignalInput,
    response: SignalInput,
    fs: float | None = None,
    *,
    response_quantity: ResponseQuantity = 'acceleration',
    force_window_s: float | None = None,
    force_window_start_s: float = 0.0,
    force_window_taper_s: float = 0.0,
    exponential_decay_rate_per_s: float = 0.0,
    exponential_on_force: bool = True,
    driving_point: bool = True,
    frequency_range_hz: tuple[float, float] | None = None,
) -> ImpactMobilityResult
```

Mobility from impact records, averaged as 8.6 prescribes.

Each row of `force` and `response` is one impact at the same point,
triggered as 8.2 describes. The force is multiplied by the force window
(8.5.1) and both records by the exponential window (8.5.2), both are
transformed, and the estimate is the averaged cross-spectrum of response
and force over the averaged auto-spectrum of the force (8.6), with the
ordinary coherence of 9.1 beside it.

The DFT runs up to the Nyquist frequency, but a force pulse has a finite
usable bandwidth (6.2) and the anti-aliasing filter cuts below the Nyquist
frequency (8.3), so the top of the spectrum is noise divided by almost no
force. `frequency_range_hz` keeps the estimate to the frequency range of
interest of 3.2, the span at which mobility data are to be obtained, and
everything built on the result (its plot, its fiche, its fit) stays there.

Where the force spectrum vanishes the frequency response is undefined,
and a range that holds such a frequency is refused. A spectrum that
vanishes in exact arithmetic, at a notch between two equal impacts for
one, comes out of the transform at the level of its rounding rather than
at zero, so any bin at or below that level counts as vanished.

With `exponential_on_force=False` the exponential window multiplies the
response only, and the force of each impact is multiplied instead by the
window's value at the instant of its peak, the approximation Annex A
describes for the common practice of windowing the response alone.

A force window that zeroes an impact the record holds raises
[`ImpactExcitationWarning`](/phonometry/reference/api/vibration/impact-mobility/#impactexcitationwarning): 6.4 forbids removing a second impact
that way.

**Parameters**

| Name | Description |
| :--- | :--- |
| `force` | Force records, in N: one record (1-D) or one per row (2-D). Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal), one channel per impact, for its rate; a calibration factor it carries is deliberately not applied, because this record is a force and not a pressure. |
| `response` | Response records, same shape, in m/s², m/s or m as `response_quantity` says; a Signal likewise, its factor not applied. |
| `fs` | Sample rate, in Hz. Required when both records are bare arrays; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value, or a second Signal, that disagrees with it raises. |
| `response_quantity` | `"acceleration"` (default), `"velocity"` or `"displacement"`. |
| `force_window_s` | Width of the unity part of the force window, in seconds (Default: `None`, no force window). |
| `force_window_start_s` | Where the unity part begins, in seconds (Default: 0). |
| `force_window_taper_s` | Half-cosine ramp on each side, in seconds (Default: 0). |
| `exponential_decay_rate_per_s` | Decay rate `a` of the exponential window, in 1/s (Default: 0, none). |
| `exponential_on_force` | Window the force too (Default: `True`, the exact case of Formula (A.2)). |
| `driving_point` | Whether force and response are co-located (Default: `True`). |
| `frequency_range_hz` | `(f_low, f_high)`, the frequency range of interest in hertz, inside the Nyquist frequency (Default: `None`, every bin above 0 Hz). |

**Returns:** An [`ImpactMobilityResult`](/phonometry/reference/api/vibration/impact-mobility/#impactmobilityresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for records of different shapes, not finite or too short, a non-positive sample rate, an unknown response quantity, an invalid window, a range that holds no bin above 0 Hz, or a force spectrum that vanishes at some frequency of the range. |

**Warns**

| Warning | When |
| :--- | :--- |
| ImpactExcitationWarning | when the force window removes an impact. |

## ImpactExcitationWarning

Advisory when an ISO 7626-5 record breaks a rule of the part.

## ImpactMobilityResult

```python
ImpactMobilityResult(
    frequencies: np.ndarray,
    mobility: np.ndarray,
    coherence: np.ndarray,
    force_energy_spectral_density: np.ndarray,
    *,
    impacts: int,
    exponential_decay_rate_per_s: float = 0.0,
    response_quantity: ResponseQuantity = 'acceleration',
    driving_point: bool = True,
)
```

Mobility averaged over impacts at one point (ISO 7626-5:2019, 8.6).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | DFT bin frequencies above 0 Hz, in hertz: up to the Nyquist frequency, or across the frequency range of interest the estimate was kept to (3.2). |
| `mobility` | Complex mobility `Y` per frequency, in m/(N·s): the averaged estimate of 8.6 as measured, exponential window included. Its resonance peaks are therefore lower than the structure's when a window was used; `fit_mode` and the correction of Annex A restore them. |
| `coherence` | Ordinary coherence $\gamma^2$ per frequency (9.1); identically 1 for a single impact. |
| `force_energy_spectral_density` | Averaged one-sided energy spectral density of the windowed force, $G_{FF}$ in N²·s/Hz (3.4). |
| `impacts` | Number of impacts averaged. |
| `exponential_decay_rate_per_s` | Decay rate `a` of the exponential window applied, in 1/s (0 for none). |
| `response_quantity` | What the response channel measured: `"acceleration"`, `"velocity"` or `"displacement"`. |
| `driving_point` | `True` if force and response are co-located. |

### ImpactMobilityResult.fit_mode()

```python
ImpactMobilityResult.fit_mode(
    band_hz: tuple[float, float],
) -> SingleModeFitResult
```

Fit the mode in a band, knowing the window this estimate carries.

The fit runs on the FRF kind the response channel measured, because
that is the record the exponential window multiplied, and the result
carries the window's decay rate so that
[`SingleModeFitResult.correction`](/phonometry/reference/api/vibration/impact-mobility/#singlemodefitresultcorrection) applies Annex A.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | `(f_low, f_high)` around one resonance, in hertz. |

**Returns:** A [`SingleModeFitResult`](/phonometry/reference/api/vibration/impact-mobility/#singlemodefitresult).

### ImpactMobilityResult.magnitude

*property*

Mobility magnitude `|Y|`, in m/(N·s).

### ImpactMobilityResult.measured_frf

*property*

The FRF kind the response channel gives: accelerance, mobility or receptance.

### ImpactMobilityResult.mobility_result

*property*

The estimate as a [`.MobilityResult`](/phonometry/reference/api/vibration/mechanical-mobility/#mobilityresult) (ISO 7626-1 vocabulary).

### ImpactMobilityResult.phase

*property*

Mobility phase, in radians.

### ImpactMobilityResult.plot()

```python
ImpactMobilityResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes | np.ndarray
```

Plot the averaged mobility and its coherence.

With no `ax` a two-panel figure is drawn: `|Y(f)|` on log-log axes
and the coherence beneath it. With `ax` only the magnitude is drawn.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the magnitude curve. |

**Returns:** The axes, or the two-axes array.

### ImpactMobilityResult.report()

```python
ImpactMobilityResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the ISO 7626 mobility fiche for an impact measurement to a PDF.

The one-page fiche of `.MobilityResult.report`, with the
standard-basis line naming ISO 7626-5:2019 and the characteristic
points extended by the number of impacts averaged, the exponential
window and the coherence at the mobility peak.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata). |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | Accepted for a uniform `.report()` signature; the fiche has a single body layout, so it has no effect. |
| `language` | `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"` or `language` is unknown. |
| ImportError | If reportlab or matplotlib is not installed. |

### ImpactMobilityResult.to()

```python
ImpactMobilityResult.to(target: str) -> np.ndarray
```

Convert the mobility to another FRF kind (see [`.convert_frf`](/phonometry/reference/api/vibration/mechanical-mobility/#convert_frf)).

## OverloadCheck

```python
OverloadCheck(record: np.ndarray, fs: float, *, full_scale: float)
```

Did the record stay inside the linear range of its channel? (8.4)

Impact excitation risks saturating the measurement system, because the
signals carry out-of-band energy and the dynamic range is used to its
limit (8.4). Saturation is not always visible as a clipped waveform, so
8.4 asks that the manufacturer's maximum for linear operation be observed,
and warns that filtered digital records give poor definition of the actual
waveform: pass the widest-band record available. A pass here is necessary,
not sufficient.

**Attributes**

| Name | Description |
| :--- | :--- |
| `record` | The record judged, in its own unit, as a bare array (a [`Signal`](/phonometry/reference/api/io/io/#signal) passed in is read without its calibration factor, and its samples are what is kept). |
| `fs` | Its sample rate, in Hz. |
| `full_scale` | The largest magnitude the channel handles linearly, in the unit of the record. |

### OverloadCheck.clipped_samples

*property*

How many samples reach the full scale.

### OverloadCheck.headroom_db

*property*

Distance from the peak to the full scale, in dB (infinite for silence).

### OverloadCheck.passes

*property*

Whether every sample stays below the full scale.

### OverloadCheck.peak

*property*

Largest magnitude in the record, in its unit.

### OverloadCheck.plot()

```python
OverloadCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the record against its full scale, clipped samples marked.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the record curve. |

**Returns:** The axes.

## RESPONSE_END_RATIO

*Constant* (`float`).

```python
RESPONSE_END_RATIO = 0.01
```

## RESPONSE_MIDPOINT_RATIO

*Constant* (`float`).

```python
RESPONSE_MIDPOINT_RATIO = 0.1
```

## ResponseDecayCheck

```python
ResponseDecayCheck(
    record: np.ndarray,
    fs: float,
    *,
    segment_s: float,
    exponential_window: bool,
    start_s: float = 0.0,
)
```

Did the response decay far enough within the record? (8.3, 8.5.2)

Without a window the response should decay to about 1 % of its initial
magnitude at the end of the record, or truncation leaks (8.3). 8.3 calls
that figure a compromise: a longer record, reaching further down, improves
the frequency resolution but can lower the signal-to-noise ratio, so a
much faster decay is no better. With an exponential window, as a general
guideline, the natural decay should reach 25 % or less, or the corrections
of Annex A become very sensitive to errors in the damping estimates
(8.5.2). 8.5.2 also offers a convenient check: the peak response at the
midpoint of the record is about 10 % of the highest one, which for a steady
exponential decay is the same statement as 1 % at the end.

Levels are peaks of the magnitude over segments of the record, relative to
the highest peak from `start_s` on; a segment needs at least one period
of the lowest mode for its peak to be a peak. The midpoint level is the
peak over the segment that starts at the midpoint. The level at the end is
read at the last sample: the peak over the last segment sits at its start,
so it is carried to the last sample at the rate the peaks decay from the
midpoint segment to the last one, the steady decay the midpoint check
itself assumes. A response that has stopped decaying, on a noise floor, is
read at the peak of its last segment, never higher.

The verdict compares the level at the end, rounded to a whole per cent
(the precision both figures are printed in), with the figure: "about 1 %"
accepts any level below 1,5 %, which rounds to 1 %, and "25 % or less"
any level below 25,5 %.

A driving-point acceleration follows the force itself during the impact
(the mass line of the structure), so its highest peak can be the impact
rather than the decay. `start_s` just after the force pulse, or the force
record passed to [`check_response_decay`](/phonometry/reference/api/vibration/impact-mobility/#check_response_decay), judges the free decay alone.

**Attributes**

| Name | Description |
| :--- | :--- |
| `record` | The response record judged, unwindowed, in its own unit, as a bare array (a [`Signal`](/phonometry/reference/api/io/io/#signal) passed in is read without its calibration factor, and its samples are what is kept). |
| `fs` | Its sample rate, in Hz. |
| `segment_s` | Length of the segments the end and midpoint levels are read over, in seconds. |
| `exponential_window` | Whether the record is to be processed with an exponential window (25 % limit) or without (1 %). |
| `start_s` | Time from which the highest peak is sought, in seconds. |

### ResponseDecayCheck.end_ratio

*property*

Level at the last sample of the record, relative to the highest peak.

The peak over the last segment, carried over the rest of the segment
at the rate the segment peaks decay from the midpoint to the last
segment (never raised).

### ResponseDecayCheck.last_segment_ratio

*property*

Peak over the last segment, relative to the highest peak.

For a response still decaying this is its level at the start of the
segment, above the level at the end of the record.

### ResponseDecayCheck.limit_ratio

*property*

The figure the clause prints: 0,01 without a window, 0,25 with one.

### ResponseDecayCheck.midpoint_ratio

*property*

Peak over the segment starting at the midpoint, relative to the highest peak.

### ResponseDecayCheck.passes

*property*

Whether the level at the end, to a whole per cent, is at most the figure.

### ResponseDecayCheck.peak

*property*

The highest peak of the response from `start_s` on, in its unit.

### ResponseDecayCheck.peak_time_s

*property*

When the highest peak from `start_s` on occurs, in seconds.

### ResponseDecayCheck.plot()

```python
ResponseDecayCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the response with the levels it reaches at the midpoint and the end.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the response curve. |

**Returns:** The axes.

## single_mode_fit

```python
single_mode_fit(
    frequencies: ArrayLike,
    frf: ArrayLike,
    *,
    band_hz: tuple[float, float],
    kind: str = 'mobility',
    exponential_decay_rate_per_s: float = 0.0,
) -> SingleModeFitResult
```

Fit one mode to an FRF over a band around its resonance.

Annex A needs the apparent damping of each mode and leaves the estimator
open ("suitable parameter estimation capability is now widely available
through a variety of curve-fitting methods"). This is a rational-fraction
fit of one mode: the FRF over the band is fitted by
$(b_0 + b_1 s + b_2 s^2)/(s^2 + a_1 s + a_0)$ in linear least
squares, reweighted by the previous denominator until it settles
(Sanathanan and Koerner), and the result is written as a pole, its residue
and a direct term ([`SingleModeFitResult`](/phonometry/reference/api/vibration/impact-mobility/#singlemodefitresult)). The model is exact for a
single-degree-of-freedom structure; on a real one, choose a band that
holds one resonance and little else.

Annex A asks that the apparent damping of each mode "can be accurately
determined", and a band without a resonance determines none: a constant,
a mass line or a spring line fits the numerator alone and leaves the pole
to rounding. The fit is refused when its system does not determine the
five coefficients to half the digits of a double, or when the pole it
finds has no decay rate or no damped natural frequency above that same
fraction of the band's centre frequency.

Fit the FRF in the kind the response channel measured, because that is
the record the exponential window multiplied:
[`ImpactMobilityResult.fit_mode`](/phonometry/reference/api/vibration/impact-mobility/#impactmobilityresultfit_mode) does so.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies of the FRF, in hertz (> 0). |
| `frf` | Complex FRF of kind `kind`, same length. |
| `band_hz` | `(f_low, f_high)`, in hertz, holding at least three frequencies. |
| `kind` | `"accelerance"`, `"mobility"` (default) or `"receptance"`. |
| `exponential_decay_rate_per_s` | Decay rate of the exponential window the data carry, in 1/s (Default: 0). |

**Returns:** A [`SingleModeFitResult`](/phonometry/reference/api/vibration/impact-mobility/#singlemodefitresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for mismatched or non-finite data, a band that is not a pair of positive numbers or holds fewer than three frequencies, an unknown kind, or a band whose data hold no lightly damped mode. |

## SingleModeFitResult

```python
SingleModeFitResult(
    frequencies: np.ndarray,
    frf: np.ndarray,
    pole_rad_s: complex,
    residue: complex,
    direct_term: complex,
    *,
    kind: str = 'mobility',
    exponential_decay_rate_per_s: float = 0.0,
)
```

One mode fitted over a band: pole, residue and a direct term.

The model is
$H(s) = D + \frac{R}{s - p} + \frac{R^{*}}{s - p^{*}}$, with
$p = -\hat\sigma + j\omega_d$ the pole of the data fitted,
$R$ its residue and $D$ a real constant that stands in for the
modes outside the band. For a single-degree-of-freedom structure the model
is exact in every FRF kind: $D = 0$ for dynamic compliance and
mobility and $D = 1/m$ for accelerance.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The frequencies fitted, in hertz. |
| `frf` | The FRF fitted, complex, of kind `kind`. |
| `pole_rad_s` | The pole $p$ of the data, upper half plane, in rad/s. |
| `residue` | Its residue $R$, in the FRF's unit times rad/s. |
| `direct_term` | The constant $D$, in the FRF's unit. |
| `kind` | The FRF kind fitted: `"accelerance"`, `"mobility"` or `"receptance"`. |
| `exponential_decay_rate_per_s` | Decay rate of the exponential window the data carry, in 1/s (0 for none). |

### SingleModeFitResult.apparent_damping_ratio

*property*

Damping ratio of the fitted pole, $\hat\sigma / \lvert p \rvert$.

With an exponential window this is the apparent damping
$\hat\zeta_r$ of Annex A, the window's included.

### SingleModeFitResult.corrected_frf()

```python
SingleModeFitResult.corrected_frf(frequencies: ArrayLike) -> np.ndarray
```

The mode with the window taken out, of kind `kind` (Annex A).

The pole is moved back by the decay rate, $p + a$, and the
residue and direct term are kept: the window multiplies the impulse
response $R e^{p t}$ by $e^{-a t}$, which changes the pole
and nothing else (Formula (A.2)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz. |

**Returns:** The complex FRF.

### SingleModeFitResult.corrected_mobility()

```python
SingleModeFitResult.corrected_mobility(frequencies: ArrayLike) -> np.ndarray
```

The corrected mode as mobility, in m/(N·s).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz (> 0). |

**Returns:** The complex mobility.

### SingleModeFitResult.correction

*property*

The Annex A correction of this mode for the window its data carry.

### SingleModeFitResult.damped_natural_frequency_hz

*property*

Damped natural frequency $\omega_d / 2\pi$, in hertz.

### SingleModeFitResult.fitted_frf()

```python
SingleModeFitResult.fitted_frf(frequencies: ArrayLike) -> np.ndarray
```

The fitted model at any frequencies, window included, of kind `kind`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz. |

**Returns:** The complex FRF.

### SingleModeFitResult.plot()

```python
SingleModeFitResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the data fitted, the fitted mode and the mode with the window taken out.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the fitted curve. |

**Returns:** The axes.

## verify_channel_match

```python
verify_channel_match(
    frequencies: ArrayLike,
    response: ArrayLike,
    *,
    frequency_range_hz: tuple[float, float],
) -> ChannelMatchVerification
```

Is the analyser's channel-to-channel match inside 8.1's tolerances?

Feed the same broad-band signal to both channels, estimate the frequency
response between them (for instance with
[`phonometry.electroacoustics.frequency_response.transfer_function`](/phonometry/reference/api/electroacoustics/frequency-response/#transfer_function)),
and pass it here. The verification passes when its magnitude is unity
within +/- 5 % and its phase zero within +/- 5 degrees at every frequency
of the range of interest.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies of the response, in hertz. |
| `response` | Complex frequency response between the channels. |
| `frequency_range_hz` | `(f_low, f_high)`, in hertz. |

**Returns:** A [`ChannelMatchVerification`](/phonometry/reference/api/vibration/impact-mobility/#channelmatchverification) over the range.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for mismatched or non-finite data, or a range that holds none of the frequencies. |

## WINDOWED_RESPONSE_END_RATIO

*Constant* (`float`).

```python
WINDOWED_RESPONSE_END_RATIO = 0.25
```
