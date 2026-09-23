---
title: "hearing.active_noise_reduction"
description: "Total attenuation of an active noise reduction earmuff (ISO 4869-6:2019)."
sidebar:
  label: "active_noise_reduction"
---

Total attenuation of an active noise reduction earmuff (ISO 4869-6:2019).

An active noise reduction (ANR) earmuff adds a cancellation circuit to a
passive one, and the circuit works mostly at low frequencies, where the
passive shell is weakest. ISO 4869-1 cannot measure it: a threshold test runs
at levels far below those at which the circuit has anything to cancel. So
ISO 4869-6 measures the two halves separately and adds them subject by
subject:

- the **passive** attenuation, the real-ear attenuation at threshold of
  ISO 4869-1 with the circuit off, in octave bands
  ([`real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/));
- the **active insertion loss** (3.4), measured with a microphone in each
  closed ear canal (MIRE, ISO 11904-1) as the difference between the level at
  the ear in the passive and in the active mode, in one-third-octave bands of a
  broadband noise at 85 dB to 95 dB (5.4.3):

  $$
  \alpha_{j,e,f} = L_{\mathrm{passive},j,e,f} - L_{\mathrm{active},j,e,f}
  $$

**The chain of 5.5.** For each subject:

a) the passive attenuation is interpolated linearly into the one-third-octave
   bands between 63 Hz (or 125 Hz) and 8 kHz, and extrapolated to 50 Hz (or
   100 Hz) and 10 kHz;
b) in each one-third-octave band, only the ear with the **lower** active
   insertion loss is kept;
c) the two are added, $A_{\mathrm{total},f,j}$;
d) each octave band is the energetic average of its three one-third-octave
   bands (Formula (1)):

   $$
   A_{\mathrm{total,oct},j} = -10 \lg \left[\left( 10^{-0,1 A_{\mathrm{total},f_1,j}} + 10^{-0,1 A_{\mathrm{total},f_2,j}} + 10^{-0,1 A_{\mathrm{total},f_3,j}}\right) / 3\right] \mathrm{dB} \tag{1}
   $$

e) the sixteen octave-band data sets go into ISO 4869-2 at a protection
   performance of 84 %: the mean, the standard deviation, the APV, the H, M
   and L values and the SNR.

[`anr_total_attenuation`](/phonometry/reference/api/hearing/active-noise-reduction/#anr_total_attenuation) runs the whole chain. Clause 5.5 says the
detailed computations are given in the calculation example ISO publishes with
the standard, and that workbook interpolates **linearly in frequency, in
hertz**, between the nominal centre frequencies, not on a logarithmic axis:
80 Hz sits 27 % of the way from 63 Hz to 125 Hz, not a third of it. This
follows the workbook. The workbook also rounds each interpolated value and
each octave result to 0,1 dB, and the mean and standard deviation before it
forms the APV; this computes at full precision throughout, which moves an
octave-band total by less than 0,1 dB.

**The uncertainty (Annex A).** Formula (A.1) is the model of ISO 4869-1
applied to the active insertion loss, and within one laboratory the combined
standard uncertainty is again the standard deviation of the mean over the
sixteen lower-ear values, $u = s/\sqrt{N}$ and $U_{95} = 2u$, which
[`active_insertion_loss`](/phonometry/reference/api/hearing/active-noise-reduction/#active_insertion_loss) returns. Table A.2 prints a typical budget,
[`ANR_WITHIN_LABORATORY_UNCERTAINTY`](/phonometry/reference/api/hearing/active-noise-reduction/#anr_within_laboratory_uncertainty).

**Linear operation (5.4.4).** A cancellation circuit saturates, so the active
insertion loss only holds up to some external level. With red noise, the level
at each ear in the 125 Hz octave band is followed while the external level
rises in 5 dB steps from the level of the insertion-loss measurement to at
most 110 dB, and each step at the ear shall also be 5 dB, within ±1 dB.
[`assess_anr_linearity`](/phonometry/reference/api/hearing/active-noise-reduction/#assess_anr_linearity) finds the highest external level up to which that
holds for every sample, subject and ear, which is what 5.6 i) reports.

Clause, formula and table numbers refer to ISO 4869-6:2019(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## active_insertion_loss

```python
active_insertion_loss(
    insertion_loss_db: ArrayLike | None = None,
    *,
    passive_levels_db: ArrayLike | None = None,
    active_levels_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> ActiveInsertionLossResult
```

The active insertion loss, its lower ear and its uncertainty (5.4, 5.5 b), A.2).

Give the levels at the ears in the two modes, both `(subjects, 2,
bands)` grids with the left ear first, and the insertion loss of each ear
is their difference (5.4.1):

$$
\alpha_{j,e,f} = L_{\mathrm{passive},j,e,f} - L_{\mathrm{active},j,e,f}
$$

or give the insertion loss directly, per ear on the same grid or already
reduced to one value per subject and band. Per subject and band only the
ear with the lower value is kept (5.5 b)), and over those the mean, the
standard deviation and the uncertainty of the mean of Annex A are formed:

$$
u = \frac{s}{\sqrt{N}}, \qquad U_{95} = 2u
$$

A negative value is a band in which the circuit adds sound, which ANR
earmuffs commonly do above 1 kHz; it is kept as it is.

**Parameters**

| Name | Description |
| :--- | :--- |
| `insertion_loss_db` | The active insertion loss in dB, a `(subjects, 2, bands)` grid per ear or a `(subjects, bands)` grid of the lower ear. |
| `passive_levels_db` | The MIRE levels in the passive mode, a `(subjects, 2, bands)` grid in dB, given together with `active_levels_db` instead of `insertion_loss_db`. |
| `active_levels_db` | The MIRE levels in the active mode, on the same grid. |
| `frequencies` | The centre frequencies in hertz, or `None` for the one-third-octave bands 50 Hz to 10 kHz (24 bands) or 100 Hz to 10 kHz (21), or the octave bands 63 Hz to 8 kHz (8) or 125 Hz to 8 kHz (7), by the number of bands. |

**Returns:** [`ActiveInsertionLossResult`](/phonometry/reference/api/hearing/active-noise-reduction/#activeinsertionlossresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if neither form or both are given, if a grid has the wrong shape, fewer than two subjects or a value that is not finite, if the two level grids differ in shape, or if `frequencies` does not match. |

## ActiveInsertionLossResult

```python
ActiveInsertionLossResult(
    insertion_loss_db: np.ndarray,
    per_ear_db: np.ndarray | None,
    mean_db: np.ndarray,
    standard_deviation_db: np.ndarray,
    standard_uncertainty_db: np.ndarray,
    expanded_uncertainty_db: np.ndarray,
    frequencies: np.ndarray,
    subjects: int,
)
```

The active insertion loss of an ANR earmuff on a panel of subjects.

**Attributes**

| Name | Description |
| :--- | :--- |
| `insertion_loss_db` | $\alpha$ per subject and band, the ear with the lower value in each band (5.5 b)), in dB. |
| `per_ear_db` | The value of each ear, a `(subjects, 2, bands)` grid with the left ear first, in dB, or `None` when only the lower-ear values were given. |
| `mean_db` | The mean over the subjects per band, in dB. |
| `standard_deviation_db` | The sample standard deviation per band, in dB. |
| `standard_uncertainty_db` | $u = s/\sqrt{N}$ (A.2), in dB. |
| `expanded_uncertainty_db` | $U_{95} = 2u$ (A.1), in dB. |
| `frequencies` | The centre frequencies of the bands, in hertz. |
| `subjects` | The number of test subjects $N$. |

### ActiveInsertionLossResult.plot()

```python
ActiveInsertionLossResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the mean active insertion loss with its expanded uncertainty.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mean curve. |

**Returns:** The axes.

## anr_total_attenuation

```python
anr_total_attenuation(
    reat: ArrayLike | RealEarAttenuationResult,
    insertion_loss: ArrayLike | ActiveInsertionLossResult,
) -> AnrTotalAttenuationResult
```

The total attenuation of an ANR earmuff, subject by subject (5.5).

Runs 5.5 a) to e): the passive attenuation of ISO 4869-1 is interpolated
into one-third-octave bands, linearly in hertz and extended at both ends;
the lower-ear active insertion loss is added to it; each octave band is
the energetic average of its three one-third-octave bands,

$$
A_{\mathrm{total,oct},j} = -10 \lg \left[\left( \sum_{i=1}^{3} 10^{-0,1 A_{\mathrm{total},f_i,j}}\right) / 3\right] \mathrm{dB} \tag{1}
$$

and the octave-band totals of all subjects go into ISO 4869-2 at 84 %. The
same subjects are measured passively and actively (5.4.3), so the two
inputs must have the same subjects, in the same order.

The passive attenuation from 63 Hz needs the active insertion loss from
50 Hz; from 125 Hz, it needs it from 100 Hz. An insertion loss that starts
at 100 Hz can only give the total from 125 Hz (5.3.1); a passive
attenuation from 63 Hz then still places the 100 Hz band, by interpolation.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reat` | The passive attenuation, a [`RealEarAttenuationResult`](/phonometry/reference/api/hearing/real-ear-attenuation/#realearattenuationresult) or its `(subjects, octaves)` grid in dB on the octave bands 63 Hz or 125 Hz to 8 kHz. |
| `insertion_loss` | The active insertion loss, an [`ActiveInsertionLossResult`](/phonometry/reference/api/hearing/active-noise-reduction/#activeinsertionlossresult) or a grid [`active_insertion_loss`](/phonometry/reference/api/hearing/active-noise-reduction/#active_insertion_loss) accepts, on the one-third-octave bands of 5.3.1. |

**Returns:** [`AnrTotalAttenuationResult`](/phonometry/reference/api/hearing/active-noise-reduction/#anrtotalattenuationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the passive attenuation is not on the octave bands of ISO 4869-1, if the insertion loss does not reach the bands it needs, or if the two do not have the same number of subjects. |

## ANR_WITHIN_LABORATORY_UNCERTAINTY

*Constant* (`phonometry.hearing.real_ear_attenuation.ProtectorUncertaintyBudget`).

## AnrLinearityResult

```python
AnrLinearityResult(
    external_levels_db: np.ndarray,
    ear_levels_db: np.ndarray,
    increments_db: np.ndarray,
)
```

How far up an ANR earmuff stays linear (5.4.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `external_levels_db` | The external A-weighted levels applied, in dB, in 5 dB steps. |
| `ear_levels_db` | The 125 Hz octave-band level at the ear, one row per sample, subject and ear, one column per external level, in dB. |
| `increments_db` | The step at the ear for each step outside, in dB. |

### AnrLinearityResult.linear

*property*

Per ear and step, whether the step at the ear is 5 dB ± 1 dB.

**Returns:** A `(ears, steps)` boolean grid.

### AnrLinearityResult.linear_to_110_db

*property*

Whether it stayed linear up to 110 dB, which 5.6 i) then states.

**Returns:** `True` when every step is linear and the last external level is 110 dB.

### AnrLinearityResult.maximum_linear_level_db

*property*

The highest external level up to which every ear stayed linear, in dB.

Read from `linear`, the same judgement `passes` makes: the
level before the first step at which any ear leaves 5 dB ± 1 dB, or
the last level applied when none does. The lowest level applied when
the first step already fails.

**Returns:** The level 5.6 i) reports, in dB.

### AnrLinearityResult.passes

*property*

Whether every step at every ear stayed linear.

**Returns:** `True` when the earmuff is linear over the whole range tested.

### AnrLinearityResult.plot()

```python
AnrLinearityResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every step at the ear against the 5 dB ± 1 dB it should be.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the median step curve. |

**Returns:** The axes.

## AnrTotalAttenuationResult

```python
AnrTotalAttenuationResult(
    total_octave_db: np.ndarray,
    total_third_octave_db: np.ndarray,
    reat_third_octave_db: np.ndarray,
    insertion_loss_db: np.ndarray,
    frequencies: np.ndarray,
    third_octave_frequencies: np.ndarray,
    assumed_protection: AssumedProtectionResult,
    hml: HMLRatingResult,
    snr: SNRRatingResult,
)
```

The total attenuation of an ANR earmuff and its ISO 4869-2 ratings (5.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `total_octave_db` | $A_{\mathrm{total,oct},j}$ per subject and octave band, Formula (1), in dB. This is the grid of 5.5 e). |
| `total_third_octave_db` | $A_{\mathrm{total},f,j}$ per subject and one-third-octave band, 5.5 c), in dB. |
| `reat_third_octave_db` | The passive attenuation interpolated and extrapolated into the one-third-octave bands, 5.5 a), in dB. |
| `insertion_loss_db` | The lower-ear active insertion loss in the same bands, 5.5 b), in dB. |
| `frequencies` | The octave bands, in hertz. |
| `third_octave_frequencies` | The one-third-octave bands, in hertz. |
| `assumed_protection` | Mean, standard deviation and APV at 84 %. |
| `hml` | The H, M and L values at 84 %. |
| `snr` | The SNR at 84 %. |

