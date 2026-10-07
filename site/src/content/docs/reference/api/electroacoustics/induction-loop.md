---
title: "electroacoustics.induction_loop"
description: "Audio-frequency induction-loop systems for hearing aids: the performance of an installed system."
sidebar:
  label: "induction_loop"
---

Audio-frequency induction-loop systems for hearing aids: the performance of an installed system.

IEC 60118-4:2014 (read in BS EN 60118-4:2015), with its Amendment 1:2017
(read in the Spanish UNE-EN IEC 60118-4:2016/A1:2018, whose text replaces
clauses 9 and 10), says what field an induction loop has to produce for a
hearing aid switched to its telecoil, and how an installer shows that it
does. The loop's components, the amplifier, the loop as a load and the neck
loop, are the subject of IEC 62489-1 and of
[`phonometry.electroacoustics.induction_loop_components`](/phonometry/reference/api/electroacoustics/induction-loop-components/).

The reference and the level
---------------------------

Everything is a level in decibels referred to a magnetic field strength of
400 mA/m (3.1), [`REFERENCE_FIELD_STRENGTH_A_PER_M`](/phonometry/reference/api/electroacoustics/induction-loop/#reference_field_strength_a_per_m):
$L = 20\lg(H / 0{,}4\ \mathrm{A/m})$ ([`field_strength_level`](/phonometry/reference/api/electroacoustics/induction-loop/#field_strength_level)).
A long-term average of -12 dB, 100 mA/m, at the telecoil gives the same
acoustic output from the hearing aid as a sound pressure level of 70 dB at
its microphone (4.3). The meter is either a true-RMS meter with the 125 ms
"F" averaging of a sound level meter or a peak programme meter (6.1); in case
of doubt the true-RMS one is definitive, and it is the one
[`field_strength_meter`](/phonometry/reference/api/electroacoustics/induction-loop/#field_strength_meter) implements, flat or A-weighted.

The requirements
----------------

For a system covering a room, the useful magnetic field volume is where the
requirements are met (8.4). They are:

* the field strength, 8.2.7 and 8.4.3: the maximum field, measured with a
  1 kHz sine (or the equivalent combi signal) and the RMS meter, is 400 mA/m
  at one point at least of the useful magnetic field volume (8.2.1), and
  every selected point is within plus or minus 3 dB of it;
* the frequency response, 8.3.7: within plus or minus 3 dB of the response at
  1 kHz from 100 Hz to 5 000 Hz, measured at least at 100 Hz, 1 kHz and 5 kHz;
* the magnetic noise with the system switched on and every input muted, 10.4.7
  (10.2.7 before Amendment 1): if the reference signal-to-noise ratio of the
  site (7.2) is above 47 dB, no point above -47 dB; below 47 dB, no point
  more than 1 dB above its level with the system switched off. Neither
  sentence covers a ratio of exactly 47 dB; the 1 dB rule is applied there
  (see `docs/ERRATA.md`).

[`verify_induction_loop_system`](/phonometry/reference/api/electroacoustics/induction-loop/#verify_induction_loop_system) judges the three. The magnetic background
noise of the site, 7.2, is a recommendation, not a requirement, and
[`assess_background_noise`](/phonometry/reference/api/electroacoustics/induction-loop/#assess_background_noise) classes it: a reference signal-to-noise ratio
above 47 dB is the ideal, 32 dB the recommended minimum below which the
shortfall "shall be reported and agreed with the system operator", and 22 dB
tolerable for short periods when the noise has no significant undesirable
tonal quality or is mostly at low frequencies.

Small systems
-------------

For a disabled refuge or call point and for a counter, Amendment 1 rewrites
clause 9. The field is measured at fixed points (Figures 2 and 3), six at
heights of 1,2 m and 1,7 m for a refuge and three at 1,2 m, 1,45 m and 1,7 m
for a counter ([`small_volume_measurement_points`](/phonometry/reference/api/electroacoustics/induction-loop/#small_volume_measurement_points)), or, by contract, at
representative points spread through a useful magnetic field volume which, at
the minimum, meets the requirements at one position at least at each of the
heights of 9.2 or 9.3 (9.4). At every point the level shall be within plus or
minus 6 dB of 400 mA/m and meet 8.3.7, at one point at least it shall reach
0 dB, and nowhere where people are expected to stand shall it exceed +8 dB
(9.5, [`verify_small_volume_system`](/phonometry/reference/api/electroacoustics/induction-loop/#verify_small_volume_system)).

Two informative passages disagree with 9.5 and are not followed: Annex A.4
allows "up to, but not greater than, +12 dB" at 1,45 m for a counter, and
calls a counter's requirement "less stringent" than a refuge's, where 9.5
applies the same limits to both (see `docs/ERRATA.md`).

Commissioning and the amplifier
-------------------------------

Amendment 1 replaces the 1,6 kHz overload test with one tied to the programme
(10.3, Table 4, [`OVERLOAD_TEST_FREQUENCIES`](/phonometry/reference/api/electroacoustics/induction-loop/#overload_test_frequencies)): with a 1 kHz sine giving a
field 7 dB below the required one, the frequency is raised at constant input
until the loop voltage doubles or the frequency of Table 4 is reached,
whichever is higher, and no clipping may appear at the frequency of Table 4
(10.3.3). One of the three ways the
amendment offers to detect clipping is the comparison of the loop voltage
with the amplifier's compliance voltage of IEC 62489-1, and that one is
computable from the loop's impedance: [`verify_amplifier_overload`](/phonometry/reference/api/electroacoustics/induction-loop/#verify_amplifier_overload).

The metal in a building lowers the field inside the loop, more at high
frequencies (Annex F), which is why 8.3.3 recommends starting the frequency
response survey at 5 kHz. Annex F gives no model of the loss: the correction
is the frequency response the installer measures and equalizes, and the
overload test above is what checks that the amplifier can afford it.

Test signals
------------

The pink noise of 6.4, band-limited by third-order Butterworth filters at
75 Hz and 6,5 kHz with a crest factor of 4 ([`loop_test_noise`](/phonometry/reference/api/electroacoustics/induction-loop/#loop_test_noise), also the
signal of IEC 62489-1 5.4.8.2 b), and the combi signal of 6.6 and Table 2,
1 kHz tone bursts of at least 1 s interleaved with at least four times as
much of that noise 6 dB lower ([`combi_signal`](/phonometry/reference/api/electroacoustics/induction-loop/#combi_signal)). 6.4 NOTE 2 prints the
theoretical responses of the band-limiting filters as -0,8 dB at 100 Hz and
-0,7 dB at 5 kHz; they are -0,71 dB and -0,82 dB, the other way round
([`band_limit_response`](/phonometry/reference/api/electroacoustics/induction-loop/#band_limit_response), `docs/ERRATA.md`).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AmplifierOverloadVerification

```python
AmplifierOverloadVerification(
    programme: OverloadTestFrequency,
    test_current_a: float,
    doubling_frequency_hz: float,
    end_frequency_hz: float,
    frequencies_hz: np.ndarray,
    voltage_v: np.ndarray,
    test_frequency_voltage_v: float,
    compliance_voltage_v: float,
)
```

The overload test of 10.3 as amended, judged on the compliance voltage.

10.3.3 as amended asks for no clipping "a la frecuencia de ensayo
especificada en la tabla 4 y al nivel especificado en el apartado 10.3.2",
so the verdict is taken at the Table 4 frequency, which the sweep always
reaches. Where the voltage doubles above that frequency, 10.3.2 carries the
sweep on to the doubling; the voltage there is drawn and kept in
`max_voltage_v`, and 10.3.3 does not judge it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `programme` | The row of Table 4 the test used. |
| `test_current_a` | The loop current at 1 kHz, 7 dB below the one that gives the required field, in amperes. |
| `doubling_frequency_hz` | Where the loop voltage first reaches twice its value at 1 kHz, in hertz; infinite when it does not double below 20 kHz (or below the top of the given current response). |
| `end_frequency_hz` | Where the sweep ends: the higher of the doubling frequency and the Table 4 frequency, in hertz. |
| `frequencies_hz` | The sweep from 1 kHz to its end, in hertz. |
| `voltage_v` | The RMS loop voltage along it, in volts. |
| `test_frequency_voltage_v` | The RMS loop voltage at the frequency of Table 4, where 10.3.3 judges the test, in volts. |
| `compliance_voltage_v` | The amplifier's compliance voltage (IEC 62489-1:2010 5.4.8), in volts. |

### AmplifierOverloadVerification.headroom_db

*property*

The compliance voltage over the voltage at the Table 4 frequency, in dB.

### AmplifierOverloadVerification.max_voltage_v

*property*

The highest loop voltage of the whole sweep, in volts.

Higher than `test_frequency_voltage_v` when the sweep runs on
past the Table 4 frequency to the doubling; 10.3.3 does not judge it.

### AmplifierOverloadVerification.passes

*property*

Whether the voltage at the Table 4 frequency is within compliance (10.3.3).

### AmplifierOverloadVerification.plot()

```python
AmplifierOverloadVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the loop voltage along the sweep against the compliance voltage.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the voltage curve's `Axes.plot`. |

## assess_background_noise

```python
assess_background_noise(
    noise_levels_db: ArrayLike,
    *,
    noise_is_tonal: bool = False,
) -> BackgroundNoiseAssessment
```

How quiet is the site magnetically? (IEC 60118-4:2014 7.2).

The magnetic background noise is measured A-weighted with the loop
switched off, everything else normally in use on and dimmable lighting
half-dimmed, at enough points of the intended volume, normally at 1,2 m
for seated and 1,7 m for standing listeners (7.1). Its difference from the
reference level, the reference signal-to-noise ratio, is taken at the
noisiest point, because that is where a listener hears the most of it.

7.2 sets no requirement, only recommendations: above 47 dB is the ideal for
theatres and places where the aesthetic value of speech matters, 32 dB is
the recommended minimum, and below it the ratio "shall be reported and
agreed with the system operator". As low as 22 dB may be tolerable for
short periods when the noise "has no significant undesirable tonal quality
or is mostly at low frequencies"; `noise_is_tonal=True` declares that it
does not, and withholds that relaxation.

**Parameters**

| Name | Description |
| :--- | :--- |
| `noise_levels_db` | A-weighted noise level at each point, in dB re 400 mA/m. |
| `noise_is_tonal` | The noise has a significant undesirable tonal quality and is not mostly at low frequencies. |

**Returns:** A [`BackgroundNoiseAssessment`](/phonometry/reference/api/electroacoustics/induction-loop/#backgroundnoiseassessment).

## BackgroundNoiseAssessment

```python
BackgroundNoiseAssessment(noise_levels_db: np.ndarray, noise_is_tonal: bool)
```

The magnetic background noise of a site against 7.2 of IEC 60118-4:2014.

The ratio, the category and the reporting duty are read from the noise
levels and the 47 dB, 32 dB and 22 dB that 7.2 prints, so they are not
fields: an assessment cannot be built to place a site in a class its
noise does not reach.

**Attributes**

| Name | Description |
| :--- | :--- |
| `noise_levels_db` | The A-weighted noise level at each point with the loop switched off, in dB re 400 mA/m. |
| `noise_is_tonal` | Whether the noise was declared tonal and not mostly at low frequencies, which withholds the 22 dB relaxation. |

### BackgroundNoiseAssessment.category

*property*

The class 7.2 puts the site in.

`"ideal"` (above 47 dB), `"acceptable"` (32 dB to 47 dB),
`"tolerable_for_short_periods"` (22 dB to 32 dB, only for noise
without an undesirable tonal quality or mostly at low frequencies) or
`"below_tolerable"`.

### BackgroundNoiseAssessment.plot()

```python
BackgroundNoiseAssessment.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the noise at each point against the 47, 32 and 22 dB lines.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the noise levels' `Axes.plot`. |

### BackgroundNoiseAssessment.reference_signal_to_noise_ratio_db

*property*

The reference level less the noisiest point, in dB.

The "reference signal-to-noise ratio" of 7.2: the levels are in dB re
400 mA/m, the reference level, so the ratio is the loudest level with
its sign changed.

### BackgroundNoiseAssessment.report_required

*property*

Whether the ratio is below 32 dB.

7.2: such a ratio "shall be reported and agreed with the system
operator".

## band_limit_response

```python
band_limit_response(frequencies_hz: ArrayLike) -> np.ndarray
```

The theoretical response of the band limiting of the pink noise, in dB.

6.4 band-limits the pink noise with third-order Butterworth high-pass and
low-pass filters, -3 dB at 75 Hz and 6,5 kHz, whose combined response is

$$
|H|^2 = \frac{1}{1 + (75/f)^6}\,\frac{1}{1 + (f/6500)^6}.
$$

At 100 Hz it is -0,71 dB and at 5 kHz -0,82 dB. 6.4 NOTE 2, and NOTE 3 to
5.4.8.2 of IEC 62489-1:2010, print -0,8 dB at 100 Hz and -0,7 dB at 5 kHz,
the two exchanged (see `docs/ERRATA.md`). The plus or minus 1 dB flatness
6.4 requires from 100 Hz to 5 kHz holds either way.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in hertz. |

**Returns:** The response, in dB.

## combi_signal

```python
combi_signal(
    fs: int,
    *,
    sine_seconds: float = 1.0,
    noise_seconds: float = 4.0,
    cycles: int = 1,
    seed: int | None = None,
) -> np.ndarray
```

The combi signal of IEC 60118-4:2014 6.6 and Table 2.

Bursts of a 1 kHz sine at an RMS of 1, with 5 ms rise and fall times,
interleaved with the pink noise of 6.4 at an RMS 6 dB lower: the sine's
peaks sit 3 dB below the maximum peak of noise of crest factor 4, as
Table 2 notes ($\sqrt{2}$ against $4 \times 10^{-6/20}$,
-3,03 dB). Each burst lasts at least 1 s so that either meter settles,
and the noise at least four times as long, so the amplifier runs cooler
than on a steady sine while the level of the sine can still be read.
Every transition is at a zero crossing: the bursts start and end on the
sine's zeros, under their ramps, and each stretch of noise is cut at its
own zero crossings.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `sine_seconds` | Duration of each sine burst, at least 1 s; rounded to a whole number of periods. |
| `noise_seconds` | Duration of each stretch of noise, at least 4 s and at least four times `sine_seconds`. It grows to four times the sine burst when rounding the burst to whole periods has lengthened it, so the ratio of 4:1 is never reduced, and by the few samples it takes to end on a zero crossing. |
| `cycles` | Number of burst-and-noise cycles. |
| `seed` | Seed for the noise generator. |

**Returns:** The signal, starting with a sine burst.

## field_strength

```python
field_strength(level_db: ArrayLike) -> np.ndarray
```

The magnetic field strength of a level in dB re 400 mA/m, in A/m.

The inverse of [`field_strength_level`](/phonometry/reference/api/electroacoustics/induction-loop/#field_strength_level): -12 dB is the 100 mA/m of
4.3, and plus or minus 3 dB span 283 mA/m to 565 mA/m (10.2 as amended
prints 566 mA/m, which is $400\sqrt{2}$).

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_db` | Level, in dB re 400 mA/m. |

**Returns:** The RMS field strength, in A/m.

## field_strength_level

```python
field_strength_level(field_strength_a_per_m: ArrayLike) -> np.ndarray
```

The magnetic field strength level, in dB re 400 mA/m (IEC 60118-4:2014 3.1).

$$
L = 20\lg\frac{H}{0{,}4\ \mathrm{A/m}}
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_strength_a_per_m` | RMS magnetic field strength, in A/m. |

**Returns:** The level, in dB re 400 mA/m.

## field_strength_meter

```python
field_strength_meter(
    x: ArrayLike,
    fs: int,
    *,
    weighting: str = 'Z',
) -> FieldStrengthReading
```

Read a magnetic field strength record like the true-RMS meter of 6.1.3.

The meter of IEC 60118-4:2014 6.1.3 is a sound level meter with a
magnetic pick-up coil in place of the microphone, equalized flat within
plus or minus 1 dB from 50 Hz to 10 kHz, with a true-RMS detector and the
125 ms averaging of its "F" mode. The A-weighting of IEC 61672-1 is what
clause 7 and 10.4 measure noise with. In case of doubt this meter, not the
peak programme meter of 6.1.4, is definitive (6.1.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | The field strength record, in A/m, as the calibrated pick-up gives it. |
| `fs` | Sample rate, in hertz. |
| `weighting` | `"Z"` for the flat response of 6.1.2, `"A"` for the A-weighted noise measurements of 7.1 and 10.4.6. |

**Returns:** A [`FieldStrengthReading`](/phonometry/reference/api/electroacoustics/induction-loop/#fieldstrengthreading).

## FieldStrengthReading

```python
FieldStrengthReading(
    fs: int,
    weighting: str,
    times_s: np.ndarray,
    levels_db: np.ndarray,
    maximum_db: float,
    equivalent_db: float,
)
```

What the true-RMS field strength meter of IEC 60118-4:2014 6.1.3 reads.

**Attributes**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate of the record, in hertz. |
| `weighting` | `"Z"` (flat, 6.1.2) or `"A"` (the noise measurements of clause 7 and 10.4). |
| `times_s` | The time of each reading, in seconds. |
| `levels_db` | The time-weighted level, 125 ms exponential averaging, in dB re 400 mA/m. |
| `maximum_db` | The maximum indication over the record, the "maximum value of the magnetic field" that 8.2.7 sets to 400 mA/m, in dB re 400 mA/m. |
| `equivalent_db` | The level of the mean square over the whole record, in dB re 400 mA/m. |

### FieldStrengthReading.plot()

```python
FieldStrengthReading.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the meter reading against time, with the 0 dB reference.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the level curve's `Axes.plot`. |

## InductionLoopVerification

```python
InductionLoopVerification(
    clause: str,
    layout: str,
    requirements: tuple[LoopRequirement, ...],
    background_noise: BackgroundNoiseAssessment | None = None,
)
```

The IEC 60118-4:2014 verdict on an installed induction-loop system.

**Attributes**

| Name | Description |
| :--- | :--- |
| `clause` | `"8"` for a system judged on its useful magnetic field volume, `"9"` for a small-volume system as amended. |
| `layout` | `"useful_volume"` for clause 8, or the small-volume layout (`"refuge_small"`, `"refuge_large"`, `"counter"`, `"refuge_useful_volume"`, `"counter_useful_volume"`). |
| `requirements` | One [`LoopRequirement`](/phonometry/reference/api/electroacoustics/induction-loop/#looprequirement) per requirement measured. |
| `background_noise` | The 7.2 assessment of the site, when the noise with the loop off was given; a recommendation, so not part of `passes`. |

### InductionLoopVerification.failed

*property*

The names of the requirements that are not met.

### InductionLoopVerification.passes

*property*

Whether every requirement measured is met; `False` when none was.

### InductionLoopVerification.plot()

```python
InductionLoopVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the worst margin of every requirement as a bar.

A requirement is met when its bar stands at or above zero.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars' `Axes.bar`. |

### InductionLoopVerification.requirement()

```python
InductionLoopVerification.requirement(name: str) -> LoopRequirement
```

The verdict on one requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Its [`LoopRequirement.name`](/phonometry/reference/api/electroacoustics/induction-loop/#looprequirement). |

**Returns:** The [`LoopRequirement`](/phonometry/reference/api/electroacoustics/induction-loop/#looprequirement).

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | when that requirement was not judged. |

## loop_test_noise

```python
loop_test_noise(
    fs: int,
    seconds: float,
    *,
    rms: float = 1.0,
    seed: int | None = None,
) -> np.ndarray
```

The pink noise test signal of IEC 60118-4:2014 6.4.

Pink noise band-limited by third-order Butterworth high-pass and low-pass
filters, -3 dB at 75 Hz and 6,5 kHz, with "a peak-to-peak voltage (as
measured with an oscilloscope) to true r.m.s. voltage ratio of at least
18 dB (crest factor = 4)". The same
signal drives the compliance voltage measurement of IEC 62489-1:2010
5.4.8.2 b), which asks for 18 dB plus or minus 2 dB.

Gaussian noise has no crest factor of its own: in 60 s at 48 kHz it
reaches about 5,5 times its RMS, a ratio of 21 dB, which meets 6.4 and
fails 5.4.8.2 b). The noise is therefore clipped at 4 times its RMS and
rescaled, which gives a peak-to-peak ratio of 18,1 dB and meets both, once
the record is long enough to reach 4 times its RMS both ways: some tens of
seconds make that certain, which is the length both measurements run for.
The filters are the bilinear transforms of the Butterworth prototypes at
`fs`, so the response at 5 kHz differs from the analog one of
[`band_limit_response`](/phonometry/reference/api/electroacoustics/induction-loop/#band_limit_response) by a tenth of a decibel at 48 kHz; 6.4
allows plus or minus 1 dB for exactly that.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `seconds` | Duration, in seconds. |
| `rms` | RMS value of the signal, in whatever unit it is scaled to. |
| `seed` | Seed for the noise generator; the same seed reproduces the same record. |

**Returns:** The signal.

## LoopRequirement

```python
LoopRequirement(
    name: str,
    clause: str,
    values_db: tuple[float, ...],
    lower_db: tuple[float, ...],
    upper_db: tuple[float, ...],
)
```

One requirement of IEC 60118-4:2014, judged on every value it covers.

Each judged value has its own lower and upper limit (minus or plus
infinity where the requirement sets none), because the system-noise limit
of 10.4.7 can differ from point to point.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | `"field_strength"` (8.4.3), `"field_strength_reached"` (8.2.7, or 9.5 for a small volume), `"frequency_response"` (8.3.7), `"system_noise"` (10.4.7), `"field_strength_range"` or `"standing_area"` (9.5). |
| `clause` | The subclause that states it, as amended. |
| `values_db` | The judged values, in dB. |
| `lower_db` | The lower limit of each, in dB. |
| `upper_db` | The upper limit of each, in dB. |

### LoopRequirement.margins_db

*property*

How far inside its limits each value lies, in dB (negative outside).

Each margin is settled to nine decimal places, a nanodecibel, so that a
value on a limit reached through floating-point arithmetic is on it: a
response of -18,6 dB against -15,6 dB at 1 kHz has a margin of 0 dB,
not -0,000 000 000 000 001 8 dB.

### LoopRequirement.passes

*property*

Whether every value lies within its limits, both inclusive.

Judged on the settled `margins_db`, so an edge reached from
decimal readings passes.

### LoopRequirement.plot()

```python
LoopRequirement.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each judged value against its limits.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the values' `Axes.plot`. |

### LoopRequirement.worst_margin_db

*property*

The smallest margin, in dB: negative when the requirement fails.

## magnetic_flux_density

```python
magnetic_flux_density(field_strength_a_per_m: ArrayLike) -> np.ndarray
```

The magnetic flux density in air of a field strength (IEC 60118-4:2014 E.6).

$B = \mu_0 \mu_\mathrm{r} H$ with $\mu_\mathrm{r} = 1$ in air,
so 1 A/m is $1{,}2566\ \mu\mathrm{T}$ and 400 mA/m about
$0{,}503\ \mu\mathrm{T}$. E.6 prints 1,256; the last digit rounds to
7 (see `docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_strength_a_per_m` | Magnetic field strength, in A/m. |

**Returns:** The flux density, in tesla.

## OVERLOAD_TEST_FREQUENCIES

*Constant* (`mapping`).

```python
OVERLOAD_TEST_FREQUENCIES = {'transient_speech': OverloadTestFrequency(programme='speech for transient use, for example small-volume systems', power_bandwidth_limit_hz=1250.0, test_frequency_hz=2500.0), 'speech': OverloadTestFrequency(programme='speech (default)', power_bandwidth_limit_hz=1600.0, test_frequency_hz=3150.0), 'music': OverloadTestFrequency(programme='music', power_bandwidth_limit_hz=2000.0, test_frequency_hz=4000.0)}
```

## OverloadTestFrequency

```python
OverloadTestFrequency(
    programme: str,
    power_bandwidth_limit_hz: float,
    test_frequency_hz: float,
)
```

One row of Table 4 of IEC 60118-4:2014/A1:2017.

**Attributes**

| Name | Description |
| :--- | :--- |
| `programme` | The typical programme material of the system. |
| `power_bandwidth_limit_hz` | The upper limit of the maximum power bandwidth it needs, in hertz. |
| `test_frequency_hz` | The frequency the overload test is run to, about twice that limit, in hertz. |

## REFERENCE_FIELD_STRENGTH_A_PER_M

*Constant* (`float`).

```python
REFERENCE_FIELD_STRENGTH_A_PER_M = 0.4
```

## small_volume_measurement_points

```python
small_volume_measurement_points(layout: str) -> np.ndarray
```

The measurement points of a disabled refuge or a counter (clause 9 as amended).

`"refuge_small"` is Figure 2 a), for a magnetic field source of small
dimensions: along the perpendicular and plus or minus 45 degrees from it,
at 300 mm and 500 mm from the reference point. `"refuge_large"` is
Figure 2 b), for a larger source such as a vertical loop: three points on
a row 424 mm wide at 300 mm from the reference line and three on a row
700 mm wide 200 mm further. Both are taken at 1,2 m and 1,7 m (9.2).
`"counter"` is Figure 3: on the semicircle of 300 mm radius around the
reference point, at its bottom and 150 mm to either side, at 1,2 m,
1,45 m and 1,7 m (9.3).

Amendment 1 corrects the key of Figure 2 a): the outer radius is
$l_2 + l_3$ = 500 mm, where the 2014 key printed "$l_3$ outer
radius 200", smaller than the inner one (see `docs/ERRATA.md`). The offset
$l_1$ between the source and the reference is the installer's
choice and is not part of the points.

**Parameters**

| Name | Description |
| :--- | :--- |
| `layout` | `"refuge_small"`, `"refuge_large"` or `"counter"`. |

**Returns:** The points, shape `(heights, points, 3)`: $x$ across, $y$ away from the reference into the area where people stand, $z$ the height above the floor, all in metres.

## telecoil_response

```python
telecoil_response(angle_deg: ArrayLike) -> np.ndarray
```

The relative response of a telecoil off its axis, in dB (IEC 60118-4:2014 E.2).

A telecoil follows a cosine law, $20\lg|\cos\theta|$: 3 dB down at
45 degrees off its magnetic axis and 9,3 dB down at 70 degrees
(Figure E.6). A telecoil at right angles to the field picks up nothing,
which is why the measurements of 8.1 are made with the coil vertical
unless the users kneel or lie.

The cosine is taken as the sine of the angle from the nearest null,
$|\cos\theta| = \sin|90^\circ - (\theta \bmod 180^\circ)|$, so a
right angle gives exactly zero: $\cos(\pi/2)$ in floating point is
$6 \times 10^{-17}$, which would read as about -324 dB instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `angle_deg` | Angle between the telecoil's axis and the field, in degrees. |

**Returns:** The response relative to the one on axis, in dB; minus infinity at 90 and 270 degrees.

## verify_amplifier_overload

```python
verify_amplifier_overload(
    required_current_a: float,
    impedance: LoopImpedance,
    compliance_voltage_v: float,
    *,
    programme: str = 'speech',
    current_response: AmplifierFrequencyResponse | None = None,
) -> AmplifierOverloadVerification
```

Does the amplifier clip in the overload test of 10.3 as amended?

10.3.2 as amended: a 1 kHz sine is set 7 dB below the field required at a
point, the voltage across the loop is measured, and the frequency is
raised at the same input until that voltage doubles or the frequency of
Table 4 is reached, whichever is the higher frequency. No clipping may
appear at the frequency of Table 4 and the level of 10.3.2 (10.3.3), and
that is where the verdict is taken; the rest of the sweep is drawn and
its highest voltage kept, but not judged. Of the three ways to detect
clipping the amendment lists,
the second compares the loop voltage with the amplifier's compliance
voltage of IEC 62489-1, and that is the one computed here: the loop is a
series resistance and inductance, and the current follows the amplifier's
frequency response into it, which is where a correction for metal loss
shows (10.3.1).

The sweep looks for the first frequency where the voltage doubles, up to
20 kHz, the top of the audio band, or up to the highest frequency of the
given current response; a loop that is mostly resistive and flat may not
double at all, and then the test ends at the Table 4 frequency. A current
response that peaks and falls again, as a correction for metal loss can,
may double the voltage and then bring it back below twice its start; the
sweep stops at that first doubling. It is found exactly: the response is
read log-linearly between its measured frequencies, and between two of
them the logarithm of the voltage, a straight line in the logarithm of
frequency plus $\tfrac{1}{2}\ln(R^2 + (2\pi f L)^2)$, is convex in
it, so the voltage crosses twice its start at most once going up in each
interval, and the first interval whose upper end has doubled holds the
first doubling.

**Parameters**

| Name | Description |
| :--- | :--- |
| `required_current_a` | The RMS loop current at 1 kHz that gives the required field strength at the chosen point, in amperes. |
| `impedance` | The loop's [`LoopImpedance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loopimpedance) ([`loop_impedance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_impedance)). |
| `compliance_voltage_v` | The amplifier's compliance voltage, in volts ([`compliance_voltage`](/phonometry/reference/api/electroacoustics/induction-loop-components/#compliance_voltage)). |
| `programme` | The row of [`OVERLOAD_TEST_FREQUENCIES`](/phonometry/reference/api/electroacoustics/induction-loop/#overload_test_frequencies): `"transient_speech"`, `"speech"` (the default of Table 4) or `"music"`. |
| `current_response` | The amplifier's current response into the loop, relative to 1 kHz ([`amplifier_frequency_response`](/phonometry/reference/api/electroacoustics/induction-loop-components/#amplifier_frequency_response)); `None` for a flat current, which is what a current-drive amplifier delivers (E.3). |

**Returns:** An [`AmplifierOverloadVerification`](/phonometry/reference/api/electroacoustics/induction-loop/#amplifieroverloadverification).

## verify_induction_loop_system

```python
verify_induction_loop_system(
    field_strength_levels_db: ArrayLike,
    *,
    specified_level_db: float = 0.0,
    frequencies_hz: ArrayLike | None = None,
    response_db: ArrayLike | None = None,
    background_noise_levels_db: ArrayLike | None = None,
    system_noise_levels_db: ArrayLike | None = None,
    noise_is_tonal: bool = False,
) -> InductionLoopVerification
```

Does an installed loop meet IEC 60118-4:2014 over its useful volume?

The requirements of clause 8 and of 10.4 as amended, on the measurements an
installer makes at the selected points of the useful magnetic field volume,
normally at 1,2 m for seated and 1,7 m for standing listeners (8.4.2):

* `"field_strength"` (8.4.3): every level within plus or minus 3 dB of
  the level specified according to 8.2.7, which is 400 mA/m, 0 dB, with a
  1 kHz sine or the combi signal and the true-RMS meter. Measured with
  another signal or meter, the specified level is the reading the
  manufacturer states for 400 mA/m (Table 3 gives -6 dB for pink noise on
  the RMS meter), passed as `specified_level_db`;
* `"field_strength_reached"` (8.2.7): the maximum value of the field is
  400 mA/m "at one point, at least, within the useful magnetic field
  volume" (8.2.1), so the highest level reaches the specified one. A
  spread that sits within its window but wholly below the reference, set
  too low, fails here;
* `"frequency_response"` (8.3.7): at every point, within plus or minus
  3 dB of the response at 1 kHz from 100 Hz to 5 000 Hz, measured at least
  at 100 Hz, 1 kHz and 5 kHz. The response is the field spectrum less the
  source spectrum (8.3.2 d), or the field at each sine frequency;
* `"system_noise"` (10.4.7, which was 10.2.7 before Amendment 1): the
  A-weighted level with the system on and every input muted. The site's
  reference signal-to-noise ratio is taken at the noisiest point with the
  system off. Above 47 dB, no point may exceed -47 dB; otherwise no point
  may exceed its own level with the system off by more than 1 dB, so the
  two sets of levels are paired point by point. 10.4.7 prints "greater
  than 47 dB" and "less than 47 dB", so a ratio of exactly 47 dB falls in
  neither sentence; the 1 dB rule is applied there, since 7.2 calls only
  a ratio above 47 dB ideal (see `docs/ERRATA.md`).

Every requirement is judged on what was given; one not measured is not
judged, and a verdict with none fails. The background noise with the loop
off is also assessed against the recommendations of 7.2
([`assess_background_noise`](/phonometry/reference/api/electroacoustics/induction-loop/#assess_background_noise)), which are not requirements.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_strength_levels_db` | The field strength level at each selected point, in dB re 400 mA/m. |
| `specified_level_db` | The level specified according to 8.2.7 for the signal and meter used, in dB re 400 mA/m. |
| `frequencies_hz` | The frequencies of the response, in hertz, including 100 Hz, 1 kHz and 5 kHz. |
| `response_db` | The response at each frequency, in dB on any fixed reference, for one point or one row per point. |
| `background_noise_levels_db` | The A-weighted level at each point with the loop switched off, in dB re 400 mA/m. |
| `system_noise_levels_db` | The A-weighted level at the same points with the system on and every input muted, in dB re 400 mA/m. |
| `noise_is_tonal` | The background noise has a significant undesirable tonal quality and is not mostly at low frequencies, which withholds the 22 dB relaxation of 7.2 ([`assess_background_noise`](/phonometry/reference/api/electroacoustics/induction-loop/#assess_background_noise)). |

**Returns:** An [`InductionLoopVerification`](/phonometry/reference/api/electroacoustics/induction-loop/#inductionloopverification).

## verify_small_volume_system

```python
verify_small_volume_system(
    field_strength_levels_db: ArrayLike,
    *,
    layout: str,
    heights_m: ArrayLike | None = None,
    standing_area_levels_db: ArrayLike | None = None,
    frequencies_hz: ArrayLike | None = None,
    response_db: ArrayLike | None = None,
) -> InductionLoopVerification
```

Does a refuge, call-point or counter loop meet clause 9 as amended?

The requirements of 9.5 as Amendment 1 writes them, at the measurement
points of Figure 2 (a refuge) or Figure 3 (a counter), or at the
representative points of a useful magnetic field volume agreed by contract
in their place (9.4):

* `"field_strength_range"`: at every point within plus or minus 6 dB of
  400 mA/m, measured according to 8.2;
* `"field_strength_reached"`: at one point at least, 0 dB or more;
* `"standing_area"`: nowhere in the area where people are expected to
  stand above +8 dB, judged on the measurement points and on any survey
  of that area given as `standing_area_levels_db`;
* `"frequency_response"`: 8.3.7 at every point.

A useful volume replaces the points of 9.2 (`"refuge_useful_volume"`)
or of 9.3 (`"counter_useful_volume"`), and 9.4 asks it, as a minimum, to
meet the requirements at one position at least at each height of the
clause it replaces: 1,2 m and 1,7 m for a refuge, and 1,2 m, 1,45 m and
1,7 m for a counter. Every point is held to 9.5 all the same, so the
minimum comes down to the points including each of those heights, and
`heights_m` says which height each point was taken at.

The informative Annex A.4 allows up to +12 dB at 1,45 m for a counter;
9.5 does not, and 9.5 is what is applied (see `docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_strength_levels_db` | The level at each measurement point, in dB re 400 mA/m: shape `(heights, points)` for a layout of Figures 2 and 3, `(2, 6)` for a refuge and `(3, 3)` for a counter, in the order of [`small_volume_measurement_points`](/phonometry/reference/api/electroacoustics/induction-loop/#small_volume_measurement_points); any shape for a useful volume. |
| `layout` | `"refuge_small"`, `"refuge_large"` or `"counter"` for the points of Figures 2 and 3; `"refuge_useful_volume"` or `"counter_useful_volume"` for a useful volume of 9.4 in their place. |
| `heights_m` | The height of each point of a useful volume above the floor, in metres, in the shape of `field_strength_levels_db`; required for a useful volume, and refused for the fixed layouts, whose heights are those of Figures 2 and 3. |
| `standing_area_levels_db` | Levels surveyed elsewhere in the area where people are expected to stand, in dB re 400 mA/m. |
| `frequencies_hz` | The frequencies of the response, in hertz, including 100 Hz, 1 kHz and 5 kHz. |
| `response_db` | The response at each frequency, one row per point. |

**Returns:** An [`InductionLoopVerification`](/phonometry/reference/api/electroacoustics/induction-loop/#inductionloopverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a fixed layout's levels of the wrong shape, or a useful volume without a point at a height of 9.2 or 9.3. |
