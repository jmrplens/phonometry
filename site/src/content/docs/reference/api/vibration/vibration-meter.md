---
title: "vibration.immission.vibration_meter"
description: "The vibration meter of DIN 45669-1:2010-09 (with Corrigendum 1:2012-12)."
sidebar:
  label: "vibration_meter"
---

The vibration meter of DIN 45669-1:2010-09 (with Corrigendum 1:2012-12).

German immission control judges vibration in buildings with two standards that
print thresholds and say almost nothing about how the number reaching them was
formed: DIN 4150-2 for people in buildings and DIN 4150-3 for the buildings
themselves. DIN 45669-1 is the missing half. It defines the instrument, and
with it the quantities those thresholds are compared against, as exact
transfer functions and exact time weightings, then grades a real meter against
them.

**The chain.** A velocity signal is band-limited (5.2.3.2, Formula (3)), which
is two Butterworth pairs: a two-pole high pass at $0{,}8 f_u$ and a
two-pole low pass at $f_o / 0{,}8$. The working range is
$f_u = 1$ Hz to $f_o = 80$ Hz for buildings, and 4 Hz to 315 Hz
next to a railway, which is where DIN 45672-1 works. Frequency weighting
(Formula (4)) divides that by $1 - \mathrm{j}\,5{,}6\,\mathrm{Hz}/f$,
one more pole and one more zero, and normalising by 1 mm/s turns the result
into the dimensionless **KB signal**. Its running r.m.s. with
$\tau = 0{,}125$ s (Formula (1)) is $KB_F(t)$, the *weighted
vibration severity*, and the quantities a meter displays are its maximum
$KB_{F\mathrm{max}}$, the maximum within each 30 s clock interval
(*Takt*) and the r.m.s. of those clock maxima $KB_{FTm}$ (Formula (2)).

**Two rules of Formula (2) that are easy to miss.** A clock maximum at or
below 0,1 enters the sum as zero but still counts in $N$, so a quiet
interval lowers the average rather than being dropped from it; and a clock
interval that the measurement did not fill does not count at all (5.1.6.4), so
the averaging time is always a whole number of clock intervals.

**What Annex E adds.** DIN 4150-3 compares a peak velocity with a guideline
value that depends on frequency, so it needs a dominant frequency, and Annex D
shows two ways of finding one that do not agree. Annex E removes the question:
three weighting filters, one per building class of DIN 4150-3:1999-02 Table 1,
each the inverse of that class's guideline curve normalised to its 1 Hz to
10 Hz value. Filter the velocity with one of them and the peak of what comes
out, the *assessment velocity* $v_{Bn}$, is compared with a single
number that no longer depends on frequency: 20, 5 or 3 mm/s (Table E.2). The
filters are specified as a target magnitude with a $\pm 5$ % band and a
linear phase, which is why this module designs them as symmetric FIRs.

