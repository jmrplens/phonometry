---
title: "environment.propagation.ground_surfaces"
description: "Ground surfaces as the pages that print them print them."
sidebar:
  label: "ground_surfaces"
---

Ground surfaces as the pages that print them print them.

Every outdoor propagation model in this package asks the ground how resistive
it is, and nobody measures that: a prediction over a pasture takes the flow
resistivity of a pasture from a table. This is that table, or rather the three
of them this library reads, with the page each row came off attached to it.

What a ground row is
--------------------
An **effective** flow resistivity, which is not the flow resistivity of the
material under your feet. It is the single number that makes a
semi-infinite, locally reacting, rigid-framed ground model reproduce a
measured excess attenuation, so it carries the model it was fitted with. Cox
and D'Antonio say so explicitly, and where they print a surface once per fit
they mark each line with the fit it belongs to, which is why a surface there
is several rows: the same grass fitted with the Delany and Bazley model, with
the semi-phenomenological model and with the variable-porosity model is three
numbers, and averaging them would be an average of three different
quantities.

Why the numbers spread the way they do
--------------------------------------
Bies, Hansen and Howard gather theirs from four sources and print the spread
as they found it, warning on the facing page that "there are great variations
in flow resistivity measured data from different sources". Grass runs from
100 to 300 kPa s/m2 in one row of that table; the same grass is 4 to 850
kPa s/m2 across the fits Cox tabulates. A row is a place to start, not a
measurement of your site.

