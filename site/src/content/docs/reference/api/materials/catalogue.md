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
would be inventing a tortuosity nobody published, so
[`unquantified`](/phonometry/reference/api/io/io/#cataloguerow) carries the word instead and
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) hands it back.

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
porous_materials_named(
    name: str,
    *,
    catalogue: Mapping[str, PorousMaterial] | None = None,
) -> tuple[PorousMaterial, ...]
```

Every row for a specimen name, across the tables.

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
| `catalogue` | The rows to search in place of [`PUBLISHED_POROUS`](/phonometry/reference/api/materials/catalogue/#published_porous): a catalogue of your own that [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) returns, `PUBLISHED_POROUS \| mine` to search both at once, or any mapping of key to row (Default: `None`, which searches [`PUBLISHED_POROUS`](/phonometry/reference/api/materials/catalogue/#published_porous)). |

**Returns:** The rows whose [`PorousMaterial.name`](/phonometry/reference/api/materials/catalogue/#porousmaterial) matches, in catalogue order, which is empty when no row names it.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a *catalogue* that is not a mapping, or that holds a row that is not a [`PorousMaterial`](/phonometry/reference/api/materials/catalogue/#porousmaterial), naming its key. |

## PorousMaterial

```python
PorousMaterial(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    basis: Mapping[str, str] = ...,
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
    converted: Mapping[str, tuple[str, str]] = ...,
    carried: Mapping[str, str] = ...,
    ranges: Mapping[str, tuple[float | None, float | None]] = ...,
    bounded_above: frozenset[str] = frozenset(),
    bounded_below: frozenset[str] = frozenset(),
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = ...,
    unquantified: Mapping[str, str] = ...,
    uncertainty: Mapping[str, float] = ...,
    not_derivable: Mapping[str, str] = ...,
    misprinted: Mapping[str, str] = ...,
    attributed_to: Mapping[str, str] = ...,
    group: str = '',
    note: str = '',
    provenance: Provenance | None = None,
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
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) says what
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
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and on every row the library builds it follows again from the row's own cells: `from_printed` writes it, and nothing else in the library does. One a caller passes to the literal constructor is the caller's word, which the row keeps and `printed_fields` leaves out with its value, as it leaves out every derived one. When the printed cells a value rests on do not all have one `basis`, the text names the basis of each, so a modulus worked out from a plate speed and a Poisson ratio Hopkins marks as an estimate says it rests on that estimate. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
| `converted` | Field to `(figure, unit)`, the page's figure and the unit it is in, for a value this row holds in a unit the page does not use. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. The unit is the one the page prints with the figure or over its column. Long prints the figures of his musician bare, and the sabins recorded for them are a reading of the table, which is set in inches and pounds and names sabins on the next row; that row's note says so. A figure written in another unit of the same kind as the field's (`thickness_m` for `thickness_mm`, `flow_resistivity_kpa_s_m2` for `flow_resistivity_pa_s_m2`) is converted by `from_printed` and recorded here, whether it is a value, the end of a range or one of several readings; for a range the figure is the printed end of a bound, or both ends as `"5 to 10"`, and for readings the list as the page gives it. A packaged table transcribed in the base unit with only its SI prefix changed, such as the megapascals of Rossing Table 15.5, holds no entry here, and the table's `about` says so. |
| `carried` | Field to where the page gives it from, for a value the page gives by reference to another of its rows rather than on this one: a cell left blank under a block whose first row prints the figure, as in Ver and Beranek Table 8.7, or a description that reads "Parecido al anterior" and prints no row number, as three rows of Harris Chapter 32 do, which refers to the row above it. The value is the page's, and this says which of its rows gives it. |
| `ranges` | `(low, high)` for each field the page prints as an interval rather than a value. One end is `None` only for a bound whose open side the quantity has no limit on; the end the page prints is always a number, and a two-sided interval has two. |
| `bounded_above` | The subset of `ranges` the page prints as `< x` or `<= x`, where the low end is a floor and not a measurement. |
| `bounded_below` | The subset of `ranges` the page prints as `> x` or `>= x`, where the high end is the ceiling the quantity cannot pass and not a measurement: Cox gives an aerogel a porosity of `>0.75`, and the 1 beside it is what a porosity is, not what anybody measured. A quantity with no such ceiling leaves that end `None` rather than borrowing a number for it: ASHRAE prints `>45` for a duct wall whose radiated sound the background swamped, and a transmission loss has no value it cannot pass, so the open end is empty. It is never an infinity, which is not a number the page has and not a token JSON can carry. |
| `reported` | Field to the values the page lists for it, for a cell that prints several with no single one: `"25, 207, 230"` or `"96, 200-450"`, readings from as many studies. Each entry is a number or a `(low, high)` pair. Not a range, because the page did not print one, and not variants, because the page does not say which is which. |
| `unquantified` | Field to what the page printed in place of a number, for a cell that is neither empty nor numeric: `"Varies with frequency"`, `"model"`, `"…"` for a row of dots. What the page printed, and never a sentence about why the number is missing: `why_missing` composes that sentence around it, so a caller and a published table both get the cell as it reads on the page. |
| `uncertainty` | Field to the plus-or-minus the page prints beside the value, in the same unit. Cox prints an effective flow resistivity of `(540 +/- 92) x 10^3`, and two of his rows print an uncertainty as large as the value itself. What the interval means is not stated on the page, so it is not stated here either: it is the number the page prints beside the value and nothing more. |
| `misprinted` | Field to what the page prints there and why it cannot be that, for a cell whose defect is confirmed and registered in `docs/ERRATA.md`. The number is not served, because a catalogue that handed it over would put a value its own registry calls wrong behind every calculation downstream; it is not dropped either, because a reader reproducing the book needs to see what the book says. This is the narrowest of the hedges and the one that costs most to claim: a cell earns it only when the defect follows from the page itself or from something as settled as the molar mass of a named molecule, and never from one book disagreeing with another. |
| `not_derivable` | Field to why this library leaves it empty although the arithmetic would reach it. Bies leaves the speed of his aluminium honeycomb panels blank, and the modulus and the density beside it are effective ones, so `sqrt(E/rho)` would put a one-dimensional speed on a panel that has none. A row says so here, and nothing fills the cell afterwards. |
| `attributed_to` | Credit for a cell the book takes from someone else. Keyed by field name, or by `"row"` or `"table"` when the credit covers all of one. |
| `group` | The heading of the block this row sits under, when the table prints its rows in named groups: Cox files each material under `"Fibrous materials"`, `"Cellular materials"`, `"Granular materials"` or `"Other"`. Empty for a table that prints one list. |
| `note` | What the page says about this row beyond its numbers. |
| `provenance` | The document the row was read from, for a row read from a caller's catalogue file: its kind, version, the day it was consulted, the laboratory and the report. `None` on every packaged row, whose `source` cites a page. A refusal names the document by its kind (`"the datasheet prints an upper bound of ..."`), where a row without one says `"the page"`; and the fields of its `field_test_standards` are fields of the row. |

