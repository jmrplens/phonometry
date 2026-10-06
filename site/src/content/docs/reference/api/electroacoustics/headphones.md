---
title: "electroacoustics.headphones"
description: "Headphones and earphones: the characteristics of IEC 60268-7:2010 that are computations."
sidebar:
  label: "headphones"
---

Headphones and earphones: the characteristics of IEC 60268-7:2010 that are computations.

IEC 60268-7:2010 (Edition 3.0) lists what the manufacturer of a headphone,
headset, earphone or earset states, and how each characteristic is measured.
Most of the clauses describe a set-up and a reading; this module holds the
parts that are arithmetic on what was read, and the verdicts where the part
sets a limit. The simulated programme signal several of them use is the one
of IEC 60268-1:1985 Clause 7, in
[`phonometry.electroacoustics.programme_signal`](/phonometry/reference/api/electroacoustics/programme-signal/).

The code (Clause 4)
-------------------

A headphone is classified by the code `60268-7-IEC-XXXX-NNRN-N`: four
letters for the transducer principle, the type of earphone, the acoustic
coupling to the ear canal and the radiation to the outside
([`TRANSDUCER_PRINCIPLES`](/phonometry/reference/api/electroacoustics/headphones/#transducer_principles), [`EARPHONE_TYPES`](/phonometry/reference/api/electroacoustics/headphones/#earphone_types),
[`ACOUSTIC_COUPLINGS`](/phonometry/reference/api/electroacoustics/headphones/#acoustic_couplings), [`BACK_RADIATIONS`](/phonometry/reference/api/electroacoustics/headphones/#back_radiations)), the impedance in ohms in
"mantissa and exponent" form, and the number of channels. The clause prints
three impedances, 8 ohm as `08R0`, 32 ohm as `32R0` and 600 ohm as
`06R2`: a two-digit mantissa times ten to the digit after the `R`. The
600 ohm example settles the one choice the rule leaves open, between `06R2`
and `60R1`: the exponent takes every trailing zero, so 150 ohm is `15R1`
and 300 ohm `03R2` ([`impedance_code`](/phonometry/reference/api/electroacoustics/headphones/#impedance_code)). [`HeadphoneClassification`](/phonometry/reference/api/electroacoustics/headphones/#headphoneclassification)
writes the code and [`parse_classification_code`](/phonometry/reference/api/electroacoustics/headphones/#parse_classification_code) reads it.

Impedance (8.2)
---------------

The rated impedance is a pure resistance the manufacturer states, "chosen so
that the lowest value of the modulus of the actual impedance within the rated
frequency range is not less than 80 % of the rated value"; a dip below that
anywhere from 0 kHz to 20 kHz "should be stated in the specification". The
modulus is measured "at least over the frequency range 20 Hz to 20 kHz"
(8.2.2.2). [`verify_rated_impedance`](/phonometry/reference/api/electroacoustics/headphones/#verify_rated_impedance) judges both.

Voltages, powers and sound pressure levels (8.3 to 8.5)
-------------------------------------------------------

Every input of IEC 60268-7 is a source e.m.f. $E$ applied through the
rated source impedance $R_\mathrm{s}$. The **characteristic voltage**
(8.3.3) is the 500 Hz sinusoidal e.m.f. that produces 94 dB in the coupler or
ear simulator; the headphone is linear there, so one reading $L$ at an
e.m.f. $E$ gives it as $E\,10^{(94 - L)/20}$
([`characteristic_voltage`](/phonometry/reference/api/electroacoustics/headphones/#characteristic_voltage)). The **simulated programme signal
characteristic voltage** (8.3.4) is the same with the programme signal, and
8.3.5 adds the A-weighting of IEC 61672-1 and the inverse of the free-field
response of the head and torso simulator of IEC 60959 to the coupler's output.
The NOTE under Figure 3 says how to do that without filters: "Power summation
of the 1/3-octave-analized data multiplied by filtering coefficients given by
IEC 61672-1 and/or IEC 60969 gives the corrected voltage" (the second
standard is IEC 60959, see `docs/ERRATA.md`). [`programme_signal_level`](/phonometry/reference/api/electroacoustics/headphones/#programme_signal_level)
is that power sum,

$$
L = 10\lg \sum_k 10^{(L_k + A_k - F_k)/10},
$$

with $A_k$ the A-weighting at the exact centre of band $k$ and
$F_k$ the free-field response, and
[`programme_characteristic_voltage`](/phonometry/reference/api/electroacoustics/headphones/#programme_characteristic_voltage) turns it into the e.m.f. for 94 dB,
for each fitting of the headphone, and averages the e.m.f. of the fittings as
8.3.5 g) asks ("3 to 5 measurements").

8.4 states each of these as a power instead, "derived from the corresponding
voltages (8.3) and the rated impedance": the power the e.m.f. dissipates in a
pure resistance equal to the rated impedance $R$ connected in place of
the headphone, $P = E^2 R/(R + R_\mathrm{s})^2$
([`headphone_input_power`](/phonometry/reference/api/electroacoustics/headphones/#headphone_input_power), and [`headphone_source_emf`](/phonometry/reference/api/electroacoustics/headphones/#headphone_source_emf) the other way
round). The **working sound pressure level** of 8.5.2 b) to d) is the level at
the e.m.f. that dissipates 1 mW that way ([`working_sound_pressure_level`](/phonometry/reference/api/electroacoustics/headphones/#working_sound_pressure_level)).
The method of 8.5.3 c) sets the e.m.f. differently, so that the voltage
across the headphone's own input connector is $\sqrt{1\ \mathrm{mW} \cdot R}$; the two agree only when the headphone's impedance at 500 Hz is the
rated one, and the function gives the second reading when that impedance is
passed (see `docs/ERRATA.md`).

8.3.1 NOTE 3 recommends that the rated source e.m.f. "should, preferably, not
exceed the characteristic voltage (see 8.3.3) by more than 10 dB to 15 dB";
the excess is $20\lg$ of their ratio, and a preference stated as a range
is not a limit, so no verdict is offered on it.

The clipped programme signal of 8.3.2, which rates the voltages a headphone
survives, has "a frequency distribution as specified in IEC 60268-1, and a
peak-to-r.m.s ratio between 1,8 and 2,2" ([`check_limiting_test_signal`](/phonometry/reference/api/electroacoustics/headphones/#check_limiting_test_signal)).
A protective device "causes a change of at least 1 dB in the sensitivity" at
its protection voltage (8.3.6.2 b), which [`protection_voltage`](/phonometry/reference/api/electroacoustics/headphones/#protection_voltage) finds in a
sweep of e.m.f. and level.

Frequency responses (8.6) and crosstalk (8.12)
----------------------------------------------

The coupler or ear simulator frequency response (8.6.2) is the level against
frequency at the rated e.m.f., and its graph has "the same length
representing 50 dB as represents one decade of frequency"
([`coupler_frequency_response`](/phonometry/reference/api/electroacoustics/headphones/#coupler_frequency_response)). The crosstalk attenuation (8.12) is the
difference of two such curves ([`crosstalk_attenuation`](/phonometry/reference/api/electroacoustics/headphones/#crosstalk_attenuation)).

The two subjective responses (8.6.3, 8.6.4) are the quotient of the reference
field's sound pressure by the e.m.f. that makes the headphone equally loud,
"expressed in decibels referred to the value at the standard reference
frequency", averaged over at least eight test persons with the standard
deviation in each band ([`field_comparison_response`](/phonometry/reference/api/electroacoustics/headphones/#field_comparison_response)); a headphone
calibrated on at least 16 persons may then serve as the reference of the
substitution method. The ear-canal responses (8.6.5) read a probe microphone
in the ear canal instead of a loudness judgement, by Formula (1),

$$
L_\mathrm{f} = L_\mathrm{e} - L_\mathrm{s} - (L_\mathrm{e} - L_\mathrm{s})_{500},
$$

after averaging the two fittings of the headphone and the two readings of the
sound field, with the procedure repeated when the two fittings differ by more
than 2,5 dB in any band ([`ear_canal_frequency_response`](/phonometry/reference/api/electroacoustics/headphones/#ear_canal_frequency_response)). A headphone
measured that way on at least 16 persons may replace the sound field of the
indirect method (8.6.5.3, whose two references to 8.6.4.2 are read as 8.6.5.2,
see `docs/ERRATA.md`). The microphone in the ear canal is specified by
Annex B ([`verify_ear_canal_microphone`](/phonometry/reference/api/electroacoustics/headphones/#verify_ear_canal_microphone)).

The two reference frequencies are not the same. Formula (1) prints its
reference band, 500 Hz, the standard measuring frequency of 7.2 b). The
comparison responses are referred to "the standard reference frequency", a
term IEC 60268-7 uses without defining; IEC 60268-1:1985 Clause 3, which it
cites, sets it at 1 000 Hz "in the absence of a clear reason to the
contrary", and 8.6.3.2 c) and 8.6.4.2 c) begin and end the test sequence on
that band, so [`field_comparison_response`](/phonometry/reference/api/electroacoustics/headphones/#field_comparison_response) refers to 1 000 Hz by default.
The coupler response keeps 500 Hz, for the reason the NOTE of 8.3.3.1 gives:
the coupler's own resonances, leakage and standing waves at other frequencies.
The frequency response itself has no tolerance: "It is not at present
possible to set limits for the frequency range based on deviations from a
flat, or defined, frequency response" (8.6.6 NOTE 2), so the rated frequency
range is the manufacturer's statement and enters only as the range a
measurement has to cover.

Distortion (8.7)
----------------

The harmonic, modulation and difference-frequency distortions are those of
IEC 60268-2, read with [`harmonic_distortion`](/phonometry/reference/api/electroacoustics/distortion/#harmonic_distortion),
[`modulation_distortion`](/phonometry/reference/api/electroacoustics/intermodulation/#modulation_distortion) and
[`difference_frequency_distortion`](/phonometry/reference/api/electroacoustics/intermodulation/#difference_frequency_distortion), and
expressed in decibels as $20\lg$ of the ratio. What 60268-7 adds are the
test signals: 70 Hz and 600 Hz in the amplitude ratio 4:1 with the peak of the
rated input voltage, "−1,9 dB at 70 Hz and −14,0 dB at 600 Hz" (NOTE 1 of
8.7.3.3; [`headphone_modulation_signal`](/phonometry/reference/api/electroacoustics/headphones/#headphone_modulation_signal)), and two tones 80 Hz apart, each
at half the rated input voltage ([`headphone_difference_frequency_signal`](/phonometry/reference/api/electroacoustics/headphones/#headphone_difference_frequency_signal)).
The third-order modulation products are at 460 Hz and 740 Hz, as 8.7.3.3 b)
says; Formula (3) prints $U_{470}$ (see `docs/ERRATA.md`).

What is not here
----------------

The rated conditions (7.1, 8.6.6, 8.8, 8.13, 8.14) are stated, not computed.
The external field (8.9) and the unwanted radiation (8.10) are readings. The
sound attenuation of 8.11 is measured "as specified in ISO 4869-1", which
[`phonometry.hearing.real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/) computes from the open and
occluded thresholds of the subjects; for a headphone with active noise
compensation, which the NOTE of 8.11.2 says "may require a modified
procedure", [`phonometry.hearing.anr_total_attenuation`](/phonometry/reference/api/hearing/active-noise-reduction/#anr_total_attenuation) follows ISO
4869-6. Annex A is the geometry of a pinna simulator and Annexes C to E are
informative practical conditions.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ACOUSTIC_COUPLINGS

*Constant* (`mapping`).

```python
ACOUSTIC_COUPLINGS = {'L': 'acoustically open (controlled leakage)', 'S': 'acoustically closed (minimum leakage)'}
```

## BACK_RADIATIONS

*Constant* (`mapping`).

```python
BACK_RADIATIONS = {'C': 'closed-back', 'O': 'open-back'}
```

## characteristic_voltage

```python
characteristic_voltage(
    source_emf_v: float,
    sound_pressure_level_db: float,
) -> float
```

The source e.m.f. that produces 94 dB in the coupler (IEC 60268-7 8.3.3).

The characteristic voltage is "the sinusoidal source e.m.f. at 500 Hz
which, when applied to the headphone through the rated source impedance,
produces a sound pressure level in the coupler or ear simulator of 94 dB".
The headphone is linear at that level, so a reading of
`sound_pressure_level_db` at `source_emf_v` scales to it:
$E\,10^{(94 - L)/20}$. The same scaling serves the programme signal
of 8.3.4 with the level of the whole signal
([`programme_signal_level`](/phonometry/reference/api/electroacoustics/headphones/#programme_signal_level)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The source e.m.f. of the reading, in volts (RMS). |
| `sound_pressure_level_db` | The level it produced in the coupler or ear simulator, in dB re 20 µPa. |

**Returns:** The characteristic voltage, in volts (RMS).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the e.m.f. is not positive or the level not finite. |

## check_limiting_test_signal

```python
check_limiting_test_signal(
    signal: Signal | NDArray[np.float64] | list[float],
    fs: int | None = None,
) -> LimitingTestSignalCheck
```

Is this the clipped programme signal IEC 60268-7 8.3.2.2 b) asks for?

"The clipped noise signal at the output of the amplifier shall have a
frequency distribution as specified in IEC 60268-1, and a peak-to-r.m.s
ratio between 1,8 and 2,2." The record's one-third-octave bands from
20 Hz up to the highest whose upper edge lies below the Nyquist frequency
are judged against Table II of IEC 60268-1
([`check_programme_signal`](/phonometry/reference/api/electroacoustics/programme-signal/#check_programme_signal)), and its
peak over its RMS against the two limits.
[`simulated_programme_signal`](/phonometry/reference/api/electroacoustics/programme-signal/#simulated_programme_signal) with
`peak_to_rms` generates such a record.

**Parameters**

| Name | Description |
| :--- | :--- |
| `signal` | The record (1-D), or a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal). |
| `fs` | Sample rate, in Hz; required for a bare array. |

**Returns:** A [`LimitingTestSignalCheck`](/phonometry/reference/api/electroacoustics/headphones/#limitingtestsignalcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the record is not 1-D and finite, or too short. |

## coupler_frequency_response

```python
coupler_frequency_response(
    frequencies_hz: ArrayLike,
    sound_pressure_level_db: ArrayLike,
    *,
    rated_frequency_range_hz: tuple[float, float] | None = None,
) -> CouplerFrequencyResponse
```

The coupler or ear simulator frequency response of IEC 60268-7 8.6.2.

"The variation of the sound pressure (level) in the coupler or ear
simulator as a function of frequency", at the rated source e.m.f. through
the rated source impedance, over "at least the rated frequency range".

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in Hz, strictly ascending. |
| `sound_pressure_level_db` | The level at each, in dB re 20 µPa. |
| `rated_frequency_range_hz` | The rated frequency range (8.6.6), as (lower, upper), in Hz, to judge the coverage; `None` if not stated. |

**Returns:** A [`CouplerFrequencyResponse`](/phonometry/reference/api/electroacoustics/headphones/#couplerfrequencyresponse).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length or are not finite. |

## CouplerFrequencyResponse

```python
CouplerFrequencyResponse(
    frequencies_hz: NDArray[np.float64],
    sound_pressure_level_db: NDArray[np.float64],
    rated_frequency_range_hz: tuple[float, float] | None,
)
```

The coupler or ear simulator frequency response (IEC 60268-7 8.6.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, ascending. |
| `sound_pressure_level_db` | The level in the coupler or ear simulator at each frequency, in dB re 20 µPa. |
| `rated_frequency_range_hz` | The rated frequency range, (lower, upper), in Hz, or `None` when not stated. |

### CouplerFrequencyResponse.covers_rated_range

*property*

Whether the frequencies span the rated range (8.6.2.2 b), `None` if unstated.

### CouplerFrequencyResponse.plot()

```python
CouplerFrequencyResponse.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes
```

Draw the level against frequency, 50 dB to the length of a decade.

8.6.2.2 c): "the preferred scale has the same length representing
50 dB as represents one decade of frequency (see IEC 60268-1 and
IEC 60263)". Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `iec_scale` | Fix that aspect (default); `False` lets the axes fill their box. |
| `kwargs` | Forwarded to the response curve's `Axes.plot`. |

**Returns:** The axes.

### CouplerFrequencyResponse.relative_response_db()

```python
CouplerFrequencyResponse.relative_response_db(
    *,
    reference_frequency_hz: float = 500.0,
) -> NDArray[np.float64]
```

The level relative to its value at a reference frequency, in dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_frequency_hz` | The reference frequency, in Hz; one of the measured frequencies (500 Hz by default, the standard measuring frequency of 7.2 b), chosen in the coupler "to avoid the effects of diaphragm resonance, leakage and standing waves", 8.3.3.1 NOTE). |

**Returns:** The relative response at each frequency, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the reference frequency was not measured. |

## crosstalk_attenuation

```python
crosstalk_attenuation(
    frequencies_hz: ArrayLike,
    driven_level_db: ArrayLike,
    other_level_db: ArrayLike,
) -> CrosstalkAttenuation
```

The crosstalk attenuation of IEC 60268-7 8.12.

"The ratio of the sound pressure produced in the coupler or ear simulator
due to rated source e.m.f. applied to the channel under test to the sound
pressure produced by rated source e.m.f. applied to another, stated
channel", expressed as the difference of the two levels against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in Hz, strictly ascending. |
| `driven_level_db` | The level with the channel under test driven, in dB re 20 µPa. |
| `other_level_db` | The level with the other channel driven, in dB re 20 µPa. |

**Returns:** A [`CrosstalkAttenuation`](/phonometry/reference/api/electroacoustics/headphones/#crosstalkattenuation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length or are not finite. |

## CrosstalkAttenuation

```python
CrosstalkAttenuation(
    frequencies_hz: NDArray[np.float64],
    driven_level_db: NDArray[np.float64],
    other_level_db: NDArray[np.float64],
)
```

The crosstalk attenuation of a multi-channel headphone (IEC 60268-7 8.12).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, ascending. |
| `driven_level_db` | The level in the coupler of the channel under test with the rated e.m.f. on that channel, in dB re 20 µPa. |
| `other_level_db` | The level in the same coupler with the rated e.m.f. on the other, stated channel, in dB re 20 µPa. |

### CrosstalkAttenuation.attenuation_db

*property*

The difference of the two levels at each frequency, in dB.

### CrosstalkAttenuation.minimum_db

*property*

The smallest attenuation over the frequencies, in dB.

### CrosstalkAttenuation.plot()

```python
CrosstalkAttenuation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the attenuation against frequency.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the attenuation curve's `Axes.plot`. |

**Returns:** The axes.

## ear_canal_frequency_response

```python
ear_canal_frequency_response(
    frequencies_hz: ArrayLike,
    earphone_levels_db: ArrayLike,
    sound_field_levels_db: ArrayLike,
    *,
    reference_frequency_hz: float = 500.0,
) -> EarCanalFrequencyResponse
```

The ear canal sound pressure level frequency response of IEC 60268-7 8.6.5.

For each test person a probe microphone in the ear canal reads each
one-third-octave band of pink noise twice in the sound field (items b and
e) and twice with the headphone, refitted between the two (c and d). The
two pairs are averaged and the response is Formula (1),
$L_\mathrm{f} = L_\mathrm{e} - L_\mathrm{s} - (L_\mathrm{e} - L_\mathrm{s})_{500}$, averaged over at least eight persons (h). The
result also carries the two checks of the procedure: the fittings within
2,5 dB in every band (f), and the 500 Hz band of the first fitting within
3 dB of the sound field's (c).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres, in Hz, ascending, including the reference band. |
| `earphone_levels_db` | The levels with the headphone, in dB, shape (persons, 2, bands), or (2, bands) for one person. |
| `sound_field_levels_db` | The levels in the sound field, in dB, the same shape. |
| `reference_frequency_hz` | The reference band of Formula (1), in Hz (500 Hz, as the formula prints it). |

**Returns:** An [`EarCanalFrequencyResponse`](/phonometry/reference/api/electroacoustics/headphones/#earcanalfrequencyresponse).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a level is not finite or the reference band is missing. |

## EarCanalFrequencyResponse

```python
EarCanalFrequencyResponse(
    frequencies_hz: NDArray[np.float64],
    earphone_levels_db: NDArray[np.float64],
    sound_field_levels_db: NDArray[np.float64],
    reference_frequency_hz: float,
)
```

The ear canal sound pressure level frequency response (IEC 60268-7 8.6.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third-octave band centres, in Hz. |
| `earphone_levels_db` | The probe microphone's band levels with the headphone, items c) and d), shape (persons, 2, bands), in dB. |
| `sound_field_levels_db` | The probe microphone's band levels in the sound field, items b) and e), shape (persons, 2, bands), in dB. |
| `reference_frequency_hz` | The band of Formula (1), in Hz. |

### EarCanalFrequencyResponse.fitting_difference_db

*property*

The largest difference between the two fittings of each person, in dB.

### EarCanalFrequencyResponse.fittings_consistent

*property*

For each person, whether the fittings agree within 2,5 dB in every band.

8.6.5.2 f): "if there is a difference exceeding 2,5 dB [...] in any 1/3
octave band, the whole procedure is repeated."

### EarCanalFrequencyResponse.level_match_db

*property*

The first fitting's level in the reference band minus the sound field's, in dB.

8.6.5.2 c): the level is adjusted "using the 1/3 octave band of noise
centred on 500 Hz, so that the filtered microphone output signal level
is within 3 dB of that due to the sound field in the same frequency
band".

### EarCanalFrequencyResponse.levels_matched

*property*

For each person, whether `level_match_db` is within 3 dB.

### EarCanalFrequencyResponse.mean_db

*property*

Formula (1) averaged arithmetically over the persons, in dB (8.6.5.2 h).

### EarCanalFrequencyResponse.meets_panel_size

*property*

Whether at least eight persons were measured (8.6.5.2 h).

### EarCanalFrequencyResponse.persons

*property*

The number of test persons.

### EarCanalFrequencyResponse.plot()

```python
EarCanalFrequencyResponse.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes
```

Draw the persons' responses, their mean and its standard deviation.

8.6.5.2 h): the results "may be tabulated or presented graphically,
the scales being preferably chosen so that 50 dB and one decade of
frequency are represented by the same length". Requires matplotlib
(`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `iec_scale` | Draw 50 dB the length of a decade (default); `False` lets the axes fill their box. |
| `kwargs` | Forwarded to the mean response's `Axes.plot`. |

**Returns:** The axes.

### EarCanalFrequencyResponse.qualifies_as_reference

*property*

Whether the panel is large enough to calibrate a reference (16 persons).

8.6.5.3: the indirect method replaces the sound field by "a
headphone, previously calibrated by the method of 8.6.4.2, using at
least 16 test persons"; the method meant is the direct ear-canal
measurement of 8.6.5.2 (see `docs/ERRATA.md`).

### EarCanalFrequencyResponse.response_db

*property*

Formula (1) for each person, one row per person, in dB.

### EarCanalFrequencyResponse.standard_deviation_db

*property*

The standard deviation of the persons' responses, in dB (NOTE 5).

## EarCanalMicrophoneVerification

```python
EarCanalMicrophoneVerification(
    entrance_area_mm2: float,
    canal_section_area_mm2: float,
    ear_canal_area_mm2: float,
    volume_mm3: float,
    neighbour_difference_db: float,
    sealed_attenuation_db: float,
)
```

A probe microphone judged by IEC 60268-7:2010 Annex B a) to e).

**Attributes**

| Name | Description |
| :--- | :--- |
| `entrance_area_mm2` | The microphone's cross-sectional area within the concha and the first 4 mm of the ear canal, in mm² (a). |
| `canal_section_area_mm2` | Its cross-sectional area in the rest of the ear canal, in mm² (b). |
| `ear_canal_area_mm2` | The cross-sectional area of the ear canal, in mm² (b; 45 mm² for an average adult). |
| `volume_mm3` | The microphone's volume with its mounting parts, in mm³ (c). |
| `neighbour_difference_db` | The largest difference between the responses to neighbouring one-third-octave bands of pink noise, in dB (d). |
| `sealed_attenuation_db` | The smallest drop of the output level when the sound entrance is sealed, over the measuring frequencies, in dB (e). |

### EarCanalMicrophoneVerification.area_ratio

*property*

The microphone's area over the ear canal's, in the rest of the canal.

### EarCanalMicrophoneVerification.passes

*property*

Whether all five requirements hold.

### EarCanalMicrophoneVerification.plot()

```python
EarCanalMicrophoneVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each requirement's value as a share of its limit.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars' `Axes.bar`. |

**Returns:** The axes.

### EarCanalMicrophoneVerification.requirements

*property*

Each of a) to e), keyed by its item letter, and whether it holds.

## EARPHONE_TYPES

*Constant* (`mapping`).

```python
EARPHONE_TYPES = {'C': 'circumaural', 'E': 'intra-concha', 'H': 'earshell', 'I': 'insert', 'M': 'supra-concha', 'S': 'supra-aural', 'T': 'stethoscopic'}
```

## field_comparison_response

```python
field_comparison_response(
    frequencies_hz: ArrayLike,
    field_level_db: ArrayLike,
    source_emf_v: ArrayLike,
    *,
    field: Literal['free', 'diffuse'],
    reference_frequency_hz: float = 1000.0,
) -> FieldComparisonResponse
```

The free-field or diffuse-field comparison response of IEC 60268-7.

"The quotient, as a function of frequency, of the sound pressure of the
reference [free or diffuse] sound field by the source e.m.f. to the
headphone which is required to produce a sound subjectively equal in
loudness to the [...] sound field. It is normally expressed in decibels
referred to the value at the standard reference frequency" (8.6.3.1,
8.6.4.1). In each band $k$ and for each person,

$$
R_k = L_{\mathrm{field},k} - 20\lg E_k - (L_{\mathrm{field},\mathrm{ref}} - 20\lg E_\mathrm{ref}),
$$

and the persons' responses are averaged in each band, with their standard
deviation (8.6.3.2 e). At least eight persons are heard (d); a headphone
calibrated on at least 16 may serve as the reference of the substitution
method (8.6.3.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third-octave band centres, in Hz, ascending, including the reference band. |
| `field_level_db` | The level of the reference field at the reference point, without the person, in dB re 20 µPa: one value per band, or one row per person. |
| `source_emf_v` | The e.m.f. that made the headphone equally loud, in volts (RMS), one row per person, one value per band. |
| `field` | `"free"` (8.6.3) or `"diffuse"` (8.6.4). |
| `reference_frequency_hz` | The band the response is referred to, in Hz: by default 1 000 Hz, the standard reference frequency of IEC 60268-1:1985 Clause 3, which IEC 60268-7 names without defining and on whose band 8.6.3.2 c) and 8.6.4.2 c) begin and end the test sequence. Pass 500 Hz to refer the response to the band of the ear-canal response of Formula (1). |

**Returns:** A [`FieldComparisonResponse`](/phonometry/reference/api/electroacoustics/headphones/#fieldcomparisonresponse).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a value is out of range or the reference band is missing. |

## FieldComparisonResponse

```python
FieldComparisonResponse(
    field: Literal['free', 'diffuse'],
    frequencies_hz: NDArray[np.float64],
    response_db: NDArray[np.float64],
    reference_frequency_hz: float,
)
```

A free-field or diffuse-field comparison frequency response (IEC 60268-7 8.6.3, 8.6.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `field` | `"free"` (8.6.3) or `"diffuse"` (8.6.4). |
| `frequencies_hz` | The one-third-octave band centres, in Hz. |
| `response_db` | Each test person's response, one row per person, in dB relative to the reference band. |
| `reference_frequency_hz` | The band the response is referred to, in Hz. |

### FieldComparisonResponse.mean_db

*property*

The response averaged over the persons in each band, in dB.

### FieldComparisonResponse.meets_panel_size

*property*

Whether at least eight persons were heard (8.6.3.2 d, 8.6.4.2 d).

### FieldComparisonResponse.persons

*property*

The number of test persons.

### FieldComparisonResponse.plot()

```python
FieldComparisonResponse.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes
```

Draw the mean response as bars with the standard deviation of each band.

8.6.3.2 e): "the resulting bar graph is presented as the free-field
comparison frequency response of the headphone. The standard
deviation of the results in each band should be indicated on the
graph. The scales for the graph preferably shall be such that 50 dB
is represented by the same length as one decade of frequency."
Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `iec_scale` | Draw 50 dB the length of a decade of the bands (default); `False` lets the axes fill their box. |
| `kwargs` | Forwarded to the bars' `Axes.bar`. |

**Returns:** The axes.

### FieldComparisonResponse.qualifies_as_reference

*property*

Whether the panel is large enough for a substitution reference (16 persons).

8.6.3.3 and 8.6.4.3: a headphone measured "using a panel of at least
16 persons, may be used as a loudness comparison reference".

### FieldComparisonResponse.standard_deviation_db

*property*

The standard deviation of the persons' responses in each band, in dB.

The sample standard deviation; zero with a single person.

## headphone_difference_frequency_signal

```python
headphone_difference_frequency_signal(
    fs: int,
    seconds: float,
    *,
    upper_frequency_hz: float,
    rated_source_emf_v: float,
) -> NDArray[np.float64]
```

The difference-frequency distortion test signal of IEC 60268-7 8.7.4.

"Two sinusoidal signals, separated in frequency by 80 Hz, each giving half
the rated input voltage": tones at $f_2 - 80$ Hz and $f_2$,
each of RMS value $U/2$, in cosine phase so that the peak is that of
the rated voltage. Read the products with
[`difference_frequency_distortion`](/phonometry/reference/api/electroacoustics/intermodulation/#difference_frequency_distortion).

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `seconds` | Duration, in seconds. |
| `upper_frequency_hz` | The upper tone $f_2$, in Hz, above 80 Hz and below the Nyquist frequency. |
| `rated_source_emf_v` | The rated input voltage, in volts (RMS). |

**Returns:** The signal, in volts.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is out of range. |

## headphone_input_power

```python
headphone_input_power(
    source_emf_v: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
) -> float
```

The power corresponding to a source e.m.f. (IEC 60268-7 8.4).

"Specifications in terms of power can be derived from the corresponding
voltages (8.3) and the rated impedance": the power the e.m.f.
$E$ dissipates, through the rated source impedance
$R_\mathrm{s}$, in a pure resistance equal to the rated impedance
$R$ connected in place of the headphone, the arrangement 8.5.2 b)
describes for 1 mW,

$$
P = \frac{E^2 R}{(R + R_\mathrm{s})^2}.
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The source e.m.f., in volts (RMS). |
| `rated_impedance_ohm` | The rated impedance, in ohms. |
| `rated_source_impedance_ohm` | The rated source impedance, in ohms (IEC 61938 specifies 120 ohm for a headphone output, 7.1 NOTE). |

**Returns:** The input power, in watts.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is out of range. |

## headphone_modulation_signal

```python
headphone_modulation_signal(
    fs: int,
    seconds: float,
    *,
    rated_source_emf_v: float,
) -> NDArray[np.float64]
```

The modulation distortion test signal of IEC 60268-7 8.7.3.

"The sum of two sinusoidal signals, at 70 Hz and 600 Hz, with amplitude
ratio 4:1. The peak voltage of the signal shall be equal to that of the
rated input voltage": amplitudes $0{,}8\sqrt{2}U$ and
$0{,}2\sqrt{2}U$ for a rated voltage $U$, which NOTE 1 states
as "−1,9 dB at 70 Hz and −14,0 dB at 600 Hz". Both start at their crest
(cosine phase), so the record reaches that peak at its first sample.
Read the products with
[`modulation_distortion`](/phonometry/reference/api/electroacoustics/intermodulation/#modulation_distortion) at
`f_low=70`, `f_high=600`: the second order at 530 Hz and 670 Hz, the
third at 460 Hz and 740 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `seconds` | Duration, in seconds. |
| `rated_source_emf_v` | The rated input voltage, the rated source e.m.f. of 8.3.1, in volts (RMS). |

**Returns:** The signal, in volts.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is out of range. |

## headphone_source_emf

```python
headphone_source_emf(
    input_power_w: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
) -> float
```

The source e.m.f. that corresponds to a power (IEC 60268-7 8.4, 8.5.2).

The inverse of [`headphone_input_power`](/phonometry/reference/api/electroacoustics/headphones/#headphone_input_power),
$E = \sqrt{P R}\,(R + R_\mathrm{s})/R$. With 1 mW it is the e.m.f.
of the working sound pressure level of 8.5.2 b) to d).

**Parameters**

| Name | Description |
| :--- | :--- |
| `input_power_w` | The power, in watts. |
| `rated_impedance_ohm` | The rated impedance, in ohms. |
| `rated_source_impedance_ohm` | The rated source impedance, in ohms. |

**Returns:** The source e.m.f., in volts (RMS).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is out of range. |

## HeadphoneClassification

```python
HeadphoneClassification(
    principle: str,
    earphone_type: str,
    coupling: str,
    radiation: str,
    impedance_ohm: float,
    channels: int,
)
```

The classification of a headphone by IEC 60268-7:2010 Clause 4.

**Attributes**

| Name | Description |
| :--- | :--- |
| `principle` | The principle of the transducer, a key of [`TRANSDUCER_PRINCIPLES`](/phonometry/reference/api/electroacoustics/headphones/#transducer_principles). |
| `earphone_type` | The type of earphone, a key of [`EARPHONE_TYPES`](/phonometry/reference/api/electroacoustics/headphones/#earphone_types). |
| `coupling` | The acoustic coupling to the ear canal, a key of [`ACOUSTIC_COUPLINGS`](/phonometry/reference/api/electroacoustics/headphones/#acoustic_couplings). |
| `radiation` | The radiation to the external environment, a key of [`BACK_RADIATIONS`](/phonometry/reference/api/electroacoustics/headphones/#back_radiations). |
| `impedance_ohm` | The impedance, in ohms, as coded by [`impedance_code`](/phonometry/reference/api/electroacoustics/headphones/#impedance_code). |
| `channels` | The number of channels, 1 to 9. |

### HeadphoneClassification.code

*property*

The code, for instance `"60268-7-IEC-DCSC-32R0-2"`.

### HeadphoneClassification.description

*property*

The four letters in words, in the clause's terms.

## impedance_code

```python
impedance_code(impedance_ohm: float) -> str
```

The NNRN form of an impedance in the code of IEC 60268-7 Clause 4.

A two-digit mantissa, `R`, and a one-digit exponent of ten: "8 Ω as
"08R0", 32 Ω as "32R0" and 600 Ω as "06R2"". The exponent takes every
trailing zero of the whole number of ohms, which is the reading the 600 ohm
example fixes (`06R2`, not `60R1`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `impedance_ohm` | The impedance, in ohms: a whole number whose digits before the trailing zeros number at most two. |

**Returns:** The four characters, for instance `"32R0"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the impedance is not a positive whole number of ohms or does not fit the form: `4.7` ohm is not whole, and `123` ohm needs a mantissa of three digits. |

## LimitingTestSignalCheck

```python
LimitingTestSignalCheck(peak_to_rms: float, spectrum: ProgrammeSignalCheck)
```

The test signal of the limiting voltages judged by IEC 60268-7 8.3.2.2 b).

**Attributes**

| Name | Description |
| :--- | :--- |
| `peak_to_rms` | The ratio of the record's peak value to its RMS value. |
| `spectrum` | Its one-third-octave spectrum judged against IEC 60268-1 Table II. |

### LimitingTestSignalCheck.passes

*property*

Whether both the ratio and the spectrum conform.

### LimitingTestSignalCheck.peak_to_rms_passes

*property*

Whether the peak-to-RMS ratio is between 1,8 and 2,2.

### LimitingTestSignalCheck.plot()

```python
LimitingTestSignalCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the spectrum against Table II, with the ratio in the title.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band levels' `Axes.plot`. |

**Returns:** The axes.

## parse_classification_code

```python
parse_classification_code(code: str) -> HeadphoneClassification
```

Read a classification code of IEC 60268-7:2010 Clause 4.

Spaces around the hyphens are ignored, so the clause's own layout,
`60268-7 - IEC - XXXX - NNRN - N`, reads as well as the compact one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `code` | The code, for instance `"60268-7-IEC-DCSC-32R0-2"`. |

**Returns:** A [`HeadphoneClassification`](/phonometry/reference/api/electroacoustics/headphones/#headphoneclassification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the code does not have the form of the clause or a letter or number is not one it defines. |

## programme_characteristic_voltage

```python
programme_characteristic_voltage(
    source_emf_v: ArrayLike,
    frequencies_hz: ArrayLike,
    band_levels_db: ArrayLike,
    *,
    a_weighted: bool = False,
    free_field_response_db: ArrayLike | None = None,
) -> ProgrammeCharacteristicVoltage
```

The simulated programme signal characteristic voltage of IEC 60268-7.

The source e.m.f. of the simulated programme signal of IEC 60268-1 that
produces 94 dB in the coupler or ear simulator (8.3.4), or 94 dB after the
A-weighting and the free-field compensation of 8.3.5. Each fitting's
one-third-octave band levels, read at a known e.m.f., are power-summed as
the NOTE under Figure 3 describes ([`programme_signal_level`](/phonometry/reference/api/electroacoustics/headphones/#programme_signal_level)) and
scaled to 94 dB; 8.3.5 g) removes and refits the headphone between
readings and states "the average value of source e.m.f. of 3 to 5
measurements".

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The source e.m.f. of each fitting's reading, in volts (RMS): one value for all, or one per fitting. |
| `frequencies_hz` | The band centre frequencies, in Hz, ascending. |
| `band_levels_db` | The band levels, in dB re 20 µPa, shape `(bands,)` for one fitting or `(fittings, bands)`. |
| `a_weighted` | Apply the A-weighting (8.3.5). |
| `free_field_response_db` | The free-field response of the head and torso simulator in each band, in dB, compensated by its inverse (8.3.5); `None` for none. |

**Returns:** A [`ProgrammeCharacteristicVoltage`](/phonometry/reference/api/electroacoustics/headphones/#programmecharacteristicvoltage).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree or a value is out of range. |

## programme_signal_level

```python
programme_signal_level(
    frequencies_hz: ArrayLike,
    band_levels_db: ArrayLike,
    *,
    a_weighted: bool = False,
    free_field_response_db: ArrayLike | None = None,
) -> float
```

The level of the simulated programme signal from its one-third-octave bands.

IEC 60268-7:2010 Figure 3, NOTE: "The output signal correction can be
done numerically without use of any filtering devices. Power summation of
the 1/3-octave-analized data multiplied by filtering coefficients given by
IEC 61672-1 and/or IEC 60969 gives the corrected voltage." The
coefficients are the A-weighting of IEC 61672-1, taken at the exact
base-ten centre of each band (where its Table 3 is computed), and the
inverse of the free-field response of the head and torso simulator of IEC
60959 (printed "IEC 60969", see `docs/ERRATA.md`):

$$
L = 10\lg \sum_k 10^{(L_k + A_k - F_k)/10}.
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centre frequencies, in Hz, ascending. |
| `band_levels_db` | The band levels read in the coupler or ear simulator, in dB re 20 µPa. |
| `a_weighted` | Apply the A-weighting (8.3.5, 8.5.2 d). |
| `free_field_response_db` | The free-field response of the head and torso simulator at 0° azimuth in each band, in dB, whose inverse compensates the output; `None` for no compensation. |

**Returns:** The level of the whole signal, in dB re 20 µPa.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length or are not finite. |

## ProgrammeCharacteristicVoltage

```python
ProgrammeCharacteristicVoltage(
    frequencies_hz: NDArray[np.float64],
    band_levels_db: NDArray[np.float64],
    source_emf_v: NDArray[np.float64],
    corrections_db: NDArray[np.float64],
    a_weighted: bool,
    free_field_compensated: bool,
)
```

The simulated programme signal characteristic voltage (IEC 60268-7 8.3.4, 8.3.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centre frequencies, in Hz. |
| `band_levels_db` | The band levels read in the coupler or ear simulator, one row per fitting, in dB re 20 µPa. |
| `source_emf_v` | The source e.m.f. of each fitting's reading, in volts (RMS). |
| `corrections_db` | The correction added to each band, in dB: the A-weighting minus the free-field response, zero when neither applies. |
| `a_weighted` | Whether the A-weighting was applied. |
| `free_field_compensated` | Whether the free-field response was compensated. |

### ProgrammeCharacteristicVoltage.band_levels_at_characteristic_db

*property*

The corrected band levels at the characteristic voltage, in dB re 20 µPa.

The mean of the fittings' corrected bands, each scaled to the
characteristic voltage; their power sum is 94 dB when the fittings
agree.

### ProgrammeCharacteristicVoltage.characteristic_voltage_v

*property*

The arithmetic mean of `voltages_v`, in volts: 8.3.5 g).

### ProgrammeCharacteristicVoltage.fittings_conform

*property*

Whether 3 to 5 fittings were averaged, as 8.3.5 g) asks.

### ProgrammeCharacteristicVoltage.levels_db

*property*

The corrected level of the whole signal in each fitting, in dB re 20 µPa.

### ProgrammeCharacteristicVoltage.plot()

```python
ProgrammeCharacteristicVoltage.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the band levels at the characteristic voltage and their 94 dB sum.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars' `Axes.bar`. |

**Returns:** The axes.

### ProgrammeCharacteristicVoltage.voltages_v

*property*

The e.m.f. that gives 94 dB in each fitting, in volts (RMS).

## protection_voltage

```python
protection_voltage(
    source_emf_v: ArrayLike,
    sound_pressure_level_db: ArrayLike,
) -> ProtectionVoltage
```

The protection voltage of a headphone's protective device (IEC 60268-7 8.3.6).

8.3.6.2 b): "The source e.m.f., at the standard reference frequency, is
increased until operation of the protective device causes a change of at
least 1 dB in the sensitivity of the headphone." The sensitivity at each
step is $L - 20\lg E$; the first step, the lowest e.m.f., is taken
as the linear one, and the protection voltage is where the change from it
first reaches 1 dB either way, interpolated linearly in $20\lg E$
between the two steps that straddle it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The source e.m.f. of each step, in volts (RMS), strictly ascending. |
| `sound_pressure_level_db` | The level at each step, in dB re 20 µPa. |

**Returns:** A [`ProtectionVoltage`](/phonometry/reference/api/electroacoustics/headphones/#protectionvoltage).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length, are not finite, the e.m.f.s are not positive and ascending, or there are fewer than two. |

## ProtectionVoltage

```python
ProtectionVoltage(
    source_emf_v: NDArray[np.float64],
    sound_pressure_level_db: NDArray[np.float64],
    protection_voltage_v: float | None,
)
```

A protective device's operating point from a level sweep (IEC 60268-7 8.3.6).

**Attributes**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The source e.m.f. of each step, in volts (RMS), ascending. |
| `sound_pressure_level_db` | The level at each step, in dB re 20 µPa. |
| `protection_voltage_v` | The e.m.f. at which the sensitivity has changed by 1 dB from the first step, interpolated, in volts; `None` when the sweep never reaches that change. |

### ProtectionVoltage.measurement_voltages_v

*property*

The e.m.f.s 1 dB below and 1 dB above the protection voltage, in volts.

8.3.6.2 b): "measurements are then made of the impedance and sound
pressure level at voltages 1 dB lower and 1 dB higher than the noted
voltage".

### ProtectionVoltage.plot()

```python
ProtectionVoltage.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the sensitivity change against the e.m.f., with the 1 dB line.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the sensitivity curve's `Axes.plot`. |

**Returns:** The axes.

### ProtectionVoltage.sensitivity_change_db

*property*

The sensitivity at each step relative to the first, in dB.

## RatedImpedanceVerification

```python
RatedImpedanceVerification(
    frequencies_hz: NDArray[np.float64],
    impedance_ohm: NDArray[np.float64],
    rated_impedance_ohm: float,
    rated_frequency_range_hz: tuple[float, float],
)
```

A rated impedance judged against the measured modulus (IEC 60268-7 8.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in Hz, ascending. |
| `impedance_ohm` | The modulus of the impedance at each frequency, in ohms. |
| `rated_impedance_ohm` | The rated impedance, in ohms. |
| `rated_frequency_range_hz` | The rated frequency range, (lower, upper), in Hz. |

### RatedImpedanceVerification.covers_measurement_range

*property*

Whether the modulus was measured at least from 20 Hz to 20 kHz (8.2.2.2 c).

### RatedImpedanceVerification.frequencies_to_state_hz

*property*

The frequencies from 0 kHz to 20 kHz where the modulus is below 80 %.

8.2.1 b): "If the impedance at any frequency between 0 kHz and 20 kHz
is less than this value, this should be stated in the specification."

### RatedImpedanceVerification.limit_ohm

*property*

80 % of the rated impedance, in ohms (8.2.1 b).

### RatedImpedanceVerification.minimum_frequency_hz

*property*

The frequency of `minimum_ohm`, in Hz.

### RatedImpedanceVerification.minimum_ohm

*property*

The lowest modulus within the rated frequency range, in ohms.

### RatedImpedanceVerification.minimum_ratio

*property*

`minimum_ohm` over the rated impedance.

### RatedImpedanceVerification.passes

*property*

Whether the rated impedance is at most 1,25 times the lowest modulus in range.

### RatedImpedanceVerification.plot()

```python
RatedImpedanceVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the modulus against frequency with the rated value and its 80 %.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the impedance curve's `Axes.plot`. |

**Returns:** The axes.

## TRANSDUCER_PRINCIPLES

*Constant* (`mapping`).

```python
TRANSDUCER_PRINCIPLES = {'D': 'electrodynamic (moving coil)', 'E': 'electret (self-polarizing)', 'F': 'piezo-electric (polymer)', 'M': 'electromagnetic (moving armature or diaphragm)', 'P': 'piezo-electric (ceramic)', 'S': 'electrostatic (externally polarized)'}
```

## verify_ear_canal_microphone

```python
verify_ear_canal_microphone(
    *,
    entrance_area_mm2: float,
    canal_section_area_mm2: float,
    volume_mm3: float,
    pink_noise_band_levels_db: ArrayLike,
    open_levels_db: ArrayLike,
    sealed_levels_db: ArrayLike,
    ear_canal_area_mm2: float = 45.0,
) -> EarCanalMicrophoneVerification
```

May this microphone measure inside the ear canal by IEC 60268-7 Annex B?

The five measurable conditions of the normative Annex B: a) a
cross-sectional area of 5 mm² or less within the concha and the first
4 mm of the canal; b) in the rest of the canal, an area less than 0,6 of
the canal's ("The average ear canal area of an adult is 45 mm²"); c) a
volume, mounting parts included, less than 130 mm³; d) responses to
neighbouring one-third-octave bands of pink noise that "do not differ by
more than 3 dB"; e) an output level with the sound entrance sealed "at
least 15 dB below that with the entrance open, at all measuring
frequencies". Items f) and g), the suspension and the physician's
certificate, are not numbers.

**Parameters**

| Name | Description |
| :--- | :--- |
| `entrance_area_mm2` | Cross-sectional area in the concha and the first 4 mm of the canal, in mm². |
| `canal_section_area_mm2` | Cross-sectional area in the rest of the canal, in mm². |
| `volume_mm3` | Volume with the mounting parts, in mm³. |
| `pink_noise_band_levels_db` | The microphone's output levels for consecutive one-third-octave bands of pink noise of equal level, in dB, ascending in frequency. |
| `open_levels_db` | The output level with the entrance open at each measuring frequency, in dB. |
| `sealed_levels_db` | The output level with the entrance sealed at the same frequencies, in dB. |
| `ear_canal_area_mm2` | The canal's cross-sectional area, in mm²; the adult average of item b) by default. |

**Returns:** An [`EarCanalMicrophoneVerification`](/phonometry/reference/api/electroacoustics/headphones/#earcanalmicrophoneverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a value is out of range or the level arrays disagree in length. |

## verify_rated_impedance

```python
verify_rated_impedance(
    frequencies_hz: ArrayLike,
    impedance_ohm: ArrayLike,
    *,
    rated_impedance_ohm: float,
    rated_frequency_range_hz: tuple[float, float],
) -> RatedImpedanceVerification
```

Is the rated impedance of a headphone chosen as IEC 60268-7 8.2.1 asks?

The rated impedance passes when the lowest modulus of the measured
impedance within the rated frequency range is at least 80 % of it. The
result also lists the frequencies up to 20 kHz where the modulus falls
below that value, which the specification should state, and whether the
measurement covered 20 Hz to 20 kHz as 8.2.2.2 c) requires.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Measurement frequencies, in Hz, strictly ascending. |
| `impedance_ohm` | The impedance at each frequency, in ohms: the modulus, or the complex impedance whose modulus is taken. |
| `rated_impedance_ohm` | The rated impedance, in ohms. |
| `rated_frequency_range_hz` | The rated frequency range (8.6.6), as (lower, upper), in Hz. |

**Returns:** A [`RatedImpedanceVerification`](/phonometry/reference/api/electroacoustics/headphones/#ratedimpedanceverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length, are not positive and finite, or no measurement frequency falls in the rated range. |

## working_sound_pressure_level

```python
working_sound_pressure_level(
    sound_pressure_level_db: float,
    source_emf_v: float,
    *,
    rated_impedance_ohm: float,
    rated_source_impedance_ohm: float,
    headphone_impedance_ohm: complex | None = None,
) -> float
```

The working sound pressure level of IEC 60268-7 8.5.2 b) to d).

The level produced by the e.m.f. "of such value that 1 mW would be
dissipated in a pure resistance equal to the rated impedance of the
headphone, connected in place of it", scaled from a reading at another
e.m.f. With a 500 Hz sine it is 8.5.2 b); with the level of the
simulated programme signal ([`programme_signal_level`](/phonometry/reference/api/electroacoustics/headphones/#programme_signal_level)) it is c), and
d) when that level is A-weighted and free-field compensated.

The method of 8.5.3 c) sets that e.m.f. another way: "so that the
voltage across the input connector of the headphone is such that it
would cause 1 mW to be dissipated in a pure resistance equal to the rated
impedance", $\sqrt{P R}$ across the headphone itself, whose
impedance $Z$ at 500 Hz takes its share of the e.m.f.,
$E = \sqrt{P R}\,|Z + R_\mathrm{s}|/|Z|$. The two readings agree
when $Z$ is the rated impedance and part when it is not: a 32 ohm
headphone of 40 ohm at 500 Hz on a 120 ohm source reads 1,49 dB lower by
8.5.3 c). Pass `headphone_impedance_ohm` for the reading of 8.5.3 c)
(see `docs/ERRATA.md`); it applies to the 500 Hz sine of 8.5.2 b),
since a noise signal has no single impedance to divide by.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_pressure_level_db` | The level read in the coupler or ear simulator, in dB re 20 µPa. |
| `source_emf_v` | The source e.m.f. of the reading, in volts (RMS). |
| `rated_impedance_ohm` | The rated impedance, in ohms. |
| `rated_source_impedance_ohm` | The rated source impedance, in ohms. |
| `headphone_impedance_ohm` | The headphone's measured impedance at 500 Hz, in ohms, complex or its modulus for a resistive one, to set the e.m.f. by 8.5.3 c); `None` (default) for the definition of 8.5.2 b) to d). |

**Returns:** The working sound pressure level, in dB re 20 µPa.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is out of range. |
