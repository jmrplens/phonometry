---
title: "vibration.immission.prediction"
description: "Predicting vibration before it is measured (DIN 4150-1:2001-06)."
sidebar:
  label: "prediction"
---

Predicting vibration before it is measured (DIN 4150-1:2001-06).

Part 1 of DIN 4150 is the first question of the series: before a blast is
fired, a pile driven or a line built, how much vibration will reach the
building, and how much of it will the floors feel. It gives no recipe, and
says so in its foreword; what it gives is the shape of every answer, the
handful of constants experience has fixed, and twenty-seven figures of
measured cases to show what the shapes look like in the ground. The shapes
and the constants are here.

**Propagation** (Clause 4.2). Beyond the reference distance
$R_1 = a/2 + \lambda_R$ of Formula (1), half the source's extent plus a
surface wavelength, the velocity amplitude decays as

$$
\bar v = \bar v_1 \left(\frac{R}{R_1}\right)^{-n} \exp[-\alpha (R - R_1)]
$$

(Formula (2)): geometric spreading with an exponent $n$ that Figure 1
fixes at 0, 0,5, 1 or 1,5 by whether the source is a line or a point,
harmonic or impulsive, and the wave a surface or a body wave; and material
damping with $\alpha \approx 2\pi D / \lambda$, the damping ratio of the
ground over the wavelength, which for loose ground may be taken as 0,01 at
most in a preliminary estimate. Nearer than $R_1$ the formula does not
hold. A train is a chain of point sources and decays with an exponent
between 0,3 and 0,5.

**Into the building** (Clause 4.3). A building on the ground is a mass on a
spring with the natural frequency of Formula (3), about 15 Hz for one or two
storeys and under 8 Hz above six; the foundation passes at most
$1 / (2 D_0)$ of the ground's amplitude at that frequency, 2 for the
0,25 of loose ground, and a mean of 0,5 above it, or all of it on rock; a
floor amplifies by at most $1 / (2 D_1)$, 10 to 25 for a concrete
floor; and the lowest horizontal natural frequency of a building of five
storeys or more is about $10 / n$ Hz (Formula (4)).

**Sources** (Clause 5). A blast in the far field follows
$v_{\max} = k (L/L_0)^b (R/R_0)^{-m}$ (Formula (5)) with the charge per
delay $L$ and constants from trial blasts; a falling mass follows the
same with the root of its fall energy (Formula (6)); a hall of $N$
similar machines gives $\chi \, v_B \sqrt{N}$ at a point where
$N_B$ of them were measured (Formula (7)), with the correction
$\chi$ of Figure 3, which is printed as a nomogram and is here as the
nomogram read at a five-hundredth. Rail traffic excites at the speed over
the spacing of whatever repeats along the track, sleepers first, and its
vehicles have natural frequencies of their own.

