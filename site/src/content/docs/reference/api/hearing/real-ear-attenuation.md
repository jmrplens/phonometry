---
title: "hearing.real_ear_attenuation"
description: "Real-ear attenuation of a hearing protector and its uncertainty (ISO 4869-1:2018)."
sidebar:
  label: "real_ear_attenuation"
---

Real-ear attenuation of a hearing protector and its uncertainty (ISO 4869-1:2018).

ISO 4869-2 starts from a grid of attenuations, one per subject per octave band,
and this is where that grid comes from. ISO 4869-1 measures it subjectively:
each of sixteen test subjects finds their threshold of hearing twice for every
test signal, once with open ears and once with the protector in place, and the
attenuation of that subject in that band is the difference (4.6.2):

$$
A_{j,f} = L_{\mathrm{occluded},j,f} - L_{\mathrm{open},j,f}
$$

The test signals are one-third-octave bands of pink noise centred on the
octave frequencies 125 Hz to 8 kHz, with 63 Hz optional (4.1). The method
measures at threshold, so it describes a passive protector at any level but
underestimates one whose attenuation depends on level (Clause 1).

**What is reported (4.6.3, Clause 6).** The individual attenuations, and per
test signal their mean $m$ and standard deviation $s$, together
with the expanded uncertainty of the mean. The uncertainty is the subject of
the normative Annex A, which models the attenuation as the measured value plus
three zero-mean input quantities (Formula (A.1)): the method (subject group,
fitting, threshold determination, tester, specimen), the test equipment and
the environment, each normal with a sensitivity coefficient of 1. Within one
laboratory the combined standard uncertainty of a given measurement is the
standard deviation of the mean (A.2),

$$
u = \frac{s}{\sqrt{N}}, \qquad U_{95} = k\,u, \quad k = 2
$$

