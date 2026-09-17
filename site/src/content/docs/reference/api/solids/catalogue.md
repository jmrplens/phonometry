---
title: "solids.catalogue"
description: "Solid materials as one published table prints them."
sidebar:
  label: "catalogue"
---

Solid materials as one published table prints them.

A caller who needs a Young's modulus for plasterboard has two bad options and
one good one. They can type a number they half remember, or they can open a
book and copy a row by hand into their script, which is the same thing with
extra steps. The good one is to read the row from a catalogue that says which
page it came from, and that is what this module is.

What it is careful about
------------------------
A materials table is not a list of measurements. Hopkins Table A2 marks most
of its Poisson ratios and internal loss factors with a footnote that reads,
in full, "Estimate", and it prints some of its densities as a range rather
than a number, some of its loss factors as an upper bound, and one of its wave
speeds with a note that the material is orthotropic and the figure quoted is
an effective value. A catalogue that flattened all of that into floats would
be claiming twenty-five measured Poisson ratios where the page offers four.

So every row carries what the cell actually said: [`SolidMaterial.estimated`](/phonometry/reference/api/solids/catalogue/#solidmaterial)
names the fields the page marks as estimates, [`SolidMaterial.ranges`](/phonometry/reference/api/solids/catalogue/#solidmaterial)
carries the two densities and the one loss factor printed as an interval,
[`SolidMaterial.bounded_above`](/phonometry/reference/api/solids/catalogue/#solidmaterial) names the two loss factors printed as
`<=`, and [`SolidMaterial.attributed_to`](/phonometry/reference/api/solids/catalogue/#solidmaterial) carries the per-cell credit for
the rows whose columns come from different authors. A field the table leaves
empty is `None` and not a guess.

What it is not
--------------
It is not a specification. Block densities vary by manufacturer, boards vary
by batch, and Hopkins says as much by printing ranges where a range is what is
known. Use a row to reproduce a worked example, to sanity-check a measurement,
or to get an order of magnitude; use a measurement for anything that has to be
right.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_SOLIDS

*Constant* (`dict`).

## SolidMaterial

```python
SolidMaterial(
    name: str,
    longitudinal_speed_m_s: float,
    poisson_ratio: float,
    thickness_critical_frequency_product_m_hz: float,
    density_kg_m3: float | None = None,
    loss_factor: float | None = None,
    estimated: frozenset[str] = frozenset(),
    ranges: Mapping[str, tuple[float, float]] = ...,
    bounded_above: frozenset[str] = frozenset(),
    attributed_to: Mapping[str, str] = ...,
    note: str = '',
    source: str = 'Hopkins (2007) Table A2, PDF pages 635-636 (no printed folio; between folios 607 and 610)',
)
```

One row of a published materials table, with what the cell said.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The material as the table names it, attribution stripped. |
| `longitudinal_speed_m_s` | Quasi-longitudinal phase velocity `c_L`, in m/s. Hopkins' footnote a states these "can be used as estimates for beams or plates", so the column is the plate speed for the purposes of [`youngs_modulus_from_plate_speed`](/phonometry/reference/api/solids/elastic/#youngs_modulus_from_plate_speed). |
| `poisson_ratio` | Poisson's ratio `nu`. |
| `thickness_critical_frequency_product_m_hz` | The `h.f_c` column, in m Hz, computed by the book for the 343 m/s its heading states. |
| `density_kg_m3` | Density `rho`, in kg/m3, or `None` when the table prints a range instead of a value. The range is then in `ranges`. |
| `loss_factor` | Internal loss factor for bending waves `eta_int`, or `None` when the table prints a dash, a range or an upper bound. |
| `estimated` | The fields the page marks with its "Estimate" footnote. Reading one of these as a measurement is the mistake this catalogue exists to prevent. |
| `ranges` | `(low, high)` for each field the table prints as an interval rather than a value. |
| `bounded_above` | Fields the table prints as `<= x`, with `x` in `ranges` as `(0.0, x)`. |
| `attributed_to` | Per-field credit, for the rows whose columns the book takes from different authors. |
| `note` | What the table says about this row beyond its numbers. |
| `source` | Document, table and PDF pages. |

### SolidMaterial.is_estimate()

```python
SolidMaterial.is_estimate(field_name: str) -> bool
```

Whether the page marks this field as an estimate rather than a value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the table carries its "Estimate" footnote there.

### SolidMaterial.youngs_modulus_pa()

```python
SolidMaterial.youngs_modulus_pa() -> float
```

Young's modulus from the printed speed and density, in pascals.

The table prints a wave speed and a density and no modulus, and the
functions this library hands a solid to want the modulus, so the
inversion happens here rather than in the caller's head. It is
[`youngs_modulus_from_plate_speed`](/phonometry/reference/api/solids/elastic/#youngs_modulus_from_plate_speed) on this
row's own numbers.

**Returns:** Young's modulus `E`, in pascals.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a row whose density the table printed as a range, because there is then no density to invert with. |