**What is not here.** The measured cases of Annex A print their inputs and
their peaks and say themselves that they are not a basis for a prediction;
two of their figures are drawn from the formulas above with every parameter
printed, and those are the conformance rows. Two symbol lists print a
distance in millimetres, one working frequency has its sign the wrong way
and one legend swaps two line styles; all in `docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## attenuation_coefficient_per_m

```python
attenuation_coefficient_per_m(
    damping_ratio: float,
    *,
    wavelength_m: float,
) -> float
```

The material damping of the ground, $\alpha$ of Formula (2).

$\alpha \approx 2\pi D / \lambda$ with $\lambda = c / f$ the
wavelength that matters. Figure A.19 prints 0,005 for a damping ratio of
0,01 and a wavelength of 12,5 m.

**Parameters**

| Name | Description |
| :--- | :--- |
| `damping_ratio` | $D$, not negative; 0,01 at most for loose ground in a preliminary estimate. |
| `wavelength_m` | $\lambda$, in metres. |

**Returns:** $\alpha$, in reciprocal metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative damping ratio or a non-positive wavelength. |

## blast_peak_velocity_mm_s

```python
blast_peak_velocity_mm_s(
    charge_kg: float,
    distance_m: ArrayLike,
    *,
    coefficient_mm_s: float,
    charge_exponent: float,
    distance_exponent: float,
) -> NDArray[np.float64]
```

The peak velocity of a blast in the far field, Formula (5).

$v_{\max} = k (L/L_0)^b (R/R_0)^{-m}$ with the charge per delay
$L$ against 1 kg, the distance $R$ against 1 m, and the
constants $k$, $b$ and $m$ from trial blasts or
comparable cases in ground, method and distance, with allowance for
scatter. The standard prints no values for them. Its symbol list prints
the distance in millimetres, which the reference metre says is a slip.

**Parameters**

| Name | Description |
| :--- | :--- |
| `charge_kg` | $L$, in kilograms per delay. |
| `distance_m` | $R$, in metres, one or many. |
| `coefficient_mm_s` | $k$, in millimetres per second. |
| `charge_exponent` | $b$. |
| `distance_exponent` | $m$. |

**Returns:** $v_{\max}$, one per distance, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive charge, distance or coefficient, or a negative exponent. |

## BLASTING_RELEVANT_DISTANCE_M

*Constant* (`dict`).

```python
BLASTING_RELEVANT_DISTANCE_M = {'quarry': 1500.0, 'construction': 400.0}
```

## fall_energy_kj

```python
fall_energy_kj(weight_kn: float, *, drop_height_m: float) -> float
```

The energy of a falling mass, $E = G h$ of Clause 5.1.3.

A weight in kilonewtons through a height in metres is that many
kilojoules, the unit Formula (6) wants.

**Parameters**

| Name | Description |
| :--- | :--- |
| `weight_kn` | $G$, in kilonewtons. |
| `drop_height_m` | $h$, in metres. |

**Returns:** $E$, in kilojoules.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive weight or height. |

## far_field_velocity_mm_s

```python
far_field_velocity_mm_s(
    reference_velocity_mm_s: float,
    distance_m: ArrayLike,
    *,
    reference_distance_m: float,
    exponent: float,
    attenuation_per_m: float = 0.0,
) -> NDArray[np.float64]
```

The velocity amplitude at a distance in the far field, Formula (2).

$\bar v = \bar v_1 (R / R_1)^{-n} \exp[-\alpha (R - R_1)]$: the
amplitude at the reference distance, spread with the exponent of Figure
1 and damped with $\alpha$. Figure A.19 draws it for 0,44 mm/s at
13 m with $\alpha$ = 0,005 for the three exponents 0, 0,5 and 1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_velocity_mm_s` | $\bar v_1$, at $R_1$, in millimetres per second. |
| `distance_m` | $R$, in metres, one or many, none nearer than $R_1$. |
| `reference_distance_m` | $R_1$, in metres. |
| `exponent` | $n$, from [`geometric_exponent`](/phonometry/reference/api/vibration/prediction/#geometric_exponent). |
| `attenuation_per_m` | $\alpha$, from [`attenuation_coefficient_per_m`](/phonometry/reference/api/vibration/prediction/#attenuation_coefficient_per_m); 0 (default) for no material damping. |

**Returns:** $\bar v$, one per distance, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative amplitude, exponent or attenuation, a non-positive reference distance, or a distance in the near field. |

## FLOOR_DAMPING_RATIO_RANGE

*Constant* (`tuple`).

```python
FLOOR_DAMPING_RATIO_RANGE = (0.02, 0.05)
```

## floor_transfer_max

```python
floor_transfer_max(floor_damping_ratio: float) -> float
```

The most a floor amplifies at its resonance, Clause 4.3.

$V_D = 1 / (2 D_1)$, from the foundation through the walls to the
floor, for a building excited in phase over its whole footprint by
predominantly harmonic vibration: 25 for a concrete floor with a damping
ratio of 0,02 and 10 for one with 0,05. Short spans, partitions and a
foundation on loose ground raise the damping.

**Parameters**

| Name | Description |
| :--- | :--- |
| `floor_damping_ratio` | $D_1$, positive. |

**Returns:** $V_D$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive damping ratio. |

## FOUNDATION_TRANSFER_ABOVE_RESONANCE

*Constant* (`float`).

```python
FOUNDATION_TRANSFER_ABOVE_RESONANCE = 0.5
```

## foundation_transfer_max

```python
foundation_transfer_max(system_damping_ratio: float = 0.25) -> float
```

The most a foundation passes at the building's resonance, Clause 4.3.

$V_F = 1 / (2 D_0)$ with the system damping of the building on its
ground, 0,25 for loose ground, which gives 2. Above the resonance a
mean of [`FOUNDATION_TRANSFER_ABOVE_RESONANCE`](/phonometry/reference/api/vibration/prediction/#foundation_transfer_above_resonance) may be assumed, and
on rock there is no reduction.

**Parameters**

| Name | Description |
| :--- | :--- |
| `system_damping_ratio` | $D_0$, positive; 0,25 by default. |

**Returns:** $V_F$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive damping ratio. |

## geometric_exponent

```python
geometric_exponent(*, geometry: str, character: str, wave: str) -> float
```

The exponent $n$ of Formula (2) for a source and a wave, Figure 1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `geometry` | `"point"` or `"line"`. |
| `character` | `"harmonic"` (stationary) or `"impulsive"`. |
| `wave` | `"surface"` or `"body"`. |

**Returns:** $n$: 0, 0,5, 1 or 1,5.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown geometry, character or wave. |

## impact_peak_velocity_mm_s

```python
impact_peak_velocity_mm_s(
    fall_energy_kj: float,
    distance_m: ArrayLike,
    *,
    coefficient_mm_s: float,
    distance_exponent: float,
) -> NDArray[np.float64]
```

The peak velocity of a falling mass, Formula (6).

$v_{\max} = k (E/E_0)^{0{,}5} (R/R_0)^{-m}$ with the fall energy
$E$ against 1 kJ, the distance against 1 m, and $k$ and
$m$ from comparable cases. The blast that fells a chimney is
usually the smaller source; the impact is this one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fall_energy_kj` | $E$, in kilojoules, from [`fall_energy_kj`](/phonometry/reference/api/vibration/prediction/#fall_energy_kj). |
| `distance_m` | $R$, in metres, one or many. |
| `coefficient_mm_s` | $k$, in millimetres per second. |
| `distance_exponent` | $m$. |

**Returns:** $v_{\max}$, one per distance, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive energy, distance or coefficient, or a negative exponent. |

## LOOSE_GROUND_DAMPING_RATIO

*Constant* (`float`).

```python
LOOSE_GROUND_DAMPING_RATIO = 0.01
```

## LOOSE_GROUND_SYSTEM_DAMPING

*Constant* (`float`).

```python
LOOSE_GROUND_SYSTEM_DAMPING = 0.25
```

## MACHINE_COUNT_AXIS

*Constant* (`tuple`).

```python
MACHINE_COUNT_AXIS = (4, 5, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100)
```

## MACHINE_COUNT_CORRECTION

*Constant* (`dict`).

```python
MACHINE_COUNT_CORRECTION = {3: (0.551, 0.537, 0.519, 0.496, 0.471, 0.423, 0.383, 0.36, 0.336, 0.323, 0.309, 0.3, 0.292, 0.289, 0.289, 0.289, 0.286), 5: (0.455, 0.444, 0.427, 0.406, 0.386, 0.342, 0.308, 0.292, 0.276, 0.264, 0.256, 0.245, 0.239, 0.238, 0.236, 0.234, 0.234), 10: (0.365, 0.355, 0.342, 0.327, 0.308, 0.28, 0.252, 0.239, 0.225, 0.216, 0.207, 0.2, 0.193, 0.192, 0.192, 0.191, 0.189), 30: (0.292, 0.283, 0.273, 0.258, 0.243, 0.22, 0.2, 0.188, 0.176, 0.169, 0.164, 0.157, 0.153, 0.153, 0.151, 0.15, 0.149), 60: (0.242, 0.239, 0.23, 0.22, 0.207, 0.189, 0.17, 0.158, 0.148, 0.142, 0.136, 0.13, 0.127, 0.127, 0.126, 0.125, 0.125), 100: (0.189, 0.188, 0.18, 0.173, 0.161, 0.147, 0.134, 0.125, 0.117, 0.111, 0.108, 0.1, 0.1, 0.1, 0.1, 0.1, 0.099)}
```

## machine_count_correction

```python
machine_count_correction(
    machine_count: ArrayLike,
    *,
    reference_count: int,
) -> NDArray[np.float64]
```

The correction $\chi$ of Formula (7), Figure 3.

The figure draws $\chi$ against the number of machines running,
from 4 to 100, for measurements made with 3, 5, 10, 30, 60 or 100 of
them, and prints no closed form; the curve is read off the page at a
five-hundredth and interpolated linearly between the readings.

**Parameters**

| Name | Description |
| :--- | :--- |
| `machine_count` | $N$, from 4 to 100, one or many. |
| `reference_count` | $N_B$, one of the six curves. |

**Returns:** $\chi$, one per count.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a count outside the figure or a reference the figure has no curve for. |

## MACHINE_FREQUENCY_BANDS_HZ

*Constant* (`dict`).

```python
MACHINE_FREQUENCY_BANDS_HZ = {'counter_blow_hammer': (4.0, 8.0), 'forging_press_horizontal': (5.0, 15.0), 'frame_saw': (4.0, 8.0)}
```

## machine_hall_velocity_mm_s

```python
machine_hall_velocity_mm_s(
    reference_velocity_mm_s: float,
    machine_count: ArrayLike,
    *,
    reference_count: int,
) -> NDArray[np.float64]
```

The peak velocity outside a hall of similar machines, Formula (7).

$v_N = \chi \, v_B \sqrt{N}$: the velocity measured at the point
with $N_B$ machines running, scaled to $N$ of them with the
correction of Figure 3. Figure A.18 draws it for 0,44 mm/s measured with
three machines and finds the measurements on the curve up to about
sixty, the nearest group; beyond that the added groups are further off.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_velocity_mm_s` | $v_B$, in millimetres per second. |
| `machine_count` | $N$, from 4 to 100, one or many. |
| `reference_count` | $N_B$, one of 3, 5, 10, 30, 60 or 100. |

**Returns:** $v_N$, one per count, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative velocity, or a count or reference outside Figure 3. |

## material_damping_factor

```python
material_damping_factor(
    distance_m: ArrayLike,
    *,
    damping_ratio: float,
    frequency_hz: float,
    wave_speed_m_s: float,
) -> NDArray[np.float64]
```

The share the ground absorbs over a distance, Figure 2.

$\exp[-2\pi D f (R - R_1) / c]$, the damping factor of Formula (2)
alone, which Figure 2 draws for a damping ratio of 0,01 and a wave speed
of 200 m/s from 10 Hz to 50 Hz: at 100 m the ground has taken 27 % of
the amplitude at 10 Hz and 79 % at 50 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | $R - R_1$, in metres, one or many, not negative. |
| `damping_ratio` | $D$, not negative. |
| `frequency_hz` | $f$, in hertz. |
| `wave_speed_m_s` | $c$, in metres per second. |

**Returns:** The factor, one per distance, between 0 and 1.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative distance or damping ratio, or a non-positive frequency or wave speed. |

## MEDIUM_SOIL_SHEAR_WAVE_SPEED_M_S

*Constant* (`tuple`).

```python
MEDIUM_SOIL_SHEAR_WAVE_SPEED_M_S = (150.0, 200.0)
```

## RAIL_INFLUENCE_RANGE_M

*Constant* (`float`).

```python
RAIL_INFLUENCE_RANGE_M = 80.0
```

## RAIL_SUPPORT_SPACING_M

*Constant* (`tuple`).

```python
RAIL_SUPPORT_SPACING_M = (0.6, 0.9)
```

## reference_distance_m

```python
reference_distance_m(
    source_extent_m: float,
    *,
    rayleigh_wavelength_m: float,
) -> float
```

The distance the far field begins at, Formula (1).

$R_1 = a/2 + \lambda_R$: half the extent of the source along the
direction of propagation plus a wavelength of the surface wave. Nearer
than it Formula (2) does not hold.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_extent_m` | $a$, in metres, not negative. |
| `rayleigh_wavelength_m` | $\lambda_R$, in metres. |

**Returns:** $R_1$, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative extent or a non-positive wavelength. |

## soil_building_frequency_guide_hz

```python
soil_building_frequency_guide_hz(storeys: int) -> tuple[float, float]
```

The natural frequency Clause 4.3 gives a building on medium ground.

About 15 Hz for one or two storeys, 8 Hz to 12 Hz for two to six, under
8 Hz above six, for a ground with a shear wave speed of 150 m/s to
200 m/s. The clause prints two storeys in both ranges, so a two-storey
building gets the union, 8 Hz to 15 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `storeys` | The number of storeys, at least one. |

**Returns:** `(low, high)` in hertz; the low bound is 0 above six storeys and both are 15 for a single storey.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For fewer than one storey or a count that is not whole. |

## soil_building_natural_frequency_hz

```python
soil_building_natural_frequency_hz(
    stiffness_n_per_m: float,
    *,
    mass_kg: float,
) -> float
```

The natural frequency of a building on its ground, Formula (3).

$f_B = \frac{1}{2\pi}\sqrt{k_B / m_B}$: the ground as a spring under
the mass of the building that moves in phase, for the vertical direction
and predominantly harmonic vibration in the lower frequency range.

**Parameters**

| Name | Description |
| :--- | :--- |
| `stiffness_n_per_m` | $k_B$, the spring stiffness of the ground, in newtons per metre. |
| `mass_kg` | $m_B$, in kilograms. |

**Returns:** $f_B$, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive stiffness or mass. |

## SOURCE_EXPONENTS

*Constant* (`dict`).

```python
SOURCE_EXPONENTS = {('line', 'harmonic', 'surface'): 0.0, ('line', 'harmonic', 'body'): 0.5, ('point', 'harmonic', 'surface'): 0.5, ('line', 'impulsive', 'surface'): 0.5, ('point', 'harmonic', 'body'): 1.0, ('line', 'impulsive', 'body'): 1.0, ('point', 'impulsive', 'surface'): 1.0, ('point', 'impulsive', 'body'): 1.5}
```

## STOREY_FORMULA_MIN_STOREYS

*Constant* (`int`).

```python
STOREY_FORMULA_MIN_STOREYS = 5
```

## storey_frequency_hz

```python
storey_frequency_hz(storeys: int) -> float
```

The lowest horizontal natural frequency of a building, Formula (4).

$f_1 \approx 10 / n$ Hz for a building of $n$ storeys, meant
for five and more, where a tall slender building meets a low excitation
frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `storeys` | $n$, at least five. |

**Returns:** $f_1$, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For fewer than five storeys. |

## track_excitation_frequency_hz

```python
track_excitation_frequency_hz(
    train_speed_m_s: float,
    *,
    spacing_m: float,
    harmonics: int = 1,
) -> NDArray[np.float64]
```

The frequencies a repeating feature of the track excites, Clause 5.3.2.

$f_A = v_Z / d$ and its multiples, for the spacing $d$ of
whatever repeats along the track or the wheel: the sleepers, the axles,
the bogies, a flat spot once per turn of the wheel. The natural
frequencies of the vehicle itself do not move with the speed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `train_speed_m_s` | $v_Z$, in metres per second. |
| `spacing_m` | $d$, in metres. |
| `harmonics` | How many multiples to return, the fundamental first. |

**Returns:** $f_A$ and its multiples, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive speed or spacing, or fewer than one harmonic. |

## TRACK_TRANSMITTED_BANDS_HZ

*Constant* (`dict`).

```python
TRACK_TRANSMITTED_BANDS_HZ = {'ballast': (40.0, 80.0), 'under_ballast_mat': (15.0, 40.0), 'mass_spring': (5.0, 20.0)}
```

## TRAIN_CHAIN_EXPONENT_RANGE

*Constant* (`tuple`).

```python
TRAIN_CHAIN_EXPONENT_RANGE = (0.3, 0.5)
```

## VEHICLE_NATURAL_FREQUENCIES_HZ

*Constant* (`dict`).

```python
VEHICLE_NATURAL_FREQUENCIES_HZ = {'car_body': (1.0, 3.0), 'bogie': (6.0, 10.0)}
```