Into the outdoor models
-----------------------
[`GroundSurface.medium`](/phonometry/reference/api/environment/ground-surfaces/#groundsurfacemedium) turns a row's resistivity into the porous
half-space [`ground_effect`](/phonometry/reference/api/environment/ground-barriers/#ground_effect),
[`barrier_insertion_loss`](/phonometry/reference/api/environment/ground-barriers/#barrier_insertion_loss) and
[`atmospheric_parabolic_equation`](/phonometry/reference/api/environment/refraction/#atmospheric_parabolic_equation) take as their
ground impedance, through the Delany and Bazley or the
Miki model those functions offer themselves. It reads the resistivity through
[`printed`](/phonometry/reference/api/io/io/#cataloguerowprinted), so a range, a bound or an empty
cell is refused in the page's terms rather than collapsed to one number, and
a row whose page names the model it was fitted with is taken into that model
only.

The classes are a different thing
---------------------------------
Bies's second table is not measured ground at all: it is the eight classes
A to H the propagation models define, with the ground factor G that ISO
9613-2 and NMPB-2008 take and the representative resistivity Harmonoise
assigns each class. Class H is water, and its resistivity is an acoustically
hard stand-in rather than anything anybody measured. Those rows carry
[`GroundSurface.harmonoise_class`](/phonometry/reference/api/environment/ground-surfaces/#groundsurface) and the two ground factors; a model
that wants a class takes the class, and a model that wants a resistivity
takes the resistivity.

Where the rows live
-------------------
In `propagation/data/*.json`, one file per published table, read at import
through the package-data reader in `phonometry._internal`. The citation is
written once, in the file that holds the rows it belongs to.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ground_surfaces_named

```python
ground_surfaces_named(
    name: str,
    *,
    catalogue: Mapping[str, GroundSurface] | None = None,
) -> tuple[GroundSurface, ...]
```

Every row for a surface name, across the tables.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The surface as a table prints it, matched without regard to case. |
| `catalogue` | The rows to search in place of [`PUBLISHED_GROUND`](/phonometry/reference/api/environment/ground-surfaces/#published_ground): a catalogue of your own that [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) returns, `PUBLISHED_GROUND \| mine` to search both at once, or any mapping of key to row (Default: `None`, which searches [`PUBLISHED_GROUND`](/phonometry/reference/api/environment/ground-surfaces/#published_ground)). |

**Returns:** The rows whose [`GroundSurface.name`](/phonometry/reference/api/environment/ground-surfaces/#groundsurface) matches, in catalogue order, which is empty when no row names it.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a *catalogue* that is not a mapping, or that holds a row that is not a [`GroundSurface`](/phonometry/reference/api/environment/ground-surfaces/#groundsurface), naming its key. |

## GroundSurface

```python
GroundSurface(
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
    water_content_percent: float | None = None,
    porosity_decay_rate_per_m: float | None = None,
    iso_9613_ground_factor: float | None = None,
    nmpb_ground_factor: float | None = None,
    harmonoise_class: str = '',
)
```

One ground surface as one table prints it.

Every quantity is optional, because the three tables print three different
sets of columns, and a quantity the page did not print answers `None`
with [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing)
saying what the cell held instead.

**Attributes**

| Name | Description |
| :--- | :--- |
| `flow_resistivity_pa_s_m2` | Effective flow resistivity `R_1` or `sigma_e`, in Pa s/m2. Bies prints it in kPa s/m2 and Cox in rayl/m, which is this unit under another name; the conversion is pinned in the data file's `about`. |
| `porosity` | Open porosity, where the fit that produced the resistivity also produced one, as the fraction of the volume that is open, from 0 to 1. Cox's Table 6.7 prints six of its porosities as 26.9 to 58.1 in a column that prints a fraction on every other row and states no unit; a porosity of 36.5 is not a porosity, so those six cells are empty, and [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) quotes the figure the page prints. |
| `water_content_percent` | Water content of the specimen, per cent, for the sands Cox tabulates wet and dry. The resistivity of a sand is not monotonic in it, which is the point of printing it. |
| `porosity_decay_rate_per_m` | The rate `zeta` at which porosity falls with depth in the variable-porosity model, in 1/m. It is negative for several surfaces, which is what the page prints. |
| `iso_9613_ground_factor` | The ground factor `G` of ISO 9613-2 for a ground class: 0 for hard ground, 1 for porous ground. |
| `nmpb_ground_factor` | The ground factor `G` of NMPB-2008 for the same class, which is not always the ISO one: two of the eight classes differ. |
| `harmonoise_class` | The class letter, `"A"` to `"H"`, for a row of the class table, and the empty string for a measured surface. |
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

### GroundSurface.basis_of()

```python
GroundSurface.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### GroundSurface.from_printed()

*classmethod*

```python
GroundSurface.from_printed(**cells: Any) -> Self
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

### GroundSurface.is_approximate()

```python
GroundSurface.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### GroundSurface.is_derived()

```python
GroundSurface.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### GroundSurface.medium()

```python
GroundSurface.medium(
    frequency: ArrayLike,
    *,
    model: Literal['delany_bazley', 'miki'] = 'delany_bazley',
    fluid: Fluid = ...,
) -> PorousMediumResult
```

The ground as a semi-infinite porous half-space.

The outdoor models take a ground as the normalized surface impedance
of a locally reacting half-space, which is the characteristic
impedance of its porous medium; this is that medium, worked out from
the row's effective flow resistivity with the Delany and Bazley or
the Miki model, and it goes into
[`ground_effect`](/phonometry/reference/api/environment/ground-barriers/#ground_effect) as `impedance`,
[`barrier_insertion_loss`](/phonometry/reference/api/environment/ground-barriers/#barrier_insertion_loss) as
`ground_impedance` and
[`atmospheric_parabolic_equation`](/phonometry/reference/api/environment/refraction/#atmospheric_parabolic_equation) as
`impedance`, unchanged. Those functions work out the same medium from a bare
`flow_resistivity`; this is the path for a row, which keeps the
refusal of a cell the page did not print as a number.

An effective flow resistivity is the parameter of the model it was
fitted with, and Cox and D'Antonio name that model for some of their
rows. Where they print a surface once per fit, a footnote marks each
line, and the row's [`variant`](/phonometry/reference/api/io/io/#cataloguerow)
quotes it; for the two sands Horoshenkov and Mohamed measured at four
water contents, the text beside the table says the parameters are
those of the two-parameter model of Attenborough. A row fitted with
the Delany and Bazley model is taken into that model only, and a row
fitted with the semi-phenomenological, the variable-porosity or the
two-parameter model into neither of the two here, because its
resistivity is not a parameter of either. A row whose page names no
fit, most of Cox's, every one of Bies's and a caller's own, is taken
into both.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `model` | `"delany_bazley"` (Default) or `"miki"`, the two ground models the outdoor functions take. |
| `fluid` | The air above the ground, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air the two models were published with, as the outdoor functions default to). |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult), in the materials domain's time convention, which the outdoor functions convert themselves.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a model other than the two, for a row whose page names another fit than *model*, or when the row holds no number for the resistivity, in which case the message says what the page has there instead. |

### GroundSurface.printed()

```python
GroundSurface.printed(
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

### GroundSurface.printed_fields()

```python
GroundSurface.printed_fields() -> dict[str, Any]
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

### GroundSurface.why_missing()

```python
GroundSurface.why_missing(field_name: str) -> str
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

## PUBLISHED_GROUND

*Constant* (`mapping`).
