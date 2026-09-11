---
title: "vibration.immission.railway_prediction"
description: "Predicting railway vibration from third-octave spectra (E DIN 45672-3:2023-02)."
sidebar:
  label: "railway_prediction"
---

Predicting railway vibration from third-octave spectra (E DIN 45672-3:2023-02).

Part 3 of DIN 45672 has never been published; the draft of February 2023 is
the only text of it, and it is the prediction method that E DIN 4150-2:2023-08
refers a planning approval to. Where Part 1 measures next to a line and Part 2
reduces what was measured, Part 3 says what a building that does not exist
yet, next to a line that does not exist yet, is going to feel: a third-octave
velocity spectrum on a floor, and from it the assessment quantities of
DIN 4150-2.

**The chain** (Clause 5.1, Formula (1)). The predicted spectrum on a floor is
an emission spectrum plus four level differences, band by band from 4 Hz to
250 Hz:

$$
L_v(f_{Tn}) = L_{v,E}(f_{Tn}) + \Delta L_{v,BB}(f_{Tn}) + \Delta L_{v,FB}(f_{Tn}) + \Delta L_{v,DF}(f_{Tn}) + D_e(f_{Tn})
$$

the emission $L_{v,E}$ as a Max Hold spectrum of the Zuggattung at a
known distance (Clause 5.2), the transmission $\Delta L_{v,BB}$ through
the ground to the building (Clause 5.3), the transfer $\Delta L_{v,FB}$
from the ground into the foundation and $\Delta L_{v,DF}$ from the
foundation to the floor (Clause 5.4), and the insertion loss $D_e$ of
whatever mitigation is planned (Clause 5.5). Every term is added as printed,
so a mitigation enters as a negative number.

**Emission** (Clause 5.2). A measured spectrum is carried to another speed of
the same category by $20 \lg(v_2/v_1)$ (Formula (3)), for a change of
speed of up to 30 %; beyond that the sleeper-passing frequency moves and the
spectrum with it.

**Transmission** (Clause 5.3). The ratio of the velocities at the distance
$r$ and at the reference distance $r_0$ is geometric spreading
times material damping (Formula (5)), $(r/r_0)^{-n} e^{-\alpha_R (r - r_0)}$ with $\alpha_R = 2\pi f D / c_s$, or a power law with an exponent
measured per band (Formula (6)); the level difference is 20 lg of it
(Formula (4)). On the surface the exponent is usually 0,2 to 0,4.

**Building** (Clause 5.4, Annex A). Six tables of level differences from
extensive building measurements: ground to floor for concrete and for timber
floors by the natural frequency of the floor (Tables A.1 and A.2), ground to
foundation for a basement and for a ground floor with a mean and a
deviation either way (Tables A.3 and A.4), and foundation to floor against
the ratio of the band to the natural frequency of the floor (Tables A.5 and
A.6). The prediction is run once per natural frequency the building may
have, never with the envelope over all of them.

