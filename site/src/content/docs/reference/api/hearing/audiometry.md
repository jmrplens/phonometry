---
title: "hearing.audiometry"
description: "Pure-tone audiometry: the test room, the threshold rules and their uncertainty (ISO 8253-1:2010)."
sidebar:
  label: "audiometry"
---

Pure-tone audiometry: the test room, the threshold rules and their uncertainty (ISO 8253-1:2010).

ISO 8253-1 sets out how a hearing threshold level is measured with earphones
or a bone vibrator. Three parts of it are arithmetic, and this module carries
them; the rest (preparing and instructing the subject, placing the
transducers, masking, calibrating the audiometer) is procedure a tester
follows.

**The test room (Clause 11).** The ambient noise must not mask the lowest
test tone. Tables 2 and 4 give the maximum permissible ambient sound pressure
levels $L_{S,\mathrm{max}}$ in one-third-octave bands from 31,5 Hz to
8 kHz, for air conduction with typical supra-aural earphones and for bone
conduction, each for the lowest test frequency of the audiometry: 125 Hz,
250 Hz or, for air conduction, 500 Hz. They hold for hearing threshold levels
down to 0 dB with at most +2 dB of threshold shift from the noise; the NOTEs
allow 8 dB more for +5 dB, and 11.1 adds the lowest hearing threshold level
to be measured when it is not 0 dB. An earphone that excludes more noise than
the supra-aural one allows a louder room: 11.1 adds the difference between
its attenuation and the supra-aural one of Table 3,

$$
L_{S,\mathrm{max}}' = L_{S,\mathrm{max}} + \left(A_\mathrm{earphone} - A_\mathrm{supra\text{-}aural}\right) + L_\mathrm{HT,min}
$$

