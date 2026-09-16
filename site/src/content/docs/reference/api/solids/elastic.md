---
title: "solids.elastic"
description: "Three longitudinal wave speeds of a solid, and which one a table prints."
sidebar:
  label: "elastic"
---

Three longitudinal wave speeds of a solid, and which one a table prints.

A solid carries more than one longitudinal wave, and which one a number belongs
to depends on the shape the wave travels in, not on the material. The three are

$$
c_{\mathrm{L,b}} = \sqrt{\frac{E}{\rho}} \qquad\text{for a beam}
$$

$$
c_{\mathrm{L,p}} = \sqrt{\frac{E}{\rho\,(1 - \nu^2)}} \qquad\text{for a plate}
$$

$$
c'_{\mathrm{L}} = \sqrt{\frac{E\,(1 - \nu)}{\rho\,(1 + \nu)(1 - 2\nu)}} \qquad\text{in an unbounded solid}
$$

and they are not interchangeable. Take the steel of Hopkins Table A2,
`rho = 7800` kg/m3, `nu = 0.28` and a plate speed of 5 270 m/s, which is a
Young's modulus of 200 GPa: the beam speed is 5 059 m/s and the bulk speed is
5 720 m/s. Reading one into another is a four to nine per cent error in
whatever it feeds, and the gap grows with Poisson's ratio. The first two are
Hopkins (2007) Eqs. (2.20) and
(2.21), PDF page 144 (printed p. 117), which also records that the `b` and
`p` subscripts are dropped later in that book and the plate value is then
called `cL` with no qualifier at all. The third is Norton & Karczub (2003)
2e Eq. (1.225), PDF page 94 (printed p. 74), the wave velocity of a *pure*
longitudinal wave, after Fahy.

Which one a printed table holds has to be read off its own page, and the
answer is not always the one the column heading suggests. EN 12354-1 Table B.3,
Hopkins Table A2 and Mechel Table 3 tabulate the plate value; a table of
*bulk* wave speeds, which is what an elastic solver integrates, is a different
table. This module exists so the conversion between them is written once,
named after the shape it belongs to, and never done in a caller's head.

Each speed has its inverse here as well, because a catalogue is built from
whatever its sources happened to print: Hopkins prints the plate speed and no
Young's modulus, Cremer and Mechel print the modulus and no speed, and the two
only meet through these six functions.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## beam_longitudinal_speed

```python
beam_longitudinal_speed(
    youngs_modulus_pa: float,
    *,
    density_kg_m3: float,
) -> float
```

Quasi-longitudinal wave speed along a beam (Hopkins Eq. 2.20).

$c_\mathrm{L,b} = \sqrt{E / \rho}$. A beam is unconstrained on its
sides, so the lateral strains cost nothing and Poisson's ratio does not
appear.

**Parameters**

| Name | Description |
| :--- | :--- |
| `youngs_modulus_pa` | Young's modulus `E`, in pascals (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |

**Returns:** The wave speed, in m/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input. |

## bulk_longitudinal_speed

```python
bulk_longitudinal_speed(
    youngs_modulus_pa: float,
    *,
    density_kg_m3: float,
    poisson_ratio: float,
) -> float
```

Pure longitudinal wave speed in an unbounded solid (Norton Eq. 1.225).

$c'_\mathrm{L} = \sqrt{B / \rho}$ with the longitudinal modulus
$B = E (1 - \nu) / ((1 + \nu)(1 - 2\nu))$. Nothing is free to move
sideways, which is why this is the fastest of the three and why it is the
speed an elastic solver integrates.

**Parameters**

| Name | Description |
| :--- | :--- |
| `youngs_modulus_pa` | Young's modulus `E`, in pascals (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |
| `poisson_ratio` | Poisson's ratio `nu`, between -1 and 0.5. |

**Returns:** The wave speed, in m/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a ratio out of range. |

## DEFAULT_SPEED_OF_SOUND_M_S

*Constant* (`float`).

```python
DEFAULT_SPEED_OF_SOUND_M_S = 343.0
```

## plate_longitudinal_speed

```python
plate_longitudinal_speed(
    youngs_modulus_pa: float,
    *,
    density_kg_m3: float,
    poisson_ratio: float,
) -> float
```

Quasi-longitudinal wave speed along a plate (Hopkins Eq. 2.21).

