---
title: "emission.reference_sound_source"
description: "Reference sound sources: the performance requirements and the calibration of ISO 6926:2016."
sidebar:
  label: "reference_sound_source"
---

Reference sound sources: the performance requirements and the calibration of
ISO 6926:2016.

A reference sound source is the yardstick of every comparison method of the
ISO 3740 family: ISO 3741 in a reverberation room, ISO 3747 in situ, ISO 9295
in the 16 kHz octave band. ISO 6926 says what a source must do to serve
(clause 5) and how its sound power levels are calibrated (clauses 8 to 10).

**Requirements (clause 5).** The sound power output is steady: the standard
deviation under repeatability conditions of three repeated sound power levels
or five repeated sound pressure levels,

$$
\sigma_r = \sqrt{\frac{1}{N-1} \sum_{j=1}^{N} \left( L_{X,j} - \overline{L_X} \right)^2} \tag{Formula (1)}
$$

with $\overline{L_X}$ the *energy* average of the $N$
repetitions, does not exceed Table 1 (0,8 dB from 50 Hz to 80 Hz, 0,4 dB from
100 Hz to 160 Hz, 0,2 dB from 200 Hz to 20 kHz), and over the declared range
of its electrical or mechanical supply (the line voltage, say) no one-third
octave band varies by more than 0,3 dB either way. The spectrum is broadband: from
100 Hz to 10 000 Hz every one-third octave band lies within a range of 12 dB
and within 3 dB of its neighbours, and 16 dB and 4 dB over a range extended
beyond it (5.4). The directivity index $D_{\mathrm{I}i} = L_{pi} - \overline{L_p}$ (3.9) does not exceed +6 dB in any band from 100 Hz to
10 000 Hz (5.5), unless the source is labelled for reverberation rooms only.
Recalibration is due when a band has moved by more than 2,83 times Table 1
between two checks (5.6).

**Calibration in a hemi-anechoic room (clause 8).** The room meets the
broadband qualification of ISO 3745 Annex A (8.1), the source stands on the
reflecting plane and the levels are measured over a hemisphere of radius 2 m
(8.2.1). The sound power level under the reference meteorological conditions
of clause 4 (23,0 degC, 101,325 kPa) is

$$
L_W = \overline{L_p} + 10 \lg\frac{S}{S_0}\ \mathrm{dB} + C_1 + C_2 + C_3 \tag{Formula (2)}
$$

with $C_1 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + 5 \lg(\theta / \theta_0)$, $\theta_0$ = 314 K, the radiation impedance correction
$C_2$ from the manufacturer or from Annex A, and the air absorption
$C_3 = A_0 (1{,}005\,3 - 0{,}001\,2 A_0)^{1{,}6}$ with $A_0 = a(f) r$. Annex A gives $C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + n \lg (\theta/\theta_1)$, $\theta_1$ = 296 K, with $n$ = 15 for a
monopole below the knee frequency $f_\mathrm{k} = c/(2\pi d_0)$, 5 for a
monopole at or above it, 25 for an aerodynamic dipole at or above it and 7,5
when the radiation is unknown. Annex B replaces the 50 Hz, 63 Hz and 80 Hz
bands by sound intensity levels when those agree with the pressure levels
within Table B.1 from 50 Hz to 315 Hz. Table 2 gives the reproducibility
standard deviation from which clause 11 builds the expanded uncertainty.

