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
and D'Antonio say so explicitly and mark each row with the fit it belongs to,
which is why a surface there is several rows: the same grass fitted with the
Delany and Bazley model, with the semi-phenomenological model and with the
variable-porosity model is three numbers, and averaging them would be an
average of three different quantities.

Why the numbers spread the way they do
--------------------------------------
Bies, Hansen and Howard gather theirs from four sources and print the spread
as they found it, warning on the facing page that "there are great variations
in flow resistivity measured data from different sources". Grass runs from
100 to 300 kPa s/m2 in one row of that table; the same grass is 4 to 850
kPa s/m2 across the fits Cox tabulates. A row is a place to start, not a
measurement of your site.

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
ground_surfaces_named(name: str) -> tuple[GroundSurface, ...]
```

Every published row for a surface name, across the tables.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The surface as a table prints it, matched without regard to case. |

**Returns:** The rows whose [`GroundSurface.name`](/phonometry/reference/api/environment/ground-surfaces/#groundsurface) matches, in the order the tables are read, which is empty when no page names it.

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
| `porosity` | Open porosity, where the fit that produced the resistivity also produced one. |
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
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and it always follows again from the row's own cells. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page carries from another row (`carried` does). |
| `converted` | Field to `(figure, unit)`, the number and the unit the page prints, for a value this row holds in another unit. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. |
| `carried` | Field to where the page carries it from, for a cell the page leaves blank because the value is printed once for a block of rows: a figure on the first row of a group, or "Parecido al anterior". The value is the page's, and this says which of its rows prints it. |
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

### GroundSurface.basis_of()

```python
GroundSurface.basis_of(field_name: str) -> str
```

What the source says this field is: measured, declared, estimated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say. Otherwise one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

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

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or prints on another row and leaves blank on this one, answers `False`: the number is the page's, and `converted` or `carried` says so.

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

### GroundSurface.why_missing()

```python
GroundSurface.why_missing(field_name: str) -> str
```

Why this field is `None`, in the page's own terms.

A catalogue that answers `None` and stops is asking the caller to
guess whether the material has no such property, whether the book
measured it and printed a dash, or whether the cell holds something
that is not a number. Each of those is a different answer.

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