$c_\mathrm{L,p} = \sqrt{E / (\rho (1 - \nu^2))}$. The plate is
constrained across its width, which stiffens it by $1/(1 - \nu^2)$
against the beam of [`beam_longitudinal_speed`](/phonometry/reference/api/solids/elastic/#beam_longitudinal_speed).

This is the value the building-acoustics tables print, and the one the
critical frequency of a wall or floor is computed from.

**Parameters**

| Name | Description |
| :--- | :--- |
| `youngs_modulus_pa` | Young's modulus `E`, in pascals (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |
| `poisson_ratio` | Poisson's ratio `nu`, between -1 and 1. |

**Returns:** The wave speed, in m/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a ratio out of range. |

## thickness_critical_frequency_product

```python
thickness_critical_frequency_product(
    plate_speed_m_s: float,
    *,
    speed_of_sound_m_s: float = 343.0,
) -> float
```

The `h f_c` a materials table prints, from the plate wave speed.

$$
h f_\mathrm{c} = \frac{c_0^2 \sqrt{12}}{2 \pi\, c_\mathrm{L,p}}
$$

which is the critical frequency of a thin plate multiplied by the thickness
it was computed for, so the product is a property of the material alone.
Hopkins Table A2, Long Table 9.1 and Mechel Table 3 each print this column,
which makes it the cheapest cross-check there is between three books that
otherwise share no column at all.

The constant here is the exact $2\pi/\sqrt{12} = 1.8138$ of the
thin-plate dispersion relation, which is what
[`phonometry.vibration.coincidence_frequency`](/phonometry/reference/api/vibration/radiation-efficiency/#coincidence_frequency) computes and what
reproduces the printed column: Hopkins states `c0 = 343` m/s in the
heading of Table A2 and prints 12.3 m Hz for steel, which this returns and
the rounded 1.8 of ISO 12354-1 misses by 0.8 per cent (12.40).
[`phonometry.building.critical_frequency`](/phonometry/reference/api/building/flanking-transmission/#critical_frequency) keeps the rounded constant,
because there it is the standard's own arithmetic and not the material's.

**Parameters**

| Name | Description |
| :--- | :--- |
| `plate_speed_m_s` | Plate wave speed `cL,p`, in m/s (> 0). |
| `speed_of_sound_m_s` | Speed of sound in air `c0`, in m/s (> 0). |

**Returns:** The product `h f_c`, in Hz m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input. |

## youngs_modulus_from_beam_speed

```python
youngs_modulus_from_beam_speed(
    longitudinal_speed_m_s: float,
    *,
    density_kg_m3: float,
) -> float
```

Young's modulus from a beam wave speed, the inverse of Eq. 2.20.

$E = \rho\, c_\mathrm{L,b}^2$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `longitudinal_speed_m_s` | Beam wave speed `cL,b`, in m/s (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |

**Returns:** Young's modulus `E`, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input. |

## youngs_modulus_from_bulk_speed

```python
youngs_modulus_from_bulk_speed(
    longitudinal_speed_m_s: float,
    *,
    density_kg_m3: float,
    poisson_ratio: float,
) -> float
```

Young's modulus from a bulk wave speed, the inverse of Eq. 1.225.

$E = \rho\, c'^2_\mathrm{L} (1 + \nu)(1 - 2\nu) / (1 - \nu)$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `longitudinal_speed_m_s` | Bulk wave speed `cL'`, in m/s (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |
| `poisson_ratio` | Poisson's ratio `nu`, between -1 and 0.5. |

**Returns:** Young's modulus `E`, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a ratio out of range. |

## youngs_modulus_from_plate_speed

```python
youngs_modulus_from_plate_speed(
    longitudinal_speed_m_s: float,
    *,
    density_kg_m3: float,
    poisson_ratio: float,
) -> float
```

Young's modulus from a plate wave speed, the inverse of Eq. 2.21.

$E = \rho\, c_\mathrm{L,p}^2 (1 - \nu^2)$. This is what turns a table
that prints `cL` and `nu` and no modulus, such as Hopkins Table A2,
into one that can be compared with a table that prints the modulus.

**Parameters**

| Name | Description |
| :--- | :--- |
| `longitudinal_speed_m_s` | Plate wave speed `cL,p`, in m/s (> 0). |
| `density_kg_m3` | Density `rho`, in kg/m3 (> 0). |
| `poisson_ratio` | Poisson's ratio `nu`, between -1 and 1. |

**Returns:** Young's modulus `E`, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a ratio out of range. |