The calibration is consumed where a comparison method asks for
$L_{W(\mathrm{RSS})}$: [`sound_power_comparison`](/phonometry/reference/api/power/sound-power-reverberation/#sound_power_comparison),
[`sound_energy_comparison`](/phonometry/reference/api/power/sound-power-reverberation/#sound_energy_comparison),
[`sound_power_in_situ`](/phonometry/reference/api/power/sound-power-in-situ/),
[`sound_energy_in_situ`](/phonometry/reference/api/power/sound-power-in-situ/#sound_energy_in_situ) and
[`high_frequency_sound_power_comparison`](/phonometry/reference/api/power/sound-power-high-frequency/#high_frequency_sound_power_comparison) accept a
[`ReferenceSourceCalibration`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibration) where they accept the levels, and read the
bands they need from it. The calibration holds $L_W$ under the
reference meteorological conditions, where $C_2$ carried the power the
source radiated during the calibration (8.4). ISO 3741 wants
$L_{W(\mathrm{RSS})}$ "corrected to the meteorological conditions at
the time of test" (Formulae (21) and (31)), and ISO 9295 carries its levels
to the reference conditions as ISO 3741 does (10.1), so for those methods the
calibration is read as $L_W - C_2$, with $C_2$ evaluated at the
test by the same formula the calibration used, as 8.4 asks
([`ReferenceSourceCalibration.sound_power_level_at`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibrationsound_power_level_at) with the test's
temperature and pressure). ISO 3747 instead corrects the reference source's
measured pressure levels "for speed, temperature and static pressure
according to the manufacturer's specifications" (Equation (9)), which puts
the source back at its calibration, and reads the calibrated levels as they
are.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## CalibrationConditions

```python
CalibrationConditions(
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    air_absorption_db_per_m: ArrayLike | None = None,
)
```

The air of a calibration on the 2 m hemisphere (ISO 6926 8.4).

The three travel together because Formula (2) reads them from the same
air: $C_1$ and the Annex A $C_2$ read its temperature and its
static pressure, and $C_3$ reads the attenuation coefficient
$a(f)$ that ISO 9613-1 gives for it. The defaults are the reference
meteorological conditions of clause 4, 23,0 degC and 101,325 kPa, with no
air absorption.

**Parameters**

| Name | Description |
| :--- | :--- |
| `temperature_c` | Air temperature during the calibration, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure during the calibration, in kilopascals. |
| `air_absorption_db_per_m` | $a(f)$ of ISO 9613-1 per band, or one value for every band, in dB/m, for $C_3$; `None` leaves $C_3 = 0$. It is held as a float64 copy. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a temperature that is not finite or not above absolute zero, a static pressure that is not finite and positive, or an air absorption that is not finite and non-negative. |

## knee_frequency

```python
knee_frequency(d0_m: float, *, speed_of_sound: float = 343.0) -> float
```

Knee frequency of the radiation efficiency (ISO 6926 Formula (A.1)).

$f_\mathrm{k} = c / (2 \pi d_0)$: the frequency at which the
radiation efficiency has dropped 3 dB from its high-frequency value.
ISO 6926:2016 describes $d_0$ as "half the characteristic source
dimension (see ISO 3745)", while ISO 3745:2012 3.14 defines the
characteristic source dimension, with the same symbol, as the distance
from the origin to the farthest corner of the reference box, already a
half dimension (see docs/ERRATA.md). The value passed here is the
$d_0$ that enters the formula, a radius-like length; the choice of
which length that is stays with the caller.

**Parameters**

| Name | Description |
| :--- | :--- |
| `d0_m` | $d_0$, in metres. |
| `speed_of_sound` | Speed of sound, in m/s (default 343). |

**Returns:** $f_\mathrm{k}$, in hertz.

## radiation_impedance_correction

```python
radiation_impedance_correction(
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    radiation: RadiationCharacter = 'unknown',
    frequencies_hz: ArrayLike | None = None,
    knee_frequency_hz: float | None = None,
) -> np.ndarray
```

The radiation impedance correction $C_2$ of ISO 6926 Annex A.

$C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + n \lg(\theta/ \theta_1)$, $\theta_1$ = 296 K and $\theta$ the air temperature
in kelvin, with $n$ = 7,5 for a source whose radiation is unknown
(A.5), 15 below and 5 at or above the knee frequency for a monopole
(A.2, A.3), and 25 at or above it for an aerodynamic dipole (A.4). Annex A
is informative: 8.4 prefers the manufacturer's value, and the formula the
calibration used should be the one the user applies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `temperature_c` | Air temperature at the test, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals. |
| `radiation` | `"unknown"` (default), `"monopole"` or `"dipole"`. |
| `frequencies_hz` | The band frequencies, in hertz; required for a monopole or a dipole, whose correction depends on the knee frequency. |
| `knee_frequency_hz` | $f_\mathrm{k}$ (see [`knee_frequency`](/phonometry/reference/api/power/reference-sound-source/#knee_frequency)), required for a monopole or a dipole. |

**Returns:** $C_2$ per band, in dB (one value without frequencies).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown radiation character, a monopole or dipole without frequencies and knee frequency, or a dipole band below the knee frequency, for which Annex A gives no formula. |

## reference_source_calibration

```python
reference_source_calibration(
    levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    arrangement: MicrophoneArrangement,
    background_levels_db: ArrayLike | None = None,
    maximum_levels_db: ArrayLike | None = None,
    conditions: CalibrationConditions | None = None,
    radiation: RadiationCharacter = 'unknown',
    knee_frequency_hz: float | None = None,
    c2_db: ArrayLike | None = None,
    intensity_sound_power_level_db: ArrayLike | None = None,
    room_qualification: FreeFieldCheck | None = None,
    coverage_factor: float = 1.96,
) -> ReferenceSourceCalibration
```

Calibrate a reference sound source in a hemi-anechoic room (ISO 6926 clause 8).

The one-third octave band levels over the 2 m hemisphere are corrected
for background position by position and energy-averaged as ISO 3745
prescribes ([`sound_power_anechoic`](/phonometry/reference/api/power/sound-power-anechoic/)), then
Formula (2) carries them to the sound power level under the reference
meteorological conditions with the $C_1$, $C_2$ and
$C_3$ of 8.4. The directivity index of each position (3.9) is its
level less the surface level; for traversing microphones 8.3.2 takes the
highest level seen on the traverse instead, which `maximum_levels_db`
carries. Annex B, the alternative at low frequencies, replaces the 50 Hz
to 80 Hz bands by the intensity levels when both agree within Table B.1
from 50 Hz to 315 Hz. B.2 asks for the directivity index of those three
bands from the intensity measurements too; the result keeps the one
from sound pressure, and [`ReferenceSourceCalibration.intensity_bands`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibration)
marks the bands whose level was replaced, as B.2 asks the report to.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | `(positions, bands)` time-averaged levels at the fixed positions or along the traverses of 8.2, in dB. |
| `frequencies_hz` | Nominal one-third octave mid-band frequencies, in hertz, ascending, from 50 Hz to 20 kHz. |
| `arrangement` | `"paths"` (meridional or spiral paths) or `"fixed"` (the 20 fixed positions or coaxial circular paths), which selects the column of Table 2. |
| `background_levels_db` | Background levels, per position or one spectrum, for the ISO 3745 correction; `None` applies none. |
| `maximum_levels_db` | For traverses, the highest level recorded on each (8.3.2), same shape as `levels_db`. |
| `conditions` | The [`CalibrationConditions`](/phonometry/reference/api/power/reference-sound-source/#calibrationconditions) of the air during the calibration, whose temperature and static pressure enter $C_1$ and the Annex A $C_2$ and whose $a(f)$ enters $C_3$; `None` (default) takes the reference meteorological conditions of clause 4 with no air absorption. |
| `radiation` | Radiation character for the Annex A $C_2$. |
| `knee_frequency_hz` | Knee frequency for a monopole or a dipole. |
| `c2_db` | The manufacturer's $C_2$, scalar or per band, which 8.4 prefers to Annex A; overrides `radiation`. A calibration made with it cannot be read at the conditions of a test, since only the manufacturer gives $C_2$ there (see [`ReferenceSourceCalibration.sound_power_level_at`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibrationsound_power_level_at)). |
| `intensity_sound_power_level_db` | Sound power levels from sound intensity per band (ISO 9614-3, Annex B), `nan` outside 50 Hz to 315 Hz; `None` applies no Annex B. |
| `room_qualification` | The [`check_free_field`](/phonometry/reference/api/power/free-field-qualification/#check_free_field) verdict of the room; 8.1 asks for a hemi-anechoic room qualified over the frequency range of interest, here the bands calibrated from sound pressure at 2 m (the bands Annex B takes from sound intensity are the ones clause 10 lets an unqualified room calibrate, and are left out). |
| `coverage_factor` | $k$ of the expanded uncertainty (1,96 in 11.2 for 95 %). |

**Returns:** [`ReferenceSourceCalibration`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for bands that are not ascending one-third octaves from 50 Hz to 20 kHz, no position, levels, background levels, maxima or a manufacturer's $C_2$ that are not finite, or inconsistent shapes. |

## reference_source_reproducibility_db

```python
reference_source_reproducibility_db(
    frequencies_hz: ArrayLike,
    *,
    environment: CalibrationEnvironment,
    arrangement: MicrophoneArrangement | None = None,
    bandwidth: BandWidth = 'one-third-octave',
) -> np.ndarray
```

Standard deviation of reproducibility of a calibration (ISO 6926 Table 2).

The one-third octave and octave columns of Table 2 are read separately,
as printed: the 3 150 Hz one-third octave band sits in the 200 Hz to
3 150 Hz row while the 4 000 Hz octave row begins at 4 000 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal mid-band frequencies, in hertz. |
| `environment` | `"hemi-anechoic"` or `"reverberation-room"`. |
| `arrangement` | In a hemi-anechoic room, `"paths"` (meridional or spiral) or `"fixed"` (20 discrete positions or coaxial circular paths); ignored in a reverberation room. |
| `bandwidth` | `"one-third-octave"` (default) or `"octave"`. |

**Returns:** $\sigma_R$ per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band outside Table 2 or an unknown option. |

## ReferenceSoundSourceVerdict

```python
ReferenceSoundSourceVerdict(
    frequencies_hz: np.ndarray,
    sound_power_level_db: np.ndarray,
    repeatability_db: np.ndarray | None,
    supply_variation_db: np.ndarray | None,
    directivity_index_db: np.ndarray | None,
    reverberation_rooms_only: bool,
)
```

Whether a source meets the performance requirements of ISO 6926 clause 5.

Only what was measured is a field. The limits of clause 5 (Table 1, the
0,3 dB of the supply, the 12 dB and 16 dB ranges, the 3 dB and 4 dB steps,
the +6 dB of the directivity) are read from the bands as properties, and so
are the spectrum figures they are compared with, so a verdict cannot be
built against another limit.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third octave bands, contiguous and ascending, in hertz. |
| `sound_power_level_db` | The calibrated $L_W$ per band. |
| `repeatability_db` | $\sigma_r$ of Formula (1) per band, or `None` when no repetitions were given. |
| `supply_variation_db` | The largest change of $L_W$ per band over the declared range of the electrical or mechanical supply (5.2), or `None` when not given. |
| `directivity_index_db` | The highest directivity index per band, or `None` when not given. |
| `reverberation_rooms_only` | Whether the source is labelled "For use as a reference sound source in reverberation test rooms complying with ISO 3741", which lifts 5.5. |

### ReferenceSoundSourceVerdict.adjacent_limit_db

*property*

The step each band is held to (5.4), in dB.

**Returns:** 3 dB from 100 Hz to 10 000 Hz, 4 dB where a neighbour lies in an extended range; per band, the pair that comes closest to its limit.

### ReferenceSoundSourceVerdict.adjacent_step_db

*property*

The largest difference from a neighbouring band, per band (5.4), in dB.

### ReferenceSoundSourceVerdict.core_range_db

*property*

The spread of $L_W$ from 100 Hz to 10 000 Hz, in dB.

### ReferenceSoundSourceVerdict.core_range_limit_db

*property*

The 12 dB of 5.4, in dB.

### ReferenceSoundSourceVerdict.directivity_limit_db

*property*

The +6 dB of 5.5, in dB.

### ReferenceSoundSourceVerdict.directivity_met

*property*

5.5: the directivity index at most +6 dB from 100 Hz to 10 000 Hz.

**Returns:** The verdict, `True` for a source labelled for reverberation rooms only, or `None` when not judged.

### ReferenceSoundSourceVerdict.extended_range_db

*property*

The spread over every band when the range is extended, else `nan`.

### ReferenceSoundSourceVerdict.extended_range_limit_db

*property*

The 16 dB of 5.4, in dB.

### ReferenceSoundSourceVerdict.frequency_range_met

*property*

Whether every band from 100 Hz to 10 000 Hz is present (5.4).

### ReferenceSoundSourceVerdict.not_judged

*property*

The requirements without data, by name.

### ReferenceSoundSourceVerdict.passes

*property*

Whether every requirement of clause 5 is judged and met (5.1).

**Returns:** `True` when the source may be declared in compliance.

### ReferenceSoundSourceVerdict.plot()

```python
ReferenceSoundSourceVerdict.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each requirement as a share of its limit, per band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the step curve. |

**Returns:** The axes.

### ReferenceSoundSourceVerdict.repeatability_limit_db

*property*

The Table 1 limit on $\sigma_r$ per band, in dB (5.2).

**Returns:** 0,8 dB up to 80 Hz, 0,4 dB up to 160 Hz, 0,2 dB above.

### ReferenceSoundSourceVerdict.spectrum_met

*property*

5.4: the 12 dB range and 3 dB steps, 16 dB and 4 dB when extended.

**Returns:** The verdict.

### ReferenceSoundSourceVerdict.stability_met

*property*

5.2: $\sigma_r$ within Table 1 in every band.

**Returns:** The verdict, or `None` when not judged.

### ReferenceSoundSourceVerdict.supply_limit_db

*property*

The 0,3 dB either way of 5.2, in dB.

### ReferenceSoundSourceVerdict.supply_met

*property*

5.2: no band moves by more than 0,3 dB over the declared supply range.

**Returns:** The verdict, or `None` when not judged.

## ReferenceSourceCalibration

```python
ReferenceSourceCalibration(
    frequencies_hz: np.ndarray,
    sound_power_level_db: np.ndarray,
    surface_pressure_level_db: np.ndarray,
    directivity_index_db: np.ndarray,
    c1_db: float,
    c2_db: np.ndarray,
    c3_db: np.ndarray,
    expanded_uncertainty_db: np.ndarray,
    coverage_factor: float,
    arrangement: str,
    intensity_bands: np.ndarray,
    intensity_agreement: bool | None,
    room_qualified: bool | None,
    radiation: str | None,
    knee_frequency_hz: float | None,
)
```

Calibrated sound power levels of a reference sound source (ISO 6926 8.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal one-third octave mid-band frequencies, in hertz, ascending. |
| `sound_power_level_db` | $L_W$ under the reference meteorological conditions, per band, in dB re 1 pW; the 50 Hz to 80 Hz bands come from sound intensity where Annex B validated them. |
| `surface_pressure_level_db` | $\overline{L_p}$ over the 2 m hemisphere after the background correction, per band. |
| `directivity_index_db` | $D_{\mathrm{I}i}$ per position or traverse and band (3.9), `(positions, bands)`. |
| `c1_db` | $C_1$, in dB. |
| `c2_db` | $C_2$ per band, in dB. |
| `c3_db` | $C_3$ per band, in dB. |
| `expanded_uncertainty_db` | $k \sigma_R$ of Table 2 per band. |
| `coverage_factor` | $k$. |
| `arrangement` | `"paths"` or `"fixed"`. |
| `intensity_bands` | Per band, whether the level came from the sound intensity of Annex B. |
| `intensity_agreement` | Whether the pressure and intensity levels agree within Table B.1 from 50 Hz to 315 Hz, or `None` without intensity levels. |
| `room_qualified` | Whether the room qualification given meets 8.1 for these bands at 2 m, or `None` when none was given. |
| `radiation` | The radiation character whose Annex A $C_2$ the calibration used, or `None` when it used the manufacturer's value. |
| `knee_frequency_hz` | The knee frequency of that $C_2$, or `None`. |

### ReferenceSourceCalibration.a_weighted_expanded_uncertainty_db

*property*

The expanded uncertainty of `sound_power_level_a_db` (Table 2).

**Returns:** $k \sigma_R$ of the A-weighted row, in dB.

### ReferenceSourceCalibration.a_weighted_range_hz

*property*

The bands the A-weighted total covers: those of ISO 3744 Annex E.

**Returns:** `(lowest, highest)` nominal frequency, in hertz.

### ReferenceSourceCalibration.maximum_directivity_index_db

*property*

The highest directivity index over the positions, per band (5.5).

**Returns:** One value per band, in dB.

### ReferenceSourceCalibration.plot()

```python
ReferenceSourceCalibration.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the calibrated spectrum with its expanded uncertainty.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the level bars. |

**Returns:** The axes.

### ReferenceSourceCalibration.sound_power_level_a_db

*property*

A-weighted sound power level over `a_weighted_range_hz` (5.3).

**Returns:** $L_{WA}$, in dB re 1 pW.

### ReferenceSourceCalibration.sound_power_level_at()

```python
ReferenceSourceCalibration.sound_power_level_at(
    frequencies_hz: ArrayLike,
    *,
    bandwidth: BandWidth = 'one-third-octave',
    temperature_c: float | None = None,
    static_pressure_kpa: float | None = None,
) -> np.ndarray
```

The calibrated level in the bands a comparison method asks for.

Without meteorological conditions, $L_W$ under the reference
conditions, as calibrated. With the temperature and the static
pressure of a test, the power the source radiates there,
$L_W - C_2$, with $C_2$ evaluated at the test by the Annex A
formula the calibration used (8.4: the formula of the calibration
laboratory "should be the same as the one used by the user"); ISO 3741
Formulae (21) and (31) ask for that level. An octave band is the energy
sum of its three one-third octave bands, all of which must have been
calibrated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal mid-band frequencies, in hertz. |
| `bandwidth` | `"one-third-octave"` (default) or `"octave"`. |
| `temperature_c` | Air temperature at the test, in degrees Celsius; `None` (default), with `static_pressure_kpa`, reads the reference conditions. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals, given together with `temperature_c`. |

**Returns:** The level per requested band, in dB re 1 pW.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band the calibration does not cover, an octave asked at a frequency that is not an octave mid-band, only one of the two conditions, or conditions asked of a calibration that used the manufacturer's $C_2$, whose value at the test only the manufacturer gives. |

## ReferenceSourceDriftResult

```python
ReferenceSourceDriftResult(
    frequencies_hz: np.ndarray,
    change_db: np.ndarray,
)
```

Whether a reference sound source has drifted enough to be recalibrated.

The limit is the clause's, 2,83 times Table 1, read from the bands as
`limit_db`, so a result cannot be built against another one.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third octave bands, in hertz. |
| `change_db` | The latest level less the reference one, per band. |

### ReferenceSourceDriftResult.limit_db

*property*

2,83 times the Table 1 value of each band (5.6), in dB.

### ReferenceSourceDriftResult.passes

*property*

Whether every band stays within 2,83 times Table 1.

**Returns:** `True` when no recalibration is called for.

### ReferenceSourceDriftResult.plot()

```python
ReferenceSourceDriftResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the change of each band against its limit.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the change bars. |

**Returns:** The axes.

### ReferenceSourceDriftResult.recalibration_required

*property*

5.6.3: a band moved by more than 2,83 times Table 1.

**Returns:** The opposite of `passes`.

## repeatability_standard_deviation

```python
repeatability_standard_deviation(levels_db: ArrayLike) -> np.ndarray
```

Standard deviation under repeatability conditions (ISO 6926 Formula (1)).

$\sigma_r = \sqrt{\sum_j (L_{X,j} - \overline{L_X})^2 / (N - 1)}$ with
$\overline{L_X}$ the energy average of the repetitions, as clause
8.4 defines it, not their arithmetic mean.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | `(N, bands)` repeated levels (sound power or sound pressure), or `(N,)` for one band, in dB. |

**Returns:** $\sigma_r$ per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than two repetitions or non-finite levels. |

## verify_reference_sound_source

```python
verify_reference_sound_source(
    calibration: ReferenceSourceCalibration | ArrayLike,
    *,
    frequencies_hz: ArrayLike | None = None,
    repeated_levels_db: ArrayLike | None = None,
    supply_variation_db: ArrayLike | None = None,
    directivity_index_db: ArrayLike | None = None,
    reverberation_rooms_only: bool = False,
) -> ReferenceSoundSourceVerdict
```

May this source be declared a reference sound source? (ISO 6926 clause 5).

Judges the temporal steadiness (5.2, Table 1), the variation over the
declared range of the supply (5.2), the spectrum (5.4) and the directivity
(5.5). A calibration made here brings its bands, levels and
directivity indices; a source calibrated elsewhere, for instance in a
reverberation room by clause 9, passes its one-third octave levels and
frequencies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `calibration` | A [`ReferenceSourceCalibration`](/phonometry/reference/api/power/reference-sound-source/#referencesourcecalibration), or the calibrated $L_W$ per band, in dB re 1 pW. |
| `frequencies_hz` | The bands of a plain level array, ascending one-third octave mid-bands, in hertz; omitted with a calibration. |
| `repeated_levels_db` | `(3, bands)` sound power levels or `(5, bands)` sound pressure levels measured in succession (8.3.3, 9.3.2); `None` leaves the steadiness of 5.2 unjudged. |
| `supply_variation_db` | The largest change of the sound power level in each band over the declared range of the electrical or mechanical supply, the line voltage for instance (5.2), per band or one value for every band, in dB; `None` leaves that requirement unjudged. |
| `directivity_index_db` | The directivity index per position and band, or the highest per band, for a plain level array (a calibration brings its own). |
| `reverberation_rooms_only` | The source is labelled for reverberation test rooms complying with ISO 3741 only, and 5.5 does not apply. |

**Returns:** [`ReferenceSoundSourceVerdict`](/phonometry/reference/api/power/reference-sound-source/#referencesoundsourceverdict).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for bands that are not ascending contiguous one-third octaves, repetitions other than three or five, or shapes that do not match. |

## verify_reference_source_drift

```python
verify_reference_source_drift(
    reference_levels_db: ArrayLike,
    latest_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
) -> ReferenceSourceDriftResult
```

Has the source drifted beyond what ISO 6926 5.6 allows?

The same check serves 5.6.2 (two calibrations), 5.6.3 (the regular
one-third octave band levels at fixed reference points) and 5.6.4 (the
surface levels of a source kept in one place): a change larger than 2,83
times Table 1 in any band calls for recalibration.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_levels_db` | The levels of the earlier check, per band, in dB. |
| `latest_levels_db` | The levels of the latest check, same bands. |
| `frequencies_hz` | Nominal one-third octave mid-bands, 50 Hz to 20 kHz, in hertz. |

**Returns:** [`ReferenceSourceDriftResult`](/phonometry/reference/api/power/reference-sound-source/#referencesourcedriftresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that do not span the bands or are not finite. |
