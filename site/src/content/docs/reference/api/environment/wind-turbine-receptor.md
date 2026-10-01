---
title: "environment.assessment.wind_turbine_receptor"
description: "Wind turbine sound at a receptor (IEC TS 61400-11-2:2024)."
sidebar:
  label: "wind_turbine_receptor"
---

Wind turbine sound at a receptor (IEC TS 61400-11-2:2024).

IEC 61400-11 measures what a turbine emits; IEC TS 61400-11-2:2024 measures
what arrives at a dwelling, where the wind that drives the turbine also stirs
the trees, the background and the propagation. This module holds its closed
forms and printed tables; the amplitude modulation of clause 13 is in
[`wind_turbine_modulation`](/phonometry/reference/api/environment/wind-turbine-modulation/).

**Wind speed at another height** (Annex K, IEC 61400-11:2012 Annex D). The
power law of Equation (K.1), [`power_law_wind_speed`](/phonometry/reference/api/environment/wind-turbine-receptor/#power_law_wind_speed), and its inverse
for the shear exponent, Equation (K.2), [`wind_shear_exponent`](/phonometry/reference/api/environment/wind-turbine-receptor/#wind_shear_exponent), which
Tables K.1 and K.2 tabulate for 10 m and 120 m; the logarithmic profile with
the reference roughness length $z_{0\mathrm{ref}} = 0.05$ m (3.31) that
9.3.2.1 uses to bring a hub-height wind speed to 10 m,
[`logarithmic_wind_speed`](/phonometry/reference/api/environment/wind-turbine-receptor/#logarithmic_wind_speed); and [`wind_shear_profile`](/phonometry/reference/api/environment/wind-turbine-receptor/#wind_shear_profile), which plots
both through two measured heights. Table K.3's roughness lengths are
[`ROUGHNESS_LENGTHS_M`](/phonometry/reference/api/environment/wind-turbine-receptor/#roughness_lengths_m).

**Bins and their averages** (10.1, 10.3). [`bin_sound_levels`](/phonometry/reference/api/environment/wind-turbine-receptor/#bin_sound_levels) sorts
interval levels into 1 m/s wind speed bins and 30 degree sectors and forms, per
bin, the energy average of Equation (1) (or the arithmetic one of Equation (8)
for statistical levels), the type A uncertainty of Equation (2) or (9), the
type B one of Equations (3) and (4) and their combination, Equation (5).
[`turbine_sound_levels`](/phonometry/reference/api/environment/wind-turbine-receptor/#turbine_sound_levels) subtracts the background per bin with Equations
(6) and (7), under the 3 dB rule of 11.7. [`predicted_receptor_level`](/phonometry/reference/api/environment/wind-turbine-receptor/#predicted_receptor_level)
sums a prediction over the turbines with the uncertainty of Equations (10)
and (11), and [`sound_relevant_turbines`](/phonometry/reference/api/environment/wind-turbine-receptor/#sound_relevant_turbines) picks the turbines whose wind
speeds make the binning wind speed (9.3.2.3).

**Low frequency sound** (Annex C). [`wind_turbine_low_frequency_level`](/phonometry/reference/api/environment/wind-turbine-receptor/#wind_turbine_low_frequency_level)
evaluates Equation (C.1) band by band with the ground correction and air
attenuation of Table C.2 and a facade insulation such as those of Table C.3.
Table C.2's air attenuation is the Danish statutory order's, not the
ISO 9613-1 value at the 70 % humidity its caption names: from 25 Hz to
100 Hz its cells are those of the order (BEK nr. 135 of 7 February 2019,
Table 1.4), set for 10 degrees C and **80 %** relative humidity with the
Nord2000 band attenuation rates and nothing below 25 Hz, which puts them
0.01 dB/km to 0.02 dB/km under ISO 9613-1 at 70 % between 50 Hz and 100 Hz;
from 125 Hz to 200 Hz the cells are ISO 9613-1 at 10 degrees C and 70 %
evaluated at the nominal band centres. ISO 9613-1's own Table 1 is computed at
the exact mid-band frequencies and prints 0.584 dB/km at 160 Hz (158.5 Hz
exactly), where Table C.2 prints the nominal 160 Hz value 0.59; Table 7 of the
TS, in contrast, follows the exact mid-bands.

**Emergence and the rating level** (Annexes J and A). [`sound_emergence`](/phonometry/reference/api/environment/wind-turbine-receptor/#sound_emergence)
is Equation (J.1); [`wind_turbine_rating_level`](/phonometry/reference/api/environment/wind-turbine-receptor/#wind_turbine_rating_level) adds the most severe of
the tonal, amplitude modulation and impulsive adjustments (A.1), with the
amplitude modulation adjustment of Figure A.1 in
[`amplitude_modulation_adjustment`](/phonometry/reference/api/environment/wind-turbine-receptor/#amplitude_modulation_adjustment).

**The upper tone search frequency** (12.5.2.4, Table 7).
[`upper_tone_search_frequency`](/phonometry/reference/api/environment/wind-turbine-receptor/#upper_tone_search_frequency) finds the lowest one-third-octave band that
ISO 9613-1 attenuates by at least 20 dB over the distance to the nearest
turbine.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## amplitude_modulation_adjustment

```python
amplitude_modulation_adjustment(
    modulation_depth_db: ArrayLike,
) -> NDArray[np.float64] | float
```

The amplitude modulation adjustment of Figure A.1, in dB.

The example adjustment of A.3: none below a modulation depth of 3 dB,
3 dB at 3 dB, rising linearly to 5 dB at 10 dB and 5 dB above it. The
figure is drawn to 12 dB; the 5 dB is kept beyond. The depth is the
reconstructed time-series modulation depth of clause 13 (the AM rating of
[`amplitude_modulation_period`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_period)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `modulation_depth_db` | The modulation depth, in dB. |

**Returns:** The adjustment $K_\mathrm{am}$, in dB; a `float` for a scalar depth.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a depth is negative or not finite. |

## BackgroundCorrectionRegime

```python
BackgroundCorrectionRegime(*values)
```

Which rule of 11.7 a bin's background correction followed.

`LOGARITHMIC`: the total is at least 3 dB above the background, and the
background is subtracted (Equation (6)). `THREE_DB`: the total is 0 dB
to 3 dB above it, and the suggested 3 dB correction is applied.
`UNDETERMINED`: the background is above the total, and the turbine
level cannot be determined (11.6.4).

## bin_sound_levels

```python
bin_sound_levels(
    levels_db: ArrayLike,
    wind_speeds_m_s: ArrayLike,
    wind_directions_deg: ArrayLike | None = None,
    *,
    averaging: str = 'energy',
    type_b_uncertainty_db: ArrayLike = 0.0,
    bin_width_m_s: float = 1.0,
    sector_width_deg: float = 30.0,
) -> BinnedSoundLevels
```

Average interval levels per wind speed bin and sector (10.1, 10.3).

Each interval (typically 10 s to 10 min) goes into the wind speed bin of
its binning wind speed, `bin_width_m_s` wide and centred on its
multiples, and, with directions, into the `sector_width_deg` sector
whose first member is centred on north. Per bin:

* the average, Equation (1)
  $\overline{L}_k = 10 \lg(\frac{1}{N}\sum 10^{L_{j,k}/10})$ for
  equivalent levels, or Equation (8), the arithmetic mean, for
  statistical levels such as $L_{90}$ (10.3.2 NOTE);
* the type A uncertainty, Equation (2) (or (9)),
  $s = \sqrt{\sum (L_{j,k} - \overline{L}_k)^2 / (N(N-1))}$;
* the type B uncertainty, Equation (4), the root mean square of the
  per-interval type B uncertainties of Equation (3);
* their combination, Equation (5), $\sqrt{s^2 + u^2}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The interval levels, in dB. |
| `wind_speeds_m_s` | The binning wind speed of each interval, in m/s. |
| `wind_directions_deg` | Optional wind direction of each interval, in degrees from north. |
| `averaging` | `"energy"` (Equation (1), for `LAeq`) or `"arithmetic"` (Equation (8), for statistical levels). |
| `type_b_uncertainty_db` | Combined type B standard uncertainty of each interval, Equation (3), in dB: one value for all or one per interval. Combine the components in quadrature, for example those of [`TYPE_B_UNCERTAINTY_EXAMPLES_DB`](/phonometry/reference/api/environment/wind-turbine-receptor/#type_b_uncertainty_examples_db). |
| `bin_width_m_s` | Width of the wind speed bins, in m/s (1 m/s by default, 10.1). |
| `sector_width_deg` | Width of the direction sectors, in degrees (30 by default, 10.1); it must divide 360. |

**Returns:** A [`BinnedSoundLevels`](/phonometry/reference/api/environment/wind-turbine-receptor/#binnedsoundlevels).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in length, a value is not finite, a wind speed or an uncertainty is negative, or `averaging` is unknown. |

## BinnedSoundLevels

```python
BinnedSoundLevels(
    wind_speeds_m_s: NDArray[np.float64],
    wind_directions_deg: NDArray[np.float64] | None,
    counts: NDArray[np.int64],
    mean_levels_db: NDArray[np.float64],
    type_a_uncertainty_db: NDArray[np.float64],
    type_b_uncertainty_db: NDArray[np.float64],
    combined_uncertainty_db: NDArray[np.float64],
    *,
    averaging: str,
    interval_levels_db: NDArray[np.float64],
    interval_wind_speeds_m_s: NDArray[np.float64],
    bin_width_m_s: float,
    sector_width_deg: float,
)
```

Interval levels averaged per wind speed bin and sector (10.1, 10.3).

One row per occupied bin, sorted by sector and then wind speed.

**Attributes**

| Name | Description |
| :--- | :--- |
| `wind_speeds_m_s` | Centre of each bin's wind speed class, in m/s. |
| `wind_directions_deg` | Centre of each bin's direction sector, in degrees, or `None` when binned by wind speed alone. |
| `counts` | Number of intervals $N$ in each bin. |
| `mean_levels_db` | The bin average, Equation (1) (energy) or Equation (8) (arithmetic), in dB. |
| `type_a_uncertainty_db` | Equation (2) or (9), in dB; NaN for a bin of one interval, whose spread the equation cannot give. |
| `type_b_uncertainty_db` | Equation (4), in dB. |
| `combined_uncertainty_db` | Equation (5), in dB; NaN where the type A part is. |
| `averaging` | `"energy"` or `"arithmetic"`. |
| `interval_levels_db` | The interval levels binned, in dB. |
| `interval_wind_speeds_m_s` | Their wind speeds, in m/s. |
| `bin_width_m_s` | Width of the wind speed bins, in m/s. |
| `sector_width_deg` | Width of the direction sectors, in degrees (also kept when binned by wind speed alone). |

### BinnedSoundLevels.background_corrected()

```python
BinnedSoundLevels.background_corrected(
    background: BinnedSoundLevels,
) -> TurbineSoundLevels
```

Correct these total levels for a background binned the same way (11.7).

The bins the two share are corrected by [`turbine_sound_levels`](/phonometry/reference/api/environment/wind-turbine-receptor/#turbine_sound_levels)
with their combined uncertainties; a bin of either without a partner
in the other is left out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `background` | The background (turbines off) levels, binned with the same wind speed classes and sectors. |

**Returns:** A [`TurbineSoundLevels`](/phonometry/reference/api/environment/wind-turbine-receptor/#turbinesoundlevels) over the shared bins, with their sector centres when binned by direction.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the two share no bin, one is binned by direction and the other is not, or their bin or sector widths differ. |

### BinnedSoundLevels.plot()

```python
BinnedSoundLevels.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the intervals against wind speed and the bin averages over them.

The scatter of interval levels against the binning wind speed is what
11.9 asks to be reported; the bin averages carry their combined
uncertainty as error bars.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bin averages. |

**Returns:** The axes.

## GroundImpedanceClass

```python
GroundImpedanceClass(
    flow_resistivity_kpa_s_m2: float,
    nordtest_classes_kpa_s_m2: tuple[float, ...],
    description: str,
)
```

One impedance class of Table C.1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `flow_resistivity_kpa_s_m2` | Representative flow resistivity, in kPa s/m². |
| `nordtest_classes_kpa_s_m2` | The Nordtest flow resistivity classes the class covers, in kPa s/m² (empty where the table prints a dash). |
| `description` | The ground the class describes. |

## logarithmic_wind_speed

```python
logarithmic_wind_speed(
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
    roughness_length_m: float = 0.05,
) -> NDArray[np.float64] | float
```

Wind speed at another height by the logarithmic profile.

$V_z = V_{z,\mathrm{ref}} \ln(z/z_0) / \ln(z_\mathrm{ref}/z_0)$
(IEC 61400-11:2012 Equation (D.1)). With the default reference roughness
length $z_{0\mathrm{ref}} = 0.05$ m (3.31), a hub-height wind speed
brought to 10 m is the binning wind speed $V_\mathrm{bin}$ of
9.3.2.1 (IEC 61400-11:2012 Equation (29) solved for $V_{10}$).

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_speed_m_s` | Wind speed at the reference height, in m/s. |
| `height_m` | Height of the wanted wind speed, in m. |
| `reference_height_m` | Height of the known wind speed, in m. |
| `roughness_length_m` | Roughness length $z_0$, in m. |

**Returns:** The wind speed at `height_m`, in m/s; a `float` for scalar inputs.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a height or the roughness length is not positive, a height does not exceed the roughness length, or a speed is negative. |

## LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM

*Constant* (`numpy.ndarray, shape (14,)`).

## LOW_FREQUENCY_BANDS_HZ

*Constant* (`numpy.ndarray, shape (14,)`).

## LOW_FREQUENCY_FACADE_INSULATION_DB

*Constant* (`mapping`).

```python
LOW_FREQUENCY_FACADE_INSULATION_DB = {'Denmark brick or similar': array([ 4.9,  5.9,  4.6,  6.6,  8.4, 10.8, 11.4, 13. , 16.6, 19.7, 21.2,
       20.2, 21.2, 21. ]), 'Denmark lightweight': array([ 6.8,  3.9,  0.4, -0.2,  4.8,  6.2,  8.4, 10.5, 11.9, 11.9, 16. ,
       17.5, 17.9, 17. ])}
```

## LOW_FREQUENCY_GROUND_CORRECTION_DB

*Constant* (`numpy.ndarray, shape (14,)`).

## LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES

*Constant* (`mapping`).

```python
LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES = {'A': GroundImpedanceClass(flow_resistivity_kpa_s_m2=12.5, nordtest_classes_kpa_s_m2=(10.0, 15.0), description='Very soft (snow, moss like)'), 'B': GroundImpedanceClass(flow_resistivity_kpa_s_m2=32.0, nordtest_classes_kpa_s_m2=(25.0, 40.0), description='Soft forest floor (short dense heatherlike or thick moss)'), 'C': GroundImpedanceClass(flow_resistivity_kpa_s_m2=80.0, nordtest_classes_kpa_s_m2=(63.0, 100.0), description='Uncompacted loose ground (turf, grass, loose soil)'), 'D': GroundImpedanceClass(flow_resistivity_kpa_s_m2=200.0, nordtest_classes_kpa_s_m2=(160.0, 250.0), description='Normal uncompacted ground (forest floor, pasture field)'), 'E': GroundImpedanceClass(flow_resistivity_kpa_s_m2=500.0, nordtest_classes_kpa_s_m2=(400.0, 630.0), description='Compacted field and gravel (compacted lawns, park area)'), 'F': GroundImpedanceClass(flow_resistivity_kpa_s_m2=2000.0, nordtest_classes_kpa_s_m2=(2000.0,), description='Compacted dense ground (gravel road, parking lot, ISO 10844)'), 'G': GroundImpedanceClass(flow_resistivity_kpa_s_m2=20000.0, nordtest_classes_kpa_s_m2=(), description='Hard surface (most normal asphalt, concrete)'), 'H': GroundImpedanceClass(flow_resistivity_kpa_s_m2=200000.0, nordtest_classes_kpa_s_m2=(), description='Very hard and dense surfaces (dense asphalt, concrete, water)')}
```

## LowFrequencyLevel

```python
LowFrequencyLevel(
    frequencies_hz: NDArray[np.float64],
    sound_power_levels_db: NDArray[np.float64],
    a_weighting_db: NDArray[np.float64],
    distance_terms_db: NDArray[np.float64],
    ground_correction_db: NDArray[np.float64],
    air_attenuation_db: NDArray[np.float64],
    facade_insulation_db: NDArray[np.float64] | None,
    outdoor_levels_db: NDArray[np.float64],
    indoor_levels_db: NDArray[np.float64] | None,
    outdoor_level_db: float,
    indoor_level_db: float | None,
    *,
    a_weighted: bool,
)
```

Low frequency sound at a receptor by Equation (C.1) (Annex C).

Arrays with a turbine axis have one row per turbine and one column per
band; the band arrays are summed over the turbines.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third-octave centres, in Hz. |
| `sound_power_levels_db` | The turbines' band sound power levels. |
| `a_weighting_db` | The A-weighting added to each band (zero when the result is unweighted). |
| `distance_terms_db` | $10 \lg(l^2 + h^2)$ of each turbine, in dB. |
| `ground_correction_db` | $\Delta L_\mathrm{g,LF}$ per band. |
| `air_attenuation_db` | $\Delta L_\mathrm{a}$ per turbine and band. |
| `facade_insulation_db` | $\Delta L_\sigma$ per band, or `None` for an outdoor result. |
| `outdoor_levels_db` | Outdoor band levels summed over the turbines. |
| `indoor_levels_db` | Indoor band levels, or `None`. |
| `outdoor_level_db` | Energy sum of the outdoor bands, in dB. |
| `indoor_level_db` | Energy sum of the indoor bands, or `None`. |
| `a_weighted` | Whether the levels are A-weighted. |

### LowFrequencyLevel.plot()

```python
LowFrequencyLevel.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the outdoor and indoor band levels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the outdoor levels. |

**Returns:** The axes.

## MODELLING_UNCERTAINTY_DB

*Constant* (`float`).

```python
MODELLING_UNCERTAINTY_DB = 0.5
```

## power_law_wind_speed

```python
power_law_wind_speed(
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
    shear_exponent: ArrayLike,
) -> NDArray[np.float64] | float
```

Wind speed at another height by the power law (Equation (K.1)).

$V_z = V_{z,\mathrm{ref}} \, (z/z_\mathrm{ref})^{\alpha}$, the
profile of IEC 61400-11:2012 D.3 that Table K.1 evaluates for 120 m and
10 m.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_speed_m_s` | Wind speed at the reference height, in m/s. |
| `height_m` | Height of the wanted wind speed, in m. |
| `reference_height_m` | Height of the known wind speed, in m. |
| `shear_exponent` | The wind shear exponent $\alpha$. |

**Returns:** The wind speed at `height_m`, in m/s; a `float` for scalar inputs.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a height is not positive, a speed is negative or a value is not finite. |

## predicted_receptor_level

```python
predicted_receptor_level(
    turbine_levels_db: ArrayLike,
    sound_power_uncertainty_db: ArrayLike,
    *,
    prediction_model_uncertainty_db: float = 2.0,
    modelling_uncertainty_db: float = 0.5,
) -> PredictedReceptorLevel
```

Sum a prediction over the turbines, with its uncertainty (10.3.4).

The receptor level is the energy sum of the turbines' predicted levels.
Equation (10) carries each turbine's sound power level uncertainty to it
weighted by the turbine's share of the energy,

$$
u_{L_{\mathrm{A},k}} = \frac{\sum_i u_{L_{W\mathrm{A}},i,k} \, 10^{L_{p\mathrm{A},i,k}/10}}{\sum_i 10^{L_{p\mathrm{A},i,k}/10}}
$$

(a linear, fully correlated combination), and Equation (11) adds the
prediction model and the modelling in quadrature.

**Parameters**

| Name | Description |
| :--- | :--- |
| `turbine_levels_db` | Predicted level at the receptor from each turbine, in dB. |
| `sound_power_uncertainty_db` | Uncertainty of each turbine's sound power level, from IEC 61400-11, in dB (one value for all or one each). |
| `prediction_model_uncertainty_db` | Standard uncertainty of the prediction model, in dB (2 dB by default, 10.3.4 NOTE). |
| `modelling_uncertainty_db` | Uncertainty of the propagation modelling, in dB (0.5 dB by default). |

**Returns:** A [`PredictedReceptorLevel`](/phonometry/reference/api/environment/wind-turbine-receptor/#predictedreceptorlevel).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a value is not finite or an uncertainty is negative. |

## PredictedReceptorLevel

```python
PredictedReceptorLevel(
    turbine_levels_db: NDArray[np.float64],
    sound_power_uncertainty_db: NDArray[np.float64],
    level_db: float,
    propagated_uncertainty_db: float,
    combined_uncertainty_db: float,
    *,
    prediction_model_uncertainty_db: float,
    modelling_uncertainty_db: float,
)
```

A predicted receptor level and its uncertainty (10.3.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `turbine_levels_db` | The predicted level from each turbine, in dB. |
| `sound_power_uncertainty_db` | The sound power level uncertainty of each turbine, in dB. |
| `level_db` | The energy sum of the turbines' levels, in dB. |
| `propagated_uncertainty_db` | Equation (10), the level-weighted mean of the turbines' sound power uncertainties, in dB. |
| `combined_uncertainty_db` | Equation (11), in dB. |
| `prediction_model_uncertainty_db` | The model's uncertainty used, in dB. |
| `modelling_uncertainty_db` | The modelling uncertainty used, in dB. |

### PredictedReceptorLevel.plot()

```python
PredictedReceptorLevel.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each turbine's contribution and the total with its uncertainty.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the turbine bars. |

**Returns:** The axes.

## PREDICTION_MODEL_UNCERTAINTY_DB

*Constant* (`float`).

```python
PREDICTION_MODEL_UNCERTAINTY_DB = 2.0
```

## REFERENCE_ROUGHNESS_LENGTH_M

*Constant* (`float`).

```python
REFERENCE_ROUGHNESS_LENGTH_M = 0.05
```

## ROUGHNESS_LENGTHS_M

*Constant* (`mapping`).

```python
ROUGHNESS_LENGTHS_M = {'Water, snow or sand surfaces': 0.0001, 'Open, flat land, mown grass, bare soil': 0.01, 'Farmland with some vegetation': 0.05, 'Suburbs, towns, forests, many trees and bushes': 0.3}
```

## sound_emergence

```python
sound_emergence(
    ambient_levels_db: ArrayLike,
    background_levels_db: ArrayLike,
    *,
    wind_speeds_m_s: ArrayLike | None = None,
) -> SoundEmergence
```

The emergence criterion of each wind speed class (Equation (J.1)).

$E(j) = L_\mathrm{Amb}(j) - L_\mathrm{R\acute{e}s}(j)$, the
difference of the ambient sound criterion (turbines operating) and the
background sound criterion (turbines stopped) for each complete wind speed
class, the criterion of French regulation. The TS warns it is not to be
confused with limits on the difference between the turbine sound and the
background.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ambient_levels_db` | The ambient sound criterion of each class, in dB. |
| `background_levels_db` | The background sound criterion of each class. |
| `wind_speeds_m_s` | Optional wind speed of each class, in m/s. |

**Returns:** A [`SoundEmergence`](/phonometry/reference/api/environment/wind-turbine-receptor/#soundemergence).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in length or are not finite. |

## sound_relevant_turbines

```python
sound_relevant_turbines(
    predicted_levels_db: ArrayLike,
) -> SoundRelevantTurbines
```

Select the sound relevant turbines of a wind farm (9.3.2.3).

The turbines are sorted by their predicted contribution at the receptor.
The quietest is left out of the prediction, and the next quietest after
it, for as long as the total of those that remain has dropped by no more
than 1.0 dB from the total of all; the turbine whose exclusion would drop
it by more is kept, with every louder one. Typically two or three
turbines remain. A drop within a nanodecibel of 1.0 dB is a drop of
1.0 dB, not more, so the rounding of the energy sums cannot keep a
turbine the TS leaves out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `predicted_levels_db` | Each turbine's predicted level at the receptor, in dB. |

**Returns:** A [`SoundRelevantTurbines`](/phonometry/reference/api/environment/wind-turbine-receptor/#soundrelevantturbines).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the levels are empty or not finite. |

## SoundEmergence

```python
SoundEmergence(
    ambient_levels_db: NDArray[np.float64],
    background_levels_db: NDArray[np.float64],
    emergence_db: NDArray[np.float64],
    *,
    wind_speeds_m_s: NDArray[np.float64] | None,
)
```

The emergence criterion per wind speed class (Annex J, Equation (J.1)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `ambient_levels_db` | The ambient sound criterion per class, in dB. |
| `background_levels_db` | The background sound criterion per class. |
| `emergence_db` | $E(j) = L_\mathrm{Amb}(j) - L_\mathrm{Res}(j)$. |
| `wind_speeds_m_s` | The wind speed classes, in m/s, when given. |

### SoundEmergence.plot()

```python
SoundEmergence.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the emergence of each wind speed class.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the emergence bars. |

**Returns:** The axes.

## SoundRelevantTurbines

```python
SoundRelevantTurbines(
    predicted_levels_db: NDArray[np.float64],
    relevant: NDArray[np.bool_],
    total_level_db: float,
    relevant_level_db: float,
)
```

The turbines that set the binning wind speed at a receptor (9.3.2.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `predicted_levels_db` | Each turbine's predicted level at the receptor, in dB, in the order given. |
| `relevant` | Whether each turbine is sound relevant. |
| `total_level_db` | The predicted level of all turbines, in dB. |
| `relevant_level_db` | The predicted level of the relevant ones, in dB. |

### SoundRelevantTurbines.binning_wind_speed_m_s()

```python
SoundRelevantTurbines.binning_wind_speed_m_s(
    turbine_wind_speeds_m_s: ArrayLike,
) -> float
```

The binning wind speed: the arithmetic mean over the relevant turbines.

**Parameters**

| Name | Description |
| :--- | :--- |
| `turbine_wind_speeds_m_s` | The wind speed derived from each turbine (power curve or nacelle, recalculated to 10 m), in m/s, in the order of `predicted_levels_db`. |

**Returns:** The mean of the relevant turbines' wind speeds, in m/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the speeds are not one per turbine or not finite. |

### SoundRelevantTurbines.indices

*property*

Positions of the sound relevant turbines, loudest first.

### SoundRelevantTurbines.plot()

```python
SoundRelevantTurbines.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the turbines' levels, loudest first, the relevant ones marked.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the turbine bars. |

**Returns:** The axes.

## SWEDISH_LOW_FREQUENCY_LIMITS_DB

*Constant* (`mapping`).

```python
SWEDISH_LOW_FREQUENCY_LIMITS_DB = {31.5: 56.0, 40.0: 49.0, 50.0: 43.0, 63.0: 42.0, 80.0: 40.0, 100.0: 38.0, 125.0: 36.0, 160.0: 34.0, 200.0: 32.0}
```

## TONE_SEARCH_BANDS_HZ

*Constant* (`numpy.ndarray, shape (24,)`).

## ToneSearchLimit

```python
ToneSearchLimit(
    distance_m: float,
    frequencies_hz: NDArray[np.float64],
    attenuation_db: NDArray[np.float64],
    upper_frequency_hz: float,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float,
)
```

The upper frequency of the tonal search range (12.5.2.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `distance_m` | Distance from the nearest turbine, in m. |
| `frequencies_hz` | The nominal one-third-octave centres searched. |
| `attenuation_db` | ISO 9613-1 attenuation of each band over the distance, at the exact mid-band frequency, in dB. |
| `upper_frequency_hz` | The nominal centre of the lowest band attenuated by at least 20 dB, or 10 kHz when none is. |
| `temperature_c` | Air temperature, in degrees C. |
| `relative_humidity_percent` | Relative humidity, in %. |
| `atmospheric_pressure_kpa` | Atmospheric pressure, in kPa. |

### ToneSearchLimit.plot()

```python
ToneSearchLimit.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band attenuation over the distance and the 20 dB line.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the attenuation curve. |

**Returns:** The axes.

## turbine_sound_levels

```python
turbine_sound_levels(
    total_levels_db: ArrayLike,
    background_levels_db: ArrayLike,
    *,
    total_uncertainty_db: ArrayLike = 0.0,
    background_uncertainty_db: ArrayLike = 0.0,
    wind_speeds_m_s: ArrayLike | None = None,
    wind_directions_deg: ArrayLike | None = None,
) -> TurbineSoundLevels
```

Subtract the background from the total, bin by bin (10.3.2, 11.7).

Where the bin-averaged total is at least 3 dB above the background, the
turbine level is the logarithmic subtraction of Equation (6),
$L_{c,k} = 10 \lg(10^{L_{T,k}/10} - 10^{L_{B,k}/10})$, with the
uncertainty of Equation (7). Where it is 0 dB to 3 dB above, 11.7 suggests
a 3 dB correction instead, and a regulatory excess cannot then be found
(11.7 NOTE 1). Where the background is louder than the total, no turbine
level can be determined (11.6.4) and the bin is NaN. A difference within
a nanodecibel of 3 dB or of 0 dB is on that limit, so the rounding of two
energy means cannot move a bin from one rule to the other.

**Parameters**

| Name | Description |
| :--- | :--- |
| `total_levels_db` | Bin levels with the turbines operating, in dB. |
| `background_levels_db` | Bin levels with the turbines off, in dB. |
| `total_uncertainty_db` | Combined standard uncertainty of each total level, Equation (5), in dB; NaN for a bin of one interval, whose uncertainty Equation (2) cannot give. |
| `background_uncertainty_db` | That of each background level, in dB. |
| `wind_speeds_m_s` | Optional wind speed of each bin, in m/s, for the plot. |
| `wind_directions_deg` | Optional centre of each bin's direction sector, in degrees, for bins classified by direction as well (10.1); the plot draws each sector apart. |

**Returns:** A [`TurbineSoundLevels`](/phonometry/reference/api/environment/wind-turbine-receptor/#turbinesoundlevels).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in length or are not finite, or an uncertainty is infinite or negative. |

## TurbineSoundLevels

```python
TurbineSoundLevels(
    total_levels_db: NDArray[np.float64],
    background_levels_db: NDArray[np.float64],
    level_differences_db: NDArray[np.float64],
    turbine_levels_db: NDArray[np.float64],
    turbine_uncertainty_db: NDArray[np.float64],
    *,
    regimes: tuple[BackgroundCorrectionRegime, ...],
    wind_speeds_m_s: NDArray[np.float64] | None,
    wind_directions_deg: NDArray[np.float64] | None,
)
```

Background-corrected wind turbine levels per bin (10.3.2, 11.7).

**Attributes**

| Name | Description |
| :--- | :--- |
| `total_levels_db` | The total (turbines on) bin levels, in dB. |
| `background_levels_db` | The background (turbines off) bin levels. |
| `level_differences_db` | Total minus background, in dB. |
| `turbine_levels_db` | The turbine level $L_{c,k}$, in dB: Equation (6) where the difference is at least 3 dB, the total minus 3 dB where it is 0 dB to 3 dB, NaN where it is negative. |
| `turbine_uncertainty_db` | Its standard uncertainty, in dB: Equation (7) for the logarithmic subtraction, the total's own uncertainty for the fixed 3 dB correction (a constant offset), NaN where undetermined. |
| `regimes` | The [`BackgroundCorrectionRegime`](/phonometry/reference/api/environment/wind-turbine-receptor/#backgroundcorrectionregime) of each bin. |
| `wind_speeds_m_s` | The bins' wind speeds, in m/s, when known. |
| `wind_directions_deg` | Centre of each bin's direction sector, in degrees, when binned by direction; `None` otherwise. Two bins of one wind speed class in different sectors are told apart by it. |

### TurbineSoundLevels.plot()

```python
TurbineSoundLevels.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot total, background and turbine levels per bin.

Binned by direction, each sector is drawn apart, in its own colour:
the turbine level solid, the total dashed and the background dotted.
The twelve 30° sectors of 10.1 take twelve colours; narrower sectors
past the twelfth take them again, in the same order.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the turbine level line (one per sector). |

**Returns:** The axes.

## TYPE_B_UNCERTAINTY_EXAMPLES_DB

*Constant* (`mapping`).

```python
TYPE_B_UNCERTAINTY_EXAMPLES_DB = {'calibration': (0.3, 0.2), 'instrument': (0.5, 0.3), 'measurement position': (0.5, 0.3), 'wind screen insertion loss': (0.3, 0.2)}
```

## TYPICAL_WIND_SHEAR_EXPONENT_RANGE

*Constant* (`tuple`).

```python
TYPICAL_WIND_SHEAR_EXPONENT_RANGE = (-0.1, 0.5)
```

## upper_tone_search_frequency

```python
upper_tone_search_frequency(
    distance_m: float,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
) -> ToneSearchLimit
```

Upper frequency of the search for tones at a receptor (12.5.2.4).

Tones in a one-third-octave band that ISO 9613-1 attenuates by at least
20 dB over the distance to the nearest turbine are typically of no concern
to its neighbours, and every higher band is attenuated more; the lowest
such band sets the top of the search range. The attenuation is evaluated
at the exact mid-band frequency of each band (ISO 9613-1), which
reproduces the printed rows of Table 7; the search stops at 10 kHz, the
top of ISO 9613-1, when no band reaches 20 dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | Distance from the source to the receiver, in m. |
| `temperature_c` | Air temperature, in degrees C. |
| `relative_humidity_percent` | Relative humidity, in %. |
| `atmospheric_pressure_kpa` | Atmospheric pressure, in kPa. |

**Returns:** A [`ToneSearchLimit`](/phonometry/reference/api/environment/wind-turbine-receptor/#tonesearchlimit).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the distance is not positive or the atmosphere is outside what ISO 9613-1 accepts. |

## wind_shear_exponent

```python
wind_shear_exponent(
    speed_m_s: ArrayLike,
    reference_speed_m_s: ArrayLike,
    *,
    height_m: float,
    reference_height_m: float,
) -> NDArray[np.float64] | float
```

Wind shear exponent from two wind speeds (Equation (K.2)).

$\alpha = \ln(V_z/V_{z,\mathrm{ref}}) / \ln(z/z_\mathrm{ref})$; with
$z = 120$ m and $z_\mathrm{ref} = 10$ m this is Table K.2.
Values outside [`TYPICAL_WIND_SHEAR_EXPONENT_RANGE`](/phonometry/reference/api/environment/wind-turbine-receptor/#typical_wind_shear_exponent_range) are returned as
computed; Table K.2 leaves them blank.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speed_m_s` | Wind speed at `height_m`, in m/s. |
| `reference_speed_m_s` | Wind speed at `reference_height_m`, in m/s. |
| `height_m` | The higher (or other) height, in m. |
| `reference_height_m` | The reference height, in m. |

**Returns:** The shear exponent; a `float` for scalar inputs.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a speed or height is not positive, or the two heights are the same. |

## wind_shear_profile

```python
wind_shear_profile(
    lower_speed_m_s: float,
    upper_speed_m_s: float,
    *,
    lower_height_m: float = 10.0,
    upper_height_m: float,
) -> WindShearProfile
```

The power-law wind profile through two measured wind speeds (K.4.3).

The wind shear is typically found from a wind speed at 10 m and one at
hub height (K.4.3); [`WindShearProfile.speed_at`](/phonometry/reference/api/environment/wind-turbine-receptor/#windshearprofilespeed_at) then gives the wind
speed at any height by Equation (K.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `lower_speed_m_s` | Wind speed at `lower_height_m`, in m/s. |
| `upper_speed_m_s` | Wind speed at `upper_height_m`, in m/s. |
| `lower_height_m` | The lower measurement height, in m (10 m by default). |
| `upper_height_m` | The upper measurement height, in m (typically the hub height). |

**Returns:** A [`WindShearProfile`](/phonometry/reference/api/environment/wind-turbine-receptor/#windshearprofile).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a speed or height is not positive or the upper height is not above the lower one. |

## wind_turbine_low_frequency_level

```python
wind_turbine_low_frequency_level(
    sound_power_levels_db: ArrayLike,
    *,
    distance_m: ArrayLike,
    hub_height_m: ArrayLike,
    frequencies_hz: ArrayLike = ...,
    ground_correction_db: ArrayLike | None = None,
    air_attenuation_db_per_km: ArrayLike | None = None,
    facade_insulation_db: ArrayLike | None = None,
    a_weighted: bool = True,
) -> LowFrequencyLevel
```

Low frequency sound level at a receptor (Annex C, Equation (C.1)).

$$
L_{p,\mathrm{LF}} = L_{W,\mathrm{LF}} - 10 \lg(l^2 + h^2) - 11~\mathrm{dB} + \Delta L_\mathrm{g,LF} - \Delta L_\mathrm{a} - \Delta L_\sigma \tag{C.1}
$$

band by band, with $\Delta L_\mathrm{a} = \alpha \sqrt{l^2 + h^2}$
(the distance in km for $\alpha$ in dB/km) and 11 dB the
$10 \lg(4\pi)$ of the text, taken as printed. The contributions of
the relevant turbines are summed energetically per band, and the
equivalent level is the energy sum of the bands (C.3, C.5); the Danish
criterion of C.6.1 sums 10 Hz to 160 Hz, so pass those bands for it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_power_levels_db` | Band sound power levels from IEC 61400-11, in dB: one row per turbine, or one row for a single turbine. |
| `distance_m` | Horizontal distance $l$ from each tower to the receptor, in m. |
| `hub_height_m` | Hub height $h$ of each turbine, in m. |
| `frequencies_hz` | Nominal centre of each column, in Hz (10 Hz to 200 Hz by default, [`LOW_FREQUENCY_BANDS_HZ`](/phonometry/reference/api/environment/wind-turbine-receptor/#low_frequency_bands_hz)). |
| `ground_correction_db` | $\Delta L_\mathrm{g,LF}$ per band; `None` for Table C.2 (onshore, impedance class D). |
| `air_attenuation_db_per_km` | $\alpha$ per band, in dB/km, zero or positive (the ISO 9613-1 absorption coefficient, C.2); `None` for Table C.2, as printed (see [`LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM`](/phonometry/reference/api/environment/wind-turbine-receptor/#low_frequency_air_attenuation_db_per_km)). |
| `facade_insulation_db` | $\Delta L_\sigma$ per band, for an indoor level (for instance a row of [`LOW_FREQUENCY_FACADE_INSULATION_DB`](/phonometry/reference/api/environment/wind-turbine-receptor/#low_frequency_facade_insulation_db)); `None` for the outdoor level alone. |
| `a_weighted` | Add the A-weighting of Table C.4 (IEC 61672-1) to each band (the default), or give unweighted levels. |

**Returns:** A [`LowFrequencyLevel`](/phonometry/reference/api/environment/wind-turbine-receptor/#lowfrequencylevel).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a distance or height is not positive, an air attenuation coefficient is negative, a default table has no value at a supplied band, or `a_weighted` is not a boolean. |

## wind_turbine_rating_level

```python
wind_turbine_rating_level(
    equivalent_level_db: float,
    *,
    tonal_adjustment_db: float = 0.0,
    amplitude_modulation_adjustment_db: float = 0.0,
    impulsive_adjustment_db: float = 0.0,
) -> WindTurbineRatingLevel
```

Rating level of wind turbine sound (Annex A, A.1).

$L_\mathrm{r} = L_\mathrm{eq} + K$ with $K$ the most severe of
the tonal adjustment $K_\mathrm{T}$, the amplitude modulation
adjustment $K_\mathrm{am}$ and the impulsive adjustment
$K_\mathrm{I}$: only one type is applied at a time. Local regulation
usually defines the adjustments; the TS's examples are Table A.1 for
$K_\mathrm{T}$
([`tonal_adjustment_from_mean_audibility`](/phonometry/reference/api/environment/measurement/#tonal_adjustment_from_mean_audibility),
ISO 1996-2:2017 Table J.1, with its 3 dB-step variant), Figure A.1 for
$K_\mathrm{am}$ ([`amplitude_modulation_adjustment`](/phonometry/reference/api/environment/wind-turbine-receptor/#amplitude_modulation_adjustment)) and
ISO/PAS 1996-3 for $K_\mathrm{I}$
([`impulse_adjustment`](/phonometry/reference/api/environment/impulsive-sound/#impulse_adjustment)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `equivalent_level_db` | The equivalent continuous level, in dB. |
| `tonal_adjustment_db` | $K_\mathrm{T}$, in dB. |
| `amplitude_modulation_adjustment_db` | $K_\mathrm{am}$, in dB. |
| `impulsive_adjustment_db` | $K_\mathrm{I}$, in dB. |

**Returns:** A [`WindTurbineRatingLevel`](/phonometry/reference/api/environment/wind-turbine-receptor/#windturbineratinglevel).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a value is not finite or an adjustment is negative. |

## WindShearProfile

```python
WindShearProfile(
    heights_m: tuple[float, float],
    speeds_m_s: tuple[float, float],
    shear_exponent: float,
    *,
    typical: bool,
)
```

A wind profile through two measured heights (Annex K).

**Attributes**

| Name | Description |
| :--- | :--- |
| `heights_m` | The two measurement heights, lower first, in m. |
| `speeds_m_s` | The wind speeds measured there, in m/s. |
| `shear_exponent` | The power-law exponent $\alpha$ through the two points (Equation (K.2)). |
| `typical` | Whether $\alpha$ lies in the typical range [`TYPICAL_WIND_SHEAR_EXPONENT_RANGE`](/phonometry/reference/api/environment/wind-turbine-receptor/#typical_wind_shear_exponent_range) (K.4.3). |

### WindShearProfile.plot()

```python
WindShearProfile.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the power-law profile through the two measured points.

The logarithmic profile with the reference roughness length through
the lower point is drawn for comparison, as the binning wind speed of
9.3.2.1 assumes it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the power-law profile. |

**Returns:** The axes.

### WindShearProfile.speed_at()

```python
WindShearProfile.speed_at(
    height_m: ArrayLike,
) -> NDArray[np.float64] | float
```

The power-law wind speed at `height_m` (Equation (K.1)), in m/s.

## WindTurbineRatingLevel

```python
WindTurbineRatingLevel(
    equivalent_level_db: float,
    adjustments_db: Mapping[str, float],
    governing: str | None,
    rating_level_db: float,
)
```

The rating level of wind turbine sound (Annex A, A.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `equivalent_level_db` | The equivalent continuous level $L_\mathrm{eq}$, in dB. |
| `adjustments_db` | The three candidate adjustments, keyed `"tonal"`, `"amplitude_modulation"` and `"impulsive"`, in dB. |
| `governing` | The adjustment applied, the most severe of the three, or `None` when all three are zero. |
| `rating_level_db` | $L_\mathrm{r} = L_\mathrm{eq} + K$, in dB. |

### WindTurbineRatingLevel.plot()

```python
WindTurbineRatingLevel.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the three candidate adjustments with the governing one marked.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the adjustment bars. |

**Returns:** The axes.