### AnrTotalAttenuationResult.plot()

```python
AnrTotalAttenuationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the passive, active and total attenuation and the APV.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mean total attenuation curve. |

**Returns:** The axes.

## assess_anr_linearity

```python
assess_anr_linearity(
    external_levels_db: ArrayLike,
    ear_levels_db: ArrayLike | None = None,
    *,
    ear_third_octave_levels_db: ArrayLike | None = None,
) -> AnrLinearityResult
```

Up to what external level does the earmuff stay linear? (5.4.4).

With red noise (5.3.2) and the circuit on, the external A-weighted level
starts at the level of the insertion-loss measurement and rises in 5 dB
steps to at most 110 dB. At each ear the level in the 125 Hz octave band,
the energy sum of the 100 Hz, 125 Hz and 160 Hz one-third-octave bands,
shall rise by the same 5 dB, within ±1 dB. The highest external level up
to which that holds for every sample and subject is what 5.6 i) reports,
and if it holds up to 110 dB, that is stated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `external_levels_db` | The external A-weighted levels applied, in dB, in increasing 5 dB steps up to 110 dB. |
| `ear_levels_db` | The 125 Hz octave-band level at the ear, in dB, with the external levels on the last axis and any number of leading axes (sample, subject, ear). |
| `ear_third_octave_levels_db` | Instead, the 100 Hz, 125 Hz and 160 Hz one-third-octave levels at the ear, with those three on the last axis and the external levels on the one before. |

**Returns:** [`AnrLinearityResult`](/phonometry/reference/api/hearing/active-noise-reduction/#anrlinearityresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the external levels are not 5 dB steps, if they pass 110 dB, if neither or both of the ear-level forms are given, or if the shapes do not match. |
