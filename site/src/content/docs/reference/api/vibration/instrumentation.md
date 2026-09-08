---
title: "vibration.human.instrumentation"
description: "Type-testing a human-vibration meter against ISO 8041-1:2017."
sidebar:
  label: "instrumentation"
---

Type-testing a human-vibration meter against ISO 8041-1:2017.

A sound level meter can be given a class: IEC 61672-1 prints design goals and
tolerance limits, and [`verify_weighting_class`](/phonometry/reference/api/filters/weighting-compliance/#verify_weighting_class)
turns a measured response into a verdict against them. A human-vibration
meter is checked the same way and by the same kind of table, and this module
is that check.

**What the standard grades.** ISO 8041-1 defines the nine frequency
weightings ([`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names)) as exact transfer
functions, and then says how far a real instrument may sit from them. The
allowance is not one number: it is a band that widens away from the middle of
the working range, keyed to four transition frequencies per weighting
(Table 4). Table 5 prints five rows across them and they carry three
distinct limit pairs, because the two skirts share theirs and so do the two
tails: inside the central region the magnitude may differ by `+12 %` /
`−11 %`; in the two skirts by `+26 %` / `−21 %`; beyond the outermost
pair the standard stops
constraining the response from below altogether, which is what `−100 %`
means in the printed table.

**What it does not grade.** A verdict here is about the *frequency weighting*,
which is one clause of a standard that also covers indication, linearity,
overload, temperature, humidity and electromagnetic susceptibility. Passing
this check is a necessary condition for conformity, never a certificate of
it: the rest are laboratory tests on hardware, not arithmetic.

**Tolerances are on the factor, not on the decibel.** The standard writes its
limits as percentages of the weighting factor, and this module keeps them
that way. `+26 %` is `+2,0 dB` to two decimals, but the percentage is
what the page prints and what the acceptance test in Annex B is written in.

**The band does not widen; the measurement does.** Two sentences of the
standard talk about expanded uncertainty and they are not the same sentence.
5.6.6 (printed folio 14) says the Table 5 limits already "include the
applicable maximum expanded uncertainties of measurement", which is why
[`weighting_tolerance_percent`](/phonometry/reference/api/vibration/instrumentation/#weighting_tolerance_percent) returns the printed numbers and never
adds to them. 13.1 (folio 42) and 14.1 (folio 48) say something else, word
for word in both: compliance is demonstrated when the measured deviation,
"extended by the actual expanded uncertainty of measurement of the testing
laboratory", does not exceed those limits. That second rule is about the
laboratory's own uncertainty, it moves the deviation rather than the band,
and it is what `expanded_uncertainty_percent` does in
[`verify_weighting`](/phonometry/reference/api/vibration/instrumentation/#verify_weighting).

**Phase is graded on a slope, not on an angle.** Footnote a of Table 5 limits
the phase criterion to instruments reporting a parameter not based on r.m.s.
values, and 5.6.6 explains why the criterion is not the phase error itself:
a constant group delay is a large phase error that changes no measured
quantity. Formula (6) (folio 15) turns a pair of adjacent phase errors into
the characteristic phase deviation the table actually grades, and
[`verify_phase_response`](/phonometry/reference/api/vibration/instrumentation/#verify_phase_response) is that comparison.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## band_limited_weighting_factor

```python
band_limited_weighting_factor(name: str) -> float
```

The factor that makes the second row of Table 2 satisfiable.

Table 2 (folio 12) allows 3 % between "the indicated value of any
frequency-weighted measurement quantity" and "the indicated value of the
corresponding band-limiting measurement multiplied by the appropriate
weighting factor", and 12.7 (folio 30) turns it into a procedure: with the
input adjusted so that the meter indicates the reference vibration value
*with band-limiting frequency weighting*, the frequency-weighted
indication "shall equal the indicated band-limited weighted vibration
value multiplied by the appropriate weighting factor (see Table 1)".

That test fixes the input at `a_ref / |H_BL(f_ref)|`, so the weighted
indication is `a_ref |H(f_ref)| / |H_BL(f_ref)|`: the factor that makes
the identity true is the **ratio** of the two responses at the reference
frequency, which is what this function returns.

==========  ==================  ===================
Weighting   This ratio          Table 1 prints
==========  ==================  ===================
`Wb`      0,812 819           0,812 6
`Wc`      0,514 617           0,514 5
`Wd`      0,126 120           0,126 1
`We`      0,062 891           0,062 87
`Wf`      0,418 982           0,388 8
`Wh`      0,202 025           0,202 0
`Wj`      1,018 841           1,019
`Wk`      0,772 066           0,771 8
`Wm`      0,336 336           0,336 2
==========  ==================  ===================

For eight of the nine the distinction is academic: their band-limiting
weighting is between 0,999 68 and 0,999 97 at their reference frequency,
so the printed Table 1 factor is the same number to 0,03 %, against a
tolerance of 3 %. For `Wf` it is not. Its reference frequency,
2,5 rad/s = 0,397 887 Hz, sits inside its own band-limiting skirt (0,08 Hz
and 0,63 Hz corners, Table 3): the band-limiting weighting is 0,928 078
there and the overall weighting 0,388 848, values Table B.5 prints as
0,927 9 and 0,388 4 at the neighbouring 0,398 1 Hz band centre. Reading
"the appropriate weighting factor" as the 0,388 8 of Table 1 makes a
*conforming* `Wf` meter miss the row by 7,75 %, more than twice the
tolerance; reading it as the ratio 0,418 982 makes the row true by
construction. The standard does not define the phrase, and the "(see
Table 1)" of 12.7 points at the reading that cannot be satisfied; the
ambiguity is registered in `docs/ERRATA.md`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |

**Returns:** `|H(f_ref)| / |H_BL(f_ref)|`, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine. |

## CENTRAL_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
CENTRAL_TOLERANCE_PERCENT = (12.0, -11.0, 6.0)
```

## characteristic_phase_deviation

```python
characteristic_phase_deviation(
    frequencies_hz: ArrayLike,
    phase_deviation_deg: ArrayLike,
) -> NDArray[np.float64]
```

The characteristic phase deviation of ISO 8041-1 Formula (6).

5.6.6 (printed folio 14) says why the phase error itself is not the
criterion: "the errors in measurement due to errors in the phase response
are dependent on the rate of change in phase error with frequency, rather
than the absolute phase error itself". Formula (6) (folio 15) is that rate,
printed inside absolute-value bars:

$$
\Delta\varphi_0 = \left\lvert \frac{f_n \, \Delta\varphi_{n+1} - f_{n+1} \, \Delta\varphi_n} {f_{n+1} - f_n} \right\rvert
$$

The normative Annex H closes the two questions the clause leaves open.
Formula (H.3) (folio 93) prints the same quantity with the two products
exchanged, which is the same number inside the bars both formulae carry,
and it says where the number belongs: "This allows the calculation of
Δφ0(f_n) at each frequency f_n except for the highest frequency". So `N`
frequencies give `N - 1` values, each attributed to the lower frequency
of its pair, and that is what decides which Table 5 region grades a pair
that straddles a transition frequency: the region of `f_n`.

Two closed forms say what the quantity measures. A constant phase error of
`c` degrees gives `|c|` at every pair, so an offset is graded at face
value. A phase error proportional to frequency, which is a constant group
delay, gives exactly zero, and NOTE 1 of H.2.1 is that reading: a constant
group delay "would probably far exceed the tolerances on phase deviation,
but would influence neither the vibration parameters to be measured nor
the characteristic phase deviation values".

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies the phase errors belong to, in hertz, strictly ascending. H.2.1 asks for them "preferably in steps of one-third octaves", which is the grid Annex B tabulates. |
| `phase_deviation_deg` | The phase error at each frequency, in degrees, measured minus design goal. |

**Returns:** One value per adjacent pair, in degrees, attributed to the lower frequency of the pair, so of length one less than the input.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the two arrays do not have the same shape, if a frequency is not positive and finite, if a phase deviation is not finite, or if there are fewer than two frequencies or they do not strictly ascend. |

## INDICATION_TOLERANCE_PERCENT

*Constant* (`float`).

```python
INDICATION_TOLERANCE_PERCENT = 4.0
```

## indication_tolerance_percent

```python
indication_tolerance_percent(name: str) -> float
```

The Table 2 indication tolerance at the reference frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |

**Returns:** The permitted deviation of the indication, in per cent.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine. |

## ISO8041_COVERAGE_FACTOR

*Constant* (`float`).

```python
ISO8041_COVERAGE_FACTOR = 2.0
```

## LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT

*Constant* (`float`).

```python
LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT = 5.0
```

## LOW_FREQUENCY_WEIGHTING

*Constant* (`str`).

```python
LOW_FREQUENCY_WEIGHTING = 'Wf'
```

## MAX_EXPANDED_UNCERTAINTY_PERCENT

*Constant* (`dict`).

```python
MAX_EXPANDED_UNCERTAINTY_PERCENT = {'12.7': 2.0, '12.10.1': 2.0, '12.10.2': 3.0, '12.10.2 additional ranges': 4.0, '12.11.2': 4.5, '12.11.3': 3.0, '12.11.4': 5.0, '12.13': 3.0, '12.14': 2.0, '12.18': 0.01, '13.9': 2.0, '13.11': 4.0, '13.14': 2.0, '13.15': 0.01, '14.9': 5.0}
```

## NOMINAL_FREQUENCY_RANGE_HZ

*Constant* (`dict`).

```python
NOMINAL_FREQUENCY_RANGE_HZ = {'Wb': (0.5, 80.0), 'Wc': (0.5, 80.0), 'Wd': (0.5, 80.0), 'We': (0.5, 80.0), 'Wf': (0.1, 0.5), 'Wh': (8.0, 1000.0), 'Wj': (0.5, 80.0), 'Wk': (0.5, 80.0), 'Wm': (1.0, 80.0)}
```

## peak_deviation_percent

```python
peak_deviation_percent(
    characteristic_phase_deviation_deg: ArrayLike,
) -> float
```

The peak-value deviation a phase response costs (Formula (H.4)).

Annex H is normative, and (H.4) (folio 93) is the only worked number in
the whole phase argument:

$$
\Delta P_{\max} \approx \pm \max\{0{,}48 \sin \Delta\varphi_0(f_n)\} \times 100 \, \%
$$

followed by "For the maximum characteristic phase deviations of 12°, the
maximum peak value deviation is approximately 10 %". The maximum is inside
the printed formula, so this returns one number for a whole response
rather than one per frequency: `ΔP_max` is what the worst pair costs.

NOTE 2 of H.2.1 fences the approximation twice, and both fences matter to
a reader of the returned number. It "applies to small Δφ0 values only
(\< 30°)", which is why a larger value is passed on with a warning rather
than silently. And it is a worst case: "Depending on the signal waveform,
the actual peak value deviation will normally be smaller than ΔP_max
which is a worst-case estimate, combining the amplitudes and zero phase
angles of two frequency components in the most unfavourable manner."

**Parameters**

| Name | Description |
| :--- | :--- |
| `characteristic_phase_deviation_deg` | One or more characteristic phase deviations, in degrees, as [`characteristic_phase_deviation`](/phonometry/reference/api/vibration/instrumentation/#characteristic_phase_deviation) returns them. |

**Returns:** The likely maximum peak-value deviation, in per cent. The printed `±` is the sign of the deviation, not part of the size, so the number returned is the magnitude.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a value is negative or not finite. Formula (6) prints the quantity inside absolute-value bars, so a negative one is not a characteristic phase deviation and is refused rather than folded. |
| UserWarning | [`HumanVibrationWarning`](/phonometry/reference/api/vibration/exposure/#humanvibrationwarning) when a value exceeds the 30 degrees NOTE 2 limits the approximation to. |

## phase_tolerance_degrees

```python
phase_tolerance_degrees(
    name: str,
    frequencies: ArrayLike,
) -> NDArray[np.float64]
```

The Table 5 characteristic phase-deviation band, region by region.

Footnote a of the table limits this to instruments that provide a
measurement parameter not based on r.m.s. values, which is why it is a
separate function rather than a third array beside the magnitudes: an
r.m.s.-only meter is not graded on phase at all.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | Frequencies at which the band is wanted, in hertz. |

**Returns:** The permitted deviation, in degrees, infinite in the two tails.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As for [`weighting_tolerance_percent`](/phonometry/reference/api/vibration/instrumentation/#weighting_tolerance_percent). |

## PhaseVerification

```python
PhaseVerification(
    weighting: str,
    frequencies_hz: NDArray[np.float64],
    measured_phase_deg: NDArray[np.float64],
    design_phase_deg: NDArray[np.float64],
    deviation_deg: NDArray[np.float64],
    characteristic_frequencies_hz: NDArray[np.float64],
    characteristic_deviation_deg: NDArray[np.float64],
    tolerance_deg: NDArray[np.float64],
    within_tolerance: NDArray[np.bool_],
)
```

One measured phase response against the ISO 8041-1 Table 5 phase band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `weighting` | The weighting the response was measured for. |
| `frequencies_hz` | The frequencies it was measured at. |
| `measured_phase_deg` | The measured phase, as supplied. |
| `design_phase_deg` | The design-goal phase of Formula (H.1) at the same frequencies, on the branch Tables B.1 to B.9 print. |
| `deviation_deg` | The phase error, measured minus design, in degrees. |
| `characteristic_frequencies_hz` | The frequencies the characteristic phase deviations are attributed to, which are all but the highest (H.2.1, Formula (H.3)). |
| `characteristic_deviation_deg` | The characteristic phase deviation of Formula (6) at each of those, in degrees. |
| `tolerance_deg` | The Table 5 limit at each of those, in degrees, infinite in the two tails. |
| `within_tolerance` | Whether each characteristic phase deviation is inside its limit. |

### PhaseVerification.failing_frequencies_hz

*property*

The frequencies whose characteristic phase deviation is too large.

### PhaseVerification.passes

*property*

Whether every characteristic phase deviation sits inside Table 5.

True says the phase response meets the criterion of footnote a of
Table 5, which is the one an instrument reporting peak, MTVV or VDV is
held to. An r.m.s.-only instrument is not graded on phase at all, and
this is not a verdict on its magnitude response.

### PhaseVerification.peak_deviation_percent

*property*

What this phase response costs a peak reading (Formula (H.4)).

The worst case over the measured range, which is where the maximum in
the printed formula is taken.

### PhaseVerification.plot()

```python
PhaseVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the characteristic phase deviation inside the Table 5 band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_phase_verification`. |

## REFERENCE_ACCELERATION_M_S2

*Constant* (`dict`).

```python
REFERENCE_ACCELERATION_M_S2 = {'Wb': 1.0, 'Wc': 1.0, 'Wd': 1.0, 'We': 1.0, 'Wf': 0.1, 'Wh': 10.0, 'Wj': 1.0, 'Wk': 1.0, 'Wm': 1.0}
```

## REFERENCE_FREQUENCY_HZ

*Constant* (`dict`).

```python
REFERENCE_FREQUENCY_HZ = {'Wb': 15.915494309189533, 'Wc': 15.915494309189533, 'Wd': 15.915494309189533, 'We': 15.915494309189533, 'Wf': 0.3978873577297384, 'Wh': 79.57747154594767, 'Wj': 15.915494309189533, 'Wk': 15.915494309189533, 'Wm': 15.915494309189533}
```

## reference_indication

```python
reference_indication(name: str) -> float
```

The weighted indication a conforming meter shows at the reference.

Table 1 pairs each application with a reference frequency and a reference
r.m.s. acceleration, and the weightings are not unity there, so the
expected indication is the product of the two.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |

**Returns:** The weighted acceleration, in metres per second squared.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine. |

## RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT

*Constant* (`float`).

```python
RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT = 2.0
```

## RUNNING_RMS_DECAY_RATE_DB_PER_S

*Constant* (`tuple`).

```python
RUNNING_RMS_DECAY_RATE_DB_PER_S = ((0.125, 31.0, 40.0), (1.0, 3.8, 4.9), (8.0, 0.48, 0.62))
```

## running_rms_decay_time

```python
running_rms_decay_time(integration_time_s: float, *, method: str) -> float
```

When the running r.m.s. falls to 10 % after the signal is shut off.

5.13 (folio 20) applies a steady sinusoid at the reference frequency for
at least 5 time constants (linear averaging) or 20 (exponential), shuts it
off, and times the decay "from the start of the decay to the time at
which the indicated value is less than 10 % of the initial value".

Both averages have a closed form. The linear average of Eq. (2) keeps the
last `tau` seconds of the record, so a time `t` after the cut its
window still holds `(tau - t) / tau` of the original mean square and the
indicated value falls as $\sqrt{(\tau - t)/\tau}$, reaching 10 % at
`t = 0,99 tau`. The exponential average of Eq. (3) decays in power as
$e^{-t/\tau}$, so the indication falls as $e^{-t/2\tau}$ and
reaches 10 % at $t = 2\tau\ln 10 = 4,605\,2\,\tau$.

Both land inside the printed bands of [`RUNNING_RMS_DECAY_TIME_S`](/phonometry/reference/api/vibration/instrumentation/#running_rms_decay_time_s)
for the three time constants the standard tabulates.

**Parameters**

| Name | Description |
| :--- | :--- |
| `integration_time_s` | The averaging time `tau`, in seconds (> 0). |
| `method` | `"linear"` (Table 10) or `"exponential"` (Table 11), the two averages of [`running_rms`](/phonometry/reference/api/vibration/exposure/#running_rms). |

**Returns:** The time to 10 % of the initial indicated value, in seconds.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `method` is neither average, or the integration time is not positive and finite. |

## RUNNING_RMS_DECAY_TIME_S

*Constant* (`dict`).

```python
RUNNING_RMS_DECAY_TIME_S = {'linear': ((0.125, 0.124, 0.005), (1.0, 0.99, 0.05), (8.0, 7.92, 0.2)), 'exponential': ((0.125, 0.58, 0.03), (1.0, 4.61, 0.25), (8.0, 36.8, 2.0))}
```

## SKIRT_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
SKIRT_TOLERANCE_PERCENT = (26.0, -21.0, 12.0)
```

## TAIL_TOLERANCE_PERCENT

*Constant* (`tuple`).

```python
TAIL_TOLERANCE_PERCENT = (26.0, -100.0, inf)
```

## TRANSITION_FREQUENCIES_HZ

*Constant* (`dict`).

```python
TRANSITION_FREQUENCIES_HZ = {'Wb': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wc': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wd': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'We': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wf': (0.05011872336272722, 0.12589254117941673, 0.3981071705534972, 1.0), 'Wh': (3.9810717055349722, 10.0, 794.3282347242813, 1995.2623149688789), 'Wj': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wk': (0.251188643150958, 0.6309573444801932, 63.09573444801933, 158.48931924611142), 'Wm': (0.5011872336272722, 1.2589254117941673, 63.09573444801933, 158.48931924611142)}
```

## UNCONSTRAINED_BELOW

*Constant* (`float`).

```python
UNCONSTRAINED_BELOW = -100.0
```

## verify_phase_response

```python
verify_phase_response(
    name: str,
    frequencies_hz: ArrayLike,
    measured_phase_deg: ArrayLike,
) -> PhaseVerification
```

Check a measured phase response against the ISO 8041-1 Table 5 band.

Table 5 (folio 15) prints a characteristic phase deviation limit beside
every magnitude limit: `±6°` in the central region, `±12°` in the two
skirts and `±∞` in the two tails. The quantity those grade is not the
phase error but Formula (6) of it, which is why this is a separate entry
point from [`verify_weighting`](/phonometry/reference/api/vibration/instrumentation/#verify_weighting) rather than a third array inside it:
footnote a of the table applies the phase criterion only to instruments
"that provide measurement parameters that are not based on r.m.s. values",
so an r.m.s.-only meter is never handed this verdict.

The design goal comes from Formula (H.1), which is the argument of the
same `H(s)` [`frequency_weighting`](/phonometry/reference/api/vibration/exposure/#frequency_weighting) evaluates,
and it is put on the branch Tables B.1 to B.9 print, so the measurement
has to arrive on a continuous branch too. That is not a convenience: the
two invariances the standard prints for this criterion hold on the
continuous phase error and on no other. A constant phase error of `c`
degrees is graded as `c`; a constant group delay, which is a phase error
proportional to frequency, is graded as zero, and H.2.3.4 n) is explicit
that "any remaining constant delay time (except 180°) does not influence
the result at all". Fold the error into a half turn either side of zero
and the second one stops being true, which is why nothing is folded here.
H.2.3.4 g) to m) is the standard's own reconstruction of that continuous
curve from wrapped phase-meter readings, and it belongs before this call:
on a one-third-octave grid a wrap and a delay ramp are the same jump, so
no check here could tell a measurement still carrying its wraps from the
delay the criterion is meant to ignore.

**What a polarity error looks like here, and why it is not this test.**
H.2.3.4 k) (folio 99) says a half-turn shift of every component "leaves
the wave form of the signal unchanged, but would create catastrophic
results attempting to apply the characteristic phase deviation (CPD)
criterion", and that the criterion "is not applicable to signal inversion.
Signal inversion is a unique form of signal processing which needs its own
test procedure, the polarity test". An inverted measurement therefore
fails this check with a 180-degree deviation everywhere, and is warned
about, because the verdict is real but the diagnosis is a polarity test
this function does not perform.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies_hz` | The frequencies the phase was measured at, in hertz, strictly ascending and at least two of them. |
| `measured_phase_deg` | The measured phase at each frequency, in degrees, on the continuous branch Tables B.1 to B.9 print. |

**Returns:** The verdict, as a [`PhaseVerification`](/phonometry/reference/api/vibration/instrumentation/#phaseverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine, if the two arrays do not have the same shape, if a frequency is not positive and finite, if a phase is not finite, or if there are fewer than two frequencies or they do not strictly ascend. |
| UserWarning | [`HumanVibrationWarning`](/phonometry/reference/api/vibration/exposure/#humanvibrationwarning) when every phase error is a half turn, which is an inverted signal rather than a phase response the criterion can grade. |

## verify_running_rms_decay

```python
verify_running_rms_decay(
    measured_time_s: float,
    *,
    integration_time_s: float,
    method: str,
) -> bool
```

Check a measured decay time against Table 10 or Table 11.

The verdict is one printed row: the measured time to 10 % of the initial
value has to sit inside the printed interval for that time constant and
that average. The rate column of Table 11 is deliberately not the
criterion, for the reason [`RUNNING_RMS_DECAY_RATE_DB_PER_S`](/phonometry/reference/api/vibration/instrumentation/#running_rms_decay_rate_db_per_s)
explains.

Only the three time constants the two tables print can be checked, so an
instrument averaging over any other time is refused rather than judged
against a band the standard does not give.

**Parameters**

| Name | Description |
| :--- | :--- |
| `measured_time_s` | The measured time to 10 % of the initial indicated value, in seconds (> 0). |
| `integration_time_s` | The averaging time it was measured at, which has to be one of the printed 0,125 s, 1 s and 8 s. Keyword-only, and so is the method: two times in seconds side by side are the kind of pair a positional call gets the wrong way round in silence. |
| `method` | `"linear"` (Table 10) or `"exponential"` (Table 11). |

**Returns:** Whether the measurement is inside the printed interval.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `method` is neither average, if the measured time is not positive and finite, or if the integration time is not one of the three printed time constants. |

## verify_weighting

```python
verify_weighting(
    name: str,
    frequencies: ArrayLike,
    measured_factors: ArrayLike,
    *,
    expanded_uncertainty_percent: float | None = None,
) -> WeightingVerification
```

Check a measured weighting response against ISO 8041-1 Tables 4 and 5.

The acceptance test is the one Annex B is written in: the deviation
`(measured / design - 1) * 100` at each frequency has to sit between the
lower and upper limits of the region that frequency falls in.

**Where the laboratory's uncertainty goes.** 13.1 (folio 42) and 14.1
(folio 48) print the same sentence: compliance is demonstrated when the
result of a measurement of a deviation from a design goal, "extended by
the actual expanded uncertainty of measurement of the testing laboratory",
does not exceed the specified tolerance limits, the uncertainty being
calculated with the coverage factor `k = 2`
([`ISO8041_COVERAGE_FACTOR`](/phonometry/reference/api/vibration/instrumentation/#iso8041_coverage_factor)). So the comparison is
`deviation + U <= upper` and `deviation - U >= lower`: the band stays
where Table 5 prints it and the measurement is what widens. That is not in
conflict with 5.6.6 (folio 14), which says the Table 5 limits already
include the applicable *maximum permitted* expanded uncertainties: the
band is not widened by either sentence, and what 13.1 adds is the
laboratory's *actual* uncertainty, which is its own number and is bounded
by [`MAX_EXPANDED_UNCERTAINTY_PERCENT`](/phonometry/reference/api/vibration/instrumentation/#max_expanded_uncertainty_percent).

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | The frequencies the response was measured at, in hertz. |
| `measured_factors` | The measured weighting factors, linear and not in decibels, one per frequency. |
| `expanded_uncertainty_percent` | The testing laboratory's actual expanded uncertainty of the deviation measurement, in per cent and already expanded with `k = 2`. `None` (the default) compares the bare deviation, which is the right reading only for a measurement whose uncertainty has been shown to be negligible. |

**Returns:** The verdict, as a [`WeightingVerification`](/phonometry/reference/api/vibration/instrumentation/#weightingverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine, if the two arrays do not have the same shape, if a frequency is not positive and finite, if a measured factor is negative or not finite, or if the expanded uncertainty is negative or not finite. |

## WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT

*Constant* (`float`).

```python
WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT = 3.0
```

## weighting_tolerance_percent

```python
weighting_tolerance_percent(
    name: str,
    frequencies: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

The Table 5 band around a weighting, region by region.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`WEIGHTING_NAMES`](/phonometry/reference/api/vibration/exposure/#weighting_names). |
| `frequencies` | Frequencies at which the band is wanted, in hertz. |

**Returns:** `(upper, lower)` percentages, elementwise. `lower` is [`UNCONSTRAINED_BELOW`](/phonometry/reference/api/vibration/instrumentation/#unconstrained_below) outside the two outer transition frequencies, where the standard sets no lower limit at all.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the weighting is not one of the nine, or a frequency is not positive and finite. |

## WeightingVerification

```python
WeightingVerification(
    weighting: str,
    frequencies_hz: NDArray[np.float64],
    measured: NDArray[np.float64],
    design: NDArray[np.float64],
    deviation_percent: NDArray[np.float64],
    within_tolerance: NDArray[np.bool_],
    expanded_uncertainty_percent: float = 0.0,
)
```

One measured weighting response against its ISO 8041-1 tolerances.

**Attributes**

| Name | Description |
| :--- | :--- |
| `weighting` | The weighting the response was measured for. |
| `frequencies_hz` | The frequencies it was measured at. |
| `measured` | The measured weighting factors, as supplied. |
| `design` | The design-goal factors of ISO 8041-1 Table 3 at the same frequencies. |
| `deviation_percent` | `(measured / design - 1) * 100` elementwise, which is the quantity the standard's acceptance test is written in. |
| `within_tolerance` | Whether each frequency is inside its band, with the deviation extended by `expanded_uncertainty_percent` as 13.1 and 14.1 require. |
| `expanded_uncertainty_percent` | The testing laboratory's own expanded uncertainty, in per cent, that the verdict was reached with. `0,0` when the caller supplied none, which compares the bare deviation. |

### WeightingVerification.failing_frequencies_hz

*property*

The frequencies whose deviation falls outside the band.

### WeightingVerification.passes

*property*

Whether every measured frequency sits inside its band.

True says the frequency weighting meets ISO 8041-1, and nothing more:
the indication, linearity, overload and environmental tests of the
same standard are hardware measurements this cannot stand in for.

### WeightingVerification.plot()

```python
WeightingVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the measured response inside the tolerance band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_weighting_verification`. |

### WeightingVerification.worst_deviation_percent

*property*

The largest deviation in magnitude, signed as it was measured.