**Assessment quantities** (Clause 7). The KB weighting of DIN 45669-1 as a
table of third-octave corrections (Table 2, Formula (8)) is added to the
predicted spectrum, the bands from 4 Hz to 80 Hz are summed, and the sum
level gives the clock maximum r.m.s. of the category (Formula (9)),
$KB_{FTm,Zug} = c_{T1} v_0 10^{L/20}$ with $c_{T1} = 1$ and
$v_0 = 5 \cdot 10^{-5}$ mm/s; 1,5 times it is $KB_{F\mathrm{max},Zug}$
(Formula (10)), three times that the peak velocity a DIN 4150-3 comparison
wants (Formula (12)), and Formula (11) is the sum of Formula (6) of E DIN
4150-2:2023-08, printed without that formula's rule that a category whose
$KB_{FTm,Zug}$ is at or below 0,1 enters as zero; the assessment the
draft says it performs is that of DIN 4150-2, so
[`train_assessment_severity`](/phonometry/reference/api/vibration/train-categories/#train_assessment_severity) of
[`phonometry.vibration.immission.train_categories`](/phonometry/reference/api/vibration/train-categories/), which applies the
rule, is what the chain ends in. Formula (13) turns a level spectrum back
into a velocity spectrum in micrometres per second, for the VC curves.

**A point source and a train** (Annex B). A train is a line of point sources
until the distance $R_0 \approx L^2/\lambda$ (Formula (B.1)) and a point
source beyond it, so a decay measured with a point excitation is made
shallower by 0,3 or 0,5 in the exponent up to $R_0$ (Formula (B.2)).

**What is not here.** Clause 6, the phases of a prediction, and Annex D are
work plans. The worked example of Annex C prints its emission and building
terms as inputs: its sum, its chain to a peak velocity and the arithmetic of
Formula (11) are conformance rows, and where the print does not reproduce
itself the entry is in `docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## FLOOR_NATURAL_FREQUENCIES_HZ

*Constant* (`tuple`).

```python
FLOOR_NATURAL_FREQUENCIES_HZ = (8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0)
```

## FOUNDATION_TO_FLOOR_DB

*Constant* (`dict`).

```python
FOUNDATION_TO_FLOOR_DB = {'concrete': {'lower': (-1.52, -1.53, -1.74, -2.42, -2.63, -1.89, -1.81, -1.73, -1.27, -0.72, 0.02, 1.43, 6.05, 9.78, 4.52, 0.12, -3.27, -4.14, -5.29, -1.96, -1.38, nan, nan), 'mean': (0.29, 0.93, 0.72, 1.09, 0.98, 1.62, 1.6, 2.06, 2.52, 3.26, 4.19, 6.35, 9.94, 17.26, 9.85, 4.41, 3.27, 3.25, 1.42, 3.89, 2.83, nan, nan), 'upper': (2.37, 4.16, 3.85, 5.17, 5.15, 5.51, 5.49, 6.42, 6.88, 7.24, 8.74, 11.76, 17.46, 24.23, 17.07, 11.11, 10.23, 10.21, 8.38, 10.25, 7.9, nan, nan)}, 'timber': {'lower': (nan, nan, 0.64, 1.05, 0.52, 1.87, 2.37, 2.45, 2.6, 2.76, 3.43, 5.98, 8.62, 15.29, 9.88, 6.26, 5.13, 5.28, 5.26, 5.42, 7.63, nan, nan), 'mean': (nan, nan, nan, nan, 3.14, 3.06, 2.19, 4.87, 6.55, 7.74, 8.29, 10.47, 17.4, 21.93, 14.81, 11.54, 9.54, 5.4, 3.55, 3.24, 3.01, 3.35, 1.85), 'upper': (nan, nan, nan, nan, nan, nan, nan, 8.1, 11.09, 14.84, 15.68, 16.61, 23.36, 28.84, 22.39, 18.26, 15.24, 14.03, 10.07, 6.88, 5.4, nan, nan)}}
```

## FOUNDATION_TO_FLOOR_RATIOS

*Constant* (`tuple`).

```python
FOUNDATION_TO_FLOOR_RATIOS = (0.05, 0.063, 0.08, 0.1, 0.125, 0.16, 0.2, 0.25, 0.315, 0.4, 0.5, 0.63, 0.8, 1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0)
```

## foundation_to_floor_transfer_db

```python
foundation_to_floor_transfer_db(
    frequencies_hz: ArrayLike,
    *,
    floor: str,
    floor_natural_frequency_hz: float,
    statistic: str = 'mean',
) -> NDArray[np.float64]
```

The level difference from the foundation to a floor, Tables A.5 and A.6.

$\Delta L_{v,DF}$ against the ratio of the band to the natural
frequency of the floor, for concrete or for timber floors, as the mean
or the mean less or plus its deviation. The tables are read at the ratio
of each band; a ratio between two tabulated ones is interpolated
linearly in decibels over the logarithm of the ratio, and a ratio the
table has no value for gives `nan`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres, in hertz. |
| `floor` | `"concrete"` or `"timber"`. |
| `floor_natural_frequency_hz` | $f_e$, positive. |
| `statistic` | `"mean"` (default), `"lower"` or `"upper"`. |

**Returns:** $\Delta L_{v,DF}$, in decibels, one per band, `nan` outside the table.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown floor or statistic, a non-positive frequency, or a non-finite input. |

## GEOMETRIC_DECAY_EXPONENT_RANGE

*Constant* (`tuple`).

```python
GEOMETRIC_DECAY_EXPONENT_RANGE = (0.2, 0.4)
```

## ground_attenuation_coefficient_per_m

```python
ground_attenuation_coefficient_per_m(
    frequencies_hz: ArrayLike,
    *,
    damping_ratio: float,
    shear_wave_speed_m_s: float,
) -> NDArray[np.float64]
```

The material damping of the ground, $\alpha_R$ of Clause 5.3.

$\alpha_R(f) = 2\pi D / \lambda_R = 2\pi f D / c_s$: the damping
ratio of the ground over the wavelength, which the standard writes with
the shear wave speed although the wave is the surface wave, and that is
how it is computed here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres, in hertz. |
| `damping_ratio` | $D$, the damping ratio of the ground. |
| `shear_wave_speed_m_s` | $c_s$, in metres per second. |

**Returns:** $\alpha_R$, in reciprocal metres, one per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative damping ratio, a non-positive speed or a non-positive frequency. |

## GROUND_TO_FLOOR_DB

*Constant* (`dict`).

## ground_to_floor_transfer_db

```python
ground_to_floor_transfer_db(
    floor: str,
    *,
    floor_natural_frequency_hz: float,
) -> NDArray[np.float64]
```

The level difference from the ground to a floor, Tables A.1 and A.2.

$\Delta L_{v,DB}$ for a building with concrete or with timber floors
whose floors have the given natural frequency, along
[`PREDICTION_BAND_CENTRES_HZ`](/phonometry/reference/api/vibration/railway-prediction/#prediction_band_centres_hz), for any storey. The tables print a
column for each of [`FLOOR_NATURAL_FREQUENCIES_HZ`](/phonometry/reference/api/vibration/railway-prediction/#floor_natural_frequencies_hz) and no rule for
a frequency between two, so the frequency has to be one of them. Clause
5.4.4: run the prediction once for each natural frequency the building
may have, and never with the envelope over all of them, which
overestimates considerably.

**Parameters**

| Name | Description |
| :--- | :--- |
| `floor` | `"concrete"` or `"timber"`. |
| `floor_natural_frequency_hz` | $f_e$, one of the tabulated frequencies. |

**Returns:** $\Delta L_{v,DB}$, in decibels, one per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown floor or a frequency the tables have no column for. |

## GROUND_TO_FOUNDATION_DB

*Constant* (`dict`).

```python
GROUND_TO_FOUNDATION_DB = {'basement': {'lower': (-9.1, -8.2, -8.3, -8.7, -8.2, -8.3, -9.5, -12.5, -14.7, -15.6, -14.5, -13.1, -12.4, -11.6), 'mean': (-4.0, -3.5, -3.6, -4.2, -4.2, -3.8, -4.6, -6.0, -8.2, -9.3, -7.4, -5.1, -4.4, -4.2), 'upper': (1.0, 1.5, 1.1, 0.3, 0.1, 0.4, 0.3, -0.4, -2.1, -2.7, -0.1, 3.0, 3.4, 3.1)}, 'ground_floor': {'lower': (-8.3, -7.0, -7.5, -6.4, -4.6, -4.3, -6.3, -7.0, -9.1, -10.7, -11.3, -10.0, -11.2, -9.8), 'mean': (-3.2, -3.0, -3.9, -3.0, -2.2, -1.9, -3.1, -4.2, -5.8, -6.4, -5.7, -4.9, -5.3, -4.7), 'upper': (1.7, 1.1, 0.0, 0.3, -0.5, 0.4, -0.4, -1.4, -1.8, -2.5, -0.7, 0.3, 0.4, 0.8)}}
```

## ground_to_foundation_transfer_db

```python
ground_to_foundation_transfer_db(
    level: str,
    *,
    statistic: str = 'mean',
) -> NDArray[np.float64]
```

The level difference from the ground into the foundation, Tables A.3 and A.4.

$\Delta L_{v,FB}$ for a basement or for a foundation at ground
level, along the 14 bands from 4 Hz to 80 Hz, as the mean of the
buildings measured or the mean less or plus its deviation. The tables
stop at 80 Hz where the others run to 250 Hz, so the result enters
[`predict_floor_spectrum`](/phonometry/reference/api/vibration/railway-prediction/#predict_floor_spectrum) only with an emission spectrum cut to the
same 14 bands, or padded with zeros above them by the caller.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level` | `"basement"` or `"ground_floor"`. |
| `statistic` | `"mean"` (default), `"lower"` or `"upper"`. |

**Returns:** $\Delta L_{v,FB}$, in decibels, one per band from 4 Hz to 80 Hz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown level or statistic. |

## ground_transmission_db

```python
ground_transmission_db(
    frequencies_hz: ArrayLike,
    *,
    distance_m: float,
    reference_distance_m: float,
    exponent: ArrayLike,
    damping_ratio: float | None = None,
    shear_wave_speed_m_s: float | None = None,
) -> NDArray[np.float64]
```

The transmission through the ground, Formulae (4) to (6).

Formula (5) gives the ratio of the velocity at $r$ to that at
$r_0$ as $(r/r_0)^{-n} e^{-\alpha_R(f)(r - r_0)}$, geometric
spreading with the exponent $n$ and material damping with
$\alpha_R$ of [`ground_attenuation_coefficient_per_m`](/phonometry/reference/api/vibration/railway-prediction/#ground_attenuation_coefficient_per_m), and
Formula (4) takes 20 lg of it. With the damping left out and an
exponent per band it is Formula (6), the power law with the exponent
measured on site for every band. On the surface the standard usually
takes $n$ between 0,2 and 0,4, frequency-independent; a train is a
line of point sources, and Annex B says what to take off an exponent
measured with a point excitation.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres, in hertz. |
| `distance_m` | $r$, from the source to the ground in front of the building or to its foundation. |
| `reference_distance_m` | $r_0$, where the emission spectrum was taken. |
| `exponent` | $n$, one value or one per band. |
| `damping_ratio` | $D$ of the ground; `None` (default) leaves the material damping out. |
| `shear_wave_speed_m_s` | $c_s$, needed with a damping ratio. |

**Returns:** $\Delta L_{v,BB}$, in decibels, one per band; negative where the building is further from the source than the reference.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive distance, a negative exponent or damping, a damping ratio without a wave speed, or an exponent that does not broadcast to the bands. |

## KB_ASSESSMENT_BANDS_HZ

*Constant* (`tuple`).

```python
KB_ASSESSMENT_BANDS_HZ = (4.0, 80.0)
```

## kb_weighted_levels_db

```python
kb_weighted_levels_db(
    levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

The KB-weighted third-octave levels, Formula (8) with Table 2.

$L_{v,KB}(f_{Tn}) = L_v(f_{Tn}) + L_{KB}(f_{Tn})$: the correction of
Table 2, the KB weighting of DIN 45669-1 rounded to a tenth of a
decibel, added to each band from 4 Hz to 80 Hz. Bands outside those are
not weighted by the table and are refused.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_v$, one level per band, in decibels. |
| `frequencies_hz` | The band centres, nominal, 4 Hz to 80 Hz. |

**Returns:** $L_{v,KB}$, one per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a band outside Table 2, or mismatched inputs. |

## KB_WEIGHTING_TABLE_DB

*Constant* (`dict`).

```python
KB_WEIGHTING_TABLE_DB = {4.0: -4.7, 5.0: -3.5, 6.3: -2.5, 8.0: -1.7, 10.0: -1.2, 12.5: -0.8, 16.0: -0.5, 20.0: -0.3, 25.0: -0.2, 31.5: -0.1, 40.0: -0.1, 50.0: -0.1, 63.0: 0.0, 80.0: 0.0}
```

## line_source_correction_db

```python
line_source_correction_db(
    distance_m: float,
    *,
    reference_distance_m: float,
    exponent_correction: float,
) -> float
```

The correction of a point-source decay to a train, Formula (B.2).

$\Delta L_{v,Korr} = 20 \, n_{Korr} \lg(r / r_0)$, added to the level
a point excitation predicts, with $n_{Korr}$ between 0,3 and 0,5:
the train spreads less than the point did, up to the distance of
Formula (B.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | $r$, in metres. |
| `reference_distance_m` | $r_0$, in metres. |
| `exponent_correction` | $n_{Korr}$, 0,3 to 0,5. |

**Returns:** $\Delta L_{v,Korr}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive distance or a correction outside 0,3 to 0,5. |

## LINE_SOURCE_EXPONENT_CORRECTION

*Constant* (`dict`).

```python
LINE_SOURCE_EXPONENT_CORRECTION = {'power_and_damping': 0.3, 'power_law': 0.5}
```

## PEAK_VELOCITY_FACTOR

*Constant* (`float`).

```python
PEAK_VELOCITY_FACTOR = 3.0
```

## peak_velocity_from_kb_mm_s

```python
peak_velocity_from_kb_mm_s(kb_fmax_zug: float) -> float
```

The peak velocity of a category, Formula (12).

$v_{\max} = \beta \, KB_{F\mathrm{max},Zug}$ with $\beta$ = 3,
an empirical factor, which is the number a DIN 4150-3 comparison wants.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fmax_zug` | $KB_{F\mathrm{max},Zug}$ of Formula (10). |

**Returns:** $v_{\max}$, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative input. |

## point_to_line_transition_distance_m

```python
point_to_line_transition_distance_m(
    train_length_m: float,
    *,
    wavelength_m: float,
) -> float
```

Where a train stops being a line source, Formula (B.1).

$R_0 \approx L^2 / \lambda$: nearer than that a train of length
$L$ is a line of point sources and its surface waves spread less
than a point's; further away it is a point source. Within the distances
of Table 1 the line behaviour is the rule.

**Parameters**

| Name | Description |
| :--- | :--- |
| `train_length_m` | $L$, in metres. |
| `wavelength_m` | $\lambda$ at the band of interest, in metres. |

**Returns:** $R_0$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive length or wavelength. |

## predict_floor_spectrum

```python
predict_floor_spectrum(
    emission_db: ArrayLike,
    *,
    ground_db: ArrayLike = 0.0,
    foundation_db: ArrayLike = 0.0,
    floor_db: ArrayLike = 0.0,
    mitigation_db: ArrayLike = 0.0,
) -> NDArray[np.float64]
```

The predicted spectrum on a floor, Formula (1).

Every term is added, band by band, as the formula prints it: the
emission spectrum, the transmission through the ground, the transfer
into the foundation, the transfer to the floor and the effect of the
mitigation. The Annex A tables are negative where they attenuate, and a
mitigation must be too, which is why the term is not called an insertion
loss here: the formula prints $D_e$ with a plus sign and names
DIN 45673-1 for it, and an insertion loss in the sense of DIN 45672-2
Annex B, [`elastic_insertion_loss`](/phonometry/reference/api/vibration/railway/#elastic_insertion_loss), is
positive where the element reduces the level, so it goes in with its
sign changed. An emission spectrum measured at the foundation makes the
foundation term zero (Annex C does exactly that).

**Parameters**

| Name | Description |
| :--- | :--- |
| `emission_db` | $L_{v,E}$, one level per band, in decibels. |
| `ground_db` | $\Delta L_{v,BB}$, per band or one value. |
| `foundation_db` | $\Delta L_{v,FB}$, per band or one value. |
| `floor_db` | $\Delta L_{v,DF}$, per band or one value. |
| `mitigation_db` | $D_e$, per band or one value, added as printed, so negative for a mitigation. |

**Returns:** $L_v$, one level per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-finite input or a term that does not broadcast to the emission spectrum. |

## predict_train_category

```python
predict_train_category(
    emission_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike = (4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0),
    ground_db: ArrayLike = 0.0,
    foundation_db: ArrayLike = 0.0,
    floor_db: ArrayLike = 0.0,
    mitigation_db: ArrayLike = 0.0,
) -> TrainCategoryPrediction
```

Run the chain from an emission spectrum to the assessment quantities.

Formula (1) for the spectrum on the floor, Formula (8) for the
KB-weighted bands from 4 Hz to 80 Hz, Formula (9) for the clock maximum
r.m.s. of the category, Formula (10) for its $KB_{F\mathrm{max}}$
and Formula (12) for the peak velocity. The assessment vibration
severity over the categories of a timetable is Formula (11), the sum of
[`train_assessment_severity`](/phonometry/reference/api/vibration/train-categories/#train_assessment_severity), which also
applies the rule of E DIN 4150-2:2023-08 that Formula (11) leaves out, a
category at or below 0,1 counting as zero.

**Parameters**

| Name | Description |
| :--- | :--- |
| `emission_db` | $L_{v,E}$, one level per band, in decibels. |
| `frequencies_hz` | The band centres, nominal; the 19 bands from 4 Hz to 250 Hz by default, and at least the 14 from 4 Hz to 80 Hz. |
| `ground_db` | $\Delta L_{v,BB}$, per band or one value. |
| `foundation_db` | $\Delta L_{v,FB}$, per band or one value. |
| `floor_db` | $\Delta L_{v,DF}$, per band or one value. |
| `mitigation_db` | $D_e$, per band or one value, added as printed, so negative for a mitigation. |

**Returns:** The chain, as a [`TrainCategoryPrediction`](/phonometry/reference/api/vibration/railway-prediction/#traincategoryprediction).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spectrum that does not hold the 14 bands of the KB assessment, or a bad term. |

## PREDICTION_BAND_CENTRES_HZ

*Constant* (`tuple`).

```python
PREDICTION_BAND_CENTRES_HZ = (4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0)
```

## RECOMMENDED_DISTANCES_M

*Constant* (`dict`).

```python
RECOMMENDED_DISTANCES_M = {'freight_soft_soil': {'tunnel': None, 'surface': 200.0}, 'mainline': {'tunnel': 30.0, 'surface': 60.0}, 's_bahn': {'tunnel': 20.0, 'surface': 40.0}, 'urban': {'tunnel': 20.0, 'surface': 25.0}}
```

## rescale_emission_for_speed

```python
rescale_emission_for_speed(
    levels_db: ArrayLike,
    *,
    speed_from_km_h: float,
    speed_to_km_h: float,
) -> NDArray[np.float64]
```

An emission spectrum carried to another train speed, Formula (3).

$L_{v,E2} = L_{v,E1} + 20 \lg (v_2 / v_1)$, the same shift in every
band, for the same category of train under the same conditions and a
change of speed of up to 30 %. Beyond that the frequencies bound to a
length, the sleeper-passing frequency $f_a = v / a$ for one, move
with the speed while the resonances do not, and the shift is refused.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{v,E1}$, the spectrum measured at the first speed, in decibels. |
| `speed_from_km_h` | $v_1$, the speed it was measured at. |
| `speed_to_km_h` | $v_2$, the speed wanted, in the same unit. |

**Returns:** $L_{v,E2}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive speed, a change of more than 30 %, or a non-finite spectrum. |

## SPEED_RESCALING_LIMIT

*Constant* (`float`).

```python
SPEED_RESCALING_LIMIT = 0.3
```

## TAKT_MAXIMUM_FACTOR

*Constant* (`float`).

```python
TAKT_MAXIMUM_FACTOR = 1.0
```

## takt_maximum_kb

```python
takt_maximum_kb(weighted_levels_db: ArrayLike) -> float
```

The clock maximum r.m.s. of a category from its spectrum, Formula (9).

$KB_{FTm,Zug} = c_{T1} v_0 10^{L_{v,ges}/20}$ with $L_{v,ges}$
the energy sum of the KB-weighted bands from 4 Hz to 80 Hz,
$c_{T1}$ = 1 for Max Hold spectra with the time weighting Fast and
$v_0 = 5 \cdot 10^{-5}$ mm/s, the reference of the velocity level;
the value is the KB quantity because KB is the velocity in millimetres
per second. Annex C prints 0,4 for a sum level of 78,1 dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `weighted_levels_db` | $L_{v,KB}$, as [`kb_weighted_levels_db`](/phonometry/reference/api/vibration/railway-prediction/#kb_weighted_levels_db) gives them, one per band. |

**Returns:** $KB_{FTm,Zug}$, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty or non-finite input. |

## train_decay_exponent

```python
train_decay_exponent(
    point_exponent: float,
    *,
    fitted_with: str = 'power_and_damping',
) -> float
```

The decay exponent of a train from that of a point excitation, Annex B.

$n_{Zug} = n_{Punkt} - 0{,}3$ when the point measurement was fitted
with spreading and damping apart (Formula (5)), $n_{Punkt} - 0{,}5$
when it was fitted as a power law alone (Formula (6)); both up to the
transition distance of Formula (B.1), beyond which the point exponent
holds as it is. The annex prints no floor, so a point exponent below the
correction gives a negative result, as printed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `point_exponent` | $n_{Punkt}$, not negative. |
| `fitted_with` | `"power_and_damping"` (default) or `"power_law"`. |

**Returns:** $n_{Zug}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative exponent or an unknown fit. |

## train_velocity_ratio

```python
train_velocity_ratio(
    distance_m: ArrayLike,
    *,
    reference_distance_m: float,
    transition_distance_m: float,
    point_exponent: float,
    exponent_correction: float,
) -> NDArray[np.float64]
```

The decay of a train's vibration with distance, Figure B.1.

The ratio of the velocity at $r$ to that at $r_0$, as the
figure draws it: a power law with the exponent
$n_{Punkt} - n_{Korr}$ up to the transition distance $R_0$ of
Formula (B.1), and the point exponent $n_{Punkt}$ beyond it,
continuous at $R_0$. The figure is a sketch and prints no closed
form; this is its reading.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | $r$, in metres, one or many. |
| `reference_distance_m` | $r_0$, in metres. |
| `transition_distance_m` | $R_0$, in metres. |
| `point_exponent` | $n_{Punkt}$. |
| `exponent_correction` | $n_{Korr}$, 0,3 to 0,5. |

**Returns:** $v(r) / v(r_0)$, one per distance.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive distance, a reference beyond the transition, a negative exponent or a correction outside Annex B. |

## TrainCategoryPrediction

```python
TrainCategoryPrediction(
    frequencies_hz: NDArray[np.float64],
    emission_db: NDArray[np.float64],
    floor_db: NDArray[np.float64],
    weighted_frequencies_hz: NDArray[np.float64],
    weighted_db: NDArray[np.float64],
    sum_level_db: float,
    kb_ftm: float,
    kb_fmax: float,
    peak_velocity_mm_s: float,
)
```

The prediction for one category of train, Clauses 5 and 7.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres. |
| `emission_db` | $L_{v,E}$ the prediction started from. |
| `floor_db` | $L_v$ of Formula (1), the spectrum on the floor. |
| `weighted_frequencies_hz` | The band centres from 4 Hz to 80 Hz the KB assessment sums. |
| `weighted_db` | $L_{v,KB}$ of Formula (8) over those bands. |
| `sum_level_db` | $L_{v,ges}$ of Formula (9), the energy sum of the weighted bands. |
| `kb_ftm` | $KB_{FTm,Zug}$ of Formula (9). |
| `kb_fmax` | $KB_{F\mathrm{max},Zug}$ of Formula (10). |
| `peak_velocity_mm_s` | $v_{\max}$ of Formula (12). |

### TrainCategoryPrediction.plot()

```python
TrainCategoryPrediction.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the emission, the floor spectrum and the KB-weighted bands.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_train_category_prediction`. |

**Returns:** The `Axes`.

## velocity_spectrum_um_s

```python
velocity_spectrum_um_s(levels_db: ArrayLike) -> NDArray[np.float64]
```

A level spectrum as a velocity spectrum, Formula (13).

$v_{RMS}(f_{Tn}) = 1000 \, v_0 \, 10^{L_v(f_{Tn})/20}$ in micrometres
per second, the form the VC curves of VDI 2038 Blatt 2 are drawn in.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_v$, one level per band, in decibels. |

**Returns:** $v_{RMS}$, one per band, in micrometres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-finite input. |