**Where the printed check values come from, and where one of them does not.**
Table 9 (folio 35) prints what a meter must display for a 1 mm/s sine at five
frequencies, and its $KB_F$, $KB_{F\mathrm{max}}$ and
$KB_{FTm}$ rows are reproduced by this module to the three decimals they
are printed with, ripple and all. Its $|v|_\mathrm{max}$ row is not, and
cannot be: at 31,5 Hz it prints 1,000 where Formula (5) gives 0,995, and at
315 Hz it prints 0,249 where Formula (5) gives 0,100, while the
$KB_F$ row of the same column follows Formula (5) at both. The table
contradicts itself rather than the formula, so [`KB_TEST_INDICATIONS`](/phonometry/reference/api/vibration/vibration-meter/#kb_test_indications)
carries the rows that agree with it and the other row is left to
`docs/ERRATA.md`.

**What a verdict here is and is not.** [`verify_vibration_meter`](/phonometry/reference/api/vibration/vibration-meter/#verify_vibration_meter) grades
one thing, the amplitude response against Tables 2 and 3, which is Clause
5.2.3.3 of a standard whose Clause 6 also asks for linearity, overload,
crest-factor handling, temperature, humidity and electromagnetic tests on
hardware. Passing here is necessary for conformity and is not conformity.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## assess_short_term_vibration

```python
assess_short_term_vibration(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    building_class: str,
    numtaps: int | None = None,
) -> AssessmentVelocity
```

Judge short-term vibration on a building by Annex E.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity at the foundation, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `building_class` | See [`assessment_weighting_response`](/phonometry/reference/api/vibration/vibration-meter/#assessment_weighting_response). |
| `numtaps` | See [`assessment_weighting_taps`](/phonometry/reference/api/vibration/vibration-meter/#assessment_weighting_taps). |

**Returns:** The comparison, as an [`AssessmentVelocity`](/phonometry/reference/api/vibration/vibration-meter/#assessmentvelocity).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a rate below 630 Hz, or an unknown class. |

## ASSESSMENT_GUIDE_VALUES_MM_S

*Constant* (`dict`).

```python
ASSESSMENT_GUIDE_VALUES_MM_S = {'commercial': 20.0, 'residential': 5.0, 'sensitive': 3.0}
```

## assessment_velocity

```python
assessment_velocity(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    building_class: str,
    numtaps: int | None = None,
) -> NDArray[np.float64]
```

The assessment velocity `v_Bn(t)` of Annex E, in mm/s.

The velocity is filtered with the weighting of its building class and the
constant delay of the symmetric filter is removed, so the result lines up
in time with the record it came from.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity, in millimetres per second (1-D). Annex E filters the unweighted signal, which has already been band-limited by 5.2.3. |
| `fs_hz` | Sampling frequency, in hertz. |
| `building_class` | See [`assessment_weighting_response`](/phonometry/reference/api/vibration/vibration-meter/#assessment_weighting_response). |
| `numtaps` | See [`assessment_weighting_taps`](/phonometry/reference/api/vibration/vibration-meter/#assessment_weighting_taps). |

**Returns:** `v_Bn(t)`, one value per sample.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a rate below 630 Hz, or an unknown class. |

## assessment_weighting_response

```python
assessment_weighting_response(
    frequencies_hz: ArrayLike,
    *,
    building_class: str,
) -> NDArray[np.float64]
```

The target magnitude of an Annex E weighting filter, Table E.1.

Each filter is the guideline curve of its building class inverted and
normalised to the value that curve holds from 1 Hz to 10 Hz, so filtering
with it turns a frequency-dependent comparison into a comparison with one
number. The curve is flat below 10 Hz, rises along two straight segments
to 100 Hz and is flat above it, and Table E.1 carries that last segment
up to the Nyquist frequency rather than stopping at 100 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in hertz. |
| `building_class` | The row of DIN 4150-3:1999-02 Table 1, as [`ASSESSMENT_GUIDE_VALUES_MM_S`](/phonometry/reference/api/vibration/vibration-meter/#assessment_guide_values_mm_s) keys it. |

**Returns:** The target magnitude, dimensionless, 1 below 10 Hz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency or an unknown class. |

## assessment_weighting_taps

```python
assessment_weighting_taps(
    fs_hz: float,
    *,
    building_class: str,
    numtaps: int | None = None,
) -> NDArray[np.float64]
```

A linear-phase FIR that realises an Annex E weighting.

Annex E asks for a linear phase and says why: a weighting filter that
delays different frequencies differently changes the peak it is there to
measure. A symmetric FIR is the type the annex names, and its only cost is
a constant delay of half its length, which [`assessment_velocity`](/phonometry/reference/api/vibration/vibration-meter/#assessment_velocity)
removes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs_hz` | Sampling frequency, in hertz. Table E.1 requires the Nyquist frequency to be above 315 Hz where the meter reaches that far, and this refuses a rate below 630 Hz for the same reason. |
| `building_class` | See [`assessment_weighting_response`](/phonometry/reference/api/vibration/vibration-meter/#assessment_weighting_response). |
| `numtaps` | Length of the filter, odd. The default resolves the 10 Hz corner of the target with room to spare, at half a second of taps. |

**Returns:** The filter coefficients.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a rate below 630 Hz, an even or non-positive length, or an unknown class. |

## ASSESSMENT_WEIGHTING_TOLERANCE

*Constant* (`float`).

```python
ASSESSMENT_WEIGHTING_TOLERANCE = 0.05
```

## AssessmentVelocity

```python
AssessmentVelocity(
    assessment_velocity_mm_s: float,
    guide_value_mm_s: float,
    building_class: str,
    velocity_mm_s: NDArray[np.float64],
    fs_hz: float,
)
```

One record judged by Annex E, without a dominant frequency.

**Attributes**

| Name | Description |
| :--- | :--- |
| `assessment_velocity_mm_s` | $\vert v_{Bn}\vert _\mathrm{max}$, the peak of the weighted velocity, in millimetres per second. |
| `guide_value_mm_s` | The Table E.2 value it is compared with. |
| `building_class` | The row of DIN 4150-3 Table 1 that was used. |
| `velocity_mm_s` | The weighted velocity itself, one value per sample. |
| `fs_hz` | The sampling frequency the record was read at. |

### AssessmentVelocity.plot()

```python
AssessmentVelocity.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the weighted velocity against its guideline value.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_assessment_velocity`. |

### AssessmentVelocity.ratio

*property*

The peak as a fraction of the guideline value.

### AssessmentVelocity.within_guideline

*property*

Whether the record keeps to the guideline value of Table E.2.

The same reading as DIN 4150-3 gives it: keeping to the value is what
the standard promises about, exceeding it means the question moves to
Clauses 4.2 to 4.4 rather than that damage has occurred.

## BAND_LIMIT_CORNER_FACTOR

*Constant* (`float`).

```python
BAND_LIMIT_CORNER_FACTOR = 0.8
```

## band_limitation_response

```python
band_limitation_response(
    frequencies_hz: ArrayLike,
    *,
    working_range: str = 'building',
) -> NDArray[np.complex128]
```

The band limitation of the unweighted signal, Formula (3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in hertz. |
| `working_range` | `"building"` (1 Hz to 80 Hz, the default) or `"railway"` (4 Hz to 315 Hz); see [`WORKING_RANGES_HZ`](/phonometry/reference/api/vibration/vibration-meter/#working_ranges_hz). |

**Returns:** The complex response $H_{u\mathrm{Soll}}$, whose magnitude is Formula (5).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency or an unknown range. |

## dominant_frequency

```python
dominant_frequency(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    method: Literal['zero_crossing', 'fourier'] | str = 'zero_crossing',
) -> DominantFrequency
```

The dominant frequency of a short-term event, by one of Annex D's ways.

A short-term vibration has no frequency in the physical sense, and Annex D
says so before giving two ways of naming one anyway. They can disagree,
and the disagreement matters: the frequency picks the guideline value in
DIN 4150-3, so it can change the verdict. That is the ambiguity Annex E
removes, and this function is here for the case where the frequency itself
has to be reported.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `method` | `"zero_crossing"` (D a), the default: the two zero crossings around the largest amplitude are half a period apart) or `"fourier"` (D b): the largest value of the spectrum of the whole event, with the runner-up reported beside it. |

**Returns:** The frequency and how it was found, as a [`DominantFrequency`](/phonometry/reference/api/vibration/vibration-meter/#dominantfrequency).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a non-positive rate, an unknown method, or a record whose largest amplitude has no zero crossing on both sides of it. |

## DominantFrequency

```python
DominantFrequency(
    frequency_hz: float,
    method: str,
    candidates: tuple[tuple[float, float], ...],
)
```

The dominant frequency of one event, and how it was found (Annex D).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | The dominant frequency, in hertz. |
| `method` | `"zero_crossing"` or `"fourier"`. |
| `candidates` | For the Fourier method, the two largest spectral values as `(frequency in hertz, magnitude)` pairs, largest first, which is what D b) asks a meter to report so the choice between them is made rather than assumed. Empty for the zero-crossing method. |

## KB_CORNER_HZ

*Constant* (`float`).

```python
KB_CORNER_HZ = 5.6
```

## KB_DETECTION_LIMIT

*Constant* (`float`).

```python
KB_DETECTION_LIMIT = 0.02
```

## KB_INDICATION_TOLERANCE_PERCENT

*Constant* (`float`).

```python
KB_INDICATION_TOLERANCE_PERCENT = 4.0
```

## KB_PULSE_RESPONSE_PERCENT

*Constant* (`tuple`).

```python
KB_PULSE_RESPONSE_PERCENT = ((inf, 80, 100.4), (800.0, 64, 100.3), (400.0, 32, 98.3), (200.0, 16, 89.7), (100.0, 8, 74.5), (50.0, 4, 57.6), (25.0, 2, 42.7), (12.5, 1, 30.9))
```

## KB_REFERENCE_FREQUENCY_HZ

*Constant* (`float`).

```python
KB_REFERENCE_FREQUENCY_HZ = 16.0
```

## KB_REFERENCE_INDICATIONS

*Constant* (`dict`).

```python
KB_REFERENCE_INDICATIONS = {'peak_velocity_mm_s': 1.0, 'kbf': 0.667, 'kbf_max': 0.68, 'kbf_takt_rms': 0.68}
```

## kb_signal

```python
kb_signal(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    working_range: str = 'building',
) -> NDArray[np.float64]
```

The KB signal `KB(t)` of 3.10.1.1, which is dimensionless.

The velocity is band-limited and frequency-weighted by Formula (4) and
normalised by 1 mm/s, which is the normalisation that makes the KB signal
a number rather than a velocity, so the record has to be in millimetres
per second for the result to mean what the standard says.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |

**Returns:** `KB(t)`, one value per sample.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a rate that cannot carry the working range, or an unknown range. |

## KB_TEST_INDICATIONS

*Constant* (`dict`).

```python
KB_TEST_INDICATIONS = {1.0: (0.103, 0.13, 0.13), 5.6: (0.5, 0.528, 0.528), 31.5: (0.693, 0.7, 0.7), 80.0: (0.594, 0.597, 0.597), 315.0: (0.071, 0.071, 0.071)}
```

## KB_TIME_CONSTANT_S

*Constant* (`float`).

```python
KB_TIME_CONSTANT_S = 0.125
```

## kb_weighting_response

```python
kb_weighting_response(
    frequencies_hz: ArrayLike,
    *,
    working_range: str = 'building',
) -> NDArray[np.complex128]
```

The KB frequency weighting, Formula (4).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in hertz. |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |

**Returns:** The complex response $H_{B\mathrm{Soll}}$, whose magnitude is Formula (6).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency or an unknown range. |

## kbf_signal

```python
kbf_signal(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    working_range: str = 'building',
    time_constant_s: float = 0.125,
) -> NDArray[np.float64]
```

The weighted vibration severity `KB_F(t)`, Formula (1).

The running r.m.s. is the exponential average the formula integrates, as
the single-pole recursion Annex A draws: `y[i] = (1 - a) y[i-1] + a x[i]`
with `a = 1 - exp(-1 / (tau fs))`. It starts from zero, so the first
samples ramp up like a meter switched on with the signal already present;
2 tau of record is 14 % low in mean square and 4 tau is 2 % low, which is
why a measurement is started before the event it is about.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |
| `time_constant_s` | The averaging time constant, in seconds. The standard fixes it at 0,125 s and the parameter exists so a comparison with another time weighting can be written down, not so a meter can use one. |

**Returns:** `KB_F(t)`, one value per sample.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a non-positive time constant, or a rate that cannot carry the working range. |

## measure_vibration_immission

```python
measure_vibration_immission(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    working_range: str = 'building',
    takt_duration_s: float = 30.0,
) -> VibrationMeterReading
```

Run one velocity record through the whole chain of 5.1.6.

**Start the record before the event.** Every filter here begins at rest,
so a record that begins with the signal already at full amplitude carries
the filter's own switch-on transient, and the peak is a max-hold that
keeps it: a 1 mm/s sine started at a zero crossing reads 1,06 mm/s rather
than the 1,00 mm/s of 6.2.3.12, and at 315 Hz outside the building range
it reads 0,25 mm/s where the steady response is 0,10 mm/s. That is an
artefact of the record, not of the chain, and a lead-in of a second or two
of quiet removes it, which is also how a real measurement is made.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The measured velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |
| `takt_duration_s` | The clock interval, in seconds (default 30 s). |

**Returns:** The displayed quantities, as a [`VibrationMeterReading`](/phonometry/reference/api/vibration/vibration-meter/#vibrationmeterreading).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a rate that cannot carry the working range, or a non-positive clock interval. |

## RESPONSE_TOLERANCE_LOWER_PERCENT

*Constant* (`tuple`).

```python
RESPONSE_TOLERANCE_LOWER_PERCENT = ((1.25, 0.8, 10.0), (0.5, 2.0, 20.0))
```

## response_tolerance_percent

```python
response_tolerance_percent(
    frequencies_hz: ArrayLike,
    *,
    working_range: str = 'building',
) -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

The limits of Tables 2 and 3 at each frequency, in per cent.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in hertz. |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |

**Returns:** `(lower, upper)`: the largest deviation allowed below and above the design response, both as positive percentages. A lower limit of 100 % is the standard declining to constrain the response from below outside the working range.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive frequency or an unknown range. |

## RESPONSE_TOLERANCE_UPPER_PERCENT

*Constant* (`tuple`).

```python
RESPONSE_TOLERANCE_UPPER_PERCENT = ((1.25, 0.8, 10.0), (0.0, inf, 20.0))
```

## TAKT_DURATION_S

*Constant* (`float`).

```python
TAKT_DURATION_S = 30.0
```

## takt_maxima

```python
takt_maxima(
    kbf: ArrayLike,
    fs_hz: float,
    *,
    takt_duration_s: float = 30.0,
) -> NDArray[np.float64]
```

The clock maxima `KB_FTi` of 3.10.1.4, one per whole clock interval.

A clock interval the record did not fill is not a clock interval: 5.1.6.4
says the averaging time always spans a whole number of them, so a trailing
part-interval is dropped rather than scaled up.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kbf` | The `KB_F(t)` signal (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `takt_duration_s` | The clock interval, in seconds (default 30 s). |

**Returns:** One maximum per whole clock interval, in order. Empty when the record is shorter than one interval.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad signal or a non-positive rate or interval. |

## takt_maximum_rms

```python
takt_maximum_rms(maxima: ArrayLike) -> float
```

The clock maximum r.m.s. `KB_FTm`, Formula (2).

Both rules of the formula are here: a clock maximum at or below
[`TAKT_SUPPRESSION_THRESHOLD`](/phonometry/reference/api/vibration/vibration-meter/#takt_suppression_threshold) enters the sum as zero, and the
interval it came from still counts in `N`, so a run of quiet intervals
pulls the result down instead of leaving it unchanged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `maxima` | The clock maxima of [`takt_maxima`](/phonometry/reference/api/vibration/vibration-meter/#takt_maxima). |

**Returns:** `KB_FTm`, dimensionless. Zero for an empty input, which is the answer for a record with no whole clock interval in it.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a maximum is negative or not finite. |

## TAKT_SUPPRESSION_THRESHOLD

*Constant* (`float`).

```python
TAKT_SUPPRESSION_THRESHOLD = 0.1
```

## VELOCITY_DETECTION_LIMIT_MM_S

*Constant* (`float`).

```python
VELOCITY_DETECTION_LIMIT_MM_S = 0.05
```

## verify_vibration_meter

```python
verify_vibration_meter(
    frequencies_hz: ArrayLike,
    measured_response: ArrayLike,
    *,
    weighting: Literal['kb', 'unweighted'] | str = 'kb',
    working_range: str = 'building',
    reference_frequency_hz: float = 16.0,
) -> VibrationMeterVerification
```

Check a measured amplitude response against Tables 2 and 3.

Formula (7) is a ratio of ratios: the measured response over the design
response, each divided by its own value at the reference frequency, so a
meter is graded on the shape of its response and not on the gain that a
calibration sets. The reference frequency itself carries no requirement,
the standard writing every limit "for all f not equal to f_r", and it is
dropped from the verdict rather than passed for free.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies the response was measured at, in hertz. The reference frequency has to be among them. |
| `measured_response` | The measured amplitude response at those frequencies, in any consistent unit: only its shape is graded. |
| `weighting` | `"kb"` for the weighted response of Formula (4), the default, or `"unweighted"` for the band limitation of Formula (3). |
| `working_range` | See [`band_limitation_response`](/phonometry/reference/api/vibration/vibration-meter/#band_limitation_response). |
| `reference_frequency_hz` | The reference frequency of 5.2.10, in hertz (default 16 Hz). |

**Returns:** The comparison, as a [`VibrationMeterVerification`](/phonometry/reference/api/vibration/vibration-meter/#vibrationmeterverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the two arrays disagree in shape, if a frequency or a response is not positive and finite, or if the reference frequency is not one of the measured frequencies. |

## VibrationMeterReading

```python
VibrationMeterReading(
    peak_velocity_mm_s: float,
    kbf: NDArray[np.float64],
    kbf_max: float,
    takt_maxima: NDArray[np.float64],
    kbf_takt_rms: float,
    fs_hz: float,
    measuring_time_s: float,
    averaging_time_s: float,
    working_range: str,
)
```

What a meter displays for one record (5.1.6.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `peak_velocity_mm_s` | $\vert v\vert _\mathrm{max}$, the largest absolute value of the band-limited velocity over the measuring time. |
| `kbf` | The `KB_F(t)` signal, one value per sample. |
| `kbf_max` | $KB_{F\mathrm{max}}$, its maximum. |
| `takt_maxima` | The clock maxima, one per whole clock interval. |
| `kbf_takt_rms` | $KB_{FTm}$ of Formula (2). |
| `fs_hz` | The sampling frequency the record was read at. |
| `measuring_time_s` | $T_M$, the length of the record. |
| `averaging_time_s` | $T_m$, the whole clock intervals in it. |
| `working_range` | The working range the chain was built for. |

### VibrationMeterReading.above_detection_limit

*property*

Whether the reading is above the detection limits of 5.2.2.

Below them a meter is not required to resolve anything, so a smaller
reading is not a measurement of a smaller vibration.

### VibrationMeterReading.plot()

```python
VibrationMeterReading.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw `KB_F(t)` with its maximum and the clock maxima on it.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_vibration_meter_reading`. |

## VibrationMeterVerification

```python
VibrationMeterVerification(
    frequencies_hz: NDArray[np.float64],
    deviation_percent: NDArray[np.float64],
    lower_percent: NDArray[np.float64],
    upper_percent: NDArray[np.float64],
    within_tolerance: NDArray[np.bool_],
    weighting: str,
    working_range: str,
    reference_frequency_hz: float,
)
```

One measured amplitude response against Tables 2 and 3.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies the response was measured at. |
| `deviation_percent` | `F(f)` of Formula (7) at each of them: the measured response over the design response, both normalised at the reference frequency, as a percentage departure from unity. |
| `lower_percent` | The Table 2 limit at each frequency. |
| `upper_percent` | The Table 3 limit at each frequency. |
| `within_tolerance` | Whether each frequency keeps to both limits. |
| `weighting` | `"kb"` or `"unweighted"`, which design response the deviation is against. |
| `working_range` | The working range the limits were read for. |
| `reference_frequency_hz` | The frequency both responses were normalised at. |

### VibrationMeterVerification.passes

*property*

Whether every graded frequency keeps to its limits.

### VibrationMeterVerification.plot()

```python
VibrationMeterVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the deviation against the tolerance band it is judged by.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_vibration_meter_verification`. |

### VibrationMeterVerification.worst_frequency_hz

*property*

The frequency that uses the largest share of its allowance.

## WORKING_RANGES_HZ

*Constant* (`dict`).

```python
WORKING_RANGES_HZ = {'building': (1.0, 80.0), 'railway': (4.0, 315.0)}
```