which is what [`real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/#real_ear_attenuation) returns. Table A.2 prints typical
values of the three components within a laboratory and Table B.2 between
laboratories, for earplugs and earmuffs in three frequency ranges;
[`REAT_WITHIN_LABORATORY_UNCERTAINTY`](/phonometry/reference/api/hearing/real-ear-attenuation/#reat_within_laboratory_uncertainty) and
[`REAT_BETWEEN_LABORATORY_UNCERTAINTY`](/phonometry/reference/api/hearing/real-ear-attenuation/#reat_between_laboratory_uncertainty) carry the components, and the
combined and expanded values are derived from them rather than copied, which
reproduces every cell the two tables print.

**Are two measurements different? (Annex B).** Two mean attenuations differ
significantly at the 5 % level when their difference exceeds the root sum of
squares of their expanded uncertainties (B.1.2),

$$
|m_1 - m_2| > \sqrt{U_{95,1}^2 + U_{95,2}^2}
$$

which for two equal uncertainties is $\sqrt{2}\,U_{95}$, the minimum
difference of B.1.1 and B.2. [`assess_attenuation_difference`](/phonometry/reference/api/hearing/real-ear-attenuation/#assess_attenuation_difference) applies it
band by band and [`minimum_significant_difference`](/phonometry/reference/api/hearing/real-ear-attenuation/#minimum_significant_difference) gives the second form.
B.1.1 and B.2 evaluate it on the **rounded** $U_{95}$ their tables print,
and say so: "the expanded measurement uncertainty ... is 2,3 dB. The minimum
difference is thus $\sqrt{2}$ × 2,3 dB = 3,3 dB". From the unrounded
2,27 dB it is 3,21 dB, and from the unrounded 6,62 dB of Table B.2 it is
9,37 dB rather than 9,3 dB; both are the same rule, fed a different precision.

**The sound field (4.2.2).** The test room is qualified with the subject absent:
the level 15 cm from the reference point along the three axes stays within
±2,5 dB of the level at it, the two ear-side positions within 3 dB of each
other, and from 500 Hz up a directional microphone rotated through 360° sees a
variation no larger than Table 1 allows for its free-field rejection.
[`check_reat_sound_field`](/phonometry/reference/api/hearing/real-ear-attenuation/#check_reat_sound_field) judges those three conditions, and its verdict
only passes a room whose directionality was measured: without the rotation, b)
is not judged and the room is not shown to qualify.

Clause, formula and table numbers refer to ISO 4869-1:2018(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## allowable_field_variation

```python
allowable_field_variation(free_field_rejection_db: float) -> float
```

How much a rotated directional microphone may see vary (Table 1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `free_field_rejection_db` | The free-field rejection of the directional microphone at the test signal, in dB: front to side for a cosine microphone, front to back for a cardioid one (4.2.2 b)). |

**Returns:** The allowable variation of the sound-field level, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a rejection below 10 dB, for which Table 1 says the microphone is not suitable, or one that is not finite. |

## assess_attenuation_difference

```python
assess_attenuation_difference(
    first: ArrayLike | RealEarAttenuationResult,
    second: ArrayLike | RealEarAttenuationResult,
    *,
    first_expanded_uncertainty_db: ArrayLike | None = None,
    second_expanded_uncertainty_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> AttenuationDifferenceResult
```

Do two attenuation measurements differ significantly? (Annex B).

Annex B asks it of two tests of the same earmuff in two configurations
(B.1.2), of two earplugs in one laboratory (B.1.1) and of one earplug in
two laboratories (B.2), and answers band by band the same way: the means
differ significantly at the 5 % level when

$$
|m_1 - m_2| > \sqrt{U_{95,1}^2 + U_{95,2}^2}
$$

Each measurement is either a [`RealEarAttenuationResult`](/phonometry/reference/api/hearing/real-ear-attenuation/#realearattenuationresult), which
carries its own $U_{95}$ from its own data (B.1.2), or its mean
attenuations with an uncertainty given alongside, such as the typical one
[`reat_expanded_uncertainty`](/phonometry/reference/api/hearing/real-ear-attenuation/#reat_expanded_uncertainty) reads from Table A.2 or B.2 (B.1.1,
B.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `first` | The first measurement, as a result or as its means in dB. |
| `second` | The second measurement, the same way. |
| `first_expanded_uncertainty_db` | $U_{95,1}$ in dB, a number or one per band, when `first` is given as means. |
| `second_expanded_uncertainty_db` | $U_{95,2}$ in dB, likewise. |
| `frequencies` | The centre frequencies, in hertz, or `None` to take them from a result or, for bare means, to assume the test signals of 4.1 as [`real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/#real_ear_attenuation) does. |

**Returns:** [`AttenuationDifferenceResult`](/phonometry/reference/api/hearing/real-ear-attenuation/#attenuationdifferenceresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if an uncertainty is missing for bare means or given twice for a result, if the two measurements cover different bands, or if a value is not finite. |

## AttenuationDifferenceResult

```python
AttenuationDifferenceResult(
    difference_db: np.ndarray,
    criterion_db: np.ndarray,
    significant: np.ndarray,
    first_mean_db: np.ndarray,
    second_mean_db: np.ndarray,
    first_expanded_uncertainty_db: np.ndarray,
    second_expanded_uncertainty_db: np.ndarray,
    frequencies: np.ndarray,
)
```

Whether two mean attenuations differ significantly, band by band (B.1.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `difference_db` | $\vert m_1 - m_2\vert $ per band, in dB. |
| `criterion_db` | $\sqrt{U_{95,1}^2 + U_{95,2}^2}$ per band, in dB. A difference larger than this is significant at the 5 % level. |
| `significant` | Whether each band's difference exceeds its criterion. |
| `first_mean_db` | $m_1$ per band, in dB. |
| `second_mean_db` | $m_2$ per band, in dB. |
| `first_expanded_uncertainty_db` | $U_{95,1}$ per band, in dB. |
| `second_expanded_uncertainty_db` | $U_{95,2}$ per band, in dB. |
| `frequencies` | The centre frequencies of the test signals, in hertz. |

### AttenuationDifferenceResult.any_significant

*property*

Whether the two measurements differ significantly in any band.

**Returns:** `True` when at least one band's difference exceeds its criterion.

### AttenuationDifferenceResult.plot()

```python
AttenuationDifferenceResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each band's difference against the criterion it has to beat.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the difference bars. |

**Returns:** The axes.

### AttenuationDifferenceResult.significant_frequencies

*property*

The test signals at which the two measurements differ, in hertz.

**Returns:** The centre frequencies of the significant bands.

## check_reat_sound_field

```python
check_reat_sound_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    rotation_levels_db: ArrayLike | None = None,
    free_field_rejection_db: float | None = None,
    frequencies: ArrayLike | None = None,
) -> ReatSoundFieldCheck
```

Is the sound field of the test site diffuse enough? (4.2.2).

Measured with the subject and the chair absent (4.2.1):

- a) the level at each of the six positions 15 cm from the reference point,
  front and back, left and right, up and down, stays within ±2,5 dB of the
  level at the reference point, and the right and left positions within
  3 dB of each other;
- b) from the 500 Hz test signal up, a directional microphone rotated
  through 360° in the horizontal plane at the reference point sees the
  level vary by no more than Table 1 allows for its free-field rejection
  ([`allowable_field_variation`](/phonometry/reference/api/hearing/real-ear-attenuation/#allowable_field_variation)).

The reverberation time of 4.2.3 and the ambient noise of 4.2.4 are
separate requirements of the test site and are not judged here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `position_levels_db` | The level at each position per test signal, in dB, keyed `"front"`, `"back"`, `"left"`, `"right"`, `"up"` and `"down"`. |
| `reference_levels_db` | The level at the reference point per test signal, in dB. |
| `rotation_levels_db` | The levels the directional microphone saw while rotated, a `(readings, bands)` grid in dB, on the same band axis; bands below 500 Hz are not read and may be `nan`. `None` leaves b) unjudged, and the verdict then does not pass. |
| `free_field_rejection_db` | The free-field rejection of that microphone, in dB, required with `rotation_levels_db`. |
| `frequencies` | The centre frequencies, in hertz, or `None` for the test signals of 4.1 as [`real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/#real_ear_attenuation) assumes them. |

**Returns:** [`ReatSoundFieldCheck`](/phonometry/reference/api/hearing/real-ear-attenuation/#reatsoundfieldcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a position is missing or unknown, if the bands do not match, if a rotation is given without its microphone's rejection or the other way round, or if that rejection is below the 10 dB Table 1 accepts. |

## minimum_significant_difference

```python
minimum_significant_difference(
    expanded_uncertainty_db: ArrayLike,
) -> float | np.ndarray
```

The smallest difference between two means that is significant (B.1.1).

For two measurements with the same expanded uncertainty the criterion of
B.1.2 reduces to

$$
\Delta_\mathrm{min} = \frac{2\,U_{95}}{\sqrt{2}} = \sqrt{2}\,U_{95}
$$

and two means that differ by more than that differ significantly at the
95 % confidence level. B.1.1 and B.2 evaluate it on the uncertainty their
tables print rounded to one decimal, and say so: with the 2,3 dB of Table
A.2 it is 3,3 dB, where the unrounded 2,27 dB gives 3,21 dB. Feed this the
value the comparison should rest on.

**Parameters**

| Name | Description |
| :--- | :--- |
| `expanded_uncertainty_db` | $U_{95}$, in dB, a number or an array. |

**Returns:** $\sqrt{2}\,U_{95}$, in dB, a float for a scalar input and an array otherwise.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an uncertainty that is negative or not finite. |

## ProtectorUncertaintyBudget

```python
ProtectorUncertaintyBudget(
    method_db: float,
    equipment_db: float,
    environment_db: float,
)
```

The three standard uncertainties of a hearing protector measurement.

The budget of Table A.1: each component is normally distributed with a
mean of zero and a sensitivity coefficient of 1, so the combined standard
uncertainty is their root sum of squares (Formula (A.2)) and the expanded
one is twice that. ISO 4869-6:2019 Annex A uses the same model for the
active insertion loss of an active noise reduction earmuff.

**Attributes**

| Name | Description |
| :--- | :--- |
| `method_db` | $u_\mathrm{meth}$, the uncertainty of the mean of the individual attenuations of 16 test subjects: subject group, fitting, threshold determination, tester and specimen, in dB. |
| `equipment_db` | $u_\mathrm{eq}$, the uncertainty of the test signal generation equipment, in dB. |
| `environment_db` | $u_\mathrm{env}$, the uncertainty of the deviations from the ideal test environment, in dB. |

### ProtectorUncertaintyBudget.combined_db

*property*

$u = \sqrt{u_\mathrm{meth}^2 + u_\mathrm{eq}^2 + u_\mathrm{env}^2}$, in dB.

**Returns:** The combined standard uncertainty, unrounded.

### ProtectorUncertaintyBudget.expanded_db

*property*

$U_{95} = 2u$, in dB.

**Returns:** The expanded uncertainty for a 95 % coverage, unrounded.

## real_ear_attenuation

```python
real_ear_attenuation(
    attenuation_db: ArrayLike | None = None,
    *,
    open_threshold_db: ArrayLike | None = None,
    occluded_threshold_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> RealEarAttenuationResult
```

The attenuation of a protector, its spread and its uncertainty (4.6, A.2).

Give the individual attenuations, or the two thresholds they come from
(4.6.2):

$$
A_{j,f} = L_{\mathrm{occluded},j,f} - L_{\mathrm{open},j,f}
$$

and this returns, per test signal, the mean, the standard deviation over
the subjects, the standard uncertainty of the mean and the expanded
uncertainty of Annex A:

$$
u = \frac{s}{\sqrt{N}}, \qquad U_{95} = 2u
$$

Everything is computed at full precision; Tables A.3 and B.1 round to one
decimal afterwards, and so should a report. The two thresholds only need
to share a reference: a threshold in sound pressure level and one in
hearing level give the same difference.

**Parameters**

| Name | Description |
| :--- | :--- |
| `attenuation_db` | A `(subjects, bands)` grid of individual attenuations, in dB. |
| `open_threshold_db` | The thresholds of hearing with open ears, a `(subjects, bands)` grid in dB, given together with `occluded_threshold_db` instead of `attenuation_db`. |
| `occluded_threshold_db` | The thresholds with the protector in place, in dB, on the same grid. |
| `frequencies` | The centre frequencies of the test signals, in hertz, or `None` for the seven of 4.1 (125 Hz to 8 kHz) when the grid has seven columns, or those eight with the optional 63 Hz when it has eight. |

**Returns:** [`RealEarAttenuationResult`](/phonometry/reference/api/hearing/real-ear-attenuation/#realearattenuationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if neither form or both are given, if a grid is not two-dimensional or holds fewer than two subjects or a value that is not finite, if the two thresholds differ in shape, or if `frequencies` does not match the grid. |

## RealEarAttenuationResult

```python
RealEarAttenuationResult(
    attenuation_db: np.ndarray,
    mean_db: np.ndarray,
    standard_deviation_db: np.ndarray,
    standard_uncertainty_db: np.ndarray,
    expanded_uncertainty_db: np.ndarray,
    frequencies: np.ndarray,
    subjects: int,
)
```

The attenuation of a hearing protector on a panel of subjects (4.6).

**Attributes**

| Name | Description |
| :--- | :--- |
| `attenuation_db` | The individual attenuations $A_{j,f}$, one row per subject and one column per test signal, in dB. This is the grid [`phonometry.hearing.assumed_protection_value`](/phonometry/reference/api/hearing/hearing-protectors/#assumed_protection_value), [`phonometry.hearing.hml_rating`](/phonometry/reference/api/hearing/hearing-protectors/#hml_rating) and [`phonometry.hearing.snr_rating`](/phonometry/reference/api/hearing/hearing-protectors/#snr_rating) take, unchanged. |
| `mean_db` | The mean attenuation $m$ per test signal, in dB. |
| `standard_deviation_db` | The standard deviation $s$ per test signal over the subjects, the sample one over $N - 1$, in dB. |
| `standard_uncertainty_db` | $u = s/\sqrt{N}$, the standard deviation of the mean (A.2), in dB. |
| `expanded_uncertainty_db` | $U_{95} = 2u$ (A.1), in dB. |
| `frequencies` | The centre frequencies of the test signals, in hertz. |
| `subjects` | The number of test subjects $N$. |

### RealEarAttenuationResult.plot()

```python
RealEarAttenuationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the mean attenuation the way Clause 6 l) asks for it.

Increasing attenuation points downwards and, on a figure this creates,
50 dB on the vertical axis spans one decade on the horizontal one
(IEC 60263). The individual attenuations are drawn faint behind the
mean, and the expanded uncertainty as bars on it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mean curve. |

**Returns:** The axes.

## REAT_BETWEEN_LABORATORY_UNCERTAINTY

*Constant* (`mapping`).

```python
REAT_BETWEEN_LABORATORY_UNCERTAINTY = {'earplug': {'below 250 Hz': ProtectorUncertaintyBudget(method_db=4.0, equipment_db=0.3, environment_db=0.8), '250 Hz up to 4 kHz': ProtectorUncertaintyBudget(method_db=3.2, equipment_db=0.3, environment_db=0.8), 'above 4 kHz': ProtectorUncertaintyBudget(method_db=3.2, equipment_db=0.3, environment_db=0.8)}, 'earmuff': {'below 250 Hz': ProtectorUncertaintyBudget(method_db=1.8, equipment_db=0.3, environment_db=0.8), '250 Hz up to 4 kHz': ProtectorUncertaintyBudget(method_db=2.3, equipment_db=0.3, environment_db=0.8), 'above 4 kHz': ProtectorUncertaintyBudget(method_db=3.2, equipment_db=0.3, environment_db=0.8)}}
```

## reat_expanded_uncertainty

```python
reat_expanded_uncertainty(
    frequencies: ArrayLike,
    *,
    protector: str,
    between_laboratories: bool = False,
) -> np.ndarray
```

The typical $U_{95}$ of a mean attenuation, band by band (A.2, B.2).

Reads the budget of Table A.2 (within one laboratory) or Table B.2
(between laboratories) for the protector type and the frequency range each
test signal falls in, and returns its expanded uncertainty at full
precision. These are the typical values B.1.1 and B.2 draw on when no data
of a specific measurement are at hand; the text of both uses them rounded
to one decimal, as the tables print them (see
[`minimum_significant_difference`](/phonometry/reference/api/hearing/real-ear-attenuation/#minimum_significant_difference)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | The centre frequencies of the test signals, in hertz. |
| `protector` | `"earplug"` or `"earmuff"`. |
| `between_laboratories` | `False` (default) for Table A.2, `True` for Table B.2. |

**Returns:** $U_{95}$ per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a protector type the tables do not list, or for frequencies that are not positive and finite. |

## REAT_FIELD_VARIATION_LIMITS

*Constant* (`tuple`).

```python
REAT_FIELD_VARIATION_LIMITS = ((25.0, 20.0), (20.0, 15.0), (15.0, 10.0), (10.0, 5.0))
```

## REAT_FREQUENCY_RANGES

*Constant* (`tuple`).

```python
REAT_FREQUENCY_RANGES = ('below 250 Hz', '250 Hz up to 4 kHz', 'above 4 kHz')
```

## REAT_WITHIN_LABORATORY_UNCERTAINTY

*Constant* (`mapping`).

```python
REAT_WITHIN_LABORATORY_UNCERTAINTY = {'earplug': {'below 250 Hz': ProtectorUncertaintyBudget(method_db=1.5, equipment_db=0.2, environment_db=0.5), '250 Hz up to 4 kHz': ProtectorUncertaintyBudget(method_db=1.0, equipment_db=0.2, environment_db=0.5), 'above 4 kHz': ProtectorUncertaintyBudget(method_db=1.5, equipment_db=0.2, environment_db=0.5)}, 'earmuff': {'below 250 Hz': ProtectorUncertaintyBudget(method_db=1.0, equipment_db=0.2, environment_db=0.5), '250 Hz up to 4 kHz': ProtectorUncertaintyBudget(method_db=0.6, equipment_db=0.2, environment_db=0.5), 'above 4 kHz': ProtectorUncertaintyBudget(method_db=1.0, equipment_db=0.2, environment_db=0.5)}}
```

## ReatSoundFieldCheck

```python
ReatSoundFieldCheck(
    frequencies: np.ndarray,
    position_deviation_db: np.ndarray,
    left_right_difference_db: np.ndarray,
    rotation_variation_db: np.ndarray,
    allowable_variation_db: float | None,
    positions: tuple[str, ...] = ('front', 'back', 'left', 'right', 'up', 'down'),
)
```

Whether the test site's sound field qualifies for ISO 4869-1 (4.2.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The centre frequencies of the test signals, in hertz. |
| `position_deviation_db` | The level at each of the six positions 15 cm from the reference point less the level at it, one row per position in the order of `positions`, in dB. |
| `left_right_difference_db` | The difference between the right and left positions per band, as an absolute value, in dB. |
| `rotation_variation_db` | The spread of the levels a rotated directional microphone saw per band, in dB, or `nan` where 4.2.2 b) does not apply (below 500 Hz) or no rotation was given. |
| `allowable_variation_db` | What Table 1 allows that spread, in dB, or `None` when no rotation was given. |
| `positions` | The position names, in row order. |

4.2.2 b) is a requirement of the clause, not an option: a check made
without the rotation leaves it unjudged whenever a band reaches 500 Hz,
`directionality_judged` says so, and `passes` is `False`
until it is judged. `uniform` and `balanced` still give the
verdict of a) on its own.

### ReatSoundFieldCheck.balanced

*property*

Per band, whether right and left differ by 3 dB at most (4.2.2 a)).

**Returns:** One boolean per band.

### ReatSoundFieldCheck.diffuse

*property*

Per band, whether the rotation stays within Table 1 (4.2.2 b)).

Bands the clause does not reach, below 500 Hz, count as meeting it.
With no rotation given nothing was measured, every band reads
`True` here and `directionality_judged` is `False`.

**Returns:** One boolean per band.

### ReatSoundFieldCheck.directionality_judged

*property*

Whether 4.2.2 b) was judged.

**Returns:** `True` when a rotation was given, or when no test signal reaches the 500 Hz from which b) applies.

### ReatSoundFieldCheck.passes

*property*

Whether the sound field qualifies for 4.2.2, a) and b) both judged.

**Returns:** `True` when every band meets a) and b); `False` when a band fails either, or when b) was not judged.

### ReatSoundFieldCheck.plot()

```python
ReatSoundFieldCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each condition of 4.2.2 against its limit, band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the worst position deviation curve. |

**Returns:** The axes.

### ReatSoundFieldCheck.uniform

*property*

Per band, whether all six positions stay within ±2,5 dB (4.2.2 a)).

**Returns:** One boolean per band.