### PorousMaterial.basis_of()

```python
PorousMaterial.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

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
[`derived`](/phonometry/reference/api/io/io/#cataloguerow) says so.

The loss factor is asked for like the other two. A row whose page
prints the moduli and no loss factor is refused rather than handed
a frame with `eta_s = 0`: a lossless frame is a claim about the
material, and a cell the page left empty is not a zero. Every
published row that prints both moduli prints the loss factor too.

**Returns:** `(shear_modulus_pa, poisson_ratio)`, the first complex.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the source prints no elastic constants, or prints them without a structural loss factor, in which case the message says what the page had in that cell instead. |

### PorousMaterial.from_printed()

*classmethod*

```python
PorousMaterial.from_printed(**cells: Any) -> Self
```

A row built from the cells its page prints, completed and marked.

The one path that works anything out. The cells are what the page
prints, under the field names of the class and with the hedges each
cell carries, as a data file writes them. A figure written in another
unit of the same kind as its field (`thickness_m` for
`thickness_mm`, `flow_resistivity_kpa_s_m2` for
`flow_resistivity_pa_s_m2`), or in a unit the class takes as an
alias of its own (an
[`AbsorptionAreaSpectrum`](/phonometry/reference/api/materials/measured/#absorptionareaspectrum) takes
`absorption_area_125_ft2` for `absorption_area_125_m2`), is
converted on its digits with an exact factor and rounded once,
whether it is a value or stands as the key of a hedge (the ends of a
range, the readings of a list and a plus-or-minus convert with it),
and `converted` records the figure and its unit. Every number
of one cell is written in one unit. The row is then
built and held to the contract the class docstring lists, so every
cell is checked before any arithmetic reads it. Last, the class
fills what follows from those cells (a modulus from a plate speed, a
density and a Poisson ratio), never over a cell that holds a value
or one the row says something else about, and `derived` says
how each filled value was reached and, when the cells it rests on
do not share one `basis`, the basis of each. Cells the
arithmetic cannot take are refused rather than turned into a value
that would be wrong: a modulus of 1 GPa and a shear modulus of
0.1 GPa give a Poisson ratio of 4, which no isotropic solid has, and
a row whose cells are not meant to give a value says so in
`not_derivable`, which keeps the arithmetic from running.

`Cls(...)` stays literal: it holds what it is given and works
nothing out. To change a cell of a row and have what follows from
it follow again, change it in `printed_fields` and build again
here; `dataclasses.replace` would copy the derived values as they
were:

```text
cells = row.printed_fields()
cells["density_kg_m3"] = 2400.0
row = type(row).from_printed(**cells)
```

**Parameters**

| Name | Description |
| :--- | :--- |
| `cells` | The printed cells, as keywords of the class. |

**Returns:** The row, with what follows from its cells filled in.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for a cell the contract refuses; for a `derived` among the cells, which is this method's to write; for a figure under a unit alias that is not a finite number, or that names a cell given under its own name or under another alias as well; for the numbers of one cell written in two units, a name two fields of one kind could both take, or a figure whose text field saying what it is of is empty; and for printed cells a value that follows from them cannot be worked out of, naming the value and the cells. |
| TypeError | for a name that is neither a field of the class nor a unit alias of one. |

### PorousMaterial.is_approximate()

```python
PorousMaterial.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### PorousMaterial.is_derived()

