---
title: "materials.absorbers.catalogue"
description: "Porous specimens as the pages that print them have them."
sidebar:
  label: "catalogue"
---

Porous specimens as the pages that print them have them.

The five-parameter models of [`porous`](/phonometry/reference/api/materials/porous/)
take a flow resistivity, a porosity, a tortuosity and two characteristic
lengths, and a caller who has not characterised a specimen to ISO 9053 and
ISO 10534-2 has nowhere to get them. They get them here, from a book, with
the page the row came off attached to it.

What it is careful about
------------------------
A parameter table is a set of numbers someone fed a model, not a set of
measurements of a material, and the books say so in different ways. Allard and
Atalla print thirty-odd such rows across nineteen tables, every one of them
the input to a worked example, and one of the rows prints the word `model`
in three of its cells because the quantity there is frequency dependent and no
single number stands for it. A catalogue that turned that word into a float
would be inventing a tortuosity nobody published, so `CatalogueRow.unquantified` carries the word instead and `CatalogueRow.why_missing`
hands it back.

The same applies to the elastic constants. Table 6.1 prints a complex shear
modulus, `220(1 + j0.1)` N/cm2, and Table 11.8 prints the same specimen as a
Young's modulus of 4,4 MPa with a structural loss factor of 0,1; they agree,
because `E / (2(1 + nu))` is the real part of the first. A row therefore
stores the real modulus and the loss factor separately, which is the form the
poroelastic models take them in, and [`PorousMaterial.frame_constants`](/phonometry/reference/api/materials/catalogue/#porousmaterialframe_constants)
puts the complex number back together.

Two kinds of row
----------------
A **specimen** row is one sample, with every parameter a model needs beside
it: Allard and Atalla's tables are all of this kind, and a row of one of them
reproduces the worked example it belongs to. A **compiled** row is one
quantity over a class of material, gathered by its book from the literature:
Cox and D'Antonio compile a flow resistivity, a fibre diameter, a porosity,
two characteristic lengths and a tortuosity, and Mechel compiles a porosity
and the fibre data of three product groups. Almost every compiled cell is an
interval, because there is no such thing as the porosity of mineral wool,
only the range the measurements fall in, and a row that answered with the
midpoint of that range would be inventing a measurement.

The two kinds sit in one catalogue because they answer one question between
them: [`porous_materials_named`](/phonometry/reference/api/materials/catalogue/#porous_materials_named) asks a name of every book at once, and a
specimen that falls outside the range its class is compiled in is worth
knowing about. What tells them apart is what a row holds: a specimen carries
several quantities, a compiled row carries one, and the compiled one carries
it as a range.

Where the rows live
-------------------
In `absorbers/data/*.json`, one file per published table, read at import
through the package-data reader in `phonometry._internal`. The citation is
written once, in the file that holds the rows it belongs to, and the
provenance gate reads it from there.

What it is not
--------------
It is not a material database. Every row here is a parameter set from a worked
example of a book, which is what makes it reproducible and also what makes it
specific: the foam of one figure is that foam, not foam. Use a row to
reproduce the example it belongs to, to sanity-check an implementation, or to
get an order of magnitude; characterise a specimen for anything that has to be
right.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## porous_materials_named

```python
porous_materials_named(name: str) -> tuple[PorousMaterial, ...]
```

Every published row for a specimen name, across the tables.

Comparing two printings of one specimen is the point of holding both, and
it has to be a deliberate act: a lookup that returned one row for "Foam"
would be choosing between published parameter sets on the caller's behalf,
and one of these books prints five different foams under that name. Across
the books it also puts a measured specimen beside the range its class is
compiled in: "Mineral wool" answers with Allard's specimen and with the
two ranges Cox compiles for it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The specimen name as a table prints it, matched without regard to case: `"Foam"`, `"foam"`. |

**Returns:** The rows whose [`PorousMaterial.name`](/phonometry/reference/api/materials/catalogue/#porousmaterial) matches, in the order the tables are read, which is empty when no page names it.

## PorousMaterial

```python
PorousMaterial(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
    ranges: Mapping[str, tuple[float, float]] = ...,
    bounded_above: frozenset[str] = frozenset(),
    bounded_below: frozenset[str] = frozenset(),
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = ...,
    unquantified: Mapping[str, str] = ...,
    uncertainty: Mapping[str, float] = ...,
    not_derivable: Mapping[str, str] = ...,
    attributed_to: Mapping[str, str] = ...,
    group: str = '',
    note: str = '',
    flow_resistivity_pa_s_m2: float | None = None,
    porosity: float | None = None,
    tortuosity: float | None = None,
    viscous_length_um: float | None = None,
    thermal_length_um: float | None = None,
    thermal_permeability_m2: float | None = None,
    fibre_diameter_um: float | None = None,
    fibre_diameter_distribution_parameter: float | None = None,
    shot_content_percent: float | None = None,
    binder_content_percent: float | None = None,
    frame_density_kg_m3: float | None = None,
    thickness_mm: float | None = None,
    youngs_modulus_pa: float | None = None,
    shear_modulus_pa: float | None = None,
    poisson_ratio: float | None = None,
    structural_loss_factor: float | None = None,
)
```

One row of a published table of porous-material parameters.

Every quantity is optional, because no two tables print the same columns:
a chapter on the Biot theory prints a shear modulus and no characteristic
length, a chapter on the transfer matrix prints both lengths and a Young's
modulus, and the one anisotropic table prints two flow resistivities and
no elastic constant the isotropic models can take. A field is `None`
when the page had nothing to put there, and
`why_missing` says what
it had instead.

The name, the citation, the variant and the hedges a cell can carry
instead of a number are the ones every catalogue row has.

**Attributes**

| Name | Description |
| :--- | :--- |
| `flow_resistivity_pa_s_m2` | Airflow resistivity `sigma`, in Pa s/m2. The books print it as N s/m4, N m-4 s or rayl/m, which are three spellings of the same unit. |
| `porosity` | Open porosity `phi`. |
| `tortuosity` | Tortuosity `alpha_inf`. |
| `viscous_length_um` | Viscous characteristic length `Lambda`, in micrometres, the unit the tables print it in. The `viscous_length` parameter of [`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) is in **metres**, so this field is not passed to it directly: `medium` makes the conversion, once, and a caller who assembles the argument list by hand divides by a million first. |
| `thermal_length_um` | Thermal characteristic length `Lambda'`, in micrometres. Metres at the model's `thermal_length`, as above. |
| `thermal_permeability_m2` | Static thermal permeability `q'_0`, in m2, which two of the tables print beside the thermal length. |
| `fibre_diameter_um` | Fibre diameter `d`, in micrometres, for the materials a table describes by the fibre rather than by the pore. |
| `fibre_diameter_distribution_parameter` | The parameter of the Poisson distribution Mechel fits to a measured spread of fibre diameters, referred to a diameter class one micrometre wide. Dimensionless: the micrometre in the column heading belongs to the class width, which is stated in the file's `about` because the value means nothing without it. |
| `shot_content_percent` | Shot content, per cent **by weight**, of particles above the diameter the table's own heading names. |
| `binder_content_percent` | Organic binder content, per cent by weight. |
| `frame_density_kg_m3` | Frame density `rho_1`, in kg/m3, the mass of the skeleton per unit volume of material and not the density of the material the skeleton is made of. |
| `thickness_mm` | Layer thickness `h` of the specimen as tabulated, in millimetres. It is the thickness of the layer the table describes and not a property of the material: the same material appears in other tables of the same book at other thicknesses. |
| `youngs_modulus_pa` | In-vacuo Young's modulus `E` of the frame, in pascals. |
| `shear_modulus_pa` | In-vacuo shear modulus `N`, in pascals, **real**. A page that prints it complex, as `N(1 + j eta)`, has printed this and `structural_loss_factor`. |
| `poisson_ratio` | Frame Poisson ratio `nu`. |
| `structural_loss_factor` | Structural loss factor `eta_s` of the frame, the imaginary part of the complex modulus over its real part. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read. |
| `ranges` | `(low, high)` for each field the page prints as an interval rather than a value. |
| `bounded_above` | The subset of `ranges` the page prints as `< x` or `<= x`, where the low end is a floor and not a measurement. |
| `bounded_below` | The subset of `ranges` the page prints as `> x` or `>= x`, where the high end is the ceiling the quantity cannot pass and not a measurement: Cox gives an aerogel a porosity of `>0.75`, and the 1 beside it is what a porosity is, not what anybody measured. |
| `reported` | Field to the values the page lists for it, for a cell that prints several with no single one: `"25, 207, 230"` or `"96, 200-450"`, readings from as many studies. Each entry is a number or a `(low, high)` pair. Not a range, because the page did not print one, and not variants, because the page does not say which is which. |
| `unquantified` | Field to what the page printed in place of a number, for a cell that is neither empty nor numeric: `"Varies with frequency"`, `"model"`, `"…"` for a row of dots. What the page printed, and never a sentence about why the number is missing: `why_missing` composes that sentence around it, so a caller and a published table both get the cell as it reads on the page. |
| `uncertainty` | Field to the plus-or-minus the page prints beside the value, in the same unit. Cox prints an effective flow resistivity of `(540 +/- 92) x 10^3`, and two of his rows print an uncertainty as large as the value itself. What the interval means is not stated on the page, so it is not stated here either: it is the number the page prints beside the value and nothing more. |
| `not_derivable` | Field to why this library leaves it empty although the arithmetic would reach it. Bies leaves the speed of his aluminium honeycomb panels blank, and the modulus and the density beside it are effective ones, so `sqrt(E/rho)` would put a one-dimensional speed on a panel that has none. A row says so here, and nothing fills the cell afterwards. |
| `attributed_to` | Credit for a cell the book takes from someone else. Keyed by field name, or by `"row"` or `"table"` when the credit covers all of one. |
| `group` | The heading of the block this row sits under, when the table prints its rows in named groups: Cox files each material under `"Fibrous materials"`, `"Cellular materials"`, `"Granular materials"` or `"Other"`. Empty for a table that prints one list. |
| `note` | What the page says about this row beyond its numbers. |

### PorousMaterial.frame_constants()

```python
PorousMaterial.frame_constants() -> tuple[complex, float]
```

The in-vacuo frame constants `(N, nu)` the source prints.

The complex shear modulus and the Poisson ratio are what
[`biot_waves`](/phonometry/reference/api/materials/biot/#biot_waves),
[`frame_quarter_wave_resonance`](/phonometry/reference/api/materials/biot/#frame_quarter_wave_resonance) and
[`PoroelasticLayer`](/phonometry/reference/api/materials/layered/#poroelasticlayer) take together, and a
table that prints one prints the other, so they are asked for together
and a specimen characterised as a rigid frame alone says so here
rather than handing out a `None` that fails further down.

The shear modulus comes back complex, `N(1 + j eta_s)`, which is the
form the page prints and the models take, rebuilt from the real
modulus and the loss factor the row stores separately. A row whose
page printed a Young's modulus instead has had its shear modulus
derived through the Poisson ratio, and
`derived` says so.

**Returns:** `(shear_modulus_pa, poisson_ratio)`, the first complex.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the source prints no elastic constants. |

### PorousMaterial.medium()

```python
PorousMaterial.medium(
    frequency: ArrayLike,
    *,
    model: str = 'johnson_champoux_allard',
    fluid: Fluid = ...,
) -> PorousMediumResult
```

The equivalent fluid of this specimen.

The characteristic lengths are stored in the micrometres the tables
print and converted, here and once, to the metres
[`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) takes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `model` | `"johnson_champoux_allard"` (Default), `"delany_bazley"` or `"miki"`. The last two read the flow resistivity alone, so they describe a coarser specimen than the one the other four parameters pin. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air)). |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown model name, or when the page does not print a parameter the model needs, in which case the message says what the page had there instead. |

## PUBLISHED_POROUS

*Constant* (`mappingproxy`).
