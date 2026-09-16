---
title: "fluids.gas"
description: "An ideal gas from the two numbers a gas table prints."
sidebar:
  label: "gas"
---

An ideal gas from the two numbers a gas table prints.

A table of gases prints a ratio of specific heats and a molar mass, and those
two close the ideal-gas state completely:

$$
c = \sqrt{\frac{\gamma R T}{M}} \qquad \rho = \frac{p\,M}{R\,T}
$$

so a caller who has a gas that is not air or water can still have a
[`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) for it, computed rather than typed.

How far the closure goes
------------------------
Against Hopkins (2007) Table A1, PDF page 634 (printed p. 607), which prints
both columns for six gases at the 20 degC and 1,013e5 Pa its own footnote
states, the speeds land within 0,5 m/s for all six and the densities within
0,002 kg/m3 for the four light ones. Carbon dioxide is 0,7 % low and sulphur
hexafluoride 2 % low, which is the compressibility factor and not an error in
the arithmetic: SF6 is a heavy molecule whose attraction is not negligible at
room conditions, and it is exactly the gas a demonstration reaches for. The
model says so in [`IDEAL_GAS_VALIDITY`](/phonometry/reference/api/fluids/gas/#ideal_gas_validity) rather than pretending otherwise.

What it does not give
---------------------
Viscosity, thermal conductivity and the Prandtl number are transport
properties. Nothing in the ideal-gas closure determines them, so the returned
fluid does not carry them and reading one raises
[`FluidPropertyUnavailable`](/phonometry/reference/api/fluids/fluids/#fluidpropertyunavailable) naming the model, which is
what every other fluid here does with a quantity its model did not fix.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ideal_gas

```python
ideal_gas(
    *,
    temperature_c: float,
    heat_capacity_ratio: float,
    molar_mass_kg_mol: float,
    static_pressure_pa: float | None = None,
) -> Fluid
```

A gas at one state, from its ratio of specific heats and molar mass.

$c = \sqrt{\gamma R T / M}$ and $\rho = p M / (R T)$, the two
ideal-gas relations, which is all a table that prints `gamma` and `M`
supports. See the module docstring for how far that goes and what it leaves
out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `temperature_c` | Temperature `t`, in degrees Celsius (above absolute zero). |
| `heat_capacity_ratio` | Ratio of specific heats `gamma` (> 1). It is 1,67 for a monatomic gas, about 1,4 for a diatomic one and lower for a polyatomic one, and it is above 1 for every gas, because `gamma` is `c_p/c_v` and `c_p - c_v` is the gas constant. |
| `molar_mass_kg_mol` | Molar mass `M`, in kg/mol (> 0). The tables print kg/mol, so 0,028 95 for dry air and not 28,95. |
| `static_pressure_pa` | Static pressure `p`, in pascals (> 0). When omitted, one standard atmosphere is assumed and a [`FluidAssumptionWarning`](/phonometry/reference/api/fluids/fluids/#fluidassumptionwarning) says so, because the density is proportional to it. |

**Returns:** The [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) at that state, carrying a density, a speed of sound and the ratio of specific heats it was given.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a temperature at or below absolute zero. |

## IDEAL_GAS_VALIDITY

*Constant* (`str`).

```python
IDEAL_GAS_VALIDITY = 'ideal gas: exact for a dilute gas and within about 1 % of a printed table for the light gases at room conditions. The error is the compressibility factor and it grows with the molecule: carbon dioxide is 0,7 % and sulphur hexafluoride 2 % against Hopkins Table A1.'
```

## MOLAR_GAS_CONSTANT

*Constant* (`float`).

```python
MOLAR_GAS_CONSTANT = 8.31446261815324
```
