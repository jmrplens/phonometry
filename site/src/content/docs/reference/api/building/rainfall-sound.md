---
title: "building.measurement.rainfall_sound"
description: "Sound of rain on roofs, roof windows and rooflights, measured in the laboratory with artificial rain (ISO 10140-1:2021 Annex K, ISO 10140-5:2021 Annexes H and I)."
sidebar:
  label: "rainfall_sound"
---

Sound of rain on roofs, roof windows and rooflights, measured in the
laboratory with artificial rain (ISO 10140-1:2021 Annex K, ISO 10140-5:2021
Annexes H and I).

Rain is an impact source that falls on the roof rather than a noise that comes
through it, so ISO 10140-1 measures it as impact sound: a tank with a
perforated base drops water on the specimen at a controlled rate, and the
sound radiated into the test room below is reported as a **sound intensity
level** $L_I$, the sound power per unit area of the specimen referred to
$10^{-12}$ W/m² (K.1). Per unit area, because only part of a large roof
is wetted and the power scales with the area the rain actually excites.

**The rain.** Real rain is classed by rate, drop size and fall velocity
(Table K.1, after IEC 60721-2-2:1988, [`RAINFALL_CLASSIFICATION`](/phonometry/reference/api/building/rainfall-sound/#rainfall_classification)). The
laboratory reproduces two of the classes at their upper limits, "since larger
drops produce most of the sound generated": heavy rain, 40 mm/h of 5 mm drops
at 7 m/s, which is mandatory and the one products are compared with, and
intense rain, 15 mm/h of 2 mm drops at 4 m/s (ISO 10140-5:2021 Table H.1,
[`ARTIFICIAL_RAIN`](/phonometry/reference/api/building/rainfall-sound/#artificial_rain)). The generator is checked by its rainfall rate, which
has to stay within 2 mm/h of the nominal value ([`verify_rain_generator`](/phonometry/reference/api/building/rainfall-sound/#verify_rain_generator),
[`rainfall_rate`](/phonometry/reference/api/building/rainfall-sound/#rainfall_rate)).

**The level.** From the room-averaged sound pressure level $L_\mathrm{pr}$,
the reverberation time $T$ and the volume $V$ of the test room and
the area $S_\mathrm{e}$ the rain excites,

$$
L_I = L_\mathrm{pr} - 10 \log_{10}(T/T_0) + 10 \log_{10}(V/V_0) - 14 - 10 \log_{10}(S_\mathrm{e}/S_0)
$$

(Formula (K.1), $T_0 = 1$ s, $V_0 = 1$ m³, $S_0 = 1$ m²),
which is the diffuse-field sound power $L_p + 10 \log_{10}(A/4)$ with the
Sabine area $A = 0.16\,V/T$ written out and divided by the excited area.
With three positions of the generator on a large specimen the three levels are
added energetically and $S_\mathrm{e}$ is three times the perforated area
of the tank (K.4.2). The alternative of K.4.3 measures the intensity directly,
$L_I = L_{I\mathrm{m}} + 10 \log_{10}(S_\mathrm{m}/S_\mathrm{e})$
(Formula (K.4)). The 18 bands 100 Hz to 5 000 Hz combine into the A-weighted
level $L_{I\mathrm{A}} = 10 \log_{10} \sum 10^{0.1(L_{Ij} + C_j)}$
(Formula (K.2)) with the $C_j$ of Table K.2 ([`RAINFALL_A_WEIGHTING`](/phonometry/reference/api/building/rainfall-sound/#rainfall_a_weighting)),
and three bands into an octave by Formula (K.3).

**The reference specimen.** For comparison between laboratories, the levels
are normalized with the result for a 6 mm glass pane of 1,25 m by 1,5 m under
heavy rain (K.6, ISO 10140-5:2021 Annex I): its measured level is corrected to
the reference loss factor of Table I.1, $L_{I,\mathrm{m,ref}} = L_{I,\mathrm{ref}} + 10 \log_{10}(\eta/\eta_\mathrm{ref})$ with
$\eta = 2.2/(f T_\mathrm{s})$ (Formulas (I.1) and (I.2)), and the
difference from the reference level of the same table is the correction
$\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} - L_{I\mathrm{c,ref}}$
(Formula (I.3)) that every later specimen subtracts,
$L_{I\mathrm{norm}} = L_I - \Delta L_{I\mathrm{c}}$ (Formula (K.5)).

Citations are to ISO 10140-1:2021 and ISO 10140-5:2021. Both tables of the
reference specimen and the rain types are printed identically in
ISO 10140-5:2010/Amd 1:2014, where they first appeared.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ARTIFICIAL_RAIN

*Constant* (`mapping`).

```python
ARTIFICIAL_RAIN = {'intense': ArtificialRain(rainfall_rate_mm_h=15.0, median_drop_diameter_mm=2.0, fall_velocity_m_s=4.0, hole_diameter_mm=(0.3, 0.5), holes_per_m2=25.0, fall_height_m=1.0, rainfall_rate_tolerance_mm_h=2.0, drop_diameter_tolerance_mm=0.5, fall_velocity_tolerance_m_s=1.0), 'heavy': ArtificialRain(rainfall_rate_mm_h=40.0, median_drop_diameter_mm=5.0, fall_velocity_m_s=7.0, hole_diameter_mm=(1.0, 1.0), holes_per_m2=60.0, fall_height_m=3.5, rainfall_rate_tolerance_mm_h=2.0, drop_diameter_tolerance_mm=0.5, fall_velocity_tolerance_m_s=1.0)}
```

## ArtificialRain

```python
ArtificialRain(
    rainfall_rate_mm_h: float,
    median_drop_diameter_mm: float,
    fall_velocity_m_s: float,
    hole_diameter_mm: tuple[float, float],
    holes_per_m2: float,
    fall_height_m: float,
    *,
    rainfall_rate_tolerance_mm_h: float = 2.0,
    drop_diameter_tolerance_mm: float = 0.5,
    fall_velocity_tolerance_m_s: float = 1.0,
)
```

One type of artificial rain and the tank that makes it (ISO 10140-5 Annex H).

**Attributes**

| Name | Description |
| :--- | :--- |
| `rainfall_rate_mm_h` | Rainfall rate, in mm/h: the depth of water the rain would leave on a horizontal surface in one hour (Table H.1). |
| `median_drop_diameter_mm` | Volume median drop diameter, in mm: half of the water falls in drops larger than it (Table H.1). |
| `fall_velocity_m_s` | Fall velocity at the specimen, in m/s (Table H.1). |
| `hole_diameter_mm` | Diameter of the holes in the perforated base, as a `(lower, upper)` range, in mm (Table H.2, row 1). |
| `holes_per_m2` | Approximate number of holes per square metre of the base (Table H.2, row 2). |
| `fall_height_m` | Approximate fall height from the base to the specimen, in m (Table H.2, row 3). |
| `rainfall_rate_tolerance_mm_h` | How far the rainfall rate may depart from its nominal value, in mm/h (H.1). |
| `drop_diameter_tolerance_mm` | Half-width of the window around the median drop diameter that half the drops should fall in, in mm (H.1). |
| `fall_velocity_tolerance_m_s` | Half-width of the window around the fall velocity that half the drops should fall in, in m/s (H.1). |

## RAINFALL_A_WEIGHTING

*Constant* (`mapping`).

```python
RAINFALL_A_WEIGHTING = {100.0: -19.1, 125.0: -16.1, 160.0: -13.4, 200.0: -10.9, 250.0: -8.6, 315.0: -6.6, 400.0: -4.8, 500.0: -3.2, 630.0: -1.9, 800.0: -0.8, 1000.0: 0.0, 1250.0: 0.6, 1600.0: 1.0, 2000.0: 1.2, 2500.0: 1.3, 3150.0: 1.2, 4000.0: 1.0, 5000.0: 0.5}
```

## RAINFALL_CLASSIFICATION

*Constant* (`mapping`).

```python
RAINFALL_CLASSIFICATION = {'moderate': RainfallType(rainfall_rate_mm_h=(None, 4.0), drop_diameter_mm=(0.5, 1.0), fall_velocity_m_s=(1.0, 2.0)), 'intense': RainfallType(rainfall_rate_mm_h=(None, 15.0), drop_diameter_mm=(1.0, 2.0), fall_velocity_m_s=(2.0, 4.0)), 'heavy': RainfallType(rainfall_rate_mm_h=(None, 40.0), drop_diameter_mm=(2.0, 5.0), fall_velocity_m_s=(5.0, 7.0)), 'cloudburst': RainfallType(rainfall_rate_mm_h=(100.0, None), drop_diameter_mm=(3.0, None), fall_velocity_m_s=(6.0, None))}
```

## rainfall_rate

```python
rainfall_rate(
    collected_volume_litres: float,
    collection_area_m2: float,
    duration_s: float,
) -> float
```

Rainfall rate from the water collected over an area and a time (H.2.3).

The periodic check of a tank generator is "collecting the water over a
given area over a precisely measured time period": the rate is the depth
of that water, one litre per square metre being one millimetre, scaled to
one hour (the definition under Table H.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `collected_volume_litres` | Volume of water collected, in litres. |
| `collection_area_m2` | Horizontal area it was collected over, in m². |
| `duration_s` | Collection time, in seconds. |

**Returns:** The rainfall rate, in mm/h.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is not positive and finite. |

## rainfall_reference_correction

```python
rainfall_reference_correction(
    l_i_ref_db: ArrayLike,
    structural_reverberation_time_s: ArrayLike,
    frequencies_hz: ArrayLike | None = None,
) -> RainfallReferenceCorrection
```

Correction $\Delta L_{I\mathrm{c}}$ of a laboratory (ISO 10140-5 I.2).

The small reference specimen is a single 6 mm glass pane of 1,25 m by
1,5 m, mounted as a window pane of ISO 10140-1:2021 Annex D and wetted by
heavy rain centred on it. Its structural reverberation time gives its
loss factor, $\eta = 2.2/(f T_\mathrm{s})$ (Formula (I.1)), and its
measured intensity level is brought to the reference loss factor of
Table I.1, $L_{I,\mathrm{m,ref}} = L_{I,\mathrm{ref}} + 10 \log_{10}(\eta/\eta_\mathrm{ref})$ (Formula (I.2)): a pane mounted more
lossily radiates less, and the correction removes that part of the
difference, which belongs to the mounting and not to the laboratory's
rain. What remains, $\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} - L_{I\mathrm{c,ref}}$ (Formula (I.3)), is subtracted from every specimen
the laboratory measures (ISO 10140-1:2021 Formula (K.5)). No reference
specimen is defined for large specimens (I.3).

$f$ in Formula (I.1) is taken as the band centre frequency given.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_i_ref_db` | $L_{I,\mathrm{ref}}$ of the reference specimen per band, in dB re 1 pW/m² (e.g. `rainfall_sound(...).l_i_db`). |
| `structural_reverberation_time_s` | Its structural reverberation time per band, measured to ISO 10140-4, in s. |
| `frequencies_hz` | Band centre frequencies, in Hz, each one of the 18 bands of Table I.1 (100 Hz to 5 000 Hz); `None` takes all 18. |

**Returns:** A [`RainfallReferenceCorrection`](/phonometry/reference/api/building/rainfall-sound/#rainfallreferencecorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in length, a level is not finite, a time or frequency is not positive, or a band is not in Table I.1. |

## RAINFALL_REFERENCE_INTENSITY_DB

*Constant* (`mapping`).

```python
RAINFALL_REFERENCE_INTENSITY_DB = {100.0: 45.0, 125.0: 45.0, 160.0: 46.0, 200.0: 46.0, 250.0: 47.0, 315.0: 47.0, 400.0: 47.0, 500.0: 47.0, 630.0: 47.0, 800.0: 46.0, 1000.0: 44.0, 1250.0: 42.0, 1600.0: 43.0, 2000.0: 46.0, 2500.0: 51.0, 3150.0: 50.0, 4000.0: 46.0, 5000.0: 44.0}
```

## RAINFALL_REFERENCE_LOSS_FACTOR_DB

*Constant* (`mapping`).

```python
RAINFALL_REFERENCE_LOSS_FACTOR_DB = {100.0: -10.0, 125.0: -11.0, 160.0: -11.0, 200.0: -12.0, 250.0: -13.0, 315.0: -13.0, 400.0: -14.0, 500.0: -14.0, 630.0: -15.0, 800.0: -15.0, 1000.0: -16.0, 1250.0: -17.0, 1600.0: -17.0, 2000.0: -18.0, 2500.0: -18.0, 3150.0: -19.0, 4000.0: -19.0, 5000.0: -20.0}
```

## rainfall_sound

```python
rainfall_sound(
    l_pr_db: ArrayLike,
    reverberation_time_s: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    excited_area_m2: float,
    background_db: ArrayLike | None = None,
    reference_correction: RainfallReferenceCorrection | ArrayLike | None = None,
) -> RainfallSoundResult
```

Sound intensity level of a specimen under artificial rain (K.4.2).

While the rain falls steadily on the specimen, the room-averaged sound
pressure level $L_\mathrm{pr}$ and the reverberation time $T$
of the test room are measured to ISO 10140-4, and each band gives

$$
L_I = L_\mathrm{pr} - 10 \log_{10}(T/T_0) + 10 \log_{10}(V/V_0) - 14 - 10 \log_{10}(S_\mathrm{e}/S_0)
$$

(Formula (K.1)). A small specimen (a roof window or rooflight, about
1,25 m by 1,5 m) is wetted from one position and $S_\mathrm{e}$ is
its area; a large one (10 m² to 20 m²) from three, whose levels are added
energetically, and $S_\mathrm{e}$ is three times the perforated
area of the tank. The 18 bands 100 Hz to 5 000 Hz give the A-weighted
level $L_{I\mathrm{A}}$ of Formula (K.2).

With the correction of the laboratory's reference specimen
([`rainfall_reference_correction`](/phonometry/reference/api/building/rainfall-sound/#rainfall_reference_correction)), the levels are also normalized,
$L_{I\mathrm{norm}} = L_I - \Delta L_{I\mathrm{c}}$ (Formula (K.5)),
for comparison between laboratories.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_pr_db` | Room-averaged sound pressure level per band, in dB: `(bands,)` for one position of the rain generator or `(positions, bands)` for several, which are added energetically. |
| `reverberation_time_s` | Reverberation time of the test room per band, in s. |
| `frequencies_hz` | Band centre frequencies, in Hz. |
| `volume_m3` | Volume of the test room, in m³. |
| `excited_area_m2` | Area of the specimen directly excited by the rain, $S_\mathrm{e}$, in m². |
| `background_db` | Background noise level per band, in dB, or `None`. When given, each position's level is corrected by ISO 10140-4 ([`background_correction`](/phonometry/reference/api/building/lab-insulation/#background_correction)) before the sum. |
| `reference_correction` | The laboratory correction: a [`RainfallReferenceCorrection`](/phonometry/reference/api/building/rainfall-sound/#rainfallreferencecorrection) covering every band, or $\Delta L_{I\mathrm{c}}$ per band in dB, or `None`. |

**Returns:** A [`RainfallSoundResult`](/phonometry/reference/api/building/rainfall-sound/#rainfallsoundresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a level is not finite, a time, frequency, volume or area is not positive, or a band has no correction. |

## rainfall_sound_from_intensity

```python
rainfall_sound_from_intensity(
    l_im_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    measuring_area_m2: float,
    excited_area_m2: float,
    reference_correction: RainfallReferenceCorrection | ArrayLike | None = None,
) -> RainfallSoundResult
```

Sound intensity level of a specimen under rain, measured directly (K.4.3).

The alternative of K.4.3 measures the intensity with a probe over a
surface $S_\mathrm{m}$ enclosing the specimen (ISO 15186-1, in any
room meeting its field indicator and background requirements), and
refers it to the excited area,
$L_I = L_{I\mathrm{m}} + 10 \log_{10}(S_\mathrm{m}/S_\mathrm{e})$
(Formula (K.4)). The A-weighted level, the octaves and the normalization
then follow as in K.4.2.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_im_db` | Sound intensity level measured over the surface, per band, in dB re 1 pW/m². |
| `frequencies_hz` | Band centre frequencies, in Hz. |
| `measuring_area_m2` | Area of the measuring surface $S_\mathrm{m}$, in m². |
| `excited_area_m2` | Area of the specimen directly excited by the rain, $S_\mathrm{e}$, in m². |
| `reference_correction` | The laboratory correction, as for [`rainfall_sound`](/phonometry/reference/api/building/rainfall-sound/#rainfall_sound), or `None`. |

**Returns:** A [`RainfallSoundResult`](/phonometry/reference/api/building/rainfall-sound/#rainfallsoundresult) with `method="intensity"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a level is not finite, or a frequency or area is not positive. |

## RainfallReferenceCorrection

```python
RainfallReferenceCorrection(
    frequencies_hz: np.ndarray,
    l_i_ref_db: np.ndarray,
    structural_reverberation_time_s: np.ndarray,
    loss_factor: np.ndarray,
    reference_loss_factor: np.ndarray,
    l_i_m_ref_db: np.ndarray,
    l_ic_ref_db: np.ndarray,
    correction_db: np.ndarray,
)
```

The normalization correction from the reference glass pane (Annex I).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave band centre frequencies, in Hz. |
| `l_i_ref_db` | Measured sound intensity level of the reference specimen, $L_{I,\mathrm{ref}}$, in dB re 1 pW/m². |
| `structural_reverberation_time_s` | Its structural reverberation time $T_\mathrm{s}$, in s. |
| `loss_factor` | Its total loss factor $\eta = 2.2/(f T_\mathrm{s})$ (Formula (I.1)), a linear ratio. |
| `reference_loss_factor` | The reference loss factor $\eta_\mathrm{ref}$ of Table I.1 as a linear ratio, like `loss_factor`: $10^{x/10}$ of the decibel value $x$ the table prints ([`RAINFALL_REFERENCE_LOSS_FACTOR_DB`](/phonometry/reference/api/building/rainfall-sound/#rainfall_reference_loss_factor_db)). |
| `l_i_m_ref_db` | The level corrected to the reference loss factor, $L_{I,\mathrm{m,ref}}$, in dB (Formula (I.2)). |
| `l_ic_ref_db` | The reference level $L_{I\mathrm{c,ref}}$ of Table I.1, in dB. |
| `correction_db` | $\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} - L_{I\mathrm{c,ref}}$, in dB (Formula (I.3)). |

### RainfallReferenceCorrection.plot()

```python
RainfallReferenceCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the corrected reference level against Table I.1.

The gap between the two curves is the correction every specimen of
the laboratory is normalized by. Requires matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

## RainfallSoundResult

```python
RainfallSoundResult(
    frequencies_hz: np.ndarray,
    l_i_db: np.ndarray,
    l_ia_db: float | None,
    method: str,
    correction_db: np.ndarray | None = None,
    l_i_norm_db: np.ndarray | None = None,
    l_ia_norm_db: float | None = None,
)
```

Sound intensity level radiated by a specimen under rain (Annex K).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave band centre frequencies, in Hz. |
| `l_i_db` | Sound intensity level $L_I$ per band, in dB re 1 pW/m² (Formula (K.1) or (K.4)). |
| `l_ia_db` | A-weighted sound intensity level $L_{I\mathrm{A}}$, in dB (Formula (K.2)), or `None` when the 18 bands 100 Hz to 5 000 Hz are not all present. |
| `method` | `"pressure"` (K.4.2) or `"intensity"` (K.4.3). |
| `correction_db` | The laboratory correction $\Delta L_{I\mathrm{c}}$ per band, in dB, or `None` when the levels were not normalized. |
| `l_i_norm_db` | Normalized level $L_{I\mathrm{norm}} = L_I - \Delta L_{I\mathrm{c}}$ per band, in dB (Formula (K.5)), or `None`. |
| `l_ia_norm_db` | Its A-weighted level $L_{I\mathrm{Anorm}}$, in dB, or `None`. |

### RainfallSoundResult.octave_bands()

```python
RainfallSoundResult.octave_bands(
    *,
    normalized: bool = False,
) -> tuple[np.ndarray, np.ndarray]
```

`(octave centres in Hz, LIoct in dB)` by Formula (K.3).

$L_{I\mathrm{oct}} = 10 \log_{10} \sum_{j=1}^{3} 10^{0.1 L_{I,j}}$
over the three one-third-octave bands of each octave present.

**Parameters**

| Name | Description |
| :--- | :--- |
| `normalized` | Combine $L_{I\mathrm{norm}}$ instead of $L_I$. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `normalized` is set on levels that were not normalized. |

### RainfallSoundResult.plot()

```python
RainfallSoundResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the sound intensity level per band, normalized when available.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### RainfallSoundResult.sound_power_levels()

```python
RainfallSoundResult.sound_power_levels(
    specimen_area_m2: float,
) -> np.ndarray
```

Sound power level radiated by the whole specimen, per band.

$L_W = L_I + 10 \log_{10}(S/S_0)$ (the NOTE to Formula (K.2)),
with $S$ the area of the whole specimen.

**Parameters**

| Name | Description |
| :--- | :--- |
| `specimen_area_m2` | Area of the specimen, in m². |

**Returns:** $L_W$ per band, in dB re 1 pW.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the area is not positive and finite. |

## RainfallType

```python
RainfallType(
    rainfall_rate_mm_h: tuple[float | None, float | None],
    drop_diameter_mm: tuple[float | None, float | None],
    fall_velocity_m_s: tuple[float | None, float | None],
)
```

One class of natural rain (ISO 10140-1:2021 Table K.1).

Each quantity is a `(lower, upper)` pair; `None` is an open end: the
table prints the three lighter classes as "up to" a rate and cloudburst as
"greater than" every quantity.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rainfall_rate_mm_h` | Rainfall rate, in mm/h. |
| `drop_diameter_mm` | Typical drop diameter, in mm. |
| `fall_velocity_m_s` | Fall velocity, in m/s. |

## RainGeneratorVerification

```python
RainGeneratorVerification(
    rain_type: str,
    rainfall_rate_mm_h: float,
    drop_diameters_mm: np.ndarray | None,
    fall_velocities_m_s: np.ndarray | None,
)
```

Whether an artificial rain generator makes the rain it should (H.1, H.2.3).

The windows are the rows of Table H.1 the rain type selects, so the
shares and the verdicts are read from the measured samples and are not
fields: a verification cannot be built to pass a rain the table fails.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rain_type` | `"intense"` or `"heavy"`. |
| `rainfall_rate_mm_h` | The measured rainfall rate, in mm/h. |
| `drop_diameters_mm` | The measured drop diameters, in mm, or `None`. |
| `fall_velocities_m_s` | The measured fall velocities, in m/s, or `None`. |

### RainGeneratorVerification.drop_share

*property*

Share of the measured drops within the diameter window, or `None`.

### RainGeneratorVerification.drops_ok

*property*

Whether at least half of the drops are within it ("should"), or `None`.

### RainGeneratorVerification.nominal

*property*

The row of [`ARTIFICIAL_RAIN`](/phonometry/reference/api/building/rainfall-sound/#artificial_rain) the generator was verified against.

### RainGeneratorVerification.passes

*property*

Whether every judged requirement holds.

### RainGeneratorVerification.plot()

```python
RainGeneratorVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each measured quantity against its tolerance window.

Every quantity is drawn as its deviation from the nominal value in
units of its tolerance, so the three share one axis and the window is
-1 to 1. Requires matplotlib (`pip install phonometry[plot]`);
returns the `Axes`.

### RainGeneratorVerification.rate_deviation_mm_h

*property*

Measured minus nominal rate, in mm/h.

### RainGeneratorVerification.rate_ok

*property*

Whether the rate is within the tolerance ("shall"), bounds included.

### RainGeneratorVerification.velocities_ok

*property*

Whether at least half of the drops fall within it ("should"), or `None`.

### RainGeneratorVerification.velocity_share

*property*

Share of the measured drops within the velocity window, or `None`.

## verify_rain_generator

```python
verify_rain_generator(
    rainfall_rate_mm_h: float,
    *,
    rain_type: str = 'heavy',
    drop_diameters_mm: ArrayLike | None = None,
    fall_velocities_m_s: ArrayLike | None = None,
) -> RainGeneratorVerification
```

Does the rain generator make the rain of Table H.1 (ISO 10140-5:2021)?

H.1 sets three tolerances on the generated rain: the rainfall rate
"shall be within ±2 mm/h" of the nominal rate, and half of the drops
"should be within ±0,5 mm" of the volume median drop diameter and
"within ±1 m/s" of the fall velocity. A tank built to Table H.2 needs only
the rate checked (H.2.3), by collecting the water ([`rainfall_rate`](/phonometry/reference/api/building/rainfall-sound/#rainfall_rate));
another generator needs the drops measured as well, and the drop criteria
are judged when their samples are given. The three windows include their
bounds: a rate exactly 2 mm/h from the nominal one passes, also when
[`rainfall_rate`](/phonometry/reference/api/building/rainfall-sound/#rainfall_rate) returns it a rounding error beyond.

**Parameters**

| Name | Description |
| :--- | :--- |
| `rainfall_rate_mm_h` | The measured rainfall rate, in mm/h. |
| `rain_type` | `"heavy"` (default) or `"intense"`. |
| `drop_diameters_mm` | Diameters of individual measured drops, in mm, or `None` to leave the drop size unjudged. |
| `fall_velocities_m_s` | Fall velocities of individual measured drops, in m/s, or `None` to leave the velocity unjudged. |

**Returns:** A [`RainGeneratorVerification`](/phonometry/reference/api/building/rainfall-sound/#raingeneratorverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the rate or a sample is not positive and finite, or `rain_type` is unknown. |
