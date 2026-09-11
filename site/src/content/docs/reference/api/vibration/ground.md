---
title: "vibration.immission.ground"
description: "The elastic properties of the ground from its wave speeds (DIN 45672-1:2009-12)."
sidebar:
  label: "ground"
---

The elastic properties of the ground from its wave speeds (DIN 45672-1:2009-12).

DIN 45672-1 is the method of measuring vibration next to a railway line, and
nearly all of it is procedure: where to put the transducers, which directions,
which trains, what to write down. Its Clause 4.5 is the exception. The ground
the vibration travels through is described by the speeds of its compression
and shear waves, and from those two speeds and the density the clause gives
the shear modulus, Poisson's ratio and the elastic modulus, and the shear
strain a vibration puts into the soil.

**Why two speeds are enough.** An unbounded elastic continuum carries two
kinds of wave, and their speeds are fixed by two elastic constants and the
density: $v_s = \sqrt{G/\rho}$ for the shear wave (Formula (2)) and
$v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}$ for the compression wave. So
measuring both speeds fixes $G$ and $\nu$, and with them every
other constant. $v_p > v_s$ always; the ratio decides Poisson's ratio
(Formula (3)).

**Why a small strain.** The shear modulus of a soil falls as the strain grows:
Figure 1 has it constant up to a shear strain of about $10^{-4}$ and
dropping below 20 % of that value further on. The experiments of the clause and
the vibration of rail traffic both strain the ground around $10^{-6}$, so
the modulus measured is the small-strain maximum and the one that applies.
The strain itself is the velocity amplitude over the shear-wave speed
(Formula (4)).

**Two formulas that are printed wrong.** Formula (1) writes the compression
speed as $\sqrt{E/\rho}$, which is the speed in a thin rod, and as
$\sqrt{G(1-\nu)/(\rho(1-2\nu))}$, which is short of a factor 2; Formula
(5) builds on the first and writes $E = v_p^2 \rho$. Both contradict
Formula (3) of the same clause, which is right, and the two expressions of
Formula (1) only agree with each other at $\nu = (\sqrt{17}-1)/8 \approx 0{,}39$. This module uses the relations of the continuum, which is
what Formula (3) is derived from, and the defect is registered in
`docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## compression_wave_speed

```python
compression_wave_speed(
    shear_modulus_pa: float,
    *,
    poisson_ratio: float,
    density_kg_m3: float,
) -> float
```

The compression-wave speed of a continuum, Formula (1) corrected, in m/s.

$v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}$, the speed of a P-wave in an
unbounded medium, whose inverse is Formula (3). Formula (1) prints the
radicand without the factor 2, which gives a speed $\sqrt{2}$ too
slow at every Poisson's ratio.

**Parameters**

| Name | Description |
| :--- | :--- |
| `shear_modulus_pa` | $G$, in pascals. |
| `poisson_ratio` | $\nu$, above -1 and below 0,5. |
| `density_kg_m3` | $\rho$, in kilograms per cubic metre. |

**Returns:** $v_p$, in metres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive modulus or density, or a ratio outside `(-1, 0.5)`, where the continuum would not be stable. |

## GROUND_WAVE_SPEED_RANGES_M_S

*Constant* (`dict`).

```python
GROUND_WAVE_SPEED_RANGES_M_S = {'compression': (200.0, 2000.0), 'shear': (10.0, 1000.0)}
```

## poisson_ratio_from_wave_speeds

```python
poisson_ratio_from_wave_speeds(
    compression_wave_speed_m_s: float,
    shear_wave_speed_m_s: float,
) -> float
```

Poisson's ratio from the two wave speeds, Formula (3).

$\nu = (v_p^2 - 2 v_s^2) / (2 (v_p^2 - v_s^2))$, the inversion of
the continuum relations and the formula of Clause 4.5.1 that is printed
right.

**Parameters**

| Name | Description |
| :--- | :--- |
| `compression_wave_speed_m_s` | $v_p$, in metres per second. |
| `shear_wave_speed_m_s` | $v_s$, in metres per second. |

**Returns:** $\nu$, between -1 and 0,5. It is positive when $v_p$ exceeds $\sqrt{2}\,v_s$, as it does in every soil; a pair between $2/\sqrt{3}$ and $\sqrt{2}$ gives the negative ratio a continuum allows and a soil does not show.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive speed, or a compression wave no faster than $2/\sqrt{3}$ times the shear wave, which no stable continuum carries. |

## shear_modulus_from_wave_speed

```python
shear_modulus_from_wave_speed(
    shear_wave_speed_m_s: float,
    *,
    density_kg_m3: float,
) -> float
```

The shear modulus $G = v_s^2 \rho$, Formula (5), in pascals.

**Parameters**

| Name | Description |
| :--- | :--- |
| `shear_wave_speed_m_s` | $v_s$, in metres per second. |
| `density_kg_m3` | $\rho$, in kilograms per cubic metre. |

**Returns:** $G$, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive speed or density. |

## shear_strain_amplitude

```python
shear_strain_amplitude(
    velocity_amplitude_m_s: float,
    *,
    shear_wave_speed_m_s: float,
) -> float
```

The shear strain amplitude $\hat\gamma = \hat v / v_s$, Formula (4).

Compare it with [`SHEAR_STRAIN_LINEAR_LIMIT`](/phonometry/reference/api/vibration/ground/#shear_strain_linear_limit) to know whether the
small-strain modulus still applies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_amplitude_m_s` | $\hat v$, the velocity amplitude, in metres per second (not millimetres: the strain is a ratio of the two speeds). |
| `shear_wave_speed_m_s` | $v_s$, in metres per second. |

**Returns:** $\hat\gamma$, in radians.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative amplitude or a non-positive speed. |

## SHEAR_STRAIN_LINEAR_LIMIT

*Constant* (`float`).

```python
SHEAR_STRAIN_LINEAR_LIMIT = 0.0001
```

## youngs_modulus_from_wave_speeds

```python
youngs_modulus_from_wave_speeds(
    compression_wave_speed_m_s: float,
    shear_wave_speed_m_s: float,
    *,
    density_kg_m3: float,
) -> float
```

The elastic modulus from the two wave speeds, in pascals.

$E = 2G(1+\nu) = \rho v_s^2 (3 v_p^2 - 4 v_s^2)/(v_p^2 - v_s^2)$,
which is what Formula (5) means. As printed it reads $E = v_p^2 \rho$, the thin-rod relation, and that overstates the modulus of a soil
with $\nu = 0{,}3$ by 35 % and of one with $\nu = 0{,}45$ by a
factor of 3,8.

**Parameters**

| Name | Description |
| :--- | :--- |
| `compression_wave_speed_m_s` | $v_p$, in metres per second. |
| `shear_wave_speed_m_s` | $v_s$, in metres per second. |
| `density_kg_m3` | $\rho$, in kilograms per cubic metre. |

**Returns:** $E$, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As [`poisson_ratio_from_wave_speeds`](/phonometry/reference/api/vibration/ground/#poisson_ratio_from_wave_speeds), or for a non-positive density. |