and Table 3 prints it for an insert (Etymotic ER-3A) and a circumaural
(Sennheiser HDA 200) earphone. [`ambient_noise_limits`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_limits) returns the
limits and [`check_audiometric_ambient_noise`](/phonometry/reference/api/hearing/audiometry/#check_audiometric_ambient_noise) judges a measured
spectrum against them, including the sound-field limits of ISO 8253-2:2009
Table 2 ([`phonometry.hearing.SOUND_FIELD_AMBIENT_LIMITS_DB`](/phonometry/reference/api/hearing/sound-field-audiometry/#sound_field_ambient_limits_db)).

**The threshold (6.2.4, 6.3.5, 7.5).** Each audiometric method ends in a rule
that turns the subject's responses into a hearing threshold level:

- the **ascending method** (6.2.3.2, 6.2.4.2) presents tones in 5 dB steps
  upwards until a response, drops 10 dB after each response, and stops when
  three responses fall at one level within at most five ascents (two out of
  three in the shortened version). The threshold is the lowest level at which
  responses occur in more than half of the ascents
  ([`ascending_method_threshold`](/phonometry/reference/api/hearing/audiometry/#ascending_method_threshold), which also replays a presentation
  sequence and gives the next level to present);
- the **bracketing method** (6.2.4.3) averages the lowest response levels of
  the ascents, and those of the descents, and rounds the mean of the two
  averages to the nearest 5 dB step ([`bracketing_method_threshold`](/phonometry/reference/api/hearing/audiometry/#bracketing_method_threshold));
- **automatic recording** audiometry (6.3.5) averages the peaks and the
  valleys of the tracing, after dropping the first reversal and those of
  excursions of 3 dB or less, and rounds the mean of the two up to the next
  whole decibel ([`automatic_audiometry_threshold`](/phonometry/reference/api/hearing/audiometry/#automatic_audiometry_threshold));
- **sweep-frequency** audiometry (7.5) averages the three peaks and the three
  valleys closest to a frequency, or runs that average along the tracing
  ([`sweep_audiometry_threshold`](/phonometry/reference/api/hearing/audiometry/#sweep_audiometry_threshold)).

Each also carries the text's own reliability test: a span of more than 10 dB
between the levels it averages.

**The cautions (6.2.3.2, 8.4).** Three more rules of the text judge the
levels once they are found. Step 3 of 6.2.3.2 repeats the measurement at
1 kHz, and the first ear is done when the two agree to 5 dB or less
([`check_retest_agreement`](/phonometry/reference/api/hearing/audiometry/#check_retest_agreement)). A hearing level of 40 dB or more calls for
caution because of cross-hearing (6.2.3.2), and a bone-conduction level at the
average vibrotactile threshold of 8.4 may be felt rather than heard
([`VIBROTACTILE_HEARING_LEVELS_DB`](/phonometry/reference/api/hearing/audiometry/#vibrotactile_hearing_levels_db)); [`audiogram_cautions`](/phonometry/reference/api/hearing/audiometry/#audiogram_cautions) flags
both.

**The uncertainty (Annex A).** The hearing threshold level is modelled as the
determined value plus seven zero-mean input quantities (Formula (A.1)), all
uncorrelated with a sensitivity coefficient of 1, so the combined standard
uncertainty is their root sum of squares (Formula (A.2)) and the expanded
one twice that:

$$
u = \sqrt{\sum_{i=1}^{8} u_i^2}, \qquad U = 2u
$$

A.3 gives typical values for the repeatability, the audiometer, the
transducer, the ambient noise and the masking;
[`audiometric_uncertainty`](/phonometry/reference/api/hearing/audiometry/#audiometric_uncertainty) assembles them into an
[`AudiometricUncertaintyBudget`](/phonometry/reference/api/hearing/audiometry/#audiometricuncertaintybudget), and for air conduction below 4 kHz
without masking it reproduces the example of Table A.2: $u$ = 4,9 dB and
$U$ = 10 dB.

Clause, table and formula numbers refer to ISO 8253-1:2010(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AIR_CONDUCTION_AMBIENT_LIMITS_DB

*Constant* (`mapping`).

```python
AIR_CONDUCTION_AMBIENT_LIMITS_DB = {125.0: array([56., 52., 47., 42., 38., 33., 28., 23., 20., 19., 18., 18., 18.,
       18., 20., 23., 25., 27., 30., 32., 34., 36., 35., 34., 33.]), 250.0: array([66., 62., 57., 52., 48., 43., 39., 30., 20., 19., 18., 18., 18.,
       18., 20., 23., 25., 27., 30., 32., 34., 36., 35., 34., 33.]), 500.0: array([78., 73., 68., 64., 59., 55., 51., 47., 42., 37., 33., 24., 18.,
       18., 20., 23., 25., 27., 30., 32., 34., 36., 35., 34., 33.])}
```

## AMBIENT_NOISE_BANDS_HZ

*Constant* (`tuple`).

```python
AMBIENT_NOISE_BANDS_HZ = (31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0)
```

## ambient_noise_limits

```python
ambient_noise_limits(
    presentation: str = 'air',
    *,
    lowest_test_frequency_hz: float = 125.0,
    earphone: str = 'supra-aural',
    earphone_attenuation_db: ArrayLike | None = None,
    lowest_hearing_level_db: float = 0.0,
    allowed_threshold_shift_db: float = 2.0,
) -> np.ndarray
```

The maximum permissible ambient sound pressure levels of a test room.

For air conduction (ISO 8253-1 Table 2), bone conduction (Table 4) or
sound field audiometry (ISO 8253-2 Table 2), in one-third-octave bands:

$$
L_{S,\mathrm{max}}' = L_{S,\mathrm{max}} + \left(A_\mathrm{earphone} - A_\mathrm{supra\text{-}aural}\right) + L_\mathrm{HT,min} + \Delta
$$

with the earphone term of 11.1 for air conduction (Table 3), the lowest
hearing threshold level $L_\mathrm{HT,min}$ to be measured (11.1 and
ISO 8253-2 Clause 6), and $\Delta$ = 8 dB when a threshold shift of
+5 dB from the ambient noise is accepted instead of +2 dB (NOTE to Table
2, NOTE 1 to Table 4, footnote a to ISO 8253-2 Table 2). Where Table 3
prints no attenuation, the HDA 200 below 63 Hz, no allowance is made:
the supra-aural earphone attenuates nothing there, so none is the
conservative reading.

**Parameters**

| Name | Description |
| :--- | :--- |
| `presentation` | `"air"` (default), `"bone"` or `"sound field"`. |
| `lowest_test_frequency_hz` | The lowest test tone frequency: 125 (default), 250, or for air conduction 500. |
| `earphone` | A column of [`EARPHONE_ATTENUATION_DB`](/phonometry/reference/api/hearing/audiometry/#earphone_attenuation_db), `"supra-aural"` (default), `"ER-3A"` or `"HDA 200"`; air conduction only. |
| `earphone_attenuation_db` | Or the attenuation of another earphone, one per band of [`AMBIENT_NOISE_BANDS_HZ`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_bands_hz), in dB; air conduction only. |
| `lowest_hearing_level_db` | The lowest hearing threshold level to be measured, in dB; 0 by default. |
| `allowed_threshold_shift_db` | The threshold shift accepted from the ambient noise, 2 (default) or 5, in dB. |

**Returns:** The limits in dB re 20 µPa, one per band of [`AMBIENT_NOISE_BANDS_HZ`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_bands_hz) for air and bone conduction and of [`phonometry.hearing.SOUND_FIELD_AMBIENT_BANDS_HZ`](/phonometry/reference/api/hearing/sound-field-audiometry/#sound_field_ambient_bands_hz) for sound field.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown presentation, lowest test frequency, earphone or threshold shift, or an earphone with bone conduction or sound field. |

## AmbientNoiseCheck

```python
AmbientNoiseCheck(
    presentation: str,
    frequencies: np.ndarray,
    levels_db: np.ndarray,
    lowest_test_frequency_hz: float,
    lowest_hearing_level_db: float,
    noise_floor_db: np.ndarray | None = None,
    earphone: str | None = None,
    earphone_attenuation_db: np.ndarray | None = None,
    allowed_threshold_shift_db: float = 2.0,
)
```

Whether a test room is quiet enough for the audiometry, band by band.

The fields hold what was measured and what the standard lets the tester
choose: the presentation, the lowest test frequency, the lowest hearing
level to be measured, the earphone and the threshold shift accepted. The
limits themselves (`limits_db`) are read from the tables with those
choices, so a check cannot be built against another table.

**Attributes**

| Name | Description |
| :--- | :--- |
| `presentation` | `"air"`, `"bone"` or `"sound field"`. |
| `frequencies` | The one-third-octave mid-frequencies judged, in hertz, each one of `table_bands_hz`. |
| `levels_db` | The measured ambient sound pressure level per band, in dB. |
| `lowest_test_frequency_hz` | The lowest test tone frequency, in hertz. |
| `lowest_hearing_level_db` | The lowest hearing threshold level to be measured the limits were raised for, in dB. |
| `noise_floor_db` | The measuring chain's noise floor per band, in dB, or `None` when not given. |
| `earphone` | For air conduction, the earphone the limits were written for: a column of Table 3, or `"own attenuation"` for an attenuation given band by band; `None` for bone conduction and sound field. |
| `earphone_attenuation_db` | The earphone's own attenuation per band of [`AMBIENT_NOISE_BANDS_HZ`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_bands_hz), in dB, when `earphone` is `"own attenuation"`; `None` otherwise. |
| `allowed_threshold_shift_db` | The threshold shift accepted from the ambient noise, 2 (default) or 5, in dB. |

A band the measurement leaves out is a band the room is not shown to meet,
so `passes` needs every band of the table.

### AmbientNoiseCheck.covers_all_bands

*property*

Whether the measurement gives every band the table limits.

**Returns:** `True` when no band of the table is missing.

### AmbientNoiseCheck.exceedance_db

*property*

The measured level less the limit per band, in dB.

**Returns:** Positive where the room is too loud.

### AmbientNoiseCheck.floor_limited

*property*

Per band, whether the reading is within 6 dB of the noise floor.

11.1 asks the measuring chain for a noise floor at least 6 dB below
the level it measures. A band that misses it reads high, so a band
within its limit still is; one over its limit may be the floor's.

**Returns:** One boolean per band, all `False` without a floor.

### AmbientNoiseCheck.limits_db

*property*

The maximum permissible level per band, in dB.

**Returns:** [`ambient_noise_limits`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_limits) of the presentation and the tester's choices, at `frequencies`.

### AmbientNoiseCheck.lowest_measurable_hearing_level_db

*property*

The lowest hearing threshold level this room lets be measured, in dB.

11.1 raises every limit by the lowest hearing threshold level to be
measured, and ISO 8253-2 Clause 6 does the same for sound field
audiometry, so the room allows the lowest level that brings every
measured band under its raised limit. For sound field audiometry,
ISO 8253-2 11.1 f) asks the report to state it when it is not 0 dB.
ISO 8253-1 has no such reporting item: with earphones or a bone
vibrator it is the level the rule of 11.1 implies.

**Returns:** `lowest_hearing_level_db` plus the largest exceedance.

### AmbientNoiseCheck.passes

*property*

Whether every band of the table was measured and is within its limit.

**Returns:** `True` when the room qualifies.

### AmbientNoiseCheck.plot()

```python
AmbientNoiseCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the measured spectrum against the limits, exceedances marked.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the measured spectrum. |

**Returns:** The axes.

### AmbientNoiseCheck.table_bands_hz

*property*

Every band the table sets a limit for, in hertz.

### AmbientNoiseCheck.within

*property*

Per band, whether the measured level is at or below the limit.

**Returns:** One boolean per band.

## ascending_method_threshold

```python
ascending_method_threshold(
    ascent_levels_db: ArrayLike | None = None,
    *,
    presentation_levels_db: ArrayLike | None = None,
    responses: ArrayLike | None = None,
    shortened: bool = False,
    familiarization_level_db: float | None = None,
) -> AscendingThresholdResult
```

The hearing threshold level by the ascending method (6.2.3.2, 6.2.4.2).

The method presents tones of 1 s to 2 s. Step 1 starts 10 dB below the
lowest level the subject responded to during familiarization and rises
in 5 dB steps until a response; Step 2 drops 10 dB after each response
until there is none, and ascends again in 5 dB steps. The series stops
when three responses fall at one level within at most five ascents, or,
in the shortened version, two within at most three. The hearing threshold
level is then the lowest level at which responses occur in more than half
of the ascents (6.2.4.2).

Give either the level at which each ascent ended in a response, or the
whole presentation sequence with its responses. The sequence is replayed
against the steps of 6.2.3.2, an ascent being a response reached from a
tone that drew none, and the result says what to present next, which is
the level a computer-controlled audiometer (6.4) can be given: call it
with an empty sequence and the familiarization level for the first tone.

After five ascents without three responses at one level the series is
exhausted, and 6.2.3.2 starts a new one 10 dB above the last response;
that is a new call. 6.2.3.2 does not say what follows a shortened series
that ends its three ascents without two responses at one level; the
library's choice is to continue it with the full method on the same
presentations, a new call with `shortened=False`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ascent_levels_db` | The response level of each ascent, in dB, in order. |
| `presentation_levels_db` | Or the hearing level of every tone presented, in dB, in order. |
| `responses` | With it, whether each tone drew a response. |
| `shortened` | `True` for the shortened version. |
| `familiarization_level_db` | The lowest level of the subject's responses during familiarization (6.2.2), in dB, to check the first tone of a sequence, or to give it when the sequence is empty. |

**Returns:** [`AscendingThresholdResult`](/phonometry/reference/api/hearing/audiometry/#ascendingthresholdresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if neither form or both are given, the responses do not match the presentations, a step differs from 6.2.3.2, a presentation follows the end of the series, or more ascents are given than a series holds. |

## AscendingThresholdResult

```python
AscendingThresholdResult(
    ascent_levels_db: np.ndarray,
    threshold_db: float,
    determined: bool,
    shortened: bool,
    series_exhausted: bool,
    next_level_db: float,
    presentation_levels_db: np.ndarray | None = None,
    responses: np.ndarray | None = None,
)
```

The hearing threshold level by the ascending method (6.2.4.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `ascent_levels_db` | The level at which each ascent ended in a response, in presentation order, in dB. |
| `threshold_db` | The hearing threshold level, in dB: the lowest level at which responses occur in more than half of the ascents, once the stopping rule of 6.2.3.2 is met; NaN until then. |
| `determined` | Whether the stopping rule is met: three responses at one level (two in the shortened version). |
| `shortened` | Whether the shortened version was applied. |
| `series_exhausted` | Whether the series used up its ascents (five, or three shortened) without a threshold. The full method then starts a new series 10 dB above the last response. |
| `next_level_db` | The level to present next, in dB, when the presentations were given and no threshold is determined yet; NaN otherwise. |
| `presentation_levels_db` | The levels presented, in dB, or `None` when only the ascents were given. |
| `responses` | Whether each presentation drew a response, or `None`. |

### AscendingThresholdResult.doubtful

*property*

Whether the response levels span more than 10 dB (6.2.4.2).

The text says such a test should be considered of doubtful reliability,
repeated, and noted on the audiogram.

**Returns:** `True` when the span exceeds 10 dB.

### AscendingThresholdResult.plot()

```python
AscendingThresholdResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the presentations, heard and not heard, and the threshold.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the presentation staircase. |

**Returns:** The axes.

### AscendingThresholdResult.responses_at_threshold

*property*

How many ascents ended at the threshold level.

**Returns:** The count, 0 when no threshold is determined.

### AscendingThresholdResult.span_db

*property*

The spread of the ascents' response levels, in dB.

**Returns:** The largest less the smallest, 0 for fewer than two ascents.

## audiogram_cautions

```python
audiogram_cautions(
    frequencies: ArrayLike,
    *,
    air_conduction_db: ArrayLike | None = None,
    bone_conduction_db: ArrayLike | None = None,
    vibrator_placement: str = 'mastoid',
) -> AudiogramCautions
```

Flag the levels of an audiogram that call for caution (6.2.3.2, 8.4).

Two rules of ISO 8253-1 judge a hearing threshold level by its size:

- **cross-hearing** (6.2.3.2): an air-conduction hearing level of 40 dB
  or more, in either ear at any frequency, is to be interpreted with
  caution, because the tone may reach the other ear; contralateral
  masking can then be necessary;
- **vibrotactile sensation** (8.4): with the bone vibrator on the
  mastoid, the vibrotactile threshold lies on average at a hearing level
  of about 40 dB at 250 Hz, 60 dB at 500 Hz and 70 dB at 1 kHz, about
  10 dB lower for an audiometer calibrated for forehead placement, and a
  bone-conduction response at such a level may be felt rather than heard.

Give the levels of one ear; the caution of 6.2.3.2 holds for the results
when either ear reaches 40 dB. Bone conduction gets no cross-hearing flag,
because 40 dB is not its limit: 8.1 asks for the non-test ear to be
masked at every level for a precise monaural result. 8.4 gives no
vibrotactile level at other frequencies, where nothing is flagged, and its
levels are averages about which individuals vary widely.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | The test frequencies, in hertz. |
| `air_conduction_db` | The air-conduction hearing threshold levels, in dB, one per frequency. |
| `bone_conduction_db` | The bone-conduction hearing threshold levels, in dB, one per frequency. |
| `vibrator_placement` | `"mastoid"` (default) or `"forehead"`, the placement the bone conduction is calibrated for. |

**Returns:** [`AudiogramCautions`](/phonometry/reference/api/hearing/audiometry/#audiogramcautions).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for neither set of levels, levels that do not match the frequencies, a frequency that is not positive, or an unknown placement. |

## AudiogramCautions

```python
AudiogramCautions(
    frequencies: np.ndarray,
    air_conduction_db: np.ndarray | None,
    bone_conduction_db: np.ndarray | None,
    vibrator_placement: str,
)
```

The levels of an audiogram that call for caution (6.2.3.2, 8.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The test frequencies, in hertz. |
| `air_conduction_db` | The air-conduction hearing threshold levels of one ear, in dB, one per frequency, or `None`. |
| `bone_conduction_db` | The bone-conduction hearing threshold levels, in dB, one per frequency, or `None`. |
| `vibrator_placement` | `"mastoid"` or `"forehead"`, the placement the audiometer's bone conduction is calibrated for. |

### AudiogramCautions.any_caution

*property*

Whether any level is flagged by either rule.

**Returns:** `True` when some level calls for caution.

### AudiogramCautions.cross_hearing

*property*

Per frequency, whether the air-conduction level is 40 dB or more.

6.2.3.2 asks for such results to be interpreted with caution because
of cross-hearing: the tone may be heard by the other ear, and
contralateral masking can be necessary.

**Returns:** One boolean per frequency, all `False` without air conduction levels.

### AudiogramCautions.plot()

```python
AudiogramCautions.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the audiogram with the caution levels and the levels flagged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the air-conduction curve. |

**Returns:** The axes.

### AudiogramCautions.vibrotactile

*property*

Per frequency, whether the bone-conduction level reaches 8.4's level.

At or above the average vibrotactile threshold the subject may feel
the vibrator rather than hear the tone, and 8.4 says care shall be
taken that such a sensation is not taken for hearing.

**Returns:** One boolean per frequency, `False` where 8.4 gives no level or without bone conduction levels.

### AudiogramCautions.vibrotactile_levels_db

*property*

The average vibrotactile threshold of 8.4 at each frequency, in dB.

**Returns:** One level per frequency, 10 dB lower for forehead placement, NaN where 8.4 gives none.

## audiometric_uncertainty

```python
audiometric_uncertainty(
    frequency: float,
    *,
    conduction: str = 'air',
    masked: bool = False,
    level_step_db: float = 5.0,
    environment_db: float = 2.0,
    tester_db: float = 0.0,
    subject_db: float = 0.0,
    special_db: float = 0.0,
) -> AudiometricUncertaintyBudget
```

The typical uncertainty budget of a hearing threshold level (A.3).

Fills Table A.1 with the values A.3 gives, which differ up to and above
4 kHz:

- $u_1$ (A.3.2): 2,5 dB and 4 dB for air conduction, 3 dB and 5 dB
  for bone conduction;
- $u_2$ (A.3.3): the audiometer's maximum output deviation
  $a$ of IEC 60645-1 (±3 dB and ±5 dB for air, ±4 dB and ±5 dB for
  bone), rectangular, with the attenuator step $s$ rounding the
  level, also rectangular:

  $$
  u_2 = \sqrt{\left(\frac{a}{\sqrt{3}}\right)^2 + \left(\frac{s}{2\sqrt{3}}\right)^2}
  $$

  which for air conduction up to 4 kHz and 5 dB steps is 2,3 dB;
- $u_3$ (A.3.4): $\sqrt{1{,}5^2 + 2{,}5^2}$ = 2,9 dB up to
  4 kHz and $\sqrt{2{,}5^2 + 3^2}$ = 3,9 dB above;
- $u_4$ (A.3.5): 2 dB when the ambient noise meets Clause 11 and the
  subject's threshold is near 0 dB. It may be negligible for thresholds
  well above 0 dB and is considerably larger in a room that exceeds the
  limits; give it with `environment_db`;
- $u_5$ (A.3.6): 2 dB when masking noise is applied;
- $u_6$ to $u_8$ (A.3.7 to A.3.9): zero in usual situations,
  where the repeatability already covers them; give them when an
  exceptional situation calls for them.

For air conduction below 4 kHz without masking this is the example of
Table A.2: $u$ = 4,9 dB and $U$ = 10 dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | The test frequency, in hertz. |
| `conduction` | `"air"` (default) or `"bone"`. |
| `masked` | Whether masking noise was applied (A.3.6). |
| `level_step_db` | The step of the hearing level control, in dB; 5 by default, 0 for a control fine enough not to count. |
| `environment_db` | $u_4$, in dB; 2 by default (A.3.5). |
| `tester_db` | $u_6$, in dB. |
| `subject_db` | $u_7$, in dB. |
| `special_db` | $u_8$, in dB. |

**Returns:** [`AudiometricUncertaintyBudget`](/phonometry/reference/api/hearing/audiometry/#audiometricuncertaintybudget).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown conduction, a frequency that is not positive, or a component or step that is negative or not finite. |

## AudiometricUncertaintyBudget

```python
AudiometricUncertaintyBudget(
    repeatability_db: float,
    equipment_db: float,
    transducer_db: float,
    environment_db: float,
    masking_db: float = 0.0,
    tester_db: float = 0.0,
    subject_db: float = 0.0,
    special_db: float = 0.0,
)
```

The uncertainty budget of a hearing threshold level (Annex A).

The eight standard uncertainties of Table A.1, each with a sensitivity
coefficient of 1 and uncorrelated with the others (A.2), so the combined
standard uncertainty is their root sum of squares (Formula (A.2)) and the
expanded one is $U = k u$ with $k$ = 2 (A.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `repeatability_db` | $u_1$, repeated determinations of $L'_\mathrm{HT}$ (A.3.2), in dB. |
| `equipment_db` | $u_2$, the audiometer (A.3.3), in dB; its distribution is rectangular, the others normal. |
| `transducer_db` | $u_3$, the transducer and its fitting (A.3.4), in dB. |
| `environment_db` | $u_4$, the ambient noise (A.3.5), in dB. |
| `masking_db` | $u_5$, a non-optimized masking noise (A.3.6), in dB. |
| `tester_db` | $u_6$, the tester's experience (A.3.7), in dB. |
| `subject_db` | $u_7$, the subject's responses (A.3.8), in dB. |
| `special_db` | $u_8$, an unusually difficult measurement (A.3.9), in dB. |

### AudiometricUncertaintyBudget.combined_db

*property*

$u = \sqrt{\sum u_i^2}$ (Formula (A.2)), in dB.

**Returns:** The combined standard uncertainty, unrounded.

### AudiometricUncertaintyBudget.components_db

*property*

The eight standard uncertainties in the order of Table A.1, in dB.

**Returns:** $u_1$ to $u_8$.

### AudiometricUncertaintyBudget.expanded_db

*property*

$U = 2u$ for a coverage probability of 95 % (A.5), in dB.

**Returns:** The expanded uncertainty, unrounded; A.6 reports it rounded to the nearest full decibel.

### AudiometricUncertaintyBudget.labels

*property*

The eight input quantities of Table A.1, in its order.

**Returns:** Their symbols.

### AudiometricUncertaintyBudget.plot()

```python
AudiometricUncertaintyBudget.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the eight contributions as bars, with the combined value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the contribution bars. |

**Returns:** The axes.

## automatic_audiometry_threshold

```python
automatic_audiometry_threshold(
    reversal_levels_db: ArrayLike,
) -> AutomaticThresholdResult
```

The hearing threshold level from an automatic recording (6.3.5).

The subject holds the level down while the tone is heard and lets it rise
when it is not, so the tracing zigzags about the threshold. At one
frequency, 6.3.5:

- a) ignores the first reversal after the change of frequency and every
  reversal of an excursion of 3 dB or less (both reversals that bound it);
- b) averages the remaining peaks, and averages the remaining valleys;
- c) takes the mean of the two averages, rounded up to the nearest whole
  number of decibels, as the hearing threshold level.

The recording is of doubtful reliability, and should be repeated, when the
peaks or the valleys deviate by more than 10 dB from each other or fewer
than six reversals remain after a). NOTE 2 to 6.3.5 puts automatic
thresholds 3 dB lower on average than manual ones with 5 dB steps; that
is a property of the method, and nothing here corrects for it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reversal_levels_db` | The hearing level at each reversal of the tracing at one frequency, in dB, in the order they were traced. |

**Returns:** [`AutomaticThresholdResult`](/phonometry/reference/api/hearing/audiometry/#automaticthresholdresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than three reversals, reversals that do not alternate between peaks and valleys, or a tracing that keeps no peak or no valley after a). |

## AutomaticThresholdResult

```python
AutomaticThresholdResult(
    reversal_levels_db: np.ndarray,
    is_peak: np.ndarray,
    retained: np.ndarray,
    mean_db: float,
    threshold_db: float,
)
```

The hearing threshold level from an automatic recording (6.3.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `reversal_levels_db` | The levels at the reversals of the tracing at one frequency, in order, in dB. |
| `is_peak` | Whether each reversal is a peak (a local maximum of the level), the others being valleys. |
| `retained` | Whether each reversal is kept after 6.3.5 a): the first is ignored, and so are both ends of every excursion of 3 dB or less. |
| `mean_db` | The mean of the average peak and the average valley, in dB. |
| `threshold_db` | That mean rounded up to the next whole decibel, in dB. |

### AutomaticThresholdResult.doubtful

*property*

Whether the recording should be repeated (6.3.5).

**Returns:** `True` when the peaks or the valleys deviate by more than 10 dB from each other, or fewer than six reversals remain.

### AutomaticThresholdResult.peaks_db

*property*

The retained peaks, in dB.

**Returns:** Their levels, in order.

### AutomaticThresholdResult.plot()

```python
AutomaticThresholdResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the tracing through its reversals, the ignored ones faded.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the tracing. |

**Returns:** The axes.

### AutomaticThresholdResult.valleys_db

*property*

The retained valleys, in dB.

**Returns:** Their levels, in order.

## BONE_CONDUCTION_AMBIENT_LIMITS_DB

*Constant* (`mapping`).

```python
BONE_CONDUCTION_AMBIENT_LIMITS_DB = {125.0: array([55., 47., 41., 35., 30., 25., 20., 17., 15., 13., 11.,  9.,  8.,
        8.,  7.,  7.,  7.,  8.,  8.,  6.,  4.,  2.,  4.,  9., 15.]), 250.0: array([63., 56., 49., 44., 39., 35., 28., 21., 15., 13., 11.,  9.,  8.,
        8.,  7.,  7.,  7.,  8.,  8.,  6.,  4.,  2.,  4.,  9., 15.])}
```

## bracketing_method_threshold

```python
bracketing_method_threshold(
    ascent_levels_db: ArrayLike,
    descent_levels_db: ArrayLike,
) -> BracketingThresholdResult
```

The hearing threshold level by the bracketing method (6.2.4.3).

The bracketing method ascends in 5 dB steps to a response, rises 5 dB and
descends in 5 dB steps until there is none, three ascents and three
descents in all, or two of each when their four lowest response levels
are within 5 dB of each other (6.2.3.2). The threshold averages the lowest
response levels of the ascents, averages those of the descents, and
rounds the mean of the two averages to the nearest 5 dB step:

$$
L_\mathrm{HT} = 5\ \mathrm{dB} \times \operatorname{round}\left( \frac{\bar L_\mathrm{asc} + \bar L_\mathrm{desc}}{2 \times 5\ \mathrm{dB}} \right)
$$

A mean halfway between two steps goes to the higher step, the rounding
the library applies wherever a standard says "nearest" without a rule for
the tie.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ascent_levels_db` | The lowest level at which a response occurred in each ascent, in dB. |
| `descent_levels_db` | The lowest level at which a response occurred in each descent, in dB. |

**Returns:** [`BracketingThresholdResult`](/phonometry/reference/api/hearing/audiometry/#bracketingthresholdresult), which also says whether the series is complete and whether 6.2.4.3 advises a repeat.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty or non-finite set of levels. |

## BracketingThresholdResult

```python
BracketingThresholdResult(
    ascent_levels_db: np.ndarray,
    descent_levels_db: np.ndarray,
    mean_db: float,
    threshold_db: float,
)
```

The hearing threshold level by the bracketing method (6.2.4.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `ascent_levels_db` | The lowest response level of each ascent, in dB. |
| `descent_levels_db` | The lowest response level of each descent, in dB. |
| `mean_db` | The mean of the two averages, unrounded, in dB. |
| `threshold_db` | That mean rounded to the nearest 5 dB step, in dB; a mean halfway between two steps goes to the higher one. |

### BracketingThresholdResult.ascent_mean_db

*property*

The average of the ascents' lowest response levels, in dB.

**Returns:** The mean.

### BracketingThresholdResult.complete

*property*

Whether the series is long enough (6.2.3.2 Step 2).

**Returns:** `True` for three ascents and three descents, or for two of each whose four levels differ by no more than 5 dB (the shortened version).

### BracketingThresholdResult.descent_mean_db

*property*

The average of the descents' lowest response levels, in dB.

**Returns:** The mean.

### BracketingThresholdResult.plot()

```python
BracketingThresholdResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the ascents' and descents' levels, their means and the threshold.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the ascents' markers. |

**Returns:** The axes.

### BracketingThresholdResult.repeat_advised

*property*

Whether the ascents or the descents spread over more than 10 dB.

6.2.4.3 says the test should then be repeated.

**Returns:** `True` when either set of levels spans more than 10 dB.

## check_audiometric_ambient_noise

```python
check_audiometric_ambient_noise(
    levels_db: ArrayLike,
    *,
    presentation: str = 'air',
    lowest_test_frequency_hz: float = 125.0,
    earphone: str = 'supra-aural',
    earphone_attenuation_db: ArrayLike | None = None,
    lowest_hearing_level_db: float = 0.0,
    allowed_threshold_shift_db: float = 2.0,
    frequencies: ArrayLike | None = None,
    noise_floor_db: ArrayLike | None = None,
) -> AmbientNoiseCheck
```

Is the test room quiet enough for the audiometry? (ISO 8253-1 Clause 11).

Compares the ambient sound pressure level measured at the position of the
subject's head, with the subject absent and the room as it is during
testing (ventilation running if it runs then), with the limits of
[`ambient_noise_limits`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_limits): ISO 8253-1 Table 2 for air conduction,
Table 4 for bone conduction, or ISO 8253-2 Table 2 for sound field
audiometry (its Clause 6).

With `presentation="sound field"` and narrow-band noise as the test
signal, footnote b to ISO 8253-2 Table 2 says the limits should be lower
than the table's. It prints no figure for how much, so the check applies
the table as printed, and a room that passes it may still be too loud for
a narrow-band noise signal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The measured one-third-octave band levels, in dB re 20 µPa: one per band of the table, or one per band of `frequencies`. |
| `presentation` | `"air"` (default), `"bone"` or `"sound field"`. |
| `lowest_test_frequency_hz` | The lowest test tone frequency, 125 (default), 250, or for air conduction 500. |
| `earphone` | A column of Table 3; air conduction only. |
| `earphone_attenuation_db` | Or another earphone's attenuation per band of Table 3; air conduction only. |
| `lowest_hearing_level_db` | The lowest hearing threshold level to be measured, in dB; 0 by default. |
| `allowed_threshold_shift_db` | The threshold shift accepted from the ambient noise, 2 (default) or 5, in dB. |
| `frequencies` | The mid-frequencies of the measured bands, in hertz, each one of the table's, or `None` for all of them. A measurement that leaves bands out is judged on those it has, and does not pass. |
| `noise_floor_db` | The measuring chain's noise floor per measured band, in dB, to flag the bands where 11.1's 6 dB margin is missed. |

**Returns:** [`AmbientNoiseCheck`](/phonometry/reference/api/hearing/audiometry/#ambientnoisecheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for the reasons [`ambient_noise_limits`](/phonometry/reference/api/hearing/audiometry/#ambient_noise_limits) gives, a frequency the table does not list, or levels that do not match the bands. |

## check_retest_agreement

```python
check_retest_agreement(
    first_db: float,
    repeat_db: float,
    *,
    frequency_hz: float = 1000.0,
) -> RetestAgreementCheck
```

Does the repeat measurement confirm the first? (6.2.3.2 Step 3).

Once every frequency of the first ear is tested, Step 3 repeats the
measurement at 1 kHz. If the repeat agrees with the first measurement to
5 dB or less, the test proceeds to the other ear; if it shows an
improvement or a worsening of 10 dB or more, the further frequencies are
retested in the same order until agreement to 5 dB or less is obtained.
ISO 8253-2 8.1 asks for the same repeat at 1 kHz in sound field
audiometry.

The text is written for the 5 dB steps of a manual audiometer, where a
difference is either 5 dB or less or 10 dB or more. A finer control can
give a difference in between; it is not agreement to 5 dB or less, so it
does not pass, and the text names no action for it, so
[`RetestAgreementCheck.retest_further_frequencies`](/phonometry/reference/api/hearing/audiometry/#retestagreementcheckretest_further_frequencies) is `False` too.

**Parameters**

| Name | Description |
| :--- | :--- |
| `first_db` | The hearing threshold level measured first, in dB. |
| `repeat_db` | The hearing threshold level of the repeat, in dB. |
| `frequency_hz` | The frequency of both, in hertz; 1 kHz by default. |

**Returns:** [`RetestAgreementCheck`](/phonometry/reference/api/hearing/audiometry/#retestagreementcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a level that is not finite or a frequency that is not positive. |

## EARPHONE_ATTENUATION_DB

*Constant* (`mapping`).

```python
EARPHONE_ATTENUATION_DB = {'supra-aural': array([ 0.,  0.,  0.,  1.,  1.,  2.,  3.,  4.,  5.,  5.,  5.,  6.,  7.,
        9., 11., 15., 18., 21., 26., 28., 31., 32., 29., 26., 24.]), 'ER-3A': array([33., 33., 33., 33., 33., 33., 33., 34., 35., 36., 37., 37., 38.,
       37., 37., 37., 35., 34., 33., 35., 37., 40., 41., 42., 43.]), 'HDA 200': array([nan, nan, nan, 17., 16., 15., 15., 15., 16., 16., 18., 20., 23.,
       25., 27., 29., 30., 31., 32., 37., 41., 46., 45., 45., 44.])}
```

## RetestAgreementCheck

```python
RetestAgreementCheck(first_db: float, repeat_db: float, frequency_hz: float)
```

Whether a repeat measurement confirms the first one (6.2.3.2 Step 3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `first_db` | The hearing threshold level measured first, in dB. |
| `repeat_db` | The hearing threshold level of the repeat measurement, in dB. |
| `frequency_hz` | The frequency of both, in hertz: 1 kHz for the repeat Step 3 asks for, another for a further frequency retested after it. |

### RetestAgreementCheck.difference_db

*property*

The repeat less the first measurement, in dB.

**Returns:** Positive for a worsening, negative for an improvement.

### RetestAgreementCheck.passes

*property*

Whether the two agree to 5 dB or less, and the test moves on.

**Returns:** `True` when the difference is at most 5 dB either way.

### RetestAgreementCheck.plot()

```python
RetestAgreementCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two measurements and the 5 dB either side of the first.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the two measurements' markers. |

**Returns:** The axes.

### RetestAgreementCheck.retest_further_frequencies

*property*

Whether Step 3 sends the test back to the further frequencies.

**Returns:** `True` for an improvement or a worsening of 10 dB or more.

## sweep_audiometry_threshold

```python
sweep_audiometry_threshold(
    reversal_frequencies: ArrayLike,
    reversal_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> SweepThresholdResult
```

Hearing threshold levels from a sweep-frequency tracing (7.5).

The frequency sweeps continuously, normally at 0,5 to 2 octaves per
minute, while the subject tracks the threshold as in automatic
audiometry. At a specified frequency, 7.5 averages the three peaks and the
three valleys of the tracing closest to it and takes the mean of the two
averages, rounded to the nearest whole decibel, as the hearing threshold
level there. Closest is measured on the logarithmic frequency axis the
sweep runs on, and a mean halfway between two decibels goes up.

As a semicontinuous function of frequency, 7.5 runs the average along the
tracing: each run of three consecutive pairs of peaks and valleys, six
consecutive reversals, gives the arithmetic mean of its six levels at the
geometric mean of its six frequencies,

$$
L_\mathrm{HT}\left(\sqrt[6]{f_1 f_2 \cdots f_6}\right) = \frac{1}{6} \sum_{k=1}^{6} L_k
$$

and the run advances one reversal at a time.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reversal_frequencies` | The frequency at each reversal, in hertz, in the order traced; the sweep may run upwards or downwards. |
| `reversal_levels_db` | The hearing level at each reversal, in dB. |
| `frequencies` | The frequencies to determine the threshold at, in hertz, or `None` for the audiometric frequencies from 125 Hz to 8 kHz that the tracing spans. |

**Returns:** [`SweepThresholdResult`](/phonometry/reference/api/hearing/audiometry/#sweepthresholdresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for arrays that do not match, fewer than three peaks or three valleys, reversals that do not alternate, a sweep that does not run one way, or no frequency to determine. |

## SweepThresholdResult

```python
SweepThresholdResult(
    reversal_frequencies: np.ndarray,
    reversal_levels_db: np.ndarray,
    is_peak: np.ndarray,
    frequencies: np.ndarray,
    mean_db: np.ndarray,
    threshold_db: np.ndarray,
    spread_db: np.ndarray,
    running_frequencies: np.ndarray,
    running_threshold_db: np.ndarray,
)
```

Hearing threshold levels from a sweep-frequency tracing (7.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `reversal_frequencies` | The frequency of each reversal, in hertz. |
| `reversal_levels_db` | The hearing level of each reversal, in dB. |
| `is_peak` | Whether each reversal is a peak, the others being valleys. |
| `frequencies` | The frequencies the threshold was determined at, in hertz. |
| `mean_db` | At each, the mean of the average of the three nearest peaks and the average of the three nearest valleys, in dB. |
| `threshold_db` | That mean rounded to the nearest whole decibel, in dB. |
| `spread_db` | At each, the larger spread of the three peaks and of the three valleys it averaged, in dB. |
| `running_frequencies` | The geometric mean frequency of each run of six consecutive reversals, in hertz. |
| `running_threshold_db` | The arithmetic mean level of each run, in dB, the semicontinuous threshold of 7.5. |

### SweepThresholdResult.less_reliable

*property*

Per frequency, whether its peaks or valleys spread over 10 dB.

7.5 NOTE 1 calls such a determination less reliable.

**Returns:** One boolean per frequency.

### SweepThresholdResult.plot()

```python
SweepThresholdResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the tracing, its running threshold and the thresholds found.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the running threshold. |

**Returns:** The axes.

## VIBROTACTILE_HEARING_LEVELS_DB

*Constant* (`mapping`).

```python
VIBROTACTILE_HEARING_LEVELS_DB = {250.0: 40.0, 500.0: 60.0, 1000.0: 70.0}
```