```python
PorousMaterial.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

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

### PorousMaterial.printed()

```python
PorousMaterial.printed(
    field_name: str,
    *,
    wanted_by: str = 'the caller',
) -> float
```

One quantity this page prints, or a refusal that says what it had.

Every quantity of a row is optional, because the pages print different
columns, so a caller passing one into a function that requires a float
has to narrow it. Doing it here beats an assertion at each call site:
the refusal names the field, who wanted it and what the page had in
that cell, which is the difference between a cell the book left empty
and a cell holding the word "model".

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | The quantity wanted. |
| `wanted_by` | What wants it, named in the message. |

**Returns:** The value, as a float.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page did not print a number there. |

### PorousMaterial.printed_fields()

```python
PorousMaterial.printed_fields() -> dict[str, Any]
```

The cells the page prints, as `from_printed` takes them.

Every field, the name, the citation, the table and every hedge
included, except the values this library derived, `derived`
itself, and a field left at a default that holds nothing (a quantity
the page leaves out, an empty text or hedge). A text field whose
default says something is kept even when it holds no text: the
`per` of an area per unit is a person unless the row says
otherwise, and a row that leaves it empty has said otherwise. A
value converted from the page's unit and one the page gives by
reference to another of its rows are the page's, so they stay, with
`converted` and `carried` beside them.

For every row `from_printed` builds, and so for every packaged
one, `type(row).from_printed(**row.printed_fields())` is the row
again, and changing a cell before building it again is how a row is
edited without carrying a derived value that no longer follows from
it. A `derived` passed to the literal constructor is the caller's
own; it is left out here with its value, like every derived one, so
building again gives back only what the class works out.

**Returns:** A new dictionary of constructor keywords. The values are the ones the row holds, frozen as the row holds them.

### PorousMaterial.why_missing()

```python
PorousMaterial.why_missing(field_name: str) -> str
```

Why this field is `None`, in the page's own terms.

A catalogue that answers `None` and stops is asking the caller to
guess whether the material has no such property, whether the book
measured it and printed a dash, or whether the cell holds something
that is not a number. Each of those is a different answer.

The sentence names the document by its kind: `"the datasheet"`,
`"the test report"`, and `"the page"` for a row with no
`provenance`, which is every packaged one. For a cell the row
holds in another unit than the page's, a bound, a range or a list
quotes the page's figure and unit first and the row's value after
it: `"the datasheet prints a lower bound of 5 kPa s/m2 (5000 Pa
s/m2) and no value"`, never a figure the page does not print.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** What the page had in that cell, or the empty string when the field is not missing at all. A field the page has no column for and this library cannot derive, because the cells it would need are themselves a range, answers that it does not follow.

**Raises**

| Exception | When |
| :--- | :--- |
| AttributeError | for a name this class does not have, because a misspelt field would otherwise answer as if the cell were empty. |

## PUBLISHED_POROUS

*Constant* (`mapping`).
