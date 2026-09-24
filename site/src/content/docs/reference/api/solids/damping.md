---
title: "solids.damping"
description: "Commercial damping materials, with the temperature and the frequency."
sidebar:
  label: "damping"
---

Commercial damping materials, with the temperature and the frequency.

Every other loss factor this library holds is a figure with no conditions
attached. Bies prints 0.0001 for mild steel, Cremer a band of 0.00002 to
0.0003 for steel and Hopkins one of 0 to 0.0001, and not one of them says at
what temperature or at what frequency, because for a metal it hardly moves.
For the materials on this page it moves by two orders of magnitude, and
neither a number nor a band is a property of them at all.

A viscoelastic damping treatment is a polymer worked near its glass
transition. Below that transition it is stiff and stores the energy it is
given; above it, it is soft and stores almost none; and in the narrow band
between, it turns a large part of each cycle into heat. The loss factor peaks
in that band, and the band moves up in temperature as the frequency rises.
That is why [`DampingMaterial.max_loss_factor`](/phonometry/reference/api/solids/damping/#dampingmaterial) is useless on its own and
why this table prints three temperatures beside it: the temperature at which
the peak occurs when the material is worked at 10 Hz, at 100 Hz and at
1000 Hz. A material whose peak sits at 20 C at 100 Hz is doing nothing for you
at 100 Hz on a winter morning.

The four moduli follow the same argument. `youngs_modulus_max_pa` is the
stiff end, low temperature or high frequency; `youngs_modulus_min_pa` is
the soft end; `youngs_modulus_transition_pa` is the one that applies in
the band where the loss factor peaks, which is the only one of the three that
belongs beside `max_loss_factor`. The fourth,
`loss_modulus_max_pa`, is not a storage modulus at all: it is the
imaginary part, and the running text gives it as the product of the other two,
which is the cheapest check there is on a row of this table.

Where the rows live
-------------------
In `solids/data/ver-beranek-2006-table-14-1.json`, read at import through the
package-data reader in `phonometry._internal`, the same as every other
catalogue here.

What it is not
--------------
It is not a specification and it is not a measurement. The page says in a
footnote that the values were read off published curves, and the text around
it says to get damping data from the supplier of the material. Three of its
cells are corrupted in the printing; they are registered in `docs/ERRATA.md`
and this catalogue refuses them rather than guessing what the digits were.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## damping_named

```python
damping_named(name: str) -> tuple[DampingMaterial, ...]
```

Every damping material whose name contains *name*, case-insensitively.

A tuple and not one row, because a name can be printed by more than one
table and this catalogue never chooses between books on the caller's
behalf.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Part of a material name, as its page prints it. |

**Returns:** The matching rows, in catalogue order. Empty when none match.

## DampingMaterial

```python
DampingMaterial(
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
    max_loss_factor: float | None = None,
    peak_temperature_at_10_hz_c: float | None = None,
    peak_temperature_at_100_hz_c: float | None = None,
    peak_temperature_at_1000_hz_c: float | None = None,
    youngs_modulus_max_pa: float | None = None,
    youngs_modulus_min_pa: float | None = None,
    youngs_modulus_transition_pa: float | None = None,
    loss_modulus_max_pa: float | None = None,
)
```

One commercial damping material, as its published table prints it.

The name, the citation and the hedges a cell can carry instead of a number
are the ones every catalogue row has. What this class adds is that a loss
factor here is never alone: it comes with the temperature at which it
peaks, once per printed frequency.

**Attributes**

| Name | Description |
| :--- | :--- |
| `max_loss_factor` | The greatest loss factor the material reaches, dimensionless. Not the loss factor at any temperature you happen to have: the peak, which the temperatures below locate. |
| `peak_temperature_at_10_hz_c` | Temperature at which `max_loss_factor` occurs when the material is worked at 10 Hz. |
| `peak_temperature_at_100_hz_c` | The same at 100 Hz. |
| `peak_temperature_at_1000_hz_c` | The same at 1000 Hz. |
| `youngs_modulus_max_pa` | Storage Young's modulus at the stiff end, for low temperatures or high frequencies. |
| `youngs_modulus_min_pa` | Storage Young's modulus at the soft end, for high temperatures or low frequencies. |
| `youngs_modulus_transition_pa` | Storage Young's modulus in the band where the loss factor peaks, which is the one that belongs beside `max_loss_factor`. |
| `loss_modulus_max_pa` | The greatest value of the loss (imaginary) modulus. The chapter gives it as the product of the two above it, so a row where it is not about `max_loss_factor * youngs_modulus_transition_pa` is worth a second look at the page. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and on every row the library builds it follows again from the row's own cells: `from_printed` writes it, and nothing else in the library does. One a caller passes to the literal constructor is the caller's word, which the row keeps and `printed_fields` leaves out with its value, as it leaves out every derived one. When the printed cells a value rests on do not all have one `basis`, the text names the basis of each, so a modulus worked out from a plate speed and a Poisson ratio Hopkins marks as an estimate says it rests on that estimate. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
| `converted` | Field to `(figure, unit)`, the page's figure and the unit it is in, for a value this row holds in a unit the page does not use. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. The unit is the one the page prints with the figure or over its column. Long prints the figures of his musician bare, and the sabins recorded for them are a reading of the table, which is set in inches and pounds and names sabins on the next row; that row's note says so. A figure a packaged table prints with another SI prefix, such as the megapascals of Rossing Table 15.5, is held in the base unit with no entry here, and the table's `about` says so. |
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

### DampingMaterial.basis_of()

```python
DampingMaterial.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### DampingMaterial.from_printed()

*classmethod*

```python
DampingMaterial.from_printed(**cells: Any) -> Self
```

A row built from the cells its page prints, completed and marked.

The one path that works anything out. The cells are what the page
prints, under the field names of the class and with the hedges each
cell carries, as a data file writes them. A figure written under a
unit the class takes as an alias of its own (an
[`AbsorptionAreaSpectrum`](/phonometry/reference/api/materials/measured/#absorptionareaspectrum) takes
`absorption_area_125_ft2` for `absorption_area_125_m2`) is
converted on its digits with an exact factor and rounded once, and
`converted` records the figure and its unit. The row is then
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
| CatalogueError | for a cell the contract refuses; for a `derived` among the cells, which is this method's to write; for a figure under a unit alias that is not a finite number, or that names a cell given under its own name or under another alias as well; and for printed cells a value that follows from them cannot be worked out of, naming the value and the cells. |
| TypeError | for a name that is neither a field of the class nor a unit alias of one. |

### DampingMaterial.is_approximate()

```python
DampingMaterial.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### DampingMaterial.is_derived()

```python
DampingMaterial.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### DampingMaterial.peak_temperature_c()

```python
DampingMaterial.peak_temperature_c(frequency_hz: float) -> float
```

The temperature at which the loss factor peaks, at one frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | One of the frequencies the table prints, in hertz. |

**Returns:** The temperature in degrees Celsius.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the table prints no column for that frequency, or when it prints one and this row leaves it empty. An infinite or not-a-number frequency is refused the same way: converting it to an integer first raised `OverflowError` instead, which is not what this method documents and says nothing about the catalogue. |

### DampingMaterial.printed()

```python
DampingMaterial.printed(
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

### DampingMaterial.printed_fields()

```python
DampingMaterial.printed_fields() -> dict[str, Any]
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

### DampingMaterial.why_missing()

```python
DampingMaterial.why_missing(field_name: str) -> str
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

## PUBLISHED_DAMPING

*Constant* (`mapping`).
